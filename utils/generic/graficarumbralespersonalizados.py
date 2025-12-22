from controllers.UmbralController import UmbralController
from utils.shared.graficarUmbrales import GraficarUmbrales

def graficarUmbralesPersonalizado(widget,unidad,idproyecto,sentido='y', tipo_pintado='color'):
    if tipo_pintado=='color':
        pintado = GraficarUmbrales.clean_on_widget(widget, 'color')
    else:
        pintado = GraficarUmbrales.clean_on_widget(widget, 'linea')
    if pintado is False:
        umbrales = UmbralController.ctrlObtenerUmbralesPersonalizados(idproyecto)
        
        if umbrales:
            # Agregar columna adicional con valor 1 a cada umbral
            umbrales_modificados = []
            for umbral in umbrales:
                # Convertir a lista para poder modificar (las tuplas son inmutables)
                umbral_lista = list(umbral)
                # Insertar el valor 1 en la posición 3 (índice 3, cuarta columna)
                umbral_lista.insert(3, 1)
                # Convertir de nuevo a tupla
                umbrales_modificados.append(tuple(umbral_lista))
            
            # Ahora trabajar con los umbrales modificados
            umbrales = umbrales_modificados
            
            # Agrupar umbrales por su tipo (última columna)
            umbrales_por_tipo = {}
            for umbral in umbrales:
                tipo = umbral[-1]  # Última columna es el tipo
                if tipo not in umbrales_por_tipo:
                    umbrales_por_tipo[tipo] = []
                umbrales_por_tipo[tipo].append(umbral)
            
            # Si hay más de un tipo, mostrar diálogo de selección
            if len(umbrales_por_tipo) > 1:
                # Preparar lista de opciones para el diálogo
                opciones = [(tipo, f"Umbral {tipo}") for tipo in umbrales_por_tipo.keys()]
                
                # Mostrar diálogo y obtener selección
                tipo_seleccionado = GraficarUmbrales.mostrarSeleccionUmbrales_personalizados(opciones, "Seleccione tipo de umbral")
                
                if tipo_seleccionado is not None:
                    # Filtrar umbrales por el tipo seleccionado
                    umbrales = umbrales_por_tipo.get(tipo_seleccionado, [])
                else:
                    # Usuario canceló, no hacer nada
                    return
            
            # Si llegamos aquí, hay un solo tipo o el usuario seleccionó uno
            if umbrales:
                GraficarUmbrales.draw_on_widget(widget, umbrales, unidad,sentido,tipo_pintado)