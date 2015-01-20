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
import os
from collections import defaultdict
from operator import itemgetter

# module imports
from indico.web.http_api.metadata.serializer import Serializer

# legacy indico imports
from MaKaC.common.TemplateExec import render


class HTML4Serializer(Serializer):

    schemaless = False
    _mime = 'text/html'

    def _execute(self, fossils):
        results = fossils['results']
        if type(results) != list:
            results = [results]

        unorderedFossils = defaultdict(list)
        for fossil in results:
            unorderedFossils[fossil['startDate'].date()].append(fossil)

        # Sort top level (by date)
        orderedFossils = sorted(unorderedFossils.items(), key=itemgetter(0))
        # Sort day level (by date/time, actually only time because it's only a single day)
        for day, events in orderedFossils:
            events.sort(key=itemgetter('startDate'))
        return render(os.path.join(os.path.dirname(__file__), 'html4.tpl'),
                      {'fossils': orderedFossils, 'ts': fossils['ts']})
