from PySide6.QtWidgets import (QDialog, QVBoxLayout, QDialog, QVBoxLayout, QPushButton, QLabel, QLineEdit, QComboBox, QHBoxLayout,
                            QScrollArea, QWidget)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import Qt
from utils.common.rutasarchivos import resource_path
from utils.generic.cargariconos import cargarIcono
from utils.generic.listaiconos import ListaIconos
from utils.common.metodosGenerales import MetodosGenerales
from controllers.ReporteController import ReporteController

class Reporte:
    file_patch = None
    
    def registrarFirmaReportes(proyectoid):       
        Reporte.file_patch=None 
        loader = QUiLoader()
        ui_file_path = resource_path("ui/firmasresponsable.ui")
        ui_file = loader.load(ui_file_path, None)
        # Configurar el cuadro de diálogo
        dialog = QDialog()
        dialog.setWindowTitle("Registro de Firma")
        layout = QVBoxLayout()
        layout.addWidget(ui_file)
        dialog.setLayout(layout)
        label_firma = dialog.findChild(QLabel, "lb_vista_firma")
        nombrePluvio = dialog.findChild(QLineEdit, "input_nombre_firma")
        botonguardar = dialog.findChild(QPushButton, "btn_subir_firma")
        botonguardarfirma = dialog.findChild(QPushButton, "btn_guardar_firma")
        
        registrofirma = ReporteController.ctrlObtenerDatosFirma(proyectoid)
        if registrofirma:
            dialog.findChild(QLineEdit, "input_responsable").setText(str(registrofirma[2]))
            dialog.findChild(QLineEdit, "input_cargo").setText(str(registrofirma[3]))
            dialog.findChild(QLineEdit, "input_dni").setText(str(registrofirma[4]))
            dialog.findChild(QLineEdit, "input_cip").setText(str(registrofirma[5]))
            if registrofirma[6]:
                pixmap = MetodosGenerales.convertir_blob_a_pixmap(registrofirma[6])
                label_firma.setPixmap(pixmap)
                label_firma.setScaledContents(True)
        
        botonguardar.clicked.connect(lambda:Reporte.subirImagenfirma(nombrePluvio, label_firma))
        botonguardarfirma.clicked.connect(lambda:Reporte.guardarfirma(proyectoid, dialog))
        dialog.exec()
    
    def subirImagenfirma(nombrePluvio, label_firma):
        Reporte.file_patch = MetodosGenerales.cargarImagenLocal(label_firma, nombrePluvio)
        
    def guardarfirma(proyectoid,dialog):
        responsable = dialog.findChild(QLineEdit, "input_responsable").text().strip()
        cargo = dialog.findChild(QLineEdit, "input_cargo").text().strip()
        dni = dialog.findChild(QLineEdit, "input_dni").text().strip()
        cip = dialog.findChild(QLineEdit, "input_cip").text().strip()
        firma_reporte = MetodosGenerales.convertir_imagen_a_blob(Reporte.file_patch)
        if responsable != "" and dni != "":
            data = [responsable, cargo, dni, cip, firma_reporte]
            respuesta = ReporteController.ctrlRegistrarFirma(proyectoid, data)
            if respuesta:
                Reporte.file_patch = None
                dialog.close()
    
    def llenarComboComponentesReporte(proyectoid, main):
        cb_componentes_anexos = main.findChild(QComboBox, "cb_componentes_anexos")
        # Limpiar el combo antes de llenarlo
        cb_componentes_anexos.clear()
        # Obtener los componentes
        componentes = ReporteController.ctrlObtenerComponentes(proyectoid)
        # Verificar si la lista de componentes está vacía
        if componentes:
            for componente in componentes:
                id_componente,_,nombre_componente,_ = componente
                cb_componentes_anexos.addItem(nombre_componente,id_componente)
    
    def mostrarListaImagenesReporteAnexos(main, idproyecto, tiporeporte):
        dialog = QDialog(main)
        dialog.setWindowTitle("Lista de Imágenes Reporte")
        dialog.resize(500, 260)
        # Crear el combo box
        combo = QComboBox(dialog)
        componentes = ReporteController.ctrlObtenerComponentes(idproyecto)
        if componentes:
            for componente in componentes:
                id_componente,_,nombre_componente,_ = componente
                combo.addItem(nombre_componente, id_componente)
        # Crear el encabezado
        encabezado_layout = QHBoxLayout()
        encabezado_imagen = QLabel("Imagen", dialog)
        encabezado_imagen.setAlignment(Qt.AlignCenter)
        encabezado_acciones = QLabel("Acciones", dialog)
        encabezado_acciones.setAlignment(Qt.AlignCenter)
        encabezado_layout.addWidget(encabezado_imagen)
        encabezado_layout.addWidget(encabezado_acciones)
        # Crear el área de scroll
        scroll_area = QScrollArea(dialog)
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_area.setWidget(scroll_content)
        # Función para limpiar el layout del scroll
        def limpiar_scroll_layout():
            while scroll_layout.count():
                item = scroll_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                elif item.layout():
                    while item.layout().count():
                        sub_item = item.layout().takeAt(0)
                        if sub_item.widget():
                            sub_item.widget().deleteLater()
                    item.layout().deleteLater()
        # Función para actualizar la lista de imágenes
        def actualizar_lista_imagenes():
            # Limpiar el layout del scroll
            limpiar_scroll_layout()
            # Obtener la lista de imágenes desde la base de datos
            lista_imagenes = ReporteController.ctrlListarImagenesReportes(combo.currentData(), tiporeporte)
            # Llenar el área de scroll con las filas de imágenes y botones "Borrar"
            if lista_imagenes:
                for imagen in lista_imagenes:
                    id_imagen = imagen[0]
                    pixmap = MetodosGenerales.convertir_blob_a_pixmap(imagen[4])
                    fila_layout = QHBoxLayout()
                    # Crear el label con la imagen y establecer un tamaño fijo
                    label_imagen = QLabel(dialog)
                    label_imagen.setPixmap(pixmap.scaled(350, 200, Qt.KeepAspectRatio))
                    label_imagen.setFixedSize(350, 200)
                    label_imagen.setAlignment(Qt.AlignCenter)
                    # Crear el botón "Borrar"
                    btn_borrar = QPushButton("Borrar", dialog)
                    btn_borrar.setFixedSize(75, 50)
                    cargarIcono(btn_borrar, ListaIconos.ICONOS["basura"])
                    btn_borrar.clicked.connect(lambda *args, id_imagen=id_imagen, fila_layout=fila_layout: Reporte.borrarImagenFila(id_imagen, fila_layout, scroll_layout))
                    # Añadir el label y el botón a la fila
                    fila_layout.addWidget(label_imagen)
                    fila_layout.addWidget(btn_borrar)
                    # Añadir la fila al layout del scroll
                    scroll_layout.addLayout(fila_layout)
            else:
                # Si no hay imágenes, añadir un mensaje indicando que no hay datos disponibles
                no_data_label = QLabel("No hay imágenes", dialog)
                no_data_label.setAlignment(Qt.AlignCenter)
                scroll_layout.addWidget(no_data_label)
        # Conectar la señal currentIndexChanged del combo box a la función de actualización
        combo.currentIndexChanged.connect(actualizar_lista_imagenes)
        # Crear el layout principal
        layout = QVBoxLayout()
        layout.addWidget(combo)
        layout.addLayout(encabezado_layout)
        layout.addWidget(scroll_area)
        dialog.setLayout(layout)
        # Cargar la lista de imágenes inicialmente
        actualizar_lista_imagenes()
        # Mostrar el diálogo
        dialog.exec()
    
    def borrarImagenFila(id_imagen, fila_layout, scroll_layout):
        # Eliminar la fila del layout del scroll
        for i in reversed(range(fila_layout.count())):
            fila_layout.itemAt(i).widget().setParent(None)
        scroll_layout.removeItem(fila_layout)
        ReporteController.ctrlEliminarGraficaReporte(id_imagen)
    
    def mostrarListaImagenesReporteGeneral(main, idproyecto, tiporeporte):
        dialog = QDialog(main)
        dialog.setWindowTitle("Lista de Imágenes Reporte")
        dialog.resize(500, 260)
        # Crear el encabezado
        encabezado_layout = QHBoxLayout()
        encabezado_imagen = QLabel("Imagen", dialog)
        encabezado_imagen.setAlignment(Qt.AlignCenter)
        encabezado_acciones = QLabel("Acciones", dialog)
        encabezado_acciones.setAlignment(Qt.AlignCenter)
        encabezado_layout.addWidget(encabezado_imagen)
        encabezado_layout.addWidget(encabezado_acciones)
        # Crear el área de scroll
        scroll_area = QScrollArea(dialog)
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_area.setWidget(scroll_content)
        # Función para limpiar el layout del scroll
        def limpiar_scroll_layout():
            while scroll_layout.count():
                item = scroll_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                elif item.layout():
                    while item.layout().count():
                        sub_item = item.layout().takeAt(0)
                        if sub_item.widget():
                            sub_item.widget().deleteLater()
                    item.layout().deleteLater()
        # Función para actualizar la lista de imágenes
        def actualizar_imagenes():
            # Limpiar el layout del scroll
            limpiar_scroll_layout()
            # Obtener la lista de imágenes desde la base de datos
            lista_imagenes = ReporteController.ctrlListarImagenesReportes(idproyecto, tiporeporte)
            # Llenar el área de scroll con las filas de imágenes y botones "Borrar"
            if lista_imagenes:
                for imagen in lista_imagenes:
                    id_imagen = imagen[0]
                    pixmap = MetodosGenerales.convertir_blob_a_pixmap(imagen[4])
                    fila_layout = QHBoxLayout()
                    # Crear el label con la imagen y establecer un tamaño fijo
                    label_imagen = QLabel(dialog)
                    label_imagen.setPixmap(pixmap.scaled(350, 200, Qt.KeepAspectRatio))
                    label_imagen.setFixedSize(350, 200)
                    label_imagen.setAlignment(Qt.AlignCenter)
                    # Crear el botón "Borrar"
                    btn_borrar = QPushButton("Borrar", dialog)
                    btn_borrar.setFixedSize(75, 50)
                    cargarIcono(btn_borrar, ListaIconos.ICONOS["basura"])
                    btn_borrar.clicked.connect(lambda *args, id_imagen=id_imagen, fila_layout=fila_layout: Reporte.borrarImagenFila(id_imagen, fila_layout, scroll_layout))
                    # Añadir el label y el botón a la fila
                    fila_layout.addWidget(label_imagen)
                    fila_layout.addWidget(btn_borrar)
                    # Añadir la fila al layout del scroll
                    scroll_layout.addLayout(fila_layout)
            else:
                # Si no hay imágenes, añadir un mensaje indicando que no hay datos disponibles
                no_data_label = QLabel("No hay imágenes", dialog)
                no_data_label.setAlignment(Qt.AlignCenter)
                scroll_layout.addWidget(no_data_label)
        # Crear el layout principal
        layout = QVBoxLayout()
        layout.addLayout(encabezado_layout)
        layout.addWidget(scroll_area)
        dialog.setLayout(layout)
        # Cargar la lista de imágenes inicialmente
        actualizar_imagenes()
        # Mostrar el diálogo
        dialog.exec()
    