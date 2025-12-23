from services.security.apis.conexiones.connection import Connection
from datetime import datetime

class PiezometroModel:
    
    @staticmethod
    def mdlObtenerFechaMaximaPiezometrosCuerda(tabla):
        conn = None
        sql = f"""SELECT MAX(fecha_cuerda) AS max_fecha FROM {tabla};"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchone()
            if row:
                return tuple(row)
            else:
                return None
        except Exception as e:
            print("Error al obtener fechas max piezo cuerda: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerFechaMaximaPiezometrosManual(tabla):
        conn = None
        sql = f"""SELECT MAX(fecha_piezometro) AS max_fecha FROM {tabla};"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchone()
            if row:
                return tuple(row)
            else:
                return None
        except Exception as e:
            print("Error al obtener fechas max piezo manual: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # LISTAR LOS PIEZOMETROS DE CUERDA VIBRANTE POR PROYECTO    
    @staticmethod
    def mdlListarPiezometrosCuerdaProyecto(proyecto, idcomponente, idpiezo, fecha):
        conn = None
        # Cambio: LIMIT 1 -> TOP 1 para SQL Server
        sql = f"""SELECT p.id_piezometro, p.nombre_piezometro, c.id_componente, p.este_piezometro, p.norte_piezometro,
        p.elevacion_piezometro, p.inclinacion_piezometro, p.azimut_piezometro,
		p.tipo_piezometro, d.fecha_cuerda, d.medida_calculada,
        COALESCE(
                (SELECT TOP 1 c2.nivel_cota FROM cotas_piezometricas c2 WHERE c2.id_piezometro = d.id_piezometro AND c2.tipo_piezometro = 'PCV'
                AND c2.fecha_cota <= d.fecha_cuerda ORDER BY c2.fecha_cota DESC),
                (SELECT TOP 1 c3.nivel_cota FROM cotas_piezometricas c3 WHERE c3.id_piezometro = d.id_piezometro AND c3.tipo_piezometro = 'PCV'
                ORDER BY c3.fecha_cota ASC)
            ) AS cota
		FROM piezometrocuerdas p
		INNER JOIN piezometrocuerda_detalle{proyecto} d ON p.id_piezometro = d.id_piezometro
		INNER JOIN instrumentacion t ON p.id_piezometro = t.id_equipo
		INNER JOIN componentes c ON t.id_componente = c.id_componente
        WHERE c.id_proyecto = ? AND t.id_instrumentacion = ? AND c.id_componente = ?
		AND d.fecha_cuerda = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyecto, idpiezo, idcomponente, fecha))
            row = cur.fetchone()
            if row:
                return tuple(row)
            else:
                return None
        except Exception as e:
            print("Error al consultar piezometro: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # LISTAR LOS PIEZOMETROS POR PROYECTO    
    @staticmethod
    def mdlListarPiezometrosManualProyecto(proyecto, idcomponente, idinstrumento, fecha):
        conn = None
        # Cambio: LIMIT 1 -> TOP 1 para SQL Server
        sql = f"""SELECT p.id_piezometro, p.nombre_piezometro, c.id_componente, p.este_piezometro, p.norte_piezometro,
        p.elevacion_piezometro, p.inclinacion_piezometro, p.azimut_piezometro, p.stickup_piezometro,
		p.tipo_piezometro, d.fecha_piezometro, d.medida_piezometro,
        COALESCE(
                (SELECT TOP 1 c2.nivel_cota FROM cotas_piezometricas c2 WHERE c2.id_piezometro = d.id_piezometro AND c2.tipo_piezometro = 'PVC'
                AND c2.fecha_cota <= d.fecha_piezometro ORDER BY c2.fecha_cota DESC),
                (SELECT TOP 1 c3.nivel_cota FROM cotas_piezometricas c3 WHERE c3.id_piezometro = d.id_piezometro AND c3.tipo_piezometro = 'PVC'
                ORDER BY c3.fecha_cota ASC)
            ) AS cota
		FROM piezometromanuales p
		INNER JOIN piezometromanual_detalle{proyecto} d ON p.id_piezometro = d.id_piezometro
		INNER JOIN instrumentacion t ON p.id_piezometro = t.id_equipo
		INNER JOIN componentes c ON t.id_componente = c.id_componente
        WHERE c.id_proyecto = ? AND t.id_instrumentacion = ? AND c.id_componente = ?
		AND d.fecha_piezometro = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyecto, idinstrumento, idcomponente, fecha))
            row = cur.fetchone()
            if row:
                return tuple(row)
            else:
                return None
        except Exception as e:
            print("Error al consultar piezometro manual: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # LISTAR LOS PIEZOMETROS CUERDA VIBRANTE ÚNICOS QUE TENGAN DATA POR PROYECTO    
    @staticmethod
    def mdlListarPiezometrosCuerdaInfoProyecto(proyecto):
        conn = None
        sql = """SELECT DISTINCT p.*, 'Automatizado' AS tipo FROM piezometrocuerdas p INNER JOIN piezometrocuerda_detalle d ON p.id_piezometro = d.id_piezometro 
        WHERE p.id_proyecto = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyecto,))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al consultar piezometros cuerda vibrante: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
                
    # LISTAR LOS PIEZOMETROS ÚNICOS QUE TENGAN DATA POR PROYECTO    
    @staticmethod
    def mdlListarPiezometrosManualInfoProyecto(proyecto):
        conn = None
        sql = """SELECT DISTINCT p.*, 'Manual' AS tipo FROM piezometros p INNER JOIN piezometro_detalle d ON p.id_piezometro = d.id_piezometro 
        WHERE p.id_proyecto = ? AND p.estado_piezometro = 1;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyecto,))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al consultar piezometros: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # LISTAR DATA PIEZOMETROS POR PROYECTO ID    
    @staticmethod
    def mdlDataPiezometrosCuerdaProyectoId(proyectoid):
        conn = None
        sql = """SELECT p.nombre_piezometro, d.fecha_cuerda, d.frecuencia_cuerda, d.temperatura_cuerda, d.presion_barometrica, d.observacion_cuerda, d.medida_calculada, 
        p.norte_piezometro, p.este_piezometro, p.elevacion_piezometro FROM piezometrocuerdas p INNER JOIN piezometrocuerda_detalle d 
        ON p.id_piezometro = d.id_piezometro WHERE p.id_proyecto = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyectoid,))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al consultar piezometros: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    # LISTAR DATA PIEZOMETROS POR PROYECTO    
    @staticmethod
    def mdlMostrarDataPiezometrosCuerdaProyecto(iddetalle):
        conn = None
        sql = """SELECT p.nombre_piezometro, d.fecha_cuerda, d.frecuencia_cuerda, d.temperatura_cuerda, d.presion_barometrica, d.observacion_cuerda, d.medida_calculada, 
        p.norte_piezometro, p.este_piezometro, p.elevacion_piezometro FROM piezometrocuerdas p INNER JOIN piezometrocuerda_detalle d 
        ON p.id_piezometro = d.id_piezometro WHERE d.id_cuerda = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (iddetalle,))
            row = cur.fetchone()
            if row:
                return tuple(row)
            else:
                return None
        except Exception as e:
            print("Error al consultar piezometros: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # LISTAR DATA PIEZOMETROS MANUALES POR PROYECTO ID    
    @staticmethod
    def mdlDataPiezometrosManualProyectoId(proyectoid):
        conn = None
        sql = """SELECT p.nombre_piezometro, d.fecha_piezometro, d.medida_piezometro, d.observacion_detalle, p.norte_piezometro, p.este_piezometro, 
        p.elevacion_piezometro FROM piezometros p INNER JOIN piezometro_detalle d ON p.id_piezometro = d.id_piezometro WHERE p.id_proyecto = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyectoid,))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al consultar piezometros: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    # LISTAR DATA PIEZOMETROS MANUALES POR PROYECTO    
    @staticmethod
    def mdlMostrarDataPiezometrosManualProyecto(iddetalle):
        conn = None
        sql = """SELECT p.nombre_piezometro, d.fecha_piezometro, d.medida_piezometro, d.observacion_detalle, p.norte_piezometro, p.este_piezometro, 
        p.elevacion_piezometro FROM piezometros p INNER JOIN piezometro_detalle d ON p.id_piezometro = d.id_piezometro WHERE d.id_detalle = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (iddetalle,))
            row = cur.fetchone()
            if row:
                return tuple(row)
            else:
                return None
        except Exception as e:
            print("Error al consultar piezometros: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # GUARDAR NUEVO PIEZOMETRO MANUAL       
    @staticmethod
    def mdlGuardarNuevoPiezometroManual(componente, datos, fecha, nivel, tipo):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            
            # Validar que el componente y el tipo sean PIEZOMETROMANUAL y que el nombre coincida
            sql_validacion = """SELECT COUNT(*) FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = ? AND nombre_equipo = ?;"""
            cur.execute(sql_validacion, (componente, 'PIEZOMETROMANUAL', datos[1]))
            count = cur.fetchone()[0]
            if count > 0:
                return "NO"
            
            # Insertar con OUTPUT INSERTED.id_piezometro para obtener el ID en SQL Server
            sql_insert = """INSERT INTO piezometromanuales (id_proyecto, nombre_piezometro, codigo_piezometro, norte_piezometro, este_piezometro, elevacion_piezometro,
            fundacion_piezometro, stickup_piezometro, inclinacion_piezometro, azimut_piezometro, comentario_piezometro)
            OUTPUT INSERTED.id_piezometro
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""
            
            cur.execute(sql_insert, datos)
            id_piezometro = cur.fetchone()[0] # Capturar el ID retornado por OUTPUT
            
            # Registrar la cota en la tabla cotas_piezometricas
            sql_detalle = """INSERT INTO cotas_piezometricas (id_piezometro, tipo_piezometro, fecha_cota, nivel_cota) VALUES (?, ?, ?, ?);"""
            cur.execute(sql_detalle, (id_piezometro, tipo, fecha, nivel))
            
            # Actualizar la tabla instrumentacion
            sql_instrumentacion = """INSERT INTO instrumentacion (id_componente, tipo_equipo, nombre_equipo, id_equipo, tabla_equipo) VALUES (?, ?, ?, ?, ?);"""
            cur.execute(sql_instrumentacion, (componente, 'PIEZOMETROMANUAL', datos[1], id_piezometro, 'piezometromanuales'))
            
            conn.commit()
            return "OK"
        except Exception as e:
            print("Error al guardar piezómetro manual: " + str(e))
            if conn:
                conn.rollback()
            return "ERROR"
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlRegistrarPiezometroManualFormato(componente, datos, fecha, nivel, tipo):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            
            # Insertar con OUTPUT
            sql_insert = """INSERT INTO piezometromanuales (id_proyecto, nombre_piezometro, codigo_piezometro, norte_piezometro, este_piezometro, elevacion_piezometro,
            fundacion_piezometro, stickup_piezometro, inclinacion_piezometro, azimut_piezometro, comentario_piezometro)
            OUTPUT INSERTED.id_piezometro
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""
            
            cur.execute(sql_insert, datos)
            id_piezometro = cur.fetchone()[0] # Captura inmediata
            
            # Registrar la cota
            sql_detalle = """INSERT INTO cotas_piezometricas (id_piezometro, tipo_piezometro, fecha_cota, nivel_cota) VALUES (?, ?, ?, ?);"""
            cur.execute(sql_detalle, (id_piezometro, tipo, fecha, nivel))
            
            # Actualizar la tabla instrumentacion
            sql_instrumentacion = """INSERT INTO instrumentacion (id_componente, tipo_equipo, nombre_equipo, id_equipo, tabla_equipo) VALUES (?, ?, ?, ?, ?);"""
            cur.execute(sql_instrumentacion, (componente, 'PIEZOMETROMANUAL', datos[1], id_piezometro, 'piezometromanuales'))
            
            conn.commit()
            return id_piezometro
        except Exception as e:
            print("Error al guardar piezómetro manual: " + str(e))
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()
    
    # GUARDAR NUEVO PIEZOMETRO CUERDA
    @staticmethod
    def mdlGuardarNuevoPiezometroCuerda(componente, datos, nivelactual, fecha, tipo):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            
            # Validar
            sql_validacion = """SELECT COUNT(*) FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = ? AND nombre_equipo = ?;"""
            cur.execute(sql_validacion, (componente, 'PIEZOMETROCUERDA', datos[2]))
            count = cur.fetchone()[0]
            if count > 0:
                return "NO"
            
            # Insertar con OUTPUT
            sql_insert = """INSERT INTO piezometrocuerdas (id_proyecto, id_formula, nombre_piezometro, serie_sensor, este_piezometro, norte_piezometro,
            elevacion_piezometro, fundacion_piezometro, inclinacion_piezometro, azimut_piezometro, frecuencia_inicial, temperatura_inicial, presion_inicial,
            factor_calibracion, temperatura_correccion, unidad_lectura, constante_a, constante_b, constante_c, factor_conversion, comentario_piezometro)
            OUTPUT INSERTED.id_piezometro
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""
            
            cur.execute(sql_insert, datos)
            id_piezometro = cur.fetchone()[0]
            
            # Registrar la cota
            sql_detalle = """INSERT INTO cotas_piezometricas (id_piezometro, tipo_piezometro, fecha_cota, nivel_cota) VALUES (?, ?, ?, ?);"""
            cur.execute(sql_detalle, (id_piezometro, tipo, fecha, nivelactual))
            
            # Actualizar instrumentacion
            sql_instrumentacion = """INSERT INTO instrumentacion (id_componente, tipo_equipo, nombre_equipo, id_equipo, tabla_equipo) VALUES (?, ?, ?, ?, ?);"""
            cur.execute(sql_instrumentacion, (componente, 'PIEZOMETROCUERDA', datos[2], id_piezometro, 'piezometrocuerdas'))
            
            conn.commit()
            return "OK"
        except Exception as e:
            print("Error al guardar piezómetro de cuerda: " + str(e))
            if conn:
                conn.rollback()
            return "ERROR"
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlRegistrarPiezometroCuerdaFormato(componente, datos, fecha, nivelactual, tipo):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            
            # Insertar con OUTPUT
            sql_insert = """INSERT INTO piezometrocuerdas (id_proyecto, nombre_piezometro, serie_sensor, este_piezometro, norte_piezometro, elevacion_piezometro,
            fundacion_piezometro, inclinacion_piezometro, azimut_piezometro, factor_calibracion, temperatura_correccion, frecuencia_inicial, temperatura_inicial,
            presion_inicial, unidad_lectura, constante_a, constante_b, constante_c, factor_conversion, comentario_piezometro)
            OUTPUT INSERTED.id_piezometro
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""
            
            cur.execute(sql_insert, datos)
            id_piezometro = cur.fetchone()[0]
            
            # Registrar la cota
            sql_detalle = """INSERT INTO cotas_piezometricas (id_piezometro, tipo_piezometro, fecha_cota, nivel_cota) VALUES (?, ?, ?, ?);"""
            cur.execute(sql_detalle, (id_piezometro, tipo, fecha, nivelactual))
            
            # Actualizar instrumentacion
            sql_instrumentacion = """INSERT INTO instrumentacion (id_componente, tipo_equipo, nombre_equipo, id_equipo,tabla_equipo) VALUES (?, ?, ?, ?, ?);"""
            cur.execute(sql_instrumentacion, (componente, 'PIEZOMETROCUERDA', datos[1], id_piezometro, 'piezometrocuerdas'))
            
            conn.commit()
            return id_piezometro
        except Exception as e:
            print("Error al guardar piezómetro de cuerda formato: " + str(e))
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlValidarExisteFormula(formula):
        conn = None
        try:
            sql = """SELECT * FROM formulas_piezometros WHERE formula = ?;"""
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (formula,))
            resultado = cur.fetchone()
            if resultado:
                return False
            else:
                return True
        except Exception as e:
            print("Error al validar formula piezometro: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlRegistrarNuevaFormula(formula, sentencia):
        conn = None
        try:
            sql = """INSERT INTO formulas_piezometros (formula, sentencia) VALUES (?, ?);"""
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (formula, sentencia))
            conn.commit()
            return True
        except Exception as e:
            print("Error al guardar formula piezometro: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    # ACTUALIZAR PIEZOMETRO DE CUERDA VIBRANTE E INSTRUMENTACION
    @staticmethod
    def mdlActualizarPiezometroCuerda(datos, data):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = """UPDATE piezometrocuerdas SET id_formula = ?, nombre_piezometro = ?, serie_sensor = ?, este_piezometro = ?, norte_piezometro = ?,
            elevacion_piezometro = ?, fundacion_piezometro = ?, inclinacion_piezometro = ?, azimut_piezometro = ?, factor_calibracion = ?, 
            temperatura_correccion = ?, frecuencia_inicial = ?, temperatura_inicial = ?, presion_inicial = ?, unidad_lectura = ?, constante_a = ?,
            constante_b = ?, constante_c = ?, factor_conversion = ?, comentario_piezometro = ? WHERE id_piezometro = ?;"""
            cur = conn.cursor()
            cur.execute(sql, datos)
            
            query_instrumentacion = """UPDATE instrumentacion SET id_componente = ?, nombre_equipo = ?
            WHERE id_instrumentacion = ? AND tipo_equipo = 'PIEZOMETROCUERDA';"""
            cur = conn.cursor()
            cur.execute(query_instrumentacion, data)
            conn.commit()
            return True
        except Exception as e:
            print("Error al editar piezometro de cuerda vibrante: " + str(e))
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlActualizarPiezometroCuerdaFormato(datos):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = """UPDATE piezometrocuerdas SET serie_sensor = ?, este_piezometro = ?, norte_piezometro = ?, elevacion_piezometro = ?,
            fundacion_piezometro = ?, inclinacion_piezometro = ?, azimut_piezometro = ?, factor_calibracion = ?, 
            temperatura_correccion = ?, frecuencia_inicial = ?, temperatura_inicial = ?, presion_inicial = ?, constante_a = ?,
            constante_b = ?, constante_c = ?, factor_conversion = ?, comentario_piezometro = ? WHERE id_piezometro = ?;"""
            cur = conn.cursor()
            cur.execute(sql, datos)
            conn.commit()
            return True
        except Exception as e:
            print("Error al editar piezometro de cuerda vibrante: " + str(e))
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    # ACTUALIZAR ESTADO PIEZOMETRO DE CUERDA VIBRANTE         
    @staticmethod
    def mdlCambiarEstadoPiezometroCuerda(idpiezo, tipo):
        conn = None
        sql = """UPDATE piezometrocuerdas SET tipo_piezometro = ? WHERE id_piezometro = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (tipo, idpiezo))
            conn.commit()
            return True
        except Exception as e:
            print("Error al editar estado cuerda vibrante: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
                
    # ACTUALIZAR PIEZOMETRO MANUAL E INSTRUMENTACION
    @staticmethod
    def mdlActualizarPiezometroManual(datos, data):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = """UPDATE piezometromanuales SET nombre_piezometro = ?, codigo_piezometro = ?, norte_piezometro = ?, este_piezometro = ?, elevacion_piezometro = ?, 
            fundacion_piezometro = ?, inclinacion_piezometro = ?, azimut_piezometro = ?, stickup_piezometro = ?, comentario_piezometro = ?
            WHERE id_piezometro = ?"""
            cur = conn.cursor()
            cur.execute(sql, datos)
            
            query_instrumentacion = """UPDATE instrumentacion SET id_componente = ?, nombre_equipo = ?
            WHERE id_instrumentacion = ? AND tipo_equipo = 'PIEZOMETROMANUAL';"""
            cur = conn.cursor()
            cur.execute(query_instrumentacion, data)
            conn.commit()
            return True
        except Exception as e:
            print("Error al actualizar piezometro manual: " + str(e))
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
        # ACTUALIZAR PIEZOMETRO CASAGRANDE
    @staticmethod
    def mdlActualizarPiezometroManualFormato(datos):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = """UPDATE piezometromanuales SET codigo_piezometro = ?, norte_piezometro = ?, este_piezometro = ?, elevacion_piezometro = ?, 
            fundacion_piezometro = ?, inclinacion_piezometro = ?, azimut_piezometro = ?, stickup_piezometro = ?, comentario_piezometro = ?
            WHERE id_piezometro = ?"""
            cur = conn.cursor()
            cur.execute(sql, datos)
            conn.commit()
            return True
        except Exception as e:
            print("Error al actualizar piezometro manual: " + str(e))
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    # CAMBIAR TIPO DE DATA PIEZOMETRO CUERDA
    @staticmethod
    def mdlCambiarTipoDataPiezometro(idpiezo, estado):
        conn = None
        sql = """UPDATE piezometrocuerdas SET estado_piezometro = ? WHERE id_piezometro = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (estado, idpiezo))
            conn.commit()
            return True
        except Exception as e:
            print("Error al cambiar tipo data piezómetro: " + str(e))
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
                
    # Validar si existe piezómetro con el mismo nombre
    @staticmethod
    def mdlComprobarExisteNombrePiezometro(proyecto, nombre, tipo):
        conn = None
        if tipo == "Automatizado":
            sql = """SELECT * FROM piezometrocuerdas WHERE id_proyecto = ? AND nombre_piezometro = ?;"""
        else:
            sql = """SELECT * FROM piezometromanuales WHERE id_proyecto = ? AND nombre_piezometro = ?;"""
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
            print("Error al comprobar piezómetro: " + str(e))
            return False, None
        finally:
            if conn:
                conn.close()
    
    # GUARDAR NUEVO PIEZOMETRO
    @staticmethod
    def mdlRegistrarMedidaPiezometroManual(idpiezometro, fecha, hora, medida):
        conn = None
        try:
            conn = Connection.connectionDB()
            fecha_nueva = datetime.strptime(fecha, '%d/%m/%Y').strftime('%Y-%m-%d')
            fecha_hora = fecha_nueva + " " + hora
            
            # Nota: SQL Server maneja bien el formato 'YYYY-MM-DD HH:MM:SS'
            sql = """INSERT INTO piezometro_detalle (observacion_detalle, id_piezometro, fecha_piezometro, medida_piezometro) VALUES ('Manual', ?, ?, ?)"""
            
            cur = conn.cursor()
            cur.execute(sql, (idpiezometro, fecha_hora, medida))
            conn.commit()
            return True
        except Exception as e:
            print("Error al guardar piezómetro manual: " + str(e))
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    # REGISTRAR LECTURAS ORIGINAL PIEZOMETROS DE CUERDA VIBRANTE DESDE LA TABLA   
    @staticmethod
    def mdlGuardarPiezometrosCuerdaTablaOriginal(data):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # Optimización para inserciones masivas en pyodbc
            cursor.fast_executemany = True
            
            # Crear un conjunto de tuplas con los valores de fecha para comparar los registros existentes
            idpiezo = data[0][0]
            
            # SELECT para verificar existentes
            cursor.execute("SELECT fecha_cuerda FROM piezometrocuerda_detalle WHERE id_piezometro = ?", (idpiezo,))
            existen_piezometros = set([row[0] for row in cursor.fetchall()]) # row[0] puede venir como string o datetime dependiendo del driver/config
            
            # Convertir fechas del set a string ISO si vienen como objetos datetime para comparar uniformemente
            existen_piezometros_str = set()
            for fecha in existen_piezometros:
                if isinstance(fecha, str):
                     existen_piezometros_str.add(fecha)
                else:
                     existen_piezometros_str.add(fecha.strftime('%Y-%m-%d %H:%M:%S'))

            lote_registros = []
            
            for fila in data:
                fecha_original = fila[1]
                hora_original = fila[2]
                
                # completar el formato de fecha
                fecha_simple = datetime.strptime(fecha_original, "%d/%m/%Y")
                fecha_formateada = fecha_simple.strftime("%d/%m/%Y")
                fecha_nueva = datetime.strptime(fecha_formateada, '%d/%m/%Y').strftime('%Y-%m-%d')
                
                # SQL Server requiere segundos para coincidir exactamente si la columna es DATETIME, asumimos 00 si no hay
                if len(hora_original.split(':')) == 2:
                     hora_original += ":00"
                     
                fecha_hora_nueva = fecha_nueva + " " + hora_original
                
                # Verifica si el registro no existe en el conjunto
                if fecha_hora_nueva not in existen_piezometros_str:
                    datito = []
                    datito.append(fila[0]) # id piezometro
                    datito.append(fecha_hora_nueva)
                    datito.append(abs(float(fila[3]))) # siempre positivo la medida
                    datito.append(fila[4]) # temperatura
                    datito.append(fila[5]) # presion
                    datito.append(fila[6]) # Observacion
                    lote_registros.append(datito)
                    
            if lote_registros:
                sql_insert = """INSERT INTO piezometrocuerda_detalle (id_piezometro, fecha_cuerda, frecuencia_cuerda, temperatura_cuerda, presion_barometrica, observacion_cuerda) VALUES (?, ?, ?, ?, ?, ?)"""
                cursor.executemany(sql_insert, lote_registros)
                    
            conn.commit()
            return True
        except Exception as e:
            print("Error al guardar los piezometros de cuerda " + str(e))
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    # REGISTRAR LECTURAS CALCULADAS DE CUERDA VIBRANTE DESDE LA TABLA  
    @staticmethod
    def mdlGuardarPiezometrosCuerdaCalculoTabla(proyectoid, data, idspiezos):
        table_name = f"piezometrocuerda_detalle{proyectoid}"
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            cursor.fast_executemany = True
            
            # Sintaxis T-SQL para crear tabla si no existe
            # Se usa IDENTITY(1,1) en lugar de AUTOINCREMENT
            # Se usan tipos compatibles SQL Server (DATETIME, FLOAT, VARCHAR)
            sql_create = f"""
            IF OBJECT_ID('{table_name}', 'U') IS NULL
            CREATE TABLE [{table_name}] (
                id_cuerda INT IDENTITY(1,1) PRIMARY KEY,
                id_piezometro INT NOT NULL,
                fecha_cuerda DATETIME NOT NULL,
                frecuencia_cuerda FLOAT NOT NULL,
                temperatura_cuerda FLOAT NOT NULL,
                presion_barometrica FLOAT,
                medida_calculada FLOAT,
                observacion_cuerda VARCHAR(MAX),
                estado_cuerda INT NOT NULL DEFAULT 1
            );"""
            cursor.execute(sql_create)
            
            # Validar existentes
            placeholders = ', '.join(['?' for _ in idspiezos])
            sql_check = f"SELECT id_piezometro, fecha_cuerda FROM {table_name} WHERE id_piezometro IN ({placeholders})"
            cursor.execute(sql_check, list(idspiezos))
            
            existen_piezometros = set()
            for row in cursor.fetchall():
                p_id = row[0]
                p_fecha = row[1]
                # Normalizar fecha a string para comparación
                if not isinstance(p_fecha, str):
                    p_fecha = p_fecha.strftime('%Y-%m-%d %H:%M:%S')
                existen_piezometros.add((p_id, p_fecha))
            
            lote_registros = []
            
            for fila in data:
                id_piezo = fila[0]
                fecha_original = fila[1]
                hora_original = fila[2]
                
                if len(hora_original.split(':')) == 2:
                     hora_original += ":00"
                     
                fecha_hora_nueva = fecha_original + " " + hora_original
                
                # Verifica si el registro no existe
                if (id_piezo, fecha_hora_nueva) not in existen_piezometros:
                    datito = []
                    datito.append(id_piezo)
                    datito.append(fecha_hora_nueva)
                    datito.append(abs(float(fila[3])))  # frecuencia
                    datito.append(fila[4])  # temperatura
                    datito.append(fila[5])  # presion barometrica
                    datito.append(fila[6])  # data calculada MCA
                    datito.append(fila[7])  # Observacion
                    lote_registros.append(datito)

            if lote_registros:
                sql_insert = f"""
                    INSERT INTO {table_name} (
                        id_piezometro, fecha_cuerda, frecuencia_cuerda,
                        temperatura_cuerda, presion_barometrica,
                        medida_calculada, observacion_cuerda
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """
                cursor.executemany(sql_insert, lote_registros)

            conn.commit()
            return True
        except Exception as e:
            if conn:
                conn.rollback()
            print("Error al guardar los piezometros de cuerda: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    # Validar si existe piezómetro con el mismo nombre al actualizar
    @staticmethod
    def mdlComprobarActualizarNombrePiezometro(idpiezo, nombre, tipo):
        conn = None
        if tipo == "Automatizado":
            sql = """SELECT * FROM piezometrocuerdas WHERE nombre_piezometro = ? AND id_piezometro != ?;"""
        else:
            sql = """SELECT * FROM piezometromanuales WHERE nombre_piezometro = ? AND id_piezometro != ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (nombre, idpiezo)) # Nota: Orden de parametros (nombre, idpiezo) corregido segun query
            row = cur.fetchone()
            if row:
                return True
            else:
                return False
        except Exception as e:
            print("Error al comprobar piezómetro: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
                              
    # REGISTRAR PIEZOMETROS MANUALES DESDE LA TABLA   
    @staticmethod
    def mdlGuardarPiezometrosManualesTabla(idproyecto, data):
        nombretabla = "piezometromanual_detalle" + str(idproyecto)
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            cursor.fast_executemany = True
            
            # Sintaxis T-SQL
            sqltable = f"""
            IF OBJECT_ID('{nombretabla}', 'U') IS NULL
            CREATE TABLE [{nombretabla}] (
                id_detalle INT IDENTITY(1,1) PRIMARY KEY,
                id_piezometro INT NOT NULL,
                fecha_piezometro DATETIME NOT NULL,
                medida_piezometro FLOAT,
                observacion_detalle VARCHAR(MAX),
                estado_manual INT NOT NULL DEFAULT 1
            );
            """
            cursor.execute(sqltable)
            
            # Verificar existentes
            cursor.execute(f"SELECT fecha_piezometro FROM {nombretabla} WHERE id_piezometro = ?", (data[0][0],))
            
            existen_piezometros = set()
            for row in cursor.fetchall():
                f_db = row[0]
                if not isinstance(f_db, str):
                    f_db = f_db.strftime('%Y-%m-%d %H:%M:%S')
                existen_piezometros.add(f_db)

            lote_registros = []

            for fila in data:
                fecha_original = fila[1]
                hora_original = fila[2]
                
                if len(hora_original.split(':')) == 2:
                     hora_original += ":00"
                
                fecha_hora_nueva = fecha_original + " " + hora_original

                if fecha_hora_nueva not in existen_piezometros:
                    datito = []
                    datito.append(fila[0])  # id_piezometro
                    datito.append(fecha_hora_nueva)
                    datito.append(abs(float(fila[3])))  # medida
                    datito.append(fila[4])  # observacion_detalle
                    lote_registros.append(datito)

            if lote_registros:
                sql_insert = f"""
                    INSERT INTO {nombretabla} (
                        id_piezometro, fecha_piezometro, medida_piezometro, observacion_detalle
                    ) VALUES (?, ?, ?, ?)
                """
                cursor.executemany(sql_insert, lote_registros)

            conn.commit()
            return True
        except Exception as e:
            if conn:
                conn.rollback()
            print("Error al guardar los piezometros manuales: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlGuardarCotasPiezometricasTabla(data):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            cursor.fast_executemany = True
            
            idpiezo = data[0][0]
            tipopiezo = data[0][1]
            
            cursor.execute("SELECT fecha_cota FROM cotas_piezometricas WHERE id_piezometro = ? AND tipo_piezometro = ?;", (idpiezo, tipopiezo))
            
            existen_cotas = set()
            for row in cursor.fetchall():
                f_db = row[0]
                if not isinstance(f_db, str):
                    f_db = f_db.strftime('%Y-%m-%d %H:%M:%S')
                existen_cotas.add(f_db)
            
            lote_registros = []
            
            for fila in data:
                nueva_fila = list(fila)
                # Formatear fecha para SQL Server (YYYY-MM-DD HH:MM:SS)
                # Asumiendo que viene YYYY-MM-DD
                fecha_str = f"{nueva_fila[2]} 00:00:00"
                nueva_fila[2] = fecha_str
                
                if fecha_str not in existen_cotas:
                    lote_registros.append(nueva_fila)
            
            if lote_registros:
                cursor.executemany("""INSERT INTO cotas_piezometricas (id_piezometro, tipo_piezometro, fecha_cota, nivel_cota) VALUES (?, ?, ?, ?);""", lote_registros)
            
            conn.commit()
            return True
        except Exception as e:
            if conn:
                conn.rollback()
            print("Error al guardar las cotas: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    # OBTENER DATA PIEZOMETRO AUTOMATIZADO 
    @staticmethod
    def mdlObtenerDataPiezometroA(idpiezo):
        conn = None
        sql = """SELECT
                pd.id_cuerda,
                pz.id_piezometro,
                pz.nombre_piezometro,
                pd.fecha_cuerda,
                pz.factor_calibracion,
                pz.temperatura_correccion,
                pd.frecuencia_cuerda,
                pd.temperatura_cuerda,
                pd.presion_barometrica,
                pz.elevacion_piezometro,
                pz.estado_piezometro,
                pd.medida_calculada, pz.unidad_lectura
                FROM piezometrocuerda_detalle pd 
                INNER JOIN piezometrocuerdas pz ON pd.id_piezometro = pz.id_piezometro 
                WHERE pd.id_piezometro = ?"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idpiezo,))
            rows = cur.fetchall()
            # Regla Crítica: Conversión a tuplas
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            return None
        finally:
            if conn:
                conn.close()
    
    # OBTENER DATA PIEZOMETRO AUTOMATIZADO ENTRE FECHAS
    @staticmethod
    def mdlObtenerDataPiezometroAutoFechas(idpiezo, fechaini, fechafin):
        conn = None
        # Corrección de Seguridad: Uso de parametros '?' en lugar de concatenación
        sql = """SELECT
                pd.id_cuerda,
                pz.id_piezometro,
                pz.nombre_piezometro,
                pd.fecha_cuerda,
                pz.factor_calibracion,
                pz.temperatura_correccion,
                pd.frecuencia_cuerda,
                pd.temperatura_cuerda,
                pd.presion_barometrica,
                pz.elevacion_piezometro,
                pz.estado_piezometro,
                pd.medida_calculada, pz.unidad_lectura
                FROM piezometrocuerda_detalle pd 
                INNER JOIN piezometrocuerdas pz ON pd.id_piezometro = pz.id_piezometro 
                WHERE pd.id_piezometro = ? AND pd.fecha_cuerda BETWEEN ? AND ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idpiezo, fechaini, fechafin))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            return None
        finally:
            if conn:
                conn.close()
                
        # OBTENER DATA PIEZOMETRO NORMAL 
    @staticmethod
    def mdlObtenerDataPiezometroN(idpiezodetalle):
        conn = None
        sql = """SELECT 
                pd.id_detalle,
                pz.id_piezometro,
                pz.nombre_piezometro,
                pd.fecha_piezometro,
                pd.medida_piezometro,
                pz.stickup_piezometro,
                pz.elevacion_piezometro
                FROM piezometro_detalle pd 
                INNER JOIN piezometros pz ON pd.id_piezometro = pz.id_piezometro 
                WHERE pd.id_piezometro = ?"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idpiezodetalle,))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            return None
        finally:
            if conn:
                conn.close()
    
    # OBTENER DATA PIEZOMETRO MANUAL ENTRE FECHAS
    @staticmethod
    def mdlObtenerDataPiezometroManualFechas(idpiezodetalle, fechaini, fechafin):
        conn = None
        # Corrección de seguridad: Uso de placeholders ? en lugar de concatenar strings
        sql = """SELECT 
            pd.id_detalle,
            pz.id_piezometro,
            pz.nombre_piezometro,
            pd.fecha_piezometro,
            pd.medida_piezometro,
            pz.stickup_piezometro,
            pz.elevacion_piezometro
            FROM piezometro_detalle pd
            INNER JOIN piezometros pz ON pd.id_piezometro = pz.id_piezometro 
            WHERE pd.id_piezometro = ? AND pd.fecha_piezometro BETWEEN ? AND ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idpiezodetalle, fechaini, fechafin))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            return None
        finally:
            if conn:
                conn.close()
                
    @staticmethod
    def mdlTraerInfoPiezometroCuerda(idipiezo):
        conn = None
        sql = """SELECT * FROM piezometrocuerdas WHERE id_piezometro = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idipiezo,))
            row = cur.fetchone()
            if row:
                return tuple(row)
            else:
                return None
        except Exception as e:
            print("Error al consultar piezometro cuerda: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlTraerInfoPiezometroManual(idipiezo):
        conn = None
        sql = """SELECT * FROM piezometros WHERE id_piezometro = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idipiezo,))
            row = cur.fetchone()
            if row:
                return tuple(row)
            else:
                return None
        except Exception as e:
            print("Error al consultar piezometro manual: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlTraerInfoDetallePiezometroCuerda(iddetalle):
        conn = None
        sql = """SELECT 'Automatizado' AS tipo, * FROM piezometrocuerda_detalle WHERE id_cuerda = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (iddetalle,))
            row = cur.fetchone()
            if row:
                return tuple(row)
            else:
                return None
        except Exception as e:
            print("Error al consultar detalle piezometro cuerda: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlTraerBaseDetallePiezometro(idpiezo):
        conn = None
        # LIMIT 1 -> TOP 1
        sql = """SELECT TOP 1 'Automatizado' AS tipo, * FROM piezometrocuerda_detalle WHERE id_piezometro = ? ORDER BY fecha_cuerda ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idpiezo,))
            row = cur.fetchone()
            if row:
                return tuple(row)
            else:
                return None
        except Exception as e:
            print("Error al consultar base piezometro cuerda: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlTraerInfoDetallePiezometroManual(iddetalle):
        conn = None
        sql = """SELECT 'Manual' AS tipo, * FROM piezometro_detalle WHERE id_detalle = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (iddetalle,))
            row = cur.fetchone()
            if row:
                return tuple(row)
            else:
                return None
        except Exception as e:
            print("Error al consultar detalle piezometro manual: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlEliminarPiezometroCuerda(idpiezometro):
        conn = None
        sql = """DELETE FROM piezometrocuerdas WHERE id_piezometro = ?"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idpiezometro,))
            conn.commit()
            if cur.rowcount > 0:
                return True
            else:
                return False
        except Exception as e:
            print("Error al eliminar piezómetro: " + str(e))
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlEliminarPiezometroManual(idpiezometro):
        conn = None
        sql = """DELETE FROM piezometros WHERE id_piezometro = ?"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idpiezometro,))
            conn.commit()
            if cur.rowcount > 0:
                return True
            else:
                return False
        except Exception as e:
            print("Error al eliminar piezómetro: " + str(e))
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    # obtener fecha mini y maximo de los piezometros cuerda
    @staticmethod
    def mdlObtenerFechaMinMaxCuerda(proyectoid):
        conn = None
        sql = """SELECT MIN(pd.fecha_cuerda) AS min_fecha, MAX(pd.fecha_cuerda) AS max_fecha FROM piezometrocuerda_detalle pd INNER JOIN piezometrocuerdas p 
        ON pd.id_piezometro = p.id_piezometro WHERE p.id_proyecto = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyectoid,))
            row = cur.fetchone()
            if row:
                return tuple(row)
            else:
                return None
        except Exception as e:
            print("Error al obtener fechas min-max: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # obtener fecha mini y maximo de los piezometros manuales
    @staticmethod
    def mdlObtenerFechaMinMaxPiezomanual(proyectoid):
        conn = None
        sql = """SELECT MIN(pd.fecha_piezometro) AS min_fecha, MAX(pd.fecha_piezometro) AS max_fecha FROM piezometro_detalle pd INNER JOIN piezometros p 
        ON pd.id_piezometro = p.id_piezometro WHERE p.id_proyecto = ? AND p.estado_piezometro != 0;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyectoid,))
            row = cur.fetchone()
            if row:
                return tuple(row)
            else:
                return None
        except Exception as e:
            print("Error al obtener fechas min-max: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularPiezometrosCasaGrande(tabla, idcomponente, listapiezo, unidadmedidad):
        conn = None
        # Generar placeholders dinámicos
        placeholders = ', '.join(['?' for _ in listapiezo])
        # Ajuste en el orden de parametros para SQL Server y pyodbc
        params = [idcomponente] + listapiezo + [unidadmedidad, unidadmedidad]
        
        # Transformación T-SQL:
        # 1. JULIANDAY(fecha) - JULIANDAY(first) -> DATEDIFF(SECOND, first, fecha) / 86400.0
        # 2. LIMIT 1 -> TOP 1
        sql = f"""WITH cte_cota AS (
            SELECT it.id_instrumentacion, p.nombre_piezometro, d.fecha_piezometro, p.tipo_piezometro,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(d.fecha_piezometro) OVER (PARTITION BY p.nombre_piezometro ORDER BY d.fecha_piezometro), d.fecha_piezometro) AS FLOAT) / 86400.0 AS dias,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(d.fecha_piezometro) OVER (PARTITION BY p.nombre_piezometro ORDER BY d.fecha_piezometro), d.fecha_piezometro) AS FLOAT) / 3600.0 AS horas,
            d.medida_piezometro, p.stickup_piezometro, p.fundacion_piezometro,
            COALESCE(
                (SELECT TOP 1 c2.nivel_cota FROM cotas_piezometricas c2 WHERE c2.id_piezometro = d.id_piezometro 
                AND c2.tipo_piezometro = 'PVC' AND c2.fecha_cota <= d.fecha_piezometro ORDER BY c2.fecha_cota DESC),
                (SELECT TOP 1 c3.nivel_cota FROM cotas_piezometricas c3 WHERE c3.id_piezometro = d.id_piezometro
                AND c3.tipo_piezometro = 'PVC' ORDER BY c3.fecha_cota ASC)
            ) AS elevacion, it.tipo_equipo, it.id_equipo
            FROM piezometromanuales p INNER JOIN {tabla} d ON p.id_piezometro = d.id_piezometro
            INNER JOIN instrumentacion AS it ON it.id_equipo = p.id_piezometro
            INNER JOIN componentes AS co ON co.id_componente = it.id_componente
            WHERE d.estado_manual = 1 AND co.id_componente = ? AND it.id_instrumentacion IN ({placeholders})
            
        )
        SELECT id_instrumentacion, nombre_piezometro, fecha_piezometro, dias, horas,
            CASE
                WHEN tipo_piezometro = 1 THEN stickup_piezometro + elevacion - medida_piezometro
                ELSE medida_piezometro
            END AS nivel_piezometrico,
            COALESCE(medida_piezometro - LAG(medida_piezometro) OVER (PARTITION BY nombre_piezometro ORDER BY fecha_piezometro), 0) * ? AS incremental,
            CASE 
                WHEN tipo_piezometro = 1 THEN 
                    (stickup_piezometro + elevacion - medida_piezometro) -
                    (stickup_piezometro + FIRST_VALUE(elevacion) OVER (PARTITION BY nombre_piezometro ORDER BY fecha_piezometro) - 
                    FIRST_VALUE(medida_piezometro) OVER (PARTITION BY nombre_piezometro ORDER BY fecha_piezometro))
                ELSE 
                    medida_piezometro - FIRST_VALUE(medida_piezometro) OVER (PARTITION BY nombre_piezometro ORDER BY fecha_piezometro)
            END * ? AS acumulado, fundacion_piezometro, elevacion, tipo_equipo, id_equipo
        FROM cte_cota ORDER BY nombre_piezometro ASC, fecha_piezometro ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al obtener data piezo manual: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularPiezometrosFechasCasaGrande(tabla, idcomponente, listapiezo, unidadmedidad, fechaini, fechafin):
        conn = None
        placeholders = ', '.join(['?' for _ in listapiezo])
        params = [idcomponente] + listapiezo + [fechaini, fechafin, unidadmedidad, unidadmedidad]
        
        # Transformación T-SQL (DATEDIFF / TOP 1)
        sql = f"""WITH cte_cota AS (
            SELECT it.id_instrumentacion, p.nombre_piezometro, d.fecha_piezometro, p.tipo_piezometro,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(d.fecha_piezometro) OVER (PARTITION BY p.nombre_piezometro ORDER BY d.fecha_piezometro), d.fecha_piezometro) AS FLOAT) / 86400.0 AS dias,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(d.fecha_piezometro) OVER (PARTITION BY p.nombre_piezometro ORDER BY d.fecha_piezometro), d.fecha_piezometro) AS FLOAT) / 3600.0 AS horas,
            d.medida_piezometro, p.stickup_piezometro, p.fundacion_piezometro,
            COALESCE(
                (SELECT TOP 1 c2.nivel_cota FROM cotas_piezometricas c2 WHERE c2.id_piezometro = d.id_piezometro 
                AND c2.tipo_piezometro = 'PVC' AND c2.fecha_cota <= d.fecha_piezometro ORDER BY c2.fecha_cota DESC),
                (SELECT TOP 1 c3.nivel_cota FROM cotas_piezometricas c3 WHERE c3.id_piezometro = d.id_piezometro
                AND c3.tipo_piezometro = 'PVC' ORDER BY c3.fecha_cota ASC)
            ) AS elevacion, it.tipo_equipo, it.id_equipo
            FROM piezometromanuales p INNER JOIN {tabla} d ON p.id_piezometro = d.id_piezometro
            INNER JOIN instrumentacion AS it ON it.id_equipo = p.id_piezometro
            INNER JOIN componentes AS co ON co.id_componente = it.id_componente
            WHERE d.estado_manual = 1 AND co.id_componente = ? AND it.id_instrumentacion IN ({placeholders})
            AND d.fecha_piezometro BETWEEN ? AND ?
        )
        SELECT id_instrumentacion, nombre_piezometro, fecha_piezometro, dias, horas,
            CASE
                WHEN tipo_piezometro = 1 THEN stickup_piezometro + elevacion - medida_piezometro
                ELSE medida_piezometro
            END AS nivel_piezometrico,
            COALESCE(medida_piezometro - LAG(medida_piezometro) OVER (PARTITION BY nombre_piezometro ORDER BY fecha_piezometro), 0) * ? AS incremental,
            CASE 
                WHEN tipo_piezometro = 1 THEN 
                    (stickup_piezometro + elevacion - medida_piezometro) -
                    (stickup_piezometro + FIRST_VALUE(elevacion) OVER (PARTITION BY nombre_piezometro ORDER BY fecha_piezometro) - 
                    FIRST_VALUE(medida_piezometro) OVER (PARTITION BY nombre_piezometro ORDER BY fecha_piezometro))
                ELSE 
                    medida_piezometro - FIRST_VALUE(medida_piezometro) OVER (PARTITION BY nombre_piezometro ORDER BY fecha_piezometro)
            END * ? AS acumulado, fundacion_piezometro, elevacion, tipo_equipo, id_equipo
        FROM cte_cota ORDER BY nombre_piezometro ASC, fecha_piezometro ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al obtener data piezo manual: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerFormulaPiezometroCuerda(idpiezometro):
        conn = None
        sql = f"""SELECT p.id_formula, f.sentencia FROM piezometrocuerdas p INNER JOIN formulas_piezometros f
        ON p.id_formula = f.id_formula WHERE p.id_piezometro = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idpiezometro,))
            results = cur.fetchone()
            if results:
                return tuple(results)
            else:
                return [0, None]
        except Exception as e:
            print("Error al obtener formula cuerda:", e)
            return [0, None]
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularPiezometrosCuerda(tabla, idcomponente, listapiezo, unidadmedida):
        conn = None
        
        # --- CORRECCIÓN DE SEGURIDAD (Aplicar también aquí por si acaso) ---
        if not isinstance(listapiezo, list):
            if isinstance(listapiezo, tuple):
                listapiezo = list(listapiezo)
            else:
                listapiezo = [listapiezo]
        # -------------------------------

        # Generar placeholders para la lista
        placeholders = ', '.join(['?' for _ in listapiezo])
        
        params = [unidadmedida, unidadmedida, idcomponente] + listapiezo
        
        sql = f"""SELECT t.id_instrumentacion, pzc.nombre_piezometro, pzcd.fecha_cuerda,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(pzcd.fecha_cuerda) OVER (PARTITION BY pzc.nombre_piezometro ORDER BY pzcd.fecha_cuerda), pzcd.fecha_cuerda) AS FLOAT) / 86400.0 AS dias,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(pzcd.fecha_cuerda) OVER (PARTITION BY pzc.nombre_piezometro ORDER BY pzcd.fecha_cuerda), pzcd.fecha_cuerda) AS FLOAT) / 3600.0 AS horas,
            pzcd.frecuencia_cuerda, pzcd.temperatura_cuerda, pzcd.presion_barometrica,
            CASE
                WHEN pzc.tipo_piezometro = 1 THEN pzc.elevacion_piezometro + pzcd.medida_calculada
                ELSE pzcd.medida_calculada
            END AS nivel_agua,
            COALESCE(pzcd.medida_calculada - LAG(pzcd.medida_calculada) OVER (PARTITION BY pzc.nombre_piezometro ORDER BY pzcd.fecha_cuerda), 0) * ? AS incremental,
            CASE 
                WHEN pzc.tipo_piezometro = 1 THEN pzcd.medida_calculada
                ELSE pzcd.medida_calculada - pzc.elevacion_piezometro
            END * ? AS acumulado, pzc.fundacion_piezometro,
			COALESCE(
				(SELECT TOP 1 c2.nivel_cota FROM cotas_piezometricas c2 WHERE c2.id_piezometro = pzc.id_piezometro 
				   AND c2.tipo_piezometro = 'PCV' AND c2.fecha_cota <= pzcd.fecha_cuerda ORDER BY c2.fecha_cota DESC),
				(SELECT TOP 1 c3.nivel_cota FROM cotas_piezometricas c3 WHERE c3.id_piezometro = pzc.id_piezometro 
				   AND c3.tipo_piezometro = 'PCV' ORDER BY c3.fecha_cota ASC)
			) AS superficie, t.tipo_equipo, pzc.unidad_lectura
        FROM piezometrocuerdas pzc INNER JOIN {tabla} pzcd ON pzc.id_piezometro = pzcd.id_piezometro 
        INNER JOIN instrumentacion t ON pzc.id_piezometro = t.id_equipo
        INNER JOIN componentes c ON t.id_componente = c.id_componente
        WHERE pzcd.estado_cuerda = 1 AND c.id_componente = ? AND t.id_instrumentacion IN ({placeholders})
        ORDER BY pzc.nombre_piezometro ASC, pzcd.fecha_cuerda ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al obtener data piezo cuerda: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
                
    @staticmethod
    def mdlCalcularPiezometrosCuerdaFormula(tabla, idcomponente, idinstrumento, unidadmedida, formula):
        conn = None
        params = (idcomponente, idinstrumento, unidadmedida, unidadmedida)
        
        # Se asume que 'formula' es una cadena segura o validada previamente
        # Transformación T-SQL: JULIANDAY -> DATEDIFF, LIMIT -> TOP
        sql = f"""WITH piezometros AS (SELECT t.id_instrumentacion, p.nombre_piezometro, d.fecha_cuerda,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(d.fecha_cuerda) OVER (PARTITION BY p.nombre_piezometro ORDER BY d.fecha_cuerda), d.fecha_cuerda) AS FLOAT) / 86400.0 AS dias,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(d.fecha_cuerda) OVER (PARTITION BY p.nombre_piezometro ORDER BY d.fecha_cuerda), d.fecha_cuerda) AS FLOAT) / 3600.0 AS horas,
                d.frecuencia_cuerda, d.temperatura_cuerda, ({formula}) AS presion_barometrica,
                p.fundacion_piezometro, p.elevacion_piezometro AS instalacion,
                COALESCE(
                    (SELECT TOP 1 c2.nivel_cota FROM cotas_piezometricas c2 WHERE c2.id_piezometro = p.id_piezometro 
                    AND c2.tipo_piezometro = 'PCV' AND c2.fecha_cota <= d.fecha_cuerda ORDER BY c2.fecha_cota DESC),
                    (SELECT TOP 1 c3.nivel_cota FROM cotas_piezometricas c3 WHERE c3.id_piezometro = p.id_piezometro 
                    AND c3.tipo_piezometro = 'PCV' ORDER BY c3.fecha_cota ASC)
                ) AS superficie, t.tipo_equipo, p.unidad_lectura, p.factor_conversion
            FROM piezometrocuerdas p INNER JOIN {tabla} d ON p.id_piezometro = d.id_piezometro 
            INNER JOIN instrumentacion t ON p.id_piezometro = t.id_equipo
            INNER JOIN componentes c ON t.id_componente = c.id_componente
            WHERE d.estado_cuerda = 1 AND c.id_componente = ? AND t.id_instrumentacion = ?
        )
        SELECT id_instrumentacion, nombre_piezometro, fecha_cuerda, dias, horas, frecuencia_cuerda, temperatura_cuerda,
            presion_barometrica,
            (instalacion + (presion_barometrica * factor_conversion)) AS nivel_agua,
            (COALESCE(presion_barometrica - LAG(presion_barometrica) OVER (PARTITION BY nombre_piezometro ORDER BY fecha_cuerda), 0) * factor_conversion) * ? AS incremental,
            (presion_barometrica * factor_conversion) * ? AS acumulado, fundacion_piezometro,
            superficie, tipo_equipo, unidad_lectura
        FROM piezometros ORDER BY nombre_piezometro ASC, fecha_cuerda ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al obtener data piezo cuerda formula: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularPiezometrosFechasCuerda(tabla, idcomponente, listapiezo, unidadmedida, fechaini, fechafin):
        conn = None
        
        # --- CORRECCIÓN DE SEGURIDAD ---
        # Validar si listapiezo llega como string o entero y convertirlo a lista
        if not isinstance(listapiezo, list):
            if isinstance(listapiezo, tuple):
                listapiezo = list(listapiezo)
            else:
                # Si es un string o int simple, lo metemos en una lista
                listapiezo = [listapiezo]
        # -------------------------------

        # Generar placeholders para IN (?)
        placeholders = ', '.join(['?' for _ in listapiezo])
        
        # Ahora listapiezo es una lista, la concatenación funcionará: list + list + list
        params = [unidadmedida, unidadmedida, idcomponente] + listapiezo + [fechaini, fechafin]
        
        sql = f"""SELECT t.id_instrumentacion, pzc.nombre_piezometro, pzcd.fecha_cuerda,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(pzcd.fecha_cuerda) OVER (PARTITION BY pzc.nombre_piezometro ORDER BY pzcd.fecha_cuerda), pzcd.fecha_cuerda) AS FLOAT) / 86400.0 AS dias,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(pzcd.fecha_cuerda) OVER (PARTITION BY pzc.nombre_piezometro ORDER BY pzcd.fecha_cuerda), pzcd.fecha_cuerda) AS FLOAT) / 3600.0 AS horas,
            pzcd.frecuencia_cuerda, pzcd.temperatura_cuerda, pzcd.presion_barometrica,
            CASE
                WHEN pzc.tipo_piezometro = 1 THEN pzc.elevacion_piezometro + pzcd.medida_calculada
                ELSE pzcd.medida_calculada
            END AS nivel_agua,
            COALESCE(pzcd.medida_calculada - LAG(pzcd.medida_calculada) OVER (PARTITION BY pzc.nombre_piezometro ORDER BY pzcd.fecha_cuerda), 0) * ? AS incremental,
            CASE 
                WHEN pzc.tipo_piezometro = 1 THEN pzcd.medida_calculada
                ELSE pzcd.medida_calculada - pzc.elevacion_piezometro
            END * ? AS acumulado, pzc.fundacion_piezometro,
			COALESCE(
				(SELECT TOP 1 c2.nivel_cota FROM cotas_piezometricas c2 WHERE c2.id_piezometro = pzc.id_piezometro 
				   AND c2.tipo_piezometro = 'PCV' AND c2.fecha_cota <= pzcd.fecha_cuerda ORDER BY c2.fecha_cota DESC),
				(SELECT TOP 1 c3.nivel_cota FROM cotas_piezometricas c3 WHERE c3.id_piezometro = pzc.id_piezometro 
				   AND c3.tipo_piezometro = 'PCV' ORDER BY c3.fecha_cota ASC)
			) AS superficie, t.tipo_equipo, pzc.unidad_lectura
        FROM piezometrocuerdas pzc INNER JOIN {tabla} pzcd ON pzc.id_piezometro = pzcd.id_piezometro 
        INNER JOIN instrumentacion t ON pzc.id_piezometro = t.id_equipo
        INNER JOIN componentes c ON t.id_componente = c.id_componente
        WHERE pzcd.estado_cuerda = 1 AND c.id_componente = ? AND t.id_instrumentacion IN ({placeholders}) AND pzcd.fecha_cuerda BETWEEN ? AND ?
        ORDER BY pzc.nombre_piezometro ASC, pzcd.fecha_cuerda ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al obtener data piezo cuerda: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularPiezometrosFechasCuerdaFormula(tabla, idcomponente, idinstrumento, unidadmedida, fechaini, fechafin, formula):
        conn = None
        params = (idcomponente, idinstrumento, fechaini, fechafin, unidadmedida, unidadmedida)
        
        # Transformación T-SQL: JULIANDAY -> DATEDIFF, LIMIT -> TOP
        # Nota: La 'formula' se inyecta directamente. Asegurarse que la fórmula use sintaxis T-SQL (ej. POWER en vez de POW)
        sql = f"""WITH piezometros AS (SELECT t.id_instrumentacion, p.nombre_piezometro, d.fecha_cuerda,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(d.fecha_cuerda) OVER (PARTITION BY p.nombre_piezometro ORDER BY d.fecha_cuerda), d.fecha_cuerda) AS FLOAT) / 86400.0 AS dias,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(d.fecha_cuerda) OVER (PARTITION BY p.nombre_piezometro ORDER BY d.fecha_cuerda), d.fecha_cuerda) AS FLOAT) / 3600.0 AS horas,
                d.frecuencia_cuerda, d.temperatura_cuerda, ({formula}) AS presion_barometrica,
                p.fundacion_piezometro, p.elevacion_piezometro AS instalacion,
                COALESCE(
                    (SELECT TOP 1 c2.nivel_cota FROM cotas_piezometricas c2 WHERE c2.id_piezometro = p.id_piezometro 
                    AND c2.tipo_piezometro = 'PCV' AND c2.fecha_cota <= d.fecha_cuerda ORDER BY c2.fecha_cota DESC),
                    (SELECT TOP 1 c3.nivel_cota FROM cotas_piezometricas c3 WHERE c3.id_piezometro = p.id_piezometro 
                    AND c3.tipo_piezometro = 'PCV' ORDER BY c3.fecha_cota ASC)
                ) AS superficie, t.tipo_equipo, p.unidad_lectura, p.factor_conversion
            FROM piezometrocuerdas p INNER JOIN {tabla} d ON p.id_piezometro = d.id_piezometro 
            INNER JOIN instrumentacion t ON p.id_piezometro = t.id_equipo
            INNER JOIN componentes c ON t.id_componente = c.id_componente
            WHERE d.estado_cuerda = 1 AND c.id_componente = ? AND t.id_instrumentacion = ? AND d.fecha_cuerda BETWEEN ? AND ?
        )
        SELECT id_instrumentacion, nombre_piezometro, fecha_cuerda, dias, horas, frecuencia_cuerda, temperatura_cuerda,
            presion_barometrica,
            (instalacion + (presion_barometrica * factor_conversion)) AS nivel_agua,
            (COALESCE(presion_barometrica - LAG(presion_barometrica) OVER (PARTITION BY nombre_piezometro ORDER BY fecha_cuerda), 0) * factor_conversion) * ? AS incremental,
            (presion_barometrica * factor_conversion) * ? AS acumulado, fundacion_piezometro,
            superficie, tipo_equipo, unidad_lectura
        FROM piezometros ORDER BY nombre_piezometro ASC, fecha_cuerda ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al obtener data piezo cuerda fechas formula: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # ACTUALIZAR LECTURA PIEZOMETRO CUERDA DESDE TABLA      
    @staticmethod
    def mdlActualizarLecturaPiezometroCuerda(tabla, datos, idproyecto, username, nombres):
        conn = None
        sql = f"""UPDATE {tabla} SET fecha_cuerda = ?, frecuencia_cuerda = ?, temperatura_cuerda = ?, presion_barometrica = ?, 
        medida_calculada = ?, observacion_cuerda = ? WHERE id_cuerda = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            
            # guardar en historial
            query_select = f"""SELECT fecha_cuerda, frecuencia_cuerda, temperatura_cuerda, presion_barometrica, medida_calculada,
            observacion_cuerda, id_cuerda FROM {tabla} WHERE id_cuerda = ?;"""
            cur.execute(query_select, (datos[-1],))
            datos_anteriores = cur.fetchone()
            
            if datos_anteriores:
                # Convertir Row a tupla para string representation limpia
                datos_anteriores_tuple = tuple(datos_anteriores)
                fecha_cambio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                accion = "update"
                cambios = f"Antiguos: {datos_anteriores_tuple}, Nuevos: {datos}"
                query_historial = """INSERT INTO historial (idproyecto, fecha, accion, tabla, cambios, usuario, nombres)
                VALUES (?, ?, ?, ?, ?, ?, ?);"""
                cur.execute(query_historial, (idproyecto, fecha_cambio, accion, tabla, cambios, username, nombres))
            
            # actualizar cuerda
            cur.execute(sql, datos)
            conn.commit()
            return True
        except Exception as e:
            print("Error al editar lectura cuerda vibrante: " + str(e))
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCambiarEstadoLecturaPiezoCuerda(tabla, iddetalle):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            query_update = f"""UPDATE {tabla} SET estado_cuerda = CASE estado_cuerda WHEN 1 THEN 0 ELSE 1 END
            WHERE id_cuerda = ?;"""
            cursor.execute(query_update, (iddetalle,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error al cambiar estado lectura cuerda: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCambiarEstadoLecturaPiezoCuerdaBloque(tabla, listacodigos):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            placeholders = ', '.join(['?' for _ in listacodigos])
            query_update = f"""UPDATE {tabla} SET estado_cuerda = CASE estado_cuerda WHEN 1 THEN 0 ELSE 1 END
            WHERE id_cuerda IN ({placeholders});"""
            cursor.execute(query_update, listacodigos)
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error al cambiar estado de lecturas cuerda: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlEliminarLecturaPiezoCuerda(tabla, iddetalle, idproyecto, username, nombres):
        conn = None
        sql = f"""DELETE FROM {tabla} WHERE id_cuerda = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            
            # guardar en historial
            query_select = f"""SELECT * FROM {tabla} WHERE id_cuerda = ?;"""
            cur.execute(query_select, (iddetalle,))
            datos_anteriores = cur.fetchone()
            
            if datos_anteriores:
                datos_anteriores_tuple = tuple(datos_anteriores)
                fecha_cambio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                accion = "delete"
                cambios = f"Datos: {datos_anteriores_tuple}"
                query_historial = """INSERT INTO historial (idproyecto, fecha, accion, tabla, cambios, usuario, nombres)
                VALUES (?, ?, ?, ?, ?, ?, ?);"""
                cur.execute(query_historial, (idproyecto, fecha_cambio, accion, tabla, cambios, username, nombres))
            
            # eliminar lectura
            cur.execute(sql, (iddetalle,))
            conn.commit()
            if cur.rowcount > 0:
                return True
            else:
                return False
        except Exception as e:
            print("Error al eliminar lectura cuerda: " + str(e))
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlEliminarLecturasBloquePiezoCuerda(tabla, iddetalles, idproyecto, username, nombres):
        conn = None
        placeholders = ', '.join(['?' for _ in iddetalles])
        query = f"""DELETE FROM {tabla} WHERE id_cuerda IN ({placeholders});"""
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            
            # guardar en historial
            query_select = f"""SELECT * FROM {tabla} WHERE id_cuerda IN ({placeholders});"""
            cursor.execute(query_select, iddetalles)
            rows = cursor.fetchall()
            # Convertir a lista de tuplas para el log
            datos_anteriores = [tuple(row) for row in rows]
            
            if datos_anteriores:
                fecha_cambio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                accion = "delete"
                cambios = f"Datos: {datos_anteriores}"
                query_historial = """INSERT INTO historial (idproyecto, fecha, accion, tabla, cambios, usuario, nombres)
                VALUES (?, ?, ?, ?, ?, ?, ?);"""
                cursor.execute(query_historial, (idproyecto, fecha_cambio, accion, tabla, cambios, username, nombres))
            
            # eliminar lecturas piezometro
            cursor.execute(query, iddetalles)
            conn.commit()
            if cursor.rowcount > 0:
                return True
            else:
                return False
        except Exception as e:
            print(f"Error al eliminar lecturas de cuerda: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlActualizarCotaPiezometrica(idproyecto, idcota, datofecha, cotamedida, username, nombres):
        conn = None
        sql = f"""UPDATE cotas_piezometricas SET fecha_cota = ?, nivel_cota = ? WHERE id_cota = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            
            # guardar en historial
            query_select = f"""SELECT * FROM cotas_piezometricas WHERE id_cota = ?;"""
            cur.execute(query_select, (idcota,))
            datos_anteriores = cur.fetchone()
            
            if datos_anteriores:
                datos_anteriores_tuple = tuple(datos_anteriores)
                fecha_cambio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                accion = "update"
                cambios = f"Antiguos: {datos_anteriores_tuple}, Nuevos: {[datofecha, cotamedida, idcota]}"
                query_historial = """INSERT INTO historial (idproyecto, fecha, accion, tabla, cambios, usuario, nombres)
                VALUES (?, ?, ?, ?, ?, ?, ?);"""
                tabla = "cotas_piezometricas"
                cur.execute(query_historial, (idproyecto, fecha_cambio, accion, tabla, cambios, username, nombres))
            
            # actualizar cota
            cur.execute(sql, (datofecha, cotamedida, idcota))
            conn.commit()
            return True
        except Exception as e:
            print("Error al editar cota piezometrica: " + str(e))
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    # ACTUALIZAR LECTURA PIEZOMETRO MANUAL DESDE TABLA      
    @staticmethod
    def mdlActualizarLecturaPiezometroManual(tabla, datos, idproyecto, username, nombres):
        conn = None
        sql = f"""UPDATE {tabla} SET fecha_piezometro = ?, medida_piezometro = ?, observacion_detalle = ? WHERE id_detalle = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            
            # guardar en historial
            query_select = f"""SELECT fecha_piezometro, medida_piezometro, observacion_detalle, id_detalle FROM {tabla} WHERE id_detalle = ?;"""
            cur.execute(query_select, (datos[-1],))
            datos_anteriores = cur.fetchone()
            
            if datos_anteriores:
                datos_anteriores_tuple = tuple(datos_anteriores)
                fecha_cambio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                accion = "update"
                cambios = f"Antiguos: {datos_anteriores_tuple}, Nuevos: {datos}"
                query_historial = """INSERT INTO historial (idproyecto, fecha, accion, tabla, cambios, usuario, nombres)
                VALUES (?, ?, ?, ?, ?, ?, ?);"""
                cur.execute(query_historial, (idproyecto, fecha_cambio, accion, tabla, cambios, username, nombres))
            
            # actualizar cuerda
            cur.execute(sql, datos)
            conn.commit()
            return True
        except Exception as e:
            print("Error al editar lectura casagrande: " + str(e))
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCambiarEstadoLecturaPiezoManual(tabla, iddetalle):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            query_update = f"""UPDATE {tabla} SET estado_manual = CASE estado_manual WHEN 1 THEN 0 ELSE 1 END
            WHERE id_detalle = ?;"""
            cursor.execute(query_update, (iddetalle,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error al cambiar estado lectura casagrande: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCambiarEstadoLecturaPiezoManualBloque(tabla, listacodigos):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            placeholders = ','.join(['?'] * len(listacodigos))
            query_update = f"""UPDATE {tabla} SET estado_manual = CASE estado_manual WHEN 1 THEN 0 ELSE 1 END
            WHERE id_detalle IN ({placeholders});"""
            cursor.execute(query_update, listacodigos)
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error al cambiar estado lecturas casagrande: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlEliminarLecturaPiezoManual(tabla, iddetalle, idproyecto, username, nombres):
        conn = None
        sql = f"""DELETE FROM {tabla} WHERE id_detalle = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            
            # guardar en historial
            query_select = f"""SELECT * FROM {tabla} WHERE id_detalle = ?;"""
            cur.execute(query_select, (iddetalle,))
            datos_anteriores = cur.fetchone()
            
            if datos_anteriores:
                datos_anteriores_tuple = tuple(datos_anteriores)
                fecha_cambio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                accion = "delete"
                cambios = f"Datos: {datos_anteriores_tuple}"
                query_historial = """INSERT INTO historial (idproyecto, fecha, accion, tabla, cambios, usuario, nombres)
                VALUES (?, ?, ?, ?, ?, ?, ?);"""
                cur.execute(query_historial, (idproyecto, fecha_cambio, accion, tabla, cambios, username, nombres))
            
            # eliminar lectura
            cur.execute(sql, (iddetalle,))
            conn.commit()
            if cur.rowcount > 0:
                return True
            else:
                return False
        except Exception as e:
            print("Error al eliminar lectura casagrande: " + str(e))
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlEliminarLecturasBloquePiezoManual(tabla, iddetalles, idproyecto, username, nombres):
        conn = None
        placeholders = ', '.join(['?' for _ in iddetalles])
        query = f"""DELETE FROM {tabla} WHERE id_detalle IN ({placeholders});"""
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            
            # guardar en historial
            query_select = f"""SELECT * FROM {tabla} WHERE id_detalle IN ({placeholders});"""
            cursor.execute(query_select, iddetalles)
            rows = cursor.fetchall()
            datos_anteriores = [tuple(row) for row in rows]
            
            if datos_anteriores:
                fecha_cambio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                accion = "delete"
                cambios = f"Datos: {datos_anteriores}"
                query_historial = """INSERT INTO historial (idproyecto, fecha, accion, tabla, cambios, usuario, nombres)
                VALUES (?, ?, ?, ?, ?, ?, ?);"""
                cursor.execute(query_historial, (idproyecto, fecha_cambio, accion, tabla, cambios, username, nombres))
            
            # eliminar lecturas piezometro
            cursor.execute(query, iddetalles)
            conn.commit()
            if cursor.rowcount > 0:
                return True
            else:
                return False
        except Exception as e:
            print(f"Error al eliminar lecturas casagrande: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
                
    # LISTAR LOS PIEZOMETROS DE CUERDA VIBRANTE POR PROYECTO    
    @staticmethod
    def mdlListarPiezometrosCuerda(proyecto):
        conn = None
        sql = """SELECT * FROM piezometrocuerdas WHERE id_proyecto = ? AND estado_piezometro = 1;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyecto,))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al consultar piezometros: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
                
    # LISTAR LOS PIEZOMETROS MANUALES POR PROYECTO    
    @staticmethod
    def mdlListarPiezometrosManuales(proyecto):
        conn = None
        sql = """SELECT * FROM piezometromanuales WHERE id_proyecto = ? AND estado_piezometro = 1;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyecto,))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al consultar piezometros: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCambiarComponentePiezometrosCuerda(idcomponente, nuevocomponente):
        conn = None
        sql = """UPDATE instrumentacion SET id_componente = ? WHERE id_componente = ? AND tipo_equipo = 'PIEZOMETROCUERDA';"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # guardar en historial y retornar datos
            query_select = """SELECT * FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'PIEZOMETROCUERDA';"""
            cur.execute(query_select, (idcomponente,))
            rows = cur.fetchall()
            dataincli = [tuple(row) for row in rows]
            
            if dataincli:
                cur.execute(sql, (nuevocomponente, idcomponente))
                conn.commit()
                return dataincli
            else:
                return None
        except Exception as e:
            print("Error al cambiar componente cuerdas: " + str(e))
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlEliminarPiezometrosCuerda(idcomponente):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # guardar en historial y retornar datos
            query_select = """SELECT * FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'PIEZOMETROCUERDA';"""
            cursor.execute(query_select, (idcomponente,))
            rows = cursor.fetchall()
            dataincli = [tuple(row) for row in rows]
            
            if dataincli:
                query = """DELETE FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'PIEZOMETROCUERDA';"""
                cursor.execute(query, (idcomponente,))
                conn.commit()
                if cursor.rowcount > 0:
                    return dataincli
                else:
                    return None
            else:
                return None
        except Exception as e:
            print(f"Error al eliminar cuerdas: {e}")
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlEliminarDataPiezometrosCuerda(tabla, cuerdas):
        conn = None
        placeholders = ','.join(['?' for _ in cuerdas])
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # Eliminar data detalle
            query_delete = f"""DELETE FROM {tabla} WHERE id_piezometro IN ({placeholders});"""
            cursor.execute(query_delete, cuerdas)
            
            # Verificar si se borró algo o si simplemente se debe proceder (lógica original implicaba que si no hay data, no se borra la cabecera)
            # Asumimos que se borran las cabeceras si se borran detalles o si se confirma la intención.
            # Sin embargo, la lógica original tiene `if rows_data > 0`. Respetamos esa lógica.
            if cursor.rowcount > 0:
                query_delete_cuerdas = f"DELETE FROM piezometrocuerdas WHERE id_piezometro IN ({placeholders});"
                cursor.execute(query_delete_cuerdas, cuerdas)
                rows_cuerdas = cursor.rowcount
                conn.commit()
                return rows_cuerdas > 0
            else:
                # Si no hay detalles, la lógica original hace rollback y retorna False.
                conn.rollback()
                return False
        except Exception as e:
            print(f"Error al eliminar data cuerdas: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerInfoPiezometroCuerda(idinstrumento):
        conn = None
        sql = """SELECT p.* FROM piezometrocuerdas p INNER JOIN instrumentacion i ON p.id_piezometro = i.id_equipo WHERE i.id_instrumentacion = ?;"""
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
            print("Error al consultar info cuerda: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
                
    @staticmethod
    def mdlEliminarCuerdaVibrante(idinstrumento):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # obtener info para eliminar data
            query_select = """SELECT * FROM instrumentacion WHERE id_instrumentacion = ? AND tipo_equipo = 'PIEZOMETROCUERDA';"""
            cursor.execute(query_select, (idinstrumento,))
            datapiezo = cursor.fetchone()
            
            if datapiezo:
                # Convertir a tupla antes de cualquier operación si es necesario devolverlo
                result_tuple = tuple(datapiezo)
                query = """DELETE FROM instrumentacion WHERE id_instrumentacion = ? AND tipo_equipo = 'PIEZOMETROCUERDA';"""
                cursor.execute(query, (idinstrumento,))
                conn.commit()
                if cursor.rowcount > 0:
                    return result_tuple
                else:
                    return None
            else:
                return None
        except Exception as e:
            print(f"Error al eliminar cuerda vibrante: {e}")
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlEliminarCuerdaVibranteData(tabla, idpiezometro):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # eliminar data
            query_delete = f"""DELETE FROM {tabla} WHERE id_piezometro = ?;"""
            cursor.execute(query_delete, (idpiezometro,))
            rows_data = cursor.rowcount
            
            if rows_data > 0:
                query_delete_cuerdas = "DELETE FROM piezometrocuerdas WHERE id_piezometro = ?;"
                cursor.execute(query_delete_cuerdas, (idpiezometro,))
                rows_cuerdas = cursor.rowcount
                conn.commit()
                return rows_cuerdas > 0
            else:
                conn.rollback()
                return False
        except Exception as e:
            print(f"Error al eliminar data cuerda vibrante: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCambiarComponentePiezometrosManuales(idcomponente, nuevocomponente):
        conn = None
        sql = """UPDATE instrumentacion SET id_componente = ? WHERE id_componente = ? AND tipo_equipo = 'PIEZOMETROMANUAL';"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # guardar info
            query_select = """SELECT * FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'PIEZOMETROMANUAL';"""
            cur.execute(query_select, (idcomponente,))
            rows = cur.fetchall()
            dataincli = [tuple(row) for row in rows]
            
            if dataincli:
                cur.execute(sql, (nuevocomponente, idcomponente))
                conn.commit()
                return dataincli
            else:
                return None
        except Exception as e:
            print("Error al cambiar componente casagrandes: " + str(e))
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlEliminarPiezometrosManuales(idcomponente):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # guardar en historial
            query_select = """SELECT * FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'PIEZOMETROMANUAL';"""
            cursor.execute(query_select, (idcomponente,))
            rows = cursor.fetchall()
            dataincli = [tuple(row) for row in rows]
            
            if dataincli:
                query = """DELETE FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'PIEZOMETROMANUAL';"""
                cursor.execute(query, (idcomponente,))
                conn.commit()
                if cursor.rowcount > 0:
                    return dataincli
                else:
                    return None
            else:
                return None
        except Exception as e:
            print(f"Error al eliminar casagrandes: {e}")
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlEliminarDataPiezometrosManuales(tabla, manuales):
        conn = None
        placeholders = ', '.join(['?' for _ in manuales])
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # eliminar data
            query_delete = f"""DELETE FROM {tabla} WHERE id_piezometro IN ({placeholders});"""
            cursor.execute(query_delete, manuales)
            rows_data = cursor.rowcount
            
            if rows_data > 0:
                query_delete_cuerdas = f"DELETE FROM piezometromanuales WHERE id_piezometro IN ({placeholders});"
                cursor.execute(query_delete_cuerdas, manuales)
                rows_cuerdas = cursor.rowcount
                conn.commit()
                return rows_cuerdas > 0
            else:
                conn.rollback()
                return False
        except Exception as e:
            print(f"Error al eliminar data casagrandes: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerInfoPiezometroManual(idinstrumento):
        conn = None
        sql = """SELECT p.* FROM piezometromanuales p INNER JOIN instrumentacion i ON p.id_piezometro = i.id_equipo WHERE i.id_instrumentacion = ?;"""
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
            print("Error al consultar info casagrande: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlEliminarManualPiezometro(idinstrumento):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # obtener info para eliminar data
            query_select = """SELECT * FROM instrumentacion WHERE id_instrumentacion = ? AND tipo_equipo = 'PIEZOMETROMANUAL';"""
            cursor.execute(query_select, (idinstrumento,))
            datapiezo = cursor.fetchone()
            
            if datapiezo:
                result_tuple = tuple(datapiezo)
                query = """DELETE FROM instrumentacion WHERE id_instrumentacion = ? AND tipo_equipo = 'PIEZOMETROMANUAL';"""
                cursor.execute(query, (idinstrumento,))
                conn.commit()
                if cursor.rowcount > 0:
                    return result_tuple
                else:
                    return None
            else:
                return None
        except Exception as e:
            print(f"Error al eliminar casagrande: {e}")
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlEliminarPiezometroManualData(tabla, idpiezometro):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # eliminar data
            query_delete = f"""DELETE FROM {tabla} WHERE id_piezometro = ?;"""
            cursor.execute(query_delete, (idpiezometro,))
            rows_data = cursor.rowcount
            
            if rows_data > 0:
                query_delete_cuerdas = "DELETE FROM piezometromanuales WHERE id_piezometro = ?;"
                cursor.execute(query_delete_cuerdas, (idpiezometro,))
                rows_cuerdas = cursor.rowcount
                conn.commit()
                return rows_cuerdas > 0
            else:
                conn.rollback()
                return False
        except Exception as e:
            print(f"Error al eliminar data casagrande: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlListarFechasPiezometroCuerda(tabla, idcomponente, idinstrumento, proyectoid):
        conn = None
        sql = f"""SELECT d.fecha_cuerda FROM {tabla} d
        INNER JOIN piezometrocuerdas p ON d.id_piezometro = p.id_piezometro
		INNER JOIN instrumentacion i ON p.id_piezometro = i.id_equipo
		INNER JOIN componentes c ON i.id_componente = c.id_componente
        WHERE c.id_proyecto = ? AND i.id_instrumentacion = ? AND c.id_componente = ?
		ORDER BY d.fecha_cuerda;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyectoid, idinstrumento, idcomponente))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al consultar fechas cuerda: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlListarFechasPiezometroManual(tabla, idcomponente, idinstrumento, proyectoid):
        conn = None
        sql = f"""SELECT d.fecha_piezometro FROM {tabla} d
        INNER JOIN piezometromanuales p ON d.id_piezometro = p.id_piezometro
		INNER JOIN instrumentacion i ON p.id_piezometro = i.id_equipo
		INNER JOIN componentes c ON i.id_componente = c.id_componente
        WHERE c.id_proyecto = ? AND i.id_instrumentacion = ? AND c.id_componente = ?
		ORDER BY d.fecha_piezometro;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyectoid, idinstrumento, idcomponente))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al consultar fechas manual: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerResumenCuerdaReporte(idproyecto, idcomponente, fechaini, fechafin):
        conn = None
        # Consulta para obtener los IDs de los equipos filtrados
        filtro_sql = """
        SELECT id_equipo
        FROM instrumentacion
        WHERE tipo_equipo = 'PIEZOMETROCUERDA' AND id_componente = ? AND estado_instrumentacion=1
        """
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # Ejecutar la consulta de filtro
            cur.execute(filtro_sql, (idcomponente,))
            filtro_rows = cur.fetchall()

            # Si no hay equipos filtrados, retornar None
            if not filtro_rows:
                return None

            # Extraer los IDs de los equipos filtrados
            filtro_ids = [row[0] for row in filtro_rows]
            
            # Placeholders dinámicos para IN
            placeholders = ','.join(['?' for _ in filtro_ids])

            # Transpilación T-SQL:
            # 1. FORMAT en lugar de strftime. Se pasan fechaini/fechafin como params para evitar inyeccion
            # 2. LIMIT 1 -> TOP 1
            sql = f"""
            SELECT p.id_piezometro, p.nombre_piezometro, 
            FORMAT(CAST(? AS DATETIME), 'dd/MM/yyyy') AS fechaini,
            FORMAT(CAST(? AS DATETIME), 'dd/MM/yyyy') AS fechafin,
            COALESCE(
                (SELECT TOP 1 c2.nivel_cota
                FROM cotas_piezometricas c2
                WHERE c2.id_piezometro = d.id_piezometro
                AND c2.tipo_piezometro = 'PCV'
                AND c2.fecha_cota <= d.fecha_cuerda
                ORDER BY c2.fecha_cota DESC),
                (SELECT TOP 1 c3.nivel_cota
                FROM cotas_piezometricas c3
                WHERE c3.id_piezometro = d.id_piezometro
                AND c3.tipo_piezometro = 'PCV'
                ORDER BY c3.fecha_cota ASC)
            ) AS cota_terreno,
            CASE
                WHEN p.tipo_piezometro = 1 THEN p.elevacion_piezometro + d.medida_calculada
                ELSE d.medida_calculada
            END AS nivel_agua, 'Operativo' AS estado
            FROM piezometrocuerdas p
            INNER JOIN piezometrocuerda_detalle{idproyecto} d ON p.id_piezometro = d.id_piezometro
            WHERE p.id_proyecto = ? AND d.estado_cuerda = 1
            AND d.fecha_cuerda BETWEEN ? AND ?
            AND d.fecha_cuerda = (
                SELECT MAX(fecha_cuerda)
                FROM piezometrocuerda_detalle{idproyecto}
                WHERE id_piezometro = p.id_piezometro
                AND fecha_cuerda BETWEEN ? AND ?
            )
            AND p.id_piezometro IN ({placeholders})
            ORDER BY p.nombre_piezometro;
            """
            
            # Orden de parametros: 
            # 1. fechaini (Select)
            # 2. fechafin (Select)
            # 3. idproyecto (Where principal)
            # 4. fechaini (Between principal)
            # 5. fechafin (Between principal)
            # 6. fechaini (Between subquery)
            # 7. fechafin (Between subquery)
            # 8. *filtro_ids (IN clause)
            params = [fechaini, fechafin, idproyecto, fechaini, fechafin, fechaini, fechafin] + filtro_ids

            # Ejecutar la consulta principal
            cur.execute(sql, params)
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]

            if results:
                return results
            else:
                return None

        except Exception as e:
            print("Error al resumir piezometros: " + str(e))
            return None

        finally:
            if conn:
                conn.close()
                
    @staticmethod
    def mdlObtenerResumenCasagrandeReporte(idproyecto, idcomponente, fechaini, fechafin):
        conn = None
        filtro_sql = """SELECT id_equipo FROM instrumentacion
        WHERE tipo_equipo = 'PIEZOMETROMANUAL' AND id_componente = ? AND estado_instrumentacion=1;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            
            # Ejecutar la consulta de filtro
            cur.execute(filtro_sql, (idcomponente,))
            filtro_rows = cur.fetchall()
            
            # Si no hay piezómetros filtrados, retornar None
            if not filtro_rows:
                return None
            
            # Extraer los IDs de los piezómetros filtrados
            filtro_ids = [row[0] for row in filtro_rows]
            placeholders = ','.join(['?' for _ in filtro_ids])
            
            # Transpilación T-SQL:
            # 1. WITH CTE y ROW_NUMBER (Compatible)
            # 2. LIMIT 1 -> TOP 1
            # 3. strftime -> FORMAT (con parametros)
            sql = f"""
            WITH cte_cota AS (
                SELECT p.id_piezometro, p.nombre_piezometro, p.tipo_piezometro, d.fecha_piezometro, d.medida_piezometro, d.observacion_detalle,
                p.stickup_piezometro, p.elevacion_piezometro AS instalacion,
                COALESCE(
                    (SELECT TOP 1 c2.nivel_cota
                    FROM cotas_piezometricas c2
                    WHERE c2.id_piezometro = d.id_piezometro
                    AND c2.tipo_piezometro = 'PVC'
                    AND c2.fecha_cota <= d.fecha_piezometro
                    ORDER BY c2.fecha_cota DESC),
                    (SELECT TOP 1 c3.nivel_cota
                    FROM cotas_piezometricas c3
                    WHERE c3.id_piezometro = d.id_piezometro
                    AND c3.tipo_piezometro = 'PVC'
                    ORDER BY c3.fecha_cota ASC)
                ) AS elevacion,
                ROW_NUMBER() OVER (PARTITION BY p.id_piezometro ORDER BY d.fecha_piezometro DESC) AS row_num
                FROM piezometromanuales p INNER JOIN piezometromanual_detalle{idproyecto} d ON p.id_piezometro = d.id_piezometro
                WHERE p.id_proyecto = ? AND d.fecha_piezometro BETWEEN ? AND ? AND d.estado_manual = 1
                AND p.id_piezometro IN ({placeholders})
            )
            SELECT id_piezometro, nombre_piezometro, 
            FORMAT(CAST(? AS DATETIME), 'dd/MM/yyyy') AS fechaini,
            FORMAT(CAST(? AS DATETIME), 'dd/MM/yyyy') AS fechafin, 
            elevacion,
            CASE
                WHEN tipo_piezometro = 1 THEN stickup_piezometro + elevacion - medida_piezometro
                ELSE medida_piezometro
            END AS nivel_agua, 'Operativo' AS estado
            FROM cte_cota WHERE row_num = 1 ORDER BY nombre_piezometro;
            """
            
            # Orden Params:
            # 1. idproyecto (CTE)
            # 2. fechaini (CTE Between)
            # 3. fechafin (CTE Between)
            # 4. *filtro_ids (CTE IN)
            # 5. fechaini (Select Format)
            # 6. fechafin (Select Format)
            params = [idproyecto, fechaini, fechafin] + filtro_ids + [fechaini, fechafin]

            cur.execute(sql, params)
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al resumir piezometros: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlTraerDataPiezometro(idinclinometro, tipo):
        conn = None
        sql = """SELECT i.id_instrumentacion, i.id_componente, c.nombre_componente FROM instrumentacion i
        INNER JOIN componentes c ON i.id_componente = c.id_componente
        WHERE i.id_equipo = ? AND i.tipo_equipo = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idinclinometro, tipo))
            row = cur.fetchone()
            if row:
                return tuple(row)
            else:
                return None
        except Exception as e:
            print("Error al traer data piezometro: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlTraerCotaPiezometrica(idcota):
        conn = None
        sql = """SELECT * FROM cotas_piezometricas WHERE id_cota = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idcota,))
            row = cur.fetchone()
            if row:
                return tuple(row)
            else:
                return None
        except Exception as e:
            print("Error al traer info cota piezometrica: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCambiarPiezometroComponente(idinstrumento, nuevocomponente):
        conn = None
        sql = """UPDATE instrumentacion SET id_componente = ? WHERE id_instrumentacion = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (nuevocomponente, idinstrumento))
            conn.commit()
            return True
        except Exception as e:
            print("Error al cambiar componente piezometro: " + str(e))
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlTraerListaFormulas():
        conn = None
        sql = """SELECT * FROM formulas_piezometros;"""
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
            print("Error al traer formulas piezo: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlOmitirLecturaPiezometro(tabla, idPiezo, fecha, campo, campo_fecha):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # Nota: 'campo' y 'campo_fecha' son nombres de columnas, no valores, 
            # por lo que deben ir en el f-string (asegurar que vienen de fuente segura).
            query_update = f"""UPDATE {tabla} SET {campo} = 0 WHERE id_piezometro = ? AND {campo_fecha}=?;"""
            cursor.execute(query_update, (idPiezo, fecha))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al omitir lecturas del Piezometros: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()