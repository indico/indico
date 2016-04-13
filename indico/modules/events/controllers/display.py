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

from io import BytesIO

from flask import request

from indico.modules.events.util import serialize_event_for_ical
from indico.web.http_api.metadata import Serializer
from indico.web.flask.util import send_file
from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay


class RHExportEventICAL(RHConferenceBaseDisplay):
    def _process(self):
        detail_level = request.args.get('detail', 'events')
        data = {'results': serialize_event_for_ical(self.event_new, detail_level)}
        serializer = Serializer.create('ics')
        return send_file('event.ics', BytesIO(serializer(data)), 'text/calendar')
