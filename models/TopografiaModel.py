from sqlite3 import Error
from services.security.apis.conexiones.conexion import Connection

class TopografiaModel:
        
    def mdlObtenerTipoTopografia(proyectoid, idcomponente, idtopo):
        tipo = "TOPOGRAFIA"
        conn = Connection.connectionDB()
        sql = """SELECT t.tipo_topografia, t.archivo_topografia FROM instrumentacion i INNER JOIN topografias t ON i.id_equipo = t.id_topografia
        INNER JOIN componentes c ON i.id_componente = c.id_componente WHERE c.id_proyecto = ? AND c.id_componente = ?
        AND i.tipo_equipo = ? AND i.id_equipo = ?;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (proyectoid, idcomponente, tipo, idtopo))
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al obtener tipo topo: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    # LISTAR DATA COTAS TERRENO DETALLE POR ID    
    def mdlObtenerDataCotasTerrenoDetalle(idsuelo):
        conn = Connection.connectionDB()
        sql = """SELECT s.nombre_terreno, d.fecha_detalle, d.nivel_detalle, d.id_detalle FROM cotaterreno_detalle d INNER JOIN cotasterreno s
        ON d.id_terreno = s.id_terreno WHERE d.id_terreno = ? ORDER BY d.fecha_detalle;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (idsuelo,))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar terreno detalle: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    
    
    
    
    
        
    def mdlRegistrarNuevaTopografia(proyectoid, idcomponente, nombrenuevo, tipo, ubicacion, comentario,fecha_formateada):
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # Iniciar una transacción
            conn.execute('BEGIN')
            # Verificar si el equipo ya existe en la tabla instrumentacion
            sql_check = """SELECT 1 FROM instrumentacion WHERE id_componente = ? AND nombre_equipo = ? AND tipo_equipo = 'TOPOGRAFIA';"""
            cur.execute(sql_check, (idcomponente, nombrenuevo))
            if cur.fetchone():
                return False, None
            # Insertar el equipo en la tabla equipos
            sql_insert = """INSERT INTO topografias (id_proyecto, nombre_topografia, tipo_topografia, archivo_topografia,
            comentario_topografia,fecha_topografia) VALUES (?, ?, ?, ?, ?,?);"""
            cur.execute(sql_insert, (proyectoid, nombrenuevo, tipo, ubicacion, comentario,fecha_formateada))
            # Obtener el ID del equipo recién insertado
            equipo_id = cur.lastrowid
            # Insertar el equipo en la tabla instrumentacion
            sql_insert_instrumentacion = """INSERT INTO instrumentacion (id_componente, tipo_equipo, nombre_equipo, id_equipo, tabla_equipo)
                                            VALUES (?, ?, ?, ?, ?);"""
            cur.execute(sql_insert_instrumentacion, (idcomponente, 'TOPOGRAFIA', nombrenuevo, equipo_id, 'topografias'))
            idinstrumento = cur.lastrowid
            # Confirmar la transacción
            conn.commit()
            return True, idinstrumento
        except Error as e:
            # Realizar rollback en caso de error
            conn.rollback()
            print("Error al guardar topografia: " + str(e))
            return False, None
        finally:
            if conn:
                conn.close()
    
    def mdlCambiarComponenteTopografias(idcomponente, nuevocomponente):
        sql = """UPDATE instrumentacion SET id_componente = ? WHERE id_componente = ? AND tipo_equipo = 'TOPOGRAFIA';"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # guardar info
            query_select = """SELECT DISTINCT * FROM instrumentacion i INNER JOIN topografias t ON i.id_equipo = t.id_topografia
            WHERE i.id_componente = ? AND i.tipo_equipo = 'TOPOGRAFIA';"""
            cur.execute(query_select, (idcomponente,))
            datatopos = cur.fetchall()
            if datatopos:
                cur.execute(sql, (nuevocomponente, idcomponente))
                conn.commit()
                return datatopos
            else:
                return None
        except Error as e:
            print("Error al cambiar componente topografias: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlEliminarTopografias(idcomponente):
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # obtener info
            query_select = """SELECT * FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'TOPOGRAFIA';"""
            cursor.execute(query_select, (idcomponente,))
            datatopos = cursor.fetchall()
            if datatopos:
                query = """DELETE FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'TOPOGRAFIA';"""
                cursor.execute(query, (idcomponente,))
                conn.commit()
                if cursor.rowcount > 0:
                    return datatopos
                else:
                    return None
            else:
                return None
        except Exception as e:
            print(f"Error al eliminar topografias: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlEliminarDataTopografias(topografias):
        placeholders = ','.join(['?' for _ in topografias])
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # eliminar data
            query_select = f"""SELECT * FROM topografias WHERE id_topografia IN ({placeholders});"""
            cursor.execute(query_select, topografias)
            datatopos = cursor.fetchall()
            if datatopos:
                stmt_delete = f"DELETE FROM topografias WHERE id_topografia IN ({placeholders});"
                cursor.execute(stmt_delete, topografias)
                rows_delete = cursor.rowcount
                conn.commit()
                if rows_delete > 0:
                    return datatopos
                else:
                    return None
            else:
                return None
        except Exception as e:
            print(f"Error al eliminar data topografias: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlObtenerInfoTopografia(idinstrumento):
        sql = """SELECT t.* FROM topografias t INNER JOIN instrumentacion i ON t.id_topografia = i.id_equipo WHERE i.id_instrumentacion = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idinstrumento,))
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar info topografia: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlActualizarTopografia(componente, nombrenuevo, comentario, asignarfecha, idinstrumento, idtopografia):
        sql = """UPDATE topografias SET nombre_topografia = ?, comentario_topografia = ?, fecha_topografia = ?  WHERE id_topografia = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (nombrenuevo, comentario, asignarfecha, idtopografia))
            query_instrumentacion = """UPDATE instrumentacion SET id_componente = ?, nombre_equipo = ?
            WHERE id_instrumentacion = ? AND tipo_equipo = 'TOPOGRAFIA';"""
            cur = conn.cursor()
            cur.execute(query_instrumentacion, (componente, nombrenuevo, idinstrumento))
            conn.commit()
            return True
        except Error as e:
            print("Error al editar topografia: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlEliminarTopografia(idinstrumento):
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # obtener info para eliminar data
            query_select = """SELECT i.*, t.archivo_topografia FROM instrumentacion i INNER JOIN topografias t
            ON i.id_equipo = t.id_topografia WHERE i.id_instrumentacion = ? AND i.tipo_equipo = 'TOPOGRAFIA';"""
            cursor.execute(query_select, (idinstrumento,))
            datatopo = cursor.fetchone()
            if datatopo:
                query = """DELETE FROM instrumentacion WHERE id_instrumentacion = ? AND tipo_equipo = 'TOPOGRAFIA';"""
                cursor.execute(query, (idinstrumento,))
                conn.commit()
                if cursor.rowcount > 0:
                    return datatopo
                else:
                    return None
            else:
                return None
        except Exception as e:
            print(f"Error al eliminar topografia: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlEliminarTopografiaData(idtopografia):
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # eliminar data
            stmt_delete = "DELETE FROM topografias WHERE id_topografia = ?;"
            cursor.execute(stmt_delete, (idtopografia,))
            rows_delete = cursor.rowcount
            conn.commit()
            return rows_delete > 0
        except Exception as e:
            print(f"Error al eliminar data topografia: {e}")
            return False
        finally:
            if conn:
                conn.close()
                
    def mdlObtenerFechaTopografia(idtopo):
        sql = """SELECT fecha_topografia FROM topografias WHERE id_topografia = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idtopo,))
            row = cur.fetchone()
            return row[0] if row else "Fecha no disponible"  # Valor por defecto si no hay resultado
        except Error as e:
            print("Error al consultar info topografia: " + str(e))
            return "Error en la consulta"  # Valor por defecto en caso de error
        finally:
            if conn:
                conn.close()
    def mdlRegistrarPrismaVirtual(id_componente, x, y, z, nombre_prisma, radio, color):
        try:
            # Obtener la conexión a la base de datos
            conn = Connection.connectionDB()
            cursor = conn.cursor()

            # Verificar si ya existe un prisma con el mismo nombre
            cursor.execute("SELECT COUNT(*) FROM prismas_virtuales WHERE nombre_prisma_virtual = ?", (nombre_prisma,))
            count = cursor.fetchone()[0]

            # Si existe, modificar el nombre
            if count > 0:
                # Agregar un número al final del nombre
                cursor.execute("SELECT nombre_prisma_virtual FROM prismas_virtuales WHERE nombre_prisma_virtual LIKE ?", (nombre_prisma + "%",))
                existing_names = cursor.fetchall()
                suffix = 1
                new_nombre_prisma = nombre_prisma
                while (new_nombre_prisma,) in existing_names:
                    suffix += 1
                    new_nombre_prisma = f"{nombre_prisma}_{suffix}"
                nombre_prisma = new_nombre_prisma

            # Insertar en la tabla prismas_virtuales
            cursor.execute("""
                INSERT INTO prismas_virtuales (nombre_prisma_virtual, coordenada_x, coordenada_y, coordenada_z, radio_prisma_virtual, color_prisma)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (nombre_prisma, x, y, z, radio, color))

            # Obtener el último ID insertado en prismas_virtuales
            id_prisma_virtual = cursor.lastrowid

            # Insertar en la tabla instrumentacion
            cursor.execute("""
                INSERT INTO instrumentacion (id_componente, tipo_equipo, nombre_equipo, id_equipo, tabla_equipo)
                VALUES (?, 'PRISMAVIRTUAL', ?, ?, 'prismas_virtuales')
            """, (id_componente, nombre_prisma, id_prisma_virtual))
            id_instrumentacion = cursor.lastrowid

            # Confirmar la transacción
            conn.commit()

            # Obtener la fila recién agregada
            cursor.execute("""
                SELECT * FROM instrumentacion WHERE id_instrumentacion = ? AND tipo_equipo = 'PRISMAVIRTUAL';
            """, (id_instrumentacion,))
            nueva_fila = cursor.fetchall()

            return nueva_fila

        except Exception as e:
            # Si hay un error, hacer rollback
            conn.rollback()
            print(f"Error al registrar prisma virtual: {e}")
            return None

        finally:
            # Cerrar la conexión
            if conn:
                conn.close()

