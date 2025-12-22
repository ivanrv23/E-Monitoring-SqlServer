from models.DesplazamientoModel import DesplazamientoModel
from utils.common.metodosGenerales import MetodosGenerales

class DesplazamientoController:
    
    def ctrlDatosPrismasMarcados(idproyecto, prismasmarcados, fechaini, fechafin, tipografico, unidad, tipofiltro, tipopromedio, cantidad):
        prismastotales = []
        if tipopromedio == "SPRO":
            if tipofiltro == 0: # sin promedio sin fechas
                method_name = 'mdlCalcularDesplazamiento' + tipografico
                for componente, listaprismas in prismasmarcados:
                    nombrecomponente, idcomponente, idproy = componente
                    resultado = MetodosGenerales.ctrlAgruparPrismasSegunTipo(listaprismas)
                    for tabla, prismas in resultado.items():
                        prismasdata = getattr(DesplazamientoModel, method_name)(tabla, unidad, prismas, idcomponente)
                        if prismasdata:
                            prismastotales.extend(prismasdata)
            else: # sin promedio con fechas
                method_name = 'mdlCalcularDesplazamientoFechas' + tipografico
                for componente, listaprismas in prismasmarcados:
                    nombrecomponente, idcomponente, idproy = componente
                    resultado = MetodosGenerales.ctrlAgruparPrismasSegunTipo(listaprismas)
                    for tabla, prismas in resultado.items():
                        prismasdata = getattr(DesplazamientoModel, method_name)(tabla, unidad, prismas, idcomponente, fechaini, fechafin)
                        if prismasdata:
                            prismastotales.extend(prismasdata)
        elif tipopromedio == "PDIA":
            if tipofiltro == 0: # promedio días sin fechas
                method_name = 'mdlCalcularDesplazamientoDias' + tipografico
                for componente, listaprismas in prismasmarcados:
                    nombrecomponente, idcomponente, idproy = componente
                    resultado = MetodosGenerales.ctrlAgruparPrismasSegunTipo(listaprismas)
                    for tabla, prismas in resultado.items():
                        prismasdata = getattr(DesplazamientoModel, method_name)(tabla, unidad, prismas, idcomponente, cantidad)
                        if prismasdata:
                            prismastotales.extend(prismasdata)
            else: # promedio días con fechas
                method_name = 'mdlCalcularDesplazamientoDiasFechas' + tipografico
                for componente, listaprismas in prismasmarcados:
                    nombrecomponente, idcomponente, idproy = componente
                    resultado = MetodosGenerales.ctrlAgruparPrismasSegunTipo(listaprismas)
                    for tabla, prismas in resultado.items():
                        prismasdata = getattr(DesplazamientoModel, method_name)(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad)
                        if prismasdata:
                            prismastotales.extend(prismasdata)
        else:
            if tipofiltro == 0: # promedio horas sin fechas
                method_name = 'mdlCalcularDesplazamientoHoras' + tipografico
                for componente, listaprismas in prismasmarcados:
                    nombrecomponente, idcomponente, idproy = componente
                    resultado = MetodosGenerales.ctrlAgruparPrismasSegunTipo(listaprismas)
                    for tabla, prismas in resultado.items():
                        prismasdata = getattr(DesplazamientoModel, method_name)(tabla, unidad, prismas, idcomponente, cantidad)
                        if prismasdata:
                            prismastotales.extend(prismasdata)
            else: # promedio horas con fechas
                method_name = 'mdlCalcularDesplazamientoHorasFechas' + tipografico
                for componente, listaprismas in prismasmarcados:
                    nombrecomponente, idcomponente, idproy = componente
                    resultado = MetodosGenerales.ctrlAgruparPrismasSegunTipo(listaprismas)
                    for tabla, prismas in resultado.items():
                        prismasdata = getattr(DesplazamientoModel, method_name)(tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad)
                        if prismasdata:
                            prismastotales.extend(prismasdata)
        return prismastotales


    