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
from indico.util.date_time import now_utc
from indico.util.signals import values_from_signal


def generate_basic_component(entity, uid=None, url=None):
    """Generates an icalendar component with basic common properties.

    :param entity: Event/session/contribution where properties come from
    :param uid: UID for the component
    :param url: URL for the component (defaults to `entity.external_url`)

    :returns: icalendar event with basic properties
    """

    component = Event()

    component.add('dtstamp', now_utc(False))
    component.add('dtstart', entity.start_dt)
    component.add('dtend', entity.end_dt)
    component.add('summary', entity.title)

    if uid:
        component.add('uid', uid)

    if url:
        component.add('url', url)
    elif hasattr(entity, 'external_url'):
        component.add('url', entity.external_url)

    location = (f'{entity.room_name} ({entity.venue_name})'
                if entity.venue_name and entity.room_name
                else (entity.venue_name or entity.room_name))
    if location:
        component.add('location', location)

    # speakers are located in a different variable in contributions
    speaker_list = None
    if hasattr(entity, 'person_links'):
        speaker_list = entity.person_links
    elif hasattr(entity, 'speakers'):
        speaker_list = entity.speakers

    description = []
    if speaker_list:
        speakers = [f'{x.full_name} ({x.affiliation})' if x.affiliation else x.full_name
                    for x in speaker_list]
        description.append('Speakers: {}'.format(', '.join(speakers)))
    if entity.description:
        desc_text = str(entity.description) or '<p/>'  # get rid of RichMarkup
        try:
            description.append(str(html.fromstring(desc_text).text_content()))
        except ParserError:
            # this happens if desc_text only contains a html comment
            pass
    component.add('description', '\n'.join(description))

    return component


def generate_event_component(event):
    """Generates an event icalendar component from an Indico event.

    :param event: The Indico event to use

    :returns: an icalendar Event
    """

    uid = 'indico-event-{}@{}'.format(event.id, url_parse(config.BASE_URL).host)
    component = generate_basic_component(event, uid)

    # add contact title, phones and emails if present
    if event.contact_title:
        contact_info = f'{event.contact_title}'
        if len(event.contact_emails):
            contact_info += f'; {"; ".join(event.contact_emails)}'
        if len(event.contact_phones):
            contact_info += f'; {"; ".join(event.contact_phones)}'
        component.add('contact', contact_info)

    # add logo url if event is public
    if event.effective_protection_mode == ProtectionMode.public and event.has_logo:
        component.add('image', f"{config.BASE_URL}{event.logo_url}", {'VALUE': 'URI'})

    return component


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
    :param detail_level: Determines the level of entities that will end up
                         being exported. Either `events` or `contributions`.
    """

    calendar = Calendar()
    calendar.add('version', '2.0')
    calendar.add('prodid', '-//CERN//INDICO//EN')

    for event in events:
        if detail_level == 'events':
            component = generate_event_component(event)
            calendar.add_component(component)
        elif detail_level == 'contributions':
            from indico.modules.events.contributions.ical import generate_contribution_component
            components = [
                generate_contribution_component(contribution) for contribution in event.contributions
            ]
            for component in components:
                calendar.add_component(component)

    data = calendar.to_ical()

    # check whether the plugins want to add/override any data
    for update in values_from_signal(
        signals.event.metadata_postprocess.send('ical-export', event=event, data=data, user=user),
        as_list=True
    ):
        data.update(update)

    return data
