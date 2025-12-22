from models.EquipoModel import EquipoModel

class EquipoController:
    
    def ctrlListarAdicionalesProyecto(idproyecto, equiposmarcados):
        equipos = []
        for componente, listaequipos in equiposmarcados:
            nombrecomponente, idcomponente, idproyec = componente
            for equipo in listaequipos:
                nombreequipo, idinstru, idequipo = equipo
                infoequipo = EquipoModel.mdlListarAdicionalProyecto(idproyecto, idcomponente, idequipo)
                if infoequipo:
                    equipos.append(infoequipo)
        return equipos
    
    def ctrlGuardarEquipoGeneral(data):
        respuesta, idequipo = EquipoModel.mdlGuardarEquipoGeneral(data)
        return respuesta, idequipo
    
    def ctrlCambiarComponenteAdicionales(idcomponente, nuevocomponente):
        respuesta = EquipoModel.mdlCambiarComponenteAdicionales(idcomponente, nuevocomponente)
        return respuesta
    
    def ctrlEliminarAdicionales(idcomponente):
        respuesta = EquipoModel.mdlEliminarAdicionales(idcomponente)
        return respuesta
    
    def ctrlEliminarDataAdiconales(idproyecto, datos):
        equipos = [dato[4] for dato in datos]
        respuesta = EquipoModel.mdlEliminarDataAdicionales(equipos)
        return respuesta
    
    def ctrlObtenerInfoEquipoAdicional(idinstrumento):
        respuesta = EquipoModel.mdlObtenerInfoEquipoAdicional(idinstrumento)
        return respuesta
    
    def ctrlActualizarEquipoAdicional(datos, data):
        respuesta = EquipoModel.mdlActualizarEquipoAdicional(datos, data)
        return respuesta
    
    def ctrlEliminarEquipoAdicional(idinstrumento):
        respuesta = EquipoModel.mdlEliminarEquipoAdicional(idinstrumento)
        return respuesta
    
    def ctrlEliminarEquipoAdicionalData(dato):
        respuesta = EquipoModel.mdlEliminarEquipoAdicionalData(dato[4])
        return respuesta
    
    def ctrlTraerDataEquipoGeneral(idequipo):
        respuesta = EquipoModel.mdlTraerDataEquipoGeneral(idequipo)
        return respuesta
    
    def ctrlCambiarEquipoComponente(idinstrumento, idcomponente):
        respuesta = EquipoModel.mdlCambiarEquipoComponente(idinstrumento, idcomponente)
        return respuesta
    