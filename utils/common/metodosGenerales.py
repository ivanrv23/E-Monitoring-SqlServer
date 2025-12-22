import re
import os
import pytz
import numpy as np
from io import BytesIO
from datetime import datetime, timedelta, time
from PySide6.QtWidgets import QColorDialog, QFileDialog
from PySide6.QtCore import QByteArray, Qt, QLocale
from PySide6.QtGui import QPixmap
from controllers.ProyectoController import ProyectoController

class MetodosGenerales:
    
    @staticmethod
    def convertirHexadecimalRGB(hexacolor):
        if not hexacolor: return (0, 0, 0)
        hex_color = hexacolor.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))

    @staticmethod
    def validarFormatoFecha(fecha):
        if not fecha: return None
        
        # 1. Si ya es un objeto datetime (viene de SQL Server), lo formateamos y devolvemos
        if isinstance(fecha, datetime):
            return fecha.strftime("%Y-%m-%d")
            
        # 2. Si es texto, intentamos parsear
        formatos_validos = [
            "%d/%m/%Y", "%-d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d",
            "%d %b %Y", "%d %B %Y", "%d-%b-%Y", "%d-%B-%Y", "%d.%m.%Y",
            "%Y.%m.%d", "%-d/%-m/%Y", '%d/%m/%y',
            "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"
        ]
        formato_standar = "%Y-%m-%d"
        fecha_str = str(fecha).strip()
        
        for formato in formatos_validos:
            try:
                fechavalida = datetime.strptime(fecha_str, formato)
                return fechavalida.strftime(formato_standar)
            except ValueError:
                continue
        return None

    @staticmethod
    def validarFormatoHora(hora):
        if not hora: return None
        
        # 1. Si llega un objeto time o datetime (SQL Server)
        if isinstance(hora, (datetime, time)):
            return hora.strftime("%H:%M:%S")
        
        # 2. Si es texto
        patrones_hora = [
            r'^([01]\d|2[0-3]):[0-5]\d$',               # HH:MM
            r'^([01]\d|2[0-3]):[0-5]\d:[0-5]\d$',        # HH:MM:SS
            r'^([01]\d|2[0-3]):[0-5]\d:[0-5]\d\.\d+$'    # HH:MM:SS.sss
        ]
        hora_str = str(hora).strip()
        for patron in patrones_hora:
            if re.match(patron, hora_str):
                try:
                    hora_limpia = hora_str.split('.')[0] # Quitar milisegundos si es texto
                    hora_estandar = datetime.strptime(hora_limpia, "%H:%M:%S")
                    return hora_estandar.strftime("%H:%M:%S")
                except ValueError:
                    try:
                        hora_estandar = datetime.strptime(hora_str, "%H:%M")
                        return hora_estandar.strftime("%H:%M:%S")
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
    def obtenerFechasRangoUnyear(fechafin, dias):
        try:
            # CORRECCIÓN PRINCIPAL PARA TU ERROR:
            # Verificamos si fechafin ya es un objeto datetime (SQL Server) o texto (SQLite/CSV)
            if isinstance(fechafin, datetime):
                fechafin_dt = fechafin
            else:
                # Si es string, limpiamos posibles milisegundos (.000) y convertimos
                fecha_limpia = str(fechafin).split('.')[0]
                fechafin_dt = datetime.strptime(fecha_limpia, "%Y-%m-%d %H:%M:%S")
            
            fechainicial_dt = fechafin_dt - timedelta(days=dias)
            return fechainicial_dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            print(f"Error calculando rango fechas: {e}")
            # Retorno de seguridad para no romper la app
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    @staticmethod
    def obtenerMesAnio(fecha):
        try:
            if not isinstance(fecha, datetime):
                # Intentar parsear si es string
                fecha_str = str(fecha).split('.')[0]
                try:
                    fecha = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")
                except:
                    fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
            
            locale = QLocale(QLocale.Spanish, QLocale.Spain)
            return locale.toString(fecha, "MMMM yyyy").upper()
        except:
            return ""
    
    @staticmethod
    def obtenerDiaMesAnio(fecha):
        try:
            if not isinstance(fecha, datetime):
                fecha_str = str(fecha).split('.')[0]
                try:
                    fecha = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")
                except:
                    fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
            
            locale = QLocale(QLocale.Spanish, QLocale.Spain)
            return locale.toString(fecha, "d 'de' MMMM 'del' yyyy").lower()
        except:
            return ""
    
    @staticmethod
    def cambiarColorBoton(boton):              
        color = QColorDialog.getColor()
        if color.isValid():
            boton.setStyleSheet("background-color: %s" % color.name())
    
    @staticmethod
    def validarFormatoFechaDatabase(fecha_str):
        try:
            if isinstance(fecha_str, datetime):
                return True
            datetime.strptime(str(fecha_str).split('.')[0], "%Y-%m-%d %H:%M:%S")
            return True
        except ValueError:
            return False
        
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
                # Ajustar indices segun tu consulta SQL: ID=0, Nombre=2
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
    def validarFormatoFechaCargaPrismas(fecha):
        if not fecha: return None
        
        # Si ya es datetime, retornar string para SQL Server
        if isinstance(fecha, datetime):
            return fecha.strftime("%Y-%m-%d %H:%M:%S")

        formatos_validos = [
            "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M", "%d-%m-%Y %H:%M:%S", "%d-%m-%Y %H:%M",
            "%d/%m/%Y", "%-d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d",
            "%d %b %Y %H:%M:%S", "%d %B %Y %H:%M:%S", "%d-%b-%Y %H:%M:%S",
            "%d-%B-%Y %H:%M:%S", "%d.%m.%Y %H:%M:%S", "%Y.%m.%d %H:%M:%S",
            "%-d/%-m/%Y %H:%M:%S", '%d/%m/%y %H:%M:%S'
        ]

        fecha_str = str(fecha).strip()
        for formato in formatos_validos:
            try:
                fechavalida = datetime.strptime(fecha_str, formato)
                return fechavalida.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue
        return None
    
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