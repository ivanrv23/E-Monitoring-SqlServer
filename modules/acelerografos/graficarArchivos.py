import os
import re
import numpy as np
import concurrent.futures
import matplotlib.pyplot as plt
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QDateEdit, QTimeEdit, QPushButton, QLabel, QGridLayout, QWidget, 
                              QHBoxLayout, QSpacerItem, QSizePolicy,QFileDialog)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from utils.common.rutasarchivos import resource_path
from utils.common.alertas import mostrar_mensaje
from PySide6.QtCore import QDate, QTime
from scipy.integrate import cumulative_trapezoid
from modules.empresa.softwareconfiguracion import SoftwareConfiguracion
from controllers.ConfiguracionController import ConfiguracionController
from pyrocko import io
from pyrocko.util import time_to_str
import xml.etree.ElementTree as ET
import pandas as pd
import shutil

def mostrar_grafico_en_widget(widget, fig):
    # Limpiar el widget si ya tiene contenido
    layout = widget.layout()
    if layout is None:
        layout = QVBoxLayout(widget)
        widget.setLayout(layout)
    else:
        # Eliminar widgets anteriores
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    # Crear canvas
    canvas = FigureCanvas(fig)
    # Crear toolbar personalizado
    toolbar_container = QWidget()
    toolbar_layout = QHBoxLayout(toolbar_container)
    toolbar_layout.setContentsMargins(10, 2, 10, 5)  # Márgenes: izquierda, arriba, derecha, abajo
    # Crear toolbar estándar
    toolbar = NavigationToolbar(canvas, toolbar_container)
    # Añadir espaciador para alinear a la izquierda
    spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
    # Agregar elementos al layout del toolbar
    toolbar_layout.addWidget(toolbar)
    toolbar_layout.addItem(spacer)
    # Agregar al layout principal
    layout.addWidget(canvas)
    layout.addWidget(toolbar_container)
    # Dibujar la figura
    canvas.draw()

# Convertir tiempos a segundos
def hora_a_segundos(hora_str):
    h, m, s = map(float, hora_str.split(':'))
    return h*3600 + m*60 + s

# =============================================================================
# FUNCIONES DE MANEJO DE CACHÉ (CORREGIDAS)
# =============================================================================
def obtener_ruta_cache(archivo_mseed):
    base_name = os.path.basename(archivo_mseed)
    # Usar expresión regular para extraer componente y fecha correctamente
    patron = re.compile(r'^.+\.(HN[E|N|Z])\.D?\.(\d{4}\.\d{3})$')
    match = patron.match(base_name)
    if match:
        componente = match.group(1)
        fecha = match.group(2)
        # Construir nombre de caché: calculos_<componente>.<fecha>.npz
        cache_name = f"calculos_{componente}.{fecha}.npz"
        directorio = os.path.dirname(archivo_mseed)
        return os.path.join(directorio, cache_name)
    return None  # Si no coincide con el patrón

def guardar_cache(tiempo, acc_mps2, acc_g, vel, desp, cache_path):
    if cache_path is None:
        return
    np.savez(cache_path, 
             tiempo=tiempo, 
             acc_mps2=acc_mps2,
             acc_g=acc_g,
             vel=vel,
             desp=desp)

def cargar_cache(cache_path, tipo_grafico, unidad_g=False, tmin=None, tmax=None):
    if cache_path is None or not os.path.exists(cache_path):
        return None, None, None
    
    # Cargar el archivo NPZ
    datos_cache = np.load(cache_path)
    tiempo = datos_cache['tiempo']
    
    # Seleccionar datos según tipo de gráfico
    if tipo_grafico == 'cuentas':
        # No guardamos cuentas en caché, requiere procesamiento original
        return None, None, None
    elif tipo_grafico == 'AAC':
        if unidad_g:
            datos = datos_cache['acc_g']
            unidad = 'g'
        else:
            datos = datos_cache['acc_mps2']
            unidad = 'm/s²'
    elif tipo_grafico == 'AVE':
        datos = datos_cache['vel']
        unidad = 'm/s'
    elif tipo_grafico == 'ADE':
        datos = datos_cache['desp']
        unidad = 'm'
    else:
        return None, None, None
    
    # Recortar si se especifican tmin y tmax
    if tmin is not None or tmax is not None:
        start_idx = 0
        end_idx = len(tiempo) - 1
        if tmin is not None:
            start_idx = np.searchsorted(tiempo, tmin, side='left')
        if tmax is not None:
            end_idx = np.searchsorted(tiempo, tmax, side='right') - 1
        tiempo_recortado = tiempo[start_idx:end_idx+1]
        datos_recortados = datos[start_idx:end_idx+1]
        return tiempo_recortado, datos_recortados, unidad
    else:
        return tiempo, datos, unidad

# =============================================================================
# MÓDULO DE PROCESAMIENTO DE SEÑALES
# =============================================================================
def cargar_traza(archivo_mseed):
    traza = io.load(archivo_mseed)[0]
    t_abs = traza.get_xdata()
    t_rel = t_abs - t_abs[0]
    return traza, t_rel, traza.ydata

def obtener_componente(archivo_mseed):
    # Usar expresión regular para extraer el componente correctamente
    patron = re.compile(r'^.+\.(HN[E|N|Z])\.D?\.\d{4}\.\d{3}$')
    match = patron.match(os.path.basename(archivo_mseed))
    if match:
        return match.group(1)
    return "UNK"  # Valor por defecto si no se encuentra

def buscar_sensibilidad_xml(xml_root, componente, ns):
    for channel in xml_root.findall(".//ns:Channel", namespaces=ns):
        if channel.get("code", "").strip() == componente:
            inst_sens = channel.find('ns:Response/ns:InstrumentSensitivity/ns:Value', namespaces=ns)
            if inst_sens is not None:
                return float(inst_sens.text)
    return 92354.24942939453  # Valor por defecto si no se encuentra

def obtener_frecuencia_muestreo(xml_root, componente, ns):
    for channel in xml_root.findall(".//ns:Channel", namespaces=ns):
        if channel.get("code", "").strip() == componente:
            sample_rate = channel.find('ns:SampleRate', namespaces=ns)
            if sample_rate is not None:
                return float(sample_rate.text)
    return 100.0  # Valor por defecto

def procesar_senal(counts, sensitivity, fs, tipo_grafico, unidad_g=False):
    dt = 1.0 / fs
    acc = counts / sensitivity
    
    if tipo_grafico == 'cuentas':
        return counts, 'Cuentas'
    
    elif tipo_grafico == 'AAC':
        if unidad_g:
            return acc / 9.80665, 'g'
        return acc, 'm/s²'
    
    elif tipo_grafico == 'AVE':
        vel = cumulative_trapezoid(acc, dx=dt, initial=0)
        return vel, 'm/s'
    
    elif tipo_grafico == 'ADE':
        vel = cumulative_trapezoid(acc, dx=dt, initial=0)
        desp = cumulative_trapezoid(vel, dx=dt, initial=0)
        return desp, 'm'
    
    raise ValueError("Tipo de gráfico no válido")

def recortar_datos(t, datos, tmin_plot=None, tmax_plot=None):
    """Recorta los datos al intervalo temporal especificado"""
    tmin = tmin_plot if tmin_plot is not None else t[0]
    tmax = tmax_plot if tmax_plot is not None else t[-1]
    mask = (t >= tmin) & (t <= tmax)
    return t[mask], datos[mask]

def procesar_componente(archivo_mseed, xml_root, tipo_grafico, fs=None, unidad_g=False, tmin_plot=None, tmax_plot=None, color=None, ns=None):
    # Obtener ruta de caché
    cache_path = obtener_ruta_cache(archivo_mseed)
    componente = obtener_componente(archivo_mseed)
    # Intentar cargar desde caché si existe
    if cache_path and os.path.exists(cache_path):
        try:
            t_plot, datos_plot, unidad = cargar_cache(cache_path, tipo_grafico, unidad_g, tmin_plot, tmax_plot)
            if t_plot is not None:
                # Obtener metadatos necesarios desde el archivo original
                traza = io.load(archivo_mseed, getdata=False)[0]  # Solo metadatos
                fs_val = fs or obtener_frecuencia_muestreo(xml_root, componente, ns)
                return {
                    'componente': componente,
                    't_plot': t_plot,
                    'datos_plot': datos_plot,
                    'unidad': unidad,
                    't_full': t_plot,
                    'datos_full': datos_plot,
                    'fs': fs_val,
                    'tmin': traza.tmin,
                    'tmax': traza.tmax,
                    'color': color
                }
        except Exception as e:
            print(f"  ERROR cargando caché: {e}. Reprocesando...")
    # Si no hay caché válido, procesar normalmente
    traza, t, counts = cargar_traza(archivo_mseed)
    # Obtener parámetros del sensor
    sensitivity = buscar_sensibilidad_xml(xml_root, componente, ns)
    fs_val = fs or obtener_frecuencia_muestreo(xml_root, componente, ns)
    dt = 1.0 / fs_val
    # Procesar señal: calcular todas las derivadas
    acc_mps2 = counts / sensitivity
    acc_g = acc_mps2 / 9.80665
    # Calcular velocidad (integral de aceleración)
    vel = cumulative_trapezoid(acc_mps2, dx=dt, initial=0)
    # Calcular desplazamiento (integral de velocidad)
    desp = cumulative_trapezoid(vel, dx=dt, initial=0)
    # Guardar en caché
    if cache_path:
        try:
            guardar_cache(t, acc_mps2, acc_g, vel, desp, cache_path)
        except Exception as e:
            print(f"  ERROR guardando caché: {e}")
    # Seleccionar datos según tipo de gráfico
    if tipo_grafico == 'cuentas':
        datos_full = counts
        unidad = 'Cuentas'
    elif tipo_grafico == 'AAC':
        datos_full = acc_g if unidad_g else acc_mps2
        unidad = 'g' if unidad_g else 'm/s²'
    elif tipo_grafico == 'AVE':
        datos_full = vel
        unidad = 'm/s'
    elif tipo_grafico == 'ADE':
        datos_full = desp
        unidad = 'm'
    else:
        raise ValueError("Tipo de gráfico no válido")
    # Recortar datos para visualización
    if tmin_plot is not None or tmax_plot is not None:
        start_idx = 0
        end_idx = len(t) - 1
        if tmin_plot is not None:
            start_idx = np.searchsorted(t, tmin_plot, side='left')
        if tmax_plot is not None:
            end_idx = np.searchsorted(t, tmax_plot, side='right') - 1
        t_plot = t[start_idx:end_idx+1]
        datos_plot = datos_full[start_idx:end_idx+1]
    else:
        t_plot = t
        datos_plot = datos_full
    
    return {
        'componente': componente,
        't_plot': t_plot,
        'datos_plot': datos_plot,
        'unidad': unidad,
        't_full': t,
        'datos_full': datos_full,
        'fs': fs_val,
        'tmin': traza.tmin,
        'tmax': traza.tmax,
        'color': color
    }

# =============================================================================
# MÓDULO DE EJECUCIÓN PARALELA
# =============================================================================
def procesar_paralelamente(archivos, xml_root, tipo_grafico, colores, unidad_g=False, tmin_plot=None, tmax_plot=None, ns=None):
    resultados = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for i, arch in enumerate(archivos):
            # Obtener color para este componente
            color = colores[i] if i < len(colores) else 'blue'
            # Enviar a procesamiento
            future = executor.submit(
                procesar_componente,
                arch,
                xml_root,
                tipo_grafico,
                None,  # fs (se determinará automáticamente)
                unidad_g,
                tmin_plot,
                tmax_plot,
                color,
                ns
            )
            futures.append(future)
        
        # Recoger resultados
        for future in concurrent.futures.as_completed(futures):
            resultados.append(future.result())
    
    return resultados

# =============================================================================
# MÓDULO DE VISUALIZACIÓN
# =============================================================================
def generar_titulo(tipo_grafico, nombre_acelerografo, unidad_g,fecha, tmin, tmax):
    fecha_str = time_to_str(fecha, format='%Y-%m-%d')
    if tipo_grafico == 'AAC':
        unidad_str = " (g)" if unidad_g else " (m/s²)"
        tipo_grafico_str = "Aceleración"
    elif tipo_grafico == 'AVE':
        unidad_str = " (m/s)"
        tipo_grafico_str = "Velocidad"
    elif tipo_grafico == 'ADE':
        unidad_str = " (m)"
        tipo_grafico_str = "Desplazamiento"
    else:
        unidad_str = ""
        tipo_grafico_str = "Desconocido"

    return f'Estación {nombre_acelerografo} - {tipo_grafico_str}{unidad_str} {fecha_str} ({tmin} - {tmax})'


def configurar_graficos(resultados, titulo_principal, ejeymin, ejeymax, ejeyprin, ejeysecu, intervalox):
    avisolabels = False
    config = SoftwareConfiguracion.obtenerDataSoftware()
    titulozise, ejezise, etiquesize, fuente, decimales = config[0], config[1], config[2], config[10], config[14]
    # configurar
    num_componentes = len(resultados)
    fig, axs = plt.subplots(num_componentes, 1, figsize=(12, 3 * num_componentes), sharex=True)
    plt.rcParams['font.family'] = fuente
    
    # Aumentar altura por componente y espacio entre subplots
    fig, axs = plt.subplots(
        num_componentes, 
        1, 
        figsize=(12, 3.8 * num_componentes),  # Aumentar altura
        sharex=True,
        gridspec_kw={'hspace': 0.5}  # Más espacio entre gráficos
    )
    
    if num_componentes == 1:
        axs = [axs]
    
    for i, res in enumerate(resultados):
        ax = axs[i]
        t_plot = res['t_plot']
        datos_plot = res['datos_plot']
        color_traza = res['color']
        ax.plot(t_plot, datos_plot, color=color_traza, linewidth=0.8)
        ax.set_ylabel(res['unidad'], fontsize=ejezise)
        ax.set_title(f'Componente {res["componente"]}', fontsize=ejezise, pad=10)
        ax.set_ylabel(res['unidad'], fontsize=10, labelpad=10)  # Añadir padding
        ax.set_title(f'Componente {res["componente"]}', fontsize=12, pad=15)  # Aumentar padding vertical
        ax.grid(True, linestyle=':', alpha=0.6)
        ax.tick_params(axis='both', which='major', labelsize=9)
        
        # Encontrar el valor máximo en magnitud absoluta
        max_idx = np.argmax(np.abs(datos_plot))
        max_time = t_plot[max_idx]
        max_val = datos_plot[max_idx]
        
        # Añadir línea vertical punteada con color de la traza
        ax.axvline(x=max_time, color=color_traza, linestyle=':', alpha=0.7, linewidth=1.2)
        
        # Añadir marcador circular cerrado con el color de la traza
        ax.plot(max_time, max_val, 'o', markersize=6, color=color_traza)
        
        # Crear texto para la etiqueta con "@" y color de la traza
        texto = f"Pico: {max_val:.6f} {res['unidad']} @ {max_time:.2f} s"
        
        # Posicionar en esquina superior derecha con margen
        x_pos = 0.98  # 98% del ancho del eje x
        y_pos = 0.88  # Reducir posición vertical para evitar superposición
        
        # Añadir etiqueta con fondo blanco y texto del color de la traza
        ax.text(
            x_pos, 
            y_pos, 
            texto, 
            transform=ax.transAxes,
            fontsize=9, 
            color=color_traza,
            verticalalignment='top', 
            horizontalalignment='right',
            bbox=dict(
                facecolor='white', 
                alpha=0.8, 
                edgecolor='gray', 
                boxstyle='round,pad=0.3'
            )
        )
        
        if i == num_componentes - 1:
            ax.set_xlabel('Tiempo desde inicio (s)', fontsize=ejezise)
            ax.set_xlabel('Tiempo desde inicio (s)', fontsize=10, labelpad=10)
        
        # CONFIGURAR EJE Y
        if ejeymin != 0 or ejeymax != 0:
            ax.set_ylim(ejeymin, ejeymax)
            # Calcula los intervalos primarios
            maxejey = ejeymax + 0.0001
            if ejeyprin > 0:
                tick_primarios = np.arange(ejeymin, maxejey, ejeyprin)
                if len(tick_primarios) > 2 and len(tick_primarios) < 50:
                    ax.set_yticks(tick_primarios)
                else:
                    avisolabels = True
            # Calcula los intervalos secundarios
            if ejeysecu > 0:
                tick_secundarios = np.arange(ejeymin, maxejey, ejeysecu)
                if len(tick_secundarios) > 2 and len(tick_secundarios) < 100:
                    for tick in tick_secundarios:
                        ax.axhline(y=tick, color='gray', linestyle='--', linewidth=0.5)
                else:
                    avisolabels = True
        else:
            ymax = np.max(np.abs(datos_plot)) * 1.15
            ax.set_ylim(-ymax, ymax)
        # Formatear el eje Y
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda val, pos: '{:.{}f}'.format(val, decimales)))
        # Ajustar padding de etiquetas Y
        ax.tick_params(axis='y', pad=5)  # Más espacio entre etiquetas y eje
        # CONFIGURAR EJE X
        start, end = t_plot[0], t_plot[-1]
        if intervalox > 0:
            ax.set_xlim(start, end)
            dias_range = np.arange(start, end, intervalox)
            if len(dias_range) > 2 and len(dias_range) < 100:
                if dias_range[-1] < end:
                    dias_range = np.append(dias_range, end)
                ax.set_xticks(dias_range)
            else:
                avisolabels = True
        ax.tick_params(axis='y', labelsize=etiquesize)
    ax.tick_params(axis='x', labelsize=etiquesize)
    fig.suptitle(titulo_principal, fontsize=titulozise, y=0.98)
    fig.subplots_adjust(top=0.9, bottom=0.1, left=0.1, right=0.95, hspace=0.1)
    return fig, avisolabels

def procesar_graficos_acelerografos(widget_grafico, tipo_grafico, proyecto_id, id_acelerografo, nombre_acelerografo, unidad_g, fecha_analisis=None, tiempo_minimo=None, tiempo_maximo=None):
    try:
        tmin_plot = hora_a_segundos(tiempo_minimo) if tiempo_minimo else None
        tmax_plot = hora_a_segundos(tiempo_maximo) if tiempo_maximo else None
        colores = ['red', 'blue', 'green']
        # Construir ruta base usando os.path.join
        ruta_base = os.path.join(
            resource_path('resources'),
            'workspace',
            'ACELEROGRAFOS',
            f'proyecto{proyecto_id}',
            str(id_acelerografo))
        
        # Verificar si existe el directorio
        if not os.path.exists(ruta_base):
            mostrar_mensaje("Error", f"Directorio no encontrado: {ruta_base}", "error")
            return
        
        # Buscar archivo XML
        archivos_xml = [a for a in os.listdir(ruta_base) if a.lower().endswith('.xml')]
        if not archivos_xml:
            mostrar_mensaje("Error", f"No se encontró archivo XML para {nombre_acelerografo}", "error")
            return
        
        # Cargar inventario desde XML
        archivo_xml = os.path.join(ruta_base, archivos_xml[0])
        
        # Patrones para buscar archivos de datos
        patron_archivo = re.compile(r'^.+\.(HN[E|N|Z])\.D?\.(\d{4}\.\d{3})$')
        archivos_por_fecha = {}
        
        # Listar archivos usando rutas completas
        for nombre_archivo in os.listdir(ruta_base):
            ruta_completa = os.path.join(ruta_base, nombre_archivo)
            
            if not os.path.isfile(ruta_completa):
                continue
                
            match = patron_archivo.match(nombre_archivo)
            if match:
                componente = match.group(1)
                fecha = match.group(2)
                if fecha not in archivos_por_fecha:
                    archivos_por_fecha[fecha] = []
                archivos_por_fecha[fecha].append(ruta_completa)
        
        # Seleccionar fecha
        fecha_seleccionada = None
        if fecha_analisis:
            # Formato: AAAA.DDD
            fecha_str = f"{fecha_analisis[0]}.{fecha_analisis[1]:03d}"
            if fecha_str in archivos_por_fecha:
                fecha_seleccionada = fecha_str
        else:
            fechas_ordenadas = sorted(archivos_por_fecha.keys(), reverse=True)
            fecha_seleccionada = fechas_ordenadas[0] if fechas_ordenadas else None
        
        if not fecha_seleccionada:
            mostrar_mensaje("Error", "No se encontraron archivos para la fecha seleccionada.", "error")
            return
        
        # Tomar los tres últimos archivos de la fecha seleccionada (rutas completas)
        archivos = archivos_por_fecha[fecha_seleccionada][-3:]
        # Cargar XML
        tree = ET.parse(archivo_xml)
        ns = {'ns': 'http://www.fdsn.org/xml/station/1'}

        # Procesamiento paralelo
        resultados = procesar_paralelamente(
            archivos, tree.getroot(), tipo_grafico, colores, 
            unidad_g, tmin_plot, tmax_plot, ns
        )
        resultados_ordenados = sorted(resultados, key=lambda x: x['componente'])
        
        # Generar y mostrar en widget
        titulo_principal = generar_titulo(tipo_grafico,nombre_acelerografo, unidad_g, resultados_ordenados[0]['tmin'], tiempo_minimo,tiempo_maximo)
        # Ajustar limites de gráficas eje y
        ejeymin, ejeymax, ejeyprin, ejeysecu, intervalo_dias = 0, 0, 0, 0, 0
        dataeje = ConfiguracionController.ctrlObtenerConfiguracionEje(proyecto_id, "ACELEROGRAFOS", tipo_grafico)
        if dataeje:
            ejeymin, ejeymax, ejeyprin, ejeysecu, intervalo_dias = dataeje[4], dataeje[5], dataeje[6], dataeje[7], dataeje[8]
        fig, aviso = configurar_graficos(resultados_ordenados, titulo_principal, ejeymin, ejeymax, ejeyprin, ejeysecu, intervalo_dias)
        mostrar_grafico_en_widget(widget_grafico, fig)  # Mostrar en widget
        if aviso:
            mostrar_mensaje("Ejes", "No se aplicó la configuración de ejes.", "advertencia")
    except Exception as e:
        mostrar_mensaje("Error", f"Error de procesamiento: {str(e)}", "error")

def hora_a_segundos(hora_str):
    """Convierte tiempo en formato HH:MM:SS a segundos desde la medianoche"""
    h, m, s = map(float, hora_str.split(':'))
    return h * 3600 + m * 60 + s

def hora_a_segundos(hora_str):
    """Convierte tiempo en formato HH:MM:SS a segundos desde la medianoche"""
    h, m, s = map(float, hora_str.split(':'))
    return h * 3600 + m * 60 + s

def generar_csvs_para_fecha(proyecto_id, id_acelerografo, tipo_dato, 
                           fecha_analisis=(2025, 171), 
                           hora_analisis=('14:28:00', '15:28:00'), 
                           unidadg=False):
    try:
        # Convertir horas a segundos
        tmin_sec = hora_a_segundos(hora_analisis[0])
        tmax_sec = hora_a_segundos(hora_analisis[1])
        
        # Construir ruta base del acelerógrafo
        ruta_base = os.path.join(
            resource_path('resources'),
            'workspace',
            'ACELEROGRAFOS',
            f'proyecto{proyecto_id}',
            str(id_acelerografo)
        )
        
        # Verificar si existe el directorio
        if not os.path.exists(ruta_base):
            mostrar_mensaje("Error", f"Directorio no encontrado: {ruta_base}", "error")
            return None
        
        # Mapeo de tipo de dato
        mapeo_datos = {
            'AAC': 'aceleracion',
            'aceleracion': 'aceleracion',
            'AVE': 'velocidad',
            'velocidad': 'velocidad',
            'ADE': 'desplazamiento',
            'desplazamiento': 'desplazamiento'
        }
        
        if tipo_dato not in mapeo_datos:
            mostrar_mensaje("Error", f"Tipo de dato no válido: {tipo_dato}", "error")
            return None
            
        tipo_espanol = mapeo_datos[tipo_dato]
        
        # Obtener año y día juliano
        año = fecha_analisis[0]
        dia_juliano = fecha_analisis[1]
        fecha_str = f"{año}.{dia_juliano}"
        
        # Buscar archivos NPZ para la fecha
        patron_npz = re.compile(rf'^calculos_(HNE|HNN|HNZ)\.{re.escape(fecha_str)}\.npz$')
        archivos_npz = []
        
        for nombre_archivo in os.listdir(ruta_base):
            if patron_npz.match(nombre_archivo):
                ruta_completa = os.path.join(ruta_base, nombre_archivo)
                archivos_npz.append(ruta_completa)
        
        # Verificar si hay archivos NPZ
        if not archivos_npz:
            mostrar_mensaje("Error", f"No se encontraron archivos NPZ para la fecha {fecha_str}", "error")
            return None
        
        # Procesar cada componente por separado
        archivos_temporales = []
        
        for archivo_npz in archivos_npz:
            # Extraer componente del nombre del archivo
            match = re.search(r'calculos_(HNE|HNN|HNZ)', os.path.basename(archivo_npz))
            if not match:
                continue
                
            componente = match.group(1)
            
            # Cargar datos desde NPZ
            datos_cache = np.load(archivo_npz)
            
            # Verificar que exista el array de tiempo
            if 'tiempo' not in datos_cache:
                continue
                
            tiempo = datos_cache['tiempo']
            
            # Seleccionar datos según tipo de dato
            if tipo_espanol == 'aceleracion':
                if unidadg:
                    datos = datos_cache['acc_g'] if 'acc_g' in datos_cache else None
                    unidad = 'g'
                else:
                    datos = datos_cache['acc_mps2'] if 'acc_mps2' in datos_cache else None
                    unidad = 'm/s2'
            elif tipo_espanol == 'velocidad':
                datos = datos_cache['vel'] if 'vel' in datos_cache else None
                unidad = 'm/s'
            elif tipo_espanol == 'desplazamiento':
                datos = datos_cache['desp'] if 'desp' in datos_cache else None
                unidad = 'm'
            
            if datos is None:
                continue
            
            # Filtrar datos por intervalo de tiempo seleccionado
            idx = np.where((tiempo >= tmin_sec) & (tiempo <= tmax_sec))[0]
            
            if len(idx) == 0:
                continue
                
            tiempo_filtrado = tiempo[idx]
            datos_filtrados = datos[idx]
            
            # Crear DataFrame para este componente
            df = pd.DataFrame({
                'time(s)': tiempo_filtrado,
                f'{tipo_espanol}({unidad})': datos_filtrados
            })
            
            # Generar nombre del archivo temporal
            nombre_archivo = f"{tipo_espanol}_{componente}_{año}_{dia_juliano}_{hora_analisis[0].replace(':','-')}_{hora_analisis[1].replace(':','-')}.csv"
            ruta_temporal = os.path.join(ruta_base, nombre_archivo)
            
            # Guardar CSV temporal
            df.to_csv(ruta_temporal, index=False)
            archivos_temporales.append(ruta_temporal)
        
        # Verificar si se generaron archivos
        if not archivos_temporales:
            mostrar_mensaje("Error", "No se generaron archivos CSV para ningún componente", "error")
            return None

        # Abrir diálogo para seleccionar carpeta destino
        carpeta_destino = QFileDialog.getExistingDirectory(
            None,
            "Seleccionar carpeta para guardar los archivos CSV",
            os.path.expanduser("~"),
            QFileDialog.ShowDirsOnly
        )
        
        # Verificar si se seleccionó una carpeta
        if not carpeta_destino:
            # Eliminar archivos temporales si el usuario cancela
            for archivo in archivos_temporales:
                if os.path.exists(archivo):
                    os.remove(archivo)
            return None
        
        # Mover archivos a la carpeta seleccionada
        archivos_movidos = []
        for ruta_temporal in archivos_temporales:
            nombre_archivo = os.path.basename(ruta_temporal)
            ruta_destino = os.path.join(carpeta_destino, nombre_archivo)
            
            try:
                # Mover el archivo
                shutil.move(ruta_temporal, ruta_destino)
                archivos_movidos.append(ruta_destino)
            except Exception as e:
                print(f"Error moviendo archivo: {e}")
        
        # Verificar si se movieron los archivos
        if not archivos_movidos:
            mostrar_mensaje("Error", "No se pudieron mover los archivos CSV a la carpeta seleccionada", "error")
            return None
        
        # Mensaje de éxito
        nombres_archivos = "\n".join([os.path.basename(r) for r in archivos_movidos])
        mensaje_exito = (
            f"Se generaron y guardaron {len(archivos_movidos)} archivos CSV:\n"
            f"{nombres_archivos}\n\n"
            f"Ubicación: {carpeta_destino}"
        )
        mostrar_mensaje("Éxito", mensaje_exito, "info")
        
        return archivos_movidos
        
    except Exception as e:
        mostrar_mensaje("Error", f"Error al generar CSV: {str(e)}", "error")
        return None
    
def mostrarDialogoFiltroFechas(widget_grafico, id_seleccionado, idproyecto, nombre_acelerografo):
    # Crear el diálogo usando QGridLayout para mejor organización
    dialog = QDialog()
    dialog.setWindowTitle("Filtro de Fechas")
    dialog.resize(350, 250)
    
    # Crear el layout principal usando grid
    grid = QGridLayout()
    grid.setSpacing(10)
    grid.setContentsMargins(15, 15, 15, 15)  # Márgenes uniformes
    
    # Añadir controles con etiquetas
    date_label = QLabel("Fecha:")
    grid.addWidget(date_label, 0, 0)
    
    date_edit = QDateEdit()
    date_edit.setDate(QDate.currentDate())
    date_edit.setCalendarPopup(True)
    grid.addWidget(date_edit, 0, 1, 1, 2)
    
    start_time_label = QLabel("Hora de Inicio:")
    grid.addWidget(start_time_label, 1, 0)
    
    start_time_edit = QTimeEdit()
    start_time_edit.setDisplayFormat("hh:mm:ss")
    start_time_edit.setTime(QTime(0, 0, 0))
    grid.addWidget(start_time_edit, 1, 1, 1, 2)
    
    end_time_label = QLabel("Hora de Fin:")
    grid.addWidget(end_time_label, 2, 0)
    
    end_time_edit = QTimeEdit()
    end_time_edit.setDisplayFormat("hh:mm:ss")
    end_time_edit.setTime(QTime(23, 59, 59))
    grid.addWidget(end_time_edit, 2, 1, 1, 2)
    
    # Botones
    apply_button = QPushButton("Aplicar")
    cancel_button = QPushButton("Cancelar")
    grid.addWidget(apply_button, 3, 1)
    grid.addWidget(cancel_button, 3, 2)
    
    def on_apply_button_clicked():
        # Obtener la fecha
        fecha = date_edit.date()
        año = fecha.year()
        dia_del_anio = fecha.dayOfYear()  # Día del año (1-365/366)
        
        # Obtener las horas
        hora_inicio = start_time_edit.time().toString("hh:mm:ss")
        hora_fin = end_time_edit.time().toString("hh:mm:ss")
        
        # Llamar a la función para procesar y mostrar gráficos
        procesar_graficos_acelerografos(
            widget_grafico,
            "AAC",  # tipo aceleración
            idproyecto,
            id_seleccionado,
            nombre_acelerografo,
            False,  # unidadg
            "",     # fechita
            fecha_analisis=(año, dia_del_anio),
            tiempo_minimo=hora_inicio,
            tiempo_maximo=hora_fin
        )
        dialog.accept()
    
    def on_cancel_button_clicked():
        dialog.reject()
    
    # Conectar los botones
    apply_button.clicked.connect(on_apply_button_clicked)
    cancel_button.clicked.connect(on_cancel_button_clicked)
    
    # Establecer el layout en el diálogo
    dialog.setLayout(grid)
    
    # Mostrar el diálogo
    dialog.exec()