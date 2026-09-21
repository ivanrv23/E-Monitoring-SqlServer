from models.InstrumentacionModel import InstrumentacionModel
class InstrumentacionController:
    def ctrlObtenerInstrumentacionComponente(id_componente,tipo_equipo):
        respuesta = InstrumentacionModel.mdlObtenerInstrumentacionComponente(id_componente,tipo_equipo)
        return respuesta

    def ctrlObtenerIdequipoInstrumentacion(idintrumentacion):
        respuesta = InstrumentacionModel.mdlObtenerIdequipoInstrumentacion(idintrumentacion)
        return respuesta