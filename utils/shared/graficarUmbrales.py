from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QDialogButtonBox
from utils.common.alertas import mostrar_mensaje
from modules.empresa.softwareconfiguracion import SoftwareConfiguracion

class GraficarUmbrales:
    
    def mostrarSeleccionUmbrales_personalizados(lista_opciones, titulo):
        dialog = QDialog()
        dialog.setWindowTitle(titulo)
        layout = QVBoxLayout()
        
        # Mostrar el mensaje
        mensaje_label = QLabel("Seleccione el tipo de umbral:")
        layout.addWidget(mensaje_label)
        
        # Crear combo box con las opciones
        combo_box = QComboBox()
        for opcion in lista_opciones:
            combo_box.addItem(opcion[1], opcion[0])  # Mostrar nombre, guardar valor
        
        layout.addWidget(combo_box)
        
        # Botones OK/Cancel
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.setLayout(layout)
        
        # Ejecutar diálogo
        if dialog.exec() == QDialog.Accepted:
            return combo_box.currentData()
        return None

    def mostrarSeleccionUmbrales(listaequipos, tipoumbral):
        dialog = QDialog()
        dialog.setWindowTitle(tipoumbral)
        layout = QVBoxLayout()
        # Mostrar el mensaje
        mensaje_label = QLabel("Seleccione el Umbral:")
        layout.addWidget(mensaje_label)
        # Crear un combo box para las opciones
        combo_box = QComboBox()
        for equipo in listaequipos:
            combo_box.addItem(equipo[1], equipo[0])
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
    
    def draw_on_widget(widget, umbrales, unidad, sentido='y', tipo_pintado='color', tipo=None):
        respuesta = SoftwareConfiguracion.obtenerDataSoftware()
        alfa = respuesta[11]
        # Convertir widget a una lista si no lo es
        widgets = widget if isinstance(widget, list) else [widget]
        if umbrales:
            for widget in widgets:
                # Buscar el canvas de Matplotlib dentro del widget
                canvas = next((child for child in widget.children() if isinstance(child, FigureCanvas)), None)
                if canvas is not None:
                    if tipo:
                        for ax in canvas.figure.axes:
                            if not hasattr(ax, 'colored_spans'):
                                ax.colored_spans = []
                            if not hasattr(ax, 'dashed_lines'):
                                ax.dashed_lines = []
                            umbrales_ordenados = sorted(umbrales, key=lambda x: x[6])
                            # Obtener los límites actuales del eje correspondiente
                            if sentido == 'y':
                                lim_inf, lim_sup = ax.get_ylim()
                                span_method = ax.axhspan
                                line_method = ax.axhline
                            elif sentido == 'x':
                                lim_inf, lim_sup = ax.get_xlim()
                                span_method = ax.axvspan
                                line_method = ax.axvline
                            else:
                                raise ValueError("El sentido debe ser 'x' o 'y'.")
                            # Dibujar las áreas coloreadas o líneas punteadas
                            for i, umbral in enumerate(umbrales_ordenados):
                                value = umbral[6] * unidad  # El valor del umbral es el quinto elemento
                                color = umbral[4]           # El color es el cuarto elemento
                                if tipo_pintado == 'color':
                                    # Dibujar áreas coloreadas
                                    if i == 0:
                                        span_pos = span_method(0, value, facecolor=color, alpha=alfa)
                                        span_neg = span_method(-value, 0, facecolor=color, alpha=alfa)
                                        ax.colored_spans.extend([span_pos, span_neg])
                                    else:
                                        prev_value = umbrales_ordenados[i-1][6] * unidad
                                        span_pos = span_method(prev_value, value, facecolor=color, alpha=alfa)
                                        span_neg = span_method(-value, -prev_value, facecolor=color, alpha=alfa)
                                        ax.colored_spans.extend([span_pos, span_neg])

                                    if i == len(umbrales_ordenados) - 1:
                                        if value < lim_sup:
                                            span_pos = span_method(value, lim_sup, facecolor=color, alpha=alfa)
                                            ax.colored_spans.append(span_pos)
                                        if -value > lim_inf:
                                            span_neg = span_method(lim_inf, -value, facecolor=color, alpha=alfa)
                                            ax.colored_spans.append(span_neg)
                                elif tipo_pintado == 'linea':
                                    # Dibujar líneas punteadas en ambos lados
                                    line_pos = line_method(value, color=color, linestyle='--')
                                    line_neg = line_method(-value, color=color, linestyle='--')
                                    ax.dashed_lines.extend([line_pos, line_neg])
                            # Restaurar los límites originales del eje
                            if sentido == 'y':
                                ax.set_ylim(lim_inf, lim_sup)
                            elif sentido == 'x':
                                ax.set_xlim(lim_inf, lim_sup)
                    else:
                        # Obtener el eje (ax) del canvas
                        ax = canvas.figure.axes[0]
                        # Ordenar los umbrales por valor
                        umbrales_ordenados = sorted(umbrales, key=lambda x: x[6])
                        # Obtener los límites actuales del eje correspondiente
                        if sentido == 'y':
                            lim_inf, lim_sup = ax.get_ylim()
                            span_method = ax.axhspan
                            line_method = ax.axhline
                        elif sentido == 'x':
                            lim_inf, lim_sup = ax.get_xlim()
                            span_method = ax.axvspan
                            line_method = ax.axvline
                        else:
                            raise ValueError("El sentido debe ser 'x' o 'y'.")
                        # Dibujar las áreas coloreadas o líneas punteadas
                        for i, umbral in enumerate(umbrales_ordenados):
                            value = umbral[6] * unidad  # El valor del umbral es el quinto elemento
                            color = umbral[4]           # El color es el cuarto elemento
                            if tipo_pintado == 'color':
                                # Dibujar áreas coloreadas
                                if i == 0:
                                    span_pos = span_method(0, value, facecolor=color, alpha=alfa)
                                    span_neg = span_method(-value, 0, facecolor=color, alpha=alfa)
                                    ax.colored_spans.extend([span_pos, span_neg])
                                else:
                                    prev_value = umbrales_ordenados[i-1][6] * unidad
                                    span_pos = span_method(prev_value, value, facecolor=color, alpha=alfa)
                                    span_neg = span_method(-value, -prev_value, facecolor=color, alpha=alfa)
                                    ax.colored_spans.extend([span_pos, span_neg])

                                if i == len(umbrales_ordenados) - 1:
                                    if value < lim_sup:
                                        span_pos = span_method(value, lim_sup, facecolor=color, alpha=alfa)
                                        ax.colored_spans.append(span_pos)
                                    if -value > lim_inf:
                                        span_neg = span_method(lim_inf, -value, facecolor=color, alpha=alfa)
                                        ax.colored_spans.append(span_neg)
                            elif tipo_pintado == 'linea':
                                # Dibujar líneas punteadas en ambos lados
                                line_pos = line_method(value, color=color, linestyle='--')
                                line_neg = line_method(-value, color=color, linestyle='--')
                                ax.dashed_lines.extend([line_pos, line_neg])
                        # Restaurar los límites originales del eje
                        if sentido == 'y':
                            ax.set_ylim(lim_inf, lim_sup)
                        elif sentido == 'x':
                            ax.set_xlim(lim_inf, lim_sup)
                    # Redibujar el canvas
                    canvas.draw()
        else:
            mostrar_mensaje("Error", "No hay umbrales.", 'error')
    
    def clean_on_widget(widget, tipo_pintado='color', tipo=None):
        # Convertir widget a una lista si no lo es
        widgets = widget if isinstance(widget, list) else [widget]
        # Variable para rastrear si se realizó alguna limpieza
        limpieza_realizada = False
        for widget in widgets:
            # Buscar el canvas de Matplotlib dentro del widget
            canvas = next((child for child in widget.children() if isinstance(child, FigureCanvas)), None)
            if canvas is not None:
                if tipo:
                    for ax in canvas.figure.axes:
                        # Inicializar atributos si no existen
                        if not hasattr(ax, 'colored_spans'):
                            ax.colored_spans = []
                        if not hasattr(ax, 'dashed_lines'):
                            ax.dashed_lines = []
                        # Verificar si ya hay elementos pintados y limpiarlos
                        if tipo_pintado == 'color' and ax.colored_spans:
                            # Limpiar las áreas coloreadas existentes
                            for span in ax.colored_spans:
                                span.remove()
                            ax.colored_spans.clear()
                            limpieza_realizada = True
                        elif tipo_pintado == 'linea' and ax.dashed_lines:
                            # Limpiar las líneas punteadas existentes
                            for line in ax.dashed_lines:
                                line.remove()
                            ax.dashed_lines.clear()
                            limpieza_realizada = True
                else:
                    # Obtener el eje (ax) del canvas
                    ax = canvas.figure.axes[0]
                    # Inicializar atributos si no existen
                    if not hasattr(ax, 'colored_spans'):
                        ax.colored_spans = []
                    if not hasattr(ax, 'dashed_lines'):
                        ax.dashed_lines = []
                    # Verificar si ya hay elementos pintados y limpiarlos
                    if tipo_pintado == 'color' and ax.colored_spans:
                        # Limpiar las áreas coloreadas existentes
                        for span in ax.colored_spans:
                            span.remove()
                        ax.colored_spans.clear()
                        limpieza_realizada = True
                    elif tipo_pintado == 'linea' and ax.dashed_lines:
                        # Limpiar las líneas punteadas existentes
                        for line in ax.dashed_lines:
                            line.remove()
                        ax.dashed_lines.clear()
                        limpieza_realizada = True
                # Redibujar el canvas después de la limpieza
                canvas.draw()
        return limpieza_realizada
    