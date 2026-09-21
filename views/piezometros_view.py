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
from utils.common.alertas import mostrar_mensaje
from utils.generic.graficarumbralespersonalizados import graficarUmbralesPersonalizado

class PiezometrosView:
    main = None
    idproyecto = None
    nameproyecto = "SIN PROYECTO"
    estadochecklist = True
    estadoPagina = True
    timer_busqueda = None
    umbral_activo_piezometros = False   # <-- nuevo
    umbral_modo = None
    umbral_general_componente = None
    umbrales_cache = None                # <-- nuevo
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
            PiezometrosView.estadoPagina = False
    
    @staticmethod
    def graficarUmbralesPersonalizado():
        if not PiezometrosView.idproyecto:
            return
        tree_widget = PiezometrosView.main.findChild(QTreeWidget, "tree_actual_piezometros")
        lista = EquiposPiezometros.obtener_todos_elementos_marcados(tree_widget)
        if not lista:
            return

        marcados, tipoequipo = PiezometrosView._obtenerMarcadosYTipo(lista)
        if len(marcados) > 1:
            return

        region, piezometro = marcados[0]
        idequipo = int(piezometro[1])

        combo_tipo_grafico = PiezometrosView.main.findChild(QComboBox, "cb_tipo_graficas_piezometros")
        tipo = combo_tipo_grafico.currentData()
        widget_grafico = PiezometrosView.main.findChild(QWidget, "widget_piezometros")
        unimedida = PiezometrosView._calcularUnimedidaUmbral(tipo)

        # 1) Redibujar
        graficarUmbralesPersonalizado(
            widget_grafico, unimedida,
            PiezometrosView.idproyecto, idequipo, tipo, tipoequipo
        )
            
    @staticmethod
    def graficarUmbralesPiezometros():
        widget_grafico = PiezometrosView.main.findChild(QWidget, "widget_piezometros")

        # Toggle real: si había algo pintado, este clic lo quita y no hace nada más
        pintado = GraficarUmbrales.clean_on_widget(widget_grafico, 'color')
        if pintado:
            PiezometrosView.umbral_modo = None
            PiezometrosView.umbral_general_componente = None
            PiezometrosView.umbral_activo_piezometros = False
            PiezometrosView.umbrales_cache = None
            return

        tree_widget = PiezometrosView.main.findChild(QTreeWidget, "tree_actual_piezometros")
        lista = EquiposPiezometros.obtener_todos_elementos_marcados(tree_widget)
        if not lista:
            return
        marcados, tipoequipo = PiezometrosView._obtenerMarcadosYTipo(lista)
        if not marcados:
            return

        combo_tipo = PiezometrosView.main.findChild(QComboBox, "cb_tipo_graficas_piezometros")
        tipo = combo_tipo.currentData()

        opciones = UmbralController.ctrlListarUmbralesGeneralesDisponibles(
            PiezometrosView.idproyecto, tipo, tipoequipo)
        if not opciones:
            mostrar_mensaje("Umbrales", "No hay umbrales generales configurados.", "advertencia")
            return

        if len(opciones) == 1:
            idcompo = opciones[0][0]
        else:
            estado, idcompo = Personalizacion.dialogoSeleccionUmbralGeneral(opciones)
            if not estado or idcompo is None:
                return

        PiezometrosView.umbral_general_componente = idcompo
        PiezometrosView.umbral_modo = "GENERAL"
        PiezometrosView._dibujarUmbralesGenerales(lista)

    @staticmethod
    def _dibujarUmbralesGenerales(lista=None):
        widget_grafico = PiezometrosView.main.findChild(QWidget, "widget_piezometros")
        GraficarUmbrales.clean_on_widget(widget_grafico, 'color')

        if lista is None:
            tree_widget = PiezometrosView.main.findChild(QTreeWidget, "tree_actual_piezometros")
            lista = EquiposPiezometros.obtener_todos_elementos_marcados(tree_widget)
        marcados, tipoequipo = PiezometrosView._obtenerMarcadosYTipo(lista)
        if not marcados:
            return

        combo_tipo = PiezometrosView.main.findChild(QComboBox, "cb_tipo_graficas_piezometros")
        tipo = combo_tipo.currentData()
        idcompo = PiezometrosView.umbral_general_componente
        if idcompo is None:
            idcompo = marcados[0][0][1]

        umbrales = UmbralController.ctrlObtenerUmbralesInstrumentacion(
            PiezometrosView.idproyecto, idcompo, tipo, tipoequipo)
        if not umbrales:
            PiezometrosView.umbral_modo = None
            PiezometrosView.umbral_activo_piezometros = False
            return

        unimedida = PiezometrosView._calcularUnimedidaUmbral(tipo)
        GraficarUmbrales.draw_on_widget(widget_grafico, umbrales, unimedida, 'y', 'color')
        PiezometrosView.umbral_activo_piezometros = True

    def _dibujarUmbralesPiezometros(widget_grafico=None, forzar_seleccion=False):
        if widget_grafico is None:
            widget_grafico = PiezometrosView.main.findChild(QWidget, "widget_piezometros")

        tree_widget = PiezometrosView.main.findChild(QTreeWidget, "tree_actual_piezometros")
        lista = EquiposPiezometros.obtener_todos_elementos_marcados(tree_widget)
        if not lista:
            return

        combo_tipo_grafico = PiezometrosView.main.findChild(QComboBox, "cb_tipo_graficas_piezometros")
        tipo = combo_tipo_grafico.currentData()

        # Determinar qué tipo de piezómetro está marcado (cuerda tiene prioridad, igual que el resto de la vista)
        piezocuerdasmarcados, _ = PiezometrosView.obtenerListaPiezometrosMarcados(lista, "Piezómetros Cuerda Vibrante")
        if len(piezocuerdasmarcados) > 0:
            marcados = piezocuerdasmarcados
            tipoequipo_umbral = 'PIEZOMETROCUERDA'
        else:
            piezomanualesmarcados, _ = PiezometrosView.obtenerListaPiezometrosMarcados(lista, "Piezómetros Casagrande")
            marcados = piezomanualesmarcados
            tipoequipo_umbral = 'PIEZOMETROMANUAL'

        if not marcados:
            return

        # --- REUTILIZAR SELECCIÓN YA HECHA ---
        cache_key = (tipo, tipoequipo_umbral)
        if (not forzar_seleccion) and PiezometrosView.umbrales_cache is not None \
                and PiezometrosView.umbrales_cache.get('key') == cache_key:
            umbrales = PiezometrosView.umbrales_cache['umbrales']
            if umbrales:
                unimedida = PiezometrosView._calcularUnimedidaUmbral(tipo)
                GraficarUmbrales.draw_on_widget(widget_grafico, umbrales, unimedida, 'y', 'color')
                PiezometrosView.umbral_activo_piezometros = True
            return
        # --------------------------------------

        idcompo = 0
        for region, piezometro in marcados:
            idcompo = region[1]   # (nombrecomponente, idcomponente, idproyecto)
            break

        umbrales = UmbralController.ctrlObtenerUmbralesInstrumentacion(
            PiezometrosView.idproyecto, idcompo, tipo, tipoequipo_umbral
        )
        if umbrales:
            PiezometrosView.umbrales_cache = {'key': cache_key, 'umbrales': umbrales}
            unimedida = PiezometrosView._calcularUnimedidaUmbral(tipo)
            GraficarUmbrales.draw_on_widget(widget_grafico, umbrales, unimedida, 'y', 'color')
            PiezometrosView.umbral_activo_piezometros = True

    def _calcularUnimedidaUmbral(tipo):
        combo_medidas = PiezometrosView.main.findChild(QComboBox, "combo_medida_piezometros")
        unidad = combo_medidas.currentData()
        if tipo == "NF":
            return 1
        elif tipo in ("NI", "NA"):
            return unidad
        elif tipo == "PB":
            return 1
        elif tipo == "FP":
            return 1
        else:
            return 1
    
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

    @staticmethod
    def _obtenerMarcadosYTipo(lista):
        """Devuelve (marcados, tipoequipo_umbral). Cuerda tiene prioridad."""
        cuerda, _ = PiezometrosView.obtenerListaPiezometrosMarcados(lista, "Piezómetros Cuerda Vibrante")
        if len(cuerda) > 0:
            return cuerda, 'PIEZOMETROCUERDA'
        manual, _ = PiezometrosView.obtenerListaPiezometrosMarcados(lista, "Piezómetros Casagrande")
        if len(manual) > 0:
            return manual, 'PIEZOMETROMANUAL'
        return [], None

    @staticmethod
    def _aplicarUmbralPersonalizado(lista):
        widget_grafico = PiezometrosView.main.findChild(QWidget, "widget_piezometros")
        # Limpiar siempre primero: si antes había un umbral pintado (1 piezómetro)
        # y ahora hay 0 o 2+, se debe quitar del gráfico.
        GraficarUmbrales.clean_on_widget(widget_grafico, 'color')

        marcados, tipoequipo = PiezometrosView._obtenerMarcadosYTipo(lista)

        # Regla: solo se pinta automáticamente si hay EXACTAMENTE 1 piezómetro marcado
        if len(marcados) != 1:
            PiezometrosView.umbral_activo_piezometros = False
            PiezometrosView.umbral_modo = None
            return False

        combo_tipo = PiezometrosView.main.findChild(QComboBox, "cb_tipo_graficas_piezometros")
        tipo = combo_tipo.currentData()

        region, piezometro = marcados[0]
        try:
            idequipo = int(piezometro[2])
        except Exception:
            idequipo = piezometro[2]

        unimedida = PiezometrosView._calcularUnimedidaUmbral(tipo)

        pintado = graficarUmbralesPersonalizado(
            widget_grafico, unimedida, PiezometrosView.idproyecto, idequipo,
            tipo, tipoequipo, 'y', 'color', silencioso=True
        )

        if pintado:
            PiezometrosView.umbral_activo_piezometros = True
            PiezometrosView.umbral_modo = "PERSONALIZADO"
            return True

        PiezometrosView.umbral_activo_piezometros = False
        PiezometrosView.umbral_modo = None
        return False

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
                    PiezometrosView._repintarUmbrales(lista)
                else:
                    PiezometrosView.limpiarGraficaPiezometros()
            else:
                piezomanualesmarcados, cotasmarcadas = PiezometrosView.obtenerListaPiezometrosMarcados(lista, "Piezómetros Casagrande")
                if len(piezomanualesmarcados) > 0:
                    datos = PiezometroController.ctrlCalcularPiezometrosCasaGrande(PiezometrosView.idproyecto, piezomanualesmarcados, PiezometrosView.manualfechainicial, PiezometrosView.manualfechafinal, filtrado, tipomedida)
                    if len(datos) > 0:
                        PiezometrosView.graficarPiezometrosManualMarcados(lista, datos, cotasmarcadas, 8, 9, tipografico, tipomedida, tipotiempo)
                        PiezometrosView._repintarUmbrales(lista)
                else:
                    terrenosmarcados = PiezometrosView.obtenerListaEquiposMarcados(lista, "Cotas de Terreno")
                    if len(terrenosmarcados) > 0:
                        PiezometrosView.graficarCotasTerrenoMarcados(lista, 0, 0, tipografico, tipomedida, tipotiempo)
                        PiezometrosView._repintarUmbrales(lista)
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
    
    @staticmethod
    def _repintarUmbrales(lista):
        if PiezometrosView.umbral_modo == "GENERAL":
            # Modo general elegido explícitamente por el usuario: se mantiene pegado
            PiezometrosView._dibujarUmbralesGenerales(lista)
        else:
            # None o "PERSONALIZADO": intentar personalizado primero
            pintado = PiezometrosView._aplicarUmbralPersonalizado(lista)
            if not pintado:
                marcados, tipoequipo = PiezometrosView._obtenerMarcadosYTipo(lista)
                if len(marcados) > 1:
                    # Fallback a general solo cuando hay más de 1 marcado
                    PiezometrosView._dibujarUmbralesGenerales(lista)
    
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
        PiezometrosView.umbral_activo_piezometros = False
        PiezometrosView.umbral_modo = None
        PiezometrosView.umbral_general_componente = None
        PiezometrosView.umbrales_cache = None
    
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
                            PiezometrosView._repintarUmbrales(lista)
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
                            PiezometrosView._repintarUmbrales(lista)

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
                            PiezometrosView._repintarUmbrales(lista)
                    else:
                        datos = PiezometroController.ctrlCalcularPiezometrosCasaGrande(PiezometrosView.idproyecto, piezometrosmarcados, PiezometrosView.manualfechainicial, PiezometrosView.manualfechafinal, filtrado, tipomedida)
                        if len(datos) > 0:
                            PiezometrosView.graficarPiezometrosManualMarcados(lista, datos, cotasmarcadas, 8, 9, tipografico, tipomedida, tipotiempo, regresion)
                            PiezometrosView._repintarUmbrales(lista)
    
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
                    rangoprecipitacion = infoeje[9] if infoeje[9] else 0
                    intervaloprecipitacion = infoeje[10] if infoeje[10] else 0
                else:
                    ejeymin, ejeymax, ejeyprim, ejeysecu, interdias = 0, 0, 0, 0, 0
                    rangoprecipitacion, intervaloprecipitacion = 0, 0
                estadoeje, minejey, maxejey, primario, secundario, dias, rango_precipitacion, intervalo_precipitacion = Personalizacion.dialogoConfiguracionEjes(ejeymin, ejeymax, ejeyprim, ejeysecu, interdias, tipomedida, rangoprecipitacion, intervaloprecipitacion, unidadtiempo)
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
                                PiezometrosView._repintarUmbrales(lista)
                        else:
                            datos = PiezometroController.ctrlCalcularPiezometrosCasaGrande(PiezometrosView.idproyecto, piezometrosmarcados, PiezometrosView.manualfechainicial, PiezometrosView.manualfechafinal, filtrado, tipomedida)
                            if len(datos) > 0:
                                PiezometrosView.graficarPiezometrosManualMarcados(lista, datos, cotasmarcadas, 8, 9, tipografico, tipomedida, tipotiempo)
                                PiezometrosView._repintarUmbrales(lista)
    
    def reiniciarVistaPiezometros(main, proyecto_id, proyecto_name):
        # reiniciar variables
        PiezometrosView.main = main
        PiezometrosView.idproyecto = proyecto_id
        PiezometrosView.nameproyecto = proyecto_name
        PiezometrosView.estadochecklist = True
        PiezometrosView.umbral_activo_piezometros = False   # <-- nuevo
        PiezometrosView.umbral_modo = None
        PiezometrosView.umbral_general_componente = None   
        PiezometrosView.umbrales_cache = None                # <-- nuevo
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
    