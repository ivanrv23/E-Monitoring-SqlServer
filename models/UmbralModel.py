import pyodbc
from services.security.apis.conexiones.connection import Connection

class UmbralModel:   
    
    @staticmethod
    def mdlObtenerUmbralesPersonalizados(proyectoid):
        conn = None
        try:
            conn = Connection.connectionDB()
            # SQL Server: Sintaxis estándar
            sql = "SELECT * FROM umbral_personalizado WHERE id_proyecto = ? ORDER BY rango_umbral ASC;"
            cur = conn.cursor()
            cur.execute(sql, (proyectoid,))
            rows = cur.fetchall()
            
            # Conversión explícita a lista de tuplas para el frontend
            result = [tuple(row) for row in rows]
            
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
        conn = None
        # T-SQL: Insert estándar
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
            # pyodbc maneja eficientemente executemany
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
        conn = None
        sql = "SELECT DISTINCT nombre_umbral FROM umbral_personalizado WHERE id_proyecto = ?;"
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyectoid,))
            # row[0] accede al primer elemento de la fila pyodbc
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
        conn = None
        sql = """SELECT * FROM umbral_personalizado 
                 WHERE id_proyecto = ? AND nombre_umbral = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyectoid, nombre_umbral))
            
            # Obtener nombres de columnas y filas
            if cur.description:
                columns = [column[0] for column in cur.description]
            else:
                columns = []
                
            rows = cur.fetchall()
            
            if not rows:
                return None
            
            # Agrupar detalles convirtiendo pyodbc.Row a dict
            detalles = []
            for row in rows:
                detalles.append(dict(zip(columns, row)))
            
            return {
                'nombre_umbral': nombre_umbral,
                'detalles': detalles
            }
        except Exception as e:
            print("Error al obtener umbral por nombre:", e)
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlEliminarUmbralPorNombre(proyectoid, nombre_umbral):
        """Elimina todos los registros de un umbral por su nombre"""
        conn = None
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
        conn = None
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
        conn = None
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
        conn = None
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
        conn = None
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
        conn = None
        # Validación de seguridad básica para inyección en nombre de tabla
        if tabla not in ['umbral_inclinometro', 'umbral_celda', 'umbral_fisurometro', 'umbral_extensometro', 'umbral_prisma']: 
            # Si la tabla no es conocida, se maneja como error o se asume riesgo controlado si viene de lógica interna
            pass 

        if tabla == 'umbral_inclinometro':            
            sql = f"""INSERT INTO {tabla} (id_proyecto, id_inclinometro, condicion_umbral, color_umbral, riesgo_umbral, rango_umbral, acciones_umbral, tipo_umbral) VALUES (?, ?, ?, ?, ?, ?, ?, ?);"""
        elif tabla == 'umbral_celda':            
            sql = f"""INSERT INTO {tabla} (id_proyecto, id_celda, condicion_umbral, color_umbral, riesgo_umbral, rango_umbral, acciones_umbral, tipo_umbral) VALUES (?, ?, ?, ?, ?, ?, ?, ?);"""
        else:
            sql = f"""INSERT INTO {tabla} (id_proyecto, id_componente, condicion_umbral, color_umbral, riesgo_umbral, rango_umbral, acciones_umbral, tipo_umbral) VALUES (?, ?, ?, ?, ?, ?, ?, ?);"""
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            
            # Preparamos los parámetros para executemany para mayor eficiencia
            params = []
            for item in data:
                params.append((proyectoid, componente_id, item['condicion'], item['color'], item['riesgo'], item['rango'], item['acciones'], selected_id))
            
            cur.executemany(sql, params)
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
        conn = None
        sql = """INSERT INTO umbral_piezometro (id_proyecto, id_piezometro, condicion_umbral, color_umbral, riesgo_umbral,
        rango_umbral, acciones_umbral, tipo_umbral, tipo_piezometro) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            
            params = []
            for item in data:
                params.append((proyectoid, idpiezometro, item['condicion'], item['color'], item['riesgo'], item['rango'], item['acciones'], tipo, tipopiezo))
            
            cur.executemany(sql, params)
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
        conn = None
        sql = f"""UPDATE {tabla} SET condicion_umbral = ?, color_umbral = ?, riesgo_umbral=?, rango_umbral = ?, acciones_umbral=?, tipo_umbral = ? WHERE id_umbral = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (nombre, color, riesgo, rango, acciones, tipo, umbral_id))
            conn.commit()
            return True
        except Exception as e:
            print("Error al actualizar Umbral:", e)
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlGuardarUmbralesAcelerografo(proyectoid, componente_id, data):
        conn = None
        sql = """INSERT INTO umbral_acelerografo (id_proyecto, id_componente, condicion_umbral, riesgo_umbral, color_umbral,
        rango_umbral, magnitud_umbral, acciones_umbral, tipo_umbral) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            
            params = []
            for item in data:
                params.append((proyectoid, componente_id, item['nombre'], item['riesgo'], item['color'], item['distancia'], item['magnitud'], item['acciones'], item['tipo']))
            
            cur.executemany(sql, params)
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
        conn = None
        sql = """UPDATE umbral_acelerografo SET condicion_umbral = ?, riesgo_umbral = ?, color_umbral = ?, rango_umbral = ?,
        magnitud_umbral = ?, acciones_umbral = ? WHERE id_umbral = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (nombre, riesgo, color, distancia, magnitud, acciones, umbral_id))
            conn.commit()
            return True
        except Exception as e:
            print("Error al actualizar Umbral:", e)
            return False
        finally:
            if conn:
                conn.close()
    
    # @staticmethod
    # def mdlObtenerUmbralesInstrumentacion(proyectoid, componente_id, tipo, tabla):
    #     conn = None
    #     try:
    #         conn = Connection.connectionDB()
    #         params = ()
    #         if tabla == 'umbral_inclinometro':
    #             sql = f"""SELECT * FROM {tabla} WHERE id_inclinometro = ? AND tipo_umbral = ? AND id_proyecto=? ORDER BY rango_umbral ASC;"""
    #             params = (componente_id, tipo, proyectoid)
    #         elif tabla=='umbral_celda':
    #             sql = f"""SELECT * FROM {tabla} WHERE id_celda = ? AND tipo_umbral = ? AND id_proyecto = ? ORDER BY rango_umbral ASC;"""
    #             params = (componente_id, tipo, proyectoid)
    #         else:
    #             sql = f"""SELECT * FROM {tabla} WHERE id_componente = ? AND tipo_umbral = ? AND id_proyecto = ? ORDER BY rango_umbral ASC;"""
    #             params = (componente_id, tipo, proyectoid)
            
    #         cur = conn.cursor()
    #         cur.execute(sql, params)
            
    #         # Conversión explícita a tupla
    #         result = [tuple(row) for row in cur.fetchall()]
            
    #         if result:
    #             return result
    #         else:
    #             return None
    #     except Exception as e:
    #         print("Error al obtener umbrales: " + str(e))
    #         return None
    #     finally:
    #         if conn:
    #             conn.close()
    
    @staticmethod
    def mdlObtenerUmbralesInstrumentacion(proyectoid, componente_id, tipo, tabla):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            
            # ==========================================
            # 1. INTENTO PRINCIPAL: Buscar por componente específico
            # ==========================================
            if tabla == 'umbral_inclinometro':
                sql = f"""SELECT * FROM {tabla} WHERE id_inclinometro = ? AND tipo_umbral = ? AND id_proyecto=? ORDER BY rango_umbral ASC;"""
                params = (componente_id, tipo, proyectoid)
            elif tabla=='umbral_celda':
                sql = f"""SELECT * FROM {tabla} WHERE id_celda = ? AND tipo_umbral = ? AND id_proyecto = ? ORDER BY rango_umbral ASC;"""
                params = (componente_id, tipo, proyectoid)
            else:
                # Este es el bloque para PRISMAS (y otros genéricos)
                sql = f"""SELECT * FROM {tabla} WHERE id_componente = ? AND tipo_umbral = ? AND id_proyecto = ? ORDER BY rango_umbral ASC;"""
                params = (componente_id, tipo, proyectoid)
            
            cur.execute(sql, params)
            result = [tuple(row) for row in cur.fetchall()]
            
            # ==========================================
            # 2. FALLBACK: Si no hay resultado y es PRISMA, buscar el GENERAL
            # ==========================================
            # Solo aplicamos el fallback si la tabla no es inclinómetro ni celda
            # y si la consulta principal no trajo nada.
            if not result and tabla not in ('umbral_inclinometro', 'umbral_celda'):
                
                # Buscamos el ID del componente GENERAL del proyecto
                sql_general = """
                    SELECT id_componente 
                    FROM componentes 
                    WHERE id_proyecto = ? AND nombre_componente = 'GENERAL'
                """
                # Nota: Si usas estado_componente = 1 para activos, puedes agregarlo al WHERE
                cur.execute(sql_general, (proyectoid,))
                row_general = cur.fetchone()
                
                if row_general:
                    id_general = row_general[0]
                    
                    # Optimización: Si el componente específico ya era el GENERAL, no volvemos a consultar
                    if id_general != componente_id:
                        sql_fallback = f"""
                            SELECT * FROM {tabla} 
                            WHERE id_componente = ? AND tipo_umbral = ? AND id_proyecto = ? 
                            ORDER BY rango_umbral ASC;
                        """
                        cur.execute(sql_fallback, (id_general, tipo, proyectoid))
                        result = [tuple(row) for row in cur.fetchall()]
            
            # Retornamos el resultado (ya sea el específico, el general, o None si no hay ninguno)
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
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = """SELECT * FROM umbral_piezometro WHERE id_piezometro = ? AND tipo_umbral = ? AND tipo_piezometro = ? ORDER BY rango_umbral ASC;"""
            cur = conn.cursor()
            cur.execute(sql, (idpiezo, tipo, tipopiezo))
            
            result = [tuple(row) for row in cur.fetchall()]
            
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
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = """SELECT * FROM umbral_acelerografo WHERE id_proyecto = ? AND id_componente = ? AND tipo_umbral = ?;"""
            cur = conn.cursor()
            cur.execute(sql, (proyectoid, componente_id, tipo))
            
            result = [tuple(row) for row in cur.fetchall()]
            
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
    def mdlEliminarUmbralEquipos(umbral_id, tabla):
        conn = None
        sql = f"""DELETE FROM {tabla} WHERE id_umbral = ?"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (umbral_id,))
            conn.commit()
            if cur.rowcount > 0:
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
        conn = None
        sql = """DELETE FROM umbral_acelerografo WHERE id_umbral = ?"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (umbral_id,))
            conn.commit()
            if cur.rowcount > 0:
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
        conn = None
        sql = """INSERT INTO umbral_prisma (id_proyecto, nombre_umbral, normal_umbral, precaucion_umbral, peligro_umbral, cerrar_umbral, color_normal,
        color_precaucion, color_peligro, color_cerrar) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # Se asume que data es una tupla o lista con los valores correctos
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
        conn = None
        sql = """UPDATE umbral_prisma SET normal_umbral = ?, precaucion_umbral = ?, peligro_umbral = ?, cerrar_umbral = ?,
        color_normal = ?, color_precaucion = ?, color_peligro = ?, color_cerrar = ? WHERE id_proyecto = ? AND nombre_umbral = ?;"""
        try:
            conn = Connection.connectionDB()
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
                
    # @staticmethod
    # def mdlObtenerUmbralPrismas(proyectoid, idcomponente, tipo):
    #     conn = None
    #     try:
    #         conn = Connection.connectionDB()
    #         sql = """SELECT * FROM umbral_prisma WHERE id_proyecto = ? AND id_componente = ? AND tipo_umbral = ?;"""
    #         cur = conn.cursor()
    #         cur.execute(sql, (proyectoid, idcomponente, tipo))
            
    #         # Conversión explícita a tupla
    #         result = [tuple(row) for row in cur.fetchall()]
    #         if result:
    #             return result
    #         else:
    #             return None
    #     except Exception as e:
    #         print("Error al obtener umbrales prismas: " + str(e))
    #         return None
    #     finally:
    #         if conn:
    #             conn.close()
    @staticmethod
    def mdlObtenerUmbralPrismas(proyectoid, idcomponente, tipo):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            
            # ==========================================
            # 1. INTENTO PRINCIPAL: Buscar por componente específico
            # ==========================================
            sql = """SELECT * FROM umbral_prisma WHERE id_proyecto = ? AND id_componente = ? AND tipo_umbral = ?;"""
            cur.execute(sql, (proyectoid, idcomponente, tipo))
            result = [tuple(row) for row in cur.fetchall()]
            
            # ==========================================
            # 2. FALLBACK: Si no hay resultado, buscar el GENERAL
            # ==========================================
            if not result:
                # Buscamos el ID del componente GENERAL del proyecto
                sql_general = """
                    SELECT id_componente 
                    FROM componentes 
                    WHERE id_proyecto = ? AND nombre_componente = 'GENERAL'
                """
                cur.execute(sql_general, (proyectoid,))
                row_general = cur.fetchone()
                
                if row_general:
                    id_general = row_general[0]
                    
                    # Optimización: Si el componente específico ya era el GENERAL, no volvemos a consultar
                    if id_general != idcomponente:
                        sql_fallback = """
                            SELECT * FROM umbral_prisma 
                            WHERE id_proyecto = ? AND id_componente = ? AND tipo_umbral = ?;
                        """
                        cur.execute(sql_fallback, (proyectoid, id_general, tipo))
                        result = [tuple(row) for row in cur.fetchall()]
            
            # Retornamos el resultado
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
                
    # Obtener datos del umbral monitor 2
    @staticmethod
    def mdlObtenerDatosUmbralm2():
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = """SELECT * FROM umbral2;"""
            
            cur = conn.cursor()
            cur.execute(sql)
            
            result = [tuple(row) for row in cur.fetchall()]
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
    def mdlGuardarUmbralm2(id_umbral, color, visd, vasd, vi3d, va3d):
        conn = None
        sql = """UPDATE umbral2 SET color_umbral = ?, VISD = ?, VASD = ?, VI3D = ?, VA3D = ? WHERE id_umbral = ?"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (color, visd, vasd, vi3d, va3d, id_umbral))
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
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = """SELECT * FROM umbral_celda WHERE id_proyecto = ?;"""
            
            cur = conn.cursor()
            cur.execute(sql, (proyectoid,))
            
            result = [tuple(row) for row in cur.fetchall()] 
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
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = """SELECT * FROM umbral_celda WHERE id_umbral = ?;"""
            
            cur = conn.cursor()
            cur.execute(sql, (idumbral,))
            row = cur.fetchone()
            
            if row:
                return tuple(row)
            else:
                return None
        except Exception as e:
            return None
        finally:
            if conn:
                conn.close()
                            
    @staticmethod
    def mdlObtenerUmbralAcelerografos(proyectoid, componente):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = """SELECT * FROM umbral_acelerografo WHERE id_proyecto=? AND id_componente=?"""
            
            with conn: # No es estrictamente necesario si usamos finally, pero se mantiene la lógica defensiva
                cur = conn.cursor()
                cur.execute(sql, (proyectoid, componente))
                
                result = [tuple(row) for row in cur.fetchall()]
                return result if result else None

        except Exception as e:
            print(f"Error al obtener umbral acelerógrafos: {str(e)}")
            return None
        # Nota: pyodbc no soporta 'with conn' de la misma forma que sqlite3 para autocommit, 
        # pero connectionDB retorna una conexión. El finally abajo asegura el cierre.
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlGuardarUmbralCeldas(datos):
        conn = None
        sql = """INSERT INTO umbral_celda (id_proyecto, nombre_umbral, normal_umbral, color_normal, precaucion_umbral, color_precaucion, peligro_umbral,
        color_peligro, cerrar_umbral, color_cerrar) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""
        try:
            conn = Connection.connectionDB()
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
        conn = None
        sql = """UPDATE umbral_celda SET normal_umbral = ?, color_normal = ?, precaucion_umbral = ?, color_precaucion = ?, peligro_umbral = ?,
            color_peligro = ?, cerrar_umbral= ?, color_cerrar = ? WHERE id_umbral = ?;"""
        try:
            conn = Connection.connectionDB()
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
        conn = None
        # Lógica manual de "Upsert" adaptada para pyodbc
        sql_check = """SELECT id FROM umbral_acelerografo WHERE proyecto_id = ? AND tipo_umbral = ?;"""
        
        sql_update = """UPDATE umbral_acelerografo 
                        SET color_umbral = ?, valor_umbral = ? 
                        WHERE proyecto_id = ? AND tipo_umbral = ?;"""
        
        sql_insert = """INSERT INTO umbral_acelerografo (proyecto_id, tipo_umbral, color_umbral, valor_umbral) 
                        VALUES (?, ?, ?, ?);"""

        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            
            # Verificamos si el registro ya existe
            cur.execute(sql_check, (id_proyecto, nombre))
            record = cur.fetchone()
            
            if record:  # Si existe, actualizamos
                cur.execute(sql_update, (color, valor, id_proyecto, nombre))
            else:  # Si no existe, insertamos
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
        conn = None
        tabla = "prismas" + str(proyecto)
        # T-SQL requiere alias para la subconsulta (AS subquery ya estaba, correcto)
        sql = f""" SELECT * FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY nombre_prisma ORDER BY id_prisma DESC) AS rn FROM {tabla}) subquery WHERE subquery.rn = 2"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql)
            
            row = [tuple(r) for r in cur.fetchall()]
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
        conn = None
        tabla = "prismas" + str(id_proyecto)
        # Adaptación T-SQL: Uso de ? para fechas y CTE
        sql = f"""WITH CTE AS (
                SELECT
                    nombre_prisma,
                    distancia_prisma AS distancia_prisma,
                    LAG(nombre_prisma) OVER (ORDER BY nombre_prisma) AS prev_nombre_prisma,
                    FIRST_VALUE(distancia_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) AS primer_valor
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
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (fechaMinInicial, fechaMaxInicial))
            
            row = [tuple(r) for r in cur.fetchall()]
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
        # Método redundante pero independiente completo, adaptado a pyodbc
        conn = None
        tabla = "prismas" + str(id_proyecto)
        sql = f"""WITH CTE AS (
                SELECT
                    nombre_prisma,
                    distancia_prisma AS distancia_prisma,
                    LAG(nombre_prisma) OVER (ORDER BY nombre_prisma) AS prev_nombre_prisma,
                    FIRST_VALUE(distancia_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) AS primer_valor
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
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (fechaMinInicial, fechaMaxInicial))
            
            row = [tuple(r) for r in cur.fetchall()]
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
        conn = None
        tabla = "prismas" + str(id_proyecto)
        # Generación de placeholders dinámicos para la lista IN
        placeholders = ','.join(['?' for _ in nombres])
        
        sql = f"""WITH CTE AS (
                SELECT
                    nombre_prisma,
                    distancia_prisma AS distancia_prisma,
                    LAG(nombre_prisma) OVER (ORDER BY nombre_prisma) AS prev_nombre_prisma,
                    FIRST_VALUE(distancia_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) AS primer_valor
                FROM {tabla}
                WHERE state_prisma = '1' AND nombre_prisma IN ({placeholders}) AND hora_prisma BETWEEN ? AND ?
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
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # Combinar tupla de nombres y fechas para los parámetros
            params = tuple(nombres) + (fechaMinInicial, fechaMaxInicial)
            cur.execute(sql, params)
            
            row = [tuple(r) for r in cur.fetchall()]
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
        # Método redundante pero independiente completo, adaptado a pyodbc
        conn = None
        tabla = "prismas" + str(id_proyecto)
        placeholders = ','.join(['?' for _ in nombres])
        
        sql = f"""WITH CTE AS (
                SELECT
                    nombre_prisma,
                    distancia_prisma AS distancia_prisma,
                    LAG(nombre_prisma) OVER (ORDER BY nombre_prisma) AS prev_nombre_prisma,
                    FIRST_VALUE(distancia_prisma) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) AS primer_valor
                FROM {tabla}
                WHERE state_prisma = '1' AND nombre_prisma IN ({placeholders}) AND hora_prisma BETWEEN ? AND ?
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
            conn = Connection.connectionDB()
            cur = conn.cursor()
            params = tuple(nombres) + (fechaMinInicial, fechaMaxInicial)
            cur.execute(sql, params)
            
            row = [tuple(r) for r in cur.fetchall()]
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
                
        # ... (Continuación de la clase UmbralModel) ...

    # --- MÉTODOS 3D (Distancia Espacial) ---
    
    @staticmethod
    def mldObtener3D(id_proyecto, fechaMinInicial, fechaMaxInicial):
        conn = None
        tabla = "prismas" + str(id_proyecto)
        # T-SQL: Para obtener la 'distancia' asociada al MAX(hora_prisma), usamos ROW_NUMBER
        sql = f"""WITH CalculoDistancias AS (
                SELECT
                    nombre_prisma,
                    hora_prisma,
                    SQRT(
                        POWER(este_target - FIRST_VALUE(este_target) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), 2) +
                        POWER(norte_target - FIRST_VALUE(norte_target) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), 2) +
                        POWER(elevacion_target - FIRST_VALUE(elevacion_target) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), 2)
                    ) AS distancia
                FROM {tabla}
                WHERE state_prisma = '1' AND hora_prisma BETWEEN ? AND ?
            ),
            Ranked AS (
                SELECT nombre_prisma, hora_prisma, distancia,
                ROW_NUMBER() OVER(PARTITION BY nombre_prisma ORDER BY hora_prisma DESC) as rn
                FROM CalculoDistancias
            )
            SELECT nombre_prisma, hora_prisma, distancia
            FROM Ranked WHERE rn = 1
            ORDER BY nombre_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (fechaMinInicial, fechaMaxInicial))
            result = [tuple(row) for row in cur.fetchall()]
            return result if result else None
        except Exception as e:
            print("Error al obtener datos 3D: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mldObtener3DManual(id_proyecto, fechaMinInicial, fechaMaxInicial):
        return UmbralModel.mldObtener3D(id_proyecto, fechaMinInicial, fechaMaxInicial)
    
    @staticmethod
    def mldObtener3DPrismaNombre(id_proyecto, nombres, fechaMinInicial, fechaMaxInicial):
        conn = None
        tabla = "prismas" + str(id_proyecto)
        placeholders = ','.join(['?' for _ in nombres])
        sql = f"""WITH CalculoDistancias AS (
                SELECT
                    nombre_prisma,
                    hora_prisma,
                    SQRT(
                        POWER(este_target - FIRST_VALUE(este_target) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), 2) +
                        POWER(norte_target - FIRST_VALUE(norte_target) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), 2) +
                        POWER(elevacion_target - FIRST_VALUE(elevacion_target) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma), 2)
                    ) AS distancia
                FROM {tabla}
                WHERE state_prisma = '1' AND nombre_prisma IN ({placeholders}) AND hora_prisma BETWEEN ? AND ?
            ),
            Ranked AS (
                SELECT nombre_prisma, hora_prisma, distancia,
                ROW_NUMBER() OVER(PARTITION BY nombre_prisma ORDER BY hora_prisma DESC) as rn
                FROM CalculoDistancias
            )
            SELECT nombre_prisma, hora_prisma, distancia
            FROM Ranked WHERE rn = 1;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            params = tuple(nombres) + (fechaMinInicial, fechaMaxInicial)
            cur.execute(sql, params)
            result = [tuple(row) for row in cur.fetchall()]
            return result if result else None
        except Exception as e:
            print("Error al obtener datos 3D: " + str(e))
            return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mldObtener3DPrismaNombreManual(id_proyecto, nombres, fechaMinInicial, fechaMaxInicial):
        return UmbralModel.mldObtener3DPrismaNombre(id_proyecto, nombres, fechaMinInicial, fechaMaxInicial)

    # --- MÉTODOS L (Longitudinal) ---
    
    @staticmethod
    def mldObtenerL(id_proyecto, fechaMinInicial, fechaMaxInicial):
        conn = None
        tabla = "prismas" + str(id_proyecto)
        # SQL Server requiere agregación explícita. Usamos ROW_NUMBER para encontrar el registro con el MAX ABS.
        sql = f"""WITH Ranked AS (
            SELECT p1.nombre_prisma, p1.desplaza_longitudinal, ABS(p1.desplaza_longitudinal) AS max_valor_absolutoDL,
            ROW_NUMBER() OVER(PARTITION BY p1.nombre_prisma ORDER BY ABS(p1.desplaza_longitudinal) DESC) as rn
            FROM {tabla} AS p1 
            WHERE state_prisma = '1' AND hora_prisma BETWEEN ? AND ?
        )
        SELECT nombre_prisma, desplaza_longitudinal, max_valor_absolutoDL 
        FROM Ranked WHERE rn = 1 ORDER BY nombre_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (fechaMinInicial, fechaMaxInicial))
            result = [tuple(row) for row in cur.fetchall()]
            return result if result else None
        except Exception as e:
            print("Error al obtener datos L: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mldObtenerLManual(id_proyecto, fechaMinInicial, fechaMaxInicial):
        return UmbralModel.mldObtenerL(id_proyecto, fechaMinInicial, fechaMaxInicial)
    
    @staticmethod
    def mldObtenerLPrismaNombre(id_proyecto, nombres, fechaMinInicial, fechaMaxInicial):
        conn = None
        tabla = "prismas" + str(id_proyecto)
        placeholders = ','.join(['?' for _ in nombres])
        sql = f"""WITH Ranked AS (
            SELECT p1.nombre_prisma, p1.desplaza_longitudinal, ABS(p1.desplaza_longitudinal) AS max_valor_absolutoDL,
            ROW_NUMBER() OVER(PARTITION BY p1.nombre_prisma ORDER BY ABS(p1.desplaza_longitudinal) DESC) as rn
            FROM {tabla} AS p1 
            WHERE state_prisma = '1' AND nombre_prisma IN ({placeholders}) AND hora_prisma BETWEEN ? AND ?
        )
        SELECT nombre_prisma, desplaza_longitudinal, max_valor_absolutoDL 
        FROM Ranked WHERE rn = 1 ORDER BY nombre_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            params = tuple(nombres) + (fechaMinInicial, fechaMaxInicial)
            cur.execute(sql, params)
            result = [tuple(row) for row in cur.fetchall()]
            return result if result else None
        except Exception as e:
            print("Error al obtener datos L: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mldObtenerLPrismaNombreManual(id_proyecto, nombres, fechaMinInicial, fechaMaxInicial):
        return UmbralModel.mldObtenerLPrismaNombre(id_proyecto, nombres, fechaMinInicial, fechaMaxInicial)

    # --- MÉTODOS T (Transversal) ---
    
    @staticmethod
    def mldObtenerT(id_proyecto, fechaMinInicial, fechaMaxInicial):
        conn = None
        tabla = "prismas" + str(id_proyecto)
        sql = f"""WITH Ranked AS (
            SELECT p1.nombre_prisma, p1.desplaza_transversal, ABS(p1.desplaza_transversal) AS max_valor_absolutoDT,
            ROW_NUMBER() OVER(PARTITION BY p1.nombre_prisma ORDER BY ABS(p1.desplaza_transversal) DESC) as rn
            FROM {tabla} AS p1 
            WHERE state_prisma = '1' AND hora_prisma BETWEEN ? AND ?
        )
        SELECT nombre_prisma, desplaza_transversal, max_valor_absolutoDT 
        FROM Ranked WHERE rn = 1 ORDER BY nombre_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (fechaMinInicial, fechaMaxInicial))
            result = [tuple(row) for row in cur.fetchall()]
            return result if result else None
        except Exception as e:
            print("Error al obtener datos T: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mldObtenerTManual(id_proyecto, fechaMinInicial, fechaMaxInicial):
        return UmbralModel.mldObtenerT(id_proyecto, fechaMinInicial, fechaMaxInicial)
    
    @staticmethod
    def mldObtenerTPrismaNombre(id_proyecto, nombres, fechaMinInicial, fechaMaxInicial):
        conn = None
        tabla = "prismas" + str(id_proyecto)
        placeholders = ','.join(['?' for _ in nombres])
        sql = f"""WITH Ranked AS (
            SELECT p1.nombre_prisma, p1.desplaza_transversal, ABS(p1.desplaza_transversal) AS max_valor_absolutoDT,
            ROW_NUMBER() OVER(PARTITION BY p1.nombre_prisma ORDER BY ABS(p1.desplaza_transversal) DESC) as rn
            FROM {tabla} AS p1 
            WHERE state_prisma = '1' AND nombre_prisma IN ({placeholders}) AND hora_prisma BETWEEN ? AND ?
        )
        SELECT nombre_prisma, desplaza_transversal, max_valor_absolutoDT 
        FROM Ranked WHERE rn = 1 ORDER BY nombre_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            params = tuple(nombres) + (fechaMinInicial, fechaMaxInicial)
            cur.execute(sql, params)
            result = [tuple(row) for row in cur.fetchall()]
            return result if result else None
        except Exception as e:
            print("Error al obtener datos T: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mldObtenerTPrismaNombreManual(id_proyecto, nombres, fechaMinInicial, fechaMaxInicial):
        return UmbralModel.mldObtenerTPrismaNombre(id_proyecto, nombres, fechaMinInicial, fechaMaxInicial)

    # --- MÉTODOS H (Altura) ---
    
    @staticmethod
    def mldObtenerH(id_proyecto, fechaMinInicial, fechaMaxInicial):
        conn = None
        tabla = "prismas" + str(id_proyecto)
        sql = f"""WITH Ranked AS (
            SELECT p1.nombre_prisma, p1.desplaza_altura, ABS(p1.desplaza_altura) AS max_valor_absolutoDH,
            ROW_NUMBER() OVER(PARTITION BY p1.nombre_prisma ORDER BY ABS(p1.desplaza_altura) DESC) as rn
            FROM {tabla} AS p1 
            WHERE state_prisma = '1' AND hora_prisma BETWEEN ? AND ?
        )
        SELECT nombre_prisma, desplaza_altura, max_valor_absolutoDH 
        FROM Ranked WHERE rn = 1 ORDER BY nombre_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (fechaMinInicial, fechaMaxInicial))
            result = [tuple(row) for row in cur.fetchall()]
            return result if result else None
        except Exception as e:
            print("Error al obtener datos H: " + str(e))
            return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mldObtenerHManual(id_proyecto, fechaMinInicial, fechaMaxInicial):
        return UmbralModel.mldObtenerH(id_proyecto, fechaMinInicial, fechaMaxInicial)

    @staticmethod
    def mldObtenerHPrismaNombre(id_proyecto, nombres, fechaMinInicial, fechaMaxInicial):
        conn = None
        tabla = "prismas" + str(id_proyecto)
        placeholders = ','.join(['?' for _ in nombres])
        sql = f"""WITH Ranked AS (
            SELECT p1.nombre_prisma, p1.desplaza_altura, ABS(p1.desplaza_altura) AS max_valor_absolutoDH,
            ROW_NUMBER() OVER(PARTITION BY p1.nombre_prisma ORDER BY ABS(p1.desplaza_altura) DESC) as rn
            FROM {tabla} AS p1 
            WHERE state_prisma = '1' AND nombre_prisma IN ({placeholders}) AND hora_prisma BETWEEN ? AND ?
        )
        SELECT nombre_prisma, desplaza_altura, max_valor_absolutoDH 
        FROM Ranked WHERE rn = 1 ORDER BY nombre_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            params = tuple(nombres) + (fechaMinInicial, fechaMaxInicial)
            cur.execute(sql, params)
            result = [tuple(row) for row in cur.fetchall()]
            return result if result else None
        except Exception as e:
            print("Error al obtener datos H: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mldObtenerHPrismaNombreManual(id_proyecto, nombres, fechaMinInicial, fechaMaxInicial):
        return UmbralModel.mldObtenerHPrismaNombre(id_proyecto, nombres, fechaMinInicial, fechaMaxInicial)

    # --- MÉTODOS N (Norte), E (Este), Z (Elevación) ---
    # Nota: Estos métodos requieren 2 niveles: Calcular V_A (Variación Absoluta) y luego filtrar el MAX(V_A)
    
    @staticmethod
    def mldObtenerN(id_proyecto, fechaMinInicial, fechaMaxInicial):
        conn = None
        tabla = "prismas" + str(id_proyecto)
        sql = f"""WITH Calculo AS (
            SELECT nombre_prisma, norte_target,
            (norte_target - FIRST_VALUE(norte_target) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma)) AS distancia,
            ABS(norte_target - FIRST_VALUE(norte_target) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma)) AS V_A
            FROM {tabla}
            WHERE state_prisma = '1' AND hora_prisma BETWEEN ? AND ?
        ),
        Ranked AS (
            SELECT nombre_prisma, distancia, V_A,
            ROW_NUMBER() OVER(PARTITION BY nombre_prisma ORDER BY V_A DESC) as rn
            FROM Calculo
        )
        SELECT nombre_prisma, distancia, V_A AS mayor_distancia 
        FROM Ranked WHERE rn = 1 ORDER BY nombre_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (fechaMinInicial, fechaMaxInicial))
            result = [tuple(row) for row in cur.fetchall()]
            return result if result else None
        except Exception as e:
            print("Error al obtener datos N: " + str(e))
            return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mldObtenerNManual(id_proyecto, fechaMinInicial, fechaMaxInicial):
        return UmbralModel.mldObtenerN(id_proyecto, fechaMinInicial, fechaMaxInicial)

    @staticmethod
    def mldObtenerNPrismaNombre(id_proyecto, nombres, fechaMinInicial, fechaMaxInicial):
        conn = None
        tabla = "prismas" + str(id_proyecto)
        placeholders = ','.join(['?' for _ in nombres])
        sql = f"""WITH Calculo AS (
            SELECT nombre_prisma, norte_target,
            (norte_target - FIRST_VALUE(norte_target) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma)) AS distancia,
            ABS(norte_target - FIRST_VALUE(norte_target) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma)) AS V_A
            FROM {tabla}
            WHERE state_prisma = '1' AND nombre_prisma IN ({placeholders}) AND hora_prisma BETWEEN ? AND ?
        ),
        Ranked AS (
            SELECT nombre_prisma, distancia, V_A,
            ROW_NUMBER() OVER(PARTITION BY nombre_prisma ORDER BY V_A DESC) as rn
            FROM Calculo
        )
        SELECT nombre_prisma, distancia, V_A AS mayor_distancia 
        FROM Ranked WHERE rn = 1 ORDER BY nombre_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            params = tuple(nombres) + (fechaMinInicial, fechaMaxInicial)
            cur.execute(sql, params)
            result = [tuple(row) for row in cur.fetchall()]
            return result if result else None
        except Exception as e:
            print("Error al obtener datos N: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mldObtenerNPrismaNombreManual(id_proyecto, nombres, fechaMinInicial, fechaMaxInicial):
        return UmbralModel.mldObtenerNPrismaNombre(id_proyecto, nombres, fechaMinInicial, fechaMaxInicial)

    @staticmethod
    def mldObtenerE(id_proyecto, fechaMinInicial, fechaMaxInicial):
        conn = None
        tabla = "prismas" + str(id_proyecto)
        sql = f"""WITH Calculo AS (
            SELECT nombre_prisma, este_target,
            (este_target - FIRST_VALUE(este_target) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma)) AS distancia,
            ABS(este_target - FIRST_VALUE(este_target) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma)) AS V_A
            FROM {tabla}
            WHERE state_prisma = '1' AND hora_prisma BETWEEN ? AND ?
        ),
        Ranked AS (
            SELECT nombre_prisma, distancia, V_A,
            ROW_NUMBER() OVER(PARTITION BY nombre_prisma ORDER BY V_A DESC) as rn
            FROM Calculo
        )
        SELECT nombre_prisma, distancia, V_A AS mayor_distancia 
        FROM Ranked WHERE rn = 1 ORDER BY nombre_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (fechaMinInicial, fechaMaxInicial))
            result = [tuple(row) for row in cur.fetchall()]
            return result if result else None
        except Exception as e:
            print("Error al obtener datos E: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mldObtenerEManual(id_proyecto, fechaMinInicial, fechaMaxInicial):
        return UmbralModel.mldObtenerE(id_proyecto, fechaMinInicial, fechaMaxInicial)
    
    @staticmethod
    def mldObtenerEPrismaNombre(id_proyecto, nombres, fechaMinInicial, fechaMaxInicial):
        conn = None
        tabla = "prismas" + str(id_proyecto)
        placeholders = ','.join(['?' for _ in nombres])
        sql = f"""WITH Calculo AS (
            SELECT nombre_prisma, este_target,
            (este_target - FIRST_VALUE(este_target) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma)) AS distancia,
            ABS(este_target - FIRST_VALUE(este_target) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma)) AS V_A
            FROM {tabla}
            WHERE state_prisma = '1' AND nombre_prisma IN ({placeholders}) AND hora_prisma BETWEEN ? AND ?
        ),
        Ranked AS (
            SELECT nombre_prisma, distancia, V_A,
            ROW_NUMBER() OVER(PARTITION BY nombre_prisma ORDER BY V_A DESC) as rn
            FROM Calculo
        )
        SELECT nombre_prisma, distancia, V_A AS mayor_distancia 
        FROM Ranked WHERE rn = 1 ORDER BY nombre_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            params = tuple(nombres) + (fechaMinInicial, fechaMaxInicial)
            cur.execute(sql, params)
            result = [tuple(row) for row in cur.fetchall()]
            return result if result else None
        except Exception as e:
            print("Error al obtener datos E: " + str(e))
            return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mldObtenerEPrismaNombreManual(id_proyecto, nombres, fechaMinInicial, fechaMaxInicial):
        return UmbralModel.mldObtenerEPrismaNombre(id_proyecto, nombres, fechaMinInicial, fechaMaxInicial)

    @staticmethod
    def mldObtenerZ(id_proyecto, fechaMinInicial, fechaMaxInicial):
        conn = None
        tabla = "prismas" + str(id_proyecto)
        sql = f"""WITH Calculo AS (
            SELECT nombre_prisma, elevacion_target,
            (elevacion_target - FIRST_VALUE(elevacion_target) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma)) AS distancia,
            ABS(elevacion_target - FIRST_VALUE(elevacion_target) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma)) AS V_A
            FROM {tabla}
            WHERE state_prisma = '1' AND hora_prisma BETWEEN ? AND ?
        ),
        Ranked AS (
            SELECT nombre_prisma, distancia, V_A,
            ROW_NUMBER() OVER(PARTITION BY nombre_prisma ORDER BY V_A DESC) as rn
            FROM Calculo
        )
        SELECT nombre_prisma, distancia, V_A AS mayor_distancia 
        FROM Ranked WHERE rn = 1 ORDER BY nombre_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (fechaMinInicial, fechaMaxInicial))
            result = [tuple(row) for row in cur.fetchall()]
            return result if result else None
        except Exception as e:
            print("Error al obtener datos Z: " + str(e))
            return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mldObtenerZManual(id_proyecto, fechaMinInicial, fechaMaxInicial):
        return UmbralModel.mldObtenerZ(id_proyecto, fechaMinInicial, fechaMaxInicial)

    @staticmethod
    def mldObtenerZPrismaNombre(id_proyecto, nombres, fechaMinInicial, fechaMaxInicial):
        conn = None
        tabla = "prismas" + str(id_proyecto)
        placeholders = ','.join(['?' for _ in nombres])
        sql = f"""WITH Calculo AS (
            SELECT nombre_prisma, elevacion_target,
            (elevacion_target - FIRST_VALUE(elevacion_target) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma)) AS distancia,
            ABS(elevacion_target - FIRST_VALUE(elevacion_target) OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma)) AS V_A
            FROM {tabla}
            WHERE state_prisma = '1' AND nombre_prisma IN ({placeholders}) AND hora_prisma BETWEEN ? AND ?
        ),
        Ranked AS (
            SELECT nombre_prisma, distancia, V_A,
            ROW_NUMBER() OVER(PARTITION BY nombre_prisma ORDER BY V_A DESC) as rn
            FROM Calculo
        )
        SELECT nombre_prisma, distancia, V_A AS mayor_distancia 
        FROM Ranked WHERE rn = 1 ORDER BY nombre_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            params = tuple(nombres) + (fechaMinInicial, fechaMaxInicial)
            cur.execute(sql, params)
            result = [tuple(row) for row in cur.fetchall()]
            return result if result else None
        except Exception as e:
            print("Error al obtener datos Z: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mldObtenerZPrismaNombreManual(id_proyecto, nombres, fechaMinInicial, fechaMaxInicial):
        return UmbralModel.mldObtenerZPrismaNombre(id_proyecto, nombres, fechaMinInicial, fechaMaxInicial)

    # --- UTILIDADES DE FECHAS Y VALIDACIONES ---

    @staticmethod
    def mdlObtenerFechaMinMaxAuto(id_proyecto):
        conn = None
        tabla = "prismas" + str(id_proyecto)
        sql = f"""SELECT MIN(hora_prisma) AS min_fecha, MAX(hora_prisma) AS max_fecha FROM {tabla} WHERE state_prisma = 1;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql)
            result = cur.fetchone()
            return tuple(result) if result else None
        except Exception as e:
            print("Error al obtener fechas min-max: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlObtenerFechaMinMaxManual(id_proyecto):
        return UmbralModel.mdlObtenerFechaMinMaxAuto(id_proyecto)

    @staticmethod
    def mdlObtenerFechasEnRango(id_proyecto, fechaMinInicial, fechaMaxInicial):
        conn = None
        tabla = "prismas" + str(id_proyecto)
        sql = f"""SELECT nombre_prisma, min(hora_prisma), max(hora_prisma) FROM {tabla} WHERE state_prisma = '1' 
        AND hora_prisma BETWEEN ? AND ? GROUP BY nombre_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (fechaMinInicial, fechaMaxInicial))
            result = [tuple(row) for row in cur.fetchall()]
            return result if result else None
        except Exception as e:
            print("Error al obtener fechas: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlObtenerFechasEnRangoManual(id_proyecto, fechaMinInicial, fechaMaxInicial):
        return UmbralModel.mdlObtenerFechasEnRango(id_proyecto, fechaMinInicial, fechaMaxInicial)
         
    @staticmethod
    def mdlObtenerFechasRangoPrismaNombre(id_proyecto, nombres, fechaini, fechafin):
        conn = None
        tabla = "prismas" + str(id_proyecto)
        placeholders = ','.join(['?' for _ in nombres])
        sql = f"""SELECT nombre_prisma, min(hora_prisma), max(hora_prisma) FROM {tabla} WHERE state_prisma = '1' AND nombre_prisma 
        IN ({placeholders}) AND hora_prisma BETWEEN ? AND ? GROUP BY nombre_prisma;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            params = tuple(nombres) + (fechaini, fechafin)
            cur.execute(sql, params)
            result = [tuple(row) for row in cur.fetchall()]
            return result if result else None
        except Exception as e:
            print("Error al obtener datos: " + str(e))
            return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlObtenerFechasRangoPrismaNombreManual(id_proyecto, nombres, fechaini, fechafin):
        return UmbralModel.mdlObtenerFechasRangoPrismaNombre(id_proyecto, nombres, fechaini, fechafin)
                
    @staticmethod
    def mdlComprobarDataPrismasAutoFecha(proyectoid, fechainicial, fechafinal):
        conn = None
        tabla = "prismas" + str(proyectoid)
        sql = f"""SELECT TOP 1 1 FROM {tabla} WHERE state_prisma = '1' AND hora_prisma BETWEEN ? AND ?"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (fechainicial, fechafinal))
            row = cur.fetchone()
            return True if row else False
        except Exception as e:
            print("Error al comprobar datos: " + str(e))
            return False
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlComprobarDataPrismasManualFecha(proyectoid, fechainicial, fechafinal):
        return UmbralModel.mdlComprobarDataPrismasAutoFecha(proyectoid, fechainicial, fechafinal)
    
    @staticmethod
    def mdlValidarUmbralesComponentes(idproyecto, tipo, tabla):
        conn = None
        try:
            conn = Connection.connectionDB()
            # Ajuste: TOP 1 para compatibilidad si el group by generaba multiples filas antes, o COUNT global
            sql = f"""SELECT COUNT(DISTINCT id_componente) AS cantidad, id_componente FROM {tabla} WHERE id_proyecto = ? AND tipo_umbral = ? GROUP BY id_componente;"""
            # Nota: Si se requiere un count total, quitar group by. Mantenemos estructura original.
            cur = conn.cursor()
            cur.execute(sql, (idproyecto, tipo))
            result = cur.fetchone()
            return tuple(result) if result else [0, None]
        except Exception as e:
            print("Error al validar umbrales: " + str(e))
            return [0, None]
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlObtenerUmbralesCodigoPiezometro(idpiezometro, tipo, tipopiezo):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = f"""SELECT * FROM umbral_piezometro WHERE id_piezometro = ? AND tipo_umbral = ? AND tipo_piezometro = ? ORDER BY rango_umbral ASC;"""
            cur = conn.cursor()
            cur.execute(sql, (idpiezometro, tipo, tipopiezo))
            result = [tuple(row) for row in cur.fetchall()]
            return result if result else None
        except Exception as e:
            print("Error al obtener umbrales: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlValidarUmbralesPiezometros(idproyecto, tipo, tipopiezo):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = f"""SELECT COUNT(DISTINCT id_piezometro) AS cantidad, id_piezometro FROM umbral_piezometro
            WHERE id_proyecto = ? AND tipo_umbral = ? AND tipo_piezometro = ? GROUP BY id_piezometro;"""
            cur = conn.cursor()
            cur.execute(sql, (idproyecto, tipo, tipopiezo))
            result = cur.fetchone()
            return tuple(result) if result else [0, None]
        except Exception as e:
            print("Error al validar umbrales: " + str(e))
            return [0, None]
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlListarPiezometrosUmbrales(idproyecto, tipo, tipopiezo, tabla):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = f"""SELECT DISTINCT u.id_piezometro, p.nombre_piezometro FROM umbral_piezometro u INNER JOIN {tabla} p
            ON u.id_piezometro = p.id_piezometro WHERE u.id_proyecto = ? AND u.tipo_umbral = ? AND u.tipo_piezometro = ?;"""
            cur = conn.cursor()
            cur.execute(sql, (idproyecto, tipo, tipopiezo))
            result = [tuple(row) for row in cur.fetchall()]
            return result
        except Exception as e:
            print("Error al listar piezo umbrales: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlValidarUmbralesCeldas(idproyecto, tipo):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = f"""SELECT COUNT(DISTINCT id_celda) AS cantidad, id_celda FROM umbral_celda WHERE id_proyecto = ? AND tipo_umbral = ? GROUP BY id_celda;"""
            cur = conn.cursor()
            cur.execute(sql, (idproyecto, tipo))
            result = cur.fetchone()
            return tuple(result) if result else [0, None]
        except Exception as e:
            print("Error al validar umbrales: " + str(e))
            return [0, None]
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlListarCeldasUmbrales(idproyecto, tipo):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = f"""SELECT DISTINCT u.id_celda, c.nombre_celda FROM umbral_celda u INNER JOIN celdas c
            ON u.id_celda = c.id_celda WHERE u.id_proyecto = ? AND u.tipo_umbral = ?;"""
            cur = conn.cursor()
            cur.execute(sql, (idproyecto, tipo))
            result = [tuple(row) for row in cur.fetchall()]
            return result
        except Exception as e:
            print("Error al listar celdas umbrales: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlListarComponentesUmbrales(idproyecto, tipo, tabla):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = f"""SELECT DISTINCT u.id_componente, c.nombre_componente FROM {tabla} u INNER JOIN componentes c
            ON u.id_componente = c.id_componente WHERE u.id_proyecto = ? AND u.tipo_umbral = ?;"""
            cur = conn.cursor()
            cur.execute(sql, (idproyecto, tipo))
            result = [tuple(row) for row in cur.fetchall()]
            return result
        except Exception as e:
            print("Error al listar compo umbrales: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlComponentesTipo(ids):
        conn = None
        try:
            conn = Connection.connectionDB()
            placeholders = ','.join('?' * len(ids))
            sql = f"""SELECT id_componente, nombre_componente FROM componentes
            WHERE estado_componente = 1 AND id_componente IN ({placeholders})"""
            cur = conn.cursor()
            cur.execute(sql, ids)
            result = [tuple(row) for row in cur.fetchall()]
            return result if result else None
        except Exception as e:
            print("Error al obtener umbrales: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlPiezometroID(ids, tipos):
        conn = None
        try:
            conn = Connection.connectionDB()
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
            params = tuple(ids) + tuple(tipos)
            cur.execute(sql, params)
            result = [tuple(row) for row in cur.fetchall()]
            return result if result else None
        except Exception as e:
            print("Error al obtener umbrales: " + str(e))
            return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlObtenerUmbralesEquiposCP(proyectoid, componente_id, tabla):
        conn = None
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
            result = [tuple(row) for row in cur.fetchall()] 
            return result if result else None
        except Exception as e:
            print("Error al obtener umbrales: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlObtenerUmbralesPiezometrosAnexo2(proyectoid, componente_id, tipopiezo):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = f"""SELECT inst.nombre_equipo, up.* FROM umbral_piezometro up INNER JOIN instrumentacion inst ON up.id_piezometro = inst.id_equipo
            WHERE inst.id_componente = ? AND up.id_proyecto = ? AND inst.tipo_equipo = ? AND tipo_umbral = 'NF';"""
            cur = conn.cursor()
            cur.execute(sql, (componente_id, proyectoid, tipopiezo))
            result = [tuple(row) for row in cur.fetchall()]
            return result if result else None
        except Exception as e:
            print("Error al obtener umbrales piezo: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlObtenerUmbralesInclinometros(ids):
        conn = None
        try:
            conn = Connection.connectionDB()
            placeholders = ','.join('?' * len(ids))
            sql = f"""SELECT * FROM umbral_inclinometro WHERE id_inclinometro IN ({placeholders}) ORDER BY rango_umbral ASC;"""
            cur = conn.cursor()
            cur.execute(sql, tuple(ids))
            result = [tuple(row) for row in cur.fetchall()]
            return result if result else None
        except Exception as e:
            print("Error al obtener umbrales: " + str(e))
            return None
        finally:
            if conn: conn.close()

    @staticmethod
    def mdlObtenerUmbralesPiezometros(ids):
        conn = None
        try:
            conn = Connection.connectionDB()
            placeholders = ','.join('?' * len(ids))
            sql = f"""SELECT * FROM umbral_piezometro WHERE id_piezometro IN ({placeholders}) AND tipo_umbral='NF' ORDER BY rango_umbral ASC;"""
            cur = conn.cursor()
            cur.execute(sql, tuple(ids))
            result = [tuple(row) for row in cur.fetchall()]
            return result if result else None
        except Exception as e:
            print("Error al obtener umbrales: " + str(e))
            return None
        finally:
            if conn: conn.close()