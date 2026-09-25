import io
import os
import csv
import math
import shutil
import zipfile
from openpyxl import Workbook
from openpyxl.styles import Alignment
from openpyxl.styles import Font
from datetime import datetime
from openpyxl.styles import Font, Alignment, Border, Side
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.drawing.image import Image as ExcelImage
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import Qt, QDateTime, QTime, Signal
from PySide6.QtWidgets import (QVBoxLayout, QPushButton, QDateTimeEdit, QDialog, QFileDialog,
    QLabel, QFrame, QWidget, QHBoxLayout, QCalendarWidget, QListWidget, QLineEdit)
from utils.common.alertas import mostrar_mensaje
from utils.common.rutasarchivos import resource_path
from utils.common.metodosGenerales import MetodosGenerales
from modules.empresa.softwareconfiguracion import SoftwareConfiguracion
from modules.empresa.empresaconfiguracion import EmpresaConfiguracion
from controllers.DatosController import DatosController

class TimeWheel(QListWidget):
    def __init__(self, limit, parent=None):
        super().__init__(parent)
        self.setFixedWidth(35)
        self.setFixedHeight(120)
        self.setUniformItemSizes(True)
        self.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        for i in range(limit):
            self.addItem(f"{i:02d}")
            self.item(i).setTextAlignment(Qt.AlignCenter)
        self.setStyleSheet("QListWidget { border: 1px solid #ddd; background: white; color: #333; font-size: 11px; } QListWidget::item:selected { background: #0078d7; color: white; }")

class DateTimePickerPopup(QDialog):
    def __init__(self, parent=None, initial_dt=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.main_frame = QFrame(self)
        self.main_frame.setStyleSheet("QFrame { background: white; border: 1px solid #ccc; border-radius: 6px; }")
        layout = QVBoxLayout(self.main_frame)
        layout.setContentsMargins(5, 5, 5, 5)
        
        body = QHBoxLayout()
        self.calendar = QCalendarWidget()
        self.calendar.setFixedSize(280, 210) 
        
        # --- ESTILO ULTRA-FINO DEL CALENDARIO ---
        self.calendar.setStyleSheet("""
            /* Barra de navegación */
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background-color: #ffffff;
                border-bottom: 1px solid #f2f2f2;
            }

            /* Botones generales de la barra superior */
            QCalendarWidget QToolButton {
                color: #333333;
                background-color: transparent;
                border: none;
                height: 25px;
            }

            /* --- SELECTOR DE MES (COMBO) --- */
            QCalendarWidget QToolButton#qt_calendar_monthbutton {
                font-size: 11px;
                font-weight: bold;
                padding-right: 12px; /* Espacio para nuestra flechita */
                padding-left: 5px;
                margin-right: 2px;
            }

            /* Personalización de la flechita del combo de meses */
            QCalendarWidget QToolButton#qt_calendar_monthbutton::menu-indicator {
                subcontrol-origin: padding;
                subcontrol-position: center right;
                right: 2px; /* Separación del borde derecho */
                top: 0px;   /* Ajuste vertical para alineación perfecta */
                width: 8px;  /* Flechita mucho más pequeña */
                height: 8px;
            }

            /* --- SELECTOR DE AÑO --- */
            QCalendarWidget QToolButton#qt_calendar_yearbutton {
                font-size: 11px;
                font-weight: bold;
                margin-left: 2px;
                padding: 0 5px;
            }

            /* Flechas laterales (Mes anterior/siguiente) */
            QCalendarWidget QToolButton#qt_calendar_prevmonth, 
            QCalendarWidget QToolButton#qt_calendar_nextmonth {
                width: 24px;
                border-radius: 12px;
                qproperty-iconSize: 14px;
            }
            
            QCalendarWidget QToolButton:hover {
                background-color: #f5f5f5;
                border-radius: 4px;
            }

            /* Menú desplegable de meses */
            QCalendarWidget QMenu {
                background-color: white;
                color: #333;
                selection-background-color: #0078d7;
                border: 1px solid #eeeeee;
            }

            /* Grilla de días y números */
            QCalendarWidget QWidget { alternate-background-color: #ffffff; }
            QCalendarWidget QAbstractItemView:enabled {
                color: #444;
                selection-background-color: #0078d7;
                font-size: 11px;
            }
            QCalendarWidget QAbstractItemView:disabled { color: #d0d0d0; }
        """)

        # Configuración de visibilidad
        self.calendar.setHorizontalHeaderFormat(QCalendarWidget.SingleLetterDayNames)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        
        if initial_dt and initial_dt.isValid(): 
            self.calendar.setSelectedDate(initial_dt.date())
        body.addWidget(self.calendar)

        # Lógica de las ruedas de tiempo (TimeWheel)
        time_lay = QHBoxLayout()
        self.h_w = TimeWheel(24); self.m_w = TimeWheel(60); self.s_w = TimeWheel(60)
        t = initial_dt.time() if initial_dt else QTime(0,0,0)
        self.h_w.setCurrentRow(t.hour()); self.m_w.setCurrentRow(t.minute()); self.s_w.setCurrentRow(t.second())
        
        for w, l in zip([self.h_w, self.m_w, self.s_w], ["H", "M", "S"]):
            v = QVBoxLayout(); lbl = QLabel(l); lbl.setAlignment(Qt.AlignCenter); lbl.setStyleSheet("font-size: 9px; color: #999; border:none;")
            v.addWidget(lbl); v.addWidget(w); time_lay.addLayout(v)
        
        body.addLayout(time_lay)
        layout.addLayout(body)
        
        self.btn_apply = QPushButton("Aplicar")
        self.btn_apply.setFixedSize(70, 26)
        self.btn_apply.setCursor(Qt.PointingHandCursor)
        self.btn_apply.setStyleSheet("""
            QPushButton { background: #0078d7; color: white; border-radius: 3px; font-size: 11px; font-weight: bold; }
            QPushButton:hover { background: #005fa3; }
        """)
        self.btn_apply.clicked.connect(self.accept)
        
        bottom_lay = QHBoxLayout(); bottom_lay.addStretch(); bottom_lay.addWidget(self.btn_apply)
        layout.addLayout(bottom_lay)
        QVBoxLayout(self).addWidget(self.main_frame)

    def get_selected_dt(self):
        return QDateTime(self.calendar.selectedDate(), QTime(self.h_w.currentRow(), self.m_w.currentRow(), self.s_w.currentRow()))
    
class CustomDateTimePicker(QWidget):
    dateTimeChanged = Signal()

    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self); layout.setContentsMargins(0,0,0,0); layout.setSpacing(0)
        
        self.line_edit = QLineEdit()
        self.line_edit.setInputMask("99/99/9999 99:99:99") # Formato visual para el usuario
        self.line_edit.setFixedHeight(26)
        self.line_edit.setStyleSheet("QLineEdit { border: 1px solid #ccc; border-radius: 3px 0 0 3px; padding-left: 5px; color: #333; font-size: 11px; }")
        self.line_edit.textChanged.connect(self._check_validity)

        self.btn = QPushButton("📅")
        self.btn.setFixedSize(26, 26)
        self.btn.setStyleSheet("background: #f8f8f8; border: 1px solid #ccc; border-left: none; border-radius: 0 3px 3px 0; color: #666;")
        self.btn.clicked.connect(self.open_picker)
        
        layout.addWidget(self.line_edit); layout.addWidget(self.btn)

    def _check_validity(self):
        if self.dateTime().isValid():
            self.dateTimeChanged.emit()

    def open_picker(self):
        dt = self.dateTime()
        if not dt.isValid(): dt = QDateTime.currentDateTime()
        pop = DateTimePickerPopup(self, dt)
        pos = self.mapToGlobal(self.line_edit.rect().bottomLeft())
        pop.move(pos.x(), pos.y() + 1)
        if pop.exec_():
            self.setDateTime(pop.get_selected_dt())
            self.dateTimeChanged.emit()

    def setDateTime(self, dt):
        if dt.isValid():
            self.line_edit.setText(dt.toString("dd/MM/yyyy HH:mm:ss"))

    def dateTime(self):
        # Siempre parsear desde el formato del input mask
        return QDateTime.fromString(self.line_edit.text(), "dd/MM/yyyy HH:mm:ss")

class ExportarData():
    
    @staticmethod
    def validarExportarDataEquipos(idproyecto, nameproyecto, idzona, tipo, equipos, fechainicial=None, fechafinal=None):
        formato = "yyyy-MM-dd HH:mm:ss"
        formato_sql = formato
        # Crear el diálogo principal
        dialogo = QDialog()
        dialogo.setWindowTitle(f"Exportar data {tipo}")
        dialogo.setMinimumWidth(500)
        dialogo.setStyleSheet("background-color: white;")
        main_layout = QVBoxLayout(dialogo)
        main_layout.setContentsMargins(15, 15, 15, 15)
        # --- Diferencia de días
        header = QHBoxLayout()
        labeldias = QLabel("0")
        labeldias.setStyleSheet("color: #0078d7; font-weight: bold; font-size: 14px;")
        header.addWidget(labeldias)
        header.addWidget(QLabel("días seleccionados"))
        header.addStretch()
        main_layout.addLayout(header)
        # --- Selectores de fecha
        form_layout = QHBoxLayout()
        # Inicio
        v1 = QVBoxLayout()
        v1.addWidget(QLabel("DESDE"))
        dt_inicio = CustomDateTimePicker()
        v1.addWidget(dt_inicio)
        # Fin
        v2 = QVBoxLayout()
        v2.addWidget(QLabel("HASTA"))
        dt_final = CustomDateTimePicker()
        v2.addWidget(dt_final)
        form_layout.addLayout(v1)
        form_layout.addSpacing(10)
        form_layout.addLayout(v2)
        main_layout.addLayout(form_layout)
        # --- Botones de acción ---
        btn_layout = QHBoxLayout()
        botoncancelar = QPushButton("Cancelar")
        botoncancelar.clicked.connect(dialogo.reject)
        botonexportar = QPushButton("EXPORTAR")
        botonexportar.setFixedHeight(30)
        botonexportar.setStyleSheet("""
            QPushButton {
                background: #0078d7; color: white; font-weight: bold;
                border-radius: 4px; padding: 0 15px;
            }
            QPushButton:disabled {
                background: #f0f0f0; color: #ccc;
            }
        """)
        # Botón adicional para CSV (solo para Prismas)
        botonexportarcsv = QPushButton("CSV")
        botonexportarcsv.setFixedHeight(30)
        botonexportarcsv.setStyleSheet(botonexportar.styleSheet())
        botonexportarcsv.setVisible(tipo == "Prismas")
        btn_layout.addStretch()
        btn_layout.addWidget(botoncancelar)
        btn_layout.addWidget(botonexportarcsv)
        btn_layout.addWidget(botonexportar)
        main_layout.addLayout(btn_layout)
        # habilitar exportar solo si diferencia > 0
        def validar():
            if tipo == "Inclinómetros" or tipo == "Pluviómetros" or tipo == "TDR" or tipo == "Cotas de Terreno":
                botonexportar.setEnabled(True)
            else:
                ini = dt_inicio.dateTime()
                fin = dt_final.dateTime()
                if ini.isValid() and fin.isValid():
                    labeldias.setText(str(ini.date().daysTo(fin.date())))
                    botonexportar.setEnabled(ini.secsTo(fin) >= 60)
                else:
                    botonexportar.setEnabled(False)

        # --- Funciones de exportación ---
        def exportarDataEquipo():
            time_inicio = dt_inicio.dateTime().toString(formato_sql)
            time_fin = dt_final.dateTime().toString(formato_sql)
            dialogo.accept()  # cerrar con éxito

            # Llamadas originales sin cambios
            if tipo == "Prismas":
                ExportarData.exportarExcelPrismas(idproyecto, nameproyecto, idzona, equipos, time_inicio, time_fin)
            elif tipo == "Inclinómetros":
                ExportarData.exportarZipInclinometros(idproyecto, nameproyecto, idzona, equipos)
            elif tipo == "Piezómetros Cuerda Vibrante":
                ExportarData.exportarExcelPiezometros("Automatizado", idproyecto, nameproyecto, idzona, equipos, time_inicio, time_fin)
            elif tipo == "Piezómetros Casagrande":
                ExportarData.exportarExcelPiezometros("Manual", idproyecto, nameproyecto, idzona, equipos, time_inicio, time_fin)
            elif tipo == "Pluviómetros":
                ExportarData.exportarExcelPluviometros(idproyecto, nameproyecto, idzona, equipos)
            elif tipo == "Cotas de Terreno":
                ExportarData.exportarExcelCotasTerreno(idproyecto, nameproyecto, idzona, equipos)
            elif tipo == "Celdas de Asentamiento":
                ExportarData.exportarExcelCeldasAsentamiento(idproyecto, nameproyecto, idzona, equipos, time_inicio, time_fin)
            elif tipo == "Acelerógrafos":
                ExportarData.exportarExcelAcelerografos(idproyecto, nameproyecto, idzona, equipos, time_inicio, time_fin)
            elif tipo == "TDR":
                ExportarData.exportarZipSondajesTDR(idproyecto, nameproyecto, idzona, equipos)

        def exportarDataEquiposCSV():
            time_inicio = dt_inicio.dateTime().toString(formato_sql)
            time_fin = dt_final.dateTime().toString(formato_sql)
            dialogo.accept()
            ExportarData.exportarExcelPrismasCSV(idproyecto, nameproyecto, idzona, equipos, time_inicio, time_fin)

        # Conectar señales
        dt_inicio.dateTimeChanged.connect(validar)
        dt_final.dateTimeChanged.connect(validar)
        botonexportar.clicked.connect(exportarDataEquipo)
        botonexportarcsv.clicked.connect(exportarDataEquiposCSV)

        # Cargar fechas iniciales
        def parsear_entrada(valor):
            if isinstance(valor, str):
                dt_parsed = QDateTime.fromString(valor, formato_sql)
                if not dt_parsed.isValid():
                    dt_parsed = QDateTime.fromString(valor, "dd/MM/yyyy HH:mm:ss")
                return dt_parsed
            elif isinstance(valor, datetime):
                return QDateTime(valor.year, valor.month, valor.day,
                                valor.hour, valor.minute, valor.second)
            return QDateTime()

        if fechainicial is not None:
            dt_ini = parsear_entrada(fechainicial)
            dt_fin = parsear_entrada(fechafinal)
            if dt_ini.isValid() and dt_fin.isValid():
                dt_inicio.setDateTime(dt_ini)
                dt_final.setDateTime(dt_fin)
            else:
                # Fallback a fecha/hora actual
                ahora = QDateTime.currentDateTime()
                dt_inicio.setDateTime(ahora)
                dt_final.setDateTime(ahora)
        else:
            ahora = QDateTime.currentDateTime()
            dt_inicio.setDateTime(ahora)
            dt_final.setDateTime(ahora)

        # Disparar validación inicial para actualizar el label y el botón
        validar()
        # Mostrar el diálogo (no necesitamos devolver valores, ya se procesa dentro)
        dialogo.exec()

    def exportarExcelPrismasCSV(proyectoid, proyectoname, idzona, prismasmarcados, fechaini, fechafin):
        encabezados = [
            'State', 'Point ID', 'Profile Name', 'Time', 'Hz', 'V', 'D [m]',
            'PPM Type', 'PPM', 'Pressure [mBar]', 'Av Temp [°C]', 'Add Const [m]',
            'Target Easting [m]', 'Target Northing [m]', 'Target Elevation [m]',
            'Reflector Height [m]', 'Instrument Height [m]', 'Station Easting [m]',
            'Station Northing [m]', 'Station Height [m]', 'Null Measurement [m]',
            'Short Time Diff [m]', 'Long Time Diff [m]', 'Vel Limit Diff [m]',
            'Horz Distance [m]', 'Difference Outlier Test [m]',
            'Longitudinal Displacement [m]',
            'Transverse Displacement [m]',
            'Height Displacement [m]', 'Point group'
        ]
        
        MAX_FILAS_POR_ARCHIVO = 1000000  # Máximo de filas por archivo CSV
        tabla = f"prismas{proyectoid}"
        nameprismas = [nameprisma for nameprisma, idinstrumento, tabla in prismasmarcados]
        # Obtener datos de la base de datos
        prismasdata = DatosController.ctrlObtenerDataExportarPrismas(tabla, nameprismas, fechaini, fechafin)
        if not prismasdata:
            return False
        
        total_filas = len(prismasdata)
        num_archivos = math.ceil(total_filas / MAX_FILAS_POR_ARCHIVO)
        # Permitir al usuario elegir la carpeta de destino
        carpeta_destino = QFileDialog.getExistingDirectory(
            None, 
            "Seleccionar carpeta para guardar archivos CSV",
            "",
            QFileDialog.ShowDirsOnly
        )
        
        if not carpeta_destino:
            return False
        
        try:
            archivos_creados = []
            for i in range(num_archivos):
                # Calcular rango de datos para este archivo
                inicio = i * MAX_FILAS_POR_ARCHIVO
                fin = min((i + 1) * MAX_FILAS_POR_ARCHIVO, total_filas)
                segmento = prismasdata[inicio:fin]
                
                # Generar nombre de archivo con sufijo numérico si hay múltiples archivos
                if num_archivos > 1:
                    nombre_archivo = f"datos_prismas_{idzona}_parte_{i+1}.csv"
                else:
                    nombre_archivo = f"datos_prismas_{idzona}.csv"
                
                # Crear ruta completa del archivo
                ruta_completa = os.path.join(carpeta_destino, nombre_archivo)
                
                # Escribir archivo CSV
                with open(ruta_completa, 'w', newline='', encoding='latin-1') as archivo_csv:
                    escritor = csv.writer(archivo_csv)
                    # Escribir encabezado en cada archivo
                    escritor.writerow(encabezados)
                    escritor.writerows(segmento)
                
                archivos_creados.append(ruta_completa)
            # Mostrar mensaje de éxito
            if num_archivos == 1:
                mensaje = f"Archivo CSV exportado exitosamente:\n{archivos_creados[0]}"
            else:
                mensaje = f"Se exportaron {num_archivos} archivos CSV en:\n{carpeta_destino}"
            
            mostrar_mensaje("Exportación exitosa", mensaje, "informacion")
            return True
            
        except Exception as e:
            return False
    
    def exportarExcelPrismas(proyectoid, proyectoname, idzona, prismasmarcados, fechaini, fechafin):
        config = SoftwareConfiguracion.obtenerDataSoftware()
        tipovelocidad = config[15]
        respuesta = EmpresaConfiguracion.obtenerDataEmpresa()
        logo = respuesta[4]
        libro = Workbook()
        cont = 0
        for nameprisma, idinstrumento, tabla in prismasmarcados:
            prismasdata = DatosController.ctrlObtenerPrismasDataExportar(proyectoid, tabla, idzona, nameprisma, tipovelocidad, fechaini, fechafin)
            if prismasdata:
                if cont == 0:
                    hoja = libro.active
                    hoja.title = nameprisma
                else:
                    hoja = libro.create_sheet(title=nameprisma)
                # La cabecera escribe los datos reales desde la fila 8
                ExportarData.configurarCabeceraHojaPrismas(
                    hoja, proyectoname, nameprisma, logo,
                    datos=[list(fila) for fila in prismasdata]
                )
                cont += 1
        rutaexcel = resource_path("resources/workspace/dataequipos.xlsx")
        libro.save(rutaexcel)
        archivo_destino, _ = QFileDialog.getSaveFileName(None, "Guardar Excel en", "Prismas", "Archivos de Excel (*.xlsx);;Todos los archivos (*)")
        if archivo_destino:
            # Asegurarse de que el archivo tenga la extensión .xlsx
            if not archivo_destino.lower().endswith('.xlsx'):
                archivo_destino += '.xlsx'
            try:
                shutil.copy(rutaexcel, archivo_destino)
                mostrar_mensaje("Data Exportada", f"El Excel se ha guardado en: {archivo_destino}", "informacion")
            except Exception as e:  # Captura cualquier excepción
                mostrar_mensaje("Error al Exportar", f"No se pudo guardar el Excel: {str(e)}", "advertencia")
    def _num(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return v  # si viene como 2° 55' 53'' se deja como texto
    def _aplicar_borde(hoja, rango, borde):
        """Aplica un borde tanto a rangos combinados (ej. 'A8:B8') como a celdas sueltas (ej. 'A8')."""
        if ":" in rango:
            for fila_celdas in hoja[rango]:
                for celda in fila_celdas:
                    celda.border = borde
        else:
            hoja[rango].border = borde
    
    def configurarCabeceraHojaPrismas(hoja, proyectoname, nameprisma, logo, datos=None):
        from openpyxl.styles import PatternFill, Border, Side, Font, Alignment

        config = SoftwareConfiguracion.obtenerDataSoftware()
        decimales = config[14] or 2

        # ---- Estilos comunes ----
        color_fondo = PatternFill(start_color="000000", end_color="000000", fill_type="solid")
        lado = Side(style="thin", color="000000")
        borde_negro = Border(left=lado, right=lado, top=lado, bottom=lado)
        fuente_blanca = Font(size=11, bold=True, color="FFFFFF")
        centro = Alignment(horizontal="center", vertical="center", wrap_text=True)
        lado_blanco = Side(style="thin", color="FFFFFF")
        borde_blanco = Border(left=lado_blanco, right=lado_blanco, top=lado_blanco, bottom=lado_blanco)

        # ---- Ancho de columnas (A hasta M) ----
        anchos = {
            "A": 20, "B": 14, "C": 14, "D": 16, "E": 16, "F": 18,
            "G": 22, "H": 18, "I": 18, "J": 14, "K": 14, "L": 14, "M": 14,
        }
        for letra, ancho in anchos.items():
            hoja.column_dimensions[letra].width = ancho

        # ---- Alto de filas ----
        for row in range(1, 5):
            hoja.row_dimensions[row].height = 25
        hoja.row_dimensions[5].height = 10
        hoja.row_dimensions[6].height = 22
        hoja.row_dimensions[7].height = 20

        # ---- LOGO (A1:A4) ----
        if logo:
            imagen_stream = MetodosGenerales.convertirBlobImagen(logo)
            imagen = ExcelImage(imagen_stream)
        else:
            ui_file_path = resource_path("resources/logo.png")
            imagen = ExcelImage(ui_file_path)
        imagen.width = 132
        imagen.height = 132
        imagen.anchor = "A1"
        hoja.merge_cells("A1:A4")
        hoja.add_image(imagen)

        # ---- TÍTULO (B1:M2) ----
        hoja.merge_cells("B1:M2")
        celda_titulo = hoja["B1"]
        celda_titulo.value = f"DATOS PRISMAS - {proyectoname.upper()}"
        celda_titulo.font = Font(size=16, bold=True)
        celda_titulo.alignment = centro

        # ---- NOTAS (B3:M3 y B4:M4) ----
        hoja.merge_cells("B3:M3")
        nota1 = hoja["B3"]
        nota1.value = ("* Los datos no debe contener fórmulas y el Formato de fecha: "
                        "día/mes/año completo (15/01/2020). El formato de hora: hh:mm:ss")
        nota1.font = Font(size=9, bold=True)
        # nota1.alignment = centro

        hoja.merge_cells("B4:M4")
        nota2 = hoja["B4"]
        nota2.value = ("* Las coordenadas son obligatorias, los otros datos puede ir con ceros (0). "
                        "Si se tienen ángulos es preferible ingresar solo numéricos: "
                        "(2° 55' 53'') o (2.931).")
        nota2.font = Font(size=9, bold=True)
        # nota2.alignment = centro

        # ---- Bordes del bloque superior ----
        for rango in ["A1:A4", "B1:M2", "B3:M3", "B4:M4"]:
            for fila_celdas in hoja[rango]:
                for celda in fila_celdas:
                    celda.border = borde_negro

        # ---- CABECERAS DE GRUPO (fila 6) ----
        cabeceras = [
            ("A6:I6", "Datos de Monitoreo"),
            ("J6:K6", "Desplazamiento (cm)"),
            ("L6:M6", "Velocidad (cm/día)"),
        ]
        for rango, texto in cabeceras:
            hoja.merge_cells(rango)
            celda = hoja[rango.split(":")[0]]
            celda.value = texto
            celda.font = Font(size=12, bold=True, color="FFFFFF")
            celda.alignment = Alignment(horizontal="center", vertical="center")
            for fila_celdas in hoja[rango]:
                for c in fila_celdas:
                    c.fill = color_fondo
                    c.border = borde_blanco

        # ---- ENCABEZADOS DETALLADOS (fila 7) ----
        encabezados = [
            "Hito", "Fecha", "Hora", "Este (m)", "Norte (m)", "Elevación (msnm)",
            "Distancia Inclinada (m)", "Ángulo Horizontal", "Ángulo Vertical",
            "Incremental", "Acumulado", "Incremental", "Acumulado",
        ]
        for col, encabezado in enumerate(encabezados, 1):
            celda = hoja.cell(row=7, column=col, value=encabezado)
            celda.font = fuente_blanca
            celda.alignment = centro
            celda.fill = color_fondo
            celda.border = borde_blanco

        # Determinar qué filas escribir
        if datos and len(datos) > 0:  # ← Verificación más robusta
            filas = datos
        else:
            filas = [
                ["HITO1", "01/12/2020", "00:00:00"] + [0] * 10,
                ["HITO1", "15/12/2020", "00:00:00"] + [0] * 10,
            ]

        # Columnas numéricas: 4=Este, 5=Norte, 6=Elevación, 7=Distancia,
        # 8=Ángulo H, 9=Ángulo V, 10-13=Desplazamiento/Velocidad (Incremental/Acumulado)
        COLUMNAS_NUMERICAS = set(range(4, 14))

        alineacion_datos = Alignment(horizontal="center", vertical="center")
        for i, fila in enumerate(filas, start=8):
            for col, valor in enumerate(fila, 1):
                if col in COLUMNAS_NUMERICAS:
                    valor_num = ExportarData._num(valor)
                    if isinstance(valor_num, (int, float)):
                        valor = round(valor_num, decimales)
                    # si no se pudo convertir (p.ej. ángulo en texto tipo 2° 55' 53''),
                    # se deja el valor original sin tocar
                celda = hoja.cell(row=i, column=col, value=valor)
                celda.alignment = alineacion_datos
                celda.border = borde_negro


    def exportarZipInclinometros(idproyecto, nameproyecto, idzona, inclinometrosmarcados):
        zip_filename = resource_path("resources/workspace/zipequipos.zip")
        try:
            with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for nombreincli, idinstrumento, idinclino in inclinometrosmarcados:
                    infoinclino = DatosController.ctrlObtenerInfoExportarInclinometro(idzona, "INCLINOMETRO", idinstrumento)
                    if infoinclino:
                        for info in infoinclino:
                            idencabezado, tipoequipo = info[0], info[4]
                            dataencabeza = DatosController.ctrlObtenerDataExportarInclinometro(idproyecto, idencabezado)
                            if dataencabeza:
                                if tipoequipo == "RST":
                                    csv_file = io.StringIO()
                                    writer = csv.writer(csv_file)
                                    ExportarData.generarEncabezadoCSVInclinometro(writer, info, nameproyecto)
                                    for datafila in dataencabeza:
                                        writer.writerow(datafila)
                                    csv_content = csv_file.getvalue()
                                    csv_file.close()
                                    # Nombre del archivo CSV dentro del ZIP
                                    csv_name = f"{info[2]}_{info[5]}.csv".replace("/", "_").replace(":", "_")
                                    zipf.writestr(csv_name, csv_content)
                                else:
                                    gkn_file = io.StringIO()
                                    writer = csv.writer(gkn_file)
                                    ExportarData.generarEncabezadoGKNInclinometro(writer, info, nameproyecto)
                                    for datafila in dataencabeza:
                                        writer.writerow(datafila)
                                    gkn_content = gkn_file.getvalue()
                                    gkn_file.close()
                                    # Nombre del archivo con extensión .gkn
                                    gkn_name = f"{info[2]}_{info[5]}.gkn".replace("/", "_").replace(":", "_")
                                    zipf.writestr(gkn_name, gkn_content)
            # Guardar el archivo ZIP en una ubicación elegida por el usuario
            archivo_destino, _ = QFileDialog.getSaveFileName(
                None, "Guardar ZIP en", "Inclinometros", "Archivos ZIP (*.zip);;Todos los archivos (*)"
            )
            if archivo_destino:
                if not archivo_destino.lower().endswith('.zip'):
                    archivo_destino += '.zip'
                shutil.copy(zip_filename, archivo_destino)
                mostrar_mensaje("Data Exportada", f"El ZIP se ha guardado en: {archivo_destino}", "informacion")
        except Exception as e:
            mostrar_mensaje("Error al Exportar", f"No se pudo guardar el ZIP: {str(e)}", "advertencia")
    
    def generarEncabezadoCSVInclinometro(writer, infoinclino, nombreproyecto):
        writer.writerow(["RST Digital Inclinometer Data"])
        writer.writerow(["File Version", ""])
        writer.writerow(["File Type", "Digital Inclinometer"])
        writer.writerow(["Site", nombreproyecto])
        writer.writerow(["Zone", infoinclino[1]])
        writer.writerow(["Borehole", infoinclino[2]])
        writer.writerow(["Probe Serial", infoinclino[3]])

        valor_fecha = infoinclino[5]
        if isinstance(valor_fecha, datetime):
            fecha_obj = valor_fecha
            hora = valor_fecha.strftime("%H:%M:%S")
        else:
            fechaorig, hora = str(valor_fecha).split(" ")
            fecha_obj = datetime.strptime(fechaorig, "%Y-%m-%d")
        fecha = fecha_obj.strftime("%m/%d/%Y")

        writer.writerow(["Reading Date(m/d/y)", fecha, hora])
        writer.writerow(["Depth", infoinclino[6]])
        writer.writerow(["Interval", "0.5"])
        writer.writerow(["Depth Units", "m"])
        writer.writerow(["Reading Units", ""])
        writer.writerow(["Offset Correction", ""])
        writer.writerow(["East", infoinclino[7]])
        writer.writerow(["North", infoinclino[8]])
        writer.writerow(["Level", infoinclino[9]])
        writer.writerow([])
        writer.writerow(["Depth", "Face A+", "Face A-", "Face B+", "Face B-"])
        writer.writerow([])
    
    def generarEncabezadoGKNInclinometro(writer, infoinclino, nombreproyecto):
        writer.writerow(["GEOKON Inclinometer Data"])
        writer.writerow(["GKN FORMAT", ""])
        writer.writerow([f"PROJECT  :{nombreproyecto}"])
        writer.writerow([f"ZONE     :{infoinclino[1]}"])
        writer.writerow([f"HOLE NO. :{infoinclino[2]}"])

        valor_fecha = infoinclino[5]
        if isinstance(valor_fecha, datetime):
            fecha_obj = valor_fecha
            hora = valor_fecha.strftime("%H:%M:%S")
        else:
            fechaorig, hora = str(valor_fecha).split(" ")
            fecha_obj = datetime.strptime(fechaorig, "%Y-%m-%d")
        fecha = fecha_obj.strftime("%m/%d/%y")

        writer.writerow([f"DATE     :{fecha}"])
        writer.writerow([f"TIME     :{hora}"])
        writer.writerow([f"PROBE NO.:{infoinclino[3]}"])
        writer.writerow([f"COORD.   :({infoinclino[7]}, {infoinclino[8]}, {infoinclino[9]})"])
        writer.writerow([f"#READINGS:"])
        writer.writerow(["FLEVEL", "A+", "A-", "B+", "B-"])

    def exportarExcelPiezometros(tipo, idproyecto, nameproyecto, idzona, piezometrosmarcados, fechaini, fechafin):
        respuesta = EmpresaConfiguracion.obtenerDataEmpresa()
        logo = respuesta[4]
        libro = Workbook()
        cont = 0
        for namepiezo, idinstrumento, idpiezo in piezometrosmarcados:
            if tipo == "Automatizado":
                tipoequipo = "PIEZOMETROCUERDA"
            else:
                tipoequipo = "PIEZOMETROMANUAL"
            infopiezo = DatosController.ctrlTraerInfoPiezometro(tipo, idzona, tipoequipo, idinstrumento)
            datospiezo = DatosController.ctrlListarDataPiezometrosProyecto(tipo, idproyecto, idzona, idinstrumento, fechaini, fechafin)
            if infopiezo and datospiezo:
                if cont == 0:
                    hoja = libro.active
                    hoja.title = namepiezo
                else:
                    hoja = libro.create_sheet(title=namepiezo)
                # Configurar la hoja (común para todas)
                if tipo == "Automatizado":
                    ExportarData.configurarCabeceraHojaPiezometroCuerda(hoja, infopiezo, nameproyecto, namepiezo, logo, datospiezo[0])
                else:
                    ExportarData.configurarCabeceraHojaPiezometroManual(hoja, infopiezo, nameproyecto, namepiezo, logo, datospiezo[0])
                # Insertar datos en la tabla
                for fila in datospiezo:
                    if tipo == "Manual":
                        fecha, hora, nivpiezo, profundidad, elevacion, cotapiezo, nivelvertical, observacion = fila
                        filaordenada = [fecha, hora, nivpiezo, observacion, profundidad, elevacion, cotapiezo, nivelvertical]
                        hoja.append(filaordenada)
                    else:
                        fecha, hora, frecuencia, temperatura, presion, mca, cotapiezo, observacion, elevacion = fila
                        filaordenada = [fecha, hora, frecuencia, temperatura, presion, mca, observacion, cotapiezo, elevacion]
                        hoja.append(filaordenada)
                cont += 1
        rutaexcel = resource_path("resources/workspace/dataequipos.xlsx")
        libro.save(rutaexcel)
        archivo_destino, _ = QFileDialog.getSaveFileName(None, "Guardar Excel en", "Piezometros", "Archivos de Excel (*.xlsx);;Todos los archivos (*)")
        if archivo_destino:
            if not archivo_destino.lower().endswith('.xlsx'):
                archivo_destino += '.xlsx'
            try:
                shutil.copy(rutaexcel, archivo_destino)
                mostrar_mensaje("Data Exportada", f"El Excel se ha guardado en: {archivo_destino}", "informacion")
            except Exception as e:
                mostrar_mensaje("Error al Exportar", f"No se pudo guardar el Excel: {str(e)}", "advertencia")
    
    def configurarCabeceraHojaPiezometroCuerda(hoja, infopiezo, proyectoname, namepiezo, logo, primerregistro=None):
        from openpyxl.styles import PatternFill, Border, Side, Font, Alignment

        color_fondo = PatternFill(start_color="000000", end_color="000000", fill_type="solid")
        borde_negro = Border(
            left=Side(style="thin", color="000000"),
            right=Side(style="thin", color="000000"),
            top=Side(style="thin", color="000000"),
            bottom=Side(style="thin", color="000000"),
        )
        borde_blanco = Border(
            left=Side(style="thin", color="FFFFFF"),
            right=Side(style="thin", color="FFFFFF"),
            top=Side(style="thin", color="FFFFFF"),
            bottom=Side(style="thin", color="FFFFFF"),
        )
        # Ancho de columnas
        for col in range(1, 10):
            hoja.column_dimensions[chr(64 + col)].width = 20
        for row in range(1, 5):
            hoja.row_dimensions[row].height = 25
        # Logo
        if logo:
            imagen_stream = MetodosGenerales.convertirBlobImagen(logo)
            imagen = ExcelImage(imagen_stream)
        else:
            ui_file_path = resource_path("resources/logo.png")
            imagen = ExcelImage(ui_file_path)
        imagen.width = 132
        imagen.height = 132
        imagen.anchor = "A1"
        hoja.merge_cells("A1:A4")
        hoja.add_image(imagen)

        # Título
        hoja.merge_cells("B1:I2")
        celda_titulo = hoja["B1"]
        celda_titulo.value = "FORMATO DE DATOS - PIEZÓMETROS CUERDA VIBRANTE"
        celda_titulo.font = Font(size=16, bold=True)
        celda_titulo.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        # Notas
        hoja.merge_cells("B3:I3")
        nota1 = hoja["B3"]
        nota1.value = "* Los datos no debe contener fórmulas y el Formato de fecha: día/mes/año completo (15/01/2020)."
        nota1.font = Font(size=9, bold=True)

        hoja.merge_cells("B4:I4")
        nota2 = hoja["B4"]
        nota2.value = "* El formato de hora: hh:mm:ss"
        nota2.font = Font(size=9, bold=True)

        # Cabeceras de bloque (fila 6-7)
        cabeceraGeneral = [("A6:B7", "DATOS DEL SENSOR"), ("C6:E7", "DATOS DE INSTALACIÓN"), ("F6:I7", "DATOS DE CALIBRACIÓN")]
        for rango, texto in cabeceraGeneral:
            hoja.merge_cells(rango)
            celda = hoja[rango.split(":")[0]]
            celda.value = texto
            celda.font = Font(size=14, bold=True, color="FFFFFF")
            celda.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            celda.fill = color_fondo

        def val(idx, default=0):
            return infopiezo[idx] if len(infopiezo) > idx else default

        # --- Bloque SENSOR (A:B, filas 8-13) ---
        datosceldas = [
            ("A8", "Nombre:"), ("A9", "Serie:"), ("A10", "Coordenada Este:"),
            ("A11", "Coordenada Norte:"), ("A12", "Cota Instalación (m.s.n.m):"), ("A13", "Cota Fundación (m.s.n.m):"),
        ]
        valoressensor = [
            ("B8", namepiezo), ("B9", val(4)), ("B10", val(9)),
            ("B11", val(10)), ("B12", val(11)), ("B13", val(12)),
        ]

        # --- Bloque INSTALACIÓN ---
        datosinstalacion = [
            ("C8:D8", "Cota de Superficie Actual (m.s.n.m):"), ("C9:D9", "Inclinación:"),
            ("C10:D10", "Azimuth:"), ("C11:D11", "C.F.:"), ("C12:D12", "T.K.:"), ("C13:D13", "Frecuencia Inicial (Dg):"),
        ]
        cota_superficie_actual = primerregistro[8] if primerregistro is not None and len(primerregistro) > 8 else 0
        valoresinstalacion = [
            ("E8", cota_superficie_actual),
            ("E9", val(5)), ("E10", val(6)), ("E11", val(7)), ("E12", val(8)),
            ("E13", val(16, 0)),
        ]

        # --- Bloque CALIBRACIÓN ---
        # Etiquetas: solo columna F (sin combinar)
        datoscalibracion = [
            ("F8", "Temperatura Inicial (°C):"), ("F9", "Presión Inicial:"), ("F10", "Factor de Conversión:"),
            ("F11", "Constante A:"), ("F12", "Constante B:"), ("F13", "Constante C:"),
        ]
        # Valores: combinados en G:I
        valorescalibracion = [
            ("G8:I8", val(26, 0)), ("G9:I9", val(27, 0)), ("G10:I10", val(28, 0)),
            ("G11:I11", val(29, 0)), ("G12:I12", val(30, 0)), ("G13:I13", val(31, 0)),
        ]

        # Escribir labels (fondo negro, texto blanco)
        for rango, texto in datosceldas:
            celda = hoja[rango]
            celda.value = texto
            celda.font = Font(bold=True, color="FFFFFF")
            celda.fill = color_fondo

        # Escribir valores del bloque SENSOR (fondo BLANCO)
        for rango, texto in valoressensor:
            celda = hoja[rango]
            celda.value = texto
            celda.alignment = Alignment(horizontal="center", vertical="center")

        # Escribir labels de INSTALACIÓN y CALIBRACIÓN (fondo negro)
        for rango, texto in datosinstalacion + datoscalibracion:
            if ":" in rango:
                hoja.merge_cells(rango)
            celda = hoja[rango.split(":")[0]]
            celda.value = texto
            celda.font = Font(bold=True, color="FFFFFF")
            celda.fill = color_fondo

        # Escribir valores INSTALACIÓN y CALIBRACIÓN (fondo BLANCO)
        for rango, texto in valoresinstalacion + valorescalibracion:
            if ":" in rango:
                hoja.merge_cells(rango)
            celda = hoja[rango.split(":")[0]]
            celda.value = texto
            celda.alignment = Alignment(horizontal="center", vertical="center")

        # --- Bordes NEGROS: bloque superior (logo, título, notas) y celdas de VALORES (fondo blanco) ---
        rangosceldas_negro = ["A1:A4", "B1:I2", "B3:I3", "B4:I4", "B8:B13", "E8:E13", "G8:I13"]
        for rango in rangosceldas_negro:
            for fila_celdas in hoja[rango]:
                for celda in fila_celdas:
                    celda.border = borde_negro

        # --- Bordes BLANCOS: cabeceras de bloque y celdas de LABELS (fondo negro) ---
        rangosceldas_blanco = ["A6:B7", "C6:E7", "F6:I7", "A8:A13", "C8:D13", "F8:F13"]
        for rango in rangosceldas_blanco:
            for fila_celdas in hoja[rango]:
                for celda in fila_celdas:
                    celda.border = borde_blanco

        # Fila de encabezados detallados -> fila 14 (fondo negro, texto blanco, borde blanco)
        encabezados = ["Fecha", "Hora", f"Frecuencia ({val(16, '')})", "Temperatura (°C)", "Presión (kPa)",
                    "mca (m)", "Observación", "Cota Piezométrica", "Cota Superficie"]
        for col, encabezado in enumerate(encabezados, 1):
            celda = hoja.cell(row=14, column=col, value=encabezado)
            celda.font = Font(bold=True, color="FFFFFF")
            celda.alignment = Alignment(horizontal="center", vertical="center")
            celda.fill = color_fondo
            celda.border = borde_blanco

    def configurarCabeceraHojaPiezometroManual(hoja, infopiezo, proyectoname, namepiezo, logo, primerregistro=None):
        # Definir colores, bordes, y otros atributos comunes
        color_fondo = PatternFill(start_color="000000", end_color="000000", fill_type="solid")
        borde_negro = Border(
            left=Side(style="thin", color="000000"),
            right=Side(style="thin", color="000000"),
            top=Side(style="thin", color="000000"),
            bottom=Side(style="thin", color="000000"),
        )
        borde_blanco = Border(
            left=Side(style="thin", color="FFFFFF"),
            right=Side(style="thin", color="FFFFFF"),
            top=Side(style="thin", color="FFFFFF"),
            bottom=Side(style="thin", color="FFFFFF"),
        )
        # Ajustar el ancho de las columnas para mejor presentación (ahora A-H, 8 columnas)
        for col in range(1, 9):
            hoja.column_dimensions[chr(64 + col)].width = 22
        # Ajustar el alto de las filas de 1 a 4 para el área de la imagen
        for row in range(1, 5):
            hoja.row_dimensions[row].height = 25
        # Ruta de la imagen
        if logo:
            imagen_stream = MetodosGenerales.convertirBlobImagen(logo)
            imagen = ExcelImage(imagen_stream)
        else:
            ui_file_path = resource_path("resources/logo.png")
            imagen = ExcelImage(ui_file_path)
        imagen.width = 132
        imagen.height = 132
        imagen.anchor = "A1"
        hoja.merge_cells("A1:A4")
        hoja.add_image(imagen)

        # Agregar el título
        hoja.merge_cells("B1:H4")          # antes: B1:D4
        celda_titulo = hoja["B1"]
        celda_titulo.value = f"MONITOREO DE PIEZÓMETROS CASAGRANDE - {proyectoname.upper()}"
        celda_titulo.font = Font(size=18, bold=True)
        celda_titulo.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        # Notas — combinadas en toda la fila (A:H)
        hoja.merge_cells("A5:H5")          # antes: A5:D5
        nota1 = hoja["A5"]
        nota1.value = "* Los datos no debe contener fórmulas y el Formato de fecha: día/mes/año completo"
        nota1.font = Font(size=9, bold=True)

        hoja.merge_cells("A6:H6")          # antes: A6:D6
        nota2 = hoja["A6"]
        nota2.value = "* El formato de hora: hh:mm:ss"
        nota2.font = Font(size=9, bold=True)

        # Fila 7 — combinada como separador (vacía)
        hoja.merge_cells("A7:H7")          # antes: A7:D7

        # Encabezado "DATOS DEL EQUIPO" (bloque único, filas 8-9)
        hoja.merge_cells("A8:H9")          # antes: A8:D9
        celda_bloque = hoja["A8"]
        celda_bloque.value = "DATOS DEL EQUIPO"
        celda_bloque.font = Font(size=14, bold=True, color="FFFFFF")
        celda_bloque.alignment = Alignment(horizontal="center", vertical="center")
        celda_bloque.fill = color_fondo

        cota_superficie_actual = primerregistro[4] if primerregistro is not None and len(primerregistro) > 4 else 0

        campos = [
            ("Nombre:", namepiezo),
            ("Código:", infopiezo[3]),
            ("Cota Fondo Pozo (m.s.n.m):", infopiezo[6]),
            ("Cota Fundación (m.s.n.m):", infopiezo[7]),
            ("Coordenada Este (m):", infopiezo[4]),
            ("Coordenada Norte (m):", infopiezo[5]),
            ("Cota de Superficie Actual (m.s.n.m):", cota_superficie_actual),
            ("Inclinación:", infopiezo[8]),
            ("Azimuth:", infopiezo[9]),
            ("Stick Up (m):", infopiezo[10]),
            ("Comentario:", infopiezo[11]),
        ]
        fila_inicio = 10
        for i, (etiqueta, valor) in enumerate(campos):
            fila = fila_inicio + i
            hoja.merge_cells(f"A{fila}:B{fila}")
            celda_lbl = hoja[f"A{fila}"]
            celda_lbl.value = etiqueta
            celda_lbl.font = Font(bold=True, color="FFFFFF")
            celda_lbl.fill = color_fondo
            celda_lbl.alignment = Alignment(horizontal="center", vertical="center")

            # Valor combinado en C:D:E:F:G:H
            hoja.merge_cells(f"C{fila}:H{fila}")
            celda_val = hoja[f"C{fila}"]
            celda_val.value = valor
            celda_val.alignment = Alignment(horizontal="center", vertical="center")

        # Bordes
        fila_fin_datos = fila_inicio + len(campos) - 1  # fila 20
        # --- Bordes NEGROS...
        rangosceldas_negro = ["A1:A4", "B1:H4", "A5:H5", "A6:H6", "A7:H7"] + \
            [f"C{f}:H{f}" for f in range(fila_inicio, fila_fin_datos + 1)]

        # --- Bordes BLANCOS...
        rangosceldas_blanco = ["A8:H9"] + \
            [f"A{f}:B{f}" for f in range(fila_inicio, fila_fin_datos + 1)]

        for rango in rangosceldas_negro:
            for fila_celdas in hoja[rango]:
                for celda in fila_celdas:
                    celda.border = borde_negro
        for rango in rangosceldas_blanco:
            for fila_celdas in hoja[rango]:
                for celda in fila_celdas:
                    celda.border = borde_blanco

        # Fila de encabezados detallados (justo después del bloque, sin espacio)
        fila_headers = fila_fin_datos + 1
        encabezados = ["Fecha", "Hora", "Nivel Piezométrico (m)", "Observación",
                    "Profundidad (m)", "Elevación (m.s.n.m)", "Cota Piezométrica", "Nivel Vertical (m)"]
        for col, encabezado in enumerate(encabezados, 1):
            celda = hoja.cell(row=fila_headers, column=col, value=encabezado)
            celda.font = Font(bold=True, color="FFFFFF")
            celda.alignment = Alignment(horizontal="center", vertical="center")
            celda.fill = color_fondo
            celda.border = borde_blanco

    def exportarExcelPluviometros(idproyecto, nameproyecto, idzona, pluviometrosmarcados):
        respuesta = EmpresaConfiguracion.obtenerDataEmpresa()
        logo = respuesta[4]
        libro = Workbook()
        cont = 0
        for namepluvio, idinstrumento, idpluvio in pluviometrosmarcados:
            infopluvio = DatosController.ctrlTraerInfoPluviometro(idzona, "PLUVIOMETRO", idinstrumento)
            datospluvio = DatosController.ctrlListarDataPluviometro(idproyecto, idzona, idinstrumento)
            if infopluvio and datospluvio:
                if cont == 0:
                    hoja = libro.active
                    hoja.title = namepluvio
                else:
                    hoja = libro.create_sheet(title=namepluvio)
                # Configurar la hoja (común para todas)
                ExportarData.configurarCabeceraHojaPluviometro(hoja, infopluvio, nameproyecto, namepluvio, logo)
                # Insertar datos en la tabla comenzando desde la fila 19
                for fila in datospluvio:
                    hoja.append(list(fila))
                cont += 1
        rutaexcel = resource_path("resources/workspace/dataequipos.xlsx")
        libro.save(rutaexcel)
        archivo_destino, _ = QFileDialog.getSaveFileName(None, "Guardar Excel en", "Pluviometros", "Archivos de Excel (*.xlsx);;Todos los archivos (*)")
        if archivo_destino:
            # Asegurarse de que el archivo tenga la extensión .xlsx
            if not archivo_destino.lower().endswith('.xlsx'):
                archivo_destino += '.xlsx'
            try:
                shutil.copy(rutaexcel, archivo_destino)
                mostrar_mensaje("Data Exportada", f"El Excel se ha guardado en: {archivo_destino}", "informacion")
            except Exception as e:  # Captura cualquier excepción
                mostrar_mensaje("Error al Exportar", f"No se pudo guardar el Excel: {str(e)}", "advertencia")
    
    def configurarCabeceraHojaPluviometro(hoja, infopluvio, proyectoname, namepluvio, logo):
        # Definir colores, bordes, y otros atributos comunes
        color_fondo = PatternFill(start_color="000000", end_color="000000", fill_type="solid")
        borde_negro = Border(
            left=Side(style="thin", color="000000"),
            right=Side(style="thin", color="000000"),
            top=Side(style="thin", color="000000"),
            bottom=Side(style="thin", color="000000"),
        )
        borde_blanco = Border(
            left=Side(style="thin", color="FFFFFF"),
            right=Side(style="thin", color="FFFFFF"),
            top=Side(style="thin", color="FFFFFF"),
            bottom=Side(style="thin", color="FFFFFF"),
        )
        # Ajustar el ancho de las columnas para mejor presentación
        for col in range(1, 5):  # 4 columnas de ancho
            hoja.column_dimensions[chr(64 + col)].width = 20
        # Ajustar el alto de las filas de 1 a 5 para el área de la imagen
        for row in range(1, 5):
            hoja.row_dimensions[row].height = 25
        # Ruta de la imagen
        if logo:
            imagen_stream = MetodosGenerales.convertirBlobImagen(logo)
            imagen = ExcelImage(imagen_stream)
        else:
            ui_file_path = resource_path("resources/logo.png")
            imagen = ExcelImage(ui_file_path)
        imagen.width = 132
        imagen.height = 132
        imagen.anchor = "A1"
        hoja.merge_cells("A1:A4")
        hoja.add_image(imagen)
        # Agregar el título
        hoja.merge_cells("B1:D4")
        celda_titulo = hoja["B1"]
        celda_titulo.value = f"MONITOREO DE PLUVIÓMETROS - {proyectoname.upper()}"
        celda_titulo.font = Font(size=18, bold=True)
        celda_titulo.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        # Notas (fila 5 y 6)
        hoja.merge_cells("A5:D5")
        nota1 = hoja["A5"]
        nota1.value = "* Los datos no debe contener fórmulas y el Formato de fecha: día/mes/año completo."
        nota1.font = Font(size=9, bold=True)

        hoja.merge_cells("A6:D6")
        nota2 = hoja["A6"]
        nota2.value = "* El formato de hora: hh:mm:ss"
        nota2.font = Font(size=9, bold=True)

        # Agregar el subtítulo (ahora en fila 8-9, tras las notas)
        rango, texto = "A8:D9", "DATOS DEL EQUIPO"
        hoja.merge_cells(rango)
        celda = hoja[rango.split(":")[0]]
        celda.value = texto
        celda.font = Font(size=14, bold=True, color="FFFFFF")
        celda.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        celda.fill = color_fondo

        # Definir datos generales (corridos 2 filas: 10, 11, 12)
        datosceldas = [("A10", "Nombre:"), ("A11", "Código:"), ("A12", "Este:"),
                    ("C10", "Norte:"), ("C11", "Elevación:"), ("C12", "Comentario:")]
        datoscombinados = [("B10", namepluvio), ("B11", infopluvio[3]), ("B12", infopluvio[4]),
                        ("D10", infopluvio[5]), ("D11", infopluvio[6]), ("D12", infopluvio[7])]
        for rango, texto in datosceldas:
            celda = hoja[rango]
            celda.value = texto
            celda.border = borde_blanco
            celda.alignment = Alignment(horizontal="center", vertical="center")
            celda.font = Font(bold=True, color="FFFFFF")
            celda.fill = color_fondo
        for rango, texto in datoscombinados:
            hoja.merge_cells(rango)
            celda = hoja[rango.split(":")[0]]
            celda.value = texto
            celda.border = borde_negro
            celda.alignment = Alignment(horizontal="left")

        # Bordes de bloques con fondo blanco (logo, título, notas)
        for rango in ["A1:D4", "A5:D5", "A6:D6"]:
            for fila_celdas in hoja[rango]:
                for celda in fila_celdas:
                    celda.border = borde_negro
        # Bordes de bloques con fondo negro
        for rango in ["A8:D9"]:
            for fila_celdas in hoja[rango]:
                for celda in fila_celdas:
                    celda.border = borde_blanco

        # Fila de encabezados detallados, pegada justo debajo de "Datos del equipo" (fila 13)
        fila_headers = 13
        encabezados = ["Fecha", "Hora", "Precipitación (mm)", "Observación"]
        for col, encabezado in enumerate(encabezados, 1):
            celda = hoja[chr(64 + col) + str(fila_headers)]
            celda.value = encabezado
            celda.font = Font(bold=True, color="FFFFFF")
            celda.alignment = Alignment(horizontal="center", vertical="center")
            celda.fill = color_fondo
            celda.border = borde_blanco
    
    def exportarExcelCeldasAsentamiento(idproyecto, nameproyecto, idzona, celdasmarcadas, fechaini, fechafin):
        respuesta = EmpresaConfiguracion.obtenerDataEmpresa()
        logo = respuesta[4]
        libro = Workbook()
        cont = 0
        for namecelda, idinstrumento, idcelda in celdasmarcadas:
            infocelda = DatosController.ctrlTraerInfoCeldaAsentamiento(idzona, "CELDA", idinstrumento)
            datoscelda = DatosController.ctrlListarDataCeldaAsentamiento(idproyecto, idzona, idinstrumento, fechaini, fechafin)
            if infocelda and datoscelda:
                if cont == 0:
                    hoja = libro.active
                    hoja.title = namecelda
                else:
                    hoja = libro.create_sheet(title=namecelda)
                # Configurar la hoja (común para todas)
                ExportarData.configurarCabeceraHojaCeldaAsentamiento(hoja, infocelda, nameproyecto, namecelda, logo)
                # Insertar datos en la tabla comenzando desde la fila 12
                for fila in datoscelda:
                    # fila viene como: Fecha, Hora, FrecDigits, FrecHz, Temperatura, Desplazamiento, Cota, Superficie, Observación
                    fecha, hora, frecdigits, frechz, temperatura, desplazamiento, cota, superficie, observacion = fila
                    filaordenada = [fecha, hora, frecdigits, frechz, temperatura, desplazamiento, observacion, cota, superficie]
                    hoja.append(filaordenada)
                cont += 1
        rutaexcel = resource_path("resources/workspace/dataequipos.xlsx")
        libro.save(rutaexcel)
        archivo_destino, _ = QFileDialog.getSaveFileName(None, "Guardar Excel en", "Celdas", "Archivos de Excel (*.xlsx);;Todos los archivos (*)")
        if archivo_destino:
            # Asegurarse de que el archivo tenga la extensión .xlsx
            if not archivo_destino.lower().endswith('.xlsx'):
                archivo_destino += '.xlsx'
            try:
                shutil.copy(rutaexcel, archivo_destino)
                mostrar_mensaje("Data Exportada", f"El Excel se ha guardado en: {archivo_destino}", "informacion")
            except Exception as e:  # Captura cualquier excepción
                mostrar_mensaje("Error al Exportar", f"No se pudo guardar el Excel: {str(e)}", "advertencia")

    def configurarCabeceraHojaCeldaAsentamiento(hoja, infocelda, proyectoname, namecelda, logo):
        # Definir colores, bordes, y otros atributos comunes
        color_fondo = PatternFill(start_color="000000", end_color="000000", fill_type="solid")
        borde_negro = Border(
            left=Side(style="thin", color="000000"),
            right=Side(style="thin", color="000000"),
            top=Side(style="thin", color="000000"),
            bottom=Side(style="thin", color="000000"),
        )
        borde_blanco = Border(
            left=Side(style="thin", color="FFFFFF"),
            right=Side(style="thin", color="FFFFFF"),
            top=Side(style="thin", color="FFFFFF"),
            bottom=Side(style="thin", color="FFFFFF"),
        )
        # Ajustar el ancho de las columnas para mejor presentación
        for col in range(1, 11):  # 10 columnas de ancho
            hoja.column_dimensions[chr(64 + col)].width = 20
        # Ajustar el alto de las filas de 1 a 5 para el área de la imagen
        for row in range(1, 5):
            hoja.row_dimensions[row].height = 25
        # Ruta de la imagen
        if logo:
            imagen_stream = MetodosGenerales.convertirBlobImagen(logo)
            imagen = ExcelImage(imagen_stream)
        else:
            ui_file_path = resource_path("resources/logo.png")
            imagen = ExcelImage(ui_file_path)
        imagen.width = 132
        imagen.height = 132
        imagen.anchor = "A1"
        hoja.merge_cells("A1:A4")
        hoja.add_image(imagen)

        # Agregar el título
        hoja.merge_cells("B1:I4")
        celda_titulo = hoja["B1"]
        celda_titulo.value = f"MONITOREO DE CELDAS DE ASENTAMIENTO - {proyectoname.upper()}"
        celda_titulo.font = Font(size=18, bold=True)
        celda_titulo.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        # Agregar el subtítulo (2 bloques: SENSOR e INSTALACIÓN) - fila 6-7, sin espacio extra
        cabeceraGeneral = [("A6:C7", "DATOS DEL SENSOR"), ("D6:I7", "DATOS DE INSTALACIÓN")]
        for rango, texto in cabeceraGeneral:
            hoja.merge_cells(rango)
            celda = hoja[rango.split(":")[0]]
            celda.value = texto
            celda.font = Font(size=14, bold=True, color="FFFFFF")
            celda.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            celda.fill = color_fondo

        # Definir datos generales (bloque de 6 filas: 8 a 13)
        datosceldas = [
            ("A8", "Nombre:"), ("A9", "Marca:"), ("A10", "Modelo:"),
            ("A11", "Serie:"), ("A12", "C.F.:"), ("A13", "T.K.:"),
        ]
        datoscombinados = [
            ("B8:C8", namecelda), ("B9:C9", infocelda[3]), ("B10:C10", infocelda[4]),
            ("B11:C11", infocelda[5]), ("B12:C12", infocelda[13]), ("B13:C13", infocelda[14]),
            ("D8:E8", "Cota Instalación (m.s.n.m):"),
            ("D9:E9", "Cota Fundación (m.s.n.m):"),
            ("D10:E10", "Coordenada Este (m):"),
            ("D11:E11", "Coordenada Norte (m):"),
            ("D12:E12", "Cota de Superficie Actual (m.s.n.m):"),
            ("D13:E13", "Rango (m):"),
            ("F8:I8", infocelda[9]), ("F9:I9", infocelda[10]),
            ("F10:I10", infocelda[7]), ("F11:I11", infocelda[8]),
            ("F12:I12", infocelda[15]),  # TODO: ajusta el índice real de "Cota de Superficie Actual"
            ("F13:I13", infocelda[6]),
        ]
        for rango, texto in datosceldas:
            celda = hoja[rango]
            celda.value = texto
            celda.font = Font(bold=True, color="FFFFFF")
            celda.fill = color_fondo
        for rango, texto in datoscombinados:
            hoja.merge_cells(rango)
            celda = hoja[rango.split(":")[0]]
            celda.value = texto
            if rango.startswith("D"):
                celda.font = Font(bold=True, color="FFFFFF")
                celda.fill = color_fondo
            else:
                celda.alignment = Alignment(horizontal="center", vertical="center")

        # --- Bordes NEGROS: bloque superior (logo, título) y celdas de VALORES (fondo blanco) ---
        rangosceldas_negro = ["A1:A4", "B1:I4"] + \
            [f"B{f}:C{f}" for f in range(8, 14)] + \
            [f"F{f}:I{f}" for f in range(8, 14)]
        for rango in rangosceldas_negro:
            ExportarData._aplicar_borde(hoja, rango, borde_negro)

        # --- Bordes BLANCOS: subtítulos y celdas de ETIQUETAS (fondo negro) ---
        rangosceldas_blanco = ["A6:C7", "D6:I7"] + \
            [f"A{f}" for f in range(8, 14)] + \
            [f"D{f}:E{f}" for f in range(8, 14)]
        for rango in rangosceldas_blanco:
            ExportarData._aplicar_borde(hoja, rango, borde_blanco)

        # Fila de encabezados detallados (fila 14, pegada al bloque de datos, sin espacio)
        encabezados = ["Fecha", "Hora", "Frecuencia (Digits)", "Frecuencia (Hz)", "Temperatura (°C)",
                    "Desplazamiento (m)", "Observación", "Cota (m.s.n.m)", "Superficie (m.s.n.m)"]
        for col, encabezado in enumerate(encabezados, 1):
            celda = hoja[chr(64 + col) + "14"]
            celda.value = encabezado
            celda.font = Font(bold=True, color="FFFFFF")
            celda.alignment = Alignment(horizontal="center", vertical="center")
            celda.fill = color_fondo
            celda.border = borde_blanco
    
    def exportarExcelAcelerografos(idproyecto, nameproyecto, idzona, acelerografosmarcados, fechaini, fechafin):
        respuesta = EmpresaConfiguracion.obtenerDataEmpresa()
        logo = respuesta[4]
        libro = Workbook()
        cont = 0
        for nameacelero, idinstrumento, idacelero in acelerografosmarcados:
            infoacelero = DatosController.ctrlTraerInfoAcelerografo(idzona, "ACELEROGRAFO", idinstrumento)
            datosacelero = DatosController.ctrlListarDataAcelerografo(idproyecto, idzona, idinstrumento, fechaini, fechafin)
            if infoacelero and datosacelero:
                if cont == 0:
                    hoja = libro.active
                    hoja.title = nameacelero
                else:
                    hoja = libro.create_sheet(title=nameacelero)
                # Configurar la hoja (común para todas)
                ExportarData.configurarCabeceraHojaAcelerografo(hoja, infoacelero, nameproyecto, nameacelero, logo)
                # Insertar datos en la tabla comenzando desde la fila 19
                for fila in datosacelero:
                    hoja.append(list(fila))
                cont += 1
        rutaexcel = resource_path("resources/workspace/dataequipos.xlsx")
        libro.save(rutaexcel)
        archivo_destino, _ = QFileDialog.getSaveFileName(None, "Guardar Excel en", "Acelerografos", "Archivos de Excel (*.xlsx);;Todos los archivos (*)")
        if archivo_destino:
            # Asegurarse de que el archivo tenga la extensión .xlsx
            if not archivo_destino.lower().endswith('.xlsx'):
                archivo_destino += '.xlsx'
            try:
                shutil.copy(rutaexcel, archivo_destino)
                mostrar_mensaje("Data Exportada", f"El Excel se ha guardado en: {archivo_destino}", "informacion")
            except Exception as e:  # Captura cualquier excepción
                mostrar_mensaje("Error al Exportar", f"No se pudo guardar el Excel: {str(e)}", "advertencia")
    
    def configurarCabeceraHojaAcelerografo(hoja, infoacelero, proyectoname, namepluvio, logo):
        # Definir colores, bordes, y otros atributos comunes
        color_fondo = PatternFill(start_color="000000", end_color="000000", fill_type="solid")
        borde_negro = Border(
            left=Side(style="thin", color="000000"),
            right=Side(style="thin", color="000000"),
            top=Side(style="thin", color="000000"),
            bottom=Side(style="thin", color="000000"),
        )
        borde_blanco = Border(
            left=Side(style="thin", color="FFFFFF"),
            right=Side(style="thin", color="FFFFFF"),
            top=Side(style="thin", color="FFFFFF"),
            bottom=Side(style="thin", color="FFFFFF"),
        )
        centro = Alignment(horizontal="center", vertical="center", wrap_text=True)

        # Ajustar el ancho de las columnas (A-E)
        anchos = {"A": 16, "B": 16, "C": 18, "D": 18, "E": 18}
        for col, ancho in anchos.items():
            hoja.column_dimensions[col].width = ancho

        # Alto de filas para el logo
        for row in range(1, 5):
            hoja.row_dimensions[row].height = 25

        # --- LOGO (A1:A4) ---
        if logo:
            imagen_stream = MetodosGenerales.convertirBlobImagen(logo)
            imagen = ExcelImage(imagen_stream)
        else:
            ui_file_path = resource_path("resources/logo.png")
            imagen = ExcelImage(ui_file_path)
        imagen.width = 132
        imagen.height = 132
        imagen.anchor = "A1"
        hoja.merge_cells("A1:A4")
        hoja.add_image(imagen)

        # --- TÍTULO (B1:E3) ---
        hoja.merge_cells("B1:E3")
        celda_titulo = hoja["B1"]
        celda_titulo.value = "FORMATO DE DATOS - ACELERÓGRAFOS"
        celda_titulo.font = Font(size=16, bold=True)
        celda_titulo.alignment = centro

        # --- NOTAS (fila 5 y 6) ---
        hoja.merge_cells("A5:E5")
        nota1 = hoja["A5"]
        nota1.value = "* Los datos no debe contener fórmulas y el Formato de fecha: día/mes/año completo (15/01/2020)."
        nota1.font = Font(size=9, bold=True)

        hoja.merge_cells("A6:E6")
        nota2 = hoja["A6"]
        nota2.value = "* El formato de hora: hh:mm:ss"
        nota2.font = Font(size=9, bold=True)

        # --- BLOQUE "DATOS DEL EQUIPO" (fila 8:9) ---
        hoja.merge_cells("A8:E9")
        celda_bloque = hoja["A8"]
        celda_bloque.value = "DATOS DEL EQUIPO"
        celda_bloque.font = Font(size=14, bold=True, color="FFFFFF")
        celda_bloque.alignment = centro
        celda_bloque.fill = color_fondo

        def val(idx, default=0):
            return infoacelero[idx] if len(infoacelero) > idx else default

        # --- Fila 10: Nombre / Norte ---
        datosceldas = [
            ("A10:B10", "Nombre:"),
            ("D10:D10", "Norte (m):"),
        ]
        valores = [
            ("C10:C10", namepluvio),
            ("E10:E10", val(5, 0)),   # Norte
        ]

        # --- Fila 11: Este / Elevación ---
        datosceldas += [
            ("A11:B11", "Este (m):"),
            ("D11:D11", "Elevación (msnm):"),
        ]
        valores += [
            ("C11:C11", val(4, 0)),   # Este
            ("E11:E11", val(6, 0)),   # Elevación
        ]

        # Escribir labels (fondo negro, texto blanco)
        for rango, texto in datosceldas:
            hoja.merge_cells(rango)
            celda = hoja[rango.split(":")[0]]
            celda.value = texto
            celda.font = Font(bold=True, color="FFFFFF")
            celda.fill = color_fondo
            celda.alignment = centro

        # Escribir valores (fondo BLANCO)
        for rango, texto in valores:
            if ":" in rango:
                hoja.merge_cells(rango)
            celda = hoja[rango.split(":")[0]]
            celda.value = texto
            celda.alignment = centro

        # --- Bordes NEGROS: bloque superior (logo, título, notas) + celdas de VALORES (fondo blanco) ---
        rangosceldas_negro = ["A1:A4", "B1:E3", "A5:E5", "A6:E6", "C10:C10", "E10:E10", "C11:C11", "E11:E11"]
        for rango in rangosceldas_negro:
            for fila_celdas in hoja[rango]:
                for celda in fila_celdas:
                    celda.border = borde_negro

        # --- Bordes BLANCOS: cabecera de bloque + celdas de LABELS (fondo negro) ---
        rangosceldas_blanco = ["A8:E9", "A10:B10", "D10:D10", "A11:B11", "D11:D11"]
        for rango in rangosceldas_blanco:
            for fila_celdas in hoja[rango]:
                for celda in fila_celdas:
                    celda.border = borde_blanco

        # --- Encabezados de la tabla (fila 12) ---
        encabezados = ["Fecha", "Hora", "Magnitud", "Distancia (Km)", "Observación"]
        for col, encabezado in enumerate(encabezados, 1):
            celda = hoja.cell(row=12, column=col, value=encabezado)
            celda.font = Font(bold=True, color="FFFFFF")
            celda.alignment = centro
            celda.fill = color_fondo
            celda.border = borde_blanco

    def exportarZipSondajesTDR(idproyecto, nameproyecto, idzona, sondajesmarcados):
        zip_filename = resource_path("resources/workspace/zipequipos.zip")
        try:
            respuesta = EmpresaConfiguracion.obtenerDataEmpresa()
            logo = respuesta[4]
            with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for nombretdr, idinstrumento, idtdr in sondajesmarcados:
                    infotdr = DatosController.ctrlObtenerInfoExportarSondajetdr(idproyecto, idzona, idinstrumento)
                    if infotdr:
                        workbook = Workbook()
                        first_sheet = True
                        for info in infotdr:
                            fecha = info[0]
                            dataencabeza = DatosController.ctrlObtenerDataExportarSondajetdr(idproyecto, idtdr, fecha)
                            if dataencabeza:
                                # Crear o seleccionar la hoja
                                nombretitle = f"{nombretdr}_{fecha}".replace("/", "_").replace(":", "_")
                                if first_sheet:
                                    sheet = workbook.active
                                    sheet.title = nombretitle
                                    first_sheet = False
                                else:
                                    sheet = workbook.create_sheet(title=nombretitle)
                                # Configurar cabecera y datos
                                ExportarData.configurarCabeceraHojaSondajetdr(sheet, info, nameproyecto, nombretdr, logo)
                                for fila in dataencabeza:
                                    sheet.append(list(fila))
                        # Guardar en memoria
                        excel_stream = io.BytesIO()
                        workbook.save(excel_stream)
                        excel_stream.seek(0)
                        # Nombre del archivo Excel dentro del ZIP
                        excel_name = f"{nombretdr}.xlsx"
                        zipf.writestr(excel_name, excel_stream.getvalue())
            # Guardar ZIP en una ubicación elegida por el usuario
            archivo_destino, _ = QFileDialog.getSaveFileName(None, "Guardar ZIP en", "SondajesTDR", "Archivos ZIP (*.zip);;Todos los archivos (*)")
            if archivo_destino:
                if not archivo_destino.lower().endswith('.zip'):
                    archivo_destino += '.zip'
                shutil.copy(zip_filename, archivo_destino)
                mostrar_mensaje("Data Exportada", f"El ZIP se ha guardado en: {archivo_destino}", "informacion")
        except Exception as e:
            mostrar_mensaje("Error al Exportar", f"No se pudo guardar el ZIP: {str(e)}", "advertencia")
    
    def configurarCabeceraHojaSondajetdr(hoja, infotdr, proyectoname, nametdr, logo):
        # Definir colores, bordes, y otros atributos comunes
        color_fondo = PatternFill(start_color="000000", end_color="000000", fill_type="solid")
        borde_negro = Border(
            left=Side(style="thin", color="000000"),
            right=Side(style="thin", color="000000"),
            top=Side(style="thin", color="000000"),
            bottom=Side(style="thin", color="000000"),
        )
        borde_blanco = Border(
            left=Side(style="thin", color="FFFFFF"),
            right=Side(style="thin", color="FFFFFF"),
            top=Side(style="thin", color="FFFFFF"),
            bottom=Side(style="thin", color="FFFFFF"),
        )
        # Ajustar el ancho de las columnas para mejor presentación
        for col in range(1, 6):  # 5 columnas de ancho
            hoja.column_dimensions[chr(64 + col)].width = 20
        # Ajustar el alto de las filas de 1 a 5 para el área de la imagen
        for row in range(1, 5):
            hoja.row_dimensions[row].height = 25
        # Ruta de la imagen
        if logo:
            imagen_stream = MetodosGenerales.convertirBlobImagen(logo)
            imagen = ExcelImage(imagen_stream)
        else:
            ui_file_path = resource_path("resources/logo.png")
            imagen = ExcelImage(ui_file_path)
        imagen.width = 132
        imagen.height = 132
        imagen.anchor = "A1"
        hoja.merge_cells("A1:A4")
        hoja.add_image(imagen)
        # Agregar el título
        hoja.merge_cells("B1:E4")
        celda_titulo = hoja["B1"]
        celda_titulo.value = f"MONITOREO DE EQUIPOS TDR - {proyectoname.upper()}"
        celda_titulo.font = Font(size=18, bold=True)
        celda_titulo.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        # Notas (fila 5 y 6)
        hoja.merge_cells("A5:E5")
        nota1 = hoja["A5"]
        nota1.value = "* Los datos no debe contener fórmulas y el Formato de fecha: día/mes/año completo."
        nota1.font = Font(size=9, bold=True)

        hoja.merge_cells("A6:E6")
        nota2 = hoja["A6"]
        nota2.value = "* El formato de hora: hh:mm:ss"
        nota2.font = Font(size=9, bold=True)

        # Agregar el subtítulo — empieza en la fila 8
        rango, texto = "A8:E8", "DATOS DEL EQUIPO"
        hoja.merge_cells(rango)
        celda = hoja[rango.split(":")[0]]
        celda.value = texto
        celda.font = Font(size=14, bold=True, color="FFFFFF")
        celda.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        celda.fill = color_fondo

        # Definir datos generales (filas 9 a 12, justo debajo del subtítulo)
        datosceldas = [("A9", "Nombre:"), ("A10", "Este:"), ("A11", "Norte:"), ("A12", "Elevación:"),
                    ("B9", nametdr), ("B10", infotdr[2]), ("B11", infotdr[3]), ("B12", infotdr[4]),
                    ("C9", "Profundidad:"), ("C10", "Inclinación:"), ("C11", "Azimuth:"), ("C12", "Comentario:")]
        datoscombinados = [("D9:E9", infotdr[5]), ("D10:E10", infotdr[6]),
                        ("D11:E11", infotdr[7]), ("D12:E12", infotdr[8])]
        for rango, texto in datosceldas:
            celda = hoja[rango]
            celda.value = texto
            if rango.startswith("B"):
                celda.alignment = Alignment(horizontal="left")
            else:
                celda.alignment = Alignment(horizontal="center", vertical="center")
                celda.font = Font(bold=True, color="FFFFFF")
                celda.fill = color_fondo
        for rango, texto in datoscombinados:
            hoja.merge_cells(rango)
            celda = hoja[rango.split(":")[0]]
            celda.value = texto
            celda.alignment = Alignment(horizontal="center", vertical="center")

        # --- Bordes NEGROS: bloque superior (logo, título, notas) y celdas de VALORES (fondo blanco) ---
        rangosceldas_negro = ["A1:A4", "B1:E4", "A5:E5", "A6:E6",
                            "B9", "B10", "B11", "B12",
                            "D9:E9", "D10:E10", "D11:E11", "D12:E12"]
        for rango in rangosceldas_negro:
            ExportarData._aplicar_borde(hoja, rango, borde_negro)

        # --- Bordes BLANCOS: subtítulo y celdas de ETIQUETAS (fondo negro) ---
        rangosceldas_blanco = ["A8:E8", "A9", "A10", "A11", "A12", "C9", "C10", "C11", "C12"]
        for rango in rangosceldas_blanco:
            ExportarData._aplicar_borde(hoja, rango, borde_blanco)

        # Fila de encabezados detallados (fila 13, pegada al bloque de datos, sin espacio)
        fila_headers = 13
        encabezados = ["Fecha", "Hora", "Profundidad (m)", "Impedancia", "Observación"]
        for col, encabezado in enumerate(encabezados, 1):
            celda = hoja[chr(64 + col) + str(fila_headers)]
            celda.value = encabezado
            celda.font = Font(bold=True, color="FFFFFF")
            celda.alignment = Alignment(horizontal="center", vertical="center")
            celda.fill = color_fondo
            celda.border = borde_blanco


    def exportarExcelCotasTerreno(idproyecto, nameproyecto, idzona, terrenosmarcados):
        respuesta = EmpresaConfiguracion.obtenerDataEmpresa()
        logo = respuesta[4]
        libro = Workbook()
        cont = 0
        for namecota, idinstrumento, idcota in terrenosmarcados:
            datospluvio = DatosController.ctrlListarDataCotaTerreno(idproyecto, idzona, idinstrumento)
            if datospluvio:
                if cont == 0:
                    hoja = libro.active
                    hoja.title = namecota
                else:
                    hoja = libro.create_sheet(title=namecota)
                # Configurar la hoja (común para todas)
                ExportarData.configurarCabeceraHojaCotaTerreno(hoja, nameproyecto, namecota, logo)
                # Insertar datos en la tabla comenzando desde la fila 12
                for fila in datospluvio:
                    hoja.append(list(fila))
                cont += 1
        rutaexcel = resource_path("resources/workspace/dataequipos.xlsx")
        libro.save(rutaexcel)
        archivo_destino, _ = QFileDialog.getSaveFileName(None, "Guardar Excel en", "Terrenos", "Archivos de Excel (*.xlsx);;Todos los archivos (*)")
        if archivo_destino:
            # Asegurarse de que el archivo tenga la extensión .xlsx
            if not archivo_destino.lower().endswith('.xlsx'):
                archivo_destino += '.xlsx'
            try:
                shutil.copy(rutaexcel, archivo_destino)
                mostrar_mensaje("Data Exportada", f"El Excel se ha guardado en: {archivo_destino}", "informacion")
            except Exception as e:  # Captura cualquier excepción
                mostrar_mensaje("Error al Exportar", f"No se pudo guardar el Excel: {str(e)}", "advertencia")
    
    def configurarCabeceraHojaCotaTerreno(hoja, proyectoname, namecota, logo, comentario=""):
        # Definir colores, bordes, y otros atributos comunes
        color_fondo = PatternFill(start_color="000000", end_color="000000", fill_type="solid")
        borde_negro = Border(
            left=Side(style="thin", color="000000"),
            right=Side(style="thin", color="000000"),
            top=Side(style="thin", color="000000"),
            bottom=Side(style="thin", color="000000"),
        )
        borde_blanco = Border(
            left=Side(style="thin", color="FFFFFF"),
            right=Side(style="thin", color="FFFFFF"),
            top=Side(style="thin", color="FFFFFF"),
            bottom=Side(style="thin", color="FFFFFF"),
        )
        centro = Alignment(horizontal="center", vertical="center", wrap_text=True)

        # Ajustar el ancho de las columnas
        anchos = {"A": 20, "B": 16, "C": 22, "D": 22}
        for col, ancho in anchos.items():
            hoja.column_dimensions[col].width = ancho

        # Alto de filas para el logo
        for row in range(1, 5):
            hoja.row_dimensions[row].height = 25

        # --- LOGO (A1:A4) ---
        if logo:
            imagen_stream = MetodosGenerales.convertirBlobImagen(logo)
            imagen = ExcelImage(imagen_stream)
        else:
            ui_file_path = resource_path("resources/logo.png")
            imagen = ExcelImage(ui_file_path)
        imagen.width = 132
        imagen.height = 132
        imagen.anchor = "A1"
        hoja.merge_cells("A1:A4")
        hoja.add_image(imagen)

        # --- TÍTULO (B1:D4) ---
        hoja.merge_cells("B1:D4")
        celda_titulo = hoja["B1"]
        celda_titulo.value = f"FORMATO DE DATOS - {proyectoname.upper() if proyectoname else 'COTAS DE TERRENO'}"
        celda_titulo.font = Font(size=16, bold=True)
        celda_titulo.alignment = centro

        # --- NOTAS (fila 5 y 6) ---
        hoja.merge_cells("A5:D5")
        nota1 = hoja["A5"]
        nota1.value = "* Los datos no debe contener fórmulas y el Formato de fecha: día/mes/año completo."
        nota1.font = Font(size=9, bold=True)

        hoja.merge_cells("A6:D6")
        nota2 = hoja["A6"]
        nota2.value = "* El formato de hora: hh:mm:ss"
        nota2.font = Font(size=9, bold=True)

        # --- BLOQUE "DATOS DEL TERRENO" (fila 8) ---
        hoja.merge_cells("A8:D8")
        celda_bloque = hoja["A8"]
        celda_bloque.value = "DATOS DEL TERRENO"
        celda_bloque.font = Font(size=13, bold=True, color="FFFFFF")
        celda_bloque.alignment = centro
        celda_bloque.fill = color_fondo

        # --- Nombre (fila 9) ---
        hoja.merge_cells("A9:B9")
        celda_lbl = hoja["A9"]
        celda_lbl.value = "Nombre:"
        celda_lbl.font = Font(bold=True, color="FFFFFF")
        celda_lbl.fill = color_fondo
        celda_lbl.alignment = centro

        hoja.merge_cells("C9:D9")
        celda_val = hoja["C9"]
        celda_val.value = namecota
        celda_val.alignment = centro

        # --- Comentario (fila 10) ---
        hoja.merge_cells("A10:B10")
        celda_lbl2 = hoja["A10"]
        celda_lbl2.value = "Comentario:"
        celda_lbl2.font = Font(bold=True, color="FFFFFF")
        celda_lbl2.fill = color_fondo
        celda_lbl2.alignment = centro

        hoja.merge_cells("C10:D10")
        celda_val2 = hoja["C10"]
        celda_val2.value = comentario
        celda_val2.alignment = centro

        # --- Bordes NEGROS: bloque superior (logo, título, notas) y celdas de VALORES (fondo blanco) ---
        rangosceldas_negro = ["A1:A4", "B1:D4", "A5:D5", "A6:D6", "C9:D9", "C10:D10"]
        for rango in rangosceldas_negro:
            for fila_celdas in hoja[rango]:
                for celda in fila_celdas:
                    celda.border = borde_negro

        # --- Bordes BLANCOS: bloque "DATOS DEL TERRENO" y celdas de ETIQUETAS (fondo negro) ---
        rangosceldas_blanco = ["A8:D8", "A9:B9", "A10:B10"]
        for rango in rangosceldas_blanco:
            for fila_celdas in hoja[rango]:
                for celda in fila_celdas:
                    celda.border = borde_blanco

        # --- Encabezados de la tabla (fila 11) ---
        encabezados = ["Fecha", "Hora", "Cota (msnm)", "Observación"]
        for col, encabezado in enumerate(encabezados, 1):
            celda = hoja.cell(row=11, column=col, value=encabezado)
            celda.font = Font(bold=True, color="FFFFFF")
            celda.alignment = centro
            celda.fill = color_fondo
            celda.border = borde_blanco

    def descargarFormatoExcel(tipo):
        if tipo == "prisma":
            rutaexcel = resource_path("resources/formatos/FormatoPrismas.xlsx")
            nombrearchivo = "FormatoPrismas.xlsx"
        elif tipo == "cuerda":
            rutaexcel = resource_path("resources/formatos/FormatoPiezometroCuerda.xlsx")
            nombrearchivo = "FormatoPiezometrosCuerda.xlsx"
        elif tipo == "casagrande":
            rutaexcel = resource_path("resources/formatos/FormatoPiezometroCasagrande.xlsx")
            nombrearchivo = "FormatoPiezometrosCasagrande.xlsx"
        elif tipo == "celda":
            rutaexcel = resource_path("resources/formatos/FormatoCeldas.xlsx")
            nombrearchivo = "FormatoCeldas.xlsx"
        elif tipo == "pluvio":
            rutaexcel = resource_path("resources/formatos/FormatoPluviometros.xlsx")
            nombrearchivo = "FormatoPluviometros.xlsx"
        elif tipo == "cota":
            rutaexcel = resource_path("resources/formatos/FormatoCotaTerreno.xlsx")
            nombrearchivo = "FormatoCotasTerreno.xlsx"
        elif tipo == "sondaje":
            rutaexcel = resource_path("resources/formatos/FormatoTDR.xlsx")
            nombrearchivo = "FormatoTDR.xlsx"
        else:
            rutaexcel = resource_path("resources/formatos/FormatoAcelerografos.xlsx")
            nombrearchivo = "FormatoAcelerografos.xlsx"
        archivo_destino, _ = QFileDialog.getSaveFileName(None, "Guardar Excel en", nombrearchivo, "Archivos de Excel (*.xlsx);;Todos los archivos (*)")
        if archivo_destino:
            # Asegurarse de que el archivo tenga la extensión .xlsx
            if not archivo_destino.lower().endswith('.xlsx'):
                archivo_destino += '.xlsx'
            try:
                shutil.copy(rutaexcel, archivo_destino)
                mostrar_mensaje("Data Exportada", f"El Excel se ha guardado en: {archivo_destino}", "informacion")
            except Exception as e:  # Captura cualquier excepción
                mostrar_mensaje("Error al Exportar", f"No se pudo guardar el Excel: {str(e)}", "advertencia")
    