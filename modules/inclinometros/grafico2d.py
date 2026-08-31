import pandas as pd
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QVBoxLayout, QSizePolicy, QPushButton, QHBoxLayout, QCheckBox)
from matplotlib.colors import TABLEAU_COLORS
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from utils.common.customToolbar import CustomToolbar 
from matplotlib.figure import Figure
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
from modules.empresa.softwareconfiguracion import SoftwareConfiguracion
from controllers.ConfiguracionController import ConfiguracionController


# Subclase de NavigationToolbar para desactivar el texto de coordenadas
class CustomNavigationToolbar(CustomToolbar):
    def set_message(self, s):
        pass  # Sobreescribe el mensaje para no mostrar coordenadas

def limpiar_layout(widget):
    # Obtener el layout del widget
    layout = widget.layout()
    # Si no hay un layout, crear uno nuevo
    if layout is None:
        layout = QVBoxLayout(widget)
        widget.setLayout(layout)
    else:
        # Eliminar todos los elementos del layout
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)  # Eliminar el widget del layout
            elif item.layout():
                # Si el elemento es otro layout, limpiarlo recursivamente
                limpiar_layout(item.layout())
    return layout

def plot_2d_in_widget(idproyecto, widget1, widget2, datos, titulo1, titulo2, nombreeje1, nombreeje2, medida, tipografica, total):
    # Convertir los datos a DataFrame si no están en ese formato
    if not isinstance(datos, pd.DataFrame):
        datos = pd.DataFrame(datos, columns=["Instrumento", "fecha_inclinometro", "profundidad_detalle", "CampoA", "CampoB"])

    # Configurar formato de la fecha
    datos["fecha_inclinometro"] = pd.to_datetime(datos["fecha_inclinometro"])

    # Configuración de colores y fechas únicas
    unique_fechas = datos["fecha_inclinometro"].unique()
    colores = list(TABLEAU_COLORS.values())

    # Asegurar suficientes colores en caso de muchas fechas únicas
    if len(unique_fechas) > len(colores):
        colores = colores * (len(unique_fechas) // len(colores) + 1)

    # Limpiar layout en ambos widgets
    main_layout1 = limpiar_layout(widget1)
    main_layout2 = limpiar_layout(widget2)

    # Configurar gráfico para desplazamiento A en widget1
    config = SoftwareConfiguracion.obtenerDataSoftware()
    titulozise, ejezise, etiquesize, leyendazise, fuente = config[0], config[1], config[2], config[3], config[10]
    grosorlinea, decimales = config[12], config[14]
    figure1 = Figure()
    plt.rcParams['font.family'] = fuente
    canvas1 = FigureCanvas(figure1)
    canvas1.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    # Layout para toolbar y botones de paginación
    toolbar_layout1 = QHBoxLayout()

    # Agregar la toolbar de Matplotlib en orientación vertical
    toolbar1 = CustomNavigationToolbar(canvas1, widget1)
    toolbar1.setOrientation(Qt.Horizontal)
    toolbar_layout1.addWidget(toolbar1)

    check_inspector1 = QCheckBox("Inspector de Datos")
    check_inspector1.setStyleSheet("font-size: 12px; margin-left: 10px; font-weight: bold;")
    toolbar_layout1.addWidget(check_inspector1)

    # Configuración de gráficos en Matplotlib
    gs1 = gridspec.GridSpec(1, 2, width_ratios=[2, 1], wspace=0.2, figure=figure1)
    ax1 = figure1.add_subplot(gs1[0])
    ax_legend1 = figure1.add_subplot(gs1[1])
    ax_legend1.axis("off")

    # Graficar Desplazamiento A
    lines1 = []
    for i, fecha in enumerate(unique_fechas):
        subset = datos[datos["fecha_inclinometro"] == fecha]
        line, = ax1.plot(subset["CampoA"], subset["profundidad_detalle"], color=colores[i], linewidth=grosorlinea)
        lines1.append((line, fecha.strftime('%d/%m/%Y'), subset))
    ax1.set_xlabel(nombreeje1, fontsize=ejezise)
    ax1.set_ylabel("Profundidad (m)", fontsize=ejezise)
    ax1.set_title(titulo1, pad=20, fontsize=titulozise)  # Separar el título de la gráfica
    ax1.grid(True, linestyle='--', linewidth=0.5)

    annot1 = ax1.annotate("", xy=(0, 0), xytext=(15, 15), textcoords="offset points",
                          bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#cccccc", lw=1, alpha=0.95),
                          arrowprops=dict(arrowstyle="-|>", connectionstyle="arc3,rad=0.2", color="#555555", lw=0.8))
    annot1.set_visible(False)
    punto_resaltado1, = ax1.plot([], [], 'o', color='#dc3545', markersize=6,
                                  markeredgecolor='white', markeredgewidth=1, zorder=10)
    punto_resaltado1.set_visible(False)

    # Ajustar el eje Y para que siempre comience en 0 y vaya hacia abajo
    if datos["profundidad_detalle"].max() > 0:
        ax1.invert_yaxis()

    # Paginación de la leyenda
    items_per_page = 15
    total_pages = (len(unique_fechas) + items_per_page - 1) // items_per_page

    def update_legend(page, ax_legend, main_axis, canvas):
        start_idx = page * items_per_page
        end_idx = start_idx + items_per_page
        current_fechas = unique_fechas[start_idx:end_idx]
        formatted_dates = [fecha.strftime('%d/%m/%Y') for fecha in current_fechas]
        # Agregar el label inicial al principio de la leyenda
        all_handles = []
        all_labels = []
        activas = len(unique_fechas)
        ocultas = total - activas
        total_handle = plt.Line2D([0], [0], color='w', label=f'Total: {total}', linestyle='None')
        activa_handle = plt.Line2D([0], [0], color='w', label=f'Activas: {activas}', linestyle='None')
        oculta_handle = plt.Line2D([0], [0], color='w', label=f'Ocultas: {ocultas}', linestyle='None')
        all_handles.append(total_handle)
        all_handles.append(activa_handle)
        all_handles.append(oculta_handle)
        all_labels.append(f'Total: {total}')
        all_labels.append(f'Activas: {activas}')
        all_labels.append(f'Ocultas: {ocultas}')
        date_handles = [plt.Line2D([0], [0], color=colores[i], lw=3) for i in range(len(current_fechas))]
        all_handles.extend(date_handles)
        all_labels.extend(formatted_dates)
        ax_legend.legend(all_handles, all_labels, loc="center left", prop={'size': leyendazise},
                        bbox_to_anchor=(1, 0.5), bbox_transform=main_axis.transAxes)
        canvas.draw()

    # Crear botones de paginación con nombres únicos y símbolos de triángulo
    if total_pages > 1:
        prev_button1 = QPushButton("◀")  # Triángulo hacia la izquierda
        next_button1 = QPushButton("▶")  # Triángulo hacia la derecha

        def on_prev_button1():
            nonlocal current_page1
            if current_page1 > 0:
                current_page1 -= 1
                update_legend(current_page1, ax_legend1, ax1, canvas1)  # Pasar ax1 como main_axis

        def on_next_button1():
            nonlocal current_page1
            if current_page1 < total_pages - 1:
                current_page1 += 1
                update_legend(current_page1, ax_legend1, ax1, canvas1)  # Pasar ax1 como main_axis

        prev_button1.clicked.connect(on_prev_button1)
        next_button1.clicked.connect(on_next_button1)

        toolbar_layout1.addWidget(prev_button1)
        toolbar_layout1.addWidget(next_button1)

    main_layout1.addWidget(canvas1)
    main_layout1.addLayout(toolbar_layout1)

    current_page1 = 0
    update_legend(current_page1, ax_legend1, ax1, canvas1)  # Pasar ax1 como main_axis

    # Formatear fechas a 'día-mes-año' y añadir leyenda en widget1
    ax1.xaxis.set_major_formatter(plt.FuncFormatter(lambda val, pos: '{:.{}f}'.format(val, decimales)))

    # Configurar gráfico para desplazamiento B en widget2
    figure2 = Figure()
    canvas2 = FigureCanvas(figure2)
    canvas2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    # Layout para toolbar y botones de paginación
    toolbar_layout2 = QHBoxLayout()

    # Agregar la toolbar de Matplotlib en orientación vertical
    toolbar2 = CustomNavigationToolbar(canvas2, widget2)
    toolbar2.setOrientation(Qt.Horizontal)
    toolbar_layout2.addWidget(toolbar2)

    check_inspector2 = QCheckBox("Inspector de Datos")
    check_inspector2.setStyleSheet("font-size: 12px; margin-left: 10px; font-weight: bold;")
    toolbar_layout2.addWidget(check_inspector2)

    # Configuración de gráficos en Matplotlib
    gs2 = gridspec.GridSpec(1, 2, width_ratios=[2, 1], wspace=0.2, figure=figure2)
    ax2 = figure2.add_subplot(gs2[0])
    ax_legend2 = figure2.add_subplot(gs2[1])
    ax_legend2.axis("off")

    # Graficar Desplazamiento B
    lines2 = []
    for i, fecha in enumerate(unique_fechas):
        subset = datos[datos["fecha_inclinometro"] == fecha]
        line, = ax2.plot(subset["CampoB"], subset["profundidad_detalle"], color=colores[i], linewidth=grosorlinea)
        lines2.append((line, fecha.strftime('%d/%m/%Y'), subset))
    ax2.set_xlabel(nombreeje2, fontsize=ejezise)
    ax2.set_ylabel("Profundidad (m)", fontsize=ejezise)
    ax2.set_title(titulo2, pad=20, fontsize=titulozise)  # Separar el título de la gráfica
    ax2.grid(True, linestyle='--', linewidth=0.5)
    ax2.xaxis.set_major_formatter(plt.FuncFormatter(lambda val, pos: '{:.{}f}'.format(val, decimales)))

    annot2 = ax2.annotate("", xy=(0, 0), xytext=(15, 15), textcoords="offset points",
                          bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#cccccc", lw=1, alpha=0.95),
                          arrowprops=dict(arrowstyle="-|>", connectionstyle="arc3,rad=0.2", color="#555555", lw=0.8))
    annot2.set_visible(False)
    punto_resaltado2, = ax2.plot([], [], 'o', color='#dc3545', markersize=6,
                                  markeredgecolor='white', markeredgewidth=1, zorder=10)
    punto_resaltado2.set_visible(False)

    # Ajustar el eje Y para que siempre comience en 0 y vaya hacia abajo
    if datos["profundidad_detalle"].max() > 0:
        ax2.invert_yaxis()

    # Crear botones de paginación con nombres únicos y símbolos de triángulo
    if total_pages > 1:
        prev_button2 = QPushButton("◀")  # Triángulo hacia la izquierda
        next_button2 = QPushButton("▶")  # Triángulo hacia la derecha

        def on_prev_button2():
            nonlocal current_page2
            if current_page2 > 0:
                current_page2 -= 1
                update_legend(current_page2, ax_legend2, ax2, canvas2)  # Pasar ax2 como main_axis

        def on_next_button2():
            nonlocal current_page2
            if current_page2 < total_pages - 1:
                current_page2 += 1
                update_legend(current_page2, ax_legend2, ax2, canvas2)  # Pasar ax2 como main_axis

        prev_button2.clicked.connect(on_prev_button2)
        next_button2.clicked.connect(on_next_button2)

        toolbar_layout2.addWidget(prev_button2)
        toolbar_layout2.addWidget(next_button2)

    main_layout2.addWidget(canvas2)
    main_layout2.addLayout(toolbar_layout2)

    current_page2 = 0
    update_legend(current_page2, ax_legend2, ax2, canvas2)  # Pasar ax2 como main_axis

    # Ajustar limites de gráficas eje x de los dos graficos
    ejexmin, ejexmax, ejexprin, ejexsecu, intervaloy = 0, 0, 0, 0, 0
    dataeje = ConfiguracionController.ctrlObtenerConfiguracionEje(idproyecto, "INCLINOMETROS", tipografica)
    if dataeje:
        ejexmin, ejexmax, ejexprin, ejexsecu, intervaloy = dataeje[4], dataeje[5], dataeje[6], dataeje[7], dataeje[8]
    
    # SOLUCIÓN AL WARNING: Evitar límites idénticos en eje X
    if ejexmin != 0 or ejexmax != 0:
        low_val = ejexmin * medida
        high_val = ejexmax * medida
        
        # Ajustar límites si son iguales
        if low_val == high_val:
            # Crear un rango mínimo alrededor del valor
            offset = max(abs(low_val) * 0.1, 0.1) if low_val != 0 else 0.1
            low_val -= offset
            high_val += offset
        
        # Establecer límites con valores ajustados
        ax1.set_xlim(low_val, high_val)
        ax2.set_xlim(low_val, high_val)
        
        # Calcula los intervalos primarios
        if ejexprin > 0:
            intervalo = ejexprin * medida
            ticks = np.arange(low_val, high_val + intervalo, intervalo)
            ticks = ticks[(ticks >= low_val) & (ticks <= high_val)]
            if len(ticks) == 0:  # Si no hay ticks, añadir el valor central
                ticks = np.array([low_val + (high_val - low_val)/2])
            ax1.set_xticks(ticks)
            ax2.set_xticks(ticks)
        
        # Calcula los intervalos secundarios
        if ejexsecu > 0:
            tick_secundarios = np.arange(low_val, high_val, ejexsecu * medida)
            for tick in tick_secundarios:
                ax1.axvline(x=tick, color='gray', linestyle='--', linewidth=0.5)
                ax2.axvline(x=tick, color='gray', linestyle='--', linewidth=0.5)
    
    # formatear el eje y
    zprofundidad = datos["profundidad_detalle"]
    if intervaloy == 0:
        if len(zprofundidad) >= 2:
            rango = abs(zprofundidad.iloc[0]) - abs(zprofundidad.iloc[-1])
            newescala = abs(rango) / 10
            if newescala > 1:
                intervaloy = int(newescala)
            else:
                intervaloy = 1
        else:
            intervaloy = 1
    
    # Encuentra el índice del primer valor en zprofundidad
    valor_min = zprofundidad.min()
    valor_max = zprofundidad.max()
    tick_values = np.arange(0, max(abs(valor_min), abs(valor_max)) + intervaloy, intervaloy)
    tick_values *= np.sign(valor_min) if valor_min != 0 else 1
    ax1.set_yticks(tick_values)
    ax2.set_yticks(tick_values)
    
    # Ajustar layout para evitar corte de etiquetas
    figure1.subplots_adjust(bottom=0.15)
    figure2.subplots_adjust(bottom=0.15)
    
    # Configuración robusta de etiquetas del eje X
    ax1.tick_params(axis='x', rotation=90, labeltop=False, labelbottom=True, labelsize=etiquesize)
    ax2.tick_params(axis='x', rotation=90, labeltop=False, labelbottom=True, labelsize=etiquesize)
    
    # Asegurar alineación correcta
    for label in ax1.get_xticklabels():
        label.set_horizontalalignment('center')
        label.set_verticalalignment('top')
    
    for label in ax2.get_xticklabels():
        label.set_horizontalalignment('center')
        label.set_verticalalignment('top')
    
    # Configuración de etiquetas del eje Y
    ax1.tick_params(axis='y', labelsize=etiquesize)
    ax2.tick_params(axis='y', labelsize=etiquesize)

    # Función para manejar el evento de clic
    def on_click(event):
        if event.inaxes in [ax1, ax2]:
            lines = lines1 if event.inaxes == ax1 else lines2
            if event.button == 3:  # Botón derecho del ratón
                min_distance = float('inf')
                closest_line = None
                closest_point = None
                closest_date = None

                for line, date, subset in reversed(lines):
                    x_data = subset["CampoA" if event.inaxes == ax1 else "CampoB"]
                    y_data = subset["profundidad_detalle"]
                    distances = np.sqrt((x_data - event.xdata)**2 + (y_data - event.ydata)**2)
                    min_line_distance = np.min(distances)
                    if min_line_distance < min_distance:
                        min_distance = min_line_distance
                        closest_line = line
                        closest_idx = np.argmin(distances)
                        closest_point = (x_data.iloc[closest_idx], y_data.iloc[closest_idx])
                        closest_date = date

                if closest_line is not None and min_distance < 10:  # Umbral de distancia para considerar el clic válido
                    # Ocultar anotaciones anteriores si existen
                    for text in event.inaxes.texts:
                        text.set_visible(False)

                    # Crear y mostrar la anotación en el punto más cercano
                    annotation = event.inaxes.annotate(closest_date, closest_point,
                                                        textcoords="offset points", xytext=(10, 10),
                                                        ha='left', fontsize=etiquesize,
                                                        bbox=dict(facecolor='yellow', alpha=0.8, edgecolor='none'))
                    annotation.set_visible(True)
                    if event.inaxes == ax1:
                        canvas1.draw()
                    else:
                        canvas2.draw()
            elif event.button == 1:  # Botón izquierdo del ratón
                # Ocultar todas las anotaciones existentes
                for text in event.inaxes.texts:
                    text.set_visible(False)
                if event.inaxes == ax1:
                    canvas1.draw()
                else:
                    canvas2.draw()

    # Conectar el evento de clic
    figure1.canvas.mpl_connect('button_press_event', on_click)
    figure2.canvas.mpl_connect('button_press_event', on_click)

    def on_hover1(event):
        if not check_inspector1.isChecked() or event.inaxes != ax1:
            if annot1.get_visible():
                annot1.set_visible(False)
                punto_resaltado1.set_visible(False)
                canvas1.draw_idle()
            return

        min_dist = 30
        encontrado = None
        xlim, ylim = ax1.get_xlim(), ax1.get_ylim()

        for line, fecha_str, subset in lines1:
            if not line.get_visible():
                continue
            x_data = subset["CampoA"].to_numpy()
            y_data = subset["profundidad_detalle"].to_numpy()
            mask = (x_data >= min(xlim)) & (x_data <= max(xlim)) & (y_data >= min(ylim)) & (y_data <= max(ylim))
            if not np.any(mask):
                continue
            puntos_px = ax1.transData.transform(np.column_stack([x_data[mask], y_data[mask]]))
            mouse = np.array([event.x, event.y])
            dists = np.sqrt(np.sum((puntos_px - mouse) ** 2, axis=1))
            idx = np.argmin(dists)
            if dists[idx] < min_dist:
                min_dist = dists[idx]
                encontrado = (x_data[mask][idx], y_data[mask][idx], fecha_str)

        if encontrado:
            fx, fy, fecha_str = encontrado
            punto_resaltado1.set_data([fx], [fy])
            punto_resaltado1.set_visible(True)
            punto_pixel = ax1.transData.transform((fx, fy))
            x_rel, y_rel = ax1.transAxes.inverted().transform(punto_pixel)
            offset_x, offset_y = 15, 15
            ha, va = 'left', 'bottom'
            if y_rel > 0.70: va, offset_y = 'top', -15
            if x_rel > 0.65: ha, offset_x = 'right', -15
            annot1.xy = (fx, fy)
            annot1.xytext = (offset_x, offset_y)
            annot1.set_ha(ha)
            annot1.set_va(va)
            annot1.set_text(f"Fecha: {fecha_str}\nProfundidad: {fy:.2f} m\nDesplaz. A: {fx:.3f}")
            annot1.set_fontsize(9)
            annot1.set_color('#333333')
            annot1.set_visible(True)
            annot1.set_zorder(999)
            canvas1.draw_idle()
        else:
            if annot1.get_visible():
                annot1.set_visible(False)
                punto_resaltado1.set_visible(False)
                canvas1.draw_idle()

    def on_hover2(event):
        if not check_inspector2.isChecked() or event.inaxes != ax2:
            if annot2.get_visible():
                annot2.set_visible(False)
                punto_resaltado2.set_visible(False)
                canvas2.draw_idle()
            return

        min_dist = 30
        encontrado = None
        xlim, ylim = ax2.get_xlim(), ax2.get_ylim()

        for line, fecha_str, subset in lines2:
            if not line.get_visible():
                continue
            x_data = subset["CampoB"].to_numpy()
            y_data = subset["profundidad_detalle"].to_numpy()
            mask = (x_data >= min(xlim)) & (x_data <= max(xlim)) & (y_data >= min(ylim)) & (y_data <= max(ylim))
            if not np.any(mask):
                continue
            puntos_px = ax2.transData.transform(np.column_stack([x_data[mask], y_data[mask]]))
            mouse = np.array([event.x, event.y])
            dists = np.sqrt(np.sum((puntos_px - mouse) ** 2, axis=1))
            idx = np.argmin(dists)
            if dists[idx] < min_dist:
                min_dist = dists[idx]
                encontrado = (x_data[mask][idx], y_data[mask][idx], fecha_str)

        if encontrado:
            fx, fy, fecha_str = encontrado
            punto_resaltado2.set_data([fx], [fy])
            punto_resaltado2.set_visible(True)
            punto_pixel = ax2.transData.transform((fx, fy))
            x_rel, y_rel = ax2.transAxes.inverted().transform(punto_pixel)
            offset_x, offset_y = 15, 15
            ha, va = 'left', 'bottom'
            if y_rel > 0.70: va, offset_y = 'top', -15
            if x_rel > 0.65: ha, offset_x = 'right', -15
            annot2.xy = (fx, fy)
            annot2.xytext = (offset_x, offset_y)
            annot2.set_ha(ha)
            annot2.set_va(va)
            annot2.set_text(f"Fecha: {fecha_str}\nProfundidad: {fy:.2f} m\nDesplaz. B: {fx:.3f}")
            annot2.set_fontsize(9)
            annot2.set_color('#333333')
            annot2.set_visible(True)
            annot2.set_zorder(999)
            canvas2.draw_idle()
        else:
            if annot2.get_visible():
                annot2.set_visible(False)
                punto_resaltado2.set_visible(False)
                canvas2.draw_idle()

    canvas1.mpl_connect('motion_notify_event', on_hover1)
    canvas2.mpl_connect('motion_notify_event', on_hover2)

    # Actualizar canvas para desplazamiento A y B
    canvas1.draw()
    canvas2.draw()