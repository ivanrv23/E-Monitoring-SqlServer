from models.InterfazModel import InterfazModel
from utils.common.metodosGenerales import MetodosGenerales

class InterfazController:
    
    def ctrlListarProyectos():
        listas = InterfazModel.mdlListarProyectos()
        return listas
    
    def ctrlListarComponentesProyecto(idproyecto):
        listas = InterfazModel.mdlListarComponentesProyecto(idproyecto)
        return listas
    
    def ctrlListarInclinometrosProyecto(idproyecto):
        listas = InterfazModel.mdlListarInclinometrosProyecto(idproyecto)
        return listas
    
    def ctrlListarPiezometrosProyecto(idproyecto):
        piezometros = []
        p_manuales = InterfazModel.mdlListarPiezometrosProyecto(idproyecto, 'piezometromanuales', "PIEZOMETROMANUAL")
        if p_manuales:
            piezometros.extend(p_manuales)
        p_cuerda = InterfazModel.mdlListarPiezometrosProyecto(idproyecto, 'piezometrocuerdas', "PIEZOMETROCUERDA")
        if p_cuerda:
            piezometros.extend(p_cuerda)
        return piezometros
    
    def ctrlListarCeldasProyecto(idproyecto):
        celdas = InterfazModel.mdlListarCeldasProyecto(idproyecto)
        return celdas
    
    def ctrlListarTopografiasComponente(idzona, estado):
        listatopos = InterfazModel.mdlListarTopografiasComponente(idzona, "TOPOGRAFIA", estado)
        return listatopos
    
    def ctrlListarComponenteTopografia(idinstrumento):
        listaincli = InterfazModel.mdlListarComponenteEquipoTopografia(idinstrumento, "TOPOGRAFIA")
        return listaincli
    
    def ctrlListarPrismasComponente(idzona, estado):
        prismas = []
        dataprismas = InterfazModel.mdlListarPrismasComponente(idzona, "PRISMAS", estado)
        if dataprismas:
            prismas.extend(dataprismas)
        return prismas
    
    def ctrlListarPrismasAutoNuevosComponente(idzona, tipo, prismas):
        respuesta = InterfazModel.mdlListarPrismasAutoNuevosComponente(idzona, tipo, prismas)
        return respuesta
    
    def ctrlListarComponentePrisma(idinstrumento, estado):
        listas = InterfazModel.mdlListarComponentePrisma(idinstrumento, estado)
        return listas
    
    def ctrlListarInclinometrosComponente(idzona, proyectoid):
        inclinometros = []
        listaincli = InterfazModel.mdlListarInclinometrosComponente(idzona, "INCLINOMETRO", 1)
        if listaincli:
            for incli in listaincli:
                fechas = InterfazModel.mdlListarFechasInclinometroCodigo(idzona, incli[0], proyectoid)
                if fechas:
                    fechitas = [fecha[0] for fecha in fechas]
                    inclinometros.append((incli[0], incli[1], incli[2], incli[3], incli[4], incli[5], incli[6], fechitas))
        return inclinometros
    
    def ctrlListarFechasInclinometro(idcomponente, idinstrumento, idproyecto):
        listas = InterfazModel.mdlListarFechasPiezometros(idcomponente, idinstrumento, idproyecto)
        return listas
    
    def ctrlListarComponenteInclinometro(proyectoid, idinstrumento):
        inclinometros = []
        listaincli = InterfazModel.mdlListarComponenteEquipo(idinstrumento, "INCLINOMETRO")
        if listaincli:
            incli = listaincli[0]
            fechas = InterfazModel.mdlListarFechasInclinometroCodigo(incli[1], incli[0], proyectoid)
            if fechas:
                fechitas = [fecha[0] for fecha in fechas]
                inclinometros.append((incli[0], incli[1], incli[2], incli[3], incli[4], incli[5], incli[6], fechitas))
        return inclinometros
    
    def ctrlListarPiezometrosCuerdaComponente(idzona, proyectoid):
        piezometros = []
        listapiezo = InterfazModel.mdlListarPiezometrosCuerdaComponente(proyectoid, idzona, "PIEZOMETROCUERDA", 1)
        if listapiezo:
            for piezo in listapiezo:
                fechas = InterfazController.ctrlListarFechasPiezometroCodigo("Automatizado", idzona, piezo[0], proyectoid)
                if fechas:
                    ultima_fecha = fechas[-1][0]
                    piezometros.append((piezo[0], piezo[1], piezo[2], piezo[3], piezo[4], piezo[5], piezo[6], ultima_fecha))
        return piezometros
    
    def ctrlListarComponentePiezometroCuerda(idinstrumento):
        listacuerda = InterfazModel.mdlListarComponenteEquipo(idinstrumento, "PIEZOMETROCUERDA")
        return listacuerda
    
    def ctrlListarPiezometrosManualComponente(idzona, proyectoid):
        piezometros = []
        listapiezo = InterfazModel.mdlListarPiezometrosManualComponente(proyectoid, idzona, "PIEZOMETROMANUAL", 1)
        if listapiezo:
            for piezo in listapiezo:
                fechas = InterfazController.ctrlListarFechasPiezometroCodigo("Manual", idzona, piezo[0], proyectoid)
                if fechas:
                    ultima_fecha = fechas[-1][0]
                    piezometros.append((piezo[0], piezo[1], piezo[2], piezo[3], piezo[4], piezo[5], piezo[6], ultima_fecha))
        return piezometros
    
    def ctrlListarComponentePiezometroManual(idinstrumento):
        listacuerda = InterfazModel.mdlListarComponenteEquipo(idinstrumento, "PIEZOMETROMANUAL")
        return listacuerda
    
    def ctrlListarPluviometrosComponente(idproyecto, idzona):
        listapiezo = InterfazModel.mdlListarPluviometrosComponente(idproyecto, idzona, "PLUVIOMETRO", 1)
        return listapiezo
    
    def ctrlListarComponentePluviometro(idinstrumento):
        lista = InterfazModel.mdlListarComponenteEquipo(idinstrumento, "PLUVIOMETRO")
        return lista
    
    def ctrlListarCotasTerrenoComponente(idproyecto, idzona):
        listapiezo = InterfazModel.mdlListarCotasTerrenoComponente(idproyecto, idzona, "COTATERRENO", 1)
        return listapiezo
    
    def ctrlListarComponenteCotaTerreno(idinstrumento):
        lista = InterfazModel.mdlListarComponenteEquipo(idinstrumento, "COTATERRENO")
        return lista
    
    def ctrlListarCeldasComponente(idproyecto, idzona):
        listapiezo = InterfazModel.mdlListarCeldasComponente(idproyecto, idzona, "CELDA", 1)
        return listapiezo
    
    def ctrlListarComponenteCelda(idinstrumento):
        lista = InterfazModel.mdlListarComponenteEquipo(idinstrumento, "CELDA")
        return lista
    
    def ctrlListarAcelerografosComponente(idproyecto, idzona):
        listapiezo = InterfazModel.mdlListarAcelerografosComponente(idproyecto, idzona, "ACELEROGRAFO", 1)
        return listapiezo
    
    def ctrlListarAcelerografosVistaComponente(idproyecto, idzona):
        acelerografos = []
        listaacelero = InterfazModel.mdlListarEquiposTipoComponente(idzona, "ACELEROGRAFO")
        if listaacelero:
            for data in listaacelero:
                acelero = InterfazModel.mdlValidarAcelerografoComponente(idproyecto, data[0], "ACELEROGRAFO")
                if acelero is False:
                    ruta = f"../../resources/workspace/ACELEROGRAFOS/proyecto{idproyecto}/{data[4]}"
                    respuesta = MetodosGenerales.existeArchivosRuta(ruta)
                    if respuesta:
                        acelerografos.append(data)
                else:
                    acelerografos.append(data)
        return acelerografos
    
    def ctrlListarComponenteAcelerografo(idinstrumento):
        lista = InterfazModel.mdlListarComponenteEquipo(idinstrumento, "ACELEROGRAFO")
        return lista
    
    def ctrlListarSondajesTDRComponente(idzona, proyectoid):
        sondajestdr = []
        listatdr = InterfazModel.mdlListarSondajestdrComponente(proyectoid, idzona, "TDR", 1)
        if listatdr:
            tabla = f"sondajetdr_detalle{proyectoid}"
            for sonda in listatdr:
                fechas = InterfazModel.mdlListarFechasSondajetdrCodigo(tabla, idzona, sonda[0])
                if fechas:
                    fechitas = [fecha[0] for fecha in fechas]
                    sondajestdr.append((sonda[0], sonda[1], sonda[2], sonda[3], sonda[4], sonda[5], sonda[6], fechitas))
        return sondajestdr
    
    def ctrlListarComponenteSondajeTDR(idinstrumento):
        lista = InterfazModel.mdlListarComponenteEquipo(idinstrumento, "TDR")
        return lista
    
    def ctrlListarEquiposAdicionalesComponente(idzona):
        listapiezo = InterfazModel.mdlListarEquiposComponente(idzona, "ADICIONAL", 1)
        return listapiezo
    
    def ctrlListarPrismasVirtualesComponente(idzona):
        listaPrismaVirtual = InterfazModel.mdlListarPrismasVirtualesComponente(idzona, "PRISMAVIRTUAL", 1)
        return listaPrismaVirtual
    
    def ctrlListarComponenteEquipoAdicional(idinstrumento):
        lista = InterfazModel.mdlListarComponenteEquipo(idinstrumento, "ADICIONAL")
        return lista
    
    def ctrlListarFechasPiezometroCodigo(tipo, idcomponente, idinstru, proyectoid):
        if tipo == "Automatizado":
            respuesta = InterfazModel.mdlListarFechasPiezometroCuerdaCodigo(idcomponente, idinstru, proyectoid)
        else:
            respuesta = InterfazModel.mdlListarFechasPiezometroManualCodigo(idcomponente, idinstru, proyectoid)
        return respuesta
    
    def ctrlListarFechasSondajetdrCodigo(proyectoid, idcomponente, idinstrumento):
        tabla = f"sondajetdr_detalle{proyectoid}"
        respuesta = InterfazModel.mdlListarFechasSondajetdrCodigo(tabla, idcomponente, idinstrumento)
        return respuesta
    
    def ctrlListarArchivosLidar(id_componente):
        respuesta = InterfazModel.mdlListarArchivosLidar(id_componente)
        return respuesta
    
    def ctrlGuardarPreferenciasMarcado(idproyecto, modulo, preferencias):
        return InterfazModel.mdlGuardarPreferenciasMarcado(idproyecto, modulo, preferencias)

    def ctrlObtenerPreferenciasMarcado(idproyecto, modulo):
        return InterfazModel.mdlObtenerPreferenciasMarcado(idproyecto, modulo)

    def ctrlObtenerPreferenciasMarcadoAnalisis(idproyecto, modulo):
        return InterfazModel.mdlObtenerPreferenciasMarcadoAnalisis(idproyecto, modulo)

    @staticmethod
    def ctrlGuardarPlantillaNombrada(idproyecto, modulo, nombre_plantilla, preferencias, cantidad):
        return InterfazModel.mdlGuardarPlantillaNombrada(idproyecto, modulo, nombre_plantilla, preferencias, cantidad)

    @staticmethod
    def ctrlListarPlantillas(idproyecto, modulo):
        return InterfazModel.mdlListarPlantillas(idproyecto, modulo)

    @staticmethod
    def ctrlObtenerPreferenciasPorNombre(idproyecto, modulo, id_plantilla):
        return InterfazModel.mdlObtenerPreferenciasPorNombre(idproyecto, modulo, id_plantilla)

    @staticmethod
    def ctrlEliminarPlantilla(idproyecto, modulo, id_plantilla):
        return InterfazModel.mdlEliminarPlantilla(idproyecto, modulo, id_plantilla)

    @staticmethod
    def ctrlRenombrarPlantilla(idproyecto, modulo, nombre_actual, nombre_nuevo):
        return InterfazModel.mdlRenombrarPlantilla(idproyecto, modulo, nombre_actual, nombre_nuevo)