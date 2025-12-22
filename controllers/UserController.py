from models.UserModel import UserModel
from services.security.encriptacion import Encriptacion

class UserController:
    
    def ctrlObtenerInfoLicencia():
        respuesta = UserModel.mdlObtenerInfoLicencia()
        if respuesta:
            datos = (
                respuesta[7],
                Encriptacion.decrypt(respuesta[1]),
                Encriptacion.decrypt(respuesta[3])
            )
            return datos
        else:
            return None