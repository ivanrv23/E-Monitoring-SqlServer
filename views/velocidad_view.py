import threading
from PySide6.QtWidgets import (QWidget, QLabel, QComboBox, QTreeWidget, QPushButton, QSpinBox,QMenu)
from PySide6.QtCore import Qt
from utils.shared.graficaDesplazamientoVelocidad import procesar_grafica
from utils.shared.graficaDesplazamientoVelocidad import limpiar_widget
from controllers.VelocidadController import VelocidadController
from controllers.PluviometroController import PluviometroController
from controllers.ConfiguracionController import ConfiguracionController
from modules.datos.equiposVelocidad import EquiposVelocidad
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

class DataWorkerVelocidad(QThread):
    # Señal que enviará los datos cuando termine
    data_ready = Signal(list)

    def __init__(self, params):
        super().__init__()
        self.params = params
        self._is_killed = False # Bandera para ignorar resultados obsoletos

    def run(self):
        try:
            if self._is_killed: return
            
            from controllers.VelocidadController import VelocidadController
            # Llamada al controlador original
            datos = VelocidadController.ctrlDatosPrismasMarcados(*self.params)
            
            if not self._is_killed:
                self.data_ready.emit(datos)
        except Exception as e:
            print(f"Error en hilo de velocidad: {e}")
            if not self._is_killed:
                self.data_ready.emit([])

    def abort(self):
        """ Anula este hilo para que no envíe datos a la UI """
        self._is_killed = True

class VelocidadView:
    main = None
    idproyecto = None
    nameproyecto = "SIN PROYECTO"
    estadochecklist = True
    estadoPagina = True
    fechainicial, fechafinal = MetodosGenerales.obtenerRangoFechas(365)
    datos_memoria = []
    
    def inicializarVistaVelocidad(main, proyectoid, proyectoname, fechaini, fechafin):
        VelocidadView.main = main
        VelocidadView.idproyecto = proyectoid
        VelocidadView.nameproyecto = proyectoname
        VelocidadView.fechainicial, VelocidadView.fechafinal = fechaini, fechafin
        if VelocidadView.estadochecklist:
            tree_widget = main.findChild(QTreeWidget, "tree_actual_velocidad")
            tree_widget.setHeaderLabels([VelocidadView.nameproyecto.upper()])
            EquiposVelocidad.inicializar_lista_equipos(tree_widget, VelocidadView.idproyecto, VelocidadView.nameproyecto)
            def sincronizar_memoria(nodo):
                for i in range(nodo.childCount()):
                    hijo = nodo.child(i)
                    hijo.setData(0, Qt.UserRole + 999, hijo.checkState(0))
                    sincronizar_memoria(hijo)
            
            root = tree_widget.invisibleRootItem()
            sincronizar_memoria(root)
            VelocidadView.estadochecklist = False
        if VelocidadView.estadoPagina:
            tree_actual_velocidad =  main.findChild(QTreeWidget, "tree_actual_velocidad")
            tree_actual_velocidad.itemClicked.connect(VelocidadView.checkProyectoActualVelocidad)
            tree_actual_velocidad.setContextMenuPolicy(Qt.CustomContextMenu)
            tree_actual_velocidad.customContextMenuRequested.connect(VelocidadView.clicderechoProyectoActualVelocidad)
            header = tree_actual_velocidad.header()
            header.setContextMenuPolicy(Qt.CustomContextMenu)
            header.customContextMenuRequested.connect(VelocidadView.clicderechoEncabezadoProyecto)
            botonRefrescarVelocidad = main.findChild(QPushButton, "btn_refrescar_vista_velocidad")
            botonRefrescarVelocidad.clicked.connect(lambda: VelocidadView.obtenerMostrarPrismasMarcados(tree_actual_velocidad))
            btn_umbral_velocidad = main.findChild(QPushButton, "btn_umbral_velocidad")
            btn_umbral_velocidad.clicked.connect(VelocidadView.graficarUmbralesVelocidad)
            # Cargar Unidades de Medida
            lista_unidades_medida = [
                ('Metros/día', "MD"),
                ('Centímetros/día', "CMD"),
                ('Milímetros/día', "MMD"),
                ('Metros/hora', "MH"),
                ('Centímetros/hora', "CMH"),
                ('Milímetros/hora', "MMH"),
            ]
            combo_medidas = main.findChild(QComboBox, "combo_medida_velocidad")
            for value, key in lista_unidades_medida:
                combo_medidas.addItem(value, key)
            combo_medidas.activated.connect(lambda: VelocidadView.obtenerMostrarPrismasMarcados(tree_actual_velocidad))
            # Cargar Unidades de Tiempo
            lista_unidades_tiempo = [
                ('Fechas', "FECHA"),
                ('Días', "DIA"),
                ('Horas', "HORA"),
            ]
            combo_tiempos = main.findChild(QComboBox, "combo_tiempo_velocidad")
            for value, key in lista_unidades_tiempo:
                combo_tiempos.addItem(value, key)
            combo_tiempos.activated.connect(lambda: VelocidadView.obtenerMostrarPrismasMarcados(tree_actual_velocidad))
            # Cargar Combo Promedios
            lista_unidades_promedio = [
                ('Sin Promedios', "SPRO"),
                ('Promedio en Días', "PDIA"),
                ('Promedio en Horas', "PHORA"),
            ]
            combo_promedios = main.findChild(QComboBox, "combo_promedio_velocidad")
            for value, key in lista_unidades_promedio:
                combo_promedios.addItem(value, key)
            combo_promedios.activated.connect(lambda: VelocidadView.obtenerMostrarPrismasMarcados(tree_actual_velocidad))
            spin_promedio = main.findChild(QSpinBox, "spin_promedio_velocidad")
            spin_promedio.setEnabled(False)
            # Cargar tipos de desplazamiento
            lista_tipos_velocidad = {
                'VI3D': 'Velocidad Incremental 3D',
                'VA3D': 'Velocidad Acumulada 3D',
                'VI2D': 'Velocidad Incremental 2D',
                'VA2D': 'Velocidad Acumulada 2D',
                'VISD': 'Velocidad Incremental SD',
                'VASD': 'Velocidad Acumulada SD',
            }
            # Localizamos el QComboBox en la interfaz
            widget_grafico = main.findChild(QWidget, "widget_grafica_velocidad")
            combo_tipo_grafico = main.findChild(QWidget, "combo_tipos_velocidad")
            for key, value in lista_tipos_velocidad.items():
                combo_tipo_grafico.addItem(value, key)
            combo_tipo_grafico.activated.connect(lambda: VelocidadView.obtenerMostrarPrismasMarcados(tree_actual_velocidad))
            # botones
            btnResumenTabla = main.findChild(QPushButton, "btn_resumen_velocidad")
            btnResumenTabla.clicked.connect(VelocidadView.mostrarTablaResumenVelocidad)
            btnAsistenteVoz = main.findChild(QPushButton, "btn_voz_velocidad")
            btnAsistenteVoz.clicked.connect(lambda: VelocidadView.iniciarAsistenteVozVelocidad(tree_actual_velocidad, btnAsistenteVoz))
            btnLimpiarRuido = main.findChild(QPushButton, "btn_limpieza_velocidad")
            btnLimpiarRuido.clicked.connect(lambda: VelocidadView.mostrarModalLimpiezaRuido(tree_actual_velocidad))
            btnTendencia = main.findChild(QPushButton, "btn_tendencia_velocidad")
            btnTendencia.clicked.connect(lambda: VelocidadView.mostrarModalTendencia(tree_actual_velocidad))
            btnEjesVelocidad = main.findChild(QPushButton, "btn_ejes_velocidad")
            btnEjesVelocidad.clicked.connect(lambda: VelocidadView.mostrarModalConfiguracionEjes(tree_actual_velocidad))
            btn_guardar_grafico_reporte = main.findChild(QPushButton, "btn_reporte_grafica_velocidad")
            btn_guardar_grafico_reporte.clicked.connect(lambda: VelocidadView.mostrarDialogoReporteVelocidad(tree_actual_velocidad, widget_grafico, combo_tipo_grafico, "Anexos"))
            btnReporteGeneral = main.findChild(QPushButton, "btn_imagen_velocidad")
            btnReporteGeneral.clicked.connect(lambda: VelocidadView.mostrarDialogoReporteVelocidad(tree_actual_velocidad, widget_grafico, combo_tipo_grafico, "General"))
            btnAplicarUmbralPersonalizado = main.findChild(QPushButton, "btn_umbral_personalizado_V")
            btnAplicarUmbralPersonalizado.clicked.connect(VelocidadView.graficarUmbralesPersonalizado)
                        
            btnExportarV = main.findChild(QPushButton, "btn_exportar_velocidad")
            if btnExportarV:
                btnExportarV.clicked.connect(VelocidadView.ejecutar_exportacion_grafica)
            VelocidadView.estadoPagina = False
            
    # En VelocidadView (dentro de la clase)
    def clicderechoEncabezadoProyecto(point):
        tree_actual = VelocidadView.main.findChild(QTreeWidget, "tree_actual_velocidad")
        # LA CLAVE: El mapeo debe ser desde el header al Global
        pos_global = tree_actual.header().mapToGlobal(point)
        
        menu = QMenu()
        # 1. Marcar Todo
        menu.addAction("Marcar Todo").triggered.connect(lambda: EquiposVelocidad.marcar_desmarcar_proyecto_completo(
            tree_actual, Qt.Checked, lambda: VelocidadView.obtenerMostrarPrismasMarcados(tree_actual)))
        
        # 2. Desmarcar Todo
        menu.addAction("Desmarcar Todo").triggered.connect(lambda: EquiposVelocidad.marcar_desmarcar_proyecto_completo(
            tree_actual, Qt.Unchecked, lambda: VelocidadView.obtenerMostrarPrismasMarcados(tree_actual)))
        
        menu.addSeparator()

        # 3. Marcar según Plantilla (Lógica de Desplazamiento)
        def accion_aplicar():
            preferencias = InterfazController.ctrlObtenerPreferenciasMarcado(VelocidadView.idproyecto, "PRISMAS_GLOBAL")
            EquiposVelocidad.aplicar_marcado_predeterminado(
                tree_actual, preferencias, lambda: VelocidadView.obtenerMostrarPrismasMarcados(tree_actual)
            )
        
        menu.addAction("Marcar según Plantilla").triggered.connect(accion_aplicar)

        # 4. Configurar Plantilla (Lógica de Desplazamiento)
        def accion_configurar():
            prefs_actuales = InterfazController.ctrlObtenerPreferenciasMarcado(VelocidadView.idproyecto, "PRISMAS_GLOBAL")
            if prefs_actuales is None: prefs_actuales = []

            def callback_guardar(lista_datos):
                return InterfazController.ctrlGuardarPreferenciasMarcado(VelocidadView.idproyecto, "PRISMAS_GLOBAL", lista_datos)
            
            Personalizacion.dialogoConfigurarMarcadoPredeterminado(tree_actual, prefs_actuales, callback_guardar)

        menu.addAction("Configurar Plantilla Predeterminada...").triggered.connect(accion_configurar)

        menu.exec(pos_global)
        
    def graficarUmbralesPersonalizado():
        if VelocidadView.idproyecto:
            widget_grafico = VelocidadView.main.findChild(QWidget, "widget_grafica_velocidad")
            combo_medidas = VelocidadView.main.findChild(QComboBox, "combo_medida_velocidad")
            unidad = combo_medidas.currentData()
            if unidad == "MD":
                unidadmedida = 1
            elif unidad == "CMD":
                unidadmedida = 100
            elif unidad == "MMD":
                unidadmedida = 1000
            elif unidad == "MH":
                unidadmedida = 1/24
            elif unidad == "CMH":
                unidadmedida = 100/24
            else:
                unidadmedida = 1000/24
            graficarUmbralesPersonalizado(widget_grafico,unidadmedida,VelocidadView.idproyecto)
            
    def graficarUmbralesVelocidad():
        widget_grafico = VelocidadView.main.findChild(QWidget, "widget_grafica_velocidad")
        pintado = GraficarUmbrales.clean_on_widget(widget_grafico, 'color')
        if pintado is False:
            combo_tipo_grafico = VelocidadView.main.findChild(QWidget, "combo_tipos_velocidad")
            tipo = combo_tipo_grafico.currentData()
            combo_medidas = VelocidadView.main.findChild(QComboBox, "combo_medida_velocidad")
            unidad = combo_medidas.currentData()
            if unidad == "MD":
                unidadmedida = 1
            elif unidad == "CMD":
                unidadmedida = 100
            elif unidad == "MMD":
                unidadmedida = 1000
            elif unidad == "MH":
                unidadmedida = 1/24
            elif unidad == "CMH":
                unidadmedida = 100/24
            else:
                unidadmedida = 1000/24
            tree_actual = VelocidadView.main.findChild(QTreeWidget, "tree_actual_velocidad")
            lista = EquiposVelocidad.obtener_todos_elementos_marcados(tree_actual)
            if lista:
                prismasmarcados = VelocidadView.obtenerListaEquiposMarcados(lista, "Prismas")
                if len(prismasmarcados) > 0:
                    idcompo, c, umbrales = 0, 0, None
                    for componente, listaprismas in prismasmarcados:
                        idcompo = componente[1]
                        c += 1
                    if c == 1:
                        umbrales = UmbralController.ctrlObtenerUmbralesInstrumentacion(VelocidadView.idproyecto, idcompo, tipo, 'umbral_prisma')
                    else:
                        # validar umbrales
                        validar = UmbralController.ctrlValidarUmbralesComponentes(VelocidadView.idproyecto, tipo, "umbral_prisma")
                        cantidad, idcomponen = validar
                        if cantidad > 0:
                            if cantidad == 1:
                                umbrales = UmbralController.ctrlObtenerUmbralesInstrumentacion(VelocidadView.idproyecto, idcomponen, tipo, 'umbral_prisma')
                            else:
                                componentes = UmbralController.ctrlListarComponentesUmbrales(VelocidadView.idproyecto, tipo, "umbral_prisma")
                                if componentes:
                                    codigoseleccionado = GraficarUmbrales.mostrarSeleccionUmbrales(componentes, "Umbral Prismas")
                                    if codigoseleccionado:
                                        umbrales = UmbralController.ctrlObtenerUmbralesInstrumentacion(VelocidadView.idproyecto, codigoseleccionado, tipo, "umbral_prisma")
                    if umbrales:
                        GraficarUmbrales.draw_on_widget(widget_grafico, umbrales, unidadmedida)
    
    def checkProyectoActualVelocidad(parent_item, column):
        treeWidget =  VelocidadView.main.findChild(QTreeWidget, "tree_actual_velocidad")
        EquiposVelocidad.validarMarcadoCheckbox(parent_item, column, lambda: VelocidadView.obtenerMostrarPrismasMarcados(treeWidget))
        
    def clicderechoProyectoActualVelocidad(point):
        treeWidget =  VelocidadView.main.findChild(QTreeWidget, "tree_actual_velocidad")
        
        # Añade el lambda al final para enviar la función de graficado
        EquiposVelocidad.validarOpcionesMenuCheckbox(
            point, 
            VelocidadView.main, 
            treeWidget, 
            VelocidadView.reiniciarVistasAfectadas,
            lambda: VelocidadView.obtenerMostrarPrismasMarcados(treeWidget)
        )
    
    def reiniciarVistasAfectadas(tipoequipo="Todos"):
        from views.datos_view import DatosView
        from views.visor_view import VisorView
        from views.desplazamiento_view import DesplazamientoView
        from views.inclinometros_view import InclinometrosView
        from views.piezometros_view import PiezometrosView
        from views.celdas_view import CeldasView
        from views.acelerografos_view import AcelerografosView
        from views.sondajestdr_view import SondajetdrView
        from views.analisis_view import AnalisisView
        if tipoequipo == "Prisma":
            DatosView.reiniciarVistaDatos(VelocidadView.main, VelocidadView.idproyecto, VelocidadView.nameproyecto)
            VisorView.reiniciarVistaVisor(VelocidadView.main, VelocidadView.idproyecto, VelocidadView.nameproyecto)
            DesplazamientoView.reiniciarVistaDesplazamiento(VelocidadView.main, VelocidadView.idproyecto, VelocidadView.nameproyecto)
            AnalisisView.reiniciarVistaAnalisis(VelocidadView.main, VelocidadView.idproyecto, VelocidadView.nameproyecto)
        else:
            DatosView.reiniciarVistaDatos(VelocidadView.main, VelocidadView.idproyecto, VelocidadView.nameproyecto)
            VisorView.reiniciarVistaVisor(VelocidadView.main, VelocidadView.idproyecto, VelocidadView.nameproyecto)
            DesplazamientoView.reiniciarVistaDesplazamiento(VelocidadView.main, VelocidadView.idproyecto, VelocidadView.nameproyecto)
            InclinometrosView.reiniciarVistaInclinometros(VelocidadView.main, VelocidadView.idproyecto, VelocidadView.nameproyecto)
            PiezometrosView.reiniciarVistaPiezometros(VelocidadView.main, VelocidadView.idproyecto, VelocidadView.nameproyecto)
            CeldasView.reiniciarVistaCeldas(VelocidadView.main, VelocidadView.idproyecto, VelocidadView.nameproyecto)
            AcelerografosView.reiniciarVistaAcelerografos(VelocidadView.main, VelocidadView.idproyecto, VelocidadView.nameproyecto)
            SondajetdrView.reiniciarVistaTDR(VelocidadView.main, VelocidadView.idproyecto, VelocidadView.nameproyecto)
            AnalisisView.reiniciarVistaAnalisis(VelocidadView.main, VelocidadView.idproyecto, VelocidadView.nameproyecto)
    
    # Asegúrate de que estas variables estén en la clase
    worker_velocidad = None 
    timer_consulta = None

    @staticmethod
    def obtenerMostrarPrismasMarcados(tree_actual):
        """ Portero (Debounce): Agrupa clics rápidos """
        if VelocidadView.timer_consulta is None:
            VelocidadView.timer_consulta = QTimer()
            VelocidadView.timer_consulta.setSingleShot(True)
            VelocidadView.timer_consulta.timeout.connect(
                lambda: VelocidadView.iniciar_peticion_final(tree_actual)
            )

        # 300ms para que la UI se sienta instantánea pero agrupe los clics en bloque
        VelocidadView.timer_consulta.stop()
        VelocidadView.timer_consulta.start(300) 

    @staticmethod
    def iniciar_peticion_final(tree_actual):
        """ Motor: Mata procesos viejos y lanza la consulta definitiva """
        # 1. Cancelar cualquier hilo previo que esté trabajando en una selección vieja
        if VelocidadView.worker_velocidad is not None and VelocidadView.worker_velocidad.isRunning():
            try:
                VelocidadView.worker_velocidad.data_ready.disconnect()
                VelocidadView.worker_velocidad.abort()
                VelocidadView.worker_velocidad.terminate()
                VelocidadView.worker_velocidad.wait()
            except:
                pass

        # 2. Captura de la selección final del árbol
        lista = EquiposVelocidad.obtener_todos_elementos_marcados(tree_actual)
        if not lista:
            VelocidadView.limpiarGraficaVelocidad()
            VelocidadView.main.unsetCursor()
            return

        prismasmarcados = VelocidadView.obtenerListaEquiposMarcados(lista, "Prismas")
        if len(prismasmarcados) == 0:
            VelocidadView.limpiarGraficaVelocidad()
            VelocidadView.main.unsetCursor()
            return

        # 3. Capturar datos de la UI (Sincrónico y rápido)
        try:
            combo_promedios = VelocidadView.main.findChild(QComboBox, "combo_promedio_velocidad")
            spin_promedio = VelocidadView.main.findChild(QSpinBox, "spin_promedio_velocidad")
            tipopromedio = combo_promedios.currentData()
            spin_promedio.setEnabled(tipopromedio != "SPRO")
            numeropromedio = spin_promedio.value()
            
            tipografico = VelocidadView.main.findChild(QComboBox, "combo_tipos_velocidad").currentData()
            tipomedida = VelocidadView.main.findChild(QComboBox, "combo_medida_velocidad").currentData()
            
            # Tu lógica de conversión de unidades
            if tipomedida == "MD": unidadmedida = 1
            elif tipomedida == "CMD": unidadmedida = 100
            elif tipomedida == "MMD": unidadmedida = 1000
            elif tipomedida == "MH": unidadmedida = 1/24
            elif tipomedida == "CMH": unidadmedida = 100/24
            else: unidadmedida = 1000/24

            tipotiempo = VelocidadView.main.findChild(QComboBox, "combo_tiempo_velocidad").currentData()
            config = SoftwareConfiguracion.obtenerDataSoftware()
            velocprisma, filtrado = config[15], config[16]

            params = (VelocidadView.idproyecto, prismasmarcados, VelocidadView.fechainicial, 
                      VelocidadView.fechafinal, tipografico, unidadmedida, velocprisma, 
                      filtrado, tipopromedio, numeropromedio)

            # 4. Lanzar el nuevo trabajador
            VelocidadView.main.setCursor(Qt.WaitCursor)
            VelocidadView.worker_velocidad = DataWorkerVelocidad(params)
            VelocidadView.worker_velocidad.data_ready.connect(
                lambda datos: VelocidadView.finalizar_flujo_velocidad(lista, datos, tipografico, tipomedida, tipotiempo)
            )
            VelocidadView.worker_velocidad.start()

        except Exception as e:
            print(f"Error al iniciar hilo: {e}")
            VelocidadView.main.unsetCursor()

    @staticmethod
    def finalizar_flujo_velocidad(lista, datos, tipografico, tipomedida, tipotiempo):
        """ Cierre: Recibe la data del hilo y manda a dibujar """
        VelocidadView.datos_memoria = datos
        
        if len(datos) > 0:
            VelocidadView.graficarPrismasVelocidad(lista, datos, tipografico, tipomedida, tipotiempo)
        else:
            VelocidadView.limpiarGraficaVelocidad()
        
        VelocidadView.main.unsetCursor()
        
    def obtenerListaEquiposMarcados(lista, tipolista):
        equiposmarcados = []
        for region, instrumentos in lista.items():
            for tipo, lista_equipos in instrumentos.items():
                if tipo[0] == tipolista:
                    equiposmarcados.append((region, lista_equipos))
        return equiposmarcados
    
    def graficarPrismasVelocidad(lista, datos, tipografico, tipomedida, tipotiempo, tendencias=None):
        if tipomedida == "MD":
            unidadmedida = 1
            labely = "Velocidad (m/d)"
        elif tipomedida == "CMD":
            unidadmedida = 100
            labely = "Velocidad (cm/d)"
        elif tipomedida == "MMD":
            unidadmedida = 1000
            labely = "Velocidad (mm/d)"
        elif tipomedida == "MH":
            unidadmedida = 1/24
            labely = "Velocidad (m/h)"
        elif tipomedida == "CMH":
            unidadmedida = 100/24
            labely = "Velocidad (cm/h)"
        else:
            unidadmedida = 1000/24
            labely = "Velocidad (mm/h)"
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
        # tipo de gráfico
        if tipografico == "VI3D":
            titulo = "Velocidad Incremental 3D"
        elif tipografico == "VA3D":
            titulo = "Velocidad Acumulada 3D"
        elif tipografico == "VI2D":
            titulo = "Velocidad Incremental 2D"
        elif tipografico == "VA2D":
            titulo = "Velocidad Acumulada 2D"
        elif tipografico == "VISD":
            titulo = "Velocidad Incremental SD"
        elif tipografico == "VASD":
            titulo = "Velocidad Acumulada SD"
        widget_velocidad = VelocidadView.main.findChild(QWidget, "widget_grafica_velocidad")
        labeltendencia = VelocidadView.main.findChild(QLabel, "label_tendencia_velocidad")
        if len(datos) > 0:
            pluviometros, escala = None, None
            modulo = "VELOCIDAD"
            pluviometrosmarcados = VelocidadView.obtenerListaEquiposMarcados(lista, "Pluviómetros")
            if len(pluviometrosmarcados) == 1:
                datapluvio = PluviometroController.ctrlObtenerPluviometros(VelocidadView.idproyecto, pluviometrosmarcados, VelocidadView.fechainicial, VelocidadView.fechafinal)
                if datapluvio:
                    pluviometros = datapluvio
            # validar tipo de filtrado
            config = SoftwareConfiguracion.obtenerDataSoftware()
            filtrado = config[16]
            if filtrado == 0:
                procesar_grafica(widget_velocidad, labeltendencia, datos, 1, indextiempo, 5, labelx, labely, tipografico, unidadmedida, tipotiempo, titulo, VelocidadView.idproyecto, modulo, pluviometros, tendencias, escala, VelocidadView.fechainicial, VelocidadView.fechafinal)
            else:
                procesar_grafica(widget_velocidad, labeltendencia, datos, 1, indextiempo, 5, labelx, labely, tipografico, unidadmedida, tipotiempo, titulo, VelocidadView.idproyecto, modulo, pluviometros, tendencias, escala)
        else:
            VelocidadView.limpiarGraficaVelocidad()
    
    def limpiarGraficaVelocidad():
        widget_velocidad = VelocidadView.main.findChild(QWidget, "widget_grafica_velocidad")
        limpiar_widget(widget_velocidad)
    
    def mostrarModalLimpiezaRuido(treeWidget):
        lista = EquiposVelocidad.obtener_todos_elementos_marcados(treeWidget)
        if lista:
            prismasmarcados = VelocidadView.obtenerListaEquiposMarcados(lista, "Prismas")
            if len(prismasmarcados) > 0:
                estado, metodoLimpieza, prismasLimpieza = Personalizacion.dialogoLimpiezaRuidoPrismas(prismasmarcados)
                if estado:
                    tipo_grafico_desplazamiento = VelocidadView.main.findChild(QComboBox, "combo_tipos_velocidad")
                    tipografico = tipo_grafico_desplazamiento.currentData()
                    combotipomedida = VelocidadView.main.findChild(QComboBox, "combo_medida_velocidad")
                    tipomedida = combotipomedida.currentData()
                    
                    combo_promedios = VelocidadView.main.findChild(QComboBox, "combo_promedio_velocidad")
                    spin_promedio = VelocidadView.main.findChild(QSpinBox, "spin_promedio_velocidad")
                    tipopromedio = combo_promedios.currentData()
                    if tipopromedio == "SPRO":
                        spin_promedio.setEnabled(False)
                    else:
                        spin_promedio.setEnabled(True)
                    numeropromedio = spin_promedio.value()
                    
                    if tipomedida == "MD":
                        unidadmedida = 1
                    elif tipomedida == "CMD":
                        unidadmedida = 100
                    elif tipomedida == "MMD":
                        unidadmedida = 1000
                    elif tipomedida == "MH":
                        unidadmedida = 1/24
                    elif tipomedida == "CMH":
                        unidadmedida = 100/24
                    else:
                        unidadmedida = 1000/24
                    combotipofecha = VelocidadView.main.findChild(QComboBox, "combo_tiempo_velocidad")
                    tipotiempo = combotipofecha.currentData()
                    config = SoftwareConfiguracion.obtenerDataSoftware()
                    velocprisma, filtrado = config[15], config[16]
                    datos = VelocidadController.ctrlDatosPrismasMarcados(VelocidadView.idproyecto, prismasmarcados, VelocidadView.fechainicial, VelocidadView.fechafinal, tipografico, unidadmedida, velocprisma, filtrado, tipopromedio, numeropromedio)
                    if len(datos) > 0:
                        if metodoLimpieza == 'Limpieza Automática':
                            data = CalculosTendencias.limpiezaAutomaticaSaltos(datos, prismasLimpieza, 1, 5)
                        elif metodoLimpieza == 'Limpieza Manual':
                            data = CalculosTendencias.limpiezaManualSaltos(datos, prismasLimpieza, 1, 5)
                        elif metodoLimpieza == 'Ajustar Gráfico':
                            data = CalculosTendencias.ajustarCalculoSaltos(datos, prismasLimpieza, 1, 5)
                        # graficar
                        VelocidadView.graficarPrismasVelocidad(lista, data, tipografico, tipomedida, tipotiempo)
    
    def mostrarModalTendencia(treeWidget):
        lista = EquiposVelocidad.obtener_todos_elementos_marcados(treeWidget)
        if lista:
            prismasmarcados = VelocidadView.obtenerListaEquiposMarcados(lista, "Prismas")
            if len(prismasmarcados) > 0:
                regresion = Personalizacion.dialogoFiltroRegresionPrismas(prismasmarcados)
                if len(regresion) > 0:
                    tipo_grafico_desplazamiento = VelocidadView.main.findChild(QComboBox, "combo_tipos_velocidad")
                    tipografico = tipo_grafico_desplazamiento.currentData()
                    combotipomedida = VelocidadView.main.findChild(QComboBox, "combo_medida_velocidad")
                    tipomedida = combotipomedida.currentData()
                    combo_promedios = VelocidadView.main.findChild(QComboBox, "combo_promedio_velocidad")
                    spin_promedio = VelocidadView.main.findChild(QSpinBox, "spin_promedio_velocidad")
                    tipopromedio = combo_promedios.currentData()
                    if tipopromedio == "SPRO":
                        spin_promedio.setEnabled(False)
                    else:
                        spin_promedio.setEnabled(True)
                    numeropromedio = spin_promedio.value()
                    if tipomedida == "MD":
                        unidadmedida = 1
                    elif tipomedida == "CMD":
                        unidadmedida = 100
                    elif tipomedida == "MMD":
                        unidadmedida = 1000
                    elif tipomedida == "MH":
                        unidadmedida = 1/24
                    elif tipomedida == "CMH":
                        unidadmedida = 100/24
                    else:
                        unidadmedida = 1000/24
                    combotipofecha = VelocidadView.main.findChild(QComboBox, "combo_tiempo_velocidad")
                    tipotiempo = combotipofecha.currentData()
                    config = SoftwareConfiguracion.obtenerDataSoftware()
                    velocprisma, filtrado = config[15], config[16]
                    datos = VelocidadController.ctrlDatosPrismasMarcados(VelocidadView.idproyecto, prismasmarcados, VelocidadView.fechainicial, VelocidadView.fechafinal, tipografico, unidadmedida, velocprisma, filtrado, tipopromedio, numeropromedio)
                    if len(datos) > 0:
                        VelocidadView.graficarPrismasVelocidad(lista, datos, tipografico, tipomedida, tipotiempo, regresion)
    
    def mostrarModalConfiguracionEjes(treeWidget):
        lista = EquiposVelocidad.obtener_todos_elementos_marcados(treeWidget)
        if lista:
            prismasmarcados = VelocidadView.obtenerListaEquiposMarcados(lista, "Prismas")
            if len(prismasmarcados) > 0:
                combotipomedida = VelocidadView.main.findChild(QComboBox, "combo_medida_velocidad")
                tipomedida = combotipomedida.currentData()
                if tipomedida == "MD":
                    unidadmedida = 1
                elif tipomedida == "CMD":
                    unidadmedida = 100
                elif tipomedida == "MMD":
                    unidadmedida = 1000
                elif tipomedida == "MH":
                    unidadmedida = 1/24
                elif tipomedida == "CMH":
                    unidadmedida = 100/24
                else:
                    unidadmedida = 1000/24
                combotipofecha = VelocidadView.main.findChild(QComboBox, "combo_tiempo_velocidad")
                tipotiempo = combotipofecha.currentData()
                if tipotiempo == "HORA":
                    unidadtiempo  = 24
                else:
                    unidadtiempo  = 1
                tipo_grafico_desplazamiento = VelocidadView.main.findChild(QComboBox, "combo_tipos_velocidad")
                tipografico = tipo_grafico_desplazamiento.currentData()
                infoeje = ConfiguracionController.ctrlObtenerConfiguracionEje(VelocidadView.idproyecto, "VELOCIDAD", tipografico)
                if infoeje:
                    ejeymin, ejeymax, ejeyprim, ejeysecu, interdias = infoeje[4], infoeje[5], infoeje[6], infoeje[7], infoeje[8]
                else:
                    ejeymin, ejeymax, ejeyprim, ejeysecu, interdias = 0, 0, 0, 0, 0
                estadoeje, minejey, maxejey, primario, secundario, dias = Personalizacion.dialogoConfiguracionEjes(ejeymin, ejeymax, ejeyprim, ejeysecu, interdias, unidadmedida, unidadtiempo)
                if estadoeje:
                    # guardar configuracion
                    respuesta = ConfiguracionController.ctrlActualizarConfiguracionEjes(VelocidadView.idproyecto, "VELOCIDAD", tipografico, minejey, maxejey, primario, secundario, dias)
                    if respuesta:
                        combo_promedios = VelocidadView.main.findChild(QComboBox, "combo_promedio_velocidad")
                        spin_promedio = VelocidadView.main.findChild(QSpinBox, "spin_promedio_velocidad")
                        tipopromedio = combo_promedios.currentData()
                        if tipopromedio == "SPRO":
                            spin_promedio.setEnabled(False)
                        else:
                            spin_promedio.setEnabled(True)
                        numeropromedio = spin_promedio.value()
                        config = SoftwareConfiguracion.obtenerDataSoftware()
                        velocprisma, filtrado = config[15], config[16]
                        datos = VelocidadController.ctrlDatosPrismasMarcados(VelocidadView.idproyecto, prismasmarcados, VelocidadView.fechainicial, VelocidadView.fechafinal, tipografico, unidadmedida, velocprisma, filtrado, tipopromedio, numeropromedio)
                        if len(datos) > 0:
                            VelocidadView.graficarPrismasVelocidad(lista, datos, tipografico, tipomedida, tipotiempo)
    
    def mostrarTablaResumenVelocidad():
        if VelocidadView.idproyecto:
            ResumenPrismas.modalResumenTablaPrismas("VELOCIDAD", VelocidadView.idproyecto, VelocidadView.fechainicial, VelocidadView.fechafinal)
    
    def mostrarDialogoReporteVelocidad(treeWidget, widget_grafico, combo_tipo_grafico, tiporeporte):
        if VelocidadView.idproyecto:
            lista = EquiposVelocidad.obtener_todos_elementos_marcados(treeWidget)
            if lista:
                tipografico = combo_tipo_grafico.currentData()
                titulografica = f"Velocidad {tipografico}"
                tipoequipo = "Prisma"
                if tiporeporte == "General":
                    GraficaReporte.mostrarDialogoImagenVisor(widget_grafico, "Velocidad", tipografico, titulografica, VelocidadView.idproyecto, tipoequipo)
                else:
                    ReporteImage.modalImagenReporte(widget_grafico, "Velocidad", tipografico, titulografica, VelocidadView.idproyecto, tipoequipo)
    
    def actualizarVistaVelocidad(fechaini, fechafin, filtro=False):
        VelocidadView.fechainicial = fechaini
        VelocidadView.fechafinal = fechafin       
        if VelocidadView.idproyecto:
            treeWidget =  VelocidadView.main.findChild(QTreeWidget, "tree_actual_velocidad")
            VelocidadView.obtenerMostrarPrismasMarcados(treeWidget)
    
    def reiniciarVistaVelocidad(main, proyecto_id, proyecto_name):
        # reiniciar variables
        VelocidadView.main = main
        VelocidadView.idproyecto = proyecto_id
        VelocidadView.nameproyecto = proyecto_name
        VelocidadView.estadochecklist = True
        VelocidadView.limpiarGraficaVelocidad()
    
    def iniciarAsistenteVozVelocidad(treeWidget, botonvoz):
        lista = EquiposVelocidad.obtener_todos_elementos_marcados(treeWidget)
        if lista:
            prismasmarcados = VelocidadView.obtenerListaEquiposMarcados(lista, "Prismas")
            if len(prismasmarcados) > 0:
                tipo_grafico_desplazamiento = VelocidadView.main.findChild(QComboBox, "combo_tipos_velocidad")
                tipografico = tipo_grafico_desplazamiento.currentData()
                botonvoz.setEnabled(False)
                hilo_asistente = threading.Thread(target=AsistenteVoz.analizarVelocidad, args=(VelocidadView.idproyecto, prismasmarcados, VelocidadView.fechainicial, VelocidadView.fechafinal, tipografico, botonvoz))
                hilo_asistente.start()
                
    @staticmethod
    def ejecutar_exportacion_grafica():
        if VelocidadView.datos_memoria:
            MetodosGenerales.exportarDataInstrumentacion(
                VelocidadView.datos_memoria, 
                "Velocidad", 
                "EXPORT_VELOCIDAD"
            )
        else:
            from utils.common.alertas import mostrar_mensaje
            mostrar_mensaje("Exportar", "No hay datos en pantalla para exportar.", "advertencia")
    