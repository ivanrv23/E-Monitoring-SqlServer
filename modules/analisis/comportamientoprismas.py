from PySide6.QtWidgets import (QWidget, QComboBox)
from utils.shared.graficaDesplazamientoVelocidad import procesar_grafica
from controllers.AnalisisController import AnalisisController
from controllers.InterfazController import InterfazController
from utils.shared.personalizacion import Personalizacion

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
_TIPOS_VELOCIDAD = list(_VELOCIDAD_COLS.keys())


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

def _filtrar_por_preferencias(datos_transformados, prefs_actuales, cols_map):
    """
    Filtra datos_transformados según las preferencias marcadas.
    
    - Si prefs_actuales está vacío → retorna todos los datos sin filtrar.
    - Si hay preferencias → extrae las claves internas cuyos índices de columna
      coincidan con los id_instrumentacion de las preferencias, luego filtra
      las filas cuyo id_serie contenga alguna de esas claves.

    Args:
        datos_transformados: Lista de tuplas pivotadas.
        prefs_actuales:      Lista de (id_componente, id_instrumentacion) o [].
        cols_map:            _VELOCIDAD_COLS o _DESPLAZAMIENTO_COLS.

    Returns:
        Lista filtrada de tuplas.
    """
    # Sin preferencias → mostrar todo
    if not prefs_actuales:
        return datos_transformados

    # Obtener los índices de columna permitidos desde las preferencias
    # id_instrumentacion corresponde al col_idx en cols_map
    indices_permitidos = {id_inst for (_, id_inst) in prefs_actuales}

    # Mapear col_idx → clave_interna  (ej: 6 → "VI3D", 7 → "VA3D")
    idx_a_clave = {col_idx: clave for clave, (col_idx, _) in cols_map.items()}

    # Claves internas permitidas (ej: {"VI3D", "VA3D"})
    claves_permitidas = {
        idx_a_clave[idx]
        for idx in indices_permitidos
        if idx in idx_a_clave
    }

    if not claves_permitidas:
        return []

    # Filtrar: id_serie tiene formato "{id_inst}_{tipo}"
    # Extraemos la parte después del primer '_' para obtener el tipo
    resultado = [
        fila for fila in datos_transformados
        if fila[0].split("_", 1)[-1] in claves_permitidas
    ]
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
        
        # ── 4. Obtener lista de preferencia marcado ───────────────
        if tipografica == "velocidad":
            tipo = "VELOCIDADANALISIS"
        else:
            tipo = "DESPLAZAMIENTOANALISIS"
        prefs_actuales = InterfazController.ctrlObtenerPreferenciasMarcado(idproyecto, tipo)
        if prefs_actuales is None:
            prefs_actuales = []

        # ── 5. Filtrar datos según preferencias ───────────────────
        datos_transformados = _filtrar_por_preferencias(datos_transformados, prefs_actuales, cols_map)
        if not datos_transformados:
            return

        # ── 6. Graficar ───────────────────────────────────────────
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
    
    @staticmethod
    def configurarMarcadoDesmarcado(idproyecto, idcomponente, tipografica, reiniciar):
        if tipografica == "velocidad":
            tipo = "VELOCIDADANALISIS"
            cols_map = _VELOCIDAD_COLS
        else:
            tipo = "DESPLAZAMIENTOANALISIS"
            cols_map = _DESPLAZAMIENTO_COLS
        prefs_actuales = InterfazController.ctrlObtenerPreferenciasMarcadoAnalisis(idproyecto, tipo)
        if prefs_actuales is None: prefs_actuales = []
        def callback_guardar(lista_datos):
            lista_preferencias = [(idcomponente, clave) for clave in lista_datos]
            return InterfazController.ctrlGuardarPreferenciasMarcado(idproyecto, tipo, lista_preferencias)
        # Mostrar dialogo
        Personalizacion.dialogoConfigurarMarcadoAnalisis(cols_map, prefs_actuales, callback_guardar, reiniciar)

    