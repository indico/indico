from MaKaC.services.implementation.base import ParameterManager, ServiceBase
from MaKaC.webinterface.mail import GenericMailer, GenericNotification
from MaKaC.errors import MaKaCError

from MaKaC.common import Config
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.common.logger import Logger

class SendErrorReport(ServiceBase):
    """
    This service sends an error report to the indico support e-mail
    """

    def _sendReport( self ):
        info = HelperMaKaCInfo().getMaKaCInfoInstance()
        cfg = Config.getInstance()

        # if no e-mail address was specified,
        # add a default one
        if self._userMail:
            fromAddr = self._userMail
        else:
            fromAddr = 'indico-reports@example.org'

        toAddr = info.getSupportEmail()

        Logger.get('errorReport').debug('mailing %s' % toAddr)

        subject = "[Indico@%s] Error report"%cfg.getBaseURL()

        # build the message body
        body = ["-"*20, "Error details\n", self._code, self._message, "Inner error: " + str(self._inner), str(self._requestInfo), "-"*20 ]
        maildata = { "fromAddr": fromAddr, "toList": [toAddr], "subject": subject, "body": "\n".join( body ) }

        # send it
        GenericMailer.send(GenericNotification(maildata))


    def _checkParams(self):
        pManager = ParameterManager(self._params)
        self._userMail = pManager.extract("userMail", pType=str, allowEmpty=True)
        self._code = pManager.extract("code", pType=str)
        self._message = pManager.extract("message", pType=str)
        self._inner = pManager.extract("inner", pType=str, allowEmpty=True)
        self._requestInfo = pManager.extract("requestInfo", pType=dict)

    def _getAnswer(self):

        # Send a mail to the support
        try:
            self._sendReport()
            # TODO: maybe return an identifier for a 'ticket'?
            return 'OK'
        except MaKaCError, e:
            Logger.get('errorReport').error(e)
            # error during sending report: maybe there's
            # no support address, or we couldn't connect to STMP server...
            return False

