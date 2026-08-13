# services/queries/query_context.py

"""
Contexto de consulta por hilo.

Permite saber, desde cualquier parte del código, si el hilo actual
está ejecutando una consulta de gráfico y cuál es su request_id.

Esto es necesario porque los modelos (DesplazamientoModel, etc.)
abren conexiones internamente sin recibir el request_id como parámetro.
"""

import threading

# Almacena el request_id activo por hilo.
# Clave: identificador del hilo. Valor: request_id (str) o None.
_thread_local = threading.local()


def set_active_request(request_id: str):
    """
    Marca el hilo actual como ejecutando una consulta con el request_id dado.
    Se llama ANTES de invocar al controller/modelo.
    """
    _thread_local.request_id = request_id


def get_active_request() -> str | None:
    """
    Devuelve el request_id activo del hilo actual, o None si no hay ninguno.
    Se llama DESDE Connection.connectionDB() para registrar la conexión.
    """
    return getattr(_thread_local, 'request_id', None)


def clear_active_request():
    """
    Limpia el contexto del hilo actual.
    Se llama DESPUÉS de que la consulta termina (éxito, error o cancelación).
    """
    if hasattr(_thread_local, 'request_id'):
        _thread_local.request_id = None