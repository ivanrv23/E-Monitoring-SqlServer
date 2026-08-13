# services/queries/query_registry.py

"""
Registro central de consultas activas.

Cada consulta de gráfico que abre una conexión se registra aquí.
El registro permite:
  - Cancelar la consulta (connection.cancel()).
  - Matar la consulta (KILL spid) si es necesario.
  - Saber cuántas consultas hay activas.
"""

import threading
import time
from typing import Dict, Optional

from services.queries.query_config import log_query


class QuerySession:
    """Información de una consulta activa."""

    def __init__(self, request_id: str, view_name: str):
        self.request_id = request_id
        self.view_name = view_name
        self.connection = None          # pyodbc.Connection
        self.cursor = None              # pyodbc.Cursor (NUEVO)
        self.spid: Optional[int] = None # SQL Server session ID
        self.created_at = time.monotonic()
        self.cancel_requested = False
        self.cancel_requested_at: Optional[float] = None
        self.state = 'RUNNING'

    def __repr__(self):
        return (f"<QuerySession request={self.request_id} spid={self.spid} "
                f"state={self.state} view={self.view_name}>")


class QueryRegistry:
    """
    Registro global de consultas activas.
    Singleton: una sola instancia para toda la aplicación.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._sessions = {}
                cls._instance._registry_lock = threading.Lock()
            return cls._instance

    # ── Registro ──────────────────────────────

    def register(self, request_id: str, view_name: str) -> QuerySession:
        """
        Registra una nueva consulta activa.
        Se llama DESDE Connection.connectionDB() cuando hay contexto activo.
        """
        session = QuerySession(request_id, view_name)
        with self._registry_lock:
            # Si ya existe una sesión con ese request_id, reemplazarla
            self._sessions[request_id] = session
        log_query(f"Registrada: {session}")
        return session

    def attach_cursor(self, request_id: str, cursor):
        """
        Asocia el cursor pyodbc a la sesión registrada.
        Se llama DESDE CancelableConnection.cursor() cada vez que
        se crea un cursor en una conexión registrada.
        """
        with self._registry_lock:
            session = self._sessions.get(request_id)
            if session:
                session.cursor = cursor
                log_query(f"Cursor asociado: request={request_id}")
            
    def attach_connection(self, request_id: str, connection, spid: int):
        """
        Asocia la conexión pyodbc y su SPID a la sesión registrada.
        Se llama DESDE Connection.connectionDB() después de abrir la conexión.
        """
        with self._registry_lock:
            session = self._sessions.get(request_id)
            if session:
                session.connection = connection
                session.spid = spid
                log_query(f"Conexión asociada: request={request_id} spid={spid}")

    def unregister(self, request_id: str, final_state: str = 'FINISHED'):
        """
        Elimina la sesión del registro y marca su estado final.
        Se llama cuando la consulta termina (éxito, error, cancelación).
        """
        with self._registry_lock:
            session = self._sessions.pop(request_id, None)
            if session:
                session.state = final_state
                log_query(f"Desregistrada: {session}")

    # ── Cancelación ───────────────────────────

    def request_cancel(self, request_id: str):
        """
        Marca una consulta como 'cancelación solicitada'.
        No intenta cancelarla todavía, solo marca el flag.
        """
        with self._registry_lock:
            session = self._sessions.get(request_id)
            if session:
                session.cancel_requested = True
                session.cancel_requested_at = time.monotonic()
                session.state = 'CANCEL_REQUESTED'
                log_query(f"Cancelación solicitada: {session}")

    def is_cancel_requested(self, request_id: str) -> bool:
        """
        Devuelve True si la consulta tiene cancelación solicitada.
        Se llama DESDE el worker para saber si debe abortar.
        """
        with self._registry_lock:
            session = self._sessions.get(request_id)
            return session.cancel_requested if session else False

    def try_cancel(self, request_id: str) -> bool:
        """
        Intenta cancelar la consulta en tres niveles:
        1. cursor.cancel() - señal ODBC al servidor
        2. conn.close()    - cierre forzado de conexión
        Devuelve True si algún nivel funcionó.
        """
        with self._registry_lock:
            session = self._sessions.get(request_id)
            if not session:
                return False

            session.cancel_requested = True
            session.cancel_requested_at = time.monotonic()
            session.state = 'CANCEL_REQUESTED'

            cursor = session.cursor
            conn = session.connection

        # Nivel 1: cursor.cancel() (thread-safe según documentación pyodbc)
        if cursor is not None:
            try:
                cursor.cancel()
                log_query(f"cursor.cancel() enviado: request={request_id}")
                return True
            except Exception as e:
                log_query(f"cursor.cancel() falló: {e}")

        # Nivel 2: conn.close() (interrumpe cualquier operación en curso)
        if conn is not None:
            try:
                conn.close()
                log_query(f"conn.close() enviado: request={request_id}")
                return True
            except Exception as e:
                log_query(f"conn.close() falló: {e}")

        log_query(f"No se pudo cancelar ODBC: request={request_id}")
        return False

    # ── Consulta de estado ────────────────────

    def get_session(self, request_id: str) -> Optional[QuerySession]:
        """Devuelve la sesión activa con ese request_id, o None."""
        with self._registry_lock:
            return self._sessions.get(request_id)

    def get_all_sessions(self) -> list:
        """Devuelve una copia de todas las sesiones activas."""
        with self._registry_lock:
            return list(self._sessions.values())

    def get_spid(self, request_id: str) -> Optional[int]:
        """Devuelve el SPID de la sesión, o None."""
        with self._registry_lock:
            session = self._sessions.get(request_id)
            return session.spid if session else None

    def active_count(self) -> int:
        """Devuelve cuántas consultas hay activas."""
        with self._registry_lock:
            return len(self._sessions)


# Instancia global del registro.
query_registry = QueryRegistry()