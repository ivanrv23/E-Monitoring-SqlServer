from PySide6.QtWidgets import QMenu
from PySide6.QtCore import Qt
from utils.shared.arbolmarcado import TreeCheckbox
from modules.proyecto.crearProyecto import CrearProyecto
from modules.datos.subirPrismas import SubirPrismas
from modules.datos.subirPluviometros import SubirPluviometros
from utils.shared.personalizacion import Personalizacion
from controllers.InterfazController import InterfazController

class EquiposAnalisis:

    def validarMarcadoCheckbox(parent_item, column, obtenerEquiposMarcados):
        codigo = parent_item.text(1)
        estado = parent_item.checkState(0)
        if estado != Qt.CheckState.PartiallyChecked:
            # comprobar si el código es numérico (primer nivel)
            if codigo.isdigit():
                if codigo == "0": # COMPONENTE
                    EquiposAnalisis.marcardesmarcar_todos_hijos(parent_item, estado)
                    # Ocultar info
                else:
                    EquiposAnalisis.marcardesmarcar_todos_hijos(parent_item, estado)
                    EquiposAnalisis.actualizar_estado_padre_hijos(parent_item)     
            else:  # child (Hijos del parent)
                EquiposAnalisis.marcardesmarcar_todos_hijos(parent_item, estado)
                EquiposAnalisis.actualizar_estado_padre_hijos(parent_item)
            # graficar
            obtenerEquiposMarcados()
          
    def validarOpcionesMenuCheckbox(point, main, treeWidget, reiniciarvistas):
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
                elif tipo == "1": # Prismas
                    idzona = item.text(2)
                    idproyecto = item.text(3)
                    nombrezona = item.parent().text(0)
                    edit_prismasalta = menu.addAction("Dar de Baja")
                    change_prismasalta = menu.addAction("Cambiar de Componente")
                    delete_prismasalta = menu.addAction("Eliminar Prismas")
                    edit_prismasalta.triggered.connect(lambda: SubirPrismas.dardebaja_prismas(idzona, idproyecto, nombrezona, treeWidget, "Prismas", "2", reiniciarvistas))
                    change_prismasalta.triggered.connect(lambda: SubirPrismas.cambiar_componente_prismas(idzona, idproyecto, treeWidget, "Prismas", "2", "prisma", reiniciarvistas))
                    delete_prismasalta.triggered.connect(lambda: SubirPrismas.eliminar_prismas(idzona, "Prismas", "2", treeWidget, reiniciarvistas))
                elif tipo == "2": # Pluviometros
                    idzona = item.text(2)
                    idproyecto = item.text(3)
                    nombrezona = item.parent().text(0)
                    edit_pluviometros = menu.addAction("Cambiar de Componente")
                    delete_pluviometros = menu.addAction("Eliminar Pluviómetros")
                    edit_pluviometros.triggered.connect(lambda: SubirPluviometros.cambiar_componente_pluviometros(idzona, idproyecto, treeWidget, "Pluviómetros", "6", "pluviometro", reiniciarvistas))
                    delete_pluviometros.triggered.connect(lambda: SubirPluviometros.eliminar_pluviometros(idproyecto, idzona, "Pluviómetros", "6", treeWidget, reiniciarvistas))
            else:    
                if tipo == "prisma":
                    nombreprisma = item.text(0)
                    idinstrumento = item.text(2)
                    nombrezona = item.parent().parent().text(0)
                    idcomponente = item.parent().parent().text(2)
                    idproyecto = item.parent().parent().text(3)
                    custom_prisma = menu.addAction("Personalizar Prisma")
                    edit_prisma = menu.addAction("Dar de Baja")
                    change_prisma = menu.addAction("Cambiar de Componente")
                    delete_prisma = menu.addAction("Eliminar Prisma")
                    custom_prisma.triggered.connect(lambda: Personalizacion.personalizarEquipoGrafica(idproyecto, idinstrumento, nombreprisma, "PRISMA"))
                    edit_prisma.triggered.connect(lambda: SubirPrismas.dardebaja_prisma(main, idproyecto, idcomponente, nombreprisma, idinstrumento, nombrezona, treeWidget, reiniciarvistas))
                    change_prisma.triggered.connect(lambda: SubirPrismas.cambiar_componente_prisma(idinstrumento, idcomponente, idproyecto, treeWidget, "Prismas", "1", "prisma", 1, reiniciarvistas))
                    delete_prisma.triggered.connect(lambda: SubirPrismas.eliminar_prisma(idinstrumento, nombreprisma, "Prismas", "prisma", treeWidget, reiniciarvistas))
                elif tipo == "pluviometro":
                    nombrepluvio = item.text(0)
                    idinstrumento = item.text(2)
                    nombrezona = item.parent().parent().text(0)
                    idcomponente = item.parent().parent().text(2)
                    idproyecto = item.parent().parent().text(3)
                    edit_pluviometro = menu.addAction("Editar Pluviómetro")
                    delete_pluviometro = menu.addAction("Eliminar Pluviómetro")
                    edit_pluviometro.triggered.connect(lambda: SubirPluviometros.actualizarPluviometro(idproyecto, idcomponente, idinstrumento, treeWidget, "Pluviómetros", "6", "pluviometro", reiniciarvistas))
                    delete_pluviometro.triggered.connect(lambda: SubirPluviometros.eliminar_pluviometro(idproyecto, idinstrumento, nombrepluvio, "Pluviómetros", "pluviometro", treeWidget, reiniciarvistas))
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
    def marcardesmarcar_todos_hijos(nodo, estado):
        for i in range(nodo.childCount()):
            hijo = nodo.child(i)
            hijo.setCheckState(0, estado)
            EquiposAnalisis.marcardesmarcar_todos_hijos(hijo, estado)

    @staticmethod
    def marcar_desmarcar_proyecto_completo(treeWidget, estado, callback_graficar):
        treeWidget.blockSignals(True)
        try:
            for i in range(treeWidget.topLevelItemCount()):
                componente = treeWidget.topLevelItem(i)
                componente.setCheckState(0, estado)
                EquiposAnalisis.marcardesmarcar_todos_hijos(componente, estado)
        finally:
            treeWidget.blockSignals(False)
        callback_graficar()

    @staticmethod
    def recalcular_jerarquia_visual(item):
        for i in range(item.childCount()):
            EquiposAnalisis.recalcular_jerarquia_visual(item.child(i))

        if item.childCount() > 0:
            estados_hijos = [item.child(k).checkState(0) for k in range(item.childCount())]
            if all(s == Qt.Checked for s in estados_hijos):
                nuevo_st = Qt.Checked
            elif all(s == Qt.Unchecked for s in estados_hijos):
                nuevo_st = Qt.Unchecked
            else:
                nuevo_st = Qt.PartiallyChecked
            item.setCheckState(0, nuevo_st)

    @staticmethod
    def aplicar_marcado_predeterminado(treeWidget, preferencias, callback_graficar):
        if preferencias is None:
            return

        # Diccionario para búsqueda rápida: {idcomponente: [idinstrumento, ...]}
        dict_pref = {}
        for id_c, id_i in preferencias:
            id_c_int = int(id_c)
            if id_c_int not in dict_pref:
                dict_pref[id_c_int] = []
            dict_pref[id_c_int].append(id_i if id_i is None else int(id_i))

        treeWidget.blockSignals(True)
        try:
            # 1. Desmarcar todo el árbol para empezar de cero
            for i in range(treeWidget.topLevelItemCount()):
                item_root = treeWidget.topLevelItem(i)
                item_root.setCheckState(0, Qt.Unchecked)
                EquiposAnalisis.marcardesmarcar_todos_hijos(item_root, Qt.Unchecked)

            # 2. Marcar según lo guardado en base de datos
            for i in range(treeWidget.topLevelItemCount()):
                item_zona = treeWidget.topLevelItem(i)
                id_zona_actual = int(item_zona.text(2))

                if id_zona_actual in dict_pref:
                    opciones = dict_pref[id_zona_actual]

                    if None in opciones:
                        # Caso: se marcó toda la zona/componente
                        item_zona.setCheckState(0, Qt.Checked)
                        EquiposAnalisis.marcardesmarcar_todos_hijos(item_zona, Qt.Checked)
                    else:
                        # Caso: marcado selectivo de equipos internos (prismas)
                        def marcar_recursivo(padre):
                            for j in range(padre.childCount()):
                                hijo = padre.child(j)
                                if not hijo.text(1).isdigit():
                                    id_inst_hijo = int(hijo.text(2))
                                    if id_inst_hijo in opciones:
                                        hijo.setCheckState(0, Qt.Checked)
                                marcar_recursivo(hijo)

                        marcar_recursivo(item_zona)

            # 3. Recalcular visualmente los estados intermedios (PartiallyChecked)
            for i in range(treeWidget.topLevelItemCount()):
                EquiposAnalisis.recalcular_jerarquia_visual(treeWidget.topLevelItem(i))
        finally:
            treeWidget.blockSignals(False)
            callback_graficar()

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
                EquiposAnalisis.actualizar_estado_padre_hijos(nodo.parent())

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
            resultado_grupo = EquiposAnalisis.obtener_elementos_marcados_recursivo(grupo)
            if resultado_grupo:
                elementos_marcados.update(resultado_grupo)
        return elementos_marcados
    
    def obtener_elementos_marcados_recursivo(nodo):
        hijos_marcados = []
        if nodo.childCount() > 0:
            marcados = {}
            for i in range(nodo.childCount()):
                hijo = nodo.child(i)
                resultado_hijo = EquiposAnalisis.obtener_elementos_marcados_recursivo(hijo)
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
            return EquiposAnalisis.obtener_elementos_des_marcados_recursivo(nodo.parent())
        else:
            marcados = EquiposAnalisis.obtener_elementos_marcados_recursivo(nodo)
        return marcados
     
    def obtener_todos_elementos_arbol(tree_widget):
        elementos = {}
        for i in range(tree_widget.topLevelItemCount()):
            grupo = tree_widget.topLevelItem(i)
            resultado_grupo = EquiposAnalisis.obtener_elementos_arbol_recursivo(grupo)
            if resultado_grupo:
                elementos.update(resultado_grupo)
        return elementos
    
    def obtener_elementos_arbol_recursivo(nodo):
        hijos = []
        if nodo.childCount() > 0:
            marcados = {}
            for i in range(nodo.childCount()):
                hijo = nodo.child(i)
                resultado_hijo = EquiposAnalisis.obtener_elementos_arbol_recursivo(hijo)
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
    
    def inicializar_lista_equipos(tree_widget, tree_vacio, proyecto_id, proyecto_name):
        TreeCheckbox.limpiarArbolCheckboxes(tree_widget, proyecto_name)
        TreeCheckbox.limpiarArbolCheckboxes(tree_vacio, proyecto_name)
        if proyecto_id:
            # LISTAR COMOPONENTES
            componentes = InterfazController.ctrlListarComponentesProyecto(proyecto_id)
            if componentes:
                for zona in componentes:
                    idzona = zona[0]
                    namezona = zona[2]
                    # LISTAR PRISMAS
                    prismas = InterfazController.ctrlListarPrismasComponente(idzona, 1)
                    if prismas:
                        TreeCheckbox.crearNuevoGrupoCheckboxesSimple(tree_widget, namezona, idzona, proyecto_id, "Prismas", "1", prismas, "prisma")

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
    