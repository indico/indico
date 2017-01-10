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

from datetime import datetime
from itertools import groupby
from operator import itemgetter

import dateutil.parser
from flask import render_template
from pytz import timezone

from indico.web.http_api.metadata.serializer import Serializer


def _deserialize_date(date_dict):
    if isinstance(date_dict, datetime):
        return date_dict
    dt = datetime.combine(dateutil.parser.parse(date_dict['date']).date(),
                          dateutil.parser.parse(date_dict['time']).time())
    return timezone(date_dict['tz']).localize(dt)


class HTML4Serializer(Serializer):
    schemaless = False
    _mime = 'text/html; charset=utf-8'

    def _execute(self, fossils):
        results = fossils['results']
        # XXX: is this actually needed?!
        if not isinstance(results, list):
            results = [results]

        events = [{'id': int(e['id']),
                   'start_dt': _deserialize_date(e['startDate']),
                   'category': e['category'],
                   'url': e['url'],
                   'title': e['title'],
                   'room': e['room']} for e in results]
        events_by_date = groupby(sorted(events, key=itemgetter('start_dt')), key=lambda x: x['start_dt'].date())
        return render_template('api/event_list.html', events_by_date=events_by_date, ts=fossils['ts'])
