from PySide6.QtGui import QIntValidator, QStandardItemModel, QColor
from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex, QSortFilterProxyModel
from PySide6.QtWidgets import QTableView, QPushButton, QLineEdit
from utils.common.metodosGenerales import MetodosGenerales
from modules.empresa.softwareconfiguracion import SoftwareConfiguracion
from controllers. DatosController import DatosController

# Clase CustomTableModel (permanece igual)
class CustomTableModel(QAbstractTableModel):
    def __init__(self, data, headers, page_size=100, columna_color=None, parent=None):
        super().__init__(parent)
        self._data = data
        self._headers = headers
        self.page_size = page_size
        self.current_page = 0  # Página actual
        self.columna_color = columna_color

    # Número de filas por página
    def rowCount(self, parent=QModelIndex()):
        return min(self.page_size, len(self._data) - self.current_page * self.page_size)

    # Número de columnas
    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)

    # Devuelve los datos de la celda solicitada
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row = index.row() + self.current_page * self.page_size
        col = index.column()
        if role == Qt.DisplayRole:
            return str(self._data[row][col])
        if self.columna_color:
            if role == Qt.ForegroundRole and col == self.columna_color:
                if str(self._data[row][col]) == "Omitido":
                    return QColor("blue")
        return None
    
    # Cambiar de página
    def change_page(self, new_page):
        if new_page * self.page_size < len(self._data) and new_page >= 0:
            self.current_page = new_page
            self.layoutChanged.emit()  # Notificar que los datos han cambiado y deben redibujarse

    # Encabezados de las columnas
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
            VistaDatos.mostrar_tabla_prismas(proyecto_id, main, idzona, equipos, tabla, tipo)
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
            VistaDatos.mostrar_tabla_prismas(proyecto_id, main, idzona, equipos, tabla, tipo)

    def mostrar_tabla_prismas(proyecto_id, main, idzona, equipos, tablawidget, tipo):
        dataprismasunido = []
        tipovelocidad = 1
        respuesta = SoftwareConfiguracion.obtenerDataSoftware()
        if respuesta:
            tipovelocidad = respuesta[15]
        resultado = MetodosGenerales.ctrlAgruparPrismasSegunTipo(equipos)
        for tabla, prismas in resultado.items():
            prismasdata = DatosController.ctrlObtenerDataPrismasMarcados(proyecto_id, tabla, idzona, prismas, tipovelocidad)
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
        
    # Función para insertar datos en el TableView
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
        # Volver a ocultar el indicador de ordenación si es posible
        header = tabla.horizontalHeader()
        if header:
            header.setSortIndicatorShown(False)
        # Reactivar la ordenación
        tabla.setSortingEnabled(True)
        # Ajustar automáticamente el tamaño de las columnas según el contenido
        tabla.resizeColumnsToContents()
        tabla.resizeRowsToContents()
        
        btn_pagina_inicio = main.findChild(QPushButton, "btn_pagina_inicio")
        btn_pagina_anterior = main.findChild(QPushButton, "btn_pagina_anterior")
        btn_pagina_siguiente = main.findChild(QPushButton, "btn_pagina_siguiente")
        btn_pagina_final = main.findChild(QPushButton, "btn_pagina_fin")
        input_pagina_salto = main.findChild(QLineEdit, "input_salto_pagina")
        
        # Solo permitir números
        input_pagina_salto.setValidator(QIntValidator(1, 2147483647))  # Limitar a números enteros positivos
        # ubicar la página actual
        if tipo == 'Prismas':
            if VistaDatos.pagina_prisma == 0:
                model.change_page(0)
                input_pagina_salto.setText("1")
            else:
                model.change_page(VistaDatos.pagina_prisma - 1)
                input_pagina_salto.setText(str(VistaDatos.pagina_prisma))
        elif tipo == 'Inclinómetros':
            if VistaDatos.pagina_inclino == 0:
                model.change_page(0)
                input_pagina_salto.setText("1")
            else:
                model.change_page(VistaDatos.pagina_inclino - 1)
                input_pagina_salto.setText(str(VistaDatos.pagina_inclino))
        elif tipo == 'Piezómetros Cuerda Vibrante':
            if VistaDatos.pagina_piezocuerda == 0:
                model.change_page(0)
                input_pagina_salto.setText("1")
            else:
                model.change_page(VistaDatos.pagina_piezocuerda - 1)
                input_pagina_salto.setText(str(VistaDatos.pagina_piezocuerda))
        elif tipo == 'Piezómetros Casagrande':
            if VistaDatos.pagina_piezomanual == 0:
                model.change_page(0)
                input_pagina_salto.setText("1")
            else:
                model.change_page(VistaDatos.pagina_piezomanual - 1)
                input_pagina_salto.setText(str(VistaDatos.pagina_piezomanual))
        elif tipo == 'Pluviómetros':
            if VistaDatos.pagina_pluvio == 0:
                model.change_page(0)
                input_pagina_salto.setText("1")
            else:
                model.change_page(VistaDatos.pagina_pluvio - 1)
                input_pagina_salto.setText(str(VistaDatos.pagina_pluvio))
        elif tipo == 'Cotas de Terreno':
            if VistaDatos.pagina_terreno == 0:
                model.change_page(0)
                input_pagina_salto.setText("1")
            else:
                model.change_page(VistaDatos.pagina_terreno - 1)
                input_pagina_salto.setText(str(VistaDatos.pagina_terreno))
        elif tipo == 'Celdas de Asentamiento':
            if VistaDatos.pagina_celda == 0:
                model.change_page(0)
                input_pagina_salto.setText("1")
            else:
                model.change_page(VistaDatos.pagina_celda - 1)
                input_pagina_salto.setText(str(VistaDatos.pagina_celda))
        elif tipo == 'Acelerógrafos':
            if VistaDatos.pagina_acelero == 0:
                model.change_page(0)
                input_pagina_salto.setText("1")
            else:
                model.change_page(VistaDatos.pagina_acelero - 1)
                input_pagina_salto.setText(str(VistaDatos.pagina_acelero))
        elif tipo == 'TDR':
            if VistaDatos.pagina_tdr == 0:
                model.change_page(0)
                input_pagina_salto.setText("1")
            else:
                model.change_page(VistaDatos.pagina_tdr - 1)
                input_pagina_salto.setText(str(VistaDatos.pagina_tdr))
        elif tipo == 'Equipos Adicionales':
            if VistaDatos.pagina_equipo == 0:
                model.change_page(0)
                input_pagina_salto.setText("1")
            else:
                model.change_page(VistaDatos.pagina_equipo - 1)
                input_pagina_salto.setText(str(VistaDatos.pagina_equipo))
        elif tipo == 'Prismas de Baja':
            if VistaDatos.pagina_prismabaja == 0:
                model.change_page(0)
                input_pagina_salto.setText("1")
            else:
                model.change_page(VistaDatos.pagina_prismabaja - 1)
                input_pagina_salto.setText(str(VistaDatos.pagina_prismabaja))
        # Actualizar el valor del QLineEdit cuando se cambie de página
        def update_input_pagina():
            current_page = model.current_page + 1
            input_pagina_salto.setText(str(current_page))
        
        # Conecta los botones con las funciones de paginación y actualiza el input_pagina_salto
        btn_pagina_inicio.clicked.connect(lambda: [VistaDatos.first_page(model, tipo), update_input_pagina()])
        btn_pagina_anterior.clicked.connect(lambda: [VistaDatos.prev_page(model, tipo), update_input_pagina()])
        btn_pagina_siguiente.clicked.connect(lambda: [VistaDatos.next_page(model, tipo), update_input_pagina()])
        btn_pagina_final.clicked.connect(lambda: [VistaDatos.last_page(model, tipo), update_input_pagina()])
        # Conectar el input para saltar a una página específica y actualizar el valor en QLineEdit
        input_pagina_salto.returnPressed.connect(lambda: [VistaDatos.jump_to_page(model, input_pagina_salto), update_input_pagina()])
        #update_input_pagina()
    
    # Función para ir a la página anterior
    def prev_page(model, tipo):
        current_page = model.current_page
        if current_page > 0:
            model.change_page(current_page - 1)
            if tipo == 'Prismas':
                VistaDatos.pagina_prisma = current_page
            elif tipo == 'Inclinómetros':
                VistaDatos.pagina_inclino = current_page
            elif tipo == 'Piezómetros Cuerda Vibrante':
                VistaDatos.pagina_piezocuerda = current_page
            elif tipo == 'Piezómetros Casagrande':
                VistaDatos.pagina_piezomanual = current_page
            elif tipo == 'Pluviómetros':
                VistaDatos.pagina_pluvio = current_page
            elif tipo == 'Cotas de Terreno':
                VistaDatos.pagina_terreno = current_page
            elif tipo == 'Celdas de Asentamiento':
                VistaDatos.pagina_celda = current_page
            elif tipo == 'Acelerógrafos':
                VistaDatos.pagina_acelero = current_page
            elif tipo == 'TDR':
                VistaDatos.pagina_tdr = current_page
            elif tipo == 'Equipos Adicionales':
                VistaDatos.pagina_equipo = current_page
            elif tipo == 'Prismas de Baja':
                VistaDatos.pagina_prismabaja = current_page
        else:
            model.change_page(0)
            if tipo == 'Prismas':
                VistaDatos.pagina_prisma = 0
            elif tipo == 'Inclinómetros':
                VistaDatos.pagina_inclino = 0
            elif tipo == 'Piezómetros Cuerda Vibrante':
                VistaDatos.pagina_piezocuerda = 0
            elif tipo == 'Piezómetros Casagrande':
                VistaDatos.pagina_piezomanual = 0
            elif tipo == 'Pluviómetros':
                VistaDatos.pagina_pluvio = 0
            elif tipo == 'Cotas de Terreno':
                VistaDatos.pagina_terreno = 0
            elif tipo == 'Celdas de Asentamiento':
                VistaDatos.pagina_celda = 0
            elif tipo == 'Acelerógrafos':
                VistaDatos.pagina_acelero = 0
            elif tipo == 'TDR':
                VistaDatos.pagina_tdr = 0
            elif tipo == 'Equipos Adicionales':
                VistaDatos.pagina_equipo = 0
            elif tipo == 'Prismas de Baja':
                VistaDatos.pagina_prismabaja = 0

    # Función para ir a la siguiente página
    def next_page(model, tipo):
        current_page = model.current_page
        total_rows = len(model._data)
        if (current_page + 1) * model.page_size < total_rows:
            model.change_page(current_page + 1)
            if tipo == 'Prismas':
                VistaDatos.pagina_prisma = current_page + 2
            elif tipo == 'Inclinómetros':
                VistaDatos.pagina_inclino = current_page + 2
            elif tipo == 'Piezómetros Cuerda Vibrante':
                VistaDatos.pagina_piezocuerda = current_page + 2
            elif tipo == 'Piezómetros Casagrande':
                VistaDatos.pagina_piezomanual = current_page + 2
            elif tipo == 'Pluviómetros':
                VistaDatos.pagina_pluvio = current_page + 2
            elif tipo == 'Cotas de Terreno':
                VistaDatos.pagina_terreno = current_page + 2
            elif tipo == 'Celdas de Asentamiento':
                VistaDatos.pagina_celda = current_page + 2
            elif tipo == 'Acelerógrafos':
                VistaDatos.pagina_acelero = current_page + 2
            elif tipo == 'TDR':
                VistaDatos.pagina_tdr = current_page + 2
            elif tipo == 'Equipos Adicionales':
                VistaDatos.pagina_equipo = current_page + 2
            elif tipo == 'Prismas de Baja':
                VistaDatos.pagina_prismabaja = current_page + 2
    
    # Función para ir a la primera página
    def first_page(model, tipo):
        model.change_page(0)
        if tipo == 'Prismas':
            VistaDatos.pagina_prisma = 0
        elif tipo == 'Inclinómetros':
            VistaDatos.pagina_inclino = 0
        elif tipo == 'Piezómetros Cuerda Vibrante':
            VistaDatos.pagina_piezocuerda = 0
        elif tipo == 'Piezómetros Casagrande':
            VistaDatos.pagina_piezomanual = 0
        elif tipo == 'Pluviómetros':
            VistaDatos.pagina_pluvio = 0
        elif tipo == 'Cotas de Terreno':
            VistaDatos.pagina_terreno = 0
        elif tipo == 'Celdas de Asentamiento':
            VistaDatos.pagina_celda = 0
        elif tipo == 'Acelerógrafos':
            VistaDatos.pagina_acelero = 0
        elif tipo == 'TDR':
            VistaDatos.pagina_tdr = 0
        elif tipo == 'Equipos Adicionales':
            VistaDatos.pagina_equipo = 0
        elif tipo == 'Prismas de Baja':
            VistaDatos.pagina_prismabaja = 0

    # Función para ir a la última página
    def last_page(model, tipo):
        total_rows = len(model._data)
        last_page = (total_rows - 1) // model.page_size
        model.change_page(last_page)
        if tipo == 'Prismas':
            VistaDatos.pagina_prisma = last_page + 1
        elif tipo == 'Inclinómetros':
            VistaDatos.pagina_inclino = last_page + 1
        elif tipo == 'Piezómetros Cuerda Vibrante':
            VistaDatos.pagina_piezocuerda = last_page + 1
        elif tipo == 'Piezómetros Casagrande':
            VistaDatos.pagina_piezomanual = last_page + 1
        elif tipo == 'Pluviómetros':
            VistaDatos.pagina_pluvio = last_page + 1
        elif tipo == 'Cotas de Terreno':
            VistaDatos.pagina_terreno = last_page + 1
        elif tipo == 'Celdas de Asentamiento':
            VistaDatos.pagina_celda = last_page + 1
        elif tipo == 'Acelerógrafos':
            VistaDatos.pagina_acelero = last_page + 1
        elif tipo == 'TDR':
            VistaDatos.pagina_tdr = last_page + 1
        elif tipo == 'Equipos Adicionales':
            VistaDatos.pagina_equipo = last_page + 1
        elif tipo == 'Prismas de Baja':
            VistaDatos.pagina_prismabaja = last_page + 1
    
    # Función para saltar a una página específica
    def jump_to_page(model, page_input):
        try:
            page_number = int(page_input.text()) - 1  # Las páginas empiezan en 0 en el modelo
            total_rows = len(model._data)
            last_page = (total_rows - 1) // model.page_size
            if 0 <= page_number <= last_page:
                model.change_page(page_number)
            else:
                print("Página fuera de rango.")
        except ValueError:
            print("Ingrese un número válido.")
    
    def limpiarTablaDatos(tabla):
        model = QStandardItemModel()
        tabla.setModel(model)
        VistaDatos.reiniciarVariablesPagina()
    