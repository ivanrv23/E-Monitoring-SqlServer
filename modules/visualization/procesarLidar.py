import numpy as np
import laspy
import time
import vtk
import matplotlib.dates as mdates
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QScrollArea, QWidget, QCheckBox, QPushButton, QSizePolicy, QLabel,
                            QHBoxLayout, QComboBox,QMenu,QDoubleSpinBox,QDialogButtonBox,QFormLayout)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, QThread, Signal
from controllers.InterfazController import InterfazController
from controllers.PrismasVirtualesController import PrismasVirtualesController
from vtkmodules.util.numpy_support import numpy_to_vtk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from datetime import datetime
from scipy.interpolate import griddata
from matplotlib.colors import TwoSlopeNorm,LinearSegmentedColormap
from utils.shared.loading import LoadingView
from utils.common.customToolbar import CustomToolbar 
from utils.common.rutasarchivos import resource_path

# ocultar onsola de errores
vtk.vtkObject.GlobalWarningDisplayOff()

class ProcesarLidar:
    @staticmethod
    def procesar_volumen_2_5d(archivo1, archivo2, grid_step, grid_step_muestreo):
        def muestrear_por_rejilla(coords, grid_step):
            if grid_step == 0:
                return coords

            x_min, y_min = np.min(coords[:, 0]), np.min(coords[:, 1])
            ix = np.floor((coords[:, 0] - x_min) / grid_step).astype(int)
            iy = np.floor((coords[:, 1] - y_min) / grid_step).astype(int)

            celdas = {}
            for i, (cx, cy) in enumerate(zip(ix, iy)):
                if (cx, cy) not in celdas:
                    celdas[(cx, cy)] = coords[i]

            return np.array(list(celdas.values()))

        def interpolar_rapido(coords, grid_points, method='linear'):
            z_interp = griddata(coords[:, :2], coords[:, 2], grid_points, method=method)
            return z_interp

        def calcular_volumen_preciso_optimizado(archivo_base, archivo_comparar, grid_step, grid_step_muestreo):
            base = laspy.read(archivo_base)
            comp = laspy.read(archivo_comparar)

            coords_base = np.vstack((base.x, base.y, base.z)).T
            coords_comp = np.vstack((comp.x, comp.y, comp.z)).T

            coords_base_muestreados = muestrear_por_rejilla(coords_base, grid_step_muestreo)
            coords_comp_muestreados = muestrear_por_rejilla(coords_comp, grid_step_muestreo)

            all_x = np.concatenate([coords_base[:, 0], coords_comp[:, 0]])
            all_y = np.concatenate([coords_base[:, 1], coords_comp[:, 1]])
            x_min, x_max = np.floor(np.min(all_x)), np.ceil(np.max(all_x))
            y_min, y_max = np.floor(np.min(all_y)), np.ceil(np.max(all_y))

            grid_x = np.arange(x_min, x_max, grid_step)
            grid_y = np.arange(y_min, y_max, grid_step)
            grid_xx, grid_yy = np.meshgrid(grid_x, grid_y)
            grid_points = np.column_stack((grid_xx.ravel(), grid_yy.ravel()))

            base_z = interpolar_rapido(coords_base_muestreados, grid_points)
            comp_z = interpolar_rapido(coords_comp_muestreados, grid_points)

            base_z_grid = base_z.reshape(grid_xx.shape)
            comp_z_grid = comp_z.reshape(grid_xx.shape)

            diff_grid = comp_z_grid - base_z_grid
            area_celda = grid_step ** 2
            mascara_valida = ~np.isnan(diff_grid)
            volumen_total = np.nansum(diff_grid[mascara_valida]) * area_celda
            volumen_relleno = np.nansum(np.where(diff_grid > 0, diff_grid, 0)) * area_celda
            volumen_excavacion = np.nansum(np.where(diff_grid < 0, diff_grid, 0)) * area_celda
            diferencia_media = np.nanmean(diff_grid)
            area_total = np.sum(mascara_valida) * area_celda

            return {
                'volumen_total': volumen_total,
                'volumen_relleno': volumen_relleno,
                'volumen_excavacion': volumen_excavacion,
                'diferencia_media': diferencia_media,
                'area_total': area_total,
                'grid_diferencias': diff_grid,
                'grid_xx': grid_xx,
                'grid_yy': grid_yy
            }

        def graficar_diferencias(grid_xx, grid_yy, diff_grid, resumen_texto):
            plt.close('all')
            # Crear colormap suave: azul → verde → amarillo → rojo
            colores = ["#0000FF", "#00FF00", "#FFFF00", "#FF0000"]
            cmap = LinearSegmentedColormap.from_list("custom_cmap", colores, N=256)
            cmap.set_under('gray')
            cmap.set_over('gray')

            # Rango real
            real_min = np.nanmin(diff_grid)
            real_max = np.nanmax(diff_grid)

            # Rango simétrico centrado en 0
            lim = max(abs(real_min), abs(real_max))
            vmin, vmax = -lim, lim

            # Normalización centrada en 0
            norm = TwoSlopeNorm(vmin=vmin, vcenter=0, vmax=vmax)

            # Crear figura y mapa
            plt.figure()
            plt.title("Mapa de calor de diferencias de altura (m)")
            plt.xlabel("Coordenada X (m)")
            plt.ylabel("Coordenada Y (m)")
            pcm = plt.pcolormesh(grid_xx, grid_yy, diff_grid, cmap=cmap, norm=norm, shading='auto')

            # Configurar formato de los ejes para evitar notación científica y mostrar 3 decimales
            plt.ticklabel_format(style='plain', useOffset=False)
            plt.xticks(np.linspace(grid_xx.min(), grid_xx.max(), 5), rotation=45)
            plt.yticks(np.linspace(grid_yy.min(), grid_yy.max(), 5))
            plt.gca().xaxis.set_major_formatter(plt.FormatStrFormatter('%.3f'))
            plt.gca().yaxis.set_major_formatter(plt.FormatStrFormatter('%.3f'))

            # Barra de color extendida
            cbar = plt.colorbar(pcm, extend='both')
            cbar.set_label('Diferencia de altura (m)')

            # 7 etiquetas equiespaciadas en el rango simétrico
            ticks = np.linspace(vmin, vmax, 7)
            cbar.set_ticks(ticks)
            cbar.set_ticklabels([f"{v:.2f}" for v in ticks])

            # Mostrar resumen dentro del gráfico
            plt.text(0.02, 0.98, resumen_texto, transform=plt.gca().transAxes,
                    fontsize=9, verticalalignment='top',
                    bbox=dict(boxstyle="round", fc="white", ec="gray"))

            plt.tight_layout()
            plt.show()

        # Procesamiento real
        try:
            resultados = calcular_volumen_preciso_optimizado(
                archivo_base=archivo1,
                archivo_comparar=archivo2,
                grid_step=grid_step,
                grid_step_muestreo=grid_step_muestreo
            )

            resumen = (
                f"Volumen total: {resultados['volumen_total']:.2f} m³\n"
                f"Relleno (+): {resultados['volumen_relleno']:.2f} m³\n"
                f"Excavación (-): {-resultados['volumen_excavacion']:.2f} m³\n"
                f"Dif. media altura: {resultados['diferencia_media']:.4f} m\n"
                f"Área analizada: {resultados['area_total']:.2f} m²"
            )

            graficar_diferencias(
                resultados['grid_xx'],
                resultados['grid_yy'],
                resultados['grid_diferencias'],
                resumen_texto=resumen
            )

            return True

        except Exception as e:
            return False
        
    @staticmethod
    def MostrarDetalles(archivo1, archivo2):
        dialog = QDialog()
        dialog.setWindowTitle("Parámetros para Volumen 2.5D")

        layout = QVBoxLayout()
        form_layout = QFormLayout()

        # Campo para grid_step
        spin_grid_step = QDoubleSpinBox()
        spin_grid_step.setDecimals(2)
        spin_grid_step.setRange(0.1, 1000.0)  # Valor mínimo ajustado a 0.1
        spin_grid_step.setSingleStep(0.1)
        spin_grid_step.setValue(1.0)

        # Campo para grid_esped
        spin_grid_esped = QDoubleSpinBox()
        spin_grid_esped.setDecimals(2)
        spin_grid_esped.setRange(0.1, 1000.0)  # Valor mínimo ajustado a 0.1
        spin_grid_esped.setSingleStep(0.1)
        spin_grid_esped.setValue(1.0)

        form_layout.addRow(QLabel("Tamaño del Grid (grid_step):"), spin_grid_step)
        form_layout.addRow(QLabel("Espesor del Grid (grid_esped):"), spin_grid_esped)

        # Etiqueta informativa centrada y en dos líneas
        info_label = QLabel("Nota: Valores más pequeños<br/>aumentan la precisión pero ralentizan el proceso.")
        info_label.setAlignment(Qt.AlignCenter)

        # Botón procesar
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        def procesar():
            grid_step = spin_grid_step.value()
            grid_esped = spin_grid_esped.value()
            ProcesarLidar.procesar_volumen_2_5d(archivo1, archivo2, grid_step, grid_esped)

        button_box.accepted.connect(procesar)

        layout.addLayout(form_layout)
        layout.addWidget(info_label)
        layout.addWidget(button_box)

        dialog.setLayout(layout)
        dialog.exec()

    def actualizar_colores(checkboxes_seleccionados):
        """Actualizar colores según el orden de selección."""
        for i, checkbox in enumerate(checkboxes_seleccionados):
            if i == 0:
                checkbox.setStyleSheet("background-color: green;")
            elif i == 1:
                checkbox.setStyleSheet("background-color: yellow;")

    def limitar_seleccion(checkbox, checkboxes_seleccionados, archivos_seleccionados):
        """Permite solo 2 checkboxes marcados y almacena rutas."""
        if checkbox.isChecked():
            checkboxes_seleccionados.append(checkbox)
            archivos_seleccionados.append(checkbox.property("ruta"))  

            if len(checkboxes_seleccionados) > 2:
                antiguo = checkboxes_seleccionados.pop(0)
                archivos_seleccionados.pop(0)  
                if antiguo:  
                    antiguo.blockSignals(True)  # 🔹 Evita señales innecesarias
                    antiguo.setChecked(False)  
                    antiguo.setStyleSheet("")  
                    antiguo.blockSignals(False)
        else:
            if checkbox in checkboxes_seleccionados:
                index = checkboxes_seleccionados.index(checkbox)
                checkboxes_seleccionados.pop(index)
                archivos_seleccionados.pop(index)  
            checkbox.setStyleSheet("")
        ProcesarLidar.actualizar_colores(checkboxes_seleccionados)

    def listarLidar(proyecto_id, rendererLidar, vtkWidgetLidar, cambiarpagina):
        dialog = QDialog()
        dialog.setWindowTitle("Procesar Archivos LiDAR")
        dialog.resize(300, 250)

        checkboxes_seleccionados = []
        archivos_seleccionados = []

        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignTop)

        leyenda_layout = QHBoxLayout()
        leyenda_verde = QLabel("Lectura base")
        leyenda_verde.setStyleSheet("background-color: green; padding: 5px;")
        leyenda_verde.setAlignment(Qt.AlignCenter)

        leyenda_amarillo = QLabel("Lectura normal")
        leyenda_amarillo.setStyleSheet("background-color: yellow; padding: 5px;")
        leyenda_amarillo.setAlignment(Qt.AlignCenter)

        leyenda_layout.addWidget(leyenda_verde)
        leyenda_layout.addWidget(leyenda_amarillo)
        main_layout.addLayout(leyenda_layout)

        combo_box = QComboBox()
        componentes = InterfazController.ctrlListarComponentesProyecto(proyecto_id)
        for componente in componentes:
            combo_box.addItem(componente[2], componente[0])
        main_layout.addWidget(combo_box)

        scroll_area = QScrollArea()
        scroll_area.setMinimumHeight(120)
        scroll_area.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        scroll_area.setWidgetResizable(True)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_layout.setSpacing(5)
        scroll_layout.setAlignment(Qt.AlignTop)

        def actualizar_archivos():
            """Carga los archivos según el componente seleccionado."""
            nonlocal checkboxes_seleccionados, archivos_seleccionados

            checkboxes_seleccionados.clear()  # Limpiar lista antes de eliminar checkboxes
            archivos_seleccionados.clear()

            for i in reversed(range(scroll_layout.count())):
                widget = scroll_layout.itemAt(i).widget()
                if widget:
                    widget.deleteLater()

            id_componente = combo_box.currentData()
            archivos_lidar = InterfazController.ctrlListarArchivosLidar(id_componente) or []

            for archivo in archivos_lidar:
                nombre_archivo, ruta_archivo = archivo
                checkbox = QCheckBox(nombre_archivo)
                checkbox.setProperty("ruta", ruta_archivo)
                checkbox.stateChanged.connect(lambda *args, cb=checkbox: ProcesarLidar.limitar_seleccion(cb, checkboxes_seleccionados, archivos_seleccionados))
                scroll_layout.addWidget(checkbox)

        combo_box.currentIndexChanged.connect(actualizar_archivos)
        actualizar_archivos()

        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)

        def procesar():
            if len(archivos_seleccionados) == 2:
                mostrar_menu_distancia()

        def mostrar_menu_distancia():
            menu = QMenu()
            action_xyz = QAction("Distancia en X, Y, Z", menu)
            action_xyz.triggered.connect(lambda: enviar_distancia('xyz'))

            action_xy = QAction("Distancia en X, Y", menu)
            action_xy.triggered.connect(lambda: enviar_distancia('xy'))

            action_x = QAction("Distancia en X", menu)
            action_x.triggered.connect(lambda: enviar_distancia('x'))

            action_y = QAction("Distancia en Y", menu)
            action_y.triggered.connect(lambda: enviar_distancia('y'))

            action_z = QAction("Distancia en Z", menu)
            action_z.triggered.connect(lambda: enviar_distancia('z'))

            # Nueva opción agregada
            action_volumen = QAction("Volumen 2.5D", menu)
            action_volumen.triggered.connect(lambda: enviar_distancia('volumen2_5d'))

            menu.addAction(action_xyz)
            menu.addAction(action_xy)
            menu.addAction(action_x)
            menu.addAction(action_y)
            menu.addAction(action_z)
            menu.addAction(action_volumen)  # Añadir al menú

            menu.exec(procesar_button.mapToGlobal(procesar_button.rect().bottomRight()))


        def enviar_distancia(distancia):
            dialog.accept()
            if distancia == 'volumen2_5d':
                ProcesarLidar.MostrarDetalles(
                    archivos_seleccionados[0],
                    archivos_seleccionados[1]
                )
            else:
                # Iniciar Hilo
                # loading = LoadingView.mostrarLoading()
                # def on_threadcorte_complete(respuesta):
                #     loading.close()
                #     if respuesta:
                #         cambiarpagina()
                # prom = CompararArchivosLidarThread(archivos_seleccionados[0], archivos_seleccionados[1], rendererLidar, vtkWidgetLidar, distancia)
                # prom.task_finishCompararLidar.connect(on_threadcorte_complete)
                # prom.start()
                # loading.exec()
            
                respuesta = ProcesarLidar.procesar_nubes_de_puntos(
                    archivos_seleccionados[0],
                    archivos_seleccionados[1],
                    rendererLidar,
                    vtkWidgetLidar,
                    distancia
                )
                if respuesta:
                    cambiarpagina()


        procesar_button = QPushButton("Procesar")
        procesar_button.clicked.connect(procesar)
        main_layout.addWidget(procesar_button)

        dialog.setLayout(main_layout)
        dialog.exec()

    def procesar_nubes_de_puntos(las_file_path1, las_file_path2, renderer, vtk_widget, forma='xyz'):
        try:
            # Intentar importar pykdtree; si no está disponible, usar cKDTree
            try:
                from pykdtree.kdtree import KDTree as PykdTree
                use_pykdtree = True
            except ImportError:
                from scipy.spatial import cKDTree
                use_pykdtree = False

            # ─── CARGA DE ARCHIVOS LAS ─────────────────────────────────────────────
            start_time = time.time()
            # Usamos laspy.read (si ya tienes un método optimizado para ello)
            las_file1 = laspy.read(resource_path(las_file_path1))
            las_file2 = laspy.read(resource_path(las_file_path2))
            
            # ─── EXTRACCIÓN DE COORDENADAS ───────────────────────────────────────────
            start_time = time.time()
            # Usamos np.asarray y transponemos para obtener un array (N,3)
            coordenadas1 = np.asarray([las_file1.x, las_file1.y, las_file1.z]).T
            coordenadas2 = np.asarray([las_file2.x, las_file2.y, las_file2.z]).T
            
            # ─── CONSTRUCCIÓN DEL KD-TREE ────────────────────────────────────────────
            if use_pykdtree:
                start_time = time.time()
                kdtree = PykdTree(coordenadas2)
            else:
                start_time = time.time()
                kdtree = cKDTree(coordenadas2, leafsize=10)
            
            # ─── CÁLCULO DE LAS DIFERENCIAS EN BLOQUES ───────────────────────────────
            def calcular_diferencias_bloques(coordenadas1, kdtree, batch_size=500_000, forma='xyz'):
                num_puntos = coordenadas1.shape[0]
                magnitudes = np.zeros(num_puntos, dtype=np.float32)
                for i in range(0, num_puntos, batch_size):
                    fin = min(i + batch_size, num_puntos)
                    # Usar workers en cKDTree; pykdtree no acepta ese argumento
                    if use_pykdtree:
                        distancias, indices = kdtree.query(coordenadas1[i:fin])
                    else:
                        distancias, indices = kdtree.query(coordenadas1[i:fin], workers=-1)
                    # Calcular la diferencia entre los puntos y sus vecinos más cercanos
                    diferencias = coordenadas1[i:fin] - coordenadas2[indices]
                    # Seleccionar el cálculo según la 'forma' deseada
                    if forma == 'x':
                        magnitudes[i:fin] = diferencias[:, 0]
                    elif forma == 'y':
                        magnitudes[i:fin] = diferencias[:, 1]
                    elif forma == 'z':
                        magnitudes[i:fin] = diferencias[:, 2]
                    elif forma == 'xy':
                        magnitudes[i:fin] = np.linalg.norm(diferencias[:, :2], axis=1)
                    elif forma == 'xyz':
                        magnitudes[i:fin] = np.linalg.norm(diferencias, axis=1)
                return magnitudes

            start_time = time.time()
            magnitudes = calcular_diferencias_bloques(coordenadas1, kdtree, batch_size=1_000_000, forma=forma)
            # ─── VISUALIZACIÓN CON VTK ───────────────────────────────────────────────
            color_transfer_function = vtk.vtkColorTransferFunction()
            if np.all(magnitudes == 0):
                color_transfer_function.AddRGBPoint(0.0, 0.0, 0.0, 1.0)  # Azul
            else:
                color_transfer_function.AddRGBPoint(magnitudes.min(), 0.0, 0.0, 1.0)  # Azul
                color_transfer_function.AddRGBPoint(
                    magnitudes.min() + (magnitudes.max() - magnitudes.min()) * 0.35,
                    0.0, 1.0, 0.0)  # Verde
                color_transfer_function.AddRGBPoint(
                    magnitudes.min() + (magnitudes.max() - magnitudes.min()) * 0.65,
                    1.0, 1.0, 0.0)  # Amarillo
                color_transfer_function.AddRGBPoint(magnitudes.max(), 1.0, 0.0, 0.0)  # Rojo

            # Preparar datos para VTK
            puntos_vtk = vtk.vtkPoints()
            puntos_vtk.SetData(numpy_to_vtk(coordenadas1))
            poli_datos = vtk.vtkPolyData()
            poli_datos.SetPoints(puntos_vtk)

            # Usar las magnitudes originales para la visualización
            vtk_magnitudes = numpy_to_vtk(magnitudes, array_type=vtk.VTK_FLOAT)
            vtk_magnitudes.SetName("Magnitudes")
            poli_datos.GetPointData().SetScalars(vtk_magnitudes)

            glifo_filtro = vtk.vtkVertexGlyphFilter()
            glifo_filtro.SetInputData(poli_datos)
            glifo_filtro.Update()

            mapeador = vtk.vtkPolyDataMapper()
            mapeador.SetInputData(glifo_filtro.GetOutput())
            mapeador.SetLookupTable(color_transfer_function)
            mapeador.SetScalarRange(magnitudes.min(), magnitudes.max())

            actor = vtk.vtkActor()
            actor.SetMapper(mapeador)

            # Limpiar el renderizador antes de agregar nuevos elementos
            renderer.RemoveAllViewProps()
            renderer.AddActor(actor)

            # Crear y configurar la barra de color
            scalar_bar = vtk.vtkScalarBarActor()
            scalar_bar.SetLookupTable(color_transfer_function)
            scalar_bar.SetNumberOfLabels(17)
            label_text_property = vtk.vtkTextProperty()
            label_text_property.SetJustificationToCentered()
            label_text_property.SetVerticalJustificationToCentered()
            label_text_property.SetColor(0.5, 0.5, 0.5)
            scalar_bar.SetLabelTextProperty(label_text_property)
            label_text_property.SetJustificationToLeft()

            title_text_property = vtk.vtkTextProperty()
            title_text_property.SetJustificationToCentered()
            title_text_property.SetVerticalJustificationToCentered()
            title_text_property.SetColor(0.5, 0.5, 0.5)

            scalar_bar.SetLabelFormat("%.6f  ")
            scalar_bar.SetPosition(0.9, 0.15)
            scalar_bar.SetPosition2(0.08, 0.8)
            scalar_bar.SetTextPositionToPrecedeScalarBar()
            renderer.AddActor2D(scalar_bar)
            renderer.ResetCamera()
            vtk_widget.GetRenderWindow().Render()
            return True
        except Exception as e:
            return False
    
    def modalGraficasDesplazamiento(topo_marcados, polydatos, prismas_virtuales):
        dialog = QDialog()
        dialog.setWindowTitle("Análisis de Desplazamientos")
        dialog.setMinimumSize(800, 500)
        
        layout = QVBoxLayout(dialog)
        
        combo_tipo = QComboBox()
        combo_tipo.addItem("Seleccione tipo de desplazamiento", None)
        combo_tipo.addItem("Desplazamiento Norte", 'y')
        combo_tipo.addItem("Desplazamiento Este", 'x')
        combo_tipo.addItem("Desplazamiento Vertical", 'z')
        
        fig = plt.Figure()
        ax = fig.add_subplot(111)
        canvas = FigureCanvas(fig)
        toolbar = CustomToolbar(canvas, dialog)
        
        date_format = mdates.DateFormatter('%d-%m-%Y')
        ax.xaxis.set_major_formatter(date_format)
        
        prismas_data = PrismasVirtualesController.ctrlPrismasVirtuales(
            [prisma[2] for grupo in prismas_virtuales for prisma in grupo[1]]
        )
        colores = plt.cm.tab10(np.linspace(0, 1, len(prismas_data)))
        series = {}

        for idx, (nombre, x, y, z, radio) in enumerate(prismas_data):
            promedios = ProcesarLidar.calcular_y_graficar_promedio(x, y, z, radio, topo_marcados, polydatos)
            desplazamientos = ProcesarLidar.calcularDesplazamientos(promedios)
            
            if desplazamientos:
                fechas = [datetime.strptime(d[0], "%Y-%m-%d") for d in desplazamientos]
                series[nombre] = {
                    'fechas': fechas,
                    'x': [d[1] for d in desplazamientos],
                    'y': [d[2] for d in desplazamientos],
                    'z': [d[3] for d in desplazamientos],
                    'color': colores[idx]
                }

        def actualizar_grafica(index):
            ax.clear()
            tipo = combo_tipo.itemData(index)
            
            if not tipo:
                # Si no hay tipo seleccionado, limpiar el gráfico
                ax.axis('off')  # Desactiva los ejes
                ax.set_title("")  # Elimina el título
                canvas.draw()
                return  # Salir de la función sin graficar nada
            
            # Configuración del gráfico
            ax.grid(True, linestyle=':', alpha=0.5)
            ax.set_xlabel("Fecha (Día-Mes-Año)", fontsize=10, labelpad=15)
            ax.set_ylabel("Desplazamiento (m)", fontsize=10)
            plt.setp(ax.get_xticklabels(), rotation=90, ha='center', fontsize=8)
            
            # Graficar series
            min_date = max_date = None
            for nombre, data in series.items():
                line = ax.plot(
                    data['fechas'],
                    data[tipo],
                    marker='o',
                    linestyle='-',
                    color=data['color'],
                    label=nombre,
                    markersize=6,
                    linewidth=1.5
                )
                
                current_min = min(data['fechas'])
                current_max = max(data['fechas'])
                min_date = current_min if min_date is None else min(min_date, current_min)
                max_date = current_max if max_date is None else max(max_date, current_max)
            
            # Ajustar márgenes
            fig.subplots_adjust(bottom=0.35, left=0.1, right=0.95)
            
            # Configurar leyenda
            ax.legend(
                loc='upper center',
                bbox_to_anchor=(0.5, -0.5),
                ncol=3,
                frameon=False,
                fontsize=9
            )
            
            ax.set_title(f"Desplazamiento {tipo.upper()}", pad=20, fontsize=12)
            canvas.draw()

        # Conexiones
        combo_tipo.currentIndexChanged.connect(actualizar_grafica)
        
        # Diseño
        layout.addWidget(combo_tipo)
        layout.addWidget(toolbar)
        layout.addWidget(canvas)

        # Inicializar gráfico en blanco
        actualizar_grafica(0)  # Llamar a la función para limpiar el gráfico al inicio

        # Mostrar diálogo
        dialog.exec()
        
    def calcular_y_graficar_promedio(x, y, z, radio, topografiasmarcadas, polydatos_LAS):
        centro_esfera = np.array([x, y, z])
        promedios = []
        ids_marcados = set()

        if topografiasmarcadas:
            for componente in topografiasmarcadas:
                for _, _, idtopo in componente[1]:
                    ids_marcados.add(idtopo)

        for componente, idtopo, fecha, poli_datos in polydatos_LAS:
            if idtopo not in ids_marcados:
                continue

            try:
                datetime.strptime(fecha, "%Y-%m-%d")
                puntos = np.array(poli_datos.GetPoints().GetData())
                distancias = np.linalg.norm(puntos - centro_esfera, axis=1)
                puntos_filtrados = puntos[distancias <= radio]

                if len(puntos_filtrados) == 0:
                    continue

                promedio = (
                    fecha,
                    np.mean(puntos_filtrados[:, 0]),
                    np.mean(puntos_filtrados[:, 1]),
                    np.mean(puntos_filtrados[:, 2])
                )
                promedios.append(promedio)

            except ValueError:
                continue
            except Exception:
                continue

        return promedios
        
    def calcularDesplazamientos(promedios):
        """Calcula desplazamientos manteniendo las fechas originales"""
        if not promedios:
            return []

        try:
            promedios_ordenados = sorted(
                promedios, 
                key=lambda x: datetime.strptime(x[0], "%Y-%m-%d")
            )
            
            x_ref, y_ref, z_ref = promedios_ordenados[0][1], promedios_ordenados[0][2], promedios_ordenados[0][3]
            
            return [
                (
                    fecha,
                    x - x_ref,
                    y - y_ref,
                    z - z_ref
                ) for (fecha, x, y, z) in promedios_ordenados
            ]
        except Exception:
            return []
    
# Hilo comparar dos Lidar
class CompararArchivosLidarThread(QThread):
    task_finishCompararLidar = Signal(bool)

    def __init__(self, file_path1, file_path2, rendererLidar, vtkWidgetLidar, distancia):
        super().__init__()
        self.file_path1 = file_path1
        self.file_path2 = file_path2
        self.rendererLidar = rendererLidar
        self.vtkWidgetLidar = vtkWidgetLidar
        self.distancia = distancia
    
    def run(self):
        respuesta = ProcesarLidar.procesar_nubes_de_puntos(self.file_path1, self.file_path2, self.rendererLidar, self.vtkWidgetLidar, self.distancia)
        # mandar señal
        self.task_finishCompararLidar.emit(respuesta)