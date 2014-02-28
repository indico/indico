# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

"""
Holder of rooms in a place and its map view related data
"""

from datetime import datetime, timedelta

import pytz
from sqlalchemy import func, or_, and_
from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import select, label, column
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.dialects.postgresql import array

from MaKaC.common.Locators import Locator

from indico.core.db import db
from indico.util.i18n import _

from . import utils
from .aspects import Aspect
from .reservations import Reservation
from .room_attributes import RoomAttribute
from .room_equipments import RoomEquipment, RoomEquipmentAssociation
from .rooms import Room

class Location(db.Model):
    __tablename__ = 'locations'

    # columns

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    name = db.Column(
        db.String,
        nullable=False,
        unique=True,
        index=True
    )
    support_emails = db.Column(
        db.String
    )
    is_default = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    default_aspect_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'aspects.id',
            use_alter=True,
            name='fk_default_aspect_id',
            onupdate='CASCADE',
            ondelete='SET NULL'
        )
    )

    # relationships

    aspects = db.relationship(
        'Aspect',
        backref='location',
        cascade='all, delete-orphan',
        primaryjoin=id==Aspect.location_id,
        lazy='dynamic',
    )

    default_aspect = db.relationship(
        'Aspect',
        primaryjoin=default_aspect_id==Aspect.id,
        post_update=True,
    )

    rooms = db.relationship(
        'Room',
        backref='location',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )

    # attributes = db.relationship(
    #     'LocationAttribute',
    #     backref='location',
    #     cascade='all, delete-orphan',
    #     lazy='dynamic'
    # )

    attributes = db.relationship(
        'RoomAttribute',
        backref='location',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )

    equipment_objects = db.relationship(
        'RoomEquipment',
        backref='location',
        lazy='dynamic'
    )

    equipments = association_proxy(
        'equipment_objects',
        'name',
        creator=lambda name: RoomEquipment(name=name)
    )

    # core

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<Location({0}, {1}, {2})>'.format(
            self.id,
            self.default_aspect_id,
            self.name
        )

    def __cmp__(self, other):
        if not (self and other):
            return cmp(
                1 if self else None,
                1 if other else None
            )
        if self.id == other.id:
            return 0
        return cmp(self.name, other.name)

    # TODO: get rid of locators, may use id field instead
    def getLocator(self):
        d = Locator()
        d['locationId'] = self.name
        return d

    # support emails

    def getSupportEmails(self, to_list=True):
        if self.support_emails:
            if to_list:
                return self.support_emails.split(',')
            else:
                return self.support_emails
        else:
            return ('', [])[to_list]

    def setSupportEmails(self, emails):
        if isinstance(emails, list):
            self.support_emails = ','.join(emails)
        else:
            self.support_emails = emails

    def addSupportEmails(self, *emails):
        new_support_emails = sorted(set(self.getSupportEmails() + list(emails)))
        self.support_emails = ','.join(new_support_emails)

    def deleteSupportEmails(self, *emails):
        support_emails = self.getSupportEmails()
        for email in emails:
            if email in emails:
                support_emails.remove(email)
        self.setSupportEmails(support_emails)

    # aspects

    @utils.filtered
    def filterAspects(self, **filters):
        return Aspect, self.aspects

    def getAspects(self):
        return self.aspects.all()

    def getAspectsAsDictionary(self):
        return [aspect.toDictionary() for aspect in self.getAspects()]

    def getAspectById(self, aid):
        return self.aspects.filter_by(id=aid).first()

    def removeAspectById(self, aid):
        return self.aspects.filter_by(id=aid).delete()

    def addAspect(self, aspect):
        self.aspects.append(aspect)

    def deleteAspect(self, aspect):
        self.aspects.remove(aspect)

    def getDefaultAspect(self):
        return self.default_aspect

    def setDefaultAspect(self, aspect):
        self.default_aspect = aspect

    def isMapAvailable(self):
        return self.aspects.count() > 0

    # room management

    @utils.filtered
    def filterRooms(self, **filters):
        return Room, self.rooms

    def addRoom(self, room):
        self.rooms.append(room)

    def deleteRoom(self, room):
        self.rooms.remove(room)

    def getRooms(self):
        return self.rooms.all()

    def getRoomById(self, rid):
        return self.rooms.filter_by(id=rid).first()

    def getRoomsOrderedByNames(self):
        return self.rooms.order_by(Room.name).all()

    # default location management

    @staticmethod
    def getDefaultLocation():
        return Location.query.filter_by(is_default=True).first()

    @staticmethod
    def setDefaultLocation(location_name):
        (
            Location
                .query
                .filter(
                    or_(
                        Location.is_default,
                        Location.name == location_name
                    )
                )
                .update(
                    {
                        'is_default': func.not_(Location.is_default)
                    },
                    synchronize_session='fetch'
                )
        )

    # generic location management

    @staticmethod
    def getLocationById(lid):
        return Location.query.get(lid)

    @staticmethod
    def getLocationByName(name):
        return Location.query.filter_by(name=name).first()

    @staticmethod
    def getLocations():
        return Location.query.all()

    @staticmethod
    def getNumberOfLocations():
        return Location.query.count()

    @staticmethod
    def addLocationByName(name):
        db.session.add(
            Location(
                name=name,
                is_default=(Location.getNumberOfLocations() == 0)
            )
        )

    @staticmethod
    def removeLocationByName(name):
        Location.query.filter_by(name=name).delete()

    # attribute management

    def addAttribute(self, name, value={}):
        attr = RoomAttribute(name=name)
        attr.value = value
        self.attributes.append(attr)

    def removeAttributeByName(self, name):
        self.attributes.filter_by(name=name).delete()

    def getAttributeByName(self, name):
        return self.attributes.filter_by(name=name).first()

    def getAttributes(self):
        return self.attributes.all()

    # equipment management

    def getEquipments(self):
        return self.equipment_objects.all()

    def getEquipmentNames(self):
        return list(self.equipments)

    def getEquipmentByName(self, name):
        return self.equipment_objects.filter_by(name=name).first()

    def addEquipment(self, name):
        self.equipments.append(name)

    def removeEquipment(self, name):
        self.equipment_objects.filter_by(name=name).delete()

    def hasEquipment(self, name):
        return self.equipment_objects.filter_by(name=name).count() > 0

    # location helpers

    def getAverageOccupation(self):
        now = datetime.utcnow()
        end_date = datetime(now.year, now.month, now.day, 17, 30, tzinfo=pytz.utc)
        start_date = end_date - timedelta(30, 9*3600)  # 30 days + 9 hours

        booked_time = self.getTotalBookedTimeInLastMonth(start_date, end_date)
        bookable_time = self.getTotalBookableTime(start_date, end_date)

        if bookable_time:
            return float(booked_time) / bookable_time
        return 0

    def getTotalBookedTime(self, *dates):
        return (self.query
                    .with_entities(func.sum())
                    .join(Location.rooms)
                    .join(Room.reservations)
                    .filter(
                        Room.is_active,
                        Room.is_reservable,
                        or_(
                            Reservation.start_date.in_(dates),
                            Reservation.end_date.in_(dates)
                        )
                    ))  # TODO

    def getTotalBookableTime(self):
        pass

    def getNumberOfRooms(self):
        return self.rooms.count()

    def getNumberOfActiveRooms(self):
        return self.rooms.filter_by(is_active=True).count()

    def getNumberOfReservableRooms(self):
        return self.rooms.filter_by(is_reservable=True).count()

    def getReservableRooms(self):
        return self.rooms.filter_by(is_reservable=True).all()

    def getTotalReservableSurfaceArea(self):
        return (self.rooms
                    .with_entities(func.sum(Room.surface_area))
                    .filter_by(is_reservable=True)
                    .scalar())

    def getTotalReservableCapacity(self):
        return (self.rooms
                    .with_entities(func.sum(Room.capacity))
                    .filter_by(is_reservable=True)
                    .scalar())

    def getReservationStats(self):
        return utils.stats_to_dict(
            self.rooms
                .join(Room.reservations)
                .with_entities(
                    Reservation.is_live,
                    Reservation.is_cancelled,
                    Reservation.is_rejected,
                    func.count(Reservation.id)
                )
                .group_by(
                    Reservation.is_live,
                    Reservation.is_cancelled,
                    Reservation.is_rejected
                )
                .all()
        )

    def getBuildings(self, with_rooms=True):

        def get_subquery(column):
            return select([column])\
                .select_from(
                    func.unnest(func.array_agg(getattr(Room, column))).alias(column)
                )\
                .correlate(None)\
                .where("{} != ''".format(column))\
                .limit(1)\
                .as_scalar()

        video_conference_equipment = self.equipment_objects\
                                         .with_entities(RoomEquipment.id)\
                                         .filter_by(name='Video conference')\
                                         .as_scalar()

        r = aliased(Room)
        room_id_subquery = db.session.query(r)\
                             .with_entities(r.id)\
                             .correlate(Room)\
                             .filter(
                                 and_(
                                     or_(
                                         with_rooms,
                                         r.equipments.any(video_conference_equipment)  # contains
                                     ),
                                     r.id.in_(
                                         select(['e'])
                                             .select_from(func.unnest(func.array_agg(Room.id)).alias('e'))
                                             .correlate(None)
                                             .as_scalar()
                                     )
                                 )
                             )\
                             .as_scalar()

        results = self.rooms\
                      .with_entities(
                        Room.building,
                        func.array(room_id_subquery),
                        get_subquery('longitude'),
                        get_subquery('latitude')
                      )\
                      .group_by(Room.building)\
                      .all()

        rooms = dict(self.rooms.with_entities(Room.id, Room).all())

        a = [{
            'number': building,
            'title': _('Building {}').format(building),
            'longitude': lo,
            'latitude': la,
            'rooms': [rooms[rid].to_serializable() for rid in room_ids]
        } for building, room_ids, lo, la in results if la and lo]

        print a
        return a
