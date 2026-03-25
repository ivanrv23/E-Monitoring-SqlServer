from PySide6.QtGui import Qt, QAction
from PySide6.QtWidgets import (QDialog, QPushButton, QVBoxLayout, QTableWidgetItem, QLabel, QComboBox, QTableWidget, QHBoxLayout,
                               QDoubleSpinBox, QSpacerItem, QSizePolicy, QMenu)
from utils.common.alertas import mostrar_mensaje
from controllers.EstratoController import EstratoController
from controllers.InterfazController import InterfazController
from utils.common.metodosGenerales import MetodosGenerales

class ConfigurarEstratos:
    
    def modalEstratos(proyectoid):
        listacomponente = InterfazController.ctrlListarComponentesProyecto(proyectoid)
        # Crear el diálogo
        dialog = QDialog()
        dialog.setWindowTitle("Registro de Estratos")
        # Layout principal
        main_layout = QVBoxLayout()

        # Layout para el ComboBox y el botón "Agregar Fila"
        combo_button_layout = QHBoxLayout()

        # Nuevo ComboBox al inicio
        component_combo_label = QLabel("Seleccione Componente:")
        component_combo = QComboBox()

        if listacomponente:
            # Añadir opciones al nuevo ComboBox desde listacomponente
            for componente in listacomponente:
                component_combo.addItem(componente[2], userData=componente[0])  # componente[2] es el nombre, componente[0] es el ID
            # Seleccionar el primer elemento por defecto
            component_combo.setCurrentIndex(0)

        # Añadir el nuevo ComboBox y el botón al layout horizontal
        combo_button_layout.addWidget(component_combo_label)
        combo_button_layout.addWidget(component_combo)

        # Botón "Agregar Fila"
        add_button = QPushButton("Agregar Fila")
        combo_button_layout.addWidget(add_button)

        # Añadir el layout horizontal al layout principal
        main_layout.addLayout(combo_button_layout)

        # Tabla
        table = QTableWidget(3, 4)  # 3 filas y 4 columnas
        table.setHorizontalHeaderLabels(["Nombre", "Color", "Rango Mínimo", "Rango Máximo"])

        # Ajustar el ancho de la columna "Nombre"
        table.setColumnWidth(0, 200)  # Puedes ajustar el valor según tus necesidades

        # Función para reiniciar la tabla
        def reset_table():
            table.setRowCount(3)
            for row in range(3):
                # Nombre
                nombre_item = QTableWidgetItem("")
                table.setItem(row, 0, nombre_item)

                # Botón de color
                color_button = QPushButton()
                color_button.clicked.connect(lambda *args, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
                table.setCellWidget(row, 1, color_button)

                # Rango Mínimo (DoubleSpinBox)
                min_spinbox = QDoubleSpinBox()
                min_spinbox.setRange(-1e9, 1e9)  # Rango grande
                min_spinbox.setDecimals(5)  # Hasta 5 decimales
                table.setCellWidget(row, 2, min_spinbox)

                # Rango Máximo (DoubleSpinBox)
                max_spinbox = QDoubleSpinBox()
                max_spinbox.setRange(-1e9, 1e9)  # Rango grande
                max_spinbox.setDecimals(5)  # Hasta 5 decimales
                table.setCellWidget(row, 3, max_spinbox)

        def load_estratos():
            selected_component_id = component_combo.currentData()  # Obtener el ID del componente seleccionado
            estratos = EstratoController.ctrObtenerEstratosInstrumentacion(proyectoid, selected_component_id)

            if estratos:
                table.setRowCount(len(estratos))
                for row, estrato in enumerate(estratos):
                    # Nombre
                    nombre_item = QTableWidgetItem(estrato[3])  # Asumiendo que el nombre está en la posición 3
                    nombre_item.setData(Qt.UserRole, estrato[0])  # Guardar el ID del estrato en el item
                    table.setItem(row, 0, nombre_item)

                    # Botón de color
                    color_button = QPushButton()
                    color_button.setStyleSheet(f"background-color: {estrato[4]};")  # Asumiendo que el color está en la posición 4
                    color_button.clicked.connect(lambda *args, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
                    table.setCellWidget(row, 1, color_button)

                    # Rango Mínimo (DoubleSpinBox)
                    min_spinbox = QDoubleSpinBox()
                    min_spinbox.setRange(-1e9, 1e9)  # Rango grande
                    min_spinbox.setDecimals(5)  # Hasta 5 decimales
                    min_spinbox.setValue(estrato[5])  # Asumiendo que el rango mínimo está en la posición 4
                    table.setCellWidget(row, 2, min_spinbox)

                    # Rango Máximo (DoubleSpinBox)
                    max_spinbox = QDoubleSpinBox()
                    max_spinbox.setRange(-1e9, 1e9)  # Rango grande
                    max_spinbox.setDecimals(5)  # Hasta 5 decimales
                    max_spinbox.setValue(estrato[6])  # Asumiendo que el rango máximo está en la posición 5
                    table.setCellWidget(row, 3, max_spinbox)
            else:
                reset_table()

        # Conectar el cambio de opción en el ComboBox para cargar los estratos
        component_combo.currentIndexChanged.connect(load_estratos)

        # Configurar las columnas iniciales
        load_estratos()

        # Añadir la tabla al layout
        main_layout.addWidget(table)

        # Layout para el botón Confirmar y el espacer
        confirm_layout = QHBoxLayout()

        # Espacer
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        confirm_layout.addSpacerItem(spacer)

        # Botón Confirmar
        confirm_button = QPushButton("Confirmar")
        confirm_layout.addWidget(confirm_button)

        # Añadir el layout horizontal al layout principal
        main_layout.addLayout(confirm_layout)

        # Establecer el layout principal en el diálogo
        dialog.setLayout(main_layout)

        # Función para agregar una nueva fila
        def add_row():
            row_count = table.rowCount()
            table.insertRow(row_count)

            # Nombre
            nombre_item = QTableWidgetItem("")
            table.setItem(row_count, 0, nombre_item)

            # Botón de color
            color_button = QPushButton()
            color_button.clicked.connect(lambda *args, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
            table.setCellWidget(row_count, 1, color_button)

            # Rango Mínimo (DoubleSpinBox)
            min_spinbox = QDoubleSpinBox()
            min_spinbox.setRange(-1e9, 1e9)  # Rango grande
            min_spinbox.setDecimals(5)  # Hasta 5 decimales
            table.setCellWidget(row_count, 2, min_spinbox)

            # Rango Máximo (DoubleSpinBox)
            max_spinbox = QDoubleSpinBox()
            max_spinbox.setRange(-1e9, 1e9)  # Rango grande
            max_spinbox.setDecimals(5)  # Hasta 5 decimales
            table.setCellWidget(row_count, 3, max_spinbox)

        # Conectar el botón a la función para agregar una nueva fila
        add_button.clicked.connect(add_row)

        # Función para manejar el evento de confirmar
        def confirm():
            selected_component_id = component_combo.currentData()  # Obtener el ID del componente seleccionado
            data = []

            for row in range(table.rowCount()):
                nombre_item = table.item(row, 0)
                min_spinbox = table.cellWidget(row, 2)
                max_spinbox = table.cellWidget(row, 3)

                if nombre_item and nombre_item.text() and min_spinbox and max_spinbox:
                    color_button = table.cellWidget(row, 1)
                    color = color_button.palette().button().color().name()
                    data.append({
                        "id": table.item(row, 0).data(Qt.UserRole) if table.item(row, 0) else None,  # Obtener el ID del estrato si existe
                        "nombre": nombre_item.text(),
                        "color": color,
                        "rango_minimo": min_spinbox.value(),
                        "rango_maximo": max_spinbox.value()
                    })

            # Guardar los datos en la base de datos
            success = EstratoController.ctrlGuardarEstratosInstrumentacion(proyectoid, selected_component_id, data)
            if success:
                load_estratos()
            else:
                mostrar_mensaje("Error", "Error al guardar estrato", 'error')

        # Conectar el botón Confirmar a la función confirm
        confirm_button.clicked.connect(confirm)

        # Función para mostrar el menú contextual
        def show_context_menu(position):
            menu = QMenu()

            delete_action = QAction("Eliminar", menu)
            delete_action.triggered.connect(lambda: delete_row(position))

            menu.addAction(delete_action)
            menu.exec(table.viewport().mapToGlobal(position))

        # Función para eliminar una fila
        def delete_row(position):
            item = table.itemAt(position)
            if item:
                row = item.row()
                nombre_item = table.item(row, 0)
                if nombre_item:
                    estrato_id = nombre_item.data(Qt.UserRole)
                    if estrato_id and estrato_id != 0:
                        # Llamar a la base de datos para eliminar el registro
                        success = EstratoController.ctrlEliminarEstratos(estrato_id)
                        if success:
                            print(f"Registro con ID {estrato_id} eliminado exitosamente.")
                        else:
                            mostrar_mensaje("Error", f"Error al eliminar el registro con ID {estrato_id}.", 'error')
                            return
                # Eliminar la fila de la tabla
                table.removeRow(row)
                # Recargar los datos de la tabla
                load_estratos()

        # Conectar el evento de clic derecho de la tabla a la función para mostrar el menú contextual
        table.setContextMenuPolicy(Qt.CustomContextMenu)
        table.customContextMenuRequested.connect(show_context_menu)

        # Calcular el ancho total de las columnas
        total_width = sum(table.columnWidth(col) for col in range(table.columnCount()))

        # Ajustar el tamaño del diálogo al contenido
        dialog.adjustSize()

        # Establecer el ancho inicial del diálogo basado en el ancho total de las columnas
        dialog.resize(total_width + 50, dialog.height())  # Añadir un margen adicional si es necesario

        # Mostrar el diálogo
        dialog.exec()
