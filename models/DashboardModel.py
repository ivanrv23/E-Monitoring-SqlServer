from services.security.apis.conexiones.connection import Connection

class DashboardModel:
    
    @staticmethod
    def mdlObtenerInstrumentacionProyecto(proyecto_id, id_componente):
        conn = None
        try:
            conn = Connection.connectionDB()
            # La sintaxis CASE WHEN y COUNT es estándar, funciona igual en T-SQL
            sql = """SELECT 'Prismas Activos' AS nameprismas,
                COUNT(CASE WHEN i.tipo_equipo = 'PRISMAS' THEN 1 END) AS canti_prismas,
                'Prismas de Baja' AS nameprismasbaja,
                0 AS canti_prisma,
                'Piezómetros Cuerda Vibrante' AS namecuerda,
                COUNT(CASE WHEN i.tipo_equipo = 'PIEZOMETROCUERDA' THEN 1 END) AS canti_cuerda,
                'Piezómetros Manuales' AS namepiezomanual,
                COUNT(CASE WHEN i.tipo_equipo = 'PIEZOMETROMANUAL' THEN 1 END) AS canti_piezomanual,
                'Inclinómetros' AS nameinclino,
                COUNT(CASE WHEN i.tipo_equipo = 'INCLINOMETRO' THEN 1 END) AS canti_inclino,
                'Celdas de Asentamiento' AS namecelda,
                COUNT(CASE WHEN i.tipo_equipo = 'CELDA' THEN 1 END) AS canti_celda,
                'Acelerógrafos' AS nameacelero,
                COUNT(CASE WHEN i.tipo_equipo = 'ACELEROGRAFO' THEN 1 END) AS canti_acelero,
                'Equipos TDR' AS nametdr,
                COUNT(CASE WHEN i.tipo_equipo = 'TDR' THEN 1 END) AS canti_tdr,
                'Pluviómetros' AS namepluvio,
                COUNT(CASE WHEN i.tipo_equipo = 'PLUVIOMETRO' THEN 1 END) AS canti_pluvio,
                'Equipos Adicionales' AS nameadicional,
                COUNT(CASE WHEN i.tipo_equipo = 'ADICIONAL' THEN 1 END) AS canti_adicional
            FROM instrumentacion i INNER JOIN componentes c ON i.id_componente = c.id_componente
            WHERE c.id_proyecto = ?  AND i.id_componente = ? AND i.estado_instrumentacion = 1;"""
            cur = conn.cursor()
            cur.execute(sql, (proyecto_id, id_componente))
            results = cur.fetchone()
            
            if results:
                # Convertir Row a Tuple
                return tuple(results)
            else:
                return None
        except Exception as e:
            print("Error al obtener instrumentación:", e)
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlObtenerInstrumentacionOIProyecto(proyecto_id, id_componete):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = """SELECT i.estado_instrumentacion, COUNT(*) AS total_equipos
            FROM componentes c INNER JOIN instrumentacion i ON c.id_componente = i.id_componente
            WHERE c.id_proyecto = ? AND i.id_componente = ? AND i.tipo_equipo NOT IN ('TOPOGRAFIA', 'COTATERRENO') 
            GROUP BY i.estado_instrumentacion;"""
            cur = conn.cursor()
            cur.execute(sql, (proyecto_id, id_componete))
            # Fetchall devuelve lista de Rows, convertir a lista de Tuplas
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            
            # Diccionario de mapeo de estados
            estado_mapeo = {
                0: 'Inoperativos',
                1: 'Operativos'
            }
            # Aplicar el mapeo de estados a los resultados
            if results:
                # Nota: item[0] e item[1] funcionan igual en tupla que en Row, pero ya aseguramos que es tupla
                results = [(estado_mapeo.get(item[0], item[0]), item[1]) for item in results]
                return results
            else:
                return None
        except Exception as e:
            print("Error al obtener instrumentación:", e)
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlObtenerLecturasPrismas(tabla, id_componente, tipo):
        conn = None
        try:
            conn = Connection.connectionDB()
            # La inyección de nombre de tabla con f-string es necesaria si la tabla es variable,
            # asegúrate de que 'tabla' venga de fuente segura.
            sql = f"""
                SELECT
                    p.nombre_prisma,
                    COUNT(*) AS total_lecturas
                FROM
                    {tabla} p
                INNER JOIN
                    instrumentacion i ON p.nombre_prisma = i.nombre_equipo
                WHERE
                    p.estado_prisma = 1
                    AND i.estado_instrumentacion=1
                    AND i.id_componente = ?
                    AND i.tipo_equipo = ?
                GROUP BY
                    p.nombre_prisma
            """
            cur = conn.cursor()
            cur.execute(sql, (id_componente, tipo))
            rows = cur.fetchall()

            if rows:
                # Convertir explícitamente a lista de tuplas
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print(f"Error al obtener las lecturas de los prismas: {e}")
            return None
        finally:
            if conn:
                conn.close()

    # @staticmethod
    # def mdlObtenerestadoequipos(proyecto_id, id_componente):
    #     conn = None
    #     try:
    #         conn = Connection.connectionDB()

    #         tabla_prismas = f"prismas{proyecto_id}"

    #         sql = f"""
    #             WITH Clasificado AS (
    #                 SELECT
    #                     'Prismas' AS tipo_equipo,
    #                     CASE
    #                         WHEN p.estado_prisma = 1
    #                             AND i.estado_instrumentacion = 1
    #                             AND p.hora_prisma >= DATEADD(DAY, -30, GETDATE())
    #                             THEN 'Operativos'
    #                         WHEN p.hora_prisma IS NULL
    #                             OR p.hora_prisma < DATEADD(DAY, -30, GETDATE())
    #                             THEN 'Desactualizados'
    #                         ELSE 'Inoperativos'
    #                     END AS categoria
    #                 FROM {tabla_prismas} p
    #                 INNER JOIN instrumentacion i
    #                     ON p.nombre_prisma = i.nombre_equipo
    #                 WHERE i.id_componente = ?
    #             )
    #             SELECT tipo_equipo, categoria, COUNT(*) AS total_equipos
    #             FROM Clasificado
    #             GROUP BY tipo_equipo, categoria
    #         """

    #         cur = conn.cursor()
    #         cur.execute(sql, (id_componente,))
    #         rows = cur.fetchall()

    #         return [tuple(row) for row in rows] if rows else None

    #     except Exception as e:
    #         print(f"Error al obtener el estado de los equipos: {e}")
    #         return None
    #     finally:
    #         if conn:
    #             conn.close()

    @staticmethod
    def _tabla_existe(cur, nombre_tabla):
        """Valida si una tabla existe en la base de datos."""
        cur.execute("""
            SELECT 1
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_NAME = ?
        """, (nombre_tabla,))
        return cur.fetchone() is not None
    
    @staticmethod
    def mdlObtenerestadoequipos(proyecto_id, id_componente):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()

            DIAS_DESACTUALIZADO = 30
            resultado_final = []

            # -----------------------------------------------------------
            # 1) PRISMAS
            # Lógica:
            # - Agrupar por nombre_prisma del componente
            # - state_prisma = 1 → Operativo (verificar desactualización)
            # - state_prisma = 0 → Inoperativo (no verificar desactualización)
            # - Operativo + última lectura (estado_prisma=1) < 30 días → Desactualizado
            # -----------------------------------------------------------
            tabla_prismas = f"prismas{proyecto_id}"
            if DashboardModel._tabla_existe(cur, tabla_prismas):
                sql_prismas = f"""
                    WITH Categorias AS (
                        SELECT 'Operativos'       AS categoria UNION ALL
                        SELECT 'Inoperativos'     AS categoria UNION ALL
                        SELECT 'Desactualizados'  AS categoria
                    ),
                    -- Obtener el estado actual y la última lectura activa por prisma
                    UltimoEstado AS (
                        SELECT
                            p.nombre_prisma,
                            p.state_prisma,
                            p.hora_prisma,
                            ROW_NUMBER() OVER (
                                PARTITION BY p.nombre_prisma
                                ORDER BY p.hora_prisma DESC
                            ) AS rn
                        FROM {tabla_prismas} p
                        INNER JOIN instrumentacion i
                            ON p.nombre_prisma = i.nombre_equipo
                        WHERE i.id_componente = ?
                    ),
                    -- Última lectura ACTIVA por prisma (estado_prisma = 1)
                    UltimaLecturaActiva AS (
                        SELECT
                            nombre_prisma,
                            MAX(hora_prisma) AS ultima_lectura_activa
                        FROM {tabla_prismas}
                        WHERE estado_prisma = 1
                        GROUP BY nombre_prisma
                    ),
                    -- Un registro por prisma con su estado actual
                    PrismaActual AS (
                        SELECT
                            ue.nombre_prisma,
                            ue.state_prisma,
                            ula.ultima_lectura_activa
                        FROM UltimoEstado ue
                        LEFT JOIN UltimaLecturaActiva ula
                            ON ue.nombre_prisma = ula.nombre_prisma
                        WHERE ue.rn = 1
                    ),
                    Clasificado AS (
                        SELECT
                            CASE
                                WHEN state_prisma = 0
                                    THEN 'Inoperativos'
                                WHEN state_prisma = 1
                                    AND (
                                        ultima_lectura_activa IS NULL
                                        OR ultima_lectura_activa < DATEADD(DAY, -?, GETDATE())
                                    )
                                    THEN 'Desactualizados'
                                ELSE 'Operativos'
                            END AS categoria
                        FROM PrismaActual
                    )
                    SELECT
                        'Prismas'                        AS tipo_equipo,
                        cat.categoria,
                        ISNULL(COUNT(cl.categoria), 0)   AS total_equipos
                    FROM Categorias cat
                    LEFT JOIN Clasificado cl ON cl.categoria = cat.categoria
                    GROUP BY cat.categoria
                """
                cur.execute(sql_prismas, (id_componente, DIAS_DESACTUALIZADO))
                resultado_final.extend(cur.fetchall())
            else:
                resultado_final.extend([
                    ('Prismas', 'Operativos', 0),
                    ('Prismas', 'Inoperativos', 0),
                    ('Prismas', 'Desactualizados', 0),
                ])

            # -----------------------------------------------------------
            # 2) PIEZOMETROS DE CUERDA VIBRANTE
            # Lógica:
            # - Tabla general: piezometrocuerdas → estado_piezometro (1=Op, 0=Inop)
            # - Tabla detalle: piezometrocuerda_detalle → fecha_cuerda
            # - Si operativo: verificar última lectura con estado_detalle = 1
            # - Si inoperativo: no verificar desactualización
            # -----------------------------------------------------------
            tabla_detalle_cuerda = f"piezometrocuerda_detalle{proyecto_id}"
            if DashboardModel._tabla_existe(cur, tabla_detalle_cuerda):
                sql_cuerda = f"""
                    WITH Categorias AS (
                        SELECT 'Operativos'       AS categoria UNION ALL
                        SELECT 'Inoperativos'     AS categoria UNION ALL
                        SELECT 'Desactualizados'  AS categoria
                    ),
                    -- Última lectura activa por piezómetro (solo estado_detalle = 1)
                    UltimaLectura AS (
                        SELECT
                            id_piezometro,
                            MAX(fecha_cuerda) AS ultima_fecha
                        FROM {tabla_detalle_cuerda}
                        WHERE estado_cuerda = 1
                        GROUP BY id_piezometro
                    ),
                    Base AS (
                        SELECT
                            pc.estado_piezometro,
                            ul.ultima_fecha
                        FROM piezometrocuerdas pc
                        INNER JOIN instrumentacion i
                            ON pc.nombre_piezometro = i.nombre_equipo
                        LEFT JOIN UltimaLectura ul
                            ON ul.id_piezometro = pc.id_piezometro
                        WHERE pc.id_proyecto = ?
                        AND i.id_componente = ?
                    ),
                    Clasificado AS (
                        SELECT
                            CASE
                                WHEN estado_piezometro = 0
                                    THEN 'Inoperativos'
                                WHEN estado_piezometro = 1
                                    AND (
                                        ultima_fecha IS NULL
                                        OR ultima_fecha < DATEADD(DAY, -?, GETDATE())
                                    )
                                    THEN 'Desactualizados'
                                ELSE 'Operativos'
                            END AS categoria
                        FROM Base
                    )
                    SELECT
                        'Piezometros Cuerda'             AS tipo_equipo,
                        cat.categoria,
                        ISNULL(COUNT(cl.categoria), 0)   AS total_equipos
                    FROM Categorias cat
                    LEFT JOIN Clasificado cl ON cl.categoria = cat.categoria
                    GROUP BY cat.categoria
                """
                cur.execute(sql_cuerda, (proyecto_id, id_componente, DIAS_DESACTUALIZADO))
                resultado_final.extend(cur.fetchall())
            else:
                resultado_final.extend([
                    ('Piezometros Cuerda', 'Operativos', 0),
                    ('Piezometros Cuerda', 'Inoperativos', 0),
                    ('Piezometros Cuerda', 'Desactualizados', 0),
                ])

            # -----------------------------------------------------------
            # 3) PIEZOMETROS MANUALES
            # Lógica:
            # - Tabla general: piezometromanuales → estado_piezometro (1=Op, 0=Inop)
            # - Tabla detalle: piezometromanual_detalle → fecha_piezometro
            # - Si operativo: verificar última lectura con estado_manual = 1
            # - Si inoperativo: no verificar desactualización
            # -----------------------------------------------------------
            tabla_detalle_manual = f"piezometromanual_detalle{proyecto_id}"
            if DashboardModel._tabla_existe(cur, tabla_detalle_manual):
                sql_manual = f"""
                    WITH Categorias AS (
                        SELECT 'Operativos'       AS categoria UNION ALL
                        SELECT 'Inoperativos'     AS categoria UNION ALL
                        SELECT 'Desactualizados'  AS categoria
                    ),
                    UltimaLectura AS (
                        SELECT
                            id_piezometro,
                            MAX(fecha_piezometro) AS ultima_fecha
                        FROM {tabla_detalle_manual}
                        WHERE estado_manual = 1
                        GROUP BY id_piezometro
                    ),
                    Base AS (
                        SELECT
                            pm.estado_piezometro,
                            ul.ultima_fecha
                        FROM piezometromanuales pm
                        INNER JOIN instrumentacion i
                            ON pm.nombre_piezometro = i.nombre_equipo
                        LEFT JOIN UltimaLectura ul
                            ON ul.id_piezometro = pm.id_piezometro
                        WHERE pm.id_proyecto = ?
                        AND i.id_componente = ?
                    ),
                    Clasificado AS (
                        SELECT
                            CASE
                                WHEN estado_piezometro = 0
                                    THEN 'Inoperativos'
                                WHEN estado_piezometro = 1
                                    AND (
                                        ultima_fecha IS NULL
                                        OR ultima_fecha < DATEADD(DAY, -?, GETDATE())
                                    )
                                    THEN 'Desactualizados'
                                ELSE 'Operativos'
                            END AS categoria
                        FROM Base
                    )
                    SELECT
                        'Piezometros Manuales'           AS tipo_equipo,
                        cat.categoria,
                        ISNULL(COUNT(cl.categoria), 0)   AS total_equipos
                    FROM Categorias cat
                    LEFT JOIN Clasificado cl ON cl.categoria = cat.categoria
                    GROUP BY cat.categoria
                """
                cur.execute(sql_manual, (proyecto_id, id_componente, DIAS_DESACTUALIZADO))
                resultado_final.extend(cur.fetchall())
            else:
                resultado_final.extend([
                    ('Piezometros Manuales', 'Operativos', 0),
                    ('Piezometros Manuales', 'Inoperativos', 0),
                    ('Piezometros Manuales', 'Desactualizados', 0),
                ])

            # -----------------------------------------------------------
            # 4) CELDAS
            # Lógica:
            # - Tabla general: celdas → estado_celda (1=Op, 0=Inop)
            # - Tabla detalle: celda_detalle → fecha_detalle
            # - Si operativo: verificar última lectura con estado_detalle = 1
            # - Si inoperativo: no verificar desactualización
            # -----------------------------------------------------------
            tabla_detalle_celda = f"celda_detalle{proyecto_id}"
            if DashboardModel._tabla_existe(cur, tabla_detalle_celda):
                sql_celda = f"""
                    WITH Categorias AS (
                        SELECT 'Operativos'       AS categoria UNION ALL
                        SELECT 'Inoperativos'     AS categoria UNION ALL
                        SELECT 'Desactualizados'  AS categoria
                    ),
                    UltimaLectura AS (
                        SELECT
                            id_celda,
                            MAX(fecha_detalle) AS ultima_fecha
                        FROM {tabla_detalle_celda}
                        WHERE estado_detalle = 1
                        GROUP BY id_celda
                    ),
                    Base AS (
                        SELECT
                            1 AS estado_celda,
                            ul.ultima_fecha
                        FROM celdas c
                        INNER JOIN instrumentacion i
                            ON c.nombre_celda = i.nombre_equipo
                        LEFT JOIN UltimaLectura ul
                            ON ul.id_celda = c.id_celda
                        WHERE c.id_proyecto = ?
                        AND i.id_componente = ?
                    ),
                    Clasificado AS (
                        SELECT
                            CASE
                                WHEN estado_celda = 0
                                    THEN 'Inoperativos'
                                WHEN estado_celda = 1
                                    AND (
                                        ultima_fecha IS NULL
                                        OR ultima_fecha < DATEADD(DAY, -?, GETDATE())
                                    )
                                    THEN 'Desactualizados'
                                ELSE 'Operativos'
                            END AS categoria
                        FROM Base
                    )
                    SELECT
                        'Celdas'                         AS tipo_equipo,
                        cat.categoria,
                        ISNULL(COUNT(cl.categoria), 0)   AS total_equipos
                    FROM Categorias cat
                    LEFT JOIN Clasificado cl ON cl.categoria = cat.categoria
                    GROUP BY cat.categoria
                """
                cur.execute(sql_celda, (proyecto_id, id_componente, DIAS_DESACTUALIZADO))
                resultado_final.extend(cur.fetchall())
            else:
                resultado_final.extend([
                    ('Celdas', 'Operativos', 0),
                    ('Celdas', 'Inoperativos', 0),
                    ('Celdas', 'Desactualizados', 0),
                ])

            # -----------------------------------------------------------
            # 5) PLUVIOMETROS
            # Lógica:
            # - Tabla general: pluviometros → estado_pluviometro (1=Op, 0=Inop)
            # - Tabla detalle: pluviometro_detalle → fecha_detalle
            # - Si operativo: verificar última lectura con estado_detalle = 1
            # - Si inoperativo: no verificar desactualización
            # -----------------------------------------------------------
            tabla_detalle_pluvio = f"pluviometro_detalle{proyecto_id}"
            if DashboardModel._tabla_existe(cur, tabla_detalle_pluvio):
                sql_pluvio = f"""
                    WITH Categorias AS (
                        SELECT 'Operativos'       AS categoria UNION ALL
                        SELECT 'Inoperativos'     AS categoria UNION ALL
                        SELECT 'Desactualizados'  AS categoria
                    ),
                    UltimaLectura AS (
                        SELECT
                            id_pluviometro,
                            MAX(fecha_pluviometro) AS ultima_fecha
                        FROM pluviometro_detalle2
                        GROUP BY id_pluviometro
                    ),
                    Base AS (
                        SELECT
                            pm.estado_pluviometro,
                            ul.ultima_fecha
                        FROM pluviometros pm
                        INNER JOIN instrumentacion i
                            ON pm.nombre_pluviometro = i.nombre_equipo
                        LEFT JOIN UltimaLectura ul
                            ON ul.id_pluviometro = pm.id_pluviometro
                        WHERE pm.id_proyecto = ?
                        AND i.id_componente = ?
                    ),
                    Clasificado AS (
                        SELECT
                            CASE
                                WHEN estado_pluviometro = 0
                                    THEN 'Inoperativos'
                                WHEN estado_pluviometro = 1
                                    AND (
                                        ultima_fecha IS NULL
                                        OR ultima_fecha < DATEADD(DAY, -?, GETDATE())
                                    )
                                    THEN 'Desactualizados'
                                ELSE 'Operativos'
                            END AS categoria
                        FROM Base
                    )
                    SELECT
                        'Pluviometros'                   AS tipo_equipo,
                        cat.categoria,
                        ISNULL(COUNT(cl.categoria), 0)   AS total_equipos
                    FROM Categorias cat
                    LEFT JOIN Clasificado cl ON cl.categoria = cat.categoria
                    GROUP BY cat.categoria
                """
                cur.execute(sql_pluvio, (proyecto_id, id_componente, DIAS_DESACTUALIZADO))
                resultado_final.extend(cur.fetchall())
            else:
                resultado_final.extend([
                    ('Pluviometros', 'Operativos', 0),
                    ('Pluviometros', 'Inoperativos', 0),
                    ('Pluviometros', 'Desactualizados', 0),
                ])

            # -----------------------------------------------------------
            # 6) ACELEROGRAFOS
            # Lógica:
            # - Tabla general: acelerografos → sin estado (se asume siempre operativo)
            # - Tabla detalle: acelerografo_detalle → fecha_detalle
            # - Si operativo: verificar última lectura con estado_detalle = 1
            # -----------------------------------------------------------
            tabla_detalle_acel = f"acelerografo_detalle{proyecto_id}"
            if DashboardModel._tabla_existe(cur, tabla_detalle_acel):
                sql_acel = f"""
                    WITH Categorias AS (
                        SELECT 'Operativos'       AS categoria UNION ALL
                        SELECT 'Inoperativos'     AS categoria UNION ALL
                        SELECT 'Desactualizados'  AS categoria
                    ),
                    UltimaLectura AS (
                        SELECT
                            id_acelerografo,
                            MAX(fecha_detalle) AS ultima_fecha
                        FROM acelerografo_detalle1
                        GROUP BY id_acelerografo
                    ),
                    Base AS (
                        SELECT
                            1 AS estado_acelerografo,
                            ul.ultima_fecha
                        FROM acelerografos a
                        INNER JOIN instrumentacion i
                            ON a.nombre_acelerografo = i.nombre_equipo
                        LEFT JOIN UltimaLectura ul
                            ON ul.id_acelerografo = a.id_acelerografo
                        WHERE a.id_proyecto = ?
                        AND i.id_componente = ?
                    ),
                    Clasificado AS (
                        SELECT
                            CASE
                                WHEN estado_acelerografo = 0
                                    THEN 'Inoperativos'
                                WHEN estado_acelerografo = 1
                                    AND (
                                        ultima_fecha IS NULL
                                        OR ultima_fecha < DATEADD(DAY, -?, GETDATE())
                                    )
                                    THEN 'Desactualizados'
                                ELSE 'Operativos'
                            END AS categoria
                        FROM Base
                    )
                    SELECT
                        'Acelerografos'                  AS tipo_equipo,
                        cat.categoria,
                        ISNULL(COUNT(cl.categoria), 0)   AS total_equipos
                    FROM Categorias cat
                    LEFT JOIN Clasificado cl ON cl.categoria = cat.categoria
                    GROUP BY cat.categoria
                """
                cur.execute(sql_acel, (proyecto_id, id_componente, DIAS_DESACTUALIZADO))
                resultado_final.extend(cur.fetchall())
            else:
                resultado_final.extend([
                    ('Acelerografos', 'Operativos', 0),
                    ('Acelerografos', 'Inoperativos', 0),
                    ('Acelerografos', 'Desactualizados', 0),
                ])

            return resultado_final if resultado_final else None

        except Exception as e:
            print(f"Error al obtener el estado de los equipos: {e}")
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod   
    def mdlObtenerObtenerComponentes(proyecto_id):
        sql = """SELECT * FROM componentes  WHERE id_proyecto = ? AND estado_componente = 1;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyecto_id,))
            rows = cur.fetchall()
            if rows:
                # Convertir explícitamente a lista de tuplas
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error al obtener componentes: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
        
    @staticmethod
    def mdlResumenPrismas(tabla, idcomponente):
        # TRANSICIÓN DE SQLITE A SQL SERVER:
        # 1. JULIANDAY(fechafin) - JULIANDAY(fechainicio) se convierte en:
        #    CAST(DATEDIFF(SECOND, fechainicio, fechafin) AS FLOAT) / 86400.0
        # 2. Las subconsultas en FROM deben tener alias en SQL Server (agregado 'AS subquery').
        # 3. Se castean los resultados matemáticos para asegurar float y no Decimal (si aplica).
        
        sql = f"""SELECT 
            nombre_prisma, 
            MIN(hora) AS fecha_minima, 
            MAX(hora) AS fecha_maxima, 
            COUNT(*) AS cantidad,
            (CAST(DATEDIFF(SECOND, MIN(hora), MAX(hora)) AS FLOAT) / 86400.0) + 1.0 as total_dias,
            CAST(COUNT(*) AS FLOAT) / ((CAST(DATEDIFF(SECOND, MIN(hora), MAX(hora)) AS FLOAT) / 86400.0) + 1.0) AS ratio
        FROM (
            SELECT nombre_prisma, hora_prisma AS hora FROM {tabla} p INNER JOIN instrumentacion i
            ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND i.estado_instrumentacion = 1 AND i.id_componente = ?
        ) AS subquery 
        GROUP BY nombre_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idcomponente,))
            rows = cur.fetchall()
            # Retornar lista de tuplas, SQL Server puede devolver Decimal en operaciones matematicas,
            # pero al convertir a tuple, Python lo maneja. Si el frontend requiere float estricto,
            # el CAST AS FLOAT en SQL ayuda.
            return [tuple(row) for row in rows]
        except Exception as e:
            print("Error al consultar Resumen prismas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()