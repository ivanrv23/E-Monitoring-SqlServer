import sys
import matplotlib
matplotlib.use('QtAgg')
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QToolTip
from PySide6.QtCore import Qt, QPoint
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import numpy as np

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig, self.ax = plt.subplots(figsize=(10, 5), tight_layout=True)
        super().__init__(self.fig)
        self.setParent(parent)

        # Conectar eventos del ratón
        self.fig.canvas.mpl_connect('scroll_event', self.on_scroll)
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_hover)

        # Variable para almacenar los datos
        self.data = []

    def plot_data(self, data):
        # Limpiar el gráfico anterior
        self.ax.clear()

        # Almacenar los datos para usarlos en el hover
        self.data = data

        # Extraer datos para el gráfico
        labels = [row[0] for row in data]
        values = [row[3] for row in data]  # Usamos 'cantidad' para las barras

        # Combinar paletas de colores
        colors_tab10 = plt.get_cmap('tab10').colors
        colors_tab20 = plt.get_cmap('tab20').colors
        colors_set3 = plt.get_cmap('Set3').colors
        self.colors = colors_tab10 + colors_tab20 + colors_set3

        # Crear el gráfico de barras
        self.bars = self.ax.bar(labels, values, color=self.colors[:len(labels)])
        self.ax.set_title('Resumen de Prismas')

        # Etiquetas de los ejes
        self.ax.set_ylabel('Lecturas')
        self.ax.set_xlabel('Equipos')

        # Rotar los nombres en el eje x
        self.ax.set_xticks(range(len(labels)))
        self.ax.set_xticklabels(labels, rotation=90, ha='right')

        # Ajustar el margen superior para que haya espacio para los valores
        self.ax.margins(y=0.1)

        # Crear textos para los valores
        # self.value_texts = [self.ax.text(
        #     bar.get_x() + bar.get_width() / 2,
        #     bar.get_height() + 0.1,
        #     f'{int(bar.get_height())}',
        #     ha='center',
        #     va='bottom',
        #     fontsize=8  # Tamaño de la fuente
        # ) for bar in self.bars]

        self.value_texts = self.ax.bar_label(
        self.bars,
        padding=5,      # separación respecto a la barra
        fontsize=20,
        fmt='%d'
    )




        # Ajustar la visibilidad inicial de las barras
        if len(labels) <= 15:
            self.ax.set_xlim(-0.5, len(labels) - 0.5)
        else:
            self.ax.set_xlim(-0.5, 14.5)

        self.update_visible_texts()
        self.draw()

    def update_visible_texts(self):
        # Actualizar la visibilidad de los textos de valor
        xlim = self.ax.get_xlim()
        for bar, text in zip(self.bars, self.value_texts):
            if xlim[0] <= bar.get_x() + bar.get_width() / 2 <= xlim[1]:
                text.set_visible(True)
            else:
                text.set_visible(False)
        self.draw()

    def on_scroll(self, event):
        # Ajustar los límites del eje x al hacer scroll
        current_xlim = self.ax.get_xlim()
        step = (current_xlim[1] - current_xlim[0]) * 0.1  # Ajustar el paso del desplazamiento
        if event.button == 'up':
            self.ax.set_xlim(current_xlim[0] - step, current_xlim[1] - step)
        elif event.button == 'down':
            self.ax.set_xlim(current_xlim[0] + step, current_xlim[1] + step)
        self.update_visible_texts()

    def on_hover(self, event):
        # Mostrar detalles al pasar el cursor sobre una barra
        if event.inaxes == self.ax:
            for bar, row in zip(self.bars, self.data):
                if bar.contains(event)[0]:
                    tooltip_text = (f"Nombre: {row[0]}\n"
                                    f"Fecha Inicial: {row[1]}\n"
                                    f"Fecha Final: {row[2]}\n"
                                    f"Lecturas: {row[3]}\n"
                                    f"Total Días: {row[4]}\n"
                                    f"Ratio: {row[5]:.2f}")
                    # Convertir la posición del evento a un QPoint
                    local_pos = self.fig.canvas.mapToGlobal(QPoint(event.x, event.y))
                    QToolTip.showText(local_pos, tooltip_text, self)
                    break

class GraficarResumenEquipos:
    
    def graficar_datos_en_widget(widget, datos):
        if datos:
            # Crear un objeto MplCanvas y establecer el widget como su padre
            canvas = MplCanvas(widget)

            # Graficar los datos en el canvas
            canvas.plot_data(datos)

            # Crear un layout vertical para el widget si no existe
            if not widget.layout():
                layout = QVBoxLayout(widget)
            else:
                layout = widget.layout()

            # Añadir el canvas al layout del widget
            layout.addWidget(canvas)

            # Ajustar el tamaño del widget para que se ajuste al contenido
            widget.adjustSize()
