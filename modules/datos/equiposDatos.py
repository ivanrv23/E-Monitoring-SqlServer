from PySide6.QtWidgets import QMenu
from PySide6.QtCore import Qt
from utils.shared.arbolmarcado import TreeCheckbox
from utils.common.alertas import mostrar_mensaje
from modules.proyecto.crearProyecto import CrearProyecto
from modules.datos.subirPrismas import SubirPrismas
from modules.datos.subirInclinometros import SubirInclinometros
from modules.datos.subirPiezometros import SubirPiezometros
from modules.datos.subirPluviometros import SubirPluviometros
from modules.datos.subirCotasTerreno import SubirCotasTerreno
from modules.datos.subirCeldas import SubirCeldas
from modules.datos.subirAcelerografos import SubirAcelerografos
from modules.datos.subirTDR import SubirTDR
from controllers.InterfazController import InterfazController
from modules.datos.registroEquipos import RegistroEquipos

class EquiposDatos:

    def validarMarcadoCheckbox(parent_item, column, treeWidget, obtenerEquiposMarcados):
        nombre = parent_item.text(column)
        codigo = parent_item.text(1)
        idgrupo = parent_item.text(2)
        tipogrupo = parent_item.text(3)
        estado = parent_item.checkState(0)
        if estado != Qt.CheckState.PartiallyChecked:
            nombremarcado = (nombre, idgrupo, tipogrupo)
            # comprobar si el código es numérico (primer nivel)
            if codigo.isdigit():
                if codigo == "0": # COMPONENTE
                    if estado == Qt.Checked:
                        # validar si solo hay un tipo de equipo
                        equipos = EquiposDatos.obtener_todos_elementos_arbol(treeWidget)
                        if EquiposDatos.validarMarcadoUnEquipoZona(equipos, nombremarcado):
                            # Desmarcar todo el arbol
                            EquiposDatos.desmarcar_todos_hijos_arbol(treeWidget)
                            parent_item.setCheckState(0, estado)
                            EquiposDatos.marcardesmarcar_todos_hijos(parent_item, estado)
                        else:
                            mostrar_mensaje("MARCACIÓN MÚLTIPLE", "Solo debe marcar un tipo de equipo.", "advertencia")
                            EquiposDatos.actualizar_estado_padre_padre(parent_item)
                    elif estado == Qt.Unchecked:
                        EquiposDatos.marcardesmarcar_todos_hijos(parent_item, estado)
                else:
                    if estado == Qt.Checked:
                        # Desmarcar todo el arbol
                        EquiposDatos.desmarcar_todos_hijos_arbol(treeWidget)
                        EquiposDatos.marcardesmarcar_todos_hijos(parent_item, estado)
                        parent_item.setCheckState(0, estado)
                        EquiposDatos.actualizar_estado_padre_hijos(parent_item)
                    elif estado == Qt.Unchecked:
                        EquiposDatos.marcardesmarcar_todos_hijos(parent_item, estado)
                        EquiposDatos.actualizar_estado_padre_hijos(parent_item)     
            else:  # child (Hijos del parent)
                if estado == Qt.Checked:
                    # Validar si es del mismo tipo equipo
                    marcados = EquiposDatos.obtener_todos_elementos_marcados(treeWidget)
                    if marcados:
                        zona = EquiposDatos.obtener_zona_tipoequipo_elementos_marcados(marcados, nombremarcado)
                        if EquiposDatos.validarPerteneceMismoEquipoZona(marcados, zona):
                            EquiposDatos.marcardesmarcar_todos_hijos(parent_item, estado)
                            EquiposDatos.actualizar_estado_padre_hijos(parent_item)
                        else:
                            EquiposDatos.desmarcar_todos_hijos_arbol(treeWidget)
                            EquiposDatos.marcardesmarcar_todos_hijos(parent_item, estado)
                            parent_item.setCheckState(0, estado)
                            EquiposDatos.actualizar_estado_padre_hijos(parent_item)
                    else:
                        EquiposDatos.marcardesmarcar_todos_hijos(parent_item, estado)
                        EquiposDatos.actualizar_estado_padre_hijos(parent_item)
                elif estado == Qt.Unchecked:
                    EquiposDatos.marcardesmarcar_todos_hijos(parent_item, estado)
                    EquiposDatos.actualizar_estado_padre_hijos(parent_item)
            # ACTUALIZAR TABLA
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
                    edit_prismasalta.triggered.connect(lambda: SubirPrismas.dardebaja_prismas(idzona, idproyecto, nombrezona, treeWidget, "Prismas", "1", reiniciarvistas, "DATOS"))
                    change_prismasalta.triggered.connect(lambda: SubirPrismas.cambiar_componente_prismas(idzona, idproyecto, treeWidget, "Prismas", "1", "prisma", reiniciarvistas))
                    delete_prismasalta.triggered.connect(lambda: SubirPrismas.eliminar_prismas(idzona, "Prismas", "1", treeWidget, reiniciarvistas))
                elif tipo == "2": # Inclinometros
                    idzona = item.text(2)
                    idproyecto = item.text(3)
                    edit_inclinometros = menu.addAction("Cambiar de Componente")
                    delete_inclinometros = menu.addAction("Eliminar Inclinómetros")
                    edit_inclinometros.triggered.connect(lambda: SubirInclinometros.cambiar_componente_inclinometros(idzona, idproyecto, treeWidget, "Inclinómetros", "2", "inclinometro", reiniciarvistas))
                    delete_inclinometros.triggered.connect(lambda: SubirInclinometros.eliminar_inclinometros(idproyecto, idzona, "Inclinómetros", "2", treeWidget, reiniciarvistas))
                elif tipo == "3": # Piezometros Cuerda Vibrante
                    idzona = item.text(2)
                    idproyecto = item.text(3)
                    nombrezona = item.parent().text(0)
                    edit_piezocuerdas = menu.addAction("Cambiar de Componente")
                    delete_piezocuerdas = menu.addAction("Eliminar P. Cuerda Vibrante")
                    edit_piezocuerdas.triggered.connect(lambda: SubirPiezometros.cambiar_componente_piezocuerdas(idzona, idproyecto, treeWidget, "Piezómetros Cuerda Vibrante", "3", "piezometrocuerda", reiniciarvistas))
                    delete_piezocuerdas.triggered.connect(lambda: SubirPiezometros.eliminar_piezocuerdas(idproyecto, idzona, "Piezómetros Cuerda Vibrante", "3", treeWidget, reiniciarvistas))
                elif tipo == "4": # Piezometros Manuales - Casagrande
                    idzona = item.text(2)
                    idproyecto = item.text(3)
                    nombrezona = item.parent().text(0)
                    edit_piezomanuales = menu.addAction("Cambiar de Componente")
                    delete_piezomanuales = menu.addAction("Eliminar P. Casagrande")
                    edit_piezomanuales.triggered.connect(lambda: SubirPiezometros.cambiar_componente_piezomanuales(idzona, idproyecto, treeWidget, "Piezómetros Casagrande", "4", "piezometromanual", reiniciarvistas))
                    delete_piezomanuales.triggered.connect(lambda: SubirPiezometros.eliminar_piezomanuales(idproyecto, idzona, "Piezómetros Casagrande", "4", treeWidget, reiniciarvistas))
                elif tipo == "5": # Pluviometros
                    idzona = item.text(2)
                    idproyecto = item.text(3)
                    nombrezona = item.parent().text(0)
                    edit_pluviometros = menu.addAction("Cambiar de Componente")
                    delete_pluviometros = menu.addAction("Eliminar Pluviómetros")
                    edit_pluviometros.triggered.connect(lambda: SubirPluviometros.cambiar_componente_pluviometros(idzona, idproyecto, treeWidget, "Pluviómetros", "5", "pluviometro", reiniciarvistas))
                    delete_pluviometros.triggered.connect(lambda: SubirPluviometros.eliminar_pluviometros(idproyecto, idzona, "Pluviómetros", "5", treeWidget, reiniciarvistas))
                elif tipo == "6": # Cotas Terreno
                    idzona = item.text(2)
                    idproyecto = item.text(3)
                    nombrezona = item.parent().text(0)
                    edit_terrenos = menu.addAction("Cambiar de Componente")
                    delete_terrenos = menu.addAction("Eliminar Cotas de Terreno")
                    edit_terrenos.triggered.connect(lambda: SubirCotasTerreno.cambiar_componente_terrenos(idzona, idproyecto, treeWidget, "Cotas de Terreno", "6", "terreno", reiniciarvistas))
                    delete_terrenos.triggered.connect(lambda: SubirCotasTerreno.eliminar_terrenos(idproyecto, idzona, "Cotas de Terreno", "6", treeWidget, reiniciarvistas))
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
                    delete_acelerografos.triggered.connect(lambda: SubirAcelerografos.eliminar_acelerografos(idproyecto, idzona, "Acelerógrafos", "8", treeWidget))
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
                elif tipo == "11": # Prismas de Baja
                    idzona = item.text(2)
                    idproyecto = item.text(3)
                    nombrezona = item.parent().text(0)
                    edit_prismasbaja = menu.addAction("Dar de Alta")
                    delete_prismasbaja = menu.addAction("Eliminar Prismas")
                    edit_prismasbaja.triggered.connect(lambda: SubirPrismas.dardealta_prismas(idzona, idproyecto, nombrezona, treeWidget, reiniciarvistas))
                    delete_prismasbaja.triggered.connect(lambda: SubirPrismas.eliminar_prismas(idzona, "Prismas de Baja", "11", treeWidget, reiniciarvistas))
            else:    
                if tipo == "prisma":
                    nombreprisma = item.text(0)
                    idinstrumento = item.text(2)
                    nombrezona = item.parent().parent().text(0)
                    idcomponente = item.parent().parent().text(2)
                    idproyecto = item.parent().parent().text(3)
                    darbaja_prisma = menu.addAction("Dar de Baja")
                    change_prisma = menu.addAction("Cambiar de Componente")
                    if EquiposDatos.validarAlgunHijoMarcado(item.parent()):
                        move_prisma = menu.addAction("Mover en Bloque")
                        move_prisma.triggered.connect(lambda: SubirPrismas.cambiar_componente_bloque_prisma(idproyecto, idcomponente, item.parent(), treeWidget, "Prismas", "1", "prisma", 1, reiniciarvistas))
                    edit_prisma = menu.addAction("Editar Prisma")
                    delete_prisma = menu.addAction("Eliminar Prisma")
                    darbaja_prisma.triggered.connect(lambda: SubirPrismas.dardebaja_prisma(main, idproyecto, idcomponente, nombreprisma, idinstrumento, nombrezona, treeWidget, reiniciarvistas, "DATOS"))
                    change_prisma.triggered.connect(lambda: SubirPrismas.cambiar_componente_prisma(idinstrumento, idcomponente, idproyecto, treeWidget, "Prismas", "1", "prisma", 1, reiniciarvistas))
                    edit_prisma.triggered.connect(lambda: SubirPrismas.editar_prisma(idproyecto, idcomponente, idinstrumento, nombreprisma, "Prismas", "prisma", treeWidget, reiniciarvistas))
                    delete_prisma.triggered.connect(lambda: SubirPrismas.eliminar_prisma(idinstrumento, nombreprisma, "Prismas", "prisma", treeWidget, reiniciarvistas))
                elif tipo == "inclinometro":
                    nombreinclino = item.text(0)
                    idinstrumento = item.text(2)
                    nombrezona = item.parent().parent().text(0)
                    idcomponente = item.parent().parent().text(2)
                    idproyecto = item.parent().parent().text(3)
                    edit_inclino = menu.addAction("Editar Inclinómetro")
                    if EquiposDatos.validarAlgunHijoMarcado(item.parent()):
                        move_inclino = menu.addAction("Cambiar de Componente")
                        move_inclino.triggered.connect(lambda: SubirInclinometros.cambiar_componente_bloque_inclinometro(idproyecto, idcomponente, item.parent(), treeWidget, "Inclinómetros", "2", "inclinometro", reiniciarvistas))
                    delete_inclino = menu.addAction("Eliminar Inclinómetro")
                    edit_inclino.triggered.connect(lambda: SubirInclinometros.actualizarInclinometro(idproyecto, idcomponente, idinstrumento, treeWidget, "Inclinómetros", "2", "inclinometro", "NO", reiniciarvistas))
                    delete_inclino.triggered.connect(lambda: SubirInclinometros.eliminar_inclinometro(idproyecto, idinstrumento, nombreinclino, "Inclinómetros", "inclinometro", treeWidget, reiniciarvistas))
                elif tipo == "piezometrocuerda":
                    nombrepiezo = item.text(0)
                    idinstrumento = item.text(2)
                    nombrezona = item.parent().parent().text(0)
                    idcomponente = item.parent().parent().text(2)
                    idproyecto = item.parent().parent().text(3)
                    edit_cuerda = menu.addAction("Editar Piezómetro")
                    if EquiposDatos.validarAlgunHijoMarcado(item.parent()):
                        move_cuerda = menu.addAction("Cambiar de Componente")
                        move_cuerda.triggered.connect(lambda: SubirPiezometros.cambiar_componente_bloque_cuerda(idproyecto, idcomponente, item.parent(), treeWidget, "Piezómetros Cuerda Vibrante", "3", "piezometrocuerda", reiniciarvistas))
                    delete_cuerda = menu.addAction("Eliminar Piezómetro")
                    edit_cuerda.triggered.connect(lambda: SubirPiezometros.actualizarPiezometroCuerda(idproyecto, idcomponente, idinstrumento, treeWidget, "Piezómetros Cuerda Vibrante", "3", "piezometrocuerda", reiniciarvistas))
                    delete_cuerda.triggered.connect(lambda: SubirPiezometros.eliminar_piezocuerda(idproyecto, idinstrumento, nombrepiezo, "Piezómetros Cuerda Vibrante", "piezometrocuerda", treeWidget, reiniciarvistas))
                elif tipo == "piezometromanual":
                    nombrepiezo = item.text(0)
                    idinstrumento = item.text(2)
                    nombrezona = item.parent().parent().text(0)
                    idcomponente = item.parent().parent().text(2)
                    idproyecto = item.parent().parent().text(3)
                    edit_piezomanual = menu.addAction("Editar Piezómetro")
                    if EquiposDatos.validarAlgunHijoMarcado(item.parent()):
                        move_casagrande = menu.addAction("Cambiar de Componente")
                        move_casagrande.triggered.connect(lambda: SubirPiezometros.cambiar_componente_bloque_casagrande(idproyecto, idcomponente, item.parent(), treeWidget, "Piezómetros Casagrande", "4", "piezometromanual", reiniciarvistas))
                    delete_piezomanual = menu.addAction("Eliminar Piezómetro")
                    edit_piezomanual.triggered.connect(lambda: SubirPiezometros.actualizarPiezometroManual(idproyecto, idcomponente, idinstrumento, treeWidget, "Piezómetros Casagrande", "4", "piezometromanual", reiniciarvistas))
                    delete_piezomanual.triggered.connect(lambda: SubirPiezometros.eliminar_piezomanual(idproyecto, idinstrumento, nombrepiezo, "Piezómetros Casagrande", "piezometromanual", treeWidget, reiniciarvistas))
                elif tipo == "pluviometro":
                    nombrepluvio = item.text(0)
                    idinstrumento = item.text(2)
                    nombrezona = item.parent().parent().text(0)
                    idcomponente = item.parent().parent().text(2)
                    idproyecto = item.parent().parent().text(3)
                    edit_pluviometro = menu.addAction("Editar Pluviómetro")
                    if EquiposDatos.validarAlgunHijoMarcado(item.parent()):
                        move_pluvio = menu.addAction("Cambiar de Componente")
                        move_pluvio.triggered.connect(lambda: SubirPluviometros.cambiar_componente_bloque_pluviometro(idproyecto, idcomponente, item.parent(), treeWidget, "Pluviómetros", "5", "pluviometro", reiniciarvistas))
                    delete_pluviometro = menu.addAction("Eliminar Pluviómetro")
                    edit_pluviometro.triggered.connect(lambda: SubirPluviometros.actualizarPluviometro(idproyecto, idcomponente, idinstrumento, treeWidget, "Pluviómetros", "5", "pluviometro", reiniciarvistas))
                    delete_pluviometro.triggered.connect(lambda: SubirPluviometros.eliminar_pluviometro(idproyecto, idinstrumento, nombrepluvio, "Pluviómetros", "pluviometro", treeWidget, reiniciarvistas))
                elif tipo == "terreno":
                    nombreterreno = item.text(0)
                    idinstrumento = item.text(2)
                    nombrezona = item.parent().parent().text(0)
                    idcomponente = item.parent().parent().text(2)
                    idproyecto = item.parent().parent().text(3)
                    edit_cotaterreno = menu.addAction("Editar Cota Terreno")
                    if EquiposDatos.validarAlgunHijoMarcado(item.parent()):
                        move_terreno = menu.addAction("Cambiar de Componente")
                        move_terreno.triggered.connect(lambda: SubirCotasTerreno.cambiar_componente_bloque_terreno(idproyecto, idcomponente, item.parent(), treeWidget, "Cotas de Terreno", "6", "terreno", reiniciarvistas))
                    delete_cotaterreno = menu.addAction("Eliminar Cota Terreno")
                    edit_cotaterreno.triggered.connect(lambda: SubirCotasTerreno.actualizarCotaTerreno(idproyecto, idcomponente, idinstrumento, treeWidget, "Cotas de Terreno", "6", "terreno", reiniciarvistas))
                    delete_cotaterreno.triggered.connect(lambda: SubirCotasTerreno.eliminar_cotaterreno(idproyecto, idinstrumento, nombreterreno, "Cotas de Terreno", "terreno", treeWidget, reiniciarvistas))
                elif tipo == "celda":
                    nombrecelda = item.text(0)
                    idinstrumento = item.text(2)
                    nombrezona = item.parent().parent().text(0)
                    idcomponente = item.parent().parent().text(2)
                    idproyecto = item.parent().parent().text(3)
                    edit_celda = menu.addAction("Editar Celda")
                    if EquiposDatos.validarAlgunHijoMarcado(item.parent()):
                        move_celda = menu.addAction("Cambiar de Componente")
                        move_celda.triggered.connect(lambda: SubirCeldas.cambiar_componente_bloque_celda(idproyecto, idcomponente, item.parent(), treeWidget, "Celdas de Asentamiento", "7", "celda", reiniciarvistas))
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
                    if EquiposDatos.validarAlgunHijoMarcado(item.parent()):
                        move_acelero = menu.addAction("Cambiar de Componente")
                        move_acelero.triggered.connect(lambda: SubirAcelerografos.cambiar_componente_bloque_acelerografo(idproyecto, idcomponente, item.parent(), treeWidget, "Acelerógrafos", "8", "acelerografo", reiniciarvistas))
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
                    if EquiposDatos.validarAlgunHijoMarcado(item.parent()):
                        move_sondaje = menu.addAction("Cambiar de Componente")
                        move_sondaje.triggered.connect(lambda: SubirTDR.cambiar_componente_bloque_sondajetdr(idproyecto, idcomponente, item.parent(), treeWidget, "TDR", "9", "sondajetdr", reiniciarvistas))
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
                    if EquiposDatos.validarAlgunHijoMarcado(item.parent()):
                        move_equipo = menu.addAction("Cambiar de Componente")
                        move_equipo.triggered.connect(lambda: RegistroEquipos.cambiar_componente_bloque_equipo(idproyecto, idcomponente, item.parent(), treeWidget, "Equipos Adicionales", "10", "adicional", reiniciarvistas))
                    delete_adicional = menu.addAction("Eliminar E. Adicional")
                    edit_adicional.triggered.connect(lambda: RegistroEquipos.actualizarEquipoAdicional(idproyecto, idcomponente, idinstrumento, treeWidget, "Equipos Adicionales", "10", "adicional", reiniciarvistas))
                    delete_adicional.triggered.connect(lambda: RegistroEquipos.eliminar_adicional(idproyecto, idinstrumento, nombreequipo, "Equipos Adicionales", "adicional", treeWidget, reiniciarvistas))
                elif tipo == "prismabaja":
                    nombreprisma = item.text(0)
                    idinstrumento = item.text(2)
                    nombrezona = item.parent().parent().text(0)
                    idcomponente = item.parent().parent().text(2)
                    idproyecto = item.parent().parent().text(3)
                    edit_prismabaja = menu.addAction("Dar de Alta")
                    change_prismabaja = menu.addAction("Cambiar de Componente")
                    if EquiposDatos.validarAlgunHijoMarcado(item.parent()):
                        move_prismabaja = menu.addAction("Cambiar de Componente")
                        move_prismabaja.triggered.connect(lambda: SubirPrismas.cambiar_componente_bloque_prisma(idproyecto, idcomponente, item.parent(), treeWidget, "Prismas de Baja", "11", "prismabaja", 0, reiniciarvistas))
                    delete_prismabaja = menu.addAction("Eliminar Prisma")
                    edit_prismabaja.triggered.connect(lambda: SubirPrismas.dardealta_prisma(idproyecto, idcomponente, nombreprisma, idinstrumento, nombrezona, treeWidget, reiniciarvistas))
                    change_prismabaja.triggered.connect(lambda: SubirPrismas.cambiar_componente_prisma(idinstrumento, idcomponente, idproyecto, treeWidget, "Prismas de Baja", "11", "prismabaja", 0, reiniciarvistas))
                    delete_prismabaja.triggered.connect(lambda: SubirPrismas.eliminar_prisma(idinstrumento, nombreprisma, "Prismas de Baja", "prismabaja", treeWidget, reiniciarvistas))
            menu.exec(treeWidget.mapToGlobal(point))
    
    def validarAlgunHijoMarcado(nodo):
        for i in range(nodo.childCount()):
            hijo = nodo.child(i)
            if hijo.checkState(0) == Qt.Checked:
                return True
        return False
    
    def validarMarcadoUnEquipoZona(datos, zona):
        respuesta = True
        if datos:
            equipos = datos.get(zona)
            if equipos:
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
                if tipos:
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
            EquiposDatos.marcardesmarcar_todos_hijos(hijo, estado)

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
                EquiposDatos.actualizar_estado_padre_hijos(nodo.parent())

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
            resultado_grupo = EquiposDatos.obtener_elementos_marcados_recursivo(grupo)
            if resultado_grupo:
                elementos_marcados.update(resultado_grupo)
        return elementos_marcados
    
    def obtener_elementos_marcados_recursivo(nodo):
        hijos_marcados = []
        if nodo.childCount() > 0:
            marcados = {}
            for i in range(nodo.childCount()):
                hijo = nodo.child(i)
                resultado_hijo = EquiposDatos.obtener_elementos_marcados_recursivo(hijo)
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
            return EquiposDatos.obtener_elementos_des_marcados_recursivo(nodo.parent())
        else:
            marcados = EquiposDatos.obtener_elementos_marcados_recursivo(nodo)
        return marcados
     
    def obtener_todos_elementos_arbol(tree_widget):
        elementos = {}
        for i in range(tree_widget.topLevelItemCount()):
            grupo = tree_widget.topLevelItem(i)
            resultado_grupo = EquiposDatos.obtener_elementos_arbol_recursivo(grupo)
            if resultado_grupo:
                elementos.update(resultado_grupo)
        return elementos
    
    def obtener_elementos_arbol_recursivo(nodo):
        hijos = []
        if nodo.childCount() > 0:
            marcados = {}
            for i in range(nodo.childCount()):
                hijo = nodo.child(i)
                resultado_hijo = EquiposDatos.obtener_elementos_arbol_recursivo(hijo)
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
   
    def inicializar_lista_datos(tree_widget, proyecto_id, proyecto_name):
        TreeCheckbox.limpiarArbolCheckboxes(tree_widget, proyecto_name)
        if proyecto_id:
            # LISTAR COMOPONENTES
            componentes = InterfazController.ctrlListarComponentesProyecto(proyecto_id)
            if componentes:
                for zona in componentes:
                    idzona = zona[0]
                    namezona = zona[2]
                    # LISTAR PRISMAS
                    prismas = InterfazController.ctrlListarPrismasComponente(idzona, 1)
                    if len(prismas) > 0:
                        TreeCheckbox.crearNuevoGrupoCheckboxesSimple(tree_widget, namezona, idzona, proyecto_id, "Prismas", "1", prismas, "prisma")
                    # LISTAR INCLINOMETROS
                    inclinometros = InterfazController.ctrlListarInclinometrosComponente(idzona, proyecto_id)
                    if inclinometros:
                        TreeCheckbox.crearNuevoGrupoCheckboxesSimple(tree_widget, namezona, idzona, proyecto_id, "Inclinómetros", "2", inclinometros, "inclinometro")
                    # LISTAR PIEZOMETROS CUERDA VIBRANTE
                    piezometroscuerda = InterfazController.ctrlListarPiezometrosCuerdaComponente(idzona, proyecto_id)
                    if piezometroscuerda:
                        TreeCheckbox.crearNuevoGrupoCheckboxesSimple(tree_widget, namezona, idzona, proyecto_id, "Piezómetros Cuerda Vibrante", "3", piezometroscuerda, "piezometrocuerda")
                    # LISTAR PIEZOMETROS MANUALES
                    piezometrosmanual = InterfazController.ctrlListarPiezometrosManualComponente(idzona, proyecto_id)
                    if piezometrosmanual:
                        TreeCheckbox.crearNuevoGrupoCheckboxesSimple(tree_widget, namezona, idzona, proyecto_id, "Piezómetros Casagrande", "4", piezometrosmanual, "piezometromanual")
                    # LISTAR PLUVIOMETROS
                    pluviometros = InterfazController.ctrlListarPluviometrosComponente(proyecto_id, idzona)
                    if pluviometros:
                        TreeCheckbox.crearNuevoGrupoCheckboxesSimple(tree_widget, namezona, idzona, proyecto_id, "Pluviómetros", "5", pluviometros, "pluviometro")
                    # LISTAR COTAS DE TERRENO
                    terrenos = InterfazController.ctrlListarCotasTerrenoComponente(proyecto_id, idzona)
                    if terrenos:
                        TreeCheckbox.crearNuevoGrupoCheckboxesSimple(tree_widget, namezona, idzona, proyecto_id, "Cotas de Terreno", "6", terrenos, "terreno")
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
                    # LISTAR PRISMAS DE BAJA
                    prismasbaja = InterfazController.ctrlListarPrismasComponente(idzona, 0)
                    if prismasbaja:
                        TreeCheckbox.crearNuevoGrupoCheckboxesSimple(tree_widget, namezona, idzona, proyecto_id, "Prismas de Baja", "11", prismasbaja, "prismabaja")
                    