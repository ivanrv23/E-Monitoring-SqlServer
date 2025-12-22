from services.security.apis.conexiones.conexion import Connection
from sqlite3 import Error
from utils.common.rutasarchivos import resource_path
import os
class ProyectoModel:
    
    @staticmethod
    def mdlRegistarProyecto(nombre, fecha, comentario):
        try:
            conn = Connection.connectionDB()
            sql = """INSERT INTO proyectos (nombre_proyecto, fecha_proyecto, descripcion_proyecto) VALUES (?, ?, ?);"""
            cur = conn.cursor()
            cur.execute(sql, (nombre, fecha, comentario))
            conn.commit()
            # Obtener el id_proyecto recién insertado
            idproyecto = cur.lastrowid
            return True, idproyecto
        except Error as e:
            print("Error al registrar proyecto:", e)
            return False, 0
        finally:
            if conn:
                conn.close()
    
    def mdlRegistarComponente(proyecto_id, nombre_componente):
        try:
            conn = Connection.connectionDB()
            sql = """INSERT INTO componentes (id_proyecto, nombre_componente) VALUES (?, ?);"""
            cur = conn.cursor()
            cur.execute(sql, (proyecto_id, nombre_componente))
            conn.commit()
            return True
        except Error as e:
            print("Error al registrar componente:", e)
            return False  
        finally:
            if conn:
                conn.close()

    def mdlObtenerInfoProyecto(idproyecto):
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            sql = "SELECT * FROM proyectos WHERE id_proyecto = ?;"
            cur.execute(sql, (idproyecto,))
            resultado = cur.fetchone()
            if resultado:
                return resultado
            else:
                return None 
        except Error as e:
            print("Error al obtener info proyecto:", e)
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlActualizarProyecto(nombre, fecha, comentario, idproyecto):
        sql = """UPDATE proyectos SET nombre_proyecto = ?, fecha_proyecto = ?, descripcion_proyecto = ? WHERE id_proyecto = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (nombre, fecha, comentario, idproyecto))
            conn.commit()
            return True
        except Error as e:
            print("Error al actualizar proyecto:", e)
            return False  
        finally:
            if conn:
                conn.close()
    
    def mdlObtenerComponentesProyecto(idproyecto):
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            sql = "SELECT * FROM componentes WHERE id_proyecto = ? AND estado_componente = 1;"
            cur.execute(sql, (idproyecto,))
            resultado = cur.fetchall()
            if resultado:
                return resultado
            else:
                return None 
        except Error as e:
            print("Error al obtener componentes:", e)
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlActualizarComponente(nombre, idcomponente):
        sql = """UPDATE componentes SET nombre_componente = ? WHERE id_componente = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (nombre, idcomponente))
            conn.commit()
            return True
        except Error as e:
            print("Error al actualizar componente:", e)
            return False  
        finally:
            if conn:
                conn.close()
    
    def mdlEliminarComponente(idproyecto, idcomponente):
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
        except Error as e:
            print("Error al eliminar componente:", e)
            return False  
        finally:
            if conn:
                conn.close()
    
    def mdlEliminarProyecto(idproyecto):
        # Consultas SQL para eliminar registros
        sql_queries = [
            "DELETE FROM acelerografos WHERE id_proyecto = ?;",
            f"DROP TABLE IF EXISTS acelerografo_detalle{idproyecto};",
            "DELETE FROM cotas_celdas WHERE id_celda IN (SELECT id_celda FROM celdas WHERE id_proyecto = ?);",
            "DELETE FROM celdas WHERE id_proyecto = ?;",
            f"DROP TABLE IF EXISTS celda_detalle{idproyecto};",
            "DELETE FROM cotas_piezometricas WHERE tipo_piezometro = 'PCV' AND id_piezometro IN (SELECT id_piezometro FROM piezometrocuerdas WHERE id_proyecto = ?);",
            "DELETE FROM piezometrocuerdas WHERE id_proyecto = ?;",
            f"DROP TABLE IF EXISTS piezometrocuerda_detalle{idproyecto};",
            "DELETE FROM cotas_piezometricas WHERE tipo_piezometro = 'PVC' AND  id_piezometro IN (SELECT id_piezometro FROM piezometromanuales WHERE id_proyecto = ?);",
            "DELETE FROM piezometromanuales WHERE id_proyecto = ?;",
            f"DROP TABLE IF EXISTS piezometromanual_detalle{idproyecto};",
            f"DROP TABLE IF EXISTS prismas{idproyecto};",
            "DELETE FROM prismas_virtuales WHERE id_prisma_virtual IN (SELECT inst.id_equipo FROM instrumentacion inst INNER JOIN componentes c ON inst.id_componente=c.id_componente WHERE c.id_proyecto = ?);",
            "DELETE FROM pluviometros WHERE id_proyecto = ?;",
            f"DROP TABLE IF EXISTS pluviometro_detalle{idproyecto};",
            "DELETE FROM cotasterreno WHERE id_proyecto = ?;",
            f"DROP TABLE IF EXISTS cotasterreno_detalle{idproyecto};",
            "DELETE FROM sondajestdr_puntos WHERE id_sondajetdr IN (SELECT id_sondajetdr FROM sondajestdr WHERE id_proyecto = ?);",
            "DELETE FROM sondajestdr WHERE id_proyecto = ?;",
            f"DROP TABLE IF EXISTS sondajestdr_detalle{idproyecto};",
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
            f"DROP TABLE IF EXISTS inclinometro_detalle{idproyecto};",
            "DELETE FROM control_parametros_anexo1 WHERE id_componente IN (SELECT id_componente FROM componentes WHERE id_proyecto = ?);",
            "DELETE FROM instrumentacion WHERE id_componente IN (SELECT id_componente FROM componentes WHERE id_proyecto = ?);",
            "DELETE FROM componentes WHERE id_proyecto = ?;",
            "DELETE FROM proyectos WHERE id_proyecto = ?;"
        ]

        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()

            # Iniciar transacción
            conn.execute("BEGIN;")

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
        except Error as e:
            print("Error al eliminar proyecto:", e)
            conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlObtenerHistorialCambios():
        sql = """SELECT p.nombre_proyecto, h.fecha, h.accion, h.tabla, h.usuario, h.cambios, h.nombres
        FROM historial h INNER JOIN proyectos p ON h.idproyecto = p.id_proyecto ORDER BY h.fecha DESC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar historial: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlObtenerAjustesCambios():
        sql = """SELECT p.nombre_proyecto, r.fecha_cambio, 'update' AS accion, r.tabla_modificada, r.usuario_cambio,
        r.columna_modificada || '(' || r.numero_fila || '): ' || r.valor_anterior || ' -> ' || r.nuevo_valor AS cambios, r.nombres_cambio
        FROM registro_ajuste_coordenadas r INNER JOIN proyectos p ON r.id_proyecto = p.id_proyecto ORDER BY r.fecha_cambio DESC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar cambios: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    