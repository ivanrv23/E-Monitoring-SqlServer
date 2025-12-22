from PySide6.QtWidgets import QDialog
from PySide6.QtGui import QPixmap
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile
from utils.common.rutasarchivos import resource_path

class LicenciaView:
    dialog_licencia = None

    @staticmethod
    def DialogLicencia():
        # Ruta del archivo UI
        ui_file_path = resource_path("ui/serial.ui")
        # Crear el diálogo
        dialog = QDialog()
        # Cargar el archivo .ui usando QFile y QUiLoader
        ui_file = QFile(ui_file_path)
        ui_file.open(QFile.ReadOnly)
        loader = QUiLoader()
        ui = loader.load(ui_file, dialog)
        ui_file.close()
        # Cambiar el título del diálogo
        dialog.setWindowTitle("Registro de Licencia")
        # Personalizar algunos elementos, como los íconos
        icon_path = resource_path("resources/logo.png")  # Ruta del ícono
        pixmap = QPixmap(icon_path)
        # Asignar el pixmap directamente sin propiedades adicionales
        ui.lb_logo_emonitoring.setPixmap(pixmap)
        # Almacenar el diálogo en la variable de clase para tener referencia
        LicenciaView.dialog_licencia = dialog
        # Retornar el diálogo con la UI cargada para poder mostrarlo o cerrarlo luego
        return dialog
    