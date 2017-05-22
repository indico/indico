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

from __future__ import unicode_literals

from io import BytesIO

import qrcode
from flask import flash, json, render_template
from werkzeug.exceptions import Forbidden, NotFound

from indico.core.config import Config
from indico.core.db import db
from indico.modules.events.registration.controllers.display import RHRegistrationFormRegistrationBase
from indico.modules.events.registration.controllers.management import RHManageRegFormBase
from indico.modules.events.registration.forms import TicketsForm
from indico.modules.events.registration.models.registrations import RegistrationState
from indico.modules.oauth.models.applications import OAuthApplication
from indico.util.date_time import format_date
from indico.util.i18n import _
from indico.web.flask.util import url_for, send_file, secure_filename
from indico.web.util import jsonify_data, jsonify_template

from indico.legacy.pdfinterface.conference import TicketToPDF


class RHRegistrationFormTickets(RHManageRegFormBase):
    """Display and modify ticket settings."""

    def _check_ticket_app_enabled(self):
        config = Config.getInstance()
        checkin_app_client_id = config.getCheckinAppClientId()

        if checkin_app_client_id is None:
            flash(_("indico-checkin client_id is not defined in the Indico configuration"), 'warning')
            return False

        checkin_app = OAuthApplication.find_first(client_id=checkin_app_client_id)
        if checkin_app is None:
            flash(_("indico-checkin is not registered as an OAuth application with client_id {}")
                  .format(checkin_app_client_id), 'warning')
            return False
        return True

    def _process(self):
        form = TicketsForm(obj=self.regform)
        if form.validate_on_submit():
            form.populate_obj(self.regform)
            db.session.flush()
            return jsonify_data(flash=False, tickets_enabled=self.regform.tickets_enabled)

        return jsonify_template('events/registration/management/regform_tickets.html',
                                regform=self.regform, form=form, can_enable_tickets=self._check_ticket_app_enabled())


def generate_ticket(registration):
    pdf = TicketToPDF(registration.registration_form.event_new, registration)
    return BytesIO(pdf.getPDFBin())


class RHTicketDownload(RHRegistrationFormRegistrationBase):
    """Generate ticket for a given registration"""

    def _checkParams(self, params):
        RHRegistrationFormRegistrationBase._checkParams(self, params)
        if not self.registration:
            raise NotFound

    def _checkProtection(self):
        RHRegistrationFormRegistrationBase._checkProtection(self)
        if self.registration.state != RegistrationState.complete:
            raise Forbidden
        if not self.regform.tickets_enabled:
            raise Forbidden
        if not self.regform.ticket_on_event_page and not self.regform.ticket_on_summary_page:
            raise Forbidden

    def _process(self):
        filename = secure_filename('{}-Ticket.pdf'.format(self.event_new.title), 'ticket.pdf')
        return send_file(filename, generate_ticket(self.registration), 'application/pdf')


class RHTicketConfigQRCodeImage(RHManageRegFormBase):
    """Display configuration QRCode."""

    def _process(self):
        config = Config.getInstance()

        # QRCode (Version 6 with error correction L can contain up to 106 bytes)
        qr = qrcode.QRCode(
            version=6,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=4,
            border=1
        )

        checkin_app_client_id = config.getCheckinAppClientId()
        checkin_app = OAuthApplication.find_first(client_id=checkin_app_client_id)

        qr_data = {
            "event_id": self.event_new.id,
            "title": self.event_new.title,
            "date": format_date(self.event_new.start_dt_local),  # XXX: switch to utc+isoformat?
            "server": {
                "baseUrl": config.getBaseURL(),
                "consumerKey": checkin_app.client_id,
                "auth_url": url_for('oauth.oauth_authorize', _external=True),
                "token_url": url_for('oauth.oauth_token', _external=True)
            }
        }
        json_qr_data = json.dumps(qr_data)
        qr.add_data(json_qr_data)
        qr.make(fit=True)
        qr_img = qr.make_image()

        output = BytesIO()
        qr_img.save(output)
        output.seek(0)

        return send_file('config.png', output, 'image/png')


class RHTicketConfigQRCode(RHManageRegFormBase):
    def _process(self):
        return render_template('events/registration/management/regform_qr_code.html', regform=self.regform)
