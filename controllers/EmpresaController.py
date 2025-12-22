from models.EmpresaModel import EmpresaModel

class EmpresaController:
    
    def ctrlObtenerDatosEmpresa():
        empresa = EmpresaModel.mdlObtenerDatosEmpresa()
        licencia = EmpresaModel.mdlObtenerDatosLicencia()
        return empresa, licencia
    
    def ctrlObtenerDatosConfiguracionSoftware():
        respuesta = EmpresaModel.mdlObtenerDatosConfiguracionSoftware()
        return respuesta
    
    def ctrlObtenerDatosConfiguracionEmpresa():
        respuesta = EmpresaModel.mdlObtenerDatosConfiguracionEmpresa()
        return respuesta
    
    def ctrlObtenerDatosConfiguracionResponsable(proyectoid):
        # Pasamos los datos del formulario al modelo
        respuesta = EmpresaModel.mdlObtenerDatosConfiguracionResponsable(proyectoid)
        return respuesta
    
    def ctrlObtenerResponsables():
        # Pasamos los datos del formulario al modelo
        respuesta = EmpresaModel.mdlObtenerResponsables()
        return respuesta
    
    def ctrlRegistrarActualizarInformacionEmpresa(datos):
        respuesta = EmpresaModel.mdlRegistrarActualizarInformacionEmpresa(datos)
        return respuesta
    
    def ctrlRegistrarResponsableEmpresa(datos, proyectoid):
        respuesta = EmpresaModel.mdlRegistrarResponsableEmpresa(datos, proyectoid)
        return respuesta
    
    def ctrlListarResponsablesFirma():
        respuesta = EmpresaModel.mdlListarResponsablesFirma()
        return respuesta
    
    def ctrlGuardarNuevoResponsable(responsable, supervision, comentario, firma):
        respuesta = EmpresaModel.mdlGuardarNuevoResponsable(responsable, supervision, comentario, firma)
        return respuesta
    
    def ctrlEliminarFirmaResponsable(id):
        respuesta = EmpresaModel.mdlEliminarFirmaResponsable(id)
        return respuesta
    
    def ctrlRegistrarActualizarAjustesEmpresa(datos):
        respuesta = EmpresaModel.mdlRegistrarActualizarAjustesEmpresa(datos)
        return respuesta
    
    def ctrlRegistrarActualizarAjustesSoftware(datos):
        respuesta = EmpresaModel.mdlRegistrarActualizarAjustesSoftware(datos)
        return respuesta
    