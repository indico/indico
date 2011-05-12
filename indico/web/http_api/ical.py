# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

# python stdlib imports
import datetime
from operator import itemgetter
import icalendar as ical

# indico imports
from indico.util.string import unicodeOrNone

# module imports
from indico.util.metadata.serializer import Serializer


class ICalSerializer(Serializer):

    schemaless = False
    _mime = 'text/calendar'

    def __call__(self, fossils):
        results = fossils['results']
        if type(results) != list:
            results = [results]

        cal = ical.Calendar()
        cal.set('version', '2.0')
        cal.set('prodid', '-//CERN//INDICO//EN')

        now = datetime.datetime.utcnow()
        for fossil in results:
            if fossil['_fossil'] == 'conferenceMetadata':
                event = ical.Event()
                event.set('uid', 'indico-%s@cern.ch' % fossil['id'])
                event.set('dtstamp', now)
                event.set('dtstart', fossil['startDate'])
                event.set('dtend', fossil['endDate'])
                event.set('url', fossil['url'])
                event.set('summary', fossil['title'])
                loc = fossil['location']
                if fossil['room']:
                    loc += ' ' + fossil['room']
                event.set('location', loc)
                if fossil['description']:
                    event.set('description', fossil['description'] + '\n' + fossil['url'])
                else:
                    event.set('description', fossil['url'])
                cal.add_component(event)

        return str(cal)
