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

from __future__ import unicode_literals

from io import BytesIO

from flask import redirect
from werkzeug.exceptions import Forbidden

from indico.core.db import db
from indico.modules.events.registration.controllers.display import RHRegistrationFormRegistrationBase
from indico.modules.events.registration.controllers.management import RHManageRegFormBase
from indico.modules.events.registration.forms import TicketsForm
from indico.modules.events.registration.models.registrations import RegistrationState
from indico.modules.events.registration.views import WPManageRegistration
from indico.web.flask.util import url_for, send_file, secure_filename
from MaKaC.PDFinterface.conference import TicketToPDF


class RHRegistrationFormTickets(RHManageRegFormBase):
    """Display and modify ticket settings"""

    def _process(self):
        form = TicketsForm(obj=self.regform)
        if form.validate_on_submit():
            form.populate_obj(self.regform)
            db.session.flush()
            return redirect(url_for('.manage_regform', self.regform))
        return WPManageRegistration.render_template('management/regform_tickets.html', self.event,
                                                    regform=self.regform, form=form)


def generate_ticket(registration):
    pdf = TicketToPDF(registration.registration_form.event, registration)
    return BytesIO(pdf.getPDFBin())


class RHTicketDownload(RHRegistrationFormRegistrationBase):
    """Generate ticket for a given registration"""

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
