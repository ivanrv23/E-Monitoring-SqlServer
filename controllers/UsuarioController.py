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
    
    def ctrlObtenerConexiones():
        result = UsuarioModel.mdlObtenerConexiones()
        return result
    
    def ctrlGuardarNuevaConexion(datos):
        respuesta = UsuarioModel.mdlGuardarNuevaConexion(datos)
        return respuesta
    
    def ctrlActualizarConexion(datos):
        respuesta = UsuarioModel.mdlActualizarConexion(datos)
        return respuesta
    
    def ctrlEliminarConexion(idconexion):
        respuesta = UsuarioModel.mdlEliminarConexion(idconexion)
        return respuesta
    