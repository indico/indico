# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from enum import Enum

from flask import request, session
from werkzeug.exceptions import Forbidden, NotFound

from indico.modules.events.management.controllers import RHManageEventBase
from indico.modules.events.timetable import TimetableEntryType


class SessionManagementLevel(Enum):
    none = 0
    manage = 1
    coordinate_with_blocks = 2
    coordinate_with_contribs = 3
    coordinate = 4


class RHManageTimetableBase(RHManageEventBase):
    """Base class for all timetable management RHs"""

    session_management_level = SessionManagementLevel.none

    def _process_args(self):
        RHManageEventBase._process_args(self)
        self.session = None
        if 'session_id' in request.view_args:
            self.session = self.event.get_session(request.view_args['session_id'])
            if self.session is None:
                raise NotFound

    def _check_access(self):
        if not self.session or self.session_management_level == SessionManagementLevel.none:
            RHManageEventBase._check_access(self)
        else:
            if self.session_management_level == SessionManagementLevel.manage:
                func = lambda u: self.session.can_manage(u)
            elif self.session_management_level == SessionManagementLevel.coordinate_with_blocks:
                func = lambda u: self.session.can_manage_blocks(u)
            elif self.session_management_level == SessionManagementLevel.coordinate_with_contribs:
                func = lambda u: self.session.can_manage_contributions(u)
            elif self.session_management_level == SessionManagementLevel.coordinate:
                func = lambda u: self.session.can_manage(u, permission='coordinate')
            else:
                raise Exception("Invalid session management level")
            if not func(session.user):
                raise Forbidden


class RHManageTimetableEntryBase(RHManageTimetableBase):
    normalize_url_spec = {
        'locators': {
            lambda self: self._get_locator()
        }
    }

    def _get_locator(self):
        if not self.entry:
            return self.event
        locator = self.entry.locator
        if 'session_id' in request.view_args:
            locator['session_id'] = self.session.id
        return locator

    def _process_args(self):
        RHManageTimetableBase._process_args(self)
        self.entry = None
        if 'entry_id' in request.view_args:
            self.entry = self.event.timetable_entries.filter_by(id=request.view_args['entry_id']).first_or_404()

    def _check_access(self):
        if self.session and self.entry:
            entry_session = None
            if self.entry.parent and self.entry.parent.type == TimetableEntryType.SESSION_BLOCK:
                entry_session = self.entry.parent.session_block.session
            elif self.entry.type == TimetableEntryType.SESSION_BLOCK:
                entry_session = self.entry.session_block.session
            if entry_session != self.session:
                raise Forbidden('Timetable entry is not in the specified session')
        RHManageTimetableBase._check_access(self)
