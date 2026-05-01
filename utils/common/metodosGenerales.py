import re
import os
import pytz
import numpy as np
from io import BytesIO
from datetime import datetime, timedelta, time

# Importaciones de PySide6 (Se incluyen QDate y QDateTime)
from PySide6.QtWidgets import QColorDialog, QFileDialog
from PySide6.QtCore import QByteArray, Qt, QLocale, QDate, QDateTime,QTime
from PySide6.QtGui import QPixmap

# Controladores
from controllers.ProyectoController import ProyectoController

class MetodosGenerales:
    
    # -------------------------------------------------------------------------
    # CORE: Lógica central para normalización de fechas
    # -------------------------------------------------------------------------
    @staticmethod
    def _parsear_fecha_segura(fecha):
        """Normaliza entrada (Qt Object, String sucio, ISO, formatos latinos) a datetime."""
        if not fecha:
            return None
            
        # 1. Objetos de Librería
        if isinstance(fecha, QDate):
            return datetime(fecha.year(), fecha.month(), fecha.day())
        if isinstance(fecha, QDateTime):
            return fecha.toPython()
        if isinstance(fecha, datetime):
            return fecha
            
        # 2. Limpieza de String
        fecha_str = str(fecha).strip()
        
        # Limpieza ISO con Timezone (ej: SQL Server)
        if len(fecha_str) >= 19 and 'T' in fecha_str:
            try:
                clean = fecha_str[:19].replace('T', ' ')
                return datetime.strptime(clean, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass 

        # 3. Detección Inteligente (Regex para 5/2/2025, 05-02-25, etc.)
        patron_latino = r'^(\d{1,2})[-/.](\d{1,2})[-/.](\d{2,4})$'
        match = re.match(patron_latino, fecha_str)
        
        if match:
            dia, mes, anio = map(int, match.groups())
            if anio < 100: anio += 2000 # Corrección año corto
            try:
                return datetime(anio, mes, dia)
            except ValueError:
                pass 

        # 4. Fallback formatos estándar
        formatos = [
            "%Y-%m-%d %H:%M:%S", "%Y-%m-%d",
            "%d/%m/%Y %H:%M:%S", "%d/%m/%Y", "%d-%m-%Y",
            "%d/%m/%y", "%d-%m-%y"
        ]
        
        for fmt in formatos:
            try:
                return datetime.strptime(fecha_str, fmt)
            except ValueError:
                continue
                
        return None
    # -------------------------------------------------------------------------
    # MÉTODOS DE FECHA Y HORA (Optimizados)
    # -------------------------------------------------------------------------

    @staticmethod
    def validarFormatoFecha(fecha):
        fecha_dt = MetodosGenerales._parsear_fecha_segura(fecha)
        if fecha_dt:
            return fecha_dt.strftime("%Y-%m-%d")

        # Fallback original conservado
        formatos_validos = [
            "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", 
            "%d/%m/%y", "%d-%m-%y", "%d.%m.%Y", "%Y-%m-%d"
        ]
        fecha_str = str(fecha).strip()
        for formato in formatos_validos:
            try:
                return datetime.strptime(fecha_str, formato).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return None

    @staticmethod
    def validarFormatoHora(hora):
        if not hora: return None
            
        # 1. Soporte Objetos
        if isinstance(hora, (datetime, time)): return hora.strftime("%H:%M:%S")
        if isinstance(hora, QTime): return hora.toString("HH:mm:ss")
        if isinstance(hora, QDateTime): return hora.time().toString("HH:mm:ss")

        # 2. Limpieza String
        hora_str = str(hora).strip().split('.')[0] # Quitar milisegundos

        # 3. Formatos estándar (Incluye AM/PM)
        formatos_comunes = ["%H:%M:%S", "%H:%M", "%I:%M %p", "%I:%M:%S %p", "%I:%M%p"]
        for fmt in formatos_comunes:
            try:
                return datetime.strptime(hora_str, fmt).strftime("%H:%M:%S")
            except ValueError:
                continue

        # 4. Regex Robusto
        match = re.match(r'^(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?$', hora_str)
        if match:
            h, m, s = match.groups()
            try:
                return time(int(h), int(m), int(s or 0)).strftime("%H:%M:%S")
            except ValueError:
                pass
        return None
    
    @staticmethod
    def obtenerMesAnio(fecha):
        try:
            dt = MetodosGenerales._parsear_fecha_segura(fecha)
            if dt:
                # Convertimos a QDateTime para usar QLocale (mejor soporte español)
                locale = QLocale(QLocale.Spanish, QLocale.Spain)
                return locale.toString(QDateTime(dt), "MMMM yyyy").upper()
            return ""
        except Exception as e:
            print(f"Error obtenerMesAnio: {e}")
            return ""
    
    @staticmethod
    def obtenerDiaMesAnio(fecha):
        try:
            dt = MetodosGenerales._parsear_fecha_segura(fecha)
            if dt:
                locale = QLocale(QLocale.Spanish, QLocale.Spain)
                return locale.toString(QDateTime(dt), "d 'de' MMMM 'del' yyyy").lower()
            return ""
        except Exception as e:
            print(f"Error obtenerDiaMesAnio: {e}")
            return ""

    @staticmethod
    def obtenerFechasRangoUnyear(fechafin, dias):
        try:
            dt_fin = MetodosGenerales._parsear_fecha_segura(fechafin)
            if not dt_fin:
                dt_fin = datetime.now()
            
            dt_ini = dt_fin - timedelta(days=dias)
            return dt_ini.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def obtenerRangoFechas(dias):
        try:
            tz = pytz.timezone("America/Lima")
            fin = datetime.now(tz)
        except Exception:
            fin = datetime.now()
            
        ini = fin - timedelta(days=dias)
        return ini.strftime("%Y-%m-%d %H:%M:%S"), fin.strftime("%Y-%m-%d %H:%M:%S")
    
    @staticmethod
    def validarFormatoFechaDatabase(fecha_str):
        return MetodosGenerales._parsear_fecha_segura(fecha_str) is not None

    @staticmethod
    def validarFormatoFechaCargaPrismas(fecha):
        dt = MetodosGenerales._parsear_fecha_segura(fecha)
        return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else None

    # -------------------------------------------------------------------------
    # RESTO DE MÉTODOS (Conservados sin cambios de lógica)
    # -------------------------------------------------------------------------

    @staticmethod
    def validarEsNumero(texto):
        try:
            float(texto)
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validarNumeroEntero(value):
        try:
            return int(value) if value and str(value).strip() else 0
        except ValueError:
            return 0
    
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
        g, m, s = map(float, match.groups())
        return 0 <= g <= 360 and 0 <= m < 60 and 0 <= s < 60

    @staticmethod
    def convertirHexadecimalRGB(hexacolor):
        if not hexacolor: return (0, 0, 0)
        h = hexacolor.lstrip('#')
        return tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))
    
    @staticmethod
    def convertiraRGBestandar(colores_las):
        factor = 65535 / 255
        return (colores_las / factor).astype(np.uint8)

    # -------------------------------------------------------------------------
    # MANEJO DE IMÁGENES Y ARCHIVOS
    # -------------------------------------------------------------------------

    @staticmethod
    def convertirImagenBlob(imagen):
        try:
            with open(imagen, 'rb') as file:
                return file.read()
        except Exception:
            return None

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
    def convertirBlobImagen(blob):
        return BytesIO(blob)

    @staticmethod
    def convertir_blob_a_pixmap(blob):
        if not blob: return QPixmap()
        pixmap = QPixmap()
        pixmap.loadFromData(QByteArray(blob))
        return pixmap
    
    @staticmethod
    def cargarImagenLocal(labelvista, inputnombre=None):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            None, "Seleccionar imagen", "", 
            "Archivos de Imagen (*.png *.jpg *.jpeg *.bmp);", options=options
        )
        if file_path:
            try:
                if inputnombre:
                    inputnombre.setText(file_path.split("/")[-1])
                pix = QPixmap(file_path).scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                labelvista.setPixmap(pix)
                return file_path
            except Exception:
                return None
        return None

    @staticmethod
    def recortarImagenEspacioBlanco(imagen, margen_lateral=5, margen_vertical=20):
        try:
            imagen_gris = imagen.convert("L")
            imagen_np = np.array(imagen_gris)
            mask = imagen_np < 240
            coords = np.argwhere(mask)
            
            if coords.size == 0: return imagen
            
            y_min, x_min = coords.min(axis=0)
            y_max, x_max = coords.max(axis=0)
            
            left = max(0, x_min - margen_lateral)
            top = max(0, y_min - margen_vertical)
            right = min(imagen.width, x_max + margen_lateral)
            bottom = min(imagen.height, y_max + margen_vertical)
            
            return imagen.crop((left, top, right, bottom))
        except Exception:
            return imagen
    
    @staticmethod
    def existeArchivosRuta(ruta):
        try:
            base = os.path.dirname(os.path.abspath(__file__))
            ruta_abs = os.path.join(base, ruta)
            if not os.path.exists(ruta_abs): return False
            for archivo in os.listdir(ruta_abs):
                if os.path.isfile(os.path.join(ruta_abs, archivo)):
                    return True
            return False
        except Exception:
            return False

    # -------------------------------------------------------------------------
    # INTERFAZ Y CONTROLADORES
    # -------------------------------------------------------------------------

    @staticmethod
    def cambiarColorBoton(boton):              
        color = QColorDialog.getColor()
        if color.isValid():
            boton.setStyleSheet(f"background-color: {color.name()}")
        
    @staticmethod
    def llenar_componentes_combo(proyecto_id, comboComponente):
        comboComponente.clear()
        datos = ProyectoController.ctrlObtenerComponentesProyecto(proyecto_id)
        if datos:
            for fila in datos:
                comboComponente.addItem(str(fila[2]), fila[0])
            comboComponente.setEnabled(True)
        else:
            comboComponente.setEnabled(False)
    
    @staticmethod
    def ctrlAgruparPrismasSegunTipo(datos):
        agrupados = {}
        # Mantenemos la estructura solicitada (nombre, idequipo, tercer_valor/tipo)
        for nombre, idequipo, tipo in datos:
            if tipo not in agrupados:
                agrupados[tipo] = []
            agrupados[tipo].append(nombre)
        return agrupados
    
    @staticmethod
    def exportarDataInstrumentacion(datos, titulo_lectura, prefijo_archivo):
        if not datos:
            return

        import pandas as pd
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        import os
        from datetime import datetime

        try:
            # 1. Crear el DataFrame inicial con las columnas de la consulta
            # Indice 2: Fecha, Indice 1: Equipo, Indice 5: Lectura
            df = pd.DataFrame(datos)
            df = df[[2, 1, 5]].copy()
            df.columns = ['Fecha', 'Equipo', titulo_lectura]

            # 2. Configurar el dialogo de guardado
            nombre_sugerido = f"{prefijo_archivo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            filtro_formatos = "Archivo CSV (*.csv);;Libro de Excel (*.xlsx)"
            
            ruta, filtro = QFileDialog.getSaveFileName(
                None, "Exportar Datos", nombre_sugerido, filtro_formatos
            )

            if not ruta:
                return

            # 3. Procesar segun el formato elegido
            if "CSV" in filtro or ruta.lower().endswith('.csv'):
                if not ruta.lower().endswith('.csv'):
                    ruta += '.csv'
                
                # Exportacion simple en formato vertical
                df.to_csv(ruta, index=False, sep=',', encoding='utf-8-sig')

            else:
                if not ruta.lower().endswith('.xlsx'):
                    ruta += '.xlsx'
                
                # Crear matriz: Fechas en filas y Equipos en columnas
                df_pivot = df.pivot_table(
                    index='Fecha', 
                    columns='Equipo', 
                    values=titulo_lectura
                )
                
                # Resetear el indice para que Fecha sea una columna normal
                df_final = df_pivot.reset_index()

                # Desactivar el estilo de encabezado predeterminado de Pandas (evita negritas)
                from pandas.io.formats.excel import ExcelFormatter
                ExcelFormatter.header_style = None

                # Escribir a Excel manteniendo tipos de datos pero sin estilos de celda
                with pd.ExcelWriter(ruta, engine='openpyxl') as writer:
                    df_final.to_excel(writer, index=False)

            # 4. Notificar exito
            if os.path.exists(ruta):
                QMessageBox.information(None, "Exportacion", "Los datos se han exportado correctamente.")

        except Exception as e:
            print(f"Error en exportacion: {str(e)}")
            QMessageBox.critical(None, "Error", f"No se pudo realizar la exportacion: {str(e)}")