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

class CeldasView:
    main = None
    idproyecto = None
    nameproyecto = "SIN PROYECTO"
    estadochecklist = True
    estadoPagina = True
    timer_busqueda = None
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
            btn_umbral_celda.clicked.connect(lambda: CeldasView.graficarUmbralesCeldas(widget_grafico, combograficoceldas, combo_medidas))
            btnAplicarUmbralPersonalizado = main.findChild(QPushButton, "btn_umbral_personalizado_C")
            btnAplicarUmbralPersonalizado.clicked.connect(lambda: CeldasView.graficarUmbralesPersonalizado(widget_grafico,combo_medidas,combograficoceldas))
            CeldasView.estadoPagina = False
    
    def graficarUmbralesPersonalizado(widget_grafico,combo_medidas,combograficoceldas):
        if CeldasView.idproyecto:
            unidad = combo_medidas.currentData()
            tipo = combograficoceldas.currentData()
            if tipo == "VI":
                if unidad == 1:
                    unimedida = 1
                elif unidad == 100:
                    unimedida = 100
                else:
                    unimedida = 1000
            elif tipo == "AC":
                unimedida = 1
            elif tipo == "AI" or tipo == "AA":
                if unidad == 1:
                    unimedida = 1
                elif unidad == 100:
                    unimedida = 100
                else:
                    unimedida = 1000
            elif tipo == "AF":
                unimedida = 1
            else: # AT
                unimedida = 1
            graficarUmbralesPersonalizado(widget_grafico,unimedida,CeldasView.idproyecto)
            
    def graficarUmbralesCeldas(widget_grafico, combograficoceldas, combo_medidas):
        pintado = GraficarUmbrales.clean_on_widget(widget_grafico, 'color')
        if pintado is False:
            tree_actual =  CeldasView.main.findChild(QTreeWidget, "tree_actual_celdas")
            lista = EquiposCeldas.obtener_todos_elementos_marcados(tree_actual)
            if lista:
                umbrales = None
                tipo = combograficoceldas.currentData()
                celdasmarcadas, cotasmarcadas = CeldasView.obtenerListaEquiposMarcados(lista, "Celdas de Asentamiento")
                if len(celdasmarcadas) > 0:
                    if len(celdasmarcadas) == 1:
                        for grupo in celdasmarcadas:
                            for celdita in grupo:
                                nombrepie, idinstru, idcelda = celdita
                        umbrales = UmbralController.ctrlObtenerUmbralesInstrumentacion(CeldasView.idproyecto, idcelda, tipo, "umbral_celda")
                        if umbrales is None:
                            validar = UmbralController.ctrlValidarUmbralesCeldas(CeldasView.idproyecto, tipo)
                            cantidad, idceldita = validar
                            if cantidad > 0:
                                if cantidad == 1:
                                    umbrales = UmbralController.ctrlObtenerUmbralesInstrumentacion(CeldasView.idproyecto, idceldita, tipo, "umbral_celda")
                                else:
                                    # Traer lista de piezometros
                                    celdaslista = UmbralController.ctrlListarCeldasUmbrales(CeldasView.idproyecto, tipo)
                                    if celdaslista:
                                        codigoseleccionado = GraficarUmbrales.mostrarSeleccionUmbrales(celdaslista, "Umbral Celdas")
                                        if codigoseleccionado:
                                            umbrales = UmbralController.ctrlObtenerUmbralesInstrumentacion(CeldasView.idproyecto, codigoseleccionado, tipo, "umbral_celda")
                    else:
                        # VALIDAR SI HAY VARIOS UMBRALES
                        validar = UmbralController.ctrlValidarUmbralesCeldas(CeldasView.idproyecto, tipo)
                        cantidad, idceldita = validar
                        if cantidad > 0:
                            if cantidad == 1:
                                umbrales = UmbralController.ctrlObtenerUmbralesInstrumentacion(CeldasView.idproyecto, idceldita, tipo, "umbral_celda")
                            else:
                                # Traer lista de piezometros
                                celdaslista = UmbralController.ctrlListarCeldasUmbrales(CeldasView.idproyecto, tipo)
                                if celdaslista:
                                    codigoseleccionado = GraficarUmbrales.mostrarSeleccionUmbrales(celdaslista, "Umbral Celdas")
                                    if codigoseleccionado:
                                        umbrales = UmbralController.ctrlObtenerUmbralesInstrumentacion(CeldasView.idproyecto, codigoseleccionado, tipo, "umbral_celda")
                    if umbrales:
                        unidad = combo_medidas.currentData()
                        if tipo == "VI":
                            if unidad == 1:
                                unimedida = 1
                            elif unidad == 100:
                                unimedida = 100
                            else:
                                unimedida = 1000
                        elif tipo == "AC":
                            unimedida = 1
                        elif tipo == "AI" or tipo == "AA":
                            if unidad == 1:
                                unimedida = 1
                            elif unidad == 100:
                                unimedida = 100
                            else:
                                unimedida = 1000
                        elif tipo == "AF":
                            unimedida = 1
                        else: # AT
                            unimedida = 1
                        GraficarUmbrales.draw_on_widget(widget_grafico, umbrales, unimedida)
    
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
            celdasmarcadas, cotasmarcadas = CeldasView.obtenerListaEquiposMarcados(lista, "Celdas de Asentamiento")
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
                    CeldasView.graficarCeldasAsentamientoMarcadas(lista, datos, cotasmarcadas, idx_funda, idx_super, tipografica, unidadmedida, unidadtiempo)
                else:
                    CeldasView.limpiarGraficaCeldas()
            else:
                CeldasView.limpiarGraficaCeldas()
        else:
            CeldasView.limpiarGraficaCeldas()
    
    def obtenerListaEquiposMarcados(lista, tipolista):
        equiposmarcados = []
        cotasmarcadas = []
        for region, instrumentos in lista.items():
            for tipo, lista_equipos in instrumentos.items():
                if tipo[0] == tipolista:
                    for celda, cotas in lista_equipos.items():
                        equiposmarcados.append((region, celda))
                        cotasmarcadas.append((celda, cotas))
        return equiposmarcados, cotasmarcadas
    
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
            # validar tipo de filtrado
            if filtrado == 0:
                procesar_grafica_piezometros(widget_celdas, labeltendencia, datos, cotasmarcadas, 1, indextiempo, ubicacion, idx_funda, idx_super, labelx, labely, tipografico, unidadmedida, unidadtiempo, titulo, CeldasView.idproyecto, modulo, pluviometros, tendencias, None, CeldasView.fechainicial, CeldasView.fechafinal)
            else:
                procesar_grafica_piezometros(widget_celdas, labeltendencia, datos, cotasmarcadas, 1, indextiempo, ubicacion, idx_funda, idx_super, labelx, labely, tipografico, unidadmedida, unidadtiempo, titulo, CeldasView.idproyecto, modulo, pluviometros, tendencias)
    
    def limpiarGraficaCeldas():
        widget_celdas = CeldasView.main.findChild(QWidget, "widget_celdas_asentamiento")
        limpiar_widget(widget_celdas)
       
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
            celdasmarcadas, cotasmarcadas = CeldasView.obtenerListaEquiposMarcados(lista, "Celdas de Asentamiento")
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
                            CeldasView.graficarCeldasAsentamientoMarcadas(lista, data, cotasmarcadas, idx_funda, idx_super, tipografica, unidadmedida, unidadtiempo)
    
    def mostrarModalTendencia(treeWidget):
        lista = EquiposCeldas.obtener_todos_elementos_marcados(treeWidget)
        if lista:
            celdasmarcadas, cotasmarcadas = CeldasView.obtenerListaEquiposMarcados(lista, "Celdas de Asentamiento")
            if len(celdasmarcadas) > 0:
                regresion = Personalizacion.dialogoFiltroRegresionPiezometrosCeldas(celdasmarcadas, "CELDAS")
                if len(regresion) > 0:
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
    
    def mostrarModalConfiguracionEjes(treeWidget):
        lista = EquiposCeldas.obtener_todos_elementos_marcados(treeWidget)
        if lista:
            celdasmarcadas, cotasmarcadas = CeldasView.obtenerListaEquiposMarcados(lista, "Celdas de Asentamiento")
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
                else:
                    ejeymin, ejeymax, ejeyprim, ejeysecu, interdias = 0, 0, 0, 0, 0
                estadoeje, minejey, maxejey, primario, secundario, dias = Personalizacion.dialogoConfiguracionEjes(ejeymin, ejeymax, ejeyprim, ejeysecu, interdias, unidadmedida, unidadtiempo)
                if estadoeje:
                    # guardar configuracion
                    respuesta = ConfiguracionController.ctrlActualizarConfiguracionEjes(CeldasView.idproyecto, "CELDAS", tipografica, minejey, maxejey, primario, secundario, dias)
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
                            CeldasView.graficarCeldasAsentamientoMarcadas(lista, datos, cotasmarcadas, idx_funda, idx_super, tipografica, unidadmedida, tipotiempo)
    
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
            celdasmarcadas, cotasmarcadas = CeldasView.obtenerListaEquiposMarcados(lista, "Celdas de Asentamiento")
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
    