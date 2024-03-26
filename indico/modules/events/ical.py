# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import timedelta
from email import message
from email.mime.base import MIMEBase
from email.policy import compat32
from urllib.parse import urlsplit

import icalendar
from lxml import html
from lxml.etree import ParserError

from indico.core import signals
from indico.core.config import config
from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.models.events import Event
from indico.modules.events.sessions.models.sessions import Session
from indico.modules.users.models.users import User
from indico.util.date_time import now_utc
from indico.util.enum import IndicoEnum
from indico.util.signals import values_from_signal


class MIMECalendar(MIMEBase):
    """MIME `text/calendar` class which adds the `method=REQUEST` to the Content-Type."""

    def __init__(self, filename: str, payload: str):
        message.Message.__init__(self, policy=compat32)
        self.add_header('Content-Type', 'text/calendar', charset='utf-8', method='REQUEST')
        self.add_header('Content-Disposition', 'attachment', filename=filename)
        self['MIME-Version'] = '1.0'
        self.set_payload(payload)


class CalendarScope(IndicoEnum):
    contribution = 1
    session = 2


def generate_basic_component(
    entity: Event | Session | Contribution,
    uid: str | None = None,
    url: str | None = None,
    title: str | None = None,
    description: str | None = None,
    organizer: tuple[str, str] | None = None
):
    """Generate an iCalendar component with basic common properties.

    :param entity: Event/session/contribution where properties come from
    :param uid: UID for the component
    :param url: URL for the component (defaults to `entity.external_url`)
    :param title: A title for the component
    :param description: A text based description for the component
    :param organizer: ORGANIZER field of the iCalendar object

    :return: iCalendar event with basic properties
    """
    if not title:
        title = entity.title

    if label := getattr(entity, 'label', None):
        title += f' [{label.title}]'

    component = icalendar.Event()

    if organizer:
        component.add('organizer', f'mailto:{organizer[1]}', parameters={'cn': organizer[0]})

    component.add('dtstamp', now_utc(False))
    component.add('dtstart', entity.start_dt)
    component.add('dtend', entity.end_dt)
    component.add('summary', title.strip())

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
        component.add('description', '\n\n'.join(cal_description))

    return component


def generate_event_component(
    event: Event,
    user: User | None = None,
    organizer: tuple[str, str] | None = None,
    skip_access_check: bool | None = False,
):
    """Generate an event icalendar component from an Indico event."""
    uid = f'indico-event-{event.id}@{urlsplit(config.BASE_URL).hostname}'
    component = generate_basic_component(event, uid, organizer=organizer)

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
        signals.event.metadata_postprocess.send('ical-export', event=event, data=data, user=user,
                                                skip_access_check=skip_access_check),
        as_list=True
    ):
        data.update(update)
    if data['description']:
        component['description'] = data['description']

    # If the user exists and the add_icloud_alerts preference isn't blank
    if user and user.settings.get('add_ical_alerts'):
        alarm = icalendar.Alarm()
        alarm.add('action', 'DISPLAY')
        alarm.add('trigger', timedelta(minutes=-user.settings.get('add_ical_alerts_mins')))
        alarm.add('summary', component['summary'])
        if data['description']:
            alarm.add('description', data['description'])
        component.add_component(alarm)

    return component


def event_to_ical(
    event: Event,
    user: User | None = None,
    scope: str | None = None,
    *,
    skip_access_check: bool = False,
    method: str | None = None,
    organizer: tuple[str, str] | None = None
):
    """Serialize an event into an ical.

    :param event: The event to serialize
    :param user: The user who needs to be able to access the events
    :param scope: If specified, use a more detailed timetable using the given scope
    :param skip_access_check: Do not perform access checks. Defaults to False.
    :param method: METHOD field of the iCalendar object
    :param organizer: ORGANIZER field of the iCalendar object
    """
    return events_to_ical([event], user, scope, skip_access_check=skip_access_check, method=method,
                          organizer=organizer)


def events_to_ical(
    events: list[Event],
    user: User | None = None,
    scope: str | None = None,
    *,
    skip_access_check: bool = False,
    method: str | None = None,
    organizer: tuple[str, str] | None = None
):
    """Serialize multiple events into an ical.

    :param events: A list of events to serialize
    :param user: The user who needs to be able to access the events
    :param scope: If specified, use a more detailed timetable using the given scope
    :param skip_access_check: Do not perform access checks. Defaults to False.
    :param method: METHOD field of the iCalendar object
    :param organizer: ORGANIZER field of the iCalendar object
    """
    from indico.modules.events.contributions.ical import generate_contribution_component
    from indico.modules.events.sessions.ical import generate_session_block_component

    calendar = icalendar.Calendar()
    calendar.add('version', '2.0')
    calendar.add('prodid', '-//CERN//INDICO//EN')

    if method:
        calendar.add('method', method)

    for event in events:
        if not skip_access_check and not event.can_access(user):
            continue

        if scope == CalendarScope.contribution and event.contributions_count > 0:
            components = [
                generate_contribution_component(contrib, organizer=organizer)
                for contrib in event.contributions
                if contrib.start_dt and contrib.can_access(user)
            ]
        elif scope == CalendarScope.session and event.session_block_count > 0:
            components = [
                generate_session_block_component(block, organizer=organizer)
                for session in event.sessions
                if session.start_dt and session.can_access(user)
                for block in session.blocks
            ]
            components += [
                generate_contribution_component(contrib, organizer=organizer)
                for contrib in event.contributions
                if contrib.start_dt and contrib.session_id is None and contrib.can_access(user)
            ]
        else:
            components = [
                generate_event_component(event, user, organizer=organizer, skip_access_check=skip_access_check)
            ]

        for component in components:
            calendar.add_component(component)

    return calendar.to_ical()
