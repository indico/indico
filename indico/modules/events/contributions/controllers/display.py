# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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
from werkzeug.exceptions import Forbidden

from indico.modules.events.contributions.models.contributions import Contribution
from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay


class RHContributionsDisplayBase(RHConferenceBaseDisplay):
    CSRF_ENABLED = True

    def _checkProtection(self):
        if not session.user:
            raise Forbidden
        RHConferenceBaseDisplay._checkProtection(self)


class RHContributionDisplayBase(RHContributionsDisplayBase):

    normalize_url_spec = {
        'locators': {
            lambda self: self.contrib
        }
    }

    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams(self, params)
        self.contrib = Contribution.find_one(id=request.view_args['contrib_id'], is_deleted=False)
