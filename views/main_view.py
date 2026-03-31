import os
from datetime import datetime
from PySide6.QtUiTools import QUiLoader
from PySide6.QtGui import QIcon, QAction, QKeySequence
from PySide6.QtWidgets import (QMenu, QStackedWidget, QToolButton, QPushButton, QTreeWidget, QMessageBox, QApplication, QComboBox)
from PySide6.QtCore import Qt, QObject, QEvent
from utils.common.alertas import mostrar_mensaje
from utils.common.rutasarchivos import resource_path
from utils.generic.cargariconos import cargarIcono
from controllers.InterfazController import InterfazController
from utils.generic.listaiconos import ListaIconos
from views.general_view import ViewGeneral
from views.datos_view import DatosView
from views.visor_view import VisorView
from views.desplazamiento_view import DesplazamientoView
from views.velocidad_view import VelocidadView
from views.inclinometros_view import InclinometrosView
from views.piezometros_view import PiezometrosView
from views.celdas_view import CeldasView
from views.acelerografos_view import AcelerografosView
from views.sondajestdr_view import SondajetdrView
from views.analisis_view import AnalisisView
from views.reporte_view import ReporteView
from views.usuarios_view import UsuariosView
from modules.datos.registroEquipos import RegistroEquipos
from modules.proyecto.crearProyecto import CrearProyecto
from modules.datos.subirTopografias import SubirTopografias
from modules.datos.subirPrismas import SubirPrismas
from modules.datos.subirInclinometros import SubirInclinometros
from modules.datos.subirPiezometros import SubirPiezometros
from modules.umbrales.umbralesEquipos import UmbralView
from modules.empresa.softwareconfiguracion import SoftwareConfiguracion
from modules.empresa.empresaconfiguracion import EmpresaConfiguracion
from modules.datos.subirCotasTerreno import SubirCotasTerreno
from modules.datos.subirPluviometros import SubirPluviometros
from modules.datos.subirAcelerografos import SubirAcelerografos
from modules.datos.subirCeldas import SubirCeldas
from modules.datos.subirTDR import SubirTDR
from utils.common.metodosGenerales import MetodosGenerales
from utils.shared.personalizacion import Personalizacion
from controllers.ProyectoController import ProyectoController
from controllers.PrismaController import PrismaController
from controllers.PiezometroController import PiezometroController
from controllers.CeldaController import CeldaController
from controllers.AcelerografoController import AcelerografoController
from modules.estratros.estratosEquipos import ConfigurarEstratos
from services.security.session import Session
from views.dashboard_view import DashboardView
from modules.conexion.conexioDB import ConexionDB
class MenuEventFilter(QObject):
    def __init__(self, menu, main_window):
        super().__init__(menu)
        self.menu = menu
        self.main_window = main_window

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress and event.button() == Qt.RightButton:
            action = self.menu.actionAt(event.pos())
            if action:
                proyecto_id, proyecto_nombre = action.data()
                MainView.dialogo_acciones_proyecto(proyecto_id, proyecto_nombre, self.menu, self.main_window)
            return True
        return False
    
class MainView:
    main_window, proyecto_id, proyecto_name = None, None, "SIN PROYECTO"
    prismafechainicial, prismafechafinal = MetodosGenerales.obtenerRangoFechas(365)
    piezocuerdafechainicial, piezocuerdafechafinal = MetodosGenerales.obtenerRangoFechas(365)
    piezomanualfechainicial, piezomanualfechafinal = MetodosGenerales.obtenerRangoFechas(365)
    celdafechainicial, celdafechafinal = MetodosGenerales.obtenerRangoFechas(365)
    acelerofechainicial, acelerofechafinal = MetodosGenerales.obtenerRangoFechas(365)
    fechaacelero = datetime.strptime(acelerofechafinal, "%Y-%m-%d %H:%M:%S")
    solofechaacelero = str(fechaacelero.date())
    acelerografofecha, acelerohorainicial, acelerohorafinal = solofechaacelero, "00:00:00", "23:59:59"
    SoftwareConfiguracion.actualizarInfoSoftware()
    respuesta = SoftwareConfiguracion.obtenerDataSoftware()
    version = respuesta[20]
    mostrararbol = True
    
    @staticmethod
    def InterfazPrincipal():
        try:
            loader = QUiLoader()
            ui_file_path = resource_path("ui/principal.ui")
            if not os.path.exists(ui_file_path):
                raise FileNotFoundError(f"El archivo UI no se encuentra en la ruta: {ui_file_path}")
            MainView.main_window = loader.load(ui_file_path, None)
            if MainView.main_window is None:
                raise RuntimeError("No se pudo cargar la ventana principal desde el archivo UI.")
            MainView.main_window.setWindowTitle(f"E-MONITORING {MainView.version} - {MainView.proyecto_name.upper()}")

            ################################ MENÚ LATERAL #################################
            MainView.botones_menu = {
                "Dashboard": MainView.main_window.findChild(QPushButton, "btn_menu_dashboard"),
                "datos": MainView.main_window.findChild(QPushButton, "btn_menu_datos"),
                "visor": MainView.main_window.findChild(QPushButton, "btn_menu_visor"),
                "desplazamiento": MainView.main_window.findChild(QPushButton, "btn_menu_desplazamiento"),
                "velocidad": MainView.main_window.findChild(QPushButton, "btn_menu_velocidad"),
                "inclinometros": MainView.main_window.findChild(QPushButton, "btn_menu_inclinometros"),
                "piezometros": MainView.main_window.findChild(QPushButton, "btn_menu_piezometros"),
                "celdas": MainView.main_window.findChild(QPushButton, "btn_menu_celdas"),
                "acelerografos": MainView.main_window.findChild(QPushButton, "btn_menu_acelerografos"),
                "tdr": MainView.main_window.findChild(QPushButton, "btn_menu_tdr"),
                "analisis": MainView.main_window.findChild(QPushButton, "btn_menu_analisis"),
                "reporte": MainView.main_window.findChild(QPushButton, "btn_menu_reporte"),
                "usuarios": MainView.main_window.findChild(QPushButton, "btn_menu_usuarios")
            }
            for key, boton in MainView.botones_menu.items():
                cargarIcono(boton, ListaIconos.ICONOS[key])
            
            def resaltar_boton_activo(boton_activo):
                estilo_normal = "background-color: none;"
                estilo_resaltado = "background-color: rgb(59, 132, 208);"
                for boton in MainView.botones_menu.values():
                    boton.setStyleSheet(estilo_normal)
                boton_activo.setStyleSheet(estilo_resaltado)
            
            def cambiar_pagina(pagina_index):
                if pagina_index == 12:
                    if not Session.is_authenticated() or Session.get_idrole() != 1:
                        return
                MainView.main_window.findChild(QStackedWidget, "stackedWidget_principal").setCurrentIndex(pagina_index)
                if pagina_index < 10 or pagina_index>0:
                    MainView.main_window.findChild(QStackedWidget, "stacked_lista_checks").setCurrentIndex(pagina_index-1)
                boton_activo = list(MainView.botones_menu.values())[pagina_index]
                resaltar_boton_activo(boton_activo)
                MainView.verificarTipoVista(pagina_index, MainView.main_window, MainView.proyecto_id, MainView.proyecto_name)
            
            ############################ MENÚ ################################
            MainView.botones_menu["Dashboard"].clicked.connect(lambda: cambiar_pagina(0))
            MainView.botones_menu["datos"].clicked.connect(lambda: cambiar_pagina(1))
            MainView.botones_menu["visor"].clicked.connect(lambda: cambiar_pagina(2))
            MainView.botones_menu["desplazamiento"].clicked.connect(lambda: cambiar_pagina(3))
            MainView.botones_menu["velocidad"].clicked.connect(lambda: cambiar_pagina(4))
            MainView.botones_menu["inclinometros"].clicked.connect(lambda: cambiar_pagina(5))
            MainView.botones_menu["piezometros"].clicked.connect(lambda: cambiar_pagina(6))
            MainView.botones_menu["celdas"].clicked.connect(lambda: cambiar_pagina(7))
            MainView.botones_menu["acelerografos"].clicked.connect(lambda: cambiar_pagina(8))
            MainView.botones_menu["tdr"].clicked.connect(lambda: cambiar_pagina(9))
            MainView.botones_menu["analisis"].clicked.connect(lambda: cambiar_pagina(10))
            MainView.botones_menu["reporte"].clicked.connect(lambda: cambiar_pagina(11))
            MainView.botones_menu["usuarios"].clicked.connect(lambda: cambiar_pagina(12))
            if Session.is_authenticated() and Session.get_idrole() == 1:
                MainView.botones_menu["usuarios"].show()
            else:
                MainView.botones_menu["usuarios"].hide()
            # Inicializar activo el boton datos
            boton_datos = list(MainView.botones_menu.values())[0]
            boton_datos.setStyleSheet("background-color: rgb(59, 132, 208);")
            ############################## DASHBOARD #############################
            btn_visor = MainView.main_window.findChild(QToolButton, "btn_menu_bar")
            # Encuentra el QStackedWidget que quieres ocultar o mostrar
            stacked_widget_lista_checks = MainView.main_window.findChild(QStackedWidget, "stacked_lista_checks")
            btn_visor.hide()
            stacked_widget_lista_checks.hide()
            btn_refrescar_dashboard = MainView.main_window.findChild(QPushButton, "btn_refrescar_dashboard")
            cargarIcono(btn_refrescar_dashboard, ListaIconos.ICONOS["refrescar_general"])
            ############################## DATOS #############################
            btnFormatos = MainView.main_window.findChild(QPushButton, "btn_formatos")
            cargarIcono(btnFormatos, ListaIconos.ICONOS["descargar"])
            btn_exportar_datos = MainView.main_window.findChild(QPushButton, "btn_exportar_tabla_datos")
            cargarIcono(btn_exportar_datos, ListaIconos.ICONOS["exportar_tabla"])
            btn_pagina_inicio = MainView.main_window.findChild(QPushButton, "btn_pagina_inicio")
            cargarIcono(btn_pagina_inicio, ListaIconos.ICONOS["primera_pagina"])
            btn_pagina_anterior = MainView.main_window.findChild(QPushButton, "btn_pagina_anterior")
            cargarIcono(btn_pagina_anterior, ListaIconos.ICONOS["anterior_pagina"])
            btn_pagina_siguiente = MainView.main_window.findChild(QPushButton, "btn_pagina_siguiente")
            cargarIcono(btn_pagina_siguiente, ListaIconos.ICONOS["siguiente_pagina"])
            btn_pagina_final = MainView.main_window.findChild(QPushButton, "btn_pagina_fin")
            cargarIcono(btn_pagina_final, ListaIconos.ICONOS["ultima_pagina"])
            btn_refrescar_tabla_datos = MainView.main_window.findChild(QPushButton, "btn_refrescar_tabla_datos")
            cargarIcono(btn_refrescar_tabla_datos, ListaIconos.ICONOS["refrescar_general"])

            ############################## VISOR #############################
            btn_refrescar_visor = MainView.main_window.findChild(QPushButton, "btn_refrescar_vista_visor")
            cargarIcono(btn_refrescar_visor, ListaIconos.ICONOS["refrescar_general"])
            btn_vista_3d = MainView.main_window.findChild(QPushButton, "btn_vista3d")
            cargarIcono(btn_vista_3d, ListaIconos.ICONOS["vista_3d"])
            btn_vista_corte = MainView.main_window.findChild(QPushButton, "btn_vista_corte")
            cargarIcono(btn_vista_corte, ListaIconos.ICONOS["vista_corte"])
            btn_vista_lidar = MainView.main_window.findChild(QPushButton, "btn_vista_lidar")
            cargarIcono(btn_vista_lidar, ListaIconos.ICONOS["lidar"])
            btn_vista_dtm = MainView.main_window.findChild(QPushButton, "btn_aplicar_dtm")
            cargarIcono(btn_vista_dtm, ListaIconos.ICONOS["vista_dtm"])
            btn_vectores = MainView.main_window.findChild(QPushButton, "btn_escalar_vectores")
            cargarIcono(btn_vectores, ListaIconos.ICONOS["vectores"])
            btn_escalar_inclinómetros = MainView.main_window.findChild(QPushButton, "btn_escalar_inclinometros")
            cargarIcono(btn_escalar_inclinómetros, ListaIconos.ICONOS["escalar_inclinometro"])
            btn_cubo_corte = MainView.main_window.findChild(QPushButton, "btn_cubo_corte")
            cargarIcono(btn_cubo_corte, ListaIconos.ICONOS["cubo_corte"])
            btn_relizar_corte = MainView.main_window.findChild(QPushButton, "btn_realizar_corte")
            cargarIcono(btn_relizar_corte, ListaIconos.ICONOS["corte_3d"])
            btn_configurar_visor = MainView.main_window.findChild(QPushButton, "btn_configurar_visor")
            cargarIcono(btn_configurar_visor, ListaIconos.ICONOS["ajustes_visor"])
            btnfiltrarfechasvisor = MainView.main_window.findChild(QPushButton, "btn_filtrarfechas_visor")
            cargarIcono(btnfiltrarfechasvisor, ListaIconos.ICONOS["calendario"])
            btnanularfechasvisor = MainView.main_window.findChild(QPushButton, "btn_anularfechas_visor")
            cargarIcono(btnanularfechasvisor, ListaIconos.ICONOS["regresar"])
            btnReporteGeneralVisor = MainView.main_window.findChild(QPushButton, "btn_imagen_visor")
            cargarIcono(btnReporteGeneralVisor, ListaIconos.ICONOS["imagenes"])
            btnReporteVisor = MainView.main_window.findChild(QPushButton, "btn_reporte_visor")
            cargarIcono(btnReporteVisor, ListaIconos.ICONOS["imagen_reporte"])
            btnExportarVectores = MainView.main_window.findChild(QPushButton, "btn_exportar_vectores")
            cargarIcono(btnExportarVectores, ListaIconos.ICONOS["exportar_dxf"])
            btnVozVisor = MainView.main_window.findChild(QPushButton, "btn_voz_visor")
            cargarIcono(btnVozVisor, ListaIconos.ICONOS["asistente_voz"])
            btnCompareLAS = MainView.main_window.findChild(QPushButton, "btn_comparar_archivos_las")
            cargarIcono(btnCompareLAS, ListaIconos.ICONOS["comparar"])
            btn_graficar_prismas_lidar= MainView.main_window.findChild(QPushButton, "btn_graficar_desplazamientos_lidar")
            cargarIcono(btn_graficar_prismas_lidar, ListaIconos.ICONOS["desplaza"])
            
            ############################## BOTONES DESPLAZAMIENTO #############################
            btn_refrescar_vista_desplazamiento = MainView.main_window.findChild(QPushButton, "btn_refrescar_vista_desplazamiento")
            cargarIcono(btn_refrescar_vista_desplazamiento, ListaIconos.ICONOS["refrescar_general"])
            btn_resumen_desplazamiento = MainView.main_window.findChild(QPushButton, "btn_resumen_desplazamiento")
            cargarIcono(btn_resumen_desplazamiento, ListaIconos.ICONOS["resumen_desplazamiento"])
            btnfiltrarfechasdesplaza = MainView.main_window.findChild(QPushButton, "btn_filtrarfechas_desplaza")
            cargarIcono(btnfiltrarfechasdesplaza, ListaIconos.ICONOS["calendario"])
            btnanularfechasdesplaza = MainView.main_window.findChild(QPushButton, "btn_anularfechas_desplaza")
            cargarIcono(btnanularfechasdesplaza, ListaIconos.ICONOS["regresar"])
            btnVozDesplazamiento = MainView.main_window.findChild(QPushButton, "btn_voz_desplazamiento")
            cargarIcono(btnVozDesplazamiento, ListaIconos.ICONOS["asistente_voz"])
            btn_add_reporteSD= MainView.main_window.findChild(QPushButton, "btn_reporte_grafica_desplazamiento")
            cargarIcono(btn_add_reporteSD, ListaIconos.ICONOS["add_imagen_reporte"])
            btnReporteGeneralDesplaza = MainView.main_window.findChild(QPushButton, "btn_imagen_desplazamiento")
            cargarIcono(btnReporteGeneralDesplaza, ListaIconos.ICONOS["imagenes"])
            btn_configurar_ejes_sd = MainView.main_window.findChild(QPushButton, "btn_ejes_desplazamiento")
            cargarIcono(btn_configurar_ejes_sd, ListaIconos.ICONOS["configurar_ejes"])
            btn_tendencia_SD= MainView.main_window.findChild(QPushButton, "btn_tendencia_desplazamiento")
            cargarIcono(btn_tendencia_SD, ListaIconos.ICONOS["tendencia"])
            btn_limpieza_SD= MainView.main_window.findChild(QPushButton, "btn_limpieza_desplazamiento")
            cargarIcono(btn_limpieza_SD, ListaIconos.ICONOS["limpieza"])          
            btn_umbral_desplazamiento= MainView.main_window.findChild(QPushButton, "btn_umbral_desplazamiento")
            cargarIcono(btn_umbral_desplazamiento, ListaIconos.ICONOS["umbral"])  
            #UMBRAL PERSONALIZADO
            btn_umbral_desplazamiento_personalizado= MainView.main_window.findChild(QPushButton, "btn_umbral_personalizado_D")
            cargarIcono(btn_umbral_desplazamiento_personalizado, ListaIconos.ICONOS["umbral2"])

            ############################## BOTONES VELOCIDAD #############################
            btn_refrescar_vista_desplazamiento = MainView.main_window.findChild(QPushButton, "btn_refrescar_vista_velocidad")
            cargarIcono(btn_refrescar_vista_desplazamiento, ListaIconos.ICONOS["refrescar_general"])
            btn_resumen_desplazamiento = MainView.main_window.findChild(QPushButton, "btn_resumen_velocidad")
            cargarIcono(btn_resumen_desplazamiento, ListaIconos.ICONOS["resumen_desplazamiento"])
            btnfiltrarfechasveloci = MainView.main_window.findChild(QPushButton, "btn_filtrarfechas_velocidad")
            cargarIcono(btnfiltrarfechasveloci, ListaIconos.ICONOS["calendario"])
            btnanularfechasveloci = MainView.main_window.findChild(QPushButton, "btn_anularfechas_velocidad")
            cargarIcono(btnanularfechasveloci, ListaIconos.ICONOS["regresar"])
            btnVozVelocidad = MainView.main_window.findChild(QPushButton, "btn_voz_velocidad")
            cargarIcono(btnVozVelocidad, ListaIconos.ICONOS["asistente_voz"])
            btn_add_reportevelocidad= MainView.main_window.findChild(QPushButton, "btn_reporte_grafica_velocidad")
            cargarIcono(btn_add_reportevelocidad, ListaIconos.ICONOS["add_imagen_reporte"])
            btnReporteGeneralVeloci = MainView.main_window.findChild(QPushButton, "btn_imagen_velocidad")
            cargarIcono(btnReporteGeneralVeloci, ListaIconos.ICONOS["imagenes"])
            btn_configurar_ejes_velocidad = MainView.main_window.findChild(QPushButton, "btn_ejes_velocidad")
            cargarIcono(btn_configurar_ejes_velocidad, ListaIconos.ICONOS["configurar_ejes"])
            btn_tendencia_velocidad= MainView.main_window.findChild(QPushButton, "btn_tendencia_velocidad")
            cargarIcono(btn_tendencia_velocidad, ListaIconos.ICONOS["tendencia"])
            btn_limpieza_velocidad= MainView.main_window.findChild(QPushButton, "btn_limpieza_velocidad")
            cargarIcono(btn_limpieza_velocidad, ListaIconos.ICONOS["limpieza"])
            btn_umbral_velocidad= MainView.main_window.findChild(QPushButton, "btn_umbral_velocidad")
            cargarIcono(btn_umbral_velocidad, ListaIconos.ICONOS["umbral"]) 
            #UMBRAL PERSONALIZADO
            btn_umbral_velocidad_personalizado= MainView.main_window.findChild(QPushButton, "btn_umbral_personalizado_V")
            cargarIcono(btn_umbral_velocidad_personalizado, ListaIconos.ICONOS["umbral2"])

            ############################## BOTONES INCLINÓMETROS #############################
            btn_refrescar_inclinometros = MainView.main_window.findChild(QPushButton, "btn_refrescar_vista_inclinometros")
            cargarIcono(btn_refrescar_inclinometros, ListaIconos.ICONOS["refrescar_general"])
            btn_voz_inclinometros = MainView.main_window.findChild(QPushButton, "btn_voz_inclinometros")
            cargarIcono(btn_voz_inclinometros, ListaIconos.ICONOS["asistente_voz"])
            btn_ejes_inclinometros = MainView.main_window.findChild(QPushButton, "btn_ejes_inclinometros")
            cargarIcono(btn_ejes_inclinometros, ListaIconos.ICONOS["configurar_ejes"])
            btn_profun_inclinometros = MainView.main_window.findChild(QPushButton, "btn_analisis_profundidad")
            cargarIcono(btn_profun_inclinometros, ListaIconos.ICONOS["profundidad"])
            btn_add_reporteD3D = MainView.main_window.findChild(QPushButton, "btn_reporte_inclinometros")
            cargarIcono(btn_add_reporteD3D, ListaIconos.ICONOS["add_imagen_reporte"])
            btnReporteGeneralIncli = MainView.main_window.findChild(QPushButton, "btn_imagen_inclinometros")
            cargarIcono(btnReporteGeneralIncli, ListaIconos.ICONOS["imagenes"])
            btn_estratos_inclinometro= MainView.main_window.findChild(QPushButton, "btn_estratos_inclinometro")
            cargarIcono(btn_estratos_inclinometro, ListaIconos.ICONOS["estrato"]) 
            btn_umbral_inclinometro= MainView.main_window.findChild(QPushButton, "btn_umbrales_inclinometro")
            cargarIcono(btn_umbral_inclinometro, ListaIconos.ICONOS["umbral"]) 
            #UMBRAL PERSONALIZADO
            btn_umbral_Inclinometros_personalizado= MainView.main_window.findChild(QPushButton, "btn_umbral_personalizado_I")
            cargarIcono(btn_umbral_Inclinometros_personalizado, ListaIconos.ICONOS["umbral2"])
            ############################## BOTONES PIEZÓMETROS #############################
            btn_refrescar_vista_piezometros = MainView.main_window.findChild(QPushButton, "btn_refrescar_vista_piezometros")
            cargarIcono(btn_refrescar_vista_piezometros, ListaIconos.ICONOS["refrescar_general"])
            btnfiltrarfechaspiezo = MainView.main_window.findChild(QPushButton, "btn_filtrarfechas_piezometros")
            cargarIcono(btnfiltrarfechaspiezo, ListaIconos.ICONOS["calendario"])
            btnanularfechaspiezo = MainView.main_window.findChild(QPushButton, "btn_anularfechas_piezometros")
            cargarIcono(btnanularfechaspiezo, ListaIconos.ICONOS["regresar"])
            btnVozPiezometros = MainView.main_window.findChild(QPushButton, "btn_voz_piezometros")
            cargarIcono(btnVozPiezometros, ListaIconos.ICONOS["asistente_voz"])
            btn_add_reporte_piezometro = MainView.main_window.findChild(QPushButton, "btn_reporte_grafica_piezometro")
            cargarIcono(btn_add_reporte_piezometro, ListaIconos.ICONOS["add_imagen_reporte"])
            btnReporteGeneralPiezo = MainView.main_window.findChild(QPushButton, "btn_imagen_piezometros")
            cargarIcono(btnReporteGeneralPiezo, ListaIconos.ICONOS["imagenes"])
            btn_configurar_ejes_piezometro = MainView.main_window.findChild(QPushButton, "btn_ejes_piezometros")
            cargarIcono(btn_configurar_ejes_piezometro, ListaIconos.ICONOS["configurar_ejes"])
            btn_tendencia_piezometro = MainView.main_window.findChild(QPushButton, "btn_tendencia_piezometros")
            cargarIcono(btn_tendencia_piezometro, ListaIconos.ICONOS["tendencia"])
            btn_limpieza_piezometro = MainView.main_window.findChild(QPushButton, "btn_limpieza_piezometros")
            cargarIcono(btn_limpieza_piezometro, ListaIconos.ICONOS["limpieza"])
            btn_umbral_piezometro = MainView.main_window.findChild(QPushButton, "btn_umbral_piezometro")
            cargarIcono(btn_umbral_piezometro, ListaIconos.ICONOS["umbral"]) 
            #UMBRAL PERSONALIZADO
            btn_umbral_piezometros_personalizado= MainView.main_window.findChild(QPushButton, "btn_umbral_personalizado_P")
            cargarIcono(btn_umbral_piezometros_personalizado, ListaIconos.ICONOS["umbral2"])

            ############################## BOTONES CELDAS #############################
            btn_refrescar_vista_celdas = MainView.main_window.findChild(QPushButton, "btn_refrescar_celdas")
            cargarIcono(btn_refrescar_vista_celdas, ListaIconos.ICONOS["refrescar_general"])
            btnfiltrarfechascelda = MainView.main_window.findChild(QPushButton, "btn_filtrarfechas_celdas")
            cargarIcono(btnfiltrarfechascelda, ListaIconos.ICONOS["calendario"])
            btnanularfechascelda = MainView.main_window.findChild(QPushButton, "btn_anularfechas_celdas")
            cargarIcono(btnanularfechascelda, ListaIconos.ICONOS["regresar"])
            btnVozCeldas = MainView.main_window.findChild(QPushButton, "btn_voz_celdas")
            cargarIcono(btnVozCeldas, ListaIconos.ICONOS["asistente_voz"])
            btn_add_reporte_celdas = MainView.main_window.findChild(QPushButton, "btn_reporte_grafica_celdas")
            cargarIcono(btn_add_reporte_celdas, ListaIconos.ICONOS["add_imagen_reporte"])
            btnReporteGeneralCeldas = MainView.main_window.findChild(QPushButton, "btn_imagen_celdas")
            cargarIcono(btnReporteGeneralCeldas, ListaIconos.ICONOS["imagenes"])
            btn_configurar_ejes_celdas = MainView.main_window.findChild(QPushButton, "btn_ejes_celdas")
            cargarIcono(btn_configurar_ejes_celdas, ListaIconos.ICONOS["configurar_ejes"])
            btn_tendencia_celdas = MainView.main_window.findChild(QPushButton, "btn_tendencia_celdas")
            cargarIcono(btn_tendencia_celdas, ListaIconos.ICONOS["tendencia"])
            btn_limpieza_celdas = MainView.main_window.findChild(QPushButton, "btn_limpieza_celdas")
            cargarIcono(btn_limpieza_celdas, ListaIconos.ICONOS["limpieza"])
            btn_umbral_celda = MainView.main_window.findChild(QPushButton, "btn_umbral_celda")
            cargarIcono(btn_umbral_celda, ListaIconos.ICONOS["umbral"])
            #UMBRAL PERSONALIZADO
            btn_umbral_celdas_personalizado= MainView.main_window.findChild(QPushButton, "btn_umbral_personalizado_C")
            cargarIcono(btn_umbral_celdas_personalizado, ListaIconos.ICONOS["umbral2"])
            
            ############################## BOTONES ACELEROGRAFOS #############################
            btn_refrescar_vista_acelerografos = MainView.main_window.findChild(QPushButton, "btn_refrescar_vista_acelerografos")
            cargarIcono(btn_refrescar_vista_acelerografos, ListaIconos.ICONOS["refrescar_general"])
            btnfiltrarfechasacelero = MainView.main_window.findChild(QPushButton, "btn_filtrarfechas_acelero")
            cargarIcono(btnfiltrarfechasacelero, ListaIconos.ICONOS["calendario"])
            btnanularfechasacelero = MainView.main_window.findChild(QPushButton, "btn_anularfechas_acelero")
            cargarIcono(btnanularfechasacelero, ListaIconos.ICONOS["regresar"])
            btnVozAcelerografos = MainView.main_window.findChild(QPushButton, "btn_voz_acelerografos")
            cargarIcono(btnVozAcelerografos, ListaIconos.ICONOS["asistente_voz"])
            btn_add_reporte_acelerografos = MainView.main_window.findChild(QPushButton, "btn_reporte_grafica_acelerografos")
            cargarIcono(btn_add_reporte_acelerografos, ListaIconos.ICONOS["add_imagen_reporte"])
            btnReporteGeneralAcelero = MainView.main_window.findChild(QPushButton, "btn_imagen_acelerografos")
            cargarIcono(btnReporteGeneralAcelero, ListaIconos.ICONOS["imagenes"])
            btn_configurar_ejes_acelerografos = MainView.main_window.findChild(QPushButton, "btn_ejes_acelerografos")
            cargarIcono(btn_configurar_ejes_acelerografos, ListaIconos.ICONOS["configurar_ejes"])
            btn_umbral_acelero = MainView.main_window.findChild(QPushButton, "btn_umbral_acelerografo")
            cargarIcono(btn_umbral_acelero, ListaIconos.ICONOS["umbral"])
            btngenerarcsv = MainView.main_window.findChild(QPushButton, "btn_generar_csv")
            cargarIcono(btngenerarcsv, ListaIconos.ICONOS["csv"])
            
            ############################## BOTONES TDR #############################
            btn_refrescar_vista_tdr = MainView.main_window.findChild(QPushButton, "btn_refrescar_vista_tdr")
            cargarIcono(btn_refrescar_vista_tdr, ListaIconos.ICONOS["refrescar_general"])
            btnVozSondajestdr = MainView.main_window.findChild(QPushButton, "btn_voz_sondajestdr")
            cargarIcono(btnVozSondajestdr, ListaIconos.ICONOS["asistente_voz"])
            btn_add_reporte_tdr = MainView.main_window.findChild(QPushButton, "btn_reporte_grafica_tdr")
            cargarIcono(btn_add_reporte_tdr, ListaIconos.ICONOS["add_imagen_reporte"])
            btnReporteGeneralTDR = MainView.main_window.findChild(QPushButton, "btn_imagen_tdr")
            cargarIcono(btnReporteGeneralTDR, ListaIconos.ICONOS["imagenes"])
            btn_configurar_ejes_tdr = MainView.main_window.findChild(QPushButton, "btn_ejes_tdr")
            cargarIcono(btn_configurar_ejes_tdr, ListaIconos.ICONOS["configurar_ejes"])
            
            ############################## BOTONES ANALISIS #############################
            btn_refrescar_vista_analisis = MainView.main_window.findChild(QPushButton, "btn_refrescar_vista_analisis")
            cargarIcono(btn_refrescar_vista_analisis, ListaIconos.ICONOS["refrescar_general"])
            btnfiltrarfechasanalisis = MainView.main_window.findChild(QPushButton, "btn_filtrarfechas_analisis")
            cargarIcono(btnfiltrarfechasanalisis, ListaIconos.ICONOS["calendario"])
            btnanularfechasanalisis = MainView.main_window.findChild(QPushButton, "btn_anularfechas_analisis")
            cargarIcono(btnanularfechasanalisis, ListaIconos.ICONOS["regresar"])
            # Trayectoria
            btn_refrescar_trayectoria = MainView.main_window.findChild(QPushButton, "btn_refresca_grafica_trayectoria")
            cargarIcono(btn_refrescar_trayectoria, ListaIconos.ICONOS["refrescar_grafico"])
            btn_add_reporte_trayectoria = MainView.main_window.findChild(QPushButton, "btn_reporte_grafica_trayectoria")
            cargarIcono(btn_add_reporte_trayectoria, ListaIconos.ICONOS["add_imagen_reporte"])
            btnReporteGeneralTrayec = MainView.main_window.findChild(QPushButton, "btn_imagen_trayectoria")
            cargarIcono(btnReporteGeneralTrayec, ListaIconos.ICONOS["imagenes"])
            btn_limpieza_trayectoria = MainView.main_window.findChild(QPushButton, "btn_limpieza_trayectoria")
            cargarIcono(btn_limpieza_trayectoria, ListaIconos.ICONOS["limpieza"])
            btn_animacion_trayectoria = MainView.main_window.findChild(QPushButton, "btn_animacion_trayectoria")
            cargarIcono(btn_animacion_trayectoria, ListaIconos.ICONOS["animacion_trayectoria"])
            # estereografia
            btn_refrescar_estereografia = MainView.main_window.findChild(QPushButton, "btn_refresca_grafica_estereografia")
            cargarIcono(btn_refrescar_estereografia, ListaIconos.ICONOS["refrescar_grafico"])
            btn_add_reporte_estereografia = MainView.main_window.findChild(QPushButton, "btn_reporte_grafica_estereografia")
            cargarIcono(btn_add_reporte_estereografia, ListaIconos.ICONOS["add_imagen_reporte"])
            btnReporteGeneralEstereo = MainView.main_window.findChild(QPushButton, "btn_imagen_estereografia")
            cargarIcono(btnReporteGeneralEstereo, ListaIconos.ICONOS["imagenes"])
            btn_planos_estreografia= MainView.main_window.findChild(QPushButton, "btn_agregar_planos")
            cargarIcono(btn_planos_estreografia, ListaIconos.ICONOS["planos_estereografia"])
            # inversa velocidad
            btn_refrescar_vista_inversa = MainView.main_window.findChild(QPushButton, "btn_refresca_grafica_analisis")
            cargarIcono(btn_refrescar_vista_inversa, ListaIconos.ICONOS["refrescar_grafico"])
            btn_add_reporte_analisis = MainView.main_window.findChild(QPushButton, "btn_reporte_grafica_analisis")
            cargarIcono(btn_add_reporte_analisis, ListaIconos.ICONOS["add_imagen_reporte"])
            btnReporteGeneralAnalisis = MainView.main_window.findChild(QPushButton, "btn_imagen_analisis")
            cargarIcono(btnReporteGeneralAnalisis, ListaIconos.ICONOS["imagenes"])
            btn_tendencia_analisis = MainView.main_window.findChild(QPushButton, "btn_tendencia_analisis")
            cargarIcono(btn_tendencia_analisis, ListaIconos.ICONOS["tendencia"])
            btn_limpieza_analisis = MainView.main_window.findChild(QPushButton, "btn_limpieza_analisis")
            cargarIcono(btn_limpieza_analisis, ListaIconos.ICONOS["limpieza"])
            btn_ejes_analisis = MainView.main_window.findChild(QPushButton, "btn_ejes_analisis")
            cargarIcono(btn_ejes_analisis, ListaIconos.ICONOS["configurar_ejes"])
            # Tiempo Real
            btn_ejes_tiempo = MainView.main_window.findChild(QPushButton, "btn_ejes_tiemporeal")
            cargarIcono(btn_ejes_tiempo, ListaIconos.ICONOS["configurar_ejes"])
            btn_umbral_tiempo = MainView.main_window.findChild(QPushButton, "btn_umbrales_tiemporeal")
            cargarIcono(btn_umbral_tiempo, ListaIconos.ICONOS["umbral"])
            btn_asignar_tiempo = MainView.main_window.findChild(QPushButton, "btn_asignar_tiempo")
            cargarIcono(btn_asignar_tiempo, ListaIconos.ICONOS["reloj"])
            # Variaciones de coordenadas
            btn_refrescar_vista_variacion = MainView.main_window.findChild(QPushButton, "btn_refresca_grafica_variaciones")
            cargarIcono(btn_refrescar_vista_variacion, ListaIconos.ICONOS["refrescar_grafico"])
            btn_add_reporte_variaciones = MainView.main_window.findChild(QPushButton, "btn_reporte_grafica_variaciones")
            cargarIcono(btn_add_reporte_variaciones, ListaIconos.ICONOS["add_imagen_reporte"])
            btnReporteGeneralVariacion = MainView.main_window.findChild(QPushButton, "btn_imagen_variaciones")
            cargarIcono(btnReporteGeneralVariacion, ListaIconos.ICONOS["imagenes"])
            btn_ejes_variacion = MainView.main_window.findChild(QPushButton, "btn_ejes_variaciones")
            cargarIcono(btn_ejes_variacion, ListaIconos.ICONOS["configurar_ejes"])
            # histograma
            btn_refrescar_histograma = MainView.main_window.findChild(QPushButton, "btn_refrescar_histograma")
            cargarIcono(btn_refrescar_histograma, ListaIconos.ICONOS["refrescar_grafico"])
            btn_reporte_histograma = MainView.main_window.findChild(QPushButton, "btn_reporte_grafica_histograma")
            cargarIcono(btn_reporte_histograma, ListaIconos.ICONOS["add_imagen_reporte"])
            btnReporteGeneralHisto = MainView.main_window.findChild(QPushButton, "btn_imagen_histograma")
            cargarIcono(btnReporteGeneralHisto, ListaIconos.ICONOS["imagenes"])
            btn_limpieza_histograma = MainView.main_window.findChild(QPushButton, "btn_limpieza_histograma")
            cargarIcono(btn_limpieza_histograma, ListaIconos.ICONOS["limpieza"])
            btn_voz_analisis = MainView.main_window.findChild(QPushButton, "btn_voz_analisis")
            cargarIcono(btn_voz_analisis, ListaIconos.ICONOS["asistente_voz"])
            # resumen barras
            btn_refrescar_barras = MainView.main_window.findChild(QPushButton, "btn_refrescar_resumen_equipos")
            cargarIcono(btn_refrescar_barras, ListaIconos.ICONOS["refrescar_grafico"])
            btnReporteAnexosBarras = MainView.main_window.findChild(QPushButton, "btn_reporte_anexos_resumen")
            cargarIcono(btnReporteAnexosBarras, ListaIconos.ICONOS["add_imagen_reporte"])
            btnReporteGeneralBarras = MainView.main_window.findChild(QPushButton, "btn_reporte_general_resumen")
            cargarIcono(btnReporteGeneralBarras, ListaIconos.ICONOS["imagenes"])
            # Elipsoide de error
            btn_refrescar_elipse = MainView.main_window.findChild(QPushButton, "btn_refresca_grafica_elipse")
            cargarIcono(btn_refrescar_elipse, ListaIconos.ICONOS["refrescar_grafico"])
            btn_tabla_elipse = MainView.main_window.findChild(QPushButton, "btn_tabla_desviaciones")
            cargarIcono(btn_tabla_elipse, ListaIconos.ICONOS["resumen_desplazamiento"])
            btn_recalcular_desviacion = MainView.main_window.findChild(QPushButton, "btn_recalcular_desviaciones")
            cargarIcono(btn_recalcular_desviacion, ListaIconos.ICONOS["calculadora"])
            btn_ocultar_mostrar_desviaciones = MainView.main_window.findChild(QPushButton, "btn_ocultar_mostrar_desviaciones")
            cargarIcono(btn_ocultar_mostrar_desviaciones, ListaIconos.ICONOS["oculta_mostrar"])
            btn_desviaciones_manual = MainView.main_window.findChild(QPushButton, "btn_desviaciones_manuales")
            cargarIcono(btn_desviaciones_manual, ListaIconos.ICONOS["desviacion"])
            btnLimpiezaElipse = MainView.main_window.findChild(QPushButton, "btn_limpieza_ruido_elipse")
            cargarIcono(btnLimpiezaElipse, ListaIconos.ICONOS["limpieza"])
            btnControlzElipse = MainView.main_window.findChild(QPushButton, "btn_controlz_prismas")
            cargarIcono(btnControlzElipse, ListaIconos.ICONOS["backup"])
            btnReporteAnexosElipse = MainView.main_window.findChild(QPushButton, "btn_reporte_elipse_anexos")
            cargarIcono(btnReporteAnexosElipse, ListaIconos.ICONOS["add_imagen_reporte"])
            btnReporteGeneralElipse = MainView.main_window.findChild(QPushButton, "btn_reporte_elipse_general")
            cargarIcono(btnReporteGeneralElipse, ListaIconos.ICONOS["imagenes"])
            # limpieza datos prismas
            btn_configurar_ejes_elipse = MainView.main_window.findChild(QPushButton, "btn_ejes_elipse")
            cargarIcono(btn_configurar_ejes_elipse, ListaIconos.ICONOS["configurar_ejes"])

            btn_refrescar_lipiar_datos_prismas = MainView.main_window.findChild(QPushButton, "btn_refresca_grafica_limpieza")
            cargarIcono(btn_refrescar_lipiar_datos_prismas, ListaIconos.ICONOS["refrescar_grafico"])
            btn_cambios_lecturas = MainView.main_window.findChild(QPushButton, "btn_mostrar_cambios_prismas")
            cargarIcono(btn_cambios_lecturas, ListaIconos.ICONOS["clipboard"])
            
            btn_limpiar_ruido_coordenadas = MainView.main_window.findChild(QPushButton, "btn_limpiar_ruido")
            cargarIcono(btn_limpiar_ruido_coordenadas, ListaIconos.ICONOS["limpieza_ruido"])
            
            btn_limpiar_ruido_manual = MainView.main_window.findChild(QPushButton, "btn_limpiar_ruido_manual")
            cargarIcono(btn_limpiar_ruido_manual, ListaIconos.ICONOS["limpieza_ruido_manual"])
            
            ############################## BOTONES REPORTE #############################
            stacked_widget_principal = MainView.main_window.findChild(QStackedWidget, "stackedWidget_principal")
            stacked_widget_principal.currentChanged.connect(MainView.check_stacked_widget)
            
            btn_regitrarfirma = MainView.main_window.findChild(QPushButton, "btn_cargar_firma_reporte")
            cargarIcono(btn_regitrarfirma, ListaIconos.ICONOS["firma_reporte"])
            btn_cargar_componente_reporte = MainView.main_window.findChild(QPushButton, "btn_imagen_reportegeneral")
            cargarIcono(btn_cargar_componente_reporte, ListaIconos.ICONOS["add_imagen_reporte"])
            btn_ocular_mostrar_reporte = MainView.main_window.findChild(QPushButton, "btn_ocultar_vista_previa_reporte")
            cargarIcono(btn_ocular_mostrar_reporte, ListaIconos.ICONOS["ocultar"])
            btn_guardar_reporte = MainView.main_window.findChild(QPushButton, "btn_guardar_reporte")
            cargarIcono(btn_guardar_reporte, ListaIconos.ICONOS["guardar_reporte"])
            btn_generar_reporte = MainView.main_window.findChild(QPushButton, "btn_generar_reporte")
            cargarIcono(btn_generar_reporte, ListaIconos.ICONOS["refrescar_grafico"])
            zoom_in = MainView.main_window.findChild(QPushButton, "btn_acercar_zoom")
            cargarIcono(zoom_in, ListaIconos.ICONOS["zoom_in"])
            zoom_out = MainView.main_window.findChild(QPushButton, "btn_alejar_zoom")
            cargarIcono(zoom_out, ListaIconos.ICONOS["zoom_out"])           
            btn_exportar_reporte = MainView.main_window.findChild(QPushButton, "btn_exportar_reporte")
            cargarIcono(btn_exportar_reporte, ListaIconos.ICONOS["exportar_reporte"])
            btn_listar_images = MainView.main_window.findChild(QPushButton, "btn_imagenes_reporte")
            cargarIcono(btn_listar_images, ListaIconos.ICONOS["imagenes"])
            btn_imagen_anexo1 = MainView.main_window.findChild(QPushButton, "btn_cargar_imagen_componente_A1")
            cargarIcono(btn_imagen_anexo1, ListaIconos.ICONOS["add_imagen_reporte"])
            btn_imagen_anexo2 = MainView.main_window.findChild(QPushButton, "btn_cargar_imagen_componente_A2")
            cargarIcono(btn_imagen_anexo2, ListaIconos.ICONOS["add_imagen_reporte"])
            
            ############################## USUARIOS #############################
            btnrefrescarusuarios = MainView.main_window.findChild(QPushButton, "btn_refrescar_usuarios")
            cargarIcono(btnrefrescarusuarios, ListaIconos.ICONOS["refrescar_general"])
            btnnuevousuario = MainView.main_window.findChild(QPushButton, "btn_nuevo_usuario")
            cargarIcono(btnnuevousuario, ListaIconos.ICONOS["adduser"])
            
            ############################## BOTONES GENERALES #############################
            btn_menu_bar = MainView.main_window.findChild(QToolButton, "btn_menu_bar")
            cargarIcono(btn_menu_bar, ListaIconos.ICONOS["menu_bar"])
            btn_menu_bar.clicked.connect(lambda: MainView.ocultarMostrarMenuProyectos(MainView.main_window))
            # filtrar fechas
            btnfiltrarfechasvisor.clicked.connect(lambda: MainView.mostrarDialogoFiltroFechas("VISOR"))
            btnanularfechasvisor.clicked.connect(lambda: MainView.anularFiltradoFechas("VISOR"))
            btnfiltrarfechasdesplaza.clicked.connect(lambda: MainView.mostrarDialogoFiltroFechas("DESPLAZAMIENTO"))
            btnanularfechasdesplaza.clicked.connect(lambda: MainView.anularFiltradoFechas("DESPLAZAMIENTO"))
            btnfiltrarfechasveloci.clicked.connect(lambda: MainView.mostrarDialogoFiltroFechas("VELOCIDAD"))
            btnanularfechasveloci.clicked.connect(lambda: MainView.anularFiltradoFechas("VELOCIDAD"))
            btnfiltrarfechaspiezo.clicked.connect(lambda: MainView.mostrarDialogoFiltroFechas("PIEZOMETROS"))
            btnanularfechaspiezo.clicked.connect(lambda: MainView.anularFiltradoFechas("PIEZOMETROS"))
            btnfiltrarfechascelda.clicked.connect(lambda: MainView.mostrarDialogoFiltroFechas("CELDAS"))
            btnanularfechascelda.clicked.connect(lambda: MainView.anularFiltradoFechas("CELDAS"))
            btnfiltrarfechasacelero.clicked.connect(MainView.mostrarFiltroFechasAcelerografos)
            btnanularfechasacelero.clicked.connect(lambda: MainView.anularFiltradoFechas("ACELEROGRAFOS"))
            btnfiltrarfechasanalisis.clicked.connect(lambda: MainView.mostrarDialogoFiltroFechas("ANALISIS"))
            btnanularfechasanalisis.clicked.connect(lambda: MainView.anularFiltradoFechas("ANALISIS"))
            # Conectar acción Nuevo proyecto
            action_nuevo_proyecto = MainView.main_window.findChild(QAction, "action_nuevo_proyecto")
            action_nuevo_proyecto.setShortcut(QKeySequence("Ctrl+N"))
            action_nuevo_proyecto.triggered.connect(lambda: MainView.crearNuevoProyecto(MainView.main_window))
            # Conectar acción importar topografia
            action_cargar_topografia = MainView.main_window.findChild(QAction, "action_importar_dxf_las")
            action_cargar_topografia.triggered.connect(MainView.subir_topografia)
            # INSTRUMENTACIÓN
            # Conectar acción cargar prismas
            action_cargar_prismas = MainView.main_window.findChild(QAction, "action_cargar_prismas_auto")
            action_cargar_prismas.triggered.connect(MainView.subirArchivoPrismasAutomatizados)
            # Conectar acción cargar manuales
            action_cargar_prismas_manuales = MainView.main_window.findChild(QAction, "action_cargar_prismas_manuales")
            action_cargar_prismas_manuales.triggered.connect(MainView.pegarDataPrismasManuales)
            action_cargar_formato_prismas = MainView.main_window.findChild(QAction, "action_formato_prismas")
            action_cargar_formato_prismas.triggered.connect(MainView.subirFormatoPrismas)
            
            # Conectar acción nuevo piezómetro cuerda
            actionNuevoPiezoCuerda = MainView.main_window.findChild(QAction, "action_nuevo_piezocuerda")
            actionNuevoPiezoCuerda.triggered.connect(MainView.crearNuevoPiezometroCuerda)
            actionNuevaFormulaCuerda = MainView.main_window.findChild(QAction, "action_nueva_formula")
            actionNuevaFormulaCuerda.triggered.connect(MainView.crearFormulaPiezometroCuerda)
            # Conectar acción nuevo piezómetro casagrande
            actionNuevoPiezoManual = MainView.main_window.findChild(QAction, "action_nuevo_piezomanual")
            actionNuevoPiezoManual.triggered.connect(MainView.crearNuevoPiezometroManual)
            actionNuevaCotaPiezo = MainView.main_window.findChild(QAction, "action_nueva_cotapiezometrica")
            actionNuevaCotaPiezo.triggered.connect(MainView.registrarNuevaCotaPiezometrica)
            # Conectar acción cargar data piezometros cuerda
            actionCargarPiezometrosCuerda = MainView.main_window.findChild(QAction, "action_cargar_cuerda_vibrante")
            actionCargarPiezometrosCuerda.triggered.connect(MainView.subirDataPiezometroCuerda)
            actionFormatoPiezoCuerda = MainView.main_window.findChild(QAction, "action_formato_cuerda")
            actionFormatoPiezoCuerda.triggered.connect(MainView.subirFormatoPiezometroCuerda)
            # actionFormatoPiezoCuerda.triggered.connect(lambda: MainView.subirExcelPiezometroCuerda())
            # Conectar acción cargar data piezometros casagrande
            actionCargarPiezometrosManual = MainView.main_window.findChild(QAction, "action_cargar_casagrande")
            actionCargarPiezometrosManual.triggered.connect(MainView.subirDataPiezometroManual)
            actionFormatoPiezoManual = MainView.main_window.findChild(QAction, "action_formato_casagrande")
            actionFormatoPiezoManual.triggered.connect(MainView.subirFormatoPiezometroManual)
            # #################################### Umbrales
            # umbrales prismas
            actionUmbralesPrismas = MainView.main_window.findChild(QAction, "action_umbrales_prismas")
            actionUmbralesPrismas.triggered.connect(lambda: MainView.configurarUmbralesInstrumentacion('PRISMAS'))
            # umbrales inclinómetros
            actionUmbralesInclinometros = MainView.main_window.findChild(QAction, "action_umbrales_inclinometros")
            actionUmbralesInclinometros.triggered.connect(lambda: MainView.configurarUmbralesInstrumentacion('INCLINOMETROS'))
            # umbrales piezómetros
            actionUmbralesPiezometros = MainView.main_window.findChild(QAction, "action_umbrales_piezometros")
            actionUmbralesPiezometros.triggered.connect(lambda: MainView.configurarUmbralesInstrumentacion('PIEZOMETROS'))
            # umbrales celdas
            actionUmbralesCeldas = MainView.main_window.findChild(QAction, "action_umbrales_celdas")
            actionUmbralesCeldas.triggered.connect(lambda: MainView.configurarUmbralesInstrumentacion('CELDAS'))
            # umbrales acelerógrafos
            actionUmbralesAcelerografos = MainView.main_window.findChild(QAction, "action_umbrales_acelerografos")
            actionUmbralesAcelerografos.triggered.connect(lambda: MainView.configurarUmbralesInstrumentacion('ACELEROGRAFOS'))
            # umbrales personalizado
            actionUmbralesPersonalizado = MainView.main_window.findChild(QAction, "action_umbral_personalizado")
            actionUmbralesPersonalizado.triggered.connect(MainView.registrarUmbralPersonalizado)
            # estratos
            actionConfigurarEstratos = MainView.main_window.findChild(QAction, "action_estratos_inclinometros")
            actionConfigurarEstratos.triggered.connect(lambda: ConfigurarEstratos.modalEstratos(MainView.proyecto_id))
            
            # inclinómetros
            actionNuevoInclinometro = MainView.main_window.findChild(QAction, "action_nuevo_Inclinometro")
            actionNuevoInclinometro.triggered.connect(MainView.mostrarDialogoRegistroInclinometros)
            action_cargar_inclinometros = MainView.main_window.findChild(QAction, "action_cargar_inclinometros")
            action_cargar_inclinometros.triggered.connect(MainView.subir_inclinometros)
            
            #Celdas de Asentamiento
            actionNuevaCelda = MainView.main_window.findChild(QAction, "action_nueva_celda_asentamiento")
            actionNuevaCelda.triggered.connect(MainView.mostrarDialogoRegistroCeldasAsentamiento)
            actionDataCeldas = MainView.main_window.findChild(QAction, "action_cargar_celdas_tabla")
            actionDataCeldas.triggered.connect(MainView.registrarDataCeldas)
            actionDataFormatoCeldas = MainView.main_window.findChild(QAction, "action_formato_celdas")
            actionDataFormatoCeldas.triggered.connect(MainView.subirFormatoDataCeldas)
            # actionDataFormatoCeldas.triggered.connect(MainView.subirExcelDataCeldas)
            # TDR
            actionNuevoSondajeTDR = MainView.main_window.findChild(QAction, "action_nuevo_tdr")
            actionNuevoSondajeTDR.triggered.connect(MainView.mostrarDialogoRegistroTDR)
            actionDataTDR = MainView.main_window.findChild(QAction, "action_lecturas_tdr")
            actionDataTDR.triggered.connect(MainView.registrarDataTDR)
            actionDataFormatoTDR = MainView.main_window.findChild(QAction, "action_formato_tdr")
            actionDataFormatoTDR.triggered.connect(MainView.subirDataFormatoTDR)
            
            actionFallasTDR = MainView.main_window.findChild(QAction, "action_fallas_tdr")
            actionFallasTDR.triggered.connect(MainView.registraFallasTDR)
            # Acelerpografos
            actionNuevoAcelerografo = MainView.main_window.findChild(QAction, "action_nuevo_acelerografo")
            actionNuevoAcelerografo.triggered.connect(MainView.mostrarDialogoRegistroAcelerografo)
            actionDataAcelerografo = MainView.main_window.findChild(QAction, "action_cargar_acelerografos_tabla")
            actionDataAcelerografo.triggered.connect(MainView.registrarDataAcelerografo)
            actionDataFormatoAcelerografo = MainView.main_window.findChild(QAction, "action_formato_acelerografos")
            actionDataFormatoAcelerografo.triggered.connect(MainView.subirFormatoDataAcelerografo)
            actionCargaArchivos = MainView.main_window.findChild(QAction, "action_cargar_archivos")
            actionCargaArchivos.triggered.connect(MainView.subirArchivosAcelerografo)
            # pluviometros
            actionNuevoPluviometro = MainView.main_window.findChild(QAction, "action_nuevo_pluviometro")
            actionNuevoPluviometro.triggered.connect(MainView.mostrarDialogoRegistroPluviometro)
            actionDataPluviometro = MainView.main_window.findChild(QAction, "action_cargar_tabla_pluviometro")
            actionDataPluviometro.triggered.connect(MainView.registrarDataPluvimetro)
            actionDataFormatoPluviometro = MainView.main_window.findChild(QAction, "action_formato_pluviometro")
            actionDataFormatoPluviometro.triggered.connect(MainView.subirFormatoDataPluviometro)
            # Cotas
            actionNuevaCotaTerreno = MainView.main_window.findChild(QAction, "action_nueva_cota_terreno")
            actionNuevaCotaTerreno.triggered.connect(MainView.mostrarDialogoRegistroCotaTerreno)
            
            actionDataCotaTerreno = MainView.main_window.findChild(QAction, "action_cargar_terreno_tabla")
            actionDataCotaTerreno.triggered.connect(MainView.registrarCotasTerreno)
            actionDataFormatoTerreno = MainView.main_window.findChild(QAction, "action_formato_terreno")
            actionDataFormatoTerreno.triggered.connect(MainView.subirFormatoDataCotasTerreno)
            #Equipos Generales
            actionNuevaEqupipoGeneral = MainView.main_window.findChild(QAction, "action_equipo_general")
            actionNuevaEqupipoGeneral.triggered.connect(MainView.mostrarDialogoEquipoGeneral)
            # Conectar acción Manual de Usuario
            actionManualUsuario = MainView.main_window.findChild(QAction, "action_manual_usuario")
            actionManualUsuario.setShortcut(QKeySequence("Ctrl+M"))
            actionManualUsuario.triggered.connect(MainView.mostrarDialogoManualUsuario)
            # Conectar acción Configuracion Software
            actionConfigSoftware = MainView.main_window.findChild(QAction, "action_configuracion_software")
            actionConfigSoftware.setShortcut(QKeySequence("Ctrl+R"))
            actionConfigSoftware.triggered.connect(MainView.mostrarDialogoConfiguracionSoftware)
            # Conectar acción Configuracion Empresa
            actionConfigEmpresa = MainView.main_window.findChild(QAction, "action_configuracion_empresa")
            actionConfigEmpresa.setShortcut(QKeySequence("Ctrl+Q"))
            actionConfigEmpresa.triggered.connect(MainView.mostrarDialogoConfiguracionEmpresa)
            # Conectar acción Acerca de
            actionAcercade = MainView.main_window.findChild(QAction, "action_acercade")
            actionAcercade.setShortcut(QKeySequence("Ctrl+I"))
            actionAcercade.triggered.connect(MainView.mostrarDialogoAcercade)
            # Conectar acción Soporte
            actionSoporte = MainView.main_window.findChild(QAction, "action_soporte")
            actionSoporte.setShortcut(QKeySequence("Ctrl+T"))
            actionSoporte.triggered.connect(MainView.mostrarDialogoSoporte)
            
            actionNuevoComponente = MainView.main_window.findChild(QAction, "action_nuevo_componente")
            actionNuevoComponente.setShortcut(QKeySequence("Ctrl+K"))
            actionNuevoComponente.triggered.connect(MainView.registrarComponente)
            
            actionHistorial = MainView.main_window.findChild(QAction, "action_historial_cambios")
            actionHistorial.triggered.connect(MainView.mostrarDialogoHistorialCambios)
            
            # conetar sqlserver
            actionConexionDB = MainView.main_window.findChild(QAction, "action_conexion_DB")
            actionConexionDB.triggered.connect(MainView.mostrarDialogoConexion)

            # Conexiones sqlserver de Prismas
            actionConexiones = MainView.main_window.findChild(QAction, "action_conexiones")
            actionConexiones.triggered.connect(MainView.mostrarDialogoConexiones)

            if Session.is_authenticated() and Session.get_idrole() == 1:
                actionHistorial.setVisible(True)
                actionConexionDB.setVisible(True)
                actionConexiones.setVisible(True)
            else:
                actionHistorial.setVisible(False)
                actionConexionDB.setVisible(False)
                actionConexiones.setVisible(False)
            
            actionSalir = MainView.main_window.findChild(QAction, "action_salir")
            actionSalir.triggered.connect(MainView.cerrarSesion)
            
            # PROYECTOS RECIENTES
            actionProyectos_Recientes = MainView.main_window.findChild(QAction, 'action_proyectos_recientes')
            if actionProyectos_Recientes:
                menu_proyectos_recientes = actionProyectos_Recientes.menu()
                if menu_proyectos_recientes is None:
                    menu_proyectos_recientes = QMenu("Proyectos Recientes", MainView.main_window)
                    actionProyectos_Recientes.setMenu(menu_proyectos_recientes)
                MainView.listar_proyectos_recientes(menu_proyectos_recientes, MainView.main_window)
            return MainView.main_window
        except Exception as e:
            mostrar_mensaje("Error de Interfaz", f"No se pudo cargar la ventana principal: {str(e)}", "error")
            return None
    
    def mostrarFiltroFechasAcelerografos():
        comboAcelerografos = MainView.main_window.findChild(QComboBox, "cb_tipo_grafico_acelerografos")
        tipografica = comboAcelerografos.currentData()
        if tipografica == "AMA":
            MainView.mostrarDialogoFiltroFechas("ACELEROGRAFOS")
        else:
            fechaini, horaini, horafin = Personalizacion.dialogoFiltroHoras(MainView.acelerografofecha, MainView.acelerohorainicial, MainView.acelerohorafinal)
            if fechaini and horaini and horafin:
                MainView.acelerografofecha, MainView.acelerohorainicial, MainView.acelerohorafinal = fechaini, horaini, horafin
                AcelerografosView.actualizarVistaAcelerografos(MainView.acelerofechainicial, MainView.acelerofechafinal, MainView.acelerografofecha, MainView.acelerohorainicial, MainView.acelerohorafinal)
    
    def mostrarDialogoFiltroFechas(tipo):
        if tipo == "VISOR":
            fechainifiltro, fechafinfiltro = MainView.prismafechainicial, MainView.prismafechafinal
        elif tipo == "DESPLAZAMIENTO":
            fechainifiltro, fechafinfiltro = MainView.prismafechainicial, MainView.prismafechafinal
        elif tipo == "VELOCIDAD":
            fechainifiltro, fechafinfiltro = MainView.prismafechainicial, MainView.prismafechafinal
        elif tipo == "PIEZOMETROS":
            fechainifiltro, fechafinfiltro = MainView.piezocuerdafechainicial, MainView.piezocuerdafechafinal
        elif tipo == "CELDAS":
            fechainifiltro, fechafinfiltro = MainView.celdafechainicial, MainView.celdafechafinal
        elif tipo == "ACELEROGRAFOS":
            fechainifiltro, fechafinfiltro = MainView.acelerofechainicial, MainView.acelerofechafinal
        elif tipo == "ANALISIS":
            fechainifiltro, fechafinfiltro = MainView.prismafechainicial, MainView.prismafechafinal
        else:
            fechainifiltro, fechafinfiltro = MainView.prismafechainicial, MainView.prismafechafinal
        fechaini, fechafin = Personalizacion.dialogoFiltroFechas(fechainifiltro, fechafinfiltro)
        if fechaini and fechafin:
            MainView.prismafechainicial, MainView.prismafechafinal = fechaini, fechafin
            MainView.piezocuerdafechainicial, MainView.piezocuerdafechafinal = fechaini, fechafin
            MainView.piezomanualfechainicial, MainView.piezomanualfechafinal = fechaini, fechafin
            MainView.celdafechainicial, MainView.celdafechafinal = fechaini, fechafin
            MainView.acelerofechainicial, MainView.acelerofechafinal = fechaini, fechafin
            if tipo == "VISOR":
                VisorView.actualizarVistaVisor(MainView.prismafechainicial, MainView.prismafechafinal)
            elif tipo == "DESPLAZAMIENTO":
                DesplazamientoView.actualizarVistaDesplazamiento(MainView.prismafechainicial, MainView.prismafechafinal)
            elif tipo == "VELOCIDAD":
                VelocidadView.actualizarVistaVelocidad(MainView.prismafechainicial, MainView.prismafechafinal)
            elif tipo == "PIEZOMETROS":
                PiezometrosView.actualizarVistaPiezometros(MainView.piezocuerdafechainicial, MainView.piezocuerdafechafinal, MainView.piezomanualfechainicial, MainView.piezomanualfechafinal)
            elif tipo == "CELDAS":
                CeldasView.actualizarVistaCeldas(MainView.celdafechainicial, MainView.celdafechafinal)
            elif tipo == "ACELEROGRAFOS":
                AcelerografosView.actualizarVistaAcelerografos(MainView.acelerofechainicial, MainView.acelerofechafinal, MainView.acelerografofecha, MainView.acelerohorainicial, MainView.acelerohorafinal)
            elif tipo == "ANALISIS":
                AnalisisView.actualizarVistaAnalisis(MainView.prismafechainicial, MainView.prismafechafinal)
    
    def anularFiltradoFechas(tipo):
        MainView.actualizarRangoFechas()
        if tipo == "VISOR":
            VisorView.actualizarVistaVisor(MainView.prismafechainicial, MainView.prismafechafinal)
        elif tipo == "DESPLAZAMIENTO":
            DesplazamientoView.actualizarVistaDesplazamiento(MainView.prismafechainicial, MainView.prismafechafinal)
        elif tipo == "VELOCIDAD":
            VelocidadView.actualizarVistaVelocidad(MainView.prismafechainicial, MainView.prismafechafinal)
        elif tipo == "PIEZOMETROS":
            PiezometrosView.actualizarVistaPiezometros(MainView.piezocuerdafechainicial, MainView.piezocuerdafechafinal, MainView.piezomanualfechainicial, MainView.piezomanualfechafinal)
        elif tipo == "CELDAS":
            CeldasView.actualizarVistaCeldas(MainView.celdafechainicial, MainView.celdafechafinal)
        elif tipo == "ACELEROGRAFOS":
            AcelerografosView.actualizarVistaAcelerografos(MainView.acelerofechainicial, MainView.acelerofechafinal, MainView.acelerografofecha, MainView.acelerohorainicial, MainView.acelerohorafinal)
        elif tipo == "ANALISIS":
            AnalisisView.actualizarVistaAnalisis(MainView.prismafechainicial, MainView.prismafechafinal)
    
    ##########################Regitrar data equipos###########################
    def registrarComponente():
        if MainView.proyecto_id:
            result = CrearProyecto.registro_componente(MainView.proyecto_id)
            if result:
                # Actualizar los componentes
                actionListaComponentes = MainView.main_window.findChild(QAction, 'action_lista_componentes')
                if actionListaComponentes:
                    menu_componentes = actionListaComponentes.menu()
                    if menu_componentes is None:
                        menu_componentes = QMenu("Lista de Componentes", MainView.main_window)
                        actionListaComponentes.setMenu(menu_componentes)
                    MainView.listar_componentes_proyecto(menu_componentes, MainView.main_window)
        else:
            mostrar_mensaje("Sin Proyecto", "Inicie un proyecto primero.", "advertencia")
            
    def registrarDataCeldas():
        if MainView.proyecto_id:
            SubirCeldas.registrarDataCeldas(MainView.main_window, MainView.proyecto_id)
            MainView.actualizarRangoFechas()
        else:
            mostrar_mensaje("Sin Proyecto", "Inicie un proyecto primero.", "advertencia")
    
    def subirFormatoDataCeldas():
        if MainView.proyecto_id:
            SubirCeldas.cargarDataFormatosCeldas(MainView.main_window, MainView.proyecto_id, "FORMATO")
            MainView.actualizarRangoFechas()
    
    def subirExcelDataCeldas():
        if MainView.proyecto_id:
            SubirCeldas.cargarDataFormatosCeldas(MainView.main_window, MainView.proyecto_id, "EXCEL")
            MainView.actualizarRangoFechas()
    
    def registrarDataTDR():
        if MainView.proyecto_id:
            SubirTDR.registrarDataTDR(MainView.main_window, MainView.proyecto_id)
        else:
            mostrar_mensaje("Sin Proyecto", "Inicie un proyecto primero.", "advertencia")
    
    def subirDataFormatoTDR():
        if MainView.proyecto_id:
            SubirTDR.cargarDataFormatoTDR(MainView.main_window, MainView.proyecto_id)
    
    def registraFallasTDR():
        if MainView.proyecto_id:
            SubirTDR.registrarFallasTDR(MainView.proyecto_id)
        else:
            mostrar_mensaje("Sin Proyecto", "Inicie un proyecto primero.", "advertencia")
    
    def registrarDataAcelerografo():
        if MainView.proyecto_id:
            SubirAcelerografos.registrarDataAcelerografos(MainView.main_window, MainView.proyecto_id)
            MainView.actualizarRangoFechas()
        else:
            mostrar_mensaje("Sin Proyecto", "Inicie un proyecto primero.", "advertencia")
    
    def subirArchivosAcelerografo():
        if MainView.proyecto_id:
            SubirAcelerografos.cargarArchivosAcelerografos(MainView.main_window, MainView.proyecto_id)

    def subirFormatoDataAcelerografo():
        if MainView.proyecto_id:
            SubirAcelerografos.cargarDataFormatoAcelerografos(MainView.main_window, MainView.proyecto_id)
            MainView.actualizarRangoFechas()
    
    def registrarDataPluvimetro():
        if MainView.proyecto_id:
            SubirPluviometros.registroNuevaDataPluviometros(MainView.main_window, MainView.proyecto_id)
        else:
            mostrar_mensaje("Sin Proyecto", "Inicie un proyecto primero.", "advertencia")
    
    def subirFormatoDataPluviometro():
        if MainView.proyecto_id:
            SubirPluviometros.cargarDataFormatosPluviometros(MainView.main_window, MainView.proyecto_id)
    
    def registrarCotasTerreno():
        if MainView.proyecto_id:
            SubirCotasTerreno.registroDataCotaTerreno(MainView.main_window, MainView.proyecto_id)
        else:
            mostrar_mensaje("Sin Proyecto", "Inicie un proyecto primero.", "advertencia")
    
    def subirFormatoDataCotasTerreno():
        if MainView.proyecto_id:
            SubirCotasTerreno.cargarDataFormatosCotasTerreno(MainView.main_window, MainView.proyecto_id)
    
    ########################Registro equipos##################################
    def mostrarDialogoRegistroInclinometros():
        if MainView.proyecto_id:
            SubirInclinometros.registrarInclinometro(MainView.proyecto_id)
        else:
            mostrar_mensaje("Sin Proyecto", "Inicie un proyecto primero.", "advertencia")
        
    def mostrarDialogoRegistroCeldasAsentamiento():
        if MainView.proyecto_id:
            ViewGeneral.mostrarDialogoRegistroCeldasAsentamiento(MainView.proyecto_id)
        
    def mostrarDialogoRegistroTDR():
        if MainView.proyecto_id:
            RegistroEquipos.mostrarDialogoRegistroSondajesTDR(MainView.proyecto_id)
        else:
            mostrar_mensaje("Sin Proyecto", "Inicie un proyecto primero.", "advertencia")
        
    def mostrarDialogoRegistroAcelerografo():
        if MainView.proyecto_id:
            RegistroEquipos.dialogoRegistroAcelerografos(MainView.proyecto_id)
        else:
            mostrar_mensaje("Sin Proyecto", "Inicie un proyecto primero.", "advertencia")
    
    def mostrarDialogoRegistroPluviometro():
        if MainView.proyecto_id:
            RegistroEquipos.mostrarDialogoRegistroPluviometros(MainView.proyecto_id)
        else:
            mostrar_mensaje("Sin Proyecto", "Inicie un proyecto primero.", "advertencia")
        
    def mostrarDialogoRegistroCotaTerreno():
        if MainView.proyecto_id:
            RegistroEquipos.mostrarDialogoRegistroCotaTerreno(MainView.proyecto_id)
        else:
            mostrar_mensaje("Sin Proyecto", "Inicie un proyecto primero.", "advertencia")
    
    def mostrarDialogoEquipoGeneral():
        if MainView.proyecto_id:
            RegistroEquipos.mostrarDialogoEquiposGenerales(MainView.main_window, MainView.proyecto_id)
        else:
            mostrar_mensaje("Sin Proyecto", "Inicie un proyecto primero.", "advertencia")
            
    def mostrarDialogoManualUsuario():
        ViewGeneral.mostrarDialogoManualUsuario()
    
    def mostrarDialogoConfiguracionSoftware():
        SoftwareConfiguracion.mostrarDialogoConfiguracionSoftware()
    
    def mostrarDialogoConfiguracionEmpresa():
        EmpresaConfiguracion.mostrarDialogoConfiguracionEmpresa()
    
    def mostrarDialogoAcercade():
        ViewGeneral.mostrarDialogoAcercade(MainView.version)
    
    def mostrarDialogoSoporte():
        ViewGeneral.mostrarDialogoSoporte(MainView.version)
    
    def mostrarDialogoHistorialCambios():
        if Session.is_authenticated() and Session.get_idrole() == 1:
            CrearProyecto.dialogoDatosHistorialCambiosDatabase()
    
    def mostrarDialogoConexion():
        if Session.is_authenticated() and Session.get_idrole() == 1:
            ConexionDB.configuracion()
    
    def mostrarDialogoConexiones():
        if Session.is_authenticated() and Session.get_idrole() == 1:
            ConexionDB.mostrarConfiguracionesSqlServer()
    
    def ocultarMostrarMenuProyectos(main):
        # Buscar el QStackedWidget y el botón una sola vez
        qstacked_widget = main.findChild(QStackedWidget, "stacked_lista_checks")
        btn_visor = main.findChild(QToolButton, "btn_menu_bar")
        # Cambiar el ícono y visibilidad según el estado actual
        if MainView.mostrararbol:
            # Si el widget está visible, cambiar al ícono de "caret-right" y ocultar el widget
            svg_icon_path = resource_path("resources/iconos/fontawesome/solid/caret-left.svg")
            qstacked_widget.hide()
            MainView.mostrararbol = False
        else:
            # Si el widget está oculto, cambiar al ícono de "caret-left" y mostrar el widget
            svg_icon_path = resource_path("resources/iconos/fontawesome/solid/caret-right.svg")
            qstacked_widget.show()
            MainView.mostrararbol = True
        # Actualizar el ícono del botón
        icon = QIcon(svg_icon_path)
        btn_visor.setIcon(icon)
    
    @staticmethod
    def listar_proyectos_recientes(menu, main_window):
        menu.clear()
        lista = InterfazController.ctrlListarProyectos()
        if lista:
            num_proyectos_a_mostrar = 10
            # Lista principal
            for i, proyecto in enumerate(lista[:num_proyectos_a_mostrar]):
                accion_proyecto = QAction(proyecto[1], main_window)
                accion_proyecto.setData((proyecto[0], proyecto[1]))
                # CORRECCIÓN AQUÍ: Usamos *args en lugar de checked
                accion_proyecto.triggered.connect(lambda *args, p=proyecto, main=main_window: MainView.manejar_proyecto_seleccionado(p, main))
                menu.addAction(accion_proyecto)
                if i < len(lista[:num_proyectos_a_mostrar]) - 1:
                    menu.addSeparator()
            
            # Submenú "Mostrar más"
            if len(lista) > num_proyectos_a_mostrar:
                menu.addSeparator()
                submenu_mostrar_mas = QMenu("Mostrar más...", main_window)
                for proyecto in lista[num_proyectos_a_mostrar:]:
                    accion_proyecto = QAction(proyecto[1], main_window)
                    accion_proyecto.setData((proyecto[0], proyecto[1]))
                    # CORRECCIÓN AQUÍ TAMBIÉN: Usamos *args
                    accion_proyecto.triggered.connect(lambda *args, p=proyecto, main=main_window: MainView.manejar_proyecto_seleccionado(p, main))
                    submenu_mostrar_mas.addAction(accion_proyecto)
                    if i < len(lista[num_proyectos_a_mostrar:]) - 1:
                        submenu_mostrar_mas.addSeparator()
                menu.addMenu(submenu_mostrar_mas)
        
        menu.installEventFilter(MenuEventFilter(menu, main_window))

    @staticmethod
    def listar_componentes_proyecto(menu, main_window):
        menu.clear()
        if MainView.proyecto_id:
            lista = ProyectoController.ctrlObtenerComponentesProyecto(MainView.proyecto_id)
            if lista:
                num_componentes_mostrar = 10
                for i, componente in enumerate(lista[:num_componentes_mostrar]):
                    sub_menu_componente = QMenu(componente[2], main_window)
                    
                    # Acción editar (CORREGIDO *args)
                    accion_editar = QAction("Editar", main_window)
                    accion_editar.triggered.connect(lambda *args, p=componente: MainView.mostrar_editar_componente(p))
                    sub_menu_componente.addAction(accion_editar)
                    
                    # Acción eliminar (CORREGIDO *args)
                    accion_eliminar = QAction("Eliminar", main_window)
                    accion_eliminar.triggered.connect(lambda *args, p=componente: MainView.mostrar_eliminar_componente(p))
                    sub_menu_componente.addAction(accion_eliminar)
                    
                    menu.addMenu(sub_menu_componente)
                    if i < len(lista[:num_componentes_mostrar]) - 1:
                        menu.addSeparator()
                
                if len(lista) > num_componentes_mostrar:
                    menu.addSeparator()
                    submenu_mostrar_mas = QMenu("Mostrar más...", main_window)
                    for componente in lista[num_componentes_mostrar:]:
                        sub_menu_componente = QMenu(componente[2], main_window)
                        
                        # accion editar (CORREGIDO *args)
                        accion_editar = QAction("Editar", main_window)
                        accion_editar.triggered.connect(lambda *args, p=componente: MainView.mostrar_editar_componente(p))
                        sub_menu_componente.addAction(accion_editar)
                        
                        # acción eliminar (CORREGIDO *args)
                        accion_eliminar = QAction("Eliminar", main_window)
                        accion_eliminar.triggered.connect(lambda *args, p=componente: MainView.mostrar_eliminar_componente(p))
                        sub_menu_componente.addAction(accion_eliminar)
                        
                        submenu_mostrar_mas.addMenu(sub_menu_componente)
                    menu.addMenu(submenu_mostrar_mas)
            menu.installEventFilter(MenuEventFilter(menu, main_window))
            
    def mostrar_editar_componente(componente):
        idcomponente, _, nombrecompo, _ = componente
        stacked_widget = MainView.main_window.findChild(QStackedWidget, "stackedWidget_principal")
        indexactual = stacked_widget.currentIndex()
        result = False
        if indexactual == 1:
            treewidget = DatosView.main.findChild(QTreeWidget, "tree_actual_datos")
            result = CrearProyecto.dialogo_editar_componente(idcomponente, nombrecompo, treewidget, DatosView.reiniciarVistasAfectadas)
        elif indexactual == 2:
            treewidget = VisorView.main.findChild(QTreeWidget, "tree_actual_visor")
            result = CrearProyecto.dialogo_editar_componente(idcomponente, nombrecompo, treewidget, VisorView.reiniciarVistasAfectadas)
        elif indexactual == 3:
            treewidget = DesplazamientoView.main.findChild(QTreeWidget, "tree_actual_desplazamiento")
            result = CrearProyecto.dialogo_editar_componente(idcomponente, nombrecompo, treewidget, DesplazamientoView.reiniciarVistasAfectadas)
        elif indexactual == 4:
            treewidget = VelocidadView.main.findChild(QTreeWidget, "tree_actual_velocidad")
            result = CrearProyecto.dialogo_editar_componente(idcomponente, nombrecompo, treewidget, VelocidadView.reiniciarVistasAfectadas)
        elif indexactual == 5:
            treewidget = InclinometrosView.main.findChild(QTreeWidget, "tree_actual_inclinometros")
            result = CrearProyecto.dialogo_editar_componente(idcomponente, nombrecompo, treewidget, InclinometrosView.reiniciarVistasAfectadas)
        elif indexactual == 6:
            treewidget = PiezometrosView.main.findChild(QTreeWidget, "tree_actual_piezometros")
            result = CrearProyecto.dialogo_editar_componente(idcomponente, nombrecompo, treewidget, PiezometrosView.reiniciarVistasAfectadas)
        elif indexactual == 7:
            treewidget = CeldasView.main.findChild(QTreeWidget, "tree_actual_celdas")
            result = CrearProyecto.dialogo_editar_componente(idcomponente, nombrecompo, treewidget, CeldasView.reiniciarVistasAfectadas)
        elif indexactual == 8:
            treewidget = AcelerografosView.main.findChild(QTreeWidget, "tree_actual_acelerografos")
            result = CrearProyecto.dialogo_editar_componente(idcomponente, nombrecompo, treewidget, AcelerografosView.reiniciarVistasAfectadas)
        elif indexactual == 9:
            treewidget = SondajetdrView.main.findChild(QTreeWidget, "tree_actual_tdr")
            result = CrearProyecto.dialogo_editar_componente(idcomponente, nombrecompo, treewidget, SondajetdrView.reiniciarVistasAfectadas)
        elif indexactual == 10:
            treewidget = AnalisisView.main.findChild(QTreeWidget, "tree_actual_analisis")
            result = CrearProyecto.dialogo_editar_componente(idcomponente, nombrecompo, treewidget, AnalisisView.reiniciarVistasAfectadas)
        else:
            result = CrearProyecto.dialogo_editar_componente_reporte(idcomponente, nombrecompo, ReporteView.reiniciarVistasAfectadas)
        if result:
            # Actualizar los componentes
            actionListaComponentes = MainView.main_window.findChild(QAction, 'action_lista_componentes')
            if actionListaComponentes:
                menu_componentes = actionListaComponentes.menu()
                if menu_componentes is None:
                    menu_componentes = QMenu("Lista de Componentes", MainView.main_window)
                    actionListaComponentes.setMenu(menu_componentes)
                MainView.listar_componentes_proyecto(menu_componentes, MainView.main_window)
    
    def mostrar_eliminar_componente(componente):
        idcomponente, idproyecto, nombrecompo, _ = componente
        stacked_widget = MainView.main_window.findChild(QStackedWidget, "stackedWidget_principal")
        indexactual = stacked_widget.currentIndex()
        result = False
        if indexactual == 1:
            treewidget = DatosView.main.findChild(QTreeWidget, "tree_actual_datos")
            result = CrearProyecto.eliminar_componente(idproyecto, idcomponente, nombrecompo, treewidget, DatosView.reiniciarVistasAfectadas)
        elif indexactual == 2:
            treewidget = VisorView.main.findChild(QTreeWidget, "tree_actual_visor")
            result = CrearProyecto.eliminar_componente(idproyecto, idcomponente, nombrecompo, treewidget, VisorView.reiniciarVistasAfectadas)
        elif indexactual == 3:
            treewidget = DesplazamientoView.main.findChild(QTreeWidget, "tree_actual_desplazamiento")
            result = CrearProyecto.eliminar_componente(idproyecto, idcomponente, nombrecompo, treewidget, DesplazamientoView.reiniciarVistasAfectadas)
        elif indexactual == 4:
            treewidget = VelocidadView.main.findChild(QTreeWidget, "tree_actual_velocidad")
            result = CrearProyecto.eliminar_componente(idproyecto, idcomponente, nombrecompo, treewidget, VelocidadView.reiniciarVistasAfectadas)
        elif indexactual == 5:
            treewidget = InclinometrosView.main.findChild(QTreeWidget, "tree_actual_inclinometros")
            result = CrearProyecto.eliminar_componente(idproyecto, idcomponente, nombrecompo, treewidget, InclinometrosView.reiniciarVistasAfectadas)
        elif indexactual == 6:
            treewidget = PiezometrosView.main.findChild(QTreeWidget, "tree_actual_piezometros")
            result = CrearProyecto.eliminar_componente(idproyecto, idcomponente, nombrecompo, treewidget, PiezometrosView.reiniciarVistasAfectadas)
        elif indexactual == 7:
            treewidget = CeldasView.main.findChild(QTreeWidget, "tree_actual_celdas")
            result = CrearProyecto.eliminar_componente(idproyecto, idcomponente, nombrecompo, treewidget, CeldasView.reiniciarVistasAfectadas)
        elif indexactual == 8:
            treewidget = AcelerografosView.main.findChild(QTreeWidget, "tree_actual_acelerografos")
            result = CrearProyecto.eliminar_componente(idproyecto, idcomponente, nombrecompo, treewidget, AcelerografosView.reiniciarVistasAfectadas)
        elif indexactual == 9:
            treewidget = SondajetdrView.main.findChild(QTreeWidget, "tree_actual_tdr")
            result = CrearProyecto.eliminar_componente(idproyecto, idcomponente, nombrecompo, treewidget, SondajetdrView.reiniciarVistasAfectadas)
        elif indexactual == 10:
            treewidget = AnalisisView.main.findChild(QTreeWidget, "tree_actual_analisis")
            result = CrearProyecto.eliminar_componente(idproyecto, idcomponente, nombrecompo, treewidget, AnalisisView.reiniciarVistasAfectadas)
        else:
            result = CrearProyecto.eliminar_componente_reporte(idproyecto, idcomponente, nombrecompo, ReporteView.reiniciarVistasAfectadas)
        if result:
            # Actualizar los componentes
            actionListaComponentes = MainView.main_window.findChild(QAction, 'action_lista_componentes')
            if actionListaComponentes:
                menu_componentes = actionListaComponentes.menu()
                if menu_componentes is None:
                    menu_componentes = QMenu("Lista de Componentes", MainView.main_window)
                    actionListaComponentes.setMenu(menu_componentes)
                MainView.listar_componentes_proyecto(menu_componentes, MainView.main_window)
    
    def dialogo_acciones_proyecto(proyecto_id, proyecto_nombre, menu, main_window):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Question)
        msg.setText(f"¿Desea editar o eliminar el proyecto '{proyecto_nombre}'?")
        msg.setInformativeText("Seleccione un opción.")
        msg.setWindowTitle(f"Proyecto {proyecto_nombre.upper()}")
        # Botones personalizados
        btn_editar = msg.addButton("Editar", QMessageBox.AcceptRole)
        btn_eliminar = msg.addButton("Eliminar", QMessageBox.DestructiveRole)
        btn_cancelar = msg.addButton("Cancelar", QMessageBox.RejectRole)
        msg.exec()
        # Comprobamos qué botón se presionó
        if msg.clickedButton() == btn_editar:
            respuesta = CrearProyecto.formularioActualizarProyecto(proyecto_id)
            if respuesta:
                if MainView.proyecto_id == proyecto_id:
                    proyecto = ProyectoController.ctrlObtenerInfoProyecto(proyecto_id)
                    MainView.manejar_proyecto_seleccionado(proyecto, main_window)
                MainView.listar_proyectos_recientes(menu, main_window)
        elif msg.clickedButton() == btn_eliminar:
            respuesta = ProyectoController.ctrlEliminarProyecto(proyecto_id)
            if respuesta:
                if MainView.proyecto_id == proyecto_id:
                    MainView.proyecto_id = None
                    MainView.proyecto_name = "SIN PROYECTO"
                    MainView.main_window.setWindowTitle(f"E-MONITORING {MainView.version} - {MainView.proyecto_name.upper()}")
                    MainView.reiniciarAplicacion(MainView.main_window, MainView.proyecto_id, MainView.proyecto_name)
                MainView.listar_proyectos_recientes(menu, main_window)
    
    def manejar_proyecto_seleccionado(proyecto, main):
        MainView.proyecto_id = proyecto[0]
        MainView.proyecto_name = proyecto[1]
        MainView.main_window.setWindowTitle(f"E-MONITORING {MainView.version} - {MainView.proyecto_name.upper()}")
        MainView.reiniciarAplicacion(main, proyecto[0], proyecto[1])
        # Actualizar los componentes
        actionListaComponentes = MainView.main_window.findChild(QAction, 'action_lista_componentes')
        if actionListaComponentes:
            menu_componentes = actionListaComponentes.menu()
            if menu_componentes is None:
                menu_componentes = QMenu("Lista de Componentes", MainView.main_window)
                actionListaComponentes.setMenu(menu_componentes)
            MainView.listar_componentes_proyecto(menu_componentes, MainView.main_window)
    
    def reiniciarAplicacion(main, proyecto_id, proyecto_name):
        pagina = MainView.main_window.findChild(QStackedWidget, "stackedWidget_principal").currentIndex()
        MainView.actualizarRangoFechas()
        DashboardView.reiniciarVistaDashboard(main, proyecto_id, proyecto_name)
        DatosView.reiniciarVistaDatos(main, proyecto_id, proyecto_name)
        VisorView.reiniciarVistaVisor(main, proyecto_id, proyecto_name)
        DesplazamientoView.reiniciarVistaDesplazamiento(main, proyecto_id, proyecto_name)
        VelocidadView.reiniciarVistaVelocidad(main, proyecto_id, proyecto_name)
        InclinometrosView.reiniciarVistaInclinometros(main, proyecto_id, proyecto_name)
        PiezometrosView.reiniciarVistaPiezometros(main, proyecto_id, proyecto_name)
        CeldasView.reiniciarVistaCeldas(main, proyecto_id, proyecto_name)
        AcelerografosView.reiniciarVistaAcelerografos(main, proyecto_id, proyecto_name)
        SondajetdrView.reiniciarVistaTDR(main, proyecto_id, proyecto_name)
        AnalisisView.reiniciarVistaAnalisis(main, proyecto_id, proyecto_name)
        ReporteView.reiniciarVistaReporte(main, proyecto_id, proyecto_name)
        MainView.verificarTipoVista(pagina, main, proyecto_id, proyecto_name)
    
    def verificarTipoVista(pagina, main, proyecto_id, proyecto_name):
        if pagina == 0: # Dashboard
            DashboardView.inicializarVistaDashboard(main, proyecto_id)
        elif pagina == 1: # Datos
            DatosView.inicializarVistaDatos(main, proyecto_id, proyecto_name)
        elif pagina == 2: # Visor
            VisorView.inicializarVistaVisor(main, proyecto_id, proyecto_name, MainView.prismafechainicial, MainView.prismafechafinal)
        elif pagina == 3: # Desplazamiento
            DesplazamientoView.inicializarVistaDesplazamiento(main, proyecto_id, proyecto_name, MainView.prismafechainicial, MainView.prismafechafinal)
        elif pagina == 4: # Velocidad
            VelocidadView.inicializarVistaVelocidad(main, proyecto_id, proyecto_name, MainView.prismafechainicial, MainView.prismafechafinal)
        elif pagina == 5: # Inclinometros
            InclinometrosView.inicializarVistaInclinometros(main, proyecto_id, proyecto_name)
        elif pagina == 6: # Piezometros
            PiezometrosView.inicializarVistaPiezometros(main, proyecto_id, proyecto_name, MainView.piezocuerdafechainicial, MainView.piezocuerdafechafinal, MainView.piezomanualfechainicial, MainView.piezomanualfechafinal)
        elif pagina == 7: # Celdas
            CeldasView.inicializarVistaCeldas(main, proyecto_id, proyecto_name, MainView.celdafechainicial, MainView.celdafechafinal)
        elif pagina == 8: # Acelerografos
            AcelerografosView.inicializarVistaAcelerografos(main, proyecto_id, proyecto_name, MainView.acelerofechainicial, MainView.acelerofechafinal)
        elif pagina == 9: # TDR
            SondajetdrView.inicializarVistaSondajesTdr(main, proyecto_id, proyecto_name)
        elif pagina == 10: # Analisis
            AnalisisView.inicializarVistaAnalisis(main, proyecto_id, proyecto_name, MainView.prismafechainicial, MainView.prismafechafinal)
        elif pagina == 11: # Reporte
            ReporteView.inicializarVistaReporte(main, proyecto_id, proyecto_name)
        elif pagina == 12: # Usuarios
            UsuariosView.inicializarVistaUsuarios(main)
    
    def actualizarRangoFechas():
        if MainView.proyecto_id:
            MainView.prismafechainicial, MainView.prismafechafinal = PrismaController.ctrlObtenerFechasRango(MainView.proyecto_id)
            MainView.piezocuerdafechainicial, MainView.piezocuerdafechafinal = PiezometroController.ctrlObtenerFechasRangoPiezometrosCuerda(MainView.proyecto_id)
            MainView.piezomanualfechainicial, MainView.piezomanualfechafinal = PiezometroController.ctrlObtenerFechasRangoPiezometrosManual(MainView.proyecto_id)
            MainView.celdafechainicial, MainView.celdafechafinal = CeldaController.ctrlObtenerFechasRango(MainView.proyecto_id)
            MainView.acelerofechainicial, MainView.acelerofechafinal = AcelerografoController.ctrlObtenerFechasRango(MainView.proyecto_id)
            fechaacelero = datetime.strptime(MainView.acelerofechainicial, "%Y-%m-%d %H:%M:%S")
            solofechaacelero = str(fechaacelero.date())
            MainView.acelerografofecha, MainView.acelerohorainicial, MainView.acelerohorafinal = solofechaacelero, "00:00:00", "23:59:59"
        
    def crearNuevoProyecto(main):
        respuesta, idproyecto = CrearProyecto.formularioRegistroNuevoProyecto()
        if respuesta and idproyecto:
            proyecto = ProyectoController.ctrlObtenerInfoProyecto(idproyecto)
            MainView.manejar_proyecto_seleccionado(proyecto, main)
            # Actualizar los proyectos recientes
            actionProyectos_Recientes = MainView.main_window.findChild(QAction, 'action_proyectos_recientes')
            if actionProyectos_Recientes:
                menu_proyectos_recientes = actionProyectos_Recientes.menu()
                if menu_proyectos_recientes is None:
                    menu_proyectos_recientes = QMenu("Proyectos Recientes", MainView.main_window)
                    actionProyectos_Recientes.setMenu(menu_proyectos_recientes)
                MainView.listar_proyectos_recientes(menu_proyectos_recientes, MainView.main_window)
            # Actualizar los componentes
            actionListaComponentes = MainView.main_window.findChild(QAction, 'action_lista_componentes')
            if actionListaComponentes:
                menu_componentes = actionListaComponentes.menu()
                if menu_componentes is None:
                    menu_componentes = QMenu("Lista de Componentes", MainView.main_window)
                    actionListaComponentes.setMenu(menu_componentes)
                MainView.listar_componentes_proyecto(menu_componentes, MainView.main_window)
    
    def registrarComponente():
        if MainView.proyecto_id:
            result = CrearProyecto.registro_componente(MainView.proyecto_id)
            if result:
                # Actualizar los componentes
                actionListaComponentes = MainView.main_window.findChild(QAction, 'action_lista_componentes')
                if actionListaComponentes:
                    menu_componentes = actionListaComponentes.menu()
                    if menu_componentes is None:
                        menu_componentes = QMenu("Lista de Componentes", MainView.main_window)
                        actionListaComponentes.setMenu(menu_componentes)
                    MainView.listar_componentes_proyecto(menu_componentes, MainView.main_window)
        else:
            mostrar_mensaje("Sin Proyecto", "Inicie un proyecto primero.", "advertencia")
    
    def subirArchivoPrismasAutomatizados():
        if MainView.proyecto_id:
            SubirPrismas.cargarPrismasAutomatizados(MainView.main_window, MainView.proyecto_id)
            MainView.actualizarRangoFechas()
        else:
            mostrar_mensaje('Sin Proyecto', 'Inicie un proyecto primero.','advertencia')
            
    def pegarDataPrismasManuales():
        if MainView.proyecto_id:
            SubirPrismas.cargarPrismasManuales(MainView.main_window, MainView.proyecto_id)
            MainView.actualizarRangoFechas()
        else:
            mostrar_mensaje('Sin Proyecto', 'Inicie un proyecto primero.','advertencia')
    
    def subirFormatoPrismas():
        if MainView.proyecto_id:
            SubirPrismas.cargarDataFormatosPrismas(MainView.main_window, MainView.proyecto_id)
            MainView.actualizarRangoFechas()
        else:
            mostrar_mensaje('Sin Proyecto', 'Inicie un proyecto primero.','advertencia')
            
    def subir_topografia():
        if MainView.proyecto_id:
            SubirTopografias.dialogoNuevaTopografia(MainView.proyecto_id, MainView.main_window)
        else:
            mostrar_mensaje('Sin Proyecto', 'Inicie un proyecto primero.','advertencia')
            
    def subir_inclinometros():
        if MainView.proyecto_id:
            SubirInclinometros.cargarInclinometros(MainView.main_window, MainView.proyecto_id)
        else:
            mostrar_mensaje('Error', 'No existe proyecto cargado', 'error')
            
    def crearNuevoPiezometroCuerda():
        if MainView.proyecto_id:
            RegistroEquipos.dialogoNuevoPiezometroCuerda(MainView.proyecto_id)
        else:
            mostrar_mensaje('Sin Proyecto', 'Inicie un proyecto primero.','advertencia')
    
    def crearNuevoPiezometroManual():
        if MainView.proyecto_id:
            RegistroEquipos.dialogoNuevoPiezometroManual(MainView.proyecto_id)
        else:
            mostrar_mensaje('Sin Proyecto', 'Inicie un proyecto primero.','advertencia')
    
    def registrarNuevaCotaPiezometrica():
        if MainView.proyecto_id:
            SubirPiezometros.dialogoNuevaCotaPiezometrica(MainView.proyecto_id)
        else:
            mostrar_mensaje('Sin Proyecto', 'Inicie un proyecto primero.','advertencia')
    
    def crearFormulaPiezometroCuerda():
        RegistroEquipos.mostrarCalculadora()
    
    def subirDataPiezometroCuerda():
        if MainView.proyecto_id:
            SubirPiezometros.cargarPiezometrosCuerda(MainView.main_window, MainView.proyecto_id)
            MainView.actualizarRangoFechas()
    
    def subirFormatoPiezometroCuerda():
        if MainView.proyecto_id:
            SubirPiezometros.cargarDataFormatosCuerda(MainView.main_window, MainView.proyecto_id, "FORMATO")
            MainView.actualizarRangoFechas()
    
    def subirExcelPiezometroCuerda():
        if MainView.proyecto_id:
            SubirPiezometros.cargarDataFormatosCuerda(MainView.main_window, MainView.proyecto_id, "EXCEL")
            MainView.actualizarRangoFechas()
    
    def subirDataPiezometroManual():
        if MainView.proyecto_id:
            SubirPiezometros.cargarPiezometrosCasagrande(MainView.main_window, MainView.proyecto_id)
            MainView.actualizarRangoFechas()
    
    def subirFormatoPiezometroManual():
        if MainView.proyecto_id:
            SubirPiezometros.cargarDataFormatosCasagrande(MainView.main_window, MainView.proyecto_id)
            MainView.actualizarRangoFechas()
    
    def registrarUmbralPersonalizado():
        UmbralView.modalUmbralesPersonalizado(MainView.proyecto_id)
        
    def configurarUmbralesInstrumentacion(tipo):
        if MainView.proyecto_id:
            pagina = MainView.main_window.findChild(QStackedWidget, "stackedWidget_principal").currentIndex()
            if tipo == 'PRISMAS':
                if pagina == 3:
                    combotipomedida = MainView.main_window.findChild(QComboBox, "combo_medida_desplaza")
                    unidadmedida = combotipomedida.currentData()
                    if unidadmedida == 1:
                        unidad1, unidad2 = 1, 1
                        medida1, medida2 = "m", "m/d"
                    elif unidadmedida == 100:
                        unidad1, unidad2 = 100, 1
                        medida1, medida2 = "cm", "m/d"
                    else:
                        unidad1, unidad2 = 1000, 1
                        medida1, medida2 = "mm", "m/d"
                elif pagina == 4:
                    combotipomedida = VelocidadView.main.findChild(QComboBox, "combo_medida_velocidad")
                    unidadmedida = combotipomedida.currentData()
                    if unidadmedida == "MD":
                        unidad1, unidad2 = 1, 1
                        medida1, medida2 = "m", "m/d"
                    elif unidadmedida == "CMD":
                        unidad1, unidad2 = 1, 100
                        medida1, medida2 = "m", "cm/d"
                    elif unidadmedida == "MMD":
                        unidad1, unidad2 = 1, 1000
                        medida1, medida2 = "m", "mm/d"
                    elif unidadmedida == "MH":
                        unidad1, unidad2 = 1, 1/24
                        medida1, medida2 = "m", "m/h"
                    elif unidadmedida == "CMH":
                        unidad1, unidad2 = 1, 100/24
                        medida1, medida2 = "m", "cm/h"
                    else:
                        unidad1, unidad2 = 1, 1000/24
                        medida1, medida2 = "m", "mm/h"
                else:
                    unidad1, unidad2 = 1, 1
                    medida1, medida2 = "m", "m/d"
                UmbralView.modalUmbralesPrismas(MainView.proyecto_id, tipo, unidad1, unidad2, medida1, medida2)
            elif tipo == 'INCLINOMETROS':
                if pagina == 5:
                    combo_medidas = InclinometrosView.main.findChild(QComboBox, "combo_medida_inclinometros")
                    unidadmedida = combo_medidas.currentData()
                else:
                    unidadmedida = 1
                UmbralView.modalUmbralesInclinometros(MainView.proyecto_id, tipo, unidadmedida)
            elif tipo == 'ACELEROGRAFOS':
                UmbralView.modalUmbralesAcelerografos(MainView.proyecto_id)
            elif tipo == 'CELDAS': # piezometros y celdas
                if pagina == 7:
                    combo_medidas = CeldasView.main.findChild(QComboBox, "combo_medida_celdas")
                    unidad = combo_medidas.currentData()
                    combotipovelocidad = CeldasView.main.findChild(QComboBox, "cb_tipo_calculo_velocidad_celda")
                    tipovelocidad = combotipovelocidad.currentText()
                else:
                    unidad = 1
                    tipovelocidad = "Por Mes"
                UmbralView.modalUmbralesCeldas(MainView.proyecto_id, tipo, unidad, tipovelocidad)
            else:
                if pagina == 6:
                    combo_medidas = PiezometrosView.main.findChild(QComboBox, "combo_medida_piezometros")
                    unidad = combo_medidas.currentData()
                else:
                    unidad = 1
                UmbralView.modalUmbralesPiezometros(MainView.proyecto_id, tipo, unidad)
        else:
            mostrar_mensaje('Sin Proyecto', 'Inicie un proyecto primero.','advertencia')
    
    def check_stacked_widget():
        # Encuentra el QStackedWidget principal
        stacked_widget_principal = MainView.main_window.findChild(QStackedWidget, "stackedWidget_principal")
        btn_visor = MainView.main_window.findChild(QToolButton, "btn_menu_bar")
        # Encuentra el QStackedWidget que quieres ocultar o mostrar
        stacked_widget_lista_checks = MainView.main_window.findChild(QStackedWidget, "stacked_lista_checks")
        # Verifica si el índice actual del QStackedWidget principal es 11 u 12
        if stacked_widget_principal and stacked_widget_lista_checks and btn_visor:
            if stacked_widget_principal.currentIndex() == 11 or stacked_widget_principal.currentIndex() == 12 or stacked_widget_principal.currentIndex() ==0:
                stacked_widget_lista_checks.hide()
                btn_visor.hide()
            else:
                if MainView.mostrararbol:
                    stacked_widget_lista_checks.show()
                else:
                    stacked_widget_lista_checks.hide()
                btn_visor.show()
    
    def cerrarSesion():
        QApplication.quit()
        # cerrar sesion
        # Session.logout()
        # MainView.main_window.close()
        # from views.login import Login
        # from views.principal import Principal
        # dialogologin = Login.mostrarLogin()
        # dialogologin.show()
        # Principal.validarInicioSesion(dialogologin)
    