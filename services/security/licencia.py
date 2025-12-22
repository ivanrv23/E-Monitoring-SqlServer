from services.security.apis.conexiones.conexion import Connection
from services.security.apis.apiDB import ConnectionAPI
from services.security.encriptacion import Encriptacion

class Licencia:
    
    @staticmethod  # Es buena práctica poner esto si no usas 'self'
    def validarLicenciaExistente():
        conn = None
        try:
            conn = Connection.connectionDB()
            if conn is None:
                return None

            # SQL Server usa sintaxis estandar, esto funciona igual
            sql = "SELECT * FROM licencias;" 
            
            cur = conn.cursor()
            cur.execute(sql)
            
            # En pyodbc fetchone devuelve un objeto Row, que actúa como tupla
            row = cur.fetchone()
            
            if row:
                # Opcional: Convertir a tupla o diccionario si tu sistema lo espera
                return row 
            else:
                return None
        except Exception as e: # Capturamos error genérico o pyodbc.Error
            print(f"Error al validar licencia: {e}")
            return None
        finally:
            if conn:
                conn.close()
                
    @staticmethod
    def registrarLicencia(serial, fechaini, fechafin, fingerprint, documento, cliente, telefono, correo, contacto, cargo, empresa, venta):
        conn = None
        try:
            # NOTA: Si 'fechaini' va encriptada, la columna en SQL Server DEBE ser NVARCHAR, no DATETIME.
            datos = (
                Encriptacion.encrypt(serial),
                Encriptacion.encrypt(fechaini),
                Encriptacion.encrypt(fechafin),
                Encriptacion.encrypt(fingerprint), 
                1, # estado_licencia
                documento, cliente, telefono, correo, contacto, cargo, empresa, venta
            )
            
            conn = Connection.connectionDB()
            if conn is None: return False
            
            cursor = conn.cursor()
            
            # Limpiar tabla (TRUNCATE es más rápido en SQL Server, pero DELETE es más seguro compatible)
            cursor.execute("DELETE FROM licencias;")
            
            # pyodbc usa ? igual que sqlite, así que esta query se mantiene igual
            query = """INSERT INTO licencias (
                serial_licencia, inicio_licencia, final_licencia, dispositivo_licencia,
                estado_licencia, documento_licencia, cliente_licencia, telefono_licencia, 
                email_licencia, contacto_licencia, cargo_licencia, codigo_empresa, codigo_venta
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""
            
            cursor.execute(query, datos)
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al registrar licencia: {e}")
            if conn: conn.rollback() # Recomendable hacer rollback si falla
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def registrarLicenciaOnline(idventa, serial, fechaini, fechafin, fingerprint, documento, cliente, telefono, correo, contacto, cargo, empresa):
        # Asumiendo que ConnectionAPI no cambia su lógica interna
        respuesta, data = ConnectionAPI.registrarLicenseOnline(idventa, fingerprint)
        
        if respuesta:
            conn = None
            try:
                datos = (
                    Encriptacion.encrypt(serial),
                    Encriptacion.encrypt(fechaini),
                    Encriptacion.encrypt(fechafin),
                    Encriptacion.encrypt(fingerprint), 
                    1, 
                    documento, cliente, telefono, correo, contacto, cargo, empresa, idventa
                )
                
                conn = Connection.connectionDB()
                if conn is None: return False

                cursor = conn.cursor()
                cursor.execute("DELETE FROM licencias;")
                
                query = """INSERT INTO licencias (
                    serial_licencia, inicio_licencia, final_licencia, dispositivo_licencia,
                    estado_licencia, documento_licencia, cliente_licencia, telefono_licencia, 
                    email_licencia, contacto_licencia, cargo_licencia, codigo_empresa, codigo_venta
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""
                
                cursor.execute(query, datos)
                conn.commit()
                return True
            except Exception as e:
                print(f"Error online: {e}")
                if conn: conn.rollback()
                return False
            finally:
                if conn:
                    conn.close()
        else:
            return False