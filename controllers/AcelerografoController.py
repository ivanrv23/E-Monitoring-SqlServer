from models.AcelerografoModel import AcelerografoModel
from utils.common.metodosGenerales import MetodosGenerales

class AcelerografoController:    
    
    def ctrlObtenerFechasRango(proyectoid):
        tabla = f"acelerografo_detalle{proyectoid}"
        fecha = AcelerografoModel.mdlObtenerFechaMaximaAcelerografos(tabla)
        if fecha:
            if fecha[0]:
                fechamax = fecha[0]
                fechamin = MetodosGenerales.obtenerFechasRangoUnyear(fechamax, 30)
                return fechamin, fechamax
            else:
                fechamin, fechamax = MetodosGenerales.obtenerRangoFechas(365)
                return fechamin, fechamax
        else:
            fechamin, fechamax = MetodosGenerales.obtenerRangoFechas(365)
            return fechamin, fechamax
    
    def ctrlListarAcelerografosProyecto(idproyecto, aceleromarcados):
        acelerografos = []
        for componente, listaaceleros in aceleromarcados:
            nombrecomponente, idcomponente, idproyec = componente
            for acelero in listaaceleros:
                nombreacelero, idinstru, idacelero = acelero
                infoacelero = AcelerografoModel.mdlListarAcelerografoProyecto(idproyecto, idcomponente, idacelero)
                if infoacelero:
                    acelerografos.append(infoacelero)
        return acelerografos
    
    def ctrlObtenerMagnitud(idproyecto, aceleromarcados):
        data = []
        tabla = f"acelerografo_detalle{idproyecto}"
        for componente, listaacelero in aceleromarcados:
            nombrecomponente, idcomponente, idproy = componente
            acelerografos = [acelero[1] for acelero in listaacelero]
            respuesta = AcelerografoModel.mdlObtenerMagnitud(tabla, idcomponente, acelerografos)
            if respuesta:
                data.extend(respuesta)
        return data
    
    def ctrlObtenerMagnitudFechas(idproyecto, aceleromarcados, fechaini, fechafin):
        data = []
        tabla = f"acelerografo_detalle{idproyecto}"
        for componente, listaacelero in aceleromarcados:
            nombrecomponente, idcomponente, idproy = componente
            acelerografos = [acelero[1] for acelero in listaacelero]
            respuesta = AcelerografoModel.mdlObtenerMagnitudFechas(tabla, idcomponente, acelerografos, fechaini, fechafin)
            if respuesta:
                data.extend(respuesta)
        return data
    
    def ctrlActualizarLecturaAcelerografo(tabla, datos, idproyecto, username, nombres):
        respuesta = AcelerografoModel.mdlActualizarLecturaAcelerografo(tabla, datos, idproyecto, username, nombres)
        return respuesta
    
    def ctrlEliminarLecturaAcelerografo(tabla, idacelero, idproyecto, username, nombres):
        respuesta = AcelerografoModel.mdlEliminarLecturaAcelerografo(tabla, idacelero, idproyecto, username, nombres)
        return respuesta
    
    def ctrlEliminarLecturasBloqueAcelerografo(tabla, iddetalles, idproyecto, username, nombres):
        respuesta = AcelerografoModel.mdlEliminarLecturasBloqueAcelerografo(tabla, iddetalles, idproyecto, username, nombres)
        return respuesta
    
    def ctrlComprobarExisteNombreAcelerografo(proyectoid, nombre):
        respuesta, info = AcelerografoModel.mdlComprobarExisteNombreAcelerografo(proyectoid, nombre)
        return respuesta, info
    
    def ctrlRegistrarAcelerografo(proyecto_id, datos):
        respuesta, id_acelerografo = AcelerografoModel.mdlRegistrarAcelerografo(proyecto_id, datos)
        return respuesta, id_acelerografo
    
    def ctrlRegistrarFormatoAcelerografo(proyecto, data):
        respuesta = AcelerografoModel.mdlRegistrarFormatoAcelerografo(proyecto, data)
        return respuesta
    
    def ctrlObtenerAcelerografos(proyectoid):
        data = AcelerografoModel.mdlObtenerAcelerografos(proyectoid)
        return data
    
    def ctrlRegistrarDataAcelerografo(proyectoid, datos):
        unique_data = {(item[1], item[2]): item for item in datos}
        datalimpia = list(unique_data.values())
        respuesta = AcelerografoModel.mdlRegistrarDataAcelerografo(proyectoid, datalimpia)
        return respuesta
    
    def ctrlCambiarComponenteAcelerografos(idcomponente, nuevocomponente):
        respuesta = AcelerografoModel.mdlCambiarComponenteAcelerografos(idcomponente, nuevocomponente)
        return respuesta
    
    def ctrlEliminarAcelerografos(idcomponente):
        respuesta = AcelerografoModel.mdlEliminarAcelerografos(idcomponente)
        return respuesta
    
    def ctrlEliminarDataAcelerografos(idproyecto, datos):
        tabla = f"acelerografo_detalle{idproyecto}"
        sismos = [dato[4] for dato in datos]
        respuesta = AcelerografoModel.mdlEliminarDataAcelerografos(tabla, sismos)
        return respuesta
    
    def ctrlObtenerInfoAcelerografo(idinstrumento):
        respuesta = AcelerografoModel.mdlObtenerInfoAcelerografo(idinstrumento)
        return respuesta
    
    def ctrlActualizarAcelerografo(datos, data):
        respuesta = AcelerografoModel.mdlActualizarAcelerografo(datos, data)
        return respuesta
    
    def ctrlEliminarAcelerografo(idinstrumento):
        respuesta = AcelerografoModel.mdlEliminarAcelerografo(idinstrumento)
        return respuesta
    
    def ctrlEliminarAcelerografoData(idproyecto, dato):
        tabla = f"acelerografo_detalle{idproyecto}"
        respuesta = AcelerografoModel.mdlEliminarAcelerografoData(tabla, dato[4])
        return respuesta
    
    def ctrlObtenerUmbralesAcelerografoComponente(idproyecto, idcomponente, tipo):
        respuesta = AcelerografoModel.mdlObtenerUmbralesAcelerografoComponente(idproyecto, idcomponente, tipo)
        return respuesta
    
    def ctrlTraerDataAcelerografo(idacelero):
        respuesta = AcelerografoModel.mdlTraerDataAcelerografo(idacelero)
        return respuesta
    
    def ctrlCambiarAcelerografoComponente(idinstrumento, idcomponente):
        respuesta = AcelerografoModel.mdlCambiarAcelerografoComponente(idinstrumento, idcomponente)
        return respuesta