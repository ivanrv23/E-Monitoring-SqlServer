from PySide6.QtGui import QIntValidator, QStandardItemModel, QColor
from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex, QSortFilterProxyModel
from PySide6.QtWidgets import QTableView, QPushButton, QLineEdit
from utils.common.metodosGenerales import MetodosGenerales
from modules.empresa.softwareconfiguracion import SoftwareConfiguracion
from controllers.DatosController import DatosController
import warnings

# Clase CustomTableModel
class CustomTableModel(QAbstractTableModel):
    def __init__(self, data, headers, page_size=100, columna_color=None, parent=None):
        super().__init__(parent)
        self._data = data
        self._headers = headers
        self.page_size = page_size
        self.current_page = 0  # Página actual
        self.columna_color = columna_color

    def rowCount(self, parent=QModelIndex()):
        if not self._data:
            return 0
        start_index = self.current_page * self.page_size
        remaining = len(self._data) - start_index
        return min(self.page_size, remaining)

    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not self._data:
            return None
            
        row = index.row() + self.current_page * self.page_size
        if row >= len(self._data):
            return None
            
        col = index.column()
        if role == Qt.DisplayRole:
            return str(self._data[row][col])
            
        if self.columna_color is not None:
            if role == Qt.ForegroundRole and col == self.columna_color:
                if str(self._data[row][col]) == "Omitido":
                    return QColor("blue")
                    
        return None

    def change_page(self, new_page):
        if not self._data:
            self.current_page = 0
            return
            
        total_pages = max(1, (len(self._data) + self.page_size - 1) // self.page_size)
        if total_pages == 0:
            new_page = 0
        else:
            new_page = max(0, min(new_page, total_pages - 1))
        
        if new_page != self.current_page:
            self.beginResetModel()  # Iniciar reset para limpiar selecciones
            self.current_page = new_page
            self.endResetModel()    # Finalizar reset

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self._headers[section]
            elif orientation == Qt.Vertical:
                return str(section + 1 + self.current_page * self.page_size)
        return None

class VistaDatos:
    # Variables de estado para paginación
    pagina_actual = 1  # Almacena solo la página actual del tipo activo
    tipo_actual = ""    # Almacena el tipo de tabla actual
    
    def reiniciarPagina():
        VistaDatos.pagina_actual = 1
    
    def mostrarTablaEquipo(proyecto_id, main, idzona, tipo, equipos, refrescar):
        tabla = main.findChild(QTableView, "table_datos")
        
        # Reiniciar página si es un nuevo tipo de tabla
        if tipo != VistaDatos.tipo_actual:
            VistaDatos.tipo_actual = tipo
            VistaDatos.reiniciarPagina()
        
        if tipo == 'Prismas':
            VistaDatos.mostrar_tabla_prismas(proyecto_id, main, idzona, equipos, tabla, tipo,1)
        elif tipo == 'Inclinómetros':
            VistaDatos.mostrar_tabla_inclinometros(proyecto_id, main, idzona, equipos, tabla, tipo)
        elif tipo == 'Piezómetros Cuerda Vibrante':
            VistaDatos.mostrar_tabla_piezometros_cuerda(proyecto_id, main, idzona, equipos, tabla, tipo)
        elif tipo == 'Piezómetros Casagrande':
            VistaDatos.mostrar_tabla_piezometros_manual(proyecto_id, main, idzona, equipos, tabla, tipo)
        elif tipo == 'Pluviómetros':
            VistaDatos.mostrar_tabla_pluviometros(proyecto_id, main, idzona, equipos, tabla, tipo)
        elif tipo == 'Cotas de Terreno':
            VistaDatos.mostrar_tabla_cotas_terreno(proyecto_id, main, idzona, equipos, tabla, tipo)
        elif tipo == 'Celdas de Asentamiento':
            VistaDatos.mostrar_tabla_celdas_asentamiento(proyecto_id, main, idzona, equipos, tabla, tipo)
        elif tipo == 'Acelerógrafos':
            VistaDatos.mostrar_tabla_acelerografos(proyecto_id, main, idzona, equipos, tabla, tipo)
        elif tipo == 'TDR':
            VistaDatos.mostrar_tabla_sondajestdr(proyecto_id, main, idzona, equipos, tabla, tipo)
        elif tipo == 'Equipos Adicionales':
            VistaDatos.mostrar_tabla_equipos_adicionales(proyecto_id, main, idzona, equipos, tabla, tipo)
        elif tipo == 'Prismas de Baja':
            VistaDatos.mostrar_tabla_prismas(proyecto_id, main, idzona, equipos, tabla, tipo,0)

    def mostrar_tabla_prismas(proyecto_id, main, idzona, equipos, tablawidget, tipo,estado):
        dataprismasunido = []
        decimales, tipovelocidad = 2, 1
        respuesta = SoftwareConfiguracion.obtenerDataSoftware()
        if respuesta:
            decimales, tipovelocidad = respuesta[14], respuesta[15]
        resultado = MetodosGenerales.ctrlAgruparPrismasSegunTipo(equipos)
        for tabla, prismas in resultado.items():
            prismasdata = DatosController.ctrlObtenerDataPrismasMarcados(proyecto_id, tabla, idzona, prismas, tipovelocidad, estado, decimales)
            if prismasdata:
                dataprismasunido.extend(prismasdata)
        if len(dataprismasunido) > 0:
            headers = [
                "", "Prisma", "Fecha Hora", "Este (m)", "Norte (m)", "Elevación (msnm)", "Distancia Inclinada (m)", "DI3D (cm)",
                "DA3D (cm)", "VI3D (cm/dia)", "VA3D (cm/dia)", "A. Horizontal", "A. Vertical", "Estado", ""
            ]
            VistaDatos.llenarTabla(tablawidget, headers, dataprismasunido, main, tipo, 13)
            tablawidget.setColumnHidden(0, True)
            tablawidget.setColumnHidden(14, True)
        else:
            VistaDatos.limpiarTablaDatos(tablawidget)
        
    def mostrar_tabla_inclinometros(proyecto_id, main, idzona, equipos, tabla, tipo):
        decimales = 2
        respuesta = SoftwareConfiguracion.obtenerDataSoftware()
        if respuesta:
            decimales = respuesta[14]
        inclino = [dato[2] for dato in equipos]
        inclinometros = DatosController.ctrlObtenerInclinometros(proyecto_id, idzona, inclino, decimales)
        if inclinometros:
            headers = [
                "", "Inclinómetro", "Tipo Equipo", "Fecha Hora", "Profundidad (m)", "Face A+ (m)", "Face A- (m)",
                "Face B+ (m)", "Face B- (m)", "Este (m)", "Norte (m)", "Elevación (msnm)", ""
            ]
            VistaDatos.llenarTabla(tabla, headers, inclinometros, main, tipo)
            tabla.setColumnHidden(0, True)
            tabla.setColumnHidden(12, True)
        else:
            VistaDatos.limpiarTablaDatos(tabla)
        
    def mostrar_tabla_piezometros_cuerda(proyecto_id, main, idzona, equipos, tabla, tipo):
        decimales = 2
        respuesta = SoftwareConfiguracion.obtenerDataSoftware()
        if respuesta:
            decimales = respuesta[14]
        cuerdas = [dato[2] for dato in equipos]
        piezometros = DatosController.ctrlObtenerPiezometrosCuerda(proyecto_id, idzona, cuerdas, decimales)
        if piezometros:
            headers = [
                "", "Piezómetro", "Fecha Hora", "Frecuencia", "Temperatura (°C)", "Presión", "MCA", "Instalación", "Nivel Agua",
                "Este (m)", "Norte (m)", "Superficie (msnm)", "Fundación (msnm)", "Estado", "Observación", "", ""
            ]
            VistaDatos.llenarTabla(tabla, headers, piezometros, main, tipo, 13)
            tabla.setColumnHidden(0, True)
            tabla.setColumnHidden(15, True)
            tabla.setColumnHidden(16, True)
        else:
            VistaDatos.limpiarTablaDatos(tabla)
    
    def mostrar_tabla_piezometros_manual(proyecto_id, main, idzona, equipos, tabla, tipo):
        decimales = 2
        respuesta = SoftwareConfiguracion.obtenerDataSoftware()
        if respuesta:
            decimales = respuesta[14]
        manuales = [dato[2] for dato in equipos]
        piezometros = DatosController.ctrlObtenerPiezometrosManuales(proyecto_id, idzona, manuales, decimales)
        if piezometros:
            headers = [
                "", "Piezómetro", "Fecha Hora", "Nivel Piezómetrico (m)", "Profundidad (m)", "Superficie (msnm)", "Nivel Agua (msnm)",
                "Stick Up (m)", "Este (m)", "Norte (m)", "Fondo (msnm)", "Fundación (msnm)", "Estado", "Observación", "", ""
            ]
            VistaDatos.llenarTabla(tabla, headers, piezometros, main, tipo, 12)
            tabla.setColumnHidden(0, True)
            tabla.setColumnHidden(14, True)
            tabla.setColumnHidden(15, True)
        else:
            VistaDatos.limpiarTablaDatos(tabla)
    
    def mostrar_tabla_pluviometros(proyecto_id, main, idzona, equipos, tabla, tipo):
        decimales = 2
        respuesta = SoftwareConfiguracion.obtenerDataSoftware()
        if respuesta:
            decimales = respuesta[14]
        lluvias = [dato[2] for dato in equipos]
        pluviometros = DatosController.ctrlObtenerPluviometros(proyecto_id, idzona, lluvias, decimales)
        if pluviometros:
            headers = [
                "", "Pluviómetro", "Fecha Hora", "Precipitación (mm)", "Este (m)", "Norte (m)", "Elevación (msnm)", "Observación", ""
            ]
            VistaDatos.llenarTabla(tabla, headers, pluviometros, main, tipo)
            tabla.setColumnHidden(0, True)
            tabla.setColumnHidden(8, True)
        else:
            VistaDatos.limpiarTablaDatos(tabla)
    
    def mostrar_tabla_cotas_terreno(proyecto_id, main, idzona, equipos, tabla, tipo):
        decimales = 2
        respuesta = SoftwareConfiguracion.obtenerDataSoftware()
        if respuesta:
            decimales = respuesta[14]
        cotas = [dato[2] for dato in equipos]
        terrenos = DatosController.ctrlObtenerCotasTerreno(proyecto_id, idzona, cotas, decimales)
        if terrenos:
            headers = [ "", "Nombre Cota", "Fecha Hora", "Cota (msnm)", "Observación", ""]
            VistaDatos.llenarTabla(tabla, headers, terrenos, main, tipo)
            tabla.setColumnHidden(0, True)
            tabla.setColumnHidden(5, True)
        else:
            VistaDatos.limpiarTablaDatos(tabla)
    
    def mostrar_tabla_celdas_asentamiento(proyecto_id, main, idzona, equipos, tabla, tipo):
        decimales = 2
        respuesta = SoftwareConfiguracion.obtenerDataSoftware()
        if respuesta:
            decimales = respuesta[14]
        asentamiento = [dato[2] for dato in equipos]
        celdas = DatosController.ctrlObtenerCeldasAsentamiento(proyecto_id, idzona, asentamiento, decimales)
        if celdas:
            headers = [
                "", "Celda", "Fecha Hora", "Frecuencia (Digits)", "Frecuencia (Hz)", "Temperatura (°C)",
                "Desplazamiento (m)", "Cota (msnm)", "Instalación (msnm)", "Rango", "Este (m)", "Norte (m)",
                "Fundación (msnm)", "Superficie (msnm)", "Estado", "Observación", ""
            ]
            VistaDatos.llenarTabla(tabla, headers, celdas, main, tipo, 14)
            tabla.setColumnHidden(0, True)
            tabla.setColumnHidden(16, True)
        else:
            VistaDatos.limpiarTablaDatos(tabla)
    
    def mostrar_tabla_acelerografos(proyecto_id, main, idzona, equipos, tabla, tipo):
        decimales = 2
        respuesta = SoftwareConfiguracion.obtenerDataSoftware()
        if respuesta:
            decimales = respuesta[14]
        acelero = [dato[2] for dato in equipos]
        acelerografos = DatosController.ctrlObtenerAcelerografos(proyecto_id, idzona, acelero, decimales)
        if acelerografos:
            headers = [
                "", "Acelerógrafo", "Fecha Hora", "Magnitud", "Distancia (Km)",
                "Este (m)", "Norte (m)", "Elevación (msnm)", "Observacion", ""
            ]
            VistaDatos.llenarTabla(tabla, headers, acelerografos, main, tipo)
            tabla.setColumnHidden(0, True)
            tabla.setColumnHidden(9, True)
        else:
            VistaDatos.limpiarTablaDatos(tabla)
    
    def mostrar_tabla_sondajestdr(proyecto_id, main, idzona, equipos, tabla, tipo):
        decimales = 2
        respuesta = SoftwareConfiguracion.obtenerDataSoftware()
        if respuesta:
            decimales = respuesta[14]
        tdr = [dato[2] for dato in equipos]
        sondajestdr = DatosController.ctrlObtenerSondajestdr(proyecto_id, idzona, tdr, decimales)
        if sondajestdr:
            headers = [
                "", "TDR", "Fecha y Hora", "Profundidad (m)", "Impedancia", "Este (m)", "Norte (m)",
                "Elevación (msnm)", "Observación", ""
            ]
            VistaDatos.llenarTabla(tabla, headers, sondajestdr, main, tipo)
            tabla.setColumnHidden(0, True)
            tabla.setColumnHidden(9, True)
        else:
            VistaDatos.limpiarTablaDatos(tabla)
    
    def mostrar_tabla_equipos_adicionales(proyecto_id, main, idzona, equipos, tabla, tipo):
        decimales = 2
        respuesta = SoftwareConfiguracion.obtenerDataSoftware()
        if respuesta:
            decimales = respuesta[14]
        adicionales = [dato[2] for dato in equipos]
        equipos = DatosController.ctrlObtenerEquiposAdicionales(proyecto_id, idzona, adicionales, decimales)
        if equipos:
            headers = [
                "", "Equipo", "Tipo Equipo", "Este (m)", "Norte (m)", "Elevación (msnm)", "Descripción", ""
            ]
            VistaDatos.llenarTabla(tabla, headers, equipos, main, tipo)
            tabla.setColumnHidden(0, True)
            tabla.setColumnHidden(7, True)
        else:
            VistaDatos.limpiarTablaDatos(tabla)
    
    def llenarTabla(tabla, headers, data, main, tipo, columnacolor=0):
        # Limpiar selecciones antes de cambiar el modelo
        tabla.clearSelection()
        tabla.setSortingEnabled(False)
        tabla.setModel(None)

        # Limpiar el header y su estado de ordenación
        header = tabla.horizontalHeader()
        if header:
            header.setSortIndicator(-1, Qt.AscendingOrder)
            header.setSortIndicatorShown(False)

        # Crear y configurar el nuevo modelo
        model = CustomTableModel(data, headers, columna_color=columnacolor)
        proxy_model = QSortFilterProxyModel()
        proxy_model.setSourceModel(model)
        proxy_model.setSortCaseSensitivity(Qt.CaseInsensitive)

        # Asignar el nuevo proxy a la tabla
        tabla.setModel(proxy_model)
        proxy_model.sort(-1, Qt.AscendingOrder)

        # Limpiar selecciones después de asignar
        tabla.clearSelection()

        # Volver a ocultar el indicador de ordenación
        header = tabla.horizontalHeader()
        if header:
            header.setSortIndicatorShown(False)

        # Reactivar la ordenación
        tabla.setSortingEnabled(True)
        tabla.resizeColumnsToContents()
        tabla.resizeRowsToContents()

        # Obtener controles de paginación
        btn_pagina_inicio = main.findChild(QPushButton, "btn_pagina_inicio")
        btn_pagina_anterior = main.findChild(QPushButton, "btn_pagina_anterior")
        btn_pagina_siguiente = main.findChild(QPushButton, "btn_pagina_siguiente")
        btn_pagina_final = main.findChild(QPushButton, "btn_pagina_fin")
        input_pagina_salto = main.findChild(QLineEdit, "input_salto_pagina")
        
        # Validación de entrada numérica
        if input_pagina_salto:
            input_pagina_salto.setValidator(QIntValidator(1, 2147483647))
        
        # Configurar paginación inicial
        total_rows = len(data)
        page_size = model.page_size
        total_pages = max(1, (total_rows + page_size - 1) // page_size)
        
        # Usar la página actual almacenada
        pagina_actual = VistaDatos.pagina_actual
        pagina_actual = max(1, min(pagina_actual, total_pages))
        model.change_page(pagina_actual - 1)
        
        # Actualizar campo de entrada
        if input_pagina_salto:
            input_pagina_salto.setText(str(pagina_actual))

        # Función para actualizar estado de botones
        def update_button_states():
            current_page = model.current_page
            VistaDatos.actualizar_estado_botones(
                btn_pagina_inicio, 
                btn_pagina_anterior,
                btn_pagina_siguiente,
                btn_pagina_final,
                current_page,
                total_pages
            )
            if input_pagina_salto:
                input_pagina_salto.setText(str(current_page + 1))

        # Desconectar señales existentes de forma segura
        VistaDatos.safe_disconnect_all([
            (btn_pagina_inicio, 'clicked'),
            (btn_pagina_anterior, 'clicked'),
            (btn_pagina_siguiente, 'clicked'),
            (btn_pagina_final, 'clicked'),
            (input_pagina_salto, 'returnPressed')
        ])

        # Conectar nuevas señales con manejo de actualización
        if btn_pagina_inicio:
            btn_pagina_inicio.clicked.connect(
                lambda: [VistaDatos.first_page(model, tipo, tabla), update_button_states()])

        if btn_pagina_anterior:
            btn_pagina_anterior.clicked.connect(
                lambda: [VistaDatos.prev_page(model, tipo, tabla), update_button_states()])

        if btn_pagina_siguiente:
            btn_pagina_siguiente.clicked.connect(
                lambda: [VistaDatos.next_page(model, tipo, total_pages, tabla), update_button_states()])

        if btn_pagina_final:
            btn_pagina_final.clicked.connect(
                lambda: [VistaDatos.last_page(model, tipo, total_pages, tabla), update_button_states()])

        if input_pagina_salto:
            input_pagina_salto.returnPressed.connect(
                lambda: [VistaDatos.jump_to_page(model, input_pagina_salto, tipo, total_pages, tabla), update_button_states()])
        
        # Estado inicial de botones
        update_button_states()

    def prev_page(model, tipo, tabla):
        # Limpiar selecciones antes de cambiar de página
        tabla.clearSelection()
        if model.current_page > 0:
            model.change_page(model.current_page - 1)
            VistaDatos.pagina_actual = model.current_page + 1

    def next_page(model, tipo, total_pages, tabla):
        # Limpiar selecciones antes de cambiar de página
        tabla.clearSelection()
        if model.current_page < total_pages - 1:
            model.change_page(model.current_page + 1)
            VistaDatos.pagina_actual = model.current_page + 1

    def first_page(model, tipo, tabla):
        # Limpiar selecciones antes de cambiar de página
        tabla.clearSelection()
        model.change_page(0)
        VistaDatos.pagina_actual = 1

    def last_page(model, tipo, total_pages, tabla):
        # Limpiar selecciones antes de cambiar de página
        tabla.clearSelection()
        last_page_index = max(0, total_pages - 1)
        model.change_page(last_page_index)
        VistaDatos.pagina_actual = last_page_index + 1

    def jump_to_page(model, page_input, tipo, total_pages, tabla):
        # Limpiar selecciones antes de cambiar de página
        tabla.clearSelection()
        if not page_input:
            return
            
        try:
            target_page = int(page_input.text().strip())
            target_page = max(1, min(target_page, total_pages))
            model.change_page(target_page - 1)
            VistaDatos.pagina_actual = target_page
            page_input.setText(str(target_page))
        except ValueError:
            # Restaurar valor actual si entrada es inválida
            current_page = model.current_page + 1
            page_input.setText(str(current_page))

    def actualizar_estado_botones(btn_inicio, btn_prev, btn_next, btn_end, current_page, total_pages):
        """Actualiza estado de botones según posición actual"""
        if not total_pages or total_pages <= 1:
            for btn in [btn_inicio, btn_prev, btn_next, btn_end]:
                if btn: btn.setEnabled(False)
            return
            
        if btn_inicio: 
            btn_inicio.setEnabled(current_page > 0)
        if btn_prev: 
            btn_prev.setEnabled(current_page > 0)
        if btn_next: 
            btn_next.setEnabled(current_page < total_pages - 1)
        if btn_end: 
            btn_end.setEnabled(current_page < total_pages - 1)

    def safe_disconnect_all(connections):
        """Desconecta señales de múltiples controles de forma segura"""
        for obj, signal_name in connections:
            if obj:
                VistaDatos.safe_disconnect(obj, signal_name)
                
    def safe_disconnect(obj, signal_name):
        """Desconecta una señal manejando posibles errores"""
        try:
            signal = getattr(obj, signal_name, None)
            if signal and callable(getattr(signal, 'disconnect', None)):
                # Intenta desconectar sin especificar slot
                signal.disconnect()
        except Exception as e:
            print(f"Error manejado al desconectar señal: {str(e)}")

    def limpiarTablaDatos(tabla):
        # Limpiar selecciones antes de cambiar modelo
        tabla.clearSelection()
        model = QStandardItemModel()
        tabla.setModel(model)
        VistaDatos.reiniciarPagina()