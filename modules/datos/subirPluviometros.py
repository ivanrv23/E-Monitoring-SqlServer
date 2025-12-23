import pandas as pd
from openpyxl import load_workbook
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QComboBox, QHeaderView, QPushButton, QMenu, QTableView, QDoubleSpinBox,
                        QFormLayout, QDialogButtonBox, QFileDialog, QMessageBox, QLabel, QTextEdit, QLineEdit, QTreeWidget)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import Qt
from datetime import datetime, time 
from PySide6.QtGui import QPen, QColor
from utils.common.rutasarchivos import resource_path
from utils.generic.cargariconos import cargarIcono
from utils.common.alertas import mostrar_mensaje
from utils.shared.pegarDatosTabla import configurar_tabla_para_pegado
from utils.shared.pegarDatosTabla import pegar_desde_portapapeles
from utils.shared.arbolmarcado import TreeCheckbox
from utils.common.metodosGenerales import MetodosGenerales
from controllers.ProyectoController import ProyectoController
from controllers.PluviometroController import PluviometroController
from controllers.InterfazController import InterfazController

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
            
class SubirPluviometros:
    
    # REGISTRO DE MEDIDAS DE COTAS DE TERRENO
    def registroNuevaDataPluviometros(main, proyectoid):
        loader = QUiLoader()
        ui_file_path = resource_path("ui/registropluviometros.ui")
        ui_file = loader.load(ui_file_path, None)
        # Configurar el cuadro de diálogo main
        dialogo = QDialog()
        dialogo.setWindowTitle("Nuevas Lecturas Pluviómetros")
        layout_procesar_data = QVBoxLayout()
        layout_procesar_data.addWidget(ui_file)
        dialogo.setLayout(layout_procesar_data)
        # inicializar herramientas
        comboPluviometros = dialogo.findChild(QComboBox, "combo_pluviometros")
        tabladata = dialogo.findChild(QTableView, "table_pluviometros_data")
        lblrespuesta = dialogo.findChild(QLabel, "label_mensaje_estado")
        # agregar una celda
        row_position = tabladata.rowCount()
        tabladata.insertRow(row_position)
        botonGuardarData = dialogo.findChild(QPushButton, "btn_guardar")
        botonCancelar = dialogo.findChild(QPushButton, "btn_cancelar")
        # cargar piezómetros en el combo
        if proyectoid != 0:
            lista_pluviometros = PluviometroController.ctrlListarPluviometrosCombo(proyectoid)
            if lista_pluviometros is not None:
                for fila in lista_pluviometros:
                    comboPluviometros.addItem(str(fila[2]), fila[0])
            else:
                comboPluviometros.addItem("Sin Pluviómetros")
                botonGuardarData.setEnabled(False)
        else:
            comboPluviometros.addItem("Sin Pluviómetros")
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
        # GUARDAR DATA
        def guardarPluviometrosTabla():
            idpluviometro = comboPluviometros.currentData()
            filas = tabladata.rowCount()
            if filas > 0 and proyectoid != 0:
                data = []
                estado = False
                for row in range(filas):
                    datosfila = []
                    datosfila.append(idpluviometro)
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
                                    mensaje = "Las medidas deben ser numéricas."
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
                                mensaje = "La medida está vacía."
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
                    respuesta = PluviometroController.ctrlGuardarPluviometrosTabla(proyectoid, data)
                    if respuesta:
                        lblrespuesta.setText("Registrado correctamente.")
                        lblrespuesta.setStyleSheet("color: green;")
                        # Limpiar filas tabla
                        tabladata.setRowCount(0)
                        tabladata.insertRow(0)
                        # actualizar árbol checkbox
                        data = PluviometroController.ctrlTraerDataPluviometro(idpluviometro)
                        if data:
                            idinstrumento, idcomponente, nombrezona = data[0], data[1], data[2]
                            treewidgetdatos = main.findChild(QTreeWidget, "tree_actual_datos")
                            treewidgetvisor = main.findChild(QTreeWidget, "tree_actual_visor")
                            treewidgetveloci = main.findChild(QTreeWidget, "tree_actual_velocidad")
                            treewidgetpiezo = main.findChild(QTreeWidget, "tree_actual_piezometros")
                            TreeCheckbox.eliminarCheckbox(treewidgetdatos, "Pluviómetros", idinstrumento, "pluviometro")
                            TreeCheckbox.eliminarCheckbox(treewidgetvisor, "Pluviómetros", idinstrumento, "pluviometro")
                            TreeCheckbox.eliminarCheckbox(treewidgetveloci, "Pluviómetros", idinstrumento, "pluviometro")
                            TreeCheckbox.eliminarCheckbox(treewidgetpiezo, "Pluviómetros", idinstrumento, "pluviometro")
                            # Crear piezometro cuerda en nuevo componente
                            pluvio = InterfazController.ctrlListarComponentePluviometro(idinstrumento)
                            if pluvio:
                                TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetdatos, nombrezona, idcomponente, proyectoid, "Pluviómetros", "5", pluvio, "pluviometro")
                                TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetvisor, nombrezona, idcomponente, proyectoid, "Pluviómetros", "6", pluvio, "pluviometro")
                                TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetveloci, nombrezona, idcomponente, proyectoid, "Pluviómetros", "2", pluvio, "pluviometro")
                                TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetpiezo, nombrezona, idcomponente, proyectoid, "Pluviómetros", "3", pluvio, "pluviometro")
                    else:
                        lblrespuesta.setText("Error al regitrar.")
                        lblrespuesta.setStyleSheet("color: red;")
                else:
                    lblrespuesta.setText(f"En la fila {len(data) + 1}: {mensaje}")
                    lblrespuesta.setStyleSheet("color: orange;")
        def cancelarData():
            dialogo.close()
        # conectar señales
        header.customContextMenuRequested.connect(mostrarMenuCabecera)
        tabladata.setContextMenuPolicy(Qt.CustomContextMenu)
        tabladata.customContextMenuRequested.connect(menuPegadoDataTabla)
        configurar_tabla_para_pegado(tabladata)
        botonGuardarData.clicked.connect(guardarPluviometrosTabla)
        botonCancelar.clicked.connect(cancelarData)
        dialogo.exec()
    
    def cargarDataFormatosPluviometros(main, proyectoid):
        loader = QUiLoader()
        ui_file_path = resource_path("ui/cargardataformato.ui")
        ui_file = loader.load(ui_file_path, None)
        dialogo = QDialog()
        dialogo.setWindowTitle("Data Pluviómetros")
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
                    respuesta, equipos, erroneos = SubirPluviometros.registrarFormatoDataPluviometros(proyectoid, ubicacion_archivo.text(), idcompo)
                    if respuesta:
                        ubicacion_archivo.clear()
                        if len(erroneos) > 0:
                            labelRespuesta.setText(f"Archivos erróneos: {erroneos}")
                        else:
                            labelRespuesta.setText("Guardado correctamente.")
                        labelRespuesta.setStyleSheet("color: green;")
                        # actualizar árbol checkbox
                        for idpluviometro in equipos:
                            data = PluviometroController.ctrlTraerDataPluviometro(idpluviometro)
                            if data:
                                idinstrumento, idcomponente, nombrezona = data[0], data[1], data[2]
                                treewidgetdatos = main.findChild(QTreeWidget, "tree_actual_datos")
                                treewidgetvisor = main.findChild(QTreeWidget, "tree_actual_visor")
                                treewidgetveloci = main.findChild(QTreeWidget, "tree_actual_velocidad")
                                treewidgetpiezo = main.findChild(QTreeWidget, "tree_actual_piezometros")
                                TreeCheckbox.eliminarCheckbox(treewidgetdatos, "Pluviómetros", idinstrumento, "pluviometro")
                                TreeCheckbox.eliminarCheckbox(treewidgetvisor, "Pluviómetros", idinstrumento, "pluviometro")
                                TreeCheckbox.eliminarCheckbox(treewidgetveloci, "Pluviómetros", idinstrumento, "pluviometro")
                                TreeCheckbox.eliminarCheckbox(treewidgetpiezo, "Pluviómetros", idinstrumento, "pluviometro")
                                # Crear piezometro cuerda en nuevo componente
                                pluvio = InterfazController.ctrlListarComponentePluviometro(idinstrumento)
                                if pluvio:
                                    TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetdatos, nombrezona, idcomponente, proyectoid, "Pluviómetros", "5", pluvio, "pluviometro")
                                    TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetvisor, nombrezona, idcomponente, proyectoid, "Pluviómetros", "6", pluvio, "pluviometro")
                                    TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetveloci, nombrezona, idcomponente, proyectoid, "Pluviómetros", "2", pluvio, "pluviometro")
                                    TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetpiezo, nombrezona, idcomponente, proyectoid, "Pluviómetros", "3", pluvio, "pluviometro")
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
    
    def registrarFormatoDataPluviometros(proyectoid, ubicacion, idcomponente):
        erroneos = []
        equipos = []
        respuesta = False
        encabezado = ['Fecha', 'Hora', 'Precipitación (mm)', 'Observación']
        archivos = ubicacion.split("\n")
        
        for file_name in archivos:
            file_name = file_name.strip()
            if not file_name or not file_name.endswith('.xlsx'):
                continue
            
            data = []
            try:
                # Validación de encabezado
                df_header = pd.read_excel(file_name, header=None, nrows=1, skiprows=16, engine='openpyxl')
                encabezados_archivo = [str(col).strip() for col in df_header.iloc[0, :len(encabezado)]]
                
                if encabezados_archivo != encabezado:
                    erroneos.append(file_name.split("/")[-1])
                    continue

                # Lectura de metadatos
                wb = load_workbook(file_name, data_only=True)
                hoja = wb.active
                
                nombrepluvio = hoja["B14"].value
                codigopluvio = hoja["B15"].value
                coordeste = hoja["B16"].value
                coordnorte = hoja["D14"].value
                superficie = hoja["D15"].value
                comentario = hoja["D16"].value
                wb.close()

                # Validación de metadatos
                if pd.isna(nombrepluvio) or proyectoid == 0 or not idcomponente:
                    erroneos.append(file_name.split("/")[-1])
                    continue

                # Registro/validación del pluviómetro
                idpluviometro = None
                respu, info = PluviometroController.ctrlComprobarExisteNombrePluviometro(proyectoid, nombrepluvio)
                
                if respu:
                    idpluviometro = info[0]
                else:
                    # Conversión segura de valores numéricos
                    try:
                        coordnorte = float(coordnorte) if not pd.isna(coordnorte) else 0.0
                    except (TypeError, ValueError):
                        coordnorte = 0.0
                    
                    try:
                        coordeste = float(coordeste) if not pd.isna(coordeste) else 0.0
                    except (TypeError, ValueError):
                        coordeste = 0.0
                    
                    try:
                        superficie = float(superficie) if not pd.isna(superficie) else 0.0
                    except (TypeError, ValueError):
                        superficie = 0.0
                    
                    datos = [
                        nombrepluvio, codigopluvio, 
                        coordnorte, coordeste, 
                        superficie, comentario, 
                        idcomponente
                    ]
                    
                    respues = PluviometroController.ctrlRegistrarFormatoPluviometro(proyectoid, datos)
                    
                    if respues:
                        idpluviometro = respues
                    else:
                        erroneos.append(file_name.split("/")[-1])
                        continue

                # Procesamiento de datos de precipitación
                if idpluviometro is not None:
                    df = pd.read_excel(file_name, header=None, skiprows=17, engine='openpyxl')
                    df.columns = ['fecha', 'hora', 'precipitacion', 'observacion']

                    for _, row in df.iterrows():
                        fecha = row['fecha']
                        hora = row['hora']
                        precipitacion = row['precipitacion']
                        observacion = row['observacion']

                        if pd.isna(fecha) or pd.isna(precipitacion):
                            continue

                        # Procesamiento de fecha
                        if isinstance(fecha, (pd.Timestamp, datetime)):
                            fecha = fecha.date().strftime('%Y-%m-%d')
                        elif isinstance(fecha, str):
                            fecha = MetodosGenerales.validarFormatoFecha(fecha)
                            if fecha is None:
                                continue
                        else:
                            continue

                        # Procesamiento de hora
                        if isinstance(hora, (pd.Timestamp, datetime)):
                            hora = hora.time().strftime('%H:%M:%S')
                        elif isinstance(hora, time):
                            hora = hora.strftime('%H:%M:%S')
                        elif isinstance(hora, str):
                            hora_validada = MetodosGenerales.validarFormatoHora(hora)
                            hora = hora_validada if hora_validada else "00:00:00"
                        else:
                            hora = "00:00:00"

                        # Validación de precipitación
                        try:
                            precipitacion = abs(float(precipitacion))
                        except (ValueError, TypeError):
                            continue
                        observa = observacion if not pd.isna(observacion) else ""
                        data.append((idpluviometro, fecha, hora, precipitacion, observa))

                    # Guardado de datos
                    if data:
                        respon = PluviometroController.ctrlGuardarPluviometrosTabla(proyectoid, data)
                        
                        if respon:
                            equipos.append(idpluviometro)
                            respuesta = True
                        else:
                            erroneos.append(file_name.split("/")[-1])
                    else:
                        erroneos.append(file_name.split("/")[-1])
                else:
                    erroneos.append(file_name.split("/")[-1])

            except Exception as e:
                erroneos.append(f"{file_name.split('/')[-1]} - Error: {str(e)}")

        return respuesta, equipos, erroneos

    def cambiar_componente_pluviometros(idcomponente, idproyecto, treewidget, nombregrupo, tipogrupo, subgrupo, reiniciarvistas):
        dialog = QDialog()
        dialog.setWindowTitle("Componente Pluviómetros")
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
                respuesta = PluviometroController.ctrlCambiarComponentePluviometros(idcomponente, componente)
                if respuesta:
                    dialog.reject()
                    # Eliminar pluvio
                    TreeCheckbox.eliminarCheckboxGrupo(treewidget, idcomponente, nombregrupo, tipogrupo)
                    # Crear pluvio en nuevo componente
                    TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidget, nombrezona, componente, idproyecto, nombregrupo, tipogrupo, respuesta, subgrupo)
                    reiniciarvistas("Pluviómetro")
                else:
                    label_mensaje.setText("Error al cambiar de componente.")
        button_box.accepted.connect(actualizarDatos)
        button_box.rejected.connect(dialog.reject)
        # Mostrar el diálogo
        dialog.setLayout(layout)
        dialog.exec()
    
    def eliminar_pluviometros(idproyecto, idzona, grupo, tipo, treewidget, reiniciarvistas):
        dlg = QMessageBox()
        dlg.setWindowTitle("Eliminar Pluviómetros")
        dlg.setText(f"¿Está seguro eliminar todos los Pluviómetros?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            respuesta = PluviometroController.ctrlEliminarPluviometros(idzona)
            if respuesta:
                delete = PluviometroController.ctrlEliminarDataPiezometrosManuales(idproyecto, respuesta)
                if delete:
                    TreeCheckbox.eliminarCheckboxGrupo(treewidget, idzona, grupo, tipo)
                    reiniciarvistas("Pluviómetro")
                else:
                    mostrar_mensaje("Eliminar Pluviómetros", "Error al eliminar data Pluviómetros.", "advertencia")
            else:
                mostrar_mensaje("Eliminar Pluviómetros", "No se pudo eliminar los Pluviómetros.", "advertencia")
    
    def actualizarPluviometro(idproyecto, idcomponente, idinstrumento, treewidget, nombregrupo, tipogrupo, subgrupo, reiniciarvistas):
        loaderLoading = QUiLoader()        
        ui_file_path = resource_path("ui/nuevopluviometro.ui")
        ui_file = loaderLoading.load(ui_file_path, None)
        dialogopluviometros = QDialog()
        dialogopluviometros.setWindowTitle("Actualizar Pluviómetro")
        layout_procesar_data = QVBoxLayout()
        layout_procesar_data.addWidget(ui_file)
        dialogopluviometros.setLayout(layout_procesar_data)
        # Obtener elementos para interactuar
        comboComponente = dialogopluviometros.findChild(QComboBox, "cb_lista_componentes")
        nombrePluvio = dialogopluviometros.findChild(QLineEdit, "input_nombre")
        codigoPluvio = dialogopluviometros.findChild(QLineEdit, "input_codigo")
        nortePluvio = dialogopluviometros.findChild(QDoubleSpinBox, "input_norte")
        estePluvio = dialogopluviometros.findChild(QDoubleSpinBox, "input_este")
        elevacionPluvio = dialogopluviometros.findChild(QDoubleSpinBox, "input_nivel")
        comentarioPluvio = dialogopluviometros.findChild(QTextEdit, "input_comentario")
        botonguardar = dialogopluviometros.findChild(QPushButton, "btn_registrar")
        lblrespuesta = dialogopluviometros.findChild(QLabel, "label_mensaje_estado")
        # cargar data componentes
        componentes = ProyectoController.ctrlObtenerComponentesProyecto(idproyecto)
        if componentes:
            for fila in componentes:
                comboComponente.addItem(str(fila[2]), fila[0])
            comboComponente.setEnabled(True)
        # mostrar data Piezómetro Cuerda
        nombreactual = ""
        idpluvio = 0
        datapiezo = PluviometroController.ctrlObtenerInfoPluviometro(idinstrumento)
        if datapiezo:
            idpluvio = datapiezo[0]
            comboComponente.setCurrentIndex(comboComponente.findData(idcomponente))
            nombrePluvio.setText(str(datapiezo[2]))
            nombreactual = str(datapiezo[2])
            codigoPluvio.setText(str(datapiezo[3]))
            estePluvio.setValue(datapiezo[4])
            nortePluvio.setValue(datapiezo[5])
            elevacionPluvio.setValue(datapiezo[6])
            comentarioPluvio.setPlainText(str(datapiezo[7]))
        def guardarNuevoPluviometro():
            componente = comboComponente.currentData()
            nombrezona = comboComponente.currentText()
            nombre = nombrePluvio.text() 
            codigo = codigoPluvio.text()
            norte = nortePluvio.value()
            este = estePluvio.value()
            nivel = elevacionPluvio.value()
            comentario = comentarioPluvio.toPlainText()
            if nombre:
                datos = (nombre, codigo, norte, este, nivel, comentario, idpluvio)
                data = (componente, nombre, idinstrumento)
                respuesta = PluviometroController.ctrlActualizarPluviometro(datos, data)
                if respuesta:
                    dialogopluviometros.close()
                    if str(idcomponente) == str(componente):
                        TreeCheckbox.actualizarTextoCheckboxEquipo(treewidget, idcomponente, nombregrupo, subgrupo, nombreactual, nombre)
                    else:
                        # Eliminar Pluviómetro
                        TreeCheckbox.eliminarCheckbox(treewidget, nombregrupo, idinstrumento, subgrupo)
                        # Crear pluviometro en nuevo componente
                        pluviome = InterfazController.ctrlListarComponentePluviometro(idinstrumento)
                        if pluviome:
                            TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidget, nombrezona, componente, idproyecto, nombregrupo, tipogrupo, pluviome, subgrupo)
                    reiniciarvistas("Pluviómetro")
                else:
                    lblrespuesta.setText("Error al actualizar el Pluviómetro.")
                    lblrespuesta.setStyleSheet("color: red;")
        botonguardar.clicked.connect(guardarNuevoPluviometro)
        dialogopluviometros.exec()
    
    def eliminar_pluviometro(idproyecto, idinstrumento, nombrepluvio, nombregrupo, tipolista, treewidget, reiniciarvistas):
        dlg = QMessageBox()
        dlg.setWindowTitle("Eliminar Pluviómetro")
        dlg.setText(f"¿Está seguro eliminar el Pluviómetro '{nombrepluvio}'?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            respuesta = PluviometroController.ctrlEliminarPluviometro(idinstrumento)
            if respuesta:
                delete = PluviometroController.ctrlEliminarPluviometroData(idproyecto, respuesta)
                if delete:
                    TreeCheckbox.eliminarCheckbox(treewidget, nombregrupo, idinstrumento, tipolista)
                    reiniciarvistas("Pluviómetro")
                else:
                    mostrar_mensaje("Eliminar Pluviómetro", "Error al eliminar data del pluviómetro.", "advertencia")
            else:
                mostrar_mensaje("Eliminar Pluviómetro", "No se pudo eliminar el pluviómetro.", "advertencia")
    
    def cambiar_componente_bloque_pluviometro(idproyecto, idcomponente, parent, treewidget, nombregrupo, tipogrupo, subgrupo, reiniciarvistas):
        dialog = QDialog()
        dialog.setWindowTitle("Mover Pluviómetros Componente")
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
                        respuesta = PluviometroController.ctrlCambiarPluviometroComponente(idinstrumento, componente)
                        if respuesta:
                            hijos_marcados.append(hijo)
                            result = True
                if result:
                    dialog.reject()
                    for hijo in hijos_marcados:
                        idinstrumento = hijo.text(2)
                        TreeCheckbox.eliminarCheckbox(treewidget, nombregrupo, idinstrumento, subgrupo)
                        # Crear prisma en nuevo componente
                        pluviometro = InterfazController.ctrlListarComponentePluviometro(idinstrumento)
                        if pluviometro:
                            TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidget, nombrezona, componente, idproyecto, nombregrupo, tipogrupo, pluviometro, subgrupo)
                    reiniciarvistas("Pluviómetros")
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
    