import fitz  # PyMuPDF
from PySide6.QtUiTools import QUiLoader
from utils.common.rutasarchivos import resource_path
from PySide6.QtGui import QImage, QPixmap, QPen
from PySide6.QtWidgets import (QPushButton, QDialog, QVBoxLayout, QDialog, QVBoxLayout, QWidget,
    QComboBox, QLabel, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsRectItem, QLineEdit, QDoubleSpinBox)
from PySide6.QtCore import Qt
from datetime import datetime
from controllers.CeldaController import CeldaController
from controllers.ProyectoController import ProyectoController

class ViewGeneral:
    
    def mostrarDialogoManualUsuario():
        loader = QUiLoader()
        ui_file_path = resource_path("ui/manualusuario.ui")
        ui_file = loader.load(ui_file_path, None)
        # Configurar el cuadro de diálogo
        dialog = QDialog()
        dialog.setWindowTitle("Manual de Usuario E-Monitoring")
        layout = QVBoxLayout()
        layout.addWidget(ui_file)
        dialog.setLayout(layout)
        # Obtener elementos para interactuar
        widgetPdf = dialog.findChild(QWidget, "widget_pdf_manual")
        botonaceptar = dialog.findChild(QPushButton, "btn_aceptar")
        botoncerrar = dialog.findChild(QPushButton, "btn_cerrar")
        def mostrarManualUsuarioPDF():
            try:
                ruta_imagen = resource_path("resources/assets/UserManual.pdf")
                # Crear una instancia de MuPDF
                doc = fitz.open(f'{ruta_imagen}')
                # Verificar si ya existe un QGraphicsView en el widget_visor_pdf
                visor_pdf = widgetPdf.findChild(QGraphicsView)
                # Si no existe, crear uno nuevo
                if not visor_pdf:
                    visor_pdf = QGraphicsView(widgetPdf)
                    visor_pdf.setGeometry(10, 10, 780, 580)
                # Obtener o crear una escena para el visor
                escena = visor_pdf.scene()
                if not escena:
                    escena = QGraphicsScene(visor_pdf)
                # Limpiar la escena antes de agregar las nuevas páginas
                escena.clear()
                # Ajustar el espacio entre las páginas
                espacio_entre_paginas = 10
                # Iterar sobre las páginas y agregarlas al visor
                for num_pagina in range(doc.page_count):
                    page = doc[num_pagina]
                    # Obtener una imagen de mayor calidad
                    image = page.get_pixmap(matrix=fitz.Matrix(0.95, 0.95), alpha=False)
                    # Convertir la imagen de PyMuPDF a QImage
                    qimage = QImage(image.samples, image.width, image.height, image.stride, QImage.Format_RGB888)
                    # Crear un elemento gráfico para mostrar la imagen en el visor
                    pixmap_item = QGraphicsPixmapItem(QPixmap.fromImage(qimage))
                    # Establecer la posición de cada página con espacio entre ellas
                    espacio_vertical = num_pagina * (pixmap_item.pixmap().height() + espacio_entre_paginas)
                    pixmap_item.setPos(0, espacio_vertical)
                    # Añadir el elemento gráfico a la escena
                    escena.addItem(pixmap_item)
                    # Crear un rectángulo para agregar un borde alrededor de cada página
                    rectangulo = QGraphicsRectItem(pixmap_item.pixmap().rect())
                    rectangulo.setPos(0, espacio_vertical)
                    rectangulo.setPen(QPen(Qt.gray, 1))  # Puedes ajustar el color y grosor del borde
                    # Añadir el rectángulo a la escena
                    escena.addItem(rectangulo)
                # Establecer la escena en el visor
                visor_pdf.setScene(escena)
                # Establecer el área de desplazamiento como widget central
                layout = QVBoxLayout(widgetPdf)
                layout.addWidget(visor_pdf)
            except Exception as e:
                print("Error al mostrar pdf manual usuario.")
        # leer y mostrar pdf
        mostrarManualUsuarioPDF()        
        def cerrarManualUsuario():
            dialog.close()
        # Inicializar botones
        botonaceptar.clicked.connect(cerrarManualUsuario)
        botoncerrar.clicked.connect(cerrarManualUsuario)
        # mostrar dialogo
        dialog.exec()
    
    def mostrarDialogoAcercade(version):
        loader = QUiLoader()
        ui_file_path = resource_path("ui/acercadesoftware.ui")
        ui_file = loader.load(ui_file_path, None)
        # Configurar el cuadro de diálogo
        dialog = QDialog()
        dialog.setWindowTitle("Acerca de E-Monitoring")
        layout = QVBoxLayout()
        layout.addWidget(ui_file)
        dialog.setLayout(layout)
        # Obtener elementos para interactuar
        lbllogo = dialog.findChild(QLabel, "label_logo")
        lblcontenido = dialog.findChild(QLabel, "label_informacion")
        botoncerrar = dialog.findChild(QPushButton, "btn_cerrar")
        path_logo = resource_path("resources/logo.png")
        pixmap = QPixmap(path_logo)
        lbllogo.setPixmap(pixmap)
        anio = datetime.now().year
        contenido = f"""E-MONITORING {version} está soportado y desarrolado por EIGHA S.A.C. \nCopyright © {anio} E-Monitoring Software. Todos los derechos reservados.
        \nVersión actual {version} \nEste programa usa Python versión 3.11, Qt Versión 3.5, Sql Lite Versión 3.1 y los \níconos desde https://fontawesome.com. 
        \nDistribuido por EIGHA S.A.C. bajo autorización de Indecopi. Este software está \nprotegido por Copyright bajo leyes internacionales. 
        \nLa reproducción no autorizada o distribución de este programa, \no alguna parte del mismo, puede incurrir en pena civil o criminal, aplicandose \nel máximo castigo impuesto por este tipo de delitos."""
        lblcontenido.setText(contenido)
        def cerrarInformacion():
            dialog.close()
        # Inicializar botones
        botoncerrar.clicked.connect(cerrarInformacion)
        # mostrar dialogo
        dialog.exec()
    
    def mostrarDialogoSoporte(version):
        loader = QUiLoader()
        ui_file_path = resource_path("ui/soporte.ui")
        ui_file = loader.load(ui_file_path, None)
        # Configurar el cuadro de diálogo
        dialog = QDialog()
        dialog.setWindowTitle("Soporte E-Monitoring")
        layout = QVBoxLayout()
        layout.addWidget(ui_file)
        dialog.setLayout(layout)
        # Obtener elementos para interactuar
        lbllogo = dialog.findChild(QLabel, "label_logo")
        lblcontenido = dialog.findChild(QLabel, "label_contenido")
        botoncerrar = dialog.findChild(QPushButton, "btn_cerrar")
        path_logo = resource_path("resources/logo.png")
        pixmap = QPixmap(path_logo)
        lbllogo.setPixmap(pixmap)
        anio = datetime.now().year
        lblcontenido.setText(f'E-MONITORING - Copyright © {anio}. \nVersión actual {version} \nPara acceder a los tutoriales detallados, guías paso a paso y \nrespuestas a preguntas frecuentes puedes ingresar a nuestros \ncanales oficiales. \nTutoriales: https://www.youtube.com \nSitio web: www.eigha.com/e-monitoring \nSoporte técnico por correo electrónico las 24 horas: \nE-mail: emonitoringsoporte@eigha.com')
        def cerrarInformacion():
            dialog.close()
        # Inicializar botones
        botoncerrar.clicked.connect(cerrarInformacion)
        # mostrar dialogo                                                                 
        dialog.exec()
    
    def mostrarDialogoRegistroCeldasAsentamiento(proyectoid):        
        loaderLoading = QUiLoader()        
        ui_file_path = resource_path("ui/registroceldas.ui")
        ui_file = loaderLoading.load(ui_file_path, None)
        dialogo = QDialog()
        dialogo.setWindowTitle("Nueva Celda de Asentamiento")
        layout_procesar_data = QVBoxLayout()
        layout_procesar_data.addWidget(ui_file)
        dialogo.setLayout(layout_procesar_data)
        # tools
        nombre_compo = dialogo.findChild(QComboBox, "combo_componente")
        nombre_celda = dialogo.findChild(QLineEdit, "nombre_celda")
        marca_celda = dialogo.findChild(QLineEdit, "marca_celda")
        modelo_celda = dialogo.findChild(QLineEdit, "modelo_celda")
        rango_celda = dialogo.findChild(QDoubleSpinBox, "dsb_rango_celda")
        frecuencia_inicial_celda = dialogo.findChild(QDoubleSpinBox, "dsb_frecuencia_inicial_celda")
        cf_celda = dialogo.findChild(QDoubleSpinBox, "dsb_cf_celda")
        cota_superficie_celda = dialogo.findChild(QDoubleSpinBox, "dsb_cota_superficie_celda")
        cota_fundacion_celda = dialogo.findChild(QDoubleSpinBox, "dsb_cota_fundacion_celda")
        coordenada_este_celda = dialogo.findChild(QDoubleSpinBox, "dsb_coordenada_este_celda")
        coordenada_norte_celda = dialogo.findChild(QDoubleSpinBox, "dsb_coordenada_norte_celda")
        cota_instalacion_celda = dialogo.findChild(QDoubleSpinBox, "dsb_cota_instalacion_celda")
        temperatura_inicial_celda = dialogo.findChild(QDoubleSpinBox, "dsb_temperatura_inicial_celda")
        tk_celda = dialogo.findChild(QDoubleSpinBox, "dsb_tk_celda")
        labelmensaje = dialogo.findChild(QLabel, "label_mensaje")
        boton_guardar = dialogo.findChild(QPushButton, f"btn_guardar_celda")
        if proyectoid:
            componentes = ProyectoController.ctrlObtenerComponentesProyecto(proyectoid)
            if componentes:
                for compo in componentes:
                    nombre_compo.addItem(str(compo[2]), str(compo[0]))
            else:
                nombre_compo.addItem("Sin Componentes")
                boton_guardar.setEnabled(False)
        else:
            nombre_compo.addItem("Sin Componentes")
            boton_guardar.setEnabled(False)
        def registrarCeldaAsentamiento():
            if nombre_celda and nombre_celda.text().strip():
                idcomponente = nombre_compo.currentData()
                celda_data = {
                    "proyecto": proyectoid,
                    "nombre_celda": nombre_celda.text(),
                    "marca_celda": marca_celda.text(),
                    "modelo_celda": modelo_celda.text(),
                    "serie_celda": modelo_celda.text(),
                    "rango_celda": rango_celda.value(),
                    "frecuencia_inicial": frecuencia_inicial_celda.value(),
                    "cf_celda": cf_celda.value(),
                    "cota_superficie_celda": cota_superficie_celda.value(),
                    "cota_fundacion_celda": cota_fundacion_celda.value(),
                    "coordenada_este_celda": coordenada_este_celda.value(),
                    "coordenada_norte_celda": coordenada_norte_celda.value(),
                    "cota_instalacion_celda": cota_instalacion_celda.value(),
                    "temperatura_inicial_celda": temperatura_inicial_celda.value(),
                    "tk_celda": tk_celda.value(),
                }
                # Llamar al método para guardar en la base de datos
                respuesta = CeldaController.ctrlRegistrarCelda(idcomponente, celda_data)
                if respuesta:
                    labelmensaje.setText("La celda se registró correctamente.")
                    labelmensaje.setStyleSheet("color: green;")
                    # Limpiar los inputs
                    nombre_celda.clear()
                    marca_celda.clear()
                    modelo_celda.clear()
                    rango_celda.setValue(0)
                    frecuencia_inicial_celda.setValue(0)
                    cf_celda.setValue(0)
                    cota_superficie_celda.setValue(0)
                    cota_fundacion_celda.setValue(0)
                    coordenada_este_celda.setValue(0)
                    coordenada_norte_celda.setValue(0)
                    cota_instalacion_celda.setValue(0)
                    temperatura_inicial_celda.setValue(0)
                    tk_celda.setValue(0)
                else:
                    labelmensaje.setText("Error al registrar la celda.")
                    labelmensaje.setStyleSheet("color: orange;")
            else:
                labelmensaje.setText("El nombre de la celda es obligatorio.")
                labelmensaje.setStyleSheet("color: red;")
        # conectar señales
        boton_guardar.clicked.connect(registrarCeldaAsentamiento)
        dialogo.exec()
