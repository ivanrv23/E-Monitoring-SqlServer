import socket
import threading
import time
import logging
from logging.handlers import RotatingFileHandler
from concurrent.futures import ThreadPoolExecutor, wait
from datetime import datetime, timedelta

import pyodbc
from PySide6.QtCore import QThread, Signal

from services.security.apis.conexiones.connection import Connection

# ==========================================
# CONFIGURACIÓN DE LOGS (Solo archivo para errores, consola limpia)
# ==========================================
logger = logging.getLogger("SyncWorker")
logger.setLevel(logging.DEBUG)

# Log para Consola (INFO y superior, formato estricto con ID y Hilo)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_format = logging.Formatter('[%(asctime)s] %(levelname)-7s | %(message)s', datefmt='%H:%M:%S')
console_handler.setFormatter(console_format)
logger.addHandler(console_handler)

# Log para Archivo (SOLO ERRORES)
file_handler = RotatingFileHandler("sync_errors.log", maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
file_handler.setLevel(logging.ERROR)
file_format = logging.Formatter('[%(asctime)s] %(levelname)-7s | [%(threadName)s] %(message)s')
file_handler.setFormatter(file_format)
logger.addHandler(file_handler)

HOSTNAME = socket.gethostname()

# ==========================================
# CONSTANTES Y CONFIGURACIÓN
# ==========================================
MAX_WORKERS_CONCURRENTES = 6
CONNECTION_TIMEOUT_SEG = 8
QUERY_TIMEOUT_SEG = 120
MAX_REINTENTOS_BACKOFF = 5
MAX_REINTENTOS_CONEXION_EXTERNA = 2
ESPERA_REINTENTO_CONEXION_SEG = 2
LOCK_STALE_MINUTOS = 5

TARGET_SEGUNDOS_LOTE = 2.0
FETCH_LOTE_MIN = 500
FETCH_LOTE_MAX = 100_000
FETCH_LOTE_INICIAL = 5_000
INSERT_LOTE_MIN = 200
INSERT_LOTE_MAX = 50_000
INSERT_LOTE_INICIAL = 2_000
MAX_MINUTOS_ESPERA = 240

# --- NUEVO: retry específico ante deadlock (SQLSTATE 40001) ---
MAX_REINTENTOS_DEADLOCK = 4
ESPERA_BASE_DEADLOCK_SEG = 1.5

# --- NUEVO: backoff fijo tras varios fallos consecutivos ---
INTENTOS_ANTES_DE_BACKOFF_LARGO = 3
BACKOFF_LARGO_MINUTOS = 60

# --- NUEVO: timeout forzado para cierres de conexión que puedan colgarse ---
CIERRE_CONEXION_TIMEOUT_SEG = 10

# SQLSTATEs que indican error de autenticación/autorización (no debe reintentarse)
AUTH_SQLSTATES = {'28000', '42000'}


class AdaptiveBatcher:
    """Ajusta dinámicamente el tamaño del lote."""
    def __init__(self, inicial, minimo, maximo, target_seg=TARGET_SEGUNDOS_LOTE):
        self.tamano = inicial
        self.minimo = minimo
        self.maximo = maximo
        self.target_seg = target_seg

    def registrar(self, duracion_seg, filas_procesadas):
        if filas_procesadas <= 0 or duracion_seg <= 0:
            return self.tamano

        if duracion_seg > (self.target_seg * 2):
            self.tamano = max(self.minimo, int(self.tamano * 0.6))
            return self.tamano

        seg_por_fila = duracion_seg / filas_procesadas
        if seg_por_fila <= 0:
            return self.tamano

        tamano_ideal = int(self.target_seg / seg_por_fila)
        nuevo_tamano = int((self.tamano * 0.7) + (tamano_ideal * 0.3))
        self.tamano = max(self.minimo, min(self.maximo, nuevo_tamano))
        return self.tamano


def _driver_odbc():
    drivers = pyodbc.drivers()
    return next((d for d in ["ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server", "SQL Server"] if d in drivers), None)


def _set_query_timeout(cur, segundos):
    try:
        cur.timeout = segundos
    except AttributeError:
        pass


def _es_deadlock(e) -> bool:
    """SQLSTATE 40001 = deadlock victim, SQL Server pide reintentar."""
    sqlstate = e.args[0] if e.args else ''
    return sqlstate == '40001'


def _es_error_autenticacion(e) -> bool:
    sqlstate = e.args[0] if e.args else ''
    return sqlstate in AUTH_SQLSTATES or 'Login failed' in str(e)


def _escapar_password_odbc(password: str) -> str:
    """Envuelve el password en llaves y escapa llaves internas, para que
    caracteres especiales (; = etc.) dentro del password no rompan la
    cadena de conexión ODBC."""
    if password is None:
        return ''
    return '{' + str(password).replace('}', '}}') + '}'


def _cerrar_con_timeout(conn, timeout_seg=CIERRE_CONEXION_TIMEOUT_SEG, nombre="conexion", emit_log=None):
    """Cierra una conexión con timeout forzado usando un hilo daemon.

    pyodbc.Connection.close() puede colgarse indefinidamente si la conexión
    quedó en un estado ambiguo (por ejemplo, tras ser elegida víctima de un
    deadlock). Sin este wrapper, un close() colgado deja el hilo del pool
    atrapado para siempre. Si no responde a tiempo, se abandona: el hilo
    del pool queda libre, aunque el socket subyacente quede huérfano hasta
    que el proceso lo recicle.
    """
    if conn is None:
        return

    resultado = {"cerrado": False}

    def _cerrar():
        try:
            conn.close()
            resultado["cerrado"] = True
        except Exception:
            pass

    hilo = threading.Thread(target=_cerrar, daemon=True, name=f"Close-{nombre}")
    hilo.start()
    hilo.join(timeout=timeout_seg)

    if not resultado["cerrado"]:
        msg = f"[Cierre] {nombre} no respondió en {timeout_seg}s al cerrar, abandonada (posible conexión zombie)"
        logger.warning(msg)
        if emit_log:
            emit_log(msg)


def _ejecutar_con_retry_deadlock(cur, consulta, params, emit_log=None):
    """Ejecuta una query con reintento automático ante deadlock (40001).
    Cualquier otro error se propaga de inmediato, sin reintentar."""
    intento = 0
    while True:
        intento += 1
        try:
            cur.execute(consulta, params)
            return
        except pyodbc.Error as e:
            if _es_deadlock(e) and intento < MAX_REINTENTOS_DEADLOCK:
                espera = ESPERA_BASE_DEADLOCK_SEG * intento
                msg = f"[Deadlock] Reintento {intento}/{MAX_REINTENTOS_DEADLOCK} en {espera:.1f}s"
                logger.warning(msg)
                if emit_log:
                    emit_log(msg)
                time.sleep(espera)
                continue
            raise


def _conectar_externa(servidor, puerto, database, usuario, password):
    driver = _driver_odbc()
    if not driver:
        raise RuntimeError("No hay driver ODBC disponible.")

    conn_str = (
        f"DRIVER={{{driver}}};"
        f"SERVER={servidor},{puerto};"
        f"DATABASE={database};"
        f"UID={usuario};"
        f"PWD={_escapar_password_odbc(password)};"
        "TrustServerCertificate=yes;"
        f"Connection Timeout={CONNECTION_TIMEOUT_SEG};"
        "KeepAliveInterval=30;KeepAliveCount=5;"
    )
    ultimo_error = None
    for intento in range(1, MAX_REINTENTOS_CONEXION_EXTERNA + 1):
        try:
            return pyodbc.connect(conn_str, timeout=CONNECTION_TIMEOUT_SEG)
        except pyodbc.Error as e:
            if _es_error_autenticacion(e):
                # No reintentar ante error de credenciales: evita acumular
                # intentos fallidos que puedan bloquear la cuenta en el servidor.
                raise
            ultimo_error = e
            if intento < MAX_REINTENTOS_CONEXION_EXTERNA:
                time.sleep(ESPERA_REINTENTO_CONEXION_SEG)
    raise ultimo_error


class ConexionWorker(QThread):
    senal_log = Signal(str)
    senal_error = Signal(str)
    senal_datos = Signal(dict)
    senal_sync_completo = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._corriendo = False
        self._evento_despertar = threading.Event()
        self._forzar_ahora = False
        self._fallos_consecutivos = {}
        self._pool = None
        self._tareas_activas = {}  # Track de tareas activas para evitar duplicados

    def detener(self):
        logger.info("Solicitando detención del Worker...")
        self._corriendo = False
        self._evento_despertar.set()
        if self._pool:
            self._pool.shutdown(wait=True, cancel_futures=True)
        logger.info("Worker detenido correctamente.")

    def sincronizar_ahora(self):
        self._forzar_ahora = True
        self._resetear_proximo_sync()
        self._evento_despertar.set()

    def _resetear_proximo_sync(self):
        conn = None
        try:
            conn = Connection.connectionDB()
            if not conn:
                self._emit_error("[Sync] No se pudo obtener conexión para resetear proximo_sync")
                return

            cur = conn.cursor()
            ahora = datetime.now()
            cur.execute("""
                UPDATE sc SET sc.proximo_sync = ?
                FROM sync_control sc INNER JOIN conexiones c ON sc.id_conexion = c.id_conexion
                WHERE sc.ejecutando = 0 AND c.estado_conexion = 1
            """, ahora)
            conn.commit()
            self._emit_log(f"[Sync] Forzado inmediato: {cur.rowcount} conexión(es) marcadas a las {ahora:%H:%M:%S}")
        except Exception as e:
            self._emit_error(f"[Sync] Error al resetear proximo_sync: {e}")
        finally:
            _cerrar_con_timeout(conn, nombre="conn_central (resetear_proximo_sync)", emit_log=self._emit_log)

    def run(self):
        self._corriendo = True
        self._evento_despertar.clear()
        self._pool = ThreadPoolExecutor(max_workers=MAX_WORKERS_CONCURRENTES, thread_name_prefix="Sync")

        self._emit_log(f"[Sync] Worker iniciado en host: {HOSTNAME} | Pool: {MAX_WORKERS_CONCURRENTES} hilos")

        try:
            self._resetear_proximo_sync()
            futuros = self._ciclo()
            if self._forzar_ahora and futuros:
                wait(futuros)
        except Exception as e:
            logger.error(f"Error en ciclo inicial: {e}", exc_info=True)
        finally:
            self._forzar_ahora = False
            self.senal_sync_completo.emit()

        while self._corriendo:
            self._evento_despertar.wait(timeout=60)
            self._evento_despertar.clear()
            if not self._corriendo:
                break
            forzado = self._forzar_ahora
            try:
                futuros = self._ciclo()
                if forzado and futuros:
                    wait(futuros)
            except Exception as e:
                logger.error(f"Error en ciclo: {e}", exc_info=True)
            self._forzar_ahora = False
            self.senal_sync_completo.emit()

        self._emit_log("[Sync] Worker detenido")

    def _emit_log(self, msg):
        logger.info(msg)
        self.senal_log.emit(msg)

    def _emit_error(self, msg):
        logger.error(msg)
        self.senal_error.emit(msg)

    def _asegurar_columna_lock(self, conn, cur):
        try:
            cur.execute("""
                IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('sync_control') AND name = 'inicio_ejecucion')
                ALTER TABLE sync_control ADD inicio_ejecucion DATETIME2 NULL;
            """)
            cur.execute("""
                IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('sync_control') AND name = 'ultimo_heartbeat')
                ALTER TABLE sync_control ADD ultimo_heartbeat DATETIME2 NULL;
            """)
            conn.commit()
        except Exception as e:
            self._emit_error(f"[Schema] Error al asegurar columnas de lock: {e}")
            raise

    def _liberar_locks_huerfanos(self, conn, cur, ahora):
        try:
            cur.execute("""
                SELECT sc.id_conexion, c.instrumento_conexion,
                       COALESCE(sc.ultimo_heartbeat, sc.inicio_ejecucion) AS ultimo_contacto, sc.hostname
                FROM sync_control sc INNER JOIN conexiones c ON sc.id_conexion = c.id_conexion
                WHERE sc.ejecutando = 1
                  AND COALESCE(sc.ultimo_heartbeat, sc.inicio_ejecucion) IS NOT NULL
                  AND COALESCE(sc.ultimo_heartbeat, sc.inicio_ejecucion) < DATEADD(MINUTE, -?, ?)
                  AND c.estado_conexion = 1
            """, LOCK_STALE_MINUTOS, ahora)

            huerfanos = cur.fetchall()
            if huerfanos:
                for row in huerfanos:
                    id_c, instrumento, ultimo_contacto, hostname = row
                    cur.execute("""
                        UPDATE sync_control SET ejecutando = 0, inicio_ejecucion = NULL, ultimo_heartbeat = NULL, proximo_sync = ?
                        WHERE id_conexion = ? AND ejecutando = 1
                    """, ahora, id_c)
                    self._emit_log(f"[Lock Huérfano] Liberado ID={id_c} ({instrumento}) | Host: {hostname}")
                conn.commit()
                self._emit_log(f"[Lock] {len(huerfanos)} lock(s) huérfano(s) liberados (> {LOCK_STALE_MINUTOS} min)")
        except Exception as e:
            self._emit_error(f"[Lock] Error al liberar locks huérfanos: {e}")
            raise

    def _ciclo(self):
        # --- NUEVO: diagnóstico de salud del pool al inicio de cada ciclo ---
        activos = {k: f for k, f in self._tareas_activas.items() if not f.done()}
        if activos:
            self._emit_log(
                f"[Salud Pool] {len(activos)} tarea(s) aún en ejecución de ciclos anteriores: {list(activos.keys())}"
            )
        # ---------------------------------------------------------------------

        conn = None
        try:
            conn = Connection.connectionDB()
            if not conn:
                self._emit_error("[Ciclo] No se pudo obtener conexión a BD central")
                return []

            ahora = datetime.now()
            cur = conn.cursor()
            self._asegurar_columna_lock(conn, cur)
            self._liberar_locks_huerfanos(conn, cur, ahora)

            cur.execute("""
                SELECT sc.id_conexion, sc.frecuencia_min, c.servidor_conexion, c.puerto_conexion,
                       c.database_conexion, c.usuario_conexion, c.password_conexion, c.grupos_conexion,
                       c.lecturas_conexion, c.dato_conexion, c.instrumento_conexion, c.id_proyecto,
                       sc.ejecutando, sc.proximo_sync, sc.ultimo_sync, sc.hostname, sc.inicio_ejecucion
                FROM sync_control sc INNER JOIN conexiones c ON sc.id_conexion = c.id_conexion
                WHERE sc.proximo_sync <= ? AND sc.ejecutando = 0 AND c.estado_conexion = 1
                ORDER BY sc.proximo_sync ASC
            """, ahora)
            pendientes = cur.fetchall()
        except Exception as e:
            logger.error(f"Error consultando BD central: {e}", exc_info=True)
            return []
        finally:
            _cerrar_con_timeout(conn, nombre="conn_central (ciclo)", emit_log=self._emit_log)

        if not pendientes:
            return []

        self._emit_log(f"[Ciclo] {len(pendientes)} conexión(es) pendiente(s) a las {ahora:%H:%M:%S}")

        # Enviar tareas al pool SIN bloquear el hilo principal
        futuros_ciclo = []
        for row in pendientes:
            id_conexion = row[0]

            # Verificación adicional: no enviar si ya está en tareas_activas
            if id_conexion in self._tareas_activas:
                futuro = self._tareas_activas[id_conexion]
                if not futuro.done():
                    self._emit_log(f"[Ciclo] ID={id_conexion} ya en ejecución, omitiendo")
                    futuros_ciclo.append(futuro)
                    continue
                else:
                    # Limpiar tarea completada
                    del self._tareas_activas[id_conexion]

            # Enviar al pool y trackear
            futuro = self._pool.submit(self._intentar_sincronizar, tuple(row))
            self._tareas_activas[id_conexion] = futuro
            futuros_ciclo.append(futuro)
            self._emit_log(f"[Ciclo] ID={id_conexion} enviado al pool")
        return futuros_ciclo

    def _intentar_sincronizar(self, row):
        (id_conexion, frecuencia_min, servidor, puerto, database, usuario, password,
         consultagrupos, consultalecturas, ultimoid_str, instrumento, id_proyecto,
         ejecutando_actual, proximo_sync, ultimo_sync, hostname_actual, inicio_ejecucion) = row

        thread_id = threading.current_thread().name
        self._emit_log(f"[Inicio] ID={id_conexion} ({instrumento}) | Hilo: {thread_id} | Proyecto: {id_proyecto}")

        try:
            ultimoid = int(ultimoid_str) if ultimoid_str else 0
        except:
            ultimoid = 0

        conn = None
        lock_adquirido = False
        ultimo_id_confirmado = ultimoid
        total_filas_procesadas = 0
        total_filas_insertadas = 0
        conn_externa = None
        nombretabla = f"prismas{id_proyecto}" if instrumento == "PRISMAS" else None
        staging_listo = False
        ahora = datetime.now()

        batcher_fetch = AdaptiveBatcher(FETCH_LOTE_INICIAL, FETCH_LOTE_MIN, FETCH_LOTE_MAX)
        batcher_insert = AdaptiveBatcher(INSERT_LOTE_INICIAL, INSERT_LOTE_MIN, INSERT_LOTE_MAX)

        try:
            # FASE 1: ADQUIRIR LOCK
            conn = Connection.connectionDB()
            if not conn:
                raise Exception("No se pudo conectar a BD central")

            cur = conn.cursor()
            cur.fast_executemany = True
            ahora = datetime.now()

            cur.execute("""
                UPDATE sync_control SET ejecutando = 1, hostname = ?, inicio_ejecucion = ?, ultimo_heartbeat = ?
                WHERE id_conexion = ? AND ejecutando = 0 AND proximo_sync <= ?
            """, HOSTNAME, ahora, ahora, id_conexion, ahora)
            conn.commit()

            if cur.rowcount == 0:
                self._emit_log(f"[Lock] ID={id_conexion} omitido (ya ejecutando por otro proceso)")
                return

            lock_adquirido = True
            self._emit_log(f"[Lock OK] ID={id_conexion} adquirido por {HOSTNAME}")

            # FASE 2: CONEXIÓN EXTERNA Y GRUPOS
            conn_externa = _conectar_externa(servidor, puerto, database, usuario, password)
            grupos = self._obtener_grupos_externos(conn_externa, consultagrupos)

            if not grupos:
                self._emit_log(f"[Grupos] ID={id_conexion} sin grupos. Finalizado.")
                return

            self._emit_log(f"[Grupos] ID={id_conexion} | {len(grupos)} grupos encontrados")

            mapa_componentes = {}
            for id_grupo, nombre_grupo in grupos:
                if not nombre_grupo or not str(nombre_grupo).strip():
                    continue
                id_comp = self._asegurar_componente(conn, cur, id_proyecto, nombre_grupo)
                mapa_componentes[id_grupo] = id_comp

            self._emit_log(f"[Componentes] ID={id_conexion} | {len(mapa_componentes)} mapeados")

            if nombretabla:
                self._asegurar_tabla_prismas(conn, cur, nombretabla)
                self._asegurar_staging(cur, nombretabla)
                staging_listo = True

            # FASE 3: BUCLE DE LOTES
            num_lote = 0
            for lote in self._consultar_bd_externa_paginado(conn_externa, consultalecturas, ultimo_id_confirmado, batcher_fetch):
                if not self._corriendo:
                    break
                if not lote:
                    continue

                num_lote += 1
                inicio_pagina = time.monotonic()
                page_max_id = max(fila[0] for fila in lote)

                filas_validas = [f for f in lote if f[17] in mapa_componentes]
                total_filas_procesadas += len(filas_validas)

                nombres_por_componente = {}
                for fila in filas_validas:
                    id_componente = mapa_componentes[fila[17]]
                    nombres_por_componente.setdefault(id_componente, set()).add(fila[2])

                inicio_insert = time.monotonic()
                insertadas, _ = self._insertar_en_bd_central(conn, cur, filas_validas, instrumento, id_proyecto, nombretabla, batcher_insert)
                dur_insert = time.monotonic() - inicio_insert
                total_filas_insertadas += insertadas

                inicio_equipos = time.monotonic()
                if nombres_por_componente:
                    self._registrar_equipos_zona_batch(conn, cur, nombres_por_componente, nombretabla, instrumento)
                dur_equipos = time.monotonic() - inicio_equipos

                ultimo_id_confirmado = page_max_id
                ahora_pagina = datetime.now()

                # GUARDADO DE PROGRESO Y HEARTBEAT
                cur.execute("UPDATE conexiones SET dato_conexion = ? WHERE id_conexion = ?", str(ultimo_id_confirmado), id_conexion)
                cur.execute("UPDATE sync_control SET ultimo_heartbeat = ? WHERE id_conexion = ?", ahora_pagina, id_conexion)
                conn.commit()

                dur_pagina = time.monotonic() - inicio_pagina
                self._emit_log(f"[Lote {num_lote}] ID={id_conexion} | Proc: {len(filas_validas)} | Ins: {insertadas} | MaxID: {page_max_id} | T: {dur_pagina:.2f}s (ins: {dur_insert:.2f}s, eq: {dur_equipos:.2f}s) | F:{batcher_fetch.tamano} I:{batcher_insert.tamano}")

            self._emit_log(f"[Éxito] ID={id_conexion} | Procesadas: {total_filas_procesadas} | Insertadas: {total_filas_insertadas}")
            self._fallos_consecutivos[id_conexion] = 0

        except Exception as e:
            logger.error(f"[Error Sync] ID={id_conexion} | Progreso hasta ID {ultimo_id_confirmado} | Error: {e}", exc_info=True)
            self._emit_error(f"[Error] ID={id_conexion}: {e}")
            self._fallos_consecutivos[id_conexion] = self._fallos_consecutivos.get(id_conexion, 0) + 1

        finally:
            if staging_listo:
                try:
                    self._limpiar_staging(cur, nombretabla)
                    conn.commit()
                except Exception as e:
                    self._emit_error(f"[Cleanup] ID={id_conexion}: {e}")

            # NUEVO: cierre con timeout forzado, evita que un hilo quede
            # atrapado para siempre si la conexión externa quedó en un
            # estado ambiguo (p. ej. tras un deadlock).
            _cerrar_con_timeout(conn_externa, nombre=f"conn_externa ID={id_conexion}", emit_log=self._emit_log)

            if lock_adquirido and conn:
                try:
                    cur = conn.cursor()
                    fallos = self._fallos_consecutivos.get(id_conexion, 0)

                    # NUEVO: backoff fijo tras varios fallos consecutivos,
                    # en vez de exponencial creciente sin techo práctico.
                    if fallos == 0:
                        minutos_espera = frecuencia_min
                    elif fallos <= INTENTOS_ANTES_DE_BACKOFF_LARGO:
                        minutos_espera = frecuencia_min
                    else:
                        minutos_espera = BACKOFF_LARGO_MINUTOS

                    proximo = ahora + timedelta(minutes=minutos_espera)

                    cur.execute("""
                        UPDATE sync_control SET ejecutando = 0, inicio_ejecucion = NULL, ultimo_heartbeat = NULL,
                            ultimo_sync = ?, proximo_sync = ? WHERE id_conexion = ?
                    """, ahora, proximo, id_conexion)
                    conn.commit()

                    self._emit_log(f"[Finalizado] ID={id_conexion} | Estado: {'OK' if total_filas_insertadas >= 0 else 'FALLIDO'} | Proc: {total_filas_procesadas} | Ins: {total_filas_insertadas} | Fallos: {fallos} | Próximo: {proximo:%H:%M:%S} ({minutos_espera} min)")
                except Exception as e:
                    logger.error(f"Error liberando lock ID={id_conexion}: {e}", exc_info=True)

            # NUEVO: cierre con timeout forzado también para la conexión central
            _cerrar_con_timeout(conn, nombre=f"conn_central ID={id_conexion}", emit_log=self._emit_log)

    def _obtener_grupos_externos(self, conn_externa, consultagrupos):
        cur = conn_externa.cursor()
        _set_query_timeout(cur, QUERY_TIMEOUT_SEG)
        cur.execute(consultagrupos)
        return [(row[0], row[1]) for row in cur.fetchall()]

    def _consultar_bd_externa_paginado(self, conn_externa, consulta, ultimoid, batcher_fetch):
        cur = conn_externa.cursor()
        _set_query_timeout(cur, QUERY_TIMEOUT_SEG)
        cur.execute("SET LOCK_TIMEOUT 30000;")

        # NUEVO: retry específico ante deadlock (40001) en vez de fallar
        # inmediatamente y abortar todo el ciclo de sincronización.
        _ejecutar_con_retry_deadlock(cur, consulta, (ultimoid,), emit_log=self._emit_log)

        while True:
            if not self._corriendo:
                break
            cur.arraysize = batcher_fetch.tamano
            inicio = time.monotonic()
            try:
                lote = cur.fetchmany(batcher_fetch.tamano)
            except pyodbc.OperationalError as e:
                self._emit_error(f"[Fetch Error] Error leyendo lote: {e}")
                break
            duracion = time.monotonic() - inicio
            if not lote:
                break
            batcher_fetch.registrar(duracion, len(lote))
            yield [tuple(r) for r in lote]

    def _asegurar_componente(self, conn, cur, id_proyecto, nombre_componente):
        cur.execute("SELECT id_componente FROM componentes WHERE id_proyecto = ? AND nombre_componente = ?", id_proyecto, nombre_componente)
        row = cur.fetchone()
        if row:
            return row[0]
        cur.execute("INSERT INTO componentes (id_proyecto, nombre_componente, estado_componente) OUTPUT INSERTED.id_componente VALUES (?, ?, 1)", id_proyecto, nombre_componente)
        nuevo_id = cur.fetchone()[0]
        conn.commit()
        return nuevo_id

    def _asegurar_tabla_prismas(self, conn, cur, nombretabla):
        cur.execute(f"""
            IF OBJECT_ID('{nombretabla}', 'U') IS NULL
            CREATE TABLE {nombretabla} (
                id_prisma INT IDENTITY(1,1) NOT NULL PRIMARY KEY, state_prisma INT NOT NULL DEFAULT 1, estado_prisma INT NOT NULL DEFAULT 1,
                nombre_prisma VARCHAR(255) NOT NULL, perfil_prisma VARCHAR(255), hora_prisma DATETIME2(0) NOT NULL,
                angulo_horizontal VARCHAR(50), angulo_vertical VARCHAR(50), distancia_prisma FLOAT DEFAULT 0,
                tipoppm_prisma VARCHAR(50), ppm_prisma FLOAT DEFAULT 0, presion_prisma FLOAT DEFAULT 0,
                temperatura_prisma FLOAT DEFAULT 0, constante_prisma FLOAT DEFAULT 0, este_target FLOAT NOT NULL,
                norte_target FLOAT NOT NULL, elevacion_target FLOAT NOT NULL, altura_reflector FLOAT DEFAULT 0,
                altura_instrumento FLOAT DEFAULT 0, este_estacion FLOAT DEFAULT 0, norte_estacion FLOAT DEFAULT 0,
                altura_estacion FLOAT DEFAULT 0, medicion_prisma FLOAT DEFAULT 0, diferencia_tiempocorto FLOAT DEFAULT 0,
                diferencia_tiempolargo FLOAT DEFAULT 0, diferencia_limitevelocidad FLOAT DEFAULT 0,
                distancia_horizontal FLOAT DEFAULT 0, diferencia_atipica FLOAT DEFAULT 0, desplaza_longitudinal FLOAT DEFAULT 0,
                desplaza_transversal FLOAT DEFAULT 0, desplaza_altura FLOAT DEFAULT 0, grupo_puntos VARCHAR(255)
            );
        """)
        idx_name = f"UX_{nombretabla}_dedupe"
        cur.execute(f"""
            IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = '{idx_name}' AND object_id = OBJECT_ID('{nombretabla}'))
            CREATE UNIQUE INDEX {idx_name} ON {nombretabla} (nombre_prisma, hora_prisma, grupo_puntos);
        """)
        conn.commit()

    def _nombre_staging(self, nombretabla):
        return f"#stg_{nombretabla}"

    def _asegurar_staging(self, cur, nombretabla):
        staging = self._nombre_staging(nombretabla)
        cur.execute(f"""
            IF OBJECT_ID('tempdb..{staging}') IS NOT NULL DROP TABLE {staging};
            CREATE TABLE {staging} (
                nombre_prisma VARCHAR(255), hora_prisma DATETIME2(0), angulo_horizontal VARCHAR(50), angulo_vertical VARCHAR(50),
                distancia_prisma FLOAT, presion_prisma FLOAT, temperatura_prisma FLOAT, este_target FLOAT, norte_target FLOAT,
                elevacion_target FLOAT, distancia_horizontal FLOAT, desplaza_longitudinal FLOAT, desplaza_transversal FLOAT,
                desplaza_altura FLOAT, grupo_puntos VARCHAR(255)
            );
        """)

    def _limpiar_staging(self, cur, nombretabla):
        staging = self._nombre_staging(nombretabla)
        cur.execute(f"DROP TABLE IF EXISTS {staging};")

    def _insertar_en_bd_central(self, conn, cur, datos, instrumento, id_proyecto, nombretabla, batcher_insert):
        if instrumento != "PRISMAS" or not nombretabla or not datos:
            return 0, set()
        vistos_en_lote = set()
        registros = []
        nombres_unicos = set()

        for fila in datos:
            nombre_prisma = fila[2]
            epoch = fila[3]
            epoch_dt = epoch.replace(microsecond=0) if isinstance(epoch, datetime) else datetime.strptime(str(epoch)[:19].replace('T', ' '), '%Y-%m-%d %H:%M:%S')
            grupo = fila[16] if fila[16] is not None else ''
            clave = (nombre_prisma, epoch_dt, grupo)
            if clave in vistos_en_lote:
                continue
            vistos_en_lote.add(clave)
            nombres_unicos.add(nombre_prisma)

            registros.append((
                nombre_prisma, epoch_dt, str(fila[4]) if fila[4] is not None else '', str(fila[5]) if fila[5] is not None else '',
                float(fila[6]) if fila[6] is not None else 0.0, float(fila[7]) if fila[7] is not None else 0.0,
                float(fila[8]) if fila[8] is not None else 0.0, float(fila[9]) if fila[9] is not None else 0.0,
                float(fila[10]) if fila[10] is not None else 0.0, float(fila[11]) if fila[11] is not None else 0.0,
                float(fila[12]) if fila[12] is not None else 0.0, float(fila[13]) if fila[13] is not None else 0.0,
                float(fila[14]) if fila[14] is not None else 0.0, float(fila[15]) if fila[15] is not None else 0.0, grupo
            ))

        if not registros:
            return 0, set()
        insertadas = self._insertar_lotes_con_staging(conn, cur, nombretabla, registros, batcher_insert)
        return insertadas, nombres_unicos

    def _insertar_lotes_con_staging(self, conn, cur, nombretabla, registros, batcher_insert):
        staging = self._nombre_staging(nombretabla)
        cur.execute(f"TRUNCATE TABLE {staging};")

        insert_staging = f"""
            INSERT INTO {staging} (nombre_prisma, hora_prisma, angulo_horizontal, angulo_vertical, distancia_prisma,
            presion_prisma, temperatura_prisma, este_target, norte_target, elevacion_target, distancia_horizontal,
            desplaza_longitudinal, desplaza_transversal, desplaza_altura, grupo_puntos)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        i = 0
        n = len(registros)
        while i < n:
            tam = batcher_insert.tamano
            sub_lote = registros[i:i + tam]
            inicio = time.monotonic()
            cur.executemany(insert_staging, sub_lote)
            duracion = time.monotonic() - inicio
            batcher_insert.registrar(duracion, len(sub_lote))
            i += tam

        # Insertar a tabla final usando LEFT JOIN
        cur.execute(f"""
            INSERT INTO {nombretabla} (state_prisma, estado_prisma, nombre_prisma, hora_prisma, angulo_horizontal, angulo_vertical,
                distancia_prisma, presion_prisma, temperatura_prisma, este_target, norte_target, elevacion_target,
                distancia_horizontal, desplaza_longitudinal, desplaza_transversal, desplaza_altura, grupo_puntos)
            SELECT 1, 1, s.nombre_prisma, s.hora_prisma, s.angulo_horizontal, s.angulo_vertical, s.distancia_prisma,
                   s.presion_prisma, s.temperatura_prisma, s.este_target, s.norte_target, s.elevacion_target,
                   s.distancia_horizontal, s.desplaza_longitudinal, s.desplaza_transversal, s.desplaza_altura, s.grupo_puntos
            FROM {staging} s
            LEFT JOIN {nombretabla} t
                ON t.nombre_prisma = s.nombre_prisma AND t.hora_prisma = s.hora_prisma AND t.grupo_puntos = s.grupo_puntos
            WHERE t.nombre_prisma IS NULL;
        """)

        # Contar filas insertadas manualmente
        total_insertadas = len(registros)
        conn.commit()
        return total_insertadas

    def _registrar_equipos_zona_batch(self, conn, cur, nombres_por_componente, nombretabla, tipo_equipo):
        pares = [(id_comp, nombre) for id_comp, nombres in nombres_por_componente.items() for nombre in nombres]
        if not pares:
            return

        staging = "#stg_equipos"
        cur.execute(f"IF OBJECT_ID('tempdb..{staging}') IS NOT NULL DROP TABLE {staging};")
        cur.execute(f"CREATE TABLE {staging} (id_componente INT, nombre_equipo VARCHAR(255));")
        cur.executemany(f"INSERT INTO {staging} (id_componente, nombre_equipo) VALUES (?, ?)", pares)

        cur.execute(f"""
            INSERT INTO instrumentacion (id_componente, tipo_equipo, nombre_equipo, tabla_equipo, estado_instrumentacion)
            SELECT DISTINCT s.id_componente, ?, s.nombre_equipo, ?, 1
            FROM {staging} s
            WHERE NOT EXISTS (SELECT 1 FROM instrumentacion i WHERE i.id_componente = s.id_componente AND i.nombre_equipo = s.nombre_equipo);
        """, tipo_equipo, nombretabla)

        nuevos = cur.rowcount if cur.rowcount and cur.rowcount > 0 else 0
        cur.execute(f"DROP TABLE IF EXISTS {staging};")
        conn.commit()

        if nuevos > 0:
            self._emit_log(f"[Equipos] {nuevos} equipo(s) nuevo(s) | Tipo: {tipo_equipo} | Tabla: {nombretabla}")