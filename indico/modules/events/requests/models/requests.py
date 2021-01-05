# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from sqlalchemy.dialects.postgresql import JSONB

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime
from indico.core.db.sqlalchemy.util.queries import limit_groups
from indico.modules.events.requests import get_request_definitions
from indico.util.date_time import now_utc
from indico.util.i18n import _
from indico.util.string import return_ascii
from indico.util.struct.enum import RichIntEnum


class RequestState(RichIntEnum):
    __titles__ = [_('Pending'), _('Accepted'), _('Rejected'), _('Withdrawn')]
    pending = 0
    accepted = 1
    rejected = 2
    withdrawn = 3


class Request(db.Model):
    """Event-related requests, e.g. for a webcast."""
    __tablename__ = 'requests'
    __table_args__ = {'schema': 'events'}

    #: request ID
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: ID of the event
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        index=True,
        nullable=False
    )
    #: the request type name
    type = db.Column(
        db.String,
        nullable=False
    )
    #: the requests's date, a :class:`RequestState` value
    state = db.Column(
        PyIntEnum(RequestState),
        nullable=False,
        default=RequestState.pending
    )
    #: plugin-specific data of the request
    data = db.Column(
        JSONB,
        nullable=False
    )
    #: ID of the user creating the request
    created_by_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        index=True,
        nullable=False
    )
    #: the date/time the request was created
    created_dt = db.Column(
        UTCDateTime,
        default=now_utc,
        index=True,
        nullable=False
    )
    #: ID of the user processing the request
    processed_by_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        index=True,
        nullable=True
    )
    #: the date/time the request was accepted/rejected
    processed_dt = db.Column(
        UTCDateTime,
        nullable=True
    )
    #: an optional comment for an accepted/rejected request
    comment = db.Column(
        db.Text,
        nullable=True
    )

    #: The user who created the request
    created_by_user = db.relationship(
        'User',
        lazy=True,
        foreign_keys=[created_by_id],
        backref=db.backref(
            'requests_created',
            lazy='dynamic'
        )
    )
    #: The user who processed the request
    processed_by_user = db.relationship(
        'User',
        lazy=True,
        foreign_keys=[processed_by_id],
        backref=db.backref(
            'requests_processed',
            lazy='dynamic'
        )
    )
    #: The Event this agreement is associated with
    event = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'requests',
            lazy='dynamic'
        )
    )

    @property
    def definition(self):
        return get_request_definitions().get(self.type)

    @definition.setter
    def definition(self, definition):
        assert self.type is None
        self.type = definition.name

    @property
    def can_be_modified(self):
        """Determine if the request can be modified or if a new one must be sent."""
        return self.state in {RequestState.pending, RequestState.accepted}

    @property
    def locator(self):
        return {'confId': self.event_id, 'type': self.type}

    @return_ascii
    def __repr__(self):
        state = self.state.name if self.state is not None else None
        return '<Request({}, {}, {}, {})>'.format(self.id, self.event_id, self.type, state)

    @classmethod
    def find_latest_for_event(cls, event, type_=None):
        """Return the latest requests for a given event.

        :param event: the event to find the requests for
        :param type_: the request type to retrieve, or `None` to get all
        :return: a dict mapping request types to a :class:`Request`
                 or if `type_` was specified, a single :class:`Request` or `None`
        """
        query = Request.query.with_parent(event)
        if type_ is not None:
            return (query.filter_by(type=type_)
                    .order_by(cls.created_dt.desc())
                    .first())
        else:
            query = limit_groups(query, cls, cls.type, cls.created_dt.desc(), 1)
            return {req.type: req for req in query}
