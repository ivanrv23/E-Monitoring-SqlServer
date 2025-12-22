from services.security.apis.conexiones.conexion import Connection
from sqlite3 import Error

class EmpresaModel:
       
    def mdlRegistrarActualizarInformacionEmpresa(datos):
        try:
            conexion = Connection.connectionDB()
            cursor = conexion.cursor()

            # Verificar si la empresa ya existe
            cursor.execute("SELECT id_empresa FROM empresa LIMIT 1")
            empresa_existente = cursor.fetchone()

            campos = ["nombre_empresa = ?", "ruc_empresa = ?", "telefono_empresa = ?", "correo_empresa = ?"]
            valores = [datos['nombre_empresa'], datos['codigo_ruc'], datos['numero_contacto'], datos['correo_electronico']]

            if 'logo' in datos and datos['logo'] is not None:
                campos.append("logo_empresa = ?")
                valores.append(datos['logo'])

            if empresa_existente:
                # Actualizar la información de la empresa
                sql = f"UPDATE empresa SET {', '.join(campos)} WHERE id_empresa = ?"
                valores.append(empresa_existente[0])
            else:
                # Insertar una nueva empresa
                sql = f"INSERT INTO empresa (nombre_empresa, ruc_empresa, telefono_empresa, correo_empresa, logo_empresa) VALUES (?, ?, ?, ?, ?)"
                if 'logo' not in datos or datos['logo'] is None:
                    valores.append(None)  # Asegurarse de que el logo sea None si no se proporciona

            cursor.execute(sql, valores)
            conexion.commit()
            return True
        except Exception as e:
            print(f"Error al actualizar/insertar información de empresa: {e}")
            return False
        finally:
            if conexion:
                conexion.close()

    def mdlRegistrarResponsableEmpresa(datos, proyectoid):
        try:
            conexion = Connection.connectionDB()
            cursor = conexion.cursor()

            # Construir la consulta SQL dinámicamente
            campos = ["responsable = ?", "cargo = ?", "dni = ?", "cip = ?"]
            valores = [datos['nombre_responsable'], datos['cargo'], datos['dni'], datos['cip']]

            if 'firma' in datos and datos['firma'] is not None:
                campos.append("firma = ?")
                valores.append(datos['firma'])

            # Verificar si ya existe un registro
            cursor.execute("SELECT COUNT(*) FROM personal_empresa WHERE id_proyecto = ?", (proyectoid,))
            resultado = cursor.fetchone()

            if resultado[0] > 0:
                # Si existe, hacer un UPDATE dinámico
                sql = f"UPDATE personal_empresa SET {', '.join(campos)} WHERE id_proyecto = ?"
                valores.append(proyectoid)
            else:
                # Si no existe, hacer un INSERT
                columnas = [campo.split('=')[0] for campo in campos]
                columnas.append('id_proyecto')
                sql = f"INSERT INTO personal_empresa ({', '.join(columnas)}) VALUES ({', '.join(['?' for _ in range(len(valores) + 1)])})"
                valores.append(proyectoid)

            cursor.execute(sql, valores)
            conexion.commit()
            return True
        except Exception as e:
            print(f"Error al insertar/actualizar en la base de datos: {e}")
            return False
        finally:
            if conexion:
                conexion.close()
    
    def mdlObtenerDatosEmpresa():
        conn = Connection.connectionDB()
        sql = """SELECT * FROM empresa"""
        try:
            cur = conn.cursor()
            cur.execute(sql,)
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al obtener información de empresa: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlObtenerDatosLicencia():
        try:
            conn = Connection.connectionDB()
            sql = """SELECT * FROM licencias;"""
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al obtener info licencia:", e)
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlObtenerDatosConfiguracionSoftware():
        conn = Connection.connectionDB()
        sql = """SELECT * FROM configuraciongrafica"""
        try:
            cur = conn.cursor()
            cur.execute(sql,)
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al obtener configuracion soft: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlObtenerDatosConfiguracionEmpresa():
        conn = Connection.connectionDB()
        sql = """SELECT * FROM empresa;"""
        try:
            cur = conn.cursor()
            cur.execute(sql,)
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al obtener empresa: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
                
    def mdlObtenerDatosConfiguracionResponsable(proyectoid):
        try:
            # Establecer la conexión con la base de datos
            conn = Connection.connectionDB()
            sql = """SELECT * FROM firmas WHERE id_proyecto = ?;"""
            with conn:
                cur = conn.cursor()
                cur.execute(sql, (proyectoid,))
                row = cur.fetchone()
                # Retornar la fila si existe, de lo contrario retornar None
                return row if row else None
        except Error as e:
            print(f"Error al obtener configuración del responsable: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlListarResponsablesFirma():
        conn = Connection.connectionDB()
        sql = """SELECT * FROM personal_empresa WHERE tipo = 0;"""
        try:
            cur = conn.cursor()
            cur.execute(sql,)
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al obtener firmas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlGuardarNuevoResponsable(responsable, supervision, comentario, firma):
        try:
            conn = Connection.connectionDB()
            sql = "INSERT INTO personal_empresa (supervision, responsable, comentario, firma) VALUES (?, ?, ?, ?);"
            
            cur = conn.cursor()
            cur.execute(sql, (supervision, responsable, comentario, firma))
            conn.commit()
            return True
        except Error as e:
            print(f"Error al insertar firma: {e}")
            return False
        finally:
            if conn:
                conn.close()
           
    def mdlEliminarFirmaResponsable(id):
        conn = Connection.connectionDB()
        sql = """DELETE FROM personal_empresa WHERE id = ?;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (id,))
            conn.commit()
            if cur.rowcount > 0:
                return True
            else:
                return False
        except Error as e:
            print("Error al eliminar firma: " + str(e))
            return False
        finally:
            if conn:
                conn.close() 
                
    def mdlObtenerResponsables():
        try:
            # Establecer la conexión con la base de datos
            conn = Connection.connectionDB()
            sql = """SELECT * FROM personal_empresa WHERE tipo = ?"""

            # Usar el manejo de contexto para asegurar que el cursor se cierre correctamente
            with conn:
                cur = conn.cursor()
                cur.execute(sql, (0,))
                row = cur.fetchall()

                # Retornar la fila si existe, de lo contrario retornar None
                return row if row else None

        except Error as e:
            print(f"Error al obtener configuración del responsable: {e}")
            return None
        finally:
            # Asegurarse de cerrar la conexión si fue creada
            if conn:
                conn.close()
    
    def mdlRegistrarActualizarAjustesSoftware(datos):
        try:
            conexion = Connection.connectionDB()
            cursor = conexion.cursor()
            # Verificar si existe algún registro
            cursor.execute("SELECT COUNT(*) FROM configuraciongrafica")
            resultado = cursor.fetchone()
            campos = [
                "titulo_grafica", "ejes_grafica", "etiquetas_grafica", "leyenda_grafica",
                "cota_grafica", "mostrarcota_grafica", "mostrar_vertices", "tipo_tendencia",
                "grosor_tendencia", "color_tendencia", "fuente_grafica", "transparencia_grafica", "grosor_lineas", "grosor_vertices",
                "cantidad_decimal", "velocidad_grafica", "filtrado_grafica", "lluvia_grafica", "mostrar_lluvia", "celda_grafica"
            ]
            valores = [
                datos['titulo'], datos['ejes'], datos['etiquetas'], datos['leyenda'], datos['cotas'],
                datos['mostrarcota'], datos['mostrarvertice'], datos['tipotendencia'], datos['grosortendencia'],
                datos['colortendencia'], datos['tipoletra'], datos['transparente'], datos['lineagrosor'], datos['verticegrosor'],
                datos['cantidecimales'], datos['velocidad_prisma'], datos['filtrofecha'], datos['precipitacion'],
                datos['mostrarlluvia'], datos['velocidad_celda']
            ]
            if resultado[0] > 0:
                set_clause = ', '.join([f"{campo} = ?" for campo in campos])
                sql = f"UPDATE configuraciongrafica SET {set_clause} WHERE id_configuracion = (SELECT id_configuracion FROM configuraciongrafica LIMIT 1)"
            else:
                # Si no existe, inserta un nuevo registro
                placeholders = ', '.join(['?' for _ in campos])
                sql = f"INSERT INTO configuraciongrafica ({', '.join(campos)}) VALUES ({placeholders})"
            cursor.execute(sql, valores)
            conexion.commit()
            return True
        except Error as e:
            print(f"Error al actualizar ajustes software: {e}")
            return False
        finally:
            if conexion:
                conexion.close()
    