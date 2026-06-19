from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame)
from PySide6.QtCore import Qt, QTimer
from services.autenticacion.gestor2fa import Gestor2FA

class EstiloDialogo:
    """Estilos compartidos para mantener coherencia"""
    INPUT_STYLE = """
        QLineEdit {
            border: 2px solid #E0E0E0;
            border-radius: 8px;
            padding: 10px;
            font-size: 24px;
            letter-spacing: 12px;
            font-family: 'Consolas', 'Monaco', monospace;
            background-color: #F9F9F9;
            color: #333;
            selection-background-color: #B3E5FC;
        }
        QLineEdit:focus {
            border: 2px solid #00BFFF;
            background-color: #FFFFFF;
        }
    """
    BTN_PRIMARIO_AZUL = """
        QPushButton {
            background-color: #00BFFF; 
            color: white; 
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            font-weight: bold;
            font-size: 13px;
        }
        QPushButton:hover { background-color: #009ACD; }
        QPushButton:pressed { background-color: #0086B3; }
    """
    BTN_PRIMARIO_VERDE = """
        QPushButton {
            background-color: #2E7D32; 
            color: white; 
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            font-weight: bold;
            font-size: 13px;
        }
        QPushButton:hover { background-color: #1B5E20; }
        QPushButton:pressed { background-color: #144418; }
    """
    BTN_CANCELAR = """
        QPushButton {
            background-color: transparent; 
            color: #757575;
            border: 1px solid #E0E0E0;
            padding: 10px 20px;
            border-radius: 6px;
            font-weight: 500;
        }
        QPushButton:hover { 
            background-color: #F5F5F5; 
            color: #424242;
            border-color: #BDBDBD;
        }
    """

class DialogoValidar2FA(QDialog):
    def __init__(self, usuario, es_eliminacion=False, parent=None):
        super().__init__(parent)
        self.usuario = usuario
        self.es_eliminacion = es_eliminacion
        
        # Configuración Ventana
        self.setWindowTitle("Seguridad")
        self.setFixedSize(360, 260)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setStyleSheet("background-color: white;")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # 1. Icono y Título
        header = QLabel("🔐 Verificación")
        if self.es_eliminacion:
            header.setText("🗑️ Confirmar Eliminación")
            
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        layout.addWidget(header)
        
        # 2. Subtítulo
        texto = f"Ingresa el código de 6 dígitos para continuar."
        if self.es_eliminacion:
            texto = "Por seguridad, confirma con tu código actual para desactivar el 2FA."
            
        subtitulo = QLabel(texto)
        subtitulo.setWordWrap(True)
        subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitulo.setStyleSheet("color: #666; font-size: 13px;")
        layout.addWidget(subtitulo)
        
        # 3. Input Código
        self.codigo_input = QLineEdit()
        self.codigo_input.setPlaceholderText("000000")
        self.codigo_input.setMaxLength(6)
        self.codigo_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.codigo_input.setStyleSheet(EstiloDialogo.INPUT_STYLE)
        layout.addWidget(self.codigo_input)
        
        # 4. Mensaje Error (oculto inicialmente)
        self.lbl_error = QLabel("")
        self.lbl_error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_error.setStyleSheet("color: #E53935; font-size: 12px; font-weight: 600;")
        layout.addWidget(self.lbl_error)
        
        # 5. Botones (Horizontal)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancelar.setStyleSheet(EstiloDialogo.BTN_CANCELAR)
        btn_cancelar.clicked.connect(self.reject)
        
        self.btn_accion = QPushButton("Verificar")
        self.btn_accion.setCursor(Qt.CursorShape.PointingHandCursor)
        # Usamos verde si es confirmación/eliminación, Azul si es login normal
        if self.es_eliminacion:
            self.btn_accion.setText("Eliminar")
            self.btn_accion.setStyleSheet(EstiloDialogo.BTN_PRIMARIO_VERDE)
        else:
            self.btn_accion.setStyleSheet(EstiloDialogo.BTN_PRIMARIO_VERDE) # Verde confirmación
            
        self.btn_accion.clicked.connect(self.verificar)
        
        btn_layout.addWidget(btn_cancelar)
        btn_layout.addWidget(self.btn_accion)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        self.codigo_input.setFocus()

    def verificar(self):
        code = self.codigo_input.text().strip()
        if len(code) != 6 or not code.isdigit():
            self.lbl_error.setText("Ingresa los 6 dígitos numéricos")
            self.codigo_input.setFocus()
            return
            
        if Gestor2FA.verificar_codigo_existente(self.usuario, code):
            self.accept()
        else:
            self.lbl_error.setText("Código incorrecto")
            self.codigo_input.clear()
            self.codigo_input.setFocus()

class DialogoActivar2FA(QDialog):
    def __init__(self, usuario, parent=None):
        super().__init__(parent)
        self.usuario = usuario
        self.secreto_temp = None
        
        self.setWindowTitle("Configurar 2FA")
        self.setFixedSize(380, 520)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setStyleSheet("background-color: white;")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        
        # Título
        titulo = QLabel("📱 Vincular Dispositivo")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        layout.addWidget(titulo)
        
        instr = QLabel("Escanea el QR con tu app (Google Auth o Authy) e ingresa el código generado.")
        instr.setWordWrap(True)
        instr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instr.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(instr)
        
        # Contenedor QR (para darle borde elegante)
        qr_container = QFrame()
        qr_container.setStyleSheet("background-color: white; border: 1px solid #E0E0E0; border-radius: 12px;")
        qr_layout = QVBoxLayout(qr_container)
        qr_layout.setContentsMargins(15, 15, 15, 15)
        
        self.lbl_qr = QLabel()
        self.lbl_qr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qr_layout.addWidget(self.lbl_qr)
        layout.addWidget(qr_container)
        
        # Input
        self.input_code = QLineEdit()
        self.input_code.setPlaceholderText("000000")
        self.input_code.setMaxLength(6)
        self.input_code.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.input_code.setStyleSheet(EstiloDialogo.INPUT_STYLE)
        layout.addWidget(self.input_code)
        
        # Status Label
        self.lbl_status = QLabel("")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet("font-size: 12px; font-weight: bold;")
        layout.addWidget(self.lbl_status)
        
        # Botones
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancelar.setStyleSheet(EstiloDialogo.BTN_CANCELAR)
        btn_cancelar.clicked.connect(self.reject)
        
        self.btn_activate = QPushButton("Activar Seguridad")
        self.btn_activate.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_activate.setStyleSheet(EstiloDialogo.BTN_PRIMARIO_AZUL) # Celeste/Azul para generar
        self.btn_activate.clicked.connect(self.activar)
        
        btn_layout.addWidget(btn_cancelar)
        btn_layout.addWidget(self.btn_activate)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        self.generar_qr()
        self.input_code.setFocus()
        
    def generar_qr(self):
        self.secreto_temp = Gestor2FA.generar_secreto_temporal()
        # Generar QR un poco más grande para calidad
        pixmap = Gestor2FA.generar_qr_pixmap(self.usuario, self.secreto_temp, 220)
        self.lbl_qr.setPixmap(pixmap)
        
    def activar(self):
        code = self.input_code.text().strip()
        if len(code) != 6 or not code.isdigit():
            self.lbl_status.setText("⚠️ El código debe ser numérico")
            self.lbl_status.setStyleSheet("color: #FF9800;")
            return

        if Gestor2FA.verificar_codigo_y_guardar(self.usuario, self.secreto_temp, code):
            self.lbl_status.setText("✅ ¡Activado Correctamente!")
            self.lbl_status.setStyleSheet("color: #2E7D32;")
            self.btn_activate.setEnabled(False)
            self.input_code.setEnabled(False)
            Gestor2FA.obtener_codigos_respaldo(self.usuario)
            
            # Cerrar automáticamente tras 1 segundo
            QTimer.singleShot(1000, self.accept)
        else:
            self.lbl_status.setText("❌ Código incorrecto")
            self.lbl_status.setStyleSheet("color: #E53935;")
            self.input_code.clear()
            self.input_code.setFocus()