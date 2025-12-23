import re
import ast
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QMenu, QComboBox, QLineEdit, QPushButton, QFileDialog, QDoubleSpinBox, QSpinBox,
                    QTreeWidgetItem, QFormLayout, QDialogButtonBox, QMessageBox, QLabel, QTextEdit, QTreeWidget, QTableView)
from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor
from utils.common.rutasarchivos import resource_path
from utils.generic.cargariconos import cargarIcono
from utils.common.alertas import mostrar_mensaje
from datetime import datetime
from utils.shared.arbolmarcado import TreeCheckbox
from controllers.ProyectoController import ProyectoController
from controllers.DatosController import DatosController
from controllers.InclinometroController import InclinometroController
from controllers.InterfazController import InterfazController
from services.security.session import Session

class SubirInclinometros:
    
    def registrarInclinometro(idproyecto):
        loaderLoading = QUiLoader()
        ui_file_path = resource_path("ui/nuevoinclinometro.ui")
        ui_file = loaderLoading.load(ui_file_path, None)

        dialogoInclinometros = QDialog()
        dialogoInclinometros.setWindowTitle("Nuevo Inclinómetro")
        layout_procesar_data = QVBoxLayout()
        layout_procesar_data.addWidget(ui_file)
        dialogoInclinometros.setLayout(layout_procesar_data)

        # Obtener elementos para interactuar
        comboComponente = dialogoInclinometros.findChild(QComboBox, "cb_lista_componentes")
        comboTipoEquipo = dialogoInclinometros.findChild(QComboBox, "cb_tipo_inclinometro")
        nombreIncli = dialogoInclinometros.findChild(QLineEdit, "input_nombre")
        codigoIncli = dialogoInclinometros.findChild(QLineEdit, "input_codigo")
        esteIncli = dialogoInclinometros.findChild(QDoubleSpinBox, "input_este")
        norteIncli = dialogoInclinometros.findChild(QDoubleSpinBox, "input_norte")
        elevacionIncli = dialogoInclinometros.findChild(QDoubleSpinBox, "input_elevacion")
        inclinacionIncli = dialogoInclinometros.findChild(QSpinBox, "input_inclinacion")
        azimutIncli = dialogoInclinometros.findChild(QSpinBox, "input_azimut")
        profundidadIncli = dialogoInclinometros.findChild(QDoubleSpinBox, "input_profundidad")
        comentarioIncli = dialogoInclinometros.findChild(QTextEdit, "input_comentario")
        lblrespuesta = dialogoInclinometros.findChild(QLabel, "label_mensaje_nuevo_inclinometro")
        botonguardar = dialogoInclinometros.findChild(QPushButton, "btn_aceptar_nuevo_inclinometro")
        inclinacionIncli.setValue(90)

        # cargar data componentes
        componentes = ProyectoController.ctrlObtenerComponentesProyecto(idproyecto)
        if componentes:
            for fila in componentes:
                comboComponente.addItem(str(fila[2]), fila[0])
            comboComponente.setEnabled(True)

        def guardarNuevoInclinometro():
            componente = comboComponente.currentData()
            tipoEquipo = comboTipoEquipo.currentText()
            nombre = nombreIncli.text()
            codigo = codigoIncli.text()
            norte = norteIncli.value()
            este = esteIncli.value()
            nivel = elevacionIncli.value()
            inclinacion = inclinacionIncli.value()
            azimut = azimutIncli.value()
            profundidad = profundidadIncli.value()
            comentario = comentarioIncli.toPlainText()
            lblrespuesta.setText("")
            # Validación de campos
            if not nombre:
                lblrespuesta.setText("Todos los campos son obligatorios.")
                lblrespuesta.setStyleSheet("color: red;")
                return

            datos = {
                "componente": componente,
                "tipoEquipo": tipoEquipo,
                "nombre": nombre,
                "codigo": codigo,
                "norte": norte,
                "este": este,
                "nivel": nivel,
                "inclinacion": inclinacion,
                "azimut": azimut,
                "profundidad": profundidad,
                "comentario": comentario
            }

            respuesta = DatosController.ctrlRegistrarInclinometro(idproyecto, datos)
            if respuesta:
                lblrespuesta.setText("Registro correcto")
                lblrespuesta.setStyleSheet("color: green;")
                # Limpiar los inputs
                nombreIncli.clear()
                codigoIncli.clear()
                norteIncli.setValue(0)
                esteIncli.setValue(0)
                elevacionIncli.setValue(0)
                inclinacionIncli.setValue(90)
                azimutIncli.setValue(0)
                profundidadIncli.setValue(0)
                comentarioIncli.clear()
            else:
                lblrespuesta.setText("Error al registrar. Por favor, intente de nuevo.")
                lblrespuesta.setStyleSheet("color: red;")

        botonguardar.clicked.connect(guardarNuevoInclinometro)
        dialogoInclinometros.exec()
        
    def cargarInclinometros(main, proyectoid):
        loaderLoading = QUiLoader()
        ui_file_path = resource_path("ui/cargardatainclinometros.ui")
        ui_file = loaderLoading.load(ui_file_path, None)
        dialogoInclinometros = QDialog()
        dialogoInclinometros.setWindowTitle("Data Inclinómetros")
        layout_procesar_data = QVBoxLayout()
        layout_procesar_data.addWidget(ui_file)
        dialogoInclinometros.setLayout(layout_procesar_data)
        ruta = "resources/iconos/fontawesome/solid/file-arrow-up.svg"
        boton_subir_archivo = dialogoInclinometros.findChild(QPushButton, "btn_cargar_archivo")
        cargarIcono(boton_subir_archivo, ruta)
        ubicacion_archivo = dialogoInclinometros.findChild(QLineEdit, "input_archivo")
        ubicacion_archivo.setReadOnly(True)
        combo_inclinometro = dialogoInclinometros.findChild(QComboBox, "combo_inclinometro_archivo")
        lblrespuesta = dialogoInclinometros.findChild(QLabel, "lb_mensaje_confirmacion")
        boton_procesar_data = dialogoInclinometros.findChild(QPushButton, "btn_aceptar")
        listaInclino = InclinometroController.ctrlListarInclinometrosNombreProyecto(proyectoid)
        if listaInclino:
            for fila in listaInclino:
                combo_inclinometro.addItem(str(fila[3]), fila[0])
                combo_inclinometro.setItemData(combo_inclinometro.count() - 1, fila[2], Qt.UserRole + 1)
        else:
            combo_inclinometro.addItem("Sin Inclinómetros")
            combo_inclinometro.setEnabled(False)
            boton_procesar_data.setEnabled(False)
        def cargar_archivo():
            tipo_inclinometro = SubirInclinometros.obtener_tipo_seleccionado_combo(combo_inclinometro)
            if tipo_inclinometro == 'GEOKON':
                file_names, _ = QFileDialog.getOpenFileNames(None, "Cargar Archivos", "", "Archivos (*.csv *.txt *.gkn)")
            else:  # RST
                file_names, _ = QFileDialog.getOpenFileNames(None, "Cargar Archivos", "", "Archivos (*.csv *.txt)")
            if file_names:
                ubicacion_archivo.setText("\n".join(file_names))
        def procesar_archivo():
            if not ubicacion_archivo.text().strip():
                lblrespuesta.setText("No se cargó ningún archivo.")
                lblrespuesta.setStyleSheet("color: red;")
                return
            else:
                tipo_inclinometro = SubirInclinometros.obtener_tipo_seleccionado_combo(combo_inclinometro)
                try:
                    idinclinometro = combo_inclinometro.currentData()
                    respuesta, erroneos = SubirInclinometros.registrarDataInclinometro(tipo_inclinometro, ubicacion_archivo.text(), proyectoid, idinclinometro)
                    if respuesta:
                        if len(erroneos) > 0:
                            lblrespuesta.setText(f"Se guardó, excepto los archivos: {erroneos}")
                        else:
                            lblrespuesta.setText("Se registró correctamente.")
                        lblrespuesta.setStyleSheet("color: green;")
                        ubicacion_archivo.clear()
                        data = InclinometroController.ctrlTraerDataInclinometro(idinclinometro)
                        if data:
                            idinstrumento, idcomponente, nombrezona = data[0], data[1], data[2]
                            # Eliminar Inclinómetro si existe en arbol
                            treewidgetdatos = main.findChild(QTreeWidget, "tree_actual_datos")
                            treewidgetvisor = main.findChild(QTreeWidget, "tree_actual_visor")
                            treewidgetincli = main.findChild(QTreeWidget, "tree_actual_inclinometros")
                            TreeCheckbox.eliminarCheckbox(treewidgetdatos, "Inclinómetros", idinstrumento, "inclinometro")
                            TreeCheckbox.eliminarCheckbox(treewidgetvisor, "Inclinómetros", idinstrumento, "inclinometro")
                            TreeCheckbox.eliminarCheckbox(treewidgetincli, "Inclinómetros", idinstrumento, "inclinometro")
                            # Crear inclinometro en nuevo componente
                            inclino = InterfazController.ctrlListarComponenteInclinometro(proyectoid, idinstrumento)
                            if inclino:
                                TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetdatos, nombrezona, idcomponente, proyectoid, "Inclinómetros", "2", inclino, "inclinometro")
                                TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetvisor, nombrezona, idcomponente, proyectoid, "Inclinómetros", "3", inclino, "inclinometro", "SI")
                                TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetincli, nombrezona, idcomponente, proyectoid, "Inclinómetros", "1", inclino, "inclinometro", "SI")
                    else:
                        if len(erroneos) > 0:
                            lblrespuesta.setText(f"Error en los archivos: {erroneos}")
                        else:
                            lblrespuesta.setText("No se guardó la data.")
                        lblrespuesta.setStyleSheet("color: red;")
                except ValueError as e:
                    lblrespuesta.setText(str(e))
                    lblrespuesta.setStyleSheet("color: red;")
        boton_subir_archivo.clicked.connect(cargar_archivo)
        boton_procesar_data.clicked.connect(procesar_archivo)
        dialogoInclinometros.exec()
    
    def registrarDataInclinometro(tipo, ubicacion, proyectoid, id_inclinometro):
        erroneos = []
        respuesta = False
        if tipo == 'GEOKON':
            archivos = ubicacion.split("\n")
            for file_name in archivos:
                if file_name.endswith(('.csv', '.gkn', '.txt')):
                    data, fecha_hora = SubirInclinometros.leer_archivo_texto('flevela+a-b+b-', file_name)
                    if data:
                        result = InclinometroController.ctrlRegistrarDataInclinometro(proyectoid, id_inclinometro, fecha_hora, data)
                        if result == "ok":
                            respuesta = True
                    else:
                        nombre_archivo = file_name.split("/")[-1]
                        erroneos.append(nombre_archivo)
        else:  # RST
            archivos = ubicacion.split("\n")
            for file_name in archivos:
                if file_name.endswith(('.csv', '.txt')):
                    data, fecha_hora = SubirInclinometros.leer_archivo_texto('depthfacea+facea-faceb+faceb-', file_name)
                    if data:
                        result = InclinometroController.ctrlRegistrarDataInclinometro(proyectoid, id_inclinometro, fecha_hora, data)
                        if result == "ok":
                            respuesta = True
                    else:
                        nombre_archivo = file_name.split("/")[-1]
                        erroneos.append(nombre_archivo)
        return respuesta, erroneos
    
    def normalizar_encabezado(linea):
        # Convertir todo a minúsculas y eliminar espacios, comas y punto y coma para la comparación
        linea = re.sub(r'[,\s;]+', '', linea).lower()
        return linea

    def limpiar_espacios(linea):
        # Eliminar espacios adicionales en los datos
        return [item.strip() for item in re.split(r'[,\t]+', linea)]

    def extraer_fecha_hora(lines):
        fecha = None
        hora = None

        # Primero buscar la línea que contiene "Reading Date" con una expresión regular más flexible
        for line in lines:
            match = re.search(r'Reading\s*Date\s*\(m/d/y\)\s*,\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s*,\s*(\d{1,2}:\d{1,2}:\d{2})', line.strip())
            if match:
                fecha = match.group(1)
                hora = match.group(2)
                break

        # Si no se encuentra "Reading Date", usar otros patrones de búsqueda
        if not fecha or not hora:
            patrones_fecha = [
                r'DATE\s*:\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # Formato DATE: mm/dd/yy o mm/dd/yyyy
                r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # Formatos mm/dd/yy, mm/dd/yyyy, mm-dd-yy, mm-dd-yyyy
                r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',  # Formato yyyy/mm/dd
                r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})',  # Formato dd/mm/yyyy
            ]
            patrones_hora = [
                r'TIME\s*:\s*(\d{1,2}:\d{1,2}:\d{2})',  # Formato TIME: h:mm:ss o hh:mm:ss
                r'(\d{1,2}:\d{1,2}:\d{2})',  # Formato h:mm:ss o hh:mm:ss
            ]

            for line in lines:
                if not fecha:
                    for patron in patrones_fecha:
                        match = re.search(patron, line.strip())
                        if match:
                            fecha = match.group(1)
                            break
                if not hora:
                    for patron in patrones_hora:
                        match = re.search(patron, line.strip())
                        if match:
                            hora = match.group(1)
                            break
                if fecha and hora:
                    break

        # Si no se encuentra la fecha, usar la fecha actual
        if not fecha:
            fecha = datetime.now().strftime('%m/%d/%Y')
        # Si no se encuentra la hora, usar 00:00:00
        if not hora:
            hora = '00:00:00'

        # Convertir la fecha al formato YYYY-MM-DD
        formatos_fecha = [
            '%m/%d/%Y', '%m/%d/%y', '%m-%d-%Y', '%m-%d-%y',
            '%d/%m/%Y', '%d/%m/%y', '%d-%m-%Y', '%d-%m-%y',
            '%Y/%m/%d', '%Y-%m-%d'
        ]

        for formato in formatos_fecha:
            try:
                fecha = datetime.strptime(fecha, formato).strftime('%Y-%m-%d')
                break
            except ValueError:
                continue
        # Asegurarse de que la hora tenga dos dígitos en horas y minutos
        hora = f"{int(hora.split(':')[0]):02d}:{int(hora.split(':')[1]):02d}:{hora.split(':')[2]}"
        return f"{fecha} {hora}"
    
    def leer_archivo_texto(encabezado, ubicacion):
        codificaciones = ['utf-8', 'ISO-8859-1', 'latin1']
        data = []
        for codificacion in codificaciones:
            try:
                with open(ubicacion, 'r', encoding=codificacion) as file:
                    lines = file.readlines()
                    fecha_hora = SubirInclinometros.extraer_fecha_hora(lines)
                    start_reading = False
                    for i, line in enumerate(lines):
                        if i >= 25 and not start_reading:
                            return False, fecha_hora
                        linea_normalizada = SubirInclinometros.normalizar_encabezado(line)
                        if encabezado in linea_normalizada:
                            start_reading = True
                            continue
                        if start_reading and line.strip():
                            # Dividir la línea por comas o tabulaciones y eliminar espacios adicionales
                            datos_limpios = SubirInclinometros.limpiar_espacios(line.strip())
                            # Verificar si la línea contiene solo comas
                            if all(item == '' for item in datos_limpios):
                                continue  # Omitir esta fila
                            data.append(datos_limpios)
                    return data, fecha_hora
            except UnicodeDecodeError:
                print(f"Error de codificación {codificacion}. Probando la siguiente codificación...")
        raise ValueError("No se pudo determinar la codificación correcta del archivo.")
    
    def obtener_tipo_seleccionado_combo(combo_inclinometro):
        indice_seleccionado = combo_inclinometro.currentIndex()
        tipo_seleccionado = combo_inclinometro.itemData(indice_seleccionado, Qt.UserRole + 1)
        return tipo_seleccionado
    
    def cambiar_componente_inclinometros(idcomponente, idproyecto, treewidget, nombregrupo, tipogrupo, subgrupo, reiniciarvistas):
        dialog = QDialog()
        dialog.setWindowTitle("Componente Inclinómetros")
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
                respuesta = InclinometroController.ctrlCambiarComponenteInclinometros(idproyecto, idcomponente, componente)
                if respuesta:
                    dialog.reject()
                    # Eliminar Inclinómetros
                    TreeCheckbox.eliminarCheckboxGrupo(treewidget, idcomponente, nombregrupo, tipogrupo)
                    # Crear inclinometros en nuevo componente
                    TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidget, nombrezona, componente, idproyecto, nombregrupo, tipogrupo, respuesta, subgrupo, "SI")
                    reiniciarvistas("Inclinómetro")
                else:
                    label_mensaje.setText("Error al cambiar de componente.")
        button_box.accepted.connect(actualizarDatos)
        button_box.rejected.connect(dialog.reject)
        # Mostrar el diálogo
        dialog.setLayout(layout)
        dialog.exec()
    
    def eliminar_inclinometros(idproyecto, idzona, grupo, tipo, treewidget, reiniciarvistas):
        dlg = QMessageBox()
        dlg.setWindowTitle("Eliminar Inclinómetros")
        dlg.setText(f"¿Está seguro eliminar todos los inclinómetros?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            respuesta = InclinometroController.ctrlEliminarInclinometros(idzona)
            if respuesta:
                delete = InclinometroController.ctrlEliminarDataInclinometros(idproyecto, respuesta)
                if delete:
                    TreeCheckbox.eliminarCheckboxGrupo(treewidget, idzona, grupo, tipo)
                    reiniciarvistas("Inclinómetro")
                else:
                    mostrar_mensaje("Eliminar Inclinómetros", "Error al eliminar data inclinómetros.", "advertencia")
            else:
                mostrar_mensaje("Eliminar Inclinómetros", "No se pudo eliminar los inclinómetros.", "advertencia")
    
    def actualizarInclinometro(idproyecto, idcomponente, idinstrumento, treewidget, nombregrupo, tipogrupo, subgrupo, confechas, reiniciarvistas):
        loaderLoading = QUiLoader()
        ui_file_path = resource_path("ui/nuevoinclinometro.ui")
        ui_file = loaderLoading.load(ui_file_path, None)
        dialogoInclinometros = QDialog()
        dialogoInclinometros.setWindowTitle("Actualizar Inclinómetro")
        layout_procesar_data = QVBoxLayout()
        layout_procesar_data.addWidget(ui_file)
        dialogoInclinometros.setLayout(layout_procesar_data)
        # Obtener elementos para interactuar
        comboComponente = dialogoInclinometros.findChild(QComboBox, "cb_lista_componentes")
        comboTipoEquipo = dialogoInclinometros.findChild(QComboBox, "cb_tipo_inclinometro")
        nombreIncli = dialogoInclinometros.findChild(QLineEdit, "input_nombre")
        codigoIncli = dialogoInclinometros.findChild(QLineEdit, "input_codigo")
        esteIncli = dialogoInclinometros.findChild(QDoubleSpinBox, "input_este")
        norteIncli = dialogoInclinometros.findChild(QDoubleSpinBox, "input_norte")
        elevacionIncli = dialogoInclinometros.findChild(QDoubleSpinBox, "input_elevacion")
        inclinacionIncli = dialogoInclinometros.findChild(QSpinBox, "input_inclinacion")
        azimutIncli = dialogoInclinometros.findChild(QSpinBox, "input_azimut")
        profundidadIncli = dialogoInclinometros.findChild(QDoubleSpinBox, "input_profundidad")
        comentarioIncli = dialogoInclinometros.findChild(QTextEdit, "input_comentario")
        lblrespuesta = dialogoInclinometros.findChild(QLabel, "label_mensaje_nuevo_inclinometro")
        botonguardar = dialogoInclinometros.findChild(QPushButton, "btn_aceptar_nuevo_inclinometro")
        # cargar data componentes
        componentes = ProyectoController.ctrlObtenerComponentesProyecto(idproyecto)
        if componentes:
            for fila in componentes:
                comboComponente.addItem(str(fila[2]), fila[0])
            comboComponente.setEnabled(True)
        # mostrar data inclinómetro
        nombreactual = ""
        idincli = 0
        dataincli = InclinometroController.ctrlObtenerInfoInclinometro(idinstrumento)
        if dataincli:
            idincli = dataincli[0]
            comboComponente.setCurrentIndex(comboComponente.findData(idcomponente))
            comboTipoEquipo.setCurrentIndex(comboTipoEquipo.findText(dataincli[2]))
            nombreIncli.setText(str(dataincli[3]))
            nombreactual = str(dataincli[3])
            codigoIncli.setText(str(dataincli[4]))
            esteIncli.setValue(dataincli[5])
            norteIncli.setValue(dataincli[6])
            elevacionIncli.setValue(dataincli[7])
            inclinacionIncli.setValue(dataincli[9])
            azimutIncli.setValue(dataincli[10])
            profundidadIncli.setValue(dataincli[8])
            comentarioIncli.setText(str(dataincli[11]))
        def guardarNuevoInclinometro():
            componente = comboComponente.currentData()
            nombrezona = comboComponente.currentText()
            tipoEquipo = comboTipoEquipo.currentText()
            nombre = nombreIncli.text()
            codigo = codigoIncli.text()
            norte = norteIncli.value()
            este = esteIncli.value()
            nivel = elevacionIncli.value()
            inclinacion = inclinacionIncli.value()
            azimut = azimutIncli.value()
            profundidad = profundidadIncli.value()
            comentario = comentarioIncli.toPlainText()
            # Validación de campos
            if not nombre:
                lblrespuesta.setText("Todos los campos son obligatorios.")
                lblrespuesta.setStyleSheet("color: red;")
                return
            datos = {
                "componente": componente,
                "tipoEquipo": tipoEquipo,
                "nombre": nombre,
                "codigo": codigo,
                "norte": norte,
                "este": este,
                "nivel": nivel,
                "inclinacion": inclinacion,
                "azimut": azimut,
                "profundidad": profundidad,
                "comentario": comentario,
                "instrumento" : idinstrumento,
                "codeincli" : idincli
            }
            respuesta = InclinometroController.ctrlActualizarInclinometro(idproyecto, datos)
            if respuesta:
                dialogoInclinometros.close()
                if str(idcomponente) == str(componente):
                    TreeCheckbox.actualizarTextoCheckboxEquipo(treewidget, idcomponente, nombregrupo, subgrupo, nombreactual, nombre)
                else:
                    # Eliminar Inclinómetro
                    TreeCheckbox.eliminarCheckbox(treewidget, nombregrupo, idinstrumento, subgrupo)
                    # Crear inclinometro en nuevo componente
                    inclino = InterfazController.ctrlListarComponenteInclinometro(idproyecto, idinstrumento)
                    if inclino:
                        TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidget, nombrezona, componente, idproyecto, nombregrupo, tipogrupo, inclino, subgrupo, confechas)
                reiniciarvistas("Inclinómetro")
            else:
                lblrespuesta.setText("Error al actualizar. Por favor, intente de nuevo.")
                lblrespuesta.setStyleSheet("color: red;")
        botonguardar.clicked.connect(guardarNuevoInclinometro)
        dialogoInclinometros.exec()
    
    def eliminar_inclinometro(idproyecto, idinstrumento, nombreinclino, nombregrupo, tipolista, treewidget, reiniciarvistas):
        dlg = QMessageBox()
        dlg.setWindowTitle("Eliminar Inclinómetro")
        dlg.setText(f"¿Está seguro eliminar el inclinómetro '{nombreinclino}'?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            respuesta = InclinometroController.ctrlEliminarInclinometroUnico(idinstrumento)
            if respuesta:
                delete = InclinometroController.ctrlEliminarInclinometroData(idproyecto, respuesta)
                if delete:
                    TreeCheckbox.eliminarCheckbox(treewidget, nombregrupo, idinstrumento, tipolista)
                    reiniciarvistas("Inclinómetro")
                else:
                    mostrar_mensaje("Eliminar Inclinómetro", "Error al eliminar data del inclinómetro.", "advertencia")
            else:
                mostrar_mensaje("Eliminar Inclinómetro", "No se pudo eliminar el inclinómetro.", "advertencia")
    
    def mostrarDialogoFechasInclinometros(treewidget, fechasmarcadas, idproyecto, idcomponente, idinstrumento, nombrecompo, nombreinclino, estado, graficarnuevafechasinclinometros):
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
        lbltitulo.setText("FECHAS DEL INCLINÓMETRO")
        treefechas.setHeaderLabels([nombrecompo])
        listafechas = InclinometroController.ctrlListarFechasInclinometro(idcomponente, idinstrumento, idproyecto)
        idinclinometro = 0
        if listafechas:
            idinclinometro = listafechas[0][4]
            if estado == Qt.Checked and fechasmarcadas is not None:
                # CAMBIO IMPORTANTE: Usamos la función robusta del controlador
                fechaselegidos = InclinometroController.procesar_lista_fechas(fechasmarcadas)
                
                parent = QTreeWidgetItem(treefechas)
                parent.setText(0, nombreinclino)
                parent.setText(1, "1")
                if len(listafechas) == len(fechaselegidos):
                    parent.setCheckState(0, Qt.Checked)
                else:
                    parent.setCheckState(0, Qt.PartiallyChecked)
                parent.setFlags(parent.flags() | Qt.ItemIsUserCheckable)
                parent.setExpanded(True)
                for fechas in listafechas:
                    item = QTreeWidgetItem(parent)
                    
                    # CORRECCIÓN: Aseguramos que la fecha DB (que puede ser datetime) sea String para mostrar y comparar
                    fecha_db_str = str(fechas[0])
                    
                    item.setText(0, fecha_db_str)
                    item.setText(1, "fecha")
                    item.setText(2, str(fechas[3])) # id encabezado
                    item.setText(3, str(fechas[4])) # id incli
                    item.setCheckState(0, Qt.Unchecked)
                    item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable)
                    if fechas[2] == 1: # es base
                        item.setForeground(0, QBrush(QColor("red")))
                    for fechita in fechaselegidos:
                        # Comparamos Strings vs Strings
                        if fechas[2] != 2 and fecha_db_str == fechita:
                            item.setCheckState(0, Qt.Checked)
            else:
                parent = QTreeWidgetItem(treefechas)
                parent.setText(0, nombreinclino)
                parent.setText(1, "1")
                parent.setCheckState(0, Qt.Unchecked)
                parent.setFlags(parent.flags() | Qt.ItemIsUserCheckable)
                parent.setExpanded(True)
                for fechas in listafechas:
                    item = QTreeWidgetItem(parent)
                    # CORRECCIÓN: Convertir a string para visualización
                    item.setText(0, str(fechas[0]))
                    item.setText(1, "fecha")
                    item.setText(2, str(fechas[3]))
                    item.setText(3, str(fechas[4]))
                    item.setCheckState(0, Qt.Unchecked)
                    item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable)
                    if fechas[2] == 1: # es base
                        item.setForeground(0, QBrush(QColor("red")))
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
                        idencabezado = item.text(2)
                        idinclinome = item.text(3)
                        edit_fecha = menu.addAction("Cambiar a Base")
                        edit_fecha.triggered.connect(lambda: SubirInclinometros.cambiarFechaBaseInclinometro(treefechas, idencabezado, idinclinome, fechaelegida))
                        if Session.is_authenticated() and Session.get_idrole != 3:
                            delete_fecha = menu.addAction("Eliminar Lectura")
                            delete_fecha.triggered.connect(lambda: SubirInclinometros.eliminarFechaDataInclinometro(treefechas, idproyecto, idencabezado, idinclinome, fechaelegida))
                menu.exec(treefechas.mapToGlobal(point))
        def obtenerFechasMarcadas():
            nonlocal idinclinometro
            fechasmarcadas = []
            lecturasdesmarcadas = []
            parent = treefechas.topLevelItem(0)
            if parent:
                for i in range(parent.childCount()):
                    hijo = parent.child(i)
                    if hijo.checkState(0) == Qt.Checked:
                        fechasmarcadas.append(hijo.text(0))
                    elif hijo.checkState(0) == Qt.Unchecked:
                        lecturasdesmarcadas.append(hijo.text(2))
            if len(fechasmarcadas) > 0:
                respuesta = InclinometroController.ctrlCambiarEstadoFechasInclinometro(lecturasdesmarcadas, idinclinometro)
                if respuesta:
                    TreeCheckbox.actualizarFechasCheckboxEquipo(treewidget, idcomponente, "Inclinómetros", "inclinometro", nombreinclino, fechasmarcadas)
                    graficarnuevafechasinclinometros()
            dialogo.close()
        # conectar funciones
        treefechas.itemClicked.connect(marcadoDesmarcadoCheckbox)
        treefechas.setContextMenuPolicy(Qt.CustomContextMenu)
        treefechas.customContextMenuRequested.connect(menuCambiarBaseCheckbox)
        botonaceptar.clicked.connect(obtenerFechasMarcadas)
        dialogo.exec()
    
    def cambiarFechaBaseInclinometro(treewidget, idencabezado, idinclinome, fecha):
        dlg = QMessageBox()
        dlg.setWindowTitle("Cambiar Base Inclinómetro")
        dlg.setText(f"¿Elegir la '{fecha}' como base?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            respuesta = InclinometroController.ctrlCambiarBaseInclinometro(idencabezado, idinclinome)
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
                mostrar_mensaje("Base Inclinómetro", "No se pudo cambiar de base.", "advertencia")
    
    def eliminarFechaDataInclinometro(treewidget, idproyecto, idencabezado, idinclinome, fecha):
        dlg = QMessageBox()
        dlg.setWindowTitle("Eliminar Lectura Inclinómetro")
        dlg.setText(f"¿Está seguro de eliminar la lectura '{fecha}'?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            username = Session.get_username()
            nombres = Session.get_nombres()
            if Session.is_authenticated():
                respuesta = InclinometroController.ctrlEliminarLecturaInclinometro(idproyecto, idencabezado, idinclinome, username, nombres)
                if respuesta:
                    root_item = treewidget.invisibleRootItem()
                    for i in range(root_item.childCount()):
                        equipo_item = root_item.child(i)
                        for j in range(equipo_item.childCount()):
                            fecha_item = equipo_item.child(j)
                            if fecha_item.text(0) == str(fecha) and fecha_item.text(2) == str(idencabezado):
                                # Eliminar el checkbox seleccionado
                                equipo_item.removeChild(fecha_item)
                else:
                    mostrar_mensaje("Eliminar Inclinómetro", "No se pudo eliminar la lectura.", "advertencia")
    
    def cambiar_componente_bloque_inclinometro(idproyecto, idcomponente, parent, treewidget, nombregrupo, tipogrupo, subgrupo, reiniciarvistas):
        dialog = QDialog()
        dialog.setWindowTitle("Mover Inclinómetros Componente")
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
                        respuesta = InclinometroController.ctrlCambiarInclinometroComponente(idinstrumento, componente)
                        if respuesta:
                            hijos_marcados.append(hijo)
                            result = True
                if result:
                    dialog.reject()
                    for hijo in hijos_marcados:
                        idinstrumento = hijo.text(2)
                        TreeCheckbox.eliminarCheckbox(treewidget, nombregrupo, idinstrumento, subgrupo)
                        # Crear prisma en nuevo componente
                        inclinome = InterfazController.ctrlListarComponenteInclinometro(idproyecto, idinstrumento)
                        if inclinome:
                            TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidget, nombrezona, componente, idproyecto, nombregrupo, tipogrupo, inclinome, subgrupo)
                    reiniciarvistas("Inclinómetro")
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