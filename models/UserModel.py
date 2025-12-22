from services.security.apis.conexiones.conexion import Connection

class UserModel:
      
    @staticmethod
    def mdlObtenerInfoLicencia():
        # Se define conn fuera del try para asegurar que finally pueda acceder si falla la conexión
        conn = None
        # En SQL Server se usa TOP 1 en lugar de LIMIT 1
        sql = """SELECT TOP 1 * FROM licencias;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener licencia: " + str(e))
            return None
        finally:
            if conn:
                conn.close()