import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()

class Connection:

    @staticmethod
    def connectionDB():
        try:
            server = os.getenv("SQL_SERVER")
            port = os.getenv("SQL_PORT", "1433")
            database = os.getenv("SQL_DATABASE")
            username = os.getenv("SQL_USER")
            password = os.getenv("SQL_PASSWORD")
            if not server or not database:
                print("Error: No se encontraron las variables de entorno para SQL Server.")
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
                print("Error: No se encontró un driver compatible de SQL Server.")
                return None
            # Construir la cadena de conexión
            connection_string = (
                f'DRIVER={driver};'
                f'SERVER={server},{port};'
                f'DATABASE={database};'
                f'UID={username};'
                f'PWD={password};'
                'TrustServerCertificate=yes;'
                'Encrypt=yes;'  # Recomendado para ODBC Driver 18
            )
            # Intentar conectar
            conn = pyodbc.connect(connection_string, timeout=5)
            return conn
        except pyodbc.Error as e:
            print(f"Error de conexión SQL Server: {e}")
            return None
        except Exception as e:
            print(f"Error general: {e}")
            return None
    