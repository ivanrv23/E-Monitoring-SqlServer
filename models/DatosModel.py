import pandas as pd
import pyodbc
from services.security.apis.conexiones.connection import Connection
from datetime import datetime

class DatosModel:
    
    @staticmethod
    def mdlObtenerListaPrismasMarcados(tabla, zona, prismas):
        placeholders = ','.join(['?'] * len(prismas))
        sql = f"""SELECT nombre_equipo FROM instrumentacion AS it 
        INNER JOIN componentes AS co ON co.id_componente = it.id_componente
        WHERE it.nombre_equipo IN ({placeholders}) AND co.nombre_componente = ? AND tabla_equipo = ?;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, prismas + [zona, tabla])
            results = cur.fetchall()
            return results if results else None
        except Exception as e:
            print("Error al obtener prismas auto marcados:", e)
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlObtenerDataPrismasPositiva(tabla, idzona, tipoequipo, prismas, estado, decimales):
        placeholders = ', '.join(['?' for _ in prismas])
        params = [idzona] + [tipoequipo] + prismas + [idzona] + [tipoequipo] + prismas
        
        sql = f"""WITH cte_prisma AS (
            SELECT it.tipo_equipo, p.id_prisma, p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, p.elevacion_target,
                p.distancia_prisma, p.angulo_horizontal, p.angulo_vertical,
                FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS norte_inicial,
                FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS este_inicial,
                FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS elevacion_inicial,
                FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS tiempo_inicial,
                LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS norte_anterior,
                LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS este_anterior,
                LAG(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS elevacion_anterior,
                LAG(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS tiempo_anterior,
                ROW_NUMBER() OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS row_num
            FROM {tabla} AS p INNER JOIN instrumentacion AS it ON it.nombre_equipo = p.nombre_prisma
            INNER JOIN componentes AS co ON co.id_componente = it.id_componente
            WHERE co.id_componente = ? AND it.tipo_equipo = ? AND it.nombre_equipo IN ({placeholders})
            AND it.estado_instrumentacion = {estado} AND p.estado_prisma = 1
            AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
        )
        SELECT it.tipo_equipo, p.nombre_prisma, p.hora_prisma, ROUND(p.este_target, {decimales}) AS este_target,
            ROUND(p.norte_target, {decimales}) AS norte_target, ROUND(p.elevacion_target, {decimales}) AS elevacion_target,
            ROUND(p.distancia_prisma, {decimales}) AS distancia_prisma,
        '-' AS DI3D, '-' AS DA3D, '-' AS VI3D, '-' AS VA3D, p.angulo_horizontal, p.angulo_vertical, 'Omitido' AS modo, p.id_prisma
        FROM {tabla} AS p INNER JOIN instrumentacion AS it ON it.nombre_equipo = p.nombre_prisma
        INNER JOIN componentes AS co ON co.id_componente = it.id_componente
        WHERE co.id_componente = ? AND it.tipo_equipo = ? AND it.nombre_equipo IN ({placeholders})
        AND it.estado_instrumentacion = {estado} AND p.estado_prisma = 0

        UNION ALL

        SELECT tipo_equipo, nombre_prisma, hora_prisma, ROUND(este_target, {decimales}) AS este_target,
            ROUND(norte_target, {decimales}) AS norte_target, ROUND(elevacion_target, {decimales}) AS elevacion_target,
            ROUND(distancia_prisma, {decimales}) AS distancia_prisma,
            CAST(CASE 
                WHEN row_num = 1 THEN 0 
                ELSE 
                    ROUND(SQRT(
                        POWER(este_target - este_anterior, 2) +
                        POWER(norte_target - norte_anterior, 2) +
                        POWER(elevacion_target - elevacion_anterior, 2)
                    ) * 100, {decimales})
            END AS VARCHAR(50)) AS DI3D,
            
            CAST(ROUND(SQRT(
                POWER(este_target - este_inicial, 2) +
                POWER(norte_target - norte_inicial, 2) +
                POWER(elevacion_target - elevacion_inicial, 2)
            ) * 100, {decimales}) AS VARCHAR(50)) AS DA3D,
            
            CAST(CASE 
                WHEN row_num = 1 THEN 0 
                ELSE 
                    ROUND(SQRT(
                        POWER(este_target - este_anterior, 2) +
                        POWER(norte_target - norte_anterior, 2) +
                        POWER(elevacion_target - elevacion_anterior, 2)
                    ) * 100 / NULLIF(DATEDIFF(SECOND, tiempo_anterior, hora_prisma) / 86400.0, 0), {decimales})
            END AS VARCHAR(50)) AS VI3D,
            
            CAST(CASE 
                WHEN row_num = 1 THEN 0
                ELSE 
                    ROUND((SQRT(
                        POWER(este_target - este_inicial, 2) +
                        POWER(norte_target - norte_inicial, 2) +
                        POWER(elevacion_target - elevacion_inicial, 2)
                    ) * 100) / NULLIF(DATEDIFF(SECOND, tiempo_inicial, hora_prisma) / 86400.0, 0), {decimales})
            END AS VARCHAR(50)) AS VA3D, 
            
            angulo_horizontal, angulo_vertical, 'Activo' AS modo, id_prisma
        FROM cte_prisma ORDER BY nombre_prisma, hora_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            results = cur.fetchall()
            return results if results else None
        except Exception as e:
            print("Error al obtener data prismas positiva:", e)
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlObtenerDataPrismasAmbas(tabla, idzona, tipoequipo, prismas, estado, decimales):
        placeholders = ', '.join(['?' for _ in prismas])
        params = [idzona] + [tipoequipo] + prismas + [estado] + [idzona] + [tipoequipo] + prismas + [estado]
        
        sql = f"""WITH cte_prisma AS (
            SELECT it.tipo_equipo, p.id_prisma, p.nombre_prisma, p.hora_prisma, este_target, p.norte_target, p.elevacion_target,
                p.distancia_prisma, p.angulo_horizontal, p.angulo_vertical,
                FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS norte_inicial,
                FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS este_inicial,
                FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS elevacion_inicial,
                FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS tiempo_inicial,
                LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS norte_anterior,
                LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS este_anterior,
                LAG(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS elevacion_anterior,
                LAG(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS tiempo_anterior,
                ROW_NUMBER() OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS row_num
            FROM {tabla} AS p INNER JOIN instrumentacion AS it ON it.nombre_equipo = p.nombre_prisma
            INNER JOIN componentes AS co ON co.id_componente = it.id_componente
            WHERE co.id_componente = ? AND it.tipo_equipo = ? AND it.nombre_equipo IN ({placeholders})
            AND it.estado_instrumentacion = ? AND p.estado_prisma = 1
            AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
        ),
        cte_distancias AS (
            SELECT nombre_prisma, hora_prisma, este_target, norte_target, elevacion_target, distancia_prisma,
                tiempo_inicial, angulo_horizontal, angulo_vertical, id_prisma, tipo_equipo,
                CASE 
                    WHEN row_num = 1 THEN 0 
                    ELSE 
                        SQRT(
                            POWER(este_target - este_anterior, 2) +
                            POWER(norte_target - norte_anterior, 2) +
                            POWER(elevacion_target - elevacion_anterior, 2)
                        ) * 100
                END AS DI3D,
                SQRT(
                    POWER(este_target - este_inicial, 2) +
                    POWER(norte_target - norte_inicial, 2) +
                    POWER(elevacion_target - elevacion_inicial, 2)
                ) * 100 AS DA3D,
                tiempo_anterior, hora_prisma AS tiempo_actual, row_num
            FROM cte_prisma
        )
        SELECT it.tipo_equipo, p.nombre_prisma, p.hora_prisma, 
            ROUND(p.este_target, {decimales}) AS este_target,
            ROUND(p.norte_target, {decimales}) AS norte_target, 
            ROUND(p.elevacion_target, {decimales}) AS elevacion_target,
            ROUND(p.distancia_prisma, {decimales}) AS distancia_prisma, 
            '-' AS DI3D, '-' AS DA3D, '-' AS VI3D, '-' AS VA3D,
            p.angulo_horizontal, p.angulo_vertical, 'Omitido' AS modo, p.id_prisma
        FROM {tabla} AS p INNER JOIN instrumentacion AS it ON it.nombre_equipo = p.nombre_prisma
        INNER JOIN componentes AS co ON co.id_componente = it.id_componente
        WHERE co.id_componente = ? AND it.tipo_equipo = ? AND it.nombre_equipo IN ({placeholders})
        AND it.estado_instrumentacion = ? AND p.estado_prisma = 0

        UNION ALL

        SELECT tipo_equipo, nombre_prisma, hora_prisma, 
            ROUND(este_target, {decimales}), ROUND(norte_target, {decimales}),
            ROUND(elevacion_target, {decimales}), ROUND(distancia_prisma, {decimales}),
            CAST(ROUND(DI3D, {decimales}) AS VARCHAR(50)) AS DI3D, 
            CAST(ROUND(DA3D, {decimales}) AS VARCHAR(50)) AS DA3D,
            CAST(
                CASE 
                    WHEN row_num = 1 THEN 0
                    ELSE 
                        ROUND((DA3D - LAG(DA3D) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma))
                        / NULLIF(DATEDIFF(SECOND, tiempo_anterior, tiempo_actual) / 86400.0, 0), {decimales})
                END 
            AS VARCHAR(50)) AS VI3D,
            CAST(
                CASE
                    WHEN row_num = 1 THEN 0
                    ELSE 
                        ROUND(DA3D / NULLIF(DATEDIFF(SECOND, tiempo_inicial, tiempo_actual) / 86400.0, 0), {decimales})
                END 
            AS VARCHAR(50)) AS VA3D, 
            angulo_horizontal, angulo_vertical, 'Activo' AS modo, id_prisma
        FROM cte_distancias ORDER BY nombre_prisma, hora_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            results = cur.fetchall()
            return results if results else None
        except Exception as e:
            print("Error al obtener data prismas ambas:", e)
            return None
        finally:
            if conn: conn.close()
            
    @staticmethod
    def mdlObtenerInclinometros(proyecto_id, idzona, inclinometros, decimales):
        placeholders = ', '.join(['?' for _ in inclinometros])
        params = [idzona] + inclinometros
        sql = f"""SELECT it.tipo_equipo, i.nombre_inclinometro, i.tipo_inclinometro, en.fecha_inclinometro,
            ROUND(de.profundidad_detalle, {decimales}) AS profundidad_detalle, de.apositivo_detalle, de.anegativo_detalle,
            de.bpositivo_detalle, de.bnegativo_detalle, ROUND(i.este_inclinometro, {decimales}) AS este_inclinometro,
            ROUND(i.norte_inclinometro, {decimales}) AS norte_inclinometro,
            ROUND(i.elevacion_inclinometro, {decimales}) AS elevacion_inclinometro, de.id_detalle
        FROM inclinometros AS i INNER JOIN inclinometro_encabezado AS en ON i.id_inclinometro = en.id_inclinometro 
        INNER JOIN inclinometro_detalle{proyecto_id} AS de ON en.id_encabezado = de.id_encabezado
        INNER JOIN instrumentacion AS it ON it.id_equipo = i.id_inclinometro
        INNER JOIN componentes AS co ON co.id_componente = it.id_componente
        WHERE co.id_componente = ? AND it.tipo_equipo = 'INCLINOMETRO' AND it.id_equipo IN ({placeholders})
        ORDER BY i.nombre_inclinometro, en.fecha_inclinometro;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            results = cur.fetchall()
            return results if results else None
        except Exception as e:
            print("Error al obtener data inclinometros:", e)
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlObtenerFormulaPiezometroCuerda(idpiezometro):
        sql = f"""SELECT p.id_formula, f.sentencia FROM piezometrocuerdas p INNER JOIN formulas_piezometros f
        ON p.id_formula = f.id_formula WHERE p.id_piezometro = ?;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idpiezometro,))
            results = cur.fetchone()
            return results if results else [0, None]
        except Exception as e:
            print("Error al obtener formula cuerda:", e)
            return [0, None]
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlObtenerPiezometrosCuerda(proyecto_id, idzona, idpiezometro, decimales):
        sql = f"""SELECT it.tipo_equipo, p.nombre_piezometro, d.fecha_cuerda, ROUND(d.frecuencia_cuerda, {decimales}) AS frecuencia_cuerda,
            ROUND(d.temperatura_cuerda, {decimales}) AS temperatura_cuerda,
            CASE 
                WHEN d.estado_cuerda = 1 THEN
                    CAST(ROUND(d.presion_barometrica, {decimales}) AS VARCHAR(50))
                ELSE '-'
            END AS presion_barometrica,
            CASE 
                WHEN d.estado_cuerda = 1 THEN
                    CAST(ROUND(CASE 
                        WHEN p.tipo_piezometro = 1 THEN d.medida_calculada 
                        ELSE d.medida_calculada - p.elevacion_piezometro 
                    END, {decimales}) AS VARCHAR(50))
                ELSE '-'
            END AS MCA,
            ROUND(p.elevacion_piezometro, {decimales}) AS instalacion,
            CASE 
                WHEN d.estado_cuerda = 1 THEN
                    CAST(ROUND(CASE 
                        WHEN p.tipo_piezometro = 1 THEN p.elevacion_piezometro + d.medida_calculada
                        ELSE d.medida_calculada
                    END, {decimales}) AS VARCHAR(50))
                ELSE '-'
            END AS nivel_agua, ROUND(p.este_piezometro, {decimales}) AS este_piezometro, ROUND(p.norte_piezometro, {decimales}) AS norte_piezometro,
            ROUND(COALESCE(
                (SELECT TOP 1 c2.nivel_cota FROM cotas_piezometricas c2 WHERE c2.id_piezometro = d.id_piezometro 
                AND c2.tipo_piezometro = 'PCV' AND c2.fecha_cota <= d.fecha_cuerda ORDER BY c2.fecha_cota DESC),
                (SELECT TOP 1 c3.nivel_cota FROM cotas_piezometricas c3 WHERE c3.id_piezometro = d.id_piezometro 
                AND c3.tipo_piezometro = 'PCV' ORDER BY c3.fecha_cota ASC)
            ), {decimales}) AS elevacion, ROUND(p.fundacion_piezometro, {decimales}) AS fundacion_piezometro,
            CASE
                WHEN d.estado_cuerda = 1 THEN 'Activo'
                ELSE 'Omitido'
            END AS estado, d.observacion_cuerda, d.id_cuerda,
            ROUND(COALESCE(
                (SELECT TOP 1 c2.id_cota FROM cotas_piezometricas c2 WHERE c2.id_piezometro = d.id_piezometro 
                AND c2.tipo_piezometro = 'PCV' AND c2.fecha_cota <= d.fecha_cuerda ORDER BY c2.fecha_cota DESC),
                (SELECT TOP 1 c3.id_cota FROM cotas_piezometricas c3 WHERE c3.id_piezometro = d.id_piezometro 
                AND c3.tipo_piezometro = 'PCV' ORDER BY c3.fecha_cota ASC)
            ), {decimales}) AS idcota
        FROM piezometrocuerdas p INNER JOIN piezometrocuerda_detalle{proyecto_id} d ON p.id_piezometro = d.id_piezometro
        INNER JOIN instrumentacion AS it ON it.id_equipo = d.id_piezometro
        INNER JOIN componentes AS co ON co.id_componente = it.id_componente
        WHERE co.id_componente = ? AND it.id_equipo = ? AND it.tipo_equipo = 'PIEZOMETROCUERDA'
        ORDER BY p.nombre_piezometro, d.fecha_cuerda;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idzona, idpiezometro))
            results = cur.fetchall()
            return results if results else None
        except Exception as e:
            print("Error al obtener data piezometros cuerda:", e)
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlObtenerPiezometrosCuerdaFormula(proyecto_id, idzona, idpiezometro, formula, decimales):
        sql = f"""WITH piezometros AS (SELECT it.tipo_equipo, p.nombre_piezometro, d.fecha_cuerda,
            d.frecuencia_cuerda, d.temperatura_cuerda,
            ({formula}) AS presion_barometrica, p.elevacion_piezometro AS instalacion,
            d.estado_cuerda, p.tipo_piezometro, d.medida_calculada,
            p.este_piezometro, p.norte_piezometro,
            COALESCE(
                (SELECT TOP 1 c2.nivel_cota FROM cotas_piezometricas c2 WHERE c2.id_piezometro = d.id_piezometro 
                AND c2.tipo_piezometro = 'PCV' AND c2.fecha_cota <= d.fecha_cuerda ORDER BY c2.fecha_cota DESC),
                (SELECT TOP 1 c3.nivel_cota FROM cotas_piezometricas c3 WHERE c3.id_piezometro = d.id_piezometro 
                AND c3.tipo_piezometro = 'PCV' ORDER BY c3.fecha_cota ASC)
            ) AS elevacion, p.fundacion_piezometro, d.observacion_cuerda, d.id_cuerda, factor_conversion,
            COALESCE(
                (SELECT TOP 1 c2.id_cota FROM cotas_piezometricas c2 WHERE c2.id_piezometro = d.id_piezometro 
                AND c2.tipo_piezometro = 'PCV' AND c2.fecha_cota <= d.fecha_cuerda ORDER BY c2.fecha_cota DESC),
                (SELECT TOP 1 c3.id_cota FROM cotas_piezometricas c3 WHERE c3.id_piezometro = d.id_piezometro 
                AND c3.tipo_piezometro = 'PCV' ORDER BY c3.fecha_cota ASC)
            ) AS idcota
        FROM piezometrocuerdas p INNER JOIN piezometrocuerda_detalle{proyecto_id} d ON p.id_piezometro = d.id_piezometro
        INNER JOIN instrumentacion AS it ON it.id_equipo = d.id_piezometro
        INNER JOIN componentes AS co ON co.id_componente = it.id_componente
        WHERE co.id_componente = ? AND it.id_equipo = ? AND it.tipo_equipo = 'PIEZOMETROCUERDA'
        )
        SELECT tipo_equipo, nombre_piezometro, fecha_cuerda, frecuencia_cuerda, temperatura_cuerda,
            CASE 
                WHEN estado_cuerda = 1 THEN
                    CAST(ROUND(presion_barometrica, {decimales}) AS VARCHAR(50))
                ELSE '-'
            END AS presion,
            CASE 
                WHEN estado_cuerda = 1 THEN
                    CAST(ROUND((presion_barometrica * factor_conversion), {decimales}) AS VARCHAR(50))
                ELSE '-'
            END AS MCA, instalacion,
            CASE 
                WHEN estado_cuerda = 1 THEN
                    CAST(ROUND((instalacion + (presion_barometrica * factor_conversion)), {decimales}) AS VARCHAR(50))
                ELSE '-'
            END AS nivel_agua,
            este_piezometro, norte_piezometro, elevacion, fundacion_piezometro,
            CASE
                WHEN estado_cuerda = 1 THEN 'Activo'
                ELSE 'Omitido'
            END AS estado, observacion_cuerda, id_cuerda, idcota
        FROM piezometros ORDER BY nombre_piezometro, fecha_cuerda;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idzona, idpiezometro))
            results = cur.fetchall()
            return results if results else None
        except Exception as e:
            print("Error al obtener data formula cuerda:", e)
            return None
        finally:
            if conn: conn.close()
            
    @staticmethod
    def mdlObtenerPiezometrosManuales(proyecto_id, idzona, piezometros, decimales):
        placeholders = ', '.join(['?' for _ in piezometros])
        params = [idzona] + piezometros
        sql = f"""WITH cte_cota AS (
            SELECT it.tipo_equipo, p.nombre_piezometro, p.tipo_piezometro, d.fecha_piezometro, d.medida_piezometro,
            d.observacion_detalle, p.stickup_piezometro, p.este_piezometro, p.norte_piezometro,
            p.elevacion_piezometro AS instalacion, p.fundacion_piezometro, d.id_detalle,
            COALESCE(
                (SELECT TOP 1 c2.nivel_cota FROM cotas_piezometricas c2 WHERE c2.id_piezometro = d.id_piezometro 
                AND c2.tipo_piezometro = 'PVC' AND c2.fecha_cota <= d.fecha_piezometro ORDER BY c2.fecha_cota DESC),
                (SELECT TOP 1 c3.nivel_cota FROM cotas_piezometricas c3 WHERE c3.id_piezometro = d.id_piezometro
                AND c3.tipo_piezometro = 'PVC' ORDER BY c3.fecha_cota ASC)
            ) AS elevacion,
            COALESCE(
                (SELECT TOP 1 c2.id_cota FROM cotas_piezometricas c2 WHERE c2.id_piezometro = d.id_piezometro 
                AND c2.tipo_piezometro = 'PVC' AND c2.fecha_cota <= d.fecha_piezometro ORDER BY c2.fecha_cota DESC),
                (SELECT TOP 1 c3.id_cota FROM cotas_piezometricas c3 WHERE c3.id_piezometro = d.id_piezometro
                AND c3.tipo_piezometro = 'PVC' ORDER BY c3.fecha_cota ASC)
            ) AS idcota, d.estado_manual
            FROM piezometromanuales p INNER JOIN piezometromanual_detalle{proyecto_id} d ON p.id_piezometro = d.id_piezometro
            INNER JOIN instrumentacion AS it ON it.id_equipo = p.id_piezometro
            INNER JOIN componentes AS co ON co.id_componente = it.id_componente
            WHERE co.id_componente = ? AND it.id_equipo IN ({placeholders}) AND it.tipo_equipo = 'PIEZOMETROMANUAL'
        )
        SELECT tipo_equipo, nombre_piezometro, fecha_piezometro,
            ROUND(CASE
                WHEN tipo_piezometro = 1 THEN medida_piezometro
                ELSE stickup_piezometro + elevacion - medida_piezometro
            END, {decimales}) AS nivel_piezometrico,
            ROUND(stickup_piezometro + elevacion - instalacion, {decimales}) AS profundidad, ROUND(elevacion, {decimales}) AS elevacion,
            CASE
                WHEN estado_manual = 1 THEN 
                    CAST(ROUND(CASE
                        WHEN tipo_piezometro = 1 THEN stickup_piezometro + elevacion - medida_piezometro
                        ELSE medida_piezometro
                    END, {decimales}) AS VARCHAR(50))
                ELSE '-'
            END AS nivel_agua, ROUND(stickup_piezometro, {decimales}) AS stickup_piezometro, ROUND(este_piezometro, {decimales}) AS este_piezometro,
            ROUND(norte_piezometro, {decimales}) AS norte_piezometro, ROUND(instalacion, {decimales}) AS instalacion,
            ROUND(fundacion_piezometro, {decimales}) AS fundacion_piezometro,
            CASE
                WHEN estado_manual = 1 THEN 'Activo'
                ELSE 'Omitido'
            END AS estado, observacion_detalle, id_detalle, idcota
        FROM cte_cota ORDER BY nombre_piezometro, fecha_piezometro;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            results = cur.fetchall()
            return results if results else None
        except Exception as e:
            print("Error al obtener data piezometros manuales:", e)
            return None
        finally:
            if conn: conn.close()
            
    @staticmethod
    def mdlObtenerPluviometros(proyecto_id, idzona, pluviometros, decimales):
        placeholders = ', '.join(['?' for _ in pluviometros])
        params = [idzona] + pluviometros
        sql = f"""SELECT it.tipo_equipo, pm.nombre_pluviometro, pd.fecha_pluviometro,
            ROUND(pd.medida_pluviometro, {decimales}) AS medida_pluviometro, ROUND(pm.este_pluviometro, {decimales}) AS este_pluviometro,
            ROUND(pm.norte_pluviometro, {decimales}) AS norte_pluviometro, ROUND(pm.elevacion_pluviometro, {decimales}) AS elevacion_pluviometro,
            pd.observacion_pluviometro, 
            CASE
                WHEN pd.estado_detalle = 1 THEN 'Activo'
                ELSE 'Omitido'
            END AS estado,  pd.id_detalle
        FROM pluviometro_detalle{proyecto_id} pd INNER JOIN pluviometros pm ON pd.id_pluviometro = pm.id_pluviometro
        INNER JOIN instrumentacion AS it ON it.id_equipo = pd.id_pluviometro
        INNER JOIN componentes AS co ON co.id_componente = it.id_componente
        WHERE co.id_componente = ? AND it.id_equipo IN ({placeholders}) AND it.tipo_equipo = 'PLUVIOMETRO'
        ORDER BY pm.nombre_pluviometro, pd.fecha_pluviometro;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            results = cur.fetchall()
            return results if results else None
        except Exception as e:
            print("Error al obtener data pluviometros:", e)
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlObtenerCotasTerreno(proyecto_id, idzona, terrenos, decimales):
        placeholders = ', '.join(['?' for _ in terrenos])
        params = [idzona] + terrenos
        sql = f"""SELECT it.tipo_equipo, ct.nombre_terreno, cd.fecha_detalle, ROUND(cd.nivel_detalle, {decimales}) AS nivel_detalle,
            cd.observacion_detalle, 
             CASE
                WHEN cd.estado_detalle = 1 THEN 'Activo'
                ELSE 'Omitido'
            END AS estado, cd.id_detalle
        FROM cotaterreno_detalle{proyecto_id} cd INNER JOIN cotasterreno ct ON cd.id_terreno = ct.id_terreno
        INNER JOIN instrumentacion AS it ON it.id_equipo = cd.id_terreno
        INNER JOIN componentes AS co ON co.id_componente = it.id_componente
        WHERE co.id_componente = ? AND it.id_equipo IN ({placeholders}) AND it.tipo_equipo = 'COTATERRENO'
        ORDER BY ct.nombre_terreno, cd.fecha_detalle;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            results = cur.fetchall()
            return results if results else None
        except Exception as e:
            print("Error al obtener data cotas terreno:", e)
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlObtenerCeldasAsentamiento(proyecto_id, idzona, celdas, decimales):
        placeholders = ', '.join(['?' for _ in celdas])
        params = [idzona] + celdas
        sql = f"""SELECT it.tipo_equipo, ca.nombre_celda, cd.fecha_detalle, ROUND(cd.frecuencia_digits, {decimales}) AS frecuencia_digits,
            ROUND(cd.frecuencia_hz, {decimales}) AS frecuencia_hz, ROUND(cd.temperatura_detalle, {decimales}) AS temperatura_detalle,
            ROUND(cd.medida_calculada, {decimales}) AS medida_calculada,
            CASE 
                WHEN cd.estado_detalle = 1 THEN 
                    CAST(ROUND(ca.instalacion_celda - abs(cd.medida_calculada), {decimales}) AS VARCHAR(50))
                ELSE '-'
            END AS cota_piezometrica, ROUND(ca.instalacion_celda, {decimales}) AS instalacion_celda, ROUND(ca.rango_celda, {decimales}) AS rango_celda,
            ROUND(ca.este_celda, {decimales}) AS este_celda, ROUND(ca.norte_celda, {decimales}) AS norte_celda, ROUND(ca.fundacion_celda, {decimales}) AS fundacion_celda,
            ROUND(COALESCE(
                (SELECT TOP 1 c2.nivel_cota FROM cotas_celdas c2 WHERE c2.id_celda = cd.id_celda
                AND c2.fecha_cota <= cd.fecha_detalle ORDER BY c2.fecha_cota DESC),
                (SELECT TOP 1 c3.nivel_cota FROM cotas_celdas c3 WHERE c3.id_celda = cd.id_celda 
                ORDER BY c3.fecha_cota ASC)
            ), {decimales}) AS superficie_celda,
            CASE
                WHEN cd.estado_detalle = 1 THEN 'Activo'
                ELSE 'Omitido'
            END AS estado, cd.observacion_detalle, cd.id_detalle
        FROM celda_detalle{proyecto_id} cd INNER JOIN celdas ca ON cd.id_celda = ca.id_celda
        INNER JOIN instrumentacion AS it ON it.id_equipo = cd.id_celda
        INNER JOIN componentes AS co ON co.id_componente = it.id_componente
        WHERE co.id_componente = ? AND it.id_equipo IN ({placeholders}) AND it.tipo_equipo = 'CELDA'
        ORDER BY ca.nombre_celda, cd.fecha_detalle;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            results = cur.fetchall()
            return results if results else None
        except Exception as e:
            print("Error al obtener data celdas:", e)
            return None
        finally:
            if conn: conn.close()
            
    @staticmethod
    def mdlObtenerAcelerografos(proyecto_id, idzona, acelerografos, decimales):
        placeholders = ', '.join(['?' for _ in acelerografos])
        params = [idzona] + acelerografos
        sql = f"""SELECT it.tipo_equipo, a.nombre_acelerografo, ad.fecha_detalle, ROUND(ad.magnitud_detalle, {decimales}) AS magnitud_detalle,
            ROUND(ad.distancia_detalle, {decimales}) AS distancia_detalle,
            ROUND(a.este_acelerografo, {decimales}) AS este_acelerografo, ROUND(a.norte_acelerografo, {decimales}) AS norte_acelerografo,
            ROUND(a.elevacion_acelerografo, {decimales}) AS elevacion_acelerografo, ad.observacion_detalle, 
            CASE
                WHEN ad.estado_detalle = 1 THEN 'Activo'
                ELSE 'Omitido'
            END AS estado, ad.id_detalle
        FROM acelerografo_detalle{proyecto_id} ad INNER JOIN acelerografos a ON ad.id_acelerografo = a.id_acelerografo
        INNER JOIN instrumentacion AS it ON it.id_equipo = ad.id_acelerografo
        INNER JOIN componentes AS co ON co.id_componente = it.id_componente
        WHERE co.id_componente = ? AND it.id_equipo IN ({placeholders}) AND it.tipo_equipo = 'ACELEROGRAFO'
        ORDER BY a.nombre_acelerografo, ad.fecha_detalle;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            results = cur.fetchall()
            return results if results else None
        except Exception as e:
            print("Error al obtener data acelerografos:", e)
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlObtenerSondajestdr(proyecto_id, idzona, sondajestdr, decimales):
        placeholders = ', '.join(['?' for _ in sondajestdr])
        params = [idzona] + sondajestdr
        sql = f"""SELECT it.tipo_equipo, s.nombre_sondajetdr, sd.fecha_detalle, ROUND(sd.profundidad_detalle, {decimales}) AS profundidad_detalle,
            ROUND(sd.impedancia_detalle, {decimales}) AS impedancia_detalle, ROUND(s.este_sondajetdr, {decimales}) AS este_sondajetdr,
            ROUND(s.norte_sondajetdr, {decimales}) AS norte_sondajetdr, ROUND(s.elevacion_sondajetdr, {decimales}) AS elevacion_sondajetdr,
            sd.observacion_detalle, sd.id_detalle
        FROM sondajetdr_detalle{proyecto_id} sd INNER JOIN sondajestdr s ON sd.id_sondajetdr = s.id_sondajetdr
        INNER JOIN instrumentacion AS it ON it.id_equipo = sd.id_sondajetdr
        INNER JOIN componentes AS co ON co.id_componente = it.id_componente
        WHERE co.id_componente = ? AND it.id_equipo IN ({placeholders}) AND it.tipo_equipo = 'TDR'
        ORDER BY s.nombre_sondajetdr, sd.fecha_detalle;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            results = cur.fetchall()
            return results if results else None
        except Exception as e:
            print("Error al obtener data sondajes tdr:", e)
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlObtenerEquiposAdicionales(proyecto_id, idzona, equipos, decimales):
        placeholders = ', '.join(['?' for _ in equipos])
        params = [proyecto_id] + [idzona] + equipos
        sql = f"""SELECT it.tipo_equipo, e.nombre_equipo, e.tipo_equipo, ROUND(e.este_equipo, {decimales}) AS este_equipo,
            ROUND(e.norte_equipo, {decimales}) AS norte_equipo, ROUND(e.elevacion_equipo, {decimales}) AS elevacion_equipo,
            e.descripcion_equipo, e.id_equipo
        FROM equipos e INNER JOIN instrumentacion AS it ON it.id_equipo = e.id_equipo
        INNER JOIN componentes AS co ON co.id_componente = it.id_componente
        WHERE co.id_proyecto = ? AND co.id_componente = ? AND it.id_equipo IN ({placeholders}) AND it.tipo_equipo = 'ADICIONAL';"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            results = cur.fetchall()
            return results if results else None
        except Exception as e:
            print("Error al obtener equipos adicionales:", e)
            return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlRegistrarPrismasAutomatizadosUno(idproyecto, datos_procesados):
        respuesta = True
        nombretabla = f"prismas{idproyecto}"
        
        # 1. USO DE DATETIME2(0)
        sqltable = f"""IF OBJECT_ID(N'dbo.{nombretabla}', N'U') IS NULL
        CREATE TABLE {nombretabla} (
            id_prisma INT IDENTITY(1,1) NOT NULL,
            state_prisma INT NOT NULL DEFAULT ((1)),
            estado_prisma INT NOT NULL DEFAULT ((1)), 
            nombre_prisma NVARCHAR(500) NOT NULL, 
            perfil_prisma NVARCHAR(MAX), 
            hora_prisma DATETIME2(0) NOT NULL, 
            angulo_horizontal NVARCHAR(50), 
            angulo_vertical NVARCHAR(50), 
            distancia_prisma FLOAT DEFAULT ((0)), 
            tipoppm_prisma NVARCHAR(50), 
            ppm_prisma FLOAT DEFAULT ((0)), 
            presion_prisma FLOAT DEFAULT ((0)), 
            temperatura_prisma FLOAT DEFAULT ((0)), 
            constante_prisma FLOAT DEFAULT ((0)), 
            este_target FLOAT NOT NULL, 
            norte_target FLOAT NOT NULL, 
            elevacion_target FLOAT NOT NULL, 
            altura_reflector FLOAT DEFAULT ((0)), 
            altura_instrumento FLOAT DEFAULT ((0)), 
            este_estacion FLOAT DEFAULT ((0)), 
            norte_estacion FLOAT DEFAULT ((0)), 
            altura_estacion FLOAT DEFAULT ((0)), 
            medicion_prisma FLOAT DEFAULT ((0)), 
            diferencia_tiempocorto FLOAT DEFAULT ((0)),
            diferencia_tiempolargo FLOAT DEFAULT ((0)), 
            diferencia_limitevelocidad FLOAT DEFAULT ((0)), 
            distancia_horizontal FLOAT DEFAULT ((0)), 
            diferencia_atipica FLOAT DEFAULT ((0)), 
            desplaza_longitudinal FLOAT DEFAULT ((0)), 
            desplaza_transversal FLOAT DEFAULT ((0)), 
            desplaza_altura FLOAT DEFAULT ((0)), 
            grupo_puntos NVARCHAR(MAX),
            CONSTRAINT [PK_{nombretabla}] PRIMARY KEY CLUSTERED (id_prisma)
        );"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            cursor.execute(sqltable)
            conn.commit()
            
            # 2. FORMATO ISO CON 'T' PARA COMPARACIÓN EXACTA
            cursor.execute(f"SELECT nombre_prisma, hora_prisma FROM {nombretabla};")
            existing_records = set()
            for row in cursor.fetchall():
                f_str = row[1].strftime('%Y-%m-%dT%H:%M:%S') if hasattr(row[1], 'strftime') else str(row[1])
                existing_records.add((row[0], f_str))
            
            lote_tamano = 5000
            lote_registros = []
            
            sql_insert = f"""
                INSERT INTO {nombretabla} (
                    state_prisma, nombre_prisma, perfil_prisma, hora_prisma, angulo_horizontal,
                    angulo_vertical, distancia_prisma, tipoppm_prisma, ppm_prisma, presion_prisma,
                    temperatura_prisma, constante_prisma, este_target, norte_target, elevacion_target,
                    altura_reflector, altura_instrumento, este_estacion, norte_estacion, altura_estacion,
                    medicion_prisma, diferencia_tiempocorto, diferencia_tiempolargo,
                    diferencia_limitevelocidad, distancia_horizontal, diferencia_atipica,
                    desplaza_longitudinal, desplaza_transversal, desplaza_altura, grupo_puntos
                ) VALUES ({', '.join(['?'] * 30)})
            """
            
            for fila in datos_procesados.itertuples(index=False):
                # fila[3] viene con 'T' desde tu controller
                if (fila[1], str(fila[3])) not in existing_records:
                    datos_limpios = [None if pd.isna(x) else x for x in fila]
                    lote_registros.append(tuple(datos_limpios))
                
                # 3. CONTADOR SEGURO (len)
                if len(lote_registros) >= lote_tamano:
                    cursor.executemany(sql_insert, lote_registros)
                    conn.commit()
                    lote_registros = []

            if lote_registros:
                cursor.executemany(sql_insert, lote_registros)
                conn.commit()

        except Exception as e:
            print(f"Error detallado SQL UNO: {e}")
            respuesta = False
            if conn: conn.rollback()
        finally:
            if conn: conn.close()
        return respuesta
    
    @staticmethod
    def mdlRemplazarPrismasAutomatizadosUno(idproyecto, datos_procesados, componente=None):
        respuesta = True
        nombretabla = f"prismas{idproyecto}"
        
        sqltable = f"""IF OBJECT_ID(N'dbo.{nombretabla}', N'U') IS NULL
        CREATE TABLE {nombretabla} (
            id_prisma INT IDENTITY(1,1) NOT NULL,
            state_prisma INT NOT NULL DEFAULT ((1)),
            estado_prisma INT NOT NULL DEFAULT ((1)), 
            nombre_prisma NVARCHAR(500) NOT NULL, 
            perfil_prisma NVARCHAR(MAX), 
            hora_prisma DATETIME2(0) NOT NULL, 
            angulo_horizontal NVARCHAR(50), 
            angulo_vertical NVARCHAR(50), 
            distancia_prisma FLOAT DEFAULT ((0)), 
            tipoppm_prisma NVARCHAR(50), 
            ppm_prisma FLOAT DEFAULT ((0)), 
            presion_prisma FLOAT DEFAULT ((0)), 
            temperatura_prisma FLOAT DEFAULT ((0)), 
            constante_prisma FLOAT DEFAULT ((0)), 
            este_target FLOAT NOT NULL, 
            norte_target FLOAT NOT NULL, 
            elevacion_target FLOAT NOT NULL, 
            altura_reflector FLOAT DEFAULT ((0)), 
            altura_instrumento FLOAT DEFAULT ((0)), 
            este_estacion FLOAT DEFAULT ((0)), 
            norte_estacion FLOAT DEFAULT ((0)), 
            altura_estacion FLOAT DEFAULT ((0)), 
            medicion_prisma FLOAT DEFAULT ((0)), 
            diferencia_tiempocorto FLOAT DEFAULT ((0)),
            diferencia_tiempolargo FLOAT DEFAULT ((0)), 
            diferencia_limitevelocidad FLOAT DEFAULT ((0)), 
            distancia_horizontal FLOAT DEFAULT ((0)), 
            diferencia_atipica FLOAT DEFAULT ((0)), 
            desplaza_longitudinal FLOAT DEFAULT ((0)), 
            desplaza_transversal FLOAT DEFAULT ((0)), 
            desplaza_altura FLOAT DEFAULT ((0)), 
            grupo_puntos NVARCHAR(MAX),
            CONSTRAINT [PK_{nombretabla}] PRIMARY KEY CLUSTERED (id_prisma)
        );"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            cursor.execute(sqltable)
            conn.commit()
            
            if componente:
                cursor.execute(f"SELECT nombre_equipo FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'PRISMAS'", (componente,))
                rows = cursor.fetchall()
                nombres_equipos = [row[0] for row in rows]
                if nombres_equipos:
                    placeholders = ','.join(['?'] * len(nombres_equipos))
                    cursor.execute(f"DELETE FROM {nombretabla} WHERE nombre_prisma IN ({placeholders})", nombres_equipos)
                cursor.execute(f"DELETE FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'PRISMAS'", (componente,))
            
            cursor.execute(f"SELECT nombre_prisma, hora_prisma FROM {nombretabla};")
            existing_records = set()
            for row in cursor.fetchall():
                f_str = row[1].strftime('%Y-%m-%dT%H:%M:%S') if hasattr(row[1], 'strftime') else str(row[1])
                existing_records.add((row[0], f_str))
            
            lote_tamano = 5000
            lote_registros = []
            
            sql_insert = f"""
                INSERT INTO {nombretabla} (
                    state_prisma, nombre_prisma, perfil_prisma, hora_prisma, angulo_horizontal,
                    angulo_vertical, distancia_prisma, tipoppm_prisma, ppm_prisma, presion_prisma,
                    temperatura_prisma, constante_prisma, este_target, norte_target, elevacion_target,
                    altura_reflector, altura_instrumento, este_estacion, norte_estacion, altura_estacion,
                    medicion_prisma, diferencia_tiempocorto, diferencia_tiempolargo,
                    diferencia_limitevelocidad, distancia_horizontal, diferencia_atipica,
                    desplaza_longitudinal, desplaza_transversal, desplaza_altura, grupo_puntos
                ) VALUES ({', '.join(['?'] * 30)})
            """
            
            for fila in datos_procesados.itertuples(index=False):
                if (fila[1], str(fila[3])) not in existing_records:
                    datos_limpios = [None if pd.isna(x) else x for x in fila]
                    lote_registros.append(tuple(datos_limpios))
                
                if len(lote_registros) >= lote_tamano:
                    cursor.executemany(sql_insert, lote_registros)
                    conn.commit()
                    lote_registros = []

            if lote_registros:
                cursor.executemany(sql_insert, lote_registros)
                conn.commit()

        except Exception as e:
            print(f"Error detallado Reemplazar UNO: {e}")
            respuesta = False
            if conn: conn.rollback()
        finally:
            if conn: conn.close()
        return respuesta
    
    @staticmethod
    def mdlRegistrarPrismasAutomatizadosDos(idproyecto, datos_procesados):
        respuesta = True
        nombretabla = f"prismas{idproyecto}"
        sqltable = f"""IF OBJECT_ID(N'dbo.{nombretabla}', N'U') IS NULL
        CREATE TABLE {nombretabla} (
            id_prisma INT IDENTITY(1,1) NOT NULL,
            state_prisma INT NOT NULL DEFAULT ((1)),
            estado_prisma INT NOT NULL DEFAULT ((1)), 
            nombre_prisma NVARCHAR(500) NOT NULL, 
            perfil_prisma NVARCHAR(MAX), 
            hora_prisma DATETIME2(0) NOT NULL, 
            angulo_horizontal NVARCHAR(50), 
            angulo_vertical NVARCHAR(50), 
            distancia_prisma FLOAT DEFAULT ((0)), 
            tipoppm_prisma NVARCHAR(50), 
            ppm_prisma FLOAT DEFAULT ((0)), 
            presion_prisma FLOAT DEFAULT ((0)), 
            temperatura_prisma FLOAT DEFAULT ((0)), 
            constante_prisma FLOAT DEFAULT ((0)), 
            este_target FLOAT NOT NULL, 
            norte_target FLOAT NOT NULL, 
            elevacion_target FLOAT NOT NULL, 
            altura_reflector FLOAT DEFAULT ((0)), 
            altura_instrumento FLOAT DEFAULT ((0)), 
            este_estacion FLOAT DEFAULT ((0)), 
            norte_estacion FLOAT DEFAULT ((0)), 
            altura_estacion FLOAT DEFAULT ((0)), 
            medicion_prisma FLOAT DEFAULT ((0)), 
            diferencia_tiempocorto FLOAT DEFAULT ((0)),
            diferencia_tiempolargo FLOAT DEFAULT ((0)), 
            diferencia_limitevelocidad FLOAT DEFAULT ((0)), 
            distancia_horizontal FLOAT DEFAULT ((0)), 
            diferencia_atipica FLOAT DEFAULT ((0)), 
            desplaza_longitudinal FLOAT DEFAULT ((0)), 
            desplaza_transversal FLOAT DEFAULT ((0)), 
            desplaza_altura FLOAT DEFAULT ((0)), 
            grupo_puntos NVARCHAR(MAX),
            CONSTRAINT [PK_{nombretabla}] PRIMARY KEY CLUSTERED (id_prisma)
        );"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            cursor.execute(sqltable)
            conn.commit()
            
            cursor.execute(f"SELECT nombre_prisma, hora_prisma FROM {nombretabla};")
            existing_records = set()
            for row in cursor.fetchall():
                f_str = row[1].strftime('%Y-%m-%dT%H:%M:%S') if hasattr(row[1], 'strftime') else str(row[1])
                existing_records.add((row[0], f_str))
            
            lote_tamano = 5000
            lote_registros = []
            
            sql_insert = f"""
                INSERT INTO {nombretabla} (
                    nombre_prisma, angulo_horizontal, angulo_vertical, distancia_prisma, altura_reflector,
                    altura_instrumento, este_target, norte_target, elevacion_target, hora_prisma)
                VALUES ({', '.join(['?'] * 10)})
            """
            
            for fila in datos_procesados.itertuples(index=False):
                # Asumiendo que fila[9] es hora_prisma
                if (fila[0], str(fila[9])) not in existing_records:
                    datos_limpios = [None if pd.isna(x) else x for x in fila]
                    lote_registros.append(tuple(datos_limpios))
                
                if len(lote_registros) >= lote_tamano:
                    cursor.executemany(sql_insert, lote_registros)
                    conn.commit()
                    lote_registros = []

            if lote_registros:
                cursor.executemany(sql_insert, lote_registros)
                conn.commit()

        except Exception as e:
            print(f"Error detallado SQL DOS: {e}")
            respuesta = False
            if conn: conn.rollback()
        finally:
            if conn: conn.close()
        return respuesta
    
    @staticmethod
    def mdlRemplazarPrismasAutomatizadosDos(idproyecto, datos_procesados, componente=None):
        # Mismos cambios: DATETIME2(0), formato con T, contador seguro
        respuesta = True
        nombretabla = f"prismas{idproyecto}"
        sqltable = f"""IF OBJECT_ID(N'dbo.{nombretabla}', N'U') IS NULL
        CREATE TABLE {nombretabla} (
            id_prisma INT IDENTITY(1,1) NOT NULL,
            state_prisma INT NOT NULL DEFAULT ((1)),
            estado_prisma INT NOT NULL DEFAULT ((1)), 
            nombre_prisma NVARCHAR(500) NOT NULL, 
            perfil_prisma NVARCHAR(MAX), 
            hora_prisma DATETIME2(0) NOT NULL, 
            angulo_horizontal NVARCHAR(50), 
            angulo_vertical NVARCHAR(50), 
            distancia_prisma FLOAT DEFAULT ((0)), 
            tipoppm_prisma NVARCHAR(50), 
            ppm_prisma FLOAT DEFAULT ((0)), 
            presion_prisma FLOAT DEFAULT ((0)), 
            temperatura_prisma FLOAT DEFAULT ((0)), 
            constante_prisma FLOAT DEFAULT ((0)), 
            este_target FLOAT NOT NULL, 
            norte_target FLOAT NOT NULL, 
            elevacion_target FLOAT NOT NULL, 
            altura_reflector FLOAT DEFAULT ((0)), 
            altura_instrumento FLOAT DEFAULT ((0)), 
            este_estacion FLOAT DEFAULT ((0)), 
            norte_estacion FLOAT DEFAULT ((0)), 
            altura_estacion FLOAT DEFAULT ((0)), 
            medicion_prisma FLOAT DEFAULT ((0)), 
            diferencia_tiempocorto FLOAT DEFAULT ((0)),
            diferencia_tiempolargo FLOAT DEFAULT ((0)), 
            diferencia_limitevelocidad FLOAT DEFAULT ((0)), 
            distancia_horizontal FLOAT DEFAULT ((0)), 
            diferencia_atipica FLOAT DEFAULT ((0)), 
            desplaza_longitudinal FLOAT DEFAULT ((0)), 
            desplaza_transversal FLOAT DEFAULT ((0)), 
            desplaza_altura FLOAT DEFAULT ((0)), 
            grupo_puntos NVARCHAR(MAX),
            CONSTRAINT [PK_{nombretabla}] PRIMARY KEY CLUSTERED (id_prisma)
        );"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            cursor.execute(sqltable)
            conn.commit()
            
            if componente:
                cursor.execute(f"SELECT nombre_equipo FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'PRISMAS'", (componente,))
                rows = cursor.fetchall()
                nombres_equipos = [row[0] for row in rows]
                if nombres_equipos:
                    placeholders = ','.join(['?'] * len(nombres_equipos))
                    cursor.execute(f"DELETE FROM {nombretabla} WHERE nombre_prisma IN ({placeholders})", nombres_equipos)
                cursor.execute(f"DELETE FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'PRISMAS'", (componente,))
            
            cursor.execute(f"SELECT nombre_prisma, hora_prisma FROM {nombretabla};")
            existing_records = set()
            for row in cursor.fetchall():
                f_str = row[1].strftime('%Y-%m-%dT%H:%M:%S') if hasattr(row[1], 'strftime') else str(row[1])
                existing_records.add((row[0], f_str))
            
            lote_tamano = 5000
            lote_registros = []
            
            sql_insert = f"""
                INSERT INTO {nombretabla} (
                    nombre_prisma, angulo_horizontal, angulo_vertical, distancia_prisma, altura_reflector,
                    altura_instrumento, este_target, norte_target, elevacion_target, hora_prisma)
                VALUES ({', '.join(['?'] * 10)})
            """
            
            for fila in datos_procesados.itertuples(index=False):
                if (fila[0], str(fila[9])) not in existing_records:
                    datos_limpios = [None if pd.isna(x) else x for x in fila]
                    lote_registros.append(tuple(datos_limpios))
                
                if len(lote_registros) >= lote_tamano:
                    cursor.executemany(sql_insert, lote_registros)
                    conn.commit()
                    lote_registros = []

            if lote_registros:
                cursor.executemany(sql_insert, lote_registros)
                conn.commit()

        except Exception as e:
            print(f"Error detallado Reemplazar DOS: {e}")
            respuesta = False
            if conn: conn.rollback()
        finally:
            if conn: conn.close()
        return respuesta
    
    @staticmethod
    def mdlRegistrarPrismasAutomatizadosTres(idproyecto, datos_procesados, encode, delimitador):
        # CAMBIO: Usar T en SQL y en el parseo manual del CSV
        equipos_unicos = set()
        nombretabla = f"prismas{idproyecto}"
        sqltable = f"""IF OBJECT_ID(N'dbo.{nombretabla}', N'U') IS NULL
        CREATE TABLE {nombretabla} (
            id_prisma INT IDENTITY(1,1) NOT NULL,
            state_prisma INT NOT NULL DEFAULT ((1)),
            estado_prisma INT NOT NULL DEFAULT ((1)), 
            nombre_prisma NVARCHAR(500) NOT NULL, 
            perfil_prisma NVARCHAR(MAX), 
            hora_prisma DATETIME2(0) NOT NULL, 
            angulo_horizontal NVARCHAR(50), 
            angulo_vertical NVARCHAR(50), 
            distancia_prisma FLOAT DEFAULT ((0)), 
            tipoppm_prisma NVARCHAR(50), 
            ppm_prisma FLOAT DEFAULT ((0)), 
            presion_prisma FLOAT DEFAULT ((0)), 
            temperatura_prisma FLOAT DEFAULT ((0)), 
            constante_prisma FLOAT DEFAULT ((0)), 
            este_target FLOAT NOT NULL, 
            norte_target FLOAT NOT NULL, 
            elevacion_target FLOAT NOT NULL, 
            altura_reflector FLOAT DEFAULT ((0)), 
            altura_instrumento FLOAT DEFAULT ((0)), 
            este_estacion FLOAT DEFAULT ((0)), 
            norte_estacion FLOAT DEFAULT ((0)), 
            altura_estacion FLOAT DEFAULT ((0)), 
            medicion_prisma FLOAT DEFAULT ((0)), 
            diferencia_tiempocorto FLOAT DEFAULT ((0)),
            diferencia_tiempolargo FLOAT DEFAULT ((0)), 
            diferencia_limitevelocidad FLOAT DEFAULT ((0)), 
            distancia_horizontal FLOAT DEFAULT ((0)), 
            diferencia_atipica FLOAT DEFAULT ((0)), 
            desplaza_longitudinal FLOAT DEFAULT ((0)), 
            desplaza_transversal FLOAT DEFAULT ((0)), 
            desplaza_altura FLOAT DEFAULT ((0)), 
            grupo_puntos NVARCHAR(MAX),
            CONSTRAINT [PK_{nombretabla}] PRIMARY KEY CLUSTERED (id_prisma)
        );"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            cursor.execute(sqltable)
            conn.commit()
            
            cursor.execute(f"SELECT nombre_prisma, hora_prisma FROM {nombretabla};")
            existing_records = set()
            for row in cursor.fetchall():
                f_str = row[1].strftime('%Y-%m-%dT%H:%M:%S') if hasattr(row[1], 'strftime') else str(row[1])
                existing_records.add((row[0], f_str))
            
            # ... (Lectura del CSV se mantiene) ...
            columnas_omitir = [2, 11, 14, 15, 16, 17]
            try:
                df = pd.read_csv(datos_procesados, encoding=encode, sep=delimitador)
            except:
                df = pd.read_csv(datos_procesados, encoding=encode, sep=delimitador, engine='python')
                
            df = df.dropna(how='all')
            todas_columnas = list(range(len(df.columns)))
            columnas_mantener = [col for col in todas_columnas if col not in columnas_omitir]
            for col in columnas_mantener:
                if df.iloc[:, col].dtype == object:
                    df.iloc[:, col] = df.iloc[:, col].apply(lambda x: x.strip() if isinstance(x, str) else x)
            df_filtrado = df.iloc[:, columnas_mantener]
            
            lote_tamano = 5000
            lote_registros = []
            
            sql_insert = f"""INSERT INTO {nombretabla} (nombre_prisma, grupo_puntos, estado_prisma,
                    hora_prisma, angulo_horizontal, angulo_vertical, distancia_prisma, este_target, norte_target, elevacion_target,
                    desplaza_transversal, desplaza_altura, perfil_prisma, medicion_prisma, tipoppm_prisma, ppm_prisma, presion_prisma, temperatura_prisma,
                    constante_prisma, altura_reflector, altura_instrumento, este_estacion, norte_estacion, altura_estacion, diferencia_tiempocorto,
                    diferencia_tiempolargo, diferencia_limitevelocidad, desplaza_longitudinal, distancia_horizontal, diferencia_atipica)
                    VALUES ({', '.join(['?'] * 30)})"""
            
            for _, fila in df_filtrado.iterrows():
                equipos_unicos.add(str(fila.iloc[0]))
                
                fecha_str = str(fila.iloc[3])
                try:
                    fecha_limpia = fecha_str.split('+')[0].strip()
                    if '.' in fecha_limpia:
                        fecha_obj = datetime.strptime(fecha_limpia, '%Y-%m-%d %H:%M:%S.%f')
                    else:
                        fecha_obj = datetime.strptime(fecha_limpia, '%Y-%m-%d %H:%M:%S')
                    
                    # CAMBIO CLAVE: Formatear con T para que coincida con existing_records
                    fechahora = fecha_obj.strftime('%Y-%m-%dT%H:%M:%S')
                except ValueError:
                    fechahora = fecha_limpia
                
                if (fila.iloc[0], fechahora) not in existing_records:
                    datos_fila = fila.tolist()
                    datos_fila[3] = fechahora # Actualizamos con el formato T
                    
                    datos_limpios = [None if pd.isna(x) else x for x in datos_fila]
                    lote_registros.append(tuple(datos_limpios))

                if len(lote_registros) >= lote_tamano:
                    cursor.executemany(sql_insert, lote_registros)
                    conn.commit()
                    lote_registros = []

            if lote_registros:
                cursor.executemany(sql_insert, lote_registros)
                conn.commit()
            
            return True, list(equipos_unicos)
        except Exception as e:
            print(f"Error detallado SQL TRES: {e}")
            if conn: conn.rollback()
            return False, []
        finally:
            if conn: conn.close()
            
    @staticmethod
    def mdlRemplazarPrismasAutomatizadosTres(idproyecto, datos_procesados, encode, delimitador, componente=None):
        # Mismos cambios que RegistrarTres
        equipos_unicos = set()
        nombretabla = f"prismas{idproyecto}"
        
        sqltable = f"""IF OBJECT_ID(N'dbo.{nombretabla}', N'U') IS NULL
        CREATE TABLE {nombretabla} (
            id_prisma INT IDENTITY(1,1) NOT NULL,
            state_prisma INT NOT NULL DEFAULT ((1)),
            estado_prisma INT NOT NULL DEFAULT ((1)), 
            nombre_prisma NVARCHAR(500) NOT NULL, 
            perfil_prisma NVARCHAR(MAX), 
            hora_prisma DATETIME2(0) NOT NULL, 
            angulo_horizontal NVARCHAR(50), 
            angulo_vertical NVARCHAR(50), 
            distancia_prisma FLOAT DEFAULT ((0)), 
            tipoppm_prisma NVARCHAR(50), 
            ppm_prisma FLOAT DEFAULT ((0)), 
            presion_prisma FLOAT DEFAULT ((0)), 
            temperatura_prisma FLOAT DEFAULT ((0)), 
            constante_prisma FLOAT DEFAULT ((0)), 
            este_target FLOAT NOT NULL, 
            norte_target FLOAT NOT NULL, 
            elevacion_target FLOAT NOT NULL, 
            altura_reflector FLOAT DEFAULT ((0)), 
            altura_instrumento FLOAT DEFAULT ((0)), 
            este_estacion FLOAT DEFAULT ((0)), 
            norte_estacion FLOAT DEFAULT ((0)), 
            altura_estacion FLOAT DEFAULT ((0)), 
            medicion_prisma FLOAT DEFAULT ((0)), 
            diferencia_tiempocorto FLOAT DEFAULT ((0)),
            diferencia_tiempolargo FLOAT DEFAULT ((0)), 
            diferencia_limitevelocidad FLOAT DEFAULT ((0)), 
            distancia_horizontal FLOAT DEFAULT ((0)), 
            diferencia_atipica FLOAT DEFAULT ((0)), 
            desplaza_longitudinal FLOAT DEFAULT ((0)), 
            desplaza_transversal FLOAT DEFAULT ((0)), 
            desplaza_altura FLOAT DEFAULT ((0)), 
            grupo_puntos NVARCHAR(MAX),
            CONSTRAINT [PK_{nombretabla}] PRIMARY KEY CLUSTERED (id_prisma)
        );"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            cursor.execute(sqltable)
            conn.commit()
            
            if componente:
                cursor.execute(f"SELECT nombre_equipo FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'PRISMAS'", (componente,))
                rows = cursor.fetchall()
                nombres_equipos = [row[0] for row in rows]
                if nombres_equipos:
                    placeholders = ','.join(['?'] * len(nombres_equipos))
                    cursor.execute(f"DELETE FROM {nombretabla} WHERE nombre_prisma IN ({placeholders})", nombres_equipos)
                cursor.execute(f"DELETE FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'PRISMAS'", (componente,))
            
            cursor.execute(f"SELECT nombre_prisma, hora_prisma FROM {nombretabla};")
            existing_records = set()
            for row in cursor.fetchall():
                f_str = row[1].strftime('%Y-%m-%dT%H:%M:%S') if hasattr(row[1], 'strftime') else str(row[1])
                existing_records.add((row[0], f_str))
            
            # ... CSV Parsing ...
            columnas_omitir = [2, 11, 14, 15, 16, 17]
            try:
                df = pd.read_csv(datos_procesados, encoding=encode, sep=delimitador)
            except:
                df = pd.read_csv(datos_procesados, encoding=encode, sep=delimitador, engine='python')
                
            df = df.dropna(how='all')
            todas_columnas = list(range(len(df.columns)))
            columnas_mantener = [col for col in todas_columnas if col not in columnas_omitir]
            for col in columnas_mantener:
                if df.iloc[:, col].dtype == object:
                    df.iloc[:, col] = df.iloc[:, col].apply(lambda x: x.strip() if isinstance(x, str) else x)
            df_filtrado = df.iloc[:, columnas_mantener]
            
            lote_tamano = 5000
            lote_registros = []
            
            sql_insert = f"""INSERT INTO {nombretabla} (nombre_prisma, grupo_puntos, estado_prisma,
                    hora_prisma, angulo_horizontal, angulo_vertical, distancia_prisma, este_target, norte_target, elevacion_target,
                    desplaza_transversal, desplaza_altura, perfil_prisma, medicion_prisma, tipoppm_prisma, ppm_prisma, presion_prisma, temperatura_prisma,
                    constante_prisma, altura_reflector, altura_instrumento, este_estacion, norte_estacion, altura_estacion, diferencia_tiempocorto,
                    diferencia_tiempolargo, diferencia_limitevelocidad, desplaza_longitudinal, distancia_horizontal, diferencia_atipica)
                    VALUES ({', '.join(['?'] * 30)})"""
            
            for _, fila in df_filtrado.iterrows():
                equipos_unicos.add(str(fila.iloc[0]))
                
                fecha_str = str(fila.iloc[3])
                try:
                    fecha_limpia = fecha_str.split('+')[0].strip()
                    if '.' in fecha_limpia:
                        fecha_obj = datetime.strptime(fecha_limpia, '%Y-%m-%d %H:%M:%S.%f')
                    else:
                        fecha_obj = datetime.strptime(fecha_limpia, '%Y-%m-%d %H:%M:%S')
                    fechahora = fecha_obj.strftime('%Y-%m-%dT%H:%M:%S')
                except ValueError:
                    fechahora = fecha_limpia
                
                if (fila.iloc[0], fechahora) not in existing_records:
                    datos_fila = fila.tolist()
                    datos_fila[3] = fechahora
                    datos_limpios = [None if pd.isna(x) else x for x in datos_fila]
                    lote_registros.append(tuple(datos_limpios))

                if len(lote_registros) >= lote_tamano:
                    cursor.executemany(sql_insert, lote_registros)
                    conn.commit()
                    lote_registros = []

            if lote_registros:
                cursor.executemany(sql_insert, lote_registros)
                conn.commit()
            
            return True, list(equipos_unicos)
        except Exception as e:
            print(f"Error detallado Reemplazar TRES: {e}")
            if conn: conn.rollback()
            return True, []
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlRegistrarPrismasAutomatizadosCuatro(idproyecto, datos_procesados):
        respuesta = True
        nombretabla = f"prismas{idproyecto}"
        sqltable = f"""IF OBJECT_ID(N'dbo.{nombretabla}', N'U') IS NULL
        CREATE TABLE {nombretabla} (
            id_prisma INT IDENTITY(1,1) NOT NULL,
            state_prisma INT NOT NULL DEFAULT ((1)),
            estado_prisma INT NOT NULL DEFAULT ((1)), 
            nombre_prisma NVARCHAR(500) NOT NULL, 
            perfil_prisma NVARCHAR(MAX), 
            hora_prisma DATETIME2(0) NOT NULL, 
            angulo_horizontal NVARCHAR(50), 
            angulo_vertical NVARCHAR(50), 
            distancia_prisma FLOAT DEFAULT ((0)), 
            tipoppm_prisma NVARCHAR(50), 
            ppm_prisma FLOAT DEFAULT ((0)), 
            presion_prisma FLOAT DEFAULT ((0)), 
            temperatura_prisma FLOAT DEFAULT ((0)), 
            constante_prisma FLOAT DEFAULT ((0)), 
            este_target FLOAT NOT NULL, 
            norte_target FLOAT NOT NULL, 
            elevacion_target FLOAT NOT NULL, 
            altura_reflector FLOAT DEFAULT ((0)), 
            altura_instrumento FLOAT DEFAULT ((0)), 
            este_estacion FLOAT DEFAULT ((0)), 
            norte_estacion FLOAT DEFAULT ((0)), 
            altura_estacion FLOAT DEFAULT ((0)), 
            medicion_prisma FLOAT DEFAULT ((0)), 
            diferencia_tiempocorto FLOAT DEFAULT ((0)),
            diferencia_tiempolargo FLOAT DEFAULT ((0)), 
            diferencia_limitevelocidad FLOAT DEFAULT ((0)), 
            distancia_horizontal FLOAT DEFAULT ((0)), 
            diferencia_atipica FLOAT DEFAULT ((0)), 
            desplaza_longitudinal FLOAT DEFAULT ((0)), 
            desplaza_transversal FLOAT DEFAULT ((0)), 
            desplaza_altura FLOAT DEFAULT ((0)), 
            grupo_puntos NVARCHAR(MAX),
            CONSTRAINT [PK_{nombretabla}] PRIMARY KEY CLUSTERED (id_prisma)
        );"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            cursor.execute(sqltable)
            conn.commit()
            
            cursor.execute(f"SELECT nombre_prisma, hora_prisma FROM {nombretabla};")
            existing_records = set()
            for row in cursor.fetchall():
                f_str = row[1].strftime('%Y-%m-%dT%H:%M:%S') if hasattr(row[1], 'strftime') else str(row[1])
                existing_records.add((row[0], f_str))
            
            lote_tamano = 5000
            lote_registros = []
            
            sql_insert = f"""
                INSERT INTO {nombretabla} (
                    state_prisma, nombre_prisma, hora_prisma, este_target, norte_target, elevacion_target, distancia_prisma,
                    angulo_horizontal, angulo_vertical, ppm_prisma, diferencia_tiempolargo, diferencia_limitevelocidad,
                    diferencia_atipica, desplaza_longitudinal, desplaza_transversal, desplaza_altura
                ) VALUES ({', '.join(['?'] * 16)})
            """
            
            for fila in datos_procesados.itertuples(index=False):
                if (fila[1], str(fila[2])) not in existing_records:
                    datos_limpios = [None if pd.isna(x) else x for x in fila]
                    lote_registros.append(tuple(datos_limpios))
                
                if len(lote_registros) >= lote_tamano:
                    cursor.executemany(sql_insert, lote_registros)
                    conn.commit()
                    lote_registros = []

            if lote_registros:
                cursor.executemany(sql_insert, lote_registros)
                conn.commit()

        except Exception as e:
            print(f"Error detallado SQL CUATRO: {e}")
            respuesta = False
            if conn: conn.rollback()
        finally:
            if conn: conn.close()
        return respuesta
    
    @staticmethod
    def mdlRemplazarPrismasAutomatizadosCuatro(idproyecto, datos_procesados, componente=None):
        respuesta = True
        nombretabla = f"prismas{idproyecto}"
        sqltable = f"""IF OBJECT_ID(N'dbo.{nombretabla}', N'U') IS NULL
        CREATE TABLE {nombretabla} (
            id_prisma INT IDENTITY(1,1) NOT NULL,
            state_prisma INT NOT NULL DEFAULT ((1)),
            estado_prisma INT NOT NULL DEFAULT ((1)), 
            nombre_prisma NVARCHAR(500) NOT NULL, 
            perfil_prisma NVARCHAR(MAX), 
            hora_prisma DATETIME2(0) NOT NULL, 
            angulo_horizontal NVARCHAR(50), 
            angulo_vertical NVARCHAR(50), 
            distancia_prisma FLOAT DEFAULT ((0)), 
            tipoppm_prisma NVARCHAR(50), 
            ppm_prisma FLOAT DEFAULT ((0)), 
            presion_prisma FLOAT DEFAULT ((0)), 
            temperatura_prisma FLOAT DEFAULT ((0)), 
            constante_prisma FLOAT DEFAULT ((0)), 
            este_target FLOAT NOT NULL, 
            norte_target FLOAT NOT NULL, 
            elevacion_target FLOAT NOT NULL, 
            altura_reflector FLOAT DEFAULT ((0)), 
            altura_instrumento FLOAT DEFAULT ((0)), 
            este_estacion FLOAT DEFAULT ((0)), 
            norte_estacion FLOAT DEFAULT ((0)), 
            altura_estacion FLOAT DEFAULT ((0)), 
            medicion_prisma FLOAT DEFAULT ((0)), 
            diferencia_tiempocorto FLOAT DEFAULT ((0)),
            diferencia_tiempolargo FLOAT DEFAULT ((0)), 
            diferencia_limitevelocidad FLOAT DEFAULT ((0)), 
            distancia_horizontal FLOAT DEFAULT ((0)), 
            diferencia_atipica FLOAT DEFAULT ((0)), 
            desplaza_longitudinal FLOAT DEFAULT ((0)), 
            desplaza_transversal FLOAT DEFAULT ((0)), 
            desplaza_altura FLOAT DEFAULT ((0)), 
            grupo_puntos NVARCHAR(MAX),
            CONSTRAINT [PK_{nombretabla}] PRIMARY KEY CLUSTERED (id_prisma)
        );"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            cursor.execute(sqltable)
            conn.commit()
            
            if componente:
                cursor.execute(f"SELECT nombre_equipo FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'PRISMAS'", (componente,))
                rows = cursor.fetchall()
                nombres_equipos = [row[0] for row in rows]
                if nombres_equipos:
                    placeholders = ','.join(['?'] * len(nombres_equipos))
                    cursor.execute(f"DELETE FROM {nombretabla} WHERE nombre_prisma IN ({placeholders})", nombres_equipos)
                cursor.execute(f"DELETE FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'PRISMAS'", (componente,))
            
            cursor.execute(f"SELECT nombre_prisma, hora_prisma FROM {nombretabla};")
            existing_records = set()
            for row in cursor.fetchall():
                f_str = row[1].strftime('%Y-%m-%dT%H:%M:%S') if hasattr(row[1], 'strftime') else str(row[1])
                existing_records.add((row[0], f_str))
            
            lote_tamano = 5000
            lote_registros = []
            
            sql_insert = f"""
                INSERT INTO {nombretabla} (
                    state_prisma, nombre_prisma, hora_prisma, este_target, norte_target, elevacion_target, distancia_prisma,
                    angulo_horizontal, angulo_vertical, ppm_prisma, diferencia_tiempolargo, diferencia_limitevelocidad,
                    diferencia_atipica, desplaza_longitudinal, desplaza_transversal, desplaza_altura
                ) VALUES ({', '.join(['?'] * 16)})
            """
            
            for fila in datos_procesados.itertuples(index=False):
                if (fila[1], str(fila[2])) not in existing_records:
                    datos_limpios = [None if pd.isna(x) else x for x in fila]
                    lote_registros.append(tuple(datos_limpios))
                
                if len(lote_registros) >= lote_tamano:
                    cursor.executemany(sql_insert, lote_registros)
                    conn.commit()
                    lote_registros = []

            if lote_registros:
                cursor.executemany(sql_insert, lote_registros)
                conn.commit()

        except Exception as e:
            print(f"Error detallado Reemplazar CUATRO: {e}")
            respuesta = False
            if conn: conn.rollback()
        finally:
            if conn: conn.close()
        return respuesta
    
    @staticmethod
    def mdlRegistrarPrismasAutomatizadosCinco(idproyecto, datos_procesados):
        respuesta = True
        nombretabla = f"prismas{idproyecto}"
        sqltable = f"""IF OBJECT_ID(N'dbo.{nombretabla}', N'U') IS NULL
        CREATE TABLE {nombretabla} (
            id_prisma INT IDENTITY(1,1) NOT NULL,
            state_prisma INT NOT NULL DEFAULT ((1)),
            estado_prisma INT NOT NULL DEFAULT ((1)), 
            nombre_prisma NVARCHAR(500) NOT NULL, 
            perfil_prisma NVARCHAR(MAX), 
            hora_prisma DATETIME2(0) NOT NULL, 
            angulo_horizontal NVARCHAR(50), 
            angulo_vertical NVARCHAR(50), 
            distancia_prisma FLOAT DEFAULT ((0)), 
            tipoppm_prisma NVARCHAR(50), 
            ppm_prisma FLOAT DEFAULT ((0)), 
            presion_prisma FLOAT DEFAULT ((0)), 
            temperatura_prisma FLOAT DEFAULT ((0)), 
            constante_prisma FLOAT DEFAULT ((0)), 
            este_target FLOAT NOT NULL, 
            norte_target FLOAT NOT NULL, 
            elevacion_target FLOAT NOT NULL, 
            altura_reflector FLOAT DEFAULT ((0)), 
            altura_instrumento FLOAT DEFAULT ((0)), 
            este_estacion FLOAT DEFAULT ((0)), 
            norte_estacion FLOAT DEFAULT ((0)), 
            altura_estacion FLOAT DEFAULT ((0)), 
            medicion_prisma FLOAT DEFAULT ((0)), 
            diferencia_tiempocorto FLOAT DEFAULT ((0)),
            diferencia_tiempolargo FLOAT DEFAULT ((0)), 
            diferencia_limitevelocidad FLOAT DEFAULT ((0)), 
            distancia_horizontal FLOAT DEFAULT ((0)), 
            diferencia_atipica FLOAT DEFAULT ((0)), 
            desplaza_longitudinal FLOAT DEFAULT ((0)), 
            desplaza_transversal FLOAT DEFAULT ((0)), 
            desplaza_altura FLOAT DEFAULT ((0)), 
            grupo_puntos NVARCHAR(MAX),
            CONSTRAINT [PK_{nombretabla}] PRIMARY KEY CLUSTERED (id_prisma)
        );"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            cursor.execute(sqltable)
            conn.commit()
            
            cursor.execute(f"SELECT nombre_prisma, hora_prisma FROM {nombretabla};")
            existing_records = set()
            for row in cursor.fetchall():
                f_str = row[1].strftime('%Y-%m-%dT%H:%M:%S') if hasattr(row[1], 'strftime') else str(row[1])
                existing_records.add((row[0], f_str))
            
            lote_tamano = 5000
            lote_registros = []
            
            sql_insert = f"""
                INSERT INTO {nombretabla} (
                    hora_prisma,nombre_prisma,este_target, norte_target, elevacion_target,altura_reflector, altura_instrumento,
                    state_prisma,este_estacion, norte_estacion, altura_estacion,medicion_prisma, diferencia_tiempocorto, diferencia_tiempolargo,perfil_prisma,
                    distancia_horizontal, diferencia_atipica,desplaza_longitudinal, desplaza_transversal, desplaza_altura, grupo_puntos,
                    angulo_horizontal,angulo_vertical, distancia_prisma, tipoppm_prisma, ppm_prisma, presion_prisma,temperatura_prisma, constante_prisma
                ) VALUES ({', '.join(['?'] * 29)})
            """
            
            for fila in datos_procesados.itertuples(index=False):
                if (fila[1], str(fila[0])) not in existing_records:
                    datos_limpios = [None if pd.isna(x) else x for x in fila]
                    lote_registros.append(tuple(datos_limpios))
                
                if len(lote_registros) >= lote_tamano:
                    cursor.executemany(sql_insert, lote_registros)
                    conn.commit()
                    lote_registros = []

            if lote_registros:
                cursor.executemany(sql_insert, lote_registros)
                conn.commit()

        except Exception as e:
            print(f"Error detallado SQL CINCO: {e}")
            respuesta = False
            if conn: conn.rollback()
        finally:
            if conn: conn.close()
        return respuesta
    
    @staticmethod
    def mdlRemplazarPrismasAutomatizadosCinco(idproyecto, datos_procesados, componente=None):
        respuesta = True
        nombretabla = f"prismas{idproyecto}"
        sqltable = f"""IF OBJECT_ID(N'dbo.{nombretabla}', N'U') IS NULL
        CREATE TABLE {nombretabla} (
            id_prisma INT IDENTITY(1,1) NOT NULL,
            state_prisma INT NOT NULL DEFAULT ((1)),
            estado_prisma INT NOT NULL DEFAULT ((1)), 
            nombre_prisma NVARCHAR(500) NOT NULL, 
            perfil_prisma NVARCHAR(MAX), 
            hora_prisma DATETIME2(0) NOT NULL, 
            angulo_horizontal NVARCHAR(50), 
            angulo_vertical NVARCHAR(50), 
            distancia_prisma FLOAT DEFAULT ((0)), 
            tipoppm_prisma NVARCHAR(50), 
            ppm_prisma FLOAT DEFAULT ((0)), 
            presion_prisma FLOAT DEFAULT ((0)), 
            temperatura_prisma FLOAT DEFAULT ((0)), 
            constante_prisma FLOAT DEFAULT ((0)), 
            este_target FLOAT NOT NULL, 
            norte_target FLOAT NOT NULL, 
            elevacion_target FLOAT NOT NULL, 
            altura_reflector FLOAT DEFAULT ((0)), 
            altura_instrumento FLOAT DEFAULT ((0)), 
            este_estacion FLOAT DEFAULT ((0)), 
            norte_estacion FLOAT DEFAULT ((0)), 
            altura_estacion FLOAT DEFAULT ((0)), 
            medicion_prisma FLOAT DEFAULT ((0)), 
            diferencia_tiempocorto FLOAT DEFAULT ((0)),
            diferencia_tiempolargo FLOAT DEFAULT ((0)), 
            diferencia_limitevelocidad FLOAT DEFAULT ((0)), 
            distancia_horizontal FLOAT DEFAULT ((0)), 
            diferencia_atipica FLOAT DEFAULT ((0)), 
            desplaza_longitudinal FLOAT DEFAULT ((0)), 
            desplaza_transversal FLOAT DEFAULT ((0)), 
            desplaza_altura FLOAT DEFAULT ((0)), 
            grupo_puntos NVARCHAR(MAX),
            CONSTRAINT [PK_{nombretabla}] PRIMARY KEY CLUSTERED (id_prisma)
        );"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            cursor.execute(sqltable)
            conn.commit()
            
            if componente:
                cursor.execute(f"SELECT nombre_equipo FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'PRISMAS'", (componente,))
                rows = cursor.fetchall()
                nombres_equipos = [row[0] for row in rows]
                if nombres_equipos:
                    placeholders = ','.join(['?'] * len(nombres_equipos))
                    cursor.execute(f"DELETE FROM {nombretabla} WHERE nombre_prisma IN ({placeholders})", nombres_equipos)
                cursor.execute(f"DELETE FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'PRISMAS'", (componente,))
            
            cursor.execute(f"SELECT nombre_prisma, hora_prisma FROM {nombretabla};")
            existing_records = set()
            for row in cursor.fetchall():
                f_str = row[1].strftime('%Y-%m-%dT%H:%M:%S') if hasattr(row[1], 'strftime') else str(row[1])
                existing_records.add((row[0], f_str))
            
            lote_tamano = 5000
            lote_registros = []
            
            sql_insert = f"""
                INSERT INTO {nombretabla} (
                    hora_prisma,nombre_prisma,este_target, norte_target, elevacion_target,altura_reflector, altura_instrumento,
                    state_prisma,este_estacion, norte_estacion, altura_estacion,medicion_prisma, diferencia_tiempocorto, diferencia_tiempolargo,perfil_prisma,
                    distancia_horizontal, diferencia_atipica,desplaza_longitudinal, desplaza_transversal, desplaza_altura, grupo_puntos,
                    angulo_horizontal,angulo_vertical, distancia_prisma, tipoppm_prisma, ppm_prisma, presion_prisma,temperatura_prisma, constante_prisma
                ) VALUES ({', '.join(['?'] * 29)})
            """
            
            for fila in datos_procesados.itertuples(index=False):
                if (fila[1], str(fila[0])) not in existing_records:
                    datos_limpios = [None if pd.isna(x) else x for x in fila]
                    lote_registros.append(tuple(datos_limpios))
                
                if len(lote_registros) >= lote_tamano:
                    cursor.executemany(sql_insert, lote_registros)
                    conn.commit()
                    lote_registros = []

            if lote_registros:
                cursor.executemany(sql_insert, lote_registros)
                conn.commit()

        except Exception as e:
            print(f"Error detallado Reemplazar CINCO: {e}")
            respuesta = False
            if conn: conn.rollback()
        finally:
            if conn: conn.close()
        return respuesta
    
    @staticmethod
    def mdlRegistrarInclinometro(idproyecto, datos):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()

            # Verificar si el nombre ya existe
            query_verificar = """
            SELECT COUNT(*) FROM inclinometros WHERE nombre_inclinometro = ? AND id_proyecto = ?
            """
            cur.execute(query_verificar, (datos['nombre'], idproyecto))
            count = cur.fetchone()[0]

            if count > 0:
                print("El nombre del inclinómetro ya existe para este proyecto.")
                return False

            # Insertar en la tabla inclinometros y obtener ID
            # USO DE SET NOCOUNT ON PARA EVITAR PROBLEMAS CON PYODBC Y SCOPE_IDENTITY
            query_inclinometro = """
            SET NOCOUNT ON;
            INSERT INTO inclinometros (
                id_proyecto, tipo_inclinometro, nombre_inclinometro, codigo_inclinometro,
                norte_inclinometro, este_inclinometro, elevacion_inclinometro,
                profundidad_inclinometro, inclinacion_inclinometro, azimut_inclinometro,
                comentario_inclinometro
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            SELECT CAST(SCOPE_IDENTITY() AS INT);
            """
            cur.execute(query_inclinometro, (
                idproyecto, datos['tipoEquipo'], datos['nombre'], datos['codigo'],
                datos['norte'], datos['este'], datos['nivel'],
                datos['profundidad'], datos['inclinacion'], datos['azimut'],
                datos['comentario']
            ))

            # Obtener el id_inclinometro generado
            row = cur.fetchone()
            id_inclinometro = int(row[0]) if row and row[0] is not None else None

            if not id_inclinometro:
                raise Exception("No se pudo obtener el ID del inclinómetro insertado.")

            # Insertar en la tabla instrumentacion
            query_instrumentacion = """
            INSERT INTO instrumentacion (
                id_componente, tipo_equipo, nombre_equipo, id_equipo, tabla_equipo
            ) VALUES (?, ?, ?, ?, ?)
            """
            cur.execute(query_instrumentacion, (
                datos['componente'], 'INCLINOMETRO', datos['nombre'], id_inclinometro, 'inclinometros'
            ))

            conn.commit()
            return True
        except Exception as e:
            print("Error al registrar inclinómetro:", e)
            if conn: conn.rollback()
            return False
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlRegistrarEquipoZona(idcomponente, tabla, equipos, tipo):
        prismasnuevos = []
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            
            consulta_verificacion = """SELECT COUNT(1) FROM instrumentacion WHERE nombre_equipo = ? AND id_componente = ?;"""
            
            sql_insert = """INSERT INTO instrumentacion (id_componente, tipo_equipo, nombre_equipo, tabla_equipo,
            estado_instrumentacion) VALUES (?, ?, ?, ?, ?);"""
            
            for nombre_equipo in equipos:
                cur.execute(consulta_verificacion, (nombre_equipo, idcomponente))
                existe = cur.fetchone()[0]
                
                if existe == 0:
                    cur.execute(sql_insert, (idcomponente, tipo, nombre_equipo, tabla, 1))
                    prismasnuevos.append(nombre_equipo)
            
            conn.commit()
            return True, prismasnuevos
        except Exception as e:
            print("Error al insertar instrumentacion:", e)
            return False, []
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlObtenerPrismaDataPositivaFechas(tabla, idzona, tipoequipo, prisma, fechaini, fechafin):
        params = [idzona] + [tipoequipo] + [prisma] + [fechaini] + [fechafin]
        
        # SQL SERVER: DATEDIFF(SECOND, ...) / 86400.0 para días fraccionarios
        # hora_prisma es DATETIME
        sql = f"""WITH cte_prisma AS (
            SELECT p.nombre_prisma, p.hora_prisma, ROUND(p.este_target, 3) AS este_target,
                ROUND(p.norte_target, 3) AS norte_target, ROUND(p.elevacion_target, 3) AS elevacion_target, p.distancia_prisma,
                FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS norte_inicial,
                FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS este_inicial,
                FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS elevacion_inicial,
                FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS tiempo_inicial,
                LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS norte_anterior,
                LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS este_anterior,
                LAG(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS elevacion_anterior,
                LAG(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS tiempo_anterior,
                ROW_NUMBER() OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS row_num
            FROM {tabla} AS p 
            INNER JOIN instrumentacion AS it ON it.nombre_equipo = p.nombre_prisma
            INNER JOIN componentes AS co ON co.id_componente = it.id_componente
            WHERE co.id_componente = ? AND it.tipo_equipo = ? AND it.nombre_equipo = ? 
            AND p.hora_prisma BETWEEN ? AND ?
            AND p.state_prisma = 1 AND p.estado_prisma = 1 AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '') 
        )
        SELECT nombre_prisma, CAST(hora_prisma AS DATE) AS fecha, CAST(hora_prisma AS TIME) AS hora, este_target,
            norte_target, elevacion_target, distancia_prisma,
            CASE
                WHEN row_num = 1 THEN 0
                ELSE 
                    SQRT(
                        POWER(este_target - este_anterior, 2) +
                        POWER(norte_target - norte_anterior, 2) +
                        POWER(elevacion_target - elevacion_anterior, 2)
                    ) * 100
            END AS DI3D,
            SQRT(
                POWER(este_target - este_inicial, 2) +
                POWER(norte_target - norte_inicial, 2) +
                POWER(elevacion_target - elevacion_inicial, 2)
            ) * 100 AS DA3D,
            CASE 
                WHEN row_num = 1 THEN 0 
                ELSE 
                    SQRT(
                        POWER(este_target - este_anterior, 2) +
                        POWER(norte_target - norte_anterior, 2) +
                        POWER(elevacion_target - elevacion_anterior, 2)
                    ) * 100 / NULLIF(DATEDIFF(SECOND, tiempo_anterior, hora_prisma) / 86400.0, 0)
            END AS VI3D,
            CASE 
                WHEN row_num = 1 THEN 0
                ELSE 
                    (SQRT(
                        POWER(este_target - este_inicial, 2) +
                        POWER(norte_target - norte_inicial, 2) +
                        POWER(elevacion_target - elevacion_inicial, 2)
                    ) * 100) / NULLIF(DATEDIFF(SECOND, tiempo_inicial, hora_prisma) / 86400.0, 0)
            END AS VA3D
        FROM cte_prisma
        ORDER BY nombre_prisma, hora_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            results = cur.fetchall()
            return results if results else None
        except Exception as e:
            print("Error al obtener data prismas positiva:", e)
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlObtenerPrismaDataAmbasFechas(tabla, idzona, tipoequipo, prisma, fechaini, fechafin):
        params = [idzona] + [tipoequipo] + [prisma] + [fechaini] + [fechafin]
        sql = f"""WITH cte_prisma AS (
            SELECT p.nombre_prisma, p.hora_prisma, ROUND(p.este_target, 3) AS este_target,
                ROUND(p.norte_target, 3) AS norte_target, ROUND(p.elevacion_target, 3) AS elevacion_target, p.distancia_prisma,
                FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS norte_inicial,
                FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS este_inicial,
                FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS elevacion_inicial,
                FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS tiempo_inicial,
                LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS norte_anterior,
                LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS este_anterior,
                LAG(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS elevacion_anterior,
                LAG(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS tiempo_anterior,
                ROW_NUMBER() OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS row_num
            FROM {tabla} AS p INNER JOIN instrumentacion AS it ON it.nombre_equipo = p.nombre_prisma
            INNER JOIN componentes AS co ON co.id_componente = it.id_componente
            WHERE co.id_componente = ? AND it.tipo_equipo = ? AND it.nombre_equipo = ? 
            AND p.hora_prisma BETWEEN ? AND ?
            AND p.state_prisma = 1 AND p.estado_prisma = 1 AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
        ),
        cte_distancias AS (
            SELECT nombre_prisma, hora_prisma, este_target, norte_target, elevacion_target, distancia_prisma, tiempo_inicial,
                CASE 
                    WHEN row_num = 1 THEN 0 
                    ELSE 
                        SQRT(
                            POWER(este_target - este_anterior, 2) +
                            POWER(norte_target - norte_anterior, 2) +
                            POWER(elevacion_target - elevacion_anterior, 2)
                        ) * 100
                END AS DI3D,
                SQRT(
                    POWER(este_target - este_inicial, 2) +
                    POWER(norte_target - norte_inicial, 2) +
                    POWER(elevacion_target - elevacion_inicial, 2)
                ) * 100 AS DA3D,
                tiempo_anterior, hora_prisma AS tiempo_actual, row_num
            FROM cte_prisma
        )
        SELECT nombre_prisma, 
            CAST(hora_prisma AS DATE) AS fecha, 
            CAST(hora_prisma AS TIME) AS hora, 
            este_target,
            norte_target, elevacion_target, distancia_prisma, DI3D, DA3D,
            CASE 
                WHEN row_num = 1 THEN 0
                ELSE 
                    (DA3D - LAG(DA3D) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma))
                    / NULLIF(DATEDIFF(SECOND, tiempo_anterior, tiempo_actual) / 86400.0, 0)
            END AS VI3D,
            CASE
                WHEN row_num = 1 THEN 0
                ELSE 
                    DA3D / NULLIF(DATEDIFF(SECOND, tiempo_inicial, tiempo_actual) / 86400.0, 0)
            END AS VA3D
        FROM cte_distancias ORDER BY nombre_prisma, hora_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            results = cur.fetchall()
            # CORRECCION AQUI: Convertir a tuplas
            if results:
                return [tuple(row) for row in results]
            else:
                return None
        except Exception as e:
            print("Error al obtener data prismas ambas: ", e)
            return None
        finally:
            if conn: conn.close()
            
    @staticmethod
    def mdlObtenerInfoExportarInclinometro(idcomponente, tipoequipo, idinstrumento):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = """SELECT en.id_encabezado, co.nombre_componente, i.nombre_inclinometro, i.codigo_inclinometro, i.tipo_inclinometro,
            en.fecha_inclinometro, i.profundidad_inclinometro, i.este_inclinometro, i.norte_inclinometro, i.elevacion_inclinometro
            FROM inclinometros AS i INNER JOIN inclinometro_encabezado AS en ON i.id_inclinometro = en.id_inclinometro
            INNER JOIN instrumentacion AS it ON it.id_equipo = i.id_inclinometro
            INNER JOIN componentes AS co ON co.id_componente = it.id_componente
            WHERE co.id_componente = ? AND it.tipo_equipo = ? AND it.id_instrumentacion = ? AND it.estado_instrumentacion = 1;"""
            cur = conn.cursor()
            cur.execute(sql, (idcomponente, tipoequipo, idinstrumento))
            results = cur.fetchall()
            return results if results else None
        except Exception as e:
            print("Error al obtener encabezado: ", e)
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlObtenerDataExportarPrismas(tabla, nameprismas, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in nameprismas])
        params = [fechaini] + [fechafin] + nameprismas
        conn = None
        
        # Exportar fecha formateada (SQL Server)
        sql = f"""SELECT state_prisma, nombre_prisma, perfil_prisma, FORMAT(hora_prisma, 'dd-MM-yyyy HH:mm:ss') AS hora_prisma,
        angulo_horizontal, angulo_vertical, distancia_prisma, tipoppm_prisma, ppm_prisma, presion_prisma, temperatura_prisma,
        constante_prisma, este_target, norte_target, elevacion_target, altura_reflector, altura_instrumento, este_estacion,
        norte_estacion, altura_estacion, medicion_prisma, diferencia_tiempocorto, diferencia_tiempolargo,
        diferencia_limitevelocidad, distancia_horizontal, diferencia_atipica, desplaza_longitudinal, desplaza_transversal,
        desplaza_altura, grupo_puntos 
        FROM {tabla} 
        WHERE hora_prisma BETWEEN ? AND ? AND nombre_prisma IN ({placeholders});"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            results = cur.fetchall()
            return results if results else None
        except Exception as e:
            print("Error al obtener prismas: ", e)
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlObtenerDataExportarInclinometro(idproyecto, idencabezado):
        tabla = f"inclinometro_detalle{idproyecto}"
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = f"""SELECT profundidad_detalle, apositivo_detalle, anegativo_detalle, bpositivo_detalle, bnegativo_detalle
            FROM {tabla} WHERE id_encabezado = ?;"""
            cur = conn.cursor()
            cur.execute(sql, (idencabezado,))
            results = cur.fetchall()
            return results if results else None
        except Exception as e:
            print("Error al obtener data inclino exportar: ", e)
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlTraerInfoPiezometroCuerda(idcomponente, tipoequipo, idinstrumento):
        conn = None
        sql = """SELECT p.*, co.nombre_componente FROM piezometrocuerdas p INNER JOIN instrumentacion AS it
        ON it.id_equipo = p.id_piezometro INNER JOIN componentes AS co ON co.id_componente = it.id_componente
        WHERE co.id_componente = ? AND it.tipo_equipo = ? AND it.id_instrumentacion = ? AND it.estado_instrumentacion = 1;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idcomponente, tipoequipo, idinstrumento))
            row = cur.fetchone()
            return row if row else None
        except Exception as e:
            print("Error al consultar piezometro cuerda: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlTraerInfoPiezometroManual(idcomponente, tipoequipo, idinstrumento):
        conn = None
        sql = """SELECT p.*, co.nombre_componente FROM piezometromanuales p INNER JOIN instrumentacion AS it
        ON it.id_equipo = p.id_piezometro INNER JOIN componentes AS co ON co.id_componente = it.id_componente
        WHERE co.id_componente = ? AND it.tipo_equipo = ? AND it.id_instrumentacion = ? AND it.estado_instrumentacion = 1;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idcomponente, tipoequipo, idinstrumento))
            row = cur.fetchone()
            return row if row else None
        except Exception as e:
            print("Error al consultar piezometro manual: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlDataExportarPiezometrosCuerda(idproyecto, idcomponente, idinstrumento, fechaini, fechafin):
        # SQL Server FORMAT y TOP 1
        sql = f"""SELECT FORMAT(d.fecha_cuerda, 'dd/MM/yyyy') AS fecha, CAST(d.fecha_cuerda AS TIME) AS hora, d.frecuencia_cuerda,
        d.temperatura_cuerda, d.presion_barometrica,
        CASE 
            WHEN p.tipo_piezometro = 1 THEN d.medida_calculada 
            ELSE d.medida_calculada - p.elevacion_piezometro 
        END AS MCA,
        CASE 
            WHEN p.tipo_piezometro = 1 THEN p.elevacion_piezometro + d.medida_calculada
            ELSE d.medida_calculada
        END AS nivel_agua, d.observacion_cuerda,
        COALESCE(
            (SELECT TOP 1 c2.nivel_cota FROM cotas_piezometricas c2 WHERE c2.id_piezometro = d.id_piezometro 
            AND c2.tipo_piezometro = 'PCV' AND c2.fecha_cota <= d.fecha_cuerda ORDER BY c2.fecha_cota DESC),
            (SELECT TOP 1 c3.nivel_cota FROM cotas_piezometricas c3 WHERE c3.id_piezometro = d.id_piezometro 
            AND c3.tipo_piezometro = 'PCV' ORDER BY c3.fecha_cota ASC)
        ) AS elevacion
        FROM piezometrocuerdas p INNER JOIN piezometrocuerda_detalle{idproyecto} d ON p.id_piezometro = d.id_piezometro
        INNER JOIN cotas_piezometricas cp ON d.id_piezometro = cp.id_piezometro
        INNER JOIN instrumentacion AS it ON it.id_equipo = d.id_piezometro
        INNER JOIN componentes AS co ON co.id_componente = it.id_componente
        WHERE co.id_componente = ? AND it.id_instrumentacion = ? AND d.fecha_cuerda BETWEEN ? AND ?
        AND d.estado_cuerda = 1 AND cp.tipo_piezometro = 'PCV' AND it.tipo_equipo = 'PIEZOMETROCUERDA'
        ORDER BY d.fecha_cuerda;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idcomponente, idinstrumento, fechaini, fechafin))
            row = cur.fetchall()
            return row if row else None
        except Exception as e:
            print("Error al consultar data piezometros cuerda: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlDataExportarPiezometrosManual(idproyecto, idcomponente, idinstrumento, fechaini, fechafin):
        # SQL Server FORMAT y TOP 1
        sql = f"""WITH cte_cota AS (
            SELECT it.tipo_equipo, p.nombre_piezometro, p.tipo_piezometro, d.fecha_piezometro, d.medida_piezometro,
            d.observacion_detalle, p.stickup_piezometro, p.elevacion_piezometro AS instalacion, p.fundacion_piezometro,
            COALESCE(
                (SELECT TOP 1 c2.nivel_cota FROM cotas_piezometricas c2 WHERE c2.id_piezometro = d.id_piezometro 
                AND c2.tipo_piezometro = 'PVC' AND c2.fecha_cota <= d.fecha_piezometro ORDER BY c2.fecha_cota DESC),
                (SELECT TOP 1 c3.nivel_cota FROM cotas_piezometricas c3 WHERE c3.id_piezometro = d.id_piezometro
                AND c3.tipo_piezometro = 'PVC' ORDER BY c3.fecha_cota ASC)
            ) AS elevacion
            FROM piezometromanuales p INNER JOIN piezometromanual_detalle{idproyecto} d ON p.id_piezometro = d.id_piezometro
            INNER JOIN instrumentacion AS it ON it.id_equipo = p.id_piezometro
            INNER JOIN componentes AS co ON co.id_componente = it.id_componente
            WHERE co.id_componente = ? AND it.id_instrumentacion = ? AND d.fecha_piezometro BETWEEN ? AND ?
            AND d.estado_manual = 1 AND it.tipo_equipo = 'PIEZOMETROMANUAL'
        )
        SELECT FORMAT(fecha_piezometro, 'dd/MM/yyyy') AS fecha, CAST(fecha_piezometro AS TIME) AS hora,
            CASE
                WHEN tipo_piezometro = 1 THEN medida_piezometro
                ELSE stickup_piezometro + elevacion - medida_piezometro
            END AS nivel_piezometrico,
            stickup_piezometro + elevacion - instalacion AS profundidad, elevacion,
            CASE
                WHEN tipo_piezometro = 1 THEN stickup_piezometro + elevacion - medida_piezometro
                ELSE medida_piezometro
            END AS nivel_agua,
            CASE
				WHEN tipo_piezometro = 1 THEN stickup_piezometro + elevacion - instalacion - medida_piezometro
				ELSE medida_piezometro - instalacion
			END AS nivel_vertical, observacion_detalle
        FROM cte_cota ORDER BY fecha_piezometro;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idcomponente, idinstrumento, fechaini, fechafin))
            row = cur.fetchall()
            return row if row else None
        except Exception as e:
            print("Error al consultar data piezometros manual: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlTraerInfoPluviometro(idcomponente, tipoequipo, idinstrumento):
        conn = None
        sql = """SELECT p.* FROM pluviometros p INNER JOIN instrumentacion AS it
        ON it.id_equipo = p.id_pluviometro INNER JOIN componentes AS co ON co.id_componente = it.id_componente
        WHERE co.id_componente = ? AND it.tipo_equipo = ? AND it.id_instrumentacion = ? AND it.estado_instrumentacion = 1;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idcomponente, tipoequipo, idinstrumento))
            row = cur.fetchone()
            return row if row else None
        except Exception as e:
            print("Error al consultar pluviometro info: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlDataExportarPluviometro(idproyecto, idcomponente, idinstrumento):
        conn = None
        sql = f"""SELECT FORMAT(d.fecha_pluviometro, 'dd/MM/yyyy') AS fecha, CAST(d.fecha_pluviometro AS TIME) AS hora,
        d.medida_pluviometro, d.observacion_pluviometro
        FROM pluviometro_detalle{idproyecto} d INNER JOIN instrumentacion AS it ON it.id_equipo = d.id_pluviometro
        INNER JOIN componentes AS co ON co.id_componente = it.id_componente
        WHERE co.id_componente = ? AND it.id_instrumentacion = ? AND it.tipo_equipo = 'PLUVIOMETRO'
        ORDER BY d.fecha_pluviometro;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idcomponente, idinstrumento))
            row = cur.fetchall()
            return row if row else None
        except Exception as e:
            print("Error al consultar data pluviometro: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlTraerInfoCeldaAsentamiento(idcomponente, tipoequipo, idinstrumento):
        conn = None
        sql = """SELECT c.*, co.nombre_componente FROM celdas c INNER JOIN instrumentacion AS it
        ON it.id_equipo = c.id_celda INNER JOIN componentes AS co ON co.id_componente = it.id_componente
        WHERE co.id_componente = ? AND it.tipo_equipo = ? AND it.id_instrumentacion = ? AND it.estado_instrumentacion = 1;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idcomponente, tipoequipo, idinstrumento))
            row = cur.fetchone()
            return row if row else None
        except Exception as e:
            print("Error al consultar info celda: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlDataExportarCeldaAsentamiento(idproyecto, idcomponente, idinstrumento, fechaini, fechafin):
        conn = None
        # SQL Server FORMAT y TOP 1
        sql = f"""SELECT FORMAT(cd.fecha_detalle, 'dd/MM/yyyy') AS fecha, CAST(cd.fecha_detalle AS TIME) AS hora, cd.frecuencia_digits,
        cd.frecuencia_hz, cd.temperatura_detalle, cd.medida_calculada,
		ca.instalacion_celda - abs(cd.medida_calculada) AS cota_piezometrica,
        COALESCE(
            (SELECT TOP 1 c2.nivel_cota FROM cotas_celdas c2 WHERE c2.id_celda = cd.id_celda
            AND c2.fecha_cota <= cd.fecha_detalle ORDER BY c2.fecha_cota DESC),
            (SELECT TOP 1 c3.nivel_cota FROM cotas_celdas c3 WHERE c3.id_celda = cd.id_celda 
            ORDER BY c3.fecha_cota ASC)
        ) AS superficie_celda, cd.observacion_detalle
        FROM celda_detalle{idproyecto} cd INNER JOIN celdas ca ON cd.id_celda = ca.id_celda
        INNER JOIN instrumentacion AS it ON it.id_equipo = cd.id_celda
        INNER JOIN componentes AS co ON co.id_componente = it.id_componente
        WHERE co.id_componente = ? AND it.id_instrumentacion = ? AND cd.fecha_detalle BETWEEN ? AND ?
        AND cd.estado_detalle = 1 AND it.tipo_equipo = 'CELDA'
        ORDER BY cd.fecha_detalle;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idcomponente, idinstrumento, fechaini, fechafin))
            row = cur.fetchall()
            return row if row else None
        except Exception as e:
            print("Error al consultar data celda: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlTraerInfoAcelerografo(idcomponente, tipoequipo, idinstrumento):
        conn = None
        sql = """SELECT a.* FROM acelerografos a INNER JOIN instrumentacion AS it
        ON it.id_equipo = a.id_acelerografo INNER JOIN componentes AS co ON co.id_componente = it.id_componente
        WHERE co.id_componente = ? AND it.tipo_equipo = ? AND it.id_instrumentacion = ? AND it.estado_instrumentacion = 1;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idcomponente, tipoequipo, idinstrumento))
            row = cur.fetchone()
            return row if row else None
        except Exception as e:
            print("Error al consultar acelerografo info: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlDataExportarAcelerografo(idproyecto, idcomponente, idinstrumento, fechaini, fechafin):
        conn = None
        sql = f"""SELECT FORMAT(d.fecha_detalle, 'dd/MM/yyyy') AS fecha, CAST(d.fecha_detalle AS TIME) AS hora,
        d.magnitud_detalle, d.distancia_detalle, d.observacion_detalle
        FROM acelerografo_detalle{idproyecto} d INNER JOIN instrumentacion AS it ON it.id_equipo = d.id_acelerografo
        INNER JOIN componentes AS co ON co.id_componente = it.id_componente
        WHERE co.id_componente = ? AND it.id_instrumentacion = ? AND d.fecha_detalle BETWEEN ? AND ?
        AND it.tipo_equipo = 'ACELEROGRAFO' ORDER BY d.fecha_detalle;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idcomponente, idinstrumento, fechaini, fechafin))
            row = cur.fetchall()
            return row if row else None
        except Exception as e:
            print("Error al consultar data acelerografo: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlObtenerInfoExportarSondajetdr(idproyecto, idcomponente, idinstrumento):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = f"""SELECT DISTINCT d.fecha_detalle, s.nombre_sondajetdr, s.este_sondajetdr, s.norte_sondajetdr,
            s.elevacion_sondajetdr, s.profundidad_sondajetdr, s.inclinacion_sondajetdr, s.azimut_sondajetdr, s.comentario_sondajetdr
            FROM sondajestdr AS s INNER JOIN sondajetdr_detalle{idproyecto} AS d ON s.id_sondajetdr = d.id_sondajetdr
            INNER JOIN instrumentacion AS it ON it.id_equipo = s.id_sondajetdr
            INNER JOIN componentes AS co ON co.id_componente = it.id_componente
            WHERE co.id_componente = ? AND it.id_instrumentacion = ? AND it.tipo_equipo = 'TDR' AND it.estado_instrumentacion = 1;"""
            cur = conn.cursor()
            cur.execute(sql, (idcomponente, idinstrumento))
            results = cur.fetchall()
            return results if results else None
        except Exception as e:
            print("Error al obtener fechas tdr: ", e)
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlObtenerDataExportarSondajetdr(idproyecto, idtdr, fecha):
        tabla = f"sondajetdr_detalle{idproyecto}"
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = f"""SELECT FORMAT(fecha_detalle, 'dd/MM/yyyy') AS fecha, CAST(fecha_detalle AS TIME) AS hora,
            profundidad_detalle, impedancia_detalle, observacion_detalle
            FROM {tabla} WHERE id_sondajetdr = ? AND fecha_detalle = ?;"""
            cur = conn.cursor()
            cur.execute(sql, (idtdr, fecha))
            results = cur.fetchall()
            return results if results else None
        except Exception as e:
            print("Error al obtener data tdr exportar: ", e)
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlDataExportarCotaTerreno(idproyecto, idcomponente, idinstrumento):
        conn = None
        sql = f"""SELECT FORMAT(d.fecha_detalle, 'dd/MM/yyyy') AS fecha, CAST(d.fecha_detalle AS TIME) AS hora,
        d.nivel_detalle, d.observacion_detalle
        FROM cotaterreno_detalle{idproyecto} d INNER JOIN instrumentacion AS it ON it.id_equipo = d.id_terreno
        INNER JOIN componentes AS co ON co.id_componente = it.id_componente
        WHERE co.id_componente = ? AND it.id_instrumentacion = ? AND it.tipo_equipo = 'COTATERRENO'
        ORDER BY d.fecha_detalle;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idcomponente, idinstrumento))
            row = cur.fetchall()
            return row if row else None
        except Exception as e:
            print("Error al consultar data terreno: " + str(e))
            return None
        finally:
            if conn: conn.close()