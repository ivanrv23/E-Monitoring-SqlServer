import pandas as pd
import matplotlib.dates as mdates
import numpy as np
from scipy.optimize import curve_fit
from scipy import stats
from collections import defaultdict

class CalculosTendencias:
    
    def dibujarTendenciaLineal(horas, valores, ax, forma_grafica, grado, prisma, lineatenden, grosortenden, colortenden):
        timestamps = []
        displacements = []
        for fecha, desplaza in zip(horas, valores):
            if desplaza is not None and desplaza != "":
                timestamps.append(fecha)
                displacements.append(desplaza)
        if forma_grafica == 'FECHA':
            coeffs = np.polyfit(mdates.date2num(timestamps), displacements, grado)
            trend_line = np.poly1d(coeffs)
            if grado == 1:
                linea, = ax.plot(timestamps, trend_line(mdates.date2num(timestamps)), linestyle=lineatenden, linewidth=grosortenden,
                                 color=colortenden, label=f'Lineal {prisma}')
            else:
                linea, = ax.plot(timestamps, trend_line(mdates.date2num(timestamps)), linestyle=lineatenden, linewidth=grosortenden,
                                 color=colortenden, label=f'Polinómica {prisma}')
        else:
            coeffs = np.polyfit(timestamps, displacements, grado)
            trend_line = np.poly1d(coeffs)
            if grado == 1:
                linea, = ax.plot(timestamps, trend_line(timestamps), linestyle=lineatenden, linewidth=grosortenden,
                                 color=colortenden, label=f'Lineal {prisma}')
            else:
                linea, = ax.plot(timestamps, trend_line(timestamps), linestyle=lineatenden, linewidth=grosortenden,
                                 color=colortenden, label=f'Polinómica {prisma}')
        return linea
    
    def generarEcuacionTendencia(horas, valores, forma_grafica, grado):
        timestamps = []
        displacements = []
        for fecha, desplaza in zip(horas, valores):
            if desplaza is not None and desplaza != "":
                timestamps.append(fecha)
                displacements.append(desplaza)
        ecuacion_tendencia = CalculosTendencias.calcularEcuacionTendenciaLineal(timestamps, displacements, forma_grafica, grado)
        r_cuadrado = CalculosTendencias.calcularRcuadrado(timestamps, displacements, forma_grafica, grado)
        if grado == 1:
            equation = f'y = {ecuacion_tendencia[1]:.6f}x + ({ecuacion_tendencia[0]:.6f})    R²={r_cuadrado:.6f}'
        elif grado == 2:
            equation = f'y = {ecuacion_tendencia[2]:.6f}x² + {ecuacion_tendencia[1]:.6f}x + ({ecuacion_tendencia[0]:.6f})    R²={r_cuadrado:.6f}'
        elif grado == 3:
            equation = f'y = {ecuacion_tendencia[3]:.6f}x³ + {ecuacion_tendencia[2]:.6f}x² + {ecuacion_tendencia[1]:.6f}x + ({ecuacion_tendencia[0]:.6f})    R²={r_cuadrado:.6f}'
        elif grado == 4:
            equation = f'y = {ecuacion_tendencia[4]:.6f}x⁴ + {ecuacion_tendencia[3]:.6f}x³ + {ecuacion_tendencia[2]:.6f}x² + {ecuacion_tendencia[1]:.6f}x + ({ecuacion_tendencia[0]:.6f})    R²={r_cuadrado:.6f}'
        elif grado == 5:
            equation = f'y = {ecuacion_tendencia[5]:.6f}x⁵ + {ecuacion_tendencia[4]:.6f}x⁴ + {ecuacion_tendencia[3]:.6f}x³ + {ecuacion_tendencia[2]:.6f}x² + {ecuacion_tendencia[1]:.6f}x + ({ecuacion_tendencia[0]:.6f})    R²={r_cuadrado:.6f}'
        elif grado == 6:
            equation = f'y = {ecuacion_tendencia[6]:.6f}x⁶ + {ecuacion_tendencia[5]:.6f}x⁵ + {ecuacion_tendencia[4]:.6f}x⁴ + {ecuacion_tendencia[3]:.6f}x³ + {ecuacion_tendencia[2]:.6f}x² + {ecuacion_tendencia[1]:.6f}x + ({ecuacion_tendencia[0]:.6f})    R²={r_cuadrado:.6f}'
        return equation
    
    def calcularEcuacionTendenciaLineal(timestamps, displacements, forma_grafica, grado):
        if forma_grafica == 'FECHA':
            coeffs = np.polyfit(mdates.date2num(timestamps), displacements, grado)
        else:
            coeffs = np.polyfit(timestamps, displacements, grado)
        trend_line = np.poly1d(coeffs)
        return trend_line
    
    def calcularRcuadrado(timestamps, displacements, forma_grafica, grado):
        if forma_grafica == 'FECHA':
            coeficientes = np.polyfit(mdates.date2num(timestamps), displacements, grado)
            polinomio = np.poly1d(coeficientes)
            puntos_ajustados = polinomio(mdates.date2num(timestamps))
            residuos = displacements - puntos_ajustados
            suma_cuadrados_residuos = np.sum(residuos**2)
            suma_cuadrados_totales = np.sum((displacements - np.mean(displacements))**2)
            if suma_cuadrados_totales != 0:
                r_cuadrado = 1 - (suma_cuadrados_residuos / suma_cuadrados_totales)
            else:
                r_cuadrado = 1
        else:
            coeficientes = np.polyfit(timestamps, displacements, grado)
            polinomio = np.poly1d(coeficientes)
            puntos_ajustados = polinomio(timestamps)
            residuos = displacements - puntos_ajustados
            suma_cuadrados_residuos = np.sum(residuos**2)
            suma_cuadrados_totales = np.sum((displacements - np.mean(displacements))**2)
            if suma_cuadrados_totales != 0:
                r_cuadrado = 1 - (suma_cuadrados_residuos / suma_cuadrados_totales)
            else:
                r_cuadrado = 1
        return r_cuadrado
    
    def dibujarTendenciaLogaritmica(horas, valores, ax, tipografica, prisma, lineatenden, grosortenden, colortenden):
        timestamps = []
        displacements = []
        for fecha, desplaza in zip(horas, valores):
            if desplaza is not None and desplaza != "":
                timestamps.append(fecha)
                displacements.append(desplaza)
        timestamps = timestamps[1:]
        displacements = displacements[1:]
        if tipografica == 'FECHA':
            # Transformación logarítmica
            fechas = mdates.date2num(timestamps)
            log_x = np.log(fechas)
            # Regresión lineal con x logarítmica
            a, b, r_value, p_value, std_err = stats.linregress(log_x, displacements)
            # Generar puntos para la curva de ajuste
            x_ajuste = np.linspace(min(fechas), max(fechas), 100)
            y_ajuste = CalculosTendencias.funcionLogaritmica(x_ajuste, a, b)
            # Convertir las fechas de nuevo a objetos de fecha
            x_ajuste = mdates.num2date(x_ajuste)
        else:
            # Transformación logarítmica
            log_x = np.log(timestamps)
            # Regresión lineal con x logarítmica
            a, b, r_value, p_value, std_err = stats.linregress(log_x, displacements)
            # Generar puntos para la curva de ajuste
            x_ajuste = np.linspace(min(timestamps), max(timestamps), 100)
            y_ajuste = CalculosTendencias.funcionLogaritmica(x_ajuste, a, b)
        linea, = ax.plot(x_ajuste, y_ajuste, linestyle=lineatenden, linewidth=grosortenden,
                         color=colortenden, label=f'Logarítmica {prisma}')
        # Calcular R cuadrado
        r_squared = r_value**2
        return linea, f"y = {a:.6f} * ln(x) + {b:.6f}    R²={r_squared:.6f}"
    
    def funcionLogaritmica(x, a, b):
        return a * np.log(x) + b
    
    def dibujarMediaMovil(timestamps, displacements, ax, tor_name, ventana_media_movil, lineatenden, grosortenden, colortenden):
        media_movil = CalculosTendencias.calcularMediaMovil(displacements, ventana_media_movil)
        linea, = ax.plot(timestamps[ventana_media_movil - 1:], media_movil, linestyle=lineatenden, linewidth=grosortenden,
                         color=colortenden, label=f'Media Móvil {tor_name}')
        return linea
    
    def calcularMediaMovil(data, ventana):
        media_movil = []
        for i in range(len(data) - ventana + 1):
            media = sum(data[i:i+ventana]) / ventana
            media_movil.append(media)
        return media_movil
    
    def dibujarTendenciaExponencial(horas, valores, ax, forma_grafica, prisma, lineatenden, grosortenden, colortenden):
        timestamps = []
        displacements = []
        for fecha, desplaza in zip(horas, valores):
            if desplaza is not None and desplaza != "":
                timestamps.append(fecha)
                displacements.append(desplaza)
        try:
            timestamps = timestamps[1:]
            displacements = displacements[1:]
            if forma_grafica == 'FECHA':
                x = mdates.date2num(timestamps)
                params, covariance = curve_fit(CalculosTendencias.funcionExponencial, mdates.date2num(timestamps), displacements)
                a, b = params
                # Crear puntos para la línea de regresión potencial
                x_fit = np.linspace(min(mdates.date2num(timestamps)), max(mdates.date2num(timestamps)), 100)
                y_fit = CalculosTendencias.funcionExponencial(x_fit, a, b)
                # Convertir las fechas de nuevo a objetos de fecha
                x_fit = mdates.num2date(x_fit)
                rcuadrado = CalculosTendencias.calcularRcuadradoExponentencial(displacements, CalculosTendencias.funcionExponencial(mdates.date2num(timestamps), *params))
            else:
                # Ajustar una regresión potencial (exponencial)
                params, covariance = curve_fit(CalculosTendencias.funcionExponencial, timestamps, displacements)
                a, b = params
                # Crear puntos para la línea de regresión potencial
                x_fit = np.linspace(min(timestamps), max(timestamps), 100)
                y_fit = CalculosTendencias.funcionExponencial(x_fit, a, b)
                rcuadrado = CalculosTendencias.calcularRcuadradoExponentencial(displacements, CalculosTendencias.funcionExponencial(timestamps, *params))
            linea, = ax.plot(x_fit, y_fit, linestyle=lineatenden, linewidth=grosortenden, color=colortenden, label=f'Exponencial {prisma}')
            return linea, f"y = {a:.6f} * e^({b:.6f}x)    R²={rcuadrado:.6f}"
        except Exception as e:
            return None, ""
    
    def funcionExponencial(x, a, b):
        return a * np.exp(b * x)
    
    def dibujarTendenciaPotencial(horas, valores, ax, forma_grafica, prisma, lineatenden, grosortenden, colortenden):
        timestamps = []
        displacements = []
        for fecha, desplaza in zip(horas, valores):
            if desplaza is not None and desplaza != "":
                timestamps.append(fecha)
                displacements.append(desplaza)
        try:
            timestamps = timestamps[1:]
            displacements = displacements[1:]
            if forma_grafica == 'FECHA':
                params, covariance = curve_fit(CalculosTendencias.funcionPotencial, mdates.date2num(timestamps), displacements)
                a, b = params
                # Crear puntos para la línea de regresión potencial
                x_fit = np.linspace(min(mdates.date2num(timestamps)), max(mdates.date2num(timestamps)), 100)
                y_fit = CalculosTendencias.funcionPotencial(x_fit, a, b)
                # Convertir las fechas de nuevo a objetos de fecha
                x_fit = mdates.num2date(x_fit)
                rcuadrado = CalculosTendencias.calcularRcuadradoExponentencial(displacements, CalculosTendencias.funcionPotencial(mdates.date2num(timestamps), *params))
            else:
                # Ajustar una regresión potencial (exponencial)
                params, covariance = curve_fit(CalculosTendencias.funcionPotencial, timestamps, displacements)
                a, b = params
                # Crear puntos para la línea de regresión potencial
                x_fit = np.linspace(min(timestamps), max(timestamps), 100)
                y_fit = CalculosTendencias.funcionPotencial(x_fit, a, b)
                rcuadrado = CalculosTendencias.calcularRcuadradoExponentencial(displacements, CalculosTendencias.funcionPotencial(timestamps, *params))
            linea, = ax.plot(x_fit, y_fit, linestyle=lineatenden, linewidth=grosortenden, color=colortenden, label=f'Potencial {prisma}')
            return linea, f"y = {a:.6f} * x^{b:.6f}    R²={rcuadrado:.6f}"
        except Exception as e:
            return None, ""
    
    def funcionPotencial(x, a, b):
        return a * np.power(x, b)
    
    def calcularRcuadradoExponentencial(y_real, y_pred):
        residuos = y_real - y_pred
        ss_res = np.sum(residuos ** 2)
        ss_tot = np.sum((y_real - np.mean(y_real)) ** 2)
        if ss_tot != 0:
            return 1 - (ss_res / ss_tot)
        else:
            return 1
    
    def limpiezaAutomaticaSaltos(data, grupos_aplicar, indexinstru, indexcol):
        grupos = defaultdict(list)
        # Agrupar los datos por nombre
        for col in data:
            grupos[col[indexinstru]].append(col)
        nuevos_datos_formateados = []
        # Recorrer cada grupo
        for idinstrumento, datos in grupos.items():
            if str(idinstrumento) in [str(tupla[0]) for tupla in grupos_aplicar]:
                datos_limpios = np.array([dt for dt in datos if dt[indexcol] is not None and dt[indexcol] != ''])
                datos_valor = np.array([float(d[indexcol]) for d in datos_limpios])
                # Aplicar suavizado exponencial con alpha dinámico
                alpha = CalculosTendencias.calcularAlpha(datos_valor)
                datos_valor_suavizados = CalculosTendencias.suavizarExponencial(datos_valor, alpha)
                # Remover o reemplazar outliers usando Grubbs test
                datos_ajustados = CalculosTendencias.reemplazarOutliers(datos_valor_suavizados)
                # Cambiamos los datos normalizados
                df = pd.DataFrame(datos_limpios, columns=[f'Col_{i+1}' for i in range(len(datos_limpios[0]))])
                df[f'Col_{indexcol+1}'] = datos_ajustados
                datos = list(df.itertuples(index=False, name=None))
            nuevos_datos_formateados.extend(datos)
        return nuevos_datos_formateados
    
    def calcularAlpha(datos):
        std = np.std(datos)
        alpha = 0.4 / (1 + np.log1p(std))
        return alpha

    def suavizarExponencial(datos, alpha):
        smoothed_data = np.zeros_like(datos)
        smoothed_data[0] = datos[0]
        for i in range(1, len(datos)):
            smoothed_data[i] = alpha * datos[i] + (1 - alpha) * smoothed_data[i - 1]
        return smoothed_data

    def reemplazarOutliers(datos):
        n = len(datos)
        mean = np.mean(datos)
        std_dev = np.std(datos)
        # Calcular estadístico de Grubbs
        G_critical = stats.t.ppf(0.975, n - 2) * (std_dev / np.sqrt((n - 1) * (n - 2)))
        # Crear una copia de los datos para no modificar el original directamente
        datos_sin_outliers = datos.copy()
        # Encontrar outliers y reemplazar por valores cercanos
        for i in range(n):
            if np.abs(datos[i] - mean) > G_critical:
                if i > 0 and i < n - 1:
                    datos_sin_outliers[i] = (datos[i - 1] + datos[i + 1]) / 2
                elif i == 0:
                    datos_sin_outliers[i] = datos[i + 1]
                else:
                    datos_sin_outliers[i] = datos[i - 1]
        return datos_sin_outliers
    
    def limpiezaManualSaltos(data, grupos_aplicar, indexinstru, indexcol):
        grupos = defaultdict(list)
        # Agrupar los datos por nombre
        for col in data:
            grupos[col[indexinstru]].append(col)
        nuevos_datos_formateados = []
        # Recorrer cada grupo
        for idinstrumento, datos in grupos.items():
            for tupla in grupos_aplicar:
                if str(idinstrumento) == str(tupla[0]):
                    datos_limpios = np.array([dt for dt in datos if dt[indexcol] is not None and dt[indexcol] != ''])
                    datos_valor = np.array([float(d[indexcol]) for d in datos_limpios])
                    datos_ajustados = CalculosTendencias.aplicarPatronDesplazamiento(datos_valor, tupla[1])
                    # Cambiamos los datos normalizados
                    df = pd.DataFrame(datos_limpios, columns=[f'Col_{i+1}' for i in range(len(datos_limpios[0]))])
                    df[f'Col_{indexcol+1}'] = datos_ajustados
                    datos = list(df.itertuples(index=False, name=None))
            nuevos_datos_formateados.extend(datos)
        return nuevos_datos_formateados
    
    def aplicarPatronDesplazamiento(datos, salto_maximo):
        valores_atipicos = []
        threshold_multiplier = salto_maximo
        std = np.std(datos)
        threshold = threshold_multiplier * std
        valor_resta = datos[0]
        for i in range(1, len(datos)):
            resta = abs(datos[i] - valor_resta)
            if resta > threshold:
                valores_atipicos.append(i)
                datos[i] = valor_resta
            else:
                valor_resta = datos[i]
        return datos
    
    def ajustarCalculoSaltos(data, grupos_aplicar, indexinstru, indexcol):
        grupos = defaultdict(list)
        # Agrupar los datos por nombre
        for col in data:
            grupos[col[indexinstru]].append(col)
        nuevos_datos_formateados = []
        # Recorrer cada grupo
        for idinstrumento, datos in grupos.items():
            if str(idinstrumento) in [str(tupla[0]) for tupla in grupos_aplicar]:
                datos_limpios = np.array([dt for dt in datos if dt[indexcol] is not None and dt[indexcol] != ''])
                datos_valor = np.array([float(d[indexcol]) for d in datos_limpios])
                datos_ajustados = CalculosTendencias.recalcularData(datos_valor)
                # Cambiamos los datos normalizados
                df = pd.DataFrame(datos_limpios, columns=[f'Col_{i+1}' for i in range(len(datos_limpios[0]))])
                df[f'Col_{indexcol+1}'] = datos_ajustados
                datos = list(df.itertuples(index=False, name=None))
            nuevos_datos_formateados.extend(datos)
        return nuevos_datos_formateados
    
    def recalcularData(data):
        threshold_multiplier = 2
        std = np.std(data)
        threshold = threshold_multiplier * std
        differences = np.diff(data)
        if len(differences) == 0 or np.max(np.abs(differences)) <= threshold:
            return data
        first_jump_index = np.where(np.abs(differences) > threshold)[0][0]
        differences_after_jump = np.diff(data[first_jump_index + 1:])
        # Reemplazar el valor del salto por el valor anterior
        data[first_jump_index + 1] = data[first_jump_index]
        # Completar los demás datos con las diferencias después del salto
        data[first_jump_index + 2:] = differences_after_jump
        return data
    
    def aplicarMetodoLimpiezaIQRestadistico(data, indexcol, tipo, valorK):
        nuevos_datos_formateados = []
        datos_limpios = np.array([dt for dt in data if dt[indexcol] is not None and dt[indexcol] != ''])
        datos_valor = np.array([float(d[indexcol]) for d in datos_limpios])
        if tipo == "IQR":
            datos_ajustados = CalculosTendencias.metodoIQR(datos_valor)
        else:
            datos_ajustados = CalculosTendencias.metodoEstadistico(datos_valor, valorK)
        # Cambiamos los datos normalizados
        if len(datos_ajustados) < len(datos_limpios):
            num_filas_a_eliminar = len(datos_limpios) - len(datos_ajustados)
            datos_limpios = datos_limpios[:-num_filas_a_eliminar]
        # Crear DataFrame con los datos truncados
        if datos_ajustados:
            df = pd.DataFrame(datos_limpios, columns=[f'Col_{i+1}' for i in range(len(datos_limpios[0]))])
            df[f'Col_{indexcol+1}'] = datos_ajustados
            datos = list(df.itertuples(index=False, name=None))
            nuevos_datos_formateados.extend(datos)
        return nuevos_datos_formateados
    
    def metodoIQR(data):
        # Calcular cuartiles
        valQ1 = np.percentile(data, 25)
        valQ3 = np.percentile(data, 75)
        # Calcular el rango intercuartílico (IQR)
        valIQR = valQ3 - valQ1
        # Definir límites para identificar valores atípicos
        limite_inferior = valQ1 - 1.5 * valIQR
        limite_superior = valQ3 + 1.5 * valIQR
        filas_filtradas_iqr = [fila for fila in data if limite_inferior <= fila <= limite_superior]
        return filas_filtradas_iqr
    
    def metodoEstadistico(data, valorK):
        datos = np.array(data)
        media = np.mean(datos)
        desviacion_estandar = np.std(datos)
        # Calcular el límite inferior y superior basado en el teorema de Chebyshev
        limite_inferior = media - valorK * desviacion_estandar
        limite_superior = media + valorK * desviacion_estandar
        datos_filtrados = [fila for fila in data if limite_inferior <= fila <= limite_superior]
        return datos_filtrados
    
    def limpiezaAutomaticaTrayectoria(data):
        grupos = defaultdict(list)
        # Agrupar los datos por idinstrumento
        for col in data:
            grupos[col[0]].append(col)
        nuevos_datos_formateados = []
        # Recorrer cada grupo
        for idinstrumento, datos in grupos.items():
            datos_limpios = [dt for dt in datos if all(dt[i] not in (None, '') for i in (3, 4, 5))]
            if len(datos_limpios) > 3:
                primera_lectura = datos_limpios[0]
                data_restante = datos_limpios[1:]
                # Extraer columnas 3, 4, 5 usando numpy para eficiencia
                arr = np.array(data_restante, dtype=object)
                datos_x = arr[:, 3].astype(float)
                datos_y = arr[:, 4].astype(float)
                datos_z = arr[:, 5].astype(float)
                # Aplicar suavizado exponencial con alpha dinámico
                alphax = CalculosTendencias.calcularAlpha(datos_x)
                alphay = CalculosTendencias.calcularAlpha(datos_y)
                alphaz = CalculosTendencias.calcularAlpha(datos_z)
                valorx_suavizados = CalculosTendencias.suavizarExponencial(datos_x, alphax)
                valory_suavizados = CalculosTendencias.suavizarExponencial(datos_y, alphay)
                valorz_suavizados = CalculosTendencias.suavizarExponencial(datos_z, alphaz)
                # Remover o reemplazar outliers usando Grubbs test
                datosx_ajustados = CalculosTendencias.reemplazarOutliers(valorx_suavizados)
                datosy_ajustados = CalculosTendencias.reemplazarOutliers(valory_suavizados)
                datosz_ajustados = CalculosTendencias.reemplazarOutliers(valorz_suavizados)
                # Reconstrucción usando zip sin bucles manuales
                cabeceras = arr[:, :3]  # columnas: id, nombre, fecha
                reconstruido = list(zip(
                    cabeceras[:, 0], cabeceras[:, 1], cabeceras[:, 2],
                    datosx_ajustados, datosy_ajustados, datosz_ajustados
                ))
                # Convertir todo a tuplas nativas
                nuevos_datos_formateados.append(primera_lectura)
                nuevos_datos_formateados.extend(map(tuple, reconstruido))
            else:
                nuevos_datos_formateados.extend(datos)
        return nuevos_datos_formateados
    