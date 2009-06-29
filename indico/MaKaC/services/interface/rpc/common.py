from MaKaC.common.PickleJar import Retrieves

class CausedError(Exception):
    def __init__(self, code, message, inner=None):
        self.code = code
        self.message = message
        self.inner = inner

    @Retrieves(['MaKaC.services.interface.rpc.common.CausedError',
                'MaKaC.services.interface.rpc.common.RequestError',
                'MaKaC.services.interface.rpc.common.ProcessError',
                'MaKaC.services.interface.rpc.common.ServiceError',
                'MaKaC.services.interface.rpc.common.PermissionError',
                'MaKaC.services.interface.rpc.common.HTMLSecurityError',
                'MaKaC.services.interface.rpc.common.ServiceAccessError',
                'MaKaC.services.implementation.base.ExpectedParameterException',
                'MaKaC.services.implementation.base.EmptyParameterException',
                'MaKaC.plugins.Collaboration.base.CollaborationServiceException',
                'MaKaC.plugins.Collaboration.EVO.common.EVOServiceException',
                'MaKaC.plugins.Collaboration.RecordingRequest.common.RecordingRequestException',
                'MaKaC.plugins.Collaboration.CERNMCU.common.CERNMCUException'], 'message')
    def getMessage(self):
        return self.message

    @Retrieves(['MaKaC.services.interface.rpc.common.CausedError',
                'MaKaC.services.interface.rpc.common.RequestError',
                'MaKaC.services.interface.rpc.common.ProcessError',
                'MaKaC.services.interface.rpc.common.ServiceError',
                'MaKaC.services.interface.rpc.common.PermissionError',
                'MaKaC.services.interface.rpc.common.HTMLSecurityError',
                'MaKaC.services.interface.rpc.common.ServiceAccessError',
                'MaKaC.services.implementation.base.ExpectedParameterException',
                'MaKaC.services.implementation.base.EmptyParameterException',
                'MaKaC.plugins.Collaboration.base.CollaborationServiceException',
                'MaKaC.plugins.Collaboration.EVO.common.EVOServiceException',
                'MaKaC.plugins.Collaboration.RecordingRequest.common.RecordingRequestException',
                'MaKaC.plugins.Collaboration.CERNMCU.common.CERNMCUException'], 'code')
    def getCode(self):
        return self.code

    @Retrieves(['MaKaC.services.interface.rpc.common.CausedError',
                'MaKaC.services.interface.rpc.common.RequestError',
                'MaKaC.services.interface.rpc.common.ProcessError',
                'MaKaC.services.interface.rpc.common.ServiceError',
                'MaKaC.services.interface.rpc.common.PermissionError',
                'MaKaC.services.interface.rpc.common.HTMLSecurityError',
                'MaKaC.services.interface.rpc.common.ServiceAccessError',
                'MaKaC.services.implementation.base.ExpectedParameterException',
                'MaKaC.services.implementation.base.EmptyParameterException',
                'MaKaC.plugins.Collaboration.base.CollaborationServiceException',
                'MaKaC.plugins.Collaboration.EVO.common.EVOServiceException',
                'MaKaC.plugins.Collaboration.RecordingRequest.common.RecordingRequestException',
                'MaKaC.plugins.Collaboration.CERNMCU.common.CERNMCUException'], 'inner')
    def getInner(self):
        return self.inner

    def __str__(self):       
        return "%s : %s \r\n %s" % (self.code, self.message, str(self.inner))
    

class RequestError(CausedError):
    pass

class ProcessError(CausedError):
    pass

class ServiceError(CausedError):
    pass

class PermissionError(CausedError):
    pass

class ServiceAccessError(CausedError):
    pass

class HTMLSecurityError(CausedError):
    pass
