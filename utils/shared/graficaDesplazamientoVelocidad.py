import gc
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches as mpatches
import matplotlib.dates as mdates
from datetime import datetime
from PySide6.QtGui import Qt
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QDialog, QWidget, QCheckBox, QSizePolicy
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from utils.common.customToolbar import CustomToolbar 
from matplotlib.dates import DateFormatter
from utils.common.alertas import mostrar_mensaje
from utils.shared.calculostendencias import CalculosTendencias
from controllers.ConfiguracionController import ConfiguracionController
from modules.empresa.softwareconfiguracion import SoftwareConfiguracion
from controllers.PrismaController import PrismaController
from controllers.PiezometroController import PiezometroController
from controllers.CeldaController import CeldaController
from controllers.EventosController import EventosController
from views.EventosDialog import EventosDialog

# ============================================================
# CONFIGURACIÓN GLOBAL DE SUAVIZADO
# False = líneas rectas (comportamiento original)
# True  = curvas suavizadas tipo Excel/ECharts
# ============================================================
SUAVIZADO_TENSION = 0.2  # 0.0=recto, 0.5=máximo suavizado


def suavizar_con_bezier(x_num, y_num, tension=0.2):
    """
    Suaviza una línea usando curvas de Bézier cúbicas.

    GARANTÍAS PARA DATOS DE SENSORES:
    - La curva pasa EXACTAMENTE por todos los puntos originales
    - No se inventan lecturas intermedias
    - Solo se suavizan las esquinas (igual que Excel y ECharts)
    - El hover sigue usando los datos reales originales

    Parámetros:
    -----------
    x_num    : np.array de float (fechas ya convertidas a número matplotlib,
                o días/horas según el modo)
    y_num    : np.array de float (lecturas reales del sensor)
    tension  : float 0.0-0.5
                0.0 = sin suavizado (línea recta)
                0.2 = suavizado moderado (recomendado sensores)
                0.5 = máximo (igual que ECharts default)

    Retorna:
    --------
    (x_bezier, y_bezier) : arrays listos para ax.plot()
                           SOLO para la representación visual.
    """
    x = np.asarray(x_num, dtype=float)
    y = np.asarray(y_num, dtype=float)

    # --- Limpieza robusta ---
    mask = np.isfinite(x) & np.isfinite(y)
    x = x[mask]
    y = y[mask]
    n = len(x)

    # Mínimo 3 puntos para suavizar (con 2 es una recta de todas formas)
    if n < 3:
        return x, y

    PASOS = 30  # Puntos por segmento bézier
    x_out = []
    y_out = []

    for i in range(n - 1):
        x0, y0 = x[i],   y[i]       # Punto real inicio
        x3, y3 = x[i+1], y[i+1]     # Punto real fin

        # Punto de control 1 (salida desde x0,y0)
        # Usa el punto anterior para calcular la tangente
        if i == 0:
            cp1x = x0 + (x3 - x0) * tension
            cp1y = y0 + (y3 - y0) * tension
        else:
            x_prev, y_prev = x[i-1], y[i-1]
            cp1x = x0 + (x3 - x_prev) * tension
            cp1y = y0 + (y3 - y_prev) * tension

        # Punto de control 2 (entrada hacia x3,y3)
        # Usa el punto siguiente para calcular la tangente
        if i == n - 2:
            cp2x = x3 - (x3 - x0) * tension
            cp2y = y3 - (y3 - y0) * tension
        else:
            x_next, y_next = x[i+2], y[i+2]
            cp2x = x3 - (x_next - x0) * tension
            cp2y = y3 - (y_next - y0) * tension

        # Curva Bézier cúbica paramétrica
        # endpoint=True solo en el último segmento para no duplicar puntos
        es_ultimo = (i == n - 2)
        t = np.linspace(0, 1, PASOS, endpoint=es_ultimo)

        bx = ((1-t)**3 * x0 +
              3*(1-t)**2 * t * cp1x +
              3*(1-t)    * t**2 * cp2x +
              t**3 * x3)

        by = ((1-t)**3 * y0 +
              3*(1-t)**2 * t * cp1y +
              3*(1-t)    * t**2 * cp2y +
              t**3 * y3)

        x_out.append(bx)
        y_out.append(by)

    return np.concatenate(x_out), np.concatenate(y_out)


def _x_a_numerico(x_data, tiempo):
    """
    Convierte x_data al formato float que necesita suavizar_con_bezier.
    Para tiempo=FECHA convierte fechas a número matplotlib.
    Para otros modos simplemente castea a float.
    """
    x_arr = np.asarray(x_data)
    if tiempo == "FECHA":
        try:
            if hasattr(x_arr, 'dtype'):
                if np.issubdtype(x_arr.dtype, np.datetime64) or x_arr.dtype == object:
                    return mdates.date2num(x_arr)
            return x_arr.astype(float)
        except Exception:
            return x_arr.astype(float)
    else:
        return x_arr.astype(float)

def plot_linea_suavizada(ax, x_data, y_data, tiempo, activo=False, **kwargs):
    marker = kwargs.pop('marker', None)
    markersize = kwargs.pop('markersize', 6)
    estilo_linea = kwargs.get('linestyle', '-')
    
    # Esta lista guardará los objetos visuales (curva y puntos)
    objetos_vinculados = []

    if not activo:
        if marker:
            kwargs['marker'] = marker
            kwargs['markersize'] = markersize
        linea, = ax.plot(x_data, y_data, **kwargs)
        linea._estilo_puro = estilo_linea
        linea._asociados = [] # No tiene capas extra
        return linea

    # ---- Modo suavizado ----
    x_num = _x_a_numerico(x_data, tiempo)
    y_num = np.asarray(y_data, dtype=float)
    x_s, y_s = suavizar_con_bezier(x_num, y_num, SUAVIZADO_TENSION)

    label = kwargs.pop('label', '_nolegend_')

    # --- CAPA 1: Curva visual ---
    kwargs_visual = kwargs.copy()
    kwargs_visual['label'] = '_nolegend_'
    linea_visual, = ax.plot(x_s, y_s, **kwargs_visual)
    color_final = linea_visual.get_color()
    objetos_vinculados.append(linea_visual) # <--- AGREGADO

    # --- CAPA 2: Marcadores ---
    if marker:
        puntos, = ax.plot(x_data, y_data, marker=marker, markersize=markersize,
                linestyle='none', color=color_final, zorder=linea_visual.get_zorder() + 1,
                label='_nolegend_')
        objetos_vinculados.append(puntos) # <--- AGREGADO

    # --- CAPA 3: Línea fantasma (La que va a la LEYENDA) ---
    linea_real, = ax.plot(
        x_data, y_data,
        linestyle='none', marker='none',
        color=color_final, label=label,
        alpha=0, zorder=0
    )

    linea_real._estilo_puro = estilo_linea
    # GUARDAMOS LOS HIJOS: Esto permite que al tocar la leyenda, 
    # la línea real sepa qué otros objetos ocultar
    linea_real._asociados = objetos_vinculados 

    return linea_real

def configurar_evento_leyenda(canvas, legend, handles):
    """
    Configura la interacción con la leyenda con alta precisión.
    """
    map_leyenda_a_grafico = {}
    
    # Obtenemos las líneas de la leyenda
    lineas_leyenda = legend.get_lines()
    
    for leg_line, orig_line in zip(lineas_leyenda, handles):
        # 1. Bajamos el pickradius a 5 para evitar solapamientos
        # Si ves que aún se marcan dos, bájalo a 3 o 4.
        leg_line.set_picker(3) 
        map_leyenda_a_grafico[leg_line] = orig_line

    def on_pick(event):
        # El evento 'pick_event' a veces detecta varios artistas si están muy cerca.
        # Matplotlib procesa todos los que estén bajo el mouse.
        
        leg_line = event.artist
        
        # Verificamos que el artista clickeado sea uno de nuestros iconos de leyenda
        if leg_line not in map_leyenda_a_grafico:
            return

        orig_line = map_leyenda_a_grafico[leg_line]
        
        # Cambiamos visibilidad
        nuevo_estado = not orig_line.get_visible()
        
        # Aplicar a la línea principal (la de la leyenda)
        orig_line.set_visible(nuevo_estado)
        
        # Aplicar a sus capas asociadas (suavizado, puntos, etc.)
        if hasattr(orig_line, '_asociados'):
            for obj in orig_line._asociados:
                obj.set_visible(nuevo_estado)
        
        # Feedback visual en la leyenda
        # Usamos alpha 1.0 para activo y 0.15 para inactivo (más tenue)
        leg_line.set_alpha(1.0 if nuevo_estado else 0.15)
        
        # Opcional: También podemos atenuar el texto de la leyenda
        # Buscamos el texto que corresponde a esta línea
        try:
            # En la leyenda, los textos suelen estar en la misma posición de índice
            idx = lineas_leyenda.index(leg_line)
            legend.get_texts()[idx].set_alpha(1.0 if nuevo_estado else 0.3)
        except:
            pass

        canvas.draw_idle()

    # IMPORTANTE: Antes de conectar, desconectamos eventos pick previos 
    # para evitar que se acumulen al redimensionar la ventana
    if hasattr(canvas, '_leyenda_gid'):
        canvas.mpl_disconnect(canvas._leyenda_gid)
    
    canvas._leyenda_gid = canvas.mpl_connect('pick_event', on_pick)
class ModalDialog(QDialog):
    def __init__(self, parent, label, date, reading):  # Añadir parent
        super().__init__(parent, Qt.Window)  # Usar Qt.Window
        self.setWindowTitle("Omitir Lectura")
        self.resize(300, 150)

        layout = QVBoxLayout()

        # Añadir etiquetas con la información
        self.label_info = QLabel(f"Equipo: {label}")
        self.date_info = QLabel(f"Fecha: {date}")
        self.reading_info = QLabel(f"Lectura: {reading}")

        layout.addWidget(self.label_info)
        layout.addWidget(self.date_info)
        layout.addWidget(self.reading_info)

        # Añadir botones
        button_layout = QHBoxLayout()
        self.accept_button = QPushButton("Aceptar")
        self.cancel_button = QPushButton("Cancelar")

        button_layout.addWidget(self.accept_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Conectar botones a sus respectivas funciones
        self.accept_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

def limpiar_widget(widget):
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

    # 1. Cierre síncrono de figuras de Matplotlib (Crucial para estabilidad)
    for child in widget.findChildren(FigureCanvas):
        try:
            if hasattr(child, 'figure'):
                plt.close(child.figure) # Cerramos la figura
                child.figure.clear()    # Limpiamos ejes
        except Exception:
            pass

    # 2. Limpieza de Layouts y Sub-Layouts
    if widget.layout() is None:
        layout = QVBoxLayout(widget)
        widget.setLayout(layout)
    else:
        layout = widget.layout()
        while layout.count():
            item = layout.takeAt(0)
            widget_to_remove = item.widget()
            if widget_to_remove is not None:
                widget_to_remove.hide() # Ocultar antes de borrar evita crashes visuales
                widget_to_remove.deleteLater()
            else:
                sub_layout = item.layout()
                if sub_layout is not None:
                    while sub_layout.count():
                        sub_item = sub_layout.takeAt(0)
                        sub_widget = sub_item.widget()
                        if sub_widget is not None:
                            sub_widget.hide()
                            sub_widget.deleteLater()

    # 3. Limpieza de atributos dinámicos (Toolbar, Botones de navegación)
    # He unificado esto para que no haya errores de RuntimeError
    for attr in ["toolbar", "toolbar_container", "boton_siguiente", "boton_anterior"]:
        if hasattr(widget, attr):
            obj = getattr(widget, attr)
            if obj is not None:
                try:
                    if hasattr(obj, 'hide'): obj.hide()
                    obj.deleteLater()
                except Exception:
                    pass
            # Seteamos a None para que nadie intente usar el objeto borrado
            setattr(widget, attr, None)

    # 4. Forzar liberación de memoria
    gc.collect()
    
def dibujar_eventos(ax, id_proyecto, tipo_inst, instrumentos_dict, fecha_inicio, fecha_fin):
    globales = []
    especificos = []
    ids_list = list(instrumentos_dict.keys()) if instrumentos_dict else []
    
    try:
        lista_eventos = EventosController.ctrlObtenerEventos(
            id_proyecto, tipo_inst, ids_list, fecha_inicio, fecha_fin
        )
    except:
        return [], []
    
    if not lista_eventos:
        return [], []

    for evento in lista_eventos:
        id_ev, fecha_ev, desc, color, alcance, id_inst_evento = evento
        
        if isinstance(fecha_ev, str):
            try:
                fecha_ev = datetime.strptime(fecha_ev, '%Y-%m-%d %H:%M:%S')
            except:
                continue
        
        fecha_num = mdates.date2num(fecha_ev)
        estilo_linea = '--' if alcance == 'GLOBAL' else '-.'
        
        linea = ax.axvline(x=fecha_ev, color=color, linestyle=estilo_linea, 
                           linewidth=1.5, alpha=0.7)
        
        texto_desc = (desc[:20] + '..') if len(desc) > 20 else desc
        
        anotacion = ax.annotate(
            texto_desc,
            xy=(fecha_num, 0.96),
            xycoords=ax.get_xaxis_transform(),
            xytext=(4, 0),
            textcoords='offset points',
            rotation=90,
            va='top',
            ha='left',
            color=color,
            fontsize=7,
            fontweight='bold',
            annotation_clip=True,
            clip_on=True
        )
        
        if alcance == 'GLOBAL':
            globales.extend([linea, anotacion])
        else:
            especificos.extend([linea, anotacion])

    return globales, especificos

def procesar_grafica(widget, labeltendencia, data, idx_nombre, idx_fecha, idx_lectura, labelejex, labelejey, tipo, medida, tiempo, titulo, idproyecto, modulo, pluviometro_data=None, equipostendencia=None, escala=None, fecha_inicio=None, fecha_fin=None):
    ax = None
    ax2 = None
    avisolabels = False
    
    # --- CORRECCIÓN SQL SERVER: Validar tipo de dato antes de convertir ---
    if fecha_inicio:
        if isinstance(fecha_inicio, str):
            fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d %H:%M:%S')
    if fecha_fin:
        if isinstance(fecha_fin, str):
            fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d %H:%M:%S')
    # ----------------------------------------------------------------------

    # Crear el DataFrame con las columnas necesarias
    df = pd.DataFrame(data, columns=['col_' + str(i) for i in range(len(data[0]))])
    df = df[[df.columns[0], df.columns[idx_nombre], df.columns[2], df.columns[idx_fecha], df.columns[idx_lectura], df.columns[-1]]]
    df.columns = ['Instrumento', 'Equipo', 'Tiempo', 'Fecha', tipo, 'TipoPrisma']

    if tiempo == "FECHA":
        # pd.to_datetime maneja bien str y datetime, no necesita cambio
        df['Fecha'] = pd.to_datetime(df['Fecha']) 
        if fecha_inicio is None:
            fecha_inicio = df['Fecha'].min()
            fecha_fin = df['Fecha'].max()
        fecha_inicio = pd.to_datetime(fecha_inicio)
        fecha_fin = pd.to_datetime(fecha_fin)
    else:
        if fecha_inicio is None:
            fecha_inicio = df['Fecha'].min()
            fecha_fin = df['Fecha'].max()
        else:
            # --- CORRECCIÓN SQL SERVER: La columna 'Tiempo' puede venir como objeto ---
            val_min_tiempo = df['Tiempo'].min()
            if isinstance(val_min_tiempo, str):
                fechainiproyecto = datetime.strptime(val_min_tiempo, '%Y-%m-%d %H:%M:%S')
            else:
                fechainiproyecto = val_min_tiempo # Ya es datetime
            # ------------------------------------------------------------------------
            
            if tiempo == "HORA":
                unidtiempo = 24
            else:
                unidtiempo = 1
            difdiasini = fecha_inicio - fechainiproyecto
            fecha_inicio = difdiasini.days * unidtiempo
            difdiasfin = fecha_fin - fechainiproyecto
            fecha_fin = difdiasfin.days * unidtiempo

    ejeymin, ejeymax, ejeyprin, ejeysecu, intervalo_dias = 0, 0, 0, 0, 0
    dataeje = ConfiguracionController.ctrlObtenerConfiguracionEje(idproyecto, modulo, tipo)
    if dataeje:
        ejeymin, ejeymax, ejeyprin, ejeysecu = dataeje[4], dataeje[5], dataeje[6], dataeje[7]
        if tiempo == "HORA":
            intervalo_dias = dataeje[8] * 24
        else:
            intervalo_dias = dataeje[8]
    if tiempo == "FECHA":
        total_dias = (fecha_fin - fecha_inicio).days
    else:
        # Aquí total_dias ya está en Horas o Días según la conversión anterior
        total_dias = (fecha_fin - fecha_inicio)

    # --- CORRECCIÓN APLICADA AQUÍ ---
    if intervalo_dias == 0:
        if tiempo == "HORA":
            # Eliminado el (* 24) redundante porque total_dias ya está en horas
            intervalo_dias = total_dias / 10 
        else:
            intervalo_dias = total_dias / 10
            
    limpiar_widget(widget)

    config = SoftwareConfiguracion.obtenerDataSoftware()
    SUAVIZADO_ESTADO = True if config[20] == 1 else False
    titulozise, ejezise, etiquesize, leyendazise, vertices = config[0], config[1], config[2], config[3], config[6]
    lineatenden, grosortenden, colortenden, fuente = config[7], config[8], config[9], config[10]
    grosorlinea, grosorvertice, decimales, mostrarlluvia, posicionlluvia = config[12], config[13], config[14], config[17], config[18]

    figure, ax = plt.subplots()
    canvas = FigureCanvas(figure)
    plt.rcParams['font.family'] = fuente
    layout = widget.layout()

    # --- INICIO MODIFICACIÓN PASO 2 ---
    toolbar_container = QWidget()
    widget.toolbar_container = toolbar_container
    toolbar_layout = QHBoxLayout(toolbar_container)
    toolbar_layout.setContentsMargins(0, 0, 0, 0)
    widget.toolbar = CustomToolbar(canvas, widget)
    toolbar_layout.addWidget(widget.toolbar)
    check_inspector = QCheckBox("Inspector de Datos")
    check_inspector.setStyleSheet("font-size: 12px; margin-left: 10px; font-weight: bold;")
    toolbar_layout.addWidget(check_inspector)
    check_ev_global = QCheckBox("Ev. Globales")
    check_ev_global.setChecked(True)
    check_ev_global.setStyleSheet("font-size: 11px; margin-left: 5px; color: #007bff; font-weight: bold;")
    toolbar_layout.addWidget(check_ev_global)
    check_ev_equipo = QCheckBox("Ev. Equipo")
    check_ev_equipo.setChecked(True)
    check_ev_equipo.setStyleSheet("font-size: 11px; margin-left: 3px; color: #28a745; font-weight: bold;")
    toolbar_layout.addWidget(check_ev_equipo)
    btn_add_evento = QPushButton("+ Evento")
    btn_add_evento.setCheckable(True) # Modo Toggle
    btn_add_evento.setStyleSheet("""
        QPushButton { font-size: 11px; padding: 4px; background-color: #f0f0f0; border: 1px solid #ccc; border-radius: 3px; }
        QPushButton:checked { background-color: #ffcccc; border: 1px solid red; color: red; font-weight: bold; }
    """)
    toolbar_layout.addWidget(btn_add_evento)
    canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    # El contenedor del toolbar solo ocupa lo que necesita
    toolbar_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    layout.addWidget(canvas)
    layout.addWidget(toolbar_container)

    barras_pluviometro = None
    if tiempo == "FECHA":
        if modulo != "ANALISIS":
            if mostrarlluvia == 0:
                if pluviometro_data:
                    idpluvio = str(pluviometro_data[0][0])
                    estilo = ConfiguracionController.ctrlTraerEstiloEquipoGrafica(idproyecto, idpluvio, 0)
                    df_pluviometro = pd.DataFrame(pluviometro_data, columns=['Codigo', 'Fecha', 'Lectura'])
                    df_pluviometro['Fecha'] = pd.to_datetime(df_pluviometro['Fecha'])
                    ax2 = ax.twinx()
                    diferencia = df_pluviometro['Fecha'].max() - df_pluviometro['Fecha'].min()
                    totaldias = diferencia.days
                    ancho = 0.8
                    if totaldias > 0:
                        if totaldias < 100:
                            ancho = totaldias / 100
                        else:
                            ancho = totaldias / 200
                    if estilo:
                        if posicionlluvia == 0:
                            ax2.set_ylim(int(estilo[3]), 0)
                        else:
                            ax2.set_ylim(0, int(estilo[3]))
                        barras_pluviometro = ax2.bar(df_pluviometro['Fecha'], df_pluviometro['Lectura'], color=estilo[5], width=ancho, label="Precipitación")
                        ticks = np.arange(0, int(estilo[3]) + int(estilo[4]), int(estilo[4]))
                        ax2.set_yticks(ticks)
                    else:
                        if posicionlluvia == 0:
                            ax2.set_ylim(100, 0)
                        else:
                            ax2.set_ylim(0, 100)
                        barras_pluviometro = ax2.bar(df_pluviometro['Fecha'], df_pluviometro['Lectura'], color='cyan', width=ancho, alpha=0.5, label="Precipitación")
                    ax2.set_ylabel("Precipitacion (mm)", fontsize=ejezise)
                else:
                    ax2 = ax.twinx()
                    if posicionlluvia == 0:
                        ax2.set_ylim(100, 0)
                    else:
                        ax2.set_ylim(0, 100)
                    ax2.axhline(y=0, color='cyan', linestyle='-', linewidth=2, alpha=0.5)
                    ax2.set_ylabel("Precipitacion (mm)", fontsize=ejezise)
                    barras_pluviometro = mpatches.Patch(color='cyan', alpha=0.5)
            else:
                if pluviometro_data:
                    idpluvio = str(pluviometro_data[0][0])
                    estilo = ConfiguracionController.ctrlTraerEstiloEquipoGrafica(idproyecto, idpluvio, 0)
                    df_pluviometro = pd.DataFrame(pluviometro_data, columns=['Codigo', 'Fecha', 'Lectura'])
                    df_pluviometro['Fecha'] = pd.to_datetime(df_pluviometro['Fecha'])
                    ax2 = ax.twinx()
                    diferencia = df_pluviometro['Fecha'].max() - df_pluviometro['Fecha'].min()
                    totaldias = diferencia.days
                    ancho = 0.8
                    if totaldias > 0:
                        if totaldias < 100:
                            ancho = totaldias / 100
                        else:
                            ancho = totaldias / 200
                    if estilo:
                        if posicionlluvia == 0:
                            ax2.set_ylim(int(estilo[3]), 0)
                        else:
                            ax2.set_ylim(0, int(estilo[3]))
                        barras_pluviometro = ax2.bar(df_pluviometro['Fecha'], df_pluviometro['Lectura'], color=estilo[5], width=ancho, label="Precipitación")
                        ticks = np.arange(0, int(estilo[3]) + int(estilo[4]), int(estilo[4]))
                        ax2.set_yticks(ticks)
                    else:
                        if posicionlluvia == 0:
                            ax2.set_ylim(100, 0)
                        else:
                            ax2.set_ylim(0, 100)
                        barras_pluviometro = ax2.bar(df_pluviometro['Fecha'], df_pluviometro['Lectura'], color='cyan', width=ancho, alpha=0.5, label="Precipitación")
                    ax2.set_ylabel("Precipitacion (mm)", fontsize=ejezise)

    lineas = []
    lblecuacion_rcuadrado = ""
    prismasmodulo = {"DESPLAZAMIENTO", "VELOCIDAD", "ANALISIS"}
    equipotipo = 1 if modulo in prismasmodulo else 0

    for idinstrumento, datos_equipo in df.groupby('Instrumento'):
        nombreequipo = str(datos_equipo['Equipo'].iloc[0])
        if equipotipo == 1:
            equipo = str(datos_equipo['Equipo'].iloc[0])
        else:
            equipo = idinstrumento
        estilo = ConfiguracionController.ctrlTraerEstiloEquipoGrafica(idproyecto, idinstrumento, 0)
        
        # ── ANTES: linea, = ax.plot(...)
        # ── AHORA: plot_linea_suavizada(...)
        if estilo:
            if vertices == 1:
                linea = plot_linea_suavizada(
                    ax, datos_equipo['Fecha'], datos_equipo[tipo], tiempo, activo=SUAVIZADO_ESTADO,
                    linestyle=estilo[3], marker='o',
                    markersize=estilo[4] + 4, linewidth=estilo[4],
                    color=estilo[5], label=nombreequipo
                )
            else:
                linea = plot_linea_suavizada(
                    ax, datos_equipo['Fecha'], datos_equipo[tipo], tiempo, activo=SUAVIZADO_ESTADO,
                    linestyle=estilo[3], linewidth=estilo[4],
                    color=estilo[5], label=nombreequipo
                )
        else:
            if vertices == 1:
                linea = plot_linea_suavizada(
                    ax, datos_equipo['Fecha'], datos_equipo[tipo], tiempo, activo=SUAVIZADO_ESTADO,
                    marker='o', markersize=grosorvertice,
                    linewidth=grosorlinea, label=nombreequipo
                )
            else:
                linea = plot_linea_suavizada(
                    ax, datos_equipo['Fecha'], datos_equipo[tipo], tiempo, activo=SUAVIZADO_ESTADO,
                    linewidth=grosorlinea, label=nombreequipo
                )
        lineas.append(linea)
        # El resto del bucle (tendencias, etc.) NO cambia

        if equipostendencia:
            for instru, regresion, grado in equipostendencia:
                if str(instru[equipotipo]) == str(equipo):
                    if regresion == 'Lineal':
                        lineal = CalculosTendencias.dibujarTendenciaLineal(datos_equipo['Fecha'], datos_equipo[tipo], ax, tiempo, 1, nombreequipo, lineatenden, grosortenden, colortenden)
                        lineas.append(lineal)
                        ecualbl = CalculosTendencias.generarEcuacionTendencia(datos_equipo['Fecha'], datos_equipo[tipo], tiempo, 1)
                        lblecuacion_rcuadrado = lblecuacion_rcuadrado + nombreequipo + ':  ' + ecualbl + '\n'
                    elif regresion == 'Polinómica':
                        polino = CalculosTendencias.dibujarTendenciaLineal(datos_equipo['Fecha'], datos_equipo[tipo], ax, tiempo, grado, nombreequipo, lineatenden, grosortenden, colortenden)
                        lineas.append(polino)
                        ecualbl = CalculosTendencias.generarEcuacionTendencia(datos_equipo['Fecha'], datos_equipo[tipo], tiempo, grado)
                        lblecuacion_rcuadrado = lblecuacion_rcuadrado + nombreequipo + ':  ' + ecualbl + '\n'
                    elif regresion == 'Media Móvil':
                        media = CalculosTendencias.dibujarMediaMovil(datos_equipo['Fecha'], datos_equipo[tipo], ax, nombreequipo, grado, lineatenden, grosortenden, colortenden)
                        lineas.append(media)
                    elif regresion == 'Logarítmica':
                        logari, ecualbl = CalculosTendencias.dibujarTendenciaLogaritmica(datos_equipo['Fecha'], datos_equipo[tipo], ax, tiempo, nombreequipo, lineatenden, grosortenden, colortenden)
                        lineas.append(logari)
                        lblecuacion_rcuadrado = lblecuacion_rcuadrado + nombreequipo + ':  ' + ecualbl + '\n'
                    elif regresion == 'Exponencial':
                        exponen, ecualbl = CalculosTendencias.dibujarTendenciaExponencial(datos_equipo['Fecha'], datos_equipo[tipo], ax, tiempo, nombreequipo, lineatenden, grosortenden, colortenden)
                        if exponen:
                            lineas.append(exponen)
                            lblecuacion_rcuadrado = lblecuacion_rcuadrado + nombreequipo + ':  ' + ecualbl + '\n'
                    elif regresion == 'Potencial':
                        potenci, ecualbl = CalculosTendencias.dibujarTendenciaPotencial(datos_equipo['Fecha'], datos_equipo[tipo], ax, tiempo, nombreequipo, lineatenden, grosortenden, colortenden)
                        if potenci:
                            lineas.append(potenci)
                            lblecuacion_rcuadrado = lblecuacion_rcuadrado + nombreequipo + ':  ' + ecualbl + '\n'
    if labeltendencia:
        if tiempo != "FECHA":
            labeltendencia.setText(lblecuacion_rcuadrado)
        else:
            labeltendencia.setText("")

    ax.set_title(titulo, fontsize=titulozise)
    ax.set_xlabel(labelejex, fontsize=ejezise)
    ax.set_ylabel(labelejey, fontsize=ejezise)
    if tiempo == "FECHA":
        ax.xaxis.set_major_formatter(DateFormatter('%d/%m/%Y'))
    if not escala:
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda val, pos: '{:.{}f}'.format(val, decimales)))
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)

    # -----------------------------------------------------------------------------
    # MEJORA VISUAL: CÁLCULO DE ETIQUETAS SIMÉTRICAS (LINSPACE)
    # -----------------------------------------------------------------------------
    if tiempo == "FECHA":
        # Convertimos fechas a números de matplotlib
        num_inicio = mdates.date2num(fecha_inicio)
        num_fin = mdates.date2num(fecha_fin)
        rango_total = num_fin - num_inicio
        intervalo_num = intervalo_dias 
    else:
        # Ya son números (Días u Horas)
        num_inicio = float(fecha_inicio)
        num_fin = float(fecha_fin)
        rango_total = num_fin - num_inicio
        intervalo_num = intervalo_dias

    # Calcular cantidad de etiquetas basada en el intervalo
    if intervalo_num <= 0:
        num_etiquetas = 10
    else:
        num_etiquetas = int(rango_total / intervalo_num) + 1

    # Protección de saturación: Limitar a 15-20 etiquetas para que se vean bien
    if num_etiquetas > 25: 
        avisolabels = True
        num_etiquetas = 15 # Forzar visualización limpia
    elif num_etiquetas < 2:
        num_etiquetas = 2

    # Generación de puntos matemáticamente equidistantes (Simetría)
    etiquetas_numericas = np.linspace(num_inicio, num_fin, num_etiquetas)
    ax.set_xticks(etiquetas_numericas)

    if escala:
        if escala == 'ESL':
            ax.set_yscale("log", base=10)
            ax.set_xlim([num_inicio, num_fin])
        else:
            ax.set_xscale("log", base=10)
            ax.set_yscale("log", base=10)
    else:
        ax.set_xlim([num_inicio, num_fin])
    # -----------------------------------------------------------------------------
    
    plt.setp(ax.get_xticklabels(), rotation=90, ha="center", fontsize=etiquesize)
    plt.setp(ax.get_yticklabels(), fontsize=etiquesize)
    if modulo != "ANALISIS":
        if mostrarlluvia == 0:
            if tiempo == "FECHA":
                plt.setp(ax2.get_yticklabels(), fontsize=etiquesize)
        else:
            if tiempo == "FECHA":
                if pluviometro_data:
                    plt.setp(ax2.get_yticklabels(), fontsize=etiquesize)

    if ejeymin != 0 or ejeymax != 0:
        if escala is None:
            ax.set_ylim(ejeymin * medida, ejeymax * medida)
            maxejey = (ejeymax * medida) + 0.0001
            if ejeyprin > 0:
                tick_primarios = np.arange(ejeymin * medida, maxejey, ejeyprin * medida)
                if len(tick_primarios) > 1 and len(tick_primarios) < 100:
                    ax.set_yticks(tick_primarios)
                else:
                    avisolabels = True
            if ejeysecu > 0:
                tick_secundarios = np.arange(ejeymin * medida, maxejey, ejeysecu * medida)
                if len(tick_secundarios) > 1 and len(tick_secundarios) < 200:
                    for tick in tick_secundarios:
                        ax.axhline(y=tick, color='gray', linestyle='--', linewidth=0.5)
                else:
                    avisolabels = True

    annot = ax.annotate("", xy=(0,0), xytext=(15,15), textcoords="offset points",
                        bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#cccccc", lw=1, alpha=0.95),
                        arrowprops=dict(arrowstyle="-|>", connectionstyle="arc3,rad=0.2", color="#555555", lw=0.8))
    annot.set_visible(False)

    punto_resaltado, = ax.plot([], [], 'o', color='#dc3545', markersize=5, markeredgecolor='white', markeredgewidth=1, zorder=10)
    punto_resaltado.set_visible(False)
    
    # Marcador y etiqueta para modo "agregar evento"
    marcador_evento, = ax.plot([], [], 'D', color='#ff4444', markersize=9,
                                markeredgecolor='white', markeredgewidth=1.5, zorder=11)
    marcador_evento.set_visible(False)

    label_evento = ax.annotate("", xy=(0, 0), xytext=(10, -20),
                                textcoords="offset points",
                                bbox=dict(boxstyle="round,pad=0.3", fc="#fff3cd",
                                          ec="#ffc107", lw=1, alpha=0.95),
                                fontsize=9, fontweight='bold', color='#856404',
                                annotation_clip=True)
    label_evento.set_visible(False)

    equipo_detectado = {'id': None, 'nombre': None}
    # --- EVENTOS ---
    linea_fantasma = ax.axvline(x=fecha_inicio, color='red', linestyle='--', linewidth=1.5, alpha=0.6)
    linea_fantasma.set_visible(False)

    instrumentos_dict = {}
    for idinstrumento, datos_equipo in df.groupby('Instrumento'):
        nombre = str(datos_equipo['Equipo'].iloc[0])
        if modulo in {"DESPLAZAMIENTO", "VELOCIDAD", "ANALISIS"}:
            instrumentos_dict[nombre] = nombre
        else:
            instrumentos_dict[str(idinstrumento)] = nombre
    
    nombre_a_id = {v: k for k, v in instrumentos_dict.items()}

    ev_globales, ev_especificos = dibujar_eventos(ax, idproyecto, "PRISMA", instrumentos_dict, fecha_inicio, fecha_fin)
    objetos_eventos = ev_globales + ev_especificos
    
    def toggle_ev_global(checked):
        for obj in ev_globales:
            try: obj.set_visible(checked)
            except: pass
        canvas.draw_idle()
    
    def toggle_ev_equipo(checked):
        for obj in ev_especificos:
            try: obj.set_visible(checked)
            except: pass
        canvas.draw_idle()
    
    def on_toggle_add_evento(checked):
        if not checked:
            marcador_evento.set_visible(False)
            label_evento.set_visible(False)
            linea_fantasma.set_visible(False)
            canvas.draw_idle()
    
    check_ev_global.toggled.connect(toggle_ev_global)
    check_ev_equipo.toggled.connect(toggle_ev_equipo)
    btn_add_evento.toggled.connect(on_toggle_add_evento)
    # ----------------------------------

    def calculate_columns():
        font_config = {'family': fuente, 'size': leyendazise, 'weight': 'normal'}
        renderer = canvas.get_renderer()

        leyenda_labels = [line.get_label() for line in lineas] + (["Precipitación"] if barras_pluviometro else [])

        max_width = 0
        for label in leyenda_labels:
            text_obj = ax.text(0, 0, label, fontproperties=font_config)
            width = text_obj.get_window_extent(renderer).width + (leyendazise*3)
            max_width = max(max_width, width)
            text_obj.remove()

        ancho_pantalla = widget.width()

        return max(1, int((ancho_pantalla - 100) / (max_width + 50)))

    def actualizar_leyenda():
        try:
            ncols = calculate_columns()
            leyenda_elementos = lineas + ([barras_pluviometro] if barras_pluviometro else [])
            leyenda_labels = [line.get_label() for line in lineas] + (["Precipitación"] if barras_pluviometro else [])
            
            if SUAVIZADO_ESTADO:
                for line in lineas:
                    if hasattr(line, '_estilo_puro'):
                        line.set_linestyle(line._estilo_puro)
                        line.set_alpha(1.0)

            legend = ax.legend(handles=leyenda_elementos, labels=leyenda_labels, 
                            loc='upper center', bbox_to_anchor=(0.5, 0), 
                            ncol=ncols, frameon=False, fontsize=leyendazise, 
                            borderaxespad=0.8)

            # --- CAMBIO CLAVE: CONECTAR INTERACCIÓN ---
            # Pasamos los elementos reales de la leyenda para que sean interactivos
            configurar_evento_leyenda(canvas, legend, leyenda_elementos)
            # ------------------------------------------

            if SUAVIZADO_ESTADO:
                for line in lineas:
                    if hasattr(line, '_estilo_puro'):
                        # Restauramos el estado fantasma, pero respetamos si el usuario lo apagó
                        # Si la línea está visible (on), se mantiene transparente en el gráfico
                        # Si la línea está oculta (off), se queda oculta.
                        if line.get_visible():
                            line.set_linestyle('none')
                            line.set_alpha(0)

            renderer = canvas.get_renderer()
            canvas.draw()
            fig_bbox = figure.bbox
            legend_bbox = legend.get_window_extent(renderer)
            legend_height = legend_bbox.height / fig_bbox.height
            padding = 0.08
            bottom_margin = 0.20 + legend_height + padding
            top_margin = 0.95 - (legend_height * 0.3)

            if bottom_margin >= top_margin:
                bottom_margin = 0.25
                top_margin = 0.90
                if ncols == 1:
                    bottom_margin = 0.35
                    top_margin = 0.85

            figure.subplots_adjust(bottom=bottom_margin, top=top_margin, left=0.1, right=0.90)
            canvas.draw()
            if figure.subplotpars.bottom >= figure.subplotpars.top:
                raise ValueError("Margen inválido, aplicando valores seguros")
            xlabel_bbox = ax.xaxis.label.get_window_extent(renderer=renderer)
            xlabel_bottom = xlabel_bbox.transformed(ax.transAxes.inverted()).y0
            legend.set_bbox_to_anchor((0.5, xlabel_bottom))
        except Exception as e:
            figure.subplots_adjust(bottom=0.25, top=0.90, left=0.1, right=0.90)
            ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=2, fontsize=8)
            canvas.draw()

    def on_resize(event):
        actualizar_leyenda()
    
    def procesar_datos_console(id_proyecto,label, date, reading, tipo_prisma):
        # Convertir la fecha al formato yyyy-mm-dd hh:mm:ss para la consola
        date_obj = datetime.strptime(date, '%d/%m/%Y %H:%M:%S')
        formatted_date= date_obj.strftime('%Y-%m-%d %H:%M:%S')

        dialog = ModalDialog(widget,label, date, reading)
        result = dialog.exec()

        if result == QDialog.Accepted:          
            respuesta=PrismaController.ctrlOmitirLecturaPrisma(id_proyecto,label,formatted_date,tipo_prisma)
            if respuesta:
                print(f"{label}\nFecha: {formatted_date}\nLectura: {reading}\nTipo: {tipo_prisma}")
            else:
                print('error al omitir')
                
    def on_hover(event):
        if event.inaxes != ax:
            if annot.get_visible(): annot.set_visible(False)
            if punto_resaltado.get_visible(): punto_resaltado.set_visible(False)
            if linea_fantasma.get_visible(): linea_fantasma.set_visible(False)
            if marcador_evento.get_visible(): marcador_evento.set_visible(False)
            if label_evento.get_visible(): label_evento.set_visible(False)
            canvas.draw_idle()
            return

        if btn_add_evento.isChecked():
            annot.set_visible(False)
            punto_resaltado.set_visible(False)
            linea_fantasma.set_xdata([event.xdata])
            linea_fantasma.set_visible(True)
            
            min_dist = 40
            cercano = None
            xlim, ylim = ax.get_xlim(), ax.get_ylim()
            
            for line in lineas:
                if not line.get_visible():
                    continue
                x_data, y_data = line.get_data()
                if tiempo == "FECHA":
                    try:
                        if hasattr(x_data, 'dtype') and (x_data.dtype == 'object' or np.issubdtype(x_data.dtype, np.datetime64)):
                            x_data = mdates.date2num(x_data)
                    except:
                        continue
                mask = ((x_data >= xlim[0]) & (x_data <= xlim[1]) &
                        (y_data >= ylim[0]) & (y_data <= ylim[1]))
                if not np.any(mask):
                    continue
                puntos_px = ax.transData.transform(np.column_stack([x_data[mask], y_data[mask]]))
                mouse = np.array([event.x, event.y])
                dists = np.sqrt(np.sum((puntos_px - mouse) ** 2, axis=1))
                if len(dists) > 0:
                    idx = np.argmin(dists)
                    if dists[idx] < min_dist:
                        min_dist = dists[idx]
                        cercano = (x_data[mask][idx], y_data[mask][idx], line.get_label())
            
            if cercano:
                fx, fy, nombre = cercano
                marcador_evento.set_data([fx], [fy])
                marcador_evento.set_visible(True)
                label_evento.xy = (fx, fy)
                label_evento.set_text(nombre)
                label_evento.set_visible(True)
                equipo_detectado['id'] = nombre_a_id.get(nombre)
                equipo_detectado['nombre'] = nombre
            else:
                marcador_evento.set_visible(False)
                label_evento.set_visible(False)
                equipo_detectado['id'] = None
                equipo_detectado['nombre'] = None
            
            canvas.draw_idle()
            return

        # --- MODO 2: INSPECTOR (Tu lógica original) ---
        linea_fantasma.set_visible(False)
        marcador_evento.set_visible(False)
        label_evento.set_visible(False)
        
        if not check_inspector.isChecked():
            return

        # (Tu lógica de búsqueda de punto cercano intacta)
        min_distancia = 30
        punto_encontrado = None
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()

        for line in lineas:
            if not line.get_visible(): continue
            x_data, y_data = line.get_data()
            if tiempo == "FECHA":
                try:
                    if hasattr(x_data, 'dtype') and (x_data.dtype == 'object' or np.issubdtype(x_data.dtype, np.datetime64)):
                         x_data = mdates.date2num(x_data)
                except Exception: continue 

            mask = (x_data >= xlim[0]) & (x_data <= xlim[1]) & (y_data >= ylim[0]) & (y_data <= ylim[1])
            if not np.any(mask): continue
            
            puntos_pixel = ax.transData.transform(np.column_stack([x_data[mask], y_data[mask]]))
            mouse_pos = np.array([event.x, event.y])
            distancias = np.sqrt(np.sum((puntos_pixel - mouse_pos)**2, axis=1))
            
            if len(distancias) > 0:
                idx_min = np.argmin(distancias)
                if distancias[idx_min] < min_distancia:
                    min_distancia = distancias[idx_min]
                    punto_encontrado = (x_data[mask][idx_min], y_data[mask][idx_min], line.get_label())

        if punto_encontrado:
            fecha_num, lectura_val, label_equipo = punto_encontrado
            punto_resaltado.set_data([fecha_num], [lectura_val])
            punto_resaltado.set_visible(True)
            
            punto_pixel = ax.transData.transform((fecha_num, lectura_val))
            x_rel, y_rel = ax.transAxes.inverted().transform(punto_pixel)
            
            offset_x, offset_y = 15, 15
            ha, va = 'left', 'bottom'
            if y_rel > 0.70: va, offset_y = 'top', -15
            if x_rel > 0.65: ha, offset_x = 'right', -15

            annot.xy = (fecha_num, lectura_val)
            annot.xytext = (offset_x, offset_y)
            annot.set_ha(ha)
            annot.set_va(va)
            
            str_fecha = mdates.num2date(fecha_num).replace(tzinfo=None).strftime('%d/%m/%Y %H:%M') if tiempo == "FECHA" else f"{fecha_num:.2f}"
            annot.set_text(f"{label_equipo}\nFecha: {str_fecha}\nLectura: {lectura_val:.3f}")
            annot.set_fontsize(9)
            annot.set_color('#333333')
            annot.set_visible(True)
            annot.set_zorder(999)
            canvas.draw_idle()
        else:
            if annot.get_visible():
                annot.set_visible(False)
                punto_resaltado.set_visible(False)
                canvas.draw_idle()
    
    def on_click(event):
        # --- CASO A: CREAR NUEVO EVENTO ---
        if btn_add_evento.isChecked():
            if event.button == 1 and event.inaxes == ax:
                fecha_clic = mdates.num2date(event.xdata).replace(tzinfo=None)
                
                eq_id = equipo_detectado.get('id')
                eq_nombre = equipo_detectado.get('nombre')
                
                dialog = EventosDialog(widget, fecha_clic, idproyecto, "PRISMA", eq_id, eq_nombre)
                if dialog.exec():
                    datos = dialog.obtener_datos()
                    exito = EventosController.ctrlCrearEvento(
                        idproyecto, datos['fecha'], datos['descripcion'], datos['color'],
                        datos['alcance'], "PRISMA", datos['id_instrumento']
                    )
                    if exito:
                        fecha_num_click = mdates.date2num(datos['fecha'])
                        nueva_linea = ax.axvline(x=datos['fecha'], color=datos['color'],
                                                  linestyle='--', linewidth=1.5, alpha=0.7)
                        
                        desc_full = datos['descripcion']
                        texto_safe = (desc_full[:20] + '..') if len(desc_full) > 20 else desc_full
                        
                        nuevo_texto = ax.annotate(
                            texto_safe,
                            xy=(fecha_num_click, 0.96),
                            xycoords=ax.get_xaxis_transform(),
                            xytext=(4, 0), textcoords='offset points',
                            rotation=90, va='top', ha='left',
                            color=datos['color'], fontsize=7, fontweight='bold',
                            annotation_clip=True, clip_on=True
                        )
                        
                        if datos['alcance'] == 'GLOBAL':
                            ev_globales.extend([nueva_linea, nuevo_texto])
                        else:
                            ev_especificos.extend([nueva_linea, nuevo_texto])
                        objetos_eventos.extend([nueva_linea, nuevo_texto])
                        
                        canvas.draw()
                        btn_add_evento.setChecked(False)
                        mostrar_mensaje("Éxito", "Evento agregado.", "info")
                    else:
                        mostrar_mensaje("Error", "No se pudo guardar el evento.", "error")
                
                marcador_evento.set_visible(False)
                label_evento.set_visible(False)
                linea_fantasma.set_visible(False)
                canvas.draw_idle()
            return

        # --- CASO B: TU LÓGICA ORIGINAL (Seleccionar / Omitir Lectura) ---
        # (Se ejecuta solo si NO estamos agregando un evento)
        
        if ax2:
            current_ax = ax2
        else:
            current_ax = ax

        # Verificar si el clic está dentro de los límites de los ejes
        if current_ax and current_ax.in_axes(event) and event.xdata is not None and event.ydata is not None:
            for line in lineas:
                contains, _ = line.contains(event)
                if contains:
                    label = line.get_label()
                    x = mdates.num2date(event.xdata).replace(tzinfo=None)
                    y = event.ydata

                    line_data = df[df['Equipo'] == label]

                    if line_data.empty:
                        date = x.strftime('%d/%m/%Y %H:%M:%S')
                        reading = round(y, 3)
                        annotation_text = f"{label}\nFecha: {date}\nLectura: {reading}"
                    else:
                        if line_data['Fecha'].dt.tz is not None:
                            line_data['Fecha'] = line_data['Fecha'].dt.tz_localize(None)

                        data_point = line_data.iloc[(line_data['Fecha'] - x).abs().argmin()]
                        closest_x = data_point['Fecha']
                        closest_y = data_point[tipo]
                        date = closest_x.strftime('%d/%m/%Y %H:%M:%S')
                        reading = round(closest_y, 3)
                        tipo_prisma = data_point['TipoPrisma']
                        annotation_text = f"{label}\nFecha: {date}\nLectura: {reading}"

                    # Anticlick (Click Derecho) - Mostrar etiqueta amarilla fija
                    if event.button == 3:
                        for text in current_ax.texts:
                            # PROTECCIÓN: No borrar las etiquetas de los eventos
                            if text not in objetos_eventos:
                                text.set_visible(False)

                        annotation = current_ax.annotate(annotation_text, (x, y),
                                                        textcoords="offset points", xytext=(10, 10),
                                                        ha='left', fontsize=etiquesize,
                                                        bbox=dict(facecolor='yellow', alpha=0.8, edgecolor='none'))
                        annotation.set_visible(True)
                        canvas.draw()
                        break 

        # Click Izquierdo (Ctrl+Click para Omitir, Click normal para limpiar)
        if event.button == 1:
            if event.guiEvent.modifiers() & Qt.ControlModifier:
                # Tu lógica de omitir lectura
                procesar_datos_console(idproyecto, label, date, reading, tipo_prisma)
            else:
                # Limpiar etiquetas (respetando eventos)
                for text in current_ax.texts:
                    if text not in objetos_eventos:
                        text.set_visible(False)
                canvas.draw()

    canvas.mpl_connect('resize_event', on_resize)
    canvas.mpl_connect('button_press_event', on_click)
    canvas.mpl_connect('motion_notify_event', on_hover)
    actualizar_leyenda()
    plt.close(figure)
    if avisolabels:
        mostrar_mensaje("Ejes", "No se aplica la configuración de ejes.", "advertencia")

def procesar_grafica_piezometros(widget, labeltendencia, data, cotasmarcadas, idx_nombre, idx_fecha, idx_lectura, idx_funda, idx_super, labelejex, labelejey, tipo, medida, tiempo, titulo, idproyecto, modulo, pluviometro_data=None, equipostendencia=None, dataterreno=None, fecha_inicio=None, fecha_fin=None):
    ax = None
    ax2 = None
    avisolabels = False
    
    # =========================================================================
    # NUEVO: IDENTIFICACIÓN DEL TIPO DE INSTRUMENTO PARA EVENTOS
    # =========================================================================
    # Mapeo claro entre módulo/tipo y el identificador que se guarda en BD
    def determinar_tipo_instrumento(modulo_actual, tipo_dato, df_datos=None):
        """
        Determina el tipo de instrumento para eventos según el contexto.
        """
        if modulo_actual == "CELDAS" or tipo_dato == "AC":
            return ("CELDA", "Celda")
        
        elif modulo_actual == "PIEZOMETROS" or tipo_dato == "NF":
            if df_datos is not None and 'TipoPiezo' in df_datos.columns:
                tipos_unicos = df_datos['TipoPiezo'].unique()
                
                if len(tipos_unicos) == 1:
                    tipo_piezo_raw = str(tipos_unicos[0]).strip()
                    tipo_piezo = tipo_piezo_raw.upper()
                    
                    # Normalizar: quitar prefijos redundantes
                    tipo_limpio = (tipo_piezo
                                   .replace("PIEZÓMETRO", "")
                                   .replace("PIEZOMETRO", "")
                                   .replace("PIEZO", "")
                                   .replace("_", "")
                                   .replace(" ", "")
                                   .strip())
                    
                    if tipo_limpio in ("CV", "CUERDA", "CUERDAVIBRANTE", "VIBRANTE"):
                        return ("PIEZO_CUERDA", "Piezo Cuerda")
                    elif tipo_limpio in ("CA", "CASAGRANDE", "CASA"):
                        return ("PIEZO_CASAGRANDE", "Piezo Casagrande")
                    elif tipo_limpio in ("MA", "MANUAL", "MAN"):
                        return ("PIEZO_MANUAL", "Piezo Manual")
                    elif tipo_limpio in ("NE", "NEUMATICO", "NEUMATICO"):
                        return ("PIEZO_NEUMATICO", "Piezo Neumático")
                    elif tipo_limpio == "":
                        return ("PIEZOMETRO", "Piezómetro")
                    else:
                        # Fallback: usar solo la parte limpia
                        return (f"PIEZO_{tipo_limpio}", f"Piezo {tipo_limpio.title()}")
                else:
                    return ("PIEZOMETRO", "Piezómetro Mixto")
            
            return ("PIEZOMETRO", "Piezómetro")
        
        else:
            return ("PIEZOMETRO", "Piezómetro")
    # =========================================================================

    # --- CORRECCIÓN SQL SERVER: Validar tipo de dato antes de convertir ---
    if fecha_inicio:
        if isinstance(fecha_inicio, str):
            fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d %H:%M:%S')
    if fecha_fin:
        if isinstance(fecha_fin, str):
            fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d %H:%M:%S')
    # ----------------------------------------------------------------------
    
    # Convertir fechas a datetime y asignar valores por defecto
    ejeymin, ejeymax, ejeyprin, ejeysecu, intervalo_dias = 0, 0, 0, 0, 0
    if data:
        df = pd.DataFrame(data, columns=['col_' + str(i) for i in range(len(data[0]))])
        df = df[[df.columns[0], df.columns[idx_nombre], df.columns[2], df.columns[idx_fecha], df.columns[idx_lectura], df.columns[idx_funda], df.columns[idx_super], df.columns[-2],df.columns[-1]]]
        df.columns = ['Instrumento', 'Equipo', 'Tiempo', 'Fecha', tipo, "Fundacion", "Superficie", "TipoPiezo", "idEquipo"]
        # validar formato filtrado
        if tiempo == "FECHA":
            df['Fecha'] = pd.to_datetime(df['Fecha'])
            if fecha_inicio is None:
                fecha_inicio = df['Fecha'].min()
                fecha_fin = df['Fecha'].max()
            fecha_inicio = pd.to_datetime(fecha_inicio)
            fecha_fin = pd.to_datetime(fecha_fin)
        else:
            df['Fecha'] = df['Fecha'].astype(float)
            if fecha_inicio is None:
                fecha_inicio = df['Fecha'].min()
                fecha_fin = df['Fecha'].max()
            else:
                val_min_tiempo = df['Tiempo'].min()
                if isinstance(val_min_tiempo, str):
                    fechainiproyecto = datetime.strptime(val_min_tiempo, '%Y-%m-%d %H:%M:%S')
                else:
                    fechainiproyecto = val_min_tiempo
                
                if tiempo == "HORA":
                    unidtiempo = 24
                else:
                    unidtiempo = 1
                difdiasini = fecha_inicio - fechainiproyecto
                fecha_inicio = difdiasini.days * unidtiempo
                difdiasfin = fecha_fin - fechainiproyecto
                fecha_fin = difdiasfin.days * unidtiempo
    
    # =========================================================================
    # NUEVO: DETERMINAR TIPO DESPUÉS DE CREAR EL DATAFRAME
    # =========================================================================
    if data:
        tipo_evento, etiqueta_tipo = determinar_tipo_instrumento(modulo, tipo, df)
    else:
        tipo_evento, etiqueta_tipo = determinar_tipo_instrumento(modulo, tipo, None)
    # =========================================================================

    # Ajustar limites de gráficas eje y
    dataeje = ConfiguracionController.ctrlObtenerConfiguracionEje(idproyecto, modulo, tipo)
    if dataeje:
        ejeymin, ejeymax, ejeyprin, ejeysecu = dataeje[4], dataeje[5], dataeje[6], dataeje[7]
        if tiempo == "HORA":
            intervalo_dias = dataeje[8] * 24
        else:
            intervalo_dias = dataeje[8]
    if tiempo == "FECHA":
        total_dias = (fecha_fin - fecha_inicio).days
    else:
        total_dias = (fecha_fin - fecha_inicio)
        
    if intervalo_dias == 0:
        if tiempo == "HORA":
            intervalo_dias = total_dias / 10
        else:
            intervalo_dias = total_dias / 10

    # Limpiar el widget
    limpiar_widget(widget)
    config = SoftwareConfiguracion.obtenerDataSoftware()
    SUAVIZADO_ESTADO = True if config[20] == 1 else False
    titulozise, ejezise, etiquesize, leyendazise, cotasize = config[0], config[1], config[2], config[3], config[4]
    mostrarcota, vertices, lineatenden, grosortenden, colortenden = config[5], config[6], config[7], config[8], config[9]
    fuente, grosorlinea, grosorvertice, decimales = config[10], config[12], config[13], config[14]
    mostrarlluvia, posicionlluvia = config[17], config[18]

    # Ajustar el tamaño de la figura al tamaño del widget
    figure, ax = plt.subplots()
    canvas = FigureCanvas(figure)
    plt.rcParams['font.family'] = fuente
    layout = widget.layout()

    # --- INICIO MODIFICACIÓN PASO 2 ---
    toolbar_container = QWidget()
    widget.toolbar_container = toolbar_container
    toolbar_layout = QHBoxLayout(toolbar_container)
    toolbar_layout.setContentsMargins(0, 0, 0, 0)
    widget.toolbar = CustomToolbar(canvas, widget)
    toolbar_layout.addWidget(widget.toolbar)
    check_inspector = QCheckBox("Inspector de Datos")
    check_inspector.setStyleSheet("font-size: 12px; margin-left: 10px; font-weight: bold;")
    toolbar_layout.addWidget(check_inspector)
    check_ev_global = QCheckBox("Ev. Globales")
    check_ev_global.setChecked(True)
    check_ev_global.setStyleSheet("font-size: 11px; margin-left: 5px; color: #007bff; font-weight: bold;")
    toolbar_layout.addWidget(check_ev_global)
    check_ev_equipo = QCheckBox("Ev. Equipo")
    check_ev_equipo.setChecked(True)
    check_ev_equipo.setStyleSheet("font-size: 11px; margin-left: 3px; color: #28a745; font-weight: bold;")
    toolbar_layout.addWidget(check_ev_equipo)
    btn_add_evento = QPushButton("+ Evento")
    btn_add_evento.setCheckable(True) # Modo Toggle
    btn_add_evento.setStyleSheet("""
        QPushButton { font-size: 11px; padding: 4px; background-color: #f0f0f0; border: 1px solid #ccc; border-radius: 3px; }
        QPushButton:checked { background-color: #ffcccc; border: 1px solid red; color: red; font-weight: bold; }
    """)
    toolbar_layout.addWidget(btn_add_evento)
    canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    # El contenedor del toolbar solo ocupa lo que necesita
    toolbar_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    layout.addWidget(canvas)
    layout.addWidget(toolbar_container)

    # Configurar eje secundario si hay datos de pluviómetro
    barras_pluviometro = None
    if tiempo == "FECHA":
        if mostrarlluvia == 0:
            if pluviometro_data:
                idpluvio = str(pluviometro_data[0][0])
                estilo = ConfiguracionController.ctrlTraerEstiloEquipoGrafica(idproyecto, idpluvio, 0)
                df_pluviometro = pd.DataFrame(pluviometro_data, columns=['Codigo', 'Fecha', 'Lectura'])
                df_pluviometro['Fecha'] = pd.to_datetime(df_pluviometro['Fecha'])
                ax2 = ax.twinx()
                diferencia = df_pluviometro['Fecha'].max() - df_pluviometro['Fecha'].min()
                totaldias = diferencia.days
                ancho = 0.8
                if totaldias > 0:
                    if totaldias < 100:
                        ancho = totaldias / 100
                    else:
                        ancho = totaldias / 200
                if estilo:
                    if posicionlluvia == 0:
                        ax2.set_ylim(int(estilo[3]), 0)
                    else:
                        ax2.set_ylim(0, int(estilo[3]))
                    barras_pluviometro = ax2.bar(df_pluviometro['Fecha'], df_pluviometro['Lectura'], color=estilo[5], width=ancho, label="Precipitación")
                    ticks = np.arange(0, int(estilo[3]) + int(estilo[4]), int(estilo[4]))
                    ax2.set_yticks(ticks)
                else:
                    if posicionlluvia == 0:
                        ax2.set_ylim(100, 0)
                    else:
                        ax2.set_ylim(0, 100)
                    barras_pluviometro = ax2.bar(df_pluviometro['Fecha'], df_pluviometro['Lectura'], color='cyan', width=ancho, alpha=0.5, label="Precipitación")
                ax2.set_ylabel("Precipitacion (mm)", fontsize=ejezise)
            else:
                if modulo == "PIEZOMETROS":
                    ax2 = ax.twinx()
                    if posicionlluvia == 0:
                        ax2.set_ylim(100, 0)
                    else:
                        ax2.set_ylim(0, 100)
                    ax2.axhline(y=0, color='cyan', linestyle='-', linewidth=2, alpha=0.5)
                    ax2.set_ylabel("Precipitacion (mm)", fontsize=ejezise)
                    barras_pluviometro = mpatches.Patch(color='cyan', alpha=0.5)
        else:
            if pluviometro_data:
                idpluvio = str(pluviometro_data[0][0])
                estilo = ConfiguracionController.ctrlTraerEstiloEquipoGrafica(idproyecto, idpluvio, 0)
                df_pluviometro = pd.DataFrame(pluviometro_data, columns=['Codigo', 'Fecha', 'Lectura'])
                df_pluviometro['Fecha'] = pd.to_datetime(df_pluviometro['Fecha'])
                ax2 = ax.twinx()
                diferencia = df_pluviometro['Fecha'].max() - df_pluviometro['Fecha'].min()
                totaldias = diferencia.days
                ancho = 0.8
                if totaldias > 0:
                    if totaldias < 100:
                        ancho = totaldias / 100
                    else:
                        ancho = totaldias / 200
                if estilo:
                    if posicionlluvia == 0:
                        ax2.set_ylim(int(estilo[3]), 0)
                    else:
                        ax2.set_ylim(0, int(estilo[3]))
                    barras_pluviometro = ax2.bar(df_pluviometro['Fecha'], df_pluviometro['Lectura'], color=estilo[5], width=ancho, label="Precipitación")
                    ticks = np.arange(0, int(estilo[3]) + int(estilo[4]), int(estilo[4]))
                    ax2.set_yticks(ticks)
                else:
                    if posicionlluvia == 0:
                        ax2.set_ylim(100, 0)
                    else:
                        ax2.set_ylim(0, 100)
                    barras_pluviometro = ax2.bar(df_pluviometro['Fecha'], df_pluviometro['Lectura'], color='cyan', width=ancho, alpha=0.5, label="Precipitación")
                ax2.set_ylabel("Precipitacion (mm)", fontsize=ejezise)

    # Graficar datos
    lineas = []
    lblecuacion_rcuadrado = ""
    if data:
        for idinstrumento, datos_equipo in df.groupby('Instrumento'):
            nombreequipo = str(datos_equipo['Equipo'].iloc[0])
            estilo = ConfiguracionController.ctrlTraerEstiloEquipoGrafica(idproyecto, idinstrumento, 0)
            if estilo:
                if vertices == 1:
                    linea = plot_linea_suavizada(
                        ax, datos_equipo['Fecha'], datos_equipo[tipo], tiempo, activo=SUAVIZADO_ESTADO,
                        marker='o', markersize=estilo[4] + 4,
                        linestyle=estilo[3], linewidth=estilo[4],
                        color=estilo[5], label=nombreequipo
                    )
                else:
                    linea = plot_linea_suavizada(
                        ax, datos_equipo['Fecha'], datos_equipo[tipo], tiempo, activo=SUAVIZADO_ESTADO,
                        linestyle=estilo[3], linewidth=estilo[4],
                        color=estilo[5], label=nombreequipo
                    )
            else:
                if vertices == 1:
                    linea = plot_linea_suavizada(
                        ax, datos_equipo['Fecha'], datos_equipo[tipo], tiempo, activo=SUAVIZADO_ESTADO,
                        marker='o', label=nombreequipo
                    )
                else:
                    linea = plot_linea_suavizada(
                        ax, datos_equipo['Fecha'], datos_equipo[tipo], tiempo, activo=SUAVIZADO_ESTADO,
                        label=nombreequipo
                    )
            lineas.append(linea)

            # graficar cota piezometrica
            if tipo == "NF":
                for piezo, cotas in cotasmarcadas:
                    for cota in cotas:
                        if piezo[1] == str(idinstrumento):
                            if cota[0] != "":
                                if cota[0] == "Cota de Fundación":
                                    estilo = ConfiguracionController.ctrlTraerEstiloEquipoGrafica(idproyecto, idinstrumento, 1)
                                    if estilo:
                                        linea, = ax.plot(datos_equipo['Fecha'], datos_equipo["Fundacion"], linestyle=estilo[3], linewidth=estilo[4], color=estilo[5], label=f"Fundación {nombreequipo}")
                                    else:
                                        linea, = ax.plot(datos_equipo['Fecha'], datos_equipo["Fundacion"], label=f"Fundación {nombreequipo}")
                                    if mostrarcota == 1:
                                        fechauno = datos_equipo['Fecha'].iloc[0]
                                        if fechauno > fecha_inicio:
                                            fechacota = fechauno
                                        else:
                                            fechacota = fecha_inicio
                                        resultado = df.loc[df['Fecha'] == fechacota, 'Fundacion']
                                        valor_fundacion = resultado.iloc[0] if not resultado.empty else datos_equipo["Fundacion"].iloc[0]
                                        ax.text(fechacota, valor_fundacion, f"  Fundación {valor_fundacion} msnm", horizontalalignment='left', verticalalignment='bottom', fontsize=cotasize)
                                else:
                                    estilo = ConfiguracionController.ctrlTraerEstiloEquipoGrafica(idproyecto, idinstrumento, 2)
                                    if estilo:
                                        linea, = ax.plot(datos_equipo['Fecha'], datos_equipo["Superficie"], linestyle=estilo[3], linewidth=estilo[4], color=estilo[5], label=f"Superficie {nombreequipo}")
                                    else:
                                        linea, = ax.plot(datos_equipo['Fecha'], datos_equipo["Superficie"], label=f"Superficie {nombreequipo}")
                                    if mostrarcota == 1:
                                        fechauno = datos_equipo['Fecha'].iloc[0]
                                        if fechauno > fecha_inicio:
                                            fechacota = fechauno
                                        else:
                                            fechacota = fecha_inicio
                                        resultado = df.loc[df['Fecha'] == fechacota, 'Superficie']
                                        valor_superficie = resultado.iloc[0] if not resultado.empty else datos_equipo["Superficie"].iloc[0]
                                        ax.text(fechacota, valor_superficie, f"  Superficie {valor_superficie} msnm", horizontalalignment='left', verticalalignment='bottom', fontsize=cotasize)
                                lineas.append(linea)
            elif tipo == "AC":
                for piezo, cotas in cotasmarcadas:
                    for cota in cotas:
                        if piezo[1] == str(idinstrumento):
                            if cota[0] != "":
                                if cota[0] == "Cota de Fundación":
                                    estilo = ConfiguracionController.ctrlTraerEstiloEquipoGrafica(idproyecto, idinstrumento, 1)
                                    if estilo:
                                        linea, = ax.plot(datos_equipo['Fecha'], datos_equipo["Fundacion"], linestyle=estilo[3], linewidth=estilo[4], color=estilo[5], label=f"Fundación {nombreequipo}")
                                    else:
                                        linea, = ax.plot(datos_equipo['Fecha'], datos_equipo["Fundacion"], label=f"Fundación {nombreequipo}")
                                    if mostrarcota == 1:
                                        fechauno = datos_equipo['Fecha'].iloc[0]
                                        if fechauno > fecha_inicio:
                                            fechacota = fechauno
                                        else:
                                            fechacota = fecha_inicio
                                        resultado = df.loc[df['Fecha'] == fechacota, 'Fundacion']
                                        valor_fundacion = resultado.iloc[0] if not resultado.empty else datos_equipo["Fundacion"].iloc[0]
                                        ax.text(fechacota, valor_fundacion, f"  Fundación {valor_fundacion} msnm", horizontalalignment='left', verticalalignment='bottom', fontsize=cotasize)
                                else:
                                    estilo = ConfiguracionController.ctrlTraerEstiloEquipoGrafica(idproyecto, idinstrumento, 2)
                                    if estilo:
                                        linea, = ax.plot(datos_equipo['Fecha'], datos_equipo["Superficie"], linestyle=estilo[3], linewidth=estilo[4], color=estilo[5], label=f"Superficie {nombreequipo}")
                                    else:
                                        linea, = ax.plot(datos_equipo['Fecha'], datos_equipo["Superficie"], label=f"Superficie {nombreequipo}")
                                    if mostrarcota == 1:
                                        fechauno = datos_equipo['Fecha'].iloc[0]
                                        if fechauno > fecha_inicio:
                                            fechacota = fechauno
                                        else:
                                            fechacota = fecha_inicio
                                        resultado = df.loc[df['Fecha'] == fechacota, 'Superficie']
                                        valor_superficie = resultado.iloc[0] if not resultado.empty else datos_equipo["Superficie"].iloc[0]
                                        ax.text(fechacota, valor_superficie, f"  Superficie {valor_superficie} msnm", horizontalalignment='left', verticalalignment='bottom', fontsize=cotasize)
                                lineas.append(linea)

            # Graficar tendencias
            if equipostendencia:
                for instru, regresion, grado in equipostendencia:
                    if str(instru[0]) == str(idinstrumento):
                        if regresion == 'Lineal':
                            lineal = CalculosTendencias.dibujarTendenciaLineal(datos_equipo['Fecha'], datos_equipo[tipo], ax, tiempo, 1, nombreequipo, lineatenden, grosortenden, colortenden)
                            lineas.append(lineal)
                            ecualbl = CalculosTendencias.generarEcuacionTendencia(datos_equipo['Fecha'], datos_equipo[tipo], tiempo, 1)
                            lblecuacion_rcuadrado = lblecuacion_rcuadrado + nombreequipo + ':  ' + ecualbl + '\n'
                        elif regresion == 'Polinómica':
                            polino = CalculosTendencias.dibujarTendenciaLineal(datos_equipo['Fecha'], datos_equipo[tipo], ax, tiempo, grado, nombreequipo, lineatenden, grosortenden, colortenden)
                            lineas.append(polino)
                            ecualbl = CalculosTendencias.generarEcuacionTendencia(datos_equipo['Fecha'], datos_equipo[tipo], tiempo, grado)
                            lblecuacion_rcuadrado = lblecuacion_rcuadrado + nombreequipo + ':  ' + ecualbl + '\n'
                        elif regresion == 'Media Móvil':
                            media = CalculosTendencias.dibujarMediaMovil(datos_equipo['Fecha'], datos_equipo[tipo], ax, nombreequipo, grado, lineatenden, grosortenden, colortenden)
                            lineas.append(media)
                        elif regresion == 'Logarítmica':
                            logari, ecualbl = CalculosTendencias.dibujarTendenciaLogaritmica(datos_equipo['Fecha'], datos_equipo[tipo], ax, tiempo, nombreequipo, lineatenden, grosortenden, colortenden)
                            lineas.append(logari)
                            lblecuacion_rcuadrado = lblecuacion_rcuadrado + nombreequipo + ':  ' + ecualbl + '\n'
                        elif regresion == 'Exponencial':
                            exponen, ecualbl = CalculosTendencias.dibujarTendenciaExponencial(datos_equipo['Fecha'], datos_equipo[tipo], ax, tiempo, nombreequipo, lineatenden, grosortenden, colortenden)
                            if exponen:
                                lineas.append(exponen)
                                lblecuacion_rcuadrado = lblecuacion_rcuadrado + nombreequipo + ':  ' + ecualbl + '\n'
                        elif regresion == 'Potencial':
                            potenci, ecualbl = CalculosTendencias.dibujarTendenciaPotencial(datos_equipo['Fecha'], datos_equipo[tipo], ax, tiempo, nombreequipo, lineatenden, grosortenden, colortenden)
                            if potenci:
                                lineas.append(potenci)
                                lblecuacion_rcuadrado = lblecuacion_rcuadrado + nombreequipo + ':  ' + ecualbl + '\n'

    if tiempo != "FECHA":
        labeltendencia.setText(lblecuacion_rcuadrado)
    else:
        labeltendencia.setText("")

    if tipo == "NF":
        # graficar terrenos
        if dataterreno:
            df_terreno = pd.DataFrame(dataterreno, columns=['Codigo', 'Nombre', 'Fecha', 'Dias', 'Horas', 'Lectura'])
            if tiempo == "FECHA":
                df_terreno['Fecha'] = pd.to_datetime(df_terreno['Fecha'])
                tipoterre = "Fecha"
                if data is None:
                    df_terreno['Fecha'] = pd.to_datetime(df_terreno['Fecha'])
                    if fecha_inicio is None:
                        fecha_inicio = df_terreno['Fecha'].min()
                        fecha_fin = df_terreno['Fecha'].max()
                    fecha_inicio = pd.to_datetime(fecha_inicio)
                    fecha_fin = pd.to_datetime(fecha_fin)
            elif tiempo == "DIA":
                tipoterre = "Dias"
                if data is None:
                    if fecha_inicio is None:
                        fecha_inicio = df_terreno['Dias'].min()
                        fecha_fin = df_terreno['Dias'].max()
                    else:
                        val_min_tiempo = df_terreno['Dias'].min()
                        if isinstance(val_min_tiempo, str):
                            fechainiproyecto = datetime.strptime(val_min_tiempo, '%Y-%m-%d %H:%M:%S')
                        else:
                            fechainiproyecto = val_min_tiempo
                        unidtiempo = 1
                        difdiasini = fecha_inicio - fechainiproyecto
                        fecha_inicio = difdiasini.days * unidtiempo
                        difdiasfin = fecha_fin - fechainiproyecto
                        fecha_fin = difdiasfin.days * unidtiempo
            else:
                tipoterre = "Horas"
                if data is None:
                    if fecha_inicio is None:
                        fecha_inicio = df_terreno['Horas'].min()
                        fecha_fin = df_terreno['Horas'].max()
                    else:
                        val_min_tiempo = df_terreno['Horas'].min()
                        if isinstance(val_min_tiempo, str):
                            fechainiproyecto = datetime.strptime(val_min_tiempo, '%Y-%m-%d %H:%M:%S')
                        else:
                            fechainiproyecto = val_min_tiempo
                        unidtiempo = 24
                        difdiasini = fecha_inicio - fechainiproyecto
                        fecha_inicio = difdiasini.days * unidtiempo
                        difdiasfin = fecha_fin - fechainiproyecto
                        fecha_fin = difdiasfin.days * unidtiempo
            for idinstruterre, datos_terreno in df_terreno.groupby('Codigo'):
                nombreterre = str(datos_terreno['Nombre'].iloc[0])
                estilo = ConfiguracionController.ctrlTraerEstiloEquipoGrafica(idproyecto, idinstruterre, 0)
                if estilo:
                    linea, = ax.plot(datos_terreno[tipoterre], datos_terreno['Lectura'], linestyle=estilo[3], linewidth=estilo[4], color=estilo[5], label=nombreterre)
                else:
                    linea, = ax.plot(datos_terreno[tipoterre], datos_terreno['Lectura'], label=nombreterre)
                lineas.append(linea)

    # Configuración de ejes y etiquetas
    ax.set_title(titulo, fontsize=titulozise)
    ax.set_xlabel(labelejex, fontsize=ejezise)
    ax.set_ylabel(labelejey, fontsize=ejezise)
    if tiempo == "FECHA":
        ax.xaxis.set_major_formatter(DateFormatter('%d/%m/%Y'))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda val, pos: '{:.{}f}'.format(val, decimales)))
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)

    # Cálculo de etiquetas simétricas
    if tiempo == "FECHA":
        num_inicio = mdates.date2num(fecha_inicio)
        num_fin = mdates.date2num(fecha_fin)
        rango_total = num_fin - num_inicio
        intervalo_num = intervalo_dias 
    else:
        num_inicio = float(fecha_inicio)
        num_fin = float(fecha_fin)
        rango_total = num_fin - num_inicio
        intervalo_num = intervalo_dias

    if intervalo_num <= 0:
        num_etiquetas = 10
    else:
        num_etiquetas = int(rango_total / intervalo_num) + 1

    if num_etiquetas > 25: 
        avisolabels = True
        num_etiquetas = 15
    elif num_etiquetas < 2:
        num_etiquetas = 2

    etiquetas_numericas = np.linspace(num_inicio, num_fin, num_etiquetas)
    ax.set_xticks(etiquetas_numericas)
    ax.set_xlim([num_inicio, num_fin])
    
    plt.setp(ax.get_xticklabels(), rotation=90, ha="center", fontsize=etiquesize)
    plt.setp(ax.get_yticklabels(), fontsize=etiquesize)
    if mostrarlluvia == 0:
        if tiempo == "FECHA":
            if modulo == "PIEZOMETROS":
                plt.setp(ax2.get_yticklabels(), fontsize=etiquesize)
    else:
        if tiempo == "FECHA":
            if pluviometro_data:
                plt.setp(ax2.get_yticklabels(), fontsize=etiquesize)

    # CONFIGURAR EJE Y
    if ejeymin != 0 or ejeymax != 0:
        ax.set_ylim(ejeymin * medida, ejeymax * medida)
        maxejey = (ejeymax * medida) + 0.0001
        if ejeyprin > 0:
            tick_primarios = np.arange(ejeymin * medida, maxejey, ejeyprin * medida)
            if len(tick_primarios) > 1 and len(tick_primarios) < 100:
                ax.set_yticks(tick_primarios)
            else:
                avisolabels = True
        if ejeysecu > 0:
            tick_secundarios = np.arange(ejeymin * medida, maxejey, ejeysecu * medida)
            if len(tick_secundarios) > 1 and len(tick_secundarios) < 200:
                for tick in tick_secundarios:
                    ax.axhline(y=tick, color='gray', linestyle='--', linewidth=0.5)
            else:
                avisolabels = True
                
    # --- INICIALIZACIÓN HOVER ---
    annot = ax.annotate("", xy=(0,0), xytext=(15,15), textcoords="offset points",
                        bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#cccccc", lw=1, alpha=0.95),
                        arrowprops=dict(arrowstyle="-|>", connectionstyle="arc3,rad=0.2", color="#555555", lw=0.8))
    annot.set_visible(False)

    punto_resaltado, = ax.plot([], [], 'o', color='#dc3545', markersize=5, markeredgecolor='white', markeredgewidth=1, zorder=10)
    punto_resaltado.set_visible(False)
        # Marcador y etiqueta para modo evento
    marcador_evento, = ax.plot([], [], 'D', color='#ff4444', markersize=9,
                                markeredgecolor='white', markeredgewidth=1.5, zorder=11)
    marcador_evento.set_visible(False)

    label_evento = ax.annotate("", xy=(0, 0), xytext=(10, -20),
                                textcoords="offset points",
                                bbox=dict(boxstyle="round,pad=0.3", fc="#fff3cd",
                                          ec="#ffc107", lw=1, alpha=0.95),
                                fontsize=9, fontweight='bold', color='#856404',
                                annotation_clip=True)
    label_evento.set_visible(False)

    equipo_detectado = {'id': None, 'nombre': None}

    # =========================================================================
    # EVENTOS
    # =========================================================================
    linea_fantasma = ax.axvline(x=num_inicio, color='red', linestyle='--', linewidth=1.5, alpha=0.6)
    linea_fantasma.set_visible(False)

    instrumentos_dict = {}
    if data and not df.empty:
        for idinstrumento, datos_eq in df.groupby('Instrumento'):
            instrumentos_dict[str(idinstrumento)] = str(datos_eq['Equipo'].iloc[0])
    
    nombre_a_id = {v: k for k, v in instrumentos_dict.items()}

    ev_globales, ev_especificos = dibujar_eventos(ax, idproyecto, tipo_evento, instrumentos_dict, fecha_inicio, fecha_fin)
    objetos_eventos = ev_globales + ev_especificos
    
    def toggle_ev_global(checked):
        for obj in ev_globales:
            try: obj.set_visible(checked)
            except: pass
        canvas.draw_idle()
    
    def toggle_ev_equipo(checked):
        for obj in ev_especificos:
            try: obj.set_visible(checked)
            except: pass
        canvas.draw_idle()
    
    def on_toggle_add_evento(checked):
        if not checked:
            marcador_evento.set_visible(False)
            label_evento.set_visible(False)
            linea_fantasma.set_visible(False)
            canvas.draw_idle()
    
    check_ev_global.toggled.connect(toggle_ev_global)
    check_ev_equipo.toggled.connect(toggle_ev_equipo)
    btn_add_evento.toggled.connect(on_toggle_add_evento)
    # =========================================================================
    
    # Configuración de leyenda paginada
    def calculate_columns():
        font_config = {'family': fuente, 'size': leyendazise, 'weight': 'normal'}
        renderer = canvas.get_renderer()
        leyenda_labels = [line.get_label() for line in lineas] + (["Precipitación"] if barras_pluviometro else [])
        max_width = 0
        for label in leyenda_labels:
            text_obj = ax.text(0, 0, label, fontproperties=font_config)
            width = text_obj.get_window_extent(renderer).width + (leyendazise*3)
            max_width = max(max_width, width)
            text_obj.remove()
        ancho_pantalla = widget.width()
        return max(1, int((ancho_pantalla - 100) / (max_width + 50)))

    def actualizar_leyenda():
        try:
            ncols = calculate_columns()
            leyenda_elementos = lineas + ([barras_pluviometro] if barras_pluviometro else [])
            leyenda_labels = [line.get_label() for line in lineas] + (["Precipitación"] if barras_pluviometro else [])
            # --- TRUCO PARA MODO SUAVIZADO ---
            if SUAVIZADO_ESTADO:
                for line in lineas:
                    if hasattr(line, '_estilo_puro'):
                        line.set_linestyle(line._estilo_puro) # Mostrar estilo en leyenda
                        line.set_alpha(1.0)                   # Mostrar color en leyenda

            # Crear la leyenda con los estilos activados temporalmente
            legend = ax.legend(handles=leyenda_elementos, labels=leyenda_labels, 
                               loc='upper center', bbox_to_anchor=(0.5, 0), 
                               ncol=ncols, frameon=False, fontsize=leyendazise, 
                               borderaxespad=0.8)

            # --- RESTAURAR ESTADO INVISIBLE ---
            if SUAVIZADO_ESTADO:
                for line in lineas:
                    if hasattr(line, '_estilo_puro'):
                        line.set_linestyle('none') # Volver a ocultar en el gráfico
                        line.set_alpha(0)          # Volver a ocultar en el gráfico
            renderer = canvas.get_renderer()
            canvas.draw()
            fig_bbox = figure.bbox
            legend_bbox = legend.get_window_extent(renderer)
            legend_height = legend_bbox.height / fig_bbox.height
            padding = 0.08
            bottom_margin = 0.20 + legend_height + padding
            top_margin = 0.95 - (legend_height * 0.3)
            if bottom_margin >= top_margin:
                bottom_margin = 0.25
                top_margin = 0.90
                if ncols == 1:
                    bottom_margin = 0.35
                    top_margin = 0.85
            figure.subplots_adjust(bottom=bottom_margin, top=top_margin, left=0.1, right=0.90)
            canvas.draw()
            if figure.subplotpars.bottom >= figure.subplotpars.top:
                raise ValueError("Margen inválido, aplicando valores seguros")
            xlabel_bbox = ax.xaxis.label.get_window_extent(renderer=renderer)
            xlabel_bottom = xlabel_bbox.transformed(ax.transAxes.inverted()).y0
            legend.set_bbox_to_anchor((0.5, xlabel_bottom))
        except Exception as e:
            figure.subplots_adjust(bottom=0.25, top=0.90, left=0.1, right=0.90)
            ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=2, fontsize=8)
            canvas.draw()

    def on_resize(event):
        actualizar_leyenda()
        
    def procesar_datos_lectura_piezo_celda(id_proyecto, label, id_equipo, date, reading, tipo_piezo, modulo):
        date_obj = datetime.strptime(date, '%d/%m/%Y %H:%M:%S')
        formatted_date = date_obj.strftime('%Y-%m-%d %H:%M:%S')
        dialog = ModalDialog(widget, label, date, reading)
        result = dialog.exec()
        if result == QDialog.Accepted:
            respuesta = None
            if modulo == "PIEZOMETROS":
                respuesta = PiezometroController.ctrlOmitirLecturaPiezometro(id_proyecto, id_equipo, formatted_date, tipo_piezo)
                if respuesta:
                    print(f"{label}\nFecha: {formatted_date}\nLectura: {reading}\nTipo: {tipo_piezo}")
                else:
                    print('error al omitir lectura de piezometros')
            else:
                respuesta = CeldaController.ctrlOmitirLecturaCelda(id_proyecto, id_equipo, formatted_date)
                if respuesta:
                    print(f"{label}\nFecha: {formatted_date}\nLectura: {reading}\nTipo: {tipo_piezo}")
                else:
                    print('error al omitir de celdas')
                    
    def on_hover(event):
        if event.inaxes != ax:
            if annot.get_visible(): annot.set_visible(False)
            if punto_resaltado.get_visible(): punto_resaltado.set_visible(False)
            if linea_fantasma.get_visible(): linea_fantasma.set_visible(False)
            if marcador_evento.get_visible(): marcador_evento.set_visible(False)
            if label_evento.get_visible(): label_evento.set_visible(False)
            canvas.draw_idle()
            return

        if btn_add_evento.isChecked():
            annot.set_visible(False)
            punto_resaltado.set_visible(False)
            linea_fantasma.set_xdata([event.xdata])
            linea_fantasma.set_visible(True)
            
            min_dist = 40
            cercano = None
            xlim, ylim = ax.get_xlim(), ax.get_ylim()
            
            for line in lineas:
                if not line.get_visible():
                    continue
                x_data, y_data = line.get_data()
                if tiempo == "FECHA":
                    try:
                        if hasattr(x_data, 'dtype') and (x_data.dtype == 'object' or np.issubdtype(x_data.dtype, np.datetime64)):
                            x_data = mdates.date2num(x_data)
                    except:
                        continue
                mask = ((x_data >= xlim[0]) & (x_data <= xlim[1]) &
                        (y_data >= ylim[0]) & (y_data <= ylim[1]))
                if not np.any(mask):
                    continue
                puntos_px = ax.transData.transform(np.column_stack([x_data[mask], y_data[mask]]))
                mouse = np.array([event.x, event.y])
                dists = np.sqrt(np.sum((puntos_px - mouse) ** 2, axis=1))
                if len(dists) > 0:
                    idx = np.argmin(dists)
                    if dists[idx] < min_dist:
                        min_dist = dists[idx]
                        cercano = (x_data[mask][idx], y_data[mask][idx], line.get_label())
            
            if cercano:
                fx, fy, nombre = cercano
                marcador_evento.set_data([fx], [fy])
                marcador_evento.set_visible(True)
                label_evento.xy = (fx, fy)
                label_evento.set_text(nombre)
                label_evento.set_visible(True)
                equipo_detectado['id'] = nombre_a_id.get(nombre)
                equipo_detectado['nombre'] = nombre
            else:
                marcador_evento.set_visible(False)
                label_evento.set_visible(False)
                equipo_detectado['id'] = None
                equipo_detectado['nombre'] = None
            
            canvas.draw_idle()
            return

        # MODO: INSPECTOR
        linea_fantasma.set_visible(False)
        marcador_evento.set_visible(False)
        label_evento.set_visible(False)
        if not check_inspector.isChecked(): return

        min_distancia = 30
        punto_encontrado = None
        xlim, ylim = ax.get_xlim(), ax.get_ylim()

        for line in lineas:
            if not line.get_visible(): continue
            x_data, y_data = line.get_data()
            if tiempo == "FECHA":
                try:
                    if hasattr(x_data, 'dtype') and (x_data.dtype == 'object' or np.issubdtype(x_data.dtype, np.datetime64)):
                         x_data = mdates.date2num(x_data)
                except Exception: continue 
            
            mask = (x_data >= xlim[0]) & (x_data <= xlim[1]) & (y_data >= ylim[0]) & (y_data <= ylim[1])
            if not np.any(mask): continue
            
            puntos_pixel = ax.transData.transform(np.column_stack([x_data[mask], y_data[mask]]))
            mouse_pos = np.array([event.x, event.y])
            distancias = np.sqrt(np.sum((puntos_pixel - mouse_pos)**2, axis=1))
            
            if len(distancias) > 0:
                idx_min = np.argmin(distancias)
                if distancias[idx_min] < min_distancia:
                    min_distancia = distancias[idx_min]
                    punto_encontrado = (x_data[mask][idx_min], y_data[mask][idx_min], line.get_label())

        if punto_encontrado:
            fecha_num, lectura_val, label_equipo = punto_encontrado
            punto_resaltado.set_data([fecha_num], [lectura_val])
            punto_resaltado.set_visible(True)
            
            punto_pixel = ax.transData.transform((fecha_num, lectura_val))
            x_rel, y_rel = ax.transAxes.inverted().transform(punto_pixel)
            
            offset_x, offset_y = 15, 15
            ha, va = 'left', 'bottom'
            if y_rel > 0.70: va, offset_y = 'top', -15
            if x_rel > 0.65: ha, offset_x = 'right', -15

            annot.xy = (fecha_num, lectura_val)
            annot.xytext = (offset_x, offset_y)
            annot.set_ha(ha)
            annot.set_va(va)
            
            str_fecha = mdates.num2date(fecha_num).replace(tzinfo=None).strftime('%d/%m/%Y %H:%M') if tiempo == "FECHA" else f"{fecha_num:.2f}"
            annot.set_text(f"{label_equipo}\nFecha: {str_fecha}\nLectura: {lectura_val:.3f}")
            annot.set_fontsize(9)
            annot.set_color('#333333')
            annot.set_visible(True)
            annot.set_zorder(999)
            canvas.draw_idle()
        else:
            if annot.get_visible():
                annot.set_visible(False)
                punto_resaltado.set_visible(False)
                canvas.draw_idle()
    
    def on_click(event):
        if event.button != 1: return

        # =====================================================================
        # CASO A: CREAR EVENTO
        # =====================================================================
        if btn_add_evento.isChecked():
            if event.inaxes == ax:
                fecha_clic = mdates.num2date(event.xdata).replace(tzinfo=None)
                
                eq_id = equipo_detectado.get('id')
                eq_nombre = equipo_detectado.get('nombre')
                
                dialog = EventosDialog(widget, fecha_clic, idproyecto, tipo_evento, eq_id, eq_nombre)
                if dialog.exec():
                    datos = dialog.obtener_datos()
                    exito = EventosController.ctrlCrearEvento(
                        idproyecto, datos['fecha'], datos['descripcion'], datos['color'],
                        datos['alcance'], tipo_evento, datos['id_instrumento']
                    )
                    
                    if exito:
                        fecha_num_click = mdates.date2num(datos['fecha'])
                        nueva_linea = ax.axvline(x=datos['fecha'], color=datos['color'],
                                                  linestyle='--', linewidth=1.5, alpha=0.7)
                        
                        desc_full = datos['descripcion']
                        texto_safe = (desc_full[:20] + '..') if len(desc_full) > 20 else desc_full
                        
                        nuevo_texto = ax.annotate(
                            texto_safe,
                            xy=(fecha_num_click, 0.96),
                            xycoords=ax.get_xaxis_transform(),
                            xytext=(4, 0), textcoords='offset points',
                            rotation=90, va='top', ha='left',
                            color=datos['color'], fontsize=7, fontweight='bold',
                            annotation_clip=True, clip_on=True
                        )
                        
                        if datos['alcance'] == 'GLOBAL':
                            ev_globales.extend([nueva_linea, nuevo_texto])
                        else:
                            ev_especificos.extend([nueva_linea, nuevo_texto])
                        objetos_eventos.extend([nueva_linea, nuevo_texto])
                        
                        canvas.draw()
                        btn_add_evento.setChecked(False)
                        mostrar_mensaje("Éxito", "Evento agregado.", "info")
                    else:
                        mostrar_mensaje("Error", "No se pudo guardar el evento.", "error")
                
                marcador_evento.set_visible(False)
                label_evento.set_visible(False)
                linea_fantasma.set_visible(False)
                canvas.draw_idle()
            return
        # =====================================================================

        # CASO B: LÓGICA ORIGINAL (Seleccionar / Omitir)
        current_ax = ax2 if ax2 and ax2.in_axes(event) else ax

        if current_ax.in_axes(event):
            for line in lineas:
                contains, _ = line.contains(event)
                if contains:
                    label = line.get_label()
                    x = mdates.num2date(event.xdata).replace(tzinfo=None)
                    y = event.ydata

                    line_data = df[df['Equipo'] == label]

                    if not line_data.empty:
                        if line_data['Fecha'].dt.tz is not None:
                            line_data['Fecha'] = line_data['Fecha'].dt.tz_localize(None)

                        data_point = line_data.iloc[(line_data['Fecha'] - x).abs().argmin()]
                        date = data_point['Fecha'].strftime('%d/%m/%Y %H:%M:%S')
                        reading = round(data_point[tipo], 3)
                        tipo_piezo = data_point['TipoPiezo']
                        id_equipo = data_point['idEquipo']
                        annotation_text = f"{label}\nFecha: {date}\nLectura: {reading}"

                        if event.guiEvent.modifiers() & Qt.ControlModifier:
                            procesar_datos_lectura_piezo_celda(idproyecto, label, id_equipo, date, reading, tipo_piezo, modulo)
                        else:
                            fecha_num_data = mdates.date2num(data_point['Fecha'])
                            annotation = current_ax.annotate(annotation_text, (fecha_num_data, data_point[tipo]),
                                                            textcoords="offset points", xytext=(10, 10),
                                                            ha='left', fontsize=etiquesize,
                                                            bbox=dict(facecolor='yellow', alpha=0.8, edgecolor='none'))
                            annotation.set_visible(True)
                            canvas.draw()
                        return

        # Limpiar etiquetas
        if not (event.guiEvent.modifiers() & Qt.ControlModifier):
            for text in current_ax.texts:
                if text not in objetos_eventos:
                    text.set_visible(False)
            canvas.draw()

    canvas.mpl_connect('resize_event', on_resize)
    canvas.mpl_connect('button_press_event', on_click)
    canvas.mpl_connect('motion_notify_event', on_hover)
    actualizar_leyenda()
    plt.close(figure)
    if avisolabels:
        mostrar_mensaje("Ejes", "No se aplicó la configuración de ejes.", "advertencia")

def procesar_grafica_analisis(widget, data, idx_nombre, idx_fecha, idx_lectura, labelejex, labelejey, titulo, tiempo, tipo, idproyecto, fecha_inicio=None, fecha_fin=None):
    avisolabels = False
    
    # --- CORRECCIÓN SQL SERVER: Validar tipo de dato antes de convertir ---
    if tiempo == "FECHA":
        if fecha_inicio:
            if isinstance(fecha_inicio, str):
                fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d %H:%M:%S')
        if fecha_fin:
            if isinstance(fecha_fin, str):
                fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d %H:%M:%S')
    # ----------------------------------------------------------------------
    
    # Convertir fechas a datetime y asignar valores por defecto
    df = pd.DataFrame(data, columns=['col_' + str(i) for i in range(len(data[0]))])
    df = df[[df.columns[0], df.columns[idx_nombre], df.columns[idx_fecha], df.columns[idx_lectura]]]
    df.columns = ['Instrumento', 'Nombre', 'Fecha', tipo]
    # validar formato filtrado
    if tiempo == "FECHA":
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        if fecha_inicio is None:
            fecha_inicio = df['Fecha'].min()
            fecha_fin = df['Fecha'].max()
        fecha_inicio = pd.to_datetime(fecha_inicio)
        fecha_fin = pd.to_datetime(fecha_fin)
    else:
        fecha_inicio = df['Fecha'].min()
        fecha_fin = df['Fecha'].max()
    # Ajustar limites de gráficas eje y
    ejeymin, ejeymax, ejeyprin, ejeysecu, intervalo_dias = 0, 0, 0, 0, 0
    dataeje = ConfiguracionController.ctrlObtenerConfiguracionEje(idproyecto, "ANALISIS", tipo)
    if dataeje:
        ejeymin, ejeymax, ejeyprin, ejeysecu = dataeje[4], dataeje[5], dataeje[6], dataeje[7]
        intervalo_dias = dataeje[8]
    if tiempo == "FECHA":
        total_dias = (fecha_fin - fecha_inicio).days
    else:
        total_dias = (fecha_fin - fecha_inicio)
    if intervalo_dias == 0:
        intervalo_dias = total_dias / 10
    # Limpiar el widget
    limpiar_widget(widget)
    # crear figura
    config = SoftwareConfiguracion.obtenerDataSoftware()
    SUAVIZADO_ESTADO = True if config[20] == 1 else False
    titulozise, ejezise, etiquesize, leyendazise = config[0], config[1], config[2], config[3]
    vertices, fuente, grosorlinea, grosorvertice, decimales = config[6], config[10], config[12], config[13], config[14]
    
    figure, ax = plt.subplots()
    canvas = FigureCanvas(figure)
    plt.rcParams['font.family'] = fuente
    layout = widget.layout()

    # --- INICIO MODIFICACIÓN PASO 2 ---
    toolbar_container = QWidget()
    widget.toolbar_container = toolbar_container
    toolbar_layout = QHBoxLayout(toolbar_container)
    toolbar_layout.setContentsMargins(0, 0, 0, 0)
    widget.toolbar = CustomToolbar(canvas, widget)
    toolbar_layout.addWidget(widget.toolbar)
    check_inspector = QCheckBox("Inspector de Datos")
    check_inspector.setStyleSheet("font-size: 12px; margin-left: 10px; font-weight: bold;")
    toolbar_layout.addWidget(check_inspector)
    canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    # El contenedor del toolbar solo ocupa lo que necesita
    toolbar_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    layout.addWidget(canvas)
    layout.addWidget(toolbar_container)

    # Graficar datos de desplazamiento
    lineas = []
    if tiempo != "FECHA":
        punto_inicial = ax.scatter([], [], color='black', label='Punto Inicial', zorder=11, s=50, edgecolors='white', linewidths=0.6)
        punto_final = ax.scatter([], [], color='red', label='Punto Final', zorder=11, s=50, edgecolors='white', linewidths=0.6)
        lineas.append(punto_inicial)
        lineas.append(punto_final)
    for idinstrumento, datos_equipo in df.groupby('Instrumento'):
        nombreequipo = str(datos_equipo['Nombre'].iloc[0])
        # Graficar todos los puntos intermedios en azul
        estilo = ConfiguracionController.ctrlTraerEstiloEquipoGrafica(idproyecto, idinstrumento, 0)
        if estilo:
            if vertices == 1:
                linea = plot_linea_suavizada(
                    ax, datos_equipo['Fecha'], datos_equipo[tipo], tiempo, activo=SUAVIZADO_ESTADO,
                    marker='o', markersize=estilo[4] + 4,
                    linestyle=estilo[3], linewidth=estilo[4],
                    color=estilo[5], label=nombreequipo
                )
            else:
                linea = plot_linea_suavizada(
                    ax, datos_equipo['Fecha'], datos_equipo[tipo], tiempo, activo=SUAVIZADO_ESTADO,
                    linestyle=estilo[3], linewidth=estilo[4],
                    color=estilo[5], label=nombreequipo
                )
        else:
            if vertices == 1:
                linea = plot_linea_suavizada(
                    ax, datos_equipo['Fecha'], datos_equipo[tipo], tiempo, activo=SUAVIZADO_ESTADO,
                    marker='o', markersize=grosorvertice,
                    linewidth=grosorlinea, linestyle='-',
                    label=nombreequipo
                )
            else:
                linea = plot_linea_suavizada(
                    ax, datos_equipo['Fecha'], datos_equipo[tipo], tiempo, activo=SUAVIZADO_ESTADO,
                    linewidth=grosorlinea, linestyle='-',
                    label=nombreequipo
                )
        lineas.append(linea)
        # Resaltar el primer y Punto Final
        if tiempo != "FECHA":
            ax.scatter([datos_equipo['Fecha'].iloc[0]], [datos_equipo[tipo].iloc[0]], color='black', label='Punto Inicial', zorder=11, s=50,
                    edgecolors='white', linewidths=0.6)
            ax.scatter([datos_equipo['Fecha'].iloc[-1]], [datos_equipo[tipo].iloc[-1]], color='red', label='Punto Final', zorder=11, s=50,
                    edgecolors='white', linewidths=0.6)
    # Configuración de ejes y etiquetas
    ax.set_title(titulo, fontsize=titulozise)
    ax.set_xlabel(labelejex, fontsize=ejezise)
    ax.set_ylabel(labelejey, fontsize=ejezise)
    if tiempo == "FECHA":
        ax.xaxis.set_major_formatter(DateFormatter('%d/%m/%Y'))
    if tipo == "VEN":
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda val, pos: '{:.{}f}'.format(val, decimales)))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda val, pos: '{:.{}f}'.format(val, decimales)))
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)

    # -----------------------------------------------------------------------------
    # MEJORA VISUAL: CÁLCULO DE ETIQUETAS SIMÉTRICAS (ANÁLISIS)
    # -----------------------------------------------------------------------------
    if tiempo == "FECHA":
        num_inicio = mdates.date2num(fecha_inicio)
        num_fin = mdates.date2num(fecha_fin)
        rango_total = num_fin - num_inicio
        intervalo_num = intervalo_dias
    else:
        num_inicio = float(fecha_inicio)
        num_fin = float(fecha_fin)
        rango_total = num_fin - num_inicio
        intervalo_num = intervalo_dias

    if intervalo_num <= 0:
        num_etiquetas = 10
    else:
        num_etiquetas = int(rango_total / intervalo_num) + 1

    if num_etiquetas > 25:
        avisolabels = True
        num_etiquetas = 15
    elif num_etiquetas < 2:
        num_etiquetas = 2

    etiquetas_numericas = np.linspace(num_inicio, num_fin, num_etiquetas)
    ax.set_xticks(etiquetas_numericas)
    ax.set_xlim([num_inicio, num_fin])
    # -----------------------------------------------------------------------------

    # ajustar las etiquetas
    plt.setp(ax.get_xticklabels(), rotation=90, ha="center", fontsize=etiquesize)
    plt.setp(ax.get_yticklabels(), fontsize=etiquesize)
    # CONFIGURAR EJE Y
    if ejeymin != 0 or ejeymax != 0:
        ax.set_ylim(ejeymin, ejeymax)
        # Calcula los intervalos primarios
        maxejey = ejeymax + 0.0001
        if ejeyprin > 0:
            tick_primarios = np.arange(ejeymin, maxejey, ejeyprin)
            if len(tick_primarios) > 1 and len(tick_primarios) < 100:
                ax.set_yticks(tick_primarios)
            else:
                avisolabels = True
        # Calcula los intervalos secundarios
        if ejeysecu > 0:
            tick_secundarios = np.arange(ejeymin, maxejey, ejeysecu)
            if len(tick_secundarios) > 1 and len(tick_secundarios) < 200:
                for tick in tick_secundarios:
                    ax.axhline(y=tick, color='gray', linestyle='--', linewidth=0.5)
            else:
                avisolabels = True
    # --- INICIALIZACIÓN HOVER ANALISIS ---
    annot = ax.annotate("", xy=(0,0), xytext=(15,15), textcoords="offset points",
                        bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#cccccc", lw=1, alpha=0.95),
                        arrowprops=dict(arrowstyle="-|>", connectionstyle="arc3,rad=0.2", color="#555555", lw=0.8))
    annot.set_visible(False)
    # Nota: En análisis a veces usas scatter, pero un plot vacío funciona para el punto resaltado
    punto_resaltado, = ax.plot([], [], 'o', color='#dc3545', markersize=5, markeredgecolor='white', markeredgewidth=1, zorder=10)
    punto_resaltado.set_visible(False)
    # -------------------------------------
    
    # Configuración de leyenda paginada
    def calculate_columns():
        font_config = {'family': fuente, 'size': leyendazise, 'weight': 'normal'}
        renderer = canvas.get_renderer()
        # Obtener los manejadores y etiquetas de la leyenda
        leyenda_labels = [line.get_label() for line in lineas]
        # Calcular el ancho máximo de las etiquetas
        max_width = 0
        for label in leyenda_labels:
            text_obj = ax.text(0, 0, label, fontproperties=font_config)
            width = text_obj.get_window_extent(renderer).width +(leyendazise*3)
            max_width = max(max_width, width)
            text_obj.remove()  # Eliminar el objeto de texto para no mostrarlo en el gráfico

        ancho_pantalla = widget.width()

        return max(1, int((ancho_pantalla - 100) / (max_width + 50)))
    
    def actualizar_leyenda():
        try:
            ncols = calculate_columns()
            leyenda_labels = [line.get_label() for line in lineas]
            # --- ACTIVAR VISIBILIDAD SOLO EN LÍNEAS SUAVIZADAS ---
            if SUAVIZADO_ESTADO:
                for item in lineas:
                    # Solo aplicamos a líneas que vienen de plot_linea_suavizada
                    if hasattr(item, '_estilo_puro'):
                        item.set_linestyle(item._estilo_puro)
                        item.set_alpha(1.0)

            # Crear la leyenda
            legend = ax.legend(handles=lineas, labels=leyenda_labels, 
                               loc='upper center', bbox_to_anchor=(0.5, 0), 
                               ncol=ncols, frameon=False, fontsize=leyendazise, 
                               borderaxespad=0.8)

            # --- VOLVER A OCULTAR ---
            if SUAVIZADO_ESTADO:
                for item in lineas:
                    if hasattr(item, '_estilo_puro'):
                        item.set_linestyle('none')
                        item.set_alpha(0)

            renderer = canvas.get_renderer()
            canvas.draw()
            fig_bbox = figure.bbox
            legend_bbox = legend.get_window_extent(renderer)
            legend_height = legend_bbox.height / fig_bbox.height
            padding = 0.08
            bottom_margin = 0.20 + legend_height + padding
            top_margin = 0.95 - (legend_height * 0.3)

            if bottom_margin >= top_margin:
                bottom_margin = 0.25
                top_margin = 0.90
                if ncols == 1:
                    bottom_margin = 0.35
                    top_margin = 0.85

            figure.subplots_adjust(bottom=bottom_margin, top=top_margin, left=0.15, right=0.90)
            canvas.draw()
            if figure.subplotpars.bottom >= figure.subplotpars.top:
                raise ValueError("Margen inválido, aplicando valores seguros")
            xlabel_bbox = ax.xaxis.label.get_window_extent(renderer=renderer)
            xlabel_bottom = xlabel_bbox.transformed(ax.transAxes.inverted()).y0
            legend.set_bbox_to_anchor((0.5, xlabel_bottom))
        except Exception as e:
            figure.subplots_adjust(bottom=0.25, top=0.90, left=0.15, right=0.90)
            ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=2, fontsize=8)
            canvas.draw()

    def on_resize(event):
        actualizar_leyenda()
    
    def on_hover(event):
        # 1. Validaciones
        if not check_inspector.isChecked() or event.inaxes != ax:
            if annot.get_visible():
                annot.set_visible(False)
                punto_resaltado.set_visible(False)
                canvas.draw_idle()
            return

        # 2. Configuración de búsqueda
        min_distancia = 30 # Radio de captura (píxeles) más preciso
        punto_encontrado = None
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()

        # 3. Búsqueda del punto más cercano
        for line in lineas:
            # Ignorar líneas que no son datos (como líneas de tendencia si no se desean, o bordes)
            if not line.get_visible(): continue

            x_data, y_data = line.get_data()
            
            # Conversión segura de fechas
            if tiempo == "FECHA":
                try:
                    if hasattr(x_data, 'dtype') and (x_data.dtype == 'object' or np.issubdtype(x_data.dtype, np.datetime64)):
                         x_data = mdates.date2num(x_data)
                except Exception:
                    continue 

            # Filtrar solo puntos visibles en el zoom actual (Optimización)
            mask = (x_data >= xlim[0]) & (x_data <= xlim[1]) & (y_data >= ylim[0]) & (y_data <= ylim[1])
            if not np.any(mask): continue
            
            x_visibles = x_data[mask]
            y_visibles = y_data[mask]
            
            # Transformar a píxeles
            puntos_pixel = ax.transData.transform(np.column_stack([x_visibles, y_visibles]))
            mouse_pos = np.array([event.x, event.y])
            
            distancias = np.sqrt(np.sum((puntos_pixel - mouse_pos)**2, axis=1))
            if len(distancias) == 0: continue

            idx_min = np.argmin(distancias)
            dist_actual = distancias[idx_min]
            
            if dist_actual < min_distancia:
                min_distancia = dist_actual
                punto_encontrado = (x_visibles[idx_min], y_visibles[idx_min], line.get_label())

        # 4. Mostrar anotación si se encontró punto
        if punto_encontrado:
            fecha_num, lectura_val, label_equipo = punto_encontrado
            
            # Posicionar punto resaltado
            punto_resaltado.set_data([fecha_num], [lectura_val])
            punto_resaltado.set_visible(True)
            
            # Posicionamiento inteligente del cuadro
            punto_pixel = ax.transData.transform((fecha_num, lectura_val))
            punto_relativo = ax.transAxes.inverted().transform(punto_pixel)
            x_rel, y_rel = punto_relativo

            offset_x = 15
            offset_y = 15
            ha = 'left'
            va = 'bottom'

            if y_rel > 0.70:
                va = 'top'
                offset_y = -15
            if x_rel > 0.65:
                ha = 'right'
                offset_x = -15

            annot.xy = (fecha_num, lectura_val)
            annot.xytext = (offset_x, offset_y) 
            annot.set_ha(ha)
            annot.set_va(va)
            
            # Formato de Texto Profesional
            if tiempo == "FECHA":
                fecha_obj = mdates.num2date(fecha_num).replace(tzinfo=None)
                str_fecha = fecha_obj.strftime('%d/%m/%Y %H:%M') # Sin segundos para limpieza visual
            else:
                str_fecha = f"{fecha_num:.2f}"
            
            # Uso de HTML-like styling (limitado en mpl) o formato limpio
            # Texto oscuro (#333) sobre fondo blanco para legibilidad
            text = f"{label_equipo}\nFecha: {str_fecha}\nLectura: {lectura_val:.3f}"
            annot.set_text(text)
            
            # Estilo de fuente
            annot.set_fontsize(9)
            annot.set_color('#333333')
            
            annot.set_visible(True)
            annot.set_zorder(999)
            canvas.draw_idle()
        
        else:
            if annot.get_visible():
                annot.set_visible(False)
                punto_resaltado.set_visible(False)
                canvas.draw_idle()
                    
    canvas.mpl_connect('resize_event', on_resize)
    canvas.mpl_connect('motion_notify_event', on_hover)
    actualizar_leyenda()
    plt.close(figure)
    if avisolabels:
        mostrar_mensaje("Ejes", "No se aplicó la configuración de ejes.", "advertencia")

def procesar_grafica_histograma(widget, data, intervalos, nombreequipo, idx_lectura, labelejex, labelejey, titulo):
    # Convertir fechas a datetime y asignar valores por defecto
    df = pd.DataFrame(data, columns=['col_' + str(i) for i in range(len(data[0]))])
    df = df[[df.columns[idx_lectura]]]
    df.columns = ['Lectura']
    # Limpiar el widget
    limpiar_widget(widget)
    config = SoftwareConfiguracion.obtenerDataSoftware()
    titulozise, ejezise, etiquesize, leyendazise, fuente = config[0], config[1], config[2], config[3], config[10]
    # crear figura
    figure, ax = plt.subplots()
    canvas = FigureCanvas(figure)
    plt.rcParams['font.family'] = fuente
    layout = widget.layout()
    layout.addWidget(canvas)
    toolbar_layout = QHBoxLayout()
    widget.toolbar = CustomToolbar(canvas, widget)
    toolbar_layout.addWidget(widget.toolbar)
    layout.addLayout(toolbar_layout)
    # Graficar datos de desplazamiento
    ax.hist(df['Lectura'], bins=intervalos, edgecolor='black', alpha=0.5, label=nombreequipo)
    # Configuración de ejes y etiquetas
    ax.set_title(titulo, fontsize=titulozise)
    ax.set_xlabel(labelejex, fontsize=ejezise)
    ax.set_ylabel(labelejey, fontsize=ejezise)
    ax.grid(False)
    # validar las etiquetas
    plt.setp(ax.get_xticklabels(), fontsize=etiquesize)
    plt.setp(ax.get_yticklabels(), fontsize=etiquesize)
    # Configuración de leyenda
    ax.legend(fontsize=leyendazise)
    #ax.legend(loc='upper center', bbox_to_anchor=(1, 0.5), prop={'size': leyendazise})
    figure.subplots_adjust(left=0.08, right=0.95, top=0.95, bottom=0.25)
    canvas.draw_idle()
    plt.close(figure)