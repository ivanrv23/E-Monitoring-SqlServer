from datetime import datetime
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui import QAction, QColor
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QTableWidget,
                               QTableWidgetItem, QPushButton, QLabel, QLineEdit, QDateTimeEdit,
                               QColorDialog, QMessageBox, QMenu, QAbstractItemView, QHeaderView)
from utils.common.alertas import mostrar_mensaje
from controllers.EventosController import EventosController


class EventosGrafica:

    # Columnas de la tabla
    COL_ID, COL_DESC, COL_FECHA, COL_ALCANCE, COL_TIPO, COL_INSTRUMENTO = range(6)

    @staticmethod
    def _a_datetime(valor):
        if isinstance(valor, datetime):
            return valor
        for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f'):
            try:
                return datetime.strptime(str(valor), fmt)
            except ValueError:
                continue
        return datetime.now()

    @staticmethod
    def modalEventos(proyectoid, on_cambio=None):
        """Lista de eventos del proyecto. `on_cambio` se llama al cerrar si se editó o eliminó algo
        (por ejemplo, para redibujar la gráfica)."""
        cambios = {'hubo': False}

        dialog = QDialog()
        dialog.setWindowTitle("Lista de Eventos")
        dialog.resize(850, 450)
        layout = QVBoxLayout(dialog)

        lbl_info = QLabel("Clic derecho o doble clic sobre un evento para editarlo o eliminarlo.")
        lbl_info.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(lbl_info)

        table = QTableWidget(0, 6)
        table.setHorizontalHeaderLabels(["ID", "Descripción", "Fecha", "Alcance", "Tipo Instrumento", "Instrumento"])
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setContextMenuPolicy(Qt.CustomContextMenu)
        table.setColumnHidden(EventosGrafica.COL_ID, True)   # el id queda oculto, como en conexiones
        header = table.horizontalHeader()
        header.setSectionResizeMode(EventosGrafica.COL_DESC, QHeaderView.Stretch)
        for col in (EventosGrafica.COL_FECHA, EventosGrafica.COL_ALCANCE,
                    EventosGrafica.COL_TIPO, EventosGrafica.COL_INSTRUMENTO):
            header.setSectionResizeMode(col, QHeaderView.ResizeToContents)
        layout.addWidget(table)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(dialog.accept)
        fila_botones = QHBoxLayout()
        fila_botones.addStretch()
        fila_botones.addWidget(btn_cerrar)
        layout.addLayout(fila_botones)

        # ---------------- carga de datos ----------------
        def cargar():
            eventos = EventosController.ctrlListarEventosProyecto(proyectoid)
            table.setRowCount(0)
            if not eventos:
                return
            table.setRowCount(len(eventos))
            for fila, (id_ev, desc, fecha, alcance, tipo_inst, id_inst, color) in enumerate(eventos):
                fecha_dt = EventosGrafica._a_datetime(fecha)
                item_desc = QTableWidgetItem(str(desc))
                item_desc.setData(Qt.UserRole, color or "#ff0000")   # color guardado en la celda
                if color:
                    item_desc.setForeground(QColor(color))
                valores = [
                    QTableWidgetItem(str(id_ev)),
                    item_desc,
                    QTableWidgetItem(fecha_dt.strftime('%d/%m/%Y %H:%M:%S')),
                    QTableWidgetItem("Global" if alcance == "GLOBAL" else "Específico"),
                    QTableWidgetItem(str(tipo_inst or "")),
                    QTableWidgetItem("Todos" if alcance == "GLOBAL" else str(id_inst or "")),
                ]
                for col, item in enumerate(valores):
                    table.setItem(fila, col, item)
                table.item(fila, EventosGrafica.COL_FECHA).setData(Qt.UserRole, fecha_dt)

        # ---------------- acciones ----------------
        def fila_actual(position=None):
            if position is not None:
                item = table.itemAt(position)
                if item is None:
                    return None
                table.selectRow(item.row())
                return item.row()
            fila = table.currentRow()
            return fila if fila >= 0 else None

        def editar(fila):
            id_ev = int(table.item(fila, EventosGrafica.COL_ID).text())
            desc = table.item(fila, EventosGrafica.COL_DESC).text()
            color = table.item(fila, EventosGrafica.COL_DESC).data(Qt.UserRole)
            fecha = table.item(fila, EventosGrafica.COL_FECHA).data(Qt.UserRole)

            resultado = EventosGrafica.dialogoEditarEvento(desc, fecha, color)
            if resultado is None:
                return
            nueva_desc, nueva_fecha, nuevo_color = resultado
            if EventosController.ctrlActualizarEvento(id_ev, nueva_fecha, nueva_desc, nuevo_color):
                cambios['hubo'] = True
                cargar()
            else:
                mostrar_mensaje("Error", "No se pudo actualizar el evento.", "error")

        def eliminar(fila):
            id_ev = int(table.item(fila, EventosGrafica.COL_ID).text())
            desc = table.item(fila, EventosGrafica.COL_DESC).text()

            msg = QMessageBox(dialog)
            msg.setWindowTitle("Eliminar evento")
            msg.setIcon(QMessageBox.Question)
            msg.setText(f"¿Eliminar definitivamente el evento \"{desc}\"?")
            btn_si = msg.addButton("Sí", QMessageBox.YesRole)
            btn_no = msg.addButton("No", QMessageBox.NoRole)
            msg.setDefaultButton(btn_no)
            msg.exec()

            if msg.clickedButton() != btn_si:
                return
            if EventosController.ctrlEliminarEvento(id_ev):
                cambios['hubo'] = True
                cargar()
            else:
                mostrar_mensaje("Error", "No se pudo eliminar el evento.", "error")

        def menu_contextual(position):
            fila = fila_actual(position)
            if fila is None:
                return
            menu = QMenu()
            act_editar = QAction("Editar Evento", table)
            act_eliminar = QAction("Eliminar Evento", table)
            act_editar.triggered.connect(lambda: editar(fila))
            act_eliminar.triggered.connect(lambda: eliminar(fila))
            menu.addAction(act_editar)
            menu.addAction(act_eliminar)
            menu.exec(table.viewport().mapToGlobal(position))

        table.customContextMenuRequested.connect(menu_contextual)
        table.cellDoubleClicked.connect(lambda fila, col: editar(fila))

        cargar()
        dialog.exec()

        if cambios['hubo'] and on_cambio:
            on_cambio()

    @staticmethod
    def dialogoEditarEvento(descripcion, fecha, color):
        """Devuelve (descripcion, fecha_datetime, color) o None si se cancela."""
        dlg = QDialog()
        dlg.setWindowTitle("Editar Evento")
        dlg.setMinimumWidth(380)
        layout = QVBoxLayout(dlg)
        form = QFormLayout()

        txt_desc = QLineEdit(descripcion)
        txt_desc.setMaxLength(100)
        form.addRow("Descripción:", txt_desc)

        dt_fecha = QDateTimeEdit()
        dt_fecha.setDisplayFormat("dd/MM/yyyy HH:mm:ss")
        dt_fecha.setCalendarPopup(True)
        dt_fecha.setDateTime(QDateTime(fecha.year, fecha.month, fecha.day,
                                       fecha.hour, fecha.minute, fecha.second))
        form.addRow("Fecha:", dt_fecha)

        estado = {'color': color or "#ff0000"}
        lbl_color = QLabel()
        lbl_color.setFixedSize(40, 25)

        def pintar():
            lbl_color.setStyleSheet(f"background-color: {estado['color']}; "
                                    f"border: 1px solid #999; border-radius: 3px;")

        def cambiar_color():
            c = QColorDialog.getColor(QColor(estado['color']), dlg)
            if c.isValid():
                estado['color'] = c.name()
                pintar()

        pintar()
        btn_color = QPushButton("Cambiar")
        btn_color.clicked.connect(cambiar_color)
        fila_color = QHBoxLayout()
        fila_color.addWidget(lbl_color)
        fila_color.addWidget(btn_color)
        fila_color.addStretch()
        form.addRow("Color:", fila_color)
        layout.addLayout(form)

        btn_guardar = QPushButton("Guardar")
        btn_cancelar = QPushButton("Cancelar")
        fila_botones = QHBoxLayout()
        fila_botones.addStretch()
        fila_botones.addWidget(btn_guardar)
        fila_botones.addWidget(btn_cancelar)
        layout.addLayout(fila_botones)

        def validar():
            if txt_desc.text().strip():
                dlg.accept()
            else:
                txt_desc.setFocus()

        btn_guardar.clicked.connect(validar)
        btn_cancelar.clicked.connect(dlg.reject)

        if dlg.exec() != QDialog.Accepted:
            return None

        dt = dt_fecha.dateTime()
        nueva_fecha = datetime(dt.date().year(), dt.date().month(), dt.date().day(),
                               dt.time().hour(), dt.time().minute(), dt.time().second())
        return txt_desc.text().strip(), nueva_fecha, estado['color']