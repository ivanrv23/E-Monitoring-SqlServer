import importlib.resources
from PySide6.QtWidgets import QMessageBox
from PySide6.QtGui import QIcon

def mostrar_mensaje(titulo, mensaje, tipo):
    # Mapeo de las cadenas en español a los tipos de QMessageBox
    tipos_mensajes = {
        "error": QMessageBox.Critical,
        "advertencia": QMessageBox.Warning,
        "informacion": QMessageBox.Information,
        "pregunta": QMessageBox.Question
    }
    # Obtener el tipo correspondiente de QMessageBox según el valor pasado
    tipo_icono = tipos_mensajes.get(tipo.lower(), QMessageBox.Information)
    # Crear el cuadro de mensaje
    msg_box = QMessageBox()
    msg_box.setWindowTitle(titulo)
    msg_box.setText(mensaje)
    # Acceder a la ruta del icono desde el paquete de recursos
    try:
        # 'resources' es el nombre del paquete donde está tu logo.png
        with importlib.resources.path('resources', 'logo.png') as icon_path:
            icon = QIcon(str(icon_path))
            msg_box.setWindowIcon(icon)  # Cambia el icono de la esquina superior izquierda
    except FileNotFoundError:
        print("El icono no fue encontrado.")
    # Usar el icono estándar del mensaje según el tipo
    msg_box.setIcon(tipo_icono)
    # Mostrar el cuadro de mensaje
    msg_box.exec()
