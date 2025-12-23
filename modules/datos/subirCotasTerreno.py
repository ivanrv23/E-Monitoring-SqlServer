import time as tm
import pandas as pd
from openpyxl import load_workbook
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QComboBox, QHeaderView, QPushButton, QMenu, QTableWidget, QFormLayout,
                            QDialogButtonBox, QMessageBox, QLabel, QTextEdit, QLineEdit, QTreeWidget, QTableView, QFileDialog)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QPen, QColor
from datetime import datetime,time
from utils.common.rutasarchivos import resource_path
from utils.common.alertas import mostrar_mensaje
from utils.generic.cargariconos import cargarIcono
from utils.shared.pegarDatosTabla import configurar_tabla_para_pegado
from utils.shared.pegarDatosTabla import pegar_desde_portapapeles
from utils.shared.arbolmarcado import TreeCheckbox
from utils.common.metodosGenerales import MetodosGenerales
from controllers.ProyectoController import ProyectoController
from controllers.TerrenoController import TerrenoController
from controllers.InterfazController import InterfazController

class CustomTableModel(QAbstractTableModel):
    def __init__(self, data, headers, parent=None):
        super().__init__(parent)
        self._data = data
        self._headers = headers

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        if self.rowCount() > 0:
            return len(self._data[0])
        return 0

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            valor = self._data[index.row()][index.column()]
            if isinstance(valor, float):
                return "{:.3f}".format(valor)
            return valor
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if section < len(self._headers):
                return self._headers[section]
        return super().headerData(section, orientation, role)
    
    def removeRows(self, row, count, parent=QModelIndex()):
        self.beginRemoveRows(parent, row, row + count - 1)
        for _ in range(count):
            del self._data[row]
        self.endRemoveRows()
        return True
        
    def insert_data_to_table_view(table_view, data, headers):
        start_time = tm.time()
        model = CustomTableModel(data, headers)
        table_view.setModel(model)
        for indice in range(model.columnCount()):
            table_view.setColumnWidth(indice, 100)
        elapsed_time = tm.time() - start_time
        return elapsed_time

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
            
class SubirCotasTerreno:
    
    # REGISTRO DE MEDIDAS DE COTAS DE TERRENO
    def registroDataCotaTerreno(main, proyectoid):
        loader = QUiLoader()
        ui_file_path = resource_path("ui/datacotaterreno.ui")
        ui_file = loader.load(ui_file_path, None)
        # Configurar el cuadro de diálogo
        dialog = QDialog()
        dialog.setWindowTitle("Data de Cotas de Terreno")
        layout = QVBoxLayout()
        layout.addWidget(ui_file)
        dialog.setLayout(layout)
        # Obtener elementos para interactuar
        combocotas = dialog.findChild(QComboBox, "combo_cotas")
        tabladata = dialog.findChild(QTableWidget, "table_cotas_data")
        # agregar una celda
        row_position = tabladata.rowCount()
        tabladata.insertRow(row_position)
        botonGuardar = dialog.findChild(QPushButton, "btn_guardar")
        lblrespuesta = dialog.findChild(QLabel, "label_mensaje_estado")
        botonCancelar = dialog.findChild(QPushButton, "btn_cancelar")
        # cargar suelos en el combo
        listacotas = TerrenoController.ctrlListaCotasTerrenoProyecto(proyectoid)
        if listacotas is not None:
            for fila in listacotas:
                combocotas.addItem(fila[2], fila[0])
        else:
            combocotas.addItem("Sin Cotas")
            botonGuardar.setEnabled(False)
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
        def guardarCotasTerreno():
            idcota = combocotas.currentData()
            filas = tabladata.rowCount()
            if filas > 0 and proyectoid != 0:
                data = []
                estado = False
                for row in range(filas):
                    datosfila = []
                    datosfila.append(idcota)
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
                                    mensaje = "Las cotas deben ser numéricas."
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
                                mensaje = "La cota está vacía."
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
                    respuesta = TerrenoController.ctrlGuardarDataCotaTerreno(proyectoid, data)
                    if respuesta:
                        lblrespuesta.setText("Registrado Correctamente.")
                        lblrespuesta.setStyleSheet("color: green;")
                        # Limpiar filas tabla
                        tabladata.setRowCount(0)
                        tabladata.insertRow(0)
                        # actualizar árbol checkbox
                        data = TerrenoController.ctrlTraerDataCotaTerreno(idcota)
                        if data:
                            idinstrumento, idcomponente, nombrezona = data[0], data[1], data[2]
                            treewidgetdatos = main.findChild(QTreeWidget, "tree_actual_datos")
                            treewidgetpiezo = main.findChild(QTreeWidget, "tree_actual_piezometros")
                            TreeCheckbox.eliminarCheckbox(treewidgetdatos, "Cotas de Terreno", idinstrumento, "terreno")
                            TreeCheckbox.eliminarCheckbox(treewidgetpiezo, "Cotas de Terreno", idinstrumento, "terreno")
                            # Crear piezometro cuerda en nuevo componente
                            terreno = InterfazController.ctrlListarComponenteCotaTerreno(idinstrumento)
                            if terreno:
                                TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetdatos, nombrezona, idcomponente, proyectoid, "Cotas de Terreno", "6", terreno, "terreno")
                                TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetpiezo, nombrezona, idcomponente, proyectoid, "Cotas de Terreno", "4", terreno, "terreno")
                    else:
                        lblrespuesta.setText("Error al registrar.")
                        lblrespuesta.setStyleSheet("color: red;")
                else:
                    lblrespuesta.setText(f"En la fila {len(data) + 1}: {mensaje}")
                    lblrespuesta.setStyleSheet("color: orange;")
        def cancelarCotasTerreno():
            dialog.close()
        # conectar señales
        header.customContextMenuRequested.connect(mostrarMenuCabecera)
        tabladata.setContextMenuPolicy(Qt.CustomContextMenu)
        tabladata.customContextMenuRequested.connect(menuPegadoDataTabla)
        configurar_tabla_para_pegado(tabladata)
        botonGuardar.clicked.connect(guardarCotasTerreno)
        botonCancelar.clicked.connect(cancelarCotasTerreno)
        dialog.exec()
    
    def cargarDataFormatosCotasTerreno(main, proyectoid):
        loader = QUiLoader()
        ui_file_path = resource_path("ui/cargardataformato.ui")
        ui_file = loader.load(ui_file_path, None)
        dialogo = QDialog()
        dialogo.setWindowTitle("Data Cotas de Terreno")
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
                    respuesta, equipos, erroneos = SubirCotasTerreno.registrarFormatoDataCotasTerreno(proyectoid, ubicacion_archivo.text(), idcompo)
                    if respuesta:
                        ubicacion_archivo.clear()
                        if len(erroneos) > 0:
                            labelRespuesta.setText(f"Archivos erróneos: {erroneos}")
                        else:
                            labelRespuesta.setText("Guardado correctamente.")
                        labelRespuesta.setStyleSheet("color: green;")
                        # actualizar árbol checkbox
                        for idcota in equipos:
                            data = TerrenoController.ctrlTraerDataCotaTerreno(idcota)
                            if data:
                                idinstrumento, idcomponente, nombrezona = data[0], data[1], data[2]
                                treewidgetdatos = main.findChild(QTreeWidget, "tree_actual_datos")
                                treewidgetpiezo = main.findChild(QTreeWidget, "tree_actual_piezometros")
                                TreeCheckbox.eliminarCheckbox(treewidgetdatos, "Cotas de Terreno", idinstrumento, "terreno")
                                TreeCheckbox.eliminarCheckbox(treewidgetpiezo, "Cotas de Terreno", idinstrumento, "terreno")
                                # Crear piezometro cuerda en nuevo componente
                                terreno = InterfazController.ctrlListarComponenteCotaTerreno(idinstrumento)
                                if terreno:
                                    TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetdatos, nombrezona, idcomponente, proyectoid, "Cotas de Terreno", "6", terreno, "terreno")
                                    TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetpiezo, nombrezona, idcomponente, proyectoid, "Cotas de Terreno", "4", terreno, "terreno")
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
    
    def registrarFormatoDataCotasTerreno(proyectoid, ubicacion, idcomponente):
        erroneos = []
        data = []
        equipos = []
        respuesta = False
        encabezado = ['Fecha', 'Hora', 'Cota (msnm)', 'Observación']
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
                nombrecota = hoja["C12"].value
                comentario = hoja["C13"].value
                wb.close()
                if pd.isna(nombrecota) or proyectoid == 0 or not idcomponente:
                    erroneos.append(file_name.split("/")[-1])
                    continue
                idterreno = None
                respu, info = TerrenoController.ctrlComprobarExisteNombreCotaTerreno(proyectoid, nombrecota)
                if respu:
                    idterreno = info[0]
                else:
                    respues = TerrenoController.ctrlRegistrarFormatoCotaTerreno(proyectoid, idcomponente, nombrecota, comentario)
                    if respues:
                        idterreno = respues
                if idterreno is not None:
                    df = pd.read_excel(file_name, header=None, skiprows=14, engine='openpyxl')
                    df.columns = ['fecha', 'hora', 'cota', 'observacion']
                    for _, row in df.iterrows():
                        fecha = row['fecha']
                        hora = row['hora']
                        cota = row['cota']
                        observacion = row['observacion']
                        if pd.isna(fecha) or pd.isna(cota):
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
                            cota = float(cota)
                        except (ValueError, TypeError):
                            continue
                        observa = observacion if not pd.isna(observacion) else ""
                        data.append((idterreno, fecha, hora, cota, observa))
                    if data:
                        respon = TerrenoController.ctrlGuardarDataCotaTerreno(proyectoid, data)
                        if respon:
                            equipos.append(idterreno)
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
    
    def cambiar_componente_terrenos(idcomponente, idproyecto, treewidget, nombregrupo, tipogrupo, subgrupo, reiniciarvistas):
        dialog = QDialog()
        dialog.setWindowTitle("Componente Cotas de Terreno")
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
                respuesta = TerrenoController.ctrlCambiarComponenteCotasTerreno(idcomponente, componente)
                if respuesta:
                    dialog.reject()
                    # Eliminar terreno
                    TreeCheckbox.eliminarCheckboxGrupo(treewidget, idcomponente, nombregrupo, tipogrupo)
                    # Crear pluvio en nuevo componente
                    TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidget, nombrezona, componente, idproyecto, nombregrupo, tipogrupo, respuesta, subgrupo)
                    reiniciarvistas("Cotaterreno")
                else:
                    label_mensaje.setText("Error al cambiar de componente.")
        button_box.accepted.connect(actualizarDatos)
        button_box.rejected.connect(dialog.reject)
        # Mostrar el diálogo
        dialog.setLayout(layout)
        dialog.exec()
    
    def eliminar_terrenos(idproyecto, idzona, grupo, tipo, treewidget, reiniciarvistas):
        dlg = QMessageBox()
        dlg.setWindowTitle("Eliminar Cotas de Terreno")
        dlg.setText(f"¿Está seguro eliminar todos las Cotas de Terreno?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            respuesta = TerrenoController.ctrlEliminarCotasTerrenos(idzona)
            if respuesta:
                delete = TerrenoController.ctrlEliminarDataCotasTerrenos(idproyecto, respuesta)
                if delete:
                    TreeCheckbox.eliminarCheckboxGrupo(treewidget, idzona, grupo, tipo)
                    reiniciarvistas("Cotaterreno")
                else:
                    mostrar_mensaje("Eliminar Cotas de Terreno", "Error al eliminar data Cotas de Terreno.", "advertencia")
            else:
                mostrar_mensaje("Eliminar Cotas de Terreno", "No se pudo eliminar las Cotas de Terreno.", "advertencia")
    
    def actualizarCotaTerreno(idproyecto, idcomponente, idinstrumento, treewidget, nombregrupo, tipogrupo, subgrupo, reiniciarvistas):
        loaderLoading = QUiLoader()        
        ui_file_path = resource_path("ui/nuevacotaterreno.ui")
        ui_file = loaderLoading.load(ui_file_path, None)
        dialogoCotaTerreno = QDialog()
        dialogoCotaTerreno.setWindowTitle("Actualizar Cota de Terreno")
        layout_procesar_data = QVBoxLayout()
        layout_procesar_data.addWidget(ui_file)
        dialogoCotaTerreno.setLayout(layout_procesar_data)
        # Obtener elementos para interactuar
        comboComponente = dialogoCotaTerreno.findChild(QComboBox, "cb_lista_componentes")
        nombrecota = dialogoCotaTerreno.findChild(QLineEdit, "input_nombre")
        comentariocota = dialogoCotaTerreno.findChild(QTextEdit, "input_comentario")
        botonguardar = dialogoCotaTerreno.findChild(QPushButton, "btn_registrar")
        lblrespuesta = dialogoCotaTerreno.findChild(QLabel, "label_mensaje_estado")
        # cargar data componentes
        componentes = ProyectoController.ctrlObtenerComponentesProyecto(idproyecto)
        if componentes:
            for fila in componentes:
                comboComponente.addItem(str(fila[2]), fila[0])
            comboComponente.setEnabled(True)
        # mostrar data Piezómetro Cuerda
        nombreactual = ""
        idterreno = 0
        datapiezo = TerrenoController.ctrlObtenerInfoCotaTerreno(idinstrumento)
        if datapiezo:
            idterreno = datapiezo[0]
            comboComponente.setCurrentIndex(comboComponente.findData(idcomponente))
            nombrecota.setText(str(datapiezo[2]))
            nombreactual = str(datapiezo[2])
            comentariocota.setPlainText(str(datapiezo[3]))
        def actualizarDatos():
            componente = comboComponente.currentData()
            nombrezona = comboComponente.currentText()
            nombre = nombrecota.text()
            comentario = comentariocota.toPlainText()
            if nombre:
                respuesta = TerrenoController.ctrlActualizarCotaTerreno(idterreno, nombre, comentario)
                if respuesta:
                    dialogoCotaTerreno.close()
                    if str(idcomponente) == str(componente):
                        TreeCheckbox.actualizarTextoCheckboxEquipo(treewidget, idcomponente, nombregrupo, subgrupo, nombreactual, nombre)
                    else:
                        # Eliminar cota terreno
                        TreeCheckbox.eliminarCheckbox(treewidget, nombregrupo, idinstrumento, subgrupo)
                        # Crear terreno en nuevo componente
                        terreno = InterfazController.ctrlListarComponenteCotaTerreno(idinstrumento)
                        if terreno:
                            TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidget, nombrezona, componente, idproyecto, nombregrupo, tipogrupo, terreno, subgrupo)
                    reiniciarvistas("Cotaterreno")
                else:
                    lblrespuesta.setText("No se pudo actualizar la Cota Terreno.")
                    lblrespuesta.setStyleSheet("color: green;")
            else:
                lblrespuesta.setText("El nombre no debe ir vacío.")
                lblrespuesta.setStyleSheet("color: red;")
        # Inicializar botones
        botonguardar.clicked.connect(actualizarDatos)
        dialogoCotaTerreno.exec()
    
    def eliminar_cotaterreno(idproyecto, idinstrumento, nombrecota, nombregrupo, tipolista, treewidget, reiniciarvistas):
        dlg = QMessageBox()
        dlg.setWindowTitle("Eliminar Cota de Terreno")
        dlg.setText(f"¿Está seguro eliminar la cota '{nombrecota}'?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            respuesta = TerrenoController.ctrlEliminarCotaTerreno(idinstrumento)
            if respuesta:
                delete = TerrenoController.ctrlEliminarCotaTerrenoData(idproyecto, respuesta)
                if delete:
                    TreeCheckbox.eliminarCheckbox(treewidget, nombregrupo, idinstrumento, tipolista)
                    reiniciarvistas("Cotaterreno")
                else:
                    mostrar_mensaje("Eliminar Cota de Terreno", "Error al eliminar data de la cota de terreno.", "advertencia")
            else:
                mostrar_mensaje("Eliminar Cota de Terreno", "No se pudo eliminar la cota de terreno.", "advertencia")
    
    def cambiar_componente_bloque_terreno(idproyecto, idcomponente, parent, treewidget, nombregrupo, tipogrupo, subgrupo, reiniciarvistas):
        dialog = QDialog()
        dialog.setWindowTitle("Mover Cotas Terreno Componente")
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
                        respuesta = TerrenoController.ctrlCambiarCotaterrenoComponente(idinstrumento, componente)
                        if respuesta:
                            hijos_marcados.append(hijo)
                            result = True
                if result:
                    dialog.reject()
                    for hijo in hijos_marcados:
                        idinstrumento = hijo.text(2)
                        TreeCheckbox.eliminarCheckbox(treewidget, nombregrupo, idinstrumento, subgrupo)
                        # Crear prisma en nuevo componente
                        cotaterreno = InterfazController.ctrlListarComponenteCotaTerreno(idinstrumento)
                        if cotaterreno:
                            TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidget, nombrezona, componente, idproyecto, nombregrupo, tipogrupo, cotaterreno, subgrupo)
                    reiniciarvistas("Cotas de Terreno")
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
    