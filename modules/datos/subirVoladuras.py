import re
import unicodedata
import pandas as pd
from datetime import datetime, time
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QComboBox, QPushButton, QMenu, QTableWidget,
                            QLabel, QLineEdit, QFileDialog, QFormLayout, QDialogButtonBox, QMessageBox, QTreeWidget, QTableView)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import Qt, QThread, Signal
from utils.common.rutasarchivos import resource_path
from utils.generic.cargariconos import cargarIcono
from utils.shared.pegarDatosTabla import configurar_tabla_para_pegado, pegar_desde_portapapeles
from utils.common.metodosGenerales import MetodosGenerales
from controllers.ProyectoController import ProyectoController
from controllers.VoladuraController import VoladuraController
from utils.shared.loading import LoadingView
from utils.common.alertas import mostrar_mensaje
from PySide6.QtWidgets import QDoubleSpinBox, QSpinBox, QColorDialog
from PySide6.QtGui import QColor
from utils.shared.arbolmarcado import TreeCheckbox
from controllers.InterfazController import InterfazController

class SubirVoladuras:
    _current_thread_voladura = None

    # ------------------------------------------------------------------
    # REFRESCAR ÁRBOL DE EQUIPOS (pestaña Datos)
    # ------------------------------------------------------------------
    def _refrescarArbol(treeWidget, reiniciarvistas=None):
        from modules.datos.equiposDatos import EquiposDatos
        from views.datos_view import DatosView
        if treeWidget is not None:
            EquiposDatos.inicializar_lista_datos(treeWidget, DatosView.idproyecto, DatosView.nameproyecto)
        DatosView.obtenerEquiposMarcados(True)
        if reiniciarvistas:
            reiniciarvistas("Voladura")

    def _actualizarGrupoArbolDatos(main, idinstrumento, idcomponente, nombrezona, vol, proyectoid, treeWidget=None):
        for nombre_arbol, tipo in SubirVoladuras.ARBOLES:
            tree = main.findChild(QTreeWidget, nombre_arbol) if main is not None else None
            if tree is None:
                continue
            if tree is None or tree.topLevelItemCount() == 0:
                continue

            def volcar(t):
                for i in range(t.topLevelItemCount()):
                    comp = t.topLevelItem(i)
                    print("   COMP:", comp.text(0), "| id:", comp.text(2))
                    for j in range(comp.childCount()):
                        grp = comp.child(j)
                        print("      GRUPO:", grp.text(0), "| tipo:", grp.text(1),
                              "| hijos:", grp.childCount(), "| oculto:", grp.isHidden())

            volcar(tree)
            try:
                TreeCheckbox.eliminarCheckbox(tree, "Voladuras", idinstrumento, "voladura")
                volcar(tree)
                if vol:
                    TreeCheckbox.crearNuevoGrupoCheckboxesSimple(
                        tree, nombrezona, idcomponente, proyectoid,
                        "Voladuras", tipo, vol, "voladura")
                volcar(tree)
            except Exception:
                import traceback
                traceback.print_exc()

    def _actualizarGrupoArbol(idvoladura, proyectoid, main=None, treeWidget=None):
        if main is None:
            from views.datos_view import DatosView
            main = DatosView.main
        data = VoladuraController.ctrlTraerDataVoladura(idvoladura)
        if not data:
            return
        idinstrumento, idcomponente, nombrezona = data[0], data[1], data[2]
        vol = InterfazController.ctrlListarComponenteVoladura(idinstrumento)
        SubirVoladuras._actualizarGrupoArbolDatos(
            main, idinstrumento, idcomponente, nombrezona, vol, proyectoid, treeWidget)
    # ------------------------------------------------------------------
    # CARGAR DESDE TABLA
    # Columnas: 0 Fecha | 1 Hora | 2 Ubicación | 3 Cota | 4 Observación
    # ------------------------------------------------------------------
    def registroNuevaDataVoladuras(main, proyectoid, treeWidget=None, reiniciarvistas=None):
        loader = QUiLoader()
        ui_file = loader.load(resource_path("ui/datavoladura.ui"), None)
        dialog = QDialog()
        dialog.setWindowTitle("Data de Voladuras")
        layout = QVBoxLayout()
        layout.addWidget(ui_file)
        dialog.setLayout(layout)

        combovoladuras = dialog.findChild(QComboBox, "combo_voladuras")
        tabladata = dialog.findChild(QTableWidget, "table_voladuras_data")
        botonGuardar = dialog.findChild(QPushButton, "btn_guardar")
        botonCancelar = dialog.findChild(QPushButton, "btn_cancelar")
        lblrespuesta = dialog.findChild(QLabel, "label_mensaje_estado")
        tabladata.insertRow(0)

        listavoladuras = VoladuraController.ctrlListaVoladurasProyecto(proyectoid)
        if listavoladuras:
            for fila in listavoladuras:
                combovoladuras.addItem(str(fila[2]), fila[0])
        else:
            combovoladuras.addItem("Sin Voladuras")
            botonGuardar.setEnabled(False)

        def menuPegadoDataTabla(pos):
            menu = QMenu()
            accion = menu.addAction("Pegar aquí")
            accion.triggered.connect(lambda: pegar_desde_portapapeles(tabladata))
            menu.exec(tabladata.mapToGlobal(pos))

        def textoCelda(row, col):
            item = tabladata.item(row, col)
            return item.text().strip() if item else ""

        def parsearCota(texto):
            """Devuelve (ok, valor). Vacío -> (True, None). Solo números -> (True, float)."""
            t = texto.replace("\xa0", "").replace(" ", "").strip()
            if t == "":
                return True, None
            if not re.fullmatch(r"-?\d+([.,]\d+)?", t):
                return True, None
            return True, float(t.replace(",", "."))

        def guardarDataVoladura():
            idvoladura = combovoladuras.currentData()
            data = []
            for row in range(tabladata.rowCount()):
                fecha = textoCelda(row, 0)
                hora = textoCelda(row, 1)
                ubicacion = textoCelda(row, 2)
                cota = textoCelda(row, 3).replace("\xa0", "").strip()
                observa = textoCelda(row, 4)
                # ignorar filas totalmente vacías
                if not any([fecha, hora, ubicacion, cota, observa]):
                    continue
                if not fecha:
                    mensaje = "La fecha está vacía."
                elif not MetodosGenerales.validarFormatoFecha(fecha):
                    mensaje = "La fecha no tiene un formato adecuado."
                elif not hora:
                    mensaje = "La hora está vacía."
                elif not MetodosGenerales.validarFormatoHora(hora):
                    mensaje = "La hora no tiene un formato adecuado."
                elif not parsearCota(cota)[0]:
                    mensaje = f"La cota debe ser numérica o estar vacía (valor: '{cota}')."
                else:
                    mensaje = None
                if mensaje:
                    lblrespuesta.setText(f"En la fila {row + 1}: {mensaje}")
                    lblrespuesta.setStyleSheet("color: orange;")
                    return
                fecha = MetodosGenerales.validarFormatoFecha(fecha)
                hora = MetodosGenerales.validarFormatoHora(hora)
                cota_valor = parsearCota(cota)[1]
                data.append((idvoladura, fecha, hora, ubicacion, cota_valor, observa))
            if not data:
                lblrespuesta.setText("No hay datos para guardar.")
                lblrespuesta.setStyleSheet("color: orange;")
                return
            if VoladuraController.ctrlGuardarVoladuraTabla(proyectoid, data):
                lblrespuesta.setText("Registrado Correctamente.")
                lblrespuesta.setStyleSheet("color: green;")
                tabladata.setRowCount(0)
                tabladata.insertRow(0)
                SubirVoladuras._actualizarGrupoArbol(idvoladura, proyectoid, main, treeWidget)
            else:
                lblrespuesta.setText("Error al registrar.")
                lblrespuesta.setStyleSheet("color: red;")

        tabladata.setContextMenuPolicy(Qt.CustomContextMenu)
        tabladata.customContextMenuRequested.connect(menuPegadoDataTabla)
        configurar_tabla_para_pegado(tabladata)
        botonGuardar.clicked.connect(guardarDataVoladura)
        botonCancelar.clicked.connect(dialog.close)
        dialog.exec()

    # ------------------------------------------------------------------
    # CARGAR FORMATO (Excel)  -> reutiliza ui/cargardataformato.ui
    # ------------------------------------------------------------------
    def cargarDataFormatosVoladuras(main, proyectoid):
        loader = QUiLoader()
        ui_file = loader.load(resource_path("ui/cargardataformato.ui"), None)
        dialogo = QDialog()
        dialogo.setWindowTitle("Data Voladuras")
        layout = QVBoxLayout()
        layout.addWidget(ui_file)
        dialogo.setLayout(layout)

        botonSubir = dialogo.findChild(QPushButton, "btn_cargar_archivo")
        cargarIcono(botonSubir, "resources/iconos/fontawesome/solid/file-arrow-up.svg")
        ubicacion_archivo = dialogo.findChild(QLineEdit, "input_archivo")
        ubicacion_archivo.setReadOnly(True)
        comboComponentes = dialogo.findChild(QComboBox, "combo_componentes")
        labelRespuesta = dialogo.findChild(QLabel, "label_mensaje")
        botonAceptar = dialogo.findChild(QPushButton, "btn_aceptar")

        componentes = ProyectoController.ctrlObtenerComponentesProyecto(proyectoid)
        if len(componentes) > 0:
            for fila in componentes:
                comboComponentes.addItem(str(fila[2]), fila[0])
            comboComponentes.setEnabled(True)
        else:
            comboComponentes.addItem("Sin Componentes")
            comboComponentes.setEnabled(False)
            botonAceptar.setEnabled(False)

        def cargar_archivo():
            files, _ = QFileDialog.getOpenFileNames(None, "Cargar Archivos", "", "Archivos Excel (*.xlsx)")
            if files:
                ubicacion_archivo.setText("\n".join(files))

        def procesar_archivo():
            if not ubicacion_archivo.text().strip():
                labelRespuesta.setText("No se cargó ningún archivo.")
                labelRespuesta.setStyleSheet("color: red;")
                return
            idcomponente = comboComponentes.currentData()
            labelRespuesta.setText("")
            botonAceptar.setEnabled(False)

            loading = LoadingView.mostrarLoading()
            thread = CargarVoladurasThread(proyectoid, ubicacion_archivo.text(), idcomponente)
            SubirVoladuras._current_thread_voladura = thread

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
                        voladu = item["vol"]

                        treewidgetdatos = main.findChild(QTreeWidget, "tree_actual_datos")
                        treewidgetveloci = main.findChild(QTreeWidget, "tree_actual_desplazamiento")
                        treewidgetanalisis = main.findChild(QTreeWidget, "tree_actual_analisis")
                        TreeCheckbox.eliminarCheckbox(treewidgetdatos, "Voladuras", idinstrumento, "voladura")
                        TreeCheckbox.eliminarCheckbox(treewidgetveloci, "Voladuras", idinstrumento, "voladura")
                        TreeCheckbox.eliminarCheckbox(treewidgetanalisis, "Voladuras", idinstrumento, "voladura")

                        if voladu:
                            TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetdatos, nombrezona, idcomponente, proyectoid, "Voladuras", "12", voladu, "voladura")
                            TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetveloci, nombrezona, idcomponente, proyectoid, "Voladuras", "3", voladu, "voladura")
                            TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidgetanalisis, nombrezona, idcomponente, proyectoid, "Voladuras", "3", voladu, "voladura")

                SubirVoladuras._current_thread_voladura = None

            thread.task_finishVoladura.connect(on_finish, Qt.ConnectionType.QueuedConnection)
            thread.finished.connect(thread.deleteLater)
            thread.start()
            loading.exec()

        botonSubir.clicked.connect(cargar_archivo)
        botonAceptar.clicked.connect(procesar_archivo)
        dialogo.exec()

    def _norm(valor):
        if valor is None or (isinstance(valor, float) and pd.isna(valor)):
            return ""
        txt = unicodedata.normalize("NFD", str(valor))
        txt = "".join(c for c in txt if unicodedata.category(c) != "Mn")
        return re.sub(r"[^a-z0-9]", "", txt.lower())

    # Busca arriba de los encabezados una celda que contenga 'clave' y
    # devuelve la primera celda no vacía a su derecha (misma fila).
    def _valorJuntoA(df, fila_limite, clave):
        for r in range(fila_limite):
            fila = df.iloc[r]
            for c in range(len(fila)):
                if clave in SubirVoladuras._norm(fila.iloc[c]):
                    for c2 in range(c + 1, len(fila)):
                        v = fila.iloc[c2]
                        if not pd.isna(v) and str(v).strip() != "":
                            return str(v).strip()
        return None

    def registrarFormatoDataVoladuras(proyectoid, ubicacion, idcomponente):
        equipos = []
        erroneos = []
        respuesta = False
        for file_name in ubicacion.split("\n"):
            file_name = file_name.strip()
            if not file_name or not file_name.endswith('.xlsx'):
                continue
            nombre_corto = file_name.replace("\\", "/").split("/")[-1]
            try:
                df = pd.read_excel(file_name, header=None, engine='openpyxl')
                # 1) localizar fila de encabezados (Fecha ... Cota ...)
                fila_enc = None
                col = {}
                for r in range(min(len(df), 40)):
                    normas = [SubirVoladuras._norm(v) for v in df.iloc[r]]
                    if "fecha" in normas and any(n.startswith("cota") for n in normas):
                        fila_enc = r
                        for idx, n in enumerate(normas):
                            if n == "fecha":
                                col["fecha"] = idx
                            elif n == "hora":
                                col["hora"] = idx
                            elif n.startswith("ubicacion"):
                                col["ubicacion"] = idx
                            elif n.startswith("cota"):
                                col["cota"] = idx
                            elif n.startswith("observ"):
                                col["observacion"] = idx
                        break
                if fila_enc is None:
                    erroneos.append(f"{nombre_corto} (no se encontró fila con encabezados Fecha y Cota)")
                    continue
                if proyectoid == 0 or not idcomponente:
                    erroneos.append(f"{nombre_corto} (seleccione un componente)")
                    continue

                # 2) nombre (y comentario opcional) que vienen en el Excel
                nombrevol = SubirVoladuras._valorJuntoA(df, fila_enc, "nombre")
                if not nombrevol:
                    erroneos.append(f"{nombre_corto} (no se encontró el nombre de la voladura)")
                    continue
                comentario = SubirVoladuras._valorJuntoA(df, fila_enc, "comentario") or ""

                # 3) leer filas de datos (sin id todavía)
                def celda(row, clave):
                    idx = col.get(clave)
                    return row.iloc[idx] if idx is not None else None
                filas = []
                for r in range(fila_enc + 1, len(df)):
                    row = df.iloc[r]
                    fecha, hora, cota_raw = celda(row, "fecha"), celda(row, "hora"), celda(row, "cota")
                    if pd.isna(fecha):
                        continue
                    if isinstance(fecha, (pd.Timestamp, datetime)):
                        fecha = fecha.strftime('%Y-%m-%d')
                    elif isinstance(fecha, str):
                        fecha = MetodosGenerales.validarFormatoFecha(fecha.strip())
                        if not fecha:
                            continue
                    else:
                        continue
                    if isinstance(hora, (pd.Timestamp, datetime)):
                        hora = hora.time().strftime('%H:%M:%S')
                    elif isinstance(hora, time):
                        hora = hora.strftime('%H:%M:%S')
                    elif isinstance(hora, str):
                        hora = MetodosGenerales.validarFormatoHora(hora.strip()) or "00:00:00"
                    else:
                        hora = "00:00:00"
                    if pd.isna(cota_raw) or str(cota_raw).strip() == "":
                        cota = None
                    else:
                        try:
                            cota = float(str(cota_raw).replace(",", ".").strip())
                        except (ValueError, TypeError):
                            continue   # texto no numérico: se omite la fila
                    ubic, obs = celda(row, "ubicacion"), celda(row, "observacion")
                    ubic = "" if ubic is None or pd.isna(ubic) else str(ubic).strip()
                    obs = "" if obs is None or pd.isna(obs) else str(obs).strip()
                    filas.append((fecha, hora, ubic, cota, obs))
                if not filas:
                    erroneos.append(f"{nombre_corto} (sin filas válidas: revise fecha y cota)")
                    continue

                # 4) buscar la voladura en la carpeta; si no existe, crearla
                idvoladura = SubirVoladuras._buscarVoladura(proyectoid, nombrevol, idcomponente)
                if not idvoladura:
                    idvoladura = VoladuraController.ctrlRegistrarFormatoVoladura(
                        proyectoid, nombrevol, nombrevol, comentario, idcomponente)
                    if not idvoladura:
                        erroneos.append(f"{nombre_corto} (no se pudo crear la voladura '{nombrevol}')")
                        continue

                # 5) guardar lecturas
                data = [(idvoladura,) + f for f in filas]
                print("### PASO 5 VISTA ### filas:", len(data), "idvoladura:", idvoladura)
                if VoladuraController.ctrlGuardarVoladuraTabla(proyectoid, data):
                    respuesta = True
                    if idvoladura not in equipos:
                        equipos.append(idvoladura)
                else:
                    erroneos.append(f"{nombre_corto} (error al guardar en BD, ver consola)")
            except Exception as e:
                import traceback
                traceback.print_exc()
                erroneos.append(f"{nombre_corto} ({type(e).__name__}: {e})")
        return respuesta, equipos, erroneos

    # ------------------------------------------------------------------
    # EDITAR / ELIMINAR VOLADURA (menú del árbol)
    # ------------------------------------------------------------------
    def actualizarVoladura(idproyecto, idcomponente, idinstrumento, treewidget, nombregrupo, tipogrupo, subgrupo, reiniciarvistas):
        info = VoladuraController.ctrlObtenerInfoVoladura(idinstrumento)
        if not info:
            mostrar_mensaje("Sin Datos", "No se pudo cargar los datos de la voladura.", "advertencia")
            return
        idvoladura, nombre_ini, codigo_ini, comentario_ini, estado_ini, idcomp_ini = info
        componentes = VoladuraController.ctrlListarComponentesProyecto(idproyecto) or []

        dialog = QDialog()
        dialog.setWindowTitle("Editar Voladura")
        layout = QFormLayout(dialog)

        nombre_input = QLineEdit(str(nombre_ini or ""))
        codigo_input = QLineEdit(str(codigo_ini or ""))
        comentario_input = QLineEdit(str(comentario_ini or ""))

        componente_combo = QComboBox()
        for comp in componentes:
            componente_combo.addItem(str(comp[1]), comp[0])
        idx = componente_combo.findData(idcomp_ini)
        if idx >= 0:
            componente_combo.setCurrentIndex(idx)

        estado_combo = QComboBox()
        estado_combo.addItems(["Activo", "Inactivo"])
        estado_combo.setCurrentText("Activo" if estado_ini in (1, True, "1") else "Inactivo")

        layout.addRow("Nombre:", nombre_input)
        layout.addRow("Código:", codigo_input)
        layout.addRow("Comentario:", comentario_input)
        layout.addRow("Componente:", componente_combo)
        layout.addRow("Estado:", estado_combo)

        label_mensaje = QLabel("")
        label_mensaje.setAlignment(Qt.AlignCenter)
        label_mensaje.setStyleSheet("QLabel { color: red; }")
        layout.addRow(label_mensaje)

        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Save).setText("Guardar")
        button_box.button(QDialogButtonBox.Cancel).setText("Cancelar")
        layout.addWidget(button_box)

        def guardar():
            nombrezona = componente_combo.currentText()
            nombre = nombre_input.text().strip()
            codigo = codigo_input.text().strip()
            comentario = comentario_input.text().strip()
            nuevo_comp = componente_combo.currentData()
            estado = 1 if estado_combo.currentText() == "Activo" else 0
            if nombre == "" or nuevo_comp is None:
                label_mensaje.setText("El nombre y el componente son obligatorios.")
                return
            existe, fila = VoladuraController.ctrlComprobarExisteNombreVoladura(idproyecto, nombre)
            if existe and fila[0] != idvoladura:
                label_mensaje.setText("Ya existe una voladura con ese nombre.")
                return
            datos = [nombre, codigo, comentario, estado, idvoladura]
            data = [nuevo_comp, nombre, estado, idinstrumento]
            respuesta = VoladuraController.ctrlActualizarVoladura(datos, data)
            if respuesta:
                dialog.accept()
                if str(idcomponente) == str(nuevo_comp):
                    TreeCheckbox.actualizarTextoCheckboxEquipo(treewidget, idcomponente, nombregrupo, subgrupo, nombre_ini, nombre)
                else:
                    # Eliminar voladura
                    TreeCheckbox.eliminarCheckbox(treewidget, nombregrupo, idinstrumento, subgrupo)
                    # Crear voladura en nuevo componente
                    voladur = InterfazController.ctrlListarComponentePluviometro(idinstrumento)
                    if voladur:
                        TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidget, nombrezona, nuevo_comp, idproyecto, nombregrupo, tipogrupo, voladur, subgrupo)
                reiniciarvistas("Voladura")
            else:
                label_mensaje.setText("Error al actualizar la voladura.")
                label_mensaje.setStyleSheet("color: red;")

        button_box.accepted.connect(guardar)
        button_box.rejected.connect(dialog.reject)
        dialog.exec()

    def eliminar_voladura(idproyecto, idinstrumento, nombrevoladu, nombregrupo, subgrupo, treewidget, reiniciarvistas):
        dlg = QMessageBox()
        dlg.setWindowTitle("Eliminar Voladura")
        dlg.setText(f"¿Está seguro eliminar la Voladura '{nombrevoladu}'?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.button(QMessageBox.Yes).setText("Sí")
        dlg.button(QMessageBox.No).setText("No")
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            respuesta = VoladuraController.ctrlEliminarVoladura(idinstrumento)
            if respuesta:
                # El instrumento ya se eliminó: quitar del árbol de inmediato
                TreeCheckbox.eliminarCheckbox(treewidget, nombregrupo, idinstrumento, subgrupo)
                reiniciarvistas("Voladura")

                delete = VoladuraController.ctrlEliminarVoladuraData(idproyecto, respuesta)
                if not delete:
                    mostrar_mensaje("Eliminar Voladura", "Error al eliminar data de la voladura.", "advertencia")
            else:
                mostrar_mensaje("Eliminar Voladura", "No se pudo eliminar la voladura.", "advertencia")
    
    def cambiar_componente_bloque_voladura(idproyecto, idcomponente, parent, treewidget, nombregrupo, tipogrupo, subgrupo, reiniciarvistas):
        dialog = QDialog()
        dialog.setWindowTitle("Mover Voladuras Componente")
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
                        respuesta = VoladuraController.ctrlCambiarVoladuraComponente(idinstrumento, componente)
                        if respuesta:
                            hijos_marcados.append(hijo)
                            result = True
                if result:
                    dialog.reject()
                    for hijo in hijos_marcados:
                        idinstrumento = hijo.text(2)
                        TreeCheckbox.eliminarCheckbox(treewidget, nombregrupo, idinstrumento, subgrupo)
                        # Crear voladura en nuevo componente
                        voladura = InterfazController.ctrlListarComponenteVoladura(idinstrumento)
                        if voladura:
                            TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidget, nombrezona, componente, idproyecto, nombregrupo, tipogrupo, voladura, subgrupo)
                    reiniciarvistas("Voladuras")
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

    # ------------------------------------------------------------------
    # CAMBIAR COMPONENTE / ELIMINAR TODAS (menú del grupo)
    # ------------------------------------------------------------------
    def cambiar_componente_voladuras(idcomponente, idproyecto, treewidget, nombregrupo, tipogrupo, subgrupo, reiniciarvistas):
        dialog = QDialog()
        dialog.setWindowTitle("Componente Voladuras")
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
                respuesta = VoladuraController.ctrlCambiarComponenteVoladuras(idcomponente, componente)
                if respuesta:
                    dialog.reject()
                    # Eliminar voladuras
                    TreeCheckbox.eliminarCheckboxGrupo(treewidget, idcomponente, nombregrupo, tipogrupo)
                    # Crear voladura en nuevo componente
                    TreeCheckbox.crearNuevoGrupoCheckboxesSimple(treewidget, nombrezona, componente, idproyecto, nombregrupo, tipogrupo, respuesta, subgrupo)
                    reiniciarvistas("Voladuras")
                else:
                    label_mensaje.setText("Error al cambiar de componente.")
        button_box.accepted.connect(actualizarDatos)
        button_box.rejected.connect(dialog.reject)
        # Mostrar el diálogo
        dialog.setLayout(layout)
        dialog.exec()
    
    def eliminar_voladuras(idproyecto, idzona, grupo, tipo, treewidget, reiniciarvistas):
        dlg = QMessageBox()
        dlg.setWindowTitle("Eliminar Voladuras")
        dlg.setText(f"¿Está seguro eliminar todos las voladuras?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.button(QMessageBox.Yes).setText("Sí")
        dlg.button(QMessageBox.No).setText("No")
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            respuesta = VoladuraController.ctrlEliminarVoladurasComponente(idzona)
            if respuesta:
                # Los instrumentos ya se eliminaron: quitar del árbol de inmediato
                TreeCheckbox.eliminarCheckboxGrupo(treewidget, idzona, grupo, tipo)
                reiniciarvistas("Voladura")

                delete = VoladuraController.ctrlEliminarDataVoladuras(idproyecto, respuesta)
                if not delete:
                    mostrar_mensaje("Eliminar Voladuras", "Error al eliminar data Voladuras.", "advertencia")
            else:
                mostrar_mensaje("Eliminar Voladuras", "No se pudo eliminar las Voladuras.", "advertencia")
    
    def personalizarVoladura(idinstrumento, nombre, callback_graficar=None):
            estilo = VoladuraController.ctrlObtenerEstiloVoladura(idinstrumento)
            grosor_ini, alto_ini, color_ini = estilo if estilo else (2.5, 0.05, "#ff0000")
    
            dialog = QDialog()
            dialog.setWindowTitle(f"Personalizar Voladura - {nombre}")
            form = QFormLayout(dialog)
    
            spin_grosor = QDoubleSpinBox()
            spin_grosor.setRange(0.5, 15.0)
            spin_grosor.setSingleStep(0.5)
            spin_grosor.setValue(float(grosor_ini))
    
            spin_largo = QSpinBox()
            spin_largo.setRange(1, 100)
            spin_largo.setSuffix(" % del alto del gráfico")
            spin_largo.setValue(int(round(float(alto_ini) * 100)))
    
            color_actual = {"hex": str(color_ini)}
            btn_color = QPushButton()
    
            def pintar_boton():
                btn_color.setText(color_actual["hex"])
                btn_color.setStyleSheet(f"background-color: {color_actual['hex']}; "
                                        f"color: {'black' if QColor(color_actual['hex']).lightness() > 128 else 'white'};")
    
            def elegir_color():
                c = QColorDialog.getColor(QColor(color_actual["hex"]), dialog, "Color de la voladura")
                if c.isValid():
                    color_actual["hex"] = c.name()
                    pintar_boton()
    
            pintar_boton()
            btn_color.clicked.connect(elegir_color)
    
            form.addRow("Grosor:", spin_grosor)
            form.addRow("Largo:", spin_largo)
            form.addRow("Color:", btn_color)
    
            box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
            box.button(QDialogButtonBox.Save).setText("Guardar")
            box.button(QDialogButtonBox.Cancel).setText("Cancelar")
            form.addRow(box)
    
            def guardar():
                ok = VoladuraController.ctrlGuardarEstiloVoladura(
                    idinstrumento, spin_grosor.value(), spin_largo.value() / 100.0, color_actual["hex"])
                if ok:
                    dialog.accept()
                    if callback_graficar:
                        callback_graficar()
                else:
                    mostrar_mensaje("Personalizar", "No se pudo guardar el estilo.", "advertencia")
    
            box.accepted.connect(guardar)
            box.rejected.connect(dialog.reject)
            dialog.exec()

    COL_COMPONENTE = 3

    ARBOLES = [
        ("tree_actual_datos", "12"),
        ("tree_actual_piezometros", "5"),
    ]

    def _buscarVoladura(proyectoid, nombre, idcomponente):
        lista = VoladuraController.ctrlListaVoladurasProyecto(proyectoid)
        if lista:
            for fila in lista:
                if (str(fila[2]).strip().lower() == nombre.lower()
                        and fila[SubirVoladuras.COL_COMPONENTE] == idcomponente):
                    return fila[0]
        return None


class CargarVoladurasThread(QThread):
    task_finishVoladura = Signal(dict)

    def __init__(self, proyectoid, ubicacion_texto, idcomponente):
        super().__init__()
        self.proyectoid = proyectoid
        self.ubicacion_texto = ubicacion_texto
        self.idcomponente = idcomponente

    def run(self):
        resultado = {"ok": False, "mensaje": "Data duplicada.", "color": "red"}
        try:
            respuesta, equipos, erroneos = SubirVoladuras.registrarFormatoDataVoladuras(
                self.proyectoid, self.ubicacion_texto, self.idcomponente)
            if respuesta:
                resultado["ok"] = True
                if erroneos:
                    resultado["mensaje"] = f"Archivos erróneos: {erroneos}"
                    resultado["color"] = "orange"
                else:
                    resultado["mensaje"] = "Guardado correctamente."
                    resultado["color"] = "green"

                equipos_data = []
                for idvoladura in equipos:
                    data = VoladuraController.ctrlTraerDataVoladura(idvoladura)
                    if not data:
                        continue
                    vol = InterfazController.ctrlListarComponenteVoladura(data[0])
                    equipos_data.append({
                        "idinstrumento": data[0],
                        "idcomponente": data[1],
                        "nombrezona": data[2],
                        "vol": vol,
                    })
                resultado["equipos_data"] = equipos_data
            elif erroneos:
                resultado["mensaje"] = f"Error en el formato de los archivos: {erroneos}"
        except Exception:
            resultado["mensaje"] = "Error al procesar los archivos."
        self.task_finishVoladura.emit(resultado)