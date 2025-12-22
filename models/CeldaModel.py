from services.security.apis.conexiones.conexion import Connection
from datetime import datetime

class CeldaModel:
    
    @staticmethod
    def mdlObtenerFechaMaximaCeldas(tabla):
        sql = f"""SELECT MAX(fecha_detalle) AS max_fecha FROM {tabla};"""
        conn = None
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
            print("Error al obtener fechas max celdas: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlListarCeldaProyecto(proyecto, idcomponente, idcelda):
        conn = None
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
            print("Error al consultar celda: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlRegistrarCelda(data, fecha):
        # SQL Server: Se agrega SELECT SCOPE_IDENTITY() para obtener el último ID
        query = """INSERT INTO celdas (id_proyecto, nombre_celda, marca_celda, modelo_celda, serie_celda, rango_celda, 
        instalacion_celda, este_celda, norte_celda, fundacion_celda, frecuencia_inicial, temperatura_inicial, cf_celda, tk_celda)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        SELECT SCOPE_IDENTITY();"""
        
        valores = (
            data['proyecto'], data['nombre_celda'], data['marca_celda'], data['modelo_celda'], data['modelo_celda'], data['rango_celda'],
            data['cota_instalacion_celda'], data['coordenada_este_celda'], data['coordenada_norte_celda'], data['cota_fundacion_celda'],
            data['frecuencia_inicial'], data['temperatura_inicial_celda'], data['cf_celda'], data['tk_celda']
        )
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            cursor.execute(query, valores)
            
            # Recuperar el ID generado
            row = cursor.fetchone()
            id_insertado = int(row[0]) if row and row[0] is not None else None
            
            if id_insertado:
                inst = """INSERT INTO cotas_celdas (id_celda, fecha_cota, nivel_cota) VALUES (?, ?, ?);"""
                val = (id_insertado, fecha, data['cota_superficie_celda'])
                cursor.execute(inst, val)
            
            conn.commit()
            return id_insertado
        except Exception as e:
            print(f"Error al registrar celda y cota: {e}")
            return None
        finally:
            if conn: conn.close()
    
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
                return True, row
            else:
                return False, None
        except Exception as e:
            print("Error al comprobar celdas: " + str(e))
            return False, None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlRegistrarInstrumentacionCelda(valores):
        query = """INSERT INTO instrumentacion (id_componente, tipo_equipo, nombre_equipo, id_equipo, tabla_equipo)
        VALUES (?, ?, ?, ?, ?);"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            cursor.execute(query, valores)
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al registrar celda en instrumentacion: {e}")
            return False
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadDias(dias, tabla, idcomponente, listaceldas):
        placeholders = ', '.join(['?' for _ in listaceldas])
        params = [idcomponente] + listaceldas + [dias]
        
        # LOGICA SQL SERVER:
        # 1. DATEDIFF(SECOND, inicio, fin) / 86400.0 reemplaza a julianday() para obtener días con decimales
        # 2. TOP 1 reemplaza a LIMIT 1
        sql = f"""WITH IncrementalCTE AS (
            SELECT t.id_instrumentacion, c.nombre_celda, cd.fecha_detalle,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) / 86400.0 AS FLOAT) AS dias,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) / 3600.0 AS FLOAT) AS horas,
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
            INNER JOIN componentes c ON t.id_componente = c.id_componente
            WHERE c.id_componente = ? AND t.id_instrumentacion IN ({placeholders}) AND cd.estado_detalle = 1
        ),
        GroupedSummary AS (
            SELECT id_instrumentacion, nombre_celda, fecha_detalle, dias, horas, incremental,
            CAST((DATEDIFF(SECOND, (SELECT MIN(fecha_detalle) FROM {tabla}), fecha_detalle) / 86400.0) / ? AS INT) AS grupo_dias,
            fundacion_celda, superficie,tipo_equipo,id_equipo
            FROM IncrementalCTE
        ),
        AggregatedSummary AS (
            SELECT id_instrumentacion, nombre_celda, grupo_dias, MAX(fecha_detalle) AS ultima_fecha_grupo, dias, horas,
            SUM(incremental) AS velocidad_metros, fundacion_celda, superficie,tipo_equipo,id_equipo
            FROM GroupedSummary GROUP BY nombre_celda, grupo_dias, dias, horas, fundacion_celda, superficie, tipo_equipo, id_equipo
        )
        SELECT id_instrumentacion, nombre_celda, ultima_fecha_grupo, dias, horas, velocidad_metros, velocidad_metros * 100 AS velocidad_cm,
        velocidad_metros * 1000 AS velocidad_mm, abs(velocidad_metros) AS velocidad_metros_positivo,
        abs(velocidad_metros * 100) AS velocidad_cm_positivo, abs(velocidad_metros * 1000) AS velocidad_mm_positivo,
        fundacion_celda, superficie,tipo_equipo,id_equipo
        FROM AggregatedSummary ORDER BY nombre_celda ASC, ultima_fecha_grupo ASC;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return rows if rows else None
        except Exception as e:
            print("Error al obtener velocidad dias celdas: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadFechasDias(dias, tabla, idcomponente, listaceldas, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in listaceldas])
        params = [idcomponente] + listaceldas + [fechaini] + [fechafin] + [dias]
        conn = None
        sql = f"""WITH IncrementalCTE AS (
            SELECT t.id_instrumentacion, c.nombre_celda, cd.fecha_detalle,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) / 86400.0 AS FLOAT) AS dias,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) / 3600.0 AS FLOAT) AS horas,
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
            INNER JOIN componentes c ON t.id_componente = c.id_componente
            WHERE c.id_componente = ? AND t.id_instrumentacion IN ({placeholders})
            AND cd.estado_detalle = 1 AND cd.fecha_detalle BETWEEN ? AND ?
        ),
        GroupedSummary AS (
            SELECT id_instrumentacion, nombre_celda, fecha_detalle, dias, horas, incremental,
            CAST((DATEDIFF(SECOND, (SELECT MIN(fecha_detalle) FROM {tabla}), fecha_detalle) / 86400.0) / ? AS INT) AS grupo_dias,
            fundacion_celda, superficie,tipo_equipo,id_equipo
            FROM IncrementalCTE
        ),
        AggregatedSummary AS (
            SELECT id_instrumentacion, nombre_celda, grupo_dias, MAX(fecha_detalle) AS ultima_fecha_grupo, dias, horas,
            SUM(incremental) AS velocidad_metros, fundacion_celda, superficie,tipo_equipo,id_equipo
            FROM GroupedSummary GROUP BY nombre_celda, grupo_dias, dias, horas, fundacion_celda, superficie, tipo_equipo, id_equipo
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
            return rows if rows else None
        except Exception as e:
            print("Error al obtener velocidad fechas dias celdas: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadMes(tabla, idcomponente, listaceldas):
        placeholders = ', '.join(['?' for _ in listaceldas])
        params = [idcomponente] + listaceldas
        
        # LOGICA SQL SERVER: FORMAT(fecha, 'yyyy-MM') reemplaza a strftime
        sql = f"""WITH IncrementalCTE AS (
            SELECT t.id_instrumentacion, c.nombre_celda, cd.fecha_detalle,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) / 86400.0 AS FLOAT) AS dias,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) / 3600.0 AS FLOAT) AS horas,
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
            INNER JOIN componentes c ON t.id_componente = c.id_componente
            WHERE c.id_componente = ? AND t.id_instrumentacion IN ({placeholders}) AND cd.estado_detalle = 1
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
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return rows if rows else None
        except Exception as e:
            print("Error al obtener velocidad mensual celda: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadFechasMes(tabla, idcomponente, listaceldas, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in listaceldas])
        params = [idcomponente] + listaceldas + [fechaini] + [fechafin]
        conn = None
        sql = f"""WITH IncrementalCTE AS (
            SELECT t.id_instrumentacion, c.nombre_celda, cd.fecha_detalle,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) / 86400.0 AS FLOAT) AS dias,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) / 3600.0 AS FLOAT) AS horas,
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
            INNER JOIN componentes c ON t.id_componente = c.id_componente
            WHERE c.id_componente = ? AND t.id_instrumentacion IN ({placeholders})
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
            return rows if rows else None
        except Exception as e:
            print("Error al obtener velocidad mensual celda: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlObtenerAsentamientoCota(tabla, idcomponente, listaceldas):
        placeholders = ', '.join(['?' for _ in listaceldas])
        params = [idcomponente] + listaceldas
        conn = None
        sql = f"""SELECT t.id_instrumentacion, c.nombre_celda, cd.fecha_detalle,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) / 86400.0 AS FLOAT) AS dias,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) / 3600.0 AS FLOAT) AS horas,
            c.instalacion_celda - abs(cd.medida_calculada) AS cota_piezometrica, c.fundacion_celda,
            COALESCE(
                (SELECT TOP 1 c2.nivel_cota FROM cotas_celdas c2 WHERE c2.id_celda = c.id_celda 
                AND c2.fecha_cota <= cd.fecha_detalle ORDER BY c2.fecha_cota DESC),
                (SELECT TOP 1 c3.nivel_cota FROM cotas_celdas c3 WHERE c3.id_celda = c.id_celda 
                ORDER BY c3.fecha_cota ASC)
            ) AS superficie, t.tipo_equipo, t.id_equipo
        FROM celdas c INNER JOIN {tabla} cd ON c.id_celda = cd.id_celda
        INNER JOIN instrumentacion t ON c.id_celda = t.id_equipo
        INNER JOIN componentes c ON t.id_componente = c.id_componente
        WHERE c.id_componente = ? AND t.id_instrumentacion IN ({placeholders}) AND cd.estado_detalle = 1
        ORDER BY c.nombre_celda ASC, cd.fecha_detalle ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return rows if rows else None
        except Exception as e:
            print("Error al obtener asentamiento cota: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlObtenerAsentamientoFechasCota(tabla, idcomponente, listaceldas, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in listaceldas])
        params = [idcomponente] + listaceldas + [fechaini] + [fechafin]
        conn = None
        sql = f"""SELECT t.id_instrumentacion, c.nombre_celda, cd.fecha_detalle,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) / 86400.0 AS FLOAT) AS dias,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) / 3600.0 AS FLOAT) AS horas,
            c.instalacion_celda - abs(cd.medida_calculada) AS cota_piezometrica, c.fundacion_celda,
            COALESCE(
                (SELECT TOP 1 c2.nivel_cota FROM cotas_celdas c2 WHERE c2.id_celda = c.id_celda 
                AND c2.fecha_cota <= cd.fecha_detalle ORDER BY c2.fecha_cota DESC),
                (SELECT TOP 1 c3.nivel_cota FROM cotas_celdas c3 WHERE c3.id_celda = c.id_celda 
                ORDER BY c3.fecha_cota ASC)
            ) AS superficie,t.tipo_equipo,t.id_equipo
        FROM celdas c INNER JOIN {tabla} cd ON c.id_celda = cd.id_celda
        INNER JOIN instrumentacion t ON c.id_celda = t.id_equipo
        INNER JOIN componentes c ON t.id_componente = c.id_componente
        WHERE c.id_componente = ? AND t.id_instrumentacion IN ({placeholders})
        AND cd.estado_detalle = 1 AND cd.fecha_detalle BETWEEN ? AND ?
        ORDER BY c.nombre_celda ASC, cd.fecha_detalle ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return rows if rows else None
        except Exception as e:
            print("Error al obtener asentamiento cota: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlCalcularAsentamientoIncremental(tabla, idcomponente, listaceldas, unidadmedida):
        placeholders = ', '.join(['?' for _ in listaceldas])
        params = [unidadmedida] + [idcomponente] + listaceldas
        sql = f"""SELECT t.id_instrumentacion, c.nombre_celda, cd.fecha_detalle,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) / 86400.0 AS FLOAT) AS dias,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) / 3600.0 AS FLOAT) AS horas,
            COALESCE(cd.medida_calculada - LAG(cd.medida_calculada) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle ASC), 0) * ? AS incremental, c.fundacion_celda,
            COALESCE(
                (SELECT TOP 1 c2.nivel_cota FROM cotas_celdas c2 WHERE c2.id_celda = c.id_celda 
                AND c2.fecha_cota <= cd.fecha_detalle ORDER BY c2.fecha_cota DESC),
                (SELECT TOP 1 c3.nivel_cota FROM cotas_celdas c3 WHERE c3.id_celda = c.id_celda 
                ORDER BY c3.fecha_cota ASC)
            ) AS superficie, t.tipo_equipo, t.id_equipo
        FROM celdas c INNER JOIN {tabla} cd ON c.id_celda = cd.id_celda
        INNER JOIN instrumentacion t ON c.id_celda = t.id_equipo
        INNER JOIN componentes c ON t.id_componente = c.id_componente
        WHERE c.id_componente = ? AND t.id_instrumentacion IN ({placeholders}) AND cd.estado_detalle = 1
        ORDER BY c.nombre_celda ASC, cd.fecha_detalle ASC;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return rows if rows else None
        except Exception as e:
            print("Error al obtener asentamiento incremental: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlCalcularAsentamientoFechasIncremental(tabla, idcomponente, listaceldas, fechaini, fechafin, unidadmedida):
        placeholders = ', '.join(['?' for _ in listaceldas])
        params = [unidadmedida] + [idcomponente] + listaceldas + [fechaini] + [fechafin]
        conn = None
        sql = f"""SELECT t.id_instrumentacion, c.nombre_celda, cd.fecha_detalle,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) / 86400.0 AS FLOAT) AS dias,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) / 3600.0 AS FLOAT) AS horas,
            COALESCE(cd.medida_calculada - LAG(cd.medida_calculada) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle ASC), 0) * ? AS incremental, c.fundacion_celda,
            COALESCE(
                (SELECT TOP 1 c2.nivel_cota FROM cotas_celdas c2 WHERE c2.id_celda = c.id_celda 
                AND c2.fecha_cota <= cd.fecha_detalle ORDER BY c2.fecha_cota DESC),
                (SELECT TOP 1 c3.nivel_cota FROM cotas_celdas c3 WHERE c3.id_celda = c.id_celda 
                ORDER BY c3.fecha_cota ASC)
            ) AS superficie,t.tipo_equipo,t.id_equipo
        FROM celdas c INNER JOIN {tabla} cd ON c.id_celda = cd.id_celda
        INNER JOIN instrumentacion t ON c.id_celda = t.id_equipo
        INNER JOIN componentes c ON t.id_componente = c.id_componente
        WHERE c.id_componente = ? AND t.id_instrumentacion IN ({placeholders})
        AND cd.estado_detalle = 1 AND cd.fecha_detalle BETWEEN ? AND ?
        ORDER BY c.nombre_celda ASC, cd.fecha_detalle ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return rows if rows else None
        except Exception as e:
            print("Error al obtener asentamiento incremental: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlObtenerAsentamientoAcumulado(tabla, idcomponente, listaceldas, unidadmedida):
        placeholders = ', '.join(['?' for _ in listaceldas])
        params = [unidadmedida] + [idcomponente] + listaceldas
        conn = None
        sql = f"""SELECT t.id_instrumentacion, c.nombre_celda, cd.fecha_detalle,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) / 86400.0 AS FLOAT) AS dias,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) / 3600.0 AS FLOAT) AS horas,
            cd.medida_calculada * ? AS medida_calculada, c.fundacion_celda,
            COALESCE(
                (SELECT TOP 1 c2.nivel_cota FROM cotas_celdas c2 WHERE c2.id_celda = c.id_celda 
                AND c2.fecha_cota <= cd.fecha_detalle ORDER BY c2.fecha_cota DESC),
                (SELECT TOP 1 c3.nivel_cota FROM cotas_celdas c3 WHERE c3.id_celda = c.id_celda 
                ORDER BY c3.fecha_cota ASC)
            ) AS superficie, t.tipo_equipo, t.id_equipo
        FROM celdas c INNER JOIN {tabla} cd ON c.id_celda = cd.id_celda
        INNER JOIN instrumentacion t ON c.id_celda = t.id_equipo
        INNER JOIN componentes c ON t.id_componente = c.id_componente
        WHERE c.id_componente = ? AND t.id_instrumentacion IN ({placeholders}) AND cd.estado_detalle = 1
        ORDER BY c.nombre_celda ASC, cd.fecha_detalle ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return rows if rows else None
        except Exception as e:
            print("Error al obtener asentamiento acumulado: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlObtenerAsentamientoFechasAcumulado(tabla, idcomponente, listaceldas, fechaini, fechafin, unidadmedida):
        placeholders = ', '.join(['?' for _ in listaceldas])
        params = [unidadmedida] + [idcomponente] + listaceldas + [fechaini] + [fechafin]
        conn = None
        sql = f"""SELECT t.id_instrumentacion, c.nombre_celda, cd.fecha_detalle,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) / 86400.0 AS FLOAT) AS dias,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) / 3600.0 AS FLOAT) AS horas,
            cd.medida_calculada * ? AS medida_calculada, c.fundacion_celda,
            COALESCE(
                (SELECT TOP 1 c2.nivel_cota FROM cotas_celdas c2 WHERE c2.id_celda = c.id_celda 
                AND c2.fecha_cota <= cd.fecha_detalle ORDER BY c2.fecha_cota DESC),
                (SELECT TOP 1 c3.nivel_cota FROM cotas_celdas c3 WHERE c3.id_celda = c.id_celda 
                ORDER BY c3.fecha_cota ASC)
            ) AS superficie, t.tipo_equipo, t.id_equipo
        FROM celdas c INNER JOIN {tabla} cd ON c.id_celda = cd.id_celda
        INNER JOIN instrumentacion t ON c.id_celda = t.id_equipo
        INNER JOIN componentes c ON t.id_componente = c.id_componente
        WHERE c.id_componente = ? AND t.id_instrumentacion IN ({placeholders})
        AND cd.estado_detalle = 1 AND cd.fecha_detalle BETWEEN ? AND ?
        ORDER BY c.nombre_celda ASC, cd.fecha_detalle ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return rows if rows else None
        except Exception as e:
            print("Error al obtener asentamiento acumulado: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlObtenerAsentamientoFrecuencia(tabla, idcomponente, listaceldas):
        placeholders = ', '.join(['?' for _ in listaceldas])
        params = [idcomponente] + listaceldas
        conn = None
        sql = f"""SELECT t.id_instrumentacion, c.nombre_celda, cd.fecha_detalle,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) / 86400.0 AS FLOAT) AS dias,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) / 3600.0 AS FLOAT) AS horas,
            cd.frecuencia_hz, c.fundacion_celda,
            COALESCE(
                (SELECT TOP 1 c2.nivel_cota FROM cotas_celdas c2 WHERE c2.id_celda = c.id_celda 
                AND c2.fecha_cota <= cd.fecha_detalle ORDER BY c2.fecha_cota DESC),
                (SELECT TOP 1 c3.nivel_cota FROM cotas_celdas c3 WHERE c3.id_celda = c.id_celda 
                ORDER BY c3.fecha_cota ASC)
            ) AS superficie, t.tipo_equipo, t.id_equipo
        FROM celdas c INNER JOIN {tabla} cd ON c.id_celda = cd.id_celda
        INNER JOIN instrumentacion t ON c.id_celda = t.id_equipo
        INNER JOIN componentes c ON t.id_componente = c.id_componente
        WHERE c.id_componente = ? AND t.id_instrumentacion IN ({placeholders}) AND cd.estado_detalle = 1
        ORDER BY c.nombre_celda ASC, cd.fecha_detalle ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return rows if rows else None
        except Exception as e:
            print("Error al obtener frecuencia celdas: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlObtenerAsentamientoFechasFrecuencia(tabla, idcomponente, listaceldas, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in listaceldas])
        params = [idcomponente] + listaceldas + [fechaini] + [fechafin]
        conn = None
        sql = f"""SELECT t.id_instrumentacion, c.nombre_celda, cd.fecha_detalle,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) / 86400.0 AS FLOAT) AS dias,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) / 3600.0 AS FLOAT) AS horas,
            cd.frecuencia_hz, c.fundacion_celda,
            COALESCE(
                (SELECT TOP 1 c2.nivel_cota FROM cotas_celdas c2 WHERE c2.id_celda = c.id_celda 
                AND c2.fecha_cota <= cd.fecha_detalle ORDER BY c2.fecha_cota DESC),
                (SELECT TOP 1 c3.nivel_cota FROM cotas_celdas c3 WHERE c3.id_celda = c.id_celda 
                ORDER BY c3.fecha_cota ASC)
            ) AS superficie, t.tipo_equipo, t.id_equipo
        FROM celdas c INNER JOIN {tabla} cd ON c.id_celda = cd.id_celda
        INNER JOIN instrumentacion t ON c.id_celda = t.id_equipo
        INNER JOIN componentes c ON t.id_componente = c.id_componente
        WHERE c.id_componente = ? AND t.id_instrumentacion IN ({placeholders})
        AND cd.estado_detalle = 1 AND cd.fecha_detalle BETWEEN ? AND ?
        ORDER BY c.nombre_celda ASC, cd.fecha_detalle ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return rows if rows else None
        except Exception as e:
            print("Error al obtener frecuencia celdas fechas: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlObtenerAsentamientoTemperatura(tabla, idcomponente, listaceldas):
        placeholders = ', '.join(['?' for _ in listaceldas])
        params = [idcomponente] + listaceldas
        conn = None
        sql = f"""SELECT t.id_instrumentacion, c.nombre_celda, cd.fecha_detalle,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) / 86400.0 AS FLOAT) AS dias,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) / 3600.0 AS FLOAT) AS horas,
            cd.temperatura_detalle, c.fundacion_celda,
            COALESCE(
                (SELECT TOP 1 c2.nivel_cota FROM cotas_celdas c2 WHERE c2.id_celda = c.id_celda 
                AND c2.fecha_cota <= cd.fecha_detalle ORDER BY c2.fecha_cota DESC),
                (SELECT TOP 1 c3.nivel_cota FROM cotas_celdas c3 WHERE c3.id_celda = c.id_celda 
                ORDER BY c3.fecha_cota ASC)
            ) AS superficie, t.tipo_equipo, t.id_equipo
        FROM celdas c INNER JOIN {tabla} cd ON c.id_celda = cd.id_celda
        INNER JOIN instrumentacion t ON c.id_celda = t.id_equipo
        INNER JOIN componentes c ON t.id_componente = c.id_componente
        WHERE c.id_componente = ? AND t.id_instrumentacion IN ({placeholders}) AND cd.estado_detalle = 1
        ORDER BY c.nombre_celda ASC, cd.fecha_detalle ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return rows if rows else None
        except Exception as e:
            print("Error al obtener temperatura celdas: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlObtenerAsentamientoFechasTemperatura(tabla, idcomponente, listaceldas, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in listaceldas])
        params = [idcomponente] + listaceldas + [fechaini] + [fechafin]
        conn = None
        sql = f"""SELECT t.id_instrumentacion, c.nombre_celda, cd.fecha_detalle,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) / 86400.0 AS FLOAT) AS dias,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(cd.fecha_detalle) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle), cd.fecha_detalle) / 3600.0 AS FLOAT) AS horas,
            cd.temperatura_detalle, c.fundacion_celda,
            COALESCE(
                (SELECT TOP 1 c2.nivel_cota FROM cotas_celdas c2 WHERE c2.id_celda = c.id_celda 
                AND c2.fecha_cota <= cd.fecha_detalle ORDER BY c2.fecha_cota DESC),
                (SELECT TOP 1 c3.nivel_cota FROM cotas_celdas c3 WHERE c3.id_celda = c.id_celda 
                ORDER BY c3.fecha_cota ASC)
            ) AS superficie, t.tipo_equipo, t.id_equipo
        FROM celdas c INNER JOIN {tabla} cd ON c.id_celda = cd.id_celda
        INNER JOIN instrumentacion t ON c.id_celda = t.id_equipo
        INNER JOIN componentes c ON t.id_componente = c.id_componente
        WHERE c.id_componente = ? AND t.id_instrumentacion IN ({placeholders})
        AND cd.estado_detalle = 1 AND cd.fecha_detalle BETWEEN ? AND ?
        ORDER BY c.nombre_celda ASC, cd.fecha_detalle ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return rows if rows else None
        except Exception as e:
            print("Error al obtener temperatura celdas fechas: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlActualizarLecturaCelda(tabla, data, idproyecto, username, nombres):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # guardar en historial
            query_select = f"""SELECT fecha_detalle, frecuencia_digits, frecuencia_hz, temperatura_detalle, medida_calculada,
            observacion_detalle, id_detalle FROM {tabla} WHERE id_detalle = ?;"""
            cursor.execute(query_select, (data[-1],))
            datos_anteriores = cursor.fetchone()
            if datos_anteriores:
                fecha_cambio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                accion = "update"
                # Convertir a tupla o string para que no falle el format
                cambios = f"Antiguos: {tuple(datos_anteriores)}, Nuevos: {data}"
                query_historial = """INSERT INTO historial (idproyecto, fecha, accion, tabla, cambios, usuario, nombres)
                VALUES (?, ?, ?, ?, ?, ?, ?);"""
                cursor.execute(query_historial, (idproyecto, fecha_cambio, accion, tabla, cambios, username, nombres))
            # actualizar prisma
            query = f"""UPDATE {tabla} SET fecha_detalle = ?, frecuencia_digits = ?, frecuencia_hz = ?, temperatura_detalle = ?,
            medida_calculada = ?, observacion_detalle = ? WHERE id_detalle = ?;"""
            cursor.execute(query, data)
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al actualizar lectura celda: {e}")
            return False
        finally:
            if conn: conn.close()
    
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
            if conn: conn.close()
    
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
            if conn: conn.close()
    
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
            if conn: conn.close()
    
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
                # Convertir lista de rows a string
                cambios = f"Datos: {[tuple(r) for r in datos_anteriores]}"
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
            if conn: conn.close()
    
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
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener datos:", e)
            return None
        finally:
            if conn: conn.close()
                
    @staticmethod
    def mdlRegistrarDataCelda(proyectoid, data, idsceldas):
        conn = None
        table_name = f"celda_detalle{proyectoid}"
        
        # LOGICA CREACION TABLA SQL SERVER
        sqltable = f"""IF OBJECT_ID(N'dbo.{table_name}', N'U') IS NULL
        CREATE TABLE {table_name} (
                [id_detalle] INT IDENTITY(1,1) NOT NULL,
                [id_celda] INT NOT NULL,
                [fecha_detalle] DATETIME NOT NULL,
                [frecuencia_digits] FLOAT,
                [frecuencia_hz] FLOAT,
                [temperatura_detalle] FLOAT,
                [medida_calculada] FLOAT,
                [observacion_detalle] NVARCHAR(MAX),
                [estado_detalle] INT DEFAULT ((1)),
                CONSTRAINT [PK_{table_name}] PRIMARY KEY CLUSTERED ([id_detalle])
        );"""
        
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            
            # Crear tabla (pyodbc no necesita PRAGMAs)
            cursor.execute(sqltable)
            conn.commit()
            
            # Obtener datos existentes para evitar duplicados
            placeholders = ','.join(['?'] * len(idsceldas))
            
            # Convertir idsceldas a lista para pyodbc
            ids_lista = list(idsceldas)
            check_sql = f"SELECT id_celda, fecha_detalle FROM {table_name} WHERE id_celda IN ({placeholders});"
            cursor.execute(check_sql, ids_lista)
            
            # Crear set de tuplas (id, fecha_str) para búsqueda rápida
            existen_celdas = set()
            for row in cursor.fetchall():
                # SQL Server devuelve datetime, lo pasamos a str para comparar con lo que viene del excel
                fecha_formateada = row[1].strftime('%Y-%m-%d %H:%M:%S') if isinstance(row[1], datetime) else str(row[1])
                existen_celdas.add((row[0], fecha_formateada))

            lote_registros = []
            
            for fila in data:
                id_celda = fila[0]
                fecha_original = fila[1] # YYYY-MM-DD
                hora_original = fila[2]  # HH:MM:SS
                fecha_hora_nueva = f"{fecha_original} {hora_original}"
                
                # Verifica si no existe
                if (id_celda, fecha_hora_nueva) not in existen_celdas:
                    # Tupla para pyodbc
                    datito = (
                        id_celda,
                        fecha_hora_nueva,
                        fila[3], # freq dig
                        fila[4], # freq hz
                        fila[5], # temp
                        fila[6], # medida
                        fila[7]  # obs
                    )
                    lote_registros.append(datito)

            if lote_registros:
                insert_query = f"""INSERT INTO {table_name} (id_celda, fecha_detalle, frecuencia_digits, frecuencia_hz, temperatura_detalle, medida_calculada, observacion_detalle) VALUES (?, ?, ?, ?, ?, ?, ?);"""
                # Insertar todo el lote (pyodbc maneja transacciones auto)
                cursor.executemany(insert_query, lote_registros)
                conn.commit()
            
            return True
        except Exception as e:
            print("Error al guardar las celdas: " + str(e))
            if conn: conn.rollback()
            return False
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlCambiarComponenteCeldas(idcomponente, nuevocomponente):
        sql = """UPDATE instrumentacion SET id_componente = ? WHERE id_componente = ? AND tipo_equipo = 'CELDA';"""
        conn = None
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
            print("Error al cambiar componente celdas: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlEliminarCeldas(idcomponente):
        conn = None
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
            if conn: conn.close()
    
    @staticmethod
    def mdlEliminarDataCeldas(tabla, terrenos):
        placeholders = ','.join(['?' for _ in terrenos])
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # eliminar data
            query_delete = f"""DELETE FROM {tabla} WHERE id_celda IN ({placeholders});"""
            cursor.execute(query_delete, terrenos)
            
            # SQL Server rowcount funciona
            # Eliminamos tabla celdas (instrumento)
            stmt_delete = f"DELETE FROM celdas WHERE id_celda IN ({placeholders});"
            cursor.execute(stmt_delete, terrenos)
            rows_delete = cursor.rowcount
            
            conn.commit()
            return rows_delete > 0 # Retornamos True si borró algo de la tabla maestra
        except Exception as e:
            print(f"Error al eliminar data celdas: {e}")
            if conn: conn.rollback()
            return False
        finally:
            if conn: conn.close()
    
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
                return row
            else:
                return None
        except Exception as e:
            print("Error al consultar info celda: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
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
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            cursor.execute(query, valores)
            query_instrumentacion = """UPDATE instrumentacion SET id_componente = ?, nombre_equipo = ?
            WHERE id_instrumentacion = ? AND tipo_equipo = 'CELDA';"""
            datos = (
                data['componente'], data['nombre_celda'], data['instrumento']
            )
            cursor.execute(query_instrumentacion, datos)
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al actualizar celda: {e}")
            return False
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlActualizarCeldaExcel(data):
        query = """UPDATE celdas SET marca_celda = ?, modelo_celda = ?, rango_celda = ?, instalacion_celda = ?,
        este_celda = ?, norte_celda = ?, fundacion_celda = ?, cf_celda = ?, tk_celda = ? WHERE id_celda = ?;"""
        valores = (
            data['marca_celda'], data['modelo_celda'], data['rango_celda'], data['cota_instalacion_celda'],
            data['coordenada_este_celda'], data['coordenada_norte_celda'], data['cota_fundacion_celda'],
            data['cf_celda'], data['tk_celda'], data['idcelda']
        )
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            cursor.execute(query, valores)
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al actualizar celda: {e}")
            return False
        finally:
            if conn: conn.close()
                
    
    @staticmethod
    def mdlEliminarCelda(idinstrumento):
        conn = None
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
            if conn: conn.close()
    
    @staticmethod
    def mdlEliminarCeldaData(tabla, idcelda):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # eliminar data
            query_delete = f"""DELETE FROM {tabla} WHERE id_celda = ?;"""
            cursor.execute(query_delete, (idcelda,))
            # SQL Server mantiene el rowcount acumulado o del último statement, 
            # pero aquí es seguro borrar maestro después
            
            stmt_delete = "DELETE FROM celdas WHERE id_celda = ?;"
            cursor.execute(stmt_delete, (idcelda,))
            rows_delete = cursor.rowcount
            
            conn.commit()
            return rows_delete > 0
        except Exception as e:
            print(f"Error al eliminar data celda: {e}")
            if conn: conn.rollback()
            return False
        finally:
            if conn: conn.close()
    
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
                return row
            else:
                return None
        except Exception as e:
            print("Error al traer data celda: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
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
            if conn: conn.close()
    
    @staticmethod
    def mdlOmitirLecturaCelda(tabla, idCelda, fecha):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            query_update = f"""UPDATE {tabla} SET estado_detalle = 0 WHERE id_celda = ? AND fecha_detalle=?;"""
            cursor.execute(query_update, (idCelda, fecha))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al omitir lecturas de Celda: {e}")
            return False
        finally:
            if conn: conn.close()