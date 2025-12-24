import pandas as pd
import numpy as np
import ast
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.dates as mdates
from datetime import datetime, date
import datetime as dt_module
from matplotlib.dates import DateFormatter
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFileDialog, QLabel, QPushButton, QComboBox, QSpinBox, QWidget, QDoubleSpinBox)
from utils.common.rutasarchivos import resource_path
from utils.generic.cargariconos import cargarIcono
from utils.common.alertas import mostrar_mensaje
from utils.generic.listaiconos import ListaIconos
from PySide6.QtUiTools import QUiLoader
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from utils.shared.guardarImagenReporte import ReporteImage
from utils.shared.graficareporte import GraficaReporte
from openpyxl import Workbook
from modules.empresa.softwareconfiguracion import SoftwareConfiguracion
from controllers.InclinometroController import InclinometroController
from controllers.UmbralController import UmbralController
from utils.shared.graficarUmbrales import GraficarUmbrales

class AnalisisProfundidad:
    datos = None
    
    def mostrarDialogoProfundidad(idproyecto, inclifechasmarcados, azimuth, zz, rint):
        loader = QUiLoader()        
        ui_file_path = resource_path("ui/inclinoprofundidad.ui")
        ui_file = loader.load(ui_file_path, None)
        dialogo = QDialog()
        dialogo.setWindowTitle("Análisis de Profundidad")
        layout = QVBoxLayout()
        layout.addWidget(ui_file)
        dialogo.setLayout(layout)
        # inicializar herramientas
        labelTitulo = dialogo.findChild(QLabel, "label_titulo")
        comboTipografica = dialogo.findChild(QComboBox, "combo_tipo_grafica") 
        botonReporte = dialogo.findChild(QPushButton, "btn_reporte_imagen") 
        cargarIcono(botonReporte, ListaIconos.ICONOS["add_imagen_reporte"])
        botonReporteGeneral = dialogo.findChild(QPushButton, "btn_imagen_general") 
        cargarIcono(botonReporteGeneral, ListaIconos.ICONOS["imagenes"])
        botonUmbral = dialogo.findChild(QPushButton, "btn_umbral") 
        cargarIcono(botonUmbral, ListaIconos.ICONOS["umbral"])
        spinProfundo = dialogo.findChild(QDoubleSpinBox, "spin_profundidad")
        botonGraficar = dialogo.findChild(QPushButton, "btn_graficar") 
        cargarIcono(botonGraficar, ListaIconos.ICONOS["dibujar"])
        comboUnidad = dialogo.findChild(QComboBox, "combo_unidades")
        comboTiempo = dialogo.findChild(QComboBox, "combo_tiempo")
        comboTendencia = dialogo.findChild(QComboBox, "combo_tendencias")
        spinGrado = dialogo.findChild(QSpinBox, "spin_grado")
        botonExportar = dialogo.findChild(QPushButton, "btn_exportar") 
        cargarIcono(botonExportar, ListaIconos.ICONOS["exportar_dxf"])
        labelEcuacion = dialogo.findChild(QLabel, "label_ecuacion")
        widgetGrafica = dialogo.findChild(QWidget, "widget_desplazamiento")
        # Cargar combos
        lista_graficos_inclinometros = {
            'DAA': 'Desplazamiento Acumulado A',
            'DAB': 'Desplazamiento Acumulado B',
            'DIA': 'Desplazamiento Incremental A',
            'DIB': 'Desplazamiento Incremental B',
            'DAN': 'Desplazamiento Acumulado N',
            'DAE': 'Desplazamiento Acumulado E',
            'DIN': 'Desplazamiento Incremental N',
            'DIE': 'Desplazamiento Incremental E',
            'PAA': 'Posoción absoluta A',
            'PAB': 'Posoción absoluta B',
            'PAN': 'Posoción absoluta N',
            'PAE': 'Posoción absoluta E',
        }
        for key, value in lista_graficos_inclinometros.items():
            comboTipografica.addItem(value, key)
        comboUnidad.addItem("Metros", 1)
        comboUnidad.addItem("Centímetros", 100)
        comboUnidad.addItem("Milímetros", 1000)
        comboTiempo.addItem("Por Fechas", "FECHA")
        comboTiempo.addItem("Por Días", "DIA")
        comboTendencia.addItem("Sin Tendencia", "ST")
        comboTendencia.addItem("Tendencia Lineal", "TL")
        comboTendencia.addItem("Tendencia Polinómica", "TP")
        # validacion de tipo geocon o rst
        AnalisisProfundidad.datos, titulo, tipoincli, nombreequipo = None, "", "RST", ""
        for componente, listainclinometros in inclifechasmarcados:
            nombrecomponente, idcomponente, idproy = componente
            for nombreincli, idinstru, fechas in listainclinometros:
                nombreequipo = nombreincli
                tipoequipo = InclinometroController.ctrlObtenerInclinometroTipo(idproyecto, idcomponente, idinstru)
                if tipoequipo:
                    if tipoequipo[0] == "RST":
                        tipoincli = "RST"
                        titulo = f"Análisis de Profundidad Inclinómetro RST - {nombreincli}"
                    else:
                        tipoincli = "GEOKON"
                        titulo = f"Análisis de Profundidad Inclinómetro GEOKON - {nombreincli}"
        labelTitulo.setText(titulo)
        def obtenerDataGraficar():
            profundidad = spinProfundo.value()
            graficatipo = comboTipografica.currentData()
            tipotiempo = comboTiempo.currentData()
            tendencia = comboTendencia.currentData()
            grado = spinGrado.value()
            m = 0.05
            if rint > 0:
                mrint = m * rint
            else:
                mrint = m * 0.5
            if profundidad != 0:
                for componente, listainclinometros in inclifechasmarcados:
                    nombrecomponente, idcomponente, idproy = componente
                    for nombreincli, idinstru, fechas in listainclinometros:
                        tabla = f"inclinometro_detalle{idproyecto}"
                        # fechitas = ast.literal_eval(fechas)
                        contexto_seguro = {'datetime': dt_module}
                        # Usamos eval porque ast.literal_eval no soporta objetos datetime
                        fechitas = eval(fechas, {"__builtins__": None}, contexto_seguro)
                        if tipoincli == "RST":
                            if graficatipo == 'DIA':
                                posicion = "CampoA"
                                AnalisisProfundidad.datos = InclinometroController.ctrlObtenerDIABprofundidad(tabla, idcomponente, idinstru, fechitas, 1, zz, mrint, "RST")
                            elif graficatipo == 'DIB':
                                posicion = "CampoB"
                                AnalisisProfundidad.datos = InclinometroController.ctrlObtenerDIABprofundidad(tabla, idcomponente, idinstru, fechitas, 1, zz, mrint, "RST")
                            elif graficatipo == 'DIN':
                                posicion = "CampoB"
                                AnalisisProfundidad.datos = InclinometroController.ctrlObtenerDINEprofundidad(tabla, idcomponente, idinstru, fechitas, 1, azimuth, mrint, "RST")
                            elif graficatipo == 'DIE':
                                posicion = "CampoA"
                                AnalisisProfundidad.datos = InclinometroController.ctrlObtenerDINEprofundidad(tabla, idcomponente, idinstru, fechitas, 1, azimuth, mrint, "RST")
                            elif graficatipo == 'DAA':
                                posicion = "CampoA"
                                AnalisisProfundidad.datos = InclinometroController.ctrlObtenerDAABprofundidad(tabla, idcomponente, idinstru, fechitas, 1, "RST")
                            elif graficatipo == 'DAB':
                                posicion = "CampoB"
                                AnalisisProfundidad.datos = InclinometroController.ctrlObtenerDAABprofundidad(tabla, idcomponente, idinstru, fechitas, 1, "RST")
                            elif graficatipo == 'DAN':
                                posicion = "CampoB"
                                AnalisisProfundidad.datos = InclinometroController.ctrlObtenerDANEprofundidad(tabla, idcomponente, idinstru, fechitas, 1, azimuth, mrint, zz, "RST")
                            elif graficatipo == 'DAE':
                                posicion = "CampoA"
                                AnalisisProfundidad.datos = InclinometroController.ctrlObtenerDANEprofundidad(tabla, idcomponente, idinstru, fechitas, 1, azimuth, mrint, zz, "RST")
                            elif graficatipo == 'PAA':
                                posicion = "CampoA"
                                AnalisisProfundidad.datos = InclinometroController.ctrlObtenerPAABprofundidad(tabla, idcomponente, idinstru, fechitas, 1, mrint, "RST")
                            elif graficatipo == 'PAB':
                                posicion = "CampoB"
                                AnalisisProfundidad.datos = InclinometroController.ctrlObtenerPAABprofundidad(tabla, idcomponente, idinstru, fechitas, 1, mrint, "RST")
                            elif graficatipo == 'PAN':
                                posicion = "CampoB"
                                AnalisisProfundidad.datos = InclinometroController.ctrlObtenerPANEprofundidad(tabla, idcomponente, idinstru, fechitas, 1, azimuth, mrint, "RST")
                            elif graficatipo == 'PAE':
                                posicion = "CampoA"
                                AnalisisProfundidad.datos = InclinometroController.ctrlObtenerPANEprofundidad(tabla, idcomponente, idinstru, fechitas, 1, azimuth, mrint, "RST")
                        else:
                            if graficatipo == 'DIA':
                                posicion = "CampoA"
                                AnalisisProfundidad.datos = InclinometroController.ctrlObtenerDIABprofundidad(tabla, idcomponente, idinstru, fechitas, 1, zz, mrint, "GEOKON")
                            elif graficatipo == 'DIB':
                                posicion = "CampoB"
                                AnalisisProfundidad.datos = InclinometroController.ctrlObtenerDIABprofundidad(tabla, idcomponente, idinstru, fechitas, 1, zz, mrint, "GEOKON")
                            elif graficatipo == 'DIN':
                                posicion = "CampoB"
                                AnalisisProfundidad.datos = InclinometroController.ctrlObtenerDINEprofundidad(tabla, idcomponente, idinstru, fechitas, 1, azimuth, mrint, "GEOKON")
                            elif graficatipo == 'DIE':
                                posicion = "CampoA"
                                AnalisisProfundidad.datos = InclinometroController.ctrlObtenerDINEprofundidad(tabla, idcomponente, idinstru, fechitas, 1, azimuth, mrint, "GEOKON")
                            elif graficatipo == 'DAA':
                                posicion = "CampoA"
                                AnalisisProfundidad.datos = InclinometroController.ctrlObtenerDAABprofundidad(tabla, idcomponente, idinstru, fechitas, 1, "GEOKON")
                            elif graficatipo == 'DAB':
                                posicion = "CampoB"
                                AnalisisProfundidad.datos = InclinometroController.ctrlObtenerDAABprofundidad(tabla, idcomponente, idinstru, fechitas, 1, "GEOKON")
                            elif graficatipo == 'DAN':
                                posicion = "CampoB"
                                AnalisisProfundidad.datos = InclinometroController.ctrlObtenerDANEprofundidad(tabla, idcomponente, idinstru, fechitas, 1, azimuth, mrint, zz, "GEOKON")
                            elif graficatipo == 'DAE':
                                posicion = "CampoA"
                                AnalisisProfundidad.datos = InclinometroController.ctrlObtenerDANEprofundidad(tabla, idcomponente, idinstru, fechitas, 1, azimuth, mrint, zz, "GEOKON")
                            elif graficatipo == 'PAA':
                                posicion = "CampoA"
                                AnalisisProfundidad.datos = InclinometroController.ctrlObtenerPAABprofundidad(tabla, idcomponente, idinstru, fechitas, 1, mrint, "GEOKON")
                            elif graficatipo == 'PAB':
                                posicion = "CampoB"
                                AnalisisProfundidad.datos = InclinometroController.ctrlObtenerPAABprofundidad(tabla, idcomponente, idinstru, fechitas, 1, mrint, "GEOKON")
                            elif graficatipo == 'PAN':
                                posicion = "CampoB"
                                AnalisisProfundidad.datos = InclinometroController.ctrlObtenerPANEprofundidad(tabla, idcomponente, idinstru, fechitas, 1, azimuth, mrint, "GEOKON")
                            elif graficatipo == 'PAE':
                                posicion = "CampoA"
                                AnalisisProfundidad.datos = InclinometroController.ctrlObtenerPANEprofundidad(tabla, idcomponente, idinstru, fechitas, 1, azimuth, mrint, "GEOKON")
                if AnalisisProfundidad.datos:
                    unidadmedida = comboUnidad.currentData()
                    if unidadmedida == 1:
                        unimed = "m"
                    elif unidadmedida == 100:
                        unimed = "cm"
                    else:
                        unimed = "mm"
                    AnalisisProfundidad.mostrarGraficaWidget(AnalisisProfundidad.datos, profundidad, posicion, tipotiempo, tendencia, grado, labelEcuacion, widgetGrafica, unidadmedida, unimed, nombreequipo)
                else:
                    mostrar_mensaje("Sin Datos", "No hay datos para graficar.", "advertencia")
            else:
                mostrar_mensaje("Sin Profundidad", "Ingrese una profundidad válida.", "advertencia")
        def aplicarUmbral():
            widget_grafico = dialogo.findChild(QWidget, "widget_desplazamiento")
            pintado = GraficarUmbrales.clean_on_widget(widget_grafico, 'linea')
            if pintado is False:
                id_intrumentacion = inclifechasmarcados[0][1][0][1]
                id_inclinometro = InclinometroController.ctrlObtenerIdIinclinometro(id_intrumentacion)
                umbrales = UmbralController.ctrlObtenerUmbralesInstrumentacion(idproyecto, id_inclinometro, 'UDI', 'umbral_inclinometro')
                unidadmedida = comboUnidad.currentData()
                GraficarUmbrales.draw_on_widget(widget_grafico, umbrales, unidadmedida, 'y', 'linea')
        def exportarDataprofundidad():
            if AnalisisProfundidad.datos:
                profundidad = spinProfundo.value()
                graficatipo = comboTipografica.currentData()
                if graficatipo == 'DIA':
                    posicion = "CampoA"
                    tipito = "Desplazamiento Incremental A"
                elif graficatipo == 'DIB':
                    posicion = "CampoB"
                    tipito = "Desplazamiento Incremental B"
                elif graficatipo == 'DIN':
                    posicion = "CampoB"
                    tipito = "Desplazamiento Incremental N"
                elif graficatipo == 'DIE':
                    posicion = "CampoA"
                    tipito = "Desplazamiento Incremental E"
                elif graficatipo == 'DAA':
                    posicion = "CampoA"
                    tipito = "Desplazamiento Acumulado A"
                elif graficatipo == 'DAB':
                    posicion = "CampoB"
                    tipito = "Desplazamiento Acumulado B"
                elif graficatipo == 'DAN':
                    posicion = "CampoB"
                    tipito = "Desplazamiento Acumulado N"
                elif graficatipo == 'DAE':
                    posicion = "CampoA"
                    tipito = "Desplazamiento Acumulado E"
                elif graficatipo == 'PAA':
                    posicion = "CampoA"
                    tipito = "Posición Absoluta A"
                elif graficatipo == 'PAB':
                    posicion = "CampoB"
                    tipito = "Posición Absoluta B"
                elif graficatipo == 'PAN':
                    posicion = "CampoB"
                    tipito = "Posición Absoluta N"
                elif graficatipo == 'PAE':
                    posicion = "CampoA"
                    tipito = "Posición Absoluta E"
                AnalisisProfundidad.exportarData(AnalisisProfundidad.datos, profundidad, posicion, tipito, tipoincli, nombreequipo)
            else:
                mostrar_mensaje("Sin Datos", "No hay datos para exportar.", "advertencia")
        # conectar señales
        comboTipografica.activated.connect(obtenerDataGraficar)
        botonReporte.clicked.connect(lambda: AnalisisProfundidad.imagenReporte(idproyecto, widgetGrafica, comboTipografica, "Anexos"))
        botonReporteGeneral.clicked.connect(lambda: AnalisisProfundidad.imagenReporte(idproyecto, widgetGrafica, comboTipografica, "General"))
        botonUmbral.clicked.connect(aplicarUmbral)
        botonGraficar.clicked.connect(obtenerDataGraficar)
        comboUnidad.activated.connect(obtenerDataGraficar)
        comboTiempo.activated.connect(obtenerDataGraficar)
        comboTendencia.activated.connect(obtenerDataGraficar)
        botonExportar.clicked.connect(exportarDataprofundidad)
        # mostrar dialogo
        dialogo.exec()
    
    def limpiar_widget(widget):
        # Configurar el layout y limpiar el anterior
        if widget.layout() is None:
            layout = QVBoxLayout(widget)
            widget.setLayout(layout)
        else:
            layout = widget.layout()
            while layout.count():
                item = layout.takeAt(0)
                widget_to_remove = item.widget()
                if widget_to_remove is not None:
                    widget_to_remove.deleteLater()
                else:
                    layout.removeItem(item)
    
    def imagenReporte(idproyecto, widget, comboTipografica, tiporeporte):
        if widget is not None:
            graficatipo = comboTipografica.currentData()
            tipografico = f"{graficatipo}AP"
            titulografica = f"Análisis Profundidad {graficatipo}"
            tipoequipo = "Inclinometro"
            if tiporeporte == "General":
                GraficaReporte.mostrarDialogoImagenVisor(widget, "Inclinometros", tipografico, titulografica, idproyecto, tipoequipo)
            else:
                ReporteImage.modalImagenReporte(widget, "Inclinometros", tipografico, titulografica, idproyecto, tipoequipo)
    
    def mostrarGraficaWidget(datos, profundidad, posicion, tipotiempo, tendencia, grado, labelEcuacion, widgetGrafica, unidad, medida, nombreequipo):
        # Limpiar widget existente
        AnalisisProfundidad.limpiar_widget(widgetGrafica)
        # Convertir datos a DataFrame si es necesario
        if not isinstance(datos, pd.DataFrame):
            datos = pd.DataFrame(datos, columns=["Instrumento", "fecha_inclinometro", "profundidad_detalle", "CampoA", "CampoB"])
        # Configurar formato de la fecha
        datos["fecha_inclinometro"] = pd.to_datetime(datos["fecha_inclinometro"])
        # Obtener fechas únicas ordenadas
        unique_fechas = sorted(datos["fecha_inclinometro"].unique())
        # Obtener datos de profundidad
        dataprofundidad = []
        fechas_validas = []
        for fecha in unique_fechas:
            datos_fecha = datos[datos["fecha_inclinometro"] == fecha]
            datos_profundidad = datos_fecha[abs(datos_fecha["profundidad_detalle"] - profundidad) < 0.1]
            if not datos_profundidad.empty:
                desplazamiento = datos_profundidad[posicion].iloc[0] * unidad
                dataprofundidad.append(desplazamiento)
                fechas_validas.append(fecha)
        if dataprofundidad:
            dataprofundidad[0] = 0
            # validar fechas
            if tipotiempo == "DIA":
                fecha_minima = min(fechas_validas)
                datafechas = [(fecha - fecha_minima).total_seconds()/(24*60*60) for fecha in fechas_validas]
            else:
                datafechas = fechas_validas
            # Crear figura y canvas
            config = SoftwareConfiguracion.obtenerDataSoftware()
            titulozise, ejezise, etiquesize, vertices = config[0], config[1], config[2], config[6]
            lineatenden, grosortenden, colortenden, fuente = config[7], config[8], config[9], config[10]
            grosorlinea, decimales = config[12], config[14]
            
            figura = plt.figure(figsize=(10, 6), constrained_layout=True)
            canvas = FigureCanvas(figura)
            plt.rcParams['font.family'] = fuente
            # Agregar el canvas al layout
            layout = widgetGrafica.layout()
            layout.addWidget(canvas)
            # Configurar el subplot
            ax = figura.add_subplot(111)
            #ax.figure.subplots_adjust(bottom=0.2, top=0.9)
            # Crear la gráfica
            if vertices == 1:
                ax.plot(datafechas, dataprofundidad, marker='o', markersize=grosorlinea + 4, linewidth=grosorlinea)
            else:
                ax.plot(datafechas, dataprofundidad, linewidth=grosorlinea)
            # Configurar el formato de las fechas en el eje x
            if tipotiempo == "FECHA":
                nombreeje = "Fechas"
                ax.xaxis.set_major_formatter(DateFormatter('%d/%m/%Y'))
                ax.xaxis.set_major_locator(mdates.AutoDateLocator())
                if tendencia != "ST":
                    if tendencia == "TL":
                        gradito = 1
                        nombretende = "Tendencia Lineal"
                    else:
                        gradito = grado
                        nombretende = "Tendencia Polinómica"
                    labelEcuacion.setText('Ecuación:')
                    fechas_num = mdates.date2num(datafechas)
                    z = np.polyfit(fechas_num, dataprofundidad, gradito)
                    p = np.poly1d(z)
                    ax.plot(fechas_num, p(fechas_num), color=colortenden, linestyle=lineatenden, linewidth=grosortenden, label=nombretende)
                else:
                    labelEcuacion.setText('Ecuación:')
            else:
                nombreeje = "Días"
                if tendencia != "ST":
                    if tendencia == "TL":
                        gradito = 1
                        nombretende = "Tendencia Lineal"
                    else:
                        gradito = grado
                        nombretende = "Tendencia Polinómica"
                    ecuacion = AnalisisProfundidad.generar_ecuaciones(datafechas, dataprofundidad, gradito)
                    labelEcuacion.setText(f'Ecuación: {ecuacion}')
                    z = np.polyfit(datafechas, dataprofundidad, gradito)
                    p = np.poly1d(z)
                    ax.plot(datafechas, p(datafechas), color=colortenden, linestyle=lineatenden, linewidth=grosortenden, label=nombretende)
                else:
                    labelEcuacion.setText('Ecuación:')
            # Rotar y alinear las etiquetas del eje x
            plt.setp(ax.get_xticklabels(), rotation=90, ha='right')
            ax.set_title(f'Desplazamientos a {profundidad} metros de profundidad: {nombreequipo}', fontsize=titulozise)
            ax.set_xlabel(nombreeje, fontsize=ejezise)
            ax.set_ylabel(f'Desplazamiento ({medida})', fontsize=ejezise)
            ax.grid(True, which='both', linestyle='--', linewidth=0.5)
            # configurar límites
            if all(isinstance(f, (datetime, date)) for f in datafechas):
                fechamin, fechamax = min(datafechas), max(datafechas)
                fechas_ticks = np.linspace(mdates.date2num(fechamin), mdates.date2num(fechamax), 20)
                fechas_ticks = mdates.num2date(fechas_ticks)
                ax.set_xticks(fechas_ticks)
            else:
                fechamin, fechamax = min(datafechas), max(datafechas)
                intervalox = (fechamax - fechamin) / 20
                if intervalox > 0:
                    ticks = np.arange(fechamin, fechamax + intervalox, intervalox)
                    ax.set_xticks(ticks)   
            ax.set_xlim(fechamin, fechamax)
            profumin, profumax = min(dataprofundidad), max(dataprofundidad)
            margen = (profumax - profumin) * 0.10
            profumin_margen = profumin - margen
            profumax_margen = profumax + margen
            ax.set_ylim(profumin_margen, profumax_margen)
            # Calcula los intervalos primarios
            intervalo = (profumax_margen - profumin_margen) / 9
            if intervalo > 0:
                ticks = np.arange(profumin_margen, profumax_margen + intervalo, intervalo)
                ax.set_yticks(ticks)
            # Ajustar la disposición
            figura.set_tight_layout(True)
            ax.tick_params(axis='x', pad=10, labelsize=etiquesize)
            ax.tick_params(axis='y', labelsize=etiquesize)
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda val, pos: '{:.{}f}'.format(val, decimales)))
            # Actualizar el canvas
            canvas.draw()
            # Establecer el layout en el widget
            widgetGrafica.setLayout(layout)
            plt.close(figura)
        else:
            mostrar_mensaje("Sin Datos", "No hay datos con esa profundidad.", "advertencia")
    
    def generar_ecuaciones(timestamps, displacements, grado):
        ecuacion_tendencia = AnalisisProfundidad.calculate_trend_line(timestamps, displacements, grado)
        r_cuadrado = AnalisisProfundidad.calculate_r_squared(timestamps, displacements, grado)
        if grado == 1:
            equation = f'y = {ecuacion_tendencia[1]:.6f}x + ({ecuacion_tendencia[0]:.6f})    R²={r_cuadrado:.6f}'
        elif grado == 2:
            equation = f'y = {ecuacion_tendencia[2]:.6f}x² + {ecuacion_tendencia[1]:.6f}x + ({ecuacion_tendencia[0]:.6f})    R²={r_cuadrado:.6f}'
        elif grado == 3:
            equation = f'y = {ecuacion_tendencia[3]:.6f}x³ + {ecuacion_tendencia[2]:.6f}x² + {ecuacion_tendencia[1]:.6f}x + ({ecuacion_tendencia[0]:.6f})    R²={r_cuadrado:.6f}'
        elif grado == 4:
            equation = f'y = {ecuacion_tendencia[4]:.6f}x⁴ + {ecuacion_tendencia[3]:.6f}x³ + {ecuacion_tendencia[2]:.6f}x² + {ecuacion_tendencia[1]:.6f}x + ({ecuacion_tendencia[0]:.6f})    R²={r_cuadrado:.6f}'
        elif grado == 5:
            equation = f'y = {ecuacion_tendencia[5]:.6f}x⁵ + {ecuacion_tendencia[4]:.6f}x⁴ + {ecuacion_tendencia[3]:.6f}x³ + {ecuacion_tendencia[2]:.6f}x² + {ecuacion_tendencia[1]:.6f}x + ({ecuacion_tendencia[0]:.6f})    R²={r_cuadrado:.6f}'
        elif grado == 6:
            equation = f'y = {ecuacion_tendencia[6]:.6f}x⁶ + {ecuacion_tendencia[5]:.6f}x⁵ + {ecuacion_tendencia[4]:.6f}x⁴ + {ecuacion_tendencia[3]:.6f}x³ + {ecuacion_tendencia[2]:.6f}x² + {ecuacion_tendencia[1]:.6f}x + ({ecuacion_tendencia[0]:.6f})    R²={r_cuadrado:.6f}'
        return equation
    
    def calculate_trend_line(timestamps, displacements, grado):
        coeffs = np.polyfit(timestamps, displacements, grado)
        trend_line = np.poly1d(coeffs)
        return trend_line
    
    def calculate_r_squared(timestamps, displacements, grado):
        coeficientes = np.polyfit(timestamps, displacements, grado)
        polinomio = np.poly1d(coeficientes)
        puntos_ajustados = polinomio(timestamps)
        residuos = displacements - puntos_ajustados
        suma_cuadrados_residuos = np.sum(residuos**2)
        suma_cuadrados_totales = np.sum((displacements - np.mean(displacements))**2)
        r_cuadrado = 1 - (suma_cuadrados_residuos / suma_cuadrados_totales)
        return r_cuadrado
    
    def exportarData(datos, profundidad, posicion, tipografica, marca, nombreequipo):
        if not isinstance(datos, pd.DataFrame):
            datos = pd.DataFrame(datos, columns=["Instrumento", "fecha_inclinometro", "profundidad_detalle", "CampoA", "CampoB"])
        # Configurar formato de la fecha
        datos["fecha_inclinometro"] = pd.to_datetime(datos["fecha_inclinometro"])
        # Obtener fechas únicas ordenadas
        unique_fechas = sorted(datos["fecha_inclinometro"].unique())
        # Obtener datos de profundidad
        dataprofundidad = []
        fechas_validas = []
        for fecha in unique_fechas:
            datos_fecha = datos[datos["fecha_inclinometro"] == fecha]
            datos_profundidad = datos_fecha[abs(datos_fecha["profundidad_detalle"] - profundidad) < 0.1]
            if not datos_profundidad.empty:
                desplazamiento = datos_profundidad[posicion].iloc[0]
                dataprofundidad.append(desplazamiento)
                fechas_validas.append(fecha)
        if dataprofundidad:
            dataprofundidad[0] = 0
            # encabezado
            metadatos = {
                'Titulo': 'Análisis de profundidad',
                'Descripción': tipografica,
                'Equipo': f'Inclinómetro {nombreequipo}',
                'Marca': marca,
                'Profundidad (m)': profundidad,
                'Unidad/lectura': "m"
            }
            # Abrir el cuadro de diálogo para seleccionar la ubicación y el nombre del archivo
            archivo_destino, _ = QFileDialog.getSaveFileName(None, "Guardar Excel en", "", "Archivos de Excel (*.xlsx);;Todos los archivos (*)")
            if archivo_destino:
                # Asegurarse de que el archivo tenga la extensión .xlsx
                if not archivo_destino.lower().endswith('.xlsx'):
                    archivo_destino += '.xlsx'
                libro_trabajo = Workbook()
                hoja_activa = libro_trabajo.active
                for clave, valor in metadatos.items():
                    hoja_activa.append([clave, valor])
                hoja_activa.append([])
                for fechita, profun in zip(fechas_validas, dataprofundidad):
                    hoja_activa.append([fechita, profun])
                libro_trabajo.save(archivo_destino)
                mostrar_mensaje("Exportado", f"Se guardó correctamente en {archivo_destino}.", "informacion")
        else:
            mostrar_mensaje("Sin Datos", "No hay datos con esa profundidad.", "advertencia")
    