import ast
# Importamos el módulo completo con un alias para usarlo en 'eval'
import datetime as dt_module 
from datetime import datetime
from models.InclinometroModel import InclinometroModel
from models.InterfazModel import InterfazModel

class InclinometroController:
    
    # --- FUNCIÓN CORREGIDA PARA FECHAS ---
    @staticmethod
    def procesar_lista_fechas(fechas_raw):
        if not fechas_raw:
            return []
        
        if "datetime.datetime" in fechas_raw:
            try:
                # CORRECCIÓN: Pasamos el módulo 'datetime' (dt_module) al contexto de eval
                lista_objetos = eval(fechas_raw, {"datetime": dt_module})
                
                lista_strings = []
                for dt in lista_objetos:
                    if isinstance(dt, datetime):
                        lista_strings.append(dt.strftime('%Y-%m-%d %H:%M:%S'))
                    else:
                        lista_strings.append(str(dt))
                return lista_strings
            except Exception as e:
                print(f"Error procesando fechas SQL Server: {e}")
                return []

        try:
            return ast.literal_eval(fechas_raw)
        except:
            return []

    # --- FUNCIÓN MEJORADA: Convertir Decimal a Float (Incluyendo Profundidad) ---
    @staticmethod
    def convertir_decimal_a_float(datos):
        """
        Convierte los valores numéricos (Profundidad, Desp A, Desp B) de Decimal a Float.
        Esto es OBLIGATORIO para que matplotlib no falle.
        """
        if not datos:
            return None
        
        datos_float = []
        for fila in datos:
            item = list(fila)
            
            # 1. Convertir Profundidad (Índice 2) - ESTO FALTABA
            if len(item) >= 3:
                if item[2] is not None: item[2] = float(item[2])
                else: item[2] = 0.0

            # 2. Convertir Desplazamientos (Índices 3 y 4)
            if len(item) >= 5:
                if item[3] is not None: item[3] = float(item[3])
                else: item[3] = 0.0
                
                if item[4] is not None: item[4] = float(item[4])
                else: item[4] = 0.0
            
            datos_float.append(tuple(item))
        return datos_float
    # -----------------------------------------------

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
        
        return InclinometroController.convertir_decimal_a_float(datos)
    
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
                    fechitas = InclinometroController.procesar_lista_fechas(fechas)
                    
                    if not fechitas: return None

                    if tipo[0] == 'RST':
                        datos = InclinometroModel.mdlObtenerDIAB_RST(tabla, idcomponente, idinstru, fechitas, unidadmedida)
                    else:
                        datos = InclinometroModel.mdlObtenerDIAB_GKN(tabla, idcomponente, idinstru, fechitas, medida, anguzz, mrint)
                    
                    return InclinometroController.convertir_decimal_a_float(datos)
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
        
        return InclinometroController.convertir_decimal_a_float(datos)
    
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
                    fechitas = InclinometroController.procesar_lista_fechas(fechas)
                    
                    if not fechitas: return None

                    if tipo[0] == 'RST':
                        datos = InclinometroModel.mdlObtenerDINE_RST(tabla, idcomponente, idinstru, fechitas, unidadmedida, alfa)
                    else:
                        datos = InclinometroModel.mdlObtenerDINE_GKN(tabla, idcomponente, idinstru, fechitas, medida, alfa, mrint)
                    
                    return InclinometroController.convertir_decimal_a_float(datos)
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
        
        return InclinometroController.convertir_decimal_a_float(datos)
    
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
                    fechitas = InclinometroController.procesar_lista_fechas(fechas)
                    
                    if not fechitas: return None

                    if tipo[0] == 'RST':
                        datos = InclinometroModel.mdlObtenerDAAB_RST(tabla, idcomponente, idinstru, fechitas, unidadmedida)
                    else:
                        datos = InclinometroModel.mdlObtenerDAAB_GKN(tabla, idcomponente, idinstru, fechitas, medida)
                    
                    return InclinometroController.convertir_decimal_a_float(datos)
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
        
        return InclinometroController.convertir_decimal_a_float(datos)
    
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
                    fechitas = InclinometroController.procesar_lista_fechas(fechas)
                    
                    if not fechitas: return None

                    if tipo[0] == 'RST':
                        datos = InclinometroModel.mdlObtenerDANE_RST(tabla, idcomponente, idinstru, fechitas, unidadmedida, alfa)
                    else:
                        datos = InclinometroModel.mdlObtenerDANE_GKN(tabla, idcomponente, idinstru, fechitas, medida, alfa, mrint, anguzz)
                    
                    return InclinometroController.convertir_decimal_a_float(datos)
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
                # Convertir Decimal a float si aplica (Profundidad, dac, dax)
                val_prof = float(profundidad) if profundidad is not None else 0.0
                val_dac = float(dac) if dac is not None else 0.0
                val_dax = float(dax) if dax is not None else 0.0
                
                datos_tupla = (nombre, val_prof, val_dac, val_dax)
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
        
        return InclinometroController.convertir_decimal_a_float(datos)
    
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
                    fechitas = InclinometroController.procesar_lista_fechas(fechas)
                    
                    if not fechitas: return None

                    if tipo[0] == 'RST':
                        datos = InclinometroModel.mdlObtenerPAAB_RST(tabla, idcomponente, idinstru, fechitas, unidadmedida)
                    else:
                        datos = InclinometroModel.mdlObtenerPAAB_GKN(tabla, idcomponente, idinstru, fechitas, medida, mrint)
                    
                    return InclinometroController.convertir_decimal_a_float(datos)
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
        
        return InclinometroController.convertir_decimal_a_float(datos)
    
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
                    fechitas = InclinometroController.procesar_lista_fechas(fechas)
                    
                    if not fechitas: return None

                    if tipo[0] == 'RST':
                        datos = InclinometroModel.mdlObtenerPANE_RST(tabla, idcomponente, idinstru, fechitas, unidadmedida, alfa)
                    else:
                        datos = InclinometroModel.mdlObtenerPANE_GKN(tabla, idcomponente, idinstru, fechitas, medida, alfa, mrint)
                    
                    return InclinometroController.convertir_decimal_a_float(datos)
                else:
                    return None
                
    def ctrlObtenerCSAB(idproyecto, inclinomarcados, unidadmedida, azimuth, anguzz, rint):
        for componente, listainclinometros in inclinomarcados:
            nombrecomponente, idcomponente, idproy = componente
            for nombreincli, idinstru, fechas in listainclinometros:
                tipo = InclinometroModel.mdlObtenerInclinometroTipo(idproyecto, idcomponente, idinstru)
                if tipo:
                    tabla = f"inclinometro_detalle{idproyecto}"
                    fechitas = InclinometroController.procesar_lista_fechas(fechas)
                    
                    if not fechitas: return None

                    if tipo[0] == 'RST':
                        datos = InclinometroModel.mdlObtenerCSAB_RST(tabla, idcomponente, idinstru, fechitas, unidadmedida)
                    else:
                        datos = None
                    
                    return InclinometroController.convertir_decimal_a_float(datos)
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
            if isinstance(fecha_inicial, str):
                fecha_inicial = datetime.strptime(fecha_inicial, '%Y-%m-%d %H:%M:%S')
            if isinstance(fecha_final, str):
                fecha_final = datetime.strptime(fecha_final, '%Y-%m-%d %H:%M:%S')
                
            for id_inclinometro,nombre_equipo, tipo_equipo in tipos:
                if tipo_equipo == 'RST':
                    datos = InclinometroModel.mdlObtenerDAA_RST(tabla, id_inclinometro, unidadmedida)
                else:
                    datos = InclinometroModel.mdlObtenerDAA_GKN(tabla, id_inclinometro, medida)
                
                # Convertir Decimal a float para cálculos en Python si es necesario
                if datos:
                    # Como convertir_decimal_a_float asume 5 cols y aca pueden ser 4, hacemos manual para asegurar:
                    datos_limpios = []
                    for d in datos:
                        val = float(d[3]) if d[3] is not None else 0.0
                        datos_limpios.append((d[0], d[1], d[2], val))
                    
                    # Filtrar datos entre las fechas dadas
                    datos_filtrados = [d for d in datos_limpios if fecha_inicial <= datetime.strptime(str(d[1]), '%Y-%m-%d %H:%M:%S') <= fecha_final]
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