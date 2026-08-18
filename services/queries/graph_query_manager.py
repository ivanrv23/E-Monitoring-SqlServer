# services/queries/graph_query_manager.py

"""
Manager de consultas de gráfico.

Coordina el ciclo de vida de cada consulta:
  1. Genera un request_id único.
  2. Cancela la consulta anterior si existe.
  3. Registra la nueva consulta.
  4. Proporciona métodos para verificar cancelación y finalizar.
"""

import uuid
import time
import threading
import pyodbc
from typing import Optional

from services.queries.query_registry import query_registry
from services.queries.query_config import (
    ENABLE_QUERY_KILL,
    CANCEL_GRACE_SEG,
    CONNECTION_TIMEOUT_SEG,
    log_query,
)


class GraphQueryManager:
    """
    Manager de consultas para una vista específica.
    Cada vista (DesplazamientoView, VelocidadView) debe tener su propia instancia.
    """

    def __init__(self, view_name: str):
        self.view_name = view_name
        self.current_request_id: Optional[str] = None
        self._lock = threading.Lock()

    # ── Ciclo de vida ─────────────────────────

    def start_request(self) -> str:
        """
        Inicia una nueva consulta:
          1. Cancela la consulta anterior si existe.
          2. Genera un request_id nuevo.
          3. Registra la nueva consulta.
          4. Devuelve el request_id.
        """
        with self._lock:
            # Cancelar la consulta anterior
            if self.current_request_id:
                self.cancel_previous()

            # Generar nuevo request_id
            new_id = str(uuid.uuid4())[:8]
            self.current_request_id = new_id

            # Registrar en el registro global
            query_registry.register(new_id, self.view_name)

            log_query(f"[{self.view_name}] Nueva consulta: {new_id}")
            return new_id

    def cancel_previous(self):
        """
        Cancela la consulta anterior de forma no bloqueante.
        Niveles:
        1. cursor.cancel() + conn.close() (via query_registry.try_cancel)
        2. KILL spid como último recurso (hilo separado, nunca bloquea)
        """
        prev_id = self.current_request_id
        if not prev_id:
            return

        log_query(f"[{self.view_name}] Cancelando anterior: {prev_id}")

        # Intentar cancelación ODBC (cursor.cancel + conn.close)
        cancelled = query_registry.try_cancel(prev_id)

        if not cancelled:
            log_query(f"[{self.view_name}] ODBC falló, programando KILL: {prev_id}")

        # Si KILL está activado, lanzar hilo de respaldo.
        # Se lanza SIEMPRE (aunque ODBC haya funcionado) porque el hilo
        # verifica si la sesión ya terminó antes de hacer KILL.
        if ENABLE_QUERY_KILL:
            threading.Thread(
                target=self._kill_if_needed,
                args=(prev_id,),
                daemon=True,
                name=f"Kill-{prev_id}"
            ).start()
            
    def _kill_if_needed(self, request_id: str):
        """
        Hilo de respaldo: espera CANCEL_GRACE_SEG y, si la consulta
        sigue viva, intenta matarla con KILL.
        
        NUNCA lanza excepciones. Si KILL falla (sin permisos, error de red,
        etc.), simplemente loguea y marca la sesión como abandonada.
        """
        time.sleep(CANCEL_GRACE_SEG)

        session = query_registry.get_session(request_id)
        if not session:
            return  # Ya terminó y fue desregistrada

        if not session.cancel_requested:
            return  # No fue cancelada

        spid = session.spid
        if not spid:
            return

        log_query(f"[{self.view_name}] Intentando KILL spid={spid} request={request_id}")

        try:
            # Abrir una conexión de control independiente.
            # En este hilo NO hay request activo, así que connectionDB()
            # devuelve una conexión pyodbc normal (sin wrapper).
            from services.security.apis.conexiones.connection import Connection
            ctrl_conn = Connection.connectionDB(timeout=5)
            if ctrl_conn:
                cur = ctrl_conn.cursor()
                cur.execute(f"KILL {spid}")
                cur.close()
                ctrl_conn.close()

                query_registry.unregister(request_id, 'KILLED')
                log_query(f"[{self.view_name}] KILL exitoso: spid={spid}")
        except Exception as e:
            # KILL falló. Posibles causas:
            #   - Sin permisos ALTER ANY CONNECTION en el servidor
            #   - El SPID ya terminó antes del KILL
            #   - Error de red al abrir la conexión de control
            # En cualquier caso, NO detener el programa.
            log_query(f"[{self.view_name}] KILL falló (spid={spid}): {e}")
            query_registry.unregister(request_id, 'ABANDONED')
            
    # ── Verificación durante la ejecución ─────

    def is_cancelled(self, request_id: str) -> bool:
        """
        Devuelve True si la consulta fue cancelada.
        Se llama DESDE el worker durante la ejecución.
        """
        return query_registry.is_cancel_requested(request_id)

    # ── Finalización ──────────────────────────

    def finish_request(self, request_id: str, state: str = 'FINISHED'):
        """
        Marca la consulta como finalizada y la desregistra.
        Se llama cuando el worker termina (éxito, error o cancelación).
        """
        query_registry.unregister(request_id, state)

        with self._lock:
            if self.current_request_id == request_id:
                self.current_request_id = None

        log_query(f"[{self.view_name}] Finalizada: {request_id} -> {state}")

    def is_current(self, request_id: str) -> bool:
        """
        Devuelve True si el request_id dado sigue siendo la consulta actual.
        Se llama ANTES de emitir datos a la interfaz para descartar
        resultados obsoletos.
        """
        with self._lock:
            return self.current_request_id == request_id
class VisorGraphQueryManager(GraphQueryManager):
    def cancel_previous(self):
        """
        Cancelación específica para el Visor 3D (Soft Cancel).
        NO usa cursor.cancel() ni conn.close() porque PrismaController
        hace múltiples consultas en bucle y cerrar la conexión corrompe
        el pool de pyodbc, causando errores HY008 y bloqueos.
        Solo marca el flag para que el Worker y el Controlador aborten limpiamente.
        """
        prev_id = self.current_request_id
        if not prev_id:
            return
        
        session = query_registry.get_session(prev_id)
        if session:
            session.cancel_requested = True
            session.cancel_requested_at = time.monotonic()
            session.state = 'CANCEL_REQUESTED'
            log_query(f"[{self.view_name}] Cancelación solo por flag (sin ODBC kill): {prev_id}")

desplazamiento_query_manager = GraphQueryManager("Desplazamiento")
velocidad_query_manager = GraphQueryManager("Velocidad")
visor_query_manager = VisorGraphQueryManager("Visor3D")