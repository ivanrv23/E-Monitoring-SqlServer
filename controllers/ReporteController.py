from models.ReporteModel import ReporteModel
from utils.common.metodosGenerales import MetodosGenerales

class ReporteController:
    
    def ctrlGuardarDatosReporte(imagen_blob, texto_titulo, texto_descripcion, proyectoid, tipo, orden, idequipo, anexo):
        # comprobar si existe gráfica para actualizar
        inclino = None
        if idequipo is not None: # traer nombre inclinometro
            inclinome = ReporteModel.mdlTraerNombreEquipoReporte(proyectoid, idequipo)
            if inclinome is not None:
                inclino = inclinome[0]
        respuesta = ReporteModel.mdlGuardarDatosReporte(imagen_blob, texto_titulo, texto_descripcion, proyectoid, tipo, orden, inclino, anexo)
        return respuesta
    
    def ctrlObtenerTiposGraficas(proyecto):
        respuesta = ReporteModel.mdlObtenerTiposGraficas(proyecto)
        return respuesta
    
    def ctrlObtenerTotalGraficas(proyecto, tipo):
        respuesta = ReporteModel.mdlObtenerTotalGraficas(proyecto, tipo)
        return respuesta
    
    def ctrlObtenerlistaGraficosAnexos(proyecto):
        respuesta = ReporteModel.mdlObtenerlistaGraficosAnexos(proyecto)
        return respuesta
    
    def ctrlObtenerlistaUmbralesAnexos(proyecto):
        data = []
        prismas = ReporteModel.mdlObtenerlistaUmbralPrismasAnexos(proyecto)
        piezometros = ReporteModel.mdlObtenerlistaUmbralPiezometrosAnexos(proyecto)
        inclino = ReporteModel.mdlObtenerlistaUmbralesInclinometrosAnexos(proyecto)
        celdas = ReporteModel.mdlObtenerlistaUmbralCeldasAnexos(proyecto)
        if prismas:
            data.extend(prismas)
        if piezometros:
            data.extend(piezometros)
        if inclino:
            data.extend(inclino)
        if celdas:
            data.extend(celdas)
        return data

    def ctrlEliminarGrafica(img_id):
        return ReporteModel.mdlEliminarGrafica(img_id)
    
    def ctrlEliminarUmbralReporte(id, tabla):
        return ReporteModel.mdlEliminarUmbralReporte(id, tabla)
    
    def ctrlListarDatosReporteGeneral(idproyecto):
        respuesta = ReporteModel.mdlListarDatosReporteGeneral(idproyecto)
        return respuesta
    
    def ctrlRegistroNuevoReporte(proyectoid, encabezado, titulo, lugar, para, de, cc, fecha, asunto, texto, comentario, conclusiones, recomendacion):
        respuesta = ReporteModel.mdlRegistroNuevoReporte(proyectoid, encabezado, titulo, lugar, para, de, cc, fecha, asunto, texto, comentario, conclusiones, recomendacion)
        return respuesta
    
    def ctrlActualizarReporte(proyectoid, encabezado, titulo, lugar, para, de, cc, fecha, asunto, texto, comentario, conclusiones, recomendacion):
        respuesta = ReporteModel.mdlActualizarReporte(proyectoid, encabezado, titulo, lugar, para, de, cc, fecha, asunto, texto, comentario, conclusiones, recomendacion)
        return respuesta
    
    def ctrlObtenerDataAnexos(proyectoid):
        respuesta = ReporteModel.mdlObtenerDataAnexos(proyectoid)
        prismaa = ReporteModel.mdlObtenerInfoPrismasAutoAnexos(proyectoid)
        prismam = ReporteModel.mdlObtenerInfoPrismasManualAnexos(proyectoid)
        prismas = prismaa + prismam
        return respuesta, prismas
    
    def ctrlGuardarDataReporteAnexo1(datos):
        respuesta = ReporteModel.mdlGuardarDataReporteAnexo1(datos)
        return respuesta
    
    def ctrlObtenerDataAnexo2(proyectoid):
        respuesta = ReporteModel.mdlObtenerDataAnexo2(proyectoid)
        return respuesta
    
    def ctrlGuardarDataReporteAnexo2(datos):
        respuesta = ReporteModel.mdlGuardarDataReporteAnexo2(datos)
        return respuesta
    
    def ctrlObtenerGraficasReporteTipo(proyecto, tipo, anexo='anexo2'):
        respuesta = ReporteModel.mdlObtenerGraficasReporteTipo(proyecto, tipo,anexo)
        return respuesta
    
    # CONSULTAR RESPONSABLES
    # GUARDAR LISTA RESPONSABLES EN EL CONTROLADOR
    def ctrlObtenerResponsables():
        datos = ReporteModel.mdlObtenerResponsables()
        return datos
    
    # GUARDAR LISTA RESPONSABLES EN EL CONTROLADOR
    def ctrlGuardarResponsables(datos_guardados):
        respuesta = ReporteModel.mdlGuardarResponsables(datos_guardados)
        return respuesta
    
    # OBTENER COORDENADAS EQUIPOS
    def ctrlObtenerCoordenadasEquipos(proyecto, tipo):
        respuesta = ReporteModel.mdlObtenerCoordenadasEquipos(proyecto, tipo)
        return respuesta
    
    def ctrlEliminardatatabla(tabla):
        respuesta = ReporteModel.mdlEliminardatatabla(tabla)
        return respuesta
    
    def ctrlGuardarUmbralesEqupisTipo(datos):
        respuesta = ReporteModel.mdlGuardarUmbralesEqupisTipo(datos)
        return respuesta
    
    def ctrlObtenerUmbralesEquiposTipo(proyectoID,id_equipo):
        respuesta = ReporteModel.mdlObtenerUmbralesEquiposTipo(proyectoID,id_equipo)
        return respuesta
    
    def ctrlGuardarInformacionReporte(data):
        respuesta = ReporteModel.mdlGuardarInformacionReporte(data)
        return respuesta
    
    def ctrlObtenerDatosFirma(proyectoid):
        respuesta = ReporteModel.mdlObtenerDatosFirma(proyectoid)
        return respuesta
        
    def ctrlRegistrarFirma(proyectoid, data):
        respuesta = ReporteModel.mdlRegistrarFirma(proyectoid, data)
        return respuesta
    
    def ctrlGuardarImagenReporte(data):
        respuesta = ReporteModel.mdlGuardarImagenReporte(data)
        return respuesta
    
    def ctrlObtenerListaPrismas(idproyecto,id_componente):
        # Obtener los datos de los prismas automáticos
        respuesta = ReporteModel.mdlObtenerListaPrismas(f'prismas{idproyecto}', 'PRISMAS', id_componente)
        # Filtrar respuestas que no sean None ni vacías
        respuestas_filtradas = []
        if respuesta:  # Verifica que no sea None ni vacío
            respuestas_filtradas.extend(respuesta)
        # Si no hay datos válidos, retornar None
        if not respuestas_filtradas:
            return None
        return respuestas_filtradas
    
    def ctrlObtenerListaInclinometros(data,id_componente):
        respuesta = ReporteModel.mdlObtenerListaInclinometros(data,id_componente)
        return respuesta
    
    def ctrlObtenerListaPiezometros(idproyecto,id_componente):
        # Obtener los datos de los prismas automáticos
        respuesta = ReporteModel.mdlObtenerListaPiezometros(idproyecto,f'piezometrocuerdas', 'PIEZOMETROCUERDA',id_componente)

        # Obtener los datos de los prismas manuales
        respuesta2 = ReporteModel.mdlObtenerListaPiezometros(idproyecto,f'piezometromanuales', 'PIEZOMETROMANUAL',id_componente)

        # Filtrar respuestas que no sean None ni vacías
        respuestas_filtradas = []

        if respuesta:  # Verifica que no sea None ni vacío
            respuestas_filtradas.extend(respuesta)

        if respuesta2:  # Verifica que no sea None ni vacío
            respuestas_filtradas.extend(respuesta2)

        # Si no hay datos válidos, retornar None
        if not respuestas_filtradas:
            return None

        # Devolver la estructura original (lista de respuestas)
        return respuestas_filtradas
    
    def ctrlObtenerListaCeldas(idproyecto,id_componente):
        respuesta = ReporteModel.mdlObtenerListaCeldas(idproyecto,id_componente)
        return respuesta
    
    def ctrlObtenerListaAcelerografos(idproyecto,id_componente):
        respuesta = ReporteModel.mdlObtenerListaAcelerografos(idproyecto,id_componente)
        return respuesta
    
    def ctrlObtenerListaSondajesTDR(idproyecto,id_componente):
        respuesta = ReporteModel.mdlObtenerListaSondajesTDR(idproyecto,id_componente)
        return respuesta
    
    def ctrlObtenerListaImagenesReporte(id_componente):
        respuesta = ReporteModel.mdlObtenerListaImagenesReporte(id_componente)
        return respuesta
    
    # OBETENER COMPONENETES
    def ctrlObtenerComponentes(proyecto_id):
        respuesta = ReporteModel.mdlObtenerObtenerComponentes(proyecto_id)
        return respuesta
    
    # -------------------------ANEXO 1---------------------------#
    def ctrlObtenerControlParametrosA1(idcomponente):
        respuesta = ReporteModel.mdlObtenerControlParametrosA1(idcomponente)
        return respuesta
    
    def ctrlObtenerCondicionesFisicasA1(idcomponente):
        respuesta = ReporteModel.mdlObtenerCondicionesFisicasA1(idcomponente)
        return respuesta
    
    def ctrlObtenerOperatividadEquiposA1(idcomponente):
        respuesta = ReporteModel.mdlObtenerOperatividadEquiposA1(idcomponente)
        return respuesta
    
    def ctrlObtenerObservacionesA1(idcomponente):
        respuesta = ReporteModel.mdlObtenerObservacionesA1(idcomponente)
        return respuesta
    
    # -------------------------ANEXO 2---------------------------#
    def ctrlObtenerUbicacionInstrumentacionGeotecnica(idcomponente):
        respuesta = ReporteModel.mdlObtenerUbicacionInstrumentacionGeotecnica(idcomponente)
        return respuesta  

    def ctrlObtenerInstrumentacionGeotecnica(idcomponente):
        respuesta = ReporteModel.mdlObtenerInstrumentacionGeotecnica(idcomponente)
        return respuesta
    
    def ctrlObtenerObservacionesA2(idcomponente):
        respuesta = ReporteModel.mdlObtenerObservacionesA2(idcomponente)
        return respuesta
    
    # -------------------------REPORTE A1 - A2---------------------------#
    def ctrlObtenerResumenEjecutivoAnexo1(idcomponente):
        respuesta = ReporteModel.mdlObtenerResumenEjecutivoAnexo1(idcomponente)
        return respuesta
    
    def ctrlObtenerTablaResumenEjecutivoAnexo1(idcomponentes):
        respuesta = ReporteModel.mdlObtenerTablaResumenEjecutivoAnexo1(idcomponentes)
        return respuesta
    
    def ctrlObtenerParametrosAnexo1(idcomponentes):
        respuesta = ReporteModel.mdlObtenerParametrosAnexo1(idcomponentes)
        return respuesta
    
    def ctrlObtenerCondicionesFisicasAnexo1(idcomponentes):
        respuesta = ReporteModel.mdlObtenerCondicionesFisicasAnexo1(idcomponentes)
        return respuesta
    
    def ctrlObtenerOperatividadEquipos(idcomponentes):
        respuesta = ReporteModel.mdlObtenerOperatividadEquipos(idcomponentes)
        return respuesta
    
    def ctrlObtenerObservacionesAnexo1(idcomponentes):
        respuesta = ReporteModel.mdlObtenerObservacionesAnexo1(idcomponentes)
        return respuesta
    
    #------
    def ctrlObtenerResumenEjecutivoAnexo2(idcomponente):
        respuesta = ReporteModel.mdlObtenerResumenEjecutivoAnexo2(idcomponente)
        return respuesta
    
    def ctrlObtenerTablaResumenEjecutivoAnexo2(idcomponentes):
        respuesta = ReporteModel.mdlObtenerTablaResumenEjecutivoAnexo2(idcomponentes)
        return respuesta
    
    def ctrlObtenerInstrumentacionAnexo2(idcomponentes):
        respuesta = ReporteModel.mdlObtenerInstrumentacionAnexo2(idcomponentes)
        return respuesta
    
    def ctrlObtenerInterpretacionValoresA2(instrumen, idcompo):
        respuesta = ReporteModel.mdlObtenerInterpretacionValoresA2(instrumen, idcompo)
        return respuesta
    
    def ctrlObtenerTablaResumenPrismas(proyecto_id,idcomponente):
        tabla = f'prismas{proyecto_id}'
        datos_automatizado = ReporteModel.mdlDatosVI3DPositivas(idcomponente, tabla, "Automatizado")
        if datos_automatizado:
            return datos_automatizado
        else:
            return None

    def ctrlObtenerObservacionesAnexo2(idcomponentes):
        respuesta = ReporteModel.mdlObtenerObservacionesAnexo2(idcomponentes)
        return respuesta
    
    def ctrlGuardarDataGeneralAnexos(datos, idproyecto, tiporeporte):
        respuesta = ReporteModel.mdlGuardarDataGeneralAnexos(datos, idproyecto, tiporeporte)
        return respuesta
    
    def ctrlListarDatosGeneralAnexos(idproyecto, tipoanexo):
        respuesta = ReporteModel.mdlListarDatosGeneralAnexos(idproyecto, tipoanexo)
        return respuesta
    
    def ctrlGuardarResumenEjecutivoAnexo1(datos, idcomponente):
        respuesta = ReporteModel.mdlGuardarResumenEjecutivoAnexo1(datos, idcomponente)
        return respuesta
    
    def ctrlObtenerImagenesGraficasReporte(idcomponente, tipo_equipo, anexo):
        respuesta = ReporteModel.mdlObtenerImagenesGraficasReporte(idcomponente, tipo_equipo, anexo)
        return respuesta
    
    def ctrlGuardarResumenEjecutivoAnexo2(datos, idcomponente):
        respuesta = ReporteModel.mdlGuardarResumenEjecutivoAnexo2(datos, idcomponente)
        return respuesta
    
    def ctrlListarImagenesReportes(idproyecto, tiporeporte):
        respuesta = ReporteModel.mdlListarImagenesReportes(idproyecto, tiporeporte)
        return respuesta
    
    def ctrlEliminarGraficaReporte(idimagen):
        respuesta = ReporteModel.mdlEliminarGraficaReporte(idimagen)
        return respuesta
    
    def ctrlGuardarParametrosAnexo1(idcomponente, datos):
        parametros = []
        for fila in datos:
            descripcion_parametro = fila[0]  # DESCRIPCIÓN
            valor_parametro = fila[1]  # PARÁMETRO 1
            unidad_parametro = fila[2]  # PARÁMETRO 2
            condicion_parametro = fila[3]  # CONDICIÓN ACTUAL
            comentario_parametro = fila[4]  # COMENTARIOS
            # Crear un diccionario o tupla para cada fila
            parametro = (
                idcomponente,
                descripcion_parametro,
                valor_parametro,
                unidad_parametro,
                condicion_parametro,
                comentario_parametro
            )
            # Añadir la fila a la lista de parámetros
            parametros.append(parametro)
        if parametros:
            respuesta = ReporteModel.mdlGuardarParametrosAnexo1(parametros, idcomponente)
            return respuesta
        else:
            return False
    
    def ctrlGuardarCondicionesAnexo1(idcomponente, datos):
        condiciones_fisicas = []
        for fila in datos:
            condicion_talud = fila[0]  # CONDICION
            estado_condicion = fila[1]  # ESTADO CONDICION
            comentario_condicion = fila[2]  # COMENTARIO
            tipo_condicion = fila[3]  # TIPO
            # Crear un diccionario o tupla para cada fila
            condicion_fisica = (
                idcomponente,  # id_componente
                condicion_talud,
                estado_condicion,
                comentario_condicion,
                tipo_condicion
            )
            # Añadir la fila a la lista de parámetros
            condiciones_fisicas.append(condicion_fisica)
        if condiciones_fisicas:
            respuesta = ReporteModel.mdlGuardarCondicionesAnexo1(condiciones_fisicas, idcomponente)
            return respuesta
        else:
            return respuesta
    
    def ctrlGuardarOperatividadAnexo1(idcomponente, datos):
        operatividad_equipos = []
        for fila in datos:
            instrumentacion = fila[0]  # INTRUMENTO
            condicion_actual = fila[1]  # CONDICION ACTUAL
            cantidad = fila[2]  # CANTIDAD
            operatividad = fila[3]  # OPERATIVIDAD
            comentario = fila[4] # COMENTARIO
            # Crear un diccionario o tupla para cada fila
            operatividad_equipo = (
                idcomponente,
                instrumentacion,
                condicion_actual,
                cantidad,
                operatividad,
                comentario
            )
            # Añadir la fila a la lista de parámetros
            operatividad_equipos.append(operatividad_equipo)
        if operatividad_equipos:
            respuesta = ReporteModel.mdlGuardarOperatividadAnexo1(operatividad_equipos, idcomponente)
            return respuesta
        else:
            return False
    
    def ctrlGuardarObservacionesAnexo1(idcomponente, datos):
        observaciones_equipos = []
        for fila in datos:
            descripcion = fila[0]  # observacion
            condicion_actual = fila[1]  # CONDICION ACTUAL
            medidas = fila[2]  # MEDIDAS
            plazo = fila[3]  # PLAZO
            comentario = fila[4] # COMENTARIO
            responsable = fila[5] # RESPONSABLE
            tipo = fila[6] # TIPO
            # Crear un diccionario o tupla para cada fila
            observacion_equipo = (
                idcomponente,
                descripcion,
                condicion_actual,
                medidas,
                plazo,
                comentario,
                responsable,
                tipo
            )
            # Añadir la fila a la lista de parámetros
            observaciones_equipos.append(observacion_equipo)
        if observaciones_equipos:
            respuesta = ReporteModel.mdlGuardarObservacionesAnexo1(observaciones_equipos, idcomponente)
            return respuesta
        else:
            return False
    
    def ctrlGuardarInstrumentacionGeotecnicaA2(idcomponente, datos):
        instrumentacion_geotecnica = []
        for fila in datos:
            intrumentacion = fila[0]  # DESCRIPCIÓN
            cantidad_autorizado = fila[1]  # AUTORIZADO - CANTIDAD OPERATIVO
            operatividad_autorizado = fila[2]  # AUTORIZADO - OPERATIVIDAD
            cantidad_adicional = fila[3]  # ADICIONAL - CANTIDAD OPERATIVO
            operatividad_adicional = fila[4]  # ADICIONAL - OPERATIVIDAD
            frecuencia_monitoreo = fila[5]  # FRECUENCIA - MONITOREO
            total_instrumentacion = MetodosGenerales.validarNuemroEntero(fila[1]) + MetodosGenerales.validarNuemroEntero(fila[3])
            # Crear un diccionario o tupla para cada fila
            instrumento = (
                idcomponente,
                intrumentacion,
                cantidad_autorizado,
                operatividad_autorizado,
                cantidad_adicional,
                operatividad_adicional,
                total_instrumentacion,
                frecuencia_monitoreo
            )
            # Añadir la fila a la lista de parámetros
            instrumentacion_geotecnica.append(instrumento)
        if instrumentacion_geotecnica:
            respuesta = ReporteModel.mdlGuardarInstrumentacionAnexo2(instrumentacion_geotecnica, idcomponente)
            return respuesta
        else:
            return False
    
    def ctrlGuardarUbicacionesInstrumentacion(idcomponente, datos):
        datos_procesados = []
        for item in datos:
            instrumento = item['instrumento']
            ruta_imagen = item['imagen']
            row_id = item['id']
            tipo_instrumentacion = item['tipo_instrumentacion']
            # Convertir la imagen a blob usando el método proporcionado
            if ruta_imagen and ruta_imagen != "Sin imagen":
                blob = MetodosGenerales.convertir_imagen_a_blob(ruta_imagen)
            else:
                blob = None
            # Agregar los datos procesados a la nueva lista
            datos_procesados.append([row_id, idcomponente, instrumento, blob, tipo_instrumentacion])
        if datos_procesados:
            respuesta = ReporteModel.mdlGuardarUbicacionesInstrumentacion(datos_procesados, idcomponente)
            return respuesta
        else:
            return False
    
    def ctrlGuardarObservacionesAnexo2(idcomponente, datos):
        observaciones_anexo = []
        for fila in datos:
            descripcion = fila[0]  # observacion
            condicion_actual = fila[1]  # CONDICION ACTUAL
            medidas = fila[2]  # MEDIDAS
            plazo = fila[3]  # PLAZO
            comentario = fila[4] # COMENTARIO
            responsable = fila[5] # RESPONSABLE
            tipo = fila[6] # TIPO
            # Crear un diccionario o tupla para cada fila
            observacion = (
                idcomponente,
                descripcion,
                condicion_actual,
                medidas,
                plazo,
                comentario,
                responsable,
                tipo
            )
            # Añadir la fila a la lista de parámetros
            observaciones_anexo.append(observacion)
        if observaciones_anexo:
            respuesta = ReporteModel.mdlGuardarObservacionesAnexo2(observaciones_anexo, idcomponente)
            return respuesta
        else:
            return False
    