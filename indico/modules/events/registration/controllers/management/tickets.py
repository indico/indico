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

from flask import redirect

from indico.core.db import db
from indico.modules.events.registration.controllers.management import RHManageRegFormBase
from indico.modules.events.registration.forms import TicketsForm
from indico.modules.events.registration.views import WPManageRegistration
from indico.web.flask.util import url_for


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
