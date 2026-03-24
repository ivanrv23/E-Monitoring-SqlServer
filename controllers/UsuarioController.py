from models.UsuarioModel import UsuarioModel

class UsuarioController:
    
    def ctrlObtenerCodigoEmpresa():
        respuesta = UsuarioModel.mdlObtenerCodigoEmpresa()
        return respuesta
    
    def ctrlObtenerListaUsuarios(idventa):
        respuesta, data = UsuarioModel.mdlObtenerListaUsuarios(idventa)
        return respuesta, data
    
    def ctrlGuardarUsuario(documento, nombres, apellidos, username, contraseña, rol, idventa):
        respuesta, data = UsuarioModel.mdlGuardarUsuario(documento, nombres, apellidos, username, contraseña, rol, idventa)
        return respuesta, data
    
    def ctrlActualizarUsuario(documento, nombres, apellidos, username, rol, estado, idusuario):
        respuesta, data = UsuarioModel.mdlActualizarUsuario(documento, nombres, apellidos, username, rol, estado, idusuario)
        return respuesta, data
    
    def ctrlCambiarContraseñaUsuario(contraseña, idusuario):
        respuesta, data = UsuarioModel.mdlCambiarContraseñaUsuario(contraseña, idusuario)
        return respuesta, data
    
    def ctrlCambiarEstadoUsuario(estado, idusuario):
        respuesta, data = UsuarioModel.mdlCambiarEstadoUsuario(estado, idusuario)
        return respuesta, data
    
    def ctrlComprobarUsuarioContraseña(usuario, contraseña, idventa):
        respuesta, data = UsuarioModel.mdlComprobarUsuarioContraseña(usuario, contraseña, idventa)
        return respuesta, data
    
    def ctrlRealizarCopia():
        try:
            # ── 1. EXTRACT ──────────────────────────────────
            datos_origen = UsuarioModel.mdlTraerPrismasOriginal()
 
            if not datos_origen:
                print("No se encontraron prismas en la BD origen.")
                return False
            datos_procesados = []
            for row in datos_origen:
                # Desempacar campos del origen
                # Orden según SELECT en mdlTraerPrismasOriginal:
                # 0: nombre_prisma
                # 1: hora_prisma
                # 2: distancia_prisma
                # 3: este_target
                # 4: norte_target
                # 5: elevacion_target
                # 6: angulo_horizontal
                # 7: angulo_vertical
 
                nombre_orig      = row[2]
                hora_orig        = row[4]
                distancia_orig   = float(row[7]) if row[7] is not None else 0.0
                este_orig        = float(row[8]) if row[8] is not None else 0.0
                norte_orig       = float(row[9]) if row[9] is not None else 0.0
                elevacion_orig   = float(row[10]) if row[10] is not None else 0.0
                horiz_orig       = row[5]
                verti_orig       = row[6]
 
                # (state_prisma y estado_prisma ya están hardcodeados en el SQL como 1,1)
                tupla = (
                    nombre_orig,   # nombre_prisma
                    hora_orig,        # hora_prisma
                    distancia_orig,   # distancia_prisma
                    este_orig,        # este_target
                    norte_orig,       # norte_target
                    elevacion_orig,   # elevacion_target
                    horiz_orig,       # angulo_horizontal
                    verti_orig,       # angulo_vertical
                )
                datos_procesados.append(tupla)
 
            if not datos_procesados:
                print("Todos los prismas del origen ya existen en emonitoring.")
                return True  # No es error, simplemente no hay nada nuevo
 
            # ── 4. LOAD en lotes de 500 ──────────────────────
            TAMANO_LOTE = 500
            for i in range(0, len(datos_procesados), TAMANO_LOTE):
                lote = datos_procesados[i : i + TAMANO_LOTE]
                saved = UsuarioModel.mdlGuardarPrismasProcesados(lote)
                if not saved:
                    print(f"Error al guardar lote {i // TAMANO_LOTE + 1}")
                    return False
 
            print(f"Copia completada: {len(datos_procesados)} registros insertados.")
            return True
 
        except Exception as e:
            print("Error en ctrlRealizarCopia: " + str(e))
            return False
    