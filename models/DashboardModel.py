import pandas as pd
from services.security.apis.conexiones.connection import Connection
# Eliminamos sqlite3, manejamos excepciones genéricas

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