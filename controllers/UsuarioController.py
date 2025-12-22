from models.UsuarioModel import UsuarioModel

class UsuarioController:
    
    def ctrlObtenerCodigoEmpresa():
        respuesta = UsuarioModel.mdlObtenerCodigoEmpresa()
        return respuesta
    
    def ctrlObtenerListaUsuarios(idventa):
        respuesta, data = UsuarioModel.mdlObtenerListaUsuarios(idventa)
        return respuesta, data
    
    def ctrlEliminarUsuario(idusuario):
        respuesta = UsuarioModel.mdlEliminarUsuario(idusuario)
        return respuesta
    
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
    