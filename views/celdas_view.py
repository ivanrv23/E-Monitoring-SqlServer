import threading
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (QWidget, QLabel, QSpinBox, QComboBox, QTreeWidget, QPushButton, QLineEdit)
from utils.shared.graficaDesplazamientoVelocidad import procesar_grafica_piezometros
from utils.shared.graficaDesplazamientoVelocidad import limpiar_widget
from utils.common.alertas import mostrar_mensaje
from modules.datos.equiposCeldas import EquiposCeldas
from utils.common.metodosGenerales import MetodosGenerales
from utils.shared.guardarImagenReporte import ReporteImage
from utils.shared.graficareporte import GraficaReporte
from utils.shared.asistentedevoz import AsistenteVoz
from utils.shared.personalizacion import Personalizacion
from utils.shared.calculostendencias import CalculosTendencias
from modules.empresa.softwareconfiguracion import SoftwareConfiguracion
from controllers.ConfiguracionController import ConfiguracionController
from controllers.CeldaController import CeldaController
from controllers.UmbralController import UmbralController
from utils.shared.graficarUmbrales import GraficarUmbrales
from utils.generic.graficarumbralespersonalizados import graficarUmbralesPersonalizado
from controllers.PluviometroController import PluviometroController

class CeldasView:
    main = None
    idproyecto = None
    nameproyecto = "SIN PROYECTO"
    estadochecklist = True
    estadoPagina = True
    timer_busqueda = None
    umbral_activo_celdas = False   # <-- nuevo
    umbrales_cache = None          # <-- nuevo
    umbral_modo = None              # <-- AGREGAR
    umbral_general_componente = None  # <-- AGREGAR
    tendencia_activa = None
    fechainicial, fechafinal = MetodosGenerales.obtenerRangoFechas(365)
    
    def inicializarVistaCeldas(main, proyectoid, proyectoname, fechaini, fechafin):
        CeldasView.main = main
        CeldasView.idproyecto = proyectoid
        CeldasView.nameproyecto = proyectoname
        CeldasView.fechainicial, CeldasView.fechafinal = fechaini, fechafin
        if CeldasView.estadochecklist:
            tree_widget = main.findChild(QTreeWidget, "tree_actual_celdas")
            tree_widget.setHeaderLabels([CeldasView.nameproyecto.upper()])
            EquiposCeldas.inicializar_lista_equipos(tree_widget, CeldasView.idproyecto, CeldasView.nameproyecto)
            CeldasView.estadochecklist = False
        if CeldasView.estadoPagina:
            tree_actual_celdas =  CeldasView.main.findChild(QTreeWidget, "tree_actual_celdas")
            tree_actual_celdas.itemClicked.connect(CeldasView.checkProyectoActualCeldas)
            # --- Buscador de equipos en el árbol ---
            buscador_arbol = CeldasView.main.findChild(QLineEdit, "input_buscar_celdas")
            if buscador_arbol is None:
                buscador_arbol = QLineEdit()
                buscador_arbol.setObjectName("input_buscar_celdas")
                buscador_arbol.setPlaceholderText("Buscar equipo...")
                layout_padre = tree_actual_celdas.parentWidget().layout()
                if layout_padre is not None:
                    indice_tree = layout_padre.indexOf(tree_actual_celdas)
                    layout_padre.insertWidget(indice_tree, buscador_arbol)

                CeldasView.timer_busqueda = QTimer()
                CeldasView.timer_busqueda.setSingleShot(True)
                CeldasView.timer_busqueda.timeout.connect(
                    lambda: EquiposCeldas.filtrarArbolPorTexto(tree_actual_celdas, buscador_arbol.text())
                )
                buscador_arbol.textChanged.connect(
                    lambda: (CeldasView.timer_busqueda.stop(),
                                CeldasView.timer_busqueda.start(250))
                )
                
            tree_actual_celdas.setContextMenuPolicy(Qt.CustomContextMenu)
            tree_actual_celdas.customContextMenuRequested.connect(CeldasView.clicderechoProyectoActualCeldas)
            #-----Imagen a Reporte-----#
            widget_grafico = main.findChild(QWidget, "widget_celdas_asentamiento")
            btn_refrescar_celdas = main.findChild(QPushButton, "btn_refrescar_celdas")
            btn_refrescar_celdas.clicked.connect(lambda: CeldasView.obtenerMostrarCeldasMarcadas(tree_actual_celdas))
            # Cargar Unidades de Medida
            lista_unidades_medida = [
                ('Metros', 1),
                ('Centímetros', 100),
                ('Milímetros', 1000)
            ]
            combo_medidas = main.findChild(QComboBox, "combo_medida_celdas")
            for value, key in lista_unidades_medida:
                combo_medidas.addItem(value, key)
            combo_medidas.activated.connect(lambda: CeldasView.obtenerMostrarCeldasMarcadas(tree_actual_celdas))
            # Cargar Unidades de Tiempo
            lista_unidades_tiempo = [
                ('Fechas', "FECHA"),
                ('Días', "DIA"),
                ('Horas', "HORA"),
            ]
            combo_tiempos = main.findChild(QComboBox, "combo_tiempo_celdas")
            for value, key in lista_unidades_tiempo:
                combo_tiempos.addItem(value, key)
            combo_tiempos.activated.connect(lambda: CeldasView.obtenerMostrarCeldasMarcadas(tree_actual_celdas))
            # Definimos el diccionario de tipos de celdas
            lista_graficos_celdas = {
                'VI': 'Velocidad Incremental',
                'AC': 'Asentamiento Cota',
                'AI': 'Asentamiento Incremental',
                'AA': 'Asentamiento Acumulado',
                'AF': 'Frecuencia',
                'AT': 'Temperatura',
            }
            combograficoceldas = main.findChild(QComboBox, "cb_tipo_graficas_celdas")
            for key, value in lista_graficos_celdas.items():
                combograficoceldas.addItem(value, key)
            combograficoceldas.activated.connect(lambda: CeldasView.obtenerMostrarCeldasMarcadas(tree_actual_celdas))
            spin_nro_dias_velocidad = main.findChild(QSpinBox, "sp_nro_dias_velocidad_celdas")
            spin_nro_dias_velocidad.setEnabled(False)
            combo_tiempo_velocidad = main.findChild(QComboBox, "cb_tipo_calculo_velocidad_celda")
            combo_tiempo_velocidad.activated.connect(lambda: CeldasView.on_tipo_velocidad_seleccionado(combo_tiempo_velocidad))
            # botones
            btnAsistenteVoz = main.findChild(QPushButton, "btn_voz_celdas")
            btnAsistenteVoz.clicked.connect(lambda: CeldasView.iniciarAsistenteVozCeldas(tree_actual_celdas, btnAsistenteVoz))
            btnLimpiarRuido = main.findChild(QPushButton, "btn_limpieza_celdas")
            btnLimpiarRuido.clicked.connect(lambda: CeldasView.mostrarModalLimpiezaRuido(tree_actual_celdas))
            btnTendencia = main.findChild(QPushButton, "btn_tendencia_celdas")
            btnTendencia.clicked.connect(lambda: CeldasView.mostrarModalTendencia(tree_actual_celdas))
            btnEjesPiezo = main.findChild(QPushButton, "btn_ejes_celdas")
            btnEjesPiezo.clicked.connect(lambda: CeldasView.mostrarModalConfiguracionEjes(tree_actual_celdas))
            btn_guardar_grafico_reporte = main.findChild(QPushButton, "btn_reporte_grafica_celdas")
            btn_guardar_grafico_reporte.clicked.connect(lambda: CeldasView.mostrarDialogoReporteCeldas(tree_actual_celdas, widget_grafico, combograficoceldas, "Anexos"))
            btnReporteGeneral = main.findChild(QPushButton, "btn_imagen_celdas")
            btnReporteGeneral.clicked.connect(lambda: CeldasView.mostrarDialogoReporteCeldas(tree_actual_celdas, widget_grafico, combograficoceldas, "General"))
            btn_umbral_celda = main.findChild(QPushButton, "btn_umbral_celda")
            btn_umbral_celda.clicked.connect(CeldasView.graficarUmbralesCeldas)
            CeldasView.estadoPagina = False
    
    @staticmethod
    def graficarUmbralesPersonalizado():
        if not CeldasView.idproyecto:
            return
        
        tree_widget = CeldasView.main.findChild(QTreeWidget, "tree_actual_celdas")
        lista = EquiposCeldas.obtener_todos_elementos_marcados(tree_widget)
        if not lista:
            return

        celdasmarcadas, _ = CeldasView.obtenerListaCeldasMarcadas(lista, "Celdas de Asentamiento")
        if len(celdasmarcadas) != 1:
            return

        region, celda = celdasmarcadas[0]
        try:
            idequipo = int(celda[2])
        except Exception:
            idequipo = celda[2]

        combo_tipo_grafico = CeldasView.main.findChild(QComboBox, "cb_tipo_graficas_celdas")
        tipo = combo_tipo_grafico.currentData()
        combo_medidas = CeldasView.main.findChild(QComboBox, "combo_medida_celdas")
        unidad = combo_medidas.currentData()
        widget_grafico = CeldasView.main.findChild(QWidget, "widget_celdas_asentamiento")
        
        unimedida = CeldasView._calcularUnimedidaUmbral(tipo, unidad)

        graficarUmbralesPersonalizado(
            widget_grafico, unimedida,
            CeldasView.idproyecto, idequipo, tipo, 'CELDA'
        )

    @staticmethod
    def _calcularUnimedidaUmbral(tipo, unidad):
        """Calcula la unidad de medida según tipo de gráfico y unidad seleccionada"""
        if tipo in ("VI", "AI", "AA"):
            return unidad  # m, cm o mm
        else:  # AC, AF, AT
            return 1
            
    @staticmethod
    def graficarUmbralesCeldas():
        widget_grafico = CeldasView.main.findChild(QWidget, "widget_celdas_asentamiento")

        # Toggle real
        pintado = GraficarUmbrales.clean_on_widget(widget_grafico, 'color')
        if pintado:
            CeldasView.umbral_modo = None
            CeldasView.umbral_general_componente = None
            CeldasView.umbral_activo_celdas = False
            CeldasView.umbrales_cache = None
            return

        tree_widget = CeldasView.main.findChild(QTreeWidget, "tree_actual_celdas")
        lista = EquiposCeldas.obtener_todos_elementos_marcados(tree_widget)
        if not lista:
            return
        
        celdasmarcadas, _ = CeldasView.obtenerListaCeldasMarcadas(lista, "Celdas de Asentamiento")
        if not celdasmarcadas:
            return

        combo_tipo = CeldasView.main.findChild(QComboBox, "cb_tipo_graficas_celdas")
        tipo = combo_tipo.currentData()

        opciones = UmbralController.ctrlListarUmbralesGeneralesDisponibles(
            CeldasView.idproyecto, tipo, 'CELDA')
        if not opciones:
            mostrar_mensaje("Umbrales", "No hay umbrales generales configurados.", "advertencia")
            return

        if len(opciones) == 1:
            idcompo = opciones[0][0]
        else:
            estado, idcompo = Personalizacion.dialogoSeleccionUmbralGeneral(opciones)
            if not estado or idcompo is None:
                return

        CeldasView.umbral_general_componente = idcompo
        CeldasView.umbral_modo = "GENERAL"
        CeldasView._dibujarUmbralesGenerales(lista)

    @staticmethod
    def _dibujarUmbralesGenerales(lista=None):
        widget_grafico = CeldasView.main.findChild(QWidget, "widget_celdas_asentamiento")
        GraficarUmbrales.clean_on_widget(widget_grafico, 'color')

        if lista is None:
            tree_widget = CeldasView.main.findChild(QTreeWidget, "tree_actual_celdas")
            lista = EquiposCeldas.obtener_todos_elementos_marcados(tree_widget)
        
        celdasmarcadas, _ = CeldasView.obtenerListaCeldasMarcadas(lista, "Celdas de Asentamiento")
        if not celdasmarcadas:
            return

        combo_tipo = CeldasView.main.findChild(QComboBox, "cb_tipo_graficas_celdas")
        tipo = combo_tipo.currentData()
        combo_medidas = CeldasView.main.findChild(QComboBox, "combo_medida_celdas")
        unidad = combo_medidas.currentData()
        
        idcompo = CeldasView.umbral_general_componente
        if idcompo is None:
            idcompo = celdasmarcadas[0][0][1]

        umbrales = UmbralController.ctrlObtenerUmbralesInstrumentacion(
            CeldasView.idproyecto, idcompo, tipo, 'CELDA')
        if not umbrales:
            CeldasView.umbral_modo = None
            CeldasView.umbral_activo_celdas = False
            return

        unimedida = CeldasView._calcularUnimedidaUmbral(tipo, unidad)
        GraficarUmbrales.draw_on_widget(widget_grafico, umbrales, unimedida, 'y', 'color')
        CeldasView.umbral_activo_celdas = True

    @staticmethod
    def _dibujarUmbralesCeldas(widget_grafico=None, forzar_seleccion=False):
        if widget_grafico is None:
            widget_grafico = CeldasView.main.findChild(QWidget, "widget_celdas_asentamiento")

        tree_actual = CeldasView.main.findChild(QTreeWidget, "tree_actual_celdas")
        lista = EquiposCeldas.obtener_todos_elementos_marcados(tree_actual)
        if not lista:
            return

        combo_tipo_grafico = CeldasView.main.findChild(QComboBox, "cb_tipo_graficas_celdas")
        tipo = combo_tipo_grafico.currentData()
        combo_medidas = CeldasView.main.findChild(QComboBox, "combo_medida_celdas")
        unidad = combo_medidas.currentData()

        celdasmarcadas, _ = CeldasView.obtenerListaCeldasMarcadas(lista, "Celdas de Asentamiento")
        if not celdasmarcadas:
            return

        # --- REUTILIZAR SELECCIÓN YA HECHA ---
        cache_key = (tipo, unidad)
        if (not forzar_seleccion) and CeldasView.umbrales_cache is not None \
                and CeldasView.umbrales_cache.get('key') == cache_key:
            umbrales = CeldasView.umbrales_cache['umbrales']
            if umbrales:
                unimedida = CeldasView._calcularUnimedidaUmbral(tipo, unidad)
                GraficarUmbrales.draw_on_widget(widget_grafico, umbrales, unimedida, 'y', 'color')
                CeldasView.umbral_activo_celdas = True
            return
        # --------------------------------------

        idcompo = celdasmarcadas[0][0][1]

        umbrales = UmbralController.ctrlObtenerUmbralesInstrumentacion(
            CeldasView.idproyecto, idcompo, tipo, 'CELDA'
        )
        if umbrales:
            CeldasView.umbrales_cache = {'key': cache_key, 'umbrales': umbrales}
            unimedida = CeldasView._calcularUnimedidaUmbral(tipo, unidad)
            GraficarUmbrales.draw_on_widget(widget_grafico, umbrales, unimedida, 'y', 'color')
            CeldasView.umbral_activo_celdas = True

    @staticmethod
    def _repintarUmbrales(lista):
        if CeldasView.umbral_modo == "GENERAL":
            CeldasView._dibujarUmbralesGenerales(lista)
        else:
            # None o "PERSONALIZADO": intentar personalizado primero
            pintado = CeldasView._aplicarUmbralPersonalizado(lista)
            if not pintado:
                celdasmarcadas, _ = CeldasView.obtenerListaCeldasMarcadas(lista, "Celdas de Asentamiento")
                if len(celdasmarcadas) > 1:
                    CeldasView._dibujarUmbralesGenerales(lista)

    @staticmethod
    def _aplicarUmbralPersonalizado(lista):
        widget_grafico = CeldasView.main.findChild(QWidget, "widget_celdas_asentamiento")
        GraficarUmbrales.clean_on_widget(widget_grafico, 'color')

        celdasmarcadas, _ = CeldasView.obtenerListaCeldasMarcadas(lista, "Celdas de Asentamiento")

        if len(celdasmarcadas) != 1:
            CeldasView.umbral_activo_celdas = False
            CeldasView.umbral_modo = None
            return False

        combo_tipo = CeldasView.main.findChild(QComboBox, "cb_tipo_graficas_celdas")
        tipo = combo_tipo.currentData()
        combo_medidas = CeldasView.main.findChild(QComboBox, "combo_medida_celdas")
        unidad = combo_medidas.currentData()

        region, celda = celdasmarcadas[0]
        try:
            idequipo = int(celda[2])
        except Exception:
            idequipo = celda[2]

        unimedida = CeldasView._calcularUnimedidaUmbral(tipo, unidad)

        pintado = graficarUmbralesPersonalizado(
            widget_grafico, unimedida, CeldasView.idproyecto, idequipo,
            tipo, 'CELDA', 'y', 'color', silencioso=True
        )

        if pintado:
            CeldasView.umbral_activo_celdas = True
            CeldasView.umbral_modo = "PERSONALIZADO"
            return True

        CeldasView.umbral_activo_celdas = False
        CeldasView.umbral_modo = None
        return False
    
    def checkProyectoActualCeldas(parent_item, column):
        treeWidget =  CeldasView.main.findChild(QTreeWidget, "tree_actual_celdas")
        EquiposCeldas.validarMarcadoCheckbox(parent_item, column, lambda: CeldasView.obtenerMostrarCeldasMarcadas(treeWidget))
        
    def clicderechoProyectoActualCeldas(point):
        treeWidget =  CeldasView.main.findChild(QTreeWidget, "tree_actual_celdas")
        EquiposCeldas.validarOpcionesMenuCheckbox(point, treeWidget, "CELDAS", CeldasView.reiniciarVistasAfectadas)
    
    def reiniciarVistasAfectadas(tipoequipo="Todos"):
        from views.datos_view import DatosView
        from views.visor_view import VisorView
        from views.desplazamiento_view import DesplazamientoView
        from views.velocidad_view import VelocidadView
        from views.inclinometros_view import InclinometrosView
        from views.piezometros_view import PiezometrosView
        from views.acelerografos_view import AcelerografosView
        from views.sondajestdr_view import SondajetdrView
        from views.analisis_view import AnalisisView
        if tipoequipo == "Celda":
            DatosView.reiniciarVistaDatos(CeldasView.main, CeldasView.idproyecto, CeldasView.nameproyecto)
            VisorView.reiniciarVistaVisor(CeldasView.main, CeldasView.idproyecto, CeldasView.nameproyecto)
        else:
            DatosView.reiniciarVistaDatos(CeldasView.main, CeldasView.idproyecto, CeldasView.nameproyecto)
            VisorView.reiniciarVistaVisor(CeldasView.main, CeldasView.idproyecto, CeldasView.nameproyecto)
            DesplazamientoView.reiniciarVistaDesplazamiento(CeldasView.main, CeldasView.idproyecto, CeldasView.nameproyecto)
            VelocidadView.reiniciarVistaVelocidad(CeldasView.main, CeldasView.idproyecto, CeldasView.nameproyecto)
            InclinometrosView.reiniciarVistaInclinometros(CeldasView.main, CeldasView.idproyecto, CeldasView.nameproyecto)
            PiezometrosView.reiniciarVistaPiezometros(CeldasView.main, CeldasView.idproyecto, CeldasView.nameproyecto)
            AcelerografosView.reiniciarVistaAcelerografos(CeldasView.main, CeldasView.idproyecto, CeldasView.nameproyecto)
            SondajetdrView.reiniciarVistaTDR(CeldasView.main, CeldasView.idproyecto, CeldasView.nameproyecto)
            AnalisisView.reiniciarVistaAnalisis(CeldasView.main, CeldasView.idproyecto, CeldasView.nameproyecto)
    
    def obtenerMostrarCeldasMarcadas(tree_actual):
        combotipografico = CeldasView.main.findChild(QComboBox, "cb_tipo_graficas_celdas")
        tipografica = combotipografico.currentData()
        combotipovelocidad = CeldasView.main.findChild(QComboBox, "cb_tipo_calculo_velocidad_celda")
        tipovelocidad = combotipovelocidad.currentText()
        spinvelocidad = CeldasView.main.findChild(QSpinBox, "sp_nro_dias_velocidad_celdas")
        nrodiasvelocidad = spinvelocidad.value()
        combo_medidas = CeldasView.main.findChild(QComboBox, "combo_medida_celdas")
        unidadmedida = combo_medidas.currentData()
        combo_tiempos = CeldasView.main.findChild(QComboBox, "combo_tiempo_celdas")
        unidadtiempo = combo_tiempos.currentData()
        lista = EquiposCeldas.obtener_todos_elementos_marcados(tree_actual)
        if lista:
            celdasmarcadas, cotasmarcadas = CeldasView.obtenerListaCeldasMarcadas(lista, "Celdas de Asentamiento")
            if len(celdasmarcadas) > 0:
                config = SoftwareConfiguracion.obtenerDataSoftware()
                filtrado = config[16]
                if tipografica == 'VI':
                    if tipovelocidad == 'Por Mes':
                        datos = CeldaController.ctrlCalcularVelocidadMes(CeldasView.idproyecto, celdasmarcadas, CeldasView.fechainicial, CeldasView.fechafinal, filtrado)
                    else:
                        if nrodiasvelocidad > 0:
                            datos = CeldaController.ctrlCalcularVelocidadDias(nrodiasvelocidad, CeldasView.idproyecto, celdasmarcadas, CeldasView.fechainicial, CeldasView.fechafinal, filtrado)
                        else:
                            datos = []
                            mostrar_mensaje("Número de días", "Debe ingresar el número de días.", "advertencia")
                elif tipografica == 'AC':
                    datos = CeldaController.ctrlObtenerAsentamientoCota(CeldasView.idproyecto, celdasmarcadas, CeldasView.fechainicial, CeldasView.fechafinal, filtrado)
                elif tipografica == 'AI':
                    datos = CeldaController.ctrlCalcularAsentamientoIncremental(CeldasView.idproyecto, celdasmarcadas, CeldasView.fechainicial, CeldasView.fechafinal, filtrado, unidadmedida)
                elif tipografica == 'AA':
                    datos = CeldaController.ctrlObtenerAsentamientoAcumulado(CeldasView.idproyecto, celdasmarcadas, CeldasView.fechainicial, CeldasView.fechafinal, filtrado, unidadmedida)
                elif tipografica == 'AF':
                    datos = CeldaController.ctrlObtenerAsentamientoFrecuencia(CeldasView.idproyecto, celdasmarcadas, CeldasView.fechainicial, CeldasView.fechafinal, filtrado)
                elif tipografica == 'AT':
                    datos = CeldaController.ctrlObtenerAsentamientoTemperatura(CeldasView.idproyecto, celdasmarcadas, CeldasView.fechainicial, CeldasView.fechafinal, filtrado)
                if len(datos) > 0:
                    idx_funda, idx_super = 6, 7
                    CeldasView.graficarCeldasAsentamientoMarcadas(lista, datos, cotasmarcadas, idx_funda, idx_super, tipografica, unidadmedida, unidadtiempo, CeldasView.tendencia_activa)
                    CeldasView._repintarUmbrales(lista)
                else:
                    CeldasView.limpiarGraficaCeldas()
            else:
                CeldasView.limpiarGraficaCeldas()
        else:
            CeldasView.limpiarGraficaCeldas()
    
    def obtenerListaCeldasMarcadas(lista, tipolista):
        equiposmarcados = []
        cotasmarcadas = []
        for region, instrumentos in lista.items():
            for tipo, lista_equipos in instrumentos.items():
                if tipo[0] == tipolista:
                    for celda, cotas in lista_equipos.items():
                        equiposmarcados.append((region, celda))
                        cotasmarcadas.append((celda, cotas))
        return equiposmarcados, cotasmarcadas
        
    def obtenerListaEquiposMarcados(lista, tipolista):
        equiposmarcados = []
        for region, instrumentos in lista.items():
            for tipo, lista_equipos in instrumentos.items():
                if tipo[0] == tipolista:
                    equiposmarcados.append((region, lista_equipos))
        return equiposmarcados
    
    def graficarCeldasAsentamientoMarcadas(lista, datos, cotasmarcadas, idx_funda, idx_super, tipografico, unidadmedida, unidadtiempo, tendencias=None):
        widget_celdas = CeldasView.main.findChild(QWidget, "widget_celdas_asentamiento")
        labeltendencia = CeldasView.main.findChild(QLabel, "label_tendencia_celdas")
        if len(datos) > 0:
            combotipovelocidad = CeldasView.main.findChild(QComboBox, "cb_tipo_calculo_velocidad_celda")
            tipovelocidad = combotipovelocidad.currentText()
            config = SoftwareConfiguracion.obtenerDataSoftware()
            filtrado, celdapositiva = config[16], config[19]
            if tipografico == 'VI':
                if tipovelocidad == "Por Mes":
                    unimed = "mes"
                else:
                    unimed = "días"
                if celdapositiva == 0:
                    if unidadmedida  == 1:
                        ubicacion = 8
                        labely = f"Velocidad (m/{unimed})"
                    elif unidadmedida  == 100:
                        ubicacion = 9
                        labely = f"Velocidad (cm/{unimed})"
                    else:
                        ubicacion = 10
                        labely = f"Velocidad (mm/{unimed})"
                else:
                    if unidadmedida  == 1:
                        ubicacion = 5
                        labely = f"Velocidad (m/{unimed})"
                    elif unidadmedida  == 100:
                        ubicacion = 6
                        labely = f"Velocidad (cm/{unimed})"
                    else:
                        ubicacion = 7
                        labely = f"Velocidad (mm/{unimed})"
                titulo = "Velocidad Incremental"
            elif tipografico == 'AC':
                ubicacion = 5
                titulo = "Asentamiento en Cota"
                labely = "Asentamiento (msnm)"
            elif tipografico == 'AI':
                ubicacion = 5
                titulo = "Asentamiento Incremental"
                if unidadmedida == 1:
                    labely = "Asentamiento (m)"
                elif unidadmedida == 100:
                    labely = "Asentamiento (cm)"
                else:
                    labely = "Asentamiento (mm)"
            elif tipografico == 'AA':
                ubicacion = 5
                titulo = "Asentamiento Acumulado"
                if unidadmedida == 1:
                    labely = "Asentamiento (m)"
                elif unidadmedida == 100:
                    labely = "Asentamiento (cm)"
                else:
                    labely = "Asentamiento (mm)"
            elif tipografico == 'AF':
                ubicacion = 5
                titulo = "Frecuencia"
                labely = "Frecuencia (Hz)"
            elif tipografico == 'AT':
                ubicacion = 5
                titulo = "Temperatura"
                labely = "Temperatura (°C)"
            # tipo de tiempo
            if unidadtiempo  == "FECHA":
                indextiempo = 2
                labelx = "Fechas"
            elif unidadtiempo  == "DIA":
                indextiempo = 3
                labelx = "Días"
            else:
                indextiempo = 4
                labelx = "Horas"
            pluviometros = None
            modulo = "CELDAS"
            pluviometrosmarcados = CeldasView.obtenerListaEquiposMarcados(lista, "Pluviómetros")
            if len(pluviometrosmarcados) == 1:
                datapluvio = PluviometroController.ctrlObtenerPluviometros(CeldasView.idproyecto, pluviometrosmarcados, CeldasView.fechainicial, CeldasView.fechafinal)
                if datapluvio:
                    pluviometros = datapluvio

            # validar tipo de filtrado
            if filtrado == 0:
                procesar_grafica_piezometros(widget_celdas, labeltendencia, datos, cotasmarcadas, 1, indextiempo, ubicacion, idx_funda, idx_super, labelx, labely, tipografico, unidadmedida, unidadtiempo, titulo, CeldasView.idproyecto, modulo, pluviometros, tendencias, None, CeldasView.fechainicial, CeldasView.fechafinal)
            else:
                procesar_grafica_piezometros(widget_celdas, labeltendencia, datos, cotasmarcadas, 1, indextiempo, ubicacion, idx_funda, idx_super, labelx, labely, tipografico, unidadmedida, unidadtiempo, titulo, CeldasView.idproyecto, modulo, pluviometros, tendencias)
    
    def limpiarGraficaCeldas():
        widget_celdas = CeldasView.main.findChild(QWidget, "widget_celdas_asentamiento")
        limpiar_widget(widget_celdas)
        CeldasView.umbral_activo_celdas = False
        CeldasView.umbral_modo = None
        CeldasView.umbral_general_componente = None
        CeldasView.umbrales_cache = None
        CeldasView.tendencia_activa = None

    def graficarSoloPluviometro(lista, tipografico, unidadmedida, unidadtiempo, tendencias=None):
        widget_celdas = CeldasView.main.findChild(QWidget, "widget_celdas_asentamiento")
        labeltendencia = CeldasView.main.findChild(QLabel, "label_tendencia_celdas")

        pluviometrosmarcados = CeldasView.obtenerListaEquiposMarcados(lista, "Pluviómetros")
        datapluvio = PluviometroController.ctrlObtenerPluviometros(
            CeldasView.idproyecto, pluviometrosmarcados,
            CeldasView.fechainicial, CeldasView.fechafinal
        )
        if not datapluvio:
            CeldasView.limpiarGraficaCeldas()
            return

        # tipo de tiempo
        if unidadtiempo == "FECHA":
            indextiempo, labelx = 2, "Fechas"
        elif unidadtiempo == "DIA":
            indextiempo, labelx = 3, "Días"
        else:
            indextiempo, labelx = 4, "Horas"

        titulo = "Precipitación"
        labely = ""
        ubicacion, idx_funda, idx_super = 5, 6, 7
        modulo = "CELDAS"

        config = SoftwareConfiguracion.obtenerDataSoftware()
        filtrado = config[16]

        if filtrado == 0:
            procesar_grafica_piezometros(widget_celdas, labeltendencia, None, None, 1, indextiempo,
                                         ubicacion, idx_funda, idx_super, labelx, labely, tipografico,
                                         unidadmedida, unidadtiempo, titulo, CeldasView.idproyecto,
                                         modulo, datapluvio, tendencias, None,
                                         CeldasView.fechainicial, CeldasView.fechafinal)
        else:
            procesar_grafica_piezometros(widget_celdas, labeltendencia, None, None, 1, indextiempo,
                                         ubicacion, idx_funda, idx_super, labelx, labely, tipografico,
                                         unidadmedida, unidadtiempo, titulo, CeldasView.idproyecto,
                                         modulo, datapluvio, tendencias)
       
    def on_tipo_velocidad_seleccionado(combo_tiempo_velocidad):
        tipo = combo_tiempo_velocidad.currentText()
        spin_nro_dias_velocidad = CeldasView.main.findChild(QSpinBox, "sp_nro_dias_velocidad_celdas")
        if tipo == 'Por Días':
            spin_nro_dias_velocidad.setEnabled(True)
        else:
            spin_nro_dias_velocidad.setEnabled(False)
    
    def mostrarDialogoReporteCeldas(treeWidget, widget_grafico, combo_tipo_grafico, tiporeporte):
        if CeldasView.idproyecto:
            lista = EquiposCeldas.obtener_todos_elementos_marcados(treeWidget)
            if lista:
                tipografico = combo_tipo_grafico.currentData()
                titulografica = combo_tipo_grafico.currentText()
                tipoequipo = "Celda"
                if tiporeporte == "General":
                    GraficaReporte.mostrarDialogoImagenVisor(widget_grafico, "Celdas", tipografico, titulografica, CeldasView.idproyecto, tipoequipo)
                else:
                    ReporteImage.modalImagenReporte(widget_grafico, "Celdas", tipografico, titulografica, CeldasView.idproyecto, tipoequipo)
    
    def mostrarModalLimpiezaRuido(treeWidget):
        lista = EquiposCeldas.obtener_todos_elementos_marcados(treeWidget)
        if lista:
            celdasmarcadas, cotasmarcadas = CeldasView.obtenerListaCeldasMarcadas(lista, "Celdas de Asentamiento")
            if len(celdasmarcadas) > 0:
                estado, metodoLimpieza, equiposLimpieza = Personalizacion.dialogoLimpiezaRuidoEquipos(celdasmarcadas)
                if estado:
                    combotipografico = CeldasView.main.findChild(QComboBox, "cb_tipo_graficas_celdas")
                    tipografica = combotipografico.currentData()
                    combotipovelocidad = CeldasView.main.findChild(QComboBox, "cb_tipo_calculo_velocidad_celda")
                    tipovelocidad = combotipovelocidad.currentText()
                    spinvelocidad = CeldasView.main.findChild(QSpinBox, "sp_nro_dias_velocidad_celdas")
                    nrodiasvelocidad = spinvelocidad.value()
                    combo_medidas = CeldasView.main.findChild(QComboBox, "combo_medida_celdas")
                    unidadmedida = combo_medidas.currentData()
                    combo_tiempos = CeldasView.main.findChild(QComboBox, "combo_tiempo_celdas")
                    unidadtiempo = combo_tiempos.currentData()
                    config = SoftwareConfiguracion.obtenerDataSoftware()
                    filtrado, celdapositiva = config[16], config[19]
                    if tipografica == 'VI':
                        if tipovelocidad == 'Por Mes':
                            datos = CeldaController.ctrlCalcularVelocidadMes(CeldasView.idproyecto, celdasmarcadas, CeldasView.fechainicial, CeldasView.fechafinal, filtrado)
                        else:
                            if nrodiasvelocidad > 0:
                                datos = CeldaController.ctrlCalcularVelocidadDias(nrodiasvelocidad, CeldasView.idproyecto, celdasmarcadas, CeldasView.fechainicial, CeldasView.fechafinal, filtrado)
                            else:
                                datos = []
                        if celdapositiva == 0:
                            if unidadmedida  == 1:
                                ubicacion = 8
                            elif unidadmedida  == 100:
                                ubicacion = 9
                            else:
                                ubicacion = 10
                        else:
                            if unidadmedida  == 1:
                                ubicacion = 5
                            elif unidadmedida  == 100:
                                ubicacion = 6
                            else:
                                ubicacion = 7
                    elif tipografica == 'AC':
                        ubicacion = 5
                        datos = CeldaController.ctrlObtenerAsentamientoCota(CeldasView.idproyecto, celdasmarcadas, CeldasView.fechainicial, CeldasView.fechafinal, filtrado)
                    elif tipografica == 'AI':
                        ubicacion = 5
                        datos = CeldaController.ctrlCalcularAsentamientoIncremental(CeldasView.idproyecto, celdasmarcadas, CeldasView.fechainicial, CeldasView.fechafinal, filtrado, unidadmedida)
                    elif tipografica == 'AA':
                        ubicacion = 5
                        datos = CeldaController.ctrlObtenerAsentamientoAcumulado(CeldasView.idproyecto, celdasmarcadas, CeldasView.fechainicial, CeldasView.fechafinal, filtrado, unidadmedida)
                    elif tipografica == 'AF':
                        ubicacion = 5
                        datos = CeldaController.ctrlObtenerAsentamientoFrecuencia(CeldasView.idproyecto, celdasmarcadas, CeldasView.fechainicial, CeldasView.fechafinal, filtrado)
                    elif tipografica == 'AT':
                        ubicacion = 5
                        datos = CeldaController.ctrlObtenerAsentamientoTemperatura(CeldasView.idproyecto, celdasmarcadas, CeldasView.fechainicial, CeldasView.fechafinal, filtrado)
                    if len(datos) > 0:
                        if metodoLimpieza == 'Limpieza Automática':
                            data = CalculosTendencias.limpiezaAutomaticaSaltos(datos, equiposLimpieza, 0, ubicacion)
                        elif metodoLimpieza == 'Limpieza Manual':
                            data = CalculosTendencias.limpiezaManualSaltos(datos, equiposLimpieza, 0, ubicacion)
                        elif metodoLimpieza == 'Ajustar Gráfico':
                            data = CalculosTendencias.ajustarCalculoSaltos(datos, equiposLimpieza, 0, ubicacion)
                        # graficar
                        if data:
                            idx_funda, idx_super = 6, 7
                            CeldasView.graficarCeldasAsentamientoMarcadas(lista, data, cotasmarcadas, idx_funda, idx_super, tipografica, unidadmedida, unidadtiempo, CeldasView.tendencia_activa)
                            if CeldasView.umbral_activo_celdas:          # <-- nuevo
                                CeldasView._repintarUmbrales(lista)      # <-- nuevo

    def mostrarModalTendencia(treeWidget):
        lista = EquiposCeldas.obtener_todos_elementos_marcados(treeWidget)
        if lista:
            celdasmarcadas, cotasmarcadas = CeldasView.obtenerListaCeldasMarcadas(lista, "Celdas de Asentamiento")
            if len(celdasmarcadas) > 0:
                regresion = Personalizacion.dialogoFiltroRegresionPiezometrosCeldas(celdasmarcadas, "CELDAS")
                if len(regresion) > 0:
                    CeldasView.tendencia_activa = regresion
                    combotipografico = CeldasView.main.findChild(QComboBox, "cb_tipo_graficas_celdas")
                    tipografica = combotipografico.currentData()
                    combotipovelocidad = CeldasView.main.findChild(QComboBox, "cb_tipo_calculo_velocidad_celda")
                    tipovelocidad = combotipovelocidad.currentText()
                    spinvelocidad = CeldasView.main.findChild(QSpinBox, "sp_nro_dias_velocidad_celdas")
                    nrodiasvelocidad = spinvelocidad.value()
                    combo_medidas = CeldasView.main.findChild(QComboBox, "combo_medida_celdas")
                    unidadmedida = combo_medidas.currentData()
                    combo_tiempos = CeldasView.main.findChild(QComboBox, "combo_tiempo_celdas")
                    unidadtiempo = combo_tiempos.currentData()
                    config = SoftwareConfiguracion.obtenerDataSoftware()
                    filtrado = config[16]
                    if tipografica == 'VI':
                        if tipovelocidad == 'Por Mes':
                            datos = CeldaController.ctrlCalcularVelocidadMes(CeldasView.idproyecto, celdasmarcadas, CeldasView.fechainicial, CeldasView.fechafinal, filtrado)
                        else:
                            if nrodiasvelocidad > 0:
                                datos = CeldaController.ctrlCalcularVelocidadDias(nrodiasvelocidad, CeldasView.idproyecto, celdasmarcadas, CeldasView.fechainicial, CeldasView.fechafinal, filtrado)
                            else:
                                datos = []
                    elif tipografica == 'AC':
                        datos = CeldaController.ctrlObtenerAsentamientoCota(CeldasView.idproyecto, celdasmarcadas, CeldasView.fechainicial, CeldasView.fechafinal, filtrado)
                    elif tipografica == 'AI':
                        datos = CeldaController.ctrlCalcularAsentamientoIncremental(CeldasView.idproyecto, celdasmarcadas, CeldasView.fechainicial, CeldasView.fechafinal, filtrado, unidadmedida)
                    elif tipografica == 'AA':
                        datos = CeldaController.ctrlObtenerAsentamientoAcumulado(CeldasView.idproyecto, celdasmarcadas, CeldasView.fechainicial, CeldasView.fechafinal, filtrado, unidadmedida)
                    elif tipografica == 'AF':
                        datos = CeldaController.ctrlObtenerAsentamientoFrecuencia(CeldasView.idproyecto, celdasmarcadas, CeldasView.fechainicial, CeldasView.fechafinal, filtrado)
                    elif tipografica == 'AT':
                        datos = CeldaController.ctrlObtenerAsentamientoTemperatura(CeldasView.idproyecto, celdasmarcadas, CeldasView.fechainicial, CeldasView.fechafinal, filtrado)
                    if len(datos) > 0:
                        idx_funda, idx_super = 6, 7
                        CeldasView.graficarCeldasAsentamientoMarcadas(lista, datos, cotasmarcadas, idx_funda, idx_super, tipografica, unidadmedida, unidadtiempo, regresion)
                        if CeldasView.umbral_activo_celdas:          # <-- nuevo
                            CeldasView._repintarUmbrales(lista)      # <-- nuevo
    def mostrarModalConfiguracionEjes(treeWidget):
        lista = EquiposCeldas.obtener_todos_elementos_marcados(treeWidget)
        if lista:
            celdasmarcadas, cotasmarcadas = CeldasView.obtenerListaCeldasMarcadas(lista, "Celdas de Asentamiento")
            if len(celdasmarcadas) > 0:
                combo_medidas = CeldasView.main.findChild(QComboBox, "combo_medida_celdas")
                unidadmedida = combo_medidas.currentData()
                combo_tiempos = CeldasView.main.findChild(QComboBox, "combo_tiempo_celdas")
                tipotiempo = combo_tiempos.currentData()
                if tipotiempo == "HORA":
                    unidadtiempo  = 24
                else:
                    unidadtiempo  = 1
                combotipografico = CeldasView.main.findChild(QComboBox, "cb_tipo_graficas_celdas")
                tipografica = combotipografico.currentData()
                infoeje = ConfiguracionController.ctrlObtenerConfiguracionEje(CeldasView.idproyecto, "CELDAS", tipografica)
                if infoeje:
                    ejeymin, ejeymax, ejeyprim, ejeysecu, interdias = infoeje[4], infoeje[5], infoeje[6], infoeje[7], infoeje[8]
                    rangoprecipitacion = infoeje[9] if infoeje[9] else 0
                    intervaloprecipitacion = infoeje[10] if infoeje[10] else 0
                else:
                    ejeymin, ejeymax, ejeyprim, ejeysecu, interdias = 0, 0, 0, 0, 0
                    rangoprecipitacion, intervaloprecipitacion = 0, 0
                estadoeje, minejey, maxejey, primario, secundario, dias, rango_precipitacion, intervalo_precipitacion = Personalizacion.dialogoConfiguracionEjes(ejeymin, ejeymax, ejeyprim, ejeysecu, interdias, unidadmedida, rangoprecipitacion, intervaloprecipitacion, unidadtiempo)
                if estadoeje:
                    # guardar configuracion
                    respuesta = ConfiguracionController.ctrlActualizarConfiguracionEjes(CeldasView.idproyecto, "CELDAS", tipografica, minejey, maxejey, primario, secundario, dias, rango_precipitacion, intervalo_precipitacion)
                    if respuesta:
                        combotipovelocidad = CeldasView.main.findChild(QComboBox, "cb_tipo_calculo_velocidad_celda")
                        tipovelocidad = combotipovelocidad.currentText()
                        spinvelocidad = CeldasView.main.findChild(QSpinBox, "sp_nro_dias_velocidad_celdas")
                        nrodiasvelocidad = spinvelocidad.value()
                        config = SoftwareConfiguracion.obtenerDataSoftware()
                        filtrado = config[16]
                        if tipografica == 'VI':
                            if tipovelocidad == 'Por Mes':
                                datos = CeldaController.ctrlCalcularVelocidadMes(CeldasView.idproyecto, celdasmarcadas, CeldasView.fechainicial, CeldasView.fechafinal, filtrado)
                            else:
                                if nrodiasvelocidad > 0:
                                    datos = CeldaController.ctrlCalcularVelocidadDias(nrodiasvelocidad, CeldasView.idproyecto, celdasmarcadas, CeldasView.fechainicial, CeldasView.fechafinal, filtrado)
                                else:
                                    datos = []
                        elif tipografica == 'AC':
                            datos = CeldaController.ctrlObtenerAsentamientoCota(CeldasView.idproyecto, celdasmarcadas, CeldasView.fechainicial, CeldasView.fechafinal, filtrado)
                        elif tipografica == 'AI':
                            datos = CeldaController.ctrlCalcularAsentamientoIncremental(CeldasView.idproyecto, celdasmarcadas, CeldasView.fechainicial, CeldasView.fechafinal, filtrado, unidadmedida)
                        elif tipografica == 'AA':
                            datos = CeldaController.ctrlObtenerAsentamientoAcumulado(CeldasView.idproyecto, celdasmarcadas, CeldasView.fechainicial, CeldasView.fechafinal, filtrado, unidadmedida)
                        elif tipografica == 'AF':
                            datos = CeldaController.ctrlObtenerAsentamientoFrecuencia(CeldasView.idproyecto, celdasmarcadas, CeldasView.fechainicial, CeldasView.fechafinal, filtrado)
                        elif tipografica == 'AT':
                            datos = CeldaController.ctrlObtenerAsentamientoTemperatura(CeldasView.idproyecto, celdasmarcadas, CeldasView.fechainicial, CeldasView.fechafinal, filtrado)
                        if len(datos) > 0:
                            idx_funda, idx_super = 6, 7
                            CeldasView.graficarCeldasAsentamientoMarcadas(lista, datos, cotasmarcadas, idx_funda, idx_super, tipografica, unidadmedida, tipotiempo, CeldasView.tendencia_activa)
                            if CeldasView.umbral_activo_celdas:          # <-- nuevo
                                CeldasView._repintarUmbrales(lista)     # <-- nuevo

    def actualizarVistaCeldas(fechaini, fechafin, filtro=False):
        CeldasView.fechainicial = fechaini
        CeldasView.fechafinal = fechafin       
        if CeldasView.idproyecto:
            treeWidget =  CeldasView.main.findChild(QTreeWidget, "tree_actual_celdas")
            CeldasView.obtenerMostrarCeldasMarcadas(treeWidget)
    
    def reiniciarVistaCeldas(main, proyecto_id, proyecto_name):
        # reiniciar variables
        CeldasView.main = main
        CeldasView.idproyecto = proyecto_id
        CeldasView.nameproyecto = proyecto_name
        CeldasView.estadochecklist = True
        CeldasView.umbral_activo_celdas = False   # <-- nuevo
        CeldasView.umbral_modo = None
        CeldasView.umbral_general_componente = None
        CeldasView.umbrales_cache = None          # <-- nuevo
        CeldasView.tendencia_activa = None
        CeldasView.limpiarGraficaCeldas()
        # LIMPIAR EL BUSCADOR AL CAMBIAR DE PROYECTO
        buscador_arbol = main.findChild(QLineEdit, "input_buscar_celdas")
        if buscador_arbol is not None:
            buscador_arbol.blockSignals(True)
            buscador_arbol.clear()
            buscador_arbol.blockSignals(False)
    
    def iniciarAsistenteVozCeldas(treeWidget, botonvoz):
        lista = EquiposCeldas.obtener_todos_elementos_marcados(treeWidget)
        if lista:
            celdasmarcadas, cotasmarcadas = CeldasView.obtenerListaCeldasMarcadas(lista, "Celdas de Asentamiento")
            if len(celdasmarcadas) > 0:
                combotipografico = CeldasView.main.findChild(QComboBox, "cb_tipo_graficas_celdas")
                tipografica = combotipografico.currentData()
                combotipovelocidad = CeldasView.main.findChild(QComboBox, "cb_tipo_calculo_velocidad_celda")
                tipovelocidad = combotipovelocidad.currentText()
                spinvelocidad = CeldasView.main.findChild(QSpinBox, "sp_nro_dias_velocidad_celdas")
                nrodiasvelocidad = spinvelocidad.value()
                botonvoz.setEnabled(False)
                hilo_asistente = threading.Thread(target=AsistenteVoz.analizarCeldas, args=(CeldasView.idproyecto, celdasmarcadas, CeldasView.fechainicial, CeldasView.fechafinal, tipografica, tipovelocidad, nrodiasvelocidad, botonvoz))
                hilo_asistente.start()
    