from PySide6.QtGui import QIntValidator, QStandardItemModel, QColor
from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex, QSortFilterProxyModel
from PySide6.QtWidgets import QTableView, QPushButton, QLineEdit
from utils.common.metodosGenerales import MetodosGenerales
from modules.empresa.softwareconfiguracion import SoftwareConfiguracion
from controllers. DatosController import DatosController
import warnings

# Clase CustomTableModel (permanece igual)
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
            
        total_pages = (len(self._data) + self.page_size - 1) // self.page_size
        if total_pages == 0:
            new_page = 0
        else:
            new_page = max(0, min(new_page, total_pages - 1))
        
        if new_page != self.current_page:
            self.current_page = new_page
            self.layoutChanged.emit()

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self._headers[section]
            elif orientation == Qt.Vertical:
                return str(section + 1 + self.current_page * self.page_size)
        return None
    
class VistaDatos:
    pagina_prisma, pagina_inclino, pagina_piezocuerda, pagina_piezomanual, pagina_pluvio,  = 0, 0, 0, 0, 0
    pagina_terreno, pagina_celda, pagina_acelero, pagina_tdr, pagina_equipo, pagina_prismabaja = 0, 0, 0, 0, 0, 0
    
    def reiniciarVariablesPagina():
        VistaDatos.pagina_prisma, VistaDatos.pagina_inclino, VistaDatos.pagina_piezocuerda = 0, 0, 0
        VistaDatos.pagina_piezomanual, VistaDatos.pagina_pluvio, VistaDatos.pagina_terreno  = 0, 0, 0
        VistaDatos.pagina_celda, VistaDatos.pagina_acelero, VistaDatos.pagina_tdr = 0, 0, 0
        VistaDatos.pagina_equipo, VistaDatos.pagina_prismabaja = 0, 0
    
    def mostrarTablaEquipo(proyecto_id, main, idzona, tipo, equipos, refrescar):
        if refrescar is False:
            VistaDatos.reiniciarVariablesPagina()
        tabla =  main.findChild(QTableView, "table_datos")
        if tipo == 'Prismas':
            VistaDatos.mostrar_tabla_prismas(proyecto_id, main, idzona, equipos, tabla, tipo, 1)
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
            VistaDatos.mostrar_tabla_prismas(proyecto_id, main, idzona, equipos, tabla, tipo, 0)

    def mostrar_tabla_prismas(proyecto_id, main, idzona, equipos, tablawidget, tipo, estado):
        dataprismasunido = []
        tipovelocidad = 1
        respuesta = SoftwareConfiguracion.obtenerDataSoftware()
        if respuesta:
            tipovelocidad = respuesta[15]
        resultado = MetodosGenerales.ctrlAgruparPrismasSegunTipo(equipos)
        for tabla, prismas in resultado.items():
            prismasdata = DatosController.ctrlObtenerDataPrismasMarcados(proyecto_id, tabla, idzona, prismas, tipovelocidad, estado)
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
        inclino = [dato[2] for dato in equipos]
        inclinometros = DatosController.ctrlObtenerInclinometros(proyecto_id, idzona, inclino)
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
        cuerdas = [dato[2] for dato in equipos]
        piezometros = DatosController.ctrlObtenerPiezometrosCuerda(proyecto_id, idzona, cuerdas)
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
        manuales = [dato[2] for dato in equipos]
        piezometros = DatosController.ctrlObtenerPiezometrosManuales(proyecto_id, idzona, manuales)
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
        lluvias = [dato[2] for dato in equipos]
        pluviometros = DatosController.ctrlObtenerPluviometros(proyecto_id, idzona, lluvias)
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
        cotas = [dato[2] for dato in equipos]
        terrenos = DatosController.ctrlObtenerCotasTerreno(proyecto_id, idzona, cotas)
        if terrenos:
            headers = [ "", "Nombre Cota", "Fecha Hora", "Cota (msnm)", "Observación", ""]
            VistaDatos.llenarTabla(tabla, headers, terrenos, main, tipo)
            tabla.setColumnHidden(0, True)
            tabla.setColumnHidden(5, True)
        else:
            VistaDatos.limpiarTablaDatos(tabla)
    
    def mostrar_tabla_celdas_asentamiento(proyecto_id, main, idzona, equipos, tabla, tipo):
        asentamiento = [dato[2] for dato in equipos]
        celdas = DatosController.ctrlObtenerCeldasAsentamiento(proyecto_id, idzona, asentamiento)
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
        acelero = [dato[2] for dato in equipos]
        acelerografos = DatosController.ctrlObtenerAcelerografos(proyecto_id, idzona, acelero)
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
        tdr = [dato[2] for dato in equipos]
        sondajestdr = DatosController.ctrlObtenerSondajestdr(proyecto_id, idzona, tdr)
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
        adicionales = [dato[2] for dato in equipos]
        equipos = DatosController.ctrlObtenerEquiposAdicionales(proyecto_id, idzona, adicionales)
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
        # Solo permitir números si el input existe
        if input_pagina_salto:
            input_pagina_salto.setValidator(QIntValidator(1, 2147483647))
        # Obtener la página actual para este tipo específico
        pagina_actual = getattr(VistaDatos, f'pagina_{tipo.lower()}', 1)
        # Calcular el número total de páginas
        total_rows = len(data)
        page_size = model.page_size
        total_pages = max(1, (total_rows + page_size - 1) // page_size)
        # Asegurar que la página actual esté dentro del rango válido
        pagina_actual = max(1, min(pagina_actual, total_pages))
        # Cambiar a la página guardada para este tipo
        model.change_page(pagina_actual - 1)
        # Actualizar el input solo si existe
        if input_pagina_salto:
            input_pagina_salto.setText(str(pagina_actual))
        # Actualizar el valor del QLineEdit cuando se cambie de página
        def update_input_pagina():
            if input_pagina_salto:
                current_page = model.current_page + 1
                input_pagina_salto.setText(str(current_page))
        def safe_disconnect(obj, signal_name):
            """Desconecta señales de forma segura, manejando objetos None y excepciones."""
            if obj is None:
                return
            try:
                signal = getattr(obj, signal_name, None)
                if signal is not None:
                    # Redirigir las advertencias para capturarlas como excepciones
                    with warnings.catch_warnings():
                        warnings.simplefilter("error")
                        try:
                            signal.disconnect()
                        except RuntimeWarning:
                            pass  # No había conexiones
                        except TypeError:
                            pass  # No había conexiones
            except Exception as e:
                pass

        # Lista de controles y sus señales a desconectar
        controls_to_disconnect = [
            (btn_pagina_inicio, 'clicked'),
            (btn_pagina_anterior, 'clicked'),
            (btn_pagina_siguiente, 'clicked'),
            (btn_pagina_final, 'clicked'),
            (input_pagina_salto, 'returnPressed')
        ]

        # Desconectar todas las señales de forma segura
        for control, signal_name in controls_to_disconnect:
            if control is not None:
                safe_disconnect(control, signal_name)

        # Conectar botones con funciones de paginación solo si existen
        if btn_pagina_inicio:
            btn_pagina_inicio.clicked.connect(
                lambda: [VistaDatos.first_page(model, tipo), update_input_pagina()])

        if btn_pagina_anterior:
            btn_pagina_anterior.clicked.connect(
                lambda: [VistaDatos.prev_page(model, tipo), update_input_pagina()])

        if btn_pagina_siguiente:
            btn_pagina_siguiente.clicked.connect(
                lambda: [VistaDatos.next_page(model, tipo), update_input_pagina()])

        if btn_pagina_final:
            btn_pagina_final.clicked.connect(
                lambda: [VistaDatos.last_page(model, tipo), update_input_pagina()])

        # Conectar el input para saltar a una página específica
        if input_pagina_salto:
            input_pagina_salto.returnPressed.connect(
                lambda: VistaDatos.jump_to_page(model, input_pagina_salto, tipo))

    def prev_page(model, tipo):
        current_page = model.current_page
        if current_page > 0:
            model.change_page(current_page - 1)
        else:
            model.change_page(0)

        setattr(VistaDatos, f"pagina_{tipo.lower()}", model.current_page + 1)

    def next_page(model, tipo):
        current_page = model.current_page
        total_rows = len(model._data)
        if (current_page + 1) * model.page_size < total_rows:
            model.change_page(current_page + 1)

        setattr(VistaDatos, f"pagina_{tipo.lower()}", model.current_page + 1)

    def first_page(model, tipo):
        model.change_page(0)
        setattr(VistaDatos, f"pagina_{tipo.lower()}", 1)

    def last_page(model, tipo):
        total_rows = len(model._data)
        last_page = (total_rows - 1) // model.page_size
        model.change_page(last_page)
        setattr(VistaDatos, f"pagina_{tipo.lower()}", last_page + 1)

    def jump_to_page(model, page_input, tipo):
        try:
            if page_input is None:
                return

            page_text = page_input.text().strip()
            if not page_text:
                return

            try:
                target_page = int(page_text)
            except ValueError:
                if hasattr(model, 'current_page') and page_input:
                    current = model.current_page + 1
                    page_input.setText(str(current))
                return

            if not hasattr(model, '_data') or not model._data:
                if page_input:
                    page_input.setText("1")
                return

            total_rows = len(model._data)
            page_size = model.page_size
            total_pages = max(1, (total_rows + page_size - 1) // page_size)

            target_page = max(1, min(target_page, total_pages))
            page_index = target_page - 1

            if page_index != model.current_page:
                model.change_page(page_index)
            setattr(VistaDatos, f"pagina_{tipo.lower()}", target_page)
            if page_input:
                page_input.setText(str(target_page))
        except Exception as e:
            if hasattr(model, 'current_page') and page_input:
                current = model.current_page + 1
                page_input.setText(str(current))
    
    def limpiarTablaDatos(tabla):
        model = QStandardItemModel()
        tabla.setModel(model)
        VistaDatos.reiniciarVariablesPagina()