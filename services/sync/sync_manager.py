from PySide6.QtCore import QEventLoop, QTimer
from services.sync.conexion_worker import ConexionWorker

class SyncManager:
    _worker: ConexionWorker = None

    @classmethod
    def iniciar(cls, on_log=None, on_error=None, on_datos=None):
        if cls._worker and cls._worker.isRunning():
            return
        cls._worker = ConexionWorker()
        if on_log:   cls._worker.senal_log.connect(on_log)
        if on_error: cls._worker.senal_error.connect(on_error)
        if on_datos: cls._worker.senal_datos.connect(on_datos)
        cls._worker.start()

    @classmethod
    def detener(cls):
        if cls._worker:
            cls._worker.detener()
            cls._worker.wait()
            cls._worker = None

    @classmethod
    def sincronizar_ahora(cls, timeout_ms: int = 120000):
        # Si el worker no existe o no está corriendo, lo iniciamos.
        worker_recien_iniciado = False
        if not (cls._worker and cls._worker.isRunning()):
            cls.iniciar()
            worker_recien_iniciado = True

        worker = cls._worker
        loop = QEventLoop()

        def _on_completo():
            if loop.isRunning():
                loop.quit()

        worker.senal_sync_completo.connect(_on_completo)

        # si por algún motivo nunca llega la señal, no nos quedamos colgados para siempre.
        timer_seguridad = QTimer()
        timer_seguridad.setSingleShot(True)
        timer_seguridad.timeout.connect(loop.quit)
        timer_seguridad.start(timeout_ms)

        # Si el worker ya estaba corriendo de antes, forzamos el ciclo.
        if not worker_recien_iniciado:
            worker.sincronizar_ahora()

        loop.exec()

        timer_seguridad.stop()
        worker.senal_sync_completo.disconnect(_on_completo)

    @classmethod
    def recargar_conexiones(cls):
        cls.sincronizar_ahora()
    
