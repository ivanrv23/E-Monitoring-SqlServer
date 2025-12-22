import sqlite3
from sqlite3 import Error
import os
from utils.common.rutasarchivos import resource_path

class Conexion:

    @staticmethod
    def conexionDB():
        try:
            # Usar resource_path para obtener la ruta de la base de datos
            db_path = resource_path('services/database/databaseeigha.db')
            # Verificar si la base de datos existe
            if not os.path.exists(db_path):
                return None
            # Conectar a la base de datos SQLite usando la ruta completa
            conn = sqlite3.connect(db_path)
            return conn
        except Error as e:
            return None
        except Exception as e:
            return None
    