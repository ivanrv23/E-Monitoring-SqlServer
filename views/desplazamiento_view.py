import threading
from PySide6.QtWidgets import (QWidget, QLabel, QComboBox, QTreeWidget, QPushButton, QSpinBox,QMenu)
from PySide6.QtCore import Qt
from utils.shared.graficaDesplazamientoVelocidad import procesar_grafica
from utils.shared.graficaDesplazamientoVelocidad import limpiar_widget
from controllers.DesplazamientoController import DesplazamientoController
from controllers.PluviometroController import PluviometroController
from controllers.ConfiguracionController import ConfiguracionController
from modules.datos.equiposDesplazamiento import EquiposDesplazamiento
from utils.shared.guardarImagenReporte import ReporteImage
from utils.shared.graficareporte import GraficaReporte
from utils.common.metodosGenerales import MetodosGenerales
from utils.shared.resumenprismas import ResumenPrismas
from utils.shared.asistentedevoz import AsistenteVoz
from utils.shared.personalizacion import Personalizacion
from utils.shared.calculostendencias import CalculosTendencias
from modules.empresa.softwareconfiguracion import SoftwareConfiguracion
from controllers.UmbralController import UmbralController
from utils.shared.graficarUmbrales import GraficarUmbrales
from utils.generic.graficarumbralespersonalizados import graficarUmbralesPersonalizado
from controllers.InterfazController import InterfazController

from PySide6.QtCore import QThread, Signal, QTimer

class DataWorker(QThread):
    # Señal que enviará los datos a la interfaz al terminar
    data_ready = Signal(list)

    def __init__(self, params):
        super().__init__()
        self.params = params
        self._is_killed = False # Bandera para anular el hilo

    def run(self):
        try:
            # Si se marcó como anulado antes de empezar, salimos inmediatamente
            if self._is_killed:
                return

            from controllers.DesplazamientoController import DesplazamientoController
            # Llamada al controlador (esto es lo que tarda)
            datos = DesplazamientoController.ctrlDatosPrismasMarcados(*self.params)
            
            # Solo emitimos la señal si el hilo no ha sido anulado por una nueva petición
            if not self._is_killed:
                self.data_ready.emit(datos)
        except Exception as e:
            print(f"Error en hilo de datos: {e}")
            if not self._is_killed:
                self.data_ready.emit([])

    def abort(self):
        """ Anula este hilo para que no envíe datos a la UI """
        self._is_killed = True
        
class DesplazamientoView:
    main = None
    idproyecto = None
    nameproyecto = "SIN PROYECTO"
    estadochecklist = True
    estadoPagina = True
    fechainicial, fechafinal = MetodosGenerales.obtenerRangoFechas(365)
    datos_memoria = []
    
    def inicializarVistaDesplazamiento(main, proyectoid, proyectoname, fechaini, fechafin):
        DesplazamientoView.main = main
        DesplazamientoView.idproyecto = proyectoid
        DesplazamientoView.nameproyecto = proyectoname
        DesplazamientoView.fechainicial, DesplazamientoView.fechafinal = fechaini, fechafin
        if DesplazamientoView.estadochecklist:
            tree_widget = main.findChild(QTreeWidget, "tree_actual_desplazamiento")
            tree_widget.setHeaderLabels([DesplazamientoView.nameproyecto.upper()])
            EquiposDesplazamiento.inicializar_lista_equipos(tree_widget, DesplazamientoView.idproyecto, DesplazamientoView.nameproyecto)
            
            def sincronizar_memoria(nodo):
                for i in range(nodo.childCount()):
                    hijo = nodo.child(i)
                    hijo.setData(0, Qt.UserRole + 999, hijo.checkState(0))
                    sincronizar_memoria(hijo)
            
            root = tree_widget.invisibleRootItem()
            sincronizar_memoria(root)

            DesplazamientoView.estadochecklist = False # Cerrar paso
        if DesplazamientoView.estadoPagina:
            tree_actual_desplaza =  main.findChild(QTreeWidget, "tree_actual_desplazamiento")
            tree_actual_desplaza.itemClicked.connect(DesplazamientoView.checkProyectoActualDesplazamiento)
            tree_actual_desplaza.setContextMenuPolicy(Qt.CustomContextMenu)
            tree_actual_desplaza.customContextMenuRequested.connect(DesplazamientoView.clicderechoProyectoActualDesplazamiento)
            # Habilitar clic derecho en el encabezado (Header)
            header = tree_actual_desplaza.header()
            header.setContextMenuPolicy(Qt.CustomContextMenu)
            header.customContextMenuRequested.connect(DesplazamientoView.clicderechoEncabezadoProyecto)
            botonRefrescarDesplazamiento = main.findChild(QPushButton, "btn_refrescar_vista_desplazamiento")
            botonRefrescarDesplazamiento.clicked.connect(lambda: DesplazamientoView.obtenerMostrarPrismasMarcados(tree_actual_desplaza))
            # Cargar Unidades de Medida
            lista_unidades_medida = [
                ('Metros', 1),
                ('Centímetros', 100),
                ('Milímetros', 1000),
            ]
            combo_medidas = main.findChild(QComboBox, "combo_medida_desplaza")
            for value, key in lista_unidades_medida:
                combo_medidas.addItem(value, key)
            combo_medidas.activated.connect(lambda: DesplazamientoView.obtenerMostrarPrismasMarcados(tree_actual_desplaza))
            # Cargar Unidades de Tiempo
            lista_unidades_tiempo = [
                ('Fechas', "FECHA"),
                ('Días', "DIA"),
                ('Horas', "HORA"),
            ]
            combo_tiempos = main.findChild(QComboBox, "combo_tiempo_desplaza")
            for value, key in lista_unidades_tiempo:
                combo_tiempos.addItem(value, key)
            combo_tiempos.activated.connect(lambda: DesplazamientoView.obtenerMostrarPrismasMarcados(tree_actual_desplaza))
            # Cargar Combo Promedios
            lista_unidades_promedio = [
                ('Sin Promedios', "SPRO"),
                ('Promedio en Días', "PDIA"),
                ('Promedio en Horas', "PHORA"),
            ]
            combo_promedios = main.findChild(QComboBox, "combo_promedio_desplaza")
            for value, key in lista_unidades_promedio:
                combo_promedios.addItem(value, key)
            combo_promedios.activated.connect(lambda: DesplazamientoView.obtenerMostrarPrismasMarcados(tree_actual_desplaza))
            spin_promedio = main.findChild(QSpinBox, "spin_promedio_desplaza")
            spin_promedio.setEnabled(False)
            # Cargar tipos de desplazamiento
            lista_tipos_desplazamiento = {
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
                'DAH': 'Ángulo Horizontal',
                'AHA': 'Ángulo Horizontal Acum.',
                'AHI': 'Ángulo Horizontal Incr.',
                'DAV': 'Ángulo Vertical',
                'AVA': 'Ángulo Vertical Acum.',
                'AVI': 'Ángulo Vertical Incr.',
            }
            widget_grafico = main.findChild(QWidget, "widget_grafica_desplazamiento")
            combo_tipo_grafico = main.findChild(QWidget, "combo_tipos_desplazamiento")
            for key, value in lista_tipos_desplazamiento.items():
                combo_tipo_grafico.addItem(value, key)
            combo_tipo_grafico.activated.connect(lambda: DesplazamientoView.obtenerMostrarPrismasMarcados(tree_actual_desplaza))
            # botones
            btnResumenTabla = main.findChild(QPushButton, "btn_resumen_desplazamiento")
            btnResumenTabla.clicked.connect(DesplazamientoView.mostrarTablaResumenDesplazamiento)
            btnAsistenteVoz = main.findChild(QPushButton, "btn_voz_desplazamiento")
            btnAsistenteVoz.clicked.connect(lambda: DesplazamientoView.iniciarAsistenteVozDesplazamiento(tree_actual_desplaza, btnAsistenteVoz))
            btn_umbral_desplazamiento = main.findChild(QPushButton, "btn_umbral_desplazamiento")
            btn_umbral_desplazamiento.clicked.connect(DesplazamientoView.graficarUmbralesDesplazamiento)
            btnLimpiarRuido = main.findChild(QPushButton, "btn_limpieza_desplazamiento")
            btnLimpiarRuido.clicked.connect(lambda: DesplazamientoView.mostrarModalLimpiezaRuido(tree_actual_desplaza))
            btnTendencia = main.findChild(QPushButton, "btn_tendencia_desplazamiento")
            btnTendencia.clicked.connect(lambda: DesplazamientoView.mostrarModalTendencia(tree_actual_desplaza))
            btnEjesDesplaza = main.findChild(QPushButton, "btn_ejes_desplazamiento")
            btnEjesDesplaza.clicked.connect(lambda: DesplazamientoView.mostrarModalConfiguracionEjes(tree_actual_desplaza))
            btn_guardar_grafico_reporte = main.findChild(QPushButton, "btn_reporte_grafica_desplazamiento")
            btn_guardar_grafico_reporte.clicked.connect(lambda: DesplazamientoView.mostrarDialogoReporteDesplazamiento(tree_actual_desplaza, widget_grafico, combo_tipo_grafico, "Anexos"))
            btnReporteGeneral = main.findChild(QPushButton, "btn_imagen_desplazamiento")
            btnReporteGeneral.clicked.connect(lambda: DesplazamientoView.mostrarDialogoReporteDesplazamiento(tree_actual_desplaza, widget_grafico, combo_tipo_grafico, "General"))
            btnAplicarUmbralPersonalizado = main.findChild(QPushButton, "btn_umbral_personalizado_D")
            btnAplicarUmbralPersonalizado.clicked.connect(DesplazamientoView.graficarUmbralesPersonalizado)

            btnExportarD = main.findChild(QPushButton, "btn_exportar_desplazamiento")
            if btnExportarD:
                btnExportarD.clicked.connect(DesplazamientoView.ejecutar_exportacion_grafica)
                
            DesplazamientoView.estadoPagina = False
    
    def clicderechoEncabezadoProyecto(point):
        tree_actual = DesplazamientoView.main.findChild(QTreeWidget, "tree_actual_desplazamiento")
        pos_global = tree_actual.header().mapToGlobal(point)
        
        menu = QMenu()
        menu.addAction("Marcar Todo").triggered.connect(lambda: EquiposDesplazamiento.marcar_desmarcar_proyecto_completo(tree_actual, Qt.Checked, lambda: DesplazamientoView.obtenerMostrarPrismasMarcados(tree_actual)))
        menu.addAction("Desmarcar Todo").triggered.connect(lambda: EquiposDesplazamiento.marcar_desmarcar_proyecto_completo(tree_actual, Qt.Unchecked, lambda: DesplazamientoView.obtenerMostrarPrismasMarcados(tree_actual)))
        
        menu.addSeparator()

        # --- OPCIÓN: APLICAR PLANTILLA ---
        def accion_aplicar():
            # Aquí la Vista usa el controlador para traer los datos
            preferencias = InterfazController.ctrlObtenerPreferenciasMarcado(DesplazamientoView.idproyecto, "PRISMAS_GLOBAL")
            # Y se los pasa limpios al método del árbol
            EquiposDesplazamiento.aplicar_marcado_predeterminado(
                tree_actual, preferencias, lambda: DesplazamientoView.obtenerMostrarPrismasMarcados(tree_actual)
            )
        
        menu.addAction("Marcar según Plantilla").triggered.connect(accion_aplicar)

        def accion_configurar():
            tree_actual = DesplazamientoView.main.findChild(QTreeWidget, "tree_actual_desplazamiento")
            
            # 1. Recuperamos lo que ya hay en base de datos para sincronizar el modal
            prefs_actuales = InterfazController.ctrlObtenerPreferenciasMarcado(
                DesplazamientoView.idproyecto, "PRISMAS_GLOBAL"
            )
            if prefs_actuales is None: prefs_actuales = []

            # 2. Definimos callback de guardado
            def callback_guardar(lista_datos):
                return InterfazController.ctrlGuardarPreferenciasMarcado(
                    DesplazamientoView.idproyecto, "PRISMAS_GLOBAL", lista_datos
                )
            
            # 3. Abrimos el modal con la sincronización
            Personalizacion.dialogoConfigurarMarcadoPredeterminado(tree_actual, prefs_actuales, callback_guardar)


        menu.addAction("Configurar Plantilla Predeterminada...").triggered.connect(accion_configurar)

        menu.exec(pos_global)
        
    def graficarUmbralesPersonalizado():
        if DesplazamientoView.idproyecto:
            widget_grafico = DesplazamientoView.main.findChild(QWidget, "widget_grafica_desplazamiento")
            combo_medidas = DesplazamientoView.main.findChild(QComboBox, "combo_medida_desplaza")
            unidad = combo_medidas.currentData()
            graficarUmbralesPersonalizado(widget_grafico,unidad,DesplazamientoView.idproyecto)
            
    def graficarUmbralesDesplazamiento():
        widget_grafico = DesplazamientoView.main.findChild(QWidget, "widget_grafica_desplazamiento")
        pintado = GraficarUmbrales.clean_on_widget(widget_grafico, 'color')
        if pintado is False:
            combo_tipo_grafico = DesplazamientoView.main.findChild(QWidget, "combo_tipos_desplazamiento")
            tipo = combo_tipo_grafico.currentData()
            combo_medidas = DesplazamientoView.main.findChild(QComboBox, "combo_medida_desplaza")
            unidad = combo_medidas.currentData()
            tree_actual = DesplazamientoView.main.findChild(QTreeWidget, "tree_actual_desplazamiento")
            lista = EquiposDesplazamiento.obtener_todos_elementos_marcados(tree_actual)
            if lista:
                prismasmarcados = DesplazamientoView.obtenerListaEquiposMarcados(lista, "Prismas")
                if len(prismasmarcados) > 0:
                    idcompo, c, umbrales = 0, 0, None
                    for componente, listaprismas in prismasmarcados:
                        idcompo = componente[1]
                        c += 1
                    if c == 1:
                        umbrales = UmbralController.ctrlObtenerUmbralesInstrumentacion(DesplazamientoView.idproyecto, idcompo, tipo, 'umbral_prisma')
                    else:
                        # validar umbrales
                        validar = UmbralController.ctrlValidarUmbralesComponentes(DesplazamientoView.idproyecto, tipo, "umbral_prisma")
                        cantidad, idcomponen = validar
                        if cantidad > 0:
                            if cantidad == 1:
                                umbrales = UmbralController.ctrlObtenerUmbralesInstrumentacion(DesplazamientoView.idproyecto, idcomponen, tipo, 'umbral_prisma')
                            else:
                                componentes = UmbralController.ctrlListarComponentesUmbrales(DesplazamientoView.idproyecto, tipo, "umbral_prisma")
                                if componentes:
                                    codigoseleccionado = GraficarUmbrales.mostrarSeleccionUmbrales(componentes, "Umbral Prismas")
                                    if codigoseleccionado:
                                        umbrales = UmbralController.ctrlObtenerUmbralesInstrumentacion(DesplazamientoView.idproyecto, codigoseleccionado, tipo, "umbral_prisma")
                    if umbrales:
                        GraficarUmbrales.draw_on_widget(widget_grafico, umbrales, unidad)
    
    def checkProyectoActualDesplazamiento(parent_item, column):
        treeWidget =  DesplazamientoView.main.findChild(QTreeWidget, "tree_actual_desplazamiento")
        EquiposDesplazamiento.validarMarcadoCheckbox(parent_item, column, lambda: DesplazamientoView.obtenerMostrarPrismasMarcados(treeWidget))
    
    def clicderechoProyectoActualDesplazamiento(point):
        treeWidget =  DesplazamientoView.main.findChild(QTreeWidget, "tree_actual_desplazamiento")
        
        # Agregamos el argumento extra: la función que dispara la gráfica
        EquiposDesplazamiento.validarOpcionesMenuCheckbox(
            point, 
            DesplazamientoView.main, 
            treeWidget, 
            DesplazamientoView.reiniciarVistasAfectadas,
            lambda: DesplazamientoView.obtenerMostrarPrismasMarcados(treeWidget)
        )
        
    def reiniciarVistasAfectadas(tipoequipo="Todos"):
        from views.datos_view import DatosView
        from views.visor_view import VisorView
        from views.velocidad_view import VelocidadView
        from views.inclinometros_view import InclinometrosView
        from views.piezometros_view import PiezometrosView
        from views.celdas_view import CeldasView
        from views.acelerografos_view import AcelerografosView
        from views.sondajestdr_view import SondajetdrView
        from views.analisis_view import AnalisisView
        if tipoequipo == "Prisma":
            DatosView.reiniciarVistaDatos(DesplazamientoView.main, DesplazamientoView.idproyecto, DesplazamientoView.nameproyecto)
            VisorView.reiniciarVistaVisor(DesplazamientoView.main, DesplazamientoView.idproyecto, DesplazamientoView.nameproyecto)
            VelocidadView.reiniciarVistaVelocidad(DesplazamientoView.main, DesplazamientoView.idproyecto, DesplazamientoView.nameproyecto)
            AnalisisView.reiniciarVistaAnalisis(DesplazamientoView.main, DesplazamientoView.idproyecto, DesplazamientoView.nameproyecto)
        else:
            DatosView.reiniciarVistaDatos(DesplazamientoView.main, DesplazamientoView.idproyecto, DesplazamientoView.nameproyecto)
            VisorView.reiniciarVistaVisor(DesplazamientoView.main, DesplazamientoView.idproyecto, DesplazamientoView.nameproyecto)
            VelocidadView.reiniciarVistaVelocidad(DesplazamientoView.main, DesplazamientoView.idproyecto, DesplazamientoView.nameproyecto)
            InclinometrosView.reiniciarVistaInclinometros(DesplazamientoView.main, DesplazamientoView.idproyecto, DesplazamientoView.nameproyecto)
            PiezometrosView.reiniciarVistaPiezometros(DesplazamientoView.main, DesplazamientoView.idproyecto, DesplazamientoView.nameproyecto)
            CeldasView.reiniciarVistaCeldas(DesplazamientoView.main, DesplazamientoView.idproyecto, DesplazamientoView.nameproyecto)
            AcelerografosView.reiniciarVistaAcelerografos(DesplazamientoView.main, DesplazamientoView.idproyecto, DesplazamientoView.nameproyecto)
            SondajetdrView.reiniciarVistaTDR(DesplazamientoView.main, DesplazamientoView.idproyecto, DesplazamientoView.nameproyecto)
            AnalisisView.reiniciarVistaAnalisis(DesplazamientoView.main, DesplazamientoView.idproyecto, DesplazamientoView.nameproyecto)
    
    # Variables de clase (Asegúrate de que existan)
    worker = None 
    timer_consulta = None 

    @staticmethod
    def obtenerMostrarPrismasMarcados(tree_actual):
        """ Maneja el temporizador para agrupar clics rápidos (Debounce) """
        if DesplazamientoView.timer_consulta is None:
            DesplazamientoView.timer_consulta = QTimer()
            DesplazamientoView.timer_consulta.setSingleShot(True)
            DesplazamientoView.timer_consulta.timeout.connect(
                lambda: DesplazamientoView.iniciar_hilo_final(tree_actual)
            )

        # Cada clic (o marcado en bloque) reinicia este reloj de 300ms
        DesplazamientoView.timer_consulta.stop()
        DesplazamientoView.timer_consulta.start(300) 

    @staticmethod
    def iniciar_hilo_final(tree_actual):
        """ Mata cualquier hilo viejo y lanza la consulta definitiva """
        # 1. Cancelación de peticiones anteriores para no saturar
        if DesplazamientoView.worker is not None and DesplazamientoView.worker.isRunning():
            try:
                DesplazamientoView.worker.data_ready.disconnect() # Desconectar eventos
                DesplazamientoView.worker.abort()                # Marcar como anulado
                DesplazamientoView.worker.terminate()            # Forzar parada
                DesplazamientoView.worker.wait()                 # Limpiar memoria
            except:
                pass

        # 2. Obtener lo que quedó marcado al final de los clics
        lista = EquiposDesplazamiento.obtener_todos_elementos_marcados(tree_actual)
        if not lista:
            DesplazamientoView.limpiarGraficaDesplazamiento()
            return

        prismasmarcados = DesplazamientoView.obtenerListaEquiposMarcados(lista, "Prismas")
        if len(prismasmarcados) == 0:
            DesplazamientoView.limpiarGraficaDesplazamiento()
            return

        # 3. Capturar valores de la interfaz (Hilo Principal)
        combo_promedios = DesplazamientoView.main.findChild(QComboBox, "combo_promedio_desplaza")
        spin_promedio = DesplazamientoView.main.findChild(QSpinBox, "spin_promedio_desplaza")
        tipopromedio = combo_promedios.currentData()
        
        spin_promedio.setEnabled(tipopromedio != "SPRO")
        numeropromedio = spin_promedio.value()
        
        tipografico = DesplazamientoView.main.findChild(QComboBox, "combo_tipos_desplazamiento").currentData()
        tipomedida = DesplazamientoView.main.findChild(QComboBox, "combo_medida_desplaza").currentData()
        tipotiempo = DesplazamientoView.main.findChild(QComboBox, "combo_tiempo_desplaza").currentData()
        config = SoftwareConfiguracion.obtenerDataSoftware()
        filtrado = config[16]

        params = (DesplazamientoView.idproyecto, prismasmarcados, DesplazamientoView.fechainicial, 
                  DesplazamientoView.fechafinal, tipografico, tipomedida, filtrado, tipopromedio, numeropromedio)

        # 4. Iniciar proceso
        DesplazamientoView.main.setCursor(Qt.WaitCursor)
        DesplazamientoView.worker = DataWorker(params)
        DesplazamientoView.worker.data_ready.connect(
            lambda datos: DesplazamientoView.finalizar_flujo(lista, datos, tipografico, tipomedida, tipotiempo)
        )
        DesplazamientoView.worker.start()

    @staticmethod
    def finalizar_flujo(lista, datos, tipografico, tipomedida, tipotiempo):
        """ Recibe la data final y manda a graficar """
        DesplazamientoView.datos_memoria = datos
        
        if len(datos) > 0:
            DesplazamientoView.graficarPrismasDesplazamiento(lista, datos, tipografico, tipomedida, tipotiempo)
        else:
            DesplazamientoView.limpiarGraficaDesplazamiento()
            
        DesplazamientoView.main.unsetCursor()
        
    def obtenerListaEquiposMarcados(lista, tipolista):
        equiposmarcados = []
        for region, instrumentos in lista.items():
            for tipo, lista_equipos in instrumentos.items():
                if tipo[0] == tipolista:
                    equiposmarcados.append((region, lista_equipos))
        return equiposmarcados
                
    def graficarPrismasDesplazamiento(lista, datos, tipografico, tipomedida, tipotiempo, tendencias=None):
        if tipomedida == 1:
            labely = "Desplazamiento (m)"
        elif tipomedida == 100:
            labely = "Desplazamiento (cm)"
        else:
            labely = "Desplazamiento (mm)"
        # tipo tiempo
        if tipotiempo  == "FECHA":
            indextiempo = 2
            labelx = "Fechas"
        elif tipotiempo  == "DIA":
            indextiempo = 4
            labelx = "Días"
        else:
            indextiempo = 3
            labelx = "Horas"
        # tipo grafico
        if tipografico == "3DA":
            titulo = "Desplazamiento Acumulado 3D"
        elif tipografico == "3DI":
            titulo = "Desplazamiento Incremental 3D"
        elif tipografico == "2DA":
            titulo = "Desplazamiento Acumulado 2D"
        elif tipografico == "2DI":
            titulo = "Desplazamiento Incremental 2D"
        elif tipografico == "SDA":
            titulo = "Desplazamiento Acumulado SD"
        elif tipografico == "SDI":
            titulo = "Desplazamiento Incremental SD"
        elif tipografico == "DLA":
            titulo = "Desplazamiento Acumulado Longitudinal"
        elif tipografico == "DLI":
            titulo = "Desplazamiento Incremental Longitudinal"
        elif tipografico == "DTA":
            titulo = "Desplazamiento Acumulado Transversal"
        elif tipografico == "DTI":
            titulo = "Desplazamiento Incremental Transversal"
        elif tipografico == "DHA":
            titulo = "Desplazamiento Acumulado Altura"
        elif tipografico == "DHI":
            titulo = "Desplazamiento Incremental Altura"
        elif tipografico == "DNA":
            titulo = "Desplazamiento Acumulado Norte"
        elif tipografico == "DNI":
            titulo = "Desplazamiento Incremental Norte"
        elif tipografico == "DEA":
            titulo = "Desplazamiento Acumulado Este"
        elif tipografico == "DEI":
            titulo = "Desplazamiento Incremental Este"
        elif tipografico == "DZA":
            titulo = "Desplazamiento Acumulado Cota"
        elif tipografico == "DZI":
            titulo = "Desplazamiento Incremental Cota"
        elif tipografico == "DAH":
            titulo = "Ángulo Horizontal"
            labely = "Ángulo (°)"
        elif tipografico == "AHA":
            titulo = "Ángulo Horizontal Acumulado"
            labely = "Ángulo (°)"
        elif tipografico == "AHI":
            titulo = "Ángulo Horizontal Incremental"
            labely = "Ángulo (°)"
        elif tipografico == "DAV":
            titulo = "Ángulo Vertical"
            labely = "Ángulo (°)"
        elif tipografico == "AVA":
            titulo = "Ángulo Vertical Acumulado"
            labely = "Ángulo (°)"
        elif tipografico == "AVI":
            titulo = "Ángulo Vertical Incremental"
            labely = "Ángulo (°)"
        widget_deplazamiento = DesplazamientoView.main.findChild(QWidget, "widget_grafica_desplazamiento")
        labeltendencia = DesplazamientoView.main.findChild(QLabel, "label_tendencia_desplaza")
        if len(datos) > 0:
            modulo = "DESPLAZAMIENTO"
            pluviometros, escala = None, None
            pluviometrosmarcados = DesplazamientoView.obtenerListaEquiposMarcados(lista, "Pluviómetros")
            if len(pluviometrosmarcados) == 1:
                datapluvio = PluviometroController.ctrlObtenerPluviometros(DesplazamientoView.idproyecto, pluviometrosmarcados, DesplazamientoView.fechainicial, DesplazamientoView.fechafinal)
                if datapluvio:
                    pluviometros = datapluvio
            config = SoftwareConfiguracion.obtenerDataSoftware()
            filtrado = config[16]
            if filtrado == 0:
                procesar_grafica(widget_deplazamiento, labeltendencia, datos, 1, indextiempo, 5, labelx, labely, tipografico, tipomedida, tipotiempo, titulo, DesplazamientoView.idproyecto, modulo, pluviometros, tendencias, escala, DesplazamientoView.fechainicial, DesplazamientoView.fechafinal)
            else:
                procesar_grafica(widget_deplazamiento, labeltendencia, datos, 1, indextiempo, 5, labelx, labely, tipografico, tipomedida, tipotiempo, titulo, DesplazamientoView.idproyecto, modulo, pluviometros, tendencias, escala)
        else:
            DesplazamientoView.limpiarGraficaDesplazamiento()
    
    def limpiarGraficaDesplazamiento():
        widget_deplazamiento = DesplazamientoView.main.findChild(QWidget, "widget_grafica_desplazamiento")
        limpiar_widget(widget_deplazamiento)
    
    def mostrarModalTendencia(treeWidget):
        lista = EquiposDesplazamiento.obtener_todos_elementos_marcados(treeWidget)
        if lista:
            prismasmarcados = DesplazamientoView.obtenerListaEquiposMarcados(lista, "Prismas")
            if len(prismasmarcados) > 0:
                regresion = Personalizacion.dialogoFiltroRegresionPrismas(prismasmarcados)
                if len(regresion) > 0:
                    combo_promedios = DesplazamientoView.main.findChild(QComboBox, "combo_promedio_desplaza")
                    spin_promedio = DesplazamientoView.main.findChild(QSpinBox, "spin_promedio_desplaza")
                    tipopromedio = combo_promedios.currentData()
                    if tipopromedio == "SPRO":
                        spin_promedio.setEnabled(False)
                    else:
                        spin_promedio.setEnabled(True)
                    numeropromedio = spin_promedio.value()
                    tipo_grafico_desplazamiento = DesplazamientoView.main.findChild(QComboBox, "combo_tipos_desplazamiento")
                    tipografico = tipo_grafico_desplazamiento.currentData()
                    combotipomedida = DesplazamientoView.main.findChild(QComboBox, "combo_medida_desplaza")
                    tipomedida = combotipomedida.currentData()
                    combotipofecha = DesplazamientoView.main.findChild(QComboBox, "combo_tiempo_desplaza")
                    tipotiempo = combotipofecha.currentData()
                    config = SoftwareConfiguracion.obtenerDataSoftware()
                    filtrado = config[16]
                    datos = DesplazamientoController.ctrlDatosPrismasMarcados(DesplazamientoView.idproyecto, prismasmarcados, DesplazamientoView.fechainicial, DesplazamientoView.fechafinal, tipografico, tipomedida, filtrado, tipopromedio, numeropromedio)
                    if len(datos) > 0:
                        DesplazamientoView.graficarPrismasDesplazamiento(lista, datos, tipografico, tipomedida, tipotiempo, regresion)
    
    def mostrarModalLimpiezaRuido(treeWidget):
        lista = EquiposDesplazamiento.obtener_todos_elementos_marcados(treeWidget)
        if lista:
            prismasmarcados = DesplazamientoView.obtenerListaEquiposMarcados(lista, "Prismas")
            if len(prismasmarcados) > 0:
                estado, metodoLimpieza, prismasLimpieza = Personalizacion.dialogoLimpiezaRuidoPrismas(prismasmarcados)
                if estado:
                    combo_promedios = DesplazamientoView.main.findChild(QComboBox, "combo_promedio_desplaza")
                    spin_promedio = DesplazamientoView.main.findChild(QSpinBox, "spin_promedio_desplaza")
                    tipopromedio = combo_promedios.currentData()
                    if tipopromedio == "SPRO":
                        spin_promedio.setEnabled(False)
                    else:
                        spin_promedio.setEnabled(True)
                    numeropromedio = spin_promedio.value()
                    tipo_grafico_desplazamiento = DesplazamientoView.main.findChild(QComboBox, "combo_tipos_desplazamiento")
                    tipografico = tipo_grafico_desplazamiento.currentData()
                    combotipomedida = DesplazamientoView.main.findChild(QComboBox, "combo_medida_desplaza")
                    tipomedida = combotipomedida.currentData()
                    combotipofecha = DesplazamientoView.main.findChild(QComboBox, "combo_tiempo_desplaza")
                    tipotiempo = combotipofecha.currentData()
                    config = SoftwareConfiguracion.obtenerDataSoftware()
                    filtrado = config[16]
                    datos = DesplazamientoController.ctrlDatosPrismasMarcados(DesplazamientoView.idproyecto, prismasmarcados, DesplazamientoView.fechainicial, DesplazamientoView.fechafinal, tipografico, tipomedida, filtrado, tipopromedio, numeropromedio)
                    if len(datos) > 0:
                        if metodoLimpieza == 'Limpieza Automática':
                            data = CalculosTendencias.limpiezaAutomaticaSaltos(datos, prismasLimpieza, 1, 5)
                        elif metodoLimpieza == 'Limpieza Manual':
                            data = CalculosTendencias.limpiezaManualSaltos(datos, prismasLimpieza, 1, 5)
                        elif metodoLimpieza == 'Ajustar Gráfico':
                            data = CalculosTendencias.ajustarCalculoSaltos(datos, prismasLimpieza, 1, 5)
                        # graficar
                        DesplazamientoView.graficarPrismasDesplazamiento(lista, data, tipografico, tipomedida, tipotiempo)
    
    def mostrarModalConfiguracionEjes(treeWidget):
        lista = EquiposDesplazamiento.obtener_todos_elementos_marcados(treeWidget)
        if lista:
            prismasmarcados = DesplazamientoView.obtenerListaEquiposMarcados(lista, "Prismas")
            if len(prismasmarcados) > 0:
                combotipomedida = DesplazamientoView.main.findChild(QComboBox, "combo_medida_desplaza")
                unidadmedida = combotipomedida.currentData()
                combotipofecha = DesplazamientoView.main.findChild(QComboBox, "combo_tiempo_desplaza")
                tipotiempo = combotipofecha.currentData()
                if tipotiempo == "HORA":
                    unidadtiempo  = 24
                else:
                    unidadtiempo  = 1
                tipo_grafico_desplazamiento = DesplazamientoView.main.findChild(QComboBox, "combo_tipos_desplazamiento")
                tipografico = tipo_grafico_desplazamiento.currentData()
                infoeje = ConfiguracionController.ctrlObtenerConfiguracionEje(DesplazamientoView.idproyecto, "DESPLAZAMIENTO", tipografico)
                if infoeje:
                    ejeymin, ejeymax, ejeyprim, ejeysecu, interdias = infoeje[4], infoeje[5], infoeje[6], infoeje[7], infoeje[8]
                else:
                    ejeymin, ejeymax, ejeyprim, ejeysecu, interdias = 0, 0, 0, 0, 0
                estadoeje, minejey, maxejey, primario, secundario, dias = Personalizacion.dialogoConfiguracionEjes(ejeymin, ejeymax, ejeyprim, ejeysecu, interdias, unidadmedida, unidadtiempo)
                if estadoeje:
                    # guardar configuracion
                    respuesta = ConfiguracionController.ctrlActualizarConfiguracionEjes(DesplazamientoView.idproyecto, "DESPLAZAMIENTO", tipografico, minejey, maxejey, primario, secundario, dias)
                    if respuesta:
                        combo_promedios = DesplazamientoView.main.findChild(QComboBox, "combo_promedio_desplaza")
                        spin_promedio = DesplazamientoView.main.findChild(QSpinBox, "spin_promedio_desplaza")
                        tipopromedio = combo_promedios.currentData()
                        if tipopromedio == "SPRO":
                            spin_promedio.setEnabled(False)
                        else:
                            spin_promedio.setEnabled(True)
                        numeropromedio = spin_promedio.value()
                        config = SoftwareConfiguracion.obtenerDataSoftware()
                        filtrado = config[16]
                        datos = DesplazamientoController.ctrlDatosPrismasMarcados(DesplazamientoView.idproyecto, prismasmarcados, DesplazamientoView.fechainicial, DesplazamientoView.fechafinal, tipografico, unidadmedida, filtrado, tipopromedio, numeropromedio)
                        if len(datos) > 0:
                            DesplazamientoView.graficarPrismasDesplazamiento(lista, datos, tipografico, unidadmedida, tipotiempo)
    
    def mostrarTablaResumenDesplazamiento():
        if DesplazamientoView.idproyecto:
            ResumenPrismas.modalResumenTablaPrismas("DESPLAZAMIENTO", DesplazamientoView.idproyecto, DesplazamientoView.fechainicial, DesplazamientoView.fechafinal)
    
    def mostrarDialogoReporteDesplazamiento(treeWidget, widget_grafico, combo_tipo_grafico, tiporeporte):
        if DesplazamientoView.idproyecto:
            lista = EquiposDesplazamiento.obtener_todos_elementos_marcados(treeWidget)
            if lista:
                tipografico = combo_tipo_grafico.currentData()
                titulografica = f"Desplazamiento {tipografico}"
                tipoequipo = "Prisma"
                if tiporeporte == "General":
                    GraficaReporte.mostrarDialogoImagenVisor(widget_grafico, "Desplazamiento", tipografico, titulografica, DesplazamientoView.idproyecto, tipoequipo)
                else:
                    ReporteImage.modalImagenReporte(widget_grafico, "Desplazamiento", tipografico, titulografica, DesplazamientoView.idproyecto, tipoequipo)
    
    def actualizarVistaDesplazamiento(fechaini, fechafin, filtro=False):
        DesplazamientoView.fechainicial = fechaini
        DesplazamientoView.fechafinal = fechafin       
        if DesplazamientoView.idproyecto:
            treeWidget =  DesplazamientoView.main.findChild(QTreeWidget, "tree_actual_desplazamiento")
            DesplazamientoView.obtenerMostrarPrismasMarcados(treeWidget)
    
    def reiniciarVistaDesplazamiento(main, proyecto_id, proyecto_name):
        # reiniciar variables
        DesplazamientoView.main = main
        DesplazamientoView.idproyecto = proyecto_id
        DesplazamientoView.nameproyecto = proyecto_name
        DesplazamientoView.estadochecklist = True
        DesplazamientoView.limpiarGraficaDesplazamiento()
    
    def iniciarAsistenteVozDesplazamiento(treeWidget, botonvoz):
        lista = EquiposDesplazamiento.obtener_todos_elementos_marcados(treeWidget)
        if lista:
            prismasmarcados = DesplazamientoView.obtenerListaEquiposMarcados(lista, "Prismas")
            if len(prismasmarcados) > 0:
                tipo_grafico_desplazamiento = DesplazamientoView.main.findChild(QComboBox, "combo_tipos_desplazamiento")
                tipografico = tipo_grafico_desplazamiento.currentData()
                botonvoz.setEnabled(False)
                hilo_asistente = threading.Thread(target=AsistenteVoz.analizarDesplazamiento, args=(DesplazamientoView.idproyecto, prismasmarcados, DesplazamientoView.fechainicial, DesplazamientoView.fechafinal, tipografico, botonvoz))
                hilo_asistente.start()
    
    @staticmethod
    def ejecutar_exportacion_grafica():
        if DesplazamientoView.datos_memoria:
            MetodosGenerales.exportarDataInstrumentacion(
                DesplazamientoView.datos_memoria, 
                "Desplazamiento", 
                "EXPORT_DESPLAZAMIENTO"
            )
        else:
            from utils.common.alertas import mostrar_mensaje
            mostrar_mensaje("Exportar", "No hay datos en pantalla para exportar.", "advertencia")
    