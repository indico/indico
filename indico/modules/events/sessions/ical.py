# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import typing as t

import icalendar
from werkzeug.urls import url_parse

from indico.core.config import config
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.ical import generate_basic_component
from indico.modules.events.sessions.models.blocks import SessionBlock
from indico.modules.events.sessions.models.sessions import Session
from indico.modules.users.models.users import User
from indico.web.flask.util import url_for


def generate_session_component(
    session: Session,
    related_to_uid: t.Optional[str] = None,
    organizer: t.Optional[t.Tuple[str, str]] = None
):
    """Generate an Event iCalendar component from an Indico Session."""
    uid = f'indico-session-{session.id}@{url_parse(config.BASE_URL).host}'
    url = url_for('sessions.display_session', session, _external=True)
    component = generate_basic_component(session, uid, url, organizer=organizer)

    if related_to_uid:
        component.add('related-to', related_to_uid)

    return component


def generate_session_block_component(
    block: SessionBlock,
    related_to_uid: t.Optional[str] = None,
    organizer: t.Optional[t.Tuple[str, str]] = None
):
    """Generate an Event iCalendar component for a session block in an Indico Session."""
    uid = f'indico-session-block-{block.id}@{url_parse(config.BASE_URL).host}'
    url = url_for('sessions.display_session', block.session, _external=True)
    component = generate_basic_component(
        block, uid, url, title=block.full_title, description=block.session.description, organizer=organizer
    )

    if related_to_uid:
        component.add('related-to', related_to_uid)

    return component


def session_to_ical(
    session: Session,
    user: t.Optional[User] = None,
    detailed: bool = False,
    organizer: t.Optional[t.Tuple[str, str]] = None
):
    """Serialize a session into an iCal.

    :param session: The session to serialize
    :param detailed: If True, iCal will include the session's contributions
    :param organizer: ORGANIZER field of the iCalendar object
    """
    calendar = icalendar.Calendar()
    calendar.add('version', '2.0')
    calendar.add('prodid', '-//CERN//INDICO//EN')

    related_event_uid = f'indico-event-{session.event.id}@{url_parse(config.BASE_URL).host}'

    if not detailed and session.blocks:
        component = generate_session_component(session, related_event_uid, organizer=organizer)
        calendar.add_component(component)
    elif detailed:
        from indico.modules.events.contributions.ical import generate_contribution_component

        contributions = (Contribution.query.with_parent(session)
                         .filter(Contribution.is_scheduled)
                         .all())
        components = [generate_contribution_component(contribution, related_event_uid, organizer=organizer)
                      for contribution in contributions
                      if contribution.can_access(user)]
        for component in components:
            calendar.add_component(component)

    return calendar.to_ical()
