import os
import pyodbc
from dotenv import load_dotenv

# Carga las variables del archivo .env al iniciar este script
# Asegúrate de que el archivo .env esté en la raíz de tu proyecto
load_dotenv()

class Connection:

    @staticmethod
    def connectionDB():
        try:
            # 1. Recuperar credenciales del archivo .env
            server = os.getenv("SQL_SERVER")
            port = os.getenv("SQL_PORT", "1433")
            database = os.getenv("SQL_DATABASE")
            username = os.getenv("SQL_USER")
            password = os.getenv("SQL_PASSWORD")
            # Validación simple: si no hay servidor o base de datos definida, retornamos None
            if not server or not database:
                print("Error: No se encontraron las variables de entorno para SQL Server.")
                return None
            # 2. Definir el Driver (asegúrate de tener instalado el ODBC Driver 17)
            driver = '{ODBC Driver 17 for SQL Server}'
            # 3. Construir la cadena de conexión
            # Nota: SQL Server usa coma para separar IP y Puerto (IP,Puerto)
            connection_string = (
                f'DRIVER={driver};'
                f'SERVER={server},{port};'
                f'DATABASE={database};'
                f'UID={username};'
                f'PWD={password};'
                'TrustServerCertificate=yes;' # Importante para evitar errores SSL locales
            )
            # 4. Intentar conectar
            conn = pyodbc.connect(connection_string, timeout=3)
            return conn
        except pyodbc.Error as e:
            # Puedes imprimir el error en consola para depurar si falla
            print(f"Error de conexión SQL Server: {e}")
            return None
        except Exception as e:
            print(f"Error general: {e}")
            return None
    