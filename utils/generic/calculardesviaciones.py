from PySide6.QtWidgets import (QDialog,QVBoxLayout,QDateEdit,QDialogButtonBox)
from PySide6.QtCore import QDate
from collections import defaultdict
import numpy as np
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox, QPushButton, QComboBox
from controllers.AnalisisController import AnalisisController

class CalcularDesviaciones:
    
    def crear_dialogo_fecha_calculo():
        dialog = QDialog()
        dialog.setWindowTitle("Fecha de Cálculo")

        # Crear el layout principal
        layout = QVBoxLayout(dialog)

        # Crear el QDateEdit con la fecha actual
        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        date_edit.setDate(QDate.currentDate())
        layout.addWidget(date_edit)

        # Crear los botones Calcular y Cancelar
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(buttons)

        # Conectar las señales de los botones
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        dialog.setLayout(layout)

        # Mostrar el diálogo y esperar la respuesta del usuario
        if dialog.exec() == QDialog.Accepted:
            return date_edit.date().toString("yyyy-MM-dd")
        return None
    
    def calcular_y_guardar_desviaciones(proyecto_id, datos, fecha_calculo):
        # Calcular las desviaciones por equipo
        desviaciones_por_equipo = CalcularDesviaciones.calcular_desviaciones_por_equipo(datos)
        
        # Preparar los datos para guardar en la estructura requerida
        desviaciones_a_guardar = []
        
        for equipo, medidas in desviaciones_por_equipo.items():
            desviacion = {
                'id_proyecto': proyecto_id,
                'nombre_prisma': equipo,
                'centro_este': medidas['este']['centro'],
                'desviacion_este': medidas['este']['std1'],
                'centro_norte': medidas['norte']['centro'],
                'desviacion_norte': medidas['norte']['std1'],
                'centro_cota': medidas['cota']['centro'],
                'desviacion_cota': medidas['cota']['std1'],
                'fecha_calculo': fecha_calculo
            }
            desviaciones_a_guardar.append(desviacion)
        
        # Guardar en la base de datos
        if len(desviaciones_a_guardar)>1:
            respuesta = AnalisisController.ctrlGuardarDesviaciones(proyecto_id, desviaciones_a_guardar)
        else: 
            respuesta = AnalisisController.ctrlGuardarDesviacionesPrisma(proyecto_id, desviaciones_a_guardar)
        return respuesta
    
    def calcular_desviaciones_por_equipo(datos):
        # Organizar datos por equipo
        equipos = defaultdict(lambda: {'este': [], 'norte': [], 'cota': []})

        for equipo, fecha, este, norte, cota in datos:
            equipos[equipo]['este'].append(este)
            equipos[equipo]['norte'].append(norte)
            equipos[equipo]['cota'].append(cota)

        resultados = {}

        for equipo, medidas in equipos.items():
            # Obtener la primera lectura como valor de centro
            centro_este = medidas['este'][0]
            centro_norte = medidas['norte'][0]
            centro_cota = medidas['cota'][0]

            # Calcular desviaciones para Este (ignorando la primera lectura ya que se toma como centro)
            este_std = np.std(medidas['este'][1:], ddof=1)

            # Calcular desviaciones para Norte (ignorando la primera lectura ya que se toma como centro)
            norte_std = np.std(medidas['norte'][1:], ddof=1)

            # Calcular desviaciones para Cota (ignorando la primera lectura ya que se toma como centro)
            cota_std = np.std(medidas['cota'][1:], ddof=1)

            resultados[equipo] = {
                'este': {
                    'centro': centro_este,
                    'std1': este_std
                },
                'norte': {
                    'centro': centro_norte,
                    'std1': norte_std
                },
                'cota': {
                    'centro': centro_cota,
                    'std1': cota_std
                }
            }

        return resultados

    # def calcular_desviaciones_por_equipo(datos):
    #     # Organizar datos por equipo
    #     equipos = defaultdict(lambda: {'este': [], 'norte': [], 'cota': []})
        
    #     for equipo, fecha, este, norte, cota in datos:
    #         equipos[equipo]['este'].append(este)
    #         equipos[equipo]['norte'].append(norte)
    #         equipos[equipo]['cota'].append(cota)
        
    #     resultados = {}
        
    #     for equipo, medidas in equipos.items():
    #         # Calcular desviaciones para Este
    #         este_std1 = np.std(medidas['este'], ddof=1)
    #         este_std2 = este_std1 * 2
    #         este_std3 = este_std1 * 3
            
    #         # Calcular desviaciones para Norte
    #         norte_std1 = np.std(medidas['norte'], ddof=1)
    #         norte_std2 = norte_std1 * 2
    #         norte_std3 = norte_std1 * 3
            
    #         # Calcular desviaciones para Cota
    #         cota_std1 = np.std(medidas['cota'], ddof=1)
    #         cota_std2 = cota_std1 * 2
    #         cota_std3 = cota_std1 * 3
            
    #         resultados[equipo] = {
    #             'este': {'std1': este_std1, 'std2': este_std2, 'std3': este_std3},
    #             'norte': {'std1': norte_std1, 'std2': norte_std2, 'std3': norte_std3},
    #             'cota': {'std1': cota_std1, 'std2': cota_std2, 'std3': cota_std3}
    #         }
        
    #     return resultados
    
    def registro_desviacion(idproyecto, idcomonente):
        # Obtener la lista de prismas desde el controlador FALTAAAAAAA CAPTURAR EL ID COMPONENTE
        lprismas = AnalisisController.ctrlObtenerNombresPrismasComponente(idcomonente)
        # Crear el diálogo
        dialog = QDialog()
        dialog.setWindowTitle("Diálogo de Configuración")
        dialog.setLayout(QVBoxLayout())
        dialog.resize(400, 200)  # Establecer un tamaño inicial para el diálogo
        # Crear el combo box para seleccionar el prisma
        combo_box = QComboBox()
        # Extraer solo los nombres de la lista lprismas
        prism_names = [prism[3] for prism in lprismas]
        # Agregar los nombres al combo box
        for name in prism_names:
            combo_box.addItem(name)
        dialog.layout().addWidget(QLabel("Seleccionar Prisma:"))
        dialog.layout().addWidget(combo_box)
        # Crear los campos para 1σ, 2σ, 3σ con columnas para Este, Norte y Cota
        sigma_layout = QVBoxLayout()
        sigma_labels = ["1σ", "2σ", "3σ"]
        directions = ["Este", "Norte", "Cota"]
        sigma_inputs = {label: {} for label in sigma_labels}

        for label_text in sigma_labels:
            layout = QHBoxLayout()
            label = QLabel(label_text)
            layout.addWidget(label)
            for direction in directions:
                input_field = QDoubleSpinBox()
                input_field.setRange(0, 1000)  # Establecer un rango adecuado para los valores
                sigma_inputs[label_text][direction] = input_field
                layout.addWidget(QLabel(direction))
                layout.addWidget(input_field)
            sigma_layout.addLayout(layout)

        dialog.layout().addLayout(sigma_layout)

        # Label para mostrar mensajes de error o éxito
        message_label = QLabel()
        message_label.setStyleSheet("color: green;")
        dialog.layout().addWidget(message_label)

        def save_values():
            message_label.clear()
            try:
                selected_prism_name = combo_box.currentText()
                desviaciones = {
                    'id_proyecto': idproyecto,
                    'nombre_prisma': selected_prism_name,
                    'primera_desviacion_este': sigma_inputs["1σ"]["Este"].value(),
                    'primera_desviacion_norte': sigma_inputs["1σ"]["Norte"].value(),
                    'primera_desviacion_cota': sigma_inputs["1σ"]["Cota"].value(),
                    'segunda_desviacion_este': sigma_inputs["2σ"]["Este"].value(),
                    'segunda_desviacion_norte': sigma_inputs["2σ"]["Norte"].value(),
                    'segunda_desviacion_cota': sigma_inputs["2σ"]["Cota"].value(),
                    'tercera_desviacion_este': sigma_inputs["3σ"]["Este"].value(),
                    'tercera_desviacion_norte': sigma_inputs["3σ"]["Norte"].value(),
                    'tercera_desviacion_cota': sigma_inputs["3σ"]["Cota"].value(),
                    'fecha_calculo': QDate.currentDate().toString("yyyy-MM-dd")
                }
                # Guardar los valores en el controlador
                respuesta = AnalisisController.ctrlGuardarDesviacionesManualesPrisma(idproyecto, [desviaciones])
                if respuesta:
                    message_label.setText("Datos guardados correctamente.")
                    dialog.accept()
                else:
                    message_label.setStyleSheet("color: red;")
                    message_label.setText("Error al guardar los valores.")
            except Exception as e:
                message_label.setStyleSheet("color: red;")
                message_label.setText("Error al guardar los valores.")

        save_button = QPushButton("Guardar")
        save_button.clicked.connect(save_values)
        dialog.layout().addWidget(save_button)

        # Mostrar el diálogo
        dialog.exec()
    
    
    def ajustarDataDesviaciones(data,desviaciones):
        centroEste = desviaciones[0][3]
        desviacion_este = desviaciones[0][4]
        centroNorte = desviaciones[0][5]
        desviacion_norte = desviaciones[0][6]
        centroCota = desviaciones[0][7]
        desviacion_cota = desviaciones[0][8]
        # Extraer datos de coordenadas
        este = np.array([row[3] for row in data])
        norte = np.array([row[4] for row in data])
        cota = np.array([row[5] for row in data])
        # Función para calcular estadísticas usando la primera lectura como centro
        # def procesar_coordenada(valores):
        #     centro = valores[0]
        #     diferencias = valores - centro
        #     sigmadecimal = np.std(diferencias)
        #     sigma = round(sigmadecimal, 3)
        #     return centro, sigma
        # # Procesar coordenadas originales
        # centro_este, sigma_este = procesar_coordenada(este)
        # centro_norte, sigma_norte = procesar_coordenada(norte)
        # centro_cota, sigma_cota = procesar_coordenada(cota)
        # Procesar coordenadas originales
        centro_este, sigma_este = centroEste,desviacion_este
        centro_norte, sigma_norte = centroNorte,desviacion_norte
        centro_cota, sigma_cota = centroCota,desviacion_cota
        # Función para ajustar coordenadas según desviaciones estándar
        def ajustar_coordenada(valores, centro, sigma):
            valores_ajustados = []
            for x in valores:
                diff = x - centro
                abs_diff = abs(diff)
                if abs_diff <= sigma:       # 1σ: no se ajusta
                    ajustado = x
                elif abs_diff <= 2*sigma:   # 2σ: ajusta con ±1σ
                    ajustado = x - sigma if diff > 0 else x + sigma
                elif abs_diff <= 3*sigma:   # 3σ: ajusta con ±2σ
                    ajustado = x - 2*sigma if diff > 0 else x + 2*sigma
                else:                       # Fuera: ajusta con ±2σ sin verificación
                    ajustado = x - 2*sigma if diff > 0 else x + 2*sigma
                valores_ajustados.append(ajustado)
            return valores_ajustados
        # Aplicar ajustes
        este_ajust = ajustar_coordenada(este, centro_este, sigma_este)
        norte_ajust = ajustar_coordenada(norte, centro_norte, sigma_norte)
        cota_ajust = ajustar_coordenada(cota, centro_cota, sigma_cota)
        # Crear nueva versión de datos con coordenadas ajustadas
        data_ajustada = []
        for i, row in enumerate(data):
            new_row = (
                row[0],                # id
                row[1],                # Fecha
                row[2],                # nombre
                este_ajust[i],         # Este ajustado
                norte_ajust[i],        # Norte ajustado
                cota_ajust[i],         # Cota ajustada
                row[6]                 # Cota ajustada
            )
            data_ajustada.append(new_row)
        return data_ajustada
    