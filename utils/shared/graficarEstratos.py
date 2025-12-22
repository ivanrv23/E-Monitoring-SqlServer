from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QDialogButtonBox
from utils.common.alertas import mostrar_mensaje
from controllers.UmbralController import UmbralController

class GraficarEstratos:
    @staticmethod
    def mostrar_dialogo_seleccion(mensaje, opciones):
        listaComponentes = UmbralController.ctrlComponentesTipo(opciones)
        dialog = QDialog()
        dialog.setWindowTitle("Seleccionar Opción")

        layout = QVBoxLayout()

        # Mostrar el mensaje
        mensaje_label = QLabel(mensaje)
        layout.addWidget(mensaje_label)

        # Crear un combo box para las opciones
        combo_box = QComboBox()
        for valor, nombre in listaComponentes:
            combo_box.addItem(nombre, valor)

        layout.addWidget(combo_box)

        # Crear un botón para confirmar la selección
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        layout.addWidget(button_box)

        dialog.setLayout(layout)

        # Ejecutar el diálogo y esperar la respuesta del usuario
        if dialog.exec() == QDialog.Accepted:
            return combo_box.currentData()
        else:
            return None

    @staticmethod
    def draw_colored_estratos(widget, estratos, unidad, sentido='y'):
        # Convertir widget a una lista si no lo es
        widgets = widget if isinstance(widget, list) else [widget]

        # Variable para rastrear si se realizó alguna limpieza
        limpieza_realizada = False

        for widget in widgets:
            # Buscar el canvas de Matplotlib dentro del widget
            canvas = next((child for child in widget.children() if isinstance(child, FigureCanvas)), None)

            if canvas is not None:
                # Obtener el eje (ax) del canvas
                ax = canvas.figure.axes[0]

                # Inicializar atributos si no existen
                if not hasattr(ax, 'colored_spans'):
                    ax.colored_spans = []

                # Verificar si ya hay elementos pintados y limpiarlos
                if ax.colored_spans:
                    # Limpiar las áreas coloreadas existentes
                    for span in ax.colored_spans:
                        span.remove()
                    ax.colored_spans.clear()
                    limpieza_realizada = True

                # Redibujar el canvas después de la limpieza
                canvas.draw()

        # Si se realizó alguna limpieza, salir del método
        if limpieza_realizada:
            return

        if estratos:
            # Extraer los componentes únicos de la ubicación especificada (posición 1)
            componentes = set(umbral[2] for umbral in estratos)

            # Verificar si hay más de un componente
            if len(componentes) > 1:
                # Mostrar un diálogo para seleccionar el componente a considerar
                componente_seleccionado = GraficarEstratos.mostrar_dialogo_seleccion("Seleccione el componente a considerar", list(componentes))
                if componente_seleccionado is None:
                    # Si no se selecciona ningún componente, salir de la función
                    return
                # Filtrar los estratos para mantener solo aquellos con el componente seleccionado
                estratos = [umbral for umbral in estratos if umbral[2] == componente_seleccionado]

            for widget in widgets:
                # Buscar el canvas de Matplotlib dentro del widget
                canvas = next((child for child in widget.children() if isinstance(child, FigureCanvas)), None)

                if canvas is not None:
                    # Obtener el eje (ax) del canvas
                    ax = canvas.figure.axes[0]

                    # Guardar los límites actuales del eje
                    if sentido == 'y':
                        original_limits = ax.get_ylim()
                    elif sentido == 'x':
                        original_limits = ax.get_xlim()
                    else:
                        raise ValueError("El sentido debe ser 'x' o 'y'.")

                    # Obtener el método de span correspondiente
                    span_method = ax.axhspan if sentido == 'y' else ax.axvspan

                    # Dibujar las áreas coloreadas
                    for umbral in estratos:
                        min_value = umbral[5] * unidad  # El valor mínimo del umbral es el cuarto elemento
                        max_value = umbral[6] * unidad  # El valor máximo del umbral es el quinto elemento
                        color = umbral[4]               # El color es el tercer elemento

                        # Determinar los límites del área a pintar
                        span = span_method(min_value, max_value, facecolor=color, alpha=0.5)
                        ax.colored_spans.append(span)

                    # Restaurar los límites originales del eje
                    if sentido == 'y':
                        ax.set_ylim(original_limits)
                    elif sentido == 'x':
                        ax.set_xlim(original_limits)
                    # Redibujar el canvas
                    canvas.draw()
        else:
            mostrar_mensaje("Error", "No existe umbrales registrados.", 'error')
