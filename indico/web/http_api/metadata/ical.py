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
import icalendar as ical
from lxml import html

# indico imports
from indico.web.http_api.metadata.serializer import Serializer

# legacy indico imports
from MaKaC.common.timezoneUtils import nowutc, getAdjustedDate


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
    event.add('uid', '%s-%s@cern.ch' % (id_prefix, fossil['id']))
    event.add('dtstamp', now)
    event.add('dtstart', getAdjustedDate(fossil['startDate'], None, "UTC"))
    event.add('dtend', getAdjustedDate(fossil['endDate'], None, "UTC"))
    event.add('url', fossil['url'])
    event.add('summary', fossil['title'].decode('utf-8'))
    loc = fossil['location'] or ''
    if loc:
        loc = loc.decode('utf-8')
    if fossil['room']:
        loc += ' ' + fossil['room'].decode('utf-8')
    event.add('location', loc)
    description = ""
    if fossil.get('speakers'):
        speakers = ('{} ({})'.format(speaker['fullName'], speaker['affiliation']) for speaker in fossil['speakers'])
        description += 'Speakers: {}\n'.format(', '.join(speakers))

    if fossil['description']:
        desc_text = fossil['description'].strip()
        if not desc_text:
            desc_text = '<p/>'
        description += '{}\n\n{}'.format(html.fromstring(desc_text.decode('utf-8')).text_content().encode('utf-8'),
                                         fossil['url'])
    else:
        description += fossil['url']
    event.add('description', description)
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
        'sessionMetadataWithContributions': serialize_contribs
    }

    @classmethod
    def register_mapper(cls, fossil, func):
        cls._mappers[fossil] = func

    def _execute(self, fossils):
        results = fossils['results']
        if type(results) != list:
            results = [results]

        cal = ical.Calendar()
        cal.add('version', '2.0')
        cal.add('prodid', '-//CERN//INDICO//EN')
        now = nowutc()
        for fossil in results:
            if '_fossil' in fossil:
                mapper = ICalSerializer._mappers.get(fossil['_fossil'])
            else:
                mapper = self._extra_args.get('ical_serializer')
            if mapper:
                mapper(cal, fossil, now)

        return cal.to_ical()
