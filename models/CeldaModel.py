from services.security.apis.conexiones.connection import Connection
from datetime import datetime

class CeldaModel:
    
    @staticmethod
    def mdlObtenerFechaMaximaCeldas(tabla):
        sql = f"""SELECT TOP 1 MAX(fecha_detalle) AS max_fecha FROM {tabla};"""
        conn = None
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
            print("Error al obtener fechas max celdas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlListarCeldaProyecto(proyecto, idcomponente, idcelda):
        conn = None
        # Aquí no había conflicto porque celdas tiene alias 'p' y componentes 'c'
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
                return tuple(row)
            else:
                return None
        except Exception as e:
            print("Error al consultar celda: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlRegistrarCelda(data, fecha):
        query = """INSERT INTO celdas (id_proyecto, nombre_celda, marca_celda, modelo_celda, serie_celda, rango_celda, 
        instalacion_celda, este_celda, norte_celda, fundacion_celda, frecuencia_inicial, temperatura_inicial, cf_celda, tk_celda)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        SELECT CAST(SCOPE_IDENTITY() AS INT);"""
        
        valores = (
            data['proyecto'], data['nombre_celda'], data['marca_celda'], data['modelo_celda'], data['modelo_celda'], data['rango_celda'],
            data['cota_instalacion_celda'], data['coordenada_este_celda'], data['coordenada_norte_celda'], data['cota_fundacion_celda'],
            data['frecuencia_inicial'], data['temperatura_inicial_celda'], data['cf_celda'], data['tk_celda']
        )
        conexion = None
        try:
            conexion = Connection.connectionDB()
            cursor = conexion.cursor()
            cursor.execute(query, valores)
            row_id = cursor.fetchone()
            id_insertado = row_id[0] if row_id else None

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
    
    @staticmethod
    def mdlComprobarExisteNombreCelda(proyecto, nombre):
        sql = """SELECT * FROM celdas WHERE id_proyecto = ? AND nombre_celda = ?;"""
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
            print("Error al comprobar celdas: " + str(e))
            return False, None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlRegistrarInstrumentacionCelda(valores):
        query = """INSERT INTO instrumentacion (id_componente, tipo_equipo, nombre_equipo, id_equipo, tabla_equipo)
        VALUES (?, ?, ?, ?, ?);"""
        conexion = None
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
    
    @staticmethod
    def mdlCalcularVelocidadDias(dias, tabla, idcomponente, listaceldas):
        # FIX: Alias componentes 'c' -> 'comp'
        # FIX: Agregadas columnas faltantes al GROUP BY
        placeholders = ', '.join(['?' for _ in listaceldas])
        params = [idcomponente] + listaceldas + [dias]
        conn = None
        
        sql = f"""WITH IncrementalCTE AS (
            SELECT t.id_instrumentacion, c.nombre_celda, cd.fecha_detalle,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 86400.0 AS dias,
                (CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 86400.0) * 24.0 AS horas,
                cd.medida_calculada, c.fundacion_celda,
                COALESCE(
                    (SELECT TOP 1 c2.nivel_cota FROM cotas_celdas c2 WHERE c2.id_celda = c.id_celda 
                    AND c2.fecha_cota <= cd.fecha_detalle ORDER BY c2.fecha_cota DESC),
                    (SELECT TOP 1 c3.nivel_cota FROM cotas_celdas c3 WHERE c3.id_celda = c.id_celda 
                    ORDER BY c3.fecha_cota ASC)
                ) AS superficie,
                COALESCE(cd.medida_calculada - LAG(cd.medida_calculada) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle ASC), 0) AS incremental,
                t.tipo_equipo, t.id_equipo
            FROM celdas c INNER JOIN {tabla} cd ON c.id_celda = cd.id_celda
            INNER JOIN instrumentacion t ON c.id_celda = t.id_equipo
            INNER JOIN componentes comp ON t.id_componente = comp.id_componente
            WHERE comp.id_componente = ? AND t.id_instrumentacion IN ({placeholders}) AND cd.estado_detalle = 1
        ),
        GroupedSummary AS (
            SELECT id_instrumentacion, nombre_celda, fecha_detalle, dias, horas, incremental,
            CAST((CAST(DATEDIFF(SECOND, (SELECT MIN(fecha_detalle) FROM {tabla}), fecha_detalle) AS FLOAT) / 86400.0) / CAST(? AS FLOAT) AS INTEGER) AS grupo_dias,
            fundacion_celda, superficie, tipo_equipo, id_equipo
            FROM IncrementalCTE
        ),
        AggregatedSummary AS (
            SELECT id_instrumentacion, nombre_celda, grupo_dias, MAX(fecha_detalle) AS ultima_fecha_grupo, dias, horas,
            SUM(incremental) AS velocidad_metros, fundacion_celda, superficie, tipo_equipo, id_equipo
            FROM GroupedSummary 
            GROUP BY nombre_celda, grupo_dias, id_instrumentacion, dias, horas, fundacion_celda, superficie, tipo_equipo, id_equipo
        )
        SELECT id_instrumentacion, nombre_celda, ultima_fecha_grupo, dias, horas, velocidad_metros, velocidad_metros * 100 AS velocidad_cm,
        velocidad_metros * 1000 AS velocidad_mm, abs(velocidad_metros) AS velocidad_metros_positivo,
        abs(velocidad_metros * 100) AS velocidad_cm_positivo, abs(velocidad_metros * 1000) AS velocidad_mm_positivo,
        fundacion_celda, superficie, tipo_equipo, id_equipo
        FROM AggregatedSummary ORDER BY nombre_celda ASC, ultima_fecha_grupo ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [tuple(row) for row in rows] if rows else None
        except Exception as e:
            print("Error al obtener velocidad dias celdas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadFechasDias(dias, tabla, idcomponente, listaceldas, fechaini, fechafin):
        # FIX: Alias componentes 'c' -> 'comp'
        # FIX: Agregadas columnas faltantes al GROUP BY
        placeholders = ', '.join(['?' for _ in listaceldas])
        params = [idcomponente] + listaceldas + [fechaini] + [fechafin] + [dias]
        conn = None
        sql = f"""WITH IncrementalCTE AS (
            SELECT t.id_instrumentacion, c.nombre_celda, cd.fecha_detalle,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 86400.0 AS dias,
                (CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 86400.0) * 24.0 AS horas,
                cd.medida_calculada, c.fundacion_celda,
                COALESCE(
                    (SELECT TOP 1 c2.nivel_cota FROM cotas_celdas c2 WHERE c2.id_celda = c.id_celda 
                    AND c2.fecha_cota <= cd.fecha_detalle ORDER BY c2.fecha_cota DESC),
                    (SELECT TOP 1 c3.nivel_cota FROM cotas_celdas c3 WHERE c3.id_celda = c.id_celda 
                    ORDER BY c3.fecha_cota ASC)
                ) AS superficie,
                COALESCE(cd.medida_calculada - LAG(cd.medida_calculada) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle ASC), 0) AS incremental,
                t.tipo_equipo,t.id_equipo
            FROM celdas c INNER JOIN {tabla} cd ON c.id_celda = cd.id_celda
            INNER JOIN instrumentacion t ON c.id_celda = t.id_equipo
            INNER JOIN componentes comp ON t.id_componente = comp.id_componente
            WHERE comp.id_componente = ? AND t.id_instrumentacion IN ({placeholders})
            AND cd.estado_detalle = 1 AND cd.fecha_detalle BETWEEN ? AND ?
        ),
        GroupedSummary AS (
            SELECT id_instrumentacion, nombre_celda, fecha_detalle, dias, horas, incremental,
            CAST((CAST(DATEDIFF(SECOND, (SELECT MIN(fecha_detalle) FROM {tabla}), fecha_detalle) AS FLOAT) / 86400.0) / CAST(? AS FLOAT) AS INTEGER) AS grupo_dias,
            fundacion_celda, superficie,tipo_equipo,id_equipo
            FROM IncrementalCTE
        ),
        AggregatedSummary AS (
            SELECT id_instrumentacion, nombre_celda, grupo_dias, MAX(fecha_detalle) AS ultima_fecha_grupo, dias, horas,
            SUM(incremental) AS velocidad_metros, fundacion_celda, superficie,tipo_equipo,id_equipo
            FROM GroupedSummary 
            GROUP BY nombre_celda, grupo_dias, id_instrumentacion, dias, horas, fundacion_celda, superficie, tipo_equipo, id_equipo
        )
        SELECT id_instrumentacion, nombre_celda, ultima_fecha_grupo, dias, horas, velocidad_metros, velocidad_metros * 100 AS velocidad_cm,
        velocidad_metros * 1000 AS velocidad_mm, abs(velocidad_metros) AS velocidad_metros_positivo,
        abs(velocidad_metros * 100) AS velocidad_cm_positivo, abs(velocidad_metros * 1000) AS velocidad_mm_positivo,
        fundacion_celda, superficie,tipo_equipo,id_equipo
        FROM AggregatedSummary ORDER BY nombre_celda ASC, ultima_fecha_grupo ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [tuple(row) for row in rows] if rows else None
        except Exception as e:
            print("Error al obtener velocidad fechas dias celdas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadMes(tabla, idcomponente, listaceldas):
        # FIX: Alias componentes 'c' -> 'comp'
        placeholders = ', '.join(['?' for _ in listaceldas])
        params = [idcomponente] + listaceldas
        conn = None
        sql = f"""WITH IncrementalCTE AS (
            SELECT t.id_instrumentacion, c.nombre_celda, cd.fecha_detalle,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 86400.0 AS dias,
                (CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 86400.0) * 24.0 AS horas,
                cd.medida_calculada, c.fundacion_celda,
                COALESCE(
                    (SELECT TOP 1 c2.nivel_cota FROM cotas_celdas c2 WHERE c2.id_celda = c.id_celda 
                    AND c2.fecha_cota <= cd.fecha_detalle ORDER BY c2.fecha_cota DESC),
                    (SELECT TOP 1 c3.nivel_cota FROM cotas_celdas c3 WHERE c3.id_celda = c.id_celda 
                    ORDER BY c3.fecha_cota ASC)
                ) AS superficie,
                COALESCE(cd.medida_calculada - LAG(cd.medida_calculada) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle ASC), 0) AS incremental,
                t.tipo_equipo,t.id_equipo
            FROM celdas c INNER JOIN {tabla} cd ON c.id_celda = cd.id_celda
            INNER JOIN instrumentacion t ON c.id_celda = t.id_equipo
            INNER JOIN componentes comp ON t.id_componente = comp.id_componente
            WHERE comp.id_componente = ? AND t.id_instrumentacion IN ({placeholders}) AND cd.estado_detalle = 1
        ),
        MonthlySummary AS (
            SELECT id_instrumentacion, nombre_celda, FORMAT(fecha_detalle, 'yyyy-MM') AS mes, fecha_detalle, dias, horas, incremental,
                SUM(incremental) OVER (PARTITION BY nombre_celda, FORMAT(fecha_detalle, 'yyyy-MM')) AS velocidad_metros,
                fundacion_celda, superficie,
                ROW_NUMBER() OVER (PARTITION BY nombre_celda, FORMAT(fecha_detalle, 'yyyy-MM') ORDER BY fecha_detalle DESC) AS rn,
                tipo_equipo,id_equipo
            FROM IncrementalCTE
        )
        SELECT id_instrumentacion, nombre_celda, fecha_detalle AS ultima_fecha_mes, dias, horas, velocidad_metros,
        velocidad_metros * 100 AS velocidad_cm, velocidad_metros * 1000 AS velocidad_mm,
        abs(velocidad_metros) AS velocidad_metros_positivo, abs(velocidad_metros * 100) AS velocidad_cm_positivo,
        abs(velocidad_metros * 1000) AS velocidad_mm_positivo, fundacion_celda, superficie,tipo_equipo,id_equipo
        FROM MonthlySummary
        WHERE rn = 1
        ORDER BY nombre_celda ASC, ultima_fecha_mes ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [tuple(row) for row in rows] if rows else None
        except Exception as e:
            print("Error al obtener velocidad mensual celda: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadFechasMes(tabla, idcomponente, listaceldas, fechaini, fechafin):
        # FIX: Alias componentes 'c' -> 'comp'
        placeholders = ', '.join(['?' for _ in listaceldas])
        params = [idcomponente] + listaceldas + [fechaini] + [fechafin]
        conn = None
        sql = f"""WITH IncrementalCTE AS (
            SELECT t.id_instrumentacion, c.nombre_celda, cd.fecha_detalle,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 86400.0 AS dias,
                (CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 86400.0) * 24.0 AS horas,
                cd.medida_calculada, c.fundacion_celda,
                COALESCE(
                    (SELECT TOP 1 c2.nivel_cota FROM cotas_celdas c2 WHERE c2.id_celda = c.id_celda 
                    AND c2.fecha_cota <= cd.fecha_detalle ORDER BY c2.fecha_cota DESC),
                    (SELECT TOP 1 c3.nivel_cota FROM cotas_celdas c3 WHERE c3.id_celda = c.id_celda 
                    ORDER BY c3.fecha_cota ASC)
                ) AS superficie,
                COALESCE(cd.medida_calculada - LAG(cd.medida_calculada) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle ASC), 0) AS incremental,
                t.tipo_equipo,t.id_equipo
            FROM celdas c INNER JOIN {tabla} cd ON c.id_celda = cd.id_celda
            INNER JOIN instrumentacion t ON c.id_celda = t.id_equipo
            INNER JOIN componentes comp ON t.id_componente = comp.id_componente
            WHERE comp.id_componente = ? AND t.id_instrumentacion IN ({placeholders})
            AND cd.estado_detalle = 1 AND cd.fecha_detalle BETWEEN ? AND ?
        ),
        MonthlySummary AS (
            SELECT id_instrumentacion, nombre_celda, FORMAT(fecha_detalle, 'yyyy-MM') AS mes, fecha_detalle, dias, horas, incremental,
                SUM(incremental) OVER (PARTITION BY nombre_celda, FORMAT(fecha_detalle, 'yyyy-MM')) AS velocidad_metros,
                fundacion_celda, superficie,
                ROW_NUMBER() OVER (PARTITION BY nombre_celda, FORMAT(fecha_detalle, 'yyyy-MM') ORDER BY fecha_detalle DESC) AS rn,
                tipo_equipo,id_equipo
            FROM IncrementalCTE
        )
        SELECT id_instrumentacion, nombre_celda, fecha_detalle AS ultima_fecha_mes, dias, horas, velocidad_metros,
            velocidad_metros * 100 AS velocidad_cm, velocidad_metros * 1000 AS velocidad_mm,
            abs(velocidad_metros) AS velocidad_metros_positivo, abs(velocidad_metros * 100) AS velocidad_cm_positivo,
            abs(velocidad_metros * 1000) AS velocidad_mm_positivo, fundacion_celda, superficie,tipo_equipo,id_equipo
        FROM MonthlySummary
        WHERE rn = 1
        ORDER BY nombre_celda ASC, ultima_fecha_mes ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [tuple(row) for row in rows] if rows else None
        except Exception as e:
            print("Error al obtener velocidad mensual celda: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerAsentamientoCota(tabla, idcomponente, listaceldas):
        # FIX: Alias componentes 'c' -> 'comp'
        placeholders = ', '.join(['?' for _ in listaceldas])
        params = [idcomponente] + listaceldas
        conn = None
        sql = f"""SELECT t.id_instrumentacion, c.nombre_celda, cd.fecha_detalle,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 86400.0 AS dias,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 86400.0) * 24.0 AS horas,
            c.instalacion_celda - abs(cd.medida_calculada) AS cota_piezometrica, c.fundacion_celda,
            COALESCE(
                (SELECT TOP 1 c2.nivel_cota FROM cotas_celdas c2 WHERE c2.id_celda = c.id_celda 
                AND c2.fecha_cota <= cd.fecha_detalle ORDER BY c2.fecha_cota DESC),
                (SELECT TOP 1 c3.nivel_cota FROM cotas_celdas c3 WHERE c3.id_celda = c.id_celda 
                ORDER BY c3.fecha_cota ASC)
            ) AS superficie, t.tipo_equipo, t.id_equipo
        FROM celdas c INNER JOIN {tabla} cd ON c.id_celda = cd.id_celda
        INNER JOIN instrumentacion t ON c.id_celda = t.id_equipo
        INNER JOIN componentes comp ON t.id_componente = comp.id_componente
        WHERE comp.id_componente = ? AND t.id_instrumentacion IN ({placeholders}) AND cd.estado_detalle = 1
        ORDER BY c.nombre_celda ASC, cd.fecha_detalle ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [tuple(row) for row in rows] if rows else None
        except Exception as e:
            print("Error al obtener asentamiento cota: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerAsentamientoFechasCota(tabla, idcomponente, listaceldas, fechaini, fechafin):
        # FIX: Alias componentes 'c' -> 'comp'
        placeholders = ', '.join(['?' for _ in listaceldas])
        params = [idcomponente] + listaceldas + [fechaini] + [fechafin]
        conn = None
        sql = f"""SELECT t.id_instrumentacion, c.nombre_celda, cd.fecha_detalle,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 86400.0 AS dias,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 86400.0) * 24.0 AS horas,
            c.instalacion_celda - abs(cd.medida_calculada) AS cota_piezometrica, c.fundacion_celda,
            COALESCE(
                (SELECT TOP 1 c2.nivel_cota FROM cotas_celdas c2 WHERE c2.id_celda = c.id_celda 
                AND c2.fecha_cota <= cd.fecha_detalle ORDER BY c2.fecha_cota DESC),
                (SELECT TOP 1 c3.nivel_cota FROM cotas_celdas c3 WHERE c3.id_celda = c.id_celda 
                ORDER BY c3.fecha_cota ASC)
            ) AS superficie,t.tipo_equipo,t.id_equipo
        FROM celdas c INNER JOIN {tabla} cd ON c.id_celda = cd.id_celda
        INNER JOIN instrumentacion t ON c.id_celda = t.id_equipo
        INNER JOIN componentes comp ON t.id_componente = comp.id_componente
        WHERE comp.id_componente = ? AND t.id_instrumentacion IN ({placeholders})
        AND cd.estado_detalle = 1 AND cd.fecha_detalle BETWEEN ? AND ?
        ORDER BY c.nombre_celda ASC, cd.fecha_detalle ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [tuple(row) for row in rows] if rows else None
        except Exception as e:
            print("Error al obtener asentamiento cota: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularAsentamientoIncremental(tabla, idcomponente, listaceldas, unidadmedida):
        # FIX: Alias componentes 'c' -> 'comp'
        placeholders = ', '.join(['?' for _ in listaceldas])
        params = [unidadmedida] + [idcomponente] + listaceldas
        conn = None
        sql = f"""SELECT t.id_instrumentacion, c.nombre_celda, cd.fecha_detalle,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 86400.0 AS dias,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 86400.0) * 24.0 AS horas,
            COALESCE(cd.medida_calculada - LAG(cd.medida_calculada) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle ASC), 0) * CAST(? AS FLOAT) AS incremental, c.fundacion_celda,
            COALESCE(
                (SELECT TOP 1 c2.nivel_cota FROM cotas_celdas c2 WHERE c2.id_celda = c.id_celda 
                AND c2.fecha_cota <= cd.fecha_detalle ORDER BY c2.fecha_cota DESC),
                (SELECT TOP 1 c3.nivel_cota FROM cotas_celdas c3 WHERE c3.id_celda = c.id_celda 
                ORDER BY c3.fecha_cota ASC)
            ) AS superficie, t.tipo_equipo, t.id_equipo
        FROM celdas c INNER JOIN {tabla} cd ON c.id_celda = cd.id_celda
        INNER JOIN instrumentacion t ON c.id_celda = t.id_equipo
        INNER JOIN componentes comp ON t.id_componente = comp.id_componente
        WHERE comp.id_componente = ? AND t.id_instrumentacion IN ({placeholders}) AND cd.estado_detalle = 1
        ORDER BY c.nombre_celda ASC, cd.fecha_detalle ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [tuple(row) for row in rows] if rows else None
        except Exception as e:
            print("Error al obtener asentamiento incremental: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularAsentamientoFechasIncremental(tabla, idcomponente, listaceldas, fechaini, fechafin, unidadmedida):
        # FIX: Alias componentes 'c' -> 'comp'
        placeholders = ', '.join(['?' for _ in listaceldas])
        params = [unidadmedida] + [idcomponente] + listaceldas + [fechaini] + [fechafin]
        conn = None
        sql = f"""SELECT t.id_instrumentacion, c.nombre_celda, cd.fecha_detalle,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 86400.0 AS dias,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 86400.0) * 24.0 AS horas,
            COALESCE(cd.medida_calculada - LAG(cd.medida_calculada) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle ASC), 0) * CAST(? AS FLOAT) AS incremental, c.fundacion_celda,
            COALESCE(
                (SELECT TOP 1 c2.nivel_cota FROM cotas_celdas c2 WHERE c2.id_celda = c.id_celda 
                AND c2.fecha_cota <= cd.fecha_detalle ORDER BY c2.fecha_cota DESC),
                (SELECT TOP 1 c3.nivel_cota FROM cotas_celdas c3 WHERE c3.id_celda = c.id_celda 
                ORDER BY c3.fecha_cota ASC)
            ) AS superficie,t.tipo_equipo,t.id_equipo
        FROM celdas c INNER JOIN {tabla} cd ON c.id_celda = cd.id_celda
        INNER JOIN instrumentacion t ON c.id_celda = t.id_equipo
        INNER JOIN componentes comp ON t.id_componente = comp.id_componente
        WHERE comp.id_componente = ? AND t.id_instrumentacion IN ({placeholders})
        AND cd.estado_detalle = 1 AND cd.fecha_detalle BETWEEN ? AND ?
        ORDER BY c.nombre_celda ASC, cd.fecha_detalle ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [tuple(row) for row in rows] if rows else None
        except Exception as e:
            print("Error al obtener asentamiento incremental: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerAsentamientoAcumulado(tabla, idcomponente, listaceldas, unidadmedida):
        # FIX: Alias componentes 'c' -> 'comp'
        placeholders = ', '.join(['?' for _ in listaceldas])
        params = [unidadmedida] + [idcomponente] + listaceldas
        conn = None
        sql = f"""SELECT t.id_instrumentacion, c.nombre_celda, cd.fecha_detalle,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 86400.0 AS dias,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 86400.0) * 24.0 AS horas,
            cd.medida_calculada * CAST(? AS FLOAT) AS medida_calculada, c.fundacion_celda,
            COALESCE(
                (SELECT TOP 1 c2.nivel_cota FROM cotas_celdas c2 WHERE c2.id_celda = c.id_celda 
                AND c2.fecha_cota <= cd.fecha_detalle ORDER BY c2.fecha_cota DESC),
                (SELECT TOP 1 c3.nivel_cota FROM cotas_celdas c3 WHERE c3.id_celda = c.id_celda 
                ORDER BY c3.fecha_cota ASC)
            ) AS superficie, t.tipo_equipo, t.id_equipo
        FROM celdas c INNER JOIN {tabla} cd ON c.id_celda = cd.id_celda
        INNER JOIN instrumentacion t ON c.id_celda = t.id_equipo
        INNER JOIN componentes comp ON t.id_componente = comp.id_componente
        WHERE comp.id_componente = ? AND t.id_instrumentacion IN ({placeholders}) AND cd.estado_detalle = 1
        ORDER BY c.nombre_celda ASC, cd.fecha_detalle ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [tuple(row) for row in rows] if rows else None
        except Exception as e:
            print("Error al obtener asentamiento acumulado: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerAsentamientoFechasAcumulado(tabla, idcomponente, listaceldas, fechaini, fechafin, unidadmedida):
        # FIX: Alias componentes 'c' -> 'comp'
        placeholders = ', '.join(['?' for _ in listaceldas])
        params = [unidadmedida] + [idcomponente] + listaceldas + [fechaini] + [fechafin]
        conn = None
        sql = f"""SELECT t.id_instrumentacion, c.nombre_celda, cd.fecha_detalle,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 86400.0 AS dias,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 86400.0) * 24.0 AS horas,
            cd.medida_calculada * CAST(? AS FLOAT) AS medida_calculada, c.fundacion_celda,
            COALESCE(
                (SELECT TOP 1 c2.nivel_cota FROM cotas_celdas c2 WHERE c2.id_celda = c.id_celda 
                AND c2.fecha_cota <= cd.fecha_detalle ORDER BY c2.fecha_cota DESC),
                (SELECT TOP 1 c3.nivel_cota FROM cotas_celdas c3 WHERE c3.id_celda = c.id_celda 
                ORDER BY c3.fecha_cota ASC)
            ) AS superficie, t.tipo_equipo, t.id_equipo
        FROM celdas c INNER JOIN {tabla} cd ON c.id_celda = cd.id_celda
        INNER JOIN instrumentacion t ON c.id_celda = t.id_equipo
        INNER JOIN componentes comp ON t.id_componente = comp.id_componente
        WHERE comp.id_componente = ? AND t.id_instrumentacion IN ({placeholders})
        AND cd.estado_detalle = 1 AND cd.fecha_detalle BETWEEN ? AND ?
        ORDER BY c.nombre_celda ASC, cd.fecha_detalle ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [tuple(row) for row in rows] if rows else None
        except Exception as e:
            print("Error al obtener asentamiento acumulado: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerAsentamientoFrecuencia(tabla, idcomponente, listaceldas):
        # FIX: Alias componentes 'c' -> 'comp'
        placeholders = ', '.join(['?' for _ in listaceldas])
        params = [idcomponente] + listaceldas
        conn = None
        sql = f"""SELECT t.id_instrumentacion, c.nombre_celda, cd.fecha_detalle,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 86400.0 AS dias,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 86400.0) * 24.0 AS horas,
            cd.frecuencia_hz, c.fundacion_celda,
            COALESCE(
                (SELECT TOP 1 c2.nivel_cota FROM cotas_celdas c2 WHERE c2.id_celda = c.id_celda 
                AND c2.fecha_cota <= cd.fecha_detalle ORDER BY c2.fecha_cota DESC),
                (SELECT TOP 1 c3.nivel_cota FROM cotas_celdas c3 WHERE c3.id_celda = c.id_celda 
                ORDER BY c3.fecha_cota ASC)
            ) AS superficie, t.tipo_equipo, t.id_equipo
        FROM celdas c INNER JOIN {tabla} cd ON c.id_celda = cd.id_celda
        INNER JOIN instrumentacion t ON c.id_celda = t.id_equipo
        INNER JOIN componentes comp ON t.id_componente = comp.id_componente
        WHERE comp.id_componente = ? AND t.id_instrumentacion IN ({placeholders}) AND cd.estado_detalle = 1
        ORDER BY c.nombre_celda ASC, cd.fecha_detalle ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [tuple(row) for row in rows] if rows else None
        except Exception as e:
            print("Error al obtener frecuencia celdas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerAsentamientoFechasFrecuencia(tabla, idcomponente, listaceldas, fechaini, fechafin):
        # FIX: Alias componentes 'c' -> 'comp'
        placeholders = ', '.join(['?' for _ in listaceldas])
        params = [idcomponente] + listaceldas + [fechaini] + [fechafin]
        conn = None
        sql = f"""SELECT t.id_instrumentacion, c.nombre_celda, cd.fecha_detalle,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 86400.0 AS dias,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 86400.0) * 24.0 AS horas,
            cd.frecuencia_hz, c.fundacion_celda,
            COALESCE(
                (SELECT TOP 1 c2.nivel_cota FROM cotas_celdas c2 WHERE c2.id_celda = c.id_celda 
                AND c2.fecha_cota <= cd.fecha_detalle ORDER BY c2.fecha_cota DESC),
                (SELECT TOP 1 c3.nivel_cota FROM cotas_celdas c3 WHERE c3.id_celda = c.id_celda 
                ORDER BY c3.fecha_cota ASC)
            ) AS superficie, t.tipo_equipo, t.id_equipo
        FROM celdas c INNER JOIN {tabla} cd ON c.id_celda = cd.id_celda
        INNER JOIN instrumentacion t ON c.id_celda = t.id_equipo
        INNER JOIN componentes comp ON t.id_componente = comp.id_componente
        WHERE comp.id_componente = ? AND t.id_instrumentacion IN ({placeholders})
        AND cd.estado_detalle = 1 AND cd.fecha_detalle BETWEEN ? AND ?
        ORDER BY c.nombre_celda ASC, cd.fecha_detalle ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [tuple(row) for row in rows] if rows else None
        except Exception as e:
            print("Error al obtener frecuencia celdas fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerAsentamientoTemperatura(tabla, idcomponente, listaceldas):
        # FIX: Alias componentes 'c' -> 'comp'
        placeholders = ', '.join(['?' for _ in listaceldas])
        params = [idcomponente] + listaceldas
        conn = None
        sql = f"""SELECT t.id_instrumentacion, c.nombre_celda, cd.fecha_detalle,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 86400.0 AS dias,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 86400.0) * 24.0 AS horas,
            cd.temperatura_detalle, c.fundacion_celda,
            COALESCE(
                (SELECT TOP 1 c2.nivel_cota FROM cotas_celdas c2 WHERE c2.id_celda = c.id_celda 
                AND c2.fecha_cota <= cd.fecha_detalle ORDER BY c2.fecha_cota DESC),
                (SELECT TOP 1 c3.nivel_cota FROM cotas_celdas c3 WHERE c3.id_celda = c.id_celda 
                ORDER BY c3.fecha_cota ASC)
            ) AS superficie, t.tipo_equipo, t.id_equipo
        FROM celdas c INNER JOIN {tabla} cd ON c.id_celda = cd.id_celda
        INNER JOIN instrumentacion t ON c.id_celda = t.id_equipo
        INNER JOIN componentes comp ON t.id_componente = comp.id_componente
        WHERE comp.id_componente = ? AND t.id_instrumentacion IN ({placeholders}) AND cd.estado_detalle = 1
        ORDER BY c.nombre_celda ASC, cd.fecha_detalle ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [tuple(row) for row in rows] if rows else None
        except Exception as e:
            print("Error al obtener temperatura celdas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerAsentamientoFechasTemperatura(tabla, idcomponente, listaceldas, fechaini, fechafin):
        # FIX: Alias componentes 'c' -> 'comp'
        placeholders = ', '.join(['?' for _ in listaceldas])
        params = [idcomponente] + listaceldas + [fechaini] + [fechafin]
        conn = None
        sql = f"""SELECT t.id_instrumentacion, c.nombre_celda, cd.fecha_detalle,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 86400.0 AS dias,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) AS FLOAT) / 86400.0) * 24.0 AS horas,
            cd.temperatura_detalle, c.fundacion_celda,
            COALESCE(
                (SELECT TOP 1 c2.nivel_cota FROM cotas_celdas c2 WHERE c2.id_celda = c.id_celda 
                AND c2.fecha_cota <= cd.fecha_detalle ORDER BY c2.fecha_cota DESC),
                (SELECT TOP 1 c3.nivel_cota FROM cotas_celdas c3 WHERE c3.id_celda = c.id_celda 
                ORDER BY c3.fecha_cota ASC)
            ) AS superficie, t.tipo_equipo, t.id_equipo
        FROM celdas c INNER JOIN {tabla} cd ON c.id_celda = cd.id_celda
        INNER JOIN instrumentacion t ON c.id_celda = t.id_equipo
        INNER JOIN componentes comp ON t.id_componente = comp.id_componente
        WHERE comp.id_componente = ? AND t.id_instrumentacion IN ({placeholders})
        AND cd.estado_detalle = 1 AND cd.fecha_detalle BETWEEN ? AND ?
        ORDER BY c.nombre_celda ASC, cd.fecha_detalle ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [tuple(row) for row in rows] if rows else None
        except Exception as e:
            print("Error al obtener temperatura celdas fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlActualizarLecturaCelda(tabla, data, idproyecto, username, nombres):
        conexion = None
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
                cambios = f"Antiguos: {tuple(datos_anteriores)}, Nuevos: {data}"
                query_historial = """INSERT INTO historial (idproyecto, fecha, accion, tabla, cambios, usuario, nombres)
                VALUES (?, ?, ?, ?, ?, ?, ?);"""
                cursor.execute(query_historial, (idproyecto, fecha_cambio, accion, tabla, cambios, username, nombres))
            # actualizar prisma
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
    
    @staticmethod
    def mdlCambiarEstadoLecturaCelda(tabla, iddetalle):
        conn = None
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
    
    @staticmethod
    def mdlCambiarEstadoLecturaCeldaBloque(tabla, listacodigos):
        conn = None
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
    
    @staticmethod
    def mdlEliminarLecturaCelda(tabla, idcelda, idproyecto, username, nombres):
        sql = f"""DELETE FROM {tabla} WHERE id_detalle = ?;"""
        conn = None
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
                cambios = f"Datos: {tuple(datos_anteriores)}"
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
            print("Error al eliminar lectura celda: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlEliminarLecturasBloqueCelda(tabla, iddetalles, idproyecto, username, nombres):
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
                cambios = f"Datos: {[tuple(row) for row in datos_anteriores]}"
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
            print("Error al eliminar lecturas celdas: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerCeldasAsentamiento(proyecto):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = """SELECT id_celda, nombre_celda FROM celdas WHERE id_proyecto = ?"""
            cur = conn.cursor()
            cur.execute(sql,(proyecto,))
            row = cur.fetchall()  
            if row:
                return [tuple(r) for r in row]
            else:
                return None
        except Exception as e:
            print("Error al obtener datos:", e)
            return None 
        finally:
            if conn:
                conn.close()
                
    @staticmethod
    def mdlRegistrarDataCelda(proyectoid, data, idsceldas):
        conn = None
        table_name = f"celda_detalle{proyectoid}"
        sqltable = f"""IF OBJECT_ID('{table_name}', 'U') IS NULL
        CREATE TABLE {table_name} (
                id_detalle INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
                id_celda INT NOT NULL,
                fecha_detalle VARCHAR(50) NOT NULL,
                frecuencia_digits FLOAT,
                frecuencia_hz FLOAT,
                temperatura_detalle FLOAT,
                medida_calculada FLOAT,
                observacion_detalle TEXT,
                estado_detalle INT DEFAULT 1
        );"""
        
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            cursor.execute(sqltable)
            conn.commit()
            
            placeholders = ','.join(['?'] * len(idsceldas))
            cursor.execute(f"SELECT id_celda, fecha_detalle FROM {table_name} WHERE id_celda IN ({placeholders});", list(idsceldas))
            existen_celdas = set([(row[0], row[1]) for row in cursor.fetchall()])
            
            lote_registros = []
            contador = 0
            for fila in data:
                id_celda = fila[0]
                fecha_original = fila[1]
                hora_original = fila[2]
                fecha_hora_nueva = fecha_original + " " + hora_original
                
                if (id_celda, fecha_hora_nueva) not in existen_celdas:
                    datito = (
                        id_celda,
                        fecha_hora_nueva,
                        fila[3], # frecuencia digits
                        fila[4], # frecuencia hz
                        fila[5], # temperatura
                        fila[6], # data calculada MCA
                        fila[7]  # Observacion
                    )
                    lote_registros.append(datito)
                    contador += 1
                
                if contador % 1000 == 0 and lote_registros:
                    cursor.executemany(f"""INSERT INTO {table_name} (id_celda, fecha_detalle, frecuencia_digits, frecuencia_hz, temperatura_detalle, medida_calculada, observacion_detalle) VALUES (?, ?, ?, ?, ?, ?, ?);""", lote_registros)
                    lote_registros = []
            
            if lote_registros:
                cursor.executemany(f"""INSERT INTO {table_name} (id_celda, fecha_detalle, frecuencia_digits, frecuencia_hz, temperatura_detalle, medida_calculada, observacion_detalle) VALUES (?, ?, ?, ?, ?, ?, ?);""", lote_registros)
            
            conn.commit()
            return True
        except Exception as e:
            print("Error al guardar las celdas: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCambiarComponenteCeldas(idcomponente, nuevocomponente):
        sql = """UPDATE instrumentacion SET id_componente = ? WHERE id_componente = ? AND tipo_equipo = 'CELDA';"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            query_select = """SELECT * FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'CELDA';"""
            cur.execute(query_select, (idcomponente,))
            dataceldas = cur.fetchall()
            if dataceldas:
                cur.execute(sql, (nuevocomponente, idcomponente))
                conn.commit()
                return [tuple(row) for row in dataceldas]
            else:
                return None
        except Exception as e:
            print("Error al cambiar componente celdas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlEliminarCeldas(idcomponente):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            query_select = """SELECT * FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'CELDA';"""
            cursor.execute(query_select, (idcomponente,))
            datacelda = cursor.fetchall()
            if datacelda:
                query = """DELETE FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'CELDA';"""
                cursor.execute(query, (idcomponente,))
                conn.commit()
                if cursor.rowcount > 0:
                    return [tuple(row) for row in datacelda]
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
    
    @staticmethod
    def mdlEliminarDataCeldas(tabla, terrenos):
        placeholders = ','.join(['?' for _ in terrenos])
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
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
    
    @staticmethod
    def mdlObtenerInfoCelda(idinstrumento):
        sql = """SELECT c.* FROM celdas c INNER JOIN instrumentacion i ON c.id_celda = i.id_equipo WHERE i.id_instrumentacion = ?;"""
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
            print("Error al consultar info celda: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlActualizarCelda(data):
        query = """UPDATE celdas SET nombre_celda = ?, marca_celda = ?, modelo_celda = ?, rango_celda = ?, instalacion_celda = ?,
        este_celda = ?, norte_celda = ?, fundacion_celda = ?, frecuencia_inicial = ?, temperatura_inicial = ?, cf_celda = ?,
        tk_celda = ? WHERE id_celda = ?;"""
        valores = (
            data['nombre_celda'], data['marca_celda'], data['modelo_celda'], data['rango_celda'], data['cota_instalacion_celda'],
            data['coordenada_este_celda'], data['coordenada_norte_celda'], data['cota_fundacion_celda'], data['frecuencia_inicial'],
            data['temperatura_inicial_celda'], data['cf_celda'], data['tk_celda'], data['idcelda']
        )
        conexion = None
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
    
    @staticmethod
    def mdlActualizarCeldaExcel(data):
        query = """UPDATE celdas SET marca_celda = ?, modelo_celda = ?, rango_celda = ?, instalacion_celda = ?,
        este_celda = ?, norte_celda = ?, fundacion_celda = ?, cf_celda = ?, tk_celda = ? WHERE id_celda = ?;"""
        valores = (
            data['marca_celda'], data['modelo_celda'], data['rango_celda'], data['cota_instalacion_celda'],
            data['coordenada_este_celda'], data['coordenada_norte_celda'], data['cota_fundacion_celda'],
            data['cf_celda'], data['tk_celda'], data['idcelda']
        )
        conexion = None
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
                
    @staticmethod
    def mdlEliminarCelda(idinstrumento):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            query_select = """SELECT * FROM instrumentacion WHERE id_instrumentacion = ? AND tipo_equipo = 'CELDA';"""
            cursor.execute(query_select, (idinstrumento,))
            datacelda = cursor.fetchone()
            if datacelda:
                query = """DELETE FROM instrumentacion WHERE id_instrumentacion = ? AND tipo_equipo = 'CELDA';"""
                cursor.execute(query, (idinstrumento,))
                conn.commit()
                if cursor.rowcount > 0:
                    return tuple(datacelda)
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
    
    @staticmethod
    def mdlEliminarCeldaData(tabla, idcelda):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
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
    
    @staticmethod
    def mdlTraerDataCeldaAsentamiento(idcelda):
        sql = """SELECT i.id_instrumentacion, i.id_componente, c.nombre_componente FROM instrumentacion i
        INNER JOIN componentes c ON i.id_componente = c.id_componente
        WHERE i.id_equipo = ? AND i.tipo_equipo = 'CELDA';"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idcelda,))
            row = cur.fetchone()
            if row:
                return tuple(row)
            else:
                return None
        except Exception as e:
            print("Error al traer data celda: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCambiarCeldaComponente(idinstrumento, nuevocomponente):
        sql = """UPDATE instrumentacion SET id_componente = ? WHERE id_instrumentacion = ?;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (nuevocomponente, idinstrumento))
            conn.commit()
            return True
        except Exception as e:
            print("Error al cambiar componente celda: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlOmitirLecturaCelda(tabla,idCelda,fecha):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            query_update = f"""UPDATE {tabla} SET estado_detalle = 0 WHERE id_celda = ? AND fecha_detalle=?;"""
            cursor.execute(query_update, (idCelda,fecha))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al omitir lecturas de Celda: {e}")
            return False
        finally:
            if conn:
                conn.close()