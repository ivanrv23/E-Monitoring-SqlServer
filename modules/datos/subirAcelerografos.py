import pandas as pd
from openpyxl import load_workbook
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QComboBox, QHeaderView, QPushButton, QMenu, QTableWidget, QFormLayout,
                            QDialogButtonBox, QMessageBox, QLabel, QLineEdit, QTreeWidget, QFileDialog, QTableView,QHBoxLayout)
from PySide6.QtGui import QPen, QColor, QDoubleValidator
from PySide6.QtCore import Qt, QThread, Signal
from datetime import datetime, time
import os
import shutil
from utils.common.rutasarchivos import resource_path
from utils.common.alertas import mostrar_mensaje
from utils.generic.cargariconos import cargarIcono
from utils.shared.pegarDatosTabla import configurar_tabla_para_pegado
from utils.shared.pegarDatosTabla import pegar_desde_portapapeles
from utils.shared.arbolmarcado import TreeCheckbox
from utils.common.metodosGenerales import MetodosGenerales
from controllers.ProyectoController import ProyectoController
from controllers.AcelerografoController import AcelerografoController
from controllers.InterfazController import InterfazController
from utils.shared.loading import LoadingView

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
            
class SubirAcelerografos:
    _current_thread_acelero = None 
    def registrarDataAcelerografos(main, proyectoid):
        loader = QUiLoader()
        ui_file_path = resource_path("ui/registroacelerografos.ui")
        dialogo_cargarData_acelerografo = loader.load(ui_file_path, None)
        # Configurar el cuadro de diálogo principal
        dialogo_cargarData = QDialog()
        dialogo_cargarData.setWindowTitle("Registro Data Acelerógrafos")
        layout_cargarData_acelerografo = QVBoxLayout()
        layout_cargarData_acelerografo.addWidget(dialogo_cargarData_acelerografo)
        dialogo_cargarData.setLayout(layout_cargarData_acelerografo)
        # VALIDANDO INPUTS
        comboAcelerografo = dialogo_cargarData.findChild(QComboBox, "combo_acelerografos")
        tabladata = dialogo_cargarData.findChild(QTableWidget, "table_data_acelerografo")
        botonGuardarData = dialogo_cargarData.findChild(QPushButton, "btn_guardar")
        lblrespuesta = dialogo_cargarData.findChild(QLabel, "label_mensaje_estado")
        # cargar combo
        data = AcelerografoController.ctrlObtenerAcelerografos(proyectoid)
        if data is not None:
            for fila in data:
                comboAcelerografo.addItem(fila[2], fila[0])
        else:
            comboAcelerografo.addItem("Sin Acelerógrafos")
            botonGuardarData.setEnabled(False)
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
        def registrarDataTipo():
            idacelero = comboAcelerografo.currentData()
            filas = tabladata.rowCount()
            if filas > 0 and proyectoid != 0:
                data = []
                estado = False
                for row in range(filas):
                    datosfila = []
                    datosfila.append(idacelero)
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
                                    mensaje = "Las magnitudes deben ser numéricas."
                                    fila_valida = False
                                    break
                            elif column == 3:
                                if not MetodosGenerales.validarEsNumero(valor):
                                    mensaje = "Las distancias deben ser numéricas."
                                    fila_valida = False
                                    break
                        else:
                            if column == 0:
                                fila_valida = False
                                mensaje = "La fecha está vacía."
                            elif column == 1:
                                valor = "00:00:00"
                            elif column == 2:
                                fila_valida = False
                                mensaje = "La magnitud está vacía."
                            elif column == 3:
                                fila_valida = False
                                mensaje = "La distancia está vacía."
                            c += 1
                        datosfila.append(valor)
                    if c != 4:
                        if fila_valida  and len(datosfila) == 5:
                            data.append(datosfila)
                            estado = True
                        else:
                            estado = False
                            break
                if estado:
                    respuesta = AcelerografoController.ctrlRegistrarDataAcelerografo(proyectoid, data)
                    if respuesta:
                        lblrespuesta.setText("Registrado Correctamente")
                        lblrespuesta.setStyleSheet("color: green;")
                        # Limpiar filas tabla
                        tabladata.setRowCount(0)
                        tabladata.insertRow(0)
                        # actualizar árbol checkbox
                        data = AcelerografoController.ctrlTraerDataAcelerografo(idacelero)
                        if data:
                            idinstrumento, idcomponente, nombrezona = data[0], data[1], data[2]
                            treewidgetdatos = main.findChild(QTreeWidget, "tree_actual_datos")
                            treewidgetvisor = main.findChild(QTreeWidget, "tree_actual_visor")
                            treewidgetacelero = main.findChild(QTreeWidget, "tree_actual_acelerografos")
                            TreeCheckbox.eliminarCheckbox(treewidgetdatos, "Acelerógrafos", idinstrumento, "acelerografo")
                            TreeCheckbox.eliminarCheckbox(treewidgetvisor, "Acelerógrafos", idinstrumento, "acelerografo")
                            TreeCheckbox.eliminarCheckbox(treewidgetacelero, "Acelerógrafos", idinstrumento, "acelerografo")
                            # Crear piezometro cuerda en nuevo componente
                            acelero = InterfazController.ctrlListarComponenteAcelerografo(idinstrumento)
                            if acelero:
                                TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetdatos, nombrezona, idcomponente, proyectoid, "Acelerógrafos", "8", acelero, "acelerografo")
                                TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetvisor, nombrezona, idcomponente, proyectoid, "Acelerógrafos", "8", acelero, "acelerografo")
                                TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetacelero, nombrezona, idcomponente, proyectoid, "Acelerógrafos", "1", acelero, "acelerografo")
                    else:
                        lblrespuesta.setText("Error al regitrar.")
                        lblrespuesta.setStyleSheet("color: red;")
                else:
                    lblrespuesta.setText(f"En la fila {len(data) + 1}: {mensaje}")
                    lblrespuesta.setStyleSheet("color: orange;")
        # conectar señales
        header.customContextMenuRequested.connect(mostrarMenuCabecera)
        tabladata.setContextMenuPolicy(Qt.CustomContextMenu)
        tabladata.customContextMenuRequested.connect(menuPegadoDataTabla)
        configurar_tabla_para_pegado(tabladata)   
        botonGuardarData.clicked.connect(registrarDataTipo)
        dialogo_cargarData.exec()
    
    def cargarDataFormatoAcelerografos(main, proyectoid):
        loader = QUiLoader()
        ui_file_path = resource_path("ui/cargardataformato.ui")
        ui_file = loader.load(ui_file_path, None)
        dialogo = QDialog()
        dialogo.setWindowTitle("Data Acelerógrafos")
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
            idcompo = comboComponentes.currentData()

            labelRespuesta.setText("")
            botonAceptar.setEnabled(False)

            loading = LoadingView.mostrarLoading()

            thread = CargarAcelerografosThread(proyectoid, ubicacion_archivo.text(), idcompo)
            SubirAcelerografos._current_thread_acelero = thread

            def on_finish(resultado):
                loading.close()
                botonAceptar.setEnabled(True)

                labelRespuesta.setText(resultado.get("mensaje", ""))
                labelRespuesta.setStyleSheet(f"color: {resultado.get('color', 'red')};")

                if resultado.get("ok"):
                    ubicacion_archivo.clear()

                    for item in resultado.get("equipos_data", []):
                        idinstrumento = item["idinstrumento"]
                        idcomponente = item["idcomponente"]
                        nombrezona = item["nombrezona"]
                        acelero = item["acelero"]

                        treewidgetdatos = main.findChild(QTreeWidget, "tree_actual_datos")
                        treewidgetvisor = main.findChild(QTreeWidget, "tree_actual_visor")
                        treewidgetacelero = main.findChild(QTreeWidget, "tree_actual_acelerografos")
                        TreeCheckbox.eliminarCheckbox(treewidgetdatos, "Acelerógrafos", idinstrumento, "acelerografo")
                        TreeCheckbox.eliminarCheckbox(treewidgetvisor, "Acelerógrafos", idinstrumento, "acelerografo")
                        TreeCheckbox.eliminarCheckbox(treewidgetacelero, "Acelerógrafos", idinstrumento, "acelerografo")

                        if acelero:
                            TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetdatos, nombrezona, idcomponente, proyectoid, "Acelerógrafos", "8", acelero, "acelerografo")
                            TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetvisor, nombrezona, idcomponente, proyectoid, "Acelerógrafos", "8", acelero, "acelerografo")
                            TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetacelero, nombrezona, idcomponente, proyectoid, "Acelerógrafos", "1", acelero, "acelerografo")

                SubirAcelerografos._current_thread_acelero = None

            thread.task_finishAcelero.connect(on_finish, Qt.ConnectionType.QueuedConnection)
            thread.finished.connect(thread.deleteLater)
            thread.start()
            loading.exec()

        botonSubir.clicked.connect(cargar_archivo)
        botonAceptar.clicked.connect(procesar_archivo)
        dialogo.exec()
    
    def registrarFormatoDataAcelerografo(proyectoid, ubicacion, idcomponente):
        erroneos = []
        data = []
        equipos = []
        respuesta = False
        encabezado = ['Fecha', 'Hora', 'Magnitud', 'Distancia (Km)', 'Observación']
        archivos = ubicacion.split("\n")
        for file_name in archivos:
            file_name = file_name.strip()
            if not file_name or not file_name.endswith('.xlsx'):
                continue
            try:
                df_header = pd.read_excel(file_name, header=None, nrows=1, skiprows=11, engine='openpyxl')
                encabezados_archivo = [str(col).strip() for col in df_header.iloc[0, :len(encabezado)]]
                if encabezados_archivo != encabezado:
                    erroneos.append(file_name.split("/")[-1])
                    continue
                wb = load_workbook(file_name, data_only=True)
                hoja = wb.active
                nombresismo = hoja["B10"].value
                coordeste = hoja["B11"].value
                coordnorte = hoja["D10"].value
                coordnivel = hoja["D11"].value
                wb.close()
                if pd.isna(nombresismo) or proyectoid == 0 or not idcomponente:
                    erroneos.append(file_name.split("/")[-1])
                    continue
                idacelerografo = None
                respu, info = AcelerografoController.ctrlComprobarExisteNombreAcelerografo(proyectoid, nombresismo)
                if respu:
                    idacelerografo = info[0]
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
                    if pd.isna(coordnivel):
                        coordnivel = 0
                    else:
                        try:
                            coordnivel = float(coordnivel)
                        except ValueError:
                            coordnivel = 0
                    datos = [nombresismo, coordeste, coordnorte, coordnivel, idcomponente]
                    respues = AcelerografoController.ctrlRegistrarFormatoAcelerografo(proyectoid, datos)
                    if respues:
                        idacelerografo = respues
                if idacelerografo is not None:
                    df = pd.read_excel(file_name, header=None, skiprows=12, engine='openpyxl')
                    df.columns = ['fecha', 'hora', 'magnitud', 'distancia', 'observacion']
                    for _, row in df.iterrows():
                        fecha = row['fecha']
                        hora = row['hora']
                        magnitud = row['magnitud']
                        distancia = row['distancia']
                        observacion = row['observacion']
                        if pd.isna(fecha) or pd.isna(magnitud) or pd.isna(distancia):
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
                            magnitud = float(magnitud)
                        except (ValueError, TypeError):
                            continue
                        try:
                            distancia = float(distancia)
                        except (ValueError, TypeError):
                            continue
                        observa = "" if pd.isna(observacion) else str(observacion).strip()
                        data.append((idacelerografo, fecha, hora, magnitud, distancia, observa))
                    if data:
                        respon = AcelerografoController.ctrlRegistrarDataAcelerografo(proyectoid, data)
                        if respon:
                            equipos.append(idacelerografo)
                            respuesta = True
                        else:
                            erroneos.append(file_name.split("/")[-1])
                    else:
                        erroneos.append(file_name.split("/")[-1])
                else:
                    erroneos.append(file_name.split("/")[-1])
            except Exception:
                erroneos.append(file_name.split("/")[-1])
        return respuesta, equipos, erroneos
    
    def cambiar_componente_acelerografos(idcomponente, idproyecto, treewidget, nombregrupo, tipogrupo, subgrupo, reiniciarvistas):
        dialog = QDialog()
        dialog.setWindowTitle("Componente Acelerógrafos")
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
                respuesta = AcelerografoController.ctrlCambiarComponenteAcelerografos(idcomponente, componente)
                if respuesta:
                    dialog.reject()
                    # Eliminar acelero
                    TreeCheckbox.eliminarCheckboxGrupo(treewidget, idcomponente, nombregrupo, tipogrupo)
                    # Crear acelro en nuevo componente
                    TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidget, nombrezona, componente, idproyecto, nombregrupo, tipogrupo, respuesta, subgrupo)
                    reiniciarvistas("Acelerógrafo")
                else:
                    label_mensaje.setText("Error al cambiar de componente.")
        button_box.accepted.connect(actualizarDatos)
        button_box.rejected.connect(dialog.reject)
        # Mostrar el diálogo
        dialog.setLayout(layout)
        dialog.exec()
    
    def eliminar_acelerografos(idproyecto, idzona, grupo, tipo, treewidget, reiniciarvistas):
        dlg = QMessageBox()
        dlg.setWindowTitle("Eliminar Acelerógrafos")
        dlg.setText(f"¿Está seguro eliminar todos los Acelerógrafos?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.button(QMessageBox.Yes).setText("Sí")
        dlg.button(QMessageBox.No).setText("No")
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            respuesta = AcelerografoController.ctrlEliminarAcelerografos(idzona)
            if respuesta:
                delete = AcelerografoController.ctrlEliminarDataAcelerografos(idproyecto, respuesta)
                if delete:
                    for acelero in respuesta:
                        ruta_destino = resource_path(f'resources/workspace/ACELEROGRAFOS/proyecto{idproyecto}/{acelero[4]}')
                        if os.path.exists(ruta_destino) and os.path.isdir(ruta_destino):
                            shutil.rmtree(ruta_destino)
                    TreeCheckbox.eliminarCheckboxGrupo(treewidget, idzona, grupo, tipo)
                    reiniciarvistas("Acelerógrafo")
                else:
                    mostrar_mensaje("Eliminar Acelerógrafos", "Error al eliminar data Acelerógrafos.", "advertencia")
            else:
                mostrar_mensaje("Eliminar Acelerógrafos", "No se pudo eliminar los Acelerógrafos.", "advertencia")
    
    def actualizarAcelerografo(idproyecto, idcomponente, idinstrumento, treewidget, nombregrupo, tipogrupo, subgrupo, reiniciarvistas):
        loaderLoading = QUiLoader()
        ui_file_path = resource_path("ui/nuevoacelerografo.ui")
        ui_file = loaderLoading.load(ui_file_path, None)
        dialogoAcelerografo = QDialog()
        dialogoAcelerografo.setWindowTitle("Actualizar Acelerógrafo")
        layout_procesar_data = QVBoxLayout()
        layout_procesar_data.addWidget(ui_file)
        dialogoAcelerografo.setLayout(layout_procesar_data)
        # VALIDANDO INPUTS
        comboComponente = dialogoAcelerografo.findChild(QComboBox, "cb_lista_componentes")
        nombre_acelero = dialogoAcelerografo.findChild(QLineEdit, 'input_acelerografo')
        este_acelero = dialogoAcelerografo.findChild(QLineEdit, 'input_este')
        norte_acelero = dialogoAcelerografo.findChild(QLineEdit, 'input_norte')
        cota_acelero = dialogoAcelerografo.findChild(QLineEdit, 'input_cota')
        lblrespuesta = dialogoAcelerografo.findChild(QLabel, "label_mensaje_estado")
        validator = QDoubleValidator()
        este_acelero.setValidator(validator)
        norte_acelero.setValidator(validator)
        cota_acelero.setValidator(validator)
        nombreXML = dialogoAcelerografo.findChild(QLineEdit, 'input_nombre_xml')
        botonSubirXML = dialogoAcelerografo.findChild(QPushButton, "btn_cargar_xml")
        botonGuardarData = dialogoAcelerografo.findChild(QPushButton, "btn_guardar")
        combo_estado_acel = dialogoAcelerografo.findChild(QComboBox, "combo_estado_acel")
        combo_estado_acel.addItem("Operativo", 1)
        combo_estado_acel.addItem("Inoperativo", 0)
        # cargar data componentes
        componentes = ProyectoController.ctrlObtenerComponentesProyecto(idproyecto)
        if componentes:
            for fila in componentes:
                comboComponente.addItem(str(fila[2]), fila[0])
            comboComponente.setEnabled(True)
        # mostrar data
        nombreactual = ""
        idacelero = 0
        datapiezo = AcelerografoController.ctrlObtenerInfoAcelerografo(idinstrumento)
        if datapiezo:
            idacelero = datapiezo[0]
            comboComponente.setCurrentIndex(comboComponente.findData(idcomponente))
            nombre_acelero.setText(str(datapiezo[2]))
            nombreactual = str(datapiezo[2])
            este_acelero.setText(str(datapiezo[3]))
            norte_acelero.setText(str(datapiezo[4]))
            cota_acelero.setText(str(datapiezo[5]))
            combo_estado_acel.setCurrentIndex(combo_estado_acel.findData(datapiezo[6]))
        def subirXML():
            # Abrir diálogo para seleccionar archivo
            file_dialog = QFileDialog()
            file_path, _ = file_dialog.getOpenFileName(dialogoAcelerografo, "Seleccionar archivo XML", "", "XML Files (*.xml)")
            if file_path:
                # Mostrar el nombre del archivo en el QLineEdit
                nombreXML.setText(file_path)

        def actualizarDatos():
            componente = comboComponente.currentData()
            nombrezona = comboComponente.currentText()
            nombre = nombre_acelero.text()
            coorx = este_acelero.text()
            coory = norte_acelero.text()
            coorz = cota_acelero.text()
            archivo_xml = nombreXML.text()
            estado = combo_estado_acel.currentData()

            if nombre != "" and coorx != "" and coory != "" and coorz != "":
                datos = [nombre, coorx, coory, coorz, estado, idacelero]
                data = [componente, nombre, estado, idinstrumento]
                respuesta = AcelerografoController.ctrlActualizarAcelerografo(datos, data)

                if respuesta:
                    if archivo_xml:
                        carpeta_destino = resource_path(f'resources/workspace/ACELEROGRAFOS/proyecto{idproyecto}/{idacelero}')
                        # Verificar si la carpeta de destino existe, si no, créala
                        if not os.path.exists(carpeta_destino):
                            os.makedirs(carpeta_destino)
                        # Ruta completa del archivo XML de destino
                        destino_xml = os.path.join(carpeta_destino, os.path.basename(archivo_xml))
                        
                        # Eliminar cualquier archivo XML existente en la ruta
                        for archivo in os.listdir(carpeta_destino):
                            if archivo.endswith('.xml'):
                                os.remove(os.path.join(carpeta_destino, archivo))

                        # Ruta completa del archivo XML de destino
                        destino_xml = os.path.join(carpeta_destino, os.path.basename(archivo_xml))

                        try:
                            # Copiar el nuevo archivo XML a la ruta
                            shutil.copy(archivo_xml, destino_xml)
                        except Exception as e:
                            print('Error al subir XML:', e)

                    dialogoAcelerografo.close()

                    if str(idcomponente) == str(componente):
                        TreeCheckbox.actualizarTextoCheckboxEquipo(treewidget, idcomponente, nombregrupo, subgrupo, nombreactual, nombre)
                    else:
                        # Eliminar acelero
                        TreeCheckbox.eliminarCheckbox(treewidget, nombregrupo, idinstrumento, subgrupo)
                        # Crear acelero en nuevo componente
                        acelerogra = InterfazController.ctrlListarComponenteAcelerografo(idinstrumento)
                        if acelerogra:
                            TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidget, nombrezona, componente, idproyecto, nombregrupo, tipogrupo, acelerogra, subgrupo)
                    reiniciarvistas("Acelerógrafo")
                else:
                    lblrespuesta.setText("Error al actualizar el acelerógrafo.")
                    lblrespuesta.setStyleSheet("color: red;")
            else:
                lblrespuesta.setText("Algunos datos están vacíos.")
                lblrespuesta.setStyleSheet("color: red;")
        botonSubirXML.clicked.connect(subirXML)
        botonGuardarData.clicked.connect(actualizarDatos)
        dialogoAcelerografo.exec()
    
    def eliminar_acelerografo(idproyecto, idinstrumento, idacelerografo, nombreacelero, nombregrupo, tipolista, treewidget, reiniciarvistas):
        dlg = QMessageBox()
        dlg.setWindowTitle("Eliminar Acelerógrafo")
        dlg.setText(f"¿Está seguro eliminar el Acelerógrafo '{nombreacelero}'?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.button(QMessageBox.Yes).setText("Sí")
        dlg.button(QMessageBox.No).setText("No")
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            respuesta = AcelerografoController.ctrlEliminarAcelerografo(idinstrumento)
            if respuesta:
                delete = AcelerografoController.ctrlEliminarAcelerografoData(idproyecto, respuesta)
                if delete:
                    ruta_destino = resource_path(f'resources/workspace/ACELEROGRAFOS/proyecto{idproyecto}/{idacelerografo}')
                    if os.path.exists(ruta_destino) and os.path.isdir(ruta_destino):
                        shutil.rmtree(ruta_destino)
                    TreeCheckbox.eliminarCheckbox(treewidget, nombregrupo, idinstrumento, tipolista)
                    reiniciarvistas("Acelerógrafo")
                else:
                    mostrar_mensaje("Eliminar Acelerógrafo", "Error al eliminar la data del acelerógrafo.", "advertencia")
            else:
                mostrar_mensaje("Eliminar Acelerógrafo", "No se pudo eliminar el Acelerógrafo.", "advertencia")
    
    def cambiar_componente_bloque_acelerografo(idproyecto, idcomponente, parent, treewidget, nombregrupo, tipogrupo, subgrupo, reiniciarvistas):
        dialog = QDialog()
        dialog.setWindowTitle("Mover Acelerógrafos Componente")
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
                        respuesta = AcelerografoController.ctrlCambiarAcelerografoComponente(idinstrumento, componente)
                        if respuesta:
                            hijos_marcados.append(hijo)
                            result = True
                if result:
                    dialog.reject()
                    for hijo in hijos_marcados:
                        idinstrumento = hijo.text(2)
                        TreeCheckbox.eliminarCheckbox(treewidget, nombregrupo, idinstrumento, subgrupo)
                        # Crear prisma en nuevo componente
                        acelerografo = InterfazController.ctrlListarComponenteAcelerografo(idinstrumento)
                        if acelerografo:
                            TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidget, nombrezona, componente, idproyecto, nombregrupo, tipogrupo, acelerografo, subgrupo)
                    reiniciarvistas("Acelerógrafos")
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

    def cargarArchivosAcelerografos(main, proyecto_id):
        acelerografos = AcelerografoController.ctrlObtenerAcelerografos(proyecto_id)
        if acelerografos:
            dialog = QDialog()
            dialog.setWindowTitle("Cargar Archivos Acelerógrafos")
            layout = QVBoxLayout()
            combo = QComboBox()
            for data in acelerografos:
                combo.addItem(data[2], data[0])
            layout.addWidget(combo)
            h_layout = QHBoxLayout()
            file_path_edit = QLineEdit()
            file_path_edit.setReadOnly(True)
            h_layout.addWidget(file_path_edit)
            browse_button = QPushButton("Buscar...")
            browse_button.clicked.connect(lambda: SubirAcelerografos.buscarArchivos(dialog, file_path_edit))
            h_layout.addWidget(browse_button)
            layout.addLayout(h_layout)
            confirm_button = QPushButton("Confirmar")
            confirm_button.clicked.connect(lambda: SubirAcelerografos.confirmarSeleccion(dialog, main, combo, file_path_edit, proyecto_id))
            layout.addWidget(confirm_button)
            dialog.setLayout(layout)
            dialog.exec_()
    
    def buscarArchivos(dialog, file_path_edit):
        files, _ = QFileDialog.getOpenFileNames(dialog, "Seleccionar Archivos", "", "All Files (*)")
        if files:
            file_path_edit.setText(", ".join(files))

    def confirmarSeleccion(dialog, main, combo, file_path_edit, proyecto_id):
        selected_tuple = combo.currentData()
        files = file_path_edit.text().split(", ")
        
        carpeta_destino = resource_path(f'resources/workspace/ACELEROGRAFOS/proyecto{proyecto_id}/{selected_tuple}')
        # Verificar si la carpeta de destino existe, si no, créala
        if not os.path.exists(carpeta_destino):
            os.makedirs(carpeta_destino)
        
        for file in files:
            try:
                destino = os.path.join(carpeta_destino, os.path.basename(file))
                # Si el archivo ya existe, se reemplaza
                if os.path.exists(destino):
                    os.remove(destino)
                shutil.copy(file, destino)
                # actualizar árbol checkbox
                print(selected_tuple)
                data = AcelerografoController.ctrlTraerDataAcelerografo(selected_tuple)
                if data:
                    print(data)
                    idinstrumento, idcomponente, nombrezona = data[0], data[1], data[2]
                    treewidgetdatos = main.findChild(QTreeWidget, "tree_actual_datos")
                    treewidgetvisor = main.findChild(QTreeWidget, "tree_actual_visor")
                    treewidgetacelero = main.findChild(QTreeWidget, "tree_actual_acelerografos")
                    TreeCheckbox.eliminarCheckbox(treewidgetdatos, "Acelerógrafos", idinstrumento, "acelerografo")
                    TreeCheckbox.eliminarCheckbox(treewidgetvisor, "Acelerógrafos", idinstrumento, "acelerografo")
                    TreeCheckbox.eliminarCheckbox(treewidgetacelero, "Acelerógrafos", idinstrumento, "acelerografo")
                    # Crear piezometro cuerda en nuevo componente
                    acelero = InterfazController.ctrlListarComponenteAcelerografo(idinstrumento)
                    if acelero:
                        TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetdatos, nombrezona, idcomponente, proyecto_id, "Acelerógrafos", "8", acelero, "acelerografo")
                        TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetvisor, nombrezona, idcomponente, proyecto_id, "Acelerógrafos", "8", acelero, "acelerografo")
                        TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetacelero, nombrezona, idcomponente, proyecto_id, "Acelerógrafos", "1", acelero, "acelerografo")
            except Exception as e:
                QMessageBox.warning(dialog, "Error", f"No se pudo mover el archivo {file}: {e}")
                return
        QMessageBox.information(dialog, "Éxito", "Archivos movidos con éxito")
        dialog.accept()

class CargarAcelerografosThread(QThread):
    task_finishAcelero = Signal(dict)

    def __init__(self, proyectoid, ubicacion_texto, idcompo):
        super().__init__()
        self.proyectoid = proyectoid
        self.ubicacion_texto = ubicacion_texto
        self.idcompo = idcompo

    def run(self):
        resultado = {"ok": False, "mensaje": "No se guardó la data.", "color": "red"}
        try:
            respuesta, equipos, erroneos = SubirAcelerografos.registrarFormatoDataAcelerografo(
                self.proyectoid, self.ubicacion_texto, self.idcompo
            )

            if respuesta:
                resultado["ok"] = True
                if erroneos:
                    resultado["mensaje"] = f"Archivos erróneos: {erroneos}"
                    resultado["color"] = "orange"
                else:
                    resultado["mensaje"] = "Guardado correctamente."
                    resultado["color"] = "green"

                equipos_data = []
                for idacelero in equipos:
                    data = AcelerografoController.ctrlTraerDataAcelerografo(idacelero)
                    if not data:
                        continue
                    idinstrumento, idcomponente, nombrezona = data[0], data[1], data[2]
                    acelero = InterfazController.ctrlListarComponenteAcelerografo(idinstrumento)
                    equipos_data.append({
                        "idinstrumento": idinstrumento,
                        "idcomponente": idcomponente,
                        "nombrezona": nombrezona,
                        "acelero": acelero,
                    })
                resultado["equipos_data"] = equipos_data
            else:
                if erroneos:
                    resultado["mensaje"] = f"Error en los archivos: {erroneos}"

        except ValueError as e:
            resultado["mensaje"] = str(e)
        except Exception:
            resultado["mensaje"] = "Error al procesar los archivos."

        self.task_finishAcelero.emit(resultado)