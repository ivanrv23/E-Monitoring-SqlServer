from services.security.apis.conexiones.conexion import Connection
from datetime import datetime

class AcelerografoModel:
    
    def mdlObtenerFechaMaximaAcelerografos(tabla):
        sql = f"""SELECT MAX(fecha_detalle) AS max_fecha FROM {tabla};"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener fechas max acelerografos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlListarAcelerografoProyecto(proyecto, idcomponente, idacelero):
        try:
            conn = Connection.connectionDB()
            sql = """SELECT p.id_acelerografo, p.nombre_acelerografo, c.id_componente, p.este_acelerografo, p.norte_acelerografo,
            p.elevacion_acelerografo FROM acelerografos p INNER JOIN instrumentacion t ON p.id_acelerografo = t.id_equipo
            INNER JOIN componentes c ON t.id_componente = c.id_componente
            WHERE c.id_proyecto = ? AND t.id_equipo = ? AND c.id_componente = ?;"""
            cur = conn.cursor()
            cur.execute(sql, (proyecto, idacelero, idcomponente))
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al consultar acelerografo: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlObtenerMagnitud(tabla, idcomponente, acelerografos):
        try:
            placeholders = ', '.join(['?' for _ in acelerografos])
            params = [idcomponente] + acelerografos
            conn = Connection.connectionDB()
            sql = f"""SELECT c.id_componente, a.nombre_acelerografo, d.fecha_detalle, d.magnitud_detalle, d.distancia_detalle
            FROM acelerografos AS a INNER JOIN {tabla} AS d ON a.id_acelerografo = d.id_acelerografo 
            INNER JOIN instrumentacion t ON a.id_acelerografo = t.id_equipo
            INNER JOIN componentes c ON t.id_componente = c.id_componente
            WHERE c.id_componente = ? AND t.id_instrumentacion IN ({placeholders})
            ORDER BY a.nombre_acelerografo ASC, d.fecha_detalle ASC;"""
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return rows if rows else None
        except Exception as e:
            print("Error al obtener magnitud acelerografos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlObtenerMagnitudFechas(tabla, idcomponente, acelerografos, fechaini, fechafin):
        try:
            placeholders = ', '.join(['?' for _ in acelerografos])
            params = [idcomponente] + acelerografos + [fechaini] + [fechafin]
            conn = Connection.connectionDB()
            sql = f"""SELECT c.id_componente, a.nombre_acelerografo, d.fecha_detalle, d.magnitud_detalle, d.distancia_detalle
            FROM acelerografos AS a INNER JOIN {tabla} AS d ON a.id_acelerografo = d.id_acelerografo 
            INNER JOIN instrumentacion t ON a.id_acelerografo = t.id_equipo
            INNER JOIN componentes c ON t.id_componente = c.id_componente
            WHERE c.id_componente = ? AND t.id_instrumentacion IN ({placeholders}) AND d.fecha_detalle BETWEEN ? AND ?
            ORDER BY a.nombre_acelerografo ASC, d.fecha_detalle ASC;"""
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return rows if rows else None
        except Exception as e:
            print("Error al obtener magnitud acelerografos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlActualizarLecturaAcelerografo(tabla, datos, idproyecto, username, nombres):
        sql_update = f"""UPDATE {tabla} SET fecha_detalle = ?, magnitud_detalle = ?, distancia_detalle = ?, observacion_detalle = ? WHERE id_detalle = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # guardar en historial
            query_select = f"""SELECT fecha_detalle, magnitud_detalle, distancia_detalle, observacion_detalle, id_detalle FROM {tabla} WHERE id_detalle = ?;"""
            cur.execute(query_select, (datos[-1],))
            datos_anteriores = cur.fetchone()
            if datos_anteriores:
                fecha_cambio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                accion = "update"
                cambios = f"Antiguos: {datos_anteriores}, Nuevos: {datos}"
                query_historial = """INSERT INTO historial (idproyecto, fecha, accion, tabla, cambios, usuario, nombres)
                VALUES (?, ?, ?, ?, ?, ?, ?);"""
                cur.execute(query_historial, (idproyecto, fecha_cambio, accion, tabla, cambios, username, nombres))
            # actualizar lectura acelerografo
            cur.execute(sql_update, datos)
            conn.commit()
            return True
        except Exception as e:
            print("Error al actualizar lectura acelerografo:", e)
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlEliminarLecturaAcelerografo(tabla, idacelero, idproyecto, username, nombres):
        try:
            conn = Connection.connectionDB()
            sql = f"""DELETE FROM {tabla} WHERE id_detalle = ?;"""
            cur = conn.cursor()
            # guardar en historial
            query_select = f"""SELECT * FROM {tabla} WHERE id_detalle = ?;"""
            cur.execute(query_select, (idacelero,))
            datos_anteriores = cur.fetchone()
            if datos_anteriores:
                fecha_cambio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                accion = "delete"
                cambios = f"Datos: {datos_anteriores}"
                query_historial = """INSERT INTO historial (idproyecto, fecha, accion, tabla, cambios, usuario, nombres)
                VALUES (?, ?, ?, ?, ?, ?, ?);"""
                cur.execute(query_historial, (idproyecto, fecha_cambio, accion, tabla, cambios, username, nombres))
            # eliminar lectura
            cur.execute(sql, (idacelero,))
            conn.commit()
            if cur.rowcount > 0:
                return True
            else:
                return False
        except Exception as e:
            print("Error al eliminar lectura acelerografo: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlEliminarLecturasBloqueAcelerografo(tabla, iddetalles, idproyecto, username, nombres):
        placeholders = ', '.join(['?' for _ in iddetalles])
        sql = f"""DELETE FROM {tabla} WHERE id_detalle IN ({placeholders});"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # guardar en historial
            query_select = f'''SELECT * FROM {tabla} WHERE id_detalle IN ({placeholders});'''
            cur.execute(query_select, iddetalles)
            datos_anteriores = cur.fetchall()
            if datos_anteriores:
                fecha_cambio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                accion = "delete"
                cambios = f"Datos: {datos_anteriores}"
                query_historial = """INSERT INTO historial (idproyecto, fecha, accion, tabla, cambios, usuario, nombres)
                VALUES (?, ?, ?, ?, ?, ?, ?);"""
                cur.execute(query_historial, (idproyecto, fecha_cambio, accion, tabla, cambios, username, nombres))
            # eliminar lecturas acelero
            cur.execute(sql, iddetalles)
            conn.commit()
            if cur.rowcount > 0:
                return True
            else:
                return False
        except Exception as e:
            print("Error al eliminar lecturas acelerografo: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlComprobarExisteNombreAcelerografo(proyecto, nombre):
        sql = """SELECT * FROM acelerografos WHERE id_proyecto = ? AND nombre_acelerografo = ?;"""
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
            print("Error al comprobar Acelerografo: " + str(e))
            return False, None
        finally:
            if conn:
                conn.close()
    
    def mdlRegistrarAcelerografo(proyecto_id, datos):
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # Verificar si el equipo ya existe en la tabla instrumentacion
            sql_check = """SELECT 1 FROM instrumentacion WHERE id_componente = ? AND nombre_equipo = ? AND tipo_equipo = 'ACELEROGRAFO';"""
            cur.execute(sql_check, (datos[4], datos[0]))
            if cur.fetchone():
                print("El equipo ya existe en la tabla instrumentacion.")
                return "NO", None
            # Insertar el nuevo acelerógrafo y obtener el ID generado
            sql_insert = """INSERT INTO acelerografos (id_proyecto, nombre_acelerografo, este_acelerografo, norte_acelerografo,
            elevacion_acelerografo) OUTPUT INSERTED.id_acelerografo VALUES (?, ?, ?, ?, ?);"""
            cur.execute(sql_insert, (proyecto_id, datos[0], datos[1], datos[2], datos[3]))
            # Obtener el ID del acelerógrafo recién insertado
            acelerografo_id = cur.fetchone()[0]
            # Insertar en la tabla instrumentacion
            sql_insert_instrumentacion = """INSERT INTO instrumentacion (id_componente, tipo_equipo, nombre_equipo, id_equipo,
            tabla_equipo) VALUES (?, ?, ?, ?, ?);"""
            cur.execute(sql_insert_instrumentacion, (datos[4], 'ACELEROGRAFO', datos[0], acelerografo_id, 'acelerografos'))
            # Confirmar la transacción
            conn.commit()
            return "SI", acelerografo_id
        except Exception as e:
            print("Error al guardar Acelerografo:", e)
            # Realizar un rollback en caso de error
            conn.rollback()
            return "ERROR", None
        finally:
            if conn:
                conn.close()

    def mdlRegistrarFormatoAcelerografo(proyecto_id, datos):
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # Insertar el nuevo acelerógrafo y obtener el ID generado
            sql_insert = """INSERT INTO acelerografos (id_proyecto, nombre_acelerografo, este_acelerografo, norte_acelerografo,
            elevacion_acelerografo) OUTPUT INSERTED.id_acelerografo VALUES (?, ?, ?, ?, ?);"""
            cur.execute(sql_insert, (proyecto_id, datos[0], datos[1], datos[2], datos[3]))
            # Obtener el ID del acelerógrafo recién insertado
            acelerografo_id = cur.fetchone()[0]
            # Insertar en la tabla instrumentacion
            sql_insert_instrumentacion = """INSERT INTO instrumentacion (id_componente, tipo_equipo, nombre_equipo, id_equipo,
            tabla_equipo) VALUES (?, ?, ?, ?, ?);"""
            cur.execute(sql_insert_instrumentacion, (datos[4], 'ACELEROGRAFO', datos[0], acelerografo_id, 'acelerografos'))
            # Confirmar la transacción
            conn.commit()
            return acelerografo_id
        except Exception as e:
            print("Error al guardar Acelerografo formato:", e)
            # Realizar un rollback en caso de error
            conn.rollback()
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlObtenerAcelerografos(proyectoID):
        try:
            conn = Connection.connectionDB()
            sql = """SELECT * FROM acelerografos WHERE id_proyecto = ?;"""
            cur = conn.cursor()
            cur.execute(sql, (proyectoID,))
            results = cur.fetchall()
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al obtener acelerografos:", e)
            return None  
        finally:
            if conn:
                conn.close()
                
    def mdlRegistrarDataAcelerografo(proyectoID, datos):
        tabla = f'acelerografo_detalle{proyectoID}'
        # Crear tabla si no existe (SQL Server)
        crear_tabla_sql = f"""IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = '{tabla}')
        BEGIN
            CREATE TABLE {tabla} (
                [id_detalle] INT IDENTITY(1,1) PRIMARY KEY,
                [id_acelerografo] INT NOT NULL,
                [fecha_detalle] NVARCHAR(50) NOT NULL,
                [magnitud_detalle] DECIMAL(18,6) NOT NULL,
                [distancia_detalle] DECIMAL(18,6) NOT NULL,
                [observacion_detalle] NVARCHAR(MAX)
            );
        END"""
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # Crear tabla si no existe
            cursor.execute(crear_tabla_sql)
            conn.commit()
            # Crear un conjunto de tuplas con los valores de fecha y hora para comparar los registros existentes
            idacelero = datos[0][0]
            cursor.execute(f"SELECT fecha_detalle FROM {tabla} WHERE id_acelerografo = ?;", (idacelero,))
            existen_acelero = set([row[0] for row in cursor.fetchall()])
            lote_registros = []
            contador = 0
            for fila in datos:
                if len(fila) < 5 or not fila[3] or not fila[4]:
                    continue
                fecha_original = fila[1]
                hora_original = fila[2]
                fecha_hora_nueva = fecha_original + " " + hora_original
                # Verifica si el registro no existe en el conjunto
                if fecha_hora_nueva not in existen_acelero:
                    datito = (fila[0], fecha_hora_nueva, fila[3], fila[4])
                    lote_registros.append(datito)
                    contador += 1
                if contador % 1000 == 0 and lote_registros:
                    cursor.executemany(f"""INSERT INTO {tabla} (id_acelerografo, fecha_detalle, magnitud_detalle, distancia_detalle)
                                       VALUES (?, ?, ?, ?);""", lote_registros)
                    conn.commit()
                    lote_registros = []
            if lote_registros:
                cursor.executemany(f"""INSERT INTO {tabla} (id_acelerografo, fecha_detalle, magnitud_detalle, distancia_detalle)
                                   VALUES (?, ?, ?, ?);""", lote_registros)
                conn.commit()
            return True
        except Exception as e:
            print("Error al guardar data acelerografos: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlCambiarComponenteAcelerografos(idcomponente, nuevocomponente):
        sql = """UPDATE instrumentacion SET id_componente = ? WHERE id_componente = ? AND tipo_equipo = 'ACELEROGRAFO';"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # guardar info
            query_select = """SELECT * FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'ACELEROGRAFO';"""
            cur.execute(query_select, (idcomponente,))
            datasismos = cur.fetchall()
            if datasismos:
                cur.execute(sql, (nuevocomponente, idcomponente))
                conn.commit()
                return datasismos
            else:
                return None
        except Exception as e:
            print("Error al cambiar componente acelerografos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlEliminarAcelerografos(idcomponente):
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # obtener info
            query_select = """SELECT * FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'ACELEROGRAFO';"""
            cursor.execute(query_select, (idcomponente,))
            datasismos = cursor.fetchall()
            if datasismos:
                query = """DELETE FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'ACELEROGRAFO';"""
                cursor.execute(query, (idcomponente,))
                conn.commit()
                if cursor.rowcount > 0:
                    return datasismos
                else:
                    return None
            else:
                return None
        except Exception as e:
            print(f"Error al eliminar acelerografos: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlEliminarDataAcelerografos(tabla, sismos):
        placeholders = ','.join(['?' for _ in sismos])
        respuesta = False
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # eliminar
            stmt_delete = f"DELETE FROM acelerografos WHERE id_acelerografo IN ({placeholders});"
            cursor.execute(stmt_delete, sismos)
            conn.commit()
            respuesta = True
            # eliminar data
            query_delete = f"""DELETE FROM {tabla} WHERE id_acelerografo IN ({placeholders});"""
            cursor.execute(query_delete, sismos)
            conn.commit()
            respuesta = True
            return respuesta
        except Exception as e:
            print(f"Error al eliminar data acelerografos: {e}")
            return respuesta
        finally:
            if conn:
                conn.close()
    
    def mdlObtenerInfoAcelerografo(idinstrumento):
        sql = """SELECT a.* FROM acelerografos a INNER JOIN instrumentacion i ON a.id_acelerografo = i.id_equipo WHERE i.id_instrumentacion = ?;"""
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
            print("Error al consultar info acelerografo: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlActualizarAcelerografo(datos, data):
        query = """UPDATE acelerografos SET nombre_acelerografo = ?, este_acelerografo = ?, norte_acelerografo = ?,
        elevacion_acelerografo = ? WHERE id_acelerografo = ?;"""
        try:
            conexion = Connection.connectionDB()
            cursor = conexion.cursor()
            cursor.execute(query, datos)
            query_instrumentacion = """UPDATE instrumentacion SET id_componente = ?, nombre_equipo = ?
            WHERE id_instrumentacion = ? AND tipo_equipo = 'ACELEROGRAFO';"""
            cursor.execute(query_instrumentacion, data)
            conexion.commit()
            return True
        except Exception as e:
            print(f"Error al actualizar acelerografo: {e}")
            return False
        finally:
            if conexion:
                conexion.close()
    
    def mdlEliminarAcelerografo(idinstrumento):
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # obtener info para eliminar data
            query_select = """SELECT * FROM instrumentacion WHERE id_instrumentacion = ? AND tipo_equipo = 'ACELEROGRAFO';"""
            cursor.execute(query_select, (idinstrumento,))
            dataacelero = cursor.fetchone()
            if dataacelero:
                query = """DELETE FROM instrumentacion WHERE id_instrumentacion = ? AND tipo_equipo = 'ACELEROGRAFO';"""
                cursor.execute(query, (idinstrumento,))
                conn.commit()
                if cursor.rowcount > 0:
                    return dataacelero
                else:
                    return None
            else:
                return None
        except Exception as e:
            print(f"Error al eliminar acelerografo: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlEliminarAcelerografoData(tabla, idacelero):
        respuesta = False
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            stmt_delete = "DELETE FROM acelerografos WHERE id_acelerografo = ?;"
            cursor.execute(stmt_delete, (idacelero,))
            conn.commit()
            respuesta = True
            # eliminar data
            query_delete = f"""DELETE FROM {tabla} WHERE id_acelerografo = ?;"""
            cursor.execute(query_delete, (idacelero,))
            conn.commit()
            respuesta = True
            return respuesta
        except Exception as e:
            print(f"Error al eliminar data acelerografo: {e}")
            return respuesta
        finally:
            if conn:
                conn.close()
    
    def mdlObtenerUmbralesAcelerografoComponente(idproyecto, idcomponente, tipo):
        try:
            conn = Connection.connectionDB()
            sql = """SELECT * FROM umbral_acelerografo WHERE id_proyecto = ? AND id_componente = ? AND tipo_umbral = ?;"""
            cur = conn.cursor()
            cur.execute(sql, (idproyecto, idcomponente, tipo))
            results = cur.fetchall()
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al obtener umbrales acelerografo:", e)
            return None  
        finally:
            if conn:
                conn.close()
    
    def mdlTraerDataAcelerografo(idacelero):
        sql = """SELECT i.id_instrumentacion, i.id_componente, c.nombre_componente FROM instrumentacion i
        INNER JOIN componentes c ON i.id_componente = c.id_componente
        WHERE i.id_equipo = ? AND i.tipo_equipo = 'ACELEROGRAFO';"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idacelero,))
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al traer data acelerografo: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlCambiarAcelerografoComponente(idinstrumento, nuevocomponente):
        sql = """UPDATE instrumentacion SET id_componente = ? WHERE id_instrumentacion = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (nuevocomponente, idinstrumento))
            conn.commit()
            return True
        except Exception as e:
            print("Error al cambiar componente acelerografo: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    