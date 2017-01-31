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

from flask import request, session
from werkzeug.exceptions import Forbidden

from MaKaC.webinterface.rh.base import RHModificationBaseProtected
from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay
from indico.modules.events.contributions import Contribution
from indico.modules.users import User


class RHPapersBase(RHConferenceBaseDisplay):
    """Base class for all paper-related RHs"""

    CSRF_ENABLED = True
    EVENT_FEATURE = 'papers'

    def _checkProtection(self):
        RHConferenceBaseDisplay._checkProtection(self)
        # Only let event managers access the management versions.
        if self.management and not self.event_new.can_manage(session.user, role='paper_manager'):
            raise Forbidden

    @property
    def management(self):
        """Whether the RH is currently used in the management area"""
        return request.view_args.get('management', False)


class RHManagePapersBase(RHPapersBase, RHModificationBaseProtected):
    """
    Base class for all paper-related RHs that require full event
    management permissions
    """

    ROLE = 'paper_manager'

    def _checkProtection(self):
        RHModificationBaseProtected._checkProtection(self)

    @property
    def management(self):
        """Whether the RH is currently used in the management area"""
        return request.view_args.get('management', True)


class RHJudgingAreaBase(RHPapersBase):
    """Base class for all paper-related RHs that require judging or event management permissions"""

    def _checkParams(self, params):
        RHPapersBase._checkParams(self, params)
        if session.user:
            query = Contribution.query.with_parent(self.event_new)
            if not self.management:
                query = query.filter(Contribution.paper_judges.any(User.id == session.user.id))
            self.contributions = query.all()

    def _checkProtection(self):
        RHPapersBase._checkProtection(self)
        if not session.user:
            raise Forbidden
        if not self.management and session.user not in self.event_new.cfp.judges:
            raise Forbidden
