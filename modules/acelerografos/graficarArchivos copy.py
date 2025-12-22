import numpy as np
import os
import re
import matplotlib.pyplot as plt
from obspy import read, read_inventory
from PySide6.QtWidgets import QDialog, QVBoxLayout, QDateEdit, QTimeEdit, QPushButton, QLabel
from obspy.core.inventory import Inventory, Network, Station, Channel, Site, Response, InstrumentSensitivity
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from utils.common.rutasarchivos import resource_path
from utils.common.alertas import mostrar_mensaje
import matplotlib.gridspec as gridspec
from matplotlib.ticker import FuncFormatter
from PySide6.QtCore import QDate, QTime
from controllers.ConfiguracionController import ConfiguracionController

# Parámetros estándar para redes sismológicas en Perú
PARAMETROS_PERU = {
    "acelerografo": {
        "sensibilidad": 800,  # V/g (típico para Kinemetrics EpiSensor)
        "rango_voltaje": 5.0,  # ±5V
        "bits": 24,
        "ganancia": 1.0,
        "respuesta_plana_min": 0.05,  # Hz
        "respuesta_plana_max": 100.0,  # Hz
        "frecuencia_natural": 200.0,  # Hz
        "amortiguamiento": 0.707
    },
    "coordenadas_lima": {
        "lat": -12.0464,
        "lon": -77.0428,
        "elevacion": 100.0  # m
    },
    "red": "G0",  # Red estándar para estaciones peruanas
    "localizador": "00"
}

# Configuración de componentes
COMPONENTES = {
    "HNE": {"color": "red", "label": "Este", "order": 0},
    "HNN": {"color": "blue", "label": "Norte", "order": 1},
    "HNZ": {"color": "green", "label": "Vertical", "order": 2}
}

TIEMPO_MINIMO = None  # Tiempo mínimo en segundos desde el inicio
TIEMPO_MAXIMO = None  # Tiempo máximo en segundos desde el inicio
ultimo_filtro = {
    "año": None,
    "dia_del_anio": None,
    "segundos_inicio": None,
    "segundos_fin": None
}

def clear_layout(layout):
    while layout.count():
        item = layout.takeAt(0)
        if item.widget():
            item.widget().deleteLater()
        elif item.layout():
            clear_layout(item.layout())

def mostrar_grafico(widget, fig):
    widget.canvas = FigureCanvas(fig)
    widget.toolbar = NavigationToolbar(widget.canvas, widget)
    # Obtener o crear el layout del widget contenedor
    layout = widget.layout()
    if layout is None:
        layout = QVBoxLayout(widget)
        widget.setLayout(layout)
    # Agregar al layout en orden: canvas, luego toolbar
    layout.addWidget(widget.canvas)
    layout.addWidget(widget.toolbar)
    # Dibujar la figura
    widget.canvas.draw()

def crear_inventario_estandar(red, estacion, canales):
    # Crear estructura básica del inventario
    red_obj = Network(code=red)
    estacion_obj = Station(
        code=estacion,
        latitude=PARAMETROS_PERU["coordenadas_lima"]["lat"],
        longitude=PARAMETROS_PERU["coordenadas_lima"]["lon"],
        elevation=PARAMETROS_PERU["coordenadas_lima"]["elevacion"],
        site=Site(name=f"Estación {estacion} (Estándar Perú)")
    )
    
    # Calcular sensibilidad total (V/m/s²)
    sensibilidad_sensor = PARAMETROS_PERU["acelerografo"]["sensibilidad"] / 9.80665
    rango_digitizador = 2 * PARAMETROS_PERU["acelerografo"]["rango_voltaje"]
    max_counts = 2**(PARAMETROS_PERU["acelerografo"]["bits"] - 1)
    sensibilidad_total = sensibilidad_sensor * (max_counts / rango_digitizador)
    
    # Crear canales estándar
    for canal in canales:
        # Configurar orientación según componente
        if canal == "HNZ":
            dip = -90.0  # Vertical
            azimuth = 0.0
        else:
            dip = 0.0
            azimuth = 90.0 if canal == "HNE" else 0.0  # Este=90°, Norte=0°
        
        channel = Channel(
            code=canal,
            location_code=PARAMETROS_PERU["localizador"],
            latitude=PARAMETROS_PERU["coordenadas_lima"]["lat"],
            longitude=PARAMETROS_PERU["coordenadas_lima"]["lon"],
            elevation=PARAMETROS_PERU["coordenadas_lima"]["elevacion"],
            depth=0.0,
            azimuth=azimuth,
            dip=dip,
            sample_rate=200.0  # Hz (asumido)
        )
        
        # Configurar respuesta instrumental estándar
        sens = InstrumentSensitivity(
            value=sensibilidad_total,
            frequency=1.0,
            input_units="M/S**2",
            output_units="COUNTS"
        )
        
        channel.response = Response(instrument_sensitivity=sens)
        estacion_obj.channels.append(channel)
    
    red_obj.stations.append(estacion_obj)
    return Inventory(networks=[red_obj], source="Estándar Perú")

def cargar_inventario(archivo_xml, estacion, canales):
    try:
        if os.path.exists(archivo_xml):
            inv = read_inventory(archivo_xml)
            # Validar que el inventario cargado corresponda a la estación esperada
            for network in inv:
                for station in network:
                    if station.code == estacion:
                        return inv
    except Exception as e:
        print(f"Error al cargar XML: {e}")

    # Crear inventario estándar si falla la carga o no es compatible
    return crear_inventario_estandar(PARAMETROS_PERU["red"], estacion, canales)

def obtener_coordenadas(inv, componente):
    """Obtiene coordenadas desde inventario sin modificar valores (0,0)"""
    try:
        net = inv[0].code
        sta = inv[0][0].code
        loc = inv[0][0][0].location_code
        
        # Construir ID completo para obtener coordenadas
        full_id = f"{net}.{sta}.{loc}.{componente}"
        coords = inv.get_coordinates(full_id)
        return coords["latitude"], coords["longitude"], coords["elevation"]
    except Exception as e:
        return (
            PARAMETROS_PERU["coordenadas_lima"]["lat"],
            PARAMETROS_PERU["coordenadas_lima"]["lon"],
            PARAMETROS_PERU["coordenadas_lima"]["elevacion"]
        )

def procesar_componente(archivo, inv, tiempo_minimo=None, tiempo_maximo=None):
    st = read(archivo)
    tr = st[0]
    componente = tr.stats.channel
    # Chequeo de saturación
    max_abs = np.max(np.abs(tr.data))
    if max_abs > 0.9 * (2**23):  # Límite para 24-bit
        print(f"Posible saturacion: Valor maximo absoluto = {max_abs}")
    # Seleccionar metadatos específicos
    inv_especifico = inv.select(
        network=tr.stats.network,
        station=tr.stats.station,
        location=tr.stats.location,
        channel=componente
    )
    # Recortar tiempo si es necesario
    if tiempo_minimo is not None:
        starttime = tr.stats.starttime + tiempo_minimo
        tr = tr.slice(starttime=starttime)
    if tiempo_maximo is not None:
        endtime = tr.stats.starttime + tiempo_maximo
        tr = tr.slice(endtime=endtime)
    # Configurar filtro anti-alias
    sample_rate = tr.stats.sampling_rate
    nyquist = sample_rate / 2.0
    pre_filt = (0.01, 0.02, 0.9 * nyquist, nyquist)
    # Convertir a aceleración física (optimizado)
    tr_acc = tr.copy()
    try:
        tr_acc.remove_response(
            inventory=inv_especifico,
            output="ACC",
            pre_filt=pre_filt,
            water_level=60  # Nivel adicional para estabilidad
        )
    except Exception as e:
        print(f"Error: {e} - Aplicando conversión manual")
        # Conversión manual usando parámetros estándar
        sensibilidad_sensor = PARAMETROS_PERU["acelerografo"]["sensibilidad"] / 9.80665
        rango_digitizador = 2 * PARAMETROS_PERU["acelerografo"]["rango_voltaje"]
        max_counts = 2**(PARAMETROS_PERU["acelerografo"]["bits"] - 1)
        factor = (rango_digitizador / max_counts) / sensibilidad_sensor
        tr_acc.data = tr_acc.data * factor
    # Calcular velocidad y desplazamiento con método robusto
    tr_vel = tr_acc.copy()
    tr_vel.integrate(method="cumtrapz")  # Integración trapezoidal
    tr_disp = tr_vel.copy()
    tr_disp.integrate(method="cumtrapz")
    return componente, tr_acc, tr_vel, tr_disp

def generar_grafico_profesional(datos, tipo, unidad, lat, lon, elev, nombre_estacion, fuente_metadatos, ejeymin, ejeymax, ejeyprin, ejeysecu, intervalox):
    componentes_disponibles = sorted(
        [comp for comp in COMPONENTES if comp in datos],
        key=lambda x: COMPONENTES[x]["order"]
    )

    n_componentes = len(componentes_disponibles)

    # Crear la figura con GridSpec
    fig = plt.figure(figsize=(14, 4 + 3 * n_componentes))
    gs = gridspec.GridSpec(n_componentes, 1, hspace=0.7)

    titulo_principal = f"{tipo.capitalize()} - Estación {nombre_estacion}"
    fig.suptitle(titulo_principal, fontsize=14, y=0.98)

    axs = []
    for i, comp in enumerate(componentes_disponibles):
        ax = fig.add_subplot(gs[i, 0])
        axs.append(ax)

        tr = datos[comp]
        conf = COMPONENTES[comp]
        t = tr.times()
        y = tr.data

        ax.plot(t, y, color=conf["color"], linewidth=1.2, label=conf["label"])

        idx_pico = np.argmax(np.abs(y))
        valor_pico = y[idx_pico]
        tiempo_pico = t[idx_pico]

        ax.axvline(tiempo_pico, color='gray', linestyle=':', alpha=0.7)
        ax.plot(tiempo_pico, valor_pico, 'o', markersize=6, color=conf["color"], markeredgecolor='black')
        info_pico = f"Máx: {abs(valor_pico):.4f} {unidad} @ {tiempo_pico:.2f}s"
        ax.legend([info_pico], loc='upper right', framealpha=0.9, fontsize=8)
        ax.set_title(f"Componente {conf['label']} ({comp})", fontsize=11, pad=10)
        ax.set_ylabel(f"{unidad}", fontsize=9)
        ax.grid(True, linestyle=':', alpha=0.5)
        ax.tick_params(axis='both', labelsize=8)
        # CONFIGURAR EJE Y
        if ejeymin != 0 or ejeymax != 0:
            ax.set_ylim(ejeymin, ejeymax)
            # Calcula los intervalos primarios
            maxejey = (ejeymax) + 0.0001
            if ejeyprin > 0:
                tick_primarios = np.arange(ejeymin, maxejey, ejeyprin)
                ax.set_yticks(tick_primarios)
            # Calcula los intervalos secundarios
            if ejeysecu > 0:
                tick_secundarios = np.arange(ejeymin, maxejey, ejeysecu)
                for tick in tick_secundarios:
                    ax.axhline(y=tick, color='gray', linestyle='--', linewidth=0.5)
        else:
            ymax = np.max(np.abs(y)) * 1.15
            ax.set_ylim(-ymax, ymax)
        # Formatear el eje Y para mostrar hasta 4 decimales
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:.4f}'))
        # Ajustar los límites del eje X
        start, end = t[0], t[-1]
        if intervalox > 0:
            dias_range = np.arange(start, end, intervalox)
            if dias_range[-1] < end:
                dias_range = np.append(dias_range, end)
            ax.set_xticks(dias_range)
        ax.set_xlim(start, end)
    # Ajustar el último subplot para que tenga el label de x
    axs[-1].set_xlabel("Tiempo (s)", fontsize=9)
    # Ajustar manualmente los márgenes
    plt.subplots_adjust(top=0.9, bottom=0.1, left=0.1, right=0.95, hspace=0.7)
    return fig

def procesar_y_mostrar_graficos(widget_grafico, tipo, proyecto_id, id_acelerografo, año=None, dia_del_anio=None, tiempo_minimo=None, tiempo_maximo=None):
    try:
        ruta_xml = resource_path(f'resources/workspace/ACELEROGRAFOS/proyecto{proyecto_id}/{str(id_acelerografo)}')

        # Patrones para buscar archivos de datos
        patron_archivo = re.compile(r'^.+\.(HN[E|N|Z])\.D?\.\d+\.\d+$')

        # Buscar archivos de datos en la ruta especificada
        archivos_datos = [archivo for archivo in os.listdir(ruta_xml) if patron_archivo.match(archivo)]

        if not archivos_datos:
            raise FileNotFoundError(f"No se encontraron archivos de datos en la ruta {ruta_xml}")

        # Agrupar archivos por fecha
        archivos_por_fecha = {}
        for archivo in archivos_datos:
            # Extraer la fecha del nombre del archivo
            fecha = archivo.split('.')[-1]

            if fecha not in archivos_por_fecha:
                archivos_por_fecha[fecha] = []
            archivos_por_fecha[fecha].append(archivo)

        # Ordenar las fechas de manera descendente para encontrar la más reciente
        fechas_ordenadas = sorted(archivos_por_fecha.keys(), reverse=True)

        if not fechas_ordenadas:
            raise ValueError("No se encontraron fechas en los archivos.")

        # Tomar la fecha más reciente
        fecha_mas_reciente = fechas_ordenadas[0]

        # Tomar los tres últimos archivos de la fecha más reciente
        archivos_a_procesar = archivos_por_fecha[fecha_mas_reciente][-3:]

        # Tomar el archivo XML correspondiente
        archivos_xml = [archivo for archivo in os.listdir(ruta_xml) if archivo.endswith('.xml')]
        archivo_xml = os.path.join(ruta_xml, archivos_xml[0])

        # Determinar nombre de estación
        nombre_estacion = "AC02"

        # Cargar inventario con respaldo
        inv = cargar_inventario(archivo_xml, nombre_estacion, list(COMPONENTES.keys()))

        # Determinar fuente de metadatos
        fuente_metadatos = "XML específico"
        if "Estándar Perú" in inv.source:
            fuente_metadatos = "Estándar Perú"

        # Obtener coordenadas
        lat, lon, elev = obtener_coordenadas(inv, list(COMPONENTES.keys())[0])
        # Actualizar tiempos globales si se proporcionan
        if tiempo_minimo is not None:
            TIEMPO_MINIMO = tiempo_minimo
        if tiempo_maximo is not None:
            TIEMPO_MAXIMO = tiempo_maximo

        # Procesar cada componente
        aceleraciones = {}
        velocidades = {}
        desplazamientos = {}

        for archivo in archivos_a_procesar:
            componente, tr_acc, tr_vel, tr_disp = procesar_componente(
                os.path.join(ruta_xml, archivo),
                inv,
                tiempo_minimo=TIEMPO_MINIMO,
                tiempo_maximo=TIEMPO_MAXIMO
            )
            aceleraciones[componente] = tr_acc
            velocidades[componente] = tr_vel
            desplazamientos[componente] = tr_disp
        # Seleccionar datos según tipo solicitado
        if tipo == "AAC":
            datos = aceleraciones
            tipo_label = "Aceleración"
            unidad = "m/s²"
        elif tipo == "AVE":
            datos = velocidades
            tipo_label = "Velocidad"
            unidad = "m/s"
        else:  # desplazamiento
            datos = desplazamientos
            tipo_label = "Desplazamiento"
            unidad = "m"
        # Ajustar limites de gráficas eje y
        ejeymin, ejeymax, ejeyprin, ejeysecu, intervalo_dias = 0, 0, 0, 0, 0
        dataeje = ConfiguracionController.ctrlObtenerConfiguracionEje(proyecto_id, "ACELEROGRAFOS", tipo)
        if dataeje:
            ejeymin, ejeymax, ejeyprin, ejeysecu, intervalo_dias = dataeje[4], dataeje[5], dataeje[6], dataeje[7], dataeje[8]
        # Generar gráfico profesional
        fig = generar_grafico_profesional(
            datos,
            tipo_label,
            unidad,
            lat,
            lon,
            elev,
            nombre_estacion,
            fuente_metadatos, ejeymin, ejeymax, ejeyprin, ejeysecu, intervalo_dias
        )
        mostrar_grafico(widget_grafico, fig)
        # Mostrar advertencias si es necesario
        if fuente_metadatos == "Estándar Perú":
            mostrar_mensaje("TIPO ESTÁNDAR", f"Se usaron parámetros estándar de Perú para la estación {nombre_estacion} \ndebido a que el archivo XML no es compatible o no corresponde a esta estación.", "advertencia")
    except Exception as e:
        print(f"Error crítico: {e}")

def convertir_hora_a_segundos(time):
    return time.hour() * 3600 + time.minute() * 60 + time.second()

def calcular_dia_del_anio(fecha):
    # Crear una fecha para el primer día del año
    primer_dia = QDate(fecha.year(), 1, 1)
    # Calcular la diferencia en días
    dia_del_anio = fecha.toJulianDay() - primer_dia.toJulianDay() + 1
    return dia_del_anio

def mostrarDialogoFiltroFechas(widget_grafico, id_seleccionado, idproyecto):
    global ultimo_filtro

    # Crear el diálogo
    dialog = QDialog()
    dialog.setWindowTitle("Filtro de Fechas")
    dialog.resize(200, dialog.sizeHint().height())

    # Crear el layout principal
    layout = QVBoxLayout()

    # Añadir un QDateEdit para la fecha
    date_label = QLabel("Fecha:")
    date_edit = QDateEdit()
    layout.addWidget(date_label)
    layout.addWidget(date_edit)

    # Añadir QTimeEdit para la hora de inicio con segundos
    start_time_label = QLabel("Hora de Inicio:")
    start_time_edit = QTimeEdit()
    start_time_edit.setDisplayFormat("hh:mm:ss")
    layout.addWidget(start_time_label)
    layout.addWidget(start_time_edit)

    # Añadir QTimeEdit para la hora de fin con segundos
    end_time_label = QLabel("Hora de Fin:")
    end_time_edit = QTimeEdit()
    end_time_edit.setDisplayFormat("hh:mm:ss")
    layout.addWidget(end_time_label)
    layout.addWidget(end_time_edit)

    # Si hay un último filtro aplicado, cargar los valores
    if all(value is not None for value in ultimo_filtro.values()):
        fecha = QDate(ultimo_filtro["año"], 1, 1).addDays(ultimo_filtro["dia_del_anio"] - 1)
        date_edit.setDate(fecha)

        horas_inicio = ultimo_filtro["segundos_inicio"] // 3600
        minutos_inicio = (ultimo_filtro["segundos_inicio"] % 3600) // 60
        segundos_inicio = ultimo_filtro["segundos_inicio"] % 60
        start_time_edit.setTime(QTime(horas_inicio, minutos_inicio, segundos_inicio))

        horas_fin = ultimo_filtro["segundos_fin"] // 3600
        minutos_fin = (ultimo_filtro["segundos_fin"] % 3600) // 60
        segundos_fin = ultimo_filtro["segundos_fin"] % 60
        end_time_edit.setTime(QTime(horas_fin, minutos_fin, segundos_fin))
    else:
        # Establecer la fecha y hora actual por defecto
        date_edit.setDate(QDate.currentDate())
        start_time_edit.setTime(QTime.currentTime())
        end_time_edit.setTime(QTime.currentTime())

    # Añadir un botón de aplicar
    apply_button = QPushButton("Aplicar")
    layout.addWidget(apply_button)

    def on_apply_button_clicked():
        # Obtener la fecha
        fecha = date_edit.date()
        año = fecha.year()

        # Calcular el día del año
        dia_del_anio = calcular_dia_del_anio(fecha)

        # Obtener las horas y convertirlas a segundos desde las 00:00:00
        hora_inicio = start_time_edit.time()
        segundos_inicio = convertir_hora_a_segundos(hora_inicio)

        hora_fin = end_time_edit.time()
        segundos_fin = convertir_hora_a_segundos(hora_fin)

        # Guardar el último filtro aplicado en las variables globales
        ultimo_filtro.update({
            "año": año,
            "dia_del_anio": dia_del_anio,
            "segundos_inicio": segundos_inicio,
            "segundos_fin": segundos_fin
        })

        # Llamar a la función para procesar y mostrar gráficos
        procesar_y_mostrar_graficos(
            widget_grafico,
            id_seleccionado,
            idproyecto, 2,
            año=año,
            dia_del_anio=dia_del_anio,
            tiempo_minimo=segundos_inicio,
            tiempo_maximo=segundos_fin
        )

        dialog.accept()

    # Conectar el botón a la función
    apply_button.clicked.connect(on_apply_button_clicked)

    # Establecer el layout en el diálogo
    dialog.setLayout(layout)

    # Mostrar el diálogo
    dialog.exec()