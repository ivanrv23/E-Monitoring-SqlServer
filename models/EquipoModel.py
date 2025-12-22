from services.security.apis.conexiones.connection import Connection

class EquipoModel:
    
    @staticmethod
    def mdlListarAdicionalProyecto(proyecto, idcomponente, idequipo):
        sql = f"""SELECT c.id_componente, p.* FROM equipos p INNER JOIN instrumentacion t
        ON p.id_equipo = t.id_equipo INNER JOIN componentes c ON t.id_componente = c.id_componente
        WHERE c.id_proyecto = ? AND t.id_equipo = ? AND c.id_componente = ?;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyecto, idequipo, idcomponente))
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al consultar equipo adicional: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # REGISTRAR NUEVO EQUIPO GENERAL 
    @staticmethod
    def mdlGuardarEquipoGeneral(data):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # En pyodbc la transaccion inicia automaticamente, se confirma con commit()
            
            # Verificar si el equipo ya existe en la tabla instrumentacion
            # SQL Server: Usar TOP 1
            sql_check = """SELECT TOP 1 1 FROM instrumentacion WHERE id_componente = ? AND nombre_equipo = ? AND tipo_equipo = 'ADICIONAL';"""
            cur.execute(sql_check, (data[10], data[1]))
            if cur.fetchone():
                return "NO", None
            
            # Insertar el equipo en la tabla equipos
            sql_insert_equipo = """INSERT INTO equipos (id_proyecto, nombre_equipo, tipo_equipo, norte_equipo, este_equipo, elevacion_equipo, figura_equipo, color_equipo, tamanio_equipo, descripcion_equipo)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
            cur.execute(sql_insert_equipo, (data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8], data[9]))
            
            # Obtener el ID del equipo recién insertado en SQL Server
            cur.execute("SELECT SCOPE_IDENTITY();")
            row_id = cur.fetchone()
            if row_id and row_id[0] is not None:
                equipo_id = int(row_id[0])
            else:
                conn.rollback()
                return "ERROR", None

            # Insertar el equipo en la tabla instrumentacion
            sql_insert_instrumentacion = """INSERT INTO instrumentacion (id_componente, tipo_equipo, nombre_equipo, id_equipo, tabla_equipo)
                                            VALUES (?, ?, ?, ?, ?)"""
            cur.execute(sql_insert_instrumentacion, (data[10], 'ADICIONAL', data[1], equipo_id, 'equipos'))
            
            # Confirmar la transacción
            conn.commit()
            return "OK", equipo_id
        except Exception as e:
            # Realizar rollback en caso de error
            if conn:
                conn.rollback()
            print("Error al guardar equipo general: " + str(e))
            return "ERROR", None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCambiarComponenteAdicionales(idcomponente, nuevocomponente):
        sql = """UPDATE instrumentacion SET id_componente = ? WHERE id_componente = ? AND tipo_equipo = 'ADICIONAL';"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # guardar info
            query_select = """SELECT * FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'ADICIONAL';"""
            cur.execute(query_select, (idcomponente,))
            dataequipo = cur.fetchall()
            if dataequipo:
                cur.execute(sql, (nuevocomponente, idcomponente))
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
            # obtener info
            query_select = """SELECT * FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'ADICIONAL';"""
            cursor.execute(query_select, (idcomponente,))
            datatdr = cursor.fetchall()
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
        placeholders = ','.join(['?' for _ in equipos])
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
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
                return row
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
        query = """UPDATE equipos SET nombre_equipo = ?, tipo_equipo = ?, este_equipo = ?, norte_equipo = ?, elevacion_equipo = ?,
        figura_equipo = ?, color_equipo = ?, tamanio_equipo = ?, descripcion_equipo = ? WHERE id_equipo = ?;"""
        conexion = None
        try:
            conexion = Connection.connectionDB()
            cursor = conexion.cursor()
            cursor.execute(query, datos)
            query_instrumentacion = """UPDATE instrumentacion SET id_componente = ?, nombre_equipo = ?
            WHERE id_instrumentacion = ? AND tipo_equipo = 'ADICIONAL';"""
            cursor.execute(query_instrumentacion, data)
            conexion.commit()
            return True
        except Exception as e:
            print(f"Error al actualizar equipo adicional: {e}")
            return False
        finally:
            if conexion:
                conexion.close()
    
    @staticmethod
    def mdlEliminarEquipoAdicional(idinstrumento):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # obtener info para eliminar data
            # SQL Server: TOP 1 es buena practica aunque fetchone lo limite
            query_select = """SELECT TOP 1 * FROM instrumentacion WHERE id_instrumentacion = ? AND tipo_equipo = 'ADICIONAL';"""
            cursor.execute(query_select, (idinstrumento,))
            dataequipo = cursor.fetchone()
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
        sql = """SELECT i.id_instrumentacion, i.id_componente, c.nombre_componente FROM instrumentacion i
        INNER JOIN componentes c ON i.id_componente = c.id_componente
        WHERE i.id_equipo = ? AND i.tipo_equipo = 'ADICIONAL';"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idequipo,))
            row = cur.fetchone()
            if row:
                return row
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