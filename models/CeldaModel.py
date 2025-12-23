from services.security.apis.conexiones.connection import Connection
from datetime import datetime

class CeldaModel:
    
    def mdlObtenerFechaMaximaCeldas(tabla):
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
            print("Error al obtener fechas max celdas:", e)
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlListarCeldaProyecto(proyecto, idcomponente, idcelda):
        sql = f"""SELECT p.id_celda, p.nombre_celda, c.id_componente, p.este_celda, p.norte_celda,
        p.instalacion_celda FROM celdas p INNER JOIN instrumentacion t ON p.id_celda = t.id_equipo
        INNER JOIN componentes c ON t.id_componente = c.id_componente
        WHERE c.id_proyecto = ? AND t.id_equipo = ? AND c.id_componente = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyecto, idcelda, idcomponente))
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al consultar celda:", e)
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlRegistrarCelda(data, fecha):
        query = """INSERT INTO celdas (id_proyecto, nombre_celda, marca_celda, modelo_celda, serie_celda, rango_celda, 
        instalacion_celda, este_celda, norte_celda, fundacion_celda, frecuencia_inicial, temperatura_inicial, cf_celda, tk_celda)
        OUTPUT INSERTED.id_celda
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""
        valores = (
            data['proyecto'], data['nombre_celda'], data['marca_celda'], data['modelo_celda'], data['modelo_celda'], data['rango_celda'],
            data['cota_instalacion_celda'], data['coordenada_este_celda'], data['coordenada_norte_celda'], data['cota_fundacion_celda'],
            data['frecuencia_inicial'], data['temperatura_inicial_celda'], data['cf_celda'], data['tk_celda']
        )
        try:
            conexion = Connection.connectionDB()
            cursor = conexion.cursor()
            cursor.execute(query, valores)
            id_insertado = cursor.fetchone()[0]
            if id_insertado:
                inst = """INSERT INTO cotas_celdas (id_celda, fecha_cota, nivel_cota) VALUES (?, ?, ?);"""
                val = (id_insertado, fecha, data['cota_superficie_celda'])
                cursor.execute(inst, val)
            conexion.commit()
            return id_insertado
        except Exception as e:
            print(f"Error al registrar celda y cota: {e}")
            return None
        finally:
            if conexion:
                conexion.close()
    
    # Validar si existe celda con el mismo nombre
    def mdlComprobarExisteNombreCelda(proyecto, nombre):
        sql = """SELECT * FROM celdas WHERE id_proyecto = ? AND nombre_celda = ?;"""
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
            print("Error al comprobar celdas:", e)
            return False, None
        finally:
            if conn:
                conn.close()
    
    def mdlRegistrarInstrumentacionCelda(valores):
        query = """INSERT INTO instrumentacion (id_componente, tipo_equipo, nombre_equipo, id_equipo, tabla_equipo)
        VALUES (?, ?, ?, ?, ?);"""
        try:
            conexion = Connection.connectionDB()
            cursor = conexion.cursor()
            cursor.execute(query, valores)
            conexion.commit()
            return True
        except Exception as e:
            print(f"Error al registrar celda en instrumentacion: {e}")
            return False
        finally:
            if conexion:
                conexion.close()
    
    def mdlCalcularVelocidadDias(dias, tabla, idcomponente, listaceldas):
        placeholders = ', '.join(['?' for _ in listaceldas])
        params = [idcomponente] + listaceldas + [dias]
        sql = f"""WITH IncrementalCTE AS (
            SELECT t.id_instrumentacion, cl.nombre_celda, cd.fecha_detalle,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY cl.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 86400.0 AS dias,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY cl.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 3600.0 AS horas,
                cd.medida_calculada, cl.fundacion_celda,
                COALESCE(
                    (SELECT TOP 1 c2.nivel_cota FROM cotas_celdas c2 WHERE c2.id_celda = cl.id_celda 
                    AND c2.fecha_cota <= cd.fecha_detalle ORDER BY c2.fecha_cota DESC),
                    (SELECT TOP 1 c3.nivel_cota FROM cotas_celdas c3 WHERE c3.id_celda = cl.id_celda 
                    ORDER BY c3.fecha_cota ASC)
                ) AS superficie,
                COALESCE(cd.medida_calculada - LAG(cd.medida_calculada) OVER (PARTITION BY cl.nombre_celda ORDER BY cd.fecha_detalle ASC), 0) AS incremental,
                t.tipo_equipo, t.id_equipo
            FROM celdas cl INNER JOIN {tabla} cd ON cl.id_celda = cd.id_celda
            INNER JOIN instrumentacion t ON cl.id_celda = t.id_equipo
            INNER JOIN componentes c ON t.id_componente = c.id_componente
            WHERE c.id_componente = ? AND t.id_instrumentacion IN ({placeholders}) AND cd.estado_detalle = 1
        ),
        GroupedSummary AS (
            SELECT id_instrumentacion, nombre_celda, fecha_detalle, dias, horas, incremental,
            CAST(DATEDIFF(SECOND, (SELECT MIN(fecha_detalle) FROM {tabla}), fecha_detalle) / 86400.0 / ? AS INT) AS grupo_dias,
            fundacion_celda, superficie, tipo_equipo, id_equipo
            FROM IncrementalCTE
        ),
        AggregatedSummary AS (
            SELECT id_instrumentacion, nombre_celda, grupo_dias, MAX(fecha_detalle) AS ultima_fecha_grupo, MAX(dias) AS dias, MAX(horas) AS horas,
            SUM(incremental) AS velocidad_metros, MAX(fundacion_celda) AS fundacion_celda, MAX(superficie) AS superficie, 
            MAX(tipo_equipo) AS tipo_equipo, MAX(id_equipo) AS id_equipo
            FROM GroupedSummary GROUP BY id_instrumentacion, nombre_celda, grupo_dias
        )
        SELECT id_instrumentacion, nombre_celda, ultima_fecha_grupo, dias, horas, velocidad_metros, velocidad_metros * 100 AS velocidad_cm,
        velocidad_metros * 1000 AS velocidad_mm, ABS(velocidad_metros) AS velocidad_metros_positivo,
        ABS(velocidad_metros * 100) AS velocidad_cm_positivo, ABS(velocidad_metros * 1000) AS velocidad_mm_positivo,
        fundacion_celda, superficie, tipo_equipo, id_equipo
        FROM AggregatedSummary ORDER BY nombre_celda ASC, ultima_fecha_grupo ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return rows if rows else None
        except Exception as e:
            print("Error al obtener velocidad dias celdas:", e)
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlCalcularVelocidadFechasDias(dias, tabla, idcomponente, listaceldas, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in listaceldas])
        params = [idcomponente] + listaceldas + [fechaini] + [fechafin] + [dias]
        sql = f"""WITH IncrementalCTE AS (
            SELECT t.id_instrumentacion, cl.nombre_celda, cd.fecha_detalle,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY cl.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 86400.0 AS dias,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY cl.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 3600.0 AS horas,
                cd.medida_calculada, cl.fundacion_celda,
                COALESCE(
                    (SELECT TOP 1 c2.nivel_cota FROM cotas_celdas c2 WHERE c2.id_celda = cl.id_celda 
                    AND c2.fecha_cota <= cd.fecha_detalle ORDER BY c2.fecha_cota DESC),
                    (SELECT TOP 1 c3.nivel_cota FROM cotas_celdas c3 WHERE c3.id_celda = cl.id_celda 
                    ORDER BY c3.fecha_cota ASC)
                ) AS superficie,
                COALESCE(cd.medida_calculada - LAG(cd.medida_calculada) OVER (PARTITION BY cl.nombre_celda ORDER BY cd.fecha_detalle ASC), 0) AS incremental,
                t.tipo_equipo, t.id_equipo
            FROM celdas cl INNER JOIN {tabla} cd ON cl.id_celda = cd.id_celda
            INNER JOIN instrumentacion t ON cl.id_celda = t.id_equipo
            INNER JOIN componentes c ON t.id_componente = c.id_componente
            WHERE c.id_componente = ? AND t.id_instrumentacion IN ({placeholders})
            AND cd.estado_detalle = 1 AND cd.fecha_detalle BETWEEN ? AND ?
        ),
        GroupedSummary AS (
            SELECT id_instrumentacion, nombre_celda, fecha_detalle, dias, horas, incremental,
            CAST(DATEDIFF(SECOND, (SELECT MIN(fecha_detalle) FROM {tabla}), fecha_detalle) / 86400.0 / ? AS INT) AS grupo_dias,
            fundacion_celda, superficie, tipo_equipo, id_equipo
            FROM IncrementalCTE
        ),
        AggregatedSummary AS (
            SELECT id_instrumentacion, nombre_celda, grupo_dias, MAX(fecha_detalle) AS ultima_fecha_grupo, MAX(dias) AS dias, MAX(horas) AS horas,
            SUM(incremental) AS velocidad_metros, MAX(fundacion_celda) AS fundacion_celda, MAX(superficie) AS superficie,
            MAX(tipo_equipo) AS tipo_equipo, MAX(id_equipo) AS id_equipo
            FROM GroupedSummary GROUP BY id_instrumentacion, nombre_celda, grupo_dias
        )
        SELECT id_instrumentacion, nombre_celda, ultima_fecha_grupo, dias, horas, velocidad_metros, velocidad_metros * 100 AS velocidad_cm,
        velocidad_metros * 1000 AS velocidad_mm, ABS(velocidad_metros) AS velocidad_metros_positivo,
        ABS(velocidad_metros * 100) AS velocidad_cm_positivo, ABS(velocidad_metros * 1000) AS velocidad_mm_positivo,
        fundacion_celda, superficie, tipo_equipo, id_equipo
        FROM AggregatedSummary ORDER BY nombre_celda ASC, ultima_fecha_grupo ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return rows if rows else None
        except Exception as e:
            print("Error al obtener velocidad fechas dias celdas:", e)
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlCalcularVelocidadMes(tabla, idcomponente, listaceldas):
        placeholders = ', '.join(['?' for _ in listaceldas])
        params = [idcomponente] + listaceldas
        sql = f"""WITH IncrementalCTE AS (
            SELECT t.id_instrumentacion, cl.nombre_celda, cd.fecha_detalle,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY cl.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 86400.0 AS dias,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY cl.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 3600.0 AS horas,
                cd.medida_calculada, cl.fundacion_celda,
                COALESCE(
                    (SELECT TOP 1 c2.nivel_cota FROM cotas_celdas c2 WHERE c2.id_celda = cl.id_celda 
                    AND c2.fecha_cota <= cd.fecha_detalle ORDER BY c2.fecha_cota DESC),
                    (SELECT TOP 1 c3.nivel_cota FROM cotas_celdas c3 WHERE c3.id_celda = cl.id_celda 
                    ORDER BY c3.fecha_cota ASC)
                ) AS superficie,
                COALESCE(cd.medida_calculada - LAG(cd.medida_calculada) OVER (PARTITION BY cl.nombre_celda ORDER BY cd.fecha_detalle ASC), 0) AS incremental,
                t.tipo_equipo, t.id_equipo
            FROM celdas cl INNER JOIN {tabla} cd ON cl.id_celda = cd.id_celda
            INNER JOIN instrumentacion t ON cl.id_celda = t.id_equipo
            INNER JOIN componentes c ON t.id_componente = c.id_componente
            WHERE c.id_componente = ? AND t.id_instrumentacion IN ({placeholders}) AND cd.estado_detalle = 1
        ),
        MonthlySummary AS (
            SELECT id_instrumentacion, nombre_celda, FORMAT(CAST(fecha_detalle AS DATE), 'yyyy-MM') AS mes, fecha_detalle, dias, horas, incremental,
                SUM(incremental) OVER (PARTITION BY nombre_celda, FORMAT(CAST(fecha_detalle AS DATE), 'yyyy-MM')) AS velocidad_metros,
                fundacion_celda, superficie,
                ROW_NUMBER() OVER (PARTITION BY nombre_celda, FORMAT(CAST(fecha_detalle AS DATE), 'yyyy-MM') ORDER BY fecha_detalle DESC) AS rn,
                tipo_equipo, id_equipo
            FROM IncrementalCTE
        )
        SELECT id_instrumentacion, nombre_celda, fecha_detalle AS ultima_fecha_mes, dias, horas, velocidad_metros,
        velocidad_metros * 100 AS velocidad_cm, velocidad_metros * 1000 AS velocidad_mm,
        ABS(velocidad_metros) AS velocidad_metros_positivo, ABS(velocidad_metros * 100) AS velocidad_cm_positivo,
        ABS(velocidad_metros * 1000) AS velocidad_mm_positivo, fundacion_celda, superficie, tipo_equipo, id_equipo
        FROM MonthlySummary
        WHERE rn = 1
        ORDER BY nombre_celda ASC, ultima_fecha_mes ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return rows
            else:
                return None
        except Exception as e:
            print("Error al obtener velocidad mensual celda:", e)
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlCalcularVelocidadFechasMes(tabla, idcomponente, listaceldas, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in listaceldas])
        params = [idcomponente] + listaceldas + [fechaini] + [fechafin]
        sql = f"""WITH IncrementalCTE AS (
            SELECT t.id_instrumentacion, cl.nombre_celda, cd.fecha_detalle,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY cl.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 86400.0 AS dias,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY cl.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 3600.0 AS horas,
                cd.medida_calculada, cl.fundacion_celda,
                COALESCE(
                    (SELECT TOP 1 c2.nivel_cota FROM cotas_celdas c2 WHERE c2.id_celda = cl.id_celda 
                    AND c2.fecha_cota <= cd.fecha_detalle ORDER BY c2.fecha_cota DESC),
                    (SELECT TOP 1 c3.nivel_cota FROM cotas_celdas c3 WHERE c3.id_celda = cl.id_celda 
                    ORDER BY c3.fecha_cota ASC)
                ) AS superficie,
                COALESCE(cd.medida_calculada - LAG(cd.medida_calculada) OVER (PARTITION BY cl.nombre_celda ORDER BY cd.fecha_detalle ASC), 0) AS incremental,
                t.tipo_equipo, t.id_equipo
            FROM celdas cl INNER JOIN {tabla} cd ON cl.id_celda = cd.id_celda
            INNER JOIN instrumentacion t ON cl.id_celda = t.id_equipo
            INNER JOIN componentes c ON t.id_componente = c.id_componente
            WHERE c.id_componente = ? AND t.id_instrumentacion IN ({placeholders})
            AND cd.estado_detalle = 1 AND cd.fecha_detalle BETWEEN ? AND ?
        ),
        MonthlySummary AS (
            SELECT id_instrumentacion, nombre_celda, FORMAT(CAST(fecha_detalle AS DATE), 'yyyy-MM') AS mes, fecha_detalle, dias, horas, incremental,
                SUM(incremental) OVER (PARTITION BY nombre_celda, FORMAT(CAST(fecha_detalle AS DATE), 'yyyy-MM')) AS velocidad_metros,
                fundacion_celda, superficie,
                ROW_NUMBER() OVER (PARTITION BY nombre_celda, FORMAT(CAST(fecha_detalle AS DATE), 'yyyy-MM') ORDER BY fecha_detalle DESC) AS rn,
                tipo_equipo, id_equipo
            FROM IncrementalCTE
        )
        SELECT id_instrumentacion, nombre_celda, fecha_detalle AS ultima_fecha_mes, dias, horas, velocidad_metros,
            velocidad_metros * 100 AS velocidad_cm, velocidad_metros * 1000 AS velocidad_mm,
            ABS(velocidad_metros) AS velocidad_metros_positivo, ABS(velocidad_metros * 100) AS velocidad_cm_positivo,
            ABS(velocidad_metros * 1000) AS velocidad_mm_positivo, fundacion_celda, superficie, tipo_equipo, id_equipo
        FROM MonthlySummary
        WHERE rn = 1
        ORDER BY nombre_celda ASC, ultima_fecha_mes ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return rows
            else:
                return None
        except Exception as e:
            print("Error al obtener velocidad mensual celda:", e)
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlObtenerAsentamientoCota(tabla, idcomponente, listaceldas):
        placeholders = ', '.join(['?' for _ in listaceldas])
        params = [idcomponente] + listaceldas
        sql = f"""SELECT t.id_instrumentacion, cl.nombre_celda, cd.fecha_detalle,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY cl.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 86400.0 AS dias,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY cl.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 3600.0 AS horas,
            cl.instalacion_celda - ABS(cd.medida_calculada) AS cota_piezometrica, cl.fundacion_celda,
            COALESCE(
                (SELECT TOP 1 c2.nivel_cota FROM cotas_celdas c2 WHERE c2.id_celda = cl.id_celda 
                AND c2.fecha_cota <= cd.fecha_detalle ORDER BY c2.fecha_cota DESC),
                (SELECT TOP 1 c3.nivel_cota FROM cotas_celdas c3 WHERE c3.id_celda = cl.id_celda 
                ORDER BY c3.fecha_cota ASC)
            ) AS superficie, t.tipo_equipo, t.id_equipo
        FROM celdas cl INNER JOIN {tabla} cd ON cl.id_celda = cd.id_celda
        INNER JOIN instrumentacion t ON cl.id_celda = t.id_equipo
        INNER JOIN componentes c ON t.id_componente = c.id_componente
        WHERE c.id_componente = ? AND t.id_instrumentacion IN ({placeholders}) AND cd.estado_detalle = 1
        ORDER BY cl.nombre_celda ASC, cd.fecha_detalle ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return rows
            else:
                return None
        except Exception as e:
            print("Error al obtener asentamiento cota:", e)
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlObtenerAsentamientoFechasCota(tabla, idcomponente, listaceldas, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in listaceldas])
        params = [idcomponente] + listaceldas + [fechaini] + [fechafin]
        sql = f"""SELECT t.id_instrumentacion, cl.nombre_celda, cd.fecha_detalle,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY cl.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 86400.0 AS dias,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY cl.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 3600.0 AS horas,
            cl.instalacion_celda - ABS(cd.medida_calculada) AS cota_piezometrica, cl.fundacion_celda,
            COALESCE(
                (SELECT TOP 1 c2.nivel_cota FROM cotas_celdas c2 WHERE c2.id_celda = cl.id_celda 
                AND c2.fecha_cota <= cd.fecha_detalle ORDER BY c2.fecha_cota DESC),
                (SELECT TOP 1 c3.nivel_cota FROM cotas_celdas c3 WHERE c3.id_celda = cl.id_celda 
                ORDER BY c3.fecha_cota ASC)
            ) AS superficie, t.tipo_equipo, t.id_equipo
        FROM celdas cl INNER JOIN {tabla} cd ON cl.id_celda = cd.id_celda
        INNER JOIN instrumentacion t ON cl.id_celda = t.id_equipo
        INNER JOIN componentes c ON t.id_componente = c.id_componente
        WHERE c.id_componente = ? AND t.id_instrumentacion IN ({placeholders})
        AND cd.estado_detalle = 1 AND cd.fecha_detalle BETWEEN ? AND ?
        ORDER BY cl.nombre_celda ASC, cd.fecha_detalle ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return rows
            else:
                return None
        except Exception as e:
            print("Error al obtener asentamiento cota:", e)
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlCalcularAsentamientoIncremental(tabla, idcomponente, listaceldas, unidadmedida):
        placeholders = ', '.join(['?' for _ in listaceldas])
        params = [unidadmedida] + [idcomponente] + listaceldas
        sql = f"""SELECT t.id_instrumentacion, cl.nombre_celda, cd.fecha_detalle,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY cl.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 86400.0 AS dias,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY cl.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 3600.0 AS horas,
            COALESCE(cd.medida_calculada - LAG(cd.medida_calculada) OVER (PARTITION BY cl.nombre_celda ORDER BY cd.fecha_detalle ASC), 0) * ? AS incremental, cl.fundacion_celda,
            COALESCE(
                (SELECT TOP 1 c2.nivel_cota FROM cotas_celdas c2 WHERE c2.id_celda = cl.id_celda 
                AND c2.fecha_cota <= cd.fecha_detalle ORDER BY c2.fecha_cota DESC),
                (SELECT TOP 1 c3.nivel_cota FROM cotas_celdas c3 WHERE c3.id_celda = cl.id_celda 
                ORDER BY c3.fecha_cota ASC)
            ) AS superficie, t.tipo_equipo, t.id_equipo
        FROM celdas cl INNER JOIN {tabla} cd ON cl.id_celda = cd.id_celda
        INNER JOIN instrumentacion t ON cl.id_celda = t.id_equipo
        INNER JOIN componentes c ON t.id_componente = c.id_componente
        WHERE c.id_componente = ? AND t.id_instrumentacion IN ({placeholders}) AND cd.estado_detalle = 1
        ORDER BY cl.nombre_celda ASC, cd.fecha_detalle ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return rows
            else:
                return None
        except Exception as e:
            print("Error al obtener asentamiento incremental:", e)
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlCalcularAsentamientoFechasIncremental(tabla, idcomponente, listaceldas, fechaini, fechafin, unidadmedida):
        placeholders = ', '.join(['?' for _ in listaceldas])
        params = [unidadmedida] + [idcomponente] + listaceldas + [fechaini] + [fechafin]
        sql = f"""SELECT t.id_instrumentacion, cl.nombre_celda, cd.fecha_detalle,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY cl.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 86400.0 AS dias,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY cl.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 3600.0 AS horas,
            COALESCE(cd.medida_calculada - LAG(cd.medida_calculada) OVER (PARTITION BY cl.nombre_celda ORDER BY cd.fecha_detalle ASC), 0) * ? AS incremental, cl.fundacion_celda,
            COALESCE(
                (SELECT TOP 1 c2.nivel_cota FROM cotas_celdas c2 WHERE c2.id_celda = cl.id_celda 
                AND c2.fecha_cota <= cd.fecha_detalle ORDER BY c2.fecha_cota DESC),
                (SELECT TOP 1 c3.nivel_cota FROM cotas_celdas c3 WHERE c3.id_celda = cl.id_celda 
                ORDER BY c3.fecha_cota ASC)
            ) AS superficie, t.tipo_equipo, t.id_equipo
        FROM celdas cl INNER JOIN {tabla} cd ON cl.id_celda = cd.id_celda
        INNER JOIN instrumentacion t ON cl.id_celda = t.id_equipo
        INNER JOIN componentes c ON t.id_componente = c.id_componente
        WHERE c.id_componente = ? AND t.id_instrumentacion IN ({placeholders})
        AND cd.estado_detalle = 1 AND cd.fecha_detalle BETWEEN ? AND ?
        ORDER BY cl.nombre_celda ASC, cd.fecha_detalle ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return rows
            else:
                return None
        except Exception as e:
            print("Error al obtener asentamiento incremental:", e)
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlObtenerAsentamientoAcumulado(tabla, idcomponente, listaceldas, unidadmedida):
        placeholders = ', '.join(['?' for _ in listaceldas])
        params = [unidadmedida] + [idcomponente] + listaceldas
        sql = f"""SELECT t.id_instrumentacion, cl.nombre_celda, cd.fecha_detalle,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY cl.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 86400.0 AS dias,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY cl.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 3600.0 AS horas,
            cd.medida_calculada * ? AS medida_calculada, cl.fundacion_celda,
            COALESCE(
                (SELECT TOP 1 c2.nivel_cota FROM cotas_celdas c2 WHERE c2.id_celda = cl.id_celda 
                AND c2.fecha_cota <= cd.fecha_detalle ORDER BY c2.fecha_cota DESC),
                (SELECT TOP 1 c3.nivel_cota FROM cotas_celdas c3 WHERE c3.id_celda = cl.id_celda 
                ORDER BY c3.fecha_cota ASC)
            ) AS superficie, t.tipo_equipo, t.id_equipo
        FROM celdas cl INNER JOIN {tabla} cd ON cl.id_celda = cd.id_celda
        INNER JOIN instrumentacion t ON cl.id_celda = t.id_equipo
        INNER JOIN componentes c ON t.id_componente = c.id_componente
        WHERE c.id_componente = ? AND t.id_instrumentacion IN ({placeholders}) AND cd.estado_detalle = 1
        ORDER BY cl.nombre_celda ASC, cd.fecha_detalle ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return rows
            else:
                return None
        except Exception as e:
            print("Error al obtener asentamiento acumulado:", e)
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlObtenerAsentamientoFechasAcumulado(tabla, idcomponente, listaceldas, fechaini, fechafin, unidadmedida):
        placeholders = ', '.join(['?' for _ in listaceldas])
        params = [unidadmedida] + [idcomponente] + listaceldas + [fechaini] + [fechafin]
        sql = f"""SELECT t.id_instrumentacion, cl.nombre_celda, cd.fecha_detalle,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY cl.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 86400.0 AS dias,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY cl.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 3600.0 AS horas,
            cd.medida_calculada * ? AS medida_calculada, cl.fundacion_celda,
            COALESCE(
                (SELECT TOP 1 c2.nivel_cota FROM cotas_celdas c2 WHERE c2.id_celda = cl.id_celda 
                AND c2.fecha_cota <= cd.fecha_detalle ORDER BY c2.fecha_cota DESC),
                (SELECT TOP 1 c3.nivel_cota FROM cotas_celdas c3 WHERE c3.id_celda = cl.id_celda 
                ORDER BY c3.fecha_cota ASC)
            ) AS superficie, t.tipo_equipo, t.id_equipo
        FROM celdas cl INNER JOIN {tabla} cd ON cl.id_celda = cd.id_celda
        INNER JOIN instrumentacion t ON cl.id_celda = t.id_equipo
        INNER JOIN componentes c ON t.id_componente = c.id_componente
        WHERE c.id_componente = ? AND t.id_instrumentacion IN ({placeholders})
        AND cd.estado_detalle = 1 AND cd.fecha_detalle BETWEEN ? AND ?
        ORDER BY cl.nombre_celda ASC, cd.fecha_detalle ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return rows
            else:
                return None
        except Exception as e:
            print("Error al obtener asentamiento acumulado:", e)
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlObtenerAsentamientoFrecuencia(tabla, idcomponente, listaceldas):
        placeholders = ', '.join(['?' for _ in listaceldas])
        params = [idcomponente] + listaceldas
        sql = f"""SELECT t.id_instrumentacion, cl.nombre_celda, cd.fecha_detalle,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY cl.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 86400.0 AS dias,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY cl.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 3600.0 AS horas,
            cd.frecuencia_hz, cl.fundacion_celda,
            COALESCE(
                (SELECT TOP 1 c2.nivel_cota FROM cotas_celdas c2 WHERE c2.id_celda = cl.id_celda 
                AND c2.fecha_cota <= cd.fecha_detalle ORDER BY c2.fecha_cota DESC),
                (SELECT TOP 1 c3.nivel_cota FROM cotas_celdas c3 WHERE c3.id_celda = cl.id_celda 
                ORDER BY c3.fecha_cota ASC)
            ) AS superficie, t.tipo_equipo, t.id_equipo
        FROM celdas cl INNER JOIN {tabla} cd ON cl.id_celda = cd.id_celda
        INNER JOIN instrumentacion t ON cl.id_celda = t.id_equipo
        INNER JOIN componentes c ON t.id_componente = c.id_componente
        WHERE c.id_componente = ? AND t.id_instrumentacion IN ({placeholders}) AND cd.estado_detalle = 1
        ORDER BY cl.nombre_celda ASC, cd.fecha_detalle ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return rows
            else:
                return None
        except Exception as e:
            print("Error al obtener frecuencia celdas:", e)
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlObtenerAsentamientoFechasFrecuencia(tabla, idcomponente, listaceldas, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in listaceldas])
        params = [idcomponente] + listaceldas + [fechaini] + [fechafin]
        sql = f"""SELECT t.id_instrumentacion, cl.nombre_celda, cd.fecha_detalle,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY cl.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 86400.0 AS dias,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY cl.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 3600.0 AS horas,
            cd.frecuencia_hz, cl.fundacion_celda,
            COALESCE(
                (SELECT TOP 1 c2.nivel_cota FROM cotas_celdas c2 WHERE c2.id_celda = cl.id_celda 
                AND c2.fecha_cota <= cd.fecha_detalle ORDER BY c2.fecha_cota DESC),
                (SELECT TOP 1 c3.nivel_cota FROM cotas_celdas c3 WHERE c3.id_celda = cl.id_celda 
                ORDER BY c3.fecha_cota ASC)
            ) AS superficie, t.tipo_equipo, t.id_equipo
        FROM celdas cl INNER JOIN {tabla} cd ON cl.id_celda = cd.id_celda
        INNER JOIN instrumentacion t ON cl.id_celda = t.id_equipo
        INNER JOIN componentes c ON t.id_componente = c.id_componente
        WHERE c.id_componente = ? AND t.id_instrumentacion IN ({placeholders})
        AND cd.estado_detalle = 1 AND cd.fecha_detalle BETWEEN ? AND ?
        ORDER BY cl.nombre_celda ASC, cd.fecha_detalle ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return rows
            else:
                return None
        except Exception as e:
            print("Error al obtener frecuencia celdas fechas:", e)
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlObtenerAsentamientoTemperatura(tabla, idcomponente, listaceldas):
        placeholders = ', '.join(['?' for _ in listaceldas])
        params = [idcomponente] + listaceldas
        sql = f"""SELECT t.id_instrumentacion, cl.nombre_celda, cd.fecha_detalle,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY cl.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 86400.0 AS dias,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY cl.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 3600.0 AS horas,
            cd.temperatura_detalle, cl.fundacion_celda,
            COALESCE(
                (SELECT TOP 1 c2.nivel_cota FROM cotas_celdas c2 WHERE c2.id_celda = cl.id_celda 
                AND c2.fecha_cota <= cd.fecha_detalle ORDER BY c2.fecha_cota DESC),
                (SELECT TOP 1 c3.nivel_cota FROM cotas_celdas c3 WHERE c3.id_celda = cl.id_celda 
                ORDER BY c3.fecha_cota ASC)
            ) AS superficie, t.tipo_equipo, t.id_equipo
        FROM celdas cl INNER JOIN {tabla} cd ON cl.id_celda = cd.id_celda
        INNER JOIN instrumentacion t ON cl.id_celda = t.id_equipo
        INNER JOIN componentes c ON t.id_componente = c.id_componente
        WHERE c.id_componente = ? AND t.id_instrumentacion IN ({placeholders}) AND cd.estado_detalle = 1
        ORDER BY cl.nombre_celda ASC, cd.fecha_detalle ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return rows
            else:
                return None
        except Exception as e:
            print("Error al obtener temperatura celdas:", e)
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlObtenerAsentamientoFechasTemperatura(tabla, idcomponente, listaceldas, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in listaceldas])
        params = [idcomponente] + listaceldas + [fechaini] + [fechafin]
        sql = f"""SELECT t.id_instrumentacion, cl.nombre_celda, cd.fecha_detalle,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY cl.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 86400.0 AS dias,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY cl.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 3600.0 AS horas,
            cd.temperatura_detalle, cl.fundacion_celda,
            COALESCE(
                (SELECT TOP 1 c2.nivel_cota FROM cotas_celdas c2 WHERE c2.id_celda = cl.id_celda 
                AND c2.fecha_cota <= cd.fecha_detalle ORDER BY c2.fecha_cota DESC),
                (SELECT TOP 1 c3.nivel_cota FROM cotas_celdas c3 WHERE c3.id_celda = cl.id_celda 
                ORDER BY c3.fecha_cota ASC)
            ) AS superficie, t.tipo_equipo, t.id_equipo
        FROM celdas cl INNER JOIN {tabla} cd ON cl.id_celda = cd.id_celda
        INNER JOIN instrumentacion t ON cl.id_celda = t.id_equipo
        INNER JOIN componentes c ON t.id_componente = c.id_componente
        WHERE c.id_componente = ? AND t.id_instrumentacion IN ({placeholders})
        AND cd.estado_detalle = 1 AND cd.fecha_detalle BETWEEN ? AND ?
        ORDER BY cl.nombre_celda ASC, cd.fecha_detalle ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return rows
            else:
                return None
        except Exception as e:
            print("Error al obtener temperatura celdas fechas:", e)
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlActualizarLecturaCelda(tabla, data, idproyecto, username, nombres):
        try:
            conexion = Connection.connectionDB()
            cursor = conexion.cursor()
            # guardar en historial
            query_select = f"""SELECT fecha_detalle, frecuencia_digits, frecuencia_hz, temperatura_detalle, medida_calculada,
            observacion_detalle, id_detalle FROM {tabla} WHERE id_detalle = ?;"""
            cursor.execute(query_select, (data[-1],))
            datos_anteriores = cursor.fetchone()
            if datos_anteriores:
                fecha_cambio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                accion = "update"
                cambios = f"Antiguos: {datos_anteriores}, Nuevos: {data}"
                query_historial = """INSERT INTO historial (idproyecto, fecha, accion, tabla, cambios, usuario, nombres)
                VALUES (?, ?, ?, ?, ?, ?, ?);"""
                cursor.execute(query_historial, (idproyecto, fecha_cambio, accion, tabla, cambios, username, nombres))
            # actualizar celda
            query = f"""UPDATE {tabla} SET fecha_detalle = ?, frecuencia_digits = ?, frecuencia_hz = ?, temperatura_detalle = ?,
            medida_calculada = ?, observacion_detalle = ? WHERE id_detalle = ?;"""
            cursor.execute(query, data)
            conexion.commit()
            return True
        except Exception as e:
            print(f"Error al actualizar lectura celda: {e}")
            return False
        finally:
            if conexion:
                conexion.close()
    
    def mdlCambiarEstadoLecturaCelda(tabla, iddetalle):
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            query_update = f"""UPDATE {tabla} SET estado_detalle = CASE estado_detalle WHEN 1 THEN 0 ELSE 1 END
            WHERE id_detalle = ?;"""
            cursor.execute(query_update, (iddetalle,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error al cambiar el estado de celda: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlCambiarEstadoLecturaCeldaBloque(tabla, listacodigos):
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            placeholders = ','.join(['?'] * len(listacodigos))
            query_update = f"""UPDATE {tabla} SET estado_detalle = CASE estado_detalle WHEN 1 THEN 0 ELSE 1 END
            WHERE id_detalle IN ({placeholders});"""
            cursor.execute(query_update, listacodigos)
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error al cambiar el estado de las celdas: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlEliminarLecturaCelda(tabla, idcelda, idproyecto, username, nombres):
        sql = f"""DELETE FROM {tabla} WHERE id_detalle = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # guardar en historial
            query_select = f"""SELECT * FROM {tabla} WHERE id_detalle = ?;"""
            cur.execute(query_select, (idcelda,))
            datos_anteriores = cur.fetchone()
            if datos_anteriores:
                fecha_cambio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                accion = "delete"
                cambios = f"Datos: {datos_anteriores}"
                query_historial = """INSERT INTO historial (idproyecto, fecha, accion, tabla, cambios, usuario, nombres)
                VALUES (?, ?, ?, ?, ?, ?, ?);"""
                cur.execute(query_historial, (idproyecto, fecha_cambio, accion, tabla, cambios, username, nombres))
            # eliminar lectura celda
            cur.execute(sql, (idcelda,))
            conn.commit()
            if cur.rowcount > 0:
                return True
            else:
                return False
        except Exception as e:
            print("Error al eliminar lectura celda:", e)
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlEliminarLecturasBloqueCelda(tabla, iddetalles, idproyecto, username, nombres):
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
            # eliminar lecturas celdas
            cur.execute(sql, iddetalles)
            conn.commit()
            if cur.rowcount > 0:
                return True
            else:
                return False
        except Exception as e:
            print("Error al eliminar lecturas celdas:", e)
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlObtenerCeldasAsentamiento(proyecto):
        try:
            conn = Connection.connectionDB()
            sql = """SELECT id_celda, nombre_celda FROM celdas WHERE id_proyecto = ?"""
            cur = conn.cursor()
            cur.execute(sql, (proyecto,))
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
                
    def mdlRegistrarDataCelda(proyectoid, data, idsceldas):
        table_name = f"celda_detalle{proyectoid}"
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # Crear tabla si no existe (SQL Server)
            cursor.execute(f"""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='{table_name}' AND xtype='U')
                CREATE TABLE [{table_name}] (
                    [id_detalle] INT NOT NULL IDENTITY(1,1),
                    [id_celda] INT NOT NULL,
                    [fecha_detalle] VARCHAR(50) NOT NULL,
                    [frecuencia_digits] DECIMAL(18,6),
                    [frecuencia_hz] DECIMAL(18,6),
                    [temperatura_detalle] DECIMAL(18,6),
                    [medida_calculada] DECIMAL(18,6),
                    [observacion_detalle] VARCHAR(MAX),
                    [estado_detalle] INT DEFAULT 1,
                    PRIMARY KEY([id_detalle])
                );
            """)
            conn.commit()
            # Crear un conjunto de tuplas con los valores de fecha y hora para comparar los registros existentes
            placeholders = ','.join(['?'] * len(idsceldas))
            cursor.execute(f"SELECT id_celda, fecha_detalle FROM [{table_name}] WHERE id_celda IN ({placeholders});", list(idsceldas))
            existen_celdas = set([(row[0], row[1]) for row in cursor.fetchall()])
            lote_registros = []
            contador = 0
            for fila in data:
                id_celda = fila[0]
                fecha_original = fila[1]
                hora_original = fila[2]
                fecha_hora_nueva = fecha_original + " " + hora_original
                # Verifica si el registro no existe en el conjunto
                if (id_celda, fecha_hora_nueva) not in existen_celdas:
                    datito = []
                    datito.append(id_celda)
                    datito.append(fecha_hora_nueva)
                    datito.append(fila[3])  # frecuencia digits
                    datito.append(fila[4])  # frecuencia hz
                    datito.append(fila[5])  # temperatura
                    datito.append(fila[6])  # data calculada MCA
                    datito.append(fila[7])  # Observacion
                    lote_registros.append(datito)
                    contador += 1
                if contador % 1000 == 0 and lote_registros:
                    cursor.executemany(f"""INSERT INTO [{table_name}] (id_celda, fecha_detalle, frecuencia_digits, frecuencia_hz, temperatura_detalle, medida_calculada, observacion_detalle) VALUES (?, ?, ?, ?, ?, ?, ?);""", lote_registros)
                    lote_registros = []
            if lote_registros:
                cursor.executemany(f"""INSERT INTO [{table_name}] (id_celda, fecha_detalle, frecuencia_digits, frecuencia_hz, temperatura_detalle, medida_calculada, observacion_detalle) VALUES (?, ?, ?, ?, ?, ?, ?);""", lote_registros)
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print("Error al guardar las celdas:", e)
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlCambiarComponenteCeldas(idcomponente, nuevocomponente):
        sql = """UPDATE instrumentacion SET id_componente = ? WHERE id_componente = ? AND tipo_equipo = 'CELDA';"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # guardar info
            query_select = """SELECT * FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'CELDA';"""
            cur.execute(query_select, (idcomponente,))
            dataceldas = cur.fetchall()
            if dataceldas:
                cur.execute(sql, (nuevocomponente, idcomponente))
                conn.commit()
                return dataceldas
            else:
                return None
        except Exception as e:
            print("Error al cambiar componente celdas:", e)
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlEliminarCeldas(idcomponente):
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # obtener info
            query_select = """SELECT * FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'CELDA';"""
            cursor.execute(query_select, (idcomponente,))
            datacelda = cursor.fetchall()
            if datacelda:
                query = """DELETE FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'CELDA';"""
                cursor.execute(query, (idcomponente,))
                conn.commit()
                if cursor.rowcount > 0:
                    return datacelda
                else:
                    return None
            else:
                return None
        except Exception as e:
            print(f"Error al eliminar celdas: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlEliminarDataCeldas(tabla, terrenos):
        placeholders = ','.join(['?' for _ in terrenos])
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # eliminar data
            query_delete = f"""DELETE FROM {tabla} WHERE id_celda IN ({placeholders});"""
            cursor.execute(query_delete, terrenos)
            rows_data = cursor.rowcount
            if rows_data > 0:
                stmt_delete = f"DELETE FROM celdas WHERE id_celda IN ({placeholders});"
                cursor.execute(stmt_delete, terrenos)
                rows_delete = cursor.rowcount
                conn.commit()
                return rows_delete > 0
            else:
                conn.rollback()
                return False
        except Exception as e:
            print(f"Error al eliminar data celdas: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlObtenerInfoCelda(idinstrumento):
        sql = """SELECT c.* FROM celdas c INNER JOIN instrumentacion i ON c.id_celda = i.id_equipo WHERE i.id_instrumentacion = ?;"""
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
            print("Error al consultar info celda:", e)
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlActualizarCelda(data):
        query = """UPDATE celdas SET nombre_celda = ?, marca_celda = ?, modelo_celda = ?, rango_celda = ?, instalacion_celda = ?,
        este_celda = ?, norte_celda = ?, fundacion_celda = ?, frecuencia_inicial = ?, temperatura_inicial = ?, cf_celda = ?,
        tk_celda = ? WHERE id_celda = ?;"""
        valores = (
            data['nombre_celda'], data['marca_celda'], data['modelo_celda'], data['rango_celda'], data['cota_instalacion_celda'],
            data['coordenada_este_celda'], data['coordenada_norte_celda'], data['cota_fundacion_celda'], data['frecuencia_inicial'],
            data['temperatura_inicial_celda'], data['cf_celda'], data['tk_celda'], data['idcelda']
        )
        try:
            conexion = Connection.connectionDB()
            cursor = conexion.cursor()
            cursor.execute(query, valores)
            query_instrumentacion = """UPDATE instrumentacion SET id_componente = ?, nombre_equipo = ?
            WHERE id_instrumentacion = ? AND tipo_equipo = 'CELDA';"""
            datos = (
                data['componente'], data['nombre_celda'], data['instrumento']
            )
            cursor.execute(query_instrumentacion, datos)
            conexion.commit()
            return True
        except Exception as e:
            print(f"Error al actualizar celda: {e}")
            return False
        finally:
            if conexion:
                conexion.close()
    
    def mdlActualizarCeldaExcel(data):
        query = """UPDATE celdas SET marca_celda = ?, modelo_celda = ?, rango_celda = ?, instalacion_celda = ?,
        este_celda = ?, norte_celda = ?, fundacion_celda = ?, cf_celda = ?, tk_celda = ? WHERE id_celda = ?;"""
        valores = (
            data['marca_celda'], data['modelo_celda'], data['rango_celda'], data['cota_instalacion_celda'],
            data['coordenada_este_celda'], data['coordenada_norte_celda'], data['cota_fundacion_celda'],
            data['cf_celda'], data['tk_celda'], data['idcelda']
        )
        try:
            conexion = Connection.connectionDB()
            cursor = conexion.cursor()
            cursor.execute(query, valores)
            conexion.commit()
            return True
        except Exception as e:
            print(f"Error al actualizar celda: {e}")
            return False
        finally:
            if conexion:
                conexion.close()
                
    def mdlEliminarCelda(idinstrumento):
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # obtener info para eliminar data
            query_select = """SELECT * FROM instrumentacion WHERE id_instrumentacion = ? AND tipo_equipo = 'CELDA';"""
            cursor.execute(query_select, (idinstrumento,))
            datacelda = cursor.fetchone()
            if datacelda:
                query = """DELETE FROM instrumentacion WHERE id_instrumentacion = ? AND tipo_equipo = 'CELDA';"""
                cursor.execute(query, (idinstrumento,))
                conn.commit()
                if cursor.rowcount > 0:
                    return datacelda
                else:
                    return None
            else:
                return None
        except Exception as e:
            print(f"Error al eliminar celda: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlEliminarCeldaData(tabla, idcelda):
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # eliminar data
            query_delete = f"""DELETE FROM {tabla} WHERE id_celda = ?;"""
            cursor.execute(query_delete, (idcelda,))
            rows_data = cursor.rowcount
            if rows_data > 0:
                stmt_delete = "DELETE FROM celdas WHERE id_celda = ?;"
                cursor.execute(stmt_delete, (idcelda,))
                rows_delete = cursor.rowcount
                conn.commit()
                return rows_delete > 0
            else:
                conn.rollback()
                return False
        except Exception as e:
            print(f"Error al eliminar data celda: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlTraerDataCeldaAsentamiento(idcelda):
        sql = """SELECT i.id_instrumentacion, i.id_componente, c.nombre_componente FROM instrumentacion i
        INNER JOIN componentes c ON i.id_componente = c.id_componente
        WHERE i.id_equipo = ? AND i.tipo_equipo = 'CELDA';"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idcelda,))
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al traer data celda:", e)
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlCambiarCeldaComponente(idinstrumento, nuevocomponente):
        sql = """UPDATE instrumentacion SET id_componente = ? WHERE id_instrumentacion = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (nuevocomponente, idinstrumento))
            conn.commit()
            return True
        except Exception as e:
            print("Error al cambiar componente celda:", e)
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlOmitirLecturaCelda(tabla, idCelda, fecha):
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            query_update = f"""UPDATE {tabla} SET estado_detalle = 0 WHERE id_celda = ? AND fecha_detalle = ?;"""
            cursor.execute(query_update, (idCelda, fecha))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al omitir lecturas de Celda: {e}")
            return False
        finally:
            if conn:
                conn.close()
    