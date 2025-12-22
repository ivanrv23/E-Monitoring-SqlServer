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
            
    def modalUmbralesPersonalizado(proyectoid):
        # Crear el diálogo
        dialog = QDialog()
        dialog.setWindowTitle("Configuración de Umbrales Personalizados")
        dialog.setMinimumWidth(800)
        
        # Layout principal
        main_layout = QVBoxLayout()
        
        # Variables de estado
        modo_edicion = False
        umbral_seleccionado_nombre = None
        nombre_original = None
        
        # Widget para la sección de selección (oculto inicialmente)
        seleccion_widget = QWidget()
        seleccion_layout = QHBoxLayout(seleccion_widget)
        seleccion_label = QLabel("Seleccionar umbral para editar:")
        umbrales_combo = QComboBox()
        seleccion_layout.addWidget(seleccion_label)
        seleccion_layout.addWidget(umbrales_combo)
        seleccion_widget.setVisible(False)
        main_layout.addWidget(seleccion_widget)
        
        # Sección de nombre y unidades de medida
        header_layout = QHBoxLayout()
        
        # Campo para el nombre (visible siempre)
        nombre_label = QLabel("Nombre:")
        nombre_input = QLineEdit()
        nombre_input.setPlaceholderText("Ingrese el nombre")
        header_layout.addWidget(nombre_label)
        header_layout.addWidget(nombre_input)
        
        # ComboBox para unidades de medida con factores de conversión
        unidades_label = QLabel("Unidad de medida:")
        unidades_combo = QComboBox()
        unidades_data = [
            {"text": "Metros (m)", "factor": 1.0},
            {"text": "Centímetros (cm)", "factor": 0.01},
            {"text": "Milímetros (mm)", "factor": 0.001},
        ]
        factores_conversion = {item["text"]: item["factor"] for item in unidades_data}
        
        for unidad in unidades_data:
            unidades_combo.addItem(unidad["text"], userData=unidad["factor"])
        header_layout.addWidget(unidades_label)
        header_layout.addWidget(unidades_combo)
        
        # Añadir el layout del encabezado al layout principal
        main_layout.addLayout(header_layout)
        
        # Crear la tabla con columna oculta para ID de fila
        table = QTableWidget(0, 6)  # 6 columnas: ID (oculto) + 5 visibles
        table.setHorizontalHeaderLabels(["ID", "Condición", "Color", "Riesgo", "Rango", "Acciones"])
        table.setColumnHidden(0, True)  # Ocultar columna ID
        
        # Función para inicializar filas de la tabla
        def init_table_row(row, condicion="", color="#FFFFFF", riesgo="", rango=0.0, acciones="", id_fila=None):
            # ID (oculto)
            id_item = QTableWidgetItem(str(id_fila) if id_fila else "")
            id_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            table.setItem(row, 0, id_item)
            
            # Condición
            condicion_item = QTableWidgetItem(condicion)
            table.setItem(row, 1, condicion_item)
            
            # Botón de color
            color_button = QPushButton("Color")
            if color:  # Solo establecer color si se proporciona
                color_button.setStyleSheet(f"background-color: {color};")
            color_button.clicked.connect(lambda _, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
            table.setCellWidget(row, 2, color_button)
            
            # Riesgo
            riesgo_item = QTableWidgetItem(riesgo)
            table.setItem(row, 3, riesgo_item)
            
            # Rango (DoubleSpinBox)
            double_spinbox = QDoubleSpinBox()
            double_spinbox.setRange(-1e9, 1e9)
            double_spinbox.setDecimals(5)
            double_spinbox.setValue(rango)
            table.setCellWidget(row, 4, double_spinbox)
            
            # Acciones
            acciones_item = QTableWidgetItem(acciones)
            table.setItem(row, 5, acciones_item)
        
        # Agregar 3 filas vacías por defecto
        for row in range(3):
            table.insertRow(row)
            init_table_row(row)
        
        # Botón para agregar filas
        add_button = QPushButton("Agregar Fila")
        add_button.clicked.connect(lambda: add_row())
        
        # Añadir la tabla y el botón al layout principal
        main_layout.addWidget(table)
        main_layout.addWidget(add_button)
        
        # Layout para los botones inferiores
        button_layout = QHBoxLayout()
        
        # Botón Editar (izquierda)
        editar_button = QPushButton("Editar")
        button_layout.addWidget(editar_button)
        
        # Botón Regresar a Registro (izquierda, oculto inicialmente)
        regresar_button = QPushButton("Regresar a Registro")
        regresar_button.setVisible(False)
        button_layout.addWidget(regresar_button)
        
        # Espaciador para alinear los botones a la derecha
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        button_layout.addSpacerItem(spacer)
        
        # Botón Eliminar (derecha, oculto inicialmente)
        eliminar_button = QPushButton("Eliminar")
        eliminar_button.setStyleSheet("background-color: #FF0000; color: white;")
        eliminar_button.setVisible(False)
        button_layout.addWidget(eliminar_button)
        
        # Botón Registrar/Actualizar
        registrar_button = QPushButton("Registrar")
        button_layout.addWidget(registrar_button)
        
        # Añadir el layout de botones al layout principal
        main_layout.addLayout(button_layout)
        
        # Función para agregar una nueva fila
        def add_row():
            row_count = table.rowCount()
            table.insertRow(row_count)
            init_table_row(row_count)
        
        # Función para limpiar y volver al modo registro
        def volver_a_modo_registro():
            nonlocal modo_edicion, umbral_seleccionado_nombre, nombre_original
            modo_edicion = False
            umbral_seleccionado_nombre = None
            nombre_original = None
            
            # Restablecer elementos de interfaz
            nombre_input.clear()
            seleccion_widget.setVisible(False)
            eliminar_button.setVisible(False)
            regresar_button.setVisible(False)
            
            # Restablecer botones
            registrar_button.setText("Registrar")
            editar_button.setEnabled(True)
            
            # Limpiar tabla y restablecer a 3 filas vacías
            while table.rowCount() > 0:
                table.removeRow(0)
            for row in range(3):
                table.insertRow(row)
                init_table_row(row)
            
            # Restablecer unidades a metros
            unidades_combo.setCurrentIndex(0)
        
        # Función para cambiar a modo edición
        def activar_modo_edicion():
            nonlocal modo_edicion, nombre_original
            modo_edicion = True
            nombre_original = None
            
            # Mostrar elementos de edición
            seleccion_widget.setVisible(True)
            eliminar_button.setVisible(True)
            regresar_button.setVisible(True)
            
            # Cambiar texto del botón
            registrar_button.setText("Actualizar")
            editar_button.setEnabled(False)
            
            # Cargar nombres únicos de umbrales existentes
            umbrales_combo.clear()
            nombres_umbrales = UmbralController.ctrlObtenerNombresUmbrales(proyectoid)
            
            if not nombres_umbrales:
                mostrar_mensaje("Información", "No hay umbrales registrados para este proyecto", 'informacion')
                volver_a_modo_registro()
                return
            
            for nombre in nombres_umbrales:
                umbrales_combo.addItem(nombre)
            
            # Seleccionar automáticamente el primer elemento si existe
            if nombres_umbrales:
                umbrales_combo.setCurrentIndex(0)
                cargar_umbral()  # Forzar carga del primer umbral
        
        # Función para cargar datos de un umbral
        def cargar_umbral():
            nonlocal umbral_seleccionado_nombre, nombre_original
            nombre_umbral = umbrales_combo.currentText()
            if not nombre_umbral:
                return
                
            umbral_seleccionado_nombre = nombre_umbral
            nombre_original = nombre_umbral  # Guardar nombre original para validación
            
            # Establecer el nombre en el input
            nombre_input.setText(nombre_umbral)
            
            # Limpiar tabla
            while table.rowCount() > 0:
                table.removeRow(0)
            
            # Obtener datos del umbral por nombre
            umbral = UmbralController.ctrlObtenerUmbralPorNombre(proyectoid, nombre_umbral)
            if umbral:
                # Obtener factor de conversión actual
                unidad_actual = unidades_combo.currentText()
                factor_conversion = factores_conversion.get(unidad_actual, 1.0)
                
                # Cargar filas (convertir metros a unidad seleccionada)
                for row, dato in enumerate(umbral.get('detalles', [])):
                    # Valor original está en metros
                    rango_metros = dato.get('rango_umbral', 0.0)
                    
                    # Convertir a la unidad seleccionada
                    rango_convertido = rango_metros / factor_conversion
                    
                    table.insertRow(row)
                    init_table_row(
                        row,
                        condicion=dato.get('condicion_umbral', ''),
                        color=dato.get('color_umbral', '#FFFFFF'),
                        riesgo=dato.get('riesgo_umbral', ''),
                        rango=rango_convertido,
                        acciones=dato.get('acciones_umbral', ''),
                        id_fila=dato.get('id_umbral')
                    )
        
        # Función para manejar cambio de unidad
        def unidad_cambiada():
            if modo_edicion and umbral_seleccionado_nombre:
                # Solo convertir si estamos en modo edición y hay un umbral cargado
                cargar_umbral()
        
        # Conectar cambio de unidad
        unidades_combo.currentIndexChanged.connect(unidad_cambiada)
        
        # Función para eliminar umbral seleccionado
        def eliminar_umbral():
            if not umbral_seleccionado_nombre:
                return
                
            confirm = QMessageBox.question(
                dialog, 
                "Confirmar Eliminación", 
                f"¿Está seguro que desea eliminar el umbral '{umbral_seleccionado_nombre}'?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if confirm == QMessageBox.Yes:
                if UmbralController.ctrlEliminarUmbralPorNombre(proyectoid, umbral_seleccionado_nombre):
                    mostrar_mensaje("Éxito", "Umbral eliminado correctamente", 'informacion')
                    # Recargar lista de umbrales
                    activar_modo_edicion()
                else:
                    mostrar_mensaje("Error", "No se pudo eliminar el umbral", 'error')
        
        # Función para validar nombre
        def validar_nombre(nombre, es_edicion=False):
            # Validar que el nombre no esté vacío
            if not nombre.strip():
                mostrar_mensaje("Advertencia", "Debe ingresar un nombre para el umbral.", 'advertencia')
                return False
            
            # Validar que no exista otro umbral con el mismo nombre
            if es_edicion:
                # En edición, permitimos mantener el mismo nombre
                if nombre == nombre_original:
                    return True
                    
            # Verificar si el nombre ya existe
            if UmbralController.ctrlExisteNombreUmbral(proyectoid, nombre, excluir=nombre_original if es_edicion else None):
                mostrar_mensaje("Advertencia", f"Ya existe un umbral con el nombre '{nombre}'. Por favor use otro nombre.", 'advertencia')
                return False
                
            return True
        # Función para manejar el registro/actualización
        def guardar_datos():
            nonlocal nombre_original
            
            # Obtener el nombre actual
            nombre_actual = nombre_input.text()
            
            # Validar el nombre
            if modo_edicion:
                if nombre_original is None:
                    mostrar_mensaje("Error", "Debe seleccionar un umbral para editar", 'error')
                    return
                
                if not validar_nombre(nombre_actual, True):
                    return
            else:
                if not validar_nombre(nombre_actual):
                    return
                
            unidad_seleccionada = unidades_combo.currentText()
            factor_conversion = factores_conversion.get(unidad_seleccionada, 1.0)
            
            # Recoger datos de la tabla
            datos_tabla = []
            for row in range(table.rowCount()):
                # Obtener ID de la fila si existe
                id_item = table.item(row, 0)
                id_fila = id_item.text() if id_item and id_item.text() else None
                
                condicion_item = table.item(row, 1)
                condicion = condicion_item.text() if condicion_item else ""
                
                color_button = table.cellWidget(row, 2)
                color = color_button.palette().button().color().name()
                
                riesgo_item = table.item(row, 3)
                riesgo = riesgo_item.text() if riesgo_item else ""
                
                rango_spinbox = table.cellWidget(row, 4)
                rango_original = rango_spinbox.value()
                rango_metros = rango_original * factor_conversion
                
                acciones_item = table.item(row, 5)
                acciones = acciones_item.text() if acciones_item else ""
                
                if condicion or riesgo or acciones or rango_original != 0:
                    datos_tabla.append({
                        "id_fila": id_fila,
                        "condicion": condicion,
                        "color": color,
                        "riesgo": riesgo,
                        "rango": rango_metros,
                        "acciones": acciones
                    })
            
            if not datos_tabla:
                mostrar_mensaje("Advertencia", "No hay datos válidos para guardar.", 'advertencia')
                return
            
            if modo_edicion:
                # Modo edición: actualizar umbral existente
                success = UmbralController.ctrlActualizarUmbral(
                    proyectoid,
                    nombre_original,
                    nombre_actual,
                    datos_tabla
                )
                if success:
                    mostrar_mensaje("Actualizado", "Umbral actualizado correctamente.", 'informacion')
                    if nombre_actual != nombre_original:
                        index = umbrales_combo.findText(nombre_original)
                        if index >= 0:
                            umbrales_combo.setItemText(index, nombre_actual)
                        umbral_seleccionado_nombre = nombre_actual
                        nombre_original = nombre_actual
                    
                    # Recargar los datos para actualizar IDs de nuevas filas
                    cargar_umbral()
                else:
                    mostrar_mensaje("Error", "Error al actualizar el umbral", 'error')
            else:
                # Modo creación: crear nuevo umbral
                success = UmbralController.ctrlGuardarUmbralesPersonalizados(
                    proyectoid,
                    nombre_actual,
                    datos_tabla
                )
                if success:
                    mostrar_mensaje("Guardado", "Umbral guardado correctamente.", 'informacion')
                    volver_a_modo_registro()
                else:
                    mostrar_mensaje("Error", "Error al guardar el umbral", 'error')
        
        # Función para eliminar fila individual
        def eliminar_fila(row):
            # Obtener ID de la fila si existe
            id_item = table.item(row, 0)
            if id_item and id_item.text():
                id_fila = id_item.text()
                # Eliminar de la base de datos
                if UmbralController.ctrlEliminarFilaUmbral(id_fila):
                    mostrar_mensaje("Éxito", "Fila eliminada correctamente", 'informacion')
                else:
                    mostrar_mensaje("Error", "No se pudo eliminar la fila", 'error')
            
            # Eliminar de la tabla
            table.removeRow(row)
        
        # Función para mostrar menú contextual (eliminar fila)
        def show_context_menu(position):
            item = table.itemAt(position)
            if item:
                row = item.row()
                menu = QMenu()
                delete_action = QAction("Eliminar fila", menu)
                delete_action.triggered.connect(lambda: eliminar_fila(row))
                menu.addAction(delete_action)
                menu.exec(table.viewport().mapToGlobal(position))
        
        # Conectar señales
        editar_button.clicked.connect(activar_modo_edicion)
        regresar_button.clicked.connect(volver_a_modo_registro)
        umbrales_combo.currentIndexChanged.connect(cargar_umbral)
        eliminar_button.clicked.connect(eliminar_umbral)
        registrar_button.clicked.connect(guardar_datos)
        
        # Configurar menú contextual
        table.setContextMenuPolicy(Qt.CustomContextMenu)
        table.customContextMenuRequested.connect(show_context_menu)
        
        # Ajustar tamaño de columnas
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Establecer el layout principal en el diálogo
        dialog.setLayout(main_layout)
        
        # Mostrar el diálogo
        dialog.exec_()
    
    def modalUmbralesPrismas(proyectoid, tipo, unidad1, unidad2, medida1, medida2):
        # Crear el diálogo
        dialog = QDialog()
        dialog.setWindowTitle("Configuración de Umbrales Prismas")
        # Layout principal
        main_layout = QVBoxLayout()
        # Nuevo ComboBox al inicio
        component_combo_label = QLabel("Seleccione Componente:")
        component_combo = QComboBox()
        # Añadir opciones al nuevo ComboBox desde listacomponente
        listacomponente = InterfazController.ctrlListarComponentesProyecto(proyectoid)
        tabla = UmbralView.obtenerTablaTipo(tipo)
        if listacomponente:
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
        #table.setHorizontalHeaderLabels(["Condición", "Color", "Riesgo", f"Rango ({medida1})", "Acciones a realizar"])
        # Función para reiniciar la tabla
        def reset_table():
            selected_option = combo.currentText()
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
                color_button.clicked.connect(lambda _, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
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
            selected_id = options[selected_option]  # Obtener el ID correspondiente
            selected_component_id = component_combo.currentData()  # Obtener el ID del componente seleccionado
            umbrales = UmbralController.ctrlObtenerUmbralesInstrumentacion(proyectoid, selected_component_id, selected_id, tabla)
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
                    color_button.clicked.connect(lambda _, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
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
                    acciones_item = QTableWidgetItem(umbral[7])  # Asumiendo que las acciones están en la posición 7
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
            color_button.clicked.connect(lambda _, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
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
            success = UmbralController.ctrlGuardarUmbralesEquipos(proyectoid, selected_component_id, selected_id, data, tabla)
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
                        success = UmbralController.ctrlEliminarUmbralEquipos(umbral_id, tabla)
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
        lista_equipos = InterfazController.ctrlListarInclinometrosProyecto(proyectoid)
        titulo = "Configuración de Umbrales Inclinómetros"
        titulo_combo = "Seleccione Inclinómetro:"
        # Crear el diálogo
        dialog = QDialog()
        dialog.setWindowTitle(titulo)
        # Layout principal
        main_layout = QVBoxLayout()
        # Nuevo ComboBox al inicio
        equipos_combo_label = QLabel(titulo_combo)
        combo_lista_equipos = QComboBox()
        tabla = UmbralView.obtenerTablaTipo(tipo)
        if lista_equipos:
            for componente in lista_equipos:
                combo_lista_equipos.addItem(componente[2], userData=componente[0])
            combo_lista_equipos.setCurrentIndex(0)
        # Añadir el nuevo ComboBox al layout principal
        main_layout.addWidget(equipos_combo_label)
        main_layout.addWidget(combo_lista_equipos)
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
                color_button.clicked.connect(lambda _, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
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
            selected_equipo_id = combo_lista_equipos.currentData()  # Obtener el ID del equipo seleccionado
            if unidad == 1:
                medida = "m"
            elif unidad == 100:
                medida = "cm"
            else:
                medida = "mm"
            umbrales = UmbralController.ctrlObtenerUmbralesInstrumentacion(proyectoid, selected_equipo_id, selected_id, tabla)
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
                    color_button.clicked.connect(lambda _, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
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
                    acciones_item = QTableWidgetItem(umbral[7])  # Asumiendo que las acciones están en la posición 7
                    table.setItem(row, 4, acciones_item)
            else:
                reset_table()
        # Conectar el cambio de opción en el ComboBox para cargar los umbrales
        combo.currentIndexChanged.connect(load_umbrales)
        combo_lista_equipos.currentIndexChanged.connect(load_umbrales)
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
            color_button.clicked.connect(lambda _, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
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
            selected_equipos_id = combo_lista_equipos.currentData()  # Obtener el ID del componente seleccionado
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
            success = UmbralController.ctrlGuardarUmbralesEquipos(proyectoid, selected_equipos_id, selected_id, data, tabla)
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
                        success = UmbralController.ctrlEliminarUmbralEquipos(umbral_id, tabla)
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
        # Añadir opciones al nuevo ComboBox desde listacomponente
        lista_equipos = InterfazController.ctrlListarPiezometrosProyecto(proyectoid)
        titulo = "Configuración de Umbrales Piezómetros"
        titulo_combo = "Seleccione Piezómetro:"
        # Crear el diálogo
        dialog = QDialog()
        dialog.setWindowTitle(titulo)
        # Layout principal
        main_layout = QVBoxLayout()
        # Nuevo ComboBox al inicio
        equipos_combo_label = QLabel(titulo_combo)
        combo_lista_equipos = QComboBox()
        tabla = UmbralView.obtenerTablaTipo(tipo)
        if lista_equipos:
            for piezometro in lista_equipos:
                combo_lista_equipos.addItem(piezometro[1], userData=(piezometro[0], piezometro[2]))
            combo_lista_equipos.setCurrentIndex(0)
        # Añadir el nuevo ComboBox al layout principal
        main_layout.addWidget(equipos_combo_label)
        main_layout.addWidget(combo_lista_equipos)
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
                color_button.clicked.connect(lambda _, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
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
            if combo_lista_equipos.count() > 0:
                datacombo = combo_lista_equipos.currentData()  # Obtener el ID del equipo seleccionado
                selected_equipo_id, tipopiezometro = datacombo
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
                umbrales = UmbralController.ctrlObtenerPiezometroUmbrales(selected_equipo_id, selected_id, tipopiezometro)
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
                        color_button.clicked.connect(lambda _, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
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
                        acciones_item = QTableWidgetItem(umbral[7])  # Asumiendo que las acciones están en la posición 7
                        table.setItem(row, 4, acciones_item)
                else:
                    reset_table()
            else:
                reset_table()
        # Conectar el cambio de opción en el ComboBox para cargar los umbrales
        combo.currentIndexChanged.connect(load_umbrales)
        combo_lista_equipos.currentIndexChanged.connect(load_umbrales)
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
            color_button.clicked.connect(lambda _, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
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
            datacombo = combo_lista_equipos.currentData()  # Obtener el ID del componente seleccionado
            selected_equipos_id, tipopiezometro = datacombo
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
            success = UmbralController.ctrlGuardarUmbralesPiezometros(proyectoid, selected_equipos_id, selected_id, data, tipopiezometro, tabla)
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
                        success = UmbralController.ctrlEliminarUmbralEquipos(umbral_id, tabla)
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
        lista_equipos = InterfazController.ctrlListarCeldasProyecto(proyectoid)
        titulo = "Configuración de Celdas"
        titulo_combo = "Seleccione Celda:"
        # Crear el diálogo
        dialog = QDialog()
        dialog.setWindowTitle(titulo)
        # Layout principal
        main_layout = QVBoxLayout()
        # Nuevo ComboBox al inicio
        equipos_combo_label = QLabel(titulo_combo)
        combo_lista_equipos = QComboBox()
        tabla = UmbralView.obtenerTablaTipo(tipo)
        if lista_equipos:
            for componente in lista_equipos:
                combo_lista_equipos.addItem(componente[2], userData=componente[0])
            combo_lista_equipos.setCurrentIndex(0)
        # Añadir el nuevo ComboBox al layout principal
        main_layout.addWidget(equipos_combo_label)
        main_layout.addWidget(combo_lista_equipos)
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
                color_button.clicked.connect(lambda _, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
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
            selected_equipo_id = combo_lista_equipos.currentData()  # Obtener el ID de la celda
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
            umbrales = UmbralController.ctrlObtenerUmbralesInstrumentacion(proyectoid, selected_equipo_id, selected_id, tabla)
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
                    color_button.clicked.connect(lambda _, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
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
                    acciones_item = QTableWidgetItem(umbral[7])  # Asumiendo que las acciones están en la posición 7
                    table.setItem(row, 4, acciones_item)
            else:
                reset_table()
        # Conectar el cambio de opción en el ComboBox para cargar los umbrales
        combo.currentIndexChanged.connect(load_umbrales)
        combo_lista_equipos.currentIndexChanged.connect(load_umbrales)
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
            color_button.clicked.connect(lambda _, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
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
            idcelda = combo_lista_equipos.currentData()  # Obtener el ID de la celda seleccionada
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
            success = UmbralController.ctrlGuardarUmbralesEquipos(proyectoid, idcelda, selected_id, data, tabla)
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
                        success = UmbralController.ctrlEliminarUmbralEquipos(umbral_id, tabla)
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
    
    def modalUmbralesEquipos(proyectoid, tipo, unidad, medida):
        tabla = UmbralView.obtenerTablaTipo(tipo)
        # Crear el diálogo
        dialog = QDialog()
        dialog.setWindowTitle("Configuración de Umbrales")
        # Layout principal
        main_layout = QVBoxLayout()
        # Nuevo ComboBox al inicio
        component_combo_label = QLabel("Seleccione Componente:")
        component_combo = QComboBox()
        # Añadir opciones al nuevo ComboBox desde listacomponente
        listacomponente = InterfazController.ctrlListarComponentesProyecto(proyectoid)
        if listacomponente:
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
        table.setHorizontalHeaderLabels(["Condición", "Color", "Riesgo", f"Rango ({medida})", "Acciones a realizar"])
        # Función para reiniciar la tabla
        def reset_table():
            selected_option = combo.currentText()
            selected_id = options[selected_option]
            if selected_id == "NF":
                unidadmedida = "msnm"
            elif selected_id == "NI":
                if unidad == 1:
                    unidadmedida = "m"
                elif unidad == 100:
                    unidadmedida = "cm"
                else:
                    unidadmedida = "mm"
            elif selected_id == "NA":
                if unidad == 1:
                    unidadmedida = "m"
                elif unidad == 100:
                    unidadmedida = "cm"
                else:
                    unidadmedida = "mm"
            elif selected_id == "PB":
                unidadmedida = "B"
            elif selected_id == "FP":
                unidadmedida = "Hz"
            elif selected_id == "TP":
                unidadmedida = "°C"
            elif selected_id == "VI":
                if unidad == 1:
                    unidadmedida = "m/d"
                elif unidad == 100:
                    unidadmedida = "cm/d"
                else:
                    unidadmedida = "mm/d"
            elif selected_id == "AC":
                unidadmedida = "msnm"
            elif selected_id == "AI":
                if unidad == 1:
                    unidadmedida = "m"
                elif unidad == 100:
                    unidadmedida = "cm"
                else:
                    unidadmedida = "mm"
            elif selected_id == "AA":
                if unidad == 1:
                    unidadmedida = "m"
                elif unidad == 100:
                    unidadmedida = "cm"
                else:
                    unidadmedida = "mm"
            table.setHorizontalHeaderLabels(["Condición", "Color", "Riesgo", f"Rango ({unidadmedida})", "Acciones a realizar"])
            table.setRowCount(3)
            for row in range(3):
                # Condición
                condicion_item = QTableWidgetItem("")
                table.setItem(row, 0, condicion_item)
                # Botón de color
                color_button = QPushButton()
                color_button.clicked.connect(lambda _, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
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
            selected_id = options[selected_option]  # Obtener el ID correspondiente
            selected_component_id = component_combo.currentData()  # Obtener el ID del componente seleccionado
            umbrales = UmbralController.ctrlObtenerUmbralesInstrumentacion(proyectoid, selected_component_id, selected_id, tabla)
            if umbrales:
                medidafinal = 1
                if selected_id == "NF":
                    unidadmedida = "msnm"
                elif selected_id == "NI":
                    if unidad == 1:
                        unidadmedida = "m"
                    elif unidad == 100:
                        unidadmedida = "cm"
                        medidafinal = 100
                    else:
                        unidadmedida = "mm"
                        medidafinal = 1000
                elif selected_id == "NA":
                    if unidad == 1:
                        unidadmedida = "m"
                    elif unidad == 100:
                        unidadmedida = "cm"
                        medidafinal = 100
                    else:
                        unidadmedida = "mm"
                        medidafinal = 1000
                elif selected_id == "PB":
                    unidadmedida = "B"
                elif selected_id == "FP":
                    unidadmedida = "Hz"
                elif selected_id == "TP":
                    unidadmedida = "°C"
                elif selected_id == "VI":
                    if unidad == 1:
                        unidadmedida = "m/d"
                    elif unidad == 100:
                        unidadmedida = "cm/d"
                        medidafinal = 100
                    else:
                        unidadmedida = "mm/d"
                        medidafinal = 1000
                elif selected_id == "AC":
                    unidadmedida = "msnm"
                elif selected_id == "AI":
                    if unidad == 1:
                        unidadmedida = "m"
                    elif unidad == 100:
                        unidadmedida = "cm"
                        medidafinal = 100
                    else:
                        unidadmedida = "mm"
                        medidafinal = 1000
                elif selected_id == "AA":
                    if unidad == 1:
                        unidadmedida = "m"
                    elif unidad == 100:
                        unidadmedida = "cm"
                        medidafinal = 100
                    else:
                        unidadmedida = "mm"
                        medidafinal = 1000
                table.setHorizontalHeaderLabels(["Condición", "Color", "Riesgo", f"Rango ({unidadmedida})", "Acciones a realizar"])
                table.setRowCount(len(umbrales))
                for row, umbral in enumerate(umbrales):
                    # Condición
                    condicion_item = QTableWidgetItem(umbral[3])  # Asumiendo que la condición está en la posición 3
                    condicion_item.setData(Qt.UserRole, umbral[0])  # Guardar el ID del umbral en el item
                    table.setItem(row, 0, condicion_item)
                    # Botón de color
                    color_button = QPushButton()
                    color_button.setStyleSheet(f"background-color: {umbral[4]};")  # Asumiendo que el color está en la posición 4
                    color_button.clicked.connect(lambda _, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
                    table.setCellWidget(row, 1, color_button)
                    # Riesgo
                    riesgo_item = QTableWidgetItem(umbral[5])  # Asumiendo que el riesgo está en la posición 5
                    table.setItem(row, 2, riesgo_item)
                    # Rango (DoubleSpinBox)
                    double_spinbox = QDoubleSpinBox()
                    double_spinbox.setRange(-1e9, 1e9)  # Rango grande
                    double_spinbox.setDecimals(5)  # Hasta 5 decimales
                    double_spinbox.setValue(umbral[6] * medidafinal)  # Asumiendo que el rango está en la posición 6
                    table.setCellWidget(row, 3, double_spinbox)
                    # Acciones a realizar
                    acciones_item = QTableWidgetItem(umbral[7])  # Asumiendo que las acciones están en la posición 7
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
            color_button.clicked.connect(lambda _, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
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
            selected_component_id = component_combo.currentData()  # Obtener el ID del componente seleccionado
            data = []
            medidafinal = 1
            if selected_id == "NI":
                if unidad == 100:
                    medidafinal = 100
                elif unidad == 1000:
                    medidafinal = 1000
            elif selected_id == "NA":
                if unidad == 100:
                    medidafinal = 100
                elif unidad == 1000:
                    medidafinal = 1000
            elif selected_id == "VI":
                if unidad == 100:
                    medidafinal = 100
                elif unidad == 1000:
                    medidafinal = 1000
            elif selected_id == "AI":
                if unidad == 100:
                    medidafinal = 100
                elif unidad == 1000:
                    medidafinal = 1000
            elif selected_id == "AA":
                if unidad == 100:
                    medidafinal = 100
                elif unidad == 1000:
                    medidafinal = 1000
            for row in range(table.rowCount()):
                condicion_item = table.item(row, 0)
                rango_item = table.cellWidget(row, 3)
                riesgo_item = table.item(row, 2)
                acciones_item = table.item(row, 4)
                if condicion_item and condicion_item.text() and rango_item and rango_item.value():
                    color_button = table.cellWidget(row, 1)
                    color = color_button.palette().button().color().name()
                    valorrango = float(rango_item.value()) / medidafinal
                    data.append({
                        "id": table.item(row, 0).data(Qt.UserRole) if table.item(row, 0) else None,  # Obtener el ID del umbral si existe
                        "condicion": condicion_item.text(),
                        "color": color,
                        "riesgo": riesgo_item.text(),
                        "rango": valorrango,
                        "acciones": acciones_item.text()
                    })
            # Guardar los datos en la base de datos
            success = UmbralController.ctrlGuardarUmbralesEquipos(proyectoid, selected_component_id, selected_id, data, tabla)
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
                        success = UmbralController.ctrlEliminarUmbralEquipos(umbral_id, tabla)
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
    
    def modalUmbralAcelerografosMagnitud(proyectoid):
        # Obtener componentes
        listacomponente = InterfazController.ctrlListarComponentesProyecto(proyectoid)
        # Crear el diálogo
        dialog = QDialog()
        dialog.setWindowTitle("Configuración de Umbrales")
        # Layout principal
        main_layout = QVBoxLayout()
        # Layout para el ComboBox y el botón Agregar Fila
        component_layout = QHBoxLayout()
        # ComboBox para seleccionar componente
        component_combo_label = QLabel("Seleccione Componente:")
        component_combo = QComboBox()
        # Añadir opciones al ComboBox desde listacomponente
        if listacomponente:
            for componente in listacomponente:
                component_combo.addItem(componente[2], userData=componente[0])  # componente[2] es el nombre, componente[0] es el ID
            component_combo.setCurrentIndex(0)
        # Botón Agregar Fila
        add_button = QPushButton("Agregar Fila")
        # Añadir el ComboBox y el botón al layout horizontal
        component_layout.addWidget(component_combo_label)
        component_layout.addWidget(component_combo)
        component_layout.addWidget(add_button)
        # Añadir el layout horizontal al layout principal
        main_layout.addLayout(component_layout)
        # Tabla
        table = QTableWidget(3, 6)  # 3 filas y 6 columnas
        table.setHorizontalHeaderLabels(["Nombre", "Riesgo", "Color", "Distancia (km)", "Magnitud (ML)", "Acciones a Realizar"])
        # Función para reiniciar la tabla
        def reset_table():
            table.setRowCount(3)
            for row in range(3):
                # Nombre
                nombre_item = QTableWidgetItem("")
                table.setItem(row, 0, nombre_item)
                # Riesgo
                riesgo_item = QTableWidgetItem("")
                table.setItem(row, 1, riesgo_item)
                # Botón de color
                color_button = QPushButton()
                color_button.clicked.connect(lambda _, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
                table.setCellWidget(row, 2, color_button)
                # Distancia (DoubleSpinBox)
                distancia_spinbox = QDoubleSpinBox()
                distancia_spinbox.setRange(0, 1e9)  # Rango grande
                distancia_spinbox.setDecimals(5)  # Hasta 5 decimales
                table.setCellWidget(row, 3, distancia_spinbox)
                # Magnitud (DoubleSpinBox)
                magnitud_spinbox = QDoubleSpinBox()
                magnitud_spinbox.setRange(0, 1e9)  # Rango grande
                magnitud_spinbox.setDecimals(5)  # Hasta 5 decimales
                table.setCellWidget(row, 4, magnitud_spinbox)
                # Acciones a Realizar
                acciones_item = QTableWidgetItem("")
                table.setItem(row, 5, acciones_item)
        def load_umbrales():
            selected_component_id = component_combo.currentData()  # Obtener el ID del componente seleccionado
            umbrales = UmbralController.ctrlObtenerUmbralesAcelerografo(proyectoid, selected_component_id, "AMA")
            if umbrales:
                table.setRowCount(len(umbrales))
                for row, umbral in enumerate(umbrales):
                    # Nombre
                    nombre_item = QTableWidgetItem(umbral[3])
                    nombre_item.setData(Qt.UserRole, umbral[0])  # Guardar el ID del umbral en el item
                    table.setItem(row, 0, nombre_item)
                    # Riesgo
                    riesgo_item = QTableWidgetItem(umbral[4])  # Asumiendo que el riesgo está en la posición 7
                    table.setItem(row, 1, riesgo_item)
                    # Botón de color
                    color_button = QPushButton()
                    color_button.setStyleSheet(f"background-color: {umbral[5]};")
                    color_button.clicked.connect(lambda _, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
                    table.setCellWidget(row, 2, color_button)
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
                reset_table()
        # Conectar el cambio de opción en el ComboBox para cargar los umbrales
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
            # Nombre
            nombre_item = QTableWidgetItem("")
            table.setItem(row_count, 0, nombre_item)
            # Riesgo
            riesgo_item = QTableWidgetItem("")
            table.setItem(row_count, 1, riesgo_item)
            # Botón de color
            color_button = QPushButton()
            color_button.clicked.connect(lambda _, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
            table.setCellWidget(row_count, 2, color_button)
            # Distancia (DoubleSpinBox)
            distancia_spinbox = QDoubleSpinBox()
            distancia_spinbox.setRange(0, 1e9)  # Rango grande
            distancia_spinbox.setDecimals(5)  # Hasta 5 decimales
            table.setCellWidget(row_count, 3, distancia_spinbox)
            # Magnitud (DoubleSpinBox)
            magnitud_spinbox = QDoubleSpinBox()
            magnitud_spinbox.setRange(0, 1e9)  # Rango grande
            magnitud_spinbox.setDecimals(5)  # Hasta 5 decimales
            table.setCellWidget(row_count, 4, magnitud_spinbox)
            # Acciones a Realizar
            acciones_item = QTableWidgetItem("")
            table.setItem(row_count, 5, acciones_item)
        # Conectar el botón a la función para agregar una nueva fila
        add_button.clicked.connect(add_row)
        # Función para manejar el evento de confirmar
        def confirm():
            selected_component_id = component_combo.currentData()  # Obtener el ID del componente seleccionado
            data = []
            for row in range(table.rowCount()):
                nombre_item = table.item(row, 0)
                distancia_item = table.cellWidget(row, 3)
                magnitud_item = table.cellWidget(row, 4)
                riesgo_item = table.item(row, 1)
                acciones_item = table.item(row, 5)
                if nombre_item and nombre_item.text() and distancia_item and magnitud_item and riesgo_item and acciones_item:
                    color_button = table.cellWidget(row, 2)
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
            success = UmbralController.ctrlGuardarUmbralesAcelerografo(proyectoid, selected_component_id, data)
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
                nombre_item = table.item(row, 0)
                if nombre_item:
                    umbral_id = nombre_item.data(Qt.UserRole)
                    if umbral_id and umbral_id != 0:
                        # Llamar a la base de datos para eliminar el registro
                        success = UmbralController.ctrlEliminarUmbralAcelerografo(umbral_id)
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
    
    def modalUmbralesAcelerografos(proyectoid):
        table = None
        # Crear el diálogo
        dialog = QDialog()
        dialog.setWindowTitle("Umbrales de Acelerógrafos")
        # Layout principal
        main_layout = QVBoxLayout()
        # Nuevo ComboBox al inicio
        component_combo_label = QLabel("Seleccione Componente:")
        component_combo = QComboBox()
        # Añadir opciones al nuevo ComboBox desde listacomponente
        listacomponente = InterfazController.ctrlListarComponentesProyecto(proyectoid)
        tabla = UmbralView.obtenerTablaTipo("ACELEROGRAFOS")
        if listacomponente:
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
        options = UmbralView.retornarArregloTipo("ACELEROGRAFOS")
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
                table.setHorizontalHeaderLabels(["Nombre", "Color", "Riesgo", "Distancia (km)", "Magnitud (ML)", "Acciones a Realizar"])
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
                    color_button.clicked.connect(lambda _, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
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
                    color_button.clicked.connect(lambda _, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
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
            umbrales = UmbralController.ctrlObtenerUmbralesInstrumentacion(proyectoid, componente_id, tipografica, tabla)
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
                        color_button.clicked.connect(lambda _, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
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
                        color_button.clicked.connect(lambda _, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
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
                        acciones_item = QTableWidgetItem(umbral[7])  # Asumiendo que las acciones están en la posición 7
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
                color_button.clicked.connect(lambda _, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
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
                color_button.clicked.connect(lambda _, btn=color_button: MetodosGenerales.cambiarColorBoton(btn))
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
                success = UmbralController.ctrlGuardarUmbralesAcelerografo(proyectoid, componente_id, data)
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
                success = UmbralController.ctrlGuardarUmbralesEquipos(proyectoid, componente_id, tipografica, data, tabla)
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
                        success = UmbralController.ctrlEliminarUmbralEquipos(umbral_id, tabla)
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
        dialog.resize(total_width + 50, dialog.height())  # Añadir un margen adicional si es necesario
        # Mostrar el diálogo
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
        elif tipo == 'INCLINOMETROS':
            options = {
                "Umbral Desplazamiento": "UDI",
            }
            return options
        elif tipo == 'PIEZOMETROS':
            options = {
                "Nivel Freático": "NF",
                "Nivel Incremental": "NI",
                "Nivel Acumulado": "NA",
                "Presión Barométrica": "PB",
                "Frecuencia": "FP",
                "Temperatura": "TP",
            }
            return options
        elif tipo == 'CELDAS':
            options = {
                "Velocidad Incremental": "VI",
                "Asentamiento en Cota": "AC",
                "Asentamiento Incremental": "AI",
                "Asentamiento Acumulado": "AA",
                "Frecuencia": "AF",
                "Temperatura": "AT",
            }
            return options
        elif tipo == 'ACELEROGRAFOS':
            options = {
                "Aceleración": "AAC",
                "Velocidad": "AVE",
                "Desplazamiento": "ADE",
                "Magnitud": "AMA"
            }
            return options
        else:
            options = {
                  
            }
            return options
    
    def obtenerTablaTipo(tipo):
        if tipo=='PRISMAS':
            return 'umbral_prisma'
        elif tipo=='INCLINOMETROS':
            return 'umbral_inclinometro'
        elif tipo=='PIEZOMETROS':
                return 'umbral_piezometro'
        elif tipo=='CELDAS':
                return 'umbral_celda'
        elif tipo=='ACELEROGRAFOS':
            return 'umbral_acelerografo'
    