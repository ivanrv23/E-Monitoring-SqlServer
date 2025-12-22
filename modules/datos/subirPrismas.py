import csv
import chardet
import unicodedata
import re
import pandas as pd
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QComboBox, QFileDialog, QHeaderView, QPushButton, QMenu, QTableWidget,
                        QFormLayout, QRadioButton, QDialogButtonBox, QMessageBox, QLabel, QLineEdit, QTreeWidget, QTableView)
from PySide6.QtGui import QIcon, QPen, QColor, QIcon
from PySide6.QtCore import Qt
from PySide6.QtUiTools import QUiLoader
from datetime import datetime,time
from utils.shared.arbolmarcado import TreeCheckbox
from utils.common.rutasarchivos import resource_path
from utils.generic.cargariconos import cargarIcono
from utils.shared.pegarDatosTabla import configurar_tabla_para_pegado
from utils.common.alertas import mostrar_mensaje
from controllers.InterfazController import InterfazController
from controllers.DatosController import DatosController
from controllers.ProyectoController import ProyectoController
from utils.common.metodosGenerales import MetodosGenerales
from controllers.PrismaController import PrismaController

# Pintar columna oculta de tabla
class CustomHeaderView(QHeaderView):
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
    
    def paintSection(self, painter, rect, logicalIndex):
        super().paintSection(painter, rect, logicalIndex)
        
        # Verificar si la columna siguiente está oculta para dibujar la línea doble
        table_widget = self.parent()
        if logicalIndex < table_widget.columnCount() - 1 and table_widget.isColumnHidden(logicalIndex + 1):
            painter.save()
            # pen = QPen(QColor(100, 100, 100), 2, Qt.SolidLine)  # Línea de color gris oscuro
            pen = QPen(QColor(255, 0, 0), 2, Qt.SolidLine)  # Cambia el color a rojo
            painter.setPen(pen)

            # Dibujar la primera línea
            painter.drawLine(rect.right() - 2, rect.top(), rect.right() - 2, rect.bottom())

            # Dibujar la segunda línea para el efecto de línea doble
            painter.drawLine(rect.right() - 6, rect.top(), rect.right() - 6, rect.bottom())
            painter.restore()

class SubirPrismas:
    
    HEADERS = {
        "UNO": {
            'columns': [
                'State', 'Point ID', 'Profile Name', 'Time', 'Hz', 'V', 'D [m]',
                'PPM Type', 'PPM', 'Pressure [mBar]', 'Av Temp [°C]', 'Add Const [m]',
                'Target Easting [m]', 'Target Northing [m]', 'Target Elevation [m]',
                'Reflector Height [m]', 'Instrument Height [m]', 'Station Easting [m]',
                'Station Northing [m]', 'Station Height [m]', 'Null Measurement [m]',
                'Short Time Diff [m]', 'Long Time Diff [m]', 'Vel Limit Diff [m]',
                'Horz Distance [m]', 'Difference Outlier Test [m]',
                'Longitudinal Displacement [m]', 'Transverse Displacement [m]',
                'Height Displacement [m]', 'Point group'
            ]
        },
        "DOS": {
            'columns': [
                'Point ID', 'Hz.Angle(g)', 'V.Angle(g)', 'Slope Dist.(m)',
                'Refl.Ht.(m)', 'Inst.Ht.(m)', 'Easting(m)', 'Northing(m)',
                'Height(m)', 'Day', 'Month', 'Year', 'Hour', 'Min'
            ]
        },
        "TRES": {
            'columns': [
                'PointNo', 'CustomText1', 'TargetPtID', 'State', 'Time', 'H', 'V',
                'D', 'TargetEasting', 'TargetNorthing', 'TargetElevation',
                'DiffFromNullMeas', 'TransverseDisplacement', 'HeightDisplacement',
                'Magnitude2D', 'Magnitude3D', 'Trend', 'Plunge', 'ProfileName',
                'NullMeasurement', 'PPMType', 'PPM', 'Pressure', 'Av_Temp',
                'AddConst', 'ReflectorHeight', 'InstrumentHeight', 'StationEasting',
                'StationNorthing', 'StationHeight', 'ShortTimeDiff', 'LongTimeDiff',
                'VelLimitDiff', 'DistProfileDirection', 'HorzDistance',
                'DifferenceOutlierTest'
            ]
        },
        "CUATRO": {
            'columns': [
                'State', 'Point ID', 'Time', 'Target Easting [m]', 'Target Northing [m]', 'Target Elevation [m]', 'D [m]',
                'Hz', 'V', 'PPM', 'Long Time Diff [m]', 'Vel Limit Diff [m]', 'Difference Outlier Test [m]',
                'Longitudinal Displacement [m]', 'Transverse Displacement [m]', 'Height Displacement [m]'
            ]
        },
        "CINCO": {
            'columns': [
                'FECHA', 'POINT ID', 'TARGET EASTING', 'TARGET NORTHING (m)', 'TARGET ELEVATION (m)', 'REFLECTOR HEIGHT (m)', 'Instrument Height(m)',
                'State', 'Station Easting','Station Northing','Station Height','Null Measurement','Short Time Diff (m)','Long Time (m)','','Horz Distance (m)',
                'Difference Outlier Test (m)','Longitudinal Displacement (m)','Transverse Displacement (m)','Height Displacement (m)','Point group','Hz (dms)',
                'V (dms)','D (m)', 'PPM Type','PPM','','','Add Const (m)'
            ]
        }
    }
    
    def cargarPrismasAutomatizados(main, idproyecto):
        loader = QUiLoader()
        ui_file_path = resource_path("ui/cargardataprismas.ui")
        ui_file = loader.load(ui_file_path, None)
        dialog = QDialog()
        dialog.setWindowTitle("Subir Prismas CSV o TXT")
        layout = QVBoxLayout()
        layout.addWidget(ui_file)
        dialog.setLayout(layout)
        # Obtener elementos para interactuar
        combocomponente = dialog.findChild(QComboBox, "combo_componentes")
        inputarchivos = dialog.findChild(QLineEdit, "input_archivos")
        btnsubirdata = dialog.findChild(QPushButton, "btn_subir_archivos")
        svg_icon_path = resource_path("resources/iconos/fontawesome/solid/arrow-up-from-bracket.svg")
        icon = QIcon(svg_icon_path)
        btnsubirdata.setIcon(icon)
        radioactualizar = dialog.findChild(QRadioButton, "radio_actualizar")
        radioremplazar = dialog.findChild(QRadioButton, "radio_remplazar")
        lblrespuesta = dialog.findChild(QLabel, "label_mensaje")
        botonguardar = dialog.findChild(QPushButton, "btn_cargar")
        # cargar data componentes
        componentes = ProyectoController.ctrlObtenerComponentesProyecto(idproyecto)
        if componentes:
            for fila in componentes:
                combocomponente.addItem(str(fila[2]), fila[0])
            combocomponente.setEnabled(True)
        else:
            combocomponente.setEnabled(False)
        archivo_ruta_completa = []
        def seleccionar_archivo():
            archivo, _ = QFileDialog.getOpenFileName(None, "Subir Prismas", "", "Archivos (*.csv *.txt)")
            if archivo:
                archivo_ruta_completa.clear()
                archivo_ruta_completa.append(archivo)
                inputarchivos.setText(archivo.split('/')[-1])
                lblrespuesta.setText("")
        def guardarDataPrismas():
            if not archivo_ruta_completa:
                lblrespuesta.setText("No existe archivo.")
                lblrespuesta.setStyleSheet("color: red;")
                return
            idcompo = combocomponente.currentData()
            namecompo = combocomponente.currentText()
            if radioactualizar.isChecked():
                tipodata = 1
            elif radioremplazar.isChecked():
                tipodata = 2
            SubirPrismas.cargar_archivo(main, idproyecto, idcompo, namecompo, tipodata, lblrespuesta, archivo_ruta_completa)
        # Inicializar botones
        lblrespuesta.setText("")
        btnsubirdata.clicked.connect(seleccionar_archivo)
        botonguardar.clicked.connect(guardarDataPrismas)
        dialog.exec()
    
    def detectar_delimitador(ruta_archivo, encoding):
        try:
            with open(ruta_archivo, 'r', encoding=encoding) as f:
                sample = f.readline()
                dialect = csv.Sniffer().sniff(sample, delimiters=[',', ';'])
                return dialect.delimiter
        except csv.Error:
            return None
    
    def cargar_archivo(main, idproyecto, idcompo, namecompo, tipodata, lblrespuesta, archivo_ruta_completa):
        # Obtener la codificación detectada
        encoding = SubirPrismas.validar_formato(archivo_ruta_completa)
        try:
            # Leer el archivo en bloques
            delimitador = SubirPrismas.detectar_delimitador(archivo_ruta_completa[0], encoding)
            if delimitador:
                chunksize = 10**6
                for chunk in pd.read_csv(archivo_ruta_completa[0], encoding=encoding, sep=delimitador, chunksize=chunksize):
                    # Obtener la primera fila que contiene el encabezado
                    encabezado_csv = chunk.columns.tolist()
                    respuesta, tipoencabezado = SubirPrismas.validarEncabezadoArchivo(encabezado_csv)
                    if respuesta:
                        SubirPrismas.registar_prismas_encabezado(main, idproyecto, idcompo, namecompo, tipodata, lblrespuesta, archivo_ruta_completa[0], encoding, tipoencabezado, delimitador)
                        break  # Si el encabezado es correcto, no necesitamos leer más bloques
                    else:
                        lblrespuesta.setText("Archivo incorrecto.")
                        lblrespuesta.setStyleSheet("color: orange;")
                        break  # Si el encabezado no coincide, no necesitamos leer más bloques
            else:
                lblrespuesta.setText("El archivo tiene delimitador incorrecto.")
                lblrespuesta.setStyleSheet("color: orange;")
        except FileNotFoundError:
            lblrespuesta.setText("Archivo no encontrado.")
            lblrespuesta.setStyleSheet("color: red;")
        except pd.errors.ParserError:
            lblrespuesta.setText("Error al analizar el archivo.")
            lblrespuesta.setStyleSheet("color: red;")
        except Exception as e:
            lblrespuesta.setText(f"Error al cargar archivo.")
            lblrespuesta.setStyleSheet("color: red;")    
    
    def normalizar_texto(texto):
        # Normaliza eliminando caracteres no ASCII (acentos y caracteres especiales)
        texto_normalizado = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii').strip()
        # Convierte a minúsculas para ignorar diferencias entre mayúsculas y minúsculas
        texto_normalizado = texto_normalizado.lower()
        # Reemplaza "i12" por una cadena vacía y elimina cualquier otro carácter no alfanumérico
        texto_limpio = re.sub(r'i12|[^a-zA-Z0-9\s]', '', texto_normalizado)
        return texto_limpio

    def validarEncabezadoArchivo(encabezado_csv):
        try:
            # Normaliza el encabezado del archivo
            encabezado_normalizado = [SubirPrismas.normalizar_texto(col) for col in encabezado_csv]
            # Itera sobre los formatos de encabezado esperados
            for formato, config in SubirPrismas.HEADERS.items():
                formato_normalizado = [SubirPrismas.normalizar_texto(col) for col in config['columns']]
                # Compara solo las columnas que tienen nombre, ignorando las vacías
                if len(encabezado_normalizado) != len(formato_normalizado):
                    continue

                coincide = True
                for col_archivo, col_formato in zip(encabezado_normalizado, formato_normalizado):
                    if col_formato and col_archivo != col_formato:
                        coincide = False
                        break

                if coincide:
                    return True, formato

            # Si no se encontró coincidencia
            return False, None

        except Exception as e:
            print(f"Error durante la validación: {e}")
            return False, None
    
    def registar_prismas_encabezado(main, idproyecto, idcompo, namecompo, tipodata, lblrespuesta, datos, encoding, tipoencabezado, delimitador):
        respuesta, equipos = False, []
        if tipoencabezado == "UNO": # LA ARENA
            respuesta, equipos = DatosController.ctrlRegistrarPrismasAutomatizadosUno(idproyecto, tipodata, datos, encoding, idcompo, delimitador)
        elif tipoencabezado == "DOS": # CHINALCO
            respuesta, equipos = DatosController.ctrlRegistrarPrismasAutomatizadosDos(idproyecto, tipodata, datos, encoding, idcompo, delimitador)
        elif tipoencabezado == "TRES": # LAS BAMBAS
            respuesta, equipos = DatosController.ctrlRegistrarPrismasAutomatizadosTres(idproyecto, tipodata, datos, encoding, idcompo, delimitador)
        elif tipoencabezado == "CUATRO": # LAS BAMBAS TSF
            respuesta, equipos = DatosController.ctrlRegistrarPrismasAutomatizadosCuatro(idproyecto, tipodata, datos, encoding, idcompo, delimitador)
        elif tipoencabezado == "CINCO": # LA ARENA 2
            respuesta, equipos = DatosController.ctrlRegistrarPrismasAutomatizadosCinco(idproyecto, tipodata, datos, encoding, idcompo, delimitador)
        if respuesta:
            registro, prismasnuevos = DatosController.ctrlRegistrarEquipoZona(idproyecto, idcompo, equipos, f'prismas{idproyecto}', 'PRISMAS')
            if registro:
                if prismasnuevos:
                    prismas = InterfazController.ctrlListarPrismasAutoNuevosComponente(idcompo, 'PRISMAS', prismasnuevos)
                    if prismas:
                        treewidgetdatos = main.findChild(QTreeWidget, "tree_actual_datos")
                        treewidgetvisor = main.findChild(QTreeWidget, "tree_actual_visor")
                        treewidgetdespla = main.findChild(QTreeWidget, "tree_actual_desplazamiento")
                        treewidgetveloci = main.findChild(QTreeWidget, "tree_actual_velocidad")
                        treewidgetanalisis = main.findChild(QTreeWidget, "tree_actual_analisis")
                        if tipodata == 2:  # reemplazar
                            for nombre in prismas:
                                TreeCheckbox.eliminarCheckboxPrisma(treewidgetdatos, "Prismas", idcompo, "prisma", nombre[3], f"prismas{idproyecto}")
                                TreeCheckbox.eliminarCheckboxPrisma(treewidgetvisor, "Prismas", idcompo, "prisma", nombre[3], f"prismas{idproyecto}")
                                TreeCheckbox.eliminarCheckboxPrisma(treewidgetdespla, "Prismas", idcompo, "prisma", nombre[3], f"prismas{idproyecto}")
                                TreeCheckbox.eliminarCheckboxPrisma(treewidgetveloci, "Prismas", idcompo, "prisma", nombre[3], f"prismas{idproyecto}")
                                TreeCheckbox.eliminarCheckboxPrisma(treewidgetanalisis, "Prismas", idcompo, "prisma", nombre[3], f"prismas{idproyecto}")
                        # añadir a checkbox
                        TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetdatos, namecompo, idcompo, idproyecto, "Prismas", "1", prismas, "prisma")
                        TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetvisor, namecompo, idcompo, idproyecto, "Prismas", "2", prismas, "prisma")
                        TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetdespla, namecompo, idcompo, idproyecto, "Prismas", "1", prismas, "prisma")
                        TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetveloci, namecompo, idcompo, idproyecto, "Prismas", "1", prismas, "prisma")
                        TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetanalisis, namecompo, idcompo, idproyecto, "Prismas", "1", prismas, "prisma")
                        # actualizar combos analisis
                        from views.analisis_view import AnalisisView
                        AnalisisView.cargarPrismasCombosAnalisis(main, idproyecto)
                lblrespuesta.setText("Guardado correctamente.")
                lblrespuesta.setStyleSheet("color: green;")
            else:
                lblrespuesta.setText("Se generó un error al actualizar instrumentación.")
                lblrespuesta.setStyleSheet("color: red;")
        else:
            lblrespuesta.setText("Se generó un error al guardar prismas.")
            lblrespuesta.setStyleSheet("color: red;")
    
    def validar_formato(archivo_ruta_completa):
        # Función para revisar caracteres problemáticos en una lista de líneas
        def revisar_caracteres_erroneos(lineas):
            for linea in lineas:
                try:
                    # Intentar normalizar la línea a ASCII
                    unicodedata.normalize('NFKD', linea).encode('ascii', 'ignore').decode('ascii')
                except UnicodeEncodeError:
                    return False  # Si hay un error de codificación, retornar False
            return True

        # Intentar con la codificación detectada
        def validar_lectura_archivo(archivo, encoding):
            try:
                with open(archivo, 'r', encoding=encoding) as f:
                    lector_csv = csv.reader(f)
                    # Leer unas pocas líneas para la validación de caracteres problemáticos
                    lineas_archivo = [','.join(next(lector_csv)) for _ in range(5)]
                    return revisar_caracteres_erroneos(lineas_archivo)
            except (UnicodeDecodeError, StopIteration, csv.Error) as e:
                return False

        if archivo_ruta_completa:
            archivo = archivo_ruta_completa if isinstance(archivo_ruta_completa, str) else archivo_ruta_completa[0]

            # Verificar la extensión del archivo
            if archivo.endswith('.csv') or archivo.endswith('.txt'):
                # Detectar la codificación del archivo
                with open(archivo, 'rb') as f:
                    raw_data = f.read(20)  # Leer una muestra para análisis
                    resultado = chardet.detect(raw_data)
                    encoding_detectada = resultado['encoding']
                    confidence = resultado['confidence']
                # Si la confianza es baja, probar con codificaciones comunes
                if confidence < 0.90:
                    for encoding in ['utf-8', 'latin-1', 'ascii']:
                        if validar_lectura_archivo(archivo, encoding):
                            return encoding
                else:
                    if validar_lectura_archivo(archivo, encoding_detectada):
                        return encoding_detectada
                    else:
                        if validar_lectura_archivo(archivo, 'latin-1'):
                            return 'latin-1'
                return None
            else:
                return None
        else:
            return None
    
    ############################ PRISMAS MANUALES  ############################
    def cargarPrismasManuales(main, idproyecto):
        loaderLoading = QUiLoader()
        ui_file_path = resource_path("ui/prismasmanuales.ui")
        ui_file = loaderLoading.load(ui_file_path, None)
        dialogoPrisma = QDialog()
        dialogoPrisma.setWindowTitle("Data Prismas Manuales")
        layout_procesar_data = QVBoxLayout()
        layout_procesar_data.addWidget(ui_file)
        dialogoPrisma.setLayout(layout_procesar_data)
        combocomponente = dialogoPrisma.findChild(QComboBox, "combo_componentes")
        botonguardar = dialogoPrisma.findChild(QPushButton, "btn_guardar_prismas")
        lblrespuesta = dialogoPrisma.findChild(QLabel, "label_mensaje")
        # cargar data componentes
        componentes = ProyectoController.ctrlObtenerComponentesProyecto(idproyecto)
        if len(componentes) > 0:
            for fila in componentes:
                combocomponente.addItem(str(fila[2]), fila[0])
            combocomponente.setEnabled(True)
        else:
            combocomponente.setEnabled(False)
            botonguardar.setEnabled(False)
        tabladata = dialogoPrisma.findChild(QTableWidget, "table_prismasmanuales_data")
        # agregar una celda a cada tabla
        row_position = tabladata.rowCount()
        tabladata.insertRow(row_position)
        # Configurar el menú contextual en la cabecera
        custom_header = CustomHeaderView(Qt.Horizontal, tabladata)
        tabladata.setHorizontalHeader(custom_header)
        header = tabladata.horizontalHeader()
        header.setContextMenuPolicy(Qt.CustomContextMenu)
        def mostrarMenuCabecera(pos):
            menu = QMenu()
            columna = header.logicalIndexAt(pos)
            if tabladata.isColumnHidden(columna):
                toggle_action = menu.addAction(f"Mostrar Columna '{tabladata.horizontalHeaderItem(columna).text()}'")
                toggle_action.triggered.connect(lambda: tabladata.showColumn(columna))
            else:
                toggle_action = menu.addAction(f"Ocultar Columna '{tabladata.horizontalHeaderItem(columna).text()}'")
                toggle_action.triggered.connect(lambda: tabladata.hideColumn(columna))
            if tabladata.isColumnHidden(columna + 1):
                # Buscar todas las columnas ocultas consecutivas y agregarlas al menú
                hidden_columns = []
                next_index = columna + 1
                while next_index < tabladata.columnCount() and tabladata.isColumnHidden(next_index):
                    hidden_columns.append(next_index)
                    next_index += 1
                # Agregar cada columna oculta consecutiva al menú
                for col in hidden_columns:
                    show_action = menu.addAction(f"Mostrar Columna '{tabladata.horizontalHeaderItem(col).text()}'")
                    show_action.triggered.connect(lambda checked, col=col: tabladata.showColumn(col))
            # Opción para mostrar todas las columnas
            show_all_action = menu.addAction("Mostrar Todas las Columnas")
            show_all_action.triggered.connect(lambda: [tabladata.showColumn(col) for col in range(tabladata.columnCount())])
            # Mostrar menu
            menu.exec(header.mapToGlobal(pos))
        # GUARDAR DATA DE TABLA PRISMAS MANUALES
        def guardarPrismasManualesTabla():
            filas = tabladata.rowCount()
            if filas > 0 and idproyecto != 0:
                data = []
                estado = False
                for row in range(filas):
                    datosfila = []
                    fila_valida = True
                    c = 0
                    for column in range(tabladata.columnCount()):
                        item = tabladata.item(row, column)
                        valor = item.text().strip() if item else ""
                        if valor != "":
                            if column == 1:
                                valor = MetodosGenerales.validarFormatoFecha(valor)
                                if not valor:
                                    mensaje = "La fecha no tiene un formato adecuado."
                                    fila_valida = False
                                    break
                            elif column == 2:
                                valor = MetodosGenerales.validarFormatoHora(valor)
                                if not valor:
                                    mensaje = "La hora no tiene un formato adecuado."
                                    fila_valida = False
                                    break
                            elif column > 2 and column < 7:
                                if not MetodosGenerales.validarEsNumero(valor):
                                    mensaje = "Las lecturas deben ser numéricas."
                                    fila_valida = False
                                    break
                            elif column == 7 or column == 8:
                                if not MetodosGenerales.validarEsNumero(valor):
                                    if not MetodosGenerales.validarEsAngulo(valor):
                                        mensaje = "Los ángulos no tiene un formato válido."
                                        fila_valida = False
                                        break
                        else:
                            if column == 0:
                                fila_valida = False
                                mensaje = "El nombre del prisma está vacío."
                            elif column == 1:
                                fila_valida = False
                                mensaje = "La fecha está vacía."
                            elif column == 2:
                                valor = "00:00:00"
                            elif column == 3 or column == 4 or column == 5:
                                fila_valida = False
                                mensaje = "Las coordenadas están vacías."
                            elif column == 6 or column == 7 or column == 8:
                                valor = "0"
                            c += 1
                        datosfila.append(valor)
                    if c != 9:
                        if fila_valida and len(datosfila) == 9:
                            data.append(datosfila)
                            estado = True
                        else:
                            estado = False
                            break
                if estado:
                    idcompo = combocomponente.currentData()
                    namecompo = combocomponente.currentText()
                    respuesta, equipos = PrismaController.ctrlGuardarPrismasManualesTabla(idproyecto, data)
                    if respuesta:
                        registro, prismasnuevos = DatosController.ctrlRegistrarEquipoZona(idproyecto, idcompo, equipos, f'prismas{idproyecto}', 'PRISMAS')
                        if registro:
                            if prismasnuevos:
                                prismas = InterfazController.ctrlListarPrismasAutoNuevosComponente(idcompo, 'PRISMAS', prismasnuevos)
                                if prismas:
                                    treewidgetdatos = main.findChild(QTreeWidget, "tree_actual_datos")
                                    treewidgetvisor = main.findChild(QTreeWidget, "tree_actual_visor")
                                    treewidgetdespla = main.findChild(QTreeWidget, "tree_actual_desplazamiento")
                                    treewidgetveloci = main.findChild(QTreeWidget, "tree_actual_velocidad")
                                    treewidgetanalisis = main.findChild(QTreeWidget, "tree_actual_analisis")
                                    # añadir a checkbox
                                    TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetdatos, namecompo, idcompo, idproyecto, "Prismas", "1", prismas, "prisma")
                                    TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetvisor, namecompo, idcompo, idproyecto, "Prismas", "2", prismas, "prisma")
                                    TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetdespla, namecompo, idcompo, idproyecto, "Prismas", "1", prismas, "prisma")
                                    TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetveloci, namecompo, idcompo, idproyecto, "Prismas", "1", prismas, "prisma")
                                    TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetanalisis, namecompo, idcompo, idproyecto, "Prismas", "1", prismas, "prisma")
                                    # actualizar combos analisis
                                    from views.analisis_view import AnalisisView
                                    AnalisisView.cargarPrismasCombosAnalisis(main, idproyecto)
                            lblrespuesta.setText("Registrado Correctamente")
                            lblrespuesta.setStyleSheet("color: green;")
                            # Limpiar filas tabla
                            tabladata.setRowCount(0)
                            tabladata.insertRow(0)
                        else:
                            lblrespuesta.setText("Error al registrar el equipo en la zona.")
                            lblrespuesta.setStyleSheet("color: red;")
                    else:
                        lblrespuesta.setText("Error al registrar.")
                        lblrespuesta.setStyleSheet("color: red;")
                else:
                    lblrespuesta.setText(f"En la fila {len(data) + 1}: {mensaje}")
                    lblrespuesta.setStyleSheet("color: orange;")
            else:
                lblrespuesta.setText(f"No se puede guardar.")
                lblrespuesta.setStyleSheet("color: orange;")
        # conectar señales
        header.customContextMenuRequested.connect(mostrarMenuCabecera)
        tabladata.setContextMenuPolicy(Qt.CustomContextMenu)
        configurar_tabla_para_pegado(tabladata)
        botonguardar.clicked.connect(guardarPrismasManualesTabla)
        dialogoPrisma.exec()
    
    def cargarDataFormatosPrismas(main, idproyecto):
        loader = QUiLoader()
        ui_file_path = resource_path("ui/cargardataformato.ui")
        ui_file = loader.load(ui_file_path, None)
        dialogo = QDialog()
        dialogo.setWindowTitle("Data Prismas")
        layout_procesar_data = QVBoxLayout()
        layout_procesar_data.addWidget(ui_file)
        dialogo.setLayout(layout_procesar_data)
        ruta = "resources/iconos/fontawesome/solid/file-arrow-up.svg"
        botonSubir = dialogo.findChild(QPushButton, "btn_cargar_archivo")
        cargarIcono(botonSubir, ruta)
        ubicacion_archivo = dialogo.findChild(QLineEdit, "input_archivo")
        ubicacion_archivo.setReadOnly(True)
        comboComponentes = dialogo.findChild(QComboBox, "combo_componentes")
        labelRespuesta = dialogo.findChild(QLabel, "label_mensaje")
        botonAceptar = dialogo.findChild(QPushButton, "btn_aceptar")
        componentes = ProyectoController.ctrlObtenerComponentesProyecto(idproyecto)
        if len(componentes) > 0:
            for fila in componentes:
                comboComponentes.addItem(str(fila[2]), fila[0])
            comboComponentes.setEnabled(True)
        else:
            comboComponentes.addItem("Sin Componentes")
            comboComponentes.setEnabled(False)
            botonAceptar.setEnabled(False)
        def cargar_archivo():
            file_names, _ = QFileDialog.getOpenFileNames(None, "Cargar Archivos", "", "Archivos Excel (*.xlsx)")
            if file_names:
                ubicacion_archivo.setText("\n".join(file_names))
        def procesar_archivo():
            if not ubicacion_archivo.text().strip():
                labelRespuesta.setText("No se cargó ningún archivo.")
                labelRespuesta.setStyleSheet("color: red;")
                return
            else:
                try:
                    idcompo = comboComponentes.currentData()
                    namecompo = comboComponentes.currentText()
                    respuesta, equipos, erroneos = SubirPrismas.registrarDataPrismas(idproyecto, ubicacion_archivo.text())
                    if respuesta:
                        registro, prismasnuevos = DatosController.ctrlRegistrarEquipoZona(idproyecto, idcompo, equipos, f'prismas{idproyecto}', 'PRISMAS')
                        if registro:
                            ubicacion_archivo.clear()
                            if len(erroneos) > 0:
                                labelRespuesta.setText(f"Algunos archivos no se guardaron: {erroneos}")
                            else:
                                labelRespuesta.setText("Los prismas se guardaron correctamente.")
                            labelRespuesta.setStyleSheet("color: green;")
                            if prismasnuevos:
                                prismas = InterfazController.ctrlListarPrismasAutoNuevosComponente(idcompo, 'PRISMAS', prismasnuevos)
                                if prismas:
                                    treewidgetdatos = main.findChild(QTreeWidget, "tree_actual_datos")
                                    treewidgetvisor = main.findChild(QTreeWidget, "tree_actual_visor")
                                    treewidgetdespla = main.findChild(QTreeWidget, "tree_actual_desplazamiento")
                                    treewidgetveloci = main.findChild(QTreeWidget, "tree_actual_velocidad")
                                    treewidgetanalisis = main.findChild(QTreeWidget, "tree_actual_analisis")
                                    # añadir a checkbox
                                    TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetdatos, namecompo, idcompo, idproyecto, "Prismas", "1", prismas, "prisma")
                                    TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetvisor, namecompo, idcompo, idproyecto, "Prismas", "2", prismas, "prisma")
                                    TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetdespla, namecompo, idcompo, idproyecto, "Prismas", "1", prismas, "prisma")
                                    TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetveloci, namecompo, idcompo, idproyecto, "Prismas", "1", prismas, "prisma")
                                    TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetanalisis, namecompo, idcompo, idproyecto, "Prismas", "1", prismas, "prisma")
                                    # actualizar combos analisis
                                    from views.analisis_view import AnalisisView
                                    AnalisisView.cargarPrismasCombosAnalisis(main, idproyecto)
                    else:
                        if len(erroneos) > 0:
                            labelRespuesta.setText(f"Error en los archivos: {erroneos}")
                        else:
                            labelRespuesta.setText("No se guardó la data.")
                        labelRespuesta.setStyleSheet("color: red;")
                except ValueError as e:
                    labelRespuesta.setText(str(e))
                    labelRespuesta.setStyleSheet("color: red;")
        botonSubir.clicked.connect(cargar_archivo)
        botonAceptar.clicked.connect(procesar_archivo)
        dialogo.exec()
    
    def registrarDataPrismas(proyectoid, ubicacion):
        erroneos = []
        data = []
        equipos = []
        respuesta = False
        encabezado = ['Hito', 'Fecha', 'Hora', 'Este (m)', 'Norte (m)', 'Elevación (msnm)', 'Distancia Inclinada (m)', 'Ángulo Horizontal', 'Ángulo Vertical']
        archivos = ubicacion.split("\n")
        for file_name in archivos:
            file_name = file_name.strip()
            if not file_name or not file_name.endswith('.xlsx'):
                continue
            try:
                df_header = pd.read_excel(file_name, header=None, nrows=1, skiprows=10, engine='openpyxl')
                encabezados_archivo = [str(col).strip() for col in df_header.iloc[0, :len(encabezado)]]
                if encabezados_archivo != encabezado:
                    erroneos.append(file_name.split("/")[-1])
                    continue
                df = pd.read_excel(file_name, header=None, skiprows=11, engine='openpyxl')
                df.columns = ['nombre', 'fecha', 'hora', 'este', 'norte', 'elevacion', 'distancia', 'horizontal', 'vertical']
                for _, row in df.iterrows():
                    nombre = str(row['nombre']).strip()
                    fecha = row['fecha']
                    hora = row['hora']
                    este = row['este']
                    norte = row['norte']
                    elevacion = row['elevacion']
                    if not nombre or pd.isna(fecha) or pd.isna(este) or pd.isna(norte) or pd.isna(elevacion):
                        continue
                    # Manejo de la columna 'fecha'
                    if isinstance(fecha, (pd.Timestamp, datetime)):
                        fecha = fecha.date()  # Convertir a date
                        fecha = fecha.strftime('%Y-%m-%d')
                    elif isinstance(fecha, str):
                        fecha = MetodosGenerales.validarFormatoFecha(fecha)
                        if fecha is None:
                            continue
                    else:
                        continue
                    # Manejo de la columna 'hora'
                    if isinstance(hora, (pd.Timestamp, datetime)):
                        hora = hora.time()
                        hora = hora.strftime('%H:%M:%S')
                    elif isinstance(hora, time):
                        hora = hora.strftime('%H:%M:%S')
                    elif isinstance(hora, str):
                        hora = MetodosGenerales.validarFormatoHora(hora) or "00:00:00"
                    else:
                        hora = "00:00:00"
                    try:
                        distancia = float(row['distancia'])
                    except (ValueError, TypeError):
                        distancia = 0
                    horizontal = row['horizontal']
                    if pd.isna(horizontal):
                        horizontal = 0
                    elif not MetodosGenerales.validarEsNumero(horizontal) and not MetodosGenerales.validarEsAngulo(horizontal):
                        horizontal = 0
                    vertical = row['vertical']
                    if pd.isna(vertical):
                        vertical = 0
                    elif not MetodosGenerales.validarEsNumero(vertical) and not MetodosGenerales.validarEsAngulo(vertical):
                        vertical = 0
                    data.append((nombre, fecha, hora, este, norte, elevacion, distancia, horizontal, vertical))
            except Exception:
                erroneos.append(file_name.split("/")[-1])
        if data:
            respuesta, equipos = PrismaController.ctrlGuardarPrismasManualesTabla(proyectoid, data)
        return respuesta, equipos, erroneos
    
    def dardebaja_prismas(idzona, idproyecto, nombrezona, treewidget, nombregrupo, tipogrupo, reiniciarvistas, vista=None):
        dlg = QMessageBox()
        dlg.setWindowTitle("Dar de Baja Prismas")
        dlg.setText(f"¿Está seguro dar de baja a todos los prismas?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            respuesta = PrismaController.ctrlCambiarEstadoPrismas(0, idzona)
            if respuesta:
                TreeCheckbox.eliminarCheckboxGrupo(treewidget, idzona, nombregrupo, tipogrupo)
                # LISTAR PRISMAS DE BAJA
                if vista:
                    prismasbaja = InterfazController.ctrlListarPrismasComponente(idzona, 0)
                    if prismasbaja:
                        TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidget, nombrezona, idzona, idproyecto, "Prismas de Baja", "11", prismasbaja, "prismabaja")
                        reiniciarvistas("Prisma")
            else:
                mostrar_mensaje("Dar de Baja Prismas", "No se pudo dar de baja los prismas.", "advertencia")
    
    def eliminar_prismas(idzona, grupo, tipo, treewidget, reiniciarvistas):
        dlg = QMessageBox()
        dlg.setWindowTitle("Eliminar Prismas")
        dlg.setText(f"¿Está seguro eliminar todos los prismas?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            respuesta = PrismaController.ctrlEliminarPrismas(idzona)
            if respuesta:
                delete = PrismaController.ctrlEliminarDataPrismas(respuesta)
                if delete:
                    TreeCheckbox.eliminarCheckboxGrupo(treewidget, idzona, grupo, tipo)
                    reiniciarvistas("Prisma")
                else:
                    mostrar_mensaje("Eliminar Prismas", "Error al eliminar data prismas.", "advertencia")
            else:
                mostrar_mensaje("Eliminar Prismas", "No se pudo eliminar los prismas.", "advertencia")
    
    def dardealta_prismas(idzona, idproyecto, nombrezona, treewidget, reiniciarvistas):
        dlg = QMessageBox()
        dlg.setWindowTitle("Dar de Alta Prismas")
        dlg.setText(f"¿Está seguro dar de alta a todos los prismas?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            respuesta = PrismaController.ctrlCambiarEstadoPrismas(1, idzona)
            if respuesta:
                TreeCheckbox.eliminarCheckboxGrupo(treewidget, idzona, "Prismas de Baja", "11")
                # LISTAR PRISMAS DE ALTA
                prismasalta = InterfazController.ctrlListarPrismasComponente(idzona, 1)
                if prismasalta:
                    TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidget, nombrezona, idzona, idproyecto, "Prismas", "1", prismasalta, "prisma")
                    reiniciarvistas("Prisma")
            else:
                mostrar_mensaje("Dar de Alta Prismas", "No se pudo dar de alta los prismas.", "advertencia")
    
    def dardebaja_prisma(main, idproyecto, idzona, nombreprisma, idinstrumento, nombrezona, treewidget, reiniciarvistas, vista=None):
        dlg = QMessageBox()
        dlg.setWindowTitle("Dar de Baja Prisma")
        dlg.setText(f"¿Está seguro dar de baja al prisma '{nombreprisma}'?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            respuesta = PrismaController.ctrlCambiarPrismaEstado(0, idzona, idinstrumento)
            if respuesta:
                TreeCheckbox.eliminarCheckbox(treewidget, "Prismas", idinstrumento, "prisma")
                # LISTAR PRISMA DE BAJA
                if vista:
                    prismasbaja = InterfazController.ctrlListarComponentePrisma(idinstrumento, 0)
                    if prismasbaja:
                        TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidget, nombrezona, idzona, idproyecto, "Prismas de Baja", "11", prismasbaja, "prismabaja")
                reiniciarvistas("Prisma")
                # actualizar combos analisis
                from views.analisis_view import AnalisisView
                AnalisisView.cargarPrismasCombosAnalisis(main, idproyecto)
            else:
                mostrar_mensaje("Dar de Baja Prisma", "No se pudo dar de baja al prisma.", "advertencia")
    
    def cambiar_componente_prismas(idcomponente, idproyecto, treewidget, nombregrupo, tipogrupo, subgrupo, reiniciarvistas):
        dialog = QDialog()
        dialog.setWindowTitle("Cambiar Componente Prismas")
        layout = QFormLayout(dialog)
        # Campo componente
        label_titulo = QLabel("Componente:")
        combo_componente = QComboBox()
        label_mensaje = QLabel("")
        label_mensaje.setAlignment(Qt.AlignCenter)
        label_mensaje.setStyleSheet("QLabel { color: red; }")
        # cargar data componentes
        componentes = ProyectoController.ctrlObtenerComponentesProyecto(idproyecto)
        if componentes:
            for fila in componentes:
                combo_componente.addItem(str(fila[2]), fila[0])
            combo_componente.setCurrentIndex(combo_componente.findData(idcomponente))
        # Botones
        layout.addRow(label_titulo)
        layout.addRow(combo_componente)
        layout.addRow(label_mensaje)
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        # Cambiar los textos a español
        button_box.button(QDialogButtonBox.Save).setText("Guardar")
        button_box.button(QDialogButtonBox.Cancel).setText("Cancelar")
        layout.addWidget(button_box)
        # Conectar los botones a las funciones correspondientes
        def actualizarDatos():
            componente = combo_componente.currentData()
            nombrezona = combo_componente.currentText()
            if str(idcomponente) == str(componente):
                dialog.reject()
            else:
                respuesta = PrismaController.ctrlCambiarComponentePrismas(idcomponente, componente)
                if respuesta:
                    dialog.reject()
                    # Eliminar prismas
                    TreeCheckbox.eliminarCheckboxGrupo(treewidget, idcomponente, nombregrupo, tipogrupo)
                    # Crear prismas en nuevo componente
                    prismasalta = InterfazController.ctrlListarPrismasComponente(componente, 1)
                    if prismasalta:
                        TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidget, nombrezona, componente, idproyecto, nombregrupo, tipogrupo, prismasalta, subgrupo)
                        reiniciarvistas("Prisma")
                else:
                    label_mensaje.setText("Error al cambiar de componente.")
        button_box.accepted.connect(actualizarDatos)
        button_box.rejected.connect(dialog.reject)
        # Mostrar el diálogo
        dialog.setLayout(layout)
        dialog.exec()
    
    def editar_prisma(idproyecto, idcomponente, idinstrumento, nombreprisma, nombregrupo, tipolista, treewidget, reiniciarvistas):
        dialog = QDialog()
        dialog.setWindowTitle("Editar Prisma")
        layout = QFormLayout(dialog)
        # Campo nombre (readonly)
        nombre_input = QLineEdit()
        nombre_input.setText(nombreprisma)
        # Añadir los campos al layout
        layout.addRow("Nombre:", nombre_input)
        label_mensaje = QLabel("")
        label_mensaje.setAlignment(Qt.AlignCenter)
        label_mensaje.setStyleSheet("QLabel { color: red; }")
        layout.addRow(label_mensaje)
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        # Cambiar los textos a español
        button_box.button(QDialogButtonBox.Save).setText("Guardar")
        button_box.button(QDialogButtonBox.Cancel).setText("Cancelar")
        layout.addWidget(button_box)
        def actualizarDatos():
            nameprisma = nombre_input.text()
            if nameprisma and nameprisma.strip() != "":
                respuesta = PrismaController.ctrlVerificarPrismaUnico(nameprisma, idinstrumento, idproyecto)
                if respuesta is False:
                    editar = PrismaController.ctrlActualizarNombrePrisma(nombreprisma, nameprisma, idinstrumento, idproyecto)
                    if editar:
                        dialog.close()
                        TreeCheckbox.actualizarTextoCheckboxEquipo(treewidget, idcomponente, nombregrupo, tipolista, nombreprisma, nameprisma)
                        reiniciarvistas("Prisma")
                    else:
                        label_mensaje.setText("No se pudo cambiar el nombre del prisma.")
                else:
                    dlg = QMessageBox()
                    dlg.setWindowTitle("Prisma Existente")
                    dlg.setText(f"Ya existe un prisma con el mismo nombre.\n¿Desea unir la data de ambos?")
                    dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                    dlg.setIcon(QMessageBox.Question)
                    result = dlg.exec()
                    if result == QMessageBox.Yes:
                        editar = PrismaController.ctrlActualizarNombrePrisma(nombreprisma, nameprisma, idinstrumento, idproyecto)
                        if editar:
                            respuesta = PrismaController.ctrlEliminarPrismaUnico(idinstrumento)
                            if respuesta:
                                dialog.close()
                                TreeCheckbox.eliminarCheckbox(treewidget, nombregrupo, idinstrumento, tipolista)
                                reiniciarvistas("Prisma")
                            else:
                                label_mensaje.setText("Error al unir la data.")
                        else:
                            label_mensaje.setText("No se pudo cambiar el nombre del prisma.")
            else:
                label_mensaje.setText("El nombre no debe ir vacío.")
        # Mostrar el diálogo
        button_box.accepted.connect(actualizarDatos)
        button_box.rejected.connect(dialog.reject)
        dialog.setLayout(layout)
        dialog.exec()
    
    def eliminar_prisma(idinstrumento, nombreprisma, nombregrupo, tipolista, treewidget, reiniciarvistas):
        dlg = QMessageBox()
        dlg.setWindowTitle("Eliminar Prisma")
        dlg.setText(f"¿Está seguro eliminar el prisma '{nombreprisma}'?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            respuesta = PrismaController.ctrlEliminarPrismaUnico(idinstrumento)
            if respuesta:
                delete = PrismaController.ctrlEliminarPrismaData(respuesta)
                if delete:
                    TreeCheckbox.eliminarCheckbox(treewidget, nombregrupo, idinstrumento, tipolista)
                    reiniciarvistas("Prisma")
                else:
                    mostrar_mensaje("Eliminar Prisma", "Error al eliminar data del prisma.", "advertencia")
            else:
                mostrar_mensaje("Eliminar Prisma", "No se pudo eliminar el prisma.", "advertencia")
    
    def dardealta_prisma(idproyecto, idzona, nombreprisma, idinstrumento, nombrezona, treewidget, reiniciarvistas):
        dlg = QMessageBox()
        dlg.setWindowTitle("Dar de Alta Prisma")
        dlg.setText(f"¿Está seguro dar de alta al prisma '{nombreprisma}'?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            respuesta = PrismaController.ctrlCambiarPrismaEstado(1, idzona, idinstrumento)
            if respuesta:
                TreeCheckbox.eliminarCheckbox(treewidget, "Prismas de Baja", idinstrumento, "prismabaja")
                # LISTAR PRISMA DE ALTA
                prismasalta = InterfazController.ctrlListarComponentePrisma(idinstrumento, 1)
                if prismasalta:
                    TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidget, nombrezona, idzona, idproyecto, "Prismas", "1", prismasalta, "prisma")
                    reiniciarvistas("Prisma")
            else:
                mostrar_mensaje("Dar de Alta Prisma", "No se pudo dar de alta al prisma.", "advertencia")
    
    def cambiar_componente_prisma(idinstrumento, idcomponente, idproyecto, treewidget, nombregrupo, tipogrupo, subgrupo, estado, reiniciarvistas):
        dialog = QDialog()
        dialog.setWindowTitle("Cambiar Componente Prisma")
        layout = QFormLayout(dialog)
        # Campo componente
        label_titulo = QLabel("Componente:")
        combo_componente = QComboBox()
        label_mensaje = QLabel("")
        label_mensaje.setAlignment(Qt.AlignCenter)
        label_mensaje.setStyleSheet("QLabel { color: red; }")
        # cargar data componentes
        componentes = ProyectoController.ctrlObtenerComponentesProyecto(idproyecto)
        if componentes:
            for fila in componentes:
                combo_componente.addItem(str(fila[2]), fila[0])
            combo_componente.setCurrentIndex(combo_componente.findData(idcomponente))
        # Botones
        layout.addRow(label_titulo)
        layout.addRow(combo_componente)
        layout.addRow(label_mensaje)
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        # Cambiar los textos a español
        button_box.button(QDialogButtonBox.Save).setText("Guardar")
        button_box.button(QDialogButtonBox.Cancel).setText("Cancelar")
        layout.addWidget(button_box)
        # Conectar los botones a las funciones correspondientes
        def actualizarDatos():
            componente = combo_componente.currentData()
            nombrezona = combo_componente.currentText()
            if str(idcomponente) == str(componente):
                dialog.reject()
            else:
                respuesta = PrismaController.ctrlCambiarPrismaComponente(idinstrumento, componente)
                if respuesta:
                    dialog.reject()
                    # Eliminar prisma
                    TreeCheckbox.eliminarCheckbox(treewidget, nombregrupo, idinstrumento, subgrupo)
                    # Crear prisma en nuevo componente
                    prismasalta = InterfazController.ctrlListarComponentePrisma(idinstrumento, estado)
                    if prismasalta:
                        TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidget, nombrezona, componente, idproyecto, nombregrupo, tipogrupo, prismasalta, subgrupo)
                        reiniciarvistas("Prisma")
                else:
                    label_mensaje.setText("Error al cambiar de componente.")
        button_box.accepted.connect(actualizarDatos)
        button_box.rejected.connect(dialog.reject)
        # Mostrar el diálogo
        dialog.setLayout(layout)
        dialog.exec()
    
    def cambiar_componente_bloque_prisma(idproyecto, idcomponente, parent, treewidget, nombregrupo, tipogrupo, subgrupo, estado, reiniciarvistas):
        dialog = QDialog()
        dialog.setWindowTitle("Mover Prismas Componente")
        layout = QFormLayout(dialog)
        # Campo componente
        label_titulo = QLabel("Componente:")
        combo_componente = QComboBox()
        label_mensaje = QLabel("")
        label_mensaje.setAlignment(Qt.AlignCenter)
        label_mensaje.setStyleSheet("QLabel { color: red; }")
        # cargar data componentes
        componentes = ProyectoController.ctrlObtenerComponentesProyecto(idproyecto)
        if componentes:
            for fila in componentes:
                combo_componente.addItem(str(fila[2]), fila[0])
            combo_componente.setCurrentIndex(combo_componente.findData(idcomponente))
        # Botones
        layout.addRow(label_titulo)
        layout.addRow(combo_componente)
        layout.addRow(label_mensaje)
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        # Cambiar los textos a español
        button_box.button(QDialogButtonBox.Save).setText("Guardar")
        button_box.button(QDialogButtonBox.Cancel).setText("Cancelar")
        layout.addWidget(button_box)
        # Conectar los botones a las funciones correspondientes
        def actualizarDatos():
            componente = combo_componente.currentData()
            nombrezona = combo_componente.currentText()
            if str(idcomponente) == str(componente):
                dialog.reject()
            else:
                result = False
                hijos_marcados = []
                for i in range(parent.childCount()):
                    hijo = parent.child(i)
                    if hijo is not None and hijo.checkState(0) == Qt.Checked:
                        idinstrumento = hijo.text(2)
                        respuesta = PrismaController.ctrlCambiarPrismaComponente(idinstrumento, componente)
                        if respuesta:
                            hijos_marcados.append(hijo)
                            result = True
                if result:
                    dialog.reject()
                    for hijo in hijos_marcados:
                        idinstrumento = hijo.text(2)
                        TreeCheckbox.eliminarCheckbox(treewidget, nombregrupo, idinstrumento, subgrupo)
                        # Crear prisma en nuevo componente
                        prismasalta = InterfazController.ctrlListarComponentePrisma(idinstrumento, estado)
                        if prismasalta:
                            TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidget, nombrezona, componente, idproyecto, nombregrupo, tipogrupo, prismasalta, subgrupo)
                    reiniciarvistas("Prisma")
                    # Limpiar tabla
                    from views.datos_view import DatosView
                    from modules.datos.vistaDatos import VistaDatos
                    tabla =  DatosView.main.findChild(QTableView, "table_datos")
                    VistaDatos.limpiarTablaDatos(tabla)
                else:
                    label_mensaje.setText("Error al cambiar de componente.")
        button_box.accepted.connect(actualizarDatos)
        button_box.rejected.connect(dialog.reject)
        # Mostrar el diálogo
        dialog.setLayout(layout)
        dialog.exec()
    