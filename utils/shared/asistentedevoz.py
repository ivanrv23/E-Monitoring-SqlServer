import pyttsx3
import ast
from datetime import datetime
import datetime as dt_module 
from PySide6.QtWidgets import QComboBox
from utils.common.metodosGenerales import MetodosGenerales
from controllers.AsistentevozController import AsistenteVozController
from controllers.InclinometroController import InclinometroController
from controllers.PiezometroController import PiezometroController
from controllers.CeldaController import CeldaController
from controllers.AnalisisController import AnalisisController
from controllers.AcelerografoController import AcelerografoController
from controllers.TDRController import TDRController
from modules.empresa.softwareconfiguracion import SoftwareConfiguracion

class AsistenteVoz:
    motor_tts = pyttsx3.init()

    @staticmethod
    def analizarVisor(proyectoid, prismasmarcados, fechaini, fechafin, inclinometromarcados, piezocuerdamarcados, piezomanualmarcados, otrosequipos, boton_analisis_visor):
        texto = AsistenteVoz.obtenerInformacionVisor(proyectoid, prismasmarcados, fechaini, fechafin, inclinometromarcados, piezocuerdamarcados, piezomanualmarcados, otrosequipos)
        AsistenteVoz.motor_tts.stop()
        AsistenteVoz.motor_tts.setProperty("rate", 150)
        AsistenteVoz.motor_tts.say(texto)
        AsistenteVoz.motor_tts.runAndWait()
        boton_analisis_visor.setEnabled(True)
    
    def obtenerInformacionVisor(proyectoid, prismasmarcados, fechaini, fechafin,  inclinometromarcados, piezocuerdamarcados, piezomanualmarcados, otrosequipos):
        if len(prismasmarcados) > 0 or len(inclinometromarcados) > 0 or len(piezocuerdamarcados) > 0 or len(piezomanualmarcados) > 0:
            texto = " "
            if len(prismasmarcados) > 0:
                textoprismas = AsistenteVoz.obtenerInformacionPrismas(proyectoid, prismasmarcados, fechaini, fechafin)
                texto = texto + textoprismas + " "
            if len(inclinometromarcados) > 0:
                textoincli = AsistenteVoz.obtenerInformacionInclinometros(inclinometromarcados)
                texto = texto + textoincli + " "
            if len(piezocuerdamarcados) > 0:
                textopiezo = AsistenteVoz.obtenerInformacionPiezometros(piezocuerdamarcados, "cuerda vibrante")
                texto = texto + textopiezo + " "
            if len(piezomanualmarcados) > 0:
                textopiezo = AsistenteVoz.obtenerInformacionPiezometros(piezomanualmarcados, "casagrande")
                texto = texto + textopiezo + " "
        else:
            if otrosequipos:
                texto = "Se está mostrando la ubicación de los equipos."
            else:
                texto = "No hay equipos para analizar."
        return texto

    def obtenerInformacionPrismas(proyectoid, prismasmarcados, fechaini, fechafin):
        arreglo = []
        cantidadPrismas = sum(len(listaprismas) for componente, listaprismas in prismasmarcados)
        for componente, listaprismas in prismasmarcados:
            marcados = MetodosGenerales.ctrlAgruparPrismasSegunTipo(listaprismas)
            idcomponente = componente[1]
            for tabla, prismas in marcados.items():
                respuesta = AsistenteVozController.ctrlObtenerInformacionPrismas(tabla, prismas, idcomponente, fechaini, fechafin)
                if respuesta:
                    arreglo.extend(respuesta)
        if arreglo:
            menor_valor = min(arreglo, key=lambda x: x[1])
            mayor_valor = max(arreglo, key=lambda x: x[1])
            if cantidadPrismas == 1:
                texto = f"""Se está analizando el prisma {mayor_valor[0]} desde el {fechaini} hasta el {fechafin}. El prisma cuenta con un total de {menor_valor[1]} lecturas entre ese rango de fechas."""
            else:
                texto = f"""Se está analizando un total de {cantidadPrismas} prismas desde el {fechaini} hasta el {fechafin}.
                El prisma con menor lecturas es el {menor_valor[0]}, con un total de {menor_valor[1]} lecturas.
                El prisma con mayor lecturas es el {mayor_valor[0]} con un total de {mayor_valor[1]} lecturas."""
        else:
            texto = "No hay data para analizar."
        return texto
    
    def obtenerInformacionInclinometros(inclinometromarcados):
        lista_fechas_dt = [] # Almacenaremos objetos datetime reales aquí

        for inclinome, fechitas_raw, idinstru in inclinometromarcados:
            temp_lista = []
            
            # 1. PARSEO: Convertir entrada a lista
            if isinstance(fechitas_raw, list):
                temp_lista = fechitas_raw
            elif isinstance(fechitas_raw, str) and "datetime.datetime" in fechitas_raw:
                try:
                    # Usamos dt_module para el contexto del eval
                    temp_lista = eval(fechitas_raw, {"__builtins__": None}, {"datetime": dt_module})
                except:
                    temp_lista = []
            elif isinstance(fechitas_raw, str):
                try:
                    temp_lista = ast.literal_eval(fechitas_raw)
                except:
                    temp_lista = []

            # 2. NORMALIZACIÓN: Convertir todo a objeto datetime
            for item in temp_lista:
                if isinstance(item, datetime):
                    # Si ya es objeto (vía eval o driver), lo guardamos directo
                    lista_fechas_dt.append(item)
                elif isinstance(item, str):
                    # Si es texto (vía ast o driver antiguo), lo convertimos
                    try:
                        dt_obj = datetime.strptime(item, "%Y-%m-%d %H:%M:%S")
                        lista_fechas_dt.append(dt_obj)
                    except ValueError:
                        pass # Ignorar formatos incorrectos

        if not lista_fechas_dt:
            return "No se encontraron fechas válidas para analizar."

        # 3. CÁLCULO
        fechamenor = min(lista_fechas_dt)
        fechamayor = max(lista_fechas_dt)
        
        cantidadIncli = len(inclinometromarcados)
        
        # str(fechamenor) convierte automáticamente a 'YYYY-MM-DD HH:MM:SS'
        if cantidadIncli == 1:
            texto = f"Se esta analizando un inclinómetro con lecturas desde el {fechamenor} hasta {fechamayor}."
        else:
            texto = f"Se esta analizando un total de {cantidadIncli} inclinómetros con lecturas desde el {fechamenor} hasta {fechamayor}."
            
        return texto
    
    def obtenerInformacionPiezometros(piezometromarcados, tipo):
        cantidadPiezo = sum(len(diccionario) for _, diccionario in piezometromarcados)
        if cantidadPiezo == 1:
            texto = f"Se esta analizando un piezómetro {tipo}, en el cual refleja el nivel freático."
        else:
            texto = f"Se esta analizando un total de {cantidadPiezo} piezómetros {tipo}, de los cuales se muestra el nivel freático."
        return texto
    
    # ANALISIS ASISTENTE DE VOZ DESPLAZAMIENTO
    def analizarDesplazamiento(proyectoid, prismasmarcados, fechaini, fechafin, tipografico, botonvoz):
        texto = AsistenteVoz.obtenerInformacionMonitor1(proyectoid, prismasmarcados, fechaini, fechafin, tipografico)
        AsistenteVoz.motor_tts.stop()
        AsistenteVoz.motor_tts.setProperty("rate", 150)
        AsistenteVoz.motor_tts.say(texto)
        AsistenteVoz.motor_tts.runAndWait()
        botonvoz.setEnabled(True)
    
    def obtenerInformacionMonitor1(proyectoid, prismasmarcados, fechaini, fechafin, tipografico):
        arreglo = []
        cantidadPrismas = sum(len(listaprismas) for componente, listaprismas in prismasmarcados)
        for componente, listaprismas in prismasmarcados:
            marcados = MetodosGenerales.ctrlAgruparPrismasSegunTipo(listaprismas)
            idcomponente = componente[1]
            for tabla, prismas in marcados.items():
                respuesta = AsistenteVozController.ctrlResumenVozDesplazamiento(tabla, prismas, idcomponente, fechaini, fechafin)
                if respuesta:
                    arreglo.extend(respuesta)
        if arreglo:
            if tipografico == '3DA':
                posi = 4
                tipo = "Desplazamiento 3D"
            elif tipografico == '3DI':
                posi = 4
                tipo = "Desplazamiento 3D"
            elif tipografico == '2DA':
                posi = 5
                tipo = "Desplazamiento 2D"
            elif tipografico == '2DI':
                posi = 5
                tipo = "Desplazamiento 2D"
            elif tipografico == 'SDA':
                posi = 3
                tipo = "Desplazamiento SD"
            elif tipografico == 'SDI':
                posi = 3
                tipo = "Desplazamiento SD"
            elif tipografico == 'DLA':
                posi = 6
                tipo = "Desplazamiento Longitudinal"
            elif tipografico == 'DLI':
                posi = 6
                tipo = "Desplazamiento Longitudinal"
            elif tipografico == 'DTA':
                posi = 7
                tipo = "Desplazamiento Transversal"
            elif tipografico == 'DTI':
                posi = 7
                tipo = "Desplazamiento Transversal"
            elif tipografico == 'DHA':
                posi = 8
                tipo = "Desplazamiento Altura"
            elif tipografico == 'DHI':
                posi = 8
                tipo = "Desplazamiento Altura"
            elif tipografico == 'DNA':
                posi = 10
                tipo = "Desplazamiento Norte"
            elif tipografico == 'DNI':
                posi = 10
                tipo = "Desplazamiento Norte"
            elif tipografico == 'DEA':
                posi = 9
                tipo = "Desplazamiento Este"
            elif tipografico == 'DEI':
                posi = 9
                tipo = "Desplazamiento Este"
            elif tipografico == 'DZA':
                posi = 11
                tipo = "Desplazamiento Cota"
            elif tipografico == 'DZI':
                posi = 11
                tipo = "Desplazamiento Cota"
            menor_valor = min(arreglo, key=lambda x: x[posi])
            mayor_valor = max(arreglo, key=lambda x: x[posi])
            if cantidadPrismas == 1:
                texto = f"""Se está analizando el {tipo} del prisma {mayor_valor[0]}, lo cual la tiene una medida de {mayor_valor[posi]:.3f} metros."""
            else:
                texto = f"""Se está analizando el {tipo} de un total de {cantidadPrismas} prismas, el prisma con menor medida es el {menor_valor[0]}
                con {menor_valor[posi]:.3f} metros, y el prisma con mayor medida es el {mayor_valor[0]} con {mayor_valor[posi]:.3f} metros."""
        else:
            texto = "No hay data para analizar."
        return texto
    
    # ANALISIS ASISTENTE DE VOZ VELOCIDAD
    def analizarVelocidad(proyectoid, prismasmarcados, fechaini, fechafin, tipografico, botonvoz):
        texto = AsistenteVoz.obtenerInformacionMonitor2(proyectoid, prismasmarcados, fechaini, fechafin, tipografico)
        AsistenteVoz.motor_tts.stop()
        AsistenteVoz.motor_tts.setProperty("rate", 150)
        AsistenteVoz.motor_tts.say(texto)
        AsistenteVoz.motor_tts.runAndWait()
        botonvoz.setEnabled(True)
    
    def obtenerInformacionMonitor2(proyectoid, prismasmarcados, fechaini, fechafin, tipografico):
        arreglo = []
        cantidadPrismas = sum(len(listaprismas) for componente, listaprismas in prismasmarcados)
        for componente, listaprismas in prismasmarcados:
            marcados = MetodosGenerales.ctrlAgruparPrismasSegunTipo(listaprismas)
            idcomponente = componente[1]
            for tabla, prismas in marcados.items():
                respuesta = AsistenteVozController.ctrlResumenVozVelocidad(tabla, prismas, idcomponente, fechaini, fechafin)
                if respuesta:
                    arreglo.extend(respuesta)
        if arreglo:
            if tipografico == 'VI3D':
                posi = 3
                tipo = "Velocidad Incremental 3D"
            elif tipografico == 'VA3D':
                posi = 4
                tipo = "Velocidad Acumulada 3D"
            elif tipografico == 'VI2D':
                posi = 5
                tipo = "Velocidad Incremental 2D"
            elif tipografico == 'VA2D':
                posi = 6
                tipo = "Velocidad Acumulada 2D"
            elif tipografico == 'VISD':
                posi = 7
                tipo = "Velocidad Incremental SD"
            elif tipografico == 'VASD':
                posi = 8
                tipo = "Velocidad Acumulada SD"
            menor_valor = min(arreglo, key=lambda x: x[posi])
            mayor_valor = max(arreglo, key=lambda x: x[posi])
            if cantidadPrismas == 1:
                texto = f"""Se está analizando la {tipo} del prisma {mayor_valor[0]}, lo cual la tiene una medida de {mayor_valor[posi]:.3f} metros por día."""
            else:
                texto = f"""Se está analizando la {tipo} de un total de {cantidadPrismas} prismas, el prisma con menor medida es el {menor_valor[0]}
                con {menor_valor[posi]:.3f} metros por día, y el prisma con mayor medida es el {mayor_valor[0]} con {mayor_valor[posi]:.3f} metros por día."""
        else:
            texto = "No hay data para analizar."
        return texto
    
    # ANALISIS ASISTENTE DE VOZ INCLINÓMETROS
    def analizarInclinometros(idproyecto, inclinometrosmarcados, tipo, botonvoz):        
        texto = AsistenteVoz.obtenerAnalisisInclinometros(idproyecto, inclinometrosmarcados, tipo)
        AsistenteVoz.motor_tts.stop()
        AsistenteVoz.motor_tts.setProperty("rate", 150)
        AsistenteVoz.motor_tts.say(texto)
        AsistenteVoz.motor_tts.runAndWait()
        botonvoz.setEnabled(True)
    
    def obtenerAnalisisInclinometros(idproyecto, inclinometrosmarcados, tipografico):
        estado3d = False
        if tipografico == 'AI3D':
            datosacum = InclinometroController.ctrlObtenerDAAB(idproyecto, inclinometrosmarcados, 1, 0, 0, 0)
            datosincr = InclinometroController.ctrlObtenerDIAB(idproyecto, inclinometrosmarcados, 1, 0, 0, 0)
            tipoacum = "Desplazamiento Acumulado 3D"
            tipoincr = "Desplazamiento Incremental 3D"
            estado3d = True
        elif tipografico == 'DAAB':
            datos = InclinometroController.ctrlObtenerDAAB(idproyecto, inclinometrosmarcados, 1, 0, 0, 0)
            tipoacum = "el Desplazamiento Acumulado en A"
            tipoincr = "el Desplazamiento Acumulado en B"
        elif tipografico == 'DIAB':
            datos = InclinometroController.ctrlObtenerDIAB(idproyecto, inclinometrosmarcados, 1, 0, 0, 0)
            tipoacum = "el Desplazamiento Incremental en A"
            tipoincr = "el Desplazamiento Incremental en B"
        elif tipografico == 'DANE':
            datos = InclinometroController.ctrlObtenerDANE(idproyecto, inclinometrosmarcados, 1, 0, 0, 0)
            tipoacum = "el Desplazamiento Acumulado en Este"
            tipoincr = "el Desplazamiento Acumulado en Norte"
        elif tipografico == 'DINE':
            datos = InclinometroController.ctrlObtenerDINE(idproyecto, inclinometrosmarcados, 1, 0, 0, 0)
            tipoacum = "el Desplazamiento Incremental en Este"
            tipoincr = "el Desplazamiento Incremental en Norte"
        elif tipografico == 'PAAB':
            datos = InclinometroController.ctrlObtenerPAAB(idproyecto, inclinometrosmarcados, 1, 0, 0, 0)
            tipoacum = "la Posición Absoluta en A"
            tipoincr = "la Posición Absoluta en B"
        elif tipografico == 'PANE':
            datos = InclinometroController.ctrlObtenerPANE(idproyecto, inclinometrosmarcados, 1, 0, 0, 0)
            tipoacum = "la Posición Absoluta en Este"
            tipoincr = "la Posición Absoluta en Norte"
        if estado3d:
            if datosacum and datosincr:
                if datosacum[-1][2] > 0: # profudidad positiva
                    mayor_acumuladoa = max(datosacum, key=lambda x: abs(x[3]))
                    mayor_acumuladob = max(datosacum, key=lambda x: abs(x[4]))
                    mayor_incrementala = max(datosincr, key=lambda x: abs(x[3]))
                    mayor_incrementalb = max(datosincr, key=lambda x: abs(x[4]))
                else: # profudidad negativa
                    mayor_acumuladoa = min(datosacum, key=lambda x: abs(x[3]))
                    mayor_acumuladob = min(datosacum, key=lambda x: abs(x[4]))
                    mayor_incrementala = min(datosincr, key=lambda x: abs(x[3]))
                    mayor_incrementalb = min(datosincr, key=lambda x: abs(x[4]))
                texto = f"""Se está realizando el análisis del {tipoacum} del inclinómetro {mayor_acumuladoa[0]}. La lectura acumulada más alta en A,
                se encuentra registrada en la fecha {mayor_acumuladoa[1]}, a una profundidad de {mayor_acumuladoa[2]}. La lectura acumulada más alta en B,
                se encuentra registrada en la fecha {mayor_acumuladob[1]}, a una profundidad de {mayor_acumuladob[2]}.
                En cuanto al {tipoincr}, se registra la lectura incremental más alta en A, en la fecha {mayor_incrementala[1]}, a una profundidad de {mayor_incrementala[2]}.
                Y la lectura incremental más alta en B, se encuentra en la fecha {mayor_incrementalb[1]}, a una profundidad de {mayor_incrementalb[2]}."""
            else:            
                texto = "No hay data para analizar."
        else:
            if datos:
                mayor_acumulado = max(datos, key=lambda x: abs(x[3]))
                mayor_incremental = max(datos, key=lambda x: abs(x[4]))
                texto = f"""Se está realizando el análisis del inclinómetro {mayor_acumulado[0]}. La lectura más alta en {tipoacum}, se encuentra registrada en la fecha {mayor_acumulado[1]},
                a una profundidad de {mayor_acumulado[2]}. Por otro lado, en {tipoincr}, se registra la lectura más alta en la fecha {mayor_incremental[1]},
                a una profundidad de {mayor_incremental[2]}."""
            else:            
                texto = "No hay data para analizar."
        return texto
    
    # ANALISIS ASISTENTE DE VOZ PIEZÓMETROS
    def analizarPiezometros(proyectoid, piezometrocuerdamarcados, piezometrocasamarcados, fechainicuerda, fechafincuerda, fechainimanual, fechafinmanual, tipo, botonvoz):
        texto = AsistenteVoz.obtenerInformacionPiezometros(proyectoid, piezometrocuerdamarcados, piezometrocasamarcados, fechainicuerda, fechafincuerda, fechainimanual, fechafinmanual, tipo)
        AsistenteVoz.motor_tts.stop()
        AsistenteVoz.motor_tts.setProperty("rate", 150)
        AsistenteVoz.motor_tts.say(texto)
        AsistenteVoz.motor_tts.runAndWait()
        botonvoz.setEnabled(True)

    def obtenerInformacionPiezometros(proyectoid, piezometrocuerdamarcados, piezometrocasamarcados, fechainicuerda, fechafincuerda, fechainimanual, fechafinmanual, tipo):
        texto = ""
        if len(piezometrocuerdamarcados) > 0:
            textocuerda = AsistenteVoz.obtenerAnalisisPiezometros(proyectoid, piezometrocuerdamarcados, fechainicuerda, fechafincuerda, tipo, "CUERDA")
            texto = texto + textocuerda + " "
        if len(piezometrocasamarcados) > 0:
            textomanual = AsistenteVoz.obtenerAnalisisPiezometros(proyectoid, piezometrocasamarcados, fechainimanual, fechafinmanual, tipo, "MANUAL")
            texto = texto + textomanual + " "
        return texto

    def obtenerAnalisisPiezometros(proyectoid, piezometromarcados, fechaini, fechafin, tipografico, tipo):
        posi = 0
        nivel = ""
        if tipo == "CUERDA":
            data = PiezometroController.ctrlCalcularPiezometrosCuerda(proyectoid, piezometromarcados, fechaini, fechafin, 1, 1)
            piezotipo = "Cuerda Vibrante"
            if tipografico == "NF":
                posi = 8
                nivel = "el Nivel Freático"
            elif tipografico == "NI":
                posi = 9
                nivel = "el Nivel Incremental"
            elif tipografico == "NA":
                posi = 10
                nivel = "el Nivel Acumulado"
            elif tipografico == "PB":
                posi = 7
                nivel = "la Presión Barométrica"
            elif tipografico == "FP":
                posi = 5
                nivel = "la Frecuencia"
            elif tipografico == "TP":
                posi = 6
                nivel = "la Temperatura"
        else:
            data = PiezometroController.ctrlCalcularPiezometrosCasaGrande(proyectoid, piezometromarcados, fechaini, fechafin, 1, 1)
            piezotipo = "Casa grande"
            if tipografico == "NF":
                posi = 5
                nivel = "el Nivel Freático"
            elif tipografico == "NI":
                posi = 6
                nivel = "el Nivel Incremental"
            elif tipografico == "NA":
                posi = 7
                nivel = "el Nivel Acumulado"
        if data and posi != 0 and nivel != "":
            data_filtrada = [fila for fila in data if fila[posi] not in (None, '')]
            if data_filtrada:
                menor_valor = min(data_filtrada, key=lambda x: x[posi])
                mayor_valor = max(data_filtrada, key=lambda x: x[posi])
                cantidadPiezo = len(piezometromarcados)
                if cantidadPiezo == 1:
                    cantidadlecturas = len(data)
                    texto = f"""Se está analizando el piezómetro {piezotipo}, {mayor_valor[1]}, con un total de {cantidadlecturas} lecturas,
                    desde el {fechaini} hasta el {fechafin}. El mayor valor en {nivel} es de {mayor_valor[posi]:.3f} en la fecha {mayor_valor[2]}."""
                else:
                    texto = f"""Se está analizando {nivel} de un total de {cantidadPiezo} piezómetros {piezotipo}.
                    El piezómetro {mayor_valor[1]} tiene la mayor medida {mayor_valor[posi]:.3f} en la fecha {mayor_valor[2]},
                    mientras el piezómetro {menor_valor[1]} tiene la menor medida {menor_valor[posi]:.3f} en la fecha {menor_valor[2]}."""
            else:
                texto = "No hay data para analizar."
        else:
            texto = "No hay data para analizar."
        return texto    
    
    # ANALISIS ASISTENTE DE VOZ CELDAS
    def analizarCeldas(proyectoid, celdasmarcadas, fechaini, fechafin, tipo, tipovelocidad, nrodiasvelocidad, botonvoz):
        texto = AsistenteVoz.obtenerInformacionCeldas(proyectoid, celdasmarcadas, fechaini, fechafin, tipo, tipovelocidad, nrodiasvelocidad)
        AsistenteVoz.motor_tts.stop()
        AsistenteVoz.motor_tts.setProperty("rate", 150)
        AsistenteVoz.motor_tts.say(texto)
        AsistenteVoz.motor_tts.runAndWait()
        botonvoz.setEnabled(True)

    def obtenerInformacionCeldas(proyectoid, celdasmarcadas, fechaini, fechafin, tipografica, tipovelocidad, nrodiasvelocidad):
        config = SoftwareConfiguracion.obtenerDataSoftware()
        celdapositiva = config[19]
        if tipografica == 'VI':
            if tipovelocidad == 'Por Mes':
                datos = CeldaController.ctrlCalcularVelocidadMes(proyectoid, celdasmarcadas, fechaini, fechafin, 1)
            else:
                if nrodiasvelocidad > 0:
                    datos = CeldaController.ctrlCalcularVelocidadDias(nrodiasvelocidad, proyectoid, celdasmarcadas, fechaini, fechafin, 1)
                else:
                    datos = []
            if celdapositiva == 0:
                posi = 8
            else:
                posi = 5
            nivel = "la velocidad"
        elif tipografica == 'AC':
            datos = CeldaController.ctrlObtenerAsentamientoCota(proyectoid, celdasmarcadas, fechaini, fechafin, 1)
            posi = 5
            nivel = "el Asentamiento en Cota"
        elif tipografica == 'AI':
            datos = CeldaController.ctrlCalcularAsentamientoIncremental(proyectoid, celdasmarcadas, fechaini, fechafin, 1, 1)
            posi = 5
            nivel = "el Asentamiento Incremental"
        elif tipografica == 'AA':
            datos = CeldaController.ctrlObtenerAsentamientoAcumulado(proyectoid, celdasmarcadas, fechaini, fechafin, 1, 1)
            posi = 5
            nivel = "el Asentamiento Acumulado"
        elif tipografica == 'AF':
            posi = 5
            nivel = "la frecuencia"
            datos = CeldaController.ctrlObtenerAsentamientoFrecuencia(proyectoid, celdasmarcadas, fechaini, fechafin, 1)
        elif tipografica == 'AT':
            posi = 5
            nivel = "la temperatura"
            datos = CeldaController.ctrlObtenerAsentamientoTemperatura(proyectoid, celdasmarcadas, fechaini, fechafin, 1)
        if datos:
            data_filtrada = [fila for fila in datos if fila[posi] not in (None, '')]
            if data_filtrada:
                menor_valor = min(data_filtrada, key=lambda x: x[posi])
                mayor_valor = max(data_filtrada, key=lambda x: x[posi])
                cantidadCeldas = len(celdasmarcadas)
                if cantidadCeldas == 1:
                    cantidadlecturas = len(datos)
                    texto = f"""Se está analizando la celda {mayor_valor[1]}, con un total de {cantidadlecturas} lecturas,
                    desde el {fechaini} hasta el {fechafin}. El mayor valor en {nivel} es de {mayor_valor[posi]:.3f} en la fecha {mayor_valor[2]}."""
                else:
                    texto = f"""Se está analizando {nivel} de un total de {cantidadCeldas} celdas.
                    La celda {mayor_valor[1]} tiene la mayor medida {mayor_valor[posi]:.3f} en la fecha {mayor_valor[2]},
                    mientras la celda {menor_valor[1]} tiene la menor medida {menor_valor[posi]:.3f} en la fecha {menor_valor[2]}."""
            else:
                texto = "No hay data para analizar."
        else:
            texto = "No hay data para analizar."
        return texto    
    
    # ANALISIS ASISTENTE DE VOZ VISTA ANALISIS PRISMAS
    def analizarVistaAnalisis(main, idproyecto, prismasmarcados, trayectoriagraficado, histogramagraficado, fechaini, fechafin, tipografico, botonvoz):        
        texto = AsistenteVoz.obtenerAnalisisPrismas(main, idproyecto, prismasmarcados, trayectoriagraficado, histogramagraficado, fechaini, fechafin, tipografico)
        AsistenteVoz.motor_tts.stop()
        AsistenteVoz.motor_tts.setProperty("rate", 150)
        AsistenteVoz.motor_tts.say(texto)
        AsistenteVoz.motor_tts.runAndWait()
        botonvoz.setEnabled(True)
    
    def obtenerAnalisisPrismas(main, idproyecto, prismasmarcados, trayectoriagraficado, histogramagraficado, fechaini, fechafin, tipografico):
        if tipografico == "TE":
            textotrayectoria, textotalud = "", ""
            if trayectoriagraficado:
                # comboPrismasTrayectoria = main.findChild(QComboBox, "cb_lista_prismas_trayectoria")
                # if comboPrismasTrayectoria.count() > 0:
                #     nombreprisma = comboPrismasTrayectoria.currentText()
                #     tipoprisma = comboPrismasTrayectoria.currentData()
                    config = SoftwareConfiguracion.obtenerDataSoftware()
                    filtrado = config[16]
                    datos = AnalisisController.ctrlCalcularDatosTrayectoria(idproyecto, prismasmarcados, fechaini, fechafin, filtrado)
                    if datos is not None:
                        este = datos[-1][3]
                        norte = datos[-1][4]
                        elevacion = datos[-1][5] 
                        # Movimiento hacia el este
                        if este > 0 and norte == 0 and elevacion > 0:
                            movimiento = f'tiene un movimiento hacia arriba en dirección este.'
                        elif este > 0 and norte == 0 and elevacion < 0:
                            movimiento = f'tiene un movimiento hacia abajo en dirección este.'
                        # Movimiento hacia el oeste
                        elif este < 0 and norte == 0 and elevacion > 0:
                            movimiento = f'tiene un movimiento hacia arriba en dirección oeste.'
                        elif este < 0 and norte == 0 and elevacion < 0:
                            movimiento = f'tiene un movimiento hacia abajo en dirección oeste.'
                        # Movimiento hacia el norte
                        elif este == 0 and norte > 0 and elevacion > 0:
                            movimiento = f'tiene un movimiento hacia arriba en dirección norte.'
                        elif este == 0 and norte > 0 and elevacion < 0:
                            movimiento = f'tiene un movimiento hacia abajo en dirección norte.'
                        # Movimiento hacia el sur
                        elif este == 0 and norte < 0 and elevacion > 0:
                            movimiento = f'tiene un movimiento hacia arriba en dirección sur.'
                        elif este == 0 and norte < 0 and elevacion < 0:
                            movimiento = f'tiene un movimiento hacia abajo en dirección sur.'
                        # Movimiento en dirección noreste
                        elif este > 0 and norte > 0 and elevacion > 0:
                            movimiento = f'tiene un movimiento hacia arriba en dirección noreste.'
                        elif este > 0 and norte > 0 and elevacion < 0:
                            movimiento = f'tiene un movimiento hacia abajo en dirección noreste.'
                        # Movimiento en dirección sureste
                        elif este > 0 and norte < 0 and elevacion > 0:
                            movimiento = f'tiene un movimiento hacia arriba en dirección sureste.'
                        elif este > 0 and norte < 0 and elevacion < 0:
                            movimiento = f'tiene un movimiento hacia abajo en dirección sureste.'
                        # Movimiento en dirección noroeste
                        elif este < 0 and norte > 0 and elevacion > 0:
                            movimiento = f'tiene un movimiento hacia arriba en dirección noroeste.'
                        elif este < 0 and norte > 0 and elevacion < 0:
                            movimiento = f'tiene un movimiento hacia abajo en dirección noroeste.'
                        # Movimiento en dirección suroeste
                        elif este < 0 and norte < 0 and elevacion > 0:
                            movimiento = f'tiene un movimiento hacia arriba en dirección suroeste.'
                        elif este < 0 and norte < 0 and elevacion < 0:
                            movimiento = f'tiene un movimiento hacia abajo en dirección suroeste.'
                        textotrayectoria = textotrayectoria + f"""Se está analizando la trayectoria de los prismas, donde {movimiento}."""
                    if len(prismasmarcados) > 0:
                        taludes = AnalisisController.ctrObtenerDataEstereografia(idproyecto)
                        data_trend_plunge = AnalisisController.ctrlDatosTrendPlunge(prismasmarcados, fechaini, fechafin, 1)
                        if taludes and data_trend_plunge:
                            direccion_talud = []
                            for i, dato in enumerate(taludes):
                                for j, prisma in enumerate(data_trend_plunge):
                                    if prisma[1] is not None and prisma[2] is not None:
                                        prisma[1] #trend
                                        prisma[2] #plunge
                                        if -30 <= dato[3]-prisma[1] <= 30:
                                            direccion_talud.append(prisma[0])
                                if len(direccion_talud) > 0:
                                    textotalud = textotalud + " Los prismas:"
                                    for valor in direccion_talud:
                                        textotalud = textotalud + f" {valor},"
                                    textotalud = textotalud + f"se mueven en dirección al talud {dato[2]}."
                                else:
                                    textotalud = textotalud + f" No existe prismas con movimiento hacia el talud {dato[2]}."
                        else:
                            textotalud = "No hay taludes para validar la dirección de los prismas."
            texto = f"{textotrayectoria} {textotalud}"
        elif tipografico == "IV":
            if len(prismasmarcados) > 0:
                datos = AnalisisController.ctrlCalcularDatosGrafica(idproyecto, prismasmarcados, fechaini, fechafin, tipografico, 1, 1)
                if len(datos) > 0:
                    menor_valor = min(datos, key=lambda x: x[6])
                    mayor_valor = max(datos, key=lambda x: x[6])
                    cantidadPrismas = sum(len(listaprismas) for componente, listaprismas in prismasmarcados)
                    if cantidadPrismas == 1:
                        cantidadlecturas = len(datos)
                        texto = f"""Se está analizando la Inversa de la velocidad del prisma {mayor_valor[1]}, con un total de {cantidadlecturas} lecturas,
                        desde el {fechaini} hasta el {fechafin}. El mayor valor es de {mayor_valor[6]:.3f} días por metros en la fecha {mayor_valor[2]}."""
                    else:
                        texto = f"""Se está analizando la Inversa de la velocidad de un total de {cantidadPrismas} prismas.
                        El prisma {mayor_valor[1]} tiene la mayor medida {mayor_valor[6]:.3f} en la fecha {mayor_valor[2]},
                        mientras el prisma {menor_valor[1]} tiene la menor medida {menor_valor[6]:.3f} en la fecha {menor_valor[2]}."""
                else:
                    texto = "No hay data para analizar."
            else:
                texto = "No hay prismas para analizar."
        elif tipografico == "HI":
            texto = ""
            if histogramagraficado:
                comboPrismasHistograma = main.findChild(QComboBox, "combo_prismas_histograma")
                if comboPrismasHistograma.count() > 0:
                    nombreprisma = comboPrismasHistograma.currentText()
                    texto = f"Se está analizando el prisma {nombreprisma} en el histograma."
        return texto
    
    # ANALISIS ASISTENTE DE VOZ ACELERÓGRAFOS
    def analizarAcelerografos(proyectoid, aceleromarcados, fechaini, fechafin, botonvoz):
        texto = AsistenteVoz.obtenerInformacionAcelerografos(proyectoid, aceleromarcados, fechaini, fechafin)
        AsistenteVoz.motor_tts.stop()
        AsistenteVoz.motor_tts.setProperty("rate", 150)
        AsistenteVoz.motor_tts.say(texto)
        AsistenteVoz.motor_tts.runAndWait()
        botonvoz.setEnabled(True)
    
    def obtenerInformacionAcelerografos(proyectoid, aceleromarcados, fechaini, fechafin):
        cantidadSismos = sum(len(listaacele) for componente, listaacele in aceleromarcados)
        datos = AcelerografoController.ctrlObtenerMagnitudFechas(proyectoid, aceleromarcados, fechaini, fechafin)
        if len(datos) > 0:
            mayor_valor = max(datos, key=lambda x: x[3])
            if cantidadSismos == 1:
                totallecturas = len(datos)
                texto = f"""Se está analizando la magnitud sísmica del Acelerógrafo {mayor_valor[1]}, con un total de {totallecturas} lecturas,
                desde el {fechaini} hasta el {fechafin}, en donde la mayor magnitud con una escala de {mayor_valor[3]:.1f} se dió el {mayor_valor[2]}."""
            else:
                texto = f"""Se está analizando la magnitud sísmica de un total de {cantidadSismos} Acelerógrafos,
                la mayor magnitud lo detectó el equipo {mayor_valor[1]} con una escala de {mayor_valor[3]:.1f} el día {mayor_valor[2]}."""
        else:
            texto = "No hay data para analizar."
        return texto
    
    # ANALISIS ASISTENTE DE VOZ SONDAJES TDR
    def analizarSondajestdr(idproyecto, sondajesmarcados, botonvoz):        
        texto = AsistenteVoz.obtenerAnalisisSondajestdr(idproyecto, sondajesmarcados)
        AsistenteVoz.motor_tts.stop()
        AsistenteVoz.motor_tts.setProperty("rate", 150)
        AsistenteVoz.motor_tts.say(texto)
        AsistenteVoz.motor_tts.runAndWait()
        botonvoz.setEnabled(True)
    
    def obtenerAnalisisSondajestdr(idproyecto, sondajesmarcados):
        datos, fallas = TDRController.ctrlObtenerLecturasTDR(idproyecto, sondajesmarcados, 1)
        if len(datos) > 0:
            mayor_valor = max(datos, key=lambda x: abs(x[4]))
            texto = f"""Se está realizando el análisis del TDR {mayor_valor[0]}, en donde la impedancia más alta es de {mayor_valor[4]},
            y se encuentra registrada en la fecha {mayor_valor[2]}, a una profundidad de {mayor_valor[3]} metros."""
        else:         
            texto = "No hay data para analizar."
        return texto
    