from services.security.apis.conexiones.connection import Connection

class DashboardModel:
    
    @staticmethod
    def mdlObtenerInstrumentacionProyecto(proyecto_id, id_componente):
        conn = None
        try:
            conn = Connection.connectionDB()
            # La sintaxis CASE WHEN y COUNT es estándar, funciona igual en T-SQL
            sql = """SELECT 'Prismas' AS nameprismas,
                COUNT(CASE WHEN i.tipo_equipo = 'PRISMAS' THEN 1 END) AS canti_prismas,
                'Piezómetros Cuerda Vibrante' AS namecuerda,
                COUNT(CASE WHEN i.tipo_equipo = 'PIEZOMETROCUERDA' THEN 1 END) AS canti_cuerda,
                'Piezómetros Casagrande' AS namepiezomanual,
                COUNT(CASE WHEN i.tipo_equipo = 'PIEZOMETROMANUAL' THEN 1 END) AS canti_piezomanual,
                'Inclinómetros' AS nameinclino,
                COUNT(CASE WHEN i.tipo_equipo = 'INCLINOMETRO' THEN 1 END) AS canti_inclino,
                'Celdas de Asentamiento' AS namecelda,
                COUNT(CASE WHEN i.tipo_equipo = 'CELDA' THEN 1 END) AS canti_celda,
                'Acelerógrafos' AS nameacelero,
                COUNT(CASE WHEN i.tipo_equipo = 'ACELEROGRAFO' THEN 1 END) AS canti_acelero,
                'Sondajes TDR' AS nametdr,
                COUNT(CASE WHEN i.tipo_equipo = 'TDR' THEN 1 END) AS canti_tdr,
                'Pluviómetros' AS namepluvio,
                COUNT(CASE WHEN i.tipo_equipo = 'PLUVIOMETRO' THEN 1 END) AS canti_pluvio,
                'Otros Equipos' AS nameadicional,
                COUNT(CASE WHEN i.tipo_equipo = 'ADICIONAL' THEN 1 END) AS canti_adicional
            FROM instrumentacion i INNER JOIN componentes c ON i.id_componente = c.id_componente
            WHERE c.id_proyecto = ?  AND i.id_componente = ?;"""
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
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            
            # Diccionario de mapeo de estados
            estado_mapeo = {
                0: 'Inoperativos',
                1: 'Operativos'
            }
            
            # Convertir resultados a diccionario {estado: total}
            resultados_dict = {item[0]: item[1] for item in results}
            
            # Estado 1 (Operativos) primero, Estado 0 (Inoperativos) segundo
            resultado_final = [
                (estado_mapeo[estado], resultados_dict.get(estado, 0))
                for estado in [1, 0]  # 👈 Orden: primero 1, luego 0
            ]
            
            return resultado_final

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
    def _resumen_sin_detalle(cur, id_proyecto, id_componente, tipo_equipo_db, tipo_equipo_label):
        """Cuando no existe la tabla de detalle (sin historial de lecturas),
        se usa instrumentacion.estado_instrumentacion como fuente de verdad.
        Como no hay forma de verificar la fecha de última lectura, todos los
        operativos se consideran también desactualizados."""
        sql = """
            SELECT
                COUNT(CASE WHEN i.estado_instrumentacion = 1 THEN 1 END) AS operativos,
                COUNT(CASE WHEN i.estado_instrumentacion = 0 THEN 1 END) AS inoperativos
            FROM instrumentacion i
            INNER JOIN componentes c ON c.id_componente = i.id_componente
            WHERE c.id_proyecto = ? AND i.id_componente = ? AND i.tipo_equipo = ?
        """
        cur.execute(sql, (id_proyecto, id_componente, tipo_equipo_db))
        row = cur.fetchone()
        operativos = row[0] if row else 0
        inoperativos = row[1] if row else 0
        return [
            (tipo_equipo_label, 'Operativos', operativos),
            (tipo_equipo_label, 'Inoperativos', inoperativos),
            (tipo_equipo_label, 'Desactualizados', operativos),
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
                    WITH UltimaLecturaActiva AS (
                        SELECT
                            nombre_prisma,
                            MAX(hora_prisma) AS ultima_lectura_activa
                        FROM {tabla_prismas}
                        WHERE estado_prisma = 1
                        GROUP BY nombre_prisma
                    ),
                    Resumen AS (
                        SELECT
                            i.estado_instrumentacion,
                            CASE
                                WHEN i.estado_instrumentacion = 1
                                     AND (
                                        ula.ultima_lectura_activa IS NULL
                                        OR ula.ultima_lectura_activa < DATEADD(DAY, -?, GETDATE())
                                     )
                                THEN 1 ELSE 0
                            END AS es_desactualizado
                        FROM instrumentacion i
                        INNER JOIN componentes c ON c.id_componente = i.id_componente
                        LEFT JOIN UltimaLecturaActiva ula
                            ON ula.nombre_prisma = i.nombre_equipo
                        WHERE c.id_proyecto = ?
                          AND i.id_componente = ?
                          AND i.tipo_equipo = 'PRISMAS'
                    )
                    SELECT 'Prismas' AS tipo_equipo, 'Operativos' AS categoria,
                           COUNT(CASE WHEN estado_instrumentacion = 1 THEN 1 END) AS total_equipos
                    FROM Resumen
                    UNION ALL
                    SELECT 'Prismas', 'Inoperativos',
                           COUNT(CASE WHEN estado_instrumentacion = 0 THEN 1 END)
                    FROM Resumen
                    UNION ALL
                    SELECT 'Prismas', 'Desactualizados',
                           COUNT(CASE WHEN es_desactualizado = 1 THEN 1 END)
                    FROM Resumen
                """
                cur.execute(sql_prismas, (DIAS_DESACTUALIZADO, proyecto_id, id_componente))
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
                            i.estado_instrumentacion,
                            CASE
                                WHEN i.estado_instrumentacion = 1
                                     AND (
                                        ul.ultima_fecha IS NULL
                                        OR ul.ultima_fecha < DATEADD(DAY, -?, GETDATE())
                                     )
                                THEN 1 ELSE 0
                            END AS es_desactualizado
                        FROM instrumentacion i
                        INNER JOIN componentes c ON c.id_componente = i.id_componente
                        LEFT JOIN inclinometros inc
                            ON inc.nombre_inclinometro = i.nombre_equipo
                        LEFT JOIN UltimaLectura ul
                            ON ul.id_inclinometro = inc.id_inclinometro
                        WHERE c.id_proyecto = ?
                          AND i.id_componente = ?
                          AND i.tipo_equipo = 'INCLINOMETRO'
                    )
                    SELECT 'Inclinometros' AS tipo_equipo, 'Operativos' AS categoria,
                           COUNT(CASE WHEN estado_instrumentacion = 1 THEN 1 END) AS total_equipos
                    FROM Resumen
                    UNION ALL
                    SELECT 'Inclinometros', 'Inoperativos',
                           COUNT(CASE WHEN estado_instrumentacion = 0 THEN 1 END)
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
                    cur, proyecto_id, id_componente, "INCLINOMETRO", "Inclinometros"
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
                        SELECT
                            id_piezometro,
                            MAX(fecha_cuerda) AS ultima_fecha
                        FROM {tabla_detalle_cuerda}
                        WHERE estado_cuerda = 1
                        GROUP BY id_piezometro
                    ),
                    Resumen AS (
                        SELECT
                            i.estado_instrumentacion,
                            CASE
                                WHEN i.estado_instrumentacion = 1
                                     AND (
                                        ul.ultima_fecha IS NULL
                                        OR ul.ultima_fecha < DATEADD(DAY, -?, GETDATE())
                                     )
                                THEN 1 ELSE 0
                            END AS es_desactualizado
                        FROM instrumentacion i
                        INNER JOIN componentes c ON c.id_componente = i.id_componente
                        LEFT JOIN piezometrocuerdas pc
                            ON pc.nombre_piezometro = i.nombre_equipo
                        LEFT JOIN UltimaLectura ul
                            ON ul.id_piezometro = pc.id_piezometro
                        WHERE c.id_proyecto = ?
                          AND i.id_componente = ?
                          AND i.tipo_equipo = 'PIEZOMETROCUERDA'
                    )
                    SELECT 'PiezometrosCuerda' AS tipo_equipo, 'Operativos' AS categoria,
                           COUNT(CASE WHEN estado_instrumentacion = 1 THEN 1 END) AS total_equipos
                    FROM Resumen
                    UNION ALL
                    SELECT 'PiezometrosCuerda', 'Inoperativos',
                           COUNT(CASE WHEN estado_instrumentacion = 0 THEN 1 END)
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
                    cur, proyecto_id, id_componente, "PIEZOMETROCUERDA", "PiezometrosCuerda"
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
                            i.estado_instrumentacion,
                            CASE
                                WHEN i.estado_instrumentacion = 1
                                    AND (
                                        ul.ultima_fecha IS NULL
                                        OR ul.ultima_fecha < DATEADD(DAY, -?, GETDATE())
                                    )
                                THEN 1 ELSE 0
                            END AS es_desactualizado
                        FROM instrumentacion i
                        INNER JOIN componentes c ON c.id_componente = i.id_componente
                        LEFT JOIN piezometromanuales pmm
                            ON pmm.nombre_piezometro = i.nombre_equipo
                        LEFT JOIN UltimaLectura ul
                            ON ul.id_piezometro = pmm.id_piezometro
                        WHERE c.id_proyecto = ?
                          AND i.id_componente = ?
                          AND i.tipo_equipo = 'PIEZOMETROMANUAL'
                    )
                    SELECT 'PiezometrosManual' AS tipo_equipo, 'Operativos' AS categoria,
                        COUNT(CASE WHEN estado_instrumentacion = 1 THEN 1 END) AS total_equipos
                    FROM Resumen
                    UNION ALL
                    SELECT 'PiezometrosManual', 'Inoperativos',
                        COUNT(CASE WHEN estado_instrumentacion = 0 THEN 1 END)
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
                    cur, proyecto_id, id_componente, "PIEZOMETROMANUAL", "PiezometrosManual"
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
                            i.estado_instrumentacion,
                            CASE
                                WHEN i.estado_instrumentacion = 1
                                     AND (
                                        ul.ultima_fecha IS NULL
                                        OR ul.ultima_fecha < DATEADD(DAY, -?, GETDATE())
                                     )
                                THEN 1 ELSE 0
                            END AS es_desactualizado
                        FROM instrumentacion i
                        INNER JOIN componentes c ON c.id_componente = i.id_componente
                        LEFT JOIN celdas cel
                            ON cel.nombre_celda = i.nombre_equipo
                        LEFT JOIN UltimaLectura ul
                            ON ul.id_celda = cel.id_celda
                        WHERE c.id_proyecto = ?
                          AND i.id_componente = ?
                          AND i.tipo_equipo = 'CELDA'
                    )
                    SELECT 'Celdas' AS tipo_equipo, 'Operativos' AS categoria,
                           COUNT(CASE WHEN estado_instrumentacion = 1 THEN 1 END) AS total_equipos
                    FROM Resumen
                    UNION ALL
                    SELECT 'Celdas', 'Inoperativos',
                           COUNT(CASE WHEN estado_instrumentacion = 0 THEN 1 END)
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
                    cur, proyecto_id, id_componente, "CELDA", "Celdas"
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
                            i.estado_instrumentacion,
                            CASE
                                WHEN i.estado_instrumentacion = 1
                                     AND (
                                        ul.ultima_fecha IS NULL
                                        OR ul.ultima_fecha < DATEADD(DAY, -?, GETDATE())
                                     )
                                THEN 1 ELSE 0
                            END AS es_desactualizado
                        FROM instrumentacion i
                        INNER JOIN componentes c ON c.id_componente = i.id_componente
                        LEFT JOIN pluviometros plv
                            ON plv.nombre_pluviometro = i.nombre_equipo
                        LEFT JOIN UltimaLectura ul
                            ON ul.id_pluviometro = plv.id_pluviometro
                        WHERE c.id_proyecto = ?
                          AND i.id_componente = ?
                          AND i.tipo_equipo = 'PLUVIOMETRO'
                    )
                    SELECT 'Pluviometros' AS tipo_equipo, 'Operativos' AS categoria,
                           COUNT(CASE WHEN estado_instrumentacion = 1 THEN 1 END) AS total_equipos
                    FROM Resumen
                    UNION ALL
                    SELECT 'Pluviometros', 'Inoperativos',
                           COUNT(CASE WHEN estado_instrumentacion = 0 THEN 1 END)
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
                    cur, proyecto_id, id_componente, "PLUVIOMETRO", "Pluviometros"
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
                            i.estado_instrumentacion,
                            CASE
                                WHEN i.estado_instrumentacion = 1
                                     AND (
                                        ul.ultima_fecha IS NULL
                                        OR ul.ultima_fecha < DATEADD(DAY, -?, GETDATE())
                                     )
                                THEN 1 ELSE 0
                            END AS es_desactualizado
                        FROM instrumentacion i
                        INNER JOIN componentes c ON c.id_componente = i.id_componente
                        LEFT JOIN acelerografos ace
                            ON ace.nombre_acelerografo = i.nombre_equipo
                        LEFT JOIN UltimaLectura ul
                            ON ul.id_acelerografo = ace.id_acelerografo
                        WHERE c.id_proyecto = ?
                          AND i.id_componente = ?
                          AND i.tipo_equipo = 'ACELEROGRAFO'
                    )
                    SELECT 'Acelerografos' AS tipo_equipo, 'Operativos' AS categoria,
                           COUNT(CASE WHEN estado_instrumentacion = 1 THEN 1 END) AS total_equipos
                    FROM Resumen
                    UNION ALL
                    SELECT 'Acelerografos', 'Inoperativos',
                           COUNT(CASE WHEN estado_instrumentacion = 0 THEN 1 END)
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
                    cur, proyecto_id, id_componente, "ACELEROGRAFO", "Acelerografos"
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
                            i.estado_instrumentacion,
                            CASE
                                WHEN i.estado_instrumentacion = 1
                                    AND (
                                        ul.ultima_fecha IS NULL
                                        OR ul.ultima_fecha < DATEADD(DAY, -?, GETDATE())
                                    )
                                THEN 1 ELSE 0
                            END AS es_desactualizado
                        FROM instrumentacion i
                        INNER JOIN componentes c ON c.id_componente = i.id_componente
                        LEFT JOIN sondajestdr tdr
                            ON tdr.nombre_sondajetdr = i.nombre_equipo
                        LEFT JOIN UltimaLectura ul
                            ON ul.id_sondajetdr = tdr.id_sondajetdr
                        WHERE c.id_proyecto = ?
                          AND i.id_componente = ?
                          AND i.tipo_equipo = 'TDR'
                    )
                    SELECT 'SondajesTDR' AS tipo_equipo, 'Operativos' AS categoria,
                           COUNT(CASE WHEN estado_instrumentacion = 1 THEN 1 END) AS total_equipos
                    FROM Resumen
                    UNION ALL
                    SELECT 'SondajesTDR', 'Inoperativos',
                           COUNT(CASE WHEN estado_instrumentacion = 0 THEN 1 END)
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
                    cur, proyecto_id, id_componente, "TDR", "SondajesTDR"
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