import os
import pyodbc # <--- AGREGADO: Usaremos pyodbc para la prueba
from pathlib import Path
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                               QLineEdit, QPushButton, QLabel, QGroupBox, 
                               QToolButton, QStyle, QFrame, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIntValidator

# Importamos las funciones para manejar el archivo .env
from dotenv import set_key, dotenv_values

class ConexionDB:
    @staticmethod
    def configuracion():
        """
        Modal para configurar credenciales .env con aviso de reinicio.
        """
        # Ruta del archivo .env
        env_path = Path(".env")
        if not env_path.exists():
            env_path.touch()

        # --- CONFIGURACIÓN DE UI ---
        dialogo = QDialog()
        dialogo.setWindowTitle("Configuración del Servidor")
        dialogo.setFixedSize(450, 520)
        dialogo.setModal(True)

        # Estilos CSS
        estilo = """
            QDialog { background-color: #f4f6f9; }
            QGroupBox { background-color: white; border: 1px solid #dcdcdc; border-radius: 8px; margin-top: 10px; padding-top: 15px; font-weight: bold; color: #333; }
            QLineEdit { border: 1px solid #ccc; border-radius: 4px; padding: 6px; background-color: #fff; }
            QPushButton { background-color: #3498db; color: white; border-radius: 4px; padding: 8px 15px; font-weight: bold; }
            QPushButton#btnCancelar { background-color: #e74c3c; }
            QLabel#lblAviso {
                color: #7f8c8d;
                font-size: 11px;
                font-style: italic;
                padding: 5px;
            }
        """
        dialogo.setStyleSheet(estilo)

        layout_principal = QVBoxLayout(dialogo)
        
        # Título
        lbl_titulo = QLabel("Conexión SQL Server")
        lbl_titulo.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_principal.addWidget(lbl_titulo)

        # Formulario
        grupo = QGroupBox("Parámetros de Conexión")
        layout_grupo = QFormLayout(grupo)
        
        txt_server = QLineEdit()
        txt_server.setPlaceholderText("Ej: 192.168.1.51")
        
        txt_port = QLineEdit()
        txt_port.setPlaceholderText("Ej: 1433")
        txt_port.setValidator(QIntValidator(1, 65535))
        txt_port.setFixedWidth(100)
        
        txt_database = QLineEdit()
        txt_database.setPlaceholderText("Ej: AdventureWorksDW2022")
        
        txt_user = QLineEdit()
        txt_user.setPlaceholderText("Ej: sa")
        
        widget_pass = QFrame()
        layout_pass = QHBoxLayout(widget_pass)
        layout_pass.setContentsMargins(0,0,0,0)
        txt_password = QLineEdit()
        txt_password.setEchoMode(QLineEdit.EchoMode.Password)
        btn_ver_pass = QToolButton()
        icon_ojo = dialogo.style().standardIcon(QStyle.StandardPixmap.SP_TitleBarNormalButton)
        btn_ver_pass.setIcon(icon_ojo)
        layout_pass.addWidget(txt_password)
        layout_pass.addWidget(btn_ver_pass)

        layout_grupo.addRow("Servidor / IP:", txt_server)
        layout_grupo.addRow("Puerto:", txt_port)
        layout_grupo.addRow("Base de Datos:", txt_database)
        layout_grupo.addRow("Usuario:", txt_user)
        layout_grupo.addRow("Contraseña:", widget_pass)

        layout_principal.addWidget(grupo)
        
        # Label de estado
        lbl_estado = QLabel("")
        lbl_estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_principal.addWidget(lbl_estado)

        # Aviso sutil
        lbl_aviso = QLabel("ℹ Nota: Para asegurar la estabilidad, reinicie el software tras guardar.")
        lbl_aviso.setObjectName("lblAviso")
        lbl_aviso.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_aviso.setWordWrap(True)
        layout_principal.addWidget(lbl_aviso)

        # Botones
        layout_botones = QHBoxLayout()
        btn_probar = QPushButton("Probar")
        btn_guardar = QPushButton("Guardar Cambios")
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("btnCancelar")

        layout_botones.addWidget(btn_probar)
        layout_botones.addStretch()
        layout_botones.addWidget(btn_cancelar)
        layout_botones.addWidget(btn_guardar)
        layout_principal.addLayout(layout_botones)

        # --- LÓGICA ---
        def cargar_valores():
            config = dotenv_values(env_path)
            txt_server.setText(config.get("SQL_SERVER", ""))
            txt_port.setText(config.get("SQL_PORT", "1433"))
            txt_database.setText(config.get("SQL_DATABASE", ""))
            txt_user.setText(config.get("SQL_USER", ""))
            txt_password.setText(config.get("SQL_PASSWORD", ""))

        def alternar_pass():
            if txt_password.echoMode() == QLineEdit.EchoMode.Password:
                txt_password.setEchoMode(QLineEdit.EchoMode.Normal)
            else:
                txt_password.setEchoMode(QLineEdit.EchoMode.Password)

        # ==============================================================
        # MODIFICACIÓN CLAVE: Usar pyodbc en lugar de QSqlDatabase
        # ==============================================================
        def probar():
            lbl_estado.setText("Probando conexión...")
            lbl_estado.setStyleSheet("color: blue;")
            lbl_estado.repaint()

            # Driver moderno (mismo que usamos en las otras partes del sistema)
            driver = '{ODBC Driver 17 for SQL Server}' 
            
            # String de conexión estilo pyodbc
            conn_str = (
                f'DRIVER={driver};'
                f'SERVER={txt_server.text()},{txt_port.text() or "1433"};'
                f'DATABASE={txt_database.text()};'
                f'UID={txt_user.text()};'
                f'PWD={txt_password.text()};'
                'TrustServerCertificate=yes;' # Vital para redes locales
                'Connection Timeout=3;'       # Para no congelar la UI mucho tiempo
            )

            try:
                # Intentamos conectar con la librería real
                conn = pyodbc.connect(conn_str)
                conn.close()
                
                lbl_estado.setText("✔ Conexión Exitosa")
                lbl_estado.setStyleSheet("background-color: #d4edda; color: #155724; border-radius: 4px; padding: 6px;")
            
            except Exception as e:
                # Mostramos el error resumido
                error_msg = str(e)
                if "Login failed" in error_msg:
                    texto_error = "✖ Error: Usuario o Contraseña incorrectos"
                elif "server was not found" in error_msg or "timeout" in error_msg:
                    texto_error = "✖ Error: No se encuentra el Servidor (IP/Puerto)"
                elif "Cannot open database" in error_msg:
                    texto_error = f"✖ Error: La base de datos '{txt_database.text()}' no existe"
                else:
                    texto_error = "✖ Falló la Conexión (Ver consola)"
                    print(error_msg)

                lbl_estado.setText(texto_error)
                lbl_estado.setStyleSheet("background-color: #f8d7da; color: #721c24; border-radius: 4px; padding: 6px;")

        def guardar():
            try:
                set_key(env_path, "SQL_SERVER", txt_server.text().strip())
                set_key(env_path, "SQL_PORT", txt_port.text().strip() or "1433")
                set_key(env_path, "SQL_DATABASE", txt_database.text().strip())
                set_key(env_path, "SQL_USER", txt_user.text().strip())
                set_key(env_path, "SQL_PASSWORD", txt_password.text())

                QMessageBox.information(
                    dialogo, 
                    "Configuración Guardada", 
                    "Los datos se han actualizado correctamente.\n\n"
                    "Reinicie la aplicación para aplicar los cambios."
                )
                dialogo.accept()

            except Exception as e:
                QMessageBox.critical(dialogo, "Error", f"No se pudo guardar: {e}")

        # Conexiones
        btn_ver_pass.clicked.connect(alternar_pass)
        btn_probar.clicked.connect(probar)
        btn_guardar.clicked.connect(guardar)
        btn_cancelar.clicked.connect(dialogo.reject)

        cargar_valores()
        dialogo.exec()