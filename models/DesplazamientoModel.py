from services.security.apis.conexiones.connection import Connection
from pyodbc import Error

class DesplazamientoModel:
    
    @staticmethod
    def mdlObtenerPrismasMarcados(componente, tablaauto, prismas):
        conn = None
        try:
            conn = Connection.connectionDB()
            # SQL Server usa ? igual que SQLite para ODBC
            # Nota: tabla_equipo en la query original parece ser un parámetro de filtro, no el nombre de la tabla dinámica.
            placeholders = ', '.join(['?' for _ in prismas])
            sql = f"""SELECT i.nombre_equipo 
                      FROM instrumentacion i 
                      INNER JOIN componentes c ON i.id_componente = c.id_componente
                      WHERE c.nombre_componente = ? AND tabla_equipo = ? 
                      AND i.nombre_equipo IN ({placeholders});"""
            
            cur = conn.cursor()
            # Parametros posicionales exactos
            params = [componente, tablaauto] + prismas
            cur.execute(sql, params)
            
            # Fidelidad de Output: Convertir pyodbc.Row a tuple para imitar SQLite
            results = [tuple(row) for row in cur.fetchall()]
            
            if results:
                return results
            else:
                return None
        except Error as e:
            print("Error al obtener prismas marcados:", e)
            return None  
        finally:
            if conn:
                conn.close()
                
    @staticmethod
    def mdlCalcularDesplazamientoSDA(tabla, unidad, prismas, idcomponente):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente]
        
        # Traducción SQL: 
        # 1. JULIANDAY diff -> DATEDIFF(SECOND, ...) / 86400.0 para obtener fracción de días precisa.
        # 2. AS NUMERIC -> AS FLOAT para asegurar retorno float en Python y no Decimal().
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (p.distancia_prisma - FIRST_VALUE(CAST(p.distancia_prisma AS FLOAT)) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma)) * ? AS SD,
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            
            # Fidelidad de Output: Convertir Row a tuple
            rows = [tuple(row) for row in cur.fetchall()]
            
            if rows:
                return rows
            else:
                return None
        except Error as e:
            print("Error al consultar DA SD: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoFechasSDA(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (p.distancia_prisma - FIRST_VALUE(CAST(p.distancia_prisma AS FLOAT)) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma)) * ? AS SD,
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        AND p.hora_prisma BETWEEN ? AND ? 
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            
            rows = [tuple(row) for row in cur.fetchall()]
            
            if rows:
                return rows
            else:
                return None
        except Error as e:
            print("Error al consultar DA SD fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasSDA(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]
        
        # Traducción SQL:
        # DATE() -> CAST(... AS DATE)
        # Diferencia de fechas en bloques -> DATEDIFF con lógica de segundos para precisión y división posterior.
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, CAST(p.hora_prisma AS DATE) AS fecha, MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.distancia_prisma AS FLOAT)) AS promedio_distancia,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
            i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (b.promedio_distancia - FIRST_VALUE(b.promedio_distancia) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma)) * ? AS SD,
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        # Nota: En SQL Server, todas las columnas no agregadas en el SELECT deben estar en el GROUP BY. 
        # He ajustado el GROUP BY de la CTE 'bloques' para cumplir con el estándar T-SQL.
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            
            rows = [tuple(row) for row in cur.fetchall()]
            
            if rows:
                return rows
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DA SD: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasFechasSDA(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
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
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (b.promedio_distancia - FIRST_VALUE(b.promedio_distancia) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma)) * ? AS SD,
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            
            rows = [tuple(row) for row in cur.fetchall()]
            
            if rows:
                return rows
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DA SD fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHorasSDA(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]
        
        # Traducción SQL:
        # STRFTIME('%H', ...) -> DATEPART(HOUR, ...)
        
        sql = f"""WITH promedios_horas AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque,
                MAX(p.hora_prisma) AS hora_prisma, AVG(CAST(p.distancia_prisma AS FLOAT)) AS promedio_distancia,
                i.tipo_equipo   
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (pd.promedio_distancia - FIRST_VALUE(pd.promedio_distancia) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.fecha, pd.bloque)) * ? AS SD,
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            
            rows = [tuple(row) for row in cur.fetchall()]
            
            if rows:
                return rows
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DA SD: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHorasFechasSDA(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
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
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (pd.promedio_distancia - FIRST_VALUE(pd.promedio_distancia) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.fecha, pd.bloque)) * ? AS SD,
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            
            rows = [tuple(row) for row in cur.fetchall()]
            
            if rows:
                return rows
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DA SD fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoSDI(tabla, unidad, prismas, idcomponente):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente]
        
        # Traducción T-SQL:
        # 1. JULIANDAY logic -> DATEDIFF(SECOND, ...) / 86400.0
        # 2. LAG: Funciona igual en T-SQL, pero convertimos el resultado final a FLOAT para evitar Decimal() en Python.
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(p.distancia_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                ELSE (p.distancia_prisma - LAG(p.distancia_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * ?
            END AS FLOAT) AS SD,
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            # Fidelidad: Convertir Row a tuple
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DI SD: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoFechasSDI(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(p.distancia_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                ELSE (p.distancia_prisma - LAG(p.distancia_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * ?
            END AS FLOAT) AS SD,
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        AND p.hora_prisma BETWEEN ? AND ? 
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DI SD fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasSDI(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        # Nota: 'unidad' es el último parámetro en la query SQL (multiplicador del SD)
        params = prismas + [idcomponente] + [unidad]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.distancia_prisma AS FLOAT)) AS promedio_distancia,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            -- SQL Server requiere que todas las columnas no agregadas estén en el GROUP BY
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(b.promedio_distancia) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma) IS NULL THEN 0
                ELSE (b.promedio_distancia - LAG(b.promedio_distancia) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma)) * ?
            END AS FLOAT) AS SD,
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DI SD: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasFechasSDI(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.distancia_prisma AS FLOAT)) AS promedio_distancia,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(b.promedio_distancia) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma) IS NULL THEN 0
                ELSE (b.promedio_distancia - LAG(b.promedio_distancia) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma)) * ?
            END AS FLOAT) AS SD,
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DI SD fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHorasSDI(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]
        
        # Corrección de sintaxis original: Se eliminó la coma flotante y se corrigió el JOIN
        # STRFTIME('%H', ...) -> DATEPART(HOUR, ...)
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque,
                MAX(p.hora_prisma) AS hora_prisma, 
                AVG(CAST(p.distancia_prisma AS FLOAT)) AS promedio_distancia,
                i.tipo_equipo 
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(pd.promedio_distancia) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.fecha, pd.bloque) IS NULL THEN 0
                ELSE (pd.promedio_distancia - LAG(pd.promedio_distancia) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.fecha, pd.bloque)) * ?
            END AS FLOAT) AS SD,
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DI SD: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHorasFechasSDI(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque,
                MAX(p.hora_prisma) AS hora_prisma, 
                AVG(CAST(p.distancia_prisma AS FLOAT)) AS promedio_distancia,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(pd.promedio_distancia) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.fecha, pd.bloque) IS NULL THEN 0
                ELSE (pd.promedio_distancia - LAG(pd.promedio_distancia) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.fecha, pd.bloque)) * ?
            END AS FLOAT) AS SD,
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DI SD fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamiento3DA(tabla, unidad, prismas, idcomponente):
        print(prismas)
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente]
        
        # Traducción:
        # JULIANDAY -> DATEDIFF en segundos / 86400.0 (para fracción de días)
        # 3D: Raíz cuadrada de la suma de los cuadrados de las diferencias respecto al valor inicial (FIRST_VALUE).
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (SQRT(
                POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2) +
                POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2) +
                POWER(p.elevacion_target - FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2)
            )) * ? AS tresD,
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DA 3D: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoFechas3DA(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        print(prismas)
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (SQRT(
                POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2) +
                POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2) +
                POWER(p.elevacion_target - FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2)
            )) * ? AS tresD,
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        AND p.hora_prisma BETWEEN ? AND ? 
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DA 3D fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDias3DA(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.este_target AS FLOAT)) AS promedio_este,
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                AVG(CAST(p.elevacion_target AS FLOAT)) AS promedio_elevacion,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE),
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (SQRT(
                POWER(b.promedio_este - FIRST_VALUE(b.promedio_este) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), 2) +
                POWER(b.promedio_norte - FIRST_VALUE(b.promedio_norte) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), 2) +
                POWER(b.promedio_elevacion - FIRST_VALUE(b.promedio_elevacion) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), 2)
            )) * ? AS tresD,
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DA 3D: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasFechas3DA(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.este_target AS FLOAT)) AS promedio_este,
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                AVG(CAST(p.elevacion_target AS FLOAT)) AS promedio_elevacion,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE),
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (SQRT(
                POWER(b.promedio_este - FIRST_VALUE(b.promedio_este) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), 2) +
                POWER(b.promedio_norte - FIRST_VALUE(b.promedio_norte) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), 2) +
                POWER(b.promedio_elevacion - FIRST_VALUE(b.promedio_elevacion) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), 2)
            )) * ? AS tresD,
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DA 3D fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHoras3DA(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.este_target AS FLOAT)) AS promedio_este,
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                AVG(CAST(p.elevacion_target AS FLOAT)) AS promedio_elevacion,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (SQRT(
                POWER(pd.promedio_este - FIRST_VALUE(pd.promedio_este) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), 2) +
                POWER(pd.promedio_norte - FIRST_VALUE(pd.promedio_norte) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), 2) +
                POWER(pd.promedio_elevacion - FIRST_VALUE(pd.promedio_elevacion) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), 2)
            )) * ? AS tresD,
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DA 3D: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHorasFechas3DA(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.este_target AS FLOAT)) AS promedio_este,
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                AVG(CAST(p.elevacion_target AS FLOAT)) AS promedio_elevacion,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (SQRT(
                POWER(pd.promedio_este - FIRST_VALUE(pd.promedio_este) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), 2) +
                POWER(pd.promedio_norte - FIRST_VALUE(pd.promedio_norte) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), 2) +
                POWER(pd.promedio_elevacion - FIRST_VALUE(pd.promedio_elevacion) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), 2)
            )) * ? AS tresD,
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DA 3D fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
                
    @staticmethod
    def mdlCalcularDesplazamiento3DI(tabla, unidad, prismas, idcomponente):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente]
        
        # Traducción:
        # 1. Tiempos: DATEDIFF(SECOND, ...) / 86400.0
        # 2. 3D Incremental: Raíz de la suma de diferencias al cuadrado comparando con el registro anterior (LAG).
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                ELSE (SQRT(
                    POWER(p.este_target - LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.norte_target - LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.elevacion_target - LAG(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                )) * ?
            END AS FLOAT) AS tresD,
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DI 3D: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoFechas3DI(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                ELSE (SQRT(
                    POWER(p.este_target - LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.norte_target - LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.elevacion_target - LAG(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                )) * ?
            END AS FLOAT) AS tresD,
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        AND p.hora_prisma BETWEEN ? AND ? 
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DI 3D fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDias3DI(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.este_target AS FLOAT)) AS promedio_este,
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                AVG(CAST(p.elevacion_target AS FLOAT)) AS promedio_elevacion,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(b.promedio_este) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma) IS NULL THEN 0
                ELSE (SQRT(
                    POWER(b.promedio_este - LAG(b.promedio_este) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2) +
                    POWER(b.promedio_norte - LAG(b.promedio_norte) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2) +
                    POWER(b.promedio_elevacion - LAG(b.promedio_elevacion) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2)
                )) * ?
            END AS FLOAT) AS tresD,
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DI 3D: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasFechas3DI(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.este_target AS FLOAT)) AS promedio_este,
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                AVG(CAST(p.elevacion_target AS FLOAT)) AS promedio_elevacion,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(b.promedio_este) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma) IS NULL THEN 0
                ELSE (SQRT(
                    POWER(b.promedio_este - LAG(b.promedio_este) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2) +
                    POWER(b.promedio_norte - LAG(b.promedio_norte) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2) +
                    POWER(b.promedio_elevacion - LAG(b.promedio_elevacion) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2)
                )) * ?
            END AS FLOAT) AS tresD,
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DI 3D fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHoras3DI(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.este_target AS FLOAT)) AS promedio_este,
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                AVG(CAST(p.elevacion_target AS FLOAT)) AS promedio_elevacion,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(pd.promedio_este) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma) IS NULL THEN 0
                ELSE (SQRT(
                    POWER(pd.promedio_este - LAG(pd.promedio_este) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2) +
                    POWER(pd.promedio_norte - LAG(pd.promedio_norte) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2) +
                    POWER(pd.promedio_elevacion - LAG(pd.promedio_elevacion) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2)
                )) * ?
            END AS FLOAT) AS tresD,
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DI 3D: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHorasFechas3DI(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.este_target AS FLOAT)) AS promedio_este,
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                AVG(CAST(p.elevacion_target AS FLOAT)) AS promedio_elevacion,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(pd.promedio_este) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma) IS NULL THEN 0
                ELSE (SQRT(
                    POWER(pd.promedio_este - LAG(pd.promedio_este) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2) +
                    POWER(pd.promedio_norte - LAG(pd.promedio_norte) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2) +
                    POWER(pd.promedio_elevacion - LAG(pd.promedio_elevacion) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2)
                )) * ?
            END AS FLOAT) AS tresD,
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DI 3D fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    @staticmethod
    def mdlCalcularDesplazamiento2DA(tabla, unidad, prismas, idcomponente):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente]
        
        # Traducción SQL Server:
        # JULIANDAY diff -> DATEDIFF en segundos / 86400.0
        # 2D -> Solo Este y Norte (Pitágoras)
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (SQRT(
                POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2) +
                POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2)
            )) * ? AS dosD,
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DA 2D: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoFechas2DA(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (SQRT(
                POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2) +
                POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2)
            )) * ? AS dosD,
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        AND p.hora_prisma BETWEEN ? AND ? 
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DA 2D fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDias2DA(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.este_target AS FLOAT)) AS promedio_este,
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (SQRT(
                POWER(b.promedio_este - FIRST_VALUE(b.promedio_este) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), 2) +
                POWER(b.promedio_norte - FIRST_VALUE(b.promedio_norte) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), 2)
            )) * ? AS dosD,
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DA 2D: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasFechas2DA(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.este_target AS FLOAT)) AS promedio_este,
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (SQRT(
                POWER(b.promedio_este - FIRST_VALUE(b.promedio_este) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), 2) +
                POWER(b.promedio_norte - FIRST_VALUE(b.promedio_norte) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), 2)
            )) * ? AS dosD,
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DA 2D fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHoras2DA(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.este_target AS FLOAT)) AS promedio_este,
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (SQRT(
                POWER(pd.promedio_este - FIRST_VALUE(pd.promedio_este) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), 2) +
                POWER(pd.promedio_norte - FIRST_VALUE(pd.promedio_norte) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), 2)
            )) * ? AS dosD,
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DA 2D: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHorasFechas2DA(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.este_target AS FLOAT)) AS promedio_este,
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (SQRT(
                POWER(pd.promedio_este - FIRST_VALUE(pd.promedio_este) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), 2) +
                POWER(pd.promedio_norte - FIRST_VALUE(pd.promedio_norte) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), 2)
            )) * ? AS dosD,
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DA 2D fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamiento2DI(tabla, unidad, prismas, idcomponente):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente]
        
        # Traducción SQL Server:
        # 1. Tiempos: DATEDIFF / 86400.0
        # 2. 2D Incremental: Pitágoras (Este/Norte) comparando con el registro anterior (LAG).
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                ELSE (SQRT(
                    POWER(p.este_target - LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.norte_target - LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                )) * ?
            END AS FLOAT) AS dosD,
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DI 2D: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoFechas2DI(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                ELSE (SQRT(
                    POWER(p.este_target - LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.norte_target - LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                )) * ?
            END AS FLOAT) AS dosD,
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        AND p.hora_prisma BETWEEN ? AND ? 
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DI 2D fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDias2DI(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.este_target AS FLOAT)) AS promedio_este,
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(b.promedio_este) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma) IS NULL THEN 0
                ELSE (SQRT(
                    POWER(b.promedio_este - LAG(b.promedio_este) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2) +
                    POWER(b.promedio_norte - LAG(b.promedio_norte) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2)
                )) * ?
            END AS FLOAT) AS dosD,
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DI 2D: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasFechas2DI(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.este_target AS FLOAT)) AS promedio_este,
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(b.promedio_este) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma) IS NULL THEN 0
                ELSE (SQRT(
                    POWER(b.promedio_este - LAG(b.promedio_este) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2) +
                    POWER(b.promedio_norte - LAG(b.promedio_norte) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2)
                )) * ?
            END AS FLOAT) AS dosD,
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DI 2D fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHoras2DI(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.este_target AS FLOAT)) AS promedio_este,
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(pd.promedio_este) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma) IS NULL THEN 0
                ELSE (SQRT(
                    POWER(pd.promedio_este - LAG(pd.promedio_este) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2) +
                    POWER(pd.promedio_norte - LAG(pd.promedio_norte) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2)
                )) * ?
            END AS FLOAT) AS dosD,
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DI 2D: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHorasFechas2DI(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.este_target AS FLOAT)) AS promedio_este,
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(pd.promedio_este) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma) IS NULL THEN 0
                ELSE (SQRT(
                    POWER(pd.promedio_este - LAG(pd.promedio_este) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2) +
                    POWER(pd.promedio_norte - LAG(pd.promedio_norte) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2)
                )) * ?
            END AS FLOAT) AS dosD,
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DI 2D fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDLA(tabla, unidad, prismas, idcomponente):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente]
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(p.desplaza_longitudinal AS FLOAT) * ? AS desplaza_longitudinal,
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DA L: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
                
    @staticmethod
    def mdlCalcularDesplazamientoFechasDLA(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(p.desplaza_longitudinal AS FLOAT) * ? AS desplaza_longitudinal,
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        AND p.hora_prisma BETWEEN ? AND ? 
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DA L fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasDLA(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.desplaza_longitudinal AS FLOAT)) AS promedio_longitudinal,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            b.promedio_longitudinal * ? AS promedio_longitudinal,
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DA L: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasFechasDLA(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.desplaza_longitudinal AS FLOAT)) AS promedio_longitudinal,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            b.promedio_longitudinal * ? AS promedio_longitudinal,
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DA L fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHorasDLA(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.desplaza_longitudinal AS FLOAT)) AS promedio_longitudinal,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            pd.promedio_longitudinal * ? AS promedio_longitudinal,
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DA L: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHorasFechasDLA(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.desplaza_longitudinal AS FLOAT)) AS promedio_longitudinal,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            pd.promedio_longitudinal * ? AS promedio_longitudinal,
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DA L fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDLI(tabla, unidad, prismas, idcomponente):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente]
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(p.desplaza_longitudinal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                ELSE (p.desplaza_longitudinal - LAG(p.desplaza_longitudinal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * ?
            END AS FLOAT) AS desplaza_longitudinal,
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DI L: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoFechasDLI(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(p.desplaza_longitudinal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                ELSE (p.desplaza_longitudinal - LAG(p.desplaza_longitudinal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * ?
            END AS FLOAT) AS desplaza_longitudinal,
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        AND p.hora_prisma BETWEEN ? AND ? 
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DI L fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasDLI(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.desplaza_longitudinal AS FLOAT)) AS promedio_longitudinal,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(b.promedio_longitudinal) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma) IS NULL THEN 0
                ELSE (b.promedio_longitudinal - LAG(b.promedio_longitudinal) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma)) * ?
            END AS FLOAT) AS promedio_longitudinal,
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DI L: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasFechasDLI(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.desplaza_longitudinal AS FLOAT)) AS promedio_longitudinal,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(b.promedio_longitudinal) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma) IS NULL THEN 0
                ELSE (b.promedio_longitudinal - LAG(b.promedio_longitudinal) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma)) * ?
            END AS FLOAT) AS promedio_longitudinal,
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DI L fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHorasDLI(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.desplaza_longitudinal AS FLOAT)) AS promedio_longitudinal,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(pd.promedio_longitudinal) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma) IS NULL THEN 0
                ELSE (pd.promedio_longitudinal - LAG(pd.promedio_longitudinal) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma)) * ?
            END AS FLOAT) AS promedio_longitudinal,
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DI L: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHorasFechasDLI(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.desplaza_longitudinal AS FLOAT)) AS promedio_longitudinal,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(pd.promedio_longitudinal) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma) IS NULL THEN 0
                ELSE (pd.promedio_longitudinal - LAG(pd.promedio_longitudinal) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma)) * ?
            END AS FLOAT) AS promedio_longitudinal,
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DI L fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDTA(tabla, unidad, prismas, idcomponente):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente]
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(p.desplaza_transversal AS FLOAT) * ?  AS desplaza_transversal,
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DA T: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoFechasDTA(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(p.desplaza_transversal AS FLOAT) * ?  AS desplaza_transversal,
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        AND p.hora_prisma BETWEEN ? AND ? 
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DA T fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasDTA(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.desplaza_transversal AS FLOAT)) AS promedio_transversal,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            b.promedio_transversal * ?  AS promedio_transversal,
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DA T: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasFechasDTA(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.desplaza_transversal AS FLOAT)) AS promedio_transversal,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            b.promedio_transversal * ?  AS promedio_transversal,
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DA T fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHorasDTA(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.desplaza_transversal AS FLOAT)) AS promedio_transversal,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            pd.promedio_transversal * ? AS promedio_transversal,
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DA T: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHorasFechasDTA(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.desplaza_transversal AS FLOAT)) AS promedio_transversal,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            pd.promedio_transversal * ? AS promedio_transversal,
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DA T fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDTI(tabla, unidad, prismas, idcomponente):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente]
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(p.desplaza_transversal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                ELSE (p.desplaza_transversal - LAG(p.desplaza_transversal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * ?
            END AS FLOAT) AS desplaza_transversal,
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DI T: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoFechasDTI(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(p.desplaza_transversal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                ELSE (p.desplaza_transversal - LAG(p.desplaza_transversal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * ?
            END AS FLOAT) AS desplaza_transversal,
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        AND p.hora_prisma BETWEEN ? AND ? 
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DI T fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasDTI(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.desplaza_transversal AS FLOAT)) AS promedio_transversal,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(b.promedio_transversal) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma) IS NULL THEN 0
                ELSE (b.promedio_transversal - LAG(b.promedio_transversal) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma)) * ?
            END AS FLOAT) AS promedio_transversal,
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DI T: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasFechasDTI(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.desplaza_transversal AS FLOAT)) AS promedio_transversal,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(b.promedio_transversal) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma) IS NULL THEN 0
                ELSE (b.promedio_transversal - LAG(b.promedio_transversal) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma)) * ?
            END AS FLOAT) AS promedio_transversal,
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DI T fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDHA(tabla, unidad, prismas, idcomponente):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente]        
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(p.desplaza_altura AS FLOAT) * ? AS desplaza_altura,
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DA H: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoFechasDHA(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente] + [fechaini] + [fechafin]        
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(p.desplaza_altura AS FLOAT) * ? AS desplaza_altura,
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        AND p.hora_prisma BETWEEN ? AND ? 
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DA H fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasDHA(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.desplaza_altura AS FLOAT)) AS promedio_altura,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            b.promedio_altura * ? AS promedio_altura,
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DA H: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasFechasDHA(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]        
        
        # Corrección: El código original tenía un error de sintaxis en el FROM ("i.tipo_equipo" flotando).
        # Se ha corregido y se ha añadido al GROUP BY como requiere SQL Server.
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.desplaza_altura AS FLOAT)) AS promedio_altura,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            b.promedio_altura * ? AS promedio_altura,
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DA H fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHorasDHA(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]        
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma, 
                AVG(CAST(p.desplaza_altura AS FLOAT)) AS promedio_altura,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            pd.promedio_altura * ? AS promedio_altura,
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DA H: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHorasFechasDHA(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]        
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma, 
                AVG(CAST(p.desplaza_altura AS FLOAT)) AS promedio_altura,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            pd.promedio_altura * ? AS promedio_altura,
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DA H fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDHI(tabla, unidad, prismas, idcomponente):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente]        
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(p.desplaza_altura) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                ELSE (p.desplaza_altura - LAG(p.desplaza_altura) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * ?
            END AS FLOAT) AS desplaza_altura,
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DI H: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoFechasDHI(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente] + [fechaini] + [fechafin]        
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(p.desplaza_altura) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                ELSE (p.desplaza_altura - LAG(p.desplaza_altura) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * ?
            END AS FLOAT) AS desplaza_altura,
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        AND p.hora_prisma BETWEEN ? AND ? 
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DI H fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasDHI(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]        
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.desplaza_altura AS FLOAT)) AS promedio_altura,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(b.promedio_altura) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma) IS NULL THEN 0
                ELSE (b.promedio_altura - LAG(b.promedio_altura) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma)) * ?
            END AS FLOAT) AS promedio_altura,
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DI H: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasFechasDHI(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]        
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.desplaza_altura AS FLOAT)) AS promedio_altura,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(b.promedio_altura) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma) IS NULL THEN 0
                ELSE (b.promedio_altura - LAG(b.promedio_altura) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma)) * ?
            END AS FLOAT) AS promedio_altura,
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DI H fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHorasDHI(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]        
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma, 
                AVG(CAST(p.desplaza_altura AS FLOAT)) AS promedio_altura,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(pd.promedio_altura) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma) IS NULL THEN 0
                ELSE (pd.promedio_altura - LAG(pd.promedio_altura) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma)) * ?
            END AS FLOAT) AS promedio_altura,
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        # Nota: Corregí el alias final de 'b.tipo_equipo' a 'pd.tipo_equipo' que estaba incorrecto en el original
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DI H: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHorasFechasDHI(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]        
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma, 
                AVG(CAST(p.desplaza_altura AS FLOAT)) AS promedio_altura,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(pd.promedio_altura) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma) IS NULL THEN 0
                ELSE (pd.promedio_altura - LAG(pd.promedio_altura) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma)) * ?
            END AS FLOAT) AS promedio_altura,
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DI H fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDNA(tabla, unidad, prismas, idcomponente):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente]
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma)) * ? AS distancia,
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DA N: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoFechasDNA(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma)) * ? AS distancia,
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        AND p.hora_prisma BETWEEN ? AND ? 
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DA N fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasDNA(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (b.promedio_norte - FIRST_VALUE(b.promedio_norte) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma)) * ? AS distancia,
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DA N: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasFechasDNA(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (b.promedio_norte - FIRST_VALUE(b.promedio_norte) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma)) * ? AS distancia,
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DA N fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHorasDNA(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma, 
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (pd.promedio_norte - FIRST_VALUE(pd.promedio_norte) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma)) * ? AS distancia,
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DA N: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHorasFechasDNA(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma, 
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (pd.promedio_norte - FIRST_VALUE(pd.promedio_norte) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma)) * ? AS distancia,
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DA N fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDNI(tabla, unidad, prismas, idcomponente):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente]
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                ELSE (p.norte_target - LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * ?
            END AS FLOAT) AS distancia,
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DI N: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    @staticmethod
    def mdlCalcularDesplazamientoHorasDNI(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma, 
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(pd.promedio_norte) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma) IS NULL THEN 0
                ELSE (pd.promedio_norte - LAG(pd.promedio_norte) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma)) * ?
            END AS FLOAT) AS distancia,
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DI N: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHorasFechasDNI(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma, 
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(pd.promedio_norte) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma) IS NULL THEN 0
                ELSE (pd.promedio_norte - LAG(pd.promedio_norte) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma)) * ?
            END AS FLOAT) AS distancia,
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DI N fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDEA(tabla, unidad, prismas, idcomponente):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente]
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma)) * ? AS distancia,
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DA E: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoFechasDEA(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma)) * ? AS distancia,
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        AND p.hora_prisma BETWEEN ? AND ? 
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DA E fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasDEA(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.este_target AS FLOAT)) AS promedio_este,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (b.promedio_este - FIRST_VALUE(b.promedio_este) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma)) * ? AS distancia,
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DA E: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    @staticmethod
    def mdlCalcularDesplazamientoDiasFechasDEA(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.este_target AS FLOAT)) AS promedio_este,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (b.promedio_este - FIRST_VALUE(b.promedio_este) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma)) * ? AS distancia,
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DA E fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHorasDEA(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma, 
                AVG(CAST(p.este_target AS FLOAT)) AS promedio_este,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (pd.promedio_este - FIRST_VALUE(pd.promedio_este) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma)) * ? AS distancia,
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DA E: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHorasFechasDEA(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma, 
                AVG(CAST(p.este_target AS FLOAT)) AS promedio_este,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (pd.promedio_este - FIRST_VALUE(pd.promedio_este) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma)) * ? AS distancia,
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DA E fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDEI(tabla, unidad, prismas, idcomponente):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente]
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                ELSE (p.este_target - LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * ?
            END AS FLOAT) AS distancia,
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DI E: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoFechasDEI(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                ELSE (p.este_target - LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * ?
            END AS FLOAT) AS distancia,
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        AND p.hora_prisma BETWEEN ? AND ? 
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DI E fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasDEI(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.este_target AS FLOAT)) AS promedio_este,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(b.promedio_este) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma) IS NULL THEN 0
                ELSE (b.promedio_este - LAG(b.promedio_este) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma)) * ?
            END AS FLOAT) AS distancia,
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DI E: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasFechasDEI(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.este_target AS FLOAT)) AS promedio_este,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(b.promedio_este) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma) IS NULL THEN 0
                ELSE (b.promedio_este - LAG(b.promedio_este) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma)) * ?
            END AS FLOAT) AS distancia,
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DI E fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoFechasDNI(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                ELSE (p.norte_target - LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * ?
            END AS FLOAT) AS distancia,
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        AND p.hora_prisma BETWEEN ? AND ? 
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DI N fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasDNI(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(b.promedio_norte) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma) IS NULL THEN 0
                ELSE (b.promedio_norte - LAG(b.promedio_norte) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma)) * ?
            END AS FLOAT) AS distancia,
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DI N: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasFechasDNI(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(b.promedio_norte) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma) IS NULL THEN 0
                ELSE (b.promedio_norte - LAG(b.promedio_norte) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma)) * ?
            END AS FLOAT) AS distancia,
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DI N fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHorasDNI(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma, 
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(pd.promedio_norte) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma) IS NULL THEN 0
                ELSE (pd.promedio_norte - LAG(pd.promedio_norte) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma)) * ?
            END AS FLOAT) AS distancia,
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DI N: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHorasFechasDNI(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma, 
                AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(pd.promedio_norte) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma) IS NULL THEN 0
                ELSE (pd.promedio_norte - LAG(pd.promedio_norte) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma)) * ?
            END AS FLOAT) AS distancia,
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DI N fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDZA(tabla, unidad, prismas, idcomponente):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente]
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (p.elevacion_target - FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma)) * ? AS distancia,
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DA Z: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoFechasDZA(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (p.elevacion_target - FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma)) * ? AS distancia,
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        AND p.hora_prisma BETWEEN ? AND ? 
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DA Z fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasDZA(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.elevacion_target AS FLOAT)) AS promedio_elevacion,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (b.promedio_elevacion - FIRST_VALUE(b.promedio_elevacion) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma)) * ? AS distancia,
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DA Z: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasFechasDZA(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.elevacion_target AS FLOAT)) AS promedio_elevacion,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (b.promedio_elevacion - FIRST_VALUE(b.promedio_elevacion) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma)) * ? AS distancia,
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DA Z fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHorasDZA(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma, 
                AVG(CAST(p.elevacion_target AS FLOAT)) AS promedio_elevacion,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (pd.promedio_elevacion - FIRST_VALUE(pd.promedio_elevacion) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma)) * ? AS distancia,
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DA Z: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHorasFechasDZA(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma, 
                AVG(CAST(p.elevacion_target AS FLOAT)) AS promedio_elevacion,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (pd.promedio_elevacion - FIRST_VALUE(pd.promedio_elevacion) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma)) * ? AS distancia,
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DA Z fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDZI(tabla, unidad, prismas, idcomponente):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente]
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                ELSE (p.elevacion_target - LAG(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * ?
            END AS FLOAT) AS distancia,
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DI Z: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoFechasDZI(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                ELSE (p.elevacion_target - LAG(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * ?
            END AS FLOAT) AS distancia,
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        AND p.hora_prisma BETWEEN ? AND ? 
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DI Z fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasDZI(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.elevacion_target AS FLOAT)) AS promedio_elevacion,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(b.promedio_elevacion) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma) IS NULL THEN 0
                ELSE (b.promedio_elevacion - LAG(b.promedio_elevacion) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma)) * ?
            END AS FLOAT) AS distancia,
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DI Z: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasFechasDZI(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(CAST(p.elevacion_target AS FLOAT)) AS promedio_elevacion,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(b.promedio_elevacion) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma) IS NULL THEN 0
                ELSE (b.promedio_elevacion - LAG(b.promedio_elevacion) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma)) * ?
            END AS FLOAT) AS distancia,
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DI Z fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHorasDZI(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [unidad]
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma, 
                AVG(CAST(p.elevacion_target AS FLOAT)) AS promedio_elevacion,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(pd.promedio_elevacion) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma) IS NULL THEN 0
                ELSE (pd.promedio_elevacion - LAG(pd.promedio_elevacion) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma)) * ?
            END AS FLOAT) AS distancia,
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DI Z: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHorasFechasDZI(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma, 
                AVG(CAST(p.elevacion_target AS FLOAT)) AS promedio_elevacion,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(pd.promedio_elevacion) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma) IS NULL THEN 0
                ELSE (pd.promedio_elevacion - LAG(pd.promedio_elevacion) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma)) * ?
            END AS FLOAT) AS distancia,
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DI Z fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDAH(tabla, unidad, prismas, idcomponente):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        # Nota: La consulta SQL original NO usa el parámetro 'unidad' en el SELECT para multiplicar,
        # pero la firma del método en Python sí lo recibe. Para mantener compatibilidad con pyodbc,
        # solo pasamos los parámetros que realmente existen en la consulta SQL (placeholders).
        # Ajuste: params = prismas + [idcomponente] (se omite 'unidad' ya que no hay '?' para ella en el SQL).
        params = prismas + [idcomponente]
        
        # Traducción compleja de parseo de strings (Grados, Minutos, Segundos):
        # SQLite: substr(col, 1, instr(col, '°') - 1)
        # SQL Server: SUBSTRING(col, 1, CHARINDEX('°', col) - 1)
        # Se requiere CAST a FLOAT para las operaciones matemáticas.
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CASE 
                WHEN p.angulo_horizontal LIKE '%°%' AND p.angulo_horizontal LIKE '%''%' AND p.angulo_horizontal LIKE '%"%' THEN
                    CAST(SUBSTRING(p.angulo_horizontal, 1, CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) +
                    CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('°', p.angulo_horizontal) + 1, CHARINDEX('''', p.angulo_horizontal) - CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) / 60.0 +
                    CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('''', p.angulo_horizontal) + 1, CHARINDEX('"', p.angulo_horizontal) - CHARINDEX('''', p.angulo_horizontal) - 1) AS FLOAT) / 3600.0
                ELSE
                    CAST(p.angulo_horizontal AS FLOAT)
            END AS angulo_horizontal, 
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar Angulo Horizontal: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
                
    @staticmethod
    def mdlCalcularDesplazamientoFechasDAH(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        
        # Traducción compleja de parseo de strings (Grados, Minutos, Segundos) a T-SQL
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CASE 
                WHEN p.angulo_horizontal LIKE '%°%' AND p.angulo_horizontal LIKE '%''%' AND p.angulo_horizontal LIKE '%"%' THEN
                    CAST(SUBSTRING(p.angulo_horizontal, 1, CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) +
                    CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('°', p.angulo_horizontal) + 1, CHARINDEX('''', p.angulo_horizontal) - CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) / 60.0 +
                    CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('''', p.angulo_horizontal) + 1, CHARINDEX('"', p.angulo_horizontal) - CHARINDEX('''', p.angulo_horizontal) - 1) AS FLOAT) / 3600.0
                ELSE
                    CAST(p.angulo_horizontal AS FLOAT)
            END AS angulo_horizontal, 
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        AND p.hora_prisma BETWEEN ? AND ? 
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar Angulo Horizontal fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasDAH(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        # Nota: 'unidad' se recibe pero no se usa en la query original para multiplicar ángulos, 
        # solo se pasan los prismas y el componente.
        params = prismas + [idcomponente]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(
                    CASE 
                        WHEN p.angulo_horizontal LIKE '%°%' AND p.angulo_horizontal LIKE '%''%' AND p.angulo_horizontal LIKE '%"%' THEN
                            CAST(SUBSTRING(p.angulo_horizontal, 1, CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('°', p.angulo_horizontal) + 1, CHARINDEX('''', p.angulo_horizontal) - CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('''', p.angulo_horizontal) + 1, CHARINDEX('"', p.angulo_horizontal) - CHARINDEX('''', p.angulo_horizontal) - 1) AS FLOAT) / 3600.0
                        ELSE
                            CAST(p.angulo_horizontal AS FLOAT)
                    END
                ) AS promedio_horizontal,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            b.promedio_horizontal AS angulo, 
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias Angulo Horizontal: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasFechasDAH(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(
                    CASE 
                        WHEN p.angulo_horizontal LIKE '%°%' AND p.angulo_horizontal LIKE '%''%' AND p.angulo_horizontal LIKE '%"%' THEN
                            CAST(SUBSTRING(p.angulo_horizontal, 1, CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('°', p.angulo_horizontal) + 1, CHARINDEX('''', p.angulo_horizontal) - CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('''', p.angulo_horizontal) + 1, CHARINDEX('"', p.angulo_horizontal) - CHARINDEX('''', p.angulo_horizontal) - 1) AS FLOAT) / 3600.0
                        ELSE
                            CAST(p.angulo_horizontal AS FLOAT)
                    END
                ) AS promedio_horizontal,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            b.promedio_horizontal AS angulo, 
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias Angulo Horizontal fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHorasDAH(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente]
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(
                    CASE 
                        WHEN p.angulo_horizontal LIKE '%°%' AND p.angulo_horizontal LIKE '%''%' AND p.angulo_horizontal LIKE '%"%' THEN
                            CAST(SUBSTRING(p.angulo_horizontal, 1, CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('°', p.angulo_horizontal) + 1, CHARINDEX('''', p.angulo_horizontal) - CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('''', p.angulo_horizontal) + 1, CHARINDEX('"', p.angulo_horizontal) - CHARINDEX('''', p.angulo_horizontal) - 1) AS FLOAT) / 3600.0
                        ELSE
                            CAST(p.angulo_horizontal AS FLOAT)
                    END
                ) AS promedio_horizontal,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            pd.promedio_horizontal AS angulo, 
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas Angulo Horizontal: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHorasFechasDAH(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(
                    CASE 
                        WHEN p.angulo_horizontal LIKE '%°%' AND p.angulo_horizontal LIKE '%''%' AND p.angulo_horizontal LIKE '%"%' THEN
                            CAST(SUBSTRING(p.angulo_horizontal, 1, CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('°', p.angulo_horizontal) + 1, CHARINDEX('''', p.angulo_horizontal) - CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('''', p.angulo_horizontal) + 1, CHARINDEX('"', p.angulo_horizontal) - CHARINDEX('''', p.angulo_horizontal) - 1) AS FLOAT) / 3600.0
                        ELSE
                            CAST(p.angulo_horizontal AS FLOAT)
                    END
                ) AS promedio_horizontal,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            pd.promedio_horizontal AS angulo, 
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas Angulo Horizontal fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoAHA(tabla, unidad, prismas, idcomponente):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        # Nota: La lógica original no multiplica el ángulo por 'unidad'. 
        # Solo pasamos los parámetros necesarios para los placeholders.
        params = prismas + [idcomponente]
        
        # Lógica de conversión DMS a Decimal en T-SQL:
        # Grados: SUBSTRING(col, 1, CHARINDEX('°') - 1)
        # Minutos: SUBSTRING(col, CHARINDEX('°') + 1, CHARINDEX(''') - CHARINDEX('°') - 1)
        # Segundos: SUBSTRING(col, CHARINDEX(''') + 1, CHARINDEX('"') - CHARINDEX(''') - 1)
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (CASE 
                WHEN p.angulo_horizontal LIKE '%°%' AND p.angulo_horizontal LIKE '%''%' AND p.angulo_horizontal LIKE '%"%' THEN
                    CAST(SUBSTRING(p.angulo_horizontal, 1, CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) +
                    CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('°', p.angulo_horizontal) + 1, CHARINDEX('''', p.angulo_horizontal) - CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) / 60.0 +
                    CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('''', p.angulo_horizontal) + 1, CHARINDEX('"', p.angulo_horizontal) - CHARINDEX('''', p.angulo_horizontal) - 1) AS FLOAT) / 3600.0
                ELSE
                    CAST(p.angulo_horizontal AS FLOAT)
            END 
            - 
            FIRST_VALUE(
                CASE 
                    WHEN p.angulo_horizontal LIKE '%°%' AND p.angulo_horizontal LIKE '%''%' AND p.angulo_horizontal LIKE '%"%' THEN
                        CAST(SUBSTRING(p.angulo_horizontal, 1, CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) +
                        CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('°', p.angulo_horizontal) + 1, CHARINDEX('''', p.angulo_horizontal) - CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) / 60.0 +
                        CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('''', p.angulo_horizontal) + 1, CHARINDEX('"', p.angulo_horizontal) - CHARINDEX('''', p.angulo_horizontal) - 1) AS FLOAT) / 3600.0
                    ELSE
                        CAST(p.angulo_horizontal AS FLOAT)
                END) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma)
            ) AS angulo_horizontal, 
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DA Horizontal: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoFechasAHA(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (CASE 
                WHEN p.angulo_horizontal LIKE '%°%' AND p.angulo_horizontal LIKE '%''%' AND p.angulo_horizontal LIKE '%"%' THEN
                    CAST(SUBSTRING(p.angulo_horizontal, 1, CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) +
                    CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('°', p.angulo_horizontal) + 1, CHARINDEX('''', p.angulo_horizontal) - CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) / 60.0 +
                    CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('''', p.angulo_horizontal) + 1, CHARINDEX('"', p.angulo_horizontal) - CHARINDEX('''', p.angulo_horizontal) - 1) AS FLOAT) / 3600.0
                ELSE
                    CAST(p.angulo_horizontal AS FLOAT)
            END 
            - 
            FIRST_VALUE(
                CASE 
                    WHEN p.angulo_horizontal LIKE '%°%' AND p.angulo_horizontal LIKE '%''%' AND p.angulo_horizontal LIKE '%"%' THEN
                        CAST(SUBSTRING(p.angulo_horizontal, 1, CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) +
                        CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('°', p.angulo_horizontal) + 1, CHARINDEX('''', p.angulo_horizontal) - CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) / 60.0 +
                        CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('''', p.angulo_horizontal) + 1, CHARINDEX('"', p.angulo_horizontal) - CHARINDEX('''', p.angulo_horizontal) - 1) AS FLOAT) / 3600.0
                    ELSE
                        CAST(p.angulo_horizontal AS FLOAT)
                END) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma)
            ) AS angulo_horizontal, 
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        AND p.hora_prisma BETWEEN ? AND ? 
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DA Horizontal fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasAHA(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(
                    CASE 
                        WHEN p.angulo_horizontal LIKE '%°%' AND p.angulo_horizontal LIKE '%''%' AND p.angulo_horizontal LIKE '%"%' THEN
                            CAST(SUBSTRING(p.angulo_horizontal, 1, CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('°', p.angulo_horizontal) + 1, CHARINDEX('''', p.angulo_horizontal) - CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('''', p.angulo_horizontal) + 1, CHARINDEX('"', p.angulo_horizontal) - CHARINDEX('''', p.angulo_horizontal) - 1) AS FLOAT) / 3600.0
                        ELSE
                            CAST(p.angulo_horizontal AS FLOAT)
                    END
                ) AS promedio_horizontal,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (b.promedio_horizontal - FIRST_VALUE(b.promedio_horizontal)
                OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma)
            ) AS angulo,
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DA Horizontal: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasFechasAHA(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(
                    CASE 
                        WHEN p.angulo_horizontal LIKE '%°%' AND p.angulo_horizontal LIKE '%''%' AND p.angulo_horizontal LIKE '%"%' THEN
                            CAST(SUBSTRING(p.angulo_horizontal, 1, CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('°', p.angulo_horizontal) + 1, CHARINDEX('''', p.angulo_horizontal) - CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('''', p.angulo_horizontal) + 1, CHARINDEX('"', p.angulo_horizontal) - CHARINDEX('''', p.angulo_horizontal) - 1) AS FLOAT) / 3600.0
                        ELSE
                            CAST(p.angulo_horizontal AS FLOAT)
                    END
                ) AS promedio_horizontal,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (b.promedio_horizontal - FIRST_VALUE(b.promedio_horizontal) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma)) AS angulo,
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DA Horizontal fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHorasAHA(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente]
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(
                    CASE 
                        WHEN p.angulo_horizontal LIKE '%°%' AND p.angulo_horizontal LIKE '%''%' AND p.angulo_horizontal LIKE '%"%' THEN
                            CAST(SUBSTRING(p.angulo_horizontal, 1, CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('°', p.angulo_horizontal) + 1, CHARINDEX('''', p.angulo_horizontal) - CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('''', p.angulo_horizontal) + 1, CHARINDEX('"', p.angulo_horizontal) - CHARINDEX('''', p.angulo_horizontal) - 1) AS FLOAT) / 3600.0
                        ELSE
                            CAST(p.angulo_horizontal AS FLOAT)
                    END
                ) AS promedio_horizontal,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (pd.promedio_horizontal - FIRST_VALUE(pd.promedio_horizontal) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma)) AS angulo,
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DA Horizontal: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHorasFechasAHA(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(
                    CASE 
                        WHEN p.angulo_horizontal LIKE '%°%' AND p.angulo_horizontal LIKE '%''%' AND p.angulo_horizontal LIKE '%"%' THEN
                            CAST(SUBSTRING(p.angulo_horizontal, 1, CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('°', p.angulo_horizontal) + 1, CHARINDEX('''', p.angulo_horizontal) - CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('''', p.angulo_horizontal) + 1, CHARINDEX('"', p.angulo_horizontal) - CHARINDEX('''', p.angulo_horizontal) - 1) AS FLOAT) / 3600.0
                        ELSE
                            CAST(p.angulo_horizontal AS FLOAT)
                    END
                ) AS promedio_horizontal,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (pd.promedio_horizontal - FIRST_VALUE(pd.promedio_horizontal) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma)) AS angulo,
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DA Horizontal fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoAHI(tabla, unidad, prismas, idcomponente):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente]
        
        # Este es el SQL más complejo debido a la conversión DMS en el LAG.
        # En T-SQL, las comillas simples dentro de un string literal (el parámetro de CHARINDEX) se escapan duplicándolas ('''').
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                ELSE (
                    (CASE 
                        WHEN p.angulo_horizontal LIKE '%°%' AND p.angulo_horizontal LIKE '%''%' AND p.angulo_horizontal LIKE '%"%' THEN
                            CAST(SUBSTRING(p.angulo_horizontal, 1, CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('°', p.angulo_horizontal) + 1, CHARINDEX('''', p.angulo_horizontal) - CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('''', p.angulo_horizontal) + 1, CHARINDEX('"', p.angulo_horizontal) - CHARINDEX('''', p.angulo_horizontal) - 1) AS FLOAT) / 3600.0
                        ELSE CAST(p.angulo_horizontal AS FLOAT)
                    END)
                    -
                    (CASE 
                        WHEN LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) LIKE '%°%' 
                            AND LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) LIKE '%''%' 
                            AND LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) LIKE '%"%' THEN
                            CAST(SUBSTRING(LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 1, CHARINDEX('°', LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) - 1) AS FLOAT) +
                            CAST(SUBSTRING(LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), CHARINDEX('°', LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) + 1, CHARINDEX('''', LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) - CHARINDEX('°', LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), CHARINDEX('''', LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) + 1, CHARINDEX('"', LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) - CHARINDEX('''', LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) - 1) AS FLOAT) / 3600.0
                        ELSE 
                            CAST(LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS FLOAT)
                    END)
                )
            END AS FLOAT) AS angulo, 
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DI Horizontal: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoFechasAHI(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                ELSE (
                    (CASE 
                        WHEN p.angulo_horizontal LIKE '%°%' AND p.angulo_horizontal LIKE '%''%' AND p.angulo_horizontal LIKE '%"%' THEN
                            CAST(SUBSTRING(p.angulo_horizontal, 1, CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('°', p.angulo_horizontal) + 1, CHARINDEX('''', p.angulo_horizontal) - CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('''', p.angulo_horizontal) + 1, CHARINDEX('"', p.angulo_horizontal) - CHARINDEX('''', p.angulo_horizontal) - 1) AS FLOAT) / 3600.0
                        ELSE CAST(p.angulo_horizontal AS FLOAT)
                    END)
                    -
                    (CASE 
                        WHEN LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) LIKE '%°%' 
                            AND LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) LIKE '%''%' 
                            AND LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) LIKE '%"%' THEN
                            CAST(SUBSTRING(LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 1, CHARINDEX('°', LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) - 1) AS FLOAT) +
                            CAST(SUBSTRING(LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), CHARINDEX('°', LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) + 1, CHARINDEX('''', LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) - CHARINDEX('°', LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), CHARINDEX('''', LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) + 1, CHARINDEX('"', LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) - CHARINDEX('''', LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) - 1) AS FLOAT) / 3600.0
                        ELSE 
                            CAST(LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS FLOAT)
                    END)
                )
            END AS FLOAT) AS angulo, 
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        AND p.hora_prisma BETWEEN ? AND ? 
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DI Horizontal fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasAHI(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(
                    CASE
                        WHEN p.angulo_horizontal LIKE '%°%' AND p.angulo_horizontal LIKE '%''%' AND p.angulo_horizontal LIKE '%"%' THEN
                            CAST(SUBSTRING(p.angulo_horizontal, 1, CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('°', p.angulo_horizontal) + 1, CHARINDEX('''', p.angulo_horizontal) - CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('''', p.angulo_horizontal) + 1, CHARINDEX('"', p.angulo_horizontal) - CHARINDEX('''', p.angulo_horizontal) - 1) AS FLOAT) / 3600.0
                        ELSE CAST(p.angulo_horizontal AS FLOAT)
                    END
                ) AS promedio_horizontal,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(b.promedio_horizontal) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma) IS NULL THEN 0
                ELSE (b.promedio_horizontal - LAG(b.promedio_horizontal) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma))
            END AS FLOAT) AS angulo, 
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DI Horizontal: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasFechasAHI(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(
                    CASE
                        WHEN p.angulo_horizontal LIKE '%°%' AND p.angulo_horizontal LIKE '%''%' AND p.angulo_horizontal LIKE '%"%' THEN
                            CAST(SUBSTRING(p.angulo_horizontal, 1, CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('°', p.angulo_horizontal) + 1, CHARINDEX('''', p.angulo_horizontal) - CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('''', p.angulo_horizontal) + 1, CHARINDEX('"', p.angulo_horizontal) - CHARINDEX('''', p.angulo_horizontal) - 1) AS FLOAT) / 3600.0
                        ELSE CAST(p.angulo_horizontal AS FLOAT)
                    END
                ) AS promedio_horizontal,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(b.promedio_horizontal) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma) IS NULL THEN 0
                ELSE (b.promedio_horizontal - LAG(b.promedio_horizontal) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma))
            END AS FLOAT) AS angulo, 
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DI Horizontal fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHorasAHI(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente]
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(
                    CASE
                        WHEN p.angulo_horizontal LIKE '%°%' AND p.angulo_horizontal LIKE '%''%' AND p.angulo_horizontal LIKE '%"%' THEN
                            CAST(SUBSTRING(p.angulo_horizontal, 1, CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('°', p.angulo_horizontal) + 1, CHARINDEX('''', p.angulo_horizontal) - CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('''', p.angulo_horizontal) + 1, CHARINDEX('"', p.angulo_horizontal) - CHARINDEX('''', p.angulo_horizontal) - 1) AS FLOAT) / 3600.0
                        ELSE CAST(p.angulo_horizontal AS FLOAT)
                    END
                ) AS promedio_horizontal,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(pd.promedio_horizontal) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma) IS NULL THEN 0
                ELSE (pd.promedio_horizontal - LAG(pd.promedio_horizontal) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma))
            END AS FLOAT) AS angulo, 
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DI Horizontal: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
                
    @staticmethod
    def mdlCalcularDesplazamientoHorasFechasAHA(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(
                    CASE 
                        WHEN p.angulo_horizontal LIKE '%°%' AND p.angulo_horizontal LIKE '%''%' AND p.angulo_horizontal LIKE '%"%' THEN
                            CAST(SUBSTRING(p.angulo_horizontal, 1, CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('°', p.angulo_horizontal) + 1, CHARINDEX('''', p.angulo_horizontal) - CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('''', p.angulo_horizontal) + 1, CHARINDEX('"', p.angulo_horizontal) - CHARINDEX('''', p.angulo_horizontal) - 1) AS FLOAT) / 3600.0
                        ELSE
                            CAST(p.angulo_horizontal AS FLOAT)
                    END
                ) AS promedio_horizontal,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (pd.promedio_horizontal - FIRST_VALUE(pd.promedio_horizontal) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma)) AS angulo,
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DA Horizontal fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoAHI(tabla, unidad, prismas, idcomponente):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente]
        
        # Traducción compleja: Parseo de DMS a Float tanto para el valor actual como para el valor LAG (anterior).
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                ELSE (
                    -- Parseo Valor Actual
                    (CASE 
                        WHEN p.angulo_horizontal LIKE '%°%' AND p.angulo_horizontal LIKE '%''%' AND p.angulo_horizontal LIKE '%"%' THEN
                            CAST(SUBSTRING(p.angulo_horizontal, 1, CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('°', p.angulo_horizontal) + 1, CHARINDEX('''', p.angulo_horizontal) - CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('''', p.angulo_horizontal) + 1, CHARINDEX('"', p.angulo_horizontal) - CHARINDEX('''', p.angulo_horizontal) - 1) AS FLOAT) / 3600.0
                        ELSE CAST(p.angulo_horizontal AS FLOAT)
                    END)
                    -
                    -- Parseo Valor Anterior (LAG)
                    (CASE 
                        WHEN LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) LIKE '%°%' 
                            AND LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) LIKE '%''%' 
                            AND LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) LIKE '%"%' THEN
                            CAST(SUBSTRING(LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 1, CHARINDEX('°', LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) - 1) AS FLOAT) +
                            CAST(SUBSTRING(LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), CHARINDEX('°', LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) + 1, CHARINDEX('''', LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) - CHARINDEX('°', LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), CHARINDEX('''', LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) + 1, CHARINDEX('"', LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) - CHARINDEX('''', LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) - 1) AS FLOAT) / 3600.0
                        ELSE 
                            CAST(LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS FLOAT)
                    END)
                )
            END AS FLOAT) AS angulo, 
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DI Horizontal: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoFechasAHI(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                ELSE (
                    (CASE 
                        WHEN p.angulo_horizontal LIKE '%°%' AND p.angulo_horizontal LIKE '%''%' AND p.angulo_horizontal LIKE '%"%' THEN
                            CAST(SUBSTRING(p.angulo_horizontal, 1, CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('°', p.angulo_horizontal) + 1, CHARINDEX('''', p.angulo_horizontal) - CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('''', p.angulo_horizontal) + 1, CHARINDEX('"', p.angulo_horizontal) - CHARINDEX('''', p.angulo_horizontal) - 1) AS FLOAT) / 3600.0
                        ELSE CAST(p.angulo_horizontal AS FLOAT)
                    END)
                    -
                    (CASE 
                        WHEN LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) LIKE '%°%' 
                            AND LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) LIKE '%''%' 
                            AND LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) LIKE '%"%' THEN
                            CAST(SUBSTRING(LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 1, CHARINDEX('°', LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) - 1) AS FLOAT) +
                            CAST(SUBSTRING(LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), CHARINDEX('°', LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) + 1, CHARINDEX('''', LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) - CHARINDEX('°', LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), CHARINDEX('''', LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) + 1, CHARINDEX('"', LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) - CHARINDEX('''', LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) - 1) AS FLOAT) / 3600.0
                        ELSE 
                            CAST(LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS FLOAT)
                    END)
                )
            END AS FLOAT) AS angulo, 
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        AND p.hora_prisma BETWEEN ? AND ? 
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DI Horizontal fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasAHI(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(
                    CASE
                        WHEN p.angulo_horizontal LIKE '%°%' AND p.angulo_horizontal LIKE '%''%' AND p.angulo_horizontal LIKE '%"%' THEN
                            CAST(SUBSTRING(p.angulo_horizontal, 1, CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('°', p.angulo_horizontal) + 1, CHARINDEX('''', p.angulo_horizontal) - CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('''', p.angulo_horizontal) + 1, CHARINDEX('"', p.angulo_horizontal) - CHARINDEX('''', p.angulo_horizontal) - 1) AS FLOAT) / 3600.0
                        ELSE CAST(p.angulo_horizontal AS FLOAT)
                    END
                ) AS promedio_horizontal,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias, 
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}), 
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(b.promedio_horizontal) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma) IS NULL THEN 0
                ELSE (b.promedio_horizontal - LAG(b.promedio_horizontal) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma))
            END AS FLOAT) AS angulo, 
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DI Horizontal: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasFechasAHI(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(
                    CASE
                        WHEN p.angulo_horizontal LIKE '%°%' AND p.angulo_horizontal LIKE '%''%' AND p.angulo_horizontal LIKE '%"%' THEN
                            CAST(SUBSTRING(p.angulo_horizontal, 1, CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('°', p.angulo_horizontal) + 1, CHARINDEX('''', p.angulo_horizontal) - CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('''', p.angulo_horizontal) + 1, CHARINDEX('"', p.angulo_horizontal) - CHARINDEX('''', p.angulo_horizontal) - 1) AS FLOAT) / 3600.0
                        ELSE CAST(p.angulo_horizontal AS FLOAT)
                    END
                ) AS promedio_horizontal,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias, 
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}), 
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(b.promedio_horizontal) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma) IS NULL THEN 0
                ELSE (b.promedio_horizontal - LAG(b.promedio_horizontal) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma))
            END AS FLOAT) AS angulo, 
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DI Horizontal fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHorasAHI(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente]
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(
                    CASE
                        WHEN p.angulo_horizontal LIKE '%°%' AND p.angulo_horizontal LIKE '%''%' AND p.angulo_horizontal LIKE '%"%' THEN
                            CAST(SUBSTRING(p.angulo_horizontal, 1, CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('°', p.angulo_horizontal) + 1, CHARINDEX('''', p.angulo_horizontal) - CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('''', p.angulo_horizontal) + 1, CHARINDEX('"', p.angulo_horizontal) - CHARINDEX('''', p.angulo_horizontal) - 1) AS FLOAT) / 3600.0
                        ELSE CAST(p.angulo_horizontal AS FLOAT)
                    END
                ) AS promedio_horizontal,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(pd.promedio_horizontal) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma) IS NULL THEN 0
                ELSE (pd.promedio_horizontal - LAG(pd.promedio_horizontal) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma))
            END AS FLOAT) AS angulo, 
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DI Horizontal: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHorasFechasAHI(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(
                    CASE
                        WHEN p.angulo_horizontal LIKE '%°%' AND p.angulo_horizontal LIKE '%''%' AND p.angulo_horizontal LIKE '%"%' THEN
                            CAST(SUBSTRING(p.angulo_horizontal, 1, CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('°', p.angulo_horizontal) + 1, CHARINDEX('''', p.angulo_horizontal) - CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('''', p.angulo_horizontal) + 1, CHARINDEX('"', p.angulo_horizontal) - CHARINDEX('''', p.angulo_horizontal) - 1) AS FLOAT) / 3600.0
                        ELSE CAST(p.angulo_horizontal AS FLOAT)
                    END
                ) AS promedio_horizontal,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(pd.promedio_horizontal) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma) IS NULL THEN 0
                ELSE (pd.promedio_horizontal - LAG(pd.promedio_horizontal) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma))
            END AS FLOAT) AS angulo, 
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DI Horizontal fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDAV(tabla, unidad, prismas, idcomponente):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente]
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CASE 
                WHEN p.angulo_vertical LIKE '%°%' AND p.angulo_vertical LIKE '%''%' AND p.angulo_vertical LIKE '%"%' THEN
                    CAST(SUBSTRING(p.angulo_vertical, 1, CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) +
                    CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('°', p.angulo_vertical) + 1, CHARINDEX('''', p.angulo_vertical) - CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) / 60.0 +
                    CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('''', p.angulo_vertical) + 1, CHARINDEX('"', p.angulo_vertical) - CHARINDEX('''', p.angulo_vertical) - 1) AS FLOAT) / 3600.0
                ELSE
                    CAST(p.angulo_vertical AS FLOAT)
            END AS angulo_vertical, 
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar Angulo Vertical: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoFechasDAV(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CASE 
                WHEN p.angulo_vertical LIKE '%°%' AND p.angulo_vertical LIKE '%''%' AND p.angulo_vertical LIKE '%"%' THEN
                    CAST(SUBSTRING(p.angulo_vertical, 1, CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) +
                    CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('°', p.angulo_vertical) + 1, CHARINDEX('''', p.angulo_vertical) - CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) / 60.0 +
                    CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('''', p.angulo_vertical) + 1, CHARINDEX('"', p.angulo_vertical) - CHARINDEX('''', p.angulo_vertical) - 1) AS FLOAT) / 3600.0
                ELSE
                    CAST(p.angulo_vertical AS FLOAT)
            END AS angulo_vertical, 
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        AND p.hora_prisma BETWEEN ? AND ? 
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar Angulo Vertical fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasDAV(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(
                    CASE 
                        WHEN p.angulo_vertical LIKE '%°%' AND p.angulo_vertical LIKE '%''%' AND p.angulo_vertical LIKE '%"%' THEN
                            CAST(SUBSTRING(p.angulo_vertical, 1, CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) +
                            CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('°', p.angulo_vertical) + 1, CHARINDEX('''', p.angulo_vertical) - CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('''', p.angulo_vertical) + 1, CHARINDEX('"', p.angulo_vertical) - CHARINDEX('''', p.angulo_vertical) - 1) AS FLOAT) / 3600.0
                        ELSE
                            CAST(p.angulo_vertical AS FLOAT)
                    END
                ) AS promedio_vertical,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            b.promedio_vertical AS angulo, 
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias Angulo Vertical: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasFechasDAV(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(
                    CASE 
                        WHEN p.angulo_vertical LIKE '%°%' AND p.angulo_vertical LIKE '%''%' AND p.angulo_vertical LIKE '%"%' THEN
                            CAST(SUBSTRING(p.angulo_vertical, 1, CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) +
                            CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('°', p.angulo_vertical) + 1, CHARINDEX('''', p.angulo_vertical) - CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('''', p.angulo_vertical) + 1, CHARINDEX('"', p.angulo_vertical) - CHARINDEX('''', p.angulo_vertical) - 1) AS FLOAT) / 3600.0
                        ELSE
                            CAST(p.angulo_vertical AS FLOAT)
                    END
                ) AS promedio_vertical,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            b.promedio_vertical AS angulo, 
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias Angulo Vertical fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHorasDAV(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente]
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(
                    CASE 
                        WHEN p.angulo_vertical LIKE '%°%' AND p.angulo_vertical LIKE '%''%' AND p.angulo_vertical LIKE '%"%' THEN
                            CAST(SUBSTRING(p.angulo_vertical, 1, CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) +
                            CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('°', p.angulo_vertical) + 1, CHARINDEX('''', p.angulo_vertical) - CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('''', p.angulo_vertical) + 1, CHARINDEX('"', p.angulo_vertical) - CHARINDEX('''', p.angulo_vertical) - 1) AS FLOAT) / 3600.0
                        ELSE
                            CAST(p.angulo_vertical AS FLOAT)
                    END
                ) AS promedio_vertical,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            pd.promedio_vertical AS angulo, 
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas Angulo Vertical: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
                
    @staticmethod
    def mdlCalcularDesplazamientoHorasFechasAHA(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(
                    CASE 
                        WHEN p.angulo_horizontal LIKE '%°%' AND p.angulo_horizontal LIKE '%''%' AND p.angulo_horizontal LIKE '%"%' THEN
                            CAST(SUBSTRING(p.angulo_horizontal, 1, CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('°', p.angulo_horizontal) + 1, CHARINDEX('''', p.angulo_horizontal) - CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('''', p.angulo_horizontal) + 1, CHARINDEX('"', p.angulo_horizontal) - CHARINDEX('''', p.angulo_horizontal) - 1) AS FLOAT) / 3600.0
                        ELSE
                            CAST(p.angulo_horizontal AS FLOAT)
                    END
                ) AS promedio_horizontal,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (pd.promedio_horizontal - FIRST_VALUE(pd.promedio_horizontal) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma)) AS angulo,
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DA Horizontal fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoAHI(tabla, unidad, prismas, idcomponente):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente]
        
        # SQL Complejo: Parseo DMS en el valor actual MENOS Parseo DMS en el valor anterior (LAG)
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                ELSE (
                    (CASE 
                        WHEN p.angulo_horizontal LIKE '%°%' AND p.angulo_horizontal LIKE '%''%' AND p.angulo_horizontal LIKE '%"%' THEN
                            CAST(SUBSTRING(p.angulo_horizontal, 1, CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('°', p.angulo_horizontal) + 1, CHARINDEX('''', p.angulo_horizontal) - CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('''', p.angulo_horizontal) + 1, CHARINDEX('"', p.angulo_horizontal) - CHARINDEX('''', p.angulo_horizontal) - 1) AS FLOAT) / 3600.0
                        ELSE CAST(p.angulo_horizontal AS FLOAT)
                    END)
                    -
                    (CASE 
                        WHEN LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) LIKE '%°%' 
                            AND LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) LIKE '%''%' 
                            AND LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) LIKE '%"%' THEN
                            CAST(SUBSTRING(LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 1, CHARINDEX('°', LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) - 1) AS FLOAT) +
                            CAST(SUBSTRING(LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), CHARINDEX('°', LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) + 1, CHARINDEX('''', LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) - CHARINDEX('°', LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), CHARINDEX('''', LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) + 1, CHARINDEX('"', LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) - CHARINDEX('''', LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) - 1) AS FLOAT) / 3600.0
                        ELSE 
                            CAST(LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS FLOAT)
                    END)
                )
            END AS FLOAT) AS angulo, 
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DI Horizontal: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoFechasAHI(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                ELSE (
                    (CASE 
                        WHEN p.angulo_horizontal LIKE '%°%' AND p.angulo_horizontal LIKE '%''%' AND p.angulo_horizontal LIKE '%"%' THEN
                            CAST(SUBSTRING(p.angulo_horizontal, 1, CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('°', p.angulo_horizontal) + 1, CHARINDEX('''', p.angulo_horizontal) - CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('''', p.angulo_horizontal) + 1, CHARINDEX('"', p.angulo_horizontal) - CHARINDEX('''', p.angulo_horizontal) - 1) AS FLOAT) / 3600.0
                        ELSE CAST(p.angulo_horizontal AS FLOAT)
                    END)
                    -
                    (CASE 
                        WHEN LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) LIKE '%°%' 
                            AND LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) LIKE '%''%' 
                            AND LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) LIKE '%"%' THEN
                            CAST(SUBSTRING(LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 1, CHARINDEX('°', LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) - 1) AS FLOAT) +
                            CAST(SUBSTRING(LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), CHARINDEX('°', LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) + 1, CHARINDEX('''', LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) - CHARINDEX('°', LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), CHARINDEX('''', LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) + 1, CHARINDEX('"', LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) - CHARINDEX('''', LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) - 1) AS FLOAT) / 3600.0
                        ELSE 
                            CAST(LAG(p.angulo_horizontal) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS FLOAT)
                    END)
                )
            END AS FLOAT) AS angulo, 
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        AND p.hora_prisma BETWEEN ? AND ? 
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DI Horizontal fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasAHI(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(
                    CASE
                        WHEN p.angulo_horizontal LIKE '%°%' AND p.angulo_horizontal LIKE '%''%' AND p.angulo_horizontal LIKE '%"%' THEN
                            CAST(SUBSTRING(p.angulo_horizontal, 1, CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('°', p.angulo_horizontal) + 1, CHARINDEX('''', p.angulo_horizontal) - CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('''', p.angulo_horizontal) + 1, CHARINDEX('"', p.angulo_horizontal) - CHARINDEX('''', p.angulo_horizontal) - 1) AS FLOAT) / 3600.0
                        ELSE CAST(p.angulo_horizontal AS FLOAT)
                    END
                ) AS promedio_horizontal,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias, 
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}), 
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(b.promedio_horizontal) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma) IS NULL THEN 0
                ELSE (b.promedio_horizontal - LAG(b.promedio_horizontal) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma))
            END AS FLOAT) AS angulo, 
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DI Horizontal: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasFechasAHI(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(
                    CASE
                        WHEN p.angulo_horizontal LIKE '%°%' AND p.angulo_horizontal LIKE '%''%' AND p.angulo_horizontal LIKE '%"%' THEN
                            CAST(SUBSTRING(p.angulo_horizontal, 1, CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('°', p.angulo_horizontal) + 1, CHARINDEX('''', p.angulo_horizontal) - CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('''', p.angulo_horizontal) + 1, CHARINDEX('"', p.angulo_horizontal) - CHARINDEX('''', p.angulo_horizontal) - 1) AS FLOAT) / 3600.0
                        ELSE CAST(p.angulo_horizontal AS FLOAT)
                    END
                ) AS promedio_horizontal,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias, 
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}), 
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(b.promedio_horizontal) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma) IS NULL THEN 0
                ELSE (b.promedio_horizontal - LAG(b.promedio_horizontal) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma))
            END AS FLOAT) AS angulo, 
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DI Horizontal fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHorasAHI(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente]
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(
                    CASE
                        WHEN p.angulo_horizontal LIKE '%°%' AND p.angulo_horizontal LIKE '%''%' AND p.angulo_horizontal LIKE '%"%' THEN
                            CAST(SUBSTRING(p.angulo_horizontal, 1, CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('°', p.angulo_horizontal) + 1, CHARINDEX('''', p.angulo_horizontal) - CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('''', p.angulo_horizontal) + 1, CHARINDEX('"', p.angulo_horizontal) - CHARINDEX('''', p.angulo_horizontal) - 1) AS FLOAT) / 3600.0
                        ELSE CAST(p.angulo_horizontal AS FLOAT)
                    END
                ) AS promedio_horizontal,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(pd.promedio_horizontal) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma) IS NULL THEN 0
                ELSE (pd.promedio_horizontal - LAG(pd.promedio_horizontal) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma))
            END AS FLOAT) AS angulo, 
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DI Horizontal: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHorasFechasAHI(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(
                    CASE
                        WHEN p.angulo_horizontal LIKE '%°%' AND p.angulo_horizontal LIKE '%''%' AND p.angulo_horizontal LIKE '%"%' THEN
                            CAST(SUBSTRING(p.angulo_horizontal, 1, CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('°', p.angulo_horizontal) + 1, CHARINDEX('''', p.angulo_horizontal) - CHARINDEX('°', p.angulo_horizontal) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(p.angulo_horizontal, CHARINDEX('''', p.angulo_horizontal) + 1, CHARINDEX('"', p.angulo_horizontal) - CHARINDEX('''', p.angulo_horizontal) - 1) AS FLOAT) / 3600.0
                        ELSE CAST(p.angulo_horizontal AS FLOAT)
                    END
                ) AS promedio_horizontal,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(pd.promedio_horizontal) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma) IS NULL THEN 0
                ELSE (pd.promedio_horizontal - LAG(pd.promedio_horizontal) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma))
            END AS FLOAT) AS angulo, 
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DI Horizontal fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDAV(tabla, unidad, prismas, idcomponente):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente]
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CASE 
                WHEN p.angulo_vertical LIKE '%°%' AND p.angulo_vertical LIKE '%''%' AND p.angulo_vertical LIKE '%"%' THEN
                    CAST(SUBSTRING(p.angulo_vertical, 1, CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) +
                    CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('°', p.angulo_vertical) + 1, CHARINDEX('''', p.angulo_vertical) - CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) / 60.0 +
                    CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('''', p.angulo_vertical) + 1, CHARINDEX('"', p.angulo_vertical) - CHARINDEX('''', p.angulo_vertical) - 1) AS FLOAT) / 3600.0
                ELSE
                    CAST(p.angulo_vertical AS FLOAT)
            END AS angulo_vertical, 
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar Angulo Vertical: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoFechasDAV(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CASE 
                WHEN p.angulo_vertical LIKE '%°%' AND p.angulo_vertical LIKE '%''%' AND p.angulo_vertical LIKE '%"%' THEN
                    CAST(SUBSTRING(p.angulo_vertical, 1, CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) +
                    CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('°', p.angulo_vertical) + 1, CHARINDEX('''', p.angulo_vertical) - CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) / 60.0 +
                    CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('''', p.angulo_vertical) + 1, CHARINDEX('"', p.angulo_vertical) - CHARINDEX('''', p.angulo_vertical) - 1) AS FLOAT) / 3600.0
                ELSE
                    CAST(p.angulo_vertical AS FLOAT)
            END AS angulo_vertical, 
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        AND p.hora_prisma BETWEEN ? AND ? 
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar Angulo Vertical fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasDAV(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(
                    CASE 
                        WHEN p.angulo_vertical LIKE '%°%' AND p.angulo_vertical LIKE '%''%' AND p.angulo_vertical LIKE '%"%' THEN
                            CAST(SUBSTRING(p.angulo_vertical, 1, CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) +
                            CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('°', p.angulo_vertical) + 1, CHARINDEX('''', p.angulo_vertical) - CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('''', p.angulo_vertical) + 1, CHARINDEX('"', p.angulo_vertical) - CHARINDEX('''', p.angulo_vertical) - 1) AS FLOAT) / 3600.0
                        ELSE
                            CAST(p.angulo_vertical AS FLOAT)
                    END
                ) AS promedio_vertical,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            b.promedio_vertical AS angulo, 
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias Angulo Vertical: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasFechasDAV(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(
                    CASE 
                        WHEN p.angulo_vertical LIKE '%°%' AND p.angulo_vertical LIKE '%''%' AND p.angulo_vertical LIKE '%"%' THEN
                            CAST(SUBSTRING(p.angulo_vertical, 1, CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) +
                            CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('°', p.angulo_vertical) + 1, CHARINDEX('''', p.angulo_vertical) - CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('''', p.angulo_vertical) + 1, CHARINDEX('"', p.angulo_vertical) - CHARINDEX('''', p.angulo_vertical) - 1) AS FLOAT) / 3600.0
                        ELSE
                            CAST(p.angulo_vertical AS FLOAT)
                    END
                ) AS promedio_vertical,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            b.promedio_vertical AS angulo, 
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias Angulo Vertical fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHorasDAV(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente]
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(
                    CASE 
                        WHEN p.angulo_vertical LIKE '%°%' AND p.angulo_vertical LIKE '%''%' AND p.angulo_vertical LIKE '%"%' THEN
                            CAST(SUBSTRING(p.angulo_vertical, 1, CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) +
                            CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('°', p.angulo_vertical) + 1, CHARINDEX('''', p.angulo_vertical) - CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('''', p.angulo_vertical) + 1, CHARINDEX('"', p.angulo_vertical) - CHARINDEX('''', p.angulo_vertical) - 1) AS FLOAT) / 3600.0
                        ELSE
                            CAST(p.angulo_vertical AS FLOAT)
                    END
                ) AS promedio_vertical,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            pd.promedio_vertical AS angulo, 
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas Angulo Vertical: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHorasFechasDAV(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(
                    CASE 
                        WHEN p.angulo_vertical LIKE '%°%' AND p.angulo_vertical LIKE '%''%' AND p.angulo_vertical LIKE '%"%' THEN
                            CAST(SUBSTRING(p.angulo_vertical, 1, CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) +
                            CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('°', p.angulo_vertical) + 1, CHARINDEX('''', p.angulo_vertical) - CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('''', p.angulo_vertical) + 1, CHARINDEX('"', p.angulo_vertical) - CHARINDEX('''', p.angulo_vertical) - 1) AS FLOAT) / 3600.0
                        ELSE
                            CAST(p.angulo_vertical AS FLOAT)
                    END
                ) AS promedio_vertical,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            pd.promedio_vertical AS angulo, 
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas Angulo Vertical fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoAVA(tabla, unidad, prismas, idcomponente):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente]
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (CASE 
                WHEN p.angulo_vertical LIKE '%°%' AND p.angulo_vertical LIKE '%''%' AND p.angulo_vertical LIKE '%"%' THEN
                    CAST(SUBSTRING(p.angulo_vertical, 1, CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) +
                    CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('°', p.angulo_vertical) + 1, CHARINDEX('''', p.angulo_vertical) - CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) / 60.0 +
                    CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('''', p.angulo_vertical) + 1, CHARINDEX('"', p.angulo_vertical) - CHARINDEX('''', p.angulo_vertical) - 1) AS FLOAT) / 3600.0
                ELSE
                    CAST(p.angulo_vertical AS FLOAT)
            END 
            - 
            FIRST_VALUE(
                CASE 
                    WHEN p.angulo_vertical LIKE '%°%' AND p.angulo_vertical LIKE '%''%' AND p.angulo_vertical LIKE '%"%' THEN
                        CAST(SUBSTRING(p.angulo_vertical, 1, CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) +
                        CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('°', p.angulo_vertical) + 1, CHARINDEX('''', p.angulo_vertical) - CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) / 60.0 +
                        CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('''', p.angulo_vertical) + 1, CHARINDEX('"', p.angulo_vertical) - CHARINDEX('''', p.angulo_vertical) - 1) AS FLOAT) / 3600.0
                    ELSE
                        CAST(p.angulo_vertical AS FLOAT)
                END) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma)
            ) AS angulo_vertical, 
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DA Vertical: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoFechasAVA(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (CASE 
                WHEN p.angulo_vertical LIKE '%°%' AND p.angulo_vertical LIKE '%''%' AND p.angulo_vertical LIKE '%"%' THEN
                    CAST(SUBSTRING(p.angulo_vertical, 1, CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) +
                    CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('°', p.angulo_vertical) + 1, CHARINDEX('''', p.angulo_vertical) - CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) / 60.0 +
                    CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('''', p.angulo_vertical) + 1, CHARINDEX('"', p.angulo_vertical) - CHARINDEX('''', p.angulo_vertical) - 1) AS FLOAT) / 3600.0
                ELSE
                    CAST(p.angulo_vertical AS FLOAT)
            END 
            - 
            FIRST_VALUE(
                CASE 
                    WHEN p.angulo_vertical LIKE '%°%' AND p.angulo_vertical LIKE '%''%' AND p.angulo_vertical LIKE '%"%' THEN
                        CAST(SUBSTRING(p.angulo_vertical, 1, CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) +
                        CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('°', p.angulo_vertical) + 1, CHARINDEX('''', p.angulo_vertical) - CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) / 60.0 +
                        CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('''', p.angulo_vertical) + 1, CHARINDEX('"', p.angulo_vertical) - CHARINDEX('''', p.angulo_vertical) - 1) AS FLOAT) / 3600.0
                    ELSE
                        CAST(p.angulo_vertical AS FLOAT)
                END) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma)
            ) AS angulo_vertical, 
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        AND p.hora_prisma BETWEEN ? AND ? 
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DA Vertical fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasAVA(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(
                    CASE 
                        WHEN p.angulo_vertical LIKE '%°%' AND p.angulo_vertical LIKE '%''%' AND p.angulo_vertical LIKE '%"%' THEN
                            CAST(SUBSTRING(p.angulo_vertical, 1, CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) +
                            CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('°', p.angulo_vertical) + 1, CHARINDEX('''', p.angulo_vertical) - CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('''', p.angulo_vertical) + 1, CHARINDEX('"', p.angulo_vertical) - CHARINDEX('''', p.angulo_vertical) - 1) AS FLOAT) / 3600.0
                        ELSE
                            CAST(p.angulo_vertical AS FLOAT)
                    END
                ) AS promedio_vertical,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (b.promedio_vertical - FIRST_VALUE(b.promedio_vertical)
                OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma)
            ) AS angulo, 
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DA Vertical: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasFechasAVA(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(
                    CASE 
                        WHEN p.angulo_vertical LIKE '%°%' AND p.angulo_vertical LIKE '%''%' AND p.angulo_vertical LIKE '%"%' THEN
                            CAST(SUBSTRING(p.angulo_vertical, 1, CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) +
                            CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('°', p.angulo_vertical) + 1, CHARINDEX('''', p.angulo_vertical) - CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('''', p.angulo_vertical) + 1, CHARINDEX('"', p.angulo_vertical) - CHARINDEX('''', p.angulo_vertical) - 1) AS FLOAT) / 3600.0
                        ELSE
                            CAST(p.angulo_vertical AS FLOAT)
                    END
                ) AS promedio_vertical,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (b.promedio_vertical - FIRST_VALUE(b.promedio_vertical) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma)) AS angulo,
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DA Vertical fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHorasAVA(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente]
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(
                    CASE 
                        WHEN p.angulo_vertical LIKE '%°%' AND p.angulo_vertical LIKE '%''%' AND p.angulo_vertical LIKE '%"%' THEN
                            CAST(SUBSTRING(p.angulo_vertical, 1, CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) +
                            CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('°', p.angulo_vertical) + 1, CHARINDEX('''', p.angulo_vertical) - CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('''', p.angulo_vertical) + 1, CHARINDEX('"', p.angulo_vertical) - CHARINDEX('''', p.angulo_vertical) - 1) AS FLOAT) / 3600.0
                        ELSE
                            CAST(p.angulo_vertical AS FLOAT)
                    END
                ) AS promedio_vertical,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (pd.promedio_vertical - FIRST_VALUE(pd.promedio_vertical) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma)) AS angulo,
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DA Vertical: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHorasFechasAVA(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(
                    CASE 
                        WHEN p.angulo_vertical LIKE '%°%' AND p.angulo_vertical LIKE '%''%' AND p.angulo_vertical LIKE '%"%' THEN
                            CAST(SUBSTRING(p.angulo_vertical, 1, CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) +
                            CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('°', p.angulo_vertical) + 1, CHARINDEX('''', p.angulo_vertical) - CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('''', p.angulo_vertical) + 1, CHARINDEX('"', p.angulo_vertical) - CHARINDEX('''', p.angulo_vertical) - 1) AS FLOAT) / 3600.0
                        ELSE
                            CAST(p.angulo_vertical AS FLOAT)
                    END
                ) AS promedio_vertical,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (pd.promedio_vertical - FIRST_VALUE(pd.promedio_vertical) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma)) AS angulo,
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DA Vertical fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
                
    @staticmethod
    def mdlCalcularDesplazamientoAVI(tabla, unidad, prismas, idcomponente):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente]
        
        # Lógica Incremental Compleja: Parseo(Actual) - Parseo(Anterior/LAG)
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(p.angulo_vertical) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                ELSE (
                    -- Parseo Valor Actual
                    (CASE 
                        WHEN p.angulo_vertical LIKE '%°%' AND p.angulo_vertical LIKE '%''%' AND p.angulo_vertical LIKE '%"%' THEN
                            CAST(SUBSTRING(p.angulo_vertical, 1, CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) +
                            CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('°', p.angulo_vertical) + 1, CHARINDEX('''', p.angulo_vertical) - CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('''', p.angulo_vertical) + 1, CHARINDEX('"', p.angulo_vertical) - CHARINDEX('''', p.angulo_vertical) - 1) AS FLOAT) / 3600.0
                        ELSE CAST(p.angulo_vertical AS FLOAT)
                    END)
                    -
                    -- Parseo Valor Anterior (LAG)
                    (CASE 
                        WHEN LAG(p.angulo_vertical) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) LIKE '%°%' 
                            AND LAG(p.angulo_vertical) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) LIKE '%''%' 
                            AND LAG(p.angulo_vertical) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) LIKE '%"%' THEN
                            CAST(SUBSTRING(LAG(p.angulo_vertical) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 1, CHARINDEX('°', LAG(p.angulo_vertical) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) - 1) AS FLOAT) +
                            CAST(SUBSTRING(LAG(p.angulo_vertical) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), CHARINDEX('°', LAG(p.angulo_vertical) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) + 1, CHARINDEX('''', LAG(p.angulo_vertical) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) - CHARINDEX('°', LAG(p.angulo_vertical) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(LAG(p.angulo_vertical) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), CHARINDEX('''', LAG(p.angulo_vertical) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) + 1, CHARINDEX('"', LAG(p.angulo_vertical) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) - CHARINDEX('''', LAG(p.angulo_vertical) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) - 1) AS FLOAT) / 3600.0
                        ELSE 
                            CAST(LAG(p.angulo_vertical) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS FLOAT)
                    END)
                )
            END AS FLOAT) AS angulo, 
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DI Vertical: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoFechasAVI(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""SELECT 
            i.id_instrumentacion, 
            p.nombre_prisma, 
            p.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(p.angulo_vertical) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                ELSE (
                    (CASE 
                        WHEN p.angulo_vertical LIKE '%°%' AND p.angulo_vertical LIKE '%''%' AND p.angulo_vertical LIKE '%"%' THEN
                            CAST(SUBSTRING(p.angulo_vertical, 1, CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) +
                            CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('°', p.angulo_vertical) + 1, CHARINDEX('''', p.angulo_vertical) - CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('''', p.angulo_vertical) + 1, CHARINDEX('"', p.angulo_vertical) - CHARINDEX('''', p.angulo_vertical) - 1) AS FLOAT) / 3600.0
                        ELSE CAST(p.angulo_vertical AS FLOAT)
                    END)
                    -
                    (CASE 
                        WHEN LAG(p.angulo_vertical) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) LIKE '%°%' 
                            AND LAG(p.angulo_vertical) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) LIKE '%''%' 
                            AND LAG(p.angulo_vertical) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) LIKE '%"%' THEN
                            CAST(SUBSTRING(LAG(p.angulo_vertical) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 1, CHARINDEX('°', LAG(p.angulo_vertical) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) - 1) AS FLOAT) +
                            CAST(SUBSTRING(LAG(p.angulo_vertical) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), CHARINDEX('°', LAG(p.angulo_vertical) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) + 1, CHARINDEX('''', LAG(p.angulo_vertical) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) - CHARINDEX('°', LAG(p.angulo_vertical) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(LAG(p.angulo_vertical) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), CHARINDEX('''', LAG(p.angulo_vertical) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) + 1, CHARINDEX('"', LAG(p.angulo_vertical) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) - CHARINDEX('''', LAG(p.angulo_vertical) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) - 1) AS FLOAT) / 3600.0
                        ELSE 
                            CAST(LAG(p.angulo_vertical) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS FLOAT)
                    END)
                )
            END AS FLOAT) AS angulo, 
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        AND p.hora_prisma BETWEEN ? AND ? 
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar DI Vertical fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasAVI(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(
                    CASE
                        WHEN p.angulo_vertical LIKE '%°%' AND p.angulo_vertical LIKE '%''%' AND p.angulo_vertical LIKE '%"%' THEN
                            CAST(SUBSTRING(p.angulo_vertical, 1, CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) +
                            CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('°', p.angulo_vertical) + 1, CHARINDEX('''', p.angulo_vertical) - CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('''', p.angulo_vertical) + 1, CHARINDEX('"', p.angulo_vertical) - CHARINDEX('''', p.angulo_vertical) - 1) AS FLOAT) / 3600.0
                        ELSE CAST(p.angulo_vertical AS FLOAT)
                    END
                ) AS promedio_vertical,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias, 
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}),
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(b.promedio_vertical) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma) IS NULL THEN 0
                ELSE (b.promedio_vertical - LAG(b.promedio_vertical) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma))
            END AS FLOAT) AS angulo, 
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DI Vertical: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoDiasFechasAVI(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""WITH fechas_inicio AS (
            SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio
            FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma
        ),
        bloques AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(
                    CASE
                        WHEN p.angulo_vertical LIKE '%°%' AND p.angulo_vertical LIKE '%''%' AND p.angulo_vertical LIKE '%"%' THEN
                            CAST(SUBSTRING(p.angulo_vertical, 1, CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) +
                            CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('°', p.angulo_vertical) + 1, CHARINDEX('''', p.angulo_vertical) - CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('''', p.angulo_vertical) + 1, CHARINDEX('"', p.angulo_vertical) - CHARINDEX('''', p.angulo_vertical) - 1) AS FLOAT) / 3600.0
                        ELSE CAST(p.angulo_vertical AS FLOAT)
                    END
                ) AS promedio_vertical,
                FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}) AS bloque_dias, 
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, f.fecha_inicio, CAST(p.hora_prisma AS DATE), 
                     FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad}), 
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.nombre_prisma, b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(b.promedio_vertical) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma) IS NULL THEN 0
                ELSE (b.promedio_vertical - LAG(b.promedio_vertical) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma))
            END AS FLOAT) AS angulo, 
            b.tipo_equipo
        FROM bloques b ORDER BY b.nombre_prisma, b.bloque_dias;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom dias DI Vertical fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHorasAVI(tabla, unidad, prismas, idcomponente, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente]
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(
                    CASE
                        WHEN p.angulo_vertical LIKE '%°%' AND p.angulo_vertical LIKE '%''%' AND p.angulo_vertical LIKE '%"%' THEN
                            CAST(SUBSTRING(p.angulo_vertical, 1, CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) +
                            CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('°', p.angulo_vertical) + 1, CHARINDEX('''', p.angulo_vertical) - CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('''', p.angulo_vertical) + 1, CHARINDEX('"', p.angulo_vertical) - CHARINDEX('''', p.angulo_vertical) - 1) AS FLOAT) / 3600.0
                        ELSE CAST(p.angulo_vertical AS FLOAT)
                    END
                ) AS promedio_vertical,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(pd.promedio_vertical) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma) IS NULL THEN 0
                ELSE (pd.promedio_vertical - LAG(pd.promedio_vertical) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma))
            END AS FLOAT) AS angulo, 
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DI Vertical: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDesplazamientoHorasFechasAVI(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        conn = None
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""WITH promedios_horas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                CAST(p.hora_prisma AS DATE) AS fecha,
                DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, 
                MAX(p.hora_prisma) AS hora_prisma,
                AVG(
                    CASE
                        WHEN p.angulo_vertical LIKE '%°%' AND p.angulo_vertical LIKE '%''%' AND p.angulo_vertical LIKE '%"%' THEN
                            CAST(SUBSTRING(p.angulo_vertical, 1, CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) +
                            CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('°', p.angulo_vertical) + 1, CHARINDEX('''', p.angulo_vertical) - CHARINDEX('°', p.angulo_vertical) - 1) AS FLOAT) / 60.0 +
                            CAST(SUBSTRING(p.angulo_vertical, CHARINDEX('''', p.angulo_vertical) + 1, CHARINDEX('"', p.angulo_vertical) - CHARINDEX('''', p.angulo_vertical) - 1) AS FLOAT) / 3600.0
                        ELSE CAST(p.angulo_vertical AS FLOAT)
                    END
                ) AS promedio_vertical,
                i.tipo_equipo
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? 
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad},
                     i.id_instrumentacion, i.tipo_equipo
        )
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.nombre_prisma, pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            CAST(CASE 
                WHEN LAG(pd.promedio_vertical) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma) IS NULL THEN 0
                ELSE (pd.promedio_vertical - LAG(pd.promedio_vertical) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma))
            END AS FLOAT) AS angulo, 
            pd.tipo_equipo
        FROM promedios_horas pd ORDER BY pd.nombre_prisma, pd.fecha, pd.bloque;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar prom horas DI Vertical fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()