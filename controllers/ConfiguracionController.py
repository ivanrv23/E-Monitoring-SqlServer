from models.ConfiguracionModel import ConfiguracionModel

class ConfiguracionController:
    
    def ctrlActualizarConfiguracionEjes(idproyecto, modulo, tipo, valejemin, valejemax, valinterpri, valintersecu, valinterdias, valrangolluvia, valintervalolluvia):
        respuesta = ConfiguracionModel.mdlActualizarConfiguracionEjes(idproyecto, modulo, tipo, valejemin, valejemax, valinterpri, valintersecu, valinterdias, valrangolluvia, valintervalolluvia)
        return respuesta
    
    def ctrlActualizarConfiguracionEjesTDR(idproyecto, minejex, maxejex, xprimario, xsecundario, minejey, maxejey, yprimario, ysecundario):
        respuesta = ConfiguracionModel.mdlActualizarConfiguracionEjesTDR(idproyecto, minejex, maxejex, xprimario, xsecundario, minejey, maxejey, yprimario, ysecundario)
        return respuesta
    
    def ctrlObtenerConfiguracionEje(idproyecto, modulo, tipo):
        respuesta = ConfiguracionModel.mdlObtenerConfiguracionEje(idproyecto, modulo, tipo)
        return respuesta
    
    def ctrlObtenerConfiguracionEjeTDR(idproyecto):
        respuesta = ConfiguracionModel.mdlObtenerConfiguracionEjeTDR(idproyecto)
        return respuesta
    
    def ctrlActualizarComponente(nombre, idcomponente):
        respuesta = ConfiguracionModel.mdlActualizarComponente(nombre, idcomponente)
        return respuesta
    
    def ctrlTraerEstiloEquipoGrafica(idproyecto, idinstrumento, tipoinstru):
        respuesta = ConfiguracionModel.mdlTraerEstiloEquipoGrafica(idproyecto, idinstrumento, tipoinstru)
        return respuesta
    
    def ctrlAnularEstiloEquipoGrafica(idproyecto, idinstrumento, tipoinstru):
        respuesta = ConfiguracionModel.mdlAnularEstiloEquipoGrafica(idproyecto, idinstrumento, tipoinstru)
        return respuesta
    
    def ctrlGuardarEstiloEquipoGrafica(idproyecto, idinstrumento, tipolinea, grosorlinea, colorlinea, tipoinstru):
        respuesta = ConfiguracionModel.mdlGuardarEstiloEquipoGrafica(idproyecto, idinstrumento, tipolinea, grosorlinea, colorlinea, tipoinstru)
        return respuesta
    
    def ctrlListarConfiguracionVisor(idproyecto):
        respuesta = ConfiguracionModel.mdlListarConfiguracionVisor(idproyecto)
        return respuesta
    
    def ctrlRegistrarActualizarAjustesVisor(datos, existe):
        respuesta = ConfiguracionModel.mdlRegistrarActualizarAjustesVisor(datos, existe)
        return respuesta
    