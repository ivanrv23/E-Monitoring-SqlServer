import sys
import os

def resource_path(relative_path):
    # Obtener la ruta absoluta del archivo, compatible con entornos empaquetados
    if hasattr(sys, '_MEIPASS'):
        # Cuando está empaquetado con PyInstaller
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)
