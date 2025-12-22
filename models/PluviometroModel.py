from services.security.apis.conexiones.conexion import Connection
from datetime import datetime

class PluviometroModel:
    
    # LISTAR LOS PLUVIOMETRO POR PROYECTO    
    @staticmethod
    def mdlListarPluviometroProyecto(proyecto, idcomponente, idpluvio):
        conn = None
        sql = f"""SELECT p.id_pluviometro, p.nombre_pluviometro, c.id_componente, p.este_pluviometro, p.norte_pluviometro,
        p.elevacion_pluviometro FROM pluviometros p INNER JOIN instrumentacion t ON p.id_pluviometro = t.id_equipo
		INNER JOIN componentes c ON t.id_componente = c.id_componente
        WHERE c.id_proyecto = ? AND t.id_equipo = ? AND c.id_componente = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyecto, idpluvio, idcomponente))
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al consultar pluviometro: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # GUARDAR NUEVO PLUVIOMETRO           
    @staticmethod
    def mdlGuardarNuevoPluviometro(proyecto_id, datos):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            
            # Verificar si el equipo ya existe en la tabla instrumentacion
            # SQL Server: Usar TOP 1
            sql_check = """SELECT TOP 1 1 FROM instrumentacion WHERE id_componente = ? AND nombre_equipo = ? AND tipo_equipo = 'PLUVIOMETRO';"""
            cur.execute(sql_check, (datos[6], datos[0]))
            if cur.fetchone():
                print("El equipo ya existe en la tabla instrumentacion.")
                return "NO"
            
            # Insertar el nuevo pluviometro
            sql_insert = """INSERT INTO pluviometros (id_proyecto, nombre_pluviometro, codigo_pluviometro, norte_pluviometro, este_pluviometro, 
                            elevacion_pluviometro, comentario_pluviometro) VALUES (?, ?, ?, ?, ?, ?, ?)"""
            cur.execute(sql_insert, (proyecto_id, datos[0], datos[1], datos[2], datos[3], datos[4], datos[5]))
            
            # Obtener el ID del pluvio recién insertado
            cur.execute("SELECT SCOPE_IDENTITY();")
            row_id = cur.fetchone()
            if row_id and row_id[0]:
                pluviometro_id = int(row_id[0])
            else:
                conn.rollback()
                return False

            # Insertar en la tabla instrumentacion
            sql_insert_instrumentacion = """INSERT INTO instrumentacion (id_componente, tipo_equipo, nombre_equipo, id_equipo, tabla_equipo)
                                            VALUES (?, ?, ?, ?, ?);"""
            cur.execute(sql_insert_instrumentacion, (datos[6], 'PLUVIOMETRO', datos[0], pluviometro_id, 'pluviometros'))
            
            # Confirmar la transacción
            conn.commit()
            return True
        except Exception as e:
            print("Error al guardar pluviometro:", e)
            # Realizar un rollback en caso de error
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlRegistrarFormatoPluviometro(proyecto_id, datos):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # Insertar el nuevo pluviometro
            sql_insert = """INSERT INTO pluviometros (id_proyecto, nombre_pluviometro, codigo_pluviometro, norte_pluviometro, este_pluviometro, 
                            elevacion_pluviometro, comentario_pluviometro) VALUES (?, ?, ?, ?, ?, ?, ?)"""
            cur.execute(sql_insert, (proyecto_id, datos[0], datos[1], datos[2], datos[3], datos[4], datos[5]))
            
            # Obtener el ID del pluvio recién insertado
            cur.execute("SELECT SCOPE_IDENTITY();")
            row_id = cur.fetchone()
            if row_id and row_id[0]:
                pluviometro_id = int(row_id[0])
            else:
                conn.rollback()
                return None

            # Insertar en la tabla instrumentacion
            sql_insert_instrumentacion = """INSERT INTO instrumentacion (id_componente, tipo_equipo, nombre_equipo, id_equipo, tabla_equipo)
                                            VALUES (?, ?, ?, ?, ?);"""
            cur.execute(sql_insert_instrumentacion, (datos[6], 'PLUVIOMETRO', datos[0], pluviometro_id, 'pluviometros'))
            
            # Confirmar la transacción
            conn.commit()
            return pluviometro_id
        except Exception as e:
            print("Error al guardar pluviometro:", e)
            # Realizar un rollback en caso de error
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()
    
    # Validar si existe pluviometro con el mismo nombre
    @staticmethod
    def mdlComprobarExisteNombrePluviometro(proyecto, nombre):
        sql = """SELECT * FROM pluviometros WHERE id_proyecto = ? AND nombre_pluviometro = ?;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyecto, nombre))
            row = cur.fetchone()
            if row:
                return True, row
            else:
                return False, None
        except Exception as e:
            print("Error al comprobar pluviómetro: " + str(e))
            return False, None
        finally:
            if conn:
                conn.close()
    
    # REGISTRAR PLUVIOMETROS DESDE LA TABLA   
    @staticmethod
    def mdlGuardarPluviometrosTabla(idproyecto, data):
        tabla = f"pluviometro_detalle{idproyecto}"
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            
            # SQL Server Create Table Syntax
            cursor.execute(f"""
            IF OBJECT_ID('{tabla}', 'U') IS NULL
            BEGIN
                CREATE TABLE "{tabla}" (
                    "id_detalle" INT IDENTITY(1,1) PRIMARY KEY,
                    "id_pluviometro" INT NOT NULL,
                    "fecha_pluviometro" VARCHAR(50) NOT NULL,
                    "medida_pluviometro" DECIMAL(18, 5) NOT NULL,
                    "observacion_pluviometro" NVARCHAR(MAX)
                );
            END""")
            
            # Eliminar PRAGMAS de SQLite (no necesarios ni válidos en SQL Server)
            
            # Crear un conjunto de tuplas con los valores de fecha y hora para comparar los registros existentes
            idpluvio = data[0][0]
            
            # Obtener fechas existentes
            cursor.execute(f"SELECT fecha_pluviometro FROM {tabla} WHERE id_pluviometro = ?", (idpluvio,))
            existen_pluviometros = set([row[0] for row in cursor.fetchall()])
            
            lote_registros = []
            
            for fila in data:
                fecha_original = fila[1]
                hora_original = fila[2]
                # completar el formato de fecha
                fecha_hora_nueva = fecha_original + " " + hora_original
                # Verifica si el registro no existe en el conjunto
                if (fecha_hora_nueva) not in existen_pluviometros:
                    datito = []
                    datito.append(fila[0])
                    datito.append(fecha_hora_nueva)
                    datito.append(abs(float(fila[3]))) # siempre positivo la medida
                    datito.append(fila[4])
                    lote_registros.append(datito)
            
            # Insertar en lotes si hay registros nuevos
            if lote_registros:
                # SQL Server soporta inserción masiva eficiente con executemany
                insert_query = f"""INSERT INTO {tabla} (id_pluviometro, fecha_pluviometro, medida_pluviometro, observacion_pluviometro) VALUES (?, ?, ?, ?);"""
                
                # Insertar en bloques para no saturar si son demasiados, aunque executemany de pyodbc lo maneja bien
                chunk_size = 1000
                for i in range(0, len(lote_registros), chunk_size):
                    chunk = lote_registros[i:i + chunk_size]
                    cursor.executemany(insert_query, chunk)
                    
            conn.commit()
            return True
        except Exception as e:
            if conn:
                conn.rollback()
            print("Error al guardar data pluviómetros: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    # LISTAR DATA PLUVIÓMETROS DETALLE POR ID    
    @staticmethod
    def mdlObtenerDataPluviometrosDetalle(idpluvio):
        conn = None
        sql = """SELECT p.nombre_pluviometro, d.fecha_pluviometro, d.medida_pluviometro 
            FROM pluviometro_detalle d INNER JOIN pluviometros p ON d.id_pluviometro = p.id_pluviometro WHERE d.id_pluviometro = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idpluvio,))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al consultar pluviómetros detalle: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # ACTUALIZAR PLUVIOMETRO       
    @staticmethod
    def mdlActualizarPluviometro(datos, data):
        sql = """UPDATE pluviometros SET nombre_pluviometro = ?, codigo_pluviometro = ?, norte_pluviometro = ?, este_pluviometro = ?, 
        elevacion_pluviometro = ?, comentario_pluviometro = ? WHERE id_pluviometro = ?;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, datos)
            query_instrumentacion = """UPDATE instrumentacion SET id_componente = ?, nombre_equipo = ?
            WHERE id_instrumentacion = ? AND tipo_equipo = 'PLUVIOMETRO';"""
            cur.execute(query_instrumentacion, data)
            conn.commit()
            return True
        except Exception as e:
            print("Error al editar pluviómetro: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
                
    # LISTAR LOS PLUVIÓMETROS POR PROYECTO    
    @staticmethod
    def mdlListarPluviometrosCombo(proyecto):
        conn = None
        sql = """SELECT * FROM pluviometros WHERE id_proyecto = ? AND estado_pluviometro = 1;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyecto,))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al listar pluviómetros: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
                
    @staticmethod
    def mdlActualizarLecturaPluviometro(tabla, datos, idproyecto, username, nombres):
        sql = f"""UPDATE {tabla} SET fecha_pluviometro = ?, medida_pluviometro = ?, observacion_pluviometro = ? WHERE id_detalle = ?;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # guardar en historial
            query_select = f"""SELECT fecha_pluviometro, medida_pluviometro, observacion_pluviometro, id_detalle FROM {tabla} WHERE id_detalle = ?;"""
            cur.execute(query_select, (datos[-1],))
            datos_anteriores = cur.fetchone()
            if datos_anteriores:
                fecha_cambio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                accion = "update"
                # tabla variable se sobreescribía en local variable
                tabla_historial = "pluviometro_detalle" 
                cambios = f"Antiguos: {datos_anteriores}, Nuevos: {datos}"
                query_historial = """INSERT INTO historial (idproyecto, fecha, accion, tabla, cambios, usuario, nombres)
                VALUES (?, ?, ?, ?, ?, ?, ?);"""
                cur.execute(query_historial, (idproyecto, fecha_cambio, accion, tabla_historial, cambios, username, nombres))
            # actualizar pluviometro
            cur.execute(sql, datos)
            conn.commit()
            return True
        except Exception as e:
            print("Error al editar lectura pluviometro: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlEliminarLecturaPluviometro(tabla, idpluviometro, idproyecto, username, nombres):
        sql = f"""DELETE FROM {tabla} WHERE id_detalle = ?;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # guardar en historial
            query_select = f"""SELECT * FROM {tabla} WHERE id_detalle = ?;"""
            cur.execute(query_select, (idpluviometro,))
            datos_anteriores = cur.fetchone()
            if datos_anteriores:
                fecha_cambio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                accion = "delete"
                cambios = f"Datos: {datos_anteriores}"
                query_historial = """INSERT INTO historial (idproyecto, fecha, accion, tabla, cambios, usuario, nombres)
                VALUES (?, ?, ?, ?, ?, ?, ?);"""
                cur.execute(query_historial, (idproyecto, fecha_cambio, accion, tabla, cambios, username, nombres))
            # eliminar lectura pluvio
            cur.execute(sql, (idpluviometro,))
            conn.commit()
            if cur.rowcount > 0:
                return True
            else:
                return False
        except Exception as e:
            print("Error al eliminar lectura pluviometro: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlEliminarLecturasBloquePluviometro(tabla, iddetalles, idproyecto, username, nombres):
        placeholders = ', '.join(['?' for _ in iddetalles])
        sql = f"""DELETE FROM {tabla} WHERE id_detalle IN ({placeholders});"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # guardar en historial
            query_select = f"""SELECT * FROM {tabla} WHERE id_detalle IN ({placeholders});"""
            cur.execute(query_select, iddetalles)
            datos_anteriores = cur.fetchall()
            if datos_anteriores:
                fecha_cambio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                accion = "delete"
                cambios = f"Datos: {datos_anteriores}"
                query_historial = """INSERT INTO historial (idproyecto, fecha, accion, tabla, cambios, usuario, nombres)
                VALUES (?, ?, ?, ?, ?, ?, ?);"""
                cur.execute(query_historial, (idproyecto, fecha_cambio, accion, tabla, cambios, username, nombres))
            # eliminar lecturas pluvio
            cur.execute(sql, iddetalles)
            conn.commit()
            if cur.rowcount > 0:
                return True
            else:
                return False
        except Exception as e:
            print("Error al eliminar lecturas pluviometro: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCambiarComponentePluviometros(idcomponente, nuevocomponente):
        sql = """UPDATE instrumentacion SET id_componente = ? WHERE id_componente = ? AND tipo_equipo = 'PLUVIOMETRO';"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # guardar info
            query_select = """SELECT * FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'PLUVIOMETRO';"""
            cur.execute(query_select, (idcomponente,))
            dataincli = cur.fetchall()
            if dataincli:
                cur.execute(sql, (nuevocomponente, idcomponente))
                conn.commit()
                return dataincli
            else:
                return None
        except Exception as e:
            print("Error al cambiar componente pluviometros: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlEliminarPluviometros(idcomponente):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # obtener info
            query_select = """SELECT * FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'PLUVIOMETRO';"""
            cursor.execute(query_select, (idcomponente,))
            datapluvio = cursor.fetchall()
            if datapluvio:
                query = """DELETE FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'PLUVIOMETRO';"""
                cursor.execute(query, (idcomponente,))
                conn.commit()
                if cursor.rowcount > 0:
                    return datapluvio
                else:
                    return None
            else:
                return None
        except Exception as e:
            print(f"Error al eliminar pluviometros: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlEliminarDataPluviometros(tabla, pluviometros):
        placeholders = ','.join(['?' for _ in pluviometros])
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # eliminar data
            query_delete = f"""DELETE FROM {tabla} WHERE id_pluviometro IN ({placeholders});"""
            cursor.execute(query_delete, pluviometros)
            rows_data = cursor.rowcount
            # En SQL Server, si no hay datos en la tabla detalle, aun así deberíamos intentar borrar el maestro
            # pero mantengo la lógica original: si se borran datos, se borran equipos.
            # OJO: Si la tabla detalle está vacía, no borrará los equipos. 
            # Sugerencia: Normalmente se borran equipos si se solicita, independientemente de si hay detalles.
            # Mantendré la lógica original adaptada:
            if rows_data >= 0: # Cambiado a >= 0 para permitir borrar equipos sin data
                query_delete_cuerdas = f"DELETE FROM pluviometros WHERE id_pluviometro IN ({placeholders});"
                cursor.execute(query_delete_cuerdas, pluviometros)
                rows_cuerdas = cursor.rowcount
                conn.commit()
                return rows_cuerdas > 0
            else:
                conn.rollback()
                return False
        except Exception as e:
            print(f"Error al eliminar data pluviometros: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerInfoPluviometro(idinstrumento):
        sql = """SELECT p.* FROM pluviometros p INNER JOIN instrumentacion i ON p.id_pluviometro = i.id_equipo WHERE i.id_instrumentacion = ?;"""
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
            print("Error al consultar info pluviometro: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # Eliminar pluviómetro
    @staticmethod
    def mdlEliminarPluviometro(idinstrumento):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # obtener info para eliminar data
            # SQL Server: TOP 1
            query_select = """SELECT TOP 1 * FROM instrumentacion WHERE id_instrumentacion = ? AND tipo_equipo = 'PLUVIOMETRO';"""
            cursor.execute(query_select, (idinstrumento,))
            datapluvio = cursor.fetchone()
            if datapluvio:
                query = """DELETE FROM instrumentacion WHERE id_instrumentacion = ? AND tipo_equipo = 'PLUVIOMETRO';"""
                cursor.execute(query, (idinstrumento,))
                conn.commit()
                if cursor.rowcount > 0:
                    return datapluvio
                else:
                    return None
            else:
                return None
        except Exception as e:
            print(f"Error al eliminar pluviometro: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlEliminarPluviometroData(tabla, idpluviometro):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # eliminar data
            query_delete = f"""DELETE FROM {tabla} WHERE id_pluviometro = ?;"""
            cursor.execute(query_delete, (idpluviometro,))
            rows_data = cursor.rowcount
            # Similar logic adjustment: allow delete master even if 0 details
            if rows_data >= 0:
                stmt_delete = "DELETE FROM pluviometros WHERE id_pluviometro = ?;"
                cursor.execute(stmt_delete, (idpluviometro,))
                rows_delete = cursor.rowcount
                conn.commit()
                return rows_delete > 0
            else:
                conn.rollback()
                return False
        except Exception as e:
            print(f"Error al eliminar data pluviometro: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerPluviometros(tabla, idcomponente, idinstrumento, fechaini, fechafin):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = f"""SELECT t.id_instrumentacion, d.fecha_pluviometro, d.medida_pluviometro FROM {tabla} d
            INNER JOIN pluviometros p ON d.id_pluviometro = p.id_pluviometro
            INNER JOIN instrumentacion t ON p.id_pluviometro = t.id_equipo
            INNER JOIN componentes c ON t.id_componente = c.id_componente
            WHERE c.id_componente = ? AND t.id_instrumentacion = ? AND d.fecha_pluviometro BETWEEN ? AND ?
            ORDER BY d.fecha_pluviometro;"""
            cur = conn.cursor()
            cur.execute(sql, (idcomponente, idinstrumento, fechaini, fechafin))
            results = cur.fetchall()
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al obtener data pluviometros:", e)
            return None  
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlTraerDataPluviometro(idpluviometro):
        sql = """SELECT i.id_instrumentacion, i.id_componente, c.nombre_componente FROM instrumentacion i
        INNER JOIN componentes c ON i.id_componente = c.id_componente
        WHERE i.id_equipo = ? AND i.tipo_equipo = 'PLUVIOMETRO';"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idpluviometro,))
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al traer data pluviometro: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCambiarPluviometroComponente(idinstrumento, nuevocomponente):
        sql = """UPDATE instrumentacion SET id_componente = ? WHERE id_instrumentacion = ?;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (nuevocomponente, idinstrumento))
            conn.commit()
            return True
        except Exception as e:
            print("Error al cambiar componente pluviometro: " + str(e))
            return False
        finally:
            if conn:
                conn.close()