import time
import socket
import pyodbc
from datetime import datetime, timedelta
from PySide6.QtCore import QThread, Signal
from services.security.apis.conexiones.connection import Connection

HOSTNAME = socket.gethostname()

class ConexionWorker(QThread):
    senal_log   = Signal(str)
    senal_error = Signal(str)
    senal_datos = Signal(dict)   # opcional: para mostrar en UI

    def __init__(self, parent=None):
        super().__init__(parent)
        self._corriendo = False

    def detener(self):
        self._corriendo = False

    def forzar_ciclo(self):
        """Resetea el contador para que el próximo tick ejecute el ciclo."""
        self._forzar = True
        
    def run(self):
        self._corriendo = True
        self._forzar    = False
        self.senal_log.emit("[Sync] Worker iniciado.")

        while self._corriendo:
            try:
                self._ciclo()
            except Exception as e:
                self.senal_error.emit(f"[Sync] Error en ciclo: {e}")

            self._forzar = False
            for _ in range(30):
                if not self._corriendo or self._forzar:
                    break
                time.sleep(1)

    # ------------------------------------------------------------------ #
    #  Ciclo principal
    # ------------------------------------------------------------------ #
    def _ciclo(self):
        conn = Connection.connectionDB()
        if not conn:
            return
        try:
            ahora = datetime.now()
            cur = conn.cursor()
            # Buscar conexiones que ya deben sincronizarse y NO están bloqueadas
            cur.execute("""
                SELECT sc.id_conexion, sc.frecuencia_min, c.servidor_conexion, c.puerto_conexion,
                c.database_conexion, c.usuario_conexion, c.password_conexion, c.consulta_conexion,
                c.dato_conexion, c.instrumento_conexion, c.id_proyecto, c.id_componente
                FROM sync_control sc
                INNER JOIN conexiones c ON sc.id_conexion = c.id_conexion
                WHERE sc.proximo_sync <= ?
                  AND sc.ejecutando   = 0 AND c.estado_conexion = 1
            """, ahora)
            pendientes = cur.fetchall()
        finally:
            conn.close()
        for row in pendientes:
            if not self._corriendo:
                break
            self._intentar_sincronizar(row)

    # ------------------------------------------------------------------ #
    #  Intento de adquirir el lock y sincronizar
    # ------------------------------------------------------------------ #
    def _intentar_sincronizar(self, row):
        (id_conexion, frecuencia_min, servidor, puerto, database, usuario, password,
         consulta, ultimoid, instrumento, id_proyecto, id_componente) = row
        conn = Connection.connectionDB()
        if not conn:
            return
        try:
            cur  = conn.cursor()
            ahora = datetime.now()
            # --- Adquirir lock atómico (UPDATE condicional) ---
            cur.execute("""
                UPDATE sync_control
                SET ejecutando = 1,
                    hostname   = ?
                WHERE id_conexion = ?
                  AND ejecutando  = 0
                  AND proximo_sync <= ?
            """, HOSTNAME, id_conexion, ahora)
            conn.commit()
            if cur.rowcount == 0:
                # Otro nodo ganó el lock — no hacer nada
                return
        except Exception as e:
            self.senal_error.emit(f"[Lock] {instrumento}: {e}")
            conn.close()
            return
        # --- Tenemos el lock: ejecutar la consulta externa ---
        exito = False
        try:
            datos = self._consultar_bd_externa(servidor, puerto, database, usuario, password, consulta, ultimoid)
            if datos is not None:
                self._insertar_en_bd_central(conn, cur, datos, instrumento, id_proyecto, id_componente, id_conexion)
                exito = True
                self.senal_log.emit(
                    f"[Sync] {instrumento} → {len(datos)} filas "
                    f"({ahora.strftime('%H:%M:%S')}) desde {HOSTNAME}"
                )
                self.senal_datos.emit({
                    "id_conexion": id_conexion,
                    "instrumento": instrumento,
                    "filas": len(datos),
                    "timestamp": ahora.isoformat(),
                })
        except Exception as e:
            self.senal_error.emit(f"[Sync] {instrumento}: {e}")
        finally:
            # --- Liberar lock siempre, tanto si hubo error como si no ---
            try:
                proximo = ahora + timedelta(minutes=frecuencia_min)
                cur.execute("""
                    UPDATE sync_control
                    SET ejecutando  = 0,
                        ultimo_sync = ?,
                        proximo_sync = ?
                    WHERE id_conexion = ?
                """, ahora if exito else None, proximo, id_conexion)
                conn.commit()
            except Exception as e:
                self.senal_error.emit(f"[Lock release] {e}")
            finally:
                conn.close()

    # ------------------------------------------------------------------ #
    #  Consultar BD externa (origen)
    # ------------------------------------------------------------------ #
    def _consultar_bd_externa(self, servidor, puerto, database, usuario, password, consulta, ultimoid):
        drivers = pyodbc.drivers()
        driver  = next(
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
            SELECT r.ID, r.Point_ID, p.Name, r.Epoch, t.Epoch,
                t.HzAngle, t.VAngle, t.SlopeDistance, t.Pressure, t.Temperature,
                r.Easting, r.Northing, r.Height, r.HorzDistance,
                r.LongitudinalDisplacement, r.TransverseDisplacement, r.HeightDisplacement
            FROM Points p
            INNER JOIN Results r ON p.ID = r.Point_ID
            INNER JOIN TPSMeasurements t ON t.Point_ID = r.Point_ID
                AND t.Epoch BETWEEN DATEADD(SECOND, -60, r.Epoch)
                                AND DATEADD(SECOND,  60, r.Epoch)
            WHERE r.Easting      IS NOT NULL
            AND r.Northing     IS NOT NULL
            AND r.Height       IS NOT NULL
            AND r.HorzDistance IS NOT NULL
            AND r.ID >= ?
            ORDER BY r.ID;
        """
        try:
            cur = conn.cursor()
            cur.execute(consultaSQL, (ultimoid,))
            filas = [tuple(r) for r in cur.fetchall()]
            return filas
        finally:
            conn.close()


    def _insertar_en_bd_central(self, conn, cur, datos, instrumento,
                                id_proyecto, id_componente, id_conexion):
        if instrumento == "Prismas":
            try:
                nombretabla = "prismas" + str(id_proyecto)

                # ══════════════════════════════════════════════
                # 1. CREAR TABLA SI NO EXISTE
                # ══════════════════════════════════════════════
                sqltable = f"""IF OBJECT_ID('{nombretabla}', 'U') IS NULL
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

                # ══════════════════════════════════════════════
                # 2. EXTRAER NOMBRES ÚNICOS
                # ══════════════════════════════════════════════
                nombres_unicos = set(fila[2] for fila in datos)  # fila[2] = p.Name

                # ══════════════════════════════════════════════
                # 3. LIMPIAR DUPLICADOS EN MEMORIA
                # ══════════════════════════════════════════════
                datos_unicos  = {}
                datos_limpios = []

                for fila in datos:
                    nombre_prisma = fila[2]   # p.Name
                    epoch         = fila[3]   # r.Epoch

                    epoch_dt = epoch.replace(microsecond=0) if isinstance(epoch, datetime) \
                            else datetime.strptime(str(epoch)[:19].replace('T', ' '), '%Y-%m-%d %H:%M:%S')

                    clave = (nombre_prisma, epoch_dt)
                    if clave not in datos_unicos:
                        datos_unicos[clave] = True
                        datos_limpios.append((fila, epoch_dt))  # guardar epoch_dt limpio

                # ══════════════════════════════════════════════
                # 4. CARGAR EXISTENTES EN BD PARA DEDUPLICACIÓN
                # ══════════════════════════════════════════════
                cur.execute(f"SELECT nombre_prisma, hora_prisma FROM {nombretabla}")
                existen_prismas = set(
                    (row[0], row[1].replace(microsecond=0) if isinstance(row[1], datetime)
                    else datetime.strptime(str(row[1])[:19], '%Y-%m-%d %H:%M:%S'))
                    for row in cur.fetchall()
                )

                # ══════════════════════════════════════════════
                # 5. PREPARAR E INSERTAR POR LOTES
                # ══════════════════════════════════════════════
                insert_query = f"""
                    INSERT INTO {nombretabla} (
                        state_prisma, estado_prisma,
                        nombre_prisma, hora_prisma,
                        angulo_horizontal, angulo_vertical,
                        distancia_prisma, presion_prisma, temperatura_prisma,
                        este_target, norte_target, elevacion_target,
                        distancia_horizontal,
                        desplaza_longitudinal, desplaza_transversal, desplaza_altura,
                        grupo_puntos
                    ) VALUES (1, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """

                lote_registros = []
                contador       = 0
                ultimo_id_ext  = None

                for fila, epoch_dt in datos_limpios:
                    id_externo    = fila[0]   # r.ID
                    # fila[1]     = r.Point_ID (no se usa)
                    nombre_prisma = fila[2]   # p.Name
                    # fila[3]     = r.Epoch   (ya en epoch_dt)
                    # fila[4]     = t.Epoch   (no se usa)
                    ang_h         = fila[5]   # t.HzAngle
                    ang_v         = fila[6]   # t.VAngle
                    distancia     = fila[7]   # t.SlopeDistance
                    presion       = fila[8]   # t.Pressure
                    temperatura   = fila[9]   # t.Temperature
                    este          = fila[10]  # r.Easting
                    norte         = fila[11]  # r.Northing
                    elevacion     = fila[12]  # r.Height
                    dist_hz       = fila[13]  # r.HorzDistance
                    desplaz_long  = fila[14]  # r.LongitudinalDisplacement
                    desplaz_trans = fila[15]  # r.TransverseDisplacement
                    desplaz_alt   = fila[16]  # r.HeightDisplacement

                    if (nombre_prisma, epoch_dt) not in existen_prismas:
                        lote_registros.append((
                            nombre_prisma,
                            epoch_dt,                                           # datetime, no string
                            str(ang_h)           if ang_h        is not None else '',
                            str(ang_v)           if ang_v        is not None else '',
                            float(distancia)     if distancia    is not None else 0.0,
                            float(presion)       if presion      is not None else 0.0,
                            float(temperatura)   if temperatura  is not None else 0.0,
                            float(este)          if este         is not None else 0.0,
                            float(norte)         if norte        is not None else 0.0,
                            float(elevacion)     if elevacion    is not None else 0.0,
                            float(dist_hz)       if dist_hz      is not None else 0.0,
                            float(desplaz_long)  if desplaz_long is not None else 0.0,
                            float(desplaz_trans) if desplaz_trans is not None else 0.0,
                            float(desplaz_alt)   if desplaz_alt  is not None else 0.0,
                            '',   # grupo_puntos — ya no viene en la query
                        ))
                        contador += 1

                    if ultimo_id_ext is None or id_externo > ultimo_id_ext:
                        ultimo_id_ext = id_externo

                    if len(lote_registros) >= 1000:
                        cur.executemany(insert_query, lote_registros)
                        lote_registros = []

                if lote_registros:
                    cur.executemany(insert_query, lote_registros)

                conn.commit()
                print(f"{contador} filas nuevas insertadas en {nombretabla}")

                # ══════════════════════════════════════════════
                # 6. ACTUALIZAR dato_conexion CON EL ÚLTIMO ID
                # ══════════════════════════════════════════════
                if ultimo_id_ext is not None:
                    cur.execute(
                        "UPDATE conexiones SET dato_conexion = ? WHERE id_conexion = ?",
                        str(ultimo_id_ext), id_conexion
                    )
                    conn.commit()
                    print(f"dato_conexion → {ultimo_id_ext} (id_conexion={id_conexion})")

                # ══════════════════════════════════════════════
                # 7. REGISTRAR EQUIPOS EN instrumentacion
                # ══════════════════════════════════════════════
                self._registrar_equipos_zona(
                    conn, cur, id_componente, nombretabla,
                    nombres_unicos, instrumento
                )

                return ultimo_id_ext

            except Exception as e:
                print(f"Error al insertar en prismas{id_proyecto}: {e}")
                if conn:
                    conn.rollback()
                return None

        return None

    def _registrar_equipos_zona(self, conn, cur, id_componente, nombretabla,
                                nombres_unicos, tipo_equipo):
        """
        Registra prismas únicos en la tabla 'instrumentacion'.
        Solo inserta los que NO existen aún para ese componente.
        Similar a mdlRegistrarEquipoZona.
        """
        prismas_nuevos = []

        try:
            consulta_verificacion = """
                SELECT COUNT(1) FROM instrumentacion
                WHERE nombre_equipo = ? AND id_componente = ?;
            """

            sql_insert = """
                INSERT INTO instrumentacion (
                    id_componente, tipo_equipo, nombre_equipo,
                    tabla_equipo, estado_instrumentacion
                ) VALUES (?, ?, ?, ?, ?);
            """

            for nombre_equipo in nombres_unicos:
                cur.execute(consulta_verificacion, (nombre_equipo, id_componente))
                existe = cur.fetchone()[0]

                if existe == 0:
                    cur.execute(sql_insert, (
                        id_componente,
                        tipo_equipo,       # "Prismas"
                        nombre_equipo,     # "P-01", "P-02", etc.
                        nombretabla,       # "prismas1"
                        1                  # estado activo
                    ))
                    prismas_nuevos.append(nombre_equipo)

            conn.commit()
            return True, prismas_nuevos

        except Exception as e:
            print(f"Error al registrar equipos en instrumentacion: {e}")
            if conn:
                conn.rollback()
            return False, []
    