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
import icalendar as ical

# indico imports
from indico.util.metadata.serializer import Serializer

# legacy indico imports
from MaKaC.rb_reservation import RepeatabilityEnum
from MaKaC.rb_tools import weekNumber

WEEK_DAYS = 'MO TU WE TH FR SA SU'.split()

class vRecur(ical.vRecur):
    """Fix vRecur so the frequency comes first"""
    def ical(self):
        # SequenceTypes
        result = ['FREQ=%s' % self.types['FREQ'](self['FREQ']).ical()]
        for key, vals in self.items():
            if key == 'FREQ':
                continue
            typ = self.types[key]
            if not type(vals) in ical.prop.SequenceTypes:
                vals = [vals]
            vals = ','.join([typ(val).ical() for val in vals])
            result.append('%s=%s' % (key, vals))
        return ';'.join(result)
ical.cal.types_factory['recur'] = vRecur

class ICalSerializer(Serializer):

    schemaless = False
    _mime = 'text/calendar'

    def _serialize_conference(self, fossil, now):
        event = ical.Event()
        event.set('uid', 'indico-event-%s@cern.ch' % fossil['id'])
        event.set('dtstamp', now)
        event.set('dtstart', fossil['startDate'])
        event.set('dtend', fossil['endDate'])
        event.set('url', fossil['url'])
        event['summary'] = fossil['title']
        loc = fossil['location'] or ''
        if fossil['room']:
            loc += ' ' + fossil['room']
        event['location'] = loc
        if fossil['description']:
            event['description'] = fossil['description'] + '\n' + fossil['url']
        else:
            event['description'] = fossil['url']
        return event

    def _serialize_repeatability(self, startDT, endDT, repType):
        intervals = { RepeatabilityEnum.onceAWeek: 1, RepeatabilityEnum.onceEvery2Weeks: 2, RepeatabilityEnum.onceEvery3Weeks: 3 }
        recur = ical.vRecur()
        recur['until'] = endDT
        if repType == RepeatabilityEnum.daily:
            recur['freq'] = 'daily'
        elif repType in intervals.keys():
            recur['freq'] = 'weekly'
            recur['interval'] = intervals[repType]
        elif repType == RepeatabilityEnum.onceAMonth:
            recur['freq'] = 'monthly'
            recur['byday'] = str(weekNumber(startDT)) + WEEK_DAYS[startDT.weekday()]
        return recur

    def _serialize_reservation(self, fossil, now):
        event = ical.Event()
        event.set('uid', 'indico-resv-%s@cern.ch' % fossil['id'])
        event.set('dtstamp', now)
        event.set('dtstart', fossil['startDT'])
        event.set('dtend', datetime.datetime.combine(fossil['startDT'].date(), fossil['endDT'].time()))
        event.set('url', fossil['bookingUrl'])
        event.set('summary', fossil['reason'])
        event['location'] = fossil['location'] + ': ' + fossil['room']['fullName']
        event['description'] = fossil['reason'] + '\n' + fossil['bookingUrl']
        rrule = None
        if fossil['repeatability'] is not None:
            rrule = self._serialize_repeatability(fossil['startDT'], fossil['endDT'], RepeatabilityEnum.shortname2rep[fossil['repeatability']])
        if rrule:
            event.set('rrule', rrule)
        return event

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
                cal.add_component(self._serialize_conference(fossil, now))
            elif fossil['_fossil'] == 'reservationMetadata':
                cal.add_component(self._serialize_reservation(fossil, now))

        return str(cal)
