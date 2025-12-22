from sqlite3 import Error
from services.security.apis.conexiones.conexion import Connection

class EstratoModel:

    def mdlGuardarEstratos(proyectoid,componente_id, data):
        conn = Connection.connectionDB()
        sql = f"""INSERT INTO estratos_instrumentacion (id_proyecto,id_componente, nombre_estrato, color_estrato, rango_min, rango_max) VALUES (?, ?, ?, ?, ?, ?);"""
        try:
            cur = conn.cursor()
            for item in data:
                cur.execute(sql, (proyectoid,componente_id, item['nombre'], item['color'], item['rango_minimo'],item['rango_maximo']))
            conn.commit()
            return True
        except Exception as e:
            print("Error al registrar estrato:", e)
            return False
        finally:
            if conn:
                conn.close()
                
    def mdlActualizarEstratos(id_estrato, nombre, color, rango_min,rango_max):
        conn = Connection.connectionDB()
        sql = f"""UPDATE estratos_instrumentacion SET nombre_estrato = ?, color_estrato = ?, rango_min = ? , rango_max = ? WHERE id_estrato = ?;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (nombre, color, rango_min,rango_max, id_estrato))
            conn.commit()
            return True
        except Exception as e:
            print("Error al actualizar estrato:", e)
            return False
        finally:
            if conn:
                conn.close()
                
    def mdlObtenerEstratosInstrumentacion(proyectoid,componente_id):
        try:
            conn = Connection.connectionDB()
            sql = f"""SELECT * FROM estratos_instrumentacion WHERE id_proyecto=? AND id_componente = ?"""
            
            cur = conn.cursor()
            cur.execute(sql, (proyectoid,componente_id))
            result = cur.fetchall() 
            if result:
                return result
            else:
                return None
        except Error as e:
            print("Error al obtener estratos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlEliminarEstrato(estrato_id):
        conn = Connection.connectionDB()
        sql = f"""DELETE FROM estratos_instrumentacion WHERE id_estrato = ?"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (estrato_id,))
            conn.commit()
            if cur.rowcount > 0:
                return True
            else:
                return False
        except Error as e:
            print("Error al eliminar estratos: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlObtenerEstratosProyecto(proyecto):
        try:
            conn = Connection.connectionDB()
            sql = f"""SELECT * FROM estratos_instrumentacion WHERE id_proyecto=?"""
            
            cur = conn.cursor()
            cur.execute(sql, (proyecto,))
            result = cur.fetchall() 
            if result:
                return result
            else:
                return None
        except Error as e:
            print("Error al obtener estratos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
  