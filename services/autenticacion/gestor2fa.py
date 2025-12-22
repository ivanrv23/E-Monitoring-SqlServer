import json
import os
import pyotp
import qrcode
import time
from datetime import datetime
from io import BytesIO
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt

class Gestor2FA:
    """Gestor para autenticación en dos factores (2FA) usando TOTP"""
    
    ARCHIVO_SECRETOS = "secretos_2fa.json"
    APP_NAME = "E-Monitoring System"
    
    @staticmethod
    def _obtener_ruta_archivo():
        """Obtiene la ruta completa del archivo de secretos"""
        try:
            from utils.common.rutasarchivos import resource_path
            return resource_path(Gestor2FA.ARCHIVO_SECRETOS)
        except ImportError:
            return Gestor2FA.ARCHIVO_SECRETOS
    
    @staticmethod
    def _cargar_datos():
        """Carga los datos desde el archivo JSON"""
        archivo = Gestor2FA._obtener_ruta_archivo()
        
        if not os.path.exists(archivo):
            datos_base = {
                "_info": "Archivo de secretos 2FA - E-Monitoring",
                "_fecha_creacion": datetime.now().isoformat(),
                "_app_name": Gestor2FA.APP_NAME,
                "usuarios": {}
            }
            with open(archivo, 'w', encoding='utf-8') as f:
                json.dump(datos_base, f, indent=2, ensure_ascii=False)
            return datos_base
        
        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {"usuarios": {}}
    
    @staticmethod
    def _guardar_datos(datos):
        """Guarda los datos en el archivo JSON"""
        try:
            archivo = Gestor2FA._obtener_ruta_archivo()
            os.makedirs(os.path.dirname(archivo), exist_ok=True)
            
            with open(archivo, 'w', encoding='utf-8') as f:
                json.dump(datos, f, indent=2, ensure_ascii=False, default=str)
            return True
        except Exception:
            return False
    
    @staticmethod
    def tiene_2fa_activado(usuario):
        """Verifica si un usuario tiene 2FA activado"""
        datos = Gestor2FA._cargar_datos()
        
        if 'usuarios' in datos and usuario in datos['usuarios']:
            usuario_data = datos['usuarios'][usuario]
            if isinstance(usuario_data, dict):
                estado = usuario_data.get('estado', 'activo')
                return estado == 'activo' and 'secret' in usuario_data
        
        return False
    
    @staticmethod
    def obtener_secreto(usuario):
        """Obtiene el secreto de un usuario"""
        datos = Gestor2FA._cargar_datos()
        
        if 'usuarios' in datos and usuario in datos['usuarios']:
            return datos['usuarios'][usuario].get('secret')
        
        return None
    
    @staticmethod
    def generar_secreto_temporal():
        """Genera un nuevo secreto temporal"""
        return pyotp.random_base32()
    
    @staticmethod
    def generar_qr_pixmap(usuario, secreto, tamano=200):
        """Genera un código QR como QPixmap"""
        try:
            totp = pyotp.TOTP(secreto)
            uri = totp.provisioning_uri(
                name=usuario,
                issuer_name=Gestor2FA.APP_NAME
            )
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(uri)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="#2E7D32", back_color="white")
            
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            pixmap = QPixmap()
            pixmap.loadFromData(buffer.read())
            
            return pixmap.scaled(tamano, tamano, 
                                Qt.AspectRatioMode.KeepAspectRatio, 
                                Qt.TransformationMode.SmoothTransformation)
        except Exception:
            pixmap = QPixmap(tamano, tamano)
            pixmap.fill(Qt.GlobalColor.white)
            return pixmap
    
    @staticmethod
    def verificar_codigo_y_guardar(usuario, secreto_temporal, codigo):
        """Verifica código y guarda si es válido (activación)"""
        try:
            totp = pyotp.TOTP(secreto_temporal)
            
            if totp.verify(codigo, valid_window=1):
                datos = Gestor2FA._cargar_datos()
                
                usuario_data = {
                    'secret': secreto_temporal,
                    'fecha_activacion': datetime.now().isoformat(),
                    'ultimo_acceso': datetime.now().isoformat(),
                    'metodo': 'TOTP',
                    'estado': 'activo'
                }
                
                if 'usuarios' not in datos:
                    datos['usuarios'] = {}
                datos['usuarios'][usuario] = usuario_data
                
                return Gestor2FA._guardar_datos(datos)
            
            return False
        except Exception:
            return False
    
    @staticmethod
    def verificar_codigo_existente(usuario, codigo):
        """Verifica código contra secreto almacenado"""
        try:
            secreto = Gestor2FA.obtener_secreto(usuario)
            
            if not secreto:
                return False
            
            totp = pyotp.TOTP(secreto)
            es_valido = totp.verify(codigo, valid_window=1)
            
            if es_valido:
                datos = Gestor2FA._cargar_datos()
                if 'usuarios' in datos and usuario in datos['usuarios']:
                    datos['usuarios'][usuario]['ultimo_acceso'] = datetime.now().isoformat()
                Gestor2FA._guardar_datos(datos)
                return True
            return False
                
        except Exception:
            return False
    
    @staticmethod
    def eliminar_2fa(usuario):
        """Desactiva el 2FA para un usuario"""
        try:
            datos = Gestor2FA._cargar_datos()
            
            if 'usuarios' in datos and usuario in datos['usuarios']:
                datos['usuarios'][usuario]['estado'] = 'inactivo'
                datos['usuarios'][usuario]['fecha_desactivacion'] = datetime.now().isoformat()
                
                return Gestor2FA._guardar_datos(datos)
            
            return False
        except Exception:
            return False
    
    @staticmethod
    def obtener_codigos_respaldo(usuario, cantidad=6):
        """Genera códigos de respaldo"""
        try:
            secreto = Gestor2FA.obtener_secreto(usuario)
            
            if not secreto:
                return []
            
            hotp = pyotp.HOTP(secreto)
            codigos = []
            base = int(time.time()) // 100
            
            for i in range(cantidad):
                codigos.append(hotp.at(base + i))
            
            datos = Gestor2FA._cargar_datos()
            
            if 'usuarios' in datos and usuario in datos['usuarios']:
                datos['usuarios'][usuario]['codigos_respaldo'] = codigos
                datos['usuarios'][usuario]['fecha_generacion_respaldo'] = datetime.now().isoformat()
            
            Gestor2FA._guardar_datos(datos)
            
            return codigos
        except Exception:
            return []