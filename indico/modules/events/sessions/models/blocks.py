# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from sqlalchemy import DDL
from sqlalchemy.event import listens_for
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm.base import NEVER_SET, NO_VALUE

from indico.core.db import db
from indico.core.db.sqlalchemy.locations import LocationMixin
from indico.core.db.sqlalchemy.util.models import auto_table_args
from indico.modules.events.timetable.models.entries import TimetableEntry
from indico.util.locators import locator_property
from indico.util.string import format_repr, slugify


class SessionBlock(LocationMixin, db.Model):
    __tablename__ = 'session_blocks'
    __auto_table_args = (db.UniqueConstraint('id', 'session_id'),  # useless but needed for the compound fkey
                         db.CheckConstraint("date_trunc('minute', duration) = duration", 'duration_no_seconds'),
                         {'schema': 'events'})
    location_backref_name = 'session_blocks'

    @declared_attr
    def __table_args__(cls):
        return auto_table_args(cls)

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    session_id = db.Column(
        db.Integer,
        db.ForeignKey('events.sessions.id'),
        index=True,
        nullable=False
    )
    title = db.Column(
        db.String,
        nullable=False,
        default=''
    )
    code = db.Column(
        db.String,
        nullable=False,
        default=''
    )
    duration = db.Column(
        db.Interval,
        nullable=False
    )

    #: Persons associated with this session block
    person_links = db.relationship(
        'SessionBlockPersonLink',
        lazy=True,
        cascade='all, delete-orphan',
        backref=db.backref(
            'session_block',
            lazy=True
        )
    )

    # relationship backrefs:
    # - contributions (Contribution.session_block)
    # - legacy_mapping (LegacySessionBlockMapping.session_block)
    # - room_reservation_links (ReservationLink.session_block)
    # - session (Session.blocks)
    # - timetable_entry (TimetableEntry.session_block)
    # - vc_room_associations (VCRoomEventAssociation.linked_block)

    @declared_attr
    def contribution_count(cls):
        from indico.modules.events.contributions.models.contributions import Contribution
        query = (db.select([db.func.count(Contribution.id)])
                 .where((Contribution.session_block_id == cls.id) & ~Contribution.is_deleted)
                 .correlate_except(Contribution)
                 .scalar_subquery())
        return db.column_property(query, deferred=True)

    def __init__(self, **kwargs):
        # explicitly initialize those relationships with None to avoid
        # an extra query to check whether there is an object associated
        # when assigning a new one (e.g. during cloning)
        kwargs.setdefault('timetable_entry', None)
        super().__init__(**kwargs)

    @property
    def event(self):
        return self.session.event

    @locator_property
    def locator(self):
        return dict(self.session.locator, block_id=self.id)

    @property
    def location_parent(self):
        return self.session

    def can_access(self, user, allow_admin=True):
        return self.session.can_access(user, allow_admin=allow_admin)

    @property
    def has_note(self):
        return self.session.has_note

    @property
    def note(self):
        return self.session.note

    @property
    def full_title(self):
        return f'{self.session.title}: {self.title}' if self.title else self.session.title

    def can_manage(self, user, allow_admin=True):
        return self.session.can_manage_blocks(user, allow_admin=allow_admin)

    def can_manage_attachments(self, user):
        return self.session.can_manage_attachments(user)

    def can_edit_note(self, user):
        return self.session.can_edit_note(user)

    @hybrid_property
    def start_dt(self):
        return self.timetable_entry.start_dt if self.timetable_entry else None

    @start_dt.expression
    def start_dt(cls):
        return (db.select([TimetableEntry.start_dt])
                .where(TimetableEntry.session_block_id == cls.id)
                .as_scalar())

    @hybrid_property
    def end_dt(self):
        return self.timetable_entry.start_dt + self.duration if self.timetable_entry else None

    @end_dt.expression
    def end_dt(cls):
        return cls.start_dt + cls.duration

    @property
    def slug(self):
        return slugify('b', self.id, self.session.title, self.title, maxlen=30)

    def __repr__(self):
        return format_repr(self, 'id', _text=self.title or None)

    def log(self, *args, **kwargs):
        """Log with prefilled metadata for the session block."""
        return self.event.log(*args, meta={'session_block_id': self.id}, **kwargs)


SessionBlock.register_location_events()


@listens_for(SessionBlock.duration, 'set')
def _set_duration(target, value, oldvalue, *unused):
    from indico.modules.events.util import register_time_change
    if oldvalue in (NEVER_SET, NO_VALUE):
        return
    if value != oldvalue and target.timetable_entry is not None:
        register_time_change(target.timetable_entry)


@listens_for(SessionBlock.__table__, 'after_create')
def _add_timetable_consistency_trigger(target, conn, **kw):
    sql = '''
        CREATE CONSTRAINT TRIGGER consistent_timetable
        AFTER INSERT OR UPDATE OF session_id, duration
        ON {}
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW
        EXECUTE PROCEDURE events.check_timetable_consistency('session_block');
    '''.format(target.fullname)
    DDL(sql).execute(conn)
