from PySide6.QtCore import QTimer
from datetime import datetime, date
from PySide6.QtWidgets import (QPushButton, QLineEdit, QLabel, QCheckBox)
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
from services.autenticacion.gestor2fa import Gestor2FA
from views.dialogos_2fa import DialogoValidar2FA, DialogoActivar2FA

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
    
    @staticmethod
    def validarInicioSesion(dialog):
        userinput = dialog.findChild(QLineEdit, "user_input")
        passinput = dialog.findChild(QLineEdit, "pass_input")
        botonlogin = dialog.findChild(QPushButton, "btn_ingresar")
        mensajelabel = dialog.findChild(QLabel, "mensaje_label")
        checkbox_2fa = dialog.findChild(QCheckBox, "check_2fa")
        
        # 1. ACTUALIZACIÓN AUTOMÁTICA DEL CHECKBOX
        # Cuando el usuario termina de escribir su nombre, verificamos si tiene 2FA
        def actualizar_estado_checkbox():
            usuario = userinput.text()
            if usuario:
                tiene_2fa = Gestor2FA.tiene_2fa_activado(usuario)
                # Bloqueamos la señal para no disparar eventos innecesarios
                checkbox_2fa.blockSignals(True)
                checkbox_2fa.setChecked(tiene_2fa)
                checkbox_2fa.blockSignals(False)
                
                if tiene_2fa:
                    checkbox_2fa.setToolTip("Desmarque para desactivar la seguridad 2FA (Requerirá código)")
                else:
                    checkbox_2fa.setToolTip("Marque para activar la seguridad 2FA")

        userinput.editingFinished.connect(actualizar_estado_checkbox)

        # 2. LÓGICA DE INICIO DE SESIÓN
        def iniciarSesion():
            botonlogin.setEnabled(False)
            usuario = userinput.text()
            contraseña = passinput.text()
            
            if usuario == "" or contraseña == "":
                mensajelabel.setText("Campos vacíos.")
                botonlogin.setEnabled(True)
                return

            empresa = UsuarioController.ctrlObtenerCodigoEmpresa()
            if not empresa:
                mensajelabel.setText("Error al obtener empresa.")
                botonlogin.setEnabled(True)
                return
                
            idempresa, idventa = empresa[0], empresa[1]
            
            # A) PRIMERO VALIDAMOS CREDENCIALES (Usuario/Pass)
            # Validar Login Base (SQL)
            respuesta, msje = Session.login(usuario, contraseña, idventa)
            
            if not respuesta:
                mensajelabel.setText(msje)
                botonlogin.setEnabled(True)
                return

            # --- LÓGICA 2FA MEJORADA ---
            tiene_2fa_real = Gestor2FA.tiene_2fa_activado(usuario)
            quiere_2fa = checkbox_2fa.isChecked()
            
            # Variable para controlar si abrimos el MainView
            entrar_al_sistema = False

            try:
                # CASO 1: TIENE 2FA Y CHECK MARCADO -> VERIFICACIÓN (Ruta Normal)
                if tiene_2fa_real and quiere_2fa:
                    # es_eliminacion=False
                    modal = DialogoValidar2FA(usuario, es_eliminacion=False, parent=dialog)
                    if modal.exec(): # Si devuelve True (Usuario dio a Verificar y fue OK)
                        entrar_al_sistema = True
                    else:
                        # Si devuelve False (Usuario dio a Cancelar)
                        mensajelabel.setText("Inicio de sesión cancelado.")
                        botonlogin.setEnabled(True)
                        return # Salimos, no entramos

                # CASO 2: NO TIENE 2FA Y CHECK DESMARCADO -> LOGIN SIMPLE (Inseguro)
                elif not tiene_2fa_real and not quiere_2fa:
                    entrar_al_sistema = True
                
                # CASO 3: NO TIENE 2FA PERO QUIERE (CHECK MARCADO) -> ACTIVAR
                elif not tiene_2fa_real and quiere_2fa:
                    modal = DialogoActivar2FA(usuario, parent=dialog)
                    if modal.exec():
                        # Se activó con éxito, entramos
                        entrar_al_sistema = True
                    else:
                        # Usuario canceló la activación
                        mensajelabel.setText("Activación cancelada. Ingrese sin 2FA si desea.")
                        checkbox_2fa.setChecked(False) # Desmarcamos sugerencia
                        botonlogin.setEnabled(True)
                        return

                # CASO 4: TIENE 2FA PERO QUIERE QUITARLO (CHECK DESMARCADO) -> ELIMINAR
                elif tiene_2fa_real and not quiere_2fa:
                    # es_eliminacion=True (Cambia textos y colores)
                    modal = DialogoValidar2FA(usuario, es_eliminacion=True, parent=dialog)
                    if modal.exec():
                        if Gestor2FA.eliminar_2fa(usuario):
                            mensajelabel.setText("Seguridad 2FA eliminada.")
                            entrar_al_sistema = True
                        else:
                            mensajelabel.setText("Error al eliminar 2FA.")
                            botonlogin.setEnabled(True)
                            return
                    else:
                        # Usuario canceló la eliminación
                        mensajelabel.setText("Eliminación cancelada.")
                        checkbox_2fa.setChecked(True) # Volvemos a marcar porque sigue activo
                        botonlogin.setEnabled(True)
                        return

                # FINAL: ENTRAR O NO
                if entrar_al_sistema:
                    dialog.close()
                    principal = MainView.InterfazPrincipal()
                    principal.showMaximized()

            except Exception as e:
                print(f"Error 2FA: {e}")
                mensajelabel.setText("Error interno de seguridad.")
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
    