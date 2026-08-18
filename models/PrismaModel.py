from services.security.apis.conexiones.connection import Connection
from datetime import datetime

class PrismaModel:
    
    # Nota Arquitecto: Para limpiar tablas en SQL Server usar:
    # DELETE FROM tabla; 
    # DBCC CHECKIDENT ('tabla', RESEED, 0);

    def asegurar_tabla_prismas(conn, cursor, nombretabla):
        """Crea la tabla de prismas (si no existe), incluyendo el índice único
        de deduplicación (nombre_prisma, hora_prisma, grupo_puntos)."""
        cursor.execute(f"""
            IF OBJECT_ID('{nombretabla}', 'U') IS NULL
            CREATE TABLE {nombretabla} (
                id_prisma INT IDENTITY(1,1) NOT NULL PRIMARY KEY, state_prisma INT NOT NULL DEFAULT 1, estado_prisma INT NOT NULL DEFAULT 1,
                nombre_prisma VARCHAR(255) NOT NULL, perfil_prisma VARCHAR(255), hora_prisma DATETIME2(0) NOT NULL,
                angulo_horizontal VARCHAR(50), angulo_vertical VARCHAR(50), distancia_prisma FLOAT DEFAULT 0,
                tipoppm_prisma VARCHAR(50), ppm_prisma FLOAT DEFAULT 0, presion_prisma FLOAT DEFAULT 0,
                temperatura_prisma FLOAT DEFAULT 0, constante_prisma FLOAT DEFAULT 0, este_target FLOAT NOT NULL,
                norte_target FLOAT NOT NULL, elevacion_target FLOAT NOT NULL, altura_reflector FLOAT DEFAULT 0,
                altura_instrumento FLOAT DEFAULT 0, este_estacion FLOAT DEFAULT 0, norte_estacion FLOAT DEFAULT 0,
                altura_estacion FLOAT DEFAULT 0, medicion_prisma FLOAT DEFAULT 0, diferencia_tiempocorto FLOAT DEFAULT 0,
                diferencia_tiempolargo FLOAT DEFAULT 0, diferencia_limitevelocidad FLOAT DEFAULT 0,
                distancia_horizontal FLOAT DEFAULT 0, diferencia_atipica FLOAT DEFAULT 0, desplaza_longitudinal FLOAT DEFAULT 0,
                desplaza_transversal FLOAT DEFAULT 0, desplaza_altura FLOAT DEFAULT 0, grupo_puntos VARCHAR(255)
            );
        """)
        idx_name = f"UX_{nombretabla}_dedupe"
        cursor.execute(f"""
            IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = '{idx_name}' AND object_id = OBJECT_ID('{nombretabla}'))
            CREATE UNIQUE INDEX {idx_name} ON {nombretabla} (nombre_prisma, hora_prisma, grupo_puntos);
        """)
        conn.commit()
    
    @staticmethod
    def mdlObtenerFechasMaximasPrismas(tabla):
        sql = f"""SELECT TOP 1 MAX(hora_prisma) AS max_fecha FROM {tabla} WHERE state_prisma = 1;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchone()
            if row:
                return tuple(row)
            else:
                return None
        except Exception as e:
            print("Error al obtener fechas max prismas: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlListarDataPrismasNombre(table, nombres):
        placeholders = ', '.join(['?' for _ in nombres])
        sql = f"""SELECT nombre_prisma, estado_prisma, perfil_prisma, hora_prisma, angulo_horizontal, angulo_vertical, distancia_prisma, tipoppm_prisma, ppm_prisma, 
            presion_prisma, temperatura_prisma, constante_prisma, este_target, norte_target, elevacion_target, altura_reflector, altura_instrumento, este_estacion, 
            norte_estacion, altura_estacion, medicion_prisma, diferencia_tiempocorto, diferencia_tiempolargo, diferencia_limitevelocidad, distancia_horizontal, 
            diferencia_atipica, desplaza_longitudinal, desplaza_transversal, desplaza_altura, grupo_puntos FROM {table} WHERE state_prisma = 1 
            AND nombre_prisma IN ({placeholders}) ORDER BY nombre_prisma, hora_prisma;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, nombres)
            rows = cur.fetchall()
            return [tuple(row) for row in rows]
        except Exception as e:
            print("Error al listar prismas: " + str(e))
            return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlListarDataPrismasNombre_manuales(table, nombres):
        placeholders = ', '.join(['?' for _ in nombres])
        sql = f"""SELECT nombre_prisma, hora_prisma, norte_target, este_target, elevacion_target, angulo_horizontal, angulo_vertical, distancia_prisma
        FROM {table} WHERE state_prisma = 1 AND nombre_prisma IN ({placeholders}) ORDER BY nombre_prisma, hora_prisma;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, nombres)
            rows = cur.fetchall()
            return [tuple(row) for row in rows]
        except Exception as e:
            print("Error al listar prismas: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlResumenPrismaNombre(tabla, nombres, fechaini, fechafin, tipo_prisma):
        nombres_str = ','.join(['?' for _ in nombres])
        # T-SQL: DATEDIFF en SEGUNDOS / 86400.0 para obtener la diferencia en días con decimales
        sql = f"""SELECT nombre_prisma, '{tipo_prisma}' AS tipo, MIN(hora) AS fecha_minima, MAX(hora) AS fecha_maxima, COUNT(*) AS cantidad,
            CAST((CAST(DATEDIFF(SECOND, MIN(hora), MAX(hora)) AS FLOAT) / 86400.0) + 1 AS INT) as total_dias
        FROM (
            SELECT nombre_prisma, '{tipo_prisma}' AS tipo, hora_prisma AS hora FROM {tabla} WHERE state_prisma = 1
            AND nombre_prisma IN ({nombres_str}) AND hora_prisma BETWEEN ? AND ?
        ) AS subquery GROUP BY nombre_prisma;"""

        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            params = tuple(nombres) + (fechaini, fechafin)
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [tuple(row) for row in rows]
        except Exception as e:
            print("Error al consultar Resumen prisma: " + str(e))
            return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlObtenerFechaMinMaxAuto(proyectoid):
        tabla = "prismas" + str(proyectoid)
        sql = """SELECT MIN(hora_prisma) AS min_fecha, MAX(hora_prisma) AS max_fecha FROM """ + tabla + """ WHERE state_prisma = 1;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchone()
            if row:
                return tuple(row)
            else:
                return None
        except Exception as e:
            print("Error al obtener fechas min-max: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlObtenerFechaMinMaxManual(proyectoid):
        tabla = "prismas" + str(proyectoid)
        sql = """SELECT MIN(hora_prisma) AS min_fecha, MAX(hora_prisma) AS max_fecha FROM """ + tabla + """ WHERE state_prisma = 1;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchone()
            if row:
                return tuple(row)
            else:
                return None
        except Exception as e:
            print("Error al obtener fechas min-max: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlListarPrismasUnicosMinima(tabla, prismas, idcomponente):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente]
        
        sql = f"""
        SELECT id_instrumentacion, nombre_equipo, este_target, norte_target, elevacion_target, id_componente, tipo_equipo, hora
        FROM (
            SELECT i.id_instrumentacion, i.nombre_equipo, p.este_target, p.norte_target, p.elevacion_target, i.id_componente,
            i.tipo_equipo, p.hora_prisma AS hora,
            ROW_NUMBER() OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma ASC) as rn
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN componentes co ON i.id_componente = co.id_componente
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
        ) t
        WHERE rn = 1
        ORDER BY nombre_equipo, hora;"""

        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [tuple(row) for row in rows]
        except Exception as e:
            print("Error al listar prismas ini: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlListarPrismasUnicosFechaMinima(tabla, prismas, idcomponente, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        
        sql = f"""
        SELECT id_instrumentacion, nombre_equipo, este_target, norte_target, elevacion_target, id_componente, tipo_equipo, hora
        FROM (
            SELECT i.id_instrumentacion, i.nombre_equipo, p.este_target, p.norte_target, p.elevacion_target, i.id_componente,
            i.tipo_equipo, p.hora_prisma AS hora,
            ROW_NUMBER() OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma ASC) as rn
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN componentes co ON i.id_componente = co.id_componente
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
            AND p.hora_prisma BETWEEN ? AND ?
        ) t
        WHERE rn = 1
        ORDER BY nombre_equipo, hora;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [tuple(row) for row in rows]
        except Exception as e:
            print("Error al listar prismas ini fechas: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlTraerPrismasInicialesProyectoFecha(proyecto, fechaini, fechafin):
        tabla = "prismas" + str(proyecto)
        sql = f"""
        SELECT t.*, t.id_prisma 
        FROM (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma ASC) as rn
            FROM {tabla}
            WHERE state_prisma = 1 AND hora_prisma BETWEEN ? AND ?
        ) t
        WHERE t.rn = 1;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (fechaini, fechafin))
            rows = cur.fetchall()
            return [tuple(row) for row in rows]
        except Exception as e:
            print("Error al listar prismas: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlPrismasManualesInicialesProyectoFecha(proyecto, fechaini, fechafin):
        tabla = "prismas" + str(proyecto)
        sql = f"""
        SELECT t.*, t.id_prisma 
        FROM (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma ASC) as rn
            FROM {tabla}
            WHERE state_prisma = 1 AND hora_prisma BETWEEN ? AND ?
        ) t
        WHERE t.rn = 1;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (fechaini, fechafin))
            rows = cur.fetchall()
            return [tuple(row) for row in rows]
        except Exception as e:
            print("Error al listar prismas: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlTraerPrismaInicialProyectoNombreFecha(proyecto, nombre, fechaini, fechafin):
        tabla = "prismas" + str(proyecto)
        sql = f"""
        SELECT TOP 1 *, id_prisma 
        FROM {tabla} 
        WHERE state_prisma = 1 AND nombre_prisma = ? AND hora_prisma BETWEEN ? AND ? 
        ORDER BY hora_prisma ASC;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (nombre, fechaini, fechafin))
            row = cur.fetchone()
            if row:
                return tuple(row)
            else:
                return None
        except Exception as e:
            print("Error al listar prismas por fecha: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlTraerPrismasFinalesProyectoFecha(proyecto, fechaini, fechafin):
        tabla = "prismas" + str(proyecto)
        sql = f"""
        SELECT t.*, t.id_prisma 
        FROM (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma DESC) as rn
            FROM {tabla}
            WHERE state_prisma = 1 AND hora_prisma BETWEEN ? AND ?
        ) t
        WHERE t.rn = 1;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (fechaini, fechafin))
            rows = cur.fetchall()
            return [tuple(row) for row in rows]
        except Exception as e:
            print("Error al listar prismas: " + str(e))
            return None
        finally:
            if conn: conn.close() 
    
    @staticmethod
    def mdlPrismasManualesFinalesProyectoFecha(proyecto, fechaini, fechafin):
        tabla = "prismas" + str(proyecto)
        sql = f"""
        SELECT t.*, t.id_prisma 
        FROM (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma DESC) as rn
            FROM {tabla}
            WHERE state_prisma = 1 AND hora_prisma BETWEEN ? AND ?
        ) t
        WHERE t.rn = 1;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (fechaini, fechafin))
            rows = cur.fetchall()
            return [tuple(row) for row in rows]
        except Exception as e:
            print("Error al listar prismas: " + str(e))
            return None
        finally:
            if conn: conn.close()  
    
    @staticmethod
    def mdlListarPrismasUnicosMaxima(tabla, prismas, idcomponente):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente]
        sql = f"""
        SELECT id_instrumentacion, nombre_equipo, este_target, norte_target, elevacion_target, id_componente, tipo_equipo, hora
        FROM (
            SELECT i.id_instrumentacion, i.nombre_equipo, p.este_target, p.norte_target, p.elevacion_target, i.id_componente,
            i.tipo_equipo, p.hora_prisma AS hora,
            ROW_NUMBER() OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma DESC) as rn
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN componentes co ON i.id_componente = co.id_componente
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
        ) t
        WHERE rn = 1
        ORDER BY nombre_equipo, hora;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [tuple(row) for row in rows]
        except Exception as e:
            print("Error al listar prismas max: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlListarPrismasUnicosFechaMaxima(tabla, prismas, idcomponente, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        sql = f"""
        SELECT id_instrumentacion, nombre_equipo, este_target, norte_target, elevacion_target, id_componente, tipo_equipo, hora
        FROM (
            SELECT i.id_instrumentacion, i.nombre_equipo, p.este_target, p.norte_target, p.elevacion_target, i.id_componente,
            i.tipo_equipo, p.hora_prisma AS hora,
            ROW_NUMBER() OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma DESC) as rn
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN componentes co ON i.id_componente = co.id_componente
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1
            AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ?
            AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
        ) t
        WHERE rn = 1
        ORDER BY nombre_equipo, hora;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [tuple(row) for row in rows]
        except Exception as e:
            print("Error al listar prismas max fechas: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlListarPrismasFechaMinimaUnicos(tabla, proyecto, fechaini, fechafin, tipo):
        sql = f"""
        SELECT id_instrumentacion, nombre_equipo, este_target, norte_target, elevacion_target, id_componente, tipo_equipo, hora
        FROM (
            SELECT i.id_instrumentacion, i.nombre_equipo, p.este_target, p.norte_target, p.elevacion_target, c.id_componente,
            i.tipo_equipo, p.hora_prisma AS hora,
            ROW_NUMBER() OVER (PARTITION BY nombre_prisma, c.id_componente ORDER BY hora_prisma ASC) as rn
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN componentes c ON i.id_componente = c.id_componente 
            WHERE p.state_prisma = 1 AND hora_prisma BETWEEN ? AND ?
            AND c.id_proyecto = ? AND i.tipo_equipo = ?
            AND (p.grupo_puntos = c.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
        ) t WHERE rn = 1;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (fechaini, fechafin, proyecto, tipo))
            rows = cur.fetchall()
            return [tuple(row) for row in rows]
        except Exception as e:
            print("Error al listar prismas minima: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlCambiarEstadoPrisma(tabla, nombreprisma, estado_prisma):
        sql = """UPDATE """ + tabla + """ SET state_prisma = ? WHERE nombre_prisma = ?"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (str(estado_prisma), nombreprisma))
            conn.commit()
            return True
        except Exception as e:
            print("Error al cambiar estado prisma: " + str(e))
            return False
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlEliminarPrisma(tabla, nombreprisma):
        sql = """DELETE FROM """ + tabla + """ WHERE nombre_prisma = ?"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (nombreprisma,))
            conn.commit()
            if cur.rowcount > 0:
                return True
            else:
                return False
        except Exception as e:
            print("Error al eliminar prisma: " + str(e))
            return False
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlListarPrismasManualesProyecto(proyecto):
        tabla = "prismas" + str(proyecto)
        sql = f"""
        SELECT t.*, t.id_prisma 
        FROM (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY id_prisma ASC) as rn
            FROM {tabla}
            WHERE state_prisma = '1'
        ) t
        WHERE t.rn = 1;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql)
            rows = cur.fetchall()
            return [tuple(row) for row in rows]
        except Exception as e:
            print("Error al listar nombre prismas manual: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlGuardarPrismasManualesTabla(proyecto, data):
        conn = None
        try:
            conn = Connection.connectionDB()
            nombretabla = "prismas" + str(proyecto)
            cursor = conn.cursor()
            PrismaModel.asegurar_tabla_prismas(conn, cursor, nombretabla)
            
            # --- VALIDACIÓN DE DUPLICADOS CON 'T' ---
            cursor.execute(f"SELECT nombre_prisma, FORMAT(hora_prisma, 'yyyy-MM-ddTHH:mm:ss') FROM {nombretabla}")
            existen_prismas = set([(row[0], row[1]) for row in cursor.fetchall()])
            
            lote_registros = []
            contador = 0
            
            insert_query = f"""INSERT INTO {nombretabla} (state_prisma, estado_prisma, nombre_prisma, hora_prisma, distancia_prisma, este_target,
                        norte_target, elevacion_target, angulo_horizontal, angulo_vertical) VALUES (1, 1, ?, ?, ?, ?, ?, ?, ?, ?)"""

            for fila in data:
                fecha_original = fila[1]
                hora_original = fila[2]
                distancia_original = float(fila[6]) if fila[6] else 0.0
                este_original = float(fila[3]) if fila[3] else 0.0
                norte_original = float(fila[4]) if fila[4] else 0.0
                nivel_original = float(fila[5]) if fila[5] else 0.0
                horiz_original = fila[7]
                verti_original = fila[8]
                
                # --- CAMBIO IMPORTANTE: CONCATENAR CON 'T' PARA QUE COINCIDA CON LA VALIDACION ---
                # Antes: fecha_original + " " + hora_original (Espacio)
                # Ahora: fecha_original + "T" + hora_original (ISO)
                fecha_hora = f"{fecha_original}T{hora_original}"
                
                # Ahora la comparación es "2023-01-01T12:00" == "2023-01-01T12:00"
                if (fila[0], fecha_hora) not in existen_prismas:
                    row = (
                        fila[0],
                        fecha_hora,
                        distancia_original,
                        este_original,
                        norte_original,
                        nivel_original,
                        horiz_original,
                        verti_original
                    )
                    lote_registros.append(row)
                    contador += 1
                
                if contador % 1000 == 0 and lote_registros:
                    cursor.executemany(insert_query, lote_registros)
                    lote_registros = []
            
            if lote_registros:
                cursor.executemany(insert_query, lote_registros)
            
            conn.commit()
            return True
        except Exception as e:
            print("Error al guardar los prismas de la tabla " + str(e))
            if conn: conn.rollback()
            return False
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlListarDataPrismasProyecto(proyecto, fechaini, fechafin):
        table = "prismas" + str(proyecto)
        sql = f"""SELECT * FROM {table} WHERE state_prisma = 1 AND hora_prisma BETWEEN ? AND ?;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (fechaini, fechafin))
            rows = cur.fetchall()
            return [tuple(row) for row in rows]
        except Exception as e:
            print("Error al listar prismas: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlTraerDataPrismasManualesFecha(proyecto, fechaini, fechafin):
        tabla = "prismas" + str(proyecto)
        sql = f"""WITH prismasmanuales AS (
            SELECT 
                id_prisma, nombre_prisma, state_prisma, hora_prisma, 
                COALESCE(CAST(DATEDIFF(SECOND, LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0, 0) AS dias,
                norte_target, este_target, elevacion_target, angulo_horizontal, angulo_vertical, distancia_prisma,
                COALESCE(LAG(norte_target) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), 0) AS norteanterior,
                COALESCE(LAG(este_target) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), 0) AS esteanterior,
                COALESCE(LAG(elevacion_target) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), 0) AS elevacionanterior,
                COALESCE(LAG(distancia_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), 0) AS distanciaanterior,
                (norte_target - FIRST_VALUE(norte_target) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma)) AS danorte,
                (este_target - FIRST_VALUE(este_target) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma)) AS daeste,
                (elevacion_target - FIRST_VALUE(elevacion_target) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma)) AS danivel,
                (distancia_prisma - FIRST_VALUE(distancia_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma)) AS dadistancia,
                SQRT(
                    POWER(norte_target - FIRST_VALUE(norte_target) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), 2) + 
                    POWER(este_target - FIRST_VALUE(este_target) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), 2)) AS magnitudNE
            FROM {tabla} 
            WHERE state_prisma = 1 AND hora_prisma BETWEEN ? AND ?
        )
        SELECT 
            id_prisma, nombre_prisma, state_prisma, hora_prisma, dias, norte_target, este_target, 
            elevacion_target, angulo_horizontal, angulo_vertical, distancia_prisma,
            CASE WHEN dias <= 0 OR dias > 365 THEN 0 ELSE ((norte_target - norteanterior) / dias) END AS vinorte,
            CASE WHEN dias <= 0 OR dias > 365 THEN 0 ELSE ((este_target - esteanterior) / dias) END AS vieste,
            CASE WHEN dias <= 0 OR dias > 365 THEN 0 ELSE ((elevacion_target - elevacionanterior) / dias) END AS vinivel,
            CASE WHEN dias <= 0 OR dias > 365 THEN 0 ELSE ((distancia_prisma - distanciaanterior) / dias) END AS vidistancia,
            danorte, daeste, danivel, dadistancia, magnitudNE,
            SQRT(POWER(magnitudNE, 2) + POWER(danivel, 2)) AS magnitudZNE,
            CASE 
                WHEN danorte = 0 THEN 0
                WHEN danorte > 0 AND daeste > 0 THEN 90 - (180.0 / PI()) * ATAN(danorte / daeste)
                WHEN danorte < 0 AND daeste > 0 THEN 90 - (180.0 / PI()) * ATAN(danorte / daeste)
                WHEN danorte < 0 AND daeste < 0 THEN 270 - (180.0 / PI()) * ATAN(danorte / daeste)
                WHEN danorte > 0 AND daeste < 0 THEN 270 - (180.0 / PI()) * ATAN(danorte / daeste)
            END AS trend, 
            CASE WHEN magnitudNE = 0 THEN 0 ELSE ((180.0 / PI()) * ATAN(danivel / magnitudNE)) END AS plunge
        FROM prismasmanuales;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (fechaini, fechafin))
            rows = cur.fetchall()
            return [tuple(row) for row in rows]
        except Exception as e:
            print("Error al listar prismas manuales: " + str(e))
            return None
        finally:
            if conn: conn.close()
                
    @staticmethod
    def mdlListarPrismasProyecto(proyecto):
        tabla = "prismas" + str(proyecto)
        sql = f"""
        SELECT t.*, t.id_prisma 
        FROM (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY id_prisma ASC) as rn
            FROM {tabla}
            WHERE state_prisma = 1
        ) t
        WHERE t.rn = 1;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql)
            rows = cur.fetchall()
            return [tuple(row) for row in rows]
        except Exception as e:
            print("Error al listar nombre prismas auto: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlObtenerInfoPrismasAutoJSONproyecto(proyecto):
        tabla = "prismas" + str(proyecto)
        sql = f"""SELECT
            nombre_prisma,
            (SELECT TOP 1 este_target FROM {tabla} AS sub WHERE sub.nombre_prisma = p.nombre_prisma AND sub.state_prisma = 1 
            ORDER BY sub.hora_prisma ASC) AS este_inicial,
            (SELECT TOP 1 norte_target FROM {tabla} AS sub WHERE sub.nombre_prisma = p.nombre_prisma AND sub.state_prisma = 1 
            ORDER BY sub.hora_prisma ASC) AS norte_inicial,
            (SELECT TOP 1 elevacion_target FROM {tabla} AS sub WHERE sub.nombre_prisma = p.nombre_prisma AND sub.state_prisma = 1 
            ORDER BY sub.hora_prisma ASC) AS nivel_inicial,
            (SELECT TOP 1 este_target FROM {tabla} AS sub WHERE sub.nombre_prisma = p.nombre_prisma AND sub.state_prisma = 1 
            ORDER BY sub.hora_prisma DESC) AS este_final,
            (SELECT TOP 1 norte_target FROM {tabla} AS sub WHERE sub.nombre_prisma = p.nombre_prisma AND sub.state_prisma = 1 
            ORDER BY sub.hora_prisma DESC) AS norte_final,
            (SELECT TOP 1 elevacion_target FROM {tabla} AS sub WHERE sub.nombre_prisma = p.nombre_prisma AND sub.state_prisma = 1 
            ORDER BY sub.hora_prisma DESC) AS nivel_final
        FROM
            {tabla} p
        WHERE
            state_prisma = 1
        GROUP BY
            nombre_prisma
        ORDER BY
            MIN(hora_prisma);"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql)
            rows = cur.fetchall()
            return [tuple(row) for row in rows]
        except Exception as e:
            print("Error al listar info prismas auto json: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlObtenerInfoPrismasManualJSONproyecto(proyecto):
        tabla = "prismas" + str(proyecto)
        sql = f"""SELECT
            nombre_prisma,
            (SELECT TOP 1 este_target FROM {tabla} AS sub WHERE sub.nombre_prisma = p.nombre_prisma AND sub.state_prisma = 1 
            ORDER BY sub.hora_prisma ASC) AS este_inicial,
            (SELECT TOP 1 norte_target FROM {tabla} AS sub WHERE sub.nombre_prisma = p.nombre_prisma AND sub.state_prisma = 1 
            ORDER BY sub.hora_prisma ASC) AS norte_inicial,
            (SELECT TOP 1 elevacion_target FROM {tabla} AS sub WHERE sub.nombre_prisma = p.nombre_prisma AND sub.state_prisma = 1 
            ORDER BY sub.hora_prisma ASC) AS nivel_inicial,
            (SELECT TOP 1 este_target FROM {tabla} AS sub WHERE sub.nombre_prisma = p.nombre_prisma AND sub.state_prisma = 1 
            ORDER BY sub.hora_prisma DESC) AS este_final,
            (SELECT TOP 1 norte_target FROM {tabla} AS sub WHERE sub.nombre_prisma = p.nombre_prisma AND sub.state_prisma = 1 
            ORDER BY sub.hora_prisma DESC) AS norte_final,
            (SELECT TOP 1 elevacion_target FROM {tabla} AS sub WHERE sub.nombre_prisma = p.nombre_prisma AND sub.state_prisma = 1 
            ORDER BY sub.hora_prisma DESC) AS nivel_final
        FROM
            {tabla} p
        WHERE
            state_prisma = 1
        GROUP BY
            nombre_prisma
        ORDER BY
            MIN(hora_prisma);"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql)
            rows = cur.fetchall()
            return [tuple(row) for row in rows]
        except Exception as e:
            print("Error al listar info prismas manual json: " + str(e))
            return None
        finally:
            if conn: conn.close()
           
    @staticmethod
    def mdlActualizarLecturaPrisma(tabla, datanueva, idproyecto, username, nombres):
        query_select = f"""SELECT hora_prisma, este_target, norte_target, elevacion_target, distancia_prisma, id_prisma
        FROM {tabla} WHERE id_prisma = ?;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            
            id_registro = datanueva[-1]
            
            cursor.execute(query_select, (id_registro,))
            datos_anteriores_row = cursor.fetchone()
            
            if datos_anteriores_row:
                datos_anteriores = tuple(datos_anteriores_row)
                # CAMBIO: Formato T para consistencia en historial
                fecha_cambio = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
                accion = "update"
                cambios = f"Antiguos: {datos_anteriores}, Nuevos: {datanueva}"
                
                query_historial = """INSERT INTO historial (idproyecto, fecha, accion, tabla, cambios, usuario, nombres)
                VALUES (?, ?, ?, ?, ?, ?, ?);"""
                cursor.execute(query_historial, (idproyecto, fecha_cambio, accion, tabla, cambios, username, nombres))
            
            query = f"""UPDATE {tabla} SET hora_prisma = ?, este_target = ?, norte_target = ?, elevacion_target = ?,
            distancia_prisma = ? WHERE id_prisma = ?;"""
            cursor.execute(query, datanueva)
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error al actualizar lectura prisma: {e}")
            if conn: conn.rollback()
            return False
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlCambiarEstadoLecturaPrisma(tabla, iddetalle):
        sql = f"""
            UPDATE {tabla}
            SET estado_detalle = CASE 
                WHEN estado_detalle = 'Activo' THEN 'Omitido' 
                ELSE 'Activo' 
            END
            WHERE id_detalle = ?;
        """
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            cursor.execute(sql, (iddetalle,))
            conn.commit()
            query_update = f"""UPDATE {tabla} SET estado_prisma = CASE WHEN estado_prisma = 1 THEN 0 ELSE 1 END
            WHERE id_prisma = ?;"""
            cursor.execute(query_update, (iddetalle,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error al cambiar el estado del prisma: {e}")
            return False
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlOmitirLecturasPrismaDesviacion(tabla, prisma, desviacioneste, desviacionnorte):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            
            query_update = f"""
            WITH primeros AS (
                SELECT id_prisma, este_target, norte_target,
                    FIRST_VALUE(este_target) OVER (ORDER BY hora_prisma) AS primera_este,
                    FIRST_VALUE(norte_target) OVER (ORDER BY hora_prisma) AS primera_norte
                FROM {tabla} WHERE nombre_prisma = ?
            )
            UPDATE {tabla} SET estado_prisma = 0
            WHERE id_prisma IN (
                SELECT p.id_prisma
                FROM primeros p
                WHERE 
                    (
                        POWER((p.este_target - p.primera_este) / CAST(? AS FLOAT), 2) +
                        POWER((p.norte_target - p.primera_norte) / CAST(? AS FLOAT), 2)
                    ) > 1
                );"""
            
            params = (prisma, desviacioneste, desviacionnorte)
            cursor.execute(query_update, params)
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al omitir lecturas segun desviacion: {e}")
            return False
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlActivarLecturasPrisma(tabla, prisma):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            query_update = f"""UPDATE {tabla} SET estado_prisma = 1 WHERE nombre_prisma = ?;"""
            cursor.execute(query_update, (prisma,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al activar lecturas del prisma: {e}")
            return False
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlCambiarEstadoLecturaPrismaBloque(tabla, listacodigos):
        if not listacodigos:
            return False
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            placeholders = ','.join(['?'] * len(listacodigos))
            query_update = f"""UPDATE {tabla} SET estado_prisma = CASE WHEN estado_prisma = 1 THEN 0 ELSE 1 END
            WHERE id_prisma IN ({placeholders});"""
            cursor.execute(query_update, listacodigos)
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error al cambiar el estado de los prismas: {e}")
            return False
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlEliminarLecturaPrisma(tabla, iddetalle, idproyecto, username, nombres):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            
            query_select = f"""SELECT * FROM {tabla} WHERE id_prisma = ?;"""
            cursor.execute(query_select, (iddetalle,))
            datos_anteriores_row = cursor.fetchone()
            
            if datos_anteriores_row:
                datos_anteriores = tuple(datos_anteriores_row)
                fecha_cambio = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
                accion = "delete"
                cambios = f"Datos: {datos_anteriores}"
                query_historial = """INSERT INTO historial (idproyecto, fecha, accion, tabla, cambios, usuario, nombres)
                VALUES (?, ?, ?, ?, ?, ?, ?);"""
                cursor.execute(query_historial, (idproyecto, fecha_cambio, accion, tabla, cambios, username, nombres))
            
            query = f"""DELETE FROM {tabla} WHERE id_prisma = ?;"""
            cursor.execute(query, (iddetalle,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error al eliminar lectura del prisma: {e}")
            if conn: conn.rollback()
            return False
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlEliminarLecturasBloquePrisma(tabla, iddetalles, idproyecto, username, nombres):
        if not iddetalles:
            return False
        placeholders = ', '.join(['?' for _ in iddetalles])
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            
            query_select = f"""SELECT * FROM {tabla} WHERE id_prisma IN ({placeholders});"""
            cursor.execute(query_select, iddetalles)
            datos_anteriores = [tuple(row) for row in cursor.fetchall()]
            
            if datos_anteriores:
                fecha_cambio = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
                accion = "delete"
                cambios = f"Datos: {datos_anteriores}"
                query_historial = """INSERT INTO historial (idproyecto, fecha, accion, tabla, cambios, usuario, nombres)
                VALUES (?, ?, ?, ?, ?, ?, ?);"""
                cursor.execute(query_historial, (idproyecto, fecha_cambio, accion, tabla, cambios, username, nombres))
            
            query = f"""DELETE FROM {tabla} WHERE id_prisma IN ({placeholders});"""
            cursor.execute(query, iddetalles)
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error al eliminar lecturas del prisma: {e}")
            if conn: conn.rollback()
            return False
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlCambiarEstadoPrismas(estado, idcomponente):
        sql = """UPDATE instrumentacion SET estado_instrumentacion = ? WHERE id_componente = ?
        AND tipo_equipo = 'PRISMAS';"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (estado, idcomponente))
            conn.commit()
            return True
        except Exception as e:
            print("Error al cambiar estado prismas: " + str(e))
            return False
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlEliminarPrismas(idcomponente):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            query_select = """SELECT * FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'PRISMAS';"""
            cursor.execute(query_select, (idcomponente,))
            dataprismas = [tuple(row) for row in cursor.fetchall()]
            
            if dataprismas:
                query = """DELETE FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'PRISMAS';"""
                cursor.execute(query, (idcomponente,))
                conn.commit()
                if cursor.rowcount > 0:
                    return dataprismas
                else:
                    return None
            else:
                return None
        except Exception as e:
            print(f"Error al eliminar prismas: {e}")
            if conn: conn.rollback()
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlEliminarDataPrismas(tabla, prismas):
        if not prismas:
            return False
        placeholders = ', '.join(['?' for _ in prismas])
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            query = f"""DELETE FROM {tabla} WHERE nombre_prisma IN ({placeholders});"""
            cursor.execute(query, prismas)
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error al eliminar data prismas: {e}")
            return False
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlCambiarPrismaEstado(estado, idcomponente, idinstrumento):
        sql = """UPDATE instrumentacion SET estado_instrumentacion = ? WHERE id_componente = ?
        AND id_instrumentacion = ?;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (estado, idcomponente, idinstrumento))
            conn.commit()
            return True
        except Exception as e:
            print("Error al cambiar estado prisma: " + str(e))
            return False
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlEliminarPrismaUnico(idinstrumento):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            query_select = """SELECT * FROM instrumentacion WHERE id_instrumentacion = ?;"""
            cursor.execute(query_select, (idinstrumento,))
            dataprismas_row = cursor.fetchone()
            
            if dataprismas_row:
                dataprismas = tuple(dataprismas_row)
                query = """DELETE FROM instrumentacion WHERE id_instrumentacion = ?;"""
                cursor.execute(query, (idinstrumento,))
                conn.commit()
                if cursor.rowcount > 0:
                    return dataprismas
                else:
                    return None
            else:
                return None
        except Exception as e:
            print(f"Error al eliminar prisma: {e}")
            if conn: conn.rollback()
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlEliminarPrismaData(tabla, nombreprisma):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            query = f"""DELETE FROM {tabla} WHERE nombre_prisma = ?;"""
            cursor.execute(query, (nombreprisma,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error al eliminar data prisma: {e}")
            return False
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlCambiarComponentePrismas(idcomponente, nuevocomponente):
        sql = """UPDATE instrumentacion SET id_componente = ? WHERE id_componente = ?
        AND tipo_equipo = 'PRISMAS';"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (nuevocomponente, idcomponente))
            conn.commit()
            return True
        except Exception as e:
            print("Error al cambiar componente prismas: " + str(e))
            return False
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlCambiarPrismaComponente(idinstrumento, nuevocomponente):
        sql = """UPDATE instrumentacion SET id_componente = ? WHERE id_instrumentacion = ?;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (nuevocomponente, idinstrumento))
            conn.commit()
            return True
        except Exception as e:
            print("Error al cambiar componente prisma: " + str(e))
            return False
        finally:
            if conn: conn.close()
                
    @staticmethod
    def mdlResumenDesplazamiento(tabla, fechaini, fechafin):
        sql = f"""WITH ResumenDesplazamiento AS (
            SELECT p.nombre_prisma, p.hora_prisma,
                ABS(
                    CASE
                        WHEN p.nombre_prisma <> LAG(p.nombre_prisma) OVER (ORDER BY p.nombre_prisma) THEN 0
                        ELSE p.distancia_prisma - FIRST_VALUE(p.distancia_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)
                    END
                ) AS desplazasd,
                SQRT(
                    POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.elevacion_target - FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                ) AS desplaza3d,
                ABS(p.desplaza_longitudinal) AS desplaza_longitudinal,
                ABS(p.desplaza_transversal) AS desplaza_transversal,
                ABS(p.desplaza_altura) AS desplaza_altura,
                ABS(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) AS desplaza_este,
                ABS(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) AS desplaza_norte,
                ABS(p.elevacion_target - FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) AS desplaza_cota
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN componentes co ON i.id_componente = co.id_componente
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND i.estado_instrumentacion = 1 
            AND p.hora_prisma BETWEEN ? AND ?
            AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
        )
        SELECT nombre_prisma, MIN(hora_prisma) AS fechamin, MAX(hora_prisma) AS fechamax, MAX(desplazasd) AS desplazasd,
        MAX(desplaza3d) AS desplaza3d, MAX(desplaza_longitudinal) AS desplaza_longitudinal, MAX(desplaza_transversal) AS desplaza_transversal,
        MAX(desplaza_altura) AS desplaza_altura, MAX(desplaza_este) AS desplaza_este, MAX(desplaza_norte) AS desplaza_norte, MAX(desplaza_cota) AS desplaza_cota
        FROM ResumenDesplazamiento
        GROUP BY nombre_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (fechaini, fechafin))
            rows = cur.fetchall()
            return [tuple(row) for row in rows]
        except Exception as e:
            print("Error al obtener resumen prismas desplazamiento: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlResumenVelocidad(tabla, fechaini, fechafin):
        sql = f"""WITH ResumenVelocidad AS (
            SELECT p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, p.elevacion_target,
                CASE 
                    WHEN LAG(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                    WHEN DATEDIFF(SECOND, LAG(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) = 0 THEN 0
                    ELSE ABS(SQRT(
                        POWER(p.este_target - LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                        POWER(p.norte_target - LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                        POWER(p.elevacion_target - LAG(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                    ) / (CAST(DATEDIFF(SECOND, LAG(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0))
                END AS VI3D,
                CASE 
                    WHEN DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) = 0 THEN 0
                    ELSE ABS(SQRT(
                        POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                        POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                        POWER(p.elevacion_target - FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                    ) / (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0))
                END AS VA3D,
                CASE 
                    WHEN LAG(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) IS NULL THEN 0
                    WHEN DATEDIFF(SECOND, LAG(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) = 0 THEN 0
                    ELSE ABS(SQRT(
                        POWER(p.este_target - LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                        POWER(p.norte_target - LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                    ) / (CAST(DATEDIFF(SECOND, LAG(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0))
                END AS VI2D,
                CASE 
                    WHEN DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) = 0 THEN 0
                    ELSE ABS(SQRT(
                        POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                        POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                    ) / (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0))
                END AS VA2D,
                CASE
                    WHEN DATEDIFF(SECOND, ISNULL(LAG(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma), p.hora_prisma) = 0 THEN 0
                    ELSE ABS((
                        (p.distancia_prisma - LAG(p.distancia_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma))
                    ) / (CAST(DATEDIFF(SECOND, ISNULL(LAG(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0))
                END AS VISD,
                CASE
                    WHEN DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) = 0 THEN 0
                    ELSE ABS((
                        (p.distancia_prisma - FIRST_VALUE(p.distancia_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma))
                    ) / (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0))
                END AS VASD
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN componentes co ON i.id_componente = co.id_componente
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND i.estado_instrumentacion = 1 
            AND p.hora_prisma BETWEEN ? AND ?
            AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
        )
        SELECT nombre_prisma, MIN(hora_prisma) AS fechamin, MAX(hora_prisma) AS fechamax, MAX(VI3D) AS VI3D, MAX(VA3D) AS VA3D,
        MAX(VI2D) AS VI2D, MAX(VA2D) AS VA2D, MAX(VISD) AS VISD, MAX(VASD) AS VASD
        FROM ResumenVelocidad
        GROUP BY nombre_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (fechaini, fechafin))
            rows = cur.fetchall()
            return [tuple(row) for row in rows]
        except Exception as e:
            print("Error al obtener resumen prismas velocidad: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlResumenTrendPlunge(tabla, fechaini, fechafin):
        sql = f"""WITH ResumenTrendplunge AS (
            SELECT p.nombre_prisma, p.hora_prisma,
                p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS desplaza_este,
                p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS desplaza_norte,
                p.elevacion_target - FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma) AS desplaza_elevacion
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN componentes co ON i.id_componente = co.id_componente
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND i.estado_instrumentacion = 1 
            AND p.hora_prisma BETWEEN ? AND ?
            AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
        ),
        MagnitudCalculada AS (
            SELECT nombre_prisma, hora_prisma, desplaza_este, desplaza_norte, desplaza_elevacion,
                SQRT(POWER(desplaza_norte, 2) + power(desplaza_este, 2)) AS magnitud
            FROM ResumenTrendplunge
        ),
        RankedCD AS (
            SELECT *,
                CASE
                    WHEN desplaza_norte IS NULL OR desplaza_este IS NULL THEN NULL
                    WHEN desplaza_norte = 0 AND desplaza_este = 0 THEN 0
                    WHEN desplaza_norte = 0 AND desplaza_este > 0 THEN 90
                    WHEN desplaza_norte = 0 AND desplaza_este < 0 THEN 270
                    WHEN desplaza_este = 0 AND desplaza_norte > 0 THEN 0
                    WHEN desplaza_este = 0 AND desplaza_norte < 0 THEN 180
                    WHEN desplaza_este > 0 THEN 90 - DEGREES(ATAN(desplaza_norte / (desplaza_este * 1.0)))
                    WHEN desplaza_este < 0 THEN 270 - DEGREES(ATAN(desplaza_norte / (desplaza_este * 1.0)))
                END AS trend,
                CASE
                    WHEN magnitud IS NULL OR desplaza_elevacion IS NULL THEN NULL
                    WHEN magnitud != 0 THEN DEGREES(ATAN(desplaza_elevacion / (magnitud * 1.0)))
                    ELSE 90
                END AS plunge,
                ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma DESC) AS RowAsc
            FROM MagnitudCalculada
        )
        SELECT trend, plunge FROM RankedCD WHERE RowAsc = 1;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (fechaini, fechafin))
            rows = cur.fetchall()
            return [tuple(row) for row in rows]
        except Exception as e:
            print("Error al obtener resumen prismas trend plunge: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlCalcularVectoresDesplazamiento3DA(tabla, prismas, idcomponente):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente]
        sql = f"""WITH ultimas_lecturas AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma,
                (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 3600.0) AS horas,
                (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
                SQRT(
                    POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.elevacion_target - FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                ) AS tresD,
                ROW_NUMBER() OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma DESC) AS rn
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN componentes co ON i.id_componente = co.id_componente
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma, horas, dias, tresD
        FROM ultimas_lecturas WHERE rn = 1;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [tuple(row) for row in rows]
        except Exception as e:
            print("Error al consultar vectores D3D: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlCalcularVectoresDesplazamientoFechas3DA(tabla, prismas, idcomponente, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        sql = f"""WITH ultimas_lecturas AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma,
                (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 3600.0) AS horas,
                (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,
                SQRT(
                    POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.elevacion_target - FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                ) AS tresD,
                ROW_NUMBER() OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma DESC) AS rn
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN componentes co ON i.id_componente = co.id_componente
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders})
            AND i.id_componente = ? AND p.hora_prisma BETWEEN ? AND ?
            AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma, horas, dias, tresD
        FROM ultimas_lecturas WHERE rn = 1;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [tuple(row) for row in rows]
        except Exception as e:
            print("Error al consultar vectores D3D Fechas: " + str(e))
            return None
        finally:
            if conn: conn.close()
            
    @staticmethod
    def mdlCalcularVectoresVelocidadPositivaVI3D(tabla, prismas, idcomponente):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente]        
        sql = f"""WITH PrismasCTE AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, p.elevacion_target,
                (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,		
                SQRT(
                    POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.elevacion_target - FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                ) AS tresD
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN componentes co ON i.id_componente = co.id_componente
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
        ),
        CalculoCompleto AS (
            SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24 AS HORAS,
            CASE 
                WHEN LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) IS NULL THEN 0
                WHEN DATEDIFF(SECOND, LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) = 0 THEN 0
                ELSE tresD / (CAST(DATEDIFF(SECOND, LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0)
            END AS VI3D
            FROM PrismasCTE
        )
        SELECT c.* FROM CalculoCompleto c INNER JOIN (SELECT nombre_prisma, MAX(FECHAS) AS ultima_fecha FROM CalculoCompleto GROUP BY nombre_prisma) ultimas
        ON c.nombre_prisma = ultimas.nombre_prisma AND c.FECHAS = ultimas.ultima_fecha;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [tuple(row) for row in rows]
        except Exception as e:
            print("Error al consultar vectores vi3d positiva: " + str(e))
            return None
        finally:
            if conn: conn.close()
            
    @staticmethod
    def mdlCalcularVectoresVelocidadPositivaFechasVI3D(tabla, prismas, idcomponente, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        sql = f"""WITH PrismasCTE AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, p.elevacion_target,
                (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,		
                SQRT(
                    POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.elevacion_target - FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                ) AS tresD
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN componentes co ON i.id_componente = co.id_componente
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ?
            AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
        ),
        CalculoCompleto AS (
            SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24 AS HORAS,
            CASE 
                WHEN LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) IS NULL THEN 0
                WHEN DATEDIFF(SECOND, LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) = 0 THEN 0
                ELSE tresD / (CAST(DATEDIFF(SECOND, LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0)
            END AS VI3D
            FROM PrismasCTE
        )
        SELECT c.* FROM CalculoCompleto c INNER JOIN (SELECT nombre_prisma, MAX(FECHAS) AS ultima_fecha FROM CalculoCompleto GROUP BY nombre_prisma) ultimas
        ON c.nombre_prisma = ultimas.nombre_prisma AND c.FECHAS = ultimas.ultima_fecha;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [tuple(row) for row in rows]
        except Exception as e:
            print("Error al consultar vectores vi3d positiva fechas: " + str(e))
            return None
        finally:
            if conn: conn.close()
        
    @staticmethod
    def mdlCalcularVectoresVelocidadVI3D(tabla, prismas, idcomponente):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente]
        sql = f"""WITH PrismasCTE AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, p.elevacion_target,
                (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,		
                SQRT(
                    POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.elevacion_target - FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                ) AS tresD
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN componentes co ON i.id_componente = co.id_componente
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
        ),
        CalculoCompleto AS (
            SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24 AS HORAS,
            CASE 
                WHEN LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) IS NULL THEN 0
                WHEN DATEDIFF(SECOND, LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) = 0 THEN 0
                ELSE (tresD - LAG(tresD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma))
                    / (CAST(DATEDIFF(SECOND, LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0)
            END AS VI3D
            FROM PrismasCTE
        )
        SELECT c.* FROM CalculoCompleto c INNER JOIN (SELECT nombre_prisma, MAX(FECHAS) AS ultima_fecha FROM CalculoCompleto GROUP BY nombre_prisma) ultimas
        ON c.nombre_prisma = ultimas.nombre_prisma AND c.FECHAS = ultimas.ultima_fecha;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [tuple(row) for row in rows]
        except Exception as e:
            print("Error al consultar vectores vi3d: " + str(e))
            return None
        finally:
            if conn: conn.close()
            
    @staticmethod
    def mdlCalcularVectoresVelocidadFechasVI3D(tabla, prismas, idcomponente, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        sql = f"""WITH PrismasCTE AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, p.elevacion_target,
                (CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) AS FLOAT) / 86400.0) AS dias,		
                SQRT(
                    POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.elevacion_target - FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                ) AS tresD
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN componentes co ON i.id_componente = co.id_componente
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ?
            AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
        ),
        CalculoCompleto AS (
            SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24 AS HORAS,
            CASE 
                WHEN LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) IS NULL THEN 0
                WHEN DATEDIFF(SECOND, LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) = 0 THEN 0
                ELSE (tresD - LAG(tresD) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma))
                    / (CAST(DATEDIFF(SECOND, LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) AS FLOAT) / 86400.0)
            END AS VI3D
            FROM PrismasCTE
        )
        SELECT c.* FROM CalculoCompleto c INNER JOIN (SELECT nombre_prisma, MAX(FECHAS) AS ultima_fecha FROM CalculoCompleto GROUP BY nombre_prisma) ultimas
        ON c.nombre_prisma = ultimas.nombre_prisma AND c.FECHAS = ultimas.ultima_fecha;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [tuple(row) for row in rows]
        except Exception as e:
            print("Error al consultar vectores vi3d fechas: " + str(e))
            return None
        finally:
            if conn: conn.close()
            
    @staticmethod
    def mdlDatosPrismasDesviaciones(tabla, tipoprisma, prisma):
        sql = f"""SELECT '{tipoprisma}' AS tipo, nombre_prisma, hora_prisma, ROUND(este_target, 3) AS este_target,
            ROUND(norte_target, 3) AS norte_target, ROUND(elevacion_target, 3) AS elevacion_target,
            distancia_prisma, angulo_horizontal, angulo_vertical,
            CASE estado_prisma
               WHEN 1 THEN 'Activo'
               WHEN 0 THEN 'Omitido'
               ELSE 'Desconocido'
           END AS estado_prisma, id_prisma
        FROM {tabla} WHERE nombre_prisma = ? ORDER BY hora_prisma;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (prisma,))
            results = cur.fetchall()
            return [tuple(row) for row in results]
        except Exception as e:
            print("Error al obtener data prismas desviaciones:", e)
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlObtenerDesviacionStandar(idproyecto, nombreprisma):
        sql = """SELECT * FROM desviaciones WHERE id_proyecto = ? AND nombre_prisma = ?;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idproyecto, nombreprisma))
            row = cur.fetchone()
            if row:
                return tuple(row)
            else:
                return None
        except Exception as e:
            print("Error al obtener desviacion estandar: " + str(e))
            return None
        finally:
            if conn: conn.close()
                
    @staticmethod
    def mdlOmitirLecturaPrisma(tabla, prisma, fecha):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            query_update = f"""UPDATE {tabla} SET estado_prisma = 0 WHERE nombre_prisma = ? AND hora_prisma=?;"""
            cursor.execute(query_update, (prisma, fecha))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al omitir lecturas del prisma: {e}")
            return False
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlVerificarPrismaUnico(nameprisma, idinstrumento, idproyecto):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            query = """SELECT TOP 1 1 FROM instrumentacion i INNER JOIN componentes c ON i.id_componente = c.id_componente
            WHERE LOWER(i.nombre_equipo) = LOWER(?) AND i.id_instrumentacion != ? 
            AND c.id_proyecto = ? AND i.tipo_equipo = 'PRISMAS';"""
            cursor.execute(query, (nameprisma, idinstrumento, idproyecto))
            resultado = cursor.fetchone()
            return bool(resultado)
        except Exception as e:
            print(f"Error al comprobar nombres del prisma: {e}")
            return False
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlActualizarNombrePrisma(nameprisma, nuevoprisma, idinstrumento, idproyecto):
        tabla = f"prismas{idproyecto}"
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            
            query_update_prisma = f"""UPDATE {tabla} SET nombre_prisma = ? WHERE nombre_prisma = ?"""
            cursor.execute(query_update_prisma, (nuevoprisma, nameprisma))
            filas_prisma = cursor.rowcount
            
            query_update_instrumento = """UPDATE instrumentacion SET nombre_equipo = ? WHERE id_instrumentacion = ?"""
            cursor.execute(query_update_instrumento, (nuevoprisma, idinstrumento))
            filas_instrumento = cursor.rowcount
            
            if filas_prisma == 0:
                conn.rollback()
                print(f"No se encontró el prisma '{nameprisma}' para actualizar")
                return False
            
            if filas_instrumento == 0:
                conn.rollback()
                print(f"No se pudo actualizar el instrumento con ID {idinstrumento}")
                return False
            
            conn.commit()
            return True
        except Exception as e:
            if conn: conn.rollback()
            print(f"Error al actualizar nombre del prisma: {e}")
            return False
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlObtenerDatosCompletosPrismasFecha(tabla, idcomponente, fechaini, fechafin):
        # Esta consulta usa CTEs para obtener el primer y último registro de cada prisma en una sola pasada
        sql = f"""
        WITH RankedPrismas AS (
            SELECT 
                i.id_instrumentacion, 
                p.nombre_prisma, 
                p.este_target, 
                p.norte_target, 
                p.elevacion_target, 
                p.hora_prisma,
                i.id_componente,
                ROW_NUMBER() OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma ASC) as rn_asc,
                ROW_NUMBER() OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma DESC) as rn_desc
            FROM {tabla} p 
            INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            INNER JOIN componentes co ON i.id_componente = co.id_componente
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 
              AND i.id_componente = ? 
              AND p.hora_prisma BETWEEN ? AND ?
              AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')
        ),
        CalculoDistancia AS (
            SELECT 
                id_instrumentacion,
                nombre_prisma,
                id_componente,
                MAX(CASE WHEN rn_asc = 1 THEN hora_prisma END) as hora_inicial,
                MAX(CASE WHEN rn_asc = 1 THEN este_target END) as este_inicial,
                MAX(CASE WHEN rn_asc = 1 THEN norte_target END) as norte_inicial,
                MAX(CASE WHEN rn_asc = 1 THEN elevacion_target END) as nivel_inicial,
                MAX(CASE WHEN rn_desc = 1 THEN hora_prisma END) as hora_final,
                MAX(CASE WHEN rn_desc = 1 THEN este_target END) as este_final,
                MAX(CASE WHEN rn_desc = 1 THEN norte_target END) as norte_final,
                MAX(CASE WHEN rn_desc = 1 THEN elevacion_target END) as nivel_final,
                SQRT(
                    POWER(MAX(CASE WHEN rn_desc = 1 THEN este_target END) - MAX(CASE WHEN rn_asc = 1 THEN este_target END), 2) +
                    POWER(MAX(CASE WHEN rn_desc = 1 THEN norte_target END) - MAX(CASE WHEN rn_asc = 1 THEN norte_target END), 2) +
                    POWER(MAX(CASE WHEN rn_desc = 1 THEN elevacion_target END) - MAX(CASE WHEN rn_asc = 1 THEN elevacion_target END), 2)
                ) as distancia_3d
            FROM RankedPrismas
            WHERE rn_asc = 1 OR rn_desc = 1
            GROUP BY id_instrumentacion, nombre_prisma, id_componente
        )
        SELECT id_instrumentacion, nombre_prisma, id_componente, 
               este_inicial, norte_inicial, nivel_inicial, hora_inicial,
               este_final, norte_final, nivel_final, hora_final, distancia_3d
        FROM CalculoDistancia
        ORDER BY nombre_prisma;
        """
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idcomponente, fechaini, fechafin))
            rows = cur.fetchall()
            return [tuple(row) for row in rows]
        except Exception as e:
            print("Error al obtener datos completos de prismas: " + str(e))
            return None
        finally:
            if conn: conn.close()