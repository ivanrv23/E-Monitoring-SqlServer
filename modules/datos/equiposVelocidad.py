from PySide6.QtWidgets import QMenu
from PySide6.QtCore import Qt
from utils.shared.arbolmarcado import TreeCheckbox
from modules.proyecto.crearProyecto import CrearProyecto
from modules.datos.subirPrismas import SubirPrismas
from modules.datos.subirPluviometros import SubirPluviometros
from utils.shared.personalizacion import Personalizacion
from controllers.InterfazController import InterfazController

class EquiposVelocidad:

    def validarMarcadoCheckbox(parent_item, column, obtenerEquiposMarcados):
        codigo = parent_item.text(1)
        estado = parent_item.checkState(0)
        if estado != Qt.CheckState.PartiallyChecked:
            # comprobar si el código es numérico (primer nivel)
            if codigo.isdigit():
                if codigo == "0": # COMPONENTE
                    EquiposVelocidad.marcardesmarcar_todos_hijos(parent_item, estado)
                    # Ocultar info
                else:
                    EquiposVelocidad.marcardesmarcar_todos_hijos(parent_item, estado)
                    EquiposVelocidad.actualizar_estado_padre_hijos(parent_item)     
            else:  # child (Hijos del parent)
                EquiposVelocidad.marcardesmarcar_todos_hijos(parent_item, estado)
                EquiposVelocidad.actualizar_estado_padre_hijos(parent_item)
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
                    custom_pluvio = menu.addAction("Personalizar Pluviómetro")
                    edit_pluviometro = menu.addAction("Editar Pluviómetro")
                    delete_pluviometro = menu.addAction("Eliminar Pluviómetro")
                    custom_pluvio.triggered.connect(lambda: Personalizacion.personalizarPluviometroGrafica(idproyecto, idinstrumento, nombrepluvio, "PLUVIÓMETRO", 0))
                    edit_pluviometro.triggered.connect(lambda: SubirPluviometros.actualizarPluviometro(idproyecto, idcomponente, idinstrumento, treeWidget, "Pluviómetros", "2", "pluviometro", reiniciarvistas))
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
            EquiposVelocidad.marcardesmarcar_todos_hijos(hijo, estado)

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
                EquiposVelocidad.actualizar_estado_padre_hijos(nodo.parent())

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
            resultado_grupo = EquiposVelocidad.obtener_elementos_marcados_recursivo(grupo)
            if resultado_grupo:
                elementos_marcados.update(resultado_grupo)
        return elementos_marcados
    
    def obtener_elementos_marcados_recursivo(nodo):
        hijos_marcados = []
        if nodo.childCount() > 0:
            marcados = {}
            for i in range(nodo.childCount()):
                hijo = nodo.child(i)
                resultado_hijo = EquiposVelocidad.obtener_elementos_marcados_recursivo(hijo)
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
            return EquiposVelocidad.obtener_elementos_des_marcados_recursivo(nodo.parent())
        else:
            marcados = EquiposVelocidad.obtener_elementos_marcados_recursivo(nodo)
        return marcados
     
    def obtener_todos_elementos_arbol(tree_widget):
        elementos = {}
        for i in range(tree_widget.topLevelItemCount()):
            grupo = tree_widget.topLevelItem(i)
            resultado_grupo = EquiposVelocidad.obtener_elementos_arbol_recursivo(grupo)
            if resultado_grupo:
                elementos.update(resultado_grupo)
        return elementos
    
    def obtener_elementos_arbol_recursivo(nodo):
        hijos = []
        if nodo.childCount() > 0:
            marcados = {}
            for i in range(nodo.childCount()):
                hijo = nodo.child(i)
                resultado_hijo = EquiposVelocidad.obtener_elementos_arbol_recursivo(hijo)
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
            # LISTAR COMPONENTES
            componentes = InterfazController.ctrlListarComponentesProyecto(proyecto_id)
            if componentes:
                for zona in componentes:
                    idzona = zona[0]
                    namezona = zona[2]
                    # LISTAR PRISMAS
                    prismas = InterfazController.ctrlListarPrismasComponente(idzona, 1)
                    if prismas:
                        TreeCheckbox.crearNuevoGrupoCheckboxesSimple(tree_widget, namezona, idzona, proyecto_id, "Prismas", "1", prismas, "prisma")
                    # Listar pluviometros
                    pluviometros = InterfazController.ctrlListarPluviometrosComponente(proyecto_id, idzona)
                    if pluviometros:
                        TreeCheckbox.crearNuevoGrupoCheckboxesSimple(tree_widget, namezona, idzona, proyecto_id, "Pluviómetros", "2", pluviometros, "pluviometro")
        