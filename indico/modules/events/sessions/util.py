# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from collections import defaultdict

from flask import render_template
from sqlalchemy.orm import contains_eager, joinedload, load_only, noload

from indico.core.db import db
from indico.core.db.sqlalchemy.principals import PrincipalType
from indico.modules.events import Event
from indico.modules.events.sessions.models.principals import SessionPrincipal
from indico.modules.events.sessions.models.sessions import Session
from indico.web.flask.templating import get_template_module


def can_manage_sessions(user, event, permission=None):
    """Check whether a user can manage any sessions in an event."""
    if event.can_manage(user):
        return True
    return any(s.can_manage(user, permission)
               for s in Session.query.with_parent(event).options(joinedload('acl_entries')))


def generate_spreadsheet_from_sessions(sessions):
    """Generate spreadsheet data from a given session list.

    :param sessions: The sessions to include in the spreadsheet
    """
    column_names = ['ID', 'Title', 'Description', 'Type', 'Code']
    rows = [{'ID': sess.friendly_id,
             'Title': sess.title,
             'Description': sess.description,
             'Type': sess.type.name if sess.type else None,
             'Code': sess.code}
            for sess in sessions]
    return column_names, rows


def generate_pdf_from_sessions(event, sessions):
    """Generate a PDF file from a given session list."""
    from indico.modules.events.timetable.util import create_pdf
    css = render_template('events/sessions/pdf/session_table.css')
    html = render_template('events/sessions/pdf/session_table.html', event=event, sessions=sessions)
    return create_pdf(html, css, event)


def session_coordinator_priv_enabled(event, priv):
    """Check whether a coordinator privilege is enabled.

    Currently the following privileges are available:

    - manage-contributions
    - manage-blocks

    :param event: The `Event` to check for
    :param priv: The name of the privilege
    """
    from indico.modules.events.sessions import COORDINATOR_PRIV_SETTINGS, session_settings
    return session_settings.get(event, COORDINATOR_PRIV_SETTINGS[priv])


def get_events_with_linked_sessions(user, dt=None):
    """
    Return a dict with keys representing event_id and the values containing
    data about the user rights for sessions within the event.

    :param user: A `User`
    :param dt: Only include events taking place on/after that date
    """
    query = (user.in_session_acls
             .options(load_only('session_id', 'permissions', 'full_access', 'read_access'))
             .options(noload('*'))
             .options(contains_eager(SessionPrincipal.session).load_only('event_id'))
             .join(Session)
             .join(Event, Event.id == Session.event_id)
             .filter(~Session.is_deleted, ~Event.is_deleted, Event.ends_after(dt)))
    data = defaultdict(set)
    for principal in query:
        roles = data[principal.session.event_id]
        if 'coordinate' in principal.permissions:
            roles.add('session_coordinator')
        if 'submit' in principal.permissions:
            roles.add('session_submission')
        if principal.full_access:
            roles.add('session_manager')
        if principal.read_access:
            roles.add('session_access')
    return data


def _query_sessions_for_user(event, user):
    return (Session.query.with_parent(event)
            .filter(Session.acl_entries.any(db.and_(SessionPrincipal.has_management_permission('coordinate'),
                                                    SessionPrincipal.type == PrincipalType.user,
                                                    SessionPrincipal.user == user))))


def get_sessions_for_user(event, user):
    if user is None:
        return []
    return (_query_sessions_for_user(event, user)
            .options(joinedload('acl_entries'))
            .order_by(db.func.lower(Session.title))
            .all())


def has_sessions_for_user(event, user):
    return user is not None and _query_sessions_for_user(event, user).has_rows()


def generate_session_pdf_timetable(sess):
    from indico.modules.events.timetable.util import TimetableExportConfig, generate_pdf_timetable
    config = TimetableExportConfig(show_toc=False)
    return generate_pdf_timetable(sess.event, config, only_session=sess)


def render_session_type_row(session_type):
    template = get_template_module('events/sessions/management/_types_table.html')
    return template.types_table_row(session_type=session_type)
