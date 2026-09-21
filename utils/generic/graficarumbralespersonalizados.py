from controllers.UmbralController import UmbralController
from utils.shared.graficarUmbrales import GraficarUmbrales

def graficarUmbralesPersonalizado(widget, unidad, idproyecto, idequipo, tipografica, tipoequipo,
                                   sentido='y', tipo_pintado='color', silencioso=False):
    """
    silencioso=True: no muestra diálogos ni mensajes (uso para pintado automático).
    Devuelve True si efectivamente pintó algo, False en caso contrario.
    """
    if tipo_pintado == 'color':
        pintado = GraficarUmbrales.clean_on_widget(widget, 'color')
    else:
        pintado = GraficarUmbrales.clean_on_widget(widget, 'linea')

    if pintado is False:
        umbrales = UmbralController.ctrlObtenerUmbralesPersonalizados(idequipo, tipografica, tipoequipo)

        if umbrales:
            # Agrupar por tipo de equipo (por si alguna vez llegan mezclados)
            umbrales_por_tipo = {}
            for umbral in umbrales:
                tipo = umbral[-1]  # tipo_equipo
                umbrales_por_tipo.setdefault(tipo, []).append(umbral)

            if len(umbrales_por_tipo) > 1:
                if silencioso:
                    # No interrumpir con diálogos durante el pintado automático
                    return False
                opciones = [(tipo, f"Umbral {tipo}") for tipo in umbrales_por_tipo.keys()]
                tipo_seleccionado = GraficarUmbrales.mostrarSeleccionUmbrales_personalizados(opciones, "Seleccione tipo de umbral")
                if tipo_seleccionado is not None:
                    umbrales = umbrales_por_tipo.get(tipo_seleccionado, [])
                else:
                    return False

            if umbrales:
                GraficarUmbrales.draw_on_widget(widget, umbrales, unidad, sentido, tipo_pintado)
                return True
    return False