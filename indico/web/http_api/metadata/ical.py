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
import datetime
import icalendar as ical
from lxml import html

# indico imports
from indico.web.http_api.metadata.serializer import Serializer

# legacy indico imports
from MaKaC.rb_reservation import RepeatabilityEnum
from MaKaC.rb_tools import weekNumber
from MaKaC.common.timezoneUtils import nowutc, getAdjustedDate

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


def serialize_event(cal, fossil, now, id_prefix="indico-event"):
    event = ical.Event()
    event.set('uid', '%s-%s@cern.ch' % (id_prefix, fossil['id']))
    event.set('dtstamp', now)
    event.set('dtstart', getAdjustedDate(fossil['startDate'], None, "UTC"))
    event.set('dtend', getAdjustedDate(fossil['endDate'], None, "UTC"))
    event.set('url', fossil['url'])
    event.set('summary', fossil['title'].decode('utf-8'))
    loc = fossil['location'] or ''
    if loc:
        loc = loc.decode('utf-8')
    if fossil['room']:
        loc += ' ' + fossil['room'].decode('utf-8')
    event.set('location', loc)
    description = ""
    if fossil.has_key("speakers"):
        speakerList = []
        for speaker in fossil["speakers"]:
            speakerList.append("%s (%s)"%(speaker["fullName"], speaker["affiliation"]))
        description += "Speakers: "+ (", ").join(speakerList) + "\n"

    if fossil['description']:
        desc_text = fossil.get('description', '').strip()
        if not desc_text:
            desc_text = '<p/>'
        description += html.fromstring(desc_text.decode('utf-8')).text_content() + '\n\n'+ fossil['url']
    else:
        description += fossil['url']
    event.set('description', description)
    cal.add_component(event)


def serialize_repeatability(startDT, endDT, repType):
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


def serialize_reservation(cal, fossil, now):
    event = ical.Event()
    event.set('uid', 'indico-resv-%s@cern.ch' % fossil['id'])
    event.set('dtstamp', now)
    event.set('dtstart', getAdjustedDate(fossil['startDT'], None, "UTC"))
    event.set('dtend', getAdjustedDate(datetime.datetime.combine(fossil['startDT'].date(), fossil['endDT'].timetz()), None, "UTC"))
    event.set('url', fossil['bookingUrl'])
    event.set('summary', fossil['reason'])
    event.set('location', fossil['location'].decode('utf-8') + ': ' + fossil['room']['fullName'].decode('utf-8'))
    event.set('description', fossil['reason'].decode('utf-8') + '\n\n' + fossil['bookingUrl'])
    rrule = None
    if fossil['repeatability'] is not None:
        rrule = serialize_repeatability(fossil['startDT'], fossil['endDT'], RepeatabilityEnum.shortname2rep[fossil['repeatability']])
    if rrule:
        event.set('rrule', rrule)
    cal.add_component(event)


def serialize_contribs(cal, fossil, now):
    if len(fossil['contributions']) == 0:
        serialize_event(cal, fossil, now)
    else:
        for sfossil in fossil['contributions']:
            if sfossil['startDate']:
                sfossil['id'] = "%s-%s" % (fossil['id'], sfossil['id'])
                serialize_event(cal, sfossil, now, id_prefix="indico-contribution")


def serialize_contrib(cal, fossil, now):
    serialize_event(cal, fossil, now, id_prefix="indico-contribution")


def serialize_sessions(cal, fossil, now):
    if len(fossil['sessions']) == 0:
        serialize_event(cal, fossil, now)
    else:
        for sfossil in fossil['sessions']:
            if sfossil['startDate']:
                serialize_session(cal, sfossil, now, fid="%s-%s" % (fossil['id'], sfossil['id']))


def serialize_session(cal, fossil, now, fid=None):
    if fid:
        fossil['id'] = fid
    serialize_event(cal, fossil, now, id_prefix="indico-session")


class ICalSerializer(Serializer):

    schemaless = False
    _mime = 'text/calendar'

    _mappers = {
        'conferenceMetadata': serialize_event,
        'contributionMetadata': serialize_contrib,
        'sessionMetadata': serialize_session,
        'conferenceMetadataWithContribs': serialize_contribs,
        'conferenceMetadataWithSessions': serialize_sessions,
        'sessionMetadataWithContributions': serialize_contribs,
        'reservationMetadata': serialize_reservation
    }

    @classmethod
    def register_mapper(cls, fossil, func):
        cls._mappers[fossil] = func

    def _execute(self, fossils):
        results = fossils['results']
        if type(results) != list:
            results = [results]

        cal = ical.Calendar()
        cal.set('version', '2.0')
        cal.set('prodid', '-//CERN//INDICO//EN')
        now = nowutc()
        for fossil in results:
            mapper = ICalSerializer._mappers.get(fossil['_fossil'])
            if mapper:
                mapper(cal, fossil, now)

        return cal.to_ical()
