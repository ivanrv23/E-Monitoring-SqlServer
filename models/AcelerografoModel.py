from services.security.apis.conexiones.connection import Connection
from datetime import datetime

class AcelerografoModel:
    
    @staticmethod
    def mdlObtenerFechaMaximaAcelerografos(tabla):
        # T-SQL: Sintaxis estándar compatible.
        sql = f"""SELECT MAX(fecha_detalle) AS max_fecha FROM {tabla};"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchone()
            if row:
                return tuple(row) # Conversión explícita a tupla
            else:
                return None
        except Exception as e:
            print("Error al obtener fechas max acelerografos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlListarAcelerografoProyecto(proyecto, idcomponente, idacelero):
        conn = None
        sql = f"""SELECT p.id_acelerografo, p.nombre_acelerografo, c.id_componente, p.este_acelerografo, p.norte_acelerografo,
        p.elevacion_acelerografo FROM acelerografos p INNER JOIN instrumentacion t ON p.id_acelerografo = t.id_equipo
		INNER JOIN componentes c ON t.id_componente = c.id_componente
        WHERE c.id_proyecto = ? AND t.id_equipo = ? AND c.id_componente = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyecto, idacelero, idcomponente))
            row = cur.fetchone()
            if row:
                return tuple(row)
            else:
                return None
        except Exception as e:
            print("Error al consultar acelerografo: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerMagnitud(tabla, idcomponente, acelerografos):
        placeholders = ', '.join(['?' for _ in acelerografos])
        params = [idcomponente] + acelerografos
        conn = None
        # T-SQL: Se mantiene igual, compatible ANSI.
        sql = f"""SELECT c.id_componente, a.nombre_acelerografo, d.fecha_detalle, d.magnitud_detalle, d.distancia_detalle
        FROM acelerografos AS a INNER JOIN {tabla} AS d ON a.id_acelerografo = d.id_acelerografo 
        INNER JOIN instrumentacion t ON a.id_acelerografo = t.id_equipo
        INNER JOIN componentes c ON t.id_componente = c.id_componente
        WHERE c.id_componente = ? AND t.id_instrumentacion IN ({placeholders})
        ORDER BY a.nombre_acelerografo ASC, d.fecha_detalle ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            # Conversión de lista de Rows a lista de Tuplas para el frontend
            return [tuple(row) for row in rows] if rows else None
        except Exception as e:
            print("Error al obtener magnitud acelerografos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerMagnitudFechas(tabla, idcomponente, acelerografos, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in acelerografos])
        params = [idcomponente] + acelerografos + [fechaini] + [fechafin]
        conn = None
        sql = f"""SELECT c.id_componente, a.nombre_acelerografo, d.fecha_detalle, d.magnitud_detalle, d.distancia_detalle
        FROM acelerografos AS a INNER JOIN {tabla} AS d ON a.id_acelerografo = d.id_acelerografo 
        INNER JOIN instrumentacion t ON a.id_acelerografo = t.id_equipo
        INNER JOIN componentes c ON t.id_componente = c.id_componente
        WHERE c.id_componente = ? AND t.id_instrumentacion IN ({placeholders}) AND d.fecha_detalle BETWEEN ? AND ?
        ORDER BY a.nombre_acelerografo ASC, d.fecha_detalle ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [tuple(row) for row in rows] if rows else None
        except Exception as e:
            print("Error al obtener magnitud acelerografos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlActualizarLecturaAcelerografo(tabla, datos, idproyecto, username, nombres):
        # T-SQL: UPDATE estándar
        sql_insert = f"""UPDATE {tabla} SET fecha_detalle = ?, magnitud_detalle = ?, distancia_detalle = ?, observacion_detalle = ?, estado_detalle = ? WHERE id_detalle = ?;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            estado_texto = datos[4]
            estado_valor = 1 if estado_texto == "Activo" else 0
            data_final = list(datos[:4]) + [estado_valor, datos[5]]
            # guardar en historial
            query_select = f"""SELECT fecha_detalle, magnitud_detalle, distancia_detalle, observacion_detalle, estado_detalle, id_detalle FROM {tabla} WHERE id_detalle = ?;"""
            cur.execute(query_select, (datos[5],))
            row = cur.fetchone()
            datos_anteriores = tuple(row) if row else None
            
            if datos_anteriores:
                fecha_cambio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                accion = "update"
                cambios = f"Antiguos: {datos_anteriores}, Nuevos: {datos}"
                query_historial = """INSERT INTO historial (idproyecto, fecha, accion, tabla, cambios, usuario, nombres)
                VALUES (?, ?, ?, ?, ?, ?, ?);"""
                cur.execute(query_historial, (idproyecto, fecha_cambio, accion, tabla, cambios, username, nombres))
            
            # actualizar
            cur.execute(sql_insert, data_final)
            conn.commit()
            return True
        except Exception as e:
            print("Error al actualizar lectura acelerografo:", e)
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlEliminarLecturaAcelerografo(tabla, idacelero, idproyecto, username, nombres):
        conn = None
        sql = f"""DELETE FROM {tabla} WHERE id_detalle = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # guardar en historial
            query_select = f"""SELECT * FROM {tabla} WHERE id_detalle = ?;"""
            cur.execute(query_select, (idacelero,))
            row = cur.fetchone()
            datos_anteriores = tuple(row) if row else None
            
            if datos_anteriores:
                fecha_cambio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                accion = "delete"
                cambios = f"Datos: {datos_anteriores}"
                query_historial = """INSERT INTO historial (idproyecto, fecha, accion, tabla, cambios, usuario, nombres)
                VALUES (?, ?, ?, ?, ?, ?, ?);"""
                cur.execute(query_historial, (idproyecto, fecha_cambio, accion, tabla, cambios, username, nombres))
            
            # eliminar lectura celda
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
    
    @staticmethod
    def mdlEliminarLecturasBloqueAcelerografo(tabla, iddetalles, idproyecto, username, nombres):
        placeholders = ', '.join(['?' for _ in iddetalles])
        sql = f"""DELETE FROM {tabla} WHERE id_detalle IN ({placeholders});"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # guardar en historial
            query_select = f'''SELECT * FROM {tabla} WHERE id_detalle IN ({placeholders});'''
            cur.execute(query_select, iddetalles)
            rows = cur.fetchall()
            datos_anteriores = [tuple(row) for row in rows] if rows else None
            
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
    
    @staticmethod
    def mdlComprobarExisteNombreAcelerografo(proyecto, nombre):
        sql = """SELECT * FROM acelerografos WHERE id_proyecto = ? AND nombre_acelerografo = ?;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyecto, nombre))
            row = cur.fetchone()
            if row:
                return True, tuple(row)
            else:
                return False, None
        except Exception as e:
            print("Error al comprobar Acelerografo: " + str(e))
            return False, None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlRegistrarAcelerografo(proyecto_id, datos):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # Verificar si el equipo ya existe
            sql_check = """SELECT 1 FROM instrumentacion WHERE id_componente = ? AND nombre_equipo = ? AND tipo_equipo = 'ACELEROGRAFO';"""
            cur.execute(sql_check, (datos[4], datos[0]))
            if cur.fetchone():
                print("El equipo ya existe en la tabla instrumentacion.")
                return "NO", None
            
            # Insertar el nuevo acelerógrafo
            sql_insert = """INSERT INTO acelerografos (id_proyecto, nombre_acelerografo, este_acelerografo, norte_acelerografo,
            elevacion_acelerografo, estado_acelerografo) OUTPUT INSERTED.id_acelerografo VALUES (?, ?, ?, ?, ?, ?);"""
            cur.execute(sql_insert, (proyecto_id, datos[0], datos[1], datos[2], datos[3], datos[5]))
            acelerografo_id = cur.fetchone()[0]
            # Insertar en la tabla instrumentacion
            sql_insert_instrumentacion = """INSERT INTO instrumentacion (id_componente, tipo_equipo, nombre_equipo, id_equipo,
            tabla_equipo, estado_instrumentacion) VALUES (?, ?, ?, ?, ?, ?);"""
            cur.execute(sql_insert_instrumentacion, (datos[4], 'ACELEROGRAFO', datos[0], acelerografo_id, 'acelerografos', datos[5]))
            # Confirmar la transacción
            conn.commit()
            return "SI", acelerografo_id
        except Exception as e:
            print("Error al guardar Acelerografo:", e)
            if conn:
                conn.rollback()
            return "ERROR", None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlRegistrarFormatoAcelerografo(proyecto_id, datos):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            
            # Insertar el nuevo acelerógrafo
            sql_insert = """INSERT INTO acelerografos (id_proyecto, nombre_acelerografo, este_acelerografo, norte_acelerografo,
            elevacion_acelerografo) OUTPUT INSERTED.id_acelerografo VALUES (?, ?, ?, ?, ?);"""
            cur.execute(sql_insert, (proyecto_id, datos[0], datos[1], datos[2], datos[3]))
            acelerografo_id = cur.fetchone()[0]
            # Insertar en la tabla instrumentacion
            sql_insert_instrumentacion = """INSERT INTO instrumentacion (id_componente, tipo_equipo, nombre_equipo, id_equipo,
            tabla_equipo) VALUES (?, ?, ?, ?, ?);"""
            cur.execute(sql_insert_instrumentacion, (datos[4], 'ACELEROGRAFO', datos[0], acelerografo_id, 'acelerografos'))
            
            conn.commit()
            return acelerografo_id
        except Exception as e:
            print("Error al guardar Acelerografo formato:", e)
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerAcelerografos(proyectoID):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = """SELECT * FROM acelerografos WHERE id_proyecto = ?;"""
            cur = conn.cursor()
            cur.execute(sql, (proyectoID,))
            rows = cur.fetchall()
            return [tuple(row) for row in rows] if rows else None
        except Exception as e:
            print("Error al obtener acelerografos:", e)
            return None  
        finally:
            if conn:
                conn.close()
                
    @staticmethod
    def mdlRegistrarDataAcelerografo(proyectoID, datos):
        tabla = f'acelerografo_detalle{proyectoID}'
        # T-SQL: Sintaxis CREATE TABLE. 
        # NOTA: Usamos FLOAT en lugar de NUMERIC para asegurar compatibilidad con cálculos numéricos de Python sin Decimal.
        # NOTA: IDENTITY(1,1) reemplaza AUTOINCREMENT.
        crear_tabla_sql = f"""
        IF OBJECT_ID('dbo.{tabla}', 'U') IS NULL
        BEGIN
            CREATE TABLE {tabla} (
                id_detalle INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
                id_acelerografo INT NOT NULL,
                fecha_detalle DATETIME2(0) NOT NULL,
                magnitud_detalle FLOAT NOT NULL,
                distancia_detalle FLOAT NOT NULL,
                observacion_detalle VARCHAR(MAX),
                estado_detalle INT NOT NULL DEFAULT 1
            );
        END
        """
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # PRAGMAS de SQLite eliminados porque no existen en SQL Server
            cursor.execute(crear_tabla_sql)
            
            # Lógica de negocio
            idacelero = datos[0][0]
            
            # Optimización: Consultar solo las fechas necesarias o usar un índice en SQL Server
            sql_check = f"SELECT fecha_detalle FROM {tabla} WHERE id_acelerografo = ?;"
            cursor.execute(sql_check, (idacelero,))
            # Convertimos a set para búsqueda rápida, asegurando que row[0] sea string
            existen_acelero = set([str(row[0]) for row in cursor.fetchall()])
            
            lote_registros = []
            contador = 0
            
            for fila in datos:
                # fila: [id_acelerografo, fecha, hora, magnitud, distancia]
                if len(fila) < 5 or not fila[3] or not fila[4]:
                    continue
                
                fecha_original = str(fila[1])
                hora_original = str(fila[2])
                fecha_hora_nueva = fecha_original + " " + hora_original
                
                if fecha_hora_nueva not in existen_acelero:
                    # En T-SQL no insertamos el ID autoincremental
                    datito = (fila[0], fecha_hora_nueva, fila[3], fila[4])
                    lote_registros.append(datito)
                    contador += 1
                
                if contador % 1000 == 0 and lote_registros:
                    # SQL Server soporta inserts múltiples, pyodbc executemany es eficiente
                    sql_batch = f"""INSERT INTO {tabla} (id_acelerografo, fecha_detalle, magnitud_detalle, distancia_detalle)
                                       VALUES (?, ?, ?, ?);"""
                    cursor.executemany(sql_batch, lote_registros)
                    lote_registros = []
            
            if lote_registros:
                sql_batch = f"""INSERT INTO {tabla} (id_acelerografo, fecha_detalle, magnitud_detalle, distancia_detalle)
                                   VALUES (?, ?, ?, ?);"""
                cursor.executemany(sql_batch, lote_registros)
            
            conn.commit()
            return True
        except Exception as e:
            print("Error al guardar data acelerografos: " + str(e))
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCambiarComponenteAcelerografos(idcomponente, nuevocomponente):
        sql = """UPDATE instrumentacion SET id_componente = ? WHERE id_componente = ? AND tipo_equipo = 'ACELEROGRAFO';"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # guardar info
            query_select = """SELECT * FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'ACELEROGRAFO';"""
            cur.execute(query_select, (idcomponente,))
            rows = cur.fetchall()
            datasismos = [tuple(row) for row in rows] if rows else None
            
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
    
    @staticmethod
    def mdlEliminarAcelerografos(idcomponente):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # obtener info
            query_select = """SELECT * FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'ACELEROGRAFO';"""
            cursor.execute(query_select, (idcomponente,))
            rows = cursor.fetchall()
            datasismos = [tuple(row) for row in rows] if rows else None
            
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
    
    @staticmethod
    def mdlEliminarDataAcelerografos(tabla, sismos):
        placeholders = ','.join(['?' for _ in sismos])
        respuesta = False
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # eliminar acelerografos
            stmt_delete = f"DELETE FROM acelerografos WHERE id_acelerografo IN ({placeholders});"
            cursor.execute(stmt_delete, sismos)
            
            # eliminar data detalle
            query_delete = f"""DELETE FROM {tabla} WHERE id_acelerografo IN ({placeholders});"""
            cursor.execute(query_delete, sismos)
            
            conn.commit()
            respuesta = True
            return respuesta
        except Exception as e:
            print(f"Error al eliminar data acelerografos: {e}")
            if conn:
                conn.rollback()
            return respuesta
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerInfoAcelerografo(idinstrumento):
        sql = """SELECT a.* FROM acelerografos a INNER JOIN instrumentacion i ON a.id_acelerografo = i.id_equipo WHERE i.id_instrumentacion = ?;"""
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
            print("Error al consultar info acelerografo: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlActualizarAcelerografo(datos, data):
        query = """UPDATE acelerografos SET nombre_acelerografo = ?, este_acelerografo = ?, norte_acelerografo = ?,
        elevacion_acelerografo = ?, estado_acelerografo = ? WHERE id_acelerografo  = ?;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            cursor.execute(query, datos)
            query_instrumentacion = """UPDATE instrumentacion SET id_componente = ?, nombre_equipo = ?, estado_instrumentacion = ?
            WHERE id_instrumentacion = ? AND tipo_equipo = 'ACELEROGRAFO';"""
            cursor.execute(query_instrumentacion, data)
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al actualizar acelerografo: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlEliminarAcelerografo(idinstrumento):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # obtener info para eliminar data
            query_select = """SELECT * FROM instrumentacion WHERE id_instrumentacion = ? AND tipo_equipo = 'ACELEROGRAFO';"""
            cursor.execute(query_select, (idinstrumento,))
            row = cursor.fetchone()
            dataacelero = tuple(row) if row else None
            
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
    
    @staticmethod
    def mdlEliminarAcelerografoData(tabla, idacelero):
        respuesta = False
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            stmt_delete = "DELETE FROM acelerografos WHERE id_acelerografo = ?;"
            cursor.execute(stmt_delete, (idacelero,))
            
            # eliminar data
            query_delete = f"""DELETE FROM {tabla} WHERE id_acelerografo = ?;"""
            cursor.execute(query_delete, (idacelero,))
            
            conn.commit()
            respuesta = True
            return respuesta
        except Exception as e:
            print(f"Error al eliminar data acelerografo: {e}")
            if conn:
                conn.rollback()
            return respuesta
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerUmbralesAcelerografoComponente(idproyecto, idcomponente, tipo):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = """SELECT * FROM umbral_acelerografo WHERE id_proyecto = ? AND id_componente = ? AND tipo_umbral = ?;"""
            cur = conn.cursor()
            cur.execute(sql, (idproyecto, idcomponente, tipo))
            rows = cur.fetchall()
            return [tuple(row) for row in rows] if rows else None
        except Exception as e:
            print("Error al obtener umbrales acelerografo:", e)
            return None  
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlTraerDataAcelerografo(idacelero):
        sql = """SELECT i.id_instrumentacion, i.id_componente, c.nombre_componente FROM instrumentacion i
        INNER JOIN componentes c ON i.id_componente = c.id_componente
        WHERE i.id_equipo = ? AND i.tipo_equipo = 'ACELEROGRAFO';"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idacelero,))
            row = cur.fetchone()
            if row:
                return tuple(row)
            else:
                return None
        except Exception as e:
            print("Error al traer data acelerografo: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCambiarAcelerografoComponente(idinstrumento, nuevocomponente):
        sql = """UPDATE instrumentacion SET id_componente = ? WHERE id_instrumentacion = ?;"""
        conn = None
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