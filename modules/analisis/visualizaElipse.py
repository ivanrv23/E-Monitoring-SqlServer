import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from PySide6.QtWidgets import (QVBoxLayout, QWidget, QSizePolicy, QTabWidget, QVBoxLayout,QMessageBox)
from scipy.stats import chi2
from matplotlib.patches import Ellipse
from modules.empresa.softwareconfiguracion import SoftwareConfiguracion
from utils.generic.calculardesviaciones import CalcularDesviaciones 
from controllers.AnalisisController import AnalisisController

class CanvasAjustable(FigureCanvas):
    """FigureCanvas optimizado con autoajuste y barra de herramientas"""
    def __init__(self, parent=None, width=5, height=4, dpi=100, projection=None):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.ax = self.fig.add_subplot(111, projection=projection) if projection else self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.updateGeometry()

    def resizeEvent(self, event):
        """Redimensionamiento automático"""
        super().resizeEvent(event)
        try:
            self.fig.tight_layout(pad=2.0)
        except:
            self.fig.subplots_adjust(left=0.15, right=0.85, bottom=0.15, top=0.9)
        self.draw()

class VisualizacionElipse:
    @staticmethod
    def convertir_unidades(datos, unidad):
        if unidad == 'cm':
            return [(id, este * 100, norte * 100, cota * 100) for id, este, norte, cota in datos]
        elif unidad == 'mm':
            return [(id, este * 1000, norte * 1000, cota * 1000) for id, este, norte, cota in datos]
        else:  # 'm' o cualquier otra cosa, se mantiene en metros
            return datos

    @staticmethod
    def graficarElipseError(idproyecto, nombreprisma, widget_elipse, widget_primera_desviacion, widget_segunda_desviacion, widget_tercera_desviacion, datos, unidad,combo_vistas_elipsoide_3d,valores_ejes):
        desviaciones = AnalisisController.ctrlObtenerDesviacionesPrisma(idproyecto, nombreprisma)
        if desviaciones:
            try:
                # Convertir datos a la unidad especificada
                datos = VisualizacionElipse.convertir_unidades(datos, unidad)
                # Configuración inicial
                plt.style.use('seaborn-v0_8-notebook')
                plt.rcParams.update({
                    'font.size': 9,
                    'axes.labelpad': 10,
                    'xtick.major.pad': 6,
                    'ytick.major.pad': 6
                })

                if unidad in ['cm', 'mm', 'm']:
                    # Calcular el acumulado de las coordenadas
                    def calcular_acumulado(datos):
                        acumulado = [(datos[0][0], 0, 0, 0)]  # El primer valor es (id, 0, 0, 0)
                        primer_valor = datos[0]
                        for i in range(1, len(datos)):
                            id = datos[i][0]
                            este_acumulado = datos[i][1] - primer_valor[1]
                            norte_acumulado = datos[i][2] - primer_valor[2]
                            cota_acumulado = datos[i][3] - primer_valor[3]
                            acumulado.append((id, este_acumulado, norte_acumulado, cota_acumulado))
                        return acumulado

                    datos_acumulados = calcular_acumulado(datos)
                else:
                    datos_acumulados = datos

                # Procesamiento de datos acumulados
                datos_este = [d[1] for d in datos_acumulados if d[1] is not None]
                datos_norte = [d[2] for d in datos_acumulados if d[2] is not None]
                datos_elevacion = [d[3] for d in datos_acumulados if d[3] is not None]

                # Usar el punto inicial como centro
                centro_este = datos_este[0]
                centro_norte = datos_norte[0]
                centro_elevacion = datos_elevacion[0]

                stats = {
                    'este': {
                        'media': centro_este,  # Usar el punto inicial como centro
                        'std': np.std(datos_este),
                        'data': datos_este,
                        'color': '#0A0A0A', 
                        'label': 'Este (m)' if unidad not in ['cm', 'mm', 'm'] else f'Este Acumulado ({unidad})'
                    },
                    'norte': {
                        'media': centro_norte,  # Usar el punto inicial como centro
                        'std': np.std(datos_norte),
                        'data': datos_norte,
                        'color': '#0A0A0A',
                        'label': 'Norte (m)' if unidad not in ['cm', 'mm', 'm'] else f'Norte Acumulado ({unidad})'
                    },
                    'elevacion': {
                        'media': centro_elevacion,  # Usar el punto inicial como centro
                        'std': np.std(datos_elevacion),
                        'data': datos_elevacion,
                        'color': '#0A0A0A',
                        'label': 'Cota (msnm)' if unidad not in ['cm', 'mm', 'm'] else f'Cota Acumulada ({unidad})'
                    }
                }

                # Configuración de pestañas
                tab_widget = QTabWidget()

                # Pestaña 2D - Elipse con límites mejorados
                widget_2d = QWidget()
                layout_2d = QVBoxLayout(widget_2d)
                canvas_2d = VisualizacionElipse._crear_grafica_elipse_2d(layout_2d, stats, datos_este, datos_norte, desviaciones, unidad, nombreprisma,valores_ejes)

                # Añadir barra de herramientas para 2D
                toolbar_2d = NavigationToolbar(canvas_2d, widget_2d)
                layout_2d.addWidget(toolbar_2d)

                tab_widget.addTab(widget_2d, "Vista 2D")

                # Pestaña 3D - Elipsoide con límites ajustados
                widget_3d = QWidget()
                layout_3d = QVBoxLayout(widget_3d)
                canvas_3d = VisualizacionElipse._crear_grafica_elipsoide_3d(layout_3d, stats, datos_este, datos_norte, datos_elevacion, desviaciones, unidad, combo_vistas_elipsoide_3d, nombreprisma)

                # Añadir barra de herramientas para 3D
                toolbar_3d = NavigationToolbar(canvas_3d, widget_3d)
                layout_3d.addWidget(toolbar_3d)

                tab_widget.addTab(widget_3d, "Vista 3D")

                # Layout principal
                layout = VisualizacionElipse._preparar_layout(widget_elipse)
                layout.addWidget(tab_widget)

                # Gráficas de campana
                VisualizacionElipse._crear_grafica_desviacion(widget_primera_desviacion, f'Este (m)' if unidad not in ['cm', 'mm', 'm'] else f'Este Acumulado ({unidad})','este', "Distribución Coordenada Este", desviaciones,unidad)
                VisualizacionElipse._crear_grafica_desviacion(widget_segunda_desviacion, f'Norte (m)' if unidad not in ['cm', 'mm', 'm'] else f'Norte Acumulado ({unidad})','norte', "Distribución Coordenada Norte", desviaciones,unidad)
                VisualizacionElipse._crear_grafica_desviacion(widget_tercera_desviacion, f'Cota (msnm)' if unidad not in ['cm', 'mm', 'm'] else f'Cota Acumulada ({unidad})', 'cota',"Distribución Coordenada Cota", desviaciones,unidad)


            except Exception as e:
                print(f"Error: {str(e)}")
        else:
            # Mostrar diálogo personalizado para seleccionar la fecha de cálculo
            fecha_calculo = CalcularDesviaciones.crear_dialogo_fecha_calculo()
            if fecha_calculo:
                # Obtener los datos crudos
                datos_crudos = AnalisisController.ctrlObtenerDataDesviacionesPrisma(idproyecto, fecha_calculo,nombreprisma)
                
                # Calcular y guardar las desviaciones
                resultado = CalcularDesviaciones.calcular_y_guardar_desviaciones(idproyecto, datos_crudos, fecha_calculo)
                
                if resultado:
                    QMessageBox.information(None, "Éxito", "Desviaciones calculadas y guardadas correctamente")
                else:
                    QMessageBox.warning(None, "Error", "No se pudieron guardar las desviaciones")

    @staticmethod
    def _crear_grafica_elipse_2d(layout, stats, datos_este, datos_norte, desviaciones, unidad, nombreprisma, valores_ejes):
        """Gráfica 2D que se ajusta dinámicamente al espacio disponible con grilla"""
        try:
            # Desempaquetar los valores del arreglo
            ejexmin, ejexmax, intervalo_principal_x, intervalo_secundario_x, ejeymin, ejeymax, intervalo_principal_y, intervalo_secundario_y = valores_ejes

            canvas = CanvasAjustable()
            ax = canvas.ax

            # Configuración de estilo
            colores_sigma = {
                1: {'line': '#008F39', 'alpha': 1.0},
                2: {'line': '#FFA500', 'alpha': 1.0},
                3: {'line': '#FF0000', 'alpha': 1.0},
                'outside': {'line': '#808080', 'alpha': 1.0}
            }

            # Factor de conversión de unidades
            if unidad == 'm':
                factor = 1
            elif unidad == 'cm':
                factor = 100
            elif unidad == 'mm':
                factor = 1000
            else:
                factor = 1

            # Ajustar valores de ejes según la unidad
            ejexmin *= factor
            ejexmax *= factor
            intervalo_principal_x *= factor
            intervalo_secundario_x *= factor
            ejeymin *= factor
            ejeymax *= factor
            intervalo_principal_y *= factor
            intervalo_secundario_y *= factor

            # Calcular dimensiones base de la elipse usando desviaciones de la base de datos
            desviacion_este_1 = desviaciones[0][4] * factor
            desviacion_este_2 = (desviaciones[0][4] * 2) * factor
            desviacion_este_3 = (desviaciones[0][4] * 3) * factor
            desviacion_norte_1 = desviaciones[0][6] * factor
            desviacion_norte_2 = (desviaciones[0][6] * 2) * factor
            desviacion_norte_3 = (desviaciones[0][6] * 3) * factor

            # Margen dinámico (10% del tamaño de la elipse o 0.5 std)
            margin_x = max(2 * desviacion_este_3 * 0.1, stats['este']['std'] * 0.5)
            margin_y = max(2 * desviacion_norte_3 * 0.1, stats['norte']['std'] * 0.5)

            # Calcular límites del contenido (elipse + puntos)
            all_x = stats['este']['data'] + [stats['este']['media'] - desviacion_este_3,
                                            stats['este']['media'] + desviacion_este_3]
            all_y = stats['norte']['data'] + [stats['norte']['media'] - desviacion_norte_3,
                                            stats['norte']['media'] + desviacion_norte_3]

            content_xmin, content_xmax = min(all_x), max(all_x)
            content_ymin, content_ymax = min(all_y), max(all_y)

            # Añadir márgenes al contenido
            x_min = content_xmin - margin_x
            x_max = content_xmax + margin_x
            y_min = content_ymin - margin_y
            y_max = content_ymax + margin_y

            # Configuración inicial de ejes
            ax.set_title(f"Elipse de Desviaciones - {nombreprisma}", pad=8, fontsize=10)
            ax.set_xlabel(stats['este']['label'], labelpad=5, fontsize=9)
            ax.set_ylabel(stats['norte']['label'], labelpad=5, fontsize=9)

            # Ajustar los límites de los ejes si se proporcionan valores distintos de cero
            if ejexmin != 0 or ejexmax != 0:
                x_min = ejexmin
                x_max = ejexmax

            if ejeymin != 0 or ejeymax != 0:
                y_min = ejeymin
                y_max = ejeymax

            
            # Configurar grilla usando intervalos principales y secundarios
            if intervalo_principal_x != 0:
                ticks = np.arange(x_min, x_max + intervalo_principal_x, intervalo_principal_x)
                # Asegurarse de que los valores mínimo y máximo estén incluidos
                if x_min not in ticks:
                    ticks = np.insert(ticks, 0, x_min)
                if x_max not in ticks:
                    ticks = np.append(ticks, x_max)
                ax.set_xticks(ticks)

            if intervalo_secundario_x != 0:
                for tick in np.arange(x_min, x_max, intervalo_secundario_x):
                    ax.axvline(x=tick, color='gray', linestyle='--', linewidth=0.5)

            if intervalo_principal_y != 0:
                ticks = np.arange(y_min, y_max + intervalo_principal_y, intervalo_principal_y)
                # Asegurarse de que los valores mínimo y máximo estén incluidos
                if y_min not in ticks:
                    ticks = np.insert(ticks, 0, y_min)
                if y_max not in ticks:
                    ticks = np.append(ticks, y_max)
                ax.set_yticks(ticks)

            if intervalo_secundario_y != 0:
                for tick in np.arange(y_min, y_max, intervalo_secundario_y):
                    ax.axhline(y=tick, color='gray', linestyle='--', linewidth=0.5)

            # Aplicar los límites de los ejes
            ax.set_xlim(x_min, x_max)
            ax.set_ylim(y_min, y_max)

            # Configurar grilla
            ax.grid(True, which='both', linestyle=':', linewidth=0.5, alpha=0.5, color='gray')
            ax.set_axisbelow(True)

            # Configurar el formato de los valores en los ejes
            config = SoftwareConfiguracion.obtenerDataSoftware()
            decimales = config[14]
            ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda val, pos: '{:.{}f}'.format(val, decimales)))
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda val, pos: '{:.{}f}'.format(val, decimales)))
            plt.setp(ax.get_xticklabels(), rotation=90, ha="center")

            # Dibujar elementos
            ellipses = []
            for n in [1, 2, 3]:
                if n == 1:
                    width = 2 * desviacion_este_1
                    height = 2 * desviacion_norte_1
                elif n == 2:
                    width = 2 * desviacion_este_2
                    height = 2 * desviacion_norte_2
                elif n == 3:
                    width = 2 * desviacion_este_3
                    height = 2 * desviacion_norte_3

                ellipse = Ellipse(
                    (stats['este']['media'], stats['norte']['media']),
                    width=width,
                    height=height,
                    angle=0,
                    fill=False,
                    edgecolor=colores_sigma[n]['line'],
                    linewidth=1.5,
                    alpha=colores_sigma[n]['alpha'],
                    zorder=5
                )
                ax.add_patch(ellipse)
                ellipses.append(ellipse)

            # Graficar puntos y unirlos con líneas
            line, = ax.plot(datos_este, datos_norte, color='#007FFF', alpha=0.8, linewidth=1.5, zorder=9)
            scatter = ax.scatter(
                datos_este,
                datos_norte,
                color='#007FFF',
                alpha=0.8,
                s=35,
                edgecolors='blue',
                linewidths=0.6,
                zorder=10
            )

            # Resaltar el primer y Punto Final
            initial_point = ax.scatter(
                [stats['este']['media']], [stats['norte']['media']],
                color='black', label='Punto Inicial', zorder=11, s=50, edgecolors='white', linewidths=0.6
            )
            final_point = ax.scatter(
                [datos_este[-1]], [datos_norte[-1]],
                color='red', label='Punto Final', zorder=11, s=50, edgecolors='white', linewidths=0.6
            )

            # Calcular puntos dentro y fuera de cada desviación
            def count_points_within_ellipse(dx, dy, desv_este, desv_norte):
                return (dx / desv_este) ** 2 + (dy / desv_norte) ** 2 <= 1

            dx = np.array(datos_este) - stats['este']['media']
            dy = np.array(datos_norte) - stats['norte']['media']

            mask_1sigma = count_points_within_ellipse(dx, dy, desviacion_este_1, desviacion_norte_1)
            mask_2sigma = count_points_within_ellipse(dx, dy, desviacion_este_2, desviacion_norte_2) & ~mask_1sigma
            mask_3sigma = count_points_within_ellipse(dx, dy, desviacion_este_3, desviacion_norte_3) & ~mask_1sigma & ~mask_2sigma
            mask_outside = ~(mask_1sigma | mask_2sigma | mask_3sigma)

            count_1sigma = np.sum(mask_1sigma)
            count_2sigma = np.sum(mask_2sigma)
            count_3sigma = np.sum(mask_3sigma)
            count_outside_3sigma = np.sum(mask_outside)

            # Calcular porcentajes
            total_lecturas = len(datos_este)
            percent_1sigma = (count_1sigma / total_lecturas) * 100
            percent_2sigma = (count_2sigma / total_lecturas) * 100
            percent_3sigma = (count_3sigma / total_lecturas) * 100
            percent_outside_3sigma = (count_outside_3sigma / total_lecturas) * 100

            # Leyenda compacta
            handles = []
            labels = []
            handles.append(plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='black', markersize=8, label='Punto Inicial'))
            handles.append(plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markersize=8, label='Punto Final'))

            handles.append(plt.Line2D([0], [0], color=colores_sigma[1]['line'], label=f'1 σ ({count_1sigma}-->{percent_1sigma:.1f}%)'))
            handles.append(plt.Line2D([0], [0], color=colores_sigma[2]['line'], label=f'2 σ ({count_2sigma}-->{percent_2sigma:.1f}%)'))
            handles.append(plt.Line2D([0], [0], color=colores_sigma[3]['line'], label=f'3 σ ({count_3sigma}-->{percent_3sigma:.1f}%)'))
            handles.append(plt.Line2D([0], [0], color=colores_sigma['outside']['line'], label=f'Fuera de 3 σ ({count_outside_3sigma}-->{percent_outside_3sigma:.1f}%)'))

            handles.append(plt.Line2D([0], [0], color='w', label=f'Total de lecturas: {total_lecturas}', linestyle='None'))
            leg = ax.legend(handles=handles, bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0.3,
                            frameon=True, fontsize=8, framealpha=0.9, markerscale=0.8)

            # Función para marcar/desmarcar líneas al hacer clic en la leyenda
            lined = dict()
            for legline, mask in zip(leg.get_lines()[2:6], [mask_1sigma, mask_2sigma, mask_3sigma, mask_outside]):
                legline.set_picker(True)
                lined[legline] = mask

            visibility_state = {id(mask): True for mask in [mask_1sigma, mask_2sigma, mask_3sigma, mask_outside]}

            def on_pick(event):
                legline = event.artist
                mask = lined[legline]
                mask_id = id(mask)

                visibility_state[mask_id] = not visibility_state[mask_id]

                current_alpha = scatter.get_alpha()

                new_alpha = np.where(mask, 0.8 if visibility_state[mask_id] else 0.0, current_alpha)
                scatter.set_alpha(new_alpha)

                visible_points = new_alpha > 0
                visible_este = np.array(datos_este)[visible_points]
                visible_norte = np.array(datos_norte)[visible_points]

                if len(visible_este) > 0:
                    initial_point.set_offsets([visible_este[0], visible_norte[0]])
                    initial_point.set_alpha(0.8)

                    final_point.set_offsets([visible_este[-1], visible_norte[-1]])
                    final_point.set_alpha(0.8)
                else:
                    initial_point.set_alpha(0.0)
                    final_point.set_alpha(0.0)

                line.set_data(visible_este, visible_norte)
                legline.set_alpha(1.0 if visibility_state[mask_id] else 0.2)
                canvas.draw_idle()

            canvas.mpl_connect('pick_event', on_pick)

            def on_resize(event):
                canvas.fig.tight_layout(pad=1.0)

            canvas.mpl_connect('resize_event', on_resize)

            canvas.fig.tight_layout(pad=1.0)
            layout.addWidget(canvas)
            return canvas
        except Exception as e:
            print(f"Error: {e}")
            return None

    @staticmethod
    def _crear_grafica_elipsoide_3d(layout, stats, datos_este, datos_norte, datos_elevacion, desviaciones, unidad, combo_vistas_elipsoide_3d, nombreprisma):
        try:
            canvas = CanvasAjustable(projection='3d')
            ax = canvas.ax

            # Configuración de estilo
            colores_sigma = {
                1: {'color': '#008F39', 'alpha': 0.3, 'label': '1σ'},
                2: {'color': '#FFA500', 'alpha': 0.25, 'label': '2σ'},
                3: {'color': '#FF0000', 'alpha': 0.2, 'label': '3σ'},
                'outside': {'color': '#808080', 'alpha': 0.2, 'label': 'Fuera de 3σ'}
            }

            # Calcular dimensiones base del elipsoide usando desviaciones de la base de datos
            if unidad == 'm':
                factor = 1
            elif unidad == 'cm':
                factor = 100
            elif unidad == 'mm':
                factor = 1000
            else:
                factor = 1

            # Cálculo de desviaciones
            desviacion_este_1 = desviaciones[0][4] * factor
            desviacion_este_2 = (desviaciones[0][4]*2) * factor
            desviacion_este_3 = (desviaciones[0][4]*3) * factor
            desviacion_norte_1 = desviaciones[0][6] * factor
            desviacion_norte_2 = (desviaciones[0][6]*2) * factor
            desviacion_norte_3 = (desviaciones[0][6]*3) * factor
            desviacion_elevacion_1 = desviaciones[0][8] * factor
            desviacion_elevacion_2 = (desviaciones[0][8]*2) * factor
            desviacion_elevacion_3 = (desviaciones[0][8]*3) * factor

            means = np.array([stats['este']['media'], stats['norte']['media'], stats['elevacion']['media']])

            # Dibujar elipsoides
            for n in [1, 2, 3]:
                if n == 1:
                    radii = [desviacion_este_1, desviacion_norte_1, desviacion_elevacion_1]
                elif n == 2:
                    radii = [desviacion_este_2, desviacion_norte_2, desviacion_elevacion_2]
                elif n == 3:
                    radii = [desviacion_este_3, desviacion_norte_3, desviacion_elevacion_3]

                def dibujar_elipsoide(ax, means, radii, n, color, alpha, label):
                    u = np.linspace(0.0, 2.0 * np.pi, 30)
                    v = np.linspace(0.0, np.pi, 30)
                    x = radii[0] * np.outer(np.cos(u), np.sin(v))
                    y = radii[1] * np.outer(np.sin(u), np.sin(v))
                    z = radii[2] * np.outer(np.ones(np.size(u)), np.cos(v))
                    ax.plot_wireframe(x + means[0], y + means[1], z + means[2], color=color, alpha=alpha, rstride=2, cstride=2)

                dibujar_elipsoide(ax, means, radii, n, colores_sigma[n]['color'], colores_sigma[n]['alpha'], colores_sigma[n]['label'])

            # Configuración de ejes
            max_radius = max(desviacion_este_3, desviacion_norte_3, desviacion_elevacion_3)
            margin = max_radius * 0.35
            x_limits = [means[0] - max_radius - margin, means[0] + max_radius + margin]
            y_limits = [means[1] - max_radius - margin, means[1] + max_radius + margin]
            z_limits = [means[2] - max_radius - margin, means[2] + max_radius + margin]

            ax.set_title(f"Elipsoide de Desviaciones - {nombreprisma}", pad=15)
            pad_x, pad_y, pad_z = 10, 10, 10
            if unidad == 'cor':
                pad_x, pad_y, pad_z = 17, 17, 15

            ax.set_xlabel(stats['este']['label'], labelpad=pad_x)
            ax.set_ylabel(stats['norte']['label'], labelpad=pad_y)
            ax.set_zlabel(stats['elevacion']['label'], labelpad=pad_z)
            ax.set_xlim(x_limits)
            ax.set_ylim(y_limits)
            ax.set_zlim(z_limits)
            ax.grid(True, linestyle=':', alpha=0.5)
            config = SoftwareConfiguracion.obtenerDataSoftware()
            decimales = config[14]
            ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda val, pos: '{:.{}f}'.format(val, decimales)))
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda val, pos: '{:.{}f}'.format(val, decimales)))
            ax.zaxis.set_major_formatter(plt.FuncFormatter(lambda val, pos: '{:.{}f}'.format(val, decimales)))

            # Ajustar los ticks de los ejes
            if unidad == 'cor':
                ax.set_xticks(np.linspace(x_limits[0], x_limits[1], 4))
                ax.set_yticks(np.linspace(y_limits[0], y_limits[1], 4))
                ax.set_zticks(np.linspace(z_limits[0], z_limits[1], 4))
            else:
                ax.set_xticks(np.linspace(x_limits[0], x_limits[1], 5))
                ax.set_yticks(np.linspace(y_limits[0], y_limits[1], 5))
                ax.set_zticks(np.linspace(z_limits[0], z_limits[1], 5))
            # Rotar las etiquetas de los ejes x, y, z en 90 grados
            # ax.tick_params(axis='x', labelrotation=90)
            # ax.tick_params(axis='y', labelrotation=90)
            # ax.tick_params(axis='z', labelrotation=90)

            # Puntos de datos
            line, = ax.plot(datos_este, datos_norte, datos_elevacion, color='#007FFF', alpha=0.8, linewidth=1.5, zorder=9)
            scatter = ax.scatter(datos_este, datos_norte, datos_elevacion, color='#007FFF', alpha=0.4, s=40, edgecolors='blue', linewidth=0.8, depthshade=True, zorder=10)

            # Resaltar el primer y Punto Final
            initial_point = ax.scatter([datos_este[0]], [datos_norte[0]], [datos_elevacion[0]], color='black', label='Punto Inicial', zorder=11, s=50, edgecolors='white', linewidths=0.8)
            final_point = ax.scatter([datos_este[-1]], [datos_norte[-1]], [datos_elevacion[-1]], color='red', label='Punto Final', zorder=11, s=50, edgecolors='white', linewidths=0.8)

            # Calcular puntos dentro y fuera de cada desviación
            def count_points_within_ellipsoid(dx, dy, dz, desv_este, desv_norte, desv_elevacion):
                return (dx / desv_este) ** 2 + (dy / desv_norte) ** 2 + (dz / desv_elevacion) ** 2 <= 1

            dx = np.array(datos_este) - stats['este']['media']
            dy = np.array(datos_norte) - stats['norte']['media']
            dz = np.array(datos_elevacion) - stats['elevacion']['media']

            mask_1sigma = count_points_within_ellipsoid(dx, dy, dz, desviacion_este_1, desviacion_norte_1, desviacion_elevacion_1)
            mask_2sigma = count_points_within_ellipsoid(dx, dy, dz, desviacion_este_2, desviacion_norte_2, desviacion_elevacion_2) & ~mask_1sigma
            mask_3sigma = count_points_within_ellipsoid(dx, dy, dz, desviacion_este_3, desviacion_norte_3, desviacion_elevacion_3) & ~mask_1sigma & ~mask_2sigma
            mask_outside = ~(mask_1sigma | mask_2sigma | mask_3sigma)

            count_1sigma = np.sum(mask_1sigma)
            count_2sigma = np.sum(mask_2sigma)
            count_3sigma = np.sum(mask_3sigma)
            count_outside_3sigma = np.sum(mask_outside)

            # Calcular porcentajes
            total_lecturas = len(datos_este)
            percent_1sigma = (count_1sigma / total_lecturas) * 100
            percent_2sigma = (count_2sigma / total_lecturas) * 100
            percent_3sigma = (count_3sigma / total_lecturas) * 100
            percent_outside_3sigma = (count_outside_3sigma / total_lecturas) * 100

            # Leyenda compacta
            handles = [
                plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='black', markersize=8, label='Punto Inicial', linewidth=2.5),
                plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markersize=8, label='Punto Final', linewidth=2.5),
                plt.Line2D([0], [0], color=colores_sigma[1]['color'], label=f'1 σ ({count_1sigma}-->{percent_1sigma:.1f}%)', linewidth=2.5),
                plt.Line2D([0], [0], color=colores_sigma[2]['color'], label=f'2 σ ({count_2sigma}-->{percent_2sigma:.1f}%)', linewidth=2.5),
                plt.Line2D([0], [0], color=colores_sigma[3]['color'], label=f'3 σ ({count_3sigma}-->{percent_3sigma:.1f}%)', linewidth=2.5),
                plt.Line2D([0], [0], color=colores_sigma['outside']['color'], label=f'Fuera de 3 σ ({count_outside_3sigma}-->{percent_outside_3sigma:.1f}%)', linewidth=2.5),
                plt.Line2D([0], [0], color='w', label=f'Total de lecturas: {total_lecturas}', linestyle='None')
            ]
            leg = ax.legend(handles=handles, bbox_to_anchor=(0.5, -0.2), loc='upper center', borderaxespad=0., frameon=True, fontsize=8, framealpha=0.9, markerscale=0.8, ncol=3)

            # Función para marcar/desmarcar líneas al hacer clic en la leyenda
            lined = dict()
            for legline, mask in zip(leg.get_lines()[2:6], [mask_1sigma, mask_2sigma, mask_3sigma, mask_outside]):
                legline.set_picker(True)
                lined[legline] = mask

            visibility_state = {id(mask): True for mask in [mask_1sigma, mask_2sigma, mask_3sigma, mask_outside]}

            def on_pick(event):
                try:
                    legline = event.artist
                    mask = lined[legline]
                    mask_id = id(mask)
                    visibility_state[mask_id] = not visibility_state[mask_id]

                    visible_points = np.array([visibility_state[id(mask_1sigma)] & mask_1sigma[i] or
                                            visibility_state[id(mask_2sigma)] & mask_2sigma[i] or
                                            visibility_state[id(mask_3sigma)] & mask_3sigma[i] or
                                            visibility_state[id(mask_outside)] & mask_outside[i]
                                            for i in range(len(datos_este))])

                    visible_este = np.array(datos_este)[visible_points]
                    visible_norte = np.array(datos_norte)[visible_points]
                    visible_elevacion = np.array(datos_elevacion)[visible_points]

                    scatter._offsets3d = (visible_este, visible_norte, visible_elevacion)

                    if len(visible_este) > 0:
                        initial_point._offsets3d = ([visible_este[0]], [visible_norte[0]], [visible_elevacion[0]])
                        initial_point.set_alpha(0.8)
                        final_point._offsets3d = ([visible_este[-1]], [visible_norte[-1]], [visible_elevacion[-1]])
                        final_point.set_alpha(0.8)
                    else:
                        initial_point.set_alpha(0.0)
                        final_point.set_alpha(0.0)

                    line.set_data(visible_este, visible_norte)
                    line.set_3d_properties(visible_elevacion)

                    legline.set_alpha(1.0 if visibility_state[mask_id] else 0.2)
                    canvas.draw_idle()
                except Exception as e:
                    print(f"Error en on_pick: {e}")

            canvas.mpl_connect('pick_event', on_pick)

            # Vista inicial optimizada
            ax.view_init(elev=30, azim=-45)
            canvas.fig.tight_layout(pad=2.5)
            canvas.fig.subplots_adjust(bottom=0.25)
            layout.addWidget(canvas)

            # Conexión de la señal para cambiar vistas
            def on_combo_activated():
                try:
                    if canvas and ax:
                        selected_option = combo_vistas_elipsoide_3d.currentData()
                        vista_config = {
                            "Frontal": (0, 0, 0),
                            "Isometrica": (30, 45, 0),
                            "Planta": (90, -90, 0),
                            "Bottom": (180, 0, 0),
                            "Left": (0, 270, 0),
                            "Right": (0, 90, 0),
                            "Posterior": (0, 180, 0),
                            "Inclinada": (45, 45, 0),
                            "Perfil": (0, -90, 0)
                        }
                        elev, azim, roll = vista_config[selected_option]
                        ax.view_init(elev=elev, azim=azim, roll=roll)
                        canvas.draw()
                except Exception as e:
                    print(f"Error al cambiar vista: {e}")

            combo_vistas_elipsoide_3d.activated.connect(on_combo_activated)
            on_combo_activated()
            return canvas
        except Exception as e:
            print(f"Error al crear gráfica: {e}")
            return None

    @staticmethod
    def _dibujar_elipsoide_3d(ax, means, cov, n_sigma=1, color='r', alpha=0.1, label=None, scale_factor=1.0):
        try:
            radius = np.sqrt(chi2.ppf(0.683, df=3)) * n_sigma * scale_factor
            vals, vecs = np.linalg.eigh(cov)
            order = vals.argsort()[::-1]
            vals, vecs = vals[order], vecs[:, order]
            u = np.linspace(0, 2 * np.pi, 32)
            v = np.linspace(0, np.pi, 16)
            x = np.outer(np.cos(u), np.sin(v))
            y = np.outer(np.sin(u), np.sin(v))
            z = np.outer(np.ones_like(u), np.cos(v))
            x_transformed = np.zeros_like(x)
            y_transformed = np.zeros_like(y)
            z_transformed = np.zeros_like(z)
            for i in range(x.shape[0]):
                for j in range(x.shape[1]):
                    [x_transformed[i,j], y_transformed[i,j], z_transformed[i,j]] = np.dot(
                        vecs,
                        np.sqrt(vals) * np.array([x[i,j], y[i,j], z[i,j]])
                    ) * radius + means
            ax.plot_wireframe(
                x_transformed,
                y_transformed,
                z_transformed,
                rstride=1,
                cstride=1,
                color=color,
                alpha=alpha,
                linewidth=0.8,
                label=label,
                zorder=5
            )
        except Exception as e:
            print(f"Error al dibujar elipsoide 3D: {str(e)}")
            

    @staticmethod
    def _crear_grafica_desviacion(widget, eje, tipo, titulo, desviaciones, unidad):
        layout = VisualizacionElipse._preparar_layout(widget)
        try:
            canvas = CanvasAjustable(widget)
            ax = canvas.ax

            # Configuración de estilo
            colores_sigma = {
                1: {'fill': '#008F39', 'line': '#008F39', 'alpha': 1, 'label': '1σ'},
                2: {'fill': '#FFA500', 'line': '#FFA500', 'alpha': 1, 'label': '2σ'},
                3: {'fill': '#FF0000', 'line': '#FF0000', 'alpha': 1, 'label': '3σ'}
            }

            # Determinar las desviaciones según el tipo
            if tipo == 'este':
                primera_desviacion = desviaciones[0][4]
                segunda_desviacion = desviaciones[0][4]*2
                tercera_desviacion = desviaciones[0][4]*3
            elif tipo == 'norte':
                primera_desviacion = desviaciones[0][6]
                segunda_desviacion = desviaciones[0][6]*2
                tercera_desviacion = desviaciones[0][6]*3
            elif tipo == 'cota':
                primera_desviacion = desviaciones[0][8]
                segunda_desviacion = desviaciones[0][8]*2
                tercera_desviacion = desviaciones[0][8]*3

            # Establecer el factor y la etiqueta de la unidad
            if unidad == 'm':
                factor = 1
                unit_label = 'm'
            elif unidad == 'cm':
                factor = 100
                unit_label = 'cm'
            elif unidad == 'mm':
                factor = 1000
                unit_label = 'mm'
            else:
                factor = 1
                unit_label = 'm'

            # Rango de valores basado en la tercera desviación
            x_min = -tercera_desviacion * factor
            x_max = tercera_desviacion * factor
            x = np.linspace(x_min, x_max, 1000)

            # Calcular la campana de Gauss
            media = 0  # Media de la distribución
            desviacion_estandar = tercera_desviacion * factor / 3  # Usar la tercera desviación como referencia
            gaussian = (1 / (desviacion_estandar * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - media) / desviacion_estandar) ** 2)

            # Curva principal
            ax.plot(x, gaussian, color='#0A0A0A', linewidth=2.2, zorder=5)

            # Colorear las áreas correspondientes a cada desviación estándar
            ax.fill_between(x, gaussian, where=(np.abs(x) <= tercera_desviacion * factor), color=colores_sigma[3]['fill'], alpha=colores_sigma[3]['alpha'])
            ax.fill_between(x, gaussian, where=(np.abs(x) <= segunda_desviacion * factor), color=colores_sigma[2]['fill'], alpha=colores_sigma[2]['alpha'])
            ax.fill_between(x, gaussian, where=(np.abs(x) <= primera_desviacion * factor), color=colores_sigma[1]['fill'], alpha=colores_sigma[1]['alpha'])

            # Añadir líneas verticales para las desviaciones estándar
            ax.axvline(x=primera_desviacion * factor, color=colores_sigma[1]['line'], linestyle='--', linewidth=1.5)
            ax.axvline(x=-primera_desviacion * factor, color=colores_sigma[1]['line'], linestyle='--', linewidth=1.5)
            ax.axvline(x=segunda_desviacion * factor, color=colores_sigma[2]['line'], linestyle='--', linewidth=1.5)
            ax.axvline(x=-segunda_desviacion * factor, color=colores_sigma[2]['line'], linestyle='--', linewidth=1.5)
            ax.axvline(x=tercera_desviacion * factor, color=colores_sigma[3]['line'], linestyle='--', linewidth=1.5)
            ax.axvline(x=-tercera_desviacion * factor, color=colores_sigma[3]['line'], linestyle='--', linewidth=1.5)

            # Configuración de ejes
            ax.set_title(titulo, pad=12)
            ax.set_xlabel(eje, labelpad=8)
            ax.set_ylabel("Densidad", labelpad=8)
            ax.grid(True, linestyle=':', alpha=0.4)

            # Ajustar los límites del eje x según la unidad
            ax.set_xlim(x_min - 0.05 * tercera_desviacion * factor, x_max + 0.05 * tercera_desviacion * factor)

            # Establecer las etiquetas del eje x para que coincidan con los valores numéricos de las desviaciones
            ticks = [-tercera_desviacion * factor, -segunda_desviacion * factor, -primera_desviacion * factor,
                    primera_desviacion * factor, segunda_desviacion * factor, tercera_desviacion * factor]
            ax.set_xticks(ticks)
            ax.set_xticklabels([f'{-tercera_desviacion * factor:.3f}', f'{-segunda_desviacion * factor:.3f}', f'{-primera_desviacion * factor:.3f}',
                                f'{primera_desviacion * factor:.3f}', f'{segunda_desviacion * factor:.3f}', f'{tercera_desviacion * factor:.3f}'])

            # Leyenda con valores de desviaciones de la base de datos
            handles, labels = ax.get_legend_handles_labels()

            # Añadir valores de desviaciones a la leyenda
            if desviaciones:
                desviacion = desviaciones[0]
                if tipo == 'este':
                    handles.append(plt.Line2D([0], [0], color=colores_sigma[1]['line'], label=f'1σ (±{desviacion[4] * factor:.3f} {unit_label})'))
                    handles.append(plt.Line2D([0], [0], color=colores_sigma[2]['line'], label=f'2σ (±{(desviacion[4]*2) * factor:.3f} {unit_label})'))
                    handles.append(plt.Line2D([0], [0], color=colores_sigma[3]['line'], label=f'3σ (±{(desviacion[4]*3) * factor:.4f} {unit_label})'))
                elif tipo == 'norte':
                    handles.append(plt.Line2D([0], [0], color=colores_sigma[1]['line'], label=f'1σ (±{desviacion[6] * factor:.3f} {unit_label})'))
                    handles.append(plt.Line2D([0], [0], color=colores_sigma[2]['line'], label=f'2σ (±{(desviacion[6]*2) * factor:.3f} {unit_label})'))
                    handles.append(plt.Line2D([0], [0], color=colores_sigma[3]['line'], label=f'3σ (±{(desviacion[6]*3) * factor:.3f} {unit_label})'))
                elif tipo == 'cota':
                    if unidad not in ['m', 'cm', 'mm']:
                        handles.append(plt.Line2D([0], [0], color=colores_sigma[1]['line'], label=f'1σ (±{desviacion[8]:.3f} msnm)'))
                        handles.append(plt.Line2D([0], [0], color=colores_sigma[2]['line'], label=f'2σ (±{(desviacion[8]*2):.3f} msnm)'))
                        handles.append(plt.Line2D([0], [0], color=colores_sigma[3]['line'], label=f'3σ (±{(desviacion[8]*3):.3f} msnm)'))
                    else:
                        handles.append(plt.Line2D([0], [0], color=colores_sigma[1]['line'], label=f'1σ (±{desviacion[8] * factor:.3f} {unit_label})'))
                        handles.append(plt.Line2D([0], [0], color=colores_sigma[2]['line'], label=f'2σ (±{(desviacion[8]*2) * factor:.3f} {unit_label})'))
                        handles.append(plt.Line2D([0], [0], color=colores_sigma[3]['line'], label=f'3σ (±{(desviacion[8]*3) * factor:.3f} {unit_label})'))

            ax.legend(handles=handles, bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.5,
                    frameon=True, fontsize=9, framealpha=0.9)

            # Ajuste final
            canvas.fig.tight_layout(pad=2.5)
            canvas.fig.subplots_adjust(right=0.68)
            layout.addWidget(canvas)
        except Exception as e:
            print(str(e))
    
    @staticmethod
    def _preparar_layout(widget):
        if widget.layout():
            for i in reversed(range(widget.layout().count())):
                widget.layout().itemAt(i).widget().setParent(None)
        else:
            widget.setLayout(QVBoxLayout())
            widget.layout().setContentsMargins(5, 5, 5, 5)
            widget.layout().setSpacing(5)
        return widget.layout()

