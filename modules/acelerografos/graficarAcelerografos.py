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
from matplotlib.transforms import Bbox
from utils.shared.graficaDesplazamientoVelocidad import construir_leyenda_flujo, configurar_evento_leyenda_flujo
from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel)


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
    label_total_puntos = QLabel("Total: 0")
    label_total_puntos.setStyleSheet("font-size: 12px; margin-left: 8px; font-weight: bold; color: #333;")
    toolbar_layout.addWidget(label_total_puntos)
    widget.label_total_puntos = label_total_puntos
    layout.addLayout(toolbar_layout)
    
    # Graficar puntos de colores según la magnitud y el color
        # Graficar puntos de colores según la magnitud y el color
    umbralesleyenda = []
    lineas_principales = []
    puntos_por_componente = []

    for idcompo, datos in df.groupby('id_componente'):
        nombre_acel = str(datos['nombre_acelerografo'].iloc[0])   # <-- NUEVO
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

        # --- CAMBIO: ya no pasamos label=colores, y guardamos el scatter ---
        scatter_obj = ax.scatter(datos['fecha_hora'], datos['magnitud'],
                                  color=colores, s=50, alpha=0.7, label='_nolegend_')

        # --- NUEVO: proxy invisible que representa a este acelerógrafo en la leyenda ---
        proxy, = ax.plot([], [], linestyle='none', marker='o', color='dimgray',
                          label=nombre_acel, alpha=0)
        proxy._asociados = [scatter_obj]   # al ocultar el proxy, se oculta el scatter real
        lineas_principales.append(proxy)

        puntos_por_componente.append((proxy, scatter_obj, len(datos)))
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
        # =====================================================================
    # NUEVO: dibuja la leyenda de niveles de alerta (fija) + la leyenda de
    # acelerógrafos clickeable con Total/Activas/Ocultas, y ajusta márgenes.
    # =====================================================================
    def actualizar_leyenda():
        try:
            actualizar_contador_puntos()
            # --- Leyenda de niveles de alerta (fija, informativa) ---
            if hasattr(ax, '_leyenda_alerta') and ax._leyenda_alerta is not None:
                ax._leyenda_alerta.remove()

            if umbralesleyenda:
                custom_legend = []
                if len(umbralesleyenda) < 4:
                    for umbral in umbralesleyenda:
                        custom_legend.append(plt.Line2D(
                            [0], [0], marker='o', color='w',
                            label=f'{umbral[3]} (M>{umbral[7]} y dentro {umbral[6]} Km)',
                            markerfacecolor=umbral[4], markersize=10))
                    custom_legend.append(plt.Line2D(
                        [0], [0], marker='o', color='w',
                        label=f'Sin Alerta (M<{umbralesleyenda[0][7]} o mayor {umbralesleyenda[-1][6]} Km)',
                        markerfacecolor='gray', markersize=10))
                else:
                    custom_legend = [
                        plt.Line2D([0], [0], marker='o', color='w', label='Alerta 1 (M>7 y dentro 200 Km)', markerfacecolor='red', markersize=10),
                        plt.Line2D([0], [0], marker='o', color='w', label='Alerta 2 (M>6 y dentro 200 Km)', markerfacecolor='orange', markersize=10),
                        plt.Line2D([0], [0], marker='o', color='w', label='Alerta 3 (M>5 y dentro 100 Km)', markerfacecolor='green', markersize=10),
                        plt.Line2D([0], [0], marker='o', color='w', label='Sin Alerta (M<5 o mayor 200 Km)', markerfacecolor='gray', markersize=10),
                    ]
            else:
                custom_legend = [
                    plt.Line2D([0], [0], marker='o', color='w', label='Alerta 1 (M>7 y dentro 200 Km)', markerfacecolor='red', markersize=10),
                    plt.Line2D([0], [0], marker='o', color='w', label='Alerta 2 (M>6 y dentro 200 Km)', markerfacecolor='orange', markersize=10),
                    plt.Line2D([0], [0], marker='o', color='w', label='Alerta 3 (M>5 y dentro 100 Km)', markerfacecolor='green', markersize=10),
                    plt.Line2D([0], [0], marker='o', color='w', label='Sin Alerta (M<5 o mayor 200 Km)', markerfacecolor='gray', markersize=10),
                ]

            canvas.draw()
            renderer = canvas.get_renderer()
            xlabel_bbox = ax.xaxis.label.get_window_extent(renderer=renderer)
            xlabel_bottom = xlabel_bbox.transformed(ax.transAxes.inverted()).y0

            offset_alerta = xlabel_bottom - (0.15 if widget.height() < 600 else 0.10)

            leyenda_alerta = ax.legend(handles=custom_legend, loc='upper center',
                                        bbox_to_anchor=(0.5, offset_alerta), ncol=4,
                                        frameon=False, fontsize=leyendazise)
            ax.add_artist(leyenda_alerta)
            ax._leyenda_alerta = leyenda_alerta

            canvas.draw()
            alerta_bbox = leyenda_alerta.get_window_extent(renderer)
            fig_bbox = figure.bbox
            alerta_height = alerta_bbox.height / fig_bbox.height
            alerta_bottom_axes = alerta_bbox.transformed(ax.transAxes.inverted()).y0

            # --- Leyenda de acelerógrafos (clickeable + Total/Activas/Ocultas) ---
            if hasattr(ax, '_leyenda_flujo') and ax._leyenda_flujo is not None:
                ax._leyenda_flujo.remove()

            anchored, mapa_toggle, hitbox_entries = construir_leyenda_flujo(
                ax, canvas, figure, widget, lineas_principales, None, fuente, leyendazise,
                lineas_principales=lineas_principales
            )
            anchored.set_bbox_to_anchor((0.5, alerta_bottom_axes - 0.02), ax.transAxes)
            ax._leyenda_flujo = anchored
            configurar_evento_leyenda_flujo(canvas, mapa_toggle, on_toggle_callback=actualizar_leyenda)
            ax._leyenda_hitbox_entries = hitbox_entries

            canvas.draw()
            flujo_bbox = anchored.get_window_extent(renderer)
            flujo_height = flujo_bbox.height / fig_bbox.height

            # --- Ajustar márgenes para que quepan ambas leyendas ---
            padding = 0.06
            TOP_MARGIN_FIJO = 0.92
            MIN_ALTO_GRAFICA = 0.25
            MAX_BOTTOM = 1 - MIN_ALTO_GRAFICA - 0.05

            top_margin = TOP_MARGIN_FIJO
            bottom_margin = min(0.12 + alerta_height + flujo_height + padding, MAX_BOTTOM)
            if bottom_margin >= top_margin:
                bottom_margin = MAX_BOTTOM
                top_margin = MIN_ALTO_GRAFICA + 0.05

            figure.subplots_adjust(left=0.08, right=0.95, top=top_margin, bottom=bottom_margin)
            canvas.draw()

            # --- Recalcular hitboxes para el click manual sobre la leyenda ---
            renderer_final = canvas.get_renderer()
            lista_hitboxes = []
            for icono_da, texto_area, handle, asociados, grupo_visual in ax._leyenda_hitbox_entries:
                try:
                    bbox_icono = icono_da.get_window_extent(renderer_final)
                    bbox_texto = texto_area.get_window_extent(renderer_final)
                    bbox_total = Bbox.union([bbox_icono, bbox_texto])
                    lista_hitboxes.append((bbox_total, handle, asociados, grupo_visual))
                except Exception:
                    pass
            ax._leyenda_hitboxes = lista_hitboxes
            canvas.draw_idle()
        except Exception:
            figure.subplots_adjust(left=0.08, right=0.95, top=0.85, bottom=0.35)
            canvas.draw()

    def actualizar_contador_puntos():
        # puntos_por_componente aún no existe en este scope si se define antes del bucle;
        # como ya se llenó en el bucle de arriba, se puede usar directamente aquí.
        total_visible = sum(
            cantidad for proxy, scatter_obj, cantidad in puntos_por_componente
            if proxy.get_visible()
        )
        widget.label_total_puntos.setText(f"Total: {total_visible}")

    def on_resize(event):
        actualizar_leyenda()

    def on_click(event):
        # Hit-testing manual sobre la leyenda de acelerógrafos (respaldo del pick_event)
        hitboxes = getattr(ax, '_leyenda_hitboxes', None)
        if hitboxes and event.x is not None and event.y is not None:
            for bbox, handle, asociados, grupo_visual in hitboxes:
                if bbox.contains(event.x, event.y):
                    nuevo_estado = not handle.get_visible()
                    handle.set_visible(nuevo_estado)
                    for obj in asociados:
                        obj.set_visible(nuevo_estado)
                    alpha_visual = 1.0 if nuevo_estado else 0.3
                    for art in grupo_visual:
                        art.set_alpha(alpha_visual)
                    actualizar_leyenda()
                    return

    canvas.mpl_connect('resize_event', on_resize)
    canvas.mpl_connect('button_press_event', on_click)

    actualizar_leyenda()
    canvas.draw_idle()
    plt.close(figure)
    if avisolabels:
        mostrar_mensaje("Ejes", "No se aplicó la configuración de ejes.", "advertencia")
