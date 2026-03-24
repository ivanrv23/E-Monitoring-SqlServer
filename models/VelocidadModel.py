from services.security.apis.conexiones.connection import Connection
import pyodbc

class VelocidadModel:
    
    @staticmethod
    def mdlCalcularVelocidadVISD(tabla, unidad, prismas, idcomponente):
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente]
        
        # SQL Server Syntax (T-SQL)
        # Nota: DATEDIFF(SECOND, start, end) / 86400.0 simula la resta de JULIANDAY para obtener días con decimales.
        sql = f"""WITH velocidad AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0 AS dias,
                CAST(DATEDIFF(SECOND, COALESCE(LAG(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0 AS dif_fechas,
                (p.distancia_prisma - FIRST_VALUE(CAST(p.distancia_prisma AS FLOAT)) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * ? AS SD,
                i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        ),
        CD_Dif AS (
            SELECT id_instrumentacion, nombre_prisma, hora_prisma, dias, dif_fechas, SD,
                SD - COALESCE(LAG(SD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), SD) AS dif_sd,
                CASE
                    WHEN dif_fechas = 0 THEN 0
                    ELSE (SD - COALESCE(LAG(SD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), SD)) / dif_fechas
                END AS VISD,
                tipo_equipo
            FROM velocidad
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS, VISD, tipo_equipo
        FROM CD_Dif
        ORDER BY nombre_prisma, hora_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                # Convertir pyodbc.Row a tupla para mantener compatibilidad con el frontend (igual que sqlite3)
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error al consultar visd: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadFechasVISD(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""WITH CD AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0 AS dias,
                CAST(DATEDIFF(SECOND, COALESCE(LAG(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0 AS dif_fechas,
                (p.distancia_prisma - FIRST_VALUE(CAST(p.distancia_prisma AS FLOAT)) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * ? AS SD,
                i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ?
        ),
        CD_Dif AS (
            SELECT id_instrumentacion, nombre_prisma, hora_prisma, dias, dif_fechas, SD,
                SD - COALESCE(LAG(SD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), SD) AS dif_sd,
                CASE
                    WHEN dif_fechas = 0 THEN 0
                    ELSE (SD - COALESCE(LAG(SD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), SD)) / dif_fechas
                END AS VISD,
                tipo_equipo
            FROM CD
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS, VISD, tipo_equipo
        FROM CD_Dif
        ORDER BY nombre_prisma, hora_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error al consultar visd fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadDiasVISD(tabla, unidad, prismas, idcomponente, cantidad):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]
        
        # T-SQL cambios: DATE() -> CAST(AS DATE), AVG(CAST(AS FLOAT)), JULIANDAY Logic -> DATEDIFF
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, CAST(p.hora_prisma AS DATE) AS fecha, MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.distancia_prisma AS FLOAT)) AS promedio_distancia,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad} ) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), f.fecha_inicio, i.id_instrumentacion, i.tipo_equipo
        ),
        velocidad AS (
            SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0 AS dias,
                CAST(DATEDIFF(SECOND, COALESCE(LAG(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0 AS dif_fechas,
                (b.promedio_distancia - FIRST_VALUE(CAST(b.promedio_distancia AS FLOAT)) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma)) * ? AS SD,
                b.tipo_equipo,
                b.bloque_dias -- Agregado para ordenar en la CTE
            FROM bloques b
        ),
        CD_Dif AS (
            SELECT id_instrumentacion, nombre_prisma, hora_prisma, dias, dif_fechas, SD,
                SD - COALESCE(LAG(SD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), SD) AS dif_sd,
                CASE
                    WHEN dif_fechas = 0 THEN 0
                    ELSE (SD - COALESCE(LAG(SD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), SD)) / dif_fechas
                END AS VISD,
                tipo_equipo
            FROM velocidad
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS, VISD, tipo_equipo
        FROM CD_Dif
        ORDER BY nombre_prisma, hora_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error al consultar prom dias visd: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadDiasFechasVISD(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, CAST(p.hora_prisma AS DATE) AS fecha, MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.distancia_prisma AS FLOAT)) AS promedio_distancia,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad} ) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), f.fecha_inicio, i.id_instrumentacion, i.tipo_equipo
        ),
        velocidad AS (
            SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0 AS dias,
                CAST(DATEDIFF(SECOND, COALESCE(LAG(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0 AS dif_fechas,
                (b.promedio_distancia - FIRST_VALUE(CAST(b.promedio_distancia AS FLOAT)) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma)) * ? AS SD,
                b.tipo_equipo,
                b.bloque_dias
            FROM bloques b
        ),
        CD_Dif AS (
            SELECT id_instrumentacion, nombre_prisma, hora_prisma, dias, dif_fechas, SD,
                SD - COALESCE(LAG(SD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), SD) AS dif_sd,
                CASE
                    WHEN dif_fechas = 0 THEN 0
                    ELSE (SD - COALESCE(LAG(SD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), SD)) / dif_fechas
                END AS VISD,
                tipo_equipo
            FROM velocidad
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS, VISD, tipo_equipo
        FROM CD_Dif
        ORDER BY nombre_prisma, hora_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error al consultar prom dias visd fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadHorasVISD(tabla, unidad, prismas, idcomponente, cantidad):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]
        
        # T-SQL cambios: STRFTIME('%H') -> DATEPART(HOUR, ...)
        sql = f"""WITH promedios_horas AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque,
                MAX(p.hora_prisma) AS hora_prisma, AVG(CAST(p.distancia_prisma AS FLOAT)) AS promedio_distancia,
                i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad}, i.id_instrumentacion, i.tipo_equipo
        ),
        velocidad AS (
            SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0 AS dias,
                CAST(DATEDIFF(SECOND, COALESCE(LAG(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0 AS dif_fechas,
                (pd.promedio_distancia - FIRST_VALUE(CAST(pd.promedio_distancia AS FLOAT)) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma)) * ? AS SD,
                pd.tipo_equipo,
                pd.fecha, pd.bloque -- Para ordenamiento si es necesario
            FROM promedios_horas pd
        ),
        CD_Dif AS (
            SELECT id_instrumentacion, nombre_prisma, hora_prisma, dias, dif_fechas, SD,
                SD - COALESCE(LAG(SD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), SD) AS dif_sd,
                CASE
                    WHEN dif_fechas = 0 THEN 0
                    ELSE (SD - COALESCE(LAG(SD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), SD)) / dif_fechas
                END AS VISD,
                tipo_equipo
            FROM velocidad
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS, VISD, tipo_equipo
        FROM CD_Dif
        ORDER BY nombre_prisma, hora_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error al consultar prom horas visd: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadHorasFechasVISD(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        
        sql = f"""WITH promedios_horas AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque,
                MAX(p.hora_prisma) AS hora_prisma, AVG(CAST(p.distancia_prisma AS FLOAT)) AS promedio_distancia,
                i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad}, i.id_instrumentacion, i.tipo_equipo
        ),
        velocidad AS (
            SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0 AS dias,
                CAST(DATEDIFF(SECOND, COALESCE(LAG(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0 AS dif_fechas,
                (pd.promedio_distancia - FIRST_VALUE(CAST(pd.promedio_distancia AS FLOAT)) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma)) * ? AS SD,
                pd.tipo_equipo,
                pd.fecha, pd.bloque
            FROM promedios_horas pd
        ),
        CD_Dif AS (
            SELECT id_instrumentacion, nombre_prisma, hora_prisma, dias, dif_fechas, SD,
                SD - COALESCE(LAG(SD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), SD) AS dif_sd,
                CASE
                    WHEN dif_fechas = 0 THEN 0
                    ELSE (SD - COALESCE(LAG(SD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), SD)) / dif_fechas
                END AS VISD,
                tipo_equipo
            FROM velocidad
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS, VISD, tipo_equipo
        FROM CD_Dif
        ORDER BY nombre_prisma, hora_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error al consultar prom horas visd fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadVASD(tabla, unidad, prismas, idcomponente):
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente]
        
        sql = f"""WITH CD AS (
            SELECT id_instrumentacion, p.nombre_prisma, p.hora_prisma,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0 AS dif_fechas,
                (p.distancia_prisma - FIRST_VALUE(CAST(p.distancia_prisma AS FLOAT)) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * ? AS SD,
                i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        ),
        CD_Dif AS (
            SELECT id_instrumentacion, nombre_prisma, hora_prisma, dif_fechas, SD,
                SD - FIRST_VALUE(SD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) AS dif_sd,
                CASE
                    WHEN dif_fechas = 0 THEN 0
                    ELSE (SD - FIRST_VALUE(SD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma)) / dif_fechas
                END AS VASD,
                tipo_equipo
            FROM CD
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dif_fechas AS DIAS, dif_fechas * 24.0 AS HORAS, VASD, tipo_equipo
        FROM CD_Dif
        ORDER BY nombre_prisma, hora_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error al consultar vasd: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
                
    @staticmethod
    def mdlCalcularVelocidadFechasVASD(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente] + [fechaini] + [fechafin]
        
        # T-SQL: Reemplazo de JULIANDAY por DATEDIFF/86400.0
        sql = f"""WITH CD AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0 AS dif_fechas,
                (p.distancia_prisma - FIRST_VALUE(CAST(p.distancia_prisma AS FLOAT)) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * ? AS SD,
                i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ?
        ),
        CD_Dif AS (
            SELECT id_instrumentacion, nombre_prisma, hora_prisma, dif_fechas, SD,
                SD - FIRST_VALUE(SD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) AS dif_sd,
                CASE
                    WHEN dif_fechas = 0 THEN 0
                    ELSE (SD - FIRST_VALUE(SD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma)) / dif_fechas
                END AS VASD,
                tipo_equipo
            FROM CD
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dif_fechas AS DIAS, dif_fechas * 24.0 AS HORAS, VASD, tipo_equipo
        FROM CD_Dif
        ORDER BY nombre_prisma, hora_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error al consultar vasd fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadDiasVASD(tabla, unidad, prismas, idcomponente, cantidad):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]
        
        # T-SQL: DATE() -> CAST(AS DATE), manejo de FLOAT en promedios
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, CAST(p.hora_prisma AS DATE) AS fecha, MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.distancia_prisma AS FLOAT)) AS promedio_distancia,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad} ) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), f.fecha_inicio, i.id_instrumentacion, i.tipo_equipo
        ),
        velocidad AS (
            SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0 AS dif_fechas,
                (b.promedio_distancia - FIRST_VALUE(CAST(b.promedio_distancia AS FLOAT)) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma)) * ? AS SD,
                b.tipo_equipo,
                b.bloque_dias
            FROM bloques b
        ),
        CD_Dif AS (
            SELECT id_instrumentacion, nombre_prisma, hora_prisma, dif_fechas, SD,
                SD - FIRST_VALUE(SD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) AS dif_sd,
                CASE
                    WHEN dif_fechas = 0 THEN 0
                    ELSE (SD - FIRST_VALUE(SD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma)) / dif_fechas
                END AS VASD,
                tipo_equipo
            FROM velocidad
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dif_fechas AS DIAS, dif_fechas * 24.0 AS HORAS, VASD, tipo_equipo
        FROM CD_Dif
        ORDER BY nombre_prisma, hora_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error al consultar prom dias vasd: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadDiasFechasVASD(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, CAST(p.hora_prisma AS DATE) AS fecha, MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.distancia_prisma AS FLOAT)) AS promedio_distancia,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad} ) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), f.fecha_inicio, i.id_instrumentacion, i.tipo_equipo
        ),
        velocidad AS (
            SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0 AS dif_fechas,
                (b.promedio_distancia - FIRST_VALUE(CAST(b.promedio_distancia AS FLOAT)) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma)) * ? AS SD,
                b.tipo_equipo,
                b.bloque_dias
            FROM bloques b
        ),
        CD_Dif AS (
            SELECT id_instrumentacion, nombre_prisma, hora_prisma, dif_fechas, SD,
                SD - FIRST_VALUE(SD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) AS dif_sd,
                CASE
                    WHEN dif_fechas = 0 THEN 0
                    ELSE (SD - FIRST_VALUE(SD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma)) / dif_fechas
                END AS VASD,
                tipo_equipo
            FROM velocidad
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dif_fechas AS DIAS, dif_fechas * 24.0 AS HORAS, VASD, tipo_equipo
        FROM CD_Dif
        ORDER BY nombre_prisma, hora_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error al consultar prom dias vasd fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadHorasVASD(tabla, unidad, prismas, idcomponente, cantidad):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]
        
        # T-SQL: DATEPART para horas, DATEDIFF para dias
        sql = f"""WITH promedios_horas AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque,
                MAX(p.hora_prisma) AS hora_prisma, AVG(CAST(p.distancia_prisma AS FLOAT)) AS promedio_distancia,
                i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad}, i.id_instrumentacion, i.tipo_equipo
        ),
        velocidad AS (
            SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0 AS dif_fechas,
                (pd.promedio_distancia - FIRST_VALUE(CAST(pd.promedio_distancia AS FLOAT)) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma)) * ? AS SD,
                pd.tipo_equipo,
                pd.fecha, pd.bloque
            FROM promedios_horas pd
        ),
        CD_Dif AS (
            SELECT id_instrumentacion, nombre_prisma, hora_prisma, dif_fechas, SD,
                SD - FIRST_VALUE(SD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) AS dif_sd,
                CASE
                    WHEN dif_fechas = 0 THEN 0
                    ELSE (SD - FIRST_VALUE(SD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma)) / dif_fechas
                END AS VASD,
                tipo_equipo
            FROM velocidad
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dif_fechas AS DIAS, dif_fechas * 24.0 AS HORAS, VASD, tipo_equipo
        FROM CD_Dif
        ORDER BY nombre_prisma, hora_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error al consultar prom horas vasd: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadHorasFechasVASD(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        
        sql = f"""WITH promedios_horas AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque,
                MAX(p.hora_prisma) AS hora_prisma, AVG(CAST(p.distancia_prisma AS FLOAT)) AS promedio_distancia,
                i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad}, i.id_instrumentacion, i.tipo_equipo
        ),
        velocidad AS (
            SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0 AS dif_fechas,
                (pd.promedio_distancia - FIRST_VALUE(CAST(pd.promedio_distancia AS FLOAT)) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma)) * ? AS SD,
                pd.tipo_equipo,
                pd.fecha, pd.bloque
            FROM promedios_horas pd
        ),
        CD_Dif AS (
            SELECT id_instrumentacion, nombre_prisma, hora_prisma, dif_fechas, SD,
                SD - FIRST_VALUE(SD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) AS dif_sd,
                CASE
                    WHEN dif_fechas = 0 THEN 0
                    ELSE (SD - FIRST_VALUE(SD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma)) / dif_fechas
                END AS VASD,
                tipo_equipo
            FROM velocidad
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dif_fechas AS DIAS, dif_fechas * 24.0 AS HORAS, VASD, tipo_equipo
        FROM CD_Dif
        ORDER BY nombre_prisma, hora_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error al consultar prom horas vasd fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadVI2D(tabla, unidad, prismas, idcomponente):
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente]
        
        # T-SQL: POW -> POWER, ROW_NUMBER() se mantiene, JULIANDAY -> DATEDIFF
        sql = f"""WITH PrismasCTE AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0 AS dias,
                CASE
                    WHEN ROW_NUMBER() OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) = 1 THEN 0
                    ELSE 
                        SQRT(
                            POWER(p.este_target - LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                            POWER(p.norte_target - LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                        ) * ?
                END AS dosD,
                i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
            CASE
                WHEN ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) = 1 THEN 0
                ELSE (dosD - LAG(dosD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma))
                / (CAST(DATEDIFF(SECOND, LAG(hora_prisma, 1, hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0)
            END AS VI2D, tipo_equipo
        FROM PrismasCTE
        ORDER BY nombre_prisma, hora_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error al consultar vi2d: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadFechasVI2D(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""WITH PrismasCTE AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0 AS dias,
                CASE
                    WHEN ROW_NUMBER() OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) = 1 THEN 0
                    ELSE 
                        SQRT(
                            POWER(p.este_target - LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                            POWER(p.norte_target - LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                        ) * ?
                END AS dosD,
                i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ?
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
            CASE
                WHEN ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) = 1 THEN 0
                ELSE (dosD - LAG(dosD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma))
                / (CAST(DATEDIFF(SECOND, LAG(hora_prisma, 1, hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0)
            END AS VI2D, tipo_equipo
        FROM PrismasCTE
        ORDER BY nombre_prisma, hora_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error al consultar vi2d fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadDiasVI2D(tabla, unidad, prismas, idcomponente, cantidad):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, CAST(p.hora_prisma AS DATE) AS fecha, MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.este_target AS FLOAT)) AS promedio_este,
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad} ) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), f.fecha_inicio, i.id_instrumentacion, i.tipo_equipo
        ),
        velocidad AS (
            SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma, b.promedio_este, b.promedio_norte,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0 AS dias,
                CASE
                    WHEN ROW_NUMBER() OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma) = 1 THEN 0
                    ELSE 
                        SQRT(
                            POWER(b.promedio_este - LAG(b.promedio_este) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2) +
                            POWER(b.promedio_norte - LAG(b.promedio_norte) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2)
                        ) * ?
                END AS dosD,
                b.tipo_equipo,
                b.bloque_dias
            FROM bloques b
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
            CASE
                WHEN ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) = 1 THEN 0
                ELSE (dosD - LAG(dosD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma))
                / (CAST(DATEDIFF(SECOND, LAG(hora_prisma, 1, hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0)
            END AS VI2D, tipo_equipo
        FROM velocidad
        ORDER BY nombre_prisma, hora_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error al consultar prom dias vi2d: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadDiasFechasVI2D(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, CAST(p.hora_prisma AS DATE) AS fecha, MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.este_target AS FLOAT)) AS promedio_este,
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad} ) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), f.fecha_inicio, i.id_instrumentacion, i.tipo_equipo
        ),
        velocidad AS (
            SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma, b.promedio_este, b.promedio_norte,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0 AS dias,
                CASE
                    WHEN ROW_NUMBER() OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma) = 1 THEN 0
                    ELSE 
                        SQRT(
                            POWER(b.promedio_este - LAG(b.promedio_este) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2) +
                            POWER(b.promedio_norte - LAG(b.promedio_norte) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2)
                        ) * ?
                END AS dosD,
                b.tipo_equipo,
                b.bloque_dias
            FROM bloques b
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
            CASE
                WHEN ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) = 1 THEN 0
                ELSE (dosD - LAG(dosD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma))
                / (CAST(DATEDIFF(SECOND, LAG(hora_prisma, 1, hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0)
            END AS VI2D, tipo_equipo
        FROM velocidad
        ORDER BY nombre_prisma, hora_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error al consultar prom dias vi2d fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadHorasVI2D(tabla, unidad, prismas, idcomponente, cantidad):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]
        
        # T-SQL: STRFTIME('%H') -> DATEPART(HOUR, ...)
        sql = f"""WITH promedios_horas AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.este_target AS FLOAT)) AS promedio_este,
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad}, i.id_instrumentacion, i.tipo_equipo
        ),
        velocidad AS (
            SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma, pd.promedio_este, pd.promedio_norte,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0 AS dias,
                CASE
                    WHEN ROW_NUMBER() OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma) = 1 THEN 0
                    ELSE 
                        SQRT(
                            POWER(pd.promedio_este - LAG(pd.promedio_este) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2) +
                            POWER(pd.promedio_norte - LAG(pd.promedio_norte) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2)
                        ) * ?
                END AS dosD,
                pd.tipo_equipo,
                pd.fecha, pd.bloque
            FROM promedios_horas pd
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
            CASE
                WHEN ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) = 1 THEN 0
                ELSE (dosD - LAG(dosD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma))
                / (CAST(DATEDIFF(SECOND, LAG(hora_prisma, 1, hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0)
            END AS VI2D, tipo_equipo
        FROM velocidad
        ORDER BY nombre_prisma, hora_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error al consultar prom horas vi2d: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadHorasFechasVI2D(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        
        sql = f"""WITH promedios_horas AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.este_target AS FLOAT)) AS promedio_este,
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad}, i.id_instrumentacion, i.tipo_equipo
        ),
        velocidad AS (
            SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma, pd.promedio_este, pd.promedio_norte,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0 AS dias,
                CASE
                    WHEN ROW_NUMBER() OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma) = 1 THEN 0
                    ELSE 
                        SQRT(
                            POWER(pd.promedio_este - LAG(pd.promedio_este) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2) +
                            POWER(pd.promedio_norte - LAG(pd.promedio_norte) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2)
                        ) * ?
                END AS dosD,
                pd.tipo_equipo,
                pd.fecha, pd.bloque
            FROM promedios_horas pd
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
            CASE
                WHEN ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) = 1 THEN 0
                ELSE (dosD - LAG(dosD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma))
                / (CAST(DATEDIFF(SECOND, LAG(hora_prisma, 1, hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0)
            END AS VI2D, tipo_equipo
        FROM velocidad
        ORDER BY nombre_prisma, hora_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error al consultar prom horas vi2d fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadVA2D(tabla, unidad, prismas, idcomponente):
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente]
        
        # T-SQL: Optimización de FIRST_VALUE y DATEDIFF
        # Nota: La consulta original retorna 'VA3D' como alias, se mantiene para compatibilidad.
        sql = f"""WITH PrismasCTE AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0 AS dias,
                SQRT(
                    POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                ) * ? AS dosD,
                i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
            CASE 
                WHEN DATEDIFF(SECOND, FIRST_VALUE(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) = 0 THEN 0
                ELSE (dosD - FIRST_VALUE(dosD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma))
                    / (CAST(DATEDIFF(SECOND, FIRST_VALUE(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0)
            END AS VA3D, tipo_equipo
        FROM PrismasCTE
        ORDER BY nombre_prisma, hora_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error al consultar va2d: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadFechasVA2D(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""WITH PrismasCTE AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0 AS dias,
                SQRT(
                    POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                ) * ? AS dosD,
                i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ?
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
            CASE 
                WHEN DATEDIFF(SECOND, FIRST_VALUE(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) = 0 THEN 0
                ELSE (dosD - FIRST_VALUE(dosD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma))
                    / (CAST(DATEDIFF(SECOND, FIRST_VALUE(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0)
            END AS VA3D, tipo_equipo
        FROM PrismasCTE
        ORDER BY nombre_prisma, hora_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error al consultar va2d fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadDiasVA2D(tabla, unidad, prismas, idcomponente, cantidad):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, CAST(p.hora_prisma AS DATE) AS fecha, MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.este_target AS FLOAT)) AS promedio_este,
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad} ) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), f.fecha_inicio, i.id_instrumentacion, i.tipo_equipo
        ),
        velocidad AS (
            SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma, b.promedio_este, b.promedio_norte,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0 AS dias,
                SQRT(
                    POWER(b.promedio_este - FIRST_VALUE(b.promedio_este) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2) +
                    POWER(b.promedio_norte - FIRST_VALUE(b.promedio_norte) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2)
                ) * ? AS dosD,
                b.tipo_equipo,
                b.bloque_dias
            FROM bloques b
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
            CASE 
                WHEN DATEDIFF(SECOND, FIRST_VALUE(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) = 0 THEN 0
                ELSE (dosD - FIRST_VALUE(dosD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma))
                    / (CAST(DATEDIFF(SECOND, FIRST_VALUE(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0)
            END AS VA3D, tipo_equipo
        FROM velocidad
        ORDER BY nombre_prisma, hora_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error al consultar prom dias va2d: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadDiasFechasVA2D(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, CAST(p.hora_prisma AS DATE) AS fecha, MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.este_target AS FLOAT)) AS promedio_este,
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad} ) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), f.fecha_inicio, i.id_instrumentacion, i.tipo_equipo
        ),
        velocidad AS (
            SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma, b.promedio_este, b.promedio_norte,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0 AS dias,
                SQRT(
                    POWER(b.promedio_este - FIRST_VALUE(b.promedio_este) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2) +
                    POWER(b.promedio_norte - FIRST_VALUE(b.promedio_norte) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2)
                ) * ? AS dosD,
                b.tipo_equipo,
                b.bloque_dias
            FROM bloques b
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
            CASE 
                WHEN DATEDIFF(SECOND, FIRST_VALUE(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) = 0 THEN 0
                ELSE (dosD - FIRST_VALUE(dosD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma))
                    / (CAST(DATEDIFF(SECOND, FIRST_VALUE(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0)
            END AS VA3D, tipo_equipo
        FROM velocidad
        ORDER BY nombre_prisma, hora_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error al consultar prom dias va2d fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadHorasVA2D(tabla, unidad, prismas, idcomponente, cantidad):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]
        
        sql = f"""WITH promedios_horas AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.este_target AS FLOAT)) AS promedio_este,
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad}, i.id_instrumentacion, i.tipo_equipo
        ),
        velocidad AS (
            SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma, pd.promedio_este, pd.promedio_norte,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0 AS dias,
                SQRT(
                    POWER(pd.promedio_este - FIRST_VALUE(pd.promedio_este) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2) +
                    POWER(pd.promedio_norte - FIRST_VALUE(pd.promedio_norte) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2)
                ) * ? AS dosD,
                pd.tipo_equipo,
                pd.fecha, pd.bloque
            FROM promedios_horas pd
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
            CASE 
                WHEN DATEDIFF(SECOND, FIRST_VALUE(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) = 0 THEN 0
                ELSE (dosD - FIRST_VALUE(dosD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma))
                    / (CAST(DATEDIFF(SECOND, FIRST_VALUE(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0)
            END AS VA3D, tipo_equipo
        FROM velocidad
        ORDER BY nombre_prisma, hora_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error al consultar prom horas va2d: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadHorasFechasVA2D(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        
        sql = f"""WITH promedios_horas AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.este_target AS FLOAT)) AS promedio_este,
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad}, i.id_instrumentacion, i.tipo_equipo
        ),
        velocidad AS (
            SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma, pd.promedio_este, pd.promedio_norte,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0 AS dias,
                SQRT(
                    POWER(pd.promedio_este - FIRST_VALUE(pd.promedio_este) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2) +
                    POWER(pd.promedio_norte - FIRST_VALUE(pd.promedio_norte) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2)
                ) * ? AS dosD,
                pd.tipo_equipo,
                pd.fecha, pd.bloque
            FROM promedios_horas pd
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
            CASE 
                WHEN DATEDIFF(SECOND, FIRST_VALUE(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) = 0 THEN 0
                ELSE (dosD - FIRST_VALUE(dosD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma))
                    / (CAST(DATEDIFF(SECOND, FIRST_VALUE(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0)
            END AS VA3D, tipo_equipo
        FROM velocidad
        ORDER BY nombre_prisma, hora_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error al consultar prom horas va2d fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
                
    @staticmethod
    def mdlCalcularVelocidadPositivaVI3D(tabla, unidad, prismas, idcomponente):
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente]
        # T-SQL: DATEDIFF para dias, lógica LAG para coordenadas
        sql = f"""WITH PrismasCTE AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, p.elevacion_target,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0 AS dias,
                SQRT(
                    POWER(p.este_target - LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.norte_target - LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.elevacion_target - LAG(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                ) * ? AS tresD,
                i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
        CASE 
            WHEN LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) IS NULL THEN 0
            ELSE tresD / (CAST(DATEDIFF(SECOND, LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0)
        END AS VI3D, tipo_equipo
        FROM PrismasCTE
        ORDER BY nombre_prisma, hora_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error al consultar vi3d positiva: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadPositivaFechasVI3D(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""WITH PrismasCTE AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, p.elevacion_target,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0 AS dias,
                SQRT(
                    POWER(p.este_target - LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.norte_target - LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.elevacion_target - LAG(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                ) * ? AS tresD,
                i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ?
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
        CASE 
            WHEN LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) IS NULL THEN 0
            ELSE tresD / (CAST(DATEDIFF(SECOND, LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0)
        END AS VI3D, tipo_equipo
        FROM PrismasCTE
        ORDER BY nombre_prisma, hora_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error al consultar vi3d positiva fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadDiasPositivaVI3D(tabla, unidad, prismas, idcomponente, cantidad):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]
        
        # T-SQL: CAST AS DATE, GROUP BY explícito
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, CAST(p.hora_prisma AS DATE) AS fecha, MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.este_target AS FLOAT)) AS promedio_este,
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                AVG(CAST(p.elevacion_target AS FLOAT)) AS promedio_elevacion,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad} ) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), f.fecha_inicio, i.id_instrumentacion, i.tipo_equipo
        ),
        velocidad AS (
            SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma, b.promedio_este, b.promedio_norte, b.promedio_elevacion,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0 AS dias,
                SQRT(
                    POWER(b.promedio_este - LAG(b.promedio_este) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2) +
                    POWER(b.promedio_norte - LAG(b.promedio_norte) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2) +
                    POWER(b.promedio_elevacion - LAG(b.promedio_elevacion) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2)
                ) * ? AS tresD,
                b.tipo_equipo,
                b.bloque_dias
            FROM bloques b
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
        CASE 
            WHEN LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) IS NULL THEN 0
            ELSE tresD / (CAST(DATEDIFF(SECOND, LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0)
        END AS VI3D, tipo_equipo
        FROM velocidad
        ORDER BY nombre_prisma, bloque_dias;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error al consultar prom dias vi3d positiva: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadDiasPositivaFechasVI3D(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, CAST(p.hora_prisma AS DATE) AS fecha, MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.este_target AS FLOAT)) AS promedio_este,
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                AVG(CAST(p.elevacion_target AS FLOAT)) AS promedio_elevacion,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad} ) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), f.fecha_inicio, i.id_instrumentacion, i.tipo_equipo
        ),
        velocidad AS (
            SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma, b.promedio_este, b.promedio_norte, b.promedio_elevacion,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0 AS dias,
                SQRT(
                    POWER(b.promedio_este - LAG(b.promedio_este) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2) +
                    POWER(b.promedio_norte - LAG(b.promedio_norte) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2) +
                    POWER(b.promedio_elevacion - LAG(b.promedio_elevacion) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2)
                ) * ? AS tresD,
                b.tipo_equipo,
                b.bloque_dias
            FROM bloques b
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
        CASE 
            WHEN LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) IS NULL THEN 0
            ELSE tresD / (CAST(DATEDIFF(SECOND, LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0)
        END AS VI3D, tipo_equipo
        FROM velocidad
        ORDER BY nombre_prisma, bloque_dias;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error al consultar prom dias vi3d positiva fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadHorasPositivaVI3D(tabla, unidad, prismas, idcomponente, cantidad):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]
        
        # T-SQL: DATEPART(HOUR)
        sql = f"""WITH promedios_horas AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.este_target AS FLOAT)) AS promedio_este,
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                AVG(CAST(p.elevacion_target AS FLOAT)) AS promedio_elevacion,
                i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad}, i.id_instrumentacion, i.tipo_equipo
        ),
        velocidad AS (
            SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma, pd.promedio_este, pd.promedio_norte, pd.promedio_elevacion,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0 AS dias,
                SQRT(
                    POWER(pd.promedio_este - LAG(pd.promedio_este) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2) +
                    POWER(pd.promedio_norte - LAG(pd.promedio_norte) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2) +
                    POWER(pd.promedio_elevacion - LAG(pd.promedio_elevacion) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2)
                ) * ? AS tresD,
                pd.tipo_equipo,
                pd.fecha, pd.bloque
            FROM promedios_horas pd
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
        CASE 
            WHEN LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) IS NULL THEN 0
            ELSE tresD / (CAST(DATEDIFF(SECOND, LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0)
        END AS VI3D, tipo_equipo
        FROM velocidad
        ORDER BY nombre_prisma, hora_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error al consultar prom horas vi3d positiva: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadHorasPositivaFechasVI3D(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        
        sql = f"""WITH promedios_horas AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.este_target AS FLOAT)) AS promedio_este,
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                AVG(CAST(p.elevacion_target AS FLOAT)) AS promedio_elevacion,
                i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad}, i.id_instrumentacion, i.tipo_equipo
        ),
        velocidad AS (
            SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma, pd.promedio_este, pd.promedio_norte, pd.promedio_elevacion,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0 AS dias,
                SQRT(
                    POWER(pd.promedio_este - LAG(pd.promedio_este) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2) +
                    POWER(pd.promedio_norte - LAG(pd.promedio_norte) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2) +
                    POWER(pd.promedio_elevacion - LAG(pd.promedio_elevacion) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2)
                ) * ? AS tresD,
                pd.tipo_equipo,
                pd.fecha, pd.bloque
            FROM promedios_horas pd
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
        CASE 
            WHEN LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) IS NULL THEN 0
            ELSE tresD / (CAST(DATEDIFF(SECOND, LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0)
        END AS VI3D, tipo_equipo
        FROM velocidad
        ORDER BY nombre_prisma, hora_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error al consultar prom horas vi3d positiva fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadVI3D(tabla, unidad, prismas, idcomponente):
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente]
        
        # T-SQL: row_number() se mantiene, JULIANDAY logic -> DATEDIFF
        sql = f"""WITH PrismasCTE AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, p.elevacion_target,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0 AS dias,
                CASE
                    WHEN ROW_NUMBER() OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) = 1 THEN 0
                    ELSE 
                        SQRT(
                            POWER(p.este_target - LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                            POWER(p.norte_target - LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                            POWER(p.elevacion_target - LAG(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                        ) * ?
                END AS tresD,
                i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
            CASE
                WHEN ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) = 1 THEN 0
                ELSE (tresD - LAG(tresD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma))
                / (CAST(DATEDIFF(SECOND, LAG(hora_prisma, 1, hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0)
            END AS VI3D, tipo_equipo
        FROM PrismasCTE
        ORDER BY nombre_prisma, hora_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error al consultar vi3d: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadFechasVI3D(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""WITH PrismasCTE AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, p.elevacion_target,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0 AS dias,
                CASE
                    WHEN ROW_NUMBER() OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) = 1 THEN 0
                    ELSE 
                        SQRT(
                            POWER(p.este_target - LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                            POWER(p.norte_target - LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                            POWER(p.elevacion_target - LAG(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                        ) * ?
                END AS tresD,
                i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ?
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
            CASE
                WHEN ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) = 1 THEN 0
                ELSE (tresD - LAG(tresD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma))
                / (CAST(DATEDIFF(SECOND, LAG(hora_prisma, 1, hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0)
            END AS VI3D, tipo_equipo
        FROM PrismasCTE
        ORDER BY nombre_prisma, hora_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error al consultar vi3d fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadDiasVI3D(tabla, unidad, prismas, idcomponente, cantidad):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, CAST(p.hora_prisma AS DATE) AS fecha, MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.este_target AS FLOAT)) AS promedio_este,
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                AVG(CAST(p.elevacion_target AS FLOAT)) AS promedio_elevacion,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad} ) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), f.fecha_inicio, i.id_instrumentacion, i.tipo_equipo
        ),
        velocidad AS (
            SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma, b.promedio_este, b.promedio_norte, b.promedio_elevacion,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0 AS dias,
                CASE
                    WHEN ROW_NUMBER() OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma) = 1 THEN 0
                    ELSE 
                        SQRT(
                            POWER(b.promedio_este - LAG(b.promedio_este) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2) +
                            POWER(b.promedio_norte - LAG(b.promedio_norte) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2) +
                            POWER(b.promedio_elevacion - LAG(b.promedio_elevacion) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2)
                        ) * ?
                END AS tresD, b.tipo_equipo,
                b.bloque_dias
            FROM bloques b
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
            CASE
                WHEN ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) = 1 THEN 0
                ELSE (tresD - LAG(tresD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma))
                / (CAST(DATEDIFF(SECOND, LAG(hora_prisma, 1, hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0)
            END AS VI3D, tipo_equipo
        FROM velocidad
        ORDER BY nombre_prisma, hora_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error al consultar prom dias vi3d: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadDiasFechasVI3D(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, CAST(p.hora_prisma AS DATE) AS fecha, MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.este_target AS FLOAT)) AS promedio_este,
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                AVG(CAST(p.elevacion_target AS FLOAT)) AS promedio_elevacion,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad} ) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), f.fecha_inicio, i.id_instrumentacion, i.tipo_equipo
        ),
        velocidad AS (
            SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma, b.promedio_este, b.promedio_norte, b.promedio_elevacion,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0 AS dias,
                CASE
                    WHEN ROW_NUMBER() OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma) = 1 THEN 0
                    ELSE 
                        SQRT(
                            POWER(b.promedio_este - LAG(b.promedio_este) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2) +
                            POWER(b.promedio_norte - LAG(b.promedio_norte) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2) +
                            POWER(b.promedio_elevacion - LAG(b.promedio_elevacion) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2)
                        ) * ?
                END AS tresD,
                b.tipo_equipo,
                b.bloque_dias
            FROM bloques b
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
            CASE
                WHEN ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) = 1 THEN 0
                ELSE (tresD - LAG(tresD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma))
                / (CAST(DATEDIFF(SECOND, LAG(hora_prisma, 1, hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0)
            END AS VI3D, tipo_equipo
        FROM velocidad
        ORDER BY nombre_prisma, hora_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error al consultar prom dias vi3d fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadHorasVI3D(tabla, unidad, prismas, idcomponente, cantidad):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]
        
        sql = f"""WITH promedios_horas AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.este_target AS FLOAT)) AS promedio_este,
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                AVG(CAST(p.elevacion_target AS FLOAT)) AS promedio_elevacion,
                i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad}, i.id_instrumentacion, i.tipo_equipo
        ),
        velocidad AS (
            SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma, pd.promedio_este, pd.promedio_norte, pd.promedio_elevacion,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0 AS dias,
                CASE
                    WHEN ROW_NUMBER() OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma) = 1 THEN 0
                    ELSE 
                        SQRT(
                            POWER(pd.promedio_este - LAG(pd.promedio_este) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2) +
                            POWER(pd.promedio_norte - LAG(pd.promedio_norte) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2) +
                            POWER(pd.promedio_elevacion - LAG(pd.promedio_elevacion) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2)
                        ) * ?
                END AS tresD,
                pd.tipo_equipo,
                pd.fecha, pd.bloque
            FROM promedios_horas pd
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
            CASE
                WHEN ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) = 1 THEN 0
                ELSE (tresD - LAG(tresD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma))
                / (CAST(DATEDIFF(SECOND, LAG(hora_prisma, 1, hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0)
            END AS VI3D, tipo_equipo
        FROM velocidad
        ORDER BY nombre_prisma, hora_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error al consultar prom horas vi3d: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadHorasFechasVI3D(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        
        sql = f"""WITH promedios_horas AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.este_target AS FLOAT)) AS promedio_este,
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                AVG(CAST(p.elevacion_target AS FLOAT)) AS promedio_elevacion,
                i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad}, i.id_instrumentacion, i.tipo_equipo
        ),
        velocidad AS (
            SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma, pd.promedio_este, pd.promedio_norte, pd.promedio_elevacion,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0 AS dias,
                CASE
                    WHEN ROW_NUMBER() OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma) = 1 THEN 0
                    ELSE 
                        SQRT(
                            POWER(pd.promedio_este - LAG(pd.promedio_este) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2) +
                            POWER(pd.promedio_norte - LAG(pd.promedio_norte) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2) +
                            POWER(pd.promedio_elevacion - LAG(pd.promedio_elevacion) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2)
                        ) * ?
                END AS tresD,
                pd.tipo_equipo,
                pd.fecha, pd.bloque
            FROM promedios_horas pd
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
            CASE
                WHEN ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) = 1 THEN 0
                ELSE (tresD - LAG(tresD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma))
                / (CAST(DATEDIFF(SECOND, LAG(hora_prisma, 1, hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0)
            END AS VI3D, tipo_equipo
        FROM velocidad
        ORDER BY nombre_prisma, hora_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error al consultar prom horas vi3d fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadVA3D(tabla, unidad, prismas, idcomponente):
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente]
        
        sql = f"""WITH PrismasCTE AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, p.elevacion_target,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0 AS dias,
                SQRT(
                    POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.elevacion_target - FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                ) * ? AS tresD,
                i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
            CASE 
                WHEN DATEDIFF(SECOND, FIRST_VALUE(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) = 0 THEN 0
                ELSE (tresD - FIRST_VALUE(tresD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma))
                    / (CAST(DATEDIFF(SECOND, FIRST_VALUE(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0)
            END AS VA3D, tipo_equipo
        FROM PrismasCTE
        ORDER BY nombre_prisma, hora_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error al consultar va3d: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadFechasVA3D(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""WITH PrismasCTE AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, p.elevacion_target,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0 AS dias,
                SQRT(
                    POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.elevacion_target - FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                ) * ? AS tresD,
                i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ?
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
            CASE 
                WHEN DATEDIFF(SECOND, FIRST_VALUE(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) = 0 THEN 0
                ELSE (tresD - FIRST_VALUE(tresD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma))
                    / (CAST(DATEDIFF(SECOND, FIRST_VALUE(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0)
            END AS VA3D, tipo_equipo
        FROM PrismasCTE
        ORDER BY nombre_prisma, hora_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error al consultar va3d fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadDiasVA3D(tabla, unidad, prismas, idcomponente, cantidad):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, CAST(p.hora_prisma AS DATE) AS fecha, MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.este_target AS FLOAT)) AS promedio_este,
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                AVG(CAST(p.elevacion_target AS FLOAT)) AS promedio_elevacion,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad} ) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), f.fecha_inicio, i.id_instrumentacion, i.tipo_equipo
        ),
        velocidad AS (
            SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma, b.promedio_este, b.promedio_norte, b.promedio_elevacion,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0 AS dias,
                SQRT(
                    POWER(b.promedio_este - FIRST_VALUE(b.promedio_este) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2) +
                    POWER(b.promedio_norte - FIRST_VALUE(b.promedio_norte) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2) +
                    POWER(b.promedio_elevacion - FIRST_VALUE(b.promedio_elevacion) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2)
                ) * ? AS tresD,
                b.tipo_equipo,
                b.bloque_dias
            FROM bloques b
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
            CASE 
                WHEN DATEDIFF(SECOND, FIRST_VALUE(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) = 0 THEN 0
                ELSE (tresD - FIRST_VALUE(tresD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma))
                    / (CAST(DATEDIFF(SECOND, FIRST_VALUE(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0)
            END AS VA3D, tipo_equipo
        FROM velocidad
        ORDER BY nombre_prisma, hora_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error al consultar prom dias va3d: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadDiasFechasVA3D(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, CAST(p.hora_prisma AS DATE) AS fecha, MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.este_target AS FLOAT)) AS promedio_este,
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                AVG(CAST(p.elevacion_target AS FLOAT)) AS promedio_elevacion,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad} ) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), f.fecha_inicio, i.id_instrumentacion, i.tipo_equipo
        ),
        velocidad AS (
            SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma, b.promedio_este, b.promedio_norte, b.promedio_elevacion,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0 AS dias,
                SQRT(
                    POWER(b.promedio_este - FIRST_VALUE(b.promedio_este) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2) +
                    POWER(b.promedio_norte - FIRST_VALUE(b.promedio_norte) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2) +
                    POWER(b.promedio_elevacion - FIRST_VALUE(b.promedio_elevacion) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2)
                ) * ? AS tresD,
                b.tipo_equipo,
                b.bloque_dias
            FROM bloques b
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
            CASE 
                WHEN DATEDIFF(SECOND, FIRST_VALUE(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) = 0 THEN 0
                ELSE (tresD - FIRST_VALUE(tresD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma))
                    / (CAST(DATEDIFF(SECOND, FIRST_VALUE(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0)
            END AS VA3D, tipo_equipo
        FROM velocidad
        ORDER BY nombre_prisma, hora_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error al consultar prom dias va3d fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadHorasVA3D(tabla, unidad, prismas, idcomponente, cantidad):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]
        
        sql = f"""WITH promedios_horas AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.este_target AS FLOAT)) AS promedio_este,
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                AVG(CAST(p.elevacion_target AS FLOAT)) AS promedio_elevacion,
                i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad}, i.id_instrumentacion, i.tipo_equipo
        ),
        velocidad AS (
            SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma, pd.promedio_este, pd.promedio_norte, pd.promedio_elevacion,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0 AS dias,
                SQRT(
                    POWER(pd.promedio_este - FIRST_VALUE(pd.promedio_este) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2) +
                    POWER(pd.promedio_norte - FIRST_VALUE(pd.promedio_norte) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2) +
                    POWER(pd.promedio_elevacion - FIRST_VALUE(pd.promedio_elevacion) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2)
                ) * ? AS tresD,
                pd.tipo_equipo,
                pd.fecha, pd.bloque
            FROM promedios_horas pd
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
            CASE 
                WHEN DATEDIFF(SECOND, FIRST_VALUE(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) = 0 THEN 0
                ELSE (tresD - FIRST_VALUE(tresD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma))
                    / (CAST(DATEDIFF(SECOND, FIRST_VALUE(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0)
            END AS VA3D, tipo_equipo
        FROM velocidad
        ORDER BY nombre_prisma, hora_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error al consultar prom horas va3d: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVelocidadHorasFechasVA3D(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        
        sql = f"""WITH promedios_horas AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.este_target AS FLOAT)) AS promedio_este,
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                AVG(CAST(p.elevacion_target AS FLOAT)) AS promedio_elevacion,
                i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad}, i.id_instrumentacion, i.tipo_equipo
        ),
        velocidad AS (
            SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma, pd.promedio_este, pd.promedio_norte, pd.promedio_elevacion,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0 AS dias,
                SQRT(
                    POWER(pd.promedio_este - FIRST_VALUE(pd.promedio_este) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2) +
                    POWER(pd.promedio_norte - FIRST_VALUE(pd.promedio_norte) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2) +
                    POWER(pd.promedio_elevacion - FIRST_VALUE(pd.promedio_elevacion) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2)
                ) * ? AS tresD,
                pd.tipo_equipo,
                pd.fecha, pd.bloque
            FROM promedios_horas pd
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
            CASE 
                WHEN DATEDIFF(SECOND, FIRST_VALUE(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) = 0 THEN 0
                ELSE (tresD - FIRST_VALUE(tresD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma))
                    / (CAST(DATEDIFF(SECOND, FIRST_VALUE(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0)
            END AS VA3D, tipo_equipo
        FROM velocidad
        ORDER BY nombre_prisma, hora_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error al consultar prom horas va3d fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()