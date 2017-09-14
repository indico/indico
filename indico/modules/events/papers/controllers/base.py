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
from werkzeug.exceptions import Forbidden, NotFound

from indico.legacy.webinterface.rh.base import RHModificationBaseProtected, check_event_locked
from indico.legacy.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay
from indico.modules.events.contributions.models.contributions import Contribution


class RHPapersBase(RHConferenceBaseDisplay):
    """Base class for all paper-related RHs"""

    EVENT_FEATURE = 'papers'

    def _checkProtection(self):
        RHConferenceBaseDisplay._checkProtection(self)
        # Only let managers access the management versions.
        if self.management and not self.event.cfp.is_manager(session.user):
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

    PERMISSION = 'paper_manager'
    DENY_FRAMES = True

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
        if not session.user or not self.event.cfp.can_access_judging_area(session.user):
            raise Forbidden
        check_event_locked(self, self.event)


class RHPaperBase(RHPapersBase):
    PAPER_REQUIRED = True

    normalize_url_spec = {
        'locators': {
            lambda self: self.contribution
        }
    }

    def _checkParams(self, params):
        RHPapersBase._checkParams(self, params)
        self.contribution = Contribution.get_one(request.view_args['contrib_id'], is_deleted=False)
        self.paper = self.contribution.paper
        if self.paper is None and self.PAPER_REQUIRED:
            raise NotFound

    def _checkProtection(self):
        RHPapersBase._checkProtection(self)
        if not self._check_paper_protection():
            raise Forbidden
        check_event_locked(self, self.event)

    def _check_paper_protection(self):
        """Perform a permission check on the current paper.

        Override this in case you want to check for more specific
        privileges than the generic "can access".
        """
        return self.contribution.can_access(session.user)
