from PySide6.QtGui import Qt, QAction
from PySide6.QtWidgets import (QDialog, QPushButton, QColorDialog, QVBoxLayout, QTableWidgetItem, QLabel,
                        QComboBox, QSpinBox, QCheckBox,QTableWidget, QHBoxLayout, QDoubleSpinBox, QSpacerItem, QSizePolicy, QMenu,QLineEdit,QHeaderView,QMessageBox,QWidget)
from PySide6.QtUiTools import QUiLoader
from utils.common.rutasarchivos import resource_path
from utils.common.alertas import mostrar_mensaje
from controllers.UmbralController import UmbralController
from controllers.InterfazController import InterfazController
from utils.common.metodosGenerales import MetodosGenerales

# Inicializar variables
coloresUmbral = [None, None, None, None]
valoresSD = [None, None, None, None]
valores3D = [None, None, None, None]

class UmbralView:
    
    # MOSTRAR DIALOGO RESUMEN TABLA MONITOR 1      
    def tabla_umbrales_inicial(proyecto, tabla,fechaMinInicial,fechaMaxInicial,minimoSD,maximoSD,minimo3D,maximo3D, prismastotales, prismasmarcados):
        try:
            # prismasmin, prismasmax = UmbralController.ctrListarPrismas(proyecto)
            fechas = UmbralController.crtObtenerFechasEnRango(proyecto,fechaMinInicial,fechaMaxInicial, prismastotales, prismasmarcados)
            # penultimovalor= UmbralController.crtObtenerPenultimoDato(proyecto)
            sd_inicial=UmbralController.crtObtenerSD(proyecto,fechaMinInicial,fechaMaxInicial, prismastotales, prismasmarcados)
            incial_3d=UmbralController.crtObtener3D(proyecto,fechaMinInicial,fechaMaxInicial, prismastotales, prismasmarcados)
            inicialL=UmbralController.crtObtenerL(proyecto,fechaMinInicial,fechaMaxInicial, prismastotales, prismasmarcados)
            inicialT=UmbralController.crtObtenerT(proyecto,fechaMinInicial,fechaMaxInicial, prismastotales, prismasmarcados)
            inicialH=UmbralController.crtObtenerH(proyecto,fechaMinInicial,fechaMaxInicial, prismastotales, prismasmarcados)
            inicialN=UmbralController.crtObtenerN(proyecto,fechaMinInicial,fechaMaxInicial, prismastotales, prismasmarcados)
            inicialE=UmbralController.crtObtenerE(proyecto,fechaMinInicial,fechaMaxInicial, prismastotales, prismasmarcados)
            inicialZ=UmbralController.crtObtenerZ(proyecto,fechaMinInicial,fechaMaxInicial, prismastotales, prismasmarcados)
            tabla.setRowCount(len(fechas))
            row = 0
            for col1,col2,col3,col4,col5,col6,col7,col8,col9 in zip(fechas,sd_inicial,inicialL,inicialT,inicialH,incial_3d,inicialN,inicialE,inicialZ):
                tabla.setItem(row, 0, QTableWidgetItem(col1[0]))
                tabla.setItem(row, 1, QTableWidgetItem(col1[1]))
                tabla.setItem(row, 2, QTableWidgetItem(col1[2]))
                tabla.setItem(row, 3, QTableWidgetItem(str(round(col2[2],4))))
                tabla.setItem(row, 4, QTableWidgetItem(str(col3[1])))
                tabla.setItem(row, 5, QTableWidgetItem(str(col4[1])))
                tabla.setItem(row, 6, QTableWidgetItem(str(col5[1])))
                tabla.setItem(row, 7, QTableWidgetItem(str(round(col6[2],4))))
                tabla.setItem(row, 8, QTableWidgetItem(str(round(col7[1],4))))
                tabla.setItem(row, 9, QTableWidgetItem(str(round(col8[1],4))))
                tabla.setItem(row, 10, QTableWidgetItem(str(round(col9[1],4))))
                row += 1
            tabla.resizeColumnsToContents()

            def mostrarResumenMaximosMinimos(columna, calculo):
                # Variables para almacenar los valores y las filas correspondientes
                valores_columna = []
                fila_maximo = None
                fila_minimo = None
                # Recorre las filas de la tabla y obtén los valores de la columna en la lista
                for row in range(tabla.rowCount()):
                    item = tabla.item(row, columna)
                    if item is not None:
                        valor = float(item.text())  # Convierte el valor a un tipo adecuado (en este caso, float)
                        valores_columna.append(valor)
                        if valor == max(valores_columna, key=abs):
                            fila_maximo = row
                        if valor == min(valores_columna, key=abs):
                            fila_minimo = row

                if valores_columna:
                    # Aplica valor absoluto solo durante la comparación
                    valor_maximo = max(valores_columna, key=abs)
                    valor_minimo = min(valores_columna, key=abs)
                    
                    if calculo == 'SD':
                        minimoSD.setText(f"{tabla.item(fila_minimo, 0).text()} -> {str(round(valor_minimo, 4))}")
                        maximoSD.setText(f"{tabla.item(fila_maximo, 0).text()} -> {str(round(valor_maximo, 4))}")
                    elif calculo == '3D':
                        minimo3D.setText(f"{tabla.item(fila_minimo, 0).text()} -> {str(round(valor_minimo, 4))}")
                        maximo3D.setText(f"{tabla.item(fila_maximo, 0).text()} -> {str(round(valor_maximo, 4))}")
            
            mostrarResumenMaximosMinimos(3,'SD')
            mostrarResumenMaximosMinimos(7,'3D')
        except Exception as e:
            print("Se ha producido un error:", e)
    
    def modalUmbralesPrismas(proyectoid, tipo, unidad1, unidad2, medida1, medida2):
        # Crear el diálogo
        dialog = QDialog()
        dialog.setWindowTitle("Umbrales Generales - Prismas")
        # Layout principal
        main_layout = QVBoxLayout()
        # Nuevo ComboBox al inicio
        component_combo_label = QLabel("Seleccione Componente:")
        component_combo = QComboBox()
        # Añadir opciones al nuevo ComboBox desde listacomponente
        listacomponente = InterfazController.ctrlListarComponentesProyecto(proyectoid)
        if listacomponente:
            component_combo.addItem("TODOS", userData=0)
            for componente in listacomponente:
                component_combo.addItem(componente[2], userData=componente[0])
            component_combo.setCurrentIndex(0)
        # Añadir el nuevo ComboBox al layout principal
        main_layout.addWidget(component_combo_label)
        main_layout.addWidget(component_combo)
        # Layout para el ComboBox y el botón
        combo_layout = QHBoxLayout()
        # ComboBox
        combo_label = QLabel("Seleccione Umbral:")
        combo_tipo = QComboBox()
        options = UmbralView.retornarArregloTipo(tipo)
        # Añadir opciones al ComboBox
        combo_tipo.addItems(options.keys())
        # Botón al lado del ComboBox
        add_button = QPushButton("Agregar Fila")
        # Añadir ComboBox y botón al layout horizontal
        combo_layout.addWidget(combo_label)
        combo_layout.addWidget(combo_tipo)
        combo_layout.addWidget(add_button)
        # Añadir el layout horizontal al layout principal
        main_layout.addLayout(combo_layout)
        # Tabla
        table = QTableWidget(3, 5)  # 3 filas y 5 columnas
        # Función para reiniciar la tabla
        def reset_table():
            selected_option = combo_tipo.currentText()
            selected_id = options[selected_option]
            if selected_id.startswith("V"):
                table.setHorizontalHeaderLabels(["Condición", "Color", "Riesgo", f"Rango ({medida2})", "Acciones a realizar"])
            else:
                table.setHorizontalHeaderLabels(["Condición", "Color", "Riesgo", f"Rango ({medida1})", "Acciones a realizar"])
            table.setRowCount(3)
            for row in range(3):
                # Condición
                condicion_item = QTableWidgetItem("")
                table.setItem(row, 0, condicion_item)
                # Botón de color
                color_button = QPushButton()
                color_button.clicked.connect(lambda *args, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
                table.setCellWidget(row, 1, color_button)
                # Riesgo
                riesgo_item = QTableWidgetItem("")
                table.setItem(row, 2, riesgo_item)
                # Rango (DoubleSpinBox)
                double_spinbox = QDoubleSpinBox()
                double_spinbox.setRange(-1e9, 1e9)  # Rango grande
                double_spinbox.setDecimals(5)  # Hasta 5 decimales
                table.setCellWidget(row, 3, double_spinbox)
                # Acciones a realizar
                acciones_item = QTableWidgetItem("")
                table.setItem(row, 4, acciones_item)
        def load_umbrales():
            selected_option = combo_tipo.currentText()
            selected_id = options[selected_option]  # Obtener el ID correspondiente
            selected_component_id = component_combo.currentData()  # Obtener el ID del componente seleccionado
            umbrales = UmbralController.ctrlObtenerUmbralesAjustes(proyectoid, selected_component_id, selected_id, tipo)
            if umbrales:
                if selected_id.startswith("V"):
                    table.setHorizontalHeaderLabels(["Condición", "Color", "Riesgo", f"Rango ({medida2})", "Acciones a realizar"])
                    unidad = unidad2
                else:
                    table.setHorizontalHeaderLabels(["Condición", "Color", "Riesgo", f"Rango ({medida1})", "Acciones a realizar"])
                    unidad = unidad1
                table.setRowCount(len(umbrales))
                for row, umbral in enumerate(umbrales):
                    # Condición
                    condicion_item = QTableWidgetItem(umbral[3])  # Asumiendo que la condición está en la posición 3
                    condicion_item.setData(Qt.UserRole, umbral[0])  # Guardar el ID del umbral en el item
                    table.setItem(row, 0, condicion_item)
                    # Botón de color
                    color_button = QPushButton()
                    color_button.setStyleSheet(f"background-color: {umbral[4]};")  # Asumiendo que el color está en la posición 4
                    color_button.clicked.connect(lambda *args, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
                    table.setCellWidget(row, 1, color_button)
                    # Riesgo
                    riesgo_item = QTableWidgetItem(umbral[5])  # Asumiendo que el riesgo está en la posición 5
                    table.setItem(row, 2, riesgo_item)
                    # Rango (DoubleSpinBox)
                    double_spinbox = QDoubleSpinBox()
                    double_spinbox.setRange(-1e9, 1e9)  # Rango grande
                    double_spinbox.setDecimals(5)  # Hasta 5 decimales
                    double_spinbox.setValue(umbral[6] * unidad) # Asumiendo que el rango está en la posición 6
                    table.setCellWidget(row, 3, double_spinbox)
                    # Acciones a realizar
                    acciones_item = QTableWidgetItem(umbral[8])  # Asumiendo que las acciones están en la posición 7
                    table.setItem(row, 4, acciones_item)
            else:
                reset_table()
        # Conectar el cambio de opción en el ComboBox para cargar los umbrales
        combo_tipo.currentIndexChanged.connect(load_umbrales)
        component_combo.currentIndexChanged.connect(load_umbrales)
        # Configurar las columnas iniciales
        load_umbrales()
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
            # Condición
            condicion_item = QTableWidgetItem("")
            table.setItem(row_count, 0, condicion_item)
            # Botón de color
            color_button = QPushButton()
            color_button.clicked.connect(lambda *args, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
            table.setCellWidget(row_count, 1, color_button)
            # Riesgo
            riesgo_item = QTableWidgetItem("")
            table.setItem(row_count, 2, riesgo_item)
            # Rango (DoubleSpinBox)
            double_spinbox = QDoubleSpinBox()
            double_spinbox.setRange(-1e9, 1e9)  # Rango grande
            double_spinbox.setDecimals(5)  # Hasta 5 decimales
            table.setCellWidget(row_count, 3, double_spinbox)
            # Acciones a realizar
            acciones_item = QTableWidgetItem("")
            table.setItem(row_count, 4, acciones_item)
        # Conectar el botón a la función para agregar una nueva fila
        add_button.clicked.connect(add_row)
        # Función para manejar el evento de confirmar
        def confirm():
            selected_option = combo_tipo.currentText()
            selected_id = options[selected_option]  # Obtener el ID correspondiente
            if selected_id.startswith("V"):
                unidad = unidad2
            else:
                unidad = unidad1
            selected_component_id = component_combo.currentData()  # Obtener el ID del componente seleccionado
            data = []
            for row in range(table.rowCount()):
                condicion_item = table.item(row, 0)
                rango_item = table.cellWidget(row, 3)
                riesgo_item = table.item(row, 2)
                acciones_item = table.item(row, 4)
                if condicion_item and condicion_item.text() and rango_item and rango_item.value():
                    color_button = table.cellWidget(row, 1)
                    color = color_button.palette().button().color().name()
                    valorrango = float(rango_item.value()) / unidad
                    data.append({
                        "id": table.item(row, 0).data(Qt.UserRole) if table.item(row, 0) else None,  # Obtener el ID del umbral si existe
                        "condicion": condicion_item.text(),
                        "color": color,
                        "riesgo": riesgo_item.text(),
                        "rango": valorrango,
                        "acciones": acciones_item.text()
                    })
            # Guardar los datos en la base de datos
            success = UmbralController.ctrlGuardarUmbralesEquipos(proyectoid, selected_component_id, selected_id, data, tipo)
            if success:
                load_umbrales()
                mostrar_mensaje("Guardado", "Se guardó el umbral.", 'informacion')
            else:
                mostrar_mensaje("Error", "Error al guardar umbral", 'error')
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
                condicion_item = table.item(row, 0)
                if condicion_item:
                    umbral_id = condicion_item.data(Qt.UserRole)
                    if umbral_id and umbral_id != 0:
                        # Llamar a la base de datos para eliminar el registro
                        success = UmbralController.ctrlEliminarUmbralEquipos(umbral_id)
                        if success:
                            print(f"Registro con ID {umbral_id} eliminado exitosamente.")
                        else:
                            mostrar_mensaje("Error", f"Error al eliminar el registro con ID {umbral_id}.", 'error')
                            return
                # Eliminar la fila de la tabla
                table.removeRow(row)
                # Recargar los datos de la tabla
                load_umbrales()
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

    def modalUmbralesInclinometros(proyectoid, tipo, unidad):
        # Añadir opciones al nuevo ComboBox desde listacomponente
        listacomponente = InterfazController.ctrlListarComponentesProyecto(proyectoid)
        titulo_combo = "Seleccione Componente:"
        # Crear el diálogo
        dialog = QDialog()
        dialog.setWindowTitle("Umbrales Generales - Inclinómetros")
        # Layout principal
        main_layout = QVBoxLayout()
        # Nuevo ComboBox al inicio
        component_combo_label = QLabel(titulo_combo)
        component_combo = QComboBox()
        if listacomponente:
            component_combo.addItem("TODOS", userData=0)
            for componente in listacomponente:
                component_combo.addItem(componente[2], userData=componente[0])
            component_combo.setCurrentIndex(0)
        # Añadir el nuevo ComboBox al layout principal
        main_layout.addWidget(component_combo_label)
        main_layout.addWidget(component_combo)
        # Layout para el ComboBox y el botón
        combo_layout = QHBoxLayout()
        # ComboBox
        combo_label = QLabel("Seleccione Umbral:")
        combo = QComboBox()
        options = UmbralView.retornarArregloTipo(tipo)
        # Añadir opciones al ComboBox
        combo.addItems(options.keys())
        # Botón al lado del ComboBox
        add_button = QPushButton("Agregar Fila")
        # Añadir ComboBox y botón al layout horizontal
        combo_layout.addWidget(combo_label)
        combo_layout.addWidget(combo)
        combo_layout.addWidget(add_button)
        # Añadir el layout horizontal al layout principal
        main_layout.addLayout(combo_layout)
        # Tabla
        table = QTableWidget(3, 5)  # 3 filas y 5 columnas
        # table.setHorizontalHeaderLabels(["Condición", "Color", "Riesgo", f"Rango ({medida})", "Acciones a realizar"])
        # Función para reiniciar la tabla
        def reset_table():
            if unidad == 1:
                medida = "m"
            elif unidad == 100:
                medida = "cm"
            else:
                medida = "mm"
            table.setHorizontalHeaderLabels(["Condición", "Color", "Riesgo", f"Rango ({medida})", "Acciones a realizar"])
            table.setRowCount(3)
            for row in range(3):
                # Condición
                condicion_item = QTableWidgetItem("")
                table.setItem(row, 0, condicion_item)
                # Botón de color
                color_button = QPushButton()
                color_button.clicked.connect(lambda *args, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
                table.setCellWidget(row, 1, color_button)
                # Riesgo
                riesgo_item = QTableWidgetItem("")
                table.setItem(row, 2, riesgo_item)
                # Rango (DoubleSpinBox)
                double_spinbox = QDoubleSpinBox()
                double_spinbox.setRange(-1e9, 1e9)  # Rango grande
                double_spinbox.setDecimals(5)  # Hasta 5 decimales
                table.setCellWidget(row, 3, double_spinbox)
                # Acciones a realizar
                acciones_item = QTableWidgetItem("")
                table.setItem(row, 4, acciones_item)
        def load_umbrales():
            selected_option = combo.currentText()
            selected_id = options[selected_option]  # Obtener el ID correspondiente del tipo
            selected_equipo_id = component_combo.currentData()  # Obtener el ID del componente seleccionado
            if unidad == 1:
                medida = "m"
            elif unidad == 100:
                medida = "cm"
            else:
                medida = "mm"
            umbrales = UmbralController.ctrlObtenerUmbralesAjustes(proyectoid, selected_equipo_id, selected_id, tipo)
            if umbrales:
                table.setHorizontalHeaderLabels(["Condición", "Color", "Riesgo", f"Rango ({medida})", "Acciones a realizar"])
                table.setRowCount(len(umbrales))
                for row, umbral in enumerate(umbrales):
                    # Condición
                    condicion_item = QTableWidgetItem(umbral[3])  # Asumiendo que la condición está en la posición 3
                    condicion_item.setData(Qt.UserRole, umbral[0])  # Guardar el ID del umbral en el item
                    table.setItem(row, 0, condicion_item)
                    # Botón de color
                    color_button = QPushButton()
                    color_button.setStyleSheet(f"background-color: {umbral[4]};")  # Asumiendo que el color está en la posición 4
                    color_button.clicked.connect(lambda *args, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
                    table.setCellWidget(row, 1, color_button)
                    # Riesgo
                    riesgo_item = QTableWidgetItem(umbral[5])  # Asumiendo que el riesgo está en la posición 5
                    table.setItem(row, 2, riesgo_item)
                    # Rango (DoubleSpinBox)
                    double_spinbox = QDoubleSpinBox()
                    double_spinbox.setRange(-1e9, 1e9)  # Rango grande
                    double_spinbox.setDecimals(5)  # Hasta 5 decimales
                    double_spinbox.setValue(umbral[6] * unidad) # Asumiendo que el rango está en la posición 5
                    table.setCellWidget(row, 3, double_spinbox)
                    # Acciones a realizar
                    acciones_item = QTableWidgetItem(umbral[8])  # Asumiendo que las acciones están en la posición 6
                    table.setItem(row, 4, acciones_item)
            else:
                reset_table()
        # Conectar el cambio de opción en el ComboBox para cargar los umbrales
        combo.currentIndexChanged.connect(load_umbrales)
        component_combo.currentIndexChanged.connect(load_umbrales)
        # Configurar las columnas iniciales
        load_umbrales()
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
            # Condición
            condicion_item = QTableWidgetItem("")
            table.setItem(row_count, 0, condicion_item)
            # Botón de color
            color_button = QPushButton()
            color_button.clicked.connect(lambda *args, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
            table.setCellWidget(row_count, 1, color_button)
            # Riesgo
            riesgo_item = QTableWidgetItem("")
            table.setItem(row_count, 2, riesgo_item)
            # Rango (DoubleSpinBox)
            double_spinbox = QDoubleSpinBox()
            double_spinbox.setRange(-1e9, 1e9)  # Rango grande
            double_spinbox.setDecimals(5)  # Hasta 5 decimales
            table.setCellWidget(row_count, 3, double_spinbox)
            # Acciones a realizar
            acciones_item = QTableWidgetItem("")
            table.setItem(row_count, 4, acciones_item)
        # Conectar el botón a la función para agregar una nueva fila
        add_button.clicked.connect(add_row)
        # Función para manejar el evento de confirmar
        def confirm():
            selected_option = combo.currentText()
            selected_id = options[selected_option]  # Obtener el ID correspondiente
            selected_equipos_id = component_combo.currentData()  # Obtener el ID del componente seleccionado
            data = []
            for row in range(table.rowCount()):
                condicion_item = table.item(row, 0)
                rango_item = table.cellWidget(row, 3)
                riesgo_item = table.item(row, 2)
                acciones_item = table.item(row, 4)
                if condicion_item and condicion_item.text() and rango_item and rango_item.value():
                    color_button = table.cellWidget(row, 1)
                    color = color_button.palette().button().color().name()
                    valorrango = float(rango_item.value()) / unidad
                    data.append({
                        "id": table.item(row, 0).data(Qt.UserRole) if table.item(row, 0) else None,  # Obtener el ID del umbral si existe
                        "condicion": condicion_item.text(),
                        "color": color,
                        "riesgo": riesgo_item.text(),
                        "rango": valorrango,
                        "acciones": acciones_item.text()
                    })
            # Guardar los datos en la base de datos
            success = UmbralController.ctrlGuardarUmbralesEquipos(proyectoid, selected_equipos_id, selected_id, data, tipo)
            if success:
                load_umbrales()
                mostrar_mensaje("Guardado", "Se guardó el umbral.", 'informacion')
            else:
                mostrar_mensaje("Error", "Error al guardar umbral", 'error')
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
                condicion_item = table.item(row, 0)
                if condicion_item:
                    umbral_id = condicion_item.data(Qt.UserRole)
                    if umbral_id and umbral_id != 0:
                        # Llamar a la base de datos para eliminar el registro
                        success = UmbralController.ctrlEliminarUmbralEquipos(umbral_id)
                        if success:
                            print(f"Registro con ID {umbral_id} eliminado exitosamente.")
                        else:
                            mostrar_mensaje("Error", f"Error al eliminar el registro con ID {umbral_id}.", 'error')
                            return
                # Eliminar la fila de la tabla
                table.removeRow(row)
                # Recargar los datos de la tabla
                load_umbrales()
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
    
    def modalUmbralesPiezometros(proyectoid, tipo, unidadmedida):
        unidad = unidadmedida
        tipotitulo = "Cuerda Vibrante" if tipo == "PIEZOMETROCUERDA" else "Casagrande"
        # Añadir opciones al nuevo ComboBox desde listacomponente
        listacomponente = InterfazController.ctrlListarComponentesProyecto(proyectoid)
        titulo_combo = "Seleccione Componente:"
        # Crear el diálogo
        dialog = QDialog()
        dialog.setWindowTitle(f"Umbrales Generales - Piezómetros {tipotitulo}")
        # Layout principal
        main_layout = QVBoxLayout()
        # Nuevo ComboBox al inicio
        component_combo_label = QLabel(titulo_combo)
        component_combo = QComboBox()
        if listacomponente:
            component_combo.addItem("TODOS", userData=0)
            for componente in listacomponente:
                component_combo.addItem(componente[2], userData=componente[0])
            component_combo.setCurrentIndex(0)
        # Añadir el nuevo ComboBox al layout principal
        main_layout.addWidget(component_combo_label)
        main_layout.addWidget(component_combo)
        # Layout para el ComboBox y el botón
        combo_layout = QHBoxLayout()
        # ComboBox
        combo_label = QLabel("Seleccione Umbral:")
        combo = QComboBox()
        options = UmbralView.retornarArregloTipo(tipo)
        # Añadir opciones al ComboBox
        combo.addItems(options.keys())
        # Botón al lado del ComboBox
        add_button = QPushButton("Agregar Fila")
        # Añadir ComboBox y botón al layout horizontal
        combo_layout.addWidget(combo_label)
        combo_layout.addWidget(combo)
        combo_layout.addWidget(add_button)
        # Añadir el layout horizontal al layout principal
        main_layout.addLayout(combo_layout)
        # Tabla
        table = QTableWidget(3, 5)  # 3 filas y 5 columnas
        # Función para reiniciar la tabla
        def reset_table():
            nonlocal unidad
            selected_option = combo.currentText()
            vista = options[selected_option]  # Obtener el ID correspondiente del tipo
            if vista == "NF":
                medida = "msnm"
            elif vista == "NI" or vista == "NA":
                if unidad == 1:
                    medida = "m"
                elif unidad == 100:
                    medida = "cm"
                else:
                    medida = "mm"
            elif vista == "PB":
                medida = "B"
            elif vista == "FP":
                medida = "Hz"
            else:
                medida = "°C"
            table.setHorizontalHeaderLabels(["Condición", "Color", "Riesgo", f"Rango ({medida})", "Acciones a realizar"])
            table.setRowCount(3)
            for row in range(3):
                # Condición
                condicion_item = QTableWidgetItem("")
                table.setItem(row, 0, condicion_item)
                # Botón de color
                color_button = QPushButton()
                color_button.clicked.connect(lambda *args, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
                table.setCellWidget(row, 1, color_button)
                # Riesgo
                riesgo_item = QTableWidgetItem("")
                table.setItem(row, 2, riesgo_item)
                # Rango (DoubleSpinBox)
                double_spinbox = QDoubleSpinBox()
                double_spinbox.setRange(-1e9, 1e9)  # Rango grande
                double_spinbox.setDecimals(5)  # Hasta 5 decimales
                table.setCellWidget(row, 3, double_spinbox)
                # Acciones a realizar
                acciones_item = QTableWidgetItem("")
                table.setItem(row, 4, acciones_item)
        def load_umbrales():
            nonlocal unidad
            selected_option = combo.currentText()
            selected_id = options[selected_option]  # Obtener el ID correspondiente del tipo
            selected_component_id = component_combo.currentData()  # Obtener el ID del piezómetro seleccionado
            if selected_component_id:
                if selected_id == "NF":
                    unimedida = 1
                    medida = "msnm"
                elif selected_id == "NI" or selected_id == "NA":
                    if unidad == 1:
                        unimedida = 1
                        medida = "m"
                    elif unidad == 100:
                        unimedida = 100
                        medida = "cm"
                    else:
                        unimedida = 1000
                        medida = "mm"
                elif selected_id == "PB":
                    unimedida = 1
                    medida = "B"
                elif selected_id == "FP":
                    unimedida = 1
                    medida = "Hz"
                else:
                    unimedida = 1
                    medida = "°C"
                umbrales = UmbralController.ctrlObtenerUmbralesAjustes(proyectoid, selected_component_id, selected_id, tipo)
                if umbrales:
                    table.setHorizontalHeaderLabels(["Condición", "Color", "Riesgo", f"Rango ({medida})", "Acciones a realizar"])
                    table.setRowCount(len(umbrales))
                    for row, umbral in enumerate(umbrales):
                        # Condición
                        condicion_item = QTableWidgetItem(umbral[3])  # Asumiendo que la condición está en la posición 2
                        condicion_item.setData(Qt.UserRole, umbral[0])  # Guardar el ID del umbral en el item
                        table.setItem(row, 0, condicion_item)
                        # Botón de color
                        color_button = QPushButton()
                        color_button.setStyleSheet(f"background-color: {umbral[4]};")  # Asumiendo que el color está en la posición 3
                        color_button.clicked.connect(lambda *args, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
                        table.setCellWidget(row, 1, color_button)
                        # Riesgo
                        riesgo_item = QTableWidgetItem(umbral[5])  # Asumiendo que el riesgo está en la posición 4
                        table.setItem(row, 2, riesgo_item)
                        # Rango (DoubleSpinBox)
                        double_spinbox = QDoubleSpinBox()
                        double_spinbox.setRange(-1e9, 1e9)  # Rango grande
                        double_spinbox.setDecimals(5)  # Hasta 5 decimales
                        double_spinbox.setValue(umbral[6] * unimedida) # Asumiendo que el rango está en la posición 5
                        table.setCellWidget(row, 3, double_spinbox)
                        # Acciones a realizar
                        acciones_item = QTableWidgetItem(umbral[8])  # Asumiendo que las acciones están en la posición 6
                        table.setItem(row, 4, acciones_item)
                else:
                    reset_table()
            else:
                reset_table()
        # Conectar el cambio de opción en el ComboBox para cargar los umbrales
        combo.currentIndexChanged.connect(load_umbrales)
        component_combo.currentIndexChanged.connect(load_umbrales)
        # Configurar las columnas iniciales
        load_umbrales()
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
            # Condición
            condicion_item = QTableWidgetItem("")
            table.setItem(row_count, 0, condicion_item)
            # Botón de color
            color_button = QPushButton()
            color_button.clicked.connect(lambda *args, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
            table.setCellWidget(row_count, 1, color_button)
            # Riesgo
            riesgo_item = QTableWidgetItem("")
            table.setItem(row_count, 2, riesgo_item)
            # Rango (DoubleSpinBox)
            double_spinbox = QDoubleSpinBox()
            double_spinbox.setRange(-1e9, 1e9)  # Rango grande
            double_spinbox.setDecimals(5)  # Hasta 5 decimales
            table.setCellWidget(row_count, 3, double_spinbox)
            # Acciones a realizar
            acciones_item = QTableWidgetItem("")
            table.setItem(row_count, 4, acciones_item)
        # Conectar el botón a la función para agregar una nueva fila
        add_button.clicked.connect(add_row)
        # Función para manejar el evento de confirmar
        def confirm():
            nonlocal unidad
            selected_option = combo.currentText()
            selected_id = options[selected_option]  # Obtener el ID correspondiente
            selected_component_id = component_combo.currentData()  # Obtener el ID del piezómetro seleccionado
            if selected_id == "NF":
                unimedida = 1
            elif selected_id == "NI" or selected_id == "NA":
                if unidad == 1:
                    unimedida = 1
                elif unidad == 100:
                    unimedida = 100
                else:
                    unimedida = 1000
            elif selected_id == "PB":
                unimedida = 1
            elif selected_id == "FP":
                unimedida = 1
            else:
                unimedida = 1
            data = []
            for row in range(table.rowCount()):
                condicion_item = table.item(row, 0)
                rango_item = table.cellWidget(row, 3)
                riesgo_item = table.item(row, 2)
                acciones_item = table.item(row, 4)
                if condicion_item and condicion_item.text() and rango_item and rango_item.value():
                    color_button = table.cellWidget(row, 1)
                    color = color_button.palette().button().color().name()
                    valorrango = float(rango_item.value()) / unimedida
                    data.append({
                        "id": table.item(row, 0).data(Qt.UserRole) if table.item(row, 0) else None,  # Obtener el ID del umbral si existe
                        "condicion": condicion_item.text(),
                        "color": color,
                        "riesgo": riesgo_item.text(),
                        "rango": valorrango,
                        "acciones": acciones_item.text()
                    })
            # Guardar los datos en la base de datos
            success = UmbralController.ctrlGuardarUmbralesEquipos(proyectoid, selected_component_id, selected_id, data, tipo)
            if success:
                load_umbrales()
                mostrar_mensaje("Guardado", "Se guardó el umbral.", 'informacion')
            else:
                mostrar_mensaje("Error", "Error al guardar umbral", 'error')
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
                condicion_item = table.item(row, 0)
                if condicion_item:
                    umbral_id = condicion_item.data(Qt.UserRole)
                    if umbral_id and umbral_id != 0:
                        # Llamar a la base de datos para eliminar el registro
                        success = UmbralController.ctrlEliminarUmbralEquipos(umbral_id)
                        if success:
                            print(f"Registro con ID {umbral_id} eliminado exitosamente.")
                        else:
                            mostrar_mensaje("Error", f"Error al eliminar el registro con ID {umbral_id}.", 'error')
                            return
                # Eliminar la fila de la tabla
                table.removeRow(row)
                # Recargar los datos de la tabla
                load_umbrales()
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
    
    def modalUmbralesCeldas(proyectoid, tipo, unidadmedida, tipovelocidad):
        unidad = unidadmedida
        # Añadir opciones al nuevo ComboBox desde listacomponente
        listacomponente = InterfazController.ctrlListarComponentesProyecto(proyectoid)
        titulo_combo = "Seleccione Componente:"
        # Crear el diálogo
        dialog = QDialog()
        dialog.setWindowTitle("Umbrales Generales - Celdas")
        # Layout principal
        main_layout = QVBoxLayout()
        # Nuevo ComboBox al inicio
        component_combo_label = QLabel(titulo_combo)
        component_combo = QComboBox()
        if listacomponente:
            component_combo.addItem("TODOS", userData=0)
            for componente in listacomponente:
                component_combo.addItem(componente[2], userData=componente[0])
            component_combo.setCurrentIndex(0)
        # Añadir el nuevo ComboBox al layout principal
        main_layout.addWidget(component_combo_label)
        main_layout.addWidget(component_combo)
        # Layout para el ComboBox y el botón
        combo_layout = QHBoxLayout()
        # ComboBox
        combo_label = QLabel("Seleccione Umbral:")
        combo = QComboBox()
        options = UmbralView.retornarArregloTipo(tipo)
        # Añadir opciones al ComboBox
        combo.addItems(options.keys())
        # Botón al lado del ComboBox
        add_button = QPushButton("Agregar Fila")
        # Añadir ComboBox y botón al layout horizontal
        combo_layout.addWidget(combo_label)
        combo_layout.addWidget(combo)
        combo_layout.addWidget(add_button)
        # Añadir el layout horizontal al layout principal
        main_layout.addLayout(combo_layout)
        # Tabla
        table = QTableWidget(3, 5)  # 3 filas y 5 columnas
        # table.setHorizontalHeaderLabels(["Condición", "Color", "Riesgo", f"Rango ({medida})", "Acciones a realizar"])
        # Función para reiniciar la tabla
        def reset_table():
            nonlocal unidad
            selected_option = combo.currentText()
            vista = options[selected_option]  # Obtener el ID correspondiente del tipo
            if vista == "VI":
                if tipovelocidad == "Por Mes":
                    if unidad == 1:
                        medida = "m/mes"
                    elif unidad == 100:
                        medida = "cm/mes"
                    else:
                        medida = "mm/mes"
                else:
                    if unidad == 1:
                        medida = "m/d"
                    elif unidad == 100:
                        medida = "cm/d"
                    else:
                        medida = "mm/d"
            elif vista == "AC":
                medida = "msnm"
            elif vista == "AI" or vista == "AA":
                if unidad == 1:
                    medida = "m"
                elif unidad == 100:
                    medida = "cm"
                else:
                    medida = "mm"
            elif vista == "AF":
                medida = "Hz"
            else: # AT
                medida = "°C"
            table.setHorizontalHeaderLabels(["Condición", "Color", "Riesgo", f"Rango ({medida})", "Acciones a realizar"])
            table.setRowCount(3)
            for row in range(3):
                # Condición
                condicion_item = QTableWidgetItem("")
                table.setItem(row, 0, condicion_item)
                # Botón de color
                color_button = QPushButton()
                color_button.clicked.connect(lambda *args, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
                table.setCellWidget(row, 1, color_button)
                # Riesgo
                riesgo_item = QTableWidgetItem("")
                table.setItem(row, 2, riesgo_item)
                # Rango (DoubleSpinBox)
                double_spinbox = QDoubleSpinBox()
                double_spinbox.setRange(-1e9, 1e9)  # Rango grande
                double_spinbox.setDecimals(5)  # Hasta 5 decimales
                table.setCellWidget(row, 3, double_spinbox)
                # Acciones a realizar
                acciones_item = QTableWidgetItem("")
                table.setItem(row, 4, acciones_item)
        def load_umbrales():
            nonlocal unidad
            selected_option = combo.currentText()
            selected_id = options[selected_option]  # Obtener el ID correspondiente del tipo
            selected_equipo_id = component_combo.currentData()  # Obtener el ID de la celda
            if selected_id == "VI":
                if tipovelocidad == "Por Mes":
                    if unidad == 1:
                        medida = "m/mes"
                        unimedida = 1
                    elif unidad == 100:
                        medida = "cm/mes"
                        unimedida = 100
                    else:
                        medida = "mm/mes"
                        unimedida = 1000
                else:
                    if unidad == 1:
                        medida = "m/d"
                        unimedida = 1
                    elif unidad == 100:
                        medida = "cm/d"
                        unimedida = 100
                    else:
                        medida = "mm/d"
                        unimedida = 1000
            elif selected_id == "AC":
                medida = "msnm"
                unimedida = 1
            elif selected_id == "AI" or selected_id == "AA":
                if unidad == 1:
                    medida = "m"
                    unimedida = 1
                elif unidad == 100:
                    medida = "cm"
                    unimedida = 100
                else:
                    medida = "mm"
                    unimedida = 1000
            elif selected_id == "AF":
                medida = "Hz"
                unimedida = 1
            else: # AT
                medida = "°C"
                unimedida = 1
            umbrales = UmbralController.ctrlObtenerUmbralesAjustes(proyectoid, selected_equipo_id, selected_id, tipo)
            if umbrales:
                table.setHorizontalHeaderLabels(["Condición", "Color", "Riesgo", f"Rango ({medida})", "Acciones a realizar"])
                table.setRowCount(len(umbrales))
                for row, umbral in enumerate(umbrales):
                    # Condición
                    condicion_item = QTableWidgetItem(umbral[3])  # Asumiendo que la condición está en la posición 3
                    condicion_item.setData(Qt.UserRole, umbral[0])  # Guardar el ID del umbral en el item
                    table.setItem(row, 0, condicion_item)
                    # Botón de color
                    color_button = QPushButton()
                    color_button.setStyleSheet(f"background-color: {umbral[4]};")  # Asumiendo que el color está en la posición 4
                    color_button.clicked.connect(lambda *args, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
                    table.setCellWidget(row, 1, color_button)
                    # Riesgo
                    riesgo_item = QTableWidgetItem(umbral[5])  # Asumiendo que el riesgo está en la posición 5
                    table.setItem(row, 2, riesgo_item)
                    # Rango (DoubleSpinBox)
                    double_spinbox = QDoubleSpinBox()
                    double_spinbox.setRange(-1e9, 1e9)  # Rango grande
                    double_spinbox.setDecimals(5)  # Hasta 5 decimales
                    double_spinbox.setValue(umbral[6] * unimedida) # Asumiendo que el rango está en la posición 6
                    table.setCellWidget(row, 3, double_spinbox)
                    # Acciones a realizar
                    acciones_item = QTableWidgetItem(umbral[8])  # Asumiendo que las acciones están en la posición 8
                    table.setItem(row, 4, acciones_item)
            else:
                reset_table()
        # Conectar el cambio de opción en el ComboBox para cargar los umbrales
        combo.currentIndexChanged.connect(load_umbrales)
        component_combo.currentIndexChanged.connect(load_umbrales)
        # Configurar las columnas iniciales
        load_umbrales()
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
            # Condición
            condicion_item = QTableWidgetItem("")
            table.setItem(row_count, 0, condicion_item)
            # Botón de color
            color_button = QPushButton()
            color_button.clicked.connect(lambda *args, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
            table.setCellWidget(row_count, 1, color_button)
            # Riesgo
            riesgo_item = QTableWidgetItem("")
            table.setItem(row_count, 2, riesgo_item)
            # Rango (DoubleSpinBox)
            double_spinbox = QDoubleSpinBox()
            double_spinbox.setRange(-1e9, 1e9)  # Rango grande
            double_spinbox.setDecimals(5)  # Hasta 5 decimales
            table.setCellWidget(row_count, 3, double_spinbox)
            # Acciones a realizar
            acciones_item = QTableWidgetItem("")
            table.setItem(row_count, 4, acciones_item)
        # Conectar el botón a la función para agregar una nueva fila
        add_button.clicked.connect(add_row)
        # Función para manejar el evento de confirmar
        def confirm():
            nonlocal unidad
            selected_option = combo.currentText()
            selected_id = options[selected_option]  # Obtener el ID correspondiente
            selected_component_id = component_combo.currentData()
            if selected_id == "VI":
                if tipovelocidad == "Por Mes":
                    if unidad == 1:
                        unimedida = 1
                    elif unidad == 100:
                        unimedida = 100
                    else:
                        unimedida = 1000
                else:
                    if unidad == 1:
                        unimedida = 1
                    elif unidad == 100:
                        unimedida = 100
                    else:
                        unimedida = 1000
            elif selected_id == "AC":
                unimedida = 1
            elif selected_id == "AI" or selected_id == "AA":
                if unidad == 1:
                    unimedida = 1
                elif unidad == 100:
                    unimedida = 100
                else:
                    unimedida = 1000
            elif selected_id == "AF":
                unimedida = 1
            else: # AT
                unimedida = 1
            data = []
            for row in range(table.rowCount()):
                condicion_item = table.item(row, 0)
                rango_item = table.cellWidget(row, 3)
                riesgo_item = table.item(row, 2)
                acciones_item = table.item(row, 4)
                if condicion_item and condicion_item.text() and rango_item and rango_item.value():
                    color_button = table.cellWidget(row, 1)
                    color = color_button.palette().button().color().name()
                    valorrango = float(rango_item.value()) / unimedida
                    data.append({
                        "id": table.item(row, 0).data(Qt.UserRole) if table.item(row, 0) else None,  # Obtener el ID del umbral si existe
                        "condicion": condicion_item.text(),
                        "color": color,
                        "riesgo": riesgo_item.text(),
                        "rango": valorrango,
                        "acciones": acciones_item.text()
                    })
            # Guardar los datos en la base de datos
            success = UmbralController.ctrlGuardarUmbralesEquipos(proyectoid, selected_component_id, selected_id, data, tipo)
            if success:
                load_umbrales()
                mostrar_mensaje("Guardado", "Se guardó el umbral.", 'informacion')
            else:
                mostrar_mensaje("Error", "Error al guardar umbral", 'error')
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
                condicion_item = table.item(row, 0)
                if condicion_item:
                    umbral_id = condicion_item.data(Qt.UserRole)
                    if umbral_id and umbral_id != 0:
                        # Llamar a la base de datos para eliminar el registro
                        success = UmbralController.ctrlEliminarUmbralEquipos(umbral_id)
                        if success:
                            print(f"Registro con ID {umbral_id} eliminado exitosamente.")
                        else:
                            mostrar_mensaje("Error", f"Error al eliminar el registro con ID {umbral_id}.", 'error')
                            return
                # Eliminar la fila de la tabla
                table.removeRow(row)
                # Recargar los datos de la tabla
                load_umbrales()
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
    

    def modalUmbralesAcelerografos(proyectoid, tipo):
        table = None
        # Crear el diálogo
        dialog = QDialog()
        dialog.setWindowTitle("Umbrales Generales - Acelerógrafos")
        # Layout principal
        main_layout = QVBoxLayout()
        # Nuevo ComboBox al inicio
        component_combo_label = QLabel("Seleccione Componente:")
        component_combo = QComboBox()
        # Añadir opciones al nuevo ComboBox desde listacomponente
        listacomponente = InterfazController.ctrlListarComponentesProyecto(proyectoid)
        if listacomponente:
            component_combo.addItem("TODOS", userData=0)
            for componente in listacomponente:
                component_combo.addItem(componente[2], userData=componente[0])
            component_combo.setCurrentIndex(0)
        # Añadir el nuevo ComboBox al layout principal
        main_layout.addWidget(component_combo_label)
        main_layout.addWidget(component_combo)
        # Layout para el ComboBox y el botón
        combo_layout = QHBoxLayout()
        # ComboBox
        combo_label = QLabel("Seleccione Umbral:")
        combo = QComboBox()
        options = UmbralView.retornarArregloTipo(tipo)
        # Añadir opciones al ComboBox
        combo.addItems(options.keys())
        # Botón al lado del ComboBox
        add_button = QPushButton("Agregar Fila")
        # Añadir ComboBox y botón al layout horizontal
        combo_layout.addWidget(combo_label)
        combo_layout.addWidget(combo)
        combo_layout.addWidget(add_button)
        # Añadir el layout horizontal al layout principal
        main_layout.addLayout(combo_layout)
        # Crear Tabla según tipo
        # Función para mostrar el menú contextual
        def show_context_menu(position):
            nonlocal table
            menu = QMenu()
            delete_action = QAction("Eliminar", menu)
            delete_action.triggered.connect(lambda: delete_row(position))
            menu.addAction(delete_action)
            menu.exec(table.viewport().mapToGlobal(position))
        def crear_tabla():
            nonlocal table  # acceder a la variable table definida afuera
            selected_option = combo.currentText()
            tipografica = options[selected_option]
            # Si ya hay una tabla previa, eliminarla del layout
            if table is not None:
                main_layout.removeWidget(table)
                table.deleteLater()
                table = None
            if tipografica == "AMA":
                table = QTableWidget(3, 6)
                table.setHorizontalHeaderLabels(["Nombre", "Color", "Riesgo", "Distancia (km)", "Magnitud (M)", "Acciones a Realizar"])
            else:
                table = QTableWidget(3, 5)
                if tipografica == "AAC":
                    medida = "m/s²"
                elif tipografica == "AVE":
                    medida = "m/s"
                elif tipografica == "ADE":
                    medida = "m"
                table.setHorizontalHeaderLabels(["Condición", "Color", "Riesgo", f"Rango ({medida})", "Acciones a realizar"])
            table.setContextMenuPolicy(Qt.CustomContextMenu)
            table.customContextMenuRequested.connect(show_context_menu)
            main_layout.insertWidget(3, table)
            return table
        # Función para reiniciar la tabla
        def reset_table():
            nonlocal table
            table = crear_tabla()
            table.setRowCount(3)
            selected_option = combo.currentText()
            tipografica = options[selected_option]
            if tipografica == "AMA":
                for row in range(3):
                    # Condición
                    condicion_item = QTableWidgetItem("")
                    table.setItem(row, 0, condicion_item)
                    # Botón de color
                    color_button = QPushButton()
                    color_button.clicked.connect(lambda *args, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
                    table.setCellWidget(row, 1, color_button)
                    # Riesgo
                    riesgo_item = QTableWidgetItem("")
                    table.setItem(row, 2, riesgo_item)
                    # Distancia (DoubleSpinBox)
                    double_spinbox = QDoubleSpinBox()
                    double_spinbox.setRange(-1e9, 1e9)  # Rango grande
                    double_spinbox.setDecimals(5)  # Hasta 5 decimales
                    table.setCellWidget(row, 3, double_spinbox)
                    # Magnitud (DoubleSpinBox)
                    double_spinbox = QDoubleSpinBox()
                    double_spinbox.setRange(-1e9, 1e9)  # Rango grande
                    double_spinbox.setDecimals(5)  # Hasta 5 decimales
                    table.setCellWidget(row, 4, double_spinbox)
                    # Acciones a realizar
                    acciones_item = QTableWidgetItem("")
                    table.setItem(row, 5, acciones_item)
            else:
                for row in range(3):
                    # Nombre
                    nombre_item = QTableWidgetItem("")
                    table.setItem(row, 0, nombre_item)
                    # Botón de color
                    color_button = QPushButton()
                    color_button.clicked.connect(lambda *args, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
                    table.setCellWidget(row, 1, color_button)
                    # Riesgo
                    riesgo_item = QTableWidgetItem("")
                    table.setItem(row, 2, riesgo_item)
                    # Rango (DoubleSpinBox)
                    distancia_spinbox = QDoubleSpinBox()
                    distancia_spinbox.setRange(0, 1e9)  # Rango grande
                    distancia_spinbox.setDecimals(5)  # Hasta 5 decimales
                    table.setCellWidget(row, 3, distancia_spinbox)
                    # Acciones a Realizar
                    acciones_item = QTableWidgetItem("")
                    table.setItem(row, 4, acciones_item)
        def load_umbrales():
            nonlocal table
            selected_option = combo.currentText()
            tipografica = options[selected_option]  # Obtener el ID correspondiente
            componente_id = component_combo.currentData()  # Obtener el ID del componente seleccionado
            umbrales = UmbralController.ctrlObtenerUmbralesAjustes(proyectoid, componente_id, tipografica, tipo)
            if umbrales:
                table = crear_tabla()
                table.setRowCount(len(umbrales))
                if tipografica == "AMA":
                    for row, umbral in enumerate(umbrales):
                        # Nombre
                        nombre_item = QTableWidgetItem(umbral[3])
                        nombre_item.setData(Qt.UserRole, umbral[0])  # Guardar el ID del umbral en el item
                        table.setItem(row, 0, nombre_item)
                        # Botón de color
                        color_button = QPushButton()
                        color_button.setStyleSheet(f"background-color: {umbral[4]};")
                        color_button.clicked.connect(lambda *args, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
                        table.setCellWidget(row, 1, color_button)
                        # Riesgo
                        riesgo_item = QTableWidgetItem(umbral[5])  # Asumiendo que el riesgo
                        table.setItem(row, 2, riesgo_item)
                        # Distancia (DoubleSpinBox)
                        distancia_spinbox = QDoubleSpinBox()
                        distancia_spinbox.setRange(0, 1e9)  # Rango grande
                        distancia_spinbox.setDecimals(5)  # Hasta 5 decimales
                        distancia_spinbox.setValue(umbral[6])
                        table.setCellWidget(row, 3, distancia_spinbox)
                        # Magnitud (DoubleSpinBox)
                        magnitud_spinbox = QDoubleSpinBox()
                        magnitud_spinbox.setRange(0, 1e9)  # Rango grande
                        magnitud_spinbox.setDecimals(5)  # Hasta 5 decimales
                        magnitud_spinbox.setValue(umbral[7])  
                        table.setCellWidget(row, 4, magnitud_spinbox)
                        # Acciones a Realizar
                        acciones_item = QTableWidgetItem(umbral[8]) 
                        table.setItem(row, 5, acciones_item)
                else:
                    for row, umbral in enumerate(umbrales):
                        # Condición
                        condicion_item = QTableWidgetItem(umbral[3])  # Asumiendo que la condición está en la posición 3
                        condicion_item.setData(Qt.UserRole, umbral[0])  # Guardar el ID del umbral en el item
                        table.setItem(row, 0, condicion_item)
                        # Botón de color
                        color_button = QPushButton()
                        color_button.setStyleSheet(f"background-color: {umbral[4]};")  # Asumiendo que el color está en la posición 4
                        color_button.clicked.connect(lambda *args, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
                        table.setCellWidget(row, 1, color_button)
                        # Riesgo
                        riesgo_item = QTableWidgetItem(umbral[5])  # Asumiendo que el riesgo está en la posición 5
                        table.setItem(row, 2, riesgo_item)
                        # Rango (DoubleSpinBox)
                        double_spinbox = QDoubleSpinBox()
                        double_spinbox.setRange(-1e9, 1e9)  # Rango grande
                        double_spinbox.setDecimals(5)  # Hasta 5 decimales
                        double_spinbox.setValue(umbral[6]) # Asumiendo que el rango está en la posición 6
                        table.setCellWidget(row, 3, double_spinbox)
                        # Acciones a realizar
                        acciones_item = QTableWidgetItem(umbral[8])  # Asumiendo que las acciones están en la posición 8
                        table.setItem(row, 4, acciones_item)
            else:
                reset_table()
        # Conectar el cambio de opción en el ComboBox para cargar los umbrales
        combo.currentIndexChanged.connect(load_umbrales)
        component_combo.currentIndexChanged.connect(load_umbrales)
        # Configurar las columnas iniciales
        load_umbrales()
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
            nonlocal table
            row_count = table.rowCount()
            table.insertRow(row_count)
            selected_option = combo.currentText()
            tipografica = options[selected_option]
            if tipografica == "AMA":
                # Nombre
                nombre_item = QTableWidgetItem("")
                table.setItem(row_count, 0, nombre_item)
                # Color
                color_button = QPushButton()
                color_button.clicked.connect(lambda *args, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
                table.setCellWidget(row_count, 1, color_button)
                # Riesgo
                riesgo_item = QTableWidgetItem("")
                table.setItem(row_count, 2, riesgo_item)
                # Distancia
                distancia = QDoubleSpinBox()
                distancia.setRange(0, 1e9)
                distancia.setDecimals(5)
                table.setCellWidget(row_count, 3, distancia)
                # Magnitud
                magnitud = QDoubleSpinBox()
                magnitud.setRange(0, 1e9)
                magnitud.setDecimals(5)
                table.setCellWidget(row_count, 4, magnitud)
                # Acciones
                acciones_item = QTableWidgetItem("")
                table.setItem(row_count, 5, acciones_item)
            else:
                # Condición
                condicion_item = QTableWidgetItem("")
                table.setItem(row_count, 0, condicion_item)
                # Color
                color_button = QPushButton()
                color_button.clicked.connect(lambda *args, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
                table.setCellWidget(row_count, 1, color_button)
                # Riesgo
                riesgo_item = QTableWidgetItem("")
                table.setItem(row_count, 2, riesgo_item)
                # Rango
                double_spinbox = QDoubleSpinBox()
                double_spinbox.setRange(-1e9, 1e9)
                double_spinbox.setDecimals(5)
                table.setCellWidget(row_count, 3, double_spinbox)
                # Acciones
                acciones_item = QTableWidgetItem("")
                table.setItem(row_count, 4, acciones_item)
        # Conectar el botón a la función para agregar una nueva fila
        add_button.clicked.connect(add_row)
        # Función para manejar el evento de confirmar
        def confirm():
            nonlocal table
            selected_option = combo.currentText()
            tipografica = options[selected_option]
            componente_id = component_combo.currentData()
            data = []
            if tipografica == "AMA":
                for row in range(table.rowCount()):
                    nombre_item = table.item(row, 0)
                    distancia_item = table.cellWidget(row, 3)
                    magnitud_item = table.cellWidget(row, 4)
                    riesgo_item = table.item(row, 2)
                    acciones_item = table.item(row, 5)
                    if nombre_item and nombre_item.text() and distancia_item and magnitud_item and riesgo_item and acciones_item:
                        color_button = table.cellWidget(row, 1)
                        color = color_button.palette().button().color().name()
                        data.append({
                            "id": table.item(row, 0).data(Qt.UserRole) if table.item(row, 0) else None,  # Obtener el ID del umbral si existe
                            "nombre": nombre_item.text(),
                            "riesgo": riesgo_item.text(),
                            "color": color,
                            "distancia": distancia_item.value(),
                            "magnitud": magnitud_item.value(),
                            "acciones": acciones_item.text(),
                            "tipo": "AMA"
                        })
                # Guardar los datos en la base de datos
                success = UmbralController.ctrlGuardarUmbralesAcelerografos(proyectoid, componente_id, tipografica, data, tipo)
            else:
                for row in range(table.rowCount()):
                    condicion_item = table.item(row, 0)
                    rango_item = table.cellWidget(row, 3)
                    riesgo_item = table.item(row, 2)
                    acciones_item = table.item(row, 4)
                    if condicion_item and condicion_item.text() and rango_item and rango_item.value():
                        color_button = table.cellWidget(row, 1)
                        color = color_button.palette().button().color().name()
                        valorrango = float(rango_item.value())
                        data.append({
                            "id": table.item(row, 0).data(Qt.UserRole) if table.item(row, 0) else None,  # Obtener el ID del umbral si existe
                            "condicion": condicion_item.text(),
                            "color": color,
                            "riesgo": riesgo_item.text(),
                            "rango": valorrango,
                            "acciones": acciones_item.text()
                        })
                # Guardar los datos en la base de datos
                success = UmbralController.ctrlGuardarUmbralesEquipos(proyectoid, componente_id, tipografica, data, tipo)
            if success:
                mostrar_mensaje("Guardado", "Se guardó el umbral.", 'informacion')
                load_umbrales()
            else:
                mostrar_mensaje("Error", "Error al guardar umbral", 'error')
        # Conectar el botón Confirmar a la función confirm
        confirm_button.clicked.connect(confirm)
        # Función para eliminar una fila
        def delete_row(position):
            nonlocal table
            item = table.itemAt(position)
            if item:
                row = item.row()
                condicion_item = table.item(row, 0)
                if condicion_item:
                    umbral_id = condicion_item.data(Qt.UserRole)
                    if umbral_id and umbral_id != 0:
                        # Llamar a la base de datos para eliminar el registro
                        success = UmbralController.ctrlEliminarUmbralEquipos(umbral_id)
                        if success:
                            print(f"Registro con ID {umbral_id} eliminado exitosamente.")
                        else:
                            mostrar_mensaje("Error", f"Error al eliminar el registro con ID {umbral_id}.", 'error')
                            return
                # Eliminar la fila de la tabla
                table.removeRow(row)
                # Recargar los datos de la tabla
                load_umbrales()
        # Calcular el ancho total de las columnas
        total_width = sum(table.columnWidth(col) for col in range(table.columnCount()))
        # Ajustar el tamaño del diálogo al contenido
        dialog.adjustSize()
        # Establecer el ancho inicial del diálogo basado en el ancho total de las columnas
        dialog.resize(total_width + 60, dialog.height())  # Añadir un margen adicional si es necesario
        # Mostrar el diálogo
        dialog.exec()

    def modalUmbralesTDR(proyectoid, tipo, unidad):
        # Crear el diálogo
        dialog = QDialog()
        dialog.setWindowTitle("Umbrales Generales - TDR")
        # Layout principal
        main_layout = QVBoxLayout()
        # Nuevo ComboBox al inicio
        component_combo_label = QLabel("Seleccione Componente:")
        component_combo = QComboBox()
        # Añadir opciones al nuevo ComboBox desde listacomponente
        listacomponente = InterfazController.ctrlListarComponentesProyecto(proyectoid)
        if listacomponente:
            component_combo.addItem("TODOS", userData=0)
            for componente in listacomponente:
                component_combo.addItem(componente[2], userData=componente[0])
            component_combo.setCurrentIndex(0)
        # Añadir el nuevo ComboBox al layout principal
        main_layout.addWidget(component_combo_label)
        main_layout.addWidget(component_combo)
        # Layout para el ComboBox y el botón
        combo_layout = QHBoxLayout()
        # ComboBox
        combo_label = QLabel("Seleccione Umbral:")
        combo_tipo = QComboBox()
        options = UmbralView.retornarArregloTipo(tipo)
        # Añadir opciones al ComboBox
        combo_tipo.addItems(options.keys())
        # Botón al lado del ComboBox
        add_button = QPushButton("Agregar Fila")
        # Añadir ComboBox y botón al layout horizontal
        combo_layout.addWidget(combo_label)
        combo_layout.addWidget(combo_tipo)
        combo_layout.addWidget(add_button)
        # Añadir el layout horizontal al layout principal
        main_layout.addLayout(combo_layout)
        # Tabla
        table = QTableWidget(3, 5)  # 3 filas y 5 columnas
        # Función para reiniciar la tabla
        def reset_table():
            table.setHorizontalHeaderLabels(["Condición", "Color", "Riesgo", f"Rango (Ω)", "Acciones a realizar"])
            table.setRowCount(3)
            for row in range(3):
                # Condición
                condicion_item = QTableWidgetItem("")
                table.setItem(row, 0, condicion_item)
                # Botón de color
                color_button = QPushButton()
                color_button.clicked.connect(lambda *args, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
                table.setCellWidget(row, 1, color_button)
                # Riesgo
                riesgo_item = QTableWidgetItem("")
                table.setItem(row, 2, riesgo_item)
                # Rango (DoubleSpinBox)
                double_spinbox = QDoubleSpinBox()
                double_spinbox.setRange(-1e9, 1e9)  # Rango grande
                double_spinbox.setDecimals(5)  # Hasta 5 decimales
                table.setCellWidget(row, 3, double_spinbox)
                # Acciones a realizar
                acciones_item = QTableWidgetItem("")
                table.setItem(row, 4, acciones_item)
        def load_umbrales():
            selected_option = combo_tipo.currentText()
            selected_id = options[selected_option]
            selected_componente_id = component_combo.currentData()  # Obtener el ID del componente seleccionado
            umbrales = UmbralController.ctrlObtenerUmbralesAjustes(proyectoid, selected_componente_id, selected_id, tipo)
            if umbrales:
                table.setHorizontalHeaderLabels(["Condición", "Color", "Riesgo", f"Rango (Ω)", "Acciones a realizar"])
                table.setRowCount(len(umbrales))
                for row, umbral in enumerate(umbrales):
                    # Condición
                    condicion_item = QTableWidgetItem(umbral[3])
                    condicion_item.setData(Qt.UserRole, umbral[0])
                    table.setItem(row, 0, condicion_item)
                    # Botón de color
                    color_button = QPushButton()
                    color_button.setStyleSheet(f"background-color: {umbral[4]};")
                    color_button.clicked.connect(lambda *args, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
                    table.setCellWidget(row, 1, color_button)
                    # Riesgo
                    riesgo_item = QTableWidgetItem(umbral[5])
                    table.setItem(row, 2, riesgo_item)
                    # Rango (DoubleSpinBox)
                    double_spinbox = QDoubleSpinBox()
                    double_spinbox.setRange(-1e9, 1e9)
                    double_spinbox.setDecimals(5)
                    double_spinbox.setValue(umbral[6] * unidad)
                    table.setCellWidget(row, 3, double_spinbox)
                    # Acciones a realizar
                    acciones_item = QTableWidgetItem(umbral[8])
                    table.setItem(row, 4, acciones_item)
            else:
                reset_table()
        # Conectar el cambio de opción en el ComboBox para cargar los umbrales
        combo_tipo.currentIndexChanged.connect(load_umbrales)
        component_combo.currentIndexChanged.connect(load_umbrales)
        # Configurar las columnas iniciales
        load_umbrales()
        # Añadir la tabla al layout
        main_layout.addWidget(table)
        # Layout para el botón Confirmar y el espacer
        confirm_layout = QHBoxLayout()
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        confirm_layout.addSpacerItem(spacer)
        confirm_button = QPushButton("Confirmar")
        confirm_layout.addWidget(confirm_button)
        main_layout.addLayout(confirm_layout)
        dialog.setLayout(main_layout)
        # Función para agregar una nueva fila
        def add_row():
            row_count = table.rowCount()
            table.insertRow(row_count)
            condicion_item = QTableWidgetItem("")
            table.setItem(row_count, 0, condicion_item)
            color_button = QPushButton()
            color_button.clicked.connect(lambda *args, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
            table.setCellWidget(row_count, 1, color_button)
            riesgo_item = QTableWidgetItem("")
            table.setItem(row_count, 2, riesgo_item)
            double_spinbox = QDoubleSpinBox()
            double_spinbox.setRange(-1e9, 1e9)
            double_spinbox.setDecimals(5)
            table.setCellWidget(row_count, 3, double_spinbox)
            acciones_item = QTableWidgetItem("")
            table.setItem(row_count, 4, acciones_item)
        add_button.clicked.connect(add_row)
        # Función para manejar el evento de confirmar
        def confirm():
            selected_option = combo_tipo.currentText()
            selected_id = options[selected_option]
            selected_component_id = component_combo.currentData()
            data = []
            for row in range(table.rowCount()):
                condicion_item = table.item(row, 0)
                rango_item = table.cellWidget(row, 3)
                riesgo_item = table.item(row, 2)
                acciones_item = table.item(row, 4)
                if condicion_item and condicion_item.text() and rango_item and rango_item.value():
                    color_button = table.cellWidget(row, 1)
                    color = color_button.palette().button().color().name()
                    valorrango = float(rango_item.value()) / unidad
                    data.append({
                        "id": table.item(row, 0).data(Qt.UserRole) if table.item(row, 0) else None,
                        "condicion": condicion_item.text(),
                        "color": color,
                        "riesgo": riesgo_item.text(),
                        "rango": valorrango,
                        "acciones": acciones_item.text()
                    })
            success = UmbralController.ctrlGuardarUmbralesEquipos(proyectoid, selected_component_id, selected_id, data, tipo)
            if success:
                load_umbrales()
                mostrar_mensaje("Guardado", "Se guardó el umbral.", 'informacion')
            else:
                mostrar_mensaje("Error", "Error al guardar umbral", 'error')
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
                condicion_item = table.item(row, 0)
                if condicion_item:
                    umbral_id = condicion_item.data(Qt.UserRole)
                    if umbral_id and umbral_id != 0:
                        success = UmbralController.ctrlEliminarUmbralEquipos(umbral_id)
                        if success:
                            print(f"Registro con ID {umbral_id} eliminado exitosamente.")
                        else:
                            mostrar_mensaje("Error", f"Error al eliminar el registro con ID {umbral_id}.", 'error')
                            return
                table.removeRow(row)
                load_umbrales()
        table.setContextMenuPolicy(Qt.CustomContextMenu)
        table.customContextMenuRequested.connect(show_context_menu)
        total_width = sum(table.columnWidth(col) for col in range(table.columnCount()))
        dialog.adjustSize()
        dialog.resize(total_width + 50, dialog.height())
        dialog.exec()


    
    def dialogoConfiguracionVectores(estadocheck, tipov, escala):
        global estadovector, tipovector, escalavector, estadodialog
        estadodialog, estadovector, tipovector, escalavector = False, False, "", 0
        loader = QUiLoader()
        ui_file_path = resource_path("ui/configuracionvectores.ui")
        ui_file = loader.load(ui_file_path, None)
        # Configurar el cuadro de diálogo
        dialogo = QDialog()
        dialogo.setWindowTitle("Escalar Vectores")
        layout = QVBoxLayout()
        layout.addWidget(ui_file)
        dialogo.setLayout(layout)
        # Acceso a los botones
        combotipo = dialogo.findChild(QComboBox, "combo_tipo")
        spinescala = dialogo.findChild(QSpinBox, "spin_escala")
        checkestado = dialogo.findChild(QCheckBox, "check_estado")
        btnAceptar = dialogo.findChild(QPushButton, "btn_confirmar")
        # Cargar combo
        item1 = ("D3D", "Desplaz. 3D")
        item2 = ("VI3D", "Vel. Inc. 3D")
        # Agregar elementos al combo con valores y texto
        for valor, texto in [item1, item2]:
            combotipo.addItem(texto, valor)
        combotipo.setCurrentIndex(combotipo.findData(tipov))
        spinescala.setValue(escala)
        checkestado.setChecked(estadocheck)
        
        def aceptarTipovectores():
            global estadodialog, estadovector, tipovector, escalavector
            estadovector = checkestado.isChecked()
            tipovector = combotipo.currentData()
            escalavector = int(spinescala.value())
            estadodialog = True
            dialogo.close()
        # conectar botones
        btnAceptar.clicked.connect(aceptarTipovectores)
        dialogo.exec()
        return estadodialog, estadovector, tipovector, escalavector
    
    def cambiarColor_botones(botonColor):
        color = QColorDialog.getColor()
        if color.isValid():
            botonColor.setStyleSheet("background-color: %s" % color.name())
    
    def dialogoEscalaInclinometros(escala):
        global estadoescalainccli, escalainclino
        estadoescalainccli, escalainclino = False, 0
        loader = QUiLoader()
        ui_file_path = resource_path("ui/inclinometrosescala.ui")
        ui_file = loader.load(ui_file_path, None)
        # Configurar el cuadro de diálogo
        dialogo = QDialog()
        dialogo.setWindowTitle("Escalar Inclinómetros")
        layout = QVBoxLayout()
        layout.addWidget(ui_file)
        dialogo.setLayout(layout)
        # Acceso a los botones
        spinescala = dialogo.findChild(QSpinBox, "spin_escala")
        btnAceptar = dialogo.findChild(QPushButton, "btn_confirmar")
        # Agregar elementos al combo con valores y texto
        spinescala.setValue(escala)
        def aceptarEscala():
            global escalainclino, estadoescalainccli
            escalainclino = int(spinescala.value())
            estadoescalainccli = True
            dialogo.close()
        # conectar botones
        btnAceptar.clicked.connect(aceptarEscala)
        dialogo.exec()
        return estadoescalainccli, escalainclino
    
    def retornarArregloTipo(tipo):
        if tipo == 'PRISMAS':
            options = {
                "Desplazamiento Acum. 3D": "3DA",
                "Desplazamiento Incr. 3D": "3DI",
                "Desplazamiento Acum. 2D": "2DA",
                "Desplazamiento Incr. 2D": "2DI",
                "Desplazamiento Acum. SD": "SDA",
                "Desplazamiento Incr. SD": "SDI",
                "Desplazamiento Acum. L": "DLA",
                "Desplazamiento Incr. L": "DLI",
                "Desplazamiento Acum. T": "DTA",
                "Desplazamiento Incr. T": "DTI",
                "Desplazamiento Acum. H": "DHA",
                "Desplazamiento Incr. H": "DHI",
                "Desplazamiento Acum. N": "DNA",
                "Desplazamiento Incr. N": "DNI",
                "Desplazamiento Acum. E": "DEA",
                "Desplazamiento Incr. E": "DEI",
                "Desplazamiento Acum. Z": "DZA",
                "Desplazamiento Incr. Z": "DZI",
                "Velocidad Incremental 3D": "VI3D",
                "Velocidad Acumulada 3D": "VA3D",
                "Velocidad Incremental 2D": "VI2D",
                "Velocidad Acumulada 2D":"VA2D",
                "Velocidad Incremental SD": "VISD",
                "Velocidad Acumulada SD" :"VASD",
            }
            return options
        elif tipo == 'INCLINOMETRO':
            options = {
                "Desplaz. Acumulado AB": "DAAB",
                "Desplaz. Incremental AB": "DIAB",
                "Desplaz. Acumulado NE": "DANE",
                "Desplaz. Incremental NE": "DINE",
                "Posición Absoluta AB": "PAAB",
                "Posición Absoluta NE": "PANE",
                "Checksum AB": "CSAB",
            }
            return options
        elif tipo == 'PIEZOMETROMANUAL':
            options = {
                "Nivel Freático": "NF",
                "Nivel Incremental": "NI",
                "Nivel Acumulado": "NA",
                "Frecuencia": "FP",
                "Temperatura": "TP",
            }
            return options

        elif tipo == 'PIEZOMETROCUERDA':
            options = {
                "Nivel Freático": "NF",
                "Nivel Incremental": "NI",
                "Nivel Acumulado": "NA",
                "Presión Barométrica": "PB",
                "Frecuencia": "FP",
                "Temperatura": "TP",
            }
            return options
        
        elif tipo == 'CELDA':
            options = {
                "Velocidad Incremental": "VI",
                "Asentamiento en Cota": "AC",
                "Asentamiento Incremental": "AI",
                "Asentamiento Acumulado": "AA",
                "Frecuencia": "AF",
                "Temperatura": "AT",
            }
            return options
        elif tipo == 'ACELEROGRAFO':
            options = {
                "Aceleración": "AAC",
                "Velocidad": "AVE",
                "Desplazamiento": "ADE",
                "Magnitud": "AMA"
            }
            return options
        elif tipo == 'TDR':
            options = {
                "Impedancia": "IP",
            }
            return options
        else:
            options = {
                  
            }
            return options
    
    def modalUmbralesPersonalizadosInclinometros(proyectoid, tipo, unidad):
        # Añadir opciones al nuevo ComboBox desde listacomponente
        listacomponente = InterfazController.ctrlListarComponentesProyecto(proyectoid)
        titulo_combo = "Seleccione Componente:"
        # Crear el diálogo
        dialog = QDialog()
        dialog.setWindowTitle("Umbrales Personalizados - Inclinómetros")
        # Layout principal
        main_layout = QVBoxLayout()
        # Nuevo ComboBox al inicio
        component_combo_label = QLabel(titulo_combo)
        component_combo = QComboBox()
        if listacomponente:
            component_combo.addItem("TODOS", userData=0)
            for componente in listacomponente:
                component_combo.addItem(componente[2], userData=componente[0])
            component_combo.setCurrentIndex(0)
        # Añadir el nuevo ComboBox al layout principal
        main_layout.addWidget(component_combo_label)
        main_layout.addWidget(component_combo)

        # Combo de Inclinómetro, filtrado por componente
        inclinometro_combo_label = QLabel("Seleccione Inclinómetro:")
        inclinometro_combo = QComboBox()
        main_layout.addWidget(inclinometro_combo_label)
        main_layout.addWidget(inclinometro_combo)

        # Layout para el ComboBox y el botón
        combo_layout = QHBoxLayout()
        # ComboBox
        combo_label = QLabel("Seleccione Umbral:")
        combo = QComboBox()
        options = UmbralView.retornarArregloTipo(tipo)
        # Añadir opciones al ComboBox
        combo.addItems(options.keys())
        # Botón al lado del ComboBox
        add_button = QPushButton("Agregar Fila")
        # Añadir ComboBox y botón al layout horizontal
        combo_layout.addWidget(combo_label)
        combo_layout.addWidget(combo)
        combo_layout.addWidget(add_button)
        # Añadir el layout horizontal al layout principal
        main_layout.addLayout(combo_layout)
        # Tabla
        table = QTableWidget(3, 5)  # 3 filas y 5 columnas

        def cargar_inclinometros():
            componente_id = component_combo.currentData()
            inclinometro_combo.clear()
            instrumentos = UmbralController.ctrlListarInstrumentosComponente(proyectoid, componente_id, tipo)
            if instrumentos:
                for id_equipo, nombre_equipo, tipo_equipo in instrumentos:
                    inclinometro_combo.addItem(nombre_equipo, userData=id_equipo)
            else:
                inclinometro_combo.addItem("Sin inclinómetros registrados", userData=None)

        component_combo.currentIndexChanged.connect(cargar_inclinometros)
        cargar_inclinometros()  # carga inicial

        def reset_table():
            if unidad == 1:
                medida = "m"
            elif unidad == 100:
                medida = "cm"
            else:
                medida = "mm"
            table.setHorizontalHeaderLabels(["Condición", "Color", "Riesgo", f"Rango ({medida})", "Acciones a realizar"])
            table.setRowCount(3)
            for row in range(3):
                # Condición
                condicion_item = QTableWidgetItem("")
                table.setItem(row, 0, condicion_item)
                # Botón de color
                color_button = QPushButton()
                color_button.clicked.connect(lambda *args, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
                table.setCellWidget(row, 1, color_button)
                # Riesgo
                riesgo_item = QTableWidgetItem("")
                table.setItem(row, 2, riesgo_item)
                # Rango (DoubleSpinBox)
                double_spinbox = QDoubleSpinBox()
                double_spinbox.setRange(-1e9, 1e9)  # Rango grande
                double_spinbox.setDecimals(5)  # Hasta 5 decimales
                table.setCellWidget(row, 3, double_spinbox)
                # Acciones a realizar
                acciones_item = QTableWidgetItem("")
                table.setItem(row, 4, acciones_item)
        def load_umbrales():
            selected_option = combo.currentText()
            selected_id = options[selected_option]  # Obtener el ID correspondiente del tipo
            selected_equipo_id = inclinometro_combo.currentData()  # Obtener el ID del inclinómetro seleccionado
            if unidad == 1:
                medida = "m"
            elif unidad == 100:
                medida = "cm"
            else:
                medida = "mm"
            umbrales = UmbralController.ctrlObtenerUmbralesPersonalizados(selected_equipo_id, selected_id, tipo)
            if umbrales:
                table.setHorizontalHeaderLabels(["Condición", "Color", "Riesgo", f"Rango ({medida})", "Acciones a realizar"])
                table.setRowCount(len(umbrales))
                for row, umbral in enumerate(umbrales):
                    # Condición
                    condicion_item = QTableWidgetItem(umbral[3])  # Asumiendo que la condición está en la posición 3
                    condicion_item.setData(Qt.UserRole, umbral[0])  # Guardar el ID del umbral en el item
                    table.setItem(row, 0, condicion_item)
                    # Botón de color
                    color_button = QPushButton()
                    color_button.setStyleSheet(f"background-color: {umbral[4]};")  # Asumiendo que el color está en la posición 4
                    color_button.clicked.connect(lambda *args, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
                    table.setCellWidget(row, 1, color_button)
                    # Riesgo
                    riesgo_item = QTableWidgetItem(umbral[5])  # Asumiendo que el riesgo está en la posición 5
                    table.setItem(row, 2, riesgo_item)
                    # Rango (DoubleSpinBox)
                    double_spinbox = QDoubleSpinBox()
                    double_spinbox.setRange(-1e9, 1e9)  # Rango grande
                    double_spinbox.setDecimals(5)  # Hasta 5 decimales
                    double_spinbox.setValue(umbral[6] * unidad) # Asumiendo que el rango está en la posición 5
                    table.setCellWidget(row, 3, double_spinbox)
                    # Acciones a realizar
                    acciones_item = QTableWidgetItem(umbral[8])  # Asumiendo que las acciones están en la posición 6
                    table.setItem(row, 4, acciones_item)
            else:
                reset_table()
        # Conectar el cambio de opción en el ComboBox para cargar los umbrales
        combo.currentIndexChanged.connect(load_umbrales)
        component_combo.currentIndexChanged.connect(load_umbrales)
        inclinometro_combo.currentIndexChanged.connect(load_umbrales)

        # Configurar las columnas iniciales
        load_umbrales()
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
            # Condición
            condicion_item = QTableWidgetItem("")
            table.setItem(row_count, 0, condicion_item)
            # Botón de color
            color_button = QPushButton()
            color_button.clicked.connect(lambda *args, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
            table.setCellWidget(row_count, 1, color_button)
            # Riesgo
            riesgo_item = QTableWidgetItem("")
            table.setItem(row_count, 2, riesgo_item)
            # Rango (DoubleSpinBox)
            double_spinbox = QDoubleSpinBox()
            double_spinbox.setRange(-1e9, 1e9)  # Rango grande
            double_spinbox.setDecimals(5)  # Hasta 5 decimales
            table.setCellWidget(row_count, 3, double_spinbox)
            # Acciones a realizar
            acciones_item = QTableWidgetItem("")
            table.setItem(row_count, 4, acciones_item)
        # Conectar el botón a la función para agregar una nueva fila
        add_button.clicked.connect(add_row)
        # Función para manejar el evento de confirmar
        def confirm():
            if not inclinometro_combo.currentData():
                mostrar_mensaje("Advertencia", "Debe seleccionar un inclinómetro.", 'advertencia')
                return
            selected_option = combo.currentText()
            selected_id = options[selected_option]  # Obtener el ID correspondiente
            selected_equipos_id = inclinometro_combo.currentData()  # Obtener el ID del inclinómetro seleccionado
            data = []
            for row in range(table.rowCount()):
                condicion_item = table.item(row, 0)
                rango_item = table.cellWidget(row, 3)
                riesgo_item = table.item(row, 2)
                acciones_item = table.item(row, 4)
                if condicion_item and condicion_item.text() and rango_item and rango_item.value():
                    color_button = table.cellWidget(row, 1)
                    color = color_button.palette().button().color().name()
                    valorrango = float(rango_item.value()) / unidad
                    data.append({
                        "id": table.item(row, 0).data(Qt.UserRole) if table.item(row, 0) else None,  # Obtener el ID del umbral si existe
                        "condicion": condicion_item.text(),
                        "color": color,
                        "riesgo": riesgo_item.text(),
                        "rango": valorrango,
                        "acciones": acciones_item.text()
                    })
            # Guardar los datos en la base de datos
            success = UmbralController.ctrlGuardarUmbralesPersonalizados(proyectoid, selected_equipos_id, selected_id, data, tipo)
            if success:
                load_umbrales()
                mostrar_mensaje("Guardado", "Se guardó el umbral.", 'informacion')
            else:
                mostrar_mensaje("Error", "Error al guardar umbral", 'error')
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
                condicion_item = table.item(row, 0)
                if condicion_item:
                    umbral_id = condicion_item.data(Qt.UserRole)
                    if umbral_id and umbral_id != 0:
                        # Llamar a la base de datos para eliminar el registro
                        success = UmbralController.ctrlEliminarUmbralPersonalizados(umbral_id)
                        if success:
                            print(f"Registro con ID {umbral_id} eliminado exitosamente.")
                        else:
                            mostrar_mensaje("Error", f"Error al eliminar el registro con ID {umbral_id}.", 'error')
                            return
                # Eliminar la fila de la tabla
                table.removeRow(row)
                # Recargar los datos de la tabla
                load_umbrales()
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
        
    def modalUmbralesPersonalizadosAcelerografos(proyectoid, tipo):
        table = None
        # Crear el diálogo
        dialog = QDialog()
        dialog.setWindowTitle("Umbrales Personalizados - Acelerógrafos")
        # Layout principal
        main_layout = QVBoxLayout()
        # Nuevo ComboBox al inicio
        component_combo_label = QLabel("Seleccione Componente:")
        component_combo = QComboBox()

        # 1) Poblar componente PRIMERO
        listacomponente = InterfazController.ctrlListarComponentesProyecto(proyectoid)
        if listacomponente:
            component_combo.addItem("TODOS", userData=0)
            for componente in listacomponente:
                component_combo.addItem(componente[2], userData=componente[0])
            component_combo.setCurrentIndex(0)
        main_layout.addWidget(component_combo_label)
        main_layout.addWidget(component_combo)

        # 2) Luego crear el combo de acelerógrafo, ya con componente_combo poblado
        acelerografo_combo_label = QLabel("Seleccione Acelerógrafo:")
        acelerografo_combo = QComboBox()
        main_layout.addWidget(acelerografo_combo_label)
        main_layout.addWidget(acelerografo_combo)

        # Layout para el ComboBox y el botón
        combo_layout = QHBoxLayout()
        # ComboBox
        combo_label = QLabel("Seleccione Umbral:")
        combo = QComboBox()
        options = UmbralView.retornarArregloTipo(tipo)
        # Añadir opciones al ComboBox
        combo.addItems(options.keys())
        # Botón al lado del ComboBox
        add_button = QPushButton("Agregar Fila")
        # Añadir ComboBox y botón al layout horizontal
        combo_layout.addWidget(combo_label)
        combo_layout.addWidget(combo)
        combo_layout.addWidget(add_button)
        # Añadir el layout horizontal al layout principal
        main_layout.addLayout(combo_layout)
        # Guardamos la posición correcta donde siempre debe insertarse la tabla
        table_row_index = main_layout.count()

        def cargar_acelerografos():
            componente_id = component_combo.currentData()
            acelerografo_combo.clear()
            instrumentos = UmbralController.ctrlListarInstrumentosComponente(proyectoid, componente_id, tipo)
            if instrumentos:
                for id_equipo, nombre_equipo, tipo_equipo in instrumentos:
                    acelerografo_combo.addItem(nombre_equipo, userData=id_equipo)
            else:
                acelerografo_combo.addItem("Sin acelerógrafos registrados", userData=None)

        component_combo.currentIndexChanged.connect(cargar_acelerografos)
        cargar_acelerografos()  # ahora sí, con componente_id válido

        # Función para mostrar el menú contextual (definida antes de crear_tabla)
        def show_context_menu(position):
            nonlocal table
            menu = QMenu()
            delete_action = QAction("Eliminar", menu)
            delete_action.triggered.connect(lambda: delete_row(position))
            menu.addAction(delete_action)
            menu.exec(table.viewport().mapToGlobal(position))

        def crear_tabla():
            nonlocal table  # acceder a la variable table definida afuera
            selected_option = combo.currentText()
            tipografica = options[selected_option]
            # Si ya hay una tabla previa, eliminarla del layout
            if table is not None:
                main_layout.removeWidget(table)
                table.deleteLater()
                table = None
            if tipografica == "AMA":
                table = QTableWidget(3, 6)
                table.setHorizontalHeaderLabels(["Nombre", "Color", "Riesgo", "Distancia (km)", "Magnitud (M)", "Acciones a Realizar"])
            else:
                table = QTableWidget(3, 5)
                if tipografica == "AAC":
                    medida = "m/s²"
                elif tipografica == "AVE":
                    medida = "m/s"
                elif tipografica == "ADE":
                    medida = "m"
                table.setHorizontalHeaderLabels(["Condición", "Color", "Riesgo", f"Rango ({medida})", "Acciones a realizar"])
            table.setContextMenuPolicy(Qt.CustomContextMenu)
            table.customContextMenuRequested.connect(show_context_menu)
            main_layout.insertWidget(table_row_index, table)
            return table

        # Función para reiniciar la tabla
        def reset_table():
            nonlocal table
            table = crear_tabla()
            table.setRowCount(3)
            selected_option = combo.currentText()
            tipografica = options[selected_option]
            if tipografica == "AMA":
                for row in range(3):
                    # Condición
                    condicion_item = QTableWidgetItem("")
                    table.setItem(row, 0, condicion_item)
                    # Botón de color
                    color_button = QPushButton()
                    color_button.clicked.connect(lambda *args, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
                    table.setCellWidget(row, 1, color_button)
                    # Riesgo
                    riesgo_item = QTableWidgetItem("")
                    table.setItem(row, 2, riesgo_item)
                    # Distancia (DoubleSpinBox)
                    double_spinbox = QDoubleSpinBox()
                    double_spinbox.setRange(-1e9, 1e9)  # Rango grande
                    double_spinbox.setDecimals(5)  # Hasta 5 decimales
                    table.setCellWidget(row, 3, double_spinbox)
                    # Magnitud (DoubleSpinBox)
                    double_spinbox = QDoubleSpinBox()
                    double_spinbox.setRange(-1e9, 1e9)  # Rango grande
                    double_spinbox.setDecimals(5)  # Hasta 5 decimales
                    table.setCellWidget(row, 4, double_spinbox)
                    # Acciones a realizar
                    acciones_item = QTableWidgetItem("")
                    table.setItem(row, 5, acciones_item)
            else:
                for row in range(3):
                    # Nombre
                    nombre_item = QTableWidgetItem("")
                    table.setItem(row, 0, nombre_item)
                    # Botón de color
                    color_button = QPushButton()
                    color_button.clicked.connect(lambda *args, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
                    table.setCellWidget(row, 1, color_button)
                    # Riesgo
                    riesgo_item = QTableWidgetItem("")
                    table.setItem(row, 2, riesgo_item)
                    # Rango (DoubleSpinBox)
                    distancia_spinbox = QDoubleSpinBox()
                    distancia_spinbox.setRange(0, 1e9)  # Rango grande
                    distancia_spinbox.setDecimals(5)  # Hasta 5 decimales
                    table.setCellWidget(row, 3, distancia_spinbox)
                    # Acciones a Realizar
                    acciones_item = QTableWidgetItem("")
                    table.setItem(row, 4, acciones_item)

        def load_umbrales():
            nonlocal table
            selected_option = combo.currentText()
            tipografica = options[selected_option]  # Obtener el ID correspondiente
            acelerografo_id = acelerografo_combo.currentData()  # Obtener el ID del acelerógrafo seleccionado
            umbrales = UmbralController.ctrlObtenerUmbralesPersonalizados(acelerografo_id, tipografica, tipo)
            if umbrales:
                table = crear_tabla()
                table.setRowCount(len(umbrales))
                if tipografica == "AMA":
                    for row, umbral in enumerate(umbrales):
                        # Nombre
                        nombre_item = QTableWidgetItem(umbral[3])
                        nombre_item.setData(Qt.UserRole, umbral[0])  # Guardar el ID del umbral en el item
                        table.setItem(row, 0, nombre_item)
                        # Botón de color
                        color_button = QPushButton()
                        color_button.setStyleSheet(f"background-color: {umbral[4]};")
                        color_button.clicked.connect(lambda *args, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
                        table.setCellWidget(row, 1, color_button)
                        # Riesgo
                        riesgo_item = QTableWidgetItem(umbral[5])  # Asumiendo que el riesgo
                        table.setItem(row, 2, riesgo_item)
                        # Distancia (DoubleSpinBox)
                        distancia_spinbox = QDoubleSpinBox()
                        distancia_spinbox.setRange(0, 1e9)  # Rango grande
                        distancia_spinbox.setDecimals(5)  # Hasta 5 decimales
                        distancia_spinbox.setValue(umbral[6])
                        table.setCellWidget(row, 3, distancia_spinbox)
                        # Magnitud (DoubleSpinBox)
                        magnitud_spinbox = QDoubleSpinBox()
                        magnitud_spinbox.setRange(0, 1e9)  # Rango grande
                        magnitud_spinbox.setDecimals(5)  # Hasta 5 decimales
                        magnitud_spinbox.setValue(umbral[7])  
                        table.setCellWidget(row, 4, magnitud_spinbox)
                        # Acciones a Realizar
                        acciones_item = QTableWidgetItem(umbral[8]) 
                        table.setItem(row, 5, acciones_item)
                else:
                    for row, umbral in enumerate(umbrales):
                        # Condición
                        condicion_item = QTableWidgetItem(umbral[3])  # Asumiendo que la condición está en la posición 3
                        condicion_item.setData(Qt.UserRole, umbral[0])  # Guardar el ID del umbral en el item
                        table.setItem(row, 0, condicion_item)
                        # Botón de color
                        color_button = QPushButton()
                        color_button.setStyleSheet(f"background-color: {umbral[4]};")  # Asumiendo que el color está en la posición 4
                        color_button.clicked.connect(lambda *args, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
                        table.setCellWidget(row, 1, color_button)
                        # Riesgo
                        riesgo_item = QTableWidgetItem(umbral[5])  # Asumiendo que el riesgo está en la posición 5
                        table.setItem(row, 2, riesgo_item)
                        # Rango (DoubleSpinBox)
                        double_spinbox = QDoubleSpinBox()
                        double_spinbox.setRange(-1e9, 1e9)  # Rango grande
                        double_spinbox.setDecimals(5)  # Hasta 5 decimales
                        double_spinbox.setValue(umbral[6]) # Asumiendo que el rango está en la posición 6
                        table.setCellWidget(row, 3, double_spinbox)
                        # Acciones a realizar
                        acciones_item = QTableWidgetItem(umbral[8])  # Asumiendo que las acciones están en la posición 8
                        table.setItem(row, 4, acciones_item)
            else:
                reset_table()

        # Conectar el cambio de opción en el ComboBox para cargar los umbrales
        combo.currentIndexChanged.connect(load_umbrales)
        component_combo.currentIndexChanged.connect(load_umbrales)
        acelerografo_combo.currentIndexChanged.connect(load_umbrales)
        # Configurar las columnas iniciales
        load_umbrales()

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
            nonlocal table
            row_count = table.rowCount()
            table.insertRow(row_count)
            selected_option = combo.currentText()
            tipografica = options[selected_option]
            if tipografica == "AMA":
                # Nombre
                nombre_item = QTableWidgetItem("")
                table.setItem(row_count, 0, nombre_item)
                # Color
                color_button = QPushButton()
                color_button.clicked.connect(lambda *args, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
                table.setCellWidget(row_count, 1, color_button)
                # Riesgo
                riesgo_item = QTableWidgetItem("")
                table.setItem(row_count, 2, riesgo_item)
                # Distancia
                distancia = QDoubleSpinBox()
                distancia.setRange(0, 1e9)
                distancia.setDecimals(5)
                table.setCellWidget(row_count, 3, distancia)
                # Magnitud
                magnitud = QDoubleSpinBox()
                magnitud.setRange(0, 1e9)
                magnitud.setDecimals(5)
                table.setCellWidget(row_count, 4, magnitud)
                # Acciones
                acciones_item = QTableWidgetItem("")
                table.setItem(row_count, 5, acciones_item)
            else:
                # Condición
                condicion_item = QTableWidgetItem("")
                table.setItem(row_count, 0, condicion_item)
                # Color
                color_button = QPushButton()
                color_button.clicked.connect(lambda *args, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
                table.setCellWidget(row_count, 1, color_button)
                # Riesgo
                riesgo_item = QTableWidgetItem("")
                table.setItem(row_count, 2, riesgo_item)
                # Rango
                double_spinbox = QDoubleSpinBox()
                double_spinbox.setRange(-1e9, 1e9)
                double_spinbox.setDecimals(5)
                table.setCellWidget(row_count, 3, double_spinbox)
                # Acciones
                acciones_item = QTableWidgetItem("")
                table.setItem(row_count, 4, acciones_item)
        # Conectar el botón a la función para agregar una nueva fila
        add_button.clicked.connect(add_row)

        # Función para manejar el evento de confirmar
        def confirm():
            nonlocal table
            selected_option = combo.currentText()
            tipografica = options[selected_option]
            if not acelerografo_combo.currentData():
                mostrar_mensaje("Advertencia", "Debe seleccionar un acelerógrafo.", 'advertencia')
                return
            acelerografo_id = acelerografo_combo.currentData()
            data = []
            if tipografica == "AMA":
                for row in range(table.rowCount()):
                    nombre_item = table.item(row, 0)
                    distancia_item = table.cellWidget(row, 3)
                    magnitud_item = table.cellWidget(row, 4)
                    riesgo_item = table.item(row, 2)
                    acciones_item = table.item(row, 5)
                    if nombre_item and nombre_item.text() and distancia_item and magnitud_item and riesgo_item and acciones_item:
                        color_button = table.cellWidget(row, 1)
                        color = color_button.palette().button().color().name()
                        data.append({
                            "id": table.item(row, 0).data(Qt.UserRole) if table.item(row, 0) else None,  # Obtener el ID del umbral si existe
                            "nombre": nombre_item.text(),
                            "riesgo": riesgo_item.text(),
                            "color": color,
                            "distancia": distancia_item.value(),
                            "magnitud": magnitud_item.value(),
                            "acciones": acciones_item.text(),
                            "tipo": "AMA"
                        })
                # Guardar los datos en la base de datos
                success = UmbralController.ctrlGuardarUmbralesPersonalizadosAcelerografos(proyectoid, acelerografo_id, tipografica, data, tipo)
            else:
                for row in range(table.rowCount()):
                    condicion_item = table.item(row, 0)
                    rango_item = table.cellWidget(row, 3)
                    riesgo_item = table.item(row, 2)
                    acciones_item = table.item(row, 4)
                    if condicion_item and condicion_item.text() and rango_item and rango_item.value():
                        color_button = table.cellWidget(row, 1)
                        color = color_button.palette().button().color().name()
                        valorrango = float(rango_item.value())
                        data.append({
                            "id": table.item(row, 0).data(Qt.UserRole) if table.item(row, 0) else None,  # Obtener el ID del umbral si existe
                            "condicion": condicion_item.text(),
                            "color": color,
                            "riesgo": riesgo_item.text(),
                            "rango": valorrango,
                            "acciones": acciones_item.text()
                        })
                # Guardar los datos en la base de datos
                success = UmbralController.ctrlGuardarUmbralesPersonalizados(proyectoid, acelerografo_id, tipografica, data, tipo)
            if success:
                mostrar_mensaje("Guardado", "Se guardó el umbral.", 'informacion')
                load_umbrales()
            else:
                mostrar_mensaje("Error", "Error al guardar umbral", 'error')
        # Conectar el botón Confirmar a la función confirm
        confirm_button.clicked.connect(confirm)

        # Función para eliminar una fila
        def delete_row(position):
            nonlocal table
            item = table.itemAt(position)
            if item:
                row = item.row()
                condicion_item = table.item(row, 0)
                if condicion_item:
                    umbral_id = condicion_item.data(Qt.UserRole)
                    if umbral_id and umbral_id != 0:
                        # Llamar a la base de datos para eliminar el registro
                        success = UmbralController.ctrlEliminarUmbralPersonalizados(umbral_id)
                        if success:
                            print(f"Registro con ID {umbral_id} eliminado exitosamente.")
                        else:
                            mostrar_mensaje("Error", f"Error al eliminar el registro con ID {umbral_id}.", 'error')
                            return
                # Eliminar la fila de la tabla
                table.removeRow(row)
                # Recargar los datos de la tabla
                load_umbrales()

        # Calcular el ancho total de las columnas
        total_width = sum(table.columnWidth(col) for col in range(table.columnCount()))
        # Ajustar el tamaño del diálogo al contenido
        dialog.adjustSize()
        # Establecer el ancho inicial del diálogo basado en el ancho total de las columnas
        dialog.resize(total_width + 60, dialog.height())  # Añadir un margen adicional si es necesario
        # Mostrar el diálogo
        dialog.exec()

    def modalUmbralesPersonalizadosCeldas(proyectoid, tipo, unidadmedida, tipovelocidad):
        unidad = unidadmedida
        # Añadir opciones al nuevo ComboBox desde listacomponente
        listacomponente = InterfazController.ctrlListarComponentesProyecto(proyectoid)
        titulo_combo = "Seleccione Componente:"
        # Crear el diálogo
        dialog = QDialog()
        dialog.setWindowTitle("Umbrales Personalizados - Celdas")
        # Layout principal
        main_layout = QVBoxLayout()
        # Nuevo ComboBox al inicio
        component_combo_label = QLabel(titulo_combo)
        component_combo = QComboBox()
        if listacomponente:
            component_combo.addItem("TODOS", userData=0)
            for componente in listacomponente:
                component_combo.addItem(componente[2], userData=componente[0])
            component_combo.setCurrentIndex(0)
        main_layout.addWidget(component_combo_label)
        main_layout.addWidget(component_combo)

        celda_combo_label = QLabel("Seleccione Celda:")
        celda_combo = QComboBox()
        main_layout.addWidget(celda_combo_label)
        main_layout.addWidget(celda_combo)

        def cargar_celdas():
            componente_id = component_combo.currentData()
            celda_combo.clear()
            instrumentos = UmbralController.ctrlListarInstrumentosComponente(proyectoid, componente_id, tipo)
            if instrumentos:
                for id_equipo, nombre_equipo, tipo_equipo in instrumentos:
                    celda_combo.addItem(nombre_equipo, userData=id_equipo)
            else:
                celda_combo.addItem("Sin celdas registradas", userData=None)

        component_combo.currentIndexChanged.connect(cargar_celdas)
        cargar_celdas()
        # Layout para el ComboBox y el botón
        combo_layout = QHBoxLayout()
        # ComboBox
        combo_label = QLabel("Seleccione Umbral:")
        combo = QComboBox()
        options = UmbralView.retornarArregloTipo(tipo)
        # Añadir opciones al ComboBox
        combo.addItems(options.keys())
        # Botón al lado del ComboBox
        add_button = QPushButton("Agregar Fila")
        # Añadir ComboBox y botón al layout horizontal
        combo_layout.addWidget(combo_label)
        combo_layout.addWidget(combo)
        combo_layout.addWidget(add_button)
        # Añadir el layout horizontal al layout principal
        main_layout.addLayout(combo_layout)
        # Tabla
        table = QTableWidget(3, 5)  # 3 filas y 5 columnas
        # table.setHorizontalHeaderLabels(["Condición", "Color", "Riesgo", f"Rango ({medida})", "Acciones a realizar"])
        # Función para reiniciar la tabla
        def reset_table():
            nonlocal unidad
            selected_option = combo.currentText()
            vista = options[selected_option]  # Obtener el ID correspondiente del tipo
            if vista == "VI":
                if tipovelocidad == "Por Mes":
                    if unidad == 1:
                        medida = "m/mes"
                    elif unidad == 100:
                        medida = "cm/mes"
                    else:
                        medida = "mm/mes"
                else:
                    if unidad == 1:
                        medida = "m/d"
                    elif unidad == 100:
                        medida = "cm/d"
                    else:
                        medida = "mm/d"
            elif vista == "AC":
                medida = "msnm"
            elif vista == "AI" or vista == "AA":
                if unidad == 1:
                    medida = "m"
                elif unidad == 100:
                    medida = "cm"
                else:
                    medida = "mm"
            elif vista == "AF":
                medida = "Hz"
            else: # AT
                medida = "°C"
            table.setHorizontalHeaderLabels(["Condición", "Color", "Riesgo", f"Rango ({medida})", "Acciones a realizar"])
            table.setRowCount(3)
            for row in range(3):
                # Condición
                condicion_item = QTableWidgetItem("")
                table.setItem(row, 0, condicion_item)
                # Botón de color
                color_button = QPushButton()
                color_button.clicked.connect(lambda *args, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
                table.setCellWidget(row, 1, color_button)
                # Riesgo
                riesgo_item = QTableWidgetItem("")
                table.setItem(row, 2, riesgo_item)
                # Rango (DoubleSpinBox)
                double_spinbox = QDoubleSpinBox()
                double_spinbox.setRange(-1e9, 1e9)  # Rango grande
                double_spinbox.setDecimals(5)  # Hasta 5 decimales
                table.setCellWidget(row, 3, double_spinbox)
                # Acciones a realizar
                acciones_item = QTableWidgetItem("")
                table.setItem(row, 4, acciones_item)
        def load_umbrales():
            nonlocal unidad
            selected_option = combo.currentText()
            selected_id = options[selected_option]  # Obtener el ID correspondiente del tipo
            selected_equipo_id = celda_combo.currentData()  # Obtener el ID de la celda seleccionada
            if selected_id == "VI":
                if tipovelocidad == "Por Mes":
                    if unidad == 1:
                        medida = "m/mes"
                        unimedida = 1
                    elif unidad == 100:
                        medida = "cm/mes"
                        unimedida = 100
                    else:
                        medida = "mm/mes"
                        unimedida = 1000
                else:
                    if unidad == 1:
                        medida = "m/d"
                        unimedida = 1
                    elif unidad == 100:
                        medida = "cm/d"
                        unimedida = 100
                    else:
                        medida = "mm/d"
                        unimedida = 1000
            elif selected_id == "AC":
                medida = "msnm"
                unimedida = 1
            elif selected_id == "AI" or selected_id == "AA":
                if unidad == 1:
                    medida = "m"
                    unimedida = 1
                elif unidad == 100:
                    medida = "cm"
                    unimedida = 100
                else:
                    medida = "mm"
                    unimedida = 1000
            elif selected_id == "AF":
                medida = "Hz"
                unimedida = 1
            else: # AT
                medida = "°C"
                unimedida = 1
            umbrales = UmbralController.ctrlObtenerUmbralesPersonalizados(selected_equipo_id, selected_id, tipo)
            if umbrales:
                table.setHorizontalHeaderLabels(["Condición", "Color", "Riesgo", f"Rango ({medida})", "Acciones a realizar"])
                table.setRowCount(len(umbrales))
                for row, umbral in enumerate(umbrales):
                    # Condición
                    condicion_item = QTableWidgetItem(umbral[3])  # Asumiendo que la condición está en la posición 3
                    condicion_item.setData(Qt.UserRole, umbral[0])  # Guardar el ID del umbral en el item
                    table.setItem(row, 0, condicion_item)
                    # Botón de color
                    color_button = QPushButton()
                    color_button.setStyleSheet(f"background-color: {umbral[4]};")  # Asumiendo que el color está en la posición 4
                    color_button.clicked.connect(lambda *args, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
                    table.setCellWidget(row, 1, color_button)
                    # Riesgo
                    riesgo_item = QTableWidgetItem(umbral[5])  # Asumiendo que el riesgo está en la posición 5
                    table.setItem(row, 2, riesgo_item)
                    # Rango (DoubleSpinBox)
                    double_spinbox = QDoubleSpinBox()
                    double_spinbox.setRange(-1e9, 1e9)  # Rango grande
                    double_spinbox.setDecimals(5)  # Hasta 5 decimales
                    double_spinbox.setValue(umbral[6] * unimedida) # Asumiendo que el rango está en la posición 6
                    table.setCellWidget(row, 3, double_spinbox)
                    # Acciones a realizar
                    acciones_item = QTableWidgetItem(umbral[8])  # Asumiendo que las acciones están en la posición 8
                    table.setItem(row, 4, acciones_item)
            else:
                reset_table()
        # Conectar el cambio de opción en el ComboBox para cargar los umbrales
        combo.currentIndexChanged.connect(load_umbrales)
        component_combo.currentIndexChanged.connect(load_umbrales)
        celda_combo.currentIndexChanged.connect(load_umbrales)
        # Configurar las columnas iniciales
        load_umbrales()
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
            # Condición
            condicion_item = QTableWidgetItem("")
            table.setItem(row_count, 0, condicion_item)
            # Botón de color
            color_button = QPushButton()
            color_button.clicked.connect(lambda *args, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
            table.setCellWidget(row_count, 1, color_button)
            # Riesgo
            riesgo_item = QTableWidgetItem("")
            table.setItem(row_count, 2, riesgo_item)
            # Rango (DoubleSpinBox)
            double_spinbox = QDoubleSpinBox()
            double_spinbox.setRange(-1e9, 1e9)  # Rango grande
            double_spinbox.setDecimals(5)  # Hasta 5 decimales
            table.setCellWidget(row_count, 3, double_spinbox)
            # Acciones a realizar
            acciones_item = QTableWidgetItem("")
            table.setItem(row_count, 4, acciones_item)
        # Conectar el botón a la función para agregar una nueva fila
        add_button.clicked.connect(add_row)
        # Función para manejar el evento de confirmar
        def confirm():
            nonlocal unidad
            selected_option = combo.currentText()
            selected_id = options[selected_option]  # Obtener el ID correspondiente
            if not celda_combo.currentData():
                mostrar_mensaje("Advertencia", "Debe seleccionar una celda.", 'advertencia')
                return
            celda_id = celda_combo.currentData()
            if selected_id == "VI":
                if tipovelocidad == "Por Mes":
                    if unidad == 1:
                        unimedida = 1
                    elif unidad == 100:
                        unimedida = 100
                    else:
                        unimedida = 1000
                else:
                    if unidad == 1:
                        unimedida = 1
                    elif unidad == 100:
                        unimedida = 100
                    else:
                        unimedida = 1000
            elif selected_id == "AC":
                unimedida = 1
            elif selected_id == "AI" or selected_id == "AA":
                if unidad == 1:
                    unimedida = 1
                elif unidad == 100:
                    unimedida = 100
                else:
                    unimedida = 1000
            elif selected_id == "AF":
                unimedida = 1
            else: # AT
                unimedida = 1
            data = []
            for row in range(table.rowCount()):
                condicion_item = table.item(row, 0)
                rango_item = table.cellWidget(row, 3)
                riesgo_item = table.item(row, 2)
                acciones_item = table.item(row, 4)
                if condicion_item and condicion_item.text() and rango_item and rango_item.value():
                    color_button = table.cellWidget(row, 1)
                    color = color_button.palette().button().color().name()
                    valorrango = float(rango_item.value()) / unimedida
                    data.append({
                        "id": table.item(row, 0).data(Qt.UserRole) if table.item(row, 0) else None,  # Obtener el ID del umbral si existe
                        "condicion": condicion_item.text(),
                        "color": color,
                        "riesgo": riesgo_item.text(),
                        "rango": valorrango,
                        "acciones": acciones_item.text()
                    })
            # Guardar los datos en la base de datos
            success = UmbralController.ctrlGuardarUmbralesPersonalizados(proyectoid, celda_id, selected_id, data, tipo)
            if success:
                load_umbrales()
                mostrar_mensaje("Guardado", "Se guardó el umbral.", 'informacion')
            else:
                mostrar_mensaje("Error", "Error al guardar umbral", 'error')
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
                condicion_item = table.item(row, 0)
                if condicion_item:
                    umbral_id = condicion_item.data(Qt.UserRole)
                    if umbral_id and umbral_id != 0:
                        # Llamar a la base de datos para eliminar el registro
                        success = UmbralController.ctrlEliminarUmbralPersonalizados(umbral_id)
                        if success:
                            print(f"Registro con ID {umbral_id} eliminado exitosamente.")
                        else:
                            mostrar_mensaje("Error", f"Error al eliminar el registro con ID {umbral_id}.", 'error')
                            return
                # Eliminar la fila de la tabla
                table.removeRow(row)
                # Recargar los datos de la tabla
                load_umbrales()
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

    def modalUmbralesPersonalizadosTDR(proyectoid, tipo, unidad):
        # Crear el diálogo
        dialog = QDialog()
        dialog.setWindowTitle("Umbrales Personalizados - TDR")
        # Layout principal
        main_layout = QVBoxLayout()
        # Nuevo ComboBox al inicio
        component_combo_label = QLabel("Seleccione Componente:")
        component_combo = QComboBox()
        # Añadir opciones al nuevo ComboBox desde listacomponente
        listacomponente = InterfazController.ctrlListarComponentesProyecto(proyectoid)
        if listacomponente:
            component_combo.addItem("TODOS", userData=0)
            for componente in listacomponente:
                component_combo.addItem(componente[2], userData=componente[0])
            component_combo.setCurrentIndex(0)
        # Añadir el nuevo ComboBox al layout principal
        main_layout.addWidget(component_combo_label)
        main_layout.addWidget(component_combo)
        # Layout para el ComboBox y el botón
        combo_layout = QHBoxLayout()
        # ComboBox
        combo_label = QLabel("Seleccione Umbral:")
        combo_tipo = QComboBox()
        options = UmbralView.retornarArregloTipo(tipo)

        tdr_combo_label = QLabel("Seleccione TDR:")
        tdr_combo = QComboBox()
        main_layout.addWidget(tdr_combo_label)
        main_layout.addWidget(tdr_combo)

        def cargar_tdr():
            componente_id = component_combo.currentData()
            tdr_combo.clear()
            instrumentos = UmbralController.ctrlListarInstrumentosComponente(proyectoid, componente_id, tipo)
            if instrumentos:
                for id_equipo, nombre_equipo, tipo_equipo in instrumentos:
                    tdr_combo.addItem(nombre_equipo, userData=id_equipo)
            else:
                tdr_combo.addItem("Sin TDR registrados", userData=None)

        component_combo.currentIndexChanged.connect(cargar_tdr)
        cargar_tdr()

        # Añadir opciones al ComboBox
        combo_tipo.addItems(options.keys())
        # Botón al lado del ComboBox
        add_button = QPushButton("Agregar Fila")
        # Añadir ComboBox y botón al layout horizontal
        combo_layout.addWidget(combo_label)
        combo_layout.addWidget(combo_tipo)
        combo_layout.addWidget(add_button)
        # Añadir el layout horizontal al layout principal
        main_layout.addLayout(combo_layout)
        # Tabla
        table = QTableWidget(3, 5)  # 3 filas y 5 columnas
        # Función para reiniciar la tabla
        def reset_table():
            table.setHorizontalHeaderLabels(["Condición", "Color", "Riesgo", f"Rango (Ω)", "Acciones a realizar"])
            table.setRowCount(3)
            for row in range(3):
                # Condición
                condicion_item = QTableWidgetItem("")
                table.setItem(row, 0, condicion_item)
                # Botón de color
                color_button = QPushButton()
                color_button.clicked.connect(lambda *args, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
                table.setCellWidget(row, 1, color_button)
                # Riesgo
                riesgo_item = QTableWidgetItem("")
                table.setItem(row, 2, riesgo_item)
                # Rango (DoubleSpinBox)
                double_spinbox = QDoubleSpinBox()
                double_spinbox.setRange(-1e9, 1e9)  # Rango grande
                double_spinbox.setDecimals(5)  # Hasta 5 decimales
                table.setCellWidget(row, 3, double_spinbox)
                # Acciones a realizar
                acciones_item = QTableWidgetItem("")
                table.setItem(row, 4, acciones_item)
        def load_umbrales():
            selected_option = combo_tipo.currentText()
            selected_id = options[selected_option]  # Obtener el ID correspondiente
            tdr_id = tdr_combo.currentData()  # Obtener el ID del TDR seleccionado
            umbrales = UmbralController.ctrlObtenerUmbralesPersonalizados(tdr_id, selected_id, tipo)
            if umbrales:
                table.setHorizontalHeaderLabels(["Condición", "Color", "Riesgo", f"Rango (Ω)", "Acciones a realizar"])
                table.setRowCount(len(umbrales))
                for row, umbral in enumerate(umbrales):
                    # Condición
                    condicion_item = QTableWidgetItem(umbral[3])
                    condicion_item.setData(Qt.UserRole, umbral[0])
                    table.setItem(row, 0, condicion_item)
                    # Botón de color
                    color_button = QPushButton()
                    color_button.setStyleSheet(f"background-color: {umbral[4]};")
                    color_button.clicked.connect(lambda *args, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
                    table.setCellWidget(row, 1, color_button)
                    # Riesgo
                    riesgo_item = QTableWidgetItem(umbral[5])
                    table.setItem(row, 2, riesgo_item)
                    # Rango (DoubleSpinBox)
                    double_spinbox = QDoubleSpinBox()
                    double_spinbox.setRange(-1e9, 1e9)
                    double_spinbox.setDecimals(5)
                    double_spinbox.setValue(umbral[6] * unidad)
                    table.setCellWidget(row, 3, double_spinbox)
                    # Acciones a realizar
                    acciones_item = QTableWidgetItem(umbral[8])
                    table.setItem(row, 4, acciones_item)
            else:
                reset_table()
        # Conectar el cambio de opción en el ComboBox para cargar los umbrales
        combo_tipo.currentIndexChanged.connect(load_umbrales)
        component_combo.currentIndexChanged.connect(load_umbrales)
        tdr_combo.currentIndexChanged.connect(load_umbrales)
        # Configurar las columnas iniciales
        load_umbrales()
        # Añadir la tabla al layout
        main_layout.addWidget(table)
        # Layout para el botón Confirmar y el espacer
        confirm_layout = QHBoxLayout()
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        confirm_layout.addSpacerItem(spacer)
        confirm_button = QPushButton("Confirmar")
        confirm_layout.addWidget(confirm_button)
        main_layout.addLayout(confirm_layout)
        dialog.setLayout(main_layout)
        # Función para agregar una nueva fila
        def add_row():
            row_count = table.rowCount()
            table.insertRow(row_count)
            condicion_item = QTableWidgetItem("")
            table.setItem(row_count, 0, condicion_item)
            color_button = QPushButton()
            color_button.clicked.connect(lambda *args, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
            table.setCellWidget(row_count, 1, color_button)
            riesgo_item = QTableWidgetItem("")
            table.setItem(row_count, 2, riesgo_item)
            double_spinbox = QDoubleSpinBox()
            double_spinbox.setRange(-1e9, 1e9)
            double_spinbox.setDecimals(5)
            table.setCellWidget(row_count, 3, double_spinbox)
            acciones_item = QTableWidgetItem("")
            table.setItem(row_count, 4, acciones_item)
        add_button.clicked.connect(add_row)
        # Función para manejar el evento de confirmar
        def confirm():
            selected_option = combo_tipo.currentText()
            selected_id = options[selected_option]
            if not tdr_combo.currentData():
                mostrar_mensaje("Advertencia", "Debe seleccionar un TDR.", 'advertencia')
                return
            tdr_id = tdr_combo.currentData()
            data = []
            for row in range(table.rowCount()):
                condicion_item = table.item(row, 0)
                rango_item = table.cellWidget(row, 3)
                riesgo_item = table.item(row, 2)
                acciones_item = table.item(row, 4)
                if condicion_item and condicion_item.text() and rango_item and rango_item.value():
                    color_button = table.cellWidget(row, 1)
                    color = color_button.palette().button().color().name()
                    valorrango = float(rango_item.value()) / unidad
                    data.append({
                        "id": table.item(row, 0).data(Qt.UserRole) if table.item(row, 0) else None,
                        "condicion": condicion_item.text(),
                        "color": color,
                        "riesgo": riesgo_item.text(),
                        "rango": valorrango,
                        "acciones": acciones_item.text()
                    })
            success = UmbralController.ctrlGuardarUmbralesPersonalizados(proyectoid, tdr_id, selected_id, data, tipo)
            if success:
                load_umbrales()
                mostrar_mensaje("Guardado", "Se guardó el umbral.", 'informacion')
            else:
                mostrar_mensaje("Error", "Error al guardar umbral", 'error')
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
                condicion_item = table.item(row, 0)
                if condicion_item:
                    umbral_id = condicion_item.data(Qt.UserRole)
                    if umbral_id and umbral_id != 0:
                        success = UmbralController.ctrlEliminarUmbralPersonalizados(umbral_id)
                        if success:
                            print(f"Registro con ID {umbral_id} eliminado exitosamente.")
                        else:
                            mostrar_mensaje("Error", f"Error al eliminar el registro con ID {umbral_id}.", 'error')
                            return
                table.removeRow(row)
                load_umbrales()
        table.setContextMenuPolicy(Qt.CustomContextMenu)
        table.customContextMenuRequested.connect(show_context_menu)
        total_width = sum(table.columnWidth(col) for col in range(table.columnCount()))
        dialog.adjustSize()
        dialog.resize(total_width + 50, dialog.height())
        dialog.exec()

    def modalUmbralesPersonalizadosPiezometros(proyectoid, tipo, unidadmedida):
        unidad = unidadmedida
        tipotitulo = "Cuerda Vibrante" if tipo == "PIEZOMETROCUERDA" else "Casagrande"
        # Añadir opciones al nuevo ComboBox desde listacomponente
        listacomponente = InterfazController.ctrlListarComponentesProyecto(proyectoid)
        titulo_combo = "Seleccione Componente:"
        # Crear el diálogo
        dialog = QDialog()
        dialog.setWindowTitle(f"Umbrales Personalizados - Piezómetros {tipotitulo}")
        # Layout principal
        main_layout = QVBoxLayout()
        # Nuevo ComboBox al inicio
        component_combo_label = QLabel(titulo_combo)
        component_combo = QComboBox()
        if listacomponente:
            component_combo.addItem("TODOS", userData=0)
            for componente in listacomponente:
                component_combo.addItem(componente[2], userData=componente[0])
            component_combo.setCurrentIndex(0)
        # Añadir el nuevo ComboBox al layout principal
        main_layout.addWidget(component_combo_label)
        main_layout.addWidget(component_combo)

        # Combo de Piezómetro, filtrado por componente
        piezometro_combo_label = QLabel("Seleccione Piezómetro:")
        piezometro_combo = QComboBox()
        main_layout.addWidget(piezometro_combo_label)
        main_layout.addWidget(piezometro_combo)

        def cargar_piezometros():
            componente_id = component_combo.currentData()
            piezometro_combo.clear()
            instrumentos = UmbralController.ctrlListarInstrumentosComponente(proyectoid, componente_id, tipo)
            if instrumentos:
                for id_equipo, nombre_equipo, tipo_equipo in instrumentos:
                    piezometro_combo.addItem(nombre_equipo, userData=id_equipo)
            else:
                piezometro_combo.addItem("Sin piezómetros registrados", userData=None)

        component_combo.currentIndexChanged.connect(cargar_piezometros)
        cargar_piezometros()  # carga inicial
    
        # Layout para el ComboBox y el botón
        combo_layout = QHBoxLayout()
        # ComboBox
        combo_label = QLabel("Seleccione Umbral:")
        combo = QComboBox()
        options = UmbralView.retornarArregloTipo(tipo)
        # Añadir opciones al ComboBox
        combo.addItems(options.keys())
        # Botón al lado del ComboBox
        add_button = QPushButton("Agregar Fila")
        # Añadir ComboBox y botón al layout horizontal
        combo_layout.addWidget(combo_label)
        combo_layout.addWidget(combo)
        combo_layout.addWidget(add_button)
        # Añadir el layout horizontal al layout principal
        main_layout.addLayout(combo_layout)
        # Tabla
        table = QTableWidget(3, 5)  # 3 filas y 5 columnas
        # table.setHorizontalHeaderLabels(["Condición", "Color", "Riesgo", f"Rango ({medida})", "Acciones a realizar"])
        # Función para reiniciar la tabla
        def reset_table():
            nonlocal unidad
            selected_option = combo.currentText()
            vista = options[selected_option]  # Obtener el ID correspondiente del tipo
            if vista == "NF":
                medida = "msnm"
            elif vista == "NI" or vista == "NA":
                if unidad == 1:
                    medida = "m"
                elif unidad == 100:
                    medida = "cm"
                else:
                    medida = "mm"
            elif vista == "PB":
                medida = "B"
            elif vista == "FP":
                medida = "Hz"
            else:
                medida = "°C"
            table.setHorizontalHeaderLabels(["Condición", "Color", "Riesgo", f"Rango ({medida})", "Acciones a realizar"])
            table.setRowCount(3)
            for row in range(3):
                # Condición
                condicion_item = QTableWidgetItem("")
                table.setItem(row, 0, condicion_item)
                # Botón de color
                color_button = QPushButton()
                color_button.clicked.connect(lambda *args, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
                table.setCellWidget(row, 1, color_button)
                # Riesgo
                riesgo_item = QTableWidgetItem("")
                table.setItem(row, 2, riesgo_item)
                # Rango (DoubleSpinBox)
                double_spinbox = QDoubleSpinBox()
                double_spinbox.setRange(-1e9, 1e9)  # Rango grande
                double_spinbox.setDecimals(5)  # Hasta 5 decimales
                table.setCellWidget(row, 3, double_spinbox)
                # Acciones a realizar
                acciones_item = QTableWidgetItem("")
                table.setItem(row, 4, acciones_item)
        def load_umbrales():
            nonlocal unidad
            selected_option = combo.currentText()
            selected_id = options[selected_option]  # Obtener el ID correspondiente del tipo
            piezometro_id = piezometro_combo.currentData()  # Obtener el ID del piezómetro seleccionado
            if piezometro_id:
                if selected_id == "NF":
                    unimedida = 1
                    medida = "msnm"
                elif selected_id == "NI" or selected_id == "NA":
                    if unidad == 1:
                        unimedida = 1
                        medida = "m"
                    elif unidad == 100:
                        unimedida = 100
                        medida = "cm"
                    else:
                        unimedida = 1000
                        medida = "mm"
                elif selected_id == "PB":
                    unimedida = 1
                    medida = "B"
                elif selected_id == "FP":
                    unimedida = 1
                    medida = "Hz"
                else:
                    unimedida = 1
                    medida = "°C"
                umbrales = UmbralController.ctrlObtenerUmbralesPersonalizados(piezometro_id, selected_id, tipo)
                if umbrales:
                    table.setHorizontalHeaderLabels(["Condición", "Color", "Riesgo", f"Rango ({medida})", "Acciones a realizar"])
                    table.setRowCount(len(umbrales))
                    for row, umbral in enumerate(umbrales):
                        # Condición
                        condicion_item = QTableWidgetItem(umbral[3])  # Asumiendo que la condición está en la posición 2
                        condicion_item.setData(Qt.UserRole, umbral[0])  # Guardar el ID del umbral en el item
                        table.setItem(row, 0, condicion_item)
                        # Botón de color
                        color_button = QPushButton()
                        color_button.setStyleSheet(f"background-color: {umbral[4]};")  # Asumiendo que el color está en la posición 3
                        color_button.clicked.connect(lambda *args, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
                        table.setCellWidget(row, 1, color_button)
                        # Riesgo
                        riesgo_item = QTableWidgetItem(umbral[5])  # Asumiendo que el riesgo está en la posición 4
                        table.setItem(row, 2, riesgo_item)
                        # Rango (DoubleSpinBox)
                        double_spinbox = QDoubleSpinBox()
                        double_spinbox.setRange(-1e9, 1e9)  # Rango grande
                        double_spinbox.setDecimals(5)  # Hasta 5 decimales
                        double_spinbox.setValue(umbral[6] * unimedida) # Asumiendo que el rango está en la posición 5
                        table.setCellWidget(row, 3, double_spinbox)
                        # Acciones a realizar
                        acciones_item = QTableWidgetItem(umbral[8])  # Asumiendo que las acciones están en la posición 6
                        table.setItem(row, 4, acciones_item)
                else:
                    reset_table()
            else:
                reset_table()
        # Conectar el cambio de opción en el ComboBox para cargar los umbrales
        combo.currentIndexChanged.connect(load_umbrales)
        component_combo.currentIndexChanged.connect(load_umbrales)
        # piezometro_combo.currentIndexChanged.connect(load_umbrales)
        # Configurar las columnas iniciales
        load_umbrales()
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
            # Condición
            condicion_item = QTableWidgetItem("")
            table.setItem(row_count, 0, condicion_item)
            # Botón de color
            color_button = QPushButton()
            color_button.clicked.connect(lambda *args, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
            table.setCellWidget(row_count, 1, color_button)
            # Riesgo
            riesgo_item = QTableWidgetItem("")
            table.setItem(row_count, 2, riesgo_item)
            # Rango (DoubleSpinBox)
            double_spinbox = QDoubleSpinBox()
            double_spinbox.setRange(-1e9, 1e9)  # Rango grande
            double_spinbox.setDecimals(5)  # Hasta 5 decimales
            table.setCellWidget(row_count, 3, double_spinbox)
            # Acciones a realizar
            acciones_item = QTableWidgetItem("")
            table.setItem(row_count, 4, acciones_item)
        # Conectar el botón a la función para agregar una nueva fila
        add_button.clicked.connect(add_row)
        # Función para manejar el evento de confirmar
        def confirm():
            nonlocal unidad
            selected_option = combo.currentText()
            selected_id = options[selected_option]  # Obtener el ID correspondiente
            if not piezometro_combo.currentData():
                mostrar_mensaje("Advertencia", "Debe seleccionar un piezómetro.", 'advertencia')
                return
            piezometro_id = piezometro_combo.currentData()  # Obtener el ID del piezómetro seleccionado
            if selected_id == "NF":
                unimedida = 1
            elif selected_id == "NI" or selected_id == "NA":
                if unidad == 1:
                    unimedida = 1
                elif unidad == 100:
                    unimedida = 100
                else:
                    unimedida = 1000
            elif selected_id == "PB":
                unimedida = 1
            elif selected_id == "FP":
                unimedida = 1
            else:
                unimedida = 1
            data = []
            for row in range(table.rowCount()):
                condicion_item = table.item(row, 0)
                rango_item = table.cellWidget(row, 3)
                riesgo_item = table.item(row, 2)
                acciones_item = table.item(row, 4)
                if condicion_item and condicion_item.text() and rango_item and rango_item.value():
                    color_button = table.cellWidget(row, 1)
                    color = color_button.palette().button().color().name()
                    valorrango = float(rango_item.value()) / unimedida
                    data.append({
                        "id": table.item(row, 0).data(Qt.UserRole) if table.item(row, 0) else None,  # Obtener el ID del umbral si existe
                        "condicion": condicion_item.text(),
                        "color": color,
                        "riesgo": riesgo_item.text(),
                        "rango": valorrango,
                        "acciones": acciones_item.text()
                    })
            # Guardar los datos en la base de datos
            success = UmbralController.ctrlGuardarUmbralesPersonalizados(proyectoid, piezometro_id, selected_id, data, tipo)
            if success:
                load_umbrales()
                mostrar_mensaje("Guardado", "Se guardó el umbral.", 'informacion')
            else:
                mostrar_mensaje("Error", "Error al guardar umbral", 'error')
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
                condicion_item = table.item(row, 0)
                if condicion_item:
                    umbral_id = condicion_item.data(Qt.UserRole)
                    if umbral_id and umbral_id != 0:
                        # Llamar a la base de datos para eliminar el registro
                        success = UmbralController.ctrlEliminarUmbralPersonalizados(umbral_id)
                        if success:
                            print(f"Registro con ID {umbral_id} eliminado exitosamente.")
                        else:
                            mostrar_mensaje("Error", f"Error al eliminar el registro con ID {umbral_id}.", 'error')
                            return
                # Eliminar la fila de la tabla
                table.removeRow(row)
                # Recargar los datos de la tabla
                load_umbrales()
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
    