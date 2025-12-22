
import ezdxf
import math
from PySide6.QtWidgets import QFileDialog
from utils.common.alertas import mostrar_mensaje
from controllers.PrismaController import PrismaController
from modules.visualization.procesardxf import ProcesarDXF

class ExportarDXF:
    
    def generarDXFvectores(proyectoid, escala, prismasmarcados, colorvectores, fechainicial, fechafinal, filtrado):
        piniciales = PrismaController.ctrlObtenerPrismasInicialesFecha(prismasmarcados, fechainicial, fechafinal, filtrado)
        pfinales = PrismaController.ctrlObtenerPrismasFinalesFecha(prismasmarcados, fechainicial, fechafinal, filtrado)
        prismasnombre = []
        puntosejexini = []
        puntosejeyini = []
        puntosejezini = []
        puntosejexfin = []
        puntosejeyfin = []
        puntosejezfin = []
        if len(piniciales) > 0 and len(pfinales) > 0:
            for componente, prismas in prismasmarcados:
                for nameprisma, idinstrumento, tabla in prismas:
                    for resulini, resulfin in zip(piniciales, pfinales):
                        if str(componente[1]) == str(resulini[5]) and nameprisma == resulini[1]:
                            puntosejexini.append(float(resulini[2]))
                            puntosejeyini.append(float(resulini[3]))
                            puntosejezini.append(float(resulini[4]))
                            prismasnombre.append((resulini[0], resulini[5])) # id_instrumentacion, id_componente
                            puntosejexfin.append(float(resulfin[2]))
                            puntosejeyfin.append(float(resulfin[3]))
                            puntosejezfin.append(float(resulfin[4]))
        # obtener colores CAD
        coloresvectorCAD = ProcesarDXF.colorRGBtoCAD(colorvectores)
        # Crea un nuevo dibujo DXF
        doc = ezdxf.new()
        msp = doc.modelspace()
        if escala > 0:
            factor_escala = escala
        else:
            factor_escala = 1
        # Agrega cada flecha al dibujo
        for i in range(len(puntosejexini)):
            start_point = (puntosejexini[i], puntosejeyini[i], puntosejezini[i])
            end_point = (puntosejexfin[i], puntosejeyfin[i], puntosejezfin[i])
            if start_point != end_point:
                for idinstru, idcompon, color in coloresvectorCAD:
                    if str(prismasnombre[i][0]) == str(idinstru) and str(prismasnombre[i][1]) == str(idcompon):
                        ExportarDXF.procesarDataVectores(msp, start_point, end_point, factor_escala, color)
        # Abrir el cuadro de diálogo para seleccionar la ubicación y el nombre del archivo
        archivo_destino, _ = QFileDialog.getSaveFileName(None, "Guardar DXF como", "", "Archivos DXF (*.dxf);;Todos los archivos (*)")
        if archivo_destino:
            # Guarda el dibujo en un archivo DXF con el nombre especificado
            doc.saveas(archivo_destino)
            mostrar_mensaje("VECTORES GUARDADOS", f"El DXF se ha guardado en: {archivo_destino}", "informacion")
        
    def procesarDataVectores(msp, start, end, scale_factor, color):
        # Calcula las coordenadas de inicio y fin
        x_start, y_start, z_start = start
        x_final, y_final, z_final = end
        
        # Aplica la escala a las coordenadas finales de la flecha
        x_final_scaled = x_start + (x_final - x_start) * scale_factor
        y_final_scaled = y_start + (y_final - y_start) * scale_factor
        z_final_scaled = z_start + (z_final - z_start) * scale_factor

        # Calcula la dirección de la flecha
        dx = x_final_scaled - x_start
        dy = y_final_scaled - y_start
        dz = z_final_scaled - z_start
        distancia = math.sqrt(dx**2 + dy**2 + dz**2)
        direction = (dx / distancia, dy / distancia, dz / distancia)

        # Calcula una dirección perpendicular al plano XY
        perp_direction = (-direction[1], direction[0], 0)  # Gira 90 grados en sentido antihorario

        # Calcula la longitud de las alas
        wing_length = distancia * 0.1  # 10% de la longitud total de la flecha

        # Calcula las coordenadas de las alas escaladas
        wing1_scaled = (x_final_scaled - direction[0] * wing_length + perp_direction[0] * wing_length / 2,
                        y_final_scaled - direction[1] * wing_length + perp_direction[1] * wing_length / 2,
                        z_final_scaled - direction[2] * wing_length + perp_direction[2] * wing_length / 2)

        wing2_scaled = (x_final_scaled - direction[0] * wing_length - perp_direction[0] * wing_length / 2,
                        y_final_scaled - direction[1] * wing_length - perp_direction[1] * wing_length / 2,
                        z_final_scaled - direction[2] * wing_length - perp_direction[2] * wing_length / 2)
        
        # Agrega la línea principal de la flecha
        line = msp.add_line(start, (x_final_scaled, y_final_scaled, z_final_scaled))
        line.dxf.color = color
        
        # Agrega las alas de la flecha con el color especificado
        wing1 = msp.add_line((x_final_scaled, y_final_scaled, z_final_scaled), wing1_scaled)
        wing1.dxf.color = color
        
        wing2 = msp.add_line((x_final_scaled, y_final_scaled, z_final_scaled), wing2_scaled)
        wing2.dxf.color = color
