from services.security.apis.conexiones.connection import Connection
import pyodbc

class EstratoModel:

    @staticmethod
    def mdlGuardarEstratos(proyectoid, componente_id, data):
        sql = """INSERT INTO estratos_instrumentacion (id_proyecto, id_componente, nombre_estrato, color_estrato, rango_min, rango_max) 
                 VALUES (?, ?, ?, ?, ?, ?);"""
        conn = None
        try:
            conn = Connection.connectionDB()
            conn.autocommit = False  # Iniciar transacción manual
            cur = conn.cursor()
            
            for item in data:
                # Se asume que data es una lista de diccionarios
                cur.execute(sql, (
                    proyectoid,
                    componente_id,
                    item['nombre'],
                    item['color'],
                    item['rango_minimo'],
                    item['rango_maximo']
                ))
            
            conn.commit() # Confirmar cambios en bloque
            return True
        except Exception as e:
            if conn:
                conn.rollback() # Revertir si hay error en el bucle
            print("Error al registrar estrato:", e)
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlActualizarEstratos(id_estrato, nombre, color, rango_min, rango_max):
        sql = """UPDATE estratos_instrumentacion 
                 SET nombre_estrato = ?, color_estrato = ?, rango_min = ?, rango_max = ? 
                 WHERE id_estrato = ?;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (nombre, color, rango_min, rango_max, id_estrato))
            conn.commit()
            return True
        except Exception as e:
            print("Error al actualizar estrato:", e)
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlObtenerEstratosInstrumentacion(proyectoid, componente_id):
        sql = """SELECT * FROM estratos_instrumentacion WHERE id_proyecto = ? AND id_componente = ?"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyectoid, componente_id))
            
            # Convertir filas de pyodbc a tuplas nativas de Python
            rows = cur.fetchall()
            result = [tuple(row) for row in rows]
            
            if result:
                return result
            else:
                return None
        except Exception as e:
            print("Error al obtener estratos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlEliminarEstrato(estrato_id):
        sql = """DELETE FROM estratos_instrumentacion WHERE id_estrato = ?"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (estrato_id,))
            conn.commit()
            
            if cur.rowcount > 0:
                return True
            else:
                return False
        except Exception as e:
            print("Error al eliminar estratos: " + str(e))
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlObtenerEstratosProyecto(proyecto):
        sql = """SELECT * FROM estratos_instrumentacion WHERE id_proyecto = ?"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyecto,))
            
            # Convertir filas de pyodbc a tuplas nativas de Python
            rows = cur.fetchall()
            result = [tuple(row) for row in rows]
            
            if result:
                return result
            else:
                return None
        except Exception as e:
            print("Error al obtener estratos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()