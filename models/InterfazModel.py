from services.security.apis.conexiones.connection import Connection

class InterfazModel:
    
    @staticmethod
    def mdlListarProyectos():
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = """SELECT * FROM proyectos WHERE estado_proyecto = 1 ORDER BY id_proyecto DESC;"""
            cur = conn.cursor()
            cur.execute(sql)
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al obtener proyectos:", e)
            return None  
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlListarComponentesProyecto(idproyecto):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = """SELECT * FROM componentes WHERE id_proyecto = ? AND estado_componente = 1;"""
            cur = conn.cursor()
            cur.execute(sql, (idproyecto,))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al obtener componentes:", e)
            return None  
        finally:
            if conn:
                conn.close()
                
    @staticmethod
    def mdlListarInclinometrosProyecto(idproyecto):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = """SELECT id_inclinometro, id_proyecto, nombre_inclinometro FROM inclinometros WHERE id_proyecto = ? AND estado_inclinometro = 1;"""
            cur = conn.cursor()
            cur.execute(sql, (idproyecto,))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al obtener inclinometros:", e)
            return None  
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlListarPiezometrosProyecto(idproyecto, tabla, tipo):
        conn = None
        try:
            conn = Connection.connectionDB()
            # Nota: SQL Server permite literales de cadena, pero asegúrate de que 'tabla' sea segura
            sql = f"""SELECT id_piezometro, nombre_piezometro, '{tipo}' AS tipo FROM {tabla} WHERE id_proyecto = ?
            AND estado_piezometro = 1;"""
            cur = conn.cursor()
            cur.execute(sql, (idproyecto,))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al obtener piezometros:", e)
            return None  
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlListarCeldasProyecto(idproyecto):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = f"""SELECT id_celda, id_proyecto, nombre_celda FROM celdas WHERE id_proyecto = ?;"""
            cur = conn.cursor()
            cur.execute(sql, (idproyecto,))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al obtener celdas:", e)
            return None  
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlListarTopografiasComponente(idzona, tipo, estado):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = f"""SELECT DISTINCT * FROM instrumentacion i INNER JOIN topografias t ON i.id_equipo = t.id_topografia
            WHERE i.id_componente = ? AND i.tipo_equipo = ? AND i.estado_instrumentacion = ? ORDER BY i.nombre_equipo;"""
            cur = conn.cursor()
            cur.execute(sql, (idzona, tipo, estado))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al obtener topografias:", e)
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlListarPrismasComponente(idzona, tipo, estado):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = """SELECT id_instrumentacion, id_componente, tipo_equipo, nombre_equipo, tabla_equipo, estado_instrumentacion
            FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = ? AND estado_instrumentacion = ? ORDER BY nombre_equipo;"""
            cur = conn.cursor()
            cur.execute(sql, (idzona, tipo, estado))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al obtener Prismas:", e)
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlListarPrismasAutoNuevosComponente(idzona, tipo, prismas):
        conn = None
        # Generación dinámica de placeholders compatible con pyodbc
        placeholders = ', '.join(['?' for _ in prismas])
        params = [idzona, tipo] + prismas
        try:
            conn = Connection.connectionDB()
            sql = f"""SELECT id_instrumentacion, id_componente, tipo_equipo, nombre_equipo, tabla_equipo, estado_instrumentacion
            FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = ? AND nombre_equipo IN ({placeholders})
            AND estado_instrumentacion = 1;"""
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al obtener nuevos prismas:", e)
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlListarInclinometrosComponente(idzona, tipo, estado):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = """SELECT DISTINCT i.* FROM instrumentacion i INNER JOIN inclinometro_encabezado d ON i.id_equipo = d.id_inclinometro
            WHERE i.id_componente = ? AND i.tipo_equipo = ? AND i.estado_instrumentacion = ? ORDER BY i.nombre_equipo;"""
            cur = conn.cursor()
            cur.execute(sql, (idzona, tipo, estado))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al obtener inclinometros:", e)
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlListarPiezometrosCuerdaComponente(idproyecto, idzona, tipo, estado):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = f"""SELECT DISTINCT i.* FROM instrumentacion i INNER JOIN piezometrocuerda_detalle{idproyecto} d
            ON i.id_equipo = d.id_piezometro WHERE i.id_componente = ? AND i.tipo_equipo = ? AND i.estado_instrumentacion = ? ORDER BY i.nombre_equipo;"""
            cur = conn.cursor()
            cur.execute(sql, (idzona, tipo, estado))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al obtener cuerdas:", e)
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlListarPiezometrosManualComponente(idproyecto, idzona, tipo, estado):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = f"""SELECT DISTINCT i.* FROM instrumentacion i INNER JOIN piezometromanual_detalle{idproyecto} d
            ON i.id_equipo = d.id_piezometro WHERE i.id_componente = ? AND i.tipo_equipo = ? AND i.estado_instrumentacion = ? ORDER BY i.nombre_equipo;"""
            cur = conn.cursor()
            cur.execute(sql, (idzona, tipo, estado))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al obtener casagrande:", e)
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlListarPluviometrosComponente(idproyecto, idzona, tipo, estado):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = f"""SELECT DISTINCT i.* FROM instrumentacion i INNER JOIN pluviometro_detalle{idproyecto} d
            ON i.id_equipo = d.id_pluviometro WHERE i.id_componente = ? AND i.tipo_equipo = ? AND i.estado_instrumentacion = ? ORDER BY i.nombre_equipo;"""
            cur = conn.cursor()
            cur.execute(sql, (idzona, tipo, estado))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al obtener pluviometros:", e)
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlListarAcelerografosComponente(idproyecto, idzona, tipo, estado):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = f"""SELECT DISTINCT i.* FROM instrumentacion i INNER JOIN acelerografo_detalle{idproyecto} d
            ON i.id_equipo = d.id_acelerografo WHERE i.id_componente = ? AND i.tipo_equipo = ? AND i.estado_instrumentacion = ? ORDER BY i.nombre_equipo;"""
            cur = conn.cursor()
            cur.execute(sql, (idzona, tipo, estado))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al obtener acelerografos:", e)
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlListarEquiposTipoComponente(idcomponente, tipo):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = """SELECT * FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = ? AND estado_instrumentacion = 1 ORDER BY nombre_equipo;"""
            cur = conn.cursor()
            cur.execute(sql, (idcomponente, tipo))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al obtener equipos componente:", e)
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlValidarAcelerografoComponente(idproyecto, idacelero, tipo):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = f"""SELECT COUNT(*) FROM instrumentacion i INNER JOIN acelerografo_detalle{idproyecto} d
            ON i.id_equipo = d.id_acelerografo WHERE i.id_instrumentacion = ? AND i.tipo_equipo = ? AND i.estado_instrumentacion = 1;"""
            cur = conn.cursor()
            cur.execute(sql, (idacelero, tipo))
            # fetchone()[0] funciona igual para COUNT(*) en SQL Server
            count = cur.fetchone()[0]
            return count > 0
        except Exception as e:
            print("Error al validar acelerografo:", e)
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlListarCeldasComponente(idproyecto, idzona, tipo, estado):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = f"""SELECT DISTINCT i.* FROM instrumentacion i INNER JOIN celda_detalle{idproyecto} d
            ON i.id_equipo = d.id_celda WHERE i.id_componente = ? AND i.tipo_equipo = ? AND i.estado_instrumentacion = ? ORDER BY i.nombre_equipo;"""
            cur = conn.cursor()
            cur.execute(sql, (idzona, tipo, estado))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al obtener celdas:", e)
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlListarCotasTerrenoComponente(idproyecto, idzona, tipo, estado):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = f"""SELECT DISTINCT i.* FROM instrumentacion i INNER JOIN cotaterreno_detalle{idproyecto} d
            ON i.id_equipo = d.id_terreno WHERE i.id_componente = ? AND i.tipo_equipo = ? AND i.estado_instrumentacion = ?;"""
            cur = conn.cursor()
            cur.execute(sql, (idzona, tipo, estado))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al obtener cotas terreno:", e)
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlListarSondajestdrComponente(idproyecto, idzona, tipo, estado):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = f"""SELECT DISTINCT i.* FROM instrumentacion i INNER JOIN sondajetdr_detalle{idproyecto} d
            ON i.id_equipo = d.id_sondajetdr WHERE i.id_componente = ? AND i.tipo_equipo = ? AND i.estado_instrumentacion = ? ORDER BY i.nombre_equipo;"""
            cur = conn.cursor()
            cur.execute(sql, (idzona, tipo, estado))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al obtener sondajes tdr:", e)
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlListarEquiposComponente(idzona, tipo, estado):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = f"""SELECT DISTINCT i.* FROM instrumentacion i INNER JOIN equipos e ON i.id_equipo = e.id_equipo
            WHERE i.id_componente = ? AND i.tipo_equipo = ? AND i.estado_instrumentacion = ? ORDER BY i.nombre_equipo;"""
            cur = conn.cursor()
            cur.execute(sql, (idzona, tipo, estado))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al obtener equipos adicionales:", e)
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlListarPrismasVirtualesComponente(idzona, tipo, estado):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = f"""SELECT DISTINCT i.* FROM instrumentacion i INNER JOIN prismas_virtuales p ON i.id_equipo = p.id_prisma_virtual
            WHERE i.id_componente = ? AND i.tipo_equipo = ? AND i.estado_instrumentacion = ? ORDER BY i.nombre_equipo;"""
            cur = conn.cursor()
            cur.execute(sql, (idzona, tipo, estado))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al obtener prismas virtuales:", e)
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlListarComponenteEquipoTopografia(idinstrumento, tipo):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = """SELECT DISTINCT * FROM instrumentacion i INNER JOIN topografias t ON i.id_equipo = t.id_topografia
            WHERE i.id_instrumentacion = ? AND i.tipo_equipo = ?;"""
            cur = conn.cursor()
            cur.execute(sql, (idinstrumento, tipo))
            rows = cur.fetchall() 
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al obtener equipo topo:", e)
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlListarComponenteEquipo(idinstrumento, tipo):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = """SELECT * FROM instrumentacion WHERE id_instrumentacion = ? AND tipo_equipo = ?;"""
            cur = conn.cursor()
            cur.execute(sql, (idinstrumento, tipo))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al obtener equipo:", e)
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlListarFechasInclinometroCodigo(idcomponente, idinstrumento, proyectoid):
        conn = None
        params = [proyectoid, idinstrumento, idcomponente, proyectoid, idinstrumento, idcomponente, proyectoid, idinstrumento, idcomponente]
        # SQL Server 2008+ soporta CTEs (WITH)
        sql = """WITH lecturas_validas AS (
            SELECT e.fecha_inclinometro, i.tipo_inclinometro, e.estado_base
            FROM inclinometro_encabezado e
            INNER JOIN inclinometros i ON i.id_inclinometro = e.id_inclinometro
            INNER JOIN instrumentacion t ON i.id_inclinometro = t.id_equipo
            INNER JOIN componentes c ON t.id_componente = c.id_componente
            WHERE c.id_proyecto = ?
            AND t.id_instrumentacion = ?
            AND c.id_componente = ?
            AND e.estado_base != 2
        ),
        lecturas_minimas AS (
            SELECT e.fecha_inclinometro, i.tipo_inclinometro, e.estado_base
            FROM inclinometro_encabezado e
            INNER JOIN inclinometros i ON i.id_inclinometro = e.id_inclinometro
            INNER JOIN instrumentacion t ON i.id_inclinometro = t.id_equipo
            INNER JOIN componentes c ON t.id_componente = c.id_componente
            WHERE c.id_proyecto = ?
            AND t.id_instrumentacion = ?
            AND c.id_componente = ?
            AND e.fecha_inclinometro = (
                SELECT MIN(e2.fecha_inclinometro)
                FROM inclinometro_encabezado e2
                INNER JOIN inclinometros i2 ON i2.id_inclinometro = e2.id_inclinometro
                INNER JOIN instrumentacion t2 ON i2.id_inclinometro = t2.id_equipo
                INNER JOIN componentes c2 ON t2.id_componente = c2.id_componente
                WHERE c2.id_proyecto = ?
                    AND t2.id_instrumentacion = ?
                    AND c2.id_componente = ?
            )
        )
        SELECT * FROM lecturas_validas
        UNION ALL
        SELECT * FROM lecturas_minimas
        WHERE NOT EXISTS (SELECT 1 FROM lecturas_validas) ORDER BY fecha_inclinometro;"""
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
            print("Error al consultar fechas inclinometros: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlListarFechasPiezometros(idcomponente, idinstrumento, proyectoid):
        conn = None
        sql = f"""SELECT * FROM inclinometro_encabezado e
            INNER JOIN inclinometros i ON i.id_inclinometro = e.id_inclinometro
            INNER JOIN instrumentacion t ON i.id_inclinometro = t.id_equipo
            INNER JOIN componentes c ON t.id_componente = c.id_componente
            WHERE c.id_proyecto = ? AND t.id_instrumentacion = ? AND c.id_componente = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyectoid, idinstrumento, idcomponente))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al consultar encabezado piezometros: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlListarFechasPiezometroCuerdaCodigo(idcomponente, idinstrumento, proyectoid):
        conn = None
        sql = f"""SELECT d.fecha_cuerda FROM piezometrocuerda_detalle{proyectoid} d
        INNER JOIN piezometrocuerdas p ON d.id_piezometro = p.id_piezometro
        INNER JOIN instrumentacion t ON p.id_piezometro = t.id_equipo
		INNER JOIN componentes c ON t.id_componente = c.id_componente
        WHERE c.id_proyecto = ? AND t.id_instrumentacion = ? AND c.id_componente = ? 
		ORDER BY d.fecha_cuerda;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyectoid, idinstrumento, idcomponente))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al consultar fechas piezometros cuerda: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlListarFechasPiezometroManualCodigo(idcomponente, idinstrumento, proyectoid):
        conn = None
        sql = f"""SELECT d.fecha_piezometro FROM piezometromanual_detalle{proyectoid} d
        INNER JOIN piezometromanuales p ON d.id_piezometro = p.id_piezometro
        INNER JOIN instrumentacion t ON p.id_piezometro = t.id_equipo
		INNER JOIN componentes c ON t.id_componente = c.id_componente
        WHERE c.id_proyecto = ? AND t.id_instrumentacion = ? AND c.id_componente = ? 
		ORDER BY d.fecha_piezometro;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyectoid, idinstrumento, idcomponente))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al consultar fechas piezometros manual: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlListarFechasSondajetdrCodigo(tabla, idcomponente, idinstrumento):
        conn = None
        # Corrección SQL SERVER: Todos los campos SELECT no agregados deben estar en GROUP BY
        sql = f"""SELECT d.fecha_detalle, i.tipo_equipo, s.base_sondajetdr FROM {tabla} d
        INNER JOIN sondajestdr s ON d.id_sondajetdr = s.id_sondajetdr
		INNER JOIN instrumentacion i ON s.id_sondajetdr = i.id_equipo
		INNER JOIN componentes c ON i.id_componente = c.id_componente
        WHERE i.id_instrumentacion = ? AND c.id_componente = ?
		GROUP BY d.fecha_detalle, i.tipo_equipo, s.base_sondajetdr 
        ORDER BY d.fecha_detalle;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idinstrumento, idcomponente))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al consultar fechas tdr: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlListarComponentePrisma(idinstrumento, estado):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = """SELECT id_instrumentacion, id_componente, tipo_equipo, nombre_equipo, tabla_equipo, estado_instrumentacion
            FROM instrumentacion WHERE id_instrumentacion = ? AND estado_instrumentacion = ?;"""
            cur = conn.cursor()
            cur.execute(sql, (idinstrumento, estado))
            rows = cur.fetchall() 
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al obtener equipo instrumentacion:", e)
            return None  
        finally:
            if conn:
                conn.close()
                
    @staticmethod
    def mdlListarArchivosLidar(id_componente):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = "SELECT t.nombre_topografia,t.archivo_topografia from topografias t INNER JOIN instrumentacion i ON t.id_topografia=i.id_equipo WHERE t.tipo_topografia='LAS' AND i.id_componente=? AND i.tabla_equipo='topografias'"
            cur = conn.cursor()
            cur.execute(sql, (id_componente,))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al obtener equipo:", e)
            return None
        finally:
            if conn:
                conn.close()
                
    @staticmethod
    def mdlGuardarPreferenciasMarcado(idproyecto, modulo, lista_preferencias):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            nombre_plantilla = "DEFAULT_analisis"
            cantidad = len(lista_preferencias)

            # Buscar si ya existe la preferencia por defecto de este proyecto/modulo
            cur.execute(
                """SELECT id_preferencia FROM preferencias_marcado
                   WHERE id_proyecto = ? AND modulo = ? AND nombre_plantilla = ?""",
                (idproyecto, modulo, nombre_plantilla)
            )
            row = cur.fetchone()

            if row:
                id_preferencia = row[0]
                cur.execute(
                    """UPDATE preferencias_marcado
                       SET cantidad_equipos = ?, fecha_registro = GETDATE()
                       WHERE id_preferencia = ?""",
                    (cantidad, id_preferencia)
                )
                cur.execute(
                    "DELETE FROM preferencias_marcado_detalle WHERE id_preferencia = ?",
                    (id_preferencia,)
                )
            else:
                cur.execute(
                    """INSERT INTO preferencias_marcado (id_proyecto, modulo, nombre_plantilla, cantidad_equipos)
                       OUTPUT INSERTED.id_preferencia
                       VALUES (?, ?, ?, ?)""",
                    (idproyecto, modulo, nombre_plantilla, cantidad)
                )
                id_preferencia = cur.fetchone()[0]

            # Insertar el detalle
            sql_detalle = """INSERT INTO preferencias_marcado_detalle
                        (id_preferencia, id_componente, id_instrumentacion)
                        VALUES (?, ?, ?)"""
            for id_comp, id_inst in lista_preferencias:
                cur.execute(sql_detalle, (id_preferencia, id_comp, id_inst))

            conn.commit()
            return True
        except Exception as e:
            print("Error mdlGuardarPreferenciasMarcado:", e)
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlObtenerPreferenciasMarcado(idproyecto, modulo):
        conn = None
        try:
            conn = Connection.connectionDB()

            sql = """SELECT d.id_componente, d.id_instrumentacion
            FROM dbo.preferencias_marcado_detalle AS d
            INNER JOIN dbo.preferencias_marcado AS p
            ON p.id_preferencia = d.id_preferencia
            WHERE p.id_preferencia = (
                SELECT TOP 1 id_preferencia
                FROM dbo.preferencias_marcado
                WHERE id_proyecto = ?
                AND modulo = ?
                ORDER BY id_preferencia DESC
            )
            """
            cur = conn.cursor()
            cur.execute(sql, (idproyecto, modulo))
            rows = cur.fetchall()

            return [tuple(row) for row in rows]

        except Exception as e:
            print("Error mdlObtenerPreferenciasMarcado:", e)
            return []
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlObtenerPreferenciasMarcadoAnalisis(idproyecto, modulo):
        conn = None
        try:
            conn = Connection.connectionDB()

            sql = """SELECT d.id_componente, d.id_instrumentacion
            FROM dbo.preferencias_marcado_detalle AS d
            INNER JOIN dbo.preferencias_marcado AS p
            ON p.id_preferencia = d.id_preferencia
            WHERE p.id_proyecto = ? AND p. modulo = ?
            """
            cur = conn.cursor()
            cur.execute(sql, (idproyecto, modulo))
            rows = cur.fetchall()

            return [tuple(row) for row in rows]

        except Exception as e:
            print("Error mdlObtenerPreferenciasMarcadoAnalisis:", e)
            return []
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlGuardarPlantillaNombrada(idproyecto, modulo_base, nombre_plantilla, lista_preferencias, cantidad = 0):
        conn = None

        try:
            if idproyecto is None:
                raise ValueError("idproyecto no puede ser None")

            if not modulo_base:
                raise ValueError("modulo_base es obligatorio")

            if not nombre_plantilla:
                raise ValueError("nombre_plantilla es obligatorio")

            lista_preferencias = lista_preferencias or []

            # Si no se recibe cantidad, se calcula automáticamente
            if cantidad is None:
                cantidad = len(lista_preferencias)

            conn = Connection.connectionDB()
            cur = conn.cursor()

            # Buscar plantilla existente
            cur.execute(
                """
                SELECT id_preferencia
                FROM dbo.preferencias_marcado
                WHERE id_proyecto = ?
                AND modulo = ?
                AND nombre_plantilla = ?
                """,
                (idproyecto, modulo_base, nombre_plantilla)
            )

            row = cur.fetchone()

            if row:
                # La plantilla ya existe
                id_preferencia = row[0]

                cur.execute(
                    """
                    UPDATE dbo.preferencias_marcado
                    SET cantidad_equipos = ?,
                        fecha_registro = GETDATE()
                    WHERE id_preferencia = ?
                    """,
                    (cantidad, id_preferencia)
                )

                cur.execute(
                    """
                    DELETE FROM dbo.preferencias_marcado_detalle
                    WHERE id_preferencia = ?
                    """,
                    (id_preferencia,)
                )

            else:
                # Crear nueva plantilla y obtener el ID generado
                cur.execute(
                    """
                    INSERT INTO dbo.preferencias_marcado
                        (
                            id_proyecto,
                            modulo,
                            nombre_plantilla,
                            cantidad_equipos
                        )
                    OUTPUT INSERTED.id_preferencia
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        idproyecto,
                        modulo_base,
                        nombre_plantilla,
                        cantidad
                    )
                )

                row_id = cur.fetchone()

                if not row_id or row_id[0] is None:
                    raise RuntimeError(
                        "No se pudo obtener el id_preferencia generado"
                    )

                id_preferencia = row_id[0]

            # Insertar detalle
            sql_detalle = """
                INSERT INTO dbo.preferencias_marcado_detalle
                    (
                        id_preferencia,
                        id_componente,
                        id_instrumentacion
                    )
                VALUES (?, ?, ?)
            """

            for id_comp, id_inst in lista_preferencias:
                cur.execute(
                    sql_detalle,
                    (id_preferencia, id_comp, id_inst)
                )

            conn.commit()
            return True

        except Exception as e:
            print("Error mdlGuardarPlantillaNombrada:", e)

            if conn:
                conn.rollback()

            return False

        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlListarPlantillas(idproyecto, modulo_base):
        """
        Lista las plantillas guardadas para un proyecto/módulo, leyendo directamente
        del maestro (ya no se necesita parsear el string 'modulo_PLANTILLA_nombre').
        """
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = """SELECT nombre_plantilla, cantidad_equipos, fecha_registro, id_preferencia
                    FROM preferencias_marcado
                    WHERE id_proyecto = ? AND modulo = ?
                    ORDER BY nombre_plantilla"""
            cur = conn.cursor()
            cur.execute(sql, (idproyecto, modulo_base))
            rows = cur.fetchall()
            return [tuple(row) for row in rows]
        except Exception as e:
            print("Error mdlListarPlantillas:", e)
            return []
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlObtenerPreferenciasPorNombre(idproyecto, modulo_base, id_plantilla):
        """
        Obtiene los equipos marcados de una plantilla específica (para aplicarla al árbol).
        """
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = """SELECT d.id_componente, d.id_instrumentacion
                    FROM preferencias_marcado_detalle d
                    INNER JOIN preferencias_marcado p ON p.id_preferencia = d.id_preferencia
                    WHERE p.id_proyecto = ? AND p.modulo = ? AND p.id_preferencia = ?"""
            cur = conn.cursor()
            cur.execute(sql, (idproyecto, modulo_base, id_plantilla))
            rows = cur.fetchall()
            return [tuple(row) for row in rows]
        except Exception as e:
            print("Error mdlObtenerPreferenciasPorNombre:", e)
            return []
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlEliminarPlantilla(idproyecto, modulo_base, id_plantilla):
        """
        Elimina una plantilla. Gracias a ON DELETE CASCADE en la FK de
        preferencias_marcado_detalle, basta con borrar el registro maestro.
        """
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM preferencias_marcado WHERE id_proyecto = ? AND modulo = ? AND id_preferencia = ?",
                (idproyecto, modulo_base, id_plantilla)
            )
            conn.commit()
            return True
        except Exception as e:
            print("Error mdlEliminarPlantilla:", e)
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlRenombrarPlantilla(idproyecto, modulo_base, nombre_actual, nombre_nuevo):
        """
        Renombra una plantilla existente, validando que el nuevo nombre
        no choque con otra plantilla ya guardada en el mismo proyecto/módulo.
        """
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()

            # Verificar que no exista ya una plantilla con el nuevo nombre
            cur.execute(
                "SELECT COUNT(*) FROM preferencias_marcado WHERE id_proyecto = ? AND modulo = ? AND nombre_plantilla = ?",
                (idproyecto, modulo_base, nombre_nuevo)
            )
            existe = cur.fetchone()[0]
            if existe > 0:
                print("Error mdlRenombrarPlantilla: ya existe una plantilla con ese nombre")
                return False

            cur.execute(
                "UPDATE preferencias_marcado SET nombre_plantilla = ? WHERE id_proyecto = ? AND modulo = ? AND nombre_plantilla = ?",
                (nombre_nuevo, idproyecto, modulo_base, nombre_actual)
            )
            conn.commit()
            return True
        except Exception as e:
            print("Error mdlRenombrarPlantilla:", e)
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()