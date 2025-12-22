import pandas as pd
from datetime import datetime
from models.DatosModel import DatosModel
from utils.common.metodosGenerales import MetodosGenerales
class DatosController:
    
    def ctrlObtenerDataPrismasMarcados(proyecto_id, tabla, idzona, prismas, tipovelocidad, estado, decimales):
        tabladb = f"prismas{proyecto_id}"
        if tabla == tabladb:
            if tipovelocidad == 0: # velocidad solo positiva
                respuesta = DatosModel.mdlObtenerDataPrismasPositiva(tabla, idzona, "PRISMAS", prismas, estado, decimales)
            else: # velocidad ambas
                respuesta = DatosModel.mdlObtenerDataPrismasAmbas(tabla, idzona, "PRISMAS", prismas, estado, decimales)
        else:
            if tipovelocidad == 0: # velocidad solo positiva
                respuesta = DatosModel.mdlObtenerDataPrismasPositiva(tabla, idzona, "PRISMAS", prismas, estado, decimales)
            else: # velocidad ambas
                respuesta = DatosModel.mdlObtenerDataPrismasAmbas(tabla, idzona, "PRISMAS", prismas, estado, decimales)
        return respuesta
    
    def ctrlObtenerInclinometros(proyecto_id, idzona, equipos, decimales):
        respuesta = DatosModel.mdlObtenerInclinometros(proyecto_id, idzona, equipos, decimales)
        return respuesta

    def ctrlObtenerPiezometrosCuerda(proyecto_id, idzona, equipos, decimales):
        datos = []
        for idequipo in equipos:
            resultado = DatosModel.mdlObtenerFormulaPiezometroCuerda(idequipo)
            if resultado[0] == 0:
                respuesta = DatosModel.mdlObtenerPiezometrosCuerda(proyecto_id, idzona, idequipo, decimales)
            else:
                respuesta = DatosModel.mdlObtenerPiezometrosCuerdaFormula(proyecto_id, idzona, idequipo, resultado[1], decimales)
            if respuesta:
                datos.extend(respuesta)
        return datos
    
    def ctrlObtenerPiezometrosManuales(proyecto_id, idzona, equipos, decimales):
        respuesta = DatosModel.mdlObtenerPiezometrosManuales(proyecto_id, idzona, equipos, decimales)
        return respuesta
    
    def ctrlObtenerPluviometros(proyecto_id, idzona, equipos, decimales):
        respuesta = DatosModel.mdlObtenerPluviometros(proyecto_id, idzona, equipos, decimales)
        return respuesta

    def ctrlObtenerCotasTerreno(proyecto_id, idzona, equipos, decimales):
        respuesta = DatosModel.mdlObtenerCotasTerreno(proyecto_id, idzona, equipos, decimales)
        return respuesta
    
    def ctrlObtenerCeldasAsentamiento(proyecto_id, idzona, equipos, decimales):
        respuesta = DatosModel.mdlObtenerCeldasAsentamiento(proyecto_id, idzona, equipos, decimales)
        return respuesta
    
    def ctrlObtenerAcelerografos(proyecto_id, idzona, equipos, decimales):
        respuesta = DatosModel.mdlObtenerAcelerografos(proyecto_id, idzona, equipos, decimales)
        return respuesta
    
    def ctrlObtenerSondajestdr(proyecto_id, idzona, equipos, decimales):
        respuesta = DatosModel.mdlObtenerSondajestdr(proyecto_id, idzona, equipos, decimales)
        return respuesta
    
    def ctrlObtenerEquiposAdicionales(proyecto_id, idzona, equipos, decimales):
        respuesta = DatosModel.mdlObtenerEquiposAdicionales(proyecto_id, idzona, equipos, decimales)
        return respuesta
    
    def ctrlRegistrarPrismasAutomatizadosUno(idproyecto, tipodata, archivo_prisma, encoding, idcompo, delimitador, chunksize=10000):
        datos_procesados = pd.DataFrame()
        equipos_unicos = set()  # Conjunto para almacenar nombres únicos de equipos
        try:
            chunks = pd.read_csv(archivo_prisma, encoding=encoding, sep=delimitador, chunksize=chunksize, header=0)
            for i, data_chunk in enumerate(chunks):
                # Limpiar caracteres no válidos en las columnas de ángulos
                data_chunk.iloc[:, 4] = data_chunk.iloc[:, 4].apply(lambda x: x.replace('ï¿½', '°') if isinstance(x, str) else x)
                data_chunk.iloc[:, 5] = data_chunk.iloc[:, 5].apply(lambda x: x.replace('ï¿½', '°') if isinstance(x, str) else x)
                # Convertir y formatear las fechas a %Y-%m-%d %H:%M:%S, omitiendo errores
                data_chunk.iloc[:, 3] = pd.to_datetime(data_chunk.iloc[:, 3], format="%d-%m-%Y %H:%M:%S", errors='coerce')\
                                        .dt.strftime("%Y-%m-%d %H:%M:%S")
                # Filtrar filas con fechas inválidas y filas completamente vacías
                data_chunk = data_chunk.dropna(subset=[data_chunk.columns[3]]).dropna(how='all')
                data_chunk = data_chunk.map(lambda x: x.strip() if isinstance(x, str) else x)
                # Extraer nombres únicos de equipos en la columna 2
                equipos_unicos.update(data_chunk.iloc[:, 1].dropna().unique())
                # Agregar datos procesados al DataFrame final
                datos_procesados = pd.concat([datos_procesados, data_chunk], ignore_index=True)
            # Convertir a lista si necesitas una lista de nombres de equipos únicos
            lista_equipos_unicos = list(equipos_unicos)
            # no permitir data duplicada
            unique_data = {(row[1], row[3]): row for row in datos_procesados.itertuples(index=False)}
            datalimpia = pd.DataFrame(unique_data.values())
            # Llamar al modelo con los datos procesados
            if tipodata == 1:  # actualizar
                respuesta = DatosModel.mdlRegistrarPrismasAutomatizadosUno(idproyecto, datalimpia)
            else:  # reemplazar
                respuesta = DatosModel.mdlRemplazarPrismasAutomatizadosUno(idproyecto, datalimpia, idcompo)
            return respuesta, lista_equipos_unicos
        except FileNotFoundError as e:
            print(f"Error: ", e)
            return False, []
        except pd.errors.ParserError as e:
            print(f"Error: ", e)
            return False, []
        except Exception as e:
            print(f"Error: ", e)
            return False, []
    
    def ctrlRegistrarPrismasAutomatizadosCinco(idproyecto, tipodata, archivo_prisma, encoding, idcompo, delimitador, chunksize=10000):
        datos_procesados = pd.DataFrame()
        equipos_unicos = set()

        try:
            chunks = pd.read_csv(archivo_prisma, encoding=encoding, sep=delimitador, chunksize=chunksize, header=0)
            for data_chunk in chunks:
                # Limpiar caracteres no válidos en las columnas de ángulos
                data_chunk.iloc[:, 21] = data_chunk.iloc[:, 21].apply(lambda x: x.replace('ï¿½', '°') if isinstance(x, str) else x)
                data_chunk.iloc[:, 22] = data_chunk.iloc[:, 22].apply(lambda x: x.replace('ï¿½', '°') if isinstance(x, str) else x)

                # Validar y formatear las fechas
                data_chunk.iloc[:, 0] = data_chunk.iloc[:, 0].apply(MetodosGenerales.validarFormatoFechaCargaPrismas)

                # Filtrar filas con fechas inválidas y filas completamente vacías
                data_chunk = data_chunk.dropna(subset=[data_chunk.columns[0]]).dropna(how='all')
                data_chunk = data_chunk.map(lambda x: x.strip() if isinstance(x, str) else x)
                # Extraer nombres únicos de equipos en la columna 2
                equipos_unicos.update(data_chunk.iloc[:, 1].dropna().unique())

                # Agregar datos procesados al DataFrame final
                datos_procesados = pd.concat([datos_procesados, data_chunk], ignore_index=True)

            # Convertir a lista si necesitas una lista de nombres de equipos únicos
            lista_equipos_unicos = list(equipos_unicos)
            # no permitir data duplicada
            unique_data = {(row[1], row[0]): row for row in datos_procesados.itertuples(index=False)}
            datalimpia = pd.DataFrame(unique_data.values())
            # Llamar al modelo con los datos procesados
            if tipodata == 1:  # actualizar
                respuesta = DatosModel.mdlRegistrarPrismasAutomatizadosCinco(idproyecto, datalimpia)
            else:  # reemplazar
                respuesta = DatosModel.mdlRemplazarPrismasAutomatizadosCinco(idproyecto, datalimpia, idcompo)

            return respuesta, lista_equipos_unicos

        except FileNotFoundError as e:
            print(f"Error: {e}")
            return False, []
        except pd.errors.ParserError as e:
            print(f"Error: {e}")
            return False, []
        except Exception as e:
            print(f"Error: {e}")
            return False, []
    
    def ctrlRegistrarPrismasAutomatizadosDos(idproyecto, tipodata, archivo_prisma, encoding, idcompo, delimitador, chunksize=10000):
        try:
            datos_chunks = []  # Lista para almacenar los chunks procesados
            equipos_unicos = set()  # Conjunto para almacenar nombres únicos de equipos
            # Leer el archivo CSV en bloques
            chunks = pd.read_csv(archivo_prisma, encoding=encoding, sep=delimitador, chunksize=chunksize, header=0)
            for i, data_chunk in enumerate(chunks):
                # Seleccionar solo las primeras 10 columnas
                data_copy = data_chunk.iloc[:, :9].copy()
                data_copy = data_copy.map(lambda x: x.strip() if isinstance(x, str) else x)
                if data_chunk.iloc[:, 9:13].isnull().any().any():
                    continue
                # Generar fecha con formato yy-mm-dd
                fecha = (
                    data_chunk.iloc[:, 11].astype(str) + "-" +  # Año
                    data_chunk.iloc[:, 10].astype(str).str.zfill(2) + "-" +  # Mes
                    data_chunk.iloc[:, 9].astype(str).str.zfill(2)  # Día
                )
                # Generar hora
                hora = (
                    data_chunk.iloc[:, 12].astype(str).str.zfill(2) + ":" +  # Hora
                    data_chunk.iloc[:, 13].astype(str).str.zfill(2) + ":00"  # Minutos + segundos fijos
                )
                # Agregar la nueva columna "Day" con la fecha y hora formateada
                data_copy["Day"] = fecha + " " + hora
                # Filtrar filas completamente vacías
                data_copy = data_copy.dropna(how='all')
                # Extraer nombres únicos de equipos en la columna 0
                equipos_unicos.update(data_copy.iloc[:, 0].dropna().unique())
                # Agregar el chunk procesado a la lista
                datos_chunks.append(data_copy)
            # Unir todos los datos procesados
            datos_procesados = pd.concat(datos_chunks, ignore_index=True) if datos_chunks else pd.DataFrame()
            # Convertir a lista si necesitas una lista de nombres de equipos únicos
            lista_equipos_unicos = list(equipos_unicos)
            # no permitir data duplicada
            unique_data = {(row[0], row[-1]): row for row in datos_procesados.itertuples(index=False)}
            datalimpia = pd.DataFrame(unique_data.values())
            # Llamar al modelo con los datos procesados
            if tipodata == 1:  # actualizar
                respuesta = DatosModel.mdlRegistrarPrismasAutomatizadosDos(idproyecto, datalimpia)
            else:  # reemplazar
                respuesta = DatosModel.mdlRemplazarPrismasAutomatizadosDos(idproyecto, datalimpia, idcompo)
            return respuesta, lista_equipos_unicos
        except FileNotFoundError as e:
            print(f"Error: ", e)
            return False, []
        except pd.errors.ParserError as e:
            print(f"Error: ", e)
            return False, []
        except Exception as e:
            print(f"Error: ", e)
            return False, []
    
    def ctrlRegistrarPrismasAutomatizadosTresantiguo(idproyecto, tipodata, archivo_prisma, encoding, idcompo, delimitador, chunksize=10000):
        try:
            datos_chunks = []  # Lista para almacenar los chunks procesados
            equipos_unicos = set()  # Conjunto para almacenar nombres únicos de equipos
            columnas_omitir = [2, 11, 14, 15, 16, 17]
            # Leer el archivo CSV en bloques
            chunks = pd.read_csv(archivo_prisma, encoding=encoding, sep=delimitador, chunksize=chunksize, header=0)
            for i, data_chunk in enumerate(chunks):
                # Seleccionar columnas a mantener
                todas_columnas = list(range(len(data_chunk.columns)))
                columnas_mantener = [col for col in todas_columnas if col not in columnas_omitir]
                data_copy = data_chunk.iloc[:, columnas_mantener].copy()
                data_copy = data_copy.map(lambda x: x.strip() if isinstance(x, str) else x)
                # Verificar si la columna de fecha tiene valores nulos
                if data_copy.iloc[:, 3].isnull().all():
                    continue
                # Procesar fechas - CORRECCIÓN: acceder a la columna correctamente
                fecha_str = data_copy.iloc[:, 3].astype(str)
                fecha_limpia = fecha_str.str.split('+').str[0].str.strip()
                # Crear columna Time con fechas formateadas
                data_copy["Time"] = pd.NaT  # Inicializar columna con valores NaT
                # Procesar cada fecha individualmente
                for idx, fecha in enumerate(fecha_limpia):
                    try:
                        try:
                            fecha_obj = datetime.strptime(fecha, '%Y-%m-%d %H:%M:%S.%f')
                        except ValueError:
                            fecha_obj = datetime.strptime(fecha, '%Y-%m-%d %H:%M:%S')
                        data_copy.loc[idx, "Time"] = fecha_obj.strftime('%Y-%m-%d %H:%M:%S')
                    except Exception:
                        pass
                # Filtrar filas completamente vacías
                data_copy = data_copy.dropna(how='all')
                # Extraer nombres únicos de equipos en la columna 0
                equipos_unicos.update(data_copy.iloc[:, 0].dropna().unique())
                # Agregar el chunk procesado a la lista
                datos_chunks.append(data_copy)
            # Unir todos los datos procesados
            datos_procesados = pd.concat(datos_chunks, ignore_index=True) if datos_chunks else pd.DataFrame()
            # Convertir a lista si necesitas una lista de nombres de equipos únicos
            lista_equipos_unicos = list(equipos_unicos)
            # no permitir data duplicada
            unique_data = {(row[0], row[4]): row for row in datos_procesados.itertuples(index=False)}
            datalimpia = pd.DataFrame(unique_data.values())
            # Llamar al modelo con los datos procesados
            if tipodata == 1:  # actualizar
                respuesta = DatosModel.mdlRegistrarPrismasAutomatizadosTres(idproyecto, datalimpia)
            else:  # reemplazar
                respuesta = DatosModel.mdlRemplazarPrismasAutomatizadosTres(idproyecto, datalimpia, idcompo)
            return respuesta, lista_equipos_unicos
        except FileNotFoundError as e:
            print(f"Error: ", e)
            return False, []
        except pd.errors.ParserError as e:
            print(f"Error: ", e)
            return False, []
        except Exception as e:
            print(f"Error: ", e)
            return False, []
    
    def ctrlRegistrarPrismasAutomatizadosTres(idproyecto, tipodata, archivo_prisma, encoding, idcompo, delimitador):
        if tipodata == 1:  # actualizar
            respuesta, equipos_unicos = DatosModel.mdlRegistrarPrismasAutomatizadosTres(idproyecto, archivo_prisma, encoding, delimitador)
        else:  # reemplazar
            respuesta, equipos_unicos = DatosModel.mdlRemplazarPrismasAutomatizadosTres(idproyecto, archivo_prisma, encoding, delimitador, idcompo)
        return respuesta, equipos_unicos
    
    def ctrlRegistrarPrismasAutomatizadosCuatro(idproyecto, tipodata, archivo_prisma, encoding, idcompo, delimitador, chunksize=10000):
        datos_procesados = pd.DataFrame()
        equipos_unicos = set()  # Conjunto para almacenar nombres únicos de equipos
        # Lee el archivo CSV en bloques, omitiendo la primera fila como encabezado
        try:
            chunks = pd.read_csv(archivo_prisma, encoding=encoding, sep=delimitador, chunksize=chunksize, header=0)
            for i, data_chunk in enumerate(chunks):
                # Convertir y formatear las fechas a %Y-%m-%d %H:%M:%S, omitiendo errores
                data_chunk.iloc[:, 2] = pd.to_datetime(data_chunk.iloc[:, 2], format="%d-%m-%Y %H:%M:%S", errors='coerce')\
                            .dt.strftime("%Y-%m-%d %H:%M:%S")
                # Filtrar filas con fechas inválidas y filas completamente vacías
                data_chunk = data_chunk.dropna(subset=[data_chunk.columns[2]]).dropna(how='all')
                data_chunk = data_chunk.map(lambda x: x.strip() if isinstance(x, str) else x)
                # Extraer nombres únicos de equipos en la columna 2
                equipos_unicos.update(data_chunk.iloc[:, 1].dropna().unique())
                # Agregar datos procesados al DataFrame final
                datos_procesados = pd.concat([datos_procesados, data_chunk], ignore_index=True)
            # Convertir a lista si necesitas una lista de nombres de equipos únicos
            lista_equipos_unicos = list(equipos_unicos)
            # no permitir data duplicada
            unique_data = {(row[1], row[2]): row for row in datos_procesados.itertuples(index=False)}
            datalimpia = pd.DataFrame(unique_data.values())
            # Llamar al modelo con los datos procesados
            if tipodata == 1:  # actualizar
                respuesta = DatosModel.mdlRegistrarPrismasAutomatizadosCuatro(idproyecto, datalimpia)
            else:  # reemplazar
                respuesta = DatosModel.mdlRemplazarPrismasAutomatizadosCuatro(idproyecto, datalimpia, idcompo)
            return respuesta, lista_equipos_unicos
        except FileNotFoundError as e:
            print(f"Error: ", e)
            return False, []
        except pd.errors.ParserError as e:
            print(f"Error: ", e)
            return False, []
        except Exception as e:
            print(f"Error: ", e)
            return False, []
    
    def ctrlRegistrarInclinometro(id_proyecto,datos):
        respueta = DatosModel.mdlRegistrarInclinometro(id_proyecto,datos)
        return respueta
        
    def ctrlRegistrarEquipoZona(idproyecto, idcomponente, equipos,tabla, tipo):
        respuesta, prismasnuevos = DatosModel.mdlRegistrarEquipoZona(idcomponente, tabla, equipos,tipo)
        return respuesta, prismasnuevos
    
    def ctrlObtenerPrismasDataExportar(proyectoid, tabla, idzona, prisma, tipovelocidad, fechaini, fechafin):
        tabladb = f"prismas{proyectoid}"
        if tabla == tabladb:
            if tipovelocidad == 0: # velocidad solo positiva
                respuesta = DatosModel.mdlObtenerPrismaDataPositivaFechas(tabla, idzona, "PRISMAS", prisma, fechaini, fechafin)
            else: # velocidad ambas
                respuesta = DatosModel.mdlObtenerPrismaDataAmbasFechas(tabla, idzona, "PRISMAS", prisma, fechaini, fechafin)
        else:
            if tipovelocidad == 0: # velocidad solo positiva
                respuesta = DatosModel.mdlObtenerPrismaDataPositivaFechas(tabla, idzona, "PRISMAS", prisma, fechaini, fechafin)
            else: # velocidad ambas
                respuesta = DatosModel.mdlObtenerPrismaDataAmbasFechas(tabla, idzona, "PRISMAS", prisma, fechaini, fechafin)
        return respuesta
    
    def ctrlObtenerDataExportarPrismas(tabla, nameprismas, fechaini, fechafin):
        respuesta = DatosModel.mdlObtenerDataExportarPrismas(tabla, nameprismas, fechaini, fechafin)
        return respuesta
    
    def ctrlObtenerInfoExportarInclinometro(idcomponente, tipoequipo, idinstrumento):
        respuesta = DatosModel.mdlObtenerInfoExportarInclinometro(idcomponente, tipoequipo, idinstrumento)
        return respuesta
    
    def ctrlObtenerDataExportarInclinometro(idproyecto, idencabezado):
        respuesta = DatosModel.mdlObtenerDataExportarInclinometro(idproyecto, idencabezado)
        return respuesta
    
    def ctrlTraerInfoPiezometro(tipo, idcomponente, tipoequipo, idinstrumento):
        if tipo == "Automatizado":
            respuesta = DatosModel.mdlTraerInfoPiezometroCuerda(idcomponente, tipoequipo, idinstrumento)
        else:
            respuesta = DatosModel.mdlTraerInfoPiezometroManual(idcomponente, tipoequipo, idinstrumento)
        return respuesta
    
    def ctrlListarDataPiezometrosProyecto(tipo, idproyecto, idcomponente, idinstrumento, fechaini, fechafin):
        if tipo == "Automatizado":
            datapiezo = DatosModel.mdlDataExportarPiezometrosCuerda(idproyecto, idcomponente, idinstrumento, fechaini, fechafin)
        else:
            datapiezo = DatosModel.mdlDataExportarPiezometrosManual(idproyecto, idcomponente, idinstrumento, fechaini, fechafin)
        return datapiezo
    
    def ctrlTraerInfoPluviometro(idcomponente, tipoequipo, idinstrumento):
        respuesta = DatosModel.mdlTraerInfoPluviometro(idcomponente, tipoequipo, idinstrumento)
        return respuesta
    
    def ctrlListarDataPluviometro(idproyecto, idcomponente, idinstrumento):
        datapiezo = DatosModel.mdlDataExportarPluviometro(idproyecto, idcomponente, idinstrumento)
        return datapiezo
    
    def ctrlTraerInfoCeldaAsentamiento(idcomponente, tipoequipo, idinstrumento):
        respuesta = DatosModel.mdlTraerInfoCeldaAsentamiento(idcomponente, tipoequipo, idinstrumento)
        return respuesta
    
    def ctrlListarDataCeldaAsentamiento(idproyecto, idcomponente, idinstrumento, fechaini, fechafin):
        datapiezo = DatosModel.mdlDataExportarCeldaAsentamiento(idproyecto, idcomponente, idinstrumento, fechaini, fechafin)
        return datapiezo
    
    def ctrlTraerInfoAcelerografo(idcomponente, tipoequipo, idinstrumento):
        respuesta = DatosModel.mdlTraerInfoAcelerografo(idcomponente, tipoequipo, idinstrumento)
        return respuesta
    
    def ctrlListarDataAcelerografo(idproyecto, idcomponente, idinstrumento, fechaini, fechafin):
        datapiezo = DatosModel.mdlDataExportarAcelerografo(idproyecto, idcomponente, idinstrumento, fechaini, fechafin)
        return datapiezo
    
    def ctrlObtenerInfoExportarSondajetdr(idproyecto, idcomponente, idinstrumento):
        respuesta = DatosModel.mdlObtenerInfoExportarSondajetdr(idproyecto, idcomponente, idinstrumento)
        return respuesta
    
    def ctrlObtenerDataExportarSondajetdr(idproyecto, idtdr, fecha):
        respuesta = DatosModel.mdlObtenerDataExportarSondajetdr(idproyecto, idtdr, fecha)
        return respuesta
    
    def ctrlListarDataCotaTerreno(idproyecto, idcomponente, idinstrumento):
        datapiezo = DatosModel.mdlDataExportarCotaTerreno(idproyecto, idcomponente, idinstrumento)
        return datapiezo
    