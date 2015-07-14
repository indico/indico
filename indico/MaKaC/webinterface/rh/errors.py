# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

import json
import os
from pprint import pformat


from flask import request, send_from_directory
from werkzeug.utils import secure_filename

from indico.web.flask.templating import get_template_module
from indico.core.notifications import make_email, send_email
from MaKaC.webinterface.pages import errors
from MaKaC.webinterface.rh.base import RH

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
            self._comments = params.get("comments", "").strip()
        self._userMail = params.get("userEmail", "")
        self._msg = params.get("reportMsg", "{}")

    def _sendReport(self):
        cfg = Config.getInstance()
        data = json.loads(self._msg)
        template = get_template_module('emails/error_report.txt', comment=self._comments, traceback=data['traceback'],
                                       request_info=pformat(data['request_info']))
        send_email(make_email(cfg.getSupportEmail(), reply_address=self._userMail, template=template), skip_queue=True)

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
