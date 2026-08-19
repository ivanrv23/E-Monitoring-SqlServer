from PySide6.QtWidgets import QMenu
from PySide6.QtCore import Qt
from utils.common.alertas import mostrar_mensaje
from utils.shared.arbolmarcado import TreeCheckbox
from modules.proyecto.crearProyecto import CrearProyecto
from modules.datos.subirAcelerografos import SubirAcelerografos
from controllers.InterfazController import InterfazController

class EquiposAcelerografos:
    
    def validarMarcadoCheckbox(parent_item, column, treeWidget, graficarEquiposMarcados):
        nombre = parent_item.text(column)
        codigo = parent_item.text(1)
        estado = parent_item.checkState(0)
        idgrupo = parent_item.text(2)
        tipogrupo = parent_item.text(3)
        nombremarcado = (nombre, idgrupo, tipogrupo)
        if estado != Qt.CheckState.PartiallyChecked:
            # comprobar si el código es numérico (primer nivel)
            if codigo.isdigit():
                equipos = EquiposAcelerografos.obtener_todos_elementos_arbol(treeWidget)
                if codigo == "0": # COMPONENTE
                    if estado == Qt.Checked:
                        if EquiposAcelerografos.validarMarcadoUnEquipoZona(equipos, nombremarcado):
                            # limpiar inclinometros
                            EquiposAcelerografos.limpiarEquiposTipo(treeWidget)
                            parent_item.setCheckState(0, Qt.Checked)
                            EquiposAcelerografos.marcardesmarcar_todos_hijos(parent_item, estado)
                        else:
                            if estado == Qt.CheckState.Checked:
                                mostrar_mensaje("MARCACIÓN MÚLTIPLE", "Solo debe marcar un Acelerógrafo.", "advertencia")
                                EquiposAcelerografos.actualizar_estado_padre_padre(parent_item)
                    elif estado == Qt.Unchecked:
                        EquiposAcelerografos.marcardesmarcar_todos_hijos(parent_item, estado)
                else:
                    zonamarcada = (parent_item.parent().text(0), parent_item.parent().text(2), parent_item.parent().text(3))
                    if EquiposAcelerografos.validarMarcadoUnEquipoZona(equipos, zonamarcada):
                        # limpiar inclinometros
                        EquiposAcelerografos.limpiarEquiposTipo(treeWidget)
                        parent_item.setCheckState(0, estado)
                        EquiposAcelerografos.marcardesmarcar_todos_hijos(parent_item, estado)
                        EquiposAcelerografos.actualizar_estado_padre_hijos(parent_item)
                    else:
                        if estado == Qt.CheckState.Checked:
                            mostrar_mensaje("MARCACIÓN MÚLTIPLE", "Solo debe marcar un Acelerógrafo.", "advertencia")
                            EquiposAcelerografos.actualizar_estado_padre_padre(parent_item)
            else:  # child (Hijos del parent)
                # limpiar inclinometros
                EquiposAcelerografos.limpiarEquiposTipo(treeWidget)
                parent_item.setCheckState(0, estado)
                EquiposAcelerografos.actualizar_estado_padre_hijos(parent_item)
            graficarEquiposMarcados()
    
    def validarMarcadoCheckboxaNTIGUO(parent_item, column, obtenerEquiposMarcados):
        codigo = parent_item.text(1)
        estado = parent_item.checkState(0)
        if estado != Qt.CheckState.PartiallyChecked:
            # comprobar si el código es numérico (primer nivel)
            if codigo.isdigit():
                if codigo == "0": # COMPONENTE
                    EquiposAcelerografos.marcardesmarcar_todos_hijos(parent_item, estado)
                    # Ocultar info
                else:
                    EquiposAcelerografos.marcardesmarcar_todos_hijos(parent_item, estado)
                    EquiposAcelerografos.actualizar_estado_padre_hijos(parent_item)     
            else:  # child (Hijos del parent)
                EquiposAcelerografos.marcardesmarcar_todos_hijos(parent_item, estado)
                EquiposAcelerografos.actualizar_estado_padre_hijos(parent_item)
            # mostrar gráfica
            obtenerEquiposMarcados()
          
    def validarOpcionesMenuCheckbox(point, treeWidget, reiniciarvistas):
        item = treeWidget.itemAt(point)
        if item:
            tipo = item.text(1)
            menu = QMenu()
            if tipo.isdigit():
                if tipo == "0": # Componente
                    nombrezona = item.text(0)
                    idzona = item.text(2)
                    idproyecto = item.text(3)
                    edit_componente = menu.addAction("Editar Componente")
                    delete_componente = menu.addAction("Eliminar Componente")
                    edit_componente.triggered.connect(lambda: CrearProyecto.dialogo_editar_componente(idzona, nombrezona, treeWidget, reiniciarvistas))
                    delete_componente.triggered.connect(lambda: CrearProyecto.eliminar_componente(idproyecto, idzona, nombrezona, treeWidget, reiniciarvistas))
                elif tipo == "1": # Acelerografos
                    idzona = item.text(2)
                    idproyecto = item.text(3)
                    nombrezona = item.parent().text(0)
                    edit_acelerografos = menu.addAction("Cambiar de Componente")
                    delete_acelerografos = menu.addAction("Eliminar Acelerógrafos")
                    edit_acelerografos.triggered.connect(lambda: SubirAcelerografos.cambiar_componente_acelerografos(idzona, idproyecto, treeWidget, "Acelerógrafos", "1", "acelerografo", reiniciarvistas))
                    delete_acelerografos.triggered.connect(lambda: SubirAcelerografos.eliminar_acelerografos(idproyecto, idzona, "Acelerógrafos", "1", treeWidget, reiniciarvistas))
            else:    
                if tipo == "acelerografo":
                    nombreacelero = item.text(0)
                    idinstrumento = item.text(2)
                    idacelerografo = item.text(3)
                    nombrezona = item.parent().parent().text(0)
                    idcomponente = item.parent().parent().text(2)
                    idproyecto = item.parent().parent().text(3)
                    edit_acelero = menu.addAction("Editar Acelerógrafo")
                    delete_acelero = menu.addAction("Eliminar Acelerógrafo")
                    edit_acelero.triggered.connect(lambda: SubirAcelerografos.actualizarAcelerografo(idproyecto, idcomponente, idinstrumento, treeWidget, "Acelerógrafos", "1", "acelerografo", reiniciarvistas))
                    delete_acelero.triggered.connect(lambda: SubirAcelerografos.eliminar_acelerografo(idproyecto, idinstrumento, idacelerografo, nombreacelero, "Acelerógrafos", "acelerografo", treeWidget, reiniciarvistas))
            menu.exec(treeWidget.mapToGlobal(point))
    
    def validarMarcadoUnEquipoZona(datos, zona):
        respuesta = True
        if datos:
            equipos = datos.get(zona)
            for tipo, equipos in equipos.items():
                if len(equipos) > 1:
                    respuesta = False
        return respuesta
    
    def validarPerteneceMismoEquipoZona(datos, zona):
        respuesta = False
        if datos:
            if len(datos) == 1:
                tipos = datos.get(zona)
                if len(tipos) == 1:
                    respuesta = True
        return respuesta
     
    def desmarcar_todos_hijos_arbol(arbol):
        def desmarcar_nodo(nodo):
            nodo.setCheckState(0, Qt.Unchecked)
            for i in range(nodo.childCount()):
                desmarcar_nodo(nodo.child(i))
        for i in range(arbol.topLevelItemCount()):
            nodo_raiz = arbol.topLevelItem(i)
            desmarcar_nodo(nodo_raiz)
                            
    # Función para marcar o desmarcar todos los hijos de un nodo
    def marcardesmarcar_todos_hijos(nodo, estado):
        for i in range(nodo.childCount()):
            hijo = nodo.child(i)
            hijo.setCheckState(0, estado)
            EquiposAcelerografos.marcardesmarcar_todos_hijos(hijo, estado)

    # Función para actualizar el estado del padre en función del estado de sus hijos
    def actualizar_estado_padre_hijos(nodo):
        if nodo.parent():
            estados_hijos = [nodo.parent().child(i).checkState(0) for i in range(nodo.parent().childCount())]
            # Verificamos los estados de los hijos y actualizamos el padre
            if all(estado == Qt.Checked for estado in estados_hijos):
                nodo.parent().setCheckState(0, Qt.Checked)
            elif all(estado == Qt.Unchecked for estado in estados_hijos):
                nodo.parent().setCheckState(0, Qt.Unchecked)
            else:
                nodo.parent().setCheckState(0, Qt.PartiallyChecked)
        if nodo.parent():
            if nodo.parent().parent():
                EquiposAcelerografos.actualizar_estado_padre_hijos(nodo.parent())

    def actualizar_estado_padre_padre(nodo):
        if nodo.childCount() > 0:
            estados_hijos = [nodo.child(i).checkState(0) for i in range(nodo.childCount())]
            # Verificamos los estados de los hijos y actualizamos el padre
            if all(estado == Qt.Checked for estado in estados_hijos):
                nodo.setCheckState(0, Qt.Checked)
            elif all(estado == Qt.Unchecked for estado in estados_hijos):
                nodo.setCheckState(0, Qt.Unchecked)
            else:
                nodo.setCheckState(0, Qt.PartiallyChecked)
    
    def obtener_zona_tipoequipo_elementos_marcados(datos, equipo):
        for zona, tipos in datos.items():
            for tipo_equipo, lista_equipos in tipos.items():
                # Si la lista de equipos es un diccionario
                if isinstance(lista_equipos, dict):
                    for sub_tipo, sub_lista in lista_equipos.items():
                        if equipo in sub_lista:
                            return zona
                # Si la lista de equipos es una lista simple
                elif isinstance(lista_equipos, list):
                    if equipo in lista_equipos:
                        return zona
        return None
                
    def obtener_todos_elementos_marcados(tree_widget):
        elementos_marcados = {}
        for i in range(tree_widget.topLevelItemCount()):
            grupo = tree_widget.topLevelItem(i)
            resultado_grupo = EquiposAcelerografos.obtener_elementos_marcados_recursivo(grupo)
            if resultado_grupo:
                elementos_marcados.update(resultado_grupo)
        return elementos_marcados
    
    def obtener_elementos_marcados_recursivo(nodo):
        hijos_marcados = []
        if nodo.childCount() > 0:
            marcados = {}
            for i in range(nodo.childCount()):
                hijo = nodo.child(i)
                resultado_hijo = EquiposAcelerografos.obtener_elementos_marcados_recursivo(hijo)
                if resultado_hijo:
                    if isinstance(resultado_hijo, dict):
                        marcados.update(resultado_hijo)
                    else:
                        hijos_marcados.append(resultado_hijo)
            if hijos_marcados:
                return {(nodo.text(0), nodo.text(2), nodo.text(3)): hijos_marcados}
            return {(nodo.text(0), nodo.text(2), nodo.text(3)): marcados} if marcados else None
        else:
            if nodo.checkState(0) == Qt.Checked:
                return (nodo.text(0), nodo.text(2), nodo.text(3))
        return None

    def obtener_elementos_des_marcados_recursivo(nodo):
        if nodo.parent():
            return EquiposAcelerografos.obtener_elementos_des_marcados_recursivo(nodo.parent())
        else:
            marcados = EquiposAcelerografos.obtener_elementos_marcados_recursivo(nodo)
        return marcados
     
    def obtener_todos_elementos_arbol(tree_widget):
        elementos = {}
        for i in range(tree_widget.topLevelItemCount()):
            grupo = tree_widget.topLevelItem(i)
            resultado_grupo = EquiposAcelerografos.obtener_elementos_arbol_recursivo(grupo)
            if resultado_grupo:
                elementos.update(resultado_grupo)
        return elementos
    
    def obtener_elementos_arbol_recursivo(nodo):
        hijos = []
        if nodo.childCount() > 0:
            marcados = {}
            for i in range(nodo.childCount()):
                hijo = nodo.child(i)
                resultado_hijo = EquiposAcelerografos.obtener_elementos_arbol_recursivo(hijo)
                if resultado_hijo:
                    if isinstance(resultado_hijo, dict):
                        marcados.update(resultado_hijo)
                    else:
                        hijos.append(resultado_hijo)
            if hijos:
                return {(nodo.text(0), nodo.text(2), nodo.text(3)): hijos}
            return {(nodo.text(0), nodo.text(2), nodo.text(3)): marcados} if marcados else None
        else:
            return (nodo.text(0), nodo.text(2), nodo.text(3))
    
    def limpiarEquiposTipo(tree_widget):
        for t in range(tree_widget.topLevelItemCount()):
            grupo = tree_widget.topLevelItem(t)
            grupo.setCheckState(0, Qt.Unchecked)
            for g in range(grupo.childCount()):
                equipo = grupo.child(g)
                equipo.setCheckState(0, Qt.Unchecked)
                EquiposAcelerografos.desmarcarHijos(equipo)
    
    def desmarcarHijos(item):
        for h in range(item.childCount()):
            hijo = item.child(h)
            hijo.setCheckState(0, Qt.Unchecked)
            EquiposAcelerografos.desmarcarHijos(hijo)
    
    def inicializar_lista_equipos(tree_widget, proyecto_id, proyecto_name):
        TreeCheckbox.limpiarArbolCheckboxes(tree_widget, proyecto_name)
        if proyecto_id:
            # LISTAR COMOPONENTES
            componentes = InterfazController.ctrlListarComponentesProyecto(proyecto_id)
            if componentes:
                for zona in componentes:
                    idzona = zona[0]
                    namezona = zona[2]
                    # LISTAR Acelerógrafos
                    acelerografos = InterfazController.ctrlListarAcelerografosVistaComponente(proyecto_id, idzona)
                    if len(acelerografos) > 0:
                        TreeCheckbox.crearNuevoGrupoCheckboxesSimple(tree_widget, namezona, idzona, proyecto_id, "Acelerógrafos", "1", acelerografos, "acelerografo")

    @staticmethod
    def filtrarArbolPorTexto(treeWidget, texto):
        """Oculta/muestra items del árbol según coincidencia de texto (recursivo)."""
        texto = texto.strip().lower()

        def procesar_nodo(nodo):
            coincide_aqui = texto in nodo.text(0).lower()
            coincide_hijo = False
            for i in range(nodo.childCount()):
                if procesar_nodo(nodo.child(i)):
                    coincide_hijo = True
            visible = texto == "" or coincide_aqui or coincide_hijo
            nodo.setHidden(not visible)
            if texto != "" and coincide_hijo:
                nodo.setExpanded(True)
            elif texto == "":
                nodo.setExpanded(False)
            return visible

        treeWidget.blockSignals(True)
        try:
            for i in range(treeWidget.topLevelItemCount()):
                procesar_nodo(treeWidget.topLevelItem(i))
        finally:
            treeWidget.blockSignals(False)
    