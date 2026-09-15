from models.UmbralModel import UmbralModel
from models.PrismaModel import PrismaModel

class UmbralController:

    def ctrlGuardarUmbralesEquipos(proyectoid, componente_id, tipografica, data, tipoequipo):
        for item in data:
            umbral_id = item['id']
            if umbral_id is None or umbral_id == 0:
                success = UmbralModel.mdlGuardarUmbralesEquipos(proyectoid, componente_id, tipografica, [item], tipoequipo)
            else:
                success = UmbralModel.mdlActualizarUmbralEquipos(umbral_id, item['condicion'], item['color'], item['riesgo'], item['rango'], item['acciones'])
            if not success:
                return False
        return True

    def ctrlGuardarUmbralesPersonalizados(proyectoid, equipo_id, tipografica, data, tipoequipo):
        for item in data:
            umbral_id = item['id']
            if umbral_id is None or umbral_id == 0:
                success = UmbralModel.mdlGuardarUmbralesPersonalizados(proyectoid, equipo_id, tipografica, [item], tipoequipo)
            else:
                success = UmbralModel.mdlActualizarUmbralPersonalizados(umbral_id, item['condicion'], item['color'], item['riesgo'], item['rango'], item['acciones'])
            if not success:
                return False
        return True
    
    def ctrlGuardarUmbralesPiezometros(proyectoid, idpiezometro, tipo, data, tipopiezo, tabla):
        for item in data:
            umbral_id = item['id']
            if umbral_id is None or umbral_id == 0:
                success = UmbralModel.mdlGuardarUmbralesPiezometros(proyectoid, idpiezometro, tipo, [item], tipopiezo)
            else:
                success = UmbralModel.mdlActualizarUmbralEquipos(umbral_id, item['condicion'], item['color'], item['riesgo'], item['rango'], item['acciones'], tipo, tabla)
            if not success:
                return False
        return True
    
    def ctrlGuardarUmbralesAcelerografos(proyectoid, componente_id, tipografica, data, tipoequipo):
        for item in data:
            umbral_id = item['id']
            if umbral_id is None or umbral_id == 0:
                success = UmbralModel.mdlGuardarUmbralesGeneralesAcelerografos(proyectoid, componente_id, tipografica, [item], tipoequipo)
            else:
                success = UmbralModel.mdlActualizarUmbralAcelerografo(umbral_id, item['nombre'], item['riesgo'], item['color'], item['distancia'], item['magnitud'], item['acciones'])
            if not success:
                return False
        return True

    def ctrlGuardarUmbralesPersonalizadosAcelerografos(proyectoid, equipo_id, tipografica, data, tipoequipo):
        for item in data:
            umbral_id = item['id']
            if umbral_id is None or umbral_id == 0:
                success = UmbralModel.mdlGuardarUmbralesPersonalizadosAcelerografos(proyectoid, equipo_id, tipografica, [item], tipoequipo)
            else:
                success = UmbralModel.mdlActualizarUmbralPersonalizadoAcelerografo(umbral_id, item['nombre'], item['riesgo'], item['color'], item['distancia'], item['magnitud'], item['acciones'])
            if not success:
                return False
        return True

    def ctrlObtenerUmbralesAjustes(proyectoid, componete_id, tipografica, tipoequipo):
        umbral = UmbralModel.mdlObtenerUmbralesAjustes(proyectoid, componete_id, tipografica, tipoequipo)
        return umbral

    def ctrlObtenerUmbralesPersonalizados(idequipo, tipografica, tipoequipo):
        umbral = UmbralModel.mdlObtenerUmbralesPersonalizados(idequipo, tipografica, tipoequipo)
        return umbral
    
    def ctrlObtenerUmbralesInstrumentacion(proyectoid, componente_id, tipografica, tipoequipo):
        umbral = UmbralModel.mdlObtenerUmbralesInstrumentacion(proyectoid, componente_id, tipografica, tipoequipo)
        return umbral
    
    def ctrlObtenerPiezometroUmbrales(idpiezo, tipo, tipopiezo):
        umbral = UmbralModel.mdlObtenerPiezometroUmbrales(idpiezo, tipo, tipopiezo)
        return umbral
    
    def ctrlObtenerUmbralesAcelerografo(proyectoid, componete_id, tipo):
        umbral = UmbralModel.mdlObtenerUmbralesAcelerografo(proyectoid, componete_id, tipo)
        return umbral
    
    def ctrlValidarUmbralesComponentes(idproyecto, tipo, tabla):
        umbral = UmbralModel.mdlValidarUmbralesComponentes(idproyecto, tipo, tabla)
        return umbral
    
    def ctrlObtenerUmbralesCodigoPiezometro(idpiezometro, tipo, tipopiezo):
        umbral = UmbralModel.mdlObtenerUmbralesCodigoPiezometro(idpiezometro, tipo, tipopiezo)
        return umbral
    
    def ctrlValidarUmbralesPiezometros(idproyecto, tipo, tipopiezo):
        umbral = UmbralModel.mdlValidarUmbralesPiezometros(idproyecto, tipo, tipopiezo)
        return umbral
    
    def ctrlListarPiezometrosUmbrales(idproyecto, tipo, tipopiezo, tabla):
        piezometros = UmbralModel.mdlListarPiezometrosUmbrales(idproyecto, tipo, tipopiezo, tabla)
        return piezometros
    
    def ctrlValidarUmbralesCeldas(idproyecto, tipo):
        umbral = UmbralModel.mdlValidarUmbralesCeldas(idproyecto, tipo)
        return umbral
    
    def ctrlListarCeldasUmbrales(idproyecto, tipo):
        celdas = UmbralModel.mdlListarCeldasUmbrales(idproyecto, tipo)
        return celdas
    
    def ctrlListarComponentesUmbrales(idproyecto, tipo, tabla):
        componen = UmbralModel.mdlListarComponentesUmbrales(idproyecto, tipo, tabla)
        return componen
    
    def ctrlComponentesTipo(ids):
        umbral = UmbralModel.mdlComponentesTipo(ids)
        return umbral
    
    def ctrlPiezometroID(ids,tipos):
        umbral = UmbralModel.mdlPiezometroID(ids,tipos)
        return umbral
    
    def ctrlEliminarUmbralEquipos(umbral_id):
        umbral = UmbralModel.mdlEliminarUmbralEquipos(umbral_id)
        return umbral

    def ctrlEliminarUmbralPersonalizados(umbral_id):
        umbral = UmbralModel.mdlEliminarUmbralPersonalizados(umbral_id)
        return umbral
    #####
    def ctrlEliminarUmbralAcelerografo(umbral_id):
        umbral = UmbralModel.mdlEliminarUmbralAcelerografo(umbral_id)
        return umbral
    
    def ctrlGuardarUmbralPrismas(datosSD, datos3D):
        umbral = UmbralModel.mdlGuardarUmbralPrismas(datosSD)
        umbral = UmbralModel.mdlGuardarUmbralPrismas(datos3D)
        return umbral
    
    def ctrlActualizarUmbralPrismas(datosSD, datos3D):
        umbral = UmbralModel.mdlActualizarUmbralPrismas(datosSD)
        umbral = UmbralModel.mdlActualizarUmbralPrismas(datos3D)
        return umbral
    
    # listar datos de umbral m1
    def ctrObtenerUmbralPrismas(proyectoid, idcomponente, tipo):
        umbral = UmbralModel.mdlObtenerUmbralPrismas(proyectoid, idcomponente, tipo)
        return umbral
    
    def ctrlObtenerUmbralCeldas(proyectoid):
        umbral = UmbralModel.mdlObtenerUmbralCeldas(proyectoid)
        return umbral

    def ctrlObtenerUmbralCodigoCeldas(idumbral):
        umbral = UmbralModel.mdlObtenerUmbralCodigoCeldas(idumbral)
        return umbral
    
    def ctrlGuardarUmbralCeldas(datos):
        respuesta = UmbralModel.mdlGuardarUmbralCeldas(datos)
        return respuesta
    
    def ctrlActualizarUmbralCelda(datos):
        respuesta = UmbralModel.mdlActualizarUmbralCelda(datos)
        return respuesta
    
    def ctrlObtenerUmbralAcelerografos(proyectoid,componente):
        umbral = UmbralModel.mdlObtenerUmbralAcelerografos(proyectoid,componente)
        return umbral
    
    def ctrlGuardarUmbralAcelerografo(datos):
        estado = False
        for fila in datos:
            id_proyecto=fila["id_proyecto"]
            nombre=fila["name"]
            color=fila["color"]
            valor=fila["valor"]
            umbral = UmbralModel.mdlGuardarUmbralAcelerografo(id_proyecto, nombre, color, valor)
            if umbral:
                estado = True
            else:
                estado = False
        return estado
    
    #OBTENER LISTA DE PRISMAS
    def ctrListarPrismas(id_proyecto):
        lista_prismas_min = PrismaModel.mdlListarPrismasProyecto(id_proyecto)
        lista_prismas_max = PrismaModel.mdlListarPrismasFinalesProyecto(id_proyecto)
        return lista_prismas_min, lista_prismas_max
    
    #obtener penultimo valor
    def crtObtenerPenultimoDato(id_proyecto):
        penultimo_valor = UmbralModel.mdlObtenerPenultimoDato(id_proyecto)
        return penultimo_valor
    
    def crtObtenerSD(id_proyecto,fechaMinInicial,fechaMaxInicial, prismastotales, prismasmarcados):
        sdGeneral = []
        if len(prismastotales) == len(prismasmarcados):
            sdAuto = UmbralModel.mldObtenerSD(id_proyecto,fechaMinInicial,fechaMaxInicial)
            sdManual = UmbralModel.mldObtenerSDManual(id_proyecto,fechaMinInicial,fechaMaxInicial)
            if sdAuto is not None:
                sdGeneral.extend(sdAuto)
            if sdManual is not None:
                sdGeneral.extend(sdManual)
        else:
            sdGeneral = UmbralController.crtlObtenerSDResumenMonitor1(id_proyecto, prismasmarcados, fechaMinInicial, fechaMaxInicial)
        return sdGeneral
    
    # obtener datos resumen sd de lecturas por prisma segun nombre y fechas
    # def crtlObtenerSDResumenMonitor1(proyecto, marcados, fechaini, fechafin):
    #     datosprisma = []
    #     for code, fila, id in marcados:
    #         if code == "Automatizado":
    #             existe = PrismaModel.mdlComprobarPrismaResumenFechas(proyecto, 1, fila, fechaini, fechafin)
    #             if existe:
    #                 datosa = UmbralModel.mldObtenerSDPrismaNombre(proyecto, fila, fechaini, fechafin)
    #                 if datosa is not None:
    #                     datosprisma.append(datosa)
    #         else:
    #             existe = PrismaModel.mdlComprobarPrismaResumenFechas(proyecto, 2, fila, fechaini, fechafin)
    #             if existe:
    #                 datosm = UmbralModel.mldObtenerSDPrismaNombreManual(proyecto, fila, fechaini, fechafin)
    #                 if datosm is not None:
    #                     datosprisma.append(datosm)
    #     return datosprisma
    
    def crtlObtenerSDResumenMonitor1(proyecto, marcados, fechaini, fechafin):
        datosprisma = []
        nombres_auto = [nombre for tipo, nombre, _ in marcados if tipo == "Automatizado"]
        nombres_manual = [nombre for tipo, nombre, _ in marcados if tipo != "Automatizado"]
        # return datosprisma
        if nombres_auto:
            datosa = UmbralModel.mldObtenerSDPrismaNombre(proyecto, nombres_auto, fechaini, fechafin)
            if datosa is not None:
                datosprisma.extend(datosa)

        if nombres_manual:
            datosm = UmbralModel.mldObtenerSDPrismaNombreManual(proyecto, nombres_manual, fechaini, fechafin)
            if datosm is not None:
                datosprisma.extend(datosm)
        return datosprisma

    
    def crtObtener3D(id_proyecto,fechaMinInicial,fechaMaxInicial, prismastotales, prismasmarcados):
        tresDGeneral = []
        if len(prismastotales) == len(prismasmarcados):
            tresDAuto = UmbralModel.mldObtener3D(id_proyecto,fechaMinInicial,fechaMaxInicial)
            tresDManual = UmbralModel.mldObtener3DManual(id_proyecto,fechaMinInicial,fechaMaxInicial)
            if tresDAuto is not None:
                tresDGeneral.extend(tresDAuto)
            if tresDManual is not None:
                tresDGeneral.extend(tresDManual)
        else:
            tresDGeneral = UmbralController.crtlObtener3DResumenMonitor1(id_proyecto, prismasmarcados, fechaMinInicial,fechaMaxInicial)
        return tresDGeneral
    
    # obtener datos resumen 3d de lecturas por prisma segun nombre y fechas
    # def crtlObtener3DResumenMonitor1(proyecto, marcados, fechaini, fechafin):
    #     datosprisma = []
    #     for code, fila, id in marcados:
    #         if code == "Automatizado":
    #             existe = PrismaModel.mdlComprobarPrismaResumenFechas(proyecto, 1, fila, fechaini, fechafin)
    #             if existe:
    #                 datosa = UmbralModel.mldObtener3DPrismaNombre(proyecto, fila, fechaini, fechafin)
    #                 if datosa is not None:
    #                     datosprisma.append(datosa)
    #         else:
    #             existe = PrismaModel.mdlComprobarPrismaResumenFechas(proyecto, 2, fila, fechaini, fechafin)
    #             if existe:
    #                 datosm = UmbralModel.mldObtener3DPrismaNombreManual(proyecto, fila, fechaini, fechafin)
    #                 if datosm is not None:
    #                     datosprisma.append(datosm)
    #     return datosprisma
    
    def crtlObtener3DResumenMonitor1(proyecto, marcados, fechaini, fechafin):
        datosprisma = []
        nombres_auto = [nombre for tipo, nombre, _ in marcados if tipo == "Automatizado"]
        nombres_manual = [nombre for tipo, nombre, _ in marcados if tipo != "Automatizado"]
        # return datosprisma
        if nombres_auto:
            datosa = UmbralModel.mldObtener3DPrismaNombre(proyecto, nombres_auto, fechaini, fechafin)
            if datosa is not None:
                datosprisma.extend(datosa)

        if nombres_manual:
            datosm = UmbralModel.mldObtener3DPrismaNombreManual(proyecto, nombres_manual, fechaini, fechafin)
            if datosm is not None:
                datosprisma.extend(datosm)
        return datosprisma
        
    def crtObtenerL(id_proyecto,fechaMinInicial,fechaMaxInicial, prismastotales, prismasmarcados):
        generalL = []
        if len(prismastotales) == len(prismasmarcados):
            lAuto = UmbralModel.mldObtenerL(id_proyecto,fechaMinInicial,fechaMaxInicial)
            lManual = UmbralModel.mldObtenerLManual(id_proyecto,fechaMinInicial,fechaMaxInicial)
            if lAuto is not None:
                generalL.extend(lAuto)
            if lManual is not None:
                generalL.extend(lManual)
        else:
            generalL = UmbralController.crtlObtenerLResumenMonitor1(id_proyecto,prismasmarcados, fechaMinInicial,fechaMaxInicial)
        return generalL
    
    # obtener datos resumen L de lecturas por prisma segun nombre y fechas
    # def crtlObtenerLResumenMonitor1(proyecto, marcados, fechaini, fechafin):
    #     datosprisma = []
    #     for code, fila, id in marcados:
    #         if code == "Automatizado":
    #             existe = PrismaModel.mdlComprobarPrismaResumenFechas(proyecto, 1, fila, fechaini, fechafin)
    #             if existe:
    #                 datosa = UmbralModel.mldObtenerLPrismaNombre(proyecto, fila, fechaini, fechafin)
    #                 if datosa is not None:
    #                     datosprisma.append(datosa)
    #         else:
    #             existe = PrismaModel.mdlComprobarPrismaResumenFechas(proyecto, 2, fila, fechaini, fechafin)
    #             if existe:
    #                 datosm = UmbralModel.mldObtenerLPrismaNombreManual(proyecto, fila, fechaini, fechafin)
    #                 if datosm is not None:
    #                     datosprisma.append(datosm)
    #     return datosprisma
    
    def crtlObtenerLResumenMonitor1(proyecto, marcados, fechaini, fechafin):
        datosprisma = []
        nombres_auto = [nombre for tipo, nombre, _ in marcados if tipo == "Automatizado"]
        nombres_manual = [nombre for tipo, nombre, _ in marcados if tipo != "Automatizado"]
        # return datosprisma
        if nombres_auto:
            datosa = UmbralModel.mldObtenerLPrismaNombre(proyecto, nombres_auto, fechaini, fechafin)
            if datosa is not None:
                datosprisma.extend(datosa)

        if nombres_manual:
            datosm = UmbralModel.mldObtenerLPrismaNombreManual(proyecto, nombres_manual, fechaini, fechafin)
            if datosm is not None:
                datosprisma.extend(datosm)
        return datosprisma
    
    def crtObtenerT(id_proyecto,fechaMinInicial,fechaMaxInicial, prismastotales, prismasmarcados):
        generalT = []
        if len(prismastotales) == len(prismasmarcados):
            generalTAuto = UmbralModel.mldObtenerT(id_proyecto,fechaMinInicial,fechaMaxInicial)
            generalTManual = UmbralModel.mldObtenerTManual(id_proyecto,fechaMinInicial,fechaMaxInicial)
            if generalTAuto is not None:
                generalT.extend(generalTAuto)
            if generalTManual is not None:
                generalT.extend(generalTManual)
        else:
            generalT = UmbralController.crtlObtenerTResumenMonitor1(id_proyecto, prismasmarcados, fechaMinInicial, fechaMaxInicial)
        return generalT
    
    
    # obtener datos resumen T de lecturas por prisma segun nombre y fechas
    # def crtlObtenerTResumenMonitor1(proyecto, marcados, fechaini, fechafin):
    #     datosprisma = []
    #     for code, fila, id in marcados:
    #         if code == "Automatizado":
    #             existe = PrismaModel.mdlComprobarPrismaResumenFechas(proyecto, 1, fila, fechaini, fechafin)
    #             if existe:
    #                 datosa = UmbralModel.mldObtenerTPrismaNombre(proyecto, fila, fechaini, fechafin)
    #                 if datosa is not None:
    #                     datosprisma.append(datosa)
    #         else:
    #             existe = PrismaModel.mdlComprobarPrismaResumenFechas(proyecto, 2, fila, fechaini, fechafin)
    #             if existe:
    #                 datosm = UmbralModel.mldObtenerTPrismaNombreManual(proyecto, fila, fechaini, fechafin)
    #                 if datosm is not None:
    #                     datosprisma.append(datosm)
    #     return datosprisma
    
    def crtlObtenerTResumenMonitor1(proyecto, marcados, fechaini, fechafin):
        datosprisma = []
        nombres_auto = [nombre for tipo, nombre, _ in marcados if tipo == "Automatizado"]
        nombres_manual = [nombre for tipo, nombre, _ in marcados if tipo != "Automatizado"]
        # return datosprisma
        if nombres_auto:
            datosa = UmbralModel.mldObtenerTPrismaNombre(proyecto, nombres_auto, fechaini, fechafin)
            if datosa is not None:
                datosprisma.extend(datosa)

        if nombres_manual:
            datosm = UmbralModel.mldObtenerTPrismaNombreManual(proyecto, nombres_manual, fechaini, fechafin)
            if datosm is not None:
                datosprisma.extend(datosm)
        return datosprisma

    def crtObtenerH(id_proyecto,fechaMinInicial,fechaMaxInicial, prismastotales, prismasmarcados):
        generalH = []
        if len(prismastotales) == len(prismasmarcados):
            generalHAuto = UmbralModel.mldObtenerH(id_proyecto,fechaMinInicial,fechaMaxInicial)
            generalHManual = UmbralModel.mldObtenerHManual(id_proyecto,fechaMinInicial,fechaMaxInicial)
            if generalHAuto is not None:
                generalH.extend(generalHAuto)
            if generalHManual is not None:
                generalH.extend(generalHManual)
        else:
            generalH = UmbralController.crtlObtenerHResumenMonitor1(id_proyecto, prismasmarcados, fechaMinInicial, fechaMaxInicial)
        return generalH
    
    # obtener datos resumen H de lecturas por prisma segun nombre y fechas
    # def crtlObtenerHResumenMonitor1(proyecto, marcados, fechaini, fechafin):
    #     datosprisma = []
    #     for code, fila, id in marcados:
    #         if code == "Automatizado":
    #             existe = PrismaModel.mdlComprobarPrismaResumenFechas(proyecto, 1, fila, fechaini, fechafin)
    #             if existe:
    #                 datosa = UmbralModel.mldObtenerHPrismaNombre(proyecto, fila, fechaini, fechafin)
    #                 if datosa is not None:
    #                     datosprisma.append(datosa)
    #         else:
    #             existe = PrismaModel.mdlComprobarPrismaResumenFechas(proyecto, 2, fila, fechaini, fechafin)
    #             if existe:
    #                 datosm = UmbralModel.mldObtenerHPrismaNombreManual(proyecto, fila, fechaini, fechafin)
    #                 if datosm is not None:
    #                     datosprisma.append(datosm)
    #     return datosprisma
    
    def crtlObtenerHResumenMonitor1(proyecto, marcados, fechaini, fechafin):
        datosprisma = []
        nombres_auto = [nombre for tipo, nombre, _ in marcados if tipo == "Automatizado"]
        nombres_manual = [nombre for tipo, nombre, _ in marcados if tipo != "Automatizado"]
        # return datosprisma
        if nombres_auto:
            datosa = UmbralModel.mldObtenerHPrismaNombre(proyecto, nombres_auto, fechaini, fechafin)
            if datosa is not None:
                datosprisma.extend(datosa)

        if nombres_manual:
            datosm = UmbralModel.mldObtenerHPrismaNombreManual(proyecto, nombres_manual, fechaini, fechafin)
            if datosm is not None:
                datosprisma.extend(datosm)
        return datosprisma
    
    def crtObtenerN(id_proyecto,fechaMinInicial,fechaMaxInicial, prismastotales, prismasmarcados):
        generalN = []
        if len(prismastotales) == len(prismasmarcados):
            generalNAuto = UmbralModel.mldObtenerN(id_proyecto,fechaMinInicial,fechaMaxInicial)
            generalNManual = UmbralModel.mldObtenerNManual(id_proyecto,fechaMinInicial,fechaMaxInicial)
            if generalNAuto is not None:
                generalN.extend(generalNAuto)
            if generalNManual is not None:
                generalN.extend(generalNManual)
        else:
            generalN = UmbralController.crtlObtenerNResumenMonitor1(id_proyecto, prismasmarcados, fechaMinInicial, fechaMaxInicial)
        return generalN
    
    # obtener datos resumen N de lecturas por prisma segun nombre y fechas
    # def crtlObtenerNResumenMonitor1(proyecto, marcados, fechaini, fechafin):
    #     datosprisma = []
    #     for code, fila, id in marcados:
    #         if code == "Automatizado":
    #             existe = PrismaModel.mdlComprobarPrismaResumenFechas(proyecto, 1, fila, fechaini, fechafin)
    #             if existe:
    #                 datosa = UmbralModel.mldObtenerNPrismaNombre(proyecto, fila, fechaini, fechafin)
    #                 if datosa is not None:
    #                     datosprisma.append(datosa)
    #         else:
    #             existe = PrismaModel.mdlComprobarPrismaResumenFechas(proyecto, 2, fila, fechaini, fechafin)
    #             if existe:
    #                 datosm = UmbralModel.mldObtenerNPrismaNombreManual(proyecto, fila, fechaini, fechafin)
    #                 if datosm is not None:
    #                     datosprisma.append(datosm)
    #     return datosprisma
    
    def crtlObtenerNResumenMonitor1(proyecto, marcados, fechaini, fechafin):
        datosprisma = []
        nombres_auto = [nombre for tipo, nombre, _ in marcados if tipo == "Automatizado"]
        nombres_manual = [nombre for tipo, nombre, _ in marcados if tipo != "Automatizado"]
        # return datosprisma
        if nombres_auto:
            datosa = UmbralModel.mldObtenerNPrismaNombre(proyecto, nombres_auto, fechaini, fechafin)
            if datosa is not None:
                datosprisma.extend(datosa)

        if nombres_manual:
            datosm = UmbralModel.mldObtenerNPrismaNombreManual(proyecto, nombres_manual, fechaini, fechafin)
            if datosm is not None:
                datosprisma.extend(datosm)
        return datosprisma
    
    def crtObtenerE(id_proyecto,fechaMinInicial,fechaMaxInicial, prismastotales, prismasmarcados):
        generalE = []
        if len(prismastotales) == len(prismasmarcados):
            generalEAuto = UmbralModel.mldObtenerE(id_proyecto,fechaMinInicial,fechaMaxInicial)
            generalEManual = UmbralModel.mldObtenerEManual(id_proyecto,fechaMinInicial,fechaMaxInicial)
            if generalEAuto is not None:
                generalE.extend(generalEAuto)
            if generalEManual is not None:
                generalE.extend(generalEManual)
        else:
            generalE = UmbralController.crtlObtenerEResumenMonitor1(id_proyecto, prismasmarcados, fechaMinInicial, fechaMaxInicial)
        return generalE
    
    # obtener datos resumen E de lecturas por prisma segun nombre y fechas
    # def crtlObtenerEResumenMonitor1(proyecto, marcados, fechaini, fechafin):
    #     datosprisma = []
    #     for code, fila, id in marcados:
    #         if code == "Automatizado":
    #             existe = PrismaModel.mdlComprobarPrismaResumenFechas(proyecto, 1, fila, fechaini, fechafin)
    #             if existe:
    #                 datosa = UmbralModel.mldObtenerEPrismaNombre(proyecto, fila, fechaini, fechafin)
    #                 if datosa is not None:
    #                     datosprisma.append(datosa)
    #         else:
    #             existe = PrismaModel.mdlComprobarPrismaResumenFechas(proyecto, 2, fila, fechaini, fechafin)
    #             if existe:
    #                 datosm = UmbralModel.mldObtenerEPrismaNombreManual(proyecto, fila, fechaini, fechafin)
    #                 if datosm is not None:
    #                     datosprisma.append(datosm)
    #     return datosprisma
    
    def crtlObtenerEResumenMonitor1(proyecto, marcados, fechaini, fechafin):
        datosprisma = []
        nombres_auto = [nombre for tipo, nombre, _ in marcados if tipo == "Automatizado"]
        nombres_manual = [nombre for tipo, nombre, _ in marcados if tipo != "Automatizado"]
        # return datosprisma
        if nombres_auto:
            datosa = UmbralModel.mldObtenerEPrismaNombre(proyecto, nombres_auto, fechaini, fechafin)
            if datosa is not None:
                datosprisma.extend(datosa)

        if nombres_manual:
            datosm = UmbralModel.mldObtenerEPrismaNombreManual(proyecto, nombres_manual, fechaini, fechafin)
            if datosm is not None:
                datosprisma.extend(datosm)
        return datosprisma
    
    def crtObtenerZ(id_proyecto,fechaMinInicial,fechaMaxInicial, prismastotales, prismasmarcados):
        generalZ = []
        if len(prismastotales) == len(prismasmarcados):
            generalZAuto = UmbralModel.mldObtenerZ(id_proyecto,fechaMinInicial,fechaMaxInicial)
            generalZManual = UmbralModel.mldObtenerZManual(id_proyecto,fechaMinInicial,fechaMaxInicial)
            if generalZAuto is not None:
                generalZ.extend(generalZAuto)
            if generalZManual is not None:
                generalZ.extend(generalZManual)
        else:
            generalZ = UmbralController.crtlObtenerZResumenMonitor1(id_proyecto, prismasmarcados, fechaMinInicial,fechaMaxInicial)
        return generalZ
    
    # obtener datos resumen Z de lecturas por prisma segun nombre y fechas
    # def crtlObtenerZResumenMonitor1(proyecto, marcados, fechaini, fechafin):
    #     datosprisma = []
    #     for code, fila, id in marcados:
    #         if code == "Automatizado":
    #             existe = PrismaModel.mdlComprobarPrismaResumenFechas(proyecto, 1, fila, fechaini, fechafin)
    #             if existe:
    #                 datosa = UmbralModel.mldObtenerZPrismaNombre(proyecto, fila, fechaini, fechafin)
    #                 if datosa is not None:
    #                     datosprisma.append(datosa)
    #         else:
    #             existe = PrismaModel.mdlComprobarPrismaResumenFechas(proyecto, 2, fila, fechaini, fechafin)
    #             if existe:
    #                 datosm = UmbralModel.mldObtenerZPrismaNombreManual(proyecto, fila, fechaini, fechafin)
    #                 if datosm is not None:
    #                     datosprisma.append(datosm)
    #     return datosprisma
    def crtlObtenerZResumenMonitor1(proyecto, marcados, fechaini, fechafin):
        datosprisma = []
        nombres_auto = [nombre for tipo, nombre, _ in marcados if tipo == "Automatizado"]
        nombres_manual = [nombre for tipo, nombre, _ in marcados if tipo != "Automatizado"]
        # return datosprisma
        if nombres_auto:
            datosa = UmbralModel.mldObtenerZPrismaNombre(proyecto, nombres_auto, fechaini, fechafin)
            if datosa is not None:
                datosprisma.extend(datosa)

        if nombres_manual:
            datosm = UmbralModel.mldObtenerZPrismaNombreManual(proyecto, nombres_manual, fechaini, fechafin)
            if datosm is not None:
                datosprisma.extend(datosm)
        return datosprisma
    
    def crtObtenerFechaMinMax(id_proyecto):       
        fechasa = UmbralModel.mdlObtenerFechaMinMaxAuto(id_proyecto)
        fechasm = UmbralModel.mdlObtenerFechaMinMaxManual(id_proyecto)
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

    def crtObtenerFechasEnRango(id_proyecto, fechaini, fechafin, prismasmarcados):
        datosprisma = []
        nombres_auto = [nombre for tipo, nombre, _ in prismasmarcados if tipo == "Automatizado"]
        nombres_manual = [nombre for tipo, nombre, _ in prismasmarcados if tipo != "Automatizado"]
        if nombres_auto:
            datosa = UmbralModel.mdlObtenerFechasRangoPrismaNombre(id_proyecto, nombres_auto, fechaini, fechafin)
            if datosa is not None:
                datosprisma.extend(datosa)
        if nombres_manual:
            datosm = UmbralModel.mdlObtenerFechasRangoPrismaNombreManual(id_proyecto, nombres_manual, fechaini, fechafin)
            if datosm is not None:
                datosprisma.extend(datosm)
        return datosprisma
    
    def ctrObtenerUmbralesEquiposCP(proyectoid, componenteid, tabla, tipoequipo):
        if tabla == "umbral_piezometro":
            umbral = UmbralModel.mdlObtenerUmbralesPiezometrosAnexo2(proyectoid, componenteid, tipoequipo)
        else:
            umbral = UmbralModel.mdlObtenerUmbralesEquiposCP(proyectoid, componenteid, tabla)
        return umbral
    
    def ctrObtenerUmbralesInclinometros(ids):
        umbral = UmbralModel.mdlObtenerUmbralesInclinometros(ids)
        return umbral
    
    def ctrObtenerUmbralesPiezometros(ids):
        umbral = UmbralModel.mdlObtenerUmbralesPiezometros(ids)
        return umbral
    
    @staticmethod
    def ctrlListarInstrumentosComponente(proyectoid, componente_id, tipo_equipo):
        return UmbralModel.mdlListarInstrumentosComponente(proyectoid, componente_id, tipo_equipo)

    @staticmethod
    def ctrlListarTiposInstrumentoComponente(componente_id):
        return UmbralModel.mdlListarTiposInstrumentoComponente(componente_id)
    
    
