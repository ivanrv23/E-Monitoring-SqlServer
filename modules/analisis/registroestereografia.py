from PySide6.QtWidgets import (QDialog, QVBoxLayout, QPushButton, QLineEdit, QDoubleSpinBox)
from PySide6.QtUiTools import QUiLoader
from utils.common.rutasarchivos import resource_path
from utils.generic.cargariconos import cargarIcono
from utils.common.alertas import mostrar_mensaje
from controllers.AnalisisController import AnalisisController
from utils.generic.listaiconos import ListaIconos

class RegistroEstereografia():
    estado = False
    
    def modalRegistroEstereografia(idproyecto):
        RegistroEstereografia.estado = False
        loaderLoading = QUiLoader()        
        ui_file_path = resource_path("ui/estereografiataludes.ui")
        ui_file = loaderLoading.load(ui_file_path, None)
        dialogo = QDialog()
        dialogo.setWindowTitle("Registro de Taludes")
        layout = QVBoxLayout()
        layout.addWidget(ui_file)
        dialogo.setLayout(layout)
        # Botones eliminar talud estereografia
        botonBorrarTalud1 = dialogo.findChild(QPushButton, "btn1_limpiar")
        cargarIcono(botonBorrarTalud1, ListaIconos.ICONOS["basura"])
        botonBorrarTalud2 = dialogo.findChild(QPushButton, "btn2_limpiar")
        cargarIcono(botonBorrarTalud2, ListaIconos.ICONOS["basura"])
        botonBorrarTalud3 = dialogo.findChild(QPushButton, "btn3_limpiar")
        cargarIcono(botonBorrarTalud3, ListaIconos.ICONOS["basura"])
        botonBorrarTalud4 = dialogo.findChild(QPushButton, "btn4_limpiar")
        cargarIcono(botonBorrarTalud4, ListaIconos.ICONOS["basura"])
        botonBorrarTalud5 = dialogo.findChild(QPushButton, "btn5_limpiar")
        cargarIcono(botonBorrarTalud5, ListaIconos.ICONOS["basura"])
        botonAceptarE = dialogo.findChild(QPushButton, "btn_aceptar")
        botonCancelarE = dialogo.findChild(QPushButton, "btn_cancelar")
        # Cargar info
        dataEstereografia = AnalisisController.ctrObtenerDataEstereografia(idproyecto)
        if dataEstereografia:
            nombres_inputs = ["input_nombre1", "input_nombre2", "input_nombre3", "input_nombre4", "input_nombre5"]
            inclinaciones_inputs = ["input_inclinacion1", "input_inclinacion2", "input_inclinacion3", "input_inclinacion4", "input_inclinacion5"]
            direcciones_inputs = ["input_direccion1", "input_direccion2", "input_direccion3", "input_direccion4", "input_direccion5"]
            # Llenar la lista con varios conjuntos de datos utilizando un bucle
            for fila in dataEstereografia:
                i = fila[5] - 1
                input_nombre = dialogo.findChild(QLineEdit, nombres_inputs[i])
                input_incli = dialogo.findChild(QDoubleSpinBox, inclinaciones_inputs[i])
                input_direc = dialogo.findChild(QDoubleSpinBox, direcciones_inputs[i])
                input_nombre.setText(fila[2])
                input_incli.setValue(float(fila[3]))
                input_direc.setValue(float(fila[4]))    
        def eliminarDatoEstereografia(numero):
            respu = AnalisisController.ctrlEliminaeDatoEstereografia(idproyecto, numero)
            nombre_input = dialogo.findChild(QLineEdit, f"input_nombre{numero}")
            inclinacion_input = dialogo.findChild(QDoubleSpinBox, f"input_inclinacion{numero}")
            direccion_input = dialogo.findChild(QDoubleSpinBox, f"input_direccion{numero}")
            if respu:
                RegistroEstereografia.estado = True
                nombre_input.setText("")
                inclinacion_input.setValue(0)
                direccion_input.setValue(0)
        def agregarDatoEstereografia():
            # Declarar una lista vacía para almacenar los datos
            datos = []
            # Definir una lista de nombres de los inputs
            nombres_inputs = ["input_nombre1", "input_nombre2", "input_nombre3", "input_nombre4", "input_nombre5"]
            inclinaciones_inputs = ["input_inclinacion1", "input_inclinacion2", "input_inclinacion3", "input_inclinacion4", "input_inclinacion5"]
            direcciones_inputs = ["input_direccion1", "input_direccion2", "input_direccion3", "input_direccion4", "input_direccion5"]
            botones = [1, 2, 3, 4, 5]
            # Llenar la lista con varios conjuntos de datos utilizando un bucle
            for nombre, inclinacion, direccion, numero in zip(nombres_inputs, inclinaciones_inputs, direcciones_inputs, botones):
                input_nombre = dialogo.findChild(QLineEdit, nombre)
                input_inclinacion = dialogo.findChild(QDoubleSpinBox, inclinacion)
                input_direccion = dialogo.findChild(QDoubleSpinBox, direccion)
                # agregar los datos
                if input_nombre.text().strip():
                    datos.append({
                        "nombre": input_nombre.text(),
                        "inclinacion": input_inclinacion.value(),
                        "direccion": input_direccion.value(),
                        "numero": numero
                    })
            if datos:
                respu = AnalisisController.ctrlGuardarDatosEstereografia(idproyecto, datos)
                if respu:
                    RegistroEstereografia.estado = True
                    dialogo.close()
                else:
                    mostrar_mensaje("Error al Guardar", "No se pudo guardar los datos.", "advertencia")
            else:
                dialogo.close()
        def cancelarAgregarDatoEstereografia():
            dialogo.close()
        botonBorrarTalud1.clicked.connect(lambda: eliminarDatoEstereografia(1))
        botonBorrarTalud2.clicked.connect(lambda: eliminarDatoEstereografia(2))
        botonBorrarTalud3.clicked.connect(lambda: eliminarDatoEstereografia(3))
        botonBorrarTalud4.clicked.connect(lambda: eliminarDatoEstereografia(4))
        botonBorrarTalud5.clicked.connect(lambda: eliminarDatoEstereografia(5))
        botonAceptarE.clicked.connect(agregarDatoEstereografia)
        botonCancelarE.clicked.connect(cancelarAgregarDatoEstereografia)
        dialogo.exec()
        return RegistroEstereografia.estado
    