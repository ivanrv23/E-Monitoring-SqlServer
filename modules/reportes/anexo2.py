from PySide6.QtWidgets import (QPushButton, QLabel,QLineEdit, QPlainTextEdit, QComboBox, QGridLayout, QGroupBox,
                               QHBoxLayout, QRadioButton, QFrame, QVBoxLayout, QWidget, QFileDialog)
from PySide6.QtGui import Qt, QPixmap
from PySide6.QtCore import QSize
from utils.generic.cargariconos import cargarIcono
from utils.generic.listaiconos import ListaIconos
from utils.common.metodosGenerales import MetodosGenerales
from controllers.ReporteController import ReporteController

class Anexo2:
    
    def setup_widget_anexo2(widget_anexo2, principal):
        componente = principal.findChild(QComboBox, "cb_componentes_anexos").currentData()
        # Obtener el layout principal del widget
        main_layout = widget_anexo2.layout()
        if not main_layout:  # Si el layout no existe, lo creamos
            main_layout = QVBoxLayout(widget_anexo2)
            widget_anexo2.setLayout(main_layout)  # Asignamos el layout al 
        # Limpiar el layout, eliminando todos los widgets dentro de él, pero dejando el  intacto
        while main_layout.count():
            item = main_layout.takeAt(0)  # Tomar el primer elemento del layout
            if item.widget():  # Si el item es un widget
                item.widget().deleteLater()
        # Agregar cada sección del layout
        main_layout.addWidget(Anexo2.create_frame_instrumentacion_A2(componente))
        main_layout.addWidget(Anexo2.create_frame_ubicacion_intrumentacion_A2(componente))
        main_layout.addWidget(Anexo2.create_frame_observaciones_A2(componente))
        # Establecer el layout nuevamente en el  (si es necesario)
        widget_anexo2.setLayout(main_layout)
    
    # ---------------- Frame UBICACION INTRUMENTACIÓN GEOTÉCNICA A2 ----------------#
    def create_frame_ubicacion_intrumentacion_A2(componente):
        ubicacion_intrumentacion_geotecnica = ReporteController.ctrlObtenerUbicacionInstrumentacionGeotecnica(componente)
        frame = QFrame()
        frame_layout = QGridLayout()
        # Título de la sección
        title_label = QLabel("UBICACIÓN INSTRUMENTACIÓN")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        frame_layout.addWidget(title_label, 0, 0, 1, 2)  # Ocupa las 2 primeras columnas
        # Encabezados de la tabla
        header_instrumento = QLabel("Instrumento")
        header_imagen = QLabel("Imagen")
        header_acciones = QLabel("Acciones")
        # Centramos los textos de los encabezados
        header_instrumento.setAlignment(Qt.AlignCenter)
        header_imagen.setAlignment(Qt.AlignCenter)
        header_acciones.setAlignment(Qt.AlignCenter)
        # Agregar los encabezados al layout
        frame_layout.addWidget(header_instrumento, 1, 0, 1, 1)
        frame_layout.addWidget(header_imagen, 1, 1, 1, 1)
        frame_layout.addWidget(header_acciones, 1, 2, 1, 1)
        # Lista de placeholders
        placeholders = [
            "Piezómetros Casagrande",
            "Piezómetros Cuerda Vibrante",
            "Hitos Topográficos",
            "Inclinómetros",
            "Celdas de Asentamiento",
            "Satelital",
            "Acelerógrafos",
            "TDR"
        ]
        # Función para crear cada fila de entrada
        def create_row(line_edit_text="", row_id=None, placeholder="", tipo_instrumentacion=None):
            row_line_edit = QLineEdit(line_edit_text)
            row_line_edit.setFixedHeight(80)  # Ajustar la altura del QLineEdit
            row_line_edit.setPlaceholderText(placeholder)
            # Miniatura de la imagen con tamaño fijo
            row_image_label = QLabel("Sin Imagen")
            row_image_label.setAlignment(Qt.AlignCenter)
            row_image_label.setFixedSize(80, 80)  # Ajustar el tamaño del QLabel de la imagen
            row_image_label.setStyleSheet("border: 1px solid gray;")  # Estilo opcional
            # Botones con iconos
            row_button_load = QPushButton()
            cargarIcono(row_button_load, ListaIconos.ICONOS["subirimagen"])
            row_button_load.setIconSize(QSize(40, 40))
            row_button_load.setFixedSize(QSize(50, 50))
            # Layout horizontal para los botones de acciones
            actions_layout = QHBoxLayout()
            actions_layout.addWidget(row_button_load)
            actions_layout.setAlignment(Qt.AlignCenter)
            actions_widget = QWidget()
            actions_widget.setLayout(actions_layout)
            # Almacenar el ID de la fila y el tipo de instrumentación en atributos personalizados
            row_line_edit.row_id = row_id
            row_line_edit.tipo_instrumentacion = tipo_instrumentacion
            return row_line_edit, row_image_label, actions_widget, row_button_load
        # Función para cargar una imagen en el QLabel
        def load_image(label):
            # Abrir cuadro de diálogo para seleccionar un archivo de imagen
            file_path, _ = QFileDialog.getOpenFileName(
                frame, "Seleccionar Imagen", "", "Imágenes (*.png *.jpg *.jpeg *.bmp *.gif)"
            )
            if file_path:
                # Cargar la imagen seleccionada
                pixmap = QPixmap(file_path)
                # Redimensionar la imagen a las dimensiones del QLabel
                pixmap = pixmap.scaled(label.size(), Qt.AspectRatioMode.KeepAspectRatio)
                label.setPixmap(pixmap)
                label.setAlignment(Qt.AlignCenter)
                # Guardar la ruta de la imagen en un atributo personalizado del QLabel
                label.ruta_imagen = file_path
            else:
                # Si no se selecciona imagen, asegurarse de mantener este atributo
                label.ruta_imagen = "Sin imagen"
        # Crear 8 filas por defecto con placeholders
        rows = [create_row(placeholder=placeholders[i], row_id=None, tipo_instrumentacion=i+1) for i in range(8)]
        for i, (line_edit, image_label, actions_widget, button_load) in enumerate(rows, start=2):
            frame_layout.addWidget(line_edit, i, 0, 1, 1)
            frame_layout.addWidget(image_label, i, 1, 1, 1)
            frame_layout.addWidget(actions_widget, i, 2, 1, 1)
            # Conectar el botón para cargar imagen
            button_load.clicked.connect(lambda _, img_label=image_label: load_image(img_label))
        # Si se encuentran datos en 'ubicacion_intrumentacion_geotecnica', procesarlos
        if ubicacion_intrumentacion_geotecnica:
            for data in ubicacion_intrumentacion_geotecnica:
                instrument = data[2]
                imagen_blob = data[3]
                tipo_instrumentacion = data[4]  # Obtener el tipo de instrumentación
                row_id = data[0]  # Obtener el ID de la fila
                if isinstance(tipo_instrumentacion, int) and 1 <= tipo_instrumentacion <= 8:
                    line_edit, image_label, actions_widget, button_load = rows[tipo_instrumentacion - 1]
                    line_edit.setText(instrument)
                    line_edit.row_id = row_id  # Asignar el ID de la fila
                    if imagen_blob:
                        pixmap = MetodosGenerales.convertir_blob_a_pixmap(imagen_blob)
                        # Redimensionar la imagen para que se ajuste al QLabel
                        pixmap = pixmap.scaled(
                            image_label.width(), image_label.height(),
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        )
                        image_label.setPixmap(pixmap)
                        image_label.setAlignment(Qt.AlignCenter)
        # Configurar layout
        frame.setLayout(frame_layout)
        return frame
    
    # ---------------- Frame INTRUMENTACIÓN GEOTÉCNICA A2 ----------------#
    def create_frame_instrumentacion_A2(componente):
        intrumentacion_geotecnica = ReporteController.ctrlObtenerInstrumentacionGeotecnica(componente)
        frame = QFrame()
        frame_layout = QGridLayout()
        # Lista para almacenar las filas
        rows = []
        # Título de la tabla
        title_label = QLabel("INSTRUMENTACIÓN GEOTÉCNICA")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")  # Estilo opcional
        # Crear un botón para agregar nueva fila
        add_row_button = QPushButton("Agregar Fila")
        add_row_button.setStyleSheet("font-size: 12px;")  # Estilo opcional
        # Función para agregar nueva fila
        def add_new_row():
            # Definir la nueva fila de entrada (nuevos widgets)
            description_input = QLineEdit()
            authorized_quantity_spin = QLineEdit()
            authorized_operational_spin = QLineEdit()
            additional_quantity_spin = QLineEdit()
            additional_operational_spin = QLineEdit()
            frequency_combobox = QComboBox()
            frequency_combobox.addItems(["Diaria", "Tiempo real", "Semanal", "Quincenal", "Mensual", "Anual"])
            # Agregar los nuevos widgets a la fila
            new_row = [
                description_input,
                authorized_quantity_spin,
                authorized_operational_spin,
                additional_quantity_spin,
                additional_operational_spin,
                frequency_combobox
            ]
            # Agregar la fila a la lista de filas
            rows.append(new_row)
            # Contar la cantidad de filas para colocar la nueva fila debajo
            row_count = frame_layout.rowCount()
            # Agregar los nuevos widgets a la nueva fila en el layout
            for col, widget in enumerate(new_row):
                frame_layout.addWidget(widget, row_count, col, 1, 1)
        # Conectar el botón con la función para agregar una nueva fila
        add_row_button.clicked.connect(add_new_row)
        # Agregar el título y el botón al layout
        frame_layout.addWidget(title_label, 0, 0, 1, 5)  # 1 fila, 5 columnas (sin contar el botón)
        frame_layout.addWidget(add_row_button, 0, 5, 1, 1)  # El botón al costado derecho
        # Encabezados de la "tabla"
        header_description = QLabel("Descripción")
        header_authorized = QLabel("Autorizado")
        header_additional = QLabel("Adicional")
        header_frequency = QLabel("Frecuencia de Monitoreo")
        label_authorized_quantity = QLabel("Cantidad")
        label_authorized_operational = QLabel("Operativo")
        label_additional_quantity = QLabel("Cantidad")
        label_additional_operational = QLabel("Operativo")
        # Centramos los textos de los encabezados
        header_description.setAlignment(Qt.AlignCenter)
        header_authorized.setAlignment(Qt.AlignCenter)
        header_additional.setAlignment(Qt.AlignCenter)
        header_frequency.setAlignment(Qt.AlignCenter)
        label_authorized_quantity.setAlignment(Qt.AlignCenter)
        label_authorized_operational.setAlignment(Qt.AlignCenter)
        label_additional_quantity.setAlignment(Qt.AlignCenter)
        label_additional_operational.setAlignment(Qt.AlignCenter)
        # Agregar los encabezados al layout
        frame_layout.addWidget(header_description, 1, 0, 2, 1)  # 2 filas, 1 columna
        frame_layout.addWidget(header_authorized, 1, 1, 1, 2)   # 1 fila, 2 columnas
        frame_layout.addWidget(label_authorized_quantity, 2, 1, 1, 1)  # Cantidad
        frame_layout.addWidget(label_authorized_operational, 2, 2, 1, 1)  # Operativo
        frame_layout.addWidget(header_additional, 1, 3, 1, 2)   # 1 fila, 2 columnas
        frame_layout.addWidget(label_additional_quantity, 2, 3, 1, 1)  # Cantidad
        frame_layout.addWidget(label_additional_operational, 2, 4, 1, 1)  # Operativo
        frame_layout.addWidget(header_frequency, 1, 5, 2, 1)    # 2 filas, 1 columna
        # Llenar la tabla con los datos si están disponibles
        if intrumentacion_geotecnica:
            for row_data in intrumentacion_geotecnica:
                # Desglosar los datos de cada tupla
                description, authorized_quantity, authorized_operational, additional_quantity, additional_operational, frequency = row_data[2], row_data[3], row_data[4], row_data[5], row_data[6], row_data[8]
                # Crear los campos correspondientes a la fila
                description_input = QLineEdit(description)
                authorized_quantity_spin = QLineEdit(authorized_quantity)
                authorized_operational_spin = QLineEdit(authorized_operational)
                additional_quantity_spin = QLineEdit(additional_quantity)
                additional_operational_spin = QLineEdit(additional_operational)
                frequency_combobox = QComboBox()
                frequency_combobox.addItems(["Diaria", "Tiempo real", "Semanal", "Quincenal", "Mensual", "Anual"])
                # Establecer el valor del combo de frecuencia
                if frequency in ["Diaria", "Tiempo real", "Semanal", "Quincenal", "Mensual", "Anual"]:
                    frequency_combobox.setCurrentText(frequency)
                # Agregar los widgets a la fila
                new_row = [
                    description_input,
                    authorized_quantity_spin,
                    authorized_operational_spin,
                    additional_quantity_spin,
                    additional_operational_spin,
                    frequency_combobox
                ]
                # Contar la cantidad de filas para colocar la nueva fila debajo
                row_count = frame_layout.rowCount()
                # Agregar los widgets de esta fila en el layout
                for col, widget in enumerate(new_row):
                    frame_layout.addWidget(widget, row_count, col, 1, 1)
        else:
            # Si no hay datos, agregar una fila en blanco
            add_new_row()
        # Configurar layout
        frame.setLayout(frame_layout)
        return frame
    
    # ---------------- Frame OBSERVACIONES A2 ----------------
    def create_frame_observaciones_A2(componente):
        observaciones_anexo2 = ReporteController.ctrlObtenerObservacionesA2(componente)
        frame = QFrame()
        frame_layout = QGridLayout()
        # Título
        title_label = QLabel("OBSERVACIONES, MEDIDAS ADOPTADAS Y SEGUIMIENTO")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        # Botones para agregar filas
        add_si_no_button = QPushButton("Agregar Fila SI/NO")
        add_plaintext_button = QPushButton("Agregar Fila Comentarios")
        # Layout del título y los botones
        title_layout = QHBoxLayout()
        title_layout.addWidget(title_label)
        title_layout.addStretch()  # Espaciado para mover los botones a la derecha
        title_layout.addWidget(add_si_no_button)
        title_layout.addWidget(add_plaintext_button)
        # Agregar el título y los botones al layout principal
        frame_layout.addLayout(title_layout, 0, 0, 1, 4)
        # Encabezados de la tabla
        header_description = QLabel("Descripción")
        header_condition = QLabel("Condición Actual")
        header_comments = QLabel("Comentarios")
        frame_layout.addWidget(header_description, 1, 0, Qt.AlignCenter)
        frame_layout.addWidget(header_condition, 1, 1, 1, 2, Qt.AlignCenter)  # Combina 2 columnas
        frame_layout.addWidget(header_comments, 1, 3, Qt.AlignCenter)
        # Crear filas dinámicamente
        rows = []
        def add_si_no_row(observacion=None):
            """Agregar una fila con SI/NO en Condición Actual."""
            row_index = len(rows) + 2
            # Descripción
            plaintext_description = QPlainTextEdit()
            plaintext_description.setPlaceholderText("Ingrese la descripción aquí...")
            plaintext_description.setMinimumHeight(60)  # Altura mínima
            plaintext_description.setMinimumWidth(200)
            frame_layout.addWidget(plaintext_description, row_index, 0)
            # Condición Actual
            group_box_condition = QGroupBox()
            group_box_condition.setMinimumHeight(60)  # Altura mínima
            group_box_condition.setMinimumWidth(100)
            group_layout_condition = QHBoxLayout(group_box_condition)
            radio_si = QRadioButton("SI")
            radio_si.setChecked(True)
            radio_no = QRadioButton("NO")
            group_layout_condition.addWidget(radio_si)
            group_layout_condition.addWidget(radio_no)
            frame_layout.addWidget(group_box_condition, row_index, 1, 1, 2)  # Combina columnas
            # Comentarios
            plaintext_comments = QPlainTextEdit()
            plaintext_comments.setPlaceholderText("Ingrese comentarios aquí...")
            plaintext_comments.setMinimumHeight(60)  # Altura mínima
            plaintext_comments.setMinimumWidth(200)
            frame_layout.addWidget(plaintext_comments, row_index, 3)
            # Si se pasó una observación, cargar los valores en la fila
            if observacion:
                plaintext_description.setPlainText(observacion[2])  # Descripción
                if observacion[3] == "SI":
                    radio_si.setChecked(True)
                elif observacion[3] == "NO":
                    radio_no.setChecked(True)
                plaintext_comments.setPlainText(observacion[6])  # Comentarios
            # Guardar la fila
            rows.append({
                "description": plaintext_description,
                "condition": group_box_condition,
                "comments": plaintext_comments,
            })
        def add_plaintext_row(observacion=None):
            """Agregar una fila con solo QPlainTextEdit en Comentarios."""
            row_index = len(rows) + 2
            # Descripción
            plaintext_description = QPlainTextEdit()
            plaintext_description.setPlaceholderText("Descripción")
            plaintext_description.setMinimumHeight(60)  # Altura mínima
            plaintext_description.setMinimumWidth(200)
            frame_layout.addWidget(plaintext_description, row_index, 0)
            # Medidas de Control
            plaintext_control = QPlainTextEdit()
            plaintext_control.setPlaceholderText("Medidas de control")
            plaintext_control.setMinimumHeight(60)  # Altura mínima
            plaintext_control.setMinimumWidth(200)
            frame_layout.addWidget(plaintext_control, row_index, 1)
            # Plazo
            plaintext_plazo = QPlainTextEdit()
            plaintext_plazo.setPlaceholderText("Plazo")
            plaintext_plazo.setMinimumHeight(60)  # Altura mínima
            plaintext_plazo.setMinimumWidth(200)            
            frame_layout.addWidget(plaintext_plazo, row_index, 2)
            # Responsable
            plaintext_responsable = QPlainTextEdit()
            plaintext_responsable.setPlaceholderText("Responsable")
            plaintext_responsable.setMinimumHeight(60)  # Altura mínima
            plaintext_responsable.setMinimumWidth(200)    
            frame_layout.addWidget(plaintext_responsable, row_index, 3)
            # Si se pasó una observación, cargar los valores en la fila
            if observacion:
                plaintext_description.setPlainText(observacion[2])  # Descripción
                plaintext_control.setPlainText(observacion[4])  # Medidas de control
                plaintext_plazo.setPlainText(observacion[5])  # Plazo
                plaintext_responsable.setPlainText(observacion[7])  # Responsable
            # Guardar la fila
            rows.append({
                "description": plaintext_description,
                "control": plaintext_control,
                "plazo": plaintext_plazo,
                "responsable": plaintext_responsable,
            })
        # Agregar filas iniciales con los datos de la base de datos
        def add_initial_rows():
            if observaciones_anexo2:
                for observacion in observaciones_anexo2:
                    if observacion[8] == 1:  # Tipo 1: SI/NO
                        add_si_no_row(observacion) 
                    else:  # Tipo 2: Comentarios extendidos
                        add_plaintext_row(observacion) 
            else:
                # Agregar filas predeterminadas si no hay datos
                add_si_no_row()       # Fila 1: SI/NO
                add_si_no_row()       # Fila 2: SI/NO
                add_plaintext_row()   # Fila 3: Comentarios extendidos
        add_initial_rows()
        # Conectar los botones para agregar filas dinámicamente
        add_si_no_button.clicked.connect(add_si_no_row)
        add_plaintext_button.clicked.connect(add_plaintext_row)
        frame.setLayout(frame_layout)
        return frame
    
    # -------Obtener valores frames------#
    def obtener_valores_frame_instrumentacion_A2(widget):
        # Buscar el layout principal del widget
        layout = widget.layout()
        # Acceder al frame3 (que está dentro del layout, en el índice 2)
        frame = layout.itemAt(0).widget()  # Cambiar índice según sea necesario
        # Verificar que frame3 exista
        if not frame:
            raise ValueError("No se encontró el frame3 en el índice especificado.")
        # Obtener el layout de frame3
        frame_layout = frame.layout()
        # Lista para almacenar los valores de las filas
        valores = []
        # Iterar a partir de la fila 3 (donde inician los datos)
        for i in range(3, frame_layout.rowCount()):
            row_values = []
            # Celda 0: QLineEdit (Descripción)
            description_input = frame_layout.itemAtPosition(i, 0).widget()
            description_text = description_input.text().strip() if description_input else ""
            # Si la descripción está vacía, no considerar la fila
            if not description_text:
                continue
            # Añadir descripción al registro
            row_values.append(description_text)
            # Celda 1: QLineEdit (Cantidad autorizada)
            authorized_quantity_input = frame_layout.itemAtPosition(i, 1).widget()
            row_values.append(authorized_quantity_input.text().strip() if authorized_quantity_input else "0")
            # Celda 2: QLineEdit (Operativo autorizado)
            authorized_operational_input = frame_layout.itemAtPosition(i, 2).widget()
            row_values.append(authorized_operational_input.text().strip() if authorized_operational_input else "0")
            # Celda 3: QLineEdit (Cantidad adicional)
            additional_quantity_input = frame_layout.itemAtPosition(i, 3).widget()
            row_values.append(additional_quantity_input.text().strip() if additional_quantity_input else "0")
            # Celda 4: QLineEdit (Operativo adicional)
            additional_operational_input = frame_layout.itemAtPosition(i, 4).widget()
            row_values.append(additional_operational_input.text().strip() if additional_operational_input else "0")
            # Celda 5: QComboBox (Frecuencia)
            frequency_combobox = frame_layout.itemAtPosition(i, 5).widget()
            row_values.append(frequency_combobox.currentText() if frequency_combobox else "")
            # Añadir los valores de esta fila a la lista
            valores.append(row_values)
        return valores
    
    def obtener_valores_frame_ubicacion_intrumentacion_A2(widget):
        # Buscar el layout principal del widget
        layout = widget.layout()
        # Asegurar que el layout existe
        if not layout:
            return []
        frame = layout.itemAt(1).widget()
        if not frame:
            return []
        # Obtener el layout dentro de frame4
        frame_layout = frame.layout()
        if not frame_layout:
            return []
        # Lista para almacenar los valores extraídos
        valores = []
        for row in range(2, frame_layout.rowCount()):
            instrumento_item = frame_layout.itemAtPosition(row, 0)
            imagen_item = frame_layout.itemAtPosition(row, 1)
            if instrumento_item and imagen_item:
                instrumento_line_edit = instrumento_item.widget()
                imagen_label = imagen_item.widget()
                if isinstance(instrumento_line_edit, QLineEdit) and isinstance(imagen_label, QLabel):
                    # Obtener el texto del instrumento
                    instrumento = instrumento_line_edit.text().strip()
                    row_id = getattr(instrumento_line_edit, "row_id", None)
                    tipo_instrumentacion = getattr(instrumento_line_edit, "tipo_instrumentacion", None)
                    if instrumento:  # Solo considerar filas con nombre de instrumento
                        pixmap = imagen_label.pixmap()
                        imagen_path = None
                        if pixmap:
                            imagen_path = getattr(imagen_label, "ruta_imagen", None)
                        # Solo agregar la fila si la imagen tiene un valor válido
                        if imagen_path and imagen_path != "Sin imagen":
                            valores.append({
                                "id": row_id,
                                "tipo_instrumentacion": tipo_instrumentacion,
                                "instrumento": instrumento,
                                "imagen": imagen_path
                            })
                        else:
                            valores.append({
                                "id": row_id,
                                "tipo_instrumentacion": tipo_instrumentacion,
                                "instrumento": instrumento,
                                "imagen": None
                            })
        return valores
    
    def obtener_valores_frame_observaciones_A2(widget):
        # Buscar el layout principal del widget
        layout = widget.layout()
        # Acceder al frame6 (que está dentro del layout, en el índice 5)
        frame = layout.itemAt(2).widget()  # Obtener el frame6 (índice 5)
        # Obtener el layout dentro de frame6
        frame_layout = frame.layout()
        # Lista para almacenar los valores de las filas
        valores = []
        # Recorremos las filas dinámicas, comenzando desde la fila 2 (porque las filas 0 y 1 son encabezados)
        for i in range(2, frame_layout.rowCount()):
            row_values = []
            # Celda 0: QPlainTextEdit (Descripción)
            description_widget = frame_layout.itemAtPosition(i, 0).widget()
            if not description_widget or not description_widget.toPlainText().strip():
                # Si la descripción está vacía, omitir esta fila
                continue
            descripcion = description_widget.toPlainText().strip()
            row_values.append(descripcion)  # Agregar Descripción
            # Determinar el tipo de fila (SI/NO o Comentarios Extendidos)
            condition_widget = frame_layout.itemAtPosition(i, 1).widget()
            if isinstance(condition_widget, QGroupBox):
                # Es una fila SI/NO
                radio_buttons = condition_widget.findChildren(QRadioButton)
                condicion_actual = next((radio.text() for radio in radio_buttons if radio.isChecked()), "")
                row_values.append(condicion_actual)  # Condición Actual
                row_values.append("")  # Medidas de Control vacío
                row_values.append("")  # Plazo vacío
                comments_widget = frame_layout.itemAtPosition(i, 3).widget()
                comentario = comments_widget.toPlainText().strip() if comments_widget else ""
                row_values.append(comentario)  # Comentarios
                row_values.append("")  # Responsable vacío
                row_values.append(1)  # Tipo de fila: 1 (SI/NO)
            else:
                # Es una fila de Comentarios Extendidos
                row_values.append("")  # Condición Actual vacío
                medidas_control_widget = frame_layout.itemAtPosition(i, 1).widget()
                medidas_control = medidas_control_widget.toPlainText().strip() if medidas_control_widget else ""
                row_values.append(medidas_control)  # Medidas de Control
                plazo_widget = frame_layout.itemAtPosition(i, 2).widget()
                plazo = plazo_widget.toPlainText().strip() if plazo_widget else ""
                row_values.append(plazo)  # Plazo
                comments_widget = frame_layout.itemAtPosition(i, 3).widget()
                responsable = comments_widget.toPlainText().strip() if comments_widget else ""
                row_values.append("")  # Comentarios vacío
                row_values.append(responsable)  # Responsable
                row_values.append(2)  # Tipo de fila: 2 (Comentarios Extendidos)
            # Añadir los valores de esta fila a la lista de valores
            valores.append(row_values)
        return valores
    