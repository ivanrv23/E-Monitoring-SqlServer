from datetime import datetime
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QStyle, QLabel, QLineEdit, QPushButton, QToolButton, QCheckBox)
from PySide6.QtGui import QIcon, QScreen, QPixmap
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
    
    @staticmethod
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
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Crea un widget interno para el contenido del formulario
        inner_widget = QWidget()
        inner_layout = QVBoxLayout(inner_widget)
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.setSpacing(0)
        
        # Crea un QLabel para la imagen de fondo
        background_label = QLabel()
        ruta_imagen = resource_path("resources/image.png")
        background_label.setPixmap(QPixmap(ruta_imagen))
        background_label.setScaledContents(True)
        background_label.setFixedSize(341, 321)
        
        # Crea un layout para superponer contenido sobre la imagen
        overlay_layout = QVBoxLayout(background_label)
        overlay_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        overlay_layout.setContentsMargins(20, 20, 20, 20)
        
        # --- TÍTULO ---
        titulo = QLabel("Iniciar Sesión")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet("""
            color: white;
            font-size: 30px;
            font-weight: bold;
        """)
        overlay_layout.addWidget(titulo)
        
        # --- INPUT USUARIO ---
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
        
        # --- INPUT CONTRASEÑA Y VISIBILIDAD ---
        def toggle_password_visibility():
            if contrasena_input.echoMode() == QLineEdit.EchoMode.Password:
                contrasena_input.setEchoMode(QLineEdit.EchoMode.Normal)
                icon_path = resource_path("resources/iconos/fontawesome/solid/eye.svg")
                toggle_button.setIcon(QIcon(icon_path))
            else:
                contrasena_input.setEchoMode(QLineEdit.EchoMode.Password)
                icon_path = resource_path("resources/iconos/fontawesome/solid/eye-slash.svg")
                toggle_button.setIcon(QIcon(icon_path))
        
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
        
        toggle_button = QToolButton(contrasena_input)
        toggle_button.setCursor(Qt.CursorShape.PointingHandCursor)
        toggle_button.setIcon(QIcon(resource_path("resources/iconos/fontawesome/solid/eye-slash.svg")))
        toggle_button.setStyleSheet("QToolButton { border: none; margin-left: -5px; background: transparent;}")
        
        frame_width = contrasena_input.style().pixelMetric(QStyle.PixelMetric.PM_DefaultFrameWidth)
        toggle_button.setFixedSize(20, 20)
        toggle_button.move(contrasena_input.rect().right() - toggle_button.width() - frame_width, 
                        (contrasena_input.height() - toggle_button.height()) // 2)
        toggle_button.raise_()
        
        def resize_event(event):
            toggle_button.move(contrasena_input.rect().right() - toggle_button.width() - frame_width,
                            (contrasena_input.height() - toggle_button.height()) // 2)
        contrasena_input.resizeEvent = resize_event
        
        overlay_layout.addWidget(contrasena_input)
        toggle_button.clicked.connect(toggle_password_visibility)

        # --- OPCIÓN CHECKBOX 2FA (NUEVO) ---
        container_checkbox = QWidget()
        layout_cb = QHBoxLayout(container_checkbox)
        layout_cb.setContentsMargins(6, 5, 0, 5) # Márgenes ajustados para alinear
        layout_cb.setSpacing(0)

        check_2fa = QCheckBox("Seguridad 2FA")
        check_2fa.setObjectName("check_2fa")
        check_2fa.setCursor(Qt.CursorShape.PointingHandCursor)
        check_2fa.setToolTip("Active para mayor seguridad o desactive para eliminar")
        check_2fa.setStyleSheet("""
            QCheckBox {
                color: white;
                font-size: 13px;
                font-weight: bold;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #00BFFF;
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 3px;
            }
            QCheckBox::indicator:hover {
                background-color: rgba(0, 191, 255, 0.3);
            }
            QCheckBox::indicator:checked {
                background-color: #00BFFF;
                border: 1px solid #00BFFF;
                image: url(resources/iconos/fontawesome/solid/check.svg); /* Opcional si tienes icono */
            }
            /* Si no tienes icono de check, puedes usar un color solido en checked */
        """)
        
        layout_cb.addWidget(check_2fa)
        layout_cb.addStretch() # Empuja el check a la izquierda
        overlay_layout.addWidget(container_checkbox)
        
        # --- BOTÓN INGRESAR ---
        boton_iniciar = QPushButton("Ingresar")
        boton_iniciar.setObjectName("btn_ingresar")
        boton_iniciar.setCursor(Qt.CursorShape.PointingHandCursor)
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
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #666666;
                border: 1px solid #00BFFF;
            }
            QPushButton:pressed {
                background-color: #222222;
            }
            QPushButton:disabled {
                background-color: #333333;
                color: #888888;
            }
        """)
        overlay_layout.addWidget(boton_iniciar)
        
        # --- MENSAJES DE ERROR ---
        label_error = QLabel("")
        label_error.setObjectName("mensaje_label")
        label_error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_error.setWordWrap(True)
        label_error.setStyleSheet("""
            color: #FF6B6B;
            font-size: 12px;
            font-weight: bold;
        """)
        overlay_layout.addWidget(label_error)
        
        # --- FOOTER AÑO ---
        anio_actual = datetime.now().year
        label_anio = QLabel(f"© E-Monitoring {anio_actual}")
        label_anio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_anio.setStyleSheet("""
            color: rgba(255, 255, 255, 0.7);
            font-size: 11px;
        """)
        overlay_layout.addWidget(label_anio)
        
        # Finalizar construcción
        inner_layout.addWidget(background_label)
        main_layout.addWidget(inner_widget)
        main_container.setLayout(main_layout)
        
        return main_container