from sqlite3 import Error
from services.security.apis.conexiones.conexion import Connection

class UserModel:
      
    def mdlObtenerInfoLicencia():
        conn = Connection.connectionDB()
        sql = """SELECT * FROM licencias;"""
        try:
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al obtener licencia: " + str(e))
            return None
        finally:
            if conn:
                conn.close()