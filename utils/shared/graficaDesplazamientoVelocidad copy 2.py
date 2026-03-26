import gc
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches as mpatches
import matplotlib.dates as mdates
import math
from datetime import datetime, timedelta
from PySide6.QtGui import Qt
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QDialog, QApplication,QCheckBox
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from utils.common.customToolbar import CustomToolbar 
from matplotlib.dates import DateFormatter
from utils.common.alertas import mostrar_mensaje
from utils.shared.calculostendencias import CalculosTendencias
from controllers.ConfiguracionController import ConfiguracionController
from modules.empresa.softwareconfiguracion import SoftwareConfiguracion
from controllers.PrismaController import PrismaController
from controllers.PiezometroController import PiezometroController
from controllers.CeldaController import CeldaController

class ModalDialog(QDialog):
    def __init__(self, parent, label, date, reading):  # Añadir parent
        super().__init__(parent, Qt.Window)  # Usar Qt.Window
        self.setWindowTitle("Omitir Lectura")
        self.resize(300, 150)

        layout = QVBoxLayout()

        # Añadir etiquetas con la información
        self.label_info = QLabel(f"Equipo: {label}")
        self.date_info = QLabel(f"Fecha: {date}")
        self.reading_info = QLabel(f"Lectura: {reading}")

        layout.addWidget(self.label_info)
        layout.addWidget(self.date_info)
        layout.addWidget(self.reading_info)

        # Añadir botones
        button_layout = QHBoxLayout()
        self.accept_button = QPushButton("Aceptar")
        self.cancel_button = QPushButton("Cancelar")

        button_layout.addWidget(self.accept_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Conectar botones a sus respectivas funciones
        self.accept_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

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

    # Eliminar toolbar anterior si existe en el layout
    if hasattr(widget, "toolbar") and widget.toolbar is not None:
        widget.toolbar.deleteLater()
        widget.toolbar = None

    # Eliminar botones anteriores si existen
    if hasattr(widget, "boton_siguiente") and widget.boton_siguiente is not None:
        widget.boton_siguiente.deleteLater()
        widget.boton_siguiente = None
    if hasattr(widget, "boton_anterior") and widget.boton_anterior is not None:
        widget.boton_anterior.deleteLater()
        widget.boton_anterior = None
    
    # limpiar memoria
    gc.collect()

def procesar_grafica(widget, labeltendencia, data, idx_nombre, idx_fecha, idx_lectura, labelejex, labelejey, tipo, medida, tiempo, titulo, idproyecto, modulo, pluviometro_data=None, equipostendencia=None, escala=None, fecha_inicio=None, fecha_fin=None):
    ax = None
    ax2 = None
    avisolabels = False
    
    # --- CORRECCIÓN SQL SERVER: Validar tipo de dato antes de convertir ---
    if fecha_inicio:
        if isinstance(fecha_inicio, str):
            fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d %H:%M:%S')
    if fecha_fin:
        if isinstance(fecha_fin, str):
            fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d %H:%M:%S')
    # ----------------------------------------------------------------------

    # Crear el DataFrame con las columnas necesarias
    df = pd.DataFrame(data, columns=['col_' + str(i) for i in range(len(data[0]))])
    df = df[[df.columns[0], df.columns[idx_nombre], df.columns[2], df.columns[idx_fecha], df.columns[idx_lectura], df.columns[-1]]]
    df.columns = ['Instrumento', 'Equipo', 'Tiempo', 'Fecha', tipo, 'TipoPrisma']

    if tiempo == "FECHA":
        # pd.to_datetime maneja bien str y datetime, no necesita cambio
        df['Fecha'] = pd.to_datetime(df['Fecha']) 
        if fecha_inicio is None:
            fecha_inicio = df['Fecha'].min()
            fecha_fin = df['Fecha'].max()
        fecha_inicio = pd.to_datetime(fecha_inicio)
        fecha_fin = pd.to_datetime(fecha_fin)
    else:
        if fecha_inicio is None:
            fecha_inicio = df['Fecha'].min()
            fecha_fin = df['Fecha'].max()
        else:
            # --- CORRECCIÓN SQL SERVER: La columna 'Tiempo' puede venir como objeto ---
            val_min_tiempo = df['Tiempo'].min()
            if isinstance(val_min_tiempo, str):
                fechainiproyecto = datetime.strptime(val_min_tiempo, '%Y-%m-%d %H:%M:%S')
            else:
                fechainiproyecto = val_min_tiempo # Ya es datetime
            # ------------------------------------------------------------------------
            
            if tiempo == "HORA":
                unidtiempo = 24
            else:
                unidtiempo = 1
            difdiasini = fecha_inicio - fechainiproyecto
            fecha_inicio = difdiasini.days * unidtiempo
            difdiasfin = fecha_fin - fechainiproyecto
            fecha_fin = difdiasfin.days * unidtiempo

    ejeymin, ejeymax, ejeyprin, ejeysecu, intervalo_dias = 0, 0, 0, 0, 0
    dataeje = ConfiguracionController.ctrlObtenerConfiguracionEje(idproyecto, modulo, tipo)
    if dataeje:
        ejeymin, ejeymax, ejeyprin, ejeysecu = dataeje[4], dataeje[5], dataeje[6], dataeje[7]
        if tiempo == "HORA":
            intervalo_dias = dataeje[8] * 24
        else:
            intervalo_dias = dataeje[8]
    if tiempo == "FECHA":
        total_dias = (fecha_fin - fecha_inicio).days
    else:
        # Aquí total_dias ya está en Horas o Días según la conversión anterior
        total_dias = (fecha_fin - fecha_inicio)

    # --- CORRECCIÓN APLICADA AQUÍ ---
    if intervalo_dias == 0:
        if tiempo == "HORA":
            # Eliminado el (* 24) redundante porque total_dias ya está en horas
            intervalo_dias = total_dias / 10 
        else:
            intervalo_dias = total_dias / 10
            
    limpiar_widget(widget)

    config = SoftwareConfiguracion.obtenerDataSoftware()
    titulozise, ejezise, etiquesize, leyendazise, vertices = config[0], config[1], config[2], config[3], config[6]
    lineatenden, grosortenden, colortenden, fuente = config[7], config[8], config[9], config[10]
    grosorlinea, grosorvertice, decimales, mostrarlluvia, posicionlluvia = config[12], config[13], config[14], config[17], config[18]

    # figure, ax = plt.subplots()
    # canvas = FigureCanvas(figure)
    # plt.rcParams['font.family'] = fuente
    # layout = widget.layout()
    # layout.addWidget(canvas)
    # toolbar_layout = QHBoxLayout()
    # widget.toolbar = CustomToolbar(canvas, widget)
    # toolbar_layout.addWidget(widget.toolbar)
    # layout.addLayout(toolbar_layout)
    
    figure, ax = plt.subplots()
    canvas = FigureCanvas(figure)
    plt.rcParams['font.family'] = fuente
    layout = widget.layout()
    layout.addWidget(canvas)

    # --- INICIO MODIFICACIÓN PASO 2 ---
    toolbar_layout = QHBoxLayout()
    widget.toolbar = CustomToolbar(canvas, widget)
    toolbar_layout.addWidget(widget.toolbar)
    
    # AGREGAMOS EL CHECKBOX AQUÍ
    check_inspector = QCheckBox("Inspector de Datos")
    check_inspector.setStyleSheet("font-size: 12px; margin-left: 10px; font-weight: bold;")
    toolbar_layout.addWidget(check_inspector)
    # ----------------------------------

    layout.addLayout(toolbar_layout)
    barras_pluviometro = None
    if tiempo == "FECHA":
        if modulo != "ANALISIS":
            if mostrarlluvia == 0:
                if pluviometro_data:
                    idpluvio = str(pluviometro_data[0][0])
                    estilo = ConfiguracionController.ctrlTraerEstiloEquipoGrafica(idproyecto, idpluvio, 0)
                    df_pluviometro = pd.DataFrame(pluviometro_data, columns=['Codigo', 'Fecha', 'Lectura'])
                    df_pluviometro['Fecha'] = pd.to_datetime(df_pluviometro['Fecha'])
                    ax2 = ax.twinx()
                    diferencia = df_pluviometro['Fecha'].max() - df_pluviometro['Fecha'].min()
                    totaldias = diferencia.days
                    ancho = 0.8
                    if totaldias > 0:
                        if totaldias < 100:
                            ancho = totaldias / 100
                        else:
                            ancho = totaldias / 200
                    if estilo:
                        if posicionlluvia == 0:
                            ax2.set_ylim(int(estilo[3]), 0)
                        else:
                            ax2.set_ylim(0, int(estilo[3]))
                        barras_pluviometro = ax2.bar(df_pluviometro['Fecha'], df_pluviometro['Lectura'], color=estilo[5], width=ancho, label="Precipitación")
                        ticks = np.arange(0, int(estilo[3]) + int(estilo[4]), int(estilo[4]))
                        ax2.set_yticks(ticks)
                    else:
                        if posicionlluvia == 0:
                            ax2.set_ylim(100, 0)
                        else:
                            ax2.set_ylim(0, 100)
                        barras_pluviometro = ax2.bar(df_pluviometro['Fecha'], df_pluviometro['Lectura'], color='cyan', width=ancho, alpha=0.5, label="Precipitación")
                    ax2.set_ylabel("Precipitacion (mm)", fontsize=ejezise)
                else:
                    ax2 = ax.twinx()
                    if posicionlluvia == 0:
                        ax2.set_ylim(100, 0)
                    else:
                        ax2.set_ylim(0, 100)
                    ax2.axhline(y=0, color='cyan', linestyle='-', linewidth=2, alpha=0.5)
                    ax2.set_ylabel("Precipitacion (mm)", fontsize=ejezise)
                    barras_pluviometro = mpatches.Patch(color='cyan', alpha=0.5)
            else:
                if pluviometro_data:
                    idpluvio = str(pluviometro_data[0][0])
                    estilo = ConfiguracionController.ctrlTraerEstiloEquipoGrafica(idproyecto, idpluvio, 0)
                    df_pluviometro = pd.DataFrame(pluviometro_data, columns=['Codigo', 'Fecha', 'Lectura'])
                    df_pluviometro['Fecha'] = pd.to_datetime(df_pluviometro['Fecha'])
                    ax2 = ax.twinx()
                    diferencia = df_pluviometro['Fecha'].max() - df_pluviometro['Fecha'].min()
                    totaldias = diferencia.days
                    ancho = 0.8
                    if totaldias > 0:
                        if totaldias < 100:
                            ancho = totaldias / 100
                        else:
                            ancho = totaldias / 200
                    if estilo:
                        if posicionlluvia == 0:
                            ax2.set_ylim(int(estilo[3]), 0)
                        else:
                            ax2.set_ylim(0, int(estilo[3]))
                        barras_pluviometro = ax2.bar(df_pluviometro['Fecha'], df_pluviometro['Lectura'], color=estilo[5], width=ancho, label="Precipitación")
                        ticks = np.arange(0, int(estilo[3]) + int(estilo[4]), int(estilo[4]))
                        ax2.set_yticks(ticks)
                    else:
                        if posicionlluvia == 0:
                            ax2.set_ylim(100, 0)
                        else:
                            ax2.set_ylim(0, 100)
                        barras_pluviometro = ax2.bar(df_pluviometro['Fecha'], df_pluviometro['Lectura'], color='cyan', width=ancho, alpha=0.5, label="Precipitación")
                    ax2.set_ylabel("Precipitacion (mm)", fontsize=ejezise)

    lineas = []
    lblecuacion_rcuadrado = ""
    prismasmodulo = {"DESPLAZAMIENTO", "VELOCIDAD", "ANALISIS"}
    equipotipo = 1 if modulo in prismasmodulo else 0

    for idinstrumento, datos_equipo in df.groupby('Instrumento'):
        nombreequipo = str(datos_equipo['Equipo'].iloc[0])
        if equipotipo == 1:
            equipo = str(datos_equipo['Equipo'].iloc[0])
        else:
            equipo = idinstrumento
        estilo = ConfiguracionController.ctrlTraerEstiloEquipoGrafica(idproyecto, idinstrumento, 0)
        if estilo:
            if vertices == 1:
                linea, = ax.plot(datos_equipo['Fecha'], datos_equipo[tipo], linestyle=estilo[3], marker='o', markersize=estilo[4] + 4, linewidth=estilo[4], color=estilo[5], label=nombreequipo)
            else:
                linea, = ax.plot(datos_equipo['Fecha'], datos_equipo[tipo], linestyle=estilo[3], linewidth=estilo[4], color=estilo[5], label=nombreequipo)
        else:
            if vertices == 1:
                linea, = ax.plot(datos_equipo['Fecha'], datos_equipo[tipo], marker='o', markersize=grosorvertice, linewidth=grosorlinea, label=nombreequipo)
            else:
                linea, = ax.plot(datos_equipo['Fecha'], datos_equipo[tipo], linewidth=grosorlinea, label=nombreequipo)
        lineas.append(linea)

        if equipostendencia:
            for instru, regresion, grado in equipostendencia:
                if str(instru[equipotipo]) == str(equipo):
                    if regresion == 'Lineal':
                        lineal = CalculosTendencias.dibujarTendenciaLineal(datos_equipo['Fecha'], datos_equipo[tipo], ax, tiempo, 1, nombreequipo, lineatenden, grosortenden, colortenden)
                        lineas.append(lineal)
                        ecualbl = CalculosTendencias.generarEcuacionTendencia(datos_equipo['Fecha'], datos_equipo[tipo], tiempo, 1)
                        lblecuacion_rcuadrado = lblecuacion_rcuadrado + nombreequipo + ':  ' + ecualbl + '\n'
                    elif regresion == 'Polinómica':
                        polino = CalculosTendencias.dibujarTendenciaLineal(datos_equipo['Fecha'], datos_equipo[tipo], ax, tiempo, grado, nombreequipo, lineatenden, grosortenden, colortenden)
                        lineas.append(polino)
                        ecualbl = CalculosTendencias.generarEcuacionTendencia(datos_equipo['Fecha'], datos_equipo[tipo], tiempo, grado)
                        lblecuacion_rcuadrado = lblecuacion_rcuadrado + nombreequipo + ':  ' + ecualbl + '\n'
                    elif regresion == 'Media Móvil':
                        media = CalculosTendencias.dibujarMediaMovil(datos_equipo['Fecha'], datos_equipo[tipo], ax, nombreequipo, grado, lineatenden, grosortenden, colortenden)
                        lineas.append(media)
                    elif regresion == 'Logarítmica':
                        logari, ecualbl = CalculosTendencias.dibujarTendenciaLogaritmica(datos_equipo['Fecha'], datos_equipo[tipo], ax, tiempo, nombreequipo, lineatenden, grosortenden, colortenden)
                        lineas.append(logari)
                        lblecuacion_rcuadrado = lblecuacion_rcuadrado + nombreequipo + ':  ' + ecualbl + '\n'
                    elif regresion == 'Exponencial':
                        exponen, ecualbl = CalculosTendencias.dibujarTendenciaExponencial(datos_equipo['Fecha'], datos_equipo[tipo], ax, tiempo, nombreequipo, lineatenden, grosortenden, colortenden)
                        if exponen:
                            lineas.append(exponen)
                            lblecuacion_rcuadrado = lblecuacion_rcuadrado + nombreequipo + ':  ' + ecualbl + '\n'
                    elif regresion == 'Potencial':
                        potenci, ecualbl = CalculosTendencias.dibujarTendenciaPotencial(datos_equipo['Fecha'], datos_equipo[tipo], ax, tiempo, nombreequipo, lineatenden, grosortenden, colortenden)
                        if potenci:
                            lineas.append(potenci)
                            lblecuacion_rcuadrado = lblecuacion_rcuadrado + nombreequipo + ':  ' + ecualbl + '\n'

    if tiempo != "FECHA":
        labeltendencia.setText(lblecuacion_rcuadrado)
    else:
        labeltendencia.setText("")

    ax.set_title(titulo, fontsize=titulozise)
    ax.set_xlabel(labelejex, fontsize=ejezise)
    ax.set_ylabel(labelejey, fontsize=ejezise)
    if tiempo == "FECHA":
        ax.xaxis.set_major_formatter(DateFormatter('%d/%m/%Y'))
    if not escala:
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda val, pos: '{:.{}f}'.format(val, decimales)))
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)

    # -----------------------------------------------------------------------------
    # MEJORA VISUAL: CÁLCULO DE ETIQUETAS SIMÉTRICAS (LINSPACE)
    # -----------------------------------------------------------------------------
    if tiempo == "FECHA":
        # Convertimos fechas a números de matplotlib
        num_inicio = mdates.date2num(fecha_inicio)
        num_fin = mdates.date2num(fecha_fin)
        rango_total = num_fin - num_inicio
        intervalo_num = intervalo_dias 
    else:
        # Ya son números (Días u Horas)
        num_inicio = float(fecha_inicio)
        num_fin = float(fecha_fin)
        rango_total = num_fin - num_inicio
        intervalo_num = intervalo_dias

    # Calcular cantidad de etiquetas basada en el intervalo
    if intervalo_num <= 0:
        num_etiquetas = 10
    else:
        num_etiquetas = int(rango_total / intervalo_num) + 1

    # Protección de saturación: Limitar a 15-20 etiquetas para que se vean bien
    if num_etiquetas > 25: 
        avisolabels = True
        num_etiquetas = 15 # Forzar visualización limpia
    elif num_etiquetas < 2:
        num_etiquetas = 2

    # Generación de puntos matemáticamente equidistantes (Simetría)
    etiquetas_numericas = np.linspace(num_inicio, num_fin, num_etiquetas)
    ax.set_xticks(etiquetas_numericas)

    if escala:
        if escala == 'ESL':
            ax.set_yscale("log", base=10)
            ax.set_xlim([num_inicio, num_fin])
        else:
            ax.set_xscale("log", base=10)
            ax.set_yscale("log", base=10)
    else:
        ax.set_xlim([num_inicio, num_fin])
    # -----------------------------------------------------------------------------
    
    plt.setp(ax.get_xticklabels(), rotation=90, ha="center", fontsize=etiquesize)
    plt.setp(ax.get_yticklabels(), fontsize=etiquesize)
    if modulo != "ANALISIS":
        if mostrarlluvia == 0:
            if tiempo == "FECHA":
                plt.setp(ax2.get_yticklabels(), fontsize=etiquesize)
        else:
            if tiempo == "FECHA":
                if pluviometro_data:
                    plt.setp(ax2.get_yticklabels(), fontsize=etiquesize)

    if ejeymin != 0 or ejeymax != 0:
        if escala is None:
            ax.set_ylim(ejeymin * medida, ejeymax * medida)
            maxejey = (ejeymax * medida) + 0.0001
            if ejeyprin > 0:
                tick_primarios = np.arange(ejeymin * medida, maxejey, ejeyprin * medida)
                if len(tick_primarios) > 1 and len(tick_primarios) < 100:
                    ax.set_yticks(tick_primarios)
                else:
                    avisolabels = True
            if ejeysecu > 0:
                tick_secundarios = np.arange(ejeymin * medida, maxejey, ejeysecu * medida)
                if len(tick_secundarios) > 1 and len(tick_secundarios) < 200:
                    for tick in tick_secundarios:
                        ax.axhline(y=tick, color='gray', linestyle='--', linewidth=0.5)
                else:
                    avisolabels = True
    # --- INICIO MODIFICACIÓN PASO 3 ---
    annot = ax.annotate("", xy=(0,0), xytext=(20,20), textcoords="offset points",
                        bbox=dict(boxstyle="round", fc="w", ec="k", alpha=0.9),
                        arrowprops=dict(arrowstyle="->"))
    annot.set_visible(False)

    # --- NUEVO: Punto que resalta el vértice exacto ---
    punto_resaltado, = ax.plot([], [], 'o', color='red', markersize=6, zorder=10)
    punto_resaltado.set_visible(False)
    # ----------------------------------
    def calculate_columns():
        font_config = {'family': fuente, 'size': leyendazise, 'weight': 'normal'}
        renderer = canvas.get_renderer()

        leyenda_labels = [line.get_label() for line in lineas] + (["Precipitación"] if barras_pluviometro else [])

        max_width = 0
        for label in leyenda_labels:
            text_obj = ax.text(0, 0, label, fontproperties=font_config)
            width = text_obj.get_window_extent(renderer).width + (leyendazise*3)
            max_width = max(max_width, width)
            text_obj.remove()

        ancho_pantalla = widget.width()

        return max(1, int((ancho_pantalla - 100) / (max_width + 50)))

    def actualizar_leyenda():
        try:
            ncols = calculate_columns()

            leyenda_elementos = lineas + ([barras_pluviometro] if barras_pluviometro else [])
            leyenda_labels = [line.get_label() for line in lineas] + (["Precipitación"] if barras_pluviometro else [])

            legend = ax.legend(handles=leyenda_elementos, labels=leyenda_labels, loc='upper center', bbox_to_anchor=(0.5, 0), ncol=ncols, frameon=False, fontsize=leyendazise, borderaxespad=0.8)
            renderer = canvas.get_renderer()
            canvas.draw()
            fig_bbox = figure.bbox
            legend_bbox = legend.get_window_extent(renderer)
            legend_height = legend_bbox.height / fig_bbox.height
            padding = 0.08
            bottom_margin = 0.20 + legend_height + padding
            top_margin = 0.95 - (legend_height * 0.3)

            if bottom_margin >= top_margin:
                bottom_margin = 0.25
                top_margin = 0.90
                if ncols == 1:
                    bottom_margin = 0.35
                    top_margin = 0.85

            figure.subplots_adjust(bottom=bottom_margin, top=top_margin, left=0.1, right=0.90)
            canvas.draw()
            if figure.subplotpars.bottom >= figure.subplotpars.top:
                raise ValueError("Margen inválido, aplicando valores seguros")
            xlabel_bbox = ax.xaxis.label.get_window_extent(renderer=renderer)
            xlabel_bottom = xlabel_bbox.transformed(ax.transAxes.inverted()).y0
            legend.set_bbox_to_anchor((0.5, xlabel_bottom))
        except Exception as e:
            figure.subplots_adjust(bottom=0.25, top=0.90, left=0.1, right=0.90)
            ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=2, fontsize=8)
            canvas.draw()

    def on_resize(event):
        actualizar_leyenda()
    
    def procesar_datos_console(id_proyecto,label, date, reading, tipo_prisma):
        # Convertir la fecha al formato yyyy-mm-dd hh:mm:ss para la consola
        date_obj = datetime.strptime(date, '%d/%m/%Y %H:%M:%S')
        formatted_date= date_obj.strftime('%Y-%m-%d %H:%M:%S')

        dialog = ModalDialog(widget,label, date, reading)
        result = dialog.exec()

        if result == QDialog.Accepted:          
            respuesta=PrismaController.ctrlOmitirLecturaPrisma(id_proyecto,label,formatted_date,tipo_prisma)
            if respuesta:
                print(f"{label}\nFecha: {formatted_date}\nLectura: {reading}\nTipo: {tipo_prisma}")
            else:
                print('error al omitir')
                
    # ---------------- INICIO DE FUNCIÓN CORREGIDA ----------------
    def on_hover(event):
        # 1. Validaciones básicas: Checkbox activo y mouse dentro de los ejes
        if not check_inspector.isChecked() or event.inaxes != ax:
            if annot.get_visible():
                annot.set_visible(False)
                punto_resaltado.set_visible(False)
                canvas.draw_idle()
            return

        # 2. Configuración inicial
        # Radio de captura en píxeles (sensibilidad)
        min_distancia = 50 
        punto_encontrado = None
        
        # Transformaciones para cálculos de coordenadas
        trans_data = ax.transData
        trans_axes = ax.transAxes
        inv_trans_axes = trans_axes.inverted()
        
        # Límites del zoom actual
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()

        # 3. Búsqueda del punto más cercano
        for line in lineas:
            x_data, y_data = line.get_data()
            
            # --- Conversión segura de fechas a números ---
            if tiempo == "FECHA":
                try:
                    if pd.api.types.is_datetime64_any_dtype(x_data) or isinstance(x_data, pd.DatetimeIndex):
                         x_data = mdates.date2num(x_data)
                    elif isinstance(x_data, np.ndarray) and x_data.dtype == 'object':
                         x_data = mdates.date2num(x_data)
                except Exception:
                    continue 
            # ---------------------------------------------

            # Optimización: Solo procesar puntos visibles en pantalla
            mask = (x_data >= xlim[0]) & (x_data <= xlim[1]) & (y_data >= ylim[0]) & (y_data <= ylim[1])
            if not np.any(mask): continue
            
            x_visibles = x_data[mask]
            y_visibles = y_data[mask]
            
            # Convertir datos a coordenadas de píxeles
            puntos_pixel = trans_data.transform(np.column_stack([x_visibles, y_visibles]))
            mouse_pos = np.array([event.x, event.y])
            
            # Calcular distancias
            distancias = np.sqrt(np.sum((puntos_pixel - mouse_pos)**2, axis=1))
            if len(distancias) == 0: continue

            idx_min = np.argmin(distancias)
            dist_actual = distancias[idx_min]
            
            if dist_actual < min_distancia:
                min_distancia = dist_actual
                punto_encontrado = (x_visibles[idx_min], y_visibles[idx_min], line.get_label())

        # 4. LÓGICA DE POSICIONAMIENTO "ANTICHOQUE"
        if punto_encontrado:
            fecha_num, lectura_val, label_equipo = punto_encontrado
            
            # A. Dibujar el punto rojo
            punto_resaltado.set_data([fecha_num], [lectura_val])
            punto_resaltado.set_visible(True)
            punto_resaltado.set_zorder(100)
            
            # B. Calcular posición relativa en los ejes (0.0 a 1.0)
            # Esto es lo que nos garantiza saber si estamos "arriba" o "abajo" independientemente de los valores
            pixel_point = trans_data.transform((fecha_num, lectura_val))
            axes_point = inv_trans_axes.transform(pixel_point)
            
            x_rel = axes_point[0] # 0=Izquierda, 1=Derecha
            y_rel = axes_point[1] # 0=Abajo, 1=Arriba

            # C. Definir márgenes de seguridad (Offsets)
            # Distancia base desde el punto rojo hasta el inicio de la caja
            base_offset = 40
            
            offset_x = 0
            offset_y = 0
            
            # Alineaciones (Horizontal Alignment / Vertical Alignment)
            ha = 'center'
            va = 'center'

            # --- REGLAS ESTRICTAS DE POSICIONAMIENTO ---
            
            # EJE VERTICAL (Evitar chocar con Título o Eje X)
            if y_rel > 0.5:
                # El punto está en la mitad SUPERIOR -> La caja DEBE ir ABAJO
                va = 'top'  # El borde superior de la caja se pega al ancla
                offset_y = -base_offset # Empujamos hacia abajo (negativo)
                
                # SI ESTÁ MUY ARRIBA (Casi tocando el título, > 85%)
                if y_rel > 0.85:
                    offset_y = -60 # Empujamos MÁS abajo para asegurar espacio
            else:
                # El punto está en la mitad INFERIOR -> La caja DEBE ir ARRIBA
                va = 'bottom' # El borde inferior de la caja se pega al ancla
                offset_y = base_offset # Empujamos hacia arriba (positivo)

            # EJE HORIZONTAL (Evitar salirse por los lados)
            if x_rel > 0.6:
                # Está a la derecha -> Mover a la izquierda
                ha = 'right'
                offset_x = -base_offset
            elif x_rel < 0.4:
                # Está a la izquierda -> Mover a la derecha
                ha = 'left'
                offset_x = base_offset
            else:
                # Centro
                ha = 'left'
                offset_x = base_offset

            # D. Aplicar configuración a la anotación
            annot.xy = (fecha_num, lectura_val)
            
            # IMPORTANTE: textcoords="offset points" hace que (offset_x, offset_y) sean píxeles desde el punto
            annot.xytext = (offset_x, offset_y) 
            
            annot.set_ha(ha)
            annot.set_va(va)
            
            # E. Estilo de Flecha y Caja
            # Usamos una flecha recta simple para evitar arcos que salgan del gráfico
            annot.arrow_patch.set_connectionstyle("arc3,rad=0") 
            
            # Formatear Texto
            if tiempo == "FECHA":
                fecha_obj = mdates.num2date(fecha_num).replace(tzinfo=None)
                str_fecha = fecha_obj.strftime('%d/%m/%Y %H:%M:%S')
            else:
                str_fecha = f"{fecha_num:.2f}"
            
            text = f"Equipo: {label_equipo}\nFecha: {str_fecha}\nLectura: {lectura_val:.3f}"
            annot.set_text(text)
            
            # Estilo visual
            annot.get_bbox_patch().set_boxstyle("round,pad=0.5")
            annot.get_bbox_patch().set_alpha(1.0) # Opaco
            annot.get_bbox_patch().set_facecolor('#ffffe0') 
            annot.get_bbox_patch().set_edgecolor('black')
            
            # F. Z-Order Máximo (Encima de todo)
            annot.set_zorder(999) 
            
            annot.set_visible(True)
            canvas.draw_idle()
        
        else:
            if annot.get_visible():
                annot.set_visible(False)
                punto_resaltado.set_visible(False)
                canvas.draw_idle()       
    # ---------------- FIN DE FUNCIÓN CORREGIDA ----------------
    
    def on_click(event):
        # Determinar el eje y las anotaciones a usar
        if ax2:
            current_ax = ax2
        else:
            current_ax = ax

        # Verificar si el clic está dentro de los límites de los ejes
        if current_ax and current_ax.in_axes(event) and event.xdata is not None and event.ydata is not None:
            for line in lineas:
                contains, _ = line.contains(event)
                if contains:
                    label = line.get_label()
                    x = mdates.num2date(event.xdata)  # Convertir x a objeto datetime
                    x = x.replace(tzinfo=None)  # Asegurarse de que x no tenga información de zona horaria
                    y = event.ydata

                    # Filtrar los datos para obtener solo los puntos correspondientes a la línea clickeada
                    line_data = df[df['Equipo'] == label]

                    # Verificar si line_data está vacío
                    if line_data.empty:
                        # Si está vacío, mostrar la anotación en el punto donde se hizo clic
                        date = x.strftime('%d/%m/%Y %H:%M:%S')  # Formatear la fecha como dd/mm/yyyy hh:mm:ss
                        reading = round(y, 3)  # Redondear la lectura a 3 decimales
                        annotation_text = f"{label}\nFecha: {date}\nLectura: {reading}"
                    else:
                        # Asegurarse de que la columna 'Fecha' no tenga información de zona horaria
                        if line_data['Fecha'].dt.tz is not None:
                            line_data['Fecha'] = line_data['Fecha'].dt.tz_localize(None)

                        # Encontrar el punto de datos más cercano al evento de clic en la línea específica
                        data_point = line_data.iloc[(line_data['Fecha'] - x).abs().argmin()]
                        closest_x = data_point['Fecha']
                        closest_y = data_point[tipo]
                        date = closest_x.strftime('%d/%m/%Y %H:%M:%S')  # Formatear la fecha como dd/mm/yyyy hh:mm:ss
                        reading = round(closest_y, 3)  # Redondear la lectura a 3 decimales
                        tipo_prisma = data_point['TipoPrisma']  # Obtener el valor de la columna 'TipoPrisma'
                        annotation_text = f"{label}\nFecha: {date}\nLectura: {reading}"

                    # Si se presiona el botón derecho del mouse (anticlick)
                    if event.button == 3:
                        # Ocultar anotaciones anteriores si existen
                        for text in current_ax.texts:
                            text.set_visible(False)

                        # Crear y mostrar la anotación en el punto más cercano o en el punto de clic
                        annotation = current_ax.annotate(annotation_text, (x, y),
                                                        textcoords="offset points", xytext=(10, 10),
                                                        ha='left', fontsize=etiquesize,
                                                        bbox=dict(facecolor='yellow', alpha=0.8, edgecolor='none'))
                        annotation.set_visible(True)
                        canvas.draw()
                        break  # Salir del bucle una vez que se haya encontrado una línea

        # Si se presiona el botón izquierdo del mouse (click) en cualquier lugar
        if event.button == 1:
            # Verificar si la tecla Control está presionada
            if event.guiEvent.modifiers() & Qt.ControlModifier:
                # Llamar al método para procesar los datos
                procesar_datos_console(idproyecto,label, date, reading, tipo_prisma)
            else:
                # Ocultar todas las anotaciones existentes
                for text in current_ax.texts:
                    text.set_visible(False)
                canvas.draw()

    canvas.mpl_connect('resize_event', on_resize)
    canvas.mpl_connect('button_press_event', on_click)
    canvas.mpl_connect('motion_notify_event', on_hover)
    actualizar_leyenda()
    plt.close(figure)
    if avisolabels:
        mostrar_mensaje("Ejes", "No se aplica la configuración de ejes.", "advertencia")

def procesar_grafica_piezometros(widget, labeltendencia, data, cotasmarcadas, idx_nombre, idx_fecha, idx_lectura, idx_funda, idx_super, labelejex, labelejey, tipo, medida, tiempo, titulo, idproyecto, modulo, pluviometro_data=None, equipostendencia=None, dataterreno=None, fecha_inicio=None, fecha_fin=None):
    ax = None
    ax2 = None
    avisolabels = False
    
    # --- CORRECCIÓN SQL SERVER: Validar tipo de dato antes de convertir ---
    if fecha_inicio:
        if isinstance(fecha_inicio, str):
            fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d %H:%M:%S')
    if fecha_fin:
        if isinstance(fecha_fin, str):
            fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d %H:%M:%S')
    # ----------------------------------------------------------------------
    
    # Convertir fechas a datetime y asignar valores por defecto
    ejeymin, ejeymax, ejeyprin, ejeysecu, intervalo_dias = 0, 0, 0, 0, 0
    if data:
        df = pd.DataFrame(data, columns=['col_' + str(i) for i in range(len(data[0]))])
        df = df[[df.columns[0], df.columns[idx_nombre], df.columns[2], df.columns[idx_fecha], df.columns[idx_lectura], df.columns[idx_funda], df.columns[idx_super], df.columns[-2],df.columns[-1]]]
        df.columns = ['Instrumento', 'Equipo', 'Tiempo', 'Fecha', tipo, "Fundacion", "Superficie", "TipoPiezo", "idEquipo"]
        # validar formato filtrado
        if tiempo == "FECHA":
            df['Fecha'] = pd.to_datetime(df['Fecha'])
            if fecha_inicio is None:
                fecha_inicio = df['Fecha'].min()
                fecha_fin = df['Fecha'].max()
            fecha_inicio = pd.to_datetime(fecha_inicio)
            fecha_fin = pd.to_datetime(fecha_fin)
        else:
            df['Fecha'] = df['Fecha'].astype(float)
            if fecha_inicio is None:
                fecha_inicio = df['Fecha'].min()
                fecha_fin = df['Fecha'].max()
            else: # con zoom
                # --- CORRECCIÓN SQL SERVER: La columna 'Tiempo' puede venir como objeto ---
                val_min_tiempo = df['Tiempo'].min()
                if isinstance(val_min_tiempo, str):
                    fechainiproyecto = datetime.strptime(val_min_tiempo, '%Y-%m-%d %H:%M:%S')
                else:
                    fechainiproyecto = val_min_tiempo
                # ------------------------------------------------------------------------
                
                if tiempo == "HORA":
                    unidtiempo = 24
                else:
                    unidtiempo = 1
                difdiasini = fecha_inicio - fechainiproyecto
                fecha_inicio = difdiasini.days * unidtiempo
                difdiasfin = fecha_fin - fechainiproyecto
                fecha_fin = difdiasfin.days * unidtiempo
    # Ajustar limites de gráficas eje y
    dataeje = ConfiguracionController.ctrlObtenerConfiguracionEje(idproyecto, modulo, tipo)
    if dataeje:
        ejeymin, ejeymax, ejeyprin, ejeysecu = dataeje[4], dataeje[5], dataeje[6], dataeje[7]
        if tiempo == "HORA":
            intervalo_dias = dataeje[8] * 24
        else:
            intervalo_dias = dataeje[8]
    if tiempo == "FECHA":
        total_dias = (fecha_fin - fecha_inicio).days
    else:
        total_dias = (fecha_fin - fecha_inicio)
        
    # --- CORRECCIÓN APLICADA AQUÍ ---
    if intervalo_dias == 0:
        if tiempo == "HORA":
            # Eliminado el (* 24) redundante porque total_dias ya está en horas
            intervalo_dias = total_dias / 10
        else:
            intervalo_dias = total_dias / 10

    # Limpiar el widget
    limpiar_widget(widget)
    config = SoftwareConfiguracion.obtenerDataSoftware()
    titulozise, ejezise, etiquesize, leyendazise, cotasize = config[0], config[1], config[2], config[3], config[4]
    mostrarcota, vertices, lineatenden, grosortenden, colortenden = config[5], config[6], config[7], config[8], config[9]
    fuente, grosorlinea, grosorvertice, decimales = config[10], config[12], config[13], config[14]
    mostrarlluvia, posicionlluvia = config[17], config[18]
    # Ajustar el tamaño de la figura al tamaño del widget
    figure, ax = plt.subplots()
    canvas = FigureCanvas(figure)
    plt.rcParams['font.family'] = fuente
    layout = widget.layout()
    layout.addWidget(canvas)
    toolbar_layout = QHBoxLayout()
    widget.toolbar = CustomToolbar(canvas, widget)
    toolbar_layout.addWidget(widget.toolbar)
    layout.addLayout(toolbar_layout)
    # Configurar eje secundario si hay datos de pluviómetro
    barras_pluviometro = None
    if tiempo == "FECHA":
        if mostrarlluvia == 0: # siempre visible
            if pluviometro_data:
                idpluvio = str(pluviometro_data[0][0])
                estilo = ConfiguracionController.ctrlTraerEstiloEquipoGrafica(idproyecto, idpluvio, 0)
                df_pluviometro = pd.DataFrame(pluviometro_data, columns=['Codigo', 'Fecha', 'Lectura'])
                df_pluviometro['Fecha'] = pd.to_datetime(df_pluviometro['Fecha'])
                ax2 = ax.twinx()
                # Calcular el ancho de la barra
                diferencia = df_pluviometro['Fecha'].max() - df_pluviometro['Fecha'].min()
                totaldias = diferencia.days
                ancho = 0.8
                if totaldias > 0:
                    if totaldias < 100:
                        ancho = totaldias / 100
                    else:
                        ancho = totaldias / 200
                if estilo:
                    if posicionlluvia == 0:
                        ax2.set_ylim(int(estilo[3]), 0)
                    else:
                        ax2.set_ylim(0, int(estilo[3]))
                    barras_pluviometro = ax2.bar(df_pluviometro['Fecha'], df_pluviometro['Lectura'], color=estilo[5], width=ancho, label="Precipitación")
                    ticks = np.arange(0, int(estilo[3]) + int(estilo[4]), int(estilo[4]))
                    ax2.set_yticks(ticks)
                else:
                    if posicionlluvia == 0:
                        ax2.set_ylim(100, 0)
                    else:
                        ax2.set_ylim(0, 100)
                    barras_pluviometro = ax2.bar(df_pluviometro['Fecha'], df_pluviometro['Lectura'], color='cyan', width=ancho, alpha=0.5, label="Precipitación")
                ax2.set_ylabel("Precipitacion (mm)", fontsize=ejezise)
            else:
                if modulo == "PIEZOMETROS":
                    ax2 = ax.twinx()
                    if posicionlluvia == 0:
                        ax2.set_ylim(100, 0)
                    else:
                        ax2.set_ylim(0, 100)
                    ax2.axhline(y=0, color='cyan', linestyle='-', linewidth=2, alpha=0.5)
                    ax2.set_ylabel("Precipitacion (mm)", fontsize=ejezise)
                    barras_pluviometro = mpatches.Patch(color='cyan', alpha=0.5)
        else:
            if pluviometro_data:
                idpluvio = str(pluviometro_data[0][0])
                estilo = ConfiguracionController.ctrlTraerEstiloEquipoGrafica(idproyecto, idpluvio, 0)
                df_pluviometro = pd.DataFrame(pluviometro_data, columns=['Codigo', 'Fecha', 'Lectura'])
                df_pluviometro['Fecha'] = pd.to_datetime(df_pluviometro['Fecha'])
                ax2 = ax.twinx()
                # Calcular el ancho de la barra
                diferencia = df_pluviometro['Fecha'].max() - df_pluviometro['Fecha'].min()
                totaldias = diferencia.days
                ancho = 0.8
                if totaldias > 0:
                    if totaldias < 100:
                        ancho = totaldias / 100
                    else:
                        ancho = totaldias / 200
                if estilo:
                    if posicionlluvia == 0:
                        ax2.set_ylim(int(estilo[3]), 0)
                    else:
                        ax2.set_ylim(0, int(estilo[3]))
                    barras_pluviometro = ax2.bar(df_pluviometro['Fecha'], df_pluviometro['Lectura'], color=estilo[5], width=ancho, label="Precipitación")
                    ticks = np.arange(0, int(estilo[3]) + int(estilo[4]), int(estilo[4]))
                    ax2.set_yticks(ticks)
                else:
                    if posicionlluvia == 0:
                        ax2.set_ylim(100, 0)
                    else:
                        ax2.set_ylim(0, 100)
                    barras_pluviometro = ax2.bar(df_pluviometro['Fecha'], df_pluviometro['Lectura'], color='cyan', width=ancho, alpha=0.5, label="Precipitación")
                ax2.set_ylabel("Precipitacion (mm)", fontsize=ejezise)
    # Graficar datos de desplazamiento
    lineas = []
    lblecuacion_rcuadrado = ""
    if data:
        # validar si son prismas para las tendencias y graficar
        for idinstrumento, datos_equipo in df.groupby('Instrumento'):
            nombreequipo = str(datos_equipo['Equipo'].iloc[0])
            estilo = ConfiguracionController.ctrlTraerEstiloEquipoGrafica(idproyecto, idinstrumento, 0)
            if estilo:
                if vertices == 1:
                    linea, = ax.plot(datos_equipo['Fecha'], datos_equipo[tipo], marker='o', markersize=estilo[4] + 4, linestyle=estilo[3], linewidth=estilo[4], color=estilo[5], label=nombreequipo)
                else:
                    linea, = ax.plot(datos_equipo['Fecha'], datos_equipo[tipo], linestyle=estilo[3], linewidth=estilo[4], color=estilo[5], label=nombreequipo)
            else:
                if vertices == 1:
                    linea, = ax.plot(datos_equipo['Fecha'], datos_equipo[tipo], marker='o', label=nombreequipo)
                else:
                    linea, = ax.plot(datos_equipo['Fecha'], datos_equipo[tipo], label=nombreequipo)
            lineas.append(linea)
            # graficar cota piezometrica
            if tipo == "NF": # piezómetros
                for piezo, cotas in cotasmarcadas:
                    for cota in cotas:
                        if piezo[1] == str(idinstrumento):
                            if cota[0] != "":
                                if cota[0] == "Cota de Fundación":
                                    estilo = ConfiguracionController.ctrlTraerEstiloEquipoGrafica(idproyecto, idinstrumento, 1)
                                    if estilo:
                                        linea, = ax.plot(datos_equipo['Fecha'], datos_equipo["Fundacion"], linestyle=estilo[3], linewidth=estilo[4], color=estilo[5], label=f"Fundación {nombreequipo}")
                                    else:
                                        linea, = ax.plot(datos_equipo['Fecha'], datos_equipo["Fundacion"], label=f"Fundación {nombreequipo}")
                                    if mostrarcota == 1:
                                        fechauno = datos_equipo['Fecha'].iloc[0]
                                        if fechauno > fecha_inicio:
                                            fechacota = fechauno
                                        else:
                                            fechacota = fecha_inicio
                                        resultado = df.loc[df['Fecha'] == fechacota, 'Fundacion']
                                        valor_fundacion = resultado.iloc[0] if not resultado.empty else datos_equipo["Fundacion"].iloc[0]
                                        ax.text(fechacota, valor_fundacion, f"  Fundación {valor_fundacion} msnm", horizontalalignment='left', verticalalignment='bottom', fontsize=cotasize)
                                else:
                                    estilo = ConfiguracionController.ctrlTraerEstiloEquipoGrafica(idproyecto, idinstrumento, 2)
                                    if estilo:
                                        linea, = ax.plot(datos_equipo['Fecha'], datos_equipo["Superficie"], linestyle=estilo[3], linewidth=estilo[4], color=estilo[5], label=f"Superficie {nombreequipo}")
                                    else:
                                        linea, = ax.plot(datos_equipo['Fecha'], datos_equipo["Superficie"], label=f"Superficie {nombreequipo}")
                                    if mostrarcota == 1:
                                        fechauno = datos_equipo['Fecha'].iloc[0]
                                        if fechauno > fecha_inicio:
                                            fechacota = fechauno
                                        else:
                                            fechacota = fecha_inicio
                                        resultado = df.loc[df['Fecha'] == fechacota, 'Superficie']
                                        valor_superficie = resultado.iloc[0] if not resultado.empty else datos_equipo["Superficie"].iloc[0]
                                        ax.text(fechacota, valor_superficie, f"  Superficie {valor_superficie} msnm", horizontalalignment='left', verticalalignment='bottom', fontsize=cotasize)
                                lineas.append(linea)
            elif tipo == "AC": # celdas
                for piezo, cotas in cotasmarcadas:
                    for cota in cotas:
                        if piezo[1] == str(idinstrumento):
                            if cota[0] != "":
                                if cota[0] == "Cota de Fundación":
                                    estilo = ConfiguracionController.ctrlTraerEstiloEquipoGrafica(idproyecto, idinstrumento, 1)
                                    if estilo:
                                        linea, = ax.plot(datos_equipo['Fecha'], datos_equipo["Fundacion"], linestyle=estilo[3], linewidth=estilo[4], color=estilo[5], label=f"Fundación {nombreequipo}")
                                    else:
                                        linea, = ax.plot(datos_equipo['Fecha'], datos_equipo["Fundacion"], label=f"Fundación {nombreequipo}")
                                    if mostrarcota == 1:
                                        fechauno = datos_equipo['Fecha'].iloc[0]
                                        if fechauno > fecha_inicio:
                                            fechacota = fechauno
                                        else:
                                            fechacota = fecha_inicio
                                        resultado = df.loc[df['Fecha'] == fechacota, 'Fundacion']
                                        valor_fundacion = resultado.iloc[0] if not resultado.empty else datos_equipo["Fundacion"].iloc[0]
                                        ax.text(fechacota, valor_fundacion, f"  Fundación {valor_fundacion} msnm", horizontalalignment='left', verticalalignment='bottom', fontsize=cotasize)
                                else:
                                    estilo = ConfiguracionController.ctrlTraerEstiloEquipoGrafica(idproyecto, idinstrumento, 2)
                                    if estilo:
                                        linea, = ax.plot(datos_equipo['Fecha'], datos_equipo["Superficie"], linestyle=estilo[3], linewidth=estilo[4], color=estilo[5], label=f"Superficie {nombreequipo}")
                                    else:
                                        linea, = ax.plot(datos_equipo['Fecha'], datos_equipo["Superficie"], label=f"Superficie {nombreequipo}")
                                    if mostrarcota == 1:
                                        fechauno = datos_equipo['Fecha'].iloc[0]
                                        if fechauno > fecha_inicio:
                                            fechacota = fechauno
                                        else:
                                            fechacota = fecha_inicio
                                        resultado = df.loc[df['Fecha'] == fechacota, 'Superficie']
                                        valor_superficie = resultado.iloc[0] if not resultado.empty else datos_equipo["Superficie"].iloc[0]
                                        ax.text(fechacota, valor_superficie, f"  Superficie {valor_superficie} msnm", horizontalalignment='left', verticalalignment='bottom', fontsize=cotasize)
                                lineas.append(linea)
            # Graficar tendencias
            if equipostendencia:
                for instru, regresion, grado in equipostendencia:
                    if str(instru[0]) == str(idinstrumento):
                        if regresion == 'Lineal':
                            lineal = CalculosTendencias.dibujarTendenciaLineal(datos_equipo['Fecha'], datos_equipo[tipo], ax, tiempo, 1, nombreequipo, lineatenden, grosortenden, colortenden)
                            lineas.append(lineal)
                            ecualbl = CalculosTendencias.generarEcuacionTendencia(datos_equipo['Fecha'], datos_equipo[tipo], tiempo, 1)
                            lblecuacion_rcuadrado = lblecuacion_rcuadrado + nombreequipo + ':  ' + ecualbl + '\n'
                        elif regresion == 'Polinómica':
                            polino = CalculosTendencias.dibujarTendenciaLineal(datos_equipo['Fecha'], datos_equipo[tipo], ax, tiempo, grado, nombreequipo, lineatenden, grosortenden, colortenden)
                            lineas.append(polino)
                            ecualbl = CalculosTendencias.generarEcuacionTendencia(datos_equipo['Fecha'], datos_equipo[tipo], tiempo, grado)
                            lblecuacion_rcuadrado = lblecuacion_rcuadrado + nombreequipo + ':  ' + ecualbl + '\n'
                        elif regresion == 'Media Móvil':
                            media = CalculosTendencias.dibujarMediaMovil(datos_equipo['Fecha'], datos_equipo[tipo], ax, nombreequipo, grado, lineatenden, grosortenden, colortenden)
                            lineas.append(media)
                        elif regresion == 'Logarítmica':
                            logari, ecualbl = CalculosTendencias.dibujarTendenciaLogaritmica(datos_equipo['Fecha'], datos_equipo[tipo], ax, tiempo, nombreequipo, lineatenden, grosortenden, colortenden)
                            lineas.append(logari)
                            lblecuacion_rcuadrado = lblecuacion_rcuadrado + nombreequipo + ':  ' + ecualbl + '\n'
                        elif regresion == 'Exponencial':
                            exponen, ecualbl = CalculosTendencias.dibujarTendenciaExponencial(datos_equipo['Fecha'], datos_equipo[tipo], ax, tiempo, nombreequipo, lineatenden, grosortenden, colortenden)
                            if exponen:
                                lineas.append(exponen)
                                lblecuacion_rcuadrado = lblecuacion_rcuadrado + nombreequipo + ':  ' + ecualbl + '\n'
                        elif regresion == 'Potencial':
                            potenci, ecualbl = CalculosTendencias.dibujarTendenciaPotencial(datos_equipo['Fecha'], datos_equipo[tipo], ax, tiempo, nombreequipo, lineatenden, grosortenden, colortenden)
                            if potenci:
                                lineas.append(potenci)
                                lblecuacion_rcuadrado = lblecuacion_rcuadrado + nombreequipo + ':  ' + ecualbl + '\n'
    if tiempo != "FECHA":
        labeltendencia.setText(lblecuacion_rcuadrado)
    else:
        labeltendencia.setText("")
    if tipo == "NF":
        # graficar terrenos
        if dataterreno:
            df_terreno = pd.DataFrame(dataterreno, columns=['Codigo', 'Nombre', 'Fecha', 'Dias', 'Horas', 'Lectura'])
            if tiempo == "FECHA":
                df_terreno['Fecha'] = pd.to_datetime(df_terreno['Fecha'])
                tipoterre = "Fecha"
                if data is None:
                    df_terreno['Fecha'] = pd.to_datetime(df_terreno['Fecha'])
                    if fecha_inicio is None:
                        fecha_inicio = df_terreno['Fecha'].min()
                        fecha_fin = df_terreno['Fecha'].max()
                    fecha_inicio = pd.to_datetime(fecha_inicio)
                    fecha_fin = pd.to_datetime(fecha_fin)
            elif tiempo == "DIA":
                tipoterre = "Dias"
                if data is None:
                    if fecha_inicio is None:
                        fecha_inicio = df_terreno['Dias'].min()
                        fecha_fin = df_terreno['Dias'].max()
                    else: # con zoom
                        # --- CORRECCIÓN SQL SERVER ---
                        val_min_tiempo = df_terreno['Dias'].min()
                        if isinstance(val_min_tiempo, str):
                            fechainiproyecto = datetime.strptime(val_min_tiempo, '%Y-%m-%d %H:%M:%S')
                        else:
                            fechainiproyecto = val_min_tiempo
                        # ----------------------------
                        unidtiempo = 1
                        difdiasini = fecha_inicio - fechainiproyecto
                        fecha_inicio = difdiasini.days * unidtiempo
                        difdiasfin = fecha_fin - fechainiproyecto
                        fecha_fin = difdiasfin.days * unidtiempo
            else:
                tipoterre = "Horas"
                if data is None:
                    if fecha_inicio is None:
                        fecha_inicio = df_terreno['Horas'].min()
                        fecha_fin = df_terreno['Horas'].max()
                    else: # con zoom
                        # --- CORRECCIÓN SQL SERVER ---
                        val_min_tiempo = df_terreno['Horas'].min()
                        if isinstance(val_min_tiempo, str):
                            fechainiproyecto = datetime.strptime(val_min_tiempo, '%Y-%m-%d %H:%M:%S')
                        else:
                            fechainiproyecto = val_min_tiempo
                        # ----------------------------
                        unidtiempo = 24
                        difdiasini = fecha_inicio - fechainiproyecto
                        fecha_inicio = difdiasini.days * unidtiempo
                        difdiasfin = fecha_fin - fechainiproyecto
                        fecha_fin = difdiasfin.days * unidtiempo
            for idinstruterre, datos_terreno in df_terreno.groupby('Codigo'):
                nombreterre = str(datos_terreno['Nombre'].iloc[0])
                estilo = ConfiguracionController.ctrlTraerEstiloEquipoGrafica(idproyecto, idinstruterre, 0)
                if estilo:
                    linea, = ax.plot(datos_terreno[tipoterre], datos_terreno['Lectura'], linestyle=estilo[3], linewidth=estilo[4], color=estilo[5], label=nombreterre)
                else:
                    linea, = ax.plot(datos_terreno[tipoterre], datos_terreno['Lectura'], label=nombreterre)
                lineas.append(linea)
    # Configuración de ejes y etiquetas
    ax.set_title(titulo, fontsize=titulozise)
    ax.set_xlabel(labelejex, fontsize=ejezise)
    ax.set_ylabel(labelejey, fontsize=ejezise)
    if tiempo == "FECHA":
        ax.xaxis.set_major_formatter(DateFormatter('%d/%m/%Y'))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda val, pos: '{:.{}f}'.format(val, decimales)))
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)

    # -----------------------------------------------------------------------------
    # MEJORA VISUAL: CÁLCULO DE ETIQUETAS SIMÉTRICAS (LINSPACE)
    # -----------------------------------------------------------------------------
    if tiempo == "FECHA":
        # Convertimos fechas a números de matplotlib
        num_inicio = mdates.date2num(fecha_inicio)
        num_fin = mdates.date2num(fecha_fin)
        rango_total = num_fin - num_inicio
        intervalo_num = intervalo_dias 
    else:
        # Ya son números (Días u Horas)
        num_inicio = float(fecha_inicio)
        num_fin = float(fecha_fin)
        rango_total = num_fin - num_inicio
        intervalo_num = intervalo_dias

    # Calcular cantidad de etiquetas basada en el intervalo
    if intervalo_num <= 0:
        num_etiquetas = 10
    else:
        num_etiquetas = int(rango_total / intervalo_num) + 1

    # Protección de saturación: Limitar a 15-20 etiquetas para que se vean bien
    if num_etiquetas > 25: 
        avisolabels = True
        num_etiquetas = 15 # Forzar visualización limpia
    elif num_etiquetas < 2:
        num_etiquetas = 2

    # Generación de puntos matemáticamente equidistantes (Simetría)
    etiquetas_numericas = np.linspace(num_inicio, num_fin, num_etiquetas)
    ax.set_xticks(etiquetas_numericas)
    ax.set_xlim([num_inicio, num_fin])
    # -----------------------------------------------------------------------------
    
    plt.setp(ax.get_xticklabels(), rotation=90, ha="center", fontsize=etiquesize)
    plt.setp(ax.get_yticklabels(), fontsize=etiquesize)
    if mostrarlluvia == 0: # siempre visible
        if tiempo == "FECHA":
            if modulo == "PIEZOMETROS":
                plt.setp(ax2.get_yticklabels(), fontsize=etiquesize)
    else:
        if tiempo == "FECHA":
            if pluviometro_data:
                plt.setp(ax2.get_yticklabels(), fontsize=etiquesize)
    # CONFIGURAR EJE Y
    if ejeymin != 0 or ejeymax != 0:
        ax.set_ylim(ejeymin * medida, ejeymax * medida)
        # Calcula los intervalos primarios
        maxejey = (ejeymax * medida) + 0.0001
        if ejeyprin > 0:
            tick_primarios = np.arange(ejeymin * medida, maxejey, ejeyprin * medida)
            if len(tick_primarios) > 1 and len(tick_primarios) < 100:
                ax.set_yticks(tick_primarios)
            else:
                avisolabels = True
        # Calcula los intervalos secundarios
        if ejeysecu > 0:
            tick_secundarios = np.arange(ejeymin * medida, maxejey, ejeysecu * medida)
            if len(tick_secundarios) > 1 and len(tick_secundarios) < 200:
                for tick in tick_secundarios:
                    ax.axhline(y=tick, color='gray', linestyle='--', linewidth=0.5)
            else:
                avisolabels = True
    
    # Configuración de leyenda paginada
    def calculate_columns():
        font_config = {'family': fuente, 'size': leyendazise, 'weight': 'normal'}
        renderer = canvas.get_renderer()

        # Obtener los manejadores y etiquetas de la leyenda
        leyenda_labels = [line.get_label() for line in lineas] + (["Precipitación"] if barras_pluviometro else [])

        # Calcular el ancho máximo de las etiquetas
        max_width = 0
        for label in leyenda_labels:
            text_obj = ax.text(0, 0, label, fontproperties=font_config)
            width = text_obj.get_window_extent(renderer).width +(leyendazise*3)
            max_width = max(max_width, width)
            text_obj.remove()  # Eliminar el objeto de texto para no mostrarlo en el gráfico

        ancho_pantalla = widget.width()

        return max(1, int((ancho_pantalla - 100) / (max_width + 50)))

    def actualizar_leyenda():
        try:
            ncols = calculate_columns()
            # Crear listas de manejadores y etiquetas para la leyenda
            leyenda_elementos = lineas + ([barras_pluviometro] if barras_pluviometro else [])
            leyenda_labels = [line.get_label() for line in lineas] + (["Precipitación"] if barras_pluviometro else [])
            legend = ax.legend(handles=leyenda_elementos, labels=leyenda_labels, loc='upper center', bbox_to_anchor=(0.5, 0), ncol=ncols, frameon=False, fontsize=leyendazise, borderaxespad=0.8)
            renderer = canvas.get_renderer()
            canvas.draw()
            fig_bbox = figure.bbox
            legend_bbox = legend.get_window_extent(renderer)
            legend_height = legend_bbox.height / fig_bbox.height
            padding = 0.08
            bottom_margin = 0.20 + legend_height + padding
            top_margin = 0.95 - (legend_height * 0.3)
            if bottom_margin >= top_margin:
                bottom_margin = 0.25
                top_margin = 0.90
                if ncols == 1:
                    bottom_margin = 0.35
                    top_margin = 0.85

            figure.subplots_adjust(bottom=bottom_margin, top=top_margin, left=0.1, right=0.90)
            canvas.draw()
            if figure.subplotpars.bottom >= figure.subplotpars.top:
                raise ValueError("Margen inválido, aplicando valores seguros")
            xlabel_bbox = ax.xaxis.label.get_window_extent(renderer=renderer)
            xlabel_bottom = xlabel_bbox.transformed(ax.transAxes.inverted()).y0
            legend.set_bbox_to_anchor((0.5, xlabel_bottom))
        except Exception as e:
            figure.subplots_adjust(bottom=0.25, top=0.90, left=0.1, right=0.90)
            ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=2, fontsize=8)
            canvas.draw()
    def on_resize(event):
        actualizar_leyenda()
        
    def procesar_datos_lectura_piezo_celda(id_proyecto,label,id_equipo, date, reading, tipo_piezo,modulo):
        # Convertir la fecha al formato yyyy-mm-dd hh:mm:ss para la consola
        date_obj = datetime.strptime(date, '%d/%m/%Y %H:%M:%S')
        formatted_date= date_obj.strftime('%Y-%m-%d %H:%M:%S')

        dialog = ModalDialog(widget,label, date, reading)
        result = dialog.exec()

        if result == QDialog.Accepted:
            respuesta=None
            if modulo == "PIEZOMETROS":
                respuesta=PiezometroController.ctrlOmitirLecturaPiezometro(id_proyecto,id_equipo,formatted_date,tipo_piezo)
                if respuesta:
                    print(f"{label}\nFecha: {formatted_date}\nLectura: {reading}\nTipo: {tipo_piezo}")
                else:
                    print('error al omitir lectura de piezometros')
            else:
                respuesta=CeldaController.ctrlOmitirLecturaCelda(id_proyecto,id_equipo,formatted_date)
                if respuesta:
                    print(f"{label}\nFecha: {formatted_date}\nLectura: {reading}\nTipo: {tipo_piezo}")
                else:
                    print('error al omitir de celdas')

    def on_click(event):
        # Determinar el eje y las anotaciones a usar
        if ax2:
            current_ax = ax2
        else:
            current_ax = ax

        # Verificar si el clic está dentro de los límites de los ejes
        if current_ax and current_ax.in_axes(event) and event.xdata is not None and event.ydata is not None:
            for line in lineas:
                contains, _ = line.contains(event)
                if contains:
                    label = line.get_label()
                    x = mdates.num2date(event.xdata)  # Convertir x a objeto datetime
                    x = x.replace(tzinfo=None)  # Asegurarse de que x no tenga información de zona horaria
                    y = event.ydata

                    # Filtrar los datos para obtener solo los puntos correspondientes a la línea clickeada
                    line_data = df[df['Equipo'] == label]

                    # Verificar si line_data está vacío
                    if line_data.empty:
                        # Si está vacío, mostrar la anotación en el punto donde se hizo clic
                        date = x.strftime('%d/%m/%Y %H:%M:%S')  # Formatear la fecha como dd/mm/yyyy hh:mm:ss
                        reading = round(y, 3)  # Redondear la lectura a 3 decimales
                        annotation_text = f"{label}\nFecha: {date}\nLectura: {reading}"
                    else:
                        # Asegurarse de que la columna 'Fecha' no tenga información de zona horaria
                        if line_data['Fecha'].dt.tz is not None:
                            line_data['Fecha'] = line_data['Fecha'].dt.tz_localize(None)

                        # Encontrar el punto de datos más cercano al evento de clic en la línea específica
                        data_point = line_data.iloc[(line_data['Fecha'] - x).abs().argmin()]
                        closest_x = data_point['Fecha']
                        closest_y = data_point[tipo]
                        date = closest_x.strftime('%d/%m/%Y %H:%M:%S')  # Formatear la fecha como dd/mm/yyyy hh:mm:ss
                        reading = round(closest_y, 3)  # Redondear la lectura a 3 decimales
                        tipo_piezo = data_point['TipoPiezo']  # Obtener el valor de la columna 'TipoPrisma'
                        id_equipo= data_point['idEquipo']
                        annotation_text = f"{label}\nFecha: {date}\nLectura: {reading}"

                    # Si se presiona el botón derecho del mouse (anticlick)
                    if event.button == 3:
                        # Ocultar anotaciones anteriores si existen
                        for text in current_ax.texts:
                            text.set_visible(False)

                        # Crear y mostrar la anotación en el punto más cercano o en el punto de clic
                        annotation = current_ax.annotate(annotation_text, (x, y),
                                                        textcoords="offset points", xytext=(10, 10),
                                                        ha='left', fontsize=etiquesize,
                                                        bbox=dict(facecolor='yellow', alpha=0.8, edgecolor='none'))
                        annotation.set_visible(True)
                        canvas.draw()
                        break  # Salir del bucle una vez que se haya encontrado una línea

        # Si se presiona el botón izquierdo del mouse (click) en cualquier lugar
        if event.button == 1:
            # Verificar si la tecla Control está presionada
            if event.guiEvent.modifiers() & Qt.ControlModifier:
                # Llamar al método para procesar los datos
                procesar_datos_lectura_piezo_celda(idproyecto,label,id_equipo, date, reading, tipo_piezo,modulo)
            else:
                # Ocultar todas las anotaciones existentes
                for text in current_ax.texts:
                    text.set_visible(False)
                canvas.draw()
                
    canvas.mpl_connect('resize_event', on_resize)
    canvas.mpl_connect('button_press_event', on_click)
    actualizar_leyenda()
    plt.close(figure)
    if avisolabels:
        mostrar_mensaje("Ejes", "No se aplicó la configuración de ejes.", "advertencia")

def procesar_grafica_analisis(widget, data, idx_nombre, idx_fecha, idx_lectura, labelejex, labelejey, titulo, tiempo, tipo, idproyecto, fecha_inicio=None, fecha_fin=None):
    avisolabels = False
    
    # --- CORRECCIÓN SQL SERVER: Validar tipo de dato antes de convertir ---
    if tiempo == "FECHA":
        if fecha_inicio:
            if isinstance(fecha_inicio, str):
                fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d %H:%M:%S')
        if fecha_fin:
            if isinstance(fecha_fin, str):
                fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d %H:%M:%S')
    # ----------------------------------------------------------------------
    
    # Convertir fechas a datetime y asignar valores por defecto
    df = pd.DataFrame(data, columns=['col_' + str(i) for i in range(len(data[0]))])
    df = df[[df.columns[0], df.columns[idx_nombre], df.columns[idx_fecha], df.columns[idx_lectura]]]
    df.columns = ['Instrumento', 'Nombre', 'Fecha', tipo]
    # validar formato filtrado
    if tiempo == "FECHA":
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        if fecha_inicio is None:
            fecha_inicio = df['Fecha'].min()
            fecha_fin = df['Fecha'].max()
        fecha_inicio = pd.to_datetime(fecha_inicio)
        fecha_fin = pd.to_datetime(fecha_fin)
    else:
        fecha_inicio = df['Fecha'].min()
        fecha_fin = df['Fecha'].max()
    # Ajustar limites de gráficas eje y
    ejeymin, ejeymax, ejeyprin, ejeysecu, intervalo_dias = 0, 0, 0, 0, 0
    dataeje = ConfiguracionController.ctrlObtenerConfiguracionEje(idproyecto, "ANALISIS", tipo)
    if dataeje:
        ejeymin, ejeymax, ejeyprin, ejeysecu = dataeje[4], dataeje[5], dataeje[6], dataeje[7]
        intervalo_dias = dataeje[8]
    if tiempo == "FECHA":
        total_dias = (fecha_fin - fecha_inicio).days
    else:
        total_dias = (fecha_fin - fecha_inicio)
    if intervalo_dias == 0:
        intervalo_dias = total_dias / 10
    # Limpiar el widget
    limpiar_widget(widget)
    # crear figura
    config = SoftwareConfiguracion.obtenerDataSoftware()
    titulozise, ejezise, etiquesize, leyendazise = config[0], config[1], config[2], config[3]
    vertices, fuente, grosorlinea, grosorvertice, decimales = config[6], config[10], config[12], config[13], config[14]
    
    figure, ax = plt.subplots()
    canvas = FigureCanvas(figure)
    plt.rcParams['font.family'] = fuente
    layout = widget.layout()
    layout.addWidget(canvas)
    toolbar_layout = QHBoxLayout()
    widget.toolbar = CustomToolbar(canvas, widget)
    toolbar_layout.addWidget(widget.toolbar)
    layout.addLayout(toolbar_layout)
    # Graficar datos de desplazamiento
    lineas = []
    if tiempo != "FECHA":
        punto_inicial = ax.scatter([], [], color='black', label='Punto Inicial', zorder=11, s=50, edgecolors='white', linewidths=0.6)
        punto_final = ax.scatter([], [], color='red', label='Punto Final', zorder=11, s=50, edgecolors='white', linewidths=0.6)
        lineas.append(punto_inicial)
        lineas.append(punto_final)
    for idinstrumento, datos_equipo in df.groupby('Instrumento'):
        nombreequipo = str(datos_equipo['Nombre'].iloc[0])
        # Graficar todos los puntos intermedios en azul
        estilo = ConfiguracionController.ctrlTraerEstiloEquipoGrafica(idproyecto, idinstrumento, 0)
        if estilo:
            if vertices == 1:
                linea, = ax.plot(datos_equipo['Fecha'], datos_equipo[tipo], marker='o', markersize=estilo[4] + 4, linestyle=estilo[3], linewidth=estilo[4], color=estilo[5], label=nombreequipo)
            else:
                linea, = ax.plot(datos_equipo['Fecha'], datos_equipo[tipo], linestyle=estilo[3], linewidth=estilo[4], color=estilo[5], label=nombreequipo)
        else:
            if vertices == 1:
                linea, = ax.plot(datos_equipo['Fecha'], datos_equipo[tipo], marker='o', markersize=grosorvertice, linewidth=grosorlinea, linestyle='-', label=nombreequipo)
            else:
                linea, = ax.plot(datos_equipo['Fecha'], datos_equipo[tipo], linewidth=grosorlinea, linestyle='-', label=nombreequipo)
        lineas.append(linea)
        # Resaltar el primer y Punto Final
        if tiempo != "FECHA":
            ax.scatter([datos_equipo['Fecha'].iloc[0]], [datos_equipo[tipo].iloc[0]], color='black', label='Punto Inicial', zorder=11, s=50,
                    edgecolors='white', linewidths=0.6)
            ax.scatter([datos_equipo['Fecha'].iloc[-1]], [datos_equipo[tipo].iloc[-1]], color='red', label='Punto Final', zorder=11, s=50,
                    edgecolors='white', linewidths=0.6)
    # Configuración de ejes y etiquetas
    ax.set_title(titulo, fontsize=titulozise)
    ax.set_xlabel(labelejex, fontsize=ejezise)
    ax.set_ylabel(labelejey, fontsize=ejezise)
    if tiempo == "FECHA":
        ax.xaxis.set_major_formatter(DateFormatter('%d/%m/%Y'))
    if tipo == "VEN":
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda val, pos: '{:.{}f}'.format(val, decimales)))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda val, pos: '{:.{}f}'.format(val, decimales)))
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)

    # -----------------------------------------------------------------------------
    # MEJORA VISUAL: CÁLCULO DE ETIQUETAS SIMÉTRICAS (ANÁLISIS)
    # -----------------------------------------------------------------------------
    if tiempo == "FECHA":
        num_inicio = mdates.date2num(fecha_inicio)
        num_fin = mdates.date2num(fecha_fin)
        rango_total = num_fin - num_inicio
        intervalo_num = intervalo_dias
    else:
        num_inicio = float(fecha_inicio)
        num_fin = float(fecha_fin)
        rango_total = num_fin - num_inicio
        intervalo_num = intervalo_dias

    if intervalo_num <= 0:
        num_etiquetas = 10
    else:
        num_etiquetas = int(rango_total / intervalo_num) + 1

    if num_etiquetas > 25:
        avisolabels = True
        num_etiquetas = 15
    elif num_etiquetas < 2:
        num_etiquetas = 2

    etiquetas_numericas = np.linspace(num_inicio, num_fin, num_etiquetas)
    ax.set_xticks(etiquetas_numericas)
    ax.set_xlim([num_inicio, num_fin])
    # -----------------------------------------------------------------------------

    # ajustar las etiquetas
    plt.setp(ax.get_xticklabels(), rotation=90, ha="center", fontsize=etiquesize)
    plt.setp(ax.get_yticklabels(), fontsize=etiquesize)
    # CONFIGURAR EJE Y
    if ejeymin != 0 or ejeymax != 0:
        ax.set_ylim(ejeymin, ejeymax)
        # Calcula los intervalos primarios
        maxejey = ejeymax + 0.0001
        if ejeyprin > 0:
            tick_primarios = np.arange(ejeymin, maxejey, ejeyprin)
            if len(tick_primarios) > 1 and len(tick_primarios) < 100:
                ax.set_yticks(tick_primarios)
            else:
                avisolabels = True
        # Calcula los intervalos secundarios
        if ejeysecu > 0:
            tick_secundarios = np.arange(ejeymin, maxejey, ejeysecu)
            if len(tick_secundarios) > 1 and len(tick_secundarios) < 200:
                for tick in tick_secundarios:
                    ax.axhline(y=tick, color='gray', linestyle='--', linewidth=0.5)
            else:
                avisolabels = True
    # Configuración de leyenda paginada
    def calculate_columns():
        font_config = {'family': fuente, 'size': leyendazise, 'weight': 'normal'}
        renderer = canvas.get_renderer()
        # Obtener los manejadores y etiquetas de la leyenda
        leyenda_labels = [line.get_label() for line in lineas]
        # Calcular el ancho máximo de las etiquetas
        max_width = 0
        for label in leyenda_labels:
            text_obj = ax.text(0, 0, label, fontproperties=font_config)
            width = text_obj.get_window_extent(renderer).width +(leyendazise*3)
            max_width = max(max_width, width)
            text_obj.remove()  # Eliminar el objeto de texto para no mostrarlo en el gráfico

        ancho_pantalla = widget.width()

        return max(1, int((ancho_pantalla - 100) / (max_width + 50)))
    
    def actualizar_leyenda():
        try:
            ncols = calculate_columns()
            leyenda_labels = [line.get_label() for line in lineas]
            legend = ax.legend(handles=lineas, labels=leyenda_labels, loc='upper center', bbox_to_anchor=(0.5, 0), ncol=ncols, frameon=False, fontsize=leyendazise, borderaxespad=0.8)
            renderer = canvas.get_renderer()
            canvas.draw()
            fig_bbox = figure.bbox
            legend_bbox = legend.get_window_extent(renderer)
            legend_height = legend_bbox.height / fig_bbox.height
            padding = 0.08
            bottom_margin = 0.20 + legend_height + padding
            top_margin = 0.95 - (legend_height * 0.3)

            if bottom_margin >= top_margin:
                bottom_margin = 0.25
                top_margin = 0.90
                if ncols == 1:
                    bottom_margin = 0.35
                    top_margin = 0.85

            figure.subplots_adjust(bottom=bottom_margin, top=top_margin, left=0.15, right=0.90)
            canvas.draw()
            if figure.subplotpars.bottom >= figure.subplotpars.top:
                raise ValueError("Margen inválido, aplicando valores seguros")
            xlabel_bbox = ax.xaxis.label.get_window_extent(renderer=renderer)
            xlabel_bottom = xlabel_bbox.transformed(ax.transAxes.inverted()).y0
            legend.set_bbox_to_anchor((0.5, xlabel_bottom))
        except Exception as e:
            figure.subplots_adjust(bottom=0.25, top=0.90, left=0.15, right=0.90)
            ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=2, fontsize=8)
            canvas.draw()

    def on_resize(event):
        actualizar_leyenda()
        
    canvas.mpl_connect('resize_event', on_resize)
    actualizar_leyenda()
    plt.close(figure)
    if avisolabels:
        mostrar_mensaje("Ejes", "No se aplicó la configuración de ejes.", "advertencia")

def procesar_grafica_histograma(widget, data, intervalos, nombreequipo, idx_lectura, labelejex, labelejey, titulo):
    # Convertir fechas a datetime y asignar valores por defecto
    df = pd.DataFrame(data, columns=['col_' + str(i) for i in range(len(data[0]))])
    df = df[[df.columns[idx_lectura]]]
    df.columns = ['Lectura']
    # Limpiar el widget
    limpiar_widget(widget)
    config = SoftwareConfiguracion.obtenerDataSoftware()
    titulozise, ejezise, etiquesize, leyendazise, fuente = config[0], config[1], config[2], config[3], config[10]
    # crear figura
    figure, ax = plt.subplots()
    canvas = FigureCanvas(figure)
    plt.rcParams['font.family'] = fuente
    layout = widget.layout()
    layout.addWidget(canvas)
    toolbar_layout = QHBoxLayout()
    widget.toolbar = CustomToolbar(canvas, widget)
    toolbar_layout.addWidget(widget.toolbar)
    layout.addLayout(toolbar_layout)
    # Graficar datos de desplazamiento
    ax.hist(df['Lectura'], bins=intervalos, edgecolor='black', alpha=0.5, label=nombreequipo)
    # Configuración de ejes y etiquetas
    ax.set_title(titulo, fontsize=titulozise)
    ax.set_xlabel(labelejex, fontsize=ejezise)
    ax.set_ylabel(labelejey, fontsize=ejezise)
    ax.grid(False)
    # validar las etiquetas
    plt.setp(ax.get_xticklabels(), fontsize=etiquesize)
    plt.setp(ax.get_yticklabels(), fontsize=etiquesize)
    # Configuración de leyenda
    ax.legend(fontsize=leyendazise)
    #ax.legend(loc='upper center', bbox_to_anchor=(1, 0.5), prop={'size': leyendazise})
    figure.subplots_adjust(left=0.08, right=0.95, top=0.95, bottom=0.25)
    canvas.draw_idle()
    plt.close(figure)