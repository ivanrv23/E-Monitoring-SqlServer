from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTreeWidget, QStackedWidget


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
                            prisma.setData(0, Qt.UserRole + 999, nuevo_estado)
            EquiposDesplazamiento.recalcular_jerarquia_visual(zona)
    finally:
        tree_desplaza.blockSignals(False)

    from views.desplazamiento_view import DesplazamientoView
    from views.velocidad_view import VelocidadView

    if DesplazamientoView.main is not None:
        DesplazamientoView.obtenerMostrarPrismasMarcados(tree_desplaza)

    if VelocidadView.main is not None:
        VelocidadView.obtenerMostrarPrismasMarcados(tree_desplaza)


def sincronizarPrismasDesplazamientoAVisor(main):
    """
    Toma los prismas marcados en el árbol compartido de Desplazamiento/Velocidad
    (tree_actual_desplazamiento) y aplica el mismo estado en el árbol de Visor
    (tree_actual_visor), sin tocar Pluviómetros ni ningún otro tipo.
    """
    from modules.datos.equiposVisor import EquiposVisor

    tree_desplaza = main.findChild(QTreeWidget, "tree_actual_desplazamiento")
    tree_visor = main.findChild(QTreeWidget, "tree_actual_visor")
    if tree_desplaza is None or tree_visor is None:
        return

    marcados = set()
    root_desplaza = tree_desplaza.invisibleRootItem()
    for i in range(root_desplaza.childCount()):
        zona = root_desplaza.child(i)
        idcomponente = zona.text(2)
        for j in range(zona.childCount()):
            grupo = zona.child(j)
            if grupo.text(0) == "Prismas":
                for k in range(grupo.childCount()):
                    prisma = grupo.child(k)
                    if prisma.text(1) == "prisma" and prisma.checkState(0) == Qt.Checked:
                        marcados.add((idcomponente, prisma.text(2)))

    tree_visor.blockSignals(True)
    try:
        root_visor = tree_visor.invisibleRootItem()
        for i in range(root_visor.childCount()):
            zona = root_visor.child(i)
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
                            prisma.setData(0, Qt.UserRole + 999, nuevo_estado)
            EquiposVisor.recalcular_jerarquia_visual(zona)
    finally:
        tree_visor.blockSignals(False)

    from views.visor_view import VisorView

    if VisorView.main is not None:
        paginacion = VisorView.main.findChild(QStackedWidget, "stacked_visor")
        VisorView.obtenerMostrarEquiposMarcados(tree_visor, paginacion)

def _buscar_nodo_equivalente(tree_destino, tipo, idcomponente, idinstrumento):
    root_destino = tree_destino.invisibleRootItem()
    for i in range(root_destino.childCount()):
        zona = root_destino.child(i)
        if zona.text(2) != idcomponente:
            continue
        for j in range(zona.childCount()):
            grupo = zona.child(j)
            for k in range(grupo.childCount()):
                candidato = grupo.child(k)
                if candidato.text(1) == tipo and candidato.text(2) == idinstrumento:
                    return candidato
    return None


def sincronizarSeleccionEntreArboles(tree_destino, item_origen):
    """
    Dado el item recién resaltado en el árbol de origen (tipo 'prisma' o
    'pluviometro'), busca el nodo equivalente en tree_destino y lo resalta,
    expandiendo sus padres y haciendo scroll hasta él, sin disparar señales
    del árbol destino.
    """
    if item_origen is None:
        return

    tipo = item_origen.text(1)
    if tipo not in ("prisma", "pluviometro"):
        return

    padre_grupo = item_origen.parent()
    if padre_grupo is None or padre_grupo.parent() is None:
        return
    idcomponente = padre_grupo.parent().text(2)
    idinstrumento = item_origen.text(2)

    nodo_destino = _buscar_nodo_equivalente(tree_destino, tipo, idcomponente, idinstrumento)
    if nodo_destino is None:
        return

    tree_destino.blockSignals(True)
    try:
        padre = nodo_destino.parent()
        while padre is not None:
            padre.setExpanded(True)
            padre = padre.parent()
        tree_destino.setCurrentItem(nodo_destino)
        tree_destino.scrollToItem(nodo_destino)
    finally:
        tree_destino.blockSignals(False)


def sincronizarSeleccionVisorADesplazamiento(main, item_actual):
    tree_desplaza = main.findChild(QTreeWidget, "tree_actual_desplazamiento")
    if tree_desplaza is None:
        return
    sincronizarSeleccionEntreArboles(tree_desplaza, item_actual)


def sincronizarSeleccionDesplazamientoAVisor(main, item_actual):
    tree_visor = main.findChild(QTreeWidget, "tree_actual_visor")
    if tree_visor is None:
        return
    sincronizarSeleccionEntreArboles(tree_visor, item_actual)