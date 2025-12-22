from services.security.apis.conexiones.conexion import Connection
from datetime import datetime

class TDRModel:

    @staticmethod
    def mdlObtenerLecturasTDR(tabla, idcomponente, idinstrumento, unidadmedida, fechas):
        placeholders = ', '.join(['?' for _ in fechas])
        # Nota: pyodbc espera los parámetros en una lista o tupla plana
        params = [unidadmedida, idcomponente, idinstrumento] + fechas
        try:
            conn = Connection.connectionDB()           
            # SQL Server: INNER JOIN sintaxis estándar.
            sql = f"""SELECT s.nombre_sondajetdr, s.base_sondajetdr, sd.fecha_detalle, 
            sd.profundidad_detalle * ? AS profundidad, sd.impedancia_detalle 
            FROM sondajestdr s 
            INNER JOIN {tabla} sd ON s.id_sondajetdr = sd.id_sondajetdr
            INNER JOIN instrumentacion t ON s.id_sondajetdr = t.id_equipo
            INNER JOIN componentes c ON t.id_componente = c.id_componente
            WHERE c.id_componente = ? AND t.id_instrumentacion = ? AND sd.fecha_detalle IN ({placeholders})
            ORDER BY sd.fecha_detalle ASC;"""
            cur = conn.cursor()
            cur.execute(sql, params)
            results = cur.fetchall()
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al obtener lecturas tdr:", e)
            return None  
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlObtenerFallasTDR(idcomponente, idinstrumento):
        try:
            conn = Connection.connectionDB()           
            sql = """SELECT s.* from sondajestdr_puntos s 
            INNER JOIN instrumentacion t ON s.id_sondajetdr = t.id_equipo
            INNER JOIN componentes c ON t.id_componente = c.id_componente
            WHERE c.id_componente = ? AND t.id_instrumentacion = ?;"""
            cur = conn.cursor()
            cur.execute(sql, (idcomponente, idinstrumento))
            results = cur.fetchall() 
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al obtener fallas tdr:", e)
            return None  
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlComprobarExisteNombreTDR(proyecto, nombre):
        sql = """SELECT * FROM sondajestdr WHERE id_proyecto = ? AND nombre_sondajetdr = ?;"""
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
            print("Error al comprobar TDR: " + str(e))
            return False, None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlComprobarExisteFechasTDR(tabla, idsondaje, fecha):
        sql = f"""SELECT * FROM {tabla} WHERE id_sondajetdr = ? AND fecha_detalle = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idsondaje, fecha))
            rows = cur.fetchall()
            return len(rows) > 0
        except Exception as e:
            print("Error al comprobar fecha TDR: " + str(e))
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlGuardarEquipoTDR(proyecto, data):
        # En SQL Server SELECT 1 es válido
        sql_check = """SELECT 1 FROM instrumentacion WHERE nombre_equipo = ? AND id_componente = ?;"""
        sql_insert_sondajestdr = """INSERT INTO sondajestdr (id_proyecto, nombre_sondajetdr, este_sondajetdr, norte_sondajetdr, elevacion_sondajetdr, azimut_sondajetdr,
        inclinacion_sondajetdr, profundidad_sondajetdr) VALUES (?, ?, ?, ?, ?, ?, ?, ?);"""
        sql_insert_instrumentacion = """INSERT INTO instrumentacion (id_componente, tipo_equipo, nombre_equipo, id_equipo, tabla_equipo) VALUES (?, ?, ?, ?, ?);"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # Pyodbc maneja transacciones implícitas, pero si se desea explicito:
            # En SQL Server con pyodbc no es necesario "BEGIN TRANSACTION" explícito si se usa commit al final.
            
            # Verificar si el nombre y el componente ya existen en la tabla instrumentacion
            cur.execute(sql_check, (data[0], data[7]))
            if cur.fetchone():
                return "NO"
            
            # Insertar en la tabla sondajestdr
            cur.execute(sql_insert_sondajestdr, (proyecto, data[0], data[1], data[2], data[3], data[4], data[5], data[6]))
            
            # Obtener el último ID insertado (Sintaxis T-SQL)
            cur.execute("SELECT SCOPE_IDENTITY();")
            row_id = cur.fetchone()
            if row_id and row_id[0] is not None:
                id_equipo = int(row_id[0])
            else:
                conn.rollback()
                return False

            # Insertar en la tabla instrumentacion
            cur.execute(sql_insert_instrumentacion, (data[7], 'TDR', data[0], id_equipo, 'sondajestdr'))
            
            # Confirmar la transacción
            conn.commit()
            return True
        except Exception as e:
            print("Error al guardar sondaje: " + str(e))
            # Deshacer la transacción en caso de error
            conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlRegistrarFormatoEquipoTDR(proyecto, data):
        sql_insert_sondajestdr = """INSERT INTO sondajestdr (id_proyecto, nombre_sondajetdr, este_sondajetdr, norte_sondajetdr, elevacion_sondajetdr, azimut_sondajetdr,
        inclinacion_sondajetdr, profundidad_sondajetdr) VALUES (?, ?, ?, ?, ?, ?, ?, ?);"""
        sql_insert_instrumentacion = """INSERT INTO instrumentacion (id_componente, tipo_equipo, nombre_equipo, id_equipo, tabla_equipo) VALUES (?, ?, ?, ?, ?);"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            
            # Insertar en la tabla sondajestdr
            cur.execute(sql_insert_sondajestdr, (proyecto, data[0], data[1], data[2], data[3], data[4], data[5], data[6]))
            
            # Obtener el último ID insertado
            cur.execute("SELECT SCOPE_IDENTITY();")
            row_id = cur.fetchone()
            if row_id and row_id[0] is not None:
                id_equipo = int(row_id[0])
            else:
                conn.rollback()
                return None

            # Insertar en la tabla instrumentacion
            cur.execute(sql_insert_instrumentacion, (data[7], 'TDR', data[0], id_equipo, 'sondajestdr'))
            
            # Confirmar la transacción
            conn.commit()
            return id_equipo
        except Exception as e:
            print("Error al guardar sondaje formato: " + str(e))
            conn.rollback()
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlActualizarLecturaSondajetdr(tabla, datos, idproyecto, username, nombres):
        sql = f"""UPDATE {tabla} SET profundidad_detalle = ?, impedancia_detalle = ?, observacion_detalle = ? WHERE id_detalle = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # guardar en historial
            query_select = f"""SELECT profundidad_detalle, impedancia_detalle, observacion_detalle, id_detalle FROM {tabla} WHERE id_detalle = ?;"""
            cur.execute(query_select, (datos[-1],))
            datos_anteriores = cur.fetchone()
            if datos_anteriores:
                fecha_cambio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                accion = "update"
                cambios = f"Antiguos: {datos_anteriores}, Nuevos: {datos}"
                query_historial = """INSERT INTO historial (idproyecto, fecha, accion, tabla, cambios, usuario, nombres)
                VALUES (?, ?, ?, ?, ?, ?, ?);"""
                cur.execute(query_historial, (idproyecto, fecha_cambio, accion, tabla, cambios, username, nombres))
            # actualizar tdr
            cur.execute(sql, datos)
            conn.commit()
            return True
        except Exception as e:
            print("Error al editar lectura tdr: " + str(e))
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlListarSondajetdrProyecto(proyecto, idcomponente, idtdr):
        sql = """SELECT c.id_componente, p.* FROM sondajestdr p INNER JOIN instrumentacion t
        ON p.id_sondajetdr = t.id_equipo INNER JOIN componentes c ON t.id_componente = c.id_componente
        WHERE c.id_proyecto = ? AND t.id_equipo = ? AND c.id_componente = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyecto, idtdr, idcomponente))
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al consultar sondaje tdr: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlObtenerListaSondajes(proyecto):
        try:
            conn = Connection.connectionDB()
            sql = """SELECT id_sondajetdr, nombre_sondajetdr FROM sondajestdr WHERE id_proyecto = ?"""
            cur = conn.cursor()
            cur.execute(sql,(proyecto,))
            row = cur.fetchall()  
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener datos:", e)
            return None 
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlGuardarDataSondajesTDR(proyectoid, data):
        tabla = f'sondajetdr_detalle{proyectoid}'
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            
            # Verificar si la tabla existe y crearla si no existe (Sintaxis T-SQL)
            # Se usa DECIMAL(18,5) para asegurar precisión en lugar de NUMERIC genérico
            # IDENTITY(1,1) reemplaza a AUTOINCREMENT
            cursor.execute(f"""
                IF OBJECT_ID('{tabla}', 'U') IS NULL
                BEGIN
                    CREATE TABLE {tabla} (
                        id_detalle INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
                        id_sondajetdr INT NOT NULL,
                        profundidad_detalle DECIMAL(18,5),
                        fecha_detalle NVARCHAR(50),
                        impedancia_detalle DECIMAL(18,5),
                        observacion_detalle NVARCHAR(MAX)
                    )
                END
            """)
            
            # Eliminados PRAGMAs de SQLite ya que no existen en SQL Server
            
            # Crear un conjunto de tuplas con los valores de fecha y hora para comparar los registros existentes
            idtdr = data[0][0]
            existen_tdr = set([(row[0]) for row in cursor.execute(f"SELECT DISTINCT fecha_detalle FROM {tabla} WHERE id_sondajetdr = ?;", (idtdr,))])
            lote_registros = []
            contador = 0
            
            for fila in data:
                fecha_original = fila[1]
                hora_original = fila[2]
                fecha_hora_nueva = fecha_original + " " + hora_original
                # Verifica si el registro no existe en el conjunto
                if (fecha_hora_nueva) not in existen_tdr:
                    datito = []
                    datito.append(fila[0])
                    datito.append(fecha_hora_nueva)
                    datito.append(abs(float(fila[3])))  # siempre positivo la profund
                    datito.append(fila[4])
                    datito.append(fila[5])
                    lote_registros.append(datito)
                    contador += 1
                
                # Insertar en lotes
                if contador % 1000 == 0 and lote_registros:
                    cursor.executemany(f"""INSERT INTO {tabla} (id_sondajetdr, fecha_detalle, profundidad_detalle, impedancia_detalle, observacion_detalle) VALUES (?, ?, ?, ?, ?)""", lote_registros)
                    lote_registros = []
            
            # Insertar remanentes
            if lote_registros:
                cursor.executemany(f"""INSERT INTO {tabla} (id_sondajetdr, fecha_detalle, profundidad_detalle, impedancia_detalle, observacion_detalle) VALUES (?, ?, ?, ?, ?)""", lote_registros)
            
            conn.commit()
            return True
        except Exception as e:
            print("Error al guardar la data tdr: " + str(e))
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlMostrarLecturasSondajeTDR(idsondaje):
        try:
            conn = Connection.connectionDB()
            sql = """SELECT * FROM sondajestdr_puntos WHERE id_sondajetdr = ?;"""
            cur = conn.cursor()
            cur.execute(sql,(idsondaje,))
            row = cur.fetchall()  
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener lecturas tdr:", e)
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlEliminarPuntoSondajes(id_punto):
        sql = """DELETE FROM sondajestdr_puntos WHERE id_detalle = ?"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (id_punto,))
            conn.commit()
            return True
        except Exception as e:
            print("Error al eliminar detalles sondaje: " + str(e))
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlRegistarMedidasSondaje(data):
        sql = """INSERT INTO sondajestdr_puntos (id_sondajetdr, tipo_detalle, medida_detalle, color_detalle, orden_detalle)
                VALUES (?, ?, ?, ?, ?);"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, data)
            conn.commit()
            return True
        except Exception as e:
            print("Error al registrar falla tdr: " + str(e))
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlValidarExisteFallaTDR(idsondaje, posicion):
        try:
            conn = Connection.connectionDB()
            sql = """SELECT COUNT(1) FROM sondajestdr_puntos WHERE id_sondajetdr = ? AND orden_detalle = ?;"""
            cur = conn.cursor()
            cur.execute(sql, (idsondaje, posicion))
            count = cur.fetchone()[0]
            return count > 0
        except Exception as e:
            print("Error al validar falla tdr:", e)
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlActualizarMedidasSondaje(data):
        sql = """UPDATE sondajestdr_puntos SET tipo_detalle = ?, medida_detalle = ?, color_detalle = ?
        WHERE id_sondajetdr = ? AND orden_detalle = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (data[1], data[2], data[3], data[0], data[4]))
            conn.commit()
            return True
        except Exception as e:
            print("Error al actualizar falla tdr: " + str(e))
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlCambiarComponenteSondajesTDR(idcomponente, nuevocomponente):
        sql = """UPDATE instrumentacion SET id_componente = ? WHERE id_componente = ? AND tipo_equipo = 'TDR';"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # guardar info
            query_select = """SELECT * FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'TDR';"""
            cur.execute(query_select, (idcomponente,))
            datatdr = cur.fetchall()
            if datatdr:
                cur.execute(sql, (nuevocomponente, idcomponente))
                conn.commit()
                return datatdr
            else:
                return None
        except Exception as e:
            print("Error al cambiar componente TDRs: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlEliminarSondajesTDR(idcomponente):
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # obtener info
            query_select = """SELECT * FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'TDR';"""
            cursor.execute(query_select, (idcomponente,))
            datatdr = cursor.fetchall()
            if datatdr:
                query = """DELETE FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'TDR';"""
                cursor.execute(query, (idcomponente,))
                # En pyodbc rowcount devuelve las filas afectadas por el último execute
                rows_affected = cursor.rowcount
                conn.commit()
                if rows_affected > 0:
                    return datatdr
                else:
                    return None
            else:
                return None
        except Exception as e:
            print(f"Error al eliminar TDRs: {e}")
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlEliminarDataSondajesTDR(tabla, sondajes):
        placeholders = ','.join(['?' for _ in sondajes])
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # eliminar data
            query_delete = f"""DELETE FROM {tabla} WHERE id_sondajetdr IN ({placeholders});"""
            cursor.execute(query_delete, sondajes)
            rows_data = cursor.rowcount
            if rows_data > 0:
                stmt_delete = f"DELETE FROM sondajestdr WHERE id_sondajetdr IN ({placeholders});"
                cursor.execute(stmt_delete, sondajes)
                rows_delete = cursor.rowcount
                conn.commit()
                return rows_delete > 0
            else:
                conn.rollback()
                return False
        except Exception as e:
            print(f"Error al eliminar data TDRs: {e}")
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlObtenerInfoSondajeTDR(idinstrumento):
        sql = """SELECT s.* FROM sondajestdr s INNER JOIN instrumentacion i ON s.id_sondajetdr = i.id_equipo WHERE i.id_instrumentacion = ?;"""
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
            print("Error al consultar info tdr: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlActualizarSondajeTDR(datos, data):
        query = """UPDATE sondajestdr SET nombre_sondajetdr = ?, este_sondajetdr = ?, norte_sondajetdr = ?, elevacion_sondajetdr = ?,
        profundidad_sondajetdr = ?, inclinacion_sondajetdr = ?, azimut_sondajetdr = ? WHERE id_sondajetdr = ?;"""
        try:
            conexion = Connection.connectionDB()
            cursor = conexion.cursor()
            cursor.execute(query, datos)
            query_instrumentacion = """UPDATE instrumentacion SET id_componente = ?, nombre_equipo = ?
            WHERE id_instrumentacion = ? AND tipo_equipo = 'TDR';"""
            cursor.execute(query_instrumentacion, data)
            conexion.commit()
            return True
        except Exception as e:
            print(f"Error al actualizar TDR: {e}")
            return False
        finally:
            if conexion:
                conexion.close()

    @staticmethod
    def mdlEliminarSondajetdr(idinstrumento):
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # obtener info para eliminar data
            query_select = """SELECT * FROM instrumentacion WHERE id_instrumentacion = ? AND tipo_equipo = 'TDR';"""
            cursor.execute(query_select, (idinstrumento,))
            datatdr = cursor.fetchone()
            if datatdr:
                query = """DELETE FROM instrumentacion WHERE id_instrumentacion = ? AND tipo_equipo = 'TDR';"""
                cursor.execute(query, (idinstrumento,))
                rows_affected = cursor.rowcount
                conn.commit()
                if rows_affected > 0:
                    return datatdr
                else:
                    return None
            else:
                return None
        except Exception as e:
            print(f"Error al eliminar tdr: {e}")
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlEliminarSondajetdrData(tabla, idtdr):
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # eliminar data
            query_delete = f"""DELETE FROM {tabla} WHERE id_sondajetdr = ?;"""
            cursor.execute(query_delete, (idtdr,))
            rows_data = cursor.rowcount
            if rows_data > 0:
                stmt_delete = "DELETE FROM sondajestdr WHERE id_sondajetdr = ?;"
                cursor.execute(stmt_delete, (idtdr,))
                rows_delete = cursor.rowcount
                conn.commit()
                return rows_delete > 0
            else:
                conn.rollback()
                return False
        except Exception as e:
            print(f"Error al eliminar data tdr: {e}")
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlListarFechasSondajetdr(tabla, idcomponente, idinstrumento):
        conn = Connection.connectionDB()
        sql = f"""SELECT DISTINCT sd.fecha_detalle, s.base_sondajetdr, s.id_sondajetdr
        FROM sondajestdr s INNER JOIN {tabla} sd ON s.id_sondajetdr = sd.id_sondajetdr
        INNER JOIN instrumentacion t ON s.id_sondajetdr = t.id_equipo
        INNER JOIN componentes c ON t.id_componente = c.id_componente
        WHERE c.id_componente = ? AND t.id_instrumentacion = ?
        ORDER BY sd.fecha_detalle ASC;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (idcomponente, idinstrumento))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al consultar fechas TDR: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlCambiarBaseSondajetdr(fecha, idsondaje):
        sql = """UPDATE sondajestdr SET base_sondajetdr = ? WHERE id_sondajetdr = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (fecha, idsondaje))
            conn.commit()
            return True
        except Exception as e:
            print("Error al cambiar estado base TDR: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlTraerDataSondajetdr(idsondaje):
        sql = """SELECT i.id_instrumentacion, i.id_componente, c.nombre_componente FROM instrumentacion i
        INNER JOIN componentes c ON i.id_componente = c.id_componente
        WHERE i.id_equipo = ? AND i.tipo_equipo = 'TDR';"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idsondaje,))
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al traer data sondaje tdr: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlCambiarSondajetdrComponente(idinstrumento, nuevocomponente):
        sql = """UPDATE instrumentacion SET id_componente = ? WHERE id_instrumentacion = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (nuevocomponente, idinstrumento))
            conn.commit()
            return True
        except Exception as e:
            print("Error al cambiar componente tdr: " + str(e))
            return False
        finally:
            if conn:
                conn.close()