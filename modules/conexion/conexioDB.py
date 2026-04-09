import pyodbc
from pathlib import Path
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QPushButton, QLabel, QGroupBox, 
    QToolButton, QStyle, QFrame, QMessageBox, QTableWidget, QTableWidgetItem, QTextEdit, QComboBox, QSpinBox, QMenu)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIntValidator, QAction
from utils.generic.listaiconos import ListaIconos
from utils.generic.cargariconos import cargarIcono
from utils.common.rutasarchivos import resource_path
from utils.common.alertas import mostrar_mensaje
from controllers.InterfazController import InterfazController
from controllers.ProyectoController import ProyectoController
from controllers.UsuarioController import UsuarioController
from services.sync.sync_manager import SyncManager

# Importamos las funciones para manejar el archivo .env
from dotenv import set_key, dotenv_values

class ConexionDB:

    @staticmethod
    def configuracion():
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
                    texto_error = "Error: Usuario o Contraseña incorrectos"
                elif "server was not found" in error_msg or "timeout" in error_msg:
                    texto_error = "Error: No se encuentra el Servidor (IP/Puerto)"
                elif "Cannot open database" in error_msg:
                    texto_error = f"Error: La base de datos '{txt_database.text()}' no existe"
                else:
                    texto_error = "Falló la Conexión (Ver consola)"
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

    def mostrarConfiguracionesSqlServer():
        loader = QUiLoader()
        ui_file_path = resource_path("ui/conexiones.ui")
        ui_file = loader.load(ui_file_path, None)
        # Configurar el cuadro de diálogo
        dialog = QDialog()
        dialog.setWindowTitle("Conexiones a SQL Server")
        layout = QVBoxLayout()
        layout.addWidget(ui_file)
        dialog.setLayout(layout)
        # Obtener elementos para interactuar
        botonnuevo = dialog.findChild(QPushButton, "btn_nueva_conexion")
        cargarIcono(botonnuevo, ListaIconos.ICONOS["nuevo"])
        tabladatos = dialog.findChild(QTableWidget, "table_conexiones")
        tabladatos.setContextMenuPolicy(Qt.CustomContextMenu)
        botonaceptar = dialog.findChild(QPushButton, "btn_aceptar")
        # Mostrar data en la tabla
        ESTADOS = {"1": "Conectado", "0": "Desconectado", 1: "Conectado", 0: "Desconectado"}
        conexiones = UsuarioController.ctrlObtenerConexiones()
        if conexiones:
            tabladatos.setRowCount(len(conexiones))
            tabladatos.setColumnCount(13)
            for fila, datos_fila in enumerate(conexiones):
                for columna, dato in enumerate(datos_fila):
                    texto = ESTADOS.get(dato, str(dato)) if columna == 10 else str(dato)
                    tabladatos.setItem(fila, columna, QTableWidgetItem(texto))
            # Ocultar columnas de IDs
            tabladatos.setColumnHidden(6, True)
            tabladatos.setColumnHidden(7, True)
            tabladatos.setColumnHidden(11, True)
            tabladatos.setColumnHidden(12, True)
        def refrescarTabla():
            conexiones = UsuarioController.ctrlObtenerConexiones()
            tabladatos.clearContents()
            if conexiones:
                tabladatos.setRowCount(len(conexiones))
                tabladatos.setColumnCount(13)
                for fila, datos_fila in enumerate(conexiones):
                    for columna, dato in enumerate(datos_fila):
                        texto = ESTADOS.get(dato, str(dato)) if columna == 10 else str(dato)
                        tabladatos.setItem(fila, columna, QTableWidgetItem(texto))
                # Ocultar columnas de IDs
                tabladatos.setColumnHidden(6, True)
                tabladatos.setColumnHidden(7, True)
                tabladatos.setColumnHidden(11, True)
                tabladatos.setColumnHidden(12, True)
        def aceptarConexiones():
            dialog.close()
        # Inicializar botones
        tabladatos.customContextMenuRequested.connect(lambda position: ConexionDB.mostrarMenuTabla(tabladatos, position, refrescarTabla))
        botonnuevo.clicked.connect(lambda: ConexionDB.dialogoNuevaConexion(refrescarTabla))
        botonaceptar.clicked.connect(aceptarConexiones)
        dialog.exec()

    def dialogoNuevaConexion(on_success=None):
        loaderLoading = QUiLoader()
        ui_file_path = resource_path("ui/nuevaconexion.ui")
        ui_file = loaderLoading.load(ui_file_path, None)
        dialogo = QDialog()
        dialogo.setWindowTitle("Nueva Conexión")
        layout_procesar_data = QVBoxLayout()
        layout_procesar_data.addWidget(ui_file)
        dialogo.setLayout(layout_procesar_data)
        # Validando inputs
        comboProyectos = dialogo.findChild(QComboBox, "cb_proyectos")
        comboInstrumentos = dialogo.findChild(QComboBox, "cb_instrumentos")
        inputServer = dialogo.findChild(QLineEdit, 'input_server')
        inputPuerto = dialogo.findChild(QLineEdit, 'input_puerto')
        inputDatabase = dialogo.findChild(QLineEdit, 'input_database')
        inputUsuario = dialogo.findChild(QLineEdit, 'input_usuario')
        inputPassword = dialogo.findChild(QLineEdit, 'input_password')
        inputDato = dialogo.findChild(QLineEdit, 'input_dato')
        inputFrecuencia = dialogo.findChild(QSpinBox, 'spin_frecuencia')
        inputGrupos = dialogo.findChild(QTextEdit, 'input_consulta_grupos')
        inputLecturas = dialogo.findChild(QTextEdit, 'input_consulta_lecturas')
        comboEstados = dialogo.findChild(QComboBox, "cb_estados")
        lblrespuesta = dialogo.findChild(QLabel, "label_mensaje")
        botonGuardar = dialogo.findChild(QPushButton, "btn_registrar")
        # Llenar proyectos
        proyectos = InterfazController.ctrlListarProyectos()
        if proyectos:
            for fila in proyectos:
                comboProyectos.addItem(str(fila[1]), fila[0])
        else:
            comboProyectos.addItem("Sin Proyectos", 0)
        # Llenar instrumentos
        comboInstrumentos.addItem("Prismas")
        comboInstrumentos.addItem("Piezómetros")
        comboInstrumentos.addItem("Celdas")
        # comboInstrumentos.addItem("Inclinómetros")
        # Llenar estados
        comboEstados.addItem("Conectado", 1)
        comboEstados.addItem("Desconectado", 0)
        def guardarInfoConexion():
            idproyecto = comboProyectos.currentData()
            instrumento = comboInstrumentos.currentText()
            servidor = inputServer.text().strip()
            puerto = inputPuerto.text().strip()
            database = inputDatabase.text().strip()
            usuario = inputUsuario.text().strip()
            contraseña = inputPassword.text().strip()
            consultaGrupos = inputGrupos.toPlainText().strip()
            consultaLecturas = inputLecturas.toPlainText().strip()
            ultimoid = inputDato.text().strip()
            frecuencia = inputFrecuencia.value()
            estado = comboEstados.currentData()
            # Validaciones
            if not idproyecto or idproyecto == 0:
                lblrespuesta.setText("Seleccione un proyecto válido")
                return
            if not instrumento:
                lblrespuesta.setText("Seleccione un instrumento")
                return
            if not servidor:
                lblrespuesta.setText("El servidor no puede estar vacío")
                return
            if not puerto or puerto == "0":
                lblrespuesta.setText("El puerto no puede ser vacío o 0")
                return
            if not database:
                lblrespuesta.setText("La base de datos no puede estar vacía")
                return
            if not usuario:
                lblrespuesta.setText("El usuario no puede estar vacío")
                return
            if not contraseña:
                lblrespuesta.setText("La contraseña no puede estar vacía")
                return
            if not consultaGrupos:
                lblrespuesta.setText("La consulta de Grupos no puede estar vacía")
                return
            if not consultaLecturas:
                lblrespuesta.setText("La consulta de Lecturas no puede estar vacía")
                return
            if not ultimoid:
                ultimoid = 0
            else:
                try:
                    ultimoid = int(ultimoid)
                except (TypeError, ValueError):
                    ultimoid = 0
            if frecuencia == 0:
                lblrespuesta.setText("La frecuencia debe ser mayor a 0")
                return
            datos = [idproyecto, instrumento, servidor, puerto, database, usuario, contraseña, consultaGrupos, consultaLecturas, ultimoid, frecuencia, estado]
            respuesta = UsuarioController.ctrlGuardarNuevaConexion(datos)
            if respuesta:
                dialogo.accept()
                if on_success:
                    on_success()
                SyncManager.recargar_conexiones()
            else:
                lblrespuesta.setText("Error al registrar.")
                lblrespuesta.setStyleSheet("color: red;")
        # conectar botones
        botonGuardar.clicked.connect(guardarInfoConexion)
        dialogo.exec()
    
    def mostrarMenuTabla(table, position, on_success=None):
        index = table.indexAt(position)
        if not index.isValid():
            # Si el índice no es válido, intenta obtener la fila desde el encabezado vertical
            vertical_header = table.verticalHeader()
            row = vertical_header.logicalIndexAt(position.x(), position.y())
            if row >= 0:
                index = table.model().index(row, 0)
            else:
                return
        row = index.row()
        # Capturar los valores de la filas
        instrumento = table.model().data(table.model().index(row, 1), Qt.DisplayRole)
        servidor = table.model().data(table.model().index(row, 2), Qt.DisplayRole)
        puerto = table.model().data(table.model().index(row, 3), Qt.DisplayRole)
        database = table.model().data(table.model().index(row, 4), Qt.DisplayRole)
        usuario = table.model().data(table.model().index(row, 5), Qt.DisplayRole)
        consultagrupos = table.model().data(table.model().index(row, 6), Qt.DisplayRole)
        consultalecturas = table.model().data(table.model().index(row, 7), Qt.DisplayRole)
        ultimoid = table.model().data(table.model().index(row, 8), Qt.DisplayRole)
        frecuencia = table.model().data(table.model().index(row, 9), Qt.DisplayRole)
        estado = table.model().data(table.model().index(row, 10), Qt.DisplayRole)
        idconexion = table.model().data(table.model().index(row, 11), Qt.DisplayRole)
        idproyecto = table.model().data(table.model().index(row, 12), Qt.DisplayRole)
        ConexionDB.generarMenuTabla(position, table, instrumento, servidor, puerto, database, usuario, consultagrupos, consultalecturas, ultimoid, frecuencia, estado, idconexion, idproyecto, on_success)
    
    def generarMenuTabla(position, table, instrumento, servidor, puerto, database, usuario, consultagrupos, consultalecturas, ultimoid, frecuencia, estado, idconexion, idproyecto, on_success=None):
        # Crear menú contextual
        menu = QMenu()
        edit_action = QAction("Editar Conexión", table)
        delete_action = QAction("Eliminar Conexión", table)
        # Conectar las acciones con los valores de la fila
        edit_action.triggered.connect(lambda: ConexionDB.dialogoActualizarConexion(instrumento, servidor, puerto, database, usuario, consultagrupos, consultalecturas, ultimoid, frecuencia, estado, idconexion, idproyecto, on_success))
        delete_action.triggered.connect(lambda: ConexionDB.delete_row_conexion(idconexion, instrumento, servidor, on_success))
        # Añadir las acciones al menú
        menu.addAction(edit_action)
        menu.addAction(delete_action)
        # Mostrar menú contextual en la posición del clic
        menu.exec(table.viewport().mapToGlobal(position))
    
    def dialogoActualizarConexion(instrumento, servidor, puerto, database, usuario, consultagrupos, consultalecturas, ultimoid, frecuencia, estado, idconexion, idproyecto, on_success=None):
        loaderLoading = QUiLoader()
        ui_file_path = resource_path("ui/nuevaconexion.ui")
        ui_file = loaderLoading.load(ui_file_path, None)
        dialogo = QDialog()
        dialogo.setWindowTitle("Editar Conexión")
        layout_procesar_data = QVBoxLayout()
        layout_procesar_data.addWidget(ui_file)
        dialogo.setLayout(layout_procesar_data)
        # Validando inputs
        comboProyectos = dialogo.findChild(QComboBox, "cb_proyectos")
        comboInstrumentos = dialogo.findChild(QComboBox, "cb_instrumentos")
        inputServer = dialogo.findChild(QLineEdit, 'input_server')
        inputPuerto = dialogo.findChild(QLineEdit, 'input_puerto')
        inputDatabase = dialogo.findChild(QLineEdit, 'input_database')
        inputUsuario = dialogo.findChild(QLineEdit, 'input_usuario')
        inputPassword = dialogo.findChild(QLineEdit, 'input_password')
        inputDato = dialogo.findChild(QLineEdit, 'input_dato')
        inputFrecuencia = dialogo.findChild(QSpinBox, 'spin_frecuencia')
        inputGrupos = dialogo.findChild(QTextEdit, 'input_consulta_grupos')
        inputLecturas = dialogo.findChild(QTextEdit, 'input_consulta_lecturas')
        comboEstados = dialogo.findChild(QComboBox, "cb_estados")
        lblrespuesta = dialogo.findChild(QLabel, "label_mensaje")
        botonGuardar = dialogo.findChild(QPushButton, "btn_registrar")
        # Llenar proyectos
        proyectos = InterfazController.ctrlListarProyectos()
        if proyectos:
            for fila in proyectos:
                comboProyectos.addItem(str(fila[1]), fila[0])
        else:
            comboProyectos.addItem("Sin Proyectos", 0)
        # Llenar instrumentos
        comboInstrumentos.addItem("Prismas")
        comboInstrumentos.addItem("Piezómetros")
        comboInstrumentos.addItem("Celdas")
        # comboInstrumentos.addItem("Inclinómetros")
        # Llenar estados
        comboEstados.addItem("Conectado", 1)
        comboEstados.addItem("Desconectado", 0)
        # Cargar la info en el formulario
        comboProyectos.setCurrentIndex(comboProyectos.findData(idproyecto))
        comboInstrumentos.setCurrentText(str(instrumento))
        inputServer.setText(str(servidor))
        inputPuerto.setText(str(puerto))
        inputDatabase.setText(str(database))
        inputUsuario.setText(str(usuario))
        inputPassword.setText("")
        inputGrupos.setPlainText(str(consultagrupos))
        inputLecturas.setPlainText(str(consultalecturas))
        inputDato.setText(ultimoid)
        inputFrecuencia.setValue(int(frecuencia))
        comboEstados.setCurrentText(str(estado))
        def actualizarInfoConexion():
            idproyecto = comboProyectos.currentData()
            instrumento = comboInstrumentos.currentText()
            servidor = inputServer.text().strip()
            puerto = inputPuerto.text().strip()
            database = inputDatabase.text().strip()
            usuario = inputUsuario.text().strip()
            contraseña = inputPassword.text().strip()
            consultagrupos = inputGrupos.toPlainText().strip()
            consultalecturas = inputLecturas.toPlainText().strip()
            ultimodato = inputDato.text().strip()
            frecuencia = inputFrecuencia.value()
            estado = comboEstados.currentData()
            password = None
            # Validaciones
            if not idproyecto or idproyecto == 0:
                lblrespuesta.setText("Seleccione un proyecto válido")
                return
            if not instrumento:
                lblrespuesta.setText("Seleccione un instrumento")
                return
            if not servidor:
                lblrespuesta.setText("El servidor no puede estar vacío")
                return
            if not puerto or puerto == "0":
                lblrespuesta.setText("El puerto no puede ser vacío o 0")
                return
            if not database:
                lblrespuesta.setText("La base de datos no puede estar vacía")
                return
            if not usuario:
                lblrespuesta.setText("El usuario no puede estar vacío")
                return
            if contraseña:
                password = contraseña
            if not consultagrupos:
                lblrespuesta.setText("La consulta de Grupos no puede estar vacía")
                return
            if not consultalecturas:
                lblrespuesta.setText("La consulta de Lecturas no puede estar vacía")
                return
            if not ultimodato:
                ultimodato = 0
            else:
                try:
                    ultimodato = int(ultimodato)
                except (TypeError, ValueError):
                    ultimodato = 0
            if frecuencia == 0:
                lblrespuesta.setText("La frecuencia debe ser mayor a 0")
                return
            datos = [idproyecto, instrumento, servidor, puerto, database, usuario, password, consultagrupos, consultalecturas, ultimodato, frecuencia, estado, idconexion]
            respuesta = UsuarioController.ctrlActualizarConexion(datos)
            if respuesta:
                dialogo.accept()
                if on_success:
                    on_success()
            else:
                lblrespuesta.setText("Error al editar.")
                lblrespuesta.setStyleSheet("color: red;")
        # conectar botones
        botonGuardar.clicked.connect(actualizarInfoConexion)
        dialogo.exec()
    
    def delete_row_conexion(idconexion, instrumento, servidor, on_success=None):
        dlg = QMessageBox()
        dlg.setWindowTitle("Eliminar Conexión")
        dlg.setText(f"¿Está seguro de eliminar la conexión de {instrumento} \n y del servidor {servidor}?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            respuesta = UsuarioController.ctrlEliminarConexion(idconexion)
            if respuesta:
                if on_success:
                    on_success()
            else:
                mostrar_mensaje("Eliminar Conexión", "No se pudo eliminar la conexión.", "advertencia")
