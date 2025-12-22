from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
from PySide6.QtGui import QStandardItemModel, QColor
from PySide6.QtWidgets import (QMenu, QComboBox, QPushButton, QTableView, QDialog, QFormLayout, QLineEdit, QDialogButtonBox,
                            QMessageBox, QLabel)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from utils.common.alertas import mostrar_mensaje
from controllers.UsuarioController import UsuarioController

class CustomTableModel(QAbstractTableModel):
    def __init__(self, data, headers, colcolor=6, parent=None):
        super().__init__(parent)
        self._data = data
        self._headers = headers
        self.columna_color = colcolor
    
    # Devuelve los datos de la celda solicitada
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row = index.row()
        col = index.column()
        if role == Qt.DisplayRole:
            return str(self._data[row][col])
        if role == Qt.ForegroundRole and col == self.columna_color:
            if str(self._data[row][col]) == "Eliminado":
                return QColor("red")
            elif str(self._data[row][col]) == "Inhabilitado":
                return QColor("blue")
        return None
    
    # Número de filas por página
    def rowCount(self, parent=QModelIndex()):
        return len(self._data)
    
    # Número de columnas
    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)
    
    # Encabezados de las columnas
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self._headers[section]
            elif orientation == Qt.Vertical:
                return str(section + 1)
        return None
    
class UsuariosView:
    main = None
    idempresa = None
    idventa = None
    estadoPagina = True
    
    def inicializarVistaUsuarios(main):
        UsuariosView.main = main
        if UsuariosView.idempresa is None:
            empresa = UsuarioController.ctrlObtenerCodigoEmpresa()
            if empresa:
                UsuariosView.idempresa = empresa[0]
                UsuariosView.idventa = empresa[1]
        if UsuariosView.estadoPagina:
            btn_refrescar_tabla = UsuariosView.main.findChild(QPushButton, "btn_refrescar_usuarios")
            btn_refrescar_tabla.clicked.connect(UsuariosView.mostrarListaUsuarios)
            # Conectar el menú contextual al QTableView
            tablausers =  main.findChild(QTableView, "table_usuarios")
            tablausers.setContextMenuPolicy(Qt.CustomContextMenu)
            tablausers.customContextMenuRequested.connect(lambda position: UsuariosView.mostrarMenuTabla(tablausers, position))
            btnnuevousuario = UsuariosView.main.findChild(QPushButton, "btn_nuevo_usuario")
            btnnuevousuario.clicked.connect(UsuariosView.modalCrearNuevoUsuario)
            UsuariosView.estadoPagina = False
    
    def mostrarListaUsuarios():
        tabla =  UsuariosView.main.findChild(QTableView, "table_usuarios")
        if UsuariosView.idventa:
            respu, respuesta = UsuarioController.ctrlObtenerListaUsuarios(UsuariosView.idventa)
            if respu is True and "data" in respuesta:
                usuarios = respuesta["data"]
                datos = []
                for usuario in usuarios:
                    datos.append([usuario['document_access'], usuario['lastname_access'], usuario['name_access'],
                                  usuario['user_access'], usuario['name_role'], usuario['update_access'],
                                  usuario['state_access'], usuario['id_access']])
                headers = [
                    "Documento", "Apellidos", "Nombres", "Usuario", "Rol", "Último Logueo", "Estado", ""
                ]
                UsuariosView.llenarTablaData(tabla, headers, datos)
                tabla.setColumnHidden(7, True)
        else:
            UsuariosView.limpiarTablaData(tabla)
    
    def modalCrearNuevoUsuario():
        dialog = QDialog()
        dialog.setWindowTitle("Nuevo Usuario")
        layout = QFormLayout(dialog)
        # Campo documento
        documento_input = QLineEdit()
        documento_input.setText("")
        # Campo Nombres
        nombre_input = QLineEdit()
        nombre_input.setText("")
        # Campo Apellidos
        apellido_input = QLineEdit()
        apellido_input.setText("")
        # Campo usuario
        usuario_input = QLineEdit()
        usuario_input.setText("")
        # Campo contraseña
        contraseña_input = QLineEdit()
        contraseña_input.setText("")
        # Campo Rol
        rol_combo = QComboBox()
        rol_combo.addItem("Superusuario", 1)
        rol_combo.addItem("Administrador", 2)
        rol_combo.addItem("Visualizador", 3)
        # Añadir los campos al layout
        layout.addRow("Documento:", documento_input)
        layout.addRow("Nombres:", nombre_input)
        layout.addRow("Apellidos:", apellido_input)
        layout.addRow("Usuario:", usuario_input)
        layout.addRow("Contraseña:", contraseña_input)
        layout.addRow("Rol:", rol_combo)
        label_mensaje = QLabel("")
        label_mensaje.setAlignment(Qt.AlignCenter)
        label_mensaje.setStyleSheet("QLabel { color: red; }")
        layout.addRow(label_mensaje)
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        # Cambiar los textos a español
        button_box.button(QDialogButtonBox.Save).setText("Guardar")
        button_box.button(QDialogButtonBox.Cancel).setText("Cancelar")
        layout.addWidget(button_box)
        # Conectar los botones a las funciones correspondientes
        def guardarDatos():
            if UsuariosView.idempresa:
                documento = documento_input.text()
                nombres = nombre_input.text()
                apellidos = apellido_input.text()
                username = usuario_input.text()
                contraseña = contraseña_input.text()
                rol = rol_combo.currentData()
                if (documento != "" and len(documento) == 8 and documento.isdigit() and username != "" and len(username) >= 5 and
                    contraseña != "" and len(contraseña) >= 6):
                    if nombres != "" and apellidos != "" and rol != "":
                        respu, respuesta = UsuarioController.ctrlGuardarUsuario(documento, nombres, apellidos, username, contraseña, rol, UsuariosView.idventa)
                        if respu is True and "data" in respuesta:
                            dialog.reject()
                            UsuariosView.mostrarListaUsuarios()
                        else:
                            result = respuesta["error"]
                            label_mensaje.setText(result)
                    else:
                        label_mensaje.setText("Los datos están vacíos.")
                else:
                    label_mensaje.setText("El usuario y contraseña deben tener al menos 5 caracteres.")
            else:
                label_mensaje.setText("Error al obtener la empresa.")
        button_box.accepted.connect(guardarDatos)
        button_box.rejected.connect(dialog.reject)
        # Mostrar el diálogo
        dialog.setLayout(layout)
        dialog.exec()
    
    def reiniciarVistaDatos(main, proyecto_id, proyecto_name):
        UsuariosView.main = main
        UsuariosView.idempresa = proyecto_id
        UsuariosView.nameproyecto = proyecto_name
        UsuariosView.estadochecklist = True
        tabla =  UsuariosView.main.findChild(QTableView, "table_datos")
        UsuariosView.limpiarTablaData(tabla)
    
    # Función para manejar el menú contextual
    def mostrarMenuTabla(table, position):
        rolusuario = 1
        if rolusuario == 1:
            index = table.indexAt(position)
            if not index.isValid():
                return
            row = index.row()
            # Capturar los valores de la fila
            dni = table.model().data(table.model().index(row, 0), Qt.DisplayRole)
            apellido = table.model().data(table.model().index(row, 1), Qt.DisplayRole)
            nombre = table.model().data(table.model().index(row, 2), Qt.DisplayRole)
            usuario = table.model().data(table.model().index(row, 3), Qt.DisplayRole)
            rol = table.model().data(table.model().index(row, 4), Qt.DisplayRole)
            estado = table.model().data(table.model().index(row, 6), Qt.DisplayRole)
            idusuario = table.model().data(table.model().index(row, 7), Qt.DisplayRole)
            UsuariosView.generarMenuTabla(position, dni, apellido, nombre, usuario, rol, estado, idusuario, table)
    
    # MENU TABLA PRISMAS    
    def generarMenuTabla(position, dni, apellido, nombre, usuario, rol, estado, idusuario, table):
        # Crear menú contextual
        menu = QMenu()
        edit_action = QAction("Editar Usuario", table)
        change_action = QAction("Cambiar Contraseña", table)
        delete_action = QAction("Eliminar Usuario", table)
        # Conectar las acciones con los valores de la fila
        edit_action.triggered.connect(lambda: UsuariosView.editarDatosUsuario(idusuario, dni, apellido, nombre, usuario, rol, estado))
        change_action.triggered.connect(lambda: UsuariosView.cambiarContraseñaUsuario(idusuario, usuario))
        delete_action.triggered.connect(lambda: UsuariosView.eliminarDatosUsuario(idusuario, usuario))
        # Añadir las acciones al menú
        menu.addAction(edit_action)
        menu.addAction(change_action)
        menu.addAction(delete_action)
        # Mostrar menú contextual en la posición del clic
        menu.exec(table.viewport().mapToGlobal(position))
    
    def editarDatosUsuario(idusuario, dni, apellido, nombre, usuario, rol, estado):
        dialog = QDialog()
        dialog.setWindowTitle("Editar Usuario")
        layout = QFormLayout(dialog)
        # Campo documento
        documento_input = QLineEdit()
        documento_input.setText(dni)
        # Campo Nombres
        nombre_input = QLineEdit()
        nombre_input.setText(nombre)
        # Campo Apellidos
        apellido_input = QLineEdit()
        apellido_input.setText(apellido)
        # Campo usuario
        usuario_input = QLineEdit()
        usuario_input.setText(usuario)
        # Campo Rol
        rol_combo = QComboBox()
        rol_combo.addItem("Superusuario", 1)
        rol_combo.addItem("Administrador", 2)
        rol_combo.addItem("Visualizador", 3)
        if rol == "Superusuario":
            rol_combo.setCurrentIndex(0)
        elif rol == "Administrador":
            rol_combo.setCurrentIndex(1)
        else:
            rol_combo.setCurrentIndex(2)
        # Campo Estado
        estado_combo = QComboBox()
        estado_combo.addItem("Habilitado", 1)
        estado_combo.addItem("Inhabilitado", 0)
        estado_combo.addItem("Eliminado", 2)
        if estado == "Habilitado":
            estado_combo.setCurrentIndex(0)
        elif estado == "Inhabilitado":
            estado_combo.setCurrentIndex(1)
        else:
            estado_combo.setCurrentIndex(2)
        # Añadir los campos al layout
        layout.addRow("Documento:", documento_input)
        layout.addRow("Nombres:", nombre_input)
        layout.addRow("Apellidos:", apellido_input)
        layout.addRow("Usuario:", usuario_input)
        layout.addRow("Rol:", rol_combo)
        layout.addRow("Estado:", estado_combo)
        label_mensaje = QLabel("")
        label_mensaje.setAlignment(Qt.AlignCenter)
        label_mensaje.setStyleSheet("QLabel { color: red; }")
        layout.addRow(label_mensaje)
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        # Cambiar los textos a español
        button_box.button(QDialogButtonBox.Save).setText("Guardar")
        button_box.button(QDialogButtonBox.Cancel).setText("Cancelar")
        layout.addWidget(button_box)
        # Conectar los botones a las funciones correspondientes
        def actualizarDatos():
            if idusuario != "" and idusuario is not None:
                docuedit = documento_input.text()
                nombredit = nombre_input.text()
                apelledit = apellido_input.text()
                useredit = usuario_input.text()
                roledit = rol_combo.currentData()
                estaedit = estado_combo.currentData()
                if docuedit != "" and len(docuedit) == 8 and docuedit.isdigit() and useredit != "" and len(useredit) >= 5:
                    if estaedit != "" and nombredit != "" and apelledit != "" and roledit != "":
                        respu, respuesta = UsuarioController.ctrlActualizarUsuario(docuedit, nombredit, apelledit, useredit, roledit, estaedit, idusuario)
                        if respu is True and "data" in respuesta:
                            dialog.reject()
                            UsuariosView.mostrarListaUsuarios()
                        else:
                            result = respuesta["error"]
                            label_mensaje.setText(result)
                    else:
                        label_mensaje.setText("Los datos están vacíos.")
                else:
                    label_mensaje.setText("El usuario debe tener al menos 5 caracteres.")
            else:
                label_mensaje.setText("Error al obtener el código de usuario.")
        button_box.accepted.connect(actualizarDatos)
        button_box.rejected.connect(dialog.reject)
        # Mostrar el diálogo
        dialog.setLayout(layout)
        dialog.exec()
    
    def cambiarContraseñaUsuario(idusuario, usuario):
        dialog = QDialog()
        dialog.setWindowTitle("Cambiar Contraseña Usuario")
        layout = QFormLayout(dialog)
        # Campo usuario
        usuario_input = QLineEdit()
        usuario_input.setText(usuario)
        usuario_input.setReadOnly(True)
        # Campo contraseña
        contraseña_input = QLineEdit()
        contraseña_input.setText("")
        # Añadir los campos al layout
        layout.addRow("Usuario:", usuario_input)
        layout.addRow("Contraseña:", contraseña_input)
        label_mensaje = QLabel("")
        label_mensaje.setAlignment(Qt.AlignCenter)
        label_mensaje.setStyleSheet("QLabel { color: red; }")
        layout.addRow(label_mensaje)
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        # Cambiar los textos a español
        button_box.button(QDialogButtonBox.Save).setText("Guardar")
        button_box.button(QDialogButtonBox.Cancel).setText("Cancelar")
        layout.addWidget(button_box)
        # Conectar los botones a las funciones correspondientes
        def actualizarDatos():
            if idusuario != "" and idusuario is not None:
                nuevapass = contraseña_input.text()
                if nuevapass != "" and len(nuevapass) >= 6:
                    respu, respuesta = UsuarioController.ctrlCambiarContraseñaUsuario(nuevapass, idusuario)
                    if respu is True and "data" in respuesta:
                        dialog.reject()
                    else:
                        result = respuesta["error"]
                        label_mensaje.setText(result)
                else:
                    label_mensaje.setText("El usuario y contraseña deben tener al menos 5 caracteres.")
            else:
                label_mensaje.setText("Error al obtener el código de usuario.")
        button_box.accepted.connect(actualizarDatos)
        button_box.rejected.connect(dialog.reject)
        # Mostrar el diálogo
        dialog.setLayout(layout)
        dialog.exec()
    
    def eliminarDatosUsuario(idusuario, usuario):
        dlg = QMessageBox()
        dlg.setWindowTitle("Eliminar Usuario")
        dlg.setText(f"¿Desea eliminar el usuario '{usuario}'?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.setIcon(QMessageBox.Question)
        result = dlg.exec()
        if result == QMessageBox.Yes:
            respu, respuesta = UsuarioController.ctrlCambiarEstadoUsuario(2, idusuario)
            if respu is True and "data" in respuesta:
                UsuariosView.mostrarListaUsuarios()
            else:
                result = respuesta["error"]
                mostrar_mensaje("Eliminar Usuario", result, "advertencia")
    
    def llenarTablaData(tabla, headers, data):
        tabla.setModel(None)
        model = CustomTableModel(data, headers)
        tabla.setModel(model)
        # Ajustar automáticamente el tamaño de las columnas según el contenido
        tabla.resizeColumnsToContents()
        tabla.resizeRowsToContents()
    
    def limpiarTablaData(tabla):
        model = QStandardItemModel()
        tabla.setModel(model)
    