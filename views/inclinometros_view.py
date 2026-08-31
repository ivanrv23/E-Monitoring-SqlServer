import threading
from PySide6.QtWidgets import (QWidget, QSpinBox, QComboBox, QTreeWidget, QPushButton,QDialog, QVBoxLayout, QDoubleSpinBox, QLineEdit)
from PySide6.QtCore import Qt, QTimer
from modules.inclinometros.grafico3d import plot_3d_in_widget
from modules.inclinometros.grafico2d import plot_2d_in_widget
from modules.inclinometros.grafico2d import limpiar_layout
from utils.common.alertas import mostrar_mensaje
from modules.inclinometros.analisisprofundidad import AnalisisProfundidad
from utils.shared.asistentedevoz import AsistenteVoz
from modules.datos.equiposInclinometros import EquiposInclinometros
from controllers.ConfiguracionController import ConfiguracionController
from utils.shared.personalizacion import Personalizacion
from utils.shared.guardarImagenReporte import ReporteImage
from utils.shared.graficareporte import GraficaReporte
from controllers.InclinometroController import InclinometroController
from controllers.EstratoController import EstratoController
from utils.shared.graficarEstratos import GraficarEstratos
from controllers.UmbralController import UmbralController
from utils.shared.graficarUmbrales import GraficarUmbrales
from controllers.InterfazController import InterfazController
from utils.generic.graficarumbralespersonalizados import graficarUmbralesPersonalizado

class InclinometrosView:
    main = None
    idproyecto = None
    nameproyecto = "SIN PROYECTO"
    estadochecklist = True
    estadoPagina = True
    timer_busqueda = None
    
    def inicializarVistaInclinometros(main, proyectoid, proyectoname):
        InclinometrosView.main = main
        InclinometrosView.idproyecto = proyectoid
        InclinometrosView.nameproyecto = proyectoname
        if InclinometrosView.estadochecklist:
            tree_widget = main.findChild(QTreeWidget, "tree_actual_inclinometros")
            tree_widget.setHeaderLabels([InclinometrosView.nameproyecto.upper()])
            EquiposInclinometros.inicializar_lista_equipos(tree_widget, InclinometrosView.idproyecto, InclinometrosView.nameproyecto)
            InclinometrosView.estadochecklist = False
        if InclinometrosView.estadoPagina:
            tree_actual_inclinometros =  main.findChild(QTreeWidget, "tree_actual_inclinometros")
            tree_actual_inclinometros.itemClicked.connect(InclinometrosView.checkProyectoActualInclinometros)
            # --- Buscador de equipos en el árbol ---
            buscador_arbol = InclinometrosView.main.findChild(QLineEdit, "input_buscar_inclinometros")
            if buscador_arbol is None:
                buscador_arbol = QLineEdit()
                buscador_arbol.setObjectName("input_buscar_inclinometros")
                buscador_arbol.setPlaceholderText("Buscar equipo...")
                layout_padre = tree_actual_inclinometros.parentWidget().layout()
                if layout_padre is not None:
                    indice_tree = layout_padre.indexOf(tree_actual_inclinometros)
                    layout_padre.insertWidget(indice_tree, buscador_arbol)

                InclinometrosView.timer_busqueda = QTimer()
                InclinometrosView.timer_busqueda.setSingleShot(True)
                InclinometrosView.timer_busqueda.timeout.connect(
                    lambda: EquiposInclinometros.filtrarArbolPorTexto(tree_actual_inclinometros, buscador_arbol.text())
                )
                buscador_arbol.textChanged.connect(
                    lambda: (InclinometrosView.timer_busqueda.stop(),
                              InclinometrosView.timer_busqueda.start(250))
                )
            
            tree_actual_inclinometros.setContextMenuPolicy(Qt.CustomContextMenu)
            tree_actual_inclinometros.customContextMenuRequested.connect(InclinometrosView.clicderechoProyectoActualInclinometros)
            botonRefrescarInclinometros = main.findChild(QPushButton, "btn_refrescar_vista_inclinometros")
            botonRefrescarInclinometros.clicked.connect(lambda: InclinometrosView.obtenerMostrarInclinometrosMarcados(tree_actual_inclinometros))
            # Cargar Unidades de Medida
            lista_unidades_medida = [
                ('Metros', 1),
                ('Centímetros', 100),
                ('Milímetros', 1000)
            ]
            combo_medidas = main.findChild(QComboBox, "combo_medida_inclinometros")
            for value, key in lista_unidades_medida:
                combo_medidas.addItem(value, key)
            combo_medidas.activated.connect(lambda: InclinometrosView.obtenerMostrarInclinometrosMarcados(tree_actual_inclinometros))
            # Definimos el diccionario de tipos de desplazamiento
            lista_graficos_inclinometros = {
                'AI3D': 'Desplaz. Acumulado e Incremental',
                'DAAB': 'Desplaz. Acumulado AB',
                'DIAB': 'Desplaz. Incremental AB',
                'DANE': 'Desplaz. Acumulado NE',
                'DINE': 'Desplaz. Incremental NE',
                'PAAB': 'Posición Absoluta AB',
                'PANE': 'Posición Absoluta NE',
                'CSAB': 'Checksum AB',
            }
            # Localizamos el QComboBox en la interfaz
            combo_tipo_grafico = main.findChild(QComboBox, "combo_tipografico_inclinometros")
            for key, value in lista_graficos_inclinometros.items():
                combo_tipo_grafico.addItem(value, key)
            combo_tipo_grafico.activated.connect(lambda: InclinometrosView.obtenerMostrarInclinometrosMarcados(tree_actual_inclinometros))
            # Botones
            btnAsistenteVoz = main.findChild(QPushButton, "btn_voz_inclinometros")
            btnAsistenteVoz.clicked.connect(lambda: InclinometrosView.iniciarAsistenteVozInclinometros(tree_actual_inclinometros, btnAsistenteVoz))
            btnProfundidad = main.findChild(QPushButton, "btn_analisis_profundidad")
            btnProfundidad.clicked.connect(lambda: InclinometrosView.mostrarAnalisisProfundidad(tree_actual_inclinometros))
            btnEjesInclino = InclinometrosView.main.findChild(QPushButton, "btn_ejes_inclinometros")
            btnEjesInclino.clicked.connect(lambda: InclinometrosView.mostrarModalConfiguracionEjes(tree_actual_inclinometros))
            btn_mostrar_estratos = InclinometrosView.main.findChild(QPushButton, "btn_estratos_inclinometro")
            btn_mostrar_estratos.clicked.connect(InclinometrosView.graficarEstratosInclinometros)
            btn_mostrar_umbrales = InclinometrosView.main.findChild(QPushButton, "btn_umbrales_inclinometro")
            btn_mostrar_umbrales.clicked.connect(InclinometrosView.graficarUmbralesInclinometros)
            btn_guardar_grafico_reporte = main.findChild(QPushButton, "btn_reporte_inclinometros")
            btn_guardar_grafico_reporte.clicked.connect(lambda: InclinometrosView.guardarGraficoReporte(tree_actual_inclinometros, "Anexos"))
            btnReporteGeneral = main.findChild(QPushButton, "btn_imagen_inclinometros")
            btnReporteGeneral.clicked.connect(lambda: InclinometrosView.guardarGraficoReporte(tree_actual_inclinometros, "General"))
            btnAplicarUmbralPersonalizado = main.findChild(QPushButton, "btn_umbral_personalizado_I")
            btnAplicarUmbralPersonalizado.clicked.connect(InclinometrosView.graficarUmbralesPersonalizado)
 
            InclinometrosView.estadoPagina = False
        
    def graficarUmbralesPersonalizado():
        if InclinometrosView.idproyecto:
            combo_tipo_grafico = InclinometrosView.main.findChild(QComboBox, "combo_tipografico_inclinometros")
            if combo_tipo_grafico.currentData()!='AI3D':                
                combo_medidas = InclinometrosView.main.findChild(QComboBox, "combo_medida_inclinometros")
                unidad = combo_medidas.currentData()
                widget_grafico = InclinometrosView.main.findChild(QWidget, "widget_grafica_inclinoizquierda")
                widget_grafico2 = InclinometrosView.main.findChild(QWidget, "widget_grafica_inclinoderecha")
                widgets = [widget_grafico, widget_grafico2]
                graficarUmbralesPersonalizado(widgets,unidad,InclinometrosView.idproyecto, 'x', 'linea')
            
    def graficarEstratosInclinometros():
        combo_tipo_grafico = InclinometrosView.main.findChild(QComboBox, "combo_tipografico_inclinometros")
        if combo_tipo_grafico.currentData() != 'AI3D':
            widget_grafico = InclinometrosView.main.findChild(QWidget, "widget_grafica_inclinoizquierda")
            widget_grafico2 = InclinometrosView.main.findChild(QWidget, "widget_grafica_inclinoderecha")
            estratos = EstratoController.ctrObtenerEstratosProyecto(InclinometrosView.idproyecto)
            if estratos:
                widgets = [widget_grafico,widget_grafico2]
                GraficarEstratos.draw_colored_estratos(widgets, estratos, 1)

    def graficarUmbralesInclinometros():
        combo_tipo_grafico = InclinometrosView.main.findChild(QComboBox, "combo_tipografico_inclinometros")
        if combo_tipo_grafico.currentData()!='AI3D':        
            widget_grafico = InclinometrosView.main.findChild(QWidget, "widget_grafica_inclinoizquierda")
            widget_grafico2 = InclinometrosView.main.findChild(QWidget, "widget_grafica_inclinoderecha")
            widgets = [widget_grafico, widget_grafico2]
            pintado = GraficarUmbrales.clean_on_widget(widgets, 'linea')
            if pintado is False:
                treeWidget =  InclinometrosView.main.findChild(QTreeWidget, "tree_actual_inclinometros")
                lista = EquiposInclinometros.obtener_todos_elementos_marcados(treeWidget)
                inclinometromarcados = InclinometrosView.obtenerListaEquiposMarcados(lista, "Inclinómetros")
                id_intrumentacion = inclinometromarcados[0][1][0][1]
                id_inclinometro = InclinometroController.ctrlObtenerIdIinclinometro(id_intrumentacion)
                umbrales = UmbralController.ctrlObtenerUmbralesInstrumentacion(InclinometrosView.idproyecto, id_inclinometro, 'UDI', 'umbral_inclinometro')
                if umbrales:
                    umbrales_inclinometro = [tupla for tupla in umbrales if tupla[2] == id_inclinometro]
                    combo_medidas = InclinometrosView.main.findChild(QComboBox, "combo_medida_inclinometros")
                    unidad = combo_medidas.currentData()
                    GraficarUmbrales.draw_on_widget(widgets, umbrales_inclinometro, unidad, 'x', 'linea')
    
    def guardarGraficoReporte(tree_actual, tiporeporte):
        if InclinometrosView.idproyecto:
            lista = EquiposInclinometros.obtener_todos_elementos_marcados(tree_actual)
            if lista:
                combo_tipo_grafico = InclinometrosView.main.findChild(QWidget, "combo_tipografico_inclinometros")
                tipo_grafico = combo_tipo_grafico.currentData()
                tipoequipo = "Inclinometro"
                if tipo_grafico == 'AI3D':
                    opcion1 = 'Desplazamiento Acumulado 3D'
                    opcion2 = 'Desplazamiento Incremental 3D'
                    tipografico1 = "DA3D"
                    tipografico2 = "DI3D"
                elif tipo_grafico == 'DIAB':
                    opcion1 = 'Desplazamiento Incremental A'
                    opcion2 = 'Desplazamiento Incremental B'
                    tipografico1 = "DIA"
                    tipografico2 = "DIB"
                elif tipo_grafico == 'DINE':
                    opcion1 = 'Desplazamiento Incremental N'
                    opcion2 = 'Desplazamiento Incremental E'
                    tipografico1 = "DIN"
                    tipografico2 = "DIE"
                elif tipo_grafico == 'DAAB':
                    opcion1 = 'Desplazamiento Acumulado A'
                    opcion2 = 'Desplazamiento Acumulado B'
                    tipografico1 = "DAA"
                    tipografico2 = "DAB"
                elif tipo_grafico == 'DANE':
                    opcion1 = 'Desplazamiento Acumulado N'
                    opcion2 = 'Desplazamiento Acumulado E'
                    tipografico1 = "DAN"
                    tipografico2 = "DAE"
                elif tipo_grafico == 'PAAB':
                    opcion1 = 'Posición Absoluta A'
                    opcion2 = 'Posición Absoluta B'
                    tipografico1 = "PAA"
                    tipografico2 = "PAB"
                elif tipo_grafico == 'PANE':
                    opcion1 = 'Posición Absoluta N'
                    opcion2 = 'Posición Absoluta E'
                    tipografico1 = "PAN"
                    tipografico2 = "PAB"
                elif tipo_grafico == 'CSAB':
                    opcion1 = 'Checksum A'
                    opcion2 = 'Checksum B'
                    tipografico1 = "CSA"
                    tipografico2 = "CSB"
                # Crear el diálogo de selección
                dialog = QDialog(InclinometrosView.main)
                dialog.setWindowTitle("Seleccionar Gráfica")
                layout = QVBoxLayout(dialog)
                button1 = QPushButton(opcion1)
                button2 = QPushButton(opcion2)
                layout.addWidget(button1)
                layout.addWidget(button2)
                def on_button1_clicked():
                    dialog.accept()
                    widget_grafico = InclinometrosView.main.findChild(QWidget, "widget_grafica_inclinoizquierda")
                    if tiporeporte == "General":
                        GraficaReporte.mostrarDialogoImagenVisor(widget_grafico, "Inclinometros", tipografico1, opcion1, InclinometrosView.idproyecto, tipoequipo)
                    else:
                        ReporteImage.modalImagenReporte(widget_grafico, "Inclinometros", tipografico1, opcion1, InclinometrosView.idproyecto, tipoequipo)
                def on_button2_clicked():
                    dialog.accept()
                    widget_grafico = InclinometrosView.main.findChild(QWidget, "widget_grafica_inclinoderecha")
                    if tiporeporte == "General":
                        GraficaReporte.mostrarDialogoImagenVisor(widget_grafico, "Inclinometros", tipografico2, opcion2, InclinometrosView.idproyecto, tipoequipo)
                    else:
                        ReporteImage.modalImagenReporte(widget_grafico, "Inclinometros", tipografico2, opcion2, InclinometrosView.idproyecto, tipoequipo)
                button1.clicked.connect(on_button1_clicked)
                button2.clicked.connect(on_button2_clicked)
                if dialog.exec() == QDialog.Rejected:
                    return
    
    def checkProyectoActualInclinometros(parent_item, column):
        treeWidget =  InclinometrosView.main.findChild(QTreeWidget, "tree_actual_inclinometros")
        EquiposInclinometros.validarMarcadoCheckbox(parent_item, column, treeWidget, lambda: InclinometrosView.obtenerMostrarInclinometrosMarcados(treeWidget))
        
    def clicderechoProyectoActualInclinometros(point):
        treeWidget =  InclinometrosView.main.findChild(QTreeWidget, "tree_actual_inclinometros")
        EquiposInclinometros.validarOpcionesMenuCheckbox(point, treeWidget, lambda: InclinometrosView.obtenerMostrarInclinometrosMarcados(treeWidget), InclinometrosView.reiniciarVistasAfectadas)
    
    def reiniciarVistasAfectadas(tipoequipo="Todos"):
        from views.datos_view import DatosView
        from views.visor_view import VisorView
        from views.desplazamiento_view import DesplazamientoView
        from views.velocidad_view import VelocidadView
        from views.piezometros_view import PiezometrosView
        from views.celdas_view import CeldasView
        from views.acelerografos_view import AcelerografosView
        from views.sondajestdr_view import SondajetdrView
        from views.analisis_view import AnalisisView
        if tipoequipo == "Inclinómetro":
            DatosView.reiniciarVistaDatos(InclinometrosView.main, InclinometrosView.idproyecto, InclinometrosView.nameproyecto)
            VisorView.reiniciarVistaVisor(InclinometrosView.main, InclinometrosView.idproyecto, InclinometrosView.nameproyecto)
        else:
            DatosView.reiniciarVistaDatos(InclinometrosView.main, InclinometrosView.idproyecto, InclinometrosView.nameproyecto)
            VisorView.reiniciarVistaVisor(InclinometrosView.main, InclinometrosView.idproyecto, InclinometrosView.nameproyecto)
            DesplazamientoView.reiniciarVistaDesplazamiento(InclinometrosView.main, InclinometrosView.idproyecto, InclinometrosView.nameproyecto)
            VelocidadView.reiniciarVistaVelocidad(InclinometrosView.main, InclinometrosView.idproyecto, InclinometrosView.nameproyecto)
            PiezometrosView.reiniciarVistaPiezometros(InclinometrosView.main, InclinometrosView.idproyecto, InclinometrosView.nameproyecto)
            CeldasView.reiniciarVistaCeldas(InclinometrosView.main, InclinometrosView.idproyecto, InclinometrosView.nameproyecto)
            AcelerografosView.reiniciarVistaAcelerografos(InclinometrosView.main, InclinometrosView.idproyecto, InclinometrosView.nameproyecto)
            SondajetdrView.reiniciarVistaTDR(InclinometrosView.main, InclinometrosView.idproyecto, InclinometrosView.nameproyecto)
            AnalisisView.reiniciarVistaAnalisis(InclinometrosView.main, InclinometrosView.idproyecto, InclinometrosView.nameproyecto)
    
    def obtenerMostrarInclinometrosMarcados(tree_actual):
        lista = EquiposInclinometros.obtener_todos_elementos_marcados(tree_actual)
        if lista:
            inclinometromarcados = InclinometrosView.obtenerListaEquiposMarcados(lista, "Inclinómetros")
            if len(inclinometromarcados) == 1:
                InclinometrosView.graficarMovimientoInclinometros(inclinometromarcados)
            else:
                InclinometrosView.limpiarGraficaInclinometros()
        else:
            InclinometrosView.limpiarGraficaInclinometros()
    
    def obtenerListaEquiposMarcados(lista, tipolista):
        equiposmarcados = []
        for region, instrumentos in lista.items():
            for tipo, lista_equipos in instrumentos.items():
                if tipo[0] == tipolista:
                    equiposmarcados.append((region, lista_equipos))
        return equiposmarcados
            
    def graficarMovimientoInclinometros(inclinometromarcados):
        comboTipoGrafico = InclinometrosView.main.findChild(QComboBox, "combo_tipografico_inclinometros")
        grafico = comboTipoGrafico.currentData()
        widget_inclinoizquierda = InclinometrosView.main.findChild(QWidget, "widget_grafica_inclinoizquierda")
        widget_inclinoderecha = InclinometrosView.main.findChild(QWidget, "widget_grafica_inclinoderecha")
        spinazimuth = InclinometrosView.main.findChild(QSpinBox, "spin_azimut_inclinometros")
        azimuth = spinazimuth.value()
        spincorrezz = InclinometrosView.main.findChild(QSpinBox, "spin_correccion_inclinometros")
        anguzz = spincorrezz.value()
        spinrint = InclinometrosView.main.findChild(QDoubleSpinBox, "spin_rint_inclinometros")
        rint = spinrint.value()
        combo_medidas = InclinometrosView.main.findChild(QComboBox, "combo_medida_inclinometros")
        unidadmedida = combo_medidas.currentData()
        if unidadmedida == 1:
            unimed = "m"
        elif unidadmedida == 100:
            unimed = "cm"
        else:
            unimed = "mm"
        nombreinclinometro, totallecturas = "", 0
        for componente, listainclinometros in inclinometromarcados:
            nombrecomponente, idcomponente, idproy = componente
            for nombreincli, idinstru, fechas in listainclinometros:
                nombreinclinometro = nombreincli
                fechas = InterfazController.ctrlListarFechasInclinometro(idcomponente, idinstru, idproy)
                if fechas:
                    totallecturas = len(fechas)
        if grafico == 'AI3D':
            spin_rotacion = InclinometrosView.main.findChild(QSpinBox, "spin_rotacion_inclinometros")
            datosacum = InclinometroController.ctrlObtenerDAAB(InclinometrosView.idproyecto, inclinometromarcados, unidadmedida, azimuth, anguzz, rint)
            if datosacum:
                titulo = f"Desplazamiento Acumulado 3D - {nombreinclinometro}"
                nombreejex = f"D. Acum. A ({unimed})"
                nombreejey = f"D. Acum. B ({unimed})"
                plot_3d_in_widget(InclinometrosView.idproyecto, datosacum, titulo, nombreejex, nombreejey, widget_inclinoizquierda, spin_rotacion, unidadmedida, grafico, totallecturas)
            else:
                InclinometrosView.limpiarGraficaInclinometros()
                mostrar_mensaje("Sin Datos", "No hay datos o no tiene fecha base.", "advertencia")
            datosincr = InclinometroController.ctrlObtenerDIAB(InclinometrosView.idproyecto, inclinometromarcados, unidadmedida, azimuth, anguzz, rint)
            if datosincr:
                titulo = f"Desplazamiento Incremental 3D - {nombreinclinometro}"
                nombreejex = f"D. Increm. A ({unimed})"
                nombreejey = f"D. Increm. B ({unimed})"
                plot_3d_in_widget(InclinometrosView.idproyecto, datosincr, titulo, nombreejex, nombreejey, widget_inclinoderecha, spin_rotacion, unidadmedida, grafico, totallecturas)
            else:
                InclinometrosView.limpiarGraficaInclinometros()
        else:
            if grafico == 'DIAB':
                titulo1 = f'Desplazamiento Incremental A - {nombreinclinometro}'
                titulo2 = f'Desplazamiento Incremental B - {nombreinclinometro}'
                nombreeje1 = f"D. Increm. A ({unimed})"
                nombreeje2 = f"D. Increm. B ({unimed})"
            elif grafico=='DINE':
                titulo1 = f'Desplazamiento Incremental E - {nombreinclinometro}'
                titulo2 = f'Desplazamiento Incremental N - {nombreinclinometro}'
                nombreeje1 = f"D. Increm. E ({unimed})"
                nombreeje2 = f"D. Increm. N ({unimed})"
            elif grafico=='DAAB':
                titulo1 = f'Desplazamiento Acumulado A - {nombreinclinometro}'
                titulo2 = f'Desplazamiento Acumulado B - {nombreinclinometro}'
                nombreeje1 = f"D. Acum. A ({unimed})"
                nombreeje2 = f"D. Acum. B ({unimed})"
            elif grafico=='DANE':
                titulo1 = f'Desplazamiento Acumulado E - {nombreinclinometro}'
                titulo2 = f'Desplazamiento Acumulado N - {nombreinclinometro}'
                nombreeje1 = f"D. Acum. E ({unimed})"
                nombreeje2 = f"D. Acum. N ({unimed})"
            elif grafico=='PAAB':
                titulo1 = f'Posición Absoluta A - {nombreinclinometro}'
                titulo2 = f'Posición Absoluta B - {nombreinclinometro}'
                nombreeje1 = f"Pos. Absoluta A ({unimed})"
                nombreeje2 = f"Pos. Absoluta B ({unimed})"
            elif grafico=='PANE':
                titulo1 = f'Posición Absoluta E - {nombreinclinometro}'
                titulo2 = f'Posición Absoluta N - {nombreinclinometro}'
                nombreeje1 = f"Pos. Absoluta E ({unimed})"
                nombreeje2 = f"Pos. Absoluta N ({unimed})"
            elif grafico=='CSAB':
                titulo1 = f'Checksum A - {nombreinclinometro}'
                titulo2 = f'Checksum B - {nombreinclinometro}'
                nombreeje1 = f"A ({unimed})"
                nombreeje2 = f"B ({unimed})"
            method_name = 'ctrlObtener' + grafico
            datos = getattr(InclinometroController, method_name)(InclinometrosView.idproyecto, inclinometromarcados, unidadmedida, azimuth, anguzz, rint)
            if datos:
                plot_2d_in_widget(InclinometrosView.idproyecto, widget_inclinoizquierda, widget_inclinoderecha, datos, titulo1, titulo2, nombreeje1, nombreeje2, unidadmedida, grafico, totallecturas)
            else:
                InclinometrosView.limpiarGraficaInclinometros()
                mostrar_mensaje("Sin Datos", "No hay datos o no tiene fecha base.", "advertencia")
    
    def limpiarGraficaInclinometros():
        widget_inclinoizquierda = InclinometrosView.main.findChild(QWidget, "widget_grafica_inclinoizquierda")
        widget_inclinoderecha = InclinometrosView.main.findChild(QWidget, "widget_grafica_inclinoderecha") 
        limpiar_layout(widget_inclinoizquierda)
        limpiar_layout(widget_inclinoderecha)
        
    def mostrarAnalisisProfundidad(treeWidget):
        lista = EquiposInclinometros.obtener_todos_elementos_marcados(treeWidget)
        if lista:
            inclinomarcados = InclinometrosView.obtenerListaEquiposMarcados(lista, "Inclinómetros")
            if len(inclinomarcados) > 0:
                spinazimuth = InclinometrosView.main.findChild(QSpinBox, "spin_azimut_inclinometros")
                azimuth = spinazimuth.value()
                spincorrezz = InclinometrosView.main.findChild(QSpinBox, "spin_correccion_inclinometros")
                anguzz = spincorrezz.value()
                spinrint = InclinometrosView.main.findChild(QDoubleSpinBox, "spin_rint_inclinometros")
                rint = spinrint.value()
                AnalisisProfundidad.mostrarDialogoProfundidad(InclinometrosView.idproyecto, inclinomarcados, azimuth, anguzz, rint)
            else:
                mostrar_mensaje("Sin Inclinómetros", "Debe seleccionar un inclinómetro", "advertencia")
        else:
            mostrar_mensaje("Sin Inclinómetros", "Debe seleccionar un inclinómetro", "advertencia")
    
    def mostrarModalConfiguracionEjes(treeWidget):
        lista = EquiposInclinometros.obtener_todos_elementos_marcados(treeWidget)
        if lista:
            inclinometromarcados = InclinometrosView.obtenerListaEquiposMarcados(lista, "Inclinómetros")
            if len(inclinometromarcados) == 1:
                combotipomedida = InclinometrosView.main.findChild(QComboBox, "combo_medida_inclinometros")
                unidadmedida = combotipomedida.currentData()
                combo_tipo_grafico = InclinometrosView.main.findChild(QWidget, "combo_tipografico_inclinometros")
                tipografico = combo_tipo_grafico.currentData()
                infoeje = ConfiguracionController.ctrlObtenerConfiguracionEje(InclinometrosView.idproyecto, "INCLINOMETROS", tipografico)
                if infoeje:
                    ejexmin, ejexmax, ejexprim, ejexsecu, interprofu = infoeje[4], infoeje[5], infoeje[6], infoeje[7], infoeje[8]
                else:
                    ejexmin, ejexmax, ejexprim, ejexsecu, interprofu = 0, 0, 0, 0, 0
                estadoeje, minejex, maxejex, xprimario, xsecundario, yprofundo = Personalizacion.dialogoConfiguracionEjesInclinometro(ejexmin, ejexmax, ejexprim, ejexsecu, interprofu, unidadmedida)
                if estadoeje:
                    # guardar configuracion
                    respuesta = ConfiguracionController.ctrlActualizarConfiguracionEjes(InclinometrosView.idproyecto, "INCLINOMETROS", tipografico, minejex, maxejex, xprimario, xsecundario, yprofundo)
                    if respuesta:
                        treeWidget = InclinometrosView.main.findChild(QTreeWidget, "tree_actual_inclinometros")
                        InclinometrosView.obtenerMostrarInclinometrosMarcados(treeWidget)
    
    def reiniciarVistaInclinometros(main, proyecto_id, proyecto_name):
        # reiniciar variables
        InclinometrosView.main = main
        InclinometrosView.idproyecto = proyecto_id
        InclinometrosView.nameproyecto = proyecto_name
        InclinometrosView.estadochecklist = True
        InclinometrosView.limpiarGraficaInclinometros()
        # LIMPIAR EL BUSCADOR AL CAMBIAR DE PROYECTO
        buscador_arbol = main.findChild(QLineEdit, "input_buscar_inclinometros")
        if buscador_arbol is not None:
            buscador_arbol.blockSignals(True)
            buscador_arbol.clear()
            buscador_arbol.blockSignals(False)
    
    def iniciarAsistenteVozInclinometros(treeWidget, botonvoz):
        lista = EquiposInclinometros.obtener_todos_elementos_marcados(treeWidget)
        if lista:
            inclinometrosmarcados = InclinometrosView.obtenerListaEquiposMarcados(lista, "Inclinómetros")
            if len(inclinometrosmarcados) > 0:
                combo_tipo_grafico = InclinometrosView.main.findChild(QWidget, "combo_tipografico_inclinometros")
                tipografico = combo_tipo_grafico.currentData()
                botonvoz.setEnabled(False)
                hilo_asistente = threading.Thread(target=AsistenteVoz.analizarInclinometros, args=(InclinometrosView.idproyecto, inclinometrosmarcados, tipografico, botonvoz))
                hilo_asistente.start()
    