import webbrowser
from PySide6.QtUiTools import QUiLoader
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtCore import QRegularExpression
from PySide6 import QtWidgets, QtCore
from utils.common.rutasarchivos import resource_path
from controllers.EmpresaController import EmpresaController
from utils.common.metodosGenerales import MetodosGenerales
from services.security.encriptacion import Encriptacion
from services.security.session import Session

class EmpresaConfiguracion:
    nombreempresa = ""
    rucempresa = ""
    telefonoempresa = ""
    correoempresa = ""
    logoempresa = None
    file_logo = None
    
    # MOSTRAR DIALOGO DE CONFIGURACIÓN DE EMPRESA
    def mostrarDialogoConfiguracionEmpresa():
        loader = QUiLoader()
        ui_file_path = resource_path("ui/ajustesempresa.ui")
        ui_file = loader.load(ui_file_path, None)
        # Configurar el cuadro de diálogo
        dialog = QtWidgets.QDialog()
        dialog.setWindowTitle("Configuración de E-Monitoring")
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(ui_file)
        dialog.setLayout(layout)
        #GENERAL 
        # INPUTS
        nombre_empresa = dialog.findChild(QtWidgets.QLineEdit, "input_empresa")
        codigo_ruc = dialog.findChild(QtWidgets.QLineEdit, "input_ruc")
        numero_contacto = dialog.findChild(QtWidgets.QLineEdit, "input_contacto")
        correo_electronico = dialog.findChild(QtWidgets.QLineEdit, "input_correo")
        confirmarConfiguracion = dialog.findChild(QtWidgets.QPushButton, "btn_aceptar")
        subirImagen = dialog.findChild(QtWidgets.QPushButton, "btn_subir_imagen")
        nombre_logo = dialog.findChild(QtWidgets.QLineEdit, f"input_nombre_logo")
        lb_vistaPrevia = dialog.findChild(QtWidgets.QLabel, f"lb_vista_logo")
        #LICENCIA
        # LABELS
        lblcliente = dialog.findChild(QtWidgets.QLabel, "label_cliente")
        lbllicencia = dialog.findChild(QtWidgets.QLabel, "label_serial")
        lblfecha = dialog.findChild(QtWidgets.QLabel, "label_vencimiento")
        lblusuario = dialog.findChild(QtWidgets.QLabel, "label_usuario")
        # BOTONES
        botoncomprar = dialog.findChild(QtWidgets.QPushButton, "btn_comprar")        
        # VALIDACIONES
        ruc_validator = QRegularExpressionValidator(QRegularExpression(r"^\d{0,11}$"))  # Solo 11 dígitos
        codigo_ruc.setValidator(ruc_validator)
        contacto_validator = QRegularExpressionValidator(QRegularExpression(r"^[\d\+\-\s]+$"))  # Acepta números, +, -, y espacios
        numero_contacto.setValidator(contacto_validator)
        # VALORES DEFECTO
        lblusuario.setText(Session.get_username() or "")
        empresa, licencia = EmpresaController.ctrlObtenerDatosEmpresa()
        if empresa:            
            nombre_empresa.setText(empresa[1])
            codigo_ruc.setText(empresa[2])
            numero_contacto.setText(empresa[3])
            correo_electronico.setText(empresa[4])
            if empresa[5]:  
                # Convertir BLOB a pixmap
                pixmap = MetodosGenerales.convertir_blob_a_pixmap(empresa[5])
                pixmap = pixmap.scaled(120, 120, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
                # Mostrar la imagen en el QLabel
                lb_vistaPrevia.setPixmap(pixmap)
        # SECCION LICENCIA
        if licencia:
            serial = Encriptacion.decrypt(licencia[1])
            fechafin = Encriptacion.decrypt(licencia[3])
            compania = licencia[7]
            lblcliente.setText(compania)
            lbllicencia.setText(serial)
            lblfecha.setText(fechafin)
        def abrirWebLicencias():
            url = "https://www.eigha.pe"
            webbrowser.open(url)
        # # Inicializar botones
        subirImagen.clicked.connect(lambda: EmpresaConfiguracion.cargarImagenLabel(nombre_logo, lb_vistaPrevia))
        confirmarConfiguracion.clicked.connect(lambda: EmpresaConfiguracion.guardarConfiguracion(dialog))
        botoncomprar.clicked.connect(abrirWebLicencias)
        # mostrar dialogo
        dialog.exec()

    def cargarImagenLabel(nombre_logo, lb_vistaPrevia):
        logo = MetodosGenerales.cargarImagenLocal(lb_vistaPrevia, nombre_logo)
        EmpresaConfiguracion.file_logo = logo
        
    def guardarConfiguracion(dialog):
        # Obtener los valores de los campos de texto
        nombre_empresa = dialog.findChild(QtWidgets.QLineEdit, "input_empresa").text()
        codigo_ruc = dialog.findChild(QtWidgets.QLineEdit, "input_ruc").text()
        numero_contacto = dialog.findChild(QtWidgets.QLineEdit, "input_contacto").text()
        correo_electronico = dialog.findChild(QtWidgets.QLineEdit, "input_correo").text()
        # Lista de datos que se enviarán al controlador
        lista_datos = {
            "nombre_empresa": nombre_empresa,
            "codigo_ruc": codigo_ruc,
            "numero_contacto": numero_contacto,
            "correo_electronico": correo_electronico
        }
        # Solo agregar logo si está disponible
        if EmpresaConfiguracion.file_logo:
            imagen_blob = MetodosGenerales.convertir_imagen_a_blob(EmpresaConfiguracion.file_logo)
            lista_datos["logo"] = imagen_blob
        else:
            lista_datos["logo"] = None
        # Enviar lista_datos al controlador para ser procesado y almacenado en la base de datos
        respuesta = EmpresaController.ctrlRegistrarActualizarInformacionEmpresa(lista_datos)
        if respuesta:
            dialog.close()
            EmpresaConfiguracion.actualizarInfoEmpresa()
        else:
            QtWidgets.QMessageBox.critical(dialog, "ERROR", f"Error al guardar configuración")
    
    def actualizarInfoEmpresa():
        empresa = EmpresaController.ctrlObtenerDatosConfiguracionEmpresa()
        if empresa:
            EmpresaConfiguracion.nombreempresa = empresa[1]
            EmpresaConfiguracion.rucempresa = empresa[2]
            EmpresaConfiguracion.telefonoempresa = empresa[3]
            EmpresaConfiguracion.correoempresa = empresa[4]
            EmpresaConfiguracion.logoempresa = empresa[5]
    
    def obtenerDataEmpresa():
        data = [
            EmpresaConfiguracion.nombreempresa,
            EmpresaConfiguracion.rucempresa,
            EmpresaConfiguracion.telefonoempresa,
            EmpresaConfiguracion.correoempresa,
            EmpresaConfiguracion.logoempresa
        ]
        return data