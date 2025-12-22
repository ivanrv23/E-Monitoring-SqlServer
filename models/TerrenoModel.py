from services.security.apis.conexiones.connection import Connection
from datetime import datetime

class TerrenoModel:
    
    # GUARDAR NUEVA COTA DE TERRENO
    @staticmethod
    def mdlGuardarNuevaCotaTerreno(proyecto_id, componente, nombre, comentario):
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # Verificar si existe un equipo con el mismo nombre en el mismo componente
            # SQL Server permite SELECT 1
            cur.execute("SELECT 1 FROM instrumentacion WHERE id_componente = ? AND nombre_equipo = ? AND tipo_equipo = 'COTATERRENO';", (componente, nombre))
            if cur.fetchone():
                return "NO"
            
            # Registrar la nueva cota de terreno
            cur.execute("""INSERT INTO cotasterreno (id_proyecto, nombre_terreno, comentario_terreno) VALUES (?, ?, ?);""",
                        (proyecto_id, nombre, comentario))
            
            # Obtener el ID insertado (Reemplazo de lastrowid)
            cur.execute("SELECT SCOPE_IDENTITY();")
            row_id = cur.fetchone()
            if row_id and row_id[0] is not None:
                id_equipo = int(row_id[0])
            else:
                conn.rollback()
                return "ERROR"

            # Registrar la cota en la tabla instrumentacion
            cur.execute("""INSERT INTO instrumentacion (id_componente, tipo_equipo, nombre_equipo, id_equipo, tabla_equipo) VALUES (?, ?, ?, ?, ?);""",
                        (componente, 'COTATERRENO', nombre, id_equipo, 'cotasterreno'))
            conn.commit()
            return "OK"
        except Exception as e:
            print("Error al guardar cota terreno: " + str(e))
            conn.rollback()
            return "ERROR"
        finally:
            if conn:
                conn.close()
    
    # LISTAR LAS COTAS POR PROYECTO
    @staticmethod
    def mdlListaCotasTerrenoProyecto(proyecto):
        conn = Connection.connectionDB()
        sql = """SELECT * FROM cotasterreno WHERE id_proyecto = ? AND estado_terreno = 1;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (proyecto,))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al listar cotas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # REGISTRAR DATA COTA TERRENO DESDE TABLA
    @staticmethod
    def mdlGuardarDataCotaTerreno(proyectoid, data):
        table_name = f"cotaterreno_detalle{proyectoid}"
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            
            # Crear la tabla si no existe (Sintaxis T-SQL)
            # Se usa DECIMAL(18,5) para asegurar precisión y NVARCHAR para fechas/textos
            create_table_sql = f"""
            IF OBJECT_ID('{table_name}', 'U') IS NULL
            BEGIN
                CREATE TABLE {table_name} (
                    id_detalle INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
                    id_terreno INT NOT NULL,
                    fecha_detalle NVARCHAR(50) NOT NULL,
                    nivel_detalle DECIMAL(18,5) NOT NULL,
                    observacion_detalle NVARCHAR(MAX),
                    estado_detalle INT DEFAULT 1
                )
            END;"""
            
            cursor.execute(create_table_sql)
            
            # Eliminados PRAGMA de SQLite
            
            # Verificar existentes
            id_terreno = data[0][0]
            # Nota: SQL Server maneja fechas en NVARCHAR implícitamente, pero es mejor asegurar el formato
            existen_cotas = set([row[0] for row in cursor.execute(f"SELECT fecha_detalle FROM {table_name} WHERE id_terreno = ?;", (id_terreno,))])
            
            lote_registros = []
            contador = 0
            for fila in data:
                if len(fila) < 5 or not fila[3]:
                    continue
                fecha_original = fila[1]
                hora_original = fila[2]
                fecha_hora_nueva = fecha_original + " " + hora_original
                
                # Verifica si el registro no existe en el conjunto
                if fecha_hora_nueva not in existen_cotas:
                    datito = [fila[0], fecha_hora_nueva, fila[3], fila[4]]
                    lote_registros.append(datito)
                    contador += 1
                
                # Insertar en lotes
                if contador % 1000 == 0 and lote_registros:
                    cursor.executemany(f"""INSERT INTO {table_name} (id_terreno, fecha_detalle, nivel_detalle, observacion_detalle) VALUES (?, ?, ?, ?)""", lote_registros)
                    lote_registros = []
            
            # Insertar remanentes
            if lote_registros:
                cursor.executemany(f"""INSERT INTO {table_name} (id_terreno, fecha_detalle, nivel_detalle, observacion_detalle) VALUES (?, ?, ?, ?)""", lote_registros)

            conn.commit()
            return True
        except Exception as e:
            print("Error al guardar data terreno: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlComprobarExisteNombreCotaTerreno(proyecto, nombre):
        sql = """SELECT * FROM cotasterreno WHERE id_proyecto = ? AND nombre_terreno = ?;"""
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
            print("Error al comprobar nombre terreno: " + str(e))
            return False, None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlRegistrarFormatoCotaTerreno(proyecto_id, componente, nombre, comentario):
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # Registrar la nueva cota de terreno
            cur.execute("""INSERT INTO cotasterreno (id_proyecto, nombre_terreno, comentario_terreno) VALUES (?, ?, ?);""",
                        (proyecto_id, nombre, comentario))
            
            # Obtener el ID insertado
            cur.execute("SELECT SCOPE_IDENTITY();")
            row_id = cur.fetchone()
            if row_id and row_id[0] is not None:
                id_equipo = int(row_id[0])
            else:
                conn.rollback()
                return None

            # Registrar la cota en la tabla instrumentacion
            cur.execute("""INSERT INTO instrumentacion (id_componente, tipo_equipo, nombre_equipo, id_equipo, tabla_equipo) VALUES (?, ?, ?, ?, ?);""",
                        (componente, 'COTATERRENO', nombre, id_equipo, 'cotasterreno'))
            conn.commit()
            return id_equipo
        except Exception as e:
            print("Error al guardar cota terreno: " + str(e))
            conn.rollback()
            return None
        finally:
            if conn:
                conn.close()

    # LISTAR DATA COTAS TERRENO DETALLE POR ID
    @staticmethod
    def mdlObtenerDataCotasTerrenoDetalle(idsuelo):
        conn = Connection.connectionDB()
        sql = """SELECT s.nombre_terreno, d.fecha_detalle, d.nivel_detalle, d.id_detalle FROM cotaterreno_detalle d INNER JOIN cotasterreno s
        ON d.id_terreno = s.id_terreno WHERE d.id_terreno = ? ORDER BY d.fecha_detalle;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (idsuelo,))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al consultar terreno detalle: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # LISTAR DATA TERRENO DETALLE POR ID
    @staticmethod
    def mdlObtenerDataTerrenoDetalle(sueloid):
        conn = Connection.connectionDB()
        sql = """SELECT d.*, t.nombre_terreno FROM cotaterreno_detalle d INNER JOIN cotasterreno t ON d.id_terreno = t.id_terreno
            WHERE d.id_terreno = ? ORDER BY d.fecha_detalle ASC;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (sueloid,))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al consultar suelo detalle: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # Info de suelo fundacion por id
    @staticmethod
    def mdlTraerInfoCotaTerreno(idsuelo):
        sql = """SELECT * FROM cotasterreno WHERE id_terreno = ?;"""
        conn = Connection.connectionDB()
        try:
            cur = conn.cursor()
            cur.execute(sql, (idsuelo,))
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al consultar cota terreno: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # ACTUALIZAR COTA DE TERRENO
    @staticmethod
    def mdlActualizarCotaTerreno(idcota, nombre, comentario):
        conn = Connection.connectionDB()
        sql = """UPDATE cotasterreno SET nombre_terreno = ?, comentario_terreno = ? WHERE id_terreno = ?;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (nombre, comentario, idcota))
            conn.commit()
            return True
        except Exception as e:
            print("Error al editar cota Terreno: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    # Eliminar el detalle del terreno
    @staticmethod
    def mdlEliminarDetalleTerreno(idsuelo):
        conn = Connection.connectionDB()
        sql = """DELETE FROM cotaterreno_detalle WHERE id_terreno = ?;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (idsuelo,))
            conn.commit()
            return True
        except Exception as e:
            print("Error al eliminar detalles terreno: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    # COMPROBAR EXISTE REGISTRO DE COTA TERRENO
    @staticmethod
    def mdlComprobarExisteCotaTerreno(idpiezo, tipo, fecha, hora):
        fecha_nueva = datetime.strptime(fecha, '%d/%m/%Y').strftime('%Y-%m-%d')
        fecha_hora = fecha_nueva + " " + hora
        conn = Connection.connectionDB()
        sql = """SELECT * FROM cotasterreno WHERE id_piezometro = ? AND tipo_piezometro = ? AND fecha_cota = ?;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (idpiezo, tipo, fecha_hora))
            row = cur.fetchone()
            if row:
                return True
            else:
                return False
        except Exception as e:
            print("Error al comprobar cota: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
                            
    # REGISTRAR MEDIDA DE COTA TERRENO
    @staticmethod
    def mdlGuardarDataCota(idcota, tipo, fecha, hora, nivel):
        fecha_nueva = datetime.strptime(fecha, '%d/%m/%Y').strftime('%Y-%m-%d')
        fecha_hora_nueva = fecha_nueva + " " + hora
        conn = Connection.connectionDB()
        sql = """INSERT INTO cotasterreno (id_piezometro, tipo_piezometro, fecha_cota, nivel_cota) VALUES (?, ?, ?, ?)"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (idcota, tipo, fecha_hora_nueva, nivel))
            conn.commit()
            return True
        except Exception as e:
            print("Error al guardar cota: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    # REGISTRAR COTAS DE PIEZOMETROS DESDE LA TABLA
    @staticmethod
    def mdlGuardarLecturasCotaPiezometrica(data):
        conn = Connection.connectionDB()
        cursor = conn.cursor()
        try:
            # Eliminados PRAGMA
            
            # Crear un conjunto de tuplas con los valores de fecha y hora para comparar los registros existentes
            idpiezo = data[0][0]
            tipo = data[0][1]
            existen_piezometros = set([row[0] for row in cursor.execute("SELECT fecha_cota FROM cotas_piezometricas WHERE id_piezometro = ? AND tipo_piezometro = ?", (idpiezo, tipo))])
            lote_registros = []
            contador = 0
            for fila in data:
                if len(fila) < 4 or not fila[3]:
                    continue
                fecha_original = fila[2]
                fecha_hora_nueva = fecha_original + " 00:00:00"
                # Verifica si el registro no existe en el conjunto
                if fecha_hora_nueva not in existen_piezometros:
                    datito = [fila[0], fila[1], fecha_hora_nueva, fila[3]]
                    lote_registros.append(datito)
                    contador += 1
                    
                if contador % 1000 == 0 and lote_registros:
                    cursor.executemany("""INSERT INTO cotas_piezometricas (id_piezometro, tipo_piezometro, fecha_cota, nivel_cota) VALUES (?, ?, ?, ?)""", lote_registros)
                    lote_registros = []

            if lote_registros:
                cursor.executemany("""INSERT INTO cotas_piezometricas (id_piezometro, tipo_piezometro, fecha_cota, nivel_cota) VALUES (?, ?, ?, ?)""", lote_registros)
                    
            conn.commit()
            return True
        except Exception as e:
            print("Error al guardar las cotas piezometricas: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    # Obtener data de cotas piezometricas por proyecto id
    @staticmethod
    def mdlObtenerDataCotasPiezometricas(proyecto):
        conn = Connection.connectionDB()
        sql = """SELECT
            CASE 
                WHEN c.tipo_piezometro = 'PCV' THEN pc.nombre_piezometro
                WHEN c.tipo_piezometro = 'PVC' THEN pm.nombre_piezometro
            END AS nombre_piezometro,
            CASE 
                WHEN c.tipo_piezometro = 'PCV' THEN 'Automatizado'
                WHEN c.tipo_piezometro = 'PVC' THEN 'Manual'
            END AS tipo_piezometro, c.fecha_cota, c.nivel_cota, c.id_cota, c.id_piezometro, c.tipo_piezometro
        FROM 
            cotas_piezometricas c
        LEFT JOIN 
            piezometrocuerdas pc ON c.id_piezometro = pc.id_piezometro AND c.tipo_piezometro = 'PCV'
        LEFT JOIN 
            piezometros pm ON c.id_piezometro = pm.id_piezometro AND c.tipo_piezometro = 'PVC'
        WHERE (pc.id_proyecto = ? OR pm.id_proyecto = ?) ORDER BY c.fecha_cota;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (proyecto, proyecto))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al consultar piezometricas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # LISTAR DATA COTAS DETALLE POR ID Y TIPO
    @staticmethod
    def mdlObtenerDataCotaDetalle(idpiezo, tipopiezo):
        conn = Connection.connectionDB()
        sql = """SELECT * FROM cotas_piezometricas WHERE id_piezometro = ? AND tipo_piezometro = ? ORDER BY fecha_cota ASC;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (idpiezo, tipopiezo))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al consultar cota detalle: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlActualizarLecturaCotapiezometrica(idcota, fecha, nivel):
        conn = Connection.connectionDB()
        sql = """UPDATE cotas_piezometricas SET fecha_cota = ?, nivel_cota = ? WHERE id_cota = ?;"""
        try:
            cur = conn.cursor()
            # guardar en historial
            query_select = '''SELECT fecha_cota, nivel_cota, id_cota FROM cotas_piezometricas WHERE id_cota = ?;'''
            cur.execute(query_select, (idcota,))
            datos_anteriores = cur.fetchone()
            if datos_anteriores:
                fecha_cambio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                accion = "update"
                tabla = "cotas_piezometricas"
                # Formato de string para SQL Server
                cambios = f"Antiguos: {datos_anteriores}, Nuevos: [{fecha}, {nivel}, {idcota}]"
                query_historial = """INSERT INTO historial (idproyecto, fecha, accion, tabla, cambios, usuario, nombres)
                VALUES (?, ?, ?, ?, ?, ?, ?);"""
                # Para el historial, como no tenemos idproyecto, asumimos que la tabla permite NULL o la lógica no lo requiere aquí estricto
                # NOTA: En la función original no pasaban idproyecto, así que lo mandaré como None o vacío.
                # Sin embargo, el INSERT espera 7 valores. En el código original mandaban (fecha_cambio, accion, tabla, cambios) -> 4 valores para 7 placeholders?
                # Revisando tu código original: `cur.execute(query_historial, (fecha_cambio, accion, tabla, cambios))` 
                # ESTO ES UN BUG EN EL ORIGINAL (4 params para 7 ?). 
                # Ajustaré para intentar evitar el crash, pero si la tabla historial requiere los otros campos, fallará.
                # Asumiré que el original funcionaba porque tal vez la tabla historial tiene defaults o el trigger lo maneja.
                # Pero pyodbc validará el número de parámetros.
                # CORRECCIÓN: Mantendré la lógica original a pesar del bug potencial, pero llenando con None los faltantes para que pyodbc no falle por count.
                cur.execute(query_historial, (None, fecha_cambio, accion, tabla, cambios, None, None))
            
            # actualizar cota piezometro
            cur.execute(sql, (fecha, nivel, idcota))
            conn.commit()
            return True
        except Exception as e:
            print("Error al editar lectura cota: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlComprobarUltimaCotapiezometrica(idpiezo, tipopiezo):
        sql = """SELECT COUNT(*) FROM cotas_piezometricas WHERE id_piezometro = ? AND tipo_piezometro = ?;"""
        conn = Connection.connectionDB()
        try:
            cur = conn.cursor()
            cur.execute(sql, (idpiezo, tipopiezo))
            row = cur.fetchone()
            if row:
                if row[0] > 1:
                    return True
                else:
                    return False
            else:
                return False
        except Exception as e:
            print("Error al comprobar cantidad cotas: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlEliminarLecturaCotapiezometrica(idcota):
        conn = Connection.connectionDB()
        sql = """DELETE FROM cotas_piezometricas WHERE id_cota = ?;"""
        try:
            cur = conn.cursor()
            # guardar en historial
            query_select = f'''SELECT * FROM cotas_piezometricas WHERE id_cota = ?;'''
            cur.execute(query_select, (idcota,))
            datos_anteriores = cur.fetchone()
            if datos_anteriores:
                fecha_cambio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                accion = "delete"
                tabla = "cotas_piezometricas"
                cambios = f"Datos: {datos_anteriores}"
                query_historial = """INSERT INTO historial (idproyecto, fecha, accion, tabla, cambios, usuario, nombres)
                VALUES (?, ?, ?, ?, ?, ?, ?);"""
                # Corrección de parámetros para pyodbc (7 placeholders)
                cur.execute(query_historial, (None, fecha_cambio, accion, tabla, cambios, None, None))
            # eliminar lectura celda
            cur.execute(sql, (idcota,))
            conn.commit()
            return True
        except Exception as e:
            print("Error al eliminar lectura cota: " + str(e))
            return False
        finally:
            if conn:
                conn.close()            
            
    @staticmethod
    def mdlActualizarLecturaCotaterreno(tabla, datos, idproyecto, username, nombres):
        sql = f"""UPDATE {tabla} SET fecha_detalle = ?, nivel_detalle = ?, observacion_detalle = ? WHERE id_detalle = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # guardar en historial
            query_select = f"""SELECT fecha_detalle, nivel_detalle, observacion_detalle, id_detalle FROM {tabla} WHERE id_detalle = ?;"""
            cur.execute(query_select, (datos[-1],))
            datos_anteriores = cur.fetchone()
            if datos_anteriores:
                fecha_cambio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                accion = "update"
                cambios = f"Antiguos: {datos_anteriores}, Nuevos: {datos}"
                query_historial = """INSERT INTO historial (idproyecto, fecha, accion, tabla, cambios, usuario, nombres)
                VALUES (?, ?, ?, ?, ?, ?, ?);"""
                cur.execute(query_historial, (idproyecto, fecha_cambio, accion, tabla, cambios, username, nombres))
            # actualizar cotaterreno
            cur.execute(sql, datos)
            conn.commit()
            return True
        except Exception as e:
            print("Error al editar lectura Terreno: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlEliminarLecturaCotaterreno(tabla, iddetalle, idproyecto, username, nombres):
        sql = f"""DELETE FROM {tabla} WHERE id_detalle = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # guardar en historial
            query_select = f"""SELECT * FROM {tabla} WHERE id_detalle = ?;"""
            cur.execute(query_select, (iddetalle,))
            datos_anteriores = cur.fetchone()
            if datos_anteriores:
                fecha_cambio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                accion = "delete"
                cambios = f"Datos: {datos_anteriores}"
                query_historial = """INSERT INTO historial (idproyecto, fecha, accion, tabla, cambios, usuario, nombres)
                VALUES (?, ?, ?, ?, ?, ?, ?);"""
                cur.execute(query_historial, (idproyecto, fecha_cambio, accion, tabla, cambios, username, nombres))
            # eliminar lectura terreno
            cur.execute(sql, (iddetalle,))
            rows_affected = cur.rowcount
            conn.commit()
            if rows_affected > 0:
                return True
            else:
                return False
        except Exception as e:
            print("Error al eliminar lectura terreno: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlEliminarLecturasBloqueCotaterreno(tabla, iddetalles, idproyecto, username, nombres):
        placeholders = ', '.join(['?' for _ in iddetalles])
        sql = f"""DELETE FROM {tabla} WHERE id_detalle IN ({placeholders});"""
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
            # eliminar lecturas terreno
            cur.execute(sql, iddetalles)
            rows_affected = cur.rowcount
            conn.commit()
            if rows_affected > 0:
                return True
            else:
                return False
        except Exception as e:
            print("Error al eliminar lecturas terrenos: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCambiarComponenteCotasTerreno(idcomponente, nuevocomponente):
        sql = """UPDATE instrumentacion SET id_componente = ? WHERE id_componente = ? AND tipo_equipo = 'COTATERRENO';"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # guardar info
            query_select = """SELECT * FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'COTATERRENO';"""
            cur.execute(query_select, (idcomponente,))
            datacotas = cur.fetchall()
            if datacotas:
                cur.execute(sql, (nuevocomponente, idcomponente))
                conn.commit()
                return datacotas
            else:
                return None
        except Exception as e:
            print("Error al cambiar componente terrenos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlEliminarCotasTerrenos(idcomponente):
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # obtener info
            query_select = """SELECT * FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'COTATERRENO';"""
            cursor.execute(query_select, (idcomponente,))
            datacota = cursor.fetchall()
            if datacota:
                query = """DELETE FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'COTATERRENO';"""
                cursor.execute(query, (idcomponente,))
                rows_affected = cursor.rowcount
                conn.commit()
                if rows_affected > 0:
                    return datacota
                else:
                    return None
            else:
                return None
        except Exception as e:
            print(f"Error al eliminar terrenos: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlEliminarDataCotasTerrenos(tabla, terrenos):
        placeholders = ','.join(['?' for _ in terrenos])
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # eliminar data
            query_delete = f"""DELETE FROM {tabla} WHERE id_terreno IN ({placeholders});"""
            cursor.execute(query_delete, terrenos)
            rows_data = cursor.rowcount
            if rows_data > 0:
                stmt_delete = f"DELETE FROM cotasterreno WHERE id_terreno IN ({placeholders});"
                cursor.execute(stmt_delete, terrenos)
                rows_delete = cursor.rowcount
                conn.commit()
                return rows_delete > 0
            else:
                conn.rollback()
                return False
        except Exception as e:
            print(f"Error al eliminar data terrenos: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerInfoPluviometro(idinstrumento):
        sql = """SELECT c.* FROM cotasterreno c INNER JOIN instrumentacion i ON c.id_terreno = i.id_equipo WHERE i.id_instrumentacion = ?;"""
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
            print("Error al consultar info cota terreno: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # Eliminar cota terreno
    @staticmethod
    def mdlEliminarCotaTerreno(idinstrumento):
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # obtener info para eliminar data
            query_select = """SELECT * FROM instrumentacion WHERE id_instrumentacion = ? AND tipo_equipo = 'COTATERRENO';"""
            cursor.execute(query_select, (idinstrumento,))
            dataterreno = cursor.fetchone()
            if dataterreno:
                query = """DELETE FROM instrumentacion WHERE id_instrumentacion = ? AND tipo_equipo = 'COTATERRENO';"""
                cursor.execute(query, (idinstrumento,))
                rows_affected = cursor.rowcount
                conn.commit()
                if rows_affected > 0:
                    return dataterreno
                else:
                    return None
            else:
                return None
        except Exception as e:
            print(f"Error al eliminar terreno: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlEliminarCotaTerrenoData(tabla, idterreno):
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # eliminar data
            query_delete = f"""DELETE FROM {tabla} WHERE id_terreno = ?;"""
            cursor.execute(query_delete, (idterreno,))
            rows_data = cursor.rowcount
            if rows_data > 0:
                stmt_delete = "DELETE FROM cotasterreno WHERE id_terreno = ?;"
                cursor.execute(stmt_delete, (idterreno,))
                rows_delete = cursor.rowcount
                conn.commit()
                return rows_delete > 0
            else:
                conn.rollback()
                return False
        except Exception as e:
            print(f"Error al eliminar data terreno: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerCotasTerreno(tabla, idcomponente, idinstrumento, fechaini, fechafin):
        try:
            conn = Connection.connectionDB()
            # MIGRACIÓN CRÍTICA:
            # JULIANDAY(fecha) - JULIANDAY(inicio) -> DATEDIFF(SECOND, inicio, fecha) / 86400.0
            # Se usa CAST a DECIMAL(18,5) para mantener la precisión decimal.
            # Se asume que fecha_detalle es convertible a DATETIME (SQL Server lo intentará implícitamente si es string 'yyyy-MM-dd HH:mm:ss').
            
            sql = f"""SELECT t.id_instrumentacion, p.nombre_terreno, d.fecha_detalle,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(CAST(d.fecha_detalle AS DATETIME)) OVER (PARTITION BY p.id_terreno ORDER BY d.fecha_detalle), CAST(d.fecha_detalle AS DATETIME)) / 86400.0 AS DECIMAL(18,5)) AS dias,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(CAST(d.fecha_detalle AS DATETIME)) OVER (PARTITION BY p.id_terreno ORDER BY d.fecha_detalle), CAST(d.fecha_detalle AS DATETIME)) / 86400.0 * 24.0 AS DECIMAL(18,5)) AS horas,
                d.nivel_detalle
            FROM {tabla} d INNER JOIN cotasterreno p ON d.id_terreno = p.id_terreno
            INNER JOIN instrumentacion t ON p.id_terreno = t.id_equipo
            INNER JOIN componentes c ON t.id_componente = c.id_componente
            WHERE c.id_componente = ? AND t.id_instrumentacion = ? AND d.fecha_detalle BETWEEN ? AND ?
            ORDER BY d.fecha_detalle;"""
            
            cur = conn.cursor()
            cur.execute(sql, (idcomponente, idinstrumento, fechaini, fechafin))
            results = cur.fetchall()
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al obtener data terreno:", e)
            return None  
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlTraerDataCotaTerreno(idterreno):
        sql = """SELECT i.id_instrumentacion, i.id_componente, c.nombre_componente FROM instrumentacion i
        INNER JOIN componentes c ON i.id_componente = c.id_componente
        WHERE i.id_equipo = ? AND i.tipo_equipo = 'COTATERRENO';"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idterreno,))
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al traer data terreno: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCambiarCotaterrenoComponente(idinstrumento, nuevocomponente):
        sql = """UPDATE instrumentacion SET id_componente = ? WHERE id_instrumentacion = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (nuevocomponente, idinstrumento))
            conn.commit()
            return True
        except Exception as e:
            print("Error al cambiar componente cota terreno: " + str(e))
            return False
        finally:
            if conn:
                conn.close()