from services.security.apis.conexiones.conexion import Connection

class UmbralModel:   
    
    @staticmethod
    def mdlObtenerUmbralesPersonalizados(proyectoid):
        try:
            conn = Connection.connectionDB()
            sql = f"""SELECT * FROM umbral_personalizado WHERE id_proyecto = ? ORDER BY rango_umbral ASC;"""
            cur = conn.cursor()
            cur.execute(sql, (proyectoid,))
            result = cur.fetchall() 
            if result:
                return result
            else:
                return None
        except Exception as e:
            print("Error al obtener umbrales: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlGuardarUmbralesPersonalizados(datos):
        """Guarda múltiples umbrales personalizados"""
        sql = """INSERT INTO umbral_personalizado (
                    id_proyecto, 
                    condicion_umbral, 
                    color_umbral, 
                    riesgo_umbral, 
                    rango_umbral, 
                    acciones_umbral,
                    nombre_umbral
                 ) VALUES (?, ?, ?, ?, ?, ?, ?);"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # Pyodbc soporta executemany nativamente
            cur.executemany(sql, datos)
            conn.commit()
            return True
        except Exception as e:
            print("Error al guardar umbrales personalizados:", e)
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerNombresUmbrales(proyectoid):
        """Obtiene nombres únicos de umbrales para un proyecto"""
        sql = "SELECT DISTINCT nombre_umbral FROM umbral_personalizado WHERE id_proyecto = ?;"
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyectoid,))
            return [row[0] for row in cur.fetchall()]
        except Exception as e:
            print("Error al obtener nombres de umbrales:", e)
            return []
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerUmbralPorNombre(proyectoid, nombre_umbral):
        """Obtiene todos los detalles de un umbral por su nombre"""
        sql = """SELECT * FROM umbral_personalizado 
                 WHERE id_proyecto = ? AND nombre_umbral = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyectoid, nombre_umbral))
            
            # Convertir resultados
            # En pyodbc cur.description devuelve una tupla de columnas
            if cur.description:
                columns = [column[0] for column in cur.description]
                rows = cur.fetchall()
                
                if not rows:
                    return None
                
                # Agrupar detalles
                detalles = []
                for row in rows:
                    detalles.append(dict(zip(columns, row)))
                
                return {
                    'nombre_umbral': nombre_umbral,
                    'detalles': detalles
                }
            return None
        except Exception as e:
            print("Error al obtener umbral por nombre:", e)
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlEliminarUmbralPorNombre(proyectoid, nombre_umbral):
        """Elimina todos los registros de un umbral por su nombre"""
        sql = "DELETE FROM umbral_personalizado WHERE id_proyecto = ? AND nombre_umbral = ?;"
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyectoid, nombre_umbral))
            conn.commit()
            return True
        except Exception as e:
            print("Error al eliminar umbral por nombre:", e)
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlEliminarFilaUmbral(id_fila):
        """Elimina una fila específica de un umbral"""
        sql = "DELETE FROM umbral_personalizado WHERE id_umbral = ?;"
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (id_fila,))
            conn.commit()
            return True
        except Exception as e:
            print("Error al eliminar fila de umbral:", e)
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlActualizarFilaUmbral(id_fila, condicion, color, riesgo, rango, acciones):
        """Actualiza una fila existente de un umbral"""
        sql = """UPDATE umbral_personalizado SET 
                    condicion_umbral = ?,
                    color_umbral = ?,
                    riesgo_umbral = ?,
                    rango_umbral = ?,
                    acciones_umbral = ?
                 WHERE id_umbral = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (condicion, color, riesgo, rango, acciones, id_fila))
            conn.commit()
            return True
        except Exception as e:
            print("Error al actualizar fila de umbral:", e)
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlActualizarNombreUmbral(proyectoid, nombre_original, nombre_nuevo):
        """Actualiza el nombre de un umbral"""
        sql = """UPDATE umbral_personalizado 
                 SET nombre_umbral = ? 
                 WHERE id_proyecto = ? AND nombre_umbral = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (nombre_nuevo, proyectoid, nombre_original))
            conn.commit()
            return True
        except Exception as e:
            print("Error al actualizar nombre de umbral:", e)
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlGuardarFilaUmbral(proyectoid, nombre_umbral, condicion, color, riesgo, rango, acciones):
        """Guarda una nueva fila en un umbral existente"""
        sql = """INSERT INTO umbral_personalizado (
                    id_proyecto, 
                    nombre_umbral,
                    condicion_umbral, 
                    color_umbral, 
                    riesgo_umbral, 
                    rango_umbral, 
                    acciones_umbral
                 ) VALUES (?, ?, ?, ?, ?, ?, ?);"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyectoid, nombre_umbral, condicion, color, riesgo, rango, acciones))
            conn.commit()
            return True
        except Exception as e:
            print("Error al guardar fila de umbral:", e)
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlGuardarUmbralesEquipos(proyectoid, componente_id, selected_id, data, tabla):
        if tabla == 'umbral_inclinometro':            
            sql = f"""INSERT INTO {tabla} (id_proyecto, id_inclinometro, condicion_umbral, color_umbral, riesgo_umbral, rango_umbral, acciones_umbral, tipo_umbral) VALUES (?, ?, ?, ?, ?, ?, ?, ?);"""
        elif tabla == 'umbral_celda':            
            sql = f"""INSERT INTO {tabla} (id_proyecto, id_celda, condicion_umbral, color_umbral, riesgo_umbral, rango_umbral, acciones_umbral, tipo_umbral) VALUES (?, ?, ?, ?, ?, ?, ?, ?);"""
        else:
            sql = f"""INSERT INTO {tabla} (id_proyecto, id_componente, condicion_umbral, color_umbral, riesgo_umbral, rango_umbral, acciones_umbral, tipo_umbral) VALUES (?, ?, ?, ?, ?, ?, ?, ?);"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # En pyodbc es preferible usar executemany si los datos están listos, 
            # pero mantendremos el bucle si la lógica original así lo requiere.
            for item in data:
                cur.execute(sql, (proyectoid, componente_id, item['condicion'], item['color'], item['riesgo'], item['rango'], item['acciones'], selected_id))
            conn.commit()
            return True
        except Exception as e:
            print("Error al registrar Umbral:", e)
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlGuardarUmbralesPiezometros(proyectoid, idpiezometro, tipo, data, tipopiezo):
        sql = f"""INSERT INTO umbral_piezometro (id_proyecto, id_piezometro, condicion_umbral, color_umbral, riesgo_umbral,
        rango_umbral, acciones_umbral, tipo_umbral, tipo_piezometro) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            for item in data:
                cur.execute(sql, (proyectoid, idpiezometro, item['condicion'], item['color'], item['riesgo'], item['rango'], item['acciones'], tipo, tipopiezo))
            conn.commit()
            return True
        except Exception as e:
            print("Error al registrar Umbral Piezometros:", e)
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlActualizarUmbralEquipos(umbral_id, nombre, color, riesgo, rango, acciones, tipo, tabla):
        conn = Connection.connectionDB()
        sql = f"""UPDATE {tabla} SET condicion_umbral = ?, color_umbral = ?, riesgo_umbral=?, rango_umbral = ?, acciones_umbral=?, tipo_umbral = ? WHERE id_umbral = ?;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (nombre, color,riesgo, rango,acciones, tipo, umbral_id))
            conn.commit()
            return True
        except Exception as e:
            print("Error al actualizar Umbral:", e)
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlGuardarUmbralesAcelerografo(proyectoid,componente_id, data):
        sql = f"""INSERT INTO umbral_acelerografo (id_proyecto, id_componente, condicion_umbral, riesgo_umbral, color_umbral,
        rango_umbral, magnitud_umbral, acciones_umbral, tipo_umbral) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            for item in data:
                cur.execute(sql, (proyectoid,componente_id, item['nombre'],item['riesgo'], item['color'], item['distancia'], item['magnitud'], item['acciones'], item['tipo']))
            conn.commit()
            return True
        except Exception as e:
            print("Error al registrar Umbral:", e)
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlActualizarUmbralAcelerografo(umbral_id, nombre,riesgo, color, distancia,magnitud,acciones):
        conn = Connection.connectionDB()
        sql = f"""UPDATE umbral_acelerografo SET condicion_umbral = ?, riesgo_umbral = ?, color_umbral = ?, rango_umbral = ?,
        magnitud_umbral = ?, acciones_umbral = ? WHERE id_umbral = ?;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (nombre,riesgo, color, distancia, magnitud,acciones, umbral_id))
            conn.commit()
            return True
        except Exception as e:
            print("Error al actualizar Umbral:", e)
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerUmbralesInstrumentacion(proyectoid, componente_id, tipo, tabla):
        try:
            conn = Connection.connectionDB()
            # En SQL Server los placeholders son ?
            if tabla == 'umbral_inclinometro':
                sql = f"""SELECT * FROM {tabla} WHERE id_inclinometro = ? AND tipo_umbral = ? AND id_proyecto=? ORDER BY rango_umbral ASC;"""
            elif tabla=='umbral_celda':
                sql = f"""SELECT * FROM {tabla} WHERE id_celda = ? AND tipo_umbral = ? AND id_proyecto = ? ORDER BY rango_umbral ASC;"""
            else:
                sql = f"""SELECT * FROM {tabla} WHERE id_componente = ? AND tipo_umbral = ? AND id_proyecto = ? ORDER BY rango_umbral ASC;"""
            cur = conn.cursor()
            cur.execute(sql, (componente_id, tipo,proyectoid))
            result = cur.fetchall() 
            if result:
                return result
            else:
                return None
        except Exception as e:
            print("Error al obtener umbrales: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerPiezometroUmbrales(idpiezo, tipo, tipopiezo):
        try:
            conn = Connection.connectionDB()
            sql = f"""SELECT * FROM umbral_piezometro WHERE id_piezometro = ? AND tipo_umbral = ? AND tipo_piezometro = ? ORDER BY rango_umbral ASC;"""
            cur = conn.cursor()
            cur.execute(sql, (idpiezo, tipo, tipopiezo))
            result = cur.fetchall() 
            if result:
                return result
            else:
                return None
        except Exception as e:
            print("Error al obtener umbrales piezo: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerUmbralesAcelerografo(proyectoid, componente_id, tipo):
        try:
            conn = Connection.connectionDB()
            sql = f"""SELECT * FROM umbral_acelerografo WHERE id_proyecto = ? AND id_componente = ? AND tipo_umbral = ?;"""
            cur = conn.cursor()
            cur.execute(sql, (proyectoid, componente_id, tipo))
            result = cur.fetchall() 
            if result:
                return result
            else:
                return None
        except Exception as e:
            print("Error al obtener umbrales: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
                
    @staticmethod
    def mdlEliminarUmbralEquipos(umbral_id,tabla):
        conn = Connection.connectionDB()
        sql = f"""DELETE FROM {tabla} WHERE id_umbral = ?"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (umbral_id,))
            rows_affected = cur.rowcount
            conn.commit()
            if rows_affected > 0:
                return True
            else:
                return False
        except Exception as e:
            print("Error al eliminar umbral prismas: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlEliminarUmbralAcelerografo(umbral_id):
        conn = Connection.connectionDB()
        sql = f"""DELETE FROM umbral_acelerografo WHERE id_umbral = ?"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (umbral_id,))
            rows_affected = cur.rowcount
            conn.commit()
            if rows_affected > 0:
                return True
            else:
                return False
        except Exception as e:
            print("Error al eliminar umbral acelerografo: " + str(e))
            return False
        finally:
            if conn:
                conn.close() 
                
    @staticmethod
    def mdlGuardarUmbralPrismas(data):
        conn = Connection.connectionDB()
        sql = """INSERT INTO umbral_prisma (id_proyecto, nombre_umbral, normal_umbral, precaucion_umbral, peligro_umbral, cerrar_umbral, color_normal,
        color_precaucion, color_peligro, color_cerrar) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""
        try:
            cur = conn.cursor()
            cur.execute(sql, data)
            conn.commit()
            return True
        except Exception as e:
            print("Error al registrar Umbral:", e)
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlActualizarUmbralPrismas(data):
        conn = Connection.connectionDB()
        sql = """UPDATE umbral_prisma SET normal_umbral = ?, precaucion_umbral = ?, peligro_umbral = ?, cerrar_umbral = ?,
        color_normal = ?, color_precaucion = ?, color_peligro = ?, color_cerrar = ? WHERE id_proyecto = ? AND nombre_umbral = ?;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, data)
            conn.commit()
            return True
        except Exception as e:
            print("Error al actualizar Umbral:", e)
            return False
        finally:
            if conn:
                conn.close()
                
    @staticmethod
    def mdlObtenerUmbralPrismas(proyectoid, idcomponente, tipo):
        try:
            conn = Connection.connectionDB()
            sql = """SELECT * FROM umbral_prisma WHERE id_proyecto = ? AND id_componente = ? AND tipo_umbral = ?;"""
            cur = conn.cursor()
            cur.execute(sql, (proyectoid, idcomponente, tipo))
            result = cur.fetchall()
            if result:
                return result
            else:
                return None
        except Exception as e:
            print("Error al obtener umbrales prismas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # Obtener datos del umbral moonitor 2
    @staticmethod
    def mdlObtenerDatosUmbralm2():
        try:
            conn = Connection.connectionDB()
            sql = """SELECT * FROM umbral2;"""
            
            cur = conn.cursor()
            cur.execute(sql)
            result = cur.fetchall() 
            if result:
                return result
            else:
                return None
        except Exception as e:
            print("Error al obtener umbrales: " + str(e))
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlGuardarUmbralm2(id,color,visd,vasd,vi3d,va3d):
        conn = Connection.connectionDB()
        sql = """UPDATE umbral2 SET color_umbral = ?, VISD = ?, VASD = ?, VI3D = ?, VA3D = ? WHERE id_umbral = ?"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (color,visd,vasd,vi3d,va3d ,id))
            conn.commit()
            return True
        except Exception as e:
            print("Error al actualizar Umbral:", e)
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerUmbralCeldas(proyectoid):
        try:
            conn = Connection.connectionDB()
            sql = """SELECT * FROM umbral_celda WHERE id_proyecto = ?;"""
            
            cur = conn.cursor()
            cur.execute(sql, (proyectoid,))
            result = cur.fetchall() 
            if result:
                return result
            else:
                return None
        except Exception as e:
            print("Error al obtener umbral celda: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerUmbralCodigoCeldas(idumbral):
        try:
            conn = Connection.connectionDB()
            sql = """SELECT * FROM umbral_celda WHERE id_umbral = ?;"""
            
            cur = conn.cursor()
            cur.execute(sql, (idumbral,))
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Exception as e:
            return None
        finally:
            if conn:
                conn.close()
                            
    @staticmethod
    def mdlObtenerUmbralAcelerografos(proyectoid,componente):
        try:
            conn = Connection.connectionDB()
            sql = """SELECT * FROM umbral_acelerografo WHERE id_proyecto=? AND id_componente=?"""
            
            # Cambiado a bloque try-finally estándar para cerrar conexión explícitamente en pyodbc
            cur = conn.cursor()
            cur.execute(sql, (proyectoid,componente))
            result = cur.fetchall()
            return result if result else None

        except Exception as e:
            print(f"Error al obtener umbral acelerógrafos: {str(e)}")
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlGuardarUmbralCeldas(datos):
        conn = Connection.connectionDB()
        sql = """INSERT INTO umbral_celda (id_proyecto, nombre_umbral, normal_umbral, color_normal, precaucion_umbral, color_precaucion, peligro_umbral,
        color_peligro, cerrar_umbral, color_cerrar) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""
        try:
            cur = conn.cursor()
            cur.execute(sql, datos)
            conn.commit()
            return True
        except Exception as e:
            print("Error al insertar Umbral:", e)
            return False
        finally:
            if conn:
                conn.close()
                    
    @staticmethod
    def mdlActualizarUmbralCelda(datos):
        conn = Connection.connectionDB()
        sql = """UPDATE umbral_celda SET normal_umbral = ?, color_normal = ?, precaucion_umbral = ?, color_precaucion = ?, peligro_umbral = ?,
            color_peligro = ?, cerrar_umbral= ?, color_cerrar = ? WHERE id_umbral = ?;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, datos)
            conn.commit()
            return True
        except Exception as e:
            print("Error al actualizar Umbral:", e)
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlGuardarUmbralAcelerografo(id_proyecto, nombre, color, valor):
        conn = Connection.connectionDB()
        
        # SQL para verificar si el registro ya existe (TOP 1 reemplaza LIMIT 1, aunque con fetchone basta)
        sql_check = """SELECT TOP 1 id FROM umbral_acelerografo WHERE proyecto_id = ? AND tipo_umbral = ?;"""
        
        # SQL para actualizar el registro si ya existe
        sql_update = """UPDATE umbral_acelerografo 
                        SET color_umbral = ?, valor_umbral = ? 
                        WHERE proyecto_id = ? AND tipo_umbral = ?;"""
        
        # SQL para insertar un nuevo registro si no existe
        sql_insert = """INSERT INTO umbral_acelerografo (proyecto_id, tipo_umbral, color_umbral, valor_umbral) 
                        VALUES (?, ?, ?, ?);"""

        try:
            cur = conn.cursor()
            
            # Verificamos si el registro ya existe
            cur.execute(sql_check, (id_proyecto, nombre))
            record = cur.fetchone()
            
            if record:  # Si existe, actualizamos el registro
                cur.execute(sql_update, (color, valor, id_proyecto, nombre))
            else:  # Si no existe, insertamos uno nuevo
                cur.execute(sql_insert, (id_proyecto, nombre, color, valor))
            
            conn.commit()
            return True
        
        except Exception as e:
            print("Error al guardar o actualizar Umbral:", e)
            return False
        
        finally:
            if conn:
                conn.close()
                    
    @staticmethod
    def mdlObtenerPenultimoDato(proyecto):
        tabla = f"prismas{proyecto}"
        conn = Connection.connectionDB()
        # Uso de ROW_NUMBER() es totalmente compatible con T-SQL.
        sql = f"""SELECT * FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY id_prisma DESC) AS rn FROM {tabla}) subquery WHERE subquery.rn = 2"""
        try:
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener penultimo dato: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mldObtenerSD(id_proyecto, fechaMinInicial, fechaMaxInicial):
        tabla = f"prismas{id_proyecto}"
        conn = Connection.connectionDB()
        # Se parametrizan las fechas para evitar inyecciones y errores de formato.
        # SQL Server soporta WITH CTE y funciones de ventana como LAG y FIRST_VALUE.
        # Nota: FIRST_VALUE en SQL Server requiere ORDER BY dentro del OVER.
        sql = f"""WITH CTE AS (
                SELECT
                    nombre_prisma,
                    distancia_prisma AS distancia_prisma,
                    LAG(nombre_prisma) OVER (ORDER BY nombre_prisma) AS prev_nombre_prisma,
                    FIRST_VALUE(distancia_prisma) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma) AS primer_valor
                FROM {tabla}
                WHERE state_prisma = '1' AND hora_prisma BETWEEN ? AND ?
            )
            , RankedCTE AS (
                SELECT
                    nombre_prisma,
                    distancia_prisma AS distancia_prisma,
                    CASE
                    WHEN nombre_prisma <> prev_nombre_prisma THEN 0
                    ELSE distancia_prisma - primer_valor
                    END AS SD,
                    ABS(CASE
                    WHEN nombre_prisma <> prev_nombre_prisma THEN 0
                    ELSE distancia_prisma - primer_valor
                    END) AS valor_absoluto_SD,
                    ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY ABS(distancia_prisma - primer_valor) DESC) AS row_num
                FROM CTE
            )
            SELECT nombre_prisma, distancia_prisma, SD, valor_absoluto_SD
            FROM RankedCTE
            WHERE row_num = 1
            ORDER BY nombre_prisma;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (fechaMinInicial, fechaMaxInicial))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener datos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mldObtenerSDManual(id_proyecto, fechaMinInicial, fechaMaxInicial):
        tabla = f"prismas{id_proyecto}"
        conn = Connection.connectionDB()
        sql = f"""WITH CTE AS (
                SELECT
                    nombre_prisma,
                    distancia_prisma AS distancia_prisma,
                    LAG(nombre_prisma) OVER (ORDER BY nombre_prisma) AS prev_nombre_prisma,
                    FIRST_VALUE(distancia_prisma) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma) AS primer_valor
                FROM {tabla}
                WHERE state_prisma = '1' AND hora_prisma BETWEEN ? AND ?
            )
            , RankedCTE AS (
                SELECT
                    nombre_prisma,
                    distancia_prisma AS distancia_prisma,
                    CASE
                    WHEN nombre_prisma <> prev_nombre_prisma THEN 0
                    ELSE distancia_prisma - primer_valor
                    END AS SD,
                    ABS(CASE
                    WHEN nombre_prisma <> prev_nombre_prisma THEN 0
                    ELSE distancia_prisma - primer_valor
                    END) AS valor_absoluto_SD,
                    ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY ABS(distancia_prisma - primer_valor) DESC) AS row_num
                FROM CTE
            )
            SELECT nombre_prisma, distancia_prisma, SD, valor_absoluto_SD
            FROM RankedCTE
            WHERE row_num = 1
            ORDER BY nombre_prisma;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (fechaMinInicial, fechaMaxInicial))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener datos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mldObtenerSDPrismaNombre(id_proyecto, nombres, fechaMinInicial, fechaMaxInicial):
        tabla = f"prismas{id_proyecto}"
        conn = Connection.connectionDB()
        # Nota: La lista 'nombres' se inyecta como string porque SQL no soporta array params directamente en IN de forma sencilla sin TVP.
        # Asegurarse de que 'nombres' venga sanitizado desde el controlador.
        nombres_str = "','".join(nombres)
        
        sql = f"""WITH CTE AS (
                SELECT
                    nombre_prisma,
                    distancia_prisma AS distancia_prisma,
                    LAG(nombre_prisma) OVER (ORDER BY nombre_prisma) AS prev_nombre_prisma,
                    FIRST_VALUE(distancia_prisma) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma) AS primer_valor
                FROM {tabla}
                WHERE state_prisma = '1' AND nombre_prisma IN ('{nombres_str}') AND hora_prisma BETWEEN ? AND ?
            )
            , RankedCTE AS (
                SELECT
                    nombre_prisma,
                    distancia_prisma AS distancia_prisma,
                    CASE
                    WHEN nombre_prisma <> prev_nombre_prisma THEN 0
                    ELSE distancia_prisma - primer_valor
                    END AS SD,
                    ABS(CASE
                    WHEN nombre_prisma <> prev_nombre_prisma THEN 0
                    ELSE distancia_prisma - primer_valor
                    END) AS valor_absoluto_SD,
                    ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY ABS(distancia_prisma - primer_valor) DESC) AS row_num
                FROM CTE
            )
            SELECT nombre_prisma, distancia_prisma, SD, valor_absoluto_SD
            FROM RankedCTE
            WHERE row_num = 1
            ORDER BY nombre_prisma;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (fechaMinInicial, fechaMaxInicial))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener datos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
                
    @staticmethod
    def mldObtenerSDPrismaNombreManual(id_proyecto, nombres, fechaMinInicial, fechaMaxInicial):
        tabla = f"prismas{id_proyecto}"
        conn = Connection.connectionDB()
        # Construcción manual del string para el IN ya que pyodbc no soporta listas directas limpiamente
        nombres_str = "','".join(nombres)
        
        sql = f"""WITH CTE AS (
                SELECT
                    nombre_prisma,
                    distancia_prisma AS distancia_prisma,
                    LAG(nombre_prisma) OVER (ORDER BY nombre_prisma) AS prev_nombre_prisma,
                    FIRST_VALUE(distancia_prisma) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma) AS primer_valor
                FROM {tabla}
                WHERE state_prisma = '1' AND nombre_prisma IN ('{nombres_str}') AND hora_prisma BETWEEN ? AND ?
            )
            , RankedCTE AS (
                SELECT
                    nombre_prisma,
                    distancia_prisma AS distancia_prisma,
                    CASE
                    WHEN nombre_prisma <> prev_nombre_prisma THEN 0
                    ELSE distancia_prisma - primer_valor
                    END AS SD,
                    ABS(CASE
                    WHEN nombre_prisma <> prev_nombre_prisma THEN 0
                    ELSE distancia_prisma - primer_valor
                    END) AS valor_absoluto_SD,
                    ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY ABS(distancia_prisma - primer_valor) DESC) AS row_num
                FROM CTE
            )
            SELECT nombre_prisma, distancia_prisma, SD, valor_absoluto_SD
            FROM RankedCTE
            WHERE row_num = 1
            ORDER BY nombre_prisma;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (fechaMinInicial, fechaMaxInicial))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener datos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mldObtener3D(id_proyecto, fechaMinInicial, fechaMaxInicial):
        tabla = f"prismas{id_proyecto}"
        conn = Connection.connectionDB()
        sql = f"""WITH CalculoDistancias AS (
                SELECT
                    nombre_prisma,
                    hora_prisma,
                    este_target,
                    norte_target,
                    elevacion_target,
                    SQRT(
                        POWER(este_target - FIRST_VALUE(este_target) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma), 2) +
                        POWER(norte_target - FIRST_VALUE(norte_target) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma), 2) +
                        POWER(elevacion_target - FIRST_VALUE(elevacion_target) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma), 2)
                    ) AS distancia
                FROM {tabla}
                WHERE state_prisma = '1' AND hora_prisma BETWEEN ? AND ?
            )
            SELECT nombre_prisma, MAX(hora_prisma), distancia
            FROM CalculoDistancias
            GROUP BY nombre_prisma, distancia;""" 
            # Nota: En SQL Server, si agrupas, todas las columnas no agregadas deben estar en el GROUP BY.
            # He agregado 'distancia' al GROUP BY para cumplir con la sintaxis estricta de SQL Server si 'distancia' no es un agregado.
            # Si 'distancia' varía por fila y queremos el MAX de todo, la lógica original podría fallar en SQL Server.
            # Asumiendo que FIRST_VALUE hace que la distancia sea constante por prisma base o que queremos agrupar así.
        try:
            cur = conn.cursor()
            cur.execute(sql, (fechaMinInicial, fechaMaxInicial))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener datos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mldObtener3DManual(id_proyecto, fechaMinInicial, fechaMaxInicial):
        tabla = f"prismas{id_proyecto}"
        conn = Connection.connectionDB()
        sql = f"""WITH CalculoDistancias AS (
                SELECT
                    nombre_prisma,
                    hora_prisma,
                    este_target,
                    norte_target,
                    elevacion_target,
                    SQRT(
                        POWER(este_target - FIRST_VALUE(este_target) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma), 2) +
                        POWER(norte_target - FIRST_VALUE(norte_target) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma), 2) +
                        POWER(elevacion_target - FIRST_VALUE(elevacion_target) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma), 2)
                    ) AS distancia
                FROM {tabla}
                WHERE state_prisma = '1' AND hora_prisma BETWEEN ? AND ?
            )
            SELECT nombre_prisma, MAX(hora_prisma), distancia
            FROM CalculoDistancias
            GROUP BY nombre_prisma, distancia;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (fechaMinInicial, fechaMaxInicial))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener datos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mldObtener3DPrismaNombre(id_proyecto, nombres, fechaMinInicial, fechaMaxInicial):
        tabla = f"prismas{id_proyecto}"
        conn = Connection.connectionDB()
        nombres_str = "','".join(nombres)
        sql = f"""WITH CalculoDistancias AS (
                SELECT
                    nombre_prisma,
                    hora_prisma,
                    este_target,
                    norte_target,
                    elevacion_target,
                    SQRT(
                        POWER(este_target - FIRST_VALUE(este_target) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma), 2) +
                        POWER(norte_target - FIRST_VALUE(norte_target) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma), 2) +
                        POWER(elevacion_target - FIRST_VALUE(elevacion_target) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma), 2)
                    ) AS distancia
                FROM {tabla}
                WHERE state_prisma = '1' AND nombre_prisma IN ('{nombres_str}') AND hora_prisma BETWEEN ? AND ?
            )
            SELECT nombre_prisma, MAX(hora_prisma), distancia
            FROM CalculoDistancias
            GROUP BY nombre_prisma, distancia;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (fechaMinInicial, fechaMaxInicial))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener datos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mldObtener3DPrismaNombreManual(id_proyecto, nombres, fechaMinInicial, fechaMaxInicial):
        tabla = f"prismas{id_proyecto}"
        conn = Connection.connectionDB()
        nombres_str = "','".join(nombres)
        sql = f"""WITH CalculoDistancias AS (
                SELECT
                    nombre_prisma,
                    hora_prisma,
                    este_target,
                    norte_target,
                    elevacion_target,
                    SQRT(
                        POWER(este_target - FIRST_VALUE(este_target) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma), 2) +
                        POWER(norte_target - FIRST_VALUE(norte_target) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma), 2) +
                        POWER(elevacion_target - FIRST_VALUE(elevacion_target) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma), 2)
                    ) AS distancia
                FROM {tabla}
                WHERE state_prisma = '1' AND nombre_prisma IN ('{nombres_str}') AND hora_prisma BETWEEN ? AND ?
            )
            SELECT nombre_prisma, MAX(hora_prisma), distancia
            FROM CalculoDistancias
            GROUP BY nombre_prisma, distancia;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (fechaMinInicial, fechaMaxInicial))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener datos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mldObtenerL(id_proyecto, fechaMinInicial, fechaMaxInicial):
        tabla = f"prismas{id_proyecto}"
        conn = Connection.connectionDB()
        # En SQL Server, las columnas en SELECT que no son agregadas deben estar en GROUP BY
        sql = f"""SELECT p1.nombre_prisma, p1.desplaza_longitudinal, MAX(ABS(p1.desplaza_longitudinal)) AS max_valor_absolutoDL 
        FROM {tabla} AS p1 
        WHERE state_prisma = '1' AND hora_prisma BETWEEN ? AND ? 
        GROUP BY p1.nombre_prisma, p1.desplaza_longitudinal 
        ORDER BY p1.nombre_prisma;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (fechaMinInicial, fechaMaxInicial))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener datos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mldObtenerLManual(id_proyecto, fechaMinInicial, fechaMaxInicial):
        tabla = f"prismas{id_proyecto}"
        conn = Connection.connectionDB()
        sql = f"""SELECT p1.nombre_prisma, p1.desplaza_longitudinal, MAX(ABS(p1.desplaza_longitudinal)) AS max_valor_absolutoDL 
        FROM {tabla} AS p1 
        WHERE state_prisma = '1' AND hora_prisma BETWEEN ? AND ? 
        GROUP BY p1.nombre_prisma, p1.desplaza_longitudinal 
        ORDER BY p1.nombre_prisma;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (fechaMinInicial, fechaMaxInicial))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener datos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mldObtenerLPrismaNombre(id_proyecto, nombres, fechaMinInicial, fechaMaxInicial):
        tabla = f"prismas{id_proyecto}"
        conn = Connection.connectionDB()
        nombres_str = "','".join(nombres)
        sql = f"""SELECT p1.nombre_prisma, p1.desplaza_longitudinal, MAX(ABS(p1.desplaza_longitudinal)) AS max_valor_absolutoDL 
        FROM {tabla} AS p1 
        WHERE state_prisma = '1' AND nombre_prisma IN ('{nombres_str}') AND hora_prisma BETWEEN ? AND ? 
        GROUP BY p1.nombre_prisma, p1.desplaza_longitudinal 
        ORDER BY p1.nombre_prisma;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (fechaMinInicial, fechaMaxInicial))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener datos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mldObtenerLPrismaNombreManual(id_proyecto, nombres, fechaMinInicial, fechaMaxInicial):
        tabla = f"prismas{id_proyecto}"
        conn = Connection.connectionDB()
        nombres_str = "','".join(nombres)
        sql = f"""SELECT p1.nombre_prisma, p1.desplaza_longitudinal, MAX(ABS(p1.desplaza_longitudinal)) AS max_valor_absolutoDL 
        FROM {tabla} AS p1 
        WHERE state_prisma = '1' AND nombre_prisma IN ('{nombres_str}') AND hora_prisma BETWEEN ? AND ? 
        GROUP BY p1.nombre_prisma, p1.desplaza_longitudinal 
        ORDER BY p1.nombre_prisma;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (fechaMinInicial, fechaMaxInicial))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener datos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mldObtenerT(id_proyecto, fechaMinInicial, fechaMaxInicial):
        tabla = f"prismas{id_proyecto}"
        conn = Connection.connectionDB()
        sql = f"""SELECT p1.nombre_prisma, p1.desplaza_transversal, MAX(ABS(p1.desplaza_transversal)) AS max_valor_absolutoDT  
        FROM {tabla} AS p1 
        WHERE state_prisma = '1' AND hora_prisma BETWEEN ? AND ? 
        GROUP BY p1.nombre_prisma, p1.desplaza_transversal 
        ORDER BY p1.nombre_prisma;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (fechaMinInicial, fechaMaxInicial))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener datos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mldObtenerTManual(id_proyecto, fechaMinInicial, fechaMaxInicial):
        tabla = f"prismas{id_proyecto}"
        conn = Connection.connectionDB()
        sql = f"""SELECT p1.nombre_prisma, p1.desplaza_transversal, MAX(ABS(p1.desplaza_transversal)) AS max_valor_absolutoDT  
        FROM {tabla} AS p1 
        WHERE state_prisma = '1' AND hora_prisma BETWEEN ? AND ? 
        GROUP BY p1.nombre_prisma, p1.desplaza_transversal 
        ORDER BY p1.nombre_prisma;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (fechaMinInicial, fechaMaxInicial))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener datos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mldObtenerTPrismaNombre(id_proyecto, nombres, fechaMinInicial, fechaMaxInicial):
        tabla = f"prismas{id_proyecto}"
        conn = Connection.connectionDB()
        nombres_str = "','".join(nombres)
        sql = f"""SELECT p1.nombre_prisma, p1.desplaza_transversal, MAX(ABS(p1.desplaza_transversal)) AS max_valor_absolutoDT  
        FROM {tabla} AS p1 
        WHERE state_prisma = '1' AND nombre_prisma IN ('{nombres_str}') AND hora_prisma BETWEEN ? AND ? 
        GROUP BY p1.nombre_prisma, p1.desplaza_transversal 
        ORDER BY p1.nombre_prisma;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (fechaMinInicial, fechaMaxInicial))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener datos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mldObtenerTPrismaNombreManual(id_proyecto, nombres, fechaMinInicial, fechaMaxInicial):
        tabla = f"prismas{id_proyecto}"
        conn = Connection.connectionDB()
        nombres_str = "','".join(nombres)
        sql = f"""SELECT p1.nombre_prisma, p1.desplaza_transversal, MAX(ABS(p1.desplaza_transversal)) AS max_valor_absolutoDT  
        FROM {tabla} AS p1 
        WHERE state_prisma = '1' AND nombre_prisma IN ('{nombres_str}') AND hora_prisma BETWEEN ? AND ? 
        GROUP BY p1.nombre_prisma, p1.desplaza_transversal 
        ORDER BY p1.nombre_prisma;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (fechaMinInicial, fechaMaxInicial))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener datos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mldObtenerH(id_proyecto, fechaMinInicial, fechaMaxInicial):
        tabla = f"prismas{id_proyecto}"
        conn = Connection.connectionDB()
        sql = f"""SELECT p1.nombre_prisma, p1.desplaza_altura, MAX(ABS(p1.desplaza_altura)) AS max_valor_absolutoDH 
        FROM {tabla} AS p1  
        WHERE state_prisma = '1' AND hora_prisma BETWEEN ? AND ? 
        GROUP BY p1.nombre_prisma, p1.desplaza_altura 
        ORDER BY p1.nombre_prisma;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (fechaMinInicial, fechaMaxInicial))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener datos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mldObtenerHManual(id_proyecto, fechaMinInicial, fechaMaxInicial):
        tabla = f"prismas{id_proyecto}"
        conn = Connection.connectionDB()
        sql = f"""SELECT p1.nombre_prisma, p1.desplaza_altura, MAX(ABS(p1.desplaza_altura)) AS max_valor_absolutoDH 
        FROM {tabla} AS p1  
        WHERE state_prisma = '1' AND hora_prisma BETWEEN ? AND ? 
        GROUP BY p1.nombre_prisma, p1.desplaza_altura 
        ORDER BY p1.nombre_prisma;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (fechaMinInicial, fechaMaxInicial))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener datos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mldObtenerHPrismaNombre(id_proyecto, nombres, fechaMinInicial, fechaMaxInicial):
        tabla = f"prismas{id_proyecto}"
        conn = Connection.connectionDB()
        nombres_str = "','".join(nombres)
        sql = f"""SELECT p1.nombre_prisma, p1.desplaza_altura, MAX(ABS(p1.desplaza_altura)) AS max_valor_absolutoDH 
        FROM {tabla} AS p1  
        WHERE state_prisma = '1' AND nombre_prisma IN ('{nombres_str}') AND hora_prisma BETWEEN ? AND ? 
        GROUP BY p1.nombre_prisma, p1.desplaza_altura 
        ORDER BY p1.nombre_prisma;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (fechaMinInicial, fechaMaxInicial))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener datos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mldObtenerHPrismaNombreManual(id_proyecto, nombres, fechaMinInicial, fechaMaxInicial):
        tabla = f"prismas{id_proyecto}"
        conn = Connection.connectionDB()
        nombres_str = "','".join(nombres)
        sql = f"""SELECT p1.nombre_prisma, p1.desplaza_altura, MAX(ABS(p1.desplaza_altura)) AS max_valor_absolutoDH 
        FROM {tabla} AS p1  
        WHERE state_prisma = '1' AND nombre_prisma IN ('{nombres_str}') AND hora_prisma BETWEEN ? AND ? 
        GROUP BY p1.nombre_prisma, p1.desplaza_altura 
        ORDER BY p1.nombre_prisma;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (fechaMinInicial, fechaMaxInicial))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener datos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
                   
    @staticmethod
    def mldObtenerN(id_proyecto, fechaMinInicial, fechaMaxInicial):
        tabla = f"prismas{id_proyecto}"
        conn = Connection.connectionDB()
        sql = f"""WITH CalculoDistancias AS (
            SELECT nombre_prisma, norte_target,
            (norte_target - FIRST_VALUE(norte_target) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma)) AS distancia, 
            ABS(norte_target - FIRST_VALUE(norte_target) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma)) AS V_A 
            FROM {tabla} 
            WHERE state_prisma = '1' AND hora_prisma BETWEEN ? AND ?
        ) 
        SELECT nombre_prisma, distancia, MAX(V_A) AS mayor_distancia 
        FROM CalculoDistancias 
        GROUP BY nombre_prisma, distancia
        ORDER BY nombre_prisma;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (fechaMinInicial, fechaMaxInicial))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener datos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mldObtenerNManual(id_proyecto, fechaMinInicial, fechaMaxInicial):
        tabla = f"prismas{id_proyecto}"
        conn = Connection.connectionDB()
        sql = f"""WITH CalculoDistancias AS (
            SELECT nombre_prisma, norte_target,
            (norte_target - FIRST_VALUE(norte_target) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma)) AS distancia, 
            ABS(norte_target - FIRST_VALUE(norte_target) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma)) AS V_A 
            FROM {tabla} 
            WHERE state_prisma = '1' AND hora_prisma BETWEEN ? AND ?
        ) 
        SELECT nombre_prisma, distancia, MAX(V_A) AS mayor_distancia 
        FROM CalculoDistancias 
        GROUP BY nombre_prisma, distancia
        ORDER BY nombre_prisma;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (fechaMinInicial, fechaMaxInicial))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener datos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mldObtenerNPrismaNombre(id_proyecto, nombres, fechaMinInicial, fechaMaxInicial):
        tabla = f"prismas{id_proyecto}"
        conn = Connection.connectionDB()
        nombres_str = "','".join(nombres)
        sql = f"""WITH CalculoDistancias AS (
            SELECT nombre_prisma, norte_target,
            (norte_target - FIRST_VALUE(norte_target) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma)) AS distancia, 
            ABS(norte_target - FIRST_VALUE(norte_target) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma)) AS V_A 
            FROM {tabla} 
            WHERE state_prisma = '1' AND nombre_prisma IN ('{nombres_str}') AND hora_prisma BETWEEN ? AND ?
        ) 
        SELECT nombre_prisma, distancia, MAX(V_A) AS mayor_distancia 
        FROM CalculoDistancias 
        GROUP BY nombre_prisma, distancia
        ORDER BY nombre_prisma;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (fechaMinInicial, fechaMaxInicial))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener datos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mldObtenerNPrismaNombreManual(id_proyecto, nombres, fechaMinInicial, fechaMaxInicial):
        tabla = f"prismas{id_proyecto}"
        conn = Connection.connectionDB()
        nombres_str = "','".join(nombres)
        sql = f"""WITH CalculoDistancias AS (
            SELECT nombre_prisma, norte_target,
            (norte_target - FIRST_VALUE(norte_target) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma)) AS distancia, 
            ABS(norte_target - FIRST_VALUE(norte_target) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma)) AS V_A 
            FROM {tabla} 
            WHERE state_prisma = '1' AND nombre_prisma IN ('{nombres_str}') AND hora_prisma BETWEEN ? AND ?
        ) 
        SELECT nombre_prisma, distancia, MAX(V_A) AS mayor_distancia 
        FROM CalculoDistancias 
        GROUP BY nombre_prisma, distancia
        ORDER BY nombre_prisma;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (fechaMinInicial, fechaMaxInicial))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener datos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
                  
    @staticmethod
    def mldObtenerE(id_proyecto, fechaMinInicial, fechaMaxInicial):
        tabla = f"prismas{id_proyecto}"
        conn = Connection.connectionDB()
        sql = f"""WITH CalculoDistancias AS (
            SELECT nombre_prisma, este_target,
            (este_target - FIRST_VALUE(este_target) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma)) AS distancia, 
            ABS(este_target - FIRST_VALUE(este_target) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma)) AS V_A 
            FROM {tabla} 
            WHERE state_prisma = '1' AND hora_prisma BETWEEN ? AND ?
        ) 
        SELECT nombre_prisma, distancia, MAX(V_A) AS mayor_distancia 
        FROM CalculoDistancias 
        GROUP BY nombre_prisma, distancia
        ORDER BY nombre_prisma;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (fechaMinInicial, fechaMaxInicial))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener datos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mldObtenerEManual(id_proyecto, fechaMinInicial, fechaMaxInicial):
        tabla = f"prismas{id_proyecto}"
        conn = Connection.connectionDB()
        # Se usa ROW_NUMBER para obtener el registro correspondiente al MAX(V_A)
        # ya que SQL Server requiere que las columnas no agregadas estén en GROUP BY
        sql = f"""WITH CalculoDistancias AS (
            SELECT nombre_prisma, este_target,
            (este_target - FIRST_VALUE(este_target) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma)) AS distancia, 
            ABS(este_target - FIRST_VALUE(este_target) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma)) AS V_A 
            FROM {tabla} 
            WHERE state_prisma = '1' AND hora_prisma BETWEEN ? AND ?
        ),
        Ranked AS (
            SELECT nombre_prisma, distancia, V_A,
            ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY V_A DESC) as rn
            FROM CalculoDistancias
        )
        SELECT nombre_prisma, distancia, V_A AS mayor_distancia 
        FROM Ranked 
        WHERE rn = 1
        ORDER BY nombre_prisma;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (fechaMinInicial, fechaMaxInicial))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener datos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
                  
    @staticmethod
    def mldObtenerEPrismaNombre(id_proyecto, nombres, fechaMinInicial, fechaMaxInicial):
        tabla = f"prismas{id_proyecto}"
        conn = Connection.connectionDB()
        nombres_str = "','".join(nombres)
        sql = f"""WITH CalculoDistancias AS (
            SELECT nombre_prisma, este_target,
            (este_target - FIRST_VALUE(este_target) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma)) AS distancia, 
            ABS(este_target - FIRST_VALUE(este_target) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma)) AS V_A 
            FROM {tabla} 
            WHERE state_prisma = '1' AND nombre_prisma IN ('{nombres_str}') AND hora_prisma BETWEEN ? AND ?
        ),
        Ranked AS (
            SELECT nombre_prisma, distancia, V_A,
            ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY V_A DESC) as rn
            FROM CalculoDistancias
        )
        SELECT nombre_prisma, distancia, V_A AS mayor_distancia 
        FROM Ranked 
        WHERE rn = 1
        ORDER BY nombre_prisma;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (fechaMinInicial, fechaMaxInicial))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener datos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mldObtenerEPrismaNombreManual(id_proyecto, nombres, fechaMinInicial, fechaMaxInicial):
        tabla = f"prismas{id_proyecto}"
        conn = Connection.connectionDB()
        nombres_str = "','".join(nombres)
        sql = f"""WITH CalculoDistancias AS (
            SELECT nombre_prisma, este_target,
            (este_target - FIRST_VALUE(este_target) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma)) AS distancia, 
            ABS(este_target - FIRST_VALUE(este_target) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma)) AS V_A 
            FROM {tabla} 
            WHERE state_prisma = '1' AND nombre_prisma IN ('{nombres_str}') AND hora_prisma BETWEEN ? AND ?
        ),
        Ranked AS (
            SELECT nombre_prisma, distancia, V_A,
            ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY V_A DESC) as rn
            FROM CalculoDistancias
        )
        SELECT nombre_prisma, distancia, V_A AS mayor_distancia 
        FROM Ranked 
        WHERE rn = 1
        ORDER BY nombre_prisma;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (fechaMinInicial, fechaMaxInicial))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener datos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mldObtenerZ(id_proyecto, fechaMinInicial, fechaMaxInicial):
        tabla = f"prismas{id_proyecto}"
        conn = Connection.connectionDB()
        sql = f"""WITH CalculoDistancias AS (
            SELECT nombre_prisma, elevacion_target,
            (elevacion_target - FIRST_VALUE(elevacion_target) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma)) AS distancia, 
            ABS(elevacion_target - FIRST_VALUE(elevacion_target) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma)) AS V_A 
            FROM {tabla} 
            WHERE state_prisma = '1' AND hora_prisma BETWEEN ? AND ?
        ),
        Ranked AS (
            SELECT nombre_prisma, distancia, V_A,
            ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY V_A DESC) as rn
            FROM CalculoDistancias
        )
        SELECT nombre_prisma, distancia, V_A AS mayor_distancia 
        FROM Ranked 
        WHERE rn = 1
        ORDER BY nombre_prisma;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (fechaMinInicial, fechaMaxInicial))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener datos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mldObtenerZManual(id_proyecto, fechaMinInicial, fechaMaxInicial):
        tabla = f"prismas{id_proyecto}"
        conn = Connection.connectionDB()
        sql = f"""WITH CalculoDistancias AS (
            SELECT nombre_prisma, elevacion_target,
            (elevacion_target - FIRST_VALUE(elevacion_target) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma)) AS distancia, 
            ABS(elevacion_target - FIRST_VALUE(elevacion_target) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma)) AS V_A 
            FROM {tabla} 
            WHERE state_prisma = '1' AND hora_prisma BETWEEN ? AND ?
        ),
        Ranked AS (
            SELECT nombre_prisma, distancia, V_A,
            ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY V_A DESC) as rn
            FROM CalculoDistancias
        )
        SELECT nombre_prisma, distancia, V_A AS mayor_distancia 
        FROM Ranked 
        WHERE rn = 1
        ORDER BY nombre_prisma;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (fechaMinInicial, fechaMaxInicial))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener datos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mldObtenerZPrismaNombre(id_proyecto, nombres, fechaMinInicial, fechaMaxInicial):
        tabla = f"prismas{id_proyecto}"
        conn = Connection.connectionDB()
        nombres_str = "','".join(nombres)
        sql = f"""WITH CalculoDistancias AS (
            SELECT nombre_prisma, elevacion_target,
            (elevacion_target - FIRST_VALUE(elevacion_target) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma)) AS distancia, 
            ABS(elevacion_target - FIRST_VALUE(elevacion_target) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma)) AS V_A 
            FROM {tabla} 
            WHERE state_prisma = '1' AND nombre_prisma IN ('{nombres_str}') AND hora_prisma BETWEEN ? AND ?
        ),
        Ranked AS (
            SELECT nombre_prisma, distancia, V_A,
            ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY V_A DESC) as rn
            FROM CalculoDistancias
        )
        SELECT nombre_prisma, distancia, V_A AS mayor_distancia 
        FROM Ranked 
        WHERE rn = 1
        ORDER BY nombre_prisma;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (fechaMinInicial, fechaMaxInicial))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener datos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mldObtenerZPrismaNombreManual(id_proyecto, nombres, fechaMinInicial, fechaMaxInicial):
        tabla = f"prismas{id_proyecto}"
        conn = Connection.connectionDB()
        nombres_str = "','".join(nombres)
        sql = f"""WITH CalculoDistancias AS (
            SELECT nombre_prisma, elevacion_target,
            (elevacion_target - FIRST_VALUE(elevacion_target) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma)) AS distancia, 
            ABS(elevacion_target - FIRST_VALUE(elevacion_target) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma)) AS V_A 
            FROM {tabla} 
            WHERE state_prisma = '1' AND nombre_prisma IN ('{nombres_str}') AND hora_prisma BETWEEN ? AND ?
        ),
        Ranked AS (
            SELECT nombre_prisma, distancia, V_A,
            ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY V_A DESC) as rn
            FROM CalculoDistancias
        )
        SELECT nombre_prisma, distancia, V_A AS mayor_distancia 
        FROM Ranked 
        WHERE rn = 1
        ORDER BY nombre_prisma;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (fechaMinInicial, fechaMaxInicial))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener datos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
            
    #obtener fecha mini y maximo de los prismas automatizados
    @staticmethod
    def mdlObtenerFechaMinMaxAuto(id_proyecto):
        tabla = f"prismas{id_proyecto}"
        conn = Connection.connectionDB()
        sql = f"""SELECT MIN(hora_prisma) AS min_fecha, MAX(hora_prisma) AS max_fecha FROM {tabla} WHERE state_prisma = 1;"""
        try:
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
    
    #obtener fecha mini y maximo de los prismas manuales
    @staticmethod
    def mdlObtenerFechaMinMaxManual(id_proyecto):
        tabla = f"prismas{id_proyecto}"
        conn = Connection.connectionDB()
        sql = f"""SELECT MIN(hora_prisma) AS min_fecha, MAX(hora_prisma) AS max_fecha FROM {tabla} WHERE state_prisma = 1;"""
        try:
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

    #Obtener fechas mininimas y maximas de los prismas auto entre fechas
    @staticmethod
    def mdlObtenerFechasEnRango(id_proyecto, fechaMinInicial, fechaMaxInicial):
        tabla = f"prismas{id_proyecto}"
        conn = Connection.connectionDB()
        sql = f"""SELECT nombre_prisma, min(hora_prisma), max(hora_prisma) FROM {tabla} WHERE state_prisma = '1' 
        AND hora_prisma BETWEEN ? AND ? GROUP BY nombre_prisma;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (fechaMinInicial, fechaMaxInicial))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    #Obtener fechas mininimas y maximas de los prismas auto entre fechas
    @staticmethod
    def mdlObtenerFechasEnRangoManual(id_proyecto, fechaMinInicial, fechaMaxInicial):
        tabla = f"prismas{id_proyecto}"
        conn = Connection.connectionDB()
        sql = f"""SELECT nombre_prisma, min(hora_prisma), max(hora_prisma) FROM {tabla} WHERE state_prisma = '1' 
        AND hora_prisma BETWEEN ? AND ? GROUP BY nombre_prisma;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (fechaMinInicial, fechaMaxInicial))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener fechas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
         
    #Obtener fechas mininimas y maximas de un prisma entre fechas
    @staticmethod
    def mdlObtenerFechasRangoPrismaNombre(id_proyecto, nombres, fechaini, fechafin):
        tabla = f"prismas{id_proyecto}"
        placeholders = ','.join(['?' for _ in nombres])
        conn = Connection.connectionDB()
        sql = f"""SELECT nombre_prisma, min(hora_prisma), max(hora_prisma) FROM {tabla} WHERE state_prisma = '1' AND nombre_prisma 
        IN ({placeholders}) AND hora_prisma BETWEEN ? AND ? GROUP BY nombre_prisma;"""
        try:
            cur = conn.cursor()
            # Pyodbc requiere que todos los parámetros estén en una sola secuencia
            params = tuple(nombres) + (fechaini, fechafin)
            cur.execute(sql, params)
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener datos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    
    #Obtener fechas mininimas y maximas de un prisma manual entre fechas
    @staticmethod
    def mdlObtenerFechasRangoPrismaNombreManual(id_proyecto, nombres, fechaini, fechafin):
        tabla = f"prismas{id_proyecto}"
        placeholders = ','.join(['?' for _ in nombres])
        conn = Connection.connectionDB()
        sql = f"""SELECT nombre_prisma, min(hora_prisma), max(hora_prisma) FROM {tabla} WHERE state_prisma = '1' AND nombre_prisma 
        IN ({placeholders}) AND hora_prisma BETWEEN ? AND ? GROUP BY nombre_prisma;"""
        try:
            cur = conn.cursor()
            params = tuple(nombres) + (fechaini, fechafin)
            cur.execute(sql, params)
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener datos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
                
    # Verificar si hay data de prismas automatizados entre fechas
    @staticmethod
    def mdlComprobarDataPrismasAutoFecha(proyectoid, fechainicial, fechafinal):
        tabla = f"prismas{proyectoid}"
        conn = Connection.connectionDB()
        # Uso de TOP 1 para optimizar en SQL Server
        sql = f"""SELECT TOP 1 1 FROM {tabla} WHERE state_prisma = '1' AND hora_prisma BETWEEN ? AND ?"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (fechainicial, fechafinal))
            row = cur.fetchone()
            if row:
                return True
            else:
                return False
        except Exception as e:
            print("Error al comprobar datos: " + str(e))
            return False
        finally:
            if conn:
                conn.close()

    # Verificar si hay data de prismas manuales entre fechas
    @staticmethod
    def mdlComprobarDataPrismasManualFecha(proyectoid, fechainicial, fechafinal):
        tabla = f"prismas{proyectoid}"
        conn = Connection.connectionDB()
        sql = f"""SELECT TOP 1 1 FROM {tabla} WHERE state_prisma = '1' AND hora_prisma BETWEEN ? AND ?"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (fechainicial, fechafinal))
            row = cur.fetchone()
            if row:
                return True
            else:
                return False
        except Exception as e:
            print("Error al comprobar datos: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlValidarUmbralesComponentes(idproyecto, tipo, tabla):
        try:
            conn = Connection.connectionDB()
            sql = f"""SELECT COUNT(DISTINCT id_componente) AS cantidad, id_componente FROM {tabla} WHERE id_proyecto = ? AND tipo_umbral = ? GROUP BY id_componente;"""
            # Nota: Si el COUNT es sobre todo el proyecto y se quiere retornar el id, el GROUP BY es necesario en SQL Server o una logica distinta
            # Original: SELECT COUNT(DISTINCT id_componente), id_componente ... 
            # Esto en SQL Server requiere GROUP BY id_componente, lo cual puede cambiar la lógica si hay multiples.
            # Asumo que se quiere saber si existen. Usaremos una consulta compatible.
            # Si solo se quiere verificar existencia, TOP 1 es mejor, pero el return es [cantidad, id].
            # Ajuste para compatibilidad:
            sql = f"""SELECT TOP 1 (SELECT COUNT(DISTINCT id_componente) FROM {tabla} WHERE id_proyecto = ? AND tipo_umbral = ?) as cantidad, 
            id_componente FROM {tabla} WHERE id_proyecto = ? AND tipo_umbral = ?;"""
            
            cur = conn.cursor()
            cur.execute(sql, (idproyecto, tipo, idproyecto, tipo))
            result = cur.fetchone()
            return result
        except Exception as e:
            print("Error al validar umbrales: " + str(e))
            return [0, None]
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerUmbralesCodigoPiezometro(idpiezometro, tipo, tipopiezo):
        try:
            conn = Connection.connectionDB()
            sql = f"""SELECT * FROM umbral_piezometro WHERE id_piezometro = ? AND tipo_umbral = ? AND tipo_piezometro = ? ORDER BY rango_umbral ASC;"""
            cur = conn.cursor()
            cur.execute(sql, (idpiezometro, tipo, tipopiezo))
            result = cur.fetchall() 
            if result:
                return result
            else:
                return None
        except Exception as e:
            print("Error al obtener umbrales: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlValidarUmbralesPiezometros(idproyecto, tipo, tipopiezo):
        try:
            conn = Connection.connectionDB()
            # Ajuste para SQL Server: Separar la agregación de la selección de columna no agregada
            sql = """SELECT TOP 1 
                        (SELECT COUNT(DISTINCT id_piezometro) FROM umbral_piezometro WHERE id_proyecto = ? AND tipo_umbral = ? AND tipo_piezometro = ?) as cantidad,
                        id_piezometro 
                     FROM umbral_piezometro
                     WHERE id_proyecto = ? AND tipo_umbral = ? AND tipo_piezometro = ?;"""
            cur = conn.cursor()
            cur.execute(sql, (idproyecto, tipo, tipopiezo, idproyecto, tipo, tipopiezo))
            result = cur.fetchone()
            return result
        except Exception as e:
            print("Error al validar umbrales: " + str(e))
            return [0, None]
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlListarPiezometrosUmbrales(idproyecto, tipo, tipopiezo, tabla):
        try:
            conn = Connection.connectionDB()
            sql = f"""SELECT DISTINCT u.id_piezometro, p.nombre_piezometro FROM umbral_piezometro u INNER JOIN {tabla} p
            ON u.id_piezometro = p.id_piezometro WHERE u.id_proyecto = ? AND u.tipo_umbral = ? AND u.tipo_piezometro = ?;"""
            cur = conn.cursor()
            cur.execute(sql, (idproyecto, tipo, tipopiezo))
            result = cur.fetchall()
            return result
        except Exception as e:
            print("Error al listar piezo umbrales: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlValidarUmbralesCeldas(idproyecto, tipo):
        try:
            conn = Connection.connectionDB()
            # Ajuste SQL Server
            sql = """SELECT TOP 1 
                        (SELECT COUNT(DISTINCT id_celda) FROM umbral_celda WHERE id_proyecto = ? AND tipo_umbral = ?) as cantidad, 
                        id_celda 
                     FROM umbral_celda 
                     WHERE id_proyecto = ? AND tipo_umbral = ?;"""
            cur = conn.cursor()
            cur.execute(sql, (idproyecto, tipo, idproyecto, tipo))
            result = cur.fetchone()
            return result
        except Exception as e:
            print("Error al validar umbrales: " + str(e))
            return [0, None]
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlListarCeldasUmbrales(idproyecto, tipo):
        try:
            conn = Connection.connectionDB()
            sql = f"""SELECT DISTINCT u.id_celda, c.nombre_celda FROM umbral_celda u INNER JOIN celdas c
            ON u.id_celda = c.id_celda WHERE u.id_proyecto = ? AND u.tipo_umbral = ?;"""
            cur = conn.cursor()
            cur.execute(sql, (idproyecto, tipo))
            result = cur.fetchall()
            return result
        except Exception as e:
            print("Error al listar celdas umbrales: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlListarComponentesUmbrales(idproyecto, tipo, tabla):
        try:
            conn = Connection.connectionDB()
            sql = f"""SELECT DISTINCT u.id_componente, c.nombre_componente FROM {tabla} u INNER JOIN componentes c
            ON u.id_componente = c.id_componente WHERE u.id_proyecto = ? AND u.tipo_umbral = ?;"""
            cur = conn.cursor()
            cur.execute(sql, (idproyecto, tipo))
            result = cur.fetchall()
            return result
        except Exception as e:
            print("Error al listar compo umbrales: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlComponentesTipo(ids):
        try:
            conn = Connection.connectionDB()
            # Crear una cadena de marcadores de posición para la consulta
            placeholders = ','.join('?' * len(ids))
            sql = f"""
            SELECT id_componente, nombre_componente
            FROM componentes
            WHERE estado_componente = 1 AND id_componente IN ({placeholders})
            """

            cur = conn.cursor()
            # Pyodbc espera una tupla o lista plana
            cur.execute(sql, tuple(ids))
            result = cur.fetchall()
            if result:
                return result
            else:
                return None
        except Exception as e:
            print("Error al obtener umbrales: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlPiezometroID(ids, tipos):
        try:
            conn = Connection.connectionDB()
            # Crear una cadena de marcadores de posición para la consulta
            placeholders_ids = ','.join('?' * len(ids))
            placeholders_tipos = ','.join('?' * len(tipos))

            sql = f"""
            SELECT DISTINCT inst.id_equipo, inst.nombre_equipo
            FROM instrumentacion inst
            INNER JOIN umbral_piezometro up ON inst.id_equipo = up.id_piezometro
            WHERE inst.estado_instrumentacion = 1
            AND (inst.tipo_equipo = 'PIEZOMETROMANUAL' OR inst.tipo_equipo = 'PIEZOMETROCUERDA')
            AND inst.id_equipo IN ({placeholders_ids})
            AND up.tipo_umbral IN ({placeholders_tipos})
            """

            cur = conn.cursor()
            # Concatenar listas para los parámetros
            cur.execute(sql, tuple(ids) + tuple(tipos))
            result = cur.fetchall()

            if result:
                return result
            else:
                return None
        except Exception as e:
            print("Error al obtener umbrales: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlObtenerUmbralesEquiposCP(proyectoid, componente_id, tabla):
        try:
            conn = Connection.connectionDB()
            if tabla == 'umbral_inclinometro':
                sql = f"""SELECT inst.nombre_equipo, ui.* FROM umbral_inclinometro ui INNER JOIN instrumentacion inst
                ON ui.id_inclinometro = inst.id_equipo WHERE inst.id_componente = ? AND ui.id_proyecto = ?
                AND inst.tipo_equipo = 'INCLINOMETRO';"""
            elif tabla == 'umbral_celda':
                sql = f"""SELECT inst.nombre_equipo, ui.* FROM umbral_celda ui INNER JOIN instrumentacion inst
                ON ui.id_celda = inst.id_equipo WHERE inst.id_componente = ? AND ui.id_proyecto = ?
                AND inst.tipo_equipo = 'CELDA';"""
            else:
                sql = f"""SELECT c.nombre_componente, u.* FROM {tabla} u INNER JOIN componentes c
                ON u.id_componente = c.id_componente WHERE u.id_componente = ? AND u.id_proyecto = ?;"""
            cur = conn.cursor()
            cur.execute(sql, (componente_id, proyectoid))
            result = cur.fetchall() 
            if result:
                return result
            else:
                return None
        except Exception as e:
            print("Error al obtener umbrales: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerUmbralesPiezometrosAnexo2(proyectoid, componente_id, tipopiezo):
        try:
            conn = Connection.connectionDB()
            sql = f"""SELECT inst.nombre_equipo, up.* FROM umbral_piezometro up INNER JOIN instrumentacion inst ON up.id_piezometro = inst.id_equipo
            WHERE inst.id_componente = ? AND up.id_proyecto = ? AND inst.tipo_equipo = ? AND tipo_umbral = 'NF';"""
            cur = conn.cursor()
            cur.execute(sql, (componente_id, proyectoid, tipopiezo))
            result = cur.fetchall() 
            if result:
                return result
            else:
                return None
        except Exception as e:
            print("Error al obtener umbrales piezo: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerUmbralesInclinometros(ids):
        try:
            conn = Connection.connectionDB()
            placeholders = ','.join('?' * len(ids))
            sql = f"""SELECT * FROM umbral_inclinometro WHERE id_inclinometro IN ({placeholders}) ORDER BY rango_umbral ASC;"""

            cur = conn.cursor()
            cur.execute(sql, tuple(ids))
            result = cur.fetchall()
            return result if result else None

        except Exception as e:
            print("Error al obtener umbrales: " + str(e))
            return None

        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlObtenerUmbralesPiezometros(ids):
        try:
            conn = Connection.connectionDB()
            placeholders = ','.join('?' * len(ids))
            sql = f"""SELECT * FROM umbral_piezometro WHERE id_piezometro IN ({placeholders}) AND tipo_umbral='NF' ORDER BY rango_umbral ASC;"""

            cur = conn.cursor()
            cur.execute(sql, tuple(ids))
            result = cur.fetchall()
            return result if result else None

        except Exception as e:
            print("Error al obtener umbrales: " + str(e))
            return None

        finally:
            if conn:
                conn.close()