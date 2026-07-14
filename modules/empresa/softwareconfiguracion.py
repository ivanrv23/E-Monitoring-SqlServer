from PySide6.QtUiTools import QUiLoader
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import (QColorDialog, QDialog, QVBoxLayout, QRadioButton, QComboBox, QSpinBox, QPushButton, QCheckBox,
                        QDoubleSpinBox, QFontComboBox, QLabel)
from utils.common.rutasarchivos import resource_path
from controllers.EmpresaController import EmpresaController

class SoftwareConfiguracion:
    titulo = 12
    ejes = 10
    etiqueta = 8
    leyenda = 8
    cotas = 8
    mostrarcota = 0
    mostrarvertice = 0
    tipotendencia = "-"
    grosortendencia = 1
    colortendencia = "#000000"
    letra = "sans-serif"
    transparencia = 1
    grosorlineas = 1
    grosorvertices = 2
    decimales = 2
    velocidad = 1
    precipitacion = 1
    mostrarpluvio = 0
    celda = 1
    filtrado = 1
    suavizado = 0
    fechahora = 0
    mesletras = 0 
    version = "5.4.0"
       
    # MOSTRAR DIALOGO DE AJUSTES DE SOFTWARE
    def mostrarDialogoConfiguracionSoftware():
        loader = QUiLoader()
        ui_file_path = resource_path("ui/ajustessoftware.ui")
        ui_file = loader.load(ui_file_path, None)
        # Configurar el cuadro de diálogo
        dialog = QDialog()
        dialog.setWindowTitle("Configuración de Gráficos")
        layout = QVBoxLayout()
        layout.addWidget(ui_file)
        dialog.setLayout(layout)
        # GRAFICADO
        spinTitulo = dialog.findChild(QSpinBox, "spin_titulo")
        spinEjes = dialog.findChild(QSpinBox, "spin_ejes")
        spinEtiquetas = dialog.findChild(QSpinBox, "spin_etiquetas")
        spinLeyenda = dialog.findChild(QSpinBox, "spin_leyenda")
        spinCotas = dialog.findChild(QSpinBox, "spin_cotas")
        checkCotas = dialog.findChild(QCheckBox, "check_cota")
        checkVertices = dialog.findChild(QCheckBox, "check_vertices")
        comboTendencia = dialog.findChild(QComboBox, "combo_tendencia")
        spinTendencia = dialog.findChild(QDoubleSpinBox, "spin_tendencia")
        botonTendencia = dialog.findChild(QPushButton, "btn_tendencia")
        comboFuente = dialog.findChild(QFontComboBox, "font_tipo_letra")
        spinTransparencia = dialog.findChild(QDoubleSpinBox, "spin_transparencia")
        spinGrosorlineas = dialog.findChild(QDoubleSpinBox, "spin_grosor_lineas")
        spinGrosorvertices = dialog.findChild(QSpinBox, "spin_grosor_vertices")
        spinDecimales = dialog.findChild(QSpinBox, "spin_decimales")
        # SOFTWARE CONFIG
        radioVelocidadPositiva = dialog.findChild(QRadioButton, "radio_velocidad_positiva")
        radioVelocidadAmbas = dialog.findChild(QRadioButton, "radio_velocidad_ambas")
        radioFiltroSinfechas = dialog.findChild(QRadioButton, "radio_filtro_sinfechas")
        radioFiltroConfechas = dialog.findChild(QRadioButton, "radio_filtro_confechas")
        radioLluviaVisible = dialog.findChild(QRadioButton, "radio_lluvia_visible")
        radioLluviaAutoma = dialog.findChild(QRadioButton, "radio_lluvia_automatica")
        radioLluviaArriba = dialog.findChild(QRadioButton, "radio_lluvia_arriba")
        radioLluviaAbajo = dialog.findChild(QRadioButton, "radio_lluvia_abajo")
        radioCeldaPositiva = dialog.findChild(QRadioButton, "radio_celdas_positivas")
        radioCeldaNegativa = dialog.findChild(QRadioButton, "radio_celdas_negativas")
        checkSuavizado = dialog.findChild(QCheckBox, "check_suavizado") 
        checkFechaHora = dialog.findChild(QCheckBox, "check_fechahora")
        checkMesLetras = dialog.findChild(QCheckBox, "check_mesletras")
        labelmensaje = dialog.findChild(QLabel, "label_mensaje")
        confirmarAjustes = dialog.findChild(QPushButton, "btn_aceptar")
        # cargar combo
        comboTendencia.addItem("Línea continua ___", "-")
        comboTendencia.addItem("Línea discontinua ---", "--")
        comboTendencia.addItem("Línea punteada ...", ":")
        comboTendencia.addItem("Línea punto raya -.-", "-.")
        # inicializar fuentes
        allowed_fonts = ["SansSerif", "Arial", "Times New Roman", "Courier New", "Garamond", "Calibri", "Cambria", "Agency FB",
            "Algerian", "Bauhaus 93", "Californian FB", "Verdana", "Elephant", "Magneto", "Sylfaen", "Microsoft Sans Serif",
            "Trebuchet MS", "Georgia", "Palatino Linotype", "Bookman Old Style", "Consolas", "Lucida Console", "Comic Sans MS", "Impact"
        ]
        # Filtrar fuentes: eliminar las no permitidas
        for i in range(comboFuente.count() - 1, -1, -1):
            font_name = comboFuente.itemText(i)
            if font_name not in allowed_fonts:
                comboFuente.removeItem(i)
        # VALORES DEFECTO
        respuesta = EmpresaController.ctrlObtenerDatosConfiguracionSoftware()
        if respuesta:            
            spinTitulo.setValue(respuesta[1])
            spinEjes.setValue(respuesta[2])
            spinEtiquetas.setValue(respuesta[3])
            spinLeyenda.setValue(respuesta[4])
            spinCotas.setValue(respuesta[5])
            if respuesta[6] == 1:
                checkCotas.setChecked(True)
            else:
                checkCotas.setChecked(False)
            if respuesta[7] == 1:
                checkVertices.setChecked(True)
            else:
                checkVertices.setChecked(False)
            comboTendencia.setCurrentIndex(comboTendencia.findData(respuesta[8]))
            spinTendencia.setValue(respuesta[9])
            botonTendencia.setStyleSheet("background-color: %s" % respuesta[10])
            # cargar fuente seleccionada
            for index in range(comboFuente.count()):
                if comboFuente.itemText(index) == respuesta[11]:
                    comboFuente.setCurrentIndex(index)
                    break
            spinTransparencia.setValue(respuesta[12])
            spinGrosorlineas.setValue(respuesta[13])
            spinGrosorvertices.setValue(respuesta[14])
            spinDecimales.setValue(respuesta[15])
            if respuesta[16] == 0:
                radioVelocidadPositiva.setChecked(True)
            else:
                radioVelocidadAmbas.setChecked(True)
            if respuesta[17] == 0:
                radioFiltroSinfechas.setChecked(True)
            else:
                radioFiltroConfechas.setChecked(True)
            if respuesta[18] == 0:
                radioLluviaVisible.setChecked(True)
            else:
                radioLluviaAutoma.setChecked(True)
            if respuesta[19] == 0:
                radioLluviaArriba.setChecked(True)
            else:
                radioLluviaAbajo.setChecked(True)
            if respuesta[20] == 0:
                radioCeldaPositiva.setChecked(True)
            else:
                radioCeldaNegativa.setChecked(True)
            
            if len(respuesta) > 21:
                checkSuavizado.setChecked(True if respuesta[21] == 1 else False)
                
            if len(respuesta) > 22: 
                checkFechaHora.setChecked(True if respuesta[22] == 1 else False)
                
            if len(respuesta) > 23:
                checkMesLetras.setChecked(True if respuesta[23] == 1 else False)
    
        else:
            spinTitulo.setValue(SoftwareConfiguracion.titulo)
            spinEjes.setValue(SoftwareConfiguracion.ejes)
            spinEtiquetas.setValue(SoftwareConfiguracion.etiqueta)
            spinLeyenda.setValue(SoftwareConfiguracion.leyenda)
            spinCotas.setValue(SoftwareConfiguracion.cotas)
            if SoftwareConfiguracion.mostrarcota == 1:
                checkCotas.setChecked(True)
            else:
                checkCotas.setChecked(False)
            if SoftwareConfiguracion.mostrarvertice == 1:
                checkVertices.setChecked(True)
            else:
                checkVertices.setChecked(False)
            comboTendencia.setCurrentIndex(comboTendencia.findData(SoftwareConfiguracion.tipotendencia))
            spinTendencia.setValue(SoftwareConfiguracion.grosortendencia)
            botonTendencia.setStyleSheet("background-color: %s" % SoftwareConfiguracion.colortendencia)
            # cargar fuente seleccionada
            for index in range(comboFuente.count()):
                if comboFuente.itemText(index) == "SansSerif":
                    comboFuente.setCurrentIndex(index)
                    break
            spinTransparencia.setValue(SoftwareConfiguracion.transparencia)
            spinGrosorlineas.setValue(SoftwareConfiguracion.grosorlineas)
            spinGrosorvertices.setValue(SoftwareConfiguracion.grosorvertices)
            spinDecimales.setValue(SoftwareConfiguracion.decimales)
            if SoftwareConfiguracion.velocidad == 0:
                radioVelocidadPositiva.setChecked(True)
            else:
                radioVelocidadAmbas.setChecked(True)
            if SoftwareConfiguracion.filtrado == 0:
                radioFiltroSinfechas.setChecked(True)
            else:
                radioFiltroConfechas.setChecked(True)
            if SoftwareConfiguracion.precipitacion == 0:
                radioLluviaVisible.setChecked(True)
            else:
                radioLluviaAutoma.setChecked(True)
            if SoftwareConfiguracion.mostrarpluvio == 0:
                radioLluviaArriba.setChecked(True)
            else:
                radioLluviaAbajo.setChecked(True)
            if SoftwareConfiguracion.celda == 0:
                radioCeldaPositiva.setChecked(True)
            else:
                radioCeldaNegativa.setChecked(True)
            
            checkSuavizado.setChecked(True if SoftwareConfiguracion.suavizado == 1 else False)
            
        def cambiarColor():
            colorcito = QColorDialog.getColor()
            if colorcito.isValid():
                botonTendencia.setStyleSheet("background-color: %s" % colorcito.name())
        def guardarAjustes():
            titulo = spinTitulo.value()
            ejes = spinEjes.value()
            etiquetas = spinEtiquetas.value()
            leyenda = spinLeyenda.value()
            cotas = spinCotas.value()
            if checkCotas.isChecked():
                mostrarcotas = 1
            else:
                mostrarcotas = 0
            if checkVertices.isChecked():
                mostrarvertices = 1
            else:
                mostrarvertices = 0
            tipotendencia = comboTendencia.currentData()
            grosortendencia = spinTendencia.value()
            colortendencia = botonTendencia.palette().color(QPalette.Button).name()
            fuente = comboFuente.currentFont()
            font_name = fuente.family()
            transparente = spinTransparencia.value()
            lineagrosor = spinGrosorlineas.value()
            verticegrosor = spinGrosorvertices.value()
            cantidecimales = spinDecimales.value()
            if radioVelocidadPositiva.isChecked():
                velocidadprisma = 0
            elif radioVelocidadAmbas.isChecked():
                velocidadprisma = 1
            if radioFiltroSinfechas.isChecked():
                filtrofecha = 0
            elif radioFiltroConfechas.isChecked():
                filtrofecha = 1
            if radioLluviaVisible.isChecked():
                lluvia = 0
            elif radioLluviaAutoma.isChecked():
                lluvia = 1
            if radioLluviaArriba.isChecked():
                poslluvia = 0
            elif radioLluviaAbajo.isChecked():
                poslluvia = 1
            if radioCeldaPositiva.isChecked():
                velocidadcelda = 0
            elif radioCeldaNegativa.isChecked():
                velocidadcelda = 1
                
            suavizado_valor = 1 if checkSuavizado.isChecked() else 0
            # Lista de datos que se enviarán al controlador
            lista_datos = {
                "titulo": titulo,
                "ejes": ejes,
                "etiquetas": etiquetas,
                "leyenda": leyenda,
                "cotas": cotas,
                "mostrarcota": mostrarcotas,
                "mostrarvertice": mostrarvertices,
                "tipotendencia": tipotendencia,
                "grosortendencia": grosortendencia,
                "colortendencia": colortendencia,
                "tipoletra": font_name,
                "transparente": transparente,
                "lineagrosor": lineagrosor,
                "verticegrosor": verticegrosor,
                "cantidecimales": cantidecimales,
                "velocidad_prisma": velocidadprisma,
                "filtrofecha": filtrofecha,
                "precipitacion": lluvia,
                "mostrarlluvia": poslluvia,
                "velocidad_celda": velocidadcelda,
                "suavizado": suavizado_valor,
                "fechahora": 1 if checkFechaHora.isChecked() else 0,
                "mesletras": 1 if checkMesLetras.isChecked() else 0
            }
            respuesta = EmpresaController.ctrlRegistrarActualizarAjustesSoftware(lista_datos)
            if respuesta:
                dialog.close()
                SoftwareConfiguracion.actualizarInfoSoftware()
            else:
                labelmensaje.setText("No se guardaron los ajustes.")
        # conectar señales
        botonTendencia.clicked.connect(cambiarColor)
        confirmarAjustes.clicked.connect(guardarAjustes)
        dialog.exec()
    
    def actualizarInfoSoftware():
        respuesta = EmpresaController.ctrlObtenerDatosConfiguracionSoftware()
        if respuesta:
            SoftwareConfiguracion.titulo = respuesta[1]
            SoftwareConfiguracion.ejes = respuesta[2]
            SoftwareConfiguracion.etiqueta = respuesta[3]
            SoftwareConfiguracion.leyenda = respuesta[4]
            SoftwareConfiguracion.cotas = respuesta[5]
            SoftwareConfiguracion.mostrarcota = respuesta[6]
            SoftwareConfiguracion.mostrarvertice = respuesta[7]
            SoftwareConfiguracion.tipotendencia = respuesta[8]
            SoftwareConfiguracion.grosortendencia = respuesta[9]
            SoftwareConfiguracion.colortendencia = respuesta[10]
            if respuesta[11] == "SansSerif":
                SoftwareConfiguracion.letra = "sans-serif"
            else:
                SoftwareConfiguracion.letra = respuesta[11]
            SoftwareConfiguracion.transparencia = respuesta[12]
            SoftwareConfiguracion.grosorlineas = respuesta[13]
            SoftwareConfiguracion.grosorvertices = respuesta[14]
            SoftwareConfiguracion.decimales = respuesta[15]
            SoftwareConfiguracion.velocidad = respuesta[16]
            SoftwareConfiguracion.filtrado = respuesta[17]
            SoftwareConfiguracion.precipitacion = respuesta[18]
            SoftwareConfiguracion.mostrarpluvio = respuesta[19]
            SoftwareConfiguracion.celda = respuesta[20]
            SoftwareConfiguracion.suavizado = respuesta[21] if len(respuesta) > 21 else 0
            SoftwareConfiguracion.fechahora = respuesta[22] if len(respuesta) > 22 else 0
            SoftwareConfiguracion.mesletras = respuesta[23] if len(respuesta) > 23 else 0
    
    def obtenerDataSoftware():
        data = [
            SoftwareConfiguracion.titulo,
            SoftwareConfiguracion.ejes,
            SoftwareConfiguracion.etiqueta,
            SoftwareConfiguracion.leyenda,
            SoftwareConfiguracion.cotas,
            SoftwareConfiguracion.mostrarcota,
            SoftwareConfiguracion.mostrarvertice,
            SoftwareConfiguracion.tipotendencia,
            SoftwareConfiguracion.grosortendencia,
            SoftwareConfiguracion.colortendencia,
            SoftwareConfiguracion.letra,
            SoftwareConfiguracion.transparencia,
            SoftwareConfiguracion.grosorlineas,
            SoftwareConfiguracion.grosorvertices,
            SoftwareConfiguracion.decimales,
            SoftwareConfiguracion.velocidad,
            SoftwareConfiguracion.filtrado,
            SoftwareConfiguracion.precipitacion,
            SoftwareConfiguracion.mostrarpluvio,
            SoftwareConfiguracion.celda,
            SoftwareConfiguracion.suavizado,
            SoftwareConfiguracion.fechahora, # Índice 21
            SoftwareConfiguracion.mesletras, # Índice 22
            SoftwareConfiguracion.version
        ]
        return data
    