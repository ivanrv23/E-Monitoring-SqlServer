import sys

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
)
from PySide6.QtGui import QFont
import qtawesome as qta


class IconTest(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Prueba de QtAwesome")
        self.setMinimumSize(700, 500)

        self.crear_interfaz()

    def crear_interfaz(self):

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(30, 30, 30, 30)
        layout_principal.setSpacing(20)

        # --------------------------------------------------
        # TÍTULO
        # --------------------------------------------------

        titulo = QLabel("Biblioteca de íconos - QtAwesome")
        titulo.setFont(QFont("Segoe UI", 20, QFont.Bold))

        subtitulo = QLabel(
            "Prueba de diferentes íconos utilizando Material Design Icons"
        )

        layout_principal.addWidget(titulo)
        layout_principal.addWidget(subtitulo)

        # --------------------------------------------------
        # SEPARADOR
        # --------------------------------------------------

        linea = QFrame()
        linea.setFrameShape(QFrame.HLine)
        linea.setFrameShadow(QFrame.Sunken)

        layout_principal.addWidget(linea)

        # --------------------------------------------------
        # BOTONES PRINCIPALES
        # --------------------------------------------------

        fila1 = QHBoxLayout()
        fila1.setSpacing(10)

        btn_agregar = QPushButton("Agregar")
        btn_agregar.setIcon(qta.icon("fa6s.eye"))
        btn_agregar.setObjectName("btnAgregar")

        btn_editar = QPushButton("Editar")
        btn_editar.setIcon(qta.icon("mdi6.pencil"))
        btn_editar.setObjectName("btnEditar")

        btn_eliminar = QPushButton("Eliminar")
        btn_eliminar.setIcon(qta.icon("ei.broom"))
        btn_eliminar.setObjectName("btnEliminar")

        btn_buscar = QPushButton("Buscar")
        btn_buscar.setIcon(qta.icon("mdi6.magnify"))
        btn_buscar.setObjectName("btnBuscar")

        fila1.addWidget(btn_agregar)
        fila1.addWidget(btn_editar)
        fila1.addWidget(btn_eliminar)
        fila1.addWidget(btn_buscar)

        layout_principal.addLayout(fila1)

        # --------------------------------------------------
        # BOTONES DE SISTEMA
        # --------------------------------------------------

        fila2 = QHBoxLayout()
        fila2.setSpacing(10)

        btn_guardar = QPushButton("Guardar")
        btn_guardar.setIcon(qta.icon("mdi6.content-save"))

        btn_config = QPushButton("Configuración")
        btn_config.setIcon(qta.icon("mdi6.cog"))

        btn_usuario = QPushButton("Usuario")
        btn_usuario.setIcon(qta.icon("mdi6.account"))

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setIcon(qta.icon("mdi6.close"))

        fila2.addWidget(btn_guardar)
        fila2.addWidget(btn_config)
        fila2.addWidget(btn_usuario)
        fila2.addWidget(btn_cerrar)

        layout_principal.addLayout(fila2)

        # --------------------------------------------------
        # BOTONES DE MONITOREO
        # --------------------------------------------------

        fila3 = QHBoxLayout()
        fila3.setSpacing(10)

        btn_grafico = QPushButton("Gráficos")
        btn_grafico.setIcon(qta.icon("mdi6.chart-line"))

        btn_datos = QPushButton("Datos")
        btn_datos.setIcon(qta.icon("mdi6.database"))

        btn_alerta = QPushButton("Alertas")
        btn_alerta.setIcon(qta.icon("mdi6.alert"))

        btn_descargar = QPushButton("Descargar")
        btn_descargar.setIcon(qta.icon("mdi6.download"))

        fila3.addWidget(btn_grafico)
        fila3.addWidget(btn_datos)
        fila3.addWidget(btn_alerta)
        fila3.addWidget(btn_descargar)

        layout_principal.addLayout(fila3)

        # --------------------------------------------------
        # BOTONES SOLO ÍCONO
        # --------------------------------------------------

        label = QLabel("Botones solamente con ícono")
        label.setFont(QFont("Segoe UI", 12, QFont.Bold))

        layout_principal.addWidget(label)

        fila4 = QHBoxLayout()
        fila4.setSpacing(10)

        iconos = [
            ("mdi6.plus", "Agregar"),
            ("mdi6.pencil", "Editar"),
            ("mdi6.delete", "Eliminar"),
            ("mdi6.magnify", "Buscar"),
            ("mdi6.refresh", "Actualizar"),
            ("mdi6.cog", "Configuración"),
            ("mdi6.download", "Descargar"),
            ("mdi6.close", "Cerrar"),
        ]

        for nombre_icono, tooltip in iconos:

            boton = QPushButton()
            boton.setIcon(qta.icon(nombre_icono))
            boton.setToolTip(tooltip)
            boton.setFixedSize(45, 45)

            fila4.addWidget(boton)

        layout_principal.addLayout(fila4)

        layout_principal.addStretch()

        # --------------------------------------------------
        # ESTILOS
        # --------------------------------------------------

        self.setStyleSheet("""
            QWidget {
                background-color: #f5f6f8;
                color: #263238;
                font-family: "Segoe UI";
                font-size: 14px;
            }

            QPushButton {
                background-color: white;
                border: 1px solid #d5d9de;
                border-radius: 6px;
                padding: 9px 15px;
                min-height: 20px;
            }

            QPushButton:hover {
                background-color: #eef3f8;
                border-color: #9aa7b2;
            }

            QPushButton:pressed {
                background-color: #dde5ec;
            }

            QLabel {
                background: transparent;
            }
        """)


if __name__ == "__main__":

    app = QApplication(sys.argv)

    ventana = IconTest()
    ventana.show()

    sys.exit(app.exec())