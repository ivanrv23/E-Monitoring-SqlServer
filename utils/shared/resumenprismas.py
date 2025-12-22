
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QVBoxLayout, QTableView, QLabel, QPushButton, QMenu, QFormLayout,
                               QLineEdit, QDialogButtonBox, QMessageBox, QComboBox)
from PySide6.QtGui import QAction, QDoubleValidator
from PySide6.QtUiTools import QUiLoader
from utils.common.alertas import mostrar_mensaje
from utils.common.rutasarchivos import resource_path
from utils.common.metodosGenerales import MetodosGenerales
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
from controllers.PrismaController import PrismaController

class CustomTableModelDesviacion(QAbstractTableModel):
    def __init__(self, data, headers, idproyecto, nombreprisma, parent=None):
        super().__init__(parent)
        self._data = data
        self._headers = headers
        self.idproyecto = idproyecto
        self.nombreprisma = nombreprisma
        self.existedesviacion = False
        self._cargar_desviaciones()

    def _cargar_desviaciones(self):
        resultado = PrismaController.ctrlObtenerDesviacionStandar(self.idproyecto, self.nombreprisma)
        if resultado:
            self.existedesviacion = True
            self.desviauno_este, self.desviados_este, self.desviatres_este = float(resultado[4]), float(resultado[4]*2), float(resultado[4]*3)
            self.desviauno_norte, self.desviados_norte, self.desviatres_norte = float(resultado[6]), float(resultado[6]*2), float(resultado[6]*3)
        
    # Número de filas por página
    def rowCount(self, parent=QModelIndex()):
        return len(self._data)
    
    # Número de columnas
    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)
    
    # Devuelve los datos de la celda solicitada
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row = index.row()
        col = index.column()
        if role == Qt.DisplayRole:
            return str(self._data[row][col])
        # validar color según desviaciones
        if role == Qt.ForegroundRole:
            if self.existedesviacion:
                valor_estado = str(self._data[row][9])
                if valor_estado != "Omitido":
                    este = float(self._data[row][3])
                    norte = float(self._data[row][4])
                    primera_este, primera_norte = self.obtener_primera_lectura_valida()
                    primera_este = float(primera_este)
                    primera_norte = float(primera_norte)
                    dx = este - primera_este
                    dy = norte - primera_norte
                    # Cálculo de radios para elipse en cada nivel
                    elipse_1 = (dx / self.desviauno_este)**2 + (dy / self.desviauno_norte)**2
                    elipse_2 = (dx / self.desviados_este)**2 + (dy / self.desviados_norte)**2
                    elipse_3 = (dx / self.desviatres_este)**2 + (dy / self.desviatres_norte)**2
                    if elipse_1 <= 1:
                        return QColor("#008F39")  # dentro de 1σ
                    elif elipse_2 <= 1:
                        return QColor("#FFA500")  # dentro de 2σ
                    elif elipse_3 <= 1:
                        return QColor("#FF0000")  # dentro de 3σ
                    else:
                        return QColor("#969992")  # fuera de 3σ
        return None
    
    def obtener_primera_lectura_valida(self):
        for fila in self._data:
            estado = str(fila[9])
            if estado != "Omitido":
                primera_este = fila[3]
                primera_norte = fila[4]
                return primera_este, primera_norte
        return None, None
    
    # Encabezados de las columnas
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self._headers[section]
            elif orientation == Qt.Vertical:
                return str(section + 1)
        return None

class CustomTableModel(QAbstractTableModel):
    def __init__(self, data, headers, parent=None):
        super().__init__(parent)
        self._data = data
        self._headers = headers
    
    # Número de filas por página
    def rowCount(self, parent=QModelIndex()):
        return len(self._data)
    
    # Número de columnas
    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)
    
    # Devuelve los datos de la celda solicitada
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row = index.row()
        col = index.column()
        if role == Qt.DisplayRole:
            return str(self._data[row][col])
        return None
    
    # Encabezados de las columnas
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self._headers[section]
            elif orientation == Qt.Vertical:
                return str(section + 1)
        return None
    
class ResumenPrismas():
    
    def modalResumenTablaPrismas(tipo, idproyecto, fechaini, fechafin):
        loader = QUiLoader()
        ui_file_path = resource_path("ui/tablaresumen.ui")
        ui_file = loader.load(ui_file_path, None)
        # Configurar el cuadro de diálogo
        dialog = QDialog()
        dialog.setWindowTitle("Resumen de Prismas")
        layout = QVBoxLayout()
        layout.addWidget(ui_file)
        dialog.setLayout(layout)        
        # Inicializar tools
        labelTitulo = dialog.findChild(QLabel, "label_titulo")
        tablaResumen = dialog.findChild(QTableView, "table_resumen")
        botonAceptar = dialog.findChild(QPushButton, "btn_aceptar")
        # Mostrar data
        if tipo == "DESPLAZAMIENTO":
            labelTitulo.setText("DESPLAZAMIENTO DE PRISMAS")
            headers = [
                "Prisma", "Fecha Mínima", "Fecha Máxima", "Desp. SD (m)", "Desp. 3D (m)", "Desp. L (m)",
                "Desp. T (m)", "Desp. H (m)", "Desp. E (m)", "Desp. N (m)", "Desp. Z (m)"
            ]
            dataresumen = PrismaController.ctrlResumenDesplazamiento(idproyecto, fechaini, fechafin)
        else:
            labelTitulo.setText("VELOCIDAD DE PRISMAS")
            headers = [
                "Prisma", "Fecha Mínima", "Fecha Máxima", "Vel. Incr. 3D (m/d)", "Vel. Acum. 3D (m/d)", "Vel. Incr. 2D (m/d)",
                "Vel. Acum. 2D (m/d)", "Vel. Incr. SD (m/d)", "Vel. Acum. SD (m/d)", "Dirección", "Inclinación"
            ]
            dataresumen = PrismaController.ctrlResumenVelocidadBuzamiento(idproyecto, fechaini, fechafin)
        if dataresumen:
            model = CustomTableModel(dataresumen, headers)
            tablaResumen.setModel(model)
            # Ajustar automáticamente el tamaño de las columnas según el contenido
            tablaResumen.resizeColumnsToContents()
            tablaResumen.resizeRowsToContents()
        def aceptarTablaResumen():
            dialog.close()
        # Conectar señales
        botonAceptar.clicked.connect(aceptarTablaResumen)
        dialog.exec()
    
    def modalDataTablaDesviaciones(idproyecto, prisma, tipoprisma):
        loader = QUiLoader()
        ui_file_path = resource_path("ui/tabladesviaciones.ui")
        ui_file = loader.load(ui_file_path, None)
        # Configurar el cuadro de diálogo
        dialog = QDialog()
        dialog.setWindowTitle("Data de Prismas")
        layout = QVBoxLayout()
        layout.addWidget(ui_file)
        dialog.setLayout(layout)
        # Inicializar tools
        labelTitulo = dialog.findChild(QLabel, "label_titulo")
        tabladatos = dialog.findChild(QTableView, "table_resumen")
        botonOmitir = dialog.findChild(QPushButton, "btn_omitir_lecturas")
        botonActivar = dialog.findChild(QPushButton, "btn_incluir_lecturas")
        botonAceptar = dialog.findChild(QPushButton, "btn_aceptar")
        # Mostrar data
        labelTitulo.setText(f"LECTURAS DEL PRISMA '{prisma.upper()}'")
        headers = [
            "", "Prisma", "Fecha Hora", "Este (m)", "Norte (m)", "Elevación (msnm)",
            "Distancia (m)", "Ángulo Horizontal", "Ángulo Vertical", "Estado", ""
        ]
        def cargarDatos():
            dataresumen = PrismaController.ctrlDatosPrismasDesviaciones(idproyecto, tipoprisma, prisma)
            if dataresumen:
                model = CustomTableModelDesviacion(dataresumen, headers, idproyecto, prisma)
                tabladatos.setModel(model)
                tabladatos.resizeColumnsToContents()
                tabladatos.resizeRowsToContents()
                tabladatos.setColumnHidden(0, True)
                tabladatos.setColumnHidden(10, True)
        def omitirLecturasDesviacion():
            dialog = QDialog()
            dialog.setWindowTitle("Aplicar Desviación Estándar")
            layout = QFormLayout(dialog)
            # Label titulo
            labelTitulo = QLabel("Seleccione la desviación estándar a aplicar:")
            labelTitulo.setAlignment(Qt.AlignCenter)
            # Tipo de desviación
            comboDesviacion = QComboBox()
            comboDesviacion.addItem("Primera Desviación", "PDS")
            comboDesviacion.addItem("Segunda Desviación", "SDS")
            comboDesviacion.addItem("Tercera Desviación", "TDS")
            # Añadir los campos al layout
            layout.addRow(labelTitulo)
            layout.addRow(comboDesviacion)
            button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
            # Cambiar los textos a español
            button_box.button(QDialogButtonBox.Save).setText("Aplicar")
            button_box.button(QDialogButtonBox.Cancel).setText("Cancelar")
            layout.addWidget(button_box)
            # omitir lecturas
            def omitirSegunDesviacion():
                tablasql = f"prismas{idproyecto}"
                activar = PrismaController.ctrlActivarLecturasPrisma(tablasql, prisma)
                if activar:
                    resultado = PrismaController.ctrlObtenerDesviacionStandar(idproyecto, prisma)
                    if resultado:
                        tipodesviacion = comboDesviacion.currentData()
                        if tipodesviacion == "PDS":
                            desveste, desvnorte = resultado[4], resultado[6]
                        elif tipodesviacion == "SDS":
                            desveste, desvnorte = resultado[4]*2, resultado[6]*2
                        elif tipodesviacion == "TDS":
                            desveste, desvnorte = resultado[4]*3, resultado[6]*3
                        respuesta = PrismaController.ctrlOmitirLecturasPrismaDesviacion(tablasql, prisma, desveste, desvnorte)
                        if respuesta:
                            cargarDatos()
                dialog.reject()
            # conectar botones
            button_box.accepted.connect(omitirSegunDesviacion)
            button_box.rejected.connect(dialog.reject)
            # Mostrar el diálogo
            dialog.setLayout(layout)
            dialog.exec()
        def activarLecturasDesviacion():
            tablasql = f"prismas{idproyecto}"
            respuesta = PrismaController.ctrlActivarLecturasPrisma(tablasql, prisma)
            if respuesta:
                cargarDatos()
        def aceptarTablaResumen():
            dialog.close()
        # Primera carga
        cargarDatos()
        # Conectar el menú contextual al QTableView
        tabladatos.setContextMenuPolicy(Qt.CustomContextMenu)
        tabladatos.customContextMenuRequested.connect(lambda position: ResumenPrismas.mostrarMenuTablaDesviaciones(tabladatos, position, idproyecto, cargarDatos))
        botonOmitir.clicked.connect(omitirLecturasDesviacion)
        botonActivar.clicked.connect(activarLecturasDesviacion)
        botonAceptar.clicked.connect(aceptarTablaResumen)
        dialog.exec()
    
    def mostrarMenuTablaDesviaciones(table, position, idproyecto, reiniciarTabla):
        index = table.indexAt(position)
        if not index.isValid():
            return
        row = index.row()
        # Capturar los valores de la fila
        tipo = table.model().data(table.model().index(row, 0), Qt.DisplayRole)
        nombre = table.model().data(table.model().index(row, 1), Qt.DisplayRole)
        fecha = table.model().data(table.model().index(row, 2), Qt.DisplayRole)
        este = table.model().data(table.model().index(row, 3), Qt.DisplayRole)
        norte = table.model().data(table.model().index(row, 4), Qt.DisplayRole)
        nivel = table.model().data(table.model().index(row, 5), Qt.DisplayRole)
        distancia = table.model().data(table.model().index(row, 6), Qt.DisplayRole)
        iddetalle = table.model().data(table.model().index(row, 10), Qt.DisplayRole)
        tablasql = f"prismas{idproyecto}"
        ResumenPrismas.generarMenuTablaDesviaciones(position, table, nombre, fecha, este, norte, nivel, distancia, iddetalle, tablasql, reiniciarTabla)
    
    def generarMenuTablaDesviaciones(position, table, nombre, fecha, este, norte, nivel, distancia, iddetalle, tablasql, reiniciarTabla):
        # Crear menú contextual
        menu = QMenu()
        edit_action = QAction("Editar Lectura", table)
        hide_action = QAction("Omitir/incluir Lectura", table)
        delete_action = QAction("Eliminar Lectura", table)
        # Conectar las acciones con los valores de la fila
        edit_action.triggered.connect(lambda: ResumenPrismas.editarDatosLecturaPrismas(iddetalle, nombre, fecha, este, norte, nivel, distancia, tablasql, reiniciarTabla))
        hide_action.triggered.connect(lambda: ResumenPrismas.hide_row_prismas(iddetalle, nombre, fecha, tablasql, reiniciarTabla))
        delete_action.triggered.connect(lambda: ResumenPrismas.delete_row_prismas(iddetalle, nombre, fecha, tablasql, reiniciarTabla))
        # Añadir las acciones al menú
        menu.addAction(edit_action)
        menu.addAction(hide_action)
        menu.addAction(delete_action)
        selected_indexes = table.selectionModel().selectedRows()
        if selected_indexes:
            omitir_action = QAction("Omitir/incluir en Bloque", table)
            eliminar_action = QAction("Eliminar en Bloque", table)
            omitir_action.triggered.connect(lambda: ResumenPrismas.omitir_mostrar_rows_prismas(table, selected_indexes, tablasql, reiniciarTabla))
            eliminar_action.triggered.connect(lambda: ResumenPrismas.delete_rows_prismas(table, selected_indexes, tablasql, reiniciarTabla))
            menu.addAction(omitir_action)
            menu.addAction(eliminar_action)
        # Mostrar menú contextual en la posición del clic
        menu.exec(table.viewport().mapToGlobal(position))
    
    def editarDatosLecturaPrismas(iddetalle, nombre, fecha, este, norte, nivel, distancia, tablasql, reiniciarTabla):
        dialog = QDialog()
        dialog.setWindowTitle("Editar Lectura Prisma")
        validator = QDoubleValidator()
        layout = QFormLayout(dialog)
        # Campo nombre (readonly)
        nombre_input = QLineEdit()
        nombre_input.setText(nombre)
        nombre_input.setReadOnly(True)
        # Campo fecha (editable)
        fecha_input = QLineEdit()
        fecha_input.setText(fecha)
        # Campo este (editable)
        este_input = QLineEdit()
        este_input.setText(str(este))
        este_input.setValidator(validator)
        # Campo norte (editable)
        norte_input = QLineEdit()
        norte_input.setText(str(norte))
        norte_input.setValidator(validator)
        # Campo cota (editable)
        cota_input = QLineEdit()
        cota_input.setText(str(nivel))
        cota_input.setValidator(validator)
        # Campo distancia (editable)
        distan_input = QLineEdit()
        distan_input.setText(str(distancia))
        distan_input.setValidator(validator)
        # Añadir los campos al layout
        layout.addRow("Nombre:", nombre_input)
        layout.addRow("Fecha:", fecha_input)
        layout.addRow("Este (m):", este_input)
        layout.addRow("Norte (m):", norte_input)
        layout.addRow("Cota (msnm):", cota_input)
        layout.addRow("Distancia I. (m):", distan_input)
        label_mensaje = QLabel("")
        label_mensaje.setAlignment(Qt.AlignCenter)
        label_mensaje.setStyleSheet("QLabel { color: red; }")
        layout.addRow(label_mensaje)
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        # Cambiar los textos a español
        button_box.button(QDialogButtonBox.Save).setText("Guardar")
        button_box.button(QDialogButtonBox.Cancel).setText("Cancelar")
        layout.addWidget(button_box)
        # Conectar los botones a las funciones correspondientes
        def actualizarDatos():
            datofecha = fecha_input.text()
            respfecha = MetodosGenerales.validarFormatoFechaDatabase(datofecha)
            if respfecha:
                datoeste = este_input.text()
                datonorte = norte_input.text()
                datonivel = cota_input.text()
                datodistan = distan_input.text()
                if datoeste != "" and datonorte != "" and datonivel != "" and datodistan != "":
                    datanueva = [datofecha, datoeste, datonorte, datonivel, datodistan, iddetalle]
                    respuesta = PrismaController.ctrlActualizarLecturaPrisma(tablasql, datanueva)
                    if respuesta:
                        dialog.reject()
                        reiniciarTabla()
                    else:
                        label_mensaje.setText("Error al actualizar los datos.")
                else:
                    label_mensaje.setText("Los datos están vacíos.")
            else:
                label_mensaje.setText("El formato de fecha no es válido.")
        button_box.accepted.connect(actualizarDatos)
        button_box.rejected.connect(dialog.reject)
        # Mostrar el diálogo
        dialog.setLayout(layout)
        dialog.exec()
    
    def hide_row_prismas(iddetalle, nombre, fecha, tablasql, reiniciarTabla):
        dlg = QMessageBox()
        dlg.setWindowTitle("Omitir Lectura Prisma")
        dlg.setText(f"¿Desea omitir/incluir la lectura del '{nombre}' con fecha '{fecha}'?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            respuesta = PrismaController.ctrlCambiarEstadoLecturaPrisma(tablasql, iddetalle)
            if respuesta:
                reiniciarTabla()
            else:
                mostrar_mensaje("Estado Lectura", "No se pudo omitir/incluir la lectura.", "advertencia")
    
    def delete_row_prismas(iddetalle, nombre, fecha, tablasql, reiniciarTabla):
        dlg = QMessageBox()
        dlg.setWindowTitle("Eliminar Lectura Prisma")
        dlg.setText(f"¿Desea eliminar la lectura del '{nombre}' con fecha '{fecha}'?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            respuesta = PrismaController.ctrlEliminarLecturaPrisma(tablasql, iddetalle)
            if respuesta:
                reiniciarTabla()
            else:
                mostrar_mensaje("Eliminar Lectura", "No se pudo eliminar la lectura.", "advertencia")
    
    def omitir_mostrar_rows_prismas(table, selected_indexes, tablasql, reiniciarTabla):
        dataomitir = []
        idsomitir = []
        for index in selected_indexes:
            row = index.row()
            nombre = table.model().data(table.model().index(row, 1), Qt.DisplayRole)
            fecha = table.model().data(table.model().index(row, 2), Qt.DisplayRole)
            iddetalle = table.model().data(table.model().index(row, 10), Qt.DisplayRole)
            dataomitir.append((nombre, fecha, row))
            idsomitir.append((iddetalle))
        if len(idsomitir) > 0:
            dlg = QMessageBox()
            dlg.setWindowTitle("Estado Lectura Prisma")
            dlg.setText(f"¿Desea omitir/incluir las lecturas '{dataomitir}'?")
            dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            dlg.setIcon(QMessageBox.Question)
            result = dlg.exec()
            if result == QMessageBox.Yes:
                respuesta = PrismaController.ctrlCambiarEstadoLecturaPrismaBloque(tablasql, idsomitir)
                if respuesta:
                    reiniciarTabla()
                else:
                    mostrar_mensaje("Omitir Lecturas", "No se pudo omitir/incluir las lecturas.", "advertencia")
    
    def delete_rows_prismas(table, selected_indexes, tablasql, reiniciarTabla):
        dataeliminar = []
        idseliminar = []
        for index in selected_indexes:
            row = index.row()
            nombre = table.model().data(table.model().index(row, 1), Qt.DisplayRole)
            fecha = table.model().data(table.model().index(row, 2), Qt.DisplayRole)
            iddetalle = table.model().data(table.model().index(row, 10), Qt.DisplayRole)
            dataeliminar.append((nombre, fecha, row))
            idseliminar.append((iddetalle))
        if len(idseliminar) > 0:
            dlg = QMessageBox()
            dlg.setWindowTitle("Eliminar Lecturas Prisma")
            dlg.setText(f"¿Desea eliminar las lecturas '{dataeliminar}'?")
            dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            dlg.setIcon(QMessageBox.Question)
            result = dlg.exec()
            if result == QMessageBox.Yes:
                respuesta = PrismaController.ctrlEliminarLecturasBloquePrisma(tablasql, idseliminar)
                if respuesta:
                    reiniciarTabla()
                else:
                    mostrar_mensaje("Eliminar Lecturas", "No se pudo eliminar las lecturas.", "advertencia")
    
    def modalHistoarialSaltosPrismas(dataresumen, prisma):
        loader = QUiLoader()
        ui_file_path = resource_path("ui/tablacambiosprisma.ui")
        ui_file = loader.load(ui_file_path, None)
        # Configurar el cuadro de diálogo
        dialog = QDialog()
        dialog.setWindowTitle("Historial de Modificaciones")
        layout = QVBoxLayout()
        layout.addWidget(ui_file)
        dialog.setLayout(layout)
        # Inicializar tools
        labelTitulo = dialog.findChild(QLabel, "label_titulo")
        tabladatos = dialog.findChild(QTableView, "table_resumen")
        botonAceptar = dialog.findChild(QPushButton, "btn_aceptar")
        # Mostrar data
        labelTitulo.setText(f"HISTORIAL DEL PRISMA '{prisma.upper()}'")
        headers = [
            "Prisma", "Fecha Hora", "Columna", "Valor Anterior", "Valor Actual", "Usuario"
        ]
        def cargarDatos():
            if dataresumen:
                model = CustomTableModel(dataresumen, headers)
                tabladatos.setModel(model)
                tabladatos.resizeColumnsToContents()
                tabladatos.resizeRowsToContents()
        def aceptarTablaResumen():
            dialog.close()
        # Primera carga
        cargarDatos()
        botonAceptar.clicked.connect(aceptarTablaResumen)
        dialog.exec()
    