import wmi
import os
from cryptography.fernet import Fernet
import hashlib
import subprocess
from utils.common.rutasarchivos import resource_path

class Encriptacion:
    
    @staticmethod
    def generate_fingerprint():
        system_uuid = Encriptacion.get_system_uuid()
        baseboard_product = Encriptacion.get_baseboard_product()
        disk_serial = Encriptacion.get_disk_serial()
        # Combinar y hashear
        combined_data = f"{system_uuid}{baseboard_product}{disk_serial}"
        return hashlib.sha256(combined_data.encode()).hexdigest()
    
    @staticmethod
    def run_command(command, use_powershell=False):
        try:
            if use_powershell:
                result = subprocess.check_output(
                    ["powershell", "-Command", command],
                    shell=True,
                    stderr=subprocess.STDOUT
                ).decode().strip()
            else:
                result = subprocess.check_output(
                    command, shell=True, stderr=subprocess.STDOUT
                ).decode().strip()
            return result if result else "Unknown"
        except Exception:
            return "Unknown"

    @staticmethod
    def get_system_uuid():
        """Obtiene el UUID del sistema."""
        uuid = Encriptacion.run_command("wmic csproduct get uuid")
        if uuid == "Unknown":
            uuid = Encriptacion.run_command('(Get-WmiObject Win32_ComputerSystemProduct).UUID', use_powershell=True)
        return uuid.split("\n")[-1].strip() if uuid != "Unknown" else "Unknown"

    @staticmethod
    def get_baseboard_product():
        """Obtiene el producto de la placa base."""
        product = Encriptacion.run_command("wmic baseboard get product")
        if product == "Unknown":
            product = Encriptacion.run_command('(Get-WmiObject Win32_BaseBoard).Product', use_powershell=True)
        return product.split("\n")[-1].strip() if product != "Unknown" else "Unknown"

    @staticmethod
    def get_disk_serial():
        """Obtiene el serial del disco principal."""
        serial = Encriptacion.run_command("wmic diskdrive get serialnumber")
        if serial == "Unknown":
            serial = Encriptacion.run_command('(Get-WmiObject Win32_DiskDrive | Where-Object { $_.DeviceID -eq "\\\\.\\PHYSICALDRIVE0" }).SerialNumber', use_powershell=True)
        return serial.split("\n")[-1].strip() if serial != "Unknown" else "Unknown"
    
    #################################################################################
    
    @staticmethod
    def obtener_dispositivo_serie_placa_base():
        try:
            c = wmi.WMI()
            for board in c.Win32_BaseBoard():
                return board.SerialNumber
        except Exception:
            return "Unknown"
    
    @staticmethod
    def load_key():
        try:
            credenciales_path = resource_path('services/security/clave.key')
            with open(credenciales_path, "rb") as key_file:
                key = key_file.read()
            return key
        except FileNotFoundError:
            print("Error: No se encontró el archivo clave.key")
            return None

    @staticmethod
    def encrypt_data(data_bytes, key):
        """Método interno que recibe bytes y devuelve bytes"""
        cipher_suite = Fernet(key)
        encrypted_data = cipher_suite.encrypt(data_bytes)
        return encrypted_data

    @staticmethod
    def decrypt_data(encrypted_bytes, key):
        """Método interno que recibe bytes y devuelve bytes"""
        cipher_suite = Fernet(key)
        decrypted_data = cipher_suite.decrypt(encrypted_bytes)
        return decrypted_data
    
    # =========================================================
    # ESTOS SON LOS METODOS QUE CORRIGEN EL PROBLEMA DE SQL
    # =========================================================

    @staticmethod
    def encrypt(text):
        """
        Recibe texto normal.
        Devuelve STRING (utf-8) listo para SQL Server.
        """
        if text is None: return ""
        
        # 1. Asegurar que 'text' es string antes de codificar a bytes
        if not isinstance(text, str):
            text = str(text)

        key = Encriptacion.load_key()
        if not key: return text # Si no hay key, devolver texto plano (fallback)

        # 2. Encriptar (Fernet devuelve bytes)
        encrypted_bytes = Encriptacion.encrypt_data(text.encode('utf-8'), key)
        
        # 3. CRÍTICO: Decodificar los bytes a String para que SQL Server no guarde símbolos raros
        return encrypted_bytes.decode('utf-8')

    @staticmethod
    def decrypt(encrypted_string):
        """
        Recibe string encriptado desde SQL Server.
        Devuelve texto normal desencriptado.
        """
        if not encrypted_string: return ""

        key = Encriptacion.load_key()
        if not key: return ""

        # 1. CRÍTICO: Convertir el String de la DB de vuelta a Bytes para Fernet
        if isinstance(encrypted_string, str):
            encrypted_bytes = encrypted_string.encode('utf-8')
        else:
            encrypted_bytes = encrypted_string

        try:
            # 2. Desencriptar
            decrypted_bytes = Encriptacion.decrypt_data(encrypted_bytes, key)
            
            # 3. Retornar como texto legible
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            print(f"Error al desencriptar: {e}")
            return "" # Retornar vacío si falla la desencriptación