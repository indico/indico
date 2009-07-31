from MaKaC.webinterface import session as sessionModule
from MaKaC.common.logger import Logger

from MaKaC.services.implementation.base import ServiceBase

class MessagingBase(ServiceBase):

    def _checkParams(self):
        pass

class MessagingAuthenticate(MessagingBase):

    def _checkParams(self):
        MessagingBase._checkParams(self)
        self._username = self._params.get("username")
        self._digest = self._params.get("digest")

    def _getAnswer(self):

        sManager = sessionModule.getSessionManager()
        session = sManager.get(self._digest, None)

        # TODO: replace with code that handles cookie revocation, etc
        if (session and
            session.getUser() and
            session.getUser().getId() == self._username):
            Logger.get('messaging').debug("Session for user %s confirmed for MAKACSESSION %s" % (session.getUser().getId(), session.getId()))
            return "OK"
        else:
            raise ServiceError()


methodMap = {
    "authenticate": MessagingAuthenticate
    }

