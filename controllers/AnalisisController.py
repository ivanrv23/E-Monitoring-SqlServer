from models.AnalisisModel import AnalisisModel
from models.DesplazamientoModel import DesplazamientoModel
from models.VelocidadModel import VelocidadModel
from utils.common.metodosGenerales import MetodosGenerales

class AnalisisController:
    
    def ctrlCalcularDatosGrafica(idproyecto, prismasmarcados, fechaini, fechafin, tipografico, filtrado, unidadmedida):
        prismastotales = []
        for componente, listaprismas in prismasmarcados:
            nombrecomponente, idcomponente, idproy = componente
            resultado = MetodosGenerales.ctrlAgruparPrismasSegunTipo(listaprismas)
            for tabla, prismas in resultado.items():
                if filtrado == 0: # sin fechas
                    method_name = "mdlCalcularVelocidad" + tipografico
                    prismasdata = getattr(AnalisisModel, method_name)(tabla, prismas, idcomponente, unidadmedida)
                else:
                    method_name = "mdlCalcularVelocidadFechas" + tipografico
                    prismasdata = getattr(AnalisisModel, method_name)(tabla, prismas, idcomponente, fechaini, fechafin, unidadmedida)
                if prismasdata:
                    prismastotales.extend(prismasdata)
        return prismastotales
    
    def ctrlListarComponentesPrismasProyecto(idproyecto):
        respuesta = AnalisisModel.mdlListarComponentesPrismasProyecto(idproyecto)
        return respuesta
    
    def ctrlObtenerNombresPrismasComponente(idcomponente):
        nombresprismas = []
        dataprismaa = AnalisisModel.mdlObtenerNombresPrismasComponente(idcomponente, "PRISMAS")
        if dataprismaa:
            nombresprismas.extend(dataprismaa)
        return nombresprismas
    
    def ctrlCalcularDatosTrayectoria(idproyecto, prismasmarcados, fechaini, fechafin, filtrado):
        prismastotales = []
        if filtrado == 0: # sin fechas
            for componente, listaprismas in prismasmarcados:
                nombrecomponente, idcomponente, idproy = componente
                resultado = MetodosGenerales.ctrlAgruparPrismasSegunTipo(listaprismas)
                for tabla, prismas in resultado.items():
                    prismasdata = AnalisisModel.mdlCalcularDatosTrayectoria(tabla, prismas, idcomponente)
                    if prismasdata:
                        prismastotales.extend(prismasdata)
        else: # con fechas
            for componente, listaprismas in prismasmarcados:
                nombrecomponente, idcomponente, idproy = componente
                resultado = MetodosGenerales.ctrlAgruparPrismasSegunTipo(listaprismas)
                for tabla, prismas in resultado.items():
                    prismasdata = AnalisisModel.mdlCalcularDatosTrayectoriaFechas(tabla, prismas, idcomponente, fechaini, fechafin)
                    if prismasdata:
                        prismastotales.extend(prismasdata)
        return prismastotales
    
    def ctrlObtenerVariacionCoordenadas(idproyecto, prismasmarcados, fechaini, fechafin, filtrado):
        prismastotales = []
        if filtrado == 0: # sin fechas
            for componente, listaprismas in prismasmarcados:
                nombrecomponente, idcomponente, idproy = componente
                resultado = MetodosGenerales.ctrlAgruparPrismasSegunTipo(listaprismas)
                for tabla, prismas in resultado.items():
                    prismasdata = AnalisisModel.mdlObtenerVariacionCoordenadas(tabla, prismas, idcomponente)
                    if prismasdata:
                        prismastotales.extend(prismasdata)
        else: # con fechas
            for componente, listaprismas in prismasmarcados:
                nombrecomponente, idcomponente, idproy = componente
                resultado = MetodosGenerales.ctrlAgruparPrismasSegunTipo(listaprismas)
                for tabla, prismas in resultado.items():
                    prismasdata = AnalisisModel.mdlObtenerVariacionCoordenadasFechas(tabla, prismas, idcomponente, fechaini, fechafin)
                    if prismasdata:
                        prismastotales.extend(prismasdata)
        return prismastotales
    
    def ctrObtenerDataEstereografia(idproyecto):
        estereografia = AnalisisModel.mdlObtenerDataEstereografia(idproyecto)
        return estereografia
    
    def ctrlDatosTrendPlunge(prismasmarcados, fechaini, fechafin, filtrado):
        prismastotales = []
        if filtrado == 0: # sin fechas
            for componente, listaprismas in prismasmarcados:
                resultado = MetodosGenerales.ctrlAgruparPrismasSegunTipo(listaprismas)
                for tabla, prismas in resultado.items():
                    prismasdata = AnalisisModel.mdlObtenerTrendPlunge(tabla, prismas)
                    if prismasdata:
                        prismastotales.extend(prismasdata)
        else: # con fechas
            for componente, listaprismas in prismasmarcados:
                resultado = MetodosGenerales.ctrlAgruparPrismasSegunTipo(listaprismas)
                for tabla, prismas in resultado.items():
                    prismasdata = AnalisisModel.mdlObtenerTrendPlungeFechas(tabla, prismas, fechaini, fechafin)
                    if prismasdata:
                        prismastotales.extend(prismasdata)
        return prismastotales
    
    def ctrlGuardarDatosEstereografia(idproyecto, datos):
        estado = False
        for fila in datos:
            nombre = fila["nombre"]
            inclinacion = fila["inclinacion"]
            direccion = fila["direccion"]
            numero = fila["numero"]
            existe  = AnalisisModel.mdlComprobarDatosEstereografia(idproyecto, numero)
            if existe:
                estado = AnalisisModel.mdlActualizarDatosEstereografia(idproyecto, nombre, inclinacion, direccion, numero)
            else:
                estado = AnalisisModel.mdlGuardarDatosEstereografia(idproyecto, nombre, inclinacion, direccion, numero)
        return estado
    
    def ctrlEliminaeDatoEstereografia(idproyecto, numero):
        respuesta = AnalisisModel.mdlEliminaeDatoEstereografia(idproyecto, numero)
        return respuesta
    
    def ctrlTraerDataHistograma(idproyecto, nombreprisma, idcomponente, tipoprisma, tipografica, fechaini, fechafin, tipofiltro, tipovelocidad):
        prismastotales = []
        unidad = 1
        prismas = [nombreprisma,]
        if tipoprisma == "PRISMAS":
            tabla = f"prismas{idproyecto}"
        else:
            tabla = f"prismas{idproyecto}"
        if tipografica.startswith('V'): # velocidad
            if tipofiltro == 0:
                method_name = 'mdlCalcularVelocidad' + tipografica
                if tipografica == "VI3D":
                    if tipovelocidad == 0:
                        method_name = 'mdlCalcularVelocidadPositiva' + tipografica
                prismasdata = getattr(VelocidadModel, method_name)(tabla, unidad, prismas, idcomponente)
                if prismasdata:
                    prismastotales.extend(prismasdata)
            else:
                method_name = 'mdlCalcularVelocidadFechas' + tipografica
                if tipografica == "VI3D":
                    if tipovelocidad == 0:
                        method_name = 'mdlCalcularVelocidadPositivaFechas' + tipografica
                prismasdata = getattr(VelocidadModel, method_name)(tabla, unidad, prismas, idcomponente, fechaini, fechafin)
                if prismasdata:
                    prismastotales.extend(prismasdata)
        else: # Desplazamiento
            if tipofiltro == 0:
                method_name = 'mdlCalcularDesplazamiento' + tipografica
                prismasdata = getattr(DesplazamientoModel, method_name)(tabla, unidad, prismas, idcomponente)
                if prismasdata:
                    prismastotales.extend(prismasdata)
            else:
                method_name = 'mdlCalcularDesplazamientoFechas' + tipografica
                prismasdata = getattr(DesplazamientoModel, method_name)(tabla, unidad, prismas, idcomponente, fechaini, fechafin)
                if prismasdata:
                    prismastotales.extend(prismasdata)
        return prismastotales
    
    def ctrlObtenerResumenPrismas(proyectoid,unidad):
        datosprisma = []
        try:
            # Automatic Prism Data
            table_auto = "prismas" + str(proyectoid)
            datosa = AnalisisModel.mdlResumenPrismas(table_auto,unidad)
            if datosa:
                datosprisma.extend(datosa)
            # Manual Prism Data
            # table_manual = "prismas" + str(proyectoid)
            # datosm = AnalisisModel.mdlResumenPrismas(table_manual,unidad)
            # if datosm:
            #     datosprisma.extend(datosm)
        except Exception as e:
            print(f"Error: {e}")
        return datosprisma
    
    def ctrlObtenerDataElipseError(idproyecto, nombreprisma, tipoprisma, fechainicial, fechafinal, filtrado):
        if tipoprisma == "PRISMAS":
            tabla = f"prismas{idproyecto}"
        else:
            tabla = f"prismas{idproyecto}"
        if filtrado == 0: # sin fechas
            elipse = AnalisisModel.mdlObtenerDataElipseError(tabla, nombreprisma)
        else: # con fechas
            elipse = AnalisisModel.mdlObtenerDataElipseErrorFechas(tabla, nombreprisma, fechainicial, fechafinal)
        return elipse
    
    def ctrlObtenerDataPrismas(idproyecto,nombreprisma,tipoprisma):
        if tipoprisma == "PRISMAS":
            tabla = f"prismas{idproyecto}"
        else:
            tabla = f"prismas{idproyecto}"
        estereografia = AnalisisModel.mdlObtenerDataPrismas(tabla,nombreprisma)
        return estereografia
    
    def ctrlObtenerDataPrismasDesviaciones(idproyecto,componente,nombreprisma,tipoprisma):
        if tipoprisma == "PRISMAS":
            tabla = f"prismas{idproyecto}"
        else:
            tabla = f"prismas{idproyecto}"
        estereografia = AnalisisModel.mdlObtenerDataPrismasDesviaciones(tabla,idproyecto,componente,nombreprisma,tipoprisma)
        return estereografia
    
    def ctrlActualizarDataLimpiaPrismas(idproyecto, datos, tipoprisma):
        if tipoprisma == "PRISMAS":
            tabla = f"prismas{idproyecto}"
        else:
            tabla = f"prismas{idproyecto}"
        respuesta = AnalisisModel.mdlActualizarDataLimpiaPrismas(tabla, datos)
        return respuesta
    
    def ctrlRestablecerDataPrismasElipse(idproyecto, nombreprisma, tipoprisma):
        if tipoprisma == "PRISMAS":
            tabla = f"prismas{idproyecto}"
        else:
            tabla = f"prismas{idproyecto}"
        respuesta = AnalisisModel.mdlRestablecerDataPrismasElipse(tabla, nombreprisma)
        return respuesta
    
    def ctrlRegistroAjusteCoordenadas(idproyecto, tabla, nombre_prisma, campo, id_prisma, current_value, nuevo_valor, fecha, username, nombres):
        respuesta = AnalisisModel.mdlRegistroAjusteCoordenadas(idproyecto, tabla, nombre_prisma, campo, id_prisma, current_value, nuevo_valor, fecha, username, nombres)
        return respuesta
    
    def ctrlVerificarSIdesviaciones(proyecto):
        respuesta = AnalisisModel.mdlVerificarSIdesviaciones(proyecto)
        return respuesta
    
    def ctrlObtenerDataDesviaciones(idproyecto, fecha_calculo):
        tabla1 = f"prismas{idproyecto}"
        tabla2 = f"prismas{idproyecto}"
        # Realizar consultas a ambas tablas
        resultado1 = AnalisisModel.mdlObtenerDataDesviacionesAuto(idproyecto,tabla1, fecha_calculo)
        resultado2 = AnalisisModel.mdlObtenerDataDesviacionesManual(idproyecto,tabla2, fecha_calculo)
        # Unir los resultados en una sola lista
        data_desviaciones = []
        if resultado1:
            data_desviaciones.extend(resultado1)
        if resultado2:
            data_desviaciones.extend(resultado2)
        return data_desviaciones
    
    def ctrlGuardarDesviaciones(proyecto,desviaciones):
        respuesta = AnalisisModel.mdlGuardarDesviaciones(proyecto,desviaciones)
        return respuesta
    
    def ctrlObtenerDesviacionesPrisma(idproyecto, nombreprisma):
        respuesta = AnalisisModel.mdlObtenerDesviacionesPrisma(idproyecto, nombreprisma)
        return respuesta
    
    def ctrlGuardarDesviacionesPrisma(proyecto,desviaciones):
        respuesta = AnalisisModel.mdlGuardarDesviacionesPrisma(proyecto,desviaciones)
        return respuesta
    
    def ctrlGuardarDesviacionesManualesPrisma(proyecto,desviaciones):
        respuesta = AnalisisModel.mdlGuardarDesviacionesManualesPrisma(proyecto,desviaciones)
        return respuesta
    
    def ctrlObtenerDataDesviacionesPrisma(idproyecto, fecha_calculo,nombreprisma):
        tabla1 = f"prismas{idproyecto}"
        tabla2 = f"prismas{idproyecto}"

        # Realizar consultas a ambas tablas
        resultado1 = AnalisisModel.mdlObtenerDataDesviacionesPrisma(idproyecto,tabla1, fecha_calculo,nombreprisma)
        resultado2 = AnalisisModel.mdlObtenerDataDesviacionesPrisma(idproyecto,tabla2, fecha_calculo,nombreprisma)

        # Unir los resultados en una sola lista
        data_desviaciones = []
        if resultado1:
            data_desviaciones.extend(resultado1)
        if resultado2:
            data_desviaciones.extend(resultado2)

        return data_desviaciones
    
    def ctrlRegistroBackup(tabla, fila_original,fecha_modificacion):
        # Mapear datos a variables separadas
        id_lectura = fila_original['id']
        fecha_equipo = fila_original['fecha'].strftime('%Y-%m-%d %H:%M:%S')
        nombre = fila_original['nombre']
        coordenada_este = fila_original['este']
        coordenada_norte = fila_original['norte']
        coordenada_cota = fila_original['elevacion']
        distancia_inclinada = fila_original['distancia']

        # Llamar al modelo para insertar los datos
        respuesta = AnalisisModel.mdlRegistroBackup(
            nombre,
            id_lectura,
            tabla,
            fecha_equipo,
            coordenada_este,
            coordenada_norte,
            coordenada_cota,
            distancia_inclinada,
            fecha_modificacion
        )
        return respuesta
    
    def ctrlRestaurarEquipo(idproyecto,nombreprisma,tipoprisma):
        respuesta,mensaje = AnalisisModel.mdlRestaurarEquipo(idproyecto,nombreprisma,tipoprisma)
        return respuesta,mensaje
    
    def ctrlRegitroUltimaLimpiezaElipse(idproyecto,componente,tipoprisma,ultima_fila):
        nombre_prisma = ultima_fila[2]
        hora_prisma = ultima_fila[1]
        respuesta = AnalisisModel.mdlRegitroUltimaLimpiezaElipse(idproyecto,componente,nombre_prisma,tipoprisma,hora_prisma)
        return respuesta
    
    def ctrlEliminarRegistroLimpiezaDesviaciones(idproyecto, nombreprisma, tipoprisma):
        respuesta = AnalisisModel.mdlEliminarRegistroLimpiezaDesviaciones(idproyecto, nombreprisma, tipoprisma)
        return respuesta
    
    def ctrlAjustarDataPrismaCoordenada(df_ajustado, tabla, idcomponente):
        respuesta, existe = AnalisisModel.mdlAjustarDataPrismaCoordenada(df_ajustado, tabla, idcomponente)
        return respuesta, existe
    
    def ctrlListarSaltosPrisma(idproyecto, nombreprisma):
        respuesta = AnalisisModel.mdlListarSaltosPrisma(idproyecto, nombreprisma)
        return respuesta
    
    def ctrlObtenerDataCoordenadaAjuste(idproyecto,nombreprisma,columna):
        tabla=f'prismas{idproyecto}'
        respuesta = AnalisisModel.mdlObtenerDataCoordenadaAjuste(tabla,nombreprisma,columna)
        return respuesta
    
    def ctrlOmitirLecturasRuido(idproyecto,ids):
        tabla=f'prismas{idproyecto}'
        respuesta = AnalisisModel.mdlOmitirLecturasRuido(tabla,ids)
        return respuesta
    
    def ctrlObtenerDataComportamiento(idproyecto, idinstrumento, tipografica, unidad, fechainicial, fechafinal):
        tabla=f'prismas{idproyecto}'
        if tipografica == "desplazamiento":
            respuesta = AnalisisModel.mdlPrismaDesplazamientosAnalisis(tabla, idinstrumento, unidad, fechainicial, fechafinal)
        else:
            respuesta = AnalisisModel.mdlPrismaVelocidadesAnalisis(tabla, idinstrumento, unidad, fechainicial, fechafinal)
        return respuesta
    
    def ctrlObtenerDataTiempoReal(idproyecto, idcomponente, equipo, tipografico, unidad):
        respuesta = None
        if equipo == "PRISMA":
            tabla = "prismas" + str(idproyecto)
            if tipografico == "3DA":
                respuesta = AnalisisModel.mdlPrismasDesplazamiento3DA(tabla, unidad, idcomponente)
            elif tipografico == "3DI":
                respuesta = AnalisisModel.mdlPrismasDesplazamiento3DI(tabla, unidad, idcomponente)
            elif tipografico == "2DA":
                respuesta = AnalisisModel.mdlPrismasDesplazamiento2DA(tabla, unidad, idcomponente)
            elif tipografico == "2DI":
                respuesta = AnalisisModel.mdlPrismasDesplazamiento2DI(tabla, unidad, idcomponente)
            elif tipografico == "SDA":
                respuesta = AnalisisModel.mdlPrismasDesplazamientoSDA(tabla, unidad, idcomponente)
            elif tipografico == "SDI":
                respuesta = AnalisisModel.mdlPrismasDesplazamientoSDI(tabla, unidad, idcomponente)
            elif tipografico == "DEA":
                respuesta = AnalisisModel.mdlPrismasDesplazamientoDEA(tabla, unidad, idcomponente)
            elif tipografico == "DEI":
                respuesta = AnalisisModel.mdlPrismasDesplazamientoDEI(tabla, unidad, idcomponente)
            elif tipografico == "DNA":
                respuesta = AnalisisModel.mdlPrismasDesplazamientoDNA(tabla, unidad, idcomponente)
            elif tipografico == "DNI":
                respuesta = AnalisisModel.mdlPrismasDesplazamientoDNI(tabla, unidad, idcomponente)
            elif tipografico == "DZA":
                respuesta = AnalisisModel.mdlPrismasDesplazamientoDZA(tabla, unidad, idcomponente)
            elif tipografico == "DZI":
                respuesta = AnalisisModel.mdlPrismasDesplazamientoDZI(tabla, unidad, idcomponente)
            elif tipografico == "VA3D":
                respuesta = AnalisisModel.mdlPrismasVelocidadVA3D(tabla, unidad, idcomponente)
            elif tipografico == "VI3D":
                respuesta = AnalisisModel.mdlPrismasVelocidadVI3D(tabla, unidad, idcomponente)
            elif tipografico == "VA2D":
                respuesta = AnalisisModel.mdlPrismasVelocidadVA2D(tabla, unidad, idcomponente)
            elif tipografico == "VI2D":
                respuesta = AnalisisModel.mdlPrismasVelocidadVI2D(tabla, unidad, idcomponente)
            elif tipografico == "VASD":
                respuesta = AnalisisModel.mdlPrismasVelocidadVASD(tabla, unidad, idcomponente)
            elif tipografico == "VISD":
                respuesta = AnalisisModel.mdlPrismasVelocidadVISD(tabla, unidad, idcomponente)
        elif equipo == "PIEZOMETROCUERDA":
            tabla = "piezometrocuerda_detalle" + str(idproyecto)
            if tipografico == "PCNF":
                respuesta = AnalisisModel.mdlPiezometrosCuerdaNivelFreatico(tabla, unidad, idcomponente)
            elif tipografico == "PCNA":
                respuesta = AnalisisModel.mdlPiezometrosCuerdaNivelAcumulado(tabla, unidad, idcomponente)
            elif tipografico == "PCNI":
                respuesta = AnalisisModel.mdlPiezometrosCuerdaNivelIncremental(tabla, unidad, idcomponente)
        elif equipo == "PIEZOMETROMANUAL":
            if tipografico == "PMNF":
                tabla = "prismas" + str(idproyecto)
                respuesta = AnalisisModel.mdlPiezometrosCasagrandeNivelFreatico(tabla, unidad, idcomponente)
            elif tipografico == "PMNA":
                tabla = "prismas" + str(idproyecto)
                respuesta = AnalisisModel.mdlPiezometrosCasagrandeNivelAcumulado(tabla, unidad, idcomponente)
            elif tipografico == "PMNI":
                tabla = "prismas" + str(idproyecto)
                respuesta = AnalisisModel.mdlPiezometrosCasagrandeNivelIncremental(tabla, unidad, idcomponente)
        elif equipo == "CELDA":
            if tipografico == "CANA":
                tabla = "prismas" + str(idproyecto)
                respuesta = AnalisisModel.mdlCeldasAsentamientoCota(tabla, unidad, idcomponente)
            elif tipografico == "CAAA":
                tabla = "prismas" + str(idproyecto)
                respuesta = AnalisisModel.mdlCeldasAsentamientoIncremental(tabla, unidad, idcomponente)
            elif tipografico == "CAAI":
                tabla = "prismas" + str(idproyecto)
                respuesta = AnalisisModel.mdlObtenerAsentamientoAcumulado(tabla, unidad, idcomponente)
        return respuesta
    