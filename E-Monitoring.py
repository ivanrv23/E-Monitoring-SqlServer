import sys
import os
import threading
import tempfile
import traceback
import datetime
import logging
import subprocess
import atexit
import platform
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QIcon
from PySide6.QtCore import QTimer, QLockFile
from views.splashscreen import SplashScreen
from utils.common.rutasarchivos import resource_path
from services.exportar.exportarDatos import ExportarDatos
from services.sync.sync_manager import SyncManager
# Constantes
LOG_FILE_PATH = "errores.log"
ICON_PATH = "resources/logo.png"
MESA_PATH = "resources/assets/mesa3d"
CIERRE_TIMEOUT_SEG = 8  # tiempo máximo a esperar el apagado ordenado antes de forzar el cierre

class MyApp:
    
    def __init__(self, mode="development"): # Cambiar a production
        self.mode = mode
        self._cleanup_ejecutado = False
        self._cleanup_lock = threading.Lock()
        self.setup_logging()
        self.setup_gpu_handling()
        self.app = QApplication(sys.argv)

        if not self.verificar_instancia_unica():
            sys.exit(0)

        self.app.setStyle("WindowsVista")
        self.app.setWindowIcon(QIcon(resource_path(ICON_PATH)))  # se setea después de verificar
        self.splash = SplashScreen()
        self.splash.show()
        QTimer.singleShot(1000, self.show_interfaz_principal)
        sys.excepthook = self.handle_exception
        atexit.register(self.cleanup)
    
    def verificar_instancia_unica(self):
        """Usa QLockFile para impedir que se abra una segunda instancia.
        Si el proceso dueño del lock ya no existe (crash previo), Qt detecta
        el lock como 'stale' y lo libera automáticamente."""
        carpeta_lock = os.path.join(os.getenv("LOCALAPPDATA", tempfile.gettempdir()), "EMonitoring")
        os.makedirs(carpeta_lock, exist_ok=True)
        ruta_lock = os.path.join(carpeta_lock, "emonitoring.lock")
        self.lock_file = QLockFile(ruta_lock)
        self.lock_file.setStaleLockTime(30000)  # 30s

        if not self.lock_file.tryLock(100):
            self._mostrar_dialogo_instancia_duplicada()
            return False
        return True

    def _mostrar_dialogo_instancia_duplicada(self):
        """Muestra un QMessageBox con ícono de la aplicación cuando ya hay una instancia corriendo."""
        icono = QIcon(resource_path(ICON_PATH))

        dialogo = QMessageBox()
        dialogo.setWindowTitle("E-Monitoring")
        dialogo.setText("E-Monitoring ya se encuentra en ejecución.")
        dialogo.setIcon(QMessageBox.Icon.Warning)
        dialogo.setWindowIcon(icono)
        dialogo.setStandardButtons(QMessageBox.StandardButton.Ok)
        dialogo.exec()
    
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
        """Apagado ordenado con límite de tiempo. Si SyncManager.detener()
        se queda colgado esperando una consulta de red muerta, este método
        no espera indefinidamente: fuerza el cierre del proceso igual."""
        with self._cleanup_lock:
            if self._cleanup_ejecutado:
                return
            self._cleanup_ejecutado = True

        def _apagado_ordenado():
            try:
                SyncManager.detener()
            except Exception as e:
                logging.error(f"Error deteniendo SyncManager: {e}")

        hilo = threading.Thread(target=_apagado_ordenado, daemon=True, name="Shutdown")
        hilo.start()
        hilo.join(timeout=CIERRE_TIMEOUT_SEG)

        if hasattr(self, "lock_file"):
            self.lock_file.unlock()

        if hilo.is_alive():
            logging.warning(
                f"Cierre forzado: el apagado ordenado no terminó en {CIERRE_TIMEOUT_SEG}s "
                "(probablemente por una consulta de red colgada). Terminando proceso."
            )
            os._exit(0)
    
    def handle_exception(self, exc_type, exc_value, exc_traceback):
        error_message = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        log_message = f"Fecha: {datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')}\nError:\n{error_message}\n"
        logging.error(log_message)
        if self.mode == "development":
            print(log_message)

if __name__ == "__main__":
    my_app = MyApp()
    my_app.run()