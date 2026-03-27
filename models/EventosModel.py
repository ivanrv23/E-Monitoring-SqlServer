from services.security.apis.conexiones.connection import Connection
from datetime import datetime
import pandas as pd

class EventosModel:
    
    @staticmethod
    def mdlCrearEvento(idproyecto, fecha, descripcion, color, alcance, tipo_inst, id_inst):
        if isinstance(fecha, pd.Timestamp):
            fecha = fecha.to_pydatetime()
        sql = """INSERT INTO Software_EventosGrafica 
                 (id_proyecto, fecha_evento, descripcion, color_hex, tipo_alcance, tipo_instrumento, id_instrumento)
                 VALUES (?, ?, ?, ?, ?, ?, ?);"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idproyecto, fecha, descripcion, color, alcance, tipo_inst, str(id_inst)))
            conn.commit()
            return True
        except Exception as e:
            print("Error al crear evento:", e)
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlObtenerEventos(idproyecto, tipo_inst, ids_instrumentos, fecha_inicio, fecha_fin):
        """
        ids_instrumentos: LISTA de ids ['1','2','3'] — ya no es un solo id
        """
        def sanitizar_fecha(fecha):
            if isinstance(fecha, str):
                try:
                    fecha = pd.to_datetime(fecha).to_pydatetime()
                except:
                    try:
                        fecha = datetime.strptime(fecha, '%Y-%m-%d %H:%M:%S')
                    except:
                        return datetime.now()
            elif isinstance(fecha, pd.Timestamp):
                fecha = fecha.to_pydatetime()
            if fecha.year < 1753:
                fecha = datetime(1753, 1, 1, 0, 0, 0)
            return fecha

        f_ini_safe = sanitizar_fecha(fecha_inicio)
        f_fin_safe = sanitizar_fecha(fecha_fin)
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            
            if ids_instrumentos:
                placeholders = ','.join(['?' for _ in ids_instrumentos])
                sql = f"""SELECT id_evento, fecha_evento, descripcion, color_hex, tipo_alcance, id_instrumento 
                         FROM Software_EventosGrafica 
                         WHERE id_proyecto = ? 
                         AND tipo_instrumento = ?
                         AND (
                            tipo_alcance = 'GLOBAL' 
                            OR (tipo_alcance = 'ESPECIFICO' AND id_instrumento IN ({placeholders}))
                         )
                         AND fecha_evento BETWEEN ? AND ?
                         ORDER BY fecha_evento ASC;"""
                params = [idproyecto, tipo_inst] + [str(i) for i in ids_instrumentos] + [f_ini_safe, f_fin_safe]
            else:
                sql = """SELECT id_evento, fecha_evento, descripcion, color_hex, tipo_alcance, id_instrumento 
                         FROM Software_EventosGrafica 
                         WHERE id_proyecto = ? 
                         AND tipo_instrumento = ?
                         AND tipo_alcance = 'GLOBAL'
                         AND fecha_evento BETWEEN ? AND ?
                         ORDER BY fecha_evento ASC;"""
                params = [idproyecto, tipo_inst, f_ini_safe, f_fin_safe]
            
            cur.execute(sql, params)
            filas = cur.fetchall()
            return [tuple(fila) for fila in filas] if filas else []
        except Exception as e:
            print("Error al obtener eventos:", e)
            return []
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlEliminarEvento(id_evento):
        sql = """DELETE FROM Software_EventosGrafica WHERE id_evento = ?;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (id_evento,))
            conn.commit()
            return True
        except Exception as e:
            print("Error al eliminar evento:", e)
            return False
        finally:
            if conn:
                conn.close()