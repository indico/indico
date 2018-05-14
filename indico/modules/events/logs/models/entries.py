# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from sqlalchemy.dialects.postgresql import JSON

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime
from indico.util.date_time import now_utc
from indico.util.i18n import _
from indico.util.string import return_ascii
from indico.util.struct.enum import IndicoEnum, RichIntEnum


class EventLogRealm(RichIntEnum):
    __titles__ = (None, _('Event'), _('Management'), _('Participants'), _('Reviewing'), _('Emails'))
    event = 1
    management = 2
    participants = 3
    reviewing = 4
    emails = 5


class EventLogKind(int, IndicoEnum):
    other = 1
    positive = 2
    change = 3
    negative = 4


class EventLogEntry(db.Model):
    """Log entries for events"""
    __tablename__ = 'logs'
    __table_args__ = {'schema': 'events'}

    #: The ID of the log entry
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The ID of the event
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        index=True,
        nullable=False
    )
    #: The ID of the user associated with the entry
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        index=True,
        nullable=True
    )
    #: The date/time when the reminder was created
    logged_dt = db.Column(
        UTCDateTime,
        nullable=False,
        default=now_utc
    )
    #: The general area of the event the entry comes from
    realm = db.Column(
        PyIntEnum(EventLogRealm),
        nullable=False
    )
    #: The general kind of operation that was performed
    kind = db.Column(
        PyIntEnum(EventLogKind),
        nullable=False
    )
    #: The module the operation was related to (does not need to match
    #: something in indico.modules and should be human-friendly but not
    #: translated).
    module = db.Column(
        db.String,
        nullable=False
    )
    #: The type of the log entry. This needs to match the name of a log renderer.
    type = db.Column(
        db.String,
        nullable=False
    )
    #: A short one-line description of the logged action.
    #: Should not be translated!
    summary = db.Column(
        db.String,
        nullable=False
    )
    #: Type-specific data
    data = db.Column(
        JSON,
        nullable=False
    )

    #: The user associated with the log entry
    user = db.relationship(
        'User',
        lazy=False,
        backref=db.backref(
            'event_log_entries',
            lazy='dynamic'
        )
    )
    #: The Event this log entry is associated with
    event = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'log_entries',
            lazy='dynamic'
        )
    )

    @property
    def logged_date(self):
        return self.logged_dt.astimezone(self.event.tzinfo).date()

    @property
    def renderer(self):
        from indico.modules.events.logs.util import get_log_renderers
        return get_log_renderers().get(self.type)

    def render(self):
        """Renders the log entry to be displayed.

        If the renderer is not available anymore, e.g. because of a
        disabled plugin, ``None`` is returned.
        """
        renderer = self.renderer
        return renderer.render_entry(self) if renderer else None

    @return_ascii
    def __repr__(self):
        realm = self.realm.name if self.realm is not None else None
        return '<EventLogEntry({}, {}, {}, {}, {}): {}>'.format(self.id, self.event_id, self.logged_dt, realm,
                                                                self.module, self.summary)
