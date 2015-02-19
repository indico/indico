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
from indico.core.db.sqlalchemy import PyIntEnum
from indico.core.db.sqlalchemy.custom.utcdatetime import UTCDateTime
from indico.util.date_time import now_utc
from indico.util.string import return_ascii
from indico.util.struct.enum import IndicoEnum
from MaKaC.user import AvatarHolder
from MaKaC.conference import ConferenceHolder


class VCRoomLinkType(int, IndicoEnum):
    event = 1
    contribution = 2
    session = 3


class VCRoomStatus(int, IndicoEnum):
    created = 1


class VCRoom(db.Model):
    __tablename__ = 'vc_rooms'
    __table_args__ = {'schema': 'events'}

    #: Video conference room ID
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: Type of the video conference room
    type = db.Column(
        db.String,
        nullable=False
    )
    #: Name of the video conference room
    name = db.Column(
        db.String,
        nullable=False
    )
    #: Status of the video conference room
    status = db.Column(
        PyIntEnum(VCRoomStatus),
        nullable=False
    )
    #: ID of the creator
    created_by_id = db.Column(
        db.Integer,
        nullable=False,
        index=True
    )
    #: Creation timestamp of the video conference room
    created_dt = db.Column(
        UTCDateTime,
        nullable=False,
        default=now_utc
    )
    #: Modification timestamp of the video conference room
    modified_dt = db.Column(
        UTCDateTime
    )
    #: video conference plugin-specific data
    data = db.Column(
        JSON,
        nullable=False
    )

    @property
    def locator(self):
        return {'vc_room_id': self.id, 'service': self.type}

    @property
    def created_by_user(self):
        """The Avatar who created the video conference room."""
        return AvatarHolder().getById(str(self.created_by_id))

    @created_by_user.setter
    def created_by_user(self, user):
        self.created_by_id = int(user.getId())

    @return_ascii
    def __repr__(self):
        return '<VCRoom({}, {}, {})>'.format(self.id, self.name, self.type)


class VCRoomEventAssociation(db.Model):
    __tablename__ = 'vc_room_events'
    __table_args__ = {'schema': 'events'}

    #: ID of the event
    event_id = db.Column(
        db.Integer,
        primary_key=True,
        index=True,
        autoincrement=False
    )
    #: ID of the video conference room
    vc_room_id = db.Column(
        db.Integer,
        db.ForeignKey('events.vc_rooms.id'),
        primary_key=True,
        index=True
    )
    #: The associated :class:VCRoom
    vc_room = db.relationship(
        'VCRoom',
        lazy=False,
        backref=db.backref('events', cascade='all, delete-orphan')
    )
    #: Link type of the vc_room to a event/contribution/session
    link_type = db.Column(
        PyIntEnum(VCRoomLinkType),
        nullable=False
    )
    #: Id of the event/contribution/session id the vc_room is linked to
    link_id = db.Column(
        db.Integer,
        nullable=True
    )

    @property
    def locator(self):
        return dict(self.event.getLocator(), **self.vc_room.locator)

    @property
    def event(self):
        return ConferenceHolder().getById(str(self.event_id))

    @property
    def link_object(self):
        if self.link_type == VCRoomLinkType.event:
            return self.event
        elif self.link_type == VCRoomLinkType.contribution:
            return self.event.getContributionById(self.link_id)
        else:
            return self.event.getSessionById(self.link_id)

    @event.setter
    def event(self, event):
        self.event_id = int(event.getId())

    @return_ascii
    def __repr__(self):
        return '<VCRoomEventAssociation({}, {})>'.format(self.event_id, self.vc_room)

    @classmethod
    def find_for_event(cls, event, **kwargs):
        """Returns a Query that retrieves the video conference rooms for an event

        :param event: an indico event (with a numeric ID)
        :param kwargs: extra kwargs to pass to ``find()``
        """
        query = cls.find(event_id=int(event.id), **kwargs)
        return query
