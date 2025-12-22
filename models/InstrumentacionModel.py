from services.security.apis.conexiones.connection import Connection

class InstrumentacionModel:
    
    @staticmethod
    def mdlObtenerInstrumentacionComponente(id_componente, tipo_equipo):
        conn = None
        try:
            conn = Connection.connectionDB()
            # La sintaxis es estándar y compatible con SQL Server
            sql = """SELECT * FROM instrumentacion WHERE estado_instrumentacion=1 AND id_componente=? AND tipo_equipo=?;"""
            cur = conn.cursor()
            cur.execute(sql, (id_componente, tipo_equipo))
            results = cur.fetchall()
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al obtener componentes:", e)
            return None  
        finally:
            if conn:
                conn.close()