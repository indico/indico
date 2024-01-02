# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from collections import defaultdict
from io import BytesIO

from flask import session
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Table, TableStyle
from sqlalchemy.orm import contains_eager, joinedload, load_only, noload

from indico.core.db import db
from indico.legacy.pdfinterface.base import Paragraph, PDFBase
from indico.modules.events import Event
from indico.modules.events.sessions.models.principals import SessionPrincipal
from indico.modules.events.sessions.models.sessions import Session
from indico.util.i18n import _
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


class SessionListToPDF(PDFBase):
    def __init__(self, sessions):
        PDFBase.__init__(self, story=[])
        self.sessions = sessions
        self.PAGE_WIDTH, self.PAGE_HEIGHT = landscape(A4)

    def getBody(self, story=None):  # noqa: N802
        story = story or self._story
        header_style = ParagraphStyle(name='header_style', fontSize=12, alignment=TA_CENTER)
        story.append(Paragraph('<b>{}</b>'.format(_('List of sessions')), header_style))

        text_style = ParagraphStyle(name='text_style', fontSize=8, alignment=TA_LEFT, leading=10, leftIndent=10)
        text_style.fontName = 'Times-Roman'
        text_style.spaceBefore = 0
        text_style.spaceAfter = 0
        text_style.firstLineIndent = 0

        headers = [
            Paragraph(f'<b>{col}</b>', text_style)
            for col in (_('ID'), _('Type'), _('Title'), _('Code'), _('Description'))
        ]
        rows = [headers]
        rows.extend([
            Paragraph(sess.friendly_id, text_style),
            Paragraph(sess.type.name if sess.type else '', text_style),
            Paragraph(sess.title, text_style),
            Paragraph(sess.code, text_style),
            Paragraph(sess.description, text_style)
        ] for sess in self.sessions)

        col_widths = (None,) * 5
        table_style = TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT')
        ])
        story.append(Table(rows, colWidths=col_widths, style=table_style))
        return story


def generate_pdf_from_sessions(sessions):
    """Generate a PDF file from a given session list."""
    pdf = SessionListToPDF(sessions)
    return BytesIO(pdf.getPDFBin())


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
                                                    SessionPrincipal.user == user))))


def get_sessions_for_user(event, user):
    return (_query_sessions_for_user(event, user)
            .options(joinedload('acl_entries'))
            .order_by(db.func.lower(Session.title))
            .all())


def has_sessions_for_user(event, user):
    return _query_sessions_for_user(event, user).has_rows()


def get_session_timetable_pdf(sess, **kwargs):
    from indico.legacy.pdfinterface.conference import TimetablePDFFormat, TimeTablePlain
    pdf_format = TimetablePDFFormat(params={'coverPage': False})
    return TimeTablePlain(sess.event, session.user, showSessions=[sess.id], showDays=[],
                          sortingCrit=None, ttPDFFormat=pdf_format, pagesize='A4', fontsize='normal',
                          firstPageNumber=1, showSpeakerAffiliation=False, **kwargs)


def render_session_type_row(session_type):
    template = get_template_module('events/sessions/management/_types_table.html')
    return template.types_table_row(session_type=session_type)
