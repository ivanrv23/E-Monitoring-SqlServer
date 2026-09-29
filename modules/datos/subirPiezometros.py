import pandas as pd
from openpyxl import load_workbook
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QComboBox, QFileDialog, QCheckBox, QPushButton, QTableWidget, QDoubleSpinBox,
                        QSpinBox, QTreeWidgetItem, QTreeWidget, QFormLayout, QDialogButtonBox, QMessageBox, QLabel, QTextEdit,
                        QLineEdit, QTableView)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import Qt, QThread, Signal
from datetime import datetime, time
from utils.common.rutasarchivos import resource_path
from utils.generic.cargariconos import cargarIcono
from utils.common.alertas import mostrar_mensaje
from utils.shared.pegarDatosTabla import configurar_tabla_para_pegado
from utils.generic.listaiconos import ListaIconos
from utils.shared.arbolmarcado import TreeCheckbox
from utils.common.metodosGenerales import MetodosGenerales
from controllers.PiezometroController import PiezometroController
from controllers.ProyectoController import ProyectoController
from controllers.InterfazController import InterfazController
from utils.shared.loading import LoadingView

class SubirPiezometros:
    _current_thread_cuerda = None       
    _current_thread_casagrande = None
    def cargarPiezometrosCuerda(main, proyectoid):
        loaderLoading = QUiLoader()        
        ui_file_path = resource_path("ui/datapiezometrocuerda.ui")
        ui_file = loaderLoading.load(ui_file_path, None)
        dialogoPiezocuerda = QDialog()
        dialogoPiezocuerda.setWindowTitle("Data Piezómetros Cuerda Vibrante")
        layout_piezocuerda = QVBoxLayout()
        layout_piezocuerda.addWidget(ui_file)
        dialogoPiezocuerda.setLayout(layout_piezocuerda)
        # tools
        comboPiezometros = dialogoPiezocuerda.findChild(QComboBox, "combo_piezometros")
        tabladata = dialogoPiezocuerda.findChild(QTableWidget, "table_piezometros_calculo")
        checknivel = dialogoPiezocuerda.findChild(QCheckBox, "check_elevacion")
        lblrespuesta = dialogoPiezocuerda.findChild(QLabel, "label_mensaje_estado")
        # agregar una celda a cada tabla
        row_position1 = tabladata.rowCount()
        tabladata.insertRow(row_position1)
        botonGuardarData = dialogoPiezocuerda.findChild(QPushButton, "btn_guardar_piezometros")
        # cargar piezómetros en el combo
        listapiezometros = PiezometroController.ctrlListarPiezometrosCuerda(proyectoid)
        if listapiezometros:
            for fila in listapiezometros:
                comboPiezometros.addItem(str(fila[3]), fila[0])
        else:
            comboPiezometros.addItem("Sin Piezómetros")
            comboPiezometros.setEnabled(False)
            botonGuardarData.setEnabled(False)
        configurar_tabla_para_pegado(tabladata)
        # GUARDAR DATA CUERDA VIBRANTE TABLA
        def guardarPiezometrosCuerdaTabla():
            idpiezometro = comboPiezometros.currentData()
            estadonivel = checknivel.isChecked()
            filas = tabladata.rowCount()
            if filas > 0 and proyectoid != 0:
                data = []
                estado = False
                for row in range(filas):
                    datosfila = []
                    datosfila.append(idpiezometro)
                    fila_valida = True
                    c = 0
                    for column in range(tabladata.columnCount()):
                        item = tabladata.item(row, column)
                        valor = item.text().strip() if item else ""
                        if valor != "":
                            if column == 0:
                                valor = MetodosGenerales.validarFormatoFecha(valor)
                                if not valor:
                                    mensaje = "La fecha no tiene un formato adecuado."
                                    fila_valida = False
                                    break
                            elif column == 1:
                                valor = MetodosGenerales.validarFormatoHora(valor)
                                if not valor:
                                    mensaje = "La hora no tiene un formato adecuado."
                                    fila_valida = False
                                    break
                            elif column > 1 and column < 6:
                                if not MetodosGenerales.validarEsNumero(valor):
                                    mensaje = "Algunas lecturas no son numéricas."
                                    fila_valida = False
                                    break
                        else:
                            if column == 0:
                                fila_valida = False
                                mensaje = "La fecha está vacía."
                            elif column == 1:
                                valor = "00:00:00"
                            elif column == 2:
                                fila_valida = False
                                mensaje = "La frecuencia está vacía."
                            elif column == 3:
                                fila_valida = False
                                mensaje = "La temperatura está vacía."
                            elif column == 4:
                                valor = 0
                            elif column == 5:
                                valor = 0
                            c += 1
                        datosfila.append(valor)
                    if c != 7:
                        if fila_valida and len(datosfila) == 8:
                            data.append(datosfila)
                            estado = True
                        else:
                            estado = False
                            break
                if estado:
                    respuesta = PiezometroController.ctrlGuardarPiezometrosCuerdaCalculada(proyectoid, data, estadonivel)
                    if respuesta:
                        lblrespuesta.setText('Guardado correctamente')
                        lblrespuesta.setStyleSheet("color: green;")
                        # Limpiar filas tabla
                        tabladata.setRowCount(0)
                        tabladata.insertRow(0)
                        # actualizar árbol checkbox
                        data = PiezometroController.ctrlTraerDataPiezometro(idpiezometro, "PIEZOMETROCUERDA")
                        if data:
                            idinstrumento, idcomponente, nombrezona = data[0], data[1], data[2]
                            treewidgetdatos = main.findChild(QTreeWidget, "tree_actual_datos")
                            treewidgetvisor = main.findChild(QTreeWidget, "tree_actual_visor")
                            treewidgetpiezo = main.findChild(QTreeWidget, "tree_actual_piezometros")
                            TreeCheckbox.eliminarCheckbox(treewidgetdatos, "Piezómetros Cuerda Vibrante", idinstrumento, "piezometrocuerda")
                            TreeCheckbox.eliminarCheckbox(treewidgetvisor, "Piezómetros Cuerda Vibrante", idinstrumento, "piezometrocuerda")
                            TreeCheckbox.eliminarCheckbox(treewidgetpiezo, "Piezómetros Cuerda Vibrante", idinstrumento, "piezometrocuerda")
                            # Crear piezometro cuerda en nuevo componente
                            piezocu = InterfazController.ctrlListarComponentePiezometroCuerda(idinstrumento)
                            if piezocu:
                                TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetdatos, nombrezona, idcomponente, proyectoid, "Piezómetros Cuerda Vibrante", "3", piezocu, "piezometrocuerda")
                                TreeCheckbox.crearNuevoGrupoCheckboxesDoble(treewidgetpiezo, nombrezona, idcomponente, proyectoid, "Piezómetros Cuerda Vibrante", "1", piezocu, "piezometrocuerda")
                                fechas = InterfazController.ctrlListarFechasPiezometroCodigo("Automatizado", idcomponente, idinstrumento, proyectoid)
                                if fechas:
                                    ultima_fecha = fechas[-1][0]
                                    piezo = piezocu[0]
                                    piezometros = [(piezo[0], piezo[1], piezo[2], piezo[3], piezo[4], piezo[5], piezo[6], ultima_fecha)]
                                    TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetvisor, nombrezona, idcomponente, proyectoid, "Piezómetros Cuerda Vibrante", "4", piezometros, "piezometrocuerda", "SI")
                    else:
                        lblrespuesta.setText(f"En la fila {len(data) + 1}: {mensaje}")
                        lblrespuesta.setStyleSheet("color: red;")
                else:
                    lblrespuesta.setText(f"En la fila {len(data) + 1}: {mensaje}")
                    lblrespuesta.setStyleSheet("color: orange;")  
                    
        # Conectar señales
        botonGuardarData.clicked.connect(guardarPiezometrosCuerdaTabla)
        dialogoPiezocuerda.exec()
    
    def cargarDataFormatosCuerda(main, idproyecto, tipo):
        loader = QUiLoader()
        ui_file_path = resource_path("ui/cargardataformato.ui")
        ui_file = loader.load(ui_file_path, None)
        dialogo = QDialog()
        dialogo.setWindowTitle("Data Piezómetros Cuerda Vibrante")
        layout_procesar_data = QVBoxLayout()
        layout_procesar_data.addWidget(ui_file)
        dialogo.setLayout(layout_procesar_data)
        ruta = "resources/iconos/fontawesome/solid/file-arrow-up.svg"
        botonSubir = dialogo.findChild(QPushButton, "btn_cargar_archivo")
        cargarIcono(botonSubir, ruta)
        ubicacion_archivo = dialogo.findChild(QLineEdit, "input_archivo")
        ubicacion_archivo.setReadOnly(True)
        comboComponentes = dialogo.findChild(QComboBox, "combo_componentes")
        labelRespuesta = dialogo.findChild(QLabel, "label_mensaje")
        botonAceptar = dialogo.findChild(QPushButton, "btn_aceptar")
        componentes = ProyectoController.ctrlObtenerComponentesProyecto(idproyecto)
        if len(componentes) > 0:
            for fila in componentes:
                comboComponentes.addItem(str(fila[2]), fila[0])
            comboComponentes.setEnabled(True)
        else:
            comboComponentes.addItem("Sin Componentes")
            comboComponentes.setEnabled(False)
            botonAceptar.setEnabled(False)
        def cargar_archivo():
            file_names, _ = QFileDialog.getOpenFileNames(None, "Cargar Archivos", "", "Archivos Excel (*.xlsx)")
            if file_names:
                ubicacion_archivo.setText("\n".join(file_names))
        def procesar_archivo():
            if not ubicacion_archivo.text().strip():
                labelRespuesta.setText("No se cargó ningún archivo.")
                labelRespuesta.setStyleSheet("color: red;")
                return
            idcompo = comboComponentes.currentData()

            labelRespuesta.setText("")
            botonAceptar.setEnabled(False)

            loading = LoadingView.mostrarLoading()

            thread = CargarPiezometrosCuerdaThread(idproyecto, ubicacion_archivo.text(), idcompo, tipo)
            SubirPiezometros._current_thread_cuerda = thread

            def on_finish(resultado):
                loading.close()
                botonAceptar.setEnabled(True)

                labelRespuesta.setText(resultado.get("mensaje", ""))
                labelRespuesta.setStyleSheet(f"color: {resultado.get('color', 'red')};")

                if resultado.get("ok"):
                    ubicacion_archivo.clear()

                    for item in resultado.get("equipos_data", []):
                        idinstrumento = item["idinstrumento"]
                        idcomponente = item["idcomponente"]
                        nombrezona = item["nombrezona"]
                        piezocu = item["piezocu"]
                        piezometros_visor = item["piezometros_visor"]

                        treewidgetdatos = main.findChild(QTreeWidget, "tree_actual_datos")
                        treewidgetvisor = main.findChild(QTreeWidget, "tree_actual_visor")
                        treewidgetpiezo = main.findChild(QTreeWidget, "tree_actual_piezometros")
                        TreeCheckbox.eliminarCheckbox(treewidgetdatos, "Piezómetros Cuerda Vibrante", idinstrumento, "piezometrocuerda")
                        TreeCheckbox.eliminarCheckbox(treewidgetvisor, "Piezómetros Cuerda Vibrante", idinstrumento, "piezometrocuerda")
                        TreeCheckbox.eliminarCheckbox(treewidgetpiezo, "Piezómetros Cuerda Vibrante", idinstrumento, "piezometrocuerda")

                        if piezocu:
                            TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetdatos, nombrezona, idcomponente, idproyecto, "Piezómetros Cuerda Vibrante", "3", piezocu, "piezometrocuerda")
                            TreeCheckbox.crearNuevoGrupoCheckboxesDoble(treewidgetpiezo, nombrezona, idcomponente, idproyecto, "Piezómetros Cuerda Vibrante", "1", piezocu, "piezometrocuerda")
                            if piezometros_visor:
                                TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetvisor, nombrezona, idcomponente, idproyecto, "Piezómetros Cuerda Vibrante", "4", piezometros_visor, "piezometrocuerda", "SI")

                SubirPiezometros._current_thread_cuerda = None

            thread.task_finishCuerda.connect(on_finish, Qt.ConnectionType.QueuedConnection)
            thread.finished.connect(thread.deleteLater)
            thread.start()
            loading.exec()

        botonSubir.clicked.connect(cargar_archivo)
        botonAceptar.clicked.connect(procesar_archivo)
        dialogo.exec()
    
   
    def registrarDataPiezometrosCuerda(proyectoid, ubicacion, idcomponente):
        erroneos = []
        data = []
        equipos = []
        respuesta = False
        
        archivos = ubicacion.split("\n")
        
        for file_name in archivos:
            file_name = file_name.strip()
            if not file_name or not file_name.endswith('.xlsx'):
                continue
            
            try:
                print("Iniciando Lectura de Encabezado")
                # 1) Leer el encabezado COMPLETO
                df_header = pd.read_excel(file_name, header=None, nrows=1, skiprows=13, engine='openpyxl')
                encabezados_archivo = [str(col).strip() for col in df_header.iloc[0]]
                
                print(f"Encabezados encontrados: {encabezados_archivo}")

                # 2) Mapeo flexible de columnas
                posiciones = {}
                faltantes = []
                
                # Columnas obligatorias con posibles variantes
                mapeo_columnas = {
                    'Fecha': ['Fecha'],
                    'Hora': ['Hora'],
                    'Frecuencia': ['Frecuencia (digits)', 'Frecuencia (Dg)', 'Frecuencia (kPa)', 'Frecuencia'],
                    'Temperatura': ['Temperatura (°C)', 'Temperatura'],
                    'mca': ['mca (m)', 'mca'],
                    'Observación': ['Observación', 'Observacion'],
                }
                
                # Buscar cada columna por sus posibles nombres
                for key, variantes in mapeo_columnas.items():
                    encontrada = False
                    for variante in variantes:
                        if variante in encabezados_archivo:
                            posiciones[key] = encabezados_archivo.index(variante)
                            encontrada = True
                            break
                    if not encontrada:
                        faltantes.append(key)
                
                # 3) Buscar columna de presión (mb o kPa)
                if 'Presión (mb)' in encabezados_archivo:
                    posiciones['Presión'] = encabezados_archivo.index('Presión (mb)')
                    unidadpresion = "mb"
                elif 'Presión (kPa)' in encabezados_archivo:
                    posiciones['Presión'] = encabezados_archivo.index('Presión (kPa)')
                    unidadpresion = "kPa"
                else:
                    # La presión es opcional, poner en 0 si no existe
                    posiciones['Presión'] = None
                    unidadpresion = "mb"

                print(f"Posiciones encontradas: {posiciones}")
                print(f"Columnas faltantes: {faltantes}")

                # Si falta alguna columna obligatoria (excepto Presión)
                if faltantes:
                    print(f"Archivo inválido por columnas faltantes: {faltantes}")
                    erroneos.append(file_name.split("/")[-1])
                    continue

                wb = load_workbook(file_name, data_only=True)
                hoja = wb.active
                
                # obtener data general
                nombrepiezo = hoja["B8"].value
                seriepiezo = hoja["B9"].value
                coordeste = hoja["B10"].value
                coordnorte = hoja["B11"].value
                instalacion = hoja["B12"].value
                fundacion = hoja["B13"].value
                superficie = hoja["E8"].value
                inclinacion = hoja["E9"].value
                azimuth = hoja["E10"].value
                cf = hoja["E11"].value
                tk = hoja["E12"].value
                frecuenciaini = hoja["E13"].value
                temperaini = hoja["G8"].value
                presionini = hoja["G9"].value
                conversion = hoja["G10"].value
                constantea = hoja["G11"].value
                constanteb = hoja["G12"].value
                constantec = hoja["G13"].value
                comentario = ""
                wb.close()
                
                # Validar datos básicos
                if pd.isna(nombrepiezo) or proyectoid == 0 or not idcomponente:
                    print(f"Datos básicos inválidos")
                    erroneos.append(file_name.split("/")[-1])
                    continue
                
                idpiezometro = None
                respu, info = PiezometroController.ctrlComprobarExisteNombrePiezometro(proyectoid, nombrepiezo, "Automatizado")
                
                if respu:
                    idpiezometro = info[0]
                    if coordeste and coordnorte and float(coordeste) != 0 and float(coordnorte) != 0:
                        datos = (seriepiezo, coordeste, coordnorte, instalacion, fundacion, inclinacion, azimuth, cf, tk, frecuenciaini, temperaini, presionini, constantea, constanteb, constantec, conversion, comentario, idpiezometro)
                        response = PiezometroController.ctrlActualizarPiezometroCuerdaFormato(datos)
                    print("Piezómetro existente actualizado")
                else:
                    print("Creando nuevo piezómetro")
                    if pd.isna(superficie):
                        print("Superficie es NA, saltando archivo")
                        continue
                    
                    # Validar y convertir valores numéricos
                    coordnorte = float(coordnorte) if not pd.isna(coordnorte) else 0
                    coordeste = float(coordeste) if not pd.isna(coordeste) else 0
                    instalacion = float(instalacion) if not pd.isna(instalacion) else 0
                    fundacion = float(fundacion) if not pd.isna(fundacion) else 0
                    inclinacion = float(inclinacion) if not pd.isna(inclinacion) else 90
                    azimuth = float(azimuth) if not pd.isna(azimuth) else 0
                    conversion = float(conversion) if not pd.isna(conversion) else 0
                    cf = float(cf) if not pd.isna(cf) else 0
                    tk = float(tk) if not pd.isna(tk) else 0
                    
                    fecha = f"{datetime.now().strftime('%Y-%m-%d')} 00:00:00"
                    datos = (proyectoid, nombrepiezo, seriepiezo, coordeste, coordnorte, instalacion, fundacion, inclinacion, azimuth, cf, tk, frecuenciaini, temperaini, presionini, unidadpresion, constantea, constanteb, constantec, conversion, comentario)
                    respues = PiezometroController.ctrlRegistrarPiezometroCuerdaFormato(idcomponente, datos, fecha, superficie, "PCV")
                    if respues:
                        idpiezometro = respues
                        print(f"Nuevo piezómetro creado con ID: {idpiezometro}")

                if idpiezometro is not None:
                    print("Leyendo datos del archivo")
                    # 4) Leer toda la data
                    df_full = pd.read_excel(file_name, header=None, skiprows=14, engine='openpyxl')
                    
                    # Verificar que tenemos suficientes columnas
                    max_col = max([v for v in posiciones.values() if v is not None])
                    if df_full.shape[1] <= max_col:
                        print(f"Error: El archivo no tiene suficientes columnas")
                        erroneos.append(file_name.split("/")[-1])
                        continue
                    
                    # Construir DataFrame con las posiciones encontradas
                    df_dict = {
                        'fecha':       df_full.iloc[:, posiciones['Fecha']],
                        'hora':        df_full.iloc[:, posiciones['Hora']],
                        'frecuencia':  df_full.iloc[:, posiciones['Frecuencia']],
                        'temperatura': df_full.iloc[:, posiciones['Temperatura']],
                        'mca':         df_full.iloc[:, posiciones['mca']],
                        'observacion': df_full.iloc[:, posiciones['Observación']],
                    }
                    
                    # Agregar presión solo si existe
                    if posiciones['Presión'] is not None:
                        df_dict['presion'] = df_full.iloc[:, posiciones['Presión']]
                    else:
                        df_dict['presion'] = 0  # Valor por defecto
                    
                    df = pd.DataFrame(df_dict)
                    
                    print(f"DataFrame creado con {len(df)} filas")
                    
                    filas_procesadas = 0
                    for _, row in df.iterrows():
                        fecha = row['fecha']
                        hora = row['hora']
                        mca = row['mca']
                        observacion = row['observacion']
                        
                        if pd.isna(fecha) or pd.isna(mca):
                            continue
                        
                        # Procesar fecha
                        if isinstance(fecha, (pd.Timestamp, datetime)):
                            fecha = fecha.date().strftime('%Y-%m-%d')
                        elif isinstance(fecha, str):
                            fecha = MetodosGenerales.validarFormatoFecha(fecha)
                            if fecha is None:
                                continue
                        else:
                            continue
                        
                        # Procesar hora
                        if isinstance(hora, (pd.Timestamp, datetime)):
                            hora = hora.time().strftime('%H:%M:%S')
                        elif isinstance(hora, time):
                            hora = hora.strftime('%H:%M:%S')
                        elif isinstance(hora, str):
                            hora = MetodosGenerales.validarFormatoHora(hora) or "00:00:00"
                        else:
                            hora = "00:00:00"
                        
                        try:
                            mca = float(mca)
                        except (ValueError, TypeError):
                            continue
                        
                        frecu = float(row['frecuencia']) if not pd.isna(row['frecuencia']) else 0
                        tempe = float(row['temperatura']) if not pd.isna(row['temperatura']) else 0
                        presio = float(row['presion']) if not pd.isna(row['presion']) else 0
                        observa = "" if pd.isna(observacion) else str(observacion).strip()
                        
                        data.append((idpiezometro, fecha, hora, frecu, tempe, presio, mca, observa))
                        filas_procesadas += 1
                    
                    print(f"Filas procesadas: {filas_procesadas}")
                    
                    if data:
                        respon = PiezometroController.ctrlGuardarPiezometrosCuerdaCalculada(proyectoid, data, False)
                        if respon:
                            equipos.append(idpiezometro)
                            respuesta = True
                            print(f"Data guardada exitosamente")
                            # Limpiar data para siguiente archivo
                            data = []
                        else:
                            print("Error al guardar data")
                            erroneos.append(file_name.split("/")[-1])
                    else:
                        print("No hay data para guardar")
                        erroneos.append(file_name.split("/")[-1])
                else:
                    print("idpiezometro es None")
                    erroneos.append(file_name.split("/")[-1])
                    
            except Exception as e:
                print(f"Excepción: {type(e).__name__}: {str(e)}")
                import traceback
                traceback.print_exc()
                erroneos.append(file_name.split("/")[-1])
        
        print(f"Proceso finalizado. Respuesta: {respuesta}, Equipos: {equipos}, Erróneos: {erroneos}")
        return respuesta, equipos, erroneos 


    def cargarPiezometrosCasagrande(main, proyectoid):
        loaderLoading = QUiLoader()        
        ui_file_path = resource_path("ui/datapiezometromanual.ui")
        ui_file = loaderLoading.load(ui_file_path, None)
        dialogoPiezomanual = QDialog()
        dialogoPiezomanual.setWindowTitle("Data Piezómetros Casagrande")
        layout_piezomanual = QVBoxLayout()
        layout_piezomanual.addWidget(ui_file)
        dialogoPiezomanual.setLayout(layout_piezomanual)
        # tools
        comboPiezometros = dialogoPiezomanual.findChild(QComboBox, "combo_piezometros")
        tabladata = dialogoPiezomanual.findChild(QTableWidget, "table_piezometros_data")
        botonGuardarData = dialogoPiezomanual.findChild(QPushButton, "btn_guardar_piezometros")
        lblrespuesta = dialogoPiezomanual.findChild(QLabel, "label_mensaje_estado")
        # agregar una celda
        tabladata.insertRow(tabladata.rowCount())
        # cargar piezómetros en el combo
        listapiezometros = PiezometroController.ctrlListarPiezometrosManuales(proyectoid)
        if listapiezometros is not None:
            for fila in listapiezometros:
                comboPiezometros.addItem(str(fila[2]), fila[0])
        else:
            comboPiezometros.addItem("Sin Piezómetros")
            comboPiezometros.setEnabled(False)
        configurar_tabla_para_pegado(tabladata)
        # GUARDAR DATA
        def guardarPiezometrosManualesTabla():
            idpiezometro = comboPiezometros.currentData()
            filas = tabladata.rowCount()
            if filas > 0 and proyectoid != 0:
                data = []
                estado = False
                for row in range(filas):
                    datosfila = []
                    datosfila.append(idpiezometro)
                    fila_valida = False
                    c = 0
                    for column in range(tabladata.columnCount()):
                        item = tabladata.item(row, column)
                        valor = item.text().strip() if item else ""
                        mensaje = "Registrado correctamente."
                        if valor != "":
                            fila_valida = True
                            if column == 0:  # Validación de la fecha
                                valor = MetodosGenerales.validarFormatoFecha(valor)
                                if not valor:
                                    mensaje = "La fecha no tiene un formato adecuado."
                                    fila_valida = False
                                    break
                            elif column == 1:  # Validación de la hora
                                valor = MetodosGenerales.validarFormatoHora(valor)
                                if not valor:
                                    mensaje = "La hora no tiene un formato adecuado."
                                    fila_valida = False
                                    break
                            elif column == 2:  # Validación numérica de medidas
                                if not MetodosGenerales.validarEsNumero(valor):
                                    mensaje = "Las medidas deben ser numéricas."
                                    fila_valida = False
                                    break
                            datosfila.append(valor)
                        else:
                            c = c + 1
                            if column == 1:
                                valor = "00:00:00"
                                datosfila.append(valor)
                            elif column == 3:
                                valor = ""
                                datosfila.append(valor)
                            else:
                                fila_valida = False
                                mensaje = "Algunos campos están vacíos."
                    # Guardar la fila solo si es válida y tiene 4 columnas
                    if fila_valida and len(datosfila) == 5:
                        data.append(datosfila)
                        estado = True
                    else:
                        # Si todas son vacias omitir
                        if c == 4:
                            estado = True
                        else:
                            estado = False
                            break                    
                if estado:
                    respuesta = PiezometroController.ctrlGuardarPiezometrosManualesTabla(proyectoid, data)
                    if respuesta:
                        lblrespuesta.setText(mensaje)
                        lblrespuesta.setStyleSheet("color: green;")
                        # Limpiar filas tabla
                        tabladata.setRowCount(0)
                        tabladata.insertRow(0)
                        # actualizar árbol checkbox
                        data = PiezometroController.ctrlTraerDataPiezometro(idpiezometro, "PIEZOMETROMANUAL")
                        if data:
                            idinstrumento, idcomponente, nombrezona = data[0], data[1], data[2]
                            treewidgetdatos = main.findChild(QTreeWidget, "tree_actual_datos")
                            treewidgetvisor = main.findChild(QTreeWidget, "tree_actual_visor")
                            treewidgetpiezo = main.findChild(QTreeWidget, "tree_actual_piezometros")
                            TreeCheckbox.eliminarCheckbox(treewidgetdatos, "Piezómetros Casagrande", idinstrumento, "piezometromanual")
                            TreeCheckbox.eliminarCheckbox(treewidgetvisor, "Piezómetros Casagrande", idinstrumento, "piezometromanual")
                            TreeCheckbox.eliminarCheckbox(treewidgetpiezo, "Piezómetros Casagrande", idinstrumento, "piezometromanual")
                            # Crear piezometro manual en nuevo componente
                            piezocu = InterfazController.ctrlListarComponentePiezometroManual(idinstrumento)
                            if piezocu:
                                TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetdatos, nombrezona, idcomponente, proyectoid, "Piezómetros Casagrande", "4", piezocu, "piezometromanual")
                                TreeCheckbox.crearNuevoGrupoCheckboxesDoble(treewidgetpiezo, nombrezona, idcomponente, proyectoid, "Piezómetros Casagrande", "2", piezocu, "piezometromanual")
                                fechas = InterfazController.ctrlListarFechasPiezometroCodigo("Manual", idcomponente, idinstrumento, proyectoid)
                                if fechas:
                                    ultima_fecha = fechas[-1][0]
                                    piezo = piezocu[0]
                                    piezometros = [(piezo[0], piezo[1], piezo[2], piezo[3], piezo[4], piezo[5], piezo[6], ultima_fecha)]
                                    TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetvisor, nombrezona, idcomponente, proyectoid, "Piezómetros Casagrande", "5", piezometros, "piezometromanual", "SI")
                    else:
                        lblrespuesta.setText(f"Enla fila {len(data) + 1}: {mensaje}")
                        lblrespuesta.setStyleSheet("color: red;")
                else:
                    lblrespuesta.setText(f"Enla fila {len(data) + 1}: {mensaje}")
                    lblrespuesta.setStyleSheet("color: orange;")  
        # Conectar señal 
        botonGuardarData.clicked.connect(guardarPiezometrosManualesTabla)
        dialogoPiezomanual.exec()
    
    def cargarDataFormatosCasagrande(main, idproyecto):
        loader = QUiLoader()
        ui_file_path = resource_path("ui/cargardataformato.ui")
        ui_file = loader.load(ui_file_path, None)
        dialogo = QDialog()
        dialogo.setWindowTitle("Data Piezómetros casagrande")
        layout_procesar_data = QVBoxLayout()
        layout_procesar_data.addWidget(ui_file)
        dialogo.setLayout(layout_procesar_data)
        ruta = "resources/iconos/fontawesome/solid/file-arrow-up.svg"
        botonSubir = dialogo.findChild(QPushButton, "btn_cargar_archivo")
        cargarIcono(botonSubir, ruta)
        ubicacion_archivo = dialogo.findChild(QLineEdit, "input_archivo")
        ubicacion_archivo.setReadOnly(True)
        comboComponentes = dialogo.findChild(QComboBox, "combo_componentes")
        labelRespuesta = dialogo.findChild(QLabel, "label_mensaje")
        botonAceptar = dialogo.findChild(QPushButton, "btn_aceptar")
        componentes = ProyectoController.ctrlObtenerComponentesProyecto(idproyecto)
        if len(componentes) > 0:
            for fila in componentes:
                comboComponentes.addItem(str(fila[2]), fila[0])
            comboComponentes.setEnabled(True)
        else:
            comboComponentes.addItem("Sin Componentes")
            comboComponentes.setEnabled(False)
            botonAceptar.setEnabled(False)
        def cargar_archivo():
            file_names, _ = QFileDialog.getOpenFileNames(None, "Cargar Archivos", "", "Archivos Excel (*.xlsx)")
            if file_names:
                ubicacion_archivo.setText("\n".join(file_names))
        def procesar_archivo():
            if not ubicacion_archivo.text().strip():
                labelRespuesta.setText("No se cargó ningún archivo.")
                labelRespuesta.setStyleSheet("color: red;")
                return
            idcompo = comboComponentes.currentData()

            labelRespuesta.setText("")
            botonAceptar.setEnabled(False)

            loading = LoadingView.mostrarLoading()

            thread = CargarPiezometrosCasagrandeThread(idproyecto, ubicacion_archivo.text(), idcompo)
            SubirPiezometros._current_thread_casagrande = thread

            def on_finish(resultado):
                loading.close()
                botonAceptar.setEnabled(True)

                labelRespuesta.setText(resultado.get("mensaje", ""))
                labelRespuesta.setStyleSheet(f"color: {resultado.get('color', 'red')};")

                if resultado.get("ok"):
                    ubicacion_archivo.clear()

                    for item in resultado.get("equipos_data", []):
                        idinstrumento = item["idinstrumento"]
                        idcomponente = item["idcomponente"]
                        nombrezona = item["nombrezona"]
                        piezocu = item["piezocu"]
                        piezometros_visor = item["piezometros_visor"]

                        treewidgetdatos = main.findChild(QTreeWidget, "tree_actual_datos")
                        treewidgetvisor = main.findChild(QTreeWidget, "tree_actual_visor")
                        treewidgetpiezo = main.findChild(QTreeWidget, "tree_actual_piezometros")
                        TreeCheckbox.eliminarCheckbox(treewidgetdatos, "Piezómetros Casagrande", idinstrumento, "piezometromanual")
                        TreeCheckbox.eliminarCheckbox(treewidgetvisor, "Piezómetros Casagrande", idinstrumento, "piezometromanual")
                        TreeCheckbox.eliminarCheckbox(treewidgetpiezo, "Piezómetros Casagrande", idinstrumento, "piezometromanual")

                        if piezocu:
                            TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetdatos, nombrezona, idcomponente, idproyecto, "Piezómetros Casagrande", "4", piezocu, "piezometromanual")
                            TreeCheckbox.crearNuevoGrupoCheckboxesDoble(treewidgetpiezo, nombrezona, idcomponente, idproyecto, "Piezómetros Casagrande", "2", piezocu, "piezometromanual")
                            if piezometros_visor:
                                TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetvisor, nombrezona, idcomponente, idproyecto, "Piezómetros Casagrande", "5", piezometros_visor, "piezometromanual", "SI")

                SubirPiezometros._current_thread_casagrande = None

            thread.task_finishCasagrande.connect(on_finish, Qt.ConnectionType.QueuedConnection)
            thread.finished.connect(thread.deleteLater)
            thread.start()
            loading.exec()

        botonSubir.clicked.connect(cargar_archivo)
        botonAceptar.clicked.connect(procesar_archivo)
        dialogo.exec()
    
    def registrarDataPiezometrosManuales(proyectoid, ubicacion, idcomponente):
        erroneos = []
        data = []
        equipos = []
        respuesta = False
        
        archivos = ubicacion.split("\n")
        
        for file_name in archivos:
            file_name = file_name.strip()
            if not file_name or not file_name.endswith('.xlsx'):
                continue
                
            try:
                print(f"Iniciando Lectura de Encabezado Casagrande: {file_name}")
                # 1) Leer el encabezado COMPLETO (en el formato manual suele estar en la fila 21, skiprows=20)
                df_header = pd.read_excel(file_name, header=None, nrows=1, skiprows=20, engine='openpyxl')
                encabezados_archivo = [str(col).strip() for col in df_header.iloc[0]]
                
                print(f"Encabezados encontrados: {encabezados_archivo}")

                # 2) Mapeo flexible de columnas
                posiciones = {}
                faltantes = []
                
                # Columnas obligatorias con posibles variantes
                mapeo_columnas = {
                    'Fecha': ['Fecha'],
                    'Hora': ['Hora'],
                    'Nivel': ['Nivel Piezométrico (m)', 'Nivel Piezometrico (m)', 'Nivel (m)', 'Nivel Piezométrico', 'Nivel'],
                    'Observación': ['Observación', 'Observacion', 'Observaciones']
                }
                
                # Buscar cada columna por sus posibles nombres
                for key, variantes in mapeo_columnas.items():
                    encontrada = False
                    for variante in variantes:
                        if variante in encabezados_archivo:
                            posiciones[key] = encabezados_archivo.index(variante)
                            encontrada = True
                            break
                    if not encontrada:
                        faltantes.append(key)

                print(f"Posiciones encontradas: {posiciones}")
                print(f"Columnas faltantes: {faltantes}")

                # 3) Si falta alguna columna obligatoria, el archivo es inválido
                if faltantes:
                    print(f"Archivo inválido por columnas faltantes: {faltantes}")
                    erroneos.append(file_name.split("/")[-1])
                    continue

                wb = load_workbook(file_name, data_only=True)
                hoja = wb.active
                
                # Obtener data general
                nombrepiezo = hoja["C10"].value
                codigopiezo = hoja["C11"].value
                cotafondo = hoja["C12"].value
                fundacion = hoja["C13"].value
                coordeste = hoja["C14"].value
                coordnorte = hoja["C15"].value
                superficie = hoja["C16"].value
                inclinacion = hoja["C17"].value
                azimuth = hoja["C18"].value
                stickup = hoja["C19"].value
                comentario = hoja["C20"].value
                wb.close()
                
                # Validar datos básicos
                if pd.isna(nombrepiezo) or proyectoid == 0 or not idcomponente:
                    print("Datos básicos inválidos (Falta nombre, proyecto o componente)")
                    erroneos.append(file_name.split("/")[-1])
                    continue
                
                idpiezometro = None
                respu, info = PiezometroController.ctrlComprobarExisteNombrePiezometro(proyectoid, nombrepiezo, "Manual")
                
                if respu:
                    idpiezometro = info[0]
                    if coordeste and coordnorte and float(coordeste) != 0 and float(coordnorte) != 0:
                        datos = (codigopiezo, coordnorte, coordeste, cotafondo, fundacion, inclinacion, azimuth, stickup, comentario, idpiezometro)
                        response = PiezometroController.ctrlActualizarPiezometroManualFormato(datos)
                    print("Piezómetro Casagrande existente actualizado")
                else:
                    print("Creando nuevo Piezómetro Casagrande")
                    if pd.isna(superficie):
                        print("Superficie es NA, saltando archivo")
                        continue
                        
                    # Validar y convertir valores numéricos
                    coordnorte = float(coordnorte) if not pd.isna(coordnorte) else 0
                    coordeste = float(coordeste) if not pd.isna(coordeste) else 0
                    cotafondo = float(cotafondo) if not pd.isna(cotafondo) else 0
                    fundacion = float(fundacion) if not pd.isna(fundacion) else 0
                    inclinacion = float(inclinacion) if not pd.isna(inclinacion) else 90
                    azimuth = float(azimuth) if not pd.isna(azimuth) else 0
                    stickup = float(stickup) if not pd.isna(stickup) else 0
                    
                    fecha = f"{datetime.now().strftime('%Y-%m-%d')} 00:00:00"
                    datos = (proyectoid, nombrepiezo, codigopiezo, coordnorte, coordeste, cotafondo, fundacion, stickup, inclinacion, azimuth, comentario)
                    respues = PiezometroController.ctrlRegistrarPiezometroManualFormato(idcomponente, datos, fecha, superficie, "PVC")
                    
                    if respues:
                        idpiezometro = respues
                        print(f"Nuevo piezómetro manual creado con ID: {idpiezometro}")

                if idpiezometro is not None:
                    print("Leyendo datos del archivo")
                    # 4) Leer toda la data
                    df_full = pd.read_excel(file_name, header=None, skiprows=21, engine='openpyxl')
                    
                    # Verificar que tenemos suficientes columnas
                    max_col = max([v for v in posiciones.values() if v is not None])
                    if df_full.shape[1] <= max_col:
                        print("Error: El archivo no tiene suficientes columnas")
                        erroneos.append(file_name.split("/")[-1])
                        continue
                    
                    # Construir DataFrame con las posiciones encontradas
                    df = pd.DataFrame({
                        'fecha':       df_full.iloc[:, posiciones['Fecha']],
                        'hora':        df_full.iloc[:, posiciones['Hora']],
                        'nivel':       df_full.iloc[:, posiciones['Nivel']],
                        'observacion': df_full.iloc[:, posiciones['Observación']],
                    })
                    
                    print(f"DataFrame creado con {len(df)} filas")
                    
                    filas_procesadas = 0
                    for _, row in df.iterrows():
                        fecha = row['fecha']
                        hora = row['hora']
                        nivel = row['nivel']
                        observacion = row['observacion']
                        
                        if pd.isna(fecha) or pd.isna(nivel):
                            continue
                            
                        # Procesar fecha
                        if isinstance(fecha, (pd.Timestamp, datetime)):
                            fecha = fecha.date().strftime('%Y-%m-%d')
                        elif isinstance(fecha, str):
                            fecha = MetodosGenerales.validarFormatoFecha(fecha)
                            if fecha is None:
                                continue
                        else:
                            continue
                            
                        # Procesar hora
                        if isinstance(hora, (pd.Timestamp, datetime)):
                            hora = hora.time().strftime('%H:%M:%S')
                        elif isinstance(hora, time):
                            hora = hora.strftime('%H:%M:%S')
                        elif isinstance(hora, str):
                            hora = MetodosGenerales.validarFormatoHora(hora) or "00:00:00"
                        else:
                            hora = "00:00:00"
                            
                        try:
                            nivel = float(nivel)
                        except (ValueError, TypeError):
                            continue
                            
                        observa = "" if pd.isna(observacion) else str(observacion).strip()
                        
                        data.append((idpiezometro, fecha, hora, nivel, observa))
                        filas_procesadas += 1
                        
                    print(f"Filas procesadas: {filas_procesadas}")
                    
                    if data:
                        respon = PiezometroController.ctrlGuardarPiezometrosManualesTabla(proyectoid, data)
                        if respon:
                            equipos.append(idpiezometro)
                            respuesta = True
                            print("Data guardada exitosamente")
                            # IMPORTANTE: Limpiar el arreglo data para el siguiente archivo
                            data = []
                        else:
                            print("Error al guardar data en la BD")
                            erroneos.append(file_name.split("/")[-1])
                    else:
                        print("No hay data válida para guardar")
                        erroneos.append(file_name.split("/")[-1])
                else:
                    print("idpiezometro es None, fallo la creación/lectura")
                    erroneos.append(file_name.split("/")[-1])
                    
            except Exception as e:
                print(f"Excepción Casagrande: {type(e).__name__}: {str(e)}")
                import traceback
                traceback.print_exc()
                erroneos.append(file_name.split("/")[-1])
                
        print(f"Proceso finalizado. Respuesta: {respuesta}, Equipos: {equipos}, Erróneos: {erroneos}")
        return respuesta, equipos, erroneos


    def dialogoNuevaCotaPiezometrica(proyectoid):
        loaderLoading = QUiLoader()        
        ui_file_path = resource_path("ui/datacotapiezometrica.ui")
        ui_file = loaderLoading.load(ui_file_path, None)
        dialogo = QDialog()
        dialogo.setWindowTitle("Data Cotas Piezométricas")
        layout_piezo = QVBoxLayout()
        layout_piezo.addWidget(ui_file)
        dialogo.setLayout(layout_piezo)
        # tools
        comboPiezometros = dialogo.findChild(QComboBox, "combo_piezometros")
        tabladata = dialogo.findChild(QTableWidget, "table_cotas")
        botonGuardar = dialogo.findChild(QPushButton, "btn_guardar")
        botonCancelar = dialogo.findChild(QPushButton, "btn_cancelar")
        lblrespuesta = dialogo.findChild(QLabel, "label_mensaje")
        # agregar una celda
        tabladata.insertRow(tabladata.rowCount())
        # cargar piezómetros en el combo
        listapiezocuerda = PiezometroController.ctrlListarPiezometrosCuerda(proyectoid)
        listapiezomanual = PiezometroController.ctrlListarPiezometrosManuales(proyectoid)
        if listapiezocuerda is not None or listapiezomanual is not None:
            if listapiezocuerda is not None:
                for fila in listapiezocuerda:
                    comboPiezometros.addItem(str(fila[3]), (fila[0], "PCV"))
            if listapiezomanual is not None:
                for fila in listapiezomanual:
                    comboPiezometros.addItem(str(fila[2]), (fila[0], "PVC"))
        else:
            comboPiezometros.addItem("Sin Piezómetros")
            comboPiezometros.setEnabled(False)
            botonGuardar.setEnabled(False)
        configurar_tabla_para_pegado(tabladata)
        # GUARDAR DATA
        def guardarCotasTabla():
            infopiezometro = comboPiezometros.currentData()
            idpiezometro = infopiezometro[0]
            tipopiezometro = infopiezometro[1]
            filas = tabladata.rowCount()
            if filas > 0 and proyectoid is not None:
                data = []
                estado = False
                for row in range(filas):
                    datosfila = []
                    datosfila.append(idpiezometro)
                    datosfila.append(tipopiezometro)
                    fila_valida = False
                    c = 0
                    for column in range(tabladata.columnCount()):
                        item = tabladata.item(row, column)
                        valor = item.text().strip() if item else ""
                        mensaje = "Registrado correctamente."
                        if valor != "":
                            fila_valida = True
                            if column == 0:  # Validación de la fecha
                                valor = MetodosGenerales.validarFormatoFecha(valor)
                                if not valor:
                                    mensaje = "La fecha no tiene un formato adecuado."
                                    fila_valida = False
                                    break
                            elif column == 1:  # Validación numérica de medidas
                                if not MetodosGenerales.validarEsNumero(valor):
                                    mensaje = "Las cotas deben ser numéricas."
                                    fila_valida = False
                                    break
                            datosfila.append(valor)
                        else:
                            c = c + 1
                    # Guardar la fila solo si es válida y tiene 4 columnas
                    if fila_valida and len(datosfila) == 4:
                        data.append(datosfila)
                        estado = True
                    else:
                        # Si todas son vacias omitir
                        if c == 2:
                            estado = True
                        else:
                            estado = False
                            break                    
                if estado:
                    respuesta = PiezometroController.ctrlGuardarCotasPiezometricasTabla(data)
                    if respuesta:
                        lblrespuesta.setText(mensaje)
                        lblrespuesta.setStyleSheet("color: green;")
                        # Limpiar filas tabla
                        tabladata.setRowCount(0)
                        tabladata.insertRow(0)
                    else:
                        lblrespuesta.setText(f"Enla fila {len(data) + 1}: {mensaje}")
                        lblrespuesta.setStyleSheet("color: red;")
                else:
                    lblrespuesta.setText(f"Enla fila {len(data) + 1}: {mensaje}")
                    lblrespuesta.setStyleSheet("color: orange;")
        def cancelarCotas():
            dialogo.close()
        # Conectar señal 
        botonGuardar.clicked.connect(guardarCotasTabla)
        botonCancelar.clicked.connect(cancelarCotas)
        dialogo.exec()
    
    def cambiar_componente_piezocuerdas(idcomponente, idproyecto, treewidget, nombregrupo, tipogrupo, subgrupo, reiniciarvistas, vista="DATOS"):
        dialog = QDialog()
        dialog.setWindowTitle("Componente P. Cuerda Vibrante")
        layout = QFormLayout(dialog)
        # Campo componente
        label_titulo = QLabel("Componente:")
        combo_componente = QComboBox()
        label_mensaje = QLabel("")
        label_mensaje.setAlignment(Qt.AlignCenter)
        label_mensaje.setStyleSheet("QLabel { color: red; }")
        # cargar data componentes
        componentes = ProyectoController.ctrlObtenerComponentesProyecto(idproyecto)
        if componentes:
            for fila in componentes:
                combo_componente.addItem(str(fila[2]), fila[0])
            combo_componente.setCurrentIndex(combo_componente.findData(idcomponente))
        # Botones
        layout.addRow(label_titulo)
        layout.addRow(combo_componente)
        layout.addRow(label_mensaje)
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        # Cambiar los textos a español
        button_box.button(QDialogButtonBox.Save).setText("Guardar")
        button_box.button(QDialogButtonBox.Cancel).setText("Cancelar")
        layout.addWidget(button_box)
        # Conectar los botones a las funciones correspondientes
        def actualizarDatos():
            componente = combo_componente.currentData()
            nombrezona = combo_componente.currentText()
            if str(idcomponente) == str(componente):
                dialog.reject()
            else:
                respuesta = PiezometroController.ctrlCambiarComponentePiezometrosCuerda(idcomponente, componente)
                if respuesta:
                    dialog.reject()
                    # Eliminar cuerdas
                    TreeCheckbox.eliminarCheckboxGrupo(treewidget, idcomponente, nombregrupo, tipogrupo)
                    # Crear cuerdas en nuevo componente
                    if vista == "PIEZOMETROS":
                        TreeCheckbox.crearNuevoGrupoCheckboxesDoble(treewidget, nombrezona, componente, idproyecto, nombregrupo, tipogrupo, respuesta, subgrupo)
                    else:
                        TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidget, nombrezona, componente, idproyecto, nombregrupo, tipogrupo, respuesta, subgrupo)
                    reiniciarvistas("Piezómetro")
                else:
                    label_mensaje.setText("Error al cambiar de componente.")
        button_box.accepted.connect(actualizarDatos)
        button_box.rejected.connect(dialog.reject)
        # Mostrar el diálogo
        dialog.setLayout(layout)
        dialog.exec()
    
    def eliminar_piezocuerdas(idproyecto, idzona, grupo, tipo, treewidget, reiniciarvistas):
        dlg = QMessageBox()
        dlg.setWindowTitle("Eliminar P. Cuerda Vibrante")
        dlg.setText(f"¿Está seguro eliminar todos los Piezómetros?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.button(QMessageBox.Yes).setText("Sí")
        dlg.button(QMessageBox.No).setText("No")
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            respuesta = PiezometroController.ctrlEliminarPiezometrosCuerda(idzona)
            if respuesta:
                delete = PiezometroController.ctrlEliminarDataPiezometrosCuerda(idproyecto, respuesta)
                if delete:
                    TreeCheckbox.eliminarCheckboxGrupo(treewidget, idzona, grupo, tipo)
                    reiniciarvistas("Piezómetro")
                else:
                    mostrar_mensaje("Eliminar Piezómetros", "Error al eliminar data Piezómetros.", "advertencia")
            else:
                mostrar_mensaje("Eliminar Piezómetros", "No se pudo eliminar los Piezómetros.", "advertencia")
    
    def actualizarPiezometroCuerda(idproyecto, idcomponente, idinstrumento, treewidget, nombregrupo, tipogrupo, subgrupo, reiniciarvistas, vista="DATOS"):
        loader = QUiLoader()
        ui_file_path = resource_path("ui/editarpiezometrocuerda.ui")
        ui_file = loader.load(ui_file_path, None)
        # Configurar el cuadro de diálogo
        dialog = QDialog()
        dialog.setWindowTitle("Actualizar Piezómetro Cuerda Vibrante")
        layout = QVBoxLayout()
        layout.addWidget(ui_file)
        dialog.setLayout(layout)
        # Obtener elementos para interactuar
        comboComponente = dialog.findChild(QComboBox, "cb_lista_componentes")
        nombrePiezo = dialog.findChild(QLineEdit, "input_nombre")
        serieSensor = dialog.findChild(QLineEdit, "input_serie_sensor")
        comboFormula = dialog.findChild(QComboBox, "combo_formula")
        botonFormula = dialog.findChild(QPushButton, "btn_formula")
        cargarIcono(botonFormula, ListaIconos.ICONOS["calculadora"])
        nortePiezo = dialog.findChild(QDoubleSpinBox, "input_norte")
        estePiezo = dialog.findChild(QDoubleSpinBox, "input_este")
        instalacionPiezo = dialog.findChild(QDoubleSpinBox, "input_cota_instalacion")
        fundacionPiezo = dialog.findChild(QDoubleSpinBox, "input_cota_fundacion")
        factorCalibracion = dialog.findChild(QDoubleSpinBox, "input_factor_calibracion")
        correccionTempe = dialog.findChild(QDoubleSpinBox, "input_correccion_temperatura")
        lecturaInicial = dialog.findChild(QDoubleSpinBox, "input_frecuencia_inicial")
        temperaInicial = dialog.findChild(QDoubleSpinBox, "input_tempeartura_inicial")
        presionInicial = dialog.findChild(QDoubleSpinBox, "input_presion_inicial")
        unidadLectura = dialog.findChild(QComboBox, "combo_unidad_frecuencia")
        constanteA = dialog.findChild(QDoubleSpinBox, "input_constante_a")
        constanteB = dialog.findChild(QDoubleSpinBox, "input_constante_b")
        constanteC = dialog.findChild(QDoubleSpinBox, "input_constante_c")
        inclinacionPiezo = dialog.findChild(QSpinBox, "input_inclinacion")
        azimutPiezo = dialog.findChild(QSpinBox, "input_azimut")
        factorConversion = dialog.findChild(QDoubleSpinBox, "input_factor_conversion")
        comboEstados = dialog.findChild(QComboBox, "cb_estados")
        comentarioPiezo = dialog.findChild(QTextEdit, "input_comentario")
        lblrespuesta = dialog.findChild(QLabel, "label_mensaje_error")
        botonguardar = dialog.findChild(QPushButton, "btn_guardar_nuevo")
        comboEstados.addItem("Operativo", 1)
        comboEstados.addItem("Inoperativo", 0)
        
        # cargar data componentes
        componentes = ProyectoController.ctrlObtenerComponentesProyecto(idproyecto)
        if componentes:
            for fila in componentes:
                comboComponente.addItem(str(fila[2]), fila[0])
        comboFormula.addItem("Sin Fórmula", 0)
        formulas = PiezometroController.ctrlTraerListaFormulas()
        if formulas:
            for fila in formulas:
                comboFormula.addItem(str(fila[1]), fila[0])
        # mostrar data Piezómetro Cuerda
        nombreactual = ""
        idpiezo = 0
        datapiezo = PiezometroController.ctrlObtenerInfoPiezometroCuerda(idinstrumento)
        if datapiezo:
            idpiezo = datapiezo[0]
            comboComponente.setCurrentIndex(comboComponente.findData(idcomponente))
            comboFormula.setCurrentIndex(comboFormula.findData(datapiezo[2]))
            nombrePiezo.setText(str(datapiezo[3]))
            nombreactual = str(datapiezo[3])
            serieSensor.setText(str(datapiezo[4]))
            estePiezo.setValue(datapiezo[5])
            nortePiezo.setValue(datapiezo[6])
            instalacionPiezo.setValue(datapiezo[7])
            fundacionPiezo.setValue(datapiezo[8])
            inclinacionPiezo.setValue(datapiezo[9])
            azimutPiezo.setValue(datapiezo[10])
            factorCalibracion.setValue(datapiezo[11])
            correccionTempe.setValue(datapiezo[12])
            lecturaInicial.setValue(datapiezo[13])
            temperaInicial.setValue(datapiezo[14])
            presionInicial.setValue(datapiezo[15])
            unidadLectura.setCurrentText(str(datapiezo[16]))
            constanteA.setValue(datapiezo[17])
            constanteB.setValue(datapiezo[18])
            constanteC.setValue(datapiezo[19])
            factorConversion.setValue(datapiezo[20])
            comentarioPiezo.setPlainText(datapiezo[21])
            comboEstados.setCurrentIndex(comboEstados.findData(datapiezo[23]))
        def actualizarPiezometro():
            componente = comboComponente.currentData()
            nombrezona = comboComponente.currentText()
            idformula = comboFormula.currentData()
            nombre = nombrePiezo.text()
            serie = serieSensor.text()
            norte = nortePiezo.value()
            este = estePiezo.value()
            instalacion = instalacionPiezo.value()
            fundacion = fundacionPiezo.value()
            inclinacion = inclinacionPiezo.value()
            azimut = azimutPiezo.value()
            calibracion = factorCalibracion.value()
            tempecorrec = correccionTempe.value()
            frecuenini = lecturaInicial.value()
            temperaini = temperaInicial.value()
            presionini = presionInicial.value()
            unidad = unidadLectura.currentText()
            variablea = constanteA.value()
            variableb = constanteB.value()
            variablec = constanteC.value()
            conversion = factorConversion.value()
            estado = comboEstados.currentData()
            comentario = comentarioPiezo.toPlainText()
            if nombre != "":
                datos = (idformula, nombre, serie, este, norte, instalacion, fundacion, inclinacion, azimut, calibracion, tempecorrec, frecuenini, temperaini, presionini, unidad, variablea, variableb, variablec, conversion, comentario, estado, idpiezo)
                data = (componente, nombre, estado, idinstrumento)
                respuesta = PiezometroController.ctrlActualizarPiezometroCuerda(datos, data)
                if respuesta:
                    dialog.close()
                    if str(idcomponente) == str(componente):
                        TreeCheckbox.actualizarTextoCheckboxEquipo(treewidget, idcomponente, nombregrupo, subgrupo, nombreactual, nombre)
                    else:
                        # Eliminar Piezómetro
                        TreeCheckbox.eliminarCheckbox(treewidget, nombregrupo, idinstrumento, subgrupo)
                        # Crear piezometro cuerda en nuevo componente
                        piezocu = InterfazController.ctrlListarComponentePiezometroCuerda(idinstrumento)
                        if piezocu:
                            if vista == "PIEZOMETROS":
                                TreeCheckbox.crearNuevoGrupoCheckboxesDoble(treewidget, nombrezona, componente, idproyecto, nombregrupo, tipogrupo, piezocu, subgrupo)
                            else:
                                TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidget, nombrezona, componente, idproyecto, nombregrupo, tipogrupo, piezocu, subgrupo)
                    reiniciarvistas("Piezómetro")
                else:
                    lblrespuesta.setText("¡Error al actualizar los datos!")
                    lblrespuesta.setStyleSheet("color: red;")
            else:
                lblrespuesta.setText("¡Algunos datos están vacíos!")
                lblrespuesta.setStyleSheet("color: orange;")
        # Inicializar botones
        lblrespuesta.setText("")
        botonguardar.clicked.connect(actualizarPiezometro)
        # mostrar dialogo
        dialog.exec()
    
    def eliminar_piezocuerda(idproyecto, idinstrumento, nombrepiezo, nombregrupo, tipolista, treewidget, reiniciarvistas):
        dlg = QMessageBox()
        dlg.setWindowTitle("Eliminar P. Cuerda Vibrante")
        dlg.setText(f"¿Está seguro eliminar el Piezómetro '{nombrepiezo}'?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.button(QMessageBox.Yes).setText("Sí")
        dlg.button(QMessageBox.No).setText("No")
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            respuesta = PiezometroController.ctrlEliminarCuerdaVibrante(idinstrumento)
            if respuesta:
                delete = PiezometroController.ctrlEliminarCuerdaVibranteData(idproyecto, respuesta)
                if delete:
                    TreeCheckbox.eliminarCheckbox(treewidget, nombregrupo, idinstrumento, tipolista)
                    reiniciarvistas("Piezómetro")
                else:
                    mostrar_mensaje("Eliminar Piezómetro", "Error al eliminar data del piezómetro.", "advertencia")
            else:
                mostrar_mensaje("Eliminar Piezómetro", "No se pudo eliminar el piezómetro.", "advertencia")
    
    def cambiar_componente_piezomanuales(idcomponente, idproyecto, treewidget, nombregrupo, tipogrupo, subgrupo, reiniciarvistas, vista="DATOS"):
        dialog = QDialog()
        dialog.setWindowTitle("Componente Piezómetros Casagrande")
        layout = QFormLayout(dialog)
        # Campo componente
        label_titulo = QLabel("Componente:")
        combo_componente = QComboBox()
        label_mensaje = QLabel("")
        label_mensaje.setAlignment(Qt.AlignCenter)
        label_mensaje.setStyleSheet("QLabel { color: red; }")
        # cargar data componentes
        componentes = ProyectoController.ctrlObtenerComponentesProyecto(idproyecto)
        if componentes:
            for fila in componentes:
                combo_componente.addItem(str(fila[2]), fila[0])
            combo_componente.setCurrentIndex(combo_componente.findData(idcomponente))
        # Botones
        layout.addRow(label_titulo)
        layout.addRow(combo_componente)
        layout.addRow(label_mensaje)
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        # Cambiar los textos a español
        button_box.button(QDialogButtonBox.Save).setText("Guardar")
        button_box.button(QDialogButtonBox.Cancel).setText("Cancelar")
        layout.addWidget(button_box)
        # Conectar los botones a las funciones correspondientes
        def actualizarDatos():
            componente = combo_componente.currentData()
            nombrezona = combo_componente.currentText()
            if str(idcomponente) == str(componente):
                dialog.reject()
            else:
                respuesta = PiezometroController.ctrlCambiarComponentePiezometrosManuales(idcomponente, componente)
                if respuesta:
                    dialog.reject()
                    # Eliminar cuerdas
                    TreeCheckbox.eliminarCheckboxGrupo(treewidget, idcomponente, nombregrupo, tipogrupo)
                    # Crear cuerdas en nuevo componente
                    if vista == "PIEZOMETROS":
                        TreeCheckbox.crearNuevoGrupoCheckboxesDoble(treewidget, nombrezona, componente, idproyecto, nombregrupo, tipogrupo, respuesta, subgrupo)
                    else:
                        TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidget, nombrezona, componente, idproyecto, nombregrupo, tipogrupo, respuesta, subgrupo)
                    reiniciarvistas("Piezómetro")
                else:
                    label_mensaje.setText("Error al cambiar de componente.")
        button_box.accepted.connect(actualizarDatos)
        button_box.rejected.connect(dialog.reject)
        # Mostrar el diálogo
        dialog.setLayout(layout)
        dialog.exec()
    
    def eliminar_piezomanuales(idproyecto, idzona, grupo, tipo, treewidget, reiniciarvistas):
        dlg = QMessageBox()
        dlg.setWindowTitle("Eliminar Piezómetros Casagrande")
        dlg.setText(f"¿Está seguro eliminar todos los Piezómetros?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.button(QMessageBox.Yes).setText("Sí")
        dlg.button(QMessageBox.No).setText("No")
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            respuesta = PiezometroController.ctrlEliminarPiezometrosManuales(idzona)
            if respuesta:
                delete = PiezometroController.ctrlEliminarDataPiezometrosManuales(idproyecto, respuesta)
                if delete:
                    TreeCheckbox.eliminarCheckboxGrupo(treewidget, idzona, grupo, tipo)
                    reiniciarvistas("Piezómetro")
                else:
                    mostrar_mensaje("Eliminar Piezómetros", "Error al eliminar data Piezómetros.", "advertencia")
            else:
                mostrar_mensaje("Eliminar Piezómetros", "No se pudo eliminar los Piezómetros.", "advertencia")
    
    def actualizarPiezometroManual(idproyecto, idcomponente, idinstrumento, treewidget, nombregrupo, tipogrupo, subgrupo, reiniciarvistas, vista="DATOS"):
        loader = QUiLoader()
        ui_file_path = resource_path("ui/editarpiezometromanual.ui")
        ui_file = loader.load(ui_file_path, None)
        # Configurar el cuadro de diálogo
        dialog = QDialog()
        dialog.setWindowTitle("Actualizar Piezómetro Casagrande")
        layout = QVBoxLayout()
        layout.addWidget(ui_file)
        dialog.setLayout(layout)
        # Obtener elementos para interactuar
        comboComponente = dialog.findChild(QComboBox, "cb_lista_componentes")
        nombrePiezo = dialog.findChild(QLineEdit, "input_nombre")
        codigoPiezo = dialog.findChild(QLineEdit, "input_codigo")
        nortePiezo = dialog.findChild(QDoubleSpinBox, "input_norte")
        estePiezo = dialog.findChild(QDoubleSpinBox, "input_este")
        elevacionPiezo = dialog.findChild(QDoubleSpinBox, "input_elevacion")
        fundacionPiezo = dialog.findChild(QDoubleSpinBox, "input_fundacion")
        stickupPiezo = dialog.findChild(QDoubleSpinBox, "input_stickup")
        inclinacionPiezo = dialog.findChild(QSpinBox, "input_inclinacion")
        azimutPiezo = dialog.findChild(QSpinBox, "input_azimut")
        comentarioPiezo = dialog.findChild(QTextEdit, "input_comentario")
        estado_piezomanual = dialog.findChild(QComboBox, "estado_piezomanual")
        estado_piezomanual.addItem("Operativo", 1)
        estado_piezomanual.addItem("Inoperativo", 0)
        lblrespuesta = dialog.findChild(QLabel, "label_mensaje_error")
        botonguardar = dialog.findChild(QPushButton, "btn_aceptar_nuevo")

        # cargar data componentes
        componentes = ProyectoController.ctrlObtenerComponentesProyecto(idproyecto)
        if componentes:
            for fila in componentes:
                comboComponente.addItem(str(fila[2]), fila[0])
            comboComponente.setEnabled(True)
        # mostrar data Piezómetro Cuerda
        nombreactual = ""
        idpiezo = 0
        datapiezo = PiezometroController.ctrlObtenerInfoPiezometroManual(idinstrumento)
        if datapiezo:
            idpiezo = datapiezo[0]
            comboComponente.setCurrentIndex(comboComponente.findData(idcomponente))
            nombrePiezo.setText(str(datapiezo[2]))
            nombreactual = str(datapiezo[2])
            codigoPiezo.setText(str(datapiezo[3]))
            estePiezo.setValue(datapiezo[4])
            nortePiezo.setValue(datapiezo[5])
            elevacionPiezo.setValue(datapiezo[6])
            fundacionPiezo.setValue(datapiezo[7])
            stickupPiezo.setValue(datapiezo[10])
            inclinacionPiezo.setValue(datapiezo[8])
            azimutPiezo.setValue(datapiezo[9])
            comentarioPiezo.setPlainText(str(datapiezo[11]))
            estado_piezomanual.setCurrentIndex(estado_piezomanual.findData(datapiezo[13]))
        def actualizarPiezometroManual():
            componente = comboComponente.currentData()
            nombrezona = comboComponente.currentText()
            nombre = nombrePiezo.text() 
            codigo = codigoPiezo.text()
            norte = nortePiezo.value()
            este = estePiezo.value()
            nivel = elevacionPiezo.value()
            fundacion = fundacionPiezo.value()
            stick = stickupPiezo.value()
            inclinacion = inclinacionPiezo.value()
            azimut = azimutPiezo.value()
            comentario = comentarioPiezo.toPlainText()
            estado = estado_piezomanual.currentData()
            if nombre != "":
                datos = (nombre, codigo, norte, este, nivel, fundacion, inclinacion, azimut, stick, comentario, estado, idpiezo)
                data = (componente, nombre, estado, idinstrumento)
                respuesta = PiezometroController.ctrlActualizarPiezometroManual(datos, data)
                if respuesta:
                    dialog.close()
                    if str(idcomponente) == str(componente):
                        TreeCheckbox.actualizarTextoCheckboxEquipo(treewidget, idcomponente, nombregrupo, subgrupo, nombreactual, nombre)
                    else:
                        # Eliminar Piezómetro
                        TreeCheckbox.eliminarCheckbox(treewidget, nombregrupo, idinstrumento, subgrupo)
                        # Crear piezometro manual en nuevo componente
                        piezocu = InterfazController.ctrlListarComponentePiezometroManual(idinstrumento)
                        if piezocu:
                            if vista == "PIEZOMETROS":
                                TreeCheckbox.crearNuevoGrupoCheckboxesDoble(treewidget, nombrezona, componente, idproyecto, nombregrupo, tipogrupo, piezocu, subgrupo)
                            else:
                                TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidget, nombrezona, componente, idproyecto, nombregrupo, tipogrupo, piezocu, subgrupo)
                    reiniciarvistas("Piezómetro")
                else:
                    lblrespuesta.setText("¡Error al guardar los datos!")
                    lblrespuesta.setStyleSheet("color: red;")
            else:
                lblrespuesta.setText("¡Algunos campos están vacíos!")
                lblrespuesta.setStyleSheet("color: red;")
        # Inicializar botones
        lblrespuesta.setText("")
        botonguardar.clicked.connect(actualizarPiezometroManual)
        # mostrar dialogo
        dialog.exec()
    
    def eliminar_piezomanual(idproyecto, idinstrumento, nombrepiezo, nombregrupo, tipolista, treewidget, reiniciarvistas):
        dlg = QMessageBox()
        dlg.setWindowTitle("Eliminar Piezómetro Casagrande")
        dlg.setText(f"¿Está seguro eliminar el Piezómetro '{nombrepiezo}'?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.button(QMessageBox.Yes).setText("Sí")
        dlg.button(QMessageBox.No).setText("No")
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            respuesta = PiezometroController.ctrlEliminarManualPiezometro(idinstrumento)
            if respuesta:
                delete = PiezometroController.ctrlEliminarPiezometroManualData(idproyecto, respuesta)
                if delete:
                    TreeCheckbox.eliminarCheckbox(treewidget, nombregrupo, idinstrumento, tipolista)
                    reiniciarvistas("Piezómetro")
                else:
                    mostrar_mensaje("Eliminar Piezómetro", "Error al eliminar data del piezómetro.", "advertencia")
            else:
                mostrar_mensaje("Eliminar Piezómetro", "No se pudo eliminar el piezómetro.", "advertencia")
    
    def mostrarDialogoFechasPiezometros(treewidget, idproyecto, idcomponente, idinstrumento, nombrecompo, nombrepiezo, fechamarcada, tipo, graficarnuevafechaspiezometros):
        loaderLoading = QUiLoader()
        ui_file_path = resource_path("ui/arbolcheckbox.ui")
        ui_file = loaderLoading.load(ui_file_path, None)
        dialogo = QDialog()
        dialogo.setWindowTitle("Lista de fechas")
        layout = QVBoxLayout()
        layout.addWidget(ui_file)
        dialogo.setLayout(layout)
        # Obtener elementos para interactuar
        lbltitulo = dialogo.findChild(QLabel, "label_nombre")
        treefechas = dialogo.findChild(QTreeWidget, "tree_fechas")
        botonaceptar = dialogo.findChild(QPushButton, "btn_aceptar")
        lbltitulo.setText("FECHAS DEL PIEZÓMETRO")
        treefechas.setHeaderLabels([nombrecompo])
        listafechas = PiezometroController.ctrlListarFechasPiezometro(tipo, idcomponente, idinstrumento, idproyecto)
        if listafechas:
            parent = QTreeWidgetItem(treefechas)
            parent.setText(0, nombrepiezo)
            parent.setText(1, "1")
            if fechamarcada:
                parent.setCheckState(0, Qt.PartiallyChecked)
            else:
                parent.setCheckState(0, Qt.Unchecked)
            parent.setFlags(parent.flags() | Qt.ItemIsUserCheckable)
            parent.setExpanded(True)
            for fechas in listafechas:
                item = QTreeWidgetItem(parent)
                item.setText(0, str(fechas[0]))
                item.setText(1, "fecha")
                item.setCheckState(0, Qt.Unchecked)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable)
                if fechamarcada:
                    if str(fechas[0]) == str(fechamarcada):
                        item.setCheckState(0, Qt.Checked)
        def marcadoDesmarcadoCheckbox(parent_item, column):
            TreeCheckbox.validarMarcadoUnicoCheckbox(parent_item, column)
        def obtenerFechasMarcadas():
            fechaelegida = None
            parent = treefechas.topLevelItem(0)
            if parent:
                for i in range(parent.childCount()):
                    hijo = parent.child(i)
                    if hijo.checkState(0) == Qt.Checked:
                        fechaelegida = hijo.text(0)
            dialogo.close()
            if fechaelegida:
                if tipo == "Automatizado":
                    TreeCheckbox.actualizarFechasCheckboxEquipo(treewidget, idcomponente, "Piezómetros Cuerda Vibrante", "piezometrocuerda", nombrepiezo, fechaelegida)
                else:
                    TreeCheckbox.actualizarFechasCheckboxEquipo(treewidget, idcomponente, "Piezómetros Casagrande", "piezometromanual", nombrepiezo, fechaelegida)
                graficarnuevafechaspiezometros(tipo)
        # conectar funciones
        treefechas.itemClicked.connect(marcadoDesmarcadoCheckbox)
        botonaceptar.clicked.connect(obtenerFechasMarcadas)
        dialogo.exec()
    
    def cambiar_componente_bloque_cuerda(idproyecto, idcomponente, parent, treewidget, nombregrupo, tipogrupo, subgrupo, reiniciarvistas):
        dialog = QDialog()
        dialog.setWindowTitle("Mover Cuerda Vibrante Componente")
        layout = QFormLayout(dialog)
        # Campo componente
        label_titulo = QLabel("Componente:")
        combo_componente = QComboBox()
        label_mensaje = QLabel("")
        label_mensaje.setAlignment(Qt.AlignCenter)
        label_mensaje.setStyleSheet("QLabel { color: red; }")
        # cargar data componentes
        componentes = ProyectoController.ctrlObtenerComponentesProyecto(idproyecto)
        if componentes:
            for fila in componentes:
                combo_componente.addItem(str(fila[2]), fila[0])
            combo_componente.setCurrentIndex(combo_componente.findData(idcomponente))
        # Botones
        layout.addRow(label_titulo)
        layout.addRow(combo_componente)
        layout.addRow(label_mensaje)
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        # Cambiar los textos a español
        button_box.button(QDialogButtonBox.Save).setText("Guardar")
        button_box.button(QDialogButtonBox.Cancel).setText("Cancelar")
        layout.addWidget(button_box)
        # Conectar los botones a las funciones correspondientes
        def actualizarDatos():
            componente = combo_componente.currentData()
            nombrezona = combo_componente.currentText()
            if str(idcomponente) == str(componente):
                dialog.reject()
            else:
                result = False
                hijos_marcados = []
                for i in range(parent.childCount()):
                    hijo = parent.child(i)
                    if hijo is not None and hijo.checkState(0) == Qt.Checked:
                        idinstrumento = hijo.text(2)
                        respuesta = PiezometroController.ctrlCambiarPiezometroComponente(idinstrumento, componente)
                        if respuesta:
                            hijos_marcados.append(hijo)
                            result = True
                if result:
                    dialog.reject()
                    for hijo in hijos_marcados:
                        idinstrumento = hijo.text(2)
                        TreeCheckbox.eliminarCheckbox(treewidget, nombregrupo, idinstrumento, subgrupo)
                        # Crear prisma en nuevo componente
                        piezometro = InterfazController.ctrlListarComponentePiezometroCuerda(idinstrumento)
                        if piezometro:
                            TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidget, nombrezona, componente, idproyecto, nombregrupo, tipogrupo, piezometro, subgrupo)
                    reiniciarvistas("Piezómetros Cuerda Vibrante")
                    # Limpiar tabla
                    from views.datos_view import DatosView
                    from modules.datos.vistaDatos import VistaDatos
                    tabla =  DatosView.main.findChild(QTableView, "table_datos")
                    VistaDatos.limpiarTablaDatos(tabla)
                else:
                    label_mensaje.setText("Error al cambiar de componente.")
        button_box.accepted.connect(actualizarDatos)
        button_box.rejected.connect(dialog.reject)
        # Mostrar el diálogo
        dialog.setLayout(layout)
        dialog.exec()
    
    def cambiar_componente_bloque_casagrande(idproyecto, idcomponente, parent, treewidget, nombregrupo, tipogrupo, subgrupo, reiniciarvistas):
        dialog = QDialog()
        dialog.setWindowTitle("Mover Casagrande Componente")
        layout = QFormLayout(dialog)
        # Campo componente
        label_titulo = QLabel("Componente:")
        combo_componente = QComboBox()
        label_mensaje = QLabel("")
        label_mensaje.setAlignment(Qt.AlignCenter)
        label_mensaje.setStyleSheet("QLabel { color: red; }")
        # cargar data componentes
        componentes = ProyectoController.ctrlObtenerComponentesProyecto(idproyecto)
        if componentes:
            for fila in componentes:
                combo_componente.addItem(str(fila[2]), fila[0])
            combo_componente.setCurrentIndex(combo_componente.findData(idcomponente))
        # Botones
        layout.addRow(label_titulo)
        layout.addRow(combo_componente)
        layout.addRow(label_mensaje)
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        # Cambiar los textos a español
        button_box.button(QDialogButtonBox.Save).setText("Guardar")
        button_box.button(QDialogButtonBox.Cancel).setText("Cancelar")
        layout.addWidget(button_box)
        # Conectar los botones a las funciones correspondientes
        def actualizarDatos():
            componente = combo_componente.currentData()
            nombrezona = combo_componente.currentText()
            if str(idcomponente) == str(componente):
                dialog.reject()
            else:
                result = False
                hijos_marcados = []
                for i in range(parent.childCount()):
                    hijo = parent.child(i)
                    if hijo is not None and hijo.checkState(0) == Qt.Checked:
                        idinstrumento = hijo.text(2)
                        respuesta = PiezometroController.ctrlCambiarPiezometroComponente(idinstrumento, componente)
                        if respuesta:
                            hijos_marcados.append(hijo)
                            result = True
                if result:
                    dialog.reject()
                    for hijo in hijos_marcados:
                        idinstrumento = hijo.text(2)
                        TreeCheckbox.eliminarCheckbox(treewidget, nombregrupo, idinstrumento, subgrupo)
                        # Crear prisma en nuevo componente
                        piezometro = InterfazController.ctrlListarComponentePiezometroManual(idinstrumento)
                        if piezometro:
                            TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidget, nombrezona, componente, idproyecto, nombregrupo, tipogrupo, piezometro, subgrupo)
                    reiniciarvistas("Piezómetros Casagrande")
                    # Limpiar tabla
                    from views.datos_view import DatosView
                    from modules.datos.vistaDatos import VistaDatos
                    tabla =  DatosView.main.findChild(QTableView, "table_datos")
                    VistaDatos.limpiarTablaDatos(tabla)
                else:
                    label_mensaje.setText("Error al cambiar de componente.")
        button_box.accepted.connect(actualizarDatos)
        button_box.rejected.connect(dialog.reject)
        # Mostrar el diálogo
        dialog.setLayout(layout)
        dialog.exec()

class CargarPiezometrosCuerdaThread(QThread):
    task_finishCuerda = Signal(dict)

    def __init__(self, idproyecto, ubicacion_texto, idcompo, tipo):
        super().__init__()
        self.idproyecto = idproyecto
        self.ubicacion_texto = ubicacion_texto
        self.idcompo = idcompo
        self.tipo = tipo

    def run(self):
        resultado = {"ok": False, "mensaje": "Data duplicada.", "color": "red"}
        try:
            if self.tipo == "FORMATO":
                respuesta, equipos, erroneos = SubirPiezometros.registrarDataPiezometrosCuerda(
                    self.idproyecto, self.ubicacion_texto, self.idcompo
                )
            else:
                respuesta, equipos, erroneos = SubirPiezometros.registrarDataExcelPiezometrosCuerda(
                    self.idproyecto, self.ubicacion_texto, self.idcompo
                )

            if respuesta:
                resultado["ok"] = True
                if erroneos:
                    resultado["mensaje"] = f"Archivos erróneos: {erroneos}"
                    resultado["color"] = "orange"
                else:
                    resultado["mensaje"] = "Guardado correctamente."
                    resultado["color"] = "green"

                equipos_data = []
                for idpiezometro in equipos:
                    data = PiezometroController.ctrlTraerDataPiezometro(idpiezometro, "PIEZOMETROCUERDA")
                    if not data:
                        continue
                    idinstrumento, idcomponente, nombrezona = data[0], data[1], data[2]
                    piezocu = InterfazController.ctrlListarComponentePiezometroCuerda(idinstrumento)
                    piezometros_visor = None
                    if piezocu:
                        fechas = InterfazController.ctrlListarFechasPiezometroCodigo("Automatizado", idcomponente, idinstrumento, self.idproyecto)
                        if fechas:
                            ultima_fecha = fechas[-1][0]
                            piezo = piezocu[0]
                            piezometros_visor = [(piezo[0], piezo[1], piezo[2], piezo[3], piezo[4], piezo[5], piezo[6], ultima_fecha)]
                    equipos_data.append({
                        "idinstrumento": idinstrumento,
                        "idcomponente": idcomponente,
                        "nombrezona": nombrezona,
                        "piezocu": piezocu,
                        "piezometros_visor": piezometros_visor,
                    })
                resultado["equipos_data"] = equipos_data
            else:
                if erroneos:
                    resultado["mensaje"] = f"Error en el formato de los archivos: {erroneos}"

        except ValueError as e:
            resultado["mensaje"] = str(e)
        except Exception:
            resultado["mensaje"] = "Error al procesar los archivos."

        self.task_finishCuerda.emit(resultado)


class CargarPiezometrosCasagrandeThread(QThread):
    task_finishCasagrande = Signal(dict)

    def __init__(self, idproyecto, ubicacion_texto, idcompo):
        super().__init__()
        self.idproyecto = idproyecto
        self.ubicacion_texto = ubicacion_texto
        self.idcompo = idcompo

    def run(self):
        resultado = {"ok": False, "mensaje": "Data duplicada.", "color": "red"}
        try:
            respuesta, equipos, erroneos = SubirPiezometros.registrarDataPiezometrosManuales(
                self.idproyecto, self.ubicacion_texto, self.idcompo
            )

            if respuesta:
                resultado["ok"] = True
                if erroneos:
                    resultado["mensaje"] = f"Archivos erróneos: {erroneos}"
                    resultado["color"] = "orange"
                else:
                    resultado["mensaje"] = "Guardado correctamente."
                    resultado["color"] = "green"

                equipos_data = []
                for idpiezometro in equipos:
                    data = PiezometroController.ctrlTraerDataPiezometro(idpiezometro, "PIEZOMETROMANUAL")
                    if not data:
                        continue
                    idinstrumento, idcomponente, nombrezona = data[0], data[1], data[2]
                    piezocu = InterfazController.ctrlListarComponentePiezometroManual(idinstrumento)
                    piezometros_visor = None
                    if piezocu:
                        fechas = InterfazController.ctrlListarFechasPiezometroCodigo("Manual", idcomponente, idinstrumento, self.idproyecto)
                        if fechas:
                            ultima_fecha = fechas[-1][0]
                            piezo = piezocu[0]
                            piezometros_visor = [(piezo[0], piezo[1], piezo[2], piezo[3], piezo[4], piezo[5], piezo[6], ultima_fecha)]
                    equipos_data.append({
                        "idinstrumento": idinstrumento,
                        "idcomponente": idcomponente,
                        "nombrezona": nombrezona,
                        "piezocu": piezocu,
                        "piezometros_visor": piezometros_visor,
                    })
                resultado["equipos_data"] = equipos_data
            else:
                if erroneos:
                    resultado["mensaje"] = f"Error en el formato de los archivos: {erroneos}"

        except ValueError as e:
            resultado["mensaje"] = str(e)
        except Exception:
            resultado["mensaje"] = "Error al procesar los archivos."

        self.task_finishCasagrande.emit(resultado)