# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime
from indico.util.date_time import now_utc
from indico.util.enum import RichIntEnum
from indico.util.locators import locator_property


class MoveRequestState(RichIntEnum):
    pending = 0
    accepted = 1
    rejected = 2
    withdrawn = 3


class EventMoveRequest(db.Model):
    """A request that represents a proposed event move."""

    __tablename__ = 'event_move_requests'
    __table_args__ = (db.Index(None, 'event_id', unique=True,
                               postgresql_where=db.text(f'state = {MoveRequestState.pending}')),
                      db.CheckConstraint(f'state in ({MoveRequestState.accepted}, {MoveRequestState.rejected}) '
                                         f'AND moderator_id IS NOT NULL OR moderator_id IS NULL',
                                         'moderator_state'),
                      {'schema': 'categories'})

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    event_id = db.Column(
        db.ForeignKey('events.events.id'),
        nullable=False,
        index=True
    )
    category_id = db.Column(
        db.ForeignKey('categories.categories.id'),
        nullable=True,
        index=True
    )
    submitter_id = db.Column(
        db.ForeignKey('users.users.id'),
        nullable=True,
        index=True
    )
    state = db.Column(
        PyIntEnum(MoveRequestState),
        default=MoveRequestState.pending,
        nullable=False
    )
    state_reason = db.Column(
        db.String,
        nullable=True
    )
    moderator_id = db.Column(
        db.ForeignKey('users.users.id'),
        nullable=True
    )
    submitted_dt = db.Column(
        UTCDateTime,
        nullable=False,
        default=now_utc
    )

    event = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'move_requests',
            cascade='all, delete-orphan',
            lazy='dynamic'
        )
    )
    category = db.relationship(
        'Category',
        lazy=True,
        backref=db.backref(
            'event_move_requests',
            cascade='all, delete-orphan',
            lazy='dynamic'
        )
    )
    submitter = db.relationship(
        'User',
        lazy=True,
        foreign_keys=submitter_id,
        backref=db.backref(
            'event_move_requests',
            lazy='dynamic'
        )
    )
    moderator = db.relationship(
        'User',
        lazy=False,
        foreign_keys=moderator_id,
        backref=db.backref(
            'moderated_event_move_requests',
            lazy='dynamic'
        )
    )

    @locator_property
    def locator(self):
        return dict(self.event.locator, request_id=self.id)

    def withdraw(self, user=None):
        from indico.modules.events import EventLogRealm
        from indico.modules.logs import LogKind
        assert self.state == MoveRequestState.pending
        self.state = MoveRequestState.withdrawn
        db.session.flush()
        self.event.log(EventLogRealm.event, LogKind.change, 'Event', 'Move request withdrawn', user=user)
