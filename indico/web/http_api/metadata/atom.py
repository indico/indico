# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

# python stdlib imports
from pyatom import AtomFeed

# indico imports
from indico.util.string import unicodeOrNone

# module imports
from indico.web.http_api.metadata.serializer import Serializer


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
                title=unicodeOrNone(fossil['title']),
                summary=unicodeOrNone(fossil['description']),
                url=fossil['url'],
                updated=fossil['startDate']  # ugh, but that's better than creationDate
                )
        return feed.to_string()
