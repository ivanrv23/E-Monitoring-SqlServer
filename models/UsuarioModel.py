import requests
from sqlite3 import Error
import pyodbc
from services.security.apis.conexiones.conexion import Conexion
from services.security.apis.conexiones.connection import Connection

class UsuarioModel:
    
    @staticmethod
    def mdlObtenerCodigoEmpresa():
        sql = """SELECT codigo_empresa, codigo_venta FROM licencias;"""
        try:
            conn = Conexion.conexionDB()
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al obtener idempresa: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
     
    # LISTAR USUARIOS POR EMPRESA
    @staticmethod
    def mdlObtenerListaUsuarios(idventa):
        url = "https://e-verifylicense.eigha.pe/validarlicense.php"
        auth_token = "697d0ecdb22ac211176e3aa370f7773aa3e5941a4ace25bce4d8bf8f6a684b77"
        headers = {
            "Authorization": auth_token,
            "Content-Type": "application/json"
        }
        param = {
            "action": "listar_usuarios",
            "idventa": idventa
        }
        timeout = 5
        try:
            response = requests.post(url, json=param, headers=headers, timeout=timeout)
            data = response.json()
            if response.status_code == 200:
                return True, data
            else:
                return False, {"error": "Error de conexión."}
        except requests.exceptions.Timeout:
            return False, {"error": "Tiempo de espera agotado. Verifique su conexión a internet."}
        except requests.exceptions.ConnectionError:
            return False, {"error": "No se pudo conectar al servidor. Verifique su conexión a internet."}
        except requests.exceptions.RequestException:
            return False, {"error": "Error en la solicitud: No se pudo obtener usuarios."}
    
    @staticmethod
    def mdlGuardarUsuario(documento, nombres, apellidos, username, contraseña, rol, idventa):
        url = "https://e-verifylicense.eigha.pe/validarlicense.php"
        auth_token = "697d0ecdb22ac211176e3aa370f7773aa3e5941a4ace25bce4d8bf8f6a684b77"
        headers = {
            "Authorization": auth_token,
            "Content-Type": "application/json"
        }
        param = {
            "action": "crear_usuario",
            "dni": documento,
            "nombre": nombres,
            "apellido": apellidos,
            "usuario": username,
            "contraseña": contraseña,
            "rol": rol,
            "venta": idventa
        }
        timeout = 5
        try:
            response = requests.post(url, json=param, headers=headers, timeout=timeout)
            data = response.json()
            if response.status_code == 200:
                return True, data
            else:
                return False, {"error": data["error"]}
        except requests.exceptions.Timeout:
            return False, {"error": "Tiempo de espera agotado. Verifique su conexión a internet."}
        except requests.exceptions.ConnectionError:
            return False, {"error": "No se pudo conectar al servidor. Verifique su conexión a internet."}
        except requests.exceptions.RequestException:
            return False, {"error": "Error en la solicitud: No se pudo guardar el usuario."}
    
    @staticmethod
    def mdlActualizarUsuario(documento, nombres, apellidos, username, rol, estado, idusuario):
        url = "https://e-verifylicense.eigha.pe/validarlicense.php"
        auth_token = "697d0ecdb22ac211176e3aa370f7773aa3e5941a4ace25bce4d8bf8f6a684b77"
        headers = {
            "Authorization": auth_token,
            "Content-Type": "application/json"
        }
        param = {
            "action": "actualizar_usuario",
            "dni": documento,
            "nombre": nombres,
            "apellido": apellidos,
            "usuario": username,
            "rol": rol,
            "estado": estado,
            "idusuario": idusuario
        }
        timeout = 5
        try:
            response = requests.post(url, json=param, headers=headers, timeout=timeout)
            data = response.json()
            if response.status_code == 200:
                return True, data
            else:
                return False, {"error": data["error"]}
        except requests.exceptions.Timeout:
            return False, {"error": "Tiempo de espera agotado. Verifique su conexión a internet."}
        except requests.exceptions.ConnectionError:
            return False, {"error": "No se pudo conectar al servidor. Verifique su conexión a internet."}
        except requests.exceptions.RequestException:
            return False, {"error": "Error en la solicitud: No se pudo actualizar el usuario."}
    
    @staticmethod
    def mdlCambiarContraseñaUsuario(contraseña, idusuario):
        url = "https://e-verifylicense.eigha.pe/validarlicense.php"
        auth_token = "697d0ecdb22ac211176e3aa370f7773aa3e5941a4ace25bce4d8bf8f6a684b77"
        headers = {
            "Authorization": auth_token,
            "Content-Type": "application/json"
        }
        param = {
            "action": "cambiar_password",
            "contraseña": contraseña,
            "idusuario": idusuario
        }
        timeout = 5
        try:
            response = requests.post(url, json=param, headers=headers, timeout=timeout)
            data = response.json()
            if response.status_code == 200:
                return True, data
            else:
                return False, {"error": data["error"]}
        except requests.exceptions.Timeout:
            return False, {"error": "Tiempo de espera agotado. Verifique su conexión a internet."}
        except requests.exceptions.ConnectionError:
            return False, {"error": "No se pudo conectar al servidor. Verifique su conexión a internet."}
        except requests.exceptions.RequestException:
            return False, {"error": "Error en la solicitud."}
    
    @staticmethod
    def mdlCambiarEstadoUsuario(estado, idusuario):
        url = "https://e-verifylicense.eigha.pe/validarlicense.php"
        auth_token = "697d0ecdb22ac211176e3aa370f7773aa3e5941a4ace25bce4d8bf8f6a684b77"
        headers = {
            "Authorization": auth_token,
            "Content-Type": "application/json"
        }
        param = {
            "action": "cambiar_estado",
            "estado": estado,
            "idusuario": idusuario
        }
        timeout = 5
        try:
            response = requests.post(url, json=param, headers=headers, timeout=timeout)
            data = response.json()
            if response.status_code == 200:
                return True, data
            else:
                return False, {"error": data["error"]}
        except requests.exceptions.Timeout:
            return False, {"error": "Tiempo de espera agotado. Verifique su conexión a internet."}
        except requests.exceptions.ConnectionError:
            return False, {"error": "No se pudo conectar al servidor. Verifique su conexión a internet."}
        except requests.exceptions.RequestException:
            return False, {"error": "Error en la solicitud."}
    
    @staticmethod
    def mdlComprobarUsuarioContraseña(usuario, contraseña, idventa):
        url = "https://e-verifylicense.eigha.pe/validarlicense.php"
        auth_token = "697d0ecdb22ac211176e3aa370f7773aa3e5941a4ace25bce4d8bf8f6a684b77"
        headers = {
            "Authorization": auth_token,
            "Content-Type": "application/json"
        }
        param = {
            "action": "iniciar_sesion",
            "usuario": usuario,
            "contrasenia": contraseña,
            "venta": idventa
        }
        timeout = 5
        try:
            response = requests.post(url, json=param, headers=headers, timeout=timeout)
            data = response.json()
            if response.status_code == 200:
                return True, data
            else:
                return False, {"error": data["error"]}
        except requests.exceptions.Timeout:
            return False, {"error": "Tiempo de espera agotado. Verifique sus permisos."}
        except requests.exceptions.ConnectionError:
            return False, {"error": "No se pudo conectar al servidor. Verifique su conexión a internet."}
        except requests.exceptions.RequestException:
            return False, {"error": "Error al validar usuario y contraseña."}
    
    @staticmethod
    def mdlObtenerConexiones():
        conn = None
        sql = """SELECT p.nombre_proyecto, c.instrumento_conexion, c.servidor_conexion, c.puerto_conexion, c.database_conexion, c.usuario_conexion,
        c.grupos_conexion, c.lecturas_conexion, c.dato_conexion, c.frecuencia_conexion, c.estado_conexion, c.id_conexion, c.id_proyecto
        FROM conexiones c INNER JOIN proyectos p ON c.id_proyecto = p.id_proyecto;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql)
            rows = cur.fetchall()
            results = [tuple(row) for row in rows]
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al consultar conexiones: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlGuardarNuevaConexion(datos):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = """INSERT INTO conexiones (id_proyecto, instrumento_conexion, servidor_conexion, puerto_conexion, database_conexion, usuario_conexion,
            password_conexion, grupos_conexion, lecturas_conexion, dato_conexion, frecuencia_conexion, estado_conexion) OUTPUT INSERTED.id_conexion
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""
            cur = conn.cursor()
            cur.execute(sql, datos)
            # Obtener el id recién insertado
            row = cur.fetchone()
            if not row:
                raise Exception("No se obtuvo el ID de la conexión insertada.")
            nuevo_id = int(row[0])
            # Registrar en sync_control para que arranque de inmediato
            cur.execute("""INSERT INTO sync_control
                (id_conexion, ultimo_sync, proximo_sync, ejecutando, hostname, frecuencia_min)
                VALUES (?, NULL, GETDATE(), 0, NULL, ?);""", nuevo_id, datos[10])   # datos[10] = frecuencia_conexion
            conn.commit()
            return True
        except Exception as e:
            print("Error al registrar conexión:", e)
            if conn:
                conn.rollback()
            return False  
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def mdlActualizarConexion(datos):
        conn = None
        try:
            conn = Connection.connectionDB()
            idproyecto, instrumento, servidor, puerto, database, usuario, password, consultagrupos, consultalecturas, ultimoid, frecuencia, estado, idconexion = datos
            if password:  # ← Con contraseña: actualiza todo
                sql = """UPDATE conexiones SET
                    id_proyecto          = ?,
                    instrumento_conexion = ?,
                    servidor_conexion    = ?,
                    puerto_conexion      = ?,
                    database_conexion    = ?,
                    usuario_conexion     = ?,
                    password_conexion    = ?,
                    grupos_conexion      = ?,
                    lecturas_conexion    = ?,
                    dato_conexion        = ?,
                    frecuencia_conexion  = ?,
                    estado_conexion      = ?
                WHERE id_conexion = ?;"""
                params = (idproyecto, instrumento, servidor, puerto, database, usuario, password,
                          consultagrupos, consultalecturas, ultimoid, frecuencia, estado, idconexion)
            else:  # ← Sin contraseña: omite password_conexion
                sql = """UPDATE conexiones SET
                    id_proyecto          = ?,
                    instrumento_conexion = ?,
                    servidor_conexion    = ?,
                    puerto_conexion      = ?,
                    database_conexion    = ?,
                    usuario_conexion     = ?,
                    grupos_conexion      = ?,
                    lecturas_conexion    = ?,
                    dato_conexion        = ?,
                    frecuencia_conexion  = ?,
                    estado_conexion      = ?
                WHERE id_conexion = ?;"""
                params = (idproyecto, instrumento, servidor, puerto, database, usuario,
                          consultagrupos, consultalecturas, ultimoid, frecuencia, estado, idconexion)
            cur = conn.cursor()
            cur.execute(sql, params)
            # Sincronizar sync_control con la nueva frecuencia
            cur.execute("""UPDATE sync_control
                SET frecuencia_min = ?, ejecutando = 0
                WHERE id_conexion = ?;""", frecuencia, idconexion)
            conn.commit()
            return True
        except Exception as e:
            print("Error al actualizar conexión:", e)
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mdlEliminarConexion(idconexion):
        conn = None
        try:
            conn = Connection.connectionDB()
            sql = """DELETE FROM conexiones WHERE id_conexion = ?;"""
            cur = conn.cursor()
            cur.execute("DELETE FROM sync_control WHERE id_conexion = ?", idconexion)
            cur.execute(sql, (idconexion,))
            conn.commit()
            return True
        except Exception as e:
            print("Error al eliminar conexión:", e)
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    