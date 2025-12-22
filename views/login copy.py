from datetime import datetime
from PySide6.QtWidgets import QLineEdit, QToolButton
from PySide6.QtGui import QIcon, QScreen, QPixmap
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QStyle, QLabel, QLineEdit, QPushButton, QToolButton
from PySide6.QtCore import Qt
from utils.common.rutasarchivos import resource_path

class DraggableWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.drag_position = None  # Inicializa la posición de arrastre

    def mousePressEvent(self, event):
        # Guarda la posición del clic del ratón para el arrastre
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        # Mueve la ventana si el botón izquierdo del ratón está presionado
        if self.drag_position is not None and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)

class Login:
    login_widget = None
    
    def mostrarLogin():
        Login.login_widget = DraggableWidget()
        main_container = Login.login_widget
        main_container.setWindowTitle("Inicio de Sesión")
        # Establece el tamaño del widget principal
        main_container.setFixedSize(341, 321)
        # Centra el widget principal en la pantalla
        screen_geometry = QScreen.availableGeometry(QApplication.primaryScreen())
        main_container.move(
            (screen_geometry.width() - main_container.width()) // 2,
            (screen_geometry.height() - main_container.height()) // 2
        )
        # Crea el layout principal
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)  # Elimina los márgenes del layout principal
        main_layout.setSpacing(0)  # Elimina el espacio entre los widgets del layout principal
        # Crea un widget interno para el contenido del formulario
        inner_widget = QWidget()
        inner_layout = QVBoxLayout(inner_widget)
        inner_layout.setContentsMargins(0, 0, 0, 0)  # Elimina los márgenes del layout interno
        inner_layout.setSpacing(0)  # Elimina el espacio entre los widgets del layout interno
        # Crea un QLabel para la imagen de fondo
        background_label = QLabel()
        ruta_imagen = resource_path("resources/image.png")
        background_label.setPixmap(QPixmap(ruta_imagen))
        background_label.setScaledContents(True)  # Ajusta la imagen al tamaño del label
        background_label.setFixedSize(341, 321)  # Establece un tamaño fijo para el QLabel
        # Crea un layout para superponer contenido sobre la imagen
        overlay_layout = QVBoxLayout(background_label)
        overlay_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        overlay_layout.setContentsMargins(20, 20, 20, 20)  # Añade márgenes al layout de superposición
        # Crea el título
        titulo = QLabel("Iniciar Sesión")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet("""
            color: white;
            font-size: 30px;
        """)
        overlay_layout.addWidget(titulo)
        # Crea el campo de entrada para el usuario
        usuario_input = QLineEdit()
        usuario_input.setObjectName("user_input")
        usuario_input.setPlaceholderText("USUARIO")
        usuario_input.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: none;
                border-bottom: 2px solid #00BFFF;
                color: black;
                padding: 5px 10px;
                text-align: left;
                font-size: 14px;
                margin: 4px;
            }
            QLineEdit:hover {
                border-bottom: 2px solid #1E90FF;
            }
            QLineEdit:focus {
                background-color: #f0f0f0;
                color: #333333;
                border-bottom: 2px solid #1E90FF;
            }
        """)
        overlay_layout.addWidget(usuario_input)
        def toggle_password_visibility():
            if contrasena_input.echoMode() == QLineEdit.EchoMode.Password:
                contrasena_input.setEchoMode(QLineEdit.EchoMode.Normal)
                icon_path = resource_path("resources/iconos/fontawesome/solid/eye.svg")
                toggle_button.setIcon(QIcon(icon_path))
            else:
                contrasena_input.setEchoMode(QLineEdit.EchoMode.Password)
                icon_path = resource_path("resources/iconos/fontawesome/solid/eye-slash.svg")
                toggle_button.setIcon(QIcon(icon_path))
        # Crea el campo de entrada para la contraseña
        contrasena_input = QLineEdit()
        contrasena_input.setObjectName("pass_input")
        contrasena_input.setPlaceholderText("CONTRASEÑA")
        contrasena_input.setEchoMode(QLineEdit.EchoMode.Password)
        contrasena_input.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: none;
                border-bottom: 2px solid #00BFFF;
                color: black;
                padding: 5px 10px;
                text-align: left;
                font-size: 14px;
                margin: 4px;
            }
            QLineEdit:hover {
                border-bottom: 2px solid #1E90FF;
            }
            QLineEdit:focus {
                background-color: #f0f0f0;
                color: #333333;
                border-bottom: 2px solid #1E90FF;
            }
        """)
        # Botón para mostrar/ocultar contraseña
        toggle_button = QToolButton(contrasena_input)
        toggle_button.setCursor(Qt.CursorShape.PointingHandCursor)
        toggle_button.setIcon(QIcon("resources/iconos/fontawesome/solid/eye-slash.svg"))
        toggle_button.setStyleSheet("QToolButton { border: none; margin-left: -5px; background: transparent;}")
        # Posicionar el botón dentro del QLineEdit
        frame_width = contrasena_input.style().pixelMetric(QStyle.PixelMetric.PM_DefaultFrameWidth)
        toggle_button.setFixedSize(20, 20)
        toggle_button.move(contrasena_input.rect().right() - toggle_button.width() - frame_width, 
                        (contrasena_input.height() - toggle_button.height()) // 2)
        toggle_button.raise_()
        # Redimensionar correctamente al cambiar tamaño
        def resize_event(event):
            toggle_button.move(contrasena_input.rect().right() - toggle_button.width() - frame_width,
                            (contrasena_input.height() - toggle_button.height()) // 2)
        contrasena_input.resizeEvent = resize_event
        overlay_layout.addWidget(contrasena_input)
        toggle_button.clicked.connect(toggle_password_visibility)
        # Crea el botón de inicio de sesión
        boton_iniciar = QPushButton("Ingresar")
        boton_iniciar.setObjectName("btn_ingresar")
        boton_iniciar.setStyleSheet("""
            QPushButton {
                background-color: #444444;
                border: 1px solid #333333;
                color: white;
                padding: 10px 24px;
                text-align: center;
                text-decoration: none;
                font-size: 16px;
                margin: 4px 2px;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #666666;
            }
            QPushButton:pressed {
                background-color: #222222;
            }
        """)
        overlay_layout.addWidget(boton_iniciar)
        # Label vacío para mensajes de error
        label_error = QLabel("")
        label_error.setObjectName("mensaje_label")
        label_error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_error.setStyleSheet("""
            color: red;
            font-size: 12px;
        """)
        overlay_layout.addWidget(label_error)
        # Crea un QLabel para el año actual
        anio_actual = datetime.now().year
        label_anio = QLabel(f"© E-Monitoring {anio_actual}")
        label_anio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_anio.setStyleSheet("""
            color: white;
            font-size: 12px;
        """)
        overlay_layout.addWidget(label_anio)
        # Añade la etiqueta de fondo al layout del widget interno
        inner_layout.addWidget(background_label)
        # Añade el widget interno al layout principal
        main_layout.addWidget(inner_widget)
        # Establece el layout en el widget principal
        main_container.setLayout(main_layout)
        # Muestra el widget principal
        return main_container
    