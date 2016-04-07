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

from flask import request

from MaKaC.webinterface.rh.base import RH
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase


class RHManageTimetableBase(RHConferenceModifBase):
    """Base class for all timetable management RHs"""

    CSRF_ENABLED = True

    def _process(self):
        return RH._process(self)


class RHManageTimetableEntryBase(RHManageTimetableBase):
    normalize_url_spec = {
        'locators': {
            lambda self: self.entry
        }
    }

    def _checkParams(self, params):
        RHManageTimetableBase._checkParams(self, params)
        self.entry = None
        if 'timetable_entry_id' in request.view_args:
            self.entry = (self.event_new.timetable_entries
                          .filter_by(id=request.view_args['timetable_entry_id'])
                          .first_or_404())
