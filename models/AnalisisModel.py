from services.security.apis.conexiones.connection import Connection
import datetime
import numpy as np
from pyodbc import Error

class AnalisisModel:
    
    @staticmethod
    def mdlListarComponentesPrismasProyecto(idproyecto):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = """SELECT DISTINCT c.* FROM componentes c INNER JOIN instrumentacion i ON c.id_componente = i.id_componente
            WHERE c.id_proyecto = ? AND c.estado_componente = 1 AND i.tipo_equipo = 'PRISMAS';"""
            cur = conn.cursor()
            cur.execute(sql, (idproyecto,))
            results = cur.fetchall()
            if results:
                # Convertir pyodbc.Row a tupla para compatibilidad con frontend
                return [tuple(row) for row in results]
            else:
                return None
        except Exception as e:
            print("Error al obtener componentes analisis: ", e)
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerNombresPrismasComponente(idcomponente, tipo):
        sql = f"""SELECT * FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = ? AND estado_instrumentacion = 1;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idcomponente, tipo))
            row = cur.fetchall()
            if row:
                return [tuple(r) for r in row]
            else:
                return None
        except Exception as e:
            print("Error al listar prismas analisis: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDatosTrayectoria(tabla, prismas, idcomponente):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente]
        # SQL Server: CAST a FLOAT para calculos precisos, TOP 1 en lugar de LIMIT
        sql = f"""SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma,
        (p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) AS var_este,
        (p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) AS var_norte,
        (p.elevacion_target - FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) AS var_elevacion
        FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        INNER JOIN componentes co ON i.id_componente = co.id_componente
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = cur.fetchall()
            if row:
                return [tuple(r) for r in row]
            else:
                return None
        except Exception as e:
            print("Error al consultar trayectoria: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularDatosTrayectoriaFechas(tabla, prismas, idcomponente, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente, fechaini, fechafin]
        sql = f"""SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma,
        (p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) AS var_este,
        (p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) AS var_norte,
        (p.elevacion_target - FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) AS var_elevacion
        FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        INNER JOIN componentes co ON i.id_componente = co.id_componente
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
        AND p.hora_prisma BETWEEN ? AND ? ORDER BY p.nombre_prisma, p.hora_prisma;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = cur.fetchall()
            if row:
                return [tuple(r) for r in row]
            else:
                return None
        except Exception as e:
            print("Error al consultar trayectoria: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerVariacionCoordenadas(tabla, prismas, idcomponente):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente]
        sql = f"""SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, p.elevacion_target
        FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        INNER JOIN componentes co ON i.id_componente = co.id_componente
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = cur.fetchall()
            if row:
                return [tuple(r) for r in row]
            else:
                return None
        except Exception as e:
            print("Error al consultar variacion coordenadas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerVariacionCoordenadasFechas(tabla, prismas, idcomponente, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente, fechaini, fechafin]
        sql = f"""SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, p.elevacion_target
        FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        INNER JOIN componentes co ON i.id_componente = co.id_componente
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
        AND p.hora_prisma BETWEEN ? AND ? ORDER BY p.nombre_prisma, p.hora_prisma;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = cur.fetchall()
            if row:
                return [tuple(r) for r in row]
            else:
                return None
        except Exception as e:
            print("Error al consultar variacion coordenadas fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
             
    @staticmethod
    def mdlCalcularVelocidadIV(tabla, prismas, idcomponente, unidadmedida):
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidadmedida] + prismas + [idcomponente]
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = f"""
            WITH inversoVelocidad AS (
                SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma,
                    (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 3600.0) AS horas,
                    (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
                    SQRT(
                        POWER(CAST(p.este_target AS FLOAT) - FIRST_VALUE(CAST(p.este_target AS FLOAT)) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                        POWER(CAST(p.norte_target AS FLOAT) - FIRST_VALUE(CAST(p.norte_target AS FLOAT)) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                        POWER(CAST(p.elevacion_target AS FLOAT) - FIRST_VALUE(CAST(p.elevacion_target AS FLOAT)) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                    ) * CAST(? AS FLOAT) AS tresD
                FROM {tabla} p 
                INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
                INNER JOIN componentes co ON i.id_componente = co.id_componente
                WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
                AND p.nombre_prisma IN ({placeholders}) 
                AND i.id_componente = ?
                AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
            )
            SELECT id_instrumentacion, nombre_prisma, hora_prisma, dias, horas,
                CASE WHEN tresD = 0 THEN 0 ELSE (horas/tresD) END AS iv_horas,
                CASE WHEN tresD = 0 THEN 0 ELSE (dias/tresD) END AS iv_dias
            FROM inversoVelocidad
            ORDER BY nombre_prisma, hora_prisma;
            """
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = [tuple(row) for row in cur.fetchall()]
            if rows:
                return rows
            else:
                return None
        except Exception as e:
            print("Error al consultar inversa velocidad: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlCalcularVelocidadFechasIV(tabla, prismas, idcomponente, fechaini, fechafin, unidadmedida):
        placeholders = ', '.join(['?' for _ in prismas])
        params = [unidadmedida] + prismas + [idcomponente] + [fechaini] + [fechafin]
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = f"""
            WITH inversoVelocidad AS (
                SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma,
                    (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 3600.0) AS horas,
                    (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
                    SQRT(
                        POWER(CAST(p.este_target AS FLOAT) - FIRST_VALUE(CAST(p.este_target AS FLOAT)) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                        POWER(CAST(p.norte_target AS FLOAT) - FIRST_VALUE(CAST(p.norte_target AS FLOAT)) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                        POWER(CAST(p.elevacion_target AS FLOAT) - FIRST_VALUE(CAST(p.elevacion_target AS FLOAT)) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                    ) * CAST(? AS FLOAT) AS tresD
                FROM {tabla} p 
                INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
                INNER JOIN componentes co ON i.id_componente = co.id_componente
                WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
                AND p.nombre_prisma IN ({placeholders}) 
                AND i.id_componente = ?
                AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
                AND p.hora_prisma BETWEEN ? AND ?
            )
            SELECT id_instrumentacion, nombre_prisma, hora_prisma, dias, horas,
                CASE WHEN tresD = 0 THEN 0 ELSE (horas/tresD) END AS iv_horas,
                CASE WHEN tresD = 0 THEN 0 ELSE (dias/tresD) END AS iv_dias
            FROM inversoVelocidad
            ORDER BY nombre_prisma, hora_prisma;
            """
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = [tuple(row) for row in cur.fetchall()]
            if rows:
                return rows
            else:
                return None
        except Exception as e:
            print("Error al consultar inversa velocidad por fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()   
    
    @staticmethod
    def mdlObtenerDataEstereografia(idproyecto):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = """SELECT * FROM estereografias WHERE id_proyecto = ?;"""
            cur = conn.cursor()
            cur.execute(sql, (idproyecto,))
            results = cur.fetchall()
            if results:
                return [tuple(r) for r in results]
            else:
                return None
        except Exception as e:
            print("Error al obtener estereografias: ", e)
            return None  
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerTrendPlunge(tabla, prismas):
        placeholders = ', '.join(['?' for _ in prismas])
        # Nota: SQRT y POWER son soportados en T-SQL. DEGREES y ATAN tambien.
        sql = f"""WITH Desplazamientos AS (
            SELECT nombre_prisma, hora_prisma, este_target, norte_target, elevacion_target,
                este_target - FIRST_VALUE(este_target) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) AS desplaza_este,
                norte_target - FIRST_VALUE(norte_target) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) AS desplaza_norte,
                elevacion_target - FIRST_VALUE(elevacion_target) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) AS desplaza_elevacion
            FROM {tabla} WHERE state_prisma = 1 AND estado_prisma = 1 AND nombre_prisma IN ({placeholders})
        ),
        MagnitudCalculada AS (
            SELECT nombre_prisma, hora_prisma, este_target, norte_target, elevacion_target, desplaza_este, desplaza_norte,
            desplaza_elevacion, sqrt(power(CAST(desplaza_norte AS FLOAT), 2) + power(CAST(desplaza_este AS FLOAT), 2)) AS magnitud
            FROM Desplazamientos
        ),
        Resultados AS (
            SELECT *,
                CASE
                    WHEN desplaza_norte IS NULL OR desplaza_este IS NULL THEN NULL
                    WHEN desplaza_norte = 0 AND desplaza_este = 0 THEN 0
                    WHEN desplaza_norte = 0 AND desplaza_este > 0 THEN 90
                    WHEN desplaza_norte = 0 AND desplaza_este < 0 THEN 270
                    WHEN desplaza_este = 0 AND desplaza_norte > 0 THEN 0
                    WHEN desplaza_este = 0 AND desplaza_norte < 0 THEN 180
                    WHEN desplaza_este > 0 THEN 90 - DEGREES(ATAN(desplaza_norte / desplaza_este))
                    WHEN desplaza_este < 0 THEN 270 - DEGREES(ATAN(desplaza_norte / desplaza_este))
                END AS trend,
                CASE
                    WHEN magnitud IS NULL OR desplaza_elevacion IS NULL THEN NULL
                    WHEN magnitud != 0 THEN DEGREES(ATAN(desplaza_elevacion / magnitud))
                    ELSE 90
                END AS plunge,
                ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma DESC) AS RowAsc
            FROM MagnitudCalculada
        )
        SELECT nombre_prisma, trend, plunge
        FROM Resultados
        WHERE RowAsc = 1;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, prismas)
            row = cur.fetchall()
            if row:
                return [tuple(r) for r in row]
            else:
                return None
        except Exception as e:
            print("Error al consultar trend plunge: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerTrendPlungeFechas(tabla, prismas, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [fechaini] + [fechafin]
        sql = f"""WITH Desplazamientos AS (
            SELECT nombre_prisma, hora_prisma, este_target, norte_target, elevacion_target,
                este_target - FIRST_VALUE(este_target) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) AS desplaza_este,
                norte_target - FIRST_VALUE(norte_target) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) AS desplaza_norte,
                elevacion_target - FIRST_VALUE(elevacion_target) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) AS desplaza_elevacion
            FROM {tabla} WHERE state_prisma = 1 AND estado_prisma = 1 AND nombre_prisma IN ({placeholders})
            AND hora_prisma BETWEEN ? AND ?
        ),
        MagnitudCalculada AS (
            SELECT nombre_prisma, hora_prisma, este_target, norte_target, elevacion_target, desplaza_este, desplaza_norte,
            desplaza_elevacion, sqrt(power(CAST(desplaza_norte AS FLOAT), 2) + power(CAST(desplaza_este AS FLOAT), 2)) AS magnitud
            FROM Desplazamientos
        ),
        Resultados AS (
            SELECT *,
                CASE
                    WHEN desplaza_norte IS NULL OR desplaza_este IS NULL THEN NULL
                    WHEN desplaza_norte = 0 AND desplaza_este = 0 THEN 0
                    WHEN desplaza_norte = 0 AND desplaza_este > 0 THEN 90
                    WHEN desplaza_norte = 0 AND desplaza_este < 0 THEN 270
                    WHEN desplaza_este = 0 AND desplaza_norte > 0 THEN 0
                    WHEN desplaza_este = 0 AND desplaza_norte < 0 THEN 180
                    WHEN desplaza_este > 0 THEN 90 - DEGREES(ATAN(desplaza_norte / desplaza_este))
                    WHEN desplaza_este < 0 THEN 270 - DEGREES(ATAN(desplaza_norte / desplaza_este))
                END AS trend,
                CASE
                    WHEN magnitud IS NULL OR desplaza_elevacion IS NULL THEN NULL
                    WHEN magnitud != 0 THEN DEGREES(ATAN(desplaza_elevacion / magnitud))
                    ELSE 90
                END AS plunge,
                ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma DESC) AS RowAsc
            FROM MagnitudCalculada
        )
        SELECT nombre_prisma, trend, plunge
        FROM Resultados
        WHERE RowAsc = 1;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = cur.fetchall()
            if row:
                return [tuple(r) for r in row]
            else:
                return None
        except Exception as e:
            print("Error al consultar trend plunge: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlComprobarDatosEstereografia(idproyecto, numero):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = """SELECT * FROM estereografias WHERE id_proyecto = ? AND codigo_estereografia = ?;"""
            cur = conn.cursor()
            cur.execute(sql, (idproyecto, numero))
            row = cur.fetchone()
            if row:
                return True
            else:
                return False
        except Exception as e:
            print("Error al obtener datos:", e)
            return False  
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlActualizarDatosEstereografia(idproyecto, nombre, inclinacion, direccion, numero):
        conn = None
        sql = """UPDATE estereografias SET nombre_estereografia = ?, inclinacion_estereografia = ?, direccion_estereografia = ?
        WHERE id_proyecto = ? AND codigo_estereografia = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (nombre, inclinacion, direccion, idproyecto, numero))
            conn.commit()
            return True
        except Exception as e:
            print("Error al actualizar Talud:", e)
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlGuardarDatosEstereografia(idproyecto, nombre, inclinacion, direccion, numero):
        conn = None
        sql = """INSERT INTO estereografias (id_proyecto, nombre_estereografia, inclinacion_estereografia, direccion_estereografia,
        codigo_estereografia) VALUES (?, ?, ?, ?, ?);"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idproyecto, nombre, inclinacion, direccion, numero))
            conn.commit()
            return True
        except Exception as e:
            print("Error al guardar talud:", e)
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlEliminaeDatoEstereografia(idproyecto, numero):
        conn = None
        sql = """DELETE FROM estereografias WHERE id_proyecto = ? AND codigo_estereografia = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idproyecto, numero))
            conn.commit()
            if cur.rowcount > 0:
                return True
            else:
                return False
        except Exception as e:
            print("Error al eliminar estereografía: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlResumenPrismas(tabla, unidad):
        conn = None
        # Transpilación: JULIANDAY -> DATEDIFF (Segundos) / 86400
        # +1 en SQLite implicaba inclusivo, mantenemos la lógica.
        sql = f"""
            SELECT nombre_prisma, MIN(hora_prisma) AS fecha_minima, MAX(hora_prisma) AS fecha_maxima,
                COUNT(*) AS cantidad,
                (CAST(DATEDIFF(SECOND, MIN(hora_prisma), MAX(hora_prisma)) AS FLOAT) / 86400.0) + 1.0 as total_dias,
                COUNT(*) / (((CAST(DATEDIFF(SECOND, MIN(hora_prisma), MAX(hora_prisma)) AS FLOAT) / 86400.0) + 1.0) / CAST(? AS FLOAT)) AS ratio
            FROM {tabla}
            WHERE state_prisma = 1 AND estado_prisma = 1
            GROUP BY nombre_prisma;
        """
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (unidad,))
            rows = cur.fetchall()
            return [tuple(r) for r in rows]
        except Exception as e:
            print("Error al consultar Resumen prisma: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerDataElipseError(tabla, nombreprisma):
        sql = f"""SELECT nombre_prisma, este_target, norte_target, elevacion_target
        FROM {tabla} WHERE state_prisma = 1 AND estado_prisma = 1 AND nombre_prisma = ?
        ORDER BY hora_prisma;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (nombreprisma,))
            rows = cur.fetchall()
            if rows:
                return [tuple(r) for r in rows]
            else:
                return None
        except Exception as e:
            print("Error al consultar coordenadas del prisma: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerDataElipseErrorFechas(tabla, nombreprisma, fechainicial, fechafinal):
        sql = f"""SELECT nombre_prisma, este_target, norte_target, elevacion_target
        FROM {tabla} WHERE state_prisma = 1 AND estado_prisma = 1 AND nombre_prisma = ?
        AND hora_prisma BETWEEN ? AND ? ORDER BY hora_prisma;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (nombreprisma, fechainicial, fechafinal))
            rows = cur.fetchall()
            if rows:
                return [tuple(r) for r in rows]
            else:
                return None
        except Exception as e:
            print("Error al consultar coordenadas del prisma fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
       
    @staticmethod
    def mdlObtenerDataPrismas(tabla, nombreprisma):
        sql = f"""SELECT id_prisma, hora_prisma, nombre_prisma, este_target, norte_target, elevacion_target, distancia_prisma
        FROM {tabla} WHERE state_prisma = 1 AND estado_prisma = 1 AND nombre_prisma = ?
        ORDER BY hora_prisma;"""
        conn = None
        try:
            conn = Connection.connectionDB() 
            cur = conn.cursor()
            cur.execute(sql, (nombreprisma,))
            rows = cur.fetchall()
            if rows:
                return [tuple(r) for r in rows]
            else:
                return None
        except Exception as e:
            print("Error al consultar coordenadas del prisma: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlObtenerDataPrismasDesviaciones(tabla, idproyecto, componente, nombreprisma, tipoprisma):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()

            # Transpilación: LIMIT 1 -> TOP 1
            cur.execute('''
                SELECT TOP 1 ultima_fecha_modificada
                FROM registro_limpieza_desviaciones
                WHERE id_proyecto = ? AND id_componente = ? AND equipo = ? AND tipo_equipo = ?
                ORDER BY ultima_fecha_modificada DESC
            ''', (idproyecto, componente, nombreprisma, tipoprisma))

            row = cur.fetchone()

            if row:
                ultima_fecha_modificada = row[0]
                sql = f"""
                    SELECT id_prisma, hora_prisma, nombre_prisma, este_target, norte_target, elevacion_target, distancia_prisma
                    FROM {tabla}
                    WHERE state_prisma = 1 AND estado_prisma = 1 AND nombre_prisma = ? AND hora_prisma > ?
                    ORDER BY hora_prisma;
                """
                cur.execute(sql, (nombreprisma, ultima_fecha_modificada))
                rows = cur.fetchall()

                if rows:
                    return [tuple(r) for r in rows]
                else:
                    return None
            else:
                sql = f"""
                    SELECT id_prisma, hora_prisma, nombre_prisma, este_target, norte_target, elevacion_target, distancia_prisma
                    FROM {tabla}
                    WHERE state_prisma = 1 AND estado_prisma = 1 AND nombre_prisma = ?
                    ORDER BY hora_prisma;
                """
                cur.execute(sql, (nombreprisma,))
                rows = cur.fetchall()

                if rows:
                    return [tuple(r) for r in rows]
                else:
                    return None

        except Exception as e:
            print("Error al consultar coordenadas del prisma: " + str(e))
            return None

        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlActualizarDataLimpiaPrismas(tabla, datos, lote=250):
        # Nota: Lote reducido a 250 para evitar límite de parámetros SQL Server (2100)
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # Validar nombre de tabla para evitar inyeccion
            if not tabla.replace("_", "").isalnum():
                return False
            
            # En SQL Server no se usan PRAGMAs de SQLite
            
            # Transpilación: IF OBJECT_ID en vez de IF NOT EXISTS para tablas
            # Tipos de datos ajustados a T-SQL (INT, VARCHAR, FLOAT)
            cursor.execute(f"""
            IF OBJECT_ID('backup_{tabla}', 'U') IS NULL
            CREATE TABLE backup_{tabla} (
                id_prisma INT NOT NULL,
                hora_prisma DATETIME2(0) NOT NULL,
                nombre_prisma VARCHAR(50) NOT NULL,
                este_target FLOAT NOT NULL,
                norte_target FLOAT NOT NULL,
                elevacion_target FLOAT NOT NULL,
                distancia_prisma FLOAT NOT NULL,
                fecha_backup DATETIME2(0) NOT NULL
            );
            """)
            # Indices
            cursor.execute(f"IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_backup_{tabla}_id_prisma') CREATE INDEX idx_backup_{tabla}_id_prisma ON backup_{tabla}(id_prisma);")
            cursor.execute(f"IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_backup_{tabla}_fecha') CREATE INDEX idx_backup_{tabla}_fecha ON backup_{tabla}(fecha_backup);")
            
            timestamp = datetime.datetime.now().isoformat()
            
            # Manejo de Transacciones pyodbc
            # pyodbc maneja transacciones con commit/rollback en el objeto connection
            
            for i in range(0, len(datos), lote):
                batch = datos[i:i + lote]
                ids = [str(registro[0]) for registro in batch]  # id_prisma
                
                # 1. Hacer backup
                cursor.execute(f"""
                INSERT INTO backup_{tabla} (
                    id_prisma, hora_prisma, nombre_prisma, 
                    este_target, norte_target, elevacion_target, distancia_prisma,
                    fecha_backup
                )
                SELECT 
                    id_prisma, hora_prisma, nombre_prisma, 
                    este_target, norte_target, elevacion_target, distancia_prisma,
                    ?
                FROM {tabla}
                WHERE id_prisma IN ({','.join(['?']*len(ids))})
                """, [timestamp] + ids)
                
                # 2. Preparar actualización
                # Construcción de CASE WHEN es compatible con T-SQL
                update_sql = f"""
                UPDATE {tabla} 
                SET este_target = CASE id_prisma {' '.join([f"WHEN ? THEN ?" for _ in batch])} ELSE este_target END,
                    norte_target = CASE id_prisma {' '.join([f"WHEN ? THEN ?" for _ in batch])} ELSE norte_target END,
                    elevacion_target = CASE id_prisma {' '.join([f"WHEN ? THEN ?" for _ in batch])} ELSE elevacion_target END
                WHERE id_prisma IN ({','.join(['?']*len(ids))})
                """
                
                # 3. Preparar parámetros
                params = []
                for row in batch:
                    id_prisma = row[0]
                    este = float(row[3]) if isinstance(row[3], (np.float64, np.float32)) else row[3]
                    params.extend([id_prisma, este])
                for row in batch:
                    id_prisma = row[0]
                    norte = float(row[4]) if isinstance(row[4], (np.float64, np.float32)) else row[4]
                    params.extend([id_prisma, norte])
                for row in batch:
                    id_prisma = row[0]
                    elevacion = float(row[5]) if isinstance(row[5], (np.float64, np.float32)) else row[5]
                    params.extend([id_prisma, elevacion])
                params.extend(ids)
                
                cursor.execute(update_sql, params)
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error en actualización: {str(e)}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlRestablecerDataPrismasElipse(tabla, nombreprisma, lote=200):
        # Lote reducido a 200 por seguridad de parámetros
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            if not tabla.replace("_", "").isalnum():
                return False
            
            # Sin Pragmas
            tabla_backup = f"backup_{tabla}"
            
            # 1. Obtener fecha backup
            cursor.execute(f"""
                SELECT MAX(fecha_backup)
                FROM {tabla_backup}
                WHERE nombre_prisma = ?
            """, (nombreprisma,))
            resultado = cursor.fetchone()
            fecha_backup_actual = resultado[0] if resultado else None
            
            if not fecha_backup_actual:
                print("No hay backups para restaurar.")
                return False
            
            # 2. Procesar en lotes
            while True:
                # SQL Server usa TOP en lugar de LIMIT
                cursor.execute(f"""SELECT TOP (?) id_prisma, este_target, norte_target, elevacion_target
                    FROM {tabla_backup}
                    WHERE nombre_prisma = ? AND fecha_backup = ?
                """, (lote, nombreprisma, fecha_backup_actual))
                
                batch = cursor.fetchall()
                if not batch:
                    break
                
                ids = [str(row[0]) for row in batch]
                
                update_sql = f"""
                UPDATE {tabla}
                SET 
                    este_target = CASE id_prisma {' '.join(['WHEN ? THEN ?' for _ in batch])} ELSE este_target END,
                    norte_target = CASE id_prisma {' '.join(['WHEN ? THEN ?' for _ in batch])} ELSE norte_target END,
                    elevacion_target = CASE id_prisma {' '.join(['WHEN ? THEN ?' for _ in batch])} ELSE elevacion_target END
                WHERE id_prisma IN ({','.join(['?'] * len(ids))})
                """
                
                params = []
                for row in batch:
                    params.extend([row[0], row[1]])
                for row in batch:
                    params.extend([row[0], row[2]])
                for row in batch:
                    params.extend([row[0], row[3]])
                params.extend(ids)
                
                cursor.execute(update_sql, params)
                
                cursor.execute(f"""
                    DELETE FROM {tabla_backup}
                    WHERE id_prisma IN ({','.join(['?'] * len(ids))})
                    AND nombre_prisma = ? AND fecha_backup = ?
                """, ids + [nombreprisma, fecha_backup_actual])
                
                conn.commit() # Commit por lote
            
            return True
        except Exception as e:
            print(f"Error en restauracion de prismas: {str(e)}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlRegistroAjusteCoordenadas(idproyecto, tabla, nombre_prisma, campo, id_prisma, current_value, nuevo_valor, fecha, username, nombres):
        sql = """INSERT INTO registro_ajuste_coordenadas (id_proyecto, tabla_modificada, nombre_equipo, columna_modificada,
        numero_fila, valor_anterior, nuevo_valor, fecha_cambio, usuario_cambio, nombres_cambio) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idproyecto, tabla, nombre_prisma, campo, id_prisma, current_value, nuevo_valor, fecha, username, nombres))
            conn.commit()
            return True
        except Exception as e:
            print("Error al registrar cambios", e)
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlVerificarSIdesviaciones(proyecto):
        conn = None
        try:
            conn = Connection.connectionDB()
            # SQL Server permite SELECT 1
            sql = "SELECT 1 FROM desviaciones WHERE id_proyecto = ?;"
            cur = conn.cursor()
            cur.execute(sql, (proyecto,))
            return cur.fetchone() is not None
        except Exception:
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlObtenerDataDesviacionesPrisma(proyecto,tabla, fecha_calculo,nombreprisma):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()

            # Verificar tabla en SQL Server (Information Schema)
            cur.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = ?", (tabla,))
            if not cur.fetchone():
                print(f"Error: La tabla '{tabla}' no existe en el proyecto {proyecto}")
                return None

            sql = """
            SELECT nombre_prisma, hora_prisma, este_target, norte_target, elevacion_target
            FROM {}
            WHERE nombre_prisma=?  AND hora_prisma <= ? ORDER BY hora_prisma ASC
            """.format(tabla)

            cur.execute(sql, (nombreprisma, fecha_calculo))
            results = cur.fetchall()
            return [tuple(r) for r in results] if results else None

        except Exception as e:
            print(f"Error al obtener desviaciones proyecto {proyecto}: {e}")
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlGuardarDesviaciones(idproyecto, desviaciones):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()

            cur.execute("DELETE FROM desviaciones WHERE id_proyecto = ?", (idproyecto,))

            for desviacion in desviaciones:
                cur.execute("""
                    INSERT INTO desviaciones (
                        id_proyecto,
                        nombre_prisma,
                        centro_este,
                        desviacion_este,
                        centro_norte,
                        desviacion_norte,
                        centro_cota,
                        desviacion_cota,
                        fecha_calculo
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    desviacion['id_proyecto'],
                    desviacion['nombre_prisma'],
                    desviacion['centro_este'],
                    desviacion['desviacion_este'],
                    desviacion['centro_norte'],
                    desviacion['desviacion_norte'],
                    desviacion['centro_cota'],
                    desviacion['desviacion_cota'],
                    desviacion['fecha_calculo']
                ))

            conn.commit()
            return True
        except Exception as e:
            print(f"Error al guardar desviaciones: {str(e)}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlGuardarDesviacionesPrisma(idproyecto, desviaciones):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            
            for desviacion in desviaciones:
                cur.execute("""
                    INSERT INTO desviaciones (
                        id_proyecto,
                        nombre_prisma,
                        centro_este,
                        desviacion_este,
                        centro_norte,
                        desviacion_norte,
                        centro_cota,
                        desviacion_cota,
                        fecha_calculo
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    desviacion['id_proyecto'],
                    desviacion['nombre_prisma'],
                    desviacion['centro_este'],
                    desviacion['desviacion_este'],
                    desviacion['centro_norte'],
                    desviacion['desviacion_norte'],
                    desviacion['centro_cota'],
                    desviacion['desviacion_cota'],
                    desviacion['fecha_calculo']
                ))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al guardar desviaciones: {str(e)}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
        
    @staticmethod
    def mdlGuardarDesviacionesManualesPrisma(idproyecto, desviaciones):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()

            for desviacion in desviaciones:
                cur.execute("""
                    SELECT COUNT(*)
                    FROM desviaciones
                    WHERE id_proyecto = ? AND nombre_prisma = ?
                """, (desviacion['id_proyecto'], desviacion['nombre_prisma']))

                if cur.fetchone()[0] > 0:
                    cur.execute("""
                        UPDATE desviaciones
                        SET
                            centro_este = ?,
                            desviacion_este = ?,
                            centro_norte = ?,
                            desviacion_norte = ?,
                            centro_cota = ?,
                            desviacion_cota = ?,
                            fecha_calculo = ?
                        WHERE id_proyecto = ? AND nombre_prisma = ?
                    """, (
                        desviacion['centro_este'],
                        desviacion['desviacion_este'],
                        desviacion['centro_norte'],
                        desviacion['desviacion_norte'],
                        desviacion['centro_cota'],
                        desviacion['desviacion_cota'],
                        desviacion['fecha_calculo'],
                        desviacion['id_proyecto'],
                        desviacion['nombre_prisma']
                    ))
                else:
                    cur.execute("""
                        INSERT INTO desviaciones (
                        id_proyecto,
                        nombre_prisma,
                        centro_este,
                        desviacion_este,
                        centro_norte,
                        desviacion_norte,
                        centro_cota,
                        desviacion_cota,
                        fecha_calculo
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    desviacion['id_proyecto'],
                    desviacion['nombre_prisma'],
                    desviacion['centro_este'],
                    desviacion['desviacion_este'],
                    desviacion['centro_norte'],
                    desviacion['desviacion_norte'],
                    desviacion['centro_cota'],
                    desviacion['desviacion_cota'],
                    desviacion['fecha_calculo']
                ))

            conn.commit()
            return True
        except Exception as e:
            print(f"Error al guardar desviaciones: {str(e)}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlObtenerDesviacionesPrisma(idproyecto, nombreprisma):
        sql = f"""SELECT * FROM desviaciones WHERE id_proyecto=? AND nombre_prisma=? """
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idproyecto,nombreprisma))
            row = cur.fetchall()
            if row:
                return [tuple(r) for r in row]
            else:
                return None
        except Exception as e:
            print("Error al listar prismas trayectoria: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
                
    @staticmethod
    def mdlObtenerDataDesviacionesAuto(proyecto, tabla, fecha_calculo):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = ?", (tabla,))
            if not cur.fetchone():
                print(f"Error: La tabla '{tabla}' no existe en el proyecto {proyecto}")
                return None
            sql = """
            SELECT nombre_prisma, hora_prisma, este_target, norte_target, elevacion_target
            FROM {}
            WHERE hora_prisma <= ? AND state_prisma = 1 AND estado_prisma = 1
            """.format(tabla)
            cur.execute(sql, (fecha_calculo,))
            results = cur.fetchall()
            return [tuple(r) for r in results]
        except Exception as e:
            print(f"Error al obtener datos de {tabla} para proyecto {proyecto}: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerDataDesviacionesManual(proyecto, tabla, fecha_calculo):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = ?", (tabla,))
            if not cur.fetchone():
                print(f"Error: La tabla '{tabla}' no existe en el proyecto {proyecto}")
                return None

            sql = """
            SELECT nombre_prisma, hora_prisma, este_target, norte_target, elevacion_target
            FROM {}
            WHERE hora_prisma <= ? AND state_prisma = 1 AND estado_prisma = 1
            """.format(tabla)

            cur.execute(sql, (fecha_calculo,))
            results = cur.fetchall()
            return [tuple(r) for r in results]

        except Exception as e:
            print(f"Error al obtener datos de {tabla} para proyecto {proyecto}: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlRegistroBackup(nombre, id_lectura, tabla, fecha_equipo, coordenada_este, coordenada_norte, coordenada_cota, distancia_inclinada, fecha_modificacion):
        sql_check = "SELECT 1 FROM registro_cambios_prismas WHERE indice_lectura = ? AND nombre_equipo = ?"
        sql_insert = """
        INSERT INTO registro_cambios_prismas
        (nombre_equipo, indice_lectura, tabla_equipo, fecha_equipo, coordenada_este, coordenada_norte, coordenada_cota, distancia_inclinada, fecha_modificacion)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()

            cur.execute(sql_check, (id_lectura, nombre))
            if cur.fetchone():
                return "Registro ya existe, no se insertó."
            cur.execute(sql_insert, (nombre, id_lectura, tabla, fecha_equipo, coordenada_este, coordenada_norte, coordenada_cota, distancia_inclinada, fecha_modificacion))
            conn.commit()
            return "Registro insertado con éxito."
        except Exception as e:
            print(f"Error al hacer buckpup de cambios: {e}")
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlRestaurarEquipo(idproyecto, nombreprisma, tipoprisma):
        tabla_prismas = f"prismas{idproyecto}"
        sql_select = """
        SELECT indice_lectura, coordenada_este, coordenada_norte, coordenada_cota, distancia_inclinada
        FROM registro_cambios_prismas
        WHERE nombre_equipo = ? AND tabla_equipo = ?
        """
        sql_update = f"""
        UPDATE {tabla_prismas}
        SET este_target = ?,
            norte_target = ?,
            elevacion_target = ?,
            distancia_prisma = ?
        WHERE id_prisma = ?
        """
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql_select, (nombreprisma, tabla_prismas))
            rows = cur.fetchall()
            if rows:
                for row in rows:
                    indice_lectura, este, norte, cota, distancia = row
                    cur.execute(sql_update, (este, norte, cota, distancia, indice_lectura))
                conn.commit()
                return True,"Registros actualizados con éxito."
            else:
                return False,f"No existe backup para el equipo '{nombreprisma}'."
        except Exception as e:
            print(f"Error al restaurar equipos: {e}")
            return False,"Error al restaurar el equipo."
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlRegitroUltimaLimpiezaElipse(idproyecto,componente,nombre_prisma,tipoprisma,hora_prisma):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # Transpilación: Sintaxis CREATE TABLE SQL Server. IDENTITY en vez de AUTOINCREMENT
            cur.execute('''
                IF OBJECT_ID('registro_limpieza_desviaciones', 'U') IS NULL
                CREATE TABLE registro_limpieza_desviaciones (
                    id_registro INT IDENTITY(1,1) PRIMARY KEY,
                    id_proyecto INT,
                    id_componente INT,
                    equipo VARCHAR(255),
                    tipo_equipo VARCHAR(255),
                    ultima_fecha_modificada DATETIME2(0)
                )
            ''')
            cur.execute('''
                INSERT INTO registro_limpieza_desviaciones (id_proyecto, id_componente, equipo, tipo_equipo, ultima_fecha_modificada)
                VALUES (?, ?, ?, ?, ?)
            ''', (idproyecto, componente, nombre_prisma, tipoprisma, hora_prisma))
            conn.commit()
        except Exception as e:
            print(f"Error al registrar la limpieza: {e}")
            return False
        finally:
            if conn:
                conn.close()
        return True
    
    @staticmethod
    def mdlEliminarRegistroLimpiezaDesviaciones(idproyecto, nombreprisma, tipoprisma):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # Transpilación: TOP 1 en subconsulta
            cur.execute('''
                DELETE FROM registro_limpieza_desviaciones
                WHERE id_registro = (
                    SELECT TOP 1 id_registro
                    FROM registro_limpieza_desviaciones
                    WHERE id_proyecto = ? AND equipo = ? AND tipo_equipo = ?
                    ORDER BY ultima_fecha_modificada DESC
                )
            ''', (idproyecto, nombreprisma, tipoprisma))
            conn.commit()
        except Exception as e:
            print(f"Error al eliminar el registro: {e}")
        finally:
            if conn:
                conn.close()
            
    @staticmethod
    def mdlAjustarDataPrismaCoordenada(df_ajustado, tabla, idcomponente):
        conn = None
        cursor = None
        existe = True
        try:
            conn = Connection.connectionDB()
            # Se eliminan los PRAGMAS de SQLite
            cursor = conn.cursor()
            
            # PASO 1: VERIFICAR Y CREAR BACKUP COMPLETO EN LA TABLA PRINCIPAL
            nombre_original = df_ajustado['nombre'].iloc[0]
            nombre_backup = f"{nombre_original}_original"
            cursor.execute(f"SELECT COUNT(*) FROM {tabla} WHERE nombre_prisma = ?", (nombre_original,))
            total_originales = cursor.fetchone()[0]
            cursor.execute(f"SELECT COUNT(*) FROM {tabla} WHERE nombre_prisma = ?", (nombre_backup,))
            total_backup = cursor.fetchone()[0]
            
            # Nota: SQL Server IDENTITY columns cannot be inserted directly without IDENTITY_INSERT ON.
            # Asumimos que id_prisma es IDENTITY. Lo excluimos del INSERT y del SELECT.
            
            # Columnas comunes (excluyendo id_prisma que se autogenera)
            columnas_sql = """
                state_prisma, estado_prisma, nombre_prisma, perfil_prisma, hora_prisma,
                angulo_horizontal, angulo_vertical, distancia_prisma, tipoppm_prisma,
                ppm_prisma, presion_prisma, temperatura_prisma, constante_prisma,
                este_target, norte_target, elevacion_target, altura_reflector,
                altura_instrumento, este_estacion, norte_estacion, altura_estacion,
                medicion_prisma, diferencia_tiempocorto, diferencia_tiempolargo,
                diferencia_limitevelocidad, distancia_horizontal, diferencia_atipica,
                desplaza_longitudinal, desplaza_transversal, desplaza_altura, grupo_puntos
            """
            
            if total_backup == 0:
                # Se asigna el nombre nuevo mediante parámetro, no en el select
                cursor.execute(f"""
                INSERT INTO {tabla} ({columnas_sql})
                SELECT 
                    state_prisma, estado_prisma, ? as nombre_prisma, perfil_prisma, hora_prisma,
                    angulo_horizontal, angulo_vertical, distancia_prisma, tipoppm_prisma,
                    ppm_prisma, presion_prisma, temperatura_prisma, constante_prisma,
                    este_target, norte_target, elevacion_target, altura_reflector,
                    altura_instrumento, este_estacion, norte_estacion, altura_estacion,
                    medicion_prisma, diferencia_tiempocorto, diferencia_tiempolargo,
                    diferencia_limitevelocidad, distancia_horizontal, diferencia_atipica,
                    desplaza_longitudinal, desplaza_transversal, desplaza_altura, grupo_puntos
                FROM {tabla} WHERE nombre_prisma = ?
                """, (nombre_backup, nombre_original))
            elif total_backup < total_originales:
                cursor.execute(f"""
                    SELECT p.id_prisma
                    FROM {tabla} p
                    LEFT JOIN {tabla} c ON (
                        c.nombre_prisma = ? 
                        AND c.hora_prisma = p.hora_prisma
                    )
                    WHERE p.nombre_prisma = ? AND c.id_prisma IS NULL
                    ORDER BY p.hora_prisma
                """, (nombre_backup, nombre_original))
                registros_faltantes = cursor.fetchall()
                ids_sin_backup = [str(row[0]) for row in registros_faltantes]
                
                if ids_sin_backup:
                    placeholders = ','.join('?' for _ in ids_sin_backup)
                    cursor.execute(f"""
                    INSERT INTO {tabla} ({columnas_sql})
                    SELECT 
                        state_prisma, estado_prisma, ? as nombre_prisma, perfil_prisma, hora_prisma,
                        angulo_horizontal, angulo_vertical, distancia_prisma, tipoppm_prisma,
                        ppm_prisma, presion_prisma, temperatura_prisma, constante_prisma,
                        este_target, norte_target, elevacion_target, altura_reflector,
                        altura_instrumento, este_estacion, norte_estacion, altura_estacion,
                        medicion_prisma, diferencia_tiempocorto, diferencia_tiempolargo,
                        diferencia_limitevelocidad, distancia_horizontal, diferencia_atipica,
                        desplaza_longitudinal, desplaza_transversal, desplaza_altura, grupo_puntos
                    FROM {tabla} 
                    WHERE nombre_prisma = ? AND id_prisma IN ({placeholders})
                    """, [nombre_backup, nombre_original] + ids_sin_backup)
            
            # PASO 2: VERIFICAR Y CREAR BACKUP EN INSTRUMENTACIÓN
            cursor.execute("""SELECT COUNT(*) FROM instrumentacion 
                        WHERE nombre_equipo = ? AND id_componente = ?""", 
                        (nombre_backup, idcomponente))
            existe_backup_instrumentacion = cursor.fetchone()[0] > 0
            
            if not existe_backup_instrumentacion:
                existe = False
                cursor.execute("""SELECT tipo_equipo, id_equipo, tabla_equipo
                FROM instrumentacion WHERE nombre_equipo = ? AND id_componente = ?
                """, (nombre_original, idcomponente))
                registro_instrumentacion = cursor.fetchone()
                if registro_instrumentacion:
                    cursor.execute("""
                    INSERT INTO instrumentacion 
                    (id_componente, tipo_equipo, nombre_equipo, id_equipo, tabla_equipo, estado_instrumentacion)
                    VALUES (?, ?, ?, ?, ?, 1)
                    """, (idcomponente,
                        registro_instrumentacion[0],  # tipo_equipo
                        nombre_backup,                # nombre_equipo
                        registro_instrumentacion[1],  # id_equipo
                        registro_instrumentacion[2]   # tabla_equipo
                    ))
            
            conn.commit()
            
            # PASO 4: ACTUALIZACIÓN POR LOTES
            query_actualizar = f"""UPDATE {tabla} SET 
                distancia_prisma = ?,
                este_target = ?, 
                norte_target = ?, 
                elevacion_target = ?
            WHERE id_prisma = ? AND nombre_prisma = ?
            """
            
            datos_actualizacion_segura = []
            for _, row in df_ajustado.iterrows():
                datos_actualizacion_segura.append((
                    row['distancia'],  # distancia_prisma
                    row['este'],       # este_target
                    row['norte'],      # norte_target
                    row['elevacion'],  # elevacion_target
                    row['id'],         # id_prisma
                    nombre_original    # nombre_prisma
                ))
            
            lote_size = 1000
            total_registros = len(datos_actualizacion_segura)
            
            # pyodbc executemany maneja los batches internamente mejor que construir strings enormes
            for i in range(0, total_registros, lote_size):
                lote = datos_actualizacion_segura[i:i + lote_size]
                cursor.executemany(query_actualizar, lote)
                conn.commit()
                
            return True, existe
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            return False, existe
        finally:
            if conn:
                try:
                    conn.close()
                except Exception as e:
                    print(f"Advertencia al cerrar conexión: {e}")
    
    @staticmethod
    def mdlListarSaltosPrisma(idproyecto, prisma):
        sql = f"""SELECT nombre_equipo, fecha_cambio, columna_modificada, valor_anterior, nuevo_valor, usuario_cambio
        FROM registro_ajuste_coordenadas WHERE id_proyecto = ? AND nombre_equipo = ?;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idproyecto, prisma))
            row = cur.fetchall()
            if row:
                return [tuple(r) for r in row]
            else:
                return None
        except Exception as e:
            print("Error al traer historial saltos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
                    
    @staticmethod
    def mdlObtenerDataCoordenadaAjuste(tabla, nombreprisma, columna):
        conn = None
        try:
            conn = Connection.connectionDB()
            # Validación simple de columna para evitar inyección
            valid_cols = ['este_target', 'norte_target', 'elevacion_target', 'distancia_prisma']
            if columna not in valid_cols:
                return None
                
            sql = f"""SELECT id_prisma,nombre_prisma, hora_prisma, {columna}
                    FROM {tabla}
                    WHERE nombre_prisma = ? AND estado_prisma=1 ORDER BY hora_prisma;"""
            cur = conn.cursor()
            cur.execute(sql, (nombreprisma,))
            results = cur.fetchall()
            return [tuple(r) for r in results] if results else None
        except Exception as e:
            print(f"Error al obtener data de coordenada: {e}")
            return None
        finally:
            if conn:
                conn.close()
                
    @staticmethod
    def mdlOmitirLecturasRuido(tabla, ids):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # Reducción de tamaño de batch para SQL Server
            batch_size = 400
            for i in range(0, len(ids), batch_size):
                batch = ids[i:i + batch_size]
                placeholders = ','.join(['?'] * len(batch))
                sql = f"""
                    UPDATE {tabla}
                    SET estado_prisma = 0
                    WHERE id_prisma IN ({placeholders});
                """
                cur.execute(sql, batch)
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al actualizar: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlPrismaDesplazamientosAnalisis(tabla, idinstrumento, unidad):
        conn = None
        sql = f"""SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma, i.tipo_equipo,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (SQRT(
                POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                POWER(p.elevacion_target - FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
            )) * {unidad} AS DA3D,
            CASE 
                WHEN LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                ELSE (SQRT(
                    POWER(p.este_target - LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.norte_target - LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.elevacion_target - LAG(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                )) * {unidad}
            END AS DI3D,
            (SQRT(
                POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
            )) * {unidad} AS DA2D,
            CASE 
                WHEN LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                ELSE (SQRT(
                    POWER(p.este_target - LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.norte_target - LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                )) * {unidad}
            END AS DI3D,
            (p.distancia_prisma - FIRST_VALUE(p.distancia_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * {unidad} AS DASD,
            CASE 
                WHEN LAG(p.distancia_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                ELSE (p.distancia_prisma - LAG(p.distancia_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * {unidad}
            END AS DISD,
            (p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * {unidad} AS DAES,
            CASE 
                WHEN LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                ELSE (p.este_target - LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * {unidad}
            END AS DIES,
            (p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * {unidad} AS DANO,
            CASE 
                WHEN LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                ELSE (p.norte_target - LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * {unidad}
            END AS DINO,
            (p.elevacion_target - FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * {unidad} AS DANI,
            CASE 
                WHEN LAG(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                ELSE (p.elevacion_target - LAG(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * {unidad}
            END AS DINI
        FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        INNER JOIN componentes co ON i.id_componente = co.id_componente
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND i.id_instrumentacion = ?
        AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
        ORDER BY p.hora_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idinstrumento))
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error en mdlPrismaDesplazamientosAnalisis: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlPrismaDesplazamientosAnalisisFechas(tabla, idinstrumento, unidad, fechainicial, fechafinal):
        conn = None
        sql = f"""SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma, i.tipo_equipo,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
            (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) * 24.0 AS horas,
            (SQRT(
                POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                POWER(p.elevacion_target - FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
            )) * {unidad} AS DA3D,
            CASE 
                WHEN LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                ELSE (SQRT(
                    POWER(p.este_target - LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.norte_target - LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.elevacion_target - LAG(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                )) * {unidad}
            END AS DI3D,
            (SQRT(
                POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
            )) * {unidad} AS DA2D,
            CASE 
                WHEN LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                ELSE (SQRT(
                    POWER(p.este_target - LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.norte_target - LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                )) * {unidad}
            END AS DI3D,
            (p.distancia_prisma - FIRST_VALUE(p.distancia_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * {unidad} AS DASD,
            CASE 
                WHEN LAG(p.distancia_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                ELSE (p.distancia_prisma - LAG(p.distancia_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * {unidad}
            END AS DISD,
            (p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * {unidad} AS DAES,
            CASE 
                WHEN LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                ELSE (p.este_target - LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * {unidad}
            END AS DIES,
            (p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * {unidad} AS DANO,
            CASE 
                WHEN LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                ELSE (p.norte_target - LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * {unidad}
            END AS DINO,
            (p.elevacion_target - FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * {unidad} AS DANI,
            CASE 
                WHEN LAG(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                ELSE (p.elevacion_target - LAG(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * {unidad}
            END AS DINI
        FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        INNER JOIN componentes co ON i.id_componente = co.id_componente
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND i.id_instrumentacion = ? AND p.hora_prisma BETWEEN ? AND ?
        AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
        ORDER BY p.hora_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idinstrumento, fechainicial, fechafinal))
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error en mdlPrismaDesplazamientosAnalisisFechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlPrismaVelocidadesAnalisis(tabla, idinstrumento, unidad):
        conn = None
        sql = f"""WITH PrismasCTE AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma, i.tipo_equipo,
                (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
                SQRT(
                    POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.elevacion_target - FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                ) AS DA3D,
                CASE 
                    WHEN LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                    ELSE SQRT(
                        POWER(p.este_target - LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                        POWER(p.norte_target - LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                        POWER(p.elevacion_target - LAG(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                    )
                END AS DI3D,
                SQRT(
                    POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                ) AS DA2D,
                CASE 
                    WHEN LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                    ELSE SQRT(
                        POWER(p.este_target - LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                        POWER(p.norte_target - LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                    )
                END AS DI2D,
                p.distancia_prisma - FIRST_VALUE(p.distancia_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS DASD,
                CASE 
                    WHEN LAG(p.distancia_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                    ELSE p.distancia_prisma - LAG(p.distancia_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)
                END AS DISD,
                p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS DAES,
                CASE 
                    WHEN LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                    ELSE p.este_target - LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)
                END AS DIES
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN componentes co ON i.id_componente = co.id_componente
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND i.id_instrumentacion = ?
            AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma, tipo_equipo, dias, dias * 24.0 AS horas,
            CASE
                WHEN ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) = 1 THEN 0
                ELSE
                    (DI3D - LAG(DI3D) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma))
                    / (CAST(DATEDIFF(SECOND, LAG(hora_prisma, 1, hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0)
            END * {unidad} AS VI3D,
            CASE
                WHEN dias = 0 THEN 0
                ELSE DA3D / dias
            END * {unidad} AS VA3D,
            CASE
                WHEN ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) = 1 THEN 0
                ELSE
                    (DI2D - LAG(DI2D) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma))
                    / (CAST(DATEDIFF(SECOND, LAG(hora_prisma, 1, hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0)
            END * {unidad} AS VI2D,
            CASE
                WHEN dias = 0 THEN 0
                ELSE DA2D / dias
            END * {unidad} AS VA2D,
            CASE
                WHEN ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) = 1 THEN 0
                ELSE
                    DISD
                    / (CAST(DATEDIFF(SECOND, LAG(hora_prisma, 1, hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0)
            END * {unidad} AS VISD,
            CASE
                WHEN dias = 0 THEN 0
                ELSE DASD / dias
            END * {unidad} AS VASD
        FROM PrismasCTE ORDER BY hora_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idinstrumento,))
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error en mdlPrismaVelocidadesAnalisis: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    def mdlPrismaVelocidadesAnalisisFechas(tabla, idinstrumento, unidad, fechainicial, fechafinal):
        conn = None
        sql = f"""WITH PrismasCTE AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma, i.tipo_equipo,
                (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
                SQRT(
                    POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.elevacion_target - FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                ) AS DA3D,
                CASE 
                    WHEN LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                    ELSE SQRT(
                        POWER(p.este_target - LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                        POWER(p.norte_target - LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                        POWER(p.elevacion_target - LAG(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                    )
                END AS DI3D,
                SQRT(
                    POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                ) AS DA2D,
                CASE 
                    WHEN LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                    ELSE SQRT(
                        POWER(p.este_target - LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                        POWER(p.norte_target - LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                    )
                END AS DI2D,
                p.distancia_prisma - FIRST_VALUE(p.distancia_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS DASD,
                CASE 
                    WHEN LAG(p.distancia_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                    ELSE p.distancia_prisma - LAG(p.distancia_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)
                END AS DISD,
                p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS DAES,
                CASE 
                    WHEN LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                    ELSE p.este_target - LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)
                END AS DIES
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN componentes co ON i.id_componente = co.id_componente
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND i.id_instrumentacion = ? AND p.hora_prisma BETWEEN ? AND ?
            AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma, tipo_equipo, dias, dias * 24.0 AS horas,
            CASE
                WHEN ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) = 1 THEN 0
                ELSE
                    (DI3D - LAG(DI3D) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma))
                    / (CAST(DATEDIFF(SECOND, LAG(hora_prisma, 1, hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0)
            END * {unidad} AS VI3D,
            CASE
                WHEN dias = 0 THEN 0
                ELSE DA3D / dias
            END * {unidad} AS VA3D,
            CASE
                WHEN ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) = 1 THEN 0
                ELSE
                    (DI2D - LAG(DI2D) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma))
                    / (CAST(DATEDIFF(SECOND, LAG(hora_prisma, 1, hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0)
            END * {unidad} AS VI2D,
            CASE
                WHEN dias = 0 THEN 0
                ELSE DA2D / dias
            END * {unidad} AS VA2D,
            CASE
                WHEN ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) = 1 THEN 0
                ELSE
                    DISD
                    / (CAST(DATEDIFF(SECOND, LAG(hora_prisma, 1, hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0)
            END * {unidad} AS VISD,
            CASE
                WHEN dias = 0 THEN 0
                ELSE DASD / dias
            END * {unidad} AS VASD
        FROM PrismasCTE ORDER BY hora_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idinstrumento, fechainicial, fechafinal))
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error en mdlPrismaVelocidadesAnalisisFechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    ###########################################################################
    @staticmethod
    def mdlPrismasDesplazamiento3DA(tabla, unidad, idcomponente):
        conn = None
        sql = f"""SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma,
            (SQRT(
                POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                POWER(p.elevacion_target - FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
            )) * ? AS valor, i.tipo_equipo
        FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        INNER JOIN componentes co ON i.id_componente = co.id_componente
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND i.id_componente = ?
        AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (unidad, idcomponente))
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error en mdlPrismasDesplazamiento3DA: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
                
    @staticmethod
    def mdlPrismasDesplazamiento3DI(tabla, unidad, idcomponente):
        conn = None
        sql = f"""SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma,
            CAST(CASE 
                WHEN LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                ELSE (SQRT(
                    POWER(p.este_target - LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.norte_target - LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.elevacion_target - LAG(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                )) * ?
            END AS FLOAT) AS valor, i.tipo_equipo
        FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        INNER JOIN componentes co ON i.id_componente = co.id_componente
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND i.id_componente = ?
        AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (unidad, idcomponente))
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error en mdlPrismasDesplazamiento3DI: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlPrismasDesplazamiento2DA(tabla, unidad, idcomponente):
        conn = None
        sql = f"""SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma,
            (SQRT(
                POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
            )) * ? AS valor, i.tipo_equipo
        FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        INNER JOIN componentes co ON i.id_componente = co.id_componente
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND i.id_componente = ?
        AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (unidad, idcomponente))
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error en mdlPrismasDesplazamiento2DA: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlPrismasDesplazamiento2DI(tabla, unidad, idcomponente):
        conn = None
        sql = f"""SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma,
            CAST(CASE 
                WHEN LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                ELSE (SQRT(
                    POWER(p.este_target - LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.norte_target - LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                )) * ?
            END AS FLOAT) AS valor, i.tipo_equipo
        FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        INNER JOIN componentes co ON i.id_componente = co.id_componente
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND i.id_componente = ?
        AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (unidad, idcomponente))
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error en mdlCalcularDesplazamiento2DI: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlPrismasDesplazamientoSDA(tabla, unidad, idcomponente):
        conn = None
        sql = f"""SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma,
            (p.distancia_prisma - FIRST_VALUE(CAST(p.distancia_prisma AS FLOAT)) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * ? AS valor,
            i.tipo_equipo
        FROM {tabla} p 
        INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        INNER JOIN componentes co ON i.id_componente = co.id_componente
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND i.id_componente = ?
        AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (unidad, idcomponente))
            rows = [tuple(row) for row in cur.fetchall()]
            if rows:
                return rows
            else:
                return None
        except Error as e:
            print("Error en mdlPrismasDesplazamientoSDA: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlPrismasDesplazamientoSDI(tabla, unidad, idcomponente):
        conn = None
        sql = f"""SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma,
            CAST(CASE 
                WHEN LAG(p.distancia_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                ELSE (p.distancia_prisma - LAG(p.distancia_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * ?
            END AS FLOAT) AS valor, i.tipo_equipo
        FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        INNER JOIN componentes co ON i.id_componente = co.id_componente
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND i.id_componente = ?
        AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (unidad, idcomponente))
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error en mdlPrismasDesplazamientoSDI: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlPrismasDesplazamientoDEA(tabla, unidad, idcomponente):
        conn = None
        sql = f"""SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma,
            (p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * ? AS valor,
            i.tipo_equipo
        FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        INNER JOIN componentes co ON i.id_componente = co.id_componente
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND i.id_componente = ?
        AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (unidad, idcomponente))
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error en mdlPrismasDesplazamientoDEA: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlPrismasDesplazamientoDEI(tabla, unidad, idcomponente):
        conn = None
        sql = f"""SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma,
            CAST(CASE 
                WHEN LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                ELSE (p.este_target - LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * ?
            END AS FLOAT) AS valor, i.tipo_equipo
        FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        INNER JOIN componentes co ON i.id_componente = co.id_componente
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND i.id_componente = ?
        AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (unidad, idcomponente))
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error en mdlPrismasDesplazamientoDEI: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlPrismasDesplazamientoDNA(tabla, unidad, idcomponente):
        conn = None
        sql = f"""SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma,
            (p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * ? AS valor,
            i.tipo_equipo
        FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        INNER JOIN componentes co ON i.id_componente = co.id_componente
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND i.id_componente = ?
        AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (unidad, idcomponente))
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error en mdlPrismasDesplazamientoDNA: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlPrismasDesplazamientoDNI(tabla, unidad, idcomponente):
        conn = None
        sql = f"""SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma,
            CAST(CASE 
                WHEN LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                ELSE (p.norte_target - LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * ?
            END AS FLOAT) AS valor, i.tipo_equipo
        FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        INNER JOIN componentes co ON i.id_componente = co.id_componente
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND i.id_componente = ?
        AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (unidad, idcomponente))
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error en mdlPrismasDesplazamientoDNI: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlPrismasDesplazamientoDZA(tabla, unidad, idcomponente):
        conn = None
        sql = f"""SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma,
            (p.elevacion_target - FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * ? AS valor,
            i.tipo_equipo
        FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        INNER JOIN componentes co ON i.id_componente = co.id_componente
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND i.id_componente = ?
        AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (unidad, idcomponente))
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error en mdlPrismasDesplazamientoDZA: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlPrismasDesplazamientoDZI(tabla, unidad, idcomponente):
        conn = None
        sql = f"""SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma,
            CAST(CASE 
                WHEN LAG(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                ELSE (p.elevacion_target - LAG(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * ?
            END AS FLOAT) AS valor, i.tipo_equipo
        FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        INNER JOIN componentes co ON i.id_componente = co.id_componente
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND i.id_componente = ?
        AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (unidad, idcomponente))
            row = [tuple(r) for r in cur.fetchall()]
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error en mdlPrismasDesplazamientoDZI: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlPrismasVelocidadVA3D(tabla, unidad, idcomponente):
        sql = f"""WITH PrismasCTE AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma,
                SQRT(
                    POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.elevacion_target - FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                ) * ? AS tresD, i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN componentes co ON i.id_componente = co.id_componente
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND i.id_componente = ?
            AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma,
            CASE 
                WHEN DATEDIFF(SECOND, FIRST_VALUE(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) = 0 THEN 0
                ELSE (tresD - FIRST_VALUE(tresD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma))
                    / (CAST(DATEDIFF(SECOND, FIRST_VALUE(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0)
            END AS valor, tipo_equipo
        FROM PrismasCTE
        ORDER BY nombre_prisma, hora_prisma;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (unidad, idcomponente))
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error en mdlPrismasVelocidadVA3D: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
             
    @staticmethod
    def mdlPrismasVelocidadVI3D(tabla, unidad, idcomponente):
        sql = f"""WITH PrismasCTE AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma,
                CASE
                    WHEN ROW_NUMBER() OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) = 1 THEN 0
                    ELSE 
                        SQRT(
                            POWER(p.este_target - LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                            POWER(p.norte_target - LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                            POWER(p.elevacion_target - LAG(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                        ) * ?
                END AS tresD, i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN componentes co ON i.id_componente = co.id_componente
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND i.id_componente = ?
            AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma,
            CASE
                WHEN ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) = 1 THEN 0
                ELSE (tresD - LAG(tresD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma))
                / (CAST(DATEDIFF(SECOND, LAG(hora_prisma, 1, hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0)
            END AS valor, tipo_equipo
        FROM PrismasCTE
        ORDER BY nombre_prisma, hora_prisma;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (unidad, idcomponente))
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error en mdlPrismasVelocidadVI3D: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
                
    @staticmethod
    def mdlPrismasVelocidadVA2D(tabla, unidad, idcomponente):
        sql = f"""WITH PrismasCTE AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma,
                SQRT(
                    POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                ) * ? AS dosD, i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN componentes co ON i.id_componente = co.id_componente
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND i.id_componente = ?
            AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma,
            CASE 
                WHEN DATEDIFF(SECOND, FIRST_VALUE(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) = 0 THEN 0
                ELSE (dosD - FIRST_VALUE(dosD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma))
                    / (CAST(DATEDIFF(SECOND, FIRST_VALUE(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0)
            END AS valor, tipo_equipo
        FROM PrismasCTE
        ORDER BY nombre_prisma, hora_prisma;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (unidad, idcomponente))
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error en mdlPrismasVelocidadVA2D: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
                
    @staticmethod
    def mdlPrismasVelocidadVI2D(tabla, unidad, prismas, idcomponente):
        sql = f"""WITH PrismasCTE AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma,
                CASE
                    WHEN ROW_NUMBER() OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) = 1 THEN 0
                    ELSE 
                        SQRT(
                            POWER(p.este_target - LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                            POWER(p.norte_target - LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                        ) * ?
                END AS dosD, i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN componentes co ON i.id_componente = co.id_componente
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND i.id_componente = ?
            AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma,
            CASE
                WHEN ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) = 1 THEN 0
                ELSE (dosD - LAG(dosD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma))
                / (CAST(DATEDIFF(SECOND, LAG(hora_prisma, 1, hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0)
            END AS valor, tipo_equipo
        FROM PrismasCTE
        ORDER BY nombre_prisma, hora_prisma;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (unidad, idcomponente))
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error en mdlPrismasVelocidadVI2D: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
                
    @staticmethod
    def mdlPrismasVelocidadVASD(tabla, unidad, idcomponente):
        sql = f"""WITH CD AS (
            SELECT id_instrumentacion, p.nombre_prisma, p.hora_prisma,
                CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0 AS dif_fechas,
                (p.distancia_prisma - FIRST_VALUE(CAST(p.distancia_prisma AS FLOAT)) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * ? AS SD,
                i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN componentes co ON i.id_componente = co.id_componente
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND i.id_componente = ?
            AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
        ),
        CD_Dif AS (
            SELECT id_instrumentacion, nombre_prisma, hora_prisma,
                CASE
                    WHEN dif_fechas = 0 THEN 0
                    ELSE (SD - FIRST_VALUE(SD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma)) / dif_fechas
                END AS valor, tipo_equipo
            FROM CD
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma, valor, tipo_equipo
        FROM CD_Dif
        ORDER BY nombre_prisma, hora_prisma;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (unidad, idcomponente))
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error en mdlPrismasVelocidadVASD: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
                
    @staticmethod
    def mdlPrismasVelocidadVISD(tabla, unidad, idcomponente):
        sql = f"""WITH velocidad AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma,
                CAST(DATEDIFF(SECOND, COALESCE(LAG(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0 AS dif_fechas,
                (p.distancia_prisma - FIRST_VALUE(CAST(p.distancia_prisma AS FLOAT)) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) * ? AS SD,
                i.tipo_equipo
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN componentes co ON i.id_componente = co.id_componente
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND i.id_componente = ?
            AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
        ),
        CD_Dif AS (
            SELECT id_instrumentacion, nombre_prisma, hora_prisma,
                CASE
                    WHEN dif_fechas = 0 THEN 0
                    ELSE (SD - COALESCE(LAG(SD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), SD)) / dif_fechas
                END AS valor, tipo_equipo
            FROM velocidad
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma, valor, tipo_equipo
        FROM CD_Dif
        ORDER BY nombre_prisma, hora_prisma;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (unidad, idcomponente))
            rows = cur.fetchall()
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error en mdlPrismasVelocidadVISD: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
                
    @staticmethod
    def mdlPiezometrosCuerdaNivelFreatico(tabla, unidad, idcomponente):
        conn = None
        sql = f"""SELECT t.id_instrumentacion, pzc.nombre_piezometro, pzcd.fecha_cuerda,
            CASE
                WHEN pzc.tipo_piezometro = 1 THEN pzc.elevacion_piezometro + pzcd.medida_calculada
                ELSE pzcd.medida_calculada
            END AS valor, t.tipo_equipo
        FROM piezometrocuerdas pzc INNER JOIN {tabla} pzcd ON pzc.id_piezometro = pzcd.id_piezometro 
        INNER JOIN instrumentacion t ON pzc.id_piezometro = t.id_equipo
        WHERE pzcd.estado_cuerda = 1 AND c.id_componente = ?
        ORDER BY pzc.nombre_piezometro ASC, pzcd.fecha_cuerda ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idcomponente,))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error en mdlPiezometrosCuerdaNivelFreatico: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlPiezometrosCuerdaNivelAcumulado(tabla, unidad, idcomponente):
        conn = None
        sql = f"""SELECT t.id_instrumentacion, pzc.nombre_piezometro, pzcd.fecha_cuerda,
            CASE 
                WHEN pzc.tipo_piezometro = 1 THEN pzcd.medida_calculada
                ELSE pzcd.medida_calculada - pzc.elevacion_piezometro
            END * ? AS valor, t.tipo_equipo
        FROM piezometrocuerdas pzc INNER JOIN {tabla} pzcd ON pzc.id_piezometro = pzcd.id_piezometro 
        INNER JOIN instrumentacion t ON pzc.id_piezometro = t.id_equipo
        WHERE pzcd.estado_cuerda = 1 AND c.id_componente = ?
        ORDER BY pzc.nombre_piezometro ASC, pzcd.fecha_cuerda ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (unidad, idcomponente))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error en mdlPiezometrosCuerdaNivelAcumulado: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlPiezometrosCuerdaNivelIncremental(tabla, unidad, idcomponente):
        conn = None
        sql = f"""SELECT t.id_instrumentacion, pzc.nombre_piezometro, pzcd.fecha_cuerda,
            COALESCE(pzcd.medida_calculada - LAG(pzcd.medida_calculada) OVER (PARTITION BY pzc.nombre_piezometro ORDER BY pzcd.fecha_cuerda), 0) * ? AS valor,
            t.tipo_equipo
        FROM piezometrocuerdas pzc INNER JOIN {tabla} pzcd ON pzc.id_piezometro = pzcd.id_piezometro 
        INNER JOIN instrumentacion t ON pzc.id_piezometro = t.id_equipo
        WHERE pzcd.estado_cuerda = 1 AND c.id_componente = ?
        ORDER BY pzc.nombre_piezometro ASC, pzcd.fecha_cuerda ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (unidad, idcomponente))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error en mdlPiezometrosCuerdaNivelIncremental: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlPiezometrosCasagrandeNivelFreatico(tabla, unidad, idcomponente):
        conn = None
        sql = f"""WITH cte_cota AS (
            SELECT it.id_instrumentacion, p.nombre_piezometro, d.fecha_piezometro, p.tipo_piezometro,
            d.medida_piezometro, p.stickup_piezometro,
            COALESCE(
                (SELECT TOP 1 c2.nivel_cota FROM cotas_piezometricas c2 WHERE c2.id_piezometro = d.id_piezometro 
                AND c2.tipo_piezometro = 'PVC' AND c2.fecha_cota <= d.fecha_piezometro ORDER BY c2.fecha_cota DESC),
                (SELECT TOP 1 c3.nivel_cota FROM cotas_piezometricas c3 WHERE c3.id_piezometro = d.id_piezometro
                AND c3.tipo_piezometro = 'PVC' ORDER BY c3.fecha_cota ASC)
            ) AS elevacion, it.tipo_equipo
            FROM piezometromanuales p INNER JOIN {tabla} d ON p.id_piezometro = d.id_piezometro
            INNER JOIN instrumentacion AS it ON it.id_equipo = p.id_piezometro
            WHERE d.estado_manual = 1 AND it.id_componente = ?
        )
        SELECT id_instrumentacion, nombre_piezometro, fecha_piezometro,
            CASE
                WHEN tipo_piezometro = 1 THEN stickup_piezometro + elevacion - medida_piezometro
                ELSE medida_piezometro
            END AS valor, tipo_equipo
        FROM cte_cota ORDER BY nombre_piezometro ASC, fecha_piezometro ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idcomponente,))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error en mdlPiezometrosCasagrandeNivelFreatico: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlPiezometrosCasagrandeNivelAcumulado(tabla, unidad, idcomponente):
        conn = None
        sql = f"""WITH cte_cota AS (
            SELECT it.id_instrumentacion, p.nombre_piezometro, d.fecha_piezometro, p.tipo_piezometro,
            d.medida_piezometro, p.stickup_piezometro,
            COALESCE(
                (SELECT TOP 1 c2.nivel_cota FROM cotas_piezometricas c2 WHERE c2.id_piezometro = d.id_piezometro 
                AND c2.tipo_piezometro = 'PVC' AND c2.fecha_cota <= d.fecha_piezometro ORDER BY c2.fecha_cota DESC),
                (SELECT TOP 1 c3.nivel_cota FROM cotas_piezometricas c3 WHERE c3.id_piezometro = d.id_piezometro
                AND c3.tipo_piezometro = 'PVC' ORDER BY c3.fecha_cota ASC)
            ) AS elevacion, it.tipo_equipo
            FROM piezometromanuales p INNER JOIN {tabla} d ON p.id_piezometro = d.id_piezometro
            INNER JOIN instrumentacion AS it ON it.id_equipo = p.id_piezometro
            WHERE d.estado_manual = 1 AND it.id_componente = ?
        )
        SELECT id_instrumentacion, nombre_piezometro, fecha_piezometro,
            CASE 
                WHEN tipo_piezometro = 1 THEN 
                    (stickup_piezometro + elevacion - medida_piezometro) -
                    (stickup_piezometro + FIRST_VALUE(elevacion) OVER (PARTITION BY nombre_piezometro ORDER BY fecha_piezometro) - 
                    FIRST_VALUE(medida_piezometro) OVER (PARTITION BY nombre_piezometro ORDER BY fecha_piezometro))
                ELSE 
                    medida_piezometro - FIRST_VALUE(medida_piezometro) OVER (PARTITION BY nombre_piezometro ORDER BY fecha_piezometro)
            END * ? AS valor, tipo_equipo
        FROM cte_cota ORDER BY nombre_piezometro ASC, fecha_piezometro ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idcomponente, unidad))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error en mdlPiezometrosCasagrandeNivelAcumulado: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlPiezometrosCasagrandeNivelIncremental(tabla, unidad, idcomponente):
        conn = None
        sql = f"""SELECT it.id_instrumentacion, p.nombre_piezometro, d.fecha_piezometro,
            COALESCE(d.medida_piezometro - LAG(d.medida_piezometro) OVER (PARTITION BY p.nombre_piezometro ORDER BY d.fecha_piezometro), 0) * ? AS valor,
            it.tipo_equipo
        FROM piezometromanuales p INNER JOIN {tabla} d ON p.id_piezometro = d.id_piezometro
        INNER JOIN instrumentacion AS it ON it.id_equipo = p.id_piezometro
        WHERE d.estado_manual = 1 AND it.id_componente = ?
        ORDER BY p.nombre_piezometro ASC, d.fecha_piezometro ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (unidad, idcomponente))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error en mdlPiezometrosCasagrandeNivelIncremental: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCeldasAsentamientoCota(tabla, unidad, idcomponente):
        conn = None
        sql = f"""SELECT t.id_instrumentacion, c.nombre_celda, cd.fecha_detalle,
            c.instalacion_celda - abs(cd.medida_calculada) AS valor, t.tipo_equipo
        FROM celdas c INNER JOIN {tabla} cd ON c.id_celda = cd.id_celda
        INNER JOIN instrumentacion t ON c.id_celda = t.id_equipo
        WHERE t.id_componente = ? AND cd.estado_detalle = 1
        ORDER BY c.nombre_celda ASC, cd.fecha_detalle ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (unidad, idcomponente))
            rows = cur.fetchall()
            return [tuple(row) for row in rows] if rows else None
        except Exception as e:
            print("Error en mdlCeldasAsentamientoCota: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCeldasAsentamientoIncremental(tabla, unidad, idcomponente):
        conn = None
        sql = f"""SELECT t.id_instrumentacion, c.nombre_celda, cd.fecha_detalle,
            COALESCE(cd.medida_calculada - LAG(cd.medida_calculada) OVER (PARTITION BY c.nombre_celda ORDER BY cd.fecha_detalle ASC), 0) * CAST(? AS FLOAT) AS valor,
            t.tipo_equipo
        FROM celdas c INNER JOIN {tabla} cd ON c.id_celda = cd.id_celda
        INNER JOIN instrumentacion t ON c.id_celda = t.id_equipo
        WHERE t.id_componente = ? AND cd.estado_detalle = 1
        ORDER BY c.nombre_celda ASC, cd.fecha_detalle ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (unidad, idcomponente))
            rows = cur.fetchall()
            return [tuple(row) for row in rows] if rows else None
        except Exception as e:
            print("Error en mdlCeldasAsentamientoIncremental: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerAsentamientoAcumulado(tabla, unidad, idcomponente):
        conn = None
        sql = f"""SELECT t.id_instrumentacion, c.nombre_celda, cd.fecha_detalle,
            cd.medida_calculada * CAST(? AS FLOAT) AS valor, t.tipo_equipo
        FROM celdas c INNER JOIN {tabla} cd ON c.id_celda = cd.id_celda
        INNER JOIN instrumentacion t ON c.id_celda = t.id_equipo
        WHERE t.id_componente = ? AND cd.estado_detalle = 1
        ORDER BY c.nombre_celda ASC, cd.fecha_detalle ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (unidad, idcomponente))
            rows = cur.fetchall()
            return [tuple(row) for row in rows] if rows else None
        except Exception as e:
            print("Error en mdlObtenerAsentamientoAcumulado: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    