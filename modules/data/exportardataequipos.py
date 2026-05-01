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
from PySide6.QtCore import QDateTime
from PySide6.QtWidgets import (QVBoxLayout, QPushButton, QDateTimeEdit, QDialog, QFileDialog)
from utils.common.alertas import mostrar_mensaje
from utils.common.rutasarchivos import resource_path
from utils.common.metodosGenerales import MetodosGenerales
from modules.empresa.softwareconfiguracion import SoftwareConfiguracion
from modules.empresa.empresaconfiguracion import EmpresaConfiguracion
from controllers.DatosController import DatosController

class ExportarData():
    
    def validarExportarDataEquipos(idproyecto, nameproyecto, idzona, tipo, equipos, fechainicial=None, fechafinal=None):
        loader = QUiLoader()        
        ui_file_path = resource_path("ui/exportardataequipos.ui")
        ui_file = loader.load(ui_file_path, None)
        dialogo = QDialog()
        dialogo.setWindowTitle(f"Exportar data {tipo}")
        layout = QVBoxLayout()
        layout.addWidget(ui_file)
        dialogo.setLayout(layout)
        # inicializar herramientas
        dateinicio = dialogo.findChild(QDateTimeEdit, "date_inicio")
        datefin = dialogo.findChild(QDateTimeEdit, "date_fin")
        botonexportar = dialogo.findChild(QPushButton, "btn_exportar")
        botonexportarcsv = dialogo.findChild(QPushButton, "btn_exportar_csv")
        botonexportarcsv.setVisible(False)
        formato = "yyyy-MM-dd HH:mm:ss"
        # cargar fechas actuales
        if fechainicial:
            datetime_inicial = QDateTime.fromString(str(fechainicial), formato)
            datetime_final = QDateTime.fromString(str(fechafinal), formato)
            if datetime_inicial.isValid() and datetime_final.isValid():
                dateinicio.setDateTime(datetime_inicial)
                datefin.setDateTime(datetime_final)
                # Habilitar o deshabilitar el botón según la diferencia           
                diferencia = datetime_inicial.date().daysTo(datetime_final.date())
                botonexportar.setEnabled(diferencia > 0)
            else:
                fecha_hora_actual = QDateTime.currentDateTime()
                dateinicio.setDateTime(fecha_hora_actual)
                datefin.setDateTime(fecha_hora_actual)
                botonexportar.setEnabled(False)
        else:
            fecha_hora_actual = QDateTime.currentDateTime()
            dateinicio.setDateTime(fecha_hora_actual)
            datefin.setDateTime(fecha_hora_actual)
            dateinicio.setEnabled(False)
            datefin.setEnabled(False)
        if tipo == "Prismas":
            botonexportarcsv.setVisible(True)
        # Función para calcular y actualizar la diferencia en días
        def actualizar_diferencia():
            inicio = dateinicio.dateTime()
            fin = datefin.dateTime()            
            diferencia = inicio.date().daysTo(fin.date())
            # Habilitar o deshabilitar el botón según la diferencia
            botonexportar.setEnabled(diferencia > 0)
        def exportarDataEquipo():
            time_inicio = dateinicio.dateTime().toString(formato)
            time_fin = datefin.dateTime().toString(formato)
            dialogo.close()
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
            time_inicio = dateinicio.dateTime().toString(formato)
            time_fin = datefin.dateTime().toString(formato)
            dialogo.close()
            ExportarData.exportarExcelPrismasCSV(idproyecto, nameproyecto, idzona, equipos, time_inicio, time_fin)
        # Conectar las señales de cambio de valor a la función
        dateinicio.dateTimeChanged.connect(actualizar_diferencia)
        datefin.dateTimeChanged.connect(actualizar_diferencia)
        botonexportar.clicked.connect(exportarDataEquipo)
        botonexportarcsv.clicked.connect(exportarDataEquiposCSV)
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
                # Configurar la hoja (común para todas)
                ExportarData.configurarCabeceraHojaPrismas(hoja, proyectoname, nameprisma, logo)
                # Insertar datos en la tabla comenzando desde la fila 11
                for fila in prismasdata:
                    hoja.append(fila)
                cont += 1
        rutaexcel = resource_path("resources/workspace/dataequipos.xlsx")
        libro.save(rutaexcel)
        archivo_destino, _ = QFileDialog.getSaveFileName(None, "Guardar Excel en", "", "Archivos de Excel (*.xlsx);;Todos los archivos (*)")
        if archivo_destino:
            # Asegurarse de que el archivo tenga la extensión .xlsx
            if not archivo_destino.lower().endswith('.xlsx'):
                archivo_destino += '.xlsx'
            try:
                shutil.copy(rutaexcel, archivo_destino)
                mostrar_mensaje("Data Exportada", f"El Excel se ha guardado en: {archivo_destino}", "informacion")
            except Exception as e:  # Captura cualquier excepción
                mostrar_mensaje("Error al Exportar", f"No se pudo guardar el Excel: {str(e)}", "advertencia")
    
    def configurarCabeceraHojaPrismas(hoja, proyectoname, nameprisma, logo):
        # Definir colores, bordes, y otros atributos comunes
        color_fondo = PatternFill(start_color="3C3C3C", end_color="3C3C3C", fill_type="solid")
        borde_negro = Border(
            left=Side(style="thin", color="000000"),
            right=Side(style="thin", color="000000"),
            top=Side(style="thin", color="000000"),
            bottom=Side(style="thin", color="000000"),
        )
        # Ajustar el ancho de las columnas (A hasta K)
        for col in range(1, 12):
            hoja.column_dimensions[chr(64 + col)].width = 20
        # Ajustar el alto de las filas 1 a 4 para el logo
        for row in range(1, 5):
            hoja.row_dimensions[row].height = 25
        # ---- LOGO (A1:A4) ----
        if logo:
            imagen_stream = MetodosGenerales.convertirBlobImagen(logo)
            imagen = ExcelImage(imagen_stream)
        else:
            ui_file_path = resource_path("resources/logo.png")
            imagen = ExcelImage(ui_file_path)
        # Tamaño cuadrado 3.5 cm x 3.5 cm
        imagen.width = 132
        imagen.height = 132
        imagen.anchor = "A1"
        hoja.merge_cells("A1:A4")
        hoja.add_image(imagen)
        # ---- TÍTULO (B1:K4) ----
        hoja.merge_cells("B1:K4")
        celda_titulo = hoja["B1"]
        celda_titulo.value = f"MONITOREO DE HITOS TOPOGRÁFICOS - {proyectoname.upper()}"
        celda_titulo.font = Font(size=18, bold=True)
        celda_titulo.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        # ---- SUBTÍTULO (ahora en A6:K7) ----
        hoja.merge_cells("A6:K7")
        celda_subtitulo = hoja["A6"]
        celda_subtitulo.value = f"Hito Topográfico: {nameprisma}"
        celda_subtitulo.font = Font(size=16, bold=True, color="FFFFFF")
        celda_subtitulo.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        celda_subtitulo.fill = color_fondo
        # ---- BORDES para las celdas fusionadas ----
        for rango in ["A1:A4", "B1:K4", "A6:K7",
                    "A9:C9", "D9:G9", "H9:I9", "J9:K9"]:
            for fila_celdas in hoja[rango]:
                for celda in fila_celdas:
                    celda.border = borde_negro
        # ---- CABECERAS DE GRUPO (ahora en fila 9) ----
        cabeceras = [
            ("A9:C9", "Datos"),
            ("D9:G9", "Coordenadas"),
            ("H9:I9", "Desplazamiento (m)"),
            ("J9:K9", "Velocidad (cm/día)"),
        ]
        for rango, texto in cabeceras:
            hoja.merge_cells(rango)
            celda = hoja[rango.split(":")[0]]
            celda.value = texto
            celda.font = Font(size=14, bold=True, color="FFFFFF")
            celda.alignment = Alignment(horizontal="center", vertical="center")
            celda.fill = color_fondo
        # ---- ENCABEZADOS DETALLADOS (ahora en fila 10) ----
        encabezados = [
            "Hito", "Fecha", "Hora", "Este", "Norte", "Elevación",
            "Distancia", "Incremental", "Acumulado", "Incremental", "Acumulado"
        ]
        for col, encabezado in enumerate(encabezados, 1):
            celda = hoja.cell(row=10, column=col, value=encabezado)
            celda.font = Font(bold=True, color="FFFFFF")
            celda.alignment = Alignment(horizontal="center", vertical="center")
            celda.fill = color_fondo
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
                None, "Guardar ZIP en", "", "Archivos ZIP (*.zip);;Todos los archivos (*)"
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
        fechaorig, hora = infoinclino[5].split(" ")
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
        fechaorig, hora = infoinclino[5].split(" ")
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
                    ExportarData.configurarCabeceraHojaPiezometroCuerda(hoja, infopiezo, nameproyecto, namepiezo, logo)
                else:
                    ExportarData.configurarCabeceraHojaPiezometroManual(hoja, infopiezo, nameproyecto, namepiezo, logo)
                # Insertar datos en la tabla comenzando desde la fila 12
                for fila in datospiezo:
                    hoja.append(list(fila))
                cont += 1
        rutaexcel = resource_path("resources/workspace/dataequipos.xlsx")
        libro.save(rutaexcel)
        archivo_destino, _ = QFileDialog.getSaveFileName(None, "Guardar Excel en", "", "Archivos de Excel (*.xlsx);;Todos los archivos (*)")
        if archivo_destino:
            # Asegurarse de que el archivo tenga la extensión .xlsx
            if not archivo_destino.lower().endswith('.xlsx'):
                archivo_destino += '.xlsx'
            try:
                shutil.copy(rutaexcel, archivo_destino)
                mostrar_mensaje("Data Exportada", f"El Excel se ha guardado en: {archivo_destino}", "informacion")
            except Exception as e:  # Captura cualquier excepción
                mostrar_mensaje("Error al Exportar", f"No se pudo guardar el Excel: {str(e)}", "advertencia")
    
    def configurarCabeceraHojaPiezometroCuerda(hoja, infopiezo, proyectoname, namepiezo, logo):
        # Definir colores, bordes, y otros atributos comunes
        color_fondo = PatternFill(start_color="00796B", end_color="00796B", fill_type="solid")
        borde_negro = Border(left=Side(style="thin", color="000000"), right=Side(style="thin", color="000000"),
                            top=Side(style="thin", color="000000"), bottom=Side(style="thin", color="000000"))
        # Ajustar el ancho de las columnas para mejor presentación
        for col in range(1, 10):  # 9 columnas de ancho
            hoja.column_dimensions[chr(64 + col)].width = 20
        # Ajustar el alto de las filas de 1 a 5 para el área de la imagen
        for row in range(1, 6):
            hoja.row_dimensions[row].height = 25
        # Ruta de la imagen
        if logo:
            imagen_stream = MetodosGenerales.convertirBlobImagen(logo)
            imagen = ExcelImage(imagen_stream)
        else:
            ui_file_path = resource_path("resources/logo.png")
            imagen = ExcelImage(ui_file_path)
        imagen.width = 600
        imagen.height = 150
        imagen.anchor = "A1"
        hoja.merge_cells("A1:E5")
        hoja.add_image(imagen)
        # Agregar el título
        hoja.merge_cells("F1:I5")
        celda_titulo = hoja["F1"]
        celda_titulo.value = f"MONITOREO DE PIEZÓMETROS CUERDA VIBRANTE {proyectoname.upper()}"
        celda_titulo.font = Font(size=18, bold=True)
        celda_titulo.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        # Agregar el subtítuloS
        cabeceraGeneral = [("A7:C8", "DATOS DEL SENSOR"), ("D7:F8", "DATOS DE INSTALACIÓN"), ("G7:I8", "DATOS DE CALIBRACIÓN")]
        for rango, texto in cabeceraGeneral:
            hoja.merge_cells(rango)
            celda = hoja[rango.split(":")[0]]
            celda.value = texto
            celda.font = Font(size=14, bold=True, color="FFFFFF")
            celda.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            celda.fill = color_fondo
        # Definir datos generales
        datosceldas = [("A9", "Nombre:"), ("A10", "Componente:"), ("A11", "Marca/Modelo:"), ("A12", "Serie:"),
                    ("F9", infopiezo[7]), ("F10", infopiezo[8]), ("F11", infopiezo[5]), ("F12", infopiezo[6]),
                    ("G9", "C.F.:"), ("G10", "T.K.:"), ("G11", "Inclinación:"), ("G12", "Azimuth:")]
        datoscombinados = [("B9:C9", namepiezo), ("B10:C10", infopiezo[19]), ("B11:C11", ""), ("B12:C12", infopiezo[3]),
                        ("D9:E9", "Cota Instalación (m.s.n.m):"), ("D10:E10", "Cota Fundación (m.s.n.m):"),
                        ("D11:E11", "Coordenada Este:"), ("D12:E12", "Coordenada Norte:"), ("H9:I9", infopiezo[12]),
                        ("H10:I10", infopiezo[13]), ("H11:I11", infopiezo[9]), ("H12:I12", infopiezo[10])]
        for rango, texto in datosceldas:
            celda = hoja[rango]
            celda.value = texto
            if rango.startswith("F"):
                celda.alignment = Alignment(horizontal="center", vertical="center")
            else:
                celda.font = Font(bold=True, color="FFFFFF")
                celda.fill = color_fondo
        for rango, texto in datoscombinados:
            hoja.merge_cells(rango)
            celda = hoja[rango.split(":")[0]]
            celda.value = texto
            if rango.startswith("D") or rango.startswith("E"):
                celda.font = Font(bold=True, color="FFFFFF")
                celda.fill = color_fondo
            else:
                celda.alignment = Alignment(horizontal="center", vertical="center")
        # Agregar bordes a las celdas fusionadas
        rangosceldas = ["A1:E5", "F1:I5", "A7:C8", "D7:F8", "G7:I8", "A9:I12"]
        for rango in rangosceldas:
            for fila_celdas in hoja[rango]:
                for celda in fila_celdas:
                    celda.border = borde_negro
        # Fila de encabezados detallados
        encabezados = ["Fecha", "Hora", f"Frecuencia ({infopiezo[14]})", "Temperatura (°C)", f"Presión ({infopiezo[15]})", "mca (m)", "Cota Piezométrica", "Observación", "Cota Superficie"]
        for col, encabezado in enumerate(encabezados, 1):
            hoja[chr(64 + col) + "14"].value = encabezado
            celda = hoja[chr(64 + col) + "14"]
            celda.font = Font(bold=True, color="FFFFFF")
            celda.alignment = Alignment(horizontal="center", vertical="center")
            celda.fill = color_fondo
            celda.border = borde_negro
    
    def configurarCabeceraHojaPiezometroManual(hoja, infopiezo, proyectoname, namepiezo, logo):
        # Definir colores, bordes, y otros atributos comunes
        color_fondo = PatternFill(start_color="00796B", end_color="00796B", fill_type="solid")
        borde_negro = Border(left=Side(style="thin", color="000000"), right=Side(style="thin", color="000000"),
                            top=Side(style="thin", color="000000"), bottom=Side(style="thin", color="000000"))
        # Ajustar el ancho de las columnas para mejor presentación
        for col in range(1, 11):  # 10 columnas de ancho
            hoja.column_dimensions[chr(64 + col)].width = 20
        # Ajustar el alto de las filas de 1 a 5 para el área de la imagen
        for row in range(1, 6):
            hoja.row_dimensions[row].height = 25
        # Ruta de la imagen
        if logo:
            imagen_stream = MetodosGenerales.convertirBlobImagen(logo)
            imagen = ExcelImage(imagen_stream)
        else:
            ui_file_path = resource_path("resources/logo.png")
            imagen = ExcelImage(ui_file_path)
        imagen.width = 550
        imagen.height = 150
        imagen.anchor = "A1"
        hoja.merge_cells("A1:D5")
        hoja.add_image(imagen)
        # Agregar el título
        hoja.merge_cells("E1:H5")
        celda_titulo = hoja["E1"]
        celda_titulo.value = f"MONITOREO DE PIEZÓMETROS CASAGRANDE {proyectoname.upper()}"
        celda_titulo.font = Font(size=18, bold=True)
        celda_titulo.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        # Agregar el subtítuloS
        cabeceraGeneral = [("A7:C8", "DATOS DEL EQUIPO"), ("D7:H8", "DATOS DE INSTALACIÓN")]
        for rango, texto in cabeceraGeneral:
            hoja.merge_cells(rango)
            celda = hoja[rango.split(":")[0]]
            celda.value = texto
            celda.font = Font(size=14, bold=True, color="FFFFFF")
            celda.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            celda.fill = color_fondo
        # Definir datos generales
        datosceldas = [("A9", "Nombre:"), ("A10", "Código:"), ("A11", "Tipo:"), ("A12", "Ubicación:"),
                    ("F9", infopiezo[6]), ("F10", infopiezo[7]), ("F11", infopiezo[5]), ("F12", infopiezo[4]),
                    ("G9", "Inclinación:"), ("G10", "Azimuth:"), ("G11", "Stick Up (m):"), ("G12", "Comentario:"),
                    ("H9", infopiezo[8]), ("H10", infopiezo[9]), ("H11", infopiezo[10]), ("H12", infopiezo[11])]
        datoscombinados = [("B9:C9", namepiezo), ("B10:C10", infopiezo[3]), ("B11:C11", ""), ("B12:C12", infopiezo[14]),
                        ("D9:E9", "Cota Fondo Pozo (m.s.n.m):"), ("D10:E10", "Cota Fundación (m.s.n.m):"),
                        ("D11:E11", "Coordenada Este:"), ("D12:E12", "Coordenada Norte:")]
        for rango, texto in datosceldas:
            celda = hoja[rango]
            celda.value = texto
            if rango.startswith("F") or rango.startswith("H"):
                celda.alignment = Alignment(horizontal="center", vertical="center")
            else:
                celda.font = Font(bold=True, color="FFFFFF")
                celda.fill = color_fondo
        for rango, texto in datoscombinados:
            hoja.merge_cells(rango)
            celda = hoja[rango.split(":")[0]]
            celda.value = texto
            if rango.startswith("D") or rango.startswith("E"):
                celda.font = Font(bold=True, color="FFFFFF")
                celda.fill = color_fondo
            else:
                celda.alignment = Alignment(horizontal="center", vertical="center")
        # Agregar bordes a las celdas fusionadas
        rangosceldas = ["A1:D5", "E1:H5", "A7:D8", "E7:H8", "A9:H12"]
        for rango in rangosceldas:
            for fila_celdas in hoja[rango]:
                for celda in fila_celdas:
                    celda.border = borde_negro
        # Fila de encabezados detallados
        encabezados = ["Fecha", "Hora", "Niv. Piezométrico (m)", "Profundidad (m)", "Elevación (m.s.n.m)", "Cota Piezométrica", "Nivel Vertical (m)", "Observación"]
        for col, encabezado in enumerate(encabezados, 1):
            hoja[chr(64 + col) + "14"].value = encabezado
            celda = hoja[chr(64 + col) + "14"]
            celda.font = Font(bold=True, color="FFFFFF")
            celda.alignment = Alignment(horizontal="center", vertical="center")
            celda.fill = color_fondo
            celda.border = borde_negro
    
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
                    hoja.append(fila)
                cont += 1
        rutaexcel = resource_path("resources/workspace/dataequipos.xlsx")
        libro.save(rutaexcel)
        archivo_destino, _ = QFileDialog.getSaveFileName(None, "Guardar Excel en", "", "Archivos de Excel (*.xlsx);;Todos los archivos (*)")
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
        color_fondo = PatternFill(start_color="00796B", end_color="00796B", fill_type="solid")
        borde_negro = Border(left=Side(style="thin", color="000000"), right=Side(style="thin", color="000000"),
                            top=Side(style="thin", color="000000"), bottom=Side(style="thin", color="000000"))
        # Ajustar el ancho de las columnas para mejor presentación
        for col in range(1, 5):  # 4 columnas de ancho
            hoja.column_dimensions[chr(64 + col)].width = 20
        # Ajustar el alto de las filas de 1 a 5 para el área de la imagen
        for row in range(1, 6):
            hoja.row_dimensions[row].height = 25
        # Ruta de la imagen
        if logo:
            imagen_stream = MetodosGenerales.convertirBlobImagen(logo)
            imagen = ExcelImage(imagen_stream)
        else:
            ui_file_path = resource_path("resources/logo.png")
            imagen = ExcelImage(ui_file_path)
        imagen.width = 550
        imagen.height = 150
        imagen.anchor = "A1"
        hoja.merge_cells("A1:D5")
        hoja.add_image(imagen)
        # Agregar el título
        hoja.merge_cells("A6:D10")
        celda_titulo = hoja["A6"]
        celda_titulo.value = f"MONITOREO DE PLUVIÓMETROS {proyectoname.upper()}"
        celda_titulo.font = Font(size=18, bold=True)
        celda_titulo.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        # Agregar el subtítuloS
        rango, texto = "A11:D12", "DATOS DEL EQUIPO"
        hoja.merge_cells(rango)
        celda = hoja[rango.split(":")[0]]
        celda.value = texto
        celda.font = Font(size=14, bold=True, color="FFFFFF")
        celda.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        celda.fill = color_fondo
        # Definir datos generales
        datosceldas = [("A13", "Nombre:"), ("A14", "Código:"), ("A15", "Este:"),
                    ("C13", "Norte:"), ("C14", "Elevación:"), ("C15", "Comentario:")]
        datoscombinados = [("B13", namepluvio), ("B14", infopluvio[3]), ("B15", infopluvio[4]),
                        ("D13", infopluvio[5]), ("D14", infopluvio[6]), ("D15", infopluvio[7])]
        for rango, texto in datosceldas:
            celda = hoja[rango]
            celda.value = texto
            celda.border = borde_negro
            celda.alignment = Alignment(horizontal="center", vertical="center")
            celda.font = Font(bold=True, color="FFFFFF")
            celda.fill = color_fondo
        for rango, texto in datoscombinados:
            hoja.merge_cells(rango)
            celda = hoja[rango.split(":")[0]]
            celda.value = texto
            celda.border = borde_negro
            celda.alignment = Alignment(horizontal="left")
        # Agregar bordes a las celdas fusionadas
        for rango in ["A1:D5", "A6:D10", "A11:D12"]:
            for fila_celdas in hoja[rango]:
                for celda in fila_celdas:
                    celda.border = borde_negro
        # Fila de encabezados detallados
        encabezados = ["Fecha", "Hora", "Precipitación (mm)", "Observación"]
        for col, encabezado in enumerate(encabezados, 1):
            hoja[chr(64 + col) + "17"].value = encabezado
            celda = hoja[chr(64 + col) + "17"]
            celda.font = Font(bold=True, color="FFFFFF")
            celda.alignment = Alignment(horizontal="center", vertical="center")
            celda.fill = color_fondo
            celda.border = borde_negro
    
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
                    hoja.append(fila)
                cont += 1
        rutaexcel = resource_path("resources/workspace/dataequipos.xlsx")
        libro.save(rutaexcel)
        archivo_destino, _ = QFileDialog.getSaveFileName(None, "Guardar Excel en", "", "Archivos de Excel (*.xlsx);;Todos los archivos (*)")
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
        color_fondo = PatternFill(start_color="00796B", end_color="00796B", fill_type="solid")
        borde_negro = Border(left=Side(style="thin", color="000000"), right=Side(style="thin", color="000000"),
                            top=Side(style="thin", color="000000"), bottom=Side(style="thin", color="000000"))
        # Ajustar el ancho de las columnas para mejor presentación
        for col in range(1, 11):  # 10 columnas de ancho
            hoja.column_dimensions[chr(64 + col)].width = 20
        # Ajustar el alto de las filas de 1 a 5 para el área de la imagen
        for row in range(1, 6):
            hoja.row_dimensions[row].height = 25
        # Ruta de la imagen
        if logo:
            imagen_stream = MetodosGenerales.convertirBlobImagen(logo)
            imagen = ExcelImage(imagen_stream)
        else:
            ui_file_path = resource_path("resources/logo.png")
            imagen = ExcelImage(ui_file_path)
        imagen.width = 550
        imagen.height = 150
        imagen.anchor = "A1"
        hoja.merge_cells("A1:D5")
        hoja.add_image(imagen)
        # Agregar el título
        hoja.merge_cells("E1:I5")
        celda_titulo = hoja["E1"]
        celda_titulo.value = f"MONITOREO DE CELDAS DE ASENTAMIENTO {proyectoname.upper()}"
        celda_titulo.font = Font(size=18, bold=True)
        celda_titulo.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        # Agregar el subtítuloS
        cabeceraGeneral = [("A7:C8", "DATOS DEL SENSOR"), ("D7:G8", "DATOS DE INSTALACIÓN"), ("H7:I8", "DATOS DE CALIBRACIÓN")]
        for rango, texto in cabeceraGeneral:
            hoja.merge_cells(rango)
            celda = hoja[rango.split(":")[0]]
            celda.value = texto
            celda.font = Font(size=14, bold=True, color="FFFFFF")
            celda.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            celda.fill = color_fondo
        # Definir datos generales
        datosceldas = [("A9", "Nombre:"), ("A10", "Marca:"), ("A11", "Modelo:"), ("A12", "Serie:"),
                    ("H9", "C.F.:"), ("H10", "T.K.:"), ("H11", "Temperatura:"), ("H12", "Rango:"), ("I9", infocelda[13]),
                    ("I10", infocelda[14]), ("I11", infocelda[12]), ("I12", infocelda[6])]
        datoscombinados = [("B9:C9", namecelda), ("B10:C10", infocelda[3]), ("B11:C11", infocelda[4]), ("B12:C12", infocelda[5]),
                        ("D9:E9", "Cota Instalación (m.s.n.m):"), ("D10:E10", "Cota Fundación (m.s.n.m):"),
                        ("D11:E11", "Coordenada Este:"), ("D12:E12", "Coordenada Norte:"),
                        ("F9:G9", infocelda[9]), ("F10:G10", infocelda[10]), ("F11:G11", infocelda[7]), ("F12:G12", infocelda[8])]
        for rango, texto in datosceldas:
            celda = hoja[rango]
            celda.value = texto
            if rango.startswith("F") or rango.startswith("I"):
                celda.alignment = Alignment(horizontal="center", vertical="center")
            else:
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
        # Agregar bordes a las celdas fusionadas
        rangosceldas = ["A1:D5", "E1:I5", "A7:C8", "D7:G8", "H7:I8", "A9:I12"]
        for rango in rangosceldas:
            for fila_celdas in hoja[rango]:
                for celda in fila_celdas:
                    celda.border = borde_negro
        # Fila de encabezados detallados
        encabezados = ["Fecha", "Hora", "Frecuencia (Digits)", "Frecuencia (Hz)", "Temperatura (°C)", "Desplazamiento (m)", "Cota (m.s.n.m)", "Superficie (m.s.n.m)", "Observación"]
        for col, encabezado in enumerate(encabezados, 1):
            hoja[chr(64 + col) + "14"].value = encabezado
            celda = hoja[chr(64 + col) + "14"]
            celda.font = Font(bold=True, color="FFFFFF")
            celda.alignment = Alignment(horizontal="center", vertical="center")
            celda.fill = color_fondo
            celda.border = borde_negro
    
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
                    hoja.append(fila)
                cont += 1
        rutaexcel = resource_path("resources/workspace/dataequipos.xlsx")
        libro.save(rutaexcel)
        archivo_destino, _ = QFileDialog.getSaveFileName(None, "Guardar Excel en", "", "Archivos de Excel (*.xlsx);;Todos los archivos (*)")
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
        color_fondo = PatternFill(start_color="00796B", end_color="00796B", fill_type="solid")
        borde_negro = Border(left=Side(style="thin", color="000000"), right=Side(style="thin", color="000000"),
                            top=Side(style="thin", color="000000"), bottom=Side(style="thin", color="000000"))
        # Ajustar el ancho de las columnas para mejor presentación
        for col in range(1, 6):  # 5 columnas de ancho
            hoja.column_dimensions[chr(64 + col)].width = 20
        # Ajustar el alto de las filas de 1 a 5 para el área de la imagen
        for row in range(1, 6):
            hoja.row_dimensions[row].height = 25
        # Ruta de la imagen
        if logo:
            imagen_stream = MetodosGenerales.convertirBlobImagen(logo)
            imagen = ExcelImage(imagen_stream)
        else:
            ui_file_path = resource_path("resources/logo.png")
            imagen = ExcelImage(ui_file_path)
        imagen.width = 550
        imagen.height = 150
        imagen.anchor = "A1"
        hoja.merge_cells("A1:E5")
        hoja.add_image(imagen)
        # Agregar el título
        hoja.merge_cells("A6:E10")
        celda_titulo = hoja["A6"]
        celda_titulo.value = f"MONITOREO DE ACELERÓGRAFOS {proyectoname.upper()}"
        celda_titulo.font = Font(size=18, bold=True)
        celda_titulo.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        # Agregar el subtítuloS
        rango, texto = "A11:E12", "DATOS DEL EQUIPO"
        hoja.merge_cells(rango)
        celda = hoja[rango.split(":")[0]]
        celda.value = texto
        celda.font = Font(size=14, bold=True, color="FFFFFF")
        celda.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        celda.fill = color_fondo
        # Definir datos generales
        datosceldas = [("A13", "Nombre:"), ("A14", "Este:"), ("C13", "Norte:"), ("C14", "Elevación:"),
                       ("B13", namepluvio), ("B14", infoacelero[3])]
        datoscombinados = [("D13:E13", infoacelero[4]), ("D14:E14", infoacelero[5])]
        for rango, texto in datosceldas:
            celda = hoja[rango]
            celda.value = texto
            celda.border = borde_negro
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
        # Agregar bordes a las celdas fusionadas
        for rango in ["A1:E5", "A6:E10", "A11:E12", "D13:E13", "D14:E14"]:
            for fila_celdas in hoja[rango]:
                for celda in fila_celdas:
                    celda.border = borde_negro
        # Fila de encabezados detallados
        encabezados = ["Fecha", "Hora", "Magnitud", "Distancia (Km)", "Observación"]
        for col, encabezado in enumerate(encabezados, 1):
            hoja[chr(64 + col) + "16"].value = encabezado
            celda = hoja[chr(64 + col) + "16"]
            celda.font = Font(bold=True, color="FFFFFF")
            celda.alignment = Alignment(horizontal="center", vertical="center")
            celda.fill = color_fondo
            celda.border = borde_negro
    
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
                                    sheet.append(fila)
                        # Guardar en memoria
                        excel_stream = io.BytesIO()
                        workbook.save(excel_stream)
                        excel_stream.seek(0)
                        # Nombre del archivo Excel dentro del ZIP
                        excel_name = f"{nombretdr}.xlsx"
                        zipf.writestr(excel_name, excel_stream.getvalue())
            # Guardar ZIP en una ubicación elegida por el usuario
            archivo_destino, _ = QFileDialog.getSaveFileName(None, "Guardar ZIP en", "", "Archivos ZIP (*.zip);;Todos los archivos (*)")
            if archivo_destino:
                if not archivo_destino.lower().endswith('.zip'):
                    archivo_destino += '.zip'
                shutil.copy(zip_filename, archivo_destino)
                mostrar_mensaje("Data Exportada", f"El ZIP se ha guardado en: {archivo_destino}", "informacion")
        except Exception as e:
            mostrar_mensaje("Error al Exportar", f"No se pudo guardar el ZIP: {str(e)}", "advertencia")
    
    def configurarCabeceraHojaSondajetdr(hoja, infotdr, proyectoname, nametdr, logo):
        # Definir colores, bordes, y otros atributos comunes
        color_fondo = PatternFill(start_color="00796B", end_color="00796B", fill_type="solid")
        borde_negro = Border(left=Side(style="thin", color="000000"), right=Side(style="thin", color="000000"),
                            top=Side(style="thin", color="000000"), bottom=Side(style="thin", color="000000"))
        # Ajustar el ancho de las columnas para mejor presentación
        for col in range(1, 6):  # 5 columnas de ancho
            hoja.column_dimensions[chr(64 + col)].width = 20
        # Ajustar el alto de las filas de 1 a 5 para el área de la imagen
        for row in range(1, 6):
            hoja.row_dimensions[row].height = 25
        # Ruta de la imagen
        if logo:
            imagen_stream = MetodosGenerales.convertirBlobImagen(logo)
            imagen = ExcelImage(imagen_stream)
        else:
            ui_file_path = resource_path("resources/logo.png")
            imagen = ExcelImage(ui_file_path)
        imagen.width = 550
        imagen.height = 150
        imagen.anchor = "A1"
        hoja.merge_cells("A1:E5")
        hoja.add_image(imagen)
        # Agregar el título
        hoja.merge_cells("A6:E9")
        celda_titulo = hoja["A6"]
        celda_titulo.value = f"MONITOREO DE EQUIPOS TDR {proyectoname.upper()}"
        celda_titulo.font = Font(size=18, bold=True)
        celda_titulo.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        # Agregar el subtítuloS
        rango, texto = "A10:E11", "DATOS DEL EQUIPO"
        hoja.merge_cells(rango)
        celda = hoja[rango.split(":")[0]]
        celda.value = texto
        celda.font = Font(size=14, bold=True, color="FFFFFF")
        celda.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        celda.fill = color_fondo
        # Definir datos generales
        datosceldas = [("A12", "Nombre:"), ("A13", "Este:"), ("A14", "Norte:"), ("A15", "Elevación:"),
                       ("B12", nametdr), ("B13", infotdr[2]), ("B14", infotdr[3]), ("B15", infotdr[4]),
                       ("C12", "Profundidad:"), ("C13", "Inclinación:"), ("C14", "Azimuth:"), ("C15", "Comentario:")]
        datoscombinados = [("D12:E12", infotdr[5]), ("D13:E13", infotdr[6]),
                           ("D14:E14", infotdr[7]), ("D15:E15", infotdr[8])]
        for rango, texto in datosceldas:
            celda = hoja[rango]
            celda.value = texto
            celda.border = borde_negro
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
        # Agregar bordes a las celdas fusionadas
        for rango in ["A1:E5", "A6:E9", "A10:E11", "D12:E12", "D13:E13", "D14:E14", "D15:E15"]:
            for fila_celdas in hoja[rango]:
                for celda in fila_celdas:
                    celda.border = borde_negro
        # Fila de encabezados detallados
        encabezados = ["Fecha", "Hora", "Profundidad (m)", "Impedancia", "Observación"]
        for col, encabezado in enumerate(encabezados, 1):
            hoja[chr(64 + col) + "17"].value = encabezado
            celda = hoja[chr(64 + col) + "17"]
            celda.font = Font(bold=True, color="FFFFFF")
            celda.alignment = Alignment(horizontal="center", vertical="center")
            celda.fill = color_fondo
            celda.border = borde_negro
    
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
                    hoja.append(fila)
                cont += 1
        rutaexcel = resource_path("resources/workspace/dataequipos.xlsx")
        libro.save(rutaexcel)
        archivo_destino, _ = QFileDialog.getSaveFileName(None, "Guardar Excel en", "", "Archivos de Excel (*.xlsx);;Todos los archivos (*)")
        if archivo_destino:
            # Asegurarse de que el archivo tenga la extensión .xlsx
            if not archivo_destino.lower().endswith('.xlsx'):
                archivo_destino += '.xlsx'
            try:
                shutil.copy(rutaexcel, archivo_destino)
                mostrar_mensaje("Data Exportada", f"El Excel se ha guardado en: {archivo_destino}", "informacion")
            except Exception as e:  # Captura cualquier excepción
                mostrar_mensaje("Error al Exportar", f"No se pudo guardar el Excel: {str(e)}", "advertencia")
    
    def configurarCabeceraHojaCotaTerreno(hoja, proyectoname, namepluvio, logo):
        # Definir colores, bordes, y otros atributos comunes
        color_fondo = PatternFill(start_color="00796B", end_color="00796B", fill_type="solid")
        borde_negro = Border(left=Side(style="thin", color="000000"), right=Side(style="thin", color="000000"),
                            top=Side(style="thin", color="000000"), bottom=Side(style="thin", color="000000"))
        # Ajustar el ancho de las columnas para mejor presentación
        for col in range(1, 5):  # 4 columnas de ancho
            hoja.column_dimensions[chr(64 + col)].width = 20
        # Ajustar el alto de las filas de 1 a 5 para el área de la imagen
        for row in range(1, 6):
            hoja.row_dimensions[row].height = 25
        # Ruta de la imagen
        if logo:
            imagen_stream = MetodosGenerales.convertirBlobImagen(logo)
            imagen = ExcelImage(imagen_stream)
        else:
            ui_file_path = resource_path("resources/logo.png")
            imagen = ExcelImage(ui_file_path)
        imagen.width = 550
        imagen.height = 150
        imagen.anchor = "A1"
        hoja.merge_cells("A1:D5")
        hoja.add_image(imagen)
        # Agregar el título
        hoja.merge_cells("A6:D10")
        celda_titulo = hoja["A6"]
        celda_titulo.value = f"DATA DE COTA DE TERRENO {namepluvio.upper()} - {proyectoname.upper()}"
        celda_titulo.font = Font(size=18, bold=True)
        celda_titulo.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        # Agregar bordes a las celdas fusionadas
        for rango in ["A1:D5", "A6:D10"]:
            for fila_celdas in hoja[rango]:
                for celda in fila_celdas:
                    celda.border = borde_negro
        # Fila de encabezados detallados
        encabezados = ["Fecha", "Hora", "Cota (msnm)", "Observación"]
        for col, encabezado in enumerate(encabezados, 1):
            hoja[chr(64 + col) + "12"].value = encabezado
            celda = hoja[chr(64 + col) + "12"]
            celda.font = Font(bold=True, color="FFFFFF")
            celda.alignment = Alignment(horizontal="center", vertical="center")
            celda.fill = color_fondo
            celda.border = borde_negro
    
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
    