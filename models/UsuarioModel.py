import requests
from services.security.apis.conexiones.conexion import Connection

class UsuarioModel:
    
    @staticmethod
    def mdlObtenerCodigoEmpresa():
        conn = Connection.connectionDB()
        # SQL Server: TOP 1 en lugar de LIMIT 1
        sql = """SELECT TOP 1 codigo_empresa, codigo_venta FROM licencias;"""
        try:
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Exception as e:
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
    def mdlEliminarUsuario(idusuario):
        sql = """UPDATE usuarios SET estado_usuario = 0 WHERE id_usuario = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idusuario,))
            conn.commit()
            return True
        except Exception as e:
            print("Error al eliminar usuario: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
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