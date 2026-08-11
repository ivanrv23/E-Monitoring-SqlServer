from PySide6.QtGui import QIntValidator, QStandardItemModel, QColor
from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex, QSortFilterProxyModel
from PySide6.QtWidgets import QPushButton, QLineEdit
from utils.common.metodosGenerales import MetodosGenerales
from modules.empresa.softwareconfiguracion import SoftwareConfiguracion
from controllers.DatosController import DatosController

# Clase CustomTableModel
class CustomTableModel(QAbstractTableModel):
    def __init__(self, data, headers, page_size=100, columna_color=None, parent=None):
        super().__init__(parent)
        self._data = data
        self._headers = headers
        self.page_size = page_size
        self.current_page = 0  # Página actual
        self.columna_color = columna_color
        
        # Definir columnas numéricas por tipo de datos
        self.columnas_numericas = self._identificar_columnas_numericas(headers)

    def _identificar_columnas_numericas(self, headers):
        """Identifica qué columnas contienen datos numéricos basándose en los encabezados"""
        columnas_num = []
        
        # Palabras clave que indican columnas numéricas
        keywords_numericos = [
            'este', 'norte', 'elevación', 'cota', 'distancia', 'frecuencia', 
            'temperatura', 'presión', 'mca', 'nivel', 'profundidad', 'magnitud',
            'desplazamiento', 'impedancia', 'precipitación', 'stick up',
            'face a+', 'face a-', 'face b+', 'face b-', 'di3d', 'da3d', 
            'vi3d', 'va3d', 'fundación', 'superficie', 'instalación', 'fondo'
        ]
        
        for idx, header in enumerate(headers):
            header_lower = header.lower()
            if any(keyword in header_lower for keyword in keywords_numericos):
                columnas_num.append(idx)
        
        return columnas_num
    
    def _formatear_numero(self, valor, col_index):
        """
        Formatea un número con decimales específicos según el tipo de columna
        """
        if valor is None or valor == '':
            return ''
        
        try:
            num = float(valor)
            header = self._headers[col_index].lower()
            
            # Definir decimales según tipo de dato
            if any(x in header for x in ['este', 'norte']):
                decimales = 4  # Coordenadas UTM: 4 decimales
            elif any(x in header for x in ['elevación', 'cota', 'profundidad', 'nivel']):
                decimales = 3  # Elevaciones: 3 decimales
            elif any(x in header for x in ['di3d', 'da3d', 'desplazamiento']):
                decimales = 2  # Desplazamientos: 2 decimales
            elif any(x in header for x in ['vi3d', 'va3d', 'velocidad']):
                decimales = 2  # Velocidades: 2 decimales
            else:
                decimales = 2  # Por defecto: 2 decimales
            
            return f"{num:.{decimales}f}"
                    
        except (ValueError, TypeError):
            return str(valor)

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
        valor = self._data[row][col]
        
        if role == Qt.DisplayRole:
            # Si la columna es numérica, formatear el número
            if col in self.columnas_numericas:
                return self._formatear_numero(valor, col)  # Pasar el índice de columna
            else:
                return str(valor)
            
        if self.columna_color is not None:
            if role == Qt.ForegroundRole and col == self.columna_color:
                if str(valor) == "Omitido":
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
    
    def obtenerDatosTablaEquipo(proyecto_id, idzona, tipo, equipos):
        """Solo trae y prepara datos (headers/filas). NO toca widgets Qt.
        Seguro para ejecutarse dentro de un QThread."""
        decimales, tipovelocidad = 2, 1
        respuesta = SoftwareConfiguracion.obtenerDataSoftware()
        if respuesta:
            decimales, tipovelocidad = respuesta[14], respuesta[15]

        if tipo == 'Prismas':
            return VistaDatos.datos_tabla_prismas(proyecto_id, idzona, equipos, decimales, tipovelocidad, 1)
        elif tipo == 'Prismas de Baja':
            return VistaDatos.datos_tabla_prismas(proyecto_id, idzona, equipos, decimales, tipovelocidad, 0)
        elif tipo == 'Inclinómetros':
            return VistaDatos.datos_tabla_inclinometros(proyecto_id, idzona, equipos, decimales)
        elif tipo == 'Piezómetros Cuerda Vibrante':
            return VistaDatos.datos_tabla_piezometros_cuerda(proyecto_id, idzona, equipos, decimales)
        elif tipo == 'Piezómetros Casagrande':
            return VistaDatos.datos_tabla_piezometros_manual(proyecto_id, idzona, equipos, decimales)
        elif tipo == 'Pluviómetros':
            return VistaDatos.datos_tabla_pluviometros(proyecto_id, idzona, equipos, decimales)
        elif tipo == 'Cotas de Terreno':
            return VistaDatos.datos_tabla_cotas_terreno(proyecto_id, idzona, equipos, decimales)
        elif tipo == 'Celdas de Asentamiento':
            return VistaDatos.datos_tabla_celdas_asentamiento(proyecto_id, idzona, equipos, decimales)
        elif tipo == 'Acelerógrafos':
            return VistaDatos.datos_tabla_acelerografos(proyecto_id, idzona, equipos, decimales)
        elif tipo == 'TDR':
            return VistaDatos.datos_tabla_sondajestdr(proyecto_id, idzona, equipos, decimales)
        elif tipo == 'Equipos Adicionales':
            return VistaDatos.datos_tabla_equipos_adicionales(proyecto_id, idzona, equipos, decimales)
        return None

    def construirTablaEquipo(main, tabla, tipo, resultado):
        """Aplica el resultado a la tabla. SIEMPRE debe correr en el hilo principal (GUI thread)."""
        if resultado:
            VistaDatos.llenarTabla(tabla, resultado['headers'], resultado['data'], main, tipo, resultado.get('columnacolor', 0))
            for col in resultado.get('hidden', []):
                tabla.setColumnHidden(col, True)
        else:
            VistaDatos.limpiarTablaDatos(tabla)

    def datos_tabla_prismas(proyecto_id, idzona, equipos, decimales, tipovelocidad, estado):
        dataprismasunido = []
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
            return {'headers': headers, 'data': dataprismasunido, 'columnacolor': 13, 'hidden': [0, 14]}
        return None

    def datos_tabla_inclinometros(proyecto_id, idzona, equipos, decimales):
        inclino = [dato[2] for dato in equipos]
        inclinometros = DatosController.ctrlObtenerInclinometros(proyecto_id, idzona, inclino, decimales)
        if inclinometros:
            headers = [
                "", "Inclinómetro", "Tipo Equipo", "Fecha Hora", "Profundidad (m)", "Face A+ (m)", "Face A- (m)",
                "Face B+ (m)", "Face B- (m)", "Este (m)", "Norte (m)", "Elevación (msnm)", ""
            ]
            return {'headers': headers, 'data': inclinometros, 'columnacolor': 0, 'hidden': [0, 12]}
        return None

    def datos_tabla_piezometros_cuerda(proyecto_id, idzona, equipos, decimales):
        cuerdas = [dato[2] for dato in equipos]
        piezometros = DatosController.ctrlObtenerPiezometrosCuerda(proyecto_id, idzona, cuerdas, decimales)
        if piezometros:
            headers = [
                "", "Piezómetro", "Fecha Hora", "Frecuencia", "Temperatura (°C)", "Presión", "MCA", "Instalación", "Nivel Agua",
                "Este (m)", "Norte (m)", "Superficie (msnm)", "Fundación (msnm)", "Estado", "Observación", "", ""
            ]
            return {'headers': headers, 'data': piezometros, 'columnacolor': 13, 'hidden': [0, 15, 16]}
        return None

    def datos_tabla_piezometros_manual(proyecto_id, idzona, equipos, decimales):
        manuales = [dato[2] for dato in equipos]
        piezometros = DatosController.ctrlObtenerPiezometrosManuales(proyecto_id, idzona, manuales, decimales)
        if piezometros:
            headers = [
                "", "Piezómetro", "Fecha Hora", "Nivel Piezómetrico (m)", "Profundidad (m)", "Superficie (msnm)", "Nivel Agua (msnm)",
                "Stick Up (m)", "Este (m)", "Norte (m)", "Fondo (msnm)", "Fundación (msnm)", "Estado", "Observación", "", ""
            ]
            return {'headers': headers, 'data': piezometros, 'columnacolor': 12, 'hidden': [0, 14, 15]}
        return None

    def datos_tabla_pluviometros(proyecto_id, idzona, equipos, decimales):
        lluvias = [dato[2] for dato in equipos]
        pluviometros = DatosController.ctrlObtenerPluviometros(proyecto_id, idzona, lluvias, decimales)
        if pluviometros:
            headers = [
                "", "Pluviómetro", "Fecha Hora", "Precipitación (mm)", "Este (m)", "Norte (m)", "Elevación (msnm)", "Observación", "Estado", ""
            ]
            return {'headers': headers, 'data': pluviometros, 'columnacolor': 0, 'hidden': [0, 9]}
        return None

    def datos_tabla_cotas_terreno(proyecto_id, idzona, equipos, decimales):
        cotas = [dato[2] for dato in equipos]
        terrenos = DatosController.ctrlObtenerCotasTerreno(proyecto_id, idzona, cotas, decimales)
        if terrenos:
            headers = ["", "Nombre Cota", "Fecha Hora", "Cota (msnm)", "Observación", "Estado", ""]
            return {'headers': headers, 'data': terrenos, 'columnacolor': 0, 'hidden': [0, 6]}
        return None

    def datos_tabla_celdas_asentamiento(proyecto_id, idzona, equipos, decimales):
        asentamiento = [dato[2] for dato in equipos]
        celdas = DatosController.ctrlObtenerCeldasAsentamiento(proyecto_id, idzona, asentamiento, decimales)
        if celdas:
            headers = [
                "", "Celda", "Fecha Hora", "Frecuencia (Digits)", "Frecuencia (Hz)", "Temperatura (°C)",
                "Desplazamiento (m)", "Cota (msnm)", "Instalación (msnm)", "Rango", "Este (m)", "Norte (m)",
                "Fundación (msnm)", "Superficie (msnm)", "Estado", "Observación", ""
            ]
            return {'headers': headers, 'data': celdas, 'columnacolor': 14, 'hidden': [0, 16]}
        return None

    def datos_tabla_acelerografos(proyecto_id, idzona, equipos, decimales):
        acelero = [dato[2] for dato in equipos]
        acelerografos = DatosController.ctrlObtenerAcelerografos(proyecto_id, idzona, acelero, decimales)
        if acelerografos:
            headers = [
                "", "Acelerógrafo", "Fecha Hora", "Magnitud", "Distancia (Km)",
                "Este (m)", "Norte (m)", "Elevación (msnm)", "Observacion", "Estado", ""
            ]
            return {'headers': headers, 'data': acelerografos, 'columnacolor': 9, 'hidden': [0, 10]}
        return None

    def datos_tabla_sondajestdr(proyecto_id, idzona, equipos, decimales):
        tdr = [dato[2] for dato in equipos]
        sondajestdr = DatosController.ctrlObtenerSondajestdr(proyecto_id, idzona, tdr, decimales)
        if sondajestdr:
            headers = [
                "", "TDR", "Fecha y Hora", "Profundidad (m)", "Impedancia", "Este (m)", "Norte (m)",
                "Elevación (msnm)", "Observación", ""
            ]
            return {'headers': headers, 'data': sondajestdr, 'columnacolor': 0, 'hidden': [0, 9]}
        return None

    def datos_tabla_equipos_adicionales(proyecto_id, idzona, equipos, decimales):
        adicionales = [dato[2] for dato in equipos]
        equiposdata = DatosController.ctrlObtenerEquiposAdicionales(proyecto_id, idzona, adicionales, decimales)
        if equiposdata:
            headers = [
                "", "Equipo", "Tipo Equipo", "Este (m)", "Norte (m)", "Elevación (msnm)", "Descripción", ""
            ]
            return {'headers': headers, 'data': equiposdata, 'columnacolor': 0, 'hidden': [0, 7]}
        return None
    
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