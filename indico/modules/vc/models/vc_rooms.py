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

from sqlalchemy.dialects.postgresql import JSON

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum
from indico.core.db.sqlalchemy.custom.utcdatetime import UTCDateTime
from indico.core.logger import Logger
from indico.modules.vc.notifications import notify_deleted
from indico.util.caching import memoize_request
from indico.util.date_time import now_utc
from indico.util.event import unify_event_args
from indico.util.string import return_ascii
from indico.util.struct.enum import IndicoEnum
from MaKaC.conference import ConferenceHolder


class VCRoomLinkType(int, IndicoEnum):
    event = 1
    contribution = 2
    block = 3


class VCRoomStatus(int, IndicoEnum):
    created = 1
    deleted = 2


class VCRoom(db.Model):
    __tablename__ = 'vc_rooms'
    __table_args__ = {'schema': 'events'}

    #: Videoconference room ID
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: Type of the videoconference room
    type = db.Column(
        db.String,
        nullable=False
    )
    #: Name of the videoconference room
    name = db.Column(
        db.String,
        nullable=False
    )
    #: Status of the videoconference room
    status = db.Column(
        PyIntEnum(VCRoomStatus),
        nullable=False
    )
    #: ID of the creator
    created_by_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        nullable=False,
        index=True
    )
    #: Creation timestamp of the videoconference room
    created_dt = db.Column(
        UTCDateTime,
        nullable=False,
        default=now_utc
    )

    #: Modification timestamp of the videoconference room
    modified_dt = db.Column(
        UTCDateTime
    )
    #: videoconference plugin-specific data
    data = db.Column(
        JSON,
        nullable=False
    )

    #: The user who created the videoconference room
    created_by_user = db.relationship(
        'User',
        lazy=True,
        backref=db.backref(
            'vc_rooms',
            lazy='dynamic'
        )
    )

    # relationship backrefs:
    # - events (VCRoomEventAssociation.vc_room)

    @property
    def plugin(self):
        from indico.modules.vc.util import get_vc_plugins
        return get_vc_plugins().get(self.type)

    @property
    def locator(self):
        return {'vc_room_id': self.id, 'service': self.type}

    @return_ascii
    def __repr__(self):
        return '<VCRoom({}, {}, {})>'.format(self.id, self.name, self.type)


class VCRoomEventAssociation(db.Model):
    __tablename__ = 'vc_room_events'
    __table_args__ = {'schema': 'events'}

    #: Association ID
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    #: ID of the event
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        index=True,
        autoincrement=False,
        nullable=False
    )
    #: ID of the videoconference room
    vc_room_id = db.Column(
        db.Integer,
        db.ForeignKey('events.vc_rooms.id'),
        index=True,
        nullable=False
    )
    #: Link type of the vc_room to a event/contribution/session
    link_type = db.Column(
        PyIntEnum(VCRoomLinkType),
        nullable=False
    )
    #: Id of the event/contribution/session block the vc_room is linked to
    link_id = db.Column(
        db.String,
        nullable=True
    )
    #: If the chatroom should be hidden on the event page
    show = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: videoconference plugin-specific data
    data = db.Column(
        JSON,
        nullable=False
    )

    #: The associated :class:VCRoom
    vc_room = db.relationship(
        'VCRoom',
        lazy=False,
        backref=db.backref('events', cascade='all, delete-orphan')
    )
    #: The associated Event
    event_new = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'vc_room_associations',
            lazy='dynamic'
        )
    )

    @property
    def locator(self):
        return dict(self.event.getLocator(), service=self.vc_room.type, event_vc_room_id=self.id)

    @property
    def event(self):
        return ConferenceHolder().getById(str(self.event_id), True)

    @event.setter
    def event(self, event):
        self.event_id = int(event.getId())

    @property
    def link_object(self):
        if self.link_type == VCRoomLinkType.event:
            return self.event
        elif self.link_type == VCRoomLinkType.contribution:
            return self.event.getContributionById(self.link_id)
        else:
            session_id, slot_id = self.link_id.split(':')
            sess = self.event.getSessionById(session_id)
            return sess.getSlotById(slot_id) if sess is not None else None

    @return_ascii
    def __repr__(self):
        return '<VCRoomEventAssociation({}, {})>'.format(self.event_id, self.vc_room)

    @classmethod
    @unify_event_args
    def find_for_event(cls, event, include_hidden=False, include_deleted=False, only_linked_to_event=False, **kwargs):
        """Returns a Query that retrieves the videoconference rooms for an event

        :param event: an indico Event
        :param only_linked_to_event: only retrieve the vc rooms linked to the whole event
        :param kwargs: extra kwargs to pass to ``find()``
        """
        if only_linked_to_event:
            kwargs['link_type'] = int(VCRoomLinkType.event)
        query = event.vc_room_associations
        if kwargs:
            query = query.filter_by(**kwargs)
        if not include_hidden:
            query = query.filter(cls.show)
        if not include_deleted:
            query = query.filter(VCRoom.status != VCRoomStatus.deleted).join(VCRoom)
        return query

    @classmethod
    @memoize_request
    def get_linked_for_event(cls, event):
        """Get a dict mapping link objects to event vc rooms"""
        return {vcr.link_object: vcr for vcr in cls.find_for_event(event)}

    def delete(self, user):
        """Deletes a VC room from an event

        If the room is not used anywhere else, the room itself is also deleted.

        :param user: the user performing the deletion
        """
        Logger.get('modules.vc').info("Detaching VC room {} from event {} ({})".format(
            self.vc_room, self.event, self.link_object)
        )
        db.session.delete(self)
        db.session.flush()
        if not self.vc_room.events:
            Logger.get('modules.vc').info("Deleting VC room {}".format(self.vc_room))
            if self.vc_room.status != VCRoomStatus.deleted:
                self.vc_room.plugin.delete_room(self.vc_room, self.event)
                notify_deleted(self.vc_room.plugin, self.vc_room, self, self.event, user)
            db.session.delete(self.vc_room)
