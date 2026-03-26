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
                SELECT sc.id_conexion, sc.frecuencia_min,
                       c.servidor_conexion, c.puerto_conexion, c.database_conexion,
                       c.usuario_conexion, c.password_conexion,
                       c.tabla_conexion,   c.instrumento_conexion,
                       c.id_proyecto,      c.id_componente
                FROM sync_control sc
                INNER JOIN conexiones c ON sc.id_conexion = c.id_conexion
                WHERE sc.proximo_sync <= ?
                  AND sc.ejecutando   = 0
                  AND c.estado_conexion = 1
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
        (id_conexion, frecuencia_min,
         servidor, puerto, database,
         usuario, password, tabla,
         instrumento, id_proyecto, id_componente) = row

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
            datos = self._consultar_bd_externa(servidor, puerto, database, usuario, password, tabla)
            if datos is not None:
                self._insertar_en_bd_central(conn, cur, datos, instrumento, id_proyecto, id_componente)
                exito = True
                self.senal_log.emit(
                    f"[Sync] ✔ {instrumento} → {len(datos)} filas "
                    f"({ahora.strftime('%H:%M:%S')}) desde {HOSTNAME}"
                )
                self.senal_datos.emit({
                    "id_conexion": id_conexion,
                    "instrumento": instrumento,
                    "filas": len(datos),
                    "timestamp": ahora.isoformat(),
                })

        except Exception as e:
            self.senal_error.emit(f"[Sync] ✖ {instrumento}: {e}")

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
    def _consultar_bd_externa(self, servidor, puerto, database, usuario, password, tabla):
        drivers  = pyodbc.drivers()
        driver   = next(
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
            cur.execute(f"SELECT * FROM {tabla};")
            return [tuple(r) for r in cur.fetchall()]
        finally:
            conn.close()

    # ------------------------------------------------------------------ #
    #  Insertar en BD central (aquí defines tu lógica de upsert/insert)
    # ------------------------------------------------------------------ #
    def _insertar_en_bd_central(self, conn, cur, datos, instrumento, id_proyecto, id_componente):
        """
        Inserta datos leídos de 'hitos' en la tabla destino 'prismasX'.
        Además registra prismas únicos en la tabla 'instrumentacion'.
        """
        if instrumento == "Prismas":
            try:
                nombretabla = "prismas" + str(id_proyecto)

                # ══════════════════════════════════════════════
                # 1. CREAR TABLA SI NO EXISTE
                # ══════════════════════════════════════════════
                sqltable = f"""IF OBJECT_ID('{nombretabla}', 'U') IS NULL
                CREATE TABLE {nombretabla} (
                    id_prisma INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
                    state_prisma INT NOT NULL DEFAULT 1,
                    estado_prisma INT NOT NULL DEFAULT 1,
                    nombre_prisma VARCHAR(255) NOT NULL,
                    perfil_prisma VARCHAR(255),
                    hora_prisma DATETIME2(0) NOT NULL,
                    angulo_horizontal VARCHAR(50),
                    angulo_vertical VARCHAR(50),
                    distancia_prisma FLOAT DEFAULT 0,
                    tipoppm_prisma VARCHAR(50),
                    ppm_prisma FLOAT DEFAULT 0,
                    presion_prisma FLOAT DEFAULT 0,
                    temperatura_prisma FLOAT DEFAULT 0,
                    constante_prisma FLOAT DEFAULT 0,
                    este_target FLOAT NOT NULL,
                    norte_target FLOAT NOT NULL,
                    elevacion_target FLOAT NOT NULL,
                    altura_reflector FLOAT DEFAULT 0,
                    altura_instrumento FLOAT DEFAULT 0,
                    este_estacion FLOAT DEFAULT 0,
                    norte_estacion FLOAT DEFAULT 0,
                    altura_estacion FLOAT DEFAULT 0,
                    medicion_prisma FLOAT DEFAULT 0,
                    diferencia_tiempocorto FLOAT DEFAULT 0,
                    diferencia_tiempolargo FLOAT DEFAULT 0,
                    diferencia_limitevelocidad FLOAT DEFAULT 0,
                    distancia_horizontal FLOAT DEFAULT 0,
                    diferencia_atipica FLOAT DEFAULT 0,
                    desplaza_longitudinal FLOAT DEFAULT 0,
                    desplaza_transversal FLOAT DEFAULT 0,
                    desplaza_altura FLOAT DEFAULT 0,
                    grupo_puntos VARCHAR(255)
                );"""

                cur.execute(sqltable)
                conn.commit()

                # ══════════════════════════════════════════════
                # 2. EXTRAER NOMBRES ÚNICOS (antes de insertar)
                # ══════════════════════════════════════════════
                nombres_unicos = set(fila[2] for fila in datos)

                # ══════════════════════════════════════════════
                # 3. LIMPIAR DUPLICADOS EN MEMORIA
                #    (similar a ctrlGuardarPrismasManualesTabla)
                # ══════════════════════════════════════════════
                datos_unicos = {}
                datos_limpios = []

                for fila in datos:
                    nombre_prisma = fila[2]

                    # Convertir fecha a ISO con 'T'
                    if hasattr(fila[3], 'strftime'):
                        fecha_hora = fila[3].strftime('%Y-%m-%dT%H:%M:%S')
                    else:
                        fecha_hora = str(fila[3]).replace(' ', 'T')

                    clave = (nombre_prisma, fecha_hora)

                    if clave not in datos_unicos:
                        datos_unicos[clave] = True
                        datos_limpios.append(fila)

                # ══════════════════════════════════════════════
                # 4. CARGAR EXISTENTES EN BD PARA DEDUPLICACIÓN
                # ══════════════════════════════════════════════
                cur.execute(
                    f"SELECT nombre_prisma, FORMAT(hora_prisma, 'yyyy-MM-ddTHH:mm:ss') "
                    f"FROM {nombretabla}"
                )
                existen_prismas = set(
                    [(row[0], row[1]) for row in cur.fetchall()]
                )

                # ══════════════════════════════════════════════
                # 5. PREPARAR E INSERTAR POR LOTES
                # ══════════════════════════════════════════════
                insert_query = f"""
                    INSERT INTO {nombretabla} (
                        state_prisma, estado_prisma, nombre_prisma, hora_prisma,
                        distancia_prisma, este_target, norte_target,
                        elevacion_target, angulo_horizontal, angulo_vertical,
                        grupo_puntos
                    ) VALUES (1, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """

                lote_registros = []
                contador = 0
                for fila in datos_limpios:
                    nombre_prisma = fila[2]

                    if hasattr(fila[3], 'strftime'):
                        fecha_hora = fila[3].strftime('%Y-%m-%dT%H:%M:%S')
                    else:
                        fecha_hora = str(fila[3]).replace(' ', 'T')

                    # Deduplicar contra BD
                    if (nombre_prisma, fecha_hora) not in existen_prismas:
                        distancia = float(fila[6]) if fila[6] else 0.0
                        este      = float(fila[7]) if fila[7] else 0.0
                        norte     = float(fila[8]) if fila[8] else 0.0
                        elevacion = float(fila[9]) if fila[9] else 0.0
                        ang_h     = 0
                        ang_v     = fila[5] if fila[5] else ''
                        grupo     = fila[10] if fila[10] else ''

                        row = (
                            nombre_prisma,
                            fecha_hora,
                            distancia,
                            este,
                            norte,
                            elevacion,
                            ang_h,
                            ang_v,
                            grupo
                        )
                        lote_registros.append(row)
                        contador += 1

                    # Insertar en lotes de 1000
                    if contador % 1000 == 0 and lote_registros:
                        cur.executemany(insert_query, lote_registros)
                        lote_registros = []

                # Lote restante
                if lote_registros:
                    cur.executemany(insert_query, lote_registros)

                conn.commit()
                print(f"✅ {contador} filas nuevas insertadas en {nombretabla}")

                # ══════════════════════════════════════════════
                # 6. REGISTRAR EQUIPOS ÚNICOS EN instrumentacion
                #    (similar a mdlRegistrarEquipoZona)
                # ══════════════════════════════════════════════
                self._registrar_equipos_zona(
                    conn, cur, id_componente, nombretabla,
                    nombres_unicos, instrumento
                )

                return True

            except Exception as e:
                print(f"❌ Error al insertar en prismas{id_proyecto}: {e}")
                if conn:
                    conn.rollback()
                return False

        # ── Aquí puedes agregar más instrumentos en el futuro ──
        # elif instrumento == "Piezometros":
        #     ...

        return False


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

            if prismas_nuevos:
                print(f"✅ Nuevos equipos registrados en instrumentacion: {prismas_nuevos}")
            else:
                print("ℹ️  Todos los equipos ya estaban registrados en instrumentacion")

            return True, prismas_nuevos

        except Exception as e:
            print(f"❌ Error al registrar equipos en instrumentacion: {e}")
            if conn:
                conn.rollback()
            return False, []
    