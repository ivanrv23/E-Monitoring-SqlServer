from services.security.apis.conexiones.connection import Connection
from datetime import datetime

class PrismaModel:
    
    # limpiar tabla BD
    # DELETE FROM prismas;
    # DELETE FROM sqlite_sequence WHERE name='prismas';

    @staticmethod
    def mdlObtenerFechasMaximasPrismas(tabla):
        sql = f"""SELECT MAX(hora_prisma) AS max_fecha FROM {tabla} WHERE state_prisma = 1;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener fechas max prismas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlListarDataPrismasNombre(table, nombres):
        placeholders = ', '.join(['?' for _ in nombres])  # Crear placeholders para los nombres
        sql = f"""SELECT nombre_prisma, estado_prisma, perfil_prisma, hora_prisma, angulo_horizontal, angulo_vertical, distancia_prisma, tipoppm_prisma, ppm_prisma, 
            presion_prisma, temperatura_prisma, constante_prisma, este_target, norte_target, elevacion_target, altura_reflector, altura_instrumento, este_estacion, 
            norte_estacion, altura_estacion, medicion_prisma, diferencia_tiempocorto, diferencia_tiempolargo, diferencia_limitevelocidad, distancia_horizontal, 
            diferencia_atipica, desplaza_longitudinal, desplaza_transversal, desplaza_altura, grupo_puntos FROM {table} WHERE state_prisma = 1 
            AND nombre_prisma IN ({placeholders}) ORDER BY nombre_prisma, hora_prisma;"""  # Utilizar placeholders en la consulta
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, nombres)  # Pasar nombres como parámetros
            rows = cur.fetchall()
            return rows  # Devolver todas las filas encontradas
        except Exception as e:
            print("Error al listar prismas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlListarDataPrismasNombre_manuales(table, nombres):
        placeholders = ', '.join(['?' for _ in nombres])  # Crear placeholders para los nombres
        sql = f"""SELECT nombre_prisma, hora_prisma, norte_target, este_target, elevacion_target, angulo_horizontal, angulo_vertical, distancia_prisma
        FROM {table} WHERE state_prisma = 1 AND nombre_prisma IN ({placeholders}) ORDER BY nombre_prisma, hora_prisma;"""  # Utilizar placeholders en la consulta
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, nombres)  # Pasar nombres como parámetros
            rows = cur.fetchall()
            return rows  # Devolver todas las filas encontradas
        except Exception as e:
            print("Error al listar prismas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlResumenPrismaNombre(tabla, nombres, fechaini, fechafin, tipo_prisma):
        nombres_str = ','.join(['?' for _ in nombres])  # Creamos una cadena de comodines para los nombres
        # SQL Server: DATEDIFF para dias
        sql = f"""SELECT nombre_prisma, tipo, MIN(hora) AS fecha_minima, MAX(hora) AS fecha_maxima, COUNT(*) AS cantidad,
            DATEDIFF(DAY, MIN(hora), MAX(hora)) + 1 as total_dias
        FROM (
            SELECT nombre_prisma, '{tipo_prisma}' AS tipo, hora_prisma AS hora FROM {tabla} WHERE state_prisma = 1
            AND nombre_prisma IN ({nombres_str}) AND hora_prisma BETWEEN ? AND ?
        ) AS subquery GROUP BY nombre_prisma, tipo;""" # Agregado 'AS subquery' y 'tipo' al GROUP BY

        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # Agregamos los nombres y los límites de fecha a los parámetros de la consulta
            cur.execute(sql, tuple(nombres) + (fechaini, fechafin))
            rows = cur.fetchall()
            return rows
        except Exception as e:
            print("Error al consultar Resumen prisma: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    # obtener fecha mini y maximo de los prismas automatizados
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
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener fechas min-max: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # obtener fecha mini y maximo de los prismas manuales
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
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener fechas min-max: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # MOSTRAR LISTA DE PRISMAS AUTO INICIALES SIN REPETIRSE
    @staticmethod
    def mdlListarPrismasUnicosMinima(tabla, prismas, idcomponente):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente]
        # SQL Server: Group By estricto
        sql = f"""SELECT i.id_instrumentacion, i.nombre_equipo, p.este_target, p.norte_target, p.elevacion_target, i.id_componente,
        i.tipo_equipo, MIN(hora_prisma) AS hora FROM {tabla} p INNER JOIN instrumentacion i
        ON p.nombre_prisma = i.nombre_equipo WHERE p.state_prisma = 1 AND p.estado_prisma = 1
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        GROUP BY p.nombre_prisma, i.id_instrumentacion, i.nombre_equipo, p.este_target, p.norte_target, p.elevacion_target, i.id_componente, i.tipo_equipo
        ORDER BY p.nombre_prisma, MIN(hora_prisma);""" # Order by agregado
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al listar prismas ini: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # MOSTRAR LISTA DE PRISMAS AUTO INICIALES SIN REPETIRSE POR FECHA
    @staticmethod
    def mdlListarPrismasUnicosFechaMinima(tabla, prismas, idcomponente, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        sql = f"""SELECT i.id_instrumentacion, i.nombre_equipo, p.este_target, p.norte_target, p.elevacion_target, i.id_componente,
        i.tipo_equipo, MIN(hora_prisma) AS hora FROM {tabla} p INNER JOIN instrumentacion i
        ON p.nombre_prisma = i.nombre_equipo WHERE p.state_prisma = 1 AND p.estado_prisma = 1
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        AND p.hora_prisma BETWEEN ? AND ? 
        GROUP BY p.nombre_prisma, i.id_instrumentacion, i.nombre_equipo, p.este_target, p.norte_target, p.elevacion_target, i.id_componente, i.tipo_equipo
        ORDER BY p.nombre_prisma, MIN(hora_prisma);"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al listar prismas ini fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # MOSTRAR LISTA DE PRISMAS INICIALES AUTOMATIZADOS SIN REPETIRSE POR FECHAS            
    @staticmethod
    def mdlTraerPrismasInicialesProyectoFecha(proyecto, fechaini, fechafin):
        tabla = "prismas" + str(proyecto)
        # SQL Server: No permite SELECT * con GROUP BY sin agregar todas las columnas.
        # Solución: Usar subconsulta con ROW_NUMBER() para obtener el primer registro por grupo.
        sql = f"""
        SELECT t.*, t.id_prisma 
        FROM (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY id_prisma ASC) as rn 
            FROM {tabla} 
            WHERE state_prisma = 1 AND hora_prisma BETWEEN ? AND ?
        ) t
        WHERE t.rn = 1;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (fechaini, fechafin))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al listar prismas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # MOSTRAR LISTA DE PRISMAS INICIALES MANUALES SIN REPETIRSE POR FECHAS            
    @staticmethod
    def mdlPrismasManualesInicialesProyectoFecha(proyecto, fechaini, fechafin):
        tabla = "prismas" + str(proyecto)
        # Igual que el anterior, usar ROW_NUMBER
        sql = f"""
        SELECT t.*, t.id_prisma 
        FROM (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY id_prisma ASC) as rn 
            FROM {tabla} 
            WHERE state_prisma = 1 AND hora_prisma BETWEEN ? AND ?
        ) t
        WHERE t.rn = 1;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (fechaini, fechafin))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al listar prismas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # MOSTRAR PRISMA INICIAL AUTOMATIZADO POR NOMBRE Y FECHAS            
    @staticmethod
    def mdlTraerPrismaInicialProyectoNombreFecha(proyecto, nombre, fechaini, fechafin):
        tabla = "prismas" + str(proyecto)
        # Usar TOP 1 en lugar de MIN(id) con *
        sql = f"""SELECT TOP 1 *, id_prisma FROM {tabla} WHERE state_prisma = 1 AND nombre_prisma = ? AND hora_prisma BETWEEN ? AND ? ORDER BY id_prisma ASC;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (nombre, fechaini, fechafin))
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al listar prismas por fecha: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # MOSTRAR LISTA DE PRISMAS FINALES AUTOMATIZADOS SIN REPETIRSE POR FECHAS   
    @staticmethod
    def mdlTraerPrismasFinalesProyectoFecha(proyecto, fechaini, fechafin):
        tabla = "prismas" + str(proyecto)
        # ROW_NUMBER DESC para obtener el último
        sql = f"""
        SELECT t.*, t.id_prisma 
        FROM (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY id_prisma DESC) as rn 
            FROM {tabla} 
            WHERE state_prisma = 1 AND hora_prisma BETWEEN ? AND ?
        ) t
        WHERE t.rn = 1;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (fechaini, fechafin))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al listar prismas: " + str(e))
            return None
        finally:
            if conn:
                conn.close() 
    
    # MOSTRAR LISTA DE PRISMAS FINALES MANUALES SIN REPETIRSE POR FECHAS   
    @staticmethod
    def mdlPrismasManualesFinalesProyectoFecha(proyecto, fechaini, fechafin):
        tabla = "prismas" + str(proyecto)
        # ROW_NUMBER DESC
        sql = f"""
        SELECT t.*, t.id_prisma 
        FROM (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY id_prisma DESC) as rn 
            FROM {tabla} 
            WHERE state_prisma = 1 AND hora_prisma BETWEEN ? AND ?
        ) t
        WHERE t.rn = 1;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (fechaini, fechafin))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al listar prismas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()  
    
    # MOSTRAR PRISMA FINAL AUTOMATIZADO
    @staticmethod
    def mdlListarPrismasUnicosMaxima(tabla, prismas, idcomponente):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente]
        sql = f"""SELECT i.id_instrumentacion, i.nombre_equipo, p.este_target, p.norte_target, p.elevacion_target, i.id_componente,
        i.tipo_equipo, MAX(hora_prisma) AS hora FROM {tabla} p INNER JOIN instrumentacion i
        ON p.nombre_prisma = i.nombre_equipo WHERE p.state_prisma = 1 AND p.estado_prisma = 1
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        GROUP BY p.nombre_prisma, i.id_instrumentacion, i.nombre_equipo, p.este_target, p.norte_target, p.elevacion_target, i.id_componente, i.tipo_equipo
        ORDER BY p.nombre_prisma, MAX(hora_prisma);"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al listar prismas max: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # MOSTRAR PRISMA FINAL AUTOMATIZADO POR FECHAS            
    @staticmethod
    def mdlListarPrismasUnicosFechaMaxima(tabla, prismas, idcomponente, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        sql = f"""SELECT i.id_instrumentacion, i.nombre_equipo, p.este_target, p.norte_target, p.elevacion_target, i.id_componente,
        i.tipo_equipo, MAX(hora_prisma) AS hora FROM {tabla} p INNER JOIN instrumentacion i
        ON p.nombre_prisma = i.nombre_equipo WHERE p.state_prisma = 1 AND p.estado_prisma = 1
        AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?
        AND p.hora_prisma BETWEEN ? AND ? 
        GROUP BY p.nombre_prisma, i.id_instrumentacion, i.nombre_equipo, p.este_target, p.norte_target, p.elevacion_target, i.id_componente, i.tipo_equipo
        ORDER BY p.nombre_prisma, MAX(hora_prisma);"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al listar prismas max fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # MOSTRAR PRISMA INICIAL MANUAL FECHAS            
    @staticmethod
    def mdlListarPrismasFechaMinimaUnicos(tabla, proyecto, fechaini, fechafin, tipo):
        sql = f"""SELECT i.id_instrumentacion, i.nombre_equipo, p.este_target, p.norte_target, p.elevacion_target, c.id_componente,
        i.tipo_equipo, MIN(hora_prisma) AS hora FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
        INNER JOIN componentes c ON i.id_componente = c.id_componente WHERE p.state_prisma = 1 AND hora_prisma BETWEEN ? AND ?
        AND c.id_proyecto = ? AND i.tipo_equipo = ? 
        GROUP BY p.nombre_prisma, i.id_instrumentacion, i.nombre_equipo, p.este_target, p.norte_target, p.elevacion_target, c.id_componente, i.tipo_equipo;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (fechaini, fechafin, proyecto, tipo))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al listar prismas minima: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # ACTUALIZAR EL ESTADO DEL PRISMA           
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
            if conn:
                conn.close()
    
    # ELIMINAR EL PRISMA           
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
            if conn:
                conn.close() 
    
    # MOSTRAR LISTA DE PRISMAS INICIALES MANUALES SIN REPETIRSE POR PROYECTO            
    @staticmethod
    def mdlListarPrismasManualesProyecto(proyecto):
        tabla = "prismas" + str(proyecto)
        # Usar ROW_NUMBER para obtener el primero de cada grupo
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
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al listar nombre prismas manual: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # AGREGAR PRISMAS MANUALES DESDE LA TABLA   
    @staticmethod
    def mdlGuardarPrismasManualesTabla(proyecto, data):
        conn = None
        try:
            conn = Connection.connectionDB()
            nombretabla = "prismas" + str(proyecto)
            cursor = conn.cursor()
            
            # SQL Server syntax
            sqltable = f"""
            IF OBJECT_ID('{nombretabla}', 'U') IS NULL
            BEGIN
                CREATE TABLE {nombretabla} (
                    id_prisma INT IDENTITY(1,1) PRIMARY KEY,
                    state_prisma INT NOT NULL DEFAULT 1,
                    estado_prisma INT NOT NULL DEFAULT 1, 
                    nombre_prisma NVARCHAR(255) NOT NULL, 
                    perfil_prisma NVARCHAR(255), 
                    hora_prisma DATETIME NOT NULL, 
                    angulo_horizontal NVARCHAR(255), 
                    angulo_vertical NVARCHAR(255), 
                    distancia_prisma DECIMAL(18,5) DEFAULT 0, 
                    tipoppm_prisma NVARCHAR(255), 
                    ppm_prisma DECIMAL(18,5) DEFAULT 0, 
                    presion_prisma DECIMAL(18,5) DEFAULT 0, 
                    temperatura_prisma DECIMAL(18,5) DEFAULT 0, 
                    constante_prisma DECIMAL(18,5) DEFAULT 0, 
                    este_target DECIMAL(18,5) NOT NULL, 
                    norte_target DECIMAL(18,5) NOT NULL, 
                    elevacion_target DECIMAL(18,5) NOT NULL, 
                    altura_reflector DECIMAL(18,5) DEFAULT 0, 
                    altura_instrumento DECIMAL(18,5) DEFAULT 0, 
                    este_estacion DECIMAL(18,5) DEFAULT 0, 
                    norte_estacion DECIMAL(18,5) DEFAULT 0, 
                    altura_estacion DECIMAL(18,5) DEFAULT 0, 
                    medicion_prisma DECIMAL(18,5) DEFAULT 0, 
                    diferencia_tiempocorto DECIMAL(18,5) DEFAULT 0,
                    diferencia_tiempolargo DECIMAL(18,5) DEFAULT 0, 
                    diferencia_limitevelocidad DECIMAL(18,5) DEFAULT 0, 
                    distancia_horizontal DECIMAL(18,5) DEFAULT 0, 
                    diferencia_atipica DECIMAL(18,5) DEFAULT 0, 
                    desplaza_longitudinal DECIMAL(18,5) DEFAULT 0, 
                    desplaza_transversal DECIMAL(18,5) DEFAULT 0, 
                    desplaza_altura DECIMAL(18,5) DEFAULT 0, 
                    grupo_puntos NVARCHAR(255)
                );
            END"""
            
            cursor.execute(sqltable)
            
            # Obtener existentes
            # SQL Server datetime format can be tricky, assuming standard ISO
            cursor.execute(f"SELECT nombre_prisma, FORMAT(hora_prisma, 'yyyy-MM-dd HH:mm:ss') FROM {nombretabla}")
            existen_prismas = set([(row[0], row[1]) for row in cursor.fetchall()])
            
            lote_registros = []
            
            for fila in data:
                fecha_original = fila[1] # se asume YYYY-MM-DD
                hora_original = fila[2]  # se asume HH:MM:SS
                
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
            
            if lote_registros:
                # Batch insert
                chunk_size = 1000
                insert_query = f"""INSERT INTO {nombretabla} (state_prisma, estado_prisma, nombre_prisma, hora_prisma, distancia_prisma, este_target,
                    norte_target, elevacion_target, angulo_horizontal, angulo_vertical) VALUES (1, 1, ?, ?, ?, ?, ?, ?, ?, ?)"""
                
                for i in range(0, len(lote_registros), chunk_size):
                    chunk = lote_registros[i:i + chunk_size]
                    cursor.executemany(insert_query, chunk)
            
            conn.commit()
            return True
        except Exception as e:
            if conn:
                conn.rollback()
            print("Error al guardar los prismas de la tabla " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    # LISTAR LA DATA DE LOS PRISMAS POR PROYECTO                  
    @staticmethod
    def mdlListarDataPrismasProyecto(proyecto, fechaini, fechafin):
        table = "prismas" + str(proyecto)
        conn = None
        try:
            conn = Connection.connectionDB()
            # Uso de parametros para evitar inyeccion SQL
            sql = f"""SELECT * FROM {table} WHERE state_prisma = '1' AND hora_prisma BETWEEN ? AND ?;"""
            
            cur = conn.cursor()
            cur.execute(sql, (fechaini, fechafin))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al listar prismas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # MOSTRAR DATA DE PRISMAS MANUALES POR FECHAS            
    @staticmethod
    def mdlTraerDataPrismasManualesFecha(proyecto, fechaini, fechafin):
        tabla = "prismas" + str(proyecto)
        # SQL Server: DATEDIFF en lugar de JULIANDAY. ATAN es ATN. POW es POWER.
        sql = f"""WITH prismasmanuales AS (
            SELECT 
                id_prisma, nombre_prisma, state_prisma, hora_prisma, 
                COALESCE(CAST(DATEDIFF(SECOND, LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), hora_prisma) / 86400.0 AS DECIMAL(18,5)), 0) AS dias,
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
            FROM {tabla} 
            WHERE state_prisma = '1' AND hora_prisma BETWEEN ? AND ?
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
                WHEN danorte > 0 AND daeste > 0 THEN 90 - (180 / PI()) * ATN(danorte / daeste)
                WHEN danorte < 0 AND daeste > 0 THEN 90 - (180 / PI()) * ATN(danorte / daeste)
                WHEN danorte < 0 AND daeste < 0 THEN 270 - (180 / PI()) * ATN(danorte / daeste)
                WHEN danorte > 0 AND daeste < 0 THEN 270 - (180 / PI()) * ATN(danorte / daeste)
            END AS trend, 
            CASE WHEN magnitudNE = 0 THEN 0 ELSE ((180 / PI()) * ATN(danivel / magnitudNE)) END AS plunge
        FROM prismasmanuales;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (fechaini, fechafin))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al listar prismas manuales: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
                
    # MOSTRAR LISTA DE PRISMAS INICIALES AUTOMATIZADOS SIN REPETIRSE POR PROYECTO            
    @staticmethod
    def mdlListarPrismasProyecto(proyecto):
        tabla = "prismas" + str(proyecto)
        # SQL Server: ROW_NUMBER para obtener unico
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
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al listar nombre prismas auto: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # LISTAR LOS PRISMAS AUTO CON COORDENADAS INICIALES Y FINALES           
    @staticmethod
    def mdlObtenerInfoPrismasAutoJSONproyecto(proyecto):
        tabla = "prismas" + str(proyecto)
        # SQL Server: TOP 1 en subconsultas
        sql = f"""SELECT
            nombre_prisma,
            (SELECT TOP 1 este_target FROM {tabla} AS sub WHERE sub.nombre_prisma = p.nombre_prisma AND sub.state_prisma = '1' 
            ORDER BY sub.hora_prisma ASC) AS este_inicial,
            (SELECT TOP 1 norte_target FROM {tabla} AS sub WHERE sub.nombre_prisma = p.nombre_prisma AND sub.state_prisma = '1' 
            ORDER BY sub.hora_prisma ASC) AS norte_inicial,
            (SELECT TOP 1 elevacion_target FROM {tabla} AS sub WHERE sub.nombre_prisma = p.nombre_prisma AND sub.state_prisma = '1' 
            ORDER BY sub.hora_prisma ASC) AS nivel_inicial,
            (SELECT TOP 1 este_target FROM {tabla} AS sub WHERE sub.nombre_prisma = p.nombre_prisma AND sub.state_prisma = '1' 
            ORDER BY sub.hora_prisma DESC) AS este_final,
            (SELECT TOP 1 norte_target FROM {tabla} AS sub WHERE sub.nombre_prisma = p.nombre_prisma AND sub.state_prisma = '1' 
            ORDER BY sub.hora_prisma DESC) AS norte_final,
            (SELECT TOP 1 elevacion_target FROM {tabla} AS sub WHERE sub.nombre_prisma = p.nombre_prisma AND sub.state_prisma = '1' 
            ORDER BY sub.hora_prisma DESC) AS nivel_final
        FROM
            {tabla} p
        WHERE
            state_prisma = '1'
        GROUP BY
            nombre_prisma
        ORDER BY
            nombre_prisma;""" # Order by columna valida
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al listar info prismas auto json: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # LISTAR LOS PRISMAS MANUALES CON COORDENADAS INICIALES Y FINALES           
    @staticmethod
    def mdlObtenerInfoPrismasManualJSONproyecto(proyecto):
        tabla = "prismas" + str(proyecto)
        # SQL Server: TOP 1
        sql = f"""SELECT
            nombre_prisma,
            (SELECT TOP 1 este_target FROM {tabla} AS sub WHERE sub.nombre_prisma = p.nombre_prisma AND sub.state_prisma = '1' 
            ORDER BY sub.hora_prisma ASC) AS este_inicial,
            (SELECT TOP 1 norte_target FROM {tabla} AS sub WHERE sub.nombre_prisma = p.nombre_prisma AND sub.state_prisma = '1' 
            ORDER BY sub.hora_prisma ASC) AS norte_inicial,
            (SELECT TOP 1 elevacion_target FROM {tabla} AS sub WHERE sub.nombre_prisma = p.nombre_prisma AND sub.state_prisma = '1' 
            ORDER BY sub.hora_prisma ASC) AS nivel_inicial,
            (SELECT TOP 1 este_target FROM {tabla} AS sub WHERE sub.nombre_prisma = p.nombre_prisma AND sub.state_prisma = '1' 
            ORDER BY sub.hora_prisma DESC) AS este_final,
            (SELECT TOP 1 norte_target FROM {tabla} AS sub WHERE sub.nombre_prisma = p.nombre_prisma AND sub.state_prisma = '1' 
            ORDER BY sub.hora_prisma DESC) AS norte_final,
            (SELECT TOP 1 elevacion_target FROM {tabla} AS sub WHERE sub.nombre_prisma = p.nombre_prisma AND sub.state_prisma = '1' 
            ORDER BY sub.hora_prisma DESC) AS nivel_final
        FROM
            {tabla} p
        WHERE
            state_prisma = '1'
        GROUP BY
            nombre_prisma
        ORDER BY
            nombre_prisma;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al listar info prismas manual json: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
           
    @staticmethod
    def mdlActualizarLecturaPrisma(tabla, datanueva, idproyecto, username, nombres):
        query_select = f"""SELECT hora_prisma, este_target, norte_target, elevacion_target, distancia_prisma, id_prisma
        FROM {tabla} WHERE id_prisma = ?;"""
        conn = None
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
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCambiarEstadoLecturaPrisma(tabla, iddetalle):
        conn = None
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
    
    @staticmethod
    def mdlOmitirLecturasPrismaDesviacion(tabla, prisma, desviacioneste, desviacionnorte):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # SQL Server: FIRST_VALUE OK.
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
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCambiarEstadoLecturaPrismaBloque(tabla, listacodigos):
        conn = None
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
    
    @staticmethod
    def mdlEliminarLecturaPrisma(tabla, iddetalle, idproyecto, username, nombres):
        conn = None
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
    
    @staticmethod
    def mdlEliminarLecturasBloquePrisma(tabla, iddetalles, idproyecto, username, nombres):
        placeholders = ', '.join(['?' for _ in iddetalles])
        conn = None
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
            if conn:
                conn.close()
    
    @staticmethod
    def mdlEliminarPrismas(idcomponente):
        conn = None
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
    
    @staticmethod
    def mdlEliminarDataPrismas(tabla, prismas):
        placeholders = ', '.join(['?' for _ in prismas])
        conn = None
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
            if conn:
                conn.close()
    
    @staticmethod
    def mdlEliminarPrismaUnico(idinstrumento):
        conn = None
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
    
    @staticmethod
    def mdlEliminarPrismaData(tabla, nombreprisma):
        conn = None
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
            if conn:
                conn.close()
    
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
            if conn:
                conn.close()
    
    @staticmethod
    def mdlResumenDesplazamiento(tabla, fechaini, fechafin):
        # SQL Server Group By:
        # En la CTE calculamos los datos brutos. Luego agrupamos.
        # ABS en SQL server es compatible.
        # POWER es compatible.
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
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (fechaini, fechafin))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener resumen prismas desplazamiento: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlResumenVelocidad(tabla, fechaini, fechafin):
        # SQL Server: DATEDIFF(SECOND, ...) / 86400.0 para decimales de dias.
        # COALESCE es compatible.
        sql = f"""WITH ResumenVelocidad AS (
            SELECT p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, p.elevacion_target,
                CASE 
                    WHEN COALESCE(DATEDIFF(SECOND, LAG(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) / 86400.0, 0) = 0 THEN 0
                    ELSE ABS(SQRT(
                        POWER(p.este_target - LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2) +
                        POWER(p.norte_target - LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2) +
                        POWER(p.elevacion_target - LAG(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2)
                    ) / (DATEDIFF(SECOND, LAG(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) / 86400.0))
                END AS VI3D,
                CASE 
                    WHEN (DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) / 86400.0) = 0 THEN 0
                    ELSE ABS(SQRT(
                        POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2) +
                        POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2) +
                        POWER(p.elevacion_target - FIRST_VALUE(p.elevacion_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2)
                    ) / (DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) / 86400.0))
                END AS VA3D,
                CASE 
                    WHEN COALESCE(DATEDIFF(SECOND, LAG(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) / 86400.0, 0) = 0 THEN 0
                    ELSE ABS(SQRT(
                        POWER(p.este_target - LAG(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2) +
                        POWER(p.norte_target - LAG(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2)
                    ) / (DATEDIFF(SECOND, LAG(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) / 86400.0))
                END AS VI2D,
                CASE 
                    WHEN (DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) / 86400.0) = 0 THEN 0
                    ELSE ABS(SQRT(
                        POWER(p.este_target - FIRST_VALUE(p.este_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2) +
                        POWER(p.norte_target - FIRST_VALUE(p.norte_target) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), 2)
                    ) / (DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) / 86400.0))
                END AS VA2D,
                CASE
                    WHEN CAST(DATEDIFF(SECOND, COALESCE(LAG(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma), p.hora_prisma) / 86400.0 AS DECIMAL(18,5)) = 0 THEN 0
                    ELSE ABS((
                        (p.distancia_prisma - LAG(p.distancia_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma))
                    ) / CAST(DATEDIFF(SECOND, COALESCE(LAG(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma), p.hora_prisma) / 86400.0 AS DECIMAL(18,5)))
                END AS VISD,
                CASE
                    WHEN CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) / 86400.0 AS DECIMAL(18,5)) = 0 THEN 0
                    ELSE ABS((
                        (p.distancia_prisma - FIRST_VALUE(p.distancia_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma))
                    ) / CAST(DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) / 86400.0 AS DECIMAL(18,5)))
                END AS VASD
            FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo
            WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND i.estado_instrumentacion = 1 AND p.hora_prisma BETWEEN ? AND ?
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
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener resumen prismas velocidad: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlResumenTrendPlunge(tabla, fechaini, fechafin):
        # SQL Server: ATAN -> ATN.
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
                    WHEN desplaza_este > 0 THEN 90 - DEGREES(ATN(desplaza_norte / desplaza_este))
                    WHEN desplaza_este < 0 THEN 270 - DEGREES(ATN(desplaza_norte / desplaza_este))
                END AS trend,
                CASE
                    WHEN magnitud IS NULL OR desplaza_elevacion IS NULL THEN NULL
                    WHEN magnitud != 0 THEN DEGREES(ATN(desplaza_elevacion / magnitud))
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
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener resumen prismas trend plunge: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVectoresDesplazamiento3DA(tabla, prismas, idcomponente):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente]
        sql = f"""WITH ultimas_lecturas AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma,
                (DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) / 86400.0) * 24.0 AS horas,
                (DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) / 86400.0) AS dias,
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
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al consultar vectores D3D: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVectoresDesplazamientoFechas3DA(tabla, prismas, idcomponente, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        sql = f"""WITH ultimas_lecturas AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma,
                (DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) / 86400.0) * 24.0 AS horas,
                (DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.hora_prisma), p.hora_prisma) / 86400.0) AS dias,
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
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al consultar vectores D3D Fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVectoresVelocidadPositivaVI3D(tabla, prismas, idcomponente):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente]
        sql = f"""WITH PrismasCTE AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, p.elevacion_target,
                CAST(
                    (DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) / 86400.0) AS DECIMAL(18,5)
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
                WHEN COALESCE(DATEDIFF(SECOND, LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma, hora_prisma), hora_prisma), 0) = 0 THEN 0
                ELSE tresD / (DATEDIFF(SECOND, LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma, hora_prisma), hora_prisma) / 86400.0)
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
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al consultar vectores vi3d positiva: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVectoresVelocidadPositivaFechasVI3D(tabla, prismas, idcomponente, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        sql = f"""WITH PrismasCTE AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, p.elevacion_target,
                CAST(
                    (DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) / 86400.0) AS DECIMAL(18,5)
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
                WHEN COALESCE(DATEDIFF(SECOND, LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma, hora_prisma), hora_prisma), 0) = 0 THEN 0
                ELSE tresD / (DATEDIFF(SECOND, LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma, hora_prisma), hora_prisma) / 86400.0)
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
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al consultar vectores vi3d positiva fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVectoresVelocidadVI3D(tabla, prismas, idcomponente):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente]
        sql = f"""WITH PrismasCTE AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, p.elevacion_target,
                CAST(
                    (DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) / 86400.0) AS DECIMAL(18,5)
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
                WHEN COALESCE(DATEDIFF(SECOND, LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma, hora_prisma), hora_prisma), 0) = 0 THEN 0
                ELSE (tresD - LAG(tresD) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma, hora_prisma))
                    / (DATEDIFF(SECOND, LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma, hora_prisma), hora_prisma) / 86400.0)
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
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al consultar vectores vi3d: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCalcularVectoresVelocidadFechasVI3D(tabla, prismas, idcomponente, fechaini, fechafin):
        placeholders = ', '.join(['?' for _ in prismas])
        params = prismas + [idcomponente] + [fechaini] + [fechafin]
        sql = f"""WITH PrismasCTE AS (
            SELECT i.id_instrumentacion, p.nombre_prisma, p.hora_prisma, p.este_target, p.norte_target, p.elevacion_target,
                CAST(
                    (DATEDIFF(SECOND, FIRST_VALUE(p.hora_prisma) OVER (PARTITION BY p.nombre_prisma ORDER BY p.nombre_prisma, p.hora_prisma), p.hora_prisma) / 86400.0) AS DECIMAL(18,5)
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
                WHEN COALESCE(DATEDIFF(SECOND, LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma, hora_prisma), hora_prisma), 0) = 0 THEN 0
                ELSE (tresD - LAG(tresD) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma, hora_prisma))
                    / (DATEDIFF(SECOND, LAG(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma, hora_prisma), hora_prisma) / 86400.0)
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
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al consultar vectores vi3d fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
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
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al obtener data prismas desviaciones:", e)
            return None
        finally:
            if conn:
                conn.close()
    
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
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener desviacion estandar: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
                
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
            if conn:
                conn.close()
    
    @staticmethod
    def mdlVerificarPrismaUnico(nameprisma, idinstrumento, idproyecto):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # SQL Server: TOP 1
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
            if conn:
                conn.close()
    
    @staticmethod
    def mdlActualizarNombrePrisma(nameprisma, nuevoprisma, idinstrumento, idproyecto):
        tabla = f"prismas{idproyecto}"
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            
            # En pyodbc la transaccion inicia automaticamente
            
            # Actualizar tabla dinámica de prismas
            query_update_prisma = f"""UPDATE {tabla} SET nombre_prisma = ? WHERE nombre_prisma = ?"""
            cursor.execute(query_update_prisma, (nuevoprisma, nameprisma))
            filas_prisma = cursor.rowcount
            
            # Actualizar tabla instrumentacion
            query_update_instrumento = """UPDATE instrumentacion SET nombre_equipo = ? WHERE id_instrumentacion = ?"""
            cursor.execute(query_update_instrumento, (nuevoprisma, idinstrumento))
            filas_instrumento = cursor.rowcount
            
            # Validar que ambas actualizaciones fueron exitosas
            # A veces una puede ser 0 si no hay datos en la tabla dinamica pero el prisma existe en instrumentacion
            # Adaptamos logica para ser flexible, pero advertir.
            if filas_prisma == 0 and filas_instrumento == 0:
                conn.rollback()
                print(f"No se encontró el prisma '{nameprisma}' para actualizar")
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
           
           
   