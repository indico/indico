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

from indico.modules.events.contributions.models.contributions import Contribution
from MaKaC.webinterface.rh.base import RHModificationBaseProtected
from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay


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
    """Base class for all paper-related RHs only available to judges/managers"""

    def _checkProtection(self):
        RHPapersBase._checkProtection(self)
        if not session.user or (not self.management and session.user not in self.event_new.cfp.judges):
            raise Forbidden


class RHPaperBase(RHPapersBase):
    normalize_url_spec = {
        'locators': {
            lambda self: self.contribution
        }
    }

    def _checkParams(self, params):
        RHPapersBase._checkParams(self, params)
        self.contribution = Contribution.get_one(request.view_args['contrib_id'], is_deleted=False)
        self.paper = self.contribution.paper

    def _checkProtection(self):
        RHPapersBase._checkProtection(self)
        if not self._check_paper_protection():
            raise Forbidden

    def _check_paper_protection(self):
        """Perform a permission check on the current paper.

        Override this in case you want to check for more specific
        privileges than the generic "can access".
        """
        return self.contribution.can_access(session.user)
