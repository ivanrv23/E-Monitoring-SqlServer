import pandas as pd
import matplotlib.pyplot as plt
import gc
import math
import numpy as np
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QCheckBox
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from utils.common.customToolbar import CustomToolbar
from utils.common.alertas import mostrar_mensaje
from modules.empresa.softwareconfiguracion import SoftwareConfiguracion
from controllers.ConfiguracionController import ConfiguracionController

class GraficarImpedancia:
    
    def limpiar_widget(widget):
        # Configurar el layout y limpiar el anterior
        if widget.layout() is None:
            layout = QVBoxLayout(widget)
            widget.setLayout(layout)
        else:
            layout = widget.layout()
            while layout.count():
                item = layout.takeAt(0)
                widget_to_remove = item.widget()
                if widget_to_remove is not None:
                    widget_to_remove.deleteLater()
                else:
                    layout.removeItem(item)

        # Eliminar toolbar anterior si existe en el layout
        if hasattr(widget, "toolbar") and widget.toolbar is not None:
            widget.toolbar.deleteLater()
            widget.toolbar = None

        # Eliminar botones anteriores si existen
        if hasattr(widget, "boton_siguiente") and widget.boton_siguiente is not None:
            widget.boton_siguiente.deleteLater()
            widget.boton_siguiente = None
        if hasattr(widget, "boton_anterior") and widget.boton_anterior is not None:
            widget.boton_anterior.deleteLater()
            widget.boton_anterior = None
        # limpiar memoria
        gc.collect()
    
    def graficarImpedanciaTDR(idproyecto, widget, data, fallas, tipo_grafico, unidadmedida):
        avisolabels = False
        # Convertir datos a DataFrame
        df = pd.DataFrame(data, columns=['col_' + str(i) for i in range(len(data[0]))])
        df = df[['col_0', 'col_1', 'col_2', 'col_3', 'col_4']]
        df.columns = ['Nombre', 'Fecha_Base', 'Fecha_Lectura', 'Profundidad', 'Impedancia']
        df['Fecha_Lectura'] = pd.to_datetime(df['Fecha_Lectura'])
        df['Fecha_Base'] = pd.to_datetime(df['Fecha_Base'])

        # Filtrar la data donde Fecha_Base == Fecha_Lectura
        data_filtrada = df[df['Fecha_Base'] == df['Fecha_Lectura']]

        # Limpiar el widget
        GraficarImpedancia.limpiar_widget(widget)

        # Configuración de la gráfica
        config = SoftwareConfiguracion.obtenerDataSoftware()
        titulozise, ejezise, etiquesize, leyendazise, vertices = config[0], config[1], config[2], config[3], config[6]
        fuente, grosorlinea, grosorvertice, decimales = config[10], config[12], config[13], config[14]
        # AJUSTAR tamaños
        widget_width = max(4, widget.width() / 100)
        widget_height = max(3, widget.height() / 100)
        figure = plt.Figure(figsize=(widget_width, widget_height), tight_layout=True)
        canvas = FigureCanvas(figure)
        plt.rcParams['font.family'] = fuente
        ax = figure.add_subplot(111)
        layout = widget.layout()
        layout.addWidget(canvas)
        toolbar_layout = QHBoxLayout()
        widget.toolbar = CustomToolbar(canvas, widget)
        toolbar_layout.addWidget(widget.toolbar)
        layout.addLayout(toolbar_layout)

        check_inspector = QCheckBox("Inspector de Datos")
        check_inspector.setStyleSheet("font-size: 12px; margin-left: 10px; font-weight: bold;")
        toolbar_layout.addWidget(check_inspector)

        # Agrupar por fecha de lectura y tipo de gráfico
        profundidad = data_filtrada['Profundidad']
        impedancia = data_filtrada['Impedancia']
        
        # Variables de control
        es_grafico_IP = False 

        if tipo_grafico == 'PI':
            valores_x = 'Profundidad'
            valores_y = 'Impedancia'
            if unidadmedida == 1:
                x_label = 'Profundidad (m)'
                tipomedida = "m"
            elif unidadmedida == 100:
                x_label = 'Profundidad (cm)'
                tipomedida = "cm"
            else:
                x_label = 'Profundidad (mm)'
                tipomedida = "mm"
            y_label = 'Impedancia (Ω)'
            title = 'Profundidad/Impedancia'
            leyenda_posicion = 'upper center'
            ajuste_margenes = {'left': 0.08, 'right': 0.95, 'top': 0.95, 'bottom': 0.15}
            leyenda_ncol = 6
            # Obtener la posición del eje x en coordenadas de la figura
            xlabel_bbox = ax.xaxis.label.get_window_extent(renderer=canvas.get_renderer())
            xlabel_bottom = xlabel_bbox.transformed(ax.transAxes.inverted()).y1
            # Ajustar la posición de la leyenda justo debajo del eje x
            leyenda_bbox = (0.5, -0.15)  

        elif tipo_grafico == 'IP':
            es_grafico_IP = True
            valores_x = 'Impedancia'
            valores_y = 'Profundidad'
            x_label = 'Impedancia (Ω)'
            if unidadmedida == 1:
                y_label = 'Profundidad (m)'
                tipomedida = "m"
            elif unidadmedida == 100:
                y_label = 'Profundidad (cm)'
                tipomedida = "cm"
            else:
                y_label = 'Profundidad (mm)'
                tipomedida = "mm"
            title = 'Impedancia/Profundidad'
            leyenda_posicion = 'center left'
            leyenda_bbox = (1.0, 0.5)
            ajuste_margenes = {'left': 0.31, 'right': 0.75, 'top': 0.95, 'bottom': 0.1}
            leyenda_ncol = 1
            # Invertir el eje Y para que la profundidad comience desde arriba (por defecto sin limites manuales)
            ax.invert_yaxis()
        else:
            raise ValueError("Tipo de gráfico no válido. Debe ser 'IP' o 'PI'.")
        
        # Graficar datos
        lineas = []
        for fecha_lectura, datos_grupo in df.groupby('Fecha_Lectura'):
            datos_grupo = datos_grupo.sort_values(by='Profundidad')
            if vertices == 1:
                linea, = ax.plot(datos_grupo[valores_x], datos_grupo[valores_y], label=f'{fecha_lectura.date()}', marker='o', markersize=grosorvertice, linewidth=grosorlinea)
            else:
                linea, = ax.plot(datos_grupo[valores_x], datos_grupo[valores_y], label=f'{fecha_lectura.date()}', linewidth=grosorlinea)
            lineas.append(linea)
        
        # Graficar fallas
        if len(fallas) > 0:
            if data_filtrada.empty is False:
                for falla in fallas:
                    profundidad = falla[3] * unidadmedida
                    color = falla[4]
                    nombre = falla[2]
                    # Buscar la impedancia correspondiente a la profundidad de la falla
                    if valores_x == 'Profundidad':
                        # Lógica para PI
                        impedancia_val = data_filtrada.loc[data_filtrada['Profundidad'] == profundidad, 'Impedancia']
                        if not impedancia_val.empty:
                            impedancia = impedancia_val.values[0]
                            punto = ax.scatter(profundidad, impedancia, color=color, label=f'Falla {nombre}: {profundidad} {tipomedida}', marker='o', edgecolors='black', s=30, zorder=5)
                            lineas.append(punto)
                    else:
                        # Lógica para IP
                        impedancia_val = data_filtrada.loc[data_filtrada['Profundidad'] == profundidad, 'Impedancia']
                        if not impedancia_val.empty:
                            impedancia = impedancia_val.values[0]
                            punto = ax.scatter(impedancia, profundidad, color=color, label=f'Falla {nombre}: {profundidad} {tipomedida}', marker='o', edgecolors='black', s=30, zorder=5)
                            lineas.append(punto)
        
        # Ajustar limites manuales
        infoeje = ConfiguracionController.ctrlObtenerConfiguracionEjeTDR(idproyecto)
        if infoeje:
            if tipo_grafico == 'PI':
                ejexmin, ejexmax, ejexprim, ejexsecu = infoeje[2], infoeje[3], infoeje[4], infoeje[5]
                ejeymin, ejeymax, ejeyprim, ejeysecu = infoeje[6], infoeje[7], infoeje[8], infoeje[9]
                
                # PI: X es Profundidad, Y es Impedancia
                if ejeymin != 0 or ejeymax != 0:
                    ax.set_xlim(ejeymin * unidadmedida, ejeymax * unidadmedida)
                    if ejeyprim > 0:
                        tick_primarios = np.arange(ejeymin * unidadmedida, ejeymax * unidadmedida, ejeyprim * unidadmedida)
                        if len(tick_primarios) > 2 and len(tick_primarios) < 100:
                            ax.set_xticks(tick_primarios)
                        else:
                            avisolabels = True
                    if ejeysecu > 0:
                        tick_secundarios = np.arange(ejeymin * unidadmedida, ejeymax * unidadmedida, ejeysecu * unidadmedida)
                        if len(tick_secundarios) > 2 and len(tick_secundarios) < 200:
                            for tick in tick_secundarios:
                                ax.axvline(x=tick, color='gray', linestyle='--', linewidth=0.5)
                        else:
                            avisolabels = True
                            
                if ejexmin != 0 or ejexmax != 0:
                    ax.set_ylim(ejexmin, ejexmax)
                    if ejexprim > 0:
                        tick_primarios = np.arange(ejexmin, ejexmax, ejexprim)
                        if len(tick_primarios) > 2 and len(tick_primarios) < 100:
                            ax.set_yticks(tick_primarios)
                        else:
                            avisolabels = True
                    if ejexsecu > 0:
                        tick_secundarios = np.arange(ejexmin, ejexmax, ejexsecu)
                        if len(tick_secundarios) > 2 and len(tick_secundarios) < 200:
                            for tick in tick_secundarios:
                                ax.axhline(y=tick, color='gray', linestyle='--', linewidth=0.5)
                        else:
                            avisolabels = True
            else:
                # CASO IP: X es Impedancia, Y es Profundidad
                ejexmin, ejexmax, ejexprim, ejexsecu = infoeje[2], infoeje[3], infoeje[4], infoeje[5]
                ejeymin, ejeymax, ejeyprim, ejeysecu = infoeje[6], infoeje[7], infoeje[8], infoeje[9]
                
                if ejexmin != 0 or ejexmax != 0:
                    ax.set_xlim(ejexmin, ejexmax)
                    if ejexprim > 0:
                        tick_primarios = np.arange(ejexmin, ejexmax, ejexprim)
                        if len(tick_primarios) > 2 and len(tick_primarios) < 100:
                            ax.set_xticks(tick_primarios)
                        else:
                            avisolabels = True
                    if ejexsecu > 0:
                        tick_secundarios = np.arange(ejexmin, ejexmax, ejexsecu)
                        if len(tick_secundarios) > 2 and len(tick_secundarios) < 200:
                            for tick in tick_secundarios:
                                ax.axvline(x=tick, color='gray', linestyle='--', linewidth=0.5)
                        else:
                            avisolabels = True
                            
                # --- AQUÍ ESTÁ EL AJUSTE PRINCIPAL ---
                if ejeymin != 0 or ejeymax != 0:
                    # Para invertir el eje Y manualmente: Primero MAX, luego MIN
                    # Esto asegura que el valor bajo (ej. 0) esté arriba y el alto (ej. 200) abajo
                    ax.set_ylim(ejeymax * unidadmedida, ejeymin * unidadmedida)
                    
                    if ejeyprim > 0:
                        # Nota: np.arange siempre debe ser de menor a mayor matemáticamente para generar los ticks
                        tick_primarios = np.arange(ejeymin * unidadmedida, ejeymax * unidadmedida, ejeyprim * unidadmedida)
                        if len(tick_primarios) > 2 and len(tick_primarios) < 100:
                            ax.set_yticks(tick_primarios)
                        else:
                            avisolabels = True
                    if ejeysecu > 0:
                        tick_secundarios = np.arange(ejeymin * unidadmedida, ejeymax * unidadmedida, ejeysecu * unidadmedida)
                        if len(tick_secundarios) > 2 and len(tick_secundarios) < 200:
                            for tick in tick_secundarios:
                                ax.axhline(y=tick, color='gray', linestyle='--', linewidth=0.5)
                        else:
                            avisolabels = True
                            
        # Configuración de ejes y etiquetas
        ax.set_title(f'Gráfico TDR {title}', fontsize=titulozise)
        ax.set_xlabel(x_label, fontsize=ejezise)
        ax.set_ylabel(y_label, fontsize=ejezise)
        ax.grid(True, which='both', linestyle='--', linewidth=0.5)
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda val, pos: '{:.{}f}'.format(val, decimales)))
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda val, pos: '{:.{}f}'.format(val, decimales)))
        plt.setp(ax.get_xticklabels(), rotation=90, ha="center", fontsize=etiquesize)
        plt.setp(ax.get_yticklabels(), fontsize=etiquesize)

        annot = ax.annotate("", xy=(0, 0), xytext=(15, 15), textcoords="offset points",
                            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#cccccc", lw=1, alpha=0.95),
                            arrowprops=dict(arrowstyle="-|>", connectionstyle="arc3,rad=0.2", color="#555555", lw=0.8))
        annot.set_visible(False)
        punto_resaltado, = ax.plot([], [], 'o', color='#dc3545', markersize=6,
                                    markeredgecolor='white', markeredgewidth=1, zorder=10)
        punto_resaltado.set_visible(False)
        
        # Configuración de leyenda paginada
        leyenda_elementos = lineas
        leyenda_labels = [line.get_label() for line in lineas]
        filas_totales = len(leyenda_labels)
        filas_max = 6
        pagina_actual = 0
        ancho_pantalla = widget.width()
        limite_caracteres = 45
        caracteres_por_pixel = limite_caracteres / 800
        total_caracteres = sum(len(nombre) for nombre in leyenda_labels)
        # Evitar división por cero si no hay caracteres
        promedio_caracteres_por_equipo = total_caracteres / filas_totales if filas_totales > 0 else 10
        columnas = max(1, int(ancho_pantalla * caracteres_por_pixel / promedio_caracteres_por_equipo))
        equipos_por_pagina = filas_max * columnas
        total_filas_leyenda = math.ceil(filas_totales / equipos_por_pagina)

        def actualizar_leyenda():
            nonlocal pagina_actual
            if total_filas_leyenda == 0: return # Evitar errores si no hay leyenda
            inicio = pagina_actual * equipos_por_pagina
            fin = min(inicio + equipos_por_pagina, filas_totales)
            ax.legend(leyenda_elementos[inicio:fin], leyenda_labels[inicio:fin], loc=leyenda_posicion, bbox_to_anchor=leyenda_bbox, ncol=leyenda_ncol, frameon=False, prop={'size': leyendazise})
            figure.subplots_adjust(**ajuste_margenes)
            canvas.draw_idle()

        def siguiente_pagina():
            nonlocal pagina_actual
            if (pagina_actual + 1) * equipos_por_pagina < filas_totales:
                pagina_actual += 1
            else:
                pagina_actual = 0
            actualizar_leyenda()

        def anterior_pagina():
            nonlocal pagina_actual
            if pagina_actual > 0:
                pagina_actual -= 1
            else:
                pagina_actual = total_filas_leyenda - 1
            actualizar_leyenda()

        if total_filas_leyenda > 1:
            boton_siguiente = QPushButton("Siguiente")
            boton_anterior = QPushButton("Anterior")
            boton_siguiente.clicked.connect(siguiente_pagina)
            boton_anterior.clicked.connect(anterior_pagina)
            toolbar_layout.addWidget(boton_anterior)
            toolbar_layout.addWidget(boton_siguiente)

        def on_hover(event):
            if not check_inspector.isChecked() or event.inaxes != ax:
                if annot.get_visible():
                    annot.set_visible(False)
                    punto_resaltado.set_visible(False)
                    canvas.draw_idle()
                return

            min_dist = 30
            encontrado = None
            xlim, ylim = ax.get_xlim(), ax.get_ylim()

            for linea in lineas:
                if not hasattr(linea, 'get_xdata') or not linea.get_visible():
                    continue  # Salta los puntos de "fallas" (son scatter, no líneas)
                x_data = np.asarray(linea.get_xdata(), dtype=float)
                y_data = np.asarray(linea.get_ydata(), dtype=float)
                mask = (x_data >= min(xlim)) & (x_data <= max(xlim)) & (y_data >= min(ylim)) & (y_data <= max(ylim))
                if not np.any(mask):
                    continue
                puntos_px = ax.transData.transform(np.column_stack([x_data[mask], y_data[mask]]))
                mouse = np.array([event.x, event.y])
                dists = np.sqrt(np.sum((puntos_px - mouse) ** 2, axis=1))
                idx = np.argmin(dists)
                if dists[idx] < min_dist:
                    min_dist = dists[idx]
                    encontrado = (x_data[mask][idx], y_data[mask][idx], linea.get_label())

            if encontrado:
                fx, fy, fecha_str = encontrado
                if es_grafico_IP:
                    impedancia_val, profundidad_val = fx, fy
                else:
                    profundidad_val, impedancia_val = fx, fy

                punto_resaltado.set_data([fx], [fy])
                punto_resaltado.set_visible(True)

                punto_pixel = ax.transData.transform((fx, fy))
                x_rel, y_rel = ax.transAxes.inverted().transform(punto_pixel)
                offset_x, offset_y = 15, 15
                ha, va = 'left', 'bottom'
                if y_rel > 0.70: va, offset_y = 'top', -15
                if x_rel > 0.65: ha, offset_x = 'right', -15

                annot.xy = (fx, fy)
                annot.xytext = (offset_x, offset_y)
                annot.set_ha(ha)
                annot.set_va(va)
                annot.set_text(f"Fecha: {fecha_str}\nProfundidad: {profundidad_val:.2f} {tipomedida}\nImpedancia: {impedancia_val:.2f} Ω")
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

        canvas.mpl_connect('motion_notify_event', on_hover)

        actualizar_leyenda()
        canvas.draw_idle()
        plt.close(figure)
        if avisolabels:
            mostrar_mensaje("Ejes", "No se aplicó la configuración de ejes.", "advertencia")