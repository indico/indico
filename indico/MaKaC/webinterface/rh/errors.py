# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

import os

from werkzeug import secure_filename
from flask import request
from flask import send_from_directory

import MaKaC.webinterface.pages.errors as errors
from MaKaC.webinterface.rh.base import RH
from MaKaC.webinterface.mail import GenericMailer, GenericNotification

from indico.core.config import Config


class RHErrorReporting(RH):
    """
    Handles the reporting of errors to the Indico support.

    This handler is quite special as it has to handle the reporting of
    generic errors to the support of the application; any error can happen
    which means that even the DB could not be avilable so it has to use
    the minimal system resources possible in order to always be able to
    report errors.
    """

    def _checkParams(self, params):
        self._sendIt = "confirm" in params
        self._comments = ""
        if self._sendIt:
            self._comments = params.get("comments", "")
        self._userMail = params.get("userEmail", "")
        self._msg = params.get("reportMsg", "")

    def _sendReport(self):
        cfg = Config.getInstance()
        fromAddr = self._userMail
        toAddr = cfg.getSupportEmail()
        subject = "[Indico@%s] Error report" % cfg.getBaseURL()
        body = ["-"*20, "User Comments\n", "%s\n\n" % self._comments, "-"*20,
                "Error details\n", self._msg, "-" * 20]
        maildata = {"fromAddr": fromAddr, "toList": [toAddr], "subject": subject, "body": "\n".join(body)}
        GenericMailer.send(GenericNotification(maildata), skipQueue=True)

    def process(self, params):
        self._checkParams(params)
        if self._sendIt:
            self._sendReport()
            p = errors.WPReportErrorSummary(self)
            return p.display()
        else:
            p = errors.WPReportError(self)
            return p.display(userEmail=self._userMail, msg=self._msg)


class RHDownloadErrorReport(RH):
    """
    Allows error reports to be downloaded
    """

    def process(self, params):
        config = Config.getInstance()

        target_dir = os.path.join(
            config.getSharedTempDir(), 'reports',
            secure_filename(request.view_args['report_id']))

        return send_from_directory(
            target_dir, request.view_args['filename'],
            mimetype='text/plain', as_attachment=True)
