import threading
from PySide6.QtCore import Qt, QTimer
from datetime import datetime
from PySide6.QtWidgets import (QWidget, QTreeWidget, QPushButton, QComboBox, QLineEdit)
from modules.acelerografos.graficarAcelerografos import procesar_grafica_acelerografos
from modules.acelerografos.graficarAcelerografos import limpiar_widget
from controllers.AcelerografoController import AcelerografoController
from controllers.ConfiguracionController import ConfiguracionController
from modules.datos.equiposAcelerografos import EquiposAcelerografos
from utils.common.metodosGenerales import MetodosGenerales
from utils.shared.personalizacion import Personalizacion
from modules.empresa.softwareconfiguracion import SoftwareConfiguracion
from utils.shared.guardarImagenReporte import ReporteImage
from utils.shared.graficareporte import GraficaReporte
from utils.shared.asistentedevoz import AsistenteVoz
from modules.acelerografos.graficarArchivos import procesar_graficos_acelerografos
from modules.acelerografos.graficarArchivos import generar_csvs_para_fecha
from utils.shared.graficarUmbrales import GraficarUmbrales
from controllers.UmbralController import UmbralController

class AcelerografosView:
    main = None
    idproyecto = None
    nameproyecto = "SIN PROYECTO"
    estadochecklist = True
    estadoPagina = True
    fechainicial, fechafinal = MetodosGenerales.obtenerRangoFechas(365)
    fechaacelero = datetime.strptime(fechainicial, "%Y-%m-%d %H:%M:%S")
    solofechaacelero = str(fechaacelero.date())
    acelerografofecha = solofechaacelero
    horainicial = "00:00:00"
    horafinal = "23:59:59"
    timer_busqueda = None
    
    def inicializarVistaAcelerografos(main, proyectoid, proyectoname, fechaini, fechafin):
        AcelerografosView.main = main
        AcelerografosView.idproyecto = proyectoid
        AcelerografosView.nameproyecto = proyectoname
        AcelerografosView.fechainicial, AcelerografosView.fechafinal = fechaini, fechafin
        if AcelerografosView.estadochecklist:
            tree_widget = main.findChild(QTreeWidget, "tree_actual_acelerografos")
            tree_widget.setHeaderLabels([AcelerografosView.nameproyecto.upper()])
            EquiposAcelerografos.inicializar_lista_equipos(tree_widget, AcelerografosView.idproyecto, AcelerografosView.nameproyecto)
            AcelerografosView.estadochecklist = False
        if AcelerografosView.estadoPagina:
            tree_actual =  AcelerografosView.main.findChild(QTreeWidget, "tree_actual_acelerografos")
            tree_actual.itemClicked.connect(AcelerografosView.checkProyectoActualAcelerografos)
            # --- Buscador de equipos en el árbol ---
            buscador_arbol = AcelerografosView.main.findChild(QLineEdit, "input_buscar_acelerografos")
            if buscador_arbol is None:
                buscador_arbol = QLineEdit()
                buscador_arbol.setObjectName("input_buscar_acelerografos")
                buscador_arbol.setPlaceholderText("Buscar equipo...")
                layout_padre = tree_actual.parentWidget().layout()
                if layout_padre is not None:
                    indice_tree = layout_padre.indexOf(tree_actual)
                    layout_padre.insertWidget(indice_tree, buscador_arbol)

                AcelerografosView.timer_busqueda = QTimer()
                AcelerografosView.timer_busqueda.setSingleShot(True)
                AcelerografosView.timer_busqueda.timeout.connect(
                    lambda: EquiposAcelerografos.filtrarArbolPorTexto(tree_actual, buscador_arbol.text())
                )
                buscador_arbol.textChanged.connect(
                    lambda: (AcelerografosView.timer_busqueda.stop(),
                                AcelerografosView.timer_busqueda.start(250))
                )
            
            tree_actual.setContextMenuPolicy(Qt.CustomContextMenu)
            tree_actual.customContextMenuRequested.connect(AcelerografosView.clicderechoProyectoActualAcelerografos)
            # CARGAR COMBO TIPO DE GRÁFICAS
            comboAcelerografos_grafico = main.findChild(QComboBox, "cb_tipo_grafico_acelerografos")
            tiposacelerografo = {
                "Aceleración (m/s²)": "AAC",
                "Aceleración (g)": "AAG",
                "Velocidad": "AVE",
                "Desplazamiento": "ADE",
                "Magnitud": "AMA"
            }
            for valor, id in tiposacelerografo.items():
                comboAcelerografos_grafico.addItem(valor, id)
            comboAcelerografos_grafico.activated.connect(lambda: AcelerografosView.obtenerMostrarAcelerografosMarcados(tree_actual))
            # Botones
            widget_grafico = main.findChild(QWidget, "widget_acelerografos")
            btn_refrescar_acelerografos = main.findChild(QPushButton, "btn_refrescar_vista_acelerografos")
            btn_refrescar_acelerografos.clicked.connect(lambda: AcelerografosView.obtenerMostrarAcelerografosMarcados(tree_actual))
            btnEjesacelero = main.findChild(QPushButton, "btn_ejes_acelerografos")
            btnEjesacelero.clicked.connect(lambda: AcelerografosView.mostrarModalConfiguracionEjes(tree_actual))
            btn_guardar_grafico_reporte = main.findChild(QPushButton, "btn_reporte_grafica_acelerografos")
            btn_guardar_grafico_reporte.clicked.connect(lambda: AcelerografosView.mostrarDialogoReporteAcelerografos(tree_actual, widget_grafico, "Anexos"))
            btnReporteGeneral = main.findChild(QPushButton, "btn_imagen_acelerografos")
            btnReporteGeneral.clicked.connect(lambda: AcelerografosView.mostrarDialogoReporteAcelerografos(tree_actual, widget_grafico, "General"))
            btnAsistenteVoz = AcelerografosView.main.findChild(QPushButton, "btn_voz_acelerografos")
            btnAsistenteVoz.clicked.connect(lambda: AcelerografosView.iniciarAsistenteVozAcelerografos(tree_actual, btnAsistenteVoz))
            btngenerarcsv = main.findChild(QPushButton, "btn_generar_csv")
            btngenerarcsv.clicked.connect(lambda:AcelerografosView.generar_csv(tree_actual))
            btnUmbralAcelero = main.findChild(QPushButton, "btn_umbral_acelerografo")
            btnUmbralAcelero.clicked.connect(lambda: AcelerografosView.graficarUmbralesAcelerografos(widget_grafico))
            AcelerografosView.estadoPagina = False
    
    def generar_csv(tree_actual):
        comboAcelerografos_grafico = AcelerografosView.main.findChild(QComboBox, "cb_tipo_grafico_acelerografos")
        tipografica = comboAcelerografos_grafico.currentData()
        idacelerografo, unidadg = None, False
        if tipografica == "AAG":
            tipografica='AAC'
            unidadg = True
        lista = EquiposAcelerografos.obtener_todos_elementos_marcados(tree_actual)
        if lista:
            aceleromarcados = AcelerografosView.obtenerListaEquiposMarcados(lista, "Acelerógrafos")
            for componente, listaacelero in aceleromarcados:
                for acelero in listaacelero:
                    idacelerografo = acelero[2]
            if idacelerografo:
                fechafinal = datetime.strptime(AcelerografosView.fechafinal, "%Y-%m-%d %H:%M:%S")
                fechainicial = datetime.strptime(AcelerografosView.fechainicial, "%Y-%m-%d %H:%M:%S")
                año = fechafinal.year
                dia_del_anio = fechafinal.timetuple().tm_yday
                añodia = (año, dia_del_anio)
                hora_inicio = fechainicial.strftime("%H:%M:%S")
                hora_fin = fechafinal.strftime("%H:%M:%S")
                horario = (hora_inicio, hora_fin)
                if hora_inicio > hora_fin:
                    hora_inicio = fechafinal.strftime("%H:%M:%S")
                    hora_fin = fechainicial.strftime("%H:%M:%S")
                generar_csvs_para_fecha(AcelerografosView.idproyecto, idacelerografo,tipografica, añodia, horario, unidadg)
        
    def graficarUmbralesAcelerografos(widget_grafico):
        pintado = GraficarUmbrales.clean_on_widget(widget_grafico, 'color', tipo="ACELEROGRAFOS")
        if pintado is False:
            tree_actual =  AcelerografosView.main.findChild(QTreeWidget, "tree_actual_acelerografos")
            lista = EquiposAcelerografos.obtener_todos_elementos_marcados(tree_actual)
            if lista:
                umbrales = None
                comboAcelerografosGrafico = AcelerografosView.main.findChild(QComboBox, "cb_tipo_grafico_acelerografos")
                tipo = comboAcelerografosGrafico.currentData()
                aceleromarcados = AcelerografosView.obtenerListaEquiposMarcados(lista, "Acelerógrafos")
                if len(aceleromarcados) == 1:
                    for componente, listaacelero in aceleromarcados:
                        nombrecomponente, idcomponente, idproy = componente
                    umbrales = UmbralController.ctrlObtenerUmbralesInstrumentacion(AcelerografosView.idproyecto, idcomponente, tipo, 'umbral_acelerografo')
                    if umbrales:
                        GraficarUmbrales.draw_on_widget(widget_grafico, umbrales, 1, sentido='y', tipo_pintado='color', tipo="ACELEROGRAFOS")
    
    def checkProyectoActualAcelerografos(parent_item, column):
        treeWidget =  AcelerografosView.main.findChild(QTreeWidget, "tree_actual_acelerografos")
        EquiposAcelerografos.validarMarcadoCheckbox(parent_item, column, treeWidget, lambda: AcelerografosView.obtenerMostrarAcelerografosMarcados(treeWidget))
        
    def clicderechoProyectoActualAcelerografos(point):
        treeWidget =  AcelerografosView.main.findChild(QTreeWidget, "tree_actual_acelerografos")
        EquiposAcelerografos.validarOpcionesMenuCheckbox(point, treeWidget, AcelerografosView.reiniciarVistasAfectadas)
    
    def reiniciarVistasAfectadas(tipoequipo="Todos"):
        from views.datos_view import DatosView
        from views.visor_view import VisorView
        from views.desplazamiento_view import DesplazamientoView
        from views.velocidad_view import VelocidadView
        from views.inclinometros_view import InclinometrosView
        from views.piezometros_view import PiezometrosView
        from views.celdas_view import CeldasView
        from views.sondajestdr_view import SondajetdrView
        from views.analisis_view import AnalisisView
        if tipoequipo == "Acelerógrafo":
            DatosView.reiniciarVistaDatos(AcelerografosView.main, AcelerografosView.idproyecto, AcelerografosView.nameproyecto)
            VisorView.reiniciarVistaVisor(AcelerografosView.main, AcelerografosView.idproyecto, AcelerografosView.nameproyecto)
        else:
            DatosView.reiniciarVistaDatos(AcelerografosView.main, AcelerografosView.idproyecto, AcelerografosView.nameproyecto)
            VisorView.reiniciarVistaVisor(AcelerografosView.main, AcelerografosView.idproyecto, AcelerografosView.nameproyecto)
            DesplazamientoView.reiniciarVistaDesplazamiento(AcelerografosView.main, AcelerografosView.idproyecto, AcelerografosView.nameproyecto)
            VelocidadView.reiniciarVistaVelocidad(AcelerografosView.main, AcelerografosView.idproyecto, AcelerografosView.nameproyecto)
            InclinometrosView.reiniciarVistaInclinometros(AcelerografosView.main, AcelerografosView.idproyecto, AcelerografosView.nameproyecto)
            PiezometrosView.reiniciarVistaPiezometros(AcelerografosView.main, AcelerografosView.idproyecto, AcelerografosView.nameproyecto)
            CeldasView.reiniciarVistaCeldas(AcelerografosView.main, AcelerografosView.idproyecto, AcelerografosView.nameproyecto)
            SondajetdrView.reiniciarVistaTDR(AcelerografosView.main, AcelerografosView.idproyecto, AcelerografosView.nameproyecto)
            AnalisisView.reiniciarVistaAnalisis(AcelerografosView.main, AcelerografosView.idproyecto, AcelerografosView.nameproyecto)
    
    def obtenerMostrarAcelerografosMarcados(tree_actual):
        lista = EquiposAcelerografos.obtener_todos_elementos_marcados(tree_actual)
        if lista:
            aceleromarcados = AcelerografosView.obtenerListaEquiposMarcados(lista, "Acelerógrafos")
            if len(aceleromarcados) == 1:
                AcelerografosView.graficarAcelerografosMarcados(aceleromarcados)
            else:
                AcelerografosView.limpiarGraficaAcelerografos()
        else:
            AcelerografosView.limpiarGraficaAcelerografos()
    
    def obtenerListaEquiposMarcados(lista, tipolista):
        equiposmarcados = []
        for region, instrumentos in lista.items():
            for tipo, lista_equipos in instrumentos.items():
                if tipo[0] == tipolista:
                    equiposmarcados.append((region, lista_equipos))
        return equiposmarcados
            
    def graficarAcelerografosMarcados(aceleromarcados):
        comboAcelerografos_grafico = AcelerografosView.main.findChild(QComboBox, "cb_tipo_grafico_acelerografos")
        tipografica = comboAcelerografos_grafico.currentData()
        widget_acelerografos = AcelerografosView.main.findChild(QWidget, "widget_acelerografos")
        AcelerografosView.limpiarGraficaAcelerografos()
        if tipografica == "AMA": # Magnitud
            config = SoftwareConfiguracion.obtenerDataSoftware()
            filtrado = config[16]
            if filtrado == 0: # sin fechas
                datos = AcelerografoController.ctrlObtenerMagnitud(AcelerografosView.idproyecto, aceleromarcados)
            else:
                datos = AcelerografoController.ctrlObtenerMagnitudFechas(AcelerografosView.idproyecto, aceleromarcados, AcelerografosView.fechainicial, AcelerografosView.fechafinal)
            if len(datos) > 0:
                if filtrado == 0:
                    procesar_grafica_acelerografos(widget_acelerografos, AcelerografosView.idproyecto, datos)
                else:
                    procesar_grafica_acelerografos(widget_acelerografos, AcelerografosView.idproyecto, datos, AcelerografosView.fechainicial, AcelerografosView.fechafinal)
        else: # ACELERACION
            idacelerografo = None
            nombre_acelerografo = None
            unidadg, graficatipo = False, tipografica
            if tipografica == "AAG":
                unidadg = True
                graficatipo = "AAC"
            for componente, listaacelero in aceleromarcados:
                for acelero in listaacelero:
                    idacelerografo = acelero[2]
                    nombre_acelerografo = acelero[0]
            if idacelerografo:
                fechafinal = datetime.strptime(AcelerografosView.acelerografofecha, "%Y-%m-%d")
                año = fechafinal.year
                dia_del_anio = fechafinal.timetuple().tm_yday
                añodia = (año, dia_del_anio)
                hora_inicio = AcelerografosView.horainicial
                hora_fin = AcelerografosView.horafinal
                procesar_graficos_acelerografos(widget_acelerografos, graficatipo, AcelerografosView.idproyecto, idacelerografo, nombre_acelerografo, unidadg, añodia, hora_inicio, hora_fin)
    
    def limpiarGraficaAcelerografos():
        widget_acelerografos = AcelerografosView.main.findChild(QWidget, "widget_acelerografos")
        limpiar_widget(widget_acelerografos)
    
    def mostrarDialogoReporteAcelerografos(treeWidget, widget_grafico, tiporeporte):
        if AcelerografosView.idproyecto:
            lista = EquiposAcelerografos.obtener_todos_elementos_marcados(treeWidget)
            if lista:
                tipografico = "SISMO"
                titulografica = "Magnitud Acelerógrafo"
                tipoequipo = "Acelerografo"
                if tiporeporte == "General":
                    GraficaReporte.mostrarDialogoImagenVisor(widget_grafico, "Acelerografos", tipografico, titulografica, AcelerografosView.idproyecto, tipoequipo)
                else:
                    ReporteImage.modalImagenReporte(widget_grafico, "Acelerografos", tipografico, titulografica, AcelerografosView.idproyecto, tipoequipo)
    
    def actualizarVistaAcelerografos(fechaini, fechafin, acelerofofecha, horainicio, horafin):
        AcelerografosView.fechainicial = fechaini
        AcelerografosView.fechafinal = fechafin
        AcelerografosView.acelerografofecha = acelerofofecha
        AcelerografosView.horainicial = horainicio
        AcelerografosView.horafinal = horafin
        if AcelerografosView.idproyecto:
            treeWidget =  AcelerografosView.main.findChild(QTreeWidget, "tree_actual_acelerografos")
            AcelerografosView.obtenerMostrarAcelerografosMarcados(treeWidget)
    
    def reiniciarVistaAcelerografos(main, proyecto_id, proyecto_name):
        # reiniciar variables
        AcelerografosView.main = main
        AcelerografosView.idproyecto = proyecto_id
        AcelerografosView.nameproyecto = proyecto_name
        AcelerografosView.estadochecklist = True
        AcelerografosView.limpiarGraficaAcelerografos()
        # LIMPIAR EL BUSCADOR AL CAMBIAR DE PROYECTO
        buscador_arbol = main.findChild(QLineEdit, "input_buscar_acelerografos")
        if buscador_arbol is not None:
            buscador_arbol.blockSignals(True)
            buscador_arbol.clear()
            buscador_arbol.blockSignals(False)
    
    def mostrarModalConfiguracionEjes(treeWidget):
        lista = EquiposAcelerografos.obtener_todos_elementos_marcados(treeWidget)
        if lista:
            aceleromarcados = AcelerografosView.obtenerListaEquiposMarcados(lista, "Acelerógrafos")
            if len(aceleromarcados) > 0:
                comboAcelerografosGrafico = AcelerografosView.main.findChild(QComboBox, "cb_tipo_grafico_acelerografos")
                tipo = comboAcelerografosGrafico.currentData()
                unidadtiempo, tipomedida  = 1, 1
                infoeje = ConfiguracionController.ctrlObtenerConfiguracionEje(AcelerografosView.idproyecto, "ACELEROGRAFOS", tipo)
                if infoeje:
                    ejeymin, ejeymax, ejeyprim, ejeysecu, interdias = infoeje[4], infoeje[5], infoeje[6], infoeje[7], infoeje[8]
                else:
                    ejeymin, ejeymax, ejeyprim, ejeysecu, interdias = 0, 0, 0, 0, 0
                estadoeje, minejey, maxejey, primario, secundario, dias = Personalizacion.dialogoConfiguracionEjes(ejeymin, ejeymax, ejeyprim, ejeysecu, interdias, tipomedida, unidadtiempo)
                if estadoeje:
                    # guardar configuracion
                    respuesta = ConfiguracionController.ctrlActualizarConfiguracionEjes(AcelerografosView.idproyecto, "ACELEROGRAFOS", tipo, minejey, maxejey, primario, secundario, dias)
                    if respuesta:
                        AcelerografosView.graficarAcelerografosMarcados(aceleromarcados)
    
    def iniciarAsistenteVozAcelerografos(treeWidget, botonvoz):
        lista = EquiposAcelerografos.obtener_todos_elementos_marcados(treeWidget)
        if lista:
            aceleromarcados = AcelerografosView.obtenerListaEquiposMarcados(lista, "Acelerógrafos")
            if len(aceleromarcados) > 0:
                botonvoz.setEnabled(False)
                hilo_asistente = threading.Thread(target=AsistenteVoz.analizarAcelerografos, args=(AcelerografosView.idproyecto, aceleromarcados, AcelerografosView.fechainicial, AcelerografosView.fechafinal, botonvoz))
                hilo_asistente.start()
    