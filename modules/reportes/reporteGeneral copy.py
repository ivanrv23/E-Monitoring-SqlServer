import os
import io
import tempfile
from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QLineEdit, QTextEdit, QLabel)
from controllers .ReporteController import ReporteController
from controllers.EmpresaController import EmpresaController
from modules.reportes.tablaMulticell import PDF_MC_Table
from utils.common.metodosGenerales import MetodosGenerales
from utils.common.rutasarchivos import resource_path
class PDF(PDF_MC_Table):
    def __init__(self):
        super().__init__()
        self.set_margins(25, 25, 25)  # Margen izquierdo, superior y derecho en mm
        self.set_auto_page_break(True, margin=25)  # Margen inferior en mm
        self.header_img_blob = None 
        self.data = None 
        self.texto_pie = None 
        self.datos_firma=None

    def header(self):
        if self.page_no() > 1:  # Solo añadir encabezado a partir de la segunda página
            self._add_header_content(self.header_img_blob,self.data)

    def footer(self):
        if self.page_no() > 1:  # Solo añadir pie de página a partir de la segunda página
            self._add_footer_content(self.texto_pie, self.datos_firma)

    def first_page(self, img_blob, titulo, lugar, fecha):
        self.add_page()
        self._add_first_page_content(img_blob, titulo, lugar,fecha)

    def chapter_body(self, body):
        self._add_chapter_body(body)

    def third_page(self, title, img_path):
        self.add_page()
        self._add_third_page_content(title, img_path)

    def instrumentation_page(self,lista_prismas,lista_Inclinometros,lista_piezometros,lista_celdas,lista_acelerografos,lista_sondajes):
        self.add_page()
        self._add_instrumentation_content(lista_prismas,lista_Inclinometros,lista_piezometros,lista_celdas,lista_acelerografos,lista_sondajes)

    def interpretation_page(self, listaimagenes):
        if self.will_page_break():
            self.add_page()
        self._add_interpretation_content(listaimagenes)

    def conclusions_page(self, concusiones,recomendaciones):
        self.add_page()
        self._add_conclusions_content(concusiones,recomendaciones)

    def set_header(self, img_blob, data):
        self.header_img_blob = img_blob
        self.data=data
    
    def set_pie_texto(self, texto_pie, datos_firma):
        self.texto_pie=texto_pie
        self.datos_firma=datos_firma

    def _add_header_content(self, img_blob,data):
        self.set_font('Arial', 'B', 15)
        self.set_y(13)  # Ajustar la posición vertical

        # Añadir la imagen si existe
        if img_blob:
            try:
                img = Image.open(io.BytesIO(img_blob))
                img_width, img_height = img.size
                max_width, max_height = 50, 20  # Ajusta el tamaño máximo de la imagen según sea necesario
                scale_width = max_width / img_width
                scale_height = max_height / img_height
                scale = min(scale_width, scale_height)
                new_width = img_width * scale
                new_height = img_height * scale

                # Guardar la imagen en un archivo temporal
                temp_img_path = tempfile.mktemp(suffix='.png')
                img.save(temp_img_path, format='PNG')

                # Añadir la imagen al PDF
                self.image(temp_img_path, x=25, y=13, w=new_width, h=new_height)

                # Eliminar el archivo temporal
                os.remove(temp_img_path)
            except Exception as e:
                self.set_font('Arial', 'B', 12)
                self.set_y(13)
                self.cell(0, 10, 'Error al cargar la imagen', 0, 1, 'C')
        self._add_title(80, data[1])
        self._draw_line(25, 33, self.w - 25, 33, 0.2, (200, 200, 200))
        self.ln(25)
        if self.page_no() == 2:  # Solo añadir información adicional en la segunda página
            self._add_additional_info(data)

    def _add_footer_content(self, texto_pie, datos_firma):
        self.set_y(-25)
        self._draw_line(25, self.get_y(), self.w - 25, self.get_y(), 0.2, (200, 200, 200))
        self._add_footer_text(texto_pie)
        if self.page_no() == 2:  # Solo añadir firma en la segunda página
            self.set_y(-65)
            # Añadir la imagen de la firma si existe
            if datos_firma:
                if datos_firma[6]:
                    try:
                        img = Image.open(io.BytesIO(datos_firma[6]))
                        img_width, img_height = img.size
                        max_width, max_height = 30, 20  # Ajusta el tamaño máximo de la imagen según sea necesario
                        scale_width = max_width / img_width
                        scale_height = max_height / img_height
                        scale = min(scale_width, scale_height)
                        new_width = img_width * scale
                        new_height = img_height * scale
                        # Guardar la imagen en un archivo temporal
                        temp_img_path = tempfile.mktemp(suffix='.png')
                        img.save(temp_img_path, format='PNG')
                        # Añadir la imagen al PDF
                        self.image(temp_img_path, x=25, y=self.get_y(), w=new_width, h=new_height)
                        # Eliminar el archivo temporal
                        os.remove(temp_img_path)
                    except Exception as e:
                        self.set_font('Arial', 'B', 12)
                        self.set_y(self.get_y() + 22)
                        self.cell(0, 10, 'Error al cargar la imagen de la firma', 0, 1, 'C')
                else:
                    self.set_font('Arial', 'B', 12)
                    self.set_y(self.get_y() + 22)
                    self.cell(0, 10, 'Error al cargar la imagen de la firma', 0, 1, 'C')
                # Añadir el texto de la firma
                self._add_signature_text(25, self.get_y() + 22, f'{datos_firma[1]}\n{datos_firma[2]}')
    
    def _add_first_page_content(self, img_blob,titulo,lugar,fecha):
        self.set_font('Arial', 'B', 12)

        # Añadir la imagen si existe
        if img_blob:
            try:
                img = Image.open(io.BytesIO(img_blob))
                img_width, img_height = img.size
                max_width, max_height = 50, 50  # Ajusta el tamaño máximo de la imagen según sea necesario
                scale_width = max_width / img_width
                scale_height = max_height / img_height
                scale = min(scale_width, scale_height)
                new_width = img_width * scale
                new_height = img_height * scale

                # Guardar la imagen en un archivo temporal
                temp_img_path = tempfile.mktemp(suffix='.png')
                img.save(temp_img_path, format='PNG')
                # Añadir la imagen al PDF
                self.image(temp_img_path, x=(self.w - new_width) / 2, y=(self.h - new_height) / 3, w=new_width, h=new_height)

                # Eliminar el archivo temporal
                os.remove(temp_img_path)
            except Exception as e:
                self.set_font('Arial', 'B', 12)
                self.set_y((self.h - 50) / 3)
                self.cell(0, 10, 'Error al cargar la imagen', 0, 1, 'C')

        self._add_centered_text((self.h - 50) / 3 + 60, titulo)
        self._add_centered_text((self.h - 50) / 3 + 70, lugar)
        self._add_centered_text((self.h - 50) / 3 + 80, f'MES:{fecha}')

    def _add_chapter_body(self, body):
        self.set_font('Arial', '', 12)
        self.multi_cell(0, 10, body)
        self.ln()

    def _add_third_page_content(self, title, img_blob):
        self.ln(20)  # Añadir un espacio adicional después del encabezado
        self.set_font('Arial', 'B', 16)
        self._add_centered_text(40, title)
        # Ajustar la posición de la imagen para que esté más cerca del título
        img_y = 60  # Ajusta esta posición según sea necesario
        img_x = (self.w - 160) / 2  # Ajusta el ancho de la imagen según sea necesario
        if img_blob:
            try:
                img = Image.open(io.BytesIO(img_blob))
                img_width, img_height = img.size
                max_width, max_height = 160, 160  # Ajusta el tamaño máximo de la imagen según sea necesario
                scale_width = max_width / img_width
                scale_height = max_height / img_height
                scale = min(scale_width, scale_height)
                new_width = img_width * scale
                new_height = img_height * scale

                # Guardar la imagen en un archivo temporal
                temp_img_path = tempfile.mktemp(suffix='.png')
                img.save(temp_img_path, format='PNG')
                # Añadir la imagen al PDF
                self.image(temp_img_path, x=img_x, y=img_y, w=new_width, h=new_height)

                # Eliminar el archivo temporal
                os.remove(temp_img_path)
            except Exception as e:
                self.set_font('Arial', 'B', 12)
                self.set_y(img_y)
                self.cell(50, 10, 'Error al cargar la imagen', 0, 0, 'C')  # Celda pequeña para el error
        else:
            self.set_font('Arial', 'B', 12)
            self.set_y(img_y)
            self.cell(50, 10, 'Error al cargar la imagen', 0, 0, 'C')  # Celda pequeña para el error

        # Calcular la posición de la descripción justo después de la imagen
        # description_y = img_y + (new_height if os.path.exists(img_path) else 10) + 10  # Ajusta el espacio después de la imagen según sea necesario
        # self.set_font('Arial', '', 12)
        # self.set_y(description_y)
        # self.multi_cell(0, 6, description)

    def _add_instrumentation_content(self, lista_prismas, lista_Inclinometros, lista_piezometros, lista_celdas, lista_acelerografos, lista_sondajes):
        self.set_font('Arial', 'B', 16)
        self.set_x(25)  # Posición a la izquierda
        self.cell(0, 10, '1. Instrumentación Geotécnica', 0, 1, 'L')
        self.ln(5)  # Reducir el espacio entre el título y los subtítulos
        # Lista de instrumentos con sus respectivos datos y títulos
        instrumentos = [
            (lista_prismas, 'Prismas'),
            (lista_Inclinometros, 'Inclinómetros'),
            (lista_piezometros, 'Piezómetros'),
            (lista_celdas, 'Celdas'),
            (lista_acelerografos, 'Acelerógrafos'),
            (lista_sondajes, 'Sondajes TDR')
        ]
        # Contador para la numeración de las secciones
        section_counter = 1
        for datos, titulo in instrumentos:
            if datos:  # Solo generar la tabla si hay datos
                self.set_font('Arial', 'B', 12)
                self.set_x(25)  # Posición a la izquierda
                self.cell(0, 10, f'1.{section_counter} {titulo}', 0, 1, 'L')
                self.ln(5)
                # Preparar los datos para la tabla
                headers = ['ID', 'Este', 'Norte', 'Elevación', 'Ubicación']
                data = [
                    [id_instrumento, este, norte, elevacion, ubicacion]
                    for id_instrumento, este, norte, elevacion, ubicacion in datos
                ]
                # Definir anchos de columnas y alineaciones
                self.set_widths([40, 30, 30, 30, 30])
                self.set_aligns(["C", "C", "C", "C", "C"])
                # Añadir encabezado con color de fondo
                self.header_row(headers, fill_color=(200, 200, 200))
                # Añadir filas de datos
                for row in data:
                    self.row(row)
                self.ln(10)
                # Incrementar el contador de secciones
                section_counter += 1
    
    def _add_interpretation_content(self, listaimagenes):
        self.set_font('Arial', 'B', 16)
        self.set_x(25)  # Posición a la izquierda
        self.cell(0, 10, '2. Interpretación', 0, 1, 'L')
        self.ln(6)
        # Crear una tabla de tres filas y una columna
        for imagen in listaimagenes:
            title = imagen[5]
            img_blob = imagen[4]
            description = imagen[6]
            # mostrar imagen
            self.set_font('Arial', 'B', 12)
            self.cell(0, 10, title, 1, 1, 'C')  # Título
            try:
                margin_inside = 10
                # Abrir imagen desde BLOB
                img = Image.open(io.BytesIO(img_blob))
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                img_width, img_height = img.size
                max_width = self.w - 40 - (margin_inside * 2)
                scale = max_width / img_width
                new_width = img_width * scale
                new_height = img_height * scale
                cell_height = new_height + (margin_inside * 2)
                self.cell(0, cell_height, '', 1, 1, 'C')
                adjusted_y = self.get_y() - cell_height + margin_inside
                adjusted_x = (self.w - new_width) / 2
                temp_img_io = io.BytesIO()
                #img.save(temp_img_io, format='PNG')
                img.save(temp_img_io, format='JPEG', quality=85, optimize=True)
                temp_img_io.seek(0)
                # Crear un archivo temporal solo si es necesario
                temp_img_path = tempfile.mktemp(suffix='.jpg')
                with open(temp_img_path, 'wb') as f:
                    f.write(temp_img_io.getvalue())
                self.image(temp_img_path, x=adjusted_x, y=adjusted_y, w=new_width)
                # Eliminar el archivo temporal
                os.remove(temp_img_path)
            except Exception as e:
                self.set_font('Arial', 'B', 12)
                self.cell(0, 6, f'Error al cargar la imagen {e}', 1, 1, 'C')
            self.set_font('Arial', '', 12)
            self.multi_cell(0, 6, description, 1, 'J')  # Descripción
            self.ln(6)
    
    def _add_conclusions_content(self, conclusions, recommendations):
        self.set_font('Arial', 'B', 16)
        self.set_x(25)  # Posición a la izquierda
        self.cell(0, 10, '3. Conclusiones y Recomendaciones', 0, 1, 'L')
        self.ln(10)

        # Añadir conclusiones
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Conclusiones', 0, 1, 'L')
        self.ln(5)

        self.set_font('Arial', '', 12)
        conclusion_paragraphs = conclusions.split('\n')
        for paragraph in conclusion_paragraphs:
            self.multi_cell(0, 6, paragraph)
            self.ln(5)

        self.ln(10)

        # Añadir recomendaciones
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Recomendaciones', 0, 1, 'L')
        self.ln(5)

        self.set_font('Arial', '', 12)
        recommendation_paragraphs = recommendations.split('\n')
        for paragraph in recommendation_paragraphs:
            self.multi_cell(0, 6, paragraph)
            self.ln(5)

    def _add_logo(self, img_path, x, y, max_width, max_height):
        ruta_img=resource_path(img_path)
        if os.path.exists(ruta_img):
            img = Image.open(ruta_img)
            img_width, img_height = img.size
            scale_width = max_width / img_width
            scale_height = max_height / img_height
            scale = min(scale_width, scale_height)
            new_width = img_width * scale
            new_height = img_height * scale
            self.image(ruta_img, x, y, new_width, new_height)
        else:
            self.set_font('Arial', 'B', 12)
            self.set_y(y)
            self.cell(50, 10, 'Error al cargar la imagen', 0, 0, 'C')  # Celda pequeña para el error

    def _add_title(self, x, title):
        self.set_x(x)
        self.cell(0, 20, title, 0, 0, 'R')

    def _draw_line(self, x1, y1, x2, y2, width, color):
        self.set_line_width(width)
        self.set_draw_color(*color)
        self.line(x1, y1, x2, y2)

    def _add_additional_info(self,data):

        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, data[3], 0, 1, 'C')
        self.ln(5)
        data = [
            ["Para", ":", data[6]],
            ["De", ":", data[7]],
            ["Cc", ":", data[8]],
            ["Fecha", ":", data[5]],
            ["Asunto", ":", data[9]]
        ]
        max_label_width = max(self.get_string_width(row[0]) for row in data) + 5
        colon_width = 5
        content_width = self.w - max_label_width - colon_width - 40
        start_x = 40
        for row in data:
            self.set_x(start_x)
            self.set_font('Arial', 'B', 12)
            self.cell(max_label_width, 10, row[0], 0, 0, 'L')
            self.cell(colon_width, 10, row[1], 0, 0, 'C')
            self.set_font('Arial', '', 12)
            self.cell(content_width, 10, row[2], 0, 1, 'L')
        self.ln(10)

    def _add_signature(self, img_path, x, y, max_width, max_height):
        ruta_img=resource_path(img_path)
        if os.path.exists(ruta_img):
            img = Image.open(ruta_img)
            img_width, img_height = img.size
            scale_width = max_width / img_width
            scale_height = max_height / img_height
            scale = min(scale_width, scale_height)
            new_width = img_width * scale
            new_height = img_height * scale
            self.image(ruta_img, x, y, new_width, new_height)
        else:
            self.set_font('Arial', 'B', 12)
            self.set_y(y)
            self.cell(50, 10, 'Error al cargar la imagen', 0, 0, 'C')  # Celda pequeña para el error

    def _add_signature_text(self, x, y, text):
        self.set_y(y)
        self.set_x(x)
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 5, text)

    def _add_footer_text(self,texto_pie):
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, texto_pie, 0, 0, 'L')
        self.set_x(self.w - 25)
        self.cell(0, 10, '%s' % self.page_no(), 0, 0, 'R')

    def _add_centered_text(self, y, text):
        self.set_y(y)
        self.cell(0, 10, text, 0, 1, 'C')

    def will_page_break(self):
        # Verificar si la posición actual más el espacio necesario para la sección de interpretación excede el límite de la página
        current_y = self.get_y()
        needed_height = 10 + 10 + 160 + 10 + 10 * 3  # Espacio para título, subtítulo, imagen, espacio y descripción
        page_height = self.h - self.b_margin - self.t_margin
        return current_y + needed_height > page_height
    
class ReporteGeneral:
    
    def guardarFormularioReporte(main,idproyecto, file_patch):
        data = ReporteGeneral.obtenerValoresFormulario(main, idproyecto, file_patch)
        ReporteController.ctrlGuardarInformacionReporte(data)
    
    def cargarDataFormulariosReporte(main, idproyecto):
        general = ReporteController.ctrlListarDatosReporteGeneral(idproyecto)
        if general:
            main.findChild(QLineEdit, "input_encabezado").setText(general[2])
            main.findChild(QLineEdit, "input_pie_pagina").setText(general[3])
            main.findChild(QLineEdit, "input_titulo").setText(general[4])
            main.findChild(QLineEdit, "input_lugar").setText(general[5])
            main.findChild(QLineEdit, "input_mes_reporte").setText(general[6])
            main.findChild(QLineEdit, "input_para").setText(general[7])
            main.findChild(QLineEdit, "input_de").setText(general[8])
            main.findChild(QLineEdit, "input_cc").setText(general[9])
            main.findChild(QLineEdit, "input_asunto").setText(general[10])
            main.findChild(QTextEdit, "input_descripcion").setPlainText(general[11])
            main.findChild(QTextEdit, "input_conclusiones").setPlainText(general[12])
            main.findChild(QTextEdit, "input_recomendaciones").setPlainText(general[13])
            if general[14]:
                pixmap = MetodosGenerales.convertir_blob_a_pixmap(general[14])
                scaled_pixmap = pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                main.findChild(QLabel, "label_imagen").setPixmap(scaled_pixmap)
    
    def obtenerValoresFormulario(main, idproyecto, file_patch):
        encabezado = main.findChild(QLineEdit, "input_encabezado").text()
        pie = main.findChild(QLineEdit, "input_pie_pagina").text()        
        titulo = main.findChild(QLineEdit, "input_titulo").text()
        lugar = main.findChild(QLineEdit, "input_lugar").text()
        mes = main.findChild(QLineEdit, "input_mes_reporte").text()
        para = main.findChild(QLineEdit, "input_para").text()
        de = main.findChild(QLineEdit, "input_de").text()
        cc = main.findChild(QLineEdit, "input_cc").text()
        asunto = main.findChild(QLineEdit, "input_asunto").text()
        descripcion = main.findChild(QTextEdit, "input_descripcion").toPlainText()
        conclusiones = main.findChild(QTextEdit, "input_conclusiones").toPlainText()
        recomendaciones = main.findChild(QTextEdit, "input_recomendaciones").toPlainText()
        imagen_componente = file_patch
        data = [idproyecto,encabezado, pie, titulo, lugar,mes, para, de, cc, asunto, descripcion, conclusiones, recomendaciones, imagen_componente]
        return data
    
    def generarReporte(main,idproyecto,file_patch,id_componente):
        #Obtener Informacion empresa
        datos_empresa, lic = EmpresaController.ctrlObtenerDatosEmpresa()
        data = ReporteGeneral.obtenerValoresFormulario(main,idproyecto,file_patch)
        datosFirma = ReporteController.ctrlObtenerDatosFirma(idproyecto)
        lista_prismas = ReporteController.ctrlObtenerListaPrismas(idproyecto,id_componente)
        lista_Inclinometros = ReporteController.ctrlObtenerListaInclinometros(idproyecto,id_componente)
        lista_piezometros = ReporteController.ctrlObtenerListaPiezometros(idproyecto,id_componente)
        lista_celdas = ReporteController.ctrlObtenerListaCeldas(idproyecto,id_componente)
        lista_acelerografos = ReporteController.ctrlObtenerListaAcelerografos(idproyecto,id_componente)
        lista_sondajes = ReporteController.ctrlObtenerListaSondajesTDR(idproyecto,id_componente)
        imagenesReporte = ReporteController.ctrlObtenerListaImagenesReporte(id_componente)
        # Crear instancia de PDF
        pdf = PDF()
        pdf.set_header(datos_empresa[5], data)
        pdf.set_pie_texto(data[2], datosFirma)
        pdf.first_page(datos_empresa[5], data[3], data[4], data[5])
        pdf.add_page()
        # Cuerpo del capítulo
        pdf.chapter_body(data[10])
        # Tercera página
        pdf.third_page(data[4], data[13])
        # Página de Instrumentación Geotécnica
        pdf.instrumentation_page(lista_prismas,lista_Inclinometros,lista_piezometros,lista_celdas,lista_acelerografos,lista_sondajes)
        # Página de Interpretación
        if imagenesReporte:
            pdf.interpretation_page(imagenesReporte)
        pdf.conclusions_page(data[11], data[12])
        # Guardar el PDF
        ruta_salida=resource_path('modules/reportes/reporte_general.pdf')
        pdf.output(ruta_salida)
