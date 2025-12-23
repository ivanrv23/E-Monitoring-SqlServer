from services.security.apis.conexiones.connection import Connection
import datetime
import numpy as np

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
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
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
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
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
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
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
        WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
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
            
            # CORRECCIÓN: Se eliminó 'p.nombre_prisma' del ORDER BY dentro de los OVER()
            # para evitar el error de límite de 900 bytes.
            sql = f"""
            WITH inversoVelocidad AS (
                SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma,
                    -- Cálculo de Horas: (Diferencia en segundos / 3600)
                    (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 3600.0) AS horas,
                    
                    -- Cálculo de Días: (Diferencia en segundos / 86400)
                    (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
                    
                    -- Cálculo 3D
                    SQRT(
                        POWER(CAST(p.este_target AS FLOAT) - FIRST_VALUE(CAST(p.este_target AS FLOAT)) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                        POWER(CAST(p.norte_target AS FLOAT) - FIRST_VALUE(CAST(p.norte_target AS FLOAT)) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                        POWER(CAST(p.elevacion_target AS FLOAT) - FIRST_VALUE(CAST(p.elevacion_target AS FLOAT)) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                    ) * CAST(? AS FLOAT) AS tresD
                FROM {tabla} p 
                INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
                WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
                  AND p.nombre_prisma IN ({placeholders}) 
                  AND i.id_componente = ?
            )
            SELECT id_instrumentacion, nombre_prisma, hora_prisma, dias, horas,
                CASE WHEN tresD = 0 THEN 0 ELSE (horas/tresD) END AS iv_horas,
                CASE WHEN tresD = 0 THEN 0 ELSE (dias/tresD) END AS iv_dias
            FROM inversoVelocidad
            ORDER BY nombre_prisma, hora_prisma;
            """
            
            cur = conn.cursor()
            cur.execute(sql, params)
            
            # Convertimos Row de Pyodbc a Tuplas para el frontend
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
            
            # CORRECCIÓN: Se eliminó 'p.nombre_prisma' del ORDER BY dentro de los OVER()
            sql = f"""
            WITH inversoVelocidad AS (
                SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma,
                    -- Cálculo de Horas
                    (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 3600.0) AS horas,
                    
                    -- Cálculo de Días
                    (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
                    
                    -- Cálculo 3D
                    SQRT(
                        POWER(CAST(p.este_target AS FLOAT) - FIRST_VALUE(CAST(p.este_target AS FLOAT)) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                        POWER(CAST(p.norte_target AS FLOAT) - FIRST_VALUE(CAST(p.norte_target AS FLOAT)) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                        POWER(CAST(p.elevacion_target AS FLOAT) - FIRST_VALUE(CAST(p.elevacion_target AS FLOAT)) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                    ) * CAST(? AS FLOAT) AS tresD
                FROM {tabla} p 
                INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
                WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
                  AND p.nombre_prisma IN ({placeholders}) 
                  AND i.id_componente = ?
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
            
            # Convertimos Row de Pyodbc a Tuplas para el frontend
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
                hora_prisma VARCHAR(50) NOT NULL,
                nombre_prisma VARCHAR(50) NOT NULL,
                este_target FLOAT NOT NULL,
                norte_target FLOAT NOT NULL,
                elevacion_target FLOAT NOT NULL,
                distancia_prisma FLOAT NOT NULL,
                fecha_backup VARCHAR(50) NOT NULL
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
                    ultima_fecha_modificada VARCHAR(255)
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