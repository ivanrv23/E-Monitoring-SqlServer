from services.security.apis.conexiones.connection import Connection
from datetime import datetime


class TerrenoModel:
    
    # GUARDAR NUEVA COTA DE TERRENO      
    def mdlGuardarNuevaCotaTerreno(proyecto_id, componente, nombre, comentario):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # Verificar si existe un equipo con el mismo nombre en el mismo componente
            cur.execute("SELECT 1 FROM instrumentacion WHERE id_componente = ? AND nombre_equipo = ? AND tipo_equipo = 'COTATERRENO';", (componente, nombre))
            if cur.fetchone():
                return "NO"
            # Registrar la nueva cota de terreno con OUTPUT para obtener el ID
            cur.execute("""INSERT INTO cotasterreno (id_proyecto, nombre_terreno, comentario_terreno) OUTPUT INSERTED.id_terreno VALUES (?, ?, ?);""",
                        (proyecto_id, nombre, comentario))
            id_equipo = cur.fetchone()[0]
            # Registrar la cota en la tabla instrumentacion
            cur.execute("""INSERT INTO instrumentacion (id_componente, tipo_equipo, nombre_equipo, id_equipo, tabla_equipo) VALUES (?, ?, ?, ?, ?);""",
                        (componente, 'COTATERRENO', nombre, id_equipo, 'cotasterreno'))
            conn.commit()
            return "OK"
        except Exception as e:
            print("Error al guardar cota terreno: " + str(e))
            if conn:
                conn.rollback()
            return "ERROR"
        finally:
            if conn:
                conn.close()
    
    # LISTAR LAS COTAS POR PROYECTO    
    def mdlListaCotasTerrenoProyecto(proyecto):
        conn = None
        sql = """SELECT * FROM cotasterreno WHERE id_proyecto = ? AND estado_terreno = 1;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyecto,))
            results = [tuple(row) for row in cur.fetchall()]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al listar cotas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # REGISTRAR DATA COTA TERRENO DESDE TABLA
    def mdlGuardarDataCotaTerreno(proyectoid, data):
        conn = None
        table_name = f"cotaterreno_detalle{proyectoid}"
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # Crear la tabla si no existe (SQL Server)
            cursor.execute(f"""
                IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = '{table_name}')
                BEGIN
                    CREATE TABLE {table_name} (
                        id_detalle INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
                        id_terreno INT NOT NULL,
                        fecha_detalle DATETIME2(0) NOT NULL,
                        nivel_detalle DECIMAL(18,6) NOT NULL,
                        observacion_detalle VARCHAR(500),
                        estado_detalle INT DEFAULT 1
                    )
                END
            """)
            conn.commit()
            # Crear un conjunto de tuplas con los valores de fecha y hora para comparar los registros existentes
            idcota = data[0][0]
            cursor.execute(f"SELECT fecha_detalle FROM {table_name} WHERE id_terreno = ?;", (idcota,))
            existen_cotas = set([tuple(row)[0] for row in cursor.fetchall()])
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
                if contador % 1000 == 0 and lote_registros:
                    cursor.executemany(f"""INSERT INTO {table_name} (id_terreno, fecha_detalle, nivel_detalle, observacion_detalle) VALUES (?, ?, ?, ?)""", lote_registros)
                    lote_registros = []
            if lote_registros:
                cursor.executemany(f"""INSERT INTO {table_name} (id_terreno, fecha_detalle, nivel_detalle, observacion_detalle) VALUES (?, ?, ?, ?)""", lote_registros)

            conn.commit()
            return True
        except Exception as e:
            print("Error al guardar data terreno: " + str(e))
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlComprobarExisteNombreCotaTerreno(proyecto, nombre):
        conn = None
        sql = """SELECT * FROM cotasterreno WHERE id_proyecto = ? AND nombre_terreno = ?;"""
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
            print("Error al comprobar nombre terreno: " + str(e))
            return False, None
        finally:
            if conn:
                conn.close()
    
    def mdlRegistrarFormatoCotaTerreno(proyecto_id, componente, nombre, comentario):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # Registrar la nueva cota de terreno con OUTPUT para obtener el ID
            cur.execute("""INSERT INTO cotasterreno (id_proyecto, nombre_terreno, comentario_terreno) OUTPUT INSERTED.id_terreno VALUES (?, ?, ?);""",
                        (proyecto_id, nombre, comentario))
            id_equipo = cur.fetchone()[0]
            # Registrar la cota en la tabla instrumentacion
            cur.execute("""INSERT INTO instrumentacion (id_componente, tipo_equipo, nombre_equipo, id_equipo, tabla_equipo) VALUES (?, ?, ?, ?, ?);""",
                        (componente, 'COTATERRENO', nombre, id_equipo, 'cotasterreno'))
            conn.commit()
            return id_equipo
        except Exception as e:
            print("Error al guardar cota terreno: " + str(e))
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()

    # LISTAR DATA COTAS TERRENO DETALLE POR ID    
    def mdlObtenerDataCotasTerrenoDetalle(idsuelo):
        conn = None
        sql = """SELECT s.nombre_terreno, d.fecha_detalle, d.nivel_detalle, d.id_detalle FROM cotaterreno_detalle d INNER JOIN cotasterreno s
        ON d.id_terreno = s.id_terreno WHERE d.id_terreno = ? ORDER BY d.fecha_detalle;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idsuelo,))
            results = [tuple(row) for row in cur.fetchall()]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al consultar terreno detalle: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # LISTAR DATA TERRENO DETALLE POR ID    
    def mdlObtenerDataTerrenoDetalle(sueloid):
        conn = None
        sql = """SELECT d.*, t.nombre_terreno FROM cotaterreno_detalle d INNER JOIN cotasterreno t ON d.id_terreno = t.id_terreno
            WHERE d.id_terreno = ? ORDER BY d.fecha_detalle ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (sueloid,))
            results = [tuple(row) for row in cur.fetchall()]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al consultar suelo detalle: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # Info de suelo fundacion por id
    def mdlTraerInfoCotaTerreno(idsuelo):
        conn = None
        sql = """SELECT * FROM cotasterreno WHERE id_terreno = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idsuelo,))
            row = cur.fetchone()
            if row:
                return tuple(row)
            else:
                return None
        except Exception as e:
            print("Error al consultar cota terreno: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # ACTUALIZAR COTA DE TERRENO      
    def mdlActualizarCotaTerreno(idcota, nombre, comentario):
        conn = None
        sql = """UPDATE cotasterreno SET nombre_terreno = ?, comentario_terreno = ? WHERE id_terreno = ?;"""
        try:
            conn = Connection.connectionDB()
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
    def mdlEliminarDetalleTerreno(idsuelo):
        conn = None
        sql = """DELETE FROM cotaterreno_detalle WHERE id_terreno = ?;"""
        try:
            conn = Connection.connectionDB()
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
    def mdlComprobarExisteCotaTerreno(idpiezo, tipo, fecha, hora):
        conn = None
        fecha_nueva = datetime.strptime(fecha, '%d/%m/%Y').strftime('%Y-%m-%d')
        fecha_hora = fecha_nueva + " " + hora
        sql = """SELECT * FROM cotasterreno WHERE id_piezometro = ? AND tipo_piezometro = ? AND fecha_cota = ?;"""
        try:
            conn = Connection.connectionDB()
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
    def mdlGuardarDataCota(idcota, tipo, fecha, hora, nivel):
        conn = None
        fecha_nueva = datetime.strptime(fecha, '%d/%m/%Y').strftime('%Y-%m-%d')
        fecha_hora_nueva = fecha_nueva + " " + hora
        sql = """INSERT INTO cotasterreno (id_piezometro, tipo_piezometro, fecha_cota, nivel_cota) VALUES (?, ?, ?, ?)"""
        try:
            conn = Connection.connectionDB()
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
    def mdlGuardarLecturasCotaPiezometrica(data):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # Crear un conjunto de tuplas con los valores de fecha y hora para comparar los registros existentes
            idpiezo = data[0][0]
            tipo = data[0][1]
            cursor.execute("SELECT fecha_cota FROM cotas_piezometricas WHERE id_piezometro = ? AND tipo_piezometro = ?", (idpiezo, tipo))
            existen_piezometros = set([tuple(row)[0] for row in cursor.fetchall()])
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
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    # Obtener data de cotas piezometricas por proyecto id
    def mdlObtenerDataCotasPiezometricas(proyecto):
        conn = None
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
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyecto, proyecto))
            results = [tuple(row) for row in cur.fetchall()]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al consultar piezometricas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # LISTAR DATA COTAS DETALLE POR ID Y TIPO   
    def mdlObtenerDataCotaDetalle(idpiezo, tipopiezo):
        conn = None
        sql = """SELECT * FROM cotas_piezometricas WHERE id_piezometro = ? AND tipo_piezometro = ? ORDER BY fecha_cota ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idpiezo, tipopiezo))
            results = [tuple(row) for row in cur.fetchall()]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al consultar cota detalle: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlActualizarLecturaCotapiezometrica(idcota, fecha, nivel):
        conn = None
        sql = """UPDATE cotas_piezometricas SET fecha_cota = ?, nivel_cota = ? WHERE id_cota = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # guardar en historial
            query_select = '''SELECT fecha_cota, nivel_cota, id_cota FROM cotas_piezometricas WHERE id_cota = ?;'''
            cur.execute(query_select, (idcota,))
            row = cur.fetchone()
            datos_anteriores = tuple(row) if row else None
            if datos_anteriores:
                fecha_cambio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                accion = "update"
                tabla = "cotas_piezometricas"
                cambios = f"Antiguos: {datos_anteriores}, Nuevos: [{fecha}, {nivel}, {idcota}]"
                query_historial = """INSERT INTO historial (idproyecto, fecha, accion, tabla, cambios, usuario, nombres)
                VALUES (?, ?, ?, ?, ?, ?, ?);"""
                cur.execute(query_historial, (fecha_cambio, accion, tabla, cambios))
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
    
    def mdlComprobarUltimaCotapiezometrica(idpiezo, tipopiezo):
        conn = None
        sql = """SELECT COUNT(*) FROM cotas_piezometricas WHERE id_piezometro = ? AND tipo_piezometro = ?;"""
        try:
            conn = Connection.connectionDB()
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
    
    def mdlEliminarLecturaCotapiezometrica(idcota):
        conn = None
        sql = """DELETE FROM cotas_piezometricas WHERE id_cota = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # guardar en historial
            query_select = '''SELECT * FROM cotas_piezometricas WHERE id_cota = ?;'''
            cur.execute(query_select, (idcota,))
            row = cur.fetchone()
            datos_anteriores = tuple(row) if row else None
            if datos_anteriores:
                fecha_cambio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                accion = "delete"
                tabla = "cotas_piezometricas"
                cambios = f"Datos: {datos_anteriores}"
                query_historial = """INSERT INTO historial (idproyecto, fecha, accion, tabla, cambios, usuario, nombres)
                VALUES (?, ?, ?, ?, ?, ?, ?);"""
                cur.execute(query_historial, (fecha_cambio, accion, tabla, cambios))
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
            
    def mdlActualizarLecturaCotaterreno(tabla, datos, idproyecto, username, nombres):
        conn = None
        sql = f"""UPDATE {tabla} SET fecha_detalle = ?, nivel_detalle = ?, observacion_detalle = ? WHERE id_detalle = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # guardar en historial
            query_select = f"""SELECT fecha_detalle, nivel_detalle, observacion_detalle, id_detalle FROM {tabla} WHERE id_detalle = ?;"""
            cur.execute(query_select, (datos[-1],))
            row = cur.fetchone()
            datos_anteriores = tuple(row) if row else None
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
    
    def mdlEliminarLecturaCotaterreno(tabla, iddetalle, idproyecto, username, nombres):
        conn = None
        sql = f"""DELETE FROM {tabla} WHERE id_detalle = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # guardar en historial
            query_select = f"""SELECT * FROM {tabla} WHERE id_detalle = ?;"""
            cur.execute(query_select, (iddetalle,))
            row = cur.fetchone()
            datos_anteriores = tuple(row) if row else None
            if datos_anteriores:
                fecha_cambio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                accion = "delete"
                cambios = f"Datos: {datos_anteriores}"
                query_historial = """INSERT INTO historial (idproyecto, fecha, accion, tabla, cambios, usuario, nombres)
                VALUES (?, ?, ?, ?, ?, ?, ?);"""
                cur.execute(query_historial, (idproyecto, fecha_cambio, accion, tabla, cambios, username, nombres))
            # eliminar lectura terreno
            cur.execute(sql, (iddetalle,))
            conn.commit()
            if cur.rowcount > 0:
                return True
            else:
                return False
        except Exception as e:
            print("Error al eliminar lectura terreno: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlEliminarLecturasBloqueCotaterreno(tabla, iddetalles, idproyecto, username, nombres):
        conn = None
        placeholders = ', '.join(['?' for _ in iddetalles])
        sql = f"""DELETE FROM {tabla} WHERE id_detalle IN ({placeholders});"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # guardar en historial
            query_select = f"""SELECT * FROM {tabla} WHERE id_detalle IN ({placeholders});"""
            cur.execute(query_select, iddetalles)
            results = [tuple(row) for row in cur.fetchall()]
            if results:
                fecha_cambio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                accion = "delete"
                cambios = f"Datos: {results}"
                query_historial = """INSERT INTO historial (idproyecto, fecha, accion, tabla, cambios, usuario, nombres)
                VALUES (?, ?, ?, ?, ?, ?, ?);"""
                cur.execute(query_historial, (idproyecto, fecha_cambio, accion, tabla, cambios, username, nombres))
            # eliminar lecturas terreno
            cur.execute(sql, iddetalles)
            conn.commit()
            if cur.rowcount > 0:
                return True
            else:
                return False
        except Exception as e:
            print("Error al eliminar lecturas terrenos: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlCambiarComponenteCotasTerreno(idcomponente, nuevocomponente):
        conn = None
        sql = """UPDATE instrumentacion SET id_componente = ? WHERE id_componente = ? AND tipo_equipo = 'COTATERRENO';"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # guardar info
            query_select = """SELECT * FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'COTATERRENO';"""
            cur.execute(query_select, (idcomponente,))
            results = [tuple(row) for row in cur.fetchall()]
            if results:
                cur.execute(sql, (nuevocomponente, idcomponente))
                conn.commit()
                return results
            else:
                return None
        except Exception as e:
            print("Error al cambiar componente terrenos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlEliminarCotasTerrenos(idcomponente):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # obtener info
            query_select = """SELECT * FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'COTATERRENO';"""
            cursor.execute(query_select, (idcomponente,))
            results = [tuple(row) for row in cursor.fetchall()]
            if results:
                query = """DELETE FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'COTATERRENO';"""
                cursor.execute(query, (idcomponente,))
                conn.commit()
                if cursor.rowcount > 0:
                    return results
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
    
    def mdlEliminarDataCotasTerrenos(tabla, terrenos):
        conn = None
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
    
    def mdlObtenerInfoPluviometro(idinstrumento):
        conn = None
        sql = """SELECT c.* FROM cotasterreno c INNER JOIN instrumentacion i ON c.id_terreno = i.id_equipo WHERE i.id_instrumentacion = ?;"""
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
            print("Error al consultar info cota terreno: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # Eliminar cota terreno
    def mdlEliminarCotaTerreno(idinstrumento):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # obtener info para eliminar data
            query_select = """SELECT * FROM instrumentacion WHERE id_instrumentacion = ? AND tipo_equipo = 'COTATERRENO';"""
            cursor.execute(query_select, (idinstrumento,))
            row = cursor.fetchone()
            dataterreno = tuple(row) if row else None
            if dataterreno:
                query = """DELETE FROM instrumentacion WHERE id_instrumentacion = ? AND tipo_equipo = 'COTATERRENO';"""
                cursor.execute(query, (idinstrumento,))
                conn.commit()
                if cursor.rowcount > 0:
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
    
    def mdlEliminarCotaTerrenoData(tabla, idterreno):
        conn = None
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
    
    def mdlObtenerCotasTerreno(tabla, idcomponente, idinstrumento, fechaini, fechafin):
        conn = None
        try:
            conn = Connection.connectionDB()
            # SQL Server: usar DATEDIFF en lugar de julianday
            sql = f"""SELECT t.id_instrumentacion, p.nombre_terreno, d.fecha_detalle,
                CAST(DATEDIFF(DAY, FIRST_VALUE(CAST(d.fecha_detalle AS DATETIME)) OVER (PARTITION BY p.id_terreno ORDER BY d.fecha_detalle), CAST(d.fecha_detalle AS DATETIME)) AS FLOAT) AS dias,
                CAST(DATEDIFF(HOUR, FIRST_VALUE(CAST(d.fecha_detalle AS DATETIME)) OVER (PARTITION BY p.id_terreno ORDER BY d.fecha_detalle), CAST(d.fecha_detalle AS DATETIME)) AS FLOAT) AS horas,
                d.nivel_detalle
            FROM {tabla} d INNER JOIN cotasterreno p ON d.id_terreno = p.id_terreno
            INNER JOIN instrumentacion t ON p.id_terreno = t.id_equipo
            INNER JOIN componentes c ON t.id_componente = c.id_componente
            WHERE c.id_componente = ? AND t.id_instrumentacion = ? AND d.fecha_detalle BETWEEN ? AND ?
            ORDER BY d.fecha_detalle;"""
            cur = conn.cursor()
            cur.execute(sql, (idcomponente, idinstrumento, fechaini, fechafin))
            results = [tuple(row) for row in cur.fetchall()]
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
    
    def mdlTraerDataCotaTerreno(idterreno):
        conn = None
        sql = """SELECT i.id_instrumentacion, i.id_componente, c.nombre_componente FROM instrumentacion i
        INNER JOIN componentes c ON i.id_componente = c.id_componente
        WHERE i.id_equipo = ? AND i.tipo_equipo = 'COTATERRENO';"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idterreno,))
            row = cur.fetchone()
            if row:
                return tuple(row)
            else:
                return None
        except Exception as e:
            print("Error al traer data terreno: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlCambiarCotaterrenoComponente(idinstrumento, nuevocomponente):
        conn = None
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
    