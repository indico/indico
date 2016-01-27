# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from collections import defaultdict
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Table, TableStyle
from sqlalchemy.orm import joinedload, load_only, contains_eager, noload

from indico.core.db import db
from indico.core.db.sqlalchemy.colors import ColorTuple
from indico.modules.events import Event
from indico.modules.events.sessions.models.sessions import Session
from indico.modules.events.sessions.models.principals import SessionPrincipal
from indico.modules.fulltextindexes.models.events import IndexedEvent
from indico.util.i18n import _
from MaKaC.PDFinterface.base import PDFBase, Paragraph


def get_colors():
    return [
        ColorTuple('#1D041F', '#EEE0EF'),
        ColorTuple('#253F08', '#E3F2D3'),
        ColorTuple('#1F1F02', '#FEFFBF'),
        ColorTuple('#202020', '#DFE555'),
        ColorTuple('#1F1D04', '#FFEC1F'),
        ColorTuple('#0F264F', '#DFEBFF'),
        ColorTuple('#EFF5FF', '#0D316F'),
        ColorTuple('#F1FFEF', '#1A3F14'),
        ColorTuple('#FFFFFF', '#5F171A'),
        ColorTuple('#272F09', '#D9DFC3'),
        ColorTuple('#FFEFFF', '#4F144E'),
        ColorTuple('#FFEDDF', '#6F390D'),
        ColorTuple('#021F03', '#8EC473'),
        ColorTuple('#03070F', '#92B6DB'),
        ColorTuple('#151515', '#DFDFDF'),
        ColorTuple('#1F1100', '#ECC495'),
        ColorTuple('#0F0202', '#B9CBCA'),
        ColorTuple('#0D1E1F', '#C2ECEF'),
        ColorTuple('#000000', '#D0C296'),
        ColorTuple('#202020', '#EFEBC2')
    ]


def query_active_sessions(event):
    return (event.sessions
            .filter_by(is_deleted=False)
            .order_by(db.func.lower(Session.title)))


def can_manage_sessions(user, event, role=None):
    """Check whether a user can manage any sessions in an event"""
    return event.can_manage(user) or any(s.can_manage(user, role)
                                         for s in event.sessions.options(joinedload('acl_entries')))


def generate_spreadsheet_from_sessions(sessions):
    """Generate spreadsheet data from a given session list.

    :param sessions: The sessions to include in the spreadsheet
    """
    column_names = ['ID', 'Title', 'Description', 'Code']
    rows = [{'ID': sess.friendly_id, 'Title': sess.title, 'Description': sess.description, 'Code': sess.code}
            for sess in sessions]
    return column_names, rows


class SessionListToPDF(PDFBase):
    def __init__(self, conf, sessions):
        PDFBase.__init__(self, story=[])
        self.conf = conf
        self.sessions = sessions
        self.PAGE_WIDTH, self.PAGE_HEIGHT = landscape(A4)

    def getBody(self, story=None):
        story = story or self._story
        header_style = ParagraphStyle(name='header_style', fontSize=12, alignment=TA_CENTER)
        story.append(Paragraph('<b>{}</b>'.format(_('List of sessions')), header_style))

        text_style = ParagraphStyle(name='text_style', fontSize=8, alignment=TA_LEFT, leading=10, leftIndent=10)
        text_style.fontName = 'Times-Roman'
        text_style.spaceBefore = 0
        text_style.spaceAfter = 0
        text_style.firstLineIndent = 0

        rows = []
        row_values = []
        for col in [_('ID'), _('Type'), _('Title'), _('Code'), _('Description')]:
            row_values.append(Paragraph('<b>{}</b>'.format(col), text_style))
        rows.append(row_values)

        for sess in self.sessions:
            rows.append([
                Paragraph(sess.friendly_id, text_style),
                Paragraph(_('Poster') if sess.is_poster else _('Standard'), text_style),
                Paragraph(sess.title.encode('utf-8'), text_style),
                Paragraph(sess.code.encode('utf-8'), text_style),
                Paragraph(sess.description.encode('utf-8'), text_style)
            ])

        col_widths = (None,) * 5
        table_style = TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT')
        ])
        story.append(Table(rows, colWidths=col_widths, style=table_style))
        return story


def generate_pdf_from_sessions(event, sessions):
    """Generate a PDF file from a given session list"""
    pdf = SessionListToPDF(event.as_legacy, sessions)
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


def get_events_with_linked_sessions(user, from_dt=None, to_dt=None):
    """Returns a dict with keys representing event_id and the values containing
    data about the user rights for sessions within the event

    :param user: A `User`
    :param from_dt: The earliest event start time to look for
    :param to_dt: The latest event start time to look for
    """
    event_date_filter = None
    if from_dt and to_dt:
        event_date_filter = IndexedEvent.start_date.between(from_dt, to_dt)
    elif from_dt:
        event_date_filter = IndexedEvent.start_date >= from_dt
    elif to_dt:
        event_date_filter = IndexedEvent.start_date <= to_dt

    query = (user.in_session_acls
             .options(load_only('session_id', 'roles', 'full_access', 'read_access'))
             .options(noload('*'))
             .options(contains_eager(SessionPrincipal.session).load_only('event_id'))
             .join(Session)
             .join(Event, Event.id == Session.event_id)
             .filter(~Session.is_deleted, ~Event.is_deleted))
    if event_date_filter is not None:
        query = query.join(IndexedEvent, IndexedEvent.id == Session.event_id)
        query = query.filter(event_date_filter)
    data = defaultdict(set)
    for principal in query:
        roles = data[principal.session.event_id]
        if 'coordinate' in principal.roles:
            roles.add('session_coordinator')
        if 'submit' in principal.roles:
            roles.add('session_submission')
        if principal.full_access:
            roles.add('session_manager')
        if principal.read_access:
            roles.add('session_access')
    return data
