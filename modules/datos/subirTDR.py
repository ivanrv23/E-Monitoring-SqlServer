import ast
import pandas as pd
from openpyxl import load_workbook
from PySide6.QtGui import QBrush, QPen, QColor, QPalette
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QComboBox, QHeaderView, QPushButton, QMenu, QTableWidget, QFormLayout,
                        QDoubleSpinBox, QDialogButtonBox, QMessageBox, QLabel, QLineEdit, QGridLayout, QHBoxLayout, QScrollArea,
                        QWidget, QSpacerItem, QSizePolicy, QFileDialog, QSpinBox, QTreeWidget, QTreeWidgetItem, QTableView)
from PySide6.QtCore import Qt
from datetime import datetime, time
import datetime as dt_module
from functools import partial
from utils.common.rutasarchivos import resource_path
from utils.generic.cargariconos import cargarIcono
from utils.common.alertas import mostrar_mensaje
from utils.shared.pegarDatosTabla import configurar_tabla_para_pegado
from utils.shared.pegarDatosTabla import pegar_desde_portapapeles
from utils.shared.arbolmarcado import TreeCheckbox
from utils.common.metodosGenerales import MetodosGenerales
from controllers.ProyectoController import ProyectoController
from controllers.TDRController import TDRController
from controllers.InterfazController import InterfazController

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

class SubirTDR:
    
    def registrarDataTDR(main, proyectoid):
        loader = QUiLoader()
        ui_file_path = resource_path("ui/cargardatatdr.ui")
        dialogo_data_tdr = loader.load(ui_file_path, None)
        # Configurar el cuadro de diálogo principal
        dialog_lecturas_TDR = QDialog()
        dialog_lecturas_TDR.setWindowTitle("Cargar Data TDR")
        layout_registro_medidas_tdr = QVBoxLayout()
        layout_registro_medidas_tdr.addWidget(dialogo_data_tdr)
        dialog_lecturas_TDR.setLayout(layout_registro_medidas_tdr)
        combo_sondajes = dialog_lecturas_TDR.findChild(QComboBox, "combo_tdr")
        tabladata = dialog_lecturas_TDR.findChild(QTableWidget, "table_data")
        boton_guardar = dialog_lecturas_TDR.findChild(QPushButton, "btn_guardar")
        lblrespuesta = dialog_lecturas_TDR.findChild(QLabel, "label_mensaje_estado")
        listasondajes = TDRController.ctrlObtenerListaSondajes(proyectoid)
        if listasondajes is not None:
            for result in listasondajes:
                val, text = result
                combo_sondajes.addItem(text, val)
        else:
            combo_sondajes.addItem("Sin sondajes TDR", 0)
            boton_guardar.setEnabled(False)      
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
        def menuPegadoDataTabla(pos):
            context_menu = QMenu()
            paste_action = context_menu.addAction("Pegar aquí")
            paste_action.triggered.connect(lambda: pegar_desde_portapapeles(tabladata))
            context_menu.exec(tabladata.mapToGlobal(pos))
        # guardar datos
        def guardar_datatdr():
            idtdr = combo_sondajes.currentData()
            filas = tabladata.rowCount()
            if filas > 0:
                data = []
                estado = False
                for row in range(filas):
                    datosfila = []
                    datosfila.append(idtdr)
                    fila_valida = True
                    c = 0
                    for column in range(tabladata.columnCount()):
                        item = tabladata.item(row, column)
                        valor = item.text().strip() if item else ""
                        if valor != "":
                            if column == 0:
                                valor = MetodosGenerales.validarFormatoFecha(valor)
                                if not valor:
                                    mensaje = "La fecha no tiene un formato adecuado."
                                    fila_valida = False
                                    break
                            elif column == 1:
                                valor = MetodosGenerales.validarFormatoHora(valor)
                                if not valor:
                                    mensaje = "La hora no tiene un formato adecuado."
                                    fila_valida = False
                                    break
                            elif column == 2:
                                if not MetodosGenerales.validarEsNumero(valor):
                                    mensaje = "La profundidad debe ser numérico."
                                    fila_valida = False
                                    break
                            elif column == 3:
                                if not MetodosGenerales.validarEsNumero(valor):
                                    mensaje = "La impedancia debe ser numérico."
                                    fila_valida = False
                                    break
                        else:
                            if column == 0:
                                fila_valida = False
                                mensaje = "La fecha está vacía."
                            if column == 1:
                                valor = "00:00:00"
                            elif column == 4:
                                valor = ""
                            c += 1
                        datosfila.append(valor)
                    if c != 5:
                        if fila_valida  and len(datosfila) == 6:
                            data.append(datosfila)
                            estado = True
                        else:
                            estado = False
                            break
                if estado:
                    respuesta = TDRController.ctrlGuardarDataSondajesTDR(proyectoid, data)
                    if respuesta:
                        lblrespuesta.setText("Registrado Correctamente.")
                        lblrespuesta.setStyleSheet("color: green;")
                        # Limpiar filas tabla
                        tabladata.setRowCount(0)
                        tabladata.insertRow(0)
                        # actualizar árbol checkbox
                        data = TDRController.ctrlTraerDataSondajetdr(idtdr)
                        if data:
                            idinstrumento, idcomponente, nombrezona = data[0], data[1], data[2]
                            treewidgetdatos = main.findChild(QTreeWidget, "tree_actual_datos")
                            treewidgetvisor = main.findChild(QTreeWidget, "tree_actual_visor")
                            treewidgettdr = main.findChild(QTreeWidget, "tree_actual_tdr")
                            TreeCheckbox.eliminarCheckbox(treewidgetdatos, "TDR", idinstrumento, "sondajetdr")
                            TreeCheckbox.eliminarCheckbox(treewidgetvisor, "TDR", idinstrumento, "sondajetdr")
                            TreeCheckbox.eliminarCheckbox(treewidgettdr, "TDR", idinstrumento, "sondajetdr")
                            # Crear piezometro cuerda en nuevo componente
                            sondaje = InterfazController.ctrlListarComponenteSondajeTDR(idinstrumento)
                            if sondaje:
                                TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetdatos, nombrezona, idcomponente, proyectoid, "TDR", "9", sondaje, "sondajetdr")
                                TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetvisor, nombrezona, idcomponente, proyectoid, "TDR", "9", sondaje, "sondajetdr")
                                fechas = InterfazController.ctrlListarFechasSondajetdrCodigo(proyectoid, idcomponente, idinstrumento)
                                if fechas:
                                    sonda = sondaje[0]
                                    fechitas = [fecha[0] for fecha in fechas]
                                    sondajestdr = [(sonda[0], sonda[1], sonda[2], sonda[3], sonda[4], sonda[5], sonda[6], fechitas)]
                                    TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgettdr, nombrezona, idcomponente, proyectoid, "TDR", "1", sondajestdr, "sondajetdr", "SI")
                    else:
                        lblrespuesta.setText("Error al registrar.")
                        lblrespuesta.setStyleSheet("color: red;")
                else:
                    lblrespuesta.setText(f"En la fila {len(data) + 1}: {mensaje}")
                    lblrespuesta.setStyleSheet("color: orange;")
        # inicializar botones
        header.customContextMenuRequested.connect(mostrarMenuCabecera)
        tabladata.setContextMenuPolicy(Qt.CustomContextMenu)
        tabladata.customContextMenuRequested.connect(menuPegadoDataTabla)
        configurar_tabla_para_pegado(tabladata)
        boton_guardar.clicked.connect(guardar_datatdr)
        dialog_lecturas_TDR.exec()
    
    def registrarFallasTDR(idproyecto):
        loader = QUiLoader()
        ui_file_path = resource_path("ui/registropuntostdr.ui")
        ui_file = loader.load(ui_file_path, None)
        dialogo = QDialog()
        dialogo.setWindowTitle("Registro de Fallas TDR")
        layout_puntos = QVBoxLayout()
        layout_puntos.addWidget(ui_file)
        dialogo.setLayout(layout_puntos)
        ruta = "resources/iconos/fontawesome/solid/trash.svg"
        boton_cancelar = dialogo.findChild(QPushButton, "btn_cancelar")
        boton_guardar = dialogo.findChild(QPushButton, "btn_guardar")
        # llenar combo
        comboSondajes = dialogo.findChild(QComboBox, "cb_lista_sondajes")
        comboSondajes.addItem("-- Seleccione TDR --", 0)
        listasondajes = TDRController.ctrlObtenerListaSondajes(idproyecto)
        if listasondajes is not None:
            for result in listasondajes:
                val, text = result
                comboSondajes.addItem(text, val)
        def eliminar_lectura_sondajetdr(posicion):
            input_nombre = dialogo.findChild(QLineEdit, f"input_tipo{posicion}")
            input_medida = dialogo.findChild(QDoubleSpinBox, f"dsp_{posicion}")
            boton_color = dialogo.findChild(QPushButton, f"btn_color_{posicion}")
            input_nombre.setText("")
            input_medida.setValue(0.00)
            boton_color.setStyleSheet("")
        # botones de eliminar
        for idx in range(1, 21):
            botoncolor = dialogo.findChild(QPushButton, f"btn_color_{idx}")
            botoneliminar = dialogo.findChild(QPushButton, f"btn_eliminar_{idx}")
            cargarIcono(botoneliminar, ruta)
            botoncolor.clicked.connect(partial(MetodosGenerales.cambiarColorBoton, botoncolor))
            botoneliminar.clicked.connect(partial(eliminar_lectura_sondajetdr, idx))
        # cargar data registrada
        def mostrarLecturasTDRsondaje():
            # limpiar registros
            for idx in range(1, 21):
                input_nombre = dialogo.findChild(QLineEdit, f"input_tipo{idx}")
                input_medida = dialogo.findChild(QDoubleSpinBox, f"dsp_{idx}")
                boton_color = dialogo.findChild(QPushButton, f"btn_color_{idx}")
                input_nombre.setText("")
                input_medida.setValue(0.00)
                boton_color.setStyleSheet("")
            # obtener valores estereografia DB
            idsondaje = comboSondajes.currentData()
            if idsondaje == 0:
                data = None
            else:
                data = TDRController.ctrlMostrarLecturasSondajeTDR(idsondaje)
            if data is not None:
                for fila in data:
                    idx = str(fila[5])
                    input_nombre = dialogo.findChild(QLineEdit, f"input_tipo{idx}")
                    input_medida = dialogo.findChild(QDoubleSpinBox, f"dsp_{idx}")
                    boton_color = dialogo.findChild(QPushButton, f"btn_color_{idx}")
                    input_nombre.setText(fila[2])
                    input_medida.setValue(fila[3])
                    boton_color.setStyleSheet(f"background-color: {fila[4]}")
        # guardar datos
        def validar_datos_medidas():
            data = []
            comboSondajes = dialogo.findChild(QComboBox, "cb_lista_sondajes")
            valor_sondaje = comboSondajes.currentData()
            if valor_sondaje != 0:
                for idx in range(1, 21):
                    input = dialogo.findChild(QLineEdit, f"input_tipo{idx}")
                    boton = dialogo.findChild(QPushButton, f"btn_color_{idx}")
                    medida = dialogo.findChild(QDoubleSpinBox, f"dsp_{idx}")
                    input_text = input.text()
                    button_color = boton.palette().color(QPalette.Button).name()
                    valor_medida = medida.value()
                    if input_text and button_color != "#f0f0f0":
                        data.append((valor_sondaje, input_text, valor_medida, button_color, idx))
                if len(data) > 0:      
                    respuesta = TDRController.ctrlRegistarMedidasSondaje(data)
                    if respuesta:
                        dialogo.close()
                        mostrar_mensaje("Registro Fallas TDR", "Las fallas se registraron correctamente.", "informacion")
                    else:
                        mostrar_mensaje("Registro Fallas TDR", "Error al registrar las fallas.", "error")
            else:
                mostrar_mensaje("Registro Fallas TDR", "Debe elegir un sondaje primero.", "advertencia")
        def cancelar_lecturastdr():
            dialogo.close()
        # inicializar botones
        comboSondajes.currentIndexChanged.connect(mostrarLecturasTDRsondaje)
        boton_cancelar.clicked.connect(cancelar_lecturastdr)
        boton_guardar.clicked.connect(validar_datos_medidas)
        dialogo.exec()
    
    def cargarDataFormatoTDR(main, proyectoid):
        loader = QUiLoader()
        ui_file_path = resource_path("ui/cargardataformato.ui")
        ui_file = loader.load(ui_file_path, None)
        dialogo = QDialog()
        dialogo.setWindowTitle("Data Sondajes TDR")
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
        componentes = ProyectoController.ctrlObtenerComponentesProyecto(proyectoid)
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
                    respuesta, equipos, erroneos = SubirTDR.registrarFormatoDataTDR(proyectoid, ubicacion_archivo.text(), idcompo)
                    if respuesta:
                        ubicacion_archivo.clear()
                        if len(erroneos) > 0:
                            labelRespuesta.setText(f"Archivos erróneos: {erroneos}")
                        else:
                            labelRespuesta.setText("Guardado correctamente.")
                        labelRespuesta.setStyleSheet("color: green;")
                        # actualizar árbol checkbox
                        for idtdr in equipos:
                            data = TDRController.ctrlTraerDataSondajetdr(idtdr)
                            if data:
                                idinstrumento, idcomponente, nombrezona = data[0], data[1], data[2]
                                treewidgetdatos = main.findChild(QTreeWidget, "tree_actual_datos")
                                treewidgetvisor = main.findChild(QTreeWidget, "tree_actual_visor")
                                treewidgettdr = main.findChild(QTreeWidget, "tree_actual_tdr")
                                TreeCheckbox.eliminarCheckbox(treewidgetdatos, "TDR", idinstrumento, "sondajetdr")
                                TreeCheckbox.eliminarCheckbox(treewidgetvisor, "TDR", idinstrumento, "sondajetdr")
                                TreeCheckbox.eliminarCheckbox(treewidgettdr, "TDR", idinstrumento, "sondajetdr")
                                # Crear piezometro cuerda en nuevo componente
                                sondaje = InterfazController.ctrlListarComponenteSondajeTDR(idinstrumento)
                                if sondaje:
                                    TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetdatos, nombrezona, idcomponente, proyectoid, "TDR", "9", sondaje, "sondajetdr")
                                    TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetvisor, nombrezona, idcomponente, proyectoid, "TDR", "9", sondaje, "sondajetdr")
                                    fechas = InterfazController.ctrlListarFechasSondajetdrCodigo(proyectoid, idcomponente, idinstrumento)
                                    if fechas:
                                        sonda = sondaje[0]
                                        fechitas = [fecha[0] for fecha in fechas]
                                        sondajestdr = [(sonda[0], sonda[1], sonda[2], sonda[3], sonda[4], sonda[5], sonda[6], fechitas)]
                                        TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgettdr, nombrezona, idcomponente, proyectoid, "TDR", "1", sondajestdr, "sondajetdr", "SI")
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
    
    def registrarFormatoDataTDR(proyectoid, ubicacion, idcomponente):
        erroneos = []
        data = []
        equipos = []
        respuesta = False
        encabezado = ['Fecha', 'Hora', 'Profundidad (m)', 'Impedancia', 'Observación']
        archivos = ubicacion.split("\n")
        for file_name in archivos:
            file_name = file_name.strip()
            if not file_name or not file_name.endswith('.xlsx'):
                continue
            try:
                df_header = pd.read_excel(file_name, header=None, nrows=1, skiprows=13, engine='openpyxl')
                encabezados_archivo = [str(col).strip() for col in df_header.iloc[0, :len(encabezado)]]
                if encabezados_archivo != encabezado:
                    erroneos.append(file_name.split("/")[-1])
                    continue
                wb = load_workbook(file_name, data_only=True)
                hoja = wb.active
                nombretdr = hoja["B10"].value
                coordeste = hoja["B11"].value
                coordnorte = hoja["B12"].value
                superficie = hoja["B13"].value
                profundo = hoja["D10"].value
                inclinacion = hoja["D11"].value
                azimuth = hoja["D12"].value
                comentario = hoja["D13"].value
                wb.close()
                if pd.isna(nombretdr) or proyectoid == 0 or not idcomponente:
                    erroneos.append(file_name.split("/")[-1])
                    continue
                idsondaje = None
                respu, info = TDRController.ctrlComprobarExisteNombreTDR(proyectoid, nombretdr)
                if respu:
                    idsondaje = info[0]
                else:
                    if pd.isna(coordnorte):
                        coordnorte = 0
                    else:
                        try:
                            coordnorte = float(coordnorte)
                        except ValueError:
                            coordnorte = 0
                    if pd.isna(coordeste):
                        coordeste = 0
                    else:
                        try:
                            coordeste = float(coordeste)
                        except ValueError:
                            coordeste = 0
                    if pd.isna(superficie):
                        superficie = 0
                    else:
                        try:
                            superficie = float(superficie)
                        except ValueError:
                            superficie = 0
                    if pd.isna(azimuth):
                        azimuth = 0
                    else:
                        try:
                            azimuth = float(azimuth)
                        except ValueError:
                            azimuth = 0
                    if pd.isna(inclinacion):
                        inclinacion = 90
                    else:
                        try:
                            inclinacion = float(inclinacion)
                        except ValueError:
                            inclinacion = 90
                    if pd.isna(profundo):
                        profundo = 1
                    else:
                        try:
                            profundo = float(profundo)
                        except ValueError:
                            profundo = 1
                    data_tdr = [nombretdr, coordeste, coordnorte, superficie, azimuth, inclinacion, profundo, idcomponente]
                    respues = TDRController.ctrlRegistrarFormatoEquipoTDR(proyectoid, data_tdr)
                    if respues:
                        idsondaje = respues
                if idsondaje is not None:
                    df = pd.read_excel(file_name, header=None, skiprows=14, engine='openpyxl')
                    df.columns = ['fecha', 'hora', 'profundidad', 'impedancia', 'observacion']
                    # Obtener la primera fila de 'fecha' y 'hora'
                    df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
                    df['hora'] = pd.to_datetime(df['hora'], errors='coerce').dt.time
                    # Obtener la primera fila de 'fecha' y 'hora' formateadas
                    primera_fecha = df.at[0, 'fecha'].strftime('%Y-%m-%d')
                    primera_hora = df.at[0, 'hora'].strftime('%H:%M:%S')
                    fechahora = primera_fecha + " " + primera_hora
                    tabla = f"sondajetdr_detalle{proyectoid}"
                    existefecha = TDRController.ctrlComprobarExisteFechaTDR(tabla, idsondaje, fechahora)
                    if existefecha is False:
                        for _, row in df.iterrows():
                            fecha = row['fecha']
                            hora = row['hora']
                            profundidad = row['profundidad']
                            impedancia = row['impedancia']
                            observacion = row['observacion']
                            if pd.isna(fecha) or pd.isna(profundidad) or pd.isna(impedancia):
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
                                profundidad = float(profundidad)
                            except (ValueError, TypeError):
                                continue
                            try:
                                impedancia = float(impedancia)
                            except (ValueError, TypeError):
                                continue
                            observa = "" if pd.isna(observacion) else str(observacion).strip()
                            data.append((idsondaje, fecha, hora, profundidad, impedancia, observa))
                        if data:
                            respon = TDRController.ctrlGuardarDataSondajesTDR(proyectoid, data)
                            if respon:
                                equipos.append(idsondaje)
                                respuesta = True
                            else:
                                erroneos.append(file_name.split("/")[-1])
                        else:
                            erroneos.append(file_name.split("/")[-1])
                    else:
                        erroneos.append(file_name.split("/")[-1])
                else:
                    erroneos.append(file_name.split("/")[-1])
            except Exception:
                erroneos.append(file_name.split("/")[-1])
        return respuesta, equipos, erroneos
    
    def cambiar_componente_sondajestdr(idcomponente, idproyecto, treewidget, nombregrupo, tipogrupo, subgrupo, reiniciarvistas):
        dialog = QDialog()
        dialog.setWindowTitle("Componente Sondajes TDR")
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
                respuesta = TDRController.ctrlCambiarComponenteSondajesTDR(idcomponente, componente)
                if respuesta:
                    dialog.reject()
                    # Eliminar TDRs
                    TreeCheckbox.eliminarCheckboxGrupo(treewidget, idcomponente, nombregrupo, tipogrupo)
                    # Crear TDR en nuevo componente
                    TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidget, nombrezona, componente, idproyecto, nombregrupo, tipogrupo, respuesta, subgrupo)
                    reiniciarvistas("TDR")
                else:
                    label_mensaje.setText("Error al cambiar de componente.")
        button_box.accepted.connect(actualizarDatos)
        button_box.rejected.connect(dialog.reject)
        # Mostrar el diálogo
        dialog.setLayout(layout)
        dialog.exec()
    
    def eliminar_sondajestdr(idproyecto, idzona, grupo, tipo, treewidget, reiniciarvistas):
        dlg = QMessageBox()
        dlg.setWindowTitle("Eliminar Sondajes TDR")
        dlg.setText(f"¿Está seguro eliminar todos los TDR?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            respuesta = TDRController.ctrlEliminarSondajesTDR(idzona)
            if respuesta:
                delete = TDRController.ctrlEliminarDataSondajesTDR(idproyecto, respuesta)
                if delete:
                    TreeCheckbox.eliminarCheckboxGrupo(treewidget, idzona, grupo, tipo)
                    reiniciarvistas("TDR")
                else:
                    mostrar_mensaje("Eliminar TDR", "Error al eliminar data TDR.", "advertencia")
            else:
                mostrar_mensaje("Eliminar TDR", "No se pudo eliminar los TDR.", "advertencia")
    
    def mostrarDialogoFechasSondajestdr(treewidget, fechasmarcadas, idproyecto, idcomponente, idinstrumento, nombrecompo, nombretdr, estado, graficarnuevafechasinclinometros):
        loaderLoading = QUiLoader()
        ui_file_path = resource_path("ui/arbolcheckbox.ui")
        ui_file = loaderLoading.load(ui_file_path, None)
        dialogo = QDialog()
        dialogo.setWindowTitle("Lista de fechas")
        layout = QVBoxLayout()
        layout.addWidget(ui_file)
        dialogo.setLayout(layout)
        # Obtener elementos para interactuar
        lbltitulo = dialogo.findChild(QLabel, "label_nombre")
        treefechas = dialogo.findChild(QTreeWidget, "tree_fechas")
        botonaceptar = dialogo.findChild(QPushButton, "btn_aceptar")
        lbltitulo.setText("FECHAS DEL TDR")
        treefechas.setHeaderLabels([nombrecompo])
        listafechas = TDRController.ctrlListarFechasSondajetdr(idcomponente, idinstrumento, idproyecto)
        if listafechas:
            if estado == Qt.Checked and fechasmarcadas:
                fechaselegidos = []
                try:
                    # 1. Si ya es una lista de objetos (por drivers modernos)
                    if isinstance(fechasmarcadas, list):
                        # Convertimos a string por si acaso
                        fechaselegidos = [str(f) for f in fechasmarcadas]
                    # 2. Si es texto y contiene "datetime.datetime" (Formato SQL Server/Repr)
                    elif isinstance(fechasmarcadas, str) and "datetime.datetime" in fechasmarcadas:
                        # Usamos el ALIAS dt_module para que eval entienda que 'datetime' es el módulo
                        contexto_seguro = {'datetime': dt_module}
                        # Ejecutamos eval de forma segura
                        temp_objs = eval(fechasmarcadas, {"__builtins__": None}, contexto_seguro)
                        # Convertimos los objetos a string 'YYYY-MM-DD HH:MM:SS' para comparar con el árbol
                        for obj in temp_objs:
                            # Verificamos usando la clase dentro del módulo alias
                            if isinstance(obj, dt_module.datetime):
                                fechaselegidos.append(obj.strftime('%Y-%m-%d %H:%M:%S'))
                            else:
                                fechaselegidos.append(str(obj))
                    # 3. Fallback: Si es texto normal (lista de strings simple)
                    elif isinstance(fechasmarcadas, str):
                        fechaselegidos = ast.literal_eval(fechasmarcadas)
                        # Aseguramos que todo sea string
                        fechaselegidos = [str(f) for f in fechaselegidos]
                except Exception as e:
                    print(f"Error procesando fechas marcadas en dialogo: {e}")
                    fechaselegidos = []
                # --- FIN LÓGICA DE CORRECCIÓN ---
                parent = QTreeWidgetItem(treefechas)
                parent.setText(0, nombretdr)
                parent.setText(1, "1")
                # Lógica para marcar check padre/hijo
                if len(listafechas) == len(fechaselegidos):
                    parent.setCheckState(0, Qt.Checked)
                else:
                    parent.setCheckState(0, Qt.PartiallyChecked)
                parent.setFlags(parent.flags() | Qt.ItemIsUserCheckable)
                parent.setExpanded(True)
                for fechas in listafechas:
                    item = QTreeWidgetItem(parent)
                    item.setText(0, str(fechas[0])) # Fecha string de la BD
                    item.setText(1, "fecha")
                    item.setText(2, str(fechas[2])) # id sondaje
                    item.setCheckState(0, Qt.Unchecked)
                    item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable)
                    if str(fechas[0]) == str(fechas[1]): # es base
                        item.setForeground(0, QBrush(QColor("red")))
                    # Comparación String vs String (Segura)
                    for fechita in fechaselegidos:
                        if str(fechas[0]) == str(fechita):
                            item.setCheckState(0, Qt.Checked)
            else:
                # Caso: No hay fechas marcadas previamente o no está checkeado
                parent = QTreeWidgetItem(treefechas)
                parent.setText(0, nombretdr)
                parent.setText(1, "1")
                parent.setCheckState(0, Qt.Unchecked)
                parent.setFlags(parent.flags() | Qt.ItemIsUserCheckable)
                parent.setExpanded(True)
                for fechas in listafechas:
                    item = QTreeWidgetItem(parent)
                    item.setText(0, str(fechas[0]))
                    item.setText(1, "fecha")
                    item.setText(2, str(fechas[2]))
                    item.setCheckState(0, Qt.Unchecked)
                    item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable)
                    if str(fechas[0]) == str(fechas[1]): # es base
                        item.setForeground(0, QBrush(QColor("red")))
        # --- Funciones internas ---
        def marcadoDesmarcadoCheckbox(parent_item, column):
            TreeCheckbox.validarMarcadoCheckbox(parent_item, column)

        def menuCambiarBaseCheckbox(point):
            item = treefechas.itemAt(point)
            if item:
                tipo = item.text(1)
                menu = QMenu()
                if not tipo.isdigit():
                    if tipo == "fecha":
                        fechaelegida = item.text(0)
                        idsondaje = item.text(2)
                        edit_fecha = menu.addAction("Cambiar a Base")
                        edit_fecha.triggered.connect(lambda: SubirTDR.cambiarFechaBaseSondajetdr(treefechas, idsondaje, fechaelegida))
                menu.exec(treefechas.mapToGlobal(point))

        def obtenerFechasMarcadas():
            fechasmarcadas_nuevas = []
            parent = treefechas.topLevelItem(0)
            if parent:
                for i in range(parent.childCount()):
                    hijo = parent.child(i)
                    if hijo.checkState(0) == Qt.Checked:
                        fechasmarcadas_nuevas.append(hijo.text(0))
            
            # Actualizamos y graficamos
            if fechasmarcadas_nuevas:
                TreeCheckbox.actualizarFechasCheckboxEquipo(treewidget, idcomponente, "TDR", "sondajetdr", nombretdr, fechasmarcadas_nuevas)
                graficarnuevafechasinclinometros()
            
            dialogo.close()

        # conectar funciones
        treefechas.itemClicked.connect(marcadoDesmarcadoCheckbox)
        treefechas.setContextMenuPolicy(Qt.CustomContextMenu)
        treefechas.customContextMenuRequested.connect(menuCambiarBaseCheckbox)
        botonaceptar.clicked.connect(obtenerFechasMarcadas)
        
        dialogo.exec()
    
    def cambiarFechaBaseSondajetdr(treewidget, idsondaje, fecha):
        dlg = QMessageBox()
        dlg.setWindowTitle("Cambiar Base TDR")
        dlg.setText(f"¿Elegir la '{fecha}' como base?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            respuesta = TDRController.ctrlCambiarBaseSondajetdr(fecha, idsondaje)
            if respuesta:
                root_item = treewidget.invisibleRootItem()
                for i in range(root_item.childCount()):
                    equipo_item = root_item.child(i)
                    for j in range(equipo_item.childCount()):
                        fecha_item = equipo_item.child(j)
                        fecha_item.setForeground(0, QBrush(QColor("black")))
                        if fecha_item.text(0) == str(fecha):
                            fecha_item.setForeground(0, QBrush(QColor("red")))
            else:
                mostrar_mensaje("Base TDR", "No se pudo cambiar de base.", "advertencia")
    
    def actualizarSondajeTDR(idproyecto, idcomponente, idinstrumento, treewidget, nombregrupo, tipogrupo, subgrupo, reiniciarvistas):
        loaderLoading = QUiLoader()        
        ui_file_path = resource_path("ui/nuevosondajetdr.ui")
        ui_file = loaderLoading.load(ui_file_path, None)
        dialogoTDR = QDialog()
        dialogoTDR.setWindowTitle("Actualizar Sondaje TDR")
        layout_procesar_data = QVBoxLayout()
        layout_procesar_data.addWidget(ui_file)
        dialogoTDR.setLayout(layout_procesar_data)
        comboComponente = dialogoTDR.findChild(QComboBox, "cb_lista_componentes")
        lblrespuesta = dialogoTDR.findChild(QLabel, "label_mensaje")
        nombreTDR = dialogoTDR.findChild(QLineEdit, "input_sondaje")
        norteTDR = dialogoTDR.findChild(QDoubleSpinBox, "input_norte")
        esteTDR = dialogoTDR.findChild(QDoubleSpinBox, "input_este")
        elevacionTDR = dialogoTDR.findChild(QDoubleSpinBox, "input_nivel")
        produndidadTDR = dialogoTDR.findChild(QDoubleSpinBox, "input_profundidad")
        azimutTDR = dialogoTDR.findChild(QSpinBox, "input_azimut")
        inclinacionTDR = dialogoTDR.findChild(QSpinBox, "input_inclinacion")
        botonguardar = dialogoTDR.findChild(QPushButton, "btn_registrar")
        combo_estado_tdr = dialogoTDR.findChild(QComboBox, "combo_estado_tdr")
        combo_estado_tdr.addItem("Operativo", 1)
        combo_estado_tdr.addItem("Inoperativo", 0)
        # cargar data componentes
        componentes = ProyectoController.ctrlObtenerComponentesProyecto(idproyecto)
        if componentes:
            for fila in componentes:
                comboComponente.addItem(str(fila[2]), fila[0])
            comboComponente.setEnabled(True)
        # mostrar data
        nombreactual = ""
        idtdr = 0
        datatdr = TDRController.ctrlObtenerInfoSondajeTDR(idinstrumento)
        if datatdr:
            idtdr = datatdr[0]
            comboComponente.setCurrentIndex(comboComponente.findData(idcomponente))
            nombreTDR.setText(str(datatdr[2]))
            nombreactual = str(datatdr[2])
            esteTDR.setValue(datatdr[3])
            norteTDR.setValue(datatdr[4])
            elevacionTDR.setValue(datatdr[5])
            produndidadTDR.setValue(datatdr[6])
            azimutTDR.setValue(datatdr[8])
            inclinacionTDR.setValue(datatdr[7])
            combo_estado_tdr.setCurrentIndex(combo_estado_tdr.findData(datatdr[11])) 
        def actualizarDatos():
            componente = comboComponente.currentData()
            nombrezona = comboComponente.currentText()
            nombre = nombreTDR.text()
            norte = norteTDR.value()
            este = esteTDR.value()
            nivel = elevacionTDR.value()
            profundidad = produndidadTDR.value()
            azimut = azimutTDR.value()
            inclinacion = inclinacionTDR.value()
            estado_tdr = combo_estado_tdr.currentData()
            if nombre:
                datos = [nombre, este, norte, nivel, profundidad, inclinacion, azimut, estado_tdr, idtdr]
                data = [componente, nombre, estado_tdr, idinstrumento]
                respuesta = TDRController.ctrlActualizarSondajeTDR(datos, data)
                if respuesta:
                    dialogoTDR.close()
                    if str(idcomponente) == str(componente):
                        TreeCheckbox.actualizarTextoCheckboxEquipo(treewidget, idcomponente, nombregrupo, subgrupo, nombreactual, nombre)
                    else:
                        # Eliminar TDR
                        TreeCheckbox.eliminarCheckbox(treewidget, nombregrupo, idinstrumento, subgrupo)
                        # Crear tdr en nuevo componente
                        sondaje = InterfazController.ctrlListarComponenteSondajeTDR(idinstrumento)
                        if sondaje:
                            TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidget, nombrezona, componente, idproyecto, nombregrupo, tipogrupo, sondaje, subgrupo)
                    reiniciarvistas("TDR")
                else:
                    lblrespuesta.setText("Error al actualizar el sondaje TDR.")
                    lblrespuesta.setStyleSheet("color: red;")
            else:
                lblrespuesta.setText("Algunos datos están vacíos.")
                lblrespuesta.setStyleSheet("color: red;")
        # Inicializar botones
        lblrespuesta.setText("")
        botonguardar.clicked.connect(actualizarDatos)
        dialogoTDR.exec()
    
    def eliminar_sondajetdr(idproyecto, idinstrumento, nombretdr, nombregrupo, tipolista, treewidget, reiniciarvistas):
        dlg = QMessageBox()
        dlg.setWindowTitle("Eliminar Sondaje TDR")
        dlg.setText(f"¿Está seguro eliminar el TDR '{nombretdr}'?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            respuesta = TDRController.ctrlEliminarSondajetdr(idinstrumento)
            if respuesta:
                delete = TDRController.ctrlEliminarSondajetdrData(idproyecto, respuesta)
                if delete:
                    TreeCheckbox.eliminarCheckbox(treewidget, nombregrupo, idinstrumento, tipolista)
                    reiniciarvistas("TDR")
                else:
                    mostrar_mensaje("Eliminar TDR", "Error al eliminar data del TDR.", "advertencia")
            else:
                mostrar_mensaje("Eliminar TDR", "No se pudo eliminar el TDR.", "advertencia")
    
    def cambiar_componente_bloque_sondajetdr(idproyecto, idcomponente, parent, treewidget, nombregrupo, tipogrupo, subgrupo, reiniciarvistas):
        dialog = QDialog()
        dialog.setWindowTitle("Mover TDR Componente")
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
                        respuesta = TDRController.ctrlCambiarSondajetdrComponente(idinstrumento, componente)
                        if respuesta:
                            hijos_marcados.append(hijo)
                            result = True
                if result:
                    dialog.reject()
                    for hijo in hijos_marcados:
                        idinstrumento = hijo.text(2)
                        TreeCheckbox.eliminarCheckbox(treewidget, nombregrupo, idinstrumento, subgrupo)
                        # Crear prisma en nuevo componente
                        sondajetdr = InterfazController.ctrlListarComponenteSondajeTDR(idinstrumento)
                        if sondajetdr:
                            TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidget, nombrezona, componente, idproyecto, nombregrupo, tipogrupo, sondajetdr, subgrupo)
                    reiniciarvistas("TDR")
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
    