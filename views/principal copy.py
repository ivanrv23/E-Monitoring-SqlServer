from PySide6.QtCore import QTimer
from datetime import datetime, date
from PySide6.QtWidgets import (QPushButton, QLineEdit, QLabel)
from services.security.apis.apiDB import ConnectionAPI
from services.security.encriptacion import Encriptacion
from services.security.licencia import Licencia
from utils.common.alertas import mostrar_mensaje
from views.main_view import MainView
from views.licencia_view import LicenciaView
from views.login import Login
from services.security.session import Session
from modules.license.procesarLicencia import ProcesarLicencia
from controllers.UsuarioController import UsuarioController

class Principal:
    timer = QTimer()
    
    @staticmethod
    def show_main_view():
        try:
            respuesta = Licencia.validarLicenciaExistente()
            if respuesta:
                Principal.verificar_licencia(respuesta)
            else:
                dialog_licencia = LicenciaView.DialogLicencia()
                dialog_licencia.show()
                ProcesarLicencia.verificar_registrar_licencia(dialog_licencia, Principal.show_main_view)
        except Exception as e:
            mostrar_mensaje("ERROR DE SOFTWARE", f"Error: \n{str(e)}", "error")

    @staticmethod
    def verificar_licencia(respuesta):
        try:
            serial = Encriptacion.decrypt(respuesta[1])
            fechafin = Encriptacion.decrypt(respuesta[3])
            fingerprint = Encriptacion.decrypt(respuesta[4])
            if Principal.timer.isActive():
                # Si el timer ya está activo, significa que ya pasó 1 día
                Principal.validarLicenciaOnline(serial, fingerprint)
            else:
                Principal.timer.setSingleShot(False)
                Principal.timer.start(86400000)  # 1 día en milisegundos
                Principal.timer.timeout.connect(lambda: Principal.validarLicenciaOnline(serial, fingerprint))
                # validar licencia localmente y alertar
                Principal.validarEquipoLicenciaDias(fingerprint, fechafin)
        except Exception as e:
            mostrar_mensaje("LICENCIA", f"Error: \n{str(e)}", "error")
    
    def validarLicenciaOnline(serial, fingerregistrado):
        fingerprint = Encriptacion.generate_fingerprint()
        if fingerregistrado == fingerprint:
            is_valid, data = ConnectionAPI.comprobarLicenciaOnline(serial, fingerprint)
            if is_valid:
                licencia_data = data.get('data')
                existe = data.get('existe')
                serial_licencia = licencia_data.get('serial_license')
                fecha_inicio = licencia_data.get('startdate_sale')
                fecha_fin = licencia_data.get('enddate_sale')
                documento = licencia_data.get('document_customer')
                cliente = licencia_data.get('name_customer')
                telefono = licencia_data.get('phone_customer')
                correo = licencia_data.get('email_customer')
                contacto = licencia_data.get('contact_customer')
                cargo = licencia_data.get('charge_customer')
                empresa = licencia_data.get('id_customer')
                venta = licencia_data.get('id_sale')
                if existe == "1":
                    resultado = Licencia.registrarLicencia(serial_licencia, fecha_inicio, fecha_fin, fingerprint, documento, cliente, telefono, correo, contacto, cargo, empresa, venta)
                    if resultado:
                        dialogologin = Login.mostrarLogin()
                        dialogologin.show()
                        Principal.validarInicioSesion(dialogologin)
                        dias_restantes = Principal.calcular_dias_restantes(fecha_fin)
                        if dias_restantes <= 7:
                            mostrar_mensaje("LICENCIA", f"Su licencia vence en {dias_restantes} días.", "advertencia")
                else:
                    mostrar_mensaje("LICENCIA", "No se pudo verificar la licencia.", "advertencia")
                    # abrir el registro de licencia para que pueda ingresar su serial
                    dialog_licencia = LicenciaView.DialogLicencia()
                    dialog_licencia.show()
                    ProcesarLicencia.verificar_registrar_licencia(dialog_licencia, Principal.show_main_view)
            else:
                mostrar_mensaje("LICENCIA", "Licencia vencida o no encontrada, contacte a su proveedor.", "advertencia")
                # abrir el registro de licencia para que pueda ingresar su serial
                dialog_licencia = LicenciaView.DialogLicencia()
                dialog_licencia.show()
                ProcesarLicencia.verificar_registrar_licencia(dialog_licencia, Principal.show_main_view)
        else:
            mostrar_mensaje("LICENCIA", "La licencia actual ya está registrada en otro equipo.", "advertencia")
            # abrir el registro de licencia para que pueda ingresar su serial
            dialog_licencia = LicenciaView.DialogLicencia()
            dialog_licencia.show()
            ProcesarLicencia.verificar_registrar_licencia(dialog_licencia, Principal.show_main_view)
    
    def validarInicioSesion(dialog):
        userinput = dialog.findChild(QLineEdit, "user_input")
        passinput = dialog.findChild(QLineEdit, "pass_input")
        botonlogin = dialog.findChild(QPushButton, "btn_ingresar")
        mensajelabel = dialog.findChild(QLabel, "mensaje_label")
        def iniciarSesion():
            botonlogin.setEnabled(False)
            usuario = userinput.text()
            contraseña = passinput.text()
            if usuario != "" and contraseña != "":
                empresa = UsuarioController.ctrlObtenerCodigoEmpresa()
                if empresa:
                    idempresa, idventa = empresa[0], empresa[1]
                    respuesta, msje = Session.login(usuario, contraseña, idventa)
                    if respuesta:
                        dialog.close()
                        principal = MainView.InterfazPrincipal()
                        principal.showMaximized()
                    else:
                        mensajelabel.setText(msje)
                        botonlogin.setEnabled(True)
                else:
                    mensajelabel.setText("Se generó un error.")
                    botonlogin.setEnabled(True)
            else:
                mensajelabel.setText("Campos vacíos.")
                botonlogin.setEnabled(True)
        userinput.returnPressed.connect(iniciarSesion)
        passinput.returnPressed.connect(iniciarSesion)
        botonlogin.clicked.connect(iniciarSesion)
    
    def validarEquipoLicenciaDias(fingerregistrado, fechafin):
        fingerprint = Encriptacion.generate_fingerprint()
        if fingerregistrado == fingerprint:
            dias_restantes = Principal.calcular_dias_restantes(fechafin)
            if dias_restantes < 0:
                mostrar_mensaje("LICENCIA", "Licencia vencida o no encontrada, contacte a su proveedor.", "advertencia")
                # abrir el registro de licencia para que pueda ingresar su serial
                dialog_licencia = LicenciaView.DialogLicencia()
                dialog_licencia.show()
                ProcesarLicencia.verificar_registrar_licencia(dialog_licencia, Principal.show_main_view)
            elif dias_restantes <= 7:
                dialogologin = Login.mostrarLogin()
                dialogologin.show()
                Principal.validarInicioSesion(dialogologin)
                mostrar_mensaje("LICENCIA", f"Su licencia vence en {dias_restantes} días.", "advertencia")
            else:
                dialogologin = Login.mostrarLogin()
                dialogologin.show()
                Principal.validarInicioSesion(dialogologin)
        else:
            mostrar_mensaje("LICENCIA", "La licencia actual ya está registrada en otro equipo.", "advertencia")
            # abrir el registro de licencia para que pueda ingresar su serial
            dialog_licencia = LicenciaView.DialogLicencia()
            dialog_licencia.show()
            ProcesarLicencia.verificar_registrar_licencia(dialog_licencia, Principal.show_main_view)
    
    def calcular_dias_restantes(fechafinstr):
        vencimiento = datetime.strptime(fechafinstr, "%Y-%m-%d").date()
        if not isinstance(vencimiento, date):
            return -1
        fecha_actual = datetime.now().date()
        diferencia = vencimiento - fecha_actual
        return diferencia.days
    