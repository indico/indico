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

from flask import jsonify, request

from indico.modules.events.timetable.legacy import TimetableSerializer
from indico.modules.events.timetable.views import WPDisplayTimetable
from indico.modules.events.timetable.util import render_entry_info_balloon, serialize_event_info
from MaKaC.webinterface.pages.conferences import WPTPLConferenceDisplay
from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay


class RHTimetable(RHConferenceBaseDisplay):
    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams(self, params)
        self.layout = request.args.get('layout')
        if not self.layout:
            self.layout = request.args.get('ttLyt')

    def _process(self):
        if self.event_new.theme == 'static':
            event_info = serialize_event_info(self.event_new)
            timetable_data = TimetableSerializer().serialize_timetable(self.event_new)
            return WPDisplayTimetable.render_template('display.html', self._conf, event_info=event_info,
                                                      timetable_data=timetable_data, timetable_layout=self.layout)
        else:
            page = WPTPLConferenceDisplay(self, self._conf, view=self.event_new.theme, type='meeting', params={})
            return page.display()


class RHTimetableEntryInfo(RHConferenceBaseDisplay):
    """Display timetable entry info balloon."""

    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams(self, params)
        self.entry = self.event_new.timetable_entries.filter_by(id=request.view_args['entry_id']).first_or_404()

    def _process(self):
        html = render_entry_info_balloon(self.entry)
        return jsonify(html=html)
