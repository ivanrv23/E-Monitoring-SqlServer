from services.security.apis.conexiones.connection import Connection

class AsistenteVozModel:
    
    @staticmethod
    def mdlObtenerInformacionPrismas(tabla, prismas, idcomponente, fechaini, fechafin):
        # Generación dinámica de placeholders para cláusula IN
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        
        # T-SQL Compatible: COUNT, MIN, MAX funcionan igual. 
        # Aseguramos compatibilidad de fechas si la BD las guarda como DATETIME.
        sql = f"""SELECT p.nombre_prisma, count(*) as cantidad, min(p.hora_prisma), max(p.hora_prisma)
        FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        AND p.hora_prisma BETWEEN ? AND ? GROUP BY nombre_prisma ORDER BY p.nombre_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            
            # CRÍTICO: Convertir pyodbc.Row a tupla estándar de Python para compatibilidad con el frontend
            rows = cur.fetchall()
            result = [tuple(row) for row in rows]
            
            if result:
                return result
            else:
                return None
        except Exception as e:
            # Captura de excepción genérica para logueo o manejo superior
            print(f"Error en mdlObtenerInformacionPrismas: {str(e)}")
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlResumenVozDesplazamiento(tabla, prismas, idcomponente, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        # T-SQL Refactor:
        # 1. CAST(... AS FLOAT) dentro de POWER/SQRT para evitar retorno de tipos Decimal.
        # 2. Funciones de ventana se mantienen (LAG, FIRST_VALUE).
        sql = f"""WITH ResumenDesplazamiento AS (
            SELECT p.nombre_prisma, p.hora_prisma,
                ABS(
                    CASE
                        WHEN p.nombre_prisma <> LAG(p.nombre_prisma) OVER (ORDER BY p.nombre_prisma) THEN 0.0
                        ELSE CAST(p.distancia_prisma AS FLOAT) - CAST(FIRST_VALUE(p.distancia_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS FLOAT)
                    END
                ) AS desplazasd,
                SQRT(
                    POWER(CAST(p.este_target AS FLOAT) - CAST(FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS FLOAT), 2) +
                    POWER(CAST(p.norte_target AS FLOAT) - CAST(FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS FLOAT), 2) +
                    POWER(CAST(p.elevacion_target AS FLOAT) - CAST(FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS FLOAT), 2)
                ) AS desplaza3d,
                SQRT(
                    POWER(CAST(p.este_target AS FLOAT) - CAST(FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS FLOAT), 2) +
                    POWER(CAST(p.norte_target AS FLOAT) - CAST(FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS FLOAT), 2)
                ) AS desplaza2d,
                ABS(CAST(p.desplaza_longitudinal AS FLOAT)) AS desplaza_longitudinal,
                ABS(CAST(p.desplaza_transversal AS FLOAT)) AS desplaza_transversal,
                ABS(CAST(p.desplaza_altura AS FLOAT)) AS desplaza_altura,
                ABS(CAST(p.este_target AS FLOAT) - CAST(FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS FLOAT)) AS desplaza_este,
                ABS(CAST(p.norte_target AS FLOAT) - CAST(FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS FLOAT)) AS desplaza_norte,
                ABS(CAST(p.elevacion_target AS FLOAT) - CAST(FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS FLOAT)) AS desplaza_cota
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ?
        )
        SELECT nombre_prisma, MIN(hora_prisma) AS fechamin, MAX(hora_prisma) AS fechamax, MAX(desplazasd) AS desplazasd, MAX(desplaza3d) AS desplaza3d,
        MAX(desplaza2d) AS desplaza2d, MAX(desplaza_longitudinal) AS desplaza_longitudinal, MAX(desplaza_transversal) AS desplaza_transversal,
        MAX(desplaza_altura) AS desplaza_altura, MAX(desplaza_este) AS desplaza_este, MAX(desplaza_norte) AS desplaza_norte, MAX(desplaza_cota) AS desplaza_cota
        FROM ResumenDesplazamiento
        GROUP BY nombre_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            
            # CRÍTICO: Convertir a tuplas
            rows = cur.fetchall()
            result = [tuple(row) for row in rows]
            
            if result:
                return result
            else:
                return None
        except Exception as e:
            print("Error al obtener resumen voz desplazamiento: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlResumenVozVelocidad(tabla, prismas, idcomponente, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        
        # T-SQL Refactor Complejo:
        # 1. JULIANDAY(t2) - JULIANDAY(t1) -> CAST(DATEDIFF(SECOND, t1, t2) AS FLOAT) / 86400.0
        # 2. CAST(... AS NUMERIC) -> CAST(... AS FLOAT) para asegurar tipos compatibles con Python float.
        # 3. Reemplazo de lógica de COALESCE/LAG para evitar división por cero en T-SQL.
        sql = f"""WITH ResumenVelocidad AS (
            SELECT p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, p.elevacion_target,
                -- VI3D
                CASE 
                    WHEN LAG(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0.0
                    WHEN DATEDIFF(SECOND, LAG(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) = 0 THEN 0.0
                    ELSE ABS(SQRT(
                        POWER(CAST(p.este_target AS FLOAT) - CAST(LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS FLOAT), 2) +
                        POWER(CAST(p.norte_target AS FLOAT) - CAST(LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS FLOAT), 2) +
                        POWER(CAST(p.elevacion_target AS FLOAT) - CAST(LAG(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS FLOAT), 2)
                    ) / (CAST(DATEDIFF(SECOND, LAG(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0))
                END AS VI3D,
                -- VA3D
                CASE 
                    WHEN DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) = 0 THEN 0.0
                    ELSE ABS(SQRT(
                        POWER(CAST(p.este_target AS FLOAT) - CAST(FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS FLOAT), 2) +
                        POWER(CAST(p.norte_target AS FLOAT) - CAST(FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS FLOAT), 2) +
                        POWER(CAST(p.elevacion_target AS FLOAT) - CAST(FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS FLOAT), 2)
                    ) / (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0))
                END AS VA3D,
                -- VI2D
                CASE 
                    WHEN LAG(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0.0
                    WHEN DATEDIFF(SECOND, LAG(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) = 0 THEN 0.0
                    ELSE ABS(SQRT(
                        POWER(CAST(p.este_target AS FLOAT) - CAST(LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS FLOAT), 2) +
                        POWER(CAST(p.norte_target AS FLOAT) - CAST(LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS FLOAT), 2)
                    ) / (CAST(DATEDIFF(SECOND, LAG(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0))
                END AS VI2D,
                -- VA2D
                CASE 
                    WHEN DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) = 0 THEN 0.0
                    ELSE ABS(SQRT(
                        POWER(CAST(p.este_target AS FLOAT) - CAST(FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS FLOAT), 2) +
                        POWER(CAST(p.norte_target AS FLOAT) - CAST(FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS FLOAT), 2)
                    ) / (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0))
                END AS VA2D,
                -- VISD
                CASE
                    WHEN CAST(DATEDIFF(SECOND, ISNULL(LAG(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma), p.hora_prisma) AS FLOAT) = 0 THEN 0.0
                    ELSE ABS((
                        (CAST(p.distancia_prisma AS FLOAT) - CAST(LAG(p.distancia_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS FLOAT))
                    ) / (CAST(DATEDIFF(SECOND, ISNULL(LAG(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0))
                END AS VISD,
                -- VASD
                CASE
                    WHEN CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) = 0 THEN 0.0
                    ELSE ABS((
                        (CAST(p.distancia_prisma AS FLOAT) - CAST(FIRST_VALUE(p.distancia_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS FLOAT))
                    ) / (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0))
                END AS VASD
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ?
        )
        SELECT nombre_prisma, MIN(hora_prisma) AS fechamin, MAX(hora_prisma) AS fechamax, MAX(VI3D) AS VI3D, MAX(VA3D) AS VA3D,
        MAX(VI2D) AS VI2D, MAX(VA2D) AS VA2D, MAX(VISD) AS VISD, MAX(VASD) AS VASD
        FROM ResumenVelocidad
        GROUP BY nombre_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            
            # CRÍTICO: Convertir a tuplas
            rows = cur.fetchall()
            result = [tuple(row) for row in rows]
            
            if result:
                return result
            else:
                return None
        except Exception as e:
            print("Error al obtener resumen voz velocidad: " + str(e))
            return None
        finally:
            if conn:
                conn.close()