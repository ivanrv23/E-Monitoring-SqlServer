from PySide6.QtWidgets import QLineEdit, QPushButton
from services.security.apis.apiDB import ConnectionAPI
from services.security.licencia import Licencia
from services.security.encriptacion import Encriptacion
from utils.common.alertas import mostrar_mensaje

class ProcesarLicencia:
    
    @staticmethod
    def verificar_registrar_licencia(dialog_licencia, callback):
        # Pasamos 'callback' para ejecutar después del registro
        serial_input = dialog_licencia.findChild(QLineEdit, "lb_serial")
        registrarLicencia = dialog_licencia.findChild(QPushButton, "btn_registrarSerial")
        def capturarSerial():
            serial = serial_input.text().strip()
            ProcesarLicencia.procesar_licencia(serial, dialog_licencia, callback)
        registrarLicencia.clicked.connect(capturarSerial)
    
    # Función para procesar la licencia
    @staticmethod
    def procesar_licencia(serial, dialog_licencia, callback):
        if serial != "":
            fingerprint = Encriptacion.generate_fingerprint()
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
                idventa = licencia_data.get('id_sale')
                if existe == "1":
                    resultado = Licencia.registrarLicencia(serial_licencia, fecha_inicio, fecha_fin, fingerprint, documento, cliente, telefono, correo, contacto, cargo, empresa, idventa)
                else:
                    resultado = Licencia.registrarLicenciaOnline(idventa, serial_licencia, fecha_inicio, fecha_fin, fingerprint, documento, cliente, telefono, correo, contacto, cargo, empresa)
                if resultado:
                    mostrar_mensaje("Información", "La licencia fue registrada/actualizada correctamente.", "informacion")
                    dialog_licencia.close()
                    callback()
                else:
                    mostrar_mensaje("Error", "Hubo un error al registrar/actualizar la licencia.", "error")
            else:
                mostrar_mensaje("Error", data["error"], "error")
    