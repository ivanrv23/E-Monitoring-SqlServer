from PySide6.QtWidgets import QMenu
from PySide6.QtCore import Qt
from utils.shared.arbolmarcado import TreeCheckbox
from utils.common.alertas import mostrar_mensaje
from modules.proyecto.crearProyecto import CrearProyecto
from modules.datos.subirPiezometros import SubirPiezometros
from modules.datos.subirPluviometros import SubirPluviometros
from modules.datos.subirCotasTerreno import SubirCotasTerreno
from utils.shared.personalizacion import Personalizacion
from controllers.InterfazController import InterfazController

class EquiposPiezometros:
    
    def validarMarcadoCheckboxPiezo(parent_item, column, treeWidget, obtenerEquiposMarcados):
        nombre = parent_item.text(column)
        codigo = parent_item.text(1)
        idgrupo = parent_item.text(2)
        tipogrupo = parent_item.text(3)
        estado = parent_item.checkState(0)
        nombremarcado = (nombre, idgrupo, tipogrupo)
        if estado != Qt.CheckState.PartiallyChecked:
            # comprobar si el código es numérico (primer nivel)
            if codigo.isdigit():
                if codigo == "0": # COMPONENTE
                    if estado == Qt.Checked:
                        equipos = EquiposPiezometros.obtener_todos_elementos_arbol(treeWidget)
                        respu, tipo = EquiposPiezometros.validarMarcadoUnEquipoZona(equipos, nombremarcado)
                        if respu:
                            if tipo != 0:
                                EquiposPiezometros.limpiarEquiposTipo(treeWidget, tipo)
                            EquiposPiezometros.marcardesmarcar_todos_hijos(parent_item, estado, 2)
                        else:
                            mostrar_mensaje("MARCACIÓN MÚLTIPLE", "Solo debe marcar un tipo de Piezómetro.", "advertencia")
                            EquiposPiezometros.actualizar_estado_padre_padre(parent_item)
                    elif estado == Qt.Unchecked:
                        EquiposPiezometros.marcardesmarcar_todos_hijos(parent_item, estado)
                elif codigo == "1": # PIEZÓMETROS CUERDA VIBRANTE
                    num_hijospiezo = parent_item.childCount()
                    if estado == Qt.Checked:
                        # limpiar piezómetros
                        EquiposPiezometros.limpiarEquiposTipo(treeWidget, 1)
                        # marcar cuerda
                        parent_item.setCheckState(0, Qt.Checked)
                        for i in range(num_hijospiezo):
                            hijo = parent_item.child(i)
                            if parent_item == hijo.parent():
                                hijo.setCheckState(0, Qt.Checked)
                    elif estado == Qt.Unchecked:
                        parent_item.setCheckState(0, Qt.Unchecked)
                        for i in range(num_hijospiezo):
                            hijo = parent_item.child(i)
                            if parent_item == hijo.parent():
                                hijo.setCheckState(0, Qt.Unchecked)
                                num_nietospiezo = hijo.childCount()
                                for i in range(num_nietospiezo):
                                    nieto = hijo.child(i)
                                    if hijo is nieto.parent():
                                        nieto.setCheckState(0, Qt.Unchecked)
                    # validar padre
                    EquiposPiezometros.actualizar_estado_padre_hijos(parent_item)
                elif codigo == "2": # PIEZÓMETROS CASAGRANDE
                    num_hijospiezo = parent_item.childCount()
                    if estado == Qt.Checked:
                        # limpiar piezómetros
                        EquiposPiezometros.limpiarEquiposTipo(treeWidget, 2)
                        # marcar manual
                        parent_item.setCheckState(0, Qt.Checked)
                        for i in range(num_hijospiezo):
                            hijo = parent_item.child(i)
                            if parent_item == hijo.parent():
                                hijo.setCheckState(0, Qt.Checked)
                    elif estado == Qt.Unchecked:
                        parent_item.setCheckState(0, Qt.Unchecked)
                        for i in range(num_hijospiezo):
                            hijo = parent_item.child(i)
                            if parent_item == hijo.parent():
                                hijo.setCheckState(0, Qt.Unchecked)
                                num_nietospiezo = hijo.childCount()
                                for i in range(num_nietospiezo):
                                    nieto = hijo.child(i)
                                    if hijo is nieto.parent():
                                        nieto.setCheckState(0, Qt.Unchecked)
                    # validar padre
                    EquiposPiezometros.actualizar_estado_padre_hijos(parent_item)
                elif codigo == "3": # PLUVIÓMETROS
                    num_hijosplu = parent_item.childCount()
                    if estado == Qt.Checked:
                        if num_hijosplu == 1:
                            for i in range(num_hijosplu):
                                hijo = parent_item.child(i)
                                if parent_item == hijo.parent():
                                    hijo.setCheckState(0, Qt.Checked)
                        else:
                            mostrar_mensaje("MARCACIÓN MÚLTIPLE", "Solo debe marcar un Pluviómetro.", "advertencia")
                    elif estado == Qt.Unchecked:
                        for i in range(num_hijosplu):
                            hijo = parent_item.child(i)
                            if parent_item == hijo.parent():
                                hijo.setCheckState(0, Qt.Unchecked)
                    # validar padre
                    EquiposPiezometros.actualizar_estado_padre_hijos(parent_item)
                elif codigo == "4": # COTAS DE TERRENO
                    num_suelohijos = parent_item.childCount()
                    if estado == Qt.Checked:
                        for i in range(num_suelohijos):
                            hijo = parent_item.child(i)
                            if parent_item == hijo.parent():
                                hijo.setCheckState(0, Qt.Checked)
                    elif estado == Qt.Unchecked:
                        for i in range(num_suelohijos):
                            hijo = parent_item.child(i)
                            if parent_item == hijo.parent():
                                hijo.setCheckState(0, Qt.Unchecked)
                    # validar padre
                    EquiposPiezometros.actualizar_estado_padre_hijos(parent_item)
            else:  # child (Hijos del parent)
                if codigo == "piezometrocuerda":
                    num_nietospiezo = parent_item.childCount()
                    if estado == Qt.Checked:
                        # limpiar casagrande
                        EquiposPiezometros.limpiarEquiposTipo(treeWidget, 1)
                    elif estado == Qt.Unchecked:
                        # desmarcar nietos
                        for i in range(num_nietospiezo):
                            nieto = parent_item.child(i)
                            if parent_item == nieto.parent():
                                nieto.setCheckState(0, Qt.Unchecked)
                    # validar padre
                    EquiposPiezometros.actualizar_estado_padre_hijos(parent_item)
                elif codigo == "piezometromanual":
                    num_nietospiezo = parent_item.childCount()
                    if estado == Qt.Checked:
                        # limpiar cuerda
                        EquiposPiezometros.limpiarEquiposTipo(treeWidget, 2)
                    elif estado == Qt.Unchecked:
                        for i in range(num_nietospiezo):
                            nieto = parent_item.child(i)
                            if parent_item == nieto.parent():
                                nieto.setCheckState(0, Qt.Unchecked)
                    # validar padre
                    EquiposPiezometros.actualizar_estado_padre_hijos(parent_item)
                elif codigo == "cotacuerda":
                    if estado == Qt.Checked:
                        # limpiar casagrande
                        EquiposPiezometros.limpiarEquiposTipo(treeWidget, 1)
                        parent_item.setCheckState(0, Qt.Checked)
                        # marcar padre
                        parent_item.parent().setCheckState(0, Qt.Checked)
                    elif estado == Qt.Unchecked:
                        parent_item.setCheckState(0, Qt.Unchecked)
                    # validar padre
                    EquiposPiezometros.actualizar_estado_padre_hijos(parent_item.parent())
                elif codigo == "cotamanual":
                    if estado == Qt.Checked:
                        # limpiar cuerda
                        EquiposPiezometros.limpiarEquiposTipo(treeWidget, 2)
                        parent_item.setCheckState(0, Qt.Checked)
                        # marcar padre
                        parent_item.parent().setCheckState(0, Qt.Checked)
                    elif estado == Qt.Unchecked:
                        parent_item.setCheckState(0, Qt.Unchecked)
                    # validar padre
                    EquiposPiezometros.actualizar_estado_padre_hijos(parent_item.parent())
                elif codigo == "pluviometro":
                    if estado == Qt.Checked:
                        # limpiar pluviómetros
                        num_nietospluvio = parent_item.parent().childCount()
                        for i in range(num_nietospluvio):
                            nieto = parent_item.parent().child(i)
                            if parent_item == nieto.parent():
                                nieto.setCheckState(0, Qt.Unchecked)
                        # Marcamo es actual
                        parent_item.setCheckState(0, Qt.Checked)
                    elif estado == Qt.Unchecked:
                        parent_item.setCheckState(0, Qt.Unchecked)
                    # validar padre
                    EquiposPiezometros.actualizar_estado_padre_hijos(parent_item)
                elif codigo == "terreno":
                    if estado == Qt.Checked:
                        parent_item.setCheckState(0, Qt.Checked)
                    elif estado == Qt.Unchecked:
                        parent_item.setCheckState(0, Qt.Unchecked)
                    # validar padre
                    EquiposPiezometros.actualizar_estado_padre_hijos(parent_item)
            # mostrar en la grafica
            obtenerEquiposMarcados()
    
    def validarOpcionesMenuCheckbox(point, treeWidget, vista, reiniciarVistas):
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
                    edit_componente.triggered.connect(lambda: CrearProyecto.dialogo_editar_componente(idzona, nombrezona, treeWidget, reiniciarVistas))
                    delete_componente.triggered.connect(lambda: CrearProyecto.eliminar_componente(idproyecto, idzona, nombrezona, treeWidget, reiniciarVistas))
                elif tipo == "1": # Piezometros Cuerda Vibrante
                    idzona = item.text(2)
                    idproyecto = item.text(3)
                    nombrezona = item.parent().text(0)
                    edit_piezocuerdas = menu.addAction("Cambiar de Componente")
                    delete_piezocuerdas = menu.addAction("Eliminar P. Cuerda Vibrante")
                    edit_piezocuerdas.triggered.connect(lambda: SubirPiezometros.cambiar_componente_piezocuerdas(idzona, idproyecto, treeWidget, "Piezómetros Cuerda Vibrante", "1", "piezometrocuerda", reiniciarVistas, vista))
                    delete_piezocuerdas.triggered.connect(lambda: SubirPiezometros.eliminar_piezocuerdas(idproyecto, idzona, "Piezómetros Cuerda Vibrante", "1", treeWidget, reiniciarVistas))
                elif tipo == "2": # Piezometros Manuales - Casagrande
                    idzona = item.text(2)
                    idproyecto = item.text(3)
                    nombrezona = item.parent().text(0)
                    edit_piezomanuales = menu.addAction("Cambiar de Componente")
                    delete_piezomanuales = menu.addAction("Eliminar P. Casagrande")
                    edit_piezomanuales.triggered.connect(lambda: SubirPiezometros.cambiar_componente_piezomanuales(idzona, idproyecto, treeWidget, "Piezómetros Casagrande", "2", "piezometromanual", reiniciarVistas, vista))
                    delete_piezomanuales.triggered.connect(lambda: SubirPiezometros.eliminar_piezomanuales(idproyecto, idzona, "Piezómetros Casagrande", "2", treeWidget, reiniciarVistas))
                elif tipo == "3": # Pluviometros
                    idzona = item.text(2)
                    idproyecto = item.text(3)
                    nombrezona = item.parent().text(0)
                    edit_pluviometros = menu.addAction("Cambiar de Componente")
                    delete_pluviometros = menu.addAction("Eliminar Pluviómetros")
                    edit_pluviometros.triggered.connect(lambda: SubirPluviometros.cambiar_componente_pluviometros(idzona, idproyecto, treeWidget, "Pluviómetros", "3", "pluviometro", reiniciarVistas))
                    delete_pluviometros.triggered.connect(lambda: SubirPluviometros.eliminar_pluviometros(idproyecto, idzona, "Pluviómetros", "3", treeWidget, reiniciarVistas))
                elif tipo == "4": # Cotas Terreno
                    idzona = item.text(2)
                    idproyecto = item.text(3)
                    nombrezona = item.parent().text(0)
                    edit_terrenos = menu.addAction("Cambiar de Componente")
                    delete_terrenos = menu.addAction("Eliminar Cotas de Terreno")
                    edit_terrenos.triggered.connect(lambda: SubirCotasTerreno.cambiar_componente_terrenos(idzona, idproyecto, treeWidget, "Cotas de Terreno", "4", "terreno", reiniciarVistas))
                    delete_terrenos.triggered.connect(lambda: SubirCotasTerreno.eliminar_terrenos(idproyecto, idzona, "Cotas de Terreno", "4", treeWidget, reiniciarVistas))
            else:    
                if tipo == "piezometrocuerda":
                    nombrepiezo = item.text(0)
                    idinstrumento = item.text(2)
                    nombrezona = item.parent().parent().text(0)
                    idcomponente = item.parent().parent().text(2)
                    idproyecto = item.parent().parent().text(3)
                    custom_cuerda = menu.addAction("Personalizar Piezómetro")
                    edit_cuerda = menu.addAction("Editar Piezómetro")
                    delete_cuerda = menu.addAction("Eliminar Piezómetro")
                    custom_cuerda.triggered.connect(lambda: Personalizacion.personalizarEquipoGrafica(idproyecto, idinstrumento, nombrepiezo, "PIEZÓMETRO CUERDA VIBRANTE"))
                    edit_cuerda.triggered.connect(lambda: SubirPiezometros.actualizarPiezometroCuerda(idproyecto, idcomponente, idinstrumento, treeWidget, "Piezómetros Cuerda Vibrante", "1", "piezometrocuerda", reiniciarVistas, vista))
                    delete_cuerda.triggered.connect(lambda: SubirPiezometros.eliminar_piezocuerda(idproyecto, idinstrumento, nombrepiezo, "Piezómetros Cuerda Vibrante", "piezometrocuerda", treeWidget, reiniciarVistas))
                elif tipo == "cotacuerda":
                    nombrecota = item.text(0)
                    if nombrecota == "Cota de Fundación":
                        tipoinstru = 1
                    else:
                        tipoinstru = 2
                    idinstrumento = item.parent().text(2)
                    nombrepiezo = item.parent().text(0)
                    nombrezona = item.parent().parent().parent().text(0)
                    idcomponente = item.parent().parent().parent().text(2)
                    idproyecto = item.parent().parent().parent().text(3)
                    custom_cota = menu.addAction("Personalizar Cota")
                    custom_cota.triggered.connect(lambda: Personalizacion.personalizarEquipoGrafica(idproyecto, idinstrumento, nombrecota, f"COTA DE PIEZÓMETRO {nombrepiezo}", tipoinstru))
                elif tipo == "piezometromanual":
                    nombrepiezo = item.text(0)
                    idinstrumento = item.text(2)
                    nombrezona = item.parent().parent().text(0)
                    idcomponente = item.parent().parent().text(2)
                    idproyecto = item.parent().parent().text(3)
                    custom_manual = menu.addAction("Personalizar Piezómetro")
                    edit_piezomanual = menu.addAction("Editar Piezómetro")
                    delete_piezomanual = menu.addAction("Eliminar Piezómetro")
                    custom_manual.triggered.connect(lambda: Personalizacion.personalizarEquipoGrafica(idproyecto, idinstrumento, nombrepiezo, "PIEZÓMETRO CASAGRANDE"))
                    edit_piezomanual.triggered.connect(lambda: SubirPiezometros.actualizarPiezometroManual(idproyecto, idcomponente, idinstrumento, treeWidget, "Piezómetros Casagrande", "2", "piezometromanual", reiniciarVistas, vista))
                    delete_piezomanual.triggered.connect(lambda: SubirPiezometros.eliminar_piezomanual(idproyecto, idinstrumento, nombrepiezo, "Piezómetros Casagrande", "piezometromanual", treeWidget, reiniciarVistas))
                elif tipo == "cotamanual":
                    nombrecota = item.text(0)
                    if nombrecota == "Cota de Fundación":
                        tipoinstru = 1
                    else:
                        tipoinstru = 2
                    idinstrumento = item.parent().text(2)
                    nombrepiezo = item.parent().text(0)
                    nombrezona = item.parent().parent().parent().text(0)
                    idcomponente = item.parent().parent().parent().text(2)
                    idproyecto = item.parent().parent().parent().text(3)
                    custom_cota = menu.addAction("Personalizar Cota")
                    custom_cota.triggered.connect(lambda: Personalizacion.personalizarEquipoGrafica(idproyecto, idinstrumento, nombrecota, f"COTA DE PIEZÓMETRO {nombrepiezo}", tipoinstru))
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
                    edit_pluviometro.triggered.connect(lambda: SubirPluviometros.actualizarPluviometro(idproyecto, idcomponente, idinstrumento, treeWidget, "Pluviómetros", "3", "pluviometro", reiniciarVistas))
                    delete_pluviometro.triggered.connect(lambda: SubirPluviometros.eliminar_pluviometro(idproyecto, idinstrumento, nombrepluvio, "Pluviómetros", "pluviometro", treeWidget, reiniciarVistas))
                elif tipo == "terreno":
                    nombreterreno = item.text(0)
                    idinstrumento = item.text(2)
                    nombrezona = item.parent().parent().text(0)
                    idcomponente = item.parent().parent().text(2)
                    idproyecto = item.parent().parent().text(3)
                    custom_cotaterreno = menu.addAction("Personalizar Cota")
                    edit_cotaterreno = menu.addAction("Editar Cota Terreno")
                    delete_cotaterreno = menu.addAction("Eliminar Cota Terreno")
                    custom_cotaterreno.triggered.connect(lambda: Personalizacion.personalizarEquipoGrafica(idproyecto, idinstrumento, nombreterreno, "COTA DE TERRENO"))
                    edit_cotaterreno.triggered.connect(lambda: SubirCotasTerreno.actualizarCotaTerreno(idproyecto, idcomponente, idinstrumento, treeWidget, "Cotas de Terreno", "4", "terreno", reiniciarVistas))
                    delete_cotaterreno.triggered.connect(lambda: SubirCotasTerreno.eliminar_cotaterreno(idproyecto, idinstrumento, nombreterreno, "Cotas de Terreno", "terreno", treeWidget, reiniciarVistas))
            menu.exec(treeWidget.mapToGlobal(point))
    
    def validarMarcadoUnEquipoZona(datos, zona):
        # validar si existe un solo pluviometros y un solo tipo de piezómetros
        respuesta = True
        if datos:
            equipos = datos.get(zona)
            pluvio, piezocu, piezoma = True, 0, 0
            for tipo, equipos in equipos.items():
                if tipo[0] == "Piezómetros Cuerda Vibrante":
                    piezocu += 1
                if tipo[0] == "Piezómetros Casagrande":
                    piezoma += 1
                if tipo[0] == "Pluviómetros":
                    if len(equipos) > 0:
                        pluvio = False
            if piezocu > 0 and piezoma > 0:
                respuesta = False, 0
            else:
                tipito = 0
                if piezocu > 0:
                    tipito = 1
                if piezoma > 0:
                    tipito = 2
                respuesta = pluvio, tipito
        return respuesta
    
    def validarVariosPluviometros(datos, zona):
        respuesta = True
        if datos:
            equipos = datos.get(zona)
            for tipo, equipos in equipos.items():
                if tipo[0] == "Pluviómetros":
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
    
    def limpiarEquiposTipo(tree_widget, tipo):
        for t in range(tree_widget.topLevelItemCount()):
            grupo = tree_widget.topLevelItem(t)
            for g in range(grupo.childCount()):
                equipo = grupo.child(g)
                nombre = equipo.text(1)
                if str(nombre) != str(tipo) and str(nombre) != str(3) and str(nombre) != str(4):
                    equipo.setCheckState(0, Qt.Unchecked)
                    EquiposPiezometros.desmarcarHijos(equipo)
    
    def desmarcarHijos(item):
        for h in range(item.childCount()):
            hijo = item.child(h)
            hijo.setCheckState(0, Qt.Unchecked)
            EquiposPiezometros.desmarcarHijos(hijo)
            EquiposPiezometros.actualizar_estado_padre_hijos(hijo)
    
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
                EquiposPiezometros.marcardesmarcar_todos_hijos(hijo, estado, nivel)
        else:
            # Si estamos marcando, controlar la profundidad
            if nivel <= 0:
                return
            for i in range(nodo.childCount()):
                hijo = nodo.child(i)
                EquiposPiezometros.marcardesmarcar_todos_hijos(hijo, estado, nivel - 1)
    
    # Función para marcar o desmarcar excepto los pluviometros
    def desmarcar_todos_piezometros(nodo):
        if nodo.parent():
            parent = nodo.parent()
            for i in range(parent.childCount()):
                hijo = parent.child(i)
                nombre = hijo.text(0)
                if nombre != "Pluviómetros" and nombre != "Cotas de Terreno":
                    hijo.setCheckState(0, Qt.Unchecked)
                    EquiposPiezometros.marcardesmarcar_todos_hijos(hijo, Qt.Unchecked)
    
    def desmarcar_todos_piezometros_hijo(nodo):
        if nodo.parent():
            if nodo.parent().parent():
                parent = nodo.parent().parent()
                for i in range(parent.childCount()):
                    hijo = parent.child(i)
                    nombre = hijo.text(0)
                    if nombre != "Pluviómetros" and nombre != "Cotas de Terreno":
                        hijo.setCheckState(0, Qt.Unchecked)
                        EquiposPiezometros.marcardesmarcar_todos_hijos(hijo, Qt.Unchecked)

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
                EquiposPiezometros.actualizar_estado_padre_hijos(nodo.parent())

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
            resultado_grupo = EquiposPiezometros.obtener_elementos_marcados_recursivo(grupo)
            if resultado_grupo:
                elementos_marcados.update(resultado_grupo)
        return elementos_marcados
    
    def obtener_elementos_marcados_recursivo(nodo):
        hijos_marcados = []
        if nodo.childCount() > 0:
            marcados = {}
            for i in range(nodo.childCount()):
                hijo = nodo.child(i)
                resultado_hijo = EquiposPiezometros.obtener_elementos_marcados_recursivo(hijo)
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
            return EquiposPiezometros.obtener_elementos_des_marcados_recursivo(nodo.parent())
        else:
            marcados = EquiposPiezometros.obtener_elementos_marcados_recursivo(nodo)
        return marcados
     
    def obtener_todos_elementos_arbol(tree_widget):
        elementos = {}
        for i in range(tree_widget.topLevelItemCount()):
            grupo = tree_widget.topLevelItem(i)
            resultado_grupo = EquiposPiezometros.obtener_elementos_arbol_recursivo(grupo)
            if resultado_grupo:
                elementos.update(resultado_grupo)
        return elementos
    
    def obtener_elementos_arbol_recursivo(nodo):
        hijos = []
        if nodo.childCount() > 0:
            marcados = {}
            for i in range(nodo.childCount()):
                hijo = nodo.child(i)
                resultado_hijo = EquiposPiezometros.obtener_elementos_arbol_recursivo(hijo)
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
    
    def obtenerListaPiezocuerdamanualFechas(tipo, piezometrosmarcados, proyectoid):
        resultado = []
        for componente, piezometros in piezometrosmarcados:
            nombrecomponente, idcomponente, idproy = componente
            dict_piezometros = {}
            for piezome in piezometros:
                nombrepiezo, idinstru, idpiezo = piezome
                fechas = InterfazController.ctrlListarFechasPiezometroCodigo(tipo, idcomponente, idpiezo, proyectoid)
                if fechas:
                    ultima_fecha = fechas[-1][0]
                    dict_piezometros[piezome] = ultima_fecha
            resultado.append((componente, dict_piezometros))
        return resultado
    
    def inicializar_lista_equipos(tree_widget, proyecto_id, proyecto_name):
        TreeCheckbox.limpiarArbolCheckboxes(tree_widget, proyecto_name)
        if proyecto_id:
            # LISTAR COMOPONENTES
            componentes = InterfazController.ctrlListarComponentesProyecto(proyecto_id)
            if componentes:
                for zona in componentes:
                    idzona = zona[0]
                    namezona = zona[2]
                    # LISTAR PIEZOMETROS CUERDA VIBRANTE
                    piezometroscuerda = InterfazController.ctrlListarPiezometrosCuerdaComponente(idzona, proyecto_id)
                    if piezometroscuerda:
                        TreeCheckbox.crearNuevoGrupoCheckboxesDoble(tree_widget, namezona, idzona, proyecto_id, "Piezómetros Cuerda Vibrante", "1", piezometroscuerda, "piezometrocuerda")
                    # LISTAR PIEZOMETROS MANUALES
                    piezometrosmanual = InterfazController.ctrlListarPiezometrosManualComponente(idzona, proyecto_id)
                    if piezometrosmanual:
                        TreeCheckbox.crearNuevoGrupoCheckboxesDoble(tree_widget, namezona, idzona, proyecto_id, "Piezómetros Casagrande", "2", piezometrosmanual, "piezometromanual")
                    # LISTAR PLUVIOMETROS
                    pluviometros = InterfazController.ctrlListarPluviometrosComponente(proyecto_id, idzona)
                    if pluviometros:
                        TreeCheckbox.crearNuevoGrupoCheckboxesDoble(tree_widget, namezona, idzona, proyecto_id, "Pluviómetros", "3", pluviometros, "pluviometro")
                    # LISTAR COTAS DE TERRENO
                    terrenos = InterfazController.ctrlListarCotasTerrenoComponente(proyecto_id, idzona)
                    if terrenos:
                        TreeCheckbox.crearNuevoGrupoCheckboxesDoble(tree_widget, namezona, idzona, proyecto_id, "Cotas de Terreno", "4", terrenos, "terreno")

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
    