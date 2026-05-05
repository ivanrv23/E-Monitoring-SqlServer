import os
from PySide6.QtWidgets import QTreeWidgetItem
from PySide6.QtCore import Qt
from pathlib import Path
from utils.common.rutasarchivos import resource_path

class TreeCheckbox:
    
    def limpiarArbolCheckboxes(tree_widget, proyecto_name):
        tree_widget.clear()
        tree_widget.setHeaderLabels([proyecto_name.upper()])
            
    def comprobarExistenciaGrupoCheckboxes(treewidget, nombregrupo, idzona):
        root_item = treewidget.invisibleRootItem()
        for i in range(root_item.childCount()):
            item = root_item.child(i)
            if item.text(0) == nombregrupo and item.text(2) == str(idzona):
                return True
        return False
    
    def validarSubgrupoCheckbox(parent_item, grupoequipo):
        existe, childitem = False, None
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            if child.text(0) == grupoequipo:
                existe, childitem = True, child
                break
        return existe, childitem
    
    def crearNuevoGrupoCheckboxesSimple(treewidget, nombrezona, idzona, idproyecto, grupoequipo, tipogrupo, equipos, tipoequipo, config="NO"):
        if not TreeCheckbox.comprobarExistenciaGrupoCheckboxes(treewidget, nombrezona, idzona):
            parent_item = QTreeWidgetItem(treewidget)
            parent_item.setText(0, nombrezona)
            parent_item.setText(1, "0")
            parent_item.setText(2, str(idzona))
            parent_item.setText(3, str(idproyecto))
            parent_item.setCheckState(0, Qt.Unchecked)
            parent_item.setData(0, Qt.UserRole + 999, Qt.Unchecked) # Memoria
            parent_item.setFlags(parent_item.flags() | Qt.ItemIsUserCheckable)
        # Crear grupo de equipos
        root_item = treewidget.invisibleRootItem()
        for i in range(root_item.childCount()):
            item = root_item.child(i)
            if item.text(0) == nombrezona and item.text(2) == str(idzona):
                existe, child_item = TreeCheckbox.validarSubgrupoCheckbox(item, grupoequipo)
                if not existe:
                    child_item = QTreeWidgetItem(item)
                    child_item.setText(0, grupoequipo) # prismas, inclinometros, piezometros, etc
                    child_item.setText(1, tipogrupo)
                    child_item.setText(2, str(idzona))
                    child_item.setText(3, str(idproyecto))
                    child_item.setCheckState(0, Qt.Unchecked)
                    child_item.setData(0, Qt.UserRole + 999, Qt.Unchecked) # Memoria
                    child_item.setFlags(child_item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable)
                for dato in equipos:
                    kid_item = QTreeWidgetItem(child_item)
                    kid_item.setText(0, str(dato[3])) # nombre
                    kid_item.setText(1, tipoequipo)
                    kid_item.setText(2, str(dato[0])) # id instrum
                    if config == "SI":
                        kid_item.setText(3, str(dato[7])) # lista de fechas
                    else:
                        kid_item.setText(3, str(dato[4])) # idequipo o tabla
                    kid_item.setCheckState(0, Qt.Unchecked)
                    kid_item.setData(0, Qt.UserRole + 999, Qt.Unchecked) # Memoria
                    kid_item.setFlags(kid_item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable)
    
    def crearNuevoGrupoCheckboxesDoble(treewidget, nombrezona, idzona, idproyecto, grupoequipo, tipogrupo, equipos, tipoequipo, config="NO"):
        if not TreeCheckbox.comprobarExistenciaGrupoCheckboxes(treewidget, nombrezona, idzona):
            parent_item = QTreeWidgetItem(treewidget)
            parent_item.setText(0, nombrezona)
            parent_item.setText(1, "0")
            parent_item.setText(2, str(idzona))
            parent_item.setText(3, str(idproyecto))
            parent_item.setCheckState(0, Qt.Unchecked)
            parent_item.setData(0, Qt.UserRole + 999, Qt.Unchecked) # Memoria
            parent_item.setFlags(parent_item.flags() | Qt.ItemIsUserCheckable)
        # Crear grupo de equipos
        root_item = treewidget.invisibleRootItem()
        for i in range(root_item.childCount()):
            item = root_item.child(i)
            if item.text(0) == nombrezona and item.text(2) == str(idzona):
                existe, child_item = TreeCheckbox.validarSubgrupoCheckbox(item, grupoequipo)
                if not existe:
                    child_item = QTreeWidgetItem(item)
                    child_item.setText(0, grupoequipo) # prismas, inclinometros, piezometros, etc
                    child_item.setText(1, tipogrupo)
                    child_item.setText(2, str(idzona))
                    child_item.setText(3, str(idproyecto))
                    child_item.setCheckState(0, Qt.Unchecked)
                    child_item.setData(0, Qt.UserRole + 999, Qt.Unchecked) # Memoria
                    child_item.setFlags(child_item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable)
                for dato in equipos:
                    kid_item = QTreeWidgetItem(child_item)
                    kid_item.setText(0, str(dato[3])) # nombre
                    kid_item.setText(1, tipoequipo)
                    kid_item.setText(2, str(dato[0])) # id instrum
                    if config == "SI":
                        kid_item.setText(3, str(dato[7])) # lista de fechas
                    else:
                        kid_item.setText(3, str(dato[4])) # idequipo o tabla
                    kid_item.setCheckState(0, Qt.Unchecked)
                    kid_item.setData(0, Qt.UserRole + 999, Qt.Unchecked) # Memoria
                    kid_item.setFlags(kid_item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable)
                    # Agregar cotas
                    if tipoequipo == "piezometrocuerda" or tipoequipo == "piezometromanual" or tipoequipo == "celda":
                        for cota in ["Cota de Superficie", "Cota de Fundación"]:
                            baby_item = QTreeWidgetItem(kid_item)
                            baby_item.setText(0, cota) # cotas
                            if tipoequipo == "piezometrocuerda":
                                baby_item.setText(1, "cotacuerda")
                            elif tipoequipo == "piezometromanual":
                                baby_item.setText(1, "cotamanual")
                            else:
                                baby_item.setText(1, "cotacelda")
                            baby_item.setText(2, str(dato[0]))
                            baby_item.setText(3, str(dato[4]))
                            baby_item.setCheckState(0, Qt.Unchecked)
                            baby_item.setData(0, Qt.UserRole + 999, Qt.Unchecked) # Memoria
                            baby_item.setFlags(baby_item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable)
    
    def crearGrupoCheckboxDobleTopografia(treewidget, nombrezona, idzona, idproyecto, grupoequipo, tipogrupo, equipos, tipoequipo):
        if not TreeCheckbox.comprobarExistenciaGrupoCheckboxes(treewidget, nombrezona, idzona):
            parent_item = QTreeWidgetItem(treewidget)
            parent_item.setText(0, nombrezona)
            parent_item.setText(1, "0")
            parent_item.setText(2, str(idzona))
            parent_item.setText(3, str(idproyecto))
            parent_item.setCheckState(0, Qt.Unchecked)
            parent_item.setData(0, Qt.UserRole + 999, Qt.Unchecked) # Memoria
            parent_item.setFlags(parent_item.flags() | Qt.ItemIsUserCheckable)
        # Crear grupo de equipos
        root_item = treewidget.invisibleRootItem()
        for i in range(root_item.childCount()):
            item = root_item.child(i)
            if item.text(0) == nombrezona and item.text(2) == str(idzona):
                existe, child_item = TreeCheckbox.validarSubgrupoCheckbox(item, grupoequipo)
                if not existe:
                    child_item = QTreeWidgetItem(item)
                    child_item.setText(0, grupoequipo)
                    child_item.setText(1, tipogrupo)
                    child_item.setText(2, str(idzona))
                    child_item.setText(3, str(idproyecto))
                    child_item.setCheckState(0, Qt.Unchecked)
                    child_item.setData(0, Qt.UserRole + 999, Qt.Unchecked) # Memoria
                    child_item.setFlags(child_item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable)
                for dato in equipos:
                    kid_item = QTreeWidgetItem(child_item)
                    kid_item.setText(0, str(dato[3]))
                    kid_item.setText(1, tipoequipo)
                    kid_item.setText(2, str(dato[0]))
                    kid_item.setText(3, str(dato[4]))
                    kid_item.setCheckState(0, Qt.Unchecked)
                    kid_item.setData(0, Qt.UserRole + 999, Qt.Unchecked) # Memoria
                    kid_item.setFlags(kid_item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable)
                    # Listar actores...
                    tipotopo = dato[10]
                    if tipotopo == "VTP":
                        ruta_archivos = resource_path(dato[11])
                        archivos = [f for f in os.listdir(ruta_archivos) if f.endswith('.vtp')]
                        for i, archivo in enumerate(archivos):
                            nombre_sin_extension = os.path.splitext(archivo)[0]
                            nombre_base = nombre_sin_extension.split('_')[0]
                            baby_item = QTreeWidgetItem(kid_item)
                            baby_item.setText(0, f"{i+1} {nombre_base}")
                            baby_item.setText(1, "actortopo")
                            baby_item.setText(2, str(dato[0]))
                            baby_item.setText(3, f"{dato[11]}/{archivo}")
                            baby_item.setText(4, str(tipotopo))
                            baby_item.setCheckState(0, Qt.Unchecked)
                            baby_item.setData(0, Qt.UserRole + 999, Qt.Unchecked) # Memoria
                            baby_item.setFlags(baby_item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable)
                    else:
                        extension_sin_punto = Path(dato[11]).suffix[1:].upper()
                        baby_item = QTreeWidgetItem(kid_item)
                        baby_item.setText(0, f"1 {extension_sin_punto}")
                        baby_item.setText(1, "actortopo")
                        baby_item.setText(2, str(dato[0]))
                        baby_item.setText(3, str(dato[11]))
                        baby_item.setText(4, str(tipotopo))
                        baby_item.setCheckState(0, Qt.Unchecked)
                        baby_item.setData(0, Qt.UserRole + 999, Qt.Unchecked) # Memoria
                        baby_item.setFlags(baby_item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable)
                        
    def agregarCheckboxGrupo(treewidget, nombregrupo, nombretool, tipolista, idtool):
        root_item = treewidget.invisibleRootItem()
        for i in range(root_item.childCount()):
            item = root_item.child(i)
            if item.text(0) == nombregrupo:
                child_item = QTreeWidgetItem(item)
                child_item.setText(0, nombretool)
                child_item.setText(1, tipolista)
                child_item.setText(2, str(idtool))
                child_item.setCheckState(0, Qt.Checked)
                child_item.setFlags(child_item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable)
                return
    
    def actualizarTextoCheckboxParent(treewidget, nombregrupo, idplano, nuevonombreplano):
        if TreeCheckbox.comprobarExistenciaGrupoCheckboxes(treewidget, nombregrupo, idplano):
            root_item = treewidget.invisibleRootItem()
            for i in range(root_item.childCount()):
                parent = root_item.child(i)
                if parent.text(0) == nombregrupo and parent.text(2) == str(idplano):
                    parent.setText(0, nuevonombreplano)
    
    def actualizarTextoCheckboxEquipo(treewidget, idzona, nombregrupo, tipolista, nombreequipo, nuevonombre):
        root_item = treewidget.invisibleRootItem()
        for i in range(root_item.childCount()):
            zona_item = root_item.child(i) # componente
            if zona_item.text(2) == idzona:
                for j in range(zona_item.childCount()):
                    group_item = zona_item.child(j) # grupo
                    if group_item.text(0) == nombregrupo:
                        for k in range(group_item.childCount()):
                            checkbox_item = group_item.child(k) # equipo
                            if checkbox_item.text(0) == str(nombreequipo) and checkbox_item.text(1) == tipolista:
                                checkbox_item.setText(0, nuevonombre)
    
    def eliminarCheckboxParent(treewidget, nombregrupo, idgrupo):
        estado = False
        root_item = treewidget.invisibleRootItem()
        # Recorremos los items del root
        if TreeCheckbox.comprobarExistenciaGrupoCheckboxes(treewidget, nombregrupo, idgrupo):
            for i in range(root_item.childCount()):
                group_item = root_item.child(i)
                if group_item.text(0) == nombregrupo:
                    for j in range(group_item.childCount()):
                        checkbox_item = group_item.child(j)
                        TreeCheckbox.eliminar_hijos_recursivamente(checkbox_item)
                        group_item.removeChild(checkbox_item)
                        if group_item.childCount() == 0:
                            root_item.removeChild(group_item)
                        estado = True
        return estado
    
    def eliminar_hijos_recursivamente(item):
        for i in range(item.childCount() - 1, -1, -1):
            child = item.child(i)
            if child.childCount() > 0:
                TreeCheckbox.eliminar_hijos_recursivamente(child)
            item.removeChild(child)
                                
    def actualizarTextoCheckbox(treewidget, nombregrupo, idplano, nuevonombreplano):
        root_item = treewidget.invisibleRootItem()
        for i in range(root_item.childCount()):
            item = root_item.child(i)
            if item.text(0) == nombregrupo:
                for j in range(item.childCount()):
                    child_item = item.child(j)
                    if child_item.text(2) == str(idplano):  # Comparar el ID del plano
                        # Actualizar el texto del checkbox
                        child_item.setText(0, nuevonombreplano)
                        return True
        return False
    
    def eliminarCheckboxGrupo(treewidget, codegrupo, nombregrupo, tipolista):
        estado = False
        root_item = treewidget.invisibleRootItem()
        if not root_item:
            return estado
        i = 0
        while i < root_item.childCount():
            group_item = root_item.child(i)
            if not group_item:
                i += 1
                continue
            if group_item.text(1) == "0" and group_item.text(2) == codegrupo:
                j = 0
                while j < group_item.childCount():
                    checkbox_item = group_item.child(j)
                    if not checkbox_item:
                        j += 1
                        continue
                    if checkbox_item.text(0) == nombregrupo and checkbox_item.text(1) == tipolista and checkbox_item.text(2) == codegrupo:
                        TreeCheckbox.eliminar_hijos_recursivamente(checkbox_item)
                        group_item.removeChild(checkbox_item)
                        estado = True
                        if group_item.childCount() == 0:
                            root_item.removeChild(group_item)
                            continue
                    j += 1
            i += 1
        return estado
    
    def eliminarCheckbox(treewidget, nombregrupo, codecheckbox, tipolista):
        root_item = treewidget.invisibleRootItem()
        for i in range(root_item.childCount()):
            zona_item = root_item.child(i) # componente
            for j in range(zona_item.childCount()):
                group_item = zona_item.child(j) # grupo
                if group_item.text(0) == str(nombregrupo):
                    for k in range(group_item.childCount()):
                        checkbox_item = group_item.child(k) # check
                        if checkbox_item.text(1) == str(tipolista) and checkbox_item.text(2) == str(codecheckbox):
                            # Eliminar el checkbox seleccionado
                            group_item.removeChild(checkbox_item)
                            # Si el grupo queda vacío, eliminar el grupo
                            if group_item.childCount() == 0:
                                zona_item.removeChild(group_item)
                            if zona_item.childCount() == 0:
                                root_item.removeChild(zona_item)
                            return True
        return False
    
    def eliminarCheckboxPrisma(treewidget, nombregrupo, idcomponente, tipolista, nombreequipo, tipotabla):
        root_item = treewidget.invisibleRootItem()
        if not root_item:
            return
        for i in range(root_item.childCount() - 1, -1, -1):  
            zona_item = root_item.child(i)  # Componente
            if zona_item and zona_item.text(2) == str(idcomponente):
                for j in range(zona_item.childCount() - 1, -1, -1):  
                    group_item = zona_item.child(j)  # Grupo
                    if group_item and group_item.text(0) == str(nombregrupo) and group_item.text(2) == str(idcomponente):
                        for k in range(group_item.childCount() - 1, -1, -1):  
                            checkbox_item = group_item.child(k)  # Checkbox
                            if (checkbox_item and checkbox_item.text(1) == str(tipolista) and
                                checkbox_item.text(0) == str(nombreequipo) and
                                checkbox_item.text(3) == str(tipotabla)):
                                # Eliminar el checkbox seleccionado
                                group_item.removeChild(checkbox_item)
                        # Si el grupo queda vacío, eliminar el grupo
                        if group_item.childCount() == 0:
                            zona_item.removeChild(group_item)
                # Si la zona queda vacía, eliminar la zona
                if zona_item.childCount() == 0:
                    root_item.removeChild(zona_item)
    
    def eliminarCheckboxTopografia(treewidget, nombregrupo, tipolista, idinstrumento, listactor, rutactor):
        root_item = treewidget.invisibleRootItem()
        for i in range(root_item.childCount()):
            zona_item = root_item.child(i) # componente
            for j in range(zona_item.childCount()):
                group_item = zona_item.child(j) # grupo
                if group_item.text(0) == str(nombregrupo):
                    for k in range(group_item.childCount()):
                        checkbox_item = group_item.child(k) # Topografía
                        if checkbox_item.text(1) == str(tipolista) and checkbox_item.text(2) == str(idinstrumento):
                            for l in range(checkbox_item.childCount()):
                                actor_item = checkbox_item.child(l) # actor
                                if actor_item.text(1) == str(listactor) and actor_item.text(2) == str(idinstrumento) and actor_item.text(3) == str(rutactor):
                                    # Eliminar el checkbox seleccionado
                                    checkbox_item.removeChild(actor_item)
                                    # Si el grupo queda vacío, eliminar el grupo
                                    if checkbox_item.childCount() == 0:
                                        group_item.removeChild(checkbox_item)
                                    if group_item.childCount() == 0:
                                        zona_item.removeChild(zona_item)
                                    if zona_item.childCount() == 0:
                                        root_item.removeChild(zona_item)
                                    return True
        return False
    
    def validarMarcadoCheckbox(parent_item, column):
        codigo = parent_item.text(1)
        estado = parent_item.checkState(0)
        if estado != Qt.CheckState.PartiallyChecked:
            if codigo.isdigit():
                for i in range(parent_item.childCount()):
                    hijo = parent_item.child(i)
                    hijo.setCheckState(0, estado)
            else:
                TreeCheckbox.actualizar_estado_padre_hijos(parent_item)
    
    def actualizar_estado_padre_hijos(nodo):
        if nodo.parent():
            estados_hijos = [nodo.parent().child(i).checkState(0) for i in range(nodo.parent().childCount())]
            if all(estado == Qt.Checked for estado in estados_hijos):
                nuevo_estado = Qt.Checked
            elif all(estado == Qt.Unchecked for estado in estados_hijos):
                nuevo_estado = Qt.Unchecked
            else:
                nuevo_estado = Qt.PartiallyChecked
            
            nodo.parent().setCheckState(0, nuevo_estado)
            # SINCRONIZACIÓN DE MEMORIA: Vital para que el padre no tenga delay después
            nodo.parent().setData(0, Qt.UserRole + 999, nuevo_estado)
            # Recursión para subir en el árbol
            TreeCheckbox.actualizar_estado_padre_hijos(nodo.parent())
    
    def validarMarcadoUnicoCheckbox(parent_item, column):
        codigo = parent_item.text(1)
        estado = parent_item.checkState(0)
        if codigo.isdigit():
            parent_item.setCheckState(0, Qt.PartiallyChecked)
            if parent_item.childCount() > 0:
                for i in range(parent_item.childCount()):
                    hijo = parent_item.child(i)
                    hijo.setCheckState(0, Qt.Unchecked)
                ultimo_hijo = parent_item.child(parent_item.childCount() - 1)
                ultimo_hijo.setCheckState(0, Qt.Checked)
        else:
            for i in range(parent_item.parent().childCount()):
                hijo = parent_item.parent().child(i)
                hijo.setCheckState(0, Qt.Unchecked)
            parent_item.setCheckState(0, Qt.Checked)
            TreeCheckbox.actualizar_estado_padre_hijos(parent_item)
    
    def actualizarFechasCheckboxEquipo(treewidget, idzona, nombregrupo, tipolista, nombreequipo, nuevasfechas):
        root_item = treewidget.invisibleRootItem()
        for i in range(root_item.childCount()):
            zona_item = root_item.child(i) # componente
            if zona_item.text(2) == idzona:
                for j in range(zona_item.childCount()):
                    group_item = zona_item.child(j) # grupo
                    if group_item.text(0) == nombregrupo:
                        for k in range(group_item.childCount()):
                            checkbox_item = group_item.child(k) # equipo
                            if checkbox_item.text(0) == str(nombreequipo) and checkbox_item.text(1) == tipolista:
                                checkbox_item.setText(3, str(nuevasfechas))
    
    @staticmethod
    def validarCambioReal(item):
        """ Retorna True si el checkbox cambió, False si fue clic en el nombre """
        estado_memoria = item.data(0, Qt.UserRole + 999)
        estado_actual = item.checkState(0)
        if estado_memoria == estado_actual:
            return False
        item.setData(0, Qt.UserRole + 999, estado_actual)
        return True