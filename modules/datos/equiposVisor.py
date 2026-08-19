import os
from PySide6.QtWidgets import QMenu
from PySide6.QtCore import Qt
from utils.shared.arbolmarcado import TreeCheckbox
from modules.proyecto.crearProyecto import CrearProyecto
from modules.datos.subirTopografias import SubirTopografias
from modules.datos.subirPrismas import SubirPrismas
from modules.datos.subirInclinometros import SubirInclinometros
from modules.datos.subirPiezometros import SubirPiezometros
from modules.datos.subirPluviometros import SubirPluviometros
from modules.datos.subirCeldas import SubirCeldas
from modules.datos.subirAcelerografos import SubirAcelerografos
from modules.datos.subirTDR import SubirTDR
from controllers.InterfazController import InterfazController
from modules.datos.registroEquipos import RegistroEquipos
from utils.common.rutasarchivos import resource_path

class EquiposVisor:

    def validarMarcadoCheckbox(parent_item, column, obtenerEquiposMarcados):
        codigo = parent_item.text(1)
        estado = parent_item.checkState(0)
        if estado != Qt.CheckState.PartiallyChecked:
            # comprobar si el código es numérico (primer nivel)
            if codigo.isdigit():
                if codigo == "0": # COMPONENTE
                    EquiposVisor.marcardesmarcar_todos_hijos(parent_item, estado)
                    # Ocultar info
                else:
                    EquiposVisor.marcardesmarcar_todos_hijos(parent_item, estado)
                    EquiposVisor.actualizar_estado_padre_hijos(parent_item)
            else:  # child (Hijos del parent)
                EquiposVisor.marcardesmarcar_todos_hijos(parent_item, estado)
                EquiposVisor.actualizar_estado_padre_hijos(parent_item)
            # mostrar en el visor
            obtenerEquiposMarcados()
          
    def validarOpcionesMenuCheckbox(point, main, treeWidget, graficarnuevafechasinclinometros, graficarnuevafechaspiezometros, validarMostrarTopografias, reiniciarvistas):
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
                elif tipo == "1": # Topografías
                    idzona = item.text(2)
                    idproyecto = item.text(3)
                    nombrezona = item.parent().text(0)
                    edit_topografia = menu.addAction("Cambiar de Componente")
                    delete_topografia = menu.addAction("Eliminar Topografías")
                    edit_topografia.triggered.connect(lambda: SubirTopografias.cambiar_componente_topografias(idzona, idproyecto, treeWidget, "Topografías", "1", "topografia", validarMostrarTopografias))
                    delete_topografia.triggered.connect(lambda: SubirTopografias.eliminar_topografias(idzona, "Topografías", "1", treeWidget, validarMostrarTopografias))
                elif tipo == "2": # Prismas
                    idzona = item.text(2)
                    idproyecto = item.text(3)
                    nombrezona = item.parent().text(0)
                    edit_prismasalta = menu.addAction("Dar de Baja")
                    change_prismasalta = menu.addAction("Cambiar de Componente")
                    delete_prismasalta = menu.addAction("Eliminar Prismas")
                    edit_prismasalta.triggered.connect(lambda: SubirPrismas.dardebaja_prismas(idzona, idproyecto, nombrezona, treeWidget, "Prismas", "2", reiniciarvistas))
                    change_prismasalta.triggered.connect(lambda: SubirPrismas.cambiar_componente_prismas(idzona, idproyecto, treeWidget, "Prismas", "2", "prisma", reiniciarvistas))
                    delete_prismasalta.triggered.connect(lambda: SubirPrismas.eliminar_prismas(idzona, "Prismas", "2", treeWidget, reiniciarvistas))
                elif tipo == "3": # Inclinometros
                    idzona = item.text(2)
                    idproyecto = item.text(3)
                    edit_inclinometros = menu.addAction("Cambiar de Componente")
                    delete_inclinometros = menu.addAction("Eliminar Inclinómetros")
                    edit_inclinometros.triggered.connect(lambda: SubirInclinometros.cambiar_componente_inclinometros(idzona, idproyecto, treeWidget, "Inclinómetros", "3", "inclinometro", reiniciarvistas))
                    delete_inclinometros.triggered.connect(lambda: SubirInclinometros.eliminar_inclinometros(idproyecto, idzona, "Inclinómetros", "3", treeWidget, reiniciarvistas))
                elif tipo == "4": # Piezometros Cuerda Vibrante
                    idzona = item.text(2)
                    idproyecto = item.text(3)
                    nombrezona = item.parent().text(0)
                    edit_piezocuerdas = menu.addAction("Cambiar de Componente")
                    delete_piezocuerdas = menu.addAction("Eliminar P. Cuerda Vibrante")
                    edit_piezocuerdas.triggered.connect(lambda: SubirPiezometros.cambiar_componente_piezocuerdas(idzona, idproyecto, treeWidget, "Piezómetros Cuerda Vibrante", "4", "piezometrocuerda", reiniciarvistas))
                    delete_piezocuerdas.triggered.connect(lambda: SubirPiezometros.eliminar_piezocuerdas(idproyecto, idzona, "Piezómetros Cuerda Vibrante", "4", treeWidget, reiniciarvistas))
                elif tipo == "5": # Piezometros Manuales - Casagrande
                    idzona = item.text(2)
                    idproyecto = item.text(3)
                    nombrezona = item.parent().text(0)
                    edit_piezomanuales = menu.addAction("Cambiar de Componente")
                    delete_piezomanuales = menu.addAction("Eliminar P. Casagrande")
                    edit_piezomanuales.triggered.connect(lambda: SubirPiezometros.cambiar_componente_piezomanuales(idzona, idproyecto, treeWidget, "Piezómetros Casagrande", "5", "piezometromanual", reiniciarvistas))
                    delete_piezomanuales.triggered.connect(lambda: SubirPiezometros.eliminar_piezomanuales(idproyecto, idzona, "Piezómetros Casagrande", "5", treeWidget, reiniciarvistas))
                elif tipo == "6": # Pluviometros
                    idzona = item.text(2)
                    idproyecto = item.text(3)
                    nombrezona = item.parent().text(0)
                    edit_pluviometros = menu.addAction("Cambiar de Componente")
                    delete_pluviometros = menu.addAction("Eliminar Pluviómetros")
                    edit_pluviometros.triggered.connect(lambda: SubirPluviometros.cambiar_componente_pluviometros(idzona, idproyecto, treeWidget, "Pluviómetros", "6", "pluviometro", reiniciarvistas))
                    delete_pluviometros.triggered.connect(lambda: SubirPluviometros.eliminar_pluviometros(idproyecto, idzona, "Pluviómetros", "6", treeWidget, reiniciarvistas))
                elif tipo == "7": # Celdas Asentamiento
                    idzona = item.text(2)
                    idproyecto = item.text(3)
                    nombrezona = item.parent().text(0)
                    edit_celdas = menu.addAction("Cambiar de Componente")
                    delete_celdas = menu.addAction("Eliminar Celdas")
                    edit_celdas.triggered.connect(lambda: SubirCeldas.cambiar_componente_celdas(idzona, idproyecto, treeWidget, "Celdas de Asentamiento", "7", "celda", reiniciarvistas))
                    delete_celdas.triggered.connect(lambda: SubirCeldas.eliminar_celdas(idproyecto, idzona, "Celdas de Asentamiento", "7", treeWidget, reiniciarvistas))
                elif tipo == "8": # Acelerografos
                    idzona = item.text(2)
                    idproyecto = item.text(3)
                    nombrezona = item.parent().text(0)
                    edit_acelerografos = menu.addAction("Cambiar de Componente")
                    delete_acelerografos = menu.addAction("Eliminar Acelerógrafos")
                    edit_acelerografos.triggered.connect(lambda: SubirAcelerografos.cambiar_componente_acelerografos(idzona, idproyecto, treeWidget, "Acelerógrafos", "8", "acelerografo", reiniciarvistas))
                    delete_acelerografos.triggered.connect(lambda: SubirAcelerografos.eliminar_acelerografos(idproyecto, idzona, "Acelerógrafos", "8", treeWidget, reiniciarvistas))
                elif tipo == "9": # Sondajes TDR
                    idzona = item.text(2)
                    idproyecto = item.text(3)
                    nombrezona = item.parent().text(0)
                    edit_sondajestdr = menu.addAction("Cambiar de Componente")
                    delete_sondajestdr = menu.addAction("Eliminar TDR")
                    edit_sondajestdr.triggered.connect(lambda: SubirTDR.cambiar_componente_sondajestdr(idzona, idproyecto, treeWidget, "TDR", "9", "sondajetdr", reiniciarvistas))
                    delete_sondajestdr.triggered.connect(lambda: SubirTDR.eliminar_sondajestdr(idproyecto, idzona, "TDR", "9", treeWidget, reiniciarvistas))
                elif tipo == "10": # Equipos Adicionales
                    idzona = item.text(2)
                    idproyecto = item.text(3)
                    nombrezona = item.parent().text(0)
                    edit_equipos = menu.addAction("Cambiar de Componente")
                    delete_equipos = menu.addAction("Eliminar E. Adicionales")
                    edit_equipos.triggered.connect(lambda: RegistroEquipos.cambiar_componente_adicionales(idzona, idproyecto, treeWidget, "Equipos Adicionales", "10", "adicional", reiniciarvistas))
                    delete_equipos.triggered.connect(lambda: RegistroEquipos.eliminar_adicionales(idproyecto, idzona, "Equipos Adicionales", "10", treeWidget, reiniciarvistas))
            else:    
                if tipo == "topografia":
                    nombretopo = item.text(0)
                    idinstrumento = item.text(2)
                    nombrezona = item.parent().parent().text(0)
                    idcomponente = item.parent().parent().text(2)
                    idproyecto = item.parent().parent().text(3)
                    change_topo = menu.addAction("Actualizar Topografía")
                    delete_topo = menu.addAction("Eliminar Topografía")
                    change_topo.triggered.connect(lambda: SubirTopografias.actualizarTopografia(idproyecto, idcomponente, idinstrumento, treeWidget, "Topografías", "1", "topografia", validarMostrarTopografias))
                    delete_topo.triggered.connect(lambda: SubirTopografias.eliminar_topografia(idinstrumento, nombretopo, "Topografías", "topografia", treeWidget, validarMostrarTopografias))
                elif tipo == "actortopo":
                    nombreactor = item.text(0)
                    idinstruactor = item.text(2)
                    rutaactor = item.text(3)
                    tipoactor = item.text(4)
                    if tipoactor == "VTP":
                        nombrezona = item.parent().parent().parent().text(0)
                        idcomponente = item.parent().parent().parent().text(2)
                        idproyecto = item.parent().parent().parent().text(3)
                        delete_actor = menu.addAction("Eliminar Elemento")
                        delete_actor.triggered.connect(lambda: SubirTopografias.eliminar_elemento(idinstruactor, nombreactor, rutaactor, "Topografías", "topografia", "actortopo", treeWidget, validarMostrarTopografias))
                elif tipo == "prisma":
                    nombreprisma = item.text(0)
                    idinstrumento = item.text(2)
                    nombrezona = item.parent().parent().text(0)
                    idcomponente = item.parent().parent().text(2)
                    idproyecto = item.parent().parent().text(3)
                    edit_prisma = menu.addAction("Dar de Baja")
                    change_prisma = menu.addAction("Cambiar de Componente")
                    delete_prisma = menu.addAction("Eliminar Prisma")
                    edit_prisma.triggered.connect(lambda: SubirPrismas.dardebaja_prisma(main, idproyecto, idcomponente, nombreprisma, idinstrumento, nombrezona, treeWidget, reiniciarvistas))
                    change_prisma.triggered.connect(lambda: SubirPrismas.cambiar_componente_prisma(idinstrumento, idcomponente, idproyecto, treeWidget, "Prismas", "1", "prisma", 1, reiniciarvistas))
                    delete_prisma.triggered.connect(lambda: SubirPrismas.eliminar_prisma(idinstrumento, nombreprisma, "Prismas", "prisma", treeWidget, reiniciarvistas))
                elif tipo == "inclinometro":
                    estado = item.checkState(0)
                    nombreinclino = item.text(0)
                    idinstrumento = item.text(2)
                    nombrezona = item.parent().parent().text(0)
                    idcomponente = item.parent().parent().text(2)
                    idproyecto = item.parent().parent().text(3)
                    # obtener marcados si está marcado
                    if estado == Qt.Checked:
                        lista = EquiposVisor.obtener_todos_elementos_marcados(treeWidget)
                        if lista:
                            inclifechas = EquiposVisor.obtenerListaFechasEquipoMarcado(lista, "Inclinómetros", idcomponente, idinstrumento)
                        else:
                            inclifechas = None
                    else:
                        inclifechas = None
                    date_inclino = menu.addAction("Marcar/Desmarcar Fechas")
                    edit_inclino = menu.addAction("Editar Inclinómetro")
                    delete_inclino = menu.addAction("Eliminar Inclinómetro")
                    date_inclino.triggered.connect(lambda: SubirInclinometros.mostrarDialogoFechasInclinometros(treeWidget, inclifechas, idproyecto, idcomponente, idinstrumento, nombrezona, nombreinclino, estado, graficarnuevafechasinclinometros))
                    edit_inclino.triggered.connect(lambda: SubirInclinometros.actualizarInclinometro(idproyecto, idcomponente, idinstrumento, treeWidget, "Inclinómetros", "3", "inclinometro", "SI", reiniciarvistas))
                    delete_inclino.triggered.connect(lambda: SubirInclinometros.eliminar_inclinometro(idproyecto, idinstrumento, nombreinclino, "Inclinómetros", "inclinometro", treeWidget, reiniciarvistas))
                elif tipo == "piezometrocuerda":
                    estado = item.checkState(0)
                    nombrepiezo = item.text(0)
                    idinstrumento = item.text(2)
                    nombrezona = item.parent().parent().text(0)
                    idcomponente = item.parent().parent().text(2)
                    idproyecto = item.parent().parent().text(3)
                    # obtener fechamarcada si está marcado
                    if estado == Qt.Checked:
                        lista = EquiposVisor.obtener_todos_elementos_marcados(treeWidget)
                        if lista:
                            fechamarcada = EquiposVisor.obtenerListaFechasEquipoMarcado(lista, "Piezómetros Cuerda Vibrante", idcomponente, idinstrumento)
                        else:
                            fechamarcada = None
                    else:
                        fechamarcada = None
                    date_cuerda = menu.addAction("Marcar/Desmarcar Fechas")
                    edit_cuerda = menu.addAction("Editar Piezómetro")
                    delete_cuerda = menu.addAction("Eliminar Piezómetro")
                    date_cuerda.triggered.connect(lambda: SubirPiezometros.mostrarDialogoFechasPiezometros(treeWidget, idproyecto, idcomponente, idinstrumento, nombrezona, nombrepiezo, fechamarcada, "Automatizado", graficarnuevafechaspiezometros))
                    edit_cuerda.triggered.connect(lambda: SubirPiezometros.actualizarPiezometroCuerda(idproyecto, idcomponente, idinstrumento, treeWidget, "Piezómetros Cuerda Vibrante", "4", "piezometrocuerda", reiniciarvistas))
                    delete_cuerda.triggered.connect(lambda: SubirPiezometros.eliminar_piezocuerda(idproyecto, idinstrumento, nombrepiezo, "Piezómetros Cuerda Vibrante", "piezometrocuerda", treeWidget, reiniciarvistas))
                elif tipo == "piezometromanual":
                    estado = item.checkState(0)
                    nombrepiezo = item.text(0)
                    idinstrumento = item.text(2)
                    nombrezona = item.parent().parent().text(0)
                    idcomponente = item.parent().parent().text(2)
                    idproyecto = item.parent().parent().text(3)
                    # obtener fechamarcada si está marcado
                    if estado == Qt.Checked:
                        lista = EquiposVisor.obtener_todos_elementos_marcados(treeWidget)
                        if lista:
                            fechamarcada = EquiposVisor.obtenerListaFechasEquipoMarcado(lista, "Piezómetros Casagrande", idcomponente, idinstrumento)
                        else:
                            fechamarcada = None
                    else:
                        fechamarcada = None
                    date_piezomanual = menu.addAction("Marcar/Desmarcar Fechas")
                    edit_piezomanual = menu.addAction("Editar Piezómetro")
                    delete_piezomanual = menu.addAction("Eliminar Piezómetro")
                    date_piezomanual.triggered.connect(lambda: SubirPiezometros.mostrarDialogoFechasPiezometros(treeWidget, idproyecto, idcomponente, idinstrumento, nombrezona, nombrepiezo, fechamarcada, "Manual", graficarnuevafechaspiezometros))
                    edit_piezomanual.triggered.connect(lambda: SubirPiezometros.actualizarPiezometroManual(idproyecto, idcomponente, idinstrumento, treeWidget, "Piezómetros Casagrande", "5", "piezometromanual", reiniciarvistas))
                    delete_piezomanual.triggered.connect(lambda: SubirPiezometros.eliminar_piezomanual(idproyecto, idinstrumento, nombrepiezo, "Piezómetros Casagrande", "piezometromanual", treeWidget, reiniciarvistas))
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
                elif tipo == "celda":
                    nombrecelda = item.text(0)
                    idinstrumento = item.text(2)
                    nombrezona = item.parent().parent().text(0)
                    idcomponente = item.parent().parent().text(2)
                    idproyecto = item.parent().parent().text(3)
                    edit_celda = menu.addAction("Editar Celda")
                    delete_celda = menu.addAction("Eliminar Celda")
                    edit_celda.triggered.connect(lambda: SubirCeldas.actualizarCeldaAsentamiento(idproyecto, idcomponente, idinstrumento, treeWidget, "Celdas de Asentamiento", "7", "celda", reiniciarvistas))
                    delete_celda.triggered.connect(lambda: SubirCeldas.eliminar_celda(idproyecto, idinstrumento, nombrecelda, "Celdas de Asentamiento", "celda", treeWidget, reiniciarvistas))
                elif tipo == "acelerografo":
                    nombreacelero = item.text(0)
                    idinstrumento = item.text(2)
                    nombrezona = item.parent().parent().text(0)
                    idcomponente = item.parent().parent().text(2)
                    idproyecto = item.parent().parent().text(3)
                    edit_acelero = menu.addAction("Editar Acelerógrafo")
                    delete_acelero = menu.addAction("Eliminar Acelerógrafo")
                    edit_acelero.triggered.connect(lambda: SubirAcelerografos.actualizarAcelerografo(idproyecto, idcomponente, idinstrumento, treeWidget, "Acelerógrafos", "8", "acelerografo", reiniciarvistas))
                    delete_acelero.triggered.connect(lambda: SubirAcelerografos.eliminar_acelerografo(idproyecto, idinstrumento, nombreacelero, "Acelerógrafos", "acelerografo", treeWidget, reiniciarvistas))
                elif tipo == "sondajetdr":
                    nombretdr = item.text(0)
                    idinstrumento = item.text(2)
                    nombrezona = item.parent().parent().text(0)
                    idcomponente = item.parent().parent().text(2)
                    idproyecto = item.parent().parent().text(3)
                    edit_tdr = menu.addAction("Editar Sondaje TDR")
                    delete_tdr = menu.addAction("Eliminar Sondaje TDR")
                    edit_tdr.triggered.connect(lambda: SubirTDR.actualizarSondajeTDR(idproyecto, idcomponente, idinstrumento, treeWidget, "TDR", "9", "sondajetdr", reiniciarvistas))
                    delete_tdr.triggered.connect(lambda: SubirTDR.eliminar_sondajetdr(idproyecto, idinstrumento, nombretdr, "TDR", "sondajetdr", treeWidget, reiniciarvistas))
                elif tipo == "adicional":
                    nombreequipo = item.text(0)
                    idinstrumento = item.text(2)
                    nombrezona = item.parent().parent().text(0)
                    idcomponente = item.parent().parent().text(2)
                    idproyecto = item.parent().parent().text(3)
                    edit_adicional = menu.addAction("Editar E. Adicional")
                    delete_adicional = menu.addAction("Eliminar E. Adicional")
                    edit_adicional.triggered.connect(lambda: RegistroEquipos.actualizarEquipoAdicional(idproyecto, idcomponente, idinstrumento, treeWidget, "Equipos Adicionales", "10", "adicional", reiniciarvistas))
                    delete_adicional.triggered.connect(lambda: RegistroEquipos.eliminar_adicional(idproyecto, idinstrumento, nombreequipo, "Equipos Adicionales", "adicional", treeWidget, reiniciarvistas))
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
            hijo.setData(0, Qt.UserRole + 999, estado) # 🔥 CLAVE: Sincronizar la memoria del hijo
            EquiposVisor.marcardesmarcar_todos_hijos(hijo, estado)

    # Función para actualizar el estado del padre en función del estado de sus hijos
    def actualizar_estado_padre_hijos(nodo):
        if nodo.parent():
            estados_hijos = [nodo.parent().child(i).checkState(0) for i in range(nodo.parent().childCount())]
            
            # Determinamos el nuevo estado
            if all(estado == Qt.Checked for estado in estados_hijos):
                nuevo_estado = Qt.Checked
            elif all(estado == Qt.Unchecked for estado in estados_hijos):
                nuevo_estado = Qt.Unchecked
            else:
                nuevo_estado = Qt.PartiallyChecked
                
            nodo.parent().setCheckState(0, nuevo_estado)
            nodo.parent().setData(0, Qt.UserRole + 999, nuevo_estado) # 🔥 CLAVE: Sincronizar la memoria del padre
            
        if nodo.parent():
            if nodo.parent().parent():
                EquiposVisor.actualizar_estado_padre_hijos(nodo.parent())

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
            resultado_grupo = EquiposVisor.obtener_elementos_marcados_recursivo(grupo)
            if resultado_grupo:
                elementos_marcados.update(resultado_grupo)
        return elementos_marcados
    
    def obtener_elementos_marcados_recursivo(nodo):
        hijos_marcados = []
        if nodo.childCount() > 0:
            marcados = {}
            for i in range(nodo.childCount()):
                hijo = nodo.child(i)
                resultado_hijo = EquiposVisor.obtener_elementos_marcados_recursivo(hijo)
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
            return EquiposVisor.obtener_elementos_des_marcados_recursivo(nodo.parent())
        else:
            marcados = EquiposVisor.obtener_elementos_marcados_recursivo(nodo)
        return marcados
     
    def obtener_todos_elementos_arbol(tree_widget):
        elementos = {}
        for i in range(tree_widget.topLevelItemCount()):
            grupo = tree_widget.topLevelItem(i)
            resultado_grupo = EquiposVisor.obtener_elementos_arbol_recursivo(grupo)
            if resultado_grupo:
                elementos.update(resultado_grupo)
        return elementos
    
    def obtener_elementos_arbol_recursivo(nodo):
        hijos = []
        if nodo.childCount() > 0:
            marcados = {}
            for i in range(nodo.childCount()):
                hijo = nodo.child(i)
                resultado_hijo = EquiposVisor.obtener_elementos_arbol_recursivo(hijo)
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
    
    def marcardesmarcar_todos_hijos_visor(nodo, estado):
        for i in range(nodo.childCount()):
            hijo = nodo.child(i)
            if not hijo.text(1).isdigit():
                if hijo.text(1) == "piezometrocuerda" or hijo.text(1) == "piezometromanual":
                    hijo.setCheckState(0, estado)
                    for i in range(hijo.childCount()):
                        nieto = hijo.child(i)
                        if i == hijo.childCount() - 1:
                            nieto.setCheckState(0, estado)
                        else:
                            nieto.setCheckState(0, Qt.Unchecked)
                else:
                    if hijo.parent().text(1) != "piezometrocuerda" and hijo.parent().text(1) != "piezometromanual":
                        hijo.setCheckState(0, estado)
            else:
                hijo.setCheckState(0, estado)
            EquiposVisor.marcardesmarcar_todos_hijos_visor(hijo, estado)
    
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
    
    def actualizarListaPiezocuerdamanualFechas(tipo, piezometrosmarcados, proyectoid, idcompo, idinstrumento, fechita):
        resultado = []
        for componente, piezometros in piezometrosmarcados:
            nombrecomponente, idcomponente, idproy = componente
            dict_piezometros = {}
            for piezome in piezometros:
                nombrepiezo, idinstru, idpiezo = piezome
                if idcompo == idcomponente and idinstru == idinstrumento:
                    dict_piezometros[piezome] = fechita
                else:
                    fechas = InterfazController.ctrlListarFechasPiezometroCodigo(tipo, idcomponente, idpiezo, proyectoid)
                    if fechas:
                        ultima_fecha = fechas[-1][0]
                        dict_piezometros[piezome] = ultima_fecha
            resultado.append((componente, dict_piezometros))
        return resultado
    
    def obtenerListaFechasEquipoMarcado(lista, tipolista, idcomponente, idinstrumento):
        for region, instrumentos in lista.items():
            for tipo, listainclinometros in instrumentos.items():
                if tipo[0] == tipolista and tipo[1] == idcomponente:
                    for nombreincli, idinstru, fechas in listainclinometros:
                        if idinstru == idinstrumento:
                            return fechas
        return None
    
    def inicializar_lista_equipos(tree_widget, proyecto_id, proyecto_name):
        TreeCheckbox.limpiarArbolCheckboxes(tree_widget, proyecto_name)
        if proyecto_id:
            # LISTAR COMOPONENTES
            componentes = InterfazController.ctrlListarComponentesProyecto(proyecto_id)
            if componentes:
                for zona in componentes:
                    idzona = zona[0]
                    namezona = zona[2]
                    # LISTAR TOPOGRAFIAS
                    try:
                        topografias = InterfazController.ctrlListarTopografiasComponente(idzona, 1)
                        if topografias:
                            # Validar que todos los archivos existan antes de mostrar el grupo
                            topografias_validas = []
                            for topo in topografias:
                                try:
                                    tipotopo = topo[10]
                                    ruta_raw = topo[11]
                                    if not ruta_raw:
                                        continue
                                    ruta_resuelta = resource_path(ruta_raw)
                                    if tipotopo == "VTP":
                                        if os.path.isdir(ruta_resuelta):
                                            archivos = [f for f in os.listdir(ruta_resuelta) if f.endswith('.vtp')]
                                            if archivos:
                                                topografias_validas.append(topo)
                                    else:
                                        if os.path.isfile(ruta_resuelta):
                                            topografias_validas.append(topo)
                                except Exception:
                                    continue
                            # Solo crear el grupo si hay al menos una topografía válida
                            if topografias_validas:
                                TreeCheckbox.crearGrupoCheckboxDobleTopografia(tree_widget, namezona, idzona, proyecto_id, "Topografías", "1", topografias_validas, "topografia")
                    except Exception as e:
                        print(f"[VISOR] Error topografías zona {namezona}: {e}")
                    # LISTAR PRISMAS
                    prismas = InterfazController.ctrlListarPrismasComponente(idzona, 1)
                    if prismas:
                        TreeCheckbox.crearNuevoGrupoCheckboxesSimple(tree_widget, namezona, idzona, proyecto_id, "Prismas", "2", prismas, "prisma")
                    # LISTAR INCLINOMETROS
                    inclinometros = InterfazController.ctrlListarInclinometrosComponente(idzona, proyecto_id)
                    if inclinometros:
                        TreeCheckbox.crearNuevoGrupoCheckboxesSimple(tree_widget, namezona, idzona, proyecto_id, "Inclinómetros", "3", inclinometros, "inclinometro", "SI")
                    # LISTAR PIEZOMETROS CUERDA VIBRANTE
                    piezometroscuerda = InterfazController.ctrlListarPiezometrosCuerdaComponente(idzona, proyecto_id)
                    if piezometroscuerda:
                        TreeCheckbox.crearNuevoGrupoCheckboxesSimple(tree_widget, namezona, idzona, proyecto_id, "Piezómetros Cuerda Vibrante", "4", piezometroscuerda, "piezometrocuerda", "SI")
                    # LISTAR PIEZOMETROS MANUALES
                    piezometrosmanual = InterfazController.ctrlListarPiezometrosManualComponente(idzona, proyecto_id)
                    if piezometrosmanual:
                        TreeCheckbox.crearNuevoGrupoCheckboxesSimple(tree_widget, namezona, idzona, proyecto_id, "Piezómetros Casagrande", "5", piezometrosmanual, "piezometromanual", "SI")
                    # LISTAR PLUVIOMETROS
                    pluviometros = InterfazController.ctrlListarPluviometrosComponente(proyecto_id, idzona)
                    if pluviometros:
                        TreeCheckbox.crearNuevoGrupoCheckboxesSimple(tree_widget, namezona, idzona, proyecto_id, "Pluviómetros", "6", pluviometros, "pluviometro")
                    # LISTAR CELDAS DE ASENTAMIENTO
                    celdas = InterfazController.ctrlListarCeldasComponente(proyecto_id, idzona)
                    if celdas:
                        TreeCheckbox.crearNuevoGrupoCheckboxesSimple(tree_widget, namezona, idzona, proyecto_id, "Celdas de Asentamiento", "7", celdas, "celda")
                    # LISTAR ACELERÓGRAFOS
                    acelerografos = InterfazController.ctrlListarAcelerografosComponente(proyecto_id, idzona)
                    if acelerografos:
                        TreeCheckbox.crearNuevoGrupoCheckboxesSimple(tree_widget, namezona, idzona, proyecto_id, "Acelerógrafos", "8", acelerografos, "acelerografo")
                    # LISTAR SONDAS TDR
                    sondajestdr = InterfazController.ctrlListarSondajesTDRComponente(idzona, proyecto_id)
                    if sondajestdr:
                        TreeCheckbox.crearNuevoGrupoCheckboxesSimple(tree_widget, namezona, idzona, proyecto_id, "TDR", "9", sondajestdr, "sondajetdr")
                    # LISTAR EQUIPOS ADICIONALES
                    adicionales = InterfazController.ctrlListarEquiposAdicionalesComponente(idzona)
                    if adicionales:
                        TreeCheckbox.crearNuevoGrupoCheckboxesSimple(tree_widget, namezona, idzona, proyecto_id, "Equipos Adicionales", "10", adicionales, "adicional")
                    # LISTAR PRISMAS VIRTUALES
                    virtuales = InterfazController.ctrlListarPrismasVirtualesComponente(idzona)
                    if virtuales:
                        TreeCheckbox.crearNuevoGrupoCheckboxesSimple(tree_widget, namezona, idzona, proyecto_id, "Prismas Virtuales", "11", virtuales, "prismavirtual")

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
    