from models.PrismasVirtualesModel import PrismasVirtualesModel

class PrismasVirtualesController:
    
    def ctrlPrismasVirtualesProyecto(idproyecto, equiposmarcados):
        equipos = []
        for componente, listaequipos in equiposmarcados:
            nombrecomponente, idcomponente, idproyec = componente
            for equipo in listaequipos:
                nombreequipo, idinstru, idequipo = equipo
                infoequipo = PrismasVirtualesModel.mdlListarPrismasVirtualesProyecto(idproyecto, idcomponente, idequipo)
                if infoequipo:
                    equipos.append(infoequipo)
        return equipos
    
    def ctrlPrismasVirtuales(ids):
        respuesta = PrismasVirtualesModel.mdlPrismasVirtuales(ids)
        return respuesta