# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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
from indico.core.db.sqlalchemy import UTCDateTime, PyIntEnum
from indico.modules.events.requests import get_request_definitions
from indico.util.date_time import now_utc
from indico.util.i18n import _
from indico.util.string import return_ascii
from indico.util.struct.enum import TitledIntEnum


class RequestState(TitledIntEnum):
    __titles__ = [_('Pending'), _('Accepted'), _('Rejected')]
    pending = 0
    accepted = 1
    rejected = 2


class Request(db.Model):
    """Event-related requests, e.g. for a webcast"""
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
        nullable=False
    )
    #: plugin-specific data of the payment
    data = db.Column(
        JSON,
        nullable=False
    )
    #: ID of the user creating the request
    created_by_id = db.Column(
        db.Integer,
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
        nullable=True
    )
    #: the date/time the request was accepted/rejected
    processed_dt = db.Column(
        UTCDateTime,
        nullable=True
    )

    @property
    def event(self):
        from MaKaC.conference import ConferenceHolder
        return ConferenceHolder().getById(str(self.event_id))

    @event.setter
    def event(self, event):
        self.event_id = int(event.getId())

    @property
    def created_by_user(self):
        from MaKaC.user import AvatarHolder
        return AvatarHolder().getById(str(self.event_id))

    @created_by_user.setter
    def created_by_user(self, user):
        self.created_by_id = int(user.getId())

    @property
    def processed_by_user(self):
        from MaKaC.user import AvatarHolder
        return AvatarHolder().getById(str(self.event_id))

    @processed_by_user.setter
    def processed_by_user(self, user):
        self.processed_by_id = int(user.getId())

    @property
    def definition(self):
        return get_request_definitions().get(self.type)

    @return_ascii
    def __repr__(self):
        state = self.state.name if self.state is not None else None
        return '<Request({}, {}, {})>'.format(self.id, self.event_id, state)
