# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from io import BytesIO

import qrcode
from flask import json, render_template

from indico.core.config import config
from indico.core.db import db
from indico.core.oauth.models.applications import OAuthApplication, SystemAppType
from indico.modules.designer import PageOrientation, PageSize
from indico.modules.events.registration.controllers.management import RHManageRegFormBase
from indico.modules.events.registration.forms import TicketsForm
from indico.web.flask.util import send_file
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
        form = TicketsForm(obj=self.regform, regform=self.regform, event=self.event)
        if form.validate_on_submit():
            form.populate_obj(self.regform)
            db.session.flush()
            return jsonify_data(flash=False, tickets_enabled=self.regform.tickets_enabled)

        return jsonify_template('events/registration/management/regform_tickets.html', regform=self.regform, form=form)


class RHTicketConfigQRCodeImage(RHManageRegFormBase):
    """Display configuration QRCode."""

    def _process(self):
        # QRCode (Version 6 with error correction L can contain up to 106 bytes)
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=4,
            border=1
        )

        checkin_app = OAuthApplication.query.filter_by(system_app_type=SystemAppType.checkin).one()
        qr_data = {
            'event_id': self.event.id,
            'title': self.event.title,
            'regform_id': self.regform.id,
            'regform_title': self.regform.title,
            'date': self.event.start_dt.isoformat(),
            'version': 2,
            'server': {
                'base_url': config.BASE_URL,
                'client_id': checkin_app.client_id,
                'scope': 'registrants',
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
