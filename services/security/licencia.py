from sqlite3 import Error
from services.security.apis.conexiones.conexion import Connection
from services.security.apis.apiDB import ConnectionAPI
from services.security.encriptacion import Encriptacion

class Licencia:
    
    def validarLicenciaExistente():
        try:
            conn = Connection.connectionDB()
            sql = """SELECT * FROM licencias;"""
            
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Error as e:
            return None
        finally:
            if conn:
                conn.close()
                
    def registrarLicencia(serial, fechaini, fechafin, fingerprint, documento, cliente, telefono, correo, contacto, cargo, empresa, venta):
        try:
            datos = (
                Encriptacion.encrypt(serial),
                Encriptacion.encrypt(fechaini),
                Encriptacion.encrypt(fechafin),
                Encriptacion.encrypt(fingerprint), 1,
                documento, cliente, telefono, correo, contacto, cargo, empresa, venta
            )
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # Limpiar la tabla antes de insertar
            cursor.execute("DELETE FROM licencias;")
            query = """INSERT INTO licencias (serial_licencia, inicio_licencia, final_licencia, dispositivo_licencia,
            estado_licencia, documento_licencia, cliente_licencia, telefono_licencia, email_licencia, contacto_licencia,
            cargo_licencia, codigo_empresa, codigo_venta) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""
            cursor.execute(query, datos)
            conn.commit()
            return True
        except Exception as e:
            return False
        finally:
            conn.close()

    def registrarLicenciaOnline(idventa, serial, fechaini, fechafin, fingerprint, documento, cliente, telefono, correo, contacto, cargo, empresa):
        respuesta, data = ConnectionAPI.registrarLicenseOnline(idventa, fingerprint)
        if respuesta:
            try:
                datos = (
                    Encriptacion.encrypt(serial),
                    Encriptacion.encrypt(fechaini),
                    Encriptacion.encrypt(fechafin),
                    Encriptacion.encrypt(fingerprint), 1,
                    documento, cliente, telefono, correo, contacto, cargo, empresa, idventa
                )
                conn = Connection.connectionDB()
                cursor = conn.cursor()
                # Limpiar la tabla antes de insertar
                cursor.execute("DELETE FROM licencias;")
                query = """INSERT INTO licencias (serial_licencia, inicio_licencia, final_licencia, dispositivo_licencia,
                estado_licencia, documento_licencia, cliente_licencia, telefono_licencia, email_licencia, contacto_licencia,
                cargo_licencia, codigo_empresa, codigo_venta) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""
                cursor.execute(query, datos)
                conn.commit()
                return True
            except Exception as e:
                return False
            finally:
                conn.close()
        else:
            return False
    