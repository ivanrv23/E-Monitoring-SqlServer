from services.security.apis.conexiones.conexion import Connection
from sqlite3 import Error
class InstrumentacionModel:
    def mdlObtenerInstrumentacionComponente(id_componente,tipo_equipo):
        try:
            conn = Connection.connectionDB()
            sql = """SELECT * FROM instrumentacion WHERE estado_instrumentacion=1 AND id_componente=? AND tipo_equipo=?;"""
            cur = conn.cursor()
            cur.execute(sql, (id_componente,tipo_equipo))
            results = cur.fetchall()
            if results:
                return results
            else:
                return None
        except Error as e:
            print("Error al obtener componentes:", e)
            return None  
        finally:
            if conn:
                conn.close()
    