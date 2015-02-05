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

from flask import request, session

from indico.core.errors import AccessError
from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay

from indico.modules.agreements.forms import AgreementForm
from indico.modules.agreements.models.agreements import Agreement
from indico.modules.agreements.views import WPAgreementForm


class RHAgreementForm(RHConferenceBaseDisplay):
    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams(self, params)
        uuid = request.view_args['uuid']
        self.agreement = Agreement.find_one(uuid=uuid)

    def _checkSessionUser(self):
        if session.user is None:
            self._redirect(self._getLoginURL())
        if self.agreement.user != session.user:
            raise AccessError()

    def _checkProtection(self):
        RHConferenceBaseDisplay._checkProtection(self)
        if self.agreement.user:
            self._checkSessionUser()

    def _process(self):
        form = AgreementForm()
        if form.validate_on_submit() and self.agreement.pending:
            if form.agreed.data:
                self.agreement.accept()
            else:
                self.agreement.reject()
        html = self.agreement.render(form)
        return WPAgreementForm.render_string(html, self._conf)
