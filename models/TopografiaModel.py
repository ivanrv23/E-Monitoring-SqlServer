from services.security.apis.conexiones.connection import Connection

class TopografiaModel:
        
    @staticmethod
    def mdlObtenerTipoTopografia(proyectoid, idcomponente, idtopo):
        conn = None
        tipo = "TOPOGRAFIA"
        sql = """SELECT t.tipo_topografia, t.archivo_topografia FROM instrumentacion i INNER JOIN topografias t ON i.id_equipo = t.id_topografia
        INNER JOIN componentes c ON i.id_componente = c.id_componente WHERE c.id_proyecto = ? AND c.id_componente = ?
        AND i.tipo_equipo = ? AND i.id_equipo = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyectoid, idcomponente, tipo, idtopo))
            row = cur.fetchone()
            if row:
                return tuple(row)
            else:
                return None
        except Exception as e:
            print("Error al obtener tipo topo: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    # LISTAR DATA COTAS TERRENO DETALLE POR ID    
    @staticmethod
    def mdlObtenerDataCotasTerrenoDetalle(idsuelo):
        conn = None
        sql = """SELECT s.nombre_terreno, d.fecha_detalle, d.nivel_detalle, d.id_detalle FROM cotaterreno_detalle d INNER JOIN cotasterreno s
        ON d.id_terreno = s.id_terreno WHERE d.id_terreno = ? ORDER BY d.fecha_detalle;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idsuelo,))
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al consultar terreno detalle: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlRegistrarNuevaTopografia(proyectoid, idcomponente, nombrenuevo, tipo, ubicacion, comentario, fecha_formateada):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            
            # Verificar si el equipo ya existe en la tabla instrumentacion
            sql_check = """SELECT 1 FROM instrumentacion WHERE id_componente = ? AND nombre_equipo = ? AND tipo_equipo = 'TOPOGRAFIA';"""
            cur.execute(sql_check, (idcomponente, nombrenuevo))
            if cur.fetchone():
                return False, None
            
            # Insertar el equipo en la tabla equipos con OUTPUT para obtener ID
            sql_insert = """INSERT INTO topografias (id_proyecto, nombre_topografia, tipo_topografia, archivo_topografia,
            comentario_topografia, fecha_topografia) 
            OUTPUT INSERTED.id_topografia
            VALUES (?, ?, ?, ?, ?, ?);"""
            cur.execute(sql_insert, (proyectoid, nombrenuevo, tipo, ubicacion, comentario, fecha_formateada))
            
            # Obtener el ID del equipo recién insertado
            equipo_id = cur.fetchone()[0]
            
            # Insertar el equipo en la tabla instrumentacion con OUTPUT
            sql_insert_instrumentacion = """INSERT INTO instrumentacion (id_componente, tipo_equipo, nombre_equipo, id_equipo, tabla_equipo)
                                            OUTPUT INSERTED.id_instrumentacion
                                            VALUES (?, ?, ?, ?, ?);"""
            cur.execute(sql_insert_instrumentacion, (idcomponente, 'TOPOGRAFIA', nombrenuevo, equipo_id, 'topografias'))
            idinstrumento = cur.fetchone()[0]
            
            # Confirmar la transacción
            conn.commit()
            return True, idinstrumento
        except Exception as e:
            # Realizar rollback en caso de error
            if conn:
                conn.rollback()
            print("Error al guardar topografia: " + str(e))
            return False, None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlCambiarComponenteTopografias(idcomponente, nuevocomponente):
        conn = None
        sql = """UPDATE instrumentacion SET id_componente = ? WHERE id_componente = ? AND tipo_equipo = 'TOPOGRAFIA';"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # guardar info
            query_select = """SELECT DISTINCT * FROM instrumentacion i INNER JOIN topografias t ON i.id_equipo = t.id_topografia
            WHERE i.id_componente = ? AND i.tipo_equipo = 'TOPOGRAFIA';"""
            cur.execute(query_select, (idcomponente,))
            rows = cur.fetchall()
            datatopos = [tuple(row) for row in rows]
            
            if datatopos:
                cur.execute(sql, (nuevocomponente, idcomponente))
                conn.commit()
                return datatopos
            else:
                return None
        except Exception as e:
            print("Error al cambiar componente topografias: " + str(e))
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlEliminarTopografias(idcomponente):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # obtener info
            query_select = """SELECT * FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'TOPOGRAFIA';"""
            cursor.execute(query_select, (idcomponente,))
            rows = cursor.fetchall()
            datatopos = [tuple(row) for row in rows]
            
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
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlEliminarDataTopografias(topografias):
        conn = None
        # Generar placeholders dinámicos
        placeholders = ','.join(['?' for _ in topografias])
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # obtener data antes de borrar
            query_select = f"""SELECT * FROM topografias WHERE id_topografia IN ({placeholders});"""
            cursor.execute(query_select, topografias)
            rows = cursor.fetchall()
            datatopos = [tuple(row) for row in rows]
            
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
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlObtenerInfoTopografia(idinstrumento):
        conn = None
        sql = """SELECT t.* FROM topografias t INNER JOIN instrumentacion i ON t.id_topografia = i.id_equipo WHERE i.id_instrumentacion = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idinstrumento,))
            row = cur.fetchone()
            if row:
                return tuple(row)
            else:
                return None
        except Exception as e:
            print("Error al consultar info topografia: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlActualizarTopografia(componente, nombrenuevo, comentario, asignarfecha, idinstrumento, idtopografia):
        conn = None
        sql = """UPDATE topografias SET nombre_topografia = ?, comentario_topografia = ?, fecha_topografia = ?  WHERE id_topografia = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (nombrenuevo, comentario, asignarfecha, idtopografia))
            
            query_instrumentacion = """UPDATE instrumentacion SET id_componente = ?, nombre_equipo = ?
            WHERE id_instrumentacion = ? AND tipo_equipo = 'TOPOGRAFIA';"""
            
            cur.execute(query_instrumentacion, (componente, nombrenuevo, idinstrumento))
            conn.commit()
            return True
        except Exception as e:
            print("Error al editar topografia: " + str(e))
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlEliminarTopografia(idinstrumento):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # obtener info para eliminar data
            query_select = """SELECT i.*, t.archivo_topografia FROM instrumentacion i INNER JOIN topografias t
            ON i.id_equipo = t.id_topografia WHERE i.id_instrumentacion = ? AND i.tipo_equipo = 'TOPOGRAFIA';"""
            cursor.execute(query_select, (idinstrumento,))
            row = cursor.fetchone()
            
            if row:
                datatopo = tuple(row)
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
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlEliminarTopografiaData(idtopografia):
        conn = None
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
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
                
    @staticmethod
    def mdlObtenerFechaTopografia(idtopo):
        conn = None
        sql = """SELECT fecha_topografia FROM topografias WHERE id_topografia = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idtopo,))
            row = cur.fetchone()
            return row[0] if row else "Fecha no disponible"
        except Exception as e:
            print("Error al consultar info topografia: " + str(e))
            return "Error en la consulta"
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlRegistrarPrismaVirtual(id_componente, x, y, z, nombre_prisma, radio, color):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()

            # Verificar si ya existe un prisma con el mismo nombre
            cursor.execute("SELECT COUNT(*) FROM prismas_virtuales WHERE nombre_prisma_virtual = ?", (nombre_prisma,))
            count = cursor.fetchone()[0]

            # Si existe, modificar el nombre (Lógica Python + SQL)
            if count > 0:
                # Agregar un número al final del nombre
                cursor.execute("SELECT nombre_prisma_virtual FROM prismas_virtuales WHERE nombre_prisma_virtual LIKE ?", (nombre_prisma + "%",))
                # Extraer nombres a una lista de tuplas
                existing_rows = cursor.fetchall()
                existing_names = [tuple(row) for row in existing_rows]
                
                suffix = 1
                new_nombre_prisma = nombre_prisma
                # Comparación de tuplas
                while (new_nombre_prisma,) in existing_names:
                    suffix += 1
                    new_nombre_prisma = f"{nombre_prisma}_{suffix}"
                nombre_prisma = new_nombre_prisma

            # Insertar en la tabla prismas_virtuales con OUTPUT
            cursor.execute("""
                INSERT INTO prismas_virtuales (nombre_prisma_virtual, coordenada_x, coordenada_y, coordenada_z, radio_prisma_virtual, color_prisma)
                OUTPUT INSERTED.id_prisma_virtual
                VALUES (?, ?, ?, ?, ?, ?)
            """, (nombre_prisma, x, y, z, radio, color))

            # Obtener el último ID insertado
            id_prisma_virtual = cursor.fetchone()[0]

            # Insertar en la tabla instrumentacion con OUTPUT
            cursor.execute("""
                INSERT INTO instrumentacion (id_componente, tipo_equipo, nombre_equipo, id_equipo, tabla_equipo)
                OUTPUT INSERTED.id_instrumentacion
                VALUES (?, 'PRISMAVIRTUAL', ?, ?, 'prismas_virtuales')
            """, (id_componente, nombre_prisma, id_prisma_virtual))
            
            id_instrumentacion = cursor.fetchone()[0]

            # Confirmar la transacción
            conn.commit()

            # Obtener la fila recién agregada
            cursor.execute("""
                SELECT * FROM instrumentacion WHERE id_instrumentacion = ? AND tipo_equipo = 'PRISMAVIRTUAL';
            """, (id_instrumentacion,))
            rows = cursor.fetchall()
            nueva_fila = [tuple(row) for row in rows]

            return nueva_fila

        except Exception as e:
            # Si hay un error, hacer rollback
            if conn:
                conn.rollback()
            print(f"Error al registrar prisma virtual: {e}")
            return None

        finally:
            # Cerrar la conexión
            if conn:
                conn.close()