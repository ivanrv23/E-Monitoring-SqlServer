import re
import os
import pytz
import numpy as np
from io import BytesIO
from datetime import datetime, timedelta
from PySide6.QtWidgets import QColorDialog, QFileDialog
from PySide6.QtCore import QByteArray, Qt, QLocale
from PySide6.QtGui import QPixmap
from controllers.ProyectoController import ProyectoController

class MetodosGenerales:
    
    def convertirHexadecimalRGB(hexacolor):
        hex_color = hexacolor.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))

    def validarFormatoFecha(fecha):
        formatos_validos = [
            "%d/%m/%Y",    # Día/Mes/Año
            "%-d/%m/%Y",   # Día (sin cero inicial)/Mes/Año
            "%Y-%m-%d",    # Año-Mes-Día (ISO estándar)
            "%d-%m-%Y",    # Día-Mes-Año con guiones
            "%Y/%m/%d",    # Año/Mes/Día con barras
            "%d %b %Y",    # Día Mes (abreviado) Año, ejemplo: 25 Oct 2024
            "%d %B %Y",    # Día Mes completo Año, ejemplo: 25 Octubre 2024
            "%d-%b-%Y",    # Día-Mes (abreviado)-Año, ejemplo: 25-Oct-2024
            "%d-%B-%Y",    # Día-Mes completo-Año, ejemplo: 25-Octubre-2024
            "%d.%m.%Y",    # Día.Mes.Año, formato europeo con puntos
            "%Y.%m.%d",    # Año.Mes.Día con puntos
            "%-d/%-m/%Y",  # Día (sin cero inicial)/Mes (sin cero inicial)/Año
            '%d/%m/%y',    # Día/Mes/Año (año dos dígitos)
        ]
        formato_standar = "%Y-%m-%d"
        for formato in formatos_validos:
            try:
                fechavalida = datetime.strptime(fecha, formato)
                return fechavalida.strftime(formato_standar)
            except ValueError:
                continue
        return None

    def validarFormatoHora(hora):
        patrones_hora = [
            r'^([01]\d|2[0-3]):[0-5]\d$',               # HH:MM
            r'^([01]\d|2[0-3]):[0-5]\d:[0-5]\d$',        # HH:MM:SS
            r'^([01]\d|2[0-3]):[0-5]\d:[0-5]\d\.\d+$'    # HH:MM:SS.sss
        ]
        for patron in patrones_hora:
            if re.match(patron, hora):
                try:
                    hora_estandar = datetime.strptime(hora.split('.')[0], "%H:%M:%S")
                    return hora_estandar.strftime("%H:%M:%S")
                except ValueError:
                    hora_estandar = datetime.strptime(hora, "%H:%M")
                    return hora_estandar.strftime("%H:%M:%S")
        return None
    
    def validarEsNumero(texto):
        try:
            float(texto)
            return True
        except ValueError:
            return False
    
    def validarEsAngulo(texto):
        patron1 = r"^\s*(\d{1,3})°\s*(\d{1,2})'\s*(\d{1,2}(?:\.\d+)?)\"\s*$"
        patron2 = r"^\s*(\d{1,3})°\s*(\d{1,2})'\s*(\d{1,2}(?:\.\d+)?)\''\s*$"
        match = re.match(patron1, texto)
        if not match:
            match = re.match(patron2, texto)
        if not match:
            return False
        grados, minutos, segundos = map(float, match.groups())
        return 0 <= grados <= 360 and 0 <= minutos < 60 and 0 <= segundos < 60
    
    def convertirImagenBlob(imagen):
        # Leer la imagen y convertirla en bytes
        with open(imagen, 'rb') as file:
            blob = file.read()
        return blob

    def obtenerRangoFechas(dias):
        timezone = pytz.timezone("America/Lima")
        fechafinal = datetime.now(timezone)
        fechainicial = fechafinal - timedelta(days=dias)
        fechafinal = fechafinal.strftime("%Y-%m-%d %H:%M:%S")
        fechainicial = fechainicial.strftime("%Y-%m-%d %H:%M:%S")
        return fechainicial, fechafinal
    
    def obtenerFechasRangoUnyear(fechafin, dias):
        fechafin_dt = datetime.strptime(fechafin, "%Y-%m-%d %H:%M:%S")
        fechainicial_dt = fechafin_dt - timedelta(days=dias)
        fechainicial = fechainicial_dt.strftime("%Y-%m-%d %H:%M:%S")
        return fechainicial
    
    def obtenerMesAnio(fecha):
        # Establecer la localización en español
        locale = QLocale(QLocale.Spanish, QLocale.Spain)
        # Obtener el nombre del mes y el año en el formato deseado
        mes_anio = locale.toString(fecha, "MMMM yyyy").upper()  # Convierte el mes a mayúsculas
        return mes_anio
    
    def obtenerDiaMesAnio(fecha):
        # Establecer la localización en español
        locale = QLocale(QLocale.Spanish, QLocale.Spain)
        # Convertir la fecha al formato "dd de mes del yyyy"
        dia_mes_anio = locale.toString(fecha, "d 'de' MMMM 'del' yyyy")
        return dia_mes_anio.lower()
    
    def cambiarColorBoton(boton):              
        color = QColorDialog.getColor()
        if color.isValid():
            boton.setStyleSheet("background-color: %s" % color.name())
    
    def validarFormatoFechaDatabase(fecha_str):
        try:
            datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")
            return True
        except ValueError:
            return False
        
    def convertir_imagen_a_blob(imagen):
        try:
            with open(imagen, 'rb') as file:
                return file.read()
        except (FileNotFoundError, IOError, Exception):
            return None
    
    def convertir_imagen_a_blob_buffer(imagen_pil):
        buffer = BytesIO()
        imagen_pil.save(buffer, format='PNG')
        return buffer.getvalue()

    def convertir_blob_a_pixmap(blob):
        # Crear un QByteArray desde el blob
        byte_array = QByteArray(blob)
        pixmap = QPixmap()
        pixmap.loadFromData(byte_array)
        return pixmap
    
    def cargarImagenLocal(labelvista, inputnombre=None):
        # Abre el cuadro de diálogo para seleccionar la imagen
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            None, "Seleccionar imagen", "", "Archivos de Imagen (*.png *.jpg *.jpeg *.bmp);", options=options
        )
        if file_path:
            try:
                # Obtener el nombre del archivo
                if inputnombre:
                    nombre_archivo = file_path.split("/")[-1]
                    inputnombre.setText(nombre_archivo)
                # Crear el objeto QPixmap a partir del archivo seleccionado
                pixmap = QPixmap(file_path)
                # Ajustar la imagen a un tamaño máximo de 120x120, manteniendo la proporción
                pixmap = pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                # Mostrar la imagen en el QLabel
                labelvista.setPixmap(pixmap)
                return file_path
            except Exception as e:
                return None
        else:
            return None
        
    def llenar_componentes_combo(proyecto_id, comboComponente):
        # cargar data componentes
        componentes = ProyectoController.ctrlObtenerComponentesProyecto(proyecto_id)
        if componentes:
            for fila in componentes:
                comboComponente.addItem(str(fila[2]), fila[0])
            comboComponente.setEnabled(True)
    
    def ctrlAgruparPrismasSegunTipo(datos):
        agrupados = {}
        for nombre, idequipo, tercer_valor in datos:
            if tercer_valor not in agrupados:
                agrupados[tercer_valor] = []
            agrupados[tercer_valor].append(nombre)
        return agrupados
    
    def convertirBlobImagen(blob):
        return BytesIO(blob)
    
    def convertiraRGBestandar(colores_las):
        factor_escala = 65535 / 255
        return (colores_las / factor_escala).astype(np.uint8)
    
    def validarNuemroEntero(value):
        try:
            return int(value) if value and value.strip() else 0
        except ValueError:
            return 0
    
    def recortarImagenEspacioBlanco(imagen, margen_lateral=5, margen_vertical=20):
        imagen_gris = imagen.convert("L")
        imagen_np = np.array(imagen_gris)
        mask = imagen_np < 240
        coords = np.argwhere(mask)
        if coords.size == 0:
            return imagen
        # Obtener los límites mínimo y máximo de los píxeles no blancos
        y_min, x_min = coords.min(axis=0)
        y_max, x_max = coords.max(axis=0)
        # Aplicar el margen y recortar la imagen
        left = max(0, x_min - margen_lateral)
        top = max(0, y_min - margen_vertical)
        right = min(imagen.width, x_max + margen_lateral)
        bottom = min(imagen.height, y_max + margen_vertical)
        # Recortar la imagen original (en color)
        imagen_recortada = imagen.crop((left, top, right, bottom))
        return imagen_recortada
    
    def validarFormatoFechaCargaPrismas(fecha):
        formatos_validos = [
            "%d/%m/%Y", "%-d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d",
            "%d %b %Y", "%d %B %Y", "%d-%b-%Y", "%d-%B-%Y", "%d.%m.%Y",
            "%Y.%m.%d", "%-d/%-m/%Y", '%d/%m/%y',
            "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M", "%d-%m-%Y %H:%M:%S", "%d-%m-%Y %H:%M",
            "%d %b %Y %H:%M:%S", "%d %B %Y %H:%M:%S", "%d-%b-%Y %H:%M:%S",
            "%d-%B-%Y %H:%M:%S", "%d.%m.%Y %H:%M:%S", "%Y.%m.%d %H:%M:%S",
            "%-d/%-m/%Y %H:%M:%S", '%d/%m/%y %H:%M:%S'
        ]

        for formato in formatos_validos:
            try:
                fechavalida = datetime.strptime(fecha, formato)
                # Si el formato no incluye tiempo, agregamos "00:00:00"
                if formato.count('%') == 3:  # Solo contiene día, mes y año
                    return fechavalida.strftime("%Y-%m-%d 00:00:00")
                else:
                    return fechavalida.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue
        return None
    
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
        except Exception as e:
            return False
    