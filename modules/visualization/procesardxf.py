import vtk
import ezdxf
import numpy as np
import functools
import os
import time
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from vtkmodules.util.numpy_support import numpy_to_vtk
from utils.common.rutasarchivos import resource_path

class ProcesarDXF:
    
    # Desactivando alertas de vtk
    vtk.vtkObject.GlobalWarningDisplayOff()
    # Nuevo arreglo de colores
    colores_cad_rgb = [
        (0, 0, 0), (255, 0, 0), (255, 255, 0), (0, 255, 0), (0, 255, 255),
        (0, 0, 255), (255, 0, 255), (255, 255, 255), (65, 65, 65), (128, 128, 128),
        (255, 0, 0), (255, 170, 170), (189, 0, 0), (189, 126, 126), (129, 0, 0),
        (129, 86, 86), (104, 0, 0), (104, 69, 69), (79, 0, 0), (79, 53, 53),
        (255, 63, 0), (255, 191, 170), (189, 46, 0), (189, 141, 126), (129, 31, 0),
        (129, 96, 86), (104, 25, 0), (104, 78, 69), (79, 19, 0), (79, 59, 53),
        (255, 127, 0), (255, 212, 170), (189, 94, 0), (189, 157, 126), (129, 64, 0),
        (129, 107, 86), (104, 52, 0), (104, 86, 69), (79, 39, 0), (79, 66, 53),
        (255, 191, 0), (255, 234, 170), (189, 141, 0), (189, 173, 126), (129, 96, 0),
        (129, 118, 86), (104, 78, 0), (104, 95, 69), (79, 59, 0), (79, 73, 53),
        (255, 255, 0), (255, 255, 170), (189, 189, 0), (189, 189, 126), (129, 129, 0),
        (129, 129, 86), (104, 104, 0), (104, 104, 69), (79, 79, 0), (79, 79, 53),
        (191, 255, 0), (234, 255, 170), (141, 189, 0), (173, 189, 126), (96, 129, 0),
        (118, 129, 86), (78, 104, 0), (95, 104, 69), (59, 79, 0), (73, 79, 53),
        (127, 255, 0), (212, 255, 170), (94, 189, 0), (157, 189, 126), (64, 129, 0),
        (107, 129, 86), (52, 104, 0), (86, 104, 69), (39, 79, 0), (66, 79, 53),
        (63, 255, 0), (191, 255, 170), (46, 189, 0), (141, 189, 126), (31, 129, 0),
        (96, 129, 86), (25, 104, 0), (78, 104, 69), (19, 79, 0), (59, 79, 53),
        (0, 255, 0), (170, 255, 170), (0, 189, 0), (126, 189, 126), (0, 129, 0),
        (86, 129, 86), (0, 104, 0), (69, 104, 69), (0, 79, 0), (53, 79, 53),
        (0, 255, 63), (170, 255, 191), (0, 189, 46), (126, 189, 141), (0, 129, 31),
        (86, 129, 96), (0, 104, 25), (69, 104, 78), (0, 79, 19), (53, 79, 59),
        (0, 255, 127), (170, 255, 212), (0, 189, 94), (126, 189, 157), (0, 129, 64),
        (86, 129, 107), (0, 104, 52), (69, 104, 86), (0, 79, 39), (53, 79, 66),
        (0, 255, 191), (170, 255, 234), (0, 189, 141), (126, 189, 173), (0, 129, 96),
        (86, 129, 118), (0, 104, 78), (69, 104, 95), (0, 79, 59), (53, 79, 73),
        (0, 255, 255), (170, 255, 255), (0, 189, 189), (126, 189, 189), (0, 129, 129),
        (86, 129, 129), (0, 104, 104), (69, 104, 104), (0, 79, 79), (53, 79, 79),
        (0, 191, 255), (170, 234, 255), (0, 141, 189), (126, 173, 189), (0, 96, 129),
        (86, 118, 129), (0, 78, 104), (69, 95, 104), (0, 59, 79), (53, 73, 79),
        (0, 127, 255), (170, 212, 255), (0, 94, 189), (126, 157, 189), (0, 64, 129),
        (86, 107, 129), (0, 52, 104), (69, 86, 104), (0, 39, 79), (53, 66, 79),
        (0, 63, 255), (170, 191, 255), (0, 46, 189), (126, 141, 189), (0, 31, 129),
        (86, 96, 129), (0, 25, 104), (69, 78, 104), (0, 19, 79), (53, 59, 79),
        (0, 0, 255), (170, 170, 255), (0, 0, 189), (126, 126, 189), (0, 0, 129),
        (86, 86, 129), (0, 0, 104), (69, 69, 104), (0, 0, 79), (53, 53, 79),
        (63, 0, 255), (191, 170, 255), (46, 0, 189), (141, 126, 189), (31, 0, 129),
        (96, 86, 129), (25, 0, 104), (78, 69, 104), (19, 0, 79), (59, 53, 79),
        (127, 0, 255), (212, 170, 255), (94, 0, 189), (157, 126, 189), (64, 0, 129),
        (107, 86, 129), (52, 0, 104), (86, 69, 104), (39, 0, 79), (66, 53, 79),
        (191, 0, 255), (234, 170, 255), (141, 0, 189), (173, 126, 189), (96, 0, 129),
        (118, 86, 129), (78, 0, 104), (95, 69, 104), (59, 0, 79), (73, 53, 79),
        (255, 0, 255), (255, 170, 255), (189, 0, 189), (189, 126, 189), (129, 0, 129),
        (129, 86, 129), (104, 0, 104), (104, 69, 104), (79, 0, 79), (79, 53, 79),
        (255, 0, 191), (255, 170, 234), (189, 0, 141), (189, 126, 173), (129, 0, 96),
        (129, 86, 118), (104, 0, 78), (104, 69, 95), (79, 0, 59), (79, 53, 73),
        (255, 0, 127), (255, 170, 212), (189, 0, 94), (189, 126, 157), (129, 0, 64),
        (129, 86, 107), (104, 0, 52), (104, 69, 86), (79, 0, 39), (79, 53, 66),
        (255, 0, 63), (255, 170, 191), (189, 0, 46), (189, 126, 141), (129, 0, 31),
        (129, 86, 96), (104, 0, 25), (104, 69, 78), (79, 0, 19), (79, 53, 59),
        (51, 51, 51), (80, 80, 80), (105, 105, 105), (130, 130, 130), (190, 190, 190),
        (255, 255, 255)
    ]

    @staticmethod
    @functools.lru_cache(maxsize=None)
    def formato_1_a_rgb(color_formato_1):
        valores = color_formato_1.split()
        r = int(valores[0]) / 255
        g = int(valores[1]) / 255
        b = int(valores[2]) / 255
        return (r, g, b)

    @staticmethod
    @functools.lru_cache(maxsize=None)
    def colorCADtoHexadecimal(colorCAD):
        colorRGB = ProcesarDXF.formato_1_a_rgb(f"{ProcesarDXF.colores_cad_rgb[colorCAD][0]} {ProcesarDXF.colores_cad_rgb[colorCAD][1]} {ProcesarDXF.colores_cad_rgb[colorCAD][2]}")
        return colorRGB

    @staticmethod
    def obtener_color_entidad(entity, doc):
        color = entity.dxf.get('color')
        true_color = entity.dxf.get('true_color')
        if color is not None:
            return ProcesarDXF.colorCADtoHexadecimal(color)
        elif true_color is not None:
            return ProcesarDXF.colorCADtoHexadecimal(true_color)
        elif entity.dxf.layer is not None:
            layer = doc.layers.get(entity.dxf.layer)
            if layer is not None and layer.color is not None:
                if isinstance(layer.color, int):
                    return ProcesarDXF.colorCADtoHexadecimal(layer.color)
                else:
                    return ProcesarDXF.colorCADtoHexadecimal(layer.color)
        return ProcesarDXF.colorCADtoHexadecimal(1)

    @staticmethod
    def procesar_entidades(entidades, doc, tipo_entidad):
        colores_puntos = {}
        colores_otros = {}
        entidades_insert = []
        entidades_circle = []

        for entity in entidades:
            if entity.dxftype() == tipo_entidad:
                coordenadas = []

                if tipo_entidad == 'POINT':
                    coordenadas.append((entity.dxf.location.x, entity.dxf.location.y, entity.dxf.location.z))
                    color = ProcesarDXF.obtener_color_entidad(entity, doc)
                    if color not in colores_puntos:
                        colores_puntos[color] = []
                    colores_puntos[color].extend(coordenadas)

                elif tipo_entidad in ['LWPOLYLINE', 'POLYLINE', 'LINE', '3DFACE']:
                    if tipo_entidad == 'LWPOLYLINE':
                        elevation = entity.dxf.elevation
                        for vertex in entity:
                            vertex_elevation = elevation if elevation is not None else vertex[2]
                            coordenadas.append((vertex[0], vertex[1], vertex_elevation))
                        if entity.is_closed:
                            coordenadas.append(coordenadas[0])

                    elif tipo_entidad == 'POLYLINE':
                        for vertex in entity.vertices:
                            coordenadas.append((vertex.dxf.location.x, vertex.dxf.location.y, vertex.dxf.location.z))
                        if entity.is_closed:
                            coordenadas.append(coordenadas[0])

                    elif tipo_entidad == 'LINE':
                        start_point = (entity.dxf.start.x, entity.dxf.start.y, entity.dxf.start.z)
                        end_point = (entity.dxf.end.x, entity.dxf.end.y, entity.dxf.end.z)
                        coordenadas = [start_point, end_point]

                    elif tipo_entidad == '3DFACE':
                        vertices = list(entity.wcs_vertices())
                        points = [(vertex.x, vertex.y, vertex.z) for vertex in vertices]
                        coordenadas = points

                    color = ProcesarDXF.obtener_color_entidad(entity, doc)
                    if color not in colores_otros:
                        colores_otros[color] = []
                    colores_otros[color].append(coordenadas)

                elif tipo_entidad == 'CIRCLE':
                    center = (entity.dxf.center.x, entity.dxf.center.y, entity.dxf.center.z)
                    radius = entity.dxf.radius
                    color = ProcesarDXF.obtener_color_entidad(entity, doc)
                    entidades_circle.append(('CIRCLE', (center, radius), color))

                elif tipo_entidad == 'INSERT':
                    block_name = entity.dxf.name
                    block = doc.blocks.get(block_name)
                    if block:
                        # Procesar entidades dentro del bloque
                        entidades_insert.extend(ProcesarDXF.procesar_bloque(block, doc))

        # Procesar entidades adicionales como entidades individuales
        for tipo, entidad, color in entidades_insert:
            if tipo == 'POINT':
                coordenadas = [(entidad.dxf.location.x, entidad.dxf.location.y, entidad.dxf.location.z)]
                if color not in colores_puntos:
                    colores_puntos[color] = []
                colores_puntos[color].extend(coordenadas)
            elif tipo in ['LWPOLYLINE', 'POLYLINE', 'LINE', '3DFACE']:
                coordenadas = []
                if tipo == 'LWPOLYLINE':
                    elevation = entidad.dxf.elevation
                    for vertex in entidad:
                        vertex_elevation = elevation if elevation is not None else vertex[2]
                        coordenadas.append((vertex[0], vertex[1], vertex_elevation))
                    if entidad.is_closed:
                        coordenadas.append(coordenadas[0])
                elif tipo == 'POLYLINE':
                    for vertex in entidad.vertices:
                        coordenadas.append((vertex.dxf.location.x, vertex.dxf.location.y, vertex.dxf.location.z))
                    if entidad.is_closed:
                        coordenadas.append(coordenadas[0])
                elif tipo == 'LINE':
                    start_point = (entidad.dxf.start.x, entidad.dxf.start.y, entidad.dxf.start.z)
                    end_point = (entidad.dxf.end.x, entidad.dxf.end.y, entidad.dxf.end.z)
                    coordenadas = [start_point, end_point]
                elif tipo == '3DFACE':
                    vertices = list(entidad.wcs_vertices())
                    points = [(vertex.x, vertex.y, vertex.z) for vertex in vertices]
                    coordenadas = points
                if color not in colores_otros:
                    colores_otros[color] = []
                colores_otros[color].append(coordenadas)
            elif tipo == 'CIRCLE':
                center = (entidad.dxf.center.x, entidad.dxf.center.y, entidad.dxf.center.z)
                radius = entidad.dxf.radius
                entidades_circle.append(('CIRCLE', (center, radius), color))

        return colores_puntos, colores_otros, entidades_circle

    @staticmethod
    def procesar_bloque(block, doc):
        entidades_adicionales = []
        for entity in block:
            tipo_entidad = entity.dxftype()
            if tipo_entidad == 'INSERT':
                # Procesar recursivamente si hay otro INSERT dentro del bloque
                entidades_adicionales.extend(ProcesarDXF.procesar_bloque(doc.blocks.get(entity.dxf.name), doc))
            else:
                # Agregar la entidad individual al resultado
                entidades_adicionales.append((tipo_entidad, entity, ProcesarDXF.obtener_color_entidad(entity, doc)))
        return entidades_adicionales

    @staticmethod
    def convertir_dxf_a_vtp(ruta_archivo, ruta):
        ruta_salida_base=resource_path(ruta)
        start_time = time.time()
        doc = ezdxf.readfile(ruta_archivo)
        msp = doc.modelspace()
        entidades = list(msp)
        tipos_entidades = set(entity.dxftype() for entity in entidades)
        results = {}
        def worker(tipo_entidad):
            return tipo_entidad, ProcesarDXF.procesar_entidades(entidades, doc, tipo_entidad)
        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(worker, tipo_entidad): tipo_entidad for tipo_entidad in tipos_entidades}
            for future in as_completed(futures):
                tipo_entidad, result = future.result()
                results[tipo_entidad] = result
        os.makedirs(ruta_salida_base, exist_ok=True)
        for tipo_entidad, (colores_puntos, colores_otros, entidades_circle) in results.items():
            entidades_por_color = {}
            for color, coordenadas in colores_puntos.items():
                if color not in entidades_por_color:
                    entidades_por_color[color] = vtk.vtkPolyData()
                punto_np = np.array(coordenadas, dtype=np.float64)
                puntos_vtk = numpy_to_vtk(punto_np)
                puntos_vtk_obj = vtk.vtkPoints()
                puntos_vtk_obj.SetData(puntos_vtk)
                polydata = entidades_por_color[color]
                polydata.SetPoints(puntos_vtk_obj)

                vertex_filter = vtk.vtkVertexGlyphFilter()
                vertex_filter.SetInputData(polydata)
                vertex_filter.Update()
                polydata = vertex_filter.GetOutput()

                colores = vtk.vtkUnsignedCharArray()
                colores.SetNumberOfComponents(3)
                colores.SetName("Colors")
                for i in range(polydata.GetNumberOfPoints()):
                    colores.InsertNextTuple3(*[int(c * 255) for c in color])
                polydata.GetPointData().SetScalars(colores)
                entidades_por_color[color] = polydata

            for color, coordenadas_list in colores_otros.items():
                if color not in entidades_por_color:
                    entidades_por_color[color] = vtk.vtkPolyData()
                polydata = entidades_por_color[color]
                puntos = vtk.vtkPoints()
                if tipo_entidad == '3DFACE':
                    poligonos = vtk.vtkCellArray()
                    colores = vtk.vtkUnsignedCharArray()
                    colores.SetNumberOfComponents(3)
                    colores.SetName("Colors")
                    punto_id = 0
                    for coordenadas in coordenadas_list:
                        poligono = vtk.vtkPolygon()
                        poligono.GetPointIds().SetNumberOfIds(len(coordenadas))
                        for i, punto in enumerate(coordenadas):
                            puntos.InsertNextPoint(punto)
                            poligono.GetPointIds().SetId(i, punto_id)
                            punto_id += 1
                        poligonos.InsertNextCell(poligono)
                        colores.InsertNextTuple3(*[int(c * 255) for c in color])

                    polydata.SetPoints(puntos)
                    polydata.SetPolys(poligonos)
                    polydata.GetCellData().SetScalars(colores)
                else:
                    lineas = vtk.vtkCellArray()
                    colores = vtk.vtkUnsignedCharArray()
                    colores.SetNumberOfComponents(3)
                    colores.SetName("Colors")
                    punto_id = 0
                    for coordenadas in coordenadas_list:
                        for punto in coordenadas:
                            puntos.InsertNextPoint(punto)
                        for i in range(len(coordenadas) - 1):
                            linea = vtk.vtkLine()
                            linea.GetPointIds().SetId(0, punto_id)
                            linea.GetPointIds().SetId(1, punto_id + 1)
                            lineas.InsertNextCell(linea)
                            colores.InsertNextTuple3(*[int(c * 255) for c in color])
                            punto_id += 1
                        punto_id += 1
                    polydata.SetPoints(puntos)
                    polydata.SetLines(lineas)
                    polydata.GetCellData().SetScalars(colores)
                entidades_por_color[color] = polydata

            for tipo_entidad, info, color in entidades_circle:
                if tipo_entidad == 'CIRCLE':
                    center = info[0]
                    radius = info[1]
                    circle_source = vtk.vtkRegularPolygonSource()
                    circle_source.SetCenter(center[0], center[1], center[2])
                    circle_source.SetRadius(radius)
                    circle_source.SetNumberOfSides(100)
                    circle_source.Update()

                    polydata = circle_source.GetOutput()

                    colores = vtk.vtkUnsignedCharArray()
                    colores.SetNumberOfComponents(3)
                    colores.SetName("Colors")

                    color_rgb = [int(c * 255) for c in color]
                    for _ in range(polydata.GetNumberOfPoints()):
                        colores.InsertNextTuple3(*color_rgb)

                    polydata.GetPointData().SetScalars(colores)

                    if tuple(color_rgb) not in entidades_por_color:
                        entidades_por_color[tuple(color_rgb)] = vtk.vtkPolyData()
                    entidades_por_color[tuple(color_rgb)].ShallowCopy(polydata)

            for color, polydata in entidades_por_color.items():
                ruta_salida = os.path.join(ruta_salida_base, f"{tipo_entidad}_{color}.vtp")
                writer = vtk.vtkXMLPolyDataWriter()
                writer.SetFileName(ruta_salida)
                writer.SetInputData(polydata)
                writer.SetDataModeToBinary()
                writer.Write()
        end_time = time.time()
    
    def graficar_vtp_antigua(ruta_carpeta):
        ruta_archivos = resource_path(ruta_carpeta)
        # Listar todos los archivos VTP en la carpeta
        archivos_vtp = [f for f in os.listdir(ruta_archivos) if f.endswith('.vtp')]
        # Crear una lista para almacenar los actores
        actores = []
        # Cargar y crear actores para cada archivo VTP
        for archivo in archivos_vtp:
            ruta_archivo = os.path.join(ruta_archivos, archivo)
            reader = vtk.vtkXMLPolyDataReader()
            reader.SetFileName(ruta_archivo)
            reader.Update()
            polydata = reader.GetOutput()
            # Crear un mapper y un actor para el polydata
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputData(polydata)
            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            # Agregar el actor a la lista de actores
            actores.append(actor)
        # Retornar la lista de actores
        return actores
    
    def graficar_vtp(ruta_carpeta):
        try:
            ruta_archivo = resource_path(ruta_carpeta)
            actor = None
            reader = vtk.vtkXMLPolyDataReader()
            reader.SetFileName(ruta_archivo)
            reader.Update()
            polydata = reader.GetOutput()
            # Crear un mapper y un actor para el polydata
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputData(polydata)
            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            return actor
        except:
            return None
    
    def distanciaEuclidiana(color1, color2):
        r1, g1, b1 = color1
        r2, g2, b2 = color2
        return math.sqrt((r1 - r2)**2 + (g1 - g2)**2 + (b1 - b2)**2)

    def encontrarColorCercano(color_dado):
        mejor_distancia = float('inf')  # Inicializar con una distancia infinita
        posicion = 0
        for i, colorcad in enumerate(ProcesarDXF.colores_cad_rgb):
            distancia = ProcesarDXF.distanciaEuclidiana(color_dado, colorcad)
            if distancia < mejor_distancia:
                mejor_distancia = distancia
                posicion = i
        return posicion
    
    def colorRGBtoCAD(coloresvector):
        colores = []
        for idinst, idcompon, colorrgb in coloresvector:
            color = (int(colorrgb[0] * 255), int(colorrgb[1] * 255), int(colorrgb[2] * 255))
            colorcad = ProcesarDXF.encontrarColorCercano(color)
            colores.append((idinst, idcompon, colorcad))
        return colores
    