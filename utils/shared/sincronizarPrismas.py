from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTreeWidget


def sincronizarPrismasVisorADesplazamiento(main):
    """
    Toma los prismas marcados en el árbol de Visor y aplica el mismo estado
    (marcado/desmarcado) en el árbol compartido de Desplazamiento/Velocidad
    (tree_actual_desplazamiento), sin tocar Pluviómetros ni ningún otro tipo.
    """
    from modules.datos.equiposDesplazamiento import EquiposDesplazamiento

    tree_visor = main.findChild(QTreeWidget, "tree_actual_visor")
    tree_desplaza = main.findChild(QTreeWidget, "tree_actual_desplazamiento")
    if tree_visor is None or tree_desplaza is None:
        return

    # 1. Recolectar prismas marcados en Visor -> {(idcomponente, idinstrumento)}
    marcados = set()
    root_visor = tree_visor.invisibleRootItem()
    for i in range(root_visor.childCount()):
        zona = root_visor.child(i)
        idcomponente = zona.text(2)
        for j in range(zona.childCount()):
            grupo = zona.child(j)
            if grupo.text(0) == "Prismas":
                for k in range(grupo.childCount()):
                    prisma = grupo.child(k)
                    if prisma.text(1) == "prisma" and prisma.checkState(0) == Qt.Checked:
                        marcados.add((idcomponente, prisma.text(2)))

    # 2. Aplicar ese estado en el árbol de Desplazamiento (== Velocidad, mismo widget)
    tree_desplaza.blockSignals(True)
    try:
        root_desplaza = tree_desplaza.invisibleRootItem()
        for i in range(root_desplaza.childCount()):
            zona = root_desplaza.child(i)
            idcomponente = zona.text(2)
            for j in range(zona.childCount()):
                grupo = zona.child(j)
                if grupo.text(0) == "Prismas":
                    for k in range(grupo.childCount()):
                        prisma = grupo.child(k)
                        if prisma.text(1) != "prisma":
                            continue
                        clave = (idcomponente, prisma.text(2))
                        nuevo_estado = Qt.Checked if clave in marcados else Qt.Unchecked
                        if prisma.checkState(0) != nuevo_estado:
                            prisma.setCheckState(0, nuevo_estado)
                            prisma.setData(0, Qt.UserRole + 999, nuevo_estado)  # sincroniza memoria
            # recalcula visualmente PartiallyChecked/Checked/Unchecked de grupo y zona
            EquiposDesplazamiento.recalcular_jerarquia_visual(zona)
    finally:
        tree_desplaza.blockSignals(False)

    # 3. Refrescar gráficos (mismo tree_desplaza para Desplazamiento y Velocidad)
    #    Solo si esas vistas ya fueron inicializadas alguna vez en esta sesión
    from views.desplazamiento_view import DesplazamientoView
    from views.velocidad_view import VelocidadView

    if DesplazamientoView.main is not None:
        DesplazamientoView.obtenerMostrarPrismasMarcados(tree_desplaza)

    if VelocidadView.main is not None:
        VelocidadView.obtenerMostrarPrismasMarcados(tree_desplaza)