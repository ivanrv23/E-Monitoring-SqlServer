from models.EstratoModel import EstratoModel

class EstratoController:
    
    def ctrlGuardarEstratosInstrumentacion(proyectoid,componente_id,data):
        for item in data:
            estrato_id = item['id']
            if estrato_id is None or estrato_id == 0:
                success = EstratoModel.mdlGuardarEstratos(proyectoid,componente_id, [item])
            else:
                success = EstratoModel.mdlActualizarEstratos(estrato_id, item['nombre'], item['color'], item['rango_minimo'],item['rango_maximo'])
            if not success:
                return False
        return True


    def ctrlEliminarEstratos(estrato_id):
        estrato = EstratoModel.mdlEliminarEstrato(estrato_id)
        return estrato
    
    def ctrObtenerEstratosInstrumentacion(proyectoid,componente_id):
        estrato = EstratoModel.mdlObtenerEstratosInstrumentacion(proyectoid,componente_id)
        return estrato
    
    def ctrObtenerEstratosProyecto(proyecto):
        umbral = EstratoModel.mdlObtenerEstratosProyecto(proyecto)
        return umbral
    
    