from models.VelocidadModel import VelocidadModel
from utils.common.metodosGenerales import MetodosGenerales

class VelocidadController:
    
    def ctrlDatosPrismasMarcados(idproyecto, prismasmarcados, fechaini, fechafin, tipografico, unidadmedida, tipovelocidad, filtrado, tipopromedio, cantidad):
        prismastotales = []
        if tipopromedio == "SPRO":
            if filtrado == 0: # sin fechas
                method_name = 'mdlCalcularVelocidad' + tipografico
                if tipografico == "VI3D":
                    if tipovelocidad == 0:
                        method_name = 'mdlCalcularVelocidadPositiva' + tipografico
                for componente, listaprismas in prismasmarcados:
                    nombrecomponente, idcomponente, idproy = componente
                    resultado = MetodosGenerales.ctrlAgruparPrismasSegunTipo(listaprismas)
                    for tabla, prismas in resultado.items():
                        prismasdata = getattr(VelocidadModel, method_name)(tabla, unidadmedida, prismas, idcomponente)
                        if prismasdata:
                            prismastotales.extend(prismasdata)
            else: # con fechas
                method_name = 'mdlCalcularVelocidadFechas' + tipografico
                if tipografico == "VI3D":
                    if tipovelocidad == 0:
                        method_name = 'mdlCalcularVelocidadPositivaFechas' + tipografico
                for componente, listaprismas in prismasmarcados:
                    nombrecomponente, idcomponente, idproy = componente
                    resultado = MetodosGenerales.ctrlAgruparPrismasSegunTipo(listaprismas)
                    for tabla, prismas in resultado.items():
                        prismasdata = getattr(VelocidadModel, method_name)(tabla, unidadmedida, prismas, idcomponente, fechaini, fechafin)
                        if prismasdata:
                            prismastotales.extend(prismasdata)
        elif tipopromedio == "PDIA":
            if filtrado == 0: # sin fechas
                method_name = 'mdlCalcularVelocidadDias' + tipografico
                if tipografico == "VI3D":
                    if tipovelocidad == 0:
                        method_name = 'mdlCalcularVelocidadDiasPositiva' + tipografico
                for componente, listaprismas in prismasmarcados:
                    nombrecomponente, idcomponente, idproy = componente
                    resultado = MetodosGenerales.ctrlAgruparPrismasSegunTipo(listaprismas)
                    for tabla, prismas in resultado.items():
                        prismasdata = getattr(VelocidadModel, method_name)(tabla, unidadmedida, prismas, idcomponente, cantidad)
                        if prismasdata:
                            prismastotales.extend(prismasdata)
            else: # con fechas
                method_name = 'mdlCalcularVelocidadDiasFechas' + tipografico
                if tipografico == "VI3D":
                    if tipovelocidad == 0:
                        method_name = 'mdlCalcularVelocidadDiasPositivaFechas' + tipografico
                for componente, listaprismas in prismasmarcados:
                    nombrecomponente, idcomponente, idproy = componente
                    resultado = MetodosGenerales.ctrlAgruparPrismasSegunTipo(listaprismas)
                    for tabla, prismas in resultado.items():
                        prismasdata = getattr(VelocidadModel, method_name)(tabla, unidadmedida, prismas, idcomponente, fechaini, fechafin, cantidad)
                        if prismasdata:
                            prismastotales.extend(prismasdata)
        else:
            if filtrado == 0: # sin fechas
                method_name = 'mdlCalcularVelocidadHoras' + tipografico
                if tipografico == "VI3D":
                    if tipovelocidad == 0:
                        method_name = 'mdlCalcularVelocidadHorasPositiva' + tipografico
                for componente, listaprismas in prismasmarcados:
                    nombrecomponente, idcomponente, idproy = componente
                    resultado = MetodosGenerales.ctrlAgruparPrismasSegunTipo(listaprismas)
                    for tabla, prismas in resultado.items():
                        prismasdata = getattr(VelocidadModel, method_name)(tabla, unidadmedida, prismas, idcomponente, cantidad)
                        if prismasdata:
                            prismastotales.extend(prismasdata)
            else: # con fechas
                method_name = 'mdlCalcularVelocidadHorasFechas' + tipografico
                if tipografico == "VI3D":
                    if tipovelocidad == 0:
                        method_name = 'mdlCalcularVelocidadHorasPositivaFechas' + tipografico
                for componente, listaprismas in prismasmarcados:
                    nombrecomponente, idcomponente, idproy = componente
                    resultado = MetodosGenerales.ctrlAgruparPrismasSegunTipo(listaprismas)
                    for tabla, prismas in resultado.items():
                        prismasdata = getattr(VelocidadModel, method_name)(tabla, unidadmedida, prismas, idcomponente, fechaini, fechafin, cantidad)
                        if prismasdata:
                            prismastotales.extend(prismasdata)
        return prismastotales
    