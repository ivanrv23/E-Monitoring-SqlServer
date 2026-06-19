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
    def sincronizar_ahora(cls):
        if cls._worker and cls._worker.isRunning():
            cls._worker.sincronizar_ahora()
        else:
            # Iniciamos y el primer ciclo se ejecuta de inmediato
            cls.iniciar()

    @classmethod
    def recargar_conexiones(cls):
        cls.sincronizar_ahora()
    