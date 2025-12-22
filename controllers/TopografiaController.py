import os
import shutil
from models.TopografiaModel import TopografiaModel
from modules.visualization.procesardxf import ProcesarDXF
from utils.shared.loading import LoadingView
from PySide6.QtCore import QThread, Signal
from utils.common.rutasarchivos import resource_path
# Hilo procesar topografías
class ProcesarTopografiaThread(QThread):
    task_finishProcesardxf = Signal()

    def __init__(self, archivoTopo,ubicacion):
        super().__init__()
        self.archivoTopo = archivoTopo
        self.ubicacion = ubicacion

    def run(self):
        # procesar topografia
        ProcesarDXF.convertir_dxf_a_vtp(self.archivoTopo, self.ubicacion)
        # mandar señal
        self.task_finishProcesardxf.emit()
    
class TopografiaController:
    
    def ctrlObtenerTipoTopografia(proyectoid, idcomponente, idtopo):
        respuesta = TopografiaModel.mdlObtenerTipoTopografia(proyectoid, idcomponente, idtopo)
        return respuesta
    
    # traer data de suelos para la tabla
    def ctrlObtenerDataCotasTerrenoDetalle(marcados):
        datasuelos = []
        for idsuelo, nombre, tipo in marcados:
            datos = TopografiaModel.mdlObtenerDataCotasTerrenoDetalle(idsuelo)
            if datos is not None:
                datasuelos.extend(datos)
        return datasuelos
    
    def ctrlRegistrarNuevaTopografia(proyectoid, idcomponente, nombrenuevo, archivoTopo, tipo, exten, comentario,fecha_topografia):
        # Carpeta de destino para guardar el archivo
        ubicacion = f"resources/workspace/proyecto{proyectoid}/{nombrenuevo}{idcomponente}{exten}"
        respuesta, idtoponueva = TopografiaModel.mdlRegistrarNuevaTopografia(proyectoid, idcomponente, nombrenuevo, tipo, ubicacion, comentario,fecha_topografia)
        if respuesta:
            carpeta_destino = resource_path(f"resources/workspace/proyecto{proyectoid}")
            # Verificar si la carpeta de destino existe, si no, créala
            if not os.path.exists(carpeta_destino):
                os.makedirs(carpeta_destino)
            ruta_destino = os.path.join(carpeta_destino, f'{nombrenuevo}{idcomponente}{exten}')
            # Copiar el archivo a la carpeta de destino
            if shutil.copy(archivoTopo, ruta_destino):
                return idtoponueva
            else:
                return None
        else:
            return None
        
    def ctrlRegistrarNuevaTopografia2(proyectoid, idcomponente, nombrenuevo, archivoTopo, tipo, comentario, fecha_formateada):
        ubicacion=f"resources/workspace/proyecto{proyectoid}/{nombrenuevo}{idcomponente}"
         # Iniciar Hilo
        loading = LoadingView.mostrarLoading()
        def on_thread_complete():
            loading.close()
        procesa_dxf = ProcesarTopografiaThread(archivoTopo, ubicacion)
        procesa_dxf.task_finishProcesardxf.connect(on_thread_complete)
        procesa_dxf.start()
        loading.exec()
        respuesta, idtoponueva = TopografiaModel.mdlRegistrarNuevaTopografia(proyectoid, idcomponente, nombrenuevo, tipo, ubicacion, comentario, fecha_formateada)
        if respuesta:
            return idtoponueva
        else:
            return None
    
    def ctrlCambiarComponenteTopografias(idcomponente, nuevocomponente):
        respuesta = TopografiaModel.mdlCambiarComponenteTopografias(idcomponente, nuevocomponente)
        return respuesta
    
    def ctrlEliminarTopografias(idcomponente):
        respuesta = TopografiaModel.mdlEliminarTopografias(idcomponente)
        return respuesta
    
    def ctrlEliminarDataTopografias(datos):
        topos = [dato[4] for dato in datos]
        respuesta = TopografiaModel.mdlEliminarDataTopografias(topos)
        if respuesta:
            for topo in respuesta:
                ruta_archivo = resource_path(topo[4])
                if not ruta_archivo or not os.path.exists(ruta_archivo):
                    continue
                try:
                    os.remove(ruta_archivo)
                except FileNotFoundError:
                    continue
                except PermissionError:
                    continue
            return True
        else:
            return False
    
    def ctrlObtenerInfoTopografia(idinstrumento):
        respuesta = TopografiaModel.mdlObtenerInfoTopografia(idinstrumento)
        return respuesta
    
    def ctrlActualizarTopografia(componente, nombrenuevo, comentario, asignarfecha, idinstrumento, idtopografia):
        respuesta = TopografiaModel.mdlActualizarTopografia(componente, nombrenuevo, comentario, asignarfecha, idinstrumento, idtopografia)
        return respuesta
    
    def ctrlEliminarTopografia(idinstrumento):
        respuesta = TopografiaModel.mdlEliminarTopografia(idinstrumento)
        return respuesta
    
    def ctrlEliminarTopografiaData(dato):
        respuesta = TopografiaModel.mdlEliminarTopografiaData(dato[4])
        return respuesta
    
    def ctrlObtenerFechaTopografia(idtopo):
        respuesta = TopografiaModel.mdlObtenerFechaTopografia(idtopo)
        return respuesta
    
    def ctrlRegistrarPrismaVirtual(id_componente,x, y, z, nombre_prisma, radio, color):
        respuesta = TopografiaModel.mdlRegistrarPrismaVirtual(id_componente,x, y, z, nombre_prisma, radio, color)
        return respuesta
    