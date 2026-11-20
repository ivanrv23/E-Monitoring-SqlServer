from models.VoladuraModel import VoladuraModel

class VoladuraController:

    def ctrlGuardarNuevaVoladura(proyectoid, datos):
        return VoladuraModel.mdlGuardarNuevaVoladura(proyectoid, datos)

    def ctrlListaVoladurasProyecto(proyectoid):
        return VoladuraModel.mdlListaVoladurasProyecto(proyectoid)

    def ctrlObtenerDataVoladuras(idproyecto, ids):
        return VoladuraModel.mdlObtenerDataVoladuras(idproyecto, ids)

    # registrar voladuras tabla
    def ctrlGuardarVoladuraTabla(idproyecto, data):
        unique_data = {(item[0], item[1], item[2]): item for item in data}
        datalimpia = list(unique_data.values())
        return VoladuraModel.mdlGuardarVoladuraTabla(idproyecto, datalimpia)

    def ctrlActualizarLecturaVoladura(idproyecto, datos, username=None, nombres=None):
        return VoladuraModel.mdlActualizarLecturaVoladura(idproyecto, datos)

    def ctrlCambiarEstadoLecturaVoladura(idproyecto, iddetalle):
        return VoladuraModel.mdlCambiarEstadoLecturaVoladura(idproyecto, iddetalle)

    def ctrlCambiarEstadoLecturaVoladuraBloque(idproyecto, ids):
        return VoladuraModel.mdlCambiarEstadoLecturaVoladuraBloque(idproyecto, ids)

    def ctrlEliminarLecturaVoladura(idproyecto, iddetalle, username=None, nombres=None):
        return VoladuraModel.mdlEliminarLecturaVoladura(idproyecto, iddetalle)

    def ctrlEliminarLecturasBloqueVoladura(idproyecto, ids, username=None, nombres=None):
        return VoladuraModel.mdlEliminarLecturasBloqueVoladura(idproyecto, ids)

    def ctrlListarComponentesProyecto(proyectoid):
        return VoladuraModel.mdlListarComponentesProyecto(proyectoid)

    def ctrlObtenerInfoVoladura(idinstrumento):
        return VoladuraModel.mdlObtenerInfoVoladura(idinstrumento)

    def ctrlActualizarVoladura(datos, data):
        return VoladuraModel.mdlActualizarVoladura(datos, data)

    def ctrlComprobarExisteNombreVoladura(proyecto, nombre):
        return VoladuraModel.mdlComprobarExisteNombreVoladura(proyecto, nombre)

    def ctrlEliminarVoladura(idinstrumento):
        return VoladuraModel.mdlEliminarVoladura(idinstrumento)

    def ctrlEliminarVoladuraData(idproyecto, idvoladura):
        return VoladuraModel.mdlEliminarVoladuraData(idproyecto, idvoladura)

    def ctrlRegistrarFormatoVoladura(proyectoid, nombre, codigo, comentario, idcomponente):
        return VoladuraModel.mdlRegistrarFormatoVoladura(proyectoid, nombre, codigo, comentario, idcomponente)

    def ctrlObtenerEstiloVoladura(idinstrumento):
        return VoladuraModel.mdlObtenerEstiloVoladura(idinstrumento)

    def ctrlGuardarEstiloVoladura(idinstrumento, grosor, alto, color):
        return VoladuraModel.mdlGuardarEstiloVoladura(idinstrumento, grosor, alto, color)

    def ctrlObtenerEstilosVoladuras(proyecto_id):
        return VoladuraModel.mdlObtenerEstilosVoladuras(proyecto_id)