from PySide6.QtGui import QPalette
from PySide6.QtCore import Qt, QDateTime, QDate, QTime, Signal
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QTreeWidgetItem, QColorDialog, QLabel, QDateEdit, QTimeEdit, QPushButton,
    QTreeWidget, QFrame, QComboBox, QSpinBox, QWidget, QHBoxLayout, QDoubleSpinBox, QCheckBox, QCalendarWidget, QListWidget, QLineEdit)
from datetime import datetime, date, time 
from utils.common.rutasarchivos import resource_path
from utils.common.metodosGenerales import MetodosGenerales
from controllers.ConfiguracionController import ConfiguracionController

class TimeWheel(QListWidget):
    def __init__(self, limit, parent=None):
        super().__init__(parent)
        self.setFixedWidth(35)
        self.setFixedHeight(120)
        self.setUniformItemSizes(True)
        self.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        for i in range(limit):
            self.addItem(f"{i:02d}")
            self.item(i).setTextAlignment(Qt.AlignCenter)
        self.setStyleSheet("QListWidget { border: 1px solid #ddd; background: white; color: #333; font-size: 11px; } QListWidget::item:selected { background: #0078d7; color: white; }")

class DateTimePickerPopup(QDialog):
    def __init__(self, parent=None, initial_dt=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.main_frame = QFrame(self)
        self.main_frame.setStyleSheet("QFrame { background: white; border: 1px solid #ccc; border-radius: 6px; }")
        layout = QVBoxLayout(self.main_frame)
        layout.setContentsMargins(5, 5, 5, 5)
        
        body = QHBoxLayout()
        self.calendar = QCalendarWidget()
        self.calendar.setFixedSize(280, 210) 
        
        # --- ESTILO ULTRA-FINO DEL CALENDARIO ---
        self.calendar.setStyleSheet("""
            /* Barra de navegación */
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background-color: #ffffff;
                border-bottom: 1px solid #f2f2f2;
            }

            /* Botones generales de la barra superior */
            QCalendarWidget QToolButton {
                color: #333333;
                background-color: transparent;
                border: none;
                height: 25px;
            }

            /* --- SELECTOR DE MES (COMBO) --- */
            QCalendarWidget QToolButton#qt_calendar_monthbutton {
                font-size: 11px;
                font-weight: bold;
                padding-right: 12px; /* Espacio para nuestra flechita */
                padding-left: 5px;
                margin-right: 2px;
            }

            /* Personalización de la flechita del combo de meses */
            QCalendarWidget QToolButton#qt_calendar_monthbutton::menu-indicator {
                subcontrol-origin: padding;
                subcontrol-position: center right;
                right: 2px; /* Separación del borde derecho */
                top: 0px;   /* Ajuste vertical para alineación perfecta */
                width: 8px;  /* Flechita mucho más pequeña */
                height: 8px;
            }

            /* --- SELECTOR DE AÑO --- */
            QCalendarWidget QToolButton#qt_calendar_yearbutton {
                font-size: 11px;
                font-weight: bold;
                margin-left: 2px;
                padding: 0 5px;
            }

            /* Flechas laterales (Mes anterior/siguiente) */
            QCalendarWidget QToolButton#qt_calendar_prevmonth, 
            QCalendarWidget QToolButton#qt_calendar_nextmonth {
                width: 24px;
                border-radius: 12px;
                qproperty-iconSize: 14px;
            }
            
            QCalendarWidget QToolButton:hover {
                background-color: #f5f5f5;
                border-radius: 4px;
            }

            /* Menú desplegable de meses */
            QCalendarWidget QMenu {
                background-color: white;
                color: #333;
                selection-background-color: #0078d7;
                border: 1px solid #eeeeee;
            }

            /* Grilla de días y números */
            QCalendarWidget QWidget { alternate-background-color: #ffffff; }
            QCalendarWidget QAbstractItemView:enabled {
                color: #444;
                selection-background-color: #0078d7;
                font-size: 11px;
            }
            QCalendarWidget QAbstractItemView:disabled { color: #d0d0d0; }
        """)

        # Configuración de visibilidad
        self.calendar.setHorizontalHeaderFormat(QCalendarWidget.SingleLetterDayNames)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        
        if initial_dt and initial_dt.isValid(): 
            self.calendar.setSelectedDate(initial_dt.date())
        body.addWidget(self.calendar)

        # Lógica de las ruedas de tiempo (TimeWheel)
        time_lay = QHBoxLayout()
        self.h_w = TimeWheel(24); self.m_w = TimeWheel(60); self.s_w = TimeWheel(60)
        t = initial_dt.time() if initial_dt else QTime(0,0,0)
        self.h_w.setCurrentRow(t.hour()); self.m_w.setCurrentRow(t.minute()); self.s_w.setCurrentRow(t.second())
        
        for w, l in zip([self.h_w, self.m_w, self.s_w], ["H", "M", "S"]):
            v = QVBoxLayout(); lbl = QLabel(l); lbl.setAlignment(Qt.AlignCenter); lbl.setStyleSheet("font-size: 9px; color: #999; border:none;")
            v.addWidget(lbl); v.addWidget(w); time_lay.addLayout(v)
        
        body.addLayout(time_lay)
        layout.addLayout(body)
        
        self.btn_apply = QPushButton("Aplicar")
        self.btn_apply.setFixedSize(70, 26)
        self.btn_apply.setCursor(Qt.PointingHandCursor)
        self.btn_apply.setStyleSheet("""
            QPushButton { background: #0078d7; color: white; border-radius: 3px; font-size: 11px; font-weight: bold; }
            QPushButton:hover { background: #005fa3; }
        """)
        self.btn_apply.clicked.connect(self.accept)
        
        bottom_lay = QHBoxLayout(); bottom_lay.addStretch(); bottom_lay.addWidget(self.btn_apply)
        layout.addLayout(bottom_lay)
        QVBoxLayout(self).addWidget(self.main_frame)

    def get_selected_dt(self):
        return QDateTime(self.calendar.selectedDate(), QTime(self.h_w.currentRow(), self.m_w.currentRow(), self.s_w.currentRow()))
    
class CustomDateTimePicker(QWidget):
    dateTimeChanged = Signal()

    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self); layout.setContentsMargins(0,0,0,0); layout.setSpacing(0)
        
        self.line_edit = QLineEdit()
        self.line_edit.setInputMask("99/99/9999 99:99:99") # Formato visual para el usuario
        self.line_edit.setFixedHeight(26)
        self.line_edit.setStyleSheet("QLineEdit { border: 1px solid #ccc; border-radius: 3px 0 0 3px; padding-left: 5px; color: #333; font-size: 11px; }")
        self.line_edit.textChanged.connect(self._check_validity)

        self.btn = QPushButton("📅")
        self.btn.setFixedSize(26, 26)
        self.btn.setStyleSheet("background: #f8f8f8; border: 1px solid #ccc; border-left: none; border-radius: 0 3px 3px 0; color: #666;")
        self.btn.clicked.connect(self.open_picker)
        
        layout.addWidget(self.line_edit); layout.addWidget(self.btn)

    def _check_validity(self):
        if self.dateTime().isValid():
            self.dateTimeChanged.emit()

    def open_picker(self):
        dt = self.dateTime()
        if not dt.isValid(): dt = QDateTime.currentDateTime()
        pop = DateTimePickerPopup(self, dt)
        pos = self.mapToGlobal(self.line_edit.rect().bottomLeft())
        pop.move(pos.x(), pos.y() + 1)
        if pop.exec_():
            self.setDateTime(pop.get_selected_dt())
            self.dateTimeChanged.emit()

    def setDateTime(self, dt):
        if dt.isValid():
            self.line_edit.setText(dt.toString("dd/MM/yyyy HH:mm:ss"))

    def dateTime(self):
        # Siempre parsear desde el formato del input mask
        return QDateTime.fromString(self.line_edit.text(), "dd/MM/yyyy HH:mm:ss")

class Personalizacion:
    time_inicio, time_final = None, None
    estadolimpio, metodoLimpieza, combosMarcados = False, "", []
    limpioEstado, limpiezaMetodo, marcadosCombos = False, "", []
    num_checkboxes_marcados, combospincreados, prismaselegidos = 0, [], []
    checkboxes_marcados, spincomboscreados, equiposelegidos = 0, [], []
    ejemin, ejemax, interpri, intersecu, interdias, rangopreci, interpreci, estadoejey = 0, 0, 0, 0, 0, 0, 0, False
    estaeje, rangoxmin, rangoxmax, interxprim, interxsecu, interyprofu = False, 0, 0, 0, 0, 0
    ejexmintdr, ejexmaxtdr, xpritdr, xsecutdr = 0, 0, 0, 0
    ejeymintdr, ejeymaxtdr, ypritdr, ysecutdr, estadotdrejey = 0, 0, 0, 0, False
    
    @staticmethod
    def dialogoFiltroFechas(fechainicial, fechafinal):
        # Formatos posibles que vienen de SQL o Python
        formato_sql = "yyyy-MM-dd HH:mm:ss"
        
        def parsear_entrada(valor):
            if isinstance(valor, str):
                # Intentar formato SQL primero, si no, otros comunes
                dt = QDateTime.fromString(valor, formato_sql)
                if not dt.isValid(): dt = QDateTime.fromString(valor, "dd/MM/yyyy HH:mm:ss")
                return dt
            elif isinstance(valor, datetime):
                return QDateTime(valor.year, valor.month, valor.day, valor.hour, valor.minute, valor.second)
            return QDateTime()

        dialogo = QDialog()
        dialogo.setWindowTitle("Filtrar Fechas")
        dialogo.setMinimumWidth(500)
        dialogo.setStyleSheet("background-color: white;")
        
        main_layout = QVBoxLayout(dialogo)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Diferencia de días
        header = QHBoxLayout()
        labeldias = QLabel("0")
        labeldias.setStyleSheet("color: #0078d7; font-weight: bold; font-size: 14px;")
        header.addWidget(labeldias); header.addWidget(QLabel("días seleccionados")); header.addStretch()
        main_layout.addLayout(header)

        # Selectores horizontales
        form_layout = QHBoxLayout()
        
        # Inicio
        v1 = QVBoxLayout(); v1.addWidget(QLabel("DESDE")); dt_inicio = CustomDateTimePicker(); v1.addWidget(dt_inicio)
        # Final
        v2 = QVBoxLayout(); v2.addWidget(QLabel("HASTA")); dt_final = CustomDateTimePicker(); v2.addWidget(dt_final)
        
        form_layout.addLayout(v1); form_layout.addSpacing(10); form_layout.addLayout(v2)
        main_layout.addLayout(form_layout)

        # Botones de acción
        btn_layout = QHBoxLayout()
        botoncancelar = QPushButton("Cancelar")
        botoncancelar.clicked.connect(dialogo.reject)
        
        botonaceptar = QPushButton("ACEPTAR Y FILTRAR")
        botonaceptar.setFixedHeight(30)
        botonaceptar.setStyleSheet("""
            QPushButton { background: #0078d7; color: white; font-weight: bold; border-radius: 4px; padding: 0 15px; }
            QPushButton:disabled { background: #f0f0f0; color: #ccc; }
        """)
        
        btn_layout.addStretch(); btn_layout.addWidget(botoncancelar); btn_layout.addWidget(botonaceptar)
        main_layout.addLayout(btn_layout)

        def validar():
            ini = dt_inicio.dateTime()
            fin = dt_final.dateTime()
            if ini.isValid() and fin.isValid():
                labeldias.setText(str(ini.date().daysTo(fin.date())))
                botonaceptar.setEnabled(ini.secsTo(fin) >= 60)
            else:
                botonaceptar.setEnabled(False)

        def devolver():
            # Guardamos en formato SQL para que tu app lo use sin cambios
            Personalizacion.time_inicio = dt_inicio.dateTime().toString(formato_sql)
            Personalizacion.time_final = dt_final.dateTime().toString(formato_sql)
            dialogo.accept() # ESTO CIERRA EL DIALOGO CON EXITO

        dt_inicio.dateTimeChanged.connect(validar)
        dt_final.dateTimeChanged.connect(validar)
        botonaceptar.clicked.connect(devolver)

        # CARGAR FECHAS (IMPORTANTE)
        dt_ini_obj = parsear_entrada(fechainicial)
        dt_fin_obj = parsear_entrada(fechafinal)

        if not dt_ini_obj.isValid():
            # Si fallan, usar MetodosGenerales
            from utils.common.metodosGenerales import MetodosGenerales
            fi, ff = MetodosGenerales.obtenerRangoFechas(365)
            dt_ini_obj = QDateTime.fromString(fi, formato_sql)
            dt_fin_obj = QDateTime.fromString(ff, formato_sql)

        dt_inicio.setDateTime(dt_ini_obj)
        dt_final.setDateTime(dt_fin_obj)
        validar()

        if dialogo.exec() == QDialog.Accepted:
            return Personalizacion.time_inicio, Personalizacion.time_final
        return None, None
    
    def dialogoFiltroHoras(fecha, horainicial, horafinal):
        fechaini, horaini, horafin = None, None, None
        loader = QUiLoader()
        ui_file_path = resource_path("ui/filtrofechahoras.ui")
        ui_file = loader.load(ui_file_path, None)
        dialogo = QDialog()
        dialogo.setWindowTitle("Filtrar por Horas")
        layout = QVBoxLayout()
        layout.addWidget(ui_file)
        dialogo.setLayout(layout)
        # Tools
        labeldias = dialogo.findChild(QLabel, "label_numerohoras")
        datefecha = dialogo.findChild(QDateEdit, "date_fecha")
        timeinicio = dialogo.findChild(QTimeEdit, "time_inicio")
        timefinal = dialogo.findChild(QTimeEdit, "time_final")
        botonaceptar = dialogo.findChild(QPushButton, "btn_aceptar")
        formatofecha = "yyyy-MM-dd"
        formatohoras = "HH:mm:ss"
        
        # --- CARGAR FECHAS Y HORAS ACTUALES (CORREGIDO) ---
        
        # 1. Validar Fecha (Date)
        if isinstance(fecha, str):
            date_inicial = QDate.fromString(fecha, formatofecha)
        elif isinstance(fecha, (datetime, date)): 
            # Si es datetime o date, extraemos componentes
            date_inicial = QDate(fecha.year, fecha.month, fecha.day)
        else:
            date_inicial = QDate()

        # 2. Validar Hora Inicial (Time)
        # Nota: SQL Server a veces devuelve datetime completo, o timedelta, o time.
        if isinstance(horainicial, str):
            time_inicial = QTime.fromString(horainicial, formatohoras)
        elif isinstance(horainicial, (datetime, time)):
            # Si es un objeto de tiempo, extraemos componentes
            # Nota: Si horainicial fuera un datetime completo, esto funciona si tiene atributos hour/minute/second
            time_inicial = QTime(horainicial.hour, horainicial.minute, horainicial.second)
        else:
            time_inicial = QTime()

        # 3. Validar Hora Final (Time)
        if isinstance(horafinal, str):
            time_final = QTime.fromString(horafinal, formatohoras)
        elif isinstance(horafinal, (datetime, time)):
            time_final = QTime(horafinal.hour, horafinal.minute, horafinal.second)
        else:
            time_final = QTime()
            
        # --------------------------------------------------

        if date_inicial.isValid() and time_inicial.isValid() and time_final.isValid():
            datefecha.setDate(date_inicial)
            timeinicio.setTime(time_inicial)
            timefinal.setTime(time_final)
        else:
            fechainici, fechafin = MetodosGenerales.obtenerRangoFechas(365)
            date_inicial = QDate.fromString(fechafin, formatofecha)
            time_inicial = QTime.fromString("00:00:00", formatohoras)
            time_final = QTime.fromString("23:59:59", formatohoras)
            datefecha.setDate(date_inicial)
            timeinicio.setTime(time_inicial)
            timefinal.setTime(time_final)
            
        # Función para calcular diferencia y habilitar el botón
        def actualizarDiferencia():
            inicio = timeinicio.time()
            final = timefinal.time()
            diferencia = inicio.secsTo(final)
            labeldias.setText(f"{diferencia // 60}" if diferencia >= 0 else "0")
            botonaceptar.setEnabled(diferencia >= 60)
            
        # Función para devolver los valores (puedes retornar si deseas)
        def devolverFechas():
            nonlocal fechaini, horaini, horafin
            fechaini = datefecha.date().toString(formatofecha)
            horaini = timeinicio.time().toString(formatohoras)
            horafin = timefinal.time().toString(formatohoras)
            dialogo.close()
            
        # Conectar señales
        timeinicio.timeChanged.connect(actualizarDiferencia)
        timefinal.timeChanged.connect(actualizarDiferencia)
        botonaceptar.clicked.connect(devolverFechas)
        # Ejecutar actualización inicial
        actualizarDiferencia()
        dialogo.exec()
        return fechaini, horaini, horafin
    
    def dialogoLimpiezaRuidoPrismas(prismasmarcados):
        Personalizacion.estadolimpio, Personalizacion.metodoLimpieza, Personalizacion.combosMarcados = False, "", []
        loader = QUiLoader()        
        ui_file_path = resource_path("ui/limpiezaruido.ui")
        ui_file = loader.load(ui_file_path, None)
        dialogo = QDialog()
        dialogo.setWindowTitle("Limpieza de Ruido")
        layout = QVBoxLayout()
        layout.addWidget(ui_file)
        dialogo.setLayout(layout)
        # Acceso a los botones
        labelTitulo = dialogo.findChild(QLabel, "label_tipo_grafica")
        widgetEquipos = dialogo.findChild(QWidget, "widget_equipos")
        comboLiempieza = dialogo.findChild(QComboBox, "combo_tipo_limpieza")
        botonAplicar = dialogo.findChild(QPushButton, "btn_aplicar")
        labelTitulo.setText("Instrumento")
        checkbox_doublespinbox_list = []
        for componente, listaprismas in prismasmarcados:
            resultado = MetodosGenerales.ctrlAgruparPrismasSegunTipo(listaprismas)
            for tabla, prismas in resultado.items():
                for nombreprisma in prismas:
                    checkbox, doublespinbox = Personalizacion.crearFilaLimpieza(widgetEquipos, nombreprisma, comboLiempieza)
                    checkbox_doublespinbox_list.append((checkbox, doublespinbox))
        def procesar_combos_marcados():
            Personalizacion.metodoLimpieza = comboLiempieza.currentText()
            for checkbox, doublespinbox in checkbox_doublespinbox_list:
                if checkbox.isChecked():
                    nombre = checkbox.text()
                    valor = doublespinbox.value()
                    combo_marcado = (nombre, valor)
                    Personalizacion.combosMarcados.append(combo_marcado)
            # validamos si hay marcados
            if len(Personalizacion.combosMarcados) == 0:
                for checkbox, doublespinbox in checkbox_doublespinbox_list:
                    nombre = checkbox.text()
                    valor = doublespinbox.value()
                    combo_marcado = (nombre, valor)
                    Personalizacion.combosMarcados.append(combo_marcado)
            Personalizacion.estadolimpio = True
            dialogo.close()
        # conectar métodos
        botonAplicar.clicked.connect(procesar_combos_marcados)
        dialogo.exec()
        return Personalizacion.estadolimpio, Personalizacion.metodoLimpieza, Personalizacion.combosMarcados
    
    def dialogoLimpiezaRuidoEquipos(equiposmarcados):
        Personalizacion.limpioEstado, Personalizacion.limpiezaMetodo, Personalizacion.marcadosCombos = False, "", []
        loader = QUiLoader()        
        ui_file_path = resource_path("ui/limpiezaruido.ui")
        ui_file = loader.load(ui_file_path, None)
        dialogo = QDialog()
        dialogo.setWindowTitle("Limpieza de Ruido")
        layout = QVBoxLayout()
        layout.addWidget(ui_file)
        dialogo.setLayout(layout)
        # Acceso a los botones
        labelTitulo = dialogo.findChild(QLabel, "label_tipo_grafica")
        widgetEquipos = dialogo.findChild(QWidget, "widget_equipos")
        comboLiempieza = dialogo.findChild(QComboBox, "combo_tipo_limpieza")
        botonAplicar = dialogo.findChild(QPushButton, "btn_aplicar")
        labelTitulo.setText("Equipo")
        checkbox_doublespinbox_list = []
        for componente, equipo in equiposmarcados:
            checkbox, doublespinbox = Personalizacion.crearFilaLimpieza(widgetEquipos, equipo[0], comboLiempieza)
            checkbox_doublespinbox_list.append((checkbox, doublespinbox, equipo[1]))
        def procesar_combos_marcados():
            Personalizacion.limpiezaMetodo = comboLiempieza.currentText()
            for checkbox, doublespinbox, idinstru in checkbox_doublespinbox_list:
                if checkbox.isChecked():
                    valor = doublespinbox.value()
                    combo_marcado = (idinstru, valor)
                    Personalizacion.marcadosCombos.append(combo_marcado)
            # validamos si hay marcados
            if len(Personalizacion.marcadosCombos) == 0:
                for checkbox, doublespinbox, idinstru in checkbox_doublespinbox_list:
                    valor = doublespinbox.value()
                    combo_marcado = (idinstru, valor)
                    Personalizacion.marcadosCombos.append(combo_marcado)
            Personalizacion.limpioEstado = True
            dialogo.close()
        # conectar métodos
        botonAplicar.clicked.connect(procesar_combos_marcados)
        dialogo.exec()
        return Personalizacion.limpioEstado, Personalizacion.limpiezaMetodo, Personalizacion.marcadosCombos
    
    def crearFilaLimpieza(widget, nombre, combotipoLiempieza):
        fila_widget = QWidget()
        checkbox = QCheckBox()
        doublespinbox = QDoubleSpinBox()
        layout = widget.layout()
        if layout is None:
            layout = QVBoxLayout(widget)
            widget.setLayout(layout)
        layout.addWidget(fila_widget)
        fila_widget.setLayout(QHBoxLayout())
        fila_widget.layout().addWidget(checkbox)
        fila_widget.layout().addWidget(doublespinbox)
        # Establecer margen vertical en cero para los widgets de la fila
        fila_widget.layout().setContentsMargins(0, 0, 0, 0)
        checkbox.setText(nombre)
        checkbox.setStyleSheet("QCheckBox { margin-top: 0px; margin-bottom: 0px; }")
        doublespinbox.setStyleSheet("QDoubleSpinBox { margin-top: 0px; margin-bottom: 0px; }")
        doublespinbox.setEnabled(False)
        doublespinbox.setValue(2)
        doublespinbox.setDecimals(5)
        def checkboxToggled(checked):
            if combotipoLiempieza.currentText() == "Limpieza Manual":
                doublespinbox.setEnabled(checked)
            else:
                doublespinbox.setEnabled(False)    
            if checked:
                if combotipoLiempieza.currentText() == "Limpieza Manual":
                    doublespinbox.setValue(2) 
                else:
                    doublespinbox.setValue(2)
            else:
                doublespinbox.setValue(2)
        checkbox.toggled.connect(checkboxToggled)
        return checkbox, doublespinbox
    
    def comprobarExisteDatoArreglo(arreglo, codigo, nombre):
        encontrado = False
        for code, name, id in arreglo:
            if code == codigo and name == nombre:
                encontrado = True
                break
        return encontrado
    
    def obtenerIndexDatoArreglo(arreglo, codigo, nombre):
        index = None
        for indice, (code, name, id) in enumerate(arreglo):
            if code == codigo and name == nombre:
                index = indice
                break
        return index

    @staticmethod
    def aplicarPreferenciasArbol(tree_referencia, preferencias):
        """
        Marca (check) en tree_referencia los nodos que coincidan con las
        tuplas (id_componente, id_instrumentacion) recibidas en 'preferencias'.
        Si id_instrumentacion es None, se marca el componente completo (todos sus hijos).
        Desmarca todo lo demás.
        """
        def limpiar_id(valor):
            if valor is None or str(valor).strip() == "" or str(valor).lower() == "none":
                return None
            try:
                return int(float(valor))
            except Exception:
                return None

        # Construir set de preferencias válidas
        set_prefs = set()
        for p in preferencias:
            if p and len(p) >= 2:
                idz, idi = limpiar_id(p[0]), limpiar_id(p[1])
                if idz is not None:
                    set_prefs.add((idz, idi))

        # ── Bloquear señales para evitar cascada de eventos ──────────
        tree_referencia.blockSignals(True)

        def marcar_hijos(item, id_zona, marcar_todo):
            for i in range(item.childCount()):
                hijo = item.child(i)
                tipo = hijo.text(1).lower()
                id_equipo = limpiar_id(hijo.text(2)) if tipo in ["prisma", "pluviometro"] else None
                estado = Qt.Checked if (marcar_todo or (id_zona, id_equipo) in set_prefs) else Qt.Unchecked
                hijo.setCheckState(0, estado)
                # ✅ FIX CLAVE: sincronizar UserRole+999 con el estado real
                #    para que validarMarcadoCheckbox no calcule transición errónea
                hijo.setData(0, Qt.UserRole + 999, estado)
                marcar_hijos(hijo, id_zona, marcar_todo)

        for i in range(tree_referencia.topLevelItemCount()):
            root = tree_referencia.topLevelItem(i)
            id_zona = limpiar_id(root.text(2))
            marcar_todo_zona = (id_zona, None) in set_prefs
            marcar_hijos(root, id_zona, marcar_todo_zona)

        # ── Refrescar estado de padres según hijos (bottom-up) ───────
        def refrescar_jerarquia(item):
            for k in range(item.childCount()):
                refrescar_jerarquia(item.child(k))
            if item.childCount() > 0:
                sts = [item.child(k).checkState(0) for k in range(item.childCount())]
                if all(s == Qt.Checked for s in sts):
                    estado_padre = Qt.Checked
                elif all(s == Qt.Unchecked for s in sts):
                    estado_padre = Qt.Unchecked
                else:
                    estado_padre = Qt.PartiallyChecked
                item.setCheckState(0, estado_padre)
                # ✅ FIX CLAVE: sincronizar también el nodo padre
                item.setData(0, Qt.UserRole + 999, estado_padre)

        for i in range(tree_referencia.topLevelItemCount()):
            refrescar_jerarquia(tree_referencia.topLevelItem(i))

        # ── Desbloquear señales ──────────────────────────────────────
        tree_referencia.blockSignals(False)

    @staticmethod
    def confirmarAccion(titulo, mensaje, parent=None):
        """
        Muestra un diálogo de confirmación Sí/No estilizado.
        Devuelve True si el usuario confirma, False en caso contrario.
        """
        dialogo = QDialog(parent)
        dialogo.setWindowTitle(titulo)
        dialogo.setFixedSize(360, 170)
        dialogo.setStyleSheet("background-color: #fcfcfc;")

        layout_principal = QVBoxLayout(dialogo)
        layout_principal.setContentsMargins(25, 20, 25, 20)
        layout_principal.setSpacing(15)

        lbl_titulo = QLabel(titulo)
        lbl_titulo.setStyleSheet("color: #2c3e50; font-size: 14px; font-weight: bold; border:none;")
        layout_principal.addWidget(lbl_titulo)

        lbl_mensaje = QLabel(mensaje)
        lbl_mensaje.setWordWrap(True)
        lbl_mensaje.setStyleSheet("color: #34495e; font-size: 11px; border:none;")
        layout_principal.addWidget(lbl_mensaje)

        layout_principal.addStretch()

        botones = QHBoxLayout()
        btn_no = QPushButton("No")
        btn_si = QPushButton("Sí, eliminar")

        btn_no.setStyleSheet("""
            QPushButton { 
                background-color: transparent; color: #7f8c8d; 
                border: 1px solid #bdc3c7; border-radius: 12px; 
                padding: 6px 16px; font-size: 11px; font-weight: bold;
            }
            QPushButton:hover { background-color: #ecf0f1; }
        """)
        btn_si.setStyleSheet("""
            QPushButton { 
                background-color: #e74c3c; color: white; 
                border: none; border-radius: 12px; 
                padding: 6px 16px; font-size: 11px; font-weight: bold;
            }
            QPushButton:hover { background-color: #c0392b; }
            QPushButton:pressed { background-color: #a93226; }
        """)

        btn_no.setCursor(Qt.PointingHandCursor)
        btn_si.setCursor(Qt.PointingHandCursor)

        btn_no.clicked.connect(dialogo.reject)
        btn_si.clicked.connect(dialogo.accept)

        botones.addStretch()
        botones.addWidget(btn_no)
        botones.addWidget(btn_si)
        layout_principal.addLayout(botones)

        return dialogo.exec() == QDialog.Accepted   
    
    def dialogoFiltroRegresionPrismas(prismasmarcados):
        Personalizacion.num_checkboxes_marcados = 0
        Personalizacion.combospincreados = []
        Personalizacion.prismaselegidos = []
        loader = QUiLoader()        
        ui_file_path = resource_path("ui/filtrotendencias.ui")
        ui_file = loader.load(ui_file_path, None)
        dialogo = QDialog()
        dialogo.setWindowTitle("Configuración de Tendencias")
        layout = QVBoxLayout()
        layout.addWidget(ui_file)
        dialogo.setLayout(layout)
        # Acceso a los botones
        checkTodosPrismas = dialogo.findChild(QCheckBox, "check_all_prismas")
        treePrismasRegresion = dialogo.findChild(QTreeWidget, "tree_prismas_regresion")
        frameTendencias = dialogo.findChild(QFrame, "frame_tendencias")
        btnAceptarRegresion = dialogo.findChild(QPushButton, "btn_aceptar_regresion")
        btnCancelarRegresion = dialogo.findChild(QPushButton, "btn_cancelar_regresion")
        # crear los checkbox
        treePrismasRegresion.setHeaderLabels(["PRISMAS"])
        lista_prismas_disponibles = []
        for componente, listaprismas in prismasmarcados:
            resultado = MetodosGenerales.ctrlAgruparPrismasSegunTipo(listaprismas)
            for tabla, prismas in resultado.items():
                for nombreprisma in prismas:
                    parent = QTreeWidgetItem(treePrismasRegresion)
                    parent.setText(0, nombreprisma)
                    parent.setText(1, tabla)
                    parent.setFlags(parent.flags() | Qt.ItemIsUserCheckable)
                    parent.setCheckState(0, Qt.Unchecked)
                    lista_prismas_disponibles.append((tabla, nombreprisma))
        # --- NUEVO: fila única combo+spin para modo "todos" ---
        layout_tend = frameTendencias.layout()
        if layout_tend is None:
            layout_tend = QVBoxLayout(frameTendencias)
            layout_tend.setSpacing(0)
            layout_tend.setAlignment(Qt.AlignTop)
            layout_tend.setContentsMargins(0, 0, 0, 0)
            frameTendencias.setLayout(layout_tend)
        label_todos, combo_todos, spin_todos = Personalizacion.crearComboSpinTendencia("Todos los prismas", "TODOS")
        fila_todos = QWidget()
        fila_todos.setObjectName("widget_modo_todos")
        fila_layout_todos = QHBoxLayout(fila_todos)
        fila_layout_todos.addWidget(label_todos)
        fila_layout_todos.addWidget(combo_todos)
        fila_layout_todos.addWidget(spin_todos)
        fila_layout_todos.setContentsMargins(0, 0, 0, 0)
        layout_tend.addWidget(fila_todos)
        fila_todos.setVisible(False)
        # --------------------------------------------------------
        # --- NUEVO: alternar entre modo individual y modo "todos" ---
        def toggle_modo_todos(checked):
            treePrismasRegresion.setEnabled(not checked)
            fila_todos.setVisible(checked)
            if checked:
                # Limpiar selección individual visual y de datos
                treePrismasRegresion.blockSignals(True)
                root = treePrismasRegresion.invisibleRootItem()
                for i in range(root.childCount()):
                    root.child(i).setCheckState(0, Qt.Unchecked)
                treePrismasRegresion.blockSignals(False)
                for tipo, nombre, cod in list(Personalizacion.combospincreados):
                    w = dialogo.findChild(QWidget, f"widget_{nombre}_{tipo}")
                    if w is not None:
                        layout_tend.removeWidget(w)
                        w.deleteLater()
                Personalizacion.combospincreados.clear()
                Personalizacion.num_checkboxes_marcados = 0
        # ----------------------------------------------------------------
        def aceptarPrismasRegresion():
            Personalizacion.prismaselegidos = []
            if checkTodosPrismas.isChecked():
                # NUEVO: generar un registro de tendencia por cada prisma disponible
                tiporegresion = combo_todos.currentText()
                grado = spin_todos.value()
                for tabla, nombreprisma in lista_prismas_disponibles:
                    dato = (tabla, nombreprisma, 0)
                    item = (dato, tiporegresion, grado)
                    Personalizacion.prismaselegidos.append(item)
            else:
                for tipo, nombre, cod in Personalizacion.combospincreados:
                    combo = dialogo.findChild(QComboBox, f"combo_{nombre}_{tipo}")
                    spin = dialogo.findChild(QSpinBox, f"spin_{nombre}_{tipo}")
                    dato = (tipo, nombre, cod)
                    item = (dato, combo.currentText(), spin.value())
                    Personalizacion.prismaselegidos.append(item)
            dialogo.close()
        def cancelarPrismasRegresion():
            dialogo.close()
        def checkboxChanged(parent_item, column):
            if checkTodosPrismas.isChecked():
                return
            nombre = parent_item.text(column)
            tipo = parent_item.text(1)
            estado = parent_item.checkState(0)
            if str(estado) == "CheckState.Checked": # marcado
                if Personalizacion.comprobarExisteDatoArreglo(Personalizacion.combospincreados, tipo, nombre) is False:
                    if Personalizacion.num_checkboxes_marcados >= 3:
                        parent_item.setCheckState(0, Qt.Unchecked)
                    else:
                        Personalizacion.combospincreados.append((tipo, nombre, 0))
                        label, combobox, spinbox = Personalizacion.crearComboSpinTendencia(nombre, tipo)
                        # mostrar en el frame
                        fila_widget = QWidget()
                        fila_widget.setObjectName(f"widget_{nombre}_{tipo}")
                        fila_layout = QHBoxLayout(fila_widget)  # Crear un layout horizontal para fila_widget
                        fila_layout.addWidget(label)
                        fila_layout.addWidget(combobox)
                        fila_layout.addWidget(spinbox)
                        fila_layout.setContentsMargins(0, 0, 0, 0)  # Establecer márgenes a 0
                        layout = frameTendencias.layout()
                        if layout is None:
                            layout = QVBoxLayout(frameTendencias)
                            layout.setSpacing(0)  # Establecer espaciado a 0
                            layout.setAlignment(Qt.AlignTop)  # Alinear hacia arriba
                            layout.setContentsMargins(0, 0, 0, 0)  # Establecer márgenes a 0
                            frameTendencias.setLayout(layout)
                        layout.addWidget(fila_widget)  # Agregar fila_widget al layout vertical
                        Personalizacion.num_checkboxes_marcados += 1
            else: # desmarcado
                if Personalizacion.comprobarExisteDatoArreglo(Personalizacion.combospincreados, tipo, nombre):
                    posma = Personalizacion.obtenerIndexDatoArreglo(Personalizacion.combospincreados, tipo, nombre)
                    if posma is not None:
                        Personalizacion.combospincreados.pop(posma)
                        Personalizacion.num_checkboxes_marcados -= 1
                    # limpiar frame
                    layout = frameTendencias.layout()
                    fila_widget = dialogo.findChild(QWidget, f"widget_{nombre}_{tipo}")
                    if layout is not None and fila_widget is not None:
                        layout.removeWidget(fila_widget)
                        fila_widget.deleteLater()     
        # conectar señales
        checkTodosPrismas.toggled.connect(toggle_modo_todos)
        treePrismasRegresion.itemClicked.connect(checkboxChanged)
        btnAceptarRegresion.clicked.connect(aceptarPrismasRegresion)
        btnCancelarRegresion.clicked.connect(cancelarPrismasRegresion)
        dialogo.exec()
        return Personalizacion.prismaselegidos
    
    def dialogoFiltroRegresionPiezometrosCeldas(equiposmarcados, tipoequipos):
        Personalizacion.checkboxes_marcados = 0
        Personalizacion.spincomboscreados = []
        Personalizacion.equiposelegidos = []
        loader = QUiLoader()        
        ui_file_path = resource_path("ui/filtrotendencias.ui")
        ui_file = loader.load(ui_file_path, None)
        dialogo = QDialog()
        dialogo.setWindowTitle("Configuración de Tendencias")
        layout = QVBoxLayout()
        layout.addWidget(ui_file)
        dialogo.setLayout(layout)
        # Acceso a los botones
        checkTodosEquipos = dialogo.findChild(QCheckBox, "check_all_prismas")
        treeEquiposRegresion = dialogo.findChild(QTreeWidget, "tree_prismas_regresion")
        frameTendencias = dialogo.findChild(QFrame, "frame_tendencias")
        btnAceptarRegresion = dialogo.findChild(QPushButton, "btn_aceptar_regresion")
        btnCancelarRegresion = dialogo.findChild(QPushButton, "btn_cancelar_regresion")
        # crear los checkbox
        treeEquiposRegresion.setHeaderLabels([tipoequipos])
        lista_equipos_disponibles = []
        for componente, equipo in equiposmarcados:
            parent = QTreeWidgetItem(treeEquiposRegresion)
            parent.setText(0, equipo[0])
            parent.setText(1, equipo[1])
            parent.setFlags(parent.flags() | Qt.ItemIsUserCheckable)
            parent.setCheckState(0, Qt.Unchecked)
            lista_equipos_disponibles.append((equipo[1], equipo[0]))
        # --- fila única combo+spin para modo "todos" ---
        layout_tend = frameTendencias.layout()
        if layout_tend is None:
            layout_tend = QVBoxLayout(frameTendencias)
            layout_tend.setSpacing(0)
            layout_tend.setAlignment(Qt.AlignTop)
            layout_tend.setContentsMargins(0, 0, 0, 0)
            frameTendencias.setLayout(layout_tend)
        label_todos, combo_todos, spin_todos = Personalizacion.crearComboSpinTendencia("Todos los equipos", "TODOS")
        fila_todos = QWidget()
        fila_todos.setObjectName("widget_modo_todos")
        fila_layout_todos = QHBoxLayout(fila_todos)
        fila_layout_todos.addWidget(label_todos)
        fila_layout_todos.addWidget(combo_todos)
        fila_layout_todos.addWidget(spin_todos)
        fila_layout_todos.setContentsMargins(0, 0, 0, 0)
        layout_tend.addWidget(fila_todos)
        fila_todos.setVisible(False)
        # --------------------------------------------------------
        # --- alternar entre modo individual y modo "todos" ---
        def toggle_modo_todos(checked):
            treeEquiposRegresion.setEnabled(not checked)
            fila_todos.setVisible(checked)
            if checked:
                # Limpiar selección individual visual y de datos
                treeEquiposRegresion.blockSignals(True)
                root = treeEquiposRegresion.invisibleRootItem()
                for i in range(root.childCount()):
                    root.child(i).setCheckState(0, Qt.Unchecked)
                treeEquiposRegresion.blockSignals(False)
                for idin, nombre, cod in list(Personalizacion.spincomboscreados):
                    w = dialogo.findChild(QWidget, f"widget_{nombre}_{idin}")
                    if w is not None:
                        layout_tend.removeWidget(w)
                        w.deleteLater()
                Personalizacion.spincomboscreados.clear()
                Personalizacion.checkboxes_marcados = 0
        # ----------------------------------------------------------------
        def aceptarEquiposRegresion():
            Personalizacion.equiposelegidos = []
            if checkTodosEquipos.isChecked():
                # generar un registro de tendencia por cada equipo disponible
                tiporegresion = combo_todos.currentText()
                grado = spin_todos.value()
                for idin, nombreequipo in lista_equipos_disponibles:
                    dato = (idin, nombreequipo, 0)
                    item = (dato, tiporegresion, grado)
                    Personalizacion.equiposelegidos.append(item)
            else:
                for idin, nombre, cod in Personalizacion.spincomboscreados:
                    combo = dialogo.findChild(QComboBox, f"combo_{nombre}_{idin}")
                    spin = dialogo.findChild(QSpinBox, f"spin_{nombre}_{idin}")
                    dato = (idin, nombre, cod)
                    item = (dato, combo.currentText(), spin.value())
                    Personalizacion.equiposelegidos.append(item)
            dialogo.close()
        def cancelarEquiposRegresion():
            dialogo.close()
        def checkboxChanged(parent_item, column):
            if checkTodosEquipos.isChecked():
                return
            nombre = parent_item.text(column)
            idinstru = parent_item.text(1)
            estado = parent_item.checkState(0)
            if str(estado) == "CheckState.Checked": # marcado
                if Personalizacion.comprobarExisteDatoArreglo(Personalizacion.spincomboscreados, idinstru, nombre) is False:
                    if Personalizacion.checkboxes_marcados >= 3:
                        parent_item.setCheckState(0, Qt.Unchecked)
                    else:
                        Personalizacion.spincomboscreados.append((idinstru, nombre, 0))
                        label, combobox, spinbox = Personalizacion.crearComboSpinTendencia(nombre, idinstru)
                        # mostrar en el frame
                        fila_widget = QWidget()
                        fila_widget.setObjectName(f"widget_{nombre}_{idinstru}")
                        fila_layout = QHBoxLayout(fila_widget)  # Crear un layout horizontal para fila_widget
                        fila_layout.addWidget(label)
                        fila_layout.addWidget(combobox)
                        fila_layout.addWidget(spinbox)
                        fila_layout.setContentsMargins(0, 0, 0, 0)  # Establecer márgenes a 0
                        layout = frameTendencias.layout()
                        if layout is None:
                            layout = QVBoxLayout(frameTendencias)
                            layout.setSpacing(0)  # Establecer espaciado a 0
                            layout.setAlignment(Qt.AlignTop)  # Alinear hacia arriba
                            layout.setContentsMargins(0, 0, 0, 0)  # Establecer márgenes a 0
                            frameTendencias.setLayout(layout)
                        layout.addWidget(fila_widget)  # Agregar fila_widget al layout vertical
                        Personalizacion.checkboxes_marcados += 1
            else: # desmarcado
                if Personalizacion.comprobarExisteDatoArreglo(Personalizacion.spincomboscreados, idinstru, nombre):
                    posma = Personalizacion.obtenerIndexDatoArreglo(Personalizacion.spincomboscreados, idinstru, nombre)
                    if posma is not None:
                        Personalizacion.spincomboscreados.pop(posma)
                        Personalizacion.checkboxes_marcados -= 1
                    # limpiar frame
                    layout = frameTendencias.layout()
                    fila_widget = dialogo.findChild(QWidget, f"widget_{nombre}_{idinstru}")
                    if layout is not None and fila_widget is not None:
                        layout.removeWidget(fila_widget)
                        fila_widget.deleteLater()     
        # conectar señales
        checkTodosEquipos.toggled.connect(toggle_modo_todos)
        treeEquiposRegresion.itemClicked.connect(checkboxChanged)
        btnAceptarRegresion.clicked.connect(aceptarEquiposRegresion)
        btnCancelarRegresion.clicked.connect(cancelarEquiposRegresion)
        dialogo.exec()
        return Personalizacion.equiposelegidos
    
    def crearComboSpinTendencia(nombre, tipo):
        # Crear el label
        label = QLabel()
        label.setText(nombre)
        label.setObjectName(f"label_{nombre}_{tipo}")
        # Crear el combobox
        combobox = QComboBox()
        combobox.addItems(["Lineal", "Polinómica", "Media Móvil", "Logarítmica"])
        combobox.setObjectName(f"combo_{nombre}_{tipo}")
        # Crear el spinbox
        spinbox = QSpinBox()
        spinbox.setObjectName(f"spin_{nombre}_{tipo}")
        spinbox.setValue(2)
        spinbox.setEnabled(False)
        def validarSpinBox():
            spinbox.setValue(2)
            if combobox.currentText() == "Lineal":
                spinbox.setEnabled(False)
            elif combobox.currentText() == "Polinómica":
                spinbox.setMinimum(2)
                spinbox.setMaximum(6)
                spinbox.setEnabled(True)
            elif combobox.currentText() == "Media Móvil":
                spinbox.setMinimum(2)
                spinbox.setMaximum(9999)
                spinbox.setEnabled(True)
            else:
                spinbox.setEnabled(False)
        combobox.currentIndexChanged.connect(validarSpinBox)
        return label, combobox, spinbox
    
    def dialogoConfiguracionEjes(ejeymin, ejeymax, ejeyprim, ejeysecu, ejexinter, unidad, rangolluvia, intervalolluvia, hora=1):
        Personalizacion.ejemin, Personalizacion.ejemax, Personalizacion.interpri = ejeymin, ejeymax, ejeyprim
        Personalizacion.intersecu, Personalizacion.interdias, Personalizacion.rangopreci, Personalizacion.interpreci, Personalizacion.estadoejey = ejeysecu, ejexinter, rangolluvia, intervalolluvia, False
        loader = QUiLoader()        
        ui_file_path = resource_path("ui/configuracionejes.ui")
        ui_file = loader.load(ui_file_path, None)
        dialogo = QDialog()
        dialogo.setWindowTitle("Configuración de Ejes")
        layout = QVBoxLayout()
        layout.addWidget(ui_file)
        dialogo.setLayout(layout)
        # Acceso a los botones
        spinminimo = dialogo.findChild(QDoubleSpinBox, "spin_limite_inferior")
        spinmaximo = dialogo.findChild(QDoubleSpinBox, "spin_limite_superior")
        spininterpri = dialogo.findChild(QDoubleSpinBox, "spin_intervalo_primario")
        spinintersecu = dialogo.findChild(QDoubleSpinBox, "spin_intervalo_secundario")
        spininterdias = dialogo.findChild(QSpinBox, "spin_intervalo_dias")
        spinrangolluvia = dialogo.findChild(QSpinBox, "spin_rango_precipitacion")
        spinintervalolluvia = dialogo.findChild(QSpinBox, "spin_intervalo_precipitacion")
        botonResetear = dialogo.findChild(QPushButton, "btn_resetear")
        botonAceptar = dialogo.findChild(QPushButton, "btn_guardar")
        botonCancelar = dialogo.findChild(QPushButton, "btn_cancelar")
        # cargar valores por defecto
        spinminimo.setValue(ejeymin * unidad)
        spinmaximo.setValue(ejeymax * unidad)
        spininterpri.setValue(ejeyprim * unidad)
        spinintersecu.setValue(ejeysecu * unidad)
        spininterdias.setValue(ejexinter * hora)
        spinrangolluvia.setValue(rangolluvia)
        spinintervalolluvia.setValue(intervalolluvia)
        # Función para calcular y actualizar la diferencia en días
        def resetear_valores():
            spinminimo.setValue(0)
            spinmaximo.setValue(0)
            spininterpri.setValue(0)
            spinintersecu.setValue(0)
            spininterdias.setValue(0)
            spinrangolluvia.setValue(0)
            spinintervalolluvia.setValue(0)
            botonAceptar.setEnabled(True)
        def actualizar_diferencia():
            vejemin = spinminimo.value()
            vejemax = spinmaximo.value()
            # Habilitar o deshabilitar el botón según la diferencia
            botonAceptar.setEnabled(vejemax >= vejemin)
        def devolver_ejes():
            valejemin = spinminimo.value()
            valejemax = spinmaximo.value()
            valinterpri = spininterpri.value()
            valintersecu = spinintersecu.value()
            valinterdias = spininterdias.value()
            valrangolluvia = spinrangolluvia.value()
            valintervalolluvia = spinintervalolluvia.value()
            Personalizacion.ejemin = valejemin / unidad
            Personalizacion.ejemax = valejemax / unidad
            Personalizacion.interpri = valinterpri / unidad
            Personalizacion.intersecu = valintersecu / unidad
            Personalizacion.interdias = int(valinterdias / hora)
            Personalizacion.rangopreci = valrangolluvia
            Personalizacion.interpreci = valintervalolluvia
            Personalizacion.estadoejey = True
            dialogo.close()
        def cancelar_ejes():
            dialogo.close()
        # Conectar las señales de cambio de valor
        botonResetear.clicked.connect(resetear_valores)
        spinminimo.valueChanged.connect(actualizar_diferencia)
        spinmaximo.valueChanged.connect(actualizar_diferencia)
        botonAceptar.clicked.connect(devolver_ejes)
        botonCancelar.clicked.connect(cancelar_ejes)
        dialogo.exec()
        return Personalizacion.estadoejey, Personalizacion.ejemin, Personalizacion.ejemax, Personalizacion.interpri, Personalizacion.intersecu, Personalizacion.interdias, Personalizacion.rangopreci, Personalizacion.interpreci
    
    def dialogoConfiguracionEjesInclinometro(ejexmin, ejexmax, ejexprim, ejexsecu, interprofu, unidad):
        Personalizacion.estaeje, Personalizacion.rangoxmin, Personalizacion.rangoxmax = False, ejexmin, ejexmax
        Personalizacion.interxprim, Personalizacion.interxsecu, Personalizacion.interyprofu = ejexprim, ejexsecu, interprofu
        loader = QUiLoader()        
        ui_file_path = resource_path("ui/configuracioninclinoejes.ui")
        ui_file = loader.load(ui_file_path, None)
        dialogo = QDialog()
        dialogo.setWindowTitle("Configuración de Ejes")
        layout = QVBoxLayout()
        layout.addWidget(ui_file)
        dialogo.setLayout(layout)
        # Acceso a los botones
        spinxmin = dialogo.findChild(QDoubleSpinBox, "spin_ejex_inferior")
        spinxmax = dialogo.findChild(QDoubleSpinBox, "spin_ejex_superior")
        spinxprima = dialogo.findChild(QDoubleSpinBox, "spin_ejex_primario")
        spinxsecu = dialogo.findChild(QDoubleSpinBox, "spin_ejex_secundario")
        spinintery = dialogo.findChild(QDoubleSpinBox, "spin_intervalo_ejey")
        # Botones
        botonRestablecer = dialogo.findChild(QPushButton, "btn_restablecer")
        botonAceptar = dialogo.findChild(QPushButton, "btn_guardar")
        botonCancelar = dialogo.findChild(QPushButton, "btn_cancelar")
        # cargar valores por defecto
        spinxmin.setValue(ejexmin * unidad)
        spinxmax.setValue(ejexmax * unidad)
        spinxprima.setValue(ejexprim * unidad)
        spinxsecu.setValue(ejexsecu * unidad)
        spinintery.setValue(interprofu)
        def resetear_valores():
            spinxmin.setValue(0)
            spinxmax.setValue(0)
            spinxprima.setValue(0)
            spinxsecu.setValue(0)
            spinintery.setValue(0)
            botonAceptar.setEnabled(True)
        def actualizar_diferencia():
            vejemin = spinxmin.value()
            vejemax = spinxmax.value()
            # Habilitar o deshabilitar el botón según la diferencia
            botonAceptar.setEnabled(vejemax >= vejemin)
        def devolverEjes():
            valejemin = spinxmin.value()
            valejemax = spinxmax.value()
            valinterpri = spinxprima.value()
            valintersecu = spinxsecu.value()
            valinterprofu = spinintery.value()
            Personalizacion.rangoxmin = valejemin / unidad
            Personalizacion.rangoxmax = valejemax / unidad
            Personalizacion.interxprim = valinterpri / unidad
            Personalizacion.interxsecu = valintersecu / unidad
            Personalizacion.interyprofu = valinterprofu
            Personalizacion.estaeje = True
            dialogo.close()
        def cancelarEjes():
            dialogo.close()
        # Conectar las señales de cambio de valor
        botonRestablecer.clicked.connect(resetear_valores)
        spinxmin.valueChanged.connect(actualizar_diferencia)
        spinxmax.valueChanged.connect(actualizar_diferencia)
        botonAceptar.clicked.connect(devolverEjes)
        botonCancelar.clicked.connect(cancelarEjes)
        dialogo.exec()
        return Personalizacion.estaeje, Personalizacion.rangoxmin, Personalizacion.rangoxmax, Personalizacion.interxprim, Personalizacion.interxsecu, Personalizacion.interyprofu
    
    def dialogoConfiguracionEjesTDR(tipo, ejexmin, ejexmax, ejexprim, ejexsecu, ejeymin, ejeymax, ejeyprim, ejeysecu, unidad):
        Personalizacion.ejexmintdr, Personalizacion.ejexmaxtdr, Personalizacion.xpritdr, Personalizacion.xsecutdr = ejexmin, ejexmax, ejexprim, ejexsecu
        Personalizacion.ejeymintdr, Personalizacion.ejeymaxtdr, Personalizacion.ypritdr = ejeymin, ejeymax, ejeyprim
        Personalizacion.ysecutdr, Personalizacion.estadotdrejey = ejeysecu, False
        loader = QUiLoader()
        ui_file_path = resource_path("ui/configuraciontdrejes.ui")
        ui_file = loader.load(ui_file_path, None)
        dialogo = QDialog()
        dialogo.setWindowTitle("Configuración de Ejes")
        layout = QVBoxLayout()
        layout.addWidget(ui_file)
        dialogo.setLayout(layout)
        # Acceso a los botones
        spinxminimo = dialogo.findChild(QDoubleSpinBox, "spin_ejex_inferior")
        spinxmaximo = dialogo.findChild(QDoubleSpinBox, "spin_ejex_superior")
        spinxprimario = dialogo.findChild(QDoubleSpinBox, "spin_ejex_primario")
        spinxsecunda = dialogo.findChild(QDoubleSpinBox, "spin_ejex_secundario")
        spinyminimo = dialogo.findChild(QDoubleSpinBox, "spin_ejey_inferior")
        spinymaximo = dialogo.findChild(QDoubleSpinBox, "spin_ejey_superior")
        spinyprimario = dialogo.findChild(QDoubleSpinBox, "spin_ejey_primario")
        spinysecunda = dialogo.findChild(QDoubleSpinBox, "spin_ejey_secundario")
        botonResetear = dialogo.findChild(QPushButton, "btn_resetear")
        botonAceptar = dialogo.findChild(QPushButton, "btn_guardar")
        botonCancelar = dialogo.findChild(QPushButton, "btn_cancelar")
        # cargar valores por defecto
        if tipo == "IP":
            spinxminimo.setValue(ejexmin)
            spinxmaximo.setValue(ejexmax)
            spinxprimario.setValue(ejexprim)
            spinxsecunda.setValue(ejexsecu)
            spinyminimo.setValue(ejeymin * unidad)
            spinymaximo.setValue(ejeymax * unidad)
            spinyprimario.setValue(ejeyprim * unidad)
            spinysecunda.setValue(ejeysecu * unidad)
        else:
            spinxminimo.setValue(ejeymin * unidad)
            spinxmaximo.setValue(ejeymax * unidad)
            spinxprimario.setValue(ejeyprim * unidad)
            spinxsecunda.setValue(ejeysecu * unidad)
            spinyminimo.setValue(ejexmin)
            spinymaximo.setValue(ejexmax)
            spinyprimario.setValue(ejexprim)
            spinysecunda.setValue(ejexsecu)
        # Función para calcular y actualizar la diferencia en días
        def resetear_valores():
            spinxminimo.setValue(0)
            spinxmaximo.setValue(0)
            spinxprimario.setValue(0)
            spinxsecunda.setValue(0)
            spinyminimo.setValue(0)
            spinymaximo.setValue(0)
            spinyprimario.setValue(0)
            spinysecunda.setValue(0)
            botonAceptar.setEnabled(True)
        def actualizar_diferencia():
            vejexmin = spinxminimo.value()
            vejexmax = spinxmaximo.value()
            vejeymin = spinxminimo.value()
            vejeymax = spinxmaximo.value()
            if vejexmax >= vejexmin and vejeymax >= vejeymin:
                botonAceptar.setEnabled(True)
            else:
                botonAceptar.setEnabled(False)
        def devolver_ejes():
            valejexmin = spinxminimo.value()
            valejexmax = spinxmaximo.value()
            valejexpri = spinxprimario.value()
            valejexsecu = spinxsecunda.value()
            valejeymin = spinyminimo.value()
            valejeymax = spinymaximo.value()
            valejeypri = spinyprimario.value()
            valejeysecu = spinysecunda.value()
            if tipo == "IP":
                Personalizacion.ejexmintdr = valejexmin
                Personalizacion.ejexmaxtdr = valejexmax
                Personalizacion.xpritdr = valejexpri
                Personalizacion.xsecutdr = valejexsecu
                Personalizacion.ejeymintdr = valejeymin / unidad
                Personalizacion.ejeymaxtdr = valejeymax / unidad
                Personalizacion.ypritdr = valejeypri / unidad
                Personalizacion.ysecutdr = valejeysecu / unidad
            else:
                Personalizacion.ejexmintdr = valejeymin / unidad
                Personalizacion.ejexmaxtdr = valejeymax / unidad
                Personalizacion.xpritdr = valejeypri / unidad
                Personalizacion.xsecutdr = valejeysecu / unidad
                Personalizacion.ejeymintdr = valejexmin
                Personalizacion.ejeymaxtdr = valejexmax
                Personalizacion.ypritdr = valejexpri
                Personalizacion.ysecutdr = valejexsecu
            Personalizacion.estadotdrejey = True
            dialogo.close()
        def cancelar_ejes():
            dialogo.close()
        # Conectar las señales de cambio de valor
        botonResetear.clicked.connect(resetear_valores)
        spinxminimo.valueChanged.connect(actualizar_diferencia)
        spinxmaximo.valueChanged.connect(actualizar_diferencia)
        spinyminimo.valueChanged.connect(actualizar_diferencia)
        spinymaximo.valueChanged.connect(actualizar_diferencia)
        botonAceptar.clicked.connect(devolver_ejes)
        botonCancelar.clicked.connect(cancelar_ejes)
        dialogo.exec()
        return Personalizacion.estadotdrejey, Personalizacion.ejexmintdr, Personalizacion.ejexmaxtdr, Personalizacion.xpritdr, Personalizacion.xsecutdr, Personalizacion.ejeymintdr, Personalizacion.ejeymaxtdr, Personalizacion.ypritdr, Personalizacion.ysecutdr
    
    def personalizarEquipoGrafica(idproyecto, idinstrumento, nombreequipo, tipoequipo, tipoinstru=0):
        loader = QUiLoader()        
        ui_file_path = resource_path("ui/ajustesequipografica.ui")
        ui_file = loader.load(ui_file_path, None)
        dialogo = QDialog()
        dialogo.setWindowTitle("Ajustes de Graficado")
        layout = QVBoxLayout()
        layout.addWidget(ui_file)
        dialogo.setLayout(layout)
        # Obtener elementos para interactuar
        lbltipoequipo = dialogo.findChild(QLabel, "label_tipoequipo")
        lblnombreequipo = dialogo.findChild(QLabel, "label_nombreequipo")
        btncolorlinea = dialogo.findChild(QPushButton, "btn_colorequipo")
        combotipolinea = dialogo.findChild(QComboBox, "combo_tipolinea")
        spingrosorlinea = dialogo.findChild(QDoubleSpinBox, "spin_grosorlinea")
        botonanular = dialogo.findChild(QPushButton, "btn_anular")
        lblmensajeerror = dialogo.findChild(QLabel, "label_mensaje")
        botonguardar = dialogo.findChild(QPushButton, "btn_guardar")
        botoncancelar = dialogo.findChild(QPushButton, "btn_cancelar")
        # cargar combo
        combotipolinea.addItem("Línea continua ___", "-")
        combotipolinea.addItem("Línea discontinua ---", "--")
        combotipolinea.addItem("Línea punteada ...", ":")
        combotipolinea.addItem("Línea punto raya -.-", "-.")
        lbltipoequipo.setText(tipoequipo)
        lblnombreequipo.setText(nombreequipo)
        # traer info de estilo
        datainfo = ConfiguracionController.ctrlTraerEstiloEquipoGrafica(idproyecto, idinstrumento, tipoinstru)
        if datainfo:
            combotipolinea.setCurrentIndex(combotipolinea.findData(datainfo[3]))
            spingrosorlinea.setValue(float(datainfo[4]))
            btncolorlinea.setStyleSheet("background-color: %s" % datainfo[5])
        else:
            spingrosorlinea.setValue(1)
        def cambiarColor():
            colorcito = QColorDialog.getColor()
            if colorcito.isValid():
                btncolorlinea.setStyleSheet("background-color: %s" % colorcito.name())
        def guardarPersonalizacion():
            tipolinea = combotipolinea.currentData()
            grosorlinea = spingrosorlinea.value()
            colorlinea = btncolorlinea.palette().color(QPalette.Button).name()
            if colorlinea != "" and tipolinea != "" and grosorlinea > 0:
                respu = ConfiguracionController.ctrlGuardarEstiloEquipoGrafica(idproyecto, idinstrumento, tipolinea, grosorlinea, colorlinea, tipoinstru)
                if respu:
                    dialogo.close()
                else:
                    lblmensajeerror.setText("Se generó un error al guardar personalización.")
            else:
                lblmensajeerror.setText("Los datos deben ser válidos.")
        def anularPersonalizacion():
            respuesta = ConfiguracionController.ctrlAnularEstiloEquipoGrafica(idproyecto, idinstrumento, tipoinstru)
            if respuesta:
                dialogo.close()
            else:
                lblmensajeerror.setText("Se generó un error al anular personalización.")
        def cancelarPersonalizacion():
            dialogo.close()
        # Inicializar botones
        btncolorlinea.clicked.connect(cambiarColor)
        botonanular.clicked.connect(anularPersonalizacion)
        botonguardar.clicked.connect(guardarPersonalizacion)
        botoncancelar.clicked.connect(cancelarPersonalizacion)
        dialogo.exec()
    
    def personalizarPluviometroGrafica(idproyecto, idinstrumento, nombreequipo, tipoequipo, tipoinstru):
        loader = QUiLoader()        
        ui_file_path = resource_path("ui/ajustepluviometrografica.ui")
        ui_file = loader.load(ui_file_path, None)
        dialogo = QDialog()
        dialogo.setWindowTitle("Ajustes de Graficado")
        layout = QVBoxLayout()
        layout.addWidget(ui_file)
        dialogo.setLayout(layout)
        # Obtener elementos para interactuar
        lbltipoequipo = dialogo.findChild(QLabel, "label_tipoequipo")
        lblnombreequipo = dialogo.findChild(QLabel, "label_nombreequipo")
        spinlimite = dialogo.findChild(QSpinBox, "spin_limite")
        spinintervalo = dialogo.findChild(QSpinBox, "spin_intervalo")
        btncolorlinea = dialogo.findChild(QPushButton, "btn_colorequipo")
        lblmensajeerror = dialogo.findChild(QLabel, "label_mensaje")
        botonguardar = dialogo.findChild(QPushButton, "btn_guardar")
        botoncancelar = dialogo.findChild(QPushButton, "btn_cancelar")
        lbltipoequipo.setText(tipoequipo)
        lblnombreequipo.setText(nombreequipo)
        # traer info de estilo
        datainfo = ConfiguracionController.ctrlTraerEstiloEquipoGrafica(idproyecto, idinstrumento, tipoinstru)
        if datainfo:
            spinlimite.setValue(int(datainfo[3]))
            spinintervalo.setValue(int(datainfo[4]))
            btncolorlinea.setStyleSheet("background-color: %s" % datainfo[5])
        else:
            spinlimite.setValue(100)
            spinintervalo.setValue(20)
        def cambiarColor():
            colorcito = QColorDialog.getColor()
            if colorcito.isValid():
                btncolorlinea.setStyleSheet("background-color: %s" % colorcito.name())
        def guardarPersonalizacion():
            limite = spinlimite.value()
            intervalo = spinintervalo.value()
            colorlinea = btncolorlinea.palette().color(QPalette.Button).name()
            if colorlinea != "" and limite != "" and intervalo > 0:
                respu = ConfiguracionController.ctrlGuardarEstiloEquipoGrafica(idproyecto, idinstrumento, limite, intervalo, colorlinea, tipoinstru)
                if respu:
                    dialogo.close()
                else:
                    lblmensajeerror.setText("Se generó un error al guardar personalización.")
            else:
                lblmensajeerror.setText("Los datos deben ser válidos.")
        def cancelarPersonalizacion():
            dialogo.close()
        # Inicializar botones
        btncolorlinea.clicked.connect(cambiarColor)
        botonguardar.clicked.connect(guardarPersonalizacion)
        botoncancelar.clicked.connect(cancelarPersonalizacion)
        dialogo.exec()
    
    @staticmethod
    def dialogoAgregarNuevaPlantilla(tree_referencia, fn_guardar):
        from PySide6.QtWidgets import QLineEdit 

        def limpiar_id(valor):
            if valor is None or str(valor).strip() == "" or str(valor).lower() == "none":
                return None
            try: return int(float(valor))
            except: return None

        dialogo = QDialog()
        dialogo.setWindowTitle("Nueva Plantilla")
        # Reducimos un poco el tamaño para que no sea tan "exagerado" 
        dialogo.setFixedSize(460, 650) 
        dialogo.setStyleSheet("background-color: #fcfcfc;")
        
        layout_principal = QVBoxLayout(dialogo)
        layout_principal.setContentsMargins(25, 25, 25, 25) # Más aire en los bordes
        layout_principal.setSpacing(12)
        
        # --- Cabecera ---
        lbl_instrucciones = QLabel("Configuración de equipos predeterminados")
        lbl_instrucciones.setStyleSheet("color: #2c3e50; font-size: 14px; font-weight: bold; border:none;")
        layout_principal.addWidget(lbl_instrucciones)

        #Agregar input para el nombre de la plantilla

        lbl_nombre = QLabel("Nombre de la plantilla:")
        lbl_nombre.setStyleSheet("color: #34495e; font-size: 11px; margin-top: 5px;")
        layout_principal.addWidget(lbl_nombre)
            
        input_nombre = QLineEdit()
        input_nombre.setPlaceholderText("Ej: Plantilla Zona Norte, Configuración Semanal...")
        input_nombre.setStyleSheet("""
        QLineEdit {
            border: 2px solid #bdc3c7;
            border-radius: 8px;
            padding: 8px 12px;
            background-color: white;
            color: #2c3e50;
            font-size: 11px;
            }
        QLineEdit:focus {
            border: 2px solid #3498db;
            }
        QLineEdit:hover {
            border: 2px solid #7f8c8d;
            }
            """)
        layout_principal.addWidget(input_nombre)

        # --- Toolbar Estilizada ---
        toolbar = QHBoxLayout()
        btn_all = QPushButton("Marcar todo")
        btn_none = QPushButton("Desmarcar todo")
        
        # Botones tipo "Ghost" (más finos)
        estilo_botones_util = """
            QPushButton { 
                background-color: transparent; color: #5dade2; 
                border: 1px solid #5dade2; border-radius: 12px; 
                padding: 3px 12px; font-size: 10px; font-weight: bold;
            }
            QPushButton:hover { background-color: #5dade2; color: white; }
            QPushButton:pressed { background-color: #3498db; }
        """
        btn_all.setStyleSheet(estilo_botones_util)
        btn_none.setStyleSheet(estilo_botones_util)
        btn_all.setCursor(Qt.PointingHandCursor)
        btn_none.setCursor(Qt.PointingHandCursor)
        
        toolbar.addStretch()
        toolbar.addWidget(btn_all)
        toolbar.addWidget(btn_none)
        layout_principal.addLayout(toolbar)

        # --- Árbol con Estilo Minimalista ---
        tree_config = QTreeWidget()
        tree_config.setHeaderHidden(True)
        tree_config.setColumnCount(3)
        tree_config.setColumnHidden(1, True)
        tree_config.setColumnHidden(2, True)
        tree_config.setIndentation(18)
        
        tree_config.setStyleSheet("""
            QTreeWidget { 
                border: 1px solid #e1e8ed; border-radius: 10px; 
                background-color: white; outline: 0; padding: 5px;
            }
            QTreeWidget::item { 
                padding: 6px; color: #34495e; border-radius: 4px;
            }
            QTreeWidget::item:hover { 
                background-color: #f4f7f6; 
            }
            QTreeWidget::item:selected { 
                background-color: #eaf2f8; color: #2980b9; font-weight: bold;
            }
            QCheckBox::indicator { width: 14px; height: 14px; }
        """)

        # Cargar datos (Lógica original intacta)
        # set_prefs = set()
        # for p in preferencias_actuales:
        #     idz, idi = limpiar_id(p[0]), limpiar_id(p[1])
        #     if idz is not None: set_prefs.add((idz, idi))

        def copiar_y_sincronizar(item_orig, parent_dest, id_zona):
            for i in range(item_orig.childCount()):
                h_orig = item_orig.child(i)
                h_dest = QTreeWidgetItem(parent_dest)
                h_dest.setText(0, h_orig.text(0))
                h_dest.setText(1, h_orig.text(1))
                h_dest.setText(2, h_orig.text(2))
                h_dest.setFlags(h_dest.flags() | Qt.ItemIsUserCheckable)
                tipo = h_orig.text(1).lower()
                id_equipo = limpiar_id(h_orig.text(2)) if tipo in ["prisma", "pluviometro"] else None
                h_dest.setCheckState(0, Qt.Unchecked)
                copiar_y_sincronizar(h_orig, h_dest, id_zona)

        tree_config.blockSignals(True)
        for i in range(tree_referencia.topLevelItemCount()):
            root_orig = tree_referencia.topLevelItem(i)
            id_z = limpiar_id(root_orig.text(2))
            root_dest = QTreeWidgetItem(tree_config)
            root_dest.setText(0, root_orig.text(0)); root_dest.setText(1, root_orig.text(1)); root_dest.setText(2, root_orig.text(2))
            root_dest.setFlags(root_dest.flags() | Qt.ItemIsUserCheckable)
            root_dest.setCheckState(0, Qt.Unchecked)
            copiar_y_sincronizar(root_orig, root_dest, id_z)
        
        def refrescar_jerarquia(item):
            for k in range(item.childCount()): refrescar_jerarquia(item.child(k))
            if item.childCount() > 0:
                sts = [item.child(k).checkState(0) for k in range(item.childCount())]
                item.setCheckState(0, Qt.Checked if all(s == Qt.Checked for s in sts) else Qt.Unchecked if all(s == Qt.Unchecked for s in sts) else Qt.PartiallyChecked)

        for i in range(tree_config.topLevelItemCount()): refrescar_jerarquia(tree_config.topLevelItem(i))
        tree_config.blockSignals(False)

        # --- Lógica de Interacción ---
        def global_check(state):
            tree_config.blockSignals(True)
            for i in range(tree_config.topLevelItemCount()):
                root = tree_config.topLevelItem(i); root.setCheckState(0, state)
                def rec(it, st):
                    for k in range(it.childCount()): it.child(k).setCheckState(0, st); rec(it.child(k), st)
                rec(root, state)
            tree_config.blockSignals(False)

        btn_all.clicked.connect(lambda: global_check(Qt.Checked))
        btn_none.clicked.connect(lambda: global_check(Qt.Unchecked))

        def on_change(item, col):
            tree_config.blockSignals(True)
            def set_h(it, st):
                for k in range(it.childCount()): it.child(k).setCheckState(0, st); set_h(it.child(k), st)
            set_h(item, item.checkState(0))
            def set_p(it):
                p = it.parent()
                if p:
                    sts = [p.child(k).checkState(0) for k in range(p.childCount())]
                    p.setCheckState(0, Qt.Checked if all(s == Qt.Checked for s in sts) else Qt.Unchecked if all(s == Qt.Unchecked for s in sts) else Qt.PartiallyChecked)
                    set_p(p)
            set_p(item); tree_config.blockSignals(False)

        tree_config.itemChanged.connect(on_change)

        # --- Botón Guardar Elegante (Azul Profundo) ---
        btn_save = QPushButton("GUARDAR PLANTILLA")
        btn_save.setFixedHeight(40)
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet("""
            QPushButton { 
                background-color: #2c3e50; color: white; 
                font-size: 12px; font-weight: bold; border-radius: 20px; 
                margin-top: 10px;
            }
            QPushButton:hover { background-color: #34495e; }
            QPushButton:pressed { background-color: #1a252f; }
        """)
        
        def recolectar_y_enviar():
            nombre_plantilla = input_nombre.text().strip()
            if not nombre_plantilla:
                from utils.common.alertas import mostrar_mensaje
                mostrar_mensaje("Validación", "Debe ingresar un nombre para la plantilla", "advertencia")
                input_nombre.setFocus()
                return
            
            res = []
            for i in range(tree_config.topLevelItemCount()):
                it = tree_config.topLevelItem(i); idz = limpiar_id(it.text(2))
                if it.checkState(0) == Qt.Checked: res.append((idz, None))
                elif it.checkState(0) == Qt.PartiallyChecked:
                    def buscar(p):
                        for j in range(p.childCount()):
                            h = p.child(j)
                            if h.text(1).lower() in ["prisma", "pluviometro"] and h.checkState(0) == Qt.Checked:
                                res.append((idz, limpiar_id(h.text(2))))
                            buscar(h)
                    buscar(it)

            if len(res) == 0:
                from utils.common.alertas import mostrar_mensaje
                mostrar_mensaje("Validación", "Debe marcar al menos un equipo para guardar la plantilla", "advertencia")
                return

            if fn_guardar(nombre_plantilla, res): 
                from utils.common.alertas import mostrar_mensaje
                cantidad = len(res)
                texto_equipos = "equipo" if cantidad == 1 else "equipos"
                mostrar_mensaje(
                    "Éxito",
                    f"Plantilla '{nombre_plantilla}' guardada correctamente con {cantidad} {texto_equipos}.",
                    "exito"
                )
                dialogo.accept()

        btn_save.clicked.connect(recolectar_y_enviar)
        layout_principal.addWidget(tree_config)
        layout_principal.addWidget(btn_save)
        
        return dialogo.exec() == QDialog.Accepted

    @staticmethod
    def dialogoConfigurarMarcadoPredeterminado(tree_referencia, preferencias_actuales, fn_guardar):
        def limpiar_id(valor):
            if valor is None or str(valor).strip() == "" or str(valor).lower() == "none":
                return None
            try: return int(float(valor))
            except: return None

        dialogo = QDialog()
        dialogo.setWindowTitle("Plantilla de Selección")
        # Reducimos un poco el tamaño para que no sea tan "exagerado"
        dialogo.setFixedSize(460, 600) 
        dialogo.setStyleSheet("background-color: #fcfcfc;")
        
        layout_principal = QVBoxLayout(dialogo)
        layout_principal.setContentsMargins(25, 25, 25, 25) # Más aire en los bordes
        layout_principal.setSpacing(12)
        
        # --- Cabecera ---
        lbl_instrucciones = QLabel("Configuración de equipos predeterminados")
        lbl_instrucciones.setStyleSheet("color: #2c3e50; font-size: 14px; font-weight: bold; border:none;")
        layout_principal.addWidget(lbl_instrucciones)

        # --- Toolbar Estilizada ---
        toolbar = QHBoxLayout()
        btn_all = QPushButton("Marcar todo")
        btn_none = QPushButton("Desmarcar todo")
        
        # Botones tipo "Ghost" (más finos)
        estilo_botones_util = """
            QPushButton { 
                background-color: transparent; color: #5dade2; 
                border: 1px solid #5dade2; border-radius: 12px; 
                padding: 3px 12px; font-size: 10px; font-weight: bold;
            }
            QPushButton:hover { background-color: #5dade2; color: white; }
            QPushButton:pressed { background-color: #3498db; }
        """
        btn_all.setStyleSheet(estilo_botones_util)
        btn_none.setStyleSheet(estilo_botones_util)
        btn_all.setCursor(Qt.PointingHandCursor)
        btn_none.setCursor(Qt.PointingHandCursor)
        
        toolbar.addStretch()
        toolbar.addWidget(btn_all)
        toolbar.addWidget(btn_none)
        layout_principal.addLayout(toolbar)

        # --- Árbol con Estilo Minimalista ---
        tree_config = QTreeWidget()
        tree_config.setHeaderHidden(True)
        tree_config.setColumnCount(3)
        tree_config.setColumnHidden(1, True)
        tree_config.setColumnHidden(2, True)
        tree_config.setIndentation(18)
        
        tree_config.setStyleSheet("""
            QTreeWidget { 
                border: 1px solid #e1e8ed; border-radius: 10px; 
                background-color: white; outline: 0; padding: 5px;
            }
            QTreeWidget::item { 
                padding: 6px; color: #34495e; border-radius: 4px;
            }
            QTreeWidget::item:hover { 
                background-color: #f4f7f6; 
            }
            QTreeWidget::item:selected { 
                background-color: #eaf2f8; color: #2980b9; font-weight: bold;
            }
            QCheckBox::indicator { width: 14px; height: 14px; }
        """)

        # Cargar datos (Lógica original intacta)
        set_prefs = set()
        for p in preferencias_actuales:
            idz, idi = limpiar_id(p[0]), limpiar_id(p[1])
            if idz is not None: set_prefs.add((idz, idi))

        def copiar_y_sincronizar(item_orig, parent_dest, id_zona):
            for i in range(item_orig.childCount()):
                h_orig = item_orig.child(i)
                h_dest = QTreeWidgetItem(parent_dest)
                h_dest.setText(0, h_orig.text(0))
                h_dest.setText(1, h_orig.text(1))
                h_dest.setText(2, h_orig.text(2))
                h_dest.setFlags(h_dest.flags() | Qt.ItemIsUserCheckable)
                tipo = h_orig.text(1).lower()
                id_equipo = limpiar_id(h_orig.text(2)) if tipo in ["prisma", "pluviometro"] else None
                h_dest.setCheckState(0, Qt.Checked if ((id_zona, id_equipo) in set_prefs or (id_zona, None) in set_prefs) else Qt.Unchecked)
                copiar_y_sincronizar(h_orig, h_dest, id_zona)

        tree_config.blockSignals(True)
        for i in range(tree_referencia.topLevelItemCount()):
            root_orig = tree_referencia.topLevelItem(i)
            id_z = limpiar_id(root_orig.text(2))
            root_dest = QTreeWidgetItem(tree_config)
            root_dest.setText(0, root_orig.text(0)); root_dest.setText(1, root_orig.text(1)); root_dest.setText(2, root_orig.text(2))
            root_dest.setFlags(root_dest.flags() | Qt.ItemIsUserCheckable)
            root_dest.setCheckState(0, Qt.Checked if (id_z, None) in set_prefs else Qt.Unchecked)
            copiar_y_sincronizar(root_orig, root_dest, id_z)
        
        def refrescar_jerarquia(item):
            for k in range(item.childCount()): refrescar_jerarquia(item.child(k))
            if item.childCount() > 0:
                sts = [item.child(k).checkState(0) for k in range(item.childCount())]
                item.setCheckState(0, Qt.Checked if all(s == Qt.Checked for s in sts) else Qt.Unchecked if all(s == Qt.Unchecked for s in sts) else Qt.PartiallyChecked)

        for i in range(tree_config.topLevelItemCount()): refrescar_jerarquia(tree_config.topLevelItem(i))
        tree_config.blockSignals(False)

        # --- Lógica de Interacción ---
        def global_check(state):
            tree_config.blockSignals(True)
            for i in range(tree_config.topLevelItemCount()):
                root = tree_config.topLevelItem(i); root.setCheckState(0, state)
                def rec(it, st):
                    for k in range(it.childCount()): it.child(k).setCheckState(0, st); rec(it.child(k), st)
                rec(root, state)
            tree_config.blockSignals(False)

        btn_all.clicked.connect(lambda: global_check(Qt.Checked))
        btn_none.clicked.connect(lambda: global_check(Qt.Unchecked))

        def on_change(item, col):
            tree_config.blockSignals(True)
            def set_h(it, st):
                for k in range(it.childCount()): it.child(k).setCheckState(0, st); set_h(it.child(k), st)
            set_h(item, item.checkState(0))
            def set_p(it):
                p = it.parent()
                if p:
                    sts = [p.child(k).checkState(0) for k in range(p.childCount())]
                    p.setCheckState(0, Qt.Checked if all(s == Qt.Checked for s in sts) else Qt.Unchecked if all(s == Qt.Unchecked for s in sts) else Qt.PartiallyChecked)
                    set_p(p)
            set_p(item); tree_config.blockSignals(False)

        tree_config.itemChanged.connect(on_change)

        # --- Botón Guardar Elegante (Azul Profundo) ---
        btn_save = QPushButton("GUARDAR CONFIGURACIÓN")
        btn_save.setFixedHeight(40)
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet("""
            QPushButton { 
                background-color: #2c3e50; color: white; 
                font-size: 12px; font-weight: bold; border-radius: 20px; 
                margin-top: 10px;
            }
            QPushButton:hover { background-color: #34495e; }
            QPushButton:pressed { background-color: #1a252f; }
        """)
        
        def recolectar_y_enviar():
            res = []
            for i in range(tree_config.topLevelItemCount()):
                it = tree_config.topLevelItem(i); idz = limpiar_id(it.text(2))
                if it.checkState(0) == Qt.Checked: res.append((idz, None))
                elif it.checkState(0) == Qt.PartiallyChecked:
                    def buscar(p):
                        for j in range(p.childCount()):
                            h = p.child(j)
                            if h.text(1).lower() in ["prisma", "pluviometro"] and h.checkState(0) == Qt.Checked:
                                res.append((idz, limpiar_id(h.text(2))))
                            buscar(h)
                    buscar(it)
            if fn_guardar(res): dialogo.accept()

        btn_save.clicked.connect(recolectar_y_enviar)
        layout_principal.addWidget(tree_config)
        layout_principal.addWidget(btn_save)
        
        return dialogo.exec() == QDialog.Accepted
  

    @staticmethod
    def dialogoConfigurarMarcadoAnalisis(lista_original, preferencias_actuales, fn_guardar, reiniciar):
        # Conjunto de claves ya marcadas
        claves_marcadas = set()
        for pref in preferencias_actuales:
            if pref and len(pref) >= 2:
                clave = pref[1]
                if clave is not None:
                    claves_marcadas.add(int(clave))

        dialogo = QDialog()
        dialogo.setWindowTitle("Ajustes de Selección")
        dialogo.setFixedSize(460, 600)
        dialogo.setStyleSheet("background-color: #fcfcfc;")

        layout_principal = QVBoxLayout(dialogo)
        layout_principal.setContentsMargins(25, 25, 25, 25)
        layout_principal.setSpacing(12)

        # --- Cabecera ---
        lbl_instrucciones = QLabel("Configuración de tipos de gráfica predeterminados")
        lbl_instrucciones.setStyleSheet("color: #2c3e50; font-size: 14px; font-weight: bold; border:none;")
        layout_principal.addWidget(lbl_instrucciones)

        # --- Toolbar Estilizada ---
        toolbar = QHBoxLayout()
        btn_all = QPushButton("Marcar todo")
        btn_none = QPushButton("Desmarcar todo")

        estilo_botones_util = """
            QPushButton { 
                background-color: transparent; color: #5dade2; 
                border: 1px solid #5dade2; border-radius: 12px; 
                padding: 3px 12px; font-size: 10px; font-weight: bold;
            }
            QPushButton:hover { background-color: #5dade2; color: white; }
            QPushButton:pressed { background-color: #3498db; }
        """
        btn_all.setStyleSheet(estilo_botones_util)
        btn_none.setStyleSheet(estilo_botones_util)
        btn_all.setCursor(Qt.PointingHandCursor)
        btn_none.setCursor(Qt.PointingHandCursor)

        toolbar.addStretch()
        toolbar.addWidget(btn_all)
        toolbar.addWidget(btn_none)
        layout_principal.addLayout(toolbar)

        # --- Árbol con Estilo Minimalista (lista plana, sin jerarquía) ---
        tree_config = QTreeWidget()
        tree_config.setHeaderHidden(True)
        tree_config.setColumnCount(2)
        tree_config.setColumnHidden(1, True)  # columna oculta: clave (ej. "VA3D")
        tree_config.setIndentation(18)

        tree_config.setStyleSheet("""
            QTreeWidget { 
                border: 1px solid #e1e8ed; border-radius: 10px; 
                background-color: white; outline: 0; padding: 5px;
            }
            QTreeWidget::item { 
                padding: 6px; color: #34495e; border-radius: 4px;
            }
            QTreeWidget::item:hover { 
                background-color: #f4f7f6; 
            }
            QTreeWidget::item:selected { 
                background-color: #eaf2f8; color: #2980b9; font-weight: bold;
            }
            QCheckBox::indicator { width: 14px; height: 14px; }
        """)

        # --- Construcción del árbol a partir de lista_original ---
        tree_config.blockSignals(True)
        for clave, (col_idx, etiqueta) in lista_original.items():
            item = QTreeWidgetItem(tree_config)
            item.setText(0, etiqueta)   # texto visible
            item.setText(1, str(col_idx))
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(0, Qt.Checked if int(col_idx) in claves_marcadas else Qt.Unchecked)
        tree_config.blockSignals(False)

        # --- Lógica de Interacción ---
        def global_check(state):
            tree_config.blockSignals(True)
            for i in range(tree_config.topLevelItemCount()):
                tree_config.topLevelItem(i).setCheckState(0, state)
            tree_config.blockSignals(False)

        btn_all.clicked.connect(lambda: global_check(Qt.Checked))
        btn_none.clicked.connect(lambda: global_check(Qt.Unchecked))

        # --- Botón Guardar ---
        btn_save = QPushButton("GUARDAR CONFIGURACIÓN")
        btn_save.setFixedHeight(40)
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet("""
            QPushButton { 
                background-color: #2c3e50; color: white; 
                font-size: 12px; font-weight: bold; border-radius: 20px; 
                margin-top: 10px;
            }
            QPushButton:hover { background-color: #34495e; }
            QPushButton:pressed { background-color: #1a252f; }
        """)

        def recolectar_y_enviar():
            res = []
            for i in range(tree_config.topLevelItemCount()):
                item = tree_config.topLevelItem(i)
                if item.checkState(0) == Qt.Checked:
                    res.append(int(item.text(1)))
            # Si no se marcó nada, se guarda lista vacía (sin preferencia = mostrar todo)
            if fn_guardar(res):
                dialogo.accept()
                reiniciar()

        btn_save.clicked.connect(recolectar_y_enviar)
        layout_principal.addWidget(tree_config)
        layout_principal.addWidget(btn_save)
        dialogo.exec()

    @staticmethod
    def dialogoListaPlantillas(id_proyecto, tree_referencia, fn_refrescar=None, modulo="DESPLAZAMIENTO"):
        """
        Muestra un diálogo con la lista de plantillas guardadas.
        """
        dialogo = QDialog()
        dialogo.setWindowTitle("Plantillas Guardadas")
        dialogo.setFixedSize(550, 400)
        dialogo.setStyleSheet("background-color: #fcfcfc;")
        
        layout_principal = QVBoxLayout(dialogo)
        layout_principal.setContentsMargins(25, 25, 25, 25)
        layout_principal.setSpacing(12)
        
        # --- Cabecera ---
        lbl_titulo = QLabel("Mis Plantillas de Selección")
        lbl_titulo.setStyleSheet("color: #2c3e50; font-size: 14px; font-weight: bold; border:none;")
        layout_principal.addWidget(lbl_titulo)
        
        lbl_subtitulo = QLabel("Selecciona una plantilla para aplicar o gestionar")
        lbl_subtitulo.setStyleSheet("color: #7f8c8d; font-size: 11px; border:none; margin-bottom: 5px;")
        layout_principal.addWidget(lbl_subtitulo)
        
        # --- Lista de Plantillas ---
        # ✅ FIX 1: Se elimina "ID" de las cabeceras visibles,
        #    la columna 3 se mantiene oculta con setColumnHidden
        tree_plantillas = QTreeWidget()
        tree_plantillas.setColumnCount(4)
        tree_plantillas.setHeaderLabels(["Nombre", "Fecha Creación", "Equipos", "ID"])
        tree_plantillas.setColumnHidden(3, True)         # ID oculto
        tree_plantillas.header().setVisible(True)
        tree_plantillas.setRootIsDecorated(False)        # ✅ FIX 2: elimina la columna/flecha de árbol vacía
        tree_plantillas.setItemsExpandable(False)        # no hay nodos expandibles
        tree_plantillas.setAlternatingRowColors(True)
        tree_plantillas.setSelectionMode(QTreeWidget.SingleSelection)
        tree_plantillas.setIndentation(0)               # ✅ FIX 2: sin sangría (sin árbol)

        # ✅ FIX 3: Selección azul sólida sin bordes redondeados
        #    Clave: usar "selection-background-color" directo en ::item:selected
        #    y NO usar border-radius en ese estado
        tree_plantillas.setStyleSheet("""
            QTreeWidget {
                border: 1px solid #e1e8ed;
                border-radius: 8px;
                background-color: white;
                outline: 0;
                padding: 3px;
            }
            QTreeWidget::item {
                padding: 6px 8px;
                color: #34495e;
                height: 28px;
            }
            QTreeWidget::item:hover {
                background-color: #ecf0f1;
            }
            QTreeWidget::item:selected {
                background-color: #2980b9;
                color: white;
                font-weight: bold;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 7px 8px;
                border: none;
                font-weight: bold;
                font-size: 11px;
            }
            QHeaderView::section:first {
                border-top-left-radius: 6px;
            }
            QHeaderView::section:last {
                border-top-right-radius: 6px;
            }
        """)
        
        # Ajustar anchos de columnas
        tree_plantillas.setColumnWidth(0, 200)
        tree_plantillas.setColumnWidth(1, 150)
        tree_plantillas.setColumnWidth(2, 80)

        # --- CARGA DESDE BASE DE DATOS ---
        from controllers.InterfazController import InterfazController

        plantillas = InterfazController.ctrlListarPlantillas(id_proyecto, modulo)

        # ✅ FIX 2: blockSignals evita fila "fantasma" al insertar;
        #    cada item se crea directamente con los 4 valores correctos
        tree_plantillas.blockSignals(True)
        if plantillas:
            for nombre, cantidad, fecha, id_plantilla in plantillas:
                item = QTreeWidgetItem()
                item.setText(0, str(nombre))
                item.setText(1, str(fecha))
                item.setText(2, str(cantidad))
                item.setText(3, str(id_plantilla))   # oculto, pero accesible
                tree_plantillas.addTopLevelItem(item) # ✅ addTopLevelItem en lugar de pasar parent en constructor
        tree_plantillas.blockSignals(False)

        if not plantillas:
            lbl_vacio = QLabel("No hay plantillas guardadas para este proyecto")
            lbl_vacio.setStyleSheet("color: #7f8c8d; font-style: italic; border:none;")
            lbl_vacio.setAlignment(Qt.AlignCenter)
            layout_principal.addWidget(lbl_vacio)
            
        layout_principal.addWidget(tree_plantillas)
        
        # --- Toolbar de Acciones ---
        toolbar = QHBoxLayout()
        
        btn_aplicar  = QPushButton("Aplicar Plantilla")
        btn_editar   = QPushButton("Editar")
        btn_eliminar = QPushButton("Eliminar")
        btn_cerrar   = QPushButton("Cerrar")
        
        estilo_btn_accion = """
            QPushButton { 
                background-color: #3498db; color: white; 
                border: none; border-radius: 12px; 
                padding: 6px 16px; font-size: 11px; font-weight: bold;
            }
            QPushButton:hover    { background-color: #2980b9; }
            QPushButton:pressed  { background-color: #21618c; }
            QPushButton:disabled { background-color: #bdc3c7; color: #7f8c8d; }
        """
        estilo_btn_eliminar = """
            QPushButton { 
                background-color: #e74c3c; color: white; 
                border: none; border-radius: 12px; 
                padding: 6px 16px; font-size: 11px; font-weight: bold;
            }
            QPushButton:hover    { background-color: #c0392b; }
            QPushButton:pressed  { background-color: #a93226; }
            QPushButton:disabled { background-color: #bdc3c7; color: #7f8c8d; }
        """
        estilo_btn_cerrar = """
            QPushButton { 
                background-color: transparent; color: #7f8c8d; 
                border: 1px solid #bdc3c7; border-radius: 12px; 
                padding: 6px 16px; font-size: 11px; font-weight: bold;
            }
            QPushButton:hover { background-color: #ecf0f1; }
        """
        
        btn_aplicar.setStyleSheet(estilo_btn_accion)
        btn_editar.setStyleSheet(estilo_btn_accion)
        btn_eliminar.setStyleSheet(estilo_btn_eliminar)
        btn_cerrar.setStyleSheet(estilo_btn_cerrar)
        
        btn_aplicar.setCursor(Qt.PointingHandCursor)
        btn_editar.setCursor(Qt.PointingHandCursor)
        btn_eliminar.setCursor(Qt.PointingHandCursor)
        btn_cerrar.setCursor(Qt.PointingHandCursor)
        
        # Deshabilitar botones hasta que haya selección
        btn_aplicar.setEnabled(False)
        btn_editar.setEnabled(False)
        btn_eliminar.setEnabled(False)
        
        toolbar.addWidget(btn_aplicar)
        toolbar.addWidget(btn_editar)
        toolbar.addWidget(btn_eliminar)
        toolbar.addStretch()
        toolbar.addWidget(btn_cerrar)
        
        layout_principal.addLayout(toolbar)

        # --- Funciones de Interacción ---
        def on_seleccion_cambio():
            hay_seleccion = bool(tree_plantillas.selectedItems())
            btn_aplicar.setEnabled(hay_seleccion)
            btn_editar.setEnabled(hay_seleccion)
            btn_eliminar.setEnabled(hay_seleccion)

        def aplicar_plantilla():
            items = tree_plantillas.selectedItems()
            if not items:
                from utils.common.alertas import mostrar_mensaje
                mostrar_mensaje("Validación", "Debe seleccionar una plantilla", "advertencia")
                return

            id_preferencia = int(items[0].text(3))
            preferencias = InterfazController.ctrlObtenerPreferenciasPorNombre(
                id_proyecto, modulo, id_preferencia
            )

            if tree_referencia is not None:
                Personalizacion.aplicarPreferenciasArbol(tree_referencia, preferencias)

            dialogo.accept()

            if fn_refrescar is not None:
                fn_refrescar()

        def editar_plantilla():
            items = tree_plantillas.selectedItems()
            if not items:
                from utils.common.alertas import mostrar_mensaje
                mostrar_mensaje("Validación", "Debe seleccionar una plantilla", "advertencia")
                return

            item = items[0]
            nombre_actual = item.text(0)

            from PySide6.QtWidgets import QInputDialog
            nuevo_nombre, ok = QInputDialog.getText(
                dialogo, "Editar Plantilla", "Nuevo nombre:", text=nombre_actual
            )
            nuevo_nombre = nuevo_nombre.strip() if nuevo_nombre else ""

            if not ok or not nuevo_nombre or nuevo_nombre == nombre_actual:
                return

            from utils.common.alertas import mostrar_mensaje
            resultado = InterfazController.ctrlRenombrarPlantilla(
                id_proyecto, modulo, nombre_actual, nuevo_nombre
            )
            if resultado:
                item.setText(0, nuevo_nombre)
                mostrar_mensaje("Éxito", "Plantilla renombrada correctamente", "exito")
            else:
                mostrar_mensaje("Error", "No se pudo renombrar la plantilla", "advertencia")

        def eliminar_plantilla():
            items = tree_plantillas.selectedItems()
            if not items:
                from utils.common.alertas import mostrar_mensaje
                mostrar_mensaje("Validación", "Debe seleccionar una plantilla", "advertencia")
                return

            nombre        = items[0].text(0)
            id_preferencia = int(items[0].text(3))

            if Personalizacion.confirmarAccion(
                "Eliminar Plantilla",
                f"¿Estás seguro de eliminar '{nombre}'? Esta acción no se puede deshacer.",
                dialogo
            ):
                if InterfazController.ctrlEliminarPlantilla(id_proyecto, modulo, id_preferencia):
                    idx = tree_plantillas.indexOfTopLevelItem(items[0])
                    tree_plantillas.takeTopLevelItem(idx)
                    from utils.common.alertas import mostrar_mensaje
                    mostrar_mensaje("Éxito", "Plantilla eliminada correctamente", "exito")
                else:
                    from utils.common.alertas import mostrar_mensaje
                    mostrar_mensaje("Error", "No se pudo eliminar la plantilla", "advertencia")

        # --- Conectar señales ---
        tree_plantillas.itemSelectionChanged.connect(on_seleccion_cambio)
        btn_aplicar.clicked.connect(aplicar_plantilla)
        btn_editar.clicked.connect(editar_plantilla)
        btn_eliminar.clicked.connect(eliminar_plantilla)
        btn_cerrar.clicked.connect(dialogo.reject)
        tree_plantillas.itemDoubleClicked.connect(lambda item, col: aplicar_plantilla())

        return dialogo.exec() == QDialog.Accepted
