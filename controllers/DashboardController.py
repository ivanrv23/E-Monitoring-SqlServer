from models.DashboardModel import DashboardModel
class DashboardController:
    
    def ctrlObtenerInstrumentacionProyecto(proyecto_id, id_componente):
        respuesta = DashboardModel.mdlObtenerInstrumentacionProyecto(proyecto_id, id_componente)
        return respuesta
    
    def ctrlObtenerInstrumentacionOIProyecto(proyecto_id,id_componete):
        respuesta = DashboardModel.mdlObtenerInstrumentacionOIProyecto(proyecto_id,id_componete)
        return respuesta
    
    def ctrlObtenerLecturasPrismas(proyecto_id,tabla,id_componete,tipo):
        tabla_prismas=f'{tabla}{proyecto_id}'
        respuesta = DashboardModel.mdlObtenerLecturasPrismas(tabla_prismas,id_componete,tipo)
        return respuesta
    
    def ctrlObtenerComponentes(proyecto_id):
        respuesta = DashboardModel.mdlObtenerObtenerComponentes(proyecto_id)
        return respuesta
    
    def ctrlObtenerResumenPrismas(proyectoid, idcomponente):
        datosprisma = []
        table_manual = "prismas" + str(proyectoid)
        datosm = DashboardModel.mdlResumenPrismas(table_manual, idcomponente)
        if datosm:
            datosprisma.extend(datosm)
        return datosprisma