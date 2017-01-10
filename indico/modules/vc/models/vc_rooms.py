# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from functools import partial
from itertools import chain

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.event import listen
from sqlalchemy.ext.hybrid import hybrid_property, Comparator

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


class VCRoomLinkType(int, IndicoEnum):
    event = 1
    contribution = 2
    block = 3


_columns_for_types = {
    VCRoomLinkType.event: {'linked_event_id'},
    VCRoomLinkType.contribution: {'contribution_id'},
    VCRoomLinkType.block: {'session_block_id'},
}


def _make_checks():
    available_columns = set(chain.from_iterable(cols for type_, cols in _columns_for_types.iteritems()))
    for link_type in VCRoomLinkType:
        required_cols = available_columns & _columns_for_types[link_type]
        forbidden_cols = available_columns - required_cols
        criteria = ['{} IS NULL'.format(col) for col in sorted(forbidden_cols)]
        criteria += ['{} IS NOT NULL'.format(col) for col in sorted(required_cols)]
        condition = 'link_type != {} OR ({})'.format(link_type, ' AND '.join(criteria))
        yield db.CheckConstraint(condition, 'valid_{}_link'.format(link_type.name))


class VCRoomStatus(int, IndicoEnum):
    created = 1
    deleted = 2


class VCRoom(db.Model):
    __tablename__ = 'vc_rooms'
    __table_args__ = (db.Index(None, 'data', postgresql_using='gin'),
                      {'schema': 'events'})

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
        JSONB,
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
    __table_args__ = tuple(_make_checks()) + (db.Index(None, 'data', postgresql_using='gin'),
                                              {'schema': 'events'})

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
    #: Type of the object the vc_room is linked to
    link_type = db.Column(
        PyIntEnum(VCRoomLinkType),
        nullable=False
    )
    linked_event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        index=True,
        nullable=True
    )
    session_block_id = db.Column(
        db.Integer,
        db.ForeignKey('events.session_blocks.id'),
        index=True,
        nullable=True
    )
    contribution_id = db.Column(
        db.Integer,
        db.ForeignKey('events.contributions.id'),
        index=True,
        nullable=True
    )
    #: If the vc room should be shown on the event page
    show = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: videoconference plugin-specific data
    data = db.Column(
        JSONB,
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
        foreign_keys=event_id,
        lazy=True,
        backref=db.backref(
            'all_vc_room_associations',
            lazy='dynamic'
        )
    )
    #: The linked event (if the VC room is attached to the event itself)
    linked_event = db.relationship(
        'Event',
        foreign_keys=linked_event_id,
        lazy=True,
        backref=db.backref(
            'vc_room_associations',
            lazy=True
        )
    )
    #: The linked contribution (if the VC room is attached to a contribution)
    linked_contrib = db.relationship(
        'Contribution',
        lazy=True,
        backref=db.backref(
            'vc_room_associations',
            lazy=True
        )
    )
    #: The linked session block (if the VC room is attached to a block)
    linked_block = db.relationship(
        'SessionBlock',
        lazy=True,
        backref=db.backref(
            'vc_room_associations',
            lazy=True
        )
    )

    @classmethod
    def register_link_events(cls):
        event_mapping = {cls.linked_block: lambda x: x.event_new,
                         cls.linked_contrib: lambda x: x.event_new,
                         cls.linked_event: lambda x: x}

        type_mapping = {cls.linked_event: VCRoomLinkType.event,
                        cls.linked_block: VCRoomLinkType.block,
                        cls.linked_contrib: VCRoomLinkType.contribution}

        def _set_link_type(link_type, target, value, *unused):
            if value is not None:
                target.link_type = link_type

        def _set_event_obj(fn, target, value, *unused):
            if value is not None:
                event = fn(value)
                assert event is not None
                target.event_new = event

        for rel, fn in event_mapping.iteritems():
            if rel is not None:
                listen(rel, 'set', partial(_set_event_obj, fn))

        for rel, link_type in type_mapping.iteritems():
            if rel is not None:
                listen(rel, 'set', partial(_set_link_type, link_type))

    @property
    def locator(self):
        return dict(self.event_new.locator, service=self.vc_room.type, event_vc_room_id=self.id)

    @hybrid_property
    def link_object(self):
        if self.link_type == VCRoomLinkType.event:
            return self.linked_event
        elif self.link_type == VCRoomLinkType.contribution:
            return self.linked_contrib
        else:
            return self.linked_block

    @link_object.setter
    def link_object(self, obj):
        self.linked_event = self.linked_contrib = self.linked_block = None
        if isinstance(obj, db.m.Event):
            self.linked_event = obj
        elif isinstance(obj, db.m.Contribution):
            self.linked_contrib = obj
        elif isinstance(obj, db.m.SessionBlock):
            self.linked_block = obj
        else:
            raise TypeError('Unexpected object: {}'.format(obj))

    @link_object.comparator
    def link_object(cls):
        return _LinkObjectComparator(cls)

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
        query = event.all_vc_room_associations
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

    def delete(self, user, delete_all=False):
        """Deletes a VC room from an event

        If the room is not used anywhere else, the room itself is also deleted.

        :param user: the user performing the deletion
        :param delete_all: if True, the room is detached from all
                           events and deleted.
        """
        vc_room = self.vc_room
        if delete_all:
            for assoc in vc_room.events[:]:
                Logger.get('modules.vc').info("Detaching VC room {} from event {} ({})".format(
                    vc_room, assoc.event_new, assoc.link_object)
                )
                vc_room.events.remove(assoc)
        else:
            Logger.get('modules.vc').info("Detaching VC room {} from event {} ({})".format(
                vc_room, self.event_new, self.link_object)
            )
            vc_room.events.remove(self)
        db.session.flush()
        if not vc_room.events:
            Logger.get('modules.vc').info("Deleting VC room {}".format(vc_room))
            if vc_room.status != VCRoomStatus.deleted:
                vc_room.plugin.delete_room(vc_room, self.event_new)
                notify_deleted(vc_room.plugin, vc_room, self, self.event_new, user)
            db.session.delete(vc_room)


VCRoomEventAssociation.register_link_events()


class _LinkObjectComparator(Comparator):
    def __init__(self, cls):
        self.cls = cls

    def __clause_element__(self):
        # just in case
        raise NotImplementedError

    def __eq__(self, other):
        if isinstance(other, db.m.Event):
            return db.and_(self.cls.link_type == VCRoomLinkType.event,
                           self.cls.linked_event_id == other.id)
        elif isinstance(other, db.m.SessionBlock):
            return db.and_(self.cls.link_type == VCRoomLinkType.block,
                           self.cls.session_block_id == other.id)
        elif isinstance(other, db.m.Contribution):
            return db.and_(self.cls.link_type == VCRoomLinkType.contribution,
                           self.cls.contribution_id == other.id)
        else:
            raise TypeError('Unexpected object type {}: {}'.format(type(other), other))
