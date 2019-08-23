# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import datetime

import dateutil.parser
from pytz import timezone, utc
from werkzeug.contrib.atom import AtomFeed

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
        if not isinstance(results, list):
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
