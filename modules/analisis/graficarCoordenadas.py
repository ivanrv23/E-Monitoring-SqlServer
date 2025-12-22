import pandas as pd
import pyqtgraph as pg
import numpy as np
from PySide6.QtWidgets import (QVBoxLayout, QWidget, QDialog, QDialogButtonBox, QLabel, QFrame, QPushButton)
from pyqtgraph import DateAxisItem
from PySide6.QtCore import QDateTime, Signal, QObject, Qt
from services.security.session import Session

class SignalHandler(QObject):
    data_updated = Signal(int, str, str, str, int, dict)

class GraficarCoordenadasPrismas:
    @staticmethod
    def graficarDesplazamiento(idproyecto, widget, datos, variable, callback=None):
        # Limpiar widget contenedor
        for child in widget.findChildren(QWidget):
            child.deleteLater()
        if widget.layout():
            QWidget().setLayout(widget.layout())

        # Convertir a DataFrame
        df = pd.DataFrame(datos, columns=['id', 'fecha', 'nombre', 'este', 'norte', 'elevacion', 'distancia'])
        df['fecha'] = pd.to_datetime(df['fecha'])
        df = df.sort_values('fecha').copy()

        # Validar variable
        variable = variable.upper()
        if variable not in ['X', 'Y', 'Z', 'DISTANCIA']:
            variable = 'X'

        # Configuración de variables
        params = {
            'X': ('este', 'Coordenada Este', 'r', 'm'),
            'Y': ('norte', 'Coordenada Norte', 'g', 'm'),
            'Z': ('elevacion', 'Elevación', 'b', 'msnm'),
            'DISTANCIA': ('distancia', 'Distancia Inclinada', 'm', 'm')
        }
        col_name, label, color, unit = params[variable]

        # Valores a graficar
        values = df[col_name].copy()
        timestamps = df['fecha'].astype('int64') // 10**9  # convertir a segundos

        # Crear widget de gráfico y layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Ejes personalizados
        class DateAxisFormatter(DateAxisItem):
            def tickStrings(self, values, scale, spacing):
                # Formato corto y legible: día/mes/año
                return [QDateTime.fromSecsSinceEpoch(int(value)).toString('dd/MM/yyyy') for value in values]

            def tickValues(self, minVal, maxVal, size):
                # Dejar que PyQtGraph decida los ticks automáticamente
                return super().tickValues(minVal, maxVal, size)

        class DecimalAxis(pg.AxisItem):
            def __init__(self, orientation='left', decimals=3, *args, **kwargs):
                super().__init__(orientation, *args, **kwargs)
                self.decimals = decimals

            def tickStrings(self, values, scale, spacing):
                return [f"{v:.{self.decimals}f}" for v in values]

        date_axis = DateAxisFormatter(orientation='bottom')
        decimal_axis = DecimalAxis(orientation='left', decimals=3)

        plot_widget = pg.PlotWidget(axisItems={'bottom': date_axis, 'left': decimal_axis})
        layout.addWidget(plot_widget)
        widget.setLayout(layout)

        # Configuración del gráfico
        plot_widget.setBackground('w')
        plot_widget.showGrid(x=True, y=True, alpha=0.3)
        plot_widget.setLabel('left', f'{label} ({unit})')
        plot_widget.setLabel('bottom', 'Fechas')
        plot_widget.setTitle(f"{label} - Prisma {df['nombre'].iloc[0]}", size='12pt')

        # Graficar puntos
        plot_item = plot_widget.plot(
            timestamps,
            values,
            pen=pg.mkPen(color=color, width=2),
            symbol='o',
            symbolSize=8,
            symbolBrush=color,
            name='Valores Originales',
            clickable=True
        )

        # Ajustar rangos dinámicamente
        if len(values) > 1:
            x_padding = max(1, (timestamps.iloc[-1] - timestamps.iloc[0]) * 0.02)
            y_range = values.max() - values.min()
            y_padding = y_range * 0.1 if y_range > 0 else max(1, abs(values.mean()) * 0.1)

            plot_widget.setXRange(timestamps.iloc[0] - x_padding, timestamps.iloc[-1] + x_padding)
            plot_widget.setYRange(values.min() - y_padding, values.max() + y_padding)

        # Señal para actualización
        signal_handler = SignalHandler()

        # Evento click en puntos
        def on_click(plot, points):
            point = points[0]
            idx = point.index()
            row = df.iloc[idx]
            current_value = values.iloc[idx]

            # Crear diálogo de confirmación
            dialog = QDialog(widget)
            dialog.setWindowTitle(f"Ajustar Salto - {row['nombre']}")
            dialog.setMinimumWidth(400)
            dialog.setModal(True)

            layout_dialog = QVBoxLayout(dialog)

            label_warning = QLabel("⚠️ ADVERTENCIA")
            label_warning.setStyleSheet("font-weight: bold; color: #d32f2f; font-size: 14px;")
            label_warning.setAlignment(Qt.AlignCenter)
            layout_dialog.addWidget(label_warning)

            label_message = QLabel("¿Está seguro de aplicar el ajuste?\n\nEsta acción modificará la data actual y NO se podrá recuperar.")
            label_message.setWordWrap(True)
            label_message.setAlignment(Qt.AlignCenter)
            label_message.setStyleSheet("margin: 20px 0; font-size: 12px;")
            layout_dialog.addWidget(label_message)

            info_frame = QFrame()
            info_frame.setFrameStyle(QFrame.Box)
            info_frame.setStyleSheet("background-color: #f5f5f5; padding: 10px; border-radius: 5px;")
            info_layout = QVBoxLayout(info_frame)

            label_info = QLabel(f"Punto seleccionado:\nFecha: {row['fecha']}\nValor actual: {current_value:.4f} {unit}")
            label_info.setStyleSheet("font-size: 11px;")
            info_layout.addWidget(label_info)
            layout_dialog.addWidget(info_frame)

            buttons = QDialogButtonBox()
            btn_ok = QPushButton("Sí, Ajustar")
            btn_cancel = QPushButton("Cancelar")

            btn_ok.setStyleSheet("QPushButton { background-color: #d32f2f; color: white; font-weight: bold; padding: 8px 20px; border-radius: 4px; } QPushButton:hover { background-color: #b71c1c; }")
            btn_cancel.setStyleSheet("QPushButton { background-color: #757575; color: white; padding: 8px 20px; border-radius: 4px; } QPushButton:hover { background-color: #616161; }")

            buttons.addButton(btn_cancel, QDialogButtonBox.RejectRole)
            buttons.addButton(btn_ok, QDialogButtonBox.AcceptRole)
            layout_dialog.addWidget(buttons)

            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)

            if dialog.exec() == QDialog.Accepted:
                if callback:
                    tabla = f"prismas{idproyecto}"
                    callback(df, row['id'], row['nombre'], row['fecha'], variable, tabla)
                signal_handler.data_updated.emit(row['id'], row['nombre'], row['fecha'], variable, idproyecto, df)

        if Session.is_authenticated() and Session.get_idrole() != 3:
            plot_item.sigPointsClicked.connect(on_click)

        return signal_handler
