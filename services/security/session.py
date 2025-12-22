from controllers.UsuarioController import UsuarioController

class Session:
    
    documento = None
    nombres = None
    apellidos = None
    iduser = None
    username = None
    idrol = None
    namerol = None
    estado = None

    @classmethod
    def login(cls, usuario, contraseña, idventa):
        #return True, "Ok"
        respuesta, datos = UsuarioController.ctrlComprobarUsuarioContraseña(usuario, contraseña, idventa)
        if respuesta is True and isinstance(datos.get("data"), dict):
            usuario = datos["data"]
            cls.documento = usuario['document_access']
            cls.nombres = usuario['name_access']
            cls.apellidos = usuario['lastname_access']
            cls.iduser = usuario['id_access']
            cls.username = usuario['user_access']
            cls.idrol = usuario['id_role']
            cls.namerol = usuario['name_role']
            cls.estado = usuario['state_access']
            return True, "Ok"
        else:
            return False, datos["error"]
    
    @classmethod
    def logout(cls):
        cls.documento = None
        cls.nombres = None
        cls.apellidos = None
        cls.iduser = None
        cls.username = None
        cls.idrol = None
        cls.namerol = None
        cls.estado = None

    @classmethod
    def get_username(cls):
        return cls.username
    
    @classmethod
    def get_iduser(cls):
        return cls.iduser
    
    @classmethod
    def get_idrole(cls):
        return cls.idrol
    
    @classmethod
    def get_nombres(cls):
        return cls.nombres + " " + cls.apellidos
    
    @classmethod
    def is_authenticated(cls):
        return cls.iduser is not None and cls.username is not None
