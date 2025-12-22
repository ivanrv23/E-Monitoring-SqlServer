from PySide6 import QtWidgets, QtGui
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QDialog, QColorDialog
from utils.common.rutasarchivos import resource_path
from controllers.ConfiguracionController import ConfiguracionController

class ConfiguracionVisor:
    estadoConfirmacion, estadoexiste = False, False
    colorFondo, colorTexto, colorPrisma, colorInclinometro, colorPiezometro = '#FFFFFF', '#000000', '#0000FF', '#FF0000', '#993300'
    colorPluviometro, colorCelda, colorAcelerografo, colorTDR = '#00FFFF', '#FF00FF', '#666666', '#000000'
    tamanioTexto, tamanioPrisma, tamanioInclinometro, tamanioPiezometro, tamanioPluviometro = 10, 10, 10, 10, 10
    tamanioCelda, tamanioAcelerografo, tamanioTDR, tamanioVector = 10, 10, 10, 4
    
    def modalConfiguracionVisor(idproyecto):
        ConfiguracionVisor.estadoConfirmacion, ConfiguracionVisor.estadoexiste = False, False
        # Dialogo personalizar
        loader = QUiLoader()
        ui_file_path = resource_path("ui/configuraciontoolsvisor.ui")
        ui_file = loader.load(ui_file_path, None)
        # Configurar el cuadro de diálogo
        dialogConfigVisor = QDialog()
        dialogConfigVisor.setWindowTitle("Configuración del Visor")
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(ui_file)
        dialogConfigVisor.setLayout(layout)
        # Inicializar tools
        spinTamañoTexto = dialogConfigVisor.findChild(QtWidgets.QDoubleSpinBox, "spin_tamanio_texto")
        botonColorFondo = dialogConfigVisor.findChild(QtWidgets.QPushButton, "btn_color_fondo")
        spinTamañoVector = dialogConfigVisor.findChild(QtWidgets.QDoubleSpinBox, "spin_tamanio_vector")
        botonColorTexto = dialogConfigVisor.findChild(QtWidgets.QPushButton, "btn_color_texto")
        spinTamañoPrisma = dialogConfigVisor.findChild(QtWidgets.QDoubleSpinBox, "spin_tamanio_prisma")
        botonColorPrisma = dialogConfigVisor.findChild(QtWidgets.QPushButton, "btn_color_prisma")
        spinTamañoIncli = dialogConfigVisor.findChild(QtWidgets.QDoubleSpinBox, "spin_tamanio_inclinometro")
        botonColorIncli = dialogConfigVisor.findChild(QtWidgets.QPushButton, "btn_color_inclinometro")
        spinTamañoPiezo = dialogConfigVisor.findChild(QtWidgets.QDoubleSpinBox, "spin_tamanio_piezometro")
        botonColorPiezo = dialogConfigVisor.findChild(QtWidgets.QPushButton, "btn_color_piezometro")
        spinTamañoPluvio = dialogConfigVisor.findChild(QtWidgets.QDoubleSpinBox, "spin_tamanio_pluviometro")
        botonColorPluvio = dialogConfigVisor.findChild(QtWidgets.QPushButton, "btn_color_pluviometro")
        spinTamañoCelda = dialogConfigVisor.findChild(QtWidgets.QDoubleSpinBox, "spin_tamanio_celda")
        botonColorCelda = dialogConfigVisor.findChild(QtWidgets.QPushButton, "btn_color_celda")
        spinTamañoAcelero = dialogConfigVisor.findChild(QtWidgets.QDoubleSpinBox, "spin_tamanio_acelerografo")
        botonColorAcelero = dialogConfigVisor.findChild(QtWidgets.QPushButton, "btn_color_acelerografo")
        spinTamañoTdr = dialogConfigVisor.findChild(QtWidgets.QDoubleSpinBox, "spin_tamanio_tdr")
        botonColorTdr = dialogConfigVisor.findChild(QtWidgets.QPushButton, "btn_color_tdr")
        labelmensaje = dialogConfigVisor.findChild(QtWidgets.QLabel, "label_mensaje")
        botonConfirmar = dialogConfigVisor.findChild(QtWidgets.QPushButton, "btn_confirmar")
        # Traer configuracion de visor
        info = ConfiguracionController.ctrlListarConfiguracionVisor(idproyecto)
        if info:
            ConfiguracionVisor.estadoexiste = True
            # botones Color
            botonColorFondo.setStyleSheet("background-color: %s;" % QtGui.QColor(info[2]).name())
            botonColorTexto.setStyleSheet("background-color: %s;" % QtGui.QColor(info[4]).name())
            botonColorPrisma.setStyleSheet("background-color: %s;" % QtGui.QColor(info[6]).name())
            botonColorIncli.setStyleSheet("background-color: %s;" % QtGui.QColor(info[8]).name())
            botonColorPiezo.setStyleSheet("background-color: %s;" % QtGui.QColor(info[10]).name())
            botonColorPluvio.setStyleSheet("background-color: %s;" % QtGui.QColor(info[12]).name())
            botonColorCelda.setStyleSheet("background-color: %s;" % QtGui.QColor(info[14]).name())
            botonColorAcelero.setStyleSheet("background-color: %s;" % QtGui.QColor(info[16]).name())
            botonColorTdr.setStyleSheet("background-color: %s;" % QtGui.QColor(info[18]).name())
            spinTamañoTexto.setValue(float(info[3]))
            spinTamañoPrisma.setValue(float(info[5]))
            spinTamañoIncli.setValue(float(info[7]))
            spinTamañoPiezo.setValue(float(info[9]))
            spinTamañoPluvio.setValue(float(info[11]))
            spinTamañoCelda.setValue(float(info[13]))
            spinTamañoAcelero.setValue(float(info[15]))
            spinTamañoTdr.setValue(float(info[17]))
            spinTamañoVector.setValue(float(info[19]))
        else:
            botonColorFondo.setStyleSheet("background-color: %s;" % QtGui.QColor(ConfiguracionVisor.colorFondo).name())
            botonColorTexto.setStyleSheet("background-color: %s;" % QtGui.QColor(ConfiguracionVisor.colorTexto).name())
            botonColorPrisma.setStyleSheet("background-color: %s;" % QtGui.QColor(ConfiguracionVisor.colorPrisma).name())
            botonColorIncli.setStyleSheet("background-color: %s;" % QtGui.QColor(ConfiguracionVisor.colorInclinometro).name())
            botonColorPiezo.setStyleSheet("background-color: %s;" % QtGui.QColor(ConfiguracionVisor.colorPiezometro).name())
            botonColorPluvio.setStyleSheet("background-color: %s;" % QtGui.QColor(ConfiguracionVisor.colorPluviometro).name())
            botonColorCelda.setStyleSheet("background-color: %s;" % QtGui.QColor(ConfiguracionVisor.colorCelda).name())
            botonColorAcelero.setStyleSheet("background-color: %s;" % QtGui.QColor(ConfiguracionVisor.colorAcelerografo).name())
            botonColorTdr.setStyleSheet("background-color: %s;" % QtGui.QColor(ConfiguracionVisor.colorTDR).name())
            spinTamañoTexto.setValue(float(ConfiguracionVisor.tamanioTexto))
            spinTamañoPrisma.setValue(float(ConfiguracionVisor.tamanioPrisma))
            spinTamañoIncli.setValue(float(ConfiguracionVisor.tamanioInclinometro))
            spinTamañoPiezo.setValue(float(ConfiguracionVisor.tamanioPiezometro))
            spinTamañoPluvio.setValue(float(ConfiguracionVisor.tamanioPluviometro))
            spinTamañoCelda.setValue(float(ConfiguracionVisor.tamanioCelda))
            spinTamañoAcelero.setValue(float(ConfiguracionVisor.tamanioAcelerografo))
            spinTamañoTdr.setValue(float(ConfiguracionVisor.tamanioTDR))
            spinTamañoVector.setValue(float(ConfiguracionVisor.tamanioVector))
        def obtenerColor(botonColor):
            color = QColorDialog.getColor()
            if color.isValid():
                botonColor.setStyleSheet("background-color: %s" % color.name())
        def confirmarConfiguracion():
            fondocolor = botonColorFondo.palette().color(QtGui.QPalette.Button).name()
            textocolor = botonColorTexto.palette().color(QtGui.QPalette.Button).name()
            prismacolor = botonColorPrisma.palette().color(QtGui.QPalette.Button).name()
            inclicolor = botonColorIncli.palette().color(QtGui.QPalette.Button).name()
            piezocolor = botonColorPiezo.palette().color(QtGui.QPalette.Button).name()
            pluviocolor = botonColorPluvio.palette().color(QtGui.QPalette.Button).name()
            celdacolor = botonColorCelda.palette().color(QtGui.QPalette.Button).name()
            acelerocolor = botonColorAcelero.palette().color(QtGui.QPalette.Button).name()
            tdrcolor = botonColorTdr.palette().color(QtGui.QPalette.Button).name()
            textosize = spinTamañoTexto.value()
            prismasize = spinTamañoPrisma.value()
            inclisize = spinTamañoIncli.value()
            piezosize = spinTamañoPiezo.value()
            pluviosize = spinTamañoPluvio.value()
            celdasize = spinTamañoCelda.value()
            acelerosize = spinTamañoAcelero.value()
            tdrsize = spinTamañoTdr.value()
            vectorsize = spinTamañoVector.value()
            # Lista de datos que se enviarán al controlador
            lista_datos = {
                "idproyecto": idproyecto,
                "colorfondo": fondocolor,
                "tamaniotexto": textosize,
                "colortexto": textocolor,
                "tamanioprisma": prismasize,
                "colorprisma": prismacolor,
                "tamanioinclino": inclisize,
                "colorinclino": inclicolor,
                "tamaniopiezo": piezosize,
                "colorpiezo": piezocolor,
                "tamaniopluvio": pluviosize,
                "colorpluvio": pluviocolor,
                "tamaniocelda": celdasize,
                "colorcelda": celdacolor,
                "tamanioacelero": acelerosize,
                "coloracelero": acelerocolor,
                "tamaniotdr": tdrsize,
                "colortdr": tdrcolor,
                "tamaniovector": vectorsize
            }
            respuesta = ConfiguracionController.ctrlRegistrarActualizarAjustesVisor(lista_datos, ConfiguracionVisor.estadoexiste)
            if respuesta:
                ConfiguracionVisor.estadoConfirmacion = True
                dialogConfigVisor.close()
                ConfiguracionVisor.actualizarInfoConfiguracionVisor(idproyecto)
            else:
                labelmensaje.setText("Error al guardar los ajustes.")
        # conectar con metodos
        botonColorFondo.clicked.connect(lambda: obtenerColor(botonColorFondo))
        botonColorTexto.clicked.connect(lambda: obtenerColor(botonColorTexto))
        botonColorPrisma.clicked.connect(lambda: obtenerColor(botonColorPrisma))
        botonColorIncli.clicked.connect(lambda: obtenerColor(botonColorIncli))
        botonColorPiezo.clicked.connect(lambda: obtenerColor(botonColorPiezo))
        botonColorPluvio.clicked.connect(lambda: obtenerColor(botonColorPluvio))
        botonColorCelda.clicked.connect(lambda: obtenerColor(botonColorCelda))
        botonColorAcelero.clicked.connect(lambda: obtenerColor(botonColorAcelero))
        botonColorTdr.clicked.connect(lambda: obtenerColor(botonColorTdr))
        botonConfirmar.clicked.connect(confirmarConfiguracion)
        dialogConfigVisor.exec()
        return ConfiguracionVisor.estadoConfirmacion
    
    def actualizarInfoConfiguracionVisor(idproyecto):
        respuesta = ConfiguracionController.ctrlListarConfiguracionVisor(idproyecto)
        if respuesta:
            ConfiguracionVisor.colorFondo = respuesta[2]
            ConfiguracionVisor.colorTexto = respuesta[4]
            ConfiguracionVisor.colorPrisma = respuesta[6]
            ConfiguracionVisor.colorInclinometro = respuesta[8]
            ConfiguracionVisor.colorPiezometro = respuesta[10]
            ConfiguracionVisor.colorPluviometro = respuesta[12]
            ConfiguracionVisor.colorCelda = respuesta[14]
            ConfiguracionVisor.colorAcelerografo = respuesta[16]
            ConfiguracionVisor.colorTDR = respuesta[18]
            ConfiguracionVisor.tamanioTexto = respuesta[3]
            ConfiguracionVisor.tamanioPrisma = respuesta[5]
            ConfiguracionVisor.tamanioInclinometro = respuesta[7]
            ConfiguracionVisor.tamanioPiezometro = respuesta[9]
            ConfiguracionVisor.tamanioPluviometro = respuesta[11]
            ConfiguracionVisor.tamanioCelda = respuesta[13]
            ConfiguracionVisor.tamanioAcelerografo = respuesta[15]
            ConfiguracionVisor.tamanioTDR = respuesta[17]
            ConfiguracionVisor.tamanioVector = respuesta[19]
    
    def obtenerDataConfiguracionVisor():
        data = [
            ConfiguracionVisor.colorFondo,
            ConfiguracionVisor.tamanioTexto,
            ConfiguracionVisor.colorTexto,
            ConfiguracionVisor.tamanioPrisma,
            ConfiguracionVisor.colorPrisma,
            ConfiguracionVisor.tamanioInclinometro,
            ConfiguracionVisor.colorInclinometro,
            ConfiguracionVisor.tamanioPiezometro,
            ConfiguracionVisor.colorPiezometro,
            ConfiguracionVisor.tamanioPluviometro,
            ConfiguracionVisor.colorPluviometro,
            ConfiguracionVisor.tamanioCelda,
            ConfiguracionVisor.colorCelda,
            ConfiguracionVisor.tamanioAcelerografo,
            ConfiguracionVisor.colorAcelerografo,
            ConfiguracionVisor.tamanioTDR,
            ConfiguracionVisor.colorTDR,
            ConfiguracionVisor.tamanioVector
        ]
        return data
    