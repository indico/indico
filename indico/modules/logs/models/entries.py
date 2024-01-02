# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from sqlalchemy.dialects.postgresql import JSON, JSONB
from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime
from indico.core.db.sqlalchemy.util.models import auto_table_args
from indico.util.date_time import now_utc
from indico.util.decorators import strict_classproperty
from indico.util.enum import IndicoIntEnum, RichIntEnum
from indico.util.i18n import _
from indico.util.string import format_repr


class EventLogRealm(RichIntEnum):
    __titles__ = (None, _('Event'), _('Management'), _('Participants'), _('Reviewing'), _('Emails'))
    event = 1
    management = 2
    participants = 3
    reviewing = 4
    emails = 5


class CategoryLogRealm(RichIntEnum):
    __titles__ = (None, _('Category'), _('Events'))
    category = 1
    events = 2


class LogKind(IndicoIntEnum):
    other = 1
    positive = 2
    change = 3
    negative = 4


class LogEntryBase(db.Model):
    """Base model for log entries."""

    __abstract__ = True
    __tablename__ = 'logs'

    @strict_classproperty
    @classmethod
    def __auto_table_args(cls):
        return (db.Index(None, 'meta', postgresql_using='gin'),)

    user_backref_name = None
    link_fk_name = None

    @declared_attr
    def __table_args__(cls):
        return auto_table_args(cls)

    #: The ID of the log entry
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The date/time when the reminder was created
    logged_dt = db.Column(
        UTCDateTime,
        nullable=False,
        default=now_utc
    )
    #: The general kind of operation that was performed
    kind = db.Column(
        PyIntEnum(LogKind),
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
    #: Non-displayable data
    meta = db.Column(
        JSONB,
        nullable=False
    )

    @declared_attr
    def user_id(cls):
        """The ID of the user associated with the entry."""
        return db.Column(
            db.Integer,
            db.ForeignKey('users.users.id'),
            index=True,
            nullable=True
        )

    @declared_attr
    def user(cls):
        """The user associated with the log entry."""
        return db.relationship(
            'User',
            lazy=False,
            backref=db.backref(
                cls.user_backref_name,
                lazy='dynamic'
            )
        )

    @property
    def logged_date(self):
        return self.logged_dt.astimezone(self.event.tzinfo).date()

    @property
    def renderer(self):
        from indico.modules.logs.util import get_log_renderers
        return get_log_renderers().get(self.type)

    def render(self):
        """Render the log entry to be displayed.

        If the renderer is not available anymore, e.g. because of a
        disabled plugin, ``None`` is returned.
        """
        renderer = self.renderer
        return renderer.render_entry(self) if renderer else None

    def __repr__(self):
        return format_repr(self, 'id', type(self).link_fk_name, 'logged_dt', 'realm', 'module', _text=self.summary)


class EventLogEntry(LogEntryBase):
    """Log entries for events."""

    __auto_table_args = {'schema': 'events'}
    user_backref_name = 'event_log_entries'
    link_fk_name = 'event_id'

    #: The ID of the event
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        index=True,
        nullable=False
    )
    #: The general area of the event the entry comes from
    realm = db.Column(
        PyIntEnum(EventLogRealm),
        nullable=False
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


class CategoryLogEntry(LogEntryBase):
    """Log entries for categories."""

    __auto_table_args = {'schema': 'categories'}
    user_backref_name = 'category_log_entries'
    link_fk_name = 'category_id'

    #: The ID of the category
    category_id = db.Column(
        db.Integer,
        db.ForeignKey('categories.categories.id'),
        index=True,
        nullable=False
    )
    #: The general area of the event the entry comes from
    realm = db.Column(
        PyIntEnum(CategoryLogRealm),
        nullable=False
    )

    #: The Category this log entry is associated with
    event = db.relationship(
        'Category',
        lazy=True,
        backref=db.backref(
            'log_entries',
            lazy='dynamic'
        )
    )
