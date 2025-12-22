import ast
from models.InclinometroModel import InclinometroModel
from models.InterfazModel import InterfazModel
from datetime import datetime

class InclinometroController:
    
    def ctrlListarInclinometrosProyecto(idproyecto, inclinometrosmarcados):
        inclinometros = []
        for componente, listainclinometros in inclinometrosmarcados:
            nombrecomponente, idcomponente, idproy = componente
            for nombreincli, idinstru, fechas in listainclinometros:
                infoincli = InclinometroModel.mdlListarInclinometrosProyecto(idproyecto, idcomponente, idinstru)
                if infoincli:
                    inclinometros.append((infoincli, fechas, idinstru))
        return inclinometros
    
    def ctrlObtenerInclinometroTipo(idproyecto, idcomponente, idinstru):
        tipo = InclinometroModel.mdlObtenerInclinometroTipo(idproyecto, idcomponente, idinstru)
        return tipo
    
    def ctrlObtenerDIABprofundidad(tabla, idcomponente, idinstru, fechitas, unidadmedida, anguzz, mrint, tipo):
        if unidadmedida == 1:
            medida = 1 / 1000
        elif unidadmedida == 100:
            medida = 1 / 10
        else:
            medida = 1
        if tipo == 'RST':
            datos = InclinometroModel.mdlObtenerDIAB_RST(tabla, idcomponente, idinstru, fechitas, unidadmedida)
        else:
            datos = InclinometroModel.mdlObtenerDIAB_GKN(tabla, idcomponente, idinstru, fechitas, medida, anguzz, mrint)
        return datos
    
    def ctrlObtenerDIAB(idproyecto, inclinomarcados, unidadmedida, azimuth, anguzz, rint):
        if unidadmedida == 1:
            medida = 1 / 1000
        elif unidadmedida == 100:
            medida = 1 / 10
        else:
            medida = 1
        m = 0.05
        if rint > 0:
            mrint = m * rint
        else:
            mrint = m * 0.5
        for componente, listainclinometros in inclinomarcados:
            nombrecomponente, idcomponente, idproy = componente
            for nombreincli, idinstru, fechas in listainclinometros:
                tipo = InclinometroModel.mdlObtenerInclinometroTipo(idproyecto, idcomponente, idinstru)
                if tipo:
                    tabla = f"inclinometro_detalle{idproyecto}"
                    fechitas = ast.literal_eval(fechas)
                    if tipo[0] == 'RST':
                        datos = InclinometroModel.mdlObtenerDIAB_RST(tabla, idcomponente, idinstru, fechitas, unidadmedida)
                    else:
                        datos = InclinometroModel.mdlObtenerDIAB_GKN(tabla, idcomponente, idinstru, fechitas, medida, anguzz, mrint)
                    return datos
                else:
                    return None
    
    def ctrlObtenerDINEprofundidad(tabla, idcomponente, idinstru, fechitas, unidadmedida, azimuth, mrint, tipo):
        if unidadmedida == 1:
            medida = 1 / 1000
        elif unidadmedida == 100:
            medida = 1 / 10
        else:
            medida = 1
        alfa = 450 - azimuth
        if tipo == 'RST':
            datos = InclinometroModel.mdlObtenerDINE_RST(tabla, idcomponente, idinstru, fechitas, unidadmedida, alfa)
        else:
            datos = InclinometroModel.mdlObtenerDINE_GKN(tabla, idcomponente, idinstru, fechitas, medida, alfa, mrint)
        return datos
    
    def ctrlObtenerDINE(idproyecto, inclinomarcados, unidadmedida, azimuth, anguzz, rint):
        if unidadmedida == 1:
            medida = 1 / 1000
        elif unidadmedida == 100:
            medida = 1 / 10
        else:
            medida = 1
        alfa = 450 - azimuth
        m = 0.05
        if rint > 0:
            mrint = m * rint
        else:
            mrint = m * 0.5
        for componente, listainclinometros in inclinomarcados:
            nombrecomponente, idcomponente, idproy = componente
            for nombreincli, idinstru, fechas in listainclinometros:
                tipo = InclinometroModel.mdlObtenerInclinometroTipo(idproyecto, idcomponente, idinstru)
                if tipo:
                    tabla = f"inclinometro_detalle{idproyecto}"
                    fechitas = ast.literal_eval(fechas)
                    if tipo[0] == 'RST':
                        datos = InclinometroModel.mdlObtenerDINE_RST(tabla, idcomponente, idinstru, fechitas, unidadmedida, alfa)
                    else:
                        datos = InclinometroModel.mdlObtenerDINE_GKN(tabla, idcomponente, idinstru, fechitas, medida, alfa, mrint)
                    return datos
                else:
                    return None
    
    def ctrlObtenerDAABprofundidad(tabla, idcomponente, idinstru, fechitas, unidadmedida, tipo):
        if unidadmedida == 1:
            medida = 1 / 1000
        elif unidadmedida == 100:
            medida = 1 / 10
        else:
            medida = 1
        if tipo == 'RST':
            datos = InclinometroModel.mdlObtenerDAAB_RST(tabla, idcomponente, idinstru, fechitas, unidadmedida)
        else:
            datos = InclinometroModel.mdlObtenerDAAB_GKN(tabla, idcomponente, idinstru, fechitas, medida)
        return datos
    
    def ctrlObtenerDAAB(idproyecto, inclinomarcados, unidadmedida, azimuth, anguzz, rint):
        if unidadmedida == 1:
            medida = 1 / 1000
        elif unidadmedida == 100:
            medida = 1 / 10
        else:
            medida = 1
        for componente, listainclinometros in inclinomarcados:
            nombrecomponente, idcomponente, idproy = componente
            for nombreincli, idinstru, fechas in listainclinometros:
                tipo = InclinometroModel.mdlObtenerInclinometroTipo(idproyecto, idcomponente, idinstru)
                if tipo:
                    tabla = f"inclinometro_detalle{idproyecto}"
                    fechitas = ast.literal_eval(fechas)
                    if tipo[0] == 'RST':
                        datos = InclinometroModel.mdlObtenerDAAB_RST(tabla, idcomponente, idinstru, fechitas, unidadmedida)
                    else:
                        datos = InclinometroModel.mdlObtenerDAAB_GKN(tabla, idcomponente, idinstru, fechitas, medida)
                    return datos
                else:
                    return None
    
    def ctrlObtenerDANEprofundidad(tabla, idcomponente, idinstru, fechitas, unidadmedida, azimuth, mrint, anguzz, tipo):
        if unidadmedida == 1:
            medida = 1 / 1000
        elif unidadmedida == 100:
            medida = 1 / 10
        else:
            medida = 1
        alfa = 450 - azimuth
        if tipo == 'RST':
            datos = InclinometroModel.mdlObtenerDANE_RST(tabla, idcomponente, idinstru, fechitas, unidadmedida, alfa)
        else:
            datos = InclinometroModel.mdlObtenerDANE_GKN(tabla, idcomponente, idinstru, fechitas, medida, alfa, mrint, anguzz)
        return datos
    
    def ctrlObtenerDANE(idproyecto, inclinomarcados, unidadmedida, azimuth, anguzz, rint):
        if unidadmedida == 1:
            medida = 1 / 1000
        elif unidadmedida == 100:
            medida = 1 / 10
        else:
            medida = 1
        alfa = 450 - azimuth
        m = 0.05
        if rint > 0:
            mrint = m * rint
        else:
            mrint = m * 0.5
        for componente, listainclinometros in inclinomarcados:
            nombrecomponente, idcomponente, idproy = componente
            for nombreincli, idinstru, fechas in listainclinometros:
                tipo = InclinometroModel.mdlObtenerInclinometroTipo(idproyecto, idcomponente, idinstru)
                if tipo:
                    tabla = f"inclinometro_detalle{idproyecto}"
                    fechitas = ast.literal_eval(fechas)
                    if tipo[0] == 'RST':
                        datos = InclinometroModel.mdlObtenerDANE_RST(tabla, idcomponente, idinstru, fechitas, unidadmedida, alfa)
                    else:
                        datos = InclinometroModel.mdlObtenerDANE_GKN(tabla, idcomponente, idinstru, fechitas, medida, alfa, mrint, anguzz)
                    return datos
                else:
                    return None
    
    def ctrlObtenerDANEvisor(idproyecto, idinclino, fechas, tipo, este, norte, nivel, escala):
        datos_por_fecha = {}
        if tipo == 'RST':
            datos = InclinometroModel.mdlObtenerDANEvisor_RST(idproyecto, idinclino, fechas, este, norte, nivel, escala)
        else:
            datos = InclinometroModel.mdlObtenerDANEvisor_GKN(idproyecto, idinclino, fechas, este, norte, nivel, escala)
        if datos:
            for nombre, fecha, profundidad, dac, dax in datos:
                datos_tupla = (nombre, profundidad, dac, dax)
                if fecha in datos_por_fecha:
                    datos_por_fecha[fecha].append(datos_tupla)
                else:
                    datos_por_fecha[fecha] = [datos_tupla]
        return datos_por_fecha
    
    def ctrlObtenerPAABprofundidad(tabla, idcomponente, idinstru, fechitas, unidadmedida, mrint, tipo):
        if unidadmedida == 1:
            medida = 1 / 1000
        elif unidadmedida == 100:
            medida = 1 / 10
        else:
            medida = 1
        if tipo == 'RST':
            datos = InclinometroModel.mdlObtenerPAAB_RST(tabla, idcomponente, idinstru, fechitas, unidadmedida)
        else:
            datos = InclinometroModel.mdlObtenerPAAB_GKN(tabla, idcomponente, idinstru, fechitas, medida, mrint)
        return datos
    
    def ctrlObtenerPAAB(idproyecto, inclinomarcados, unidadmedida, azimuth, anguzz, rint):
        if unidadmedida == 1:
            medida = 1 / 1000
        elif unidadmedida == 100:
            medida = 1 / 10
        else:
            medida = 1
        m = 0.05
        if rint > 0:
            mrint = m * rint
        else:
            mrint = m * 0.5
        for componente, listainclinometros in inclinomarcados:
            nombrecomponente, idcomponente, idproy = componente
            for nombreincli, idinstru, fechas in listainclinometros:
                tipo = InclinometroModel.mdlObtenerInclinometroTipo(idproyecto, idcomponente, idinstru)
                if tipo:
                    tabla = f"inclinometro_detalle{idproyecto}"
                    fechitas = ast.literal_eval(fechas)
                    if tipo[0] == 'RST':
                        datos = InclinometroModel.mdlObtenerPAAB_RST(tabla, idcomponente, idinstru, fechitas, unidadmedida)
                    else:
                        datos = InclinometroModel.mdlObtenerPAAB_GKN(tabla, idcomponente, idinstru, fechitas, medida, mrint)
                    return datos
                else:
                    return None
    
    def ctrlObtenerPANEprofundidad(tabla, idcomponente, idinstru, fechitas, unidadmedida, azimuth, mrint, tipo):
        if unidadmedida == 1:
            medida = 1 / 1000
        elif unidadmedida == 100:
            medida = 1 / 10
        else:
            medida = 1
        alfa = 450 - azimuth
        if tipo == 'RST':
            datos = InclinometroModel.mdlObtenerPANE_RST(tabla, idcomponente, idinstru, fechitas, unidadmedida, alfa)
        else:
            datos = InclinometroModel.mdlObtenerPANE_GKN(tabla, idcomponente, idinstru, fechitas, medida, alfa, mrint)
        return datos
    
    def ctrlObtenerPANE(idproyecto, inclinomarcados, unidadmedida, azimuth, anguzz, rint):
        if unidadmedida == 1:
            medida = 1 / 1000
        elif unidadmedida == 100:
            medida = 1 / 10
        else:
            medida = 1
        alfa = 450 - azimuth
        m = 0.05
        if rint > 0:
            mrint = m * rint
        else:
            mrint = m * 0.5
        for componente, listainclinometros in inclinomarcados:
            nombrecomponente, idcomponente, idproy = componente
            for nombreincli, idinstru, fechas in listainclinometros:
                tipo = InclinometroModel.mdlObtenerInclinometroTipo(idproyecto, idcomponente, idinstru)
                if tipo:
                    tabla = f"inclinometro_detalle{idproyecto}"
                    fechitas = ast.literal_eval(fechas)
                    if tipo[0] == 'RST':
                        datos = InclinometroModel.mdlObtenerPANE_RST(tabla, idcomponente, idinstru, fechitas, unidadmedida, alfa)
                    else:
                        datos = InclinometroModel.mdlObtenerPANE_GKN(tabla, idcomponente, idinstru, fechitas, medida, alfa, mrint)
                    return datos
                else:
                    return None
                
    def ctrlObtenerCSAB(idproyecto, inclinomarcados, unidadmedida, azimuth, anguzz, rint):
        for componente, listainclinometros in inclinomarcados:
            nombrecomponente, idcomponente, idproy = componente
            for nombreincli, idinstru, fechas in listainclinometros:
                tipo = InclinometroModel.mdlObtenerInclinometroTipo(idproyecto, idcomponente, idinstru)
                if tipo:
                    tabla = f"inclinometro_detalle{idproyecto}"
                    fechitas = ast.literal_eval(fechas)
                    if tipo[0] == 'RST':
                        datos = InclinometroModel.mdlObtenerCSAB_RST(tabla, idcomponente, idinstru, fechitas, unidadmedida)
                    else:
                        datos = None
                    return datos
                else:
                    return None
    
    def ctrlListarInclinometrosNombreProyecto(proyecto):
        respuesta = InclinometroModel.mdlListarInclinometrosNombreProyecto(proyecto)
        return respuesta
    
    def ctrlRegistrarDataInclinometro(proyectoid,id_inclinometro,fecha_hora,data):
        respuesta = InclinometroModel.mdlRegistrarDataInclinometro(proyectoid,id_inclinometro,fecha_hora,data)
        return respuesta
    
    def ctrlActualizarLecturaInclinometro(tabla, datos, idproyecto, username, nombres):
        respuesta = InclinometroModel.mdlActualizarLecturaInclinometro(tabla, datos, idproyecto, username, nombres)
        return respuesta
    
    def ctrlEliminarInclinometros(idcomponente):
        respuesta = InclinometroModel.mdlEliminarInclinometros(idcomponente)
        return respuesta
    
    def ctrlEliminarDataInclinometros(idproyecto, datos):
        tabla = f"inclinometro_detalle{idproyecto}"
        inclinometros = [dato[4] for dato in datos]
        respuesta = InclinometroModel.mdlEliminarDataInclinometros(tabla, inclinometros)
        return respuesta
    
    def ctrlObtenerInfoInclinometro(idinstrumento):
        respuesta = InclinometroModel.mdlObtenerInfoInclinometro(idinstrumento)
        return respuesta
    
    def ctrlActualizarInclinometro(id_proyecto, datos):
        respueta = InclinometroModel.mdlActualizarInclinometro(id_proyecto, datos)
        return respueta
    
    def ctrlCambiarComponenteInclinometros(proyectoid, idcomponente, nuevocomponente):
        inclinometros = []
        respuesta = InclinometroModel.mdlCambiarComponenteInclinometros(idcomponente, nuevocomponente)
        if respuesta:
            for incli in respuesta:
                fechas = InterfazModel.mdlListarFechasInclinometroCodigo(incli[1], incli[0], proyectoid)
                if fechas:
                    fechitas = [fecha[0] for fecha in fechas]
                    inclinometros.append((incli[0], incli[1], incli[2], incli[3], incli[4], incli[5], incli[6], fechitas))
        return inclinometros
    
    def ctrlCambiarInclinometroComponente(idinstrumento, idcomponente):
        respuesta = InclinometroModel.mdlCambiarInclinometroComponente(idinstrumento, idcomponente)
        return respuesta
    
    def ctrlEliminarInclinometroUnico(idinstrumento):
        respuesta = InclinometroModel.mdlEliminarInclinometroUnico(idinstrumento)
        return respuesta
    
    def ctrlEliminarInclinometroData(idproyecto, dato):
        tabla = f"inclinometro_detalle{idproyecto}"
        respuesta = InclinometroModel.mdlEliminarInclinometroData(tabla, dato[4])
        return respuesta
    
    def ctrlListarFechasInclinometro(idcomponente, idinstrumento, proyectoid):
        respuesta = InclinometroModel.mdlListarFechasInclinometro(idcomponente, idinstrumento, proyectoid)
        return respuesta
    
    def ctrlCambiarBaseInclinometro(idencabezado, idinclinome):
        respueta = InclinometroModel.mdlCambiarBaseInclinometro(idencabezado, idinclinome)
        return respueta
    
    def ctrlCambiarEstadoFechasInclinometro(iddesmarcadas, idinclinometro):
        respueta = InclinometroModel.mdlCambiarEstadoFechasInclinometro(iddesmarcadas, idinclinometro)
        return respueta
    
    def ctrlEliminarLecturaInclinometro(idproyecto, idencabezado, idinclinome, username, nombres):
        tabla = f"inclinometro_detalle{idproyecto}"
        respueta = InclinometroModel.mdlEliminarLecturaInclinometro(tabla, idproyecto, idencabezado, idinclinome, username, nombres)
        return respueta
    
    def ctrlObtenerIdIinclinometro(id_intruemntacion):
        respueta = InclinometroModel.mdlObtenerIdIinclinometro(id_intruemntacion)
        return respueta
    
    #----
    def ctrlObtenerDAA_Inclinometro(idproyecto, idcomponente, unidadmedida, fecha_inicial, fecha_final):
        if unidadmedida == 1:
            medida = 1 / 1000
        elif unidadmedida == 100:
            medida = 1 / 10
        else:
            medida = 1
        resultados = []
        tipos = InclinometroModel.mdlObtener_datos_incli_reporte(idcomponente)
        if tipos:
            tabla = f"inclinometro_detalle{idproyecto}"
            # Convertir las fechas a objetos datetime para facilitar la comparación
            fecha_inicial = datetime.strptime(fecha_inicial, '%Y-%m-%d %H:%M:%S')
            fecha_final = datetime.strptime(fecha_final, '%Y-%m-%d %H:%M:%S')
            for id_inclinometro,nombre_equipo, tipo_equipo in tipos:
                if tipo_equipo == 'RST':
                    datos = InclinometroModel.mdlObtenerDAA_RST(tabla, id_inclinometro, unidadmedida)
                else:
                    datos = InclinometroModel.mdlObtenerDAA_GKN(tabla, id_inclinometro, medida)
                if datos:
                    # Filtrar datos entre las fechas dadas
                    datos_filtrados = [d for d in datos if fecha_inicial <= datetime.strptime(d[1], '%Y-%m-%d %H:%M:%S') <= fecha_final]
                    if datos_filtrados:
                        # Calcular el mayor desplazamiento
                        mayor_desplazamiento = max(datos_filtrados, key=lambda x: x[3])[3]
                    else:
                        # Si no hay datos en el rango de fechas
                        mayor_desplazamiento = "Sin Lectura"
                    # Agregar el resultado para este equipo
                    resultados.append((id_inclinometro, nombre_equipo, fecha_inicial, fecha_final, mayor_desplazamiento))
        return resultados
    
    def ctrlTraerDataInclinometro(idinclinometro):
        respuesta = InclinometroModel.mdlTraerDataInclinometro(idinclinometro)
        return respuesta
    