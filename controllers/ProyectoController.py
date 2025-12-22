from models.ProyectoModel import ProyectoModel

class ProyectoController:
    
    def ctrlRegistarProyecto(nombre, fecha, comentario):
        respuesta = ProyectoModel.mdlRegistarProyecto(nombre, fecha, comentario)
        return respuesta
    
    def ctrlRegistarComponente(id_proyecto, nombre):
        respuesta = ProyectoModel.mdlRegistarComponente(id_proyecto, nombre)
        return respuesta
    
    def ctrlObtenerInfoProyecto(idproyecto):
        respuesta = ProyectoModel.mdlObtenerInfoProyecto(idproyecto)
        return respuesta
    
    def ctrlActualizarProyecto(nombre, fecha, comentario, idproyecto):
        respuesta = ProyectoModel.mdlActualizarProyecto(nombre, fecha, comentario, idproyecto)
        return respuesta
    
    def ctrlObtenerComponentesProyecto(idproyecto):
        respuesta = ProyectoModel.mdlObtenerComponentesProyecto(idproyecto)
        return respuesta
    
    def ctrlActualizarComponente(nombre, idcomponente):
        respuesta = ProyectoModel.mdlActualizarComponente(nombre, idcomponente)
        return respuesta
    
    def ctrlEliminarComponente(idproyecto, idcomponente):
        respuesta = ProyectoModel.mdlEliminarComponente(idproyecto, idcomponente)
        return respuesta
    
    def ctrlEliminarProyecto(idproyecto):
        respuesta = ProyectoModel.mdlEliminarProyecto(idproyecto)
        return respuesta
    
    def ctrlObtenerHistorialCambios():
        result = ProyectoModel.mdlObtenerHistorialCambios()
        return result
    
    def ctrlObtenerAjustesCambios():
        result = ProyectoModel.mdlObtenerAjustesCambios()
        return result
    