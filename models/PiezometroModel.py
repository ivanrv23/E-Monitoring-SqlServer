import sqlite3
from sqlite3 import Error
from services.security.apis.conexiones.conexion import Connection
from datetime import datetime

class PiezometroModel:
    
    def mdlObtenerFechaMaximaPiezometrosCuerda(tabla):
        sql = f"""SELECT MAX(fecha_cuerda) AS max_fecha FROM {tabla};"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al obtener fechas max piezo cuerda: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlObtenerFechaMaximaPiezometrosManual(tabla):
        sql = f"""SELECT MAX(fecha_piezometro) AS max_fecha FROM {tabla};"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al obtener fechas max piezo manual: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # LISTAR LOS PIEZOMETROS DE CUERDA VIBRANTE POR PROYECTO    
    def mdlListarPiezometrosCuerdaProyecto(proyecto, idcomponente, idpiezo, fecha):
        sql = f"""SELECT p.id_piezometro, p.nombre_piezometro, c.id_componente, p.este_piezometro, p.norte_piezometro,
        p.elevacion_piezometro, p.inclinacion_piezometro, p.azimut_piezometro,
		p.tipo_piezometro, d.fecha_cuerda, d.medida_calculada,
        COALESCE(
                (SELECT c2.nivel_cota FROM cotas_piezometricas c2 WHERE c2.id_piezometro = d.id_piezometro AND c2.tipo_piezometro = 'PCV'
                AND c2.fecha_cota <= d.fecha_cuerda ORDER BY c2.fecha_cota DESC LIMIT 1),
                (SELECT c3.nivel_cota FROM cotas_piezometricas c3 WHERE c3.id_piezometro = d.id_piezometro AND c3.tipo_piezometro = 'PCV'
                ORDER BY c3.fecha_cota ASC LIMIT 1)
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
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar piezometro: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # LISTAR LOS PIEZOMETROS POR PROYECTO    
    def mdlListarPiezometrosManualProyecto(proyecto, idcomponente, idinstrumento, fecha):
        conn = Connection.connectionDB()
        sql = f"""SELECT p.id_piezometro, p.nombre_piezometro, c.id_componente, p.este_piezometro, p.norte_piezometro,
        p.elevacion_piezometro, p.inclinacion_piezometro, p.azimut_piezometro, p.stickup_piezometro,
		p.tipo_piezometro, d.fecha_piezometro, d.medida_piezometro,
        COALESCE(
                (SELECT c2.nivel_cota FROM cotas_piezometricas c2 WHERE c2.id_piezometro = d.id_piezometro AND c2.tipo_piezometro = 'PVC'
                AND c2.fecha_cota <= d.fecha_piezometro ORDER BY c2.fecha_cota DESC LIMIT 1),
                (SELECT c3.nivel_cota FROM cotas_piezometricas c3 WHERE c3.id_piezometro = d.id_piezometro AND c3.tipo_piezometro = 'PVC'
                ORDER BY c3.fecha_cota ASC LIMIT 1)
            ) AS cota
		FROM piezometromanuales p
		INNER JOIN piezometromanual_detalle{proyecto} d ON p.id_piezometro = d.id_piezometro
		INNER JOIN instrumentacion t ON p.id_piezometro = t.id_equipo
		INNER JOIN componentes c ON t.id_componente = c.id_componente
        WHERE c.id_proyecto = ? AND t.id_instrumentacion = ? AND c.id_componente = ?
		AND d.fecha_piezometro = ?;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (proyecto, idinstrumento, idcomponente, fecha))
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar piezometro manual: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # LISTAR LOS PIEZOMETROS CUERDA VIBRANTE ÚNICOS QUE TENGAN DATA POR PROYECTO    
    def mdlListarPiezometrosCuerdaInfoProyecto(proyecto):
        conn = Connection.connectionDB()
        sql = """SELECT DISTINCT p.*, 'Automatizado' AS tipo FROM piezometrocuerdas p INNER JOIN piezometrocuerda_detalle d ON p.id_piezometro = d.id_piezometro 
        WHERE p.id_proyecto = ?;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (proyecto,))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar piezometros cuerda vibrante: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
                
    # LISTAR LOS PIEZOMETROS ÚNICOS QUE TENGAN DATA POR PROYECTO    
    def mdlListarPiezometrosManualInfoProyecto(proyecto):
        conn = Connection.connectionDB()
        sql = """SELECT DISTINCT p.*, 'Manual' AS tipo FROM piezometros p INNER JOIN piezometro_detalle d ON p.id_piezometro = d.id_piezometro 
        WHERE p.id_proyecto = ? AND p.estado_piezometro = 1;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (proyecto,))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar piezometros: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # LISTAR DATA PIEZOMETROS POR PROYECTO ID    
    def mdlDataPiezometrosCuerdaProyectoId(proyectoid):
        conn = Connection.connectionDB()
        sql = """SELECT p.nombre_piezometro, d.fecha_cuerda, d.frecuencia_cuerda, d.temperatura_cuerda, d.presion_barometrica, d.observacion_cuerda, d.medida_calculada, 
        p.norte_piezometro, p.este_piezometro, p.elevacion_piezometro FROM piezometrocuerdas p INNER JOIN piezometrocuerda_detalle d 
        ON p.id_piezometro = d.id_piezometro WHERE p.id_proyecto = ?;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (proyectoid,))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar piezometros: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    # LISTAR DATA PIEZOMETROS POR PROYECTO    
    def mdlMostrarDataPiezometrosCuerdaProyecto(iddetalle):
        conn = Connection.connectionDB()
        sql = """SELECT p.nombre_piezometro, d.fecha_cuerda, d.frecuencia_cuerda, d.temperatura_cuerda, d.presion_barometrica, d.observacion_cuerda, d.medida_calculada, 
        p.norte_piezometro, p.este_piezometro, p.elevacion_piezometro FROM piezometrocuerdas p INNER JOIN piezometrocuerda_detalle d 
        ON p.id_piezometro = d.id_piezometro WHERE d.id_cuerda = ?;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (iddetalle,))
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar piezometros: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # LISTAR DATA PIEZOMETROS MANUALES POR PROYECTO ID    
    def mdlDataPiezometrosManualProyectoId(proyectoid):
        conn = Connection.connectionDB()
        sql = """SELECT p.nombre_piezometro, d.fecha_piezometro, d.medida_piezometro, d.observacion_detalle, p.norte_piezometro, p.este_piezometro, 
        p.elevacion_piezometro FROM piezometros p INNER JOIN piezometro_detalle d ON p.id_piezometro = d.id_piezometro WHERE p.id_proyecto = ?;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (proyectoid,))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar piezometros: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    # LISTAR DATA PIEZOMETROS MANUALES POR PROYECTO    
    def mdlMostrarDataPiezometrosManualProyecto(iddetalle):
        conn = Connection.connectionDB()
        sql = """SELECT p.nombre_piezometro, d.fecha_piezometro, d.medida_piezometro, d.observacion_detalle, p.norte_piezometro, p.este_piezometro, 
        p.elevacion_piezometro FROM piezometros p INNER JOIN piezometro_detalle d ON p.id_piezometro = d.id_piezometro WHERE d.id_detalle = ?;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (iddetalle,))
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar piezometros: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # GUARDAR NUEVO PIEZOMETRO MANUAL       
    def mdlGuardarNuevoPiezometroManual(componente, datos, fecha, nivel, tipo):
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # Validar que el componente y el tipo sean PIEZOMETROMANUAL y que el nombre coincida
            sql_validacion = """SELECT COUNT(*) FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = ? AND nombre_equipo = ?;"""
            cur.execute(sql_validacion, (componente, 'PIEZOMETROMANUAL', datos[1]))  # Asumiendo que el nombre está en la segunda posición de datos
            count = cur.fetchone()[0]
            if count > 0:
                return "NO"
            # Insertar el piezómetro en la tabla piezometromanuales
            sql_insert = """INSERT INTO piezometromanuales (id_proyecto, nombre_piezometro, codigo_piezometro, norte_piezometro, este_piezometro, elevacion_piezometro,
            fundacion_piezometro, stickup_piezometro, inclinacion_piezometro, azimut_piezometro, comentario_piezometro)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""
            cur.execute(sql_insert, datos)
            # Obtener el id_piezometro recién insertado
            id_piezometro = cur.lastrowid
            # Registrar la cota en la tabla cotas_piezometricas
            sql_detalle = """INSERT INTO cotas_piezometricas (id_piezometro, tipo_piezometro, fecha_cota, nivel_cota) VALUES (?, ?, ?, ?);"""
            cur.execute(sql_detalle, (id_piezometro, tipo, fecha, nivel))
            # Actualizar la tabla instrumentacion
            sql_instrumentacion = """INSERT INTO instrumentacion (id_componente, tipo_equipo, nombre_equipo, id_equipo, tabla_equipo) VALUES (?, ?, ?, ?, ?);"""
            cur.execute(sql_instrumentacion, (componente, 'PIEZOMETROMANUAL', datos[1], id_piezometro, 'piezometromanuales'))
            # Confirmar la transacción
            conn.commit()
            return "OK"
        except Error as e:
            print("Error al guardar piezómetro manual: " + str(e))
            # Hacer rollback en caso de error
            conn.rollback()
            return "ERROR"
        finally:
            if conn:
                conn.close()
    
    def mdlRegistrarPiezometroManualFormato(componente, datos, fecha, nivel, tipo):
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # Insertar el piezómetro en la tabla piezometromanuales
            sql_insert = """INSERT INTO piezometromanuales (id_proyecto, nombre_piezometro, codigo_piezometro, norte_piezometro, este_piezometro, elevacion_piezometro,
            fundacion_piezometro, stickup_piezometro, inclinacion_piezometro, azimut_piezometro, comentario_piezometro)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""
            cur.execute(sql_insert, datos)
            # Obtener el id_piezometro recién insertado
            id_piezometro = cur.lastrowid
            # Registrar la cota en la tabla cotas_piezometricas
            sql_detalle = """INSERT INTO cotas_piezometricas (id_piezometro, tipo_piezometro, fecha_cota, nivel_cota) VALUES (?, ?, ?, ?);"""
            cur.execute(sql_detalle, (id_piezometro, tipo, fecha, nivel))
            # Actualizar la tabla instrumentacion
            sql_instrumentacion = """INSERT INTO instrumentacion (id_componente, tipo_equipo, nombre_equipo, id_equipo, tabla_equipo) VALUES (?, ?, ?, ?, ?);"""
            cur.execute(sql_instrumentacion, (componente, 'PIEZOMETROMANUAL', datos[1], id_piezometro, 'piezometromanuales'))
            # Confirmar la transacción
            conn.commit()
            return id_piezometro
        except Error as e:
            print("Error al guardar piezómetro manual: " + str(e))
            # Hacer rollback en caso de error
            conn.rollback()
            return None
        finally:
            if conn:
                conn.close()
    
    # GUARDAR NUEVO PIEZOMETRO CUERDA
    def mdlGuardarNuevoPiezometroCuerda(componente, datos, nivelactual, fecha, tipo):
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # Validar que el componente y el tipo sean PIEZOMETROCUERDA y que el nombre coincida
            sql_validacion = """SELECT COUNT(*) FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = ? AND nombre_equipo = ?;"""
            cur.execute(sql_validacion, (componente, 'PIEZOMETROCUERDA', datos[2]))  # Asumiendo que el nombre está en la segunda posición de datos
            count = cur.fetchone()[0]
            if count > 0:
                return "NO"
            # Insertar el piezómetro en la tabla piezometrocuerdas
            sql_insert = """INSERT INTO piezometrocuerdas (id_proyecto, id_formula, nombre_piezometro, serie_sensor, este_piezometro, norte_piezometro,
            elevacion_piezometro, fundacion_piezometro, inclinacion_piezometro, azimut_piezometro, frecuencia_inicial, temperatura_inicial, presion_inicial,
            factor_calibracion, temperatura_correccion, unidad_lectura, constante_a, constante_b, constante_c, factor_conversion, comentario_piezometro)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""
            cur.execute(sql_insert, datos)
            # Obtener el id_piezometro recién insertado
            id_piezometro = cur.lastrowid
            # Registrar la cota en la tabla cotas_piezometricas
            sql_detalle = """INSERT INTO cotas_piezometricas (id_piezometro, tipo_piezometro, fecha_cota, nivel_cota) VALUES (?, ?, ?, ?);"""
            cur.execute(sql_detalle, (id_piezometro, tipo, fecha, nivelactual))
            # Actualizar la tabla instrumentacion
            sql_instrumentacion = """INSERT INTO instrumentacion (id_componente, tipo_equipo, nombre_equipo, id_equipo, tabla_equipo) VALUES (?, ?, ?, ?, ?);"""
            cur.execute(sql_instrumentacion, (componente, 'PIEZOMETROCUERDA', datos[2], id_piezometro, 'piezometrocuerdas'))
            # Confirmar la transacción
            conn.commit()
            return "OK"
        except Error as e:
            print("Error al guardar piezómetro de cuerda: " + str(e))
            # Hacer rollback en caso de error
            conn.rollback()
            return "ERROR"
        finally:
            if conn:
                conn.close()
    
    def mdlRegistrarPiezometroCuerdaFormato(componente, datos, fecha, nivelactual, tipo):
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # Insertar el piezómetro en la tabla piezometrocuerdas
            sql_insert = """INSERT INTO piezometrocuerdas (id_proyecto, nombre_piezometro, serie_sensor, este_piezometro, norte_piezometro, elevacion_piezometro,
            fundacion_piezometro, inclinacion_piezometro, azimut_piezometro, factor_calibracion, temperatura_correccion, frecuencia_inicial, temperatura_inicial,
            presion_inicial, unidad_lectura, constante_a, constante_b, constante_c, factor_conversion, comentario_piezometro)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""
            cur.execute(sql_insert, datos)
            # Obtener el id_piezometro recién insertado
            id_piezometro = cur.lastrowid
            # Registrar la cota en la tabla cotas_piezometricas
            sql_detalle = """INSERT INTO cotas_piezometricas (id_piezometro, tipo_piezometro, fecha_cota, nivel_cota) VALUES (?, ?, ?, ?);"""
            cur.execute(sql_detalle, (id_piezometro, tipo, fecha, nivelactual))
            # Actualizar la tabla instrumentacion
            sql_instrumentacion = """INSERT INTO instrumentacion (id_componente, tipo_equipo, nombre_equipo, id_equipo,tabla_equipo) VALUES (?, ?, ?, ?, ?);"""
            cur.execute(sql_instrumentacion, (componente, 'PIEZOMETROCUERDA', datos[1], id_piezometro, 'piezometrocuerdas'))
            # Confirmar la transacción
            conn.commit()
            return id_piezometro
        except Error as e:
            print("Error al guardar piezómetro de cuerda formato: " + str(e))
            # Hacer rollback en caso de error
            conn.rollback()
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlValidarExisteFormula(formula):
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
        except Error as e:
            print("Error al validar formula piezometro: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlRegistrarNuevaFormula(formula, sentencia):
        try:
            sql = """INSERT INTO formulas_piezometros (formula, sentencia) VALUES (?, ?);"""
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (formula, sentencia))
            conn.commit()
            return True
        except Error as e:
            print("Error al guardar formula piezometro: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    # ACTUALIZAR PIEZOMETRO DE CUERDA VIBRANTE E INSTRUMENTACION
    def mdlActualizarPiezometroCuerda(datos, data):
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
        except Error as e:
            print("Error al editar piezometro de cuerda vibrante: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlActualizarPiezometroCuerdaFormato(datos):
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
        except Error as e:
            print("Error al editar piezometro de cuerda vibrante: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    # ACTUALIZAR ESTADO PIEZOMETRO DE CUERDA VIBRANTE         
    def mdlCambiarEstadoPiezometroCuerda(idpiezo, tipo):
        conn = Connection.connectionDB()
        sql = """UPDATE piezometrocuerdas SET tipo_piezometro = ? WHERE id_piezometro = ?;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (tipo, idpiezo))
            conn.commit()
            return True
        except Error as e:
            print("Error al editar estado cuerda vibrante: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
                
    # ACTUALIZAR PIEZOMETRO MANUAL E INSTRUMENTACION
    def mdlActualizarPiezometroManual(datos, data):
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
        except Error as e:
            print("Error al actualizar piezometro manual: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    # ACTUALIZAR PIEZOMETRO CASAGRANDE
    def mdlActualizarPiezometroManualFormato(datos):
        try:
            conn = Connection.connectionDB()
            sql = """UPDATE piezometromanuales SET codigo_piezometro = ?, norte_piezometro = ?, este_piezometro = ?, elevacion_piezometro = ?, 
            fundacion_piezometro = ?, inclinacion_piezometro = ?, azimut_piezometro = ?, stickup_piezometro = ?, comentario_piezometro = ?
            WHERE id_piezometro = ?"""
            cur = conn.cursor()
            cur.execute(sql, datos)
            conn.commit()
            return True
        except Error as e:
            print("Error al actualizar piezometro manual: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    # CAMBIAR TIPO DE DATA PIEZOMETRO CUERDA
    def mdlCambiarTipoDataPiezometro(idpiezo, estado):
        conn = Connection.connectionDB()
        sql = """UPDATE piezometrocuerdas SET estado_piezometro = ? WHERE id_piezometro = ?;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (estado, idpiezo))
            conn.commit()
            return True
        except Error as e:
            print("Error al cambiar tipo data piezómetro: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
                
    # Validar si existe piezómetro con el mismo nombre
    def mdlComprobarExisteNombrePiezometro(proyecto, nombre, tipo):
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
                return True, row
            else:
                return False, None
        except Error as e:
            print("Error al comprobar piezómetro: " + str(e))
            return False, None
        finally:
            if conn:
                conn.close()
    
    # GUARDAR NUEVO PIEZOMETRO
    def mdlRegistrarMedidaPiezometroManual(idpiezometro, fecha, hora, medida):
        try:
            conn = Connection.connectionDB()
            fecha_nueva = datetime.strptime(fecha, '%d/%m/%Y').strftime('%Y-%m-%d')
            fecha_hora = fecha_nueva + " " + hora
            sql = """INSERT INTO piezometro_detalle (observacion_detalle, id_piezometro, fecha_piezometro, medida_piezometro) VALUES ('Manual', ?, ?, ?)"""
            
            cur = conn.cursor()
            cur.execute(sql, (idpiezometro, fecha_hora, medida))
            conn.commit()
            return True
        except Error as e:
            print("Error al guardar piezómetro manual: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    # REGISTRAR LECTURAS ORIGINAL PIEZOMETROS DE CUERDA VIBRANTE DESDE LA TABLA   
    def mdlGuardarPiezometrosCuerdaTablaOriginal(data):
        # DELETE FROM prismas;
        # DELETE FROM sqlite_sequence WHERE name='prismas';
        conn = Connection.connectionDB()
        cursor = conn.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys = OFF")
            cursor.execute("PRAGMA synchronous = OFF")
            cursor.execute("PRAGMA journal_mode = OFF")
            cursor.execute("PRAGMA temp_store = MEMORY")
            cursor.execute("PRAGMA cache_size = 100000")
            conn.execute("BEGIN TRANSACTION")
            # Crear un conjunto de tuplas con los valores de fecha y hora para comparar los registros existentes
            idpiezo = data[0][0]
            existen_piezometros = set([(row[0]) for row in cursor.execute(f"SELECT fecha_cuerda FROM piezometrocuerda_detalle WHERE id_piezometro = {idpiezo}")])
            lote_registros = []
            contador = 0
            for fila in data:
                fecha_original = fila[1]
                hora_original = fila[2]
                # completar el formato de fecha
                fecha_simple = datetime.strptime(fecha_original, "%d/%m/%Y")
                fecha_formateada = fecha_simple.strftime("%d/%m/%Y")
                fecha_nueva = datetime.strptime(fecha_formateada, '%d/%m/%Y').strftime('%Y-%m-%d')
                fecha_hora_nueva = fecha_nueva + " " + hora_original
                # Verifica si el registro no existe en el conjunto
                if (fecha_hora_nueva) not in existen_piezometros:
                    datito = []
                    datito.append(fila[0]) # id piezometro
                    datito.append(fecha_hora_nueva)
                    datito.append(abs(float(fila[3]))) # siempre positivo la medida
                    datito.append(fila[4]) # temperatura
                    datito.append(fila[5]) # presion
                    datito.append(fila[6]) # Observacion
                    lote_registros.append(datito)
                    contador += 1
                    
                if contador % 1000 == 0:
                    cursor.executemany("""INSERT INTO piezometrocuerda_detalle (id_piezometro, fecha_cuerda, frecuencia_cuerda, temperatura_cuerda, presion_barometrica, observacion_cuerda) VALUES (?, ?, ?, ?, ?, ?)""", lote_registros)
                    lote_registros = []

            if lote_registros:
                cursor.executemany("""INSERT INTO piezometrocuerda_detalle (id_piezometro, fecha_cuerda, frecuencia_cuerda, temperatura_cuerda, presion_barometrica, observacion_cuerda) VALUES (?, ?, ?, ?, ?, ?)""", lote_registros)
                    
            conn.execute("COMMIT")
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute("PRAGMA synchronous = NORMAL")
            cursor.execute("PRAGMA journal_mode = DELETE")
            return True
        except Error as e:
            print("Error al guardar los piezometros de cuerda " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    # REGISTRAR LECTURAS CALCULADAS DE CUERDA VIBRANTE DESDE LA TABLA  
    def mdlGuardarPiezometrosCuerdaCalculoTabla(proyectoid, data, idspiezos):
        table_name = f"piezometrocuerda_detalle{proyectoid}"
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            cursor.execute(f"""CREATE TABLE IF NOT EXISTS "{table_name}" (
                "id_cuerda" INTEGER NOT NULL UNIQUE,
                "id_piezometro" INTEGER NOT NULL,
                "fecha_cuerda" TEXT NOT NULL,
                "frecuencia_cuerda" NUMERIC NOT NULL,
                "temperatura_cuerda" NUMERIC NOT NULL,
                "presion_barometrica" NUMERIC,
                "medida_calculada" NUMERIC,
                "observacion_cuerda" TEXT,
                "estado_cuerda" INTEGER NOT NULL DEFAULT 1,
                PRIMARY KEY("id_cuerda" AUTOINCREMENT)
            );""")
            cursor.execute("PRAGMA foreign_keys = OFF")
            cursor.execute("PRAGMA synchronous = OFF")
            cursor.execute("PRAGMA journal_mode = OFF")
            cursor.execute("PRAGMA temp_store = MEMORY")
            cursor.execute("PRAGMA cache_size = 100000")
            conn.execute("BEGIN TRANSACTION")
            # Crear un conjunto de tuplas con los valores de fecha y hora para comparar los registros existentes
            placeholders = ','.join(['?'] * len(idspiezos))
            existen_piezometros = set([(row[0], row[1]) for row in cursor.execute(f"SELECT id_piezometro, fecha_cuerda FROM {table_name} WHERE id_piezometro IN ({placeholders});", list(idspiezos))])
            lote_registros = []
            contador = 0
            for fila in data:
                id_piezo = fila[0]
                fecha_original = fila[1]
                hora_original = fila[2]
                fecha_hora_nueva = fecha_original + " " + hora_original
                # Verifica si el registro no existe en el conjunto
                if (id_piezo, fecha_hora_nueva) not in existen_piezometros:
                    datito = []
                    datito.append(id_piezo)
                    datito.append(fecha_hora_nueva)
                    datito.append(abs(float(fila[3])))  # siempre positivo la frecuencia
                    datito.append(fila[4])  # temperatura
                    datito.append(fila[5])  # presion barometrica
                    datito.append(fila[6])  # data calculada MCA
                    datito.append(fila[7])  # Observacion
                    lote_registros.append(datito)
                    contador += 1

                    if contador % 1000 == 0:
                        cursor.executemany(f"""
                            INSERT INTO {table_name} (
                                id_piezometro, fecha_cuerda, frecuencia_cuerda,
                                temperatura_cuerda, presion_barometrica,
                                medida_calculada, observacion_cuerda
                            ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, lote_registros)
                        lote_registros = []

            if lote_registros:
                cursor.executemany(f"""
                    INSERT INTO {table_name} (
                        id_piezometro, fecha_cuerda, frecuencia_cuerda,
                        temperatura_cuerda, presion_barometrica,
                        medida_calculada, observacion_cuerda
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, lote_registros)

            conn.execute("COMMIT")
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute("PRAGMA synchronous = NORMAL")
            cursor.execute("PRAGMA journal_mode = DELETE")
            return True
        except Exception as e:
            conn.execute("ROLLBACK")
            print("Error al guardar los piezometros de cuerda: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    # Validar si existe piezómetro con el mismo nombre al actualizar
    def mdlComprobarActualizarNombrePiezometro(idpiezo, nombre, tipo):
        if tipo == "Automatizado":
            sql = """SELECT * FROM piezometrocuerdas WHERE nombre_piezometro = ? AND id_piezometro != ?;"""
        else:
            sql = """SELECT * FROM piezometromanuales WHERE nombre_piezometro = ? AND id_piezometro != ?;"""
        conn = Connection.connectionDB()
        try:
            cur = conn.cursor()
            cur.execute(sql, (idpiezo, nombre))
            row = cur.fetchone()
            if row:
                return True
            else:
                return False
        except Error as e:
            print("Error al comprobar piezómetro: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
                              
    # REGISTRAR PIEZOMETROS MANUALES DESDE LA TABLA   
    def mdlGuardarPiezometrosManualesTabla(idproyecto, data):
        nombretabla = "piezometromanual_detalle" + str(idproyecto)
        sqltable = f"""
            CREATE TABLE IF NOT EXISTS "{nombretabla}" (
                "id_detalle" INTEGER NOT NULL UNIQUE,
                "id_piezometro" INTEGER NOT NULL,
                "fecha_piezometro" TEXT NOT NULL,
                "medida_piezometro" NUMERIC,
                "observacion_detalle" TEXT,
                "estado_manual" INTEGER NOT NULL DEFAULT 1,
                PRIMARY KEY("id_detalle" AUTOINCREMENT)
            );
        """
        conn = Connection.connectionDB()
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = OFF")
            cursor.execute("PRAGMA synchronous = OFF")
            cursor.execute("PRAGMA journal_mode = OFF")
            cursor.execute("PRAGMA temp_store = MEMORY")
            cursor.execute("PRAGMA cache_size = 100000")
            cursor.execute(sqltable)
            conn.execute("BEGIN TRANSACTION")

            # Crear un conjunto de tuplas con los valores de fecha y hora para comparar los registros existentes
            idpiezo = data[0][0]
            existen_piezometros = set([(row[0]) for row in cursor.execute(f"SELECT fecha_piezometro FROM {nombretabla} WHERE id_piezometro = ?;", (idpiezo,))])

            lote_registros = []
            contador = 0

            for fila in data:
                fecha_original = fila[1]
                hora_original = fila[2]
                fecha_hora_nueva = fecha_original + " " + hora_original

                # Verifica si el registro no existe en el conjunto
                if fecha_hora_nueva not in existen_piezometros:
                    datito = []
                    datito.append(fila[0])  # id_piezometro
                    datito.append(fecha_hora_nueva)
                    datito.append(abs(float(fila[3])))  # siempre positivo la medida
                    datito.append(fila[4])  # observacion_detalle
                    lote_registros.append(datito)
                    contador += 1

                    if contador % 1000 == 0:
                        cursor.executemany(f"""
                            INSERT INTO {nombretabla} (
                                id_piezometro, fecha_piezometro, medida_piezometro, observacion_detalle
                            ) VALUES (?, ?, ?, ?)
                        """, lote_registros)
                        lote_registros = []

            if lote_registros:
                cursor.executemany(f"""
                    INSERT INTO {nombretabla} (
                        id_piezometro, fecha_piezometro, medida_piezometro, observacion_detalle
                    ) VALUES (?, ?, ?, ?)
                """, lote_registros)

            conn.execute("COMMIT")
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute("PRAGMA synchronous = NORMAL")
            cursor.execute("PRAGMA journal_mode = DELETE")
            return True
        except Exception as e:
            conn.execute("ROLLBACK")
            print("Error al guardar los piezometros manuales: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlGuardarCotasPiezometricasTabla(data):
        try:
            conn = Connection.connectionDB()
            # Crear un conjunto de tuplas con los valores de fecha para comparar los registros existentes
            idpiezo = data[0][0]
            tipopiezo = data[0][1]
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = OFF")
            cursor.execute("PRAGMA synchronous = OFF")
            cursor.execute("PRAGMA journal_mode = OFF")
            cursor.execute("PRAGMA temp_store = MEMORY")
            cursor.execute("PRAGMA cache_size = 100000")
            conn.execute("BEGIN TRANSACTION")
            existen_cotas = set([(row[0]) for row in cursor.execute("SELECT fecha_cota FROM cotas_piezometricas WHERE id_piezometro = ? AND tipo_piezometro = ?;", (idpiezo, tipopiezo))])
            lote_registros = []
            contador = 0
            for fila in data:
                nueva_fila = list(fila)
                nueva_fila[2] = f"{nueva_fila[2]} 00:00:00"
                # Verifica si el registro no existe en el conjunto
                if nueva_fila[2] not in existen_cotas:
                    lote_registros.append(nueva_fila)
                    contador += 1
                    if contador % 1000 == 0:
                        cursor.executemany("""INSERT INTO cotas_piezometricas (id_piezometro, tipo_piezometro, fecha_cota, nivel_cota) VALUES (?, ?, ?, ?);""", lote_registros)
                        lote_registros = []
            if lote_registros:
                cursor.executemany("""INSERT INTO cotas_piezometricas (id_piezometro, tipo_piezometro, fecha_cota, nivel_cota) VALUES (?, ?, ?, ?);""", lote_registros)
            conn.execute("COMMIT")
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute("PRAGMA synchronous = NORMAL")
            cursor.execute("PRAGMA journal_mode = DELETE")
            return True
        except Exception as e:
            conn.execute("ROLLBACK")
            print("Error al guardar las cotas: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    # OBTENER DATA PIEZOMETRO AUTOMATIZADO 
    def mdlObtenerDataPiezometroA(idpiezo):
        conn = Connection.connectionDB()
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
            cur = conn.cursor()
            cur.execute(sql, (idpiezo,))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Error as e:
            return None
        finally:
            if conn:
                conn.close()
    
    # OBTENER DATA PIEZOMETRO AUTOMATIZADO ENTRE FECHAS
    def mdlObtenerDataPiezometroAutoFechas(idpiezo, fechaini, fechafin):
        conn = Connection.connectionDB()
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
                WHERE pd.id_piezometro = ? AND pd.fecha_cuerda BETWEEN '""" + str(fechaini) + """' AND '""" + str(fechafin) + """';"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (idpiezo,))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Error as e:
            return None
        finally:
            if conn:
                conn.close()
                  
    # OBTENER DATA PIEZOMETRO NORMAL 
    def mdlObtenerDataPiezometroN(idpiezodetalle):
        conn = Connection.connectionDB()
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
            cur = conn.cursor()
            cur.execute(sql, (idpiezodetalle,))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Error as e:
            return None
        finally:
            if conn:
                conn.close()
    
    # OBTENER DATA PIEZOMETRO MANUAL ENTRE FECHAS
    def mdlObtenerDataPiezometroManualFechas(idpiezodetalle, fechaini, fechafin):
        conn = Connection.connectionDB()
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
            WHERE pd.id_piezometro = ? AND pd.fecha_piezometro BETWEEN '""" + str(fechaini) + """' AND '""" + str(fechafin) + """';"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (idpiezodetalle,))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Error as e:
            return None
        finally:
            if conn:
                conn.close()
                
    def mdlTraerInfoPiezometroCuerda(idipiezo):
        conn = Connection.connectionDB()
        sql = """SELECT * FROM piezometrocuerdas WHERE id_piezometro = ?;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (idipiezo,))
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar piezometro cuerda: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlTraerInfoPiezometroManual(idipiezo):
        conn = Connection.connectionDB()
        sql = """SELECT * FROM piezometros WHERE id_piezometro = ?;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (idipiezo,))
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar piezometro manual: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlTraerInfoDetallePiezometroCuerda(iddetalle):
        conn = Connection.connectionDB()
        sql = """SELECT 'Automatizado' AS tipo, * FROM piezometrocuerda_detalle WHERE id_cuerda = ?;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (iddetalle,))
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar detalle piezometro cuerda: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlTraerBaseDetallePiezometro(idpiezo):
        conn = Connection.connectionDB()
        sql = """SELECT 'Automatizado' AS tipo, * FROM piezometrocuerda_detalle WHERE id_piezometro = ? ORDER BY fecha_cuerda ASC LIMIT 1;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (idpiezo,))
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar base piezometro cuerda: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlTraerInfoDetallePiezometroManual(iddetalle):
        conn = Connection.connectionDB()
        sql = """SELECT 'Manual' AS tipo, * FROM piezometro_detalle WHERE id_detalle = ?;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (iddetalle,))
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar detalle piezometro manual: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlEliminarPiezometroCuerda(idpiezometro):
        conn = Connection.connectionDB()
        sql = """DELETE FROM piezometrocuerdas WHERE id_piezometro = ?"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (idpiezometro,))
            conn.commit()
            if cur.rowcount > 0:
                return True
            else:
                return False
        except Error as e:
            print("Error al eliminar piezómetro: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlEliminarPiezometroManual(idpiezometro):
        conn = Connection.connectionDB()
        sql = """DELETE FROM piezometros WHERE id_piezometro = ?"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (idpiezometro,))
            conn.commit()
            if cur.rowcount > 0:
                return True
            else:
                return False
        except Error as e:
            print("Error al eliminar piezómetro: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    # obtener fecha mini y maximo de los piezometros cuerda
    def mdlObtenerFechaMinMaxCuerda(proyectoid):
        conn = Connection.connectionDB()
        sql = """SELECT MIN(pd.fecha_cuerda) AS min_fecha, MAX(pd.fecha_cuerda) AS max_fecha FROM piezometrocuerda_detalle pd INNER JOIN piezometrocuerdas p 
        ON pd.id_piezometro = p.id_piezometro WHERE p.id_proyecto = ?;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (proyectoid,))
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al obtener fechas min-max: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # obtener fecha mini y maximo de los piezometros manuales
    def mdlObtenerFechaMinMaxPiezomanual(proyectoid):
        conn = Connection.connectionDB()
        sql = """SELECT MIN(pd.fecha_piezometro) AS min_fecha, MAX(pd.fecha_piezometro) AS max_fecha FROM piezometro_detalle pd INNER JOIN piezometros p 
        ON pd.id_piezometro = p.id_piezometro WHERE p.id_proyecto = ? AND p.estado_piezometro != 0;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (proyectoid,))
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al obtener fechas min-max: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlCalcularPiezometrosCasaGrande(tabla, idcomponente, listapiezo, unidadmedidad):
        placeholders = ', '.join(['?' for _ in listapiezo])
        params = [idcomponente] + listapiezo + [unidadmedidad] + [unidadmedidad]
        sql = f"""WITH cte_cota AS (
            SELECT it.id_instrumentacion, p.nombre_piezometro, d.fecha_piezometro, p.tipo_piezometro,
            CAST(julianday(d.fecha_piezometro) - julianday(FIRST_VALUE(d.fecha_piezometro) OVER (PARTITION BY p.nombre_piezometro ORDER BY d.fecha_piezometro)) AS NUMERIC) AS dias,
            CAST(julianday(d.fecha_piezometro) - julianday(FIRST_VALUE(d.fecha_piezometro) OVER (PARTITION BY p.nombre_piezometro ORDER BY d.fecha_piezometro)) AS NUMERIC) * 24 AS horas,
            d.medida_piezometro, p.stickup_piezometro, p.fundacion_piezometro,
            COALESCE(
                (SELECT c2.nivel_cota FROM cotas_piezometricas c2 WHERE c2.id_piezometro = d.id_piezometro 
                AND c2.tipo_piezometro = 'PVC' AND c2.fecha_cota <= d.fecha_piezometro ORDER BY c2.fecha_cota DESC LIMIT 1),
                (SELECT c3.nivel_cota FROM cotas_piezometricas c3 WHERE c3.id_piezometro = d.id_piezometro
                AND c3.tipo_piezometro = 'PVC' ORDER BY c3.fecha_cota ASC LIMIT 1)
            ) AS elevacion,it.tipo_equipo,it.id_equipo
            FROM piezometromanuales p INNER JOIN {tabla} d ON p.id_piezometro = d.id_piezometro
            INNER JOIN instrumentacion AS it ON it.id_equipo = p.id_piezometro
            INNER JOIN componentes AS co ON co.id_componente = it.id_componente
            WHERE d.estado_manual = 1 AND co.id_componente = ? AND it.id_instrumentacion IN ({placeholders})
            ORDER BY p.nombre_piezometro ASC, d.fecha_piezometro ASC
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
            END * ? AS acumulado, fundacion_piezometro, elevacion,tipo_equipo,id_equipo
        FROM cte_cota ORDER BY nombre_piezometro ASC, fecha_piezometro ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return rows
            else:
                return None
        except Error as e:
            print("Error al obtener data piezo manual: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlCalcularPiezometrosFechasCasaGrande(tabla, idcomponente, listapiezo, unidadmedidad, fechaini, fechafin):
        conn = Connection.connectionDB()
        placeholders = ', '.join(['?' for _ in listapiezo])
        params = [idcomponente] + listapiezo + [fechaini] + [fechafin] + [unidadmedidad] + [unidadmedidad]
        sql = f"""WITH cte_cota AS (
            SELECT it.id_instrumentacion, p.nombre_piezometro, d.fecha_piezometro, p.tipo_piezometro,
            CAST(julianday(d.fecha_piezometro) - julianday(FIRST_VALUE(d.fecha_piezometro) OVER (PARTITION BY p.nombre_piezometro ORDER BY d.fecha_piezometro)) AS NUMERIC) AS dias,
            CAST(julianday(d.fecha_piezometro) - julianday(FIRST_VALUE(d.fecha_piezometro) OVER (PARTITION BY p.nombre_piezometro ORDER BY d.fecha_piezometro)) AS NUMERIC) * 24 AS horas,
            d.medida_piezometro, p.stickup_piezometro, p.fundacion_piezometro,
            COALESCE(
                (SELECT c2.nivel_cota FROM cotas_piezometricas c2 WHERE c2.id_piezometro = d.id_piezometro 
                AND c2.tipo_piezometro = 'PVC' AND c2.fecha_cota <= d.fecha_piezometro ORDER BY c2.fecha_cota DESC LIMIT 1),
                (SELECT c3.nivel_cota FROM cotas_piezometricas c3 WHERE c3.id_piezometro = d.id_piezometro
                AND c3.tipo_piezometro = 'PVC' ORDER BY c3.fecha_cota ASC LIMIT 1)
            ) AS elevacion,it.tipo_equipo,it.id_equipo
            FROM piezometromanuales p INNER JOIN {tabla} d ON p.id_piezometro = d.id_piezometro
            INNER JOIN instrumentacion AS it ON it.id_equipo = p.id_piezometro
            INNER JOIN componentes AS co ON co.id_componente = it.id_componente
            WHERE d.estado_manual = 1 AND co.id_componente = ? AND it.id_instrumentacion IN ({placeholders})
            AND d.fecha_piezometro BETWEEN ? AND ? ORDER BY p.nombre_piezometro ASC, d.fecha_piezometro ASC
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
            END * ? AS acumulado, fundacion_piezometro, elevacion,tipo_equipo,id_equipo
        FROM cte_cota ORDER BY nombre_piezometro ASC, fecha_piezometro ASC;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return rows
            else:
                return None
        except Error as e:
            print("Error al obtener data piezo manual: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlObtenerFormulaPiezometroCuerda(idpiezometro):
        sql = f"""SELECT p.id_formula, f.sentencia FROM piezometrocuerdas p INNER JOIN formulas_piezometros f
        ON p.id_formula = f.id_formula WHERE p.id_piezometro = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idpiezometro,))
            results = cur.fetchone()
            if results:
                return results
            else:
                return [0, None]
        except Error as e:
            print("Error al obtener formula cuerda:", e)
            return [0, None]
        finally:
            if conn:
                conn.close()
    
    def mdlCalcularPiezometrosCuerda(tabla, idcomponente, listapiezo, unidadmedida):
        params = (unidadmedida, unidadmedida, idcomponente, listapiezo)
        sql = f"""SELECT t.id_instrumentacion, pzc.nombre_piezometro, pzcd.fecha_cuerda,
            CAST(julianday(pzcd.fecha_cuerda) - julianday(FIRST_VALUE(pzcd.fecha_cuerda) OVER (PARTITION BY pzc.nombre_piezometro ORDER BY pzcd.fecha_cuerda)) AS NUMERIC) AS dias,
            CAST(julianday(pzcd.fecha_cuerda) - julianday(FIRST_VALUE(pzcd.fecha_cuerda) OVER (PARTITION BY pzc.nombre_piezometro ORDER BY pzcd.fecha_cuerda)) AS NUMERIC) * 24 AS horas,
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
				(SELECT c2.nivel_cota FROM cotas_piezometricas c2 WHERE c2.id_piezometro = pzc.id_piezometro 
				   AND c2.tipo_piezometro = 'PCV' AND c2.fecha_cota <= pzcd.fecha_cuerda ORDER BY c2.fecha_cota DESC LIMIT 1),
				(SELECT c3.nivel_cota FROM cotas_piezometricas c3 WHERE c3.id_piezometro = pzc.id_piezometro 
				   AND c3.tipo_piezometro = 'PCV' ORDER BY c3.fecha_cota ASC LIMIT 1)
			) AS superficie, t.tipo_equipo, pzc.unidad_lectura
        FROM piezometrocuerdas pzc INNER JOIN {tabla} pzcd ON pzc.id_piezometro = pzcd.id_piezometro 
        INNER JOIN instrumentacion t ON pzc.id_piezometro = t.id_equipo
        INNER JOIN componentes c ON t.id_componente = c.id_componente
        WHERE pzcd.estado_cuerda = 1 AND c.id_componente = ? AND t.id_instrumentacion = ?
        ORDER BY pzc.nombre_piezometro ASC, pzcd.fecha_cuerda ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return rows
            else:
                return None
        except Error as e:
            print("Error al obtener data piezo cuerda: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlCalcularPiezometrosCuerdaFormula(tabla, idcomponente, idinstrumento, unidadmedida, formula):
        params = (idcomponente, idinstrumento, unidadmedida, unidadmedida)
        sql = f"""WITH piezometros AS (SELECT t.id_instrumentacion, p.nombre_piezometro, d.fecha_cuerda,
                CAST(julianday(d.fecha_cuerda) - julianday(FIRST_VALUE(d.fecha_cuerda) OVER (PARTITION BY p.nombre_piezometro ORDER BY d.fecha_cuerda)) AS NUMERIC) AS dias,
                CAST(julianday(d.fecha_cuerda) - julianday(FIRST_VALUE(d.fecha_cuerda) OVER (PARTITION BY p.nombre_piezometro ORDER BY d.fecha_cuerda)) AS NUMERIC) * 24 AS horas,
                d.frecuencia_cuerda, d.temperatura_cuerda, ({formula}) AS presion_barometrica,
                p.fundacion_piezometro, p.elevacion_piezometro AS instalacion,
                COALESCE(
                    (SELECT c2.nivel_cota FROM cotas_piezometricas c2 WHERE c2.id_piezometro = p.id_piezometro 
                    AND c2.tipo_piezometro = 'PCV' AND c2.fecha_cota <= d.fecha_cuerda ORDER BY c2.fecha_cota DESC LIMIT 1),
                    (SELECT c3.nivel_cota FROM cotas_piezometricas c3 WHERE c3.id_piezometro = p.id_piezometro 
                    AND c3.tipo_piezometro = 'PCV' ORDER BY c3.fecha_cota ASC LIMIT 1)
                ) AS superficie, t.tipo_equipo, p.unidad_lectura, p.factor_conversion
            FROM piezometrocuerdas p INNER JOIN {tabla} d ON p.id_piezometro = d.id_piezometro 
            INNER JOIN instrumentacion t ON p.id_piezometro = t.id_equipo
            INNER JOIN componentes c ON t.id_componente = c.id_componente
            WHERE d.estado_cuerda = 1 AND c.id_componente = ? AND t.id_instrumentacion = ?
            ORDER BY p.nombre_piezometro ASC, d.fecha_cuerda ASC
        )
        SELECT id_instrumentacion, nombre_piezometro, fecha_cuerda, dias, horas, frecuencia_cuerda, temperatura_cuerda,
            presion_barometrica,
            (instalacion + (presion_barometrica * factor_conversion)) AS nivel_agua,
            (COALESCE(presion_barometrica - LAG(presion_barometrica) OVER (PARTITION BY nombre_piezometro ORDER BY fecha_cuerda), 0) * factor_conversion) * ? AS incremental,
            (presion_barometrica * factor_conversion) * ? AS acumulado, fundacion_piezometro,
            superficie, tipo_equipo, unidad_lectura
        FROM piezometros;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return rows
            else:
                return None
        except Error as e:
            print("Error al obtener data piezo cuerda formula: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlCalcularPiezometrosFechasCuerda(tabla, idcomponente, listapiezo, unidadmedida, fechaini, fechafin):
        params = (unidadmedida, unidadmedida, idcomponente, listapiezo, fechaini, fechafin)
        sql = f"""SELECT t.id_instrumentacion, pzc.nombre_piezometro, pzcd.fecha_cuerda,
            CAST(julianday(pzcd.fecha_cuerda) - julianday(FIRST_VALUE(pzcd.fecha_cuerda) OVER (PARTITION BY pzc.nombre_piezometro ORDER BY pzcd.fecha_cuerda)) AS NUMERIC) AS dias,
            CAST(julianday(pzcd.fecha_cuerda) - julianday(FIRST_VALUE(pzcd.fecha_cuerda) OVER (PARTITION BY pzc.nombre_piezometro ORDER BY pzcd.fecha_cuerda)) AS NUMERIC) * 24 AS horas,
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
				(SELECT c2.nivel_cota FROM cotas_piezometricas c2 WHERE c2.id_piezometro = pzc.id_piezometro 
				   AND c2.tipo_piezometro = 'PCV' AND c2.fecha_cota <= pzcd.fecha_cuerda ORDER BY c2.fecha_cota DESC LIMIT 1),
				(SELECT c3.nivel_cota FROM cotas_piezometricas c3 WHERE c3.id_piezometro = pzc.id_piezometro 
				   AND c3.tipo_piezometro = 'PCV' ORDER BY c3.fecha_cota ASC LIMIT 1)
			) AS superficie, t.tipo_equipo, pzc.unidad_lectura
        FROM piezometrocuerdas pzc INNER JOIN {tabla} pzcd ON pzc.id_piezometro = pzcd.id_piezometro 
        INNER JOIN instrumentacion t ON pzc.id_piezometro = t.id_equipo
        INNER JOIN componentes c ON t.id_componente = c.id_componente
        WHERE pzcd.estado_cuerda = 1 AND c.id_componente = ? AND t.id_instrumentacion = ? AND pzcd.fecha_cuerda BETWEEN ? AND ?
        ORDER BY pzc.nombre_piezometro ASC, pzcd.fecha_cuerda ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return rows
            else:
                return None
        except Error as e:
            print("Error al obtener data piezo cuerda: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlCalcularPiezometrosFechasCuerdaFormula(tabla, idcomponente, idinstrumento, unidadmedida, fechaini, fechafin, formula):
        params = (idcomponente, idinstrumento, fechaini, fechafin, unidadmedida, unidadmedida)
        sql = f"""WITH piezometros AS (SELECT t.id_instrumentacion, p.nombre_piezometro, d.fecha_cuerda,
                CAST(julianday(d.fecha_cuerda) - julianday(FIRST_VALUE(d.fecha_cuerda) OVER (PARTITION BY p.nombre_piezometro ORDER BY d.fecha_cuerda)) AS NUMERIC) AS dias,
                CAST(julianday(d.fecha_cuerda) - julianday(FIRST_VALUE(d.fecha_cuerda) OVER (PARTITION BY p.nombre_piezometro ORDER BY d.fecha_cuerda)) AS NUMERIC) * 24 AS horas,
                d.frecuencia_cuerda, d.temperatura_cuerda, ({formula}) AS presion_barometrica,
                p.fundacion_piezometro, p.elevacion_piezometro AS instalacion,
                COALESCE(
                    (SELECT c2.nivel_cota FROM cotas_piezometricas c2 WHERE c2.id_piezometro = p.id_piezometro 
                    AND c2.tipo_piezometro = 'PCV' AND c2.fecha_cota <= d.fecha_cuerda ORDER BY c2.fecha_cota DESC LIMIT 1),
                    (SELECT c3.nivel_cota FROM cotas_piezometricas c3 WHERE c3.id_piezometro = p.id_piezometro 
                    AND c3.tipo_piezometro = 'PCV' ORDER BY c3.fecha_cota ASC LIMIT 1)
                ) AS superficie, t.tipo_equipo, p.unidad_lectura, p.factor_conversion
            FROM piezometrocuerdas p INNER JOIN {tabla} d ON p.id_piezometro = d.id_piezometro 
            INNER JOIN instrumentacion t ON p.id_piezometro = t.id_equipo
            INNER JOIN componentes c ON t.id_componente = c.id_componente
            WHERE d.estado_cuerda = 1 AND c.id_componente = ? AND t.id_instrumentacion = ? AND d.fecha_cuerda BETWEEN ? AND ?
            ORDER BY p.nombre_piezometro ASC, d.fecha_cuerda ASC
        )
        SELECT id_instrumentacion, nombre_piezometro, fecha_cuerda, dias, horas, frecuencia_cuerda, temperatura_cuerda,
            presion_barometrica,
            (instalacion + (presion_barometrica * factor_conversion)) AS nivel_agua,
            (COALESCE(presion_barometrica - LAG(presion_barometrica) OVER (PARTITION BY nombre_piezometro ORDER BY fecha_cuerda), 0) * factor_conversion) * ? AS incremental,
            (presion_barometrica * factor_conversion) * ? AS acumulado, fundacion_piezometro,
            superficie, tipo_equipo, unidad_lectura
        FROM piezometros;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return rows
            else:
                return None
        except Error as e:
            print("Error al obtener data piezo cuerda fechas formula: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # ACTUALIZAR LECTURA PIEZOMETRO CUERDA DESDE TABLA      
    def mdlActualizarLecturaPiezometroCuerda(tabla, datos, idproyecto, username, nombres):
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
                fecha_cambio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                accion = "update"
                cambios = f"Antiguos: {datos_anteriores}, Nuevos: {datos}"
                query_historial = """INSERT INTO historial (idproyecto, fecha, accion, tabla, cambios, usuario, nombres)
                VALUES (?, ?, ?, ?, ?, ?, ?);"""
                cur.execute(query_historial, (idproyecto, fecha_cambio, accion, tabla, cambios, username, nombres))
            # actualizar cuerda
            cur.execute(sql, datos)
            conn.commit()
            return True
        except Error as e:
            print("Error al editar lectura cuerda vibrante: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlCambiarEstadoLecturaPiezoCuerda(tabla, iddetalle):
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
            return False
        finally:
            conn.close()
    
    def mdlCambiarEstadoLecturaPiezoCuerdaBloque(tabla, listacodigos):
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            placeholders = ','.join(['?'] * len(listacodigos))
            query_update = f"""UPDATE {tabla} SET estado_cuerda = CASE estado_cuerda WHEN 1 THEN 0 ELSE 1 END
            WHERE id_cuerda IN ({placeholders});"""
            cursor.execute(query_update, listacodigos)
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error al cambiar estado de lecturas cuerda: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlEliminarLecturaPiezoCuerda(tabla, iddetalle, idproyecto, username, nombres):
        sql = f"""DELETE FROM {tabla} WHERE id_cuerda = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # guardar en historial
            query_select = f"""SELECT * FROM {tabla} WHERE id_cuerda = ?;"""
            cur.execute(query_select, (iddetalle,))
            datos_anteriores = cur.fetchone()
            if datos_anteriores:
                fecha_cambio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                accion = "delete"
                cambios = f"Datos: {datos_anteriores}"
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
        except Error as e:
            print("Error al eliminar lectura cuerda: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlEliminarLecturasBloquePiezoCuerda(tabla, iddetalles, idproyecto, username, nombres):
        placeholders = ', '.join(['?' for _ in iddetalles])
        query = f"""DELETE FROM {tabla} WHERE id_cuerda IN ({placeholders});"""
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # guardar en historial
            query_select = f"""SELECT * FROM {tabla} WHERE id_cuerda IN ({placeholders});"""
            cursor.execute(query_select, iddetalles)
            datos_anteriores = cursor.fetchall()
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
            return False
        finally:
            conn.close()
    
    def mdlActualizarCotaPiezometrica(idproyecto, idcota, datofecha, cotamedida, username, nombres):
        sql = f"""UPDATE cotas_piezometricas SET fecha_cota = ?, nivel_cota = ? WHERE id_cota = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # guardar en historial
            query_select = f"""SELECT * FROM cotas_piezometricas WHERE id_cota = ?;"""
            cur.execute(query_select, (idcota,))
            datos_anteriores = cur.fetchone()
            if datos_anteriores:
                fecha_cambio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                accion = "update"
                cambios = f"Antiguos: {datos_anteriores}, Nuevos: {[datofecha, cotamedida, idcota]}"
                query_historial = """INSERT INTO historial (idproyecto, fecha, accion, tabla, cambios, usuario, nombres)
                VALUES (?, ?, ?, ?, ?, ?, ?);"""
                tabla = "cotas_piezometricas"
                cur.execute(query_historial, (idproyecto, fecha_cambio, accion, tabla, cambios, username, nombres))
            # actualizar cuerda
            cur.execute(sql, (datofecha, cotamedida, idcota))
            conn.commit()
            return True
        except Error as e:
            print("Error al editar cota piezometrica: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    # ACTUALIZAR LECTURA PIEZOMETRO MANUAL DESDE TABLA      
    def mdlActualizarLecturaPiezometroManual(tabla, datos, idproyecto, username, nombres):
        sql = f"""UPDATE {tabla} SET fecha_piezometro = ?, medida_piezometro = ?, observacion_detalle = ? WHERE id_detalle = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # guardar en historial
            query_select = f"""SELECT fecha_piezometro, medida_piezometro, observacion_detalle, id_detalle FROM {tabla} WHERE id_detalle = ?;"""
            cur.execute(query_select, (datos[-1],))
            datos_anteriores = cur.fetchone()
            if datos_anteriores:
                fecha_cambio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                accion = "update"
                cambios = f"Antiguos: {datos_anteriores}, Nuevos: {datos}"
                query_historial = """INSERT INTO historial (idproyecto, fecha, accion, tabla, cambios, usuario, nombres)
                VALUES (?, ?, ?, ?, ?, ?, ?);"""
                cur.execute(query_historial, (idproyecto, fecha_cambio, accion, tabla, cambios, username, nombres))
            # actualizar cuerda
            cur.execute(sql, datos)
            conn.commit()
            return True
        except Error as e:
            print("Error al editar lectura casagrande: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlCambiarEstadoLecturaPiezoManual(tabla, iddetalle):
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
            return False
        finally:
            conn.close()
    
    def mdlCambiarEstadoLecturaPiezoManualBloque(tabla, listacodigos):
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
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlEliminarLecturaPiezoManual(tabla, iddetalle, idproyecto, username, nombres):
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
            # eliminar lectura
            cur.execute(sql, (iddetalle,))
            conn.commit()
            if cur.rowcount > 0:
                return True
            else:
                return False
        except Error as e:
            print("Error al eliminar lectura casagrande: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlEliminarLecturasBloquePiezoManual(tabla, iddetalles, idproyecto, username, nombres):
        placeholders = ', '.join(['?' for _ in iddetalles])
        query = f"""DELETE FROM {tabla} WHERE id_detalle IN ({placeholders});"""
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # guardar en historial
            query_select = f"""SELECT * FROM {tabla} WHERE id_detalle IN ({placeholders});"""
            cursor.execute(query_select, iddetalles)
            datos_anteriores = cursor.fetchall()
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
            return False
        finally:
            if conn:
                conn.close()
                
    # LISTAR LOS PIEZOMETROS DE CUERDA VIBRANTE POR PROYECTO    
    def mdlListarPiezometrosCuerda(proyecto):
        conn = Connection.connectionDB()
        sql = """SELECT * FROM piezometrocuerdas WHERE id_proyecto = ? AND estado_piezometro = 1;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (proyecto,))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar piezometros: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
                
    # LISTAR LOS PIEZOMETROS MANUALES POR PROYECTO    
    def mdlListarPiezometrosManuales(proyecto):
        conn = Connection.connectionDB()
        sql = """SELECT * FROM piezometromanuales WHERE id_proyecto = ? AND estado_piezometro = 1;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (proyecto,))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar piezometros: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    
    def mdlCambiarComponentePiezometrosCuerda(idcomponente, nuevocomponente):
        sql = """UPDATE instrumentacion SET id_componente = ? WHERE id_componente = ? AND tipo_equipo = 'PIEZOMETROCUERDA';"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # guardar en historial
            query_select = """SELECT * FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'PIEZOMETROCUERDA';"""
            cur.execute(query_select, (idcomponente,))
            dataincli = cur.fetchall()
            if dataincli:
                cur.execute(sql, (nuevocomponente, idcomponente))
                conn.commit()
                return dataincli
            else:
                return None
        except Error as e:
            print("Error al cambiar componente cuerdas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlEliminarPiezometrosCuerda(idcomponente):
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # guardar en historial
            query_select = """SELECT * FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'PIEZOMETROCUERDA';"""
            cursor.execute(query_select, (idcomponente,))
            dataincli = cursor.fetchall()
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
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlEliminarDataPiezometrosCuerda(tabla, cuerdas):
        placeholders = ','.join(['?' for _ in cuerdas])
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # eliminar data
            query_delete = f"""DELETE FROM {tabla} WHERE id_piezometro IN ({placeholders});"""
            cursor.execute(query_delete, cuerdas)
            rows_data = cursor.rowcount
            if rows_data > 0:
                query_delete_cuerdas = f"DELETE FROM piezometrocuerdas WHERE id_piezometro IN ({placeholders});"
                cursor.execute(query_delete_cuerdas, cuerdas)
                rows_cuerdas = cursor.rowcount
                conn.commit()
                return rows_cuerdas > 0
            else:
                conn.rollback()
                return False
        except Exception as e:
            print(f"Error al eliminar data cuerdas: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlObtenerInfoPiezometroCuerda(idinstrumento):
        sql = """SELECT p.* FROM piezometrocuerdas p INNER JOIN instrumentacion i ON p.id_piezometro = i.id_equipo WHERE i.id_instrumentacion = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idinstrumento,))
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar info cuerda: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlEliminarCuerdaVibrante(idinstrumento):
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # obtener info para eliminar data
            query_select = """SELECT * FROM instrumentacion WHERE id_instrumentacion = ? AND tipo_equipo = 'PIEZOMETROCUERDA';"""
            cursor.execute(query_select, (idinstrumento,))
            datapiezo = cursor.fetchone()
            if datapiezo:
                query = """DELETE FROM instrumentacion WHERE id_instrumentacion = ? AND tipo_equipo = 'PIEZOMETROCUERDA';"""
                cursor.execute(query, (idinstrumento,))
                conn.commit()
                if cursor.rowcount > 0:
                    return datapiezo
                else:
                    return None
            else:
                return None
        except Exception as e:
            print(f"Error al eliminar cuerda vibrante: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlEliminarCuerdaVibranteData(tabla, idpiezometro):
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
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlCambiarComponentePiezometrosManuales(idcomponente, nuevocomponente):
        sql = """UPDATE instrumentacion SET id_componente = ? WHERE id_componente = ? AND tipo_equipo = 'PIEZOMETROMANUAL';"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # guardar info
            query_select = """SELECT * FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'PIEZOMETROMANUAL';"""
            cur.execute(query_select, (idcomponente,))
            dataincli = cur.fetchall()
            if dataincli:
                cur.execute(sql, (nuevocomponente, idcomponente))
                conn.commit()
                return dataincli
            else:
                return None
        except Error as e:
            print("Error al cambiar componente casagrandes: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlEliminarPiezometrosManuales(idcomponente):
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # guardar en historial
            query_select = """SELECT * FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'PIEZOMETROMANUAL';"""
            cursor.execute(query_select, (idcomponente,))
            dataincli = cursor.fetchall()
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
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlEliminarDataPiezometrosManuales(tabla, manuales):
        placeholders = ','.join(['?' for _ in manuales])
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
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlObtenerInfoPiezometroManual(idinstrumento):
        sql = """SELECT p.* FROM piezometromanuales p INNER JOIN instrumentacion i ON p.id_piezometro = i.id_equipo WHERE i.id_instrumentacion = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idinstrumento,))
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar info casagrande: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlEliminarManualPiezometro(idinstrumento):
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # obtener info para eliminar data
            query_select = """SELECT * FROM instrumentacion WHERE id_instrumentacion = ? AND tipo_equipo = 'PIEZOMETROMANUAL';"""
            cursor.execute(query_select, (idinstrumento,))
            datapiezo = cursor.fetchone()
            if datapiezo:
                query = """DELETE FROM instrumentacion WHERE id_instrumentacion = ? AND tipo_equipo = 'PIEZOMETROMANUAL';"""
                cursor.execute(query, (idinstrumento,))
                conn.commit()
                if cursor.rowcount > 0:
                    return datapiezo
                else:
                    return None
            else:
                return None
        except Exception as e:
            print(f"Error al eliminar casagrande: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlEliminarPiezometroManualData(tabla, idpiezometro):
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
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlListarFechasPiezometroCuerda(tabla, idcomponente, idinstrumento, proyectoid):
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
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar fechas cuerda: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlListarFechasPiezometroManual(tabla, idcomponente, idinstrumento, proyectoid):
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
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar fechas manual: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlObtenerResumenCuerdaReporte(idproyecto, idcomponente, fechaini, fechafin):
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

            # Consulta principal modificada para usar los IDs filtrados
            sql = f"""
            SELECT p.id_piezometro,p.nombre_piezometro, strftime('%d/%m/%Y', '{fechaini}') AS fechaini,
            strftime('%d/%m/%Y', '{fechafin}') AS fechafin,
            COALESCE(
                (SELECT c2.nivel_cota
                FROM cotas_piezometricas c2
                WHERE c2.id_piezometro = d.id_piezometro
                AND c2.tipo_piezometro = 'PCV'
                AND c2.fecha_cota <= d.fecha_cuerda
                ORDER BY c2.fecha_cota DESC LIMIT 1),
                (SELECT c3.nivel_cota
                FROM cotas_piezometricas c3
                WHERE c3.id_piezometro = d.id_piezometro
                AND c3.tipo_piezometro = 'PCV'
                ORDER BY c3.fecha_cota ASC LIMIT 1)
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
            AND p.id_piezometro IN ({','.join(['?']*len(filtro_ids))})
            ORDER BY p.nombre_piezometro;
            """

            # Ejecutar la consulta principal con los parámetros adicionales
            cur.execute(sql, (idproyecto, fechaini, fechafin, fechaini, fechafin, *filtro_ids))
            row = cur.fetchall()

            if row:
                return row
            else:
                return None

        except Error as e:
            print("Error al resumir piezometros: " + str(e))
            return None

        finally:
            if conn:
                conn.close()
                
    def mdlObtenerResumenCasagrandeReporte(idproyecto, idcomponente, fechaini, fechafin):
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
            # Consulta principal modificada para usar los IDs filtrados
            sql = f"""
            WITH cte_cota AS (
                SELECT p.id_piezometro, p.nombre_piezometro, p.tipo_piezometro, d.fecha_piezometro, d.medida_piezometro, d.observacion_detalle,
                p.stickup_piezometro, p.elevacion_piezometro AS instalacion,
                COALESCE(
                    (SELECT c2.nivel_cota
                    FROM cotas_piezometricas c2
                    WHERE c2.id_piezometro = d.id_piezometro
                    AND c2.tipo_piezometro = 'PVC'
                    AND c2.fecha_cota <= d.fecha_piezometro
                    ORDER BY c2.fecha_cota DESC LIMIT 1),
                    (SELECT c3.nivel_cota
                    FROM cotas_piezometricas c3
                    WHERE c3.id_piezometro = d.id_piezometro
                    AND c3.tipo_piezometro = 'PVC'
                    ORDER BY c3.fecha_cota ASC LIMIT 1)
                ) AS elevacion,
                ROW_NUMBER() OVER (PARTITION BY p.id_piezometro ORDER BY d.fecha_piezometro DESC) AS row_num
                FROM piezometromanuales p INNER JOIN piezometromanual_detalle{idproyecto} d ON p.id_piezometro = d.id_piezometro
                WHERE p.id_proyecto = ? AND d.fecha_piezometro BETWEEN ? AND ? AND d.estado_manual = 1
                AND p.id_piezometro IN ({','.join(['?']*len(filtro_ids))})
            )
            SELECT id_piezometro,nombre_piezometro, strftime('%d/%m/%Y', '{fechaini}') AS fechaini,
            strftime('%d/%m/%Y', '{fechafin}') AS fechafin, elevacion,
            CASE
                WHEN tipo_piezometro = 1 THEN stickup_piezometro + elevacion - medida_piezometro
                ELSE medida_piezometro
            END AS nivel_agua, 'Operativo' AS estado
            FROM cte_cota WHERE row_num = 1 ORDER BY nombre_piezometro;
            """
            # Ejecutar la consulta principal con los parámetros adicionales
            cur.execute(sql, (idproyecto, fechaini, fechafin, *filtro_ids))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al resumir piezometros: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlTraerDataPiezometro(idinclinometro, tipo):
        sql = """SELECT i.id_instrumentacion, i.id_componente, c.nombre_componente FROM instrumentacion i
        INNER JOIN componentes c ON i.id_componente = c.id_componente
        WHERE i.id_equipo = ? AND i.tipo_equipo = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idinclinometro, tipo))
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al traer data piezometro: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlTraerCotaPiezometrica(idcota):
        sql = """SELECT * FROM cotas_piezometricas WHERE id_cota = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idcota,))
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al traer info cota piezometrica: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlCambiarPiezometroComponente(idinstrumento, nuevocomponente):
        sql = """UPDATE instrumentacion SET id_componente = ? WHERE id_instrumentacion = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (nuevocomponente, idinstrumento))
            conn.commit()
            return True
        except Error as e:
            print("Error al cambiar componente piezometro: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlTraerListaFormulas():
        sql = """SELECT * FROM formulas_piezometros;"""
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
            print("Error al traer formulas piezo: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlOmitirLecturaPiezometro(tabla,idPiezo,fecha,campo,campo_fecha):
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            query_update = f"""UPDATE {tabla} SET {campo} = 0 WHERE id_piezometro = ? AND {campo_fecha}=?;"""
            cursor.execute(query_update, (idPiezo,fecha))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al omitir lecturas del Piezometros: {e}")
            return False
        finally:
            if conn:
                conn.close()