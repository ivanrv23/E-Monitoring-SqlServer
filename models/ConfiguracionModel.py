from services.security.apis.conexiones.conexion import Connection

class ConfiguracionModel:
    
    @staticmethod
    def mdlActualizarConfiguracionEjes(idproyecto, modulo, tipo, valejemin, valejemax, valinterpri, valintersecu, valinterdias):
        sqlinsert = """INSERT INTO ejes (id_proyecto, modulo_ejes, tipo_ejes, yinferior_ejes, ysuperior_ejes, yprincipal_ejes, ysecundario_ejes, xintervalo_ejes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);"""
        sqlupdate = """UPDATE ejes SET yinferior_ejes = ?, ysuperior_ejes = ?, yprincipal_ejes = ?, ysecundario_ejes = ?, xintervalo_ejes = ?
            WHERE id_proyecto = ? AND modulo_ejes = ? AND tipo_ejes = ?;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            
            # Verificar existencia
            cur.execute("SELECT COUNT(*) FROM ejes WHERE id_proyecto = ? AND modulo_ejes = ? AND tipo_ejes = ?;", (idproyecto, modulo, tipo))
            row = cur.fetchone()
            exists = row[0] if row else 0
            
            if exists > 0:
                cur.execute(sqlupdate, (valejemin, valejemax, valinterpri, valintersecu, valinterdias, idproyecto, modulo, tipo))
            else:
                cur.execute(sqlinsert, (idproyecto, modulo, tipo, valejemin, valejemax, valinterpri, valintersecu, valinterdias))
            
            conn.commit()
            return True
        except Exception as e:
            print("Error al registrar ejes:", e)
            return False  
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlActualizarConfiguracionEjesTDR(idproyecto, minejex, maxejex, xprimario, xsecundario, minejey, maxejey, yprimario, ysecundario):
        sqlinsert = """INSERT INTO ejestdr (id_proyecto, xminimo_eje, xmaximo_eje, interxprima_eje, interxsecu_eje, yminimo_eje,
        ymaximo_eje, interyprima_eje, interysecu_eje) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);"""
        sqlupdate = """UPDATE ejestdr SET xminimo_eje = ?, xmaximo_eje = ?, interxprima_eje = ?, interxsecu_eje = ?, yminimo_eje = ?,
        ymaximo_eje = ?, interyprima_eje = ?, interysecu_eje = ? WHERE id_proyecto = ?;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            
            # Verificar existencia
            cur.execute("SELECT COUNT(*) FROM ejestdr WHERE id_proyecto = ?;", (idproyecto,))
            row = cur.fetchone()
            exists = row[0] if row else 0
            
            if exists > 0:
                cur.execute(sqlupdate, (minejex, maxejex, xprimario, xsecundario, minejey, maxejey, yprimario, ysecundario, idproyecto))
            else:
                cur.execute(sqlinsert, (idproyecto, minejex, maxejex, xprimario, xsecundario, minejey, maxejey, yprimario, ysecundario))
            
            conn.commit()
            return True
        except Exception as e:
            print("Error al registrar ejes tdr:", e)
            return False  
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlObtenerConfiguracionEje(idproyecto, modulo, tipo):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            sql = "SELECT * FROM ejes WHERE id_proyecto = ? AND modulo_ejes = ? AND tipo_ejes = ?;"
            cur.execute(sql, (idproyecto, modulo, tipo))
            resultado = cur.fetchone()
            if resultado:
                return resultado
            else:
                return None 
        except Exception as e:
            print("Error al obtener info eje:", e)
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlObtenerConfiguracionEjeTDR(idproyecto):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            sql = "SELECT * FROM ejestdr WHERE id_proyecto = ?;"
            cur.execute(sql, (idproyecto,))
            resultado = cur.fetchone()
            if resultado:
                return resultado
            else:
                return None 
        except Exception as e:
            print("Error al obtener info eje tdr:", e)
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlActualizarComponente(nombre, idcomponente):
        sql = """UPDATE componentes SET nombre_componente = ? WHERE id_componente = ?;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (nombre, idcomponente))
            conn.commit()
            return True
        except Exception as e:
            print("Error al actualizar componente:", e)
            return False  
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlTraerEstiloEquipoGrafica(idproyecto, idinstrumento, tipoinstru):
        sql = """SELECT * FROM estilos WHERE id_proyecto = ? AND id_equipo = ? AND tipo_equipo = ?;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idproyecto, idinstrumento, tipoinstru))
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al consultar estilo: " + str(e))
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlAnularEstiloEquipoGrafica(idproyecto, idinstrumento, tipoinstru):
        sql = """DELETE FROM estilos WHERE id_proyecto = ? AND id_equipo = ? AND tipo_equipo = ?;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idproyecto, idinstrumento, tipoinstru))
            conn.commit()
            return True
        except Exception as e:
            print("Error al anular estilo: " + str(e))
            return False
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlGuardarEstiloEquipoGrafica(idproyecto, idinstrumento, tipolinea, grosorlinea, colorlinea, tipoinstru):
        sqlinsert = """INSERT INTO estilos (id_proyecto, id_equipo, tipo_linea, grosor_linea, color_linea, tipo_equipo)
            VALUES (?, ?, ?, ?, ?, ?);"""
        sqlupdate = """UPDATE estilos SET tipo_linea = ?, grosor_linea = ?, color_linea = ?
            WHERE id_proyecto = ? AND id_equipo = ? AND tipo_equipo = ?;"""
        
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            
            # Verificar existencia
            cur.execute("SELECT COUNT(*) FROM estilos WHERE id_proyecto = ? AND id_equipo = ? AND tipo_equipo = ?;", (idproyecto, idinstrumento, tipoinstru))
            row = cur.fetchone()
            exists = row[0] if row else 0
            
            if exists > 0:
                cur.execute(sqlupdate, (tipolinea, grosorlinea, colorlinea, idproyecto, idinstrumento, tipoinstru))
            else:
                cur.execute(sqlinsert, (idproyecto, idinstrumento, tipolinea, grosorlinea, colorlinea, tipoinstru))
            
            conn.commit()
            return True
        except Exception as e:
            print("Error al registrar estilo:", e)
            return False  
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlListarConfiguracionVisor(idproyecto):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            sql = "SELECT * FROM configuracionvisor WHERE id_proyecto = ?;"
            cur.execute(sql, (idproyecto,))
            resultado = cur.fetchone()
            if resultado:
                return resultado
            else:
                return None 
        except Exception as e:
            print("Error al obtener config visor:", e)
            return None
        finally:
            if conn: conn.close()
    
    @staticmethod
    def mdlRegistrarActualizarAjustesVisor(datos, existe):
        conn = None
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            
            if existe:
                camposupdate = ["color_fondo = ?", "tamanio_texto = ?", "color_texto = ?", "tamanio_prisma = ?",
                    "color_prisma = ?", "tamanio_inclinometro = ?", "color_inclinometro = ?", "tamanio_piezometro = ?",
                    "color_piezometro = ?", "tamanio_pluviometro = ?", "color_pluviometro = ?", "tamanio_celda = ?",
                    "color_celda = ?", "tamanio_acelerografo = ?", "color_acelerografo = ?", "tamanio_tdr = ?",
                    "color_tdr = ?", "tamanio_vector = ?"
                ]
                # Asegurar el orden de valores
                valoresupdate = [
                    datos['colorfondo'], datos['tamaniotexto'], datos['colortexto'], datos['tamanioprisma'], datos['colorprisma'],
                    datos['tamanioinclino'], datos['colorinclino'], datos['tamaniopiezo'], datos['colorpiezo'], datos['tamaniopluvio'],
                    datos['colorpluvio'], datos['tamaniocelda'], datos['colorcelda'], datos['tamanioacelero'], datos['coloracelero'],
                    datos['tamaniotdr'], datos['colortdr'], datos['tamaniovector'], datos['idproyecto']
                ]
                sql = f"UPDATE configuracionvisor SET {', '.join(camposupdate)} WHERE id_proyecto = ?;"
                cursor.execute(sql, valoresupdate)
            else:
                camposinsert = ["id_proyecto", "color_fondo", "tamanio_texto", "color_texto", "tamanio_prisma",
                    "color_prisma", "tamanio_inclinometro", "color_inclinometro", "tamanio_piezometro",
                    "color_piezometro", "tamanio_pluviometro", "color_pluviometro", "tamanio_celda",
                    "color_celda", "tamanio_acelerografo", "color_acelerografo", "tamanio_tdr", "color_tdr", "tamanio_vector"
                ]
                valoresinsert = [
                    datos['idproyecto'], datos['colorfondo'], datos['tamaniotexto'], datos['colortexto'],
                    datos['tamanioprisma'], datos['colorprisma'], datos['tamanioinclino'], datos['colorinclino'],
                    datos['tamaniopiezo'], datos['colorpiezo'], datos['tamaniopluvio'], datos['colorpluvio'], datos['tamaniocelda'],
                    datos['colorcelda'], datos['tamanioacelero'], datos['coloracelero'], datos['tamaniotdr'], datos['colortdr'],
                    datos['tamaniovector']
                ]
                placeholders = ', '.join(['?' for _ in camposinsert])
                sql = f"INSERT INTO configuracionvisor ({', '.join(camposinsert)}) VALUES ({placeholders});"
                cursor.execute(sql, valoresinsert)
                
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al registrar/actualizar ajustes visor: {e}")
            return False
        finally:
            if conn: conn.close()