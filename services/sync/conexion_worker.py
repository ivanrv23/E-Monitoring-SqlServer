import socket
import pyodbc
from datetime import datetime, timedelta
from PySide6.QtCore import QThread, Signal
from services.security.apis.conexiones.connection import Connection
import threading

HOSTNAME = socket.gethostname()


class ConexionWorker(QThread):
    senal_log   = Signal(str)
    senal_error = Signal(str)
    senal_datos = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._corriendo = False
        # Usamos un evento de threading para despertar el worker
        self._evento_despertar = threading.Event()
        self._forzar_ahora     = False

    def detener(self):
        """Detiene el worker de forma segura."""
        self._corriendo = False
        self._evento_despertar.set()  # Despertamos para que salga del wait

    def sincronizar_ahora(self):
        self._forzar_ahora = True
        self._resetear_proximo_sync()
        self._evento_despertar.set()  # Interrumpe el wait

    def _resetear_proximo_sync(self):
        try:
            conn = Connection.connectionDB()
            if not conn:
                return
            try:
                cur = conn.cursor()
                # Solo reseteamos las que NO están ejecutándose en este momento
                cur.execute("""
                    UPDATE sc
                    SET sc.proximo_sync = GETDATE()
                    FROM sync_control sc
                    INNER JOIN conexiones c ON sc.id_conexion = c.id_conexion
                    WHERE sc.ejecutando = 0
                      AND c.estado_conexion = 1
                """)
                conn.commit()
                filas = cur.rowcount
                self.senal_log.emit(
                    f"[Sync] Forzado inmediato: {filas} conexión(es) marcadas para sync."
                )
            finally:
                conn.close()
        except Exception as e:
            self.senal_error.emit(f"[Sync] Error al resetear proximo_sync: {e}")

    def run(self):
        self._corriendo = True
        self._evento_despertar.clear()
        self.senal_log.emit("[Sync] Worker iniciado.")

        while self._corriendo:
            try:
                self._ciclo()
            except Exception as e:
                self.senal_error.emit(f"[Sync] Error en ciclo: {e}")

            self._forzar_ahora = False

            # Esperamos hasta 60 segundos O hasta que nos despierten
            self._evento_despertar.wait(timeout=60)
            self._evento_despertar.clear()

    # ------------------------------------------------------------------ #
    #  Ciclo principal - Lee de BD qué conexiones están pendientes
    # ------------------------------------------------------------------ #
    def _ciclo(self):
        conn = Connection.connectionDB()
        if not conn:
            return
        try:
            ahora = datetime.now()
            cur = conn.cursor()
            cur.execute("""
                SELECT sc.id_conexion, sc.frecuencia_min,
                       c.servidor_conexion, c.puerto_conexion,
                       c.database_conexion, c.usuario_conexion, c.password_conexion,
                       c.grupos_conexion, c.lecturas_conexion, c.dato_conexion,
                       c.instrumento_conexion, c.id_proyecto
                FROM sync_control sc
                INNER JOIN conexiones c ON sc.id_conexion = c.id_conexion
                WHERE sc.proximo_sync <= ?
                  AND sc.ejecutando   = 0
                  AND c.estado_conexion = 1
            """, ahora)
            pendientes = cur.fetchall()
        finally:
            conn.close()

        if not pendientes:
            return

        for row in pendientes:
            if not self._corriendo:
                break
            self._intentar_sincronizar(row)

    # ------------------------------------------------------------------ #
    #  El resto del código permanece igual
    # ------------------------------------------------------------------ #
    def _intentar_sincronizar(self, row):
        (id_conexion, frecuencia_min, servidor, puerto, database, usuario, password,
         consultagrupos, consultalecturas, ultimoid_str, instrumento, id_proyecto) = row

        try:
            ultimoid = int(ultimoid_str) if ultimoid_str else 0
        except (ValueError, TypeError):
            ultimoid = 0

        conn = Connection.connectionDB()
        if not conn:
            return
        try:
            cur   = conn.cursor()
            ahora = datetime.now()
            cur.execute("""
                UPDATE sync_control
                SET ejecutando = 1, hostname = ?
                WHERE id_conexion = ? AND ejecutando = 0 AND proximo_sync <= ?
            """, HOSTNAME, id_conexion, ahora)
            conn.commit()
            if cur.rowcount == 0:
                return  # Otro proceso/instancia ya lo tomó (concurrencia)
        except Exception as e:
            self.senal_error.emit(f"[Lock] {instrumento}: {e}")
            conn.close()
            return

        exito = False

        try:
            grupos = self._obtener_grupos_externos(
                servidor, puerto, database, usuario, password, consultagrupos
            )
            if not grupos:
                self.senal_log.emit("[Sync] No se encontraron grupos.")
                return

            self.senal_log.emit(f"[Sync] {len(grupos)} grupos encontrados.")

            mapa_componentes = {}
            mapa_nombres     = {}
            for id_grupo, nombre_grupo in grupos:
                id_comp = self._asegurar_componente(conn, cur, id_proyecto, nombre_grupo)
                mapa_componentes[id_grupo] = id_comp
                mapa_nombres[id_grupo]     = nombre_grupo

            self.senal_log.emit(f"[Sync] Consultando data desde ID {ultimoid}...")
            todos_los_datos = self._consultar_bd_externa(
                servidor, puerto, database, usuario, password, consultalecturas, ultimoid
            )

            if not todos_los_datos:
                self.senal_log.emit("[Sync] Sin datos nuevos.")
                exito = True
                return

            total_filas    = 0
            ultimoid_final = max(fila[0] for fila in todos_los_datos)
            self.senal_log.emit(
                f"[Sync] {len(todos_los_datos)} filas obtenidas. Distribuyendo..."
            )

            datos_por_grupo = {}
            for fila in todos_los_datos:
                nombre_grupo_fila = fila[16]
                id_grupo_fila = next(
                    (gid for gid, gnombre in mapa_nombres.items()
                     if gnombre == nombre_grupo_fila),
                    None
                )
                if id_grupo_fila is None:
                    continue
                datos_por_grupo.setdefault(id_grupo_fila, []).append(fila)

            for id_grupo, filas_grupo in datos_por_grupo.items():
                if not self._corriendo:
                    break
                id_componente = mapa_componentes[id_grupo]
                nombre_grupo  = mapa_nombres[id_grupo]

                respinsert = self._insertar_en_bd_central(
                    conn, cur, filas_grupo, instrumento, id_proyecto, id_componente
                )
                if respinsert:
                    total_filas += len(filas_grupo)
                    self.senal_log.emit(
                        f"[Sync] Grupo '{nombre_grupo}': {len(filas_grupo)} filas."
                    )

            if total_filas > 0:
                exito = True
                cur.execute(
                    "UPDATE conexiones SET dato_conexion = ? WHERE id_conexion = ?",
                    str(ultimoid_final), id_conexion
                )
                conn.commit()
                self.senal_log.emit(
                    f"[Sync] Total {total_filas} filas. Último ID: {ultimoid_final}"
                )

        except Exception as e:
            self.senal_error.emit(f"[Sync] {instrumento}: {e}")

        finally:
            # SIEMPRE liberamos el lock y programamos el próximo ciclo
            try:
                proximo = ahora + timedelta(minutes=frecuencia_min)
                cur.execute("""
                    UPDATE sync_control
                    SET ejecutando   = 0,
                        ultimo_sync  = ?,
                        proximo_sync = ?
                    WHERE id_conexion = ?
                """, ahora if exito else None, proximo, id_conexion)
                conn.commit()
                self.senal_log.emit(
                    f"[Sync] Próximo sync de conexión {id_conexion}: {proximo:%H:%M:%S}"
                )
            except Exception as e:
                self.senal_error.emit(f"[Lock release] {e}")
            finally:
                conn.close()

    # ---- Métodos de BD sin cambios ---- #

    def _obtener_grupos_externos(self, servidor, puerto, database,
                                  usuario, password, consultagrupos):
        drivers = pyodbc.drivers()
        driver = next(
            (d for d in ["ODBC Driver 18 for SQL Server",
                         "ODBC Driver 17 for SQL Server",
                         "SQL Server"] if d in drivers),
            None
        )
        if not driver:
            raise RuntimeError("No hay driver ODBC disponible.")

        conn_str = (
            f"DRIVER={{{driver}}};"
            f"SERVER={servidor},{puerto};"
            f"DATABASE={database};"
            f"UID={usuario};PWD={password};"
            "TrustServerCertificate=yes;"
            "Connection Timeout=5;"
        )
        conn = pyodbc.connect(conn_str)
        try:
            cur = conn.cursor()
            cur.execute(consultagrupos)
            return [(row[0], row[1]) for row in cur.fetchall()]
        finally:
            conn.close()

    def _asegurar_componente(self, conn, cur, id_proyecto, nombre_componente):
        cur.execute("""
            SELECT id_componente FROM componentes
            WHERE id_proyecto = ? AND nombre_componente = ?
        """, id_proyecto, nombre_componente)
        row = cur.fetchone()
        if row:
            return row[0]
        cur.execute("""
            INSERT INTO componentes (id_proyecto, nombre_componente, estado_componente)
            OUTPUT INSERTED.id_componente
            VALUES (?, ?, 1)
        """, id_proyecto, nombre_componente)
        nuevo_id = cur.fetchone()[0]
        conn.commit()
        self.senal_log.emit(f"[Componente] Creado '{nombre_componente}' (ID: {nuevo_id})")
        return nuevo_id

    def _consultar_bd_externa(self, servidor, puerto, database, usuario, password, consulta, ultimoid):
        drivers = pyodbc.drivers()
        driver = next(
            (d for d in ["ODBC Driver 18 for SQL Server",
                         "ODBC Driver 17 for SQL Server",
                         "SQL Server"] if d in drivers),
            None
        )
        if not driver:
            raise RuntimeError("No hay driver ODBC disponible.")

        conn_str = (
            f"DRIVER={{{driver}}};"
            f"SERVER={servidor},{puerto};"
            f"DATABASE={database};"
            f"UID={usuario};PWD={password};"
            "TrustServerCertificate=yes;"
            "Connection Timeout=5;"
        )
        conn = pyodbc.connect(conn_str)
        consultaSQL = """
            SELECT r.ID, r.Point_ID, p.Name, t.Epoch,
                t.HzAngle, t.VAngle, t.SlopeDistance, t.Pressure, t.Temperature,
                r.Easting, r.Northing, r.Height, r.HorzDistance, r.LongitudinalDisplacement,
                r.TransverseDisplacement, r.HeightDisplacement, g.Name
            FROM Points p
            INNER JOIN Results r ON p.ID = r.Point_ID
            INNER JOIN TPSMeasurements t ON t.Point_ID = r.Point_ID
                AND t.Epoch BETWEEN DATEADD(SECOND, -60, r.Epoch)
                                AND DATEADD(SECOND,  60, r.Epoch)
            INNER JOIN PointGroups g ON t.PointGroup_ID = g.ID
            WHERE r.Easting      IS NOT NULL
              AND r.Northing     IS NOT NULL
              AND r.Height       IS NOT NULL
              AND r.HorzDistance IS NOT NULL
              AND r.ID >= ?
            ORDER BY r.ID;
        """
        try:
            cur = conn.cursor()
            cur.execute(consulta, (ultimoid,))
            return [tuple(r) for r in cur.fetchall()]
        finally:
            conn.close()

    def _insertar_en_bd_central(self, conn, cur, datos, instrumento, id_proyecto, id_componente_grupo):
        if instrumento == "Prismas":
            try:
                nombretabla = "prismas" + str(id_proyecto)
                sqltable = f"""
                    IF OBJECT_ID('{nombretabla}', 'U') IS NULL
                    CREATE TABLE {nombretabla} (
                        id_prisma               INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
                        state_prisma            INT NOT NULL DEFAULT 1,
                        estado_prisma           INT NOT NULL DEFAULT 1,
                        nombre_prisma           VARCHAR(255) NOT NULL,
                        perfil_prisma           VARCHAR(255),
                        hora_prisma             DATETIME2(0) NOT NULL,
                        angulo_horizontal       VARCHAR(50),
                        angulo_vertical         VARCHAR(50),
                        distancia_prisma        FLOAT DEFAULT 0,
                        tipoppm_prisma          VARCHAR(50),
                        ppm_prisma              FLOAT DEFAULT 0,
                        presion_prisma          FLOAT DEFAULT 0,
                        temperatura_prisma      FLOAT DEFAULT 0,
                        constante_prisma        FLOAT DEFAULT 0,
                        este_target             FLOAT NOT NULL,
                        norte_target            FLOAT NOT NULL,
                        elevacion_target        FLOAT NOT NULL,
                        altura_reflector        FLOAT DEFAULT 0,
                        altura_instrumento      FLOAT DEFAULT 0,
                        este_estacion           FLOAT DEFAULT 0,
                        norte_estacion          FLOAT DEFAULT 0,
                        altura_estacion         FLOAT DEFAULT 0,
                        medicion_prisma         FLOAT DEFAULT 0,
                        diferencia_tiempocorto  FLOAT DEFAULT 0,
                        diferencia_tiempolargo  FLOAT DEFAULT 0,
                        diferencia_limitevelocidad FLOAT DEFAULT 0,
                        distancia_horizontal    FLOAT DEFAULT 0,
                        diferencia_atipica      FLOAT DEFAULT 0,
                        desplaza_longitudinal   FLOAT DEFAULT 0,
                        desplaza_transversal    FLOAT DEFAULT 0,
                        desplaza_altura         FLOAT DEFAULT 0,
                        grupo_puntos            VARCHAR(255)
                    );"""
                cur.execute(sqltable)
                conn.commit()

                nombres_unicos = set(fila[2] for fila in datos)
                datos_unicos   = {}
                datos_limpios  = []

                for fila in datos:
                    nombre_prisma = fila[2]
                    epoch = fila[3]
                    epoch_dt = (
                        epoch.replace(microsecond=0)
                        if isinstance(epoch, datetime)
                        else datetime.strptime(
                            str(epoch)[:19].replace('T', ' '), '%Y-%m-%d %H:%M:%S'
                        )
                    )
                    clave = (nombre_prisma, epoch_dt)
                    if clave not in datos_unicos:
                        datos_unicos[clave] = True
                        datos_limpios.append((fila, epoch_dt))

                cur.execute(f"SELECT nombre_prisma, hora_prisma FROM {nombretabla}")
                existen_prismas = set(
                    (row[0],
                     row[1].replace(microsecond=0)
                     if isinstance(row[1], datetime)
                     else datetime.strptime(str(row[1])[:19], '%Y-%m-%d %H:%M:%S'))
                    for row in cur.fetchall()
                )

                insert_query = f"""
                    INSERT INTO {nombretabla} (
                        state_prisma, estado_prisma,
                        nombre_prisma, hora_prisma,
                        angulo_horizontal, angulo_vertical,
                        distancia_prisma, presion_prisma, temperatura_prisma,
                        este_target, norte_target, elevacion_target,
                        distancia_horizontal, desplaza_longitudinal,
                        desplaza_transversal, desplaza_altura,
                        grupo_puntos
                    ) VALUES (1, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """

                lote_registros = []
                contador = 0

                for fila, epoch_dt in datos_limpios:
                    nombre_prisma = fila[2]
                    ang_h         = fila[4]
                    ang_v         = fila[5]
                    distancia     = fila[6]
                    presion       = fila[7]
                    temperatura   = fila[8]
                    este          = fila[9]
                    norte         = fila[10]
                    elevacion     = fila[11]
                    dist_hz       = fila[12]
                    desplaz_long  = fila[13]
                    desplaz_trans = fila[14]
                    desplaz_alt   = fila[15]
                    grupo         = fila[16]

                    if (nombre_prisma, epoch_dt) not in existen_prismas:
                        lote_registros.append((
                            nombre_prisma,
                            epoch_dt,
                            str(ang_h)            if ang_h        is not None else '',
                            str(ang_v)            if ang_v        is not None else '',
                            float(distancia)      if distancia    is not None else 0.0,
                            float(presion)        if presion      is not None else 0.0,
                            float(temperatura)    if temperatura  is not None else 0.0,
                            float(este)           if este         is not None else 0.0,
                            float(norte)          if norte        is not None else 0.0,
                            float(elevacion)      if elevacion    is not None else 0.0,
                            float(dist_hz)        if dist_hz      is not None else 0.0,
                            float(desplaz_long)   if desplaz_long is not None else 0.0,
                            float(desplaz_trans)  if desplaz_trans is not None else 0.0,
                            float(desplaz_alt)    if desplaz_alt  is not None else 0.0,
                            grupo                 if grupo        is not None else '',
                        ))
                        contador += 1

                    if len(lote_registros) >= 1000:
                        cur.executemany(insert_query, lote_registros)
                        lote_registros = []

                if lote_registros:
                    cur.executemany(insert_query, lote_registros)

                conn.commit()
                self.senal_log.emit(
                    f"[Sync] {contador} filas nuevas en {nombretabla}"
                )

                self._registrar_equipos_zona(
                    conn, cur, id_componente_grupo,
                    nombretabla, nombres_unicos, instrumento
                )
                return True

            except Exception as e:
                self.senal_error.emit(f"Error insertar en {nombretabla}: {e}")
                if conn:
                    conn.rollback()
                return False

        return False

    def _registrar_equipos_zona(self, conn, cur, id_componente,
                                 nombretabla, nombres_unicos, tipo_equipo):
        try:
            for nombre_equipo in nombres_unicos:
                cur.execute("""
                    SELECT COUNT(1) FROM instrumentacion
                    WHERE nombre_equipo = ? AND id_componente = ?
                """, (nombre_equipo, id_componente))
                if cur.fetchone()[0] == 0:
                    cur.execute("""
                        INSERT INTO instrumentacion (
                            id_componente, tipo_equipo, nombre_equipo,
                            tabla_equipo, estado_instrumentacion
                        ) VALUES (?, ?, ?, ?, 1)
                    """, (id_componente, tipo_equipo, nombre_equipo, nombretabla))
            conn.commit()
            return True, []
        except Exception as e:
            self.senal_error.emit(f"Error registrar equipos: {e}")
            if conn:
                conn.rollback()
            return False, []
    