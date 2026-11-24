from services.security.apis.conexiones.connection import Connection
from datetime import datetime, date, time


def _norm_fecha(f):
    if isinstance(f, datetime):
        return f.date().isoformat()
    if isinstance(f, date):
        return f.isoformat()
    s = str(f).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%y"):
        try:
            return datetime.strptime(s[:10] if fmt.startswith("%Y-") else s, fmt).date().isoformat()
        except ValueError:
            continue
    return s


def _norm_hora(h):
    if isinstance(h, datetime):
        return h.time().strftime("%H:%M:%S")
    if isinstance(h, time):
        return h.strftime("%H:%M:%S")
    s = str(h).strip()
    for fmt in ("%H:%M:%S", "%H:%M", "%I:%M:%S %p", "%I:%M %p"):
        try:
            return datetime.strptime(s, fmt).strftime("%H:%M:%S")
        except ValueError:
            continue
    return s


class VoladuraModel:

    # ------------------------------------------------------------------
    # VOLADURAS (equipo)
    # ------------------------------------------------------------------
    @staticmethod
    def mdlGuardarNuevaVoladura(proyecto_id, datos):
        conn = None
        try:
            conn = Connection.connectionDB()
            if not conn:
                return False
            cur = conn.cursor()
            nombre, codigo, comentario, estado, idcomponente = datos
            cur.execute("""SELECT 1 FROM instrumentacion
                           WHERE id_componente = ? AND nombre_equipo = ? AND tipo_equipo = 'VOLADURA';""",
                        (idcomponente, nombre))
            if cur.fetchone():
                return "NO"
            cur.execute("""INSERT INTO voladuras (id_proyecto, nombre_voladura, codigo_voladura, comentario_voladura, estado_voladura)
                           OUTPUT INSERTED.id_voladura VALUES (?, ?, ?, ?, ?);""",
                        (proyecto_id, nombre, codigo, comentario, estado))
            voladura_id = cur.fetchone()[0]
            cur.execute("""SET NOCOUNT ON;
                           INSERT INTO instrumentacion (id_componente, tipo_equipo, nombre_equipo, id_equipo, tabla_equipo, estado_instrumentacion)
                           VALUES (?, ?, ?, ?, ?, ?);
                           SELECT CAST(SCOPE_IDENTITY() AS INT);""",
                        (idcomponente, 'VOLADURA', nombre, voladura_id, 'voladuras', estado))
            idinstrumento = cur.fetchone()[0]
            conn.commit()
            return idinstrumento if idinstrumento else True
        except Exception:
            import traceback
            traceback.print_exc()
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    # Devuelve filas (id_voladura, id_proyecto, nombre_voladura, id_componente) o None
    @staticmethod
    def mdlListaVoladurasProyecto(proyecto_id):
        conn = None
        try:
            conn = Connection.connectionDB()
            if not conn:
                return None
            cur = conn.cursor()
            cur.execute("""SELECT v.id_voladura, v.id_proyecto, v.nombre_voladura, i.id_componente
                           FROM voladuras v
                           LEFT JOIN instrumentacion i
                                  ON i.id_equipo = v.id_voladura AND i.tipo_equipo = 'VOLADURA'
                           WHERE v.id_proyecto = ? ORDER BY v.nombre_voladura;""", (proyecto_id,))
            filas = [tuple(r) for r in cur.fetchall()]
            return filas if filas else None
        except Exception:
            import traceback
            traceback.print_exc()
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlListarComponentesProyecto(proyectoid):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute("""SELECT id_componente, nombre_componente FROM componentes
                           WHERE id_proyecto = ? ORDER BY nombre_componente;""", (proyectoid,))
            results = [tuple(row) for row in cur.fetchall()]
            return results if results else None
        except Exception as e:
            print("Error al listar componentes:", e)
            return None
        finally:
            if conn:
                conn.close()

    # Info de la voladura a partir del id de instrumentación
    @staticmethod
    def mdlObtenerInfoVoladura(idinstrumento):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute("""SELECT v.id_voladura, v.nombre_voladura, v.codigo_voladura,
                                  v.comentario_voladura, v.estado_voladura, i.id_componente
                           FROM voladuras v
                           INNER JOIN instrumentacion i ON v.id_voladura = i.id_equipo
                           WHERE i.id_instrumentacion = ? AND i.tipo_equipo = 'VOLADURA';""",
                        (idinstrumento,))
            row = cur.fetchone()
            return tuple(row) if row else None
        except Exception as e:
            print("Error al consultar info voladura: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    # datos = [nombre, codigo, comentario, estado, idvoladura]
    # data  = [idcomponente, nombre, estado, idinstrumentacion]
    @staticmethod
    def mdlActualizarVoladura(datos, data):
        conn = None
        try:
            conn = Connection.connectionDB()
            if not conn:
                return False
            cur = conn.cursor()
            cur.execute("""UPDATE voladuras
                           SET nombre_voladura = ?, codigo_voladura = ?, comentario_voladura = ?, estado_voladura = ?
                           WHERE id_voladura = ?;""", datos)
            cur.execute("""UPDATE instrumentacion
                           SET id_componente = ?, nombre_equipo = ?, estado_instrumentacion = ?
                           WHERE id_instrumentacion = ? AND tipo_equipo = 'VOLADURA';""", data)
            conn.commit()
            return True
        except Exception as e:
            print("Error al editar voladura: " + str(e))
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    # Valida si ya existe una voladura con ese nombre en el proyecto
    @staticmethod
    def mdlComprobarExisteNombreVoladura(proyecto, nombre):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute("SELECT * FROM voladuras WHERE id_proyecto = ? AND nombre_voladura = ?;",
                        (proyecto, nombre))
            row = cur.fetchone()
            return (True, tuple(row)) if row else (False, None)
        except Exception as e:
            print("Error al comprobar voladura: " + str(e))
            return False, None
        finally:
            if conn:
                conn.close()

    # Eliminar voladura
    def mdlEliminarVoladura(idinstrumento):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            query_select = """SELECT * FROM instrumentacion WHERE id_instrumentacion = ? AND tipo_equipo = 'VOLADURA';"""
            cursor.execute(query_select, (idinstrumento,))
            row = cursor.fetchone()
            datapluvio = tuple(row) if row else None
            if not datapluvio:
                return None
            cursor.execute("""DELETE FROM instrumentacion WHERE id_instrumentacion = ? AND tipo_equipo = 'VOLADURA';""", (idinstrumento,))
            borrados = cursor.rowcount      # ANTES del commit
            conn.commit()
            return datapluvio if borrados > 0 else None
        except Exception as e:
            print(f"Error al eliminar voladura: {e}")
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()
    
    # Elimina la voladura
    @staticmethod
    def mdlEliminarVoladuraData(tabla, idvoladura):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            cursor.execute("""SELECT 1 FROM instrumentacion
                WHERE id_equipo = ? AND tipo_equipo = 'VOLADURA';""", (idvoladura,))
            if cursor.fetchone():
                return True  # sigue en otro componente: conservar pluviómetro y data
            cursor.execute("SELECT 1 FROM sys.tables WHERE name = ?", (tabla,))
            if cursor.fetchone():
                cursor.execute(f"DELETE FROM {tabla} WHERE id_voladura = ?;", (idvoladura,))
            cursor.execute("DELETE FROM voladuras WHERE id_voladura = ?;", (idvoladura,))
            cursor.execute("DELETE FROM voladuras_estilo WHERE id_voladura = ?;", (idvoladura,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al eliminar data voladura: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    # Crea voladura + instrumentacion desde un formato Excel. Devuelve id_voladura o None
    @staticmethod
    def mdlRegistrarFormatoVoladura(proyecto_id, nombre, codigo, comentario, idcomponente):
        conn = None
        try:
            conn = Connection.connectionDB()
            if not conn:
                return None
            cur = conn.cursor()
            cur.execute("""INSERT INTO voladuras (id_proyecto, nombre_voladura, codigo_voladura, comentario_voladura, estado_voladura)
                           OUTPUT INSERTED.id_voladura VALUES (?, ?, ?, ?, ?);""",
                        (proyecto_id, nombre, codigo, comentario, 1))
            voladura_id = cur.fetchone()[0]
            cur.execute("""INSERT INTO instrumentacion (id_componente, tipo_equipo, nombre_equipo, id_equipo, tabla_equipo, estado_instrumentacion)
                           VALUES (?, ?, ?, ?, ?, ?);""",
                        (idcomponente, 'VOLADURA', nombre, voladura_id, 'voladuras', 1))
            conn.commit()
            return voladura_id
        except Exception:
            import traceback
            traceback.print_exc()
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()

    # ------------------------------------------------------------------
    # LECTURAS (tabla por proyecto: voladura_detalle{idproyecto})
    # Columnas: id_detalle, id_voladura, fecha_detalle, ubicacion_detalle,
    #           cota_detalle, observacion_detalle, estado_detalle
    # ------------------------------------------------------------------

    # data = [(id_voladura, fecha, hora, ubicacion, cota, observacion), ...]
    @staticmethod
    def mdlGuardarVoladuraTabla(idproyecto, data):
        conn = None
        tabla = f"voladura_detalle{int(idproyecto)}"
        sql_insert = f"""INSERT INTO {tabla}
                         (id_voladura, fecha_detalle, ubicacion_detalle, cota_detalle, observacion_detalle)
                         VALUES (?, ?, ?, ?, ?);"""
        try:
            if not data:
                return False
            conn = Connection.connectionDB()
            if not conn:
                return False
            cursor = conn.cursor()
            cursor.execute(f"""
                IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = '{tabla}')
                BEGIN
                    CREATE TABLE {tabla} (
                        id_detalle INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
                        id_voladura INT NOT NULL,
                        fecha_detalle DATETIME2(0) NOT NULL,
                        ubicacion_detalle VARCHAR(500),
                        cota_detalle DECIMAL(18,6) NULL,
                        observacion_detalle VARCHAR(500),
                        estado_detalle INT NOT NULL DEFAULT 1
                    )
                END
            """)
            conn.commit()

            # existentes de TODAS las voladuras del archivo: (id_voladura, fecha-hora)
            ids = list({int(f[0]) for f in data})
            placeholders = ",".join("?" * len(ids))
            cursor.execute(
                f"SELECT id_voladura, fecha_detalle FROM {tabla} WHERE id_voladura IN ({placeholders});", ids)
            existentes = {(r[0], r[1].strftime('%Y-%m-%d %H:%M:%S')) for r in cursor.fetchall()}

            lote = []
            for fila in data:
                fecha_hora = f"{_norm_fecha(fila[1])} {_norm_hora(fila[2])}"
                clave = (int(fila[0]), fecha_hora)
                if clave in existentes:
                    continue
                existentes.add(clave)
                cota = None if fila[4] is None or fila[4] == "" else float(fila[4])
                lote.append((clave[0], fecha_hora, fila[3], cota, fila[5]))
                if len(lote) >= 1000:
                    cursor.executemany(sql_insert, lote)
                    lote = []
            if lote:
                cursor.executemany(sql_insert, lote)
            conn.commit()
            return True
        except Exception:
            import traceback
            traceback.print_exc()
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlObtenerDataVoladuras(idproyecto, ids):
        conn = None
        tabla = f"voladura_detalle{int(idproyecto)}"
        try:
            if not ids:
                return None
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute("SELECT OBJECT_ID(?, 'U');", (tabla,))
            if cur.fetchone()[0] is None:
                return None  # el proyecto aún no tiene lecturas
            placeholders = ', '.join(['?' for _ in ids])
            sql = f"""SELECT 'VOLADURA', v.nombre_voladura,
                             CONVERT(varchar(19), d.fecha_detalle, 120),
                             COALESCE(d.ubicacion_detalle, ''), d.cota_detalle, COALESCE(d.observacion_detalle, ''),
                             CASE WHEN d.estado_detalle = 1 THEN 'Activo' ELSE 'Omitido' END,
                             d.id_detalle
                      FROM {tabla} d
                      INNER JOIN voladuras v ON d.id_voladura = v.id_voladura
                      WHERE d.id_voladura IN ({placeholders})
                      ORDER BY d.fecha_detalle;"""
            cur.execute(sql, [int(i) for i in ids])
            rows = [tuple(r) for r in cur.fetchall()]
            return rows if rows else None
        except Exception:
            import traceback
            traceback.print_exc()
            return None
        finally:
            if conn:
                conn.close()

    # datos = [fecha, hora, ubicacion, cota, observacion, id_detalle]
    @staticmethod
    def mdlActualizarLecturaVoladura(idproyecto, datos):
        conn = None
        tabla = f"voladura_detalle{int(idproyecto)}"
        try:
            fecha, hora, ubic, cota, obs, iddetalle = datos
            conn = Connection.connectionDB()
            if not conn:
                return False
            cur = conn.cursor()
            cur.execute(f"""UPDATE {tabla}
                            SET fecha_detalle = ?, ubicacion_detalle = ?, cota_detalle = ?, observacion_detalle = ?
                            WHERE id_detalle = ?;""",
                        (f"{fecha} {hora}", ubic, None if cota in (None, "") else float(cota), obs, iddetalle))
            conn.commit()
            return True
        except Exception:
            import traceback
            traceback.print_exc()
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlCambiarEstadoLecturaVoladura(idproyecto, iddetalle):
        conn = None
        tabla = f"voladura_detalle{int(idproyecto)}"
        try:
            conn = Connection.connectionDB()
            if not conn:
                return False
            cur = conn.cursor()
            cur.execute(f"""UPDATE {tabla}
                            SET estado_detalle = CASE WHEN estado_detalle = 1 THEN 0 ELSE 1 END
                            WHERE id_detalle = ?;""", (iddetalle,))
            conn.commit()
            return True
        except Exception:
            import traceback
            traceback.print_exc()
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlCambiarEstadoLecturaVoladuraBloque(idproyecto, ids):
        conn = None
        tabla = f"voladura_detalle{int(idproyecto)}"
        try:
            if not ids:
                return False
            conn = Connection.connectionDB()
            if not conn:
                return False
            cur = conn.cursor()
            cur.executemany(f"""UPDATE {tabla}
                                SET estado_detalle = CASE WHEN estado_detalle = 1 THEN 0 ELSE 1 END
                                WHERE id_detalle = ?;""", [(int(i),) for i in ids])
            conn.commit()
            return True
        except Exception:
            import traceback
            traceback.print_exc()
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlEliminarLecturaVoladura(idproyecto, iddetalle):
        conn = None
        tabla = f"voladura_detalle{int(idproyecto)}"
        try:
            conn = Connection.connectionDB()
            if not conn:
                return False
            cur = conn.cursor()
            cur.execute(f"DELETE FROM {tabla} WHERE id_detalle = ?;", (iddetalle,))
            conn.commit()
            return True
        except Exception:
            import traceback
            traceback.print_exc()
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlEliminarLecturasBloqueVoladura(idproyecto, ids):
        conn = None
        tabla = f"voladura_detalle{int(idproyecto)}"
        try:
            if not ids:
                return False
            conn = Connection.connectionDB()
            if not conn:
                return False
            cur = conn.cursor()
            cur.executemany(f"DELETE FROM {tabla} WHERE id_detalle = ?;", [(int(i),) for i in ids])
            conn.commit()
            return True
        except Exception:
            import traceback
            traceback.print_exc()
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    # ------------------------------------------------------------------
    # ESTILO
    # ------------------------------------------------------------------

    # Devuelve (grosor, alto, color) o None si no tiene estilo guardado
    @staticmethod
    def mdlObtenerEstiloVoladura(idinstrumento):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute("""SELECT e.grosor, e.alto, e.color
                           FROM instrumentacion i
                           INNER JOIN voladuras_estilo e ON e.id_voladura = i.id_equipo
                           WHERE i.id_instrumentacion = ? AND i.tipo_equipo = 'VOLADURA';""",
                        (idinstrumento,))
            row = cur.fetchone()
            return tuple(row) if row else None
        except Exception:
            import traceback
            traceback.print_exc()
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlGuardarEstiloVoladura(idinstrumento, grosor, alto, color):
        conn = None
        try:
            conn = Connection.connectionDB()
            if not conn:
                return False
            cur = conn.cursor()
            cur.execute("""SELECT id_equipo FROM instrumentacion
                           WHERE id_instrumentacion = ? AND tipo_equipo = 'VOLADURA';""",
                        (idinstrumento,))
            r = cur.fetchone()
            if not r:
                return False
            idvol = r[0]
            cur.execute("""UPDATE voladuras_estilo SET grosor = ?, alto = ?, color = ?
                           WHERE id_voladura = ?;""", (grosor, alto, color, idvol))
            if cur.rowcount == 0:
                cur.execute("""INSERT INTO voladuras_estilo (id_voladura, grosor, alto, color)
                               VALUES (?, ?, ?, ?);""", (idvol, grosor, alto, color))
            conn.commit()
            return True
        except Exception:
            import traceback
            traceback.print_exc()
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    # Devuelve {nombre_voladura: (grosor, alto, color)} de todo el proyecto
    @staticmethod
    def mdlObtenerEstilosVoladuras(proyecto_id):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute("""SELECT v.nombre_voladura, e.grosor, e.alto, e.color
                           FROM voladuras v
                           INNER JOIN voladuras_estilo e ON e.id_voladura = v.id_voladura
                           WHERE v.id_proyecto = ?;""", (proyecto_id,))
            return {str(r[0]): (float(r[1]), float(r[2]), str(r[3])) for r in cur.fetchall()}
        except Exception:
            import traceback
            traceback.print_exc()
            return {}
        finally:
            if conn:
                conn.close()

    # ------------------------------------------------------------------
    # OPERACIONES POR COMPONENTE (menú del grupo "Voladuras")
    # ------------------------------------------------------------------
    def mdlCambiarComponenteVoladuras(idcomponente, nuevocomponente):
        conn = None
        sql = """UPDATE instrumentacion SET id_componente = ? WHERE id_componente = ? AND tipo_equipo = 'VOLADURA';"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # guardar info
            query_select = """SELECT * FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'VOLADURA';"""
            cur.execute(query_select, (idcomponente,))
            results = [tuple(row) for row in cur.fetchall()]
            if results:
                cur.execute(sql, (nuevocomponente, idcomponente))
                conn.commit()
                return results
            else:
                return None
        except Exception as e:
            print("Error al cambiar componente voladuras: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # Elimina TODAS las voladuras de un componente (instrumentación, lecturas, estilo y voladura)
    def mdlEliminarVoladurasComponente(idcomponente):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            query_select = """SELECT * FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'VOLADURA';"""
            cursor.execute(query_select, (idcomponente,))
            results = [tuple(row) for row in cursor.fetchall()]
            if not results:
                return None
            cursor.execute("""DELETE FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'VOLADURA';""", (idcomponente,))
            borrados = cursor.rowcount      # ANTES del commit
            conn.commit()
            return results if borrados > 0 else None
        except Exception as e:
            print(f"Error al eliminar voladuras: {e}")
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlEliminarDataVoladuras(tabla, voladuras):
        conn = None
        if not voladuras:
            return True
        placeholders = ','.join(['?' for _ in voladuras])
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # solo los que ya no están en ningún componente
            cursor.execute(f"""SELECT p.id_voladura FROM voladuras p
                WHERE p.id_voladura IN ({placeholders})
                AND NOT EXISTS (SELECT 1 FROM instrumentacion i
                    WHERE i.id_equipo = p.id_voladura AND i.tipo_equipo = 'VOLADURA');""", voladuras)
            huerfanos = [r[0] for r in cursor.fetchall()]
            if huerfanos:
                ph = ','.join(['?' for _ in huerfanos])
                cursor.execute("SELECT 1 FROM sys.tables WHERE name = ?", (tabla,))
                if cursor.fetchone():
                    cursor.execute(f"DELETE FROM {tabla} WHERE id_voladura IN ({ph});", huerfanos)
                cursor.execute(f"DELETE FROM voladuras WHERE id_voladura IN ({ph});", huerfanos)
                cursor.execute(f"DELETE FROM voladuras_estilo WHERE id_voladura IN ({ph});", huerfanos)
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al eliminar data voladuras: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    # Devuelve (id_instrumentacion, id_componente, nombre_componente) a partir del id_voladura
    @staticmethod
    def mdlTraerDataVoladura(idvoladura):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute("""SELECT i.id_instrumentacion, i.id_componente, c.nombre_componente
                           FROM instrumentacion i
                           INNER JOIN componentes c ON c.id_componente = i.id_componente
                           WHERE i.id_equipo = ? AND i.tipo_equipo = 'VOLADURA';""",
                        (idvoladura,))
            row = cur.fetchone()
            return tuple(row) if row else None
        except Exception:
            import traceback
            traceback.print_exc()
            return None
        finally:
            if conn:
                conn.close()

    def mdlCambiarVoladuraComponente(idinstrumento, nuevocomponente):
        conn = None
        sql = """UPDATE instrumentacion SET id_componente = ? WHERE id_instrumentacion = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (nuevocomponente, idinstrumento))
            conn.commit()
            return True
        except Exception as e:
            print("Error al cambiar componente voladura: " + str(e))
            return False
        finally:
            if conn:
                conn.close()