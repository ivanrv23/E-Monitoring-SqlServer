from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                                QLineEdit, QCheckBox, QPushButton, QDateTimeEdit,
                                QColorDialog)
from PySide6.QtCore import QDateTime
from PySide6.QtGui import QColor
from datetime import datetime


class EventosDialog(QDialog):
    def __init__(self, parent, fecha, idproyecto, tipo_inst, equipo_id=None, equipo_nombre=None):
        super().__init__(parent)
        self.setWindowTitle("Agregar Evento")
        self.setMinimumWidth(380)
        self.color_seleccionado = "#ff0000"
        self.equipo_id = equipo_id
        self.equipo_nombre = equipo_nombre
        
        layout = QVBoxLayout(self)
        
        if equipo_nombre:
            lbl_equipo = QLabel(f"Equipo detectado: {equipo_nombre}")
            lbl_equipo.setStyleSheet(
                "font-size: 12px; font-weight: bold; color: #0056b3; "
                "padding: 5px; background: #e7f1ff; border-radius: 3px;"
            )
        else:
            lbl_equipo = QLabel("Evento general (todos los equipos)")
            lbl_equipo.setStyleSheet(
                "font-size: 12px; font-weight: bold; color: #856404; "
                "padding: 5px; background: #fff3cd; border-radius: 3px;"
            )
        layout.addWidget(lbl_equipo)
        
        self.chk_global = QCheckBox("Aplicar a todos los equipos")
        self.chk_global.setChecked(equipo_id is None)
        if equipo_id is None:
            self.chk_global.setEnabled(False)
        layout.addWidget(self.chk_global)
        
        layout.addSpacing(5)
        
        layout.addWidget(QLabel("Fecha:"))
        self.dt_fecha = QDateTimeEdit()
        self.dt_fecha.setDateTime(QDateTime(
            fecha.year, fecha.month, fecha.day,
            fecha.hour, fecha.minute, fecha.second
        ))
        self.dt_fecha.setDisplayFormat("dd/MM/yyyy HH:mm:ss")
        self.dt_fecha.setCalendarPopup(True)
        layout.addWidget(self.dt_fecha)
        
        layout.addWidget(QLabel("Descripción:"))
        self.txt_descripcion = QLineEdit()
        self.txt_descripcion.setPlaceholderText("Ej: Inicio de excavación")
        self.txt_descripcion.setMaxLength(100)
        layout.addWidget(self.txt_descripcion)
        
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Color:"))
        self.lbl_color = QLabel()
        self.lbl_color.setFixedSize(40, 25)
        self.lbl_color.setStyleSheet(
            f"background-color: {self.color_seleccionado}; "
            f"border: 1px solid #999; border-radius: 3px;"
        )
        color_layout.addWidget(self.lbl_color)
        self.btn_color = QPushButton("Cambiar")
        self.btn_color.setFixedWidth(80)
        self.btn_color.clicked.connect(self._seleccionar_color)
        color_layout.addWidget(self.btn_color)
        color_layout.addStretch()
        layout.addLayout(color_layout)
        
        layout.addSpacing(10)
        
        btn_layout = QHBoxLayout()
        btn_guardar = QPushButton("Guardar")
        btn_guardar.setStyleSheet(
            "QPushButton { background-color: #28a745; color: white; "
            "padding: 6px 20px; border-radius: 3px; font-weight: bold; }"
        )
        btn_guardar.clicked.connect(self._validar_y_aceptar)
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet("QPushButton { padding: 6px 20px; }")
        btn_cancelar.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_guardar)
        btn_layout.addWidget(btn_cancelar)
        layout.addLayout(btn_layout)
    
    def _seleccionar_color(self):
        color = QColorDialog.getColor(QColor(self.color_seleccionado), self)
        if color.isValid():
            self.color_seleccionado = color.name()
            self.lbl_color.setStyleSheet(
                f"background-color: {self.color_seleccionado}; "
                f"border: 1px solid #999; border-radius: 3px;"
            )
    
    def _validar_y_aceptar(self):
        if self.txt_descripcion.text().strip():
            self.accept()
    
    def obtener_datos(self):
        dt = self.dt_fecha.dateTime()
        fecha = datetime(
            dt.date().year(), dt.date().month(), dt.date().day(),
            dt.time().hour(), dt.time().minute(), dt.time().second()
        )
        
        if self.chk_global.isChecked() or self.equipo_id is None:
            alcance = "GLOBAL"
            id_inst = "ALL"
        else:
            alcance = "ESPECIFICO"
            id_inst = str(self.equipo_id)
        
        return {
            'fecha': fecha,
            'descripcion': self.txt_descripcion.text().strip(),
            'color': self.color_seleccionado,
            'alcance': alcance,
            'id_instrumento': id_inst
        }