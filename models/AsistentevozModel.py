from services.security.apis.conexiones.connection import Connection

class AsistenteVozModel:
    
    def mdlObtenerInformacionPrismas(tabla, prismas, idcomponente, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        sql = f"""SELECT p.nombre_prisma, COUNT(*) AS cantidad, MIN(p.hora_prisma), MAX(p.hora_prisma)
        FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        AND p.hora_prisma BETWEEN ? AND ? GROUP BY p.nombre_prisma ORDER BY p.nombre_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener información prismas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlResumenVozDesplazamiento(tabla, prismas, idcomponente, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        sql = f"""WITH ResumenDesplazamiento AS (
            SELECT p.nombre_prisma, p.hora_prisma,
                ABS(
                    CASE
                        WHEN p.nombre_prisma <> LAG(p.nombre_prisma) OVER (ORDER BY p.nombre_prisma) THEN 0
                        ELSE p.distancia_prisma - FIRST_VALUE(p.distancia_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma)
                    END
                ) AS desplazasd,
                SQRT(
                    POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma), 2) +
                    POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma), 2) +
                    POWER(p.elevacion_target - FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma), 2)
                ) AS desplaza3d,
                SQRT(
                    POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma), 2) +
                    POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma), 2)
                ) AS desplaza2d,
                ABS(p.desplaza_longitudinal) AS desplaza_longitudinal,
                ABS(p.desplaza_transversal) AS desplaza_transversal,
                ABS(p.desplaza_altura) AS desplaza_altura,
                ABS(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma)) AS desplaza_este,
                ABS(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma)) AS desplaza_norte,
                ABS(p.elevacion_target - FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma)) AS desplaza_cota
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ?
        )
        SELECT nombre_prisma, MIN(hora_prisma) AS fechamin, MAX(hora_prisma) AS fechamax, MAX(desplazasd) AS desplazasd, MAX(desplaza3d) AS desplaza3d,
        MAX(desplaza2d) AS desplaza2d, MAX(desplaza_longitudinal) AS desplaza_longitudinal, MAX(desplaza_transversal) AS desplaza_transversal,
        MAX(desplaza_altura) AS desplaza_altura, MAX(desplaza_este) AS desplaza_este, MAX(desplaza_norte) AS desplaza_norte, MAX(desplaza_cota) AS desplaza_cota
        FROM ResumenDesplazamiento
        GROUP BY nombre_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener resumen voz desplazamiento: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlResumenVozVelocidad(tabla, prismas, idcomponente, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        sql = f"""WITH ResumenVelocidad AS (
            SELECT p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, p.elevacion_target,
                CASE 
                    WHEN LAG(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma) IS NULL THEN 0
                    WHEN DATEDIFF(SECOND, LAG(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) = 0 THEN 0
                    ELSE ABS(SQRT(
                        POWER(p.este_target - LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2) +
                        POWER(p.norte_target - LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2) +
                        POWER(p.elevacion_target - LAG(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2)
                    ) / (CAST(DATEDIFF(SECOND, LAG(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0))
                END AS VI3D,
                CASE 
                    WHEN DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) = 0 THEN 0
                    ELSE ABS(SQRT(
                        POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2) +
                        POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2) +
                        POWER(p.elevacion_target - FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2)
                    ) / (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0))
                END AS VA3D,
                CASE 
                    WHEN LAG(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma) IS NULL THEN 0
                    WHEN DATEDIFF(SECOND, LAG(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) = 0 THEN 0
                    ELSE ABS(SQRT(
                        POWER(p.este_target - LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2) +
                        POWER(p.norte_target - LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2)
                    ) / (CAST(DATEDIFF(SECOND, LAG(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0))
                END AS VI2D,
                CASE 
                    WHEN DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) = 0 THEN 0
                    ELSE ABS(SQRT(
                        POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2) +
                        POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2)
                    ) / (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0))
                END AS VA2D,
                CASE
                    WHEN LAG(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma) IS NULL THEN 0
                    WHEN DATEDIFF(SECOND, LAG(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) = 0 THEN 0
                    ELSE ABS((
                        p.distancia_prisma - LAG(p.distancia_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma)
                    ) / (CAST(DATEDIFF(SECOND, LAG(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0))
                END AS VISD,
                CASE
                    WHEN DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) = 0 THEN 0
                    ELSE ABS((
                        p.distancia_prisma - FIRST_VALUE(p.distancia_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma)
                    ) / (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0))
                END AS VASD
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ?
        )
        SELECT nombre_prisma, MIN(hora_prisma) AS fechamin, MAX(hora_prisma) AS fechamax, MAX(VI3D) AS VI3D, MAX(VA3D) AS VA3D,
        MAX(VI2D) AS VI2D, MAX(VA2D) AS VA2D, MAX(VISD) AS VISD, MAX(VASD) AS VASD
        FROM ResumenVelocidad
        GROUP BY nombre_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener resumen voz velocidad: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    