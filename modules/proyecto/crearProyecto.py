from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDateEdit, QLabel, QTextEdit, QPushButton, QMessageBox,
                               QTableWidget, QTableWidgetItem)
from PySide6.QtCore import QDate, Qt
from utils.common.alertas import mostrar_mensaje
from utils.common.rutasarchivos import resource_path
from utils.shared.arbolmarcado import TreeCheckbox
from controllers.ProyectoController import ProyectoController

class CrearProyecto:
    creado, idproyecto = False, None
    
    def formularioRegistroNuevoProyecto():
        CrearProyecto.creado, CrearProyecto.idproyecto = False, None
        dialog = QDialog()
        dialog.setWindowTitle("Nuevo Proyecto")
        layout = QVBoxLayout(dialog)
        form_layout = QFormLayout()
        # Campos del formulario
        nombre_proyecto = QLineEdit()
        fecha_proyecto = QDateEdit()
        fecha_proyecto.setCalendarPopup(True)
        fecha_proyecto.setDate(QDate.currentDate())
        comentario_proyecto = QTextEdit()
        # Añadir los campos al layout del formulario
        form_layout.addRow("Nombre del Proyecto:", nombre_proyecto)
        form_layout.addRow("Fecha:", fecha_proyecto)
        form_layout.addRow("Comentario:", comentario_proyecto)
        # Añadir el formulario al layout principal
        layout.addLayout(form_layout)
        # Botón para guardar
        label_mensaje = QLabel()
        label_mensaje.setAlignment(Qt.AlignCenter)
        label_mensaje.setStyleSheet("color: red;")
        boton_guardar = QPushButton("Guardar")
        # Conectar el botón "Guardar"
        def guardar_proyecto():
            nombre = nombre_proyecto.text()
            fecha = fecha_proyecto.date().toString("yyyy-MM-dd")
            comentario = comentario_proyecto.toPlainText()
            if nombre and nombre != "":
                respuesta, idproyecto = ProyectoController.ctrlRegistarProyecto(nombre, fecha, comentario)
                if respuesta:
                    componente = ProyectoController.ctrlRegistarComponente(idproyecto, 'GENERAL')
                    if componente:
                        CrearProyecto.creado, CrearProyecto.idproyecto = True, idproyecto
                        dialog.close()
                    else:
                        label_mensaje.setText("Error al crear el componente.")
                else:
                    label_mensaje.setText("Error al crear el proyecto.")
            else:
                label_mensaje.setText("El nombre no debe ir vacío.")
        # Añadir el botón al layout principal
        layout.addWidget(label_mensaje)
        layout.addWidget(boton_guardar)
        boton_guardar.clicked.connect(guardar_proyecto)
        dialog.exec()
        return CrearProyecto.creado, CrearProyecto.idproyecto
    
    def formularioActualizarProyecto(idproyecto):
        result = False
        dialog = QDialog()
        dialog.setWindowTitle("Editar Proyecto")
        layout = QVBoxLayout(dialog)
        form_layout = QFormLayout()
        # Campos del formulario
        nombre_proyecto = QLineEdit()
        fecha_proyecto = QDateEdit()
        fecha_proyecto.setCalendarPopup(True)
        fecha_proyecto.setDate(QDate.currentDate())
        comentario_proyecto = QTextEdit()
        # Añadir los campos al layout del formulario
        form_layout.addRow("Nombre del Proyecto:", nombre_proyecto)
        form_layout.addRow("Fecha:", fecha_proyecto)
        form_layout.addRow("Comentario:", comentario_proyecto)
        # Añadir el formulario al layout principal
        layout.addLayout(form_layout)
        # Botón para guardar
        label_mensaje = QLabel()
        label_mensaje.setAlignment(Qt.AlignCenter)
        label_mensaje.setStyleSheet("color: red;")
        boton_guardar = QPushButton("Guardar")
        # cargar data
        proyecto = ProyectoController.ctrlObtenerInfoProyecto(idproyecto)
        if proyecto:
            nombre_proyecto.setText(proyecto[1])
            fecha_qdate = QDate.fromString(proyecto[2], "yyyy-MM-dd")
            fecha_proyecto.setDate(fecha_qdate)
            comentario_proyecto.setPlainText(proyecto[3])
        # Conectar el botón "Guardar"
        def actualizar_proyecto():
            nonlocal result
            nombre = nombre_proyecto.text()
            fecha = fecha_proyecto.date().toString("yyyy-MM-dd")
            comentario = comentario_proyecto.toPlainText()
            if nombre and nombre != "":
                respuesta = ProyectoController.ctrlActualizarProyecto(nombre, fecha, comentario, idproyecto)
                if respuesta:
                    result = True
                    dialog.close()
                else:
                    label_mensaje.setText("Error al actualizar el proyecto.")
            else:
                label_mensaje.setText("El nombre no debe ir vacío.")
        # Añadir el botón al layout principal
        layout.addWidget(label_mensaje)
        layout.addWidget(boton_guardar)
        boton_guardar.clicked.connect(actualizar_proyecto)
        dialog.exec()
        return result
    
    def registro_componente(idproyecto):
        result = False
        dialog = QDialog()
        dialog.setWindowTitle("Registro de Componente")
        dialog.setMinimumWidth(250)
        # Layout principal vertical
        layout = QVBoxLayout(dialog)
        layout.setSpacing(10)
        label_nombre = QLabel("Nombre del componente:")
        # Campo de entrada
        nombre_input = QLineEdit()
        # Label para mensajes de error
        label_mensaje = QLabel()
        label_mensaje.setAlignment(Qt.AlignCenter)
        label_mensaje.setStyleSheet("color: red;")
        boton_guardar = QPushButton("Guardar")
        # Añadir el botón al layout principal
        layout.addWidget(label_nombre)
        layout.addWidget(nombre_input)
        layout.addWidget(label_mensaje)
        layout.addWidget(boton_guardar)
        def guardar_componente():
            nonlocal result
            nombre = nombre_input.text()
            if nombre:
                componente = ProyectoController.ctrlRegistarComponente(idproyecto, nombre)
                if componente:
                    dialog.accept()
                    result = True
                else:
                    label_mensaje.setText("Error al registrar componente.")
            else:
                label_mensaje.setText("El nombre del componente es obligatorio.")
        # Conectar el botón de guardar a la función de guardado
        boton_guardar.clicked.connect(guardar_componente)
        dialog.exec()
        return result
    
    def dialogo_editar_componente(idcomponente, nombrecompo, treewidget, reiniciarvistas):
        result = False
        dialog = QDialog()
        dialog.setWindowTitle("Actualizar Componente")
        dialog.setMinimumWidth(250)
        # Layout principal vertical
        layout = QVBoxLayout(dialog)
        layout.setSpacing(10)
        label_nombre = QLabel("Nombre del componente:")
        # Campo de entrada
        nombre_input = QLineEdit()
        nombre_input.setText(nombrecompo)
        # Label para mensajes de error
        label_mensaje = QLabel()
        label_mensaje.setAlignment(Qt.AlignCenter)
        label_mensaje.setStyleSheet("color: red;")
        boton_guardar = QPushButton("Guardar")
        # Añadir el botón al layout principal
        layout.addWidget(label_nombre)
        layout.addWidget(nombre_input)
        layout.addWidget(label_mensaje)
        layout.addWidget(boton_guardar)
        def actualizarComponente():
            nonlocal result
            nombrenuevo = nombre_input.text()
            if nombrenuevo != "":
                respuesta = ProyectoController.ctrlActualizarComponente(nombrenuevo, idcomponente)
                if respuesta:
                    dialog.reject()
                    TreeCheckbox.actualizarTextoCheckboxParent(treewidget, nombrecompo, idcomponente, nombrenuevo)
                    reiniciarvistas()
                    result = True
                else:
                    label_mensaje.setText("Error al actualizar el componente.")
            else:
                label_mensaje.setText("El nombre está vacío.")
        # Conectar el botón de guardar a la función de guardado
        boton_guardar.clicked.connect(actualizarComponente)
        dialog.exec()
        return result
    
    def dialogo_editar_componente_reporte(idcomponente, nombrecompo, reiniciarvistas):
        result = False
        dialog = QDialog()
        dialog.setWindowTitle("Actualizar Componente")
        dialog.setMinimumWidth(250)
        # Layout principal vertical
        layout = QVBoxLayout(dialog)
        layout.setSpacing(10)
        label_nombre = QLabel("Nombre del componente:")
        # Campo de entrada
        nombre_input = QLineEdit()
        nombre_input.setText(nombrecompo)
        # Label para mensajes de error
        label_mensaje = QLabel()
        label_mensaje.setAlignment(Qt.AlignCenter)
        label_mensaje.setStyleSheet("color: red;")
        boton_guardar = QPushButton("Guardar")
        # Añadir el botón al layout principal
        layout.addWidget(label_nombre)
        layout.addWidget(nombre_input)
        layout.addWidget(label_mensaje)
        layout.addWidget(boton_guardar)
        def actualizarComponente():
            nonlocal result
            nombrenuevo = nombre_input.text()
            if nombrenuevo != "":
                respuesta = ProyectoController.ctrlActualizarComponente(nombrenuevo, idcomponente)
                if respuesta:
                    dialog.reject()
                    reiniciarvistas()
                    result = True
                else:
                    label_mensaje.setText("Error al actualizar el componente.")
            else:
                label_mensaje.setText("El nombre está vacío.")
        # Conectar el botón de guardar a la función de guardado
        boton_guardar.clicked.connect(actualizarComponente)
        dialog.exec()
        return result
    
    def eliminar_componente(idproyecto, idzona, nombrezona, treewidget, reiniciarvistas):
        resultado = False
        dlg = QMessageBox()
        dlg.setWindowTitle("Eliminar Componente")
        dlg.setText(f"¿Desea eliminar el componente '{nombrezona}'?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            respuesta = ProyectoController.ctrlEliminarComponente(idproyecto, idzona)
            if respuesta:
                TreeCheckbox.eliminarCheckboxParent(treewidget, nombrezona, idzona)
                reiniciarvistas()
                resultado = True
            else:
                mostrar_mensaje("Eliminar Lectura", "No se pudo eliminar el componente.", "advertencia")
        return resultado
    
    def eliminar_componente_reporte(idproyecto, idzona, nombrezona, reiniciarvistas):
        resultado = False
        dlg = QMessageBox()
        dlg.setWindowTitle("Eliminar Componente")
        dlg.setText(f"¿Desea eliminar el componente '{nombrezona}'?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            respuesta = ProyectoController.ctrlEliminarComponente(idproyecto, idzona)
            if respuesta:
                reiniciarvistas()
                resultado = True
            else:
                mostrar_mensaje("Eliminar Lectura", "No se pudo eliminar el componente.", "advertencia")
        return resultado
    
    def dialogoDatosHistorialCambiosDatabase():
        loader = QUiLoader()
        ui_file_path = resource_path("ui/historialcambios.ui")
        ui_file = loader.load(ui_file_path, None)
        # Configurar el cuadro de diálogo
        dialog = QDialog()
        dialog.setWindowTitle("Historial de Cambios Database")
        layout = QVBoxLayout()
        layout.addWidget(ui_file)
        dialog.setLayout(layout)
        # Obtener elementos para interactuar
        tabladatos = dialog.findChild(QTableWidget, "table_historial_datos")
        tablaanalisis = dialog.findChild(QTableWidget, "table_historial_analisis")
        botonaceptar = dialog.findChild(QPushButton, "btn_aceptar")
        # Mostrar data en la tabla
        historial = ProyectoController.ctrlObtenerHistorialCambios()
        if historial:
            tabladatos.setRowCount(len(historial))
            tabladatos.setColumnCount(7)
            for fila, datos_fila in enumerate(historial):
                for columna, dato in enumerate(datos_fila):
                    item = QTableWidgetItem(str(dato))
                    tabladatos.setItem(fila, columna, item)
            tabladatos.setColumnWidth(5, 500)
        datacambios = ProyectoController.ctrlObtenerAjustesCambios()
        if datacambios:
            tablaanalisis.setRowCount(len(datacambios))
            tablaanalisis.setColumnCount(7)
            for fila, datos_fila in enumerate(datacambios):
                for columna, dato in enumerate(datos_fila):
                    item = QTableWidgetItem(str(dato))
                    tablaanalisis.setItem(fila, columna, item)
            tablaanalisis.setColumnWidth(5, 500)
        def aceptarHistorial():
            dialog.close()
        # Inicializar botones
        botonaceptar.clicked.connect(aceptarHistorial)
        dialog.exec()
    