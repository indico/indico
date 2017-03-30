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

from io import BytesIO

from flask import redirect, request

from indico.legacy.webinterface.pages.conferences import WPConferenceDisplay
from indico.legacy.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay
from indico.modules.events.layout.views import WPPage
from indico.modules.events.models.events import EventType
from indico.modules.events.util import serialize_event_for_ical, get_theme
from indico.modules.events.views import WPSimpleEventDisplay
from indico.web.flask.util import send_file, url_for
from indico.web.http_api.metadata import Serializer


class RHExportEventICAL(RHConferenceBaseDisplay):
    def _process(self):
        detail_level = request.args.get('detail', 'events')
        data = {'results': serialize_event_for_ical(self.event_new, detail_level)}
        serializer = Serializer.create('ics')
        return send_file('event.ics', BytesIO(serializer(data)), 'text/calendar')


class RHDisplayEvent(RHConferenceBaseDisplay):
    """Display the main page of an event.

    For a conference this is either the overview page or the custom
    home page if one has been set.
    For a meeting/lecture the timetable is shown.
    """

    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams(self, params)
        self.force_overview = request.view_args.get('force_overview', False)
        self.theme_id, self.theme_override = get_theme(self.event_new, request.args.get('view'))

    def _process(self):
        if self.event_new.type_ == EventType.conference:
            if self.theme_override:
                return redirect(url_for('timetable.timetable', self.event_new, view=self.theme_id))
            elif self.event_new.default_page and not self.force_overview:
                return self._display_conference_page()
            else:
                return self._display_conference()
        else:
            return self._display_simple()

    def _display_conference_page(self):
        """Display the custom conference home page"""
        return WPPage.render_template('page.html', self._conf, page=self.event_new.default_page)

    def _display_conference(self):
        """Display the conference overview page"""
        return WPConferenceDisplay(self, self._conf).display()

    def _display_simple(self):
        """Display a simple single-page event (meeting/lecture)"""
        return WPSimpleEventDisplay(self, self._conf, self.theme_id, self.theme_override).display()
