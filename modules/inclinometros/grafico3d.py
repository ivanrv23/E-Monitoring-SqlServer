import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from PySide6.QtWidgets import (QVBoxLayout, QSizePolicy,QPushButton,QHBoxLayout)
from matplotlib.colors import TABLEAU_COLORS
from PySide6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from utils.common.customToolbar import CustomToolbar 
from utils.common.alertas import mostrar_mensaje
from matplotlib.figure import Figure
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

def plot_3d_in_widget(idproyecto, datos, titulo, nombreejex, nombreejey, widget, spin_rotacion, medida, tipografica, total):
    avisolabels = False
    # Crear DataFrame a partir de los datos reales
    df = pd.DataFrame(datos, columns=['Instrumento', 'Fecha', 'Profundidad', 'D_A', 'D_B'])

    # Convertir la columna 'Fecha' a datetime si no está en ese formato
    df['Fecha'] = pd.to_datetime(df['Fecha'])

    # Obtener el QSpinBox y desconectar el evento si está conectado
    try:
        if spin_rotacion.receivers(spin_rotacion.valueChanged) > 0:
            spin_rotacion.valueChanged.disconnect()
    except (TypeError, RuntimeError):
        pass  # Ignoramos el error si no estaba conectado

    # Reiniciar el valor del spin_rotacion a cero
    spin_rotacion.setValue(0)

    # Limpiar todo el contenido del layout
    main_layout = limpiar_layout(widget)

    # Crear nuevo FigureCanvas y agregar al layout
    config = SoftwareConfiguracion.obtenerDataSoftware()
    titulozise, ejezise, etiquesize, leyendazise, fuente = config[0], config[1], config[2], config[3], config[10]
    grosorlinea, decimales = config[12], config[14]
    figure = Figure()  # No especificar figsize para permitir redimensionamiento dinámico
    plt.rcParams['font.family'] = fuente
    canvas = FigureCanvas(figure)
    canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    # Layout para toolbar y botones de paginación
    toolbar_layout = QHBoxLayout()

    # Agregar la toolbar de Matplotlib en orientación vertical
    toolbar = CustomNavigationToolbar(canvas, widget)
    toolbar.setOrientation(Qt.Horizontal)
    toolbar_layout.addWidget(toolbar)

    # Configuración de gráficos en Matplotlib
    gs = gridspec.GridSpec(1, 2, width_ratios=[2, 1], wspace=0.02, figure=figure)
    ax = figure.add_subplot(gs[0], projection='3d')

    # Colores para cada fecha usando TABLEAU_COLORS
    unique_fechas = df["Fecha"].unique()
    colores = list(TABLEAU_COLORS.values())
    colores = colores * (len(unique_fechas) // len(colores) + 1)  # Repetir colores si faltan

    # Graficar cada línea de desplazamiento usando un loop sobre fechas únicas
    for i, fecha in enumerate(unique_fechas):
        subset = df[df["Fecha"] == fecha]
        if not subset.empty and subset["D_A"].notna().any() and subset["D_B"].notna().any() and subset["Profundidad"].notna().any():
            ax.plot(subset["D_A"], subset["D_B"], subset["Profundidad"], color=colores[i], linewidth=grosorlinea)

    # Configuración de etiquetas
    ax.set_xlabel(nombreejex, labelpad=5, fontsize=ejezise)
    ax.set_ylabel(nombreejey, labelpad=5, fontsize=ejezise)
    ax.set_zlabel("Profundidad (m)", labelpad=7, fontsize=ejezise)
    ax.set_title(titulo, pad=15, fontsize=titulozise)  # Reducir el padding del título

    # Ajuste del tamaño de los valores en los ejes
    ax.tick_params(axis='x', labelsize=etiquesize)
    ax.tick_params(axis='y', labelsize=etiquesize)
    ax.tick_params(axis='z', labelsize=etiquesize)

    # Ajuste de los límites de los ejes para hacer más largo el eje Y
    ax.set_box_aspect([1.5, 1.5, 3])

    # Ajustar limites de gráficas eje x, y de los dos graficos
    ejexmin, ejexmax, ejexprin, ejexsecu, intervaloy = 0, 0, 0, 0, 0
    dataeje = ConfiguracionController.ctrlObtenerConfiguracionEje(idproyecto, "INCLINOMETROS", tipografica)
    if dataeje:
        ejexmin, ejexmax, ejexprin, ejexsecu, intervaloy = dataeje[4], dataeje[5], dataeje[6], dataeje[7], dataeje[8]
    if ejexmin != 0 or ejexmax != 0:
        ax.set_xlim(ejexmin * medida, ejexmax * medida)
        ax.set_ylim(ejexmin * medida, ejexmax * medida)
        # Calcula los intervalos primarios
        if ejexprin > 0:
            inicio = ejexmin * medida
            fin = ejexmax * medida
            intervalo = ejexprin * medida
            ticks = np.arange(inicio, fin + intervalo, intervalo)
            ticks = ticks[(ticks >= inicio) & (ticks <= fin)]
            if inicio not in ticks:
                ticks = np.insert(ticks, 0, inicio)
            if fin not in ticks:
                ticks = np.append(ticks, fin)
            if len(ticks) > 2 and len(ticks) < 50:
                ax.set_xticks(ticks)
                ax.set_yticks(ticks)
            else:
                avisolabels = True
    else:
        ax.set_xlim([df["D_A"].min() - 0.01, df["D_A"].max() + 0.01])
        ax.set_ylim([df["D_B"].min() - 0.01, df["D_B"].max() + 0.01])
    # formatear el eje z
    zprofundidad = df["Profundidad"]
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
    valor_min = zprofundidad.min()
    valor_max = zprofundidad.max()
    tick_values = np.arange(0, max(abs(valor_min), abs(valor_max)) + intervaloy, intervaloy)
    tick_values *= np.sign(valor_min)
    ax.set_zticks(tick_values)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda val, pos: '{:.{}f}'.format(val, decimales)))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda val, pos: '{:.{}f}'.format(val, decimales)))
    # Validar eje z
    z_min = df["Profundidad"].min()
    z_max = df["Profundidad"].max()
    # Ajustar los límites del eje z para incluir el cero y invertir si es necesario
    if z_min < 0 and z_max > 0:
        ax.set_zlim([z_min, z_max])
    elif z_min < 0:
        ax.set_zlim([z_min, 0.1])  # Asegurar que el cero esté visible si todos los valores son negativos
    elif z_max > 0:
        ax.set_zlim([z_max + 0.1, 0])  # Invertir el eje z si todos los valores son positivos
    else:
        ax.set_zlim([-0.1, 0.1])  # Si todos los valores son cero

    # Subparcela para la leyenda
    ax_legend = figure.add_subplot(gs[1])
    ax_legend.axis("off")

    # Paginación de la leyenda
    items_per_page = 15
    total_pages = (len(unique_fechas) + items_per_page - 1) // items_per_page

    def update_legend(page):
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
        ax_legend.legend(all_handles, all_labels, loc="center left", prop={'size': leyendazise}, bbox_to_anchor=(1.0, 0.5), bbox_transform=ax.transAxes)
        canvas.draw()

    # Crear botones de paginación con nombres únicos y símbolos de triángulo
    if total_pages > 1:
        prev_button = QPushButton("◀")  # Triángulo hacia la izquierda
        next_button = QPushButton("▶")  # Triángulo hacia la derecha

        def on_prev_button():
            nonlocal current_page
            if current_page > 0:
                current_page -= 1
                update_legend(current_page)

        def on_next_button():
            nonlocal current_page
            if current_page < total_pages - 1:
                current_page += 1
                update_legend(current_page)

        prev_button.clicked.connect(on_prev_button)
        next_button.clicked.connect(on_next_button)

        toolbar_layout.addWidget(prev_button)
        toolbar_layout.addWidget(next_button)

    main_layout.addWidget(canvas)
    main_layout.addLayout(toolbar_layout)

    current_page = 0
    update_legend(current_page)

    # Establecer ángulo inicial y reconectar el evento
    angulo_inicial = 270
    ax.view_init(elev=5, azim=angulo_inicial)

    # Reconectar el evento solo si el canvas está disponible
    if canvas is not None:
        spin_rotacion.valueChanged.connect(lambda: rotar_en_x(ax, angulo_inicial, spin_rotacion, figure))

    # Ajustar manualmente los márgenes para maximizar el espacio del gráfico
    figure.subplots_adjust(left=0, right=1, top=1, bottom=0)

    # Actualizar el canvas
    canvas.draw()

    # Conectar el evento de redimensionamiento del widget al ajuste del gráfico
    def on_resize(event):
        figure.subplots_adjust(left=0, right=1, top=1, bottom=0)
        canvas.draw()

    widget.resizeEvent = on_resize
    if avisolabels:
        mostrar_mensaje("Ejes", "No se aplicó la configuración de ejes.", "advertencia")
    
def rotar_en_x(ax, angulo_inicial, spin_rotacion, fig):
    angulo_total = spin_rotacion.value()
    ax.view_init(elev=ax.elev, azim=angulo_inicial + angulo_total)
    # Verifica que el canvas sigue existiendo y esté visible antes de dibujar
    try:
        if fig.canvas is not None:
            fig.canvas.draw()
    except RuntimeError:
        # Si el canvas ya no existe, no se realiza ninguna acción
        pass
