import re
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator, QPalette, QFont
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QComboBox, QPushButton, QFormLayout, QDoubleSpinBox, QDialogButtonBox,
                            QMessageBox, QLabel, QLineEdit, QSpinBox, QTextEdit, QColorDialog, QTreeWidget, QTableView, QGridLayout,QFileDialog)
import os
import shutil
from utils.common.rutasarchivos import resource_path
from utils.common.alertas import mostrar_mensaje
from utils.generic.cargariconos import cargarIcono
from controllers.InterfazController import InterfazController
from utils.generic.listaiconos import ListaIconos
from controllers.PiezometroController import PiezometroController
from controllers.ProyectoController import ProyectoController
from controllers.TDRController import TDRController
from controllers.AcelerografoController import AcelerografoController
from controllers.PluviometroController import PluviometroController
from controllers.TerrenoController import TerrenoController
from controllers.EquipoController import EquipoController
from utils.shared.arbolmarcado import TreeCheckbox

class RegistroEquipos:
    
    # MOSTRAR DIALOGO DE NUEVO PIEZÓMETRO DE CUERDA VIBRANTE           
    def dialogoNuevoPiezometroCuerda(proyectoid):
        loader = QUiLoader()
        ui_file_path = resource_path("ui/nuevopiezometrocuerda.ui")
        ui_file = loader.load(ui_file_path, None)
        # Configurar el cuadro de diálogo
        dialog = QDialog()
        dialog.setWindowTitle("Nuevo Piezómetro Cuerda Vibrante")
        layout = QVBoxLayout()
        layout.addWidget(ui_file)
        dialog.setLayout(layout)
        # Obtener elementos para interactuar
        comboComponente = dialog.findChild(QComboBox, "cb_lista_componentes")
        nombrePiezo = dialog.findChild(QLineEdit, "input_nombre")
        serieSensor = dialog.findChild(QLineEdit, "input_serie_sensor")
        comboFormula = dialog.findChild(QComboBox, "combo_formula")
        botonFormula = dialog.findChild(QPushButton, "btn_formula")
        cargarIcono(botonFormula, ListaIconos.ICONOS["calculadora"])
        nortePiezo = dialog.findChild(QDoubleSpinBox, "input_norte")
        estePiezo = dialog.findChild(QDoubleSpinBox, "input_este")
        instalacionPiezo = dialog.findChild(QDoubleSpinBox, "input_cota_instalacion")
        fundacionPiezo = dialog.findChild(QDoubleSpinBox, "input_cota_fundacion")
        cotaactualPiezo = dialog.findChild(QDoubleSpinBox, "input_cota_actual")
        factorCalibracion = dialog.findChild(QDoubleSpinBox, "input_factor_calibracion")
        correccionTempe = dialog.findChild(QDoubleSpinBox, "input_correccion_temperatura")
        lecturaInicial = dialog.findChild(QDoubleSpinBox, "input_frecuencia_inicial")
        temperaInicial = dialog.findChild(QDoubleSpinBox, "input_tempeartura_inicial")
        presionInicial = dialog.findChild(QDoubleSpinBox, "input_presion_inicial")
        unidadLectura = dialog.findChild(QComboBox, "combo_unidad_frecuencia")
        constanteA = dialog.findChild(QDoubleSpinBox, "input_constante_a")
        constanteB = dialog.findChild(QDoubleSpinBox, "input_constante_b")
        constanteC = dialog.findChild(QDoubleSpinBox, "input_constante_c")
        inclinacionPiezo = dialog.findChild(QSpinBox, "input_inclinacion")
        azimutPiezo = dialog.findChild(QSpinBox, "input_azimut")
        factorConversion = dialog.findChild(QDoubleSpinBox, "input_factor_conversion")
        comboEstados = dialog.findChild(QComboBox, "cb_estados")
        comentarioPiezo = dialog.findChild(QTextEdit, "input_comentario")
        lblrespuesta = dialog.findChild(QLabel, "label_mensaje_error")
        botonguardar = dialog.findChild(QPushButton, "btn_guardar_nuevo")
        
        # --- Cargando el ComboBox de Estados ---
        comboEstados.addItems(["Operativo", "Inoperativo"])

        # cargar data componentes
        RegistroEquipos.llenar_componentes_combo(proyectoid, comboComponente)
        comboFormula.addItem("Seleccione Fórmula", 0)
        formulas = PiezometroController.ctrlTraerListaFormulas()
        if formulas:
            for fila in formulas:
                comboFormula.addItem(str(fila[1]), fila[0])
        def guardarNuevoPiezometro():
            componente = comboComponente.currentData()
            formula = comboFormula.currentData()
            nombre = nombrePiezo.text()
            serie = serieSensor.text()
            este = estePiezo.value()
            norte = nortePiezo.value()
            instalacion = instalacionPiezo.value()
            fundacion = fundacionPiezo.value()
            nivelactual = cotaactualPiezo.value()
            calibracion = factorCalibracion.value()
            tempecorrec = correccionTempe.value()
            inclinacion = inclinacionPiezo.value()
            azimut = azimutPiezo.value()
            lecturaini = lecturaInicial.value()
            temperaini = temperaInicial.value()
            presionini = presionInicial.value()
            lectura = unidadLectura.currentText()
            variablea = constanteA.value()
            variableb = constanteB.value()
            variablec = constanteC.value()
            conversion = factorConversion.value()
            comentario = comentarioPiezo.toPlainText()
            estado = comboEstados.currentText()
            estado_valor = 1 if estado == "Operativo" else 0
            if nombre != "" and proyectoid != 0:
                respu = PiezometroController.ctrlGuardarNuevoPiezometroCuerda(proyectoid, componente, formula, nombre, serie, este, norte, instalacion, fundacion, nivelactual, inclinacion, azimut, lecturaini, temperaini, presionini, calibracion, tempecorrec, lectura, variablea, variableb, variablec, conversion, comentario, estado_valor)
                if respu == "OK":
                    lblrespuesta.setText("Registrado Correctamente")
                    lblrespuesta.setStyleSheet("color: green;")
                    # Limpiar los inputs
                    nombrePiezo.clear()
                    serieSensor.clear()
                    estePiezo.setValue(0)
                    nortePiezo.setValue(0)
                    instalacionPiezo.setValue(0)
                    fundacionPiezo.setValue(0)
                    cotaactualPiezo.setValue(0)
                    inclinacionPiezo.setValue(90)
                    azimutPiezo.setValue(0)
                    lecturaInicial.setValue(0)
                    temperaInicial.setValue(0)
                    factorCalibracion.setValue(0)
                    correccionTempe.setValue(0)
                    constanteA.setValue(0)
                    constanteB.setValue(0)
                    constanteC.setValue(0)
                    factorConversion.setValue(0)
                    comentarioPiezo.clear()
                elif respu == "NO":
                    lblrespuesta.setText("¡Ya existe piezómetro con el mismo nombre!")
                    lblrespuesta.setStyleSheet("color: orange;")
                else:
                    lblrespuesta.setText("¡Error al guardar los datos!")
                    lblrespuesta.setStyleSheet("color: red;")
            else:
                lblrespuesta.setText("¡Algunos datos están vacíos!")
                lblrespuesta.setStyleSheet("color: orange;")
        # Inicializar botones
        lblrespuesta.setText("")
        botonFormula.clicked.connect(RegistroEquipos.mostrarCalculadora)
        botonguardar.clicked.connect(guardarNuevoPiezometro)
        # mostrar dialogo
        dialog.exec()
    
    # MOSTRAR DIALOGO DE NUEVO PIEZÓMETRO MANUAL
    def dialogoNuevoPiezometroManual(proyectoid):
        loader = QUiLoader()
        ui_file_path = resource_path("ui/nuevopiezometromanual.ui")
        ui_file = loader.load(ui_file_path, None)
        # Configurar el cuadro de diálogo
        dialog = QDialog()
        dialog.setWindowTitle("Nuevo Piezómetro Casagrande")
        layout = QVBoxLayout()
        layout.addWidget(ui_file)
        dialog.setLayout(layout)
        # Obtener elementos para interactuar
        comboComponente = dialog.findChild(QComboBox, "cb_lista_componentes")
        nombrePiezo = dialog.findChild(QLineEdit, "input_nombre")
        codigoPiezo = dialog.findChild(QLineEdit, "input_codigo")
        nortePiezo = dialog.findChild(QDoubleSpinBox, "input_norte")
        estePiezo = dialog.findChild(QDoubleSpinBox, "input_este")
        elevacionPiezo = dialog.findChild(QDoubleSpinBox, "input_elevacion")
        fundacionPiezo = dialog.findChild(QDoubleSpinBox, "input_fundacion")
        stickupPiezo = dialog.findChild(QDoubleSpinBox, "input_stickup")
        profundidadPiezo = dialog.findChild(QDoubleSpinBox, "input_profundidad")
        inclinacionPiezo = dialog.findChild(QSpinBox, "input_inclinacion")
        azimutPiezo = dialog.findChild(QSpinBox, "input_azimut")
        estadonuevo_piezomanual = dialog.findChild(QComboBox, "estadonuevo_piezomanual")
        estadonuevo_piezomanual.addItem("Operativo", 1)
        estadonuevo_piezomanual.addItem("Inoperativo", 0)
        comentarioPiezo = dialog.findChild(QTextEdit, "input_comentario")
        lblrespuesta = dialog.findChild(QLabel, "label_mensaje_error")
        botonguardar = dialog.findChild(QPushButton, "btn_aceptar_nuevo")
        inclinacionPiezo.setValue(90)
        # cargar data componentes
        RegistroEquipos.llenar_componentes_combo(proyectoid, comboComponente)
        def guardarNuevoPiezometro():
            componente = comboComponente.currentData()
            nombre = nombrePiezo.text() 
            codigo = codigoPiezo.text()
            norte = nortePiezo.value()
            este = estePiezo.value()
            nivel = elevacionPiezo.value()
            fundacion = fundacionPiezo.value()
            stick = stickupPiezo.value()
            inclinacion = inclinacionPiezo.value()
            azimut = azimutPiezo.value()
            profundidad = profundidadPiezo.value()
            comentario = comentarioPiezo.toPlainText()
            estado = estadonuevo_piezomanual.currentData()
            if nombre != "" and proyectoid != 0:
                respu = PiezometroController.ctrlGuardarNuevoPiezometroManual(proyectoid, componente, nombre, codigo, norte, este, nivel, fundacion, stick, profundidad, inclinacion, azimut, estado, comentario)
                if respu == "OK":
                    lblrespuesta.setText("Piezómetro Registrado")
                    lblrespuesta.setStyleSheet("color: green;")
                    # Limpiar los inputs
                    nombrePiezo.clear()
                    codigoPiezo.clear()
                    estePiezo.setValue(0)
                    nortePiezo.setValue(0)
                    elevacionPiezo.setValue(0)
                    fundacionPiezo.setValue(0)
                    inclinacionPiezo.setValue(90)
                    azimutPiezo.setValue(0)
                    estadonuevo_piezomanual.setCurrentIndex(0)
                    stickupPiezo.setValue(0)
                    profundidadPiezo.setValue(0)
                    comentarioPiezo.clear()
                elif respu == "NO":
                    lblrespuesta.setText("¡Ya existe piezómetro con el mismo nombre!")
                    lblrespuesta.setStyleSheet("color: orange;")
                else:
                    lblrespuesta.setText("¡Error al guardar los datos!")
                    lblrespuesta.setStyleSheet("color: red;")
            else:
                lblrespuesta.setText("¡Algunos campos están vacíos!")
                lblrespuesta.setStyleSheet("color: red;")
        # Inicializar botones
        lblrespuesta.setText("")
        botonguardar.clicked.connect(guardarNuevoPiezometro)
        # mostrar dialogo
        dialog.exec()
    
    def llenar_componentes_combo(proyecto_id,comboComponente):
        # cargar data componentes
        componentes = ProyectoController.ctrlObtenerComponentesProyecto(proyecto_id)
        if componentes:
            for fila in componentes:
                comboComponente.addItem(str(fila[2]), fila[0])
            comboComponente.setEnabled(True)
    
    ###############################TDR########################################
    # MOSTRAR DIALOGO NUEVO TDR
    def mostrarDialogoRegistroSondajesTDR(proyecto_id):
        loaderLoading = QUiLoader()        
        ui_file_path = resource_path("ui/nuevosondajetdr.ui")
        ui_file = loaderLoading.load(ui_file_path, None)
        dialogoTDR = QDialog()
        dialogoTDR.setWindowTitle("Nuevo Sondaje TDR")
        layout_procesar_data = QVBoxLayout()
        layout_procesar_data.addWidget(ui_file)
        dialogoTDR.setLayout(layout_procesar_data)
        comboComponente = dialogoTDR.findChild(QComboBox, "cb_lista_componentes")
        botonguardar = dialogoTDR.findChild(QPushButton, "btn_registrar")
        lblrespuesta = dialogoTDR.findChild(QLabel, "label_mensaje")
        nombreTDR = dialogoTDR.findChild(QLineEdit, "input_sondaje")
        norteTDR = dialogoTDR.findChild(QDoubleSpinBox, "input_norte")
        esteTDR = dialogoTDR.findChild(QDoubleSpinBox, "input_este")
        elevacionTDR = dialogoTDR.findChild(QDoubleSpinBox, "input_nivel")
        produndidadTDR = dialogoTDR.findChild(QDoubleSpinBox, "input_profundidad")
        azimutTDR = dialogoTDR.findChild(QSpinBox, "input_azimut")
        inclinacionTDR = dialogoTDR.findChild(QSpinBox, "input_inclinacion")
        combo_estado_tdr = dialogoTDR.findChild(QComboBox, "combo_estado_tdr")
        combo_estado_tdr.addItem("Operativo", 1)
        combo_estado_tdr.addItem("Inoperativo", 0)
        RegistroEquipos.llenar_componentes_combo(proyecto_id, comboComponente)
        def guardarNuevoTDR():
            componente = comboComponente.currentData()
            nombre = nombreTDR.text()
            norte = norteTDR.value()
            este = esteTDR.value()
            nivel = elevacionTDR.value()
            profun = produndidadTDR.value()
            azimut = azimutTDR.value()
            inclinacion = inclinacionTDR.value()
            estado = combo_estado_tdr.currentData()
            data = [nombre, este, norte, nivel, azimut, inclinacion, profun, componente, estado]
            respuesta = TDRController.ctrlGuardarEquipoTDR(proyecto_id, data)
            if respuesta == "NO":
                lblrespuesta.setText("El nombre y el componente ya existen.")
                lblrespuesta.setStyleSheet("color: orange;")
            elif respuesta:
                lblrespuesta.setText("Sondaje guardado exitosamente.")
                lblrespuesta.setStyleSheet("color: green;")
                # Limpiar los inputs
                nombreTDR.clear()
                esteTDR.setValue(0)
                norteTDR.setValue(0)
                elevacionTDR.setValue(0)
                produndidadTDR.setValue(0)
                inclinacionTDR.setValue(90)
                azimutTDR.setValue(0)
                combo_estado_tdr.setCurrentIndex(0) 
            else:
                lblrespuesta.setText("Error al guardar el sondaje.")
                lblrespuesta.setStyleSheet("color: red;")
        # Inicializar botones
        lblrespuesta.setText("")
        botonguardar.clicked.connect(guardarNuevoTDR)
        dialogoTDR.exec()
        
    ###############################Acelerógrafos########################################
    def dialogoRegistroAcelerografos(proyecto_id):
        loaderLoading = QUiLoader()
        ui_file_path = resource_path("ui/nuevoacelerografo.ui")
        ui_file = loaderLoading.load(ui_file_path, None)
        dialogoAcelerografo = QDialog()
        dialogoAcelerografo.setWindowTitle("Nuevo Acelerógrafo")
        layout_procesar_data = QVBoxLayout()
        layout_procesar_data.addWidget(ui_file)
        dialogoAcelerografo.setLayout(layout_procesar_data)
        # Validando inputs
        comboComponente = dialogoAcelerografo.findChild(QComboBox, "cb_lista_componentes")
        nombreacelero = dialogoAcelerografo.findChild(QLineEdit, 'input_acelerografo')
        este = dialogoAcelerografo.findChild(QLineEdit, 'input_este')
        norte = dialogoAcelerografo.findChild(QLineEdit, 'input_norte')
        cota = dialogoAcelerografo.findChild(QLineEdit, 'input_cota')
        lblrespuesta = dialogoAcelerografo.findChild(QLabel, "label_mensaje")
        RegistroEquipos.llenar_componentes_combo(proyecto_id, comboComponente)
        validator = QDoubleValidator()
        este.setValidator(validator)
        norte.setValidator(validator)
        cota.setValidator(validator)
        botonGuardarData = dialogoAcelerografo.findChild(QPushButton, "btn_guardar")
        nombreXML = dialogoAcelerografo.findChild(QLineEdit, 'input_nombre_xml')
        botonSubirXML = dialogoAcelerografo.findChild(QPushButton, "btn_cargar_xml")
        combo_estado_acel = dialogoAcelerografo.findChild(QComboBox, "combo_estado_acel")
        combo_estado_acel.addItem("Operativo", 1)
        combo_estado_acel.addItem("Inoperativo", 0)
        def subirXML():
            # Abrir diálogo para seleccionar archivo
            file_dialog = QFileDialog()
            file_path, _ = file_dialog.getOpenFileName(dialogoAcelerografo, "Seleccionar archivo XML", "", "XML Files (*.xml)")
            if file_path:
                # Mostrar el nombre del archivo en el QLineEdit
                nombreXML.setText(file_path)
        def guardarInfoAcelero():
            componente = comboComponente.currentData()
            nombre = nombreacelero.text()
            coorx = este.text()
            coory = norte.text()
            coorz = cota.text()
            archivo_xml = nombreXML.text()
            estado = combo_estado_acel.currentData()
            if nombre:
                datos = [nombre, coorx, coory, coorz, componente, estado]
                respuesta, id_acelerografo = AcelerografoController.ctrlRegistrarAcelerografo(proyecto_id, datos)
                if respuesta == "NO":
                    lblrespuesta.setText("El equipo ya existe.")
                    lblrespuesta.setStyleSheet("color: orange;")
                elif respuesta == "SI":
                    if archivo_xml:
                        carpeta_destino = resource_path(f'resources/workspace/ACELEROGRAFOS/proyecto{proyecto_id}/{id_acelerografo}')
                        # Verificar si la carpeta de destino existe, si no, créala
                        if not os.path.exists(carpeta_destino):
                            os.makedirs(carpeta_destino)
                        # Ruta completa del archivo XML de destino
                        destino_xml = os.path.join(carpeta_destino, os.path.basename(archivo_xml))
                        try:
                            # Copiar el archivo XML a la nueva ruta
                            shutil.copy(archivo_xml, destino_xml)
                            lblrespuesta.setText("Acelerógrafo registrado exitosamente.")
                            lblrespuesta.setStyleSheet("color: green;")
                            # Limpiar los inputs
                            nombreacelero.clear()
                            este.setText("0")
                            norte.setText("0")
                            cota.setText("0")
                            nombreXML.clear()
                        except Exception as e:
                            lblrespuesta.setText(f"Registrado, error al copiar el archivo XML: {e}")
                            lblrespuesta.setStyleSheet("color: orange;")
                    else:
                        lblrespuesta.setText("Acelerógrafo registrado exitosamente.")
                        lblrespuesta.setStyleSheet("color: green;")
                        # Limpiar los inputs
                        nombreacelero.clear()
                        este.setText("0")
                        norte.setText("0")
                        cota.setText("0")
                else:
                    lblrespuesta.setText("Error al registrar el acelerógrafo.")
                    lblrespuesta.setStyleSheet("color: red;")
        # conectar botones
        botonSubirXML.clicked.connect(subirXML)
        botonGuardarData.clicked.connect(guardarInfoAcelero)
        dialogoAcelerografo.exec()

    ###############################Pluviómetros########################################
    def mostrarDialogoRegistroPluviometros(proyecto_id):
        loaderLoading = QUiLoader()        
        ui_file_path = resource_path("ui/nuevopluviometro.ui")
        ui_file = loaderLoading.load(ui_file_path, None)
        dialogopluviometros = QDialog()
        dialogopluviometros.setWindowTitle("Nuevo Pluviómetro")
        layout_procesar_data = QVBoxLayout()
        layout_procesar_data.addWidget(ui_file)
        dialogopluviometros.setLayout(layout_procesar_data)
        # Obtener elementos para interactuar
        comboComponente = dialogopluviometros.findChild(QComboBox, "cb_lista_componentes")
        nombrePluvio = dialogopluviometros.findChild(QLineEdit, "input_nombre")
        codigoPluvio = dialogopluviometros.findChild(QLineEdit, "input_codigo")
        nortePluvio = dialogopluviometros.findChild(QDoubleSpinBox, "input_norte")
        estePluvio = dialogopluviometros.findChild(QDoubleSpinBox, "input_este")
        elevacionPluvio = dialogopluviometros.findChild(QDoubleSpinBox, "input_nivel")
        comentarioPiezo = dialogopluviometros.findChild(QTextEdit, "input_comentario")
        botonguardar = dialogopluviometros.findChild(QPushButton, "btn_registrar")
        lblrespuesta = dialogopluviometros.findChild(QLabel, "label_mensaje")
        estado_pluvio = dialogopluviometros.findChild(QComboBox, "estado_pluvio")
        estado_pluvio.addItem("Operativo", 1)
        estado_pluvio.addItem("Inoperativo", 0) 

        RegistroEquipos.llenar_componentes_combo(proyecto_id, comboComponente)
        def guardarNuevoPluviometro():
            componente = comboComponente.currentData()
            nombre = nombrePluvio.text() 
            codigo = codigoPluvio.text()
            norte = nortePluvio.value()
            este = estePluvio.value()
            nivel = elevacionPluvio.value()
            comentario = comentarioPiezo.toPlainText()
            estado = estado_pluvio.currentData()
            if nombre:
                datos = [nombre, codigo, norte, este, nivel, comentario, estado, componente]
                respuesta = PluviometroController.ctrlGuardarNuevoPluviometro(proyecto_id, datos)
                if respuesta == "NO":
                    lblrespuesta.setText("El equipo ya existe.")
                    lblrespuesta.setStyleSheet("color: orange;")
                elif respuesta:
                    lblrespuesta.setText("Pluviómetro registrado exitosamente.")
                    lblrespuesta.setStyleSheet("color: green;")
                    # Limpiar los inputs
                    nombrePluvio.clear()
                    codigoPluvio.clear()
                    estePluvio.setValue(0)
                    nortePluvio.setValue(0)
                    elevacionPluvio.setValue(0)
                    comentarioPiezo.clear()
                else:
                    lblrespuesta.setText("Error al registrar el Pluviómetro.")
                    lblrespuesta.setStyleSheet("color: red;")

        botonguardar.clicked.connect(guardarNuevoPluviometro)
        dialogopluviometros.exec()
    
    ###############################Cotas Terreno########################################    
    def mostrarDialogoRegistroCotaTerreno(proyecto_id):
        loaderLoading = QUiLoader()        
        ui_file_path = resource_path("ui/nuevacotaterreno.ui")
        ui_file = loaderLoading.load(ui_file_path, None)
        dialogoCotaTerreno = QDialog()
        dialogoCotaTerreno.setWindowTitle("Nueva Cota de Terreno")
        layout_procesar_data = QVBoxLayout()
        layout_procesar_data.addWidget(ui_file)
        dialogoCotaTerreno.setLayout(layout_procesar_data)
        # Obtener elementos para interactuar
        comboComponente = dialogoCotaTerreno.findChild(QComboBox, "cb_lista_componentes")
        RegistroEquipos.llenar_componentes_combo(proyecto_id, comboComponente)
        nombrecota = dialogoCotaTerreno.findChild(QLineEdit, "input_nombre")
        comentariocota = dialogoCotaTerreno.findChild(QTextEdit, "input_comentario")
        botonguardar = dialogoCotaTerreno.findChild(QPushButton, "btn_registrar")
        lblrespuesta = dialogoCotaTerreno.findChild(QLabel, "label_mensaje")
        if proyecto_id == 0:
            botonguardar.setEnabled(False)
        def guardarNuevaCota():
            componente = comboComponente.currentData()
            nombre = nombrecota.text()
            comentario = comentariocota.toPlainText()
            if nombre:
                respuesta = TerrenoController.ctrlGuardarNuevaCotaTerreno(proyecto_id, componente, nombre, comentario)
                if respuesta == "NO":
                    lblrespuesta.setText("El equipo ya existe.")
                    lblrespuesta.setStyleSheet("color: orange;")
                elif respuesta == "OK":
                    lblrespuesta.setText("Cota registrada exitosamente.")
                    lblrespuesta.setStyleSheet("color: green;")
                    # Limpiar los inputs
                    nombrecota.clear()
                    comentariocota.clear()
                else:
                    lblrespuesta.setText("Error al registrar el Cota.")
                    lblrespuesta.setStyleSheet("color: red;")
            else:
                lblrespuesta.setText("El nombre no debe ir vacío.")
                lblrespuesta.setStyleSheet("color: red;")
        # Inicializar botones
        botonguardar.clicked.connect(guardarNuevaCota)
        dialogoCotaTerreno.exec()
    
    ###############################Equipos Generales########################################   
    def mostrarDialogoEquiposGenerales(main, proyectoid):
        loaderLoading = QUiLoader()        
        ui_file_path = resource_path("ui/equipogeneral.ui")
        ui_file = loaderLoading.load(ui_file_path, None)
        dialogoEquipoGeneral = QDialog()
        dialogoEquipoGeneral.setWindowTitle("Nuevo Equipo General")
        layout_procesar_data = QVBoxLayout()
        layout_procesar_data.addWidget(ui_file)
        dialogoEquipoGeneral.setLayout(layout_procesar_data)
        #  Obtener elementos para interactuar
        comboComponente = dialogoEquipoGeneral.findChild(QComboBox, "cb_lista_componentes")
        RegistroEquipos.llenar_componentes_combo(proyectoid, comboComponente)
        nombreEquipo = dialogoEquipoGeneral.findChild(QLineEdit, "input_nombre")
        tipoEquipo = dialogoEquipoGeneral.findChild(QLineEdit, "input_tipo")
        norteEquipo = dialogoEquipoGeneral.findChild(QDoubleSpinBox, "input_norte")
        esteEquipo = dialogoEquipoGeneral.findChild(QDoubleSpinBox, "input_este")
        nivelEquipo = dialogoEquipoGeneral.findChild(QDoubleSpinBox, "input_nivel")
        figuraEquipo = dialogoEquipoGeneral.findChild(QComboBox, "combo_figura")
        colorEquipo = dialogoEquipoGeneral.findChild(QPushButton, "btn_color")
        tamanioEquipo = dialogoEquipoGeneral.findChild(QSpinBox, "input_tamanio")
        descripEquipo = dialogoEquipoGeneral.findChild(QTextEdit, "input_descripcion")
        botonguardar = dialogoEquipoGeneral.findChild(QPushButton, "btn_registrar")
        lblrespuesta = dialogoEquipoGeneral.findChild(QLabel, "label_mensaje")
        # cargar combo
        figuraEquipo.addItem("◑ Esfera", "Esfera")
        figuraEquipo.addItem("∎ Cilindro", "Cilindro")
        figuraEquipo.addItem("◮ Cono", "Cono")
        figuraEquipo.addItem("❒ Cubo", "Cubo")
        def elegirColorEquipo():
            colorcito = QColorDialog.getColor()
            if colorcito.isValid():
                colorEquipo.setStyleSheet("background-color: %s" % colorcito.name())
        def guardarEquipoGeneral():
            componente = comboComponente.currentData()
            nombre = nombreEquipo.text()
            tipo = tipoEquipo.text()
            norte = norteEquipo.value()
            este = esteEquipo.value()
            nivel = nivelEquipo.value()
            figura = figuraEquipo.currentData()
            color = colorEquipo.palette().color(QPalette.Button).name()
            tamaño = tamanioEquipo.value()
            descripcion = descripEquipo.toPlainText()
            if nombre and tamaño > 0:
                data = [proyectoid, nombre, tipo, norte, este, nivel, figura, color, tamaño, descripcion, componente]
                respuesta, idequipo = EquipoController.ctrlGuardarEquipoGeneral(data)
                if respuesta == "NO":
                    lblrespuesta.setText("El equipo ya existe.")
                    lblrespuesta.setStyleSheet("color: orange;")
                elif respuesta == "OK":
                    lblrespuesta.setText("Equipo registrado exitosamente.")
                    lblrespuesta.setStyleSheet("color: green;")
                    # Limpiar los inputs
                    nombreEquipo.clear()
                    tipoEquipo.clear()
                    esteEquipo.setValue(0)
                    norteEquipo.setValue(0)
                    nivelEquipo.setValue(0)
                    descripEquipo.clear()
                    # actualizar árbol checkbox
                    data = EquipoController.ctrlTraerDataEquipoGeneral(idequipo)
                    if data:
                        idinstrumento, idcomponente, nombrezona = data[0], data[1], data[2]
                        treewidgetdatos = main.findChild(QTreeWidget, "tree_actual_datos")
                        treewidgetvisor = main.findChild(QTreeWidget, "tree_actual_visor")
                        TreeCheckbox.eliminarCheckbox(treewidgetdatos, "Equipos Adicionales", idinstrumento, "adicional")
                        TreeCheckbox.eliminarCheckbox(treewidgetvisor, "Equipos Adicionales", idinstrumento, "adicional")
                        # Crear piezometro cuerda en nuevo componente
                        equipo = InterfazController.ctrlListarComponenteEquipoAdicional(idinstrumento)
                        if equipo:
                            TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetdatos, nombrezona, idcomponente, proyectoid, "Equipos Adicionales", "10", equipo, "adicional")
                            TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetvisor, nombrezona, idcomponente, proyectoid, "Equipos Adicionales", "10", equipo, "adicional")
                else:
                    lblrespuesta.setText("Error al registrar el Equipo.")
                    lblrespuesta.setStyleSheet("color: red;")
            else:
                lblrespuesta.setText("El nombre o el tamaño es erróneo.")
                lblrespuesta.setStyleSheet("color: red;")
        # # Inicializar botones
        colorEquipo.clicked.connect(elegirColorEquipo)
        botonguardar.clicked.connect(guardarEquipoGeneral)
        dialogoEquipoGeneral.exec()
        
    def cambiar_componente_adicionales(idcomponente, idproyecto, treewidget, nombregrupo, tipogrupo, subgrupo, reiniciarvistas):
        dialog = QDialog()
        dialog.setWindowTitle("Componentes Adicionales")
        layout = QFormLayout(dialog)
        # Campo componente
        label_titulo = QLabel("Componente:")
        combo_componente = QComboBox()
        label_mensaje = QLabel("")
        label_mensaje.setAlignment(Qt.AlignCenter)
        label_mensaje.setStyleSheet("QLabel { color: red; }")
        # cargar data componentes
        componentes = ProyectoController.ctrlObtenerComponentesProyecto(idproyecto)
        if componentes:
            for fila in componentes:
                combo_componente.addItem(str(fila[2]), fila[0])
            combo_componente.setCurrentIndex(combo_componente.findData(idcomponente))
        # Botones
        layout.addRow(label_titulo)
        layout.addRow(combo_componente)
        layout.addRow(label_mensaje)
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        # Cambiar los textos a español
        button_box.button(QDialogButtonBox.Save).setText("Guardar")
        button_box.button(QDialogButtonBox.Cancel).setText("Cancelar")
        layout.addWidget(button_box)
        # Conectar los botones a las funciones correspondientes
        def actualizarDatos():
            componente = combo_componente.currentData()
            nombrezona = combo_componente.currentText()
            if str(idcomponente) == str(componente):
                dialog.reject()
            else:
                respuesta = EquipoController.ctrlCambiarComponenteAdicionales(idcomponente, componente)
                if respuesta:
                    dialog.reject()
                    # Eliminar equipos
                    TreeCheckbox.eliminarCheckboxGrupo(treewidget, idcomponente, nombregrupo, tipogrupo)
                    # Crear equipos en nuevo componente
                    TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidget, nombrezona, componente, idproyecto, nombregrupo, tipogrupo, respuesta, subgrupo)
                    reiniciarvistas("Adicional")
                else:
                    label_mensaje.setText("Error al cambiar de componente.")
        button_box.accepted.connect(actualizarDatos)
        button_box.rejected.connect(dialog.reject)
        # Mostrar el diálogo
        dialog.setLayout(layout)
        dialog.exec()
    
    def eliminar_adicionales(idproyecto, idzona, grupo, tipo, treewidget, reiniciarvistas):
        dlg = QMessageBox()
        dlg.setWindowTitle("Eliminar Equipos Adicionales")
        dlg.setText(f"¿Está seguro eliminar todos los Adicionales?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.button(QMessageBox.Yes).setText("Sí")
        dlg.button(QMessageBox.No).setText("No")
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            respuesta = EquipoController.ctrlEliminarAdicionales(idzona)
            if respuesta:
                delete = EquipoController.ctrlEliminarDataAdiconales(idproyecto, respuesta)
                if delete:
                    TreeCheckbox.eliminarCheckboxGrupo(treewidget, idzona, grupo, tipo)
                    reiniciarvistas("Adicional")
                else:
                    mostrar_mensaje("Eliminar Adicionales", "Error al eliminar data Adicionales.", "advertencia")
            else:
                mostrar_mensaje("Eliminar Adicionales", "No se pudo eliminar los Adicionales.", "advertencia")
    
    def actualizarEquipoAdicional(idproyecto, idcomponente, idinstrumento, treewidget, nombregrupo, tipogrupo, subgrupo, reiniciarvistas):
        loaderLoading = QUiLoader()        
        ui_file_path = resource_path("ui/equipogeneral.ui")
        ui_file = loaderLoading.load(ui_file_path, None)
        dialogoEquipoGeneral = QDialog()
        dialogoEquipoGeneral.setWindowTitle("Actualizar Equipo Adicional")
        layout_procesar_data = QVBoxLayout()
        layout_procesar_data.addWidget(ui_file)
        dialogoEquipoGeneral.setLayout(layout_procesar_data)
        #  # Obtener elementos para interactuar
        comboComponente = dialogoEquipoGeneral.findChild(QComboBox, "cb_lista_componentes")
        nombreEquipo = dialogoEquipoGeneral.findChild(QLineEdit, "input_nombre")
        tipoEquipo = dialogoEquipoGeneral.findChild(QLineEdit, "input_tipo")
        norteEquipo = dialogoEquipoGeneral.findChild(QDoubleSpinBox, "input_norte")
        esteEquipo = dialogoEquipoGeneral.findChild(QDoubleSpinBox, "input_este")
        nivelEquipo = dialogoEquipoGeneral.findChild(QDoubleSpinBox, "input_nivel")
        figuraEquipo = dialogoEquipoGeneral.findChild(QComboBox, "combo_figura")
        colorEquipo = dialogoEquipoGeneral.findChild(QPushButton, "btn_color")
        tamanioEquipo = dialogoEquipoGeneral.findChild(QSpinBox, "input_tamanio")
        descripEquipo = dialogoEquipoGeneral.findChild(QTextEdit, "input_descripcion")
        botonguardar = dialogoEquipoGeneral.findChild(QPushButton, "btn_registrar")
        lblrespuesta = dialogoEquipoGeneral.findChild(QLabel, "label_mensaje_estado")
        # cargar combo
        figuraEquipo.addItem("◑ Esfera", "Esfera")
        figuraEquipo.addItem("∎ Cilindro", "Cilindro")
        figuraEquipo.addItem("◮ Cono", "Cono")
        figuraEquipo.addItem("❒ Cubo", "Cubo")
        # cargar data componentes
        componentes = ProyectoController.ctrlObtenerComponentesProyecto(idproyecto)
        if componentes:
            for fila in componentes:
                comboComponente.addItem(str(fila[2]), fila[0])
            comboComponente.setEnabled(True)
        # mostrar data
        nombreactual = ""
        idequipo = 0
        datatdr = EquipoController.ctrlObtenerInfoEquipoAdicional(idinstrumento)
        if datatdr:
            idequipo = datatdr[0]
            comboComponente.setCurrentIndex(comboComponente.findData(idcomponente))
            nombreEquipo.setText(str(datatdr[2]))
            nombreactual = str(datatdr[2])
            tipoEquipo.setText(str(datatdr[3]))
            esteEquipo.setValue(datatdr[4])
            norteEquipo.setValue(datatdr[5])
            nivelEquipo.setValue(datatdr[6])
            figuraEquipo.setCurrentIndex(figuraEquipo.findData(datatdr[7]))
            colorEquipo.setStyleSheet("background-color: %s" % datatdr[8])
            tamanioEquipo.setValue(datatdr[9])
            descripEquipo.setPlainText(str(datatdr[10]))
        def elegirColorEquipo():
            colorcito = QColorDialog.getColor()
            if colorcito.isValid():
                colorEquipo.setStyleSheet("background-color: %s" % colorcito.name())
        def actualizarDatos():
            componente = comboComponente.currentData()
            nombrezona = comboComponente.currentText()
            nombre = nombreEquipo.text()
            tipo = tipoEquipo.text()
            norte = norteEquipo.value()
            este = esteEquipo.value()
            nivel = nivelEquipo.value()
            figura = figuraEquipo.currentData()
            color = colorEquipo.palette().color(QPalette.Button).name()
            tamaño = tamanioEquipo.value()
            descripcion = descripEquipo.toPlainText()
            if nombre:
                datos = [nombre, tipo, este, norte, nivel, figura, color, tamaño, descripcion, idequipo]
                data = [componente, nombre, idinstrumento]
                respuesta = EquipoController.ctrlActualizarEquipoAdicional(datos, data)
                if respuesta:
                    dialogoEquipoGeneral.close()
                    if str(idcomponente) == str(componente):
                        TreeCheckbox.actualizarTextoCheckboxEquipo(treewidget, idcomponente, nombregrupo, subgrupo, nombreactual, nombre)
                    else:
                        # Eliminar equipo
                        TreeCheckbox.eliminarCheckbox(treewidget, nombregrupo, idinstrumento, subgrupo)
                        # Crear adicional en nuevo componente
                        equipo = InterfazController.ctrlListarComponenteEquipoAdicional(idinstrumento)
                        if equipo:
                            TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidget, nombrezona, componente, idproyecto, nombregrupo, tipogrupo, equipo, subgrupo)
                            reiniciarvistas("Adicional")
                else:
                    lblrespuesta.setText("Error al actualizar el equipo adicional.")
                    lblrespuesta.setStyleSheet("color: red;")
            else:
                lblrespuesta.setText("Algunos campos están vacíos.")
                lblrespuesta.setStyleSheet("color: red;")
        # # Inicializar botones
        colorEquipo.clicked.connect(elegirColorEquipo)
        botonguardar.clicked.connect(actualizarDatos)
        dialogoEquipoGeneral.exec()
    
    def eliminar_adicional(idproyecto, idinstrumento, nombreequipo, nombregrupo, tipolista, treewidget, reiniciarvistas):
        dlg = QMessageBox()
        dlg.setWindowTitle("Eliminar Equipo Adicional")
        dlg.setText(f"¿Está seguro eliminar el equipo adicional '{nombreequipo}'?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.button(QMessageBox.Yes).setText("Sí")
        dlg.button(QMessageBox.No).setText("No")
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            respuesta = EquipoController.ctrlEliminarEquipoAdicional(idinstrumento)
            if respuesta:
                delete = EquipoController.ctrlEliminarEquipoAdicionalData(respuesta)
                if delete:
                    TreeCheckbox.eliminarCheckbox(treewidget, nombregrupo, idinstrumento, tipolista)
                    reiniciarvistas("Adicional")
                else:
                    mostrar_mensaje("Eliminar Adicional", "Error al eliminar data del equipo adicional.", "advertencia")
            else:
                mostrar_mensaje("Eliminar Adicional", "No se pudo eliminar el equipo adicional.", "advertencia")
    
    def cambiar_componente_bloque_equipo(idproyecto, idcomponente, parent, treewidget, nombregrupo, tipogrupo, subgrupo, reiniciarvistas):
        dialog = QDialog()
        dialog.setWindowTitle("Mover Equipo Componente")
        layout = QFormLayout(dialog)
        # Campo componente
        label_titulo = QLabel("Componente:")
        combo_componente = QComboBox()
        label_mensaje = QLabel("")
        label_mensaje.setAlignment(Qt.AlignCenter)
        label_mensaje.setStyleSheet("QLabel { color: red; }")
        # cargar data componentes
        componentes = ProyectoController.ctrlObtenerComponentesProyecto(idproyecto)
        if componentes:
            for fila in componentes:
                combo_componente.addItem(str(fila[2]), fila[0])
            combo_componente.setCurrentIndex(combo_componente.findData(idcomponente))
        # Botones
        layout.addRow(label_titulo)
        layout.addRow(combo_componente)
        layout.addRow(label_mensaje)
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        # Cambiar los textos a español
        button_box.button(QDialogButtonBox.Save).setText("Guardar")
        button_box.button(QDialogButtonBox.Cancel).setText("Cancelar")
        layout.addWidget(button_box)
        # Conectar los botones a las funciones correspondientes
        def actualizarDatos():
            componente = combo_componente.currentData()
            nombrezona = combo_componente.currentText()
            if str(idcomponente) == str(componente):
                dialog.reject()
            else:
                result = False
                hijos_marcados = []
                for i in range(parent.childCount()):
                    hijo = parent.child(i)
                    if hijo is not None and hijo.checkState(0) == Qt.Checked:
                        idinstrumento = hijo.text(2)
                        respuesta = EquipoController.ctrlCambiarEquipoComponente(idinstrumento, componente)
                        if respuesta:
                            hijos_marcados.append(hijo)
                            result = True
                if result:
                    dialog.reject()
                    for hijo in hijos_marcados:
                        idinstrumento = hijo.text(2)
                        TreeCheckbox.eliminarCheckbox(treewidget, nombregrupo, idinstrumento, subgrupo)
                        # Crear prisma en nuevo componente
                        adicional = InterfazController.ctrlListarComponenteEquipoAdicional(idinstrumento)
                        if adicional:
                            TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidget, nombrezona, componente, idproyecto, nombregrupo, tipogrupo, adicional, subgrupo)
                    reiniciarvistas("Equipos Adicionales")
                    # Limpiar tabla
                    from views.datos_view import DatosView
                    from modules.datos.vistaDatos import VistaDatos
                    tabla =  DatosView.main.findChild(QTableView, "table_datos")
                    VistaDatos.limpiarTablaDatos(tabla)
                else:
                    label_mensaje.setText("Error al cambiar de componente.")
        button_box.accepted.connect(actualizarDatos)
        button_box.rejected.connect(dialog.reject)
        # Mostrar el diálogo
        dialog.setLayout(layout)
        dialog.exec()
    
    def mostrarCalculadora():
        dialog = QDialog()
        dialog.setWindowTitle("Generar fórmula")
        # Layout principal
        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(5, 5, 5, 5)  # Ajustar márgenes al mínimo
        main_layout.setSpacing(0)  # Eliminar espaciado entre elementos
        
        # Área para mostrar la ecuación
        equation_display = QLineEdit()
        equation_display.setReadOnly(True)
        equation_display.setPlaceholderText("Forma tu ecuación aquí...")
        main_layout.addWidget(equation_display)

        # Label para mostrar la ecuación confirmada
        confirmed_equation_label = QLabel("Genere la fórmula lineal o polinómica")
        confirmed_equation_label.setAlignment(Qt.AlignCenter)
        confirmed_equation_label.setFont(QFont("Arial", 10))  # Ajustar el tamaño de la fuente
        confirmed_equation_label.setFixedHeight(20)  # Ajustar la altura del label
        main_layout.addWidget(confirmed_equation_label)

        # Layout para los botones de la calculadora
        calculator_layout = QGridLayout()
        calculator_layout.setSpacing(2)  # Ajustar espaciado entre botones
        calculator_layout.setContentsMargins(0, 0, 0, 0)  # Eliminar márgenes internos
        # mensaje de alertas
        message_label = QLabel("")
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setFixedHeight(20)
        # MÉTODOS
        def verificar_ultimo_digito(texto):
            if not texto:  # Verifica si la cadena está vacía
                return False
            return texto[-1].isdigit()
        
        def verificar_ultimo_punto(texto):
            return bool(texto and texto[-1] == ".")
        
        def validar_numero_decimal(formula):
            if not formula:
                return False
            ultimo_numero = formula.split()[-1] if formula.split() else ""
            if verificar_ultimo_digito(ultimo_numero.rstrip()):
                decimal = '.' in ultimo_numero
            else:
                decimal = False
            return decimal
        
        def add_component(component):
            current_text = equation_display.text()
            if component.isdigit():
                if verificar_ultimo_digito(current_text.rstrip()):
                    new_text = f"{current_text}{component}"
                else:
                    if current_text == "" or verificar_ultimo_punto(current_text.rstrip()):
                        new_text = f"{current_text}{component}"
                    else:
                        new_text = current_text + " " + component
            elif component == ".":
                if verificar_ultimo_digito(current_text.rstrip()):
                    if validar_numero_decimal(current_text.rstrip()):
                        new_text = current_text
                    else:
                        new_text = f"{current_text}{component}"
                else:
                    if current_text == "":
                        new_text = f"0{component}"
                    else:
                        new_text = current_text
            else:
                if current_text == "":
                    new_text = f"{current_text}{component}"
                else:
                    new_text = current_text + " " + component
            equation_display.setText(new_text)
            message_label.setText("")

        def delete_last_component():
            current_text = equation_display.text()
            message_label.setText("")
            if current_text:
                components = current_text.split()
                components.pop()
                new_text = " ".join(components)
                equation_display.setText(new_text)

        def confirm_equation():
            equation = equation_display.text()
            respuesta = RegistroEquipos.validar_formula(equation)
            if respuesta:
                validar = PiezometroController.ctrlValidarExisteFormula(equation)
                if validar:
                    sentencia = RegistroEquipos.convertir_formula_sentencia(equation)
                    resultado = PiezometroController.ctrlRegistrarNuevaFormula(equation, sentencia)
                    if resultado:
                        clear_equation()
                        message_label.setText("La fórmula se guardó correctamente.")
                        message_label.setStyleSheet("color: green;")
                    else:
                        message_label.setText("No se pudo guardar la fórmula.")
                        message_label.setStyleSheet("color: orange;")
                else:
                    message_label.setText("Ya existe la fórmula.")
                    message_label.setStyleSheet("color: orange;")
            else:
                message_label.setText("La fórmula es incorrecta.")
                message_label.setStyleSheet("color: red;")

        def clear_equation():
            equation_display.clear()
            message_label.setText("")
        # Botones de funciones y números
        function_buttons = [
            ['Rad', 'Deg', 'x!', '(', ')', '←'],
            ['Inv', 'sin', 'ln', '7', '8', '9', '/'],
            ['π', 'cos', 'log', '4', '5', '6', '*'],
            ['e', 'tan', '√', '1', '2', '3', '-'],
            ['Ans', 'EXP', 'x^y', '0', '.', 'CLR', '+']
        ]
        tooltips = {
            'Rad': 'Radianes',
            'Deg': 'Grados',
            'x!': 'Factorial',
            '←': 'Borrar',
            'Inv': 'Inverso',
            'sin': 'Seno',
            'ln': 'Logaritmo Natural',
            'cos': 'Coseno',
            'log': 'Logaritmo Base 10',
            'tan': 'Tangente',
            '√': 'Raíz Cuadrada',
            'π': 'Pi (3.14159...)',
            'e': 'Número de Euler (2.718...)',
            'Ans': 'Respuesta Anterior',
            'EXP': 'Notación Científica',
            'x^y': 'Potencia',
            'CLR': 'Limpiar'
        }
        permitidos = ['(', ')', '←', '0', '7', '8', '9', '/', '4', '5', '6', '*', '1', '2', '3', '-', '.', 'CLR', '+']
        for i, row in enumerate(function_buttons):
            for j, text in enumerate(row):
                button = QPushButton(text)
                if text in tooltips:
                    button.setToolTip(tooltips[text])
                if text not in permitidos:
                    button.setEnabled(False)
                if text == 'CLR':
                    button.clicked.connect(clear_equation)
                elif text == '←':
                    button.clicked.connect(delete_last_component)
                else:
                    button.clicked.connect(lambda *args, t=text: add_component(t))
                calculator_layout.addWidget(button, i, j)
        main_layout.addLayout(calculator_layout)

        # Layout para los botones dinámicos
        dynamic_layout = QGridLayout()
        dynamic_layout.setSpacing(5)  # Ajustar espaciado entre botones dinámicos
        dynamic_layout.setContentsMargins(0, 0, 0, 0)  # Eliminar márgenes internos
        dynamic_buttons = ['Frecuencia', 'Temperatura', 'Presion', 'FI', 'TI', 'PI', 'CF', 'TK', 'A', 'B', 'C']
        tooltipsdynamic = {
            'Frecuencia': 'Frecuencia Actual',
            'Temperatura': 'Temperatura Actual',
            'Presion': 'Presión Actual',
            'FI': 'Frecuencia Inicial',
            'TI': 'Temperatura Inicial',
            'PI': 'Presión Inicial',
            'CF': 'Factor de Calibración',
            'TK': 'Corrección de Temperatura',
            'A': 'Constante A',
            'B': 'Constante B',
            'C': 'Constante C'
        }
        for i, text in enumerate(dynamic_buttons):
            button = QPushButton(text)
            if text in tooltipsdynamic:
                button.setToolTip(tooltipsdynamic[text])
            button.clicked.connect(lambda *args, t=text: add_component(t))
            fila = i // 5       # Nueva fila cada 5 botones
            columna = i % 5     # Columna va de 0 a 4
            dynamic_layout.addWidget(button, fila, columna)
        main_layout.addLayout(dynamic_layout)
        main_layout.addWidget(message_label)
        # Botón de confirmar
        confirm_button = QPushButton("Confirmar")
        confirm_button.clicked.connect(confirm_equation)
        main_layout.addWidget(confirm_button)
        dialog.setLayout(main_layout)
        dialog.exec()
    
    def validar_formula(formula: str) -> bool:
        funciones = ['sin', 'cos', 'tan', 'ln', 'log', '√', 'EXP', 'x!', 'Rad', 'Deg', 'Inv', 'Ans', 'x^y']
        constantes = ['π', 'e']
        variables = ['Frecuencia', 'Temperatura', 'Presion', 'FI', 'TI', 'PI', 'CF', 'TK', 'A', 'B', 'C']
        operadores = ['+', '-', '*', '/']
        parentesis = ['(', ')']
        numero_regex = re.compile(r'^\d+(\.\d+)?$')
        tokens = formula.strip().split()
        if not tokens:
            return False
        # 1. Validar paréntesis balanceados
        stack = []
        for token in tokens:
            if token == '(':
                stack.append(token)
            elif token == ')':
                if not stack:
                    return False
                stack.pop()
        if stack:
            return False
        # 2. Validar que no existan paréntesis vacíos
        for i in range(len(tokens) - 1):
            if tokens[i] == '(' and tokens[i + 1] == ')':
                return False
        # 2. Validar tokens y su relación con vecinos
        def es_operando(t):
            return (
                t in funciones or
                t in constantes or
                t in variables or
                numero_regex.fullmatch(t)
            )
        for i, token in enumerate(tokens):
            # Token inválido
            if not (es_operando(token) or token in operadores or token in parentesis):
                return False
            # Validar que no haya operandos consecutivos sin operador entre ellos
            if i > 0:
                prev = tokens[i - 1]
                if es_operando(prev) and es_operando(token):
                    return False
            # Evitar que operadores estén al inicio o final
            if i == 0 and token in operadores:
                return False
            if i == len(tokens) - 1 and token in operadores:
                return False
            # Evitar operadores seguidos
            if i > 0 and token in operadores and tokens[i - 1] in operadores:
                return False
        return True
    
    def convertir_formula_sentencia(formula):
        reemplazos = {
            'Frecuencia': 'd.frecuencia_cuerda',
            'Temperatura': 'd.temperatura_cuerda',
            'Presion': 'd.presion_barometrica',
            'FI': 'p.frecuencia_inicial',
            'TI': 'p.temperatura_inicial',
            'PI': 'p.presion_inicial',
            'CF': 'p.factor_calibracion',
            'TK': 'p.temperatura_correccion',
            'A': 'p.constante_a',
            'B': 'p.constante_b',
            'C': 'p.constante_c'
        }
        formula_sql = formula
        for clave, valor in reemplazos.items():
            formula_sql = re.sub(r'\b' + re.escape(clave) + r'\b', valor, formula_sql)
        return formula_sql
    