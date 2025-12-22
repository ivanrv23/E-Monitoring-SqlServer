import os
from PySide6.QtWidgets import QVBoxLayout, QLabel, QWidget
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QTimer
from utils.common.rutasarchivos import resource_path

class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # Utilizar Qt.SplashScreen para el comportamiento adecuado de un splash
        self.setWindowFlags(Qt.SplashScreen | Qt.FramelessWindowHint)
        # Obtener el tamaño de la pantalla y ajustar el tamaño del splash al 40% de ancho y 50% de altura
        screen_geometry = self.screen().geometry()
        width = screen_geometry.width() * 0.4  # 40% del ancho de la pantalla
        height = screen_geometry.height() * 0.5  # 50% de la altura de la pantalla
        self.resize(width, height)
        # Centrar la ventana en la pantalla
        x = (screen_geometry.width() - width) / 2
        y = (screen_geometry.height() - height) / 2
        self.move(int(x), int(y))
        # Contenedor principal
        container = QWidget(self)
        # Layout principal para centrar el contenido
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        # Fondo con imagen
        image_path = resource_path("resources/splash_image.png")
        pixmap = QPixmap(image_path)
        # Verificar si la imagen existe
        self.background = QLabel(container)
        self.background.setAlignment(Qt.AlignCenter)
        if pixmap.isNull():
            self.background.setText("Imagen no disponible")
        else:
            self.set_image(pixmap)
        layout.addWidget(self.background)
        self.setLayout(layout)
        # Temporizador para cerrar el splash después de unos segundos (por ejemplo, 3 segundos)
        QTimer.singleShot(3000, self.close_splash)
    
    def set_image(self, pixmap):
        # Método para escalar la imagen para que ocupe todo el tamaño actual del SplashScreen
        self.background.setPixmap(pixmap.scaled(
            self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation))
    
    def resizeEvent(self, event):
        if hasattr(self, 'background'):
            self.set_image(self.background.pixmap())
        super().resizeEvent(event)
    
    # Método para cerrar correctamente el splash screen
    def close_splash(self):
        self.close()
    
    # Evitar que el splash desaparezca al hacer clic (ignoramos eventos)
    def mousePressEvent(self, event):
        # Ignorar eventos de mouse para evitar que desaparezca al hacer clic
        event.ignore()
    
    def mouseReleaseEvent(self, event):
        # Ignorar eventos de liberación del mouse para evitar que desaparezca
        event.ignore()
    