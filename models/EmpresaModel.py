from services.security.apis.conexiones.connection import Connection
from services.security.apis.conexiones.conexion import Conexion

class EmpresaModel:

    @staticmethod
    def mdlRegistrarActualizarInformacionEmpresa(datos):
        conexion = None
        try:
            conexion = Connection.connectionDB()
            cursor = conexion.cursor()

            # SQL Server: Usa TOP 1 en lugar de LIMIT 1
            cursor.execute("SELECT TOP 1 id_empresa FROM empresa")
            empresa_existente = cursor.fetchone()

            campos = ["nombre_empresa = ?", "ruc_empresa = ?", "telefono_empresa = ?", "correo_empresa = ?"]
            valores = [datos['nombre_empresa'], datos['codigo_ruc'], datos['numero_contacto'], datos['correo_electronico']]

            if 'logo' in datos and datos['logo'] is not None:
                campos.append("logo_empresa = ?")
                valores.append(datos['logo'])

            if empresa_existente:
                # Actualizar la información de la empresa
                # empresa_existente es un objeto Row, accedemos por índice [0]
                sql = f"UPDATE empresa SET {', '.join(campos)} WHERE id_empresa = ?"
                valores.append(empresa_existente[0])
            else:
                # Insertar una nueva empresa
                sql = f"INSERT INTO empresa (nombre_empresa, ruc_empresa, telefono_empresa, correo_empresa, logo_empresa) VALUES (?, ?, ?, ?, ?)"
                if 'logo' not in datos or datos['logo'] is None:
                    valores.append(None)

            cursor.execute(sql, valores)
            conexion.commit()
            return True
        except Exception as e:
            print(f"Error al actualizar/insertar información de empresa: {e}")
            return False
        finally:
            if conexion:
                conexion.close()

    @staticmethod
    def mdlRegistrarResponsableEmpresa(datos, proyectoid):
        conexion = None
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
                # UPDATE
                sql = f"UPDATE personal_empresa SET {', '.join(campos)} WHERE id_proyecto = ?"
                valores.append(proyectoid)
            else:
                # INSERT
                columnas = [campo.split('=')[0].strip() for campo in campos]
                columnas.append('id_proyecto')
                
                # Generar placeholders ? dinámicos para pyodbc
                placeholders = ', '.join(['?' for _ in range(len(valores) + 1)])
                
                sql = f"INSERT INTO personal_empresa ({', '.join(columnas)}) VALUES ({placeholders})"
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

    @staticmethod
    def mdlObtenerDatosEmpresa():
        conn = None
        sql = """SELECT * FROM empresa"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchone()
            # Conversión explícita a tupla para compatibilidad con Frontend
            if row:
                return tuple(row)
            else:
                return None
        except Exception as e:
            print("Error al obtener información de empresa: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlObtenerDatosLicencia():
        conn = None
        try:
            conn = Conexion.conexionDB()
            sql = """SELECT * FROM licencias;"""
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al obtener info licencia:", e)
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlObtenerDatosConfiguracionSoftware():
        conn = None
        sql = """SELECT * FROM configuraciongrafica"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchone()
            # Conversión explícita a tupla
            if row:
                return tuple(row)
            else:
                return None
        except Exception as e:
            print("Error al obtener configuracion soft: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlObtenerDatosConfiguracionEmpresa():
        conn = None
        sql = """SELECT * FROM empresa;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchone()
            # Conversión explícita a tupla
            if row:
                return tuple(row)
            else:
                return None
        except Exception as e:
            print("Error al obtener empresa: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlObtenerDatosConfiguracionResponsable(proyectoid):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = """SELECT * FROM firmas WHERE id_proyecto = ?;"""
            cur = conn.cursor()
            cur.execute(sql, (proyectoid,))
            row = cur.fetchone()
            # Conversión explícita a tupla
            return tuple(row) if row else None
        except Exception as e:
            print(f"Error al obtener configuración del responsable: {e}")
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlListarResponsablesFirma():
        conn = None
        sql = """SELECT * FROM personal_empresa WHERE tipo = 0;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql)
            rows = cur.fetchall()
            # Conversión explícita a lista de tuplas
            if rows:
                return [tuple(row) for row in rows]
            else:
                return None
        except Exception as e:
            print("Error al obtener firmas: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlGuardarNuevoResponsable(responsable, supervision, comentario, firma):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = "INSERT INTO personal_empresa (supervision, responsable, comentario, firma) VALUES (?, ?, ?, ?);"
            
            cur = conn.cursor()
            cur.execute(sql, (supervision, responsable, comentario, firma))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al insertar firma: {e}")
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlEliminarFirmaResponsable(id):
        conn = None
        sql = """DELETE FROM personal_empresa WHERE id = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (id,))
            conn.commit()
            if cur.rowcount > 0:
                return True
            else:
                return False
        except Exception as e:
            print("Error al eliminar firma: " + str(e))
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlObtenerResponsables():
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = """SELECT * FROM personal_empresa WHERE tipo = ?"""

            cur = conn.cursor()
            cur.execute(sql, (0,))
            rows = cur.fetchall()

            # Conversión explícita a lista de tuplas para evitar pyodbc.Row en frontend
            return [tuple(row) for row in rows] if rows else None

        except Exception as e:
            print(f"Error al obtener configuración del responsable: {e}")
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlRegistrarActualizarAjustesSoftware(datos):
        conexion = None
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
                "cantidad_decimal", "velocidad_grafica", "filtrado_grafica", "lluvia_grafica", "mostrar_lluvia", "celda_grafica", "suavizado_grafica", "fechahora_grafica", "mesletras_grafica"
            ]
            valores = [
                datos['titulo'], datos['ejes'], datos['etiquetas'], datos['leyenda'], datos['cotas'],
                datos['mostrarcota'], datos['mostrarvertice'], datos['tipotendencia'], datos['grosortendencia'],
                datos['colortendencia'], datos['tipoletra'], datos['transparente'], datos['lineagrosor'], datos['verticegrosor'],
                datos['cantidecimales'], datos['velocidad_prisma'], datos['filtrofecha'], datos['precipitacion'],
                datos['mostrarlluvia'], datos['velocidad_celda'], datos['suavizado'], datos['fechahora'], datos['mesletras']
            ]

            if resultado[0] > 0:
                set_clause = ', '.join([f"{campo} = ?" for campo in campos])
                # SQL Server: Subconsulta con TOP 1 para el UPDATE
                sql = f"UPDATE configuraciongrafica SET {set_clause} WHERE id_configuracion = (SELECT TOP 1 id_configuracion FROM configuraciongrafica)"
            else:
                # Insertar un nuevo registro
                placeholders = ', '.join(['?' for _ in campos])
                sql = f"INSERT INTO configuraciongrafica ({', '.join(campos)}) VALUES ({placeholders})"
            
            cursor.execute(sql, valores)
            conexion.commit()
            return True
        except Exception as e:
            print(f"Error al actualizar ajustes software: {e}")
            return False
        finally:
            if conexion:
                conexion.close()