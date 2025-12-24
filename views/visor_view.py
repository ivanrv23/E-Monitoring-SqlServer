import vtk
import numpy as np
import laspy
import threading
import ast
import sys
import random
import matplotlib.dates as mdates
from PySide6.QtGui import QColor, QDoubleValidator
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from datetime import datetime
import datetime as dt_module 
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QComboBox, QTreeWidget, QPushButton, QSlider, QStackedWidget,
                               QDialog, QGridLayout, QLineEdit, QLabel, QColorDialog, QHBoxLayout, QApplication)
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.util.numpy_support import numpy_to_vtk
from utils.common.alertas import mostrar_mensaje
from utils.common.rutasarchivos import resource_path
from vtkmodules.vtkRenderingFreeType import vtkVectorText
from vtkmodules.vtkRenderingCore import vtkFollower, vtkPolyDataMapper
from scipy.spatial import ConvexHull, Delaunay
from modules.datos.equiposVisor import EquiposVisor
from utils.shared.loading import LoadingView
from modules.visualization.procesardxf import ProcesarDXF
from utils.common.metodosGenerales import MetodosGenerales
from modules.visualization.configurarDTM import ConfigurarDTM
from modules.visualization.exportardxfvectores import ExportarDXF
from modules.visualization.configuracionvisor import ConfiguracionVisor
from utils.shared.graficareporte import GraficaReporte
from utils.shared.asistentedevoz import AsistenteVoz
from modules.umbrales.umbralesEquipos import UmbralView
from controllers.TopografiaController import TopografiaController
from controllers.PrismaController import PrismaController
from controllers.InclinometroController import InclinometroController
from controllers.PiezometroController import PiezometroController
from controllers.PluviometroController import PluviometroController
from controllers.CeldaController import CeldaController
from controllers.AcelerografoController import AcelerografoController
from controllers.TDRController import TDRController
from controllers.EquipoController import EquipoController
from controllers.UmbralController import UmbralController
from utils.shared.guardarImagenReporte import ReporteImage
from modules.visualization.procesarLidar import ProcesarLidar
from controllers.PrismasVirtualesController import PrismasVirtualesController
from utils.shared.arbolmarcado import TreeCheckbox
from modules.empresa.softwareconfiguracion import SoftwareConfiguracion
# desactivando alertas de vtk
vtk.vtkObject.GlobalWarningDisplayOff()

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)

    def clear(self):
        self.axes.cla()
       
class VisorView:
    main, idproyecto, nameproyecto, estadochecklist = None, None, "SIN PROYECTO", True
    equiposgenerales, colorvectores, limites_corte = [], [], []
    visorVisible, estadoPagina, estadografico, cambioproyecto = False, True, False, False
    vtkWidgetVisor, rendererVisor, actorVisor = None, None, None
    listatopograficados, vectoresDXF, piezometrostuboscuerda, piezometrostubosmanual, cablescoaxiales = [], [], [], [], []
    vtkWidgetCorte, rendererCorte, lista_actoresDXF_corte, solidoDXF_corte = None, None, [], None
    prismasGrafico, inclinometrolineas, inclinometroPuntos, toposDTM, listaDTMactivos = [], [], [], [], []
    dibujarLineaIncli, dibujarPuntoIncli, estadorenderizado, estadorenderizado_corte = 0, 0, 0, 0
    estadovector, tipovector, escalavector = False, 'D3D', 0
    polyDataCorte, boxWidget, estado_box, boxVisible = None, None, True, False
    dibujarTuboPiezo, estadoInicialCubo, resetvisor = 0, None, False
    listaactorespluvio, clipFunction, planes = [], None, None
    orientation_widget3d, orientation_widgetcorte = None, None
    escalainclinometro, listaactoresceldas, listaactoresacelero = 0, [], []
    vtkWidgetLidar, rendererLidar, orientation_widgetLidar = None, None, None
    fechainicial, fechafinal = MetodosGenerales.obtenerRangoFechas(365)
    estilo_personalizado, polydatos_LAS = None, []
    prismasvirtualesgraficados = []
    respuesta = ConfiguracionVisor.obtenerDataConfiguracionVisor()
    colorfondo = respuesta[0]
    
    def inicializarVistaVisor(main, proyectoid, proyectoname, fechaini, fechafin):
        VisorView.main = main
        VisorView.idproyecto = proyectoid
        VisorView.nameproyecto = proyectoname
        VisorView.fechainicial, VisorView.fechafinal = fechaini, fechafin
        
        try:
            if VisorView.estadoPagina:
                tree_actual_visor = VisorView.main.findChild(QTreeWidget, "tree_actual_visor")
                tree_actual_visor.itemClicked.connect(VisorView.checkProyectoActualVisor)
                tree_actual_visor.setContextMenuPolicy(Qt.CustomContextMenu)
                tree_actual_visor.customContextMenuRequested.connect(VisorView.clicderechoProyectoActualVisor)

                # INICIALIZAR VISOR 3D VTK
                widgetVisor3d = VisorView.main.findChild(QWidget, "widget_visor3d")
                VisorView.vtkWidgetVisor = QVTKRenderWindowInteractor(widgetVisor3d)
                VisorView.vtkWidgetVisor.Initialize()
                
                VisorView.rendererVisor = vtk.vtkRenderer()
                VisorView.vtkWidgetVisor.GetRenderWindow().AddRenderer(VisorView.rendererVisor)
                
                layout = QVBoxLayout(widgetVisor3d)
                layout.setContentsMargins(0, 0, 0, 0)
                layout.addWidget(VisorView.vtkWidgetVisor)
                
                VisorView.actorVisor = vtk.vtkActor()
                VisorView.rendererVisor.AddActor(VisorView.actorVisor)
                VisorView.rendererVisor.ResetCamera()
                VisorView.rendererVisor.SetBackground(1, 1, 1)
                
                # Ejes únicos para Visor 3D
                axes_visor = vtk.vtkAxesActor()
                axes_visor.SetTotalLength(2, 2, 2)
                axes_visor.SetShaftType(1)
                axes_visor.SetAxisLabels(1)
                
                VisorView.orientation_widget3d = vtk.vtkOrientationMarkerWidget()
                VisorView.orientation_widget3d.SetOrientationMarker(axes_visor)
                VisorView.orientation_widget3d.SetInteractor(VisorView.vtkWidgetVisor)
                VisorView.orientation_widget3d.SetEnabled(1)
                VisorView.orientation_widget3d.InteractiveOff()
                
                VisorView.vtkWidgetVisor.AddObserver(vtk.vtkCommand.MouseMoveEvent, VisorView.mostrar_coordenadas3d)

                # INICIALIZAR VISOR CORTE
                widgetVisor3d_corte = VisorView.main.findChild(QWidget, "widget_visor_corte")
                VisorView.vtkWidgetCorte = QVTKRenderWindowInteractor(widgetVisor3d_corte)
                VisorView.vtkWidgetCorte.Initialize()
                
                VisorView.rendererCorte = vtk.vtkRenderer()
                VisorView.vtkWidgetCorte.GetRenderWindow().AddRenderer(VisorView.rendererCorte)
                
                layout_corte = QVBoxLayout(widgetVisor3d_corte)
                layout_corte.setContentsMargins(0, 0, 0, 0)
                layout_corte.addWidget(VisorView.vtkWidgetCorte)
                
                VisorView.rendererCorte.SetBackground(1, 1, 1)
                
                # Ejes únicos para Corte
                axes_corte = vtk.vtkAxesActor()
                axes_corte.SetTotalLength(2, 2, 2)
                axes_corte.SetShaftType(1)
                axes_corte.SetAxisLabels(1)
                
                VisorView.orientation_widgetcorte = vtk.vtkOrientationMarkerWidget()
                VisorView.orientation_widgetcorte.SetOrientationMarker(axes_corte)
                VisorView.orientation_widgetcorte.SetInteractor(VisorView.vtkWidgetCorte)
                VisorView.orientation_widgetcorte.SetEnabled(1)
                VisorView.orientation_widgetcorte.InteractiveOff()
                
                VisorView.vtkWidgetCorte.AddObserver(vtk.vtkCommand.MouseMoveEvent, VisorView.mostrar_coordenadas3d_corte)

                # INICIALIZAR VISOR COMPARAR LIDAR
                widgetVisor3d_lidar = VisorView.main.findChild(QWidget, "widget_visor_comparar_nubes")
                VisorView.vtkWidgetLidar = QVTKRenderWindowInteractor(widgetVisor3d_lidar)
                VisorView.vtkWidgetLidar.Initialize()
                
                VisorView.rendererLidar = vtk.vtkRenderer()
                VisorView.vtkWidgetLidar.GetRenderWindow().AddRenderer(VisorView.rendererLidar)
                
                layout_lidar = QVBoxLayout(widgetVisor3d_lidar)
                layout_lidar.setContentsMargins(0, 0, 0, 0)
                layout_lidar.addWidget(VisorView.vtkWidgetLidar)
                
                VisorView.rendererLidar.SetBackground(1.0, 1.0, 1.0)
                
                # Ejes únicos para LIDAR
                axes_lidar = vtk.vtkAxesActor()
                axes_lidar.SetTotalLength(2, 2, 2)
                axes_lidar.SetShaftType(1)
                axes_lidar.SetAxisLabels(1)
                
                VisorView.orientation_widgetLidar = vtk.vtkOrientationMarkerWidget()
                VisorView.orientation_widgetLidar.SetOrientationMarker(axes_lidar)
                VisorView.orientation_widgetLidar.SetInteractor(VisorView.vtkWidgetLidar)
                VisorView.orientation_widgetLidar.SetEnabled(1)
                VisorView.orientation_widgetLidar.InteractiveOff()
                
                VisorView.vtkWidgetLidar.AddObserver(vtk.vtkCommand.MouseMoveEvent, VisorView.mostrar_coordenadas3d_lidar)

                # CONFIGURACIÓN DE BOTONES Y CONTROLES
                paginacionvisor = VisorView.main.findChild(QStackedWidget, "stacked_visor")
                
                botonRefrescarVisor = VisorView.main.findChild(QPushButton, "btn_refrescar_vista_visor")
                if botonRefrescarVisor:
                    botonRefrescarVisor.clicked.connect(lambda: VisorView.obtenerMostrarEquiposMarcados(tree_actual_visor, paginacionvisor))
                
                lbltipovista = VisorView.main.findChild(QLabel, "label_modo_visor")
                if lbltipovista:
                    lbltipovista.setText("VISTA VISOR 3D")
                
                botonvista3d = VisorView.main.findChild(QPushButton, "btn_vista3d")
                if botonvista3d:
                    botonvista3d.clicked.connect(lambda: VisorView.cambiarVistaVisor("3D", lbltipovista, paginacionvisor))
                
                botonvistaCorte = VisorView.main.findChild(QPushButton, "btn_vista_corte")
                if botonvistaCorte:
                    botonvistaCorte.clicked.connect(lambda: VisorView.cambiarVistaVisor("CORTE", lbltipovista, paginacionvisor))
                
                botonvistaLidar = VisorView.main.findChild(QPushButton, "btn_vista_lidar")
                if botonvistaLidar:
                    botonvistaLidar.clicked.connect(lambda: VisorView.cambiarVistaVisor("LIDAR", lbltipovista, paginacionvisor))
                
                btnRealizarcorte = VisorView.main.findChild(QPushButton, "btn_realizar_corte")
                if btnRealizarcorte:
                    btnRealizarcorte.clicked.connect(lambda: VisorView.realizarCorteVisor(lbltipovista, paginacionvisor, tree_actual_visor))
                
                botonEscalaVectores = VisorView.main.findChild(QPushButton, "btn_escalar_vectores")
                if botonEscalaVectores:
                    botonEscalaVectores.clicked.connect(lambda: VisorView.mostrarVectores(tree_actual_visor))
                
                botonEscalaInclino = VisorView.main.findChild(QPushButton, "btn_escalar_inclinometros")
                if botonEscalaInclino:
                    botonEscalaInclino.clicked.connect(lambda: VisorView.mostrarEscalaInclinometros(tree_actual_visor, paginacionvisor))
                
                botonRenderizar = VisorView.main.findChild(QPushButton, "btn_aplicar_dtm")
                if botonRenderizar:
                    botonRenderizar.clicked.connect(lambda: VisorView.aplicarDTMtopografia(tree_actual_visor, paginacionvisor))
                
                btnExportarVectoresDXF = VisorView.main.findChild(QPushButton, "btn_exportar_vectores")
                if btnExportarVectoresDXF:
                    btnExportarVectoresDXF.clicked.connect(lambda: VisorView.exportarVetoresdxf(tree_actual_visor))
                
                comboVistasVisor = VisorView.main.findChild(QComboBox, "combo_vistas_visor")
                if comboVistasVisor:
                    comboVistasVisor.activated.connect(lambda: VisorView.cambiarPerspectivaVistaVisor(comboVistasVisor, paginacionvisor))
                
                botonReporteVisor = VisorView.main.findChild(QPushButton, "btn_reporte_visor")
                if botonReporteVisor:
                    botonReporteVisor.clicked.connect(lambda: VisorView.agregarImagenReporteVisor(tree_actual_visor, paginacionvisor, "Anexos"))
                
                btnReporteGeneral = VisorView.main.findChild(QPushButton, "btn_imagen_visor")
                if btnReporteGeneral:
                    btnReporteGeneral.clicked.connect(lambda: VisorView.agregarImagenReporteVisor(tree_actual_visor, paginacionvisor, "General"))
                
                botonmostrarcubocorte = VisorView.main.findChild(QPushButton, "btn_cubo_corte")
                if botonmostrarcubocorte:
                    botonmostrarcubocorte.clicked.connect(lambda: VisorView.visibilidadCuboSeleccion(tree_actual_visor, paginacionvisor))
                
                btnAsistentevisor = VisorView.main.findChild(QPushButton, "btn_voz_visor")
                if btnAsistentevisor:
                    btnAsistentevisor.clicked.connect(lambda: VisorView.analisisAsistenteVozVisor(tree_actual_visor, btnAsistentevisor))
                
                sliderTransparencia = VisorView.main.findChild(QSlider, "slider_transparencia_visor")
                if sliderTransparencia:
                    sliderTransparencia.valueChanged.connect(lambda: VisorView.sliderCambioTransparencia(sliderTransparencia, paginacionvisor))
                
                botonconfigurarVisor = VisorView.main.findChild(QPushButton, "btn_configurar_visor")
                if botonconfigurarVisor:
                    botonconfigurarVisor.clicked.connect(lambda: VisorView.configurarInstrumentosVisor(paginacionvisor))
                
                botonCompararLidar = VisorView.main.findChild(QPushButton, "btn_comparar_archivos_las")
                if botonCompararLidar:
                    botonCompararLidar.clicked.connect(lambda: VisorView.procesarLidar(paginacionvisor))
                
                botongraficasLidar = VisorView.main.findChild(QPushButton, "btn_graficar_desplazamientos_lidar")
                if botongraficasLidar:
                    botongraficasLidar.clicked.connect(VisorView.ProcesarDesplazamientoLidar)

                # Actualizar estado y forzar renderizado inicial
                VisorView.estadoPagina = False
                VisorView.vtkWidgetVisor.GetRenderWindow().Render()
                VisorView.vtkWidgetCorte.GetRenderWindow().Render()
                VisorView.vtkWidgetLidar.GetRenderWindow().Render()

            if VisorView.estadochecklist:
                VisorView.actualizarColorFondo()
                tree_widget = VisorView.main.findChild(QTreeWidget, "tree_actual_visor")
                if tree_widget:
                    tree_widget.setHeaderLabels([VisorView.nameproyecto.upper()])
                    EquiposVisor.inicializar_lista_equipos(tree_widget, VisorView.idproyecto, VisorView.nameproyecto)
                VisorView.estadochecklist = False
        except Exception as e:
            mostrar_mensaje("Error Fatal", f"Error durante la inicialización del visor:\n{str(e)}", "error")
            VisorView.estadoPagina = False
            VisorView.estadochecklist = False

    def actualizarColorFondo():
        if VisorView.idproyecto:
            ConfiguracionVisor.actualizarInfoConfiguracionVisor(VisorView.idproyecto)
        respuesta = ConfiguracionVisor.obtenerDataConfiguracionVisor()
        colorfondo = MetodosGenerales.convertirHexadecimalRGB(respuesta[0])
        if VisorView.rendererVisor:
            VisorView.rendererVisor.SetBackground(colorfondo)
        if VisorView.rendererCorte:
            VisorView.rendererCorte.SetBackground(colorfondo)
        if VisorView.rendererLidar:
            VisorView.rendererLidar.SetBackground(colorfondo)
        if VisorView.vtkWidgetVisor:
            VisorView.vtkWidgetVisor.GetRenderWindow().Render()
    
    def ProcesarDesplazamientoLidar():
        topografiasmarcadas = None
        tree_actual = VisorView.main.findChild(QTreeWidget, "tree_actual_visor")
        lista = EquiposVisor.obtener_todos_elementos_marcados(tree_actual)
        if lista:
            topografiasmarcadas = VisorView.obtenerListaEquiposMarcados(lista, "Topografías")
            prismasvirtualesmarcados = VisorView.obtenerListaEquiposMarcados(lista, "Prismas Virtuales")
        if topografiasmarcadas:
            if prismasvirtualesmarcados:            
                ProcesarLidar.modalGraficasDesplazamiento(topografiasmarcadas, VisorView.polydatos_LAS, prismasvirtualesmarcados)
    
    def procesarLidar(paginacionvisor):
        def cambiarpagina():
            lbltipovisor = VisorView.main.findChild(QLabel, "label_modo_visor")
            paginacionvisor.setCurrentIndex(2)
            lbltipovisor.setText("MAPA DE CALOR")
        if VisorView.idproyecto:            
            ProcesarLidar.listarLidar(VisorView.idproyecto, VisorView.rendererLidar, VisorView.vtkWidgetLidar, cambiarpagina)
        
    def checkProyectoActualVisor(parent_item, column):
        treeWidget =  VisorView.main.findChild(QTreeWidget, "tree_actual_visor")
        paginacion = VisorView.main.findChild(QStackedWidget, "stacked_visor")
        EquiposVisor.validarMarcadoCheckbox(parent_item, column, lambda: VisorView.obtenerMostrarEquiposMarcados(treeWidget, paginacion))
    
    def clicderechoProyectoActualVisor(point):
        treeWidget =  VisorView.main.findChild(QTreeWidget, "tree_actual_visor")
        EquiposVisor.validarOpcionesMenuCheckbox(point, VisorView.main, treeWidget, VisorView.actualizarGraficaFechasInclinometros, VisorView.actualizarGraficaFechasPiezometros, VisorView.validarTopografiasMostrarVisor, VisorView.reiniciarVistasAfectadas)
    
    def reiniciarVistasAfectadas(tipoequipo="Todos"):
        from views.datos_view import DatosView
        from views.desplazamiento_view import DesplazamientoView
        from views.velocidad_view import VelocidadView
        from views.inclinometros_view import InclinometrosView
        from views.piezometros_view import PiezometrosView
        from views.celdas_view import CeldasView
        from views.acelerografos_view import AcelerografosView
        from views.sondajestdr_view import SondajetdrView
        from views.analisis_view import AnalisisView
        if tipoequipo == "Prisma":
            DatosView.reiniciarVistaDatos(VisorView.main, VisorView.idproyecto, VisorView.nameproyecto)
            DesplazamientoView.reiniciarVistaDesplazamiento(VisorView.main, VisorView.idproyecto, VisorView.nameproyecto)
            VelocidadView.reiniciarVistaVelocidad(VisorView.main, VisorView.idproyecto, VisorView.nameproyecto)
            AnalisisView.reiniciarVistaAnalisis(VisorView.main, VisorView.idproyecto, VisorView.nameproyecto)
        elif tipoequipo == "Inclinómetro":
            DatosView.reiniciarVistaDatos(VisorView.main, VisorView.idproyecto, VisorView.nameproyecto)
            InclinometrosView.reiniciarVistaInclinometros(VisorView.main, VisorView.idproyecto, VisorView.nameproyecto)
        elif tipoequipo == "Piezómetro":
            DatosView.reiniciarVistaDatos(VisorView.main, VisorView.idproyecto, VisorView.nameproyecto)
            PiezometrosView.reiniciarVistaPiezometros(VisorView.main, VisorView.idproyecto, VisorView.nameproyecto)
        elif tipoequipo == "Pluviómetro":
            DatosView.reiniciarVistaDatos(VisorView.main, VisorView.idproyecto, VisorView.nameproyecto)
            VelocidadView.reiniciarVistaVelocidad(VisorView.main, VisorView.idproyecto, VisorView.nameproyecto)
            PiezometrosView.reiniciarVistaPiezometros(VisorView.main, VisorView.idproyecto, VisorView.nameproyecto)
        elif tipoequipo == "Cotaterreno":
            DatosView.reiniciarVistaDatos(VisorView.main, VisorView.idproyecto, VisorView.nameproyecto)
            PiezometrosView.reiniciarVistaPiezometros(VisorView.main, VisorView.idproyecto, VisorView.nameproyecto)
        elif tipoequipo == "Celda":
            DatosView.reiniciarVistaDatos(VisorView.main, VisorView.idproyecto, VisorView.nameproyecto)
            CeldasView.reiniciarVistaCeldas(VisorView.main, VisorView.idproyecto, VisorView.nameproyecto)
        elif tipoequipo == "Acelerógrafo":
            DatosView.reiniciarVistaDatos(VisorView.main, VisorView.idproyecto, VisorView.nameproyecto)
            AcelerografosView.reiniciarVistaAcelerografos(VisorView.main, VisorView.idproyecto, VisorView.nameproyecto)
        elif tipoequipo == "TDR":
            DatosView.reiniciarVistaDatos(VisorView.main, VisorView.idproyecto, VisorView.nameproyecto)
            SondajetdrView.reiniciarVistaTDR(VisorView.main, VisorView.idproyecto, VisorView.nameproyecto)
        elif tipoequipo == "Adicional":
            DatosView.reiniciarVistaDatos(VisorView.main, VisorView.idproyecto, VisorView.nameproyecto)
        else:
            DatosView.reiniciarVistaDatos(VisorView.main, VisorView.idproyecto, VisorView.nameproyecto)
            DesplazamientoView.reiniciarVistaDesplazamiento(VisorView.main, VisorView.idproyecto, VisorView.nameproyecto)
            VelocidadView.reiniciarVistaVelocidad(VisorView.main, VisorView.idproyecto, VisorView.nameproyecto)
            InclinometrosView.reiniciarVistaInclinometros(VisorView.main, VisorView.idproyecto, VisorView.nameproyecto)
            PiezometrosView.reiniciarVistaPiezometros(VisorView.main, VisorView.idproyecto, VisorView.nameproyecto)
            CeldasView.reiniciarVistaCeldas(VisorView.main, VisorView.idproyecto, VisorView.nameproyecto)
            AcelerografosView.reiniciarVistaAcelerografos(VisorView.main, VisorView.idproyecto, VisorView.nameproyecto)
            SondajetdrView.reiniciarVistaTDR(VisorView.main, VisorView.idproyecto, VisorView.nameproyecto)
            AnalisisView.reiniciarVistaAnalisis(VisorView.main, VisorView.idproyecto, VisorView.nameproyecto)
    
    def mostrar_coordenadas3d(obj, event):
        x, y = VisorView.vtkWidgetVisor.GetEventPosition()
        # Convertir las coordenadas del evento a coordenadas de datos
        VisorView.rendererVisor.SetDisplayPoint(x, y, 0)
        VisorView.rendererVisor.DisplayToWorld()
        worldCoords = VisorView.rendererVisor.GetWorldPoint()
        # Actualizar el texto con las coordenadas X, Y y Z
        lblcoordvisor =  VisorView.main.findChild(QLabel, "label_coordenadas_visor")
        lblcoordvisor.setText("X: {:.3f} Y:  {:.3f} Z: {:.3f}".format(worldCoords[0], worldCoords[1], worldCoords[2]))
    
    def mostrar_coordenadas3d_corte(obj, event):
        x, y = VisorView.vtkWidgetCorte.GetEventPosition()
        # Convertir las coordenadas del evento a coordenadas de datos
        VisorView.rendererCorte.SetDisplayPoint(x, y, 0)
        VisorView.rendererCorte.DisplayToWorld()
        worldCoords = VisorView.rendererCorte.GetWorldPoint()
        # Actualizar el texto con las coordenadas X, Y y Z
        lblcoordvisor =  VisorView.main.findChild(QLabel, "label_coordenadas_visor")
        lblcoordvisor.setText("X: {:.3f} Y:  {:.3f} Z: {:.3f}".format(worldCoords[0], worldCoords[1], worldCoords[2]))
        
    def mostrar_coordenadas3d_lidar(obj, event):
        x, y = VisorView.vtkWidgetLidar.GetEventPosition()
        # Convertir las coordenadas del evento a coordenadas de datos
        VisorView.rendererLidar.SetDisplayPoint(x, y, 0)
        VisorView.rendererLidar.DisplayToWorld()
        worldCoords = VisorView.rendererLidar.GetWorldPoint()
        # Actualizar el texto con las coordenadas X, Y y Z
        lblcoordvisor =  VisorView.main.findChild(QLabel, "label_coordenadas_visor")
        lblcoordvisor.setText("X: {:.3f} Y:  {:.3f} Z: {:.3f}".format(worldCoords[0], worldCoords[1], worldCoords[2]))
                
    def obtenerMostrarEquiposMarcados(tree_actual, paginacion):
        VisorView.resetvisor = False
        lista = EquiposVisor.obtener_todos_elementos_marcados(tree_actual)
        if lista:
            topografiasmarcadas = VisorView.obtenerListaEquiposMarcados(lista, "Topografías")
            if len(topografiasmarcadas) > 0:
                VisorView.resetvisor = True
                VisorView.mostrarTopografiasVisor(topografiasmarcadas)
            else:
                VisorView.limpiarTopografiasVisor()
            prismasmarcados = VisorView.obtenerListaEquiposMarcados(lista, "Prismas")
            if len(prismasmarcados) > 0:
                VisorView.mostrarPrismasVisor(prismasmarcados)
            else:
                VisorView.limpiarPrismasVisor()
            inclinometrosmarcados = VisorView.obtenerListaEquiposMarcados(lista, "Inclinómetros")
            if len(inclinometrosmarcados) > 0:
                VisorView.mostrarInclinometrosVisor(paginacion, VisorView.escalainclinometro, inclinometrosmarcados)
            else:
                VisorView.limpiarInclinometrosVisor()
            piezocuerdasmarcados = VisorView.obtenerListaEquiposMarcados(lista, "Piezómetros Cuerda Vibrante")
            if len(piezocuerdasmarcados) > 0:
                VisorView.mostrarPiezometrosCuerdaVisor(paginacion, piezocuerdasmarcados)
            else:
                VisorView.limpiarPiezometrosCuerdaVisor()
            piezomanualesmarcados = VisorView.obtenerListaEquiposMarcados(lista, "Piezómetros Casagrande")
            if len(piezomanualesmarcados) > 0:
                VisorView.mostrarPiezometrosManualVisor(paginacion, piezomanualesmarcados)
            else:
                VisorView.limpiarPiezometrosManualVisor()
            pluviometrosmarcados = VisorView.obtenerListaEquiposMarcados(lista, "Pluviómetros")
            if len(pluviometrosmarcados) > 0:
                VisorView.mostrarPluviometrosVisor(paginacion, pluviometrosmarcados)
            else:
                VisorView.limpiarPluviometrosVisor()
            celdasmarcadas = VisorView.obtenerListaEquiposMarcados(lista, "Celdas de Asentamiento")
            if len(celdasmarcadas) > 0:
                VisorView.mostrarCeldasAsentamientoVisor(paginacion, celdasmarcadas)
            else:
                VisorView.limpiarCeldasAsentamientoVisor()
            acelerografosmarcados = VisorView.obtenerListaEquiposMarcados(lista, "Acelerógrafos")
            if len(acelerografosmarcados) > 0:
                VisorView.mostrarAcelerografosVisor(paginacion, acelerografosmarcados)
            else:
                VisorView.limpiarAcelerografosVisor()
            sondajestdrmarcados = VisorView.obtenerListaEquiposMarcados(lista, "TDR")
            if len(sondajestdrmarcados) > 0:
                VisorView.mostrarSondajestdrVisor(paginacion, sondajestdrmarcados)
            else:
                VisorView.limpiarSondajestdrVisor()
            adicionalesmarcados = VisorView.obtenerListaEquiposMarcados(lista, "Equipos Adicionales")
            if len(adicionalesmarcados) > 0:
                VisorView.mostrarEquiposAdicionalesVisor(paginacion, adicionalesmarcados)
            else:
                VisorView.limpiarEquiposAdicionalesVisor()
            prismasvirtuales = VisorView.obtenerListaEquiposMarcados(lista, "Prismas Virtuales")
            if len(prismasvirtuales) > 0:
                VisorView.mostrarPrismasVirtualesVisor(paginacion, prismasvirtuales)
            else:
                VisorView.limpiarPrismasVirtualesVisor()
        else:
            VisorView.limpiarTodosElementosVisor()
    
    def limpiarTodosElementosVisor():
        VisorView.limpiarTopografiasVisor()
        VisorView.limpiarPrismasVisor()
        VisorView.limpiarInclinometrosVisor()
        VisorView.limpiarPiezometrosCuerdaVisor()
        VisorView.limpiarPiezometrosManualVisor()
        VisorView.limpiarPluviometrosVisor()
        VisorView.limpiarCeldasAsentamientoVisor()
        VisorView.limpiarAcelerografosVisor()
        VisorView.limpiarSondajestdrVisor()
        VisorView.limpiarEquiposAdicionalesVisor()
        VisorView.limpiarPrismasVirtualesVisor()
        
    def obtenerListaEquiposMarcados(lista, tipolista):
        equiposmarcados = []
        for region, instrumentos in lista.items():
            for tipo, lista_equipos in instrumentos.items():
                if tipo[0] == tipolista:
                    equiposmarcados.append((region, lista_equipos))
        return equiposmarcados
    
    def cambiarVistaVisor(tipo, lbltipovisor, paginacionvisor):
        if tipo == "3D":
            paginacionvisor.setCurrentIndex(0)
            lbltipovisor.setText("VISTA VISOR 3D")
        elif tipo == "CORTE":
            paginacionvisor.setCurrentIndex(1)
            lbltipovisor.setText("VISTA VISOR CORTE 3D")
        else:
            paginacionvisor.setCurrentIndex(2)
            lbltipovisor.setText("MAPA DE CALOR")
        
    def realizarCorteVisor(lbltipovisor, paginacion, tree_actual):
        lista = EquiposVisor.obtener_todos_elementos_marcados(tree_actual)
        if lista:
            toposmarcados = VisorView.obtenerListaEquiposMarcados(lista, "Topografías")
            if len(toposmarcados) > 0:
                respuesta = VisorView.recortarGrafico(paginacion, toposmarcados)
                if respuesta:
                    lbltipovisor.setText("VISTA VISOR CORTE 3D")
            
    def mostrarTopografiasVisor(topomarcados):
        # GRAFICAR LAS TOPOGRAFÍAS
        VisorView.graficarTopografiasProyecto(topomarcados)
        # MOSTRAR VISOR
        camera = VisorView.rendererVisor.GetActiveCamera()
        VisorView.rendererVisor.ResetCamera()
        camera.Zoom(1.5)
        VisorView.vtkWidgetVisor.GetRenderWindow().Render()
    
    def graficarTopografiasProyecto(topomarcados):
        VisorView.reiniciarBox()
        if len(topomarcados) > 0:
            # Iniciar Hilo
            loading = LoadingView.mostrarLoading()
            def on_thread_complete():
                loading.close()
            procesa_dxf = ProcesarTopografiaThread(topomarcados)
            procesa_dxf.task_finishProcesardxf.connect(on_thread_complete)
            procesa_dxf.start()
            loading.exec()
            # mostrar u ocultar topos y dtm
            VisorView.validarTopografiasMostrarVisor(topomarcados)
    
    def validarTopografiasMostrarVisor(topomarcados=None):
        if topomarcados is None:
            treeWidget =  VisorView.main.findChild(QTreeWidget, "tree_actual_visor")
            lista = EquiposVisor.obtener_todos_elementos_marcados(treeWidget)
            topomarcados = []
            if lista:
                topomarcados = VisorView.obtenerListaEquiposMarcados(lista, "Topografías")
        for compocod, codtopo, actor_dtm, color_dtm, rutadtm in VisorView.toposDTM:
            actor_dtm.SetVisibility(False)
        listadtm = {f"{solido[0]}_{solido[1]}_{solido[4]}": solido for solido in VisorView.toposDTM}
        topo_set = set((componente[1], topo[2], rutaact) for componente, listatopos in topomarcados for topo, actores in listatopos.items() for nameact, idinst, rutaact in actores)
        for idcomponente, idtopo, tipo, actor, rutaactor in VisorView.listatopograficados:
            if (idcomponente, idtopo, rutaactor) in topo_set:
                actor.SetVisibility(True)
                if f"{idcomponente}_{idtopo}_{rutaactor}" in listadtm:
                    if f"{idcomponente}_{idtopo}_{rutaactor}" in VisorView.listaDTMactivos:
                        listadtm[f"{idcomponente}_{idtopo}_{rutaactor}"][2].SetVisibility(True)
            else:
                actor.SetVisibility(False)
    
    def agregarActoresDXF(topografiamarcados):
        for componente, listatopos in topografiamarcados:
            nombrecomponente, idcomponente, idproy = componente
            for topo, actores in listatopos.items():
                nombretopo, idinstrumento, idtopo = topo
                tipoarchivo = TopografiaController.ctrlObtenerTipoTopografia(VisorView.idproyecto, idcomponente, idtopo)
                if tipoarchivo:
                    tipo = tipoarchivo[0]
                    for actortopo in actores:
                        nombreactor, idinstruactor, rutaactor = actortopo
                        # Verificar si el idtopo ya está en listatopograficados
                        topo_existente = any(idcomponente == grafico[0] and idtopo == grafico[1] and rutaactor == grafico[4] for grafico in VisorView.listatopograficados)
                        if not topo_existente:
                            if tipo == "DXF":
                                actorescreado, totalPuntos = VisorView.crearActoresTopografia("DXF", rutaactor)
                                if actorescreado:
                                    VisorView.listatopograficados.append((idcomponente, idtopo, "DXF", actorescreado, rutaactor))
                                    for actor in actorescreado:
                                        VisorView.rendererVisor.AddActor(actor)
                            elif tipo == "LAS":
                                actorcreado, datos_adicionales = VisorView.crearActoresTopografia("LAS", rutaactor)
                                if actorcreado:
                                    VisorView.listatopograficados.append((idcomponente, idtopo, "LAS", actorcreado, rutaactor))
                                    obtener_fecha_topo = TopografiaController.ctrlObtenerFechaTopografia(idtopo)
                                    if datos_adicionales[0] > 10000000:
                                        VisorView.vtkWidgetVisor.GetRenderWindow().SetMultiSamples(0)
                                        VisorView.vtkWidgetVisor.GetRenderWindow().SetAlphaBitPlanes(1)
                                    else:
                                        # Resetear las configuraciones a sus valores predeterminados o deseados
                                        VisorView.vtkWidgetVisor.GetRenderWindow().SetMultiSamples(8)  # Ejemplo: restablecer a 8 muestras
                                        VisorView.vtkWidgetVisor.GetRenderWindow().SetAlphaBitPlanes(0)  # Ejemplo: restablecer a 0 planos alpha
                                    VisorView.polydatos_LAS.append((idcomponente, idtopo, obtener_fecha_topo, datos_adicionales[1]))
                                    VisorView.rendererVisor.AddActor(actorcreado)
                            else:
                                actorcreado, totalPuntos = VisorView.crearActoresTopografia("VTP", rutaactor)
                                if actorcreado:
                                    VisorView.listatopograficados.append((idcomponente, idtopo, "VTP", actorcreado, rutaactor))
                                    VisorView.rendererVisor.AddActor(actorcreado)
    
    def crearActoresTopografia(tipo, ubicacion):
        if tipo == "VTP":
            try:
                actoresDXF = ProcesarDXF.graficar_vtp(ubicacion)
                return actoresDXF, None
            except Exception as e:
                return None, None
        else:
            actorLAS, datos_adicionales = VisorView.crearActorLAS(ubicacion)
            return actorLAS, datos_adicionales
    
    def crearActorLAS(las_file_path):
        try:            
            # Abrir el archivo LAS
            las_file = laspy.read(resource_path(las_file_path))
            # Obtener coordenadas XYZ
            coordenadas = np.vstack((las_file.x, las_file.y, las_file.z)).transpose()
            num_puntos = coordenadas.shape[0]
            # Obtener colores RGB si están disponibles
            colores = None
            if hasattr(las_file, 'red') and hasattr(las_file, 'green') and hasattr(las_file, 'blue'):
                colores = np.vstack((las_file.red, las_file.green, las_file.blue)).transpose()
                colores = MetodosGenerales.convertiraRGBestandar(colores)
            # Crear un objeto vtkPoints usando numpy_to_vtk para convertir las coordenadas
            puntos_vtk = vtk.vtkPoints()
            puntos_vtk.SetData(numpy_to_vtk(coordenadas))
            # Crear un objeto vtkPolyData para almacenar los puntos
            poli_datos = vtk.vtkPolyData()
            poli_datos.SetPoints(puntos_vtk)
            # Añadir colores si están disponibles
            if colores is not None:
                vtk_colores = numpy_to_vtk(colores, array_type=vtk.VTK_UNSIGNED_CHAR)
                vtk_colores.SetNumberOfComponents(3)
                vtk_colores.SetName("Colores")
                poli_datos.GetPointData().SetScalars(vtk_colores)
            # Crear el glifo para visualizar los puntos
            glifo_filtro = vtk.vtkVertexGlyphFilter()
            glifo_filtro.SetInputData(poli_datos)
            glifo_filtro.Update()
            # Crear el mapeador y configurar el input
            mapeador = vtk.vtkPolyDataMapper()
            mapeador.SetInputData(glifo_filtro.GetOutput())
            # Crear el actor directamente con el mapeador
            actor = vtk.vtkActor()
            actor.SetMapper(mapeador)
            picker = vtk.vtkPointPicker()  # Usar vtkPointPicker para seleccionar puntos
            picker.SetTolerance(0.001)  # Ajustar la tolerancia para mejorar la precisión
            # Configurar estilo de interacción
            VisorView.estilo_personalizado = vtk.vtkInteractorStyleTrackballCamera()
            VisorView.estilo_personalizado.AddObserver(
                "LeftButtonPressEvent",
                lambda obj, event: VisorView.on_left_click(picker, obj, event)
            )
            VisorView.vtkWidgetVisor.SetInteractorStyle(VisorView.estilo_personalizado)
            datos_adicionales = [num_puntos, poli_datos]
            return actor, datos_adicionales
        except:
            return None, None
    
    @staticmethod
    def on_left_click(picker, obj, event):
        if VisorView.vtkWidgetVisor.GetControlKey():
            click_pos = VisorView.vtkWidgetVisor.GetEventPosition()
            picker.Pick(click_pos[0], click_pos[1], 0, VisorView.rendererVisor)
            picked_point = picker.GetPickPosition()
            if picked_point:
                x, y, z = picked_point
                VisorView.abrir_dialogo(x, y, z)
                # Evitar que el evento continúe propagándose
                VisorView.vtkWidgetVisor.SetControlKey(0)  # Desactiva la tecla Ctrl después del uso
                return  # Salimos de la función aquí
        VisorView.estilo_personalizado.OnLeftButtonDown()
    
    @staticmethod
    def crear_prisma_virtual(x, y, z, nombre_esfera, radio, color):
        try:
            esfera = vtk.vtkSphereSource()
            esfera.SetCenter(0, 0, 0)
            esfera.SetRadius(radio)
            esfera.SetThetaResolution(32)
            esfera.SetPhiResolution(32)
            esfera_mapper = vtk.vtkPolyDataMapper()
            esfera_mapper.SetInputConnection(esfera.GetOutputPort())
            esfera_actor = vtk.vtkActor()
            esfera_actor.SetMapper(esfera_mapper)
            r = color.red() / 255.0
            g = color.green() / 255.0
            b = color.blue() / 255.0
            esfera_actor.GetProperty().SetColor(r, g, b)
            esfera_actor.GetProperty().SetOpacity(0.5)
            esfera_actor.SetPosition(x, y, z)
            # Crear el texto 3D usando vtkVectorText y vtkFollower
            texto_vector = vtk.vtkVectorText()
            texto_vector.SetText(nombre_esfera)
            texto_mapper = vtk.vtkPolyDataMapper()
            texto_mapper.SetInputConnection(texto_vector.GetOutputPort())
            texto_follower = vtk.vtkFollower()
            texto_follower.SetMapper(texto_mapper)
            texto_follower.GetProperty().SetColor(0, 0, 0)
            texto_follower.GetProperty().SetOpacity(1.0)
            # Ajustar la escala del texto proporcionalmente al radio de la esfera
            escala_texto = radio * 0.5
            texto_follower.SetScale(escala_texto, escala_texto, escala_texto)
            # Posicionar el texto cerca de la esfera
            texto_follower.SetPosition(x + radio, y, z + radio)
            texto_follower.SetCamera(VisorView.rendererVisor.GetActiveCamera())
            return True, esfera_actor, texto_follower
        except Exception as e:
            return False, None, None
    
    @staticmethod
    def abrir_dialogo(x, y, z):
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        topografiasmarcadas = None
        tree_actual = VisorView.main.findChild(QTreeWidget, "tree_actual_visor")
        lista = EquiposVisor.obtener_todos_elementos_marcados(tree_actual)
        if lista:
            topografiasmarcadas = VisorView.obtenerListaEquiposMarcados(lista, "Topografías")
        dialog, nombre_edit, radio_edit, color_container, combo_box, plot_widget = VisorView.create_sphere_dialog(x, y, z)
        def on_combo_change():
            radedit = float(radio_edit.text())
            # Iniciar Hilo
            loading = LoadingView.mostrarLoading()
            def on_threadcorte_complete():
                loading.close()
            prom = GenerarPrismaVirtualThread(x, y, z, radedit, topografiasmarcadas, combo_box, plot_widget)
            prom.task_finishPrismaVirtual.connect(on_threadcorte_complete)
            prom.start()
            loading.exec()
            # promedios = VisorView.calcular_y_graficar_promedio(x, y, z, float(radio_edit.text()), topografiasmarcadas)
            # # Graficar los resultados
            # VisorView.graficar_resultados(combo_box, plot_widget, promedios)
        combo_box.currentIndexChanged.connect(on_combo_change)
        if dialog.exec() == QDialog.Accepted:
            try:
                radio = float(radio_edit.text())
            except ValueError:
                radio = 1.0
            nombre_esfera = nombre_edit.text()
            selected_color = color_container[0]
            # Crear la esfera con las propiedades especificadas
            respuesta, actoresfera, actortexto = VisorView.crear_prisma_virtual(x, y, z, nombre_esfera, radio, selected_color)
            if respuesta:
                datos_componente = topografiasmarcadas[0][0]
                id_componente, nombrecomponente = datos_componente[1], datos_componente[0]
                respuesta = TopografiaController.ctrlRegistrarPrismaVirtual(id_componente, x, y, z, nombre_esfera, radio, VisorView.convert_color(selected_color))
                if respuesta:
                    # Agregar topos en nuevo componente
                    TreeCheckbox.crearNuevoGrupoCheckboxesSimple(tree_actual, nombrecomponente, id_componente, VisorView.idproyecto, 'Prismas Virtuales', '11', respuesta, 'prismavirtual')
    
    def convert_color(color):
        if isinstance(color, str):
            # Si el valor es un string, asumimos que es un color hexadecimal
            hex_color = color
            if hex_color.startswith('#'):
                hex_color = hex_color[1:]
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return QColor(r, g, b)
        elif isinstance(color, QColor):
            # Si el valor es un QColor, convertimos a hexadecimal
            return f'#{color.red():02X}{color.green():02X}{color.blue():02X}'
        else:
            raise ValueError("El valor de entrada debe ser un color hexadecimal (string) o un objeto QColor.")
    
    @staticmethod
    def calcular_y_graficar_promedio(x, y, z, radio, topografiasmarcadas):
        centro_esfera = np.array([x, y, z])
        promedios = []
        # Extraer los IDs de las topografías marcadas
        ids_topografias_marcadas = set()
        if topografiasmarcadas:
            for componente in topografiasmarcadas:
                for _, _, idtopo in componente[1]:
                    ids_topografias_marcadas.add(idtopo)
        for componente, idtopo, fecha, poli_datos in VisorView.polydatos_LAS:
            # Verificar si el idtopo está en las topografías marcadas
            if idtopo in ids_topografias_marcadas:
                puntos = np.array(poli_datos.GetPoints().GetData())
                distancias = np.linalg.norm(puntos - centro_esfera, axis=1)
                puntos_dentro_esfera = puntos[distancias <= radio]
                total_puntos = len(puntos_dentro_esfera)
                if total_puntos > 0:
                    promedio_x = np.mean(puntos_dentro_esfera[:, 0])
                    promedio_y = np.mean(puntos_dentro_esfera[:, 1])
                    promedio_z = np.mean(puntos_dentro_esfera[:, 2])
                    promedios.append((fecha, promedio_x, promedio_y, promedio_z))
        # retornar los promedios
        return promedios
    
    @staticmethod
    def graficar_resultados(combo_box, plot_widget, promedios):
        seleccion = combo_box.currentText()
        plot_widget.clear()  # Limpiar el gráfico anterior

        if seleccion == "Seleccionar Desplazamiento":
            return
        if len(promedios) == 1:
            # Si solo hay una fecha, graficar 0 en el eje Y
            fecha = datetime.strptime(promedios[0][0], "%Y-%m-%d")
            plot_widget.axes.plot(fecha, 0, 'ro', label='Desplazamiento')
        else:
            # Ordenar los promedios por fecha
            promedios.sort(key=lambda p: datetime.strptime(p[0], "%Y-%m-%d"))
            # Calcular el desplazamiento acumulado
            valores_base = np.array([promedios[0][1], promedios[0][2], promedios[0][3]])
            fechas = [datetime.strptime(p[0], "%Y-%m-%d") for p in promedios]
            x_vals = [p[1] for p in promedios]
            y_vals = [p[2] for p in promedios]
            z_vals = [p[3] for p in promedios]
            desplazamientos_x = [0] + [x - valores_base[0] for x in x_vals[1:]]
            desplazamientos_y = [0] + [y - valores_base[1] for y in y_vals[1:]]
            desplazamientos_z = [0] + [z - valores_base[2] for z in z_vals[1:]]
            if seleccion == "Desplazamiento Acumulado Este":
                plot_widget.axes.plot(fechas, desplazamientos_x, 'bo-', label='Desplazamiento Acumulado Este')
            elif seleccion == "Desplazamiento Acumulado Norte":
                plot_widget.axes.plot(fechas, desplazamientos_y, 'go-', label='Desplazamiento Acumulado Norte')
            elif seleccion == "Desplazamiento Acumulado Cota":
                plot_widget.axes.plot(fechas, desplazamientos_z, 'yo-', label='Desplazamiento Acumulado Cota')
        plot_widget.axes.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m-%Y'))
        plot_widget.axes.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        plot_widget.axes.set_xlabel('Fecha')
        plot_widget.axes.set_ylabel('Desplazamiento Acumulado')
        plot_widget.axes.set_title('Gráfico de Desplazamiento Acumulado')
        # Girar las etiquetas del eje X 90 grados
        plot_widget.axes.xaxis.set_tick_params(rotation=90)
        # Ajustar el layout para que el gráfico se adapte al widget
        plot_widget.figure.tight_layout()
        if promedios:
            plot_widget.axes.legend()
        plot_widget.axes.grid(True)
        plot_widget.axes.set_frame_on(True)
        plot_widget.draw()
    
    @staticmethod
    def create_sphere_dialog(x, y, z):
        dialog = QDialog()
        dialog.setWindowTitle("Propiedades de la Esfera")
        grid_layout = QGridLayout(dialog)
        labelname_coord = QLabel("Coordenadas:")
        coordena_label = QLabel(f"{x, y, z}")
        grid_layout.addWidget(labelname_coord, 0, 0)
        grid_layout.addWidget(coordena_label, 0, 1)
        nombre_label = QLabel("Nombre:")
        nombre_edit = QLineEdit(f"prisma_{random.randint(1, 1000)}")
        grid_layout.addWidget(nombre_label, 1, 0)
        grid_layout.addWidget(nombre_edit, 1, 1)
        radio_label = QLabel("Radio:")
        radio_edit = QLineEdit("1.00000")
        validator = QDoubleValidator(0.00001, 1e6, 5, dialog)
        validator.setNotation(QDoubleValidator.StandardNotation)
        radio_edit.setValidator(validator)
        grid_layout.addWidget(radio_label, 2, 0)
        grid_layout.addWidget(radio_edit, 2, 1)

        color_container = [QColor("red")]
        color_label = QLabel("Color:")
        color_button = QPushButton()
        color_button.setStyleSheet(f"background-color: {color_container[0].name()}")
        color_button.setText(color_container[0].name())

        def choose_color():
            color = QColorDialog.getColor(initial=color_container[0], parent=dialog, title="Seleccionar color")
            if color.isValid():
                color_container[0] = color
                color_button.setStyleSheet(f"background-color: {color.name()}")
                color_button.setText(color.name())

        color_button.clicked.connect(choose_color)
        grid_layout.addWidget(color_label, 3, 0)
        grid_layout.addWidget(color_button, 3, 1)

        combo_label = QLabel("Seleccionar Desplazamiento:")
        combo_box = QComboBox()
        combo_box.addItems(["Seleccionar Desplazamiento", "Desplazamiento Acumulado Este", "Desplazamiento Acumulado Norte", "Desplazamiento Acumulado Cota"])
        grid_layout.addWidget(combo_label, 4, 0)
        grid_layout.addWidget(combo_box, 4, 1)

        plot_widget = MplCanvas(dialog, width=5, height=4, dpi=100)
        plot_widget.axes.grid(False)
        plot_widget.axes.set_xticks([])
        plot_widget.axes.set_yticks([])
        plot_widget.axes.set_xticklabels([])
        plot_widget.axes.set_yticklabels([])
        plot_widget.axes.set_frame_on(False)
        plot_widget.draw()  # Refresca el lienzo en blanco
        grid_layout.addWidget(plot_widget, 5, 0, 1, 2)

        botones_layout = QHBoxLayout()
        aceptar_button = QPushButton("Aceptar")
        cancelar_button = QPushButton("Cancelar")
        botones_layout.addWidget(aceptar_button)
        botones_layout.addWidget(cancelar_button)
        grid_layout.addLayout(botones_layout, 6, 0, 1, 2)

        aceptar_button.clicked.connect(dialog.accept)
        cancelar_button.clicked.connect(dialog.reject)

        return dialog, nombre_edit, radio_edit, color_container, combo_box, plot_widget

    ################################################################
    def limpiarTopografiasVisor():
        if len(VisorView.toposDTM) > 0 or len(VisorView.listatopograficados) > 0:
            for compocod, codtopo, actor_dtm, color_dtm, rutadtm in VisorView.toposDTM:
                actor_dtm.SetVisibility(False)   
            for idcomponente, idtopo, tipo, actor, rutaactor in VisorView.listatopograficados:
                actor.SetVisibility(False)
            VisorView.vtkWidgetVisor.GetRenderWindow().Render()
    
    def mostrarPrismasVisor(prismasmarcados):
        VisorView.limpiarPrismasVisor()
        # dibujar prismas
        listaPrismas = PrismaController.ctrlObtenerPrismasFechaUnicos(VisorView.idproyecto, VisorView.fechainicial, VisorView.fechafinal)
        if len(listaPrismas) > 0:
            prismasactor = VisorView.createPointsActorPrismas(listaPrismas)
            # Agregar prismas a la escena
            if len(prismasactor) > 0:
                for prisma in prismasactor:
                    VisorView.rendererVisor.AddActor(prisma[0])
                    VisorView.rendererVisor.AddActor(prisma[1])
                    prisma[0].SetVisibility(False)
                    prisma[1].SetVisibility(False)
                    for componente, listaprismas in prismasmarcados:
                        for prismarcado in listaprismas:
                            if str(prisma[4]) == str(componente[1]) and str(prisma[2]) == str(prismarcado[0]) and str(prisma[3]) == str(prismarcado[1]):
                                prisma[0].SetVisibility(True)
                                prisma[1].SetVisibility(True)
            # si hay vectores mostrar
            if VisorView.estadovector:
                VisorView.escalarVectores(prismasmarcados)
        if VisorView.resetvisor is False:
            camera = VisorView.rendererVisor.GetActiveCamera()
            VisorView.rendererVisor.ResetCamera()
            camera.Zoom(1.5)
        VisorView.vtkWidgetVisor.GetRenderWindow().Render()
    
    def createPointsActorPrismas(data):
        respuesta = ConfiguracionVisor.obtenerDataConfiguracionVisor()
        tamaniotexto, radioprisma = respuesta[1], respuesta[3]
        colorprisma = MetodosGenerales.convertirHexadecimalRGB(respuesta[4])
        colortexto = MetodosGenerales.convertirHexadecimalRGB(respuesta[2])
        for item in data:
            idinstrumento = item[0]
            idcomponente = item[5]
            nameprisma = item[1]
            coord = (item[2], item[3], item[4])
            # Crear el actor del punto
            sphereSource = vtk.vtkSphereSource()
            sphereSource.SetCenter(coord[0], coord[1], coord[2])
            sphereSource.SetRadius(radioprisma)
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(sphereSource.GetOutputPort())
            punto_prisma = vtk.vtkActor()
            punto_prisma.SetMapper(mapper)
            punto_prisma.GetProperty().SetColor(colorprisma)
            # Crear el texto para el punto
            atext = vtkVectorText()
            atext.SetText(nameprisma)
            textMapper = vtkPolyDataMapper()
            textMapper.SetInputConnection(atext.GetOutputPort())
            textMapper.SetResolveCoincidentTopologyToPolygonOffset() 
            actorNombrePrisma = vtkFollower()
            actorNombrePrisma.SetMapper(textMapper)
            actorNombrePrisma.SetScale(tamaniotexto, tamaniotexto, tamaniotexto)
            actorNombrePrisma.AddPosition(coord[0] + 10, coord[1], coord[2])
            actorNombrePrisma.GetProperty().SetColor(colortexto)
            actorNombrePrisma.SetCamera(VisorView.rendererVisor.GetActiveCamera())
            # creamos la tupla de prismas
            VisorView.prismasGrafico.append((punto_prisma, actorNombrePrisma, nameprisma, idinstrumento, idcomponente, coord))
        return VisorView.prismasGrafico
    
    def limpiarPrismasVisor():
        if len(VisorView.prismasGrafico) > 0 or len(VisorView.vectoresDXF) > 0:
            for prisma in VisorView.prismasGrafico: # eliminar
                VisorView.rendererVisor.RemoveActor(prisma[0])
                VisorView.rendererVisor.RemoveActor(prisma[1])
            VisorView.prismasGrafico.clear()
            for vector in VisorView.vectoresDXF: # ocultar
                vector[3].SetVisibility(False)
            VisorView.vtkWidgetVisor.GetRenderWindow().Render()
    
    def recortarGrafico(paginacion, toposmarcados):
        VisorView.estadorenderizado_corte = 0
        if VisorView.boxWidget and VisorView.boxVisible:
            # Eliminar todos los actores del renderer CORTE
            VisorView.rendererCorte.RemoveAllViewProps()
            # Iniciar Hilo
            loading = LoadingView.mostrarLoading()
            def on_threadcorte_complete():
                loading.close()
            corte = ProcesarCorteTopografiaThread(VisorView.boxWidget, toposmarcados)
            corte.task_finishProcesarCorteTopo.connect(on_threadcorte_complete)
            corte.start()
            loading.exec()
            #VisorView.polyDataCorte, VisorView.limites_corte = VisorView.limitesBoxCallback(VisorView.boxWidget, None, toposmarcados)
            # Filtrar los prismas que están dentro del área de recorte
            prismas_corte = []
            vectores_corte = []
            inclinometros_puntos = []
            inclinometros_lineas = []
            piezocuerdas_corte = []
            piezomanuales_corte = []
            pluvios_corte = []
            celdas_corte = []
            aceleros_corte = []
            coaxiales_corte = []
            adicionales_corte = []
            if len(VisorView.prismasGrafico) > 0:
                for prisma in VisorView.prismasGrafico:
                    center_prisma = prisma[5]
                    # Convertir el punto de prueba al formato compatible
                    coordenada_equipo = VisorView.formatoCordenadas(center_prisma)
                    # Verificar si el punto está dentro de la geometría
                    if VisorView.point_inside_geometry(VisorView.limites_corte, coordenada_equipo):
                        prismas_corte.append(prisma)
            if len(VisorView.vectoresDXF) > 0:
                for vector in VisorView.vectoresDXF:
                    inicio_vector = vector[2]
                    coordenada_equipo = VisorView.formatoCordenadas(inicio_vector)
                    if VisorView.point_inside_geometry(VisorView.limites_corte, coordenada_equipo):
                        vectores_corte.append(vector)
            if len(VisorView.inclinometroPuntos) > 0:
                for punto_incli in VisorView.inclinometroPuntos:
                    center_incliP = punto_incli[2].GetCenter()
                    coordenada_equipo = VisorView.formatoCordenadas(center_incliP)
                    if VisorView.point_inside_geometry(VisorView.limites_corte, coordenada_equipo):
                        inclinometros_puntos.append(punto_incli)
                        for linea_incli in VisorView.inclinometrolineas:
                            if punto_incli[0] == linea_incli[0] and punto_incli[1] == linea_incli[1]:
                                inclinometros_lineas.append(linea_incli)
            if len(VisorView.piezometrostuboscuerda) > 0:
                for tubopiezocuerda in VisorView.piezometrostuboscuerda:
                    center_piezo = tubopiezocuerda[4].GetCenter()
                    coordenada_equipo = VisorView.formatoCordenadas(center_piezo)
                    if VisorView.point_inside_geometry(VisorView.limites_corte, coordenada_equipo):
                        piezocuerdas_corte.append(tubopiezocuerda)
            if len(VisorView.piezometrostubosmanual) > 0:
                for tubopiezomanual in VisorView.piezometrostubosmanual:
                    center_piezo = tubopiezomanual[4].GetCenter()
                    coordenada_equipo = VisorView.formatoCordenadas(center_piezo)
                    if VisorView.point_inside_geometry(VisorView.limites_corte, coordenada_equipo):
                        piezomanuales_corte.append(tubopiezomanual)
            if len(VisorView.listaactorespluvio) > 0:
                for actorpluvio in VisorView.listaactorespluvio:
                    center_pluvio = actorpluvio[2].GetCenter()
                    coordenada_equipo = VisorView.formatoCordenadas(center_pluvio)
                    if VisorView.point_inside_geometry(VisorView.limites_corte, coordenada_equipo):
                        pluvios_corte.append(actorpluvio)
            if len(VisorView.listaactoresceldas) > 0:
                for actorcelda in VisorView.listaactoresceldas:
                    center_celda = actorcelda[2].GetCenter()
                    coordenada_equipo = VisorView.formatoCordenadas(center_celda)
                    if VisorView.point_inside_geometry(VisorView.limites_corte, coordenada_equipo):
                        celdas_corte.append(actorcelda)
            if len(VisorView.listaactoresacelero) > 0:
                for actoracelero in VisorView.listaactoresacelero:
                    center_acelero = actoracelero[2].GetCenter()
                    coordenada_equipo = VisorView.formatoCordenadas(center_acelero)
                    if VisorView.point_inside_geometry(VisorView.limites_corte, coordenada_equipo):
                        aceleros_corte.append(actoracelero)
            if len(VisorView.cablescoaxiales) > 0:
                for punto_cable in VisorView.cablescoaxiales:
                    center_cable = punto_cable[2].GetCenter()
                    coordenada_equipo = VisorView.formatoCordenadas(center_cable)
                    if VisorView.point_inside_geometry(VisorView.limites_corte, coordenada_equipo):
                        coaxiales_corte.append(punto_cable)
            if len(VisorView.equiposgenerales) > 0:
                for actorequipo in VisorView.equiposgenerales:
                    center_equipo = actorequipo[3].GetCenter()
                    coordenada_equipo = VisorView.formatoCordenadas(center_equipo)
                    if VisorView.point_inside_geometry(VisorView.limites_corte, coordenada_equipo):
                        adicionales_corte.append(actorequipo)
            # Agregar prismas a la escena
            for actorprisma in prismas_corte:
                actorprisma[1].SetCamera(VisorView.rendererCorte.GetActiveCamera())
                VisorView.rendererCorte.AddActor(actorprisma[0])
                VisorView.rendererCorte.AddActor(actorprisma[1])
            # Agregar vectores a la escena
            for vector in vectores_corte:
                VisorView.rendererCorte.AddActor(vector[3])
            # Agregar puntos inclinometros a la escena
            for inclinometro_punto in inclinometros_puntos:
                inclinometro_punto[3].SetCamera(VisorView.rendererCorte.GetActiveCamera())
                VisorView.rendererCorte.AddActor(inclinometro_punto[2])
                VisorView.rendererCorte.AddActor(inclinometro_punto[3])
            # Agregar lineas inclinometros a la escena
            for inclilineas in inclinometros_lineas:
                VisorView.rendererCorte.AddActor(inclilineas[3])
            # Agregar tubos piezometros a la escena
            for tubo_corte in piezocuerdas_corte:
                tubo_corte[3].SetCamera(VisorView.rendererCorte.GetActiveCamera())
                VisorView.rendererCorte.AddActor(tubo_corte[3])
                VisorView.rendererCorte.AddActor(tubo_corte[4])
                if tubo_corte[0] == "DOS":
                    VisorView.rendererCorte.AddActor(tubo_corte[5])
            for tubo_corte in piezomanuales_corte:
                tubo_corte[3].SetCamera(VisorView.rendererCorte.GetActiveCamera())
                VisorView.rendererCorte.AddActor(tubo_corte[3])
                VisorView.rendererCorte.AddActor(tubo_corte[4])
                if tubo_corte[0] == "DOS":
                    VisorView.rendererCorte.AddActor(tubo_corte[5])
            # Agregar Pluviometros
            for actor in pluvios_corte:
                actor[3].SetCamera(VisorView.rendererCorte.GetActiveCamera())
                VisorView.rendererCorte.AddActor(actor[2])
                VisorView.rendererCorte.AddActor(actor[3])
            # Agregar Celdas
            for actor in celdas_corte:
                actor[3].SetCamera(VisorView.rendererCorte.GetActiveCamera())
                VisorView.rendererCorte.AddActor(actor[2])
                VisorView.rendererCorte.AddActor(actor[3])
            # Agregar Acelerografos
            for actor in aceleros_corte:
                actor[3].SetCamera(VisorView.rendererCorte.GetActiveCamera())
                VisorView.rendererCorte.AddActor(actor[2])
                VisorView.rendererCorte.AddActor(actor[3])
            # Agregar cable a la escena
            for cable in coaxiales_corte:
                cable[3].SetCamera(VisorView.rendererCorte.GetActiveCamera())
                VisorView.rendererCorte.AddActor(cable[2])
                VisorView.rendererCorte.AddActor(cable[3])
            # Agregar equipo general a la escena
            for otroequipo in adicionales_corte:
                otroequipo[2].SetCamera(VisorView.rendererCorte.GetActiveCamera())
                VisorView.rendererCorte.AddActor(otroequipo[2])
                VisorView.rendererCorte.AddActor(otroequipo[3])
            for actorCorte, planes, color in VisorView.polyDataCorte:
                # Agregar el polígono de recorte a la escena
                mapper_corte = vtk.vtkPolyDataMapper()
                mapper_corte.SetInputData(actorCorte)
                actorVisor_corte = vtk.vtkActor()
                actorVisor_corte.SetMapper(mapper_corte)
                actorVisor_corte.GetProperty().SetColor(color)
                # Verificar si el tipo de geometría es punto
                if actorCorte.GetNumberOfPoints() > 0:
                    actorVisor_corte.GetProperty().SetPointSize(1.5)
                VisorView.lista_actoresDXF_corte.append(actorVisor_corte)
                VisorView.rendererCorte.AddActor(actorVisor_corte)
            # CAMBIAR DE VISTA
            paginacion.setCurrentIndex(1)
            # configurar cámara visor
            VisorView.rendererCorte.ResetCamera()
            VisorView.rendererCorte.Render()
            camera_corte = VisorView.rendererCorte.GetActiveCamera()
            camera_corte.Zoom(1.5)
            VisorView.vtkWidgetCorte.GetRenderWindow().Render()
            return True
        else:
            return False
    
    def limitesBoxCallback(obj, event, topografiamarcados):
        # Obtener los números de los datos de entrada
        numeros_filtrar = [(componente[1], idtopo) for componente, listatopos in topografiamarcados for nomtopo, idinstru, idtopo in listatopos]
        # Filtrar la lista de actores basándose en los números
        actores_filtrados = [(componid, topoid, tipotopo, actor) for componid, topoid, tipotopo, actor, rutaactor in VisorView.listatopograficados if (componid, topoid) in numeros_filtrar]
        actores = []
        for compoid, topocode, tip, actors in actores_filtrados:
            actores.append(actors)
        resultados = []
        # Obtener las esquinas del cuadro general
        polyDataBox = vtk.vtkPolyData()
        obj.GetPolyData(polyDataBox)
        points = polyDataBox.GetPoints()
        corners = []
        for i in range(8):
            corner = [0.0, 0.0, 0.0]
            points.GetPoint(i, corner)
            corners.append(corner)
        for actor in actores:
            mapper = actor.GetMapper()
            polyData = mapper.GetInput()
            # Crear un filtro de recorte
            clipFunction = vtk.vtkClipPolyData()
            clipFunction.SetInputData(polyData)
            # Establecer el plano de recorte
            planes = vtk.vtkPlanes()
            obj.GetPlanes(planes)
            clipFunction.SetClipFunction(planes)
            clipFunction.InsideOutOn()
            clipFunction.Update()
            # Obtener el poliedro recortado
            clippedPolyData = clipFunction.GetOutput()
            # Obtener el color del actor
            color = actor.GetProperty().GetColor()
            # Agregar el poliedro recortado y el color al arreglo de resultados
            resultados.append((clippedPolyData, planes, color))
        # igualar los arreglos
        VisorView.polyDataCorte, VisorView.limites_corte = resultados, corners
        #return resultados, corners
    
    def formatoCordenadas(point):
        return np.array([point])    

    def point_inside_geometry(points, coordenada_equipo):
        # Convertimos los puntos a un arreglo numpy
        points = np.array(points)
        # Verificamos si los puntos son 2D o 3D
        if points.shape[1] == 2:
            # Si son 2D, utilizamos ConvexHull
            hull = ConvexHull(points)
            return hull.find_simplex(coordenada_equipo) >= 0
        elif points.shape[1] == 3:
            # Si son 3D, utilizamos Delaunay
            tri = Delaunay(points)
            return tri.find_simplex(coordenada_equipo) >= 0
        else:
            raise ValueError("Los puntos deben ser 2D o 3D")
        
    def reiniciarBox():
        if VisorView.boxWidget:
            if VisorView.boxWidget.GetEnabled():
                VisorView.boxWidget.Off()
            # Liberar la memoria asignada al boxWidget
            VisorView.boxWidget.SetInteractor(None)
            VisorView.boxWidget.SetCurrentRenderer(None)
            VisorView.boxWidget.SetEnabled(0)
            VisorView.boxWidget = None
            VisorView.estado_box = True
    
    def mostrarVectores(tree_actual):
        lista = EquiposVisor.obtener_todos_elementos_marcados(tree_actual)
        if lista:
            prismasmarcados = VisorView.obtenerListaEquiposMarcados(lista, "Prismas")
            if len(prismasmarcados) > 0:
                respuesta, estadvect, tipvect, escavect = UmbralView.dialogoConfiguracionVectores(VisorView.estadovector, VisorView.tipovector, VisorView.escalavector)
                if respuesta:
                    VisorView.estadovector, VisorView.tipovector, VisorView.escalavector = estadvect, tipvect, escavect
                    VisorView.escalarVectores(prismasmarcados)
    
    def escalarVectores(prismasmarcados):
        if len(VisorView.vectoresDXF) > 0:
            for vector in VisorView.vectoresDXF:
                VisorView.rendererVisor.RemoveActor(vector[3])
            VisorView.vectoresDXF.clear()
        if VisorView.estadovector:
            estadovect, VisorView.vectoresDXF = VisorView.vectoresPrismas(prismasmarcados)
            if estadovect == "OK":
                for vector in VisorView.vectoresDXF: # id inst, id compon, coord, actor
                    vector[3].SetVisibility(False)
                    for componente, listaprismas in prismasmarcados:
                        for prismarcado in listaprismas:
                            if str(vector[0]) == str(prismarcado[1]) and str(vector[1]) == str(componente[1]):
                                vector[3].SetVisibility(True)
            elif estadovect == "NO":
                mostrar_mensaje("Mostrar Vectores", "No hay umbrales configurados.", "advertencia")
            else:
                mostrar_mensaje("Mostrar Vectores", "No se puede mostrar los vectores.", "advertencia")
        VisorView.vtkWidgetVisor.GetRenderWindow().Render()
    
    def vectoresPrismas(prismasmarcados):
        if VisorView.estadovector:
            config = SoftwareConfiguracion.obtenerDataSoftware()
            velocprisma, filtrado = config[15], config[16]
            info = ConfiguracionVisor.obtenerDataConfiguracionVisor()
            grosor = info[17]
            piniciales = PrismaController.ctrlObtenerPrismasInicialesFecha(prismasmarcados, VisorView.fechainicial, VisorView.fechafinal, filtrado)
            pfinales = PrismaController.ctrlObtenerPrismasFinalesFecha(prismasmarcados, VisorView.fechainicial, VisorView.fechafinal, filtrado)
            puntos_iniciales = [(tupla[2], tupla[3], tupla[4]) for tupla in piniciales]
            puntos_finales = [(tupla[2], tupla[3], tupla[4]) for tupla in pfinales]
            nombreprismas = [(tupla[0], tupla[1], tupla[5]) for tupla in pfinales]
            print(f'prismas: {nombreprismas}')
            print(f'puntos iniciales: {puntos_iniciales}')
            print(f'puntos finales: {puntos_finales}')
            vectores = []  # Arreglo para almacenar la información de los vectores
            VisorView.colorvectores.clear()
            # Traer distancias según tipo
            umbrales_color = []
            idcomponente = prismasmarcados[0][0][1]
            if VisorView.tipovector == "D3D":
                distancias = PrismaController.ctrlObtenerDistanciaVectores3DPrisma(VisorView.idproyecto, prismasmarcados, VisorView.fechainicial, VisorView.fechafinal, filtrado)
                umbrales = UmbralController.ctrObtenerUmbralPrismas(VisorView.idproyecto, idcomponente, "3DA")
                if umbrales:
                    for fila in umbrales:
                        nombre, color, valor = fila[3], fila[4], fila[6]
                        umbrales_color.append((nombre, color, valor))
            else:
                distancias = PrismaController.ctrlObtenerDistanciaVectoresVI3DPrisma(VisorView.idproyecto, prismasmarcados, VisorView.fechainicial, VisorView.fechafinal, filtrado, velocprisma)
                umbrales = UmbralController.ctrObtenerUmbralPrismas(VisorView.idproyecto, idcomponente, "VI3D")
                if umbrales:
                    for fila in umbrales:
                        nombre, color, valor = fila[3], fila[4], fila[6]
                        umbrales_color.append((nombre, color, valor))
            if umbrales_color:
                if puntos_iniciales and puntos_finales:
                    umbrales_color.sort(key=lambda x: x[2]) # ordenar por valor
                    for prisma, punto_inicio, punto_fin in zip(nombreprismas, puntos_iniciales, puntos_finales):
                        # Calcular la dirección de la flecha
                        if punto_inicio == punto_fin:
                            continue
                        direccion = [punto_fin[i] - punto_inicio[i] for i in range(3)]
                        # Calcular el punto final de la flecha
                        if VisorView.escalavector > 0:
                            # Normalizar la dirección
                            longitud = vtk.vtkMath.Norm(direccion)
                            direccion_normalizada = [direccion[i] / longitud for i in range(3)]
                            # Calcular el punto final de la flecha
                            punto_fin_fijo = [punto_inicio[i] + direccion_normalizada[i] * VisorView.escalavector for i in range(3)]
                            # Ajustar la posición de la punta del cono hacia atrás a lo largo de la dirección normalizada
                            punto_punta_cono = [punto_inicio[i] + direccion_normalizada[i] * (VisorView.escalavector + 5) for i in range(3)]
                        else:
                            # Escalar la dirección para ajustar la longitud
                            direccion_normalizada = [direccion[i] * VisorView.escalavector for i in range(3)]
                            # Calcular el punto final escalado
                            punto_fin_fijo = [punto_inicio[i] + direccion_normalizada[i] for i in range(3)]
                            # Ajustar la posición de la punta del cono hacia atrás a lo largo de la dirección normalizada
                            punto_punta_cono = [punto_inicio[i] + direccion_normalizada[i] * (VisorView.escalavector + 5) for i in range(3)]
                        # Calcular la distancia entre los puntos inicial y final
                        for dato in distancias:
                            if dato[0] == prisma[0] and dato[1] == prisma[1]:
                                # Determinar el color de la flecha en función de la distancia  
                                distancia = abs(float(dato[5]))
                                colorcito = umbrales_color[0][1]
                                for nombre, color, valor in umbrales_color:
                                    if distancia <= float(valor):
                                        colorcito = color
                                        break
                                color_rgb = MetodosGenerales.convertirHexadecimalRGB(colorcito)
                                VisorView.colorvectores.append((prisma[0], prisma[2], color_rgb)) # id inst, id compon, color
                                # Crear un objeto vtkPoints para almacenar los puntos de inicio y fin
                                puntos = vtk.vtkPoints()
                                puntos.InsertNextPoint(punto_inicio)
                                puntos.InsertNextPoint(punto_fin_fijo)
                                # Crear una línea conectando los puntos de inicio y fin
                                linea = vtk.vtkLine()
                                linea.GetPointIds().SetId(0, 0)
                                linea.GetPointIds().SetId(1, 1)
                                # Crear un objeto vtkCellArray para almacenar la línea
                                lineas = vtk.vtkCellArray()
                                lineas.InsertNextCell(linea)
                                # Crear un objeto vtkPolyData para contener la línea
                                polydata = vtk.vtkPolyData()
                                polydata.SetPoints(puntos)
                                polydata.SetLines(lineas)
                                # Crear un objeto vtkTubeFilter para dar grosor a la línea
                                tubo = vtk.vtkTubeFilter()
                                tubo.SetInputData(polydata)
                                tubo.SetRadius(grosor)
                                tubo.SetNumberOfSides(20)
                                # Crear un objeto vtkConeSource para la punta de la flecha
                                punta_cono = vtk.vtkConeSource()
                                # Establecer la posición de la punta del cono
                                punta_cono.SetCenter(punto_punta_cono)
                                punta_cono.SetDirection(direccion_normalizada)
                                anchocono = grosor * 2
                                largocono = grosor * 3
                                punta_cono.SetRadius(anchocono)
                                punta_cono.SetHeight(largocono)
                                # Combinar el cuerpo del cilindro y la punta del cono
                                appendFilter = vtk.vtkAppendPolyData()
                                appendFilter.AddInputConnection(tubo.GetOutputPort())
                                appendFilter.AddInputConnection(punta_cono.GetOutputPort())
                                appendFilter.Update()
                                # Crear un objeto vtkPolyDataMapper para mapear los datos
                                mapper = vtk.vtkPolyDataMapper()
                                mapper.SetInputConnection(appendFilter.GetOutputPort())
                                # Crear un objeto vtkActor para mostrar la flecha
                                flecha = vtk.vtkActor()
                                flecha.SetMapper(mapper)
                                flecha.GetProperty().SetColor(color_rgb)  
                                # Agregar el actor al renderer
                                VisorView.rendererVisor.AddActor(flecha)
                                flecha.SetVisibility(False)
                                vectores.append((prisma[0], prisma[2], punto_inicio, flecha)) # id inst, id compon, coord, actor
                    return "OK", vectores
                else:
                    return "NO", []
            else:
                return "NO", []
        else:
            return "ERROR", []
    
    # Graficar los inclinometros 3d en el visor
    def mostrarInclinometrosVisor(paginacion, escala, inclinometrofechasmarcados):
        if paginacion.currentIndex() == 0:
            # iniciar hilo
            # loading = LoadingView.cargar_loading()
            # def on_thread_complete():
            #     loading.close()
            # guardar_data_thread = ProcesarVisor3dThread(proyecto, ax, canvas, inclinometrofechasmarcados, escala, dibujar)
            # guardar_data_thread.task_finished.connect(on_thread_complete)
            # guardar_data_thread.start()
            # loading.exec()
            # fin hilo
            # Dibujar puntos y nombres
            if VisorView.dibujarLineaIncli == 0:
                VisorView.limpiarInclinometrosVisor()
            else:
                VisorView.ocultarInclinometrosVisor()
            if len(inclinometrofechasmarcados) > 0:
                VisorView.dibujarPuntosInclinometros(inclinometrofechasmarcados)
                VisorView.dibujarDesplazamientoInclinometros(inclinometrofechasmarcados, escala)
                VisorView.dibujarPuntoIncli = 1
                VisorView.dibujarLineaIncli = 1
                # mostrar puntos inclinometro
                for idcomponente, codinstru, puntito, label in VisorView.inclinometroPuntos:
                    puntito.SetVisibility(False)
                    label.SetVisibility(False)
                    for compo, listaincli in inclinometrofechasmarcados:
                        for nombreincli, idinstrum, dates in listaincli:
                            if str(idcomponente) == compo[1] and str(codinstru) == idinstrum:
                                puntito.SetVisibility(True)
                                label.SetVisibility(True)
                # mostrar lineas incli
                for idcomponen, idinstru, fecha, linea in VisorView.inclinometrolineas:
                    linea.SetVisibility(False)
                    for compon, inclinos in inclinometrofechasmarcados:
                        for nombreincli, idinstrume, fechas in inclinos:
                            # listafechas = ast.literal_eval(fechas)
                            # Le decimos a eval que cuando lea "datetime" en el texto, use el MÓDULO, no la clase.
                            contexto_seguro = {'datetime': dt_module}
                            
                            # Convertimos el texto a objetos reales
                            listafechas = eval(fechas, {"__builtins__": None}, contexto_seguro)
                            for fech in listafechas:
                                if str(fecha) == str(fech) and str(idcomponen) == compon[1] and str(idinstru) == idinstrume:
                                    linea.SetVisibility(True)
            # validar si no hay inclinometros
            if VisorView.resetvisor is False:
                camera = VisorView.rendererVisor.GetActiveCamera()
                VisorView.rendererVisor.ResetCamera()
                camera.Zoom(1.5)
            VisorView.vtkWidgetVisor.GetRenderWindow().Render()
    
    # dibujar puntos de inclinómetros
    def dibujarPuntosInclinometros(inclinometrosmarcados):
        # VisorView.inclinometroPuntos = []
        # VisorView.inclinometrosTubos = []
        listainclinometros = InclinometroController.ctrlListarInclinometrosProyecto(VisorView.idproyecto, inclinometrosmarcados)
        if len(listainclinometros) > 0:
            respuesta = ConfiguracionVisor.obtenerDataConfiguracionVisor()
            tamaniotexto, radioinclino = respuesta[1], respuesta[5]
            colorinclino = MetodosGenerales.convertirHexadecimalRGB(respuesta[6])
            colortexto = MetodosGenerales.convertirHexadecimalRGB(respuesta[2])
            # omitir si ya está graficado
            ids_graficados = {codinstru for idcomponente, codinstru, puntito, label in VisorView.inclinometroPuntos}
            for inclinome, fechas, idinstru in listainclinometros:
                if idinstru not in ids_graficados:
                    idinclino = inclinome[0]
                    idencabeza = inclinome[1]
                    nombreincli = inclinome[2]
                    idcompo = inclinome[3]
                    este = inclinome[4]
                    norte = inclinome[5]
                    nivel = inclinome[6]
                    tipografica = inclinome[12]
                    # graficar el punto o perforación
                    if tipografica == 1:
                        # Crear el texto para el punto
                        text = f"{nombreincli}"
                        atext = vtkVectorText()
                        atext.SetText(text)
                        textMapper = vtkPolyDataMapper()
                        textMapper.SetInputConnection(atext.GetOutputPort())
                        textMapper.SetResolveCoincidentTopologyToPolygonOffset()
                        actorNombreIncli = vtkFollower()
                        actorNombreIncli.SetMapper(textMapper)
                        actorNombreIncli.SetScale(tamaniotexto, tamaniotexto, tamaniotexto)
                        actorNombreIncli.AddPosition(este + 10, norte, nivel)                    
                        actorNombreIncli.GetProperty().SetColor(colortexto)
                        actorNombreIncli.SetCamera(VisorView.rendererVisor.GetActiveCamera())
                        # Crear el actor del punto
                        sphereSource = vtk.vtkSphereSource()
                        sphereSource.SetCenter(este, norte, nivel)
                        sphereSource.SetRadius(radioinclino)
                        mapper = vtk.vtkPolyDataMapper()
                        mapper.SetInputConnection(sphereSource.GetOutputPort())
                        punto_incli = vtk.vtkActor()
                        punto_incli.SetMapper(mapper)
                        punto_incli.GetProperty().SetColor(colorinclino)
                        # agregar al visor
                        VisorView.rendererVisor.AddActor(actorNombreIncli)
                        VisorView.rendererVisor.AddActor(punto_incli)
                        # creamos la tupla de prismas
                        VisorView.inclinometroPuntos.append((idcompo, idinstru, punto_incli, actorNombreIncli))
                    else:
                        # obtener datos
                        inclinacion = float(inclinome[9])
                        azimuth = 270 - float(inclinome[10])
                        profundidad = -1 * float(inclinome[11])
                        # Agregar los puntos al objeto vtkPoints
                        puntosondaje = vtk.vtkPoints()
                        xfondo, yfondo, zfondo = PiezometroController.ctrlCalcularCoordenadas3d(este, norte, nivel, inclinacion, azimuth, profundidad)
                        coord_sondaje = [(este, norte, nivel), (xfondo, yfondo, zfondo)]
                        for puntito in coord_sondaje:
                            puntosondaje.InsertNextPoint(puntito)
                        # Agregar las línea entre los dos puntos
                        lineasondaje = vtk.vtkPolyLine()
                        lineasondaje.GetPointIds().SetNumberOfIds(len(coord_sondaje))
                        for i in range(len(coord_sondaje)):
                            lineasondaje.GetPointIds().SetId(i, i)
                        # Crear celdas para las línea
                        cellsondaje = vtk.vtkCellArray()
                        cellsondaje.InsertNextCell(lineasondaje)
                        # Crear un objeto vtkPolyData para almacenar los puntos y la línea
                        polydatacon = vtk.vtkPolyData()
                        polydatacon.SetPoints(puntosondaje)
                        polydatacon.SetLines(cellsondaje)
                        # Crear un objeto vtkTubeFilter para dar grosor a la línea
                        tubocon = vtk.vtkTubeFilter()
                        tubocon.SetInputData(polydatacon)
                        tubocon.SetRadius(radioinclino)
                        tubocon.SetNumberOfSides(200)
                        # Crear un mapper para mapear los datos en geometría
                        mappercon = vtk.vtkPolyDataMapper()
                        mappercon.SetInputConnection(tubocon.GetOutputPort())
                        # Crear un actor para mostrar el desplazamiento
                        actorsondaje = vtk.vtkActor()
                        actorsondaje.SetMapper(mappercon)
                        actorsondaje.GetProperty().SetColor(colorinclino)
                        # Crear el texto para el punto
                        text = f"{nombreincli}"
                        atext = vtkVectorText()
                        atext.SetText(text)
                        textMapper = vtkPolyDataMapper()
                        textMapper.SetInputConnection(atext.GetOutputPort())
                        textMapper.SetResolveCoincidentTopologyToPolygonOffset()
                        actorNombreIncli = vtkFollower()
                        actorNombreIncli.SetMapper(textMapper)
                        actorNombreIncli.SetScale(tamaniotexto, tamaniotexto, tamaniotexto)
                        actorNombreIncli.AddPosition(este + 10, norte, nivel)                    
                        actorNombreIncli.GetProperty().SetColor(colortexto)
                        actorNombreIncli.SetCamera(VisorView.rendererVisor.GetActiveCamera())
                        # agregar al visor
                        VisorView.rendererVisor.AddActor(actorNombreIncli)
                        VisorView.rendererVisor.AddActor(actorsondaje)
                        # creamos la tupla de prismas
                        VisorView.inclinometroPuntos.append((idcompo, idinstru, actorsondaje, actorNombreIncli))
        
    # dibujar desplazamientos de inclinometros
    def dibujarDesplazamientoInclinometros(inclinometrosmarcados, escala):
        colores = [
            (1.0, 0.0, 0.0),   # Rojo
            (0.0, 1.0, 0.0),   # Verde
            (0.0, 0.0, 1.0),   # Azul
            (1.0, 1.0, 0.0),   # Amarillo
            (1.0, 0.0, 1.0),   # Magenta
            (0.0, 1.0, 1.0),   # Cian
            (0.5, 0.5, 0.5),   # Gris
            (1.0, 0.5, 0.0),   # Naranja
            (0.5, 0.0, 1.0),   # Púrpura
            (0.0, 0.5, 0.0),   # Verde oscuro
            (0.0, 0.0, 0.5),   # Azul oscuro
            (0.8, 0.8, 0.8),   # Gris claro
            (0.5, 1.0, 0.0),   # Verde lima
            (0.0, 0.5, 0.5),   # Verde azulado
            (0.5, 0.0, 0.5),   # Magenta oscuro
            (0.6, 0.3, 0.0)    # Marrón
        ]
        listainclinometros = InclinometroController.ctrlListarInclinometrosProyecto(VisorView.idproyecto, inclinometrosmarcados)
        if len(listainclinometros) > 0:
            ids_graficados = {codinstru for idcompo, codinstru, fecha, linea in VisorView.inclinometrolineas}
            for inclinome, fechitas, idinstru in listainclinometros:
                if idinstru not in ids_graficados: # verificar si ya está graficado
                    # fechas = ast.literal_eval(fechitas)
                     # Le decimos a eval que cuando lea "datetime" en el texto, use el MÓDULO, no la clase.
                    contexto_seguro = {'datetime': dt_module}
                    
                    # Convertimos el texto a objetos reales
                    fechas = eval(fechitas, {"__builtins__": None}, contexto_seguro)
                    
                    idinclino = inclinome[0]
                    idencabeza = inclinome[1]
                    nameincli = inclinome[2]
                    idcompo = inclinome[3]
                    este = inclinome[4]
                    norte = inclinome[5]
                    nivel = inclinome[6]
                    fechabase = inclinome[7]
                    tipoequipo = inclinome[8]
                    if tipoequipo == "RST":
                        datanormal = InclinometroController.ctrlObtenerDANEvisor(VisorView.idproyecto, idinclino, fechas, tipoequipo, este, norte, nivel, escala)
                        if datanormal:
                            color = 0
                            for fechita, datos in datanormal.items():
                                if len(datos) > 0:
                                    # dibujar desplzamientos inclinometro
                                    points = vtk.vtkPoints()
                                    lines = vtk.vtkPolyLine()
                                    lines.GetPointIds().SetNumberOfIds(len(datos))
                                    i = 0
                                    for incliname, ejez, ejex, ejey in datos:
                                        # insertar los puntos
                                        points.InsertNextPoint(ejex, ejey, ejez)
                                        lines.GetPointIds().SetId(i, i)
                                        i += 1
                                    # crear celda para las lineas
                                    cells = vtk.vtkCellArray()
                                    cells.InsertNextCell(lines)
                                    # Crear un objeto vtkPolyData para almacenar los puntos y las líneas
                                    polydata = vtk.vtkPolyData()
                                    polydata.SetPoints(points)
                                    polydata.SetLines(cells)
                                    # Crear un mapper para mapear los datos de la trayectoria en geometría
                                    mapper = vtk.vtkPolyDataMapper()
                                    mapper.SetInputData(polydata)
                                    # Crear un actor para la trayectoria
                                    actorlinea = vtk.vtkActor()
                                    actorlinea.SetMapper(mapper)
                                    if color == 16:
                                        color = 0
                                    actorlinea.GetProperty().SetColor(colores[color])
                                    actorlinea.GetProperty().SetLineWidth(4)
                                    # agregar al visor
                                    VisorView.rendererVisor.AddActor(actorlinea)
                                    # agregamos al arreglo
                                    VisorView.inclinometrolineas.append((idcompo, idinstru, fechita, actorlinea))
                                    color += 1
                    else: # GEOKON
                        datanormal = InclinometroController.ctrlObtenerDANEvisor(VisorView.idproyecto, idinclino, fechas, tipoequipo, este, norte, nivel, escala)
                        if datanormal:
                            color = 0
                            for fechita, datos in datanormal.items():
                                if len(datos) > 0:
                                    # dibujar desplazamientos inclinometro
                                    points = vtk.vtkPoints()
                                    lines = vtk.vtkPolyLine()
                                    lines.GetPointIds().SetNumberOfIds(len(datos))
                                    i = 0
                                    for incliname, ejez, ejex, ejey in datos:
                                        points.InsertNextPoint(ejex, ejey, ejez)
                                        lines.GetPointIds().SetId(i, i)
                                        i += 1
                                    # crear celda para las lineas
                                    cells = vtk.vtkCellArray()
                                    cells.InsertNextCell(lines)
                                    # Crear un objeto vtkPolyData para almacenar los puntos y las líneas
                                    polydata = vtk.vtkPolyData()
                                    polydata.SetPoints(points)
                                    polydata.SetLines(cells)
                                    # Crear un mapper para mapear los datos de la trayectoria en geometría
                                    mapper = vtk.vtkPolyDataMapper()
                                    mapper.SetInputData(polydata)
                                    # Crear un actor para la trayectoria
                                    actorlinea = vtk.vtkActor()
                                    actorlinea.SetMapper(mapper)
                                    if color == 16:
                                        color = 0
                                    actorlinea.GetProperty().SetColor(colores[color])
                                    actorlinea.GetProperty().SetLineWidth(5)
                                    # agregar al visor
                                    VisorView.rendererVisor.AddActor(actorlinea)
                                    # agregamos al arreglo
                                    VisorView.inclinometrolineas.append((idcompo, idinstru, fechita, actorlinea))
                                    color += 1
        
    def limpiarInclinometrosVisor():
        VisorView.dibujarPuntoIncli = 0
        VisorView.dibujarLineaIncli = 0
        if len(VisorView.inclinometroPuntos) > 0 or len(VisorView.inclinometrolineas) > 0:
            for idcomponente, codinclino, punto, label in VisorView.inclinometroPuntos:
                VisorView.rendererVisor.RemoveActor(punto)
                VisorView.rendererVisor.RemoveActor(label)
            VisorView.inclinometroPuntos.clear()
            for idcompo, idinstru, fecha, linea in VisorView.inclinometrolineas:
                VisorView.rendererVisor.RemoveActor(linea)
            VisorView.inclinometrolineas.clear()
            VisorView.vtkWidgetVisor.GetRenderWindow().Render()
    
    def ocultarInclinometrosVisor():
        if len(VisorView.inclinometroPuntos) > 0 or len(VisorView.inclinometrolineas) > 0:
            for idcomponente, codinstru, puntito, label in VisorView.inclinometroPuntos:
                puntito.SetVisibility(False)
                label.SetVisibility(False)
            for idcomponen, idinstru, fecha, linea in VisorView.inclinometrolineas:
                linea.SetVisibility(False)
            VisorView.vtkWidgetVisor.GetRenderWindow().Render()
    
    def mostrarPiezometrosCuerdaVisor(paginacion, piezocuerdafechasmarcados):
        if paginacion.currentIndex() == 0:
            if len(piezocuerdafechasmarcados) > 0:
                # limpiar cilindros
                VisorView.limpiarPiezometrosCuerdaVisor()
                # dibujar cilindros marcados
                piezoerroneos = []
                listapiezometroscuerda = PiezometroController.ctrlListarPiezometrosCuerdaProyecto(VisorView.idproyecto, piezocuerdafechasmarcados)
                if len(listapiezometroscuerda) > 0:
                    respuesta = ConfiguracionVisor.obtenerDataConfiguracionVisor()
                    tamaniotexto, radiopiezo = respuesta[1], respuesta[7]
                    colorpiezo = MetodosGenerales.convertirHexadecimalRGB(respuesta[8])
                    colortexto = MetodosGenerales.convertirHexadecimalRGB(respuesta[2])
                    for piezome in listapiezometroscuerda:
                        idpiezo = piezome[0]
                        nombrepiezo = piezome[1]
                        idcomponente = piezome[2]
                        este = piezome[3]
                        norte = piezome[4]
                        nivel = piezome[5]
                        inclinacion = piezome[6]
                        azimut = piezome[7]
                        subtipo = piezome[8]
                        fecha = piezome[9]
                        detalle = piezome[10]
                        superficie = piezome[11]
                        if detalle is not None and detalle != "":
                            dibujar = True
                            dibujo = 1
                            # DIBUJAR CUERDA VIBRANTE
                            azimuth = 270 - azimut
                            if subtipo == 1: # data calculada sin cota
                                lectura = detalle
                                if superficie and superficie > nivel:
                                    distancia, estesup, nortesup = PiezometroController.ctrlCalcularDistanciaCoordenadas(este, norte, nivel, superficie, inclinacion, azimuth)
                                    profundidad = distancia
                                    if lectura > 0: # tiene agua
                                        if distancia > lectura: # con agua y sin agua
                                            depth = -(float(profundidad) - float(lectura))
                                            xsinagua, ysinagua, zsinagua = PiezometroController.ctrlCalcularCoordenadas3d(estesup, nortesup, superficie, inclinacion, azimuth, depth)
                                        else: # solo agua
                                            dibujo = 2
                                            depth = -lectura
                                            xfondo, yfondo, zfondo = PiezometroController.ctrlCalcularCoordenadas3d(estesup, nortesup, superficie, inclinacion, azimuth, depth)
                                    else: # está seco
                                        dibujo = 3
                                        depth = -profundidad
                                        xfondo, yfondo, zfondo = PiezometroController.ctrlCalcularCoordenadas3d(estesup, nortesup, superficie, inclinacion, azimuth, depth)
                                else:
                                    dibujar = False
                                    piezoerroneos.append(nombrepiezo)
                            else: # 2 data calculada con cota
                                lectura = detalle
                                if superficie and superficie > nivel:
                                    distancia, estesup, nortesup = PiezometroController.ctrlCalcularDistanciaCoordenadas(este, norte, nivel, superficie, inclinacion, azimuth)
                                    profundidad = distancia
                                    if lectura > nivel:
                                        if superficie > lectura:
                                            depth = superficie - lectura
                                            xsinagua, ysinagua, zsinagua = PiezometroController.ctrlCalcularCoordenadas3d(estesup, nortesup, superficie, inclinacion, azimuth, depth)
                                        else:
                                            dibujo = 2
                                            xfondo, yfondo, zfondo = PiezometroController.ctrlCalcularCoordenadas3d(estesup, nortesup, superficie, inclinacion, azimuth, profundidad)
                                    else:
                                        dibujo = 3
                                        xfondo, yfondo, zfondo = PiezometroController.ctrlCalcularCoordenadas3d(estesup, nortesup, superficie, inclinacion, azimuth, profundidad)
                                else:
                                    dibujar = False
                                    piezoerroneos.append(nombrepiezo)
                            # DIBUJAR TUBERIA DEL PIEZÓMETRO
                            if dibujo == 1: # dos tubos con y sin agua
                                if dibujar:
                                    puntosinagua = vtk.vtkPoints()
                                    puntoconagua = vtk.vtkPoints()
                                    coord_sinagua = [(estesup, nortesup, superficie), (xsinagua, ysinagua, zsinagua)]
                                    for punto in coord_sinagua:
                                        puntosinagua.InsertNextPoint(punto)
                                    coord_conagua = [(xsinagua, ysinagua, zsinagua), (este, norte, nivel)]
                                    for puntito in coord_conagua:
                                        puntoconagua.InsertNextPoint(puntito)
                                    # Agregar las líneas para cada desplazamiento
                                    lineasinagua = vtk.vtkPolyLine()
                                    lineasinagua.GetPointIds().SetNumberOfIds(len(coord_sinagua))
                                    for i in range(len(coord_sinagua)):
                                        lineasinagua.GetPointIds().SetId(i, i)
                                    lineaconagua = vtk.vtkPolyLine()
                                    lineaconagua.GetPointIds().SetNumberOfIds(len(coord_conagua))
                                    for i in range(len(coord_conagua)):
                                        lineaconagua.GetPointIds().SetId(i, i)
                                    # Crear celdas para las líneas
                                    cellsinagua = vtk.vtkCellArray()
                                    cellsinagua.InsertNextCell(lineasinagua)
                                    cellconagua = vtk.vtkCellArray()
                                    cellconagua.InsertNextCell(lineasinagua)
                                    # Crear un objeto vtkPolyData para almacenar los puntos y las líneas
                                    polydatasin = vtk.vtkPolyData()
                                    polydatasin.SetPoints(puntosinagua)
                                    polydatasin.SetLines(cellsinagua)
                                    polydatacon = vtk.vtkPolyData()
                                    polydatacon.SetPoints(puntoconagua)
                                    polydatacon.SetLines(cellconagua)
                                    # Crear un objeto vtkTubeFilter para dar grosor a las líneas
                                    tubosin = vtk.vtkTubeFilter()
                                    tubosin.SetInputData(polydatasin)
                                    tubosin.SetRadius(radiopiezo)
                                    tubosin.SetNumberOfSides(200)
                                    tubosin.SetCapping(True)
                                    tubocon = vtk.vtkTubeFilter()
                                    tubocon.SetInputData(polydatacon)
                                    tubocon.SetRadius(radiopiezo)
                                    tubocon.SetNumberOfSides(200)
                                    tubocon.SetCapping(True)
                                    # Crear un mapper para mapear los datos en geometría
                                    mappersin = vtk.vtkPolyDataMapper()
                                    mappersin.SetInputConnection(tubosin.GetOutputPort())
                                    mappercon = vtk.vtkPolyDataMapper()
                                    mappercon.SetInputConnection(tubocon.GetOutputPort())
                                    # Crear un actor para mostrar los desplazamientos
                                    actorsinagua = vtk.vtkActor()
                                    actorsinagua.SetMapper(mappersin)
                                    actorsinagua.GetProperty().SetColor(colorpiezo)
                                    actorconagua = vtk.vtkActor()
                                    actorconagua.SetMapper(mappercon)
                                    actorconagua.GetProperty().SetColor(0.0, 1.0, 1.0) # cian
                                    # Crear el texto para el punto
                                    atext = vtkVectorText()
                                    atext.SetText(str(nombrepiezo))
                                    textMapper = vtkPolyDataMapper()
                                    textMapper.SetInputConnection(atext.GetOutputPort())
                                    textMapper.SetResolveCoincidentTopologyToPolygonOffset()
                                    actorNombrePiezo = vtkFollower()
                                    actorNombrePiezo.SetMapper(textMapper)
                                    actorNombrePiezo.SetScale(tamaniotexto, tamaniotexto, tamaniotexto)
                                    actorNombrePiezo.AddPosition(estesup + 10, nortesup, superficie)                      
                                    actorNombrePiezo.GetProperty().SetColor(colortexto)
                                    actorNombrePiezo.SetCamera(VisorView.rendererVisor.GetActiveCamera())
                                    VisorView.rendererVisor.AddActor(actorNombrePiezo)
                                    VisorView.rendererVisor.AddActor(actorsinagua)
                                    VisorView.rendererVisor.AddActor(actorconagua)
                                    # creamos la tupla de prismas
                                    VisorView.piezometrostuboscuerda.append(("DOS", idcomponente, idpiezo, actorNombrePiezo, actorsinagua, actorconagua)) # tipo, label, tubos
                            else: # un tubo
                                if dibujo == 2:
                                    color = (0.0, 1.0, 1.0) # cian
                                else:
                                    color = colorpiezo
                                if dibujar:
                                    puntoconagua = vtk.vtkPoints()
                                    coord_conagua = [(estesup, nortesup, superficie), (xfondo, yfondo, zfondo)]
                                    for puntito in coord_conagua:
                                        puntoconagua.InsertNextPoint(puntito)
                                    # Agregar las línea entre los dos puntos
                                    lineaconagua = vtk.vtkPolyLine()
                                    lineaconagua.GetPointIds().SetNumberOfIds(len(coord_conagua))
                                    for i in range(len(coord_conagua)):
                                        lineaconagua.GetPointIds().SetId(i, i)
                                    # Crear celdas para las línea
                                    cellconagua = vtk.vtkCellArray()
                                    cellconagua.InsertNextCell(lineaconagua)
                                    # Crear un objeto vtkPolyData para almacenar los puntos y la línea
                                    polydatacon = vtk.vtkPolyData()
                                    polydatacon.SetPoints(puntoconagua)
                                    polydatacon.SetLines(cellconagua)
                                    # Crear un objeto vtkTubeFilter para dar grosor a la línea
                                    tubocon = vtk.vtkTubeFilter()
                                    tubocon.SetInputData(polydatacon)
                                    tubocon.SetRadius(radiopiezo)
                                    tubocon.SetNumberOfSides(200)
                                    tubocon.SetCapping(True)
                                    # Crear un mapper para mapear los datos en geometría
                                    mappercon = vtk.vtkPolyDataMapper()
                                    mappercon.SetInputConnection(tubocon.GetOutputPort())
                                    # Crear un actor para mostrar el desplazamiento
                                    actorconagua = vtk.vtkActor()
                                    actorconagua.SetMapper(mappercon)
                                    actorconagua.GetProperty().SetColor(color)
                                    # Crear el texto para el punto
                                    atext = vtkVectorText()
                                    atext.SetText(str(nombrepiezo))
                                    textMapper = vtkPolyDataMapper()
                                    textMapper.SetInputConnection(atext.GetOutputPort())
                                    textMapper.SetResolveCoincidentTopologyToPolygonOffset()
                                    actorNombrePiezo = vtkFollower()
                                    actorNombrePiezo.SetMapper(textMapper)
                                    actorNombrePiezo.SetScale(tamaniotexto, tamaniotexto, tamaniotexto)
                                    actorNombrePiezo.AddPosition(estesup + 10, nortesup, superficie)
                                    actorNombrePiezo.GetProperty().SetColor(colortexto)
                                    actorNombrePiezo.SetCamera(VisorView.rendererVisor.GetActiveCamera())
                                    # agregar al visor
                                    VisorView.rendererVisor.AddActor(actorNombrePiezo)
                                    VisorView.rendererVisor.AddActor(actorconagua)
                                    # creamos la tupla de prismas
                                    VisorView.piezometrostuboscuerda.append(("UNO", idcomponente, idpiezo, actorNombrePiezo, actorconagua)) # tipo, label, tubo
                        else:
                            piezoerroneos.append(nombrepiezo)
                # validar si no hay piezos
                if VisorView.resetvisor is False:
                    camera = VisorView.rendererVisor.GetActiveCamera()
                    VisorView.rendererVisor.ResetCamera()
                    camera.Zoom(1.5)
                VisorView.vtkWidgetVisor.GetRenderWindow().Render()
                if len(piezoerroneos) > 0:
                    mostrar_mensaje("ERROR AL MOSTRAR PIEZÓMETRO", f"Hubo error con los siguientes piezómetros:\n {piezoerroneos}", "advertencia")
    
    def mostrarPiezometrosManualVisor(paginacion, piezomanualfechasmarcados):
        if paginacion.currentIndex() == 0:
            if len(piezomanualfechasmarcados) > 0:
                # limpiar cilindros
                VisorView.limpiarPiezometrosManualVisor()
                # dibujar cilindros marcados
                piezoerroneos = []
                listapiezometrosmanual = PiezometroController.ctrlListarPiezometrosManualProyecto(VisorView.idproyecto, piezomanualfechasmarcados)
                if len(listapiezometrosmanual) > 0:
                    respuesta = ConfiguracionVisor.obtenerDataConfiguracionVisor()
                    tamaniotexto, radiopiezo = respuesta[1], respuesta[7]
                    colorpiezo = MetodosGenerales.convertirHexadecimalRGB(respuesta[8])
                    colortexto = MetodosGenerales.convertirHexadecimalRGB(respuesta[2])
                    for piezome in listapiezometrosmanual:
                        idpiezo = piezome[0]
                        nombrepiezo = piezome[1]
                        idcomponente = piezome[2]
                        este = piezome[3]
                        norte = piezome[4]
                        nivel = piezome[5]
                        inclinacion = piezome[6]
                        azimut = piezome[7]
                        stickup = piezome[8]
                        subtipo = piezome[9]
                        fecha = piezome[10]
                        detalle = piezome[11]
                        superficie = piezome[12]
                        if detalle is not None and detalle != "":
                            dibujo = 1
                            dibujar = True
                            azimuth = 270 - azimut
                            # DIBUJAR MANUALES
                            if subtipo == 1: # data sin cota
                                lectura = abs(detalle)
                                if superficie and superficie > nivel:
                                    distancia, estesup, nortesup = PiezometroController.ctrlCalcularDistanciaCoordenadas(este, norte, nivel, superficie, inclinacion, azimuth)
                                    profundidad = distancia + stickup
                                    if lectura > 0: # tiene agua
                                        if distancia > lectura: # sin agua y con agua
                                            depth = -lectura
                                            xsinagua, ysinagua, zsinagua = PiezometroController.ctrlCalcularCoordenadas3d(estesup, nortesup, superficie, inclinacion, azimuth, depth)
                                        else: # solo agua
                                            dibujo = 3
                                            depth = -profundidad
                                            xfondo, yfondo, zfondo = PiezometroController.ctrlCalcularCoordenadas3d(estesup, nortesup, superficie, inclinacion, azimuth, depth)
                                    else: # está seco
                                        dibujo = 2
                                        depth = -profundidad
                                        xfondo, yfondo, zfondo = PiezometroController.ctrlCalcularCoordenadas3d(estesup, nortesup, superficie, inclinacion, azimuth, depth)
                                else:
                                    dibujar = False
                                    piezoerroneos.append(nombrepiezo)
                            else: # 2 data con cota
                                lectura = detalle
                                if superficie and superficie > nivel:
                                    distancia, estesup, nortesup = PiezometroController.ctrlCalcularDistanciaCoordenadas(este, norte, nivel, superficie, inclinacion, azimuth)
                                    profundidad = distancia + stickup
                                    if lectura > nivel:
                                        if superficie > lectura:
                                            depth = superficie - lectura
                                            xsinagua, ysinagua, zsinagua = PiezometroController.ctrlCalcularCoordenadas3d(estesup, nortesup, superficie, inclinacion, azimuth, depth)
                                        else:
                                            dibujo = 2
                                            depth = superficie - nivel
                                            xfondo, yfondo, zfondo = PiezometroController.ctrlCalcularCoordenadas3d(estesup, nortesup, superficie, inclinacion, azimuth, depth)
                                    else:
                                        dibujo = 3
                                        depth = superficie - nivel
                                        xfondo, yfondo, zfondo = PiezometroController.ctrlCalcularCoordenadas3d(estesup, nortesup, superficie, inclinacion, azimuth, depth)
                                else:
                                    dibujar = False
                                    piezoerroneos.append(nombrepiezo)
                            # DIBUJAR TUBERIA DEL PIEZÓMETRO
                            if dibujo == 1: # dos tubos con y sin agua
                                if dibujar:
                                    puntosinagua = vtk.vtkPoints()
                                    puntoconagua = vtk.vtkPoints()
                                    coord_sinagua = [(estesup, nortesup, superficie), (xsinagua, ysinagua, zsinagua)]
                                    for punto in coord_sinagua:
                                        puntosinagua.InsertNextPoint(punto)
                                    coord_conagua = [(xsinagua, ysinagua, zsinagua), (este, norte, nivel)]
                                    for puntito in coord_conagua:
                                        puntoconagua.InsertNextPoint(puntito)
                                    # Agregar las líneas para cada desplazamiento
                                    lineasinagua = vtk.vtkPolyLine()
                                    lineasinagua.GetPointIds().SetNumberOfIds(len(coord_sinagua))
                                    for i in range(len(coord_sinagua)):
                                        lineasinagua.GetPointIds().SetId(i, i)
                                    lineaconagua = vtk.vtkPolyLine()
                                    lineaconagua.GetPointIds().SetNumberOfIds(len(coord_conagua))
                                    for i in range(len(coord_conagua)):
                                        lineaconagua.GetPointIds().SetId(i, i)
                                    # Crear celdas para las líneas
                                    cellsinagua = vtk.vtkCellArray()
                                    cellsinagua.InsertNextCell(lineasinagua)
                                    cellconagua = vtk.vtkCellArray()
                                    cellconagua.InsertNextCell(lineasinagua)
                                    # Crear un objeto vtkPolyData para almacenar los puntos y las líneas
                                    polydatasin = vtk.vtkPolyData()
                                    polydatasin.SetPoints(puntosinagua)
                                    polydatasin.SetLines(cellsinagua)
                                    polydatacon = vtk.vtkPolyData()
                                    polydatacon.SetPoints(puntoconagua)
                                    polydatacon.SetLines(cellconagua)
                                    # Crear un objeto vtkTubeFilter para dar grosor a las líneas
                                    tubosin = vtk.vtkTubeFilter()
                                    tubosin.SetInputData(polydatasin)
                                    tubosin.SetRadius(radiopiezo)
                                    tubosin.SetNumberOfSides(200)
                                    tubosin.SetCapping(True)
                                    tubocon = vtk.vtkTubeFilter()
                                    tubocon.SetInputData(polydatacon)
                                    tubocon.SetRadius(radiopiezo)
                                    tubocon.SetNumberOfSides(200)
                                    tubocon.SetCapping(True)
                                    # Crear un mapper para mapear los datos en geometría
                                    mappersin = vtk.vtkPolyDataMapper()
                                    mappersin.SetInputConnection(tubosin.GetOutputPort())
                                    mappercon = vtk.vtkPolyDataMapper()
                                    mappercon.SetInputConnection(tubocon.GetOutputPort())
                                    # Crear un actor para mostrar los desplazamientos
                                    actorsinagua = vtk.vtkActor()
                                    actorsinagua.SetMapper(mappersin)
                                    actorsinagua.GetProperty().SetColor(colorpiezo)
                                    actorconagua = vtk.vtkActor()
                                    actorconagua.SetMapper(mappercon)
                                    actorconagua.GetProperty().SetColor(0.0, 1.0, 1.0) # cian
                                    # Crear el texto para el punto
                                    atext = vtkVectorText()
                                    atext.SetText(str(nombrepiezo))
                                    textMapper = vtkPolyDataMapper()
                                    textMapper.SetInputConnection(atext.GetOutputPort())
                                    textMapper.SetResolveCoincidentTopologyToPolygonOffset()
                                    actorNombrePiezo = vtkFollower()
                                    actorNombrePiezo.SetMapper(textMapper)
                                    actorNombrePiezo.SetScale(tamaniotexto, tamaniotexto, tamaniotexto)
                                    actorNombrePiezo.AddPosition(estesup + 10, nortesup, superficie)
                                    actorNombrePiezo.GetProperty().SetColor(colortexto)
                                    actorNombrePiezo.SetCamera(VisorView.rendererVisor.GetActiveCamera())
                                    VisorView.rendererVisor.AddActor(actorNombrePiezo)
                                    VisorView.rendererVisor.AddActor(actorsinagua)
                                    VisorView.rendererVisor.AddActor(actorconagua)
                                    # creamos la tupla de prismas
                                    VisorView.piezometrostubosmanual.append(("DOS", idcomponente, idpiezo, actorNombrePiezo, actorsinagua, actorconagua)) # tipo, label, tubos
                            else: # un tubo
                                if dibujo == 2:
                                    color = (0.0, 1.0, 1.0) # cian
                                else:
                                    color = colorpiezo
                                if dibujar:
                                    puntoconagua = vtk.vtkPoints()
                                    coord_conagua = [(estesup, nortesup, superficie), (xfondo, yfondo, zfondo)]
                                    for puntito in coord_conagua:
                                        puntoconagua.InsertNextPoint(puntito)
                                    # Agregar las línea entre los dos puntos
                                    lineaconagua = vtk.vtkPolyLine()
                                    lineaconagua.GetPointIds().SetNumberOfIds(len(coord_conagua))
                                    for i in range(len(coord_conagua)):
                                        lineaconagua.GetPointIds().SetId(i, i)
                                    # Crear celdas para las línea
                                    cellconagua = vtk.vtkCellArray()
                                    cellconagua.InsertNextCell(lineaconagua)
                                    # Crear un objeto vtkPolyData para almacenar los puntos y la línea
                                    polydatacon = vtk.vtkPolyData()
                                    polydatacon.SetPoints(puntoconagua)
                                    polydatacon.SetLines(cellconagua)
                                    # Crear un objeto vtkTubeFilter para dar grosor a la línea
                                    tubocon = vtk.vtkTubeFilter()
                                    tubocon.SetInputData(polydatacon)
                                    tubocon.SetRadius(radiopiezo)
                                    tubocon.SetNumberOfSides(200)
                                    tubocon.SetCapping(True)
                                    # Crear un mapper para mapear los datos en geometría
                                    mappercon = vtk.vtkPolyDataMapper()
                                    mappercon.SetInputConnection(tubocon.GetOutputPort())
                                    # Crear un actor para mostrar el desplazamiento
                                    actorconagua = vtk.vtkActor()
                                    actorconagua.SetMapper(mappercon)
                                    actorconagua.GetProperty().SetColor(color)
                                    # Crear el texto para el punto
                                    atext = vtkVectorText()
                                    atext.SetText(str(nombrepiezo))
                                    textMapper = vtkPolyDataMapper()
                                    textMapper.SetInputConnection(atext.GetOutputPort())
                                    textMapper.SetResolveCoincidentTopologyToPolygonOffset()                                    
                                    actorNombrePiezo = vtkFollower()
                                    actorNombrePiezo.SetMapper(textMapper)
                                    actorNombrePiezo.SetScale(tamaniotexto, tamaniotexto, tamaniotexto)
                                    actorNombrePiezo.AddPosition(estesup + 10, nortesup, superficie)
                                    actorNombrePiezo.GetProperty().SetColor(colortexto)
                                    actorNombrePiezo.SetCamera(VisorView.rendererVisor.GetActiveCamera())
                                    # agregar al visor
                                    VisorView.rendererVisor.AddActor(actorNombrePiezo)
                                    VisorView.rendererVisor.AddActor(actorconagua)
                                    # creamos la tupla de prismas
                                    VisorView.piezometrostubosmanual.append(("UNO", idcomponente, idpiezo, actorNombrePiezo, actorconagua)) # tipo, label, tubo
                        else:
                            dibujar = False
                            piezoerroneos.append(nombrepiezo)
                # validar si no hay piezometros
                if VisorView.resetvisor is False:
                    camera = VisorView.rendererVisor.GetActiveCamera()
                    VisorView.rendererVisor.ResetCamera()
                    camera.Zoom(1.5)
                VisorView.vtkWidgetVisor.GetRenderWindow().Render()
                if len(piezoerroneos) > 0:
                    mostrar_mensaje("ERROR AL MOSTRAR PIEZÓMETRO", f"Hubo error con los siguientes piezómetros:\n {piezoerroneos}", "advertencia")
    
    def limpiarPiezometrosCuerdaVisor():
        if len(VisorView.piezometrostuboscuerda) > 0:
            for tupla in VisorView.piezometrostuboscuerda:
                VisorView.rendererVisor.RemoveActor(tupla[3])
                VisorView.rendererVisor.RemoveActor(tupla[4])
                if tupla[0] == "DOS":
                    VisorView.rendererVisor.RemoveActor(tupla[5])
            VisorView.piezometrostuboscuerda.clear()
            VisorView.vtkWidgetVisor.GetRenderWindow().Render()
        
    def limpiarPiezometrosManualVisor():
        if len(VisorView.piezometrostubosmanual) > 0:
            for tupla in VisorView.piezometrostubosmanual:
                VisorView.rendererVisor.RemoveActor(tupla[3])
                VisorView.rendererVisor.RemoveActor(tupla[4])
                if tupla[0] == "DOS":
                    VisorView.rendererVisor.RemoveActor(tupla[5])
            VisorView.piezometrostubosmanual.clear()
            VisorView.vtkWidgetVisor.GetRenderWindow().Render()
    
    def mostrarPluviometrosVisor(paginacion, pluviomarcados):
        if paginacion.currentIndex() == 0:
            VisorView.limpiarPluviometrosVisor()
            listapluviometros = PluviometroController.ctrlListarPluviometrosProyecto(VisorView.idproyecto, pluviomarcados)
            # crear y mostrar actores dxf
            if len(listapluviometros) > 0:
                respuesta = ConfiguracionVisor.obtenerDataConfiguracionVisor()
                tamaniotexto, radiopluvio = respuesta[1], respuesta[9]
                colorpluvio = MetodosGenerales.convertirHexadecimalRGB(respuesta[10])
                colortexto = MetodosGenerales.convertirHexadecimalRGB(respuesta[2])
                for info in listapluviometros:
                    idpluviometro = info[0]
                    nombrepluvio = info[1]
                    idcomponen = info[2]
                    estepluvio = float(info[3])
                    nortepluvio = float(info[4])
                    nivelpluvio = float(info[5])
                    # Crear el texto para el equipo
                    atext = vtkVectorText()
                    atext.SetText(nombrepluvio)
                    textMapper = vtkPolyDataMapper()
                    textMapper.SetInputConnection(atext.GetOutputPort())
                    textMapper.SetResolveCoincidentTopologyToPolygonOffset()                                    
                    nombreActor = vtkFollower()
                    nombreActor.SetMapper(textMapper)
                    nombreActor.SetScale(tamaniotexto, tamaniotexto, tamaniotexto)
                    nombreActor.AddPosition(estepluvio + 10, nortepluvio, nivelpluvio)
                    nombreActor.GetProperty().SetColor(colortexto)
                    nombreActor.SetCamera(VisorView.rendererVisor.GetActiveCamera())
                    VisorView.rendererVisor.AddActor(nombreActor)
                    # Crear cono
                    coneSource = vtk.vtkConeSource()
                    coneSource.SetCenter(estepluvio, nortepluvio, nivelpluvio)
                    coneSource.SetDirection(0, 0, -1)
                    coneSource.SetRadius(radiopluvio)
                    coneSource.SetHeight(radiopluvio * 2)
                    coneSource.SetResolution(200)
                    # Crear mapeador
                    coneMapper = vtk.vtkPolyDataMapper()
                    coneMapper.SetInputConnection(coneSource.GetOutputPort())
                    # Crear actor
                    coneActor = vtk.vtkActor()
                    coneActor.SetMapper(coneMapper)
                    coneActor.GetProperty().SetColor(colorpluvio)
                    # agregar al visor
                    VisorView.rendererVisor.AddActor(coneActor)
                    VisorView.listaactorespluvio.append((idcomponen, idpluviometro, coneActor, nombreActor))
                # validar si no hay pluviometros
                if VisorView.resetvisor is False:
                    camera = VisorView.rendererVisor.GetActiveCamera()
                    VisorView.rendererVisor.ResetCamera()
                    camera.Zoom(1.5)
                VisorView.vtkWidgetVisor.GetRenderWindow().Render()
        
    def limpiarPluviometrosVisor():
        if len(VisorView.listaactorespluvio) > 0:
            for tupla in VisorView.listaactorespluvio:
                VisorView.rendererVisor.RemoveActor(tupla[2])
                VisorView.rendererVisor.RemoveActor(tupla[3])
            VisorView.listaactorespluvio.clear()
            VisorView.vtkWidgetVisor.GetRenderWindow().Render()
    
    def mostrarCeldasAsentamientoVisor(paginacion, celdasmarcadas):
        if paginacion.currentIndex() == 0:
            VisorView.limpiarCeldasAsentamientoVisor()
            listaceldas = CeldaController.ctrlListarCeldasProyecto(VisorView.idproyecto, celdasmarcadas)
            # crear y mostrar actores dxf
            if len(listaceldas) > 0:
                respuesta = ConfiguracionVisor.obtenerDataConfiguracionVisor()
                tamaniotexto, radiocelda = respuesta[1], respuesta[11]
                colorcelda = MetodosGenerales.convertirHexadecimalRGB(respuesta[12])
                colortexto = MetodosGenerales.convertirHexadecimalRGB(respuesta[2])
                for info in listaceldas:
                    idcelda = info[0]
                    nombrecelda = info[1]
                    idcomponen = info[2]
                    estecelda = float(info[3])
                    nortecelda = float(info[4])
                    nivelcelda = float(info[5])
                    # Crear el texto para el equipo
                    atext = vtkVectorText()
                    atext.SetText(nombrecelda)
                    textMapper = vtkPolyDataMapper()
                    textMapper.SetInputConnection(atext.GetOutputPort())
                    textMapper.SetResolveCoincidentTopologyToPolygonOffset()                                    
                    nombreActor = vtkFollower()
                    nombreActor.SetMapper(textMapper)
                    nombreActor.SetScale(tamaniotexto, tamaniotexto, tamaniotexto)
                    nombreActor.AddPosition(estecelda + 10, nortecelda, nivelcelda)
                    nombreActor.GetProperty().SetColor(colortexto)
                    nombreActor.SetCamera(VisorView.rendererVisor.GetActiveCamera())
                    VisorView.rendererVisor.AddActor(nombreActor)
                    # Crear el cubo
                    cube_source = vtk.vtkCubeSource()
                    cube_source.SetXLength(radiocelda)  # Longitud en el eje X
                    cube_source.SetYLength(radiocelda * 0.8)  # Longitud en el eje Y
                    cube_source.SetZLength(radiocelda * 0.6)  # Longitud en el eje Z
                    # Crear una transformación para posicionar el cubo
                    transform = vtk.vtkTransform()
                    transform.Translate(estecelda, nortecelda, nivelcelda)
                    # Crear un filtro de transformación
                    transform_filter = vtk.vtkTransformPolyDataFilter()
                    transform_filter.SetInputConnection(cube_source.GetOutputPort())
                    transform_filter.SetTransform(transform)
                    # Crear un mapper para conectar los datos del cubo con el actor
                    cube_mapper = vtk.vtkPolyDataMapper()
                    cube_mapper.SetInputConnection(transform_filter.GetOutputPort())
                    # Crear el actor del cubo
                    cube_actor = vtk.vtkActor()
                    cube_actor.SetMapper(cube_mapper)
                    cube_actor.GetProperty().SetColor(colorcelda)
                    # agregar al visor
                    VisorView.rendererVisor.AddActor(cube_actor)
                    VisorView.listaactoresceldas.append((idcomponen, idcelda, cube_actor, nombreActor, cube_source))
                # validar si no hay celdas
                if VisorView.resetvisor is False:
                    camera = VisorView.rendererVisor.GetActiveCamera()
                    VisorView.rendererVisor.ResetCamera()
                    camera.Zoom(1.5)
                VisorView.vtkWidgetVisor.GetRenderWindow().Render()
        
    def limpiarCeldasAsentamientoVisor():
        if len(VisorView.listaactoresceldas) > 0:
            for tupla in VisorView.listaactoresceldas:
                VisorView.rendererVisor.RemoveActor(tupla[2])
                VisorView.rendererVisor.RemoveActor(tupla[3])
            VisorView.listaactoresceldas.clear()
            VisorView.vtkWidgetVisor.GetRenderWindow().Render()
    
    def mostrarAcelerografosVisor(paginacion, aceleromarcados):
        if paginacion.currentIndex() == 0:
            VisorView.limpiarAcelerografosVisor()
            listaaceleros = AcelerografoController.ctrlListarAcelerografosProyecto(VisorView.idproyecto, aceleromarcados)
            # crear y mostrar actores dxf
            if len(listaaceleros) > 0:
                respuesta = ConfiguracionVisor.obtenerDataConfiguracionVisor()
                tamaniotexto, radioacelero = respuesta[1], respuesta[13]
                coloracelero = MetodosGenerales.convertirHexadecimalRGB(respuesta[14])
                colortexto = MetodosGenerales.convertirHexadecimalRGB(respuesta[2])
                for info in listaaceleros:
                    idacelero = info[0]
                    nombreacelero = info[1]
                    idcomponen = info[2]
                    esteacelero = float(info[3])
                    norteacelero = float(info[4])
                    nivelacelero = float(info[5])
                    # Crear el texto para el equipo
                    atext = vtkVectorText()
                    atext.SetText(nombreacelero)
                    textMapper = vtkPolyDataMapper()
                    textMapper.SetInputConnection(atext.GetOutputPort())
                    textMapper.SetResolveCoincidentTopologyToPolygonOffset()                                    
                    nombreActor = vtkFollower()
                    nombreActor.SetMapper(textMapper)
                    nombreActor.SetScale(tamaniotexto, tamaniotexto, tamaniotexto)
                    nombreActor.AddPosition(esteacelero + 10, norteacelero, nivelacelero)
                    nombreActor.GetProperty().SetColor(colortexto)
                    nombreActor.SetCamera(VisorView.rendererVisor.GetActiveCamera())
                    VisorView.rendererVisor.AddActor(nombreActor)
                    # Crear el poliedro
                    cylinder_source = vtk.vtkCylinderSource()
                    cylinder_source.SetHeight(radioacelero)       # Altura del cilindro
                    cylinder_source.SetRadius(radioacelero / 2)       # Radio del cilindro
                    cylinder_source.SetResolution(6)     # 6 lados para el cilindro
                    cylinder_source.SetCapping(1)
                    # Crear un mapper
                    cylinder_mapper = vtk.vtkPolyDataMapper()
                    cylinder_mapper.SetInputConnection(cylinder_source.GetOutputPort())
                    # Crear el actor del cilindro
                    cylinder_actor = vtk.vtkActor()
                    cylinder_actor.SetMapper(cylinder_mapper)
                    cylinder_actor.GetProperty().SetColor(coloracelero)
                    # Transformación para rotar y posicionar el cilindro
                    cylinder_actor.SetPosition(esteacelero, norteacelero, nivelacelero)
                    cylinder_actor.RotateX(90)
                    # agregar al visor
                    VisorView.rendererVisor.AddActor(cylinder_actor)
                    VisorView.listaactoresacelero.append((idcomponen, idacelero, cylinder_actor, nombreActor))
                # validar si no hay acelerografos
                if VisorView.resetvisor is False:
                    camera = VisorView.rendererVisor.GetActiveCamera()
                    VisorView.rendererVisor.ResetCamera()
                    camera.Zoom(1.5)
                VisorView.vtkWidgetVisor.GetRenderWindow().Render()
        
    def limpiarAcelerografosVisor():
        if len(VisorView.listaactoresacelero) > 0:
            for tupla in VisorView.listaactoresacelero:
                VisorView.rendererVisor.RemoveActor(tupla[2])
                VisorView.rendererVisor.RemoveActor(tupla[3])
            VisorView.listaactoresacelero.clear()
            VisorView.vtkWidgetVisor.GetRenderWindow().Render()
    
    def mostrarSondajestdrVisor(paginacion, sondajesmarcados):
        if paginacion.currentIndex() == 0:
            VisorView.limpiarSondajestdrVisor()
            listasondajes = TDRController.ctrlListarSondajestdrProyecto(VisorView.idproyecto, sondajesmarcados)
            if len(listasondajes) > 0:
                respuesta = ConfiguracionVisor.obtenerDataConfiguracionVisor()
                tamaniotexto, radiotdr = respuesta[1], respuesta[15]
                colortdr = MetodosGenerales.convertirHexadecimalRGB(respuesta[16])
                colortexto = MetodosGenerales.convertirHexadecimalRGB(respuesta[2])
                for info in listasondajes:
                    idcompo, idsondaje, nombrecable = info[0], info[1], info[3]
                    estecable, nortecable, nivelcable = info[4], info[5], info[6]
                    profundo, inclinacion, azimuth = info[7], info[8], info[9]
                    profundidad = -1 * float(profundo)
                    azimut = 270 - float(azimuth)
                    # Crear el texto para el cable
                    atext = vtkVectorText()
                    atext.SetText(nombrecable)
                    textMapper = vtkPolyDataMapper()
                    textMapper.SetInputConnection(atext.GetOutputPort())
                    textMapper.SetResolveCoincidentTopologyToPolygonOffset()                                    
                    nombreActor = vtkFollower()
                    nombreActor.SetMapper(textMapper)
                    nombreActor.SetScale(tamaniotexto, tamaniotexto, tamaniotexto)
                    nombreActor.AddPosition(estecable + 10, nortecable, nivelcable)
                    nombreActor.GetProperty().SetColor(colortexto)
                    nombreActor.SetCamera(VisorView.rendererVisor.GetActiveCamera())
                    VisorView.rendererVisor.AddActor(nombreActor)
                    # calcular coordenadas finales (fondo)
                    xfondo, yfondo, zfondo = PiezometroController.ctrlCalcularCoordenadas3d(estecable, nortecable, nivelcable, inclinacion, azimut, profundidad)
                    # Crear un assembly para agrupar los actores
                    cableactor = vtk.vtkAssembly()
                    # Crear un objeto de línea
                    line = vtk.vtkLineSource()
                    line.SetPoint1(estecable, nortecable, nivelcable)
                    line.SetPoint2(xfondo, yfondo, zfondo)
                    # Crear un actor para la línea
                    line_mapper = vtk.vtkPolyDataMapper()
                    line_mapper.SetInputConnection(line.GetOutputPort())
                    line_actor = vtk.vtkActor()
                    line_actor.SetMapper(line_mapper)
                    line_actor.GetProperty().SetLineWidth(3)
                    line_actor.GetProperty().SetColor(colortdr)
                    cableactor.AddPart(line_actor)
                    # Crear un actor para las esferas
                    sphere_source = vtk.vtkSphereSource()
                    sphere_source.SetRadius(radiotdr)
                    sphere_mapper = vtk.vtkPolyDataMapper()
                    sphere_mapper.SetInputConnection(sphere_source.GetOutputPort())
                    # Punto inicial
                    sphere_actor_inicial = vtk.vtkActor()
                    sphere_actor_inicial.SetMapper(sphere_mapper)
                    sphere_actor_inicial.GetProperty().SetColor(colortdr)
                    sphere_actor_inicial.SetPosition(estecable, nortecable, nivelcable)
                    cableactor.AddPart(sphere_actor_inicial)
                    # Punto final
                    sphere_actor_final = vtk.vtkActor()
                    sphere_actor_final.SetMapper(sphere_mapper)
                    sphere_actor_final.GetProperty().SetColor(colortdr)
                    sphere_actor_final.SetPosition(xfondo, yfondo, zfondo)
                    cableactor.AddPart(sphere_actor_final)
                    # Agregar puntos a lo largo de la línea
                    puntostdr = TDRController.ctrlMostrarLecturasSondajeTDR(idsondaje)
                    if puntostdr:
                        for dato in puntostdr:
                            punto = -1 * abs(float(dato[3]))
                            if punto > profundidad:
                                color = MetodosGenerales.convertirHexadecimalRGB(dato[4])
                                # Calcular las coordenadas de los puntos objetivo
                                xpunto, ypunto, zpunto = PiezometroController.ctrlCalcularCoordenadas3d(estecable, nortecable, nivelcable, inclinacion, azimut, punto)
                                sphere_actor = vtk.vtkActor()
                                sphere_actor.SetMapper(sphere_mapper)
                                sphere_actor.GetProperty().SetColor(color)
                                sphere_actor.SetPosition(xpunto, ypunto, zpunto)
                                cableactor.AddPart(sphere_actor)
                    # agregar al visor
                    VisorView.rendererVisor.AddActor(cableactor)
                    VisorView.cablescoaxiales.append((idcompo, idsondaje, cableactor, nombreActor))
                # validar si no hay tdr
                if VisorView.resetvisor is False:
                    camera = VisorView.rendererVisor.GetActiveCamera()
                    VisorView.rendererVisor.ResetCamera()
                    camera.Zoom(1.5)
                VisorView.vtkWidgetVisor.GetRenderWindow().Render()
    
    def limpiarSondajestdrVisor():
        if len(VisorView.cablescoaxiales) > 0:
            for tupla in VisorView.cablescoaxiales:
                VisorView.rendererVisor.RemoveActor(tupla[2])
                VisorView.rendererVisor.RemoveActor(tupla[3])
            VisorView.cablescoaxiales.clear()
            VisorView.vtkWidgetVisor.GetRenderWindow().Render()
    
    def mostrarEquiposAdicionalesVisor(paginacion, equiposmarcados):
        if paginacion.currentIndex() == 0:
            VisorView.limpiarEquiposAdicionalesVisor()
            listaequipos = EquipoController.ctrlListarAdicionalesProyecto(VisorView.idproyecto, equiposmarcados)
            if len(listaequipos) > 0:
                for info in listaequipos:
                    idcompo, idequipo, nombreequipo = info[0], info[1], info[3]
                    esteequipo, norteequipo, nivelequipo = info[5], info[6], info[7]
                    figura, color, tamanio = info[8], info[9], info[10]
                    # Crear actores                          
                    nombreactor, equipoactor = VisorView.crearActorEquipo(nombreequipo, esteequipo, norteequipo, nivelequipo, figura, color, tamanio)
                    if equipoactor:
                        VisorView.equiposgenerales.append((idcompo, idequipo, nombreactor, equipoactor))
                        # agregar al visor
                        VisorView.rendererVisor.AddActor(nombreactor)
                        VisorView.rendererVisor.AddActor(equipoactor)
                # validar si no hay equipos
                if VisorView.resetvisor is False:
                    camera = VisorView.rendererVisor.GetActiveCamera()
                    VisorView.rendererVisor.ResetCamera()
                    camera.Zoom(1.5)
                VisorView.vtkWidgetVisor.GetRenderWindow().Render()
    
    def crearActorEquipo(eqnombre, este, norte, nivel, eqfigura, eqcolor, eqsize):
        respuesta = ConfiguracionVisor.obtenerDataConfiguracionVisor()
        tamaniotexto = respuesta[1]
        colortexto = MetodosGenerales.convertirHexadecimalRGB(respuesta[2])
        actor = None
        # Crear el texto para el equipo
        atext = vtkVectorText()
        atext.SetText(eqnombre)
        textMapper = vtkPolyDataMapper()
        textMapper.SetInputConnection(atext.GetOutputPort())
        textMapper.SetResolveCoincidentTopologyToPolygonOffset()                                    
        nombreActor = vtkFollower()
        nombreActor.SetMapper(textMapper)
        nombreActor.SetScale(tamaniotexto, tamaniotexto, tamaniotexto)
        nombreActor.AddPosition(este + 10, norte, nivel)
        nombreActor.GetProperty().SetColor(colortexto)
        nombreActor.SetCamera(VisorView.rendererVisor.GetActiveCamera())
        # obtener color
        colorfigura = MetodosGenerales.convertirHexadecimalRGB(eqcolor)
        if eqfigura == "Esfera":
            # Crear esfera
            sphereSource = vtk.vtkSphereSource()
            sphereSource.SetCenter(este, norte, nivel)
            sphereSource.SetRadius(eqsize)
            # Crear mapeador
            sphereMapper = vtk.vtkPolyDataMapper()
            sphereMapper.SetInputConnection(sphereSource.GetOutputPort())
            # Crear actor
            sphereActor = vtk.vtkActor()
            sphereActor.SetMapper(sphereMapper)
            sphereActor.GetProperty().SetColor(colorfigura)
            actor = sphereActor
        elif eqfigura == "Cilindro":
            # Crear el objeto vtkLineSource
            lineaSource = vtk.vtkLineSource()
            lineaSource.SetPoint1(este, norte, nivel)
            lineaSource.SetPoint2(este, norte, nivel + (eqsize * 2 ))
            # Crear un objeto vtkTubeFilter para dar grosor a la línea
            cylinder = vtk.vtkTubeFilter()
            cylinder.SetInputConnection(lineaSource.GetOutputPort())
            cylinder.SetRadius(eqsize)
            cylinder.SetNumberOfSides(200)
            cylinder.SetCapping(True)
            # Crear un mapper para mapear los datos en geometría
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(cylinder.GetOutputPort())
            # Crear un actor para mostrar el cilindro
            cylinderActor = vtk.vtkActor()
            cylinderActor.SetMapper(mapper)
            cylinderActor.GetProperty().SetColor(colorfigura)
            actor = cylinderActor
        elif eqfigura == "Cono":
            # Crear cono
            coneSource = vtk.vtkConeSource()
            coneSource.SetCenter(este, norte, nivel)
            coneSource.SetDirection(0, 0, 1)
            coneSource.SetRadius(eqsize)
            coneSource.SetHeight(eqsize * 2)
            coneSource.SetResolution(200)
            # Crear mapeador
            coneMapper = vtk.vtkPolyDataMapper()
            coneMapper.SetInputConnection(coneSource.GetOutputPort())
            # Crear actor
            coneActor = vtk.vtkActor()
            coneActor.SetMapper(coneMapper)
            coneActor.GetProperty().SetColor(colorfigura)
            actor = coneActor
        elif eqfigura == "Cubo":
            # Crear un cubo
            cubeSource = vtk.vtkCubeSource()
            cubeSource.SetCenter(este, norte, nivel)
            cubeSource.SetXLength(eqsize)
            cubeSource.SetYLength(eqsize)
            cubeSource.SetZLength(eqsize)
            # Crear mapeador
            cubeMapper = vtk.vtkPolyDataMapper()
            cubeMapper.SetInputConnection(cubeSource.GetOutputPort())
            # Crear actor
            cubeActor = vtk.vtkActor()
            cubeActor.SetMapper(cubeMapper)
            cubeActor.GetProperty().SetColor(colorfigura)
            actor = cubeActor
        return nombreActor, actor
    
    def limpiarEquiposAdicionalesVisor():
        if len(VisorView.equiposgenerales) > 0:
            for tupla in VisorView.equiposgenerales:
                VisorView.rendererVisor.RemoveActor(tupla[2])
                VisorView.rendererVisor.RemoveActor(tupla[3])
            VisorView.equiposgenerales.clear()
            VisorView.vtkWidgetVisor.GetRenderWindow().Render()
            
    def mostrarPrismasVirtualesVisor(paginacion, prismasvirtuales):
        if paginacion.currentIndex() == 0:
            VisorView.limpiarPrismasVirtualesVisor()
            listaprismasvirtuales = PrismasVirtualesController.ctrlPrismasVirtualesProyecto(VisorView.idproyecto, prismasvirtuales)
            if len(listaprismasvirtuales) > 0:
                for info in listaprismasvirtuales:
                    idcompo, idequipo, nombreequipo = info[0], info[1], info[2]
                    esteequipo, norteequipo, nivelequipo = info[3], info[4], info[5]                    
                    radio, color = info[6], VisorView.convert_color(info[7])
                    # Crear actores
                    respuesta,actor_esfera,actor_texto=VisorView.crear_prisma_virtual(esteequipo,norteequipo,nivelequipo,nombreequipo,radio, color)        
                    if respuesta:
                        VisorView.prismasvirtualesgraficados.append((idcompo, idequipo, actor_texto, actor_esfera))
                        # agregar al visor
                        VisorView.rendererVisor.AddActor(actor_esfera)
                        VisorView.rendererVisor.AddActor(actor_texto)
                # validar si no hay prismas virtuales
                if VisorView.resetvisor is False:
                    camera = VisorView.rendererVisor.GetActiveCamera()
                    VisorView.rendererVisor.ResetCamera()
                    camera.Zoom(1.5)
                VisorView.vtkWidgetVisor.GetRenderWindow().Render()
    
    def limpiarPrismasVirtualesVisor():
        if len(VisorView.prismasvirtualesgraficados) > 0:
            for tupla in VisorView.prismasvirtualesgraficados:
                VisorView.rendererVisor.RemoveActor(tupla[2])
                VisorView.rendererVisor.RemoveActor(tupla[3])
            VisorView.prismasvirtualesgraficados.clear()
            VisorView.vtkWidgetVisor.GetRenderWindow().Render()
            
    def mostrarEscalaInclinometros(tree_actual, paginacion):
        lista = EquiposVisor.obtener_todos_elementos_marcados(tree_actual)
        if lista:
            inclinometrosmarcados = VisorView.obtenerListaEquiposMarcados(lista, "Inclinómetros")
            if len(inclinometrosmarcados) > 0:
                respuesta, escala = UmbralView.dialogoEscalaInclinometros(VisorView.escalainclinometro)
                if respuesta:
                    VisorView.escalainclinometro = escala
                    VisorView.dibujarLineaIncli = 0
                    VisorView.mostrarInclinometrosVisor(paginacion, VisorView.escalainclinometro, inclinometrosmarcados)
        else:
            mostrar_mensaje("SIN INCLINÓMETROS", "Debe marcar los inclinómetros.", "advertencia")
    
    def aplicarDTMtopografia(tree_actual, paginacion):
        if len(VisorView.listatopograficados) > 0:
            lista = EquiposVisor.obtener_todos_elementos_marcados(tree_actual)
            if lista:
                toposmarcados = VisorView.obtenerListaEquiposMarcados(lista, "Topografías")
                if len(toposmarcados) > 0:
                    if paginacion.currentIndex() == 0:
                        VisorView.configurarRenderizado(toposmarcados)
                    elif paginacion.currentIndex() == 1:
                        VisorView.renderizarGrafico_corte()
    
    def configurarRenderizado(topografiamarcados):
        estad, respuesta = ConfigurarDTM.dialogConfiguracion(topografiamarcados, VisorView.cambioproyecto)
        if estad:
            toposPorRenderizar = [(idcomponente, idtopo, color, ruta) for (idcomponente, idtopo, estado, color, nombre, ruta) in respuesta if estado == 1]
            VisorView.listaDTMactivos = {f"{idcomponen}_{codtopito}_{rutita}": colorcito for idcomponen, codtopito, colorcito, rutita in toposPorRenderizar}
            lista_filtrada = [(componenteid, topoid, tipo, actor, rutactor, VisorView.listaDTMactivos[f"{componenteid}_{topoid}_{rutactor}"]) for componenteid, topoid, tipo, actor, rutactor in VisorView.listatopograficados if f"{componenteid}_{topoid}_{rutactor}" in VisorView.listaDTMactivos]
            topos_marcadas = {f"{compon[1]}_{topo[2]}_{rutaactor}" for compon, listatopos in topografiamarcados for topo, elemen in listatopos.items() for nameactor, idtactor, rutaactor in elemen}
            # Iniciar Hilo
            loading = LoadingView.mostrarLoading()
            def on_thread_complete():
                loading.close()
            dtmvisor3d = GenerarDTMThread(lista_filtrada, topos_marcadas, VisorView.listaDTMactivos)
            dtmvisor3d.task_finishGenerardtm.connect(on_thread_complete)
            dtmvisor3d.start()
            loading.exec()
            # mostrar visor
            VisorView.cambioproyecto = False
            VisorView.vtkWidgetVisor.GetRenderWindow().Render()
    
    def solidificarActoresDXF(lista_filtrada, topos_marcadas, toposRenderizadas_dict):
        if len(lista_filtrada) > 0:
            for tupla in lista_filtrada:
                if not any(elemento[0] == tupla[0] and elemento[1] == tupla[1] and elemento[4] == tupla[4] for elemento in VisorView.toposDTM):
                    tipoelem = tupla[2]
                    elementoGraficar = tupla[3]
                    rutaactor = tupla[4]
                    colorGraficar = tupla[5]
                    solido = VisorView.renderizarGrafico(elementoGraficar)
                    if solido is not None:
                        VisorView.toposDTM.append((tupla[0], tupla[1], solido, colorGraficar, rutaactor))
            # Mostrar u ocultar dtm en base a condiciones
            for idcompon, idtopo, actor_dtm, color_dtm, rutita in VisorView.toposDTM:
                if f"{idcompon}_{idtopo}_{rutita}" in toposRenderizadas_dict:
                    color_rgb = MetodosGenerales.convertirHexadecimalRGB(str(toposRenderizadas_dict[f"{idcompon}_{idtopo}_{rutita}"]))
                    actor_dtm.GetProperty().SetColor(color_rgb)
                    if f"{idcompon}_{idtopo}_{rutita}" in topos_marcadas:
                        actor_dtm.SetVisibility(True)
                else:
                    actor_dtm.SetVisibility(False)
            # ocultar topos     
            for componenteid, topoid, tipotopo, actor, rutiactor in VisorView.listatopograficados:
                if f"{componenteid}_{topoid}_{rutiactor}" in topos_marcadas:
                    if f"{componenteid}_{topoid}_{rutiactor}" in toposRenderizadas_dict:
                        actor.SetVisibility(False)
                    else:
                        actor.SetVisibility(True)                         
                else:
                    actor.SetVisibility(False)
        else:
            for componid, codtopo, actor, color_dtm, rutitactor in VisorView.toposDTM:
                actor.SetVisibility(False)
            for componenteid, topoid, tipotopo, actorcito, rutactor in VisorView.listatopograficados:
                if f"{componenteid}_{topoid}_{rutactor}" in topos_marcadas:
                    actorcito.SetVisibility(True)
                else:
                    actorcito.SetVisibility(False)
    
    def solidificarGraficaCorte(appendFilter, limites):
        # Extraer puntos del appendFilter
        puntos = np.array([appendFilter.GetOutput().GetPoint(i) for i in range(appendFilter.GetOutput().GetNumberOfPoints())])
        # Triangulación utilizando scipy.spatial.Delaunay
        triangulacion = Delaunay(puntos[:, :2])
        caras = triangulacion.simplices
        puntos_vtk = vtk.vtkPoints()
        for punto in puntos:
            puntos_vtk.InsertNextPoint(punto)
        triangulos = vtk.vtkCellArray()
        for cara in caras:
            triangulo = vtk.vtkTriangle()
            triangulo.GetPointIds().SetId(0, cara[0])
            triangulo.GetPointIds().SetId(1, cara[1])
            triangulo.GetPointIds().SetId(2, cara[2])
            triangulos.InsertNextCell(triangulo)
                
        polydata_triangulada = vtk.vtkPolyData()
        polydata_triangulada.SetPoints(puntos_vtk)
        polydata_triangulada.SetPolys(triangulos)

        clipper_corte = vtk.vtkClipPolyData()
        clipper_corte.SetInputData(polydata_triangulada)
        clipper_corte.SetClipFunction(limites)
        clipper_corte.InsideOutOn()
        clipper_corte.Update()

        extrusion_corte = vtk.vtkLinearExtrusionFilter()
        extrusion_corte.SetInputConnection(clipper_corte.GetOutputPort())
        extrusion_corte.SetExtrusionTypeToNormalExtrusion()
        extrusion_corte.SetVector(0, 0, 1)
        extrusion_corte.SetScaleFactor(10)

        solid_mapper_corte = vtk.vtkPolyDataMapper()
        solid_mapper_corte.SetInputConnection(extrusion_corte.GetOutputPort())

        VisorView.solidoDXF_corte = vtk.vtkActor()
        VisorView.solidoDXF_corte.SetMapper(solid_mapper_corte)
        VisorView.solidoDXF_corte.GetProperty().SetColor(0.95, 0.9, 0.7)
        # Agregar el nuevo actor a la escena
        VisorView.rendererCorte.AddActor(VisorView.solidoDXF_corte)
        for actor in VisorView.lista_actoresDXF_corte:
            actor.VisibilityOff()
    
    def renderizarGrafico(elementoGraficar):
        try:
            actoresUnidos = VisorView.convertirYUnirActores(elementoGraficar)
            # Triangulación de Delaunay
            puntos = np.array([[actoresUnidos.GetPoint(i) for i in range(actoresUnidos.GetNumberOfPoints())]])
            puntos = puntos.squeeze()
            triangulacion = Delaunay(puntos[:, :2])
            caras = triangulacion.simplices
            puntos_vtk = vtk.vtkPoints()
            for punto in puntos:
                puntos_vtk.InsertNextPoint(punto)
            triangulos = vtk.vtkCellArray()
            for cara in caras:
                triangulo = vtk.vtkTriangle()
                triangulo.GetPointIds().SetId(0, cara[0])
                triangulo.GetPointIds().SetId(1, cara[1])
                triangulo.GetPointIds().SetId(2, cara[2])
                triangulos.InsertNextCell(triangulo)  
            polydata_triangulada = vtk.vtkPolyData()
            polydata_triangulada.SetPoints(puntos_vtk)
            polydata_triangulada.SetPolys(triangulos)
            # Crear un filtro de extrusión
            extrusion_filter = vtk.vtkLinearExtrusionFilter()
            extrusion_filter.SetInputData(polydata_triangulada)
            extrusion_filter.SetExtrusionTypeToNormalExtrusion()
            extrusion_filter.SetVector(0, 0, 1)  # Extrusión en dirección Z
            extrusion_filter.SetScaleFactor(10)  # Grosor de la extrusión
            triangulacion_mapper = vtk.vtkPolyDataMapper()
            triangulacion_mapper.SetInputConnection(extrusion_filter.GetOutputPort())
            triangulacion_actor = vtk.vtkActor()
            triangulacion_actor.SetMapper(triangulacion_mapper)
            # Habilitar blending en el renderizador
            # rendererVisor.SetUseDepthPeeling(True)
            # rendererVisor.SetMaximumNumberOfPeels(100)
            # rendererVisor.SetOcclusionRatio(0.01)
            # Habilitar sombras
            # rendererVisor.SetUseShadows(True)
            VisorView.rendererVisor.AddActor(triangulacion_actor)
            return triangulacion_actor
        except Exception as e:
            return None
    
    def convertirYUnirActores(elemento):
        polydata_combined = vtk.vtkAppendPolyData()
        try:
            mapper = elemento.GetMapper()
            input_polydata = mapper.GetInput()
            if isinstance(input_polydata, vtk.vtkPolyData):
                polydata_combined.AddInputData(input_polydata)
        except Exception as e:
            print(f"Error al procesar actor {elemento}: {e}")
        polydata_combined.Update()
        return polydata_combined.GetOutput()
    
    def renderizarGrafico_corte():
        if VisorView.polyDataCorte is not None:
            appendFilter = vtk.vtkAppendPolyData()
            for tupla in VisorView.polyDataCorte:
                polydata = tupla[0]
                limites = tupla[1]
                appendFilter.AddInputData(polydata)
            appendFilter.Update()
            try:
                if VisorView.estadorenderizado_corte == 0:
                    # Iniciar Hilo
                    loading = LoadingView.mostrarLoading()
                    def on_thread_complete():
                        loading.close()
                    dtmcorte = GenerarDTMcorteThread(appendFilter, limites)
                    dtmcorte.task_finishGenerarcortedtm.connect(on_thread_complete)
                    dtmcorte.start()
                    loading.exec()
                else:
                    # Manejar la visibilidad en función del estado de renderizado
                    if VisorView.estadorenderizado_corte % 2 == 0:
                        for actor in VisorView.lista_actoresDXF_corte:
                            actor.VisibilityOff()
                        VisorView.solidoDXF_corte.VisibilityOn()
                    else:
                        for actor in VisorView.lista_actoresDXF_corte:
                            actor.VisibilityOn()
                        VisorView.solidoDXF_corte.VisibilityOff()
                VisorView.vtkWidgetCorte.GetRenderWindow().Render()
                VisorView.estadorenderizado_corte += 1
            except Exception as e:
                print("Error al aplicar DTM al gráfico corte:", e)

    def exportarVetoresdxf(tree_actual):
        lista = EquiposVisor.obtener_todos_elementos_marcados(tree_actual)
        if lista:
            prismasmarcados = VisorView.obtenerListaEquiposMarcados(lista, "Prismas")
            if len(prismasmarcados) > 0:
                config = SoftwareConfiguracion.obtenerDataSoftware()
                filtrado = config[16]
                if VisorView.estadovector and VisorView.escalavector > 0:
                    ExportarDXF.generarDXFvectores(VisorView.idproyecto, VisorView.escalavector, prismasmarcados, VisorView.colorvectores, VisorView.fechainicial, VisorView.fechafinal, filtrado)

    def cambiarPerspectivaVistaVisor(combovistas3d, paginacionvisor):
        vista_3d = combovistas3d.currentText()
        vistas = {
            'Frontal': {'position': (0, -1, 0), 'focal_point': (0, 0, 0), 'view_up': (0, 0, 1)},
            'Isométrica': {'position': (1, 1, 1), 'focal_point': (0, 0, 0), 'view_up': (0, 1, 0)},
            'Planta': {'position': (0, 0, 1), 'focal_point': (0, 0, 0), 'view_up': (0, 1, 0)},
            'Inferior': {'position': (0, 0, -1), 'focal_point': (0, 0, 0), 'view_up': (0, -1, 0)},
            'Izquierda': {'position': (-1, 0, 0), 'focal_point': (0, 0, 0), 'view_up': (0, 0, 1)},
            'Derecha': {'position': (1, 0, 0), 'focal_point': (0, 0, 0), 'view_up': (0, 0, 1)},
            'Posterior': {'position': (0, 1, 0), 'focal_point': (0, 0, 0), 'view_up': (0, 0, -1)},
            'Inclinada': {'position': (1, -1, 1), 'focal_point': (0, 0, 0), 'view_up': (0, 1, 0)},
            'Perfil': {'position': (-1, -1, 0), 'focal_point': (0, 0, 0), 'view_up': (0, 0, 1)}
        }
        
        def actualizar_camara(vista,renderer):
            camera = renderer.GetActiveCamera()
            if vista in vistas:
                params = vistas[vista]
                camera.SetPosition(*params['position'])
                camera.SetFocalPoint(*params['focal_point'])
                camera.SetViewUp(*params['view_up'])
            renderer.ResetCamera()
            camera.Zoom(1.5)
        
        if paginacionvisor.currentIndex() == 0:
            actualizar_camara(vista_3d,VisorView.rendererVisor)
            VisorView.vtkWidgetVisor.GetRenderWindow().Render()
        elif paginacionvisor.currentIndex() == 1:
            actualizar_camara(vista_3d,VisorView.rendererCorte)
            VisorView.vtkWidgetCorte.GetRenderWindow().Render()
        elif paginacionvisor.currentIndex() == 2:
            actualizar_camara(vista_3d,VisorView.rendererLidar)
            VisorView.vtkWidgetLidar.GetRenderWindow().Render()
    
    def agregarImagenReporteVisor(tree_actual, paginacion, tiporeporte):
        if VisorView.idproyecto:
            lista = EquiposVisor.obtener_todos_elementos_marcados(tree_actual)
            if lista:
                if paginacion.currentIndex() == 0:
                    tipo = 'VISOR3D'
                    vista = VisorView.vtkWidgetVisor
                elif paginacion.currentIndex() == 1:
                    tipo = 'CORTE'
                    vista = VisorView.vtkWidgetCorte
                else:
                    tipo = 'LIDAR'
                    vista = VisorView.vtkWidgetLidar
                titulografica = f'Gráfico {tipo} Topografía'
                tipoequipo = "Topografia"
                if tiporeporte == "General":
                    GraficaReporte.mostrarDialogoImagenVisor(vista, "Visor", tipo, titulografica, VisorView.idproyecto, tipoequipo)
                else:
                    ReporteImage.modalImagenReporte(vista, "Visor", tipo, titulografica, VisorView.idproyecto, tipoequipo)
    
    def visibilidadCuboSeleccion(tree_actual, paginacion):
        lista = EquiposVisor.obtener_todos_elementos_marcados(tree_actual)
        if lista:
            topografiamarcados = VisorView.obtenerListaEquiposMarcados(lista, "Topografías")
            if len(topografiamarcados) > 0:
                bounds = VisorView.rendererVisor.ComputeVisiblePropBounds()
                # Obtiene los actores visibles en la escena
                if paginacion.currentIndex() == 0: 
                    if VisorView.estado_box: 
                        VisorView.estadoInicialCubo = bounds
                        if None in [VisorView.vtkWidgetVisor, VisorView.rendererVisor]:
                            return
                        # Crear un vtkBoxWidget
                        VisorView.boxWidget = vtk.vtkBoxWidget()
                        VisorView.boxWidget.SetInteractor(VisorView.vtkWidgetVisor.GetRenderWindow().GetInteractor())
                        VisorView.boxWidget.SetPlaceFactor(1)
                        VisorView.boxWidget.PlaceWidget(bounds)
                        # VisorView.boxWidget.SetHandleSize(0.01)
                        # VisorView.boxWidget.SetRotationEnabled(False) 
                        VisorView.boxWidget.GetHandleProperty().SetColor(1,0,0)
                        VisorView.boxWidget.GetOutlineProperty().SetColor(0.2,0.2,0.2) 
                        VisorView.vtkWidgetVisor.GetRenderWindow().Render()
                        VisorView.estado_box = False
                    if VisorView.boxWidget.GetEnabled():
                        VisorView.boxWidget.Off()
                        VisorView.boxWidget.PlaceWidget(VisorView.estadoInicialCubo)
                        VisorView.boxVisible = False
                    else:
                        VisorView.boxWidget.On()
                        VisorView.boxWidget.PlaceWidget(VisorView.estadoInicialCubo)
                        VisorView.boxVisible = True
    
    def sliderCambioTransparencia(slider, paginacion):
        valor = slider.value()
        if paginacion.currentIndex() == 0:   
            if len(VisorView.toposDTM) > 0:
                for idcompon, idtopo, solido, color, ruta in VisorView.toposDTM:
                    solido.GetProperty().SetOpacity(valor/100)
                VisorView.vtkWidgetVisor.GetRenderWindow().Render()
        else:
            if VisorView.solidoDXF_corte is not None:
                VisorView.solidoDXF_corte.GetProperty().SetOpacity(valor/100)
                VisorView.vtkWidgetCorte.GetRenderWindow().Render()
    
    def configurarInstrumentosVisor(paginacion):
        if VisorView.idproyecto:
            respuesta = ConfiguracionVisor.modalConfiguracionVisor(VisorView.idproyecto)
            if respuesta:
                # validar colores y tamaños equipos
                info = ConfiguracionVisor.obtenerDataConfiguracionVisor()
                colorfondo = MetodosGenerales.convertirHexadecimalRGB(info[0])
                VisorView.rendererVisor.SetBackground(colorfondo)
                VisorView.rendererCorte.SetBackground(colorfondo)
                VisorView.rendererLidar.SetBackground(colorfondo)
                if paginacion.currentIndex() == 0:
                    colortexto = MetodosGenerales.convertirHexadecimalRGB(info[2])
                    tamaniotexto = info[1]
                    # prismas texto
                    if len(VisorView.prismasGrafico) > 0:
                        colorprisma = MetodosGenerales.convertirHexadecimalRGB(info[4])
                        radioPrisma = info[3]
                        for prisma in VisorView.prismasGrafico:
                            # actualizar texto
                            prisma[1].SetScale(tamaniotexto, tamaniotexto, tamaniotexto)
                            prisma[1].GetProperty().SetColor(colortexto)
                            current_position = prisma[1].GetPosition()
                            # Actualizar la posición en x
                            new_x = (current_position[0] - 10) + radioPrisma
                            new_y = current_position[1]
                            new_z = current_position[2]
                            prisma[1].SetPosition(new_x, new_y, new_z)
                            # Obtener la fuente de la esfera del punto
                            mapper = prisma[0].GetMapper()
                            sphereSource = mapper.GetInputConnection(0, 0).GetProducer()
                            sphereSource.SetRadius(radioPrisma)                        
                            prisma[0].GetProperty().SetColor(colorprisma)
                        # validar los vectores
                        if len(VisorView.vectoresDXF) > 0:
                            tree_actual = VisorView.main.findChild(QTreeWidget, "tree_actual_visor")
                            lista = EquiposVisor.obtener_todos_elementos_marcados(tree_actual)
                            if lista:
                                prismasmarcados = VisorView.obtenerListaEquiposMarcados(lista, "Prismas")
                                if len(prismasmarcados) > 0:
                                    VisorView.escalarVectores(prismasmarcados)
                    if len(VisorView.inclinometroPuntos) > 0:
                        colorincli = MetodosGenerales.convertirHexadecimalRGB(info[6])
                        radioIncli = info[5]
                        for label in VisorView.inclinometroPuntos:
                            # actualizar texto
                            label[3].SetScale(tamaniotexto, tamaniotexto, tamaniotexto)                 
                            label[3].GetProperty().SetColor(colortexto)
                            current_position = label[3].GetPosition()
                            new_x = (current_position[0] - 10) + radioIncli
                            new_y = current_position[1]
                            new_z = current_position[2]
                            label[3].SetPosition(new_x, new_y, new_z)
                            # Obtener la fuente de la esfera o tubo
                            mapper = label[2].GetMapper()
                            esferatubo = mapper.GetInputConnection(0, 0).GetProducer()
                            esferatubo.SetRadius(radioIncli)                        
                            label[2].GetProperty().SetColor(colorincli)
                    if len(VisorView.piezometrostuboscuerda) > 0:
                        colorpiezo = MetodosGenerales.convertirHexadecimalRGB(info[8])
                        radioPiezo = info[7]
                        for actorpiezo in VisorView.piezometrostuboscuerda:
                            # actualizar texto
                            actorpiezo[3].SetScale(tamaniotexto, tamaniotexto, tamaniotexto) 
                            actorpiezo[3].GetProperty().SetColor(colortexto)
                            current_position = actorpiezo[3].GetPosition()
                            new_x = (current_position[0] - 10) + radioPiezo
                            new_y = current_position[1]
                            new_z = current_position[2]
                            actorpiezo[3].SetPosition(new_x, new_y, new_z)
                            # Obtener la fuente de la esfera o tubo
                            mapper = actorpiezo[4].GetMapper()
                            tubo = mapper.GetInputConnection(0, 0).GetProducer()
                            tubo.SetRadius(radioPiezo)
                            if actorpiezo[0] == "DOS":
                                actorpiezo[4].GetProperty().SetColor(colorpiezo)
                                mapper2 = actorpiezo[5].GetMapper()
                                tubo2 = mapper2.GetInputConnection(0, 0).GetProducer()
                                tubo2.SetRadius(radioPiezo)
                    if len(VisorView.piezometrostubosmanual) > 0:
                        colorpiezo = MetodosGenerales.convertirHexadecimalRGB(info[8])
                        radioPiezo = info[7]
                        for actorpiezo in VisorView.piezometrostubosmanual:
                            # actualizar texto
                            actorpiezo[3].SetScale(tamaniotexto, tamaniotexto, tamaniotexto) 
                            actorpiezo[3].GetProperty().SetColor(colortexto)
                            current_position = actorpiezo[3].GetPosition()
                            new_x = (current_position[0] - 10) + radioPiezo
                            new_y = current_position[1]
                            new_z = current_position[2]
                            actorpiezo[3].SetPosition(new_x, new_y, new_z)
                            # Obtener la fuente de la esfera o tubo
                            mapper = actorpiezo[4].GetMapper()
                            tubo = mapper.GetInputConnection(0, 0).GetProducer()
                            tubo.SetRadius(radioPiezo)
                            if actorpiezo[0] == "DOS":
                                actorpiezo[4].GetProperty().SetColor(colorpiezo)
                                mapper2 = actorpiezo[5].GetMapper()
                                tubo2 = mapper2.GetInputConnection(0, 0).GetProducer()
                                tubo2.SetRadius(radioPiezo)
                    if len(VisorView.listaactorespluvio) > 0:
                        colorpluvio = MetodosGenerales.convertirHexadecimalRGB(info[10])
                        radioPluvio = info[9]
                        for actorpluvio in VisorView.listaactorespluvio:
                            # actualizar texto
                            actorpluvio[3].SetScale(tamaniotexto, tamaniotexto, tamaniotexto) 
                            actorpluvio[3].GetProperty().SetColor(colortexto)
                            current_position = actorpluvio[3].GetPosition()
                            new_x = (current_position[0] - 10) + radioPluvio
                            new_y = current_position[1]
                            new_z = current_position[2]
                            actorpluvio[3].SetPosition(new_x, new_y, new_z)
                            # Obtener la fuente de la esfera o tubo
                            mapper = actorpluvio[2].GetMapper()
                            cono = mapper.GetInputConnection(0, 0).GetProducer()
                            cono.SetRadius(radioPluvio)
                            cono.SetHeight(radioPluvio * 2)
                            actorpluvio[2].GetProperty().SetColor(colorpluvio)
                    if len(VisorView.listaactoresceldas) > 0:
                        colorcelda = MetodosGenerales.convertirHexadecimalRGB(info[12])
                        radioCelda = info[11]
                        for actorcelda in VisorView.listaactoresceldas:
                            # actualizar texto
                            actorcelda[3].SetScale(tamaniotexto, tamaniotexto, tamaniotexto) 
                            actorcelda[3].GetProperty().SetColor(colortexto)
                            current_position = actorcelda[3].GetPosition()
                            new_x = (current_position[0] - 10) + radioCelda
                            new_y = current_position[1]
                            new_z = current_position[2]
                            actorcelda[3].SetPosition(new_x, new_y, new_z)
                            # Obtener la fuente de la esfera o tubo
                            cubo = actorcelda[4]
                            cubo.SetXLength(radioCelda)
                            cubo.SetYLength(radioCelda * 0.8)
                            cubo.SetZLength(radioCelda * 0.6)
                            cubo.Update()
                            actorcelda[2].GetProperty().SetColor(colorcelda)
                    if len(VisorView.listaactoresacelero) > 0:
                        coloracelero = MetodosGenerales.convertirHexadecimalRGB(info[14])
                        radioAcelero = info[13]
                        for actoracelero in VisorView.listaactoresacelero:
                            # actualizar texto
                            actoracelero[3].SetScale(tamaniotexto, tamaniotexto, tamaniotexto)
                            actoracelero[3].GetProperty().SetColor(colortexto)
                            current_position = actoracelero[3].GetPosition()
                            new_x = (current_position[0] - 10) + radioAcelero
                            new_y = current_position[1]
                            new_z = current_position[2]
                            actoracelero[3].SetPosition(new_x, new_y, new_z)
                            # Obtener la fuente de la esfera o tubo
                            mapper = actoracelero[2].GetMapper()
                            cilindro = mapper.GetInputConnection(0, 0).GetProducer()
                            cilindro.SetHeight(radioAcelero)
                            cilindro.SetRadius(radioAcelero / 2)
                            actoracelero[2].GetProperty().SetColor(coloracelero)
                    if len(VisorView.cablescoaxiales) > 0:
                        tree_actual =  VisorView.main.findChild(QTreeWidget, "tree_actual_visor")
                        lista = EquiposVisor.obtener_todos_elementos_marcados(tree_actual)
                        if lista:
                            sondajestdrmarcados = VisorView.obtenerListaEquiposMarcados(lista, "TDR")
                            if len(sondajestdrmarcados) > 0:
                                VisorView.mostrarSondajestdrVisor(paginacion, sondajestdrmarcados)
                    if len(VisorView.equiposgenerales) > 0:
                        for equipo in VisorView.equiposgenerales:
                            # actualizar texto
                            equipo[2].SetScale(tamaniotexto, tamaniotexto, tamaniotexto)
                            equipo[2].GetProperty().SetColor(colortexto)
                            current_position = equipo[2].GetPosition()
                            new_x = (current_position[0] - 10) + tamaniotexto
                            new_y = current_position[1]
                            new_z = current_position[2]
                            equipo[2].SetPosition(new_x, new_y, new_z)
    
    def reiniciarVistaVisor(main, proyecto_id, proyecto_name):
        paginavisor = main.findChild(QStackedWidget, "stacked_visor")
        paginavisor.setCurrentIndex(0)
        # reiniciar variables
        VisorView.idproyecto = proyecto_id
        VisorView.nameproyecto = proyecto_name
        VisorView.estadochecklist = True
        VisorView.inclinometrolineas = []
        VisorView.prismasGrafico = []
        VisorView.inclinometroPuntos = []
        VisorView.dibujarLineaIncli = 0
        VisorView.dibujarPuntoIncli = 0
        VisorView.estadorenderizado, VisorView.estadorenderizado_corte = 0, 0
        VisorView.vectoresDXF = []
        VisorView.listatopograficados = []
        VisorView.piezometrostuboscuerda = []
        VisorView.dibujarTuboPiezo = 0   
        VisorView.cablescoaxiales = []
        VisorView.equiposgenerales = []
        VisorView.estadovector, VisorView.tipovector, VisorView.escalavector = False, 'D3D', 0
        VisorView.toposDTM = []
        ConfigurarDTM.limpiarElementosDTM()
        if VisorView.boxWidget is not None:
            if VisorView.boxWidget.GetEnabled():
                VisorView.boxWidget.Off()
        VisorView.polyDataCorte, VisorView.boxWidget, VisorView.estado_box = None, None, True
        VisorView.estadografico, VisorView.resetvisor = False, False
        if VisorView.rendererVisor is not None:
            VisorView.rendererVisor.RemoveAllViewProps()
            # Crear un actor vacío
            actorVisor = vtk.vtkActor()
            # Agregar el actor al renderizador
            VisorView.rendererVisor.AddActor(actorVisor)
            VisorView.rendererVisor.ResetCamera()
            camera = VisorView.rendererVisor.GetActiveCamera()
            camera.Zoom(1.5)
        if VisorView.rendererCorte is not None:
            VisorView.rendererCorte.RemoveAllViewProps()
        if VisorView.rendererLidar is not None:
            VisorView.rendererLidar.RemoveAllViewProps()
        if VisorView.vtkWidgetVisor:
            VisorView.vtkWidgetVisor.GetRenderWindow().Render()
        if VisorView.vtkWidgetCorte:
            VisorView.vtkWidgetCorte.GetRenderWindow().Render()
        if VisorView.vtkWidgetLidar:
            VisorView.vtkWidgetLidar.GetRenderWindow().Render()
                            
    def analisisAsistenteVozVisor(tree_actual_visor, boton_voz_visor):
        boton_voz_visor.setEnabled(False)
        prismasmarcados, listainclinometros, piezocuerdamarcados, piezomanualmarcados, otrosequipos = [], [], [], [], False
        lista = EquiposVisor.obtener_todos_elementos_marcados(tree_actual_visor)
        if lista:
            otrosequipos = True
            prismasmarcados = VisorView.obtenerListaEquiposMarcados(lista, "Prismas")
            inclinomarcados = VisorView.obtenerListaEquiposMarcados(lista, "Inclinómetros")
            listainclinometros = InclinometroController.ctrlListarInclinometrosProyecto(VisorView.idproyecto, inclinomarcados)
            piezocuerdamarcados = VisorView.obtenerListaEquiposMarcados(lista, "Piezómetros Cuerda Vibrante")
            piezomanualmarcados = VisorView.obtenerListaEquiposMarcados(lista, "Piezómetros Casagrande")
        hilo_asistente = threading.Thread(target=AsistenteVoz.analizarVisor, args=(VisorView.idproyecto, prismasmarcados, VisorView.fechainicial, VisorView.fechafinal, listainclinometros, piezocuerdamarcados, piezomanualmarcados, otrosequipos, boton_voz_visor))
        hilo_asistente.start()
        
    def actualizarVistaVisor(fechaini, fechafin, filtro=False):
        VisorView.fechainicial = fechaini
        VisorView.fechafinal = fechafin       
        if VisorView.idproyecto:
            tree_actual_visor =  VisorView.main.findChild(QTreeWidget, "tree_actual_visor")
            paginacionvisor = VisorView.main.findChild(QStackedWidget, "stacked_visor")
            VisorView.obtenerMostrarEquiposMarcados(tree_actual_visor, paginacionvisor)
            VisorView.validarVectores(tree_actual_visor)
    
    def validarVectores(tree_actual):
        if VisorView.estadovector:
            lista = EquiposVisor.obtener_todos_elementos_marcados(tree_actual)
            if lista:
                prismasmarcados = VisorView.obtenerListaEquiposMarcados(lista, "Prismas")
                if len(prismasmarcados) > 0:
                        VisorView.escalarVectores(prismasmarcados)
    
    def actualizarGraficaFechasInclinometros():
        treewidget = VisorView.main.findChild(QTreeWidget, "tree_actual_visor")
        paginacion = VisorView.main.findChild(QStackedWidget, "stacked_visor")
        lista = EquiposVisor.obtener_todos_elementos_marcados(treewidget)
        if lista:
            inclinometrosmarcados = VisorView.obtenerListaEquiposMarcados(lista, "Inclinómetros")
            if len(inclinometrosmarcados) > 0:
                VisorView.mostrarInclinometrosVisor(paginacion, VisorView.escalainclinometro, inclinometrosmarcados)
    
    def actualizarGraficaFechasPiezometros(tipo):
        treewidget = VisorView.main.findChild(QTreeWidget, "tree_actual_visor")
        paginacion = VisorView.main.findChild(QStackedWidget, "stacked_visor")
        lista = EquiposVisor.obtener_todos_elementos_marcados(treewidget)
        if lista:
            if tipo == "Automatizado":
                piezocuerdasmarcados = VisorView.obtenerListaEquiposMarcados(lista, "Piezómetros Cuerda Vibrante")
                if len(piezocuerdasmarcados) > 0:
                    # traer lista de fechas
                    VisorView.mostrarPiezometrosCuerdaVisor(paginacion, piezocuerdasmarcados)
            else:
                piezomanualmarcados = VisorView.obtenerListaEquiposMarcados(lista, "Piezómetros Casagrande")
                if len(piezomanualmarcados) > 0:
                    VisorView.mostrarPiezometrosManualVisor(paginacion, piezomanualmarcados)

# Hilo procesar topografías
class ProcesarTopografiaThread(QThread):
    task_finishProcesardxf = Signal()

    def __init__(self, topos_marcadas):
        super().__init__()
        self.toposmarcadas = topos_marcadas

    def run(self):
        # procesar topografia
        VisorView.agregarActoresDXF(self.toposmarcadas)
        # mandar señal
        self.task_finishProcesardxf.emit()

# Hilo aplicar DTM
class GenerarDTMThread(QThread):
    task_finishGenerardtm = Signal()

    def __init__(self, lista_filtrada, topos_marcadas, toposRenderizadas_dict):
        super().__init__()
        self.listafiltrada = lista_filtrada
        self.toposmarcadas = topos_marcadas
        self.renderizadasdict = toposRenderizadas_dict

    def run(self):
        # procesar archivos
        VisorView.solidificarActoresDXF(self.listafiltrada, self.toposmarcadas, self.renderizadasdict)
        # mandar señal
        self.task_finishGenerardtm.emit()

# Hilo procesar el corte
class ProcesarCorteTopografiaThread(QThread):
    task_finishProcesarCorteTopo = Signal()

    def __init__(self, boxWidget, toposmarcados):
        super().__init__()
        self.boxWidget = boxWidget
        self.toposmarcados = toposmarcados

    def run(self):
        # procesar corte
        VisorView.limitesBoxCallback(self.boxWidget, None, self.toposmarcados)
        # mandar señal
        self.task_finishProcesarCorteTopo.emit()

# Hilo aplicar DTM corte
class GenerarDTMcorteThread(QThread):
    task_finishGenerarcortedtm = Signal()

    def __init__(self, appendFilter, limites):
        super().__init__()
        self.appendFilter = appendFilter
        self.limites = limites

    def run(self):
        # procesar archivos
        VisorView.solidificarGraficaCorte(self.appendFilter, self.limites)
        # mandar señal
        self.task_finishGenerarcortedtm.emit()

# Hilo vista previa prismas virtuales
class GenerarPrismaVirtualThread(QThread):
    task_finishPrismaVirtual = Signal()

    def __init__(self, x, y, z, radio, topografiasmarcadas, combo_box, plot_widget):
        super().__init__()
        self.x = x
        self.y = y
        self.z = z
        self.radio = radio
        self.topografiasmarcadas = topografiasmarcadas
        self.combo_box = combo_box
        self.plot_widget = plot_widget

    def run(self):
        promedios = VisorView.calcular_y_graficar_promedio(self.x, self.y, self.z, self.radio, self.topografiasmarcadas)
        # Graficar los resultados
        VisorView.graficar_resultados(self.combo_box, self.plot_widget, promedios)
        # mandar señal
        self.task_finishPrismaVirtual.emit()