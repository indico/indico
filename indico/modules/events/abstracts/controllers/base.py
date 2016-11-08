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

from indico.modules.events.abstracts.models.abstracts import Abstract
from MaKaC.webinterface.rh.base import RHModificationBaseProtected
from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay


class SpecificAbstractMixin:
    """Mixin for RHs that deal with a specific abstract"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.abstract
        }
    }

    def _checkParams(self):
        self.abstract = Abstract.get_one(request.view_args['abstract_id'], is_deleted=False)

    def _checkProtection(self):
        if not self._check_abstract_protection():
            raise Forbidden

    def _check_abstract_protection(self):
        raise NotImplementedError


class RHAbstractsBase(RHConferenceBaseDisplay):
    """Base class for all abstract-related RHs"""

    CSRF_ENABLED = True
    EVENT_FEATURE = 'abstracts'

    def _checkProtection(self):
        RHConferenceBaseDisplay._checkProtection(self)
        # Only let event managers access the management versions.
        if self.management and not self.event_new.can_manage(session.user):
            raise Forbidden

    @property
    def management(self):
        """Whether the RH is currently used in the management area"""
        return request.view_args.get('management', False)


class RHManageAbstractsBase(RHAbstractsBase, RHModificationBaseProtected):
    """
    Base class for all abstract-related RHs that require full event
    management permissions
    """

    @property
    def management(self):
        """Whether the RH is currently used in the management area"""
        return request.view_args.get('management', True)

    def _checkProtection(self):
        RHModificationBaseProtected._checkProtection(self)
        # Only let event managers access the management versions.
        if self.management and not self.event_new.can_manage(session.user):
            raise Forbidden


class RHAbstractBase(SpecificAbstractMixin, RHAbstractsBase):
    """
    Base class for all abstract-related RHs that require read access
    to the associated abstract.
    """

    def _checkParams(self, params):
        RHAbstractsBase._checkParams(self, params)
        SpecificAbstractMixin._checkParams(self)

    def _checkProtection(self):
        RHAbstractsBase._checkProtection(self)
        SpecificAbstractMixin._checkProtection(self)

    def _check_abstract_protection(self):
        """Perform a permission check on the current abstract.

        Override this in case you want to check for more specific
        privileges than the generic "can access".
        """
        return self.abstract.can_access(session.user)
