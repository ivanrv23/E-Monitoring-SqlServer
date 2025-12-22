from PySide6.QtWidgets import QMenu
from PySide6.QtCore import Qt
from utils.shared.arbolmarcado import TreeCheckbox
from modules.proyecto.crearProyecto import CrearProyecto
from modules.datos.subirCeldas import SubirCeldas
from controllers.InterfazController import InterfazController
from utils.shared.personalizacion import Personalizacion

class EquiposCeldas:

    def validarMarcadoCheckbox(parent_item, column, obtenerEquiposMarcados):
        codigo = parent_item.text(1)
        estado = parent_item.checkState(0)
        if estado != Qt.CheckState.PartiallyChecked:
            # comprobar si el código es numérico (primer nivel)
            if codigo.isdigit():
                if codigo == "0": # COMPONENTE
                    EquiposCeldas.marcardesmarcar_todos_hijos(parent_item, estado, 2)
                else:
                    EquiposCeldas.marcardesmarcar_todos_hijos(parent_item, estado, 1)
                    EquiposCeldas.actualizar_estado_padre_hijos(parent_item)
            else:  # child (Hijos del parent)
                if codigo == "cotacelda":
                    if estado == Qt.Checked:
                        parent_item.setCheckState(0, Qt.Checked)
                        # marcar padre
                        parent_item.parent().setCheckState(0, Qt.Checked)
                    elif estado == Qt.Unchecked:
                        parent_item.setCheckState(0, Qt.Unchecked)
                    EquiposCeldas.actualizar_estado_padre_hijos(parent_item.parent())
                else:
                    EquiposCeldas.marcardesmarcar_todos_hijos(parent_item, estado)
                    EquiposCeldas.actualizar_estado_padre_hijos(parent_item)
            # mostrar gráfica
            obtenerEquiposMarcados()
    
    def validarOpcionesMenuCheckbox(point, treeWidget, vista, reiniciarvistas):
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
                elif tipo == "1": # Celdas Asentamiento
                    idzona = item.text(2)
                    idproyecto = item.text(3)
                    nombrezona = item.parent().text(0)
                    edit_celdas = menu.addAction("Cambiar de Componente")
                    delete_celdas = menu.addAction("Eliminar Celdas")
                    edit_celdas.triggered.connect(lambda: SubirCeldas.cambiar_componente_celdas(idzona, idproyecto, treeWidget, "Celdas de Asentamiento", "1", "celda", reiniciarvistas, vista))
                    delete_celdas.triggered.connect(lambda: SubirCeldas.eliminar_celdas(idproyecto, idzona, "Celdas de Asentamiento", "1", treeWidget, reiniciarvistas))
            else:    
                if tipo == "celda":
                    nombrecelda = item.text(0)
                    idinstrumento = item.text(2)
                    nombrezona = item.parent().parent().text(0)
                    idcomponente = item.parent().parent().text(2)
                    idproyecto = item.parent().parent().text(3)
                    custom_celda = menu.addAction("Personalizar Celda")
                    edit_celda = menu.addAction("Editar Celda")
                    delete_celda = menu.addAction("Eliminar Celda")
                    custom_celda.triggered.connect(lambda: Personalizacion.personalizarEquipoGrafica(idproyecto, idinstrumento, nombrecelda, "CELDA DE ASENTAMIENTO"))
                    edit_celda.triggered.connect(lambda: SubirCeldas.actualizarCeldaAsentamiento(idproyecto, idcomponente, idinstrumento, treeWidget, "Celdas de Asentamiento", "1", "celda", reiniciarvistas, vista))
                    delete_celda.triggered.connect(lambda: SubirCeldas.eliminar_celda(idproyecto, idinstrumento, nombrecelda, "Celdas de Asentamiento", "celda", treeWidget, reiniciarvistas))
                elif tipo == "cotacelda":
                    nombrecota = item.text(0)
                    if nombrecota == "Cota de Fundación":
                        tipoinstru = 1
                    else:
                        tipoinstru = 2
                    idinstrumento = item.parent().text(2)
                    nombrecelda = item.parent().text(0)
                    nombrezona = item.parent().parent().parent().text(0)
                    idcomponente = item.parent().parent().parent().text(2)
                    idproyecto = item.parent().parent().parent().text(3)
                    custom_cota = menu.addAction("Personalizar Cota")
                    custom_cota.triggered.connect(lambda: Personalizacion.personalizarEquipoGrafica(idproyecto, idinstrumento, nombrecota, f"COTA DE CELDA {nombrecelda}", tipoinstru))
            menu.exec(treeWidget.mapToGlobal(point))
    
    def validarMarcadoUnEquipoZona(datos, zona):
        respuesta = True
        if datos:
            equipos = datos.get(zona)
            if len(equipos) > 1:
                respuesta = False
            else:
                respuesta = True
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
    def marcardesmarcar_todos_hijos(nodo, estado, nivel=0):
        nodo.setCheckState(0, estado)
        # Si estamos desmarcando, ignorar nivel y recorrer todo
        if estado == Qt.Unchecked:
            for i in range(nodo.childCount()):
                hijo = nodo.child(i)
                EquiposCeldas.marcardesmarcar_todos_hijos(hijo, estado, nivel)
        else:
            # Si estamos marcando, controlar la profundidad
            if nivel <= 0:
                return
            for i in range(nodo.childCount()):
                hijo = nodo.child(i)
                EquiposCeldas.marcardesmarcar_todos_hijos(hijo, estado, nivel - 1)
    
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
                EquiposCeldas.actualizar_estado_padre_hijos(nodo.parent())

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
            resultado_grupo = EquiposCeldas.obtener_elementos_marcados_recursivo(grupo)
            if resultado_grupo:
                elementos_marcados.update(resultado_grupo)
        return elementos_marcados
    
    def obtener_elementos_marcados_recursivo(nodo):
        hijos_marcados = []
        if nodo.childCount() > 0:
            marcados = {}
            for i in range(nodo.childCount()):
                hijo = nodo.child(i)
                resultado_hijo = EquiposCeldas.obtener_elementos_marcados_recursivo(hijo)
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
            elif nodo.parent().checkState(0) == Qt.Checked:
                return ("", "", "")
        return None

    def obtener_elementos_des_marcados_recursivo(nodo):
        if nodo.parent():
            return EquiposCeldas.obtener_elementos_des_marcados_recursivo(nodo.parent())
        else:
            marcados = EquiposCeldas.obtener_elementos_marcados_recursivo(nodo)
        return marcados
     
    def obtener_todos_elementos_arbol(tree_widget):
        elementos = {}
        for i in range(tree_widget.topLevelItemCount()):
            grupo = tree_widget.topLevelItem(i)
            resultado_grupo = EquiposCeldas.obtener_elementos_arbol_recursivo(grupo)
            if resultado_grupo:
                elementos.update(resultado_grupo)
        return elementos
    
    def obtener_elementos_arbol_recursivo(nodo):
        hijos = []
        if nodo.childCount() > 0:
            marcados = {}
            for i in range(nodo.childCount()):
                hijo = nodo.child(i)
                resultado_hijo = EquiposCeldas.obtener_elementos_arbol_recursivo(hijo)
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
    
    def inicializar_lista_equipos(tree_widget, proyecto_id, proyecto_name):
        TreeCheckbox.limpiarArbolCheckboxes(tree_widget, proyecto_name)
        if proyecto_id:
            # LISTAR COMOPONENTES
            componentes = InterfazController.ctrlListarComponentesProyecto(proyecto_id)
            if componentes:
                for zona in componentes:
                    idzona = zona[0]
                    namezona = zona[2]
                    # LISTAR CELDAS
                    celdas = InterfazController.ctrlListarCeldasComponente(proyecto_id, idzona)
                    if celdas:
                        TreeCheckbox.crearNuevoGrupoCheckboxesDoble(tree_widget, namezona, idzona, proyecto_id, "Celdas de Asentamiento", "1", celdas, "celda")
    