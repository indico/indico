# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import datetime

import dateutil.parser
from feedgen.feed import FeedGenerator
from pytz import timezone, utc

from indico.util.string import sanitize_html, to_unicode
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

        feed = FeedGenerator()
        feed.id(fossils['url'])
        feed.title('Indico Feed')
        feed.link(href=fossils['url'], rel='self')

        for fossil in results:
            entry = feed.add_entry(order='append')
            entry.id(fossil['url'])
            entry.title(to_unicode(fossil['title']) or None)
            entry.summary(sanitize_html(to_unicode(fossil['description'])) or None, type='html')
            entry.link(href=fossil['url'])
            entry.updated(_deserialize_date(fossil['startDate']))
        return feed.atom_str(pretty=True)
