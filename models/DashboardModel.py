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
    def _resumen_sin_detalle(cur, id_proyecto, id_componente, tabla_principal, columna_nombre_equipo, columna_estado, tipo_equipo):
        """Cuando no existe la tabla de detalle (sin historial de lecturas),
        solo se puede determinar operativo/inoperativo desde la tabla principal.
        Como no hay forma de verificar la fecha de última lectura, todos los
        operativos se consideran también desactualizados."""
        sql = f"""
            SELECT
                COUNT(CASE WHEN t.{columna_estado} = 1 THEN 1 END) AS operativos,
                COUNT(CASE WHEN t.{columna_estado} = 0 THEN 1 END) AS inoperativos
            FROM {tabla_principal} t
            INNER JOIN instrumentacion i ON t.{columna_nombre_equipo} = i.nombre_equipo
            WHERE t.id_proyecto = ? AND i.id_componente = ?
        """
        cur.execute(sql, (id_proyecto, id_componente))
        row = cur.fetchone()
        operativos = row[0] if row else 0
        inoperativos = row[1] if row else 0
        return [
            (tipo_equipo, 'Operativos', operativos),
            (tipo_equipo, 'Inoperativos', inoperativos),
            (tipo_equipo, 'Desactualizados', operativos),
        ]

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
                    WITH UltimoEstado AS (
                        -- El estado (operativo/inoperativo) de cada prisma es el de
                        -- su última fila insertada, sin importar si esa lectura es válida.
                        SELECT
                            p.nombre_prisma,
                            p.state_prisma,
                            ROW_NUMBER() OVER (
                                PARTITION BY p.nombre_prisma
                                ORDER BY p.hora_prisma DESC, p.id_prisma DESC
                            ) AS rn
                        FROM {tabla_prismas} p
                        INNER JOIN instrumentacion i
                            ON p.nombre_prisma = i.nombre_equipo
                        WHERE i.id_componente = ?
                    ),
                    PrismaActual AS (
                        SELECT nombre_prisma, state_prisma
                        FROM UltimoEstado
                        WHERE rn = 1
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
                    -- Un registro por prisma: su estado actual + si está desactualizado
                    -- (SOLO se marca desactualizado si está operativo; un inoperativo
                    -- no cuenta como desactualizado, según lo pedido)
                    Resumen AS (
                        SELECT
                            pa.nombre_prisma,
                            pa.state_prisma,
                            CASE
                                WHEN pa.state_prisma = 1
                                     AND (
                                        ula.ultima_lectura_activa IS NULL
                                        OR ula.ultima_lectura_activa < DATEADD(DAY, -?, GETDATE())
                                     )
                                THEN 1 ELSE 0
                            END AS es_desactualizado
                        FROM PrismaActual pa
                        LEFT JOIN UltimaLecturaActiva ula
                            ON ula.nombre_prisma = pa.nombre_prisma
                    )
                    SELECT 'Prismas' AS tipo_equipo, 'Operativos' AS categoria,
                           COUNT(CASE WHEN state_prisma = 1 THEN 1 END) AS total_equipos
                    FROM Resumen
                    UNION ALL
                    SELECT 'Prismas', 'Inoperativos',
                           COUNT(CASE WHEN state_prisma = 0 THEN 1 END)
                    FROM Resumen
                    UNION ALL
                    SELECT 'Prismas', 'Desactualizados',
                           COUNT(CASE WHEN es_desactualizado = 1 THEN 1 END)
                    FROM Resumen
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
            # 8) INCLINÓMETROS
            # Lógica:
            # - Tabla general: inclinometros → estado_inclinometro (1=Op, 0=Inop)
            # - Tabla encabezado (SIN sufijo de proyecto): inclinometro_encabezado → fecha_inclinometro,
            # - Tabla detalle (CON sufijo): inclinometro_detalle{proyecto_id},
            #   solo se usa para validar que el proyecto tiene este equipo
            # - Si operativo: verificar última lectura
            # - Si inoperativo: no verificar desactualización
            # -----------------------------------------------------------
            tabla_detalle_inclino = f"inclinometro_detalle{proyecto_id}"
            if DashboardModel._tabla_existe(cur, tabla_detalle_inclino):
                sql_inclino = f"""
                    WITH UltimaLectura AS (
                        SELECT
                            id_inclinometro,
                            MAX(fecha_inclinometro) AS ultima_fecha
                        FROM inclinometro_encabezado
                        GROUP BY id_inclinometro
                    ),
                    Resumen AS (
                        SELECT
                            inc.estado_inclinometro,
                            CASE
                                WHEN inc.estado_inclinometro = 1
                                     AND (
                                        ul.ultima_fecha IS NULL
                                        OR ul.ultima_fecha < DATEADD(DAY, -?, GETDATE())
                                     )
                                THEN 1 ELSE 0
                            END AS es_desactualizado
                        FROM inclinometros inc
                        INNER JOIN instrumentacion i
                            ON inc.nombre_inclinometro = i.nombre_equipo
                        LEFT JOIN UltimaLectura ul
                            ON ul.id_inclinometro = inc.id_inclinometro
                        WHERE inc.id_proyecto = ?
                        AND i.id_componente = ?
                    )
                    SELECT 'Inclinometros' AS tipo_equipo, 'Operativos' AS categoria,
                           COUNT(CASE WHEN estado_inclinometro = 1 THEN 1 END) AS total_equipos
                    FROM Resumen
                    UNION ALL
                    SELECT 'Inclinometros', 'Inoperativos',
                           COUNT(CASE WHEN estado_inclinometro = 0 THEN 1 END)
                    FROM Resumen
                    UNION ALL
                    SELECT 'Inclinometros', 'Desactualizados',
                           COUNT(CASE WHEN es_desactualizado = 1 THEN 1 END)
                    FROM Resumen
                """
                cur.execute(sql_inclino, (DIAS_DESACTUALIZADO, proyecto_id, id_componente))
                resultado_final.extend(cur.fetchall())
            else:
                resultado_final.extend(DashboardModel._resumen_sin_detalle(
                    cur, proyecto_id, id_componente, "inclinometros", "nombre_inclinometro", "estado_inclinometro", "Inclinometros"
                ))
            
            # -----------------------------------------------------------
            # 2) PIEZOMETROS DE CUERDA VIBRANTE
            # Lógica:
            # - Tabla general: piezometrocuerdas → estado_piezometro (1=Op, 0=Inop)
            # - Tabla detalle: piezometrocuerda_detalle → fecha_cuerda
            # - Si operativo: verificar última lectura con estado_cuerda = 1
            # - Si inoperativo: no verificar desactualización
            # -----------------------------------------------------------
            tabla_detalle_cuerda = f"piezometrocuerda_detalle{proyecto_id}"
            if DashboardModel._tabla_existe(cur, tabla_detalle_cuerda):
                sql_cuerda = f"""
                    WITH UltimaLectura AS (
                        -- Última lectura activa por piezómetro (solo estado_cuerda = 1)
                        SELECT
                            id_piezometro,
                            MAX(fecha_cuerda) AS ultima_fecha
                        FROM {tabla_detalle_cuerda}
                        WHERE estado_cuerda = 1
                        GROUP BY id_piezometro
                    ),
                    Resumen AS (
                        SELECT
                            pc.estado_piezometro,
                            CASE
                                WHEN pc.estado_piezometro = 1
                                     AND (
                                        ul.ultima_fecha IS NULL
                                        OR ul.ultima_fecha < DATEADD(DAY, -?, GETDATE())
                                     )
                                THEN 1 ELSE 0
                            END AS es_desactualizado
                        FROM piezometrocuerdas pc
                        INNER JOIN instrumentacion i
                            ON pc.nombre_piezometro = i.nombre_equipo
                        LEFT JOIN UltimaLectura ul
                            ON ul.id_piezometro = pc.id_piezometro
                        WHERE pc.id_proyecto = ?
                        AND i.id_componente = ?
                    )
                    SELECT 'PiezometrosCuerda' AS tipo_equipo, 'Operativos' AS categoria,
                           COUNT(CASE WHEN estado_piezometro = 1 THEN 1 END) AS total_equipos
                    FROM Resumen
                    UNION ALL
                    SELECT 'PiezometrosCuerda', 'Inoperativos',
                           COUNT(CASE WHEN estado_piezometro = 0 THEN 1 END)
                    FROM Resumen
                    UNION ALL
                    SELECT 'PiezometrosCuerda', 'Desactualizados',
                           COUNT(CASE WHEN es_desactualizado = 1 THEN 1 END)
                    FROM Resumen
                """
                cur.execute(sql_cuerda, (DIAS_DESACTUALIZADO, proyecto_id, id_componente))
                resultado_final.extend(cur.fetchall())
            else:
                resultado_final.extend(DashboardModel._resumen_sin_detalle(
                    cur, proyecto_id, id_componente, "piezometrocuerdas", "nombre_piezometro", "estado_piezometro", "PiezometrosCuerda"
                ))

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
                    WITH UltimaLectura AS (
                        SELECT
                            id_piezometro,
                            MAX(fecha_piezometro) AS ultima_fecha
                        FROM {tabla_detalle_manual}
                        WHERE estado_manual = 1
                        GROUP BY id_piezometro
                    ),
                    Resumen AS (
                        SELECT
                            pm.estado_piezometro,
                            CASE
                                WHEN pm.estado_piezometro = 1
                                    AND (
                                        ul.ultima_fecha IS NULL
                                        OR ul.ultima_fecha < DATEADD(DAY, -?, GETDATE())
                                    )
                                THEN 1 ELSE 0
                            END AS es_desactualizado
                        FROM piezometromanuales pm
                        INNER JOIN instrumentacion i
                            ON pm.nombre_piezometro = i.nombre_equipo
                        LEFT JOIN UltimaLectura ul
                            ON ul.id_piezometro = pm.id_piezometro
                        WHERE pm.id_proyecto = ?
                        AND i.id_componente = ?
                    )
                    SELECT 'PiezometrosManual' AS tipo_equipo, 'Operativos' AS categoria,
                        COUNT(CASE WHEN estado_piezometro = 1 THEN 1 END) AS total_equipos
                    FROM Resumen
                    UNION ALL
                    SELECT 'PiezometrosManual', 'Inoperativos',
                        COUNT(CASE WHEN estado_piezometro = 0 THEN 1 END)
                    FROM Resumen
                    UNION ALL
                    SELECT 'PiezometrosManual', 'Desactualizados',
                        COUNT(CASE WHEN es_desactualizado = 1 THEN 1 END)
                    FROM Resumen
                """
                cur.execute(sql_manual, (DIAS_DESACTUALIZADO, proyecto_id, id_componente))
                resultado_final.extend(cur.fetchall())
            else:
                resultado_final.extend(DashboardModel._resumen_sin_detalle(
                    cur, proyecto_id, id_componente, "piezometromanuales", "nombre_piezometro", "estado_piezometro", "PiezometrosManual"
                ))

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
                    WITH UltimaLectura AS (
                        SELECT
                            id_celda,
                            MAX(fecha_detalle) AS ultima_fecha
                        FROM {tabla_detalle_celda}
                        WHERE estado_detalle = 1
                        GROUP BY id_celda
                    ),
                    Resumen AS (
                        SELECT
                            c.estado_celda,
                            CASE
                                WHEN c.estado_celda = 1
                                     AND (
                                        ul.ultima_fecha IS NULL
                                        OR ul.ultima_fecha < DATEADD(DAY, -?, GETDATE())
                                     )
                                THEN 1 ELSE 0
                            END AS es_desactualizado
                        FROM celdas c
                        INNER JOIN instrumentacion i
                            ON c.nombre_celda = i.nombre_equipo
                        LEFT JOIN UltimaLectura ul
                            ON ul.id_celda = c.id_celda
                        WHERE c.id_proyecto = ?
                        AND i.id_componente = ?
                    )
                    SELECT 'Celdas' AS tipo_equipo, 'Operativos' AS categoria,
                           COUNT(CASE WHEN estado_celda = 1 THEN 1 END) AS total_equipos
                    FROM Resumen
                    UNION ALL
                    SELECT 'Celdas', 'Inoperativos',
                           COUNT(CASE WHEN estado_celda = 0 THEN 1 END)
                    FROM Resumen
                    UNION ALL
                    SELECT 'Celdas', 'Desactualizados',
                           COUNT(CASE WHEN es_desactualizado = 1 THEN 1 END)
                    FROM Resumen
                """
                cur.execute(sql_celda, (DIAS_DESACTUALIZADO, proyecto_id, id_componente))
                resultado_final.extend(cur.fetchall())
            else:
                resultado_final.extend(DashboardModel._resumen_sin_detalle(
                    cur, proyecto_id, id_componente, "celdas", "nombre_celda", "estado_celda", "Celdas"
                ))

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
                    WITH UltimaLectura AS (
                        SELECT
                            id_pluviometro,
                            MAX(fecha_pluviometro) AS ultima_fecha
                        FROM {tabla_detalle_pluvio}
                        WHERE estado_detalle = 1
                        GROUP BY id_pluviometro
                    ),
                    Resumen AS (
                        SELECT
                            pm.estado_pluviometro,
                            CASE
                                WHEN pm.estado_pluviometro = 1
                                     AND (
                                        ul.ultima_fecha IS NULL
                                        OR ul.ultima_fecha < DATEADD(DAY, -?, GETDATE())
                                     )
                                THEN 1 ELSE 0
                            END AS es_desactualizado
                        FROM pluviometros pm
                        INNER JOIN instrumentacion i
                            ON pm.nombre_pluviometro = i.nombre_equipo
                        LEFT JOIN UltimaLectura ul
                            ON ul.id_pluviometro = pm.id_pluviometro
                        WHERE pm.id_proyecto = ?
                        AND i.id_componente = ?
                    )
                    SELECT 'Pluviometros' AS tipo_equipo, 'Operativos' AS categoria,
                           COUNT(CASE WHEN estado_pluviometro = 1 THEN 1 END) AS total_equipos
                    FROM Resumen
                    UNION ALL
                    SELECT 'Pluviometros', 'Inoperativos',
                           COUNT(CASE WHEN estado_pluviometro = 0 THEN 1 END)
                    FROM Resumen
                    UNION ALL
                    SELECT 'Pluviometros', 'Desactualizados',
                           COUNT(CASE WHEN es_desactualizado = 1 THEN 1 END)
                    FROM Resumen
                """
                cur.execute(sql_pluvio, (DIAS_DESACTUALIZADO, proyecto_id, id_componente))
                resultado_final.extend(cur.fetchall())
            else:
                resultado_final.extend(DashboardModel._resumen_sin_detalle(
                    cur, proyecto_id, id_componente, "pluviometros", "nombre_pluviometro", "estado_pluviometro", "Pluviometros"
                ))

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
                    WITH UltimaLectura AS (
                        SELECT
                            id_acelerografo,
                            MAX(fecha_detalle) AS ultima_fecha
                        FROM {tabla_detalle_acel}
                        WHERE estado_detalle = 1
                        GROUP BY id_acelerografo
                    ),
                    Resumen AS (
                        SELECT
                            a.estado_acelerografo,
                            CASE
                                WHEN a.estado_acelerografo = 1
                                     AND (
                                        ul.ultima_fecha IS NULL
                                        OR ul.ultima_fecha < DATEADD(DAY, -?, GETDATE())
                                     )
                                THEN 1 ELSE 0
                            END AS es_desactualizado
                        FROM acelerografos a
                        INNER JOIN instrumentacion i
                            ON a.nombre_acelerografo = i.nombre_equipo
                        LEFT JOIN UltimaLectura ul
                            ON ul.id_acelerografo = a.id_acelerografo
                        WHERE a.id_proyecto = ?
                        AND i.id_componente = ?
                    )
                    SELECT 'Acelerografos' AS tipo_equipo, 'Operativos' AS categoria,
                           COUNT(CASE WHEN estado_acelerografo = 1 THEN 1 END) AS total_equipos
                    FROM Resumen
                    UNION ALL
                    SELECT 'Acelerografos', 'Inoperativos',
                           COUNT(CASE WHEN estado_acelerografo = 0 THEN 1 END)
                    FROM Resumen
                    UNION ALL
                    SELECT 'Acelerografos', 'Desactualizados',
                           COUNT(CASE WHEN es_desactualizado = 1 THEN 1 END)
                    FROM Resumen
                """
                cur.execute(sql_acel, (DIAS_DESACTUALIZADO, proyecto_id, id_componente))
                resultado_final.extend(cur.fetchall())
            else:
                resultado_final.extend(DashboardModel._resumen_sin_detalle(
                    cur, proyecto_id, id_componente, "acelerografos", "nombre_acelerografo", "estado_acelerografo", "Acelerografos"
                ))
            
            # -----------------------------------------------------------
            # 7) SONDAJES TDR
            # Lógica:
            # - Tabla general: sondajestdr → estado_sondajetdr (1=Op, 0=Inop)
            # - Tabla detalle: sondajetdr_detalle{proyecto_id} → fecha_detalle
            #   (sin columna de estado por lectura, se usa la fecha directamente)
            # - Si operativo: verificar última lectura
            # - Si inoperativo: no verificar desactualización
            # -----------------------------------------------------------
            tabla_detalle_tdr = f"sondajetdr_detalle{proyecto_id}"
            if DashboardModel._tabla_existe(cur, tabla_detalle_tdr):
                sql_tdr = f"""
                    WITH UltimaLectura AS (
                        SELECT
                            id_sondajetdr,
                            MAX(fecha_detalle) AS ultima_fecha
                        FROM {tabla_detalle_tdr}
                        GROUP BY id_sondajetdr
                    ),
                    Resumen AS (
                        SELECT
                            t.estado_sondajetdr,
                            CASE
                                WHEN t.estado_sondajetdr = 1
                                    AND (
                                        ul.ultima_fecha IS NULL
                                        OR ul.ultima_fecha < DATEADD(DAY, -?, GETDATE())
                                    )
                                THEN 1 ELSE 0
                            END AS es_desactualizado
                        FROM sondajestdr t
                        INNER JOIN instrumentacion i
                            ON t.nombre_sondajetdr = i.nombre_equipo
                        LEFT JOIN UltimaLectura ul
                            ON ul.id_sondajetdr = t.id_sondajetdr
                        WHERE t.id_proyecto = ?
                        AND i.id_componente = ?
                    )
                    SELECT 'SondajesTDR' AS tipo_equipo, 'Operativos' AS categoria,
                           COUNT(CASE WHEN estado_sondajetdr = 1 THEN 1 END) AS total_equipos
                    FROM Resumen
                    UNION ALL
                    SELECT 'SondajesTDR', 'Inoperativos',
                           COUNT(CASE WHEN estado_sondajetdr = 0 THEN 1 END)
                    FROM Resumen
                    UNION ALL
                    SELECT 'SondajesTDR', 'Desactualizados',
                           COUNT(CASE WHEN es_desactualizado = 1 THEN 1 END)
                    FROM Resumen
                """
                cur.execute(sql_tdr, (DIAS_DESACTUALIZADO, proyecto_id, id_componente))
                resultado_final.extend(cur.fetchall())
            else:
                resultado_final.extend(DashboardModel._resumen_sin_detalle(
                    cur, proyecto_id, id_componente, "sondajestdr", "nombre_sondajetdr", "estado_sondajetdr", "SondajesTDR"
                ))

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