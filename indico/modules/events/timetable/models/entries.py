# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from datetime import timedelta

from sqlalchemy import DDL
from sqlalchemy.event import listens_for
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm.base import NEVER_SET, NO_VALUE

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime
from indico.core.db.sqlalchemy.util.models import populate_one_to_one_backrefs
from indico.util.date_time import overlaps
from indico.util.i18n import _
from indico.util.locators import locator_property
from indico.util.string import format_repr, return_ascii
from indico.util.struct.enum import RichIntEnum


class TimetableEntryType(RichIntEnum):
    __titles__ = [None, _("Session Block"), _("Contribution"), _("Break")]
    # entries are uppercase since `break` is a keyword...
    SESSION_BLOCK = 1
    CONTRIBUTION = 2
    BREAK = 3


def _make_check(type_, *cols):
    all_cols = {'session_block_id', 'contribution_id', 'break_id'}
    required_cols = all_cols & set(cols)
    forbidden_cols = all_cols - required_cols
    criteria = ['{} IS NULL'.format(col) for col in sorted(forbidden_cols)]
    criteria += ['{} IS NOT NULL'.format(col) for col in sorted(required_cols)]
    condition = 'type != {} OR ({})'.format(type_, ' AND '.join(criteria))
    return db.CheckConstraint(condition, 'valid_{}'.format(type_.name.lower()))


class TimetableEntry(db.Model):
    __tablename__ = 'timetable_entries'

    @declared_attr
    def __table_args__(cls):
        return (db.Index('ix_timetable_entries_start_dt_desc', cls.start_dt.desc()),
                _make_check(TimetableEntryType.SESSION_BLOCK, 'session_block_id'),
                _make_check(TimetableEntryType.CONTRIBUTION, 'contribution_id'),
                _make_check(TimetableEntryType.BREAK, 'break_id'),
                db.CheckConstraint("type != {} OR parent_id IS NULL".format(TimetableEntryType.SESSION_BLOCK),
                                   'valid_parent'),
                {'schema': 'events'})

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        index=True,
        nullable=False
    )
    parent_id = db.Column(
        db.Integer,
        db.ForeignKey('events.timetable_entries.id'),
        index=True,
        nullable=True,
    )
    session_block_id = db.Column(
        db.Integer,
        db.ForeignKey('events.session_blocks.id'),
        index=True,
        unique=True,
        nullable=True
    )
    contribution_id = db.Column(
        db.Integer,
        db.ForeignKey('events.contributions.id'),
        index=True,
        unique=True,
        nullable=True
    )
    break_id = db.Column(
        db.Integer,
        db.ForeignKey('events.breaks.id'),
        index=True,
        unique=True,
        nullable=True
    )
    type = db.Column(
        PyIntEnum(TimetableEntryType),
        nullable=False
    )
    start_dt = db.Column(
        UTCDateTime,
        nullable=False
    )

    event = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'timetable_entries',
            order_by=lambda: TimetableEntry.start_dt,
            cascade='all, delete-orphan',
            lazy='dynamic'
        )
    )
    session_block = db.relationship(
        'SessionBlock',
        lazy=False,
        backref=db.backref(
            'timetable_entry',
            cascade='all, delete-orphan',
            uselist=False,
            lazy=True
        )
    )
    contribution = db.relationship(
        'Contribution',
        lazy=False,
        backref=db.backref(
            'timetable_entry',
            cascade='all, delete-orphan',
            uselist=False,
            lazy=True
        )
    )
    break_ = db.relationship(
        'Break',
        cascade='all, delete-orphan',
        single_parent=True,
        lazy=False,
        backref=db.backref(
            'timetable_entry',
            cascade='all, delete-orphan',
            uselist=False,
            lazy=True
        )
    )
    children = db.relationship(
        'TimetableEntry',
        order_by='TimetableEntry.start_dt',
        lazy=True,
        backref=db.backref(
            'parent',
            remote_side=[id],
            lazy=True
        )
    )

    # relationship backrefs:
    # - parent (TimetableEntry.children)

    @property
    def object(self):
        if self.type == TimetableEntryType.SESSION_BLOCK:
            return self.session_block
        elif self.type == TimetableEntryType.CONTRIBUTION:
            return self.contribution
        elif self.type == TimetableEntryType.BREAK:
            return self.break_

    @object.setter
    def object(self, value):
        from indico.modules.events.contributions import Contribution
        from indico.modules.events.sessions.models.blocks import SessionBlock
        from indico.modules.events.timetable.models.breaks import Break
        self.session_block = self.contribution = self.break_ = None
        if isinstance(value, SessionBlock):
            self.session_block = value
        elif isinstance(value, Contribution):
            self.contribution = value
        elif isinstance(value, Break):
            self.break_ = value
        elif value is not None:
            raise TypeError('Unexpected object: {}'.format(value))

    @hybrid_property
    def duration(self):
        return self.object.duration if self.object is not None else None

    @duration.setter
    def duration(self, value):
        self.object.duration = value

    @duration.expression
    def duration(cls):
        from indico.modules.events.contributions import Contribution
        from indico.modules.events.sessions.models.blocks import SessionBlock
        from indico.modules.events.timetable.models.breaks import Break
        return db.case({
            TimetableEntryType.SESSION_BLOCK.value:
                db.select([SessionBlock.duration])
                .where(SessionBlock.id == cls.session_block_id)
                .correlate_except(SessionBlock)
                .as_scalar(),
            TimetableEntryType.CONTRIBUTION.value:
                db.select([Contribution.duration])
                .where(Contribution.id == cls.contribution_id)
                .correlate_except(Contribution)
                .as_scalar(),
            TimetableEntryType.BREAK.value:
                db.select([Break.duration])
                .where(Break.id == cls.break_id)
                .correlate_except(Break)
                .as_scalar(),
        }, value=cls.type)

    @hybrid_property
    def end_dt(self):
        if self.start_dt is None or self.duration is None:
            return None
        return self.start_dt + self.duration

    @end_dt.expression
    def end_dt(cls):
        return cls.start_dt + cls.duration

    @property
    def session_siblings(self):
        if self.type == TimetableEntryType.SESSION_BLOCK:
            return [x for x in self.siblings
                    if x.session_block and x.session_block.session == self.session_block.session]
        elif self.parent:
            return self.siblings
        else:
            return []

    @property
    def siblings(self):
        from indico.modules.events.timetable.util import get_top_level_entries, get_nested_entries
        tzinfo = self.event.tzinfo
        day = self.start_dt.astimezone(tzinfo).date()
        siblings = (get_nested_entries(self.event)[self.parent_id]
                    if self.parent_id else
                    get_top_level_entries(self.event))
        return [x for x in siblings if x.start_dt.astimezone(tzinfo).date() == day and x.id != self.id]

    @property
    def siblings_query(self):
        tzinfo = self.event.tzinfo
        day = self.start_dt.astimezone(tzinfo).date()
        criteria = (TimetableEntry.id != self.id,
                    TimetableEntry.parent == self.parent,
                    db.cast(TimetableEntry.start_dt.astimezone(tzinfo), db.Date) == day)
        return TimetableEntry.query.with_parent(self.event).filter(*criteria)

    @locator_property
    def locator(self):
        return dict(self.event.locator, entry_id=self.id)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'type', 'start_dt', 'end_dt', _repr=self.object)

    def can_view(self, user):
        """Check whether the user will see this entry in the timetable."""
        if self.type in (TimetableEntryType.CONTRIBUTION, TimetableEntryType.BREAK):
            return self.object.can_access(user)
        elif self.type == TimetableEntryType.SESSION_BLOCK:
            if self.object.can_access(user):
                return True
            return any(x.can_access(user) for x in self.object.contributions)

    def extend_start_dt(self, start_dt):
        assert start_dt < self.start_dt
        extension = self.start_dt - start_dt
        self.start_dt = start_dt
        self.duration = self.duration + extension

    def extend_end_dt(self, end_dt):
        diff = end_dt - self.end_dt
        if diff < timedelta(0):
            raise ValueError("New end_dt is before current end_dt.")
        self.duration += diff

    def extend_parent(self, by_start=True, by_end=True):
        """Extend start/end of parent objects if needed.

        No extension if performed for entries crossing a day boundary in the
        event timezone.

        :param by_start: Extend parent by start datetime.
        :param by_end: Extend parent by end datetime.
        """
        tzinfo = self.event.tzinfo
        if self.start_dt.astimezone(tzinfo).date() != self.end_dt.astimezone(tzinfo).date():
            return
        if self.parent is None:
            if by_start and self.start_dt < self.event.start_dt:
                self.event.start_dt = self.start_dt
            if by_end and self.end_dt > self.event.end_dt:
                self.event.end_dt = self.end_dt
        else:
            extended = False
            if by_start and self.start_dt < self.parent.start_dt:
                self.parent.extend_start_dt(self.start_dt)
                extended = True
            if by_end and self.end_dt > self.parent.end_dt:
                self.parent.extend_end_dt(self.end_dt)
                extended = True
            if extended:
                self.parent.extend_parent(by_start=by_start, by_end=by_end)

    def is_parallel(self, in_session=False):
        siblings = self.siblings if not in_session else self.session_siblings
        for sibling in siblings:
            if overlaps((self.start_dt, self.end_dt), (sibling.start_dt, sibling.end_dt)):
                return True
        return False

    def move(self, start_dt):
        """Move the entry to start at a different time.

        This method automatically moves children of the entry to
        preserve their start time relative to the parent's start time.
        """
        if self.type == TimetableEntryType.SESSION_BLOCK:
            diff = start_dt - self.start_dt
            for child in self.children:
                child.start_dt += diff
        self.start_dt = start_dt

    def move_next_to(self, sibling, position='before'):
        if sibling not in self.siblings:
            raise ValueError("Not a sibling")
        if position not in ('before', 'after'):
            raise ValueError("Invalid position")
        if position == 'before':
            start_dt = sibling.start_dt - self.duration
        else:
            start_dt = sibling.end_dt
        self.move(start_dt)


@listens_for(TimetableEntry.__table__, 'after_create')
def _add_timetable_consistency_trigger(target, conn, **kw):
    sql = """
        CREATE CONSTRAINT TRIGGER consistent_timetable
        AFTER INSERT OR UPDATE
        ON {}
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW
        EXECUTE PROCEDURE events.check_timetable_consistency('timetable_entry');
    """.format(target.fullname)
    DDL(sql).execute(conn)


@listens_for(TimetableEntry.session_block, 'set')
def _set_session_block(target, value, *unused):
    target.type = TimetableEntryType.SESSION_BLOCK


@listens_for(TimetableEntry.contribution, 'set')
def _set_contribution(target, value, *unused):
    target.type = TimetableEntryType.CONTRIBUTION


@listens_for(TimetableEntry.break_, 'set')
def _set_break(target, value, *unused):
    target.type = TimetableEntryType.BREAK


@listens_for(TimetableEntry.start_dt, 'set')
def _set_start_dt(target, value, oldvalue, *unused):
    from indico.modules.events.util import register_time_change
    if oldvalue in (NEVER_SET, NO_VALUE):
        return
    if value != oldvalue and target.object is not None:
        register_time_change(target)


populate_one_to_one_backrefs(TimetableEntry, 'session_block', 'contribution', 'break_')
