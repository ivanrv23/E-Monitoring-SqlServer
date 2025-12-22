import io
import vtk
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QComboBox, QPushButton, QTextEdit, QLabel, QTabWidget)
from PySide6.QtCore import Qt
from PIL import Image
from utils.common.rutasarchivos import resource_path
from utils.common.alertas import mostrar_mensaje
from utils.common.metodosGenerales import MetodosGenerales
from controllers.ReporteController import ReporteController

class GraficaReporte:
    
    def mostrarDialogoImagenVisor(canvaswidget, vista, tipo, titulografica, idproyecto, tipoequipo):
        loader = QUiLoader()
        ui_file_path = resource_path("ui/capturaimagenreporte.ui")
        ui_file = loader.load(ui_file_path, None)
        dialogo = QDialog()
        dialogo.setWindowTitle("Imagen a Reporte General")
        layout_add_grafica = QVBoxLayout()
        layout_add_grafica.addWidget(ui_file)
        dialogo.setLayout(layout_add_grafica)
        # inicializar tools
        combo_componentes = dialogo.findChild(QComboBox, "combo_componentes")
        entrada_tittle = dialogo.findChild(QTextEdit, "input_titulo")
        entrada_comenta = dialogo.findChild(QTextEdit, "input_descripcion")
        label_imagen = dialogo.findChild(QLabel, "label_grafico")
        boton_cancelar = dialogo.findChild(QPushButton, "btn_cancelar")
        boton_aceptar = dialogo.findChild(QPushButton, "btn_confirmar")
        entrada_tittle.setPlainText(titulografica)
        # Cargar componentes
        MetodosGenerales.llenar_componentes_combo(idproyecto, combo_componentes)
        if vista == "Visor":
            GraficaReporte.imagen_widget_vtk(canvaswidget, label_imagen)
        else:
            imagen, _ = GraficaReporte.capture_canvas_image(canvaswidget, dpi=72)
            if imagen:
                pixmap = QPixmap.fromImage(imagen)
                scaled_pixmap = pixmap.scaled(label_imagen.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
                label_imagen.setPixmap(scaled_pixmap)
                label_imagen.adjustSize()
            else:
                boton_aceptar.setEnabled(False)
        def cerrar_dialogo():
            dialogo.close()
        def confirmar_dialogo():
            if combo_componentes.count() > 0:
                idcomponente = combo_componentes.currentData()
                nombre_carpeta = "resources/images/graficatemporal.png"
                if vista == "Visor":
                    respuesta = GraficaReporte.guardarGraficaVTK(canvaswidget, nombre_carpeta, vista, tipo, entrada_tittle, entrada_comenta, tipoequipo, idcomponente)
                else:
                    respuesta = GraficaReporte.guardarGraficaReporte(canvaswidget, vista, tipo, entrada_tittle, entrada_comenta, tipoequipo, idcomponente)
                if respuesta is False:
                    mostrar_mensaje("ERROR AL GUARDAR", "No se pudo guardar la imagen.", "advertencia")
                dialogo.close()
        boton_cancelar.clicked.connect(cerrar_dialogo)
        boton_aceptar.clicked.connect(confirmar_dialogo)
        dialogo.exec()
    
    def guardarGraficaVTK(canvas, nombrecarpeta, vista, tipo, entradatittle, entradacomenta, tipoequipo, idcomponente):
        try:
            GraficaReporte.save_image_vtk(canvas, nombrecarpeta)
            try:
                GraficaReporte.recortar_imagen(nombrecarpeta)
            except Exception as e:
                print("Ocurrió un error al recortar la imagen:", e)
            image_path = resource_path(nombrecarpeta)
            if image_path:
                imagen_blob = MetodosGenerales.convertirImagenBlob(image_path)
                texto_titulo = entradatittle.toPlainText()
                texto_descripcion = entradacomenta.toPlainText()
                data = {
                    "id_componente": idcomponente,
                    "vista_reporte": vista,
                    "tipo_grafico": tipo,
                    "imagen_grafica": imagen_blob,
                    "titulo_grafica": texto_titulo,
                    "descripcion_grafica": texto_descripcion,
                    "tipo_reporte": "GENERAL",
                    "tipo_equipo": tipoequipo
                }
                respue = ReporteController.ctrlGuardarImagenReporte(data)
                if respue:
                    return True
            else:
                return False
        except Exception as e:
            return False
    
    def save_image_vtk(canvas, ruta, scale_factor=2):
        # Obtener la ventana de renderizado
        render_window = canvas.GetRenderWindow()
        render_window.OffScreenRenderingOn()  # Activar renderizado fuera de pantalla
        # Crear el filtro para capturar la ventana de renderizado
        image_filter = vtk.vtkWindowToImageFilter()
        image_filter.SetInput(render_window)
        # Aumentar la resolución de la captura usando ScaleFactor
        image_filter.SetScale(scale_factor, scale_factor)
        # Capturar con transparencia (RGBA)
        # image_filter.SetInputBufferTypeToRGBA()
        # Capturar con sin  transparencia (RGB)
        image_filter.SetInputBufferTypeToRGB()
        image_filter.ReadFrontBufferOff()
        image_filter.Update()
        # Guardar la imagen en formato PNG con vtkPNGWriter
        writer = vtk.vtkPNGWriter()
        writer.SetFileName(ruta)
        writer.SetInputConnection(image_filter.GetOutputPort())
        # Guardar la imagen sin compresión para la máxima calidad
        writer.SetCompressionLevel(0)
        writer.Write()
        # Desactivar el renderizado fuera de pantalla
        render_window.OffScreenRenderingOff()        
    
    def imagen_widget_vtk(vtkWidgetVisor, label_imagen):
        buffer = io.BytesIO()
        # Renderizar el vtkWidgetVisor en el buffer como una imagen PNG
        image = vtk.vtkWindowToImageFilter()
        image.SetInput(vtkWidgetVisor.GetRenderWindow())
        image.SetInputBufferTypeToRGB()
        # image.SetInputBufferTypeToRGBA()
        image.ReadFrontBufferOff()
        image.Update()
        writer = vtk.vtkPNGWriter()
        writer.SetWriteToMemory(True)  # Escribir la imagen en memoria en lugar de en un archivo
        writer.SetInputConnection(image.GetOutputPort())
        writer.Write()
        # Obtener los datos de la imagen desde el escritor
        buffer.write(writer.GetResult())
        # Reiniciar el cursor del búfer al inicio
        buffer.seek(0)
        # Crear una imagen QPixmap desde el búfer y mostrarla en el QLabel
        pixmap = QPixmap()
        pixmap.loadFromData(buffer.getvalue())
        label_imagen.setPixmap(pixmap)
        label_imagen.setScaledContents(True)
    
    def recortar_imagen(rutaimagen):
        imagen = Image.open(rutaimagen)
        # Recortar el espacio en blanco con margen
        imagen_recortada = MetodosGenerales.recortarImagenEspacioBlanco(imagen)
        # Cerrar la imagen original
        imagen.close()
        # Sobreescribir la imagen original con la imagen recortada
        imagen_recortada.save(rutaimagen)
    
    def guardarGraficaReporte(canvas, vista, tipo, entradatittle, entradacomenta, tipoequipo, idcomponente):
        _, buffer = GraficaReporte.capture_canvas_image(canvas, dpi=400)
        blob = None
        with Image.open(buffer) as imagen:
            imagen_recortada = MetodosGenerales.recortarImagenEspacioBlanco(imagen)
            # Convertir la imagen a un blob
            blob = MetodosGenerales.convertir_imagen_a_blob_buffer(imagen_recortada)
        # Capturar los datos del diálogo
        titulo = entradatittle.toPlainText()
        descripcion = entradacomenta.toPlainText()
        # Crear un diccionario con los datos
        data = {
            "id_componente": idcomponente,
            "vista_reporte": vista,
            "tipo_grafico": tipo,
            "imagen_grafica": blob,
            "titulo_grafica": titulo,
            "descripcion_grafica": descripcion,
            "tipo_reporte": "GENERAL",
            "tipo_equipo": tipoequipo
        }
        # Llamar a la función para guardar los datos en la base de datos
        respuesta = ReporteController.ctrlGuardarImagenReporte(data)
        return respuesta
    
    def capture_canvas_image(widgetgeneral, dpi=300):
        canvas = None
        tab_widget = widgetgeneral.findChild(QTabWidget)
        if tab_widget:
            current_index = tab_widget.currentIndex()
            widget_target = tab_widget.widget(current_index)
        else:
            widget_target = widgetgeneral
        canvas = widget_target.findChild(FigureCanvas)
        if canvas is None:
            canvas = widgetgeneral.findChild(FigureCanvas)
        if canvas is None:
            return None, None
        # Guardar la figura en un buffer
        buffer = io.BytesIO()
        canvas.figure.savefig(buffer, format='png', dpi=dpi)
        buffer.seek(0)
        # Convertir a QImage
        image = QImage()
        image.loadFromData(buffer.getvalue())
        return image, buffer
    