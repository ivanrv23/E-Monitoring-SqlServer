from models.VelocidadModel import VelocidadModel
from utils.common.metodosGenerales import MetodosGenerales
from services.queries.query_context import get_active_request
from services.queries.query_registry import query_registry


class VelocidadController:

    @staticmethod
    def _esta_cancelado():
        request_id = get_active_request()
        if request_id is None:
            return False
        return query_registry.is_cancel_requested(request_id)

    @staticmethod
    def ctrlDatosPrismasMarcados(idproyecto, prismasmarcados, fechaini, fechafin, tipografico, unidad, tipovelocidad, tipofiltro, tipopromedio, cantidad):
        prismastotales = []

        if tipopromedio == "SPRO":

            for componente, listaprismas in prismasmarcados:
                if VelocidadController._esta_cancelado():
                    return []

                nombrecomponente, idcomponente, idproy = componente
                resultado = MetodosGenerales.ctrlAgruparPrismasSegunTipo(listaprismas)

                for tabla, prismas in resultado.items():
                    if VelocidadController._esta_cancelado():
                        return []

                    if tipofiltro == 0:
                        base_name = 'mdlCalcularVelocidad'
                        if tipografico == "VI3D" and tipovelocidad == 0:
                            base_name = 'mdlCalcularVelocidadPositiva'

                        method_name = base_name + tipografico

                        prismasdata = getattr(VelocidadModel, method_name)(
                            tabla, unidad, prismas, idcomponente, fechaini, fechafin
                        )
                    else:
                        base_name_f = 'mdlCalcularVelocidadFechas'
                        if tipografico == "VI3D" and tipovelocidad == 0:
                            base_name_f = 'mdlCalcularVelocidadPositivaFechas'

                        method_name_f = base_name_f + tipografico

                        prismasdata = getattr(VelocidadModel, method_name_f)(
                            tabla, unidad, prismas, idcomponente, fechaini, fechafin
                        )

                    if prismasdata:
                        prismastotales.extend(prismasdata)

        elif tipopromedio == "PDIA":

            for componente, listaprismas in prismasmarcados:
                if VelocidadController._esta_cancelado():
                    return []

                nombrecomponente, idcomponente, idproy = componente
                resultado = MetodosGenerales.ctrlAgruparPrismasSegunTipo(listaprismas)

                for tabla, prismas in resultado.items():
                    if VelocidadController._esta_cancelado():
                        return []

                    if tipofiltro == 0:
                        base_name = 'mdlCalcularVelocidadDias'
                        if tipografico == "VI3D" and tipovelocidad == 0:
                            base_name = 'mdlCalcularVelocidadDiasPositiva'

                        method_name = base_name + tipografico

                        prismasdata = getattr(VelocidadModel, method_name)(
                            tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad
                        )
                    else:
                        base_name_f = 'mdlCalcularVelocidadDiasFechas'
                        if tipografico == "VI3D" and tipovelocidad == 0:
                            base_name_f = 'mdlCalcularVelocidadDiasPositivaFechas'

                        method_name_f = base_name_f + tipografico

                        prismasdata = getattr(VelocidadModel, method_name_f)(
                            tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad
                        )

                    if prismasdata:
                        prismastotales.extend(prismasdata)

        else:

            for componente, listaprismas in prismasmarcados:
                if VelocidadController._esta_cancelado():
                    return []

                nombrecomponente, idcomponente, idproy = componente
                resultado = MetodosGenerales.ctrlAgruparPrismasSegunTipo(listaprismas)

                for tabla, prismas in resultado.items():
                    if VelocidadController._esta_cancelado():
                        return []

                    if tipofiltro == 0:
                        base_name = 'mdlCalcularVelocidadHoras'
                        if tipografico == "VI3D" and tipovelocidad == 0:
                            base_name = 'mdlCalcularVelocidadHorasPositiva'

                        method_name = base_name + tipografico

                        prismasdata = getattr(VelocidadModel, method_name)(
                            tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad
                        )
                    else:
                        base_name_f = 'mdlCalcularVelocidadHorasFechas'
                        if tipografico == "VI3D" and tipovelocidad == 0:
                            base_name_f = 'mdlCalcularVelocidadHorasPositivaFechas'

                        method_name_f = base_name_f + tipografico

                        prismasdata = getattr(VelocidadModel, method_name_f)(
                            tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad
                        )

                    if prismasdata:
                        prismastotales.extend(prismasdata)

        return prismastotales