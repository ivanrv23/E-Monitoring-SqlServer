import sys
import os
import traceback
import datetime
import logging
import subprocess
import psutil
import atexit
import platform
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from PySide6.QtCore import QTimer
from views.splashscreen import SplashScreen
from utils.common.rutasarchivos import resource_path
from services.exportar.exportarDatos import ExportarDatos
from services.sync.sync_manager import SyncManager
# Constantes
LOG_FILE_PATH = "errores.log"
ICON_PATH = "resources/logo.png"
MESA_PATH = "resources/assets/mesa3d"

class MyApp:
    
    def __init__(self, mode="development"): # Cambiar a production
        self.mode = mode
        self.setup_logging()
        self.setup_gpu_handling()
        self.app = QApplication(sys.argv)
        self.app.setStyle("WindowsVista")
        self.app.setWindowIcon(QIcon(resource_path(ICON_PATH)))
        self.splash = SplashScreen()
        self.splash.show()
        QTimer.singleShot(1000, self.show_interfaz_principal)
        sys.excepthook = self.handle_exception
        atexit.register(self.cleanup)
    
    def kill_existing_instance(self):
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] == 'python.exe':  # Cambiar a E-Monitoring.exe en producción
                try:
                    proc.kill()
                except psutil.NoSuchProcess:
                    pass
    
    def setup_gpu_handling(self):
        if not self.is_gpu_available():
            self.configure_mesa()
    
    def is_gpu_available(self):
        CREATE_NO_WINDOW = 0x08000000  # Constante para ocultar la ventana de la consola
        try:
            # Intenta usar wmic para obtener información de la tarjeta gráfica
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            result = subprocess.run(['wmic', 'path', 'win32_VideoController', 'get', 'name'],
                                    capture_output=True, text=True, check=True,
                                    startupinfo=startupinfo, creationflags=CREATE_NO_WINDOW)
            output = result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Si wmic falla, intenta usar PowerShell
            try:
                result = subprocess.run(
                    ['powershell', 'Get-WmiObject Win32_VideoController | Select-Object -ExpandProperty Name'],
                    capture_output=True, text=True, check=True,
                    startupinfo=startupinfo, creationflags=CREATE_NO_WINDOW)
                output = result.stdout.strip()
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                logging.error(f"Error al ejecutar PowerShell: {e}")
                return False
        # Lista de tarjetas gráficas
        tarjetas = ["NVIDIA", "AMD", "Intel"]
        # Verifica si hay una tarjeta gráfica
        for tarjeta in tarjetas:
            if tarjeta in output:
                return True
        return False
    
    def configure_mesa(self):
        # Configurar GALLIUM_DRIVER solo si no está ya configurado
        if "GALLIUM_DRIVER" not in os.environ:
            os.environ["GALLIUM_DRIVER"] = "llvmpipe"
        # Determinar la arquitectura del sistema
        architecture = platform.architecture()[0]
        mesa_subdir = "x86" if architecture == "32bit" else "x64"
        mesa_path = os.path.join(resource_path(MESA_PATH), mesa_subdir)
        # Añadir el directorio de Mesa al PATH solo si no está ya presente
        if mesa_path not in os.environ["PATH"].split(os.pathsep):
            os.environ["PATH"] = f"{mesa_path}{os.pathsep}{os.environ['PATH']}"
        # Añadir el directorio de Mesa a la lista de directorios de DLL solo si está disponible y no está ya añadido
        if hasattr(os, "add_dll_directory"):
            try:
                # Intentar añadir el directorio de DLL
                os.add_dll_directory(mesa_path)
            except Exception as e:
                print(f"Error al añadir el directorio de DLL: {e}")
    
    def setup_logging(self):
        log_file_path = resource_path(LOG_FILE_PATH)
        if self.mode == "production" and not os.path.exists(log_file_path):
            with open(log_file_path, 'w') as file:
                file.write("Archivo de errores creado.\n")
        logging.basicConfig(filename=log_file_path, level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')
    
    def _procesar_datos_sync(self, payload: dict):
        print(f"Datos recibidos de {payload['instrumento']}: {payload['filas']} filas")
   
    def show_interfaz_principal(self):
        from views.principal import Principal
        Principal.show_main_view()
        self.splash.close()
        ExportarDatos.programar_exportacion()
        # Iniciar sincronización automática
        SyncManager.iniciar(
            on_datos  = self._procesar_datos_sync,
            on_log    = lambda msg: print(msg),
            on_error  = lambda err: print(err),
        )
    
    def run(self):
        try:
            sys.exit(self.app.exec())
        finally:
            self.cleanup()
    
    def cleanup(self):
        SyncManager.detener()
        self.kill_existing_instance()
    
    def handle_exception(self, exc_type, exc_value, exc_traceback):
        error_message = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        log_message = f"Fecha: {datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')}\nError:\n{error_message}\n"
        logging.error(log_message)
        if self.mode == "development":
            print(log_message)

if __name__ == "__main__":
    my_app = MyApp()
    my_app.run()
