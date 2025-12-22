import vtk
import io
import numpy as np
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QDialog, QVBoxLayout, QLabel, QComboBox, QLineEdit, QTextEdit,
                               QPushButton, QRadioButton, QTabWidget)
from PySide6.QtUiTools import QUiLoader
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt
from PIL import Image
from utils.common.rutasarchivos import resource_path
from utils.common.alertas import mostrar_mensaje
from utils.common.metodosGenerales import MetodosGenerales
from controllers.ReporteController import ReporteController

class ReporteImage():
    
    def modalImagenReporte(canvaswidget, vista, tipo, titulografica, idproyecto, tipoequipo):
        loader = QUiLoader()
        ui_file_path = resource_path("ui/imagenesReporte.ui")
        ui_file = loader.load(ui_file_path, None)
        # Configurar el cuadro de diálogo
        dialog = QDialog()
        dialog.setWindowTitle("Imagen a Reporte Anexos")
        layout = QVBoxLayout()
        layout.addWidget(ui_file)
        dialog.setLayout(layout)        
        # Inicializar tools
        comboComponente = dialog.findChild(QComboBox, "combo_componentes")
        radioAnexo1 = dialog.findChild(QRadioButton, "radio_anexo1")
        radioAnexo2 = dialog.findChild(QRadioButton, "radio_anexo2")
        inputTitulo = dialog.findChild(QLineEdit, "input_titulo")
        inputDescri = dialog.findChild(QTextEdit, "imput_descripcion")
        labelGrafica = dialog.findChild(QLabel, "label_grafica")
        botonGuardar = dialog.findChild(QPushButton, "btn_guardar")
        MetodosGenerales.llenar_componentes_combo(idproyecto, comboComponente)
        inputTitulo.setText(titulografica)
        if vista == "Visor":
            ReporteImage.imagen_widget_vtk(canvaswidget, labelGrafica)
        else:
            imagen, _ = ReporteImage.capture_canvas_image(canvaswidget, dpi=72)
            if imagen:
                pixmap = QPixmap.fromImage(imagen)
                scaled_pixmap = pixmap.scaled(labelGrafica.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
                labelGrafica.setPixmap(scaled_pixmap)
                labelGrafica.adjustSize()
            else:
                botonGuardar.setEnabled(False)
        def confirmar_dialogo():
            if comboComponente.count() > 0:
                idcomponente = comboComponente.currentData()
                nombre_carpeta = "resources/images/graficatemporal.png"
                if vista == "Visor":
                    respuesta = ReporteImage.guardarGraficaVTK(canvaswidget, nombre_carpeta, vista, tipo, idcomponente, radioAnexo1, radioAnexo2, inputTitulo, inputDescri, tipoequipo)
                else:
                    respuesta = ReporteImage.guardarGraficaReporte(canvaswidget, vista, tipo, idcomponente, radioAnexo1, radioAnexo2, inputTitulo, inputDescri, tipoequipo)
                if respuesta is False:
                    mostrar_mensaje("ERROR AL GUARDAR", "No se pudo guardar la imagen.", "advertencia")
                dialog.close()
        # conectar señaeles
        botonGuardar.clicked.connect(confirmar_dialogo)
        dialog.exec()
    
    def guardarGraficaReporte(widget_grafico, vista, tipo, idcomponente, radioAnexo1, radioAnexo2, inputTitulo, inputDescri, tipoequipo):
        _, buffer = ReporteImage.capture_canvas_image(widget_grafico, dpi=400)
        blob = None
        with Image.open(buffer) as imagen:
            imagen_recortada = MetodosGenerales.recortarImagenEspacioBlanco(imagen)
            # Convertir la imagen a un blob
            blob = MetodosGenerales.convertir_imagen_a_blob_buffer(imagen_recortada)
        # Capturar los datos
        if radioAnexo1.isChecked():
            anexo = "ANEXO1"
        elif radioAnexo2.isChecked():
            anexo = "ANEXO2"
        titulo = inputTitulo.text()
        descripcion = inputDescri.toPlainText()
        # Crear un diccionario con los datos
        data = {
            "id_componente": idcomponente,
            "vista_reporte": vista,
            "tipo_grafico": tipo,
            "imagen_grafica": blob,
            "titulo_grafica": titulo,
            "descripcion_grafica": descripcion,
            "tipo_reporte": anexo,
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
    
    def guardarGraficaVTK(canvas, nombrecarpeta, vista, tipo, idcomponente, radioAnexo1, radioAnexo2, inputTitulo, inputDescri, tipoequipo):
        try:
            ReporteImage.save_image_vtk(canvas, nombrecarpeta)
            try:
                ReporteImage.recortar_imagen(nombrecarpeta)
            except Exception as e:
                print("Ocurrió un error al recortar la imagen:", e)
            image_path = resource_path(nombrecarpeta)
            if image_path:
                imagen_blob = MetodosGenerales.convertirImagenBlob(image_path)
                if radioAnexo1.isChecked():
                    anexo = "ANEXO1"
                elif radioAnexo2.isChecked():
                    anexo = "ANEXO2"
                titulo = inputTitulo.text()
                descripcion = inputDescri.toPlainText()
                data = {
                    "id_componente": idcomponente,
                    "vista_reporte": vista,
                    "tipo_grafico": tipo,
                    "imagen_grafica": imagen_blob,
                    "titulo_grafica": titulo,
                    "descripcion_grafica": descripcion,
                    "tipo_reporte": anexo,
                    "tipo_equipo": tipoequipo
                }
                respue = ReporteController.ctrlGuardarImagenReporte(data)
                if respue:
                    return True
            else:
                return False
        except Exception as e:
            return False
    
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
    
    def recortar_espacio_blanco_con_margen(imagen, margen_lateral=5, margen_vertical=20):
        # Convertir la imagen a escala de grises solo para el análisis de bordes
        imagen_gris = imagen.convert("L")
        # Convertir la imagen en escala de grises a un array NumPy
        imagen_np = np.array(imagen_gris)
        # Crear una máscara binaria donde 0 representa los píxeles blancos (valor alto en grises)
        mask = imagen_np < 240
        # Encontrar los límites de los píxeles no blancos
        coords = np.argwhere(mask)
        # Si no se encuentra contenido no blanco, devolver la imagen original
        if coords.size == 0:
            return imagen
        # Obtener los límites mínimo y máximo de los píxeles no blancos
        y_min, x_min = coords.min(axis=0)
        y_max, x_max = coords.max(axis=0)
        # Aplicar el margen y recortar la imagen
        left = max(0, x_min - margen_lateral)
        top = max(0, y_min - margen_vertical)
        right = min(imagen.width, x_max + margen_lateral)
        bottom = min(imagen.height, y_max + margen_vertical)
        # Recortar la imagen original (en color)
        imagen_recortada = imagen.crop((left, top, right, bottom))
        return imagen_recortada

    def recortar_imagen(rutaimagen):
        imagen = Image.open(rutaimagen)
        # Recortar el espacio en blanco con margen
        imagen_recortada = ReporteImage.recortar_espacio_blanco_con_margen(imagen)
        # Cerrar la imagen original
        imagen.close()
        # Sobreescribir la imagen original con la imagen recortada
        imagen_recortada.save(rutaimagen)
    