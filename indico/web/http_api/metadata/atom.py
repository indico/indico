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

import dateutil.parser
from pyatom import AtomFeed
from pytz import timezone, utc

from indico.util.string import to_unicode
from indico.web.http_api.metadata.serializer import Serializer


def _deserialize_date(date_dict):
    if isinstance(date_dict, datetime):
        return date_dict
    dt = datetime.combine(dateutil.parser.parse(date_dict['date']).date(),
                          dateutil.parser.parse(date_dict['time']).time())
    return timezone(date_dict['tz']).localize(dt).astimezone(utc)


class AtomSerializer(Serializer):

    schemaless = False
    _mime = 'application/atom+xml'

    def _execute(self, fossils):
        results = fossils['results']
        if type(results) != list:
            results = [results]

        feed = AtomFeed(
            title='Indico Feed',
            feed_url=fossils['url']
        )

        for fossil in results:
            feed.add(
                title=to_unicode(fossil['title']) or None,
                summary=to_unicode(fossil['description']) or None,
                url=fossil['url'],
                updated=_deserialize_date(fossil['startDate'])  # ugh, but that's better than creationDate
            )
        return feed.to_string()
