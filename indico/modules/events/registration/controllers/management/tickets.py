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
from flask import json, render_template
from werkzeug.exceptions import Forbidden, NotFound

from indico.core import signals
from indico.core.config import Config
from indico.core.db import db
from indico.modules.designer import PageOrientation, PageSize
from indico.modules.designer.util import get_default_template_on_category
from indico.modules.events.registration.badges import RegistrantsListToBadgesPDF, RegistrantsListToBadgesPDFFoldable
from indico.modules.events.registration.controllers.display import RHRegistrationFormRegistrationBase
from indico.modules.events.registration.controllers.management import RHManageRegFormBase
from indico.modules.events.registration.forms import TicketsForm
from indico.modules.events.registration.models.registrations import RegistrationState
from indico.modules.oauth.models.applications import OAuthApplication, SystemAppType
from indico.web.flask.util import secure_filename, send_file, url_for
from indico.web.util import jsonify_data, jsonify_template


DEFAULT_TICKET_PRINTING_SETTINGS = {
    'top_margin': 0,
    'bottom_margin': 0,
    'left_margin': 0,
    'right_margin': 0,
    'margin_columns': 0,
    'margin_rows': 0.0,
    'page_size': PageSize.A4,
    'page_orientation': PageOrientation.portrait,
    'dashed_border': False,
    'page_layout': None
}


class RHRegistrationFormTickets(RHManageRegFormBase):
    """Display and modify ticket settings."""

    def _process(self):
        form = TicketsForm(obj=self.regform, event=self.event_new)
        if form.validate_on_submit():
            form.populate_obj(self.regform)
            db.session.flush()
            return jsonify_data(flash=False, tickets_enabled=self.regform.tickets_enabled)

        return jsonify_template('events/registration/management/regform_tickets.html', regform=self.regform, form=form)


def generate_ticket(registration):
    template = (registration.registration_form.ticket_template or
                get_default_template_on_category(registration.event_new.category))
    signals.event.designer.print_badge_template.send(template, regform=registration.registration_form)
    pdf_class = RegistrantsListToBadgesPDFFoldable if template.backside_template else RegistrantsListToBadgesPDF
    pdf = pdf_class(template, DEFAULT_TICKET_PRINTING_SETTINGS, registration.event_new, [registration.id])
    return pdf.get_pdf()


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

        checkin_app = OAuthApplication.find_one(system_app_type=SystemAppType.checkin)
        qr_data = {
            "event_id": self.event_new.id,
            "title": self.event_new.title,
            "date": self.event_new.start_dt.isoformat(),
            "version": 1,
            "server": {
                "base_url": config.getBaseURL(),
                "consumer_key": checkin_app.client_id,
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
