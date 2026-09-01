import matplotlib
import matplotlib.pyplot as plt
from PySide6.QtWidgets import (QGridLayout, QWidget, QSizePolicy, QScrollArea, QGraphicsSimpleTextItem, QComboBox,
                               QGraphicsTextItem, QPushButton, QLayout, QToolTip, QLabel)
from PySide6.QtCharts import (QChart, QChartView, QPieSeries, QPieSlice, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis)
from PySide6.QtCore import Qt, QMargins, QPoint, QThread, Signal, QRectF
from PySide6.QtGui import QPainter, QColor, QBrush, QFont, QPen
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from utils.shared.loading import LoadingView
from utils.shared.loading import LoadingView
from controllers.DashboardController import DashboardController

class DashboardView():
    estadoPagina = True
    main, nameproyecto = None, "SIN PROYECTO"
    idproyecto = None
    _widgets_referencias = []
    _signals_conectadas = False
    _NOMBRES_EQUIPO_DISPLAY = {
        'Prismas': 'Prismas',
        'Inclinometros': 'Inclinómetros',
        'PiezometrosCuerda': 'Piezómetros Cuerda Vibrante',
        'PiezometrosManual': 'Piezómetros Casagrande',
        'Celdas': 'Celdas',
        'Pluviometros': 'Pluviómetros',
        'Acelerografos': 'Acelerógrafos',
        'SondajesTDR': 'Sondajes TDR',
    }

    def inicializarVistaDashboard(main, idproyecto):
        DashboardView.main = main
        DashboardView.idproyecto = idproyecto
        comboComponentesDashboard = main.findChild(QComboBox, "cb_lista_componentes_dashboard")
        comboComponentesDashboard.clear()
        if DashboardView.idproyecto:
            componentes = DashboardController.ctrlObtenerComponentes(DashboardView.idproyecto)
            if componentes:
                for componente in componentes:
                    comboComponentesDashboard.addItem(componente[2], componente[0])
            DashboardView.dashboardInicial()

        btn_refrescar_dashboard = main.findChild(QPushButton, "btn_refrescar_dashboard")

        # Conectar solo una vez por proceso, sin desconectar (evita el warning)
        if not DashboardView._signals_conectadas:
            btn_refrescar_dashboard.clicked.connect(DashboardView.dashboardInicial)
            comboComponentesDashboard.activated.connect(DashboardView.dashboardInicial)
            DashboardView._signals_conectadas = True

        DashboardView.estadoPagina = False

    def dashboardInicial():
        # Evitar lanzar un thread nuevo mientras el anterior sigue vivo.
        thread_previo = getattr(DashboardView, '_current_thread', None)
        if thread_previo is not None:
            try:
                if thread_previo.isRunning():
                    thread_previo.quit()
                    thread_previo.wait()
            except RuntimeError:
                # El objeto C++ ya fue eliminado (deleteLater ya se ejecutó); ignorar
                pass

        loading = LoadingView.mostrarLoading()
        comboComponentesDashboard = DashboardView.main.findChild(QComboBox, "cb_lista_componentes_dashboard")
        id_componente = comboComponentesDashboard.currentData() if comboComponentesDashboard else None

        nombre_componente = comboComponentesDashboard.currentText() if comboComponentesDashboard and comboComponentesDashboard.currentData() is not None else ""
        label_dashboard = DashboardView.main.findChild(QLabel, "label_dashboard")
        if label_dashboard:
            label_dashboard.setText(f"DASHBOARD {nombre_componente.upper()}")

        def on_threaddashboard_complete(datos):
            DashboardView.construir_dashboard(datos)
            loading.close()

        def on_thread_finished():
            # Limpiar la referencia para no quedarnos con un puntero a un objeto
            # que está a punto de ser destruido por deleteLater()
            if DashboardView._current_thread is prom:
                DashboardView._current_thread = None

        prom = CargarDashboardThread(DashboardView.idproyecto, id_componente)
        DashboardView._current_thread = prom
        prom.task_finishDashboard.connect(
            on_threaddashboard_complete,
            Qt.ConnectionType.QueuedConnection
        )
        prom.finished.connect(on_thread_finished)
        prom.finished.connect(prom.deleteLater)
        prom.start()
        loading.exec()

    def obtener_datos_dashboard(idproyecto, id_componente):
        """Solo trae datos del controlador/BD. NO crea nada de Qt.
        Seguro para ejecutarse dentro de un QThread."""
        instrumentacion = DashboardController.ctrlObtenerInstrumentacionProyecto(idproyecto, id_componente)
        operativos_inoperativos = DashboardController.ctrlObtenerInstrumentacionOIProyecto(idproyecto, id_componente)
        lecturas_prismas = DashboardController.ctrlObtenerLecturasPrismas(idproyecto, 'prismas', id_componente, 'PRISMAS')
        
        try:
            estadoequipos = DashboardController.ctrlObtenerestadoequipos(idproyecto, id_componente)
        except Exception as e:
            print(f"Error al obtener estadoequipos: {e}")
            estadoequipos = []

        return {
            'instrumentacion': instrumentacion,
            'operativos_inoperativos': operativos_inoperativos,
            'lecturas_prismas': lecturas_prismas,
            'estadoequipos': estadoequipos,
        }

    def construir_dashboard(datos):
        """Construye los widgets/gráficos. SIEMPRE debe correr en el hilo principal (GUI thread)."""
        if not datos:
            return
        instrumentacion = datos.get('instrumentacion')
        operativos_inoperativos = datos.get('operativos_inoperativos')
        lecturas_prismas = datos.get('lecturas_prismas')
        estadoequipos = datos.get('estadoequipos')
        

        scroll_area = DashboardView.main.findChild(QScrollArea, "scrollArea")
        if not scroll_area:
            return
        scroll_content = DashboardView.main.findChild(QWidget, "widget_grafica_dashboard")
        if not scroll_content:
            return
        if scroll_content.layout() is None:
            grid_layout = QGridLayout(scroll_content)
        else:
            grid_layout = scroll_content.layout()
            DashboardView.limpiar_layout(grid_layout)
        grid_layout.setSpacing(15)
        grid_layout.setContentsMargins(15, 15, 15, 15)
        chart_functions = [
            (lambda: DashboardView.create_pie_instrumentacion(instrumentacion), 'half'),
            (lambda: DashboardView.create_donut_chart(operativos_inoperativos), 'half'),
            (lambda: DashboardView.create_bar_chart_estados(estadoequipos), 'half'),
            (lambda: DashboardView.create_pie_prismas('Lecturas por Prisma', lecturas_prismas), 'half'),

        ]
        row = 0
        col = 0
        for chart_func, size_type in chart_functions:
            try:
                chart_widget = chart_func()
                if chart_widget is None:
                    continue
                DashboardView._widgets_referencias.append(chart_widget)
                chart_widget.setSizePolicy(
                    QSizePolicy.Policy.Expanding,
                    QSizePolicy.Policy.Expanding
                )
                if size_type == 'full':
                    chart_widget.setMinimumSize(500, 500)
                    grid_layout.addWidget(chart_widget, row, 0, 1, 2)
                    grid_layout.setRowStretch(row, 1)
                    row += 1
                    col = 0
                else:
                    chart_widget.setMinimumSize(400, 400)
                    grid_layout.addWidget(chart_widget, row, col)
                    grid_layout.setColumnStretch(col, 1)
                    grid_layout.setRowStretch(row, 1)
                    col += 1
                    if col > 1:
                        col = 0
                        row += 1
            except Exception as e:
                print(f"Error al crear gráfico: {str(e)}")
        scroll_content.adjustSize()
        scroll_area.setWidgetResizable(True)

    def setup_dashboard():
        """Se usa cuando ya estamos en el hilo principal (botón refrescar / combo)."""
        comboComponentesDashboard = DashboardView.main.findChild(QComboBox, "cb_lista_componentes_dashboard")
        id_componente = comboComponentesDashboard.currentData()
        if id_componente is not None:
            datos = DashboardView.obtener_datos_dashboard(DashboardView.idproyecto, id_componente)
            DashboardView.construir_dashboard(datos)

    def limpiar_layout(layout: QLayout):
        if layout is None:
            return
        
        # Limpiar referencias antes de eliminar widgets
        DashboardView._widgets_referencias.clear()
        
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                # Desconectar señales si es un MplCanvas
                if isinstance(widget, MplCanvas):
                    try:
                        widget.fig.canvas.mpl_disconnect_all()
                        widget.close()
                        plt.close(widget.fig)
                    except:
                        pass
                # Remover y eliminar
                widget.setParent(None)
                widget.deleteLater()
            elif item.layout() is not None:
                DashboardView.limpiar_layout(item.layout())
                item.layout().deleteLater()
    
    def limpiarGraficaDashboard():
        widget_dashboard = DashboardView.main.findChild(QWidget, "widget_grafica_dashboard")
        if widget_dashboard and widget_dashboard.layout():
            DashboardView.limpiar_layout(widget_dashboard.layout())
    
    def reiniciarVistaDashboard(main, proyecto_id, proyecto_name):
        DashboardView.main = main
        DashboardView.idproyecto = proyecto_id
        DashboardView.nameproyecto = proyecto_name
        DashboardView.estadoPagina = True
        DashboardView.limpiarGraficaDashboard()
        # Limpiar referencias
        DashboardView._widgets_referencias.clear()
    
    def show_hover_info(slice_, text_item, hovered, total):
        if hovered:
            # Calcular el porcentaje basado en el valor total
            percentage = (slice_.value() / total) * 100
            # Mostrar el porcentaje o cantidad al pasar el cursor
            text_item.setText(f"{slice_.label()}: {percentage:.2f}%")
        else:
            # Limpiar el texto cuando el cursor ya no está sobre el segmento
            text_item.setText("")

    def create_pie_instrumentacion(data):
        chart = QChart()
        chart.setTitle("Total de Instrumentación")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.legend().setAlignment(Qt.AlignRight)
        if data:
            # Crear la serie del gráfico de tarta
            series = QPieSeries()
            series.setHoleSize(0.35)
            colors = [
                QColor(0xFF0000),  # Rojo
                QColor(0x0000FF),  # Azul
                QColor(0xFFFF00),  # Amarillo
                QColor(0x00FF00),  # Verde claro
                QColor(0x9966FF),  # Violeta
                QColor(0xFFA500),  # Naranja
                QColor(0xC9CBCF),  # Gris claro
                QColor(0x008000),  # Verde
                QColor(0x00FFFF),  # Cyan
                QColor(0xFF00FF),  # Magenta
            ]
            total = sum(data[i] for i in range(len(data)) if i % 2 == 1)
            pares = [(data[i], data[i+1]) for i in range(0, len(data), 2)]
            if total > 0:
                slices = []
                for index, (label, value) in enumerate(pares):
                    value_float = float(value)
                    color = colors[index % len(colors)]
                    slice_ = series.append(f"{label}: {value_float}", value_float)
                    slice_.setLabelVisible(False)
                    slice_.setBrush(color)
                    slices.append(slice_)
                chart.addSeries(series)
                # Crear texto central
                text_item = QGraphicsSimpleTextItem(chart)
                text_item.setText("")
                text_item.setPos(chart.plotArea().center())
                text_item.setZValue(11)
                for slice_ in slices:
                    slice_.hovered.connect(lambda hovered, slice_=slice_, text_item=text_item, total=total:
                        DashboardView.show_hover_info(slice_, text_item, hovered, total))
            else:
                # Caso cuando total = 0: mostrar leyenda con todos los equipos pero torta vacía
                for i, (label, value) in enumerate(pares):
                    color = colors[i % len(colors)]
                    # Crear slice invisible (valor 0) para mostrar en leyenda
                    slice_ = series.append(f"{label}: {value}", 0.001)  # Valor mínimo técnico
                    slice_.setLabelVisible(False)
                    slice_.setBrush(QColor(220, 220, 220))  # Completamente transparente
                    slice_.setPen(QPen(QColor(220, 220, 220)))  # Sin borde
                chart.addSeries(series)
                # Crear texto central indicando que no hay datos
                text_item = QGraphicsSimpleTextItem(chart)
                text_item.setText("Sin Equipos")
                text_item.setPos(chart.plotArea().center())
                text_item.setZValue(11)
                # Crear leyenda personalizada manualmente
                chart.legend().setVisible(True)
                # Limpiar la leyenda automática y crear una personalizada
                legend_items = []
                for i, (label, value) in enumerate(pares):
                    color = colors[i % len(colors)]
                    # Esto asegura que la leyenda muestre los colores correctos
                    marker = chart.legend().markers()[i] if i < len(chart.legend().markers()) else None
                    if marker:
                        marker.setBrush(color)
                        marker.setLabel(f"{label}: 0")
        # Configurar la vista del gráfico
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_view.setMinimumHeight(300)
        return chart_view
    
    def create_donut_chart(operativos_inoperativos):
        series = QPieSeries()
        series.setHoleSize(0.5)

        total = sum(value for _, value in operativos_inoperativos) if operativos_inoperativos else 0

        chart = QChart()

        if operativos_inoperativos and total > 0:
            colors = {
                'Operativos': QColor(0x00CED1),  # Dark Turquoise
                'Inoperativos': QColor(0xFF6347)  # Tomato
            }
            # Crear segmentos a partir de los datos proporcionados
            slices = []
            for label, value in operativos_inoperativos:
                color = colors.get(label, QColor(0x808080))  # Color por defecto si no se encuentra
                # Crear una etiqueta personalizada que incluya la cantidad
                custom_label = f"{label} ({value})"
                slice_ = series.append(custom_label, value)
                slice_.setLabelVisible()
                slice_.setLabelColor(Qt.black)  # Color del texto negro para mejor visibilidad
                slice_.setLabelPosition(QPieSlice.LabelOutside)
                slice_.setBrush(QBrush(color))  # Aplicar el color sólido
                slices.append(slice_)
            # Conectar la señal hovered para resaltar el segmento
            for slice_ in slices:
                slice_.hovered.connect(lambda hovered, slice_=slice_: slice_.setExploded(hovered))
                slice_.setExplodeDistanceFactor(0.05)
            chart.legend().setVisible(True)
        else:
            # Sin datos (lista vacía o todos los valores en 0): dona gris completa + texto centrado
            empty_slice = series.append("Sin datos", 1)
            empty_slice.setLabelVisible(False)  # Ocultar la etiqueta
            empty_slice.setBrush(QColor(220, 220, 220))  # Gris claro
            empty_slice.setPen(QPen(QColor(220, 220, 220)))  # Sin borde
            chart.legend().setVisible(False)
        # Dibujar
        chart.addSeries(series)
        chart.setTitle("Estado de Instrumentación")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.legend().setAlignment(Qt.AlignBottom)
        chart.legend().setFont(QFont("Arial", 10))
        chart.setBackgroundBrush(QBrush(Qt.white))  # Fondo blanco
        chart.setTitleBrush(QBrush(Qt.black))  # Color del título negro
        # Texto centrado cuando no hay datos, igual que en create_pie_instrumentacion
        if total <= 0:
            text_item = QGraphicsSimpleTextItem(chart)
            text_item.setText("Sin Datos")
            text_item.setPos(chart.plotArea().center())
            text_item.setZValue(11)
        # Configurar la vista del gráfico
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_view.setMinimumHeight(400)
        return chart_view
    
    def create_pie_prismas(titulo, data):
        series = QPieSeries()
        series.setHoleSize(0.35)
        if data:
            # Lista de colores para los segmentos
            colors = [
                QColor(0x00CED1), QColor(0xFF6347), QColor(0x7CFC00),
                QColor(0xFFD700), QColor(0x9932CC), QColor(0xFF4500),
                QColor(0x8A2BE2), QColor(0x32CD32), QColor(0xFF69B4),
                QColor(0x1E90FF)
            ]
            # Añadir segmentos a la serie
            for index, (nombre_prisma, total_lecturas) in enumerate(data):
                color = colors[index % len(colors)]
                slice_ = series.append(nombre_prisma, total_lecturas)
                slice_.setBrush(color)
                slice_.setLabelVisible(False)  # Ocultar etiquetas
                # Función para crear hover effect
                def on_hovered(state, slice=slice_, name=nombre_prisma, value=total_lecturas):
                    if state:
                        slice.setExploded(True)
                        slice.setExplodeDistanceFactor(0.05)
                        slice.setLabelVisible(True)
                        slice.setLabel(f"{name}: {value}")
                    else:
                        slice.setExploded(False)
                        slice.setLabelVisible(False)
                # Conectar evento hover
                slice_.hovered.connect(on_hovered)
        else:
            # Agregar un segmento vacío en color gris claro o blanco
            empty_slice = series.append("Sin datos", 1)
            empty_slice.setBrush(QColor(220, 220, 220))  # Gris claro
            empty_slice.setLabelVisible(False)
        # Configurar el gráfico
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle(titulo)
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.legend().hide()  # Ocultar leyenda para más espacio
        # Ajustar márgenes del gráfico para dar un poco más de espacio al texto del hover
        chart.setMargins(QMargins(10, 20, 10, 10))  # Margen superior reducido
        # Configurar la vista del gráfico
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_view.setMinimumHeight(300)
        return chart_view
    
    def create_pie_chart(data):
        chart = QChart()
        chart.setTitle("Instrumentación")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.legend().setAlignment(Qt.AlignBottom)
        chart.legend().setFont(QFont("Arial", 10))
        chart.setBackgroundBrush(QBrush(QColor(0xF5F5F5)))
        # Crear la serie del gráfico de tarta
        series = QPieSeries()
        series.setHoleSize(0.0)
        colors = [
            QColor(0xFF0000),  # Rojo
            QColor(0x0000FF),  # Azul
            QColor(0xFFFF00),  # Amarillo
            QColor(0x00FF00),  # Verde claro
            QColor(0x9966FF),  # Violeta
            QColor(0xFFA500),  # Naranja
            QColor(0xC9CBCF),  # Gris claro
            QColor(0x008000),  # Verde
            QColor(0x00FFFF),  # Cyan
            QColor(0xFF00FF),  # Magenta
        ]
        # Parsear pares [label, valor]
        pares = [(data[i], data[i + 1]) for i in range(0, len(data), 2)]
        total = sum(value for _, value in pares)
        slices = []
        for i, (label, value) in enumerate(pares):
            valor_final = value if total > 0 else 0.0001  # valor mínimo para mostrar algo
            slice_ = series.append(label, valor_final)
            slice_.setLabelVisible()
            slice_.setLabelColor(Qt.white)
            slice_.setLabelPosition(QPieSlice.LabelInsideTangential)
            slice_.setBrush(QBrush(colors[i % len(colors)]))
            slices.append(slice_)
        if total > 0:
            for slice_ in slices:
                slice_.hovered.connect(lambda hovered, slice_=slice_: slice_.setExploded(hovered))
                slice_.setExplodeDistanceFactor(0.05)
        chart.addSeries(series)
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_view.setMinimumHeight(400)
        return chart_view
    
    def resumen_prismas_barras(datos, parent=None):
        if datos:
            # Cerrar figuras anteriores de matplotlib
            plt.close('all')
            canvas = MplCanvas(parent)
            canvas.plot_data(datos)
            return canvas
        return None

    @staticmethod
    def _dividir_etiqueta_dos_lineas(texto):
        """Divide un texto en dos líneas, cortando en el espacio más cercano al centro.
        Devuelve una tupla (linea1, linea2). Si no se puede dividir, linea2 queda vacía."""
        palabras = texto.split()
        if len(palabras) <= 1:
            return (texto, "")
        mitad = len(texto) // 2
        mejor_corte = 1
        menor_diferencia = len(texto)
        acumulado = 0
        for i, palabra in enumerate(palabras[:-1]):
            acumulado += len(palabra) + 1
            diferencia = abs(acumulado - mitad)
            if diferencia < menor_diferencia:
                menor_diferencia = diferencia
                mejor_corte = i + 1
        linea1 = " ".join(palabras[:mejor_corte])
        linea2 = " ".join(palabras[mejor_corte:])
        return (linea1, linea2)

    @staticmethod
    def _dibujar_etiquetas_eje_x(chart, categorias, font_axis):
        """Dibuja manualmente las etiquetas del eje X en diagonal (45°) y en
        hasta dos líneas, ya que QBarCategoryAxis no permite rotar ni partir
        sus labels nativas. El pivote de rotación queda en la esquina
        superior-izquierda del texto: al rotar en sentido horario, el texto
        'cae' hacia abajo-derecha, quedando debajo del eje X y sin invadir
        el área de la gráfica. También reposiciona la leyenda debajo de
        estas etiquetas, calculando el espacio real que ocupan ya rotadas."""
        etiquetas_items = []
        for categoria in categorias:
            linea1, linea2 = DashboardView._dividir_etiqueta_dos_lineas(categoria)
            texto = f"{linea1}\n{linea2}" if linea2 else linea1
            item = QGraphicsTextItem(chart)
            item.setPlainText(texto)
            item.setFont(font_axis)
            item.setDefaultTextColor(QColor("#000000"))
            item.setZValue(20)
            # Pivote en la esquina superior izquierda: el texto queda fijo
            # justo debajo del tick y cae en diagonal hacia abajo-derecha.
            item.setTransformOriginPoint(0, 0)
            item.setRotation(45)
            etiquetas_items.append(item)
        DashboardView._widgets_referencias.extend(etiquetas_items)

        leyenda = chart.legend()
        leyenda.detachFromChart()
        leyenda.setVisible(True)
        leyenda.setBackgroundVisible(False)

        def reposicionar():
            plot_area = chart.plotArea()
            n = len(categorias)
            if n == 0:
                return
            ancho_categoria = plot_area.width() / n
            max_bottom = plot_area.bottom()
            for i, item in enumerate(etiquetas_items):
                centro_x = plot_area.left() + ancho_categoria * (i + 0.5)
                pos_y = plot_area.bottom() + 6
                # El pivote (esquina sup-izquierda) queda anclado al centro
                # de la categoría; con mapRectToParent obtenemos el espacio
                # real que ocupa el texto ya rotado.
                item.setPos(centro_x, pos_y)
                rect = item.boundingRect()
                rotated_rect = item.mapRectToParent(rect)
                max_bottom = max(max_bottom, rotated_rect.bottom())

            alto_leyenda = max(leyenda.geometry().height(), 24)
            leyenda.setGeometry(QRectF(plot_area.left(), max_bottom + 8, plot_area.width(), alto_leyenda))

        reposicionar()
        chart.plotAreaChanged.connect(reposicionar)
    
    @staticmethod
    def create_bar_chart_estados(data):
        """
        data viene como:
        [('Prismas', 'Operativos', 12), ('Prismas', 'Inoperativos', 3), ('Prismas', 'Desactualizados', 5)]
        """
        if not data:
            return None

        # Reorganizar: { tipo_equipo: {categoria: cantidad} }
        resumen = {}
        tipos_equipo_orden = []
        for tipo_equipo_raw, categoria, cantidad in data:
            tipo_equipo = DashboardView._NOMBRES_EQUIPO_DISPLAY.get(tipo_equipo_raw, tipo_equipo_raw)
            if tipo_equipo not in resumen:
                resumen[tipo_equipo] = {}
                tipos_equipo_orden.append(tipo_equipo)
            resumen[tipo_equipo][categoria] = cantidad

        if not tipos_equipo_orden:
            return None

        categorias = ["Operativos", "Inoperativos", "Desactualizados"]
        colores = {
            "Operativos": QColor("#2ecc71"),
            "Inoperativos": QColor("#e74c3c"),
            "Desactualizados": QColor("#f39c12"),
        }

        series = QBarSeries()

        font_labels = QFont()
        font_labels.setBold(True)
        font_labels.setPointSize(10)

        for categoria in categorias:
            bar_set = QBarSet(categoria)
            bar_set.setColor(colores[categoria])
            bar_set.setLabelColor(QColor("#000000"))
            bar_set.setLabelFont(font_labels)
            valores = [resumen.get(tipo, {}).get(categoria, 0) for tipo in tipos_equipo_orden]
            bar_set.append(valores)
            series.append(bar_set)

        series.setLabelsVisible(True)
        series.setLabelsFormat("@value")
        series.setLabelsPosition(QBarSeries.LabelsPosition.LabelsOutsideEnd)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Estado de Equipos")
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        chart.setMargins(QMargins(10, 40, 10, 130))

        font_axis = QFont()
        font_axis.setPointSize(9)

        axisX = QBarCategoryAxis()
        axisX.append(tipos_equipo_orden)
        axisX.setLabelsVisible(False)
        axisX.setTruncateLabels(False)
        chart.addAxis(axisX, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axisX)

        import math
        max_valor = max(
            (resumen.get(tipo, {}).get(cat, 0) for tipo in tipos_equipo_orden for cat in categorias),
            default=0
        )
        tope_eje = math.ceil(max_valor + 1.5) + 10
        axisY = QValueAxis()
        axisY.setMin(0)
        axisY.setMax(tope_eje)
        axisY.setLabelFormat("%d")
        axisY.setTickCount(6)
        chart.addAxis(axisY, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axisY)

        DashboardView._dibujar_etiquetas_eje_x(chart, tipos_equipo_orden, font_axis)

        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        chart_view.setMinimumSize(400, 470)
        return chart_view


class MplCanvas(FigureCanvas):
    def __init__(self, parent=None):
        # Cerrar todas las figuras existentes antes de crear una nueva
        plt.close('all')
        
        self.fig, self.ax = plt.subplots(figsize=(10, 5), tight_layout=True)
        super().__init__(self.fig)
        
        # Establecer el parent DESPUÉS de la inicialización
        if parent is not None:
            self.setParent(parent)
        
        # Variables para almacenar conexiones de eventos
        self.scroll_connection = None
        self.hover_connection = None
        
        # Conectar eventos del ratón
        self.scroll_connection = self.fig.canvas.mpl_connect('scroll_event', self.on_scroll)
        self.hover_connection = self.fig.canvas.mpl_connect('motion_notify_event', self.on_hover)
        
        # Variable para almacenar los datos
        self.data = []
        self.bars = []
        self.value_texts = []
        self.colors = []

    def closeEvent(self, event):
        """Manejar el evento de cierre del widget"""
        self.cleanup()
        super().closeEvent(event)

    def cleanup(self):
        """Limpiar recursos antes de eliminar el widget"""
        try:
            # Desconectar eventos de matplotlib
            if self.scroll_connection is not None:
                self.fig.canvas.mpl_disconnect(self.scroll_connection)
                self.scroll_connection = None
            
            if self.hover_connection is not None:
                self.fig.canvas.mpl_disconnect(self.hover_connection)
                self.hover_connection = None
            
            # Cerrar la figura
            plt.close(self.fig)
        except Exception as e:
            print(f"Error durante cleanup: {e}")

    def __del__(self):
        try:
            self.cleanup()
        except:
            pass

    def plot_data(self, data):
        # Limpiar el gráfico anterior
        self.ax.clear()
        # Almacenar los datos para usarlos en el hover
        self.data = data
        # Extraer datos para el gráfico
        labels = [row[0] for row in data]
        values = [row[3] for row in data]  # Usamos 'cantidad' para las barras
        # Combinar paletas de colores
        colors_tab10 = plt.get_cmap('tab10').colors
        colors_tab20 = plt.get_cmap('tab20').colors
        colors_set3 = plt.get_cmap('Set3').colors
        self.colors = colors_tab10 + colors_tab20 + colors_set3
        # Crear el gráfico de barras
        self.bars = self.ax.bar(labels, values, color=self.colors[:len(labels)])
        self.ax.set_title('Resumen de Prismas')
        # Etiquetas de los ejes
        self.ax.set_ylabel('Lecturas')
        self.ax.set_xlabel('Prismas')
        # Rotar los nombres en el eje x
        self.ax.set_xticks(range(len(labels)))
        self.ax.set_xticklabels(labels, rotation=45, ha='right')
        # Ajustar el margen superior para que haya espacio para los valores
        self.ax.margins(y=0.1)
        # Crear textos para los valores
        self.value_texts = [self.ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.1,
            f'{int(bar.get_height())}',
            ha='center',
            va='bottom',
            fontsize=8  # Tamaño de la fuente
        ) for bar in self.bars]
        # Ajustar la visibilidad inicial de las barras
        if len(labels) <= 15:
            self.ax.set_xlim(-0.5, len(labels) - 0.5)
        else:
            self.ax.set_xlim(-0.5, 14.5)
        self.update_visible_texts()
        self.draw()

    def update_visible_texts(self):
        # Actualizar la visibilidad de los textos de valor
        try:
            xlim = self.ax.get_xlim()
            for bar, text in zip(self.bars, self.value_texts):
                if xlim[0] <= bar.get_x() + bar.get_width() / 2 <= xlim[1]:
                    text.set_visible(True)
                else:
                    text.set_visible(False)
            self.draw()
        except RuntimeError:
            # El widget fue eliminado, no hacer nada
            pass

    def on_scroll(self, event):
        try:
            # Ajustar los límites del eje x al hacer scroll
            current_xlim = self.ax.get_xlim()
            step = (current_xlim[1] - current_xlim[0]) * 0.1  # Ajustar el paso del desplazamiento
            if event.button == 'up':
                self.ax.set_xlim(current_xlim[0] - step, current_xlim[1] - step)
            elif event.button == 'down':
                self.ax.set_xlim(current_xlim[0] + step, current_xlim[1] + step)
            self.update_visible_texts()
        except RuntimeError:
            # El widget fue eliminado, no hacer nada
            pass

    def on_hover(self, event):
        try:
            # Mostrar detalles al pasar el cursor sobre una barra
            if event.inaxes == self.ax and hasattr(self, 'bars') and hasattr(self, 'data'):
                for bar, row in zip(self.bars, self.data):
                    if bar.contains(event)[0]:
                        tooltip_text = (f"Nombre: {row[0]}\n"
                                        f"Fecha Inicial: {row[1]}\n"
                                        f"Fecha Final: {row[2]}\n"
                                        f"Lecturas: {row[3]}\n"
                                        f"Total Días: {row[4]}\n"
                                        f"Ratio: {row[5]:.2f}")
                        # Convertir la posición del evento a un QPoint
                        try:
                            local_pos = self.fig.canvas.mapToGlobal(QPoint(int(event.x), int(event.y)))
                            QToolTip.showText(local_pos, tooltip_text, self)
                        except:
                            pass
                        break
        except (RuntimeError, AttributeError):
            # El widget fue eliminado o los atributos no existen, no hacer nada
            pass

# Hilo para cargar dashboard
class CargarDashboardThread(QThread):
    task_finishDashboard = Signal(dict)

    def __init__(self, idproyecto, id_componente=None):
        super().__init__()
        self.idproyecto = idproyecto
        self.id_componente = id_componente

    def run(self):
        try:
            datos = DashboardView.obtener_datos_dashboard(self.idproyecto, self.id_componente)
        except Exception as e:
            print(f"Error obteniendo datos del dashboard: {e}")
            datos = {}
        self.task_finishDashboard.emit(datos)

# Hilo para cargar dashboard
class CargarDashboardThread(QThread):
    task_finishDashboard = Signal(dict)

    def __init__(self, idproyecto, id_componente=None):
        super().__init__()
        self.idproyecto = idproyecto
        self.id_componente = id_componente

    def run(self):
        try:
            datos = DashboardView.obtener_datos_dashboard(self.idproyecto, self.id_componente)
        except Exception as e:
            print(f"Error obteniendo datos del dashboard: {e}")
            datos = {}
        self.task_finishDashboard.emit(datos)