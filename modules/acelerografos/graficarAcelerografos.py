import pandas as pd
import gc
import numpy as np
import matplotlib.pyplot as plt
import math
from datetime import timedelta
from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from utils.common.customToolbar import CustomToolbar 
from matplotlib.dates import DateFormatter
from utils.common.alertas import mostrar_mensaje
from controllers.ConfiguracionController import ConfiguracionController
from modules.empresa.softwareconfiguracion import SoftwareConfiguracion
from controllers.AcelerografoController import AcelerografoController

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
    
def procesar_grafica_acelerografos(widget, idproyecto, data, fecha_inicio=None, fecha_fin=None):
    avisolabels = False
    # Convertir data a DataFrame
    df = pd.DataFrame(data, columns=['id_componente', 'nombre_acelerografo', 'fecha_hora', 'magnitud', 'distancia'])
    df['fecha_hora'] = pd.to_datetime(df['fecha_hora'])
    
    # Definir fechas de inicio y fin si no están especificadas
    if fecha_inicio is None:
        fecha_inicio = df['fecha_hora'].min()
    else:
        fecha_inicio = pd.to_datetime(fecha_inicio)
    
    if fecha_fin is None:
        fecha_fin = df['fecha_hora'].max()
    else:
        fecha_fin = pd.to_datetime(fecha_fin)
    
    # Ajustar limites de gráficas eje y
    ejeymin, ejeymax, ejeyprin, ejeysecu, intervalo_dias = 0, 0, 0, 0, 0
    dataeje = ConfiguracionController.ctrlObtenerConfiguracionEje(idproyecto, "ACELEROGRAFOS", "AMA")
    if dataeje:
        ejeymin, ejeymax, ejeyprin, ejeysecu, intervalo_dias = dataeje[4], dataeje[5], dataeje[6], dataeje[7], dataeje[8]
    total_dias = (fecha_fin - fecha_inicio).days
    if intervalo_dias == 0:
        intervalo_dias = total_dias / 10
    # Configurar el layout y limpiar el anterior
    limpiar_widget(widget)
    # Configuración de la gráfica
    config = SoftwareConfiguracion.obtenerDataSoftware()
    titulozise, ejezise, etiquesize, leyendazise, fuente = config[0], config[1], config[2], config[3], config[10]
    decimales = config[14]
    # Ajustar el tamaño de la figura al tamaño del widget
    dpi = widget.logicalDpiX()
    # Modifica estas líneas para asegurar un tamaño mínimo
    fig_width = max(widget.width() / dpi, 6)  # Mínimo 6 pulgadas
    fig_height = max(widget.height() / dpi, 4)  # Mínimo 4 pulgadas
    figure, ax = plt.subplots(figsize=(fig_width, fig_height))
    canvas = FigureCanvas(figure)
    plt.rcParams['font.family'] = fuente
    layout = widget.layout()
    layout.addWidget(canvas)
    toolbar_layout = QHBoxLayout()
    widget.toolbar = CustomToolbar(canvas, widget)
    toolbar_layout.addWidget(widget.toolbar)
    layout.addLayout(toolbar_layout)
    
    # Graficar puntos de colores según la magnitud y el color
    umbralesleyenda = []
    for idcompo, datos in df.groupby('id_componente'):
        umbrales = AcelerografoController.ctrlObtenerUmbralesAcelerografoComponente(idproyecto, idcompo, "AMA")
        if umbrales:
            umbralesleyenda = umbrales
            colores = []
            for magni, dista in zip(datos['magnitud'], datos['distancia']):
                color = "gray"
                for umbral in umbrales:
                    if magni > umbral[7] and dista < umbral[6]:
                        color = umbral[4]
                        break
                colores.append(color)
            ax.scatter(datos['fecha_hora'], datos['magnitud'], label=colores, color=colores, s=50, alpha=0.7)
        else:
            colores = []
            for magni, dista in zip(datos['magnitud'], datos['distancia']):
                color = "gray"
                if magni > 5 and dista < 200:
                    color = "green"
                elif magni > 6 and dista < 200:
                    color = "orange"
                elif magni > 7 and dista < 100:
                    color = "red"
                colores.append(color)
            ax.scatter(datos['fecha_hora'], datos['magnitud'], label=colores, color=colores, s=50, alpha=0.7)
    # Configuración de ejes y etiquetas
    
    ax.set_title('Magnitud de Acelerógrafos', fontsize=titulozise)
    ax.set_xlabel('Fecha', fontsize=ejezise)
    ax.set_ylabel('Magnitud', fontsize=ejezise)
    ax.xaxis.set_major_formatter(DateFormatter('%d/%m/%Y'))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda val, pos: '{:.{}f}'.format(val, decimales)))
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)
    # método de calculo automático de etiquetas
    def calcular_intervalo_automatico(total):
        if total <= 0:
            return 1
        if total <= 10:
            return max(1, total / 5)
        elif total <= 30:
            return max(2, total / 7)
        elif total <= 100:
            return max(5, total / 10)
        elif total <= 365:
            return max(15, total / 12)
        else:
            return max(30, total / 15)
    # Configuración personalizada del rango de fechas en el eje x para incluir inicio y fin
    intervalos_exactos = total_dias / intervalo_dias
    num_etiquetas = math.ceil(intervalos_exactos) + 1
    if num_etiquetas > 200:
        avisolabels = True
        num_etiquetas = int(calcular_intervalo_automatico(total_dias)) + 1
    intervalo_real = total_dias / (num_etiquetas - 1)
    etiquetas = []
    for i in range(num_etiquetas):
        dias_a_sumar = i * intervalo_real
        fecha_etiqueta = fecha_inicio + timedelta(days=dias_a_sumar)
        if i == num_etiquetas - 1:
            etiquetas.append(fecha_fin)
        else:
            etiquetas.append(fecha_etiqueta)
    ax.set_xticks(etiquetas)
    ax.set_xlim([etiquetas[0], etiquetas[-1]])
    # ajustar eje
    plt.setp(ax.get_xticklabels(), rotation=90, ha="center", fontsize=etiquesize)
    plt.setp(ax.get_yticklabels(), fontsize=etiquesize)
    # CONFIGURAR EJE Y
    if ejeymin != 0 or ejeymax != 0:
        ax.set_ylim(ejeymin, ejeymax)
        # Calcula los intervalos primarios
        maxejey = (ejeymax) + 0.0001
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
    # Leyenda para los diferentes niveles de alerta por color
    if umbralesleyenda:
        custom_legend = []
        if len(umbralesleyenda) < 4:
            for umbral in umbralesleyenda:
                custom_legend.append(plt.Line2D([0], [0], marker='o', color='w', label=f'{umbral[3]} (M>{umbral[7]} y dentro {umbral[6]} Km)', markerfacecolor=umbral[4], markersize=10))
            custom_legend.append(plt.Line2D([0], [0], marker='o', color='w', label=f'Sin Alerta (M<{umbralesleyenda[0][7]} o mayor {umbralesleyenda[-1][6]} Km)', markerfacecolor='gray', markersize=10))
        else:
            custom_legend = [
                plt.Line2D([0], [0], marker='o', color='w', label=f'Alerta 1 (M>{7} y dentro 200 Km)', markerfacecolor='red', markersize=10),
                plt.Line2D([0], [0], marker='o', color='w', label=f'Alerta 2 (M>{6}  y dentro 200 Km)', markerfacecolor='orange', markersize=10),
                plt.Line2D([0], [0], marker='o', color='w', label=f'Alerta 3 (M>{5} y dentro 100 Km)', markerfacecolor='green', markersize=10),
                plt.Line2D([0], [0], marker='o', color='w', label=f'Sin Alerta (M<{5} o mayor 200 Km)', markerfacecolor='gray', markersize=10)
            ]
    else:
        custom_legend = [
            plt.Line2D([0], [0], marker='o', color='w', label=f'Alerta 1 (M>{7} y dentro 200 Km)', markerfacecolor='red', markersize=10),
            plt.Line2D([0], [0], marker='o', color='w', label=f'Alerta 2 (M>{6}  y dentro 200 Km)', markerfacecolor='orange', markersize=10),
            plt.Line2D([0], [0], marker='o', color='w', label=f'Alerta 3 (M>{5} y dentro 100 Km)', markerfacecolor='green', markersize=10),
            plt.Line2D([0], [0], marker='o', color='w', label=f'Sin Alerta (M<{5} o mayor 200 Km)', markerfacecolor='gray', markersize=10)
        ]
    
    renderer = canvas.get_renderer()
    canvas.draw()

    # Obtener la posición del eje x en coordenadas de la figura
    xlabel_bbox = ax.xaxis.label.get_window_extent(renderer=renderer)
    xlabel_bottom = xlabel_bbox.transformed(ax.transAxes.inverted()).y0

    # Ajustar la posición de la leyenda en función del tamaño de la pantalla
    if widget.height() < 600:
        bbox_to_anchor = (0.5, xlabel_bottom - 0.15)
    else:
        bbox_to_anchor = (0.5, xlabel_bottom - 0.1)
    ax.legend(handles=custom_legend, loc='upper center', bbox_to_anchor=bbox_to_anchor, ncol=4, frameon=False, fontsize=leyendazise)
    figure.subplots_adjust(left=0.08, right=0.95, top=0.95, bottom=0.35)
    canvas.draw()
    canvas.draw_idle()
    plt.close(figure)
    if avisolabels:
        mostrar_mensaje("Ejes", "No se aplicó la configuración de ejes.", "advertencia")
