from models.PrismaModel import PrismaModel
from utils.common.metodosGenerales import MetodosGenerales

class PrismaController:
    
    def ctrlObtenerFechasRango(proyectoid):
        tabla = f"prismas{proyectoid}"
        fechasa = PrismaModel.mdlObtenerFechasMaximasPrismas(tabla)
        if fechasa:
            if fechasa[0]:
                fechamax = fechasa[0]
                fechamin = MetodosGenerales.obtenerFechasRangoUnyear(fechamax, 365)
                return fechamin, fechamax
            else:
                fechamin, fechamax = MetodosGenerales.obtenerRangoFechas(365)
                return fechamin, fechamax
        else:
            fechamin, fechamax = MetodosGenerales.obtenerRangoFechas(365)
            return fechamin, fechamax
    
    def ctrlObtenerPrismasFechaUnicos(proyecto, fechaini, fechafin):
        prismasmin = []
        tabla = f"prismas{proyecto}"
        dataprismaamin = PrismaModel.mdlListarPrismasFechaMinimaUnicos(tabla, proyecto, fechaini, fechafin, "PRISMAS")
        if dataprismaamin:
            prismasmin.extend(dataprismaamin)
        return prismasmin

    # Obtener prismas iniciales automatizados por fecha    
    def ctrlObtenerPrismasInicialesFecha(prismasmarcados, fechaini, fechafin, filtrado):
        prismasmin = []
        if filtrado == 0: # sin fechas
            for componente, listaprismas in prismasmarcados:
                marcados = MetodosGenerales.ctrlAgruparPrismasSegunTipo(listaprismas)
                idcomponente = componente[1]
                for tabla, prismas in marcados.items():
                    datosa = PrismaModel.mdlListarPrismasUnicosMinima(tabla, prismas, idcomponente)
                    if datosa is not None:
                        prismasmin.extend(datosa)
        else: # con fechas
            for componente, listaprismas in prismasmarcados:
                marcados = MetodosGenerales.ctrlAgruparPrismasSegunTipo(listaprismas)
                idcomponente = componente[1]
                for tabla, prismas in marcados.items():
                    datosa = PrismaModel.mdlListarPrismasUnicosFechaMinima(tabla, prismas, idcomponente, fechaini, fechafin)
                    if datosa is not None:
                        prismasmin.extend(datosa)
        return prismasmin
    
    # Obtener prismas finales automatizados por fecha    
    def ctrlObtenerPrismasFinalesFecha(prismasmarcados, fechaini, fechafin, filtrado):
        prismasmax = []
        if filtrado == 0: # sin fechas
            for componente, listaprismas in prismasmarcados:
                marcados = MetodosGenerales.ctrlAgruparPrismasSegunTipo(listaprismas)
                idcomponente = componente[1]
                for tabla, prismas in marcados.items():
                    datosa = PrismaModel.mdlListarPrismasUnicosMaxima(tabla, prismas, idcomponente)
                    if datosa is not None:
                        prismasmax.extend(datosa)
        else: # con fechas
            for componente, listaprismas in prismasmarcados:
                marcados = MetodosGenerales.ctrlAgruparPrismasSegunTipo(listaprismas)
                idcomponente = componente[1]
                for tabla, prismas in marcados.items():
                    datosa = PrismaModel.mdlListarPrismasUnicosFechaMaxima(tabla, prismas, idcomponente, fechaini, fechafin)
                    if datosa is not None:
                        prismasmax.extend(datosa)
        return prismasmax
    
    def ctrlObtenerDistanciaVectores3DPrisma(proyecto, prismasmarcados, fechaini, fechafin, filtrado):
        datosprisma = []
        if filtrado == 0: # sin fechas
            for componente, listaprismas in prismasmarcados:
                marcados = MetodosGenerales.ctrlAgruparPrismasSegunTipo(listaprismas)
                idcomponente = componente[1]
                for tabla, prismas in marcados.items():
                    datosa = PrismaModel.mdlCalcularVectoresDesplazamiento3DA(tabla, prismas, idcomponente)
                    if datosa is not None:
                        datosprisma.extend(datosa)
        else: # con fechas
            for componente, listaprismas in prismasmarcados:
                marcados = MetodosGenerales.ctrlAgruparPrismasSegunTipo(listaprismas)
                idcomponente = componente[1]
                for tabla, prismas in marcados.items():
                    datosa = PrismaModel.mdlCalcularVectoresDesplazamientoFechas3DA(tabla, prismas, idcomponente, fechaini, fechafin)
                    if datosa is not None:
                        datosprisma.extend(datosa)
        return datosprisma
        
    def ctrlObtenerDistanciaVectoresVI3DPrisma(proyecto, prismasmarcados, fechaini, fechafin, filtrado, tipovelocidad):
        datosprisma = []
        if filtrado == 0: # sin fechas
            for componente, listaprismas in prismasmarcados:
                marcados = MetodosGenerales.ctrlAgruparPrismasSegunTipo(listaprismas)
                idcomponente = componente[1]
                for tabla, prismas in marcados.items():
                    if tipovelocidad == 0:
                        datosa = PrismaModel.mdlCalcularVectoresVelocidadPositivaVI3D(tabla, prismas, idcomponente)
                    else:
                        datosa = PrismaModel.mdlCalcularVectoresVelocidadVI3D(tabla, prismas, idcomponente)
                    if datosa is not None:
                        datosprisma.extend(datosa)
        else: # con fechas
            for componente, listaprismas in prismasmarcados:
                marcados = MetodosGenerales.ctrlAgruparPrismasSegunTipo(listaprismas)
                idcomponente = componente[1]
                for tabla, prismas in marcados.items():
                    if tipovelocidad == 0:
                        datosa = PrismaModel.mdlCalcularVectoresVelocidadPositivaFechasVI3D(tabla, prismas, idcomponente, fechaini, fechafin)
                    else:
                        datosa = PrismaModel.mdlCalcularVectoresVelocidadFechasVI3D(tabla, prismas, idcomponente, fechaini, fechafin)
                    if datosa is not None:
                        datosprisma.extend(datosa)
        return datosprisma
    
    def ctrlCambiarEstadoLecturaPrisma(tabla, iddetalle):
        respuesta = PrismaModel.mdlCambiarEstadoLecturaPrisma(tabla, iddetalle)
        return respuesta
    
    def ctrlOmitirLecturasPrismaDesviacion(tabla, prisma, desviacioneste, desviacionnorte):
        respuesta = PrismaModel.mdlOmitirLecturasPrismaDesviacion(tabla, prisma, desviacioneste, desviacionnorte)
        return respuesta
    
    def ctrlActivarLecturasPrisma(tabla, prisma):
        respuesta = PrismaModel.mdlActivarLecturasPrisma(tabla, prisma)
        return respuesta
    
    def ctrlCambiarEstadoLecturaPrismaBloque(tabla, listaids):
        respuesta = PrismaModel.mdlCambiarEstadoLecturaPrismaBloque(tabla, listaids)
        return respuesta
    
    def ctrlEliminarLecturaPrisma(tabla, iddetalle, idproyecto, username, nombres):
        respuesta = PrismaModel.mdlEliminarLecturaPrisma(tabla, iddetalle, idproyecto, username, nombres)
        return respuesta
    
    def ctrlActualizarLecturaPrisma(tabla, datanueva, idproyecto, username, nombres):
        respuesta = PrismaModel.mdlActualizarLecturaPrisma(tabla, datanueva, idproyecto, username, nombres)
        return respuesta
    
    def ctrlEliminarLecturasBloquePrisma(tabla, iddetalles, idproyecto, username, nombres):
        respuesta = PrismaModel.mdlEliminarLecturasBloquePrisma(tabla, iddetalles, idproyecto, username, nombres)
        return respuesta
    
    def ctrlGuardarPrismasManualesTabla(proyecto, data):
        # Extraer nombres únicos de la columna 1
        nombres_unicos = set(item[0] for item in data)
        # Limpiar datos repetidos
        datos_unicos = {}
        datos_limpios = []
        for nombre, fecha, hora, norte, este, nivel, sd, ah, av in data:
            fechahora = fecha + " " + hora
            clave = (nombre, fechahora)
            if clave not in datos_unicos:
                datos_unicos[clave] = (norte, este, nivel, sd, ah, av)
                datos_limpios.append((nombre, fecha, hora, norte, este, nivel, sd, ah, av))
        # Llamar a la función
        respuesta = PrismaModel.mdlGuardarPrismasManualesTabla(proyecto, datos_limpios)
        # Devolver la respuesta y los nombres únicos
        return respuesta, list(nombres_unicos)
    
    def ctrlCambiarEstadoPrismas(estado, idcomponente):
        respuesta = PrismaModel.mdlCambiarEstadoPrismas(estado, idcomponente)
        return respuesta
    
    def ctrlEliminarPrismas(idcomponente):
        respuesta = PrismaModel.mdlEliminarPrismas(idcomponente)
        return respuesta
    
    def ctrlEliminarDataPrismas(datos):
        result = False
        grupos = {}
        for item in datos:
            nombre = item[3]
            tabla = item[5]
            if tabla not in grupos:
                grupos[tabla] = []
            grupos[tabla].append(nombre)
        for tabla, prismas in grupos.items():
            respuesta = PrismaModel.mdlEliminarDataPrismas(tabla, prismas)
            if respuesta:
                result = True
        return result
    
    def ctrlCambiarPrismaEstado(estado, idcomponente, idinstrumento):
        respuesta = PrismaModel.mdlCambiarPrismaEstado(estado, idcomponente, idinstrumento)
        return respuesta
    
    def ctrlEliminarPrismaUnico(idinstrumento):
        respuesta = PrismaModel.mdlEliminarPrismaUnico(idinstrumento)
        return respuesta
    
    def ctrlEliminarPrismaData(dato):
        respuesta = PrismaModel.mdlEliminarPrismaData(dato[5], dato[3])
        return respuesta
    
    def ctrlCambiarComponentePrismas(idcomponente, nuevocomponente):
        respuesta = PrismaModel.mdlCambiarComponentePrismas(idcomponente, nuevocomponente)
        return respuesta
    
    def ctrlCambiarPrismaComponente(idinstrumento, nuevocomponente):
        respuesta = PrismaModel.mdlCambiarPrismaComponente(idinstrumento, nuevocomponente)
        return respuesta
    
    def ctrlResumenDesplazamiento(proyectoid, fechaini, fechafin):
        resumen = []
        tabla = f"prismas{proyectoid}"
        dataauto = PrismaModel.mdlResumenDesplazamiento(tabla, fechaini, fechafin)
        if dataauto:
            resumen.extend(dataauto)
        return resumen
    
    def ctrlResumenVelocidadBuzamiento(proyectoid, fechaini, fechafin):
        velocidad = PrismaController.ctrlResumenVelocidad(proyectoid, fechaini, fechafin)
        trendplunge = PrismaController.ctrlResumenTrendPlunge(proyectoid, fechaini, fechafin)
        if velocidad and trendplunge:
            resumen = [tuple(list(velocidad[i]) + list(trendplunge[i])) for i in range(len(velocidad))]
            return resumen
        else:
            return []
    
    def ctrlResumenVelocidad(proyectoid, fechaini, fechafin):
        resumen = []
        tabla = f"prismas{proyectoid}"
        dataauto = PrismaModel.mdlResumenVelocidad(tabla, fechaini, fechafin)
        if dataauto:
            resumen.extend(dataauto)
        return resumen
    
    def ctrlResumenTrendPlunge(proyectoid, fechaini, fechafin):
        resumen = []
        tabla = f"prismas{proyectoid}"
        dataauto = PrismaModel.mdlResumenTrendPlunge(tabla, fechaini, fechafin)
        if dataauto:
            resumen.extend(dataauto)
        return resumen
    
    def ctrlDatosPrismasDesviaciones(proyectoid, tipoprisma, prisma):
        if tipoprisma == "PRISMAS":
            tabla = f"prismas{proyectoid}"
        else:
            tabla = f"prismas{proyectoid}"
        respuesta = PrismaModel.mdlDatosPrismasDesviaciones(tabla, tipoprisma, prisma)
        return respuesta
    
    def ctrlObtenerDesviacionStandar(idproyecto, nombreprisma):
        respuesta = PrismaModel.mdlObtenerDesviacionStandar(idproyecto, nombreprisma)
        return respuesta
    
    def ctrlOmitirLecturaPrisma(proyecto,prisma,fecha,tipo):
        if tipo == 'PRISMAS':
            tabla = f'prismas{proyecto}'
        else:
            tabla = f'prismas{proyecto}'
        respuesta = PrismaModel.mdlOmitirLecturaPrisma(tabla, prisma, fecha)
        return respuesta
    
    def ctrlVerificarPrismaUnico(nameprisma, idinstrumento, idproyecto):
        respuesta = PrismaModel.mdlVerificarPrismaUnico(nameprisma, idinstrumento, idproyecto)
        return respuesta
    
    def ctrlActualizarNombrePrisma(nameprisma, nuevoprisma, idinstrumento, idproyecto):
        respuesta = PrismaModel.mdlActualizarNombrePrisma(nameprisma, nuevoprisma, idinstrumento, idproyecto)
        return respuesta
    