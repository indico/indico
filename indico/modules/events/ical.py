# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from icalendar import Calendar, Event
from lxml import html
from lxml.etree import ParserError
from werkzeug.urls import url_parse

from indico.core import signals
from indico.core.config import config
from indico.util.date_time import now_utc
from indico.util.signals import values_from_signal


def event_to_ical(event, user=None):
    """Serialize an event into an ical.

    :param event: The event to serialize
    :param user: The user who needs to be able to access the events
    """

    return events_to_ical([event], user)


def events_to_ical(events, user=None):
    """Serialize multiple events into an ical.

    :param events: A list of events to serialize
    :param user: The user who needs to be able to access the events
    """

    calendar = Calendar()
    calendar.add('version', '2.0')
    calendar.add('prodid', '-//CERN//INDICO//EN')

    for event in events:
        cal_event = Event()

        cal_event.add('uid', 'indico-event-{}@{}'.format(event.id, url_parse(config.BASE_URL).host))

        cal_event.add('dtstamp', now_utc(False))
        cal_event.add('dtstart', event.start_dt)
        cal_event.add('dtend', event.end_dt)
        cal_event.add('url', event.external_url)
        cal_event.add('summary', event.title)

        location = (f'{event.room_name} ({event.venue_name})'
                    if event.venue_name and event.room_name
                    else (event.venue_name or event.room_name))

        if location:
            cal_event.add('location', location)

        description = []
        if event.person_links:
            speakers = [f'{x.full_name} ({x.affiliation})' if x.affiliation else x.full_name
                        for x in event.person_links]
            description.append('Speakers: {}'.format(', '.join(speakers)))

        if event.description:
            desc_text = str(event.description) or '<p/>'  # get rid of RichMarkup
            try:
                description.append(str(html.fromstring(desc_text).text_content()))
            except ParserError:
                # this happens if desc_text only contains a html comment
                pass

        description.append(event.external_url)
        data = {'description': '\n'.join(description)}

        for update in values_from_signal(
            signals.event.metadata_postprocess.send('ical-export', event=event, data=data, user=user),
            as_list=True
        ):
            data.update(update)

        cal_event.add('description', data['description'])

        calendar.add_component(cal_event)

    return calendar.to_ical()
