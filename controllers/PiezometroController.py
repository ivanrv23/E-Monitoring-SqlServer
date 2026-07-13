import numpy as np
from collections import defaultdict
from itertools import chain
from datetime import datetime
from models.PiezometroModel import PiezometroModel
from utils.common.metodosGenerales import MetodosGenerales

class PiezometroController:    
    
    def ctrlObtenerFechasRangoPiezometrosCuerda(proyectoid):
        tabla = f"piezometrocuerda_detalle{proyectoid}"
        fecha = PiezometroModel.mdlObtenerFechaMaximaPiezometrosCuerda(tabla)
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
    
    def ctrlObtenerFechasRangoPiezometrosManual(proyectoid):
        tabla = f"piezometromanual_detalle{proyectoid}"
        fecha = PiezometroModel.mdlObtenerFechaMaximaPiezometrosManual(tabla)
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
    
    def ctrlListarPiezometrosCuerdaProyecto(idproyecto, piezometrosmarcados):
        piezometros = []
        for componente, listapiezometros in piezometrosmarcados:
            nombrecomponente, idcomponente, idproy = componente
            for nombrepiezo, idinstru, fecha in listapiezometros:
                infopiezo = PiezometroModel.mdlListarPiezometrosCuerdaProyecto(idproyecto, idcomponente, idinstru, fecha)
                if infopiezo:
                    piezometros.append(infopiezo)
        return piezometros
    
    def ctrlListarPiezometrosManualProyecto(idproyecto, piezometrosmarcados):
        piezometros = []
        for componente, listapiezometros in piezometrosmarcados:
            nombrecomponente, idcomponente, idproy = componente
            for nombrepiezo, idinstru, fecha in listapiezometros:
                infopiezo = PiezometroModel.mdlListarPiezometrosManualProyecto(idproyecto, idcomponente, idinstru, fecha)
                if infopiezo:
                    piezometros.append(infopiezo)
        return piezometros
    
    def ctrlCalcularDistanciaCoordenadas(este, norte, nivel, superficie, inclinacion, azimuth):
        inclination_rad = inclinacion * np.pi / 180
        azimuth_rad = azimuth * np.pi / 180
        delta_z = superficie - nivel
        if inclinacion == 0:
            distancia = 0
        else:
            distancia = delta_z / np.sin(inclination_rad)
        dir_x = np.cos(inclination_rad) * np.cos(azimuth_rad)
        dir_y = np.cos(inclination_rad) * np.sin(azimuth_rad)
        x = este + distancia * dir_x
        y = norte + distancia * dir_y
        return distancia, x, y
    
    # traer piezómetros únicos que tengan data
    def ctrlListarPiezometrosInfoProyecto(proyecto):
        datos = []
        cuerdas = PiezometroModel.mdlListarPiezometrosCuerdaInfoProyecto(proyecto)
        if cuerdas is not None:
            for dato in cuerdas:
                item = ("Automatizado", dato)
                datos.append(item)
        manuales = PiezometroModel.mdlListarPiezometrosManualInfoProyecto(proyecto)
        if manuales is not None:
            for datito in manuales:
                item1 = ("Manual", datito)
                datos.append(item1)
        return datos
    
    # listar detalle de piezometro por id
    def ctrlTraerLecturasPiezometro(tipo, idpiezometro):
        if tipo == "Automatizado":
            respuesta = PiezometroModel.mdlListarFechasPiezometroCuerda(idpiezometro)
        else:
            respuesta = PiezometroModel.mdlListarFechasPiezometroManual(idpiezometro)
        return respuesta

    def ctrlDataPiezometrosCuerdaProyectoId(proyectoid):
        respuesta = PiezometroModel.mdlDataPiezometrosCuerdaProyectoId(proyectoid)
        return respuesta
    
    def ctrlMostrarDataPiezometrosCuerdaProyecto(iddetalle):
        respuesta = PiezometroModel.mdlMostrarDataPiezometrosCuerdaProyecto(iddetalle)
        return respuesta
    
    def ctrlDataPiezometrosManualProyectoId(proyectoid):
        respuesta = PiezometroModel.mdlDataPiezometrosManualProyectoId(proyectoid)
        return respuesta
    
    def ctrlMostrarDataPiezometrosManualProyecto(iddetalle):
        respuesta = PiezometroModel.mdlMostrarDataPiezometrosManualProyecto(iddetalle)
        return respuesta
    
    def ctrlGuardarNuevoPiezometroManual(proyectoid,componente, nombre, codigo, norte, este, nivel, fundacion, stick, profundidad, inclinacion, azimut, comentario):
        # validar nombre
        respu, info = PiezometroModel.mdlComprobarExisteNombrePiezometro(proyectoid, nombre, "Manual")
        if respu:
            respuesta = "NO"
        else:
            fecha = f"{datetime.now().strftime('%Y-%m-%d')} 00:00:00"
            inclination_rad = inclinacion * np.pi / 180
            dir_z = np.sin(inclination_rad)
            instalacion = "{:.3f}".format(nivel + -abs(profundidad) * dir_z)
            datos = (proyectoid, nombre, codigo, norte, este, instalacion, fundacion, stick, inclinacion, azimut, comentario)
            respuesta = PiezometroModel.mdlGuardarNuevoPiezometroManual(componente,datos, fecha, nivel, "PVC")
        return respuesta
    
    def ctrlComprobarExisteNombrePiezometro(proyectoid, nombre, tipo):
        respuesta, info = PiezometroModel.mdlComprobarExisteNombrePiezometro(proyectoid, nombre, tipo)
        return respuesta, info
    
    def ctrlRegistrarPiezometroManualFormato(componente, datos, fecha, nivel, tipo):
        respuesta = PiezometroModel.mdlRegistrarPiezometroManualFormato(componente, datos, fecha, nivel, tipo)
        return respuesta
    
    def ctrlGuardarNuevoPiezometroCuerda(proyectoid, componente, formula, nombre, serie, este, norte, instalacion, fundacion, nivelactual, inclinacion, azimut, lecturaini, temperaini, presionini, calibracion, tempecorrec, lectura, variablea, variableb, variablec, conversion, comentario):
        respu, info = PiezometroModel.mdlComprobarExisteNombrePiezometro(proyectoid, nombre, "Automatizado")
        if respu:
            respuesta = "NO"
        else:
            fecha = f"{datetime.now().strftime('%Y-%m-%d')} 00:00:00"
            datos = (proyectoid, formula, nombre, serie, este, norte, instalacion, fundacion, inclinacion, azimut, lecturaini, temperaini, presionini, calibracion, tempecorrec, lectura, variablea, variableb, variablec, conversion, comentario)
            respuesta = PiezometroModel.mdlGuardarNuevoPiezometroCuerda(componente, datos, nivelactual, fecha, "PCV")
        return respuesta
    
    def ctrlRegistrarPiezometroCuerdaFormato(componente, datos, fecha, nivel, tipo):
        respuesta = PiezometroModel.mdlRegistrarPiezometroCuerdaFormato(componente, datos, fecha, nivel, tipo)
        return respuesta
    
    def ctrlActualizarPiezometroCuerda(datos, data):
        respuesta = PiezometroModel.mdlActualizarPiezometroCuerda(datos, data)
        return respuesta
    
    def ctrlActualizarPiezometroCuerdaFormato(datos):
        respuesta = PiezometroModel.mdlActualizarPiezometroCuerdaFormato(datos)
        return respuesta
    
    def ctrlActualizarPiezometroManual(datos, data):
        respuesta = PiezometroModel.mdlActualizarPiezometroManual(datos, data)
        return respuesta
    
    def ctrlActualizarPiezometroManualFormato(datos):
        respuesta = PiezometroModel.mdlActualizarPiezometroManualFormato(datos)
        return respuesta
    
    def ctrlCambiarTipoDataPiezometro(idpiezo, estado):
        respuesta = PiezometroModel.mdlCambiarTipoDataPiezometro(idpiezo, estado)
        return respuesta
    
    # registrar medida de piezometro manual
    def ctrlRegistrarMedidaPiezometroManual(idpiezometro, fecha, hora, medida):
        respuesta = PiezometroModel.mdlRegistrarMedidaPiezometroManual(idpiezometro, fecha, hora, medida)
        return respuesta
    
    # registrar piezometros manuales
    def ctrlGuardarPiezometrosManualesTabla(proyectoid, data):
        unique_data = {(item[1], item[2]): item for item in data}
        datalimpia = list(unique_data.values())
        respuesta = PiezometroModel.mdlGuardarPiezometrosManualesTabla(proyectoid, datalimpia)
        return respuesta
    
    def ctrlGuardarCotasPiezometricasTabla(data):
        respuesta = PiezometroModel.mdlGuardarCotasPiezometricasTabla(data)
        return respuesta
    
    # registrar data original piezometros de cuerda vibrante
    def ctrlGuardarPiezometrosCuerdaOriginal(data):
        respuesta = PiezometroModel.mdlGuardarPiezometrosCuerdaTablaOriginal(data)
        return respuesta
    
    # registrar data calculada piezometros de cuerda vibrante
    def ctrlGuardarPiezometrosCuerdaCalculada(proyectoid, data, estadonivel):
        idspiezos = {item[0] for item in data}
        unique_data = {(item[0], item[1], item[2]): item for item in data}
        datalimpia = list(unique_data.values())
        respuesta = PiezometroModel.mdlGuardarPiezometrosCuerdaCalculoTabla(proyectoid, datalimpia, idspiezos)
        if respuesta:
            if estadonivel:
                respuesta = PiezometroModel.mdlCambiarEstadoPiezometroCuerda(data[0][0], 2) # 2 es con cota
            else:
                respuesta = PiezometroModel.mdlCambiarEstadoPiezometroCuerda(data[0][0], 1) # 1 es sin cota
        else:
            respuesta = False
        return respuesta

    # comprobar si existe una fecha del mismo piezometro marcada
    def ctrlComprobarMismoPiezometro(arreglo, codigoid, tipo):
        encontrado = False
        for code, tipito, idpiezo in arreglo:
            if idpiezo == codigoid and tipo == tipito:
                encontrado = True
                break
        return encontrado

    # comprobar si existe una fecha del mismo piezometro marcada
    def ctrlComprobarMismoPiezometroMarcado(arreglo, codigoid, tipito):
        encontrado = False
        for code, tipo, idpiezo in arreglo[1:]:
            if idpiezo == codigoid and tipo == tipito:
                encontrado = True
                break
        return encontrado
    
    def ctrlComprobarDiferentePiezometro(arreglo, codigoid):
        encontrado = True
        for code, tipo, idpiezo in arreglo:
            if idpiezo != codigoid:
                encontrado = False
                break
        return encontrado
    
    def ctrlTraerInfoPiezometro(idipiezo, tipo):
        if tipo == "Automatizado":
            respuesta = PiezometroModel.mdlTraerInfoPiezometroCuerda(idipiezo)
        else:
            respuesta = PiezometroModel.mdlTraerInfoPiezometroManual(idipiezo)
        return respuesta
    
    def ctrlTraerInfoDetallePiezometro(iddetalle, tipo):
        if tipo == "Automatizado":
            respuesta = PiezometroModel.mdlTraerInfoDetallePiezometroCuerda(iddetalle)
        else:
            respuesta = PiezometroModel.mdlTraerInfoDetallePiezometroManual(iddetalle)
        return respuesta
    
    def ctrlTraerBaseDetallePiezometro(idpiezo):
        respuesta = PiezometroModel.mdlTraerBaseDetallePiezometro(idpiezo)
        return respuesta

    #calculo de agua para ejemplo:
    def ctrlCalculosPiezometros(piezometrofechasmarcados):
        tipopie = piezometrofechasmarcados[0][1]
        idpiezo = piezometrofechasmarcados[0][2]
        if tipopie == "Automatizado":
            piedatos = PiezometroModel.mdlObtenerDataPiezometroA(idpiezo)
        else:
            piedatos = PiezometroModel.mdlObtenerDataPiezometroN(idpiezo)
        # obtenemos los ids
        idpiedatos = {tubo[0]: tubo for tubo in piedatos}
        datos = []
        # solo marcados
        for idp, tip, idpiez in piezometrofechasmarcados:
            datos.append(idpiedatos[float(idp)])
        # ordenar por fecha   
        data_ordenada = sorted(datos, key=lambda x: x[3])
        if tipopie == "Automatizado":
            estado_piezometro = data_ordenada[0][10]
            if estado_piezometro == 0: # data original
                data_resultados = PiezometroController.calculosPiezometrosAuto(data_ordenada)
            elif estado_piezometro == 1: # data calculada sin cota
                data_resultados = PiezometroController.ctrlCalcularNivelFreatico(data_ordenada)
            else: # data calculada con cota
                data_resultados = PiezometroController.ctrlCalcularFreaticoAcumulado(data_ordenada)
        else:
            data_resultados = PiezometroController.calculosPiezometrosManuales(data_ordenada)
        return tipopie, data_resultados
    
    # calcular nivel freatico con data calculada
    def ctrlCalcularNivelFreatico(data_ordenada):
        niveles_agua = []
        data_resultados = []
        for row in data_ordenada:
            cota = row[9]
            acumulado = row[11]
            niveles_agua.append(acumulado + cota)
        for i in range(len(data_ordenada)):
            resultado_tupla = data_ordenada[i] + (niveles_agua[i],)
            data_resultados.append(resultado_tupla)
        return data_resultados
    
    # calcular acumulado sin cota con data calculada
    def ctrlCalcularFreaticoAcumulado(data_ordenada):
        niveles_agua = []
        data_resultados = []
        for row in data_ordenada:
            cota = row[9]
            acumulado = row[11]
            niveles_agua.append(acumulado - cota)
        for i in range(len(data_ordenada)):
            resultado_tupla = data_ordenada[i] + (niveles_agua[i],)
            data_resultados.append(resultado_tupla)
        return data_resultados
        
    def calculosPiezometrosAuto(data_ordenada):
        niveles_agua = []
        data_resultados = []
        niveles_pma = []
        cf=data_ordenada[0][4]
        tk=data_ordenada[0][5]
        li=data_ordenada[0][6]
        ti=data_ordenada[0][7]
        bi=data_ordenada[0][8]
        z=data_ordenada[0][9]
        # Procesar los resultados
        for index, row in enumerate(data_ordenada):
            if index > 0:  # Omite la primera fila
                lc = row[6]
                tc = row[7]
                bc = row[8]
                nivel_pma = PiezometroController.ctrlCalcularPMApiezometroCuerda(cf,tk,li,ti,bi,lc,tc,bc)
                niveles_pma.append(nivel_pma)

        if len(niveles_pma) > 0:
            niveles_agua = [((valor * 101.974428) + z) for valor in niveles_pma]
        altura_incremental, altura_acumulada = PiezometroController.calcular_alturas(niveles_agua)
        for i in range(1, len(data_ordenada)):
            resultado_tupla = data_ordenada[i] + (
                altura_acumulada[i - 1],
                altura_incremental[i - 1],
                niveles_agua[i - 1]
            )
            data_resultados.append(resultado_tupla)
    
        return data_resultados

    def ctrlCalcularPMApiezometroCuerda(cf,tk,li,ti,bi,lc,tc,bc):
        resultadopma = (float(cf) * (float(li) - float(lc))) - (float(tk) * (float(ti) - float(tc))) + (0.0001 * (float(bi) - float(bc)))
        return resultadopma
        
    def calculosPiezometrosManuales(data_ordenada):
        niveles_agua = []
        data_resultados = []
        # Procesar los resultados
        for row in data_ordenada:
            elevacion = row[6]
            medida = row[4]
            stickup = row[5]
            nivel_agua = PiezometroController.calcular_nivel_aguaM(elevacion, medida, stickup)
            niveles_agua.append(nivel_agua)
        altura_incremental, altura_acumulada = PiezometroController.calcular_alturas(niveles_agua)
        for i in range(len(data_ordenada)):
            resultado_tupla = data_ordenada[i] + (
                altura_acumulada[i], 
                altura_incremental[i],
                niveles_agua[i]
            )
            data_resultados.append(resultado_tupla)
        return data_resultados
            
    def calcular_nivel_aguaM(elevacion, medida, stickup):
        return elevacion - (medida - (stickup / 100))

    def calcular_alturas(niveles_agua):
        alturas_acumuladas = []
        alturas_incrementales = []

        for idx, nivel_agua in enumerate(niveles_agua):
            if idx == 0:
                altura_incremental = 0.0
                altura_acumulada = 0.0
            else:
                altura_incremental = nivel_agua - niveles_agua[idx - 1]
                altura_acumulada = nivel_agua - niveles_agua[0]
            alturas_incrementales.append(altura_incremental)
            alturas_acumuladas.append(altura_acumulada)

        return alturas_incrementales, alturas_acumuladas
    
    def ctrlCalcularCoordenadas3d(este, norte, nivel, inclinacion, azimuth, profundidad):
        este = float(este)
        norte = float(norte)
        nivel = float(nivel)
        profundidad = float(profundidad)
        inclinacion = float(inclinacion)
        azimuth = float(azimuth)
        # 
        inclination_rad = inclinacion * np.pi / 180
        azimuth_rad = azimuth * np.pi / 180
        dir_x = np.cos(inclination_rad) * np.cos(azimuth_rad)
        dir_y = np.cos(inclination_rad) * np.sin(azimuth_rad)
        dir_z = np.sin(inclination_rad)
        x = este + profundidad * dir_x
        y = norte + profundidad * dir_y
        z = nivel + profundidad * dir_z
        return x, y, z

    def ctrlTransformarPiezometrosUnicos(data_set):
        unique_data = {}
        for elemento in data_set:
            tipo_actual = elemento[1]
            id_actual = elemento[2]
            clave = (tipo_actual, id_actual)
            if clave not in unique_data:
                unique_data[clave] = elemento
        data_list = list(unique_data.values())
        return data_list

    # calculos de todos los piezometros para vista analisis
    def ctrlCalculosPiezometrosAnalisis(piezometrosunicos, piezometrofechasmarcados, fechaini, fechafin):
        datacalculos = []
        tipopie = ""
        idpiezometro = 0
        for iddetalle, tipo, idpiezo in piezometrosunicos:
            idpiezometro = idpiezo
            if tipo == "Automatizado":
                piedatos = PiezometroModel.mdlObtenerDataPiezometroAutoFechas(idpiezo, fechaini, fechafin)
                tipopie = "Automatizado"
            else:
                piedatos = PiezometroModel.mdlObtenerDataPiezometroManualFechas(idpiezo, fechaini, fechafin)
                tipopie = "Manual"
            # obtenemos los ids
            if piedatos is not None:
                idpiedatos = {tubo[0]: tubo for tubo in piedatos}
                datos = []
                # solo marcados
                for idp, tip, idpiez in piezometrofechasmarcados:
                    if float(idp) in idpiedatos:
                        datos.append(idpiedatos[float(idp)])
                # ordenar por fecha   
                data_ordenada = sorted(datos, key=lambda x: x[3])
                if tipopie == "Automatizado":
                    estado_piezometro = data_ordenada[0][10]
                    if estado_piezometro == 0: # data original
                        data_resultados = PiezometroController.calculosPiezometrosAuto(data_ordenada)
                    elif estado_piezometro == 1: # data calculada sin cota
                        data_resultados = PiezometroController.ctrlCalcularNivelFreatico(data_ordenada)
                    else: # data calculada con cota
                        data_resultados = PiezometroController.ctrlCalcularFreaticoAcumulado(data_ordenada)
                else:
                    data_resultados = PiezometroController.calculosPiezometrosManuales(data_ordenada)
                datacalculos.append((idpiezometro, data_resultados))
        return datacalculos
    
    # obtener medidas minimos y máximos
    def ctrlObtenerMinimosMaximosNivelAgua(datos):
        datos_planos = list(chain(*datos))
        minimo = min(datos_planos)
        maximo = max(datos_planos)
        return minimo, maximo
    
    # obtener fechas minimos y máximos
    def ctrlObtenerMinimosMaximosFechas(datos_fechas):
        datos_fechas_convertidas = [fecha for tupla in datos_fechas for fecha in tupla]
        fecha_minima = min(datos_fechas_convertidas)
        fecha_maxima = max(datos_fechas_convertidas)
        return fecha_minima, fecha_maxima
    
    def crtObtenerRangoFechasPiezometros(proyectoid):       
        fechasa = PiezometroModel.mdlObtenerFechaMinMaxCuerda(proyectoid)
        fechasm = PiezometroModel.mdlObtenerFechaMinMaxPiezomanual(proyectoid)
        if fechasa is None and fechasm is None:
            return None
        elif fechasa is not None and fechasm is not None:
            if fechasa[0] is None and fechasm[0] is None:
                return None
            elif fechasa[0] is not None and fechasm[0] is not None:
                fechaamin = min(fechasa[0], fechasm[0])
                fechaamax = max(fechasa[1], fechasm[1])
                return [fechaamin, fechaamax]
            else:
                if fechasa[0] is not None:
                    return fechasa
                else:
                    return fechasm
        elif fechasa is not None:
            return fechasa
        else:
            return fechasm
                       
    def ctrlObtenerFechasUnicasSuelos(datasuelos, fechitas):
        fechasuelo = []
        medidasuelo = []
        medida1 = datasuelos[0][3]
        datos_fechas_convertidas = [fecha for tupla in fechitas for fecha in tupla]
        fechas_unicas = set(datos_fechas_convertidas)
        fechas_unicas_lista = sorted(fechas_unicas)
        for fecha in fechas_unicas_lista:
            for data in datasuelos:
                fechita = datetime.strptime(data[2], '%Y-%m-%d %H:%M:%S')
                if fechita.date() <= fecha.date():
                    medida1 = data[3]
            fechasuelo.append(fecha)
            medidasuelo.append(medida1)
        return fechasuelo, medidasuelo

    def ctrlCalcularPiezometrosCuerda(idproyecto, piezocuerdamarcados, fechaini, fechafin, filtrado, unidadmedida):
        datos = []
        tabla = f"piezometrocuerda_detalle{idproyecto}"
        agrupados = defaultdict(list)
        if filtrado == 0: # sin fechas
            for componente, listacuerdas in piezocuerdamarcados:
                clave = componente[1]
                agrupados[clave].append(listacuerdas)
            for idcomponente, piezoma in agrupados.items():
                for piezo in piezoma:
                    nombrepie, idinstru, idpiezo = piezo
                    resultado = PiezometroModel.mdlObtenerFormulaPiezometroCuerda(idpiezo)
                    if resultado[0] == 0:
                        respuesta = PiezometroModel.mdlCalcularPiezometrosCuerda(tabla, idcomponente, idinstru, unidadmedida)
                    else:
                        respuesta = PiezometroModel.mdlCalcularPiezometrosCuerdaFormula(tabla, idcomponente, idinstru, unidadmedida, resultado[1])
                    if respuesta:
                        datos.extend(respuesta)
        else:
            for componente, listacuerdas in piezocuerdamarcados:
                clave = componente[1]
                agrupados[clave].append(listacuerdas)
            for idcomponente, piezoma in agrupados.items():
                for piezo in piezoma:
                    nombrepie, idinstru, idpiezo = piezo
                    resultado = PiezometroModel.mdlObtenerFormulaPiezometroCuerda(idpiezo)
                    if resultado[0] == 0:
                        respuesta = PiezometroModel.mdlCalcularPiezometrosFechasCuerda(tabla, idcomponente, idinstru, unidadmedida, fechaini, fechafin)
                    else:
                        respuesta = PiezometroModel.mdlCalcularPiezometrosFechasCuerdaFormula(tabla, idcomponente, idinstru, unidadmedida, fechaini, fechafin, resultado[1])
                    if respuesta:
                        datos.extend(respuesta)
        return datos
    
    def ctrlCalcularPiezometrosCasaGrande(idproyecto, piezomanualesmarcados, fechaini, fechafin, filtrado, unidadmedida):
        data = []
        tabla = f"piezometromanual_detalle{idproyecto}"
        agrupados = defaultdict(list)
        if filtrado == 0: # sin fechas
            for componente, listamanuales in piezomanualesmarcados:
                clave = componente[1]
                agrupados[clave].append(listamanuales)
            for idcomponente, piezoma in agrupados.items():
                listapiezo = []
                for piezo in piezoma:
                    listapiezo.append(piezo[1])
                if listapiezo:
                    respuesta = PiezometroModel.mdlCalcularPiezometrosCasaGrande(tabla, idcomponente, listapiezo, unidadmedida)
                    if respuesta:
                        data.extend(respuesta)
        else:
            for componente, listamanuales in piezomanualesmarcados:
                clave = componente[1]
                agrupados[clave].append(listamanuales)
            for idcomponente, piezoma in agrupados.items():
                listapiezo = []
                for piezo in piezoma:
                    listapiezo.append(piezo[1])
                if listapiezo:
                    respuesta = PiezometroModel.mdlCalcularPiezometrosFechasCasaGrande(tabla, idcomponente, listapiezo, unidadmedida, fechaini, fechafin)
                    if respuesta:
                        data.extend(respuesta)
        return data
    
    def ctrlActualizarLecturaPiezoCuerda(tabla, datos, idproyecto, username, nombres):
        respuesta = PiezometroModel.mdlActualizarLecturaPiezometroCuerda(tabla, datos, idproyecto, username, nombres)
        return respuesta
    
    
#------------------------------------------------------------------------------------------------------------
    def ctrlActualizarLecturaPiezoCuerdaConEstado(tabla, datos, idproyecto, username, nombres):
        """
        Actualiza lectura de piezómetro cuerda incluyendo el estado
        datos = [datofecha, datofrecuencia, datotemperatura, datopresion, datomedida, datoobserva, datoestado, iddetalle]
        donde datoestado puede ser "Activo" u "Omitido"
        """
        respuesta = PiezometroModel.mdlActualizarLecturaPiezometroCuerdaConEstado(tabla, datos, idproyecto, username, nombres)
        return respuesta
    
    def ctrlActualizarLecturaPiezoManualConEstado(tabla, datos, idproyecto, username, nombres):
        """
        Actualiza lectura de piezómetro manual incluyendo el estado
        datos = [datofecha, datomedida, datoobserva, datoestado, iddetalle]
        donde datoestado puede ser "Activo" u "Omitido"
        """
        respuesta = PiezometroModel.mdlActualizarLecturaPiezometroManualConEstado(tabla, datos, idproyecto, username, nombres)
        return respuesta
    
    def ctrlConvertirEstadoTextoAValor(estado_texto):
        """
        Convierte el texto del ComboBox a valor numérico para la BD
        "Activo" -> 1
        "Omitido" -> 0
        """
        return 1 if estado_texto == "Activo" else 0

    def ctrlConvertirEstadoValorATexto(estado_valor):
        """
        Convierte el valor numérico de la BD a texto para el ComboBox
        1 -> "Activo"
        0 -> "Omitido"
        """
        return "Activo" if estado_valor == 1 else "Omitido"
    
    def ctrlActualizarSoloEstadoPiezoCuerda(tabla, iddetalle, nuevo_estado):
        """
        Actualiza únicamente el estado de una lectura sin modificar otros datos
        """
        estado_valor = PiezometroController.ctrlConvertirEstadoTextoAValor(nuevo_estado)
        respuesta = PiezometroModel.mdlActualizarSoloEstadoPiezoCuerda(tabla, iddetalle, estado_valor)
        return respuesta

    def ctrlActualizarSoloEstadoPiezoManual(tabla, iddetalle, nuevo_estado):
        """
        Actualiza únicamente el estado de una lectura sin modificar otros datos
        """
        estado_valor = PiezometroController.ctrlConvertirEstadoTextoAValor(nuevo_estado)
        respuesta = PiezometroModel.mdlActualizarSoloEstadoPiezoManual(tabla, iddetalle, estado_valor)
        return respuesta
#----------------------------------------------------------------------------------------------------


    def ctrlValidarExisteFormula(formula):
        respuesta = PiezometroModel.mdlValidarExisteFormula(formula)
        return respuesta
    
    def ctrlRegistrarNuevaFormula(formula, sentencia):
        respuesta = PiezometroModel.mdlRegistrarNuevaFormula(formula, sentencia)
        return respuesta
    
    def ctrlCambiarEstadoLecturaPiezoCuerda(tabla, iddetalle):
        respuesta = PiezometroModel.mdlCambiarEstadoLecturaPiezoCuerda(tabla, iddetalle)
        return respuesta
    
    def ctrlCambiarEstadoLecturaPiezoCuerdaBloque(tabla, iddetalles):
        respuesta = PiezometroModel.mdlCambiarEstadoLecturaPiezoCuerdaBloque(tabla, iddetalles)
        return respuesta
    
    def ctrlEliminarLecturaPiezoCuerda(tabla, iddetalle, idproyecto, username, nombres):
        respuesta = PiezometroModel.mdlEliminarLecturaPiezoCuerda(tabla, iddetalle, idproyecto, username, nombres)
        return respuesta
    
    def ctrlEliminarLecturasBloquePiezoCuerda(tabla, iddetalles, idproyecto, username, nombres):
        respuesta = PiezometroModel.mdlEliminarLecturasBloquePiezoCuerda(tabla, iddetalles, idproyecto, username, nombres)
        return respuesta
    
    def ctrlActualizarLecturaPiezoManual(tabla, datos, idproyecto, username, nombres):
        respuesta = PiezometroModel.mdlActualizarLecturaPiezometroManual(tabla, datos, idproyecto, username, nombres)
        return respuesta
    
    def ctrlActualizarCotaPiezometrica(idproyecto, idcota, datofecha, cotamedida, username, nombres):
        respuesta = PiezometroModel.mdlActualizarCotaPiezometrica(idproyecto, idcota, datofecha, cotamedida, username, nombres)
        return respuesta
    
    def ctrlCambiarEstadoLecturaPiezoManual(tabla, iddetalle):
        respuesta = PiezometroModel.mdlCambiarEstadoLecturaPiezoManual(tabla, iddetalle)
        return respuesta
    
    def ctrlCambiarEstadoLecturaPiezoManualBloque(tabla, iddetalles):
        respuesta = PiezometroModel.mdlCambiarEstadoLecturaPiezoManualBloque(tabla, iddetalles)
        return respuesta
    
    def ctrlEliminarLecturaPiezoManual(tabla, iddetalle, idproyecto, username, nombres):
        respuesta = PiezometroModel.mdlEliminarLecturaPiezoManual(tabla, iddetalle, idproyecto, username, nombres)
        return respuesta
    
    def ctrlEliminarLecturasBloquePiezoManual(tabla, iddetalles, idproyecto, username, nombres):
        respuesta = PiezometroModel.mdlEliminarLecturasBloquePiezoManual(tabla, iddetalles, idproyecto, username, nombres)
        return respuesta
    
    def ctrlListarPiezometrosCuerda(proyecto):
        respuesta = PiezometroModel.mdlListarPiezometrosCuerda(proyecto)
        return respuesta
    
    def ctrlListarPiezometrosManuales(proyecto):
        respuesta = PiezometroModel.mdlListarPiezometrosManuales(proyecto)
        return respuesta
    
    def ctrlCambiarComponentePiezometrosCuerda(idcomponente, nuevocomponente):
        respuesta = PiezometroModel.mdlCambiarComponentePiezometrosCuerda(idcomponente, nuevocomponente)
        return respuesta
    
    def ctrlTraerCotaPiezometrica(idcota):
        respuesta = PiezometroModel.mdlTraerCotaPiezometrica(idcota)
        return respuesta
    
    def ctrlEliminarPiezometrosCuerda(idcomponente):
        respuesta = PiezometroModel.mdlEliminarPiezometrosCuerda(idcomponente)
        return respuesta
    
    def ctrlEliminarDataPiezometrosCuerda(idproyecto, datos):
        tabla = f"piezometrocuerda_detalle{idproyecto}"
        cuerdas = [dato[4] for dato in datos]
        respuesta = PiezometroModel.mdlEliminarDataPiezometrosCuerda(tabla, cuerdas)
        return respuesta
    
    def ctrlObtenerInfoPiezometroCuerda(idinstrumento):
        respuesta = PiezometroModel.mdlObtenerInfoPiezometroCuerda(idinstrumento)
        return respuesta
    
    def ctrlEliminarCuerdaVibrante(idinstrumento):
        respuesta = PiezometroModel.mdlEliminarCuerdaVibrante(idinstrumento)
        return respuesta
    
    def ctrlEliminarCuerdaVibranteData(idproyecto, dato):
        tabla = f"piezometrocuerda_detalle{idproyecto}"
        respuesta = PiezometroModel.mdlEliminarCuerdaVibranteData(tabla, dato[4])
        return respuesta
    
    def ctrlCambiarComponentePiezometrosManuales(idcomponente, nuevocomponente):
        respuesta = PiezometroModel.mdlCambiarComponentePiezometrosManuales(idcomponente, nuevocomponente)
        return respuesta
    
    def ctrlEliminarPiezometrosManuales(idcomponente):
        respuesta = PiezometroModel.mdlEliminarPiezometrosManuales(idcomponente)
        return respuesta
    
    def ctrlEliminarDataPiezometrosManuales(idproyecto, datos):
        tabla = f"piezometromanual_detalle{idproyecto}"
        manuales = [dato[4] for dato in datos]
        respuesta = PiezometroModel.mdlEliminarDataPiezometrosManuales(tabla, manuales)
        return respuesta
    
    def ctrlObtenerInfoPiezometroManual(idinstrumento):
        respuesta = PiezometroModel.mdlObtenerInfoPiezometroManual(idinstrumento)
        return respuesta
    
    def ctrlEliminarManualPiezometro(idinstrumento):
        respuesta = PiezometroModel.mdlEliminarManualPiezometro(idinstrumento)
        return respuesta
    
    def ctrlEliminarPiezometroManualData(idproyecto, dato):
        tabla = f"piezometromanual_detalle{idproyecto}"
        respuesta = PiezometroModel.mdlEliminarPiezometroManualData(tabla, dato[4])
        return respuesta
    
    def ctrlListarFechasPiezometro(tipo, idcomponente, idinstrumento, proyectoid):
        if tipo == "Automatizado":
            tabla = f"piezometrocuerda_detalle{proyectoid}"
            respuesta = PiezometroModel.mdlListarFechasPiezometroCuerda(tabla, idcomponente, idinstrumento, proyectoid)
        else:
            tabla = f"piezometromanual_detalle{proyectoid}"
            respuesta = PiezometroModel.mdlListarFechasPiezometroManual(tabla, idcomponente, idinstrumento, proyectoid)
        return respuesta
    
    def ctrlObtenerResumenCuerdaReporte(idproyecto,idcomponente, fechaini, fechafin):
        respuesta = PiezometroModel.mdlObtenerResumenCuerdaReporte(idproyecto,idcomponente, fechaini, fechafin)
        return respuesta
    
    def ctrlObtenerResumenCasagrandeReporte(idproyecto,idcomponente, fechaini, fechafin):
        respuesta = PiezometroModel.mdlObtenerResumenCasagrandeReporte(idproyecto,idcomponente, fechaini, fechafin)
        return respuesta
    
    def ctrlTraerDataPiezometro(idpiezometro, tipo):
        respuesta = PiezometroModel.mdlTraerDataPiezometro(idpiezometro, tipo)
        return respuesta
    
    def ctrlCambiarPiezometroComponente(idinstrumento, idcomponente):
        respuesta = PiezometroModel.mdlCambiarPiezometroComponente(idinstrumento, idcomponente)
        return respuesta
    
    def ctrlTraerListaFormulas():
        respuesta = PiezometroModel.mdlTraerListaFormulas()
        return respuesta
    
    def ctrlOmitirLecturaPiezometro(proyecto,idPiezo,fecha,tipo):
        if tipo=='PIEZOMETROCUERDA':
            tabla=f'piezometrocuerda_detalle{proyecto}'
            campo='estado_cuerda'
            campo_fecha='fecha_cuerda'
        else:
            tabla=f'piezometromanual_detalle{proyecto}'
            campo='estado_manual'
            campo_fecha='fecha_piezometro'

        respuesta= PiezometroModel.mdlOmitirLecturaPiezometro(tabla,int(idPiezo),fecha,campo,campo_fecha)
        return respuesta