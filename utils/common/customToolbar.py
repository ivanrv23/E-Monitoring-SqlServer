import io
from PySide6.QtGui import QAction, QImage, QIcon
from PySide6.QtWidgets import QApplication, QFileDialog
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from utils.common.rutasarchivos import resource_path


class CustomToolbar(NavigationToolbar):
    def __init__(self, canvas, parent=None, coordinates=True):
        super().__init__(canvas, parent, coordinates)
        self._agregar_boton_copiar()

    # ------------------------------------------------------------------
    # Guardar (lo que ya tenías)
    # ------------------------------------------------------------------
    def save_figure(self, *args):
        file_dialog = QFileDialog(self)
        file_dialog.setDefaultSuffix("png")
        file_dialog.setAcceptMode(QFileDialog.AcceptSave)
        file_dialog.setNameFilters(["PNG Files (*.png)", "All Files (*)"])

        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            self.canvas.figure.savefig(file_path, dpi=300)

    # ------------------------------------------------------------------
    # NUEVO: Copiar al portapapeles
    # ------------------------------------------------------------------
    def _agregar_boton_copiar(self):
        action = QAction("Copiar", self)
        action.setToolTip("Copiar la gráfica")
        icon_path = resource_path("resources/iconos/fontawesome/regular/copy.svg")
        action.setIcon(QIcon(icon_path))
        action.triggered.connect(self.copiar_al_portapapeles)

        acciones = self.actions()
        if acciones:
            # Insertamos justo antes del botón "Guardar" (último action estándar)
            self.insertAction(acciones[-1], action)
        else:
            self.addAction(action)

        self._accion_copiar = action

    def copiar_al_portapapeles(self):
        try:
            fig = self.canvas.figure
            if fig is None:
                self._avisar("No hay gráfica para copiar.", "advertencia")
                return

            # Render a PNG en memoria (sin tocar disco)
            buf = io.BytesIO()
            fig.savefig(
                buf,
                format="png",
                dpi=200,                # buena calidad para Word/PPT
                bbox_inches="tight",    # recorta espacio blanco sobrante
                facecolor="white",      # evita fondo transparente
                edgecolor="white",
            )
            buf.seek(0)

            img = QImage()
            if not img.loadFromData(buf.getvalue(), "PNG"):
                self._avisar("No se pudo generar la imagen.", "error")
                return

            QApplication.clipboard().setImage(img)

        except Exception as e:
            self._avisar(f"No se pudo copiar la imagen:\n{e}", "error")

    # ------------------------------------------------------------------
    @staticmethod
    def _avisar(mensaje, tipo):
        try:
            from utils.common.alertas import mostrar_mensaje
            mostrar_mensaje("Copiar", mensaje, tipo)
        except Exception:
            print(f"[CustomToolbar] {tipo}: {mensaje}")