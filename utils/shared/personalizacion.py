from PySide6.QtGui import QPalette
from PySide6.QtCore import Qt, QDateTime, QDate, QTime
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QTreeWidgetItem, QColorDialog, QLabel, QDateTimeEdit, QDateEdit, QTimeEdit,
                            QPushButton, QTreeWidget, QFrame, QComboBox, QSpinBox, QWidget, QHBoxLayout, QDoubleSpinBox, QCheckBox)
from datetime import datetime, date, time 
from utils.common.rutasarchivos import resource_path
from utils.common.metodosGenerales import MetodosGenerales
from controllers.ConfiguracionController import ConfiguracionController

class Personalizacion:
    time_inicio, time_final = None, None
    estadolimpio, metodoLimpieza, combosMarcados = False, "", []
    limpioEstado, limpiezaMetodo, marcadosCombos = False, "", []
    num_checkboxes_marcados, combospincreados, prismaselegidos = 0, [], []
    checkboxes_marcados, spincomboscreados, equiposelegidos = 0, [], []
    ejemin, ejemax, interpri, intersecu, interdias, estadoejey = 0, 0, 0, 0, 0, False
    estaeje, rangoxmin, rangoxmax, interxprim, interxsecu, interyprofu = False, 0, 0, 0, 0, 0
    ejexmintdr, ejexmaxtdr, xpritdr, xsecutdr = 0, 0, 0, 0
    ejeymintdr, ejeymaxtdr, ypritdr, ysecutdr, estadotdrejey = 0, 0, 0, 0, False
    
    def dialogoFiltroFechas(fechainicial, fechafinal):
        Personalizacion.time_inicio, Personalizacion.time_final = None, None
        loader = QUiLoader()        
        ui_file_path = resource_path("ui/filtrofechas.ui")
        ui_file = loader.load(ui_file_path, None)
        dialogo = QDialog()
        dialogo.setWindowTitle("Filtrar por Fechas")
        layout = QVBoxLayout()
        layout.addWidget(ui_file)
        dialogo.setLayout(layout)
        # tools
        labeldias = dialogo.findChild(QLabel, "label_numerodias")
        datetimeinicio = dialogo.findChild(QDateTimeEdit, "datetime_inicio")
        datetimefinal = dialogo.findChild(QDateTimeEdit, "datetime_final")
        botonaceptar = dialogo.findChild(QPushButton, "btn_aceptar")
        formato = "yyyy-MM-dd HH:mm:ss" 
        
        # --- CARGAR FECHAS ACTUALES (CORREGIDO PARA SQL SERVER/SQLITE) ---
        
        # 1. Validar Fecha Inicial
        if isinstance(fechainicial, str):
            datetime_inicial = QDateTime.fromString(fechainicial, formato)
        elif isinstance(fechainicial, datetime):
            # Convertimos objeto datetime de Python a QDateTime de Qt manualmente para evitar errores
            datetime_inicial = QDateTime(fechainicial.year, fechainicial.month, fechainicial.day,
                                         fechainicial.hour, fechainicial.minute, fechainicial.second)
        else:
            datetime_inicial = QDateTime() # Fecha inválida

        # 2. Validar Fecha Final
        if isinstance(fechafinal, str):
            datetime_final = QDateTime.fromString(fechafinal, formato)
        elif isinstance(fechafinal, datetime):
            datetime_final = QDateTime(fechafinal.year, fechafinal.month, fechafinal.day,
                                       fechafinal.hour, fechafinal.minute, fechafinal.second)
        else:
            datetime_final = QDateTime() # Fecha inválida

        # -----------------------------------------------------------------

        if datetime_inicial.isValid() and datetime_final.isValid():
            datetimeinicio.setDateTime(datetime_inicial)
            datetimefinal.setDateTime(datetime_final)
            # Habilitar o deshabilitar el botón según la diferencia           
            diferencia = datetime_inicial.date().daysTo(datetime_final.date())
            labeldias.setText(str(diferencia))
            diferencia_segundos = datetime_inicial.secsTo(datetime_final)
            botonaceptar.setEnabled(diferencia_segundos >= 60)
        else:
            fechaini, fechafin = MetodosGenerales.obtenerRangoFechas(365)
            # Aquí asumimos que obtenerRangoFechas devuelve strings, si devuelve datetime también funcionaría el parseo
            datetime_inicial = QDateTime.fromString(fechaini, formato)
            datetime_final = QDateTime.fromString(fechafin, formato)
            datetimeinicio.setDateTime(datetime_inicial)
            datetimefinal.setDateTime(datetime_final)
            diferencia = datetime_inicial.date().daysTo(datetime_final.date())
            labeldias.setText(str(diferencia))
            diferencia_segundos = datetime_inicial.secsTo(datetime_final)
            botonaceptar.setEnabled(diferencia_segundos >= 60)
            
        # Función para calcular y actualizar la diferencia en días
        def actualizarDiferencia():
            inicio = datetimeinicio.dateTime()
            final = datetimefinal.dateTime()            
            diferencia = inicio.date().daysTo(final.date())
            labeldias.setText(str(diferencia))
            # Habilitar o deshabilitar el botón según la diferencia
            diferencia_segundos = inicio.secsTo(final)
            botonaceptar.setEnabled(diferencia_segundos >= 60)
            
        def devolverFechas():
            Personalizacion.time_inicio = datetimeinicio.dateTime().toString(formato)
            Personalizacion.time_final = datetimefinal.dateTime().toString(formato)
            dialogo.close()
            
        # Conectar las señales de cambio de valor a la función
        datetimeinicio.dateTimeChanged.connect(actualizarDiferencia)
        datetimefinal.dateTimeChanged.connect(actualizarDiferencia)
        botonaceptar.clicked.connect(devolverFechas)
        dialogo.exec()
        return Personalizacion.time_inicio, Personalizacion.time_final
    
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
        treePrismasRegresion = dialogo.findChild(QTreeWidget, "tree_prismas_regresion")
        frameTendencias = dialogo.findChild(QFrame, "frame_tendencias")
        btnAceptarRegresion = dialogo.findChild(QPushButton, "btn_aceptar_regresion")
        btnCancelarRegresion = dialogo.findChild(QPushButton, "btn_cancelar_regresion")
        # crear los checkbox
        treePrismasRegresion.setHeaderLabels(["PRISMAS"])
        for componente, listaprismas in prismasmarcados:
            resultado = MetodosGenerales.ctrlAgruparPrismasSegunTipo(listaprismas)
            for tabla, prismas in resultado.items():
                for nombreprisma in prismas:
                    parent = QTreeWidgetItem(treePrismasRegresion)
                    parent.setText(0, nombreprisma)
                    parent.setText(1, tabla)
                    parent.setFlags(parent.flags() | Qt.ItemIsUserCheckable)
                    parent.setCheckState(0, Qt.Unchecked)
        def aceptarPrismasRegresion():
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
            nombre = parent_item.text(column)
            tipo = parent_item.text(1)
            estado = parent_item.checkState(0)
            if str(estado) == "CheckState.Checked": # marcado
                if Personalizacion.comprobarExisteDatoArreglo(Personalizacion.combospincreados, tipo, nombre) is False:
                    if Personalizacion.num_checkboxes_marcados > 3:
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
        treePrismasRegresion.itemClicked.connect(checkboxChanged)
        btnAceptarRegresion.clicked.connect(aceptarPrismasRegresion)
        btnCancelarRegresion.clicked.connect(cancelarPrismasRegresion)
        dialogo.exec()
        return Personalizacion.prismaselegidos
    
    def dialogoFiltroRegresionEquipos(equiposmarcados, tipoequipos):
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
        treePrismasRegresion = dialogo.findChild(QTreeWidget, "tree_prismas_regresion")
        frameTendencias = dialogo.findChild(QFrame, "frame_tendencias")
        btnAceptarRegresion = dialogo.findChild(QPushButton, "btn_aceptar_regresion")
        btnCancelarRegresion = dialogo.findChild(QPushButton, "btn_cancelar_regresion")
        # crear los checkbox
        treePrismasRegresion.setHeaderLabels([tipoequipos])
        for componente, listaequipos in equiposmarcados:
            for nombreequipo, idintrumento, idequipo in listaequipos:
                parent = QTreeWidgetItem(treePrismasRegresion)
                parent.setText(0, nombreequipo)
                parent.setText(1, idintrumento)
                parent.setFlags(parent.flags() | Qt.ItemIsUserCheckable)
                parent.setCheckState(0, Qt.Unchecked)
        def aceptarPrismasRegresion():
            for idin, nombre, cod in Personalizacion.spincomboscreados:
                combo = dialogo.findChild(QComboBox, f"combo_{nombre}_{idin}")
                spin = dialogo.findChild(QSpinBox, f"spin_{nombre}_{idin}")
                dato = (idin, nombre, cod)
                item = (dato, combo.currentText(), spin.value())
                Personalizacion.equiposelegidos.append(item)
            dialogo.close()
        def cancelarPrismasRegresion():
            dialogo.close()
        def checkboxChanged(parent_item, column):
            nombre = parent_item.text(column)
            idinstru = parent_item.text(1)
            estado = parent_item.checkState(0)
            if str(estado) == "CheckState.Checked": # marcado
                if Personalizacion.comprobarExisteDatoArreglo(Personalizacion.spincomboscreados, idinstru, nombre) is False:
                    if Personalizacion.checkboxes_marcados > 3:
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
        treePrismasRegresion.itemClicked.connect(checkboxChanged)
        btnAceptarRegresion.clicked.connect(aceptarPrismasRegresion)
        btnCancelarRegresion.clicked.connect(cancelarPrismasRegresion)
        dialogo.exec()
        return Personalizacion.equiposelegidos
    
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
        treePrismasRegresion = dialogo.findChild(QTreeWidget, "tree_prismas_regresion")
        frameTendencias = dialogo.findChild(QFrame, "frame_tendencias")
        btnAceptarRegresion = dialogo.findChild(QPushButton, "btn_aceptar_regresion")
        btnCancelarRegresion = dialogo.findChild(QPushButton, "btn_cancelar_regresion")
        # crear los checkbox
        treePrismasRegresion.setHeaderLabels([tipoequipos])
        for componente, equipo in equiposmarcados:
            parent = QTreeWidgetItem(treePrismasRegresion)
            parent.setText(0, equipo[0])
            parent.setText(1, equipo[1])
            parent.setFlags(parent.flags() | Qt.ItemIsUserCheckable)
            parent.setCheckState(0, Qt.Unchecked)
        def aceptarPrismasRegresion():
            for idin, nombre, cod in Personalizacion.spincomboscreados:
                combo = dialogo.findChild(QComboBox, f"combo_{nombre}_{idin}")
                spin = dialogo.findChild(QSpinBox, f"spin_{nombre}_{idin}")
                dato = (idin, nombre, cod)
                item = (dato, combo.currentText(), spin.value())
                Personalizacion.equiposelegidos.append(item)
            dialogo.close()
        def cancelarPrismasRegresion():
            dialogo.close()
        def checkboxChanged(parent_item, column):
            nombre = parent_item.text(column)
            idinstru = parent_item.text(1)
            estado = parent_item.checkState(0)
            if str(estado) == "CheckState.Checked": # marcado
                if Personalizacion.comprobarExisteDatoArreglo(Personalizacion.spincomboscreados, idinstru, nombre) is False:
                    if Personalizacion.checkboxes_marcados > 3:
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
        treePrismasRegresion.itemClicked.connect(checkboxChanged)
        btnAceptarRegresion.clicked.connect(aceptarPrismasRegresion)
        btnCancelarRegresion.clicked.connect(cancelarPrismasRegresion)
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
    
    def dialogoConfiguracionEjes(ejeymin, ejeymax, ejeyprim, ejeysecu, ejexinter, unidad, hora=1):
        Personalizacion.ejemin, Personalizacion.ejemax, Personalizacion.interpri = ejeymin, ejeymax, ejeyprim
        Personalizacion.intersecu, Personalizacion.interdias, Personalizacion.estadoejey = ejeysecu, ejexinter, False
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
        botonResetear = dialogo.findChild(QPushButton, "btn_resetear")
        botonAceptar = dialogo.findChild(QPushButton, "btn_guardar")
        botonCancelar = dialogo.findChild(QPushButton, "btn_cancelar")
        # cargar valores por defecto
        spinminimo.setValue(ejeymin * unidad)
        spinmaximo.setValue(ejeymax * unidad)
        spininterpri.setValue(ejeyprim * unidad)
        spinintersecu.setValue(ejeysecu * unidad)
        spininterdias.setValue(ejexinter * hora)
        # Función para calcular y actualizar la diferencia en días
        def resetear_valores():
            spinminimo.setValue(0)
            spinmaximo.setValue(0)
            spininterpri.setValue(0)
            spinintersecu.setValue(0)
            spininterdias.setValue(0)
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
            Personalizacion.ejemin = valejemin / unidad
            Personalizacion.ejemax = valejemax / unidad
            Personalizacion.interpri = valinterpri / unidad
            Personalizacion.intersecu = valintersecu / unidad
            Personalizacion.interdias = int(valinterdias / hora)
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
        return Personalizacion.estadoejey, Personalizacion.ejemin, Personalizacion.ejemax, Personalizacion.interpri, Personalizacion.intersecu, Personalizacion.interdias
    
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
    