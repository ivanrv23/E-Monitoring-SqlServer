# services/queries/query_config.py

"""
Configuración central del sistema de consultas cancelables.
Ajustar estos valores según las necesidades del proyecto.
"""

# ─────────────────────────────────────────────
# TIMEOUTS DE CONSULTA (segundos)
# ─────────────────────────────────────────────

# Tiempo máximo que una consulta de gráfico puede estar ejecutándose.
# Si se supera, se intenta cancelar automáticamente.
QUERY_TIMEOUT_SEG = 180

# Tiempo máximo que una consulta puede esperar un lock de SQL Server.
# Si el SyncManager está insertando y bloquea la tabla, la consulta
# de la interfaz esperará como máximo este tiempo antes de fallar.
LOCK_TIMEOUT_MS = 30000

# Tiempo máximo para abrir una conexión nueva.
CONNECTION_TIMEOUT_SEG = 8


# ─────────────────────────────────────────────
# CANCELACIÓN Y KILL
# ─────────────────────────────────────────────

# Activar el uso de KILL para cancelar consultas en SQL Server.
# Si es False, solo se usa connection.cancel() y timeouts.
ENABLE_QUERY_KILL = False

# Tiempo (segundos) que se espera después de solicitar cancelación
# antes de considerar KILL.
CANCEL_GRACE_SEG = 5

# Intervalo (segundos) entre revisiones del limpiador de zombies.
REAPER_INTERVAL_SEG = 3


# ─────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────

# Activar logs detallados del sistema de consultas.
DEBUG_QUERIES = False


def log_query(msg: str):
    """Imprime un log si DEBUG_QUERIES está activo."""
    if DEBUG_QUERIES:
        print(f"[QuerySystem] {msg}")