import wmi
import os
from cryptography.fernet import Fernet
import hashlib
import subprocess
from utils.common.rutasarchivos import resource_path
class Encriptacion:
    
    def generate_fingerprint():
        system_uuid = Encriptacion.get_system_uuid()
        baseboard_product = Encriptacion.get_baseboard_product()
        disk_serial = Encriptacion.get_disk_serial()
        # Combinar y hashear
        combined_data = f"{system_uuid}{baseboard_product}{disk_serial}"
        return hashlib.sha256(combined_data.encode()).hexdigest()
    
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

    def get_system_uuid():
        """Obtiene el UUID del sistema."""
        uuid = Encriptacion.run_command("wmic csproduct get uuid")
        if uuid == "Unknown":
            uuid = Encriptacion.run_command('(Get-WmiObject Win32_ComputerSystemProduct).UUID', use_powershell=True)
        return uuid.split("\n")[-1].strip() if uuid != "Unknown" else "Unknown"

    def get_baseboard_product():
        """Obtiene el producto de la placa base."""
        product = Encriptacion.run_command("wmic baseboard get product")
        if product == "Unknown":
            product = Encriptacion.run_command('(Get-WmiObject Win32_BaseBoard).Product', use_powershell=True)
        return product.split("\n")[-1].strip() if product != "Unknown" else "Unknown"

    def get_disk_serial():
        """Obtiene el serial del disco principal."""
        serial = Encriptacion.run_command("wmic diskdrive get serialnumber")
        if serial == "Unknown":
            serial = Encriptacion.run_command('(Get-WmiObject Win32_DiskDrive | Where-Object { $_.DeviceID -eq "\\\\.\\PHYSICALDRIVE0" }).SerialNumber', use_powershell=True)
        return serial.split("\n")[-1].strip() if serial != "Unknown" else "Unknown"
    
    #################################################################################
    def obtener_dispositivo_serie_placa_base():
        c = wmi.WMI()
        for board in c.Win32_BaseBoard():
            return board.SerialNumber
    
    def load_key():
        credenciales_path=resource_path('services/security/clave.key')
        with open(credenciales_path, "rb") as key_file:
            key = key_file.read()
        return key

    def encrypt_data(data, key):
        cipher_suite = Fernet(key)
        encrypted_data = cipher_suite.encrypt(data)
        return encrypted_data

    def decrypt_data(encrypted_data, key):
        cipher_suite = Fernet(key)
        decrypted_data = cipher_suite.decrypt(encrypted_data)
        return decrypted_data
    
    def encrypt(text):
        key = Encriptacion.load_key()
        encrypted_data = Encriptacion.encrypt_data(text.encode(), key)
        return encrypted_data

    def decrypt(encrypted_data):
        key = Encriptacion.load_key()
        decrypted_text = Encriptacion.decrypt_data(encrypted_data, key)
        return decrypted_text.decode()
    