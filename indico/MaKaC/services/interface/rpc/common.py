from MaKaC.common.PickleJar import Retrieves
import sys
import traceback
from MaKaC.common.fossilize import Fossilizable, fossilizes
from MaKaC.fossils.error import ICausedErrorFossil

class CausedError(Exception, Fossilizable):
    fossilizes(ICausedErrorFossil)

    def __init__(self, code, message, inner=None, type=None):
        self.code = code
        self.message = message
        self.inner = inner
        self.type = type

    @Retrieves(['MaKaC.services.interface.rpc.common.CausedError',
                'MaKaC.services.interface.rpc.common.NoReportError',
                'MaKaC.services.interface.rpc.common.RequestError',
                'MaKaC.services.interface.rpc.common.ProcessError',
                'MaKaC.services.interface.rpc.common.ServiceError',
                'MaKaC.services.interface.rpc.common.PermissionError',
                'MaKaC.services.interface.rpc.common.HTMLSecurityError',
                'MaKaC.services.interface.rpc.common.ServiceAccessError',
                'MaKaC.services.interface.rpc.common.TimingNoReportError',
                'MaKaC.services.implementation.base.ExpectedParameterException',
                'MaKaC.services.implementation.base.EmptyParameterException',
                'MaKaC.plugins.Collaboration.base.CollaborationServiceException',
                'MaKaC.plugins.Collaboration.EVO.common.EVOServiceException',
                'MaKaC.plugins.Collaboration.RecordingRequest.common.RecordingRequestException',
                'MaKaC.plugins.Collaboration.CERNMCU.common.CERNMCUException'], 'message')
    def getMessage(self):
        return self.message

    @Retrieves(['MaKaC.services.interface.rpc.common.CausedError',
                'MaKaC.services.interface.rpc.common.NoReportError',
                'MaKaC.services.interface.rpc.common.RequestError',
                'MaKaC.services.interface.rpc.common.ProcessError',
                'MaKaC.services.interface.rpc.common.ServiceError',
                'MaKaC.services.interface.rpc.common.PermissionError',
                'MaKaC.services.interface.rpc.common.HTMLSecurityError',
                'MaKaC.services.interface.rpc.common.ServiceAccessError',
                'MaKaC.services.interface.rpc.common.TimingNoReportError',
                'MaKaC.services.implementation.base.ExpectedParameterException',
                'MaKaC.services.implementation.base.EmptyParameterException',
                'MaKaC.plugins.Collaboration.base.CollaborationServiceException',
                'MaKaC.plugins.Collaboration.EVO.common.EVOServiceException',
                'MaKaC.plugins.Collaboration.RecordingRequest.common.RecordingRequestException',
                'MaKaC.plugins.Collaboration.CERNMCU.common.CERNMCUException'], 'code')
    def getCode(self):
        return self.code

    @Retrieves(['MaKaC.services.interface.rpc.common.CausedError',
                'MaKaC.services.interface.rpc.common.NoReportError',
                'MaKaC.services.interface.rpc.common.RequestError',
                'MaKaC.services.interface.rpc.common.ProcessError',
                'MaKaC.services.interface.rpc.common.ServiceError',
                'MaKaC.services.interface.rpc.common.PermissionError',
                'MaKaC.services.interface.rpc.common.HTMLSecurityError',
                'MaKaC.services.interface.rpc.common.ServiceAccessError',
                'MaKaC.services.interface.rpc.common.TimingNoReportError',
                'MaKaC.services.implementation.base.ExpectedParameterException',
                'MaKaC.services.implementation.base.EmptyParameterException',
                'MaKaC.plugins.Collaboration.base.CollaborationServiceException',
                'MaKaC.plugins.Collaboration.EVO.common.EVOServiceException',
                'MaKaC.plugins.Collaboration.RecordingRequest.common.RecordingRequestException',
                'MaKaC.plugins.Collaboration.CERNMCU.common.CERNMCUException'], 'inner')
    def getInner(self):
        return self.inner

    @Retrieves(['MaKaC.services.interface.rpc.common.CausedError',
                'MaKaC.services.interface.rpc.common.NoReportError',
                'MaKaC.services.interface.rpc.common.RequestError',
                'MaKaC.services.interface.rpc.common.ProcessError',
                'MaKaC.services.interface.rpc.common.ServiceError',
                'MaKaC.services.interface.rpc.common.PermissionError',
                'MaKaC.services.interface.rpc.common.HTMLSecurityError',
                'MaKaC.services.interface.rpc.common.ServiceAccessError',
                'MaKaC.services.interface.rpc.common.TimingNoReportError',
                'MaKaC.services.implementation.base.ExpectedParameterException',
                'MaKaC.services.implementation.base.EmptyParameterException',
                'MaKaC.plugins.Collaboration.base.CollaborationServiceException',
                'MaKaC.plugins.Collaboration.EVO.common.EVOServiceException',
                'MaKaC.plugins.Collaboration.RecordingRequest.common.RecordingRequestException',
                'MaKaC.plugins.Collaboration.CERNMCU.common.CERNMCUException'], 'type')
    def getType(self):
        return self.type

    def __str__(self):
        if not self.inner:
            return "%s : %s (no inner exception)" % (self.code, self.message)
        else:
            if type(self.inner) is list:
                inner = "\r\n".join(self.inner)
            else:
                inner = self.inner
            return "%s : %s\r\n\r\nInner Exception:\r\n%s" % (self.code, self.message, inner)

class NoReportError(CausedError):

    def __init__(self, code, message, inner=None):
        CausedError.__init__(self, code, message, inner, "noReport")

class RequestError(CausedError):
    pass

class ProcessError(CausedError):

    def __init__(self, code, message):
        CausedError.__init__(self, code, message, inner = traceback.format_exception(*sys.exc_info()))

class ServiceError(CausedError):
    pass

class PermissionError(CausedError):
    pass

class HTMLSecurityError(CausedError):
    pass

class ServiceAccessError(NoReportError):
    pass

class TimingNoReportError(NoReportError):
    pass


class Warning(object):

    def __init__(self, title, content):
        self._title = title
        self._content = content

    @Retrieves(['MaKaC.services.interface.rpc.common.Warning'], 'title')
    def getTitle(self):
        return self._title

    @Retrieves(['MaKaC.services.interface.rpc.common.Warning'], 'content')
    def getProblems(self):
        return self._content

class ResultWithWarning(object):

    def __init__(self, result, warning):
        self._result = result
        self._warning = warning

    @Retrieves(['MaKaC.services.interface.rpc.common.ResultWithWarning'], 'result', isPicklableObject = True)
    def getResult(self):
        return self._result

    @Retrieves(['MaKaC.services.interface.rpc.common.ResultWithWarning'], 'warning', isPicklableObject = True)
    def getWarning(self):
        return self._warning

    @Retrieves(['MaKaC.services.interface.rpc.common.ResultWithWarning'], 'hasWarning')
    def hasWarning(self):
        return True
