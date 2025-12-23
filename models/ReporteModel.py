from services.security.apis.conexiones.connection import Connection
from sqlite3 import Error

class ReporteModel:
    
    # Comprobar si existe gráfica
    @staticmethod
    def mdlTraerNombreEquipoReporte(proyectoid, idequipo):
        conn = None
        sql = """SELECT nombre_inclinometro FROM inclinometros WHERE id_proyecto = ? AND id_inclinometro = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyectoid, idequipo))
            row = cur.fetchone()
            if row:
                return tuple(row)
            else:
                return None
        except Exception as e:
            print("Error al traer nombre equipo reporte: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
                
    @staticmethod
    def mdlActualizarDatosReporte(ruta, texto_titulo, texto_descripcion, proyectoid, tipo, orden):
        conn = None
        sql = """UPDATE graficos_reporte SET imagen_grafica = ?, titulo_grafica = ?, descripcion_grafica = ? WHERE id_proyecto = ? AND vista_reporte = ?
        AND posicion_grafica = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (ruta, texto_titulo, texto_descripcion, proyectoid, tipo, orden))
            conn.commit()
            return True
        except Exception as e:
            print("Error al actualizar reporte: " + str(e))
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlGuardarDatosReporte(imagen_blob, texto_titulo, texto_descripcion, proyectoid, tipo, orden, equipo, anexo):
        conn = None
        sql = """INSERT INTO graficos_reporte (id_proyecto, vista_reporte, imagen_grafica, titulo_grafica, descripcion_grafica, posicion_grafica, equipo_grafica, anexo_reporte) 
        VALUES (?, ?, ?, ?, ?, ?, ?,?);"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # imagen_blob debe ser bytes para pyodbc VARBINARY
            cur.execute(sql, (proyectoid, tipo, imagen_blob, texto_titulo, texto_descripcion, orden, equipo, anexo))
            conn.commit()
            return True
        except Exception as e:
            print("Error al guardar reporte: " + str(e))
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlObtenerTotalGraficas(proyecto, tipo):
        conn = None
        # Corrección SQL: ORDER BY posicion_grafica AND id_reporte no es estándar. Debe ser coma.
        sql = """SELECT * FROM graficos_reporte WHERE id_proyecto = ? AND vista_reporte = ? ORDER BY posicion_grafica, id_reporte"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyecto, tipo))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al comprobar reporte: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerlistaGraficosAnexos(proyecto):
        conn = None
        sql = """SELECT id_reporte, imagen_grafica FROM graficos_reporte WHERE id_proyecto = ?"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyecto,))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al comprobar reporte: " + str(e))
            return None
        finally:
            if conn:
                    conn.close()
    
    @staticmethod
    def mdlObtenerlistaUmbralPrismasAnexos(proyecto):
        conn = None
        sql = """SELECT id_umbral, nombre_umbral, 'Prismas' AS equipo, 'umbral_prisma' AS tabla FROM umbral_prisma WHERE id_proyecto = ? AND nombre_umbral = 'VI3D';"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyecto,))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al traer umbral: " + str(e))
            return None
        finally:
            if conn:
                    conn.close()
    
    @staticmethod
    def mdlObtenerlistaUmbralPiezometrosAnexos(proyecto):
        conn = None
        sql = """SELECT id_umbral, nombre_umbral, 'Piezómetros' AS equipo, 'umbral_piezometro' AS tabla FROM umbral_piezometro WHERE id_proyecto = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyecto,))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al traer umbral: " + str(e))
            return None
        finally:
            if conn:
                    conn.close()
    
    @staticmethod
    def mdlObtenerlistaUmbralesInclinometrosAnexos(proyecto):
        conn = None
        sql = """SELECT id_umbral, nombre_umbral, 'Inclinómetros' AS equipo, 'umbral_inclinometro' AS tabla FROM umbral_inclinometro WHERE id_proyecto = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyecto,))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al traer umbral: " + str(e))
            return None
        finally:
            if conn:
                    conn.close()
    
    @staticmethod
    def mdlObtenerlistaUmbralCeldasAnexos(proyecto):
        conn = None
        sql = """SELECT id_umbral, nombre_umbral, 'Celdas' AS equipo, 'umbral_celda' AS tabla FROM umbral_celda WHERE id_proyecto = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyecto,))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al traer umbral: " + str(e))
            return None
        finally:
            if conn:
                    conn.close()
                   
    # En el modelo se agrega la consulta SQL para eliminar el gráfico
    @staticmethod
    def mdlEliminarGrafica(img_id):
        conn = None
        sql = """DELETE FROM graficos_reporte WHERE id_reporte = ?"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (img_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al eliminar gráfico: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlEliminarUmbralReporte(id, tabla):
        conn = None
        sql = f"""DELETE FROM {tabla} WHERE id_umbral = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al eliminar umbral: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
            
    @staticmethod
    def mdlObtenerTiposGraficas(proyecto):
        conn = None
        sql = """SELECT DISTINCT vista_reporte FROM graficos_reporte WHERE id_proyecto = ? ORDER BY posicion_grafica;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyecto,))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al comprobar reportes: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlListarDatosReporteGeneral(idproyecto):
        conn = None
        sql = """SELECT * FROM reporte_general WHERE id_proyecto = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idproyecto,))
            row = cur.fetchone()
            if row:
                return tuple(row)
            else:
                return None
        except Exception as e:
            print("Error al listar reporte general: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlRegistroNuevoReporte(proyectoid, encabezado, titulo, lugar, para, de, cc, fecha, asunto, texto, comentario, conclusiones, recomendacion):
        conn = None
        sql = """INSERT INTO reporte (id_proyecto, encabezado_reporte, titulo_reporte, lugar_reporte, para_reporte, de_reporte, copia_reporte, fecha_reporte,
        asunto_reporte, texto_reporte, comentario_reporte, conclusiones_reporte, recomendaciones_reporte) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyectoid, encabezado, titulo, lugar, para, de, cc, fecha, asunto, texto, comentario, conclusiones, recomendacion))
            conn.commit()
            return True
        except Exception as e:
            print("Error al guardar reporte: " + str(e))
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlActualizarReporte(proyectoid, encabezado, titulo, lugar, para, de, cc, fecha, asunto, texto, comentario, conclusiones, recomendacion):
        conn = None
        sql = """UPDATE reporte SET encabezado_reporte = ?, titulo_reporte = ?, lugar_reporte = ?, para_reporte = ?, de_reporte = ?, copia_reporte = ?, fecha_reporte = ?,
        asunto_reporte = ?, texto_reporte = ?, comentario_reporte = ?, conclusiones_reporte = ?, recomendaciones_reporte = ? WHERE id_proyecto = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (encabezado, titulo, lugar, para, de, cc, fecha, asunto, texto, comentario, conclusiones, recomendacion, proyectoid))
            conn.commit()
            return True
        except Exception as e:
            print("Error al actualizar reporte: " + str(e))
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerDataAnexos(proyectoid):
        conn = None
        sql = """SELECT (SELECT count(*) FROM inclinometros WHERE id_proyecto = ?) AS canti_inclino,
        (SELECT count(*) FROM piezometros WHERE id_proyecto = ? AND estado_piezometro = '1') AS canti_piezohidra,
        (SELECT count(*) FROM piezometrocuerdas WHERE id_proyecto = ?) AS canti_piezocuerda,
        (SELECT count(*) FROM celdas WHERE id_proyecto = ?) AS canti_celdas;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyectoid, proyectoid, proyectoid, proyectoid))
            row = cur.fetchone()
            if row:
                return tuple(row)
            else:
                return None
        except Exception as e:
            print("Error al obtener data anexos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerInfoPrismasAutoAnexos(proyectoid):
        conn = None
        tabla = "prismas" + str(proyectoid)
        # Nota: Asegurar que tabla existe. COUNT(DISTINCT col) es valido en SQL Server
        sql = f"""SELECT COUNT(DISTINCT nombre_prisma) AS cantidad_prismauto FROM {tabla} WHERE state_prisma = '1';"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchone()
            if row:
                return row[0]
            else:
                return 0
        except Exception as e:
            print("Error al obtener prismas anexos: " + str(e))
            return 0
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerInfoPrismasManualAnexos(proyectoid):
        conn = None
        tabla = "prismas" + str(proyectoid)
        sql = f"""SELECT COUNT(DISTINCT nombre_prisma) AS cantidad_prismanual FROM {tabla} WHERE state_prisma = '1';"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchone()
            if row:
                return row[0]
            else:
                return 0
        except Exception as e:
            print("Error al obtener prismas anexos: " + str(e))
            return 0
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlGuardarDataReporteAnexo1(datos):
        conn = None
        sql = """INSERT INTO reporte_anexo1 (id_proyecto, fechaini_reporte, fechafin_reporte, codigo_reporte, resumejecu1_reporte, resumejecu2_reporte,
        cotamaxima_reporte, comencotamaxima_reporte, alturabanco_reporte, comenalturabanco_reporte, anchobanco_reporte, comenanchobanco_reporte, taludbanco_reporte,
        comentaludbanco_reporte, totalapila_reporte, comentotalapila_reporte, desmonte_reporte, comendesmonte_reporte, areaocupada_reporte, comenareaocupada_reporte,
        vidautil_reporte, comenvidautil_reporte, taludes_reporte, comentaludes_reporte, grietas_reporte, comengrietas_reporte, distangrieta_reporte,
        comendistangrieta_reporte, profundigrieta_reporte, comenprofundigrieta_reporte, longigrieta_reporte, comenlongigrieta_reporte, agua_reporte, comenagua_reporte,
        inestabilidad_reporte, comeninestabilidad_reporte, inclinometros_reporte, cantiinclinometros_reporte, operainclinometros_reporte, condiinclinometros_reporte,
        piezohidra_reporte, cantipiezohidra_reporte, operapiezohidra_reporte, condipiezohidra_reporte, piezocuerda_reporte, cantipiezocuerda_reporte,
        operapiezocuerda_reporte, condipiezocuerda_reporte, prismas_reporte, cantiprismas_reporte, operaprismas_reporte, condiprismas_reporte, celdas_reporte,
        canticeldas_reporte, operaceldas_reporte, condiceldas_reporte, satelital_reporte, cantisatelital_reporte, operasatelital_reporte, condisatelital_reporte,
        acelerografo_reporte, cantiacelerografo_reporte, operaacelerografo_reporte, condiacelerografo_reporte, condigeome_reporte, comencondigeome_reporte,
        afectacion_reporte, comenafectacion_reporte) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, datos)
            conn.commit()
            return True
        except Exception as e:
            print("Error al guardar anexo 1: " + str(e))
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerDataAnexo2(proyectoid):
        conn = None
        sql = """SELECT * FROM reporte_anexo2 WHERE id_proyecto = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyectoid,))
            row = cur.fetchone()
            if row:
                return tuple(row)
            else:
                return None
        except Exception as e:
            print("Error al obtener data anexo 2: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
                
    @staticmethod
    def mdlGuardarDataReporteAnexo2(datos):
        conn = None
        sql = """INSERT INTO reporte_anexo2 (id_proyecto, componente_reporte, descripcompo_reporte, fechaini_reporte, fechafin_reporte, codigo_reporte,
        resumejecu_reporte, cantiinclino_reporte, operainclino_reporte, adicantiinclino_reporte, adioperainclino_reporte, frecuenciainclino_reporte,
        cantipiezohidra_reporte, operapiezohidra_reporte, adicantipiezohidra_reporte, adioperapiezohidra_reporte, frecuenciapiezohidra_reporte, cantipiezocuerda_reporte,
        operapiezocuerda_reporte, adicantipiezocuerda_reporte, adioperapiezocuerda_reporte, frecuenciapiezocuerda_reporte, cantiprismas_reporte, operaprismas_reporte,
        adicantiprismas_reporte, adioperaprismas_reporte, frecuenciaprismas_reporte, canticeldas_reporte, operaceldas_reporte, adicanticeldas_reporte,
        adioperaceldas_reporte, frecuenciaceldas_reporte, cantisatelital_reporte, operasatelital_reporte, adicantisatelital_reporte, adioperasatelital_reporte,
        frecuenciasatelital_reporte, cantiacelero_reporte, operaacelero_reporte, adicantiacelero_reporte, adioperaacelero_reporte, frecuenciaacelero_reporte)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, datos)
            conn.commit()
            return True
        except Exception as e:
            print("Error al guardar anexo 2: " + str(e))
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerGraficasReporteTipo(proyectoid, tipo, anexo):
        conn = None
        sql = """SELECT * FROM graficos_reporte WHERE id_proyecto = ? AND vista_reporte = ? AND anexo_reporte=?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyectoid, tipo, anexo))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al listar gráficas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
                                                                
    # Obtener jefes firma
    @staticmethod
    def mdlObtenerResponsables():
        conn = None
        sql = """SELECT * FROM personal_empresa WHERE tipo=?"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (0,))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al comprobar reporte: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # MODELO PARA GUARDAR RESPONSABLES
    @staticmethod
    def mdlGuardarResponsables(datos_guardados):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            
            # Reemplazo de INSERT OR REPLACE por MERGE o IF EXISTS en SQL Server
            # Lógica: Si existe actualiza, sino inserta.
            sql = '''
            MERGE personal_empresa AS target
            USING (VALUES (?, ?, ?, ?, ?)) AS source (id, supervision, responsable, comentario, firma)
            ON target.id = source.id
            WHEN MATCHED THEN
                UPDATE SET supervision = source.supervision,
                           responsable = source.responsable,
                           comentario = source.comentario,
                           firma = source.firma
            WHEN NOT MATCHED THEN
                INSERT (id, supervision, responsable, comentario, firma)
                VALUES (source.id, source.supervision, source.responsable, source.comentario, source.firma);
            '''
            
            # Recorrer cada fila de datos y ejecutar la lógica
            for datos in datos_guardados:
                cursor.execute(sql, (
                    datos['id'],
                    datos['supervision'],
                    datos['responsable'],
                    datos['comentarios'],
                    datos['imagen']
                ))
            
            # Guardar los cambios en la base de datos
            conn.commit()
            return "Datos guardados correctamente"
        except Exception as e:
            if conn:
                conn.rollback()  # Revertir cambios en caso de error
            return f"Error al guardar los datos: {str(e)}"
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerCoordenadasEquipos(proyecto, tipo):
        # 1: prismas
        # 2: prismas manuales
        # 3: piezometros manual
        # 4: piezometros Cuerda
        # 5: inclinometros
        # 6: celdas 
        conn = None
        sql = ""
        params = ()
        
        # En SQL Server no existe rowid. Usamos ROW_NUMBER() para filtrar duplicados.
        try:
            if tipo == 1 or tipo == 2:
                tabla = f'prismas{proyecto}'
                # Se selecciona la primera ocurrencia basada en algun orden (ej. ordenamiento por defecto)
                # Como no hay rowid, usamos CTE con ROW_NUMBER
                sql = f"""
                    WITH CTE AS (
                        SELECT nombre_prisma, este_target, norte_target, elevacion_target,
                        ROW_NUMBER() OVER(PARTITION BY nombre_prisma ORDER BY (SELECT NULL)) as rn
                        FROM {tabla}
                    )
                    SELECT nombre_prisma, este_target, norte_target, elevacion_target
                    FROM CTE WHERE rn = 1;
                """
                params = ()
            elif tipo == 3:
                tabla = 'piezometros'
                sql = """
                    SELECT nombre_piezometro, este_piezometro, norte_piezometro, elevacion_piezometro
                    FROM piezometros
                    WHERE id_proyecto = ?;
                """
                params = (proyecto,)
            elif tipo == 4:
                tabla = 'piezometrocuerdas'
                sql = """
                    SELECT nombre_piezometro, este_piezometro, norte_piezometro, elevacion_piezometro
                    FROM piezometrocuerdas
                    WHERE id_proyecto = ?;
                """
                params = (proyecto,)
            elif tipo == 5:
                tabla = 'inclinometros'
                sql = """
                    SELECT nombre_inclinometro, este_inclinometro, norte_inclinometro, elevacion_inclinometro
                    FROM inclinometros
                    WHERE id_proyecto = ?;
                """
                params = (proyecto,)
            elif tipo == 6:
                tabla = 'celdas'
                sql = """
                    SELECT nombre_celda, coordenada_este_celda, coordenada_norte_celda, cota_instalacion_celda
                    FROM celdas
                    WHERE id_proyecto = ?;
                """
                params = (proyecto,)
            
            # realizar consulta
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            return results if results else None
        except Exception as e:
            print(f"Error al comprobar reporte: {str(e)}")
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlEliminardatatabla(tabla):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # Elimina los datos de la tabla
            cursor.execute(f"DELETE FROM {tabla}")
            
            # Reinicia los índices de la tabla (Para SQL Server: DBCC CHECKIDENT)
            # Solo funciona si la tabla tiene columna IDENTITY
            try:
                cursor.execute(f"DBCC CHECKIDENT ('{tabla}', RESEED, 0);")
            except Exception:
                # Si la tabla no tiene IDENTITY, esto fallará pero no es crítico si solo queríamos borrar datos
                pass
                
            conn.commit()
            return True 
        except Exception as e:
            print(f"Ocurrió un error: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlGuardarUmbralesEqupisTipo(datos):
        conn = None
        try:
            conexion = Connection.connectionDB()
            cursor = conexion.cursor()
            
            # Transpilación a MERGE (Upsert)
            sql = """
                MERGE umbrales_alerta_equipos AS target
                USING (VALUES (?, ?)) AS source (proyecto_id, id_equipo)
                ON target.proyecto_id = source.proyecto_id AND target.id_equipo = source.id_equipo
                WHEN MATCHED THEN
                    UPDATE SET 
                        descripcion_normal = ?, 
                        descripcion_seguimiento = ?, 
                        descripcion_modo_proactivo = ?, 
                        descripcion_modo_reactivo = ?, 
                        descripcion_detencion_operaciones = ?
                WHEN NOT MATCHED THEN
                    INSERT (proyecto_id, id_equipo, descripcion_normal, descripcion_seguimiento, 
                            descripcion_modo_proactivo, descripcion_modo_reactivo, descripcion_detencion_operaciones)
                    VALUES (?, ?, ?, ?, ?, ?, ?);
            """
            
            # Parametros ordenados para MERGE
            # 1. Source (PKs)
            # 2. Update Values
            # 3. Insert Values (PKs + Values)
            params = (
                datos['proyectoID'], datos['equipo_id'], # Source
                datos['umbral_normal'], datos['umbral_seguimiento'], datos['umbral_proactivo'], datos['umbral_reactivo'], datos['umbral_deteccion_operacion'], # Update
                datos['proyectoID'], datos['equipo_id'], datos['umbral_normal'], datos['umbral_seguimiento'], datos['umbral_proactivo'], datos['umbral_reactivo'], datos['umbral_deteccion_operacion'] # Insert
            )
            
            cursor.execute(sql, params)
            conexion.commit()
            return True
        except Exception as e:
            if conexion:
                conexion.rollback()
            print(f"Error al guardar los umbrales: {e}")
            return False
        finally:
            if conexion:
                conexion.close()
    
    @staticmethod
    def mdlObtenerUmbralesEquiposTipo(proyectoID, id_equipo):
        conn = None
        try:
            conexion = Connection.connectionDB()
            cursor = conexion.cursor()
            query = """SELECT *
            FROM umbrales_alerta_equipos
            WHERE proyecto_id = ? AND id_equipo=?
            """
            cursor.execute(query, (proyectoID, id_equipo))
            resultados = cursor.fetchone()
            if resultados:
                return tuple(resultados)
            else:
                return None
        except Exception as e:
            print(f"Error al obtener umbrales de equipos para el proyecto {proyectoID}: {e}")
            return None
        finally:
            if conexion:
                conexion.close()
    
    @staticmethod
    def mdlGuardarInformacionReporte(data):
        conn = None
        try:
            conexion = Connection.connectionDB()
            cursor = conexion.cursor()
            
            # Upsert logic manual o MERGE. Aquí manual:
            cursor.execute("SELECT componente_reporte FROM reporte_general WHERE id_proyecto = ?", (data[0],))
            existing_image = cursor.fetchone()
            
            if existing_image:
                cursor.execute("""
                    UPDATE reporte_general
                    SET encabezado_reporte = ?, pie_reporte = ?, titulo_reporte = ?,
                        lugar_reporte = ?,fecha_reporte = ?, para_reporte = ?, de_reporte = ?, cc_reporte = ?,
                        asunto_reporte = ?, descripcion_reporte = ?, conclusiones_reporte = ?,
                        recomendaciones_reporte = ?, componente_reporte = ?
                    WHERE id_proyecto = ?
                """, (data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8], data[9], data[10], data[11], data[12], data[13], data[0]))
            else:
                cursor.execute("""
                    INSERT INTO reporte_general (id_proyecto, encabezado_reporte, pie_reporte, titulo_reporte,
                                                lugar_reporte,fecha_reporte, para_reporte, de_reporte, cc_reporte, asunto_reporte,
                                                descripcion_reporte, conclusiones_reporte, recomendaciones_reporte, componente_reporte)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, data)
            conexion.commit()
        except Exception as e:
            if conexion:
                conexion.rollback()
            print(f"Error al guardar la información del reporte: {e}")
        finally:
            if conexion:
                conexion.close()
    
    @staticmethod
    def mdlObtenerDatosFirma(proyectoid):
        conn = None
        sql = """SELECT * FROM firmas WHERE id_proyecto = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql,(proyectoid,))
            row = cur.fetchone()
            if row:
                return tuple(row)
            else:
                return None
        except Exception as e:
            print("Error al traer firma: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlRegistrarFirma(proyectoid, data):
        conn = None
        responsable, cargo, dni, cip, firma_reporte = data
        try:
            conexion = Connection.connectionDB()
            cursor = conexion.cursor()
            # Verificar si ya existe algún registro en la tabla
            cursor.execute("SELECT COUNT(*) FROM firmas WHERE id_proyecto=?", (proyectoid,))
            count = cursor.fetchone()[0]
            if count > 0:
                # Actualizar el registro existente
                if firma_reporte is not None:
                    cursor.execute("""
                        UPDATE firmas
                        SET responsable = ?, cargo = ?, dni = ?, cip = ?, firma = ?
                        WHERE id_proyecto = ?
                    """, (responsable, cargo, dni, cip, firma_reporte, proyectoid))
                else:
                    cursor.execute("""
                        UPDATE firmas
                        SET responsable = ?, cargo = ?, dni = ?, cip = ?
                        WHERE id_proyecto = ?
                    """, (responsable, cargo, dni, cip, proyectoid))
            else:
                # Insertar un nuevo registro
                cursor.execute("""
                    INSERT INTO firmas (id_proyecto, responsable, cargo, dni, cip, firma)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (proyectoid, responsable, cargo, dni, cip, firma_reporte))
            conexion.commit()
            return True
        except Exception as e:
            if conexion:
                conexion.rollback()
            print(f"Error al guardar firma del reporte: {e}")
            return False
        finally:
            if conexion:
                conexion.close()
    
    @staticmethod
    def mdlGuardarImagenReporte(data):
        conn = None
        query = """INSERT INTO graficos_reporte (id_componente, vista_reporte, tipo_grafico, imagen_grafica, titulo_grafica,
        descripcion_grafica, tipo_reporte, tipo_equipo) VALUES (?, ?, ?, ?, ?, ?, ?, ?);"""
        try:
            conexion = Connection.connectionDB()
            cursor = conexion.cursor()
            cursor.execute(query, (data["id_componente"], data["vista_reporte"], data["tipo_grafico"], data["imagen_grafica"],
                data["titulo_grafica"], data["descripcion_grafica"], data["tipo_reporte"], data["tipo_equipo"]))
            conexion.commit()
            return True
        except Exception as e:
            if conexion:
                conexion.rollback()
            print(f"Error al guardar la imagen del reporte: {e}")
            return False
        finally:
            if conexion:
                conexion.close()
    
    @staticmethod
    def mdlObtenerListaPrismas(tabla, tipo, id_componente):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # ROW_NUMBER() es compatible con SQL Server 2008+
            sql = f"""
            SELECT
                subquery.nombre_prisma,
                subquery.este_target,
                subquery.norte_target,
                subquery.elevacion_target,
                subquery.nombre_componente
            FROM (
                SELECT
                    pr.nombre_prisma,
                    pr.este_target,
                    pr.norte_target,
                    pr.elevacion_target,
                    com.nombre_componente,
                    ROW_NUMBER() OVER (PARTITION BY pr.nombre_prisma ORDER BY pr.hora_prisma) AS rn
                FROM
                    instrumentacion ins
                INNER JOIN
                    {tabla} pr ON ins.nombre_equipo = pr.nombre_prisma
                INNER JOIN
                    componentes com ON ins.id_componente = com.id_componente
                WHERE
                    ins.estado_instrumentacion = 1 AND ins.tipo_equipo = ? AND ins.id_componente=?
            ) AS subquery
            WHERE
                subquery.rn = 1
            ORDER BY
                subquery.nombre_prisma;
            """
            cursor.execute(sql, (tipo, id_componente))
            rows = cursor.fetchall()
            results = [tuple(row) for row in rows]
            return results if results else None
        except Exception as e:
            print("Error al traer lista prismas reporte: ", e)
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerListaInclinometros(proyectoid, id_componente):
        conn = None
        sql = """SELECT 
                    incl.nombre_inclinometro,
                    incl.este_inclinometro,
                    incl.norte_inclinometro,
                    incl.elevacion_inclinometro,
                    com.nombre_componente
                FROM 
                    instrumentacion ins
                INNER JOIN 
                    inclinometros incl ON ins.id_equipo = incl.id_inclinometro
                INNER JOIN 
                    componentes com ON ins.id_componente = com.id_componente
                WHERE 
                    incl.id_proyecto=? AND ins.estado_instrumentacion = 1 AND ins.tipo_equipo= 'INCLINOMETRO' AND ins.id_componente=?
                """
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyectoid, id_componente))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al traer lista inclinómetros reporte: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerListaPiezometros(proyecto, tabla, tipo, id_componente):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            sql = f"""
            SELECT 
                pz.nombre_piezometro,
                pz.este_piezometro,
                pz.norte_piezometro,
                pz.elevacion_piezometro,
                com.nombre_componente
            FROM 
                instrumentacion ins
            INNER JOIN 
                {tabla} pz ON ins.id_equipo = pz.id_piezometro
            INNER JOIN 
                componentes com ON ins.id_componente = com.id_componente
            WHERE 
                pz.id_proyecto=? AND ins.estado_instrumentacion = 1 AND ins.tipo_equipo= ? AND ins.id_componente=?
            """
            cursor.execute(sql, (proyecto, tipo, id_componente))
            rows = cursor.fetchall()
            results = [tuple(row) for row in rows]
            return results if results else None
        except Exception as e:
            print("Error al traer lista prismas reporte: ", e)
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerListaCeldas(proyectoid, id_componente):
        conn = None
        sql = """SELECT 
                    cld.nombre_celda,
                    cld.este_celda,
                    cld.norte_celda,
                    cld.instalacion_celda,
                    com.nombre_componente
                FROM 
                    instrumentacion ins
                INNER JOIN 
                    celdas cld ON ins.id_equipo = cld.id_celda
                INNER JOIN 
                    componentes com ON ins.id_componente = com.id_componente
                WHERE 
                    cld.id_proyecto=? AND ins.estado_instrumentacion = 1 AND ins.tipo_equipo= 'CELDA' AND ins.id_componente=?
                """
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyectoid, id_componente))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al traer lista inclinómetros reporte: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerListaAcelerografos(proyectoid, id_componente):
        conn = None
        sql = """SELECT 
            acel.nombre_acelerografo,
            acel.este_acelerografo,
            acel.norte_acelerografo,
            acel.elevacion_acelerografo,
            com.nombre_componente
        FROM 
            instrumentacion ins
        INNER JOIN 
            acelerografos acel ON ins.id_equipo = acel.id_acelerografo
        INNER JOIN
            componentes com ON ins.id_componente = com.id_componente
        WHERE 
            acel.id_proyecto=? AND ins.estado_instrumentacion = 1 AND ins.tipo_equipo= 'ACELEROGRAFO' AND ins.id_componente=?
                """
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyectoid, id_componente))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al traer lista inclinómetros reporte: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerListaSondajesTDR(proyectoid, id_componente):
        conn = None
        sql = """SELECT 
            stdr.nombre_sondajetdr,
            stdr.este_sondajetdr,
            stdr.norte_sondajetdr,
            stdr.elevacion_sondajetdr,
            com.nombre_componente
        FROM 
            instrumentacion ins
        INNER JOIN 
            sondajestdr stdr ON ins.id_equipo = stdr.id_sondajetdr
        INNER JOIN
            componentes com ON ins.id_componente = com.id_componente
        WHERE 
            stdr.id_proyecto=? AND ins.estado_instrumentacion = 1 AND ins.tipo_equipo= 'TDR' AND ins.id_componente=?
                """
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyectoid, id_componente))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al traer lista inclinómetros reporte: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    @staticmethod
    def mdlObtenerListaImagenesReporte(id_componente):
        conn = None
        sql = """SELECT * FROM graficos_reporte WHERE id_componente = ? AND tipo_reporte = 'GENERAL';"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (id_componente,))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al traer img reporte general: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerControlParametrosA1(idcomponente):
        conn = None
        sql = """SELECT * FROM control_parametros_anexo1 WHERE id_componente = ?;"""
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
            print("Error al comprobar control parametros: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerCondicionesFisicasA1(idcomponente):
        conn = None
        sql = """SELECT * FROM condiciones_fisicas_anexo1 WHERE id_componente = ?;"""
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
            print("Error al comprobar condiciones físicas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerOperatividadEquiposA1(idcomponente):
        conn = None
        sql = """SELECT * FROM operatividad_equipos_anexo1 WHERE id_componente = ?;"""
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
            print("Error al comprobar operatividad equipos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerObservacionesA1(idcomponente):
        conn = None
        sql = """SELECT * FROM observaciones_medidas_anexo1 WHERE id_componente = ?;"""
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
            print("Error al comprobar observaciones anexo1: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerAnexo2(proyectoid):
        conn = None
        sql = """SELECT * FROM anexos2 WHERE proyecto_id=?"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyectoid,))
            row = cur.fetchone()
            if row:
                return tuple(row)
            else:
                return None
        except Exception as e:
            print("Error al comprobar reporte: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerUbicacionInstrumentacionGeotecnica(idcomponente):
        conn = None
        sql = """SELECT * FROM ubicaciones_instrumentacion_anexo2 WHERE id_componente = ?;"""
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
            print("Error al comprobar ubicaciones intrumentacion anexo2: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerInstrumentacionGeotecnica(idcomponente):
        conn = None
        sql = """SELECT * FROM instrumentacion_geotecnica_anexo2 WHERE id_componente = ?;"""
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
            print("Error al comprobar intrumentacion anexo2: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerObservacionesA2(idcomponente):
        conn = None
        sql = """SELECT * FROM observaciones_medidas_anexo2 WHERE id_componente = ?;"""
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
            print("Error al comprobar observaciones anexo2: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerObtenerComponentes(proyecto_id):
        conn = None
        sql = """SELECT * FROM componentes  WHERE id_proyecto = ? AND estado_componente = 1;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyecto_id,))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al obtener componentes: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerResumenEjecutivoAnexo1(idcomponente):
        conn = None
        sql = f"""SELECT * FROM resumen_ejecutivo_anexo1 WHERE id_componente = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idcomponente,))
            row = cur.fetchone()
            if row:
                return tuple(row)
            else:
                return None
        except Exception as e:
            print("Error al traer resumen ejecutivo a1: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerTablaResumenEjecutivoAnexo1(idcomponentes):
        conn = None
        # Validación de lista
        if not isinstance(idcomponentes, list):
            idcomponentes = [idcomponentes] if idcomponentes is not None else []
            
        placeholders = ', '.join(['?' for _ in idcomponentes])
        sql = f"""SELECT c.nombre_componente, r.* FROM resumen_ejecutivo_anexo1 r INNER JOIN componentes c
        ON r.id_componente = c.id_componente WHERE r.id_componente IN ({placeholders});"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, idcomponentes)
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error en resumen ejecutivo a1: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerParametrosAnexo1(idcomponentes):
        conn = None
        # Validación de lista
        if not isinstance(idcomponentes, list):
            idcomponentes = [idcomponentes] if idcomponentes is not None else []

        placeholders = ', '.join(['?' for _ in idcomponentes])
        sql = f"""SELECT c.nombre_componente, p.* FROM control_parametros_anexo1 p INNER JOIN componentes c
        ON c.id_componente = p.id_componente WHERE p.id_componente IN ({placeholders});"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, idcomponentes)
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al comprobar parametros : " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerCondicionesFisicasAnexo1(idcomponentes):
        conn = None
        # Validación de lista
        if not isinstance(idcomponentes, list):
            idcomponentes = [idcomponentes] if idcomponentes is not None else []

        placeholders = ', '.join(['?' for _ in idcomponentes])
        sql = f"""SELECT c.nombre_componente, f.* FROM componentes c INNER JOIN condiciones_fisicas_anexo1 f
        ON c.id_componente = f.id_componente WHERE f.id_componente IN ({placeholders});"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, idcomponentes)
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al comprobar condiciones fisicas : " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerOperatividadEquipos(idcomponentes):
        conn = None
        # Validación de lista
        if not isinstance(idcomponentes, list):
            idcomponentes = [idcomponentes] if idcomponentes is not None else []

        placeholders = ', '.join(['?' for _ in idcomponentes])
        sql = f"""SELECT c.nombre_componente, o.* FROM componentes c INNER JOIN operatividad_equipos_anexo1 o
        ON c.id_componente = o.id_componente WHERE o.id_componente IN ({placeholders});"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, idcomponentes)
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al comprobar observaciones : " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerObservacionesAnexo1(idcomponentes):
        conn = None
        # Validación de lista
        if not isinstance(idcomponentes, list):
            idcomponentes = [idcomponentes] if idcomponentes is not None else []

        placeholders = ', '.join(['?' for _ in idcomponentes])
        sql = f"""SELECT c.nombre_componente, o.* FROM componentes c INNER JOIN observaciones_medidas_anexo1 o
        ON c.id_componente = o.id_componente WHERE o.id_componente IN ({placeholders});"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, idcomponentes)
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al comprobar observaciones : " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerResumenEjecutivoAnexo2(idcomponente):
        conn = None
        sql = """SELECT * FROM resumen_ejecutivo_anexo2 WHERE id_componente = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idcomponente,))
            row = cur.fetchone()
            if row:
                return tuple(row)
            else:
                return None
        except Exception as e:
            print("Error al traer resumen ejecutivo a2: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerTablaResumenEjecutivoAnexo2(idcomponentes):
        conn = None
        # Validación de lista
        if not isinstance(idcomponentes, list):
            idcomponentes = [idcomponentes] if idcomponentes is not None else []

        placeholders = ', '.join(['?' for _ in idcomponentes])
        sql = f"""SELECT c.nombre_componente, r.* FROM resumen_ejecutivo_anexo2 r INNER JOIN componentes c
        ON r.id_componente = c.id_componente WHERE r.id_componente IN ({placeholders});"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, idcomponentes)
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error resumen ejecutivo a2: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerInstrumentacionAnexo2(idcomponentes):
        conn = None
        # Validación de lista
        if not isinstance(idcomponentes, list):
            idcomponentes = [idcomponentes] if idcomponentes is not None else []

        placeholders = ', '.join(['?' for _ in idcomponentes])
        sql = f"""SELECT c.nombre_componente, i.* FROM componentes c INNER JOIN instrumentacion_geotecnica_anexo2 i
        ON c.id_componente = i.id_componente WHERE i.id_componente IN ({placeholders});"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, idcomponentes)
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al comprobar intrumentacion Geotecnica: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerInterpretacionValoresA2(instrumento, idcompo):
        conn = None
        sql = """SELECT c.nombre_componente, u.* FROM componentes c INNER JOIN ubicaciones_instrumentacion_anexo2 u
        ON c.id_componente = u.id_componente WHERE u.id_componente = ? AND u.tipo_instrumentacion = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idcompo, instrumento))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al comprobar interpretacion: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    @staticmethod
    def mdlDatosVI3DPositivas(idcomponente, tabla, tipo_prisma):
        conn = None
        validacion = "SELECT nombre_equipo FROM instrumentacion WHERE tipo_equipo = 'PRISMAS' AND id_componente=?;"
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            
            # 1. Obtener nombres de equipos
            cur.execute(validacion, (idcomponente,))
            filtro_rows = cur.fetchall()
            
            if not filtro_rows:
                return None
            
            nombres_equipos = [row[0] for row in filtro_rows]
            placeholders = ','.join(['?' for _ in nombres_equipos])
            
            # 2. Transpilación T-SQL compleja
            # - JULIANDAY(x) - JULIANDAY(y)  ->  DATEDIFF(SECOND, y, x) / 86400.0
            # - POWER, SQRT, LAG, FIRST_VALUE, ROW_NUMBER son compatibles
            sql = f"""
            WITH PrismasCTE AS (
                SELECT
                    nombre_prisma,
                    hora_prisma,
                    este_target,
                    norte_target,
                    elevacion_target,
                    CAST(DATEDIFF(SECOND, first_value(hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma, hora_prisma), hora_prisma) AS FLOAT) / 86400.0 AS dias,
                    CASE
                        WHEN row_number() OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma, hora_prisma) = 1 THEN 0
                        ELSE
                            SQRT(
                                POWER(este_target - lag(este_target) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma, hora_prisma), 2) +
                                POWER(norte_target - lag(norte_target) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma, hora_prisma), 2) +
                                POWER(elevacion_target - lag(elevacion_target) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma, hora_prisma), 2)
                            )
                    END AS tresD2
                FROM {tabla}
                WHERE state_prisma = 1 AND estado_prisma = 1 AND nombre_prisma IN ({placeholders})
            )
            SELECT
                nombre_prisma,
                hora_prisma AS FECHAS,
                dias AS DIAS,
                dias*24 AS HORAS,
                CASE
                    WHEN row_number() OVER (PARTITION BY nombre_prisma ORDER BY hora_prisma) = 1 THEN 0
                    ELSE
                        (tresD2*100) / 
                        NULLIF((CAST(DATEDIFF(SECOND, LAG(hora_prisma, 1, hora_prisma) OVER (PARTITION BY nombre_prisma ORDER BY nombre_prisma, hora_prisma), hora_prisma) AS FLOAT) / 86400.0), 0)
                END AS VI3D2,
                ? AS tipo_prisma
            FROM PrismasCTE;
            """
            
            # Parametros: Lista de nombres para el IN + tipo_prisma para el SELECT final
            params = nombres_equipos + [tipo_prisma]
            
            cur.execute(sql, params)
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al consultar lecturas VI3D positivas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerObservacionesAnexo2(idcomponentes):
        conn = None
        if not isinstance(idcomponentes, list):
            idcomponentes = [idcomponentes] if idcomponentes is not None else []
            
        placeholders = ', '.join(['?' for _ in idcomponentes])
        sql = f"""SELECT c.nombre_componente, o.* FROM componentes c INNER JOIN observaciones_medidas_anexo2 o
        ON c.id_componente = o.id_componente WHERE o.id_componente IN ({placeholders});"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, idcomponentes)
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al comprobar observaciones : " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlGuardarDataGeneralAnexos(datos, idproyecto, tiporeporte):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute("SELECT id_reporte FROM reporte_anexos WHERE id_proyecto = ? AND tipo_anexo = ?;", (idproyecto, tiporeporte))
            registro_existente = cur.fetchone()
            
            if registro_existente:
                # datos es una lista, insertamos el valor en la posicion 13 (imagen_componente)
                datos.insert(13, datos[12]) 
                
                # Actualizar
                sql_update = """UPDATE reporte_anexos SET titulo_portada = ?, subtitulo_portada = ?, lugar_portada = ?,
                autor_portada = ?, tipo_documento = ?, codigo_reporte = ?, destinatario_reporte = ?, remitente_reporte = ?,
                asunto_reporte = ?, descripcion_reporte = ?, tipo_reporte = ?, componente_reporte = ?,
                imagen_componente = CASE WHEN ? IS NOT NULL THEN ? ELSE imagen_componente END, objetivo_reporte = ?,
                finalidad_reporte = ?, ambito_aplicacion_reporte = ?, detalle_reporte = ?, titulo_anexo = ?, tipo_anexo = ?
                WHERE id_reporte = ?;"""
                
                params = datos + [registro_existente[0]]
                cur.execute(sql_update, params)
            else:
                # Insertar nuevo registro
                sql_insert = """INSERT INTO reporte_anexos (id_proyecto, titulo_portada, subtitulo_portada, lugar_portada,
                autor_portada, tipo_documento, codigo_reporte, destinatario_reporte, remitente_reporte, asunto_reporte,
                descripcion_reporte, tipo_reporte, componente_reporte, imagen_componente, objetivo_reporte, finalidad_reporte,
                ambito_aplicacion_reporte, detalle_reporte, titulo_anexo, tipo_anexo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""
                
                params = [idproyecto] + datos
                cur.execute(sql_insert, params)
                
            conn.commit()
            return True
        except Exception as e:
            print("Error al guardar o actualizar data general anexo: " + str(e))
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlListarDatosGeneralAnexos(idproyecto, tipoanexo):
        conn = None
        sql = """SELECT * FROM reporte_anexos WHERE id_proyecto = ? AND tipo_anexo = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idproyecto, tipoanexo))
            row = cur.fetchone()
            if row:
                return tuple(row)
            else:
                return None
        except Exception as e:
            print("Error al listar reporte anexo general: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlGuardarResumenEjecutivoAnexo1(valores, idcomponente):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            sql_check = """SELECT COUNT(*) FROM resumen_ejecutivo_anexo1 WHERE id_componente = ?;"""
            cur.execute(sql_check, (idcomponente,))
            result = cur.fetchone()
            
            if result[0] > 0:
                sql_update = """UPDATE resumen_ejecutivo_anexo1 SET descripcion_anexo = ?,
                componente_encabezado = ?, valor_componente_encabezado = ?, autorizacion_encabezado = ?,
                valor_autorizacion_encabezado = ?, fecha_encabezado = ?, valor_fecha_encabezado = ?, expediente_control = ?,
                valor_expediente_control = ?, inspeccion_control = ?, valor_inspeccion_control = ? WHERE id_componente = ?;"""
                params = valores + [idcomponente]
                cur.execute(sql_update, params)
            else:
                sql_insert = """INSERT INTO resumen_ejecutivo_anexo1 (id_componente, descripcion_anexo,
                componente_encabezado, valor_componente_encabezado, autorizacion_encabezado, valor_autorizacion_encabezado,
                fecha_encabezado, valor_fecha_encabezado, expediente_control, valor_expediente_control, inspeccion_control,
                valor_inspeccion_control) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""
                params = [idcomponente] + valores
                cur.execute(sql_insert, params)
                
            conn.commit()
            return True
        except Exception as e:
            print("Error al guardar resumen ejecutivo a1: " + str(e))
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerImagenesGraficasReporte(idcomponente, tipo_equipo, anexo):
        conn = None
        sql = """SELECT * FROM graficos_reporte WHERE id_componente = ? AND tipo_reporte = ? AND tipo_equipo = ?;"""
        params = (idcomponente, anexo, tipo_equipo)
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al traer imagenes reporte: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlGuardarResumenEjecutivoAnexo2(valores, idcomponente):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            sql_check = """SELECT COUNT(*) FROM resumen_ejecutivo_anexo2 WHERE id_componente = ?;"""
            cur.execute(sql_check, (idcomponente,))
            result = cur.fetchone()
            
            if result[0] > 0:
                sql_update = """UPDATE resumen_ejecutivo_anexo2 SET descripcion_anexo = ?, componente_encabezado = ?,
                valor_componente_encabezado = ?, periodo_encabezado = ?, valor_periodo_encabezado = ?,
                interpretacion_monitoreo = ?, valor_interpretacion = ? WHERE id_componente = ?;"""
                params = valores + [idcomponente]
                cur.execute(sql_update, params)
            else:
                sql_insert = """INSERT INTO resumen_ejecutivo_anexo2 (id_componente, descripcion_anexo,
                componente_encabezado, valor_componente_encabezado, periodo_encabezado, valor_periodo_encabezado,
                interpretacion_monitoreo, valor_interpretacion) VALUES (?, ?, ?, ?, ?, ?, ?, ?);"""
                params = [idcomponente] + valores
                cur.execute(sql_insert, params)
                
            conn.commit()
            return True
        except Exception as e:
            print("Error al guardar resumen ejecutivo a2: " + str(e))
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlListarImagenesReportes(idcomponente, tiporeporte):
        conn = None
        sql = """SELECT * FROM graficos_reporte WHERE id_componente = ? AND tipo_reporte = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idcomponente, tiporeporte))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al traer img reportes: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlEliminarGraficaReporte(idimagen):
        conn = None
        sql = """DELETE FROM graficos_reporte WHERE id_reporte = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idimagen,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al eliminar imagen reporte: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlGuardarParametrosAnexo1(parametros, idcomponente):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.fast_executemany = True  # Optimización SQL Server
            
            delete_sql = """DELETE FROM control_parametros_anexo1 WHERE id_componente = ?;"""
            cur.execute(delete_sql, (idcomponente,))
            
            insert_sql = """INSERT INTO control_parametros_anexo1 (id_componente, descripcion_parametro, valor_parametro,
            unidad_parametro, condicion_parametro, comentario_parametro) VALUES (?, ?, ?, ?, ?, ?);"""
            cur.executemany(insert_sql, parametros)
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al guardar los parámetros a1: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlGuardarCondicionesAnexo1(condiciones, idcomponente):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.fast_executemany = True
            
            delete_sql = """DELETE FROM condiciones_fisicas_anexo1 WHERE id_componente = ?;"""
            cur.execute(delete_sql, (idcomponente,))
            
            insert_sql = """INSERT INTO condiciones_fisicas_anexo1 (id_componente, condicion_talud, estado_condicion, comentario,
            tipo_condicion) VALUES (?, ?, ?, ?, ?);"""
            cur.executemany(insert_sql, condiciones)
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al guardar condiciones fisicas a1: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlGuardarOperatividadAnexo1(operatividad, idcomponente):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.fast_executemany = True
            
            delete_sql = """DELETE FROM operatividad_equipos_anexo1 WHERE id_componente = ?;"""
            cur.execute(delete_sql, (idcomponente,))
            
            insert_sql = """INSERT INTO operatividad_equipos_anexo1 (id_componente, instrumentacion, condicion_actual, cantidad, 
            operatividad, comentario) VALUES (?, ?, ?, ?, ?, ?);"""
            cur.executemany(insert_sql, operatividad)
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al guardar operatividad a1: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlGuardarObservacionesAnexo1(observaciones, idcomponente):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.fast_executemany = True
            
            delete_sql = """DELETE FROM observaciones_medidas_anexo1 WHERE id_componente = ?;"""
            cur.execute(delete_sql, (idcomponente,))
            
            insert_sql = """INSERT INTO observaciones_medidas_anexo1 (id_componente, descripcion, condicion_actual, medidas,
            plazo, comentario, responsable, tipo) VALUES (?, ?, ?, ?, ?, ?, ?, ?);"""
            cur.executemany(insert_sql, observaciones)
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al guardar observaciones a1: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlGuardarInstrumentacionAnexo2(instrumentacion, idcomponente):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.fast_executemany = True
            
            sql_delete = """DELETE FROM instrumentacion_geotecnica_anexo2 WHERE id_componente = ?;"""
            cur.execute(sql_delete, (idcomponente,))
            
            sql_insert = """INSERT INTO instrumentacion_geotecnica_anexo2 (id_componente, instrumentacion, cantidad_autorizado, 
            operatividad_autorizado, cantidad_adicional, operatividad_adicional, total_intrumentacion, frecuencia_monitoreo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);"""
            cur.executemany(sql_insert, instrumentacion)
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al guardar los instrumentacion a2: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlGuardarUbicacionesInstrumentacion(instrumentacion, idcomponente):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            
            # Obtener IDs existentes
            select_sql = """SELECT id_ubicacion FROM ubicaciones_instrumentacion_anexo2 WHERE id_componente = ?;"""
            cur.execute(select_sql, (idcomponente,))
            existing_ids = {row[0] for row in cur.fetchall()}
            
            # Obtener IDs nuevos
            new_ids = {item[0] for item in instrumentacion if item[0] is not None}
            
            # Identificar IDs a borrar
            ids_to_delete = list(existing_ids - new_ids)
            
            if ids_to_delete:
                placeholders = ', '.join(['?' for _ in ids_to_delete])
                delete_sql = f"""DELETE FROM ubicaciones_instrumentacion_anexo2 WHERE id_ubicacion IN ({placeholders})"""
                cur.execute(delete_sql, ids_to_delete)
                
            # Insertar o actualizar
            for item in instrumentacion:
                row_id = item[0]
                # item[1] es id_componente (ya lo tenemos en argumento pero iteramos item)
                id_comp_item = item[1]
                instrumento = item[2]
                imagen_blob = item[3]
                tipo_instrumentacion = item[4]
                
                if row_id is not None:
                    if imagen_blob:
                        update_sql = """UPDATE ubicaciones_instrumentacion_anexo2 SET instrumento = ?, ubicacion_imagen = ?,
                        tipo_instrumentacion = ? WHERE id_ubicacion = ?;"""
                        cur.execute(update_sql, (instrumento, imagen_blob, tipo_instrumentacion, row_id))
                    else:
                        update_sql = """UPDATE ubicaciones_instrumentacion_anexo2 SET instrumento = ?, tipo_instrumentacion = ?
                        WHERE id_ubicacion = ?;"""
                        cur.execute(update_sql, (instrumento, tipo_instrumentacion, row_id))
                else:
                    insert_sql = """INSERT INTO ubicaciones_instrumentacion_anexo2 (id_componente, instrumento, ubicacion_imagen,
                    tipo_instrumentacion) VALUES (?, ?, ?, ?);"""
                    cur.execute(insert_sql, (id_comp_item, instrumento, imagen_blob, tipo_instrumentacion))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al atualizar ubicaciones: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlGuardarObservacionesAnexo2(observaciones, idcomponente):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.fast_executemany = True
            
            sql_delete = """DELETE FROM observaciones_medidas_anexo2 WHERE id_componente = ?;"""
            cur.execute(sql_delete, (idcomponente,))
            
            sql_insert = """INSERT INTO observaciones_medidas_anexo2 (id_componente, descripcion, condicion_actual, medidas,
            plazo, comentario, responsable, tipo) VALUES (?, ?, ?, ?, ?, ?, ?, ?);"""
            cur.executemany(sql_insert, observaciones)
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al guardar observaciones a2: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()