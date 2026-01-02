from services.security.apis.conexiones.connection import Connection
from utils.common.rutasarchivos import resource_path
import os

class ProyectoModel:
    
    @staticmethod
    def mdlRegistarProyecto(nombre, fecha, comentario):
        conn = None
        try:
            conn = Connection.connectionDB()
            # Uso de OUTPUT INSERTED.id_proyecto para obtener el ID en SQL Server
            sql = """INSERT INTO proyectos (nombre_proyecto, fecha_proyecto, descripcion_proyecto) 
                     OUTPUT INSERTED.id_proyecto 
                     VALUES (?, ?, ?);"""
            cur = conn.cursor()
            cur.execute(sql, (nombre, fecha, comentario))
            
            # Obtener el id inmediatamente
            idproyecto = cur.fetchone()[0]
            
            conn.commit()
            return True, idproyecto
        except Exception as e:
            print("Error al registrar proyecto:", e)
            if conn:
                conn.rollback()
            return False, 0
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlRegistarComponente(proyecto_id, nombre_componente):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = """INSERT INTO componentes (id_proyecto, nombre_componente) VALUES (?, ?);"""
            cur = conn.cursor()
            cur.execute(sql, (proyecto_id, nombre_componente))
            conn.commit()
            return True
        except Exception as e:
            print("Error al registrar componente:", e)
            if conn:
                conn.rollback()
            return False  
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlObtenerInfoProyecto(idproyecto):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            sql = "SELECT * FROM proyectos WHERE id_proyecto = ?;"
            cur.execute(sql, (idproyecto,))
            resultado = cur.fetchone()
            if resultado:
                return tuple(resultado)
            else:
                return None 
        except Exception as e:
            print("Error al obtener info proyecto:", e)
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlActualizarProyecto(nombre, fecha, comentario, idproyecto):
        conn = None
        sql = """UPDATE proyectos SET nombre_proyecto = ?, fecha_proyecto = ?, descripcion_proyecto = ? WHERE id_proyecto = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (nombre, fecha, comentario, idproyecto))
            conn.commit()
            return True
        except Exception as e:
            print("Error al actualizar proyecto:", e)
            if conn:
                conn.rollback()
            return False  
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerComponentesProyecto(idproyecto):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            sql = "SELECT * FROM componentes WHERE id_proyecto = ? AND estado_componente = 1;"
            cur.execute(sql, (idproyecto,))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
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
    
    @staticmethod
    def mdlActualizarComponente(nombre, idcomponente):
        conn = None
        sql = """UPDATE componentes SET nombre_componente = ? WHERE id_componente = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (nombre, idcomponente))
            conn.commit()
            return True
        except Exception as e:
            print("Error al actualizar componente:", e)
            if conn:
                conn.rollback()
            return False  
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlEliminarComponente(idproyecto, idcomponente):
        conn = None
        sql_count = """SELECT COUNT(*) FROM componentes WHERE id_proyecto = ? AND estado_componente = 1;"""
        sql = """UPDATE componentes SET estado_componente = 0 WHERE id_componente = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # Verificamos la cantidad de componentes activos
            cur.execute(sql_count, (idproyecto,))
            cantidad = cur.fetchone()[0]
            if cantidad <= 1:
                return False
            # eliminar
            cur.execute(sql, (idcomponente,))
            conn.commit()
            return True
        except Exception as e:
            print("Error al eliminar componente:", e)
            if conn:
                conn.rollback()
            return False  
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlEliminarProyectoooooooooooooo(idproyecto):
        conn = None
        sql = """UPDATE proyectos SET estado_proyecto = 0 WHERE id_proyecto = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idproyecto,))
            conn.commit()
            return True
        except Exception as e:
            print("Error al eliminar proyecto:", e)
            if conn:
                conn.rollback()
            return False  
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlEliminarProyecto(idproyecto):
        conn = None
        # Consultas SQL para eliminar registros
        # Sintaxis T-SQL para DROP TABLE IF EXISTS
        sql_queries = [
            "DELETE FROM acelerografos WHERE id_proyecto = ?;",
            f"IF OBJECT_ID('acelerografo_detalle{idproyecto}', 'U') IS NOT NULL DROP TABLE acelerografo_detalle{idproyecto};",
            "DELETE FROM cotas_celdas WHERE id_celda IN (SELECT id_celda FROM celdas WHERE id_proyecto = ?);",
            "DELETE FROM celdas WHERE id_proyecto = ?;",
            f"IF OBJECT_ID('celda_detalle{idproyecto}', 'U') IS NOT NULL DROP TABLE celda_detalle{idproyecto};",
            "DELETE FROM cotas_piezometricas WHERE tipo_piezometro = 'PCV' AND id_piezometro IN (SELECT id_piezometro FROM piezometrocuerdas WHERE id_proyecto = ?);",
            "DELETE FROM piezometrocuerdas WHERE id_proyecto = ?;",
            f"IF OBJECT_ID('piezometrocuerda_detalle{idproyecto}', 'U') IS NOT NULL DROP TABLE piezometrocuerda_detalle{idproyecto};",
            "DELETE FROM cotas_piezometricas WHERE tipo_piezometro = 'PVC' AND  id_piezometro IN (SELECT id_piezometro FROM piezometromanuales WHERE id_proyecto = ?);",
            "DELETE FROM piezometromanuales WHERE id_proyecto = ?;",
            f"IF OBJECT_ID('piezometromanual_detalle{idproyecto}', 'U') IS NOT NULL DROP TABLE piezometromanual_detalle{idproyecto};",
            f"IF OBJECT_ID('prismas{idproyecto}', 'U') IS NOT NULL DROP TABLE prismas{idproyecto};",
            "DELETE FROM prismas_virtuales WHERE id_prisma_virtual IN (SELECT inst.id_equipo FROM instrumentacion inst INNER JOIN componentes c ON inst.id_componente=c.id_componente WHERE c.id_proyecto = ?);",
            "DELETE FROM pluviometros WHERE id_proyecto = ?;",
            f"IF OBJECT_ID('pluviometro_detalle{idproyecto}', 'U') IS NOT NULL DROP TABLE pluviometro_detalle{idproyecto};",
            "DELETE FROM cotasterreno WHERE id_proyecto = ?;",
            f"IF OBJECT_ID('cotasterreno_detalle{idproyecto}', 'U') IS NOT NULL DROP TABLE cotasterreno_detalle{idproyecto};",
            "DELETE FROM sondajestdr_puntos WHERE id_sondajetdr IN (SELECT id_sondajetdr FROM sondajestdr WHERE id_proyecto = ?);",
            "DELETE FROM sondajestdr WHERE id_proyecto = ?;",
            f"IF OBJECT_ID('sondajestdr_detalle{idproyecto}', 'U') IS NOT NULL DROP TABLE sondajestdr_detalle{idproyecto};",
            "DELETE FROM umbral_acelerografo WHERE id_proyecto = ?;",
            "DELETE FROM umbral_celda WHERE id_proyecto = ?;",
            "DELETE FROM umbral_inclinometro WHERE id_proyecto = ?;",
            "DELETE FROM umbral_piezometro WHERE id_proyecto = ?;",
            "DELETE FROM umbral_prisma WHERE id_proyecto = ?;",
            "DELETE FROM ejes WHERE id_proyecto = ?;",
            "DELETE FROM equipos WHERE id_proyecto = ?;",
            "DELETE FROM estereografias WHERE id_proyecto = ?;",
            "DELETE FROM estilos WHERE id_proyecto = ?;",
            "DELETE FROM estratos_instrumentacion WHERE id_proyecto = ?;",
            "DELETE FROM firmas WHERE id_proyecto = ?;",
            "DELETE FROM graficos_reporte WHERE id_componente IN (SELECT id_componente FROM componentes WHERE id_proyecto = ?);",
            "DELETE FROM inclinometro_encabezado WHERE id_inclinometro IN (SELECT id_inclinometro FROM inclinometros WHERE id_proyecto = ?);",
            "DELETE FROM inclinometros WHERE id_proyecto = ?;",
            f"IF OBJECT_ID('inclinometro_detalle{idproyecto}', 'U') IS NOT NULL DROP TABLE inclinometro_detalle{idproyecto};",
            "DELETE FROM control_parametros_anexo1 WHERE id_componente IN (SELECT id_componente FROM componentes WHERE id_proyecto = ?);",
            "DELETE FROM instrumentacion WHERE id_componente IN (SELECT id_componente FROM componentes WHERE id_proyecto = ?);",
            "DELETE FROM componentes WHERE id_proyecto = ?;",
            "DELETE FROM proyectos WHERE id_proyecto = ?;"
        ]

        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()

            # En pyodbc con SQL Server no se usa conn.execute("BEGIN;").
            # Las transacciones se manejan implicitamente y se confirman con conn.commit()
            
            # Ejecutar consultas SQL
            for query in sql_queries:
                if '?' in query:
                    cur.execute(query, (idproyecto,))
                else:
                    cur.execute(query)

            # Eliminar archivos de topografías si existen
            cur.execute("SELECT archivo_topografia FROM topografias WHERE id_proyecto = ?;", (idproyecto,))
            rutas_topografias = cur.fetchall()
            for ruta in rutas_topografias:
                # ruta[0] es lo que necesitamos
                archivo_path = resource_path(ruta[0])
                try:
                    if os.path.exists(archivo_path):
                        os.remove(archivo_path)
                except OSError as e:
                    print(f"Error al eliminar el archivo {archivo_path}: {e}")

            # Eliminar registros de topografías
            cur.execute("DELETE FROM topografias WHERE id_proyecto = ?;", (idproyecto,))

            # Confirmar transacción
            conn.commit()
            return True
        except Exception as e:
            print("Error al eliminar proyecto:", e)
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerHistorialCambios():
        conn = None
        sql = """SELECT p.nombre_proyecto, h.fecha, h.accion, h.tabla, h.usuario, h.cambios, h.nombres
        FROM historial h INNER JOIN proyectos p ON h.idproyecto = p.id_proyecto ORDER BY h.fecha DESC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql)
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al consultar historial: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerAjustesCambios():
        conn = None
        # Corrección SQL Server: Operador de concatenación es '+' en lugar de '||'
        sql = """SELECT p.nombre_proyecto, r.fecha_cambio, 'update' AS accion, r.tabla_modificada, r.usuario_cambio,
        r.columna_modificada + '(' + CAST(r.numero_fila AS VARCHAR) + '): ' + CAST(r.valor_anterior AS VARCHAR) + ' -> ' + CAST(r.nuevo_valor AS VARCHAR) AS cambios, r.nombres_cambio
        FROM registro_ajuste_coordenadas r INNER JOIN proyectos p ON r.id_proyecto = p.id_proyecto ORDER BY r.fecha_cambio DESC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql)
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al consultar cambios: " + str(e))
            return None
        finally:
            if conn:
                conn.close()