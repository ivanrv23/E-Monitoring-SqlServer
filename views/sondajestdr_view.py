import threading
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (QWidget, QComboBox, QTreeWidget, QPushButton, QLineEdit)
from modules.tdr.graficarImpedancia import GraficarImpedancia
from controllers.TDRController import TDRController
from modules.datos.equiposSondajestdr import EquiposSondajestdr
from utils.shared.guardarImagenReporte import ReporteImage
from utils.shared.graficareporte import GraficaReporte
from utils.shared.asistentedevoz import AsistenteVoz
from controllers.ConfiguracionController import ConfiguracionController
from utils.shared.personalizacion import Personalizacion
from controllers.UmbralController import UmbralController
from controllers.InstrumentacionController import InstrumentacionController
from utils.shared.graficarUmbrales import GraficarUmbrales
from utils.common.alertas import mostrar_mensaje
from utils.generic.graficarumbralespersonalizados import graficarUmbralesPersonalizado

class SondajetdrView:
    main = None
    idproyecto = None
    nameproyecto = "SIN PROYECTO"
    estadochecklist = True
    estadoPagina = True
    timer_busqueda = None
    umbral_activo_tdr = False
    umbrales_cache = None
    umbral_modo = None
    umbral_general_componente = None
    
    def inicializarVistaSondajesTdr(main, proyectoid, proyectoname):
        SondajetdrView.main = main
        SondajetdrView.idproyecto = proyectoid
        SondajetdrView.nameproyecto = proyectoname
        if SondajetdrView.estadochecklist:
            tree_widget = main.findChild(QTreeWidget, "tree_actual_tdr")
            tree_widget.setHeaderLabels([SondajetdrView.nameproyecto.upper()])
            EquiposSondajestdr.inicializar_lista_equipos(tree_widget, SondajetdrView.idproyecto, SondajetdrView.nameproyecto)
            SondajetdrView.estadochecklist = False
        if SondajetdrView.estadoPagina:
            tree_actual =  SondajetdrView.main.findChild(QTreeWidget, "tree_actual_tdr")
            tree_actual.itemClicked.connect(SondajetdrView.checkProyectoActualSondajestdr)
            # --- Buscador de equipos en el árbol ---
            buscador_arbol = SondajetdrView.main.findChild(QLineEdit, "input_buscar_tdr")
            if buscador_arbol is None:
                buscador_arbol = QLineEdit()
                buscador_arbol.setObjectName("input_buscar_tdr")
                buscador_arbol.setPlaceholderText("Buscar equipo...")
                layout_padre = tree_actual.parentWidget().layout()
                if layout_padre is not None:
                    indice_tree = layout_padre.indexOf(tree_actual)
                    layout_padre.insertWidget(indice_tree, buscador_arbol)

                SondajetdrView.timer_busqueda = QTimer()
                SondajetdrView.timer_busqueda.setSingleShot(True)
                SondajetdrView.timer_busqueda.timeout.connect(
                    lambda: EquiposSondajestdr.filtrarArbolPorTexto(tree_actual, buscador_arbol.text())
                )
                buscador_arbol.textChanged.connect(
                    lambda: (SondajetdrView.timer_busqueda.stop(),
                                SondajetdrView.timer_busqueda.start(250))
                )

            tree_actual.setContextMenuPolicy(Qt.CustomContextMenu)
            tree_actual.customContextMenuRequested.connect(SondajetdrView.clicderechoProyectoActualSondajestdr)
            btn_refrescar_sondajestdr = main.findChild(QPushButton, "btn_refrescar_vista_tdr")
            btn_refrescar_sondajestdr.clicked.connect(lambda: SondajetdrView.obtenerMostrarSondajestdrMarcados(tree_actual))
            btn_umbral_tdr = main.findChild(QPushButton, "btn_umbral_tdr")
            btn_umbral_tdr.clicked.connect(SondajetdrView.graficarUmbralesTDR)
            
            # BOTÓN UMBRAL PERSONALIZADO - CON VALIDACIÓN
            btnAplicarUmbralPersonalizado = main.findChild(QPushButton, "btn_umbral_personalizado_T")
            if btnAplicarUmbralPersonalizado:
                btnAplicarUmbralPersonalizado.clicked.connect(SondajetdrView.pintarUmbralesPersonalizado)
            
            # Definimos el diccionario de tipos de tdr
            lista_graficos_tdr = {
                'IP': 'Impedancia/Profundidad',
                'PI': 'Profundidad/Impedancia',
            }
            # Localizamos el QComboBox en la interfaz
            combo_tipo_grafico_tdr = main.findChild(QComboBox, "cb_tipo_graficas_tdr")
            for key, value in lista_graficos_tdr.items():
                combo_tipo_grafico_tdr.addItem(value, key)
            combo_tipo_grafico_tdr.activated.connect(lambda: SondajetdrView.obtenerMostrarSondajestdrMarcados(tree_actual))
            # Cargar Unidades de Medida
            lista_unidades_medida = [
                ('Metros', 1),
                ('Centímetros', 100),
                ('Milímetros', 1000),
            ]
            combo_medidas = main.findChild(QComboBox, "combo_medida_sondajestdr")
            for value, key in lista_unidades_medida:
                combo_medidas.addItem(value, key)
            combo_medidas.activated.connect(lambda: SondajetdrView.obtenerMostrarSondajestdrMarcados(tree_actual))
            btnAsistenteVoz = main.findChild(QPushButton, "btn_voz_sondajestdr")
            btnAsistenteVoz.clicked.connect(lambda: SondajetdrView.iniciarAsistenteVozSondajestdr(tree_actual, btnAsistenteVoz))
            btnEjesTDR = main.findChild(QPushButton, "btn_ejes_tdr")
            btnEjesTDR.clicked.connect(lambda: SondajetdrView.mostrarModalConfiguracionEjes(tree_actual))
            widget_tdr = SondajetdrView.main.findChild(QWidget, "widget_tdr")
            btn_grafico_reporte = main.findChild(QPushButton, "btn_reporte_grafica_tdr")
            btn_grafico_reporte.clicked.connect(lambda: SondajetdrView.mostrarDialogoReporteSondajestdr(tree_actual, widget_tdr, combo_tipo_grafico_tdr, "Anexos"))
            btnReporteGeneral = main.findChild(QPushButton, "btn_imagen_tdr")
            btnReporteGeneral.clicked.connect(lambda: SondajetdrView.mostrarDialogoReporteSondajestdr(tree_actual, widget_tdr, combo_tipo_grafico_tdr, "General"))
            SondajetdrView.estadoPagina = False

    @staticmethod
    def _calcularUnimedidaUmbral():
        """Calcula la unidad de medida para umbrales en TDR"""
        combo_medidas = SondajetdrView.main.findChild(QComboBox, "combo_medida_sondajestdr")
        return combo_medidas.currentData()  # 1, 100 o 1000

    # ========== UMBRALES PERSONALIZADOS (BOTÓN MANUAL) ==========
    @staticmethod
    def pintarUmbralesPersonalizado():
        """Botón manual para aplicar umbral personalizado"""
        if not SondajetdrView.idproyecto:
            return
        
        tree_widget = SondajetdrView.main.findChild(QTreeWidget, "tree_actual_tdr")
        lista = EquiposSondajestdr.obtener_todos_elementos_marcados(tree_widget)
        if not lista:
            return

        sondajetdrmarcados = SondajetdrView.obtenerListaEquiposMarcados(lista, "TDR")
        if len(sondajetdrmarcados) != 1:
            mostrar_mensaje("Umbrales Personalizados", 
                        "Debe seleccionar exactamente un TDR.", 
                        "advertencia")
            return

        componente, lista_tdr = sondajetdrmarcados[0]
        
        if not lista_tdr:
            mostrar_mensaje("Error", "No se pudo obtener el TDR.", "error")
            return

        # ✅ OBTENER idinstru (índice 1)
        idinstru = lista_tdr[0][1]
        
        # ✅ TRAER idequipo desde base de datos
        idequipo = InstrumentacionController.ctrlObtenerIdequipoInstrumentacion(idinstru)
        if not idequipo:
            mostrar_mensaje("Error", "No se pudo obtener el ID del equipo.", "error")
            return

        tipo_grafico_TDR = SondajetdrView.main.findChild(QComboBox, "cb_tipo_graficas_tdr")
        tipo = tipo_grafico_TDR.currentData()
        widget_tdr = SondajetdrView.main.findChild(QWidget, "widget_tdr")
        
        unimedida = SondajetdrView._calcularUnimedidaUmbral()

        # Llamar SIN silencioso (muestra el diálogo)
        pintado = graficarUmbralesPersonalizado(
            widget_tdr, unimedida,
            SondajetdrView.idproyecto, idequipo, tipo, 'TDR',
            'x', 'linea'
        )
        
        if pintado:
            SondajetdrView.umbral_modo = "PERSONALIZADO"
            SondajetdrView.umbral_activo_tdr = True

    # ========== UMBRALES GENERALES ==========
    @staticmethod
    def graficarUmbralesTDR():
        widget_tdr = SondajetdrView.main.findChild(QWidget, "widget_tdr")

        # Toggle real: limpiar solo líneas de umbral
        pintado = GraficarUmbrales.clean_on_widget(widget_tdr, 'linea')
        if pintado:
            SondajetdrView.umbral_modo = None
            SondajetdrView.umbral_general_componente = None
            SondajetdrView.umbral_activo_tdr = False
            SondajetdrView.umbrales_cache = None
            return

        tree_widget = SondajetdrView.main.findChild(QTreeWidget, "tree_actual_tdr")
        lista = EquiposSondajestdr.obtener_todos_elementos_marcados(tree_widget)
        if not lista:
            return

        sondajetdrmarcados = SondajetdrView.obtenerListaEquiposMarcados(lista, "TDR")
        if not sondajetdrmarcados:
            return

        tipo_grafico_TDR = SondajetdrView.main.findChild(QComboBox, "cb_tipo_graficas_tdr")
        tipo = tipo_grafico_TDR.currentData()

        opciones = UmbralController.ctrlListarUmbralesGeneralesDisponibles(
            SondajetdrView.idproyecto, tipo, 'TDR')
        if not opciones:
            mostrar_mensaje("Umbrales", "No hay umbrales generales configurados.", "advertencia")
            return

        # Seleccionar componente
        if len(opciones) == 1:
            idcompo = opciones[0][0]
        else:
            estado, idcompo = Personalizacion.dialogoSeleccionUmbralGeneral(opciones)
            if not estado or idcompo is None:
                return

        # GUARDAR la selección
        SondajetdrView.umbral_general_componente = idcompo
        SondajetdrView.umbral_modo = "GENERAL"
        SondajetdrView._dibujarUmbralesGenerales(sondajetdrmarcados)

    @staticmethod
    def _dibujarUmbralesGenerales(sondajetdrmarcados=None):
        """Redibuja umbrales generales usando la selección ya guardada"""
        widget_tdr = SondajetdrView.main.findChild(QWidget, "widget_tdr")
        # Solo limpiar líneas de umbral
        GraficarUmbrales.clean_on_widget(widget_tdr, 'linea')

        if sondajetdrmarcados is None:
            tree_widget = SondajetdrView.main.findChild(QTreeWidget, "tree_actual_tdr")
            lista = EquiposSondajestdr.obtener_todos_elementos_marcados(tree_widget)
            sondajetdrmarcados = SondajetdrView.obtenerListaEquiposMarcados(lista, "TDR")
        
        if not sondajetdrmarcados:
            return

        tipo_grafico_TDR = SondajetdrView.main.findChild(QComboBox, "cb_tipo_graficas_tdr")
        tipo = tipo_grafico_TDR.currentData()
        
        idcompo = SondajetdrView.umbral_general_componente
        if idcompo is None:
            componente, _ = sondajetdrmarcados[0]
            idcompo = componente[1]

        umbrales = UmbralController.ctrlObtenerUmbralesInstrumentacion(
            SondajetdrView.idproyecto, idcompo, tipo, 'TDR')
        
        if not umbrales:
            SondajetdrView.umbral_modo = None
            SondajetdrView.umbral_activo_tdr = False
            return

        unimedida = SondajetdrView._calcularUnimedidaUmbral()
        GraficarUmbrales.draw_on_widget(widget_tdr, umbrales, unimedida, 'x', 'linea')
        SondajetdrView.umbral_activo_tdr = True

    @staticmethod
    def _aplicarUmbralPersonalizado(sondajetdrmarcados):
        """Intenta aplicar umbral personalizado si hay exactamente 1 TDR (automático/silencioso)"""
        widget_tdr = SondajetdrView.main.findChild(QWidget, "widget_tdr")
        
        # Solo limpiar líneas de umbral
        GraficarUmbrales.clean_on_widget(widget_tdr, 'linea')

        if len(sondajetdrmarcados) != 1:
            SondajetdrView.umbral_activo_tdr = False
            SondajetdrView.umbral_modo = None
            return False

        componente, lista_tdr = sondajetdrmarcados[0]
        
        if not lista_tdr:
            SondajetdrView.umbral_activo_tdr = False
            SondajetdrView.umbral_modo = None
            return False

        # ✅ OBTENER idinstru (igual que inclinómetros)
        idinstru = lista_tdr[0][1]  # índice 1 = idinstru
        
        # ✅ TRAER idequipo desde base de datos (igual que inclinómetros)
        idequipo = InstrumentacionController.ctrlObtenerIdequipoInstrumentacion(idinstru)
        if not idequipo:
            SondajetdrView.umbral_activo_tdr = False
            SondajetdrView.umbral_modo = None
            return False

        tipo_grafico_TDR = SondajetdrView.main.findChild(QComboBox, "cb_tipo_graficas_tdr")
        tipo = tipo_grafico_TDR.currentData()
        unimedida = SondajetdrView._calcularUnimedidaUmbral()

        # ✅ LLAMAR CON silencioso=True (automático, sin diálogo)
        pintado = graficarUmbralesPersonalizado(
            widget_tdr, unimedida, SondajetdrView.idproyecto, idequipo,
            tipo, 'TDR', 'x', 'linea', silencioso=True
        )

        if pintado:
            SondajetdrView.umbral_activo_tdr = True
            SondajetdrView.umbral_modo = "PERSONALIZADO"
            return True

        SondajetdrView.umbral_activo_tdr = False
        SondajetdrView.umbral_modo = None
        return False

    @staticmethod
    def _repintarUmbrales(sondajetdrmarcados):
        """Repinta umbrales después de redibujar el gráfico"""
        if SondajetdrView.umbral_modo == "GENERAL":
            SondajetdrView._dibujarUmbralesGenerales(sondajetdrmarcados)
        else:
            # Intentar personalizado primero
            pintado = SondajetdrView._aplicarUmbralPersonalizado(sondajetdrmarcados)
            # Si falla y hay más de 1, fallback a general
            if not pintado and len(sondajetdrmarcados) > 1:
                SondajetdrView._dibujarUmbralesGenerales(sondajetdrmarcados)
    
    def checkProyectoActualSondajestdr(parent_item, column):
        treeWidget =  SondajetdrView.main.findChild(QTreeWidget, "tree_actual_tdr")
        EquiposSondajestdr.validarMarcadoCheckbox(parent_item, column, treeWidget, lambda: SondajetdrView.obtenerMostrarSondajestdrMarcados(treeWidget))
        
    def clicderechoProyectoActualSondajestdr(point):
        treeWidget =  SondajetdrView.main.findChild(QTreeWidget, "tree_actual_tdr")
        EquiposSondajestdr.validarOpcionesMenuCheckbox(point, treeWidget, lambda: SondajetdrView.obtenerMostrarSondajestdrMarcados(treeWidget), SondajetdrView.reiniciarVistasAfectadas)
    
    def reiniciarVistasAfectadas(tipoequipo="Todos"):
        from views.datos_view import DatosView
        from views.visor_view import VisorView
        from views.desplazamiento_view import DesplazamientoView
        from views.velocidad_view import VelocidadView
        from views.inclinometros_view import InclinometrosView
        from views.piezometros_view import PiezometrosView
        from views.celdas_view import CeldasView
        from views.acelerografos_view import AcelerografosView
        from views.analisis_view import AnalisisView
        if tipoequipo == "TDR":
            DatosView.reiniciarVistaDatos(SondajetdrView.main, SondajetdrView.idproyecto, SondajetdrView.nameproyecto)
            VisorView.reiniciarVistaVisor(SondajetdrView.main, SondajetdrView.idproyecto, SondajetdrView.nameproyecto)
        else:
            DatosView.reiniciarVistaDatos(SondajetdrView.main, SondajetdrView.idproyecto, SondajetdrView.nameproyecto)
            VisorView.reiniciarVistaVisor(SondajetdrView.main, SondajetdrView.idproyecto, SondajetdrView.nameproyecto)
            DesplazamientoView.reiniciarVistaDesplazamiento(SondajetdrView.main, SondajetdrView.idproyecto, SondajetdrView.nameproyecto)
            VelocidadView.reiniciarVistaVelocidad(SondajetdrView.main, SondajetdrView.idproyecto, SondajetdrView.nameproyecto)
            InclinometrosView.reiniciarVistaInclinometros(SondajetdrView.main, SondajetdrView.idproyecto, SondajetdrView.nameproyecto)
            PiezometrosView.reiniciarVistaPiezometros(SondajetdrView.main, SondajetdrView.idproyecto, SondajetdrView.nameproyecto)
            CeldasView.reiniciarVistaCeldas(SondajetdrView.main, SondajetdrView.idproyecto, SondajetdrView.nameproyecto)
            AcelerografosView.reiniciarVistaAcelerografos(SondajetdrView.main, SondajetdrView.idproyecto, SondajetdrView.nameproyecto)
            AnalisisView.reiniciarVistaAnalisis(SondajetdrView.main, SondajetdrView.idproyecto, SondajetdrView.nameproyecto)

    def obtenerMostrarSondajestdrMarcados(tree_actual):
        lista = EquiposSondajestdr.obtener_todos_elementos_marcados(tree_actual)
        if lista:
            sondajetdrmarcados = SondajetdrView.obtenerListaEquiposMarcados(lista, "TDR")
            if len(sondajetdrmarcados) > 0:
                SondajetdrView.graficarSondajestdrMarcados(sondajetdrmarcados)
            else:
                SondajetdrView.limpiarGraficaSondajestdr()
        else:
            SondajetdrView.limpiarGraficaSondajestdr()
    
    def obtenerListaEquiposMarcados(lista, tipolista):
        equiposmarcados = []
        for region, instrumentos in lista.items():
            for tipo, lista_equipos in instrumentos.items():
                if tipo[0] == tipolista:
                    equiposmarcados.append((region, lista_equipos))
        return equiposmarcados
            
    def graficarSondajestdrMarcados(sondajetdrmarcados):
        widget_tdr = SondajetdrView.main.findChild(QWidget, "widget_tdr")
        tipo_grafico_TDR = SondajetdrView.main.findChild(QComboBox, "cb_tipo_graficas_tdr")
        id_seleccionado = tipo_grafico_TDR.currentData()
        combo_medidas = SondajetdrView.main.findChild(QComboBox, "combo_medida_sondajestdr")
        unidadmedida = combo_medidas.currentData()
        
        datos, fallas = TDRController.ctrlObtenerLecturasTDR(SondajetdrView.idproyecto, sondajetdrmarcados, unidadmedida)
        
        if len(datos) > 0:
            # Graficar datos principales
            GraficarImpedancia.graficarImpedanciaTDR(SondajetdrView.idproyecto, widget_tdr, datos, fallas, id_seleccionado, unidadmedida)
            
            # REPINTAR UMBRALES (igual que acelerógrafos e inclinómetros)
            SondajetdrView._repintarUmbrales(sondajetdrmarcados)
        else:
            SondajetdrView.limpiarGraficaSondajestdr()
    
    def limpiarGraficaSondajestdr():
        widget_tdr = SondajetdrView.main.findChild(QWidget, "widget_tdr")
        GraficarImpedancia.limpiar_widget(widget_tdr)
        SondajetdrView.umbral_activo_tdr = False
        SondajetdrView.umbral_modo = None
        SondajetdrView.umbral_general_componente = None
        SondajetdrView.umbrales_cache = None
    
    def reiniciarVistaTDR(main, proyecto_id, proyecto_name):
        # reiniciar variables
        SondajetdrView.main = main
        SondajetdrView.idproyecto = proyecto_id
        SondajetdrView.nameproyecto = proyecto_name
        SondajetdrView.estadochecklist = True
        SondajetdrView.umbral_activo_tdr = False
        SondajetdrView.umbral_modo = None
        SondajetdrView.umbral_general_componente = None
        SondajetdrView.umbrales_cache = None
        SondajetdrView.limpiarGraficaSondajestdr()
        
        # LIMPIAR EL BUSCADOR AL CAMBIAR DE PROYECTO
        buscador_arbol = main.findChild(QLineEdit, "input_buscar_tdr")
        if buscador_arbol is not None:
            buscador_arbol.blockSignals(True)
            buscador_arbol.clear()
            buscador_arbol.blockSignals(False)
    
    def mostrarModalConfiguracionEjes(treeWidget):
        lista = EquiposSondajestdr.obtener_todos_elementos_marcados(treeWidget)
        if lista:
            sondajetdrmarcados = SondajetdrView.obtenerListaEquiposMarcados(lista, "TDR")
            if len(sondajetdrmarcados) > 0:
                combotipomedida = SondajetdrView.main.findChild(QComboBox, "combo_medida_sondajestdr")
                unidadmedida = combotipomedida.currentData()
                tipo_grafico_TDR = SondajetdrView.main.findChild(QComboBox, "cb_tipo_graficas_tdr")
                id_seleccionado = tipo_grafico_TDR.currentData()
                infoeje = ConfiguracionController.ctrlObtenerConfiguracionEjeTDR(SondajetdrView.idproyecto)
                if infoeje:
                    ejexmin, ejexmax, ejexprim, ejexsecu = infoeje[2], infoeje[3], infoeje[4], infoeje[5]
                    ejeymin, ejeymax, ejeyprim, ejeysecu = infoeje[6], infoeje[7], infoeje[8], infoeje[9]
                else:
                    ejexmin, ejexmax, ejexprim, ejexsecu, ejeymin, ejeymax, ejeyprim, ejeysecu = 0, 0, 0, 0, 0, 0, 0, 0
                estadoeje, minejex, maxejex, xprimario, xsecundario, minejey, maxejey, yprimario, ysecundario = Personalizacion.dialogoConfiguracionEjesTDR(id_seleccionado, ejexmin, ejexmax, ejexprim, ejexsecu, ejeymin, ejeymax, ejeyprim, ejeysecu, unidadmedida)
                if estadoeje:
                    # guardar configuracion
                    respuesta = ConfiguracionController.ctrlActualizarConfiguracionEjesTDR(SondajetdrView.idproyecto, minejex, maxejex, xprimario, xsecundario, minejey, maxejey, yprimario, ysecundario)
                    if respuesta:
                        SondajetdrView.graficarSondajestdrMarcados(sondajetdrmarcados)
    
    def mostrarDialogoReporteSondajestdr(treeWidget, widget_grafico, combo_tipo_grafico, tiporeporte):
        if SondajetdrView.idproyecto:
            lista = EquiposSondajestdr.obtener_todos_elementos_marcados(treeWidget)
            if lista:
                tipografico = combo_tipo_grafico.currentData()
                titulografica = combo_tipo_grafico.currentText()
                tipoequipo = "Sondajetdr"
                if tiporeporte == "General":
                    GraficaReporte.mostrarDialogoImagenVisor(widget_grafico, "Sondajes", tipografico, titulografica, SondajetdrView.idproyecto, tipoequipo)
                else:
                    ReporteImage.modalImagenReporte(widget_grafico, "Sondajes", tipografico, titulografica, SondajetdrView.idproyecto, tipoequipo)
    
    def iniciarAsistenteVozSondajestdr(treeWidget, botonvoz):
        lista = EquiposSondajestdr.obtener_todos_elementos_marcados(treeWidget)
        if lista:
            sondajetdrmarcados = SondajetdrView.obtenerListaEquiposMarcados(lista, "TDR")
            if len(sondajetdrmarcados) > 0:
                botonvoz.setEnabled(False)
                hilo_asistente = threading.Thread(target=AsistenteVoz.analizarSondajestdr, args=(SondajetdrView.idproyecto, sondajetdrmarcados, botonvoz))
                hilo_asistente.start()