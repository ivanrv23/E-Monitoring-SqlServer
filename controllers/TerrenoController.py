from models.TerrenoModel import TerrenoModel

class TerrenoController:
    
    def ctrlGuardarNuevaCotaTerreno(proyectoid, componente, nombre, comentario):
        respuesta = TerrenoModel.mdlGuardarNuevaCotaTerreno(proyectoid, componente, nombre, comentario)
        return respuesta
    
    # traer lista de cotas terreno por proyecto
    def ctrlListaCotasTerrenoProyecto(proyectoid):
        respuesta = TerrenoModel.mdlListaCotasTerrenoProyecto(proyectoid)
        return respuesta
    
    # registrar data cota terreno
    def ctrlGuardarDataCotaTerreno(proyectoid, data):
        unique_data = {(item[1], item[2]): item for item in data}
        datalimpia = list(unique_data.values())
        respuesta = TerrenoModel.mdlGuardarDataCotaTerreno(proyectoid, datalimpia)
        return respuesta
    
    def ctrlComprobarExisteNombreCotaTerreno(proyectoid, nombre):
        respuesta, info = TerrenoModel.mdlComprobarExisteNombreCotaTerreno(proyectoid, nombre)
        return respuesta, info
    
    def ctrlRegistrarFormatoCotaTerreno(proyectoid, componente, nombre, comentario):
        respuesta = TerrenoModel.mdlRegistrarFormatoCotaTerreno(proyectoid, componente, nombre, comentario)
        return respuesta
    
    # traer lista de cotas terreno por proyecto
    def ctrlListaCotasTerrenoProyecto(proyectoid):
        respuesta = TerrenoModel.mdlListaCotasTerrenoProyecto(proyectoid)
        return respuesta
    
    # traer data de suelos para la tabla
    def ctrlObtenerDataCotasTerrenoDetalle(marcados):
        datasuelos = []
        for idsuelo, nombre, tipo in marcados:
            datos = TerrenoModel.mdlObtenerDataCotasTerrenoDetalle(idsuelo)
            if datos is not None:
                datasuelos.extend(datos)
        return datasuelos
    
    def ctrlObtenerDataCotaDetalle(idpiezo, tipopiezo):
        datos = TerrenoModel.mdlObtenerDataCotaDetalle(idpiezo, tipopiezo)
        return datos
    
    def ctrlTraerInfoCotaTerreno(idsuelo):
        respuesta = TerrenoModel.mdlTraerInfoCotaTerreno(idsuelo)
        return respuesta

    def ctrlActualizarCotaTerreno(idcota, nombre, comentario):
        respuesta = TerrenoModel.mdlActualizarCotaTerreno(idcota, nombre, comentario)
        return respuesta
    
    # registrar data cota terreno
    def ctrlGuardarDataCota(idpiezo, tipo, fecha, hora, nivel):
        # comprobar si existe fecha igual
        existe = TerrenoModel.mdlComprobarExisteCotaTerreno(idpiezo, tipo, fecha, hora)
        if existe is False:
            respuesta = TerrenoModel.mdlGuardarDataCota(idpiezo, tipo, fecha, hora, nivel)
        else:
            respuesta = False
        return respuesta
    
    def ctrlGuardarLecturasCotaPiezometrica(data):
        unique_data = {item[2]: item for item in data}
        datalimpia = list(unique_data.values())
        respuesta = TerrenoModel.mdlGuardarLecturasCotaPiezometrica(datalimpia)
        return respuesta
    
    def ctrlObtenerDataCotasPiezometricas(proyectoid, marcados):
        # traer suelos que tengan data
        datos = []
        cotadatos = TerrenoModel.mdlObtenerDataCotasPiezometricas(proyectoid)
        if cotadatos is not None:
            for idpiezo, tipopiezo, nomb in marcados:
                for equipo in cotadatos:
                    if str(equipo[5]) == str(idpiezo) and equipo[6] == tipopiezo:
                        datos.append(equipo)
        return datos
    
    # obtener data cota gráfica
    def ctrlObtenerDataTerrenoDetalle(sueloid):
        datos = TerrenoModel.mdlObtenerDataTerrenoDetalle(sueloid)
        return datos
    
    def ctrlActualizarLecturaCotapiezometrica(idcota, fecha, nivel):
        respuesta = TerrenoModel.mdlActualizarLecturaCotapiezometrica(idcota, fecha, nivel)
        return respuesta
    
    def ctrlEliminarLecturaCotapiezometrica(idcota, idpiezo, tipopiezo):
        # validar si hay más de dos cotas
        respue = TerrenoModel.mdlComprobarUltimaCotapiezometrica(idpiezo, tipopiezo)
        if respue:
            respuesta = TerrenoModel.mdlEliminarLecturaCotapiezometrica(idcota)
        else:
            respuesta = False
        return respuesta
    
    def ctrlActualizarLecturaCotaterreno(tabla, datos, idproyecto, username, nombres):
        respuesta = TerrenoModel.mdlActualizarLecturaCotaterreno(tabla, datos, idproyecto, username, nombres)
        return respuesta
    
    def ctrlEliminarLecturaCotaterreno(tabla, iddetalle, idproyecto, username, nombres):
        respuesta = TerrenoModel.mdlEliminarLecturaCotaterreno(tabla, iddetalle, idproyecto, username, nombres)
        return respuesta
    
    def ctrlEliminarLecturasBloqueCotaterreno(tabla, iddetalles, idproyecto, username, nombres):
        respuesta = TerrenoModel.mdlEliminarLecturasBloqueCotaterreno(tabla, iddetalles, idproyecto, username, nombres)
        return respuesta
    
    def ctrlCambiarComponenteCotasTerreno(idcomponente, nuevocomponente):
        respuesta = TerrenoModel.mdlCambiarComponenteCotasTerreno(idcomponente, nuevocomponente)
        return respuesta
    
    def ctrlEliminarCotasTerrenos(idcomponente):
        respuesta = TerrenoModel.mdlEliminarCotasTerrenos(idcomponente)
        return respuesta
    
    def ctrlEliminarDataCotasTerrenos(idproyecto, datos):
        tabla = f"cotaterreno_detalle{idproyecto}"
        pluvio = [dato[4] for dato in datos]
        respuesta = TerrenoModel.mdlEliminarDataCotasTerrenos(tabla, pluvio)
        return respuesta
    
    def ctrlObtenerInfoCotaTerreno(idinstrumento):
        respuesta = TerrenoModel.mdlObtenerInfoPluviometro(idinstrumento)
        return respuesta
    
    def ctrlEliminarCotaTerreno(idinstrumento):
        respuesta = TerrenoModel.mdlEliminarCotaTerreno(idinstrumento)
        return respuesta
    
    def ctrlEliminarCotaTerrenoData(idproyecto, dato):
        tabla = f"cotaterreno_detalle{idproyecto}"
        respuesta = TerrenoModel.mdlEliminarCotaTerrenoData(tabla, dato[4])
        return respuesta
    
    def ctrlObtenerCotasTerreno(idproyecto, terrenomarcados, fechaini, fechafin):
        terrenosdata = []
        tabla = f"cotaterreno_detalle{idproyecto}"
        for componente, listaterrenos in terrenomarcados:
            nombrecomponente, idcomponente, idproy = componente
            for terreno in listaterrenos:
                nombrecota, idinstru, idcota = terreno
                respuesta = TerrenoModel.mdlObtenerCotasTerreno(tabla, idcomponente, idinstru, fechaini, fechafin)
                if respuesta:
                    terrenosdata.extend(respuesta)
        return terrenosdata
    
    def ctrlTraerDataCotaTerreno(idterreno):
        respuesta = TerrenoModel.mdlTraerDataCotaTerreno(idterreno)
        return respuesta
    
    def ctrlCambiarCotaterrenoComponente(idinstrumento, idcomponente):
        respuesta = TerrenoModel.mdlCambiarCotaterrenoComponente(idinstrumento, idcomponente)
        return respuesta
    