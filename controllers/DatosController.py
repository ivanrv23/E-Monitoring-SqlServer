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
        equipos_unicos = set()
        
        try:
            chunks = pd.read_csv(archivo_prisma, encoding=encoding, sep=delimitador, chunksize=chunksize, header=0)
            
            for i, data_chunk in enumerate(chunks):
                # 1. Limpiar caracteres no válidos en las columnas de ángulos
                # Usamos regex=False para evitar advertencias futuras de Pandas
                data_chunk.iloc[:, 4] = data_chunk.iloc[:, 4].apply(lambda x: x.replace('ï¿½', '°') if isinstance(x, str) else x)
                data_chunk.iloc[:, 5] = data_chunk.iloc[:, 5].apply(lambda x: x.replace('ï¿½', '°') if isinstance(x, str) else x)

                # --- INICIO AJUSTE PARA SQL SERVER DATETIME2(0) ---
                
                # 2. Convertir a objetos datetime primero (sin pasar a string todavía)
                # errors='coerce' transformará formatos irreconocibles en NaT (Not a Time)
                fechas_obj = pd.to_datetime(data_chunk.iloc[:, 3], format="%d-%m-%Y %H:%M:%S", errors='coerce')
                
                # 3. Filtrar: Eliminamos NaT y años antiguos/basura (< 1900)
                # Esto previene el error 22007 por "fuera de intervalo"
                mask_valida = fechas_obj.notna() & (fechas_obj.dt.year >= 1900)
                data_chunk = data_chunk[mask_valida].copy() # .copy() es importante para evitar warnings

                # 4. Formatear a String ISO 8601 estricto (Con la 'T')
                # Ejemplo resultado: "2024-05-20T14:30:00"
                # Al usar DATETIME2(0) en la BD, esto calza perfecto.
                data_chunk.iloc[:, 3] = fechas_obj[mask_valida].dt.strftime("%Y-%m-%dT%H:%M:%S")
                
                # --- FIN AJUSTE ---

                # 5. Limpieza final de espacios y nulos
                data_chunk = data_chunk.dropna(how='all')
                data_chunk = data_chunk.map(lambda x: x.strip() if isinstance(x, str) else x)
                
                # 6. Extraer nombres únicos de equipos
                equipos_unicos.update(data_chunk.iloc[:, 1].dropna().unique())
                
                # 7. Concatenar
                datos_procesados = pd.concat([datos_procesados, data_chunk], ignore_index=True)

            # Si tras el filtro no quedó nada, retornamos vacío
            if datos_procesados.empty:
                return False, []

            lista_equipos_unicos = list(equipos_unicos)
            
            # 8. Eliminar duplicados en memoria
            # Como ya formateamos la fecha con 'T' en el paso 4, la tupla será consistente
            unique_data = {(row[1], row[3]): row for row in datos_procesados.itertuples(index=False)}
            datalimpia = pd.DataFrame(unique_data.values())
            
            # 9. Llamar al modelo
            if tipodata == 1:  # actualizar
                respuesta = DatosModel.mdlRegistrarPrismasAutomatizadosUno(idproyecto, datalimpia)
            else:  # reemplazar
                respuesta = DatosModel.mdlRemplazarPrismasAutomatizadosUno(idproyecto, datalimpia, idcompo)
                
            return respuesta, lista_equipos_unicos

        except FileNotFoundError as e:
            print(f"Error Archivo no encontrado: {e}")
            return False, []
        except pd.errors.ParserError as e:
            print(f"Error Parseo Pandas: {e}")
            return False, []
        except Exception as e:
            print(f"Error General: {e}")
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

                # --- REGLAS DE ORO: ISO 'T' + FILTRO 1900 ---
                # 1. Convertir a datetime (vectorizado, sin apply externo)
                fechas_obj = pd.to_datetime(data_chunk.iloc[:, 0], errors='coerce')
                
                # 2. Filtrar: Validar no nulos y Año >= 1900 (Evita error SQL 22007)
                mask_valida = fechas_obj.notna() & (fechas_obj.dt.year >= 1900)
                data_chunk = data_chunk[mask_valida].copy()

                # 3. Formatear Estricto con 'T'
                data_chunk.iloc[:, 0] = fechas_obj[mask_valida].dt.strftime("%Y-%m-%dT%H:%M:%S")
                # --------------------------------------------

                # Limpieza final
                data_chunk = data_chunk.dropna(how='all')
                data_chunk = data_chunk.map(lambda x: x.strip() if isinstance(x, str) else x)
                
                # Extraer nombres únicos
                equipos_unicos.update(data_chunk.iloc[:, 1].dropna().unique())

                # Agregar datos procesados
                datos_procesados = pd.concat([datos_procesados, data_chunk], ignore_index=True)

            if datos_procesados.empty:
                return False, []

            lista_equipos_unicos = list(equipos_unicos)
            
            # No permitir duplicados (Usando la fecha formateada con 'T')
            unique_data = {(row[1], row[0]): row for row in datos_procesados.itertuples(index=False)}
            datalimpia = pd.DataFrame(unique_data.values())
            
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
            datos_chunks = []
            equipos_unicos = set()
            
            chunks = pd.read_csv(archivo_prisma, encoding=encoding, sep=delimitador, chunksize=chunksize, header=0)
            for i, data_chunk in enumerate(chunks):
                data_copy = data_chunk.iloc[:, :9].copy()
                data_copy = data_copy.map(lambda x: x.strip() if isinstance(x, str) else x)
                
                if data_chunk.iloc[:, 9:13].isnull().any().any():
                    continue
                
                # --- REGLAS DE ORO: ISO 'T' + FILTRO 1900 ---
                # Construcción manual de la fecha para conversión
                # Formato temporal para parseo: YYYY-MM-DD HH:MM:SS
                fechas_temp = (
                    data_chunk.iloc[:, 11].astype(str) + "-" + 
                    data_chunk.iloc[:, 10].astype(str).str.zfill(2) + "-" + 
                    data_chunk.iloc[:, 9].astype(str).str.zfill(2) + " " +
                    data_chunk.iloc[:, 12].astype(str).str.zfill(2) + ":" + 
                    data_chunk.iloc[:, 13].astype(str).str.zfill(2) + ":00"
                )

                # 1. Convertir a objetos datetime
                fechas_obj = pd.to_datetime(fechas_temp, errors='coerce')

                # 2. Filtrar Años < 1900 y NaT
                mask_valida = fechas_obj.notna() & (fechas_obj.dt.year >= 1900)
                
                # Aplicar filtro al chunk original (importante para mantener alineación)
                data_copy = data_copy[mask_valida].copy()
                
                # 3. Asignar formato ISO estricto con 'T'
                data_copy["Day"] = fechas_obj[mask_valida].dt.strftime("%Y-%m-%dT%H:%M:%S")
                # --------------------------------------------

                data_copy = data_copy.dropna(how='all')
                equipos_unicos.update(data_copy.iloc[:, 0].dropna().unique())
                datos_chunks.append(data_copy)
            
            datos_procesados = pd.concat(datos_chunks, ignore_index=True) if datos_chunks else pd.DataFrame()
            
            if datos_procesados.empty:
                return False, []

            lista_equipos_unicos = list(equipos_unicos)
            
            # Duplicados: clave compuesta (Equipo, FechaISO)
            unique_data = {(row[0], row[-1]): row for row in datos_procesados.itertuples(index=False)}
            datalimpia = pd.DataFrame(unique_data.values())
            
            if tipodata == 1:
                respuesta = DatosModel.mdlRegistrarPrismasAutomatizadosDos(idproyecto, datalimpia)
            else:
                respuesta = DatosModel.mdlRemplazarPrismasAutomatizadosDos(idproyecto, datalimpia, idcompo)
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
    
    def ctrlRegistrarPrismasAutomatizadosTresantiguo(idproyecto, tipodata, archivo_prisma, encoding, idcompo, delimitador, chunksize=10000):
        try:
            datos_chunks = []
            equipos_unicos = set()
            columnas_omitir = [2, 11, 14, 15, 16, 17]
            
            chunks = pd.read_csv(archivo_prisma, encoding=encoding, sep=delimitador, chunksize=chunksize, header=0)
            for i, data_chunk in enumerate(chunks):
                todas_columnas = list(range(len(data_chunk.columns)))
                columnas_mantener = [col for col in todas_columnas if col not in columnas_omitir]
                data_copy = data_chunk.iloc[:, columnas_mantener].copy()
                data_copy = data_copy.map(lambda x: x.strip() if isinstance(x, str) else x)
                
                if data_copy.iloc[:, 3].isnull().all():
                    continue

                # --- REGLAS DE ORO: ISO 'T' + FILTRO 1900 + OPTIMIZACIÓN VECTORIZADA ---
                # Limpieza de string de fecha (eliminar zona horaria '+' y espacios)
                fechas_series = data_copy.iloc[:, 3].astype(str).str.split('+').str[0].str.strip()
                
                # 1. Convertir a datetime (Vectorizado es 100x más rápido que el bucle for original)
                # Intentamos inferir el formato automáticamente, manejando milisegundos si existen
                fechas_obj = pd.to_datetime(fechas_series, errors='coerce')
                
                # 2. Filtrar Años < 1900 y NaT
                mask_valida = fechas_obj.notna() & (fechas_obj.dt.year >= 1900)
                data_copy = data_copy[mask_valida].copy()

                # 3. Formato ISO estricto con 'T'
                data_copy["Time"] = fechas_obj[mask_valida].dt.strftime("%Y-%m-%dT%H:%M:%S")
                # --------------------------------------------

                data_copy = data_copy.dropna(how='all')
                equipos_unicos.update(data_copy.iloc[:, 0].dropna().unique())
                datos_chunks.append(data_copy)
            
            datos_procesados = pd.concat(datos_chunks, ignore_index=True) if datos_chunks else pd.DataFrame()
            
            if datos_procesados.empty:
                return False, []

            lista_equipos_unicos = list(equipos_unicos)
            
            unique_data = {(row[0], row[-1]): row for row in datos_procesados.itertuples(index=False)}
            datalimpia = pd.DataFrame(unique_data.values())
            
            if tipodata == 1:
                respuesta = DatosModel.mdlRegistrarPrismasAutomatizadosTres(idproyecto, datalimpia)
            else:
                respuesta = DatosModel.mdlRemplazarPrismasAutomatizadosTres(idproyecto, datalimpia, idcompo)
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
    
    def ctrlRegistrarPrismasAutomatizadosTres(idproyecto, tipodata, archivo_prisma, encoding, idcompo, delimitador):
        if tipodata == 1:  # actualizar
            respuesta, equipos_unicos = DatosModel.mdlRegistrarPrismasAutomatizadosTres(idproyecto, archivo_prisma, encoding, delimitador)
        else:  # reemplazar
            respuesta, equipos_unicos = DatosModel.mdlRemplazarPrismasAutomatizadosTres(idproyecto, archivo_prisma, encoding, delimitador, idcompo)
        return respuesta, equipos_unicos
    
    def ctrlRegistrarPrismasAutomatizadosCuatro(idproyecto, tipodata, archivo_prisma, encoding, idcompo, delimitador, chunksize=10000):
        datos_procesados = pd.DataFrame()
        equipos_unicos = set()
        
        try:
            chunks = pd.read_csv(archivo_prisma, encoding=encoding, sep=delimitador, chunksize=chunksize, header=0)
            for i, data_chunk in enumerate(chunks):
                # --- REGLAS DE ORO: ISO 'T' + FILTRO 1900 ---
                # 1. Convertir a datetime
                fechas_obj = pd.to_datetime(data_chunk.iloc[:, 2], format="%d-%m-%Y %H:%M:%S", errors='coerce')
                
                # 2. Filtrar Años < 1900 y NaT
                mask_valida = fechas_obj.notna() & (fechas_obj.dt.year >= 1900)
                data_chunk = data_chunk[mask_valida].copy()

                # 3. Formato ISO estricto con 'T'
                data_chunk.iloc[:, 2] = fechas_obj[mask_valida].dt.strftime("%Y-%m-%dT%H:%M:%S")
                # --------------------------------------------

                data_chunk = data_chunk.dropna(how='all')
                data_chunk = data_chunk.map(lambda x: x.strip() if isinstance(x, str) else x)
                
                equipos_unicos.update(data_chunk.iloc[:, 1].dropna().unique())
                datos_procesados = pd.concat([datos_procesados, data_chunk], ignore_index=True)
            
            if datos_procesados.empty:
                return False, []

            lista_equipos_unicos = list(equipos_unicos)
            
            unique_data = {(row[1], row[2]): row for row in datos_procesados.itertuples(index=False)}
            datalimpia = pd.DataFrame(unique_data.values())
            
            if tipodata == 1:
                respuesta = DatosModel.mdlRegistrarPrismasAutomatizadosCuatro(idproyecto, datalimpia)
            else:
                respuesta = DatosModel.mdlRemplazarPrismasAutomatizadosCuatro(idproyecto, datalimpia, idcompo)
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
    