import ast
from models.TDRModel import TDRModel

class TDRController:
    
    def ctrlObtenerLecturasTDR(idproyecto, sondajetdrmarcados, unidadmedida):
        data = []
        fallas = []
        tabla = f"sondajetdr_detalle{idproyecto}"
        for componente, listatdr in sondajetdrmarcados:
            nombrecomponente, idcomponente, idproy = componente
            for nombretdr, idinstru, fechas in listatdr:
                fechitas = ast.literal_eval(fechas)
                respuesta = TDRModel.mdlObtenerLecturasTDR(tabla, idcomponente, idinstru, unidadmedida, fechitas)
                datafallas = TDRModel.mdlObtenerFallasTDR(idcomponente, idinstru)
                if respuesta:
                    data.extend(respuesta)
                if datafallas:
                    fallas.extend(datafallas)
        return data, fallas

    def ctrlObtenerFallasTDR(idproyecto, sondajetdrmarcados): # usar para el visor
        for componente, listatdr in sondajetdrmarcados:
            nombrecomponente, idcomponente, idproy = componente
            for sondaje, fechas in listatdr.items():
                idsondaje = sondaje[2]
                respuesta = TDRModel.mdlObtenerFallasTDR(idcomponente, idsondaje)
        return respuesta
    
    def ctrlActualizarLecturaSondajetdr(tabla, datos, idproyecto, username, nombres):
        respuesta = TDRModel.mdlActualizarLecturaSondajetdr(tabla, datos, idproyecto, username, nombres)
        return respuesta
    
    def ctrlComprobarExisteNombreTDR(proyectoid, nombre):
        respuesta, info = TDRModel.mdlComprobarExisteNombreTDR(proyectoid, nombre)
        return respuesta, info
    
    def ctrlGuardarEquipoTDR(proyecto, data):
        respuesta = TDRModel.mdlGuardarEquipoTDR(proyecto, data)
        return respuesta
    
    def ctrlRegistrarFormatoEquipoTDR(proyecto, data):
        respuesta = TDRModel.mdlRegistrarFormatoEquipoTDR(proyecto, data)
        return respuesta
    
    def ctrlComprobarExisteFechaTDR(tabla, idsondaje, fechahora):
        respuesta = TDRModel.mdlComprobarExisteFechasTDR(tabla, idsondaje, fechahora)
        return respuesta
    
    def ctrlListarSondajestdrProyecto(idproyecto, tdrmarcados):
        sondajestdr = []
        for componente, listasondajes in tdrmarcados:
            nombrecomponente, idcomponente, idproyec = componente
            for sondatdr in listasondajes:
                nombretdr, idinstru, idtdr = sondatdr
                infotdr = TDRModel.mdlListarSondajetdrProyecto(idproyecto, idcomponente, idtdr)
                if infotdr:
                    sondajestdr.append(infotdr)
        return sondajestdr
    
    def ctrlObtenerListaSondajes(proyecto):
        respuesta = TDRModel.mdlObtenerListaSondajes(proyecto)
        return respuesta
    
    def ctrlGuardarDataSondajesTDR(proyectoid, data):
        respuesta = TDRModel.mdlGuardarDataSondajesTDR(proyectoid, data)
        return respuesta
    
    def ctrlMostrarLecturasSondajeTDR(idsondaje):
        respuesta = TDRModel.mdlMostrarLecturasSondajeTDR(idsondaje)
        return respuesta
    
    def ctrlRegistarMedidasSondaje(data):
        for item in data:
            idsondaje, nombre, medida, color, posicion = item
            existente = TDRModel.mdlValidarExisteFallaTDR(idsondaje, posicion)
            if existente: # actualizar
                respuesta = TDRModel.mdlActualizarMedidasSondaje(item)
            else:
                respuesta = TDRModel.mdlRegistarMedidasSondaje(item)
            if not respuesta:
                return False
        return True
    
    def ctrlEliminarDetalleSondajes(id_punto):        
        delet = TDRModel.mdlEliminarPuntoSondajes(id_punto)
        return delet
    
    def ctrlCambiarComponenteSondajesTDR(idcomponente, nuevocomponente):
        respuesta = TDRModel.mdlCambiarComponenteSondajesTDR(idcomponente, nuevocomponente)
        return respuesta
    
    def ctrlEliminarSondajesTDR(idcomponente):
        respuesta = TDRModel.mdlEliminarSondajesTDR(idcomponente)
        return respuesta
    
    def ctrlEliminarDataSondajesTDR(idproyecto, datos):
        tabla = f"sondajetdr_detalle{idproyecto}"
        sondajes = [dato[4] for dato in datos]
        respuesta = TDRModel.mdlEliminarDataSondajesTDR(tabla, sondajes)
        return respuesta
    
    def ctrlObtenerInfoSondajeTDR(idinstrumento):
        respuesta = TDRModel.mdlObtenerInfoSondajeTDR(idinstrumento)
        return respuesta
    
    def ctrlActualizarSondajeTDR(datos, data):
        respuesta = TDRModel.mdlActualizarSondajeTDR(datos, data)
        return respuesta
    
    def ctrlEliminarSondajetdr(idinstrumento):
        respuesta = TDRModel.mdlEliminarSondajetdr(idinstrumento)
        return respuesta
    
    def ctrlEliminarSondajetdrData(idproyecto, dato):
        tabla = f"sondajetdr_detalle{idproyecto}"
        respuesta = TDRModel.mdlEliminarSondajetdrData(tabla, dato[4])
        return respuesta
    
    def ctrlListarFechasSondajetdr(idcomponente, idinstrumento, idproyecto):
        tabla = f"sondajetdr_detalle{idproyecto}"
        respuesta = TDRModel.mdlListarFechasSondajetdr(tabla, idcomponente, idinstrumento)
        return respuesta
    
    def ctrlCambiarBaseSondajetdr(fecha, idsondaje):
        respueta = TDRModel.mdlCambiarBaseSondajetdr(fecha, idsondaje)
        return respueta
    
    def ctrlTraerDataSondajetdr(idsondaje):
        respuesta = TDRModel.mdlTraerDataSondajetdr(idsondaje)
        return respuesta
    
    def ctrlCambiarSondajetdrComponente(idinstrumento, idcomponente):
        respuesta = TDRModel.mdlCambiarSondajetdrComponente(idinstrumento, idcomponente)
        return respuesta
    