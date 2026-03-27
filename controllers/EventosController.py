from models.EventosModel import EventosModel

class EventosController:
    
    @staticmethod
    def ctrlCrearEvento(idproyecto, fecha, descripcion, color, alcance, tipo_inst, id_inst):
        return EventosModel.mdlCrearEvento(idproyecto, fecha, descripcion, color, alcance, tipo_inst, id_inst)
    
    @staticmethod
    def ctrlObtenerEventos(idproyecto, tipo_inst, ids_instrumentos, fecha_inicio, fecha_fin):
        """ids_instrumentos ahora es una LISTA"""
        return EventosModel.mdlObtenerEventos(idproyecto, tipo_inst, ids_instrumentos, fecha_inicio, fecha_fin)

    @staticmethod
    def ctrlEliminarEvento(id_evento):
        return EventosModel.mdlEliminarEvento(id_evento)