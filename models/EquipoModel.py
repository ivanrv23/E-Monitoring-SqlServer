from services.security.apis.conexiones.connection import Connection
import pyodbc

class EquipoModel:
    
    @staticmethod
    def mdlListarAdicionalProyecto(proyecto, idcomponente, idequipo):
        # SQL compatible con T-SQL
        sql = """SELECT c.id_componente, p.* 
                 FROM equipos p 
                 INNER JOIN instrumentacion t ON p.id_equipo = t.id_equipo 
                 INNER JOIN componentes c ON t.id_componente = c.id_componente
                 WHERE c.id_proyecto = ? AND t.id_equipo = ? AND c.id_componente = ?;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyecto, idequipo, idcomponente))
            row = cur.fetchone()
            if row:
                return tuple(row) # Conversión explícita a tupla
            else:
                return None
        except Exception as e:
            print("Error al consultar equipo adicional: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlGuardarEquipoGeneral(data):
        conn = None
        try:
            conn = Connection.connectionDB()
            conn.autocommit = False # Iniciar control manual de transacción
            cur = conn.cursor()
            
            # 1. Verificar existencia
            sql_check = """SELECT 1 FROM instrumentacion WHERE id_componente = ? AND nombre_equipo = ? AND tipo_equipo = 'ADICIONAL';"""
            # data[10] = id_componente, data[1] = nombre_equipo
            cur.execute(sql_check, (data[10], data[1]))
            if cur.fetchone():
                conn.rollback()
                return "NO", None

            # 2. Insertar equipo y obtener ID (Estrategia OUTPUT INSERTED)
            # Asumimos que la PK es 'id_equipo' basado en las otras consultas
            sql_insert_equipo = """INSERT INTO equipos (id_proyecto, nombre_equipo, tipo_equipo, norte_equipo, este_equipo, 
                                   elevacion_equipo, figura_equipo, color_equipo, tamanio_equipo, descripcion_equipo)
                                   OUTPUT INSERTED.id_equipo
                                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
            
            cur.execute(sql_insert_equipo, (data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8], data[9]))
            
            # Capturar el ID retornado por OUTPUT
            row_id = cur.fetchone()
            if not row_id:
                raise Exception("No se pudo obtener el ID del equipo insertado.")
            equipo_id = row_id[0]

            # 3. Insertar en instrumentacion
            sql_insert_instrumentacion = """INSERT INTO instrumentacion (id_componente, tipo_equipo, nombre_equipo, id_equipo, tabla_equipo)
                                            VALUES (?, ?, ?, ?, ?)"""
            cur.execute(sql_insert_instrumentacion, (data[10], 'ADICIONAL', data[1], equipo_id, 'equipos'))
            
            # Confirmar transacción
            conn.commit()
            return "OK", equipo_id

        except Exception as e:
            if conn:
                conn.rollback()
            print("Error al guardar equipo general: " + str(e))
            return "ERROR", None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlCambiarComponenteAdicionales(idcomponente, nuevocomponente):
        sql_update = """UPDATE instrumentacion SET id_componente = ? WHERE id_componente = ? AND tipo_equipo = 'ADICIONAL';"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            
            # Guardar info antes de actualizar
            query_select = """SELECT * FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'ADICIONAL';"""
            cur.execute(query_select, (idcomponente,))
            # pyodbc devuelve objetos Row, convertimos a lista de tuplas
            rows = cur.fetchall()
            dataequipo = [tuple(row) for row in rows]
            
            if dataequipo:
                cur.execute(sql_update, (nuevocomponente, idcomponente))
                conn.commit()
                return dataequipo
            else:
                return None
        except Exception as e:
            print("Error al cambiar componente adicionales: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlEliminarAdicionales(idcomponente):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            
            # Obtener info
            query_select = """SELECT * FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'ADICIONAL';"""
            cursor.execute(query_select, (idcomponente,))
            rows = cursor.fetchall()
            datatdr = [tuple(row) for row in rows]
            
            if datatdr:
                query = """DELETE FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'ADICIONAL';"""
                cursor.execute(query, (idcomponente,))
                conn.commit()
                
                if cursor.rowcount > 0:
                    return datatdr
                else:
                    return None
            else:
                return None
        except Exception as e:
            print(f"Error al eliminar Adicionales: {e}")
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlEliminarDataAdicionales(equipos):
        # Generar placeholders dinámicos para IN (?, ?, ...)
        placeholders = ', '.join(['?' for _ in equipos])
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # Formato seguro para evitar inyección SQL, pasando la lista como parámetros
            stmt_delete = f"DELETE FROM equipos WHERE id_equipo IN ({placeholders});"
            cursor.execute(stmt_delete, equipos)
            rows_delete = cursor.rowcount
            conn.commit()
            return rows_delete > 0
        except Exception as e:
            print(f"Error al eliminar equipos adicionales: {e}")
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlObtenerInfoEquipoAdicional(idinstrumento):
        sql = """SELECT e.* FROM equipos e INNER JOIN instrumentacion i ON e.id_equipo = i.id_equipo WHERE i.id_instrumentacion = ?;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idinstrumento,))
            row = cur.fetchone()
            if row:
                return tuple(row)
            else:
                return None
        except Exception as e:
            print("Error al consultar info adicional: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlActualizarEquipoAdicional(datos, data):
        query_equipo = """UPDATE equipos SET nombre_equipo = ?, tipo_equipo = ?, este_equipo = ?, norte_equipo = ?, elevacion_equipo = ?,
                          figura_equipo = ?, color_equipo = ?, tamanio_equipo = ?, descripcion_equipo = ? WHERE id_equipo = ?;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            conn.autocommit = False # Transacción explícita
            cursor = conn.cursor()
            
            cursor.execute(query_equipo, datos)
            
            query_instrumentacion = """UPDATE instrumentacion SET id_componente = ?, nombre_equipo = ?
                                       WHERE id_instrumentacion = ? AND tipo_equipo = 'ADICIONAL';"""
            cursor.execute(query_instrumentacion, data)
            
            conn.commit()
            return True
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"Error al actualizar equipo adicional: {e}")
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlEliminarEquipoAdicional(idinstrumento):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            
            # Obtener info para eliminar data
            query_select = """SELECT * FROM instrumentacion WHERE id_instrumentacion = ? AND tipo_equipo = 'ADICIONAL';"""
            cursor.execute(query_select, (idinstrumento,))
            row = cursor.fetchone()
            dataequipo = tuple(row) if row else None
            
            if dataequipo:
                query = """DELETE FROM instrumentacion WHERE id_instrumentacion = ? AND tipo_equipo = 'ADICIONAL';"""
                cursor.execute(query, (idinstrumento,))
                conn.commit()
                if cursor.rowcount > 0:
                    return dataequipo
                else:
                    return None
            else:
                return None
        except Exception as e:
            print(f"Error al eliminar adicional: {e}")
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlEliminarEquipoAdicionalData(idequipo):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            stmt_delete = "DELETE FROM equipos WHERE id_equipo = ?;"
            cursor.execute(stmt_delete, (idequipo,))
            rows_delete = cursor.rowcount
            conn.commit()
            return rows_delete > 0
        except Exception as e:
            print(f"Error al eliminar data adicional: {e}")
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlTraerDataEquipoGeneral(idequipo):
        sql = """SELECT i.id_instrumentacion, i.id_componente, c.nombre_componente 
                 FROM instrumentacion i
                 INNER JOIN componentes c ON i.id_componente = c.id_componente
                 WHERE i.id_equipo = ? AND i.tipo_equipo = 'ADICIONAL';"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idequipo,))
            row = cur.fetchone()
            if row:
                return tuple(row)
            else:
                return None
        except Exception as e:
            print("Error al traer data equipo adicional: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlCambiarEquipoComponente(idinstrumento, nuevocomponente):
        sql = """UPDATE instrumentacion SET id_componente = ? WHERE id_instrumentacion = ?;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (nuevocomponente, idinstrumento))
            conn.commit()
            return True
        except Exception as e:
            print("Error al cambiar componente adicional: " + str(e))
            return False
        finally:
            if conn:
                conn.close()