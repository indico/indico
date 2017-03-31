# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from pprint import pformat

from werkzeug.urls import url_parse

from indico.core.config import Config
from indico.core.logger import Logger

from indico.legacy.common.mail import GenericMailer
from indico.legacy.errors import MaKaCError
from indico.legacy.services.implementation.base import ServiceBase
from indico.legacy.webinterface.mail import GenericNotification


class SendErrorReport(ServiceBase):
    """
    This service sends an error report to the indico support e-mail
    """

    CHECK_HTML = False

    def _sendReport( self ):
        cfg = Config.getInstance()

        # if no e-mail address was specified,
        # add a default one
        if self._userMail:
            fromAddr = self._userMail
        else:
            fromAddr = 'indico-reports@example.org'

        toAddr = Config.getInstance().getSupportEmail()
        Logger.get('errorReport').debug('mailing %s' % toAddr)
        subject = "[Indico@{}] Error report".format(url_parse(cfg.getBaseURL()).netloc)

        request_info = self._requestInfo or ''
        if isinstance(request_info, (dict, list)):
            request_info = pformat(request_info)

        # build the message body
        body = [
            "-" * 20,
            "Error details\n",
            str(self._code),
            self._message,
            "Inner error: " + str(self._inner),
            request_info,
            "-" * 20
        ]
        maildata = {"fromAddr": fromAddr, "toList": [toAddr], "subject": subject, "body": "\n".join(body)}
        GenericMailer.send(GenericNotification(maildata))

    def _checkParams(self):
        params = self._params or {}  # if params is not specified it's an empty list
        self._userMail = params.get('userMail', '')
        self._code = params.get('code', '')
        self._message = params.get('message', '')
        inner = params.get('inner', '')
        self._inner = '\n'.join(inner) if isinstance(inner, list) else inner
        self._requestInfo = params.get('requestInfo')

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
