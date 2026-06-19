from PySide6.QtWidgets import (QWidget, QComboBox)
from utils.shared.graficaDesplazamientoVelocidad import procesar_grafica
from controllers.AnalisisController import AnalisisController

# ─────────────────────────────────────────────────────────────
#  Mapeo: clave_interna → (índice_columna_en_raw, etiqueta_leyenda)
# ─────────────────────────────────────────────────────────────

_DESPLAZAMIENTO_COLS = {
    "DA3D": (6,  "Despl. Acumulado 3D"),
    "DI3D": (7,  "Despl. Incremental 3D"),
    "DA2D": (8,  "Despl. Acumulado 2D"),
    "DI2D": (9,  "Despl. Incremental 2D"),
    "DASD": (10, "Despl. Acumulado SD"),
    "DISD": (11, "Despl. Incremental SD"),
    "DAES": (12, "Despl. Acumulado Este"),
    "DIES": (13, "Despl. Incremental Este"),
    "DANO": (14, "Despl. Acumulado Norte"),
    "DINO": (15, "Despl. Incremental Norte"),
    "DACO": (16, "Despl. Acumulado Cota"),
    "DICO": (17, "Despl. Incremental Cota"),
}

_VELOCIDAD_COLS = {
    "VI3D": (6,  "Vel. Incremental 3D"),
    "VA3D": (7,  "Vel. Acumulado 3D"),
    "VI2D": (8,  "Vel. Incremental 2D"),
    "VA2D": (9,  "Vel. Acumulado 2D"),
    "VISD": (10, "Vel. Incremental SD"),
    "VASD": (11, "Vel. Acumulado SD"),
}

# Todos los tipos en orden de aparición para cada modo
_TIPOS_DESPLAZAMIENTO = list(_DESPLAZAMIENTO_COLS.keys())
_TIPOS_VELOCIDAD      = list(_VELOCIDAD_COLS.keys())


def _pivotear_datos(raw, cols_map, tipos_seleccionados, idx_fecha=2, idx_dias=4, idx_horas=5):
    """
    Transforma filas multi-columna del modelo en filas de una sola lectura.
    """
    if not raw:
        return []

    resultado = []
    for tipo in tipos_seleccionados:
        if tipo not in cols_map:
            continue
        col_idx, etiqueta = cols_map[tipo]
        for fila in raw:
            id_inst  = fila[0]
            hora     = fila[idx_fecha]
            tipo_eq  = fila[3]
            dias     = fila[idx_dias]
            horas    = fila[idx_horas]
            lectura  = fila[col_idx]
            # id_serie único por tipo → cada tipo es una serie independiente
            id_serie = f"{id_inst}_{tipo}"
            resultado.append((
                id_serie,   # col[0] Instrumento (groupby)
                etiqueta,   # col[1] Equipo / leyenda
                hora,       # col[2] Fecha
                tipo_eq,    # col[3] tipo_equipo
                dias,       # col[4]
                horas,      # col[5]
                lectura,    # col[6] lectura (eje Y)
                tipo_eq,    # col[7] TipoPrisma (col[-1])
            ))

    return resultado


class GraficaComportamiento:

    @staticmethod
    def obtener_simbolo_unidad(tipografico, nombreunidad):
        if tipografico == "desplazamiento":
            labeleje = "Desplazamiento"
            tabla = {
                "Metros":       "(m)",
                "Centímetros":  "(cm)",
                "Milímetros":   "(mm)",
            }
            labely = tabla.get(nombreunidad, "(m)")
        else:
            labeleje = "Velocidad"
            tabla = {
                "Metros/día":        "(m/d)",
                "Centímetros/día":   "(cm/d)",
                "Milímetros/día":    "(mm/d)",
                "Metros/hora":       "(m/h)",
                "Centímetros/hora":  "(cm/h)",
                "Milímetros/hora":   "(mm/h)",
            }
            labely = tabla.get(nombreunidad, "(m/d)")
        return f"{labeleje} {labely}"

    # ─────────────────────────────────────────────────────────────
    #  Método principal
    # ─────────────────────────────────────────────────────────────

    def graficarComportamientoPrismas(main, idproyecto, fechainicial, fechafinal):
        widget           = main.findChild(QWidget,   "widget_graficas_comportamiento")
        comboComponentes = main.findChild(QComboBox, "combo_componentes_comportamiento")
        comboPrismas     = main.findChild(QComboBox, "combo_prismas_comportamiento")
        comboGraficas    = main.findChild(QComboBox, "combo_tiposgrafica_comportamiento")
        comboUnidades    = main.findChild(QComboBox, "combo_unidades_comportamiento")

        idcomponente  = comboComponentes.currentData()
        idinstrumento = comboPrismas.currentData()
        tipografica   = comboGraficas.currentData()   or "desplazamiento"
        unidadmedida  = comboUnidades.currentData()   or 1
        nombreunidad  = comboUnidades.currentText()
        nombreprisma  = comboPrismas.currentText()

        if not idinstrumento:
            return

        # ── 1. Datos crudos ───────────────────────────────────────
        datos = AnalisisController.ctrlObtenerDataComportamiento(
            idproyecto, idinstrumento, tipografica,
            unidadmedida, fechainicial, fechafinal
        )
        if not datos:
            return

        # ── 2. Seleccionar mapa de columnas y tipos ───────────────
        es_velocidad = (tipografica == "velocidad")

        if es_velocidad:
            cols_map          = _VELOCIDAD_COLS
            tipos_seleccionados = _TIPOS_VELOCIDAD
            tipo_col          = "VA3D"
            titulografica     = f"Velocidades del Prisma: {nombreprisma}"
        else:
            cols_map          = _DESPLAZAMIENTO_COLS
            tipos_seleccionados = _TIPOS_DESPLAZAMIENTO
            tipo_col          = "DA3D"
            titulografica     = f"Desplazamientos del Prisma: {nombreprisma}"

        label_eje = GraficaComportamiento.obtener_simbolo_unidad(tipografica, nombreunidad)

        # ── 3. Pivotar: una fila por (tipo, fecha) ────────────────
        datos_transformados = _pivotear_datos(
            datos,
            cols_map,
            tipos_seleccionados,
            idx_fecha=2,   # hora_prisma
            idx_dias=4,
            idx_horas=5,
        )

        if not datos_transformados:
            return

        # ── 4. Graficar ───────────────────────────────────────────
        procesar_grafica(
            widget,
            None,                 # labeltendencia
            datos_transformados,
            1,                    # idx_nombre  → col[1] = etiqueta leyenda
            2,                    # idx_fecha   → col[2] = hora_prisma
            6,                    # idx_lectura → col[6] = lectura
            "Fechas",
            label_eje,
            tipografica,             # graficatipo (para config de ejes)
            unidadmedida,
            "FECHA",
            titulografica,
            idproyecto,
            "ANALISIS",
            None,                 # pluviometro_data
            None,                 # equipostendencia
            None,                 # escala
            fechainicial,
            fechafinal,
        )
    