import requests
from services.security.encriptacion import Encriptacion

class ConnectionAPI:

    def verify_fingerprint(encrypted_code):
        current_fingerprint = Encriptacion.generate_fingerprint()
        return current_fingerprint == encrypted_code

    def comprobarLicenciaOnline(serial, fingerprint):
        url = "https://e-verifylicense.eigha.pe/validarlicense.php"
        auth_token = "697d0ecdb22ac211176e3aa370f7773aa3e5941a4ace25bce4d8bf8f6a684b77"
        headers = {
            "Authorization": auth_token,
            "Content-Type": "application/json"
        }
        param = {
            "action": "validar_licencia",
            "serial": serial,
            "placa": fingerprint
        }
        timeout = 5
        try:
            response = requests.post(url, json=param, headers=headers, timeout=timeout)
            data = response.json()
            if response.status_code == 200:
                return True, data
            else:
                return False, {"error": "Licencia no válida."}
        except requests.exceptions.Timeout:
            return False, {"error": "Tiempo de espera agotado. Verifique su conexión a internet."}
        except requests.exceptions.ConnectionError:
            return False, {"error": "No se pudo conectar al servidor. Verifique su conexión a internet."}
        except requests.exceptions.RequestException:
            return False, {"error": "Error en la solicitud: No se pudo verificar la licencia."}
    
    def registrarLicenseOnline(idventa, fingerprint):
        url = "https://e-verifylicense.eigha.pe/validarlicense.php"
        auth_token = "697d0ecdb22ac211176e3aa370f7773aa3e5941a4ace25bce4d8bf8f6a684b77"
        headers = {
            "Authorization": auth_token,
            "Content-Type": "application/json"
        }
        param = {
            "action": "registrar_licencia",
            "codigo": idventa,
            "placa": fingerprint
        }
        timeout = 5
        try:
            response = requests.post(url, json=param, headers=headers, timeout=timeout)
            data = response.json()
            if response.status_code == 200:
                return True, data
            else:
                return False, {"error": "Licencia no válida."}
        except requests.exceptions.Timeout:
            return False, {"error": "Tiempo de espera agotado. Verifique su conexión a internet."}
        except requests.exceptions.ConnectionError:
            return False, {"error": "No se pudo conectar al servidor. Verifique su conexión a internet."}
        except requests.exceptions.RequestException:
            return False, {"error": "Error en la solicitud: No se pudo verificar la licencia."}
    