from models.DesplazamientoModel import DesplazamientoModel
from utils.common.metodosGenerales import MetodosGenerales
from services.queries.query_context import get_active_request
from services.queries.query_registry import query_registry


class DesplazamientoController:

    @staticmethod
    def _esta_cancelado():
        request_id = get_active_request()
        if request_id is None:
            return False
        return query_registry.is_cancel_requested(request_id)

    @staticmethod
    def ctrlDatosPrismasMarcados(idproyecto, prismasmarcados, fechaini, fechafin, tipografico, unidad, tipofiltro, tipopromedio, cantidad):
        prismastotales = []

        if tipopromedio == "SPRO":

            method_name = 'mdlCalcularDesplazamiento' + tipografico
            method_name_f = 'mdlCalcularDesplazamientoFechas' + tipografico

            for componente, listaprismas in prismasmarcados:
                if DesplazamientoController._esta_cancelado():
                    return []

                nombrecomponente, idcomponente, idproy = componente
                resultado = MetodosGenerales.ctrlAgruparPrismasSegunTipo(listaprismas)

                for tabla, prismas in resultado.items():
                    if DesplazamientoController._esta_cancelado():
                        return []

                    if tipofiltro == 0:
                        prismasdata = getattr(DesplazamientoModel, method_name)(
                            tabla, unidad, prismas, idcomponente, fechaini, fechafin
                        )
                    else:
                        prismasdata = getattr(DesplazamientoModel, method_name_f)(
                            tabla, unidad, prismas, idcomponente, fechaini, fechafin
                        )

                    if prismasdata:
                        prismastotales.extend(prismasdata)

        elif tipopromedio == "PDIA":

            for componente, listaprismas in prismasmarcados:
                if DesplazamientoController._esta_cancelado():
                    return []

                nombrecomponente, idcomponente, idproy = componente
                resultado = MetodosGenerales.ctrlAgruparPrismasSegunTipo(listaprismas)

                for tabla, prismas in resultado.items():
                    if DesplazamientoController._esta_cancelado():
                        return []

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

        else:

            for componente, listaprismas in prismasmarcados:
                if DesplazamientoController._esta_cancelado():
                    return []

                nombrecomponente, idcomponente, idproy = componente
                resultado = MetodosGenerales.ctrlAgruparPrismasSegunTipo(listaprismas)

                for tabla, prismas in resultado.items():
                    if DesplazamientoController._esta_cancelado():
                        return []

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