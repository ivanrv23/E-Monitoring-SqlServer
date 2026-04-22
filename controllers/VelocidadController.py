from models.VelocidadModel import VelocidadModel
from utils.common.metodosGenerales import MetodosGenerales

class VelocidadController:
    
    @staticmethod
    def ctrlDatosPrismasMarcados(idproyecto, prismasmarcados, fechaini, fechafin, tipografico, unidad, tipovelocidad, tipofiltro, tipopromedio, cantidad):
        prismastotales = []

        # =========================
        # SIN PROMEDIO
        # =========================
        if tipopromedio == "SPRO":

            for componente, listaprismas in prismasmarcados:
                nombrecomponente, idcomponente, idproy = componente
                resultado = MetodosGenerales.ctrlAgruparPrismasSegunTipo(listaprismas)

                for tabla, prismas in resultado.items():

                    if tipofiltro == 0:
                        # ✅ MODO HISTÓRICO: Llama al método histórico pero ahora PASANDO LAS FECHAS para optimización.
                        base_name = 'mdlCalcularVelocidad'
                        if tipografico == "VI3D" and tipovelocidad == 0:
                            base_name = 'mdlCalcularVelocidadPositiva'
                        
                        method_name = base_name + tipografico
                        
                        prismasdata = getattr(VelocidadModel, method_name)(
                            tabla, unidad, prismas, idcomponente, fechaini, fechafin
                        )
                    else:
                        # ✅ MODO POR FECHAS: Llama al método de fechas existente. NO se altera.
                        base_name_f = 'mdlCalcularVelocidadFechas'
                        if tipografico == "VI3D" and tipovelocidad == 0:
                            base_name_f = 'mdlCalcularVelocidadPositivaFechas'

                        method_name_f = base_name_f + tipografico

                        prismasdata = getattr(VelocidadModel, method_name_f)(
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
                        # ✅ MODO HISTÓRICO: Llama al método histórico pero ahora PASANDO LAS FECHAS para optimización.
                        base_name = 'mdlCalcularVelocidadDias'
                        if tipografico == "VI3D" and tipovelocidad == 0:
                            base_name = 'mdlCalcularVelocidadDiasPositiva'

                        method_name = base_name + tipografico

                        prismasdata = getattr(VelocidadModel, method_name)(
                            tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad
                        )
                    else:
                        # ✅ MODO POR FECHAS: Llama al método de fechas existente. NO se altera.
                        base_name_f = 'mdlCalcularVelocidadDiasFechas'
                        if tipografico == "VI3D" and tipovelocidad == 0:
                            base_name_f = 'mdlCalcularVelocidadDiasPositivaFechas'

                        method_name_f = base_name_f + tipografico
                        
                        prismasdata = getattr(VelocidadModel, method_name_f)(
                            tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad
                        )

                    if prismasdata:
                        prismastotales.extend(prismasdata)

        # =========================
        # PROMEDIO EN HORAS
        # =========================
        else: # Asume "PHOR" o cualquier otro valor para promedio por horas

            for componente, listaprismas in prismasmarcados:
                nombrecomponente, idcomponente, idproy = componente
                resultado = MetodosGenerales.ctrlAgruparPrismasSegunTipo(listaprismas)

                for tabla, prismas in resultado.items():

                    if tipofiltro == 0:
                        # ✅ MODO HISTÓRICO: Llama al método histórico pero ahora PASANDO LAS FECHAS para optimización.
                        base_name = 'mdlCalcularVelocidadHoras'
                        if tipografico == "VI3D" and tipovelocidad == 0:
                            base_name = 'mdlCalcularVelocidadHorasPositiva'
                        
                        method_name = base_name + tipografico

                        prismasdata = getattr(VelocidadModel, method_name)(
                            tabla, unidad, prismas, idcomponente, fechaini, fechafin, cantidad
                        )
                    else:
                        # ✅ MODO POR FECHAS: Llama al método de fechas existente. NO se altera.
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