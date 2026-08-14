import os
import logging
import pyodbc
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("Connection")

# SQLSTATEs que indican error de autenticación/autorización (no debe reintentarse
# automáticamente con las mismas credenciales, ya que insistir puede contribuir
# a un bloqueo de la cuenta en el servidor).
AUTH_SQLSTATES = {'28000', '42000'}

DEFAULT_TIMEOUT_SEG = 8


class ConnectionAuthError(Exception):
    """Error de autenticación/autorización al conectar a SQL Server.

    Se lanza en vez de devolver None para que el código que llama pueda
    distinguir este caso (credenciales inválidas, cuenta bloqueada, etc.)
    de un problema de red/timeout transitorio, y así evitar reintentos
    automáticos que agraven un posible bloqueo de cuenta en el servidor.
    """
    pass


def _escapar_password_odbc(password: str) -> str:
    """Envuelve el password en llaves y escapa llaves internas, para que
    caracteres especiales (; = etc.) dentro del password no rompan la
    cadena de conexión ODBC."""
    if password is None:
        return ''
    return '{' + str(password).replace('}', '}}') + '}'

class CancelableConnection:
    def __init__(self, pyodbc_conn, request_id):
        object.__setattr__(self, '_conn', pyodbc_conn)
        object.__setattr__(self, '_request_id', request_id)

    def cursor(self):
        cur = self._conn.cursor()
        try:
            from services.queries.query_registry import query_registry
            query_registry.attach_cursor(self._request_id, cur)
        except Exception:
            pass
        return cur

    def close(self):
        try:
            self._conn.close()
        except Exception:
            pass

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def __getattr__(self, name):
        return getattr(self._conn, name)

    def __setattr__(self, name, value):
        if name in ('_conn', '_request_id'):
            object.__setattr__(self, name, value)
        else:
            setattr(self._conn, name, value)
                   
class Connection:

    @staticmethod
    def connectionDB(timeout: int = DEFAULT_TIMEOUT_SEG):
        """Conecta a la BD central usando las credenciales del .env.
        Devuelve la conexión pyodbc si tiene éxito, o None ante un error
        no relacionado a autenticación (por ejemplo, timeout de red o
        servidor no disponible). Ante un error de autenticación, lanza
        ConnectionAuthError en vez de devolver None, para que el llamador
        pueda manejarlo explícitamente y evitar reintentos ciegos.
        """
        try:
            server = os.getenv("SQL_SERVER")
            port = os.getenv("SQL_PORT", "1433")
            database = os.getenv("SQL_DATABASE")
            username = os.getenv("SQL_USER")
            password = os.getenv("SQL_PASSWORD")

            if not server or not database:
                logger.error("No se encontraron las variables de entorno para SQL Server "
                           "(SQL_SERVER / SQL_DATABASE).")
                return None

            # Detectar el mejor driver disponible
            available_drivers = pyodbc.drivers()
            driver_priority = [
                'ODBC Driver 18 for SQL Server',
                'ODBC Driver 17 for SQL Server',
                'ODBC Driver 13 for SQL Server',
                'SQL Server Native Client 11.0',
                'SQL Server'
            ]
            driver = None
            for preferred_driver in driver_priority:
                if preferred_driver in available_drivers:
                    driver = f'{{{preferred_driver}}}'
                    break

            if not driver:
                logger.error("No se encontró un driver compatible de SQL Server. "
                           f"Drivers disponibles: {available_drivers}")
                return None

            connection_string = (
                f'DRIVER={driver};'
                f'SERVER={server},{port};'
                f'DATABASE={database};'
                f'UID={username};'
                f'PWD={_escapar_password_odbc(password)};'
                'TrustServerCertificate=yes;'
                'Encrypt=yes;'
                f'Connection Timeout={timeout};'
                'KeepAliveInterval=30;KeepAliveCount=5;'
            )

            conn = pyodbc.connect(connection_string, timeout=timeout)

            try:
                from services.queries.query_context import get_active_request
                from services.queries.query_registry import query_registry

                active_request_id = get_active_request()
                if active_request_id:
                    cur = conn.cursor()
                    cur.execute("SELECT @@SPID")
                    spid = cur.fetchone()[0]
                    cur.close()

                    query_registry.attach_connection(active_request_id, conn, spid)
                    logger.info(f"Conexión registrada para consulta: "
                                f"request={active_request_id} spid={spid}")

                    # DEVOLVER EL WRAPPER en vez de la conexión directa
                    return CancelableConnection(conn, active_request_id)
            except Exception as reg_err:
                logger.warning(f"No se pudo registrar la consulta: {reg_err}")

            return conn

        except pyodbc.Error as e:
            sqlstate = e.args[0] if e.args else ''
            mensaje = str(e)
            if sqlstate in AUTH_SQLSTATES or 'Login failed' in mensaje:
                logger.error(f"[AUTH] Credenciales inválidas o sin permiso al conectar a BD central: {mensaje}")
                raise ConnectionAuthError(mensaje) from e
            logger.error(f"Error de conexión SQL Server ({sqlstate}): {mensaje}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Error general al conectar a SQL Server: {e}", exc_info=True)
            return None