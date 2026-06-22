from collections import defaultdict
from datetime import datetime
from models.CeldaModel import CeldaModel
from utils.common.metodosGenerales import MetodosGenerales

class CeldaController:    
    
    def ctrlObtenerFechasRango(proyectoid):
        tabla = f"celda_detalle{proyectoid}"
        fecha = CeldaModel.mdlObtenerFechaMaximaCeldas(tabla)
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
    
    def ctrlRegistrarCelda(idcomponente, data):
        fecha_actual = f"{datetime.now().strftime('%Y-%m-%d')} 00:00:00"
        idcelda = CeldaModel.mdlRegistrarCelda(data, fecha_actual)
        if idcelda:
            respuesta = CeldaModel.mdlRegistrarInstrumentacionCelda((idcomponente, "CELDA", data['nombre_celda'], idcelda, "celdas"))
        else:
            respuesta = False
        return respuesta
    
    def ctrlComprobarExisteNombreCelda(proyectoid, nombre):
        respuesta, info = CeldaModel.mdlComprobarExisteNombreCelda(proyectoid, nombre)
        return respuesta, info
    
    def ctrlRegistrarCeldaFormato(idcomponente, datos):
        fecha_actual = f"{datetime.now().strftime('%Y-%m-%d')} 00:00:00"
        idcelda = CeldaModel.mdlRegistrarCelda(datos, fecha_actual)
        if idcelda:
            respues = CeldaModel.mdlRegistrarInstrumentacionCelda((idcomponente, "CELDA", datos['nombre_celda'], idcelda, "celdas"))
            if respues:
                respuesta = idcelda
            else:
                respuesta = None
        else:
            respuesta = None
        return respuesta
    
    def ctrlListarCeldasProyecto(idproyecto, celdasmarcadas):
        celdas = []
        for componente, listaceldas in celdasmarcadas:
            nombrecomponente, idcomponente, idproyec = componente
            for celda in listaceldas:
                nombrecelda, idinstru, idcelda = celda
                infocelda = CeldaModel.mdlListarCeldaProyecto(idproyecto, idcomponente, idcelda)
                if infocelda:
                    celdas.append(infocelda)
        return celdas
    
    def ctrlCalcularVelocidadDias(dias, idproyecto, celdasmarcadas, fechaini, fechafin, filtrado):
        data = []
        tabla = f"celda_detalle{idproyecto}"
        agrupados = defaultdict(list)
        if filtrado == 0: # sin fechas
            for componente, listaceldas in celdasmarcadas:
                clave = componente[1]
                agrupados[clave].append(listaceldas)
            for idcomponente, celdama in agrupados.items():
                listaidceldas = []
                for celd in celdama:
                    listaidceldas.append(celd[1])
                if listaidceldas:
                    respuesta = CeldaModel.mdlCalcularVelocidadDias(dias, tabla, idcomponente, listaidceldas)
                    if respuesta:
                        data.extend(respuesta)
        else:
            for componente, listaceldas in celdasmarcadas:
                clave = componente[1]
                agrupados[clave].append(listaceldas)
            for idcomponente, celdama in agrupados.items():
                listaidceldas = []
                for celd in celdama:
                    listaidceldas.append(celd[1])
                if listaidceldas:
                    respuesta = CeldaModel.mdlCalcularVelocidadFechasDias(dias, tabla, idcomponente, listaidceldas, fechaini, fechafin)
                    if respuesta:
                        data.extend(respuesta)
        return data
    
    def ctrlCalcularVelocidadMes(idproyecto, celdasmarcadas, fechaini, fechafin, filtrado):
        data = []
        tabla = f"celda_detalle{idproyecto}"
        agrupados = defaultdict(list)
        if filtrado == 0: # sin fechas
            for componente, listaceldas in celdasmarcadas:
                clave = componente[1]
                agrupados[clave].append(listaceldas)
            for idcomponente, celdama in agrupados.items():
                listaidceldas = []
                for celd in celdama:
                    listaidceldas.append(celd[1])
                if listaidceldas:
                    respuesta = CeldaModel.mdlCalcularVelocidadMes(tabla, idcomponente, listaidceldas)
                    if respuesta:
                        data.extend(respuesta)
        else:
            for componente, listaceldas in celdasmarcadas:
                clave = componente[1]
                agrupados[clave].append(listaceldas)
            for idcomponente, celdama in agrupados.items():
                listaidceldas = []
                for celd in celdama:
                    listaidceldas.append(celd[1])
                if listaidceldas:
                    respuesta = CeldaModel.mdlCalcularVelocidadFechasMes(tabla, idcomponente, listaidceldas, fechaini, fechafin)
                    if respuesta:
                        data.extend(respuesta)
        return data
    
    def ctrlCalcularVelocidadMesReporte(idproyecto,idcomponente, ids, fechaini, fechafin, filtrado):
        data = []
        tabla = f"celda_detalle{idproyecto}"
        if filtrado == 0: # sin fechas
                respuesta = CeldaModel.mdlCalcularVelocidadMes(tabla, idcomponente, ids)
                if respuesta:
                    data.extend(respuesta)
        else:
            respuesta = CeldaModel.mdlCalcularVelocidadFechasMes(tabla, idcomponente, ids, fechaini, fechafin)
            if respuesta:
                data.extend(respuesta)
        return data
    
    def ctrlObtenerAsentamientoCota(idproyecto, celdasmarcadas, fechaini, fechafin, filtrado):
        data = []
        tabla = f"celda_detalle{idproyecto}"
        agrupados = defaultdict(list)
        if filtrado == 0: # sin fechas
            for componente, listaceldas in celdasmarcadas:
                clave = componente[1]
                agrupados[clave].append(listaceldas)
            for idcomponente, celdama in agrupados.items():
                listaidceldas = []
                for celd in celdama:
                    listaidceldas.append(celd[1])
                if listaidceldas:
                    respuesta = CeldaModel.mdlObtenerAsentamientoCota(tabla, idcomponente, listaidceldas)
                    if respuesta:
                        data.extend(respuesta)
        else:
            for componente, listaceldas in celdasmarcadas:
                clave = componente[1]
                agrupados[clave].append(listaceldas)
            for idcomponente, celdama in agrupados.items():
                listaidceldas = []
                for celd in celdama:
                    listaidceldas.append(celd[1])
                if listaidceldas:
                    respuesta = CeldaModel.mdlObtenerAsentamientoFechasCota(tabla, idcomponente, listaidceldas, fechaini, fechafin)
                    if respuesta:
                        data.extend(respuesta)
        return data
    
    def ctrlCalcularAsentamientoIncremental(idproyecto, celdasmarcadas, fechaini, fechafin, filtrado, unidadmedida):
        data = []
        tabla = f"celda_detalle{idproyecto}"
        agrupados = defaultdict(list)
        if filtrado == 0: # sin fechas
            for componente, listaceldas in celdasmarcadas:
                clave = componente[1]
                agrupados[clave].append(listaceldas)
            for idcomponente, celdama in agrupados.items():
                listaidceldas = []
                for celd in celdama:
                    listaidceldas.append(celd[1])
                if listaidceldas:
                    respuesta = CeldaModel.mdlCalcularAsentamientoIncremental(tabla, idcomponente, listaidceldas, unidadmedida)
                    if respuesta:
                        data.extend(respuesta)
        else:
            for componente, listaceldas in celdasmarcadas:
                clave = componente[1]
                agrupados[clave].append(listaceldas)
            for idcomponente, celdama in agrupados.items():
                listaidceldas = []
                for celd in celdama:
                    listaidceldas.append(celd[1])
                if listaidceldas:
                    respuesta = CeldaModel.mdlCalcularAsentamientoFechasIncremental(tabla, idcomponente, listaidceldas, fechaini, fechafin, unidadmedida)
                    if respuesta:
                        data.extend(respuesta)
        return data
    
    def ctrlObtenerAsentamientoAcumulado(idproyecto, celdasmarcadas, fechaini, fechafin, filtrado, unidadmedida):
        data = []
        tabla = f"celda_detalle{idproyecto}"
        agrupados = defaultdict(list)
        if filtrado == 0: # sin fechas
            for componente, listaceldas in celdasmarcadas:
                clave = componente[1]
                agrupados[clave].append(listaceldas)
            for idcomponente, celdama in agrupados.items():
                listaidceldas = []
                for celd in celdama:
                    listaidceldas.append(celd[1])
                if listaidceldas:
                    respuesta = CeldaModel.mdlObtenerAsentamientoAcumulado(tabla, idcomponente, listaidceldas, unidadmedida)
                    if respuesta:
                        data.extend(respuesta)
        else:
            for componente, listaceldas in celdasmarcadas:
                clave = componente[1]
                agrupados[clave].append(listaceldas)
            for idcomponente, celdama in agrupados.items():
                listaidceldas = []
                for celd in celdama:
                    listaidceldas.append(celd[1])
                if listaidceldas:
                    respuesta = CeldaModel.mdlObtenerAsentamientoFechasAcumulado(tabla, idcomponente, listaidceldas, fechaini, fechafin, unidadmedida)
                    if respuesta:
                        data.extend(respuesta)
        return data
    
    def ctrlObtenerAsentamientoFrecuencia(idproyecto, celdasmarcadas, fechaini, fechafin, filtrado):
        data = []
        tabla = f"celda_detalle{idproyecto}"
        agrupados = defaultdict(list)
        if filtrado == 0: # sin fechas
            for componente, listaceldas in celdasmarcadas:
                clave = componente[1]
                agrupados[clave].append(listaceldas)
            for idcomponente, celdama in agrupados.items():
                listaidceldas = []
                for celd in celdama:
                    listaidceldas.append(celd[1])
                if listaidceldas:
                    respuesta = CeldaModel.mdlObtenerAsentamientoFrecuencia(tabla, idcomponente, listaidceldas)
                    if respuesta:
                        data.extend(respuesta)
        else:
            for componente, listaceldas in celdasmarcadas:
                clave = componente[1]
                agrupados[clave].append(listaceldas)
            for idcomponente, celdama in agrupados.items():
                listaidceldas = []
                for celd in celdama:
                    listaidceldas.append(celd[1])
                if listaidceldas:
                    respuesta = CeldaModel.mdlObtenerAsentamientoFechasFrecuencia(tabla, idcomponente, listaidceldas, fechaini, fechafin)
                    if respuesta:
                        data.extend(respuesta)
        return data
    
    def ctrlObtenerAsentamientoTemperatura(idproyecto, celdasmarcadas, fechaini, fechafin, filtrado):
        data = []
        tabla = f"celda_detalle{idproyecto}"
        agrupados = defaultdict(list)
        if filtrado == 0: # sin fechas
            for componente, listaceldas in celdasmarcadas:
                clave = componente[1]
                agrupados[clave].append(listaceldas)
            for idcomponente, celdama in agrupados.items():
                listaidceldas = []
                for celd in celdama:
                    listaidceldas.append(celd[1])
                if listaidceldas:
                    respuesta = CeldaModel.mdlObtenerAsentamientoTemperatura(tabla, idcomponente, listaidceldas)
                    if respuesta:
                        data.extend(respuesta)
        else:
            for componente, listaceldas in celdasmarcadas:
                clave = componente[1]
                agrupados[clave].append(listaceldas)
            for idcomponente, celdama in agrupados.items():
                listaidceldas = []
                for celd in celdama:
                    listaidceldas.append(celd[1])
                if listaidceldas:
                    respuesta = CeldaModel.mdlObtenerAsentamientoFechasTemperatura(tabla, idcomponente, listaidceldas, fechaini, fechafin)
                    if respuesta:
                        data.extend(respuesta)
        return data
    
    def ctrlActualizarLecturaCelda(tabla, data, idproyecto, username, nombres):
        respuesta = CeldaModel.mdlActualizarLecturaCelda(tabla, data, idproyecto, username, nombres)
        return respuesta
    
    def ctrlCambiarEstadoLecturaCelda(tabla, iddetalle):
        respuesta = CeldaModel.mdlCambiarEstadoLecturaCelda(tabla, iddetalle)
        return respuesta
    
    def ctrlCambiarEstadoLecturaCeldaBloque(tabla, iddetalles):
        respuesta = CeldaModel.mdlCambiarEstadoLecturaCeldaBloque(tabla, iddetalles)
        return respuesta
    
    def ctrlEliminarLecturaCelda(tabla, idcelda, idproyecto, username, nombres):
        respuesta = CeldaModel.mdlEliminarLecturaCelda(tabla, idcelda, idproyecto, username, nombres)
        return respuesta
    
    def ctrlEliminarLecturasBloqueCelda(tabla, iddetalles, idproyecto, username, nombres):
        respuesta = CeldaModel.mdlEliminarLecturasBloqueCelda(tabla, iddetalles, idproyecto, username, nombres)
        return respuesta
    
    def ctrlObtenerCeldasAsentamiento(proyecto):
        result = CeldaModel.mdlObtenerCeldasAsentamiento(proyecto)
        return result
    
    def ctrlRegistrarDataCelda(proyectoid, data):
        idsceldas = {item[0] for item in data}
        unique_data = {(item[0], item[1], item[2]): item for item in data}
        datalimpia = list(unique_data.values())
        result = CeldaModel.mdlRegistrarDataCelda(proyectoid, datalimpia, idsceldas)
        return result
    
    def ctrlCambiarComponenteCeldas(idcomponente, nuevocomponente):
        respuesta = CeldaModel.mdlCambiarComponenteCeldas(idcomponente, nuevocomponente)
        return respuesta
    
    def ctrlEliminarCeldas(idcomponente):
        respuesta = CeldaModel.mdlEliminarCeldas(idcomponente)
        return respuesta
    
    def ctrlEliminarDataCeldas(idproyecto, datos):
        tabla = f"celda_detalle{idproyecto}"
        pluvio = [dato[4] for dato in datos]
        respuesta = CeldaModel.mdlEliminarDataCeldas(tabla, pluvio)
        return respuesta
    
    def ctrlObtenerInfoCelda(idinstrumento):
        respuesta = CeldaModel.mdlObtenerInfoCelda(idinstrumento)
        return respuesta
    
    def ctrlActualizarCelda(data):
        respuesta = CeldaModel.mdlActualizarCelda(data)
        return respuesta
    
    def ctrlActualizarCeldaExcel(data):
        respuesta = CeldaModel.mdlActualizarCeldaExcel(data)
        return respuesta
    
    def ctrlEliminarCelda(idinstrumento):
        respuesta = CeldaModel.mdlEliminarCelda(idinstrumento)
        return respuesta
    
    def ctrlEliminarCeldaData(idproyecto, dato):
        tabla = f"celda_detalle{idproyecto}"
        respuesta = CeldaModel.mdlEliminarCeldaData(tabla, dato[4])
        return respuesta
    
    def ctrlTraerDataCeldaAsentamiento(idcelda):
        respuesta = CeldaModel.mdlTraerDataCeldaAsentamiento(idcelda)
        return respuesta
    
    def ctrlCambiarCeldaComponente(idinstrumento, idcomponente):
        respuesta = CeldaModel.mdlCambiarCeldaComponente(idinstrumento, idcomponente)
        return respuesta
    
    def ctrlOmitirLecturaCelda(proyecto,idCelda,fecha):
        tabla=f'celda_detalle{proyecto}'

        respuesta= CeldaModel.mdlOmitirLecturaCelda(tabla,int(idCelda),fecha)
        return respuesta
    