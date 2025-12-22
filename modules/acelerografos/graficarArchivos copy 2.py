import numpy as np
import os
import re
import time
import pandas as pd
import h5py
import shutil
import concurrent.futures
import matplotlib.pyplot as plt
from obspy import read, read_inventory, UTCDateTime
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QDateEdit, QTimeEdit, QPushButton, QLabel, QGridLayout, QWidget, 
                              QHBoxLayout, QSpacerItem, QSizePolicy, QFileDialog)
from obspy.core.inventory import Inventory, Network, Station, Channel, Site, Response, InstrumentSensitivity
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from utils.common.rutasarchivos import resource_path
from utils.common.alertas import mostrar_mensaje
from PySide6.QtCore import QDate, QTime
from scipy.integrate import cumulative_trapezoid
from matplotlib.ticker import FuncFormatter
from controllers.ConfiguracionController import ConfiguracionController

# Componentes para procesamiento
COMPONENTES = {
    "HNE": {"color": "red", "label": "Este", "order": 0},
    "HNN": {"color": "blue", "label": "Norte", "order": 1},
    "HNZ": {"color": "green", "label": "Vertical", "order": 2}
}

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

def procesar_graficos_acelerografos(widget_grafico, tipo, proyecto_id, id_acelerografo, nombre_acelerografo, unidadg, fechita, fecha_analisis=None, tiempo_minimo=None, tiempo_maximo=None):
    try:
        hora_analisis = (tiempo_minimo, tiempo_maximo)
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
        nombre_XML = os.path.splitext(os.path.basename(archivo_xml))[0]
        try:
            inv = read_inventory(archivo_xml)
        except Exception as e:
            mostrar_mensaje("Error", f"Error al cargar XML: {str(e)}", "error")
            return
        
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
        archivos_a_procesar = archivos_por_fecha[fecha_seleccionada][-3:]
        
        # Procesar componentes usando rutas completas
        hdf5_paths = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(procesar_componente, archivo, inv, ruta_base): archivo for archivo in archivos_a_procesar}
            for future in concurrent.futures.as_completed(futures):
                archivo = futures[future]
                try:
                    result = future.result()
                    if result:
                        hdf5_paths.append(result)
                except Exception as e:
                    print(f"Error de procesamiento de {archivo}: {e}")
        
        # Recopilar metadatos
        metadatos = {}
        for archivo in archivos_a_procesar:
            nombre_archivo = os.path.basename(archivo)
            hdf5_path = obtener_nombre_h5(nombre_archivo, ruta_base)
            
            if os.path.exists(hdf5_path):
                try:
                    with h5py.File(hdf5_path, "r") as hdf:
                        metadatos[archivo] = {
                            "sampling_rate": hdf.attrs["sampling_rate"],
                            "start_time": UTCDateTime(hdf.attrs["start_time"]),
                            "npts": hdf.attrs["npts"],
                            "component": hdf.attrs["component"]
                        }
                except Exception as e:
                    print(f"Error leyendo metadatos para {archivo}: {str(e)}")
        
        if not metadatos:
            mostrar_mensaje("Error", "No se encontraron datos procesados.", "error")
            return
        
        # Determinar tiempo de inicio común
        start_time_comun = max(meta["start_time"] for meta in metadatos.values())
        sr_comun = next(iter(metadatos.values()))["sampling_rate"]
        
        # Calcular duración común disponible
        duracion_comun = min(
            meta["npts"] / meta["sampling_rate"] 
            for meta in metadatos.values()
        )
        
        # Manejar segmento de tiempo
        inicio_seg_ajustado = 0
        fin_seg_ajustado = duracion_comun
        segundos_desde_medianoche = start_time_comun.hour * 3600 + start_time_comun.minute * 60 + start_time_comun.second
        
        # Si no se especificó tiempo, usar la última hora disponible
        if tiempo_minimo is None or tiempo_maximo is None:
            common_end_time = min(
                meta["start_time"] + meta["npts"] / meta["sampling_rate"]
                for meta in metadatos.values()
            )
            common_end_seconds = common_end_time.hour * 3600 + common_end_time.minute * 60 + common_end_time.second
            start_seconds = max(0, common_end_seconds - 3600)
            
            tiempo_minimo = f"{int(start_seconds/3600):02d}:{int((start_seconds%3600)/60):02d}:{int(start_seconds%60):02d}"
            tiempo_maximo = f"{int(common_end_seconds/3600):02d}:{int((common_end_seconds%3600)/60):02d}:{int(common_end_seconds%60):02d}"
            hora_analisis = (tiempo_minimo, tiempo_maximo)
        
        # Convertir tiempos a segundos
        def hora_a_segundos(hora_str):
            h, m, s = map(float, hora_str.split(':'))
            return h*3600 + m*60 + s
        
        inicio_seg = hora_a_segundos(tiempo_minimo)
        fin_seg = hora_a_segundos(tiempo_maximo)
        inicio_seg_ajustado = max(inicio_seg, segundos_desde_medianoche)
        fin_seg_ajustado = min(fin_seg, segundos_desde_medianoche + duracion_comun)
        
        if inicio_seg_ajustado >= fin_seg_ajustado:
            mostrar_mensaje("Error", "Segmento de tiempo fuera de rango disponible.", "error")
            return
        
        # Calcular muestras para el segmento
        offset_segundos = inicio_seg_ajustado - segundos_desde_medianoche
        inicio_muestra = int(offset_segundos * sr_comun)
        n_muestras = int((fin_seg_ajustado - inicio_seg_ajustado) * sr_comun)
        fin_muestra = inicio_muestra + n_muestras
        
        # Crear vector de tiempos
        tiempos = np.linspace(
            inicio_seg_ajustado,
            inicio_seg_ajustado + n_muestras/sr_comun,
            n_muestras,
            endpoint=False,
            dtype=np.float64
        )
        
        # Generar gráficos para el tipo solicitado
        tipos = {
            "AAC": ("Aceleración", "m/s²", "aceleraciones"),
            "AVE": ("Velocidad", "m/s", "velocidades"),
            "ADE": ("Desplazamiento", "m", "desplazamientos")
        }
        
        if tipo not in tipos:
            mostrar_mensaje("Error", f"Tipo de gráfico no válido: {tipo}", "error")
            return
            
        nombre, unidad, archivo_nombre = tipos[tipo]
        datos_componentes = {}
        
        for archivo in archivos_a_procesar:
            nombre_archivo = os.path.basename(archivo)
            hdf5_path = obtener_nombre_h5(nombre_archivo, ruta_base)
            
            datos, sr, start_time, comp_name = cargar_segmento_hdf5(
                hdf5_path, tipo, inicio_muestra, fin_muestra
            )
            
            if datos is None:
                continue
            
            # Conversión a g si es necesario
            unidad_actual = unidad
            if tipo == "AAC" and unidadg:
                datos = datos / 9.80665
                unidad_actual = "g"
                
            datos_componentes[comp_name] = {
                "data": datos,
                "unidad": unidad_actual
            }
        
        if not datos_componentes:
            mostrar_mensaje("Advertencia", "No hay datos disponibles para generar el gráfico.", "advertencia")
            return
        
        # Ajustar limites de gráficas eje y
        ejeymin, ejeymax, ejeyprin, ejeysecu, intervalox = 0, 0, 0, 0, 0
        dataeje = ConfiguracionController.ctrlObtenerConfiguracionEje(proyecto_id, "ACELEROGRAFOS", tipo)
        if dataeje:
            ejeymin, ejeymax, ejeyprin, ejeysecu, intervalox = dataeje[4], dataeje[5], dataeje[6], dataeje[7], dataeje[8]
        
        fig = generar_grafico(
            nombre, 
            unidad_actual, 
            tiempos, 
            datos_componentes, 
            nombre_acelerografo, fechita,
            hora_analisis, ejeymin, ejeymax, ejeyprin, ejeysecu, intervalox
        )
        
        if fig is None:
            mostrar_mensaje("Advertencia", "No se pudo generar la figura.", "advertencia")
        else:
            mostrar_grafico_en_widget(widget_grafico, fig)
            
    except Exception as e:
        mostrar_mensaje("Error", f"Error de procesamiento: {str(e)}", "error")

def obtener_nombre_h5(archivo_datos, ruta_base):
    """Construye la ruta completa del archivo HDF5"""
    return os.path.join(ruta_base, f"{archivo_datos}.h5")

def cargar_segmento_hdf5(hdf5_path, tipo, inicio_muestra, fin_muestra):
    if not os.path.exists(hdf5_path):
        return None, None, None, None
        
    try:
        with h5py.File(hdf5_path, "r") as hdf:
            if tipo not in hdf:
                return None, None, None, None
                
            dataset = hdf[tipo]
            # Verificar rango de muestras
            n_muestras_total = dataset.shape[0]
            if inicio_muestra < 0 or fin_muestra > n_muestras_total:
                inicio_muestra = max(0, inicio_muestra)
                fin_muestra = min(n_muestras_total, fin_muestra)
                
            if inicio_muestra >= fin_muestra:
                return None, None, None, None
                
            segmento = dataset[inicio_muestra:fin_muestra]
            sr = hdf.attrs["sampling_rate"]
            start_time = UTCDateTime(hdf.attrs["start_time"])
            comp = hdf.attrs["component"]
            
            return np.array(segmento, dtype=np.float64), sr, start_time, comp
            
    except Exception as e:
        return None, None, None, None

def procesar_componente(ruta_datos, inv, ruta_base):
    """Procesa un componente usando ruta completa del archivo"""
    # Extraer solo el nombre del archivo para determinar el componente
    nombre_archivo = os.path.basename(ruta_datos)
    comp = next((c for c in COMPONENTES if f".{c}." in nombre_archivo), None)
    
    if not comp:
        return None
        
    # Construir ruta HDF5 usando el mismo directorio base
    hdf5_path = obtener_nombre_h5(nombre_archivo, ruta_base)
    
    # Verificar si ya está procesado (y es válido)
    if os.path.exists(hdf5_path):
        try:
            with h5py.File(hdf5_path, "r") as hdf:
                # Verificar que tenga todos los datasets necesarios
                if "AAC" in hdf and "AVE" in hdf and "ADE" in hdf:
                    # Verificar que tenga atributos necesarios
                    required_attrs = ["sampling_rate", "start_time", "component", "npts"]
                    if all(attr in hdf.attrs for attr in required_attrs):
                        return hdf5_path
        except Exception as e:
            print(f" Error al abrir HDF5: {e}, reprocesando...")
    
    if not os.path.exists(ruta_datos):
        return None
        
    start_time = time.time()
    
    try:
        # Cargar datos
        st = read(ruta_datos, dtype=np.float64)
        if not st:
            return None
            
        tr = st[0]
        sr = tr.stats.sampling_rate
        npts = tr.stats.npts
        dt = 1.0 / sr
        
        # Vector de tiempo completo
        t = np.arange(0, npts) * dt
        
        # Selección de respuesta
        tiempo_medio = tr.stats.starttime + npts / sr / 2
        inv_especifico = inv.select(
            network=tr.stats.network,
            station=tr.stats.station,
            location=tr.stats.location,
            channel=tr.stats.channel,
            time=tiempo_medio
        )
        
        if not inv_especifico.networks:
            return None
            
        # Filtro anti-alias
        nyq = sr / 2.0
        pre_filt = (0.01, 0.02, nyq * 0.9, nyq)
        
        # Procesamiento
        tr_acc = tr.copy()
        tr_acc.remove_response(inventory=inv_especifico, output="ACC", pre_filt=pre_filt)
        acc_data = tr_acc.data.astype(np.float64)
        
        # Integración
        vel_data = cumulative_trapezoid(acc_data, dx=dt, initial=0)
        disp_data = cumulative_trapezoid(vel_data, dx=dt, initial=0)
        
        # Validación de longitud
        if not (len(acc_data) == len(vel_data) == len(disp_data) == npts):
            return None
            
        # Guardar HDF5
        chunk_size = min(60000, npts)
        with h5py.File(hdf5_path, "w") as hdf:
            hdf.attrs["sampling_rate"] = sr
            hdf.attrs["start_time"] = str(tr.stats.starttime)
            hdf.attrs["component"] = comp
            hdf.attrs["npts"] = npts
            
            hdf.create_dataset("AAC", data=acc_data, dtype=np.float64,
                              chunks=(chunk_size,), compression="gzip")
            hdf.create_dataset("AVE", data=vel_data, dtype=np.float64,
                              chunks=(chunk_size,), compression="gzip")
            hdf.create_dataset("ADE", data=disp_data, dtype=np.float64,
                              chunks=(chunk_size,), compression="gzip")
                              
        return hdf5_path
        
    except Exception as e:
        print(f"Error procesando componente: {str(e)}")
        return None

def generar_grafico(nombre, unidad, tiempos, datos, estacion, fechita, hora_analisis, ejeymin, ejeymax, ejeyprin, ejeysecu, intervalox):
    # Filtrar componentes con datos
    componentes_con_datos = []
    for comp in COMPONENTES:
        comp_data = datos.get(comp)
        if comp_data and len(comp_data["data"]) > 0:
            componentes_con_datos.append(comp)
    
    if not componentes_con_datos:
        return None
        
    # Ordenar componentes
    componentes_con_datos = sorted(componentes_con_datos, key=lambda x: COMPONENTES[x]["order"])
    n_componentes = len(componentes_con_datos)
    fig, axs = plt.subplots(n_componentes, 1, figsize=(15, 4 * n_componentes), sharex=True)
    
    if n_componentes == 1:
        axs = [axs]
    
    # Configurar título principal
    titulo = f"{estacion}: "
    if hora_analisis[0] and hora_analisis[1]:
        titulo += f"{fechita} ({hora_analisis[0]} - {hora_analisis[1]})"
    
    fig.suptitle(titulo, fontsize=14, y=0.99)
    plt.subplots_adjust(top=0.9, bottom=0.1, left=0.1, right=0.95, hspace=0.7)
    
    # Determinar escala adecuada para eje Y
    max_global = max(np.max(np.abs(datos[comp]["data"])) for comp in componentes_con_datos)
    escala = 1.0
    unidad_escalada = unidad
    
    if max_global > 1e6:
        escala = 1e6
        unidad_escalada = f"10^6 {unidad}"
    elif max_global > 1e3:
        escala = 1e3
        unidad_escalada = f"10^3 {unidad}"
    
    # Crear gráficos para cada componente
    for i, comp in enumerate(componentes_con_datos):
        conf = COMPONENTES[comp]
        y = datos[comp]["data"] / escala
        
        # Trazar la señal
        axs[i].plot(tiempos, y, color=conf["color"], linewidth=1.2, 
                   label=f"{conf['label']} ({comp})")
        
        # Encontrar y marcar el valor pico
        idx_pico = np.argmax(np.abs(y))
        valor_pico = y[idx_pico] * escala
        tiempo_pico = tiempos[idx_pico]
        y_pico = y[idx_pico]
        
        # Marcar línea vertical en el pico
        axs[i].axvline(x=tiempo_pico, color=conf["color"], 
                      linestyle=':', alpha=0.8, linewidth=1.2)
        
        # Marcar punto del pico
        axs[i].plot(tiempo_pico, y_pico, 'o', 
                   color=conf["color"], 
                   markersize=8,
                   markeredgecolor='white',
                   markeredgewidth=1.5,
                   zorder=1)
        
        # Formatear información del pico
        fmt_valor = f"{valor_pico:.6f}"
        info = f"Pico: {fmt_valor} {unidad} @ {tiempo_pico:.6f}s"
        
        # Agregar anotación
        axs[i].text(0.99, 0.97, info, transform=axs[i].transAxes,
                    fontsize=9, color=conf["color"], ha='right', va='top',
                    bbox=dict(facecolor='white', alpha=0.85, edgecolor='lightgray', boxstyle='round, pad=0.3'))
        
        # Configurar título y etiquetas
        axs[i].set_title(f"Componente {conf['label']}", fontsize=10, pad=8)
        axs[i].set_ylabel(f"{nombre} ({unidad_escalada})", fontsize=10)
        axs[i].grid(True, linestyle='--', alpha=0.6)
        
        # CONFIGURAR EJE Y
        if ejeymin != 0 or ejeymax != 0:
            axs[i].set_ylim(ejeymin, ejeymax)
            # Calcula los intervalos primarios
            maxejey = (ejeymax) + 0.0001
            if ejeyprin > 0:
                tick_primarios = np.arange(ejeymin, maxejey, ejeyprin)
                axs[i].set_yticks(tick_primarios)
            # Calcula los intervalos secundarios
            if ejeysecu > 0:
                tick_secundarios = np.arange(ejeymin, maxejey, ejeysecu)
                for tick in tick_secundarios:
                    axs[i].axhline(y=tick, color='gray', linestyle='--', linewidth=0.5)
        else:
            current_ylim = axs[i].get_ylim()
            y_range = current_ylim[1] - current_ylim[0]
            axs[i].set_ylim(current_ylim[0], current_ylim[1] + 0.12 * y_range)
        
        # Formatear el eje Y para mostrar hasta 4 decimales
        axs[i].yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:.6f}'))
        
        # Ajustar los límites del eje X
        start, end = tiempos[0], tiempos[-1]
        if intervalox > 0:
            dias_range = np.arange(start, end, intervalox)
            if dias_range[-1] < end:
                dias_range = np.append(dias_range, end)
            axs[i].set_xticks(dias_range)
        
        axs[i].set_xlim(start, end)
    
    # Configurar eje X
    axs[-1].set_xlabel("Tiempo (s)", fontsize=10)
    return fig

def obtener_nombre_csv_desde_hdf5(hdf5_path, hora_analisis):
    base_name = os.path.basename(hdf5_path)
    base_name_no_ext = os.path.splitext(base_name)[0]  # Remover .h5
    dir_name = os.path.dirname(hdf5_path)
    
    if hora_analisis[0] is None or hora_analisis[1] is None:
        return os.path.join(dir_name, f"{base_name_no_ext}_todo_el_dia.csv")
    else:
        # Crear nombres seguros para archivos
        inicio_str = hora_analisis[0].replace(':', '-')
        fin_str = hora_analisis[1].replace(':', '-')
        return os.path.join(dir_name, f"{base_name_no_ext}_{inicio_str}_a_{fin_str}.csv")

def obtener_segmento_indices(starttime_utc, npts, sr, hora_analisis):
    if hora_analisis[0] is None or hora_analisis[1] is None:
        return 0, npts
        
    inicio_hora, fin_hora = hora_analisis
    dia = starttime_utc.date  # Fecha del registro (YYYY-MM-DD)
    
    try:
        # Convertir a tiempos absolutos
        inicio_abs = UTCDateTime(f"{dia}T{inicio_hora}")
        fin_abs = UTCDateTime(f"{dia}T{fin_hora}")
    except Exception as e:
        return 0, 0
    
    # Calcular desplazamiento relativo al inicio del registro
    inicio_rel = inicio_abs - starttime_utc
    fin_rel = fin_abs - starttime_utc
    
    # Convertir a muestras
    inicio_muestra = int(inicio_rel * sr)
    fin_muestra = int(fin_rel * sr)
    
    # Ajustar a los límites del registro
    inicio_muestra = max(0, inicio_muestra)
    fin_muestra = min(npts, fin_muestra)
    
    if inicio_muestra >= fin_muestra:
        return 0, 0
        
    return inicio_muestra, fin_muestra

def generar_csv_desde_hdf5(hdf5_path, hora_analisis, unidadg):
    # Generar nombre del CSV basado en el H5 y las horas
    csv_path = obtener_nombre_csv_desde_hdf5(hdf5_path, hora_analisis)
    
    if not os.path.exists(hdf5_path):
        return
        
    try:
        with h5py.File(hdf5_path, "r") as hdf:
            # Leer atributos
            sr = hdf.attrs["sampling_rate"]
            start_time_utc = UTCDateTime(hdf.attrs["start_time"])
            npts = hdf.attrs["npts"]
            comp = hdf.attrs["component"]
            
            # Obtener segmento
            inicio_muestra, fin_muestra = obtener_segmento_indices(start_time_utc, npts, sr, hora_analisis)
            duracion_muestras = fin_muestra - inicio_muestra
            
            if duracion_muestras <= 0:
                return
                
            # Extraer datos
            acc = hdf["AAC"][inicio_muestra:fin_muestra]
            vel = hdf["AVE"][inicio_muestra:fin_muestra]
            disp = hdf["ADE"][inicio_muestra:fin_muestra]
            
            # Crear vector de tiempo relativo al inicio del segmento
            dt = 1.0 / sr
            t = np.arange(0, len(acc)) * dt
            
            # Guardar CSV
            factor = 1 / 9.80665 if unidadg else 1.0
            unidad = "g" if unidadg else "m/s^2"
            
            df = pd.DataFrame({
                "Time (s)": t,
                f"Acceleration ({unidad})": acc * factor,
                "Velocity (m/s)": vel,
                "Displacement (m)": disp
            })
            
            df.to_csv(csv_path, index=False, float_format="%.8e")
            return csv_path
            
    except Exception as e:
        print(f"Error generando CSV: {str(e)}")

def generar_csvs_para_fecha(proyecto_id, id_acelerografo, fecha_analisis=(2025, 171), hora_analisis=('14:28:00', '15:28:00'), unidadg=False):
    # Construir ruta base usando os.path.join
    ruta_base = os.path.join(
        resource_path('resources'),
        'workspace',
        'ACELEROGRAFOS',
        f'proyecto{proyecto_id}',
        str(id_acelerografo)
    )
    
    año, dia_del_anio = fecha_analisis
    fecha_str = f"{año}.{dia_del_anio:03d}"  # Formato: 2025.171
    
    # Buscar archivos H5 para esta fecha
    patron_h5 = re.compile(rf'^.*\.{re.escape(fecha_str)}\.h5$')
    h5_files = []
    
    for nombre_archivo in os.listdir(ruta_base):
        if patron_h5.match(nombre_archivo):
            h5_path = os.path.join(ruta_base, nombre_archivo)
            h5_files.append(h5_path)
    
    if not h5_files:
        mostrar_mensaje("Error", f"No se encontraron archivos H5 para la fecha {fecha_str}", "error")
        return
    
    # Generar CSV para cada archivo H5 (cada componente)
    for h5_path in h5_files:
        generar_csv_desde_hdf5(h5_path, hora_analisis, unidadg)
    
    # Seleccionar ruta para guardar
    carpeta_destino = QFileDialog.getExistingDirectory(None, "Seleccionar carpeta para guardar CSV")
    
    if carpeta_destino:
        try:
            # Copiar solo archivos CSV desde ruta_base hacia carpeta_destino
            for nombre_archivo in os.listdir(ruta_base):
                if nombre_archivo.lower().endswith(".csv"):
                    origen = os.path.join(ruta_base, nombre_archivo)
                    destino = os.path.join(carpeta_destino, nombre_archivo)
                    shutil.move(origen, destino)
                    
            mostrar_mensaje("Data Exportada", f"Los archivos CSV se han guardado en:\n{carpeta_destino}", "informacion")
        except Exception as e:
            mostrar_mensaje("Error al Exportar", f"No se pudo guardar los archivos CSV: {str(e)}", "advertencia")

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