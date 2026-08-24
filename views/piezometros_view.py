import threading
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (QWidget, QLabel, QComboBox, QTreeWidget, QPushButton, QLineEdit)
from utils.common.metodosGenerales import MetodosGenerales
from utils.shared.graficaDesplazamientoVelocidad import procesar_grafica_piezometros
from utils.shared.graficaDesplazamientoVelocidad import limpiar_widget
from controllers.PiezometroController import PiezometroController
from controllers.PluviometroController import PluviometroController
from controllers.TerrenoController import TerrenoController
from controllers.ConfiguracionController import ConfiguracionController
from modules.datos.equiposPiezometros import EquiposPiezometros
from utils.shared.guardarImagenReporte import ReporteImage
from utils.shared.graficareporte import GraficaReporte
from utils.shared.asistentedevoz import AsistenteVoz
from utils.shared.personalizacion import Personalizacion
from utils.shared.calculostendencias import CalculosTendencias
from modules.empresa.softwareconfiguracion import SoftwareConfiguracion
from controllers.UmbralController import UmbralController
from utils.shared.graficarUmbrales import GraficarUmbrales
from utils.generic.graficarumbralespersonalizados import graficarUmbralesPersonalizado

class PiezometrosView:
    main = None
    idproyecto = None
    nameproyecto = "SIN PROYECTO"
    estadochecklist = True
    estadoPagina = True
    timer_busqueda = None
    cuerdafechainicial, cuerdafechafinal = MetodosGenerales.obtenerRangoFechas(365)
    manualfechainicial, manualfechafinal = MetodosGenerales.obtenerRangoFechas(365)
    
    def inicializarVistaPiezometros(main, proyectoid, proyectoname, fechainicuerda, fechafincuerda, fechainimanual, fechafinmanual):
        PiezometrosView.main = main
        PiezometrosView.idproyecto = proyectoid
        PiezometrosView.nameproyecto = proyectoname
        PiezometrosView.cuerdafechainicial, PiezometrosView.cuerdafechafinal = fechainicuerda, fechafincuerda
        PiezometrosView.manualfechainicial, PiezometrosView.manualfechafinal = fechainimanual, fechafinmanual
        if PiezometrosView.estadochecklist:
            tree_widget = main.findChild(QTreeWidget, "tree_actual_piezometros")
            tree_widget.setHeaderLabels([PiezometrosView.nameproyecto.upper()])
            EquiposPiezometros.inicializar_lista_equipos(tree_widget, PiezometrosView.idproyecto, PiezometrosView.nameproyecto)
            PiezometrosView.estadochecklist = False
        if PiezometrosView.estadoPagina:
            tree_actual_piezometros =  PiezometrosView.main.findChild(QTreeWidget, "tree_actual_piezometros")
            tree_actual_piezometros.itemClicked.connect(PiezometrosView.checkProyectoActualPiezometros)
            # --- Buscador de equipos en el árbol ---
            buscador_arbol = PiezometrosView.main.findChild(QLineEdit, "input_buscar_piezometros")
            if buscador_arbol is None:
                buscador_arbol = QLineEdit()
                buscador_arbol.setObjectName("input_buscar_piezometros")
                buscador_arbol.setPlaceholderText("Buscar equipo...")
                layout_padre = tree_actual_piezometros.parentWidget().layout()
                if layout_padre is not None:
                    indice_tree = layout_padre.indexOf(tree_actual_piezometros)
                    layout_padre.insertWidget(indice_tree, buscador_arbol)

                PiezometrosView.timer_busqueda = QTimer()
                PiezometrosView.timer_busqueda.setSingleShot(True)
                PiezometrosView.timer_busqueda.timeout.connect(
                    lambda: EquiposPiezometros.filtrarArbolPorTexto(tree_actual_piezometros, buscador_arbol.text())
                )
                buscador_arbol.textChanged.connect(
                    lambda: (PiezometrosView.timer_busqueda.stop(),
                                PiezometrosView.timer_busqueda.start(250))
                )

            tree_actual_piezometros.setContextMenuPolicy(Qt.CustomContextMenu)
            tree_actual_piezometros.customContextMenuRequested.connect(PiezometrosView.clicderechoProyectoActualPiezometros)
            # inicializar tools
            widget_grafico = main.findChild(QWidget, "widget_piezometros")
            btn_refrescar_piezometros = main.findChild(QPushButton, "btn_refrescar_vista_piezometros")
            btn_refrescar_piezometros.clicked.connect(lambda: PiezometrosView.obtenerMostrarEquiposMarcados(tree_actual_piezometros))
            btn_umbral_piezometro= main.findChild(QPushButton, "btn_umbral_piezometro")
            btn_umbral_piezometro.clicked.connect(PiezometrosView.graficarUmbralesPiezometros)
            # Cargar Unidades de Medida
            lista_unidades_medida = [
                ('Metros', 1),
                ('Centímetros', 100),
                ('Milímetros', 1000)
            ]
            combo_medidas = main.findChild(QComboBox, "combo_medida_piezometros")
            for value, key in lista_unidades_medida:
                combo_medidas.addItem(value, key)
            combo_medidas.activated.connect(lambda: PiezometrosView.obtenerMostrarEquiposMarcados(tree_actual_piezometros))
            # Cargar Unidades de Tiempo
            lista_unidades_tiempo = [
                ('Fechas', "FECHA"),
                ('Días', "DIA"),
                ('Horas', "HORA"),
            ]
            combo_tiempos = main.findChild(QComboBox, "combo_tiempo_piezometros")
            for value, key in lista_unidades_tiempo:
                combo_tiempos.addItem(value, key)
            combo_tiempos.activated.connect(lambda: PiezometrosView.obtenerMostrarEquiposMarcados(tree_actual_piezometros))
            # Cargamos tipos de desplazamiento
            lista_graficos_inclinometros = {
                'NF': 'Nivel Freático',
                'NI': 'Nivel Incremental',
                'NA': 'Nivel Acumulado',
                'PB': 'Presión Barométrica',
                'FP': 'Frecuencia',
                'TP': 'Temperatura',
            }
            combo_tipografico = main.findChild(QComboBox, "cb_tipo_graficas_piezometros")
            for key, value in lista_graficos_inclinometros.items():
                combo_tipografico.addItem(value, key)
            combo_tipografico.activated.connect(lambda: PiezometrosView.obtenerMostrarEquiposMarcados(tree_actual_piezometros))
            # botones
            btnAsistenteVoz = main.findChild(QPushButton, "btn_voz_piezometros")
            btnAsistenteVoz.clicked.connect(lambda: PiezometrosView.iniciarAsistenteVozPiezometros(tree_actual_piezometros, btnAsistenteVoz))
            btnLimpiarRuido = main.findChild(QPushButton, "btn_limpieza_piezometros")
            btnLimpiarRuido.clicked.connect(lambda: PiezometrosView.mostrarModalLimpiezaRuido(tree_actual_piezometros))
            btnTendencia = main.findChild(QPushButton, "btn_tendencia_piezometros")
            btnTendencia.clicked.connect(lambda: PiezometrosView.mostrarModalTendencia(tree_actual_piezometros))
            btnEjesPiezo = main.findChild(QPushButton, "btn_ejes_piezometros")
            btnEjesPiezo.clicked.connect(lambda: PiezometrosView.mostrarModalConfiguracionEjes(tree_actual_piezometros))
            btn_guardar_grafico_reporte = main.findChild(QPushButton, "btn_reporte_grafica_piezometro")
            btn_guardar_grafico_reporte.clicked.connect(lambda: PiezometrosView.mostrarDialogoReportePiezometros(tree_actual_piezometros, widget_grafico, combo_tipografico, "Anexos"))
            btnReporteGeneral = main.findChild(QPushButton, "btn_imagen_piezometros")
            btnReporteGeneral.clicked.connect(lambda: PiezometrosView.mostrarDialogoReportePiezometros(tree_actual_piezometros, widget_grafico, combo_tipografico, "General"))
            btnAplicarUmbralPersonalizado = main.findChild(QPushButton, "btn_umbral_personalizado_P")
            btnAplicarUmbralPersonalizado.clicked.connect(PiezometrosView.graficarUmbralesPersonalizado)
            PiezometrosView.estadoPagina = False
    
    def graficarUmbralesPersonalizado():
        if PiezometrosView.idproyecto:
            widget_grafico = PiezometrosView.main.findChild(QWidget, "widget_piezometros")
            combo_medidas = PiezometrosView.main.findChild(QComboBox, "combo_medida_piezometros")
            unidad = combo_medidas.currentData()
            combo_tipo_grafico = PiezometrosView.main.findChild(QWidget, "cb_tipo_graficas_piezometros")
            tipo = combo_tipo_grafico.currentData()
            if tipo == "NF":
                unimedida = 1
            elif tipo == "NI" or tipo == "NA":
                if unidad == 1:
                    unimedida = 1
                elif unidad == 100:
                    unimedida = 100
                else:
                    unimedida = 1000
            elif tipo == "PB":
                unimedida = 1
            elif tipo == "FP":
                unimedida = 1
            else:
                unimedida = 1
            graficarUmbralesPersonalizado(widget_grafico,unimedida,PiezometrosView.idproyecto)
            
    def graficarUmbralesPiezometros():
        # validar si está pintado, despintar
        widget_grafico = PiezometrosView.main.findChild(QWidget, "widget_piezometros")
        pintado = GraficarUmbrales.clean_on_widget(widget_grafico, 'color')
        if pintado is False:
            tree_widget = PiezometrosView.main.findChild(QTreeWidget, "tree_actual_piezometros")
            lista = EquiposPiezometros.obtener_todos_elementos_marcados(tree_widget)
            umbrales = None
            combo_tipo_grafico = PiezometrosView.main.findChild(QWidget, "cb_tipo_graficas_piezometros")
            tipo = combo_tipo_grafico.currentData()
            if lista:
                piezocuerdasmarcados, cotasmarcadas = PiezometrosView.obtenerListaPiezometrosMarcados(lista, "Piezómetros Cuerda Vibrante")
                if len(piezocuerdasmarcados) > 0:
                    if len(piezocuerdasmarcados) == 1:
                        for grupo in piezocuerdasmarcados:
                            for piezocu in grupo:
                                nombrepie, idinstru, idpiezo = piezocu
                        umbrales = UmbralController.ctrlObtenerUmbralesCodigoPiezometro(idpiezo, tipo, "PIEZOMETROCUERDA")
                        if umbrales is None:
                            validar = UmbralController.ctrlValidarUmbralesPiezometros(PiezometrosView.idproyecto, tipo, "PIEZOMETROCUERDA")
                            cantidad, idpiezome = validar
                            if cantidad > 0:
                                if cantidad == 1:
                                    umbrales = UmbralController.ctrlObtenerUmbralesCodigoPiezometro(idpiezome, tipo, "PIEZOMETROCUERDA")
                                else:
                                    # Traer lista de piezometros
                                    piezomecuerdas = UmbralController.ctrlListarPiezometrosUmbrales(PiezometrosView.idproyecto, tipo, "PIEZOMETROCUERDA", "piezometrocuerdas")
                                    if piezomecuerdas:
                                        codigoseleccionado = GraficarUmbrales.mostrarSeleccionUmbrales(piezomecuerdas, "Umbral Piezómetros")
                                        if codigoseleccionado:
                                            umbrales = UmbralController.ctrlObtenerUmbralesCodigoPiezometro(codigoseleccionado, tipo, "PIEZOMETROCUERDA")
                    else:
                        # VALIDAR SI HAY VARIOS UMBRALES
                        validar = UmbralController.ctrlValidarUmbralesPiezometros(PiezometrosView.idproyecto, tipo, "PIEZOMETROCUERDA")
                        cantidad, idpiezome = validar
                        if cantidad > 0:
                            if cantidad == 1:
                                umbrales = UmbralController.ctrlObtenerUmbralesCodigoPiezometro(idpiezome, tipo, "PIEZOMETROCUERDA")
                            else:
                                # Traer lista de piezometros
                                piezomecuerdas = UmbralController.ctrlListarPiezometrosUmbrales(PiezometrosView.idproyecto, tipo, "PIEZOMETROCUERDA", "piezometrocuerdas")
                                if piezomecuerdas:
                                    codigoseleccionado = GraficarUmbrales.mostrarSeleccionUmbrales(piezomecuerdas, "Umbral Piezómetros")
                                    if codigoseleccionado:
                                        umbrales = UmbralController.ctrlObtenerUmbralesCodigoPiezometro(codigoseleccionado, tipo, "PIEZOMETROCUERDA")
                else:
                    piezomanualesmarcados, cotasmarcadas = PiezometrosView.obtenerListaPiezometrosMarcados(lista, "Piezómetros Casagrande")
                    if len(piezomanualesmarcados) > 0:
                        if len(piezomanualesmarcados) == 1:
                            for grupo in piezomanualesmarcados:
                                for piezocu in grupo:
                                    nombrepie, idinstru, idpiezo = piezocu
                            umbrales = UmbralController.ctrlObtenerUmbralesCodigoPiezometro(idpiezo, tipo, "PIEZOMETROMANUAL")
                            if umbrales is None:
                                validar = UmbralController.ctrlValidarUmbralesPiezometros(PiezometrosView.idproyecto, tipo, "PIEZOMETROMANUAL")
                                cantidad, idpiezome = validar
                                if cantidad > 0:
                                    if cantidad == 1:
                                        umbrales = UmbralController.ctrlObtenerUmbralesCodigoPiezometro(idpiezome, tipo, "PIEZOMETROMANUAL")
                                    else:
                                        # Traer lista de piezometros
                                        piezomecuerdas = UmbralController.ctrlListarPiezometrosUmbrales(PiezometrosView.idproyecto, tipo, "PIEZOMETROMANUAL", "piezometromanuales")
                                        if piezomecuerdas:
                                            codigoseleccionado = GraficarUmbrales.mostrarSeleccionUmbrales(piezomecuerdas, "Umbral Piezómetros")
                                            if codigoseleccionado:
                                                umbrales = UmbralController.ctrlObtenerUmbralesCodigoPiezometro(codigoseleccionado, tipo, "PIEZOMETROMANUAL")
                        else:
                            # VALIDAR SI HAY VARIOS UMBRALES
                            validar = UmbralController.ctrlValidarUmbralesPiezometros(PiezometrosView.idproyecto, tipo, "PIEZOMETROMANUAL")
                            cantidad, idpiezome = validar
                            if cantidad > 0:
                                if cantidad == 1:
                                    umbrales = UmbralController.ctrlObtenerUmbralesCodigoPiezometro(idpiezome, tipo, "PIEZOMETROMANUAL")
                                else:
                                    # Traer lista de piezometros
                                    piezomecuerdas = UmbralController.ctrlListarPiezometrosUmbrales(PiezometrosView.idproyecto, tipo, "PIEZOMETROMANUAL", "piezometromanuales")
                                    if piezomecuerdas:
                                        codigoseleccionado = GraficarUmbrales.mostrarSeleccionUmbrales(piezomecuerdas, "Umbral Piezómetros")
                                        if codigoseleccionado:
                                            umbrales = UmbralController.ctrlObtenerUmbralesCodigoPiezometro(codigoseleccionado, tipo, "PIEZOMETROMANUAL")
                if umbrales:
                    combo_medidas = PiezometrosView.main.findChild(QComboBox, "combo_medida_piezometros")
                    unidad = combo_medidas.currentData()
                    if tipo == "NF":
                        unimedida = 1
                    elif tipo == "NI" or tipo == "NA":
                        if unidad == 1:
                            unimedida = 1
                        elif unidad == 100:
                            unimedida = 100
                        else:
                            unimedida = 1000
                    elif tipo == "PB":
                        unimedida = 1
                    elif tipo == "FP":
                        unimedida = 1
                    else:
                        unimedida = 1
                    GraficarUmbrales.draw_on_widget(widget_grafico, umbrales, unimedida, 'y', 'color')
    
    def checkProyectoActualPiezometros(parent_item, column):
        treeWidget =  PiezometrosView.main.findChild(QTreeWidget, "tree_actual_piezometros")
        EquiposPiezometros.validarMarcadoCheckboxPiezo(parent_item, column, treeWidget, lambda: PiezometrosView.obtenerMostrarEquiposMarcados(treeWidget))
        
    def clicderechoProyectoActualPiezometros(point):
        treeWidget =  PiezometrosView.main.findChild(QTreeWidget, "tree_actual_piezometros")
        EquiposPiezometros.validarOpcionesMenuCheckbox(point, treeWidget, "PIEZOMETROS", PiezometrosView.reiniciarVistasAfectadas)
    
    def reiniciarVistasAfectadas(tipoequipo="Todos"):
        from views.datos_view import DatosView
        from views.visor_view import VisorView
        from views.desplazamiento_view import DesplazamientoView
        from views.velocidad_view import VelocidadView
        from views.inclinometros_view import InclinometrosView
        from views.celdas_view import CeldasView
        from views.acelerografos_view import AcelerografosView
        from views.sondajestdr_view import SondajetdrView
        from views.analisis_view import AnalisisView
        if tipoequipo == "Piezómetro":
            DatosView.reiniciarVistaDatos(PiezometrosView.main, PiezometrosView.idproyecto, PiezometrosView.nameproyecto)
            VisorView.reiniciarVistaVisor(PiezometrosView.main, PiezometrosView.idproyecto, PiezometrosView.nameproyecto)
        else:
            DatosView.reiniciarVistaDatos(PiezometrosView.main, PiezometrosView.idproyecto, PiezometrosView.nameproyecto)
            VisorView.reiniciarVistaVisor(PiezometrosView.main, PiezometrosView.idproyecto, PiezometrosView.nameproyecto)
            DesplazamientoView.reiniciarVistaDesplazamiento(PiezometrosView.main, PiezometrosView.idproyecto, PiezometrosView.nameproyecto)
            VelocidadView.reiniciarVistaVelocidad(PiezometrosView.main, PiezometrosView.idproyecto, PiezometrosView.nameproyecto)
            InclinometrosView.reiniciarVistaInclinometros(PiezometrosView.main, PiezometrosView.idproyecto, PiezometrosView.nameproyecto)
            CeldasView.reiniciarVistaCeldas(PiezometrosView.main, PiezometrosView.idproyecto, PiezometrosView.nameproyecto)
            AcelerografosView.reiniciarVistaAcelerografos(PiezometrosView.main, PiezometrosView.idproyecto, PiezometrosView.nameproyecto)
            SondajetdrView.reiniciarVistaTDR(PiezometrosView.main, PiezometrosView.idproyecto, PiezometrosView.nameproyecto)
            AnalisisView.reiniciarVistaAnalisis(PiezometrosView.main, PiezometrosView.idproyecto, PiezometrosView.nameproyecto)
    
    def obtenerMostrarEquiposMarcados(tree_actual):
        lista = EquiposPiezometros.obtener_todos_elementos_marcados(tree_actual)
        if lista:
            tipo_grafico = PiezometrosView.main.findChild(QComboBox, "cb_tipo_graficas_piezometros")
            tipografico = tipo_grafico.currentData()
            combotipomedida = PiezometrosView.main.findChild(QComboBox, "combo_medida_piezometros")
            tipomedida = combotipomedida.currentData()
            combotipofecha = PiezometrosView.main.findChild(QComboBox, "combo_tiempo_piezometros")
            tipotiempo = combotipofecha.currentData()
            config = SoftwareConfiguracion.obtenerDataSoftware()
            filtrado = config[16]
            piezocuerdasmarcados, cotasmarcadas = PiezometrosView.obtenerListaPiezometrosMarcados(lista, "Piezómetros Cuerda Vibrante")
            if len(piezocuerdasmarcados) > 0:
                datos = PiezometroController.ctrlCalcularPiezometrosCuerda(PiezometrosView.idproyecto, piezocuerdasmarcados, PiezometrosView.cuerdafechainicial, PiezometrosView.cuerdafechafinal, filtrado, tipomedida)
                if len(datos) > 0:
                    PiezometrosView.graficarPiezometrosCuerdaMarcados(lista, datos, cotasmarcadas, 11, 12, tipografico, tipomedida, tipotiempo)
                else:
                    PiezometrosView.limpiarGraficaPiezometros()
            else:
                piezomanualesmarcados, cotasmarcadas = PiezometrosView.obtenerListaPiezometrosMarcados(lista, "Piezómetros Casagrande")
                if len(piezomanualesmarcados) > 0:
                    datos = PiezometroController.ctrlCalcularPiezometrosCasaGrande(PiezometrosView.idproyecto, piezomanualesmarcados, PiezometrosView.manualfechainicial, PiezometrosView.manualfechafinal, filtrado, tipomedida)
                    if len(datos) > 0:
                        PiezometrosView.graficarPiezometrosManualMarcados(lista, datos, cotasmarcadas, 8, 9, tipografico, tipomedida, tipotiempo)
                else:
                    terrenosmarcados = PiezometrosView.obtenerListaEquiposMarcados(lista, "Cotas de Terreno")
                    if len(terrenosmarcados) > 0:
                        PiezometrosView.graficarCotasTerrenoMarcados(lista, 0, 0, tipografico, tipomedida, tipotiempo)
                    else:
                        PiezometrosView.limpiarGraficaPiezometros()
        else:
            PiezometrosView.limpiarGraficaPiezometros()
    
    def obtenerListaPiezometrosMarcados(lista, tipolista):
        equiposmarcados = []
        cotasmarcadas = []
        for region, instrumentos in lista.items():
            for tipo, lista_equipos in instrumentos.items():
                if tipo[0] == tipolista:
                    for piezometro, cotas in lista_equipos.items():
                        equiposmarcados.append((region, piezometro))
                        cotasmarcadas.append((piezometro, cotas))
        return equiposmarcados, cotasmarcadas
    
    def obtenerListaEquiposMarcados(lista, tipolista):
        equiposmarcados = []
        for region, instrumentos in lista.items():
            for tipo, lista_equipos in instrumentos.items():
                if tipo[0] == tipolista:
                    equiposmarcados.append((region, lista_equipos))
        return equiposmarcados
    
    def graficarPiezometrosCuerdaMarcados(lista, datos, cotasmarcadas, idx_funda, idx_super, tipografico, tipomedida, tipotiempo, tendencias=None):
        widget_piezometros = PiezometrosView.main.findChild(QWidget, "widget_piezometros")
        labeltendencia = PiezometrosView.main.findChild(QLabel, "label_tendencia_piezometros")
        # Acceder a la primera fila
        primera_fila = datos[0]
        # Obtener el último y el penúltimo valor de la primera fila
        frecuencia = primera_fila[-1]
        if tipografico == 'NF':
            valor = 8
            titulo = "Nivel Freático en Cota"
            labely = "Nivel Freático (msnm)"
        elif tipografico == 'NI':
            valor = 9
            titulo = "Nivel Freático Incremental"
            if tipomedida == 1:
                labely = "Nivel Incremental (m)"
            elif tipomedida == 100:
                labely = "Nivel Incremental (cm)"
            else:
                labely = "Nivel Incremental (mm)"
        elif tipografico == 'NA':
            valor = 10
            titulo = "Nivel Freático Acumulado"
            if tipomedida == 1:
                labely = "Nivel Acumulado (m)"
            elif tipomedida == 100:
                labely = "Nivel Acumulado (cm)"
            else:
                labely = "Nivel Acumulado (mm)"
        elif tipografico == 'PB':
            valor = 7
            titulo = "Presión Barométrica Piezométrica"
            labely = f"Presión Barométrica (kPa)"
        elif tipografico == 'FP':
            valor = 5
            titulo = "Frecuencia Piezométrica"
            labely = f"Frecuencia ({frecuencia})"
        elif tipografico == 'TP':
            valor = 6
            titulo = "Temperatura Piezométrica"
            labely = "Temperatura (°C)"
        # tipo de tiempo
        if tipotiempo  == "FECHA":
            indextiempo = 2
            labelx = "Fechas"
        elif tipotiempo  == "DIA":
            indextiempo = 3
            labelx = "Días"
        else:
            indextiempo = 4
            labelx = "Horas"
        pluviometros, terrenos = None, None
        modulo = "PIEZOMETROS"
        pluviometrosmarcados = PiezometrosView.obtenerListaEquiposMarcados(lista, "Pluviómetros")
        if len(pluviometrosmarcados) == 1:
            datapluvio = PluviometroController.ctrlObtenerPluviometros(PiezometrosView.idproyecto, pluviometrosmarcados, PiezometrosView.cuerdafechainicial, PiezometrosView.cuerdafechafinal)
            if datapluvio:
                pluviometros = datapluvio
        terrenosmarcados = PiezometrosView.obtenerListaEquiposMarcados(lista, "Cotas de Terreno")
        if len(terrenosmarcados) > 0:
            dataterreno = TerrenoController.ctrlObtenerCotasTerreno(PiezometrosView.idproyecto, terrenosmarcados, PiezometrosView.cuerdafechainicial, PiezometrosView.cuerdafechafinal)
            if dataterreno:
                terrenos = dataterreno
        if len(datos) > 0:
            # validar tipo de filtrado
            config = SoftwareConfiguracion.obtenerDataSoftware()
            filtrado = config[16]
            if filtrado == 0:
                procesar_grafica_piezometros(widget_piezometros, labeltendencia, datos, cotasmarcadas, 1, indextiempo, valor, idx_funda, idx_super, labelx, labely, tipografico, tipomedida, tipotiempo, titulo, PiezometrosView.idproyecto, modulo, pluviometros, tendencias, terrenos, PiezometrosView.cuerdafechainicial, PiezometrosView.cuerdafechafinal)
            else:
                procesar_grafica_piezometros(widget_piezometros, labeltendencia, datos, cotasmarcadas, 1, indextiempo, valor, idx_funda, idx_super, labelx, labely, tipografico, tipomedida, tipotiempo, titulo, PiezometrosView.idproyecto, modulo, pluviometros, tendencias, terrenos)
        else:
            PiezometrosView.limpiarGraficaPiezometros()
        
    def graficarPiezometrosManualMarcados(lista, datos, cotasmarcadas, idx_funda, idx_super, tipografico, tipomedida, tipotiempo, tendencias=None):
        widget_piezometros = PiezometrosView.main.findChild(QWidget, "widget_piezometros")
        labeltendencia = PiezometrosView.main.findChild(QLabel, "label_tendencia_piezometros")
        if tipografico == 'NF':
            valor = 5
            titulo = "Nivel Freático en Cota"
            labely = "Nivel Freático (msnm)"
        elif tipografico == 'NI':
            valor = 6
            titulo = "Nivel Freático Incremental"
            if tipomedida == 1:
                labely = "Nivel Incremental (m)"
            elif tipomedida == 100:
                labely = "Nivel Incremental (cm)"
            else:
                labely = "Nivel Incremental (mm)"
        elif tipografico == 'NA':
            valor = 7
            titulo = "Nivel Freático Acumulado"
            if tipomedida == 1:
                labely = "Nivel Acumulado (m)"
            elif tipomedida == 100:
                labely = "Nivel Acumulado (cm)"
            else:
                labely = "Nivel Acumulado (mm)"
        elif tipografico == 'PB':
            valor = 0
            titulo = ""
            labely = ""
        elif tipografico == 'FP':
            valor = 0
            titulo = ""
            labely = ""
        elif tipografico == 'TP':
            valor = 0
            titulo = ""
            labely = ""
        # tipo de tiempo
        if tipotiempo  == "FECHA":
            indextiempo = 2
            labelx = "Fechas"
        elif tipotiempo  == "DIA":
            indextiempo = 3
            labelx = "Días"
        else:
            indextiempo = 4
            labelx = "Horas"
        if valor != 0:
            pluviometros, terrenos = None, None
            modulo = "PIEZOMETROS"
            pluviometrosmarcados = PiezometrosView.obtenerListaEquiposMarcados(lista, "Pluviómetros")
            if len(pluviometrosmarcados) == 1:
                datapluvio = PluviometroController.ctrlObtenerPluviometros(PiezometrosView.idproyecto, pluviometrosmarcados, PiezometrosView.manualfechainicial, PiezometrosView.manualfechafinal)
                if datapluvio:
                    pluviometros = datapluvio
            terrenosmarcados = PiezometrosView.obtenerListaEquiposMarcados(lista, "Cotas de Terreno")
            if len(terrenosmarcados) > 0:
                dataterreno = TerrenoController.ctrlObtenerCotasTerreno(PiezometrosView.idproyecto, terrenosmarcados, PiezometrosView.manualfechainicial, PiezometrosView.manualfechafinal)
                if dataterreno:
                    terrenos = dataterreno
            config = SoftwareConfiguracion.obtenerDataSoftware()
            filtrado = config[16]
            if len(datos) > 0:
                # validar tipo de filtrado
                if filtrado == 0:
                    procesar_grafica_piezometros(widget_piezometros, labeltendencia, datos, cotasmarcadas, 1, indextiempo, valor, idx_funda, idx_super, labelx, labely, tipografico, tipomedida, tipotiempo, titulo, PiezometrosView.idproyecto, modulo, pluviometros, tendencias, terrenos, PiezometrosView.manualfechainicial, PiezometrosView.manualfechafinal)
                else:
                    procesar_grafica_piezometros(widget_piezometros, labeltendencia, datos, cotasmarcadas, 1, indextiempo, valor, idx_funda, idx_super, labelx, labely, tipografico, tipomedida, tipotiempo, titulo, PiezometrosView.idproyecto, modulo, pluviometros, tendencias, terrenos)
            else:
                if dataterreno and tipografico == "NF":
                    if filtrado == 0:
                        procesar_grafica_piezometros(widget_piezometros, labeltendencia, datos, cotasmarcadas, 1, indextiempo, valor, idx_funda, idx_super, labelx, labely, tipografico, tipomedida, tipotiempo, titulo, PiezometrosView.idproyecto, modulo, pluviometros, tendencias, terrenos, PiezometrosView.manualfechainicial, PiezometrosView.manualfechafinal)
                    else:
                        procesar_grafica_piezometros(widget_piezometros, labeltendencia, datos, cotasmarcadas, 1, indextiempo, valor, idx_funda, idx_super, labelx, labely, tipografico, tipomedida, tipotiempo, titulo, PiezometrosView.idproyecto, modulo, pluviometros, tendencias, terrenos)
                else:
                    PiezometrosView.limpiarGraficaPiezometros()
        else:
            PiezometrosView.limpiarGraficaPiezometros()
    
    def graficarCotasTerrenoMarcados(lista, idx_funda, idx_super, tipografico, tipomedida, tipotiempo, tendencias=None):
        widget_piezometros = PiezometrosView.main.findChild(QWidget, "widget_piezometros")
        labeltendencia = PiezometrosView.main.findChild(QLabel, "label_tendencia_piezometros")
        # tipo de tiempo
        if tipotiempo  == "FECHA":
            indextiempo = 2
            labelx = "Fechas"
        elif tipotiempo  == "DIA":
            indextiempo = 3
            labelx = "Días"
        else:
            indextiempo = 4
            labelx = "Horas"
        if tipografico == 'NF':
            valor = 5
            titulo = "Nivel Freático en Cota"
            labely = "Nivel Freático (msnm)"
            pluviometros = None
            modulo = "PIEZOMETROS"
            pluviometrosmarcados = PiezometrosView.obtenerListaEquiposMarcados(lista, "Pluviómetros")
            if len(pluviometrosmarcados) == 1:
                datapluvio = PluviometroController.ctrlObtenerPluviometros(PiezometrosView.idproyecto, pluviometrosmarcados, PiezometrosView.manualfechainicial, PiezometrosView.manualfechafinal)
                if datapluvio:
                    pluviometros = datapluvio
            terrenosmarcados = PiezometrosView.obtenerListaEquiposMarcados(lista, "Cotas de Terreno")
            if len(terrenosmarcados) > 0:
                dataterreno = TerrenoController.ctrlObtenerCotasTerreno(PiezometrosView.idproyecto, terrenosmarcados, PiezometrosView.manualfechainicial, PiezometrosView.manualfechafinal)
                if dataterreno:
                    datos, cotasmarcadas = None, None
                    config = SoftwareConfiguracion.obtenerDataSoftware()
                    filtrado = config[16]
                    # validar tipo de filtrado
                    if filtrado == 0:
                        procesar_grafica_piezometros(widget_piezometros, labeltendencia, datos, cotasmarcadas, 1, indextiempo, valor, idx_funda, idx_super, labelx, labely, tipografico, tipomedida, tipotiempo, titulo, PiezometrosView.idproyecto, modulo, pluviometros, tendencias, dataterreno, PiezometrosView.manualfechainicial, PiezometrosView.manualfechafinal)
                    else:
                        procesar_grafica_piezometros(widget_piezometros, labeltendencia, datos, cotasmarcadas, 1, indextiempo, valor, idx_funda, idx_super, labelx, labely, tipografico, tipomedida, tipotiempo, titulo, PiezometrosView.idproyecto, modulo, pluviometros, tendencias, dataterreno)
                else:
                    PiezometrosView.limpiarGraficaPiezometros()
        else:
            PiezometrosView.limpiarGraficaPiezometros()
    
    def limpiarGraficaPiezometros():
        widget_piezometros = PiezometrosView.main.findChild(QWidget, "widget_piezometros")
        limpiar_widget(widget_piezometros)
    
    def mostrarDialogoReportePiezometros(treeWidget, widget_grafico, combo_tipo_grafico, tiporeporte):
        if PiezometrosView.idproyecto:
            lista = EquiposPiezometros.obtener_todos_elementos_marcados(treeWidget)
            if lista:
                piezocuerdasmarcados, cotasmarcadas = PiezometrosView.obtenerListaPiezometrosMarcados(lista, "Piezómetros Cuerda Vibrante")
                piezomanualesmarcados, cotasmarcadas = PiezometrosView.obtenerListaPiezometrosMarcados(lista, "Piezómetros Casagrande")
                terrenosmarcados = PiezometrosView.obtenerListaEquiposMarcados(lista, "Cotas de Terreno")
                tipografico = combo_tipo_grafico.currentData()
                titulografica = combo_tipo_grafico.currentText()
                opcion, tipoequipo = False, "Cotaterreno"
                if len(piezocuerdasmarcados) > 0:
                    tipoequipo = "Piezometrocuerda"
                    opcion = True
                elif len(piezomanualesmarcados) > 0:
                    if tipografico == "NF" or tipografico == "NI" or tipografico == "NA":
                        opcion = True
                        tipoequipo = "Piezometromanual"
                elif len(terrenosmarcados) > 0:
                    if tipografico == "NF":
                        opcion = True
                        tipoequipo = "Cotaterreno"
                if opcion:
                    if tiporeporte == "General":
                        GraficaReporte.mostrarDialogoImagenVisor(widget_grafico, "Piezometros", tipografico, titulografica, PiezometrosView.idproyecto, tipoequipo)
                    else:
                        ReporteImage.modalImagenReporte(widget_grafico, "Piezometros", tipografico, titulografica, PiezometrosView.idproyecto, tipoequipo)
    
    def mostrarModalLimpiezaRuido(treeWidget):
        lista = EquiposPiezometros.obtener_todos_elementos_marcados(treeWidget)
        if lista:
            piezometrosmarcados, tipopiezo = None, None
            piezocuerdasmarcados, cotasmarcadas = PiezometrosView.obtenerListaPiezometrosMarcados(lista, "Piezómetros Cuerda Vibrante")
            if len(piezocuerdasmarcados) > 0:
                piezometrosmarcados, tipopiezo = piezocuerdasmarcados, "CUERDA"
            else:
                piezomanualesmarcados, cotasmarcadas = PiezometrosView.obtenerListaPiezometrosMarcados(lista, "Piezómetros Casagrande")
                if len(piezomanualesmarcados) > 0:
                    piezometrosmarcados, tipopiezo = piezomanualesmarcados, "MANUAL"
            if piezometrosmarcados and tipopiezo:
                estado, metodoLimpieza, equiposLimpieza = Personalizacion.dialogoLimpiezaRuidoEquipos(piezometrosmarcados)
                if estado:
                    tipo_grafico = PiezometrosView.main.findChild(QComboBox, "cb_tipo_graficas_piezometros")
                    tipografico = tipo_grafico.currentData()
                    if tipografico == "NF":
                        indexcuerda = 8
                        indexmanual = 5
                    elif tipografico == 'NI':
                        indexcuerda = 9
                        indexmanual = 6
                    elif tipografico == 'NA':
                        indexcuerda = 10
                        indexmanual = 7
                    elif tipografico == 'PB':
                        indexcuerda = 7
                        indexmanual = 0
                    elif tipografico == 'FP':
                        indexcuerda = 5
                        indexmanual = 0
                    elif tipografico == 'TP':
                        indexcuerda = 6
                        indexmanual = 0
                    combotipomedida = PiezometrosView.main.findChild(QComboBox, "combo_medida_piezometros")
                    tipomedida = combotipomedida.currentData()
                    combotipofecha = PiezometrosView.main.findChild(QComboBox, "combo_tiempo_piezometros")
                    tipotiempo = combotipofecha.currentData()
                    config = SoftwareConfiguracion.obtenerDataSoftware()
                    filtrado = config[16]
                    if tipopiezo == "CUERDA":
                        datos = PiezometroController.ctrlCalcularPiezometrosCuerda(PiezometrosView.idproyecto, piezometrosmarcados, PiezometrosView.cuerdafechainicial, PiezometrosView.cuerdafechafinal, filtrado, tipomedida)
                        if len(datos) > 0:
                            if metodoLimpieza == 'Limpieza Automática':
                                data = CalculosTendencias.limpiezaAutomaticaSaltos(datos, equiposLimpieza, 0, indexcuerda)
                            elif metodoLimpieza == 'Limpieza Manual':
                                data = CalculosTendencias.limpiezaManualSaltos(datos, equiposLimpieza, 0, indexcuerda)
                            elif metodoLimpieza == 'Ajustar Gráfico':
                                data = CalculosTendencias.ajustarCalculoSaltos(datos, equiposLimpieza, 0, indexcuerda)
                            # graficar
                            PiezometrosView.graficarPiezometrosCuerdaMarcados(lista, data, cotasmarcadas, 11, 12, tipografico, tipomedida, tipotiempo)
                    else:
                        datos = PiezometroController.ctrlCalcularPiezometrosCasaGrande(PiezometrosView.idproyecto, piezometrosmarcados, PiezometrosView.manualfechainicial, PiezometrosView.manualfechafinal, filtrado, tipomedida)
                        if len(datos) > 0:
                            if metodoLimpieza == 'Limpieza Automática':
                                data = CalculosTendencias.limpiezaAutomaticaSaltos(datos, equiposLimpieza, 0, indexmanual)
                            elif metodoLimpieza == 'Limpieza Manual':
                                data = CalculosTendencias.limpiezaManualSaltos(datos, equiposLimpieza, 0, indexmanual)
                            elif metodoLimpieza == 'Ajustar Gráfico':
                                data = CalculosTendencias.ajustarCalculoSaltos(datos, equiposLimpieza, 0, indexmanual)
                            # graficar
                            PiezometrosView.graficarPiezometrosManualMarcados(lista, data, cotasmarcadas, 8, 9, tipografico, tipomedida, tipotiempo)
    
    def mostrarModalTendencia(treeWidget):
        lista = EquiposPiezometros.obtener_todos_elementos_marcados(treeWidget)
        if lista:
            piezometrosmarcados, tipopiezo = None, None
            piezocuerdasmarcados, cotasmarcadas = PiezometrosView.obtenerListaPiezometrosMarcados(lista, "Piezómetros Cuerda Vibrante")
            if len(piezocuerdasmarcados) > 0:
                piezometrosmarcados, tipopiezo = piezocuerdasmarcados, "CUERDA"
            else:
                piezomanualesmarcados, cotasmarcadas = PiezometrosView.obtenerListaPiezometrosMarcados(lista, "Piezómetros Casagrande")
                if len(piezomanualesmarcados) > 0:
                    piezometrosmarcados, tipopiezo = piezomanualesmarcados, "MANUAL"
            if piezometrosmarcados and tipopiezo:
                regresion = Personalizacion.dialogoFiltroRegresionPiezometrosCeldas(piezometrosmarcados, "PIEZÓMETROS")
                if len(regresion) > 0:
                    tipo_grafico = PiezometrosView.main.findChild(QComboBox, "cb_tipo_graficas_piezometros")
                    tipografico = tipo_grafico.currentData()
                    combotipomedida = PiezometrosView.main.findChild(QComboBox, "combo_medida_piezometros")
                    tipomedida = combotipomedida.currentData()
                    combotipofecha = PiezometrosView.main.findChild(QComboBox, "combo_tiempo_piezometros")
                    tipotiempo = combotipofecha.currentData()
                    config = SoftwareConfiguracion.obtenerDataSoftware()
                    filtrado = config[16]
                    if tipopiezo == "CUERDA":
                        datos = PiezometroController.ctrlCalcularPiezometrosCuerda(PiezometrosView.idproyecto, piezometrosmarcados, PiezometrosView.cuerdafechainicial, PiezometrosView.cuerdafechafinal, filtrado, tipomedida)
                        if len(datos) > 0:
                            PiezometrosView.graficarPiezometrosCuerdaMarcados(lista, datos, cotasmarcadas, 11, 12, tipografico, tipomedida, tipotiempo, regresion)
                    else:
                        datos = PiezometroController.ctrlCalcularPiezometrosCasaGrande(PiezometrosView.idproyecto, piezometrosmarcados, PiezometrosView.manualfechainicial, PiezometrosView.manualfechafinal, filtrado, tipomedida)
                        if len(datos) > 0:
                            PiezometrosView.graficarPiezometrosManualMarcados(lista, datos, cotasmarcadas, 8, 9, tipografico, tipomedida, tipotiempo, regresion)
    
    def mostrarModalConfiguracionEjes(treeWidget):
        lista = EquiposPiezometros.obtener_todos_elementos_marcados(treeWidget)
        if lista:
            piezometrosmarcados, tipopiezo = None, None
            piezocuerdasmarcados, cotasmarcadas = PiezometrosView.obtenerListaPiezometrosMarcados(lista, "Piezómetros Cuerda Vibrante")
            if len(piezocuerdasmarcados) > 0:
                piezometrosmarcados, tipopiezo = piezocuerdasmarcados, "CUERDA"
            else:
                piezomanualesmarcados, cotasmarcadas = PiezometrosView.obtenerListaPiezometrosMarcados(lista, "Piezómetros Casagrande")
                if len(piezomanualesmarcados) > 0:
                    piezometrosmarcados, tipopiezo = piezomanualesmarcados, "MANUAL"
            if piezometrosmarcados and tipopiezo:
                combotipomedida = PiezometrosView.main.findChild(QComboBox, "combo_medida_piezometros")
                tipomedida = combotipomedida.currentData()
                combotipofecha = PiezometrosView.main.findChild(QComboBox, "combo_tiempo_piezometros")
                tipotiempo = combotipofecha.currentData()
                if tipotiempo == "HORA":
                    unidadtiempo  = 24
                else:
                    unidadtiempo  = 1
                tipo_grafico = PiezometrosView.main.findChild(QComboBox, "cb_tipo_graficas_piezometros")
                tipografico = tipo_grafico.currentData()
                infoeje = ConfiguracionController.ctrlObtenerConfiguracionEje(PiezometrosView.idproyecto, "PIEZOMETROS", tipografico)
                if infoeje:
                    ejeymin, ejeymax, ejeyprim, ejeysecu, interdias = infoeje[4], infoeje[5], infoeje[6], infoeje[7], infoeje[8]
                    rango_precipitacion = infoeje[9] if infoeje[9] else 100
                    intervalo_precipitacion = infoeje[10] if infoeje[10] else 20
                else:
                    ejeymin, ejeymax, ejeyprim, ejeysecu, interdias = 0, 0, 0, 0, 0
                    rango_precipitacion, intervalo_precipitacion = 100, 20
                estadoeje, minejey, maxejey, primario, secundario, dias, rango_precipitacion, intervalo_precipitacion = Personalizacion.dialogoConfiguracionEjes(ejeymin, ejeymax, ejeyprim, ejeysecu, interdias, tipomedida, rango_precipitacion, intervalo_precipitacion, unidadtiempo)
                if estadoeje:
                    # guardar configuracion
                    respuesta = ConfiguracionController.ctrlActualizarConfiguracionEjes(PiezometrosView.idproyecto, "PIEZOMETROS", tipografico, minejey, maxejey, primario, secundario, dias, rango_precipitacion, intervalo_precipitacion)
                    if respuesta:
                        config = SoftwareConfiguracion.obtenerDataSoftware()
                        filtrado = config[16]
                        if tipopiezo == "CUERDA":
                            datos = PiezometroController.ctrlCalcularPiezometrosCuerda(PiezometrosView.idproyecto, piezometrosmarcados, PiezometrosView.cuerdafechainicial, PiezometrosView.cuerdafechafinal, filtrado, tipomedida)
                            if len(datos) > 0:
                                PiezometrosView.graficarPiezometrosCuerdaMarcados(lista, datos, cotasmarcadas, 11, 12, tipografico, tipomedida, tipotiempo)
                        else:
                            datos = PiezometroController.ctrlCalcularPiezometrosCasaGrande(PiezometrosView.idproyecto, piezometrosmarcados, PiezometrosView.manualfechainicial, PiezometrosView.manualfechafinal, filtrado, tipomedida)
                            if len(datos) > 0:
                                PiezometrosView.graficarPiezometrosManualMarcados(lista, datos, cotasmarcadas, 8, 9, tipografico, tipomedida, tipotiempo)
    
    def reiniciarVistaPiezometros(main, proyecto_id, proyecto_name):
        # reiniciar variables
        PiezometrosView.main = main
        PiezometrosView.idproyecto = proyecto_id
        PiezometrosView.nameproyecto = proyecto_name
        PiezometrosView.estadochecklist = True
        PiezometrosView.limpiarGraficaPiezometros()
        # LIMPIAR EL BUSCADOR AL CAMBIAR DE PROYECTO
        buscador_arbol = main.findChild(QLineEdit, "input_buscar_piezometros")
        if buscador_arbol is not None:
            buscador_arbol.blockSignals(True)
            buscador_arbol.clear()
            buscador_arbol.blockSignals(False)
    
    def actualizarVistaPiezometros(fechainicuerda, fechafincuerda, fechainimanual, fechafinmanual):
        PiezometrosView.cuerdafechainicial, PiezometrosView.cuerdafechafinal = fechainicuerda, fechafincuerda
        PiezometrosView.manualfechainicial, PiezometrosView.manualfechafinal = fechainimanual, fechafinmanual       
        if PiezometrosView.idproyecto:
            treeWidget =  PiezometrosView.main.findChild(QTreeWidget, "tree_actual_piezometros")
            PiezometrosView.obtenerMostrarEquiposMarcados(treeWidget)
    
    def iniciarAsistenteVozPiezometros(treeWidget, botonvoz):
        lista = EquiposPiezometros.obtener_todos_elementos_marcados(treeWidget)
        if lista:
            piezocuerdasmarcados, cotasmarcadas = PiezometrosView.obtenerListaPiezometrosMarcados(lista, "Piezómetros Cuerda Vibrante")
            piezomanualesmarcados, cotasmarcadas = PiezometrosView.obtenerListaPiezometrosMarcados(lista, "Piezómetros Casagrande")
            if len(piezocuerdasmarcados) > 0 or len(piezomanualesmarcados) > 0:
                tipo_grafico = PiezometrosView.main.findChild(QComboBox, "cb_tipo_graficas_piezometros")
                tipografico = tipo_grafico.currentData()
                botonvoz.setEnabled(False)
                hilo_asistente = threading.Thread(target=AsistenteVoz.analizarPiezometros, args=(PiezometrosView.idproyecto, piezocuerdasmarcados, piezomanualesmarcados, PiezometrosView.cuerdafechainicial, PiezometrosView.cuerdafechafinal, PiezometrosView.manualfechainicial, PiezometrosView.manualfechafinal, tipografico, botonvoz))
                hilo_asistente.start()
    