import os
import shutil
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QComboBox, QPlainTextEdit, QPushButton, QTreeWidget, QFormLayout,
                            QDialogButtonBox, QMessageBox, QLabel, QLineEdit, QFileDialog,QDateEdit)
from PySide6.QtCore import Qt, QFileInfo
from datetime import datetime
from utils.common.rutasarchivos import resource_path
from utils.generic.cargariconos import cargarIcono
from utils.common.alertas import mostrar_mensaje
from utils.generic.listaiconos import ListaIconos
from utils.shared.arbolmarcado import TreeCheckbox
from controllers.ProyectoController import ProyectoController
from controllers.TopografiaController import TopografiaController
from controllers.InterfazController import InterfazController
from PySide6.QtCore import QDate

class SubirTopografias:
    archivoTopo = None
    
    def dialogoNuevaTopografia(idproyecto, main):
        loader = QUiLoader()
        ui_file_path = resource_path("ui/nuevatopografia.ui")
        ui_file = loader.load(ui_file_path, None)
        # Configurar el cuadro de diálogo principal
        dialogo = QDialog()
        dialogo.setWindowTitle("Nueva Topografía")
        layout = QVBoxLayout()
        layout.addWidget(ui_file)
        dialogo.setLayout(layout)
        # Obtener elementos para interactuar
        combocomponente = dialogo.findChild(QComboBox, "combo_componente")
        labelnombretopo = dialogo.findChild(QLabel, "label_archivo")
        botonsubir = dialogo.findChild(QPushButton, "btn_cargar_archivo")
        cargarIcono(botonsubir, ListaIconos.ICONOS["subir_archivo"])
        inputnombre = dialogo.findChild(QLineEdit, "input_nombre")
        fecha_edit = dialogo.findChild(QDateEdit, "date_fecha_topo")
        inputcomenta = dialogo.findChild(QPlainTextEdit, "input_comentario")
        labelmensaje = dialogo.findChild(QLabel, "label_mensaje")
        botonaceptar = dialogo.findChild(QPushButton, "btn_guardar")
        fecha_edit.setDate(QDate.currentDate())
        # cargar data componentes
        componentes = ProyectoController.ctrlObtenerComponentesProyecto(idproyecto)
        if componentes:
            for fila in componentes:
                combocomponente.addItem(str(fila[2]), fila[0])
        def cargarArchivoTopo():
            file_dialog = QFileDialog()
            file_dialog.setNameFilter("Archivos DXF, LAS, LAZ o VTP (*.dxf *.las *.laz *.vtp)")
            if file_dialog.exec():
                selected_files = file_dialog.selectedFiles()
                if selected_files:
                    file_path = selected_files[0]
                    file_name = QFileInfo(file_path).fileName()
                    SubirTopografias.archivoTopo = file_path
                    labelnombretopo.setText(file_name)
                    inputnombre.setText(file_name.split('.')[0])
        def guardarTopografia():
            botonaceptar.setEnabled(False)
            idcomponente = combocomponente.currentData()
            nombrezona = combocomponente.currentText()
            nombrenuevo = inputnombre.text()
            comentario = inputcomenta.toPlainText()
            fecha = fecha_edit.date()
            fecha_formateada=fecha.toString("yyyy-MM-dd")
            if nombrenuevo != "" and SubirTopografias.archivoTopo is not None:
                if SubirTopografias.archivoTopo.lower().endswith(('.dxf')):
                    tipo = "VTP"
                    result = TopografiaController.ctrlRegistrarNuevaTopografia2(idproyecto, idcomponente, nombrenuevo, SubirTopografias.archivoTopo, tipo, comentario, fecha_formateada)
                elif SubirTopografias.archivoTopo.lower().endswith(('.las')):
                    tipo = "LAS"
                    result = TopografiaController.ctrlRegistrarNuevaTopografia(idproyecto, idcomponente, nombrenuevo, SubirTopografias.archivoTopo, tipo, ".las", comentario, fecha_formateada)
                elif SubirTopografias.archivoTopo.lower().endswith(('.laz')):
                    tipo = "LAS"
                    result = TopografiaController.ctrlRegistrarNuevaTopografia(idproyecto, idcomponente, nombrenuevo, SubirTopografias.archivoTopo, tipo, ".laz", comentario, fecha_formateada)
                elif SubirTopografias.archivoTopo.lower().endswith(('.vtp')):
                    tipo = "VTP"
                    result = TopografiaController.ctrlRegistrarNuevaTopografia(idproyecto, idcomponente, nombrenuevo, SubirTopografias.archivoTopo, tipo, ".vtp", comentario, fecha_formateada)
                if result is not None:
                    dialogo.close()
                    SubirTopografias.archivoTopo = None
                    # Agregar nueva topografía en el arbol
                    topogra = InterfazController.ctrlListarComponenteTopografia(result)
                    if topogra:
                        treewidget = main.findChild(QTreeWidget, "tree_actual_visor")
                        TreeCheckbox.crearGrupoCheckboxDobleTopografia(treewidget, nombrezona, idcomponente, idproyecto, "Topografías", "1", topogra, "topografia")
                else:
                    botonaceptar.setEnabled(True)
                    labelmensaje.setText("Error al al guardar la topografía.")
            else:
                botonaceptar.setEnabled(True)
                labelmensaje.setText("Todos los campos son obligatorios.")
        # Inicializar botones
        botonsubir.clicked.connect(cargarArchivoTopo)
        botonaceptar.clicked.connect(guardarTopografia)
        # mostrar dialogo
        dialogo.exec()
    
    def cambiar_componente_topografias(idcomponente, idproyecto, treewidget, nombregrupo, tipogrupo, subgrupo, validarMostrarTopografias):
        dialog = QDialog()
        dialog.setWindowTitle("Cambiar Componente Topografías")
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
                respuesta = TopografiaController.ctrlCambiarComponenteTopografias(idcomponente, componente)
                if respuesta:
                    dialog.reject()
                    # Eliminar topos
                    TreeCheckbox.eliminarCheckboxGrupo(treewidget, idcomponente, nombregrupo, tipogrupo)
                    # Agregar topos en nuevo componente
                    TreeCheckbox.crearGrupoCheckboxDobleTopografia(treewidget, nombrezona, componente, idproyecto, nombregrupo, tipogrupo, respuesta, subgrupo)
                    validarMostrarTopografias()
                else:
                    label_mensaje.setText("Error al cambiar de componente.")
        button_box.accepted.connect(actualizarDatos)
        button_box.rejected.connect(dialog.reject)
        # Mostrar el diálogo
        dialog.setLayout(layout)
        dialog.exec()
    
    def eliminar_topografias(idzona, grupo, tipo, treewidget, validarMostrarTopografias):
        dlg = QMessageBox()
        dlg.setWindowTitle("Eliminar Topografías")
        dlg.setText(f"¿Está seguro eliminar todos las Topografías?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.button(QMessageBox.Yes).setText("Sí")
        dlg.button(QMessageBox.No).setText("No")
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            respuesta = TopografiaController.ctrlEliminarTopografias(idzona)
            if respuesta:
                delete = TopografiaController.ctrlEliminarDataTopografias(respuesta)
                if delete:
                    TreeCheckbox.eliminarCheckboxGrupo(treewidget, idzona, grupo, tipo)
                    validarMostrarTopografias()
                    # falta eliminar el bloque de la carpeta
                else:
                    mostrar_mensaje("Eliminar Topografías", "Error al eliminar data Topografías.", "advertencia")
            else:
                mostrar_mensaje("Eliminar Topografías", "No se pudo eliminar las Topografías.", "advertencia")
    
    def actualizarTopografia(idproyecto, idcomponente, idinstrumento, treewidget, nombregrupo, tipogrupo, subgrupo, validarMostrarTopografias):
        loader = QUiLoader()
        ui_file_path = resource_path("ui/editartopografia.ui")
        ui_file = loader.load(ui_file_path, None)
        # Configurar el cuadro de diálogo principal
        dialogo = QDialog()
        dialogo.setWindowTitle("Actualizar Topografía")
        layout = QVBoxLayout()
        layout.addWidget(ui_file)
        dialogo.setLayout(layout)
        # Obtener elementos para interactuar
        combocomponente = dialogo.findChild(QComboBox, "combo_componente")
        inputnombre = dialogo.findChild(QLineEdit, "input_nombre")
        inputcomenta = dialogo.findChild(QPlainTextEdit, "input_comentario")
        labelmensaje = dialogo.findChild(QLabel, "label_mensaje")
        fecha_edit = dialogo.findChild(QDateEdit, "date_fecha_topo")
        botonaceptar = dialogo.findChild(QPushButton, "btn_guardar")
        # cargar data componentes
        componentes = ProyectoController.ctrlObtenerComponentesProyecto(idproyecto)
        if componentes:
            for fila in componentes:
                combocomponente.addItem(str(fila[2]), fila[0])
        # mostrar data topo
        nombreactual = ""
        idtopografia = 0
        datatopo = TopografiaController.ctrlObtenerInfoTopografia(idinstrumento)
        if datatopo:
            idtopografia = datatopo[0]
            combocomponente.setCurrentIndex(combocomponente.findData(idcomponente))
            inputnombre.setText(str(datatopo[2]))
            nombreactual = str(datatopo[2])
            inputcomenta.setPlainText(str(datatopo[5]))
            fecha_dato = datatopo[7]
            if isinstance(fecha_dato, datetime):
                fecha_qdate = QDate(fecha_dato.year, fecha_dato.month, fecha_dato.day)
            elif isinstance(fecha_dato, str):
                fecha_qdate = QDate.fromString(fecha_dato, "yyyy-MM-dd")
            else:
                fecha_qdate = QDate.currentDate()
            fecha_edit.setDate(fecha_qdate)
        def actualizarDatos():
            componente = combocomponente.currentData()
            nombrezona = combocomponente.currentText()
            nombrenuevo = inputnombre.text()
            comentario = inputcomenta.toPlainText()
            fecha_actual = fecha_edit.date()
            asignarfecha = fecha_actual.toString("yyyy-MM-dd")
            if nombrenuevo != "":
                resultado = TopografiaController.ctrlActualizarTopografia(componente, nombrenuevo, comentario, asignarfecha, idinstrumento, idtopografia)
                if resultado:
                    dialogo.close()
                    if str(idcomponente) == str(componente):
                        TreeCheckbox.actualizarTextoCheckboxEquipo(treewidget, idcomponente, nombregrupo, subgrupo, nombreactual, nombrenuevo)
                    else:
                        # Eliminar topo
                        TreeCheckbox.eliminarCheckbox(treewidget, nombregrupo, idinstrumento, subgrupo)
                        # Crear topo nuevo componente
                        topo = InterfazController.ctrlListarComponenteTopografia(idinstrumento)
                        if topo:
                            TreeCheckbox.crearGrupoCheckboxDobleTopografia(treewidget, nombrezona, componente, idproyecto, nombregrupo, tipogrupo, topo, subgrupo)
                            validarMostrarTopografias()
                else:
                    labelmensaje.setText("Error al actualizar la topografía.")
            else:
                labelmensaje.setText("Todos los campos son obligatorios.")
        # conectar señales
        botonaceptar.clicked.connect(actualizarDatos)
        dialogo.exec()
    
    def eliminar_topografia(idinstrumento, nombretopo, nombregrupo, tipolista, treewidget, validarMostrarTopografias):
        dlg = QMessageBox()
        dlg.setWindowTitle("Eliminar Topografía")
        dlg.setText(f"¿Está seguro eliminar la Topografía '{nombretopo}'?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.button(QMessageBox.Yes).setText("Sí")
        dlg.button(QMessageBox.No).setText("No")
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            respuesta = TopografiaController.ctrlEliminarTopografia(idinstrumento)
            if respuesta:
                delete = TopografiaController.ctrlEliminarTopografiaData(respuesta)
                if delete:
                    TreeCheckbox.eliminarCheckbox(treewidget, nombregrupo, idinstrumento, tipolista)
                    validarMostrarTopografias()
                    carpeta = resource_path(respuesta[7])
                    # eliminar carpeta con topografía
                    if os.path.exists(carpeta) and os.path.isdir(carpeta):
                        try:
                            shutil.rmtree(carpeta)
                        except PermissionError:
                            mostrar_mensaje("Eliminar Topografía", "Error al eliminar los archivos.", "advertencia")
                        except Exception as e:
                            mostrar_mensaje("Eliminar Topografía", "Error al eliminar los archivos.", "advertencia")
                else:
                    mostrar_mensaje("Eliminar Topografía", "Error al eliminar data de la topografía.", "advertencia")
            else:
                mostrar_mensaje("Eliminar Topografía", "No se pudo eliminar la topografía.", "advertencia")
    
    def eliminar_elemento(idinstrumento, nombreactor, rutaactor, nombregrupo, tipolista, tipolistaactor, treewidget, validarMostrarTopografias):
        dlg = QMessageBox()
        dlg.setWindowTitle("Eliminar Elemento de Topografía")
        dlg.setText(f"¿Está seguro eliminar el elemento '{nombreactor}'?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.button(QMessageBox.Yes).setText("Sí")
        dlg.button(QMessageBox.No).setText("No")
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            # validar si hay un elemento
            directorio = os.path.dirname(rutaactor)
            archivos = os.listdir(directorio)
            cantidad = len([f for f in archivos if os.path.isfile(os.path.join(directorio, f))])
            if cantidad > 1:
                try:
                    if os.path.exists(rutaactor):
                        TreeCheckbox.eliminarCheckboxTopografia(treewidget, nombregrupo, tipolista, idinstrumento, tipolistaactor, rutaactor)
                        validarMostrarTopografias()
                        os.remove(rutaactor)
                    else:
                        mostrar_mensaje("Eliminar Topografía", "Error al eliminar el archivo.", "advertencia")
                except PermissionError:
                    mostrar_mensaje("Eliminar Topografía", "No hay permisos para eliminar el archivo.", "advertencia")
                except OSError as e:
                    mostrar_mensaje("Eliminar Topografía", "No se pudo eliminar el archivo.", "advertencia")
            else:
                respuesta = TopografiaController.ctrlEliminarTopografia(idinstrumento)
                if respuesta:
                    delete = TopografiaController.ctrlEliminarTopografiaData(respuesta)
                    if delete:
                        TreeCheckbox.eliminarCheckbox(treewidget, nombregrupo, idinstrumento, tipolista)
                        validarMostrarTopografias()
                        carpeta = resource_path(respuesta[7])
                        # eliminar carpeta con topografía
                        if os.path.exists(carpeta) and os.path.isdir(carpeta):
                            try:
                                shutil.rmtree(carpeta)
                            except PermissionError:
                                mostrar_mensaje("Eliminar Topografía", "Error al eliminar los archivos.", "advertencia")
                            except Exception as e:
                                mostrar_mensaje("Eliminar Topografía", "Error al eliminar los archivos.", "advertencia")
                    else:
                        mostrar_mensaje("Eliminar Topografía", "Error al eliminar data de la topografía.", "advertencia")
                else:
                    mostrar_mensaje("Eliminar Topografía", "No se pudo eliminar la topografía.", "advertencia")
    