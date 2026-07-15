from models.PluviometroModel import PluviometroModel

class PluviometroController:
    
    def ctrlListarPluviometrosCombo(proyectoid):
        respuesta = PluviometroModel.mdlListarPluviometrosCombo(proyectoid)
        return respuesta
    
    def ctrlListarPluviometrosProyecto(idproyecto, pluviometrosmarcados):
        pluviometros = []
        for componente, listapluviometros in pluviometrosmarcados:
            nombrecomponente, idcomponente, idproyec = componente
            for pluviome in listapluviometros:
                nombrepluvio, idinstru, idpluvio = pluviome
                infopluvio = PluviometroModel.mdlListarPluviometroProyecto(idproyecto, idcomponente, idpluvio)
                if infopluvio:
                    pluviometros.append(infopluvio)
        return pluviometros
    
    def ctrlGuardarNuevoPluviometro(proyectoid, datos):
        respuesta = PluviometroModel.mdlGuardarNuevoPluviometro(proyectoid, datos)
        return respuesta
    
    def ctrlComprobarExisteNombrePluviometro(proyectoid, nombre):
        respuesta, info = PluviometroModel.mdlComprobarExisteNombrePluviometro(proyectoid, nombre)
        return respuesta, info
    
    def ctrlRegistrarFormatoPluviometro(proyectoid, datos):
        respuesta = PluviometroModel.mdlRegistrarFormatoPluviometro(proyectoid, datos)
        return respuesta
    
    # registrar pluviometros tabla
    def ctrlGuardarPluviometrosTabla(idproyecto, data):
        unique_data = {(item[1], item[2]): item for item in data}
        datalimpia = list(unique_data.values())
        respuesta = PluviometroModel.mdlGuardarPluviometrosTabla(idproyecto, datalimpia)
        return respuesta
    
    # obtener data pluviometros mostrar tabla
    def ctrlObtenerDataPluviometrosDetalle(idproyecto, marcados):
        datainclinometros = []
        for idpluvio, nombre, tipo in marcados:
            datos = PluviometroModel.mdlObtenerDataPluviometrosDetalle(idproyecto, idpluvio)
            if datos is not None:
                datainclinometros.extend(datos)
        return datainclinometros
    
    def ctrlActualizarPluviometro(datos, data):
        respuesta = PluviometroModel.mdlActualizarPluviometro(datos, data)
        return respuesta
    
    def ctrlActualizarLecturaPluviometro(tabla, datos, idproyecto, username, nombres):
        respuesta = PluviometroModel.mdlActualizarLecturaPluviometro(tabla, datos, idproyecto, username, nombres)
        return respuesta
    
    def ctrlEliminarLecturaPluviometro(tabla, idpluviometro, idproyecto, username, nombres):
        respuesta = PluviometroModel.mdlEliminarLecturaPluviometro(tabla, idpluviometro, idproyecto, username, nombres)
        return respuesta
    
    def ctrlEliminarLecturasBloquePluviometro(tabla, iddetalles,idproyecto, username, nombres):
        respuesta = PluviometroModel.mdlEliminarLecturasBloquePluviometro(tabla, iddetalles, idproyecto, username, nombres)
        return respuesta
    
    def ctrlCambiarComponentePluviometros(idcomponente, nuevocomponente):
        respuesta = PluviometroModel.mdlCambiarComponentePluviometros(idcomponente, nuevocomponente)
        return respuesta
    
    def ctrlEliminarPluviometros(idcomponente):
        respuesta = PluviometroModel.mdlEliminarPluviometros(idcomponente)
        return respuesta
    
    def ctrlEliminarDataPiezometrosManuales(idproyecto, datos):
        tabla = f"pluviometro_detalle{idproyecto}"
        pluvio = [dato[4] for dato in datos]
        respuesta = PluviometroModel.mdlEliminarDataPluviometros(tabla, pluvio)
        return respuesta
    
    def ctrlObtenerInfoPluviometro(idinstrumento):
        respuesta = PluviometroModel.mdlObtenerInfoPluviometro(idinstrumento)
        return respuesta
    
    def ctrlEliminarPluviometro(idinstrumento):
        respuesta = PluviometroModel.mdlEliminarPluviometro(idinstrumento)
        return respuesta
    
    def ctrlEliminarPluviometroData(idproyecto, dato):
        tabla = f"pluviometro_detalle{idproyecto}"
        respuesta = PluviometroModel.mdlEliminarPluviometroData(tabla, dato[4])
        return respuesta
    
    def ctrlObtenerPluviometros(idproyecto, pluviometromarcados, fechaini, fechafin):
        precipitaciones = []
        tabla = f"pluviometro_detalle{idproyecto}"
        for componente, listalluvia in pluviometromarcados:
            nombrecomponente, idcomponente, idproy = componente
            for lluvia in listalluvia:
                nombrepluvio, idinstru, idpluvio = lluvia
                respuesta = PluviometroModel.mdlObtenerPluviometros(tabla, idcomponente, idinstru, fechaini, fechafin)
                if respuesta:
                    precipitaciones.extend(respuesta)
        return precipitaciones
    
    def ctrlTraerDataPluviometro(idpiezometro):
        respuesta = PluviometroModel.mdlTraerDataPluviometro(idpiezometro)
        return respuesta
    
    def ctrlCambiarPluviometroComponente(idinstrumento, idcomponente):
        respuesta = PluviometroModel.mdlCambiarPluviometroComponente(idinstrumento, idcomponente)
        return respuesta
    