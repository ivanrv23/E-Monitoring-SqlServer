import mplstereonet as mpl # No borrar
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.gridspec import GridSpec
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PySide6.QtWidgets import QVBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import QTimer
from modules.empresa.softwareconfiguracion import SoftwareConfiguracion

class GraficarEstereografiaTrayectoria:
    trayectoriagraficada = False
    canvastrayectoria, axtrayectoria = None, None
    
    def limpiar_widget(widget):
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
    
    def graficar_estereografia_nuevaversion(widget, vectores, dataestereo, tipo="polar"):
        config = SoftwareConfiguracion.obtenerDataSoftware()
        ejezise, fuente = config[1], config[10]
        plt.rcParams['font.family'] = fuente
        plt.rcParams['font.size'] = ejezise
        # Limpiar el layout del widget para eliminar gráficos previos
        GraficarEstereografiaTrayectoria.limpiar_widget(widget)
        layout = widget.layout()
        # Verificar que el tipo de gráfico sea válido
        if tipo not in ["polar", "ecuatorial"]:
            label = QLabel("Tipo de gráfico no válido. Use 'polar' o 'ecuatorial'.")
            layout.addWidget(label)
            return
        # Crear la figura y definir el layout usando GridSpec
        fig = plt.figure()
        fig.subplots_adjust(left=0.25)  # Ajuste del margen izquierdo para centrar la gráfica
        gs = GridSpec(1, 2, width_ratios=[2, 1], wspace=0.1)
        legend_lines = []
        # Definir vectores y graficar
        colores = ['b', 'g', 'r', 'c', 'm', 'y', 'orange', 'purple', 'brown', 'gray']
        if tipo == "polar":
            # Gráfico polar
            ax = fig.add_subplot(gs[0], projection='polar')
            ax.set_theta_offset(np.pi / 2)
            ax.set_theta_direction(-1)
            angles = np.arange(0, 360, 15)
            ax.set_thetagrids(angles, fontsize=9)
            plunge_angles = np.arange(0, 90, 10)
            ax.set_rgrids(plunge_angles, labels=[f"{angle}°" for angle in plunge_angles], angle=0, fontsize=7)
            ax.set_ylim(0, 90)
            if vectores:
                
                for i, (nombre, trend, plunge) in enumerate(vectores):
                    trend_rad = np.deg2rad(trend)
                    ax.plot([0, trend_rad], [0, plunge], color=colores[i % len(colores)], linewidth=1.5)
                    ax.annotate('', xy=(trend_rad, plunge), xytext=(0, 0),
                                arrowprops=dict(arrowstyle="->", color=colores[i % len(colores)], lw=1.5))
                    legendline = Line2D([0], [1], color=colores[i % len(colores)], lw=1.5, label=f"{nombre}: ({trend:.3f}, {plunge:.3f})")
                    legend_lines.append(legendline)
            if dataestereo:
                for i, estereo in enumerate(dataestereo):
                    strike = estereo[4] - 90  # Ajuste de 90 grados
                    dip = estereo[3]
                    # transformar
                    theta_values = np.linspace(0, 2*np.pi, 100)
                    # Esta fórmula puede necesitar ajustes según la convención exacta que uses
                    r_values = 90 - dip / np.sin(np.abs(theta_values - np.deg2rad(strike)))
                    valid_indices = (r_values <= 90) & (r_values >= 0)
                    theta_valid = theta_values[valid_indices]
                    r_valid = r_values[valid_indices]
                    # Graficar la línea
                    ax.plot(theta_valid, r_valid, color=colores[i % len(colores)], linestyle='-', linewidth=1.5)
                    legend_lines.insert(0, Line2D([0], [0], color=colores[i % len(colores)], lw=1.5, label=estereo[2]))
            ax.set_title("Gráfica Polar", fontsize=10, pad=10)

        elif tipo == "ecuatorial":
            # Gráfico estereográfico
            ax = fig.add_subplot(gs[0], projection='stereonet')
            # Definir vectores y graficar
            if vectores:
                for i, (nombre, trend, plunge) in enumerate(vectores):
                    trend_rad = np.radians(trend)
                    plunge_rad = np.radians(plunge)
                    ax.annotate('', xy=(trend_rad, plunge_rad), xytext=(0, 0),
                                arrowprops=dict(arrowstyle="->", color=colores[i % len(colores)], lw=1.5))
                    legendline = Line2D([0], [1], color=colores[i % len(colores)], lw=1.5, label=f"{nombre}: ({trend:.3f}, {plunge:.3f})")
                    legend_lines.append(legendline)
            if dataestereo:
                for i, estereo in enumerate(dataestereo):
                    strike = estereo[4] - 90  # Ajuste de 90 grados
                    dip = estereo[3]
                    ax.plane(strike, dip, color=colores[i % len(colores)], linestyle='-', linewidth=1.5, label=estereo[2])
                    legend_lines.insert(0, Line2D([0], [0], color=colores[i % len(colores)], lw=1.5, label=estereo[2]))

            ax.grid(True, linewidth=0.5)
            ax.set_azimuth_ticks(np.arange(0, 360, 15))
            ax.set_title("Gráfica Estereográfica", fontsize=10, pad=30)

        # Leyenda en el segundo espacio de GridSpec
        legend_ax = fig.add_subplot(gs[1])
        legend_ax.axis('off')
        legend_ax.legend(handles=legend_lines, loc="center left", prop={'size': 7}, bbox_to_anchor=(1.15, 0.5), bbox_transform=ax.transAxes)

        # Crear y añadir el canvas al widget
        canvas = FigureCanvas(fig)
        layout.addWidget(canvas)
        plt.close(fig)
    
    def graficar_estereografia(widget, vectores, dataestereo, tipo="polar"):
        config = SoftwareConfiguracion.obtenerDataSoftware()
        titulozise, ejezise, leyendazise, fuente = config[0], config[1], config[3], config[10]
        plt.rcParams['font.family'] = fuente
        plt.rcParams['font.size'] = ejezise

        # Limpiar el layout del widget para eliminar gráficos previos
        GraficarEstereografiaTrayectoria.limpiar_widget(widget)
        layout = widget.layout()

        if tipo not in ["polar", "ecuatorial"]:
            label = QLabel("Tipo de gráfico no válido. Use 'polar' o 'ecuatorial'.")
            layout.addWidget(label)
            return

        figura = plt.figure()
        canvas = FigureCanvas(figura)
        gs = GridSpec(2, 1, height_ratios=[4, 1], hspace=0.2)

        ax = figura.add_subplot(gs[0], projection='equal_angle_stereonet')
        if tipo == 'polar':
            ax.grid(kind='polar')
            ax.set_azimuth_ticks(np.arange(0, 360, 30))
            titulografica = "Gráfica Estereográfica Polar"
        else:
            ax.grid()
            ax.set_azimuth_ticks(np.arange(0, 360, 15))
            titulografica = "Gráfica Estereográfica Ecuatorial"
        # graficar
        legend_lines = []
        if vectores:
            cmap1 = plt.get_cmap('tab20')
            cmap2 = plt.get_cmap('tab20b')
            for i, (nombre, trend, plunge) in enumerate(vectores):
                if trend is not None and plunge is not None:
                    color_flecha = cmap1(i % 20) if i < 20 else cmap2((i - 20) % 20)
                    plunge_abs = abs(plunge)
                    if plunge_abs == 90:
                        ax.scatter(0, 0, color=color_flecha, s=50, zorder=5, marker='o')
                    else:
                        x_dest, y_dest = mpl.line(plunge_abs, trend)
                        x_dest = float(np.asarray(x_dest).ravel()[0])
                        y_dest = float(np.asarray(y_dest).ravel()[0])
                        ax.annotate('', xy=(x_dest, y_dest), xytext=(0, 0), arrowprops=dict(arrowstyle='->', linewidth=2, color=color_flecha, shrinkA=0, shrinkB=0), zorder=5)
                    legendline = Line2D([0], [0], color=color_flecha, linewidth=2, label=f"{nombre}: ({trend:06.2f}°, {plunge:05.2f}°)")
                    legend_lines.append(legendline)
        if dataestereo:
            colores = ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'orange', 'purple', 'brown', 'gray']
            for i, estereo in enumerate(dataestereo):
                strike = estereo[4] - 90
                dip = estereo[3]
                ax.plane(strike, dip, color=colores[i % len(colores)], linestyle='-', linewidth=2)
                legend_lines.insert(
                    0, 
                    Line2D(
                        [0], [0], 
                        color=colores[i % len(colores)], 
                        lw=2, 
                        label=f"{estereo[2]} ({estereo[4]:.2f}°/{estereo[3]:.2f}°)"
                    )
                )

        ax.set_title(titulografica, fontsize=titulozise, pad=30)

        legend_ax = figura.add_subplot(gs[1])
        legend_ax.axis('off')
        legend_ax.legend(
            handles=legend_lines, 
            loc="upper center", 
            ncol=2, 
            prop={'size': leyendazise},
            framealpha=0.7
        )

        layout.addWidget(canvas)
        canvas.draw()
        plt.close(figura)
    
    def graficar_trayectoria(widget, datos, combovistas, tipo):
        df = pd.DataFrame(datos, columns=['col_' + str(i) for i in range(len(datos[0]))])
        df = df[[df.columns[0], df.columns[1], df.columns[2], 
                df.columns[3], df.columns[4], df.columns[5]]]
        df.columns = ['Instrumento', 'Nombre', 'Fecha', 'Este', 'Norte', 'Nivel']

        # Detener y limpiar timer previo si existe
        if hasattr(widget, "timer") and widget.timer:
            if widget.timer.isActive():
                widget.timer.stop()
            widget.timer.deleteLater()
            widget.timer = None

        # =========================================================
        # CORRECCIÓN 1: Desconectar señal anterior antes de limpiar
        # =========================================================
        if hasattr(widget, '_cambiar_vistas_slot') and widget._cambiar_vistas_slot:
            try:
                combovistas.activated.disconnect(widget._cambiar_vistas_slot)
            except RuntimeError:
                pass  # Ya estaba desconectada
            widget._cambiar_vistas_slot = None
        # =========================================================

        # Limpiar el layout del widget
        if widget.layout() is None:
            layout = QVBoxLayout(widget)
            widget.setLayout(layout)
        else:
            layout = widget.layout()
            while layout.count():
                item = layout.takeAt(0)
                widget_to_remove = item.widget()
                if widget_to_remove is not None:
                    widget_to_remove.setParent(None)
                    widget_to_remove.deleteLater()
                else:
                    layout.removeItem(item)

        # Crear figura y ejes
        fig = plt.figure(dpi=100)
        fig.set_tight_layout(True)
        gs = GridSpec(2, 1, height_ratios=[4, 1])
        ax = fig.add_subplot(gs[0], projection='3d')
        ax.set_box_aspect([1, 1, 1])

        datax = df['Este']
        datay = df['Norte']
        dataz = df['Nivel']

        def agregar_margen(valores, porcentaje=0.1):
            minimo = np.min(valores)
            maximo = np.max(valores)
            rango = maximo - minimo
            margen = rango * porcentaje if rango > 0 else 1
            return minimo - margen, maximo + margen

        xlim = agregar_margen(datax)
        ylim = agregar_margen(datay)
        zlim = agregar_margen(dataz)
        ax.set_xlim(*xlim)
        ax.set_ylim(*ylim)
        ax.set_zlim(*zlim)

        ax.scatter([], [], color='black', s=25, label='Punto inicial')
        ax.scatter([], [], color='red', s=25, label='Punto final')

        arrows = []

        for idinstrumento, datos_equipo in df.groupby('Instrumento'):
            nombreprisma = str(datos_equipo['Nombre'].iloc[0])
            x = datos_equipo['Este']
            y = datos_equipo['Norte']
            z = datos_equipo['Nivel']

            punto_inicial = f'({round(x.iloc[0],3)}, {round(y.iloc[0],3)}, {round(z.iloc[0],3)})'
            punto_final = f'({round(x.iloc[-1],3)}, {round(y.iloc[-1],3)}, {round(z.iloc[-1],3)})'

            trajectory, = ax.plot([], [], [], linewidth=2, 
                                label=f'{nombreprisma}: [{punto_inicial}, {punto_final}]')
            ax.scatter(x.iloc[0], y.iloc[0], z.iloc[0], color='black', s=25)
            ax.scatter(x.iloc[-1], y.iloc[-1], z.iloc[-1], color='red', s=25)

            if tipo == "estatico":
                trajectory.set_data(x, y)
                trajectory.set_3d_properties(z)
                if len(x) > 1:
                    arrow = ax.quiver(
                        x.iloc[-2], y.iloc[-2], z.iloc[-2],
                        x.iloc[-1] - x.iloc[-2], 
                        y.iloc[-1] - y.iloc[-2], 
                        z.iloc[-1] - z.iloc[-2],
                        color='r', linewidth=2, arrow_length_ratio=0.5
                    )
                    arrows.append(arrow)

            elif tipo == "animado":
                if len(x) > 1:
                    arrow = ax.quiver(
                        x.iloc[0], y.iloc[0], z.iloc[0],
                        x.iloc[1] - x.iloc[0], 
                        y.iloc[1] - y.iloc[0], 
                        z.iloc[1] - z.iloc[0],
                        color='r', linewidth=2, arrow_length_ratio=0.5
                    )
                    arrows.append(arrow)

                    def update(num, x, y, z, trajectory, arrow_list):
                        if num > 0:
                            trajectory.set_data(x[:num+1], y[:num+1])
                            trajectory.set_3d_properties(z[:num+1])
                        if num < len(x) - 1:
                            if arrow_list and arrow_list[0]:
                                arrow_list[0].remove()
                                arrow_list[0] = None
                            arrow_list[0] = ax.quiver(
                                x.iloc[num], y.iloc[num], z.iloc[num],
                                x.iloc[num+1] - x.iloc[num], 
                                y.iloc[num+1] - y.iloc[num], 
                                z.iloc[num+1] - z.iloc[num],
                                color='r', linewidth=2, arrow_length_ratio=0.5
                            )

                    arrow_ref = [arrow]
                    timer = QTimer()
                    widget.timer = timer
                    current_frame = 0

                    def advance_frame():
                        nonlocal current_frame
                        # =====================================================
                        # CORRECCIÓN 2: Validar canvas antes de dibujar
                        # =====================================================
                        if not hasattr(widget, 'canvas') or widget.canvas is None:
                            timer.stop()
                            return
                        try:
                            if current_frame < len(x) - 1:
                                update(current_frame, x, y, z, trajectory, arrow_ref)
                                current_frame += 1
                                widget.canvas.draw_idle()
                            else:
                                timer.stop()
                        except RuntimeError:
                            # Canvas destruido, detener timer
                            timer.stop()
                        # =====================================================

                    timer.timeout.connect(advance_frame)
                    timer.setInterval(50)

        ax.plot([0, 0], [0, 0], [np.min(dataz), np.max(dataz)], 
                'gray', linestyle='--', linewidth=1)
        ax.plot([0, 0], [np.min(datay), np.max(datay)], [0, 0], 
                'gray', linestyle='--', linewidth=1)
        ax.plot([np.min(datax), np.max(datax)], [0, 0], [0, 0], 
                'gray', linestyle='--', linewidth=1)

        ax.set_title('Trayectoria de los prismas', fontsize=10)
        ax.set_xlabel('Este (m)', labelpad=9)
        ax.set_ylabel('Norte (m)', labelpad=9)
        ax.set_zlabel('Elevación (m)', labelpad=9)

        config = SoftwareConfiguracion.obtenerDataSoftware()
        decimales = config[14]
        ax.xaxis.set_major_formatter(
            plt.FuncFormatter(lambda val, pos: '{:.{}f}'.format(val, decimales)))
        ax.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda val, pos: '{:.{}f}'.format(val, decimales)))
        ax.zaxis.set_major_formatter(
            plt.FuncFormatter(lambda val, pos: '{:.{}f}'.format(val, decimales)))

        legend_ax = fig.add_subplot(gs[1])
        legend_ax.axis('off')
        legend_ax.legend(*ax.get_legend_handles_labels(), loc="upper center", prop={'size': 7})

        canvas = FigureCanvas(fig)
        layout.addWidget(canvas)
        canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        widget.canvas = canvas
        widget.ax = ax
        widget.fig = fig

        # =========================================================
        # CORRECCIÓN 3: Siempre crear nueva función y reconectar
        # =========================================================
        def cambiarVistas():
            # Validar que canvas y ax siguen vivos
            if not hasattr(widget, 'canvas') or widget.canvas is None:
                return
            if not hasattr(widget, 'ax') or widget.ax is None:
                return
            try:
                selected_option = combovistas.currentData()
                vista_config = {
                    "Frontal":    (0,   0,    0),
                    "Isometrica": (30,  45,   0),
                    "Planta":     (90,  -90,  0),
                    "Bottom":     (180, 0,    0),
                    "Left":       (0,   270,  0),
                    "Right":      (0,   90,   0),
                    "Posterior":  (0,   180,  0),
                    "Inclinada":  (45,  45,   0),
                    "Perfil":     (0,   -90,  0)
                }
                if selected_option in vista_config:
                    elev, azim, roll = vista_config[selected_option]
                    widget.ax.view_init(elev=elev, azim=azim, roll=roll)
                    widget.canvas.draw()
            except RuntimeError:
                # Canvas ya destruido, ignorar
                pass

        # Guardar referencia y conectar
        widget._cambiar_vistas_slot = cambiarVistas
        combovistas.activated.connect(cambiarVistas)
        # =========================================================

        # Vista inicial
        cambiarVistas()

        # Iniciar animación
        if tipo == "animado" and hasattr(widget, "timer") and widget.timer:
            widget.timer.start()
        
        plt.close(fig)