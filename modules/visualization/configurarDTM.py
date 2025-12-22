import copy
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QWidget, QColorDialog, QPushButton)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QSize
from utils.common.rutasarchivos import resource_path

class ConfigurarDTM:
    estadorender = False
    elementosRenderizado, estadosRenderizadoDXF = [], []

    @staticmethod
    def dialogConfiguracion(topomarcados, cambioproyecto):
        ConfigurarDTM.estadorender = False
        if cambioproyecto:
            ConfigurarDTM.elementosRenderizado.clear()
            ConfigurarDTM.estadosRenderizadoDXF.clear()
        if topomarcados:
            for componente, topografias in topomarcados:
                nombrecomponente, idcomponente, idproy = componente
                for topo, elementos in topografias.items():
                    nombretopo, idinstru, idtopo = topo
                    for nombreactor, idtactor, rutaactor in elementos:
                        if not any(idcomponente == elemento[0] and idtopo == elemento[1] and rutaactor == elemento[5] for elemento in ConfigurarDTM.elementosRenderizado):
                            ConfigurarDTM.elementosRenderizado.append((idcomponente, idtopo, 0, "#f2e5b2", nombretopo, rutaactor))
            # sacar topos únicas
            toposunicas = []
            encontrados = set()
            for item in ConfigurarDTM.elementosRenderizado:
                clave = (item[0], item[1])
                if clave not in encontrados:
                    toposunicas.append(item)
                    encontrados.add(clave)
            # Iniciar dialogo
            dialogo = QDialog()
            dialogo.setWindowTitle("Configuración DTM")
            loader = QUiLoader()
            ui_file_path = resource_path("ui/configuracionDTM.ui")
            loader.load(ui_file_path, dialogo)
            # elementos
            frameElementos = dialogo.findChild(QWidget, "scrollAreaWidgetContents")
            btn_confirmar = dialogo.findChild(QPushButton, "btn_confirmar")
            frame_layout = frameElementos.layout()
            if frame_layout is None:
                frame_layout = QVBoxLayout()
                frame_layout.setAlignment(Qt.AlignTop)
                frameElementos.setLayout(frame_layout)
            for codcompon, codtopo, estado, colorsoli, nombre, ruta in toposunicas:
                fila_widget = QWidget()
                fila_widget.setObjectName(f"widget_{codcompon}_{codtopo}")
                fila_layout = QHBoxLayout(fila_widget)
                etiqueta_nombre = QLabel(nombre)
                nombrebtn=f'boton_{codcompon}_{codtopo}'
                nombreDinamico = QPushButton()
                nombreDinamico.setObjectName(nombrebtn)
                nombreDinamico.setFixedSize(QSize(40, 28))
                if estado == 0:
                    activo_icon_path = resource_path("resources/iconos/fontawesome/regular/lightbulb.svg")
                else:
                    activo_icon_path = resource_path("resources/iconos/fontawesome/solid/lightbulb.svg")
                nombreDinamico.setIcon(QIcon(activo_icon_path))
                #nombreDinamico.setIconSize(QSize(20, 20))
                nombreDinamico.setStyleSheet("border: none;")
                nombreDinamico.clicked.connect(lambda _, id=f"{codcompon}_{codtopo}", nombreBoton=nombreDinamico: ConfigurarDTM.cambiarEstadoDTM(id, nombreBoton))
                fila_layout.addWidget(nombreDinamico)
                # agregar el boton para el color del sólido
                nombrecolorbtn = f'botoncolor_{codcompon}_{codtopo}'
                nombrecolorDinamico = QPushButton()
                nombrecolorDinamico.setObjectName(nombrecolorbtn)
                nombrecolorDinamico.setFixedSize(QSize(40, 28))
                nombrecolorDinamico.setStyleSheet("background-color: %s" % colorsoli)
                nombrecolorDinamico.clicked.connect(lambda _, idc=f"{codcompon}_{codtopo}", nombreBtnColor=nombrecolorDinamico: ConfigurarDTM.cambiarColorSolido(idc, nombreBtnColor))
                fila_layout.addWidget(nombrecolorDinamico)
                fila_layout.addWidget(etiqueta_nombre)
                fila_layout.setContentsMargins(5, 0, 5, 0)
                frame_layout.addWidget(fila_widget)
            ConfigurarDTM.estadosRenderizadoDXF = copy.deepcopy(ConfigurarDTM.elementosRenderizado)
            # conectar boton
            btn_confirmar.clicked.connect(lambda: ConfigurarDTM.confirmarConfiguracion(dialogo))
            dialogo.exec()
        return ConfigurarDTM.estadorender, ConfigurarDTM.elementosRenderizado
    
    @staticmethod
    def cambiarEstadoDTM(id_elemento, nombreBoton):  
        for i, elemento in enumerate(ConfigurarDTM.estadosRenderizadoDXF):
            if f"{elemento[0]}_{elemento[1]}" == id_elemento:
                nuevo_estado = 1 if elemento[2] == 0 else 0
                ConfigurarDTM.estadosRenderizadoDXF[i] = (elemento[0], elemento[1], nuevo_estado, elemento[3], elemento[4], elemento[5])
                activo_icon_path = resource_path("resources/iconos/fontawesome/solid/lightbulb.svg")
                inactivo_icon_path = resource_path("resources/iconos/fontawesome/regular/lightbulb.svg")
                icono_path = activo_icon_path if nuevo_estado == 1 else inactivo_icon_path
                nombreBoton.setIcon(QIcon(icono_path))
    
    @staticmethod
    def cambiarColorSolido(id_elemento, nombreBoton):
        for i, elemento in enumerate(ConfigurarDTM.estadosRenderizadoDXF):
            if f"{elemento[0]}_{elemento[1]}" == id_elemento:
                colorcito = QColorDialog.getColor()
                if colorcito.isValid():
                    nombreBoton.setStyleSheet("background-color: %s" % colorcito.name())
                    colorsolidonuevo = colorcito.name()
                    ConfigurarDTM.estadosRenderizadoDXF[i] = (elemento[0], elemento[1], elemento[2], colorsolidonuevo, elemento[4], elemento[5])
    
    def confirmarConfiguracion(dialogo):
        ConfigurarDTM.elementosRenderizado = copy.deepcopy(ConfigurarDTM.estadosRenderizadoDXF)
        ConfigurarDTM.estadorender = True
        dialogo.close()
        
    def limpiarElementosDTM():
        ConfigurarDTM.elementosRenderizado.clear()
        ConfigurarDTM.estadosRenderizadoDXF.clear()
    