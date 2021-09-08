# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import icalendar
from lxml import html
from lxml.etree import ParserError
from werkzeug.urls import url_parse

from indico.core import signals
from indico.core.config import config
from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.util.date_time import now_utc
from indico.util.enum import IndicoEnum
from indico.util.signals import values_from_signal


class CalendarScope(IndicoEnum):
    contribution = 1
    session = 2


def generate_basic_component(entity, uid=None, url=None, title=None, description=None):
    """Generate an iCalendar component with basic common properties.

    :param entity: Event/session/contribution where properties come from
    :param uid: UID for the component
    :param url: URL for the component (defaults to `entity.external_url`)
    :param title: A title for the component
    :param description: A text based description for the component

    :return: iCalendar event with basic properties
    """
    component = icalendar.Event()

    component.add('dtstamp', now_utc(False))
    component.add('dtstart', entity.start_dt)
    component.add('dtend', entity.end_dt)
    component.add('summary', title or entity.title)

    if uid:
        component.add('uid', uid)

    if not url and hasattr(entity, 'external_url'):
        url = entity.external_url
    if url:
        component.add('url', url)

    location = (f'{entity.room_name} ({entity.venue_name})'
                if entity.venue_name and entity.room_name
                else (entity.venue_name or entity.room_name))
    if location:
        component.add('location', location)

    speaker_list = getattr(entity, 'person_links', [])
    cal_description = []
    if speaker_list:
        speakers = [f'{x.full_name} ({x.affiliation})' if x.affiliation else x.full_name
                    for x in speaker_list]
        cal_description.append('Speakers: {}'.format(', '.join(speakers)))
    if description is None:
        description = getattr(entity, 'description', None)
    if description:
        desc_text = str(description) or '<p/>'  # get rid of RichMarkup
        try:
            cal_description.append(str(html.fromstring(desc_text).text_content()))
        except ParserError:
            # this happens if desc_text only contains a html comment
            pass
    if url:
        cal_description.append(url)
    if cal_description:
        component.add('description', '\n'.join(cal_description))

    return component


def generate_event_component(event, user=None):
    """Generate an event icalendar component from an Indico event."""
    uid = f'indico-event-{event.id}@{url_parse(config.BASE_URL).host}'
    component = generate_basic_component(event, uid)

    # add contact information
    contact_info = event.contact_emails + event.contact_phones
    if contact_info:
        component.add('contact', ';'.join(contact_info))

    # add logo url if event is public
    if event.effective_protection_mode == ProtectionMode.public and event.has_logo:
        component.add('image', event.external_logo_url, {'VALUE': 'URI'})

    # send description to plugins in case one wants to add anything to it
    data = {'description': component.get('description', '')}
    for update in values_from_signal(
        signals.event.metadata_postprocess.send('ical-export', event=event, data=data, user=user),
        as_list=True
    ):
        data.update(update)
    if data['description']:
        component['description'] = data['description']

    return component


def event_to_ical(event, user=None, scope=None, *, skip_access_check=False):
    """Serialize an event into an ical.

    :param event: The event to serialize
    :param user: The user who needs to be able to access the events
    :param scope: If specified, use a more detailed timetable using the given scope
    :param skip_access_check: Do not perform access checks. Defaults to False.
    """
    return events_to_ical([event], user, scope, skip_access_check=skip_access_check)


def events_to_ical(events, user=None, scope=None, *, skip_access_check=False):
    """Serialize multiple events into an ical.

    :param events: A list of events to serialize
    :param user: The user who needs to be able to access the events
    :param scope: If specified, use a more detailed timetable using the given scope
    :param skip_access_check: Do not perform access checks. Defaults to False.
    """
    from indico.modules.events.contributions.ical import generate_contribution_component
    from indico.modules.events.sessions.ical import generate_session_block_component

    calendar = icalendar.Calendar()
    calendar.add('version', '2.0')
    calendar.add('prodid', '-//CERN//INDICO//EN')

    for event in events:
        if not skip_access_check and not event.can_access(user):
            continue

        if scope == CalendarScope.contribution:
            components = [
                generate_contribution_component(contrib)
                for contrib in event.contributions
                if contrib.start_dt and contrib.can_access(user)
            ]
        elif scope == CalendarScope.session:
            components = [
                generate_session_block_component(block)
                for session in event.sessions
                if session.start_dt and session.can_access(user)
                for block in session.blocks
            ]
            components += [
                generate_contribution_component(contrib)
                for contrib in event.contributions
                if contrib.start_dt and contrib.session_id is None and contrib.can_access(user)
            ]
        else:
            components = [generate_event_component(event, user)]

        for component in components:
            calendar.add_component(component)

    return calendar.to_ical()
