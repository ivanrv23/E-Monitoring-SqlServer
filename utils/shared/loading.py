from PySide6 import QtCore
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QLabel, QDialog, QVBoxLayout
from PySide6.QtGui import QMovie
from utils.common.rutasarchivos import resource_path

class LoadingView:
    
    def mostrarLoading():
        loader_loading = QUiLoader()
        ui_file_path = resource_path("ui/loading.ui")
        dialogo_loading = loader_loading.load(ui_file_path, None)
        # Configurar el cuadro de diálogo principal
        dialog_loading = QDialog()
        dialog_loading.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        dialog_loading.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.FramelessWindowHint | QtCore.Qt.Tool)
        layout = QVBoxLayout(dialog_loading)  # Establecer el layout en el diálogo
        layout.setContentsMargins(0, 0, 0, 0)  # Establecer los márgenes del layout a 0
        layout.addWidget(dialogo_loading)

        label_carga = dialogo_loading.findChild(QLabel, "label_loading")
        absolute_gif_path = resource_path("resources/images/loading.gif")

        movie = QMovie(absolute_gif_path)
        label_carga.setMovie(movie)
        label_carga.setFixedSize(QtCore.QSize(70, 70))
        movie.start()
        return dialog_loading