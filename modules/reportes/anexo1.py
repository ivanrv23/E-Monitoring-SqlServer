from PySide6.QtWidgets import (QPushButton, QLabel, QLineEdit, QPlainTextEdit, QComboBox, QGridLayout, QGroupBox, QHBoxLayout,
                               QRadioButton, QFrame, QVBoxLayout, QSpinBox, QCheckBox)
from PySide6.QtGui import Qt
from controllers.ReporteController import ReporteController

class Anexo1:
    
    def setup_widget_anexo1(widget_anexo1, principal):
        componente = principal.findChild(QComboBox, "cb_componentes_anexos").currentData()
        # Obtener el layout principal del widget
        main_layout = widget_anexo1.layout()
        if not main_layout:  # Si el layout no existe, lo creamos
            main_layout = QVBoxLayout(widget_anexo1)
            widget_anexo1.setLayout(main_layout)  # Asignamos el layout al widget_anexo1
        # Limpiar el layout, eliminando todos los widgets dentro de él, pero dejando el widget_anexo1 intacto
        while main_layout.count():
            item = main_layout.takeAt(0)  # Tomar el primer elemento del layout
            if item.widget():  # Si el item es un widget
                item.widget().deleteLater()  # Eliminar el widget
        # Regenerar los frames y agregarlos al layout
        main_layout.addWidget(Anexo1.create_frame_parametros_A1(componente))
        main_layout.addWidget(Anexo1.create_frame_condiciones_A1(componente))
        main_layout.addWidget(Anexo1.create_frame_operatividad_A1(componente))
        main_layout.addWidget(Anexo1.create_frame_observaciones_A1(componente))
        # Establecer el layout nuevamente en el widget_anexo1 (si es necesario)
        widget_anexo1.setLayout(main_layout)

    # ---------------- Frame CONTROL PARÁMETROS ----------------
    def create_frame_parametros_A1(componente):
        parametros = ReporteController.ctrlObtenerControlParametrosA1(componente)
        frame = QFrame()
        frame_layout = QGridLayout()
        control_label = QLabel("CONTROL DE PARÁMETROS")
        control_label.setStyleSheet("font-weight: bold;")
        frame_layout.addWidget(control_label, 0, 0, 1, 5, Qt.AlignLeft)
        add_row_button = QPushButton("Agregar Fila")
        frame_layout.addWidget(add_row_button, 0, 5, Qt.AlignRight)
        header_desc = QLabel("DESCRIPCIÓN")
        header_param = QLabel("PARÁMETROS")
        header_cond = QLabel("CONDICIÓN ACTUAL")
        header_com = QLabel("COMENTARIOS")
        frame_layout.addWidget(header_desc, 1, 0, Qt.AlignCenter)
        frame_layout.addWidget(header_param, 1, 1, 1, 2, Qt.AlignCenter)
        frame_layout.addWidget(header_cond, 1, 3, 1, 2, Qt.AlignCenter)
        frame_layout.addWidget(header_com, 1, 5, Qt.AlignCenter)
        rows = []
        def add_row(data=None):
            row_index = len(rows) + 2
            row_widgets = []
            # Descripción
            line_edit_desc = QLineEdit(data[2] if data else "")
            frame_layout.addWidget(line_edit_desc, row_index, 0)
            line_edit_desc.setMinimumHeight(40)  # Altura mínima
            line_edit_desc.setMinimumWidth(200)
            row_widgets.append(line_edit_desc)
            # Parámetro 1
            line_edit_param1 = QLineEdit(data[3] if data else "")
            frame_layout.addWidget(line_edit_param1, row_index, 1)
            line_edit_param1.setMinimumHeight(40)  # Altura mínima
            line_edit_param1.setMinimumWidth(80)
            row_widgets.append(line_edit_param1)
            # Parámetro 2
            line_edit_param2 = QLineEdit(data[4] if data else "")
            frame_layout.addWidget(line_edit_param2, row_index, 2)
            line_edit_param2.setMinimumHeight(40)  # Altura mínima
            line_edit_param2.setMinimumWidth(80)
            row_widgets.append(line_edit_param2)
            # Condición (Radio Buttons)
            group_box_condition = QGroupBox()
            radio_group_layout = QHBoxLayout(group_box_condition)
            group_box_condition.setMinimumHeight(40)  # Altura mínima
            group_box_condition.setMinimumWidth(100)
            radio_cumple = QRadioButton("CUMPLE")
            radio_no_cumple = QRadioButton("NO CUMPLE")
            if data:
                if data[5] == "CUMPLE":
                    radio_cumple.setChecked(True)
                else:
                    radio_no_cumple.setChecked(True)
            else:
                radio_cumple.setChecked(True)
            radio_group_layout.addWidget(radio_cumple)
            radio_group_layout.addWidget(radio_no_cumple)
            frame_layout.addWidget(group_box_condition, row_index, 3, 1, 2)
            row_widgets.append(group_box_condition)
            # Comentarios
            text_edit_comments = QPlainTextEdit(data[6] if data else "")
            frame_layout.addWidget(text_edit_comments, row_index, 5)
            text_edit_comments.setMinimumHeight(40)  # Altura mínima
            text_edit_comments.setMinimumWidth(100)
            row_widgets.append(text_edit_comments)
            rows.append(row_widgets)
        # Si hay parámetros, crear filas a partir de ellos
        if parametros:
            for parametro in parametros:
                add_row(parametro)
        else:
            # Si no hay parámetros, agregar una fila vacía inicial
            add_row()
        add_row_button.clicked.connect(lambda: add_row())
        frame.setLayout(frame_layout)
        return frame
    
    # ---------------- Frame VERIFICACION DE CONDICIONES FISICAS----------------
    def create_frame_condiciones_A1(componente):
        condiciones_fisicas = ReporteController.ctrlObtenerCondicionesFisicasA1(componente)
        frame = QFrame()
        frame_layout = QGridLayout()
        # Título y botones al costado
        verification_title = QLabel("VERIFICACIÓN DE CONDICIONES FÍSICAS")
        verification_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        button1 = QPushButton("Fila Cumple/No cumple")
        button2 = QPushButton("Fila SI/NO")
        button3 = QPushButton("Fila Normal")
        button_layout = QHBoxLayout()
        button_layout.addWidget(button1)
        button_layout.addWidget(button2)
        button_layout.addWidget(button3)
        title_and_buttons_layout = QHBoxLayout()
        title_and_buttons_layout.addWidget(verification_title)
        title_and_buttons_layout.addLayout(button_layout)
        frame_layout.addLayout(title_and_buttons_layout, 0, 0, 1, 3)
        # Encabezados
        header_condition = QLabel("Condiciones de los Taludes")
        header_actual = QLabel("Condición Actual")
        header_comments = QLabel("Comentarios")
        frame_layout.addWidget(header_condition, 1, 0, Qt.AlignCenter)
        frame_layout.addWidget(header_actual, 1, 1, Qt.AlignCenter)
        frame_layout.addWidget(header_comments, 1, 2, Qt.AlignCenter)
        # Fila iniciales
        rows = []
        def add_row(row_type, condicion=None):
            row_index = len(rows) + 2
            if row_type == "CUMPLE_NO_CUMPLE":
                line_edit_condition = QLineEdit(condicion[2] if condicion else '')
                line_edit_condition.setMinimumHeight(60)  # Altura mínima
                line_edit_condition.setMinimumWidth(200)
                frame_layout.addWidget(line_edit_condition, row_index, 0)
                group_box_condition = QGroupBox()
                group_layout_condition = QHBoxLayout(group_box_condition)
                radio_cumple = QRadioButton("CUMPLE")
                radio_cumple.setChecked(True)
                radio_no_cumple = QRadioButton("NO CUMPLE")
                group_layout_condition.addWidget(radio_cumple)
                group_layout_condition.addWidget(radio_no_cumple)
                group_box_condition.setMinimumHeight(60)  # Altura mínima
                group_box_condition.setMinimumWidth(100)
                frame_layout.addWidget(group_box_condition, row_index, 1)
                text_edit_comments = QPlainTextEdit(condicion[4] if condicion else '')
                text_edit_comments.setMinimumHeight(60)  # Altura mínima
                text_edit_comments.setMinimumWidth(200)
                frame_layout.addWidget(text_edit_comments, row_index, 2)
                rows.append((line_edit_condition, group_box_condition, text_edit_comments))
            elif row_type == "SI_NO":
                line_edit_condition = QLineEdit(condicion[2] if condicion else '')
                line_edit_condition.setMinimumHeight(60)  # Altura mínima
                line_edit_condition.setMinimumWidth(200)
                frame_layout.addWidget(line_edit_condition, row_index, 0)
                group_box_condition = QGroupBox()
                group_layout_condition = QHBoxLayout(group_box_condition)
                radio_si = QRadioButton("SI")
                radio_no = QRadioButton("NO")
                radio_no.setChecked(True)
                group_layout_condition.addWidget(radio_si)
                group_layout_condition.addWidget(radio_no)
                group_box_condition.setMinimumHeight(60)  # Altura mínima
                group_box_condition.setMinimumWidth(100)
                frame_layout.addWidget(group_box_condition, row_index, 1)
                text_edit_comments = QPlainTextEdit(condicion[4] if condicion else '')
                text_edit_comments.setMinimumHeight(60)  # Altura mínima
                text_edit_comments.setMinimumWidth(200)
                frame_layout.addWidget(text_edit_comments, row_index, 2)
                rows.append((line_edit_condition, group_box_condition, text_edit_comments))
            elif row_type == "LINE_EDIT":
                line_edit_condition = QLineEdit(condicion[2] if condicion else '')
                line_edit_condition.setMinimumHeight(60)  # Altura mínima
                line_edit_condition.setMinimumWidth(200)
                frame_layout.addWidget(line_edit_condition, row_index, 0)
                line_edit_actual = QLineEdit(condicion[3] if condicion else '')
                line_edit_actual.setMinimumHeight(60)  # Altura mínima
                line_edit_actual.setMinimumWidth(200)
                frame_layout.addWidget(line_edit_actual, row_index, 1)
                text_edit_comments = QPlainTextEdit(condicion[4] if condicion else '')
                text_edit_comments.setMinimumHeight(60)  # Altura mínima
                text_edit_comments.setMinimumWidth(200)
                frame_layout.addWidget(text_edit_comments, row_index, 2)
                rows.append((line_edit_condition, line_edit_actual, text_edit_comments))
        # Botones para agregar filas dinámicas
        button1.clicked.connect(lambda: add_row("CUMPLE_NO_CUMPLE"))
        button2.clicked.connect(lambda: add_row("SI_NO"))
        button3.clicked.connect(lambda: add_row("LINE_EDIT"))
        # Agregar filas iniciales
        def add_initial_rows():
            if condiciones_fisicas:
                for condicion in condiciones_fisicas:
                    # Se revisa el valor de la última posición (7) para determinar el tipo de fila
                    if condicion[5] == 1:  # CUMPLE/NO CUMPLE
                        add_row("CUMPLE_NO_CUMPLE", condicion)
                    elif condicion[5] == 2:  # SI/NO
                        add_row("SI_NO", condicion)
                    elif condicion[5] == 3:  # NORMAL
                        add_row("LINE_EDIT", condicion)
            else:
                # Si no hay condiciones, agregar filas por defecto
                add_row("CUMPLE_NO_CUMPLE")
                add_row("SI_NO")
                add_row("LINE_EDIT")
                add_row("LINE_EDIT")
                add_row("LINE_EDIT")
                add_row("SI_NO")
                add_row("SI_NO")
        add_initial_rows()
        frame.setLayout(frame_layout)
        return frame
    
    # ---------------- Frame OPERATIVIDAD EQUIPOS----------------
    def create_frame_operatividad_A1(componente):
        operatividad_equipos = ReporteController.ctrlObtenerOperatividadEquiposA1(componente)
        frame = QFrame()
        frame_layout = QGridLayout()
        # Título y botón de agregar fila
        title_label = QLabel("OPERATIVIDAD DE EQUIPOS DE MONITOREO")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        add_row_button = QPushButton("Agregar Fila")
        # Layout para el título y el botón
        title_layout = QHBoxLayout()
        title_layout.addWidget(title_label)
        title_layout.addStretch()  # Para empujar el botón al extremo derecho
        title_layout.addWidget(add_row_button)
        # Agregar el título y el botón al layout principal
        frame_layout.addLayout(title_layout, 0, 0, 1, 5)
        # Encabezados de la tabla
        header_instrumentation = QLabel("Instrumentación")
        header_condition = QLabel("Condición Actual")
        header_performance = QLabel("Performance")
        frame_layout.addWidget(header_instrumentation, 1, 0, Qt.AlignCenter)
        frame_layout.addWidget(header_condition, 1, 1, Qt.AlignCenter)
        frame_layout.addWidget(header_performance, 1, 2, 1, 3, Qt.AlignCenter)
        # Subencabezados de Performance
        subheader_quantity = QLabel("Cantidad")
        subheader_operativo = QLabel("Operativo")
        subheader_comments = QLabel("Comentarios")
        frame_layout.addWidget(subheader_quantity, 2, 2, Qt.AlignCenter)
        frame_layout.addWidget(subheader_operativo, 2, 3, Qt.AlignCenter)
        frame_layout.addWidget(subheader_comments, 2, 4, Qt.AlignCenter)
        # Crear filas iniciales
        rows = []
        def add_row(data=None):
            row_index = len(rows) + 3
            # Instrumentación
            line_edit_instrumentation = QLineEdit(data[2] if data else '')
            frame_layout.addWidget(line_edit_instrumentation, row_index, 0)
            # Condición Actual (SI/NO)
            group_box_condition = QGroupBox()
            group_layout_condition = QHBoxLayout(group_box_condition)
            radio_si = QRadioButton("SI")
            radio_no = QRadioButton("NO")
            if data and data[3] == 'SI':
                radio_si.setChecked(True)
            else:
                radio_no.setChecked(True)
            group_layout_condition.addWidget(radio_si)
            group_layout_condition.addWidget(radio_no)
            frame_layout.addWidget(group_box_condition, row_index, 1)
            # Cantidad
            spin_box_quantity = QSpinBox()
            if data and data[5].isdigit():
                spin_box_quantity.setValue(int(data[4]))
            frame_layout.addWidget(spin_box_quantity, row_index, 2)
            # Operativo (Checkbox)
            checkbox_operativo = QCheckBox()
            if data and data[5] == 'SI':
                checkbox_operativo.setChecked(True)
            frame_layout.addWidget(checkbox_operativo, row_index, 3, Qt.AlignCenter)
            # Comentarios
            line_edit_comments = QLineEdit(data[6] if data else '')
            frame_layout.addWidget(line_edit_comments, row_index, 4)
            # Guardar la fila
            rows.append({
                "instrumentation": line_edit_instrumentation,
                "condition": group_box_condition,
                "quantity": spin_box_quantity,
                "operativo": checkbox_operativo,
                "comments": line_edit_comments,
            })
        # Si hay parámetros, crear filas a partir de ellos
        if operatividad_equipos:
            for equipo in operatividad_equipos:
                add_row(equipo)
        else:
            # Si no hay parámetros, agregar una fila vacía inicial
            add_row()
        # Conectar el botón para agregar filas dinámicamente
        add_row_button.clicked.connect(add_row)
        frame.setLayout(frame_layout)
        return frame
    
    # ---------------- Frame OBSERVACIONES----------------
    def create_frame_observaciones_A1(componente):
        observaciones_anexo1 = ReporteController.ctrlObtenerObservacionesA1(componente)
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
            # Agregar una fila con SI/NO en Condición Actual
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
            # Agregar una fila con solo QPlainTextEdit en Comentarios
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
            if observaciones_anexo1:
                for observacion in observaciones_anexo1:
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
    
    def obtener_valores_frame1(widget_anexo1):
        # Buscar el layout principal del widget
        layout = widget_anexo1.layout()
        # Acceder al primer frame (frame1)
        frame1 = layout.itemAt(0).widget()  # El primer widget en el layout debería ser frame1
        texto, id_seleccionado = "", 6
        if isinstance(frame1, QFrame):
            # Obtener el único QPlainTextEdit y QComboBox dentro del frame
            text_edit = frame1.findChild(QPlainTextEdit)
            combo_box = frame1.findChild(QComboBox)
            if text_edit and combo_box:
                # Obtener valores
                texto = text_edit.toPlainText()
                texto_combo = combo_box.currentText()
                id_seleccionado = combo_box.currentData()
        return texto, id_seleccionado
    
    def obtener_valores_frame2(widget):
        # Buscar el layout principal del widget
        layout = widget.layout()

        # Acceder al segundo frame (frame2)
        frame2 = layout.itemAt(1).widget()  # El segundo widget en el layout (índice 1) debería ser frame2

        # Verificar si el widget encontrado es un QFrame
        if isinstance(frame2, QFrame):
            # Obtener los valores dentro de frame2
            valores = {
                "line_edits": [],  # Lista de valores de QLineEdit
                "plain_text_edits": [],  # Lista de textos de QPlainTextEdit
                "radio_buttons": []  # Lista de estados de QRadioButton (True = Sí, False = No)
            }

            # Buscar todos los widgets relevantes dentro de frame2
            line_edits = frame2.findChildren(QLineEdit)
            plain_text_edits = frame2.findChildren(QPlainTextEdit)
            group_boxes = frame2.findChildren(QGroupBox)

            # Obtener valores de QLineEdit
            for line_edit in line_edits:
                valores["line_edits"].append(line_edit.text())

            # Obtener valores de QPlainTextEdit
            for plain_text_edit in plain_text_edits:
                valores["plain_text_edits"].append(plain_text_edit.toPlainText())

            # Obtener estados de los QRadioButton dentro de QGroupBox
            for group_box in group_boxes:
                radio_buttons = group_box.findChildren(QRadioButton)
                for radio_button in radio_buttons:
                    if radio_button.isChecked():
                        valores["radio_buttons"].append(radio_button.text() == "Sí")
                        break  # Solo uno estará marcado por grupo
            return valores

        return None  # Si no se encuentra un QFrame, retornar None

    def obtener_valores_frame_parametros_A1(widget):
        # Buscar el layout principal del widget
        layout = widget.layout()

        # Acceder al frame3 (que está dentro del layout, en el índice 2)
        frame = layout.itemAt(0).widget()  # Obtener el frame3 (índice 2)

        # Obtener el layout dentro de frame3
        frame_layout = frame.layout()

        # Lista para almacenar los valores de las filas
        valores = []

        # Recorremos las filas, comenzando desde la fila 2 (porque la fila 1 tiene los encabezados)
        for i in range(2, frame_layout.rowCount()):
            row_values = []

            # Celda 0: QLineEdit (DESCRIPCIÓN)
            line_edit_desc = frame_layout.itemAtPosition(i, 0).widget()
            descripcion = line_edit_desc.text() if line_edit_desc else ""

            # Verificamos si la descripción está vacía; si es así, no consideramos la fila
            if not descripcion:
                continue  # Saltamos esta iteración si la descripción está vacía

            row_values.append(descripcion)

            # Celda 1: QLineEdit (PARÁMETRO 1)
            line_edit_param1 = frame_layout.itemAtPosition(i, 1).widget()
            row_values.append(line_edit_param1.text() if line_edit_param1 else "")

            # Celda 2: QLineEdit (PARÁMETRO 2)
            line_edit_param2 = frame_layout.itemAtPosition(i, 2).widget()
            row_values.append(line_edit_param2.text() if line_edit_param2 else "")

            # Celda 3 y 4: Buscar los QRadioButton en el QGroupBox (CONDICIÓN ACTUAL)
            group_box_condition = frame_layout.itemAtPosition(i, 3).widget()

            # Buscar todos los widgets dentro del group box
            radio_buttons = [widget for widget in group_box_condition.findChildren(QRadioButton)]
            
            # Verificar cuál radio button está seleccionado
            if radio_buttons:
                if any(radio.isChecked() for radio in radio_buttons):
                    # Si alguno está seleccionado, agregar el valor correspondiente
                    selected_radio = next((radio.text() for radio in radio_buttons if radio.isChecked()), "")
                    row_values.append(selected_radio)
                else:
                    row_values.append("")  # Si ninguno está seleccionado, dejamos el valor vacío
            else:
                row_values.append("")  # Si no hay radio buttons, agregamos un valor vacío

            # Celda 5: QPlainTextEdit (COMENTARIOS)
            text_edit_comments = frame_layout.itemAtPosition(i, 5).widget()
            row_values.append(text_edit_comments.toPlainText() if text_edit_comments else "")

            # Añadir los valores de esta fila a la lista de valores
            valores.append(row_values)

        return valores

    def obtener_valores_frame_condiciones_A1(widget):
        # Buscar el layout principal del widget
        layout = widget.layout()

        # Acceder al frame4 (que está dentro del layout, en el índice 3)
        frame = layout.itemAt(1).widget()  # Obtener el frame4 (índice 3)

        # Obtener el layout dentro de frame4
        frame_layout = frame.layout()

        # Lista para almacenar los valores de las filas
        valores = []

        # Recorremos las filas, comenzando desde la fila 2 (porque las filas 0 y 1 son encabezados)
        for i in range(2, frame_layout.rowCount()):
            row_values = []

            # Celda 0: QLineEdit (Condición)
            line_edit_condition = frame_layout.itemAtPosition(i, 0).widget()
            if not line_edit_condition or not line_edit_condition.text().strip():
                # Si la celda está vacía, omitimos esta fila
                continue

            row_values.append(line_edit_condition.text().strip())  # Agregamos el texto del campo Condición

            # Celda 1: Condición Actual (puede ser QGroupBox o QLineEdit dependiendo del tipo de fila)
            condition_widget = frame_layout.itemAtPosition(i, 1).widget()

            tipo = None
            if isinstance(condition_widget, QGroupBox):  # Si es un QGroupBox (con radio buttons)
                # Buscar todos los QRadioButton dentro del group box
                radio_buttons = condition_widget.findChildren(QRadioButton)

                # Verificar cuál está seleccionado
                if any(radio.isChecked() for radio in radio_buttons):
                    selected_radio = next((radio.text() for radio in radio_buttons if radio.isChecked()), "")
                    row_values.append(selected_radio)
                else:
                    row_values.append("")  # Si ninguno está seleccionado, dejamos vacío

                # Determinar tipo según los textos de los radio buttons
                radio_texts = [radio.text().strip().upper() for radio in radio_buttons]
                if "CUMPLE" in radio_texts and "NO CUMPLE" in radio_texts:
                    tipo = 1
                elif "SI" in radio_texts or "SI" in radio_texts and "NO" in radio_texts:
                    tipo = 2

            elif isinstance(condition_widget, QLineEdit):  # Si es un QLineEdit
                row_values.append(condition_widget.text().strip() if condition_widget else "")
                tipo = 3  # Tipo 3: solo inputs de texto

            # Celda 2: QPlainTextEdit (Comentarios)
            text_edit_comments = frame_layout.itemAtPosition(i, 2).widget()
            row_values.append(text_edit_comments.toPlainText().strip() if text_edit_comments else "")

            # Añadir tipo al final de la fila
            row_values.append(tipo)

            # Añadir los valores de esta fila a la lista de valores
            valores.append(row_values)

        return valores

    def obtener_valores_frame_operatividad_A1(widget):
        # Buscar el layout principal del widget
        layout = widget.layout()

        # Acceder al frame5 (que está dentro del layout, en el índice 4)
        frame = layout.itemAt(2).widget()  # Obtener el frame5 (índice 4)

        # Obtener el layout dentro de frame5
        frame_layout = frame.layout()

        # Lista para almacenar los valores de las filas
        valores = []

        # Recorremos las filas, comenzando desde la fila 3 (porque las filas 0, 1 y 2 son encabezados)
        for i in range(3, frame_layout.rowCount()):
            row_values = []

            # Celda 0: QLineEdit (Instrumentación)
            line_edit_instrumentation = frame_layout.itemAtPosition(i, 0).widget()
            if not line_edit_instrumentation or not line_edit_instrumentation.text().strip():
                # Si la celda está vacía, omitimos esta fila
                continue

            row_values.append(line_edit_instrumentation.text().strip())  # Agregar Instrumentación

            # Celda 1: Condición Actual (QGroupBox con radio buttons)
            group_box_condition = frame_layout.itemAtPosition(i, 1).widget()
            radio_buttons = group_box_condition.findChildren(QRadioButton)

            if any(radio.isChecked() for radio in radio_buttons):
                selected_radio = next((radio.text() for radio in radio_buttons if radio.isChecked()), "")
                row_values.append(selected_radio)
            else:
                row_values.append("")  # Si ninguno está seleccionado, dejamos vacío

            # Celda 2: QSpinBox (Cantidad)
            spin_box_quantity = frame_layout.itemAtPosition(i, 2).widget()
            row_values.append(spin_box_quantity.value() if spin_box_quantity else 0)

            # Celda 3: QCheckBox (Operativo)
            checkbox_operativo = frame_layout.itemAtPosition(i, 3).widget()
            row_values.append("SI" if checkbox_operativo.isChecked() else "")  # Marcar como "SI" si está checked, "" si no

            # Celda 4: QLineEdit (Comentarios)
            line_edit_comments = frame_layout.itemAtPosition(i, 4).widget()
            row_values.append(line_edit_comments.text().strip() if line_edit_comments else "")

            # Añadir los valores de esta fila a la lista de valores
            valores.append(row_values)

        return valores

    def obtener_valores_frame_observaciones_A1(widget):
        # Buscar el layout principal del widget
        layout = widget.layout()

        frame = layout.itemAt(3).widget() 

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
