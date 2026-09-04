import fitz  # PyMuPDF
import os
import shutil
import win32com.client
import pythoncom
from PySide6.QtCore import QDate
from PySide6.QtWidgets import (QPushButton, QFrame, QWidget, QScrollArea, QVBoxLayout, QLabel, QLineEdit, QMessageBox,
                        QRadioButton, QFileDialog, QTabWidget, QComboBox, QDialog, QHBoxLayout, QDateEdit, QTextEdit, QPlainTextEdit)
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt, QThread, Signal
from utils.common.rutasarchivos import resource_path
from utils.generic.cargariconos import cargarIcono
from utils.common.alertas import mostrar_mensaje
from utils.shared.loading import LoadingView
from modules.reportes.reporteGeneral import ReporteGeneral
from modules.reportes.reporte import Reporte
from utils.common.metodosGenerales import MetodosGenerales
from modules.reportes.anexo1 import Anexo1
from modules.reportes.anexo2 import Anexo2
from modules.reportes.generarAnexo1 import ReporteAnexo1
from modules.reportes.generarAnexo2 import ReporteAnexo2

class PDFViewerWidget(QWidget):
    def __init__(self, parent=None, ruta_pdf='CONTRATO.pdf'):
        super().__init__(parent)
        self.pdf_document = None
        self.ruta_pdf = ruta_pdf
        self.zoom_factor = 1.0
        self.current_page = 0

        # Crear el área de scroll
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)

        # Contenedor para varias páginas
        self.page_container = QWidget()
        self.page_layout = QVBoxLayout(self.page_container)
        self.page_layout.setSpacing(20)

        # Añadir el contenedor al ScrollArea
        self.scroll_area.setWidget(self.page_container)

        # Layout del widget principal
        layout = QVBoxLayout(self)
        layout.addWidget(self.scroll_area)
        self.setLayout(layout)

        # Mostrar las páginas iniciales
        self.show_pages()

    def show_pages(self):
        # Limpiar páginas anteriores
        for i in reversed(range(self.page_layout.count())):
            widget_to_remove = self.page_layout.itemAt(i).widget()
            self.page_layout.removeWidget(widget_to_remove)
            widget_to_remove.deleteLater()

        # Abrir el documento PDF
        self.pdf_document = fitz.open(self.ruta_pdf)

        for page_index in range(self.pdf_document.page_count):
            page = self.pdf_document.load_page(page_index)
            pix = page.get_pixmap(matrix=fitz.Matrix(self.zoom_factor, self.zoom_factor))

            image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(image)

            pdf_label = QLabel()
            pdf_label.setPixmap(pixmap)
            pdf_label.setAlignment(Qt.AlignCenter)
            pdf_label.resize(pixmap.size())

            self.page_layout.addWidget(pdf_label)

        # Cerrar el documento PDF para liberar el archivo
        self.pdf_document.close()

    def zoom_in(self):
        self.zoom_factor += 0.1
        self.show_pages()

    def zoom_out(self):
        self.zoom_factor = max(0.1, self.zoom_factor - 0.1)
        self.show_pages()

    def wheelEvent(self, event):
        # validar existencia del documento
        if not hasattr(self, 'pdf_document') or self.pdf_document is None or self.pdf_document.is_closed:
            return
        # Navegar entre páginas
        if event.angleDelta().y() > 0:
            if self.current_page > 0:
                self.current_page -= 1
        else:
            if self.current_page < self.pdf_document.page_count - 1:
                self.current_page += 1
        # Ajustar scroll
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().value() + (-event.angleDelta().y())
        )
        event.accept()
    
class ReporteView:
    main = None
    idproyecto = None
    nameproyecto = "SIN PROYECTO"
    estadochecklist = True
    estadoPagina = True
    imagePathGeneral, imagePathAnexo1, imagePathAnexo2 = None, None, None
    
    def inicializarVistaReporte(main, proyectoid, proyectoname):
        ReporteView.main = main
        ReporteView.idproyecto = proyectoid
        ReporteView.nameproyecto = proyectoname
        if ReporteView.estadochecklist:
            Reporte.llenarComboComponentesReporte(ReporteView.idproyecto, ReporteView.main)
            ReporteView.llenarDataFormulariosReportes()
            fecha_hoy = QDate.currentDate()
            año_actual = fecha_hoy.year()
            mes_actual = fecha_hoy.month()
            primer_dia = QDate(año_actual, mes_actual, 1)
            ultimo_dia = QDate(año_actual, mes_actual, fecha_hoy.daysInMonth())
            main.findChild(QDateEdit, "date_fecha_inicio_reportes").setDate(primer_dia)
            main.findChild(QDateEdit, "date_fecha_final_reportes").setDate(ultimo_dia)
            ReporteView.estadochecklist = False
        if ReporteView.estadoPagina:
            btn_ocular_mostrar_reporte = main.findChild(QPushButton, "btn_ocultar_vista_previa_reporte")
            btn_ocular_mostrar_reporte.clicked.connect(lambda: ReporteView.mostrar_ocultar_vista_previa(main))
            btn_generar_reporte = main.findChild(QPushButton, "btn_generar_reporte")
            btn_generar_reporte.clicked.connect(lambda: ReporteView.crearReporteGeneral(main))
            btn_imagen_reporte_general = main.findChild(QPushButton, "btn_imagen_reportegeneral")
            btn_imagen_reporte_general.clicked.connect(lambda: ReporteView.cargarImagenComponente("General"))
            btn_imagen_general_anexo1 = main.findChild(QPushButton, "btn_cargar_imagen_componente_A1")
            btn_imagen_general_anexo1.clicked.connect(lambda: ReporteView.cargarImagenComponente("Anexo1"))
            btn_imagen_general_anexo2 = main.findChild(QPushButton, "btn_cargar_imagen_componente_A2")
            btn_imagen_general_anexo2.clicked.connect(lambda: ReporteView.cargarImagenComponente("Anexo2"))
            btn_guardar_rg_db = main.findChild(QPushButton, "btn_guardar_reporte")
            btn_guardar_rg_db.clicked.connect(lambda: ReporteView.guardarReportesDatabase(main))
            btn_regitrar_firma = main.findChild(QPushButton, "btn_cargar_firma_reporte")
            btn_regitrar_firma.clicked.connect(ReporteView.registrarFirmaReporte)
            btn_exportar_reporte_general = main.findChild(QPushButton, "btn_exportar_reporte")
            btn_exportar_reporte_general.clicked.connect(lambda: ReporteView.exportarReporte(main))
            comboComponentesReporte = main.findChild(QComboBox, "cb_componentes_anexos")
            comboComponentesReporte.activated.connect(ReporteView.actualizarDataAnexosResumenEjecutivo)
            btn_lista_images = main.findChild(QPushButton, "btn_imagenes_reporte")
            btn_lista_images.clicked.connect(ReporteView.actualizarListaImagenesReporte)
            ReporteView.estadoPagina = False
    
    def llenarDataFormulariosReportes():
        ReporteGeneral.cargarDataFormulariosReporte(ReporteView.main, ReporteView.idproyecto)
        ReporteAnexo1.cargarDataFormulariosAnexoGeneral(ReporteView.main, ReporteView.idproyecto)
        ReporteAnexo1.cargarInformacionResumenEjecutivoAnexo(ReporteView.main)
        ReporteAnexo2.cargarDataFormulariosAnexoGeneral(ReporteView.main, ReporteView.idproyecto)
        ReporteAnexo2.cargarInformacionResumenEjecutivoAnexo(ReporteView.main)
        ReporteView.cargarValoresAnexos()
    
    def actualizarDataAnexosResumenEjecutivo():
        ReporteAnexo1.cargarInformacionResumenEjecutivoAnexo(ReporteView.main)
        ReporteAnexo2.cargarInformacionResumenEjecutivoAnexo(ReporteView.main)
        ReporteView.cargarValoresAnexos()
    
    def mostrarDialogoExportacion():
        dialog = QDialog()
        dialog.setWindowTitle("Exportar Reporte")
        layout = QHBoxLayout ()
        pdf_button = QPushButton("PDF")
        word_button = QPushButton("Word")
        layout.addWidget(pdf_button)
        layout.addWidget(word_button)
        dialog.setLayout(layout)
        # Variable para almacenar la elección del usuario
        choice = None
        def on_pdf_clicked():
            nonlocal choice
            choice = "PDF"
            dialog.accept()
        def on_word_clicked():
            nonlocal choice
            choice = "Word"
            dialog.accept()
        pdf_button.clicked.connect(on_pdf_clicked)
        word_button.clicked.connect(on_word_clicked)
        # Mostrar el diálogo y esperar la respuesta del usuario
        dialog.exec()
        return choice

    def exportarReporte(main):
        if not hasattr(ReporteView, 'idproyecto') or not ReporteView.idproyecto:
            return

        tab_widget_reporte = main.findChild(QTabWidget, "tabWidget_reporte")
        if not tab_widget_reporte:
            return

        current_index = tab_widget_reporte.currentIndex()
        if current_index not in [0, 1, 2]:
            return

        choice = ReporteView.mostrarDialogoExportacion()
        if choice not in ["PDF", "Word"]:
            return

        # Diccionario para mapear índices y formatos a rutas de recursos
        resource_map = {
            0: {
                "PDF": 'modules/reportes/reporte_general.pdf',
                "Word": 'modules/reportes/reporte_general.docx'
            },
            1: {
                "PDF": 'modules/reportes/ANEXO1.pdf',
                "Word": 'modules/reportes/ANEXO1.docx'
            },
            2: {
                "PDF": 'modules/reportes/ANEXO2.pdf',
                "Word": 'modules/reportes/ANEXO2.docx'
            }
        }

        resource_path_value = resource_map[current_index][choice]
        ReporteView.guardarReporteTipo(resource_path(resource_path_value))
                
    ######## REPORTE GENERAL ########                    
    def guardarReporteTipo(file):
        # Obtener la ruta absoluta del archivo original
        ruta_original = resource_path(file)
        # Verificar si el archivo original existe
        if not os.path.isfile(ruta_original):
            raise FileNotFoundError(f"El archivo no existe: {ruta_original}")
        # Obtener la extensión del archivo original
        extension = os.path.splitext(ruta_original)[1][1:]  # Obtiene la extensión sin el punto
        # Abrir un cuadro de diálogo para seleccionar la ubicación y el nombre del archivo
        ruta_guardado, _ = QFileDialog.getSaveFileName(
            None,  # Ventana padre (None para que sea independiente)
            "Guardar reporte como",  # Título del diálogo
            os.path.basename(ruta_original),  # Nombre predeterminado con extensión
            f"{extension.upper()} Files (*.{extension})"  # Filtro de archivos basado en la extensión
        )
        # Si el usuario seleccionó una ruta (no cerró el diálogo)
        if ruta_guardado:
            shutil.copy(ruta_original, ruta_guardado)
            mostrar_mensaje("Reporte Guardado", f"Se guardó en: {ruta_guardado}", "informacion")
    
    def registrarFirmaReporte():
        Reporte.registrarFirmaReportes(ReporteView.idproyecto)
    
    def mostrar_ocultar_vista_previa(main):
        ocultar = "resources/iconos/fontawesome/solid/eye-slash.svg"
        mostrar = "resources/iconos/fontawesome/solid/eye.svg"
        btn_ocultar_mostrar_reporte = main.findChild(QPushButton, "btn_ocultar_vista_previa_reporte")
        frame_vista_previa_reporte = main.findChild(QFrame, "frame_vista_previa_reporte")
        if frame_vista_previa_reporte.isVisible():
            frame_vista_previa_reporte.hide()
            cargarIcono(btn_ocultar_mostrar_reporte, ocultar)
        else:
            frame_vista_previa_reporte.show()
            cargarIcono(btn_ocultar_mostrar_reporte, mostrar)
            
    def cargarImagenComponente(tipo):
        if tipo == "General":
            input_nombre = ReporteView.main.findChild(QLineEdit, "input_imagen")
            lb_vistaPrevia = ReporteView.main.findChild(QLabel, "label_imagen")
            ReporteView.imagePathGeneral = MetodosGenerales.cargarImagenLocal(lb_vistaPrevia, input_nombre)
        elif tipo == "Anexo1":
            lb_vistaPrevia = ReporteView.main.findChild(QLabel, "lb_imagen_componente_A1")
            ReporteView.imagePathAnexo1 = MetodosGenerales.cargarImagenLocal(lb_vistaPrevia)
        elif tipo == "Anexo2":
            lb_vistaPrevia = ReporteView.main.findChild(QLabel, "lb_imagen_componente_A2")
            ReporteView.imagePathAnexo2 = MetodosGenerales.cargarImagenLocal(lb_vistaPrevia)
    
    def crearReporteGeneral(main):
        if ReporteView.idproyecto:
            tab_widget_reporte = main.findChild(QTabWidget, "tabWidget_reporte")
            idcomponente = main.findChild(QComboBox, "cb_componentes_anexos").currentData()
            current_index = tab_widget_reporte.currentIndex()
            # Mostrar diálogo de advertencia
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle("Advertencia")
            msg_box.setText("Debe cerrar cualquier documento WORD que tenga abierto, ya que puede interferir con el proceso de generar el reporte.")
            msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            result = msg_box.exec()
            if result == QMessageBox.Cancel:
                return  # Salir de la función si el usuario cancela
            if current_index == 0:
                imagen_componente = MetodosGenerales.convertir_imagen_a_blob(ReporteView.imagePathGeneral)
                # Iniciar Hilo
                loading = LoadingView.mostrarLoading()
                def on_thread_complete_general():
                    loading.close()
                genera_pdf = GenerarReporteGeneralThread(main, ReporteView.idproyecto, imagen_componente, idcomponente)
                genera_pdf.task_finishReporteGeneral.connect(on_thread_complete_general)
                genera_pdf.start()
                loading.exec()
                # mostrar pdf
                ruta_reporte = resource_path('modules/reportes/reporte_general.pdf')
                ReporteView.mostrarReporte(main, ruta_reporte)
            elif current_index == 1:
                dateFechaInicio = main.findChild(QDateEdit, "date_fecha_inicio_reportes")
                dateFechaFinal = main.findChild(QDateEdit, "date_fecha_final_reportes")
                fechainicio = dateFechaInicio.date()
                fechafinal = dateFechaFinal.date()
                ReporteAnexo1.generarReporte(ReporteView.idproyecto, fechainicio, fechafinal)
                relative_word_path = 'modules/reportes/ANEXO1.docx'
                relative_pdf_path = 'modules/reportes/ANEXO1.pdf'
                # Iniciar Hilo convertir
                loading = LoadingView.mostrarLoading()
                def on_thread_complete_pdfanexo1():
                    loading.close()
                anexo1_pdf = MostrarReporteAnexo1Thread(relative_word_path, relative_pdf_path)
                anexo1_pdf.task_finishAnexo1Report.connect(on_thread_complete_pdfanexo1)
                anexo1_pdf.start()
                loading.exec()
                # Mostrar pdf
                ReporteView.mostrarReporte(main, relative_pdf_path)
            elif current_index == 2:
                dateFechaInicio = main.findChild(QDateEdit, "date_fecha_inicio_reportes")
                dateFechaFinal = main.findChild(QDateEdit, "date_fecha_final_reportes")
                fechainicio = dateFechaInicio.date()
                fechafinal = dateFechaFinal.date()
                ReporteAnexo2.generarReporte(ReporteView.idproyecto, fechainicio, fechafinal)
                relative_word_path = 'modules/reportes/ANEXO2.docx'
                relative_pdf_path = 'modules/reportes/ANEXO2.pdf'
                # Iniciar Hilo convertir
                loading = LoadingView.mostrarLoading()
                def on_thread_complete_pdfanexo2():
                    loading.close()
                anexo2_pdf = MostrarReporteAnexo2Thread(relative_word_path, relative_pdf_path)
                anexo2_pdf.task_finishAnexo2Report.connect(on_thread_complete_pdfanexo2)
                anexo2_pdf.start()
                loading.exec()
                # Mostrar pdf
                ReporteView.mostrarReporte(main, relative_pdf_path)
            else:
                print('Historial de Reportes')

    @staticmethod
    def convertir_docx_a_pdf(input_file, output_file):
        # 1. Inicializar COM para este hilo (OBLIGATORIO)
        pythoncom.CoInitialize()

        input_path = os.path.abspath(resource_path(input_file))
        output_path = os.path.abspath(resource_path(output_file))
        
        word = None
        try:
            # Inicializar Word
            word = win32com.client.Dispatch("Word.Application")
            
            # 2. Protección contra el error de visibilidad
            try:
                word.Visible = False
                word.DisplayAlerts = False
            except Exception:
                pass # Si falla ocultarse, ignoramos el error y seguimos

            # Abrir el archivo .docx
            doc = word.Documents.Open(input_path)

            # Exportar a PDF
            doc.ExportAsFixedFormat(
                OutputFileName=output_path,
                ExportFormat=17,  # 17 es PDF
                OpenAfterExport=False,
                OptimizeFor=0,
                Item=7,
                IncludeDocProps=True,
                KeepIRM=True,
                CreateBookmarks=1,
                DocStructureTags=True,
                BitmapMissingFonts=True,
                UseISO19005_1=False
            )
            doc.Close(False)
            return True

        except Exception as e:
            print(f"Error convirtiendo PDF: {e}")
            return False
            
        finally:
            # Asegurarse de cerrar Word si se abrió
            if word:
                try:
                    word.Quit()
                except Exception:
                    pass
            # 3. Liberar recursos COM del hilo (OBLIGATORIO)
            pythoncom.CoUninitialize()
    
    def guardarReportesDatabase(main):
        if ReporteView.idproyecto:
            # Crear un cuadro de diálogo de confirmación
            confirmacion = QMessageBox()
            confirmacion.setIcon(QMessageBox.Question)
            confirmacion.setWindowTitle("Guardar Reporte")
            confirmacion.setText("¿Desea guardar la información del reporte?")
            confirmacion.setStandardButtons(QMessageBox.Sí | QMessageBox.No)
            # Mostrar el cuadro de diálogo y obtener la respuesta del usuario
            respuesta = confirmacion.exec()
            if respuesta == QMessageBox.Yes:
                imagen_componente = None
                tab_widget_reporte = main.findChild(QTabWidget, "tabWidget_reporte")
                current_index = tab_widget_reporte.currentIndex()
                if current_index == 0:
                    if ReporteView.imagePathGeneral:
                        imagen_componente = MetodosGenerales.convertir_imagen_a_blob(ReporteView.imagePathGeneral)
                    ReporteGeneral.guardarFormularioReporte(main, ReporteView.idproyecto, imagen_componente)
                    mostrar_mensaje("Datos Guardados", "Los datos se guardaron correctamente.", "informacion")
                elif current_index == 1:
                    if ReporteView.imagePathAnexo1:
                        imagen_componente = MetodosGenerales.convertir_imagen_a_blob(ReporteView.imagePathAnexo1)
                    ReporteAnexo1.guardarInformacionGeneralAnexo1(main, ReporteView.idproyecto, imagen_componente, "Anexo1")
                    ReporteAnexo1.guardarInformacionResumenEjecutivo(main, ReporteView.idproyecto)
                    widget_anexo1 = main.findChild(QWidget, "widget_elementos_dinamicos_anexo_A1")
                    idcomponente = main.findChild(QComboBox, "cb_componentes_anexos").currentData()
                    ReporteAnexo1.guardarDatosDinamicosAnexo1(widget_anexo1, idcomponente)
                    mostrar_mensaje("Datos Guardados", "Los datos se guardaron correctamente.", "informacion")
                elif current_index == 2:
                    if ReporteView.imagePathAnexo2:
                        imagen_componente = MetodosGenerales.convertir_imagen_a_blob(ReporteView.imagePathAnexo2)
                    ReporteAnexo2.guardarInformacionGeneralAnexo2(main, ReporteView.idproyecto, imagen_componente, "Anexo2")
                    ReporteAnexo2.guardarInformacionResumenEjecutivo(main, ReporteView.idproyecto)
                    widget_anexo2 = main.findChild(QWidget, "widget_elementos_dinamicos_anexo_A2")
                    idcomponente = main.findChild(QComboBox, "cb_componentes_anexos").currentData()
                    ReporteAnexo2.guardarDatosDinamicosAnexo2(widget_anexo2, idcomponente)
                    mostrar_mensaje("Datos Guardados", "Los datos se guardaron correctamente.", "informacion")
    
    def mostrarReporte(main, file):
        ruta_pdf = resource_path(file)
        widget = main.findChild(QWidget, "widget_vista_pdf")
        zoom_in = main.findChild(QPushButton, "btn_acercar_zoom")
        zoom_out = main.findChild(QPushButton, "btn_alejar_zoom")
        if widget:
            ReporteView.limpiarWidgetReportePDF()
            # Crear y añadir el visor PDF
            pdf_viewer = PDFViewerWidget(widget, ruta_pdf)
            widget.layout().addWidget(pdf_viewer)
            # Conectar los botones a los métodos de zoom
            if zoom_in:
                zoom_in.clicked.connect(pdf_viewer.zoom_in)
            if zoom_out:
                zoom_out.clicked.connect(pdf_viewer.zoom_out)
    
    def limpiarWidgetReportePDF():
        widget = ReporteView.main.findChild(QWidget, "widget_vista_pdf")
        if widget:
            # Eliminar cualquier contenido existente en el widget
            if widget.layout():
                # Eliminar todos los widgets del layout
                for i in reversed(range(widget.layout().count())):
                    widget.layout().itemAt(i).widget().setParent(None)
            else:
                widget.setLayout(QVBoxLayout())
    
    def actualizarListaImagenesReporte():
        if ReporteView.idproyecto:
            tab_widget_reporte = ReporteView.main.findChild(QTabWidget, "tabWidget_reporte")
            current_index = tab_widget_reporte.currentIndex()
            if current_index == 0:
                Reporte.mostrarListaImagenesReporteGeneral(ReporteView.main, ReporteView.idproyecto, "GENERAL")
            elif current_index == 1:
                Reporte.mostrarListaImagenesReporteAnexos(ReporteView.main, ReporteView.idproyecto, "ANEXO1")
            elif current_index == 2:
                Reporte.mostrarListaImagenesReporteAnexos(ReporteView.main, ReporteView.idproyecto, "ANEXO2")
    
    ######## REPORTE ANEXO 1 - 2 ########
    def cargarValoresAnexos():
        widget_anexo1 = ReporteView.main.findChild(QWidget, "widget_elementos_dinamicos_anexo_A1")
        widget_anexo2 = ReporteView.main.findChild(QWidget, "widget_elementos_dinamicos_anexo_A2")
        Anexo1.setup_widget_anexo1(widget_anexo1, ReporteView.main)
        Anexo2.setup_widget_anexo2(widget_anexo2, ReporteView.main)
    
    def reiniciarVistaReporte(main, proyecto_id, proyecto_name):
        # reiniciar variables
        ReporteView.main = main
        ReporteView.idproyecto = proyecto_id
        ReporteView.nameproyecto = proyecto_name
        ReporteView.limpiarFormularioReporteGeneral()
        ReporteView.limpiarFormularioAnexo1General()
        ReporteView.limpiarFormularioAnexo1ResumenEjecutivo()
        ReporteView.limpiarFormularioAnexo2General()
        ReporteView.limpiarFormularioAnexo2ResumenEjecutivo()
        ReporteView.limpiarWidgetReportePDF()
        ReporteView.estadochecklist = True
    
    def limpiarFormularioReporteGeneral():
        ReporteView.main.findChild(QLineEdit, "input_encabezado").setText("Reporte Mensual")
        ReporteView.main.findChild(QLineEdit, "input_pie_pagina").setText("Unidad Minera")
        ReporteView.main.findChild(QLineEdit, "input_titulo").setText("INFORME MENSUAL DE INSTRUMENTACIÓN GEOTÉCNICA")
        ReporteView.main.findChild(QLineEdit, "input_lugar").setText("Unidad Minera")
        ReporteView.main.findChild(QLineEdit, "input_mes_reporte").setText("")
        ReporteView.main.findChild(QLineEdit, "input_para").setText("Geotecnia")
        ReporteView.main.findChild(QLineEdit, "input_de").setText("Eigha SAC")
        ReporteView.main.findChild(QLineEdit, "input_cc").setText("Planeamiento")
        ReporteView.main.findChild(QLineEdit, "input_asunto").setText("Informe de monitoreo geotécnico")
        ReporteView.main.findChild(QTextEdit, "input_descripcion").setPlainText("La Unidad Minera gestionó la realizació del informe...")
        ReporteView.main.findChild(QTextEdit, "input_conclusiones").setPlainText("1. Se concluyó...")
        ReporteView.main.findChild(QTextEdit, "input_recomendaciones").setPlainText("1. Se recomienda...")
        ReporteView.main.findChild(QLabel, "label_imagen").setPixmap(QPixmap())
        ReporteView.main.findChild(QLineEdit, "input_imagen").setText("")
    
    def limpiarFormularioAnexo1General():
        ReporteView.main.findChild(QLineEdit, "input_titulo_portada_A1").setText("REPORTE MENSUAL DE SUPERVISIÓN ...")
        ReporteView.main.findChild(QLineEdit, "input_subtitulo_portada_A1").setText("RELAVERA ...")
        ReporteView.main.findChild(QLineEdit, "input_lugar_portada_A1").setText("Lima, Perú")
        ReporteView.main.findChild(QLineEdit, "input_autor_portada_A1").setText("Jefatura de Geotecnia")
        # DOCUMENTO
        ReporteView.main.findChild(QLineEdit, "input_tipo_documento_A1").setText("MEMORANDUM")
        ReporteView.main.findChild(QLineEdit, "input_codigo_reporte_A1").setText("SMEB-GEO-...")
        ReporteView.main.findChild(QPlainTextEdit, "input_destinatario_reporte_A1").setPlainText("Ing. ...\nGerente de Unidad")
        ReporteView.main.findChild(QPlainTextEdit, "input_remitente_reporte_A1").setPlainText("Ing. ...\nJefe de Geotecnia")
        ReporteView.main.findChild(QPlainTextEdit, "input_asunto_reporte_A1").setPlainText("Reporte Mensual de Supervisión de ...")
        ReporteView.main.findChild(QPlainTextEdit, "input_descripcion_reporte_A1").setPlainText("Estimado ingeniero ...,\nSe adjunta el presente Reporte ...")
        # COMPONENTE
        ReporteView.main.findChild(QLineEdit, "input_tipo_reporte_A1").setText("REPORTE MENSUAL")
        ReporteView.main.findChild(QLineEdit, "input_componente_reporte_A1").setText("RELAVERA ...")
        ReporteView.main.findChild(QLabel, "lb_imagen_componente_A1").setPixmap(QPixmap())
        # INTRODUCCIÓN
        ReporteView.main.findChild(QPlainTextEdit, "input_objetivo_reporte_A1").setPlainText("El presente documento tiene como objeto emitir el reporte ...")
        ReporteView.main.findChild(QPlainTextEdit, "input_finalidad_reporte_A1").setPlainText("En concordancia con lo dispuesto en el Decreto Supremo N° ...")
        ReporteView.main.findChild(QPlainTextEdit, "input_ambito_reporte_A1").setPlainText("El presente reporte aplica al componente ...")
        ReporteView.main.findChild(QPlainTextEdit, "input_detalle_reporte_A1").setPlainText("De conformidad con el artículo 323 del RSSO, el depósito de relaves ...")
        ReporteView.main.findChild(QLineEdit, "input_titulo_anexo_A1").setText("Reporte Mensual de Supervisión de ...")
    
    def limpiarFormularioAnexo1ResumenEjecutivo():
        ReporteView.main.findChild(QPlainTextEdit, "input_descripcion_general_anexo_A1").setPlainText("El componente de ..., está compuesta por ...")
        ReporteView.main.findChild(QLineEdit, "input_componente_encabezado_anexo_A1").setText("DEPÓSITO:")
        ReporteView.main.findChild(QLineEdit, "input_valor_componente_encabezado_anexo_A1").setText("")
        ReporteView.main.findChild(QLineEdit, "input_autorizacion_encabezado_anexo_A1").setText("ÚLTIMA AUTORIZACIÓN DE FUNCIONAMIENTO:")
        ReporteView.main.findChild(QLineEdit, "input_valor_autorizacion_encabezado_anexo_A1").setText("")
        ReporteView.main.findChild(QLineEdit, "input_fecha_encabezado_anexo_A1").setText("MES / AÑO:")
        ReporteView.main.findChild(QLineEdit, "input_valor_fecha_encabezado_anexo_A1").setText("")
        ReporteView.main.findChild(QPlainTextEdit, "input_expediente_control_anexo_A1").setPlainText("Se cumple con el expediente técnico (condiciones geométricas y parámetros operativos) aprobado por la autoridad minera ...")
        si_expediente_a1 = ReporteView.main.findChild(QRadioButton, "rb_expediente_control_SI_anexo_A1")
        si_expediente_a1.setChecked(True)
        ReporteView.main.findChild(QPlainTextEdit, "input_inspeccion_anexo_A1").setPlainText("De la inspección del depósito de relaves se advierten signos de afectación a la integridad física del ...")
        no_inspeccion_a1 = ReporteView.main.findChild(QRadioButton, "rb_inspeccion_NO_anexo_A1")
        no_inspeccion_a1.setChecked(True)
    
    def limpiarFormularioAnexo2General():
        ReporteView.main.findChild(QLineEdit, "input_titulo_portada_A2").setText("REPORTE MENSUAL DE SUPERVISIÓN ...")
        ReporteView.main.findChild(QLineEdit, "input_subtitulo_portada_A2").setText("RELAVERA ...")
        ReporteView.main.findChild(QLineEdit, "input_lugar_portada_A2").setText("Lima, Perú")
        ReporteView.main.findChild(QLineEdit, "input_autor_portada_A2").setText("Jefatura de Geotecnia")
        # DOCUMENTO
        ReporteView.main.findChild(QLineEdit, "input_tipo_documento_A2").setText("MEMORANDUM")
        ReporteView.main.findChild(QLineEdit, "input_codigo_reporte_A2").setText("SMEB-GEO-...")
        ReporteView.main.findChild(QPlainTextEdit, "input_destinatario_reporte_A2").setPlainText("Ing. ...\nGerente de Unidad")
        ReporteView.main.findChild(QPlainTextEdit, "input_remitente_reporte_A2").setPlainText("Ing. ...\nJefe de Geotecnia")
        ReporteView.main.findChild(QPlainTextEdit, "input_asunto_reporte_A2").setPlainText("Reporte Mensual de Supervisión de ...")
        ReporteView.main.findChild(QPlainTextEdit, "input_descripcion_reporte_A2").setPlainText("Estimado ingeniero ...,\nSe adjunta el presente Reporte ...")
        # COMPONENTE
        ReporteView.main.findChild(QLineEdit, "input_tipo_reporte_A2").setText("REPORTE MENSUAL")
        ReporteView.main.findChild(QLineEdit, "input_componente_reporte_A2").setText("RELAVERA ...")
        ReporteView.main.findChild(QLabel, "lb_imagen_componente_A2").setPixmap(QPixmap())
        # INTRODUCCIÓN
        ReporteView.main.findChild(QPlainTextEdit, "input_objetivo_reporte_A2").setPlainText("El presente documento tiene como objeto emitir el reporte ...")
        ReporteView.main.findChild(QPlainTextEdit, "input_finalidad_reporte_A2").setPlainText("En concordancia con lo dispuesto en el Decreto Supremo N° ...")
        ReporteView.main.findChild(QPlainTextEdit, "input_ambito_reporte_A2").setPlainText("El presente reporte aplica al componente ...")
        ReporteView.main.findChild(QPlainTextEdit, "input_detalle_reporte_A2").setPlainText("De conformidad con el artículo 323 del RSSO, el depósito de relaves ...")
        ReporteView.main.findChild(QLineEdit, "input_titulo_anexo_A2").setText("Reporte Mensual de Supervisión de ...")
    
    def limpiarFormularioAnexo2ResumenEjecutivo():
        ReporteView.main.findChild(QPlainTextEdit, "input_descripcion_general_anexo_A2").setPlainText("El componente de ..., está compuesta por ...")
        ReporteView.main.findChild(QLineEdit, "input_componente_encabezado_anexo_A2").setText("DEPÓSITO:")
        ReporteView.main.findChild(QLineEdit, "input_valor_componente_encabezado_anexo_A2").setText("")
        ReporteView.main.findChild(QLineEdit, "input_periodo_encabezado_anexo_A2").setText("PERIODO DE INTERPRETACIÓN")
        ReporteView.main.findChild(QLineEdit, "input_valor_periodo_encabezado_anexo_A2").setText("")
        ReporteView.main.findChild(QPlainTextEdit, "input_interpretacion_monitoreo_anexo_A2").setPlainText("La interpretación del monitoreo geotécnico indica magnitudes y tendencias que comprometen la estabilidad física del ...")
        no_interpreta_a2 = ReporteView.main.findChild(QRadioButton, "rb_interpretacion_NO_anexo_A2")
        no_interpreta_a2.setChecked(True)
    
    def reiniciarVistasAfectadas():
        from views.datos_view import DatosView
        from views.visor_view import VisorView
        from views.desplazamiento_view import DesplazamientoView
        from views.velocidad_view import VelocidadView
        from views.inclinometros_view import InclinometrosView
        from views.piezometros_view import PiezometrosView
        from views.celdas_view import CeldasView
        from views.acelerografos_view import AcelerografosView
        from views.sondajestdr_view import SondajetdrView
        from views.analisis_view import AnalisisView
        DatosView.reiniciarVistaDatos(DesplazamientoView.main, DesplazamientoView.idproyecto, DesplazamientoView.nameproyecto)
        VisorView.reiniciarVistaVisor(ReporteView.main, ReporteView.idproyecto, ReporteView.nameproyecto)
        DesplazamientoView.reiniciarVistaDesplazamiento(ReporteView.main, ReporteView.idproyecto, ReporteView.nameproyecto)
        VelocidadView.reiniciarVistaVelocidad(ReporteView.main, ReporteView.idproyecto, ReporteView.nameproyecto)
        InclinometrosView.reiniciarVistaInclinometros(ReporteView.main, ReporteView.idproyecto, ReporteView.nameproyecto)
        PiezometrosView.reiniciarVistaPiezometros(ReporteView.main, ReporteView.idproyecto, ReporteView.nameproyecto)
        CeldasView.reiniciarVistaCeldas(ReporteView.main, ReporteView.idproyecto, ReporteView.nameproyecto)
        AcelerografosView.reiniciarVistaAcelerografos(ReporteView.main, ReporteView.idproyecto, ReporteView.nameproyecto)
        SondajetdrView.reiniciarVistaTDR(ReporteView.main, ReporteView.idproyecto, ReporteView.nameproyecto)
        AnalisisView.reiniciarVistaAnalisis(ReporteView.main, ReporteView.idproyecto, ReporteView.nameproyecto)
        # reiniciar formularios
        Reporte.llenarComboComponentesReporte(ReporteView.idproyecto, ReporteView.main)
        ReporteView.llenarDataFormulariosReportes()
    




# Hilo generar reporte general
class GenerarReporteGeneralThread(QThread):
    task_finishReporteGeneral = Signal()

    def __init__(self, main, idproyecto, imagen_componente,idcomponente):
        super().__init__()
        self.main = main
        self.idproyecto = idproyecto
        self.imagen_componente = imagen_componente
        self.idcomponente=idcomponente
    
    def run(self):
        # procesar reporte
        ReporteGeneral.generarReporte(self.main, self.idproyecto, self.imagen_componente,self.idcomponente)
        # mandar señal
        self.task_finishReporteGeneral.emit()


class MostrarReporteAnexo1Thread(QThread):
    task_finishAnexo1Report = Signal()

    def __init__(self, relative_word_path, relative_pdf_path):
        super().__init__()
        self.relative_word_path = relative_word_path
        self.relative_pdf_path = relative_pdf_path
    
    def run(self):
        # procesar reporte
        ReporteView.convertir_docx_a_pdf(self.relative_word_path, self.relative_pdf_path)
        # mandar señal
        self.task_finishAnexo1Report.emit()

class MostrarReporteAnexo2Thread(QThread):
    task_finishAnexo2Report = Signal()

    def __init__(self, relative_word_path, relative_pdf_path):
        super().__init__()
        self.relative_word_path = relative_word_path
        self.relative_pdf_path = relative_pdf_path
    
    def run(self):
        # procesar reporte
        ReporteView.convertir_docx_a_pdf(self.relative_word_path, self.relative_pdf_path)
        # mandar señal
        self.task_finishAnexo2Report.emit()
    