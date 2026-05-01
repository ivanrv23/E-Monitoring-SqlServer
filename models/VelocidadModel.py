from services.security.apis.conexiones.connection import Connection

class VelocidadModel:
    @staticmethod
    def mdlCalcularVelocidadVISD(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        if not prismas: return None
        conn = None
        try:
            placeholders = ', '.join(['?' for _ in prismas])
            sql = f"""WITH datos_filtrados AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma, p.distancia_prisma, i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND i.id_componente = ? AND p.nombre_prisma IN ({placeholders})
            AND p.hora_prisma <= ?
            UNION
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma, p.distancia_prisma, i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND i.id_componente = ? AND p.nombre_prisma IN ({placeholders})
            AND p.hora_prisma BETWEEN ? AND ?
            ),
            velocidad AS (
            SELECT id_instrumentacion, nombre_prisma, hora_prisma, tipo_equipo,
            CAST(DATEDIFF(SECOND, COALESCE(LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma), hora_prisma) AS FLOAT) / 86400.0 AS dif_fechas,
            (distancia_prisma - COALESCE(LAG(distancia_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), distancia_prisma)) * ? AS dif_sd
            FROM datos_filtrados
            ),
            calculo_final AS (
            SELECT id_instrumentacion, nombre_prisma, hora_prisma, tipo_equipo,
            COALESCE(dif_sd / NULLIF(dif_fechas, 0), 0) AS VISD
            FROM velocidad
            )
            SELECT cf.id_instrumentacion, cf.nombre_prisma, cf.hora_prisma AS FECHAS, 0 AS DIAS, 0 AS HORAS, cf.VISD, cf.tipo_equipo
            FROM calculo_final cf WHERE cf.hora_prisma BETWEEN ? AND ?
            ORDER BY cf.nombre_prisma, cf.hora_prisma;"""
            params = [idcomponente] + prismas + [fechafin] + [idcomponente] + prismas + [fechaini, fechafin] + [unidad] + [fechaini, fechafin]
            conn = Connection.connectionDB(); cur = conn.cursor(); cur.arraysize = 1000
            cur.execute(sql, params); rows = cur.fetchall(); results = list(map(tuple, rows))
            return results if results else None
        except Exception as e:
            print("Error al consultar visd: " + str(e)); return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlCalcularVelocidadFechasVISD(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente] + [fechaini] + [fechafin]
        sql = f"""WITH CD AS (
        SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma,
        CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0 AS dias,
        CAST(DATEDIFF(SECOND, COALESCE(LAG(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0 AS dif_fechas,
        (p.distancia_prisma - FIRST_VALUE(CAST(p.distancia_prisma AS FLOAT)) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * ? AS SD, i.tipo_equipo
        FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ? AND p.hora_prisma BETWEEN ? AND ?
        ),
        CD_Dif AS (
        SELECT id_instrumentacion, nombre_prisma, hora_prisma, dias, dif_fechas, SD,
        SD - COALESCE(LAG(SD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), SD) AS dif_sd,
        COALESCE((SD - COALESCE(LAG(SD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), SD)) / NULLIF(dif_fechas, 0), 0) AS VISD, tipo_equipo
        FROM CD
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS, VISD, tipo_equipo
        FROM CD_Dif ORDER BY nombre_prisma, hora_prisma;"""
        conn = None
        try:
            conn = Connection.connectionDB(); cur = conn.cursor(); cur.arraysize = 1000
            cur.execute(sql, params); rows = cur.fetchall(); results = list(map(tuple, rows))
            return results if results else None
        except Exception as e:
            print("Error al consultar visd fechas: " + str(e)); return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlCalcularVelocidadDiasVISD(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        if not prismas: return None
        conn = None
        try:
            placeholders = ', '.join(['?' for _ in prismas])
            sql = f"""WITH datos_para_promedio AS (
            SELECT p.nombre_prisma, p.hora_prisma, p.distancia_prisma, i.id_instrumentacion, i.tipo_equipo
            FROM {tabla} p JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.nombre_prisma IN ({placeholders}) AND i.id_componente = ? AND p.hora_prisma BETWEEN ? AND ?
            UNION ALL
            SELECT p.nombre_prisma, p.hora_prisma, p.distancia_prisma, i.id_instrumentacion, i.tipo_equipo
            FROM {tabla} p JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND CAST(p.hora_prisma AS DATE) = (SELECT MAX(CAST(p_inner.hora_prisma AS DATE)) FROM {tabla} p_inner WHERE p_inner.nombre_prisma = p.nombre_prisma AND p_inner.hora_prisma < ?)
            ),
            bloques AS (
            SELECT nombre_prisma, CAST(hora_prisma AS DATE) as fecha_bloque, MAX(hora_prisma) AS hora_prisma, AVG(CAST(distancia_prisma AS FLOAT)) AS promedio_distancia, MAX(id_instrumentacion) AS id_instrumentacion, MAX(tipo_equipo) AS tipo_equipo
            FROM datos_para_promedio GROUP BY nombre_prisma, CAST(hora_prisma AS DATE)
            ),
            velocidad AS (
            SELECT *,
            CAST(DATEDIFF(SECOND, COALESCE(LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma), hora_prisma) AS FLOAT) / 86400.0 AS dif_fechas,
            (promedio_distancia - COALESCE(LAG(promedio_distancia) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), promedio_distancia)) * ? AS dif_sd
            FROM bloques
            )
            SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, 0 AS DIAS, 0 AS HORAS,
            CASE WHEN dif_fechas = 0 THEN 0 ELSE dif_sd / NULLIF(dif_fechas, 0) END AS VISD, tipo_equipo
            FROM velocidad WHERE hora_prisma BETWEEN ? AND ? ORDER BY nombre_prisma, hora_prisma;"""
            params = prismas + [idcomponente, fechaini, fechafin] + prismas + [idcomponente, fechaini] + [unidad, fechaini, fechafin]
            conn = Connection.connectionDB(); cur = conn.cursor(); cur.arraysize = 1000
            cur.execute(sql, params); rows = cur.fetchall(); results = list(map(tuple, rows))
            return results if results else None
        except Exception as e:
            print("Error al consultar prom dias visd: " + str(e)); return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlCalcularVelocidadDiasFechasVISD(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        sql = f"""WITH fechas_inicio AS (
        SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1 GROUP BY p.nombre_prisma
        ),
        bloques AS (
        SELECT i.id_instrumentacion, p.nombre_prisma, CAST(p.hora_prisma AS DATE) AS fecha, MAX(p.hora_prisma) AS hora_prisma, AVG(CAST(p.distancia_prisma AS FLOAT)) AS promedio_distancia,
        FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad} ) AS bloque_dias, i.tipo_equipo
        FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ? AND p.hora_prisma BETWEEN ? AND ?
        GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), f.fecha_inicio, i.id_instrumentacion, i.tipo_equipo
        ),
        velocidad AS (
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
        CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0 AS dias,
        CAST(DATEDIFF(SECOND, COALESCE(LAG(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0 AS dif_fechas,
        (b.promedio_distancia - FIRST_VALUE(CAST(b.promedio_distancia AS FLOAT)) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma)) * ? AS SD, b.tipo_equipo, b.bloque_dias
        FROM bloques b
        ),
        CD_Dif AS (
        SELECT id_instrumentacion, nombre_prisma, hora_prisma, dias, dif_fechas, SD,
        SD - COALESCE(LAG(SD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), SD) AS dif_sd,
        COALESCE((SD - COALESCE(LAG(SD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), SD)) / NULLIF(dif_fechas, 0), 0) AS VISD, tipo_equipo
        FROM velocidad
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS, VISD, tipo_equipo FROM CD_Dif ORDER BY nombre_prisma, hora_prisma;"""
        conn = None
        try:
            conn = Connection.connectionDB(); cur = conn.cursor(); cur.arraysize = 1000
            cur.execute(sql, params); rows = cur.fetchall(); results = list(map(tuple, rows))
            return results if results else None
        except Exception as e:
            print("Error al consultar prom dias visd fechas: " + str(e)); return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlCalcularVelocidadHorasVISD(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        if not prismas: return None
        conn = None
        try:
            placeholders = ', '.join(['?' for _ in prismas])
            sql = f"""WITH datos_para_promedio AS (
            SELECT p.nombre_prisma, p.hora_prisma, p.distancia_prisma, i.id_instrumentacion, i.tipo_equipo FROM {tabla} p JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.nombre_prisma IN ({placeholders}) AND i.id_componente = ? AND p.hora_prisma BETWEEN ? AND ?
            UNION ALL
            SELECT p.nombre_prisma, p.hora_prisma, p.distancia_prisma, i.id_instrumentacion, i.tipo_equipo FROM {tabla} p JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma IN (SELECT TOP 1 WITH TIES p_inner.hora_prisma FROM {tabla} p_inner WHERE p_inner.nombre_prisma = p.nombre_prisma AND p_inner.hora_prisma < ? ORDER BY p_inner.hora_prisma DESC)
            ),
            bloques AS (
            SELECT nombre_prisma, MAX(hora_prisma) AS hora_prisma, AVG(CAST(distancia_prisma AS FLOAT)) AS promedio_distancia, MAX(id_instrumentacion) AS id_instrumentacion, MAX(tipo_equipo) AS tipo_equipo
            FROM datos_para_promedio GROUP BY nombre_prisma, CAST(hora_prisma AS DATE), DATEPART(HOUR, hora_prisma) / {cantidad}
            ),
            velocidad AS (
            SELECT *,
            CAST(DATEDIFF(SECOND, COALESCE(LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma), hora_prisma) AS FLOAT) / 86400.0 AS dif_fechas,
            (promedio_distancia - COALESCE(LAG(promedio_distancia) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), promedio_distancia)) * ? AS dif_sd
            FROM bloques
            )
            SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, 0 AS DIAS, 0 AS HORAS,
            CASE WHEN dif_fechas = 0 THEN 0 ELSE dif_sd / NULLIF(dif_fechas, 0) END AS VISD, tipo_equipo
            FROM velocidad WHERE hora_prisma BETWEEN ? AND ? ORDER BY nombre_prisma, hora_prisma;"""
            params = prismas + [idcomponente, fechaini, fechafin] + prismas + [idcomponente, fechaini] + [unidad, fechaini, fechafin]
            conn = Connection.connectionDB(); cur = conn.cursor(); cur.arraysize = 1000
            cur.execute(sql, params); rows = cur.fetchall(); results = list(map(tuple, rows))
            return results if results else None
        except Exception as e:
            print("Error al consultar prom horas visd: " + str(e)); return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlCalcularVelocidadHorasFechasVISD(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        sql = f"""WITH promedios_horas AS (
        SELECT i.id_instrumentacion, p.nombre_prisma, CAST(p.hora_prisma AS DATE) AS fecha, DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, MAX(p.hora_prisma) AS hora_prisma, AVG(CAST(p.distancia_prisma AS FLOAT)) AS promedio_distancia, i.tipo_equipo
        FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ? AND p.hora_prisma BETWEEN ? AND ?
        GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad}, i.id_instrumentacion, i.tipo_equipo
        ),
        velocidad AS (
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
        CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0 AS dias,
        CAST(DATEDIFF(SECOND, COALESCE(LAG(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0 AS dif_fechas,
        (pd.promedio_distancia - FIRST_VALUE(CAST(pd.promedio_distancia AS FLOAT)) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma)) * ? AS SD, pd.tipo_equipo, pd.fecha, pd.bloque
        FROM promedios_horas pd
        ),
        CD_Dif AS (
        SELECT id_instrumentacion, nombre_prisma, hora_prisma, dias, dif_fechas, SD,
        SD - COALESCE(LAG(SD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), SD) AS dif_sd,
        COALESCE((SD - COALESCE(LAG(SD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), SD)) / NULLIF(dif_fechas, 0), 0) AS VISD, tipo_equipo
        FROM velocidad
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS, VISD, tipo_equipo FROM CD_Dif ORDER BY nombre_prisma, hora_prisma;"""
        conn = None
        try:
            conn = Connection.connectionDB(); cur = conn.cursor(); cur.arraysize = 1000
            cur.execute(sql, params); rows = cur.fetchall(); results = list(map(tuple, rows))
            return results if results else None
        except Exception as e:
            print("Error al consultar prom horas visd fechas: " + str(e)); return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlCalcularVelocidadVASD(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        if not prismas: return None
        conn = None
        try:
            placeholders = ', '.join(['?' for _ in prismas])
            sql = f"""WITH ValoresCero AS (
            SELECT p_cte.nombre_prisma, p_cte.distancia_prisma AS valor_cero, p_cte.hora_prisma AS hora_cero
            FROM (SELECT nombre_prisma, distancia_prisma, hora_prisma, ROW_NUMBER() OVER(PARTITION BY nombre_prisma ORDER BY hora_prisma ASC) as rn FROM {tabla} WHERE nombre_prisma IN ({placeholders}) AND state_prisma = 1 AND estado_prisma = 1) p_cte
            WHERE p_cte.rn = 1
            )
            SELECT i.id_instrumentacion, datos.nombre_prisma, datos.hora_prisma AS FECHAS,
            (CAST(DATEDIFF(SECOND, vc.hora_cero, datos.hora_prisma) AS FLOAT) / 86400.0) AS DIAS,
            (CAST(DATEDIFF(SECOND, vc.hora_cero, datos.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS HORAS,
            CASE WHEN (CAST(DATEDIFF(SECOND, vc.hora_cero, datos.hora_prisma) AS FLOAT) / 86400.0) = 0 THEN 0
            ELSE ((datos.distancia_prisma - vc.valor_cero) * ?) / NULLIF((CAST(DATEDIFF(SECOND, vc.hora_cero, datos.hora_prisma) AS FLOAT) / 86400.0), 0) END AS VASD, i.tipo_equipo
            FROM {tabla} datos INNER JOIN instrumentacion i ON datos.nombre_prisma = i.nombre_equipo INNER JOIN ValoresCero vc ON datos.nombre_prisma = vc.nombre_prisma
            WHERE datos.state_prisma = 1 AND datos.estado_prisma = 1 AND i.id_componente = ? AND datos.hora_prisma BETWEEN ? AND ?
            ORDER BY datos.nombre_prisma, datos.hora_prisma;"""
            params = prismas + [unidad, idcomponente, fechaini, fechafin]
            conn = Connection.connectionDB(); cur = conn.cursor(); cur.arraysize = 1000
            cur.execute(sql, params); rows = cur.fetchall(); results = list(map(tuple, rows))
            return results if results else None
        except Exception as e:
            print("Error al consultar vasd: " + str(e)); return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlCalcularVelocidadFechasVASD(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente] + [fechaini] + [fechafin]
        sql = f"""WITH CD AS (
        SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma,
        CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0 AS dif_fechas,
        (p.distancia_prisma - FIRST_VALUE(CAST(p.distancia_prisma AS FLOAT)) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * ? AS SD, i.tipo_equipo
        FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ? AND p.hora_prisma BETWEEN ? AND ?
        ),
        CD_Dif AS (
        SELECT id_instrumentacion, nombre_prisma, hora_prisma, dif_fechas, SD,
        SD - FIRST_VALUE(SD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) AS dif_sd,
        COALESCE((SD - FIRST_VALUE(SD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma)) / NULLIF(dif_fechas, 0), 0) AS VASD, tipo_equipo
        FROM CD
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dif_fechas AS DIAS, dif_fechas * 24.0 AS HORAS, VASD, tipo_equipo FROM CD_Dif ORDER BY nombre_prisma, hora_prisma;"""
        conn = None
        try:
            conn = Connection.connectionDB(); cur = conn.cursor(); cur.arraysize = 1000
            cur.execute(sql, params); rows = cur.fetchall(); results = list(map(tuple, rows))
            return results if results else None
        except Exception as e:
            print("Error al consultar vasd fechas: " + str(e)); return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlCalcularVelocidadDiasVASD(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        if not prismas: return None
        conn = None
        try:
            placeholders = ', '.join(['?' for _ in prismas])
            sql = f"""WITH PrimerDia AS (
            SELECT nombre_prisma, MIN(CAST(hora_prisma AS DATE)) as fecha_cero FROM {tabla} WHERE nombre_prisma IN ({placeholders}) AND state_prisma = 1 AND estado_prisma = 1 GROUP BY nombre_prisma
            ),
            ValoresCero AS (
            SELECT p.nombre_prisma, MAX(p.hora_prisma) as hora_cero, AVG(CAST(p.distancia_prisma AS FLOAT)) as valor_cero
            FROM {tabla} p JOIN PrimerDia pd ON p.nombre_prisma = pd.nombre_prisma AND CAST(p.hora_prisma AS DATE) = pd.fecha_cero WHERE p.state_prisma = 1 AND p.estado_prisma = 1 GROUP BY p.nombre_prisma, pd.fecha_cero
            ),
            BloquesEnRango AS (
            SELECT p.nombre_prisma, MAX(p.hora_prisma) as hora_bloque, AVG(CAST(p.distancia_prisma AS FLOAT)) as valor_bloque, MAX(i.id_instrumentacion) as id_instrumentacion, MAX(i.tipo_equipo) as tipo_equipo
            FROM {tabla} p JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.nombre_prisma IN ({placeholders}) AND i.id_componente = ? AND p.hora_prisma BETWEEN ? AND ? AND p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE)
            )
            SELECT br.id_instrumentacion, br.nombre_prisma, br.hora_bloque AS FECHAS,
            CAST(DATEDIFF(SECOND, vc.hora_cero, br.hora_bloque) AS FLOAT) / 86400.0 AS DIAS,
            (CAST(DATEDIFF(SECOND, vc.hora_cero, br.hora_bloque) AS FLOAT) / 86400.0) * 24.0 AS HORAS,
            CASE WHEN (CAST(DATEDIFF(SECOND, vc.hora_cero, br.hora_bloque) AS FLOAT) / 86400.0) = 0 THEN 0
            ELSE ((br.valor_bloque - vc.valor_cero) * ?) / NULLIF((CAST(DATEDIFF(SECOND, vc.hora_cero, br.hora_bloque) AS FLOAT) / 86400.0), 0) END AS VASD, br.tipo_equipo
            FROM BloquesEnRango br JOIN ValoresCero vc ON br.nombre_prisma = vc.nombre_prisma ORDER BY br.nombre_prisma, br.hora_bloque;"""
            params = prismas + prismas + [idcomponente, fechaini, fechafin, unidad]
            conn = Connection.connectionDB(); cur = conn.cursor(); cur.arraysize = 1000
            cur.execute(sql, params); rows = cur.fetchall(); results = list(map(tuple, rows))
            return results if results else None
        except Exception as e:
            print("Error al consultar prom dias vasd: " + str(e)); return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlCalcularVelocidadDiasFechasVASD(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        sql = f"""WITH fechas_inicio AS (
        SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1 GROUP BY p.nombre_prisma
        ),
        bloques AS (
        SELECT i.id_instrumentacion, p.nombre_prisma, CAST(p.hora_prisma AS DATE) AS fecha, MAX(p.hora_prisma) AS hora_prisma, AVG(CAST(p.distancia_prisma AS FLOAT)) AS promedio_distancia,
        FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad} ) AS bloque_dias, i.tipo_equipo
        FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ? AND p.hora_prisma BETWEEN ? AND ?
        GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), f.fecha_inicio, i.id_instrumentacion, i.tipo_equipo
        ),
        velocidad AS (
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma,
        CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0 AS dif_fechas,
        (b.promedio_distancia - FIRST_VALUE(CAST(b.promedio_distancia AS FLOAT)) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma)) * ? AS SD, b.tipo_equipo, b.bloque_dias
        FROM bloques b
        ),
        CD_Dif AS (
        SELECT id_instrumentacion, nombre_prisma, hora_prisma, dif_fechas, SD,
        SD - FIRST_VALUE(SD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) AS dif_sd,
        COALESCE((SD - FIRST_VALUE(SD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma)) / NULLIF(dif_fechas, 0), 0) AS VASD, tipo_equipo
        FROM velocidad
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dif_fechas AS DIAS, dif_fechas * 24.0 AS HORAS, VASD, tipo_equipo FROM CD_Dif ORDER BY nombre_prisma, hora_prisma;"""
        conn = None
        try:
            conn = Connection.connectionDB(); cur = conn.cursor(); cur.arraysize = 1000
            cur.execute(sql, params); rows = cur.fetchall(); results = list(map(tuple, rows))
            return results if results else None
        except Exception as e:
            print("Error al consultar prom dias vasd fechas: " + str(e)); return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlCalcularVelocidadHorasVASD(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        if not prismas: return None
        conn = None
        try:
            placeholders = ', '.join(['?' for _ in prismas])
            sql = f"""WITH PrimerBloque AS (
            SELECT nombre_prisma, MIN(hora_prisma) as hora_cero_aprox FROM {tabla} WHERE nombre_prisma IN ({placeholders}) AND state_prisma = 1 AND estado_prisma = 1 GROUP BY nombre_prisma
            ),
            ValoresCero AS (
            SELECT p.nombre_prisma, MAX(p.hora_prisma) as hora_cero, AVG(CAST(p.distancia_prisma AS FLOAT)) as valor_cero FROM {tabla} p JOIN PrimerBloque pb ON p.nombre_prisma = pb.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND CAST(p.hora_prisma AS DATE) = CAST(pb.hora_cero_aprox AS DATE) AND DATEPART(HOUR, p.hora_prisma) / {cantidad} = DATEPART(HOUR, pb.hora_cero_aprox) / {cantidad} GROUP BY p.nombre_prisma
            ),
            BloquesEnRango AS (
            SELECT p.nombre_prisma, MAX(p.hora_prisma) as hora_bloque, AVG(CAST(p.distancia_prisma AS FLOAT)) as valor_bloque, MAX(i.id_instrumentacion) as id_instrumentacion, MAX(i.tipo_equipo) as tipo_equipo
            FROM {tabla} p JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.nombre_prisma IN ({placeholders}) AND i.id_componente = ? AND p.hora_prisma BETWEEN ? AND ? AND p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad}
            )
            SELECT br.id_instrumentacion, br.nombre_prisma, br.hora_bloque AS FECHAS,
            CAST(DATEDIFF(SECOND, vc.hora_cero, br.hora_bloque) AS FLOAT) / 86400.0 AS DIAS,
            (CAST(DATEDIFF(SECOND, vc.hora_cero, br.hora_bloque) AS FLOAT) / 86400.0) * 24.0 AS HORAS,
            CASE WHEN (CAST(DATEDIFF(SECOND, vc.hora_cero, br.hora_bloque) AS FLOAT) / 86400.0) = 0 THEN 0
            ELSE ((br.valor_bloque - vc.valor_cero) * ?) / NULLIF((CAST(DATEDIFF(SECOND, vc.hora_cero, br.hora_bloque) AS FLOAT) / 86400.0), 0) END AS VASD, br.tipo_equipo
            FROM BloquesEnRango br JOIN ValoresCero vc ON br.nombre_prisma = vc.nombre_prisma ORDER BY br.nombre_prisma, br.hora_bloque;"""
            params = prismas + prismas + [idcomponente, fechaini, fechafin, unidad]
            conn = Connection.connectionDB(); cur = conn.cursor(); cur.arraysize = 1000
            cur.execute(sql, params); rows = cur.fetchall(); results = list(map(tuple, rows))
            return results if results else None
        except Exception as e:
            print("Error al consultar prom horas vasd: " + str(e)); return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlCalcularVelocidadHorasFechasVASD(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        sql = f"""WITH promedios_horas AS (
        SELECT i.id_instrumentacion, p.nombre_prisma, CAST(p.hora_prisma AS DATE) AS fecha, DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, MAX(p.hora_prisma) AS hora_prisma, AVG(CAST(p.distancia_prisma AS FLOAT)) AS promedio_distancia, i.tipo_equipo
        FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ? AND p.hora_prisma BETWEEN ? AND ?
        GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad}, i.id_instrumentacion, i.tipo_equipo
        ),
        velocidad AS (
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma,
        CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0 AS dif_fechas,
        (pd.promedio_distancia - FIRST_VALUE(CAST(pd.promedio_distancia AS FLOAT)) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma)) * ? AS SD, pd.tipo_equipo, pd.fecha, pd.bloque
        FROM promedios_horas pd
        ),
        CD_Dif AS (
        SELECT id_instrumentacion, nombre_prisma, hora_prisma, dif_fechas, SD,
        SD - FIRST_VALUE(SD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) AS dif_sd,
        COALESCE((SD - FIRST_VALUE(SD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma)) / NULLIF(dif_fechas, 0), 0) AS VASD, tipo_equipo
        FROM velocidad
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dif_fechas AS DIAS, dif_fechas * 24.0 AS HORAS, VASD, tipo_equipo FROM CD_Dif ORDER BY nombre_prisma, hora_prisma;"""
        conn = None
        try:
            conn = Connection.connectionDB(); cur = conn.cursor(); cur.arraysize = 1000
            cur.execute(sql, params); rows = cur.fetchall(); results = list(map(tuple, rows))
            return results if results else None
        except Exception as e:
            print("Error al consultar prom horas vasd fechas: " + str(e)); return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlCalcularVelocidadVI2D(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        if not prismas: return None
        conn = None
        try:
            placeholders = ', '.join(['?' for _ in prismas])
            sql = f"""WITH datos_filtrados AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, i.tipo_equipo FROM (
            SELECT *, ROW_NUMBER() OVER(PARTITION BY nombre_prisma ORDER BY hora_prisma DESC) as rn FROM {tabla} WHERE nombre_prisma IN ({placeholders}) AND hora_prisma < ?
            ) p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo WHERE p.rn = 1 AND i.id_componente = ?
            UNION ALL
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, i.tipo_equipo FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.nombre_prisma IN ({placeholders}) AND i.id_componente = ? AND p.hora_prisma BETWEEN ? AND ?
            ),
            PrismasCTE AS (
            SELECT id_instrumentacion, nombre_prisma, hora_prisma, tipo_equipo,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0 AS dias,
            SQRT(POWER(este_target - LAG(este_target) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), 2) + POWER(norte_target - LAG(norte_target) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), 2)) * ? AS dosD,
            CAST(DATEDIFF(SECOND, LAG(hora_prisma, 1, hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0 AS dif_dias
            FROM datos_filtrados
            )
            SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
            CASE WHEN dif_dias = 0 THEN 0 ELSE (dosD - LAG(dosD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma)) / NULLIF(dif_dias, 0) END AS VI2D, tipo_equipo
            FROM PrismasCTE WHERE hora_prisma BETWEEN ? AND ? ORDER BY nombre_prisma, hora_prisma;"""
            params = prismas + [fechaini] + [idcomponente] + prismas + [idcomponente, fechaini, fechafin] + [unidad] + [fechaini, fechafin]
            conn = Connection.connectionDB(); cur = conn.cursor(); cur.arraysize = 1000
            cur.execute(sql, params); rows = cur.fetchall(); results = list(map(tuple, rows))
            return results if results else None
        except Exception as e:
            print("Error al consultar vi2d: " + str(e)); return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlCalcularVelocidadFechasVI2D(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente] + [fechaini] + [fechafin]
        sql = f"""WITH PrismasCTE AS (
        SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target,
        CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0 AS dias,
        CASE WHEN ROW_NUMBER() OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) = 1 THEN 0 ELSE
        SQRT(POWER(p.este_target - LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) + POWER(p.norte_target - LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)) * ? END AS dosD, i.tipo_equipo
        FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ? AND p.hora_prisma BETWEEN ? AND ?
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
        CASE WHEN ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) = 1 THEN 0 ELSE
        (dosD - LAG(dosD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma)) / NULLIF((CAST(DATEDIFF(SECOND, LAG(hora_prisma, 1, hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0), 0) END AS VI2D, tipo_equipo
        FROM PrismasCTE ORDER BY nombre_prisma, hora_prisma;"""
        conn = None
        try:
            conn = Connection.connectionDB(); cur = conn.cursor(); cur.arraysize = 1000
            cur.execute(sql, params); rows = cur.fetchall(); results = list(map(tuple, rows))
            return results if results else None
        except Exception as e:
            print("Error al consultar vi2d fechas: " + str(e)); return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlCalcularVelocidadDiasVI2D(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        if not prismas: return None
        conn = None
        try:
            placeholders = ', '.join(['?' for _ in prismas])
            sql = f"""WITH datos_para_promedio AS (
            SELECT p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, i.id_instrumentacion, i.tipo_equipo FROM {tabla} p JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.nombre_prisma IN ({placeholders}) AND i.id_componente = ? AND p.hora_prisma BETWEEN ? AND ?
            UNION ALL
            SELECT p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, i.id_instrumentacion, i.tipo_equipo FROM {tabla} p JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.nombre_prisma IN ({placeholders}) AND i.id_componente = ? AND CAST(p.hora_prisma AS DATE) = (SELECT MAX(CAST(p_inner.hora_prisma AS DATE)) FROM {tabla} p_inner WHERE p_inner.nombre_prisma = p.nombre_prisma AND p_inner.hora_prisma < ?)
            ),
            bloques AS (
            SELECT nombre_prisma, MAX(hora_prisma) AS hora_prisma, AVG(CAST(este_target AS FLOAT)) AS promedio_este, AVG(CAST(norte_target AS FLOAT)) AS promedio_norte, MAX(id_instrumentacion) AS id_instrumentacion, MAX(tipo_equipo) AS tipo_equipo
            FROM datos_para_promedio GROUP BY nombre_prisma, CAST(hora_prisma AS DATE)
            ),
            velocidad AS (
            SELECT *,
            SQRT(POWER(promedio_este - LAG(promedio_este) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), 2) + POWER(promedio_norte - LAG(promedio_norte) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), 2)) * ? AS dosD,
            CAST(DATEDIFF(SECOND, LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0 AS dif_dias
            FROM bloques
            )
            SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, 0 AS DIAS, 0 AS HORAS,
            CASE WHEN dif_dias = 0 THEN 0 ELSE (dosD - LAG(dosD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma)) / NULLIF(dif_dias, 0) END AS VI2D, tipo_equipo
            FROM velocidad WHERE hora_prisma BETWEEN ? AND ? ORDER BY nombre_prisma, hora_prisma;"""
            params = prismas + [idcomponente, fechaini, fechafin] + prismas + [idcomponente, fechaini] + [unidad, fechaini, fechafin]
            conn = Connection.connectionDB(); cur = conn.cursor(); cur.arraysize = 1000
            cur.execute(sql, params); rows = cur.fetchall(); results = list(map(tuple, rows))
            return results if results else None
        except Exception as e:
            print("Error al consultar prom dias vi2d: " + str(e)); return None
        finally:
            if conn: conn.close()
            
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
        / NULLIF((CAST(DATEDIFF(SECOND, LAG(hora_prisma, 1, hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0), 0)
        END AS VI2D, tipo_equipo
        FROM velocidad
        ORDER BY nombre_prisma, hora_prisma;"""
        conn = None
        try:
            conn = Connection.connectionDB(); cur = conn.cursor(); cur.arraysize = 1000
            cur.execute(sql, params); rows = cur.fetchall(); results = list(map(tuple, rows))
            return results if results else None
        except Exception as e:
            print("Error al consultar prom dias vi2d fechas: " + str(e)); return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlCalcularVelocidadHorasVI2D(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        if not prismas: return None
        conn = None
        try:
            placeholders = ', '.join(['?' for _ in prismas])
            sql = f"""WITH datos_para_promedio AS (
            SELECT p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, i.id_instrumentacion, i.tipo_equipo FROM {tabla} p JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.nombre_prisma IN ({placeholders}) AND i.id_componente = ? AND p.hora_prisma BETWEEN ? AND ?
            UNION ALL
            SELECT p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, i.id_instrumentacion, i.tipo_equipo FROM {tabla} p JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.nombre_prisma IN ({placeholders}) AND i.id_componente = ? AND p.hora_prisma IN (SELECT TOP 1 WITH TIES p_inner.hora_prisma FROM {tabla} p_inner WHERE p_inner.nombre_prisma = p.nombre_prisma AND p_inner.hora_prisma < ? ORDER BY p_inner.hora_prisma DESC)
            ),
            bloques AS (
            SELECT nombre_prisma, MAX(hora_prisma) AS hora_prisma, AVG(CAST(este_target AS FLOAT)) AS promedio_este, AVG(CAST(norte_target AS FLOAT)) AS promedio_norte, MAX(id_instrumentacion) AS id_instrumentacion, MAX(tipo_equipo) AS tipo_equipo
            FROM datos_para_promedio GROUP BY nombre_prisma, CAST(hora_prisma AS DATE), DATEPART(HOUR, hora_prisma) / {cantidad}
            ),
            velocidad AS (
            SELECT *, SQRT(POWER(promedio_este - LAG(promedio_este) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), 2) + POWER(promedio_norte - LAG(promedio_norte) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), 2)) * ? AS dosD,
            CAST(DATEDIFF(SECOND, LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0 AS dif_dias FROM bloques
            )
            SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, 0 AS DIAS, 0 AS HORAS,
            CASE WHEN dif_dias = 0 THEN 0 ELSE (dosD - LAG(dosD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma)) / NULLIF(dif_dias, 0) END AS VI2D, tipo_equipo
            FROM velocidad WHERE hora_prisma BETWEEN ? AND ? ORDER BY nombre_prisma, hora_prisma;"""
            params = prismas + [idcomponente, fechaini, fechafin] + prismas + [idcomponente, fechaini] + [unidad, fechaini, fechafin]
            conn = Connection.connectionDB(); cur = conn.cursor(); cur.arraysize = 1000
            cur.execute(sql, params); rows = cur.fetchall(); results = list(map(tuple, rows))
            return results if results else None
        except Exception as e:
            print("Error al consultar prom horas vi2d: " + str(e)); return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlCalcularVelocidadHorasFechasVI2D(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        sql = f"""WITH promedios_horas AS (
        SELECT i.id_instrumentacion, p.nombre_prisma, CAST(p.hora_prisma AS DATE) AS fecha, DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, MAX(p.hora_prisma) AS hora_prisma,
        AVG(CAST(p.este_target AS FLOAT)) AS promedio_este, AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte, i.tipo_equipo
        FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ? AND p.hora_prisma BETWEEN ? AND ?
        GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad}, i.id_instrumentacion, i.tipo_equipo
        ),
        velocidad AS (
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma, pd.promedio_este, pd.promedio_norte,
        CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0 AS dias,
        CASE WHEN ROW_NUMBER() OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma) = 1 THEN 0 ELSE
        SQRT(POWER(pd.promedio_este - LAG(pd.promedio_este) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2) + POWER(pd.promedio_norte - LAG(pd.promedio_norte) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2)) * ? END AS dosD, pd.tipo_equipo, pd.fecha, pd.bloque
        FROM promedios_horas pd
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
        CASE WHEN ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) = 1 THEN 0 ELSE
        (dosD - LAG(dosD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma)) / NULLIF((CAST(DATEDIFF(SECOND, LAG(hora_prisma, 1, hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0), 0)
        END AS VI2D, tipo_equipo FROM velocidad ORDER BY nombre_prisma, hora_prisma;"""
        conn = None
        try:
            conn = Connection.connectionDB(); cur = conn.cursor(); cur.arraysize = 1000
            cur.execute(sql, params); rows = cur.fetchall(); results = list(map(tuple, rows))
            return results if results else None
        except Exception as e:
            print("Error al consultar prom horas vi2d fechas: " + str(e)); return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlCalcularVelocidadVA2D(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        if not prismas: return None
        conn = None
        try:
            placeholders = ', '.join(['?' for _ in prismas])
            sql = f"""WITH ValoresCero AS (
            SELECT p_cte.nombre_prisma, p_cte.este_target AS este_cero, p_cte.norte_target AS norte_cero, p_cte.hora_prisma AS hora_cero
            FROM (SELECT nombre_prisma, este_target, norte_target, hora_prisma, ROW_NUMBER() OVER(PARTITION BY nombre_prisma ORDER BY hora_prisma ASC) as rn FROM {tabla} WHERE nombre_prisma IN ({placeholders}) AND state_prisma = 1 AND estado_prisma = 1) p_cte
            WHERE p_cte.rn = 1
            ),
            CalculoCTE AS (
            SELECT i.id_instrumentacion, datos.nombre_prisma, datos.hora_prisma, i.tipo_equipo,
            (CAST(DATEDIFF(SECOND, vc.hora_cero, datos.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            SQRT(POWER(datos.este_target - vc.este_cero, 2) + POWER(datos.norte_target - vc.norte_cero, 2)) * ? AS dosD
            FROM {tabla} datos INNER JOIN instrumentacion i ON datos.nombre_prisma = i.nombre_equipo INNER JOIN ValoresCero vc ON datos.nombre_prisma = vc.nombre_prisma
            WHERE datos.state_prisma = 1 AND datos.estado_prisma = 1 AND i.id_componente = ? AND datos.hora_prisma BETWEEN ? AND ?
            )
            SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
            CASE WHEN dias = 0 THEN 0 ELSE dosD / NULLIF(dias, 0) END AS VA2D, tipo_equipo FROM CalculoCTE ORDER BY nombre_prisma, hora_prisma;"""
            params = prismas + [unidad, idcomponente, fechaini, fechafin]
            conn = Connection.connectionDB(); cur = conn.cursor(); cur.arraysize = 1000
            cur.execute(sql, params); rows = cur.fetchall(); results = list(map(tuple, rows))
            return results if results else None
        except Exception as e:
            print("Error al consultar va2d: " + str(e)); return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlCalcularVelocidadFechasVA2D(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente] + [fechaini] + [fechafin]
        sql = f"""WITH PrismasCTE AS (
        SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target,
        CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0 AS dias,
        SQRT(POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) + POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)) * ? AS dosD,
        i.tipo_equipo
        FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ? AND p.hora_prisma BETWEEN ? AND ?
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
        CASE WHEN DATEDIFF(SECOND, FIRST_VALUE(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) = 0 THEN 0
        ELSE (dosD - FIRST_VALUE(dosD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma)) / NULLIF((CAST(DATEDIFF(SECOND, FIRST_VALUE(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0), 0) END AS VA2D, tipo_equipo
        FROM PrismasCTE ORDER BY nombre_prisma, hora_prisma;"""
        conn = None
        try:
            conn = Connection.connectionDB(); cur = conn.cursor(); cur.arraysize = 1000
            cur.execute(sql, params); rows = cur.fetchall(); results = list(map(tuple, rows))
            return results if results else None
        except Exception as e:
            print("Error al consultar va2d fechas: " + str(e)); return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlCalcularVelocidadDiasVA2D(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        if not prismas: return None
        conn = None
        try:
            placeholders = ', '.join(['?' for _ in prismas])
            sql = f"""WITH PrimerDia AS (
            SELECT nombre_prisma, MIN(CAST(hora_prisma AS DATE)) as fecha_cero FROM {tabla} WHERE nombre_prisma IN ({placeholders}) AND state_prisma = 1 AND estado_prisma = 1 GROUP BY nombre_prisma
            ),
            ValoresCero AS (
            SELECT p.nombre_prisma, MAX(p.hora_prisma) as hora_cero, AVG(CAST(p.este_target AS FLOAT)) as este_cero, AVG(CAST(p.norte_target AS FLOAT)) as norte_cero
            FROM {tabla} p JOIN PrimerDia pd ON p.nombre_prisma = pd.nombre_prisma AND CAST(p.hora_prisma AS DATE) = pd.fecha_cero WHERE p.state_prisma = 1 AND p.estado_prisma = 1 GROUP BY p.nombre_prisma, pd.fecha_cero
            ),
            BloquesEnRango AS (
            SELECT p.nombre_prisma, MAX(p.hora_prisma) as hora_bloque, AVG(CAST(p.este_target AS FLOAT)) as este_bloque, AVG(CAST(p.norte_target AS FLOAT)) as norte_bloque, MAX(i.id_instrumentacion) as id_instrumentacion, MAX(i.tipo_equipo) as tipo_equipo
            FROM {tabla} p JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.nombre_prisma IN ({placeholders}) AND i.id_componente = ? AND p.hora_prisma BETWEEN ? AND ? AND p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE)
            )
            SELECT br.id_instrumentacion, br.nombre_prisma, br.hora_bloque AS FECHAS,
            CAST(DATEDIFF(SECOND, vc.hora_cero, br.hora_bloque) AS FLOAT) / 86400.0 AS DIAS,
            (CAST(DATEDIFF(SECOND, vc.hora_cero, br.hora_bloque) AS FLOAT) / 86400.0) * 24.0 AS HORAS,
            CASE WHEN (CAST(DATEDIFF(SECOND, vc.hora_cero, br.hora_bloque) AS FLOAT) / 86400.0) = 0 THEN 0
            ELSE (SQRT(POWER(br.este_bloque - vc.este_cero, 2) + POWER(br.norte_bloque - vc.norte_cero, 2)) * ?) / NULLIF((CAST(DATEDIFF(SECOND, vc.hora_cero, br.hora_bloque) AS FLOAT) / 86400.0), 0) END AS VA2D, br.tipo_equipo
            FROM BloquesEnRango br JOIN ValoresCero vc ON br.nombre_prisma = vc.nombre_prisma ORDER BY br.nombre_prisma, br.hora_bloque;"""
            params = prismas + prismas + [idcomponente, fechaini, fechafin, unidad]
            conn = Connection.connectionDB(); cur = conn.cursor(); cur.arraysize = 1000
            cur.execute(sql, params); rows = cur.fetchall(); results = list(map(tuple, rows))
            return results if results else None
        except Exception as e:
            print("Error al consultar prom dias va2d: " + str(e)); return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlCalcularVelocidadDiasFechasVA2D(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        sql = f"""WITH fechas_inicio AS (
        SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1 GROUP BY p.nombre_prisma
        ),
        bloques AS (
        SELECT i.id_instrumentacion, p.nombre_prisma, CAST(p.hora_prisma AS DATE) AS fecha, MAX(p.hora_prisma) AS hora_prisma,
        AVG(CAST(p.este_target AS FLOAT)) AS promedio_este, AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte,
        FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad} ) AS bloque_dias, i.tipo_equipo
        FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ? AND p.hora_prisma BETWEEN ? AND ?
        GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), f.fecha_inicio, i.id_instrumentacion, i.tipo_equipo
        ),
        velocidad AS (
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma, b.promedio_este, b.promedio_norte,
        CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0 AS dias,
        SQRT(POWER(b.promedio_este - FIRST_VALUE(b.promedio_este) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2) + POWER(b.promedio_norte - FIRST_VALUE(b.promedio_norte) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2)) * ? AS dosD,
        b.tipo_equipo, b.bloque_dias FROM bloques b
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
        CASE WHEN DATEDIFF(SECOND, FIRST_VALUE(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) = 0 THEN 0
        ELSE (dosD - FIRST_VALUE(dosD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma)) / NULLIF((CAST(DATEDIFF(SECOND, FIRST_VALUE(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0), 0) END AS VA2D, tipo_equipo
        FROM velocidad ORDER BY nombre_prisma, hora_prisma;"""
        conn = None
        try:
            conn = Connection.connectionDB(); cur = conn.cursor(); cur.arraysize = 1000
            cur.execute(sql, params); rows = cur.fetchall(); results = list(map(tuple, rows))
            return results if results else None
        except Exception as e:
            print("Error al consultar prom dias va2d fechas: " + str(e)); return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlCalcularVelocidadHorasVA2D(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        if not prismas: return None
        conn = None
        try:
            placeholders = ', '.join(['?' for _ in prismas])
            sql = f"""WITH PrimerBloque AS (
            SELECT nombre_prisma, MIN(hora_prisma) as hora_cero_aprox FROM {tabla} WHERE nombre_prisma IN ({placeholders}) AND state_prisma = 1 AND estado_prisma = 1 GROUP BY nombre_prisma
            ),
            ValoresCero AS (
            SELECT p.nombre_prisma, MAX(p.hora_prisma) as hora_cero, AVG(CAST(p.este_target AS FLOAT)) as este_cero, AVG(CAST(p.norte_target AS FLOAT)) as norte_cero
            FROM {tabla} p JOIN PrimerBloque pb ON p.nombre_prisma = pb.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND CAST(p.hora_prisma AS DATE) = CAST(pb.hora_cero_aprox AS DATE) AND DATEPART(HOUR, p.hora_prisma) / {cantidad} = DATEPART(HOUR, pb.hora_cero_aprox) / {cantidad} GROUP BY p.nombre_prisma
            ),
            BloquesEnRango AS (
            SELECT p.nombre_prisma, MAX(p.hora_prisma) as hora_bloque, AVG(CAST(p.este_target AS FLOAT)) as este_bloque, AVG(CAST(p.norte_target AS FLOAT)) as norte_bloque, MAX(i.id_instrumentacion) as id_instrumentacion, MAX(i.tipo_equipo) as tipo_equipo
            FROM {tabla} p JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.nombre_prisma IN ({placeholders}) AND i.id_componente = ? AND p.hora_prisma BETWEEN ? AND ? AND p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad}
            )
            SELECT br.id_instrumentacion, br.nombre_prisma, br.hora_bloque AS FECHAS,
            CAST(DATEDIFF(SECOND, vc.hora_cero, br.hora_bloque) AS FLOAT) / 86400.0 AS DIAS,
            (CAST(DATEDIFF(SECOND, vc.hora_cero, br.hora_bloque) AS FLOAT) / 86400.0) * 24.0 AS HORAS,
            CASE WHEN (CAST(DATEDIFF(SECOND, vc.hora_cero, br.hora_bloque) AS FLOAT) / 86400.0) = 0 THEN 0
            ELSE (SQRT(POWER(br.este_bloque - vc.este_cero, 2) + POWER(br.norte_bloque - vc.norte_cero, 2)) * ?) / NULLIF((CAST(DATEDIFF(SECOND, vc.hora_cero, br.hora_bloque) AS FLOAT) / 86400.0), 0) END AS VA2D, br.tipo_equipo
            FROM BloquesEnRango br JOIN ValoresCero vc ON br.nombre_prisma = vc.nombre_prisma ORDER BY br.nombre_prisma, br.hora_bloque;"""
            params = prismas + prismas + [idcomponente, fechaini, fechafin, unidad]
            conn = Connection.connectionDB(); cur = conn.cursor(); cur.arraysize = 1000
            cur.execute(sql, params); rows = cur.fetchall(); results = list(map(tuple, rows))
            return results if results else None
        except Exception as e:
            print("Error al consultar prom horas va2d: " + str(e)); return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlCalcularVelocidadHorasFechasVA2D(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        sql = f"""WITH promedios_horas AS (
        SELECT i.id_instrumentacion, p.nombre_prisma, CAST(p.hora_prisma AS DATE) AS fecha, DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, MAX(p.hora_prisma) AS hora_prisma,
        AVG(CAST(p.este_target AS FLOAT)) AS promedio_este, AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte, i.tipo_equipo
        FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ? AND p.hora_prisma BETWEEN ? AND ?
        GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad}, i.id_instrumentacion, i.tipo_equipo
        ),
        velocidad AS (
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma, pd.promedio_este, pd.promedio_norte,
        CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0 AS dias,
        SQRT(POWER(pd.promedio_este - FIRST_VALUE(pd.promedio_este) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2) + POWER(pd.promedio_norte - FIRST_VALUE(pd.promedio_norte) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2)) * ? AS dosD,
        pd.tipo_equipo, pd.fecha, pd.bloque FROM promedios_horas pd
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
        CASE WHEN DATEDIFF(SECOND, FIRST_VALUE(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) = 0 THEN 0
        ELSE (dosD - FIRST_VALUE(dosD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma)) / NULLIF((CAST(DATEDIFF(SECOND, FIRST_VALUE(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0), 0) END AS VA2D, tipo_equipo
        FROM velocidad ORDER BY nombre_prisma, hora_prisma;"""
        conn = None
        try:
            conn = Connection.connectionDB(); cur = conn.cursor(); cur.arraysize = 1000
            cur.execute(sql, params); rows = cur.fetchall(); results = list(map(tuple, rows))
            return results if results else None
        except Exception as e:
            print("Error al consultar prom horas va2d fechas: " + str(e)); return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlCalcularVelocidadPositivaVI3D(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        if not prismas: return None
        conn = None
        try:
            placeholders = ', '.join(['?' for _ in prismas])
            sql = f"""WITH datos_filtrados AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, p.elevacion_target, i.tipo_equipo FROM (
            SELECT *, ROW_NUMBER() OVER(PARTITION BY nombre_prisma ORDER BY hora_prisma DESC) as rn FROM {tabla} WHERE nombre_prisma IN ({placeholders}) AND hora_prisma < ?
            ) p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo WHERE p.rn = 1 AND i.id_componente = ?
            UNION ALL
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, p.elevacion_target, i.tipo_equipo FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.nombre_prisma IN ({placeholders}) AND i.id_componente = ? AND p.hora_prisma BETWEEN ? AND ?
            ),
            PrismasCTE AS (
            SELECT id_instrumentacion, nombre_prisma, hora_prisma, tipo_equipo,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0 AS dias,
            SQRT(POWER(este_target - LAG(este_target) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), 2) + POWER(norte_target - LAG(norte_target) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), 2) + POWER(elevacion_target - LAG(elevacion_target) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), 2)) * ? AS tresD,
            CAST(DATEDIFF(SECOND, LAG(hora_prisma, 1, hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0 AS dif_dias FROM datos_filtrados
            )
            SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
            CASE WHEN dif_dias = 0 THEN 0 ELSE tresD / NULLIF(dif_dias, 0) END AS VI3D, tipo_equipo FROM PrismasCTE WHERE hora_prisma BETWEEN ? AND ? ORDER BY nombre_prisma, hora_prisma;"""
            params = prismas + [fechaini] + [idcomponente] + prismas + [idcomponente, fechaini, fechafin] + [unidad] + [fechaini, fechafin]
            conn = Connection.connectionDB(); cur = conn.cursor(); cur.arraysize = 1000
            cur.execute(sql, params); rows = cur.fetchall(); results = list(map(tuple, rows))
            return results if results else None
        except Exception as e:
            print("Error al consultar vi3d positiva: " + str(e)); return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlCalcularVelocidadPositivaFechasVI3D(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente] + [fechaini] + [fechafin]
        sql = f"""WITH PrismasCTE AS (
        SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, p.elevacion_target,
        CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0 AS dias,
        SQRT(POWER(p.este_target - LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) + POWER(p.norte_target - LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) + POWER(p.elevacion_target - LAG(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)) * ? AS tresD, i.tipo_equipo
        FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ? AND p.hora_prisma BETWEEN ? AND ?
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
        CASE WHEN LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) IS NULL THEN 0
        ELSE tresD / NULLIF((CAST(DATEDIFF(SECOND, LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0), 0) END AS VI3D, tipo_equipo
        FROM PrismasCTE ORDER BY nombre_prisma, hora_prisma;"""
        conn = None
        try:
            conn = Connection.connectionDB(); cur = conn.cursor(); cur.arraysize = 1000
            cur.execute(sql, params); rows = cur.fetchall(); results = list(map(tuple, rows))
            return results if results else None
        except Exception as e:
            print("Error al consultar vi3d positiva fechas: " + str(e)); return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlCalcularVelocidadDiasPositivaVI3D(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        if not prismas: return None
        conn = None
        try:
            placeholders = ', '.join(['?' for _ in prismas])
            sql = f"""WITH datos_para_promedio AS (
            SELECT p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, p.elevacion_target, i.id_instrumentacion, i.tipo_equipo FROM {tabla} p JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.nombre_prisma IN ({placeholders}) AND i.id_componente = ? AND p.hora_prisma BETWEEN ? AND ?
            UNION ALL
            SELECT p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, p.elevacion_target, i.id_instrumentacion, i.tipo_equipo FROM {tabla} p JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.nombre_prisma IN ({placeholders}) AND i.id_componente = ? AND CAST(p.hora_prisma AS DATE) = (SELECT MAX(CAST(p_inner.hora_prisma AS DATE)) FROM {tabla} p_inner WHERE p_inner.nombre_prisma = p.nombre_prisma AND p_inner.hora_prisma < ?)
            ),
            bloques AS (
            SELECT nombre_prisma, MAX(hora_prisma) AS hora_prisma, AVG(CAST(este_target AS FLOAT)) AS promedio_este, AVG(CAST(norte_target AS FLOAT)) AS promedio_norte, AVG(CAST(elevacion_target AS FLOAT)) AS promedio_elevacion, MAX(id_instrumentacion) AS id_instrumentacion, MAX(tipo_equipo) AS tipo_equipo
            FROM datos_para_promedio GROUP BY nombre_prisma, CAST(hora_prisma AS DATE)
            ),
            velocidad AS (
            SELECT *, SQRT(POWER(promedio_este - LAG(promedio_este) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), 2) + POWER(promedio_norte - LAG(promedio_norte) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), 2) + POWER(promedio_elevacion - LAG(promedio_elevacion) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), 2)) * ? AS tresD,
            CAST(DATEDIFF(SECOND, LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0 AS dif_dias FROM bloques
            )
            SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, 0 AS DIAS, 0 AS HORAS,
            CASE WHEN dif_dias = 0 THEN 0 ELSE tresD / NULLIF(dif_dias, 0) END AS VI3D, tipo_equipo FROM velocidad WHERE hora_prisma BETWEEN ? AND ? ORDER BY nombre_prisma, hora_prisma;"""
            params = prismas + [idcomponente, fechaini, fechafin] + prismas + [idcomponente, fechaini] + [unidad, fechaini, fechafin]
            conn = Connection.connectionDB(); cur = conn.cursor(); cur.arraysize = 1000
            cur.execute(sql, params); rows = cur.fetchall(); results = list(map(tuple, rows))
            return results if results else None
        except Exception as e:
            print("Error al consultar prom dias vi3d positiva: " + str(e)); return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlCalcularVelocidadDiasPositivaFechasVI3D(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        sql = f"""WITH fechas_inicio AS (
        SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1 GROUP BY p.nombre_prisma
        ),
        bloques AS (
        SELECT i.id_instrumentacion, p.nombre_prisma, CAST(p.hora_prisma AS DATE) AS fecha, MAX(p.hora_prisma) AS hora_prisma,
        AVG(CAST(p.este_target AS FLOAT)) AS promedio_este, AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte, AVG(CAST(p.elevacion_target AS FLOAT)) AS promedio_elevacion,
        FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad} ) AS bloque_dias, i.tipo_equipo
        FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ? AND p.hora_prisma BETWEEN ? AND ?
        GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), f.fecha_inicio, i.id_instrumentacion, i.tipo_equipo
        ),
        velocidad AS (
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma, b.promedio_este, b.promedio_norte, b.promedio_elevacion,
        CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0 AS dias,
        SQRT(POWER(b.promedio_este - LAG(b.promedio_este) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2) + POWER(b.promedio_norte - LAG(b.promedio_norte) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2) + POWER(b.promedio_elevacion - LAG(b.promedio_elevacion) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2)) * ? AS tresD,
        b.tipo_equipo, b.bloque_dias FROM bloques b
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
        CASE WHEN LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) IS NULL THEN 0
        ELSE tresD / NULLIF((CAST(DATEDIFF(SECOND, LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0), 0) END AS VI3D, tipo_equipo
        FROM velocidad ORDER BY nombre_prisma, bloque_dias;"""
        conn = None
        try:
            conn = Connection.connectionDB(); cur = conn.cursor(); cur.arraysize = 1000
            cur.execute(sql, params); rows = cur.fetchall(); results = list(map(tuple, rows))
            return results if results else None
        except Exception as e:
            print("Error al consultar prom dias vi3d positiva fechas: " + str(e)); return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlCalcularVelocidadHorasPositivaVI3D(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        if not prismas: return None
        conn = None
        try:
            placeholders = ', '.join(['?' for _ in prismas])
            sql = f"""WITH datos_para_promedio AS (
            SELECT p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, p.elevacion_target, i.id_instrumentacion, i.tipo_equipo FROM {tabla} p JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.nombre_prisma IN ({placeholders}) AND i.id_componente = ? AND p.hora_prisma BETWEEN ? AND ?
            UNION ALL
            SELECT p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, p.elevacion_target, i.id_instrumentacion, i.tipo_equipo FROM {tabla} p JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.nombre_prisma IN ({placeholders}) AND i.id_componente = ? AND p.hora_prisma IN (SELECT TOP 1 WITH TIES p_inner.hora_prisma FROM {tabla} p_inner WHERE p_inner.nombre_prisma = p.nombre_prisma AND p_inner.hora_prisma < ? ORDER BY p_inner.hora_prisma DESC)
            ),
            bloques AS (
            SELECT nombre_prisma, MAX(hora_prisma) AS hora_prisma, AVG(CAST(este_target AS FLOAT)) AS promedio_este, AVG(CAST(norte_target AS FLOAT)) AS promedio_norte, AVG(CAST(elevacion_target AS FLOAT)) AS promedio_elevacion, MAX(id_instrumentacion) AS id_instrumentacion, MAX(tipo_equipo) AS tipo_equipo
            FROM datos_para_promedio GROUP BY nombre_prisma, CAST(hora_prisma AS DATE), DATEPART(HOUR, hora_prisma) / {cantidad}
            ),
            velocidad AS (
            SELECT *, SQRT(POWER(promedio_este - LAG(promedio_este) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), 2) + POWER(promedio_norte - LAG(promedio_norte) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), 2) + POWER(promedio_elevacion - LAG(promedio_elevacion) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), 2)) * ? AS tresD,
            CAST(DATEDIFF(SECOND, LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0 AS dif_dias FROM bloques
            )
            SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, 0 AS DIAS, 0 AS HORAS,
            CASE WHEN dif_dias = 0 THEN 0 ELSE tresD / NULLIF(dif_dias, 0) END AS VI3D, tipo_equipo FROM velocidad WHERE hora_prisma BETWEEN ? AND ? ORDER BY nombre_prisma, hora_prisma;"""
            params = prismas + [idcomponente, fechaini, fechafin] + prismas + [idcomponente, fechaini] + [unidad, fechaini, fechafin]
            conn = Connection.connectionDB(); cur = conn.cursor(); cur.arraysize = 1000
            cur.execute(sql, params); rows = cur.fetchall(); results = list(map(tuple, rows))
            return results if results else None
        except Exception as e:
            print("Error al consultar prom horas vi3d positiva: " + str(e)); return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlCalcularVelocidadHorasPositivaFechasVI3D(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        sql = f"""WITH promedios_horas AS (
        SELECT i.id_instrumentacion, p.nombre_prisma, CAST(p.hora_prisma AS DATE) AS fecha, DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, MAX(p.hora_prisma) AS hora_prisma,
        AVG(CAST(p.este_target AS FLOAT)) AS promedio_este, AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte, AVG(CAST(p.elevacion_target AS FLOAT)) AS promedio_elevacion, i.tipo_equipo
        FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ? AND p.hora_prisma BETWEEN ? AND ?
        GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad}, i.id_instrumentacion, i.tipo_equipo
        ),
        velocidad AS (
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma, pd.promedio_este, pd.promedio_norte, pd.promedio_elevacion,
        CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0 AS dias,
        SQRT(POWER(pd.promedio_este - LAG(pd.promedio_este) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2) + POWER(pd.promedio_norte - LAG(pd.promedio_norte) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2) + POWER(pd.promedio_elevacion - LAG(pd.promedio_elevacion) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2)) * ? AS tresD,
        pd.tipo_equipo, pd.fecha, pd.bloque FROM promedios_horas pd
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
        CASE WHEN LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) IS NULL THEN 0
        ELSE tresD / NULLIF((CAST(DATEDIFF(SECOND, LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0), 0) END AS VI3D, tipo_equipo
        FROM velocidad ORDER BY nombre_prisma, hora_prisma;"""
        conn = None
        try:
            conn = Connection.connectionDB(); cur = conn.cursor(); cur.arraysize = 1000
            cur.execute(sql, params); rows = cur.fetchall(); results = list(map(tuple, rows))
            return results if results else None
        except Exception as e:
            print("Error al consultar prom horas vi3d positiva fechas: " + str(e)); return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlCalcularVelocidadVI3D(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        if not prismas: return None
        conn = None
        try:
            placeholders = ', '.join(['?' for _ in prismas])
            sql = f"""WITH datos_filtrados AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, p.elevacion_target, i.tipo_equipo FROM (
            SELECT *, ROW_NUMBER() OVER(PARTITION BY nombre_prisma ORDER BY hora_prisma DESC) as rn FROM {tabla} WHERE nombre_prisma IN ({placeholders}) AND hora_prisma < ?
            ) p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo WHERE p.rn = 1 AND i.id_componente = ?
            UNION ALL
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, p.elevacion_target, i.tipo_equipo FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.nombre_prisma IN ({placeholders}) AND i.id_componente = ? AND p.hora_prisma BETWEEN ? AND ?
            ),
            PrismasCTE AS (
            SELECT id_instrumentacion, nombre_prisma, hora_prisma, tipo_equipo,
            CAST(DATEDIFF(SECOND, FIRST_VALUE(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0 AS dias,
            SQRT(POWER(este_target - LAG(este_target) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), 2) + POWER(norte_target - LAG(norte_target) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), 2) + POWER(elevacion_target - LAG(elevacion_target) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), 2)) * ? AS tresD,
            CAST(DATEDIFF(SECOND, LAG(hora_prisma, 1, hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0 AS dif_dias FROM datos_filtrados
            )
            SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
            CASE WHEN dif_dias = 0 THEN 0 ELSE (tresD - LAG(tresD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma)) / NULLIF(dif_dias, 0) END AS VI3D, tipo_equipo FROM PrismasCTE WHERE hora_prisma BETWEEN ? AND ? ORDER BY nombre_prisma, hora_prisma;"""
            params = prismas + [fechaini] + [idcomponente] + prismas + [idcomponente, fechaini, fechafin] + [unidad] + [fechaini, fechafin]
            conn = Connection.connectionDB(); cur = conn.cursor(); cur.arraysize = 1000
            cur.execute(sql, params); rows = cur.fetchall(); results = list(map(tuple, rows))
            return results if results else None
        except Exception as e:
            print("Error al consultar vi3d: " + str(e)); return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlCalcularVelocidadFechasVI3D(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente] + [fechaini] + [fechafin]
        sql = f"""WITH PrismasCTE AS (
        SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, p.elevacion_target,
        CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0 AS dias,
        CASE WHEN ROW_NUMBER() OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) = 1 THEN 0 ELSE
        SQRT(POWER(p.este_target - LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) + POWER(p.norte_target - LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) + POWER(p.elevacion_target - LAG(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)) * ?
        END AS tresD, i.tipo_equipo
        FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ? AND p.hora_prisma BETWEEN ? AND ?
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
        CASE WHEN ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) = 1 THEN 0 ELSE
        (tresD - LAG(tresD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma)) / NULLIF((CAST(DATEDIFF(SECOND, LAG(hora_prisma, 1, hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0), 0)
        END AS VI3D, tipo_equipo FROM PrismasCTE ORDER BY nombre_prisma, hora_prisma;"""
        conn = None
        try:
            conn = Connection.connectionDB(); cur = conn.cursor(); cur.arraysize = 1000
            cur.execute(sql, params); rows = cur.fetchall(); results = list(map(tuple, rows))
            return results if results else None
        except Exception as e:
            print("Error al consultar vi3d fechas: " + str(e)); return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlCalcularVelocidadDiasVI3D(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        if not prismas: return None
        conn = None
        try:
            placeholders = ', '.join(['?' for _ in prismas])
            sql = f"""WITH datos_para_promedio AS (
            SELECT p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, p.elevacion_target, i.id_instrumentacion, i.tipo_equipo FROM {tabla} p JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.nombre_prisma IN ({placeholders}) AND i.id_componente = ? AND p.hora_prisma BETWEEN ? AND ?
            UNION ALL
            SELECT p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, p.elevacion_target, i.id_instrumentacion, i.tipo_equipo FROM {tabla} p JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.nombre_prisma IN ({placeholders}) AND i.id_componente = ? AND CAST(p.hora_prisma AS DATE) = (SELECT MAX(CAST(p_inner.hora_prisma AS DATE)) FROM {tabla} p_inner WHERE p_inner.nombre_prisma = p.nombre_prisma AND p_inner.hora_prisma < ?)
            ),
            bloques AS (
            SELECT nombre_prisma, MAX(hora_prisma) AS hora_prisma, AVG(CAST(este_target AS FLOAT)) AS promedio_este, AVG(CAST(norte_target AS FLOAT)) AS promedio_norte, AVG(CAST(elevacion_target AS FLOAT)) AS promedio_elevacion, MAX(id_instrumentacion) AS id_instrumentacion, MAX(tipo_equipo) AS tipo_equipo
            FROM datos_para_promedio GROUP BY nombre_prisma, CAST(hora_prisma AS DATE)
            ),
            velocidad AS (
            SELECT *, SQRT(POWER(promedio_este - LAG(promedio_este) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), 2) + POWER(promedio_norte - LAG(promedio_norte) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), 2) + POWER(promedio_elevacion - LAG(promedio_elevacion) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), 2)) * ? AS tresD,
            CAST(DATEDIFF(SECOND, LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0 AS dif_dias FROM bloques
            )
            SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, 0 AS DIAS, 0 AS HORAS,
            CASE WHEN dif_dias = 0 THEN 0 ELSE (tresD - LAG(tresD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma)) / NULLIF(dif_dias, 0) END AS VI3D, tipo_equipo FROM velocidad WHERE hora_prisma BETWEEN ? AND ? ORDER BY nombre_prisma, hora_prisma;"""
            params = prismas + [idcomponente, fechaini, fechafin] + prismas + [idcomponente, fechaini] + [unidad, fechaini, fechafin]
            conn = Connection.connectionDB(); cur = conn.cursor(); cur.arraysize = 1000
            cur.execute(sql, params); rows = cur.fetchall(); results = list(map(tuple, rows))
            return results if results else None
        except Exception as e:
            print("Error al consultar prom dias vi3d: " + str(e)); return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlCalcularVelocidadDiasFechasVI3D(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        sql = f"""WITH fechas_inicio AS (
        SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1 GROUP BY p.nombre_prisma
        ),
        bloques AS (
        SELECT i.id_instrumentacion, p.nombre_prisma, CAST(p.hora_prisma AS DATE) AS fecha, MAX(p.hora_prisma) AS hora_prisma,
        AVG(CAST(p.este_target AS FLOAT)) AS promedio_este, AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte, AVG(CAST(p.elevacion_target AS FLOAT)) AS promedio_elevacion,
        FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad} ) AS bloque_dias, i.tipo_equipo
        FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ? AND p.hora_prisma BETWEEN ? AND ?
        GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), f.fecha_inicio, i.id_instrumentacion, i.tipo_equipo
        ),
        velocidad AS (
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma, b.promedio_este, b.promedio_norte, b.promedio_elevacion,
        CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0 AS dias,
        CASE WHEN ROW_NUMBER() OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma) = 1 THEN 0 ELSE
        SQRT(POWER(b.promedio_este - LAG(b.promedio_este) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2) + POWER(b.promedio_norte - LAG(b.promedio_norte) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2) + POWER(b.promedio_elevacion - LAG(b.promedio_elevacion) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2)) * ? END AS tresD, b.tipo_equipo, b.bloque_dias FROM bloques b
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
        CASE WHEN ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) = 1 THEN 0 ELSE
        (tresD - LAG(tresD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma)) / NULLIF((CAST(DATEDIFF(SECOND, LAG(hora_prisma, 1, hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0), 0)
        END AS VI3D, tipo_equipo FROM velocidad ORDER BY nombre_prisma, hora_prisma;"""
        conn = None
        try:
            conn = Connection.connectionDB(); cur = conn.cursor(); cur.arraysize = 1000
            cur.execute(sql, params); rows = cur.fetchall(); results = list(map(tuple, rows))
            return results if results else None
        except Exception as e:
            print("Error al consultar prom dias vi3d fechas: " + str(e)); return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlCalcularVelocidadHorasVI3D(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        if not prismas: return None
        conn = None
        try:
            placeholders = ', '.join(['?' for _ in prismas])
            sql = f"""WITH datos_para_promedio AS (
            SELECT p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, p.elevacion_target, i.id_instrumentacion, i.tipo_equipo FROM {tabla} p JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.nombre_prisma IN ({placeholders}) AND i.id_componente = ? AND p.hora_prisma BETWEEN ? AND ?
            UNION ALL
            SELECT p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, p.elevacion_target, i.id_instrumentacion, i.tipo_equipo FROM {tabla} p JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.nombre_prisma IN ({placeholders}) AND i.id_componente = ? AND p.hora_prisma IN (SELECT TOP 1 WITH TIES p_inner.hora_prisma FROM {tabla} p_inner WHERE p_inner.nombre_prisma = p.nombre_prisma AND p_inner.hora_prisma < ? ORDER BY p_inner.hora_prisma DESC)
            ),
            bloques AS (
            SELECT nombre_prisma, MAX(hora_prisma) AS hora_prisma, AVG(CAST(este_target AS FLOAT)) AS promedio_este, AVG(CAST(norte_target AS FLOAT)) AS promedio_norte, AVG(CAST(elevacion_target AS FLOAT)) AS promedio_elevacion, MAX(id_instrumentacion) AS id_instrumentacion, MAX(tipo_equipo) AS tipo_equipo
            FROM datos_para_promedio GROUP BY nombre_prisma, CAST(hora_prisma AS DATE), DATEPART(HOUR, hora_prisma) / {cantidad}
            ),
            velocidad AS (
            SELECT *, SQRT(POWER(promedio_este - LAG(promedio_este) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), 2) + POWER(promedio_norte - LAG(promedio_norte) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), 2) + POWER(promedio_elevacion - LAG(promedio_elevacion) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), 2)) * ? AS tresD,
            CAST(DATEDIFF(SECOND, LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0 AS dif_dias FROM bloques
            )
            SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, 0 AS DIAS, 0 AS HORAS,
            CASE WHEN dif_dias = 0 THEN 0 ELSE (tresD - LAG(tresD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma)) / NULLIF(dif_dias, 0) END AS VI3D, tipo_equipo FROM velocidad WHERE hora_prisma BETWEEN ? AND ? ORDER BY nombre_prisma, hora_prisma;"""
            params = prismas + [idcomponente, fechaini, fechafin] + prismas + [idcomponente, fechaini] + [unidad, fechaini, fechafin]
            conn = Connection.connectionDB(); cur = conn.cursor(); cur.arraysize = 1000
            cur.execute(sql, params); rows = cur.fetchall(); results = list(map(tuple, rows))
            return results if results else None
        except Exception as e:
            print("Error al consultar prom horas vi3d: " + str(e)); return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlCalcularVelocidadHorasFechasVI3D(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        sql = f"""WITH promedios_horas AS (
        SELECT i.id_instrumentacion, p.nombre_prisma, CAST(p.hora_prisma AS DATE) AS fecha, DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, MAX(p.hora_prisma) AS hora_prisma,
        AVG(CAST(p.este_target AS FLOAT)) AS promedio_este, AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte, AVG(CAST(p.elevacion_target AS FLOAT)) AS promedio_elevacion, i.tipo_equipo
        FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ? AND p.hora_prisma BETWEEN ? AND ?
        GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad}, i.id_instrumentacion, i.tipo_equipo
        ),
        velocidad AS (
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma, pd.promedio_este, pd.promedio_norte, pd.promedio_elevacion,
        CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0 AS dias,
        CASE WHEN ROW_NUMBER() OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma) = 1 THEN 0 ELSE
        SQRT(POWER(pd.promedio_este - LAG(pd.promedio_este) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2) + POWER(pd.promedio_norte - LAG(pd.promedio_norte) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2) + POWER(pd.promedio_elevacion - LAG(pd.promedio_elevacion) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2)) * ? END AS tresD, pd.tipo_equipo, pd.fecha, pd.bloque FROM promedios_horas pd
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
        CASE WHEN ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) = 1 THEN 0 ELSE
        (tresD - LAG(tresD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma)) / NULLIF((CAST(DATEDIFF(SECOND, LAG(hora_prisma, 1, hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0), 0)
        END AS VI3D, tipo_equipo FROM velocidad ORDER BY nombre_prisma, hora_prisma;"""
        conn = None
        try:
            conn = Connection.connectionDB(); cur = conn.cursor(); cur.arraysize = 1000
            cur.execute(sql, params); rows = cur.fetchall(); results = list(map(tuple, rows))
            return results if results else None
        except Exception as e:
            print("Error al consultar prom horas vi3d fechas: " + str(e)); return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlCalcularVelocidadVA3D(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        if not prismas: return None
        conn = None
        try:
            placeholders = ', '.join(['?' for _ in prismas])
            sql = f"""WITH ValoresCero AS (
            SELECT p_cte.nombre_prisma, p_cte.este_target AS este_cero, p_cte.norte_target AS norte_cero, p_cte.elevacion_target AS elevacion_cero, p_cte.hora_prisma AS hora_cero
            FROM (SELECT nombre_prisma, este_target, norte_target, elevacion_target, hora_prisma, ROW_NUMBER() OVER(PARTITION BY nombre_prisma ORDER BY hora_prisma ASC) as rn FROM {tabla} WHERE nombre_prisma IN ({placeholders}) AND state_prisma = 1 AND estado_prisma = 1) p_cte WHERE p_cte.rn = 1
            ),
            CalculoCTE AS (
            SELECT i.id_instrumentacion, datos.nombre_prisma, datos.hora_prisma, i.tipo_equipo,
            (CAST(DATEDIFF(SECOND, vc.hora_cero, datos.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            SQRT(POWER(datos.este_target - vc.este_cero, 2) + POWER(datos.norte_target - vc.norte_cero, 2) + POWER(datos.elevacion_target - vc.elevacion_cero, 2)) * ? AS tresD
            FROM {tabla} datos INNER JOIN instrumentacion i ON datos.nombre_prisma = i.nombre_equipo INNER JOIN ValoresCero vc ON datos.nombre_prisma = vc.nombre_prisma
            WHERE datos.state_prisma = 1 AND datos.estado_prisma = 1 AND i.id_componente = ? AND datos.hora_prisma BETWEEN ? AND ?
            )
            SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
            CASE WHEN dias = 0 THEN 0 ELSE tresD / NULLIF(dias, 0) END AS VA3D, tipo_equipo FROM CalculoCTE ORDER BY nombre_prisma, hora_prisma;"""
            params = prismas + [unidad, idcomponente, fechaini, fechafin]
            conn = Connection.connectionDB(); cur = conn.cursor(); cur.arraysize = 1000
            cur.execute(sql, params); rows = cur.fetchall(); results = list(map(tuple, rows))
            return results if results else None
        except Exception as e:
            print("Error al consultar va3d: " + str(e)); return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlCalcularVelocidadFechasVA3D(tabla, unidad, prismas, idcomponente, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidad] + prismas + [idcomponente] + [fechaini] + [fechafin]
        sql = f"""WITH PrismasCTE AS (
        SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, p.elevacion_target,
        CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0 AS dias,
        SQRT(POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) + POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) + POWER(p.elevacion_target - FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)) * ? AS tresD, i.tipo_equipo
        FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ? AND p.hora_prisma BETWEEN ? AND ?
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
        CASE WHEN DATEDIFF(SECOND, FIRST_VALUE(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) = 0 THEN 0
        ELSE (tresD - FIRST_VALUE(tresD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma)) / NULLIF((CAST(DATEDIFF(SECOND, FIRST_VALUE(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0), 0) END AS VA3D, tipo_equipo
        FROM PrismasCTE ORDER BY nombre_prisma, hora_prisma;"""
        conn = None
        try:
            conn = Connection.connectionDB(); cur = conn.cursor(); cur.arraysize = 1000
            cur.execute(sql, params); rows = cur.fetchall(); results = list(map(tuple, rows))
            return results if results else None
        except Exception as e:
            print("Error al consultar va3d fechas: " + str(e)); return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlCalcularVelocidadDiasVA3D(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        if not prismas: return None
        conn = None
        try:
            placeholders = ', '.join(['?' for _ in prismas])
            sql = f"""WITH PrimerDia AS (
            SELECT nombre_prisma, MIN(CAST(hora_prisma AS DATE)) as fecha_cero FROM {tabla} WHERE nombre_prisma IN ({placeholders}) AND state_prisma = 1 AND estado_prisma = 1 GROUP BY nombre_prisma
            ),
            ValoresCero AS (
            SELECT p.nombre_prisma, MAX(p.hora_prisma) as hora_cero, AVG(CAST(p.este_target AS FLOAT)) as este_cero, AVG(CAST(p.norte_target AS FLOAT)) as norte_cero, AVG(CAST(p.elevacion_target AS FLOAT)) as elevacion_cero
            FROM {tabla} p JOIN PrimerDia pd ON p.nombre_prisma = pd.nombre_prisma AND CAST(p.hora_prisma AS DATE) = pd.fecha_cero WHERE p.state_prisma = 1 AND p.estado_prisma = 1 GROUP BY p.nombre_prisma, pd.fecha_cero
            ),
            BloquesEnRango AS (
            SELECT p.nombre_prisma, MAX(p.hora_prisma) as hora_bloque, AVG(CAST(p.este_target AS FLOAT)) as este_bloque, AVG(CAST(p.norte_target AS FLOAT)) as norte_bloque, AVG(CAST(p.elevacion_target AS FLOAT)) as elevacion_bloque, MAX(i.id_instrumentacion) as id_instrumentacion, MAX(i.tipo_equipo) as tipo_equipo
            FROM {tabla} p JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.nombre_prisma IN ({placeholders}) AND i.id_componente = ? AND p.hora_prisma BETWEEN ? AND ? AND p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE)
            )
            SELECT br.id_instrumentacion, br.nombre_prisma, br.hora_bloque AS FECHAS,
            CAST(DATEDIFF(SECOND, vc.hora_cero, br.hora_bloque) AS FLOAT) / 86400.0 AS DIAS,
            (CAST(DATEDIFF(SECOND, vc.hora_cero, br.hora_bloque) AS FLOAT) / 86400.0) * 24.0 AS HORAS,
            CASE WHEN (CAST(DATEDIFF(SECOND, vc.hora_cero, br.hora_bloque) AS FLOAT) / 86400.0) = 0 THEN 0
            ELSE (SQRT(POWER(br.este_bloque - vc.este_cero, 2) + POWER(br.norte_bloque - vc.norte_cero, 2) + POWER(br.elevacion_bloque - vc.elevacion_cero, 2)) * ?) / NULLIF((CAST(DATEDIFF(SECOND, vc.hora_cero, br.hora_bloque) AS FLOAT) / 86400.0), 0) END AS VA3D, br.tipo_equipo
            FROM BloquesEnRango br JOIN ValoresCero vc ON br.nombre_prisma = vc.nombre_prisma ORDER BY br.nombre_prisma, br.hora_bloque;"""
            params = prismas + prismas + [idcomponente, fechaini, fechafin, unidad]
            conn = Connection.connectionDB(); cur = conn.cursor(); cur.arraysize = 1000
            cur.execute(sql, params); rows = cur.fetchall(); results = list(map(tuple, rows))
            return results if results else None
        except Exception as e:
            print("Error al consultar prom dias va3d: " + str(e)); return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlCalcularVelocidadDiasFechasVA3D(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        sql = f"""WITH fechas_inicio AS (
        SELECT p.nombre_prisma, MIN(CAST(p.hora_prisma AS DATE)) AS fecha_inicio FROM {tabla} p WHERE p.state_prisma = 1 AND p.estado_prisma = 1 GROUP BY p.nombre_prisma
        ),
        bloques AS (
        SELECT i.id_instrumentacion, p.nombre_prisma, CAST(p.hora_prisma AS DATE) AS fecha, MAX(p.hora_prisma) AS hora_prisma,
        AVG(CAST(p.este_target AS FLOAT)) AS promedio_este, AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte, AVG(CAST(p.elevacion_target AS FLOAT)) AS promedio_elevacion,
        FLOOR( (CAST(DATEDIFF(SECOND, f.fecha_inicio, CAST(p.hora_prisma AS DATE)) AS FLOAT) / 86400.0) / {cantidad} ) AS bloque_dias, i.tipo_equipo
        FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo INNER JOIN fechas_inicio f ON f.nombre_prisma = p.nombre_prisma
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ? AND p.hora_prisma BETWEEN ? AND ?
        GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), f.fecha_inicio, i.id_instrumentacion, i.tipo_equipo
        ),
        velocidad AS (
        SELECT b.id_instrumentacion, b.nombre_prisma, b.hora_prisma, b.promedio_este, b.promedio_norte, b.promedio_elevacion,
        CAST(DATEDIFF(SECOND, FIRST_VALUE(b.hora_prisma) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), b.hora_prisma) AS FLOAT) / 86400.0 AS dias,
        SQRT(POWER(b.promedio_este - FIRST_VALUE(b.promedio_este) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2) + POWER(b.promedio_norte - FIRST_VALUE(b.promedio_norte) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2) + POWER(b.promedio_elevacion - FIRST_VALUE(b.promedio_elevacion) OVER (PARTITION BY b.nombre_prisma ORDER BY b.hora_prisma), 2)) * ? AS tresD, b.tipo_equipo, b.bloque_dias FROM bloques b
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
        CASE WHEN DATEDIFF(SECOND, FIRST_VALUE(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) = 0 THEN 0
        ELSE (tresD - FIRST_VALUE(tresD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma)) / NULLIF((CAST(DATEDIFF(SECOND, FIRST_VALUE(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0), 0) END AS VA3D, tipo_equipo
        FROM velocidad ORDER BY nombre_prisma, hora_prisma;"""
        conn = None
        try:
            conn = Connection.connectionDB(); cur = conn.cursor(); cur.arraysize = 1000
            cur.execute(sql, params); rows = cur.fetchall(); results = list(map(tuple, rows))
            return results if results else None
        except Exception as e:
            print("Error al consultar prom dias va3d fechas: " + str(e)); return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlCalcularVelocidadHorasVA3D(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        if not prismas: return None
        conn = None
        try:
            placeholders = ', '.join(['?' for _ in prismas])
            sql = f"""WITH PrimerBloque AS (
            SELECT nombre_prisma, MIN(hora_prisma) as hora_cero_aprox FROM {tabla} WHERE nombre_prisma IN ({placeholders}) AND state_prisma = 1 AND estado_prisma = 1 GROUP BY nombre_prisma
            ),
            ValoresCero AS (
            SELECT p.nombre_prisma, MAX(p.hora_prisma) as hora_cero, AVG(CAST(p.este_target AS FLOAT)) as este_cero, AVG(CAST(p.norte_target AS FLOAT)) as norte_cero, AVG(CAST(p.elevacion_target AS FLOAT)) as elevacion_cero
            FROM {tabla} p JOIN PrimerBloque pb ON p.nombre_prisma = pb.nombre_prisma
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND CAST(p.hora_prisma AS DATE) = CAST(pb.hora_cero_aprox AS DATE) AND DATEPART(HOUR, p.hora_prisma) / {cantidad} = DATEPART(HOUR, pb.hora_cero_aprox) / {cantidad} GROUP BY p.nombre_prisma
            ),
            BloquesEnRango AS (
            SELECT p.nombre_prisma, MAX(p.hora_prisma) as hora_bloque, AVG(CAST(p.este_target AS FLOAT)) as este_bloque, AVG(CAST(p.norte_target AS FLOAT)) as norte_bloque, AVG(CAST(p.elevacion_target AS FLOAT)) as elevacion_bloque, MAX(i.id_instrumentacion) as id_instrumentacion, MAX(i.tipo_equipo) as tipo_equipo
            FROM {tabla} p JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.nombre_prisma IN ({placeholders}) AND i.id_componente = ? AND p.hora_prisma BETWEEN ? AND ? AND p.state_prisma = 1 AND p.estado_prisma = 1
            GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad}
            )
            SELECT br.id_instrumentacion, br.nombre_prisma, br.hora_bloque AS FECHAS,
            CAST(DATEDIFF(SECOND, vc.hora_cero, br.hora_bloque) AS FLOAT) / 86400.0 AS DIAS,
            (CAST(DATEDIFF(SECOND, vc.hora_cero, br.hora_bloque) AS FLOAT) / 86400.0) * 24.0 AS HORAS,
            CASE WHEN (CAST(DATEDIFF(SECOND, vc.hora_cero, br.hora_bloque) AS FLOAT) / 86400.0) = 0 THEN 0
            ELSE (SQRT(POWER(br.este_bloque - vc.este_cero, 2) + POWER(br.norte_bloque - vc.norte_cero, 2) + POWER(br.elevacion_bloque - vc.elevacion_cero, 2)) * ?) / NULLIF((CAST(DATEDIFF(SECOND, vc.hora_cero, br.hora_bloque) AS FLOAT) / 86400.0), 0) END AS VA3D, br.tipo_equipo
            FROM BloquesEnRango br JOIN ValoresCero vc ON br.nombre_prisma = vc.nombre_prisma ORDER BY br.nombre_prisma, br.hora_bloque;"""
            params = prismas + prismas + [idcomponente, fechaini, fechafin, unidad]
            conn = Connection.connectionDB(); cur = conn.cursor(); cur.arraysize = 1000
            cur.execute(sql, params); rows = cur.fetchall(); results = list(map(tuple, rows))
            return results if results else None
        except Exception as e:
            print("Error al consultar prom horas va3d: " + str(e)); return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlCalcularVelocidadHorasFechasVA3D(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin] + [unidad]
        sql = f"""WITH promedios_horas AS (
        SELECT i.id_instrumentacion, p.nombre_prisma, CAST(p.hora_prisma AS DATE) AS fecha, DATEPART(HOUR, p.hora_prisma) / {cantidad} AS bloque, MAX(p.hora_prisma) AS hora_prisma,
        AVG(CAST(p.este_target AS FLOAT)) AS promedio_este, AVG(CAST(p.norte_target AS FLOAT)) AS promedio_norte, AVG(CAST(p.elevacion_target AS FLOAT)) AS promedio_elevacion, i.tipo_equipo
        FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ? AND p.hora_prisma BETWEEN ? AND ?
        GROUP BY p.nombre_prisma, CAST(p.hora_prisma AS DATE), DATEPART(HOUR, p.hora_prisma) / {cantidad}, i.id_instrumentacion, i.tipo_equipo
        ),
        velocidad AS (
        SELECT pd.id_instrumentacion, pd.nombre_prisma, pd.hora_prisma, pd.promedio_este, pd.promedio_norte, pd.promedio_elevacion,
        CAST(DATEDIFF(SECOND, FIRST_VALUE(pd.hora_prisma) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), pd.hora_prisma) AS FLOAT) / 86400.0 AS dias,
        SQRT(POWER(pd.promedio_este - FIRST_VALUE(pd.promedio_este) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2) + POWER(pd.promedio_norte - FIRST_VALUE(pd.promedio_norte) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2) + POWER(pd.promedio_elevacion - FIRST_VALUE(pd.promedio_elevacion) OVER (PARTITION BY pd.nombre_prisma ORDER BY pd.hora_prisma), 2)) * ? AS tresD, pd.tipo_equipo, pd.fecha, pd.bloque FROM promedios_horas pd
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24.0 AS HORAS,
        CASE WHEN DATEDIFF(SECOND, FIRST_VALUE(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) = 0 THEN 0
        ELSE (tresD - FIRST_VALUE(tresD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma)) / NULLIF((CAST(DATEDIFF(SECOND, FIRST_VALUE(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0), 0) END AS VA3D, tipo_equipo
        FROM velocidad ORDER BY nombre_prisma, hora_prisma;"""
        conn = None
        try:
            conn = Connection.connectionDB(); cur = conn.cursor(); cur.arraysize = 1000
            cur.execute(sql, params); rows = cur.fetchall(); results = list(map(tuple, rows))
            return results if results else None
        except Exception as e:
            print("Error al consultar prom horas va3d fechas: " + str(e)); return None
        finally:
            if conn: conn.close()
