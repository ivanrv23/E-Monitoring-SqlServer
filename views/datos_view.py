from PySide6.QtWidgets import (QMenu, QTreeWidget, QPushButton, QTableView, QDialog, QFormLayout, QLineEdit, QDialogButtonBox,
                            QMessageBox, QLabel)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QDoubleValidator
from utils.common.alertas import mostrar_mensaje
from utils.common.metodosGenerales import MetodosGenerales
from modules.datos.equiposDatos import EquiposDatos
from modules.datos.vistaDatos import VistaDatos
from modules.data.exportardataequipos import ExportarData
from controllers.PrismaController import PrismaController
from controllers.InclinometroController import InclinometroController
from controllers.PiezometroController import PiezometroController
from controllers.PluviometroController import PluviometroController
from controllers.CeldaController import CeldaController
from controllers.AcelerografoController import AcelerografoController
from controllers.TDRController import TDRController
from controllers.TerrenoController import TerrenoController
from services.security.session import Session

class DatosView:
    main = None
    idproyecto = None
    nameproyecto = "SIN PROYECTO"
    estadochecklist = True
    estadoPagina = True
    
    def inicializarVistaDatos(main, proyectoid, proyectoname):
        DatosView.main = main
        DatosView.idproyecto = proyectoid
        DatosView.nameproyecto = proyectoname
        if DatosView.estadochecklist:
            tree_widget = DatosView.main.findChild(QTreeWidget, "tree_actual_datos")
            tree_widget.setHeaderLabels([DatosView.nameproyecto.upper()])
            EquiposDatos.inicializar_lista_datos(tree_widget, DatosView.idproyecto, DatosView.nameproyecto)
            DatosView.estadochecklist = False
        if DatosView.estadoPagina:
            tree_actual_datos =  DatosView.main.findChild(QTreeWidget, "tree_actual_datos")
            tree_actual_datos.itemClicked.connect(DatosView.checkProyectoActualDatos)
            btn_refrescar_tabla = DatosView.main.findChild(QPushButton, "btn_refrescar_tabla_datos")
            btn_refrescar_tabla.clicked.connect(lambda: DatosView.obtenerEquiposMarcados(True))
            tree_actual_datos.setContextMenuPolicy(Qt.CustomContextMenu)
            tree_actual_datos.customContextMenuRequested.connect(DatosView.clicderechoProyectoActualDatos)
            # Conectar el menú contextual al QTableView
            tabladatos =  main.findChild(QTableView, "table_datos")
            tabladatos.setContextMenuPolicy(Qt.CustomContextMenu)
            tabladatos.customContextMenuRequested.connect(lambda position: DatosView.mostrarMenuTabla(tabladatos, position))
            # Conectar el menú contextual al encabezado vertical
            vertical_header = tabladatos.verticalHeader()
            vertical_header.setContextMenuPolicy(Qt.CustomContextMenu)
            vertical_header.customContextMenuRequested.connect(lambda position: DatosView.mostrarMenuTabla(tabladatos, position))
            btnFormatos = DatosView.main.findChild(QPushButton, "btn_formatos")
            btnFormatos.clicked.connect(DatosView.descargarFormatosData)
            btn_exportar_data = DatosView.main.findChild(QPushButton, "btn_exportar_tabla_datos")
            btn_exportar_data.clicked.connect(DatosView.exportarDataEquiposMarcados)
            DatosView.estadoPagina = False

    def checkProyectoActualDatos(parent_item, column):
        treeWidget =  DatosView.main.findChild(QTreeWidget, "tree_actual_datos")
        EquiposDatos.validarMarcadoCheckbox(parent_item, column, treeWidget, DatosView.obtenerEquiposMarcados)
        
    def clicderechoProyectoActualDatos(point):
        treeWidget =  DatosView.main.findChild(QTreeWidget, "tree_actual_datos")
        EquiposDatos.validarOpcionesMenuCheckbox(point, DatosView.main, treeWidget, DatosView.reiniciarVistasAfectadas)
    
    def reiniciarVistasAfectadas(tipoequipo="Todos"):
        from views.visor_view import VisorView
        from views.desplazamiento_view import DesplazamientoView
        from views.velocidad_view import VelocidadView
        from views.inclinometros_view import InclinometrosView
        from views.piezometros_view import PiezometrosView
        from views.celdas_view import CeldasView
        from views.acelerografos_view import AcelerografosView
        from views.sondajestdr_view import SondajetdrView
        from views.analisis_view import AnalisisView
        if tipoequipo == "Prisma":
            VisorView.reiniciarVistaVisor(DatosView.main, DatosView.idproyecto, DatosView.nameproyecto)
            DesplazamientoView.reiniciarVistaDesplazamiento(DatosView.main, DatosView.idproyecto, DatosView.nameproyecto)
            VelocidadView.reiniciarVistaVelocidad(DatosView.main, DatosView.idproyecto, DatosView.nameproyecto)
            AnalisisView.reiniciarVistaAnalisis(DatosView.main, DatosView.idproyecto, DatosView.nameproyecto)
        elif tipoequipo == "Inclinómetro":
            VisorView.reiniciarVistaVisor(DatosView.main, DatosView.idproyecto, DatosView.nameproyecto)
            InclinometrosView.reiniciarVistaInclinometros(DatosView.main, DatosView.idproyecto, DatosView.nameproyecto)
        elif tipoequipo == "Piezómetro":
            VisorView.reiniciarVistaVisor(DatosView.main, DatosView.idproyecto, DatosView.nameproyecto)
            PiezometrosView.reiniciarVistaPiezometros(DatosView.main, DatosView.idproyecto, DatosView.nameproyecto)
        elif tipoequipo == "Pluviómetro":
            VisorView.reiniciarVistaVisor(DatosView.main, DatosView.idproyecto, DatosView.nameproyecto)
            VelocidadView.reiniciarVistaVelocidad(DatosView.main, DatosView.idproyecto, DatosView.nameproyecto)
            PiezometrosView.reiniciarVistaPiezometros(DatosView.main, DatosView.idproyecto, DatosView.nameproyecto)
        elif tipoequipo == "Cotaterreno":
            PiezometrosView.reiniciarVistaPiezometros(DatosView.main, DatosView.idproyecto, DatosView.nameproyecto)
        elif tipoequipo == "Celda":
            VisorView.reiniciarVistaVisor(DatosView.main, DatosView.idproyecto, DatosView.nameproyecto)
            CeldasView.reiniciarVistaCeldas(DatosView.main, DatosView.idproyecto, DatosView.nameproyecto)
        elif tipoequipo == "Acelerógrafo":
            VisorView.reiniciarVistaVisor(DatosView.main, DatosView.idproyecto, DatosView.nameproyecto)
            AcelerografosView.reiniciarVistaAcelerografos(DatosView.main, DatosView.idproyecto, DatosView.nameproyecto)
        elif tipoequipo == "TDR":
            VisorView.reiniciarVistaVisor(DatosView.main, DatosView.idproyecto, DatosView.nameproyecto)
            SondajetdrView.reiniciarVistaTDR(DatosView.main, DatosView.idproyecto, DatosView.nameproyecto)
        elif tipoequipo == "Adicional":
            VisorView.reiniciarVistaVisor(DatosView.main, DatosView.idproyecto, DatosView.nameproyecto)
        else:
            VisorView.reiniciarVistaVisor(DatosView.main, DatosView.idproyecto, DatosView.nameproyecto)
            DesplazamientoView.reiniciarVistaDesplazamiento(DatosView.main, DatosView.idproyecto, DatosView.nameproyecto)
            VelocidadView.reiniciarVistaVelocidad(DatosView.main, DatosView.idproyecto, DatosView.nameproyecto)
            InclinometrosView.reiniciarVistaInclinometros(DatosView.main, DatosView.idproyecto, DatosView.nameproyecto)
            PiezometrosView.reiniciarVistaPiezometros(DatosView.main, DatosView.idproyecto, DatosView.nameproyecto)
            CeldasView.reiniciarVistaCeldas(DatosView.main, DatosView.idproyecto, DatosView.nameproyecto)
            AcelerografosView.reiniciarVistaAcelerografos(DatosView.main, DatosView.idproyecto, DatosView.nameproyecto)
            SondajetdrView.reiniciarVistaTDR(DatosView.main, DatosView.idproyecto, DatosView.nameproyecto)
            AnalisisView.reiniciarVistaAnalisis(DatosView.main, DatosView.idproyecto, DatosView.nameproyecto)
    
    def obtenerEquiposMarcados(refrescar=False):
        treeWidget_lista_checks_datos = DatosView.main.findChild(QTreeWidget, "tree_actual_datos")
        lista = EquiposDatos.obtener_todos_elementos_marcados(treeWidget_lista_checks_datos)
        if lista:
            zona = list(lista.keys())[0]
            tipoequipos = lista.get(zona)
            tipito = list(tipoequipos.keys())[0]
            equipos = tipoequipos.get(tipito)
            idzona = zona[1]
            tipo = tipito[0]
            VistaDatos.mostrarTablaEquipo(DatosView.idproyecto, DatosView.main, idzona, tipo, equipos, refrescar)
        else:
            tabla =  DatosView.main.findChild(QTableView, "table_datos")
            VistaDatos.limpiarTablaDatos(tabla)
    
    def descargarFormatosData():
        dialog = QDialog()
        dialog.setWindowTitle("Descargar Formato")
        layout = QFormLayout(dialog)
        # Título
        tituloLabel = QLabel()
        tituloLabel.setText("Elija el formato a descargar:")
        # Prismas
        btnPrismas = QPushButton()
        btnPrismas.setText("Prismas")
        # Piezómetros Cuerda
        btnPiezocuerda = QPushButton()
        btnPiezocuerda.setText("Piezómetros Cuerda Vibrante")
        # Piezómetros Manual
        btnPiezomanual = QPushButton()
        btnPiezomanual.setText("Piezómetros Casagrande")
        # Piezómetros Manual
        btnCeldas = QPushButton()
        btnCeldas.setText("Celdas")
        # Pluviometros
        btnPluviometro = QPushButton()
        btnPluviometro.setText("Pluviómetros")
        # Cotas de Terreno
        btnCotas = QPushButton()
        btnCotas.setText("Cotas de Terreno")
        # Sondajes tdr
        btnSondajes = QPushButton()
        btnSondajes.setText("TDR")
        # Acelerografos
        btnAcelerografo = QPushButton()
        btnAcelerografo.setText("Acelerógrafos")
        # Añadir los campos al layout
        tituloLabel.setAlignment(Qt.AlignCenter)
        layout.addRow(tituloLabel)
        layout.addRow(btnPrismas, btnPiezocuerda)
        layout.addRow(btnCeldas, btnPiezomanual)
        layout.addRow(btnPluviometro, btnCotas)
        layout.addRow(btnSondajes, btnAcelerografo)
        # Conectar los botones a las funciones correspondientes
        btnPrismas.clicked.connect(lambda: ExportarData.descargarFormatoExcel("prisma"))
        btnPiezocuerda.clicked.connect(lambda: ExportarData.descargarFormatoExcel("cuerda"))
        btnPiezomanual.clicked.connect(lambda: ExportarData.descargarFormatoExcel("casagrande"))
        btnCeldas.clicked.connect(lambda: ExportarData.descargarFormatoExcel("celda"))
        btnPluviometro.clicked.connect(lambda: ExportarData.descargarFormatoExcel("pluvio"))
        btnCotas.clicked.connect(lambda: ExportarData.descargarFormatoExcel("cota"))
        btnSondajes.clicked.connect(lambda: ExportarData.descargarFormatoExcel("sondaje"))
        btnAcelerografo.clicked.connect(lambda: ExportarData.descargarFormatoExcel("acelero"))
        # Mostrar el diálogo
        dialog.setLayout(layout)
        dialog.exec()
    
    def exportarDataEquiposMarcados():
        treeWidget_lista_checks_datos =  DatosView.main.findChild(QTreeWidget, "tree_actual_datos")
        lista = EquiposDatos.obtener_todos_elementos_marcados(treeWidget_lista_checks_datos)
        if lista:
            zona = list(lista.keys())[0]
            tipoequipos = lista.get(zona)
            tipito = list(tipoequipos.keys())[0]
            equipos = tipoequipos.get(tipito)
            idzona = zona[1]
            tipo = tipito[0]
            if equipos:
                fechainicial, fechafinal = None, None
                if tipo == "Prismas":
                    fechainicial, fechafinal = PrismaController.ctrlObtenerFechasRango(DatosView.idproyecto)
                elif tipo == "Piezómetros Cuerda Vibrante":
                    fechainicial, fechafinal = PiezometroController.ctrlObtenerFechasRangoPiezometrosCuerda(DatosView.idproyecto)
                elif tipo == "Piezómetros Casagrande":
                    fechainicial, fechafinal = PiezometroController.ctrlObtenerFechasRangoPiezometrosManual(DatosView.idproyecto)
                elif tipo == "Celdas de Asentamiento":
                    fechainicial, fechafinal = CeldaController.ctrlObtenerFechasRango(DatosView.idproyecto)
                elif tipo == "Acelerógrafos":
                    fechainicial, fechafinal = AcelerografoController.ctrlObtenerFechasRango(DatosView.idproyecto)
                if fechainicial and fechafinal:
                    ExportarData.validarExportarDataEquipos(DatosView.idproyecto, DatosView.nameproyecto, idzona, tipo, equipos, fechainicial, fechafinal)
                else:
                    if tipo == "Inclinómetros" or tipo == "Pluviómetros" or tipo == "TDR" or tipo == "Cotas de Terreno":
                        ExportarData.validarExportarDataEquipos(DatosView.idproyecto, DatosView.nameproyecto, idzona, tipo, equipos)
    
    def reiniciarVistaDatos(main, proyecto_id, proyecto_name):
        DatosView.main = main
        DatosView.idproyecto = proyecto_id
        DatosView.nameproyecto = proyecto_name
        DatosView.estadochecklist = True
        tabla =  DatosView.main.findChild(QTableView, "table_datos")
        VistaDatos.limpiarTablaDatos(tabla)
    
    # Función para manejar el menú contextual
    def mostrarMenuTabla(table, position):
        if Session.is_authenticated() and Session.get_idrole() != 3:
            index = table.indexAt(position)
            if not index.isValid():
                # Si el índice no es válido, intenta obtener la fila desde el encabezado vertical
                vertical_header = table.verticalHeader()
                row = vertical_header.logicalIndexAt(position.x(), position.y())
                if row >= 0:
                    index = table.model().index(row, 0)
                else:
                    return
            row = index.row()
            # Capturar los valores de la fila
            tipo = table.model().data(table.model().index(row, 0), Qt.DisplayRole)
            if tipo == 'PRISMAS':
                nombre = table.model().data(table.model().index(row, 1), Qt.DisplayRole)
                fecha = table.model().data(table.model().index(row, 2), Qt.DisplayRole)
                este = table.model().data(table.model().index(row, 3), Qt.DisplayRole)
                norte = table.model().data(table.model().index(row, 4), Qt.DisplayRole)
                nivel = table.model().data(table.model().index(row, 5), Qt.DisplayRole)
                distancia = table.model().data(table.model().index(row, 6), Qt.DisplayRole)
                iddetalle = table.model().data(table.model().index(row, 14), Qt.DisplayRole)
                tablasql = f"prismas{DatosView.idproyecto}"
                DatosView.generarMenuTablaPrismas(position, table, nombre, fecha, este, norte, nivel, distancia, iddetalle, tablasql)
            elif tipo == 'INCLINOMETRO':
                nombre = table.model().data(table.model().index(row, 1), Qt.DisplayRole)
                tipo = table.model().data(table.model().index(row, 2), Qt.DisplayRole)
                fecha = table.model().data(table.model().index(row, 3), Qt.DisplayRole)
                profun = table.model().data(table.model().index(row, 4), Qt.DisplayRole)
                apositivo = table.model().data(table.model().index(row, 5), Qt.DisplayRole)
                anegativo = table.model().data(table.model().index(row, 6), Qt.DisplayRole)
                bpositivo = table.model().data(table.model().index(row, 7), Qt.DisplayRole)
                bnegativo = table.model().data(table.model().index(row, 8), Qt.DisplayRole)
                iddetalle = table.model().data(table.model().index(row, 12), Qt.DisplayRole)
                tablasql = f"inclinometro_detalle{DatosView.idproyecto}"
                DatosView.generarMenuTablaInclinometros(position, table, nombre, tipo, fecha, profun, apositivo, anegativo, bpositivo, bnegativo, iddetalle, tablasql)
            elif tipo == 'PIEZOMETROCUERDA':
                nombre = table.model().data(table.model().index(row, 1), Qt.DisplayRole)
                fecha = table.model().data(table.model().index(row, 2), Qt.DisplayRole)
                frecuencia = table.model().data(table.model().index(row, 3), Qt.DisplayRole)
                temperatura = table.model().data(table.model().index(row, 4), Qt.DisplayRole)
                presion = table.model().data(table.model().index(row, 5), Qt.DisplayRole)
                medida = table.model().data(table.model().index(row, 6), Qt.DisplayRole)
                cota = table.model().data(table.model().index(row, 11), Qt.DisplayRole)
                observa = table.model().data(table.model().index(row, 14), Qt.DisplayRole)
                iddetalle = table.model().data(table.model().index(row, 15), Qt.DisplayRole)
                idcota = table.model().data(table.model().index(row, 16), Qt.DisplayRole)
                tablasql = f"piezometrocuerda_detalle{DatosView.idproyecto}"
                DatosView.generarMenuTablaPiezometrosCuerda(position, table, nombre, fecha, frecuencia, temperatura, presion, medida, observa, iddetalle, idcota, cota, tablasql)
            elif tipo == 'PIEZOMETROMANUAL':
                nombre = table.model().data(table.model().index(row, 1), Qt.DisplayRole)
                fecha = table.model().data(table.model().index(row, 2), Qt.DisplayRole)
                medida = table.model().data(table.model().index(row, 3), Qt.DisplayRole)
                cota = table.model().data(table.model().index(row, 5), Qt.DisplayRole)
                observa = table.model().data(table.model().index(row, 13), Qt.DisplayRole)
                iddetalle = table.model().data(table.model().index(row, 14), Qt.DisplayRole)
                idcota = table.model().data(table.model().index(row, 15), Qt.DisplayRole)
                tablasql = f"piezometromanual_detalle{DatosView.idproyecto}"
                DatosView.generarMenuTablaPiezometrosManual(position, table, nombre, fecha, medida, observa, iddetalle, idcota, cota, tablasql)
            elif tipo == 'PLUVIOMETRO':
                nombre = table.model().data(table.model().index(row, 1), Qt.DisplayRole)
                fecha = table.model().data(table.model().index(row, 2), Qt.DisplayRole)
                medida = table.model().data(table.model().index(row, 3), Qt.DisplayRole)
                observa = table.model().data(table.model().index(row, 7), Qt.DisplayRole)
                iddetalle = table.model().data(table.model().index(row, 8), Qt.DisplayRole)
                tablasql = f"pluviometro_detalle{DatosView.idproyecto}"
                DatosView.generarMenuTablaPluviometros(position, table, nombre, fecha, medida, observa, iddetalle, tablasql)
            elif tipo == 'COTATERRENO':
                nombre = table.model().data(table.model().index(row, 1), Qt.DisplayRole)
                fecha = table.model().data(table.model().index(row, 2), Qt.DisplayRole)
                cota = table.model().data(table.model().index(row, 3), Qt.DisplayRole)
                observa = table.model().data(table.model().index(row, 4), Qt.DisplayRole)
                iddetalle = table.model().data(table.model().index(row, 5), Qt.DisplayRole)
                tablasql = f"cotaterreno_detalle{DatosView.idproyecto}"
                DatosView.generarMenuTablaCotaTerreno(position, table, nombre, fecha, cota, observa, iddetalle, tablasql)
            elif tipo == 'CELDA':
                nombre = table.model().data(table.model().index(row, 1), Qt.DisplayRole)
                fecha = table.model().data(table.model().index(row, 2), Qt.DisplayRole)
                frecuendigi = table.model().data(table.model().index(row, 3), Qt.DisplayRole)
                frecuencihz = table.model().data(table.model().index(row, 4), Qt.DisplayRole)
                temperatura = table.model().data(table.model().index(row, 5), Qt.DisplayRole)
                desplaza = table.model().data(table.model().index(row, 6), Qt.DisplayRole)
                observa = table.model().data(table.model().index(row, 15), Qt.DisplayRole)
                iddetalle = table.model().data(table.model().index(row, 16), Qt.DisplayRole)
                tablasql = f"celda_detalle{DatosView.idproyecto}"
                DatosView.generarMenuTablaCeldas(position, table, nombre, fecha, frecuendigi, frecuencihz, temperatura, desplaza, observa, iddetalle, tablasql)
            elif tipo == 'ACELEROGRAFO':
                nombre = table.model().data(table.model().index(row, 1), Qt.DisplayRole)
                fecha = table.model().data(table.model().index(row, 2), Qt.DisplayRole)
                magnitud = table.model().data(table.model().index(row, 3), Qt.DisplayRole)
                distancia = table.model().data(table.model().index(row, 4), Qt.DisplayRole)
                observa = table.model().data(table.model().index(row, 8), Qt.DisplayRole)
                iddetalle = table.model().data(table.model().index(row, 9), Qt.DisplayRole)
                tablasql = f"acelerografo_detalle{DatosView.idproyecto}"
                DatosView.generarMenuTablaAcelerografos(position, table, nombre, fecha, magnitud, distancia, observa, iddetalle, tablasql)
            elif tipo == 'TDR':
                nombre = table.model().data(table.model().index(row, 1), Qt.DisplayRole)
                fecha = table.model().data(table.model().index(row, 2), Qt.DisplayRole)
                medida = table.model().data(table.model().index(row, 3), Qt.DisplayRole)
                impedancia = table.model().data(table.model().index(row, 4), Qt.DisplayRole)
                observa = table.model().data(table.model().index(row, 8), Qt.DisplayRole)
                iddetalle = table.model().data(table.model().index(row, 9), Qt.DisplayRole)
                tablasql = f"sondajetdr_detalle{DatosView.idproyecto}"
                DatosView.generarMenuTablaSondajestdr(position, table, nombre, fecha, medida, impedancia, observa, iddetalle, tablasql)
        
    # MENU TABLA PRISMAS    
    def generarMenuTablaPrismas(position, table, nombre, fecha, este, norte, nivel, distancia, iddetalle, tablasql):
        # Crear menú contextual
        menu = QMenu()
        edit_action = QAction("Editar Lectura", table)
        hide_action = QAction("Omitir/incluir Lectura", table)
        delete_action = QAction("Eliminar Lectura", table)
        # Conectar las acciones con los valores de la fila
        edit_action.triggered.connect(lambda: DatosView.editarDatosLecturaPrismas(iddetalle, nombre, fecha, este, norte, nivel, distancia, tablasql))
        hide_action.triggered.connect(lambda: DatosView.hide_row_prismas(iddetalle, nombre, fecha, tablasql))
        delete_action.triggered.connect(lambda: DatosView.delete_row_prismas(iddetalle, nombre, fecha, tablasql))
        # Añadir las acciones al menú
        menu.addAction(edit_action)
        menu.addAction(hide_action)
        menu.addAction(delete_action)
        selected_indexes = table.selectionModel().selectedRows()
        if selected_indexes:
            omitir_action = QAction("Omitir/incluir en Bloque", table)
            eliminar_action = QAction("Eliminar en Bloque", table)
            omitir_action.triggered.connect(lambda: DatosView.omitir_mostrar_rows_prismas(table, selected_indexes, tablasql))
            eliminar_action.triggered.connect(lambda: DatosView.delete_rows_prismas(table, selected_indexes, tablasql))
            menu.addAction(omitir_action)
            menu.addAction(eliminar_action)
        # Mostrar menú contextual en la posición del clic
        menu.exec(table.viewport().mapToGlobal(position))
    
    def editarDatosLecturaPrismas(iddetalle, nombre, fecha, este, norte, nivel, distancia, tablasql):
        dialog = QDialog()
        dialog.setWindowTitle("Editar Lectura Prisma")
        validator = QDoubleValidator()
        layout = QFormLayout(dialog)
        # Campo nombre (readonly)
        nombre_input = QLineEdit()
        nombre_input.setText(nombre)
        nombre_input.setReadOnly(True)
        # Campo fecha (editable)
        fecha_input = QLineEdit()
        fecha_input.setText(fecha)
        # Campo este (editable)
        este_input = QLineEdit()
        este_input.setText(str(este))
        este_input.setValidator(validator)
        # Campo norte (editable)
        norte_input = QLineEdit()
        norte_input.setText(str(norte))
        norte_input.setValidator(validator)
        # Campo cota (editable)
        cota_input = QLineEdit()
        cota_input.setText(str(nivel))
        cota_input.setValidator(validator)
        # Campo distancia (editable)
        distan_input = QLineEdit()
        distan_input.setText(str(distancia))
        distan_input.setValidator(validator)
        # Añadir los campos al layout
        layout.addRow("Nombre:", nombre_input)
        layout.addRow("Fecha:", fecha_input)
        layout.addRow("Este (m):", este_input)
        layout.addRow("Norte (m):", norte_input)
        layout.addRow("Cota (msnm):", cota_input)
        layout.addRow("Distancia I. (m):", distan_input)
        label_mensaje = QLabel("")
        label_mensaje.setAlignment(Qt.AlignCenter)
        label_mensaje.setStyleSheet("QLabel { color: red; }")
        layout.addRow(label_mensaje)
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        # Cambiar los textos a español
        button_box.button(QDialogButtonBox.Save).setText("Guardar")
        button_box.button(QDialogButtonBox.Cancel).setText("Cancelar")
        layout.addWidget(button_box)
        # Conectar los botones a las funciones correspondientes
        def actualizarDatos():
            datofecha = fecha_input.text()
            respfecha = MetodosGenerales.validarFormatoFechaDatabase(datofecha)
            if respfecha:
                datoeste = este_input.text()
                datonorte = norte_input.text()
                datonivel = cota_input.text()
                datodistan = distan_input.text()
                username = Session.get_username()
                nombres = Session.get_nombres()
                if Session.is_authenticated() and DatosView.idproyecto and datoeste != "" and datonorte != "" and datonivel != "" and datodistan != "":
                    datanueva = [datofecha, datoeste, datonorte, datonivel, datodistan, iddetalle]
                    respuesta = PrismaController.ctrlActualizarLecturaPrisma(tablasql, datanueva, DatosView.idproyecto, username, nombres)
                    if respuesta:
                        dialog.reject()
                        DatosView.obtenerEquiposMarcados(True)
                    else:
                        label_mensaje.setText("Error al actualizar los datos.")
                else:
                    label_mensaje.setText("Los datos están vacíos.")
            else:
                label_mensaje.setText("El formato de fecha no es válido.")
        button_box.accepted.connect(actualizarDatos)
        button_box.rejected.connect(dialog.reject)
        # Mostrar el diálogo
        dialog.setLayout(layout)
        dialog.exec()
    
    def hide_row_prismas(iddetalle, nombre, fecha, tablasql):
        dlg = QMessageBox()
        dlg.setWindowTitle("Omitir Lectura Prisma")
        dlg.setText(f"¿Desea omitir/incluir la lectura del '{nombre}' con fecha '{fecha}'?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            respuesta = PrismaController.ctrlCambiarEstadoLecturaPrisma(tablasql, iddetalle)
            if respuesta:
                DatosView.obtenerEquiposMarcados(True)
            else:
                mostrar_mensaje("Estado Lectura", "No se pudo omitir/incluir la lectura.", "advertencia")
    
    def delete_row_prismas(iddetalle, nombre, fecha, tablasql):
        dlg = QMessageBox()
        dlg.setWindowTitle("Eliminar Lectura Prisma")
        dlg.setText(f"¿Desea eliminar la lectura del '{nombre}' con fecha '{fecha}'?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            username = Session.get_username()
            nombres = Session.get_nombres()
            if Session.is_authenticated() and DatosView.idproyecto:
                respuesta = PrismaController.ctrlEliminarLecturaPrisma(tablasql, iddetalle, DatosView.idproyecto, username, nombres)
                if respuesta:
                    DatosView.obtenerEquiposMarcados(True)
                else:
                    mostrar_mensaje("Eliminar Lectura", "No se pudo eliminar la lectura.", "advertencia")
    
    def omitir_mostrar_rows_prismas(table, selected_indexes, tablasql):
        dataomitir = []
        idomitir = []
        for index in selected_indexes:
            row = index.row()
            nombre = table.model().data(table.model().index(row, 1), Qt.DisplayRole)
            fecha = table.model().data(table.model().index(row, 2), Qt.DisplayRole)
            iddetalle = table.model().data(table.model().index(row, 14), Qt.DisplayRole)
            dataomitir.append((nombre, fecha, row))
            idomitir.append((iddetalle))
        if len(idomitir) > 0:
            dlg = QMessageBox()
            dlg.setWindowTitle("Estado Lectura Prisma")
            dlg.setText(f"¿Desea omitir/incluir las lecturas '{dataomitir}'?")
            dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            dlg.setIcon(QMessageBox.Question)
            result = dlg.exec()
            if result == QMessageBox.Yes:
                respuesta = PrismaController.ctrlCambiarEstadoLecturaPrismaBloque(tablasql, idomitir)
                if respuesta:
                    DatosView.obtenerEquiposMarcados(True)
                else:
                    mostrar_mensaje("Omitir Lecturas", "No se pudo omitir/incluir las lecturas.", "advertencia")
    
    def delete_rows_prismas(table, selected_indexes, tablasql):
        dataeliminar = []
        idseliminar = []
        for index in selected_indexes:
            row = index.row()
            nombre = table.model().data(table.model().index(row, 1), Qt.DisplayRole)
            fecha = table.model().data(table.model().index(row, 2), Qt.DisplayRole)
            iddetalle = table.model().data(table.model().index(row, 14), Qt.DisplayRole)
            dataeliminar.append((nombre, fecha, row))
            idseliminar.append((iddetalle))
        if len(idseliminar) > 0:
            dlg = QMessageBox()
            dlg.setWindowTitle("Eliminar Lecturas Prisma")
            dlg.setText(f"¿Desea eliminar las lecturas '{dataeliminar}'?")
            dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            dlg.setIcon(QMessageBox.Question)
            result = dlg.exec()
            if result == QMessageBox.Yes:
                username = Session.get_username()
                nombres = Session.get_nombres()
                if Session.is_authenticated() and DatosView.idproyecto:
                    respuesta = PrismaController.ctrlEliminarLecturasBloquePrisma(tablasql, idseliminar, DatosView.idproyecto, username, nombres)
                    if respuesta:
                        DatosView.obtenerEquiposMarcados(True)
                    else:
                        mostrar_mensaje("Eliminar Lecturas", "No se pudo eliminar las lecturas.", "advertencia")
    
    # MENU TABLA INCLINÓMETROS
    def generarMenuTablaInclinometros(position, table, nombre, tipo, fecha, profun, apositivo, anegativo, bpositivo, bnegativo, iddetalle, tablasql):
        # Crear menú contextual
        menu = QMenu()
        edit_action = QAction("Editar Lectura", table)
        # Conectar las acciones con los valores de la fila
        edit_action.triggered.connect(lambda: DatosView.editarDatosLecturaInclinometros(iddetalle, nombre, tipo, fecha, profun, apositivo, anegativo, bpositivo, bnegativo, tablasql))
        # Añadir las acciones al menú
        menu.addAction(edit_action)
        menu.exec(table.viewport().mapToGlobal(position))
    
    def editarDatosLecturaInclinometros(iddetalle, nombre, tipo, fecha, profun, apositivo, anegativo, bpositivo, bnegativo, tablasql):
        dialog = QDialog()
        dialog.setWindowTitle("Editar Lectura Inclinómetro")
        validator = QDoubleValidator()
        layout = QFormLayout(dialog)
        # Campo nombre (readonly)
        nombre_input = QLineEdit()
        nombre_input.setText(nombre)
        nombre_input.setReadOnly(True)
        # Campo tipo (readonly)
        tipo_input = QLineEdit()
        tipo_input.setText(tipo)
        tipo_input.setReadOnly(True)
        # Campo fecha (editable)
        fecha_input = QLineEdit()
        fecha_input.setText(fecha)
        fecha_input.setReadOnly(True)
        # Campo profundidad (readonly)
        profundidad_input = QLineEdit()
        profundidad_input.setText(profun)
        profundidad_input.setReadOnly(True)
        # Campo A+ (editable)
        apositivo_input = QLineEdit()
        apositivo_input.setText(str(apositivo))
        apositivo_input.setValidator(validator)
        # Campo A- (editable)
        anegativo_input = QLineEdit()
        anegativo_input.setText(str(anegativo))
        anegativo_input.setValidator(validator)
        # Campo B+ (editable)
        bpositivo_input = QLineEdit()
        bpositivo_input.setText(str(bpositivo))
        bpositivo_input.setValidator(validator)
        # Campo B- (editable)
        bnegativo_input = QLineEdit()
        bnegativo_input.setText(str(bnegativo))
        bnegativo_input.setValidator(validator)
        # Añadir los campos al layout
        layout.addRow("Nombre:", nombre_input)
        layout.addRow("Tipo:", tipo_input)
        layout.addRow("Fecha:", fecha_input)
        layout.addRow("Profundidad (m):", profundidad_input)
        layout.addRow("A+ (m):", apositivo_input)
        layout.addRow("A- (m):", anegativo_input)
        layout.addRow("B+ (m):", bpositivo_input)
        layout.addRow("B- (m):", bnegativo_input)
        label_mensaje = QLabel("")
        label_mensaje.setAlignment(Qt.AlignCenter)
        label_mensaje.setStyleSheet("QLabel { color: red; }")
        layout.addRow(label_mensaje)
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        # Cambiar los textos a español
        button_box.button(QDialogButtonBox.Save).setText("Guardar")
        button_box.button(QDialogButtonBox.Cancel).setText("Cancelar")
        layout.addWidget(button_box)
        # Conectar los botones a las funciones correspondientes
        def actualizarDatos():
            faceaposi = apositivo_input.text()
            faceanega = anegativo_input.text()
            facebposi = bpositivo_input.text()
            facebnega = bnegativo_input.text()
            username = Session.get_username()
            nombres = Session.get_nombres()
            if Session.is_authenticated() and DatosView.idproyecto and faceaposi != "" and faceanega != "" and facebposi != "" and facebnega != "":
                datanueva = [faceaposi, faceanega, facebposi, facebnega, iddetalle]
                respuesta = InclinometroController.ctrlActualizarLecturaInclinometro(tablasql, datanueva, DatosView.idproyecto, username, nombres)
                if respuesta:
                    dialog.reject()
                    DatosView.obtenerEquiposMarcados(True)
                else:
                    label_mensaje.setText("Error al actualizar los datos.")
            else:
                label_mensaje.setText("Los datos están vacíos.")
        button_box.accepted.connect(actualizarDatos)
        button_box.rejected.connect(dialog.reject)
        # Mostrar el diálogo
        dialog.setLayout(layout)
        dialog.exec()
    
    # MENU TABLA PIEZÓMETROS CUERDA
    def generarMenuTablaPiezometrosCuerda(position, table, nombre, fecha, frecuencia, temperatura, presion, medida, observa, iddetalle, idcota, cota, tablasql):
        # Crear menú contextual
        menu = QMenu()
        edit_action = QAction("Editar Lectura", table)
        update_action = QAction("Editar Cota Piezométrica", table)
        hide_action = QAction("Omitir/incluir Lectura", table)
        delete_action = QAction("Eliminar Lectura", table)
        # Conectar las acciones con los valores de la fila
        edit_action.triggered.connect(lambda: DatosView.editarDatosLecturaPiezometroCuerda(iddetalle, nombre, fecha, frecuencia, temperatura, presion, medida, observa, tablasql))
        update_action.triggered.connect(lambda: DatosView.editarCotaPiezometrica(idcota, nombre))
        hide_action.triggered.connect(lambda: DatosView.hide_row_piezometrocuerda(iddetalle, nombre, fecha, tablasql))
        delete_action.triggered.connect(lambda: DatosView.delete_row_piezometrocuerda(iddetalle, nombre, fecha, tablasql))
        # Añadir las acciones al menú
        menu.addAction(edit_action)
        menu.addAction(update_action)
        menu.addAction(hide_action)
        menu.addAction(delete_action)
        selected_indexes = table.selectionModel().selectedRows()
        if selected_indexes:
            omitir_action = QAction("Omitir/incluir en Bloque", table)
            eliminar_action = QAction("Eliminar en Bloque", table)
            omitir_action.triggered.connect(lambda: DatosView.omitir_rows_piezometrocuerda(table, selected_indexes, tablasql))
            eliminar_action.triggered.connect(lambda: DatosView.delete_rows_piezometrocuerda(table, selected_indexes, tablasql))
            menu.addAction(omitir_action)
            menu.addAction(eliminar_action)
        # Mostrar menú contextual en la posición del clic
        menu.exec(table.viewport().mapToGlobal(position))
    
    def editarDatosLecturaPiezometroCuerda(iddetalle, nombre, fecha, frecuencia, temperatura, presion, medida, observa, tablasql):
        dialog = QDialog()
        dialog.setWindowTitle("Editar Lectura Piezómetro")
        validator = QDoubleValidator()
        layout = QFormLayout(dialog)
        # Campo nombre (readonly)
        nombre_input = QLineEdit()
        nombre_input.setText(nombre)
        nombre_input.setReadOnly(True)
        # Campo fecha (editable)
        fecha_input = QLineEdit()
        fecha_input.setText(fecha)
        # Campo frecuencia (editable)
        frecuencia_input = QLineEdit()
        frecuencia_input.setText(str(frecuencia))
        frecuencia_input.setValidator(validator)
        # Campo temperatura (editable)
        temperatura_input = QLineEdit()
        temperatura_input.setText(str(temperatura))
        temperatura_input.setValidator(validator)
        # Campo presion (editable)
        presion_input = QLineEdit()
        presion_input.setText(str(presion))
        presion_input.setValidator(validator)
        # Campo medida mca (editable)
        medida_input = QLineEdit()
        medida_input.setText(str(medida))
        medida_input.setValidator(validator)
        # Campo medida observacion (editable)
        observa_input = QLineEdit()
        observa_input.setText(str(observa))
        # Añadir los campos al layout
        layout.addRow("Nombre:", nombre_input)
        layout.addRow("Fecha:", fecha_input)
        layout.addRow("Frecuencia:", frecuencia_input)
        layout.addRow("Temperatura:", temperatura_input)
        layout.addRow("Presión:", presion_input)
        layout.addRow("MCA (m):", medida_input)
        layout.addRow("Observación:", observa_input)
        label_mensaje = QLabel("")
        label_mensaje.setAlignment(Qt.AlignCenter)
        label_mensaje.setStyleSheet("QLabel { color: red; }")
        layout.addRow(label_mensaje)
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        # Cambiar los textos a español
        button_box.button(QDialogButtonBox.Save).setText("Guardar")
        button_box.button(QDialogButtonBox.Cancel).setText("Cancelar")
        layout.addWidget(button_box)
        # Conectar los botones a las funciones correspondientes
        def actualizarDatos():
            datofecha = fecha_input.text()
            respfecha = MetodosGenerales.validarFormatoFechaDatabase(datofecha)
            if respfecha:
                datofrecuencia = frecuencia_input.text()
                datotemperatura = temperatura_input.text()
                datopresion = presion_input.text()
                datomedida = medida_input.text()
                datoobserva = observa_input.text()
                username = Session.get_username()
                nombres = Session.get_nombres()
                if Session.is_authenticated() and DatosView.idproyecto and datofrecuencia != "" and datotemperatura != "" and datopresion != "" and datomedida != "":
                    datanueva = [datofecha, datofrecuencia, datotemperatura, datopresion, datomedida, datoobserva, iddetalle]
                    respuesta = PiezometroController.ctrlActualizarLecturaPiezoCuerda(tablasql, datanueva, DatosView.idproyecto, username, nombres)
                    if respuesta:
                        dialog.reject()
                        DatosView.obtenerEquiposMarcados(True)
                    else:
                        label_mensaje.setText("Error al actualizar los datos.")
                else:
                    label_mensaje.setText("Los datos están vacíos.")
            else:
                label_mensaje.setText("El formato de fecha no es válido.")
        button_box.accepted.connect(actualizarDatos)
        button_box.rejected.connect(dialog.reject)
        # Mostrar el diálogo
        dialog.setLayout(layout)
        dialog.exec()
    
    def hide_row_piezometrocuerda(iddetalle, nombre, fecha, tablasql):
        dlg = QMessageBox()
        dlg.setWindowTitle("Omitir Lectura Piezómetro")
        dlg.setText(f"¿Desea omitir/incluir la lectura del '{nombre}' con fecha '{fecha}'?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            respuesta = PiezometroController.ctrlCambiarEstadoLecturaPiezoCuerda(tablasql, iddetalle)
            if respuesta:
                DatosView.obtenerEquiposMarcados(True)
            else:
                mostrar_mensaje("Estado Lectura", "No se pudo omitir/incluir la lectura.", "advertencia")
    
    def delete_row_piezometrocuerda(iddetalle, nombre, fecha, tablasql):
        dlg = QMessageBox()
        dlg.setWindowTitle("Eliminar Lectura Piezómetro")
        dlg.setText(f"¿Desea eliminar la lectura del '{nombre}' con fecha '{fecha}'?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            username = Session.get_username()
            nombres = Session.get_nombres()
            if Session.is_authenticated() and DatosView.idproyecto:
                respuesta = PiezometroController.ctrlEliminarLecturaPiezoCuerda(tablasql, iddetalle, DatosView.idproyecto, username, nombres)
                if respuesta:
                    DatosView.obtenerEquiposMarcados(True)
                else:
                    mostrar_mensaje("Eliminar Lectura", "No se pudo eliminar la lectura.", "advertencia")
    
    def omitir_rows_piezometrocuerda(table, selected_indexes, tablasql):
        dataomitir = []
        idsomitir = []
        for index in selected_indexes:
            row = index.row()
            nombre = table.model().data(table.model().index(row, 1), Qt.DisplayRole)
            fecha = table.model().data(table.model().index(row, 2), Qt.DisplayRole)
            iddetalle = table.model().data(table.model().index(row, 15), Qt.DisplayRole)
            dataomitir.append((nombre, fecha, row))
            idsomitir.append((iddetalle))
        if len(idsomitir) > 0:
            dlg = QMessageBox()
            dlg.setWindowTitle("Omitir Lecturas Piezómetro")
            dlg.setText(f"¿Desea omitir/incluir las lecturas '{dataomitir}'?")
            dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            dlg.setIcon(QMessageBox.Question)
            result = dlg.exec()
            if result == QMessageBox.Yes:
                respuesta = PiezometroController.ctrlCambiarEstadoLecturaPiezoCuerdaBloque(tablasql, idsomitir)
                if respuesta:
                    DatosView.obtenerEquiposMarcados(True)
                else:
                    mostrar_mensaje("Omitir Lecturas", "No se pudo omitir/incluir las lecturas.", "advertencia")
    
    def delete_rows_piezometrocuerda(table, selected_indexes, tablasql):
        dataeliminar = []
        idseliminar = []
        for index in selected_indexes:
            row = index.row()
            nombre = table.model().data(table.model().index(row, 1), Qt.DisplayRole)
            fecha = table.model().data(table.model().index(row, 2), Qt.DisplayRole)
            iddetalle = table.model().data(table.model().index(row, 15), Qt.DisplayRole)
            dataeliminar.append((nombre, fecha, row))
            idseliminar.append((iddetalle))
        if len(idseliminar) > 0:
            dlg = QMessageBox()
            dlg.setWindowTitle("Eliminar Lecturas Piezómetro")
            dlg.setText(f"¿Desea eliminar las lecturas '{dataeliminar}'?")
            dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            dlg.setIcon(QMessageBox.Question)
            result = dlg.exec()
            if result == QMessageBox.Yes:
                username = Session.get_username()
                nombres = Session.get_nombres()
                if Session.is_authenticated() and DatosView.idproyecto:
                    respuesta = PiezometroController.ctrlEliminarLecturasBloquePiezoCuerda(tablasql, idseliminar, DatosView.idproyecto, username, nombres)
                    if respuesta:
                        DatosView.obtenerEquiposMarcados(True)
                    else:
                        mostrar_mensaje("Eliminar Lecturas", "No se pudo eliminar las lecturas.", "advertencia")
    
    # MENU TABLA PIEZOMETROS MANUALES
    def generarMenuTablaPiezometrosManual(position, table, nombre, fecha, medida, observa, iddetalle, idcota, cota, tablasql):
        # Crear menú contextual
        menu = QMenu()
        edit_action = QAction("Editar Lectura", table)
        update_action = QAction("Editar Cota Piezométrica", table)
        hide_action = QAction("Omitir/incluir Lectura", table)
        delete_action = QAction("Eliminar Lectura", table)
        # Conectar las acciones con los valores de la fila
        edit_action.triggered.connect(lambda: DatosView.editarDatosLecturaPiezometroManual(iddetalle, nombre, fecha, medida, observa, tablasql))
        update_action.triggered.connect(lambda: DatosView.editarCotaPiezometrica(idcota, nombre))
        hide_action.triggered.connect(lambda: DatosView.hide_row_piezometromanual(iddetalle, nombre, fecha, tablasql))
        delete_action.triggered.connect(lambda: DatosView.delete_row_piezometromanual(iddetalle, nombre, fecha, tablasql))
        # Añadir las acciones al menú
        menu.addAction(edit_action)
        menu.addAction(update_action)
        menu.addAction(hide_action)
        menu.addAction(delete_action)
        selected_indexes = table.selectionModel().selectedRows()
        if selected_indexes:
            omitir_action = QAction("Omitir/incluir en Bloque", table)
            eliminar_action = QAction("Eliminar en Bloque", table)
            omitir_action.triggered.connect(lambda: DatosView.omitir_rows_piezometromanual(table, selected_indexes, tablasql))
            eliminar_action.triggered.connect(lambda: DatosView.delete_rows_piezometromanual(table, selected_indexes, tablasql))
            menu.addAction(omitir_action)
            menu.addAction(eliminar_action)
        # Mostrar menú contextual en la posición del clic
        menu.exec(table.viewport().mapToGlobal(position))
    
    def editarDatosLecturaPiezometroManual(iddetalle, nombre, fecha, medida, observa, tablasql):
        dialog = QDialog()
        dialog.setWindowTitle("Editar Lectura Piezómetro")
        validator = QDoubleValidator()
        layout = QFormLayout(dialog)
        # Campo nombre (readonly)
        nombre_input = QLineEdit()
        nombre_input.setText(nombre)
        nombre_input.setReadOnly(True)
        # Campo fecha (editable)
        fecha_input = QLineEdit()
        fecha_input.setText(fecha)
        # Campo medida (editable)
        medida_input = QLineEdit()
        medida_input.setText(str(medida))
        medida_input.setValidator(validator)
        # Campo observación (editable)
        observa_input = QLineEdit()
        observa_input.setText(str(observa))
        # Añadir los campos al layout
        layout.addRow("Nombre:", nombre_input)
        layout.addRow("Fecha:", fecha_input)
        layout.addRow("Lectura (m):", medida_input)
        layout.addRow("Observación:", observa_input)
        label_mensaje = QLabel("")
        label_mensaje.setAlignment(Qt.AlignCenter)
        label_mensaje.setStyleSheet("QLabel { color: red; }")
        layout.addRow(label_mensaje)
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        # Cambiar los textos a español
        button_box.button(QDialogButtonBox.Save).setText("Guardar")
        button_box.button(QDialogButtonBox.Cancel).setText("Cancelar")
        layout.addWidget(button_box)
        # Conectar los botones a las funciones correspondientes
        def actualizarDatos():
            datofecha = fecha_input.text()
            respfecha = MetodosGenerales.validarFormatoFechaDatabase(datofecha)
            if respfecha:
                datomedida = medida_input.text()
                datoobserva = observa_input.text()
                username = Session.get_username()
                nombres = Session.get_nombres()
                if Session.is_authenticated() and DatosView.idproyecto and MetodosGenerales.validarEsNumero(datomedida) and datomedida != "":
                    datanueva = [datofecha, datomedida, datoobserva, iddetalle]
                    respuesta = PiezometroController.ctrlActualizarLecturaPiezoManual(tablasql, datanueva, DatosView.idproyecto, username, nombres)
                    if respuesta:
                        dialog.reject()
                        DatosView.obtenerEquiposMarcados(True)
                    else:
                        label_mensaje.setText("Error al actualizar los datos.")
                else:
                    label_mensaje.setText("Los datos están vacíos.")
            else:
                label_mensaje.setText("El formato de fecha no es válido.")
        button_box.accepted.connect(actualizarDatos)
        button_box.rejected.connect(dialog.reject)
        # Mostrar el diálogo
        dialog.setLayout(layout)
        dialog.exec()
    
    def editarCotaPiezometrica(idcota, nombre):
        if idcota != "":
            datacota = PiezometroController.ctrlTraerCotaPiezometrica(idcota)
            if datacota:
                dialog = QDialog()
                dialog.setWindowTitle("Editar Cota Piezométrica")
                validator = QDoubleValidator()
                layout = QFormLayout(dialog)
                # Campo nombre (readonly)
                nombre_input = QLineEdit()
                nombre_input.setText(nombre)
                nombre_input.setReadOnly(True)
                # Campo fecha (editable)
                fecha_input = QLineEdit()
                # fecha_input.setText(datacota[3])
                fecha_input.setText(str(datacota[3]))
                # Campo cota (editable)
                medida_input = QLineEdit()
                medida_input.setText(str(datacota[4]))
                medida_input.setValidator(validator)
                # Añadir los campos al layout
                layout.addRow("Piezómetro:", nombre_input)
                layout.addRow("Fecha:", fecha_input)
                layout.addRow("Cota (msnm):", medida_input)
                label_mensaje = QLabel("")
                label_mensaje.setAlignment(Qt.AlignCenter)
                label_mensaje.setStyleSheet("QLabel { color: red; }")
                layout.addRow(label_mensaje)
                button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
                # Cambiar los textos a español
                button_box.button(QDialogButtonBox.Save).setText("Guardar")
                button_box.button(QDialogButtonBox.Cancel).setText("Cancelar")
                layout.addWidget(button_box)
                # Conectar los botones a las funciones correspondientes
                def actualizarDatos():
                    datofecha = fecha_input.text()
                    respfecha = MetodosGenerales.validarFormatoFechaDatabase(datofecha)
                    if respfecha:
                        cotamedida = medida_input.text()
                        username = Session.get_username()
                        nombres = Session.get_nombres()
                        if Session.is_authenticated() and DatosView.idproyecto and MetodosGenerales.validarEsNumero(cotamedida) and cotamedida != "":
                            respuesta = PiezometroController.ctrlActualizarCotaPiezometrica(DatosView.idproyecto, idcota, datofecha, cotamedida, username, nombres)
                            if respuesta:
                                dialog.reject()
                                DatosView.obtenerEquiposMarcados(True)
                            else:
                                label_mensaje.setText("Error al actualizar los datos.")
                        else:
                            label_mensaje.setText("Los datos están vacíos.")
                button_box.accepted.connect(actualizarDatos)
                button_box.rejected.connect(dialog.reject)
                # Mostrar el diálogo
                dialog.setLayout(layout)
                dialog.exec()
            else:
                mostrar_mensaje("Sin Datos", "No se pudo cargar los datos.", "advertencia")
    
    def hide_row_piezometromanual(iddetalle, nombre, fecha, tablasql):
        dlg = QMessageBox()
        dlg.setWindowTitle("Omitir Lectura Piezómetro")
        dlg.setText(f"¿Desea omitir/incluir la lectura del '{nombre}' con fecha '{fecha}'?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            respuesta = PiezometroController.ctrlCambiarEstadoLecturaPiezoManual(tablasql, iddetalle)
            if respuesta:
                DatosView.obtenerEquiposMarcados(True)
            else:
                mostrar_mensaje("Estado Lectura", "No se pudo omitir/incluir la lectura.", "advertencia")
    
    def delete_row_piezometromanual(iddetalle, nombre, fecha, tablasql):
        dlg = QMessageBox()
        dlg.setWindowTitle("Eliminar Lectura Piezómetro")
        dlg.setText(f"¿Desea eliminar la lectura del '{nombre}' con fecha '{fecha}'?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            username = Session.get_username()
            nombres = Session.get_nombres()
            if Session.is_authenticated() and DatosView.idproyecto:
                respuesta = PiezometroController.ctrlEliminarLecturaPiezoManual(tablasql, iddetalle, DatosView.idproyecto, username, nombres)
                if respuesta:
                    DatosView.obtenerEquiposMarcados(True)
                else:
                    mostrar_mensaje("Eliminar Lectura", "No se pudo eliminar la lectura.", "advertencia")
    
    def omitir_rows_piezometromanual(table, selected_indexes, tablasql):
        dataomitir = []
        idsomitir = []
        for index in selected_indexes:
            row = index.row()
            nombre = table.model().data(table.model().index(row, 1), Qt.DisplayRole)
            fecha = table.model().data(table.model().index(row, 2), Qt.DisplayRole)
            iddetalle = table.model().data(table.model().index(row, 14), Qt.DisplayRole)
            dataomitir.append((nombre, fecha, row))
            idsomitir.append((iddetalle))
        if len(idsomitir) > 0:
            dlg = QMessageBox()
            dlg.setWindowTitle("Omitir Lecturas Piezómetro")
            dlg.setText(f"¿Desea omitir/incluir las lecturas '{dataomitir}'?")
            dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            dlg.setIcon(QMessageBox.Question)
            result = dlg.exec()
            if result == QMessageBox.Yes:
                respuesta = PiezometroController.ctrlCambiarEstadoLecturaPiezoManualBloque(tablasql, idsomitir)
                if respuesta:
                    DatosView.obtenerEquiposMarcados(True)
                else:
                    mostrar_mensaje("Omitir Lecturas", "No se pudo omitir/incluir las lecturas.", "advertencia")
    
    def delete_rows_piezometromanual(table, selected_indexes, tablasql):
        dataeliminar = []
        idseliminar = []
        for index in selected_indexes:
            row = index.row()
            nombre = table.model().data(table.model().index(row, 1), Qt.DisplayRole)
            fecha = table.model().data(table.model().index(row, 2), Qt.DisplayRole)
            iddetalle = table.model().data(table.model().index(row, 14), Qt.DisplayRole)
            dataeliminar.append((nombre, fecha, row))
            idseliminar.append((iddetalle))
        if len(idseliminar) > 0:
            dlg = QMessageBox()
            dlg.setWindowTitle("Eliminar Lecturas Piezómetro")
            dlg.setText(f"¿Desea eliminar las lecturas '{dataeliminar}'?")
            dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            dlg.setIcon(QMessageBox.Question)
            result = dlg.exec()
            if result == QMessageBox.Yes:
                username = Session.get_username()
                nombres = Session.get_nombres()
                if Session.is_authenticated() and DatosView.idproyecto:
                    respuesta = PiezometroController.ctrlEliminarLecturasBloquePiezoManual(tablasql, idseliminar, DatosView.idproyecto, username, nombres)
                    if respuesta:
                        DatosView.obtenerEquiposMarcados(True)
                    else:
                        mostrar_mensaje("Eliminar Lecturas", "No se pudo eliminar las lecturas.", "advertencia")
    
    # MENU TABLA PLUVIOMETROS
    def generarMenuTablaPluviometros(position, table, nombre, fecha, medida, observa, iddetalle, tablasql):
        # Crear menú contextual
        menu = QMenu()
        edit_action = QAction("Editar Lectura", table)
        delete_action = QAction("Eliminar Lectura", table)
        # Conectar las acciones con los valores de la fila
        edit_action.triggered.connect(lambda: DatosView.editarDatosLecturaPluviometros(iddetalle, nombre, fecha, medida, observa, tablasql))
        delete_action.triggered.connect(lambda: DatosView.delete_row_pluviometros(iddetalle, nombre, fecha, tablasql))
        # Añadir las acciones al menú
        menu.addAction(edit_action)
        menu.addAction(delete_action)
        selected_indexes = table.selectionModel().selectedRows()
        if selected_indexes:
            eliminar_action = QAction("Eliminar Bloque", table)
            eliminar_action.triggered.connect(lambda: DatosView.delete_rows_pluviometros(table, selected_indexes, tablasql))
            menu.addAction(eliminar_action)
        # Mostrar menú contextual en la posición del clic
        menu.exec(table.viewport().mapToGlobal(position))
    
    def editarDatosLecturaPluviometros(iddetalle, nombre, fecha, medida, observa, tablasql):
        dialog = QDialog()
        dialog.setWindowTitle("Editar Lectura Pluviómetro")
        validator = QDoubleValidator()
        layout = QFormLayout(dialog)
        # Campo nombre (readonly)
        nombre_input = QLineEdit()
        nombre_input.setText(nombre)
        nombre_input.setReadOnly(True)
        # Campo fecha (editable)
        fecha_input = QLineEdit()
        fecha_input.setText(fecha)
        # Campo medida (editable)
        medida_input = QLineEdit()
        medida_input.setText(str(medida))
        medida_input.setValidator(validator)
        # Campo medida (editable)
        observa_input = QLineEdit()
        observa_input.setText(str(observa))
        # Añadir los campos al layout
        layout.addRow("Nombre:", nombre_input)
        layout.addRow("Fecha:", fecha_input)
        layout.addRow("Precipitación (mm):", medida_input)
        layout.addRow("Observación:", observa_input)
        label_mensaje = QLabel("")
        label_mensaje.setAlignment(Qt.AlignCenter)
        label_mensaje.setStyleSheet("QLabel { color: red; }")
        layout.addRow(label_mensaje)
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        # Cambiar los textos a español
        button_box.button(QDialogButtonBox.Save).setText("Guardar")
        button_box.button(QDialogButtonBox.Cancel).setText("Cancelar")
        layout.addWidget(button_box)
        # Conectar los botones a las funciones correspondientes
        def actualizarDatos():
            datofecha = fecha_input.text()
            respfecha = MetodosGenerales.validarFormatoFechaDatabase(datofecha)
            if respfecha:
                datomedida = medida_input.text()
                datoobserva = observa_input.text()
                username = Session.get_username()
                nombres = Session.get_nombres()
                if Session.is_authenticated() and DatosView.idproyecto and MetodosGenerales.validarEsNumero(datomedida) and datomedida != "":
                    datanueva = [datofecha, datomedida, datoobserva, iddetalle]
                    respuesta = PluviometroController.ctrlActualizarLecturaPluviometro(tablasql, datanueva, DatosView.idproyecto, username, nombres)
                    if respuesta:
                        dialog.reject()
                        DatosView.obtenerEquiposMarcados(True)
                    else:
                        label_mensaje.setText("Error al actualizar los datos.")
                else:
                    label_mensaje.setText("Los datos están vacíos.")
            else:
                label_mensaje.setText("El formato de fecha no es válido.")
        button_box.accepted.connect(actualizarDatos)
        button_box.rejected.connect(dialog.reject)
        # Mostrar el diálogo
        dialog.setLayout(layout)
        dialog.exec()
    
    def delete_row_pluviometros(iddetalle, nombre, fecha, tablasql):
        dlg = QMessageBox()
        dlg.setWindowTitle("Eliminar Lectura Piezómetro")
        dlg.setText(f"¿Desea eliminar la lectura del '{nombre}' con fecha '{fecha}'?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            username = Session.get_username()
            nombres = Session.get_nombres()
            if Session.is_authenticated() and DatosView.idproyecto:
                respuesta = PluviometroController.ctrlEliminarLecturaPluviometro(tablasql, iddetalle, DatosView.idproyecto, username, nombres)
                if respuesta:
                    DatosView.obtenerEquiposMarcados(True)
                else:
                    mostrar_mensaje("Eliminar Lectura", "No se pudo eliminar la lectura.", "advertencia")
    
    def delete_rows_pluviometros(table, selected_indexes, tablasql):
        dataeliminar = []
        idseliminar = []
        for index in selected_indexes:
            row = index.row()
            nombre = table.model().data(table.model().index(row, 1), Qt.DisplayRole)
            fecha = table.model().data(table.model().index(row, 2), Qt.DisplayRole)
            iddetalle = table.model().data(table.model().index(row, 8), Qt.DisplayRole)
            dataeliminar.append((nombre, fecha, row))
            idseliminar.append((iddetalle))
        if len(idseliminar) > 0:
            dlg = QMessageBox()
            dlg.setWindowTitle("Eliminar Lecturas Pluviómetro")
            dlg.setText(f"¿Desea eliminar las lecturas '{dataeliminar}'?")
            dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            dlg.setIcon(QMessageBox.Question)
            result = dlg.exec()
            if result == QMessageBox.Yes:
                username = Session.get_username()
                nombres = Session.get_nombres()
                if Session.is_authenticated() and DatosView.idproyecto:
                    respuesta = PluviometroController.ctrlEliminarLecturasBloquePluviometro(tablasql, idseliminar, DatosView.idproyecto, username, nombres)
                    if respuesta:
                        DatosView.obtenerEquiposMarcados(True)
                    else:
                        mostrar_mensaje("Eliminar Lecturas", "No se pudo eliminar las lecturas.", "advertencia")
    
    # MENU TABLA COTAS TERRENO
    def generarMenuTablaCotaTerreno(position, table, nombre, fecha, cota, observa, iddetalle, tablasql):
        # Crear menú contextual
        menu = QMenu()
        edit_action = QAction("Editar Lectura", table)
        delete_action = QAction("Eliminar Lectura", table)
        # Conectar las acciones con los valores de la fila
        edit_action.triggered.connect(lambda: DatosView.editarDatosLecturaCotasTerreno(iddetalle, nombre, fecha, cota, observa, tablasql))
        delete_action.triggered.connect(lambda: DatosView.delete_row_cotasterreno(iddetalle, nombre, fecha, tablasql))
        # Añadir las acciones al menú
        menu.addAction(edit_action)
        menu.addAction(delete_action)
        selected_indexes = table.selectionModel().selectedRows()
        if selected_indexes:
            eliminar_action = QAction("Eliminar Bloque", table)
            eliminar_action.triggered.connect(lambda: DatosView.delete_rows_cotasterreno(table, selected_indexes, tablasql))
            menu.addAction(eliminar_action)
        # Mostrar menú contextual en la posición del clic
        menu.exec(table.viewport().mapToGlobal(position))
    
    def editarDatosLecturaCotasTerreno(iddetalle, nombre, fecha, cota, observa, tablasql):
        dialog = QDialog()
        dialog.setWindowTitle("Editar Lectura Cotas Terreno")
        validator = QDoubleValidator()
        layout = QFormLayout(dialog)
        # Campo nombre (readonly)
        nombre_input = QLineEdit()
        nombre_input.setText(nombre)
        nombre_input.setReadOnly(True)
        # Campo fecha (editable)
        fecha_input = QLineEdit()
        fecha_input.setText(fecha)
        # Campo cota (editable)
        cota_input = QLineEdit()
        cota_input.setText(str(cota))
        cota_input.setValidator(validator)
        # Campo observación (editable)
        observa_input = QLineEdit()
        observa_input.setText(observa)
        # Añadir los campos al layout
        layout.addRow("Nombre:", nombre_input)
        layout.addRow("Fecha:", fecha_input)
        layout.addRow("Cota (msnm):", cota_input)
        layout.addRow("Observación:", observa_input)
        label_mensaje = QLabel("")
        label_mensaje.setAlignment(Qt.AlignCenter)
        label_mensaje.setStyleSheet("QLabel { color: red; }")
        layout.addRow(label_mensaje)
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        # Cambiar los textos a español
        button_box.button(QDialogButtonBox.Save).setText("Guardar")
        button_box.button(QDialogButtonBox.Cancel).setText("Cancelar")
        layout.addWidget(button_box)
        # Conectar los botones a las funciones correspondientes
        def actualizarDatos():
            datofecha = fecha_input.text()
            respfecha = MetodosGenerales.validarFormatoFechaDatabase(datofecha)
            if respfecha:
                datocota = cota_input.text()
                datoobserva = observa_input.text()
                username = Session.get_username()
                nombres = Session.get_nombres()
                if Session.is_authenticated() and DatosView.idproyecto and MetodosGenerales.validarEsNumero(datocota) and datocota != "":
                    datanueva = [datofecha, datocota, datoobserva, iddetalle]
                    respuesta = TerrenoController.ctrlActualizarLecturaCotaterreno(tablasql, datanueva, DatosView.idproyecto, username, nombres)
                    if respuesta:
                        dialog.reject()
                        DatosView.obtenerEquiposMarcados(True)
                    else:
                        label_mensaje.setText("Error al actualizar los datos.")
                else:
                    label_mensaje.setText("Los datos están vacíos.")
            else:
                label_mensaje.setText("El formato de fecha no es válido.")
        button_box.accepted.connect(actualizarDatos)
        button_box.rejected.connect(dialog.reject)
        # Mostrar el diálogo
        dialog.setLayout(layout)
        dialog.exec()
    
    def delete_row_cotasterreno(iddetalle, nombre, fecha, tablasql):
        dlg = QMessageBox()
        dlg.setWindowTitle("Eliminar Lectura Cotas Terreno")
        dlg.setText(f"¿Desea eliminar la lectura del '{nombre}' con fecha '{fecha}'?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            username = Session.get_username()
            nombres = Session.get_nombres()
            if Session.is_authenticated() and DatosView.idproyecto:
                respuesta = TerrenoController.ctrlEliminarLecturaCotaterreno(tablasql, iddetalle, DatosView.idproyecto, username, nombres)
                if respuesta:
                    DatosView.obtenerEquiposMarcados(True)
                else:
                    mostrar_mensaje("Eliminar Lectura", "No se pudo eliminar la lectura.", "advertencia")
    
    def delete_rows_cotasterreno(table, selected_indexes, tablasql):
        dataeliminar = []
        idseliminar = []
        for index in selected_indexes:
            row = index.row()
            nombre = table.model().data(table.model().index(row, 1), Qt.DisplayRole)
            fecha = table.model().data(table.model().index(row, 2), Qt.DisplayRole)
            iddetalle = table.model().data(table.model().index(row, 5), Qt.DisplayRole)
            dataeliminar.append((nombre, fecha, row))
            idseliminar.append((iddetalle))
        if len(idseliminar) > 0:
            dlg = QMessageBox()
            dlg.setWindowTitle("Eliminar Lecturas Cotas Terreno")
            dlg.setText(f"¿Desea eliminar las lecturas '{dataeliminar}'?")
            dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            dlg.setIcon(QMessageBox.Question)
            result = dlg.exec()
            if result == QMessageBox.Yes:
                username = Session.get_username()
                nombres = Session.get_nombres()
                if Session.is_authenticated() and DatosView.idproyecto:
                    respuesta = TerrenoController.ctrlEliminarLecturasBloqueCotaterreno(tablasql, idseliminar, DatosView.idproyecto, username, nombres)
                    if respuesta:
                        DatosView.obtenerEquiposMarcados(True)
                    else:
                        mostrar_mensaje("Eliminar Lecturas", "No se pudo eliminar las lecturas.", "advertencia")
    
    # MENU TABLA CELDAS
    def generarMenuTablaCeldas(position, table, nombre, fecha, frecuendigi, frecuencihz, temperatura, desplaza, observa, iddetalle, tablasql):
        # Crear menú contextual
        menu = QMenu()
        edit_action = QAction("Editar Lectura", table)
        hide_action = QAction("Omitir/incluir Lectura", table)
        delete_action = QAction("Eliminar Lectura", table)
        # Conectar las acciones con los valores de la fila
        edit_action.triggered.connect(lambda: DatosView.editarDatosLecturaCeldas(iddetalle, nombre, fecha, frecuendigi, frecuencihz, temperatura, desplaza, observa, tablasql))
        hide_action.triggered.connect(lambda: DatosView.hide_row_celdas(iddetalle, nombre, fecha, tablasql))
        delete_action.triggered.connect(lambda: DatosView.delete_row_celdas(iddetalle, nombre, fecha, tablasql))
        # Añadir las acciones al menú
        menu.addAction(edit_action)
        menu.addAction(hide_action)
        menu.addAction(delete_action)
        selected_indexes = table.selectionModel().selectedRows()
        if selected_indexes:
            omitir_action = QAction("Omitir/incluir en Bloque", table)
            eliminar_action = QAction("Eliminar en Bloque", table)
            omitir_action.triggered.connect(lambda: DatosView.omitir_rows_celdas(table, selected_indexes, tablasql))
            eliminar_action.triggered.connect(lambda: DatosView.delete_rows_celdas(table, selected_indexes, tablasql))
            menu.addAction(omitir_action)
            menu.addAction(eliminar_action)
        # Mostrar menú contextual en la posición del clic
        menu.exec(table.viewport().mapToGlobal(position))
    
    def editarDatosLecturaCeldas(iddetalle, nombre, fecha, frecuendigi, frecuencihz, temperatura, desplaza, observa, tablasql):
        dialog = QDialog()
        dialog.setWindowTitle("Editar Lectura Celdas")
        validator = QDoubleValidator()
        layout = QFormLayout(dialog)
        # Campo nombre (readonly)
        nombre_input = QLineEdit()
        nombre_input.setText(nombre)
        nombre_input.setReadOnly(True)
        # Campo fecha (editable)
        fecha_input = QLineEdit()
        fecha_input.setText(fecha)
        # Campo frecuencia (editable)
        frecuendigi_input = QLineEdit()
        frecuendigi_input.setText(str(frecuendigi))
        frecuendigi_input.setValidator(validator)
        # Campo frecuencia hz (editable)
        frecuencihz_input = QLineEdit()
        frecuencihz_input.setText(str(frecuencihz))
        frecuencihz_input.setValidator(validator)
        # Campo temperatura (editable)
        temperatura_input = QLineEdit()
        temperatura_input.setText(str(temperatura))
        temperatura_input.setValidator(validator)
        # Campo medida mca (editable)
        desplaza_input = QLineEdit()
        desplaza_input.setText(str(desplaza))
        desplaza_input.setValidator(validator)
        # Campo observación (editable)
        observa_input = QLineEdit()
        observa_input.setText(observa)
        # Añadir los campos al layout
        layout.addRow("Nombre:", nombre_input)
        layout.addRow("Fecha y Hora:", fecha_input)
        layout.addRow("Frecuencia (Digits):", frecuendigi_input)
        layout.addRow("Frecuencia (Hz):", frecuencihz_input)
        layout.addRow("Temperatura (°C):", temperatura_input)
        layout.addRow("Desplazamiento (m):", desplaza_input)
        layout.addRow("Observación:", observa_input)
        label_mensaje = QLabel("")
        label_mensaje.setAlignment(Qt.AlignCenter)
        label_mensaje.setStyleSheet("QLabel { color: red; }")
        layout.addRow(label_mensaje)
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        # Cambiar los textos a español
        button_box.button(QDialogButtonBox.Save).setText("Guardar")
        button_box.button(QDialogButtonBox.Cancel).setText("Cancelar")
        layout.addWidget(button_box)
        # Conectar los botones a las funciones correspondientes
        def actualizarDatos():
            datofecha = fecha_input.text()
            respfecha = MetodosGenerales.validarFormatoFechaDatabase(datofecha)
            if respfecha:
                datofrecuendigi = frecuendigi_input.text()
                datofrecuencihz = frecuencihz_input.text()
                datotemperatura = temperatura_input.text()
                datodesplaza = desplaza_input.text()
                datoobserva = observa_input.text()
                username = Session.get_username()
                nombres = Session.get_nombres()
                if Session.is_authenticated() and DatosView.idproyecto and MetodosGenerales.validarEsNumero(datofrecuendigi) and MetodosGenerales.validarEsNumero(datofrecuencihz) and MetodosGenerales.validarEsNumero(datotemperatura) and MetodosGenerales.validarEsNumero(datodesplaza):
                    datanueva = [datofecha, datofrecuendigi, datofrecuencihz, datotemperatura, datodesplaza, datoobserva, iddetalle]
                    respuesta = CeldaController.ctrlActualizarLecturaCelda(tablasql, datanueva, DatosView.idproyecto, username, nombres)
                    if respuesta:
                        dialog.reject()
                        DatosView.obtenerEquiposMarcados(True)
                    else:
                        label_mensaje.setText("Error al actualizar los datos.")
                else:
                    label_mensaje.setText("Los datos están vacíos.")
            else:
                label_mensaje.setText("El formato de fecha no es válido.")
        button_box.accepted.connect(actualizarDatos)
        button_box.rejected.connect(dialog.reject)
        # Mostrar el diálogo
        dialog.setLayout(layout)
        dialog.exec()
    
    def hide_row_celdas(iddetalle, nombre, fecha, tablasql):
        dlg = QMessageBox()
        dlg.setWindowTitle("Omitir Lectura Celda")
        dlg.setText(f"¿Desea omitir/incluir la lectura del '{nombre}' con fecha '{fecha}'?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            respuesta = CeldaController.ctrlCambiarEstadoLecturaCelda(tablasql, iddetalle)
            if respuesta:
                DatosView.obtenerEquiposMarcados(True)
            else:
                mostrar_mensaje("Estado Lectura", "No se pudo omitir/incluir la lectura.", "advertencia")
    
    def delete_row_celdas(iddetalle, nombre, fecha, tablasql):
        dlg = QMessageBox()
        dlg.setWindowTitle("Eliminar Lectura Celdas")
        dlg.setText(f"¿Desea eliminar la lectura del '{nombre}' con fecha '{fecha}'?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            username = Session.get_username()
            nombres = Session.get_nombres()
            if Session.is_authenticated() and DatosView.idproyecto:
                respuesta = CeldaController.ctrlEliminarLecturaCelda(tablasql, iddetalle, DatosView.idproyecto, username, nombres)
                if respuesta:
                    DatosView.obtenerEquiposMarcados(True)
                else:
                    mostrar_mensaje("Eliminar Lectura", "No se pudo eliminar la lectura.", "advertencia")
    
    def omitir_rows_celdas(table, selected_indexes, tablasql):
        dataomitir = []
        idsomitir = []
        for index in selected_indexes:
            row = index.row()
            nombre = table.model().data(table.model().index(row, 1), Qt.DisplayRole)
            fecha = table.model().data(table.model().index(row, 2), Qt.DisplayRole)
            iddetalle = table.model().data(table.model().index(row, 16), Qt.DisplayRole)
            dataomitir.append((nombre, fecha, row))
            idsomitir.append((iddetalle))
        if len(idsomitir) > 0:
            dlg = QMessageBox()
            dlg.setWindowTitle("Omitir Lecturas Celdas")
            dlg.setText(f"¿Desea omitir/incluir las lecturas '{dataomitir}'?")
            dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            dlg.setIcon(QMessageBox.Question)
            result = dlg.exec()
            if result == QMessageBox.Yes:
                respuesta = CeldaController.ctrlCambiarEstadoLecturaCeldaBloque(tablasql, idsomitir)
                if respuesta:
                    DatosView.obtenerEquiposMarcados(True)
                else:
                    mostrar_mensaje("Omitir Lecturas", "No se pudo omitir/incluir las lecturas.", "advertencia")
    
    def delete_rows_celdas(table, selected_indexes, tablasql):
        dataeliminar = []
        idseliminar = []
        for index in selected_indexes:
            row = index.row()
            nombre = table.model().data(table.model().index(row, 1), Qt.DisplayRole)
            fecha = table.model().data(table.model().index(row, 2), Qt.DisplayRole)
            iddetalle = table.model().data(table.model().index(row, 16), Qt.DisplayRole)
            dataeliminar.append((nombre, fecha, row))
            idseliminar.append((iddetalle))
        if len(idseliminar) > 0:
            dlg = QMessageBox()
            dlg.setWindowTitle("Eliminar Lecturas Celdas")
            dlg.setText(f"¿Desea eliminar las lecturas '{dataeliminar}'?")
            dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            dlg.setIcon(QMessageBox.Question)
            result = dlg.exec()
            if result == QMessageBox.Yes:
                username = Session.get_username()
                nombres = Session.get_nombres()
                if Session.is_authenticated() and DatosView.idproyecto:
                    respuesta = CeldaController.ctrlEliminarLecturasBloqueCelda(tablasql, idseliminar, DatosView.idproyecto, username, nombres)
                    if respuesta:
                        DatosView.obtenerEquiposMarcados(True)
                    else:
                        mostrar_mensaje("Eliminar Lecturas", "No se pudo eliminar las lecturas.", "advertencia")
    
    # MENU TABLA ACELERÓGRAFOS
    def generarMenuTablaAcelerografos(position, table, nombre, fecha, magnitud, distancia, observa, iddetalle, tablasql):
        # Crear menú contextual
        menu = QMenu()
        edit_action = QAction("Editar Lectura", table)
        delete_action = QAction("Eliminar Lectura", table)
        # Conectar las acciones con los valores de la fila
        edit_action.triggered.connect(lambda: DatosView.editarDatosLecturaAcelerografos(iddetalle, nombre, fecha, magnitud, distancia, observa, tablasql))
        delete_action.triggered.connect(lambda: DatosView.delete_row_acelerografos(iddetalle, nombre, fecha, tablasql))
        # Añadir las acciones al menú
        menu.addAction(edit_action)
        menu.addAction(delete_action)
        selected_indexes = table.selectionModel().selectedRows()
        if selected_indexes:
            eliminar_action = QAction("Eliminar Bloque", table)
            eliminar_action.triggered.connect(lambda: DatosView.delete_rows_acelerografos(table, selected_indexes, tablasql))
            menu.addAction(eliminar_action)
        # Mostrar menú contextual en la posición del clic
        menu.exec(table.viewport().mapToGlobal(position))
    
    def editarDatosLecturaAcelerografos(iddetalle, nombre, fecha, magnitud, distancia, observa, tablasql):
        dialog = QDialog()
        dialog.setWindowTitle("Editar Lectura Acelerógrafo")
        validator = QDoubleValidator()
        layout = QFormLayout(dialog)
        # Campo nombre (readonly)
        nombre_input = QLineEdit()
        nombre_input.setText(nombre)
        nombre_input.setReadOnly(True)
        # Campo fecha (editable)
        fecha_input = QLineEdit()
        fecha_input.setText(fecha)
        # Campo magnitud (editable)
        magnitud_input = QLineEdit()
        magnitud_input.setText(str(magnitud))
        magnitud_input.setValidator(validator)
        # Campo distancia (editable)
        distancia_input = QLineEdit()
        distancia_input.setText(str(distancia))
        distancia_input.setValidator(validator)
        # Campo observación (editable)
        observa_input = QLineEdit()
        observa_input.setText(observa)
        # Añadir los campos al layout
        layout.addRow("Nombre:", nombre_input)
        layout.addRow("Fecha:", fecha_input)
        layout.addRow("Magnitud:", magnitud_input)
        layout.addRow("Distancia (km):", distancia_input)
        layout.addRow("Observación:", observa_input)
        label_mensaje = QLabel("")
        label_mensaje.setAlignment(Qt.AlignCenter)
        label_mensaje.setStyleSheet("QLabel { color: red; }")
        layout.addRow(label_mensaje)
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        # Cambiar los textos a español
        button_box.button(QDialogButtonBox.Save).setText("Guardar")
        button_box.button(QDialogButtonBox.Cancel).setText("Cancelar")
        layout.addWidget(button_box)
        # Conectar los botones a las funciones correspondientes
        def actualizarDatos():
            datofecha = fecha_input.text()
            respfecha = MetodosGenerales.validarFormatoFechaDatabase(datofecha)
            if respfecha:
                datomagnitud = magnitud_input.text()
                datodistancia = distancia_input.text()
                datoobserva = observa_input.text()
                username = Session.get_username()
                nombres = Session.get_nombres()
                if Session.is_authenticated() and DatosView.idproyecto and MetodosGenerales.validarEsNumero(datomagnitud) and MetodosGenerales.validarEsNumero(datodistancia):
                    datanueva = [datofecha, datomagnitud, datodistancia, datoobserva, iddetalle]
                    respuesta = AcelerografoController.ctrlActualizarLecturaAcelerografo(tablasql, datanueva, DatosView.idproyecto, username, nombres)
                    if respuesta:
                        dialog.reject()
                        DatosView.obtenerEquiposMarcados(True)
                    else:
                        label_mensaje.setText("Error al actualizar los datos.")
                else:
                    label_mensaje.setText("Los datos están vacíos.")
            else:
                label_mensaje.setText("El formato de fecha no es válido.")
        button_box.accepted.connect(actualizarDatos)
        button_box.rejected.connect(dialog.reject)
        # Mostrar el diálogo
        dialog.setLayout(layout)
        dialog.exec()
    
    def delete_row_acelerografos(iddetalle, nombre, fecha, tablasql):
        dlg = QMessageBox()
        dlg.setWindowTitle("Eliminar Lectura Acelerógrafo")
        dlg.setText(f"¿Desea eliminar la lectura del '{nombre}' con fecha '{fecha}'?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            username = Session.get_username()
            nombres = Session.get_nombres()
            if Session.is_authenticated() and DatosView.idproyecto:
                respuesta = AcelerografoController.ctrlEliminarLecturaAcelerografo(tablasql, iddetalle, DatosView.idproyecto, username, nombres)
                if respuesta:
                    DatosView.obtenerEquiposMarcados(True)
                else:
                    mostrar_mensaje("Eliminar Lectura", "No se pudo eliminar la lectura.", "advertencia")
    
    def delete_rows_acelerografos(table, selected_indexes, tablasql):
        dataeliminar = []
        idseliminar = []
        for index in selected_indexes:
            row = index.row()
            nombre = table.model().data(table.model().index(row, 1), Qt.DisplayRole)
            fecha = table.model().data(table.model().index(row, 2), Qt.DisplayRole)
            iddetalle = table.model().data(table.model().index(row, 9), Qt.DisplayRole)
            dataeliminar.append((nombre, fecha, row))
            idseliminar.append((iddetalle))
        if len(idseliminar) > 0:
            dlg = QMessageBox()
            dlg.setWindowTitle("Eliminar Lecturas Acelerógrafo")
            dlg.setText(f"¿Desea eliminar las lecturas '{dataeliminar}'?")
            dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            dlg.setIcon(QMessageBox.Question)
            result = dlg.exec()
            if result == QMessageBox.Yes:
                username = Session.get_username()
                nombres = Session.get_nombres()
                if Session.is_authenticated() and DatosView.idproyecto:
                    respuesta = AcelerografoController.ctrlEliminarLecturasBloqueAcelerografo(tablasql, idseliminar, DatosView.idproyecto, username, nombres)
                    if respuesta:
                        DatosView.obtenerEquiposMarcados(True)
                    else:
                        mostrar_mensaje("Eliminar Lecturas", "No se pudo eliminar las lecturas.", "advertencia")
    
    # MENU TABLA TDR
    def generarMenuTablaSondajestdr(position, table, nombre, fecha, medida, impedancia, observa, iddetalle, tablasql):
        # Crear menú contextual
        menu = QMenu()
        edit_action = QAction("Editar Lectura", table)
        # Conectar las acciones con los valores de la fila
        edit_action.triggered.connect(lambda: DatosView.editarDatosLecturaSondajestdr(iddetalle, nombre, fecha, medida, impedancia, observa, tablasql))
        # Añadir las acciones al menú
        menu.addAction(edit_action)
        menu.exec(table.viewport().mapToGlobal(position))
    
    def editarDatosLecturaSondajestdr(iddetalle, nombre, fecha, medida, impedancia, observa, tablasql):
        dialog = QDialog()
        dialog.setWindowTitle("Editar Lectura TDR")
        validator = QDoubleValidator()
        layout = QFormLayout(dialog)
        # Campo nombre (readonly)
        nombre_input = QLineEdit()
        nombre_input.setText(nombre)
        nombre_input.setReadOnly(True)
        # Campo fecha (readonly)
        fecha_input = QLineEdit()
        fecha_input.setText(fecha)
        fecha_input.setReadOnly(True)
        # Campo profundidad (editable)
        profundidad_input = QLineEdit()
        profundidad_input.setText(medida)
        # Campo Impedancia (editable)
        impedancia_input = QLineEdit()
        impedancia_input.setText(str(impedancia))
        impedancia_input.setValidator(validator)
        # Campo observación (editable)
        observa_input = QLineEdit()
        observa_input.setText(observa)
        # Añadir los campos al layout
        layout.addRow("Nombre:", nombre_input)
        layout.addRow("Fecha:", fecha_input)
        layout.addRow("Profundidad (m):", profundidad_input)
        layout.addRow("Impedancia (m):", impedancia_input)
        layout.addRow("Observación:", observa_input)
        label_mensaje = QLabel("")
        label_mensaje.setAlignment(Qt.AlignCenter)
        label_mensaje.setStyleSheet("QLabel { color: red; }")
        layout.addRow(label_mensaje)
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        # Cambiar los textos a español
        button_box.button(QDialogButtonBox.Save).setText("Guardar")
        button_box.button(QDialogButtonBox.Cancel).setText("Cancelar")
        layout.addWidget(button_box)
        # Conectar los botones a las funciones correspondientes
        def actualizarDatos():
            datoprofundidad = profundidad_input.text()
            datoimpedancia = impedancia_input.text()
            datoobserva = observa_input.text()
            username = Session.get_username()
            nombres = Session.get_nombres()
            if Session.is_authenticated() and DatosView.idproyecto and MetodosGenerales.validarEsNumero(datoprofundidad) and MetodosGenerales.validarEsNumero(datoimpedancia):
                datanueva = [datoprofundidad, datoimpedancia, datoobserva, iddetalle]
                respuesta = TDRController.ctrlActualizarLecturaSondajetdr(tablasql, datanueva, DatosView.idproyecto, username, nombres)
                if respuesta:
                    dialog.reject()
                    DatosView.obtenerEquiposMarcados(True)
                else:
                    label_mensaje.setText("Error al actualizar los datos.")
            else:
                label_mensaje.setText("Los datos están vacíos.")
        button_box.accepted.connect(actualizarDatos)
        button_box.rejected.connect(dialog.reject)
        # Mostrar el diálogo
        dialog.setLayout(layout)
        dialog.exec()
    