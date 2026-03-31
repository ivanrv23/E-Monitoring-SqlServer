from PySide6.QtWidgets import (QWidget, QComboBox)
from utils.shared.graficaDesplazamientoVelocidad import procesar_grafica
from controllers.AnalisisController import AnalisisController

class GraficaTiempoReal:
    
    # ─────────────────────────────────────────────────────────────
    #  Helper: obtener título y labels según tipo de gráfico
    # ─────────────────────────────────────────────────────────────

    @staticmethod
    def obtener_titulo_labels(instrumento, tipografico, unidad):
        equipos = {
            "PRISMA": "Prismas",
            "PIEZOMETROCUERDA": "Piezómetros Cuerda Vibrante",
            "CELDA": "Celdas de Asentamiento",
        }
        tipos = {
            "3DA": "Desplazamiento",
            "3DI": "Desplazamiento",
            "2DA": "Desplazamiento",
            "2DI": "Desplazamiento",
            "SDA": "Desplazamiento",
            "SDI": "Desplazamiento",
            "DEA": "Desplazamiento",
            "DEI": "Desplazamiento",
            "DNA": "Desplazamiento",
            "DNI": "Desplazamiento",
            "DZA": "Desplazamiento",
            "DZI": "Desplazamiento",

            "VA3D": "Velocidad",
            "VI3D": "Velocidad",
            "VA2D": "Velocidad",
            "VI2D": "Velocidad",
            "VASD": "Velocidad",
            "VISD": "Velocidad",

            "PCNF": "Nivel Freático",
            "PCNA": "Nivel Acumulado",
            "PCNI": "Nivel Incremental",
            # "PMNF": "Nivel Freático",
            # "PMNA": "Nivel Acumulado",
            # "PMNI": "Nivel Incremental",
            "CANA": "Nivel Asentamiento",
            "CAAA": "Asentamiento",
            "CAAI": "Asentamiento",
        }
        titulos = {
            "3DA": "Desplazamiento Acumulado 3D",
            "3DI": "Desplazamiento Incremental 3D",
            "2DA": "Desplazamiento Acumulado 2D",
            "2DI": "Desplazamiento Incremental 2D",
            "SDA": "Desplazamiento Acumulado SD",
            "SDI": "Desplazamiento Incremental SD",
            "DEA": "Desplazamiento Acumulado Este",
            "DEI": "Desplazamiento Incremental Este",
            "DNA": "Desplazamiento Acumulado Norte",
            "DNI": "Desplazamiento Incremental Norte",
            "DZA": "Desplazamiento Acumulado Cota",
            "DZI": "Desplazamiento Incremental Cota",

            "VA3D": "Velocidad Acumulada 3D",
            "VI3D": "Velocidad Incremental 3D",
            "VA2D": "Velocidad Acumulada 2D",
            "VI2D": "Velocidad Incremental 2D",
            "VASD": "Velocidad Acumulada SD",
            "VISD": "Velocidad Incremental SD",

            "PCNF": "Nivel Freático",
            "PCNA": "Nivel Acumulado",
            "PCNI": "Nivel Incremental",
            # "PMNF": "Nivel Freático",
            # "PMNA": "Nivel Acumulado",
            # "PMNI": "Nivel Incremental",
            "CANA": "Nivel Asentamiento",
            "CAAA": "Asentamiento Acumulado",
            "CAAI": "Asentamiento Incremental",
        }
        if unidad == 1:
            labely = "(m)"
        elif unidad == 100:
            labely = "(cm)"
        elif unidad == 1000:
            labely = "(mm)"
        else:
            labely = "(u)"
        if tipografico in ("PCNF", "PMNF", "CANA"):
            labely = "(msnm)"
        
        title = titulos.get(tipografico, "Gráfico")
        instrument = equipos.get(instrumento, "Equipos")
        titulo = f"{title} - {instrument}"

        tipo = tipos.get(tipografico, "Valor")
        etiqueta = f"{tipo} {labely}"

        return titulo, etiqueta

    def graficarDatosTimpoReal(main, idproyecto):
        widget = main.findChild(QWidget, "widget_graficas_tiemporeal")
        comboComponentes = main.findChild(QComboBox, "combo_componentes_tiemporeal")
        comboInstrumentos = main.findChild(QComboBox, "combo_instrumentos_tiemporeal")
        comboTipograficas = main.findChild(QComboBox, "combo_tipografica_tiemporeal")
        comboUnidades = main.findChild(QComboBox, "combo_unidades_tiemporeal")
        idcomponente = comboComponentes.currentData()
        instrumento = comboInstrumentos.currentData() or "PRISMA"
        tipografico = comboTipograficas.currentData() or "3DA"
        unidad = comboUnidades.currentData() or 1
        titulografica, labely = GraficaTiempoReal.obtener_titulo_labels(instrumento, tipografico, unidad)
        unidadtiempo = "FECHA"
        escala = None
        datos = AnalisisController.ctrlObtenerDataTiempoReal(idproyecto, idcomponente, instrumento, tipografico, unidad)
        if datos:
            graficatipo = f"{instrumento}{tipografico}"
            labeltendencia = None
            modulo, pluviometros, tendencias = "ANALISIS", None, None
            indexnombre, idx_fecha, idx_lectura, labelejex = 1, 2, 3, "Fechas"
            procesar_grafica(widget, labeltendencia, datos, indexnombre, idx_fecha, idx_lectura, labelejex, labely, graficatipo, unidad, unidadtiempo, titulografica, idproyecto, modulo, pluviometros, tendencias, escala)

    