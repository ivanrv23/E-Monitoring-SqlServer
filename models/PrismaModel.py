from sqlite3 import Error
from services.security.apis.conexiones.conexion import Connection
from datetime import datetime

class PrismaModel:
    
    # limpiar tabla BD
    # DELETE FROM prismas;
    # DELETE FROM sqlite_sequence WHERE name='prismas';

    def mdlObtenerFechasMaximasPrismas(tabla):
        sql = f"""SELECT MAX(hora_prisma) AS max_fecha FROM {tabla} WHERE state_prisma = 1;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al obtener fechas max prismas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlListarDataPrismasNombre(table, nombres):
        placeholders = ', '.join(['?' for _ in nombres])  # Crear placeholders para los nombres
        sql = f"""SELECT nombre_prisma, estado_prisma, perfil_prisma, hora_prisma, angulo_horizontal, angulo_vertical, distancia_prisma, tipoppm_prisma, ppm_prisma, 
            presion_prisma, temperatura_prisma, constante_prisma, este_target, norte_target, elevacion_target, altura_reflector, altura_instrumento, este_estacion, 
            norte_estacion, altura_estacion, medicion_prisma, diferencia_tiempocorto, diferencia_tiempolargo, diferencia_limitevelocidad, distancia_horizontal, 
            diferencia_atipica, desplaza_longitudinal, desplaza_transversal, desplaza_altura, grupo_puntos FROM {table} WHERE state_prisma = 1 
            AND nombre_prisma IN ({placeholders}) ORDER BY nombre_prisma, hora_prisma;"""  # Utilizar placeholders en la consulta
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, nombres)  # Pasar nombres como parámetros
            rows = cur.fetchall()
            return rows  # Devolver todas las filas encontradas
        except Error as e:
            print("Error al listar prismas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    def mdlListarDataPrismasNombre_manuales(table, nombres):
        placeholders = ', '.join(['?' for _ in nombres])  # Crear placeholders para los nombres
        sql = f"""SELECT nombre_prisma, hora_prisma, norte_target, este_target, elevacion_target, angulo_horizontal, angulo_vertical, distancia_prisma
        FROM {table} WHERE state_prisma = 1 AND nombre_prisma IN ({placeholders}) ORDER BY nombre_prisma, hora_prisma;"""  # Utilizar placeholders en la consulta
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, nombres)  # Pasar nombres como parámetros
            rows = cur.fetchall()
            return rows  # Devolver todas las filas encontradas
        except Error as e:
            print("Error al listar prismas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlResumenPrismaNombre(tabla, nombres, fechaini, fechafin, tipo_prisma):
        nombres_str = ','.join(['?' for _ in nombres])  # Creamos una cadena de comodines para los nombres
        sql = f"""SELECT nombre_prisma, tipo, MIN(hora) AS fecha_minima, MAX(hora) AS fecha_maxima, COUNT(*) AS cantidad,
            CAST(JULIANDAY(MAX(hora)) - JULIANDAY(MIN(hora)) + 1 AS INTEGER) as total_dias
        FROM (
            SELECT nombre_prisma, '{tipo_prisma}' AS tipo, hora_prisma AS hora FROM {tabla} WHERE state_prisma = 1
            AND nombre_prisma IN ({nombres_str}) AND hora_prisma BETWEEN ? AND ?
        ) GROUP BY nombre_prisma;"""

        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # Agregamos los nombres y los límites de fecha a los parámetros de la consulta
            cur.execute(sql, tuple(nombres) + (fechaini, fechafin))
            rows = cur.fetchall()
            return rows
        except Error as e:
            print("Error al consultar Resumen prisma: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    # obtener fecha mini y maximo de los prismas automatizados
    def mdlObtenerFechaMinMaxAuto(proyectoid):
        tabla = "prismas" + str(proyectoid)
        sql = """SELECT MIN(hora_prisma) AS min_fecha, MAX(hora_prisma) AS max_fecha FROM """ + tabla + """ WHERE state_prisma = 1;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al obtener fechas min-max: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # obtener fecha mini y maximo de los prismas manuales
    def mdlObtenerFechaMinMaxManual(proyectoid):
        tabla = "prismas" + str(proyectoid)
        sql = """SELECT MIN(hora_prisma) AS min_fecha, MAX(hora_prisma) AS max_fecha FROM """ + tabla + """ WHERE state_prisma = 1;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al obtener fechas min-max: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # MOSTRAR LISTA DE PRISMAS AUTO INICIALES SIN REPETIRSE
    def mdlListarPrismasUnicosMinima(tabla, prismas, idcomponente):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente]
        sql = f"""SELECT i.id_instrumentacion, i.nombre_equipo, p.este_target, p.norte_target, p.elevacion_target, i.id_componente,
        i.tipo_equipo, MIN(hora_prisma) AS hora FROM {tabla} p INNER JOIN instrumentacion i
        ON p.nombre_prisma = i.nombre_equipo WHERE p.state_prisma = 1 AND p.estado_prisma = 1
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        GROUP BY p.nombre_prisma, i.id_instrumentacion, i.id_componente, i.tipo_equipo
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al listar prismas ini: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # MOSTRAR LISTA DE PRISMAS AUTO INICIALES SIN REPETIRSE POR FECHA
    def mdlListarPrismasUnicosFechaMinima(tabla, prismas, idcomponente, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        sql = f"""SELECT i.id_instrumentacion, i.nombre_equipo, p.este_target, p.norte_target, p.elevacion_target, i.id_componente,
        i.tipo_equipo, MIN(hora_prisma) AS hora FROM {tabla} p INNER JOIN instrumentacion i
        ON p.nombre_prisma = i.nombre_equipo WHERE p.state_prisma = 1 AND p.estado_prisma = 1
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        AND p.hora_prisma BETWEEN ? AND ? GROUP BY p.nombre_prisma, i.id_instrumentacion, i.id_componente, i.tipo_equipo
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al listar prismas ini fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # MOSTRAR LISTA DE PRISMAS INICIALES AUTOMATIZADOS SIN REPETIRSE POR FECHAS            
    def mdlTraerPrismasInicialesProyectoFecha(proyecto, fechaini, fechafin):
        tabla = "prismas" + str(proyecto)
        sql = """SELECT *, MIN(id_prisma) FROM """ + tabla + """ WHERE state_prisma = 1 AND hora_prisma BETWEEN ? AND ? GROUP BY nombre_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (fechaini, fechafin))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al listar prismas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # MOSTRAR LISTA DE PRISMAS INICIALES MANUALES SIN REPETIRSE POR FECHAS            
    def mdlPrismasManualesInicialesProyectoFecha(proyecto, fechaini, fechafin):
        tabla = "prismas" + str(proyecto)
        sql = """SELECT *, MIN(id_prisma) FROM """ + tabla + """ WHERE state_prisma = 1 AND hora_prisma BETWEEN ? AND ? GROUP BY nombre_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (fechaini, fechafin))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al listar prismas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # MOSTRAR PRISMA INICIAL AUTOMATIZADO POR NOMBRE Y FECHAS            
    def mdlTraerPrismaInicialProyectoNombreFecha(proyecto, nombre, fechaini, fechafin):
        tabla = "prismas" + str(proyecto)
        sql = """SELECT *, MIN(id_prisma) FROM """ + tabla + """ WHERE state_prisma = 1 AND nombre_prisma = ? AND hora_prisma BETWEEN ? AND ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (nombre, fechaini, fechafin))
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al listar prismas por fecha: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # MOSTRAR LISTA DE PRISMAS FINALES AUTOMATIZADOS SIN REPETIRSE POR FECHAS   
    def mdlTraerPrismasFinalesProyectoFecha(proyecto, fechaini, fechafin):
        tabla = "prismas" + str(proyecto)
        sql = """SELECT *, MAX(id_prisma) FROM """ + tabla + """ WHERE state_prisma = 1 AND hora_prisma BETWEEN ? AND ? GROUP BY nombre_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (fechaini, fechafin))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al listar prismas: " + str(e))
            return None
        finally:
            if conn:
                conn.close() 
    
    # MOSTRAR LISTA DE PRISMAS FINALES MANUALES SIN REPETIRSE POR FECHAS   
    def mdlPrismasManualesFinalesProyectoFecha(proyecto, fechaini, fechafin):
        tabla = "prismas" + str(proyecto)
        sql = """SELECT *, MAX(id_prisma) FROM """ + tabla + """ WHERE state_prisma = 1 AND hora_prisma BETWEEN ? AND ? GROUP BY nombre_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (fechaini, fechafin))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al listar prismas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()  
    
    # MOSTRAR PRISMA FINAL AUTOMATIZADO
    def mdlListarPrismasUnicosMaxima(tabla, prismas, idcomponente):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente]
        sql = f"""SELECT i.id_instrumentacion, i.nombre_equipo, p.este_target, p.norte_target, p.elevacion_target, i.id_componente,
        i.tipo_equipo, MAX(hora_prisma) AS hora FROM {tabla} p INNER JOIN instrumentacion i
        ON p.nombre_prisma = i.nombre_equipo WHERE p.state_prisma = 1 AND p.estado_prisma = 1
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        GROUP BY p.nombre_prisma, i.id_instrumentacion, i.id_componente, i.tipo_equipo
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al listar prismas max: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # MOSTRAR PRISMA FINAL AUTOMATIZADO POR FECHAS            
    def mdlListarPrismasUnicosFechaMaxima(tabla, prismas, idcomponente, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        sql = f"""SELECT i.id_instrumentacion, i.nombre_equipo, p.este_target, p.norte_target, p.elevacion_target, i.id_componente,
        i.tipo_equipo, MAX(hora_prisma) AS hora FROM {tabla} p INNER JOIN instrumentacion i
        ON p.nombre_prisma = i.nombre_equipo WHERE p.state_prisma = 1 AND p.estado_prisma = 1
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        AND p.hora_prisma BETWEEN ? AND ? GROUP BY p.nombre_prisma, i.id_instrumentacion, i.id_componente, i.tipo_equipo
        ORDER BY p.nombre_prisma, p.hora_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al listar prismas max fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # MOSTRAR PRISMA INICIAL MANUAL FECHAS            
    def mdlListarPrismasFechaMinimaUnicos(tabla, proyecto, fechaini, fechafin, tipo):
        sql = f"""SELECT i.id_instrumentacion, i.nombre_equipo, p.este_target, p.norte_target, p.elevacion_target, c.id_componente,
        i.tipo_equipo, MIN(hora_prisma) AS hora FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        INNER JOIN componentes c ON i.id_componente = c.id_componente WHERE p.state_prisma = 1 AND hora_prisma BETWEEN ? AND ?
        AND c.id_proyecto = ? AND i.tipo_equipo = ? GROUP BY nombre_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (fechaini, fechafin, proyecto, tipo))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al listar prismas minima: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # ACTUALIZAR EL ESTADO DEL PRISMA           
    def mdlCambiarEstadoPrisma(tabla, nombreprisma, estado_prisma):
        sql = """UPDATE """ + tabla + """ SET state_prisma = ? WHERE nombre_prisma = ?"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (str(estado_prisma), nombreprisma))
            conn.commit()
            return True
        except Error as e:
            print("Error al cambiar estado prisma: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    # ELIMINAR EL PRISMA           
    def mdlEliminarPrisma(tabla, nombreprisma):
        sql = """DELETE FROM """ + tabla + """ WHERE nombre_prisma = ?"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (nombreprisma,))
            conn.commit()
            if cur.rowcount > 0:
                return True
            else:
                return False
        except Error as e:
            print("Error al eliminar prisma: " + str(e))
            return False
        finally:
            if conn:
                conn.close() 
    
    # MOSTRAR LISTA DE PRISMAS INICIALES MANUALES SIN REPETIRSE POR PROYECTO            
    def mdlListarPrismasManualesProyecto(proyecto):
        tabla = "prismas" + str(proyecto)
        conn = Connection.connectionDB()
        sql = """SELECT *, MIN(id_prisma) FROM """ + tabla + """ WHERE state_prisma = '1' GROUP BY nombre_prisma;"""
        try:
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al listar nombre prismas manual: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # AGREGAR PRISMAS MANUALES DESDE LA TABLA   
    def mdlGuardarPrismasManualesTabla(proyecto, data):
        # DELETE FROM prismas;
        # DELETE FROM sqlite_sequence WHERE name='prismas';
        try:
            conn = Connection.connectionDB()
            nombretabla = "prismas" + str(proyecto)
            cursor = conn.cursor()
            sqltable = """CREATE TABLE IF NOT EXISTS """ + nombretabla + """ (
                id_prisma INTEGER NOT NULL UNIQUE,
                state_prisma INTEGER NOT NULL DEFAULT 1,
                estado_prisma INTEGER NOT NULL DEFAULT 1, 
                nombre_prisma TEXT NOT NULL, 
                perfil_prisma TEXT, 
                hora_prisma TEXT NOT NULL, 
                angulo_horizontal TEXT, 
                angulo_vertical TEXT, 
                distancia_prisma NUMERIC DEFAULT 0, 
                tipoppm_prisma TEXT, 
                ppm_prisma NUMERIC DEFAULT 0, 
                presion_prisma NUMERIC DEFAULT 0, 
                temperatura_prisma NUMERIC DEFAULT 0, 
                constante_prisma NUMERIC DEFAULT 0, 
                este_target NUMERIC NOT NULL, 
                norte_target NUMERIC NOT NULL, 
                elevacion_target NUMERIC NOT NULL, 
                altura_reflector NUMERIC DEFAULT 0, 
                altura_instrumento NUMERIC DEFAULT 0, 
                este_estacion NUMERIC DEFAULT 0, 
                norte_estacion NUMERIC DEFAULT 0, 
                altura_estacion NUMERIC DEFAULT 0, 
                medicion_prisma NUMERIC DEFAULT 0, 
                diferencia_tiempocorto NUMERIC DEFAULT 0,
                diferencia_tiempolargo NUMERIC DEFAULT 0, 
                diferencia_limitevelocidad NUMERIC DEFAULT 0, 
                distancia_horizontal NUMERIC DEFAULT 0, 
                diferencia_atipica NUMERIC DEFAULT 0, 
                desplaza_longitudinal NUMERIC DEFAULT 0, 
                desplaza_transversal NUMERIC DEFAULT 0, 
                desplaza_altura NUMERIC DEFAULT 0, 
                grupo_puntos TEXT,
                PRIMARY KEY("id_prisma" AUTOINCREMENT)
            );"""
            cursor.execute("PRAGMA foreign_keys = OFF")
            cursor.execute("PRAGMA synchronous = OFF")
            cursor.execute("PRAGMA journal_mode = OFF")
            cursor.execute("PRAGMA temp_store = MEMORY")
            cursor.execute("PRAGMA cache_size = 100000")
            cursor.execute(sqltable)
            conn.execute("BEGIN TRANSACTION")
            # Crear un conjunto de tuplas con los valores de fecha y hora para comparar los registros existentes
            existen_prismas = set([(dato[0], dato[1]) for dato in cursor.execute(f"SELECT nombre_prisma, hora_prisma FROM {nombretabla};")])
            lote_registros = []
            contador = 0
            for fila in data:
                fecha_original = fila[1]
                hora_original = fila[2]
                distancia_original = fila[6]
                este_original = fila[3]
                norte_original = fila[4]
                nivel_original = fila[5]
                horiz_original = fila[7]
                verti_original = fila[8]
                # completar el formato de fecha
                fecha_hora = fecha_original + " " + hora_original
                # Verifica si el registro no existe en el conjunto
                if (fila[0], fecha_hora) not in existen_prismas:
                    row = [] 
                    row.append(fila[0])
                    row.append(fecha_hora)
                    row.append(distancia_original)
                    row.append(este_original)
                    row.append(norte_original)
                    row.append(nivel_original)
                    row.append(horiz_original)
                    row.append(verti_original)
                    lote_registros.append(row)
                    contador += 1
                if contador % 1000 == 0:
                    cursor.executemany(f"""INSERT INTO {nombretabla} (state_prisma, estado_prisma, nombre_prisma, hora_prisma, distancia_prisma, este_target,
                        norte_target, elevacion_target, angulo_horizontal, angulo_vertical) VALUES (1, 1, ?, ?, ?, ?, ?, ?, ?, ?)""", lote_registros)
                    lote_registros = []
            if lote_registros:
                cursor.executemany(f"""INSERT INTO {nombretabla} (state_prisma, estado_prisma, nombre_prisma, hora_prisma, distancia_prisma, este_target,
                    norte_target, elevacion_target, angulo_horizontal, angulo_vertical) VALUES (1, 1, ?, ?, ?, ?, ?, ?, ?, ?)""", lote_registros)
            conn.execute("COMMIT")
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute("PRAGMA synchronous = NORMAL")
            cursor.execute("PRAGMA journal_mode = DELETE")
            return True
        except Error as e:
            print("Error al guardar los prismas de la tabla " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    # LISTAR LA DATA DE LOS PRISMAS POR PROYECTO                  
    def mdlListarDataPrismasProyecto(proyecto, fechaini, fechafin):
        table = "prismas" + str(proyecto)
        try:
            conn = Connection.connectionDB()
            sql = """SELECT * FROM """ + table + """ WHERE state_prisma = '1' AND hora_prisma BETWEEN '""" + fechaini + """' AND '""" + fechafin + """';"""
            
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al listar prismas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # MOSTRAR DATA DE PRISMAS MANUALES POR FECHAS            
    def mdlTraerDataPrismasManualesFecha(proyecto, fechaini, fechafin):
        tabla = "prismas" + str(proyecto)
        sql = """WITH prismasmanuales AS (
            SELECT 
                id_prisma, nombre_prisma, state_prisma, hora_prisma, 
                COALESCE(CAST(julianday(hora_prisma) - julianday(LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma)) AS NUMERIC), 0) AS dias,
                norte_target, este_target, elevacion_target, angulo_horizontal, angulo_vertical, distancia_prisma,
                COALESCE(LAG(norte_target) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), 0) AS norteanterior,
                COALESCE(LAG(este_target) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), 0) AS esteanterior,
                COALESCE(LAG(elevacion_target) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), 0) AS elevacionanterior,
                COALESCE(LAG(distancia_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), 0) AS distanciaanterior,
                (norte_target - FIRST_VALUE(norte_target) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma)) AS danorte,
                (este_target - FIRST_VALUE(este_target) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma)) AS daeste,
                (elevacion_target - FIRST_VALUE(elevacion_target) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma)) AS danivel,
                (distancia_prisma - FIRST_VALUE(distancia_prisma) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma)) AS dadistancia,
                SQRT(
                    POWER(norte_target - FIRST_VALUE(norte_target) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma), 2) + 
                    POWER(este_target - FIRST_VALUE(este_target) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma), 2)) AS magnitudNE
            FROM """ + tabla + """ 
            WHERE state_prisma = '1' AND hora_prisma BETWEEN '""" + fechaini + """' AND '""" + fechafin + """'
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
                WHEN danorte > 0 AND daeste > 0 THEN 90 - (180 / PI()) * ATAN(danorte / daeste)
                WHEN danorte < 0 AND daeste > 0 THEN 90 - (180 / PI()) * ATAN(danorte / daeste)
                WHEN danorte < 0 AND daeste < 0 THEN 270 - (180 / PI()) * ATAN(danorte / daeste)
                WHEN danorte > 0 AND daeste < 0 THEN 270 - (180 / PI()) * ATAN(danorte / daeste)
            END AS trend, 
            CASE WHEN magnitudNE = 0 THEN 0 ELSE ((180 / PI()) * ATAN(danivel / magnitudNE)) END AS plunge
        FROM prismasmanuales;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al listar prismas manuales: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
                
    # MOSTRAR LISTA DE PRISMAS INICIALES AUTOMATIZADOS SIN REPETIRSE POR PROYECTO            
    def mdlListarPrismasProyecto(proyecto):
        tabla = "prismas" + str(proyecto)
        sql = """SELECT *, MIN(id_prisma) FROM """ + tabla + """ WHERE state_prisma = 1 GROUP BY nombre_prisma"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al listar nombre prismas auto: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # LISTAR LOS PRISMAS AUTO CON COORDENADAS INICIALES Y FINALES           
    def mdlObtenerInfoPrismasAutoJSONproyecto(proyecto):
        tabla = "prismas" + str(proyecto)
        sql = """SELECT
            nombre_prisma,
            (SELECT este_target FROM """ + tabla + """ AS sub WHERE sub.nombre_prisma = p.nombre_prisma AND sub.state_prisma = '1' 
            ORDER BY sub.hora_prisma ASC LIMIT 1) AS este_inicial,
            (SELECT norte_target FROM """ + tabla + """ AS sub WHERE sub.nombre_prisma = p.nombre_prisma AND sub.state_prisma = '1' 
            ORDER BY sub.hora_prisma ASC LIMIT 1) AS norte_inicial,
            (SELECT elevacion_target FROM """ + tabla + """ AS sub WHERE sub.nombre_prisma = p.nombre_prisma AND sub.state_prisma = '1' 
            ORDER BY sub.hora_prisma ASC LIMIT 1) AS nivel_inicial,
            (SELECT este_target FROM """ + tabla + """ AS sub WHERE sub.nombre_prisma = p.nombre_prisma AND sub.state_prisma = '1' 
            ORDER BY sub.hora_prisma DESC LIMIT 1) AS este_final,
            (SELECT norte_target FROM """ + tabla + """ AS sub WHERE sub.nombre_prisma = p.nombre_prisma AND sub.state_prisma = '1' 
            ORDER BY sub.hora_prisma DESC LIMIT 1) AS norte_final,
            (SELECT elevacion_target FROM """ + tabla + """ AS sub WHERE sub.nombre_prisma = p.nombre_prisma AND sub.state_prisma = '1' 
            ORDER BY sub.hora_prisma DESC LIMIT 1) AS nivel_final
        FROM
            """ + tabla + """ p
        WHERE
            state_prisma = '1'
        GROUP BY
            nombre_prisma
        ORDER BY
            hora_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al listar info prismas auto json: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # LISTAR LOS PRISMAS MANUALES CON COORDENADAS INICIALES Y FINALES           
    def mdlObtenerInfoPrismasManualJSONproyecto(proyecto):
        tabla = "prismas" + str(proyecto)
        sql = """SELECT
            nombre_prisma,
            (SELECT este_target FROM """ + tabla + """ AS sub WHERE sub.nombre_prisma = p.nombre_prisma AND sub.state_prisma = '1' 
            ORDER BY sub.hora_prisma ASC LIMIT 1) AS este_inicial,
            (SELECT norte_target FROM """ + tabla + """ AS sub WHERE sub.nombre_prisma = p.nombre_prisma AND sub.state_prisma = '1' 
            ORDER BY sub.hora_prisma ASC LIMIT 1) AS norte_inicial,
            (SELECT elevacion_target FROM """ + tabla + """ AS sub WHERE sub.nombre_prisma = p.nombre_prisma AND sub.state_prisma = '1' 
            ORDER BY sub.hora_prisma ASC LIMIT 1) AS nivel_inicial,
            (SELECT este_target FROM """ + tabla + """ AS sub WHERE sub.nombre_prisma = p.nombre_prisma AND sub.state_prisma = '1' 
            ORDER BY sub.hora_prisma DESC LIMIT 1) AS este_final,
            (SELECT norte_target FROM """ + tabla + """ AS sub WHERE sub.nombre_prisma = p.nombre_prisma AND sub.state_prisma = '1' 
            ORDER BY sub.hora_prisma DESC LIMIT 1) AS norte_final,
            (SELECT elevacion_target FROM """ + tabla + """ AS sub WHERE sub.nombre_prisma = p.nombre_prisma AND sub.state_prisma = '1' 
            ORDER BY sub.hora_prisma DESC LIMIT 1) AS nivel_final
        FROM
            """ + tabla + """ p
        WHERE
            state_prisma = '1'
        GROUP BY
            nombre_prisma
        ORDER BY
            hora_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al listar info prismas manual json: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
           
    def mdlActualizarLecturaPrisma(tabla, datanueva, idproyecto, username, nombres):
        query_select = f"""SELECT hora_prisma, este_target, norte_target, elevacion_target, distancia_prisma, id_prisma
        FROM {tabla} WHERE id_prisma = ?;"""
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            cursor.execute(query_select, (datanueva[-1],))
            datos_anteriores = cursor.fetchone()
            if datos_anteriores:
                fecha_cambio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                accion = "update"
                cambios = f"Antiguos: {datos_anteriores}, Nuevos: {datanueva}"
                query_historial = """INSERT INTO historial (idproyecto, fecha, accion, tabla, cambios, usuario, nombres)
                VALUES (?, ?, ?, ?, ?, ?, ?);"""
                cursor.execute(query_historial, (idproyecto, fecha_cambio, accion, tabla, cambios, username, nombres))
            # actualizar prisma
            query = f"""UPDATE {tabla} SET hora_prisma = ?, este_target = ?, norte_target = ?, elevacion_target = ?,
            distancia_prisma = ? WHERE id_prisma = ?;"""
            cursor.execute(query, datanueva)
            conn.commit()
            if cursor.rowcount > 0:
                return True
            else:
                return False
        except Exception as e:
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlCambiarEstadoLecturaPrisma(tabla, iddetalle):
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            query_update = f"""UPDATE {tabla} SET estado_prisma = CASE estado_prisma WHEN 1 THEN 0 ELSE 1 END
            WHERE id_prisma = ?;"""
            cursor.execute(query_update, (iddetalle,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error al cambiar el estado del prisma: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlOmitirLecturasPrismaDesviacion(tabla, prisma, desviacioneste, desviacionnorte):
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            query_update = f"""WITH primeros AS (
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
                        ((p.este_target - p.primera_este) / ?) * ((p.este_target - p.primera_este) / ?) +
                        ((p.norte_target - p.primera_norte) / ?) * ((p.norte_target - p.primera_norte) / ?)
                    ) > 1
                );"""
            params = (prisma, desviacioneste, desviacioneste, desviacionnorte, desviacionnorte)
            cursor.execute(query_update, params)
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al omitir lecturas segun desviacion: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlActivarLecturasPrisma(tabla, prisma):
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
            if conn:
                conn.close()
    
    def mdlCambiarEstadoLecturaPrismaBloque(tabla, listacodigos):
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            placeholders = ','.join(['?'] * len(listacodigos))
            query_update = f"""UPDATE {tabla} SET estado_prisma = CASE estado_prisma WHEN 1 THEN 0 ELSE 1 END
            WHERE id_prisma IN ({placeholders});"""
            cursor.execute(query_update, listacodigos)
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error al cambiar el estado de los prismas: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlEliminarLecturaPrisma(tabla, iddetalle, idproyecto, username, nombres):
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # guardar en historial
            query_select = f"""SELECT * FROM {tabla} WHERE id_prisma = ?;"""
            cursor.execute(query_select, (iddetalle,))
            datos_anteriores = cursor.fetchone()
            if datos_anteriores:
                fecha_cambio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                accion = "delete"
                cambios = f"Datos: {datos_anteriores}"
                query_historial = """INSERT INTO historial (idproyecto, fecha, accion, tabla, cambios, usuario, nombres)
                VALUES (?, ?, ?, ?, ?, ?, ?);"""
                cursor.execute(query_historial, (idproyecto, fecha_cambio, accion, tabla, cambios, username, nombres))
            # eliminar lectura prisma
            query = f"""DELETE FROM {tabla} WHERE id_prisma = ?;"""
            cursor.execute(query, (iddetalle,))
            conn.commit()
            if cursor.rowcount > 0:
                return True
            else:
                return False
        except Exception as e:
            print(f"Error al eliminar lectura del prisma: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlEliminarLecturasBloquePrisma(tabla, iddetalles, idproyecto, username, nombres):
        placeholders = ', '.join(['?' for _ in iddetalles])
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # guardar en historial
            query_select = f"""SELECT * FROM {tabla} WHERE id_prisma IN ({placeholders});"""
            cursor.execute(query_select, iddetalles)
            datos_anteriores = cursor.fetchall()
            if datos_anteriores:
                fecha_cambio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                accion = "delete"
                cambios = f"Datos: {datos_anteriores}"
                query_historial = """INSERT INTO historial (idproyecto, fecha, accion, tabla, cambios, usuario, nombres)
                VALUES (?, ?, ?, ?, ?, ?, ?);"""
                cursor.execute(query_historial, (idproyecto, fecha_cambio, accion, tabla, cambios, username, nombres))
            # eliminar lecturas prisma
            query = f"""DELETE FROM {tabla} WHERE id_prisma IN ({placeholders});"""
            cursor.execute(query, iddetalles)
            conn.commit()
            if cursor.rowcount > 0:
                return True
            else:
                return False
        except Exception as e:
            print(f"Error al eliminar lecturas del prisma: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlCambiarEstadoPrismas(estado, idcomponente):
        sql = """UPDATE instrumentacion SET estado_instrumentacion = ? WHERE id_componente = ?
        AND tipo_equipo = 'PRISMAS';"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (estado, idcomponente))
            conn.commit()
            return True
        except Error as e:
            print("Error al cambiar estado prismas: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlEliminarPrismas(idcomponente):
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # guardar en historial
            query_select = """SELECT * FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'PRISMAS';"""
            cursor.execute(query_select, (idcomponente,))
            dataprismas = cursor.fetchall()
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
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlEliminarDataPrismas(tabla, prismas):
        placeholders = ', '.join(['?' for _ in prismas])
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            query = f"""DELETE FROM {tabla} WHERE nombre_prisma IN ({placeholders});"""
            cursor.execute(query, prismas)
            conn.commit()
            if cursor.rowcount > 0:
                return True
            else:
                return False
        except Exception as e:
            print(f"Error al eliminar data prismas: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlCambiarPrismaEstado(estado, idcomponente, idinstrumento):
        sql = """UPDATE instrumentacion SET estado_instrumentacion = ? WHERE id_componente = ?
        AND id_instrumentacion = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (estado, idcomponente, idinstrumento))
            conn.commit()
            return True
        except Error as e:
            print("Error al cambiar estado prisma: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlEliminarPrismaUnico(idinstrumento):
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # guardar en historial
            query_select = """SELECT * FROM instrumentacion WHERE id_instrumentacion = ?;"""
            cursor.execute(query_select, (idinstrumento,))
            dataprismas = cursor.fetchone()
            if dataprismas:
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
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlEliminarPrismaData(tabla, nombreprisma):
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            query = f"""DELETE FROM {tabla} WHERE nombre_prisma = ?;"""
            cursor.execute(query, (nombreprisma,))
            conn.commit()
            if cursor.rowcount > 0:
                return True
            else:
                return False
        except Exception as e:
            print(f"Error al eliminar data prisma: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlCambiarComponentePrismas(idcomponente, nuevocomponente):
        sql = """UPDATE instrumentacion SET id_componente = ? WHERE id_componente = ?
        AND tipo_equipo = 'PRISMAS';"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (nuevocomponente, idcomponente))
            conn.commit()
            return True
        except Error as e:
            print("Error al cambiar componente prismas: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlCambiarPrismaComponente(idinstrumento, nuevocomponente):
        sql = """UPDATE instrumentacion SET id_componente = ? WHERE id_instrumentacion = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (nuevocomponente, idinstrumento))
            conn.commit()
            return True
        except Error as e:
            print("Error al cambiar componente prisma: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlResumenDesplazamiento(tabla, fechaini, fechafin):
        sql = f"""WITH ResumenDesplazamiento AS (
            SELECT p.nombre_prisma, p.hora_prisma,
                ABS(
                    CASE
                        WHEN p.nombre_prisma <> LAG(p.nombre_prisma) OVER (ORDER BY p.nombre_prisma) THEN 0
                        ELSE p.distancia_prisma - FIRST_VALUE(p.distancia_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma)
                    END
                ) AS desplazasd,
                SQRT(
                    POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma), 2) +
                    POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma), 2) +
                    POWER(p.elevacion_target - FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma), 2)
                ) AS desplaza3d,
                ABS(p.desplaza_longitudinal) AS desplaza_longitudinal,
                ABS(p.desplaza_transversal) AS desplaza_transversal,
                ABS(p.desplaza_altura) AS desplaza_altura,
                ABS(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma)) AS desplaza_este,
                ABS(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma)) AS desplaza_norte,
                ABS(p.elevacion_target - FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma)) AS desplaza_cota
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND i.estado_instrumentacion = 1 AND p.hora_prisma BETWEEN ? AND ?
        )
        SELECT nombre_prisma, MIN(hora_prisma) AS fechamin, MAX(hora_prisma) AS fechamax, MAX(desplazasd) AS desplazasd,
        MAX(desplaza3d) AS desplaza3d, MAX(desplaza_longitudinal) AS desplaza_longitudinal, MAX(desplaza_transversal) AS desplaza_transversal,
        MAX(desplaza_altura) AS desplaza_altura, MAX(desplaza_este) AS desplaza_este, MAX(desplaza_norte) AS desplaza_norte, MAX(desplaza_cota) AS desplaza_cota
        FROM ResumenDesplazamiento
        GROUP BY nombre_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (fechaini, fechafin))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al obtener resumen prismas desplazamiento: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlResumenVelocidad(tabla, fechaini, fechafin):
        sql = f"""WITH ResumenVelocidad AS (
            SELECT p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, p.elevacion_target,
                CASE 
                    WHEN COALESCE(LAG(julianday(p.hora_prisma)) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 0) = 0 THEN 0
                    ELSE ABS(SQRT(
                        POWER(p.este_target - LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2) +
                        POWER(p.norte_target - LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2) +
                        POWER(p.elevacion_target - LAG(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2)
                    ) / (julianday(p.hora_prisma) - LAG(julianday(p.hora_prisma)) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma)))
                END AS VI3D,
                CASE 
                    WHEN (julianday(p.hora_prisma) - julianday(FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma))) = 0 THEN 0
                    ELSE ABS(SQRT(
                        POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2) +
                        POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2) +
                        POWER(p.elevacion_target - FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2)
                    ) / (julianday(p.hora_prisma) - julianday(FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma))))
                END AS VA3D,
                CASE 
                    WHEN COALESCE(LAG(julianday(p.hora_prisma)) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 0) = 0 THEN 0
                    ELSE ABS(SQRT(
                        POWER(p.este_target - LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2) +
                        POWER(p.norte_target - LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2)
                    ) / (julianday(p.hora_prisma) - LAG(julianday(p.hora_prisma)) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma)))
                END AS VI2D,
                CASE 
                    WHEN (julianday(p.hora_prisma) - julianday(FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma))) = 0 THEN 0
                    ELSE ABS(SQRT(
                        POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2) +
                        POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2)
                    ) / (julianday(p.hora_prisma) - julianday(FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma))))
                END AS VA2D,
                CASE
                    WHEN CAST(julianday(p.hora_prisma) - julianday(COALESCE(LAG(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma)) AS NUMERIC) = 0 THEN 0
                    ELSE ABS((
                        (p.distancia_prisma - LAG(p.distancia_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma))
                    ) / CAST(julianday(p.hora_prisma) - julianday(COALESCE(LAG(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma)) AS NUMERIC))
                END AS VISD,
                CASE
                    WHEN CAST(julianday(p.hora_prisma) - julianday(FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma)) AS NUMERIC) = 0 THEN 0
                    ELSE ABS((
                        (p.distancia_prisma - FIRST_VALUE(p.distancia_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma))
                    ) / CAST(julianday(p.hora_prisma) - julianday(FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma)) AS NUMERIC))
                END AS VASD
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND i.estado_instrumentacion = 1 AND p.hora_prisma BETWEEN ? AND ?
        )
        SELECT nombre_prisma, MIN(hora_prisma) AS fechamin, MAX(hora_prisma) AS fechamax, MAX(VI3D) AS VI3D, MAX(VA3D) AS VA3D,
        MAX(VI2D) AS VI2D, MAX(VA2D) AS VA2D, MAX(VISD) AS VISD, MAX(VASD) AS VASD
        FROM ResumenVelocidad
        GROUP BY nombre_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (fechaini, fechafin))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al obtener resumen prismas velocidad: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlResumenTrendPlunge(tabla, fechaini, fechafin):
        sql = f"""WITH ResumenTrendplunge AS (
            SELECT p.nombre_prisma, p.hora_prisma,
                p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma) AS desplaza_este,
                p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma) AS desplaza_norte,
                p.elevacion_target - FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma) AS desplaza_elevacion
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND i.estado_instrumentacion = 1 AND p.hora_prisma BETWEEN ? AND ?
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
        SELECT trend, plunge FROM RankedCD WHERE RowAsc = 1;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (fechaini, fechafin))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al obtener resumen prismas trend plunge: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlCalcularVectoresDesplazamiento3DA(tabla, prismas, idcomponente):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente]
        sql = f"""WITH ultimas_lecturas AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma,
                CAST(julianday(p.hora_prisma) - julianday(FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) AS NUMERIC) * 24 AS horas,
                CAST(julianday(p.hora_prisma) - julianday(FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) AS NUMERIC) AS dias,
                SQRT(
                    POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.elevacion_target - FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                ) AS tresD,
                ROW_NUMBER() OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma DESC) AS rn
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma, horas, dias, tresD
        FROM ultimas_lecturas WHERE rn = 1;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar vectores D3D: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlCalcularVectoresDesplazamientoFechas3DA(tabla, prismas, idcomponente, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        sql = f"""WITH ultimas_lecturas AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma,
                CAST(julianday(p.hora_prisma) - julianday(FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) AS NUMERIC) * 24 AS horas,
                CAST(julianday(p.hora_prisma) - julianday(FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma)) AS NUMERIC) AS dias,
                SQRT(
                    POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2) +
                    POWER(p.elevacion_target - FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), 2)
                ) AS tresD,
                ROW_NUMBER() OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma DESC) AS rn
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders})
            AND i.id_componente = ? AND p.hora_prisma BETWEEN ? AND ?
        )
        SELECT id_instrumentacion, nombre_prisma, hora_prisma, horas, dias, tresD
        FROM ultimas_lecturas WHERE rn = 1;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar vectores D3D Fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlCalcularVectoresVelocidadPositivaVI3D(tabla, prismas, idcomponente):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente]
        sql = f"""WITH PrismasCTE AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, p.elevacion_target,
                CAST(
                    julianday(p.hora_prisma) - julianday(FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma)) AS NUMERIC
                ) AS dias,		
                SQRT(
                    POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2) +
                    POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2) +
                    POWER(p.elevacion_target - FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2)
                ) AS tresD
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            ORDER BY p.nombre_prisma, p.hora_prisma
        ),
        CalculoCompleto AS (
            SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24 AS HORAS,
            CASE 
                WHEN COALESCE(LAG(julianday(hora_prisma)) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma, hora_prisma), 0) = 0 THEN 0
                ELSE tresD / (julianday(hora_prisma) - LAG(julianday(hora_prisma)) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma, hora_prisma))
            END AS VI3D
            FROM PrismasCTE
        )
        SELECT c.* FROM CalculoCompleto c INNER JOIN (SELECT nombre_prisma, MAX(FECHAS) AS ultima_fecha FROM CalculoCompleto GROUP BY nombre_prisma) ultimas
        ON c.nombre_prisma = ultimas.nombre_prisma AND c.FECHAS = ultimas.ultima_fecha;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar vectores vi3d positiva: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlCalcularVectoresVelocidadPositivaFechasVI3D(tabla, prismas, idcomponente, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        sql = f"""WITH PrismasCTE AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, p.elevacion_target,
                CAST(
                    julianday(p.hora_prisma) - julianday(FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma)) AS NUMERIC
                ) AS dias,		
                SQRT(
                    POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2) +
                    POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2) +
                    POWER(p.elevacion_target - FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2)
                ) AS tresD
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? ORDER BY p.nombre_prisma, p.hora_prisma
        ),
        CalculoCompleto AS (
            SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24 AS HORAS,
            CASE 
                WHEN COALESCE(LAG(julianday(hora_prisma)) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma, hora_prisma), 0) = 0 THEN 0
                ELSE tresD / (julianday(hora_prisma) - LAG(julianday(hora_prisma)) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma, hora_prisma))
            END AS VI3D
            FROM PrismasCTE
        )
        SELECT c.* FROM CalculoCompleto c INNER JOIN (SELECT nombre_prisma, MAX(FECHAS) AS ultima_fecha FROM CalculoCompleto GROUP BY nombre_prisma) ultimas
        ON c.nombre_prisma = ultimas.nombre_prisma AND c.FECHAS = ultimas.ultima_fecha;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar vectores vi3d positiva fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlCalcularVectoresVelocidadVI3D(tabla, prismas, idcomponente):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente]
        sql = f"""WITH PrismasCTE AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, p.elevacion_target,
                CAST(
                    julianday(p.hora_prisma) - julianday(FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma)) AS NUMERIC
                ) AS dias,		
                SQRT(
                    POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2) +
                    POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2) +
                    POWER(p.elevacion_target - FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2)
                ) AS tresD
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            ORDER BY p.nombre_prisma, p.hora_prisma
        ),
        CalculoCompleto AS (
            SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24 AS HORAS,
            CASE 
                WHEN COALESCE(LAG(julianday(hora_prisma)) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma, hora_prisma), 0) = 0 THEN 0
                ELSE (tresD - LAG(tresD) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma, hora_prisma))
                    / (julianday(hora_prisma) - LAG(julianday(hora_prisma)) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma, hora_prisma))
            END AS VI3D
            FROM PrismasCTE
        )
        SELECT c.* FROM CalculoCompleto c INNER JOIN (SELECT nombre_prisma, MAX(FECHAS) AS ultima_fecha FROM CalculoCompleto GROUP BY nombre_prisma) ultimas
        ON c.nombre_prisma = ultimas.nombre_prisma AND c.FECHAS = ultimas.ultima_fecha;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar vectores vi3d: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlCalcularVectoresVelocidadFechasVI3D(tabla, prismas, idcomponente, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        sql = f"""WITH PrismasCTE AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, p.elevacion_target,
                CAST(
                    julianday(p.hora_prisma) - julianday(FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma)) AS NUMERIC
                ) AS dias,		
                SQRT(
                    POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2) +
                    POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2) +
                    POWER(p.elevacion_target - FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2)
                ) AS tresD
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
            AND p.hora_prisma BETWEEN ? AND ? ORDER BY p.nombre_prisma, p.hora_prisma
        ),
        CalculoCompleto AS (
            SELECT id_instrumentacion, nombre_prisma, hora_prisma AS FECHAS, dias AS DIAS, dias * 24 AS HORAS,
            CASE 
                WHEN COALESCE(LAG(julianday(hora_prisma)) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma, hora_prisma), 0) = 0 THEN 0
                ELSE (tresD - LAG(tresD) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma, hora_prisma))
                    / (julianday(hora_prisma) - LAG(julianday(hora_prisma)) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma, hora_prisma))
            END AS VI3D
            FROM PrismasCTE
        )
        SELECT c.* FROM CalculoCompleto c INNER JOIN (SELECT nombre_prisma, MAX(FECHAS) AS ultima_fecha FROM CalculoCompleto GROUP BY nombre_prisma) ultimas
        ON c.nombre_prisma = ultimas.nombre_prisma AND c.FECHAS = ultimas.ultima_fecha;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar vectores vi3d fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
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
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (prisma,))
            results = cur.fetchall()
            if results:
                return results
            else:
                return None
        except Error as e:
            print("Error al obtener data prismas desviaciones:", e)
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlObtenerDesviacionStandar(idproyecto, nombreprisma):
        sql = """SELECT * FROM desviaciones WHERE id_proyecto = ? AND nombre_prisma = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idproyecto, nombreprisma))
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al obtener desviacion estandar: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
                
    def mdlOmitirLecturaPrisma(tabla,prisma,fecha):
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            query_update = f"""UPDATE {tabla} SET estado_prisma = 0 WHERE nombre_prisma = ? AND hora_prisma=?;"""
            cursor.execute(query_update, (prisma,fecha))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al omitir lecturas del prisma: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlVerificarPrismaUnico(nameprisma, idinstrumento, idproyecto):
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            query = """SELECT 1 FROM instrumentacion i INNER JOIN componentes c ON i.id_componente = c.id_componente
            WHERE LOWER(i.nombre_equipo) = LOWER(?) AND i.id_instrumentacion != ? 
            AND c.id_proyecto = ? AND i.tipo_equipo = 'PRISMAS' LIMIT 1;"""
            cursor.execute(query, (nameprisma, idinstrumento, idproyecto))
            resultado = cursor.fetchone()
            return bool(resultado)
        except Exception as e:
            print(f"Error al comprobar nombres del prisma: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlActualizarNombrePrisma(nameprisma, nuevoprisma, idinstrumento, idproyecto):
        tabla = f"prismas{idproyecto}"
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # Iniciar transacción explícita
            cursor.execute("BEGIN TRANSACTION")
            # Actualizar tabla dinámica de prismas
            query_update_prisma = f"""UPDATE {tabla} SET nombre_prisma = ? WHERE nombre_prisma = ?"""
            cursor.execute(query_update_prisma, (nuevoprisma, nameprisma))
            filas_prisma = cursor.rowcount
            # Actualizar tabla instrumentacion
            query_update_instrumento = """UPDATE instrumentacion SET nombre_equipo = ? WHERE id_instrumentacion = ?"""
            cursor.execute(query_update_instrumento, (nuevoprisma, idinstrumento))
            filas_instrumento = cursor.rowcount
            # Validar que ambas actualizaciones fueron exitosas
            if filas_prisma == 0:
                cursor.execute("ROLLBACK")
                print(f"No se encontró el prisma '{nameprisma}' para actualizar")
                return False
            if filas_instrumento == 0:
                cursor.execute("ROLLBACK")
                print(f"No se pudo actualizar el instrumento con ID {idinstrumento}")
                return False
            # Confirmar transacción
            conn.commit()
            return True
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            print(f"Error al actualizar nombre del prisma: {e}")
            return False
        finally:
            if conn:
                conn.close()
    