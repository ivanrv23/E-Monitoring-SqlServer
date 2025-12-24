import re
import os
import pytz
import numpy as np
from io import BytesIO
from datetime import datetime, timedelta, time
from PySide6.QtWidgets import QColorDialog, QFileDialog
# AGREGADO QDate y QDateTime a las importaciones
from PySide6.QtCore import QByteArray, Qt, QLocale, QDate, QDateTime
from PySide6.QtGui import QPixmap
from controllers.ProyectoController import ProyectoController

class MetodosGenerales:
    
    # -------------------------------------------------------------------------
    # MÉTODO CORE: Convierte QDate/QDateTime/String -> Python datetime
    # -------------------------------------------------------------------------
    @staticmethod
    def _parsear_fecha_segura(fecha):
        """
        Normaliza cualquier entrada (Qt Object, String sucio, ISO) a datetime de Python.
        """
        if not fecha:
            return None
            
        # 1. Soporte directo para objetos de PySide6 (La causa de tu error)
        if isinstance(fecha, QDate):
            return datetime(fecha.year(), fecha.month(), fecha.day())
        
        if isinstance(fecha, QDateTime):
            return fecha.toPython() # Convierte QDateTime a datetime

        # 2. Si ya es datetime de Python
        if isinstance(fecha, datetime):
            return fecha
            
        # 3. Procesamiento de Strings
        fecha_str = str(fecha).strip()
        
        # Limpieza para formatos ISO largos con Timezone (ej. SQL Server)
        if len(fecha_str) >= 19:
            # "2025-12-24 12:05:55.502578-05:00" -> "2025-12-24 12:05:55"
            fecha_clean = fecha_str[:19].replace('T', ' ')
            try:
                return datetime.strptime(fecha_clean, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass 
        
        # Intentos de formatos comunes
        formatos = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y"
        ]
        
        for fmt in formatos:
            try:
                return datetime.strptime(fecha_str, fmt)
            except ValueError:
                continue
                
        return None

    # -------------------------------------------------------------------------
    # MÉTODOS DE FORMATO (Corregidos para usar el parseador seguro)
    # -------------------------------------------------------------------------

    @staticmethod
    def obtenerMesAnio(fecha):
        try:
            # Obtenemos un datetime limpio
            fecha_dt = MetodosGenerales._parsear_fecha_segura(fecha)
            
            if fecha_dt:
                locale = QLocale(QLocale.Spanish, QLocale.Spain)
                # Convertimos de nuevo a QDateTime para que QLocale funcione perfecto
                q_dt = QDateTime(fecha_dt)
                return locale.toString(q_dt, "MMMM yyyy").upper()
            return ""
        except Exception as e:
            print(f"Error obtenerMesAnio: {e}")
            return ""
    
    @staticmethod
    def obtenerDiaMesAnio(fecha):
        try:
            fecha_dt = MetodosGenerales._parsear_fecha_segura(fecha)
            
            if fecha_dt:
                locale = QLocale(QLocale.Spanish, QLocale.Spain)
                q_dt = QDateTime(fecha_dt)
                return locale.toString(q_dt, "d 'de' MMMM 'del' yyyy").lower()
            return ""
        except Exception as e:
            print(f"Error obtenerDiaMesAnio: {e}")
            return ""

    @staticmethod
    def validarFormatoFecha(fecha):
        # Usamos el parseador seguro
        fecha_dt = MetodosGenerales._parsear_fecha_segura(fecha)
        if fecha_dt:
            return fecha_dt.strftime("%Y-%m-%d")

        # Fallback para strings muy raros (lógica original conservada)
        formatos_validos = [
            "%d/%m/%Y", "%-d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d",
            "%d %b %Y", "%d %B %Y", "%d-%b-%Y", "%d.%m.%Y"
        ]
        fecha_str = str(fecha).strip()
        for formato in formatos_validos:
            try:
                fechavalida = datetime.strptime(fecha_str, formato)
                return fechavalida.strftime("%Y-%m-%d")
            except ValueError:
                continue
        return None

    @staticmethod
    def obtenerFechasRangoUnyear(fechafin, dias):
        try:
            fechafin_dt = MetodosGenerales._parsear_fecha_segura(fechafin)
            
            if not fechafin_dt:
                fechafin_dt = datetime.now()
                
            fechainicial_dt = fechafin_dt - timedelta(days=dias)
            return fechainicial_dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    @staticmethod
    def validarFormatoFechaDatabase(fecha_str):
        return MetodosGenerales._parsear_fecha_segura(fecha_str) is not None

    @staticmethod
    def validarFormatoFechaCargaPrismas(fecha):
        fecha_dt = MetodosGenerales._parsear_fecha_segura(fecha)
        if fecha_dt:
            return fecha_dt.strftime("%Y-%m-%d %H:%M:%S")
        return None

    # -------------------------------------------------------------------------
    # RESTO DE MÉTODOS (Sin cambios lógicos, solo incluidos para completar)
    # -------------------------------------------------------------------------

    @staticmethod
    def convertirHexadecimalRGB(hexacolor):
        if not hexacolor: return (0, 0, 0)
        hex_color = hexacolor.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))

    @staticmethod
    def validarFormatoHora(hora):
        if not hora: return None
        if isinstance(hora, (datetime, time)):
            return hora.strftime("%H:%M:%S")
        
        patrones_hora = [
            r'^([01]\d|2[0-3]):[0-5]\d$',
            r'^([01]\d|2[0-3]):[0-5]\d:[0-5]\d$',
            r'^([01]\d|2[0-3]):[0-5]\d:[0-5]\d\.\d+$'
        ]
        hora_str = str(hora).strip()
        for patron in patrones_hora:
            if re.match(patron, hora_str):
                try:
                    hora_limpia = hora_str.split('.')[0]
                    return datetime.strptime(hora_limpia, "%H:%M:%S").strftime("%H:%M:%S")
                except ValueError:
                    try:
                        return datetime.strptime(hora_str, "%H:%M").strftime("%H:%M:%S")
                    except ValueError:
                        continue
        return None
    
    @staticmethod
    def validarEsNumero(texto):
        try:
            float(texto)
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validarEsAngulo(texto):
        if not texto: return False
        patron1 = r"^\s*(\d{1,3})°\s*(\d{1,2})'\s*(\d{1,2}(?:\.\d+)?)\"\s*$"
        patron2 = r"^\s*(\d{1,3})°\s*(\d{1,2})'\s*(\d{1,2}(?:\.\d+)?)\''\s*$"
        match = re.match(patron1, str(texto))
        if not match:
            match = re.match(patron2, str(texto))
        if not match:
            return False
        grados, minutos, segundos = map(float, match.groups())
        return 0 <= grados <= 360 and 0 <= minutos < 60 and 0 <= segundos < 60
    
    @staticmethod
    def convertirImagenBlob(imagen):
        try:
            with open(imagen, 'rb') as file:
                blob = file.read()
            return blob
        except Exception:
            return None

    @staticmethod
    def obtenerRangoFechas(dias):
        try:
            timezone = pytz.timezone("America/Lima")
            fechafinal = datetime.now(timezone)
            fechainicial = fechafinal - timedelta(days=dias)
            return fechainicial.strftime("%Y-%m-%d %H:%M:%S"), fechafinal.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            fechafinal = datetime.now()
            fechainicial = fechafinal - timedelta(days=dias)
            return fechainicial.strftime("%Y-%m-%d %H:%M:%S"), fechafinal.strftime("%Y-%m-%d %H:%M:%S")
    
    @staticmethod
    def cambiarColorBoton(boton):              
        color = QColorDialog.getColor()
        if color.isValid():
            boton.setStyleSheet("background-color: %s" % color.name())
    
    @staticmethod
    def convertir_imagen_a_blob(imagen):
        try:
            with open(imagen, 'rb') as file:
                return file.read()
        except (FileNotFoundError, IOError, Exception):
            return None
    
    @staticmethod
    def convertir_imagen_a_blob_buffer(imagen_pil):
        try:
            buffer = BytesIO()
            imagen_pil.save(buffer, format='PNG')
            return buffer.getvalue()
        except Exception:
            return None

    @staticmethod
    def convertir_blob_a_pixmap(blob):
        if not blob: return QPixmap()
        byte_array = QByteArray(blob)
        pixmap = QPixmap()
        pixmap.loadFromData(byte_array)
        return pixmap
    
    @staticmethod
    def cargarImagenLocal(labelvista, inputnombre=None):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            None, "Seleccionar imagen", "", "Archivos de Imagen (*.png *.jpg *.jpeg *.bmp);", options=options
        )
        if file_path:
            try:
                if inputnombre:
                    nombre_archivo = file_path.split("/")[-1]
                    inputnombre.setText(nombre_archivo)
                pixmap = QPixmap(file_path)
                pixmap = pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                labelvista.setPixmap(pixmap)
                return file_path
            except Exception:
                return None
        else:
            return None
        
    @staticmethod
    def llenar_componentes_combo(proyecto_id, comboComponente):
        comboComponente.clear()
        componentes = ProyectoController.ctrlObtenerComponentesProyecto(proyecto_id)
        if componentes:
            for fila in componentes:
                comboComponente.addItem(str(fila[2]), fila[0])
            comboComponente.setEnabled(True)
        else:
            comboComponente.setEnabled(False)
    
    @staticmethod
    def ctrlAgruparPrismasSegunTipo(datos):
        agrupados = {}
        for nombre, idequipo, tercer_valor in datos:
            if tercer_valor not in agrupados:
                agrupados[tercer_valor] = []
            agrupados[tercer_valor].append(nombre)
        return agrupados
    
    @staticmethod
    def convertirBlobImagen(blob):
        return BytesIO(blob)
    
    @staticmethod
    def convertiraRGBestandar(colores_las):
        factor_escala = 65535 / 255
        return (colores_las / factor_escala).astype(np.uint8)
    
    @staticmethod
    def validarNumeroEntero(value):
        try:
            return int(value) if value and str(value).strip() else 0
        except ValueError:
            return 0
    
    @staticmethod
    def recortarImagenEspacioBlanco(imagen, margen_lateral=5, margen_vertical=20):
        try:
            imagen_gris = imagen.convert("L")
            imagen_np = np.array(imagen_gris)
            mask = imagen_np < 240
            coords = np.argwhere(mask)
            if coords.size == 0:
                return imagen
            y_min, x_min = coords.min(axis=0)
            y_max, x_max = coords.max(axis=0)
            left = max(0, x_min - margen_lateral)
            top = max(0, y_min - margen_vertical)
            right = min(imagen.width, x_max + margen_lateral)
            bottom = min(imagen.height, y_max + margen_vertical)
            imagen_recortada = imagen.crop((left, top, right, bottom))
            return imagen_recortada
        except Exception:
            return imagen
    
    @staticmethod
    def existeArchivosRuta(ruta):
        try:
            ruta_base = os.path.dirname(os.path.abspath(__file__))
            ruta_absoluta = os.path.join(ruta_base, ruta)
            if not os.path.exists(ruta_absoluta):
                return False
            for archivo in os.listdir(ruta_absoluta):
                if os.path.isfile(os.path.join(ruta_absoluta, archivo)):
                    return True
            return False
        except Exception:
            return False