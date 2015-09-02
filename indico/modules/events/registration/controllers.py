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
from indico.modules.events.registration.models.registration_forms import RegistrationForm
from indico.modules.events.registration.views import WPManageRegistration
from indico.web.flask.util import url_for
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase


class RHManageRegistrationBase(RHConferenceModifBase):
    """Base class for all registration management RHs"""

    CSRF_ENABLED = True

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self.event = self._conf


class RHRegistrationForms(RHManageRegistrationBase):
    """List of registration form for an event"""

    def _process(self):
        query = RegistrationForm.find(event_id=self.event.id, is_deleted=False)
        regforms = query.order_by(db.func.lower(RegistrationForm.title)).all()
        return WPManageRegistration.render_template('management/regform_list.html', self.event,
                                                    event=self.event, regforms=regforms)


class RHRegistrationFormCreate(RHManageRegistrationBase):
    "Creates a new registration form"

    def _process(self):
        return redirect(url_for('.manage_regform_list', self.event))
