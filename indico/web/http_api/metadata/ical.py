# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import datetime

import dateutil.parser
import icalendar as ical
from lxml import html
from lxml.etree import ParserError
from pytz import timezone, utc
from werkzeug.urls import url_parse

from indico.core.config import config
from indico.util.date_time import now_utc
from indico.util.string import to_unicode
from indico.web.http_api.metadata.serializer import Serializer


class vRecur(ical.vRecur):
    """Fix vRecur so the frequency comes first."""
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


def _deserialize_date(date_dict):
    if isinstance(date_dict, datetime):
        return date_dict
    dt = datetime.combine(dateutil.parser.parse(date_dict['date']).date(),
                          dateutil.parser.parse(date_dict['time']).time())
    return timezone(date_dict['tz']).localize(dt).astimezone(utc)


def serialize_event(cal, fossil, now, id_prefix="indico-event"):
    event = ical.Event()
    event.add('uid', '{}-{}@{}'.format(id_prefix, fossil['id'], url_parse(config.BASE_URL).host))
    event.add('dtstamp', now)
    event.add('dtstart', _deserialize_date(fossil['startDate']))
    event.add('dtend', _deserialize_date(fossil['endDate']))
    event.add('url', fossil['url'])
    event.add('summary', to_unicode(fossil['title']))
    loc = fossil['location'] or ''
    if loc:
        loc = to_unicode(loc)
    if fossil['roomFullname']:
        loc += ' ' + to_unicode(fossil['roomFullname'])
    event.add('location', loc)
    description = ''
    if fossil.get('speakers'):
        speakers = ('{} ({})'.format(speaker['fullName'].encode('utf-8'),
                                     speaker['affiliation'].encode('utf-8')) for speaker in fossil['speakers'])
        description += 'Speakers: {}\n'.format(', '.join(speakers))

    if fossil['description']:
        desc_text = fossil['description'].strip()
        if not desc_text:
            desc_text = '<p/>'
        try:
            description += '{}\n\n{}'.format(to_unicode(html.fromstring(to_unicode(desc_text))
                                                        .text_content()).encode('utf-8'),
                                             fossil['url'].encode('utf-8'))
        except ParserError:
            # this happens e.g. if desc_text contains only a html comment
            description += fossil['url'].encode('utf-8')
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
        if not isinstance(results, list):
            results = [results]

        cal = ical.Calendar()
        cal.add('version', '2.0')
        cal.add('prodid', '-//CERN//INDICO//EN')
        now = now_utc()
        for fossil in results:
            if '_fossil' in fossil:
                mapper = ICalSerializer._mappers.get(fossil['_fossil'])
            else:
                mapper = self._extra_args.get('ical_serializer')
            if mapper:
                mapper(cal, fossil, now)

        return cal.to_ical()
