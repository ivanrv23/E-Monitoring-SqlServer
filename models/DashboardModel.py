import pyodbc
# import pandas as pd # (Opcional, si no lo usas en este archivo específico puedes quitarlo)
from services.security.apis.conexiones.conexion import Connection

class DashboardModel:
    
    @staticmethod
    def mdlObtenerInstrumentacionProyecto(proyecto_id, id_componente):
        conn = None
        # Esta consulta usa sintaxis estándar SQL (CASE WHEN), funciona bien en SQL Server
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
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyecto_id, id_componente))
            results = cur.fetchone()
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al obtener instrumentación:", e)
            return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlObtenerInstrumentacionOIProyecto(proyecto_id, id_componente):
        conn = None
        sql = """SELECT i.estado_instrumentacion, COUNT(*) AS total_equipos
        FROM componentes c INNER JOIN instrumentacion i ON c.id_componente = i.id_componente
        WHERE c.id_proyecto = ? AND i.id_componente = ? AND i.tipo_equipo NOT IN ('TOPOGRAFIA', 'COTATERRENO') 
        GROUP BY i.estado_instrumentacion;"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyecto_id, id_componente))
            results = cur.fetchall()
            # Diccionario de mapeo de estados
            estado_mapeo = {
                0: 'Inoperativos',
                1: 'Operativos'
            }
            # Aplicar el mapeo de estados a los resultados
            if results:
                results = [(estado_mapeo.get(item[0], item[0]), item[1]) for item in results]
                return results
            else:
                return None
        except Exception as e:
            print("Error al obtener instrumentación:", e)
            return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlObtenerLecturasPrismas(tabla, id_componente, tipo):
        conn = None
        # La sintaxis de esta consulta es compatible con SQL Server
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
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (id_componente, tipo))
            results = cur.fetchall()

            if results:
                return results
            else:
                return None
        except Exception as e:
            print(f"Error al obtener las lecturas de los prismas: {e}")
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlObtenerObtenerComponentes(proyecto_id):
        conn = None
        sql = """SELECT * FROM componentes  WHERE id_proyecto = ? AND estado_componente = 1;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyecto_id,))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener componentes: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlResumenPrismas(tabla, idcomponente):
        conn = None
        
        # LOGICA SQL SERVER:
        # Reemplazamos JULIANDAY(...) por DATEDIFF(DAY, fecha1, fecha2)
        # Reemplazamos CAST(... AS REAL) por CAST(... AS FLOAT)
        
        sql = f"""SELECT nombre_prisma, MIN(hora) AS fecha_minima, MAX(hora) AS fecha_maxima, COUNT(*) AS cantidad,
            CAST(DATEDIFF(DAY, MIN(hora), MAX(hora)) + 1 AS FLOAT) as total_dias,
            COUNT(*) / (CAST(DATEDIFF(DAY, MIN(hora), MAX(hora)) + 1 AS FLOAT)) AS ratio
        FROM (
            SELECT nombre_prisma, hora_prisma AS hora FROM {tabla} p INNER JOIN instrumentacion i
            ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND i.estado_instrumentacion = 1 AND i.id_componente = ?
        ) AS subquery_alias GROUP BY nombre_prisma;""" 
        # Nota: SQL Server a veces exige un alias para subconsultas en FROM, agregué 'AS subquery_alias' por si acaso
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idcomponente,))
            rows = cur.fetchall()
            return rows
        except Exception as e:
            print("Error al consultar Resumen prismas: " + str(e))
            return None
        finally:
            if conn: conn.close()