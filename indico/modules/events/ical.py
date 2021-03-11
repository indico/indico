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
from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.modules.events.contributions.ical import generate_contribution_component
from indico.util.date_time import now_utc
from indico.util.signals import values_from_signal


def generate_event_component(event, event_uid):
    """Generates an Event icalendar component from an Indico Event.

    :param event: The Indico Event to use
    :returns: an icalendar Event
    """

    cal_event = Event()
    cal_event.add('uid', event_uid)
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

    if event.contact_title:
        contact_info = f'{event.contact_title}'
        if len(event.contact_emails):
            contact_info += f'; {"; ".join(event.contact_emails)}'
        if len(event.contact_phones):
            contact_info += f'; {"; ".join(event.contact_phones)}'
        cal_event.add('contact', contact_info)

    # logo url will be added only if event is public
    if event.effective_protection_mode == ProtectionMode.public and event.has_logo:
        cal_event.add('image', f"{config.BASE_URL}{event.logo_url}", {'VALUE': 'URI'})

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
    cal_event.add('description', '\n'.join(description))

    return cal_event


def event_to_ical(event, user=None, detail_level='events'):
    """Serialize an event into an ical.

    :param event: The event to serialize
    :param user: The user who needs to be able to access the events
    """

    return events_to_ical([event], user, detail_level)


def events_to_ical(events, user=None, detail_level='events'):
    """Serialize multiple events into an ical.

    :param events: A list of events to serialize
    :param user: The user who needs to be able to access the events
    """

    calendar = Calendar()
    calendar.add('version', '2.0')
    calendar.add('prodid', '-//CERN//INDICO//EN')

    for event in events:
        event_uid = 'indico-event-{}@{}'.format(event.id, url_parse(config.BASE_URL).host)
        if detail_level == 'events':
            cal_event = generate_event_component(event, event_uid)
            calendar.add_component(cal_event)
        elif detail_level == 'contributions':
            contributions = [
                generate_contribution_component(contribution, event_uid) for contribution in event.contributions
            ]
            for contribution in contributions:
                calendar.add_component(contribution)

    data = calendar.to_ical()

    # check whether the plugins want to add/override any data
    for update in values_from_signal(
        signals.event.metadata_postprocess.send('ical-export', event=event, data=data, user=user),
        as_list=True
    ):
        data.update(update)

    return data
