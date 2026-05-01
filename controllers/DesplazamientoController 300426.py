from models.DesplazamientoModel import DesplazamientoModel
from utils.common.metodosGenerales import MetodosGenerales

class DesplazamientoController:
    
    @staticmethod
    def ctrlDatosPrismasMarcados(idproyecto, prismasmarcados, fechaini, fechafin, tipografico, unidad, tipofiltro, tipopromedio, cantidad):
        prismastotales = []

        # =========================
        # SIN PROMEDIO
        # =========================
        if tipopromedio == "SPRO":

            method_name = 'mdlCalcularDesplazamiento' + tipografico

            for componente, listaprismas in prismasmarcados:
                nombrecomponente, idcomponente, idproy = componente
                resultado = MetodosGenerales.ctrlAgruparPrismasSegunTipo(listaprismas)

                for tabla, prismas in resultado.items():

                    if tipofiltro == 0:
                        # ✅ Histórico optimizado (ahora también recibe rango)
                        prismasdata = getattr(DesplazamientoModel, method_name)(
                            tabla, unidad, prismas, idcomponente, fechaini, fechafin
                        )
                    else:
                        # ✅ Con fechas (ya existente)
                        method_name_f = 'mdlCalcularDesplazamientoFechas' + tipografico
                        prismasdata = getattr(DesplazamientoModel, method_name_f)(
                            tabla, unidad, prismas, idcomponente, fechaini, fechafin
                        )

                    if prismasdata:
                        prismastotales.extend(prismasdata)

        # =========================
        # PROMEDIO EN DÍAS
        # =========================
        elif tipopromedio == "PDIA":

            for componente, listaprismas in prismasmarcados:
                nombrecomponente, idcomponente, idproy = componente
                resultado = MetodosGenerales.ctrlAgruparPrismasSegunTipo(listaprismas)

                for tabla, prismas in resultado.items():

                    if tipofiltro == 0:
                        method_name = 'mdlCalcularDesplazamientoDias' + tipografico
                        prismasdata = getattr(DesplazamientoModel, method_name)(
                            tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad
                        )
                    else:
                        method_name_f = 'mdlCalcularDesplazamientoDiasFechas' + tipografico
                        prismasdata = getattr(DesplazamientoModel, method_name_f)(
                            tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad
                        )

                    if prismasdata:
                        prismastotales.extend(prismasdata)

        # =========================
        # PROMEDIO EN HORAS
        # =========================
        else:

            for componente, listaprismas in prismasmarcados:
                nombrecomponente, idcomponente, idproy = componente
                resultado = MetodosGenerales.ctrlAgruparPrismasSegunTipo(listaprismas)

                for tabla, prismas in resultado.items():

                    if tipofiltro == 0:
                        method_name = 'mdlCalcularDesplazamientoHoras' + tipografico
                        prismasdata = getattr(DesplazamientoModel, method_name)(
                            tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad
                        )
                    else:
                        method_name_f = 'mdlCalcularDesplazamientoHorasFechas' + tipografico
                        prismasdata = getattr(DesplazamientoModel, method_name_f)(
                            tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad
                        )

                    if prismasdata:
                        prismastotales.extend(prismasdata)

        return prismastotales