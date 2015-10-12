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

from flask import request, jsonify
from sqlalchemy.orm import joinedload

from indico.core.db import db
from indico.modules.events.registration.controllers.management import RHManageRegFormBase
from indico.modules.events.registration.models.invitations import RegistrationInvitation
from indico.modules.events.registration.views import WPManageRegistration


class RHRegistrationFormInvitations(RHManageRegFormBase):
    """Overview of all registration invitations"""

    def _process(self):
        invitations = (RegistrationInvitation.query
                       .with_parent(self.regform)
                       .options(joinedload('registration'))
                       .all())
        return WPManageRegistration.render_template('management/regform_invitations.html', self.event,
                                                    regform=self.regform, invitations=invitations)


class RHRegistrationFormDeleteInvitation(RHManageRegFormBase):
    """Delete a registration invitation"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.invitation
        }
    }

    def _checkParams(self, params):
        RHManageRegFormBase._checkParams(self, params)
        self.invitation = RegistrationInvitation.get_one(request.view_args['invitation_id'])

    def _process(self):
        db.session.delete(self.invitation)
        return jsonify(success=True)
