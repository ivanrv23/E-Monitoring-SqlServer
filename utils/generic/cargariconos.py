import os
from utils.common.rutasarchivos import resource_path
from PySide6.QtGui import QIcon

def cargarIcono(boton, ruta_icono):
    svg_icon_path = resource_path(ruta_icono)
    if not os.path.exists(svg_icon_path):
        raise FileNotFoundError(f"El ícono no se encuentra en la ruta: {svg_icon_path}")
    icon = QIcon(svg_icon_path)
    boton.setIcon(icon)