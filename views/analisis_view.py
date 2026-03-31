import threading
import numpy as np
from datetime import datetime
import pandas as pd
from typing import Tuple, Dict, Any 
import pyqtgraph as pg
from PySide6.QtWidgets import (QWidget, QLabel, QComboBox, QTreeWidget, QPushButton, QSpinBox, QScrollArea, QMessageBox,
    QStackedWidget, QFormLayout, QLineEdit, QHBoxLayout, QDialog, QVBoxLayout, QSplitter, QGroupBox, QRubberBand, QToolTip)
from PySide6.QtCore import Qt, QPoint, QRect, QSize, QEvent, QPointF, QTimer
from PySide6.QtGui import QDoubleValidator,QShortcut, QKeySequence
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from modules.analisis.graficarTrayectoriaEstereografia import GraficarEstereografiaTrayectoria
from modules.analisis.registroestereografia import RegistroEstereografia
from utils.common.alertas import mostrar_mensaje
from utils.shared.graficaDesplazamientoVelocidad import procesar_grafica, procesar_grafica_histograma, procesar_grafica_analisis
from controllers.AnalisisController import AnalisisController
from controllers.ConfiguracionController import ConfiguracionController
from modules.datos.equiposAnalisis import EquiposAnalisis
from utils.common.metodosGenerales import MetodosGenerales
from modules.empresa.softwareconfiguracion import SoftwareConfiguracion
from utils.shared.guardarImagenReporte import ReporteImage
from utils.shared.graficareporte import GraficaReporte
from utils.shared.calculostendencias import CalculosTendencias
from utils.shared.asistentedevoz import AsistenteVoz
from utils.shared.personalizacion import Personalizacion
from modules.analisis.graficar_barras import GraficarResumenEquipos
from modules.analisis.visualizaElipse import VisualizacionElipse
from modules.analisis.graficarCoordenadas import GraficarCoordenadasPrismas
from utils.shared.resumenprismas import ResumenPrismas
from utils.generic.calculardesviaciones import CalcularDesviaciones
from modules.analisis.tiemporeal import GraficaTiempoReal
from controllers.UmbralController import UmbralController
from utils.shared.graficarUmbrales import GraficarUmbrales
from services.security.session import Session

# Subclase de AxisItem para forzar 3 decimales
class DecimalAxis(pg.AxisItem):
    def __init__(self, orientation, decimals=3, *args, **kwargs):
        super().__init__(orientation, *args, **kwargs)
        self.decimals = decimals

    def tickStrings(self, values, scale, spacing):
        return [f"{v:.{self.decimals}f}" for v in values]
    
# ===== CLASE COMPLETAMENTE AJUSTADA =====
class OutlierDialog(QDialog):
    def __init__(self, df: pd.DataFrame, value_column: str, parent=None, initial_tolerance: float = 1.5):
        super().__init__(parent)
        self.df_original = df
        self.value_column = value_column
        self.tolerance = initial_tolerance
        self.setWindowTitle("Detección de Valores Atípicos")
        self.setModal(True)
        self.setGeometry(100, 100, 1200, 600)

        if parent:
            self.center_on_parent(parent)

        self.setup_ui()
        self.update_analysis()

    def center_on_parent(self, parent):
        if hasattr(parent, 'geometry'):
            parent_rect = parent.geometry()
            self.move(parent_rect.center() - self.rect().center())

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Controles
        control_group = QGroupBox("Configuración de Detección")
        control_layout = QVBoxLayout(control_group)

        tolerance_layout = QHBoxLayout()
        tolerance_label = QLabel("Nivel de Tolerancia:")
        self.tolerance_edit = QLineEdit(str(self.tolerance))
        self.tolerance_edit.setFixedWidth(100)

        self.update_button = QPushButton("Actualizar Análisis")
        self.update_button.clicked.connect(self.on_update_clicked)

        tolerance_layout.addWidget(tolerance_label)
        tolerance_layout.addWidget(self.tolerance_edit)
        tolerance_layout.addWidget(self.update_button)
        tolerance_layout.addStretch()
        control_layout.addLayout(tolerance_layout)

        self.info_label = QLabel("")
        control_layout.addWidget(self.info_label)

        layout.addWidget(control_group)

        # Splitter con gráficos
        splitter = QSplitter(Qt.Vertical)
        layout.addWidget(splitter)

        # --- Ejes personalizados con 3 decimales ---
        axis_y_original = DecimalAxis(orientation='left', decimals=3)
        self.original_widget = pg.PlotWidget(axisItems={'left': axis_y_original}, background='w')
        self.original_widget.showGrid(x=True, y=True, alpha=0.3)

        axis_y_clean = DecimalAxis(orientation='left', decimals=3)
        self.clean_widget = pg.PlotWidget(axisItems={'left': axis_y_clean}, background='w')
        self.clean_widget.showGrid(x=True, y=True, alpha=0.3)


        splitter.addWidget(self.original_widget)
        splitter.addWidget(self.clean_widget)
        splitter.setSizes([600, 400])

        # Curvas iniciales
        self.curve_all = self.original_widget.plot(
            pen=pg.mkPen(color='blue', width=2),
            name="Datos normales",
            downsample=10,
            autoDownsample=True
        )
        self.curve_outliers = pg.ScatterPlotItem(
            pen=pg.mkPen('darkred'),
            brush=pg.mkBrush('red'),
            size=6,
            name="Valores atípicos"
        )
        self.original_widget.addItem(self.curve_outliers)

        self.curve_clean = self.clean_widget.plot(
            pen=pg.mkPen(color='green', width=2),
            name="Datos limpios",
            downsample=10,
            autoDownsample=True
        )

        # Leyendas (una sola vez)
        self.original_widget.addLegend(offset=(10, 10))
        self.clean_widget.addLegend(offset=(10, 10))

        # Botones acción
        button_layout = QHBoxLayout()
        self.confirm_button = QPushButton("Confirmar Limpieza")
        self.confirm_button.clicked.connect(self.confirm_cleaning)
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(self.confirm_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

    def on_update_clicked(self):
        try:
            new_tolerance = float(self.tolerance_edit.text())
            if new_tolerance <= 0:
                QMessageBox.warning(self, "Valor inválido", "El nivel de tolerancia debe ser mayor que 0")
                return
            self.tolerance = new_tolerance
            self.update_analysis()
        except ValueError:
            QMessageBox.warning(self, "Valor inválido", "Por favor ingrese un número válido")
            self.tolerance_edit.setText(str(self.tolerance))

    def update_analysis(self):
        try:
            # Aquí llamas a tu método real de análisis
            self.df_processed, self.df_clean, self.results = AnalisisView.analyze_outliers(
                self.df_original,
                method='iqr',
                value_column=self.value_column,
                multiplier=self.tolerance
            )
            self.plot_analysis()

            outlier_count = self.results['outliers_count']
            total_data = self.results['total_data']
            percentage = (outlier_count / total_data * 100) if total_data > 0 else 0
            self.info_label.setText(f"Valores atípicos detectados: {outlier_count} de {total_data} datos ({percentage:.1f}%)")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error en el análisis: {str(e)}")

    def convert_dates_to_timestamps(self, dates):
        try:
            return pd.to_datetime(dates).astype("int64") // 10**9
        except Exception:
            return np.arange(len(dates))

    def plot_analysis(self):
        try:
            value_column = self.value_column
            date_column = 'hora_prisma'

            # Conversión rápida de fechas
            timestamps_all = self.convert_dates_to_timestamps(self.df_processed[date_column])
            timestamps_clean = self.convert_dates_to_timestamps(self.df_clean[date_column])

            # Actualizar curvas
            self.curve_all.setData(timestamps_all, self.df_processed[value_column].values)

            outlier_mask = self.df_processed['is_outlier']
            if outlier_mask.any():
                self.curve_outliers.setData(
                    x=self.convert_dates_to_timestamps(self.df_processed.loc[outlier_mask, date_column]),
                    y=self.df_processed.loc[outlier_mask, value_column].values
                )
            else:
                self.curve_outliers.setData([], [])

            self.curve_clean.setData(timestamps_clean, self.df_clean[value_column].values)

            # Ajuste manual de rangos (más rápido que autoRange continuo)
            self.original_widget.setXRange(timestamps_all.min(), timestamps_all.max(), padding=0.01)
            self.original_widget.setYRange(self.df_processed[value_column].min(), self.df_processed[value_column].max(), padding=0.1)
            self.clean_widget.setXRange(timestamps_clean.min(), timestamps_clean.max(), padding=0.01)
            self.clean_widget.setYRange(self.df_clean[value_column].min(), self.df_clean[value_column].max(), padding=0.1)

            # Eje con fechas
            self.original_widget.setAxisItems({'bottom': pg.DateAxisItem(orientation='bottom')})
            self.clean_widget.setAxisItems({'bottom': pg.DateAxisItem(orientation='bottom')})

        except Exception as e:
            print(f"Error en plot_analysis: {e}")

    def confirm_cleaning(self):
        outlier_ids = self.results['outlier_ids']
        equipo_nombre = self.results['equipo_nombre']

        omitir_lecturas = AnalisisController.ctrlOmitirLecturasRuido(AnalisisView.idproyecto, outlier_ids)
        if omitir_lecturas:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Limpieza Confirmada")
            msg.setText(f"El prisma {equipo_nombre} se limpió completada exitosamente.")
            msg.exec_()
            self.accept()
        else:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Error De limpieza")
            msg.setText(f"Error al realizar limpieza de ruido del prisma {equipo_nombre}")
            msg.exec_()

    
class AnalisisView:
    main = None
    idproyecto = None
    nameproyecto = "SIN PROYECTO"
    estadochecklist = True
    estadoPagina = True
    fechainicial, fechafinal = MetodosGenerales.obtenerRangoFechas(365)
    ejexmin = 0
    ejexmax = 0
    intervalo_principal_x = 0
    intervalo_secundario_x = 0
    ejeymin = 0
    ejeymax = 0
    intervalo_principal_y = 0
    intervalo_secundario_y = 0
    _timer_tiempo_real = None
    _umbral_idcomponente = None
    _graficando_tiempo_real = False
    _intervalo_tiempo_real = 60

    def inicializarVistaAnalisis(main, proyectoid, proyectoname, fechaini, fechafin):
        AnalisisView.main = main
        AnalisisView.idproyecto = proyectoid
        AnalisisView.nameproyecto = proyectoname
        AnalisisView.fechainicial, AnalisisView.fechafinal = fechaini, fechafin
        comboComponentesHistograma = main.findChild(QComboBox, "combo_componentes_histograma")
        comboPrismasHistograma = AnalisisView.main.findChild(QComboBox, "combo_prismas_histograma")
        comboComponentesElipse = main.findChild(QComboBox, "combo_componentes_elipse")
        comboPrismasElipse = main.findChild(QComboBox, "combo_prismas_elipse")
        comboComponentesLimpieza = AnalisisView.main.findChild(QComboBox, "combo_componentes_limpieza")
        comboPrismasLimpieza = main.findChild(QComboBox, "combo_prismas_limpieza")
        if AnalisisView.estadochecklist:
            tree_widget = main.findChild(QTreeWidget, "tree_actual_analisis")
            tree_vacio = main.findChild(QTreeWidget, "tree_actual_vacio")
            tree_widget.setHeaderLabels([AnalisisView.nameproyecto.upper()])
            EquiposAnalisis.inicializar_lista_equipos(tree_widget, tree_vacio, AnalisisView.idproyecto, AnalisisView.nameproyecto)
            AnalisisView.estadochecklist = False
            if AnalisisView.idproyecto:
                AnalisisView.cargarPrismasCombosAnalisis(AnalisisView.main, AnalisisView.idproyecto)
        if AnalisisView.estadoPagina:
            tree_actual =  main.findChild(QTreeWidget, "tree_actual_analisis")
            tree_actual.itemClicked.connect(AnalisisView.checkProyectoActualAnalisis)
            tree_actual.setContextMenuPolicy(Qt.CustomContextMenu)
            tree_actual.customContextMenuRequested.connect(AnalisisView.clicderechoProyectoActualAnalisis)
            # VISTA GENERAL ANÁLISIS
            lista_graficos_analisis = {
                'TE': 'Trayectoria - Estereografía',
                'IV': 'Inversa de la Velocidad',
                'VC': 'Variación de Coordenadas',
                'HI': 'Histograma',
                'TR': 'Gráfica Tiempo Real',
                'RE': 'Resumen de Equipos',
                'EE': 'Elipse/Elipsoide de Desviaciones',
                'LC': 'Limpieza de Coordenadas',
            }
            tipo_grafico_analisis = main.findChild(QComboBox, "combo_graficas_analisis")
            for key, value in lista_graficos_analisis.items():
                tipo_grafico_analisis.addItem(value, key)
            tipo_grafico_analisis.activated.connect(AnalisisView.ocultarMostrarVistasAnalisis)
            # VISTA TRAYECTORIA
            lista_vistas = {
                'Planta': 'Planta',
                'Frontal': 'Frontal',
                'Isometrica': 'Isométrica',
                'Bottom': 'Inferior',
                'Left': 'Izquierda',
                'Right': 'Derecha',
                'Posterior': 'Posterior',
                'Inclinada': 'Inclinada',
                'Perfil': 'Perfil',
            }
            vista_trayectoria = main.findChild(QComboBox, "cb_tipo_vista_trayectoria")
            for key, value in lista_vistas.items():
                vista_trayectoria.addItem(value, key)
            qscroll_graficas_analisis = main.findChild(QScrollArea, "scrollArea_graficas_analisis")
            qscroll_graficas_analisis.hide()
            btn_reporte_trayectoria = main.findChild(QPushButton, "btn_reporte_grafica_trayectoria")
            btn_reporte_trayectoria.clicked.connect(lambda: AnalisisView.mostrarDialogoReporteAnalisis(tree_actual, "Trayectoria", "Anexos"))
            btnTrayectoGeneral = main.findChild(QPushButton, "btn_imagen_trayectoria")
            btnTrayectoGeneral.clicked.connect(lambda: AnalisisView.mostrarDialogoReporteAnalisis(tree_actual, "Trayectoria", "General"))
            btn_refrescar_trayectoria = main.findChild(QPushButton, "btn_refresca_grafica_trayectoria")
            btn_refrescar_trayectoria.clicked.connect(lambda: AnalisisView.validarVistaAnalisis(tree_actual))
            btn_limpiar_trayectoria = main.findChild(QPushButton, "btn_limpieza_trayectoria")
            btn_limpiar_trayectoria.clicked.connect(lambda: AnalisisView.graficarLimpiezaTrayectoria(tree_actual, "estatico"))
            btn_animado_trayectoria = main.findChild(QPushButton, "btn_animacion_trayectoria")
            btn_animado_trayectoria.clicked.connect(lambda: AnalisisView.animarGraficaTrayectoria(tree_actual, "animado"))
            # VISTA ESTEREOGRAFIA
            lista_tipo_estereografia = {
                'ecuatorial': 'Ecuatorial',
                'polar': 'Polar',
            }
            tipo_estereografia = main.findChild(QComboBox, "cb_tipo_estereografia")
            for key, value in lista_tipo_estereografia.items():
                tipo_estereografia.addItem(value, key)
            tipo_estereografia.activated.connect(lambda: AnalisisView.validarGraficaEstereografia(tree_actual))
            btn_refrescar_estereografia = main.findChild(QPushButton, "btn_refresca_grafica_estereografia")
            btn_refrescar_estereografia.clicked.connect(lambda: AnalisisView.validarGraficaEstereografia(tree_actual))
            btn_reporte_estereografia = main.findChild(QPushButton, "btn_reporte_grafica_estereografia")
            btn_reporte_estereografia.clicked.connect(lambda: AnalisisView.mostrarDialogoReporteAnalisis(tree_actual, "Estereografia", "Anexos"))
            btnEstereoGeneral = main.findChild(QPushButton, "btn_imagen_estereografia")
            btnEstereoGeneral.clicked.connect(lambda: AnalisisView.mostrarDialogoReporteAnalisis(tree_actual, "Estereografia", "General"))
            btn_taludes = main.findChild(QPushButton, "btn_agregar_planos")
            btn_taludes.clicked.connect(lambda: AnalisisView.modalRegistroTaludes(tree_actual))
            # INVERSA DE LA VELOCIDAD
            lista_unidades_tiempo = [
                ('Fechas', "FECHA"),
                ('Días', "DIA"),
                ('Horas', "HORA"),
            ]
            combo_tiempos = main.findChild(QComboBox, "combo_tiempo_analisis")
            for value, key in lista_unidades_tiempo:
                combo_tiempos.addItem(value, key)
            combo_tiempos.activated.connect(lambda: AnalisisView.obtenerMostrarPrismasMarcados(tree_actual))
            # unidades velocidad
            lista_velocidad_medida = [
                ('Día/metros', "DM"),
                ('Día/centímetros', "DCM"),
                ('Día/milímetros', "DMM"),
                ('Hora/metros', "HM"),
                ('Hora/centímetros', "HCM"),
                ('Hora/milímetros', "HMM"),
            ]
            combo_velocidad = main.findChild(QComboBox, "combo_velocidad_analisis")
            for value, key in lista_velocidad_medida:
                combo_velocidad.addItem(value, key)
            combo_velocidad.activated.connect(lambda: AnalisisView.obtenerMostrarPrismasMarcados(tree_actual))
            # unidades escala
            lista_velocidad_medida = [
                ('Sin Escala', "SEL"),
                ('Semilogarítmica', "ESL"),
                ('Logarítmica', "ELL"),
            ]
            combo_escala = main.findChild(QComboBox, "combo_escala_analisis")
            for value, key in lista_velocidad_medida:
                combo_escala.addItem(value, key)
            combo_escala.activated.connect(lambda: AnalisisView.obtenerMostrarPrismasMarcados(tree_actual))
            btn_refrescar_vista = main.findChild(QPushButton, "btn_refrescar_vista_analisis")
            btn_refrescar_vista.clicked.connect(lambda: AnalisisView.validarVistaAnalisis(tree_actual))
            btnLimpiarRuido = main.findChild(QPushButton, "btn_limpieza_analisis")
            btnLimpiarRuido.clicked.connect(lambda: AnalisisView.mostrarModalLimpiezaRuido(tree_actual))
            btnTendencia = main.findChild(QPushButton, "btn_tendencia_analisis")
            btnTendencia.clicked.connect(lambda: AnalisisView.mostrarModalTendencia(tree_actual))
            btnEjesAnalisis = main.findChild(QPushButton, "btn_ejes_analisis")
            btnEjesAnalisis.clicked.connect(lambda: AnalisisView.mostrarModalConfiguracionEjesInversaVelocidad(tree_actual))
            btn_reporte_analisis = main.findChild(QPushButton, "btn_reporte_grafica_analisis")
            btn_reporte_analisis.clicked.connect(lambda: AnalisisView.mostrarDialogoReporteAnalisis(tree_actual, "Analisis", "Anexos"))
            btnAnalisisGeneral = main.findChild(QPushButton, "btn_imagen_analisis")
            btnAnalisisGeneral.clicked.connect(lambda: AnalisisView.mostrarDialogoReporteAnalisis(tree_actual, "Analisis", "General"))
            # VISTA VARIACIÓN DE COORDENADAS
            lista_variaciones = [
                ('Variación en Este - Norte', "VEN"),
                ('Variación en Cota', "VAC")
            ]
            combo_variaciones = main.findChild(QComboBox, "combo_coordenadas_variacion")
            for value, key in lista_variaciones:
                combo_variaciones.addItem(value, key)
            combo_variaciones.activated.connect(lambda: AnalisisView.validarVariacionesCoordenadas(tree_actual))
            btn_refrescar_variacion = main.findChild(QPushButton, "btn_refresca_grafica_variaciones")
            btn_refrescar_variacion.clicked.connect(lambda: AnalisisView.validarVariacionesCoordenadas(tree_actual))
            btnReporteAnexosVariacion = main.findChild(QPushButton, "btn_reporte_grafica_variaciones")
            btnReporteAnexosVariacion.clicked.connect(lambda: AnalisisView.mostrarDialogoReporteAnalisis(tree_actual, "Variacion", "Anexos"))
            btnReporteGeneralVariacion = main.findChild(QPushButton, "btn_imagen_variaciones")
            btnReporteGeneralVariacion.clicked.connect(lambda: AnalisisView.mostrarDialogoReporteAnalisis(tree_actual, "Variacion", "General"))
            btnEjesVariacion = main.findChild(QPushButton, "btn_ejes_variaciones")
            btnEjesVariacion.clicked.connect(lambda: AnalisisView.mostrarModalConfiguracionEjesCoordenadas(tree_actual))
            # VISTA HISTOGRAMA
            btn_refrescar_histograma = main.findChild(QPushButton, "btn_refrescar_histograma")
            btn_refrescar_histograma.clicked.connect(AnalisisView.graficarHistograma)
            comboComponentesHistograma.activated.connect(AnalisisView.cargarPrismasComboHistograma)
            comboPrismasHistograma.activated.connect(AnalisisView.graficarHistograma)
            lista_calculos_histograma = {
                '3DA': 'Desplazamiento Acum. 3D',
                '3DI': 'Desplazamiento Incr. 3D',
                '2DA': 'Desplazamiento Acum. 2D',
                '2DI': 'Desplazamiento Incr. 2D',
                'SDA': 'Desplazamiento Acum. SD',
                'SDI': 'Desplazamiento Incr. SD',
                'DLA': 'Desplazamiento Acum. L',
                'DLI': 'Desplazamiento Incr. L',
                'DTA': 'Desplazamiento Acum. T',
                'DTI': 'Desplazamiento Incr. T',
                'DHA': 'Desplazamiento Acum. H',
                'DHI': 'Desplazamiento Incr. H',
                'DNA': 'Desplazamiento Acum. N',
                'DNI': 'Desplazamiento Incr. N',
                'DEA': 'Desplazamiento Acum. E',
                'DEI': 'Desplazamiento Incr. E',
                'DZA': 'Desplazamiento Acum. Z',
                'DZI': 'Desplazamiento Incr. Z',
                'VI3D': 'Velocidad Incremental 3D',
                'VA3D': 'Velocidad Acumulada 3D',
                'VI2D': 'Velocidad Incremental 2D',
                'VA2D': 'Velocidad Acumulada 2D',
                'VISD': 'Velocidad Incremental SD',
                'VASD': 'Velocidad Acumulada SD',
            }
            combo_tipografica = AnalisisView.main.findChild(QComboBox, "combo_tipografica_histograma")
            for key, value in lista_calculos_histograma.items():
                combo_tipografica.addItem(value, key)
            combo_tipografica.activated.connect(AnalisisView.graficarHistograma)
            # metodos limpieza histograma
            lista_limpieza_histograma = [
                ('Método IQR', "IQR"),
                ('Estadístico', "EST"),
            ]
            combo_limpieza = main.findChild(QComboBox, "combo_limpieza_histograma")
            for value, key in lista_limpieza_histograma:
                combo_limpieza.addItem(value, key)
            btn_limpieza_histograma = main.findChild(QPushButton, "btn_limpieza_histograma")
            btn_limpieza_histograma.clicked.connect(AnalisisView.aplicarMetodoLimpiezaHistograma)
            btn_refrescar_analisis = main.findChild(QPushButton, "btn_refresca_grafica_analisis")
            btn_refrescar_analisis.clicked.connect(lambda: AnalisisView.obtenerMostrarPrismasMarcados(tree_actual))
            btnAsistenteVoz = AnalisisView.main.findChild(QPushButton, "btn_voz_analisis")
            btnAsistenteVoz.clicked.connect(lambda: AnalisisView.iniciarAsistenteVozAnalisis(tree_actual, btnAsistenteVoz))
            btn_reporte_histograma = main.findChild(QPushButton, "btn_reporte_grafica_histograma")
            btn_reporte_histograma.clicked.connect(lambda: AnalisisView.mostrarDialogoReporteAnalisis(tree_actual, "Histograma", "Anexos"))
            btnHistograGeneral = main.findChild(QPushButton, "btn_imagen_histograma")
            btnHistograGeneral.clicked.connect(lambda: AnalisisView.mostrarDialogoReporteAnalisis(tree_actual, "Histograma", "General"))
            # VISTA RESUMEN DE EQUIPOS
            comboRatio = main.findChild(QComboBox, "combo_unidad_resumen_equipos")
            # Crear objetos para los elementos del combo
            ratio1 = (1, "Diario")
            ratio2 = (7, "Semanal")
            ratio3 = (15, "Quincenal")
            ratio4 = (30, "Mensual")
            ratio5 = (90, "Trimestral")
            ratio6 = (365, "Anual")
            # Agregar elementos al combo con valores y texto
            for val, text in [ratio1, ratio2, ratio3, ratio4, ratio5, ratio6]:
                comboRatio.addItem(text, val)
            comboRatio.activated.connect(AnalisisView.grafica_barras_resumen)
            btnReporteAnexosBarras = main.findChild(QPushButton, "btn_reporte_anexos_resumen")
            btnReporteAnexosBarras.clicked.connect(lambda: AnalisisView.mostrarDialogoReporteAnalisis(tree_actual, "Resumen", "Anexos"))
            btnReporteGeneralBarras = main.findChild(QPushButton, "btn_reporte_general_resumen")
            btnReporteGeneralBarras.clicked.connect(lambda: AnalisisView.mostrarDialogoReporteAnalisis(tree_actual, "Resumen", "General"))
            btn_refrescar_resumen_equipos = main.findChild(QPushButton, "btn_refrescar_resumen_equipos")
            btn_refrescar_resumen_equipos.clicked.connect(AnalisisView.grafica_barras_resumen)
            ##### VISTA TIEMPO REAL
            comboComponentesReal = main.findChild(QComboBox, "combo_componentes_tiemporeal")
            comboInstrumentosReal = main.findChild(QComboBox, "combo_instrumentos_tiemporeal")
            comboTipograficasReal = main.findChild(QComboBox, "combo_tipografica_tiemporeal")
            comboUnidadesReal = main.findChild(QComboBox, "combo_unidades_tiemporeal")
            comboInstrumentosReal.clear()
            # cargar instrumentos
            comboInstrumentosReal.addItem("Prismas", "PRISMA")
            comboInstrumentosReal.addItem("Pz Cuerda Vibrante", "PIEZOMETROCUERDA")
            comboInstrumentosReal.addItem("Celdas", "CELDA")
            def cargarTiposGraficos():
                comboTipograficasReal.clear()
                instrumento = comboInstrumentosReal.currentData()
                if instrumento == "PRISMA":
                    lista = [
                        ("Despl. Acumulado 3D","3DA"), ("Despl. Incremental 3D","3DI"), 
                        ("Despl. Acumulado 2D","2DA"), ("Despl. Incremental 2D","2DI"), 
                        ("Despl. Acumulado SD","SDA"), ("Despl. Incremental SD","SDI"), 
                        ("Despl. Acumulado E","DEA"), ("Despl. Incremental E","DEI"),
                        ("Despl. Acumulado N","DNA"), ("Despl. Incremental N","DNI"),
                        ("Despl. Acumulado Z","DZA"), ("Despl. Incremental Z","DZI"),
                        ("Velocidad Acumulado 3D","VA3D"), ("Velocidad Incremental 3D","VI3D"),
                        ("Velocidad Acumulado 2D","VA2D"), ("Velocidad Incremental 2D","VI2D"),
                        ("Velocidad Acumulado SD","VASD"), ("Velocidad Incremental SD","VISD"),
                    ]
                elif instrumento == "PIEZOMETROCUERDA":
                    lista = [("Nivel Freático","PCNF"),("Nivel Acumulado","PCNA"),("Nivel Incremental","PCNI")]
                elif instrumento == "CELDA":
                    lista = [("Nivel Asentamiento","CANA"),("Asentamiento Acumulado","CAAA"),("Asentamiento Incremental","CAAI")]
                else:
                    lista = []
                for texto, valor in lista:
                    comboTipograficasReal.addItem(texto, valor)
            def cargarTiposUnidades():
                comboUnidadesReal.clear()
                tipografica = comboTipograficasReal.currentData()
                if tipografica in ("3DA","3DI","2DA","2DI","SDA","SDI","DEA","DEI","DNA","DNI","DZA","DZI","PCNA","PCNI","PMNA","PMNI","CAAA","CAAI"):
                    for texto, valor in [("Metros",1),("Centímetros",100),("Milímetros",1000)]:
                        comboUnidadesReal.addItem(texto, valor)
                elif tipografica in ("VA3D","VI3D","VA2D","VI2D","VASD","VISD"):
                    for texto, valor in [("Metros/día",1),("Centímetros/día",100),("Milímetros/día",1000),("Metros/hora",1/24),("Centímetros/hora",100/24),("Milímetros/hora",1000/24)]:
                        comboUnidadesReal.addItem(texto, valor)
                elif tipografica in ("PCNF","PMNF","CANA"):
                    comboUnidadesReal.addItem("MSNM", 1)
            # Cuando cambia el INSTRUMENTO → recargar tipos + unidades
            def reiniciarPorInstrumento():
                comboTipograficasReal.blockSignals(True)
                comboUnidadesReal.blockSignals(True)
                try:
                    cargarTiposGraficos()
                    cargarTiposUnidades()
                finally:
                    comboTipograficasReal.blockSignals(False)
                    comboUnidadesReal.blockSignals(False)
                AnalisisView.GraficarTiempoReal()
            # Cuando cambia el TIPO DE GRÁFICA → recargar solo unidades
            def reiniciarPorTipografica():
                comboUnidadesReal.blockSignals(True)
                try:
                    cargarTiposUnidades()
                finally:
                    comboUnidadesReal.blockSignals(False)
                AnalisisView.GraficarTiempoReal()
            # Inicialización
            reiniciarPorInstrumento()
            # Botones
            btnEjesTiempoReal = main.findChild(QPushButton, "btn_ejes_tiemporeal")
            btnEjesTiempoReal.clicked.connect(AnalisisView.mostrarModalConfiguracionEjesTiempoReal)
            btnUmbralTiempoReal = main.findChild(QPushButton, "btn_umbrales_tiemporeal")
            btnUmbralTiempoReal.clicked.connect(AnalisisView.graficarUmbralesTiempoReal)

            btnAsignarTiempo = main.findChild(QPushButton, "btn_asignar_tiempo")
            btnAsignarTiempo.clicked.connect(AnalisisView.modalAsignarTiempo)

            comboInstrumentosReal.currentIndexChanged.connect(reiniciarPorInstrumento)
            comboTipograficasReal.activated.connect(reiniciarPorTipografica)
            comboComponentesReal.activated.connect(AnalisisView.GraficarTiempoReal)
            comboUnidadesReal.activated.connect(AnalisisView.GraficarTiempoReal)
            # VISTA ELIPSE DE ERROR
            btn_refrescar_elipse = main.findChild(QPushButton, "btn_refresca_grafica_elipse")
            btn_refrescar_elipse.clicked.connect(AnalisisView.graficarElipseDesviaciones)
            btn_ocultar_mostrar_desviaciones = main.findChild(QPushButton, "btn_ocultar_mostrar_desviaciones")
            btn_ocultar_mostrar_desviaciones.clicked.connect(AnalisisView.OcultarDesviaciones)
            btn_mostrar_cambios = main.findChild(QPushButton, "btn_mostrar_cambios_prismas")
            btn_mostrar_cambios.clicked.connect(AnalisisView.mostrarCambiosPrismas)
            
            btn_limpiar_ruido_coordenadas = main.findChild(QPushButton, "btn_limpiar_ruido")
            btn_limpiar_ruido_coordenadas.clicked.connect(AnalisisView.LimpiarRuidoGrafico)
            
            btn_limpiar_ruido_manual = main.findChild(QPushButton, "btn_limpiar_ruido_manual")
            btn_limpiar_ruido_manual.clicked.connect(AnalisisView.LimpiarRuidoManual)
            
            # Limpieza y elipse
            comboComponentesElipse.activated.connect(AnalisisView.cargarPrismasElipseComponente)
            comboPrismasElipse.activated.connect(AnalisisView.graficarElipseDesviaciones)
            comboUnidadesMedidaElipse = main.findChild(QComboBox, "combo_unidades_medida")
            lista_unidades_medida = [
                ('En Coordenadas', "cor"),
                ('En Metros', "m"),
                ('En Centímetros', "cm"),
                ('En Milímetros', "mm"),
            ]
            for value, key in lista_unidades_medida:
                comboUnidadesMedidaElipse.addItem(value, key)
            comboUnidadesMedidaElipse.activated.connect(AnalisisView.graficarElipseDesviaciones)
            btn_data_tabla = main.findChild(QPushButton, "btn_tabla_desviaciones")
            btn_data_tabla.clicked.connect(AnalisisView.mostrarDataTablaDesviaciones)
            btn_recalcular_desviacion = main.findChild(QPushButton, "btn_recalcular_desviaciones")
            btn_recalcular_desviacion.clicked.connect(AnalisisView.recalcular_desviaciones)
            btnLimpiezaElipse = main.findChild(QPushButton, "btn_limpieza_ruido_elipse")
            btnLimpiezaElipse.clicked.connect(AnalisisView.aplicarLimpiezaRuidoDesviaciones)
            btn_desviaciones_manual = main.findChild(QPushButton, "btn_desviaciones_manuales")
            btn_desviaciones_manual.clicked.connect(AnalisisView.registrar_desviaciones_manuales)
            btnControlzElipse = main.findChild(QPushButton, "btn_controlz_prismas")
            btnControlzElipse.clicked.connect(AnalisisView.restablecerCambiosPrismasElipse)
            combo_vistas_elipsoide_3d = main.findChild(QComboBox, "combo_vistas_elipsoide")
            for key, value in lista_vistas.items():
                combo_vistas_elipsoide_3d.addItem(value, key)
            btn_configurar_ejes_elipse = AnalisisView.main.findChild(QPushButton, "btn_ejes_elipse")
            btn_configurar_ejes_elipse.clicked.connect(AnalisisView.configurarEjesElipse)
            btnReporteAnexosElipse = main.findChild(QPushButton, "btn_reporte_elipse_anexos")
            btnReporteAnexosElipse.clicked.connect(lambda: AnalisisView.mostrarDialogoReporteAnalisis(tree_actual, "Elipse", "Anexos"))
            btnReporteGeneralElipse = main.findChild(QPushButton, "btn_reporte_elipse_general")
            btnReporteGeneralElipse.clicked.connect(lambda: AnalisisView.mostrarDialogoReporteAnalisis(tree_actual, "Elipse", "General"))
            # VISTA LIMPIEZA DE COORDENADAS
            lista_tipografica_limpieza_datos= [
                ('Gráfica Este', "GE"),
                ('Gráfica Norte', "GN"),
                ('Gráfica Cota', "GC"),
                ('Gráfica SD', "GSD"),
            ]
            comboTipoDataLimpieza = main.findChild(QComboBox, "combo_tipo_grafico")
            for value, key in lista_tipografica_limpieza_datos:
                comboTipoDataLimpieza.addItem(value, key)
            comboComponentesLimpieza.activated.connect(AnalisisView.cargarPrismasLimpiezaComponente)
            comboPrismasLimpieza.activated.connect(AnalisisView.graficarCoordenadasPrismas)
            comboTipoDataLimpieza.activated.connect(AnalisisView.graficarCoordenadasPrismas)
            btn_refrescar_lipiar_datos_prismas = main.findChild(QPushButton, "btn_refresca_grafica_limpieza")
            btn_refrescar_lipiar_datos_prismas.clicked.connect(AnalisisView.graficarCoordenadasPrismas)
            # validación de las vistas
            AnalisisView.ocultarMostrarVistasAnalisis()
            AnalisisView.estadoPagina = False
        # validar arbol
        AnalisisView.validarCheckboxVistasAnalisis()
    
    def checkProyectoActualAnalisis(parent_item, column):
        treeWidget =  AnalisisView.main.findChild(QTreeWidget, "tree_actual_analisis")
        EquiposAnalisis.validarMarcadoCheckbox(parent_item, column, lambda: AnalisisView.obtenerMostrarPrismasMarcados(treeWidget))
        
    def clicderechoProyectoActualAnalisis(point):
        treeWidget =  AnalisisView.main.findChild(QTreeWidget, "tree_actual_analisis")
        EquiposAnalisis.validarOpcionesMenuCheckbox(point, AnalisisView.main, treeWidget, AnalisisView.reiniciarVistasAfectadas)
    
    def reiniciarCombosPrismasAnalisis():
        tree_widget = AnalisisView.main.findChild(QTreeWidget, "tree_actual_analisis")
        tree_vacio = AnalisisView.main.findChild(QTreeWidget, "tree_actual_vacio")
        tree_widget.setHeaderLabels([AnalisisView.nameproyecto.upper()])
        EquiposAnalisis.inicializar_lista_equipos(tree_widget, tree_vacio, AnalisisView.idproyecto, AnalisisView.nameproyecto)
        if AnalisisView.idproyecto:
            AnalisisView.cargarPrismasCombosAnalisis(AnalisisView.main, AnalisisView.idproyecto)
    
    def cargarPrismasCombosAnalisis(main, idproyecto):
        if main and idproyecto:
            comboComponentesHistograma = main.findChild(QComboBox, "combo_componentes_histograma")
            comboComponentesElipse = main.findChild(QComboBox, "combo_componentes_elipse")
            comboComponentesLimpieza = AnalisisView.main.findChild(QComboBox, "combo_componentes_limpieza")
            comboPrismasHistograma = AnalisisView.main.findChild(QComboBox, "combo_prismas_histograma")
            comboPrismasElipse = main.findChild(QComboBox, "combo_prismas_elipse")
            comboPrismasLimpieza = main.findChild(QComboBox, "combo_prismas_limpieza")
            comboComponentesTiempoReal = main.findChild(QComboBox, "combo_componentes_tiemporeal")
            # Traer lista de componentes que tengan prismas
            componentes = AnalisisController.ctrlListarComponentesPrismasProyecto(idproyecto)
            if componentes:
                comboComponentesHistograma.clear()
                comboComponentesElipse.clear()
                comboComponentesLimpieza.clear()
                comboComponentesTiempoReal.clear()
                for componente in componentes:
                    comboComponentesHistograma.addItem(componente[2], componente[0])
                    comboComponentesElipse.addItem(componente[2], componente[0])
                    comboComponentesLimpieza.addItem(componente[2], componente[0])
                    comboComponentesTiempoReal.addItem(componente[2], componente[0])
                # listar prismas por el primer componente
                idcomponente = componentes[0][0]
                if idcomponente:
                    listaprismas = AnalisisController.ctrlObtenerNombresPrismasComponente(idcomponente)
                    if listaprismas:
                        comboPrismasHistograma.clear()
                        comboPrismasElipse.clear()
                        comboPrismasLimpieza.clear()
                        for prisma in listaprismas: # idinstr, idcompo, tipo, nomb, idequipo, tabla, estado
                            comboPrismasHistograma.addItem(prisma[3], (prisma[2], prisma[1]))
                            comboPrismasElipse.addItem(prisma[3], prisma[2])
                            comboPrismasLimpieza.addItem(prisma[3], prisma[2])
    
    def reiniciarVistasAfectadas(tipoequipo="Todos"):
        from views.datos_view import DatosView
        from views.visor_view import VisorView
        from views.desplazamiento_view import AnalisisView
        from views.velocidad_view import VelocidadView
        from views.inclinometros_view import InclinometrosView
        from views.piezometros_view import PiezometrosView
        from views.celdas_view import CeldasView
        from views.acelerografos_view import AcelerografosView
        from views.sondajestdr_view import SondajetdrView
        if tipoequipo == "Prisma":
            DatosView.reiniciarVistaDatos(AnalisisView.main, AnalisisView.idproyecto, AnalisisView.nameproyecto)
            VisorView.reiniciarVistaVisor(AnalisisView.main, AnalisisView.idproyecto, AnalisisView.nameproyecto)
            AnalisisView.reiniciarVistaDesplazamiento(AnalisisView.main, AnalisisView.idproyecto, AnalisisView.nameproyecto)
            VelocidadView.reiniciarVistaVelocidad(AnalisisView.main, AnalisisView.idproyecto, AnalisisView.nameproyecto)
        else:
            DatosView.reiniciarVistaDatos(AnalisisView.main, AnalisisView.idproyecto, AnalisisView.nameproyecto)
            VisorView.reiniciarVistaVisor(AnalisisView.main, AnalisisView.idproyecto, AnalisisView.nameproyecto)
            AnalisisView.reiniciarVistaDesplazamiento(AnalisisView.main, AnalisisView.idproyecto, AnalisisView.nameproyecto)
            VelocidadView.reiniciarVistaVelocidad(AnalisisView.main, AnalisisView.idproyecto, AnalisisView.nameproyecto)
            InclinometrosView.reiniciarVistaInclinometros(AnalisisView.main, AnalisisView.idproyecto, AnalisisView.nameproyecto)
            PiezometrosView.reiniciarVistaPiezometros(AnalisisView.main, AnalisisView.idproyecto, AnalisisView.nameproyecto)
            CeldasView.reiniciarVistaCeldas(AnalisisView.main, AnalisisView.idproyecto, AnalisisView.nameproyecto)
            AcelerografosView.reiniciarVistaAcelerografos(AnalisisView.main, AnalisisView.idproyecto, AnalisisView.nameproyecto)
            SondajetdrView.reiniciarVistaTDR(AnalisisView.main, AnalisisView.idproyecto, AnalisisView.nameproyecto)
    
    def validarVistaAnalisis(tree_actual):    
        tipo_grafico_analisis = AnalisisView.main.findChild(QComboBox, "combo_graficas_analisis")
        tipografico = tipo_grafico_analisis.currentData()
        if tipografico == "TE":
            lista = EquiposAnalisis.obtener_todos_elementos_marcados(tree_actual)
            if lista:
                prismasmarcados = AnalisisView.obtenerListaEquiposMarcados(lista, "Prismas")
                if len(prismasmarcados) > 0:
                    AnalisisView.graficarEquiposMarcadosAnalisis(prismasmarcados)
                else:
                    AnalisisView.limpiarGraficaTrayectoria()
                    AnalisisView.limpiarGraficaEstereografia()
        elif tipografico == "IV":
            lista = EquiposAnalisis.obtener_todos_elementos_marcados(tree_actual)
            if lista:
                prismasmarcados = AnalisisView.obtenerListaEquiposMarcados(lista, "Prismas")
                if len(prismasmarcados) > 0:
                    AnalisisView.graficarEquiposMarcadosAnalisis(prismasmarcados)
                else:
                    AnalisisView.limpiarGraficasAnalisis()
            else:
                AnalisisView.limpiarGraficasAnalisis()
        elif tipografico == "VC":
            AnalisisView.validarVariacionesCoordenadas(tree_actual)
        elif tipografico == "HI":
            AnalisisView.graficarHistograma()
        elif tipografico == "RE":
            AnalisisView.grafica_barras_resumen()
        elif tipografico == "EE":
            AnalisisView.graficarElipseDesviaciones()
        elif tipografico == "LC":
            AnalisisView.graficarCoordenadasPrismas()
    
    def obtenerMostrarPrismasMarcados(tree_actual):
        lista = EquiposAnalisis.obtener_todos_elementos_marcados(tree_actual)
        if lista:
            prismasmarcados = AnalisisView.obtenerListaEquiposMarcados(lista, "Prismas")
            if len(prismasmarcados) > 0:
                AnalisisView.graficarEquiposMarcadosAnalisis(prismasmarcados)
            else:
                tipo_grafico_analisis = AnalisisView.main.findChild(QComboBox, "combo_graficas_analisis")
                tipografico = tipo_grafico_analisis.currentData()
                if tipografico == "TE":
                    AnalisisView.limpiarGraficaTrayectoria()
                    AnalisisView.limpiarGraficaEstereografia()
                elif tipografico == "IV":
                    AnalisisView.limpiarGraficasAnalisis()
                elif tipografico == "VC":
                    AnalisisView.limpiarGraficaVariacion()
        else:
            tipo_grafico_analisis = AnalisisView.main.findChild(QComboBox, "combo_graficas_analisis")
            tipografico = tipo_grafico_analisis.currentData()
            if tipografico == "TE":
                AnalisisView.limpiarGraficaTrayectoria()
                AnalisisView.limpiarGraficaEstereografia()
            elif tipografico == "IV":
                AnalisisView.limpiarGraficasAnalisis()
            elif tipografico == "VC":
                AnalisisView.limpiarGraficaVariacion()
    
    def obtenerListaEquiposMarcados(lista, tipolista):
        equiposmarcados = []
        for region, instrumentos in lista.items():
            for tipo, lista_equipos in instrumentos.items():
                if tipo[0] == tipolista:
                    equiposmarcados.append((region, lista_equipos))
        return equiposmarcados
    
    def graficarEquiposMarcadosAnalisis(prismasmarcados):
        tipo_grafico_analisis = AnalisisView.main.findChild(QComboBox, "combo_graficas_analisis")
        tipografico = tipo_grafico_analisis.currentData()
        if tipografico == "TE":
            AnalisisView.graficarTrayectoria(prismasmarcados, "estatico")
            AnalisisView.graficarEstereografia(prismasmarcados)
        elif tipografico == "VC":
            AnalisisView.graficarVariacionesCoordenadas(prismasmarcados)
        elif tipografico == "IV":
            config = SoftwareConfiguracion.obtenerDataSoftware()
            filtrado = config[16]
            combotiempos = AnalisisView.main.findChild(QComboBox, "combo_tiempo_analisis")
            unidadtiempo = combotiempos.currentData()
            escala = None
            widget_analisis = AnalisisView.main.findChild(QWidget, "widget_analisis")
            combo_escala = AnalisisView.main.findChild(QComboBox, "combo_escala_analisis")
            tipoescala = combo_escala.currentData()
            combo_velocidad = AnalisisView.main.findChild(QComboBox, "combo_velocidad_analisis")
            velocidad = combo_velocidad.currentData()
            if velocidad == "DM":
                unidadmedida = 1
                labelejey = "Inversa velocidad (d/m)"
            elif velocidad == "DCM":
                unidadmedida = 1/100
                labelejey = "Inversa velocidad (d/cm)"
            elif velocidad == "DMM":
                unidadmedida = 1/1000
                labelejey = "Inversa velocidad (d/mm)"
            elif velocidad == "HM":
                unidadmedida = 24
                labelejey = "Inversa velocidad (h/m)"
            elif velocidad == "HCM":
                unidadmedida = 24/100
                labelejey = "Inversa velocidad (h/cm)"
            else:
                unidadmedida = 24/1000
                labelejey = "Inversa velocidad (h/mm)"
            if unidadtiempo == "FECHA":
                labelejex = "Fechas"
                idx_fecha = 2
                idx_lectura = 6
                escala = None
            elif unidadtiempo == "DIA":
                labelejex = "Días"
                idx_fecha = 3
                idx_lectura = 6
            else:
                labelejex = "Horas"
                idx_fecha = 4
                idx_lectura = 5
            if tipoescala == "SEL":
                titulografica = "Inversa de la Velocidad"
            elif tipoescala == "ESL":
                if unidadtiempo == "FECHA":
                    titulografica = "Inversa de la Velocidad"
                else:
                    titulografica = "Inversa de la Velocidad - Semilogarítmica"
                    escala = tipoescala
            else:
                if unidadtiempo == "FECHA":
                    titulografica = "Inversa de la Velocidad"
                else:
                    titulografica = "Inversa de la Velocidad - Logarítmica"
                    escala = tipoescala
            datos = AnalisisController.ctrlCalcularDatosGrafica(AnalisisView.idproyecto, prismasmarcados, AnalisisView.fechainicial, AnalisisView.fechafinal, tipografico, filtrado, unidadmedida)
            if len(datos) > 0:
                labeltendencia = AnalisisView.main.findChild(QLabel, "label_tendencia_analisis")
                modulo, pluviometros, tendencias = "ANALISIS", None, None
                if filtrado == 0:
                    procesar_grafica(widget_analisis, labeltendencia, datos, 1, idx_fecha, idx_lectura, labelejex, labelejey, tipografico, unidadmedida, unidadtiempo, titulografica, AnalisisView.idproyecto, modulo, pluviometros, tendencias, escala, AnalisisView.fechainicial, AnalisisView.fechafinal)
                else:
                    procesar_grafica(widget_analisis, labeltendencia, datos, 1, idx_fecha, idx_lectura, labelejex, labelejey, tipografico, unidadmedida, unidadtiempo, titulografica, AnalisisView.idproyecto, modulo, pluviometros, tendencias, escala)
    
    def ocultarMostrarVistasAnalisis():
        combo_grafico_analisis = AnalisisView.main.findChild(QComboBox, "combo_graficas_analisis")
        tipografica = combo_grafico_analisis.currentData()
        scroll_graficas_histograma = AnalisisView.main.findChild(QScrollArea, "scrollArea_graficas_histograma")
        scroll_graficas_analisis = AnalisisView.main.findChild(QScrollArea, "scrollArea_graficas_analisis")
        scroll_graficas_variacion = AnalisisView.main.findChild(QScrollArea, "scrollArea_graficas_variaciones")
        scroll_trayectoria_estereografia = AnalisisView.main.findChild(QScrollArea, "scrollArea_trayectoria_estereografia")
        scroll_elipzoide_error = AnalisisView.main.findChild(QScrollArea, "scrollArea_graficas_elipse_error")
        scroll_limpiar_datos = AnalisisView.main.findChild(QScrollArea, "scrollArea_graficas_limpieza_datos")
        tree_actual =  AnalisisView.main.findChild(QTreeWidget, "tree_actual_analisis")
        scroll_resumen_equipos = AnalisisView.main.findChild(QScrollArea, "scrollArea_graficas_resumen_equipos")
        scroll_tiempo_real = AnalisisView.main.findChild(QScrollArea, "scrollArea_graficas_tiemporeal")
        listachecks = AnalisisView.main.findChild(QStackedWidget, "stacked_lista_checks")
        if tipografica == 'TE':
            listachecks.setCurrentIndex(9)
            scroll_graficas_histograma.hide()
            scroll_graficas_analisis.hide()
            scroll_graficas_variacion.hide()
            scroll_resumen_equipos.hide()
            scroll_elipzoide_error.hide()
            scroll_limpiar_datos.hide()
            scroll_tiempo_real.hide()
            scroll_trayectoria_estereografia.show()
            AnalisisView.validarGraficaEstereografia(tree_actual)
            AnalisisView.detenerTimerTiempoReal()
        elif tipografica == 'IV':
            listachecks.setCurrentIndex(9)
            scroll_graficas_histograma.hide()
            scroll_trayectoria_estereografia.hide()
            scroll_graficas_variacion.hide()
            scroll_resumen_equipos.hide()
            scroll_elipzoide_error.hide()
            scroll_limpiar_datos.hide()
            scroll_tiempo_real.hide()
            scroll_graficas_analisis.show()
            AnalisisView.obtenerMostrarPrismasMarcados(tree_actual)
            AnalisisView.detenerTimerTiempoReal()
        elif tipografica == 'VC':
            listachecks.setCurrentIndex(9)
            scroll_graficas_histograma.hide()
            scroll_trayectoria_estereografia.hide()
            scroll_graficas_analisis.hide()
            scroll_resumen_equipos.hide()
            scroll_elipzoide_error.hide()
            scroll_limpiar_datos.hide()
            scroll_tiempo_real.hide()
            scroll_graficas_variacion.show()
            AnalisisView.detenerTimerTiempoReal()
        elif tipografica == 'HI':
            listachecks.setCurrentIndex(10)
            scroll_trayectoria_estereografia.hide()
            scroll_graficas_analisis.hide()
            scroll_graficas_variacion.hide()
            scroll_resumen_equipos.hide()
            scroll_elipzoide_error.hide()
            scroll_limpiar_datos.hide()
            scroll_tiempo_real.hide()
            scroll_graficas_histograma.show()
            AnalisisView.detenerTimerTiempoReal()
        elif tipografica == 'RE':
            listachecks.setCurrentIndex(10)
            scroll_trayectoria_estereografia.hide()
            scroll_graficas_analisis.hide()
            scroll_graficas_variacion.hide()
            scroll_graficas_histograma.hide()
            scroll_elipzoide_error.hide()
            scroll_limpiar_datos.hide()
            scroll_tiempo_real.hide()
            scroll_resumen_equipos.show()
            AnalisisView.detenerTimerTiempoReal()
        elif tipografica == 'TR':
            listachecks.setCurrentIndex(10)
            scroll_trayectoria_estereografia.hide()
            scroll_graficas_analisis.hide()
            scroll_graficas_variacion.hide()
            scroll_graficas_histograma.hide()
            scroll_elipzoide_error.hide()
            scroll_limpiar_datos.hide()
            scroll_resumen_equipos.hide()
            scroll_tiempo_real.show()
            AnalisisView.GraficarTiempoReal()
            AnalisisView.iniciarTimerTiempoReal()
        elif tipografica == 'EE':
            listachecks.setCurrentIndex(10)
            scroll_trayectoria_estereografia.hide()
            scroll_graficas_analisis.hide()
            scroll_graficas_variacion.hide()
            scroll_graficas_histograma.hide()
            scroll_resumen_equipos.hide()
            scroll_limpiar_datos.hide()
            scroll_tiempo_real.hide()
            scroll_elipzoide_error.show()
            AnalisisView.detenerTimerTiempoReal()
        else:
            listachecks.setCurrentIndex(10)
            scroll_trayectoria_estereografia.hide()
            scroll_graficas_analisis.hide()
            scroll_graficas_variacion.hide()
            scroll_graficas_histograma.hide()
            scroll_resumen_equipos.hide()
            scroll_elipzoide_error.hide()
            scroll_limpiar_datos.show()
            AnalisisView.detenerTimerTiempoReal()
    
    def validarCheckboxVistasAnalisis():
        combo_grafico_analisis = AnalisisView.main.findChild(QComboBox, "combo_graficas_analisis")
        tipografica = combo_grafico_analisis.currentData()
        listachecks = AnalisisView.main.findChild(QStackedWidget, "stacked_lista_checks")
        if tipografica == 'TE':
            listachecks.setCurrentIndex(9)
        elif tipografica == 'IV':
            listachecks.setCurrentIndex(9)
        elif tipografica == 'VC':
            listachecks.setCurrentIndex(9)
        elif tipografica == 'HI':
            listachecks.setCurrentIndex(10)
        elif tipografica == 'RE':
            listachecks.setCurrentIndex(10)
        elif tipografica == 'TR':
            listachecks.setCurrentIndex(10)
        elif tipografica == 'EE':
            listachecks.setCurrentIndex(10)
        else:
            listachecks.setCurrentIndex(10)
    
    def validarGraficaEstereografia(tree_actual):
        lista = EquiposAnalisis.obtener_todos_elementos_marcados(tree_actual)
        if lista:
            prismasmarcados = AnalisisView.obtenerListaEquiposMarcados(lista, "Prismas")
            if len(prismasmarcados) > 0:
                AnalisisView.graficarEstereografia(prismasmarcados)
            else:
                AnalisisView.limpiarGraficaEstereografia()
        else:
            AnalisisView.limpiarGraficaEstereografia()
        
    def graficarEstereografia(prismasmarcados):
        combotipo_estereografia = AnalisisView.main.findChild(QComboBox, "cb_tipo_estereografia")
        tipoestereo = combotipo_estereografia.currentData()
        config = SoftwareConfiguracion.obtenerDataSoftware()
        filtrado = config[16]
        dataestereografia = AnalisisController.ctrObtenerDataEstereografia(AnalisisView.idproyecto)
        dataprismas = AnalisisController.ctrlDatosTrendPlunge(prismasmarcados, AnalisisView.fechainicial, AnalisisView.fechafinal, filtrado)
        if dataestereografia or dataprismas:
            widget_estereografia = AnalisisView.main.findChild(QWidget, "widget_estereografia")
            GraficarEstereografiaTrayectoria.graficar_estereografia(widget_estereografia, dataprismas, dataestereografia, tipoestereo)
    
    def animarGraficaTrayectoria(tree_actual, tipo):
        lista = EquiposAnalisis.obtener_todos_elementos_marcados(tree_actual)
        if lista:
            prismasmarcados = AnalisisView.obtenerListaEquiposMarcados(lista, "Prismas")
            if len(prismasmarcados) > 0:
                cantidad = 0
                for componente, listaprismas in prismasmarcados:
                    for prisma in listaprismas:
                        cantidad += 1
                if cantidad == 1:
                    AnalisisView.graficarTrayectoria(prismasmarcados, tipo)
                else:
                    mostrar_mensaje("Trayectoria Prismas", "Debe seleccionar solo un prisma para ver la animación.", "advertencia")
        
    def graficarTrayectoria(prismasmarcados, tipo):
        config = SoftwareConfiguracion.obtenerDataSoftware()
        filtrado = config[16]
        datos = AnalisisController.ctrlCalcularDatosTrayectoria(AnalisisView.idproyecto, prismasmarcados, AnalisisView.fechainicial, AnalisisView.fechafinal, filtrado)
        if datos:
            widget_trayectoria = AnalisisView.main.findChild(QWidget, "widget_trayectoria")
            combovistas = AnalisisView.main.findChild(QComboBox, "cb_tipo_vista_trayectoria")
            GraficarEstereografiaTrayectoria.graficar_trayectoria(widget_trayectoria, datos, combovistas, tipo)

    def GraficarTiempoReal():
        # Evitar re-entrada
        if AnalisisView._graficando_tiempo_real:
            return
        combo_grafico = AnalisisView.main.findChild(QComboBox, "combo_graficas_analisis")
        if combo_grafico.currentData() != "TR":
            return
        comboComponentes = AnalisisView.main.findChild(QComboBox, "combo_componentes_tiemporeal")
        AnalisisView._graficando_tiempo_real = True
        try:
            AnalisisView.limpiarGraficaTiempoReal()
            if comboComponentes.count() > 0:
                GraficaTiempoReal.graficarDatosTimpoReal(AnalisisView.main, AnalisisView.idproyecto)
                AnalisisView.aplicarUmbralesTiempoReal()
        finally:
            AnalisisView._graficando_tiempo_real = False

    def validarVariacionesCoordenadas(tree_actual):
        lista = EquiposAnalisis.obtener_todos_elementos_marcados(tree_actual)
        if lista:
            prismasmarcados = AnalisisView.obtenerListaEquiposMarcados(lista, "Prismas")
            if len(prismasmarcados) > 0:
                AnalisisView.graficarVariacionesCoordenadas(prismasmarcados)
            else:
                AnalisisView.limpiarGraficaVariacion()
        else:
            AnalisisView.limpiarGraficaVariacion()
    
    def graficarVariacionesCoordenadas(prismasmarcados):
        config = SoftwareConfiguracion.obtenerDataSoftware()
        filtrado = config[16]
        combo_variaciones = AnalisisView.main.findChild(QComboBox, "combo_coordenadas_variacion")
        tipografica = combo_variaciones.currentData()
        if tipografica == "VEN":
            indexnombre, indexejex, indexejey = 1, 3, 4
            labelejex, labelejey, labeltitulo = "Este (m)", "Norte (m)", "Variación en Este y Norte"
            tipotiempo = "DIAS"
        else:
            indexnombre, indexejex, indexejey = 1, 2, 5
            labelejex, labelejey, labeltitulo = "Fechas", "Elevación (msnm)", "Variación en Cota"
            tipotiempo = "FECHA"
        datos = AnalisisController.ctrlObtenerVariacionCoordenadas(AnalisisView.idproyecto, prismasmarcados, AnalisisView.fechainicial, AnalisisView.fechafinal, filtrado)
        if datos:
            widget_variacion = AnalisisView.main.findChild(QWidget, "widget_variaciones")
            if filtrado == 0: # con zoom
                procesar_grafica_analisis(widget_variacion, datos, indexnombre, indexejex, indexejey, labelejex, labelejey, labeltitulo, tipotiempo, tipografica, AnalisisView.idproyecto, AnalisisView.fechainicial, AnalisisView.fechafinal)
            else:
                procesar_grafica_analisis(widget_variacion, datos, indexnombre, indexejex, indexejey, labelejex, labelejey, labeltitulo, tipotiempo, tipografica, AnalisisView.idproyecto)
        else:
            AnalisisView.limpiarGraficaVariacion()
    
    def graficarLimpiezaTrayectoria(tree_actual, tipo):
        lista = EquiposAnalisis.obtener_todos_elementos_marcados(tree_actual)
        if lista:
            prismasmarcados = AnalisisView.obtenerListaEquiposMarcados(lista, "Prismas")
            if len(prismasmarcados) > 0:
                config = SoftwareConfiguracion.obtenerDataSoftware()
                filtrado = config[16]
                datos = AnalisisController.ctrlCalcularDatosTrayectoria(AnalisisView.idproyecto, prismasmarcados, AnalisisView.fechainicial, AnalisisView.fechafinal, filtrado)
                if datos:
                    data = CalculosTendencias.limpiezaAutomaticaTrayectoria(datos)
                    widget_trayectoria = AnalisisView.main.findChild(QWidget, "widget_trayectoria")
                    combovistas = AnalisisView.main.findChild(QComboBox, "cb_tipo_vista_trayectoria")
                    GraficarEstereografiaTrayectoria.graficar_trayectoria(widget_trayectoria, data, combovistas, tipo)
    
    def cargarPrismasComboHistograma():
        comboComponentesHistograma = AnalisisView.main.findChild(QComboBox, "combo_componentes_histograma")
        comboPrismasHistograma = AnalisisView.main.findChild(QComboBox, "combo_prismas_histograma")
        if comboComponentesHistograma.count() > 0:
            idcomponente = comboComponentesHistograma.currentData()
            listaprismas = AnalisisController.ctrlObtenerNombresPrismasComponente(idcomponente)
            if listaprismas:
                comboPrismasHistograma.clear()
                for prisma in listaprismas: # idinstr, idcompo, tipo, nomb, idequipo, tabla, estado
                    comboPrismasHistograma.addItem(prisma[3], (prisma[2], prisma[1]))
                # Graficar histograma
                AnalisisView.graficarHistograma()
    
    def graficarHistograma():
        combo_prismas = AnalisisView.main.findChild(QComboBox, "combo_prismas_histograma")
        if combo_prismas.count() > 0:
            nombreprisma = combo_prismas.currentText()
            tipoprisma, idcomponente = combo_prismas.currentData()
            combo_tipografica = AnalisisView.main.findChild(QComboBox, "combo_tipografica_histograma")
            tipografica = combo_tipografica.currentData()
            spinintervalo = AnalisisView.main.findChild(QSpinBox, "spin_intervalo_histograma")
            intervalos = spinintervalo.value()
            widget_histograma = AnalisisView.main.findChild(QWidget, "widget_histograma")
            titulografica = f"Histograma - Prisma {nombreprisma}"
            config = SoftwareConfiguracion.obtenerDataSoftware()
            tipovelocidad, filtrado = config[15], config[16]
            data = AnalisisController.ctrlTraerDataHistograma(AnalisisView.idproyecto, nombreprisma, idcomponente, tipoprisma, tipografica, AnalisisView.fechainicial, AnalisisView.fechafinal, filtrado, tipovelocidad)
            if data:
                idxlectura = 5
                if tipografica.startswith('V'):
                    labelejex = "Velocidad (m/d)"
                else:
                    labelejex = "Desplazamiento (m)"
                labelejey = "Frecuencia (u)"
                procesar_grafica_histograma(widget_histograma, data, intervalos, nombreprisma, idxlectura, labelejex, labelejey, titulografica)
            else:
                AnalisisView.limpiarGraficaHistograma()
        else:
            AnalisisView.limpiarGraficaHistograma()
    
    def grafica_barras_resumen():
        comboRatio = AnalisisView.main.findChild(QComboBox, "combo_unidad_resumen_equipos")
        unidad = comboRatio.currentData()
        widget_resumen_equipos = AnalisisView.main.findChild(QWidget, "widget_resumen_equipos")
        datos = AnalisisController.ctrlObtenerResumenPrismas(AnalisisView.idproyecto,unidad)
        AnalisisView.limpiarGraficaBarras()
        GraficarResumenEquipos.graficar_datos_en_widget(widget_resumen_equipos,datos)

    def recalcular_desviaciones():
        # Mostrar diálogo personalizado para seleccionar la fecha de cálculo
        fecha_calculo = CalcularDesviaciones.crear_dialogo_fecha_calculo()
        if fecha_calculo:
            # Obtener los datos crudos
            datos_crudos = AnalisisController.ctrlObtenerDataDesviaciones(AnalisisView.idproyecto, fecha_calculo)
            # Calcular y guardar las desviaciones
            resultado = CalcularDesviaciones.calcular_y_guardar_desviaciones(AnalisisView.idproyecto, datos_crudos, fecha_calculo)
            if resultado:
                mostrar_mensaje("Desviaciones Estándar", "Desviaciones calculadas y guardadas correctamente.", "informacion")
            else:
                mostrar_mensaje("Desviaciones Estándar", "No se pudieron guardar las desviaciones.", "error")
                
    def registrar_desviaciones_manuales():
        if AnalisisView.idproyecto:
            comboComponentesElipse = AnalisisView.main.findChild(QComboBox, "combo_componentes_elipse")
            if comboComponentesElipse.count() > 0:
                idcomponente = comboComponentesElipse.currentData()
                CalcularDesviaciones.registro_desviacion(AnalisisView.idproyecto, idcomponente)
    
    def aplicarLimpiezaRuidoDesviaciones():
        if AnalisisView.idproyecto:
            comboPrismasElipse = AnalisisView.main.findChild(QComboBox, "combo_prismas_elipse")
            comboComponentesElipse = AnalisisView.main.findChild(QComboBox, "combo_componentes_elipse")
            componente = comboComponentesElipse.currentData()
            if comboPrismasElipse.count() > 0:
                nombreprisma = comboPrismasElipse.currentText()
                tipoprisma = comboPrismasElipse.currentData()
                # crear dialogo
                dlg = QMessageBox()
                dlg.setWindowTitle("Limpieza Ruido Prismas")
                dlg.setText(f"¿Está seguro de aplicar limpieza al prisma {nombreprisma}?")
                dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                dlg.setIcon(QMessageBox.Question)
                result = dlg.exec()
                if result == QMessageBox.Yes:
                    datos = AnalisisController.ctrlObtenerDataPrismasDesviaciones(AnalisisView.idproyecto,componente, nombreprisma, tipoprisma)
                    if datos:
                        desviaciones = AnalisisController.ctrlObtenerDesviacionesPrisma(AnalisisView.idproyecto, nombreprisma)
                        datalimpia = CalcularDesviaciones.ajustarDataDesviaciones(datos,desviaciones)
                        if datalimpia:
                            respuesta = AnalisisController.ctrlActualizarDataLimpiaPrismas(AnalisisView.idproyecto, datalimpia, tipoprisma)
                            if respuesta:
                                ultima_fila = datos[-1]
                                
                                AnalisisController.ctrlRegitroUltimaLimpiezaElipse(AnalisisView.idproyecto,componente,tipoprisma,ultima_fila)
                                mostrar_mensaje("Limpieza Prismas", "Se limpió correctamente.", "informacion")
                                AnalisisView.graficarElipseDesviaciones()
                            else:
                                mostrar_mensaje("Limpieza Prismas", "Error al guardar la data limpiada.", "error")
                        else:
                            mostrar_mensaje("Limpieza Prismas", "Error al aplicar ajuste de limpieza.", "advertencia")
                    else:
                        mostrar_mensaje("Limpieza Prismas", "No existe data para limpiar.", "advertencia")
    
    def cargarPrismasElipseComponente():
        comboComponentesElipse = AnalisisView.main.findChild(QComboBox, "combo_componentes_elipse")
        comboPrismasElipseError = AnalisisView.main.findChild(QComboBox, "combo_prismas_elipse")
        if comboComponentesElipse.count() > 0:
            idcomponente = comboComponentesElipse.currentData()
            listaprismas = AnalisisController.ctrlObtenerNombresPrismasComponente(idcomponente)
            if listaprismas:
                comboPrismasElipseError.clear()
                for prisma in listaprismas: # idinstr, idcompo, tipo, nomb, idequipo, tabla, estado
                    comboPrismasElipseError.addItem(prisma[3], prisma[2])
                # Graficar histograma
                AnalisisView.graficarElipseDesviaciones()
    
    def graficarElipseDesviaciones():
        # Verificar si existen desviaciones calculadas
        desviaciones = AnalisisController.ctrlVerificarSIdesviaciones(AnalisisView.idproyecto)
        if desviaciones:
            comboPrismasElipseError = AnalisisView.main.findChild(QComboBox, "combo_prismas_elipse")
            comboUnidadesMedidaElipse = AnalisisView.main.findChild(QComboBox, "combo_unidades_medida")
            if comboPrismasElipseError.count() > 0:
                nombreprisma = comboPrismasElipseError.currentText()
                tipoprisma = comboPrismasElipseError.currentData()
                config = SoftwareConfiguracion.obtenerDataSoftware()
                filtrado = config[16]
                datos = AnalisisController.ctrlObtenerDataElipseError(AnalisisView.idproyecto, nombreprisma, tipoprisma, AnalisisView.fechainicial, AnalisisView.fechafinal, filtrado)
                if datos:
                    widget_elipse = AnalisisView.main.findChild(QWidget, "widget_elipse_error")
                    widget_primera_desviacion = AnalisisView.main.findChild(QWidget, "widget_primera_desviacion")
                    widget_segunda_desviacion = AnalisisView.main.findChild(QWidget, "widget_segunda_desviacion")
                    widget_tercera_desviacion = AnalisisView.main.findChild(QWidget, "widget_tercera_desviacion")
                    AnalisisView.limpiarGraficaElipse()
                    unidad_medida = comboUnidadesMedidaElipse.currentData()
                    combo_vistas_elipsoide_3d = AnalisisView.main.findChild(QComboBox, "combo_vistas_elipsoide")
                    valores_ejes = [
                        AnalisisView.ejexmin,
                        AnalisisView.ejexmax,
                        AnalisisView.intervalo_principal_x,
                        AnalisisView.intervalo_secundario_x,
                        AnalisisView.ejeymin,
                        AnalisisView.ejeymax,
                        AnalisisView.intervalo_principal_y,
                        AnalisisView.intervalo_secundario_y
                    ]
                    VisualizacionElipse.graficarElipseError(AnalisisView.idproyecto, nombreprisma, widget_elipse, widget_primera_desviacion, widget_segunda_desviacion, widget_tercera_desviacion, datos, unidad_medida,combo_vistas_elipsoide_3d,valores_ejes)
                else:
                    AnalisisView.limpiarGraficaElipse()
                    mostrar_mensaje("Sin Lecturas", "No hay data en el rango de fechas.", "informacion")
            else:
                AnalisisView.limpiarGraficaElipse()
        else:
            # Mostrar diálogo de confirmación
            respuesta = QMessageBox.question(
                None,
                "Desviaciones Estándar",
                "No existen desviaciones calculadas. ¿Desea calcularlas?",
                QMessageBox.Yes | QMessageBox.No
            )
            if respuesta == QMessageBox.Yes:
                # Mostrar diálogo personalizado para seleccionar la fecha de cálculo
                fecha_calculo = CalcularDesviaciones.crear_dialogo_fecha_calculo()
                if fecha_calculo:
                    # Obtener los datos crudos
                    datos_crudos = AnalisisController.ctrlObtenerDataDesviaciones(AnalisisView.idproyecto, fecha_calculo)
                    # Calcular y guardar las desviaciones
                    resultado = CalcularDesviaciones.calcular_y_guardar_desviaciones(AnalisisView.idproyecto, datos_crudos, fecha_calculo)
                    if resultado:
                        mostrar_mensaje("Desviaciones Estándar", "Desviaciones calculadas y guardadas correctamente.", "informacion")
                    else:
                        mostrar_mensaje("Desviaciones Estándar", "No se pudieron guardar las desviaciones.", "error")

    @staticmethod
    def configurarEjesElipse():
        comboUnidadesMedidaElipse = AnalisisView.main.findChild(QComboBox, "combo_unidades_medida")
        unidad_medida = comboUnidadesMedidaElipse.currentData()

        # Crear una ventana flotante (QDialog)
        dialog = QDialog()
        dialog.setWindowTitle("Configuración de Ejes de Elipse")

        # Crear campos de entrada numéricos
        def create_numeric_input(default_value):
            line_edit = QLineEdit()
            line_edit.setValidator(QDoubleValidator())
            line_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
            line_edit.setText(str(default_value))
            return line_edit

        # Obtener valores actuales y convertirlos a la unidad de medida actual
        def convertir_a_unidad(valor, unidad):
            if unidad == "m":
                return valor
            elif unidad == "cm":
                return valor * 100
            elif unidad == "mm":
                return valor * 1000
            else:  # cor
                return valor

        # Convertir desde la unidad de medida actual
        def convertir_desde_unidad(valor, unidad):
            if unidad == "m":
                return valor
            elif unidad == "cm":
                return valor / 100
            elif unidad == "mm":
                return valor / 1000
            else:  # cor
                return valor

        # Obtener valores actuales y convertirlos para mostrar
        ejexmin = convertir_a_unidad(AnalisisView.ejexmin, unidad_medida)
        ejexmax = convertir_a_unidad(AnalisisView.ejexmax, unidad_medida)
        interval_principal_x = convertir_a_unidad(AnalisisView.intervalo_principal_x, unidad_medida)
        interval_secundario_x = convertir_a_unidad(AnalisisView.intervalo_secundario_x, unidad_medida)
        ejeymin = convertir_a_unidad(AnalisisView.ejeymin, unidad_medida)
        ejeymax = convertir_a_unidad(AnalisisView.ejeymax, unidad_medida)
        interval_principal_y = convertir_a_unidad(AnalisisView.intervalo_principal_y, unidad_medida)
        interval_secundario_y = convertir_a_unidad(AnalisisView.intervalo_secundario_y, unidad_medida)

        min_x_principal = create_numeric_input(ejexmin)
        max_x_principal = create_numeric_input(ejexmax)
        eje_principal_x = create_numeric_input(interval_principal_x)
        eje_secundario_x = create_numeric_input(interval_secundario_x)
        min_y_principal = create_numeric_input(ejeymin)
        max_y_principal = create_numeric_input(ejeymax)
        eje_principal_y = create_numeric_input(interval_principal_y)
        eje_secundario_y = create_numeric_input(interval_secundario_y)

        # Layout del formulario
        form_layout = QFormLayout()
        form_layout.addRow(QLabel("Rango Mín X:"), min_x_principal)
        form_layout.addRow(QLabel("Rango Máx X:"), max_x_principal)
        form_layout.addRow(QLabel("Eje Principal X:"), eje_principal_x)
        form_layout.addRow(QLabel("Eje Secundario X:"), eje_secundario_x)
        form_layout.addRow(QLabel("Rango Mín Y:"), min_y_principal)
        form_layout.addRow(QLabel("Rango Máx Y:"), max_y_principal)
        form_layout.addRow(QLabel("Eje Principal Y:"), eje_principal_y)
        form_layout.addRow(QLabel("Eje Secundario Y:"), eje_secundario_y)

        # Función para asignar valores
        def asignar_valores():
            AnalisisView.ejexmin = convertir_desde_unidad(float(min_x_principal.text() or 0), unidad_medida)
            AnalisisView.ejexmax = convertir_desde_unidad(float(max_x_principal.text() or 0), unidad_medida)
            AnalisisView.intervalo_principal_x = convertir_desde_unidad(float(eje_principal_x.text() or 0), unidad_medida)
            AnalisisView.intervalo_secundario_x = convertir_desde_unidad(float(eje_secundario_x.text() or 0), unidad_medida)
            AnalisisView.ejeymin = convertir_desde_unidad(float(min_y_principal.text() or 0), unidad_medida)
            AnalisisView.ejeymax = convertir_desde_unidad(float(max_y_principal.text() or 0), unidad_medida)
            AnalisisView.intervalo_principal_y = convertir_desde_unidad(float(eje_principal_y.text() or 0), unidad_medida)
            AnalisisView.intervalo_secundario_y = convertir_desde_unidad(float(eje_secundario_y.text() or 0), unidad_medida)
            dialog.close()
            AnalisisView.graficarElipseDesviaciones()

        # Función para restablecer valores
        def restablecer_valores():
            AnalisisView.ejexmin = 0
            AnalisisView.ejexmax = 0
            AnalisisView.intervalo_principal_x = 0
            AnalisisView.intervalo_secundario_x = 0
            AnalisisView.ejeymin = 0
            AnalisisView.ejeymax = 0
            AnalisisView.intervalo_principal_y = 0
            AnalisisView.intervalo_secundario_y = 0

            min_x_principal.setText("")
            max_x_principal.setText("")
            eje_principal_x.setText("")
            eje_secundario_x.setText("")
            min_y_principal.setText("")
            max_y_principal.setText("")
            eje_principal_y.setText("")
            eje_secundario_y.setText("")
            dialog.close()
            AnalisisView.graficarElipseDesviaciones()

        # Botones
        boton_confirmar = QPushButton("Confirmar")
        boton_restablecer = QPushButton("Restablecer")

        boton_confirmar.clicked.connect(asignar_valores)
        boton_restablecer.clicked.connect(restablecer_valores)

        # Layout para los botones
        botones_layout = QHBoxLayout()
        botones_layout.addWidget(boton_confirmar)
        botones_layout.addWidget(boton_restablecer)

        # Layout principal del diálogo
        dialog_layout = QVBoxLayout()
        dialog_layout.addLayout(form_layout)
        dialog_layout.addLayout(botones_layout)

        dialog.setLayout(dialog_layout)
        dialog.exec()

    def OcultarDesviaciones():
        # Encuentra los widgets por su nombre
        widget_primera_desviacion = AnalisisView.main.findChild(QWidget, "widget_primera_desviacion")
        widget_segunda_desviacion = AnalisisView.main.findChild(QWidget, "widget_segunda_desviacion")
        widget_tercera_desviacion = AnalisisView.main.findChild(QWidget, "widget_tercera_desviacion")
        # Verifica si los widgets existen
        if widget_primera_desviacion and widget_segunda_desviacion and widget_tercera_desviacion:
            # Alterna la visibilidad de cada widget
            widget_primera_desviacion.setVisible(not widget_primera_desviacion.isVisible())
            widget_segunda_desviacion.setVisible(not widget_segunda_desviacion.isVisible())
            widget_tercera_desviacion.setVisible(not widget_tercera_desviacion.isVisible())
    
    def ajustarDataPrismaCoordenadas(df, id_ajuste, nombreprisma, fecha, columna_ajuste, tabla):
        # Mapear columna_ajuste a nombre de columna
        if columna_ajuste == 'X':
            variable = 'este'
            columnaajuste = 'este_target'
        elif columna_ajuste == 'Y':
            variable = 'norte'
            columnaajuste = 'norte_target'
        elif columna_ajuste == 'Z':
            variable = 'elevacion'
            columnaajuste = 'elevacion_target'
        else:  # 'D' o cualquier otra cosa
            variable = 'distancia'
            columnaajuste = 'distancia_prisma'
        columnas_validas = ['este', 'norte', 'elevacion', 'distancia']
        if variable not in columnas_validas:
            raise ValueError(f"Columna debe ser una de: {columnas_validas}")
        # Crear copia del DataFrame para no modificar el original
        df_ajustado = df.copy()
        valores = df_ajustado[variable].values
        n = len(valores)
        try:
            indice_ajuste = df_ajustado[df_ajustado['id'] == id_ajuste].index[0]
            posicion_ajuste = df_ajustado.index.get_loc(indice_ajuste)
        except (IndexError, KeyError):
            raise ValueError(f"ID {id_ajuste} no encontrado en el DataFrame")
        current_value = valores[posicion_ajuste]
        # PASO 1: Calcular columna incremental (diferencia entre valor actual y anterior)
        incremental = np.zeros(n)
        if n > 1:
            incremental[1:] = np.diff(valores)  # valores[i] - valores[i-1]
            incremental[0] = 0  # El primer valor es 0 por defecto
        # Añadir la columna incremental al DataFrame
        df_ajustado['incremental'] = incremental
        # PASO 2: Obtener el valor anterior al id_ajuste
        if posicion_ajuste == 0:
            # Si es la primera fila, no hay valor anterior, usar el mismo valor
            valor_anterior = valores[0]
        else:
            valor_anterior = valores[posicion_ajuste - 1]
        # PASO 3: Crear array para los nuevos valores ajustados
        valores_ajustados = valores.copy()
        # PASO 4: Aplicar el ajuste desde posicion_ajuste en adelante
        if posicion_ajuste < n:
            # Reemplazar el valor en posicion_ajuste con el valor anterior
            valores_ajustados[posicion_ajuste] = valor_anterior
            # Para las filas siguientes: sumar el incremental al valor anterior ajustado
            for i in range(posicion_ajuste + 1, n):
                valores_ajustados[i] = valores_ajustados[i-1] + incremental[i]
        # PASO 5: Reemplazar la columna original con los valores ajustados
        nuevo_valor = valores_ajustados[posicion_ajuste]
        df_ajustado[variable] = valores_ajustados
        idcomponente = 0
        comboComponentesLimpieza = AnalisisView.main.findChild(QComboBox, "combo_componentes_limpieza")
        if comboComponentesLimpieza.count() > 0:
            idcomponente = comboComponentesLimpieza.currentData()
        # Llamar al controlador
        respu, existe = AnalisisController.ctrlAjustarDataPrismaCoordenada(df_ajustado, tabla, idcomponente)
        if respu:
            username = Session.get_username()
            nombres = Session.get_nombres()
            if Session.is_authenticated() and AnalisisView.idproyecto:
                AnalisisController.ctrlRegistroAjusteCoordenadas(AnalisisView.idproyecto, tabla, nombreprisma, columnaajuste, int(id_ajuste), current_value, nuevo_valor, str(fecha), username, nombres)
            if existe is False:
                AnalisisView.reiniciarCombosPrismasAnalisis()
                AnalisisView.reiniciarVistasAfectadas("Prisma")
            AnalisisView.graficarCoordenadasPrismas()
    
    def cargarPrismasLimpiezaComponente():
        comboComponentesLimpieza = AnalisisView.main.findChild(QComboBox, "combo_componentes_limpieza")
        comboPrismasLimpieza = AnalisisView.main.findChild(QComboBox, "combo_prismas_limpieza")
        if comboComponentesLimpieza.count() > 0:
            idcomponente = comboComponentesLimpieza.currentData()
            listaprismas = AnalisisController.ctrlObtenerNombresPrismasComponente(idcomponente)
            if listaprismas:
                comboPrismasLimpieza.clear()
                for prisma in listaprismas: # idinstr, idcompo, tipo, nomb, idequipo, tabla, estado
                    comboPrismasLimpieza.addItem(prisma[3], prisma[2])
                AnalisisView.graficarCoordenadasPrismas()
    
    def graficarCoordenadasPrismas():
        comboPrismasLimpiezaDatos = AnalisisView.main.findChild(QComboBox, "combo_prismas_limpieza")
        combo_limpieza_datos = AnalisisView.main.findChild(QComboBox, "combo_tipo_grafico")
        if comboPrismasLimpiezaDatos.count() > 0:
            nombreprisma = comboPrismasLimpiezaDatos.currentText()
            tipoprisma = comboPrismasLimpiezaDatos.currentData()
            tipo_grafico = combo_limpieza_datos.currentData()
            if tipo_grafico == "GE":
                ubicacion = 'X'
            elif tipo_grafico == "GN":
                ubicacion = 'Y'
            elif tipo_grafico == "GC":
                ubicacion = 'Z'
            else:
                ubicacion = 'DISTANCIA'
            datos = AnalisisController.ctrlObtenerDataPrismas(AnalisisView.idproyecto, nombreprisma, tipoprisma)
            if datos:
                widget_desplazamiento_limpieza = AnalisisView.main.findChild(QWidget, "widget_grafica_limpieza_datos")
                AnalisisView.limpiarGraficaLimpieza()
                GraficarCoordenadasPrismas.graficarDesplazamiento(AnalisisView.idproyecto, widget_desplazamiento_limpieza, datos,ubicacion,AnalisisView.ajustarDataPrismaCoordenadas)
        else:
            AnalisisView.limpiarGraficaLimpieza()
    
    def restablecerCambiosPrismasElipse():
        if AnalisisView.idproyecto:
            comboPrismasElipse = AnalisisView.main.findChild(QComboBox, "combo_prismas_elipse")
            if comboPrismasElipse.count() > 0:
                nombreprisma = comboPrismasElipse.currentText()
                tipoprisma = comboPrismasElipse.currentData()
                # crear dialogo
                dlg = QMessageBox()
                dlg.setWindowTitle("Restablecer Prismas")
                dlg.setText(f"¿Está seguro de restablecer cambios del prisma {nombreprisma}?")
                dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                dlg.setIcon(QMessageBox.Question)
                result = dlg.exec()
                if result == QMessageBox.Yes:
                    respuesta = AnalisisController.ctrlRestablecerDataPrismasElipse(AnalisisView.idproyecto, nombreprisma, tipoprisma)
                    if respuesta:
                        AnalisisController.ctrlEliminarRegistroLimpiezaDesviaciones(AnalisisView.idproyecto, nombreprisma, tipoprisma)

                        mostrar_mensaje("Restablecer Prismas", "Se restauró correctamente.", "informacion")
                        AnalisisView.graficarElipseDesviaciones()
                    else:
                        mostrar_mensaje("Restablecer Prismas", "No se pudo restablecer los datos.", "advertencia")
    
    def mostrarCambiosPrismas():
        # Obtener el QComboBox
        comboPrismasLimpiezaDatos = AnalisisView.main.findChild(QComboBox, "combo_prismas_limpieza")
        if comboPrismasLimpiezaDatos.count() > 0:
            nombreprisma = comboPrismasLimpiezaDatos.currentText()
            # Mostrar historial
            dataresumen = AnalisisController.ctrlListarSaltosPrisma(AnalisisView.idproyecto, nombreprisma)
            ResumenPrismas.modalHistoarialSaltosPrismas(dataresumen, nombreprisma)
    
    def LimpiarRuidoManual():
        comboPrismasLimpiezaDatos = AnalisisView.main.findChild(QComboBox, "combo_prismas_limpieza")
        combo_limpieza_datos = AnalisisView.main.findChild(QComboBox, "combo_tipo_grafico")            

        if not comboPrismasLimpiezaDatos or comboPrismasLimpiezaDatos.count() == 0:
            QMessageBox.warning(AnalisisView.main, "Advertencia", "No hay prismas disponibles para analizar")
            return

        nombreprisma = comboPrismasLimpiezaDatos.currentText()
        tipo_grafico = combo_limpieza_datos.currentData()

        column_map = {
            "GE": 'este_target',
            "GN": 'norte_target', 
            "GC": 'elevacion_target'
        }
        columna = column_map.get(tipo_grafico, 'distancia_prisma')

        respuesta = AnalisisController.ctrlObtenerDataCoordenadaAjuste(AnalisisView.idproyecto, nombreprisma, columna)
        if respuesta:
            inspector_dialog = TimeSeriesInspector(respuesta, parent=AnalisisView.main)
            result = inspector_dialog.exec()  # Esto abre la ventana modal y espera cierre
            if result == QDialog.Accepted:
                # Ya se imprimió en confirm_selection, o aquí podrías obtener algo más si lo guardas
                pass
        else:
            QMessageBox.information(AnalisisView.main, "Información", "No hay datos para mostrar")

                         
    # ===== MÉTODO PRINCIPAL AJUSTADO =====
    def LimpiarRuidoGrafico():
        try:
            # Obtener el QComboBox
            comboPrismasLimpiezaDatos = AnalisisView.main.findChild(QComboBox, "combo_prismas_limpieza")
            combo_limpieza_datos = AnalisisView.main.findChild(QComboBox, "combo_tipo_grafico")            
            
            if not comboPrismasLimpiezaDatos or comboPrismasLimpiezaDatos.count() == 0:
                QMessageBox.warning(AnalisisView.main, "Advertencia", "No hay prismas disponibles para analizar")
                return
                
            nombreprisma = comboPrismasLimpiezaDatos.currentText()
            tipo_grafico = combo_limpieza_datos.currentData()
            
            # Mapear tipo de gráfico a columna
            column_map = {
                "GE": 'este_target',
                "GN": 'norte_target', 
                "GC": 'elevacion_target'
            }
            columna = column_map.get(tipo_grafico, 'distancia_prisma')
                
            # Obtener datos de la base de datos
            respuesta = AnalisisController.ctrlObtenerDataCoordenadaAjuste(AnalisisView.idproyecto, nombreprisma, columna)
            
            if not respuesta:
                QMessageBox.warning(AnalisisView.main, "Advertencia", "No se obtuvieron datos del prisma seleccionado")
                return
                
            # Convertir a DataFrame
            df = pd.DataFrame(respuesta, columns=['id_prisma', 'nombre_prisma', 'hora_prisma', columna])
            
            # Asegurar que la columna de fecha es datetime
            df['hora_prisma'] = pd.to_datetime(df['hora_prisma'], errors='coerce')
            
            # Eliminar filas con fechas inválidas
            df = df.dropna(subset=['hora_prisma'])
            
            if len(df) == 0:
                QMessageBox.warning(AnalisisView.main, "Advertencia", "No hay datos válidos para analizar")
                return
                
            # Mostrar el diálogo centrado en la vista principal
            dialog = OutlierDialog(df, columna, AnalisisView.main, initial_tolerance=1.5)
            
            # Asegurar que el diálogo se muestre como ventana modal
            dialog.setWindowModality(Qt.ApplicationModal)
            
            if dialog.exec_() == QDialog.Accepted:
                print("Limpieza confirmada por el usuario")
            else:
                print("Limpieza cancelada por el usuario")
                
        except Exception as e:
            print(f"Error en LimpiarRuidoGrafico: {e}")
            QMessageBox.critical(AnalisisView.main, "Error", f"Error en el análisis: {str(e)}")
            
    # ===== FUNCIONES DE DETECCIÓN DE OUTLIERS =====
    def detect_outliers_zscore(df: pd.DataFrame, value_column: str = 'Este', 
                            threshold: float = 3) -> pd.Series:
        mean = df[value_column].mean()
        std = df[value_column].std()
        z_scores = np.abs((df[value_column] - mean) / std)
        return z_scores > threshold

    def detect_outliers_iqr(df: pd.DataFrame, value_column: str = 'Este', 
                        multiplier: float = 1.5) -> Tuple[pd.Series, Dict[str, Any]]:
        Q1 = df[value_column].quantile(0.25)
        Q3 = df[value_column].quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - multiplier * IQR
        upper_bound = Q3 + multiplier * IQR
        
        outliers = (df[value_column] < lower_bound) | (df[value_column] > upper_bound)
        
        stats_dict = {
            'Q1': Q1, 'Q3': Q3, 'IQR': IQR,
            'lower_bound': lower_bound, 'upper_bound': upper_bound
        }
        
        return outliers, stats_dict

    def analyze_outliers(df: pd.DataFrame, method: str = 'iqr', value_column: str = 'Este', 
                    **kwargs) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
        df = df.copy()
        
        if method == 'zscore':
            threshold = kwargs.get('threshold', 3)
            outliers = AnalisisView.detect_outliers_zscore(df, value_column, threshold)
            results = {
                'method': 'Z-Score',
                'threshold': threshold
            }
        else:
            multiplier = kwargs.get('multiplier', 1.5)
            outliers, stats = AnalisisView.detect_outliers_iqr(df, value_column, multiplier)
            results = {**stats, 'method': 'IQR', 'multiplier': multiplier}
        
        df['is_outlier'] = outliers
        df_clean = df[~outliers].copy()
        
        # Obtener los IDs de los valores atípicos
        outlier_ids = df[outliers]['id_prisma'].tolist() if 'id_prisma' in df.columns else []
        
        # Obtener el nombre del equipo (prisma)
        equipo_nombre = df['nombre_prisma'].iloc[0] if 'nombre_prisma' in df.columns and len(df) > 0 else "Desconocido"
        
        results.update({
            'total_data': len(df),
            'outliers_count': outliers.sum(),
            'clean_data': len(df_clean),
            'outlier_values': df[outliers][value_column].values,
            'outlier_ids': outlier_ids,  # Lista de IDs atípicos
            'equipo_nombre': equipo_nombre,  # Nombre del equipo
            'outlier_dates': df[outliers]['hora_prisma'].values if 'hora_prisma' in df.columns else None,
            'value_column': value_column
        })
        
        return df, df_clean, results

    def aplicarMetodoLimpiezaHistograma():
        combo_prismas = AnalisisView.main.findChild(QComboBox, "combo_prismas_histograma")
        if combo_prismas.count() > 0:
            nombreprisma = combo_prismas.currentText()
            tipoprisma, idcompo = combo_prismas.currentData()
            combo_tipografica = AnalisisView.main.findChild(QComboBox, "combo_tipografica_histograma")
            tipografica = combo_tipografica.currentData()
            spinintervalo = AnalisisView.main.findChild(QSpinBox, "spin_intervalo_histograma")
            intervalos = spinintervalo.value()
            widget_histograma = AnalisisView.main.findChild(QWidget, "widget_histograma")
            titulografica = f"Histograma - Prisma {nombreprisma}"
            config = SoftwareConfiguracion.obtenerDataSoftware()
            tipovelocidad, filtrado = config[15], config[16]
            data = AnalisisController.ctrlTraerDataHistograma(AnalisisView.idproyecto, nombreprisma, idcompo, tipoprisma, tipografica, AnalisisView.fechainicial, AnalisisView.fechafinal, filtrado, tipovelocidad)
            if data:
                combo_limpieza = AnalisisView.main.findChild(QComboBox, "combo_limpieza_histograma")
                tipoLimpieza = combo_limpieza.currentData()
                spinvalork = AnalisisView.main.findChild(QSpinBox, "spin_valork_histograma")
                valorK = spinvalork.value()
                idxlectura = 5
                nvdata = CalculosTendencias.aplicarMetodoLimpiezaIQRestadistico(data, idxlectura, tipoLimpieza, valorK)
                if nvdata:
                    if tipografica.startswith('V'):
                        labelejex = "Velocidad (m/d)"
                    else:
                        labelejex = "Desplazamiento (m)"
                    labelejey = "Frecuencia (u)"
                    procesar_grafica_histograma(widget_histograma, nvdata, intervalos, nombreprisma, idxlectura, labelejex, labelejey, titulografica)
    
    def limpiarGraficaTrayectoria():
        widget_trayectoria = AnalisisView.main.findChild(QWidget, "widget_trayectoria")
        GraficarEstereografiaTrayectoria.limpiar_widget(widget_trayectoria)
    
    def limpiarGraficaEstereografia():
        widget_estereografia = AnalisisView.main.findChild(QWidget, "widget_estereografia")
        GraficarEstereografiaTrayectoria.limpiar_widget(widget_estereografia)
        
    def limpiarGraficaInversaVelocidad():
        widget_analisis = AnalisisView.main.findChild(QWidget, "widget_analisis")
        GraficarEstereografiaTrayectoria.limpiar_widget(widget_analisis)
    
    def limpiarGraficaTiempoReal():
        widget_tiemporeal = AnalisisView.main.findChild(QWidget, "widget_graficas_tiemporeal")
        if widget_tiemporeal:
            # Cerrar figuras de matplotlib para liberar memoria
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
            for child in widget_tiemporeal.findChildren(FigureCanvas):
                try:
                    plt.close(child.figure)
                except Exception:
                    pass
        GraficarEstereografiaTrayectoria.limpiar_widget(widget_tiemporeal)
    
    def limpiarGraficaVariacion():
        widget_variacion = AnalisisView.main.findChild(QWidget, "widget_variaciones")
        GraficarEstereografiaTrayectoria.limpiar_widget(widget_variacion)
        
    def limpiarGraficaHistograma():
        widget_histograma = AnalisisView.main.findChild(QWidget, "widget_histograma")
        GraficarEstereografiaTrayectoria.limpiar_widget(widget_histograma)
        
    def limpiarGraficaBarras():
        widget_barras = AnalisisView.main.findChild(QWidget, "widget_resumen_equipos")
        GraficarEstereografiaTrayectoria.limpiar_widget(widget_barras)
        
    def limpiarGraficaElipse():
        widget_elipse = AnalisisView.main.findChild(QWidget, "widget_elipse_error")
        widget_primera_desviacion = AnalisisView.main.findChild(QWidget, "widget_primera_desviacion")
        widget_segunda_desviacion = AnalisisView.main.findChild(QWidget, "widget_segunda_desviacion")
        widget_tercera_desviacion = AnalisisView.main.findChild(QWidget, "widget_tercera_desviacion")
        GraficarEstereografiaTrayectoria.limpiar_widget(widget_elipse)
        GraficarEstereografiaTrayectoria.limpiar_widget(widget_primera_desviacion)
        GraficarEstereografiaTrayectoria.limpiar_widget(widget_segunda_desviacion)
        GraficarEstereografiaTrayectoria.limpiar_widget(widget_tercera_desviacion)
        
    def limpiarGraficaLimpieza():
        widget_limpieza_datos = AnalisisView.main.findChild(QWidget, "widget_grafica_limpieza_datos")
        GraficarEstereografiaTrayectoria.limpiar_widget(widget_limpieza_datos)
        
    def limpiarGraficasAnalisis():
        AnalisisView.limpiarGraficaTrayectoria()
        AnalisisView.limpiarGraficaEstereografia()
        AnalisisView.limpiarGraficaInversaVelocidad()
        AnalisisView.limpiarGraficaTiempoReal()
        AnalisisView.limpiarGraficaVariacion()
        AnalisisView.limpiarGraficaHistograma()
        AnalisisView.limpiarGraficaBarras()
        AnalisisView.limpiarGraficaElipse()
        AnalisisView.limpiarGraficaLimpieza()
    
    def modalRegistroTaludes(tree_actual):
        if AnalisisView.idproyecto:
            respuesta = RegistroEstereografia.modalRegistroEstereografia(AnalisisView.idproyecto)
            if respuesta:
                AnalisisView.validarGraficaEstereografia(tree_actual)
    
    def mostrarDialogoReporteAnalisis(treeWidget, tipovista, tiporeporte):
        if AnalisisView.idproyecto:
            opcion = False
            if tipovista == "Analisis":
                lista = EquiposAnalisis.obtener_todos_elementos_marcados(treeWidget)
                if lista:
                    opcion =  True
                    titulografica = "Inversa de la velocidad"
                    tipografico = "IVP"
                    widget_grafico = AnalisisView.main.findChild(QWidget, "widget_analisis")
            elif tipovista == "Estereografia":
                lista = EquiposAnalisis.obtener_todos_elementos_marcados(treeWidget)
                if lista:
                    opcion =  True
                    titulografica = "Estereografía"
                    tipografico = "STER"
                    widget_grafico = AnalisisView.main.findChild(QWidget, "widget_estereografia")
            elif tipovista == "Trayectoria":
                opcion =  True
                titulografica = "Trayectoria"
                tipografico = "TRAY"
                widget_grafico = AnalisisView.main.findChild(QWidget, "widget_trayectoria")
            elif tipovista == "Histograma":
                opcion =  True
                titulografica = "Histograma"
                tipografico = "HIST"
                widget_grafico = AnalisisView.main.findChild(QWidget, "widget_histograma")
            elif tipovista == "Variacion":
                opcion =  True
                combo_variaciones = AnalisisView.main.findChild(QComboBox, "combo_coordenadas_variacion")
                tipografica = combo_variaciones.currentData()
                if tipografica == "VEN":
                    titulografica = "Variación Este y Norte"
                else:
                    titulografica = "Variación en Cota"
                tipografico = "VARI"
                widget_grafico = AnalisisView.main.findChild(QWidget, "widget_variaciones")
            elif tipovista == "Resumen":
                opcion =  True
                titulografica = "Resumen de Prismas"
                tipografico = "REPR"
                widget_grafico = AnalisisView.main.findChild(QWidget, "widget_resumen_equipos")
            elif tipovista == "Elipse":
                opcion =  True
                titulografica = "Elipse de Desviaciones"
                tipografico = "ELID"
                widget_grafico = AnalisisView.main.findChild(QWidget, "widget_elipse_error")
            if opcion:
                tipoequipo = "Prisma"
                if tiporeporte == "General":
                    GraficaReporte.mostrarDialogoImagenVisor(widget_grafico, "Analisis", tipografico, titulografica, AnalisisView.idproyecto, tipoequipo)
                else:
                    ReporteImage.modalImagenReporte(widget_grafico, "Analisis", tipografico, titulografica, AnalisisView.idproyecto, tipoequipo)
    
    def mostrarModalLimpiezaRuido(treeWidget):
        lista = EquiposAnalisis.obtener_todos_elementos_marcados(treeWidget)
        if lista:
            prismasmarcados = AnalisisView.obtenerListaEquiposMarcados(lista, "Prismas")
            if len(prismasmarcados) > 0:
                estado, metodoLimpieza, prismasLimpieza = Personalizacion.dialogoLimpiezaRuidoPrismas(prismasmarcados)
                if estado:
                    config = SoftwareConfiguracion.obtenerDataSoftware()
                    filtrado = config[16]
                    combotiempos = AnalisisView.main.findChild(QComboBox, "combo_tiempo_analisis")
                    unidadtiempo = combotiempos.currentData()
                    escala = None
                    tipografico = 'IV'
                    widget_analisis = AnalisisView.main.findChild(QWidget, "widget_analisis")
                    combo_escala = AnalisisView.main.findChild(QComboBox, "combo_escala_analisis")
                    tipoescala = combo_escala.currentData()
                    combo_velocidad = AnalisisView.main.findChild(QComboBox, "combo_velocidad_analisis")
                    velocidad = combo_velocidad.currentData()
                    if velocidad == "DM":
                        unidadmedida = 1
                        labelejey = "Inversa velocidad (d/m)"
                    elif velocidad == "DCM":
                        unidadmedida = 1/100
                        labelejey = "Inversa velocidad (d/cm)"
                    elif velocidad == "DMM":
                        unidadmedida = 1/1000
                        labelejey = "Inversa velocidad (d/mm)"
                    elif velocidad == "HM":
                        unidadmedida = 24
                        labelejey = "Inversa velocidad (h/m)"
                    elif velocidad == "HCM":
                        unidadmedida = 24/100
                        labelejey = "Inversa velocidad (h/cm)"
                    else:
                        unidadmedida = 24/1000
                        labelejey = "Inversa velocidad (h/mm)"
                    if unidadtiempo == "FECHA":
                        labelejex = "Fechas"
                        idx_fecha = 2
                        idx_lectura = 6
                        escala = None
                    elif unidadtiempo == "DIA":
                        labelejex = "Días"
                        idx_fecha = 3
                        idx_lectura = 6
                    else:
                        labelejex = "Horas"
                        idx_fecha = 4
                        idx_lectura = 5
                    if tipoescala == "SEL":
                        titulografica = "Inversa de la Velocidad"
                    elif tipoescala == "ESL":
                        if unidadtiempo == "FECHA":
                            titulografica = "Inversa de la Velocidad"
                        else:
                            titulografica = "Inversa de la Velocidad Semilogarítmica"
                            escala = tipoescala
                    else:
                        if unidadtiempo == "FECHA":
                            titulografica = "Inversa de la Velocidad"
                        else:
                            titulografica = "Inversa de la Velocidad Logarítmica"
                            escala = tipoescala
                    datos = AnalisisController.ctrlCalcularDatosGrafica(AnalisisView.idproyecto, prismasmarcados, AnalisisView.fechainicial, AnalisisView.fechafinal, tipografico, filtrado, unidadmedida)
                    if len(datos) > 0:
                        if metodoLimpieza == 'Limpieza Automática':
                            data = CalculosTendencias.limpiezaAutomaticaSaltos(datos, prismasLimpieza, 1, idx_lectura)
                        elif metodoLimpieza == 'Limpieza Manual':
                            data = CalculosTendencias.limpiezaManualSaltos(datos, prismasLimpieza, 1, idx_lectura)
                        elif metodoLimpieza == 'Ajustar Gráfico':
                            data = CalculosTendencias.ajustarCalculoSaltos(datos, prismasLimpieza, 1, idx_lectura)
                        labeltendencia = AnalisisView.main.findChild(QLabel, "label_tendencia_analisis")
                        modulo, pluviometros, tendencias = "ANALISIS", None, None
                        if filtrado == 0:
                            procesar_grafica(widget_analisis, labeltendencia, data, 1, idx_fecha, idx_lectura, labelejex, labelejey, tipografico, unidadmedida, unidadtiempo, titulografica, AnalisisView.idproyecto, modulo, pluviometros, tendencias, escala, AnalisisView.fechainicial, AnalisisView.fechafinal)
                        else:
                            procesar_grafica(widget_analisis, labeltendencia, data, 1, idx_fecha, idx_lectura, labelejex, labelejey, tipografico, unidadmedida, unidadtiempo, titulografica, AnalisisView.idproyecto, modulo, pluviometros, tendencias, escala)
    
    def mostrarModalTendencia(treeWidget):
        lista = EquiposAnalisis.obtener_todos_elementos_marcados(treeWidget)
        if lista:
            prismasmarcados = AnalisisView.obtenerListaEquiposMarcados(lista, "Prismas")
            if len(prismasmarcados) > 0:
                regresion = Personalizacion.dialogoFiltroRegresionPrismas(prismasmarcados)
                if len(regresion) > 0:
                    config = SoftwareConfiguracion.obtenerDataSoftware()
                    filtrado = config[16]
                    combotiempos = AnalisisView.main.findChild(QComboBox, "combo_tiempo_analisis")
                    unidadtiempo = combotiempos.currentData()
                    escala = None
                    tipografico = 'IV'
                    widget_analisis = AnalisisView.main.findChild(QWidget, "widget_analisis")
                    combo_escala = AnalisisView.main.findChild(QComboBox, "combo_escala_analisis")
                    tipoescala = combo_escala.currentData()
                    combo_velocidad = AnalisisView.main.findChild(QComboBox, "combo_velocidad_analisis")
                    velocidad = combo_velocidad.currentData()
                    if velocidad == "DM":
                        unidadmedida = 1
                        labelejey = "Inversa velocidad (d/m)"
                    elif velocidad == "DCM":
                        unidadmedida = 1/100
                        labelejey = "Inversa velocidad (d/cm)"
                    elif velocidad == "DMM":
                        unidadmedida = 1/1000
                        labelejey = "Inversa velocidad (d/mm)"
                    elif velocidad == "HM":
                        unidadmedida = 24
                        labelejey = "Inversa velocidad (h/m)"
                    elif velocidad == "HCM":
                        unidadmedida = 24/100
                        labelejey = "Inversa velocidad (h/cm)"
                    else:
                        unidadmedida = 24/1000
                        labelejey = "Inversa velocidad (h/mm)"
                    if unidadtiempo == "FECHA":
                        labelejex = "Fechas"
                        idx_fecha = 2
                        idx_lectura = 6
                        escala = None
                    elif unidadtiempo == "DIA":
                        labelejex = "Días"
                        idx_fecha = 3
                        idx_lectura = 6
                    else:
                        labelejex = "Horas"
                        idx_fecha = 4
                        idx_lectura = 5
                    if tipoescala == "SEL":
                        titulografica = "Inversa de la Velocidad"
                    elif tipoescala == "ESL":
                        if unidadtiempo == "FECHA":
                            titulografica = "Inversa de la Velocidad"
                        else:
                            titulografica = "Inversa de la Velocidad Semilogarítmica"
                            escala = tipoescala
                    else:
                        if unidadtiempo == "FECHA":
                            titulografica = "Inversa de la Velocidad"
                        else:
                            titulografica = "Inversa de la Velocidad Logarítmica"
                            escala = tipoescala
                    datos = AnalisisController.ctrlCalcularDatosGrafica(AnalisisView.idproyecto, prismasmarcados, AnalisisView.fechainicial, AnalisisView.fechafinal, tipografico, filtrado, unidadmedida)
                    if len(datos) > 0:
                        labeltendencia = AnalisisView.main.findChild(QLabel, "label_tendencia_analisis")
                        modulo, pluviometros = "ANALISIS", None
                        if filtrado == 0:
                            procesar_grafica(widget_analisis, labeltendencia, datos, 1, idx_fecha, idx_lectura, labelejex, labelejey, tipografico, unidadmedida, unidadtiempo, titulografica, AnalisisView.idproyecto, modulo, pluviometros, regresion, escala, AnalisisView.fechainicial, AnalisisView.fechafinal)
                        else:
                            procesar_grafica(widget_analisis, labeltendencia, datos, 1, idx_fecha, idx_lectura, labelejex, labelejey, tipografico, unidadmedida, unidadtiempo, titulografica, AnalisisView.idproyecto, modulo, pluviometros, regresion, escala)

    def graficarUmbralesTiempoReal():
        comboComponentes = AnalisisView.main.findChild(QComboBox, "combo_componentes_tiemporeal")
        if comboComponentes.count() == 0:
            return
        widget = AnalisisView.main.findChild(QWidget, "widget_graficas_tiemporeal")
        comboInstrumentos = AnalisisView.main.findChild(QComboBox, "combo_instrumentos_tiemporeal")
        comboTipograficas = AnalisisView.main.findChild(QComboBox, "combo_tipografica_tiemporeal")
        comboUnidades = AnalisisView.main.findChild(QComboBox, "combo_unidades_tiemporeal")
        instrumento = comboInstrumentos.currentData() or "PRISMA"
        tipografico = comboTipograficas.currentData() or "DA3D"
        unidad = comboUnidades.currentData() or 1
        tabla = 'umbral_prisma' if instrumento == "PRISMA" else 'umbral_piezometro' if instrumento == "PIEZOMETROCUERDA" else 'umbral_celda'

        validar = UmbralController.ctrlValidarUmbralesComponentes(AnalisisView.idproyecto, tipografico, tabla)
        if not validar:
            return
        cantidad, idcomponen = validar
        if cantidad == 0:
            return

        umbrales = None
        if cantidad == 1:
            AnalisisView._umbral_idcomponente = idcomponen  # guardar selección
            umbrales = UmbralController.ctrlObtenerUmbralesInstrumentacion(
                AnalisisView.idproyecto, idcomponen, tipografico, tabla
            )
        else:
            componentes = UmbralController.ctrlListarComponentesUmbrales(
                AnalisisView.idproyecto, tipografico, tabla
            )
            if componentes:
                codigoseleccionado = GraficarUmbrales.mostrarSeleccionUmbrales(componentes, "Umbral Prismas")
                if codigoseleccionado:
                    AnalisisView._umbral_idcomponente = codigoseleccionado  # guardar selección
                    umbrales = UmbralController.ctrlObtenerUmbralesInstrumentacion(
                        AnalisisView.idproyecto, codigoseleccionado, tipografico, tabla
                    )
        if umbrales:
            GraficarUmbrales.draw_on_widget(widget, umbrales, unidad)

    def mostrarModalConfiguracionEjesInversaVelocidad(treeWidget):
        lista = EquiposAnalisis.obtener_todos_elementos_marcados(treeWidget)
        if lista:
            prismasmarcados = AnalisisView.obtenerListaEquiposMarcados(lista, "Prismas")
            if len(prismasmarcados) > 0:
                combo_velocidad = AnalisisView.main.findChild(QComboBox, "combo_velocidad_analisis")
                velocidad = combo_velocidad.currentData()
                combotiempos = AnalisisView.main.findChild(QComboBox, "combo_tiempo_analisis")
                tiempomedida = combotiempos.currentData()
                if velocidad == "DM":
                    unidadmedida = 1
                    labelejey = "Inversa velocidad (d/m)"
                elif velocidad == "DCM":
                    unidadmedida = 1/100
                    labelejey = "Inversa velocidad (d/cm)"
                elif velocidad == "DMM":
                    unidadmedida = 1/1000
                    labelejey = "Inversa velocidad (d/mm)"
                elif velocidad == "HM":
                    unidadmedida = 24
                    labelejey = "Inversa velocidad (h/m)"
                elif velocidad == "HCM":
                    unidadmedida = 24/100
                    labelejey = "Inversa velocidad (h/cm)"
                else:
                    unidadmedida = 24/1000
                    labelejey = "Inversa velocidad (h/mm)"
                if tiempomedida == "FECHA":
                    labelejex = "Fechas"
                    idx_fecha = 2
                    idx_lectura = 6
                    escala = None
                    unidadtiempo = 1
                elif tiempomedida == "DIA":
                    labelejex = "Días"
                    idx_fecha = 3
                    idx_lectura = 6
                    unidadtiempo = 1
                else:
                    labelejex = "Horas"
                    idx_fecha = 4
                    idx_lectura = 5
                    unidadtiempo = 24
                infoeje = ConfiguracionController.ctrlObtenerConfiguracionEje(AnalisisView.idproyecto, "ANALISIS", "IV")
                if infoeje:
                    ejeymin, ejeymax, ejeyprim, ejeysecu, interdias = infoeje[4], infoeje[5], infoeje[6], infoeje[7], infoeje[8]
                else:
                    ejeymin, ejeymax, ejeyprim, ejeysecu, interdias = 0, 0, 0, 0, 0
                estadoeje, minejey, maxejey, primario, secundario, dias = Personalizacion.dialogoConfiguracionEjes(ejeymin, ejeymax, ejeyprim, ejeysecu, interdias, unidadmedida, unidadtiempo)
                if estadoeje:
                    # guardar configuracion
                    respuesta = ConfiguracionController.ctrlActualizarConfiguracionEjes(AnalisisView.idproyecto, "ANALISIS", "IV", minejey, maxejey, primario, secundario, dias)
                    if respuesta:
                        config = SoftwareConfiguracion.obtenerDataSoftware()
                        filtrado = config[16]
                        escala = None
                        tipografico = 'IV'
                        widget_analisis = AnalisisView.main.findChild(QWidget, "widget_analisis")
                        combo_escala = AnalisisView.main.findChild(QComboBox, "combo_escala_analisis")
                        tipoescala = combo_escala.currentData()
                        if tipoescala == "SEL":
                            titulografica = "Inversa de la Velocidad"
                        elif tipoescala == "ESL":
                            if tiempomedida == "FECHA":
                                titulografica = "Inversa de la Velocidad"
                            else:
                                titulografica = "Inversa de la Velocidad Semilogarítmica"
                                escala = tipoescala
                        else:
                            if tiempomedida == "FECHA":
                                titulografica = "Inversa de la Velocidad"
                            else:
                                titulografica = "Inversa de la Velocidad Logarítmica"
                                escala = tipoescala
                        datos = AnalisisController.ctrlCalcularDatosGrafica(AnalisisView.idproyecto, prismasmarcados, AnalisisView.fechainicial, AnalisisView.fechafinal, tipografico, filtrado, unidadmedida)
                        if len(datos) > 0:
                            labeltendencia = AnalisisView.main.findChild(QLabel, "label_tendencia_analisis")
                            modulo, pluviometros, tendencias = "ANALISIS", None, None
                            if filtrado == 0:
                                procesar_grafica(widget_analisis, labeltendencia, datos, 1, idx_fecha, idx_lectura, labelejex, labelejey, tipografico, unidadmedida, tiempomedida, titulografica, AnalisisView.idproyecto, modulo, pluviometros, tendencias, escala, AnalisisView.fechainicial, AnalisisView.fechafinal)
                            else:
                                procesar_grafica(widget_analisis, labeltendencia, datos, 1, idx_fecha, idx_lectura, labelejex, labelejey, tipografico, unidadmedida, tiempomedida, titulografica, AnalisisView.idproyecto, modulo, pluviometros, tendencias, escala)
    
    def mostrarModalConfiguracionEjesCoordenadas(treeWidget):
        lista = EquiposAnalisis.obtener_todos_elementos_marcados(treeWidget)
        if lista:
            prismasmarcados = AnalisisView.obtenerListaEquiposMarcados(lista, "Prismas")
            if len(prismasmarcados) > 0:
                combovariaciones = AnalisisView.main.findChild(QComboBox, "combo_coordenadas_variacion")
                tipografica = combovariaciones.currentData()
                infoeje = ConfiguracionController.ctrlObtenerConfiguracionEje(AnalisisView.idproyecto, "ANALISIS", tipografica)
                if infoeje:
                    ejeymin, ejeymax, ejeyprim, ejeysecu, interdias = infoeje[4], infoeje[5], infoeje[6], infoeje[7], infoeje[8]
                else:
                    ejeymin, ejeymax, ejeyprim, ejeysecu, interdias = 0, 0, 0, 0, 0
                estadoeje, minejey, maxejey, primario, secundario, dias = Personalizacion.dialogoConfiguracionEjes(ejeymin, ejeymax, ejeyprim, ejeysecu, interdias, 1, 1)
                if estadoeje:
                    # guardar configuracion
                    respuesta = ConfiguracionController.ctrlActualizarConfiguracionEjes(AnalisisView.idproyecto, "ANALISIS", tipografica, minejey, maxejey, primario, secundario, dias)
                    if respuesta:
                        AnalisisView.graficarVariacionesCoordenadas(prismasmarcados)
    
    def mostrarModalConfiguracionEjesTiempoReal():
        comboComponentes = AnalisisView.main.findChild(QComboBox, "combo_componentes_tiemporeal")
        if comboComponentes.count() > 0:
            comboInstrumentos = AnalisisView.main.findChild(QComboBox, "combo_instrumentos_tiemporeal")
            comboTipograficas = AnalisisView.main.findChild(QComboBox, "combo_tipografica_tiemporeal")
            comboUnidades = AnalisisView.main.findChild(QComboBox, "combo_unidades_tiemporeal")
            instrumento = comboInstrumentos.currentData() or "PRISMA"
            tipografico = comboTipograficas.currentData() or "DA3D"
            unidad = comboUnidades.currentData() or 1
            graficatipo = f"{instrumento}{tipografico}"
            unidadtiempo = 1
            infoeje = ConfiguracionController.ctrlObtenerConfiguracionEje(AnalisisView.idproyecto, "ANALISIS", graficatipo)
            if infoeje:
                ejeymin, ejeymax, ejeyprim, ejeysecu, interdias = infoeje[4], infoeje[5], infoeje[6], infoeje[7], infoeje[8]
            else:
                ejeymin, ejeymax, ejeyprim, ejeysecu, interdias = 0, 0, 0, 0, 0
            estadoeje, minejey, maxejey, primario, secundario, dias = Personalizacion.dialogoConfiguracionEjes(ejeymin, ejeymax, ejeyprim, ejeysecu, interdias, unidad, unidadtiempo)
            if estadoeje:
                # guardar configuracion
                respuesta = ConfiguracionController.ctrlActualizarConfiguracionEjes(AnalisisView.idproyecto, "ANALISIS", graficatipo, minejey, maxejey, primario, secundario, dias)
                if respuesta:
                    AnalisisView.GraficarTiempoReal()
    
    def modalAsignarTiempo():
        if not AnalisisView.idproyecto:
            return
        dialog = QDialog(AnalisisView.main)
        dialog.setWindowTitle("Configurar Intervalo de Actualización")
        dialog.setFixedWidth(320)
        dialog.setModal(True)
        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        # Etiqueta informativa
        lbl_info = QLabel("Ingrese el intervalo de actualización\npara la gráfica en tiempo real:")
        lbl_info.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_info)
        # Fila de input
        fila = QHBoxLayout()
        lbl_min = QLabel("Minutos:")
        spin = QSpinBox()
        spin.setMinimum(1)
        spin.setMaximum(60)
        spin.setValue(AnalisisView._intervalo_tiempo_real)  # mostrar valor actual
        spin.setSuffix(" min")
        spin.setFixedWidth(100)
        fila.addWidget(lbl_min)
        fila.addStretch()
        fila.addWidget(spin)
        layout.addLayout(fila)
        # Etiqueta que muestra el estado actual
        lbl_actual = QLabel(f"Intervalo actual: {AnalisisView._intervalo_tiempo_real} minuto(s)")
        lbl_actual.setStyleSheet("color: gray; font-size: 11px;")
        lbl_actual.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_actual)
        # Botones
        botones = QHBoxLayout()
        btn_confirmar = QPushButton("Confirmar")
        btn_cancelar = QPushButton("Cancelar")
        btn_confirmar.setFixedHeight(32)
        btn_cancelar.setFixedHeight(32)
        botones.addWidget(btn_confirmar)
        botones.addWidget(btn_cancelar)
        layout.addLayout(botones)
        def confirmar():
            minutos = spin.value()
            AnalisisView._intervalo_tiempo_real = minutos
            # Si el timer está activo, reiniciarlo con el nuevo intervalo
            if AnalisisView._timer_tiempo_real is not None:
                AnalisisView.iniciarTimerTiempoReal()
            dialog.accept()
        btn_confirmar.clicked.connect(confirmar)
        btn_cancelar.clicked.connect(dialog.reject)
        dialog.exec()
    
    def actualizarVistaAnalisis(fechaini, fechafin, filtro=False):
        AnalisisView.fechainicial = fechaini
        AnalisisView.fechafinal = fechafin
        if AnalisisView.idproyecto:
            treeWidget =  AnalisisView.main.findChild(QTreeWidget, "tree_actual_analisis")
            AnalisisView.obtenerMostrarPrismasMarcados(treeWidget)
    
    def mostrarDataTablaDesviaciones():
        if AnalisisView.idproyecto:
            comboPrismasElipse = AnalisisView.main.findChild(QComboBox, "combo_prismas_elipse")
            nombreprisma = comboPrismasElipse.currentText()
            tipoprisma = comboPrismasElipse.currentData()
            ResumenPrismas.modalDataTablaDesviaciones(AnalisisView.idproyecto, nombreprisma, tipoprisma)
    
    def reiniciarVistaAnalisis(main, proyecto_id, proyecto_name):
        # reiniciar variables
        AnalisisView.main = main
        AnalisisView.idproyecto = proyecto_id
        AnalisisView.nameproyecto = proyecto_name
        AnalisisView.estadochecklist = True
        AnalisisView.limpiarGraficasAnalisis()
    
    def iniciarAsistenteVozAnalisis(treeWidget, botonvoz):
        prismasmarcados, trayectoriagraficado, histogramagraficado = [], False, False
        widget_trayectoria = AnalisisView.main.findChild(QWidget, "widget_trayectoria")
        if widget_trayectoria:
            canvas = next((child for child in widget_trayectoria.children() if isinstance(child, FigureCanvas)), None)
            trayectoriagraficado = canvas is not None
        widget_histograma = AnalisisView.main.findChild(QWidget, "widget_histograma")
        if widget_histograma:
            canvash = next((child for child in widget_histograma.children() if isinstance(child, FigureCanvas)), None)
            histogramagraficado = canvash is not None
        lista = EquiposAnalisis.obtener_todos_elementos_marcados(treeWidget)
        if lista:
            prismasmarcados = AnalisisView.obtenerListaEquiposMarcados(lista, "Prismas")
        if len(prismasmarcados) > 0 or trayectoriagraficado or histogramagraficado:
            tipo_grafico_analisis = AnalisisView.main.findChild(QComboBox, "combo_graficas_analisis")
            tipografico = tipo_grafico_analisis.currentData()
            botonvoz.setEnabled(False)
            hilo_asistente = threading.Thread(target=AsistenteVoz.analizarVistaAnalisis, args=(AnalisisView.main, AnalisisView.idproyecto, prismasmarcados, trayectoriagraficado, histogramagraficado, AnalisisView.fechainicial, AnalisisView.fechafinal, tipografico, botonvoz))
            hilo_asistente.start()
    
    # Nuevo método interno para pintar umbrales sin diálogos
    def aplicarUmbralesTiempoReal():
        try:
            widget = AnalisisView.main.findChild(QWidget, "widget_graficas_tiemporeal")
            comboInstrumentos = AnalisisView.main.findChild(QComboBox, "combo_instrumentos_tiemporeal")
            comboTipograficas = AnalisisView.main.findChild(QComboBox, "combo_tipografica_tiemporeal")
            comboUnidades = AnalisisView.main.findChild(QComboBox, "combo_unidades_tiemporeal")
            instrumento = comboInstrumentos.currentData() or "PRISMA"
            tipografico = comboTipograficas.currentData() or "DA3D"
            unidad = comboUnidades.currentData() or 1
            tabla = 'umbral_prisma' if instrumento == "PRISMA" else 'umbral_piezometro' if instrumento == "PIEZOMETROCUERDA" else 'umbral_celda'

            validar = UmbralController.ctrlValidarUmbralesComponentes(AnalisisView.idproyecto, tipografico, tabla)
            if not validar:
                return
            cantidad, idcomponen = validar
            if cantidad == 0:
                return

            # Usar el componente recordado, o el primero disponible si no hay uno guardado
            if AnalisisView._umbral_idcomponente is not None:
                idseleccionado = AnalisisView._umbral_idcomponente
            else:
                idseleccionado = idcomponen  # primero disponible

            umbrales = UmbralController.ctrlObtenerUmbralesInstrumentacion(
                AnalisisView.idproyecto, idseleccionado, tipografico, tabla
            )
            if umbrales:
                GraficarUmbrales.draw_on_widget(widget, umbrales, unidad)
        except Exception:
            pass  # No interrumpir el refresco si umbrales falla
        
    # Timer de tiempo real
    def iniciarTimerTiempoReal():
        if AnalisisView._timer_tiempo_real is not None:
            AnalisisView._timer_tiempo_real.stop()
            AnalisisView._timer_tiempo_real = None

        timer = QTimer()
        timer.setInterval(AnalisisView._intervalo_tiempo_real * 60 * 1000)
        timer.timeout.connect(AnalisisView.GraficarTiempoReal)
        timer.start()
        AnalisisView._timer_tiempo_real = timer

    def detenerTimerTiempoReal():
        if AnalisisView._timer_tiempo_real is not None:
            AnalisisView._timer_tiempo_real.stop()
            AnalisisView._timer_tiempo_real = None


# Eje de fechas en X
class DateAxis(pg.AxisItem):
    def tickStrings(self, values, scale, spacing):
        strings = []
        for value in values:
            try:
                dt = datetime.fromtimestamp(value)
                strings.append(dt.strftime('%Y-%m-%d'))
            except Exception:
                strings.append('')
        return strings

class TimeSeriesInspector(QDialog):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Limpieza Manual de Series Temporales")
        self.resize(1000, 650)

        # --- GESTIÓN DE ESTADO (DESHACER) ---
        self.marked_indices = set()
        self.history_stack = []  # Pila para el historial

        # --- DATOS (Híbrido SQLite/SQLServer) ---
        self.data = data
        self.ids = [item[0] for item in self.data]
        
        # Validación robusta de fechas (String vs Datetime)
        self.dates = []
        for item in self.data:
            raw_date = item[2]
            if isinstance(raw_date, str):
                self.dates.append(datetime.strptime(raw_date, '%Y-%m-%d %H:%M:%S'))
            else:
                self.dates.append(raw_date)

        self.values = np.array([item[3] for item in self.data], dtype=float)
        self.timestamps = np.array([dt.timestamp() for dt in self.dates], dtype=float)

        # Layout principal
        layout = QVBoxLayout(self)

        # Ejes personalizados
        try:
            date_axis = DateAxis(orientation='bottom')
            decimal_axis = DecimalAxis(orientation='left')
            self.plot_widget = pg.PlotWidget(axisItems={'bottom': date_axis, 'left': decimal_axis})
        except NameError:
            self.plot_widget = pg.PlotWidget(axisItems={'bottom': pg.DateAxisItem()})

        layout.addWidget(self.plot_widget)

        # Estilo gráfico
        self.plot_widget.setBackground('w')
        axis_pen = pg.mkPen(color=(80, 80, 80), width=1)
        for axis_name in ['bottom', 'left', 'top', 'right']:
            axis = self.plot_widget.getAxis(axis_name)
            axis.setPen(axis_pen)
            axis.setTextPen(axis_pen)
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)

        # Línea principal
        self.curve = self.plot_widget.plot(
            self.timestamps, self.values,
            pen=pg.mkPen('b', width=2),
            name="Serie"
        )

        # --- PUNTOS INTELIGENTES ---
        self.scatter = pg.ScatterPlotItem(size=8, symbol='o', pen=pg.mkPen(None))
        
        points_data = []
        base_brush = pg.mkBrush(0, 0, 255, 150)
        
        # Preparamos los puntos guardando su índice original en 'data' para precisión
        for i, (ts, val) in enumerate(zip(self.timestamps, self.values)):
            points_data.append({
                'pos': (ts, val),
                'data': i,  # Guardamos el índice real aquí
                'brush': base_brush
            })
        self.scatter.addPoints(points_data)
        self.plot_widget.addItem(self.scatter)

        # --- ATAJOS DE TECLADO (Invisible) ---
        # Ctrl+Z para deshacer (Requiere: from PyQt6.QtGui import QShortcut, QKeySequence)
        self.undo_shortcut = QShortcut(QKeySequence("Ctrl+Z"), self)
        self.undo_shortcut.activated.connect(self.undo_last_action)

        # --- CONTROLES INFERIORES ---
        control_layout = QHBoxLayout()
        layout.addLayout(control_layout)

        self.info_label = QLabel("Seleccionados: 0 puntos")
        control_layout.addWidget(self.info_label)

        # Instrucciones actualizadas
        self.instructions_label = QLabel(
            "Instrucciones: Click para marcar. Ctrl+Arrastrar para área. (Ctrl+Z para deshacer)."
        )
        self.instructions_label.setStyleSheet("color: gray; font-style: italic;")
        control_layout.addWidget(self.instructions_label)
        
        btn_confirm = QPushButton("Confirmar")
        btn_confirm.clicked.connect(self.confirm_selection)
        control_layout.addWidget(btn_confirm)

        # Herramienta de selección (Rectángulo)
        self.rubberBand = QRubberBand(QRubberBand.Shape.Rectangle, self.plot_widget)
        self.origin = QPoint()
        self.selecting = False

        # Eventos
        self.plot_widget.viewport().installEventFilter(self)
        self.scatter.sigClicked.connect(self.on_point_clicked)
        self.plot_widget.scene().sigMouseMoved.connect(self.on_mouse_moved)

    # --- LÓGICA DE DESHACER ---

    def save_state(self):
        """Guarda una copia de los índices marcados antes de modificar."""
        self.history_stack.append(set(self.marked_indices))
        if len(self.history_stack) > 20: # Límite de memoria
            self.history_stack.pop(0)

    def undo_last_action(self):
        """Restaura el estado anterior."""
        if not self.history_stack:
            return
        
        prev_state = self.history_stack.pop()
        self.marked_indices = prev_state
        self.update_plot_colors()

    # --- MÉTODOS PRINCIPALES ---

    def update_plot_colors(self):
        """Actualiza los colores basado en los índices marcados."""
        brushes = np.full(len(self.timestamps), pg.mkBrush(0, 0, 255, 150), dtype=object)
        if self.marked_indices:
            indices = list(self.marked_indices)
            brushes[indices] = pg.mkBrush(255, 0, 0) # Rojo para seleccionados
        
        self.scatter.setBrush(brushes.tolist())
        self.info_label.setText(f"Seleccionados: {len(self.marked_indices)} puntos")

    def on_point_clicked(self, plot, points):
        """Selección precisa usando el índice guardado en el punto."""
        self.save_state() # Guardar para deshacer
        changed = False
        
        for pt in points:
            idx = pt.data() # Recuperamos el índice original
            if idx is None: continue

            if idx in self.marked_indices:
                self.marked_indices.remove(idx)
            else:
                self.marked_indices.add(idx)
            changed = True
            
        if changed:
            self.update_plot_colors()

    def eventFilter(self, obj, event):
        if obj is self.plot_widget.viewport():
            if event.type() == QEvent.Type.MouseButtonPress:
                if event.modifiers() & Qt.KeyboardModifier.ControlModifier and event.button() == Qt.MouseButton.LeftButton:
                    self.origin = event.position().toPoint()
                    self.rubberBand.setGeometry(QRect(self.origin, QSize()))
                    self.rubberBand.show()
                    self.selecting = True
                    return True
            elif event.type() == QEvent.Type.MouseMove:
                if self.selecting:
                    rect = QRect(self.origin, event.position().toPoint()).normalized()
                    self.rubberBand.setGeometry(rect)
                    return True
            elif event.type() == QEvent.Type.MouseButtonRelease:
                if self.selecting:
                    self.rubberBand.hide()
                    rect = QRect(self.origin, event.position().toPoint()).normalized()
                    self.select_points_in_rect(rect)
                    self.selecting = False
                    return True
        return super().eventFilter(obj, event)

    def select_points_in_rect(self, rect):
        """Selección rectangular corregida usando mapToScene (Precisión visual)."""
        if rect.width() < 2 and rect.height() < 2: return

        self.save_state() # Guardar para deshacer
        vb = self.plot_widget.getViewBox()

        # 1. Convertir Píxeles -> Escena
        scene_tl = self.plot_widget.mapToScene(rect.topLeft())
        scene_br = self.plot_widget.mapToScene(rect.bottomRight())

        # 2. Convertir Escena -> Valores de los Ejes
        p1 = vb.mapSceneToView(scene_tl)
        p2 = vb.mapSceneToView(scene_br)

        # 3. Ordenar coordenadas y buscar
        xmin, xmax = sorted([p1.x(), p2.x()])
        ymin, ymax = sorted([p1.y(), p2.y()])

        mask = (self.timestamps >= xmin) & (self.timestamps <= xmax) & \
               (self.values >= ymin) & (self.values <= ymax)
        
        indices_inside = np.where(mask)[0]

        if len(indices_inside) > 0:
            self.marked_indices.update(indices_inside)
            self.update_plot_colors()

    def on_mouse_moved(self, pos):
        """Tooltip optimizado."""
        vb = self.plot_widget.getViewBox()
        mouse_point = vb.mapSceneToView(pos)
        
        if len(self.timestamps) == 0: return

        # Búsqueda binaria
        idx = np.searchsorted(self.timestamps, mouse_point.x())
        if idx >= len(self.timestamps): idx = len(self.timestamps) - 1
        
        if idx > 0:
            prev = idx - 1
            if abs(self.timestamps[idx] - mouse_point.x()) > abs(self.timestamps[prev] - mouse_point.x()):
                idx = prev

        # Validar distancia visual
        point_scene = vb.mapViewToScene(QPointF(self.timestamps[idx], self.values[idx]))
        dist_x = abs(point_scene.x() - pos.x())
        dist_y = abs(point_scene.y() - pos.y())

        if dist_x < 20 and dist_y < 20:
            dt = datetime.fromtimestamp(self.timestamps[idx])
            tooltip = f"Fecha: {dt.strftime('%Y-%m-%d %H:%M:%S')}\nValor: {self.values[idx]:.3f}"
            
            view = vb.scene().views()[0]
            global_pos = view.viewport().mapToGlobal(view.mapFromScene(pos))
            QToolTip.showText(global_pos, tooltip)
        else:
            QToolTip.hideText()

    def confirm_selection(self):
        selected_ids = [self.ids[i] for i in self.marked_indices]
        if not selected_ids:
            QMessageBox.information(self, "Información", "No ha seleccionado ningún punto para limpiar.")
            return

        try:
            # Usamos la variable estática del padre como tenías originalmente
            respuesta = AnalisisController.ctrlOmitirLecturasRuido(AnalisisView.idproyecto, selected_ids)

            if respuesta:
                QMessageBox.information(self, "Éxito", "Lecturas omitidas correctamente.")
                self.accept()
            else:
                QMessageBox.warning(self, "Error", "No se pudo omitir las lecturas. Intente de nuevo.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error: {str(e)}")