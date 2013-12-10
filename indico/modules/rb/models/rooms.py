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
Schema of a room
"""

from datetime import datetime

from sqlalchemy import event, func
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm.scoping import scoped_session
# from sqlalchemy.sql import literal_column, expression

from MaKaC.accessControl import AccessWrapper
from MaKaC.common.Locators import Locator
from MaKaC.errors import MaKaCError
from MaKaC.user import Avatar, AvatarHolder

from indico.core.db import db, group_concat
from indico.modules.rb.models import utils
from indico.modules.rb.models.reservations import Reservation
from indico.modules.rb.models.room_attributes import RoomAttribute
from indico.modules.rb.models.room_equipments import (
    RoomEquipment,
    RoomEquipmentAssociation
)
from indico.modules.rb.models.room_bookable_times import BookableTime
from indico.modules.rb.models.room_nonbookable_dates import NonBookableDate


class Room(db.Model):
    __tablename__ = 'rooms'

    # columns

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    # location
    location_id = db.Column(
        db.Integer,
        db.ForeignKey('locations.id'),
        nullable=False
    )
    # user-facing identifier of the room
    name = db.Column(
        db.String,
        nullable=False
    )
    # address
    site = db.Column(
        db.String
    )
    division = db.Column(
        db.String
    )
    building = db.Column(
        db.String,
        nullable=False
    )
    floor = db.Column(
        db.String,
        nullable=False
    )
    number = db.Column(
        db.String,
        nullable=False
    )
    # notifications
    notification_for_start = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )
    notification_for_end = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )
    notification_for_responsible = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )
    notification_for_assistance = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )
    reservations_need_confirmation = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    # extra info about room
    telephone = db.Column(
        db.String
    )
    key_location = db.Column(
        db.String
    )
    capacity = db.Column(
        db.Integer,
        default=20
    )
    surface_area = db.Column(
        db.Integer
    )
    latitude = db.Column(
        db.String
    )
    longitude = db.Column(
        db.String
    )
    comments = db.Column(
        db.String
    )
    # just a pointer to avatar
    owner_id = db.Column(
        db.String,
        nullable=False
    )
    # reservations
    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )
    is_reservable = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )
    max_advance_days = db.Column(
        db.Integer,
        nullable=False,
        default=30
    )

    # relationships

    attributes = db.relationship(
        'RoomAttribute',
        backref='room',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )

    blocked_rooms = db.relationship(
        'BlockedRoom',
        backref='room',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )

    bookable_times = db.relationship(
        'BookableTime',
        backref=db.backref(
            'room',
            order_by='BookableTime.start_time'
        ),
        cascade='all, delete-orphan',
        lazy='dynamic'
    )

    equipments = db.relationship(
        'RoomEquipment',
        secondary=RoomEquipmentAssociation,
        backref='rooms',
        lazy='dynamic'
    )
    equipment_names = association_proxy(
        'equipments',
        'name',
        creator=lambda name: RoomEquipment(name=name)
    )

    nonbookable_dates = db.relationship(
        'NonBookableDate',
        backref='room',
        order_by=NonBookableDate.end_date.desc(),
        cascade='all, delete-orphan',
        lazy='dynamic'
    )

    photos = db.relationship(
        'Photo',
        backref='room',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )

    reservations = db.relationship(
        'Reservation',
        backref='room',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )

    # @event.listens_for(scoped_session, 'after_flush')

    # core

    def __str__(self):
        s = """
               id: {id}
         isActive: {is_active}

             room: {name}

         building: {building}
            floor: {floor}
           roomNr: {number}
     isReservable: {is_reservable}
rNeedConfirmation: {reservations_need_confirmation}
startNotification: {notification_for_start}
  endNotification: {notification_for_end}
notificationToResponsible: {notification_for_responsible}
notificationAssistance: {notification_for_assistance}

             site: {site}
         capacity: {capacity}
      surfaceArea: {surface_area}
         division: {division}

        telephone: {telephone}
       whereIsKey: {key_location}
         comments: {comments}
    responsibleId: {responsible_id}
        equipment: """
        return "{}{}\n".format(utils.formatString(s, self),
                               self.getVerboseEquipment())

    def __cmp__(self, other):
        if not (self and other):
            return cmp(
                1 if self else None,
                1 if other else None
            )
        if self.id == other.id:
            return 0

        return (cmp(self.location.name, other.location.name) or
                cmp(self.building, other.building) or
                cmp(self.floor, other.floor) or
                cmp(self.number, other.number) or
                cmp(self.name, other.name))

    def __repr__(self):
        return '<Room({0}, {1}, {2})>'.format(
            self.id,
            self.location_id,
            self.name
        )

    def getLocator(self):
        loc = Locator()
        # TODO: only id is enough, get rid of location
        loc['roomLocation'] = self.location.name
        loc['roomID'] = self.id
        return loc

    # room management

    @staticmethod
    def getRoomById(rid):
        return Room.query.get(rid)

    @staticmethod
    @utils.filtered
    def getRooms(**filters):
        return Room, Room.query

    @staticmethod
    def getRoomsByName(name):
        return Room.getRooms(name=name)

    @staticmethod
    def getRoomByName(name):
        return Room.query.filter_by(name=name).first()

    def doesHaveLiveReservations(self):
        return len(self.getLiveReservations()) > 0

    def getLiveReservations(self):
        return self.getReservations(
            is_cancelled=False,
            is_rejected=False,
            end_date=('ge', datetime.now())
        )

    @utils.filtered
    def getReservations(self, **filters):
        return Reservation, self.reservations

    def removeReservations(self):
        for r in self.reservations:
            db.session.delete(r)

    @staticmethod
    def isAvatarResponsibleForRooms(avatar):
        return (Room.query
                    .filter(Room.responsible_id == avatar.id)
                    .count() > 0)

    # equipments

    @utils.filtered
    def getEquipments(self, **filters):
        return RoomEquipment, self.equipments

    def addEquipments(self, equipment_names):
        for ename in equipment_names:
            self.addEquipment(ename)

    def addEquipment(self, equipment_name):
        equipment = self.getEquipments(name=equipment_name)
        if not equipment:
            equipment = RoomEquipment(name=equipment_name)
        self.equipments.append(equipment)

    def removeEquipments(self, equipment_names):
        for equipment in equipment_names:
            self.equipments.delete(equipment)

    def removeEquipment(self, equipment_name):
        equipment = self.getEquipments(name=equipment_name)
        if equipment:
            self.equipments.delete(equipment)

    def hasEquipment(self, name):
        return len(self.getEquipments(name=name)) > 0

    def doesNeedVideoConferenceSetup(self):
        return self.hasEquipment('Video Conference')

    def hasWebcastRecording(self):
        return self.hasEquipment('Webcast/Recording')

    def getVerboseEquipment(self):
        return (self.equipments
                    .with_entities(
                        func.group_concat(RoomEquipment.name)  # separator
                    )
                    .scalar())

    # bookable times

    def getBookableTimes(self):
        return self.bookable_times.all()

    def addBookableTime(self, bookable_time):
        self.bookable_times.append(bookable_time)

    def clearBookableTimes(self):
        del self.bookable_times[:]

    # nonbookable dates

    def getNonBookableDates(self, skip_past=False):
        q = self.nonbookable_dates
        if skip_past:
            q = q.filter(NonBookableDate.start_date >= datetime.utcnow())
        return q.all()

    def addNonBookableDate(self, nonbookable_date):
        self.nonbookable_dates.append(nonbookable_date)

    def clearNonBookableDates(self):
        del self.nonbookable_dates[:]

    def getBlockedDay(self, day):
        pass

    def getAllManagers(self):
        # managers = set([self.getResponsible()])
        pass

    @staticmethod
    def isAvatarResponsibleForRooms(avatar):
        return Room.query.filter(exists(Room.responsible_id == avatar.getId())).scalar()

    @staticmethod
    def getRoomsOfUser():
        return Room.query.filter_by(responsible_id=avatar.getId()).all()

    # TODO
    def isAvailable(self, potential_reservation):
        if self.getCollisions(potential_reservation):
            return False
        return True

    def getResponsible(self):
        return AvatarHolder().getById(self.responsible_id)

    def getLocationName(self):
        return self.location.name

    # photos

    # TODO completely different

    # attributes

    @utils.filtered
    def getAttributes(self, **filters):
        return RoomAttribute, self.attributes

    # def getAttributeByName(self, name):
    #     aval = (self.attributes
    #                 .with_entities(RoomAttribute.value)
    #                 .outerjoin(RoomAttribute.key)
    #                 .filter(
    #                     self.id == RoomAttribute.room_id,
    #                     RoomAttribute.key_id == RoomAttributeKey.id,
    #                     RoomAttributeKey.name == name
    #                 )
    #                 .first())
    #     if aval:
    #         return aval[0]

    def hasBookingACL(self):
        return self.getAttributeByName('Booking Simba List') is not None

    def canBeViewedBy(self, accessWrapper):
        """Room details are public - anyone can view."""
        return True

    @utils.accessChecked
    def canBeBookedByProcess(self, avatar, pre=False):
        """
        Execution for canBeBookedBy and canBePreBookedBy methods
        """
        if (self.is_active and self.is_reservable and
            (pre or not self.reservations_need_confirmation)):

            simbaList = self.getAttributeByName('Booking Simba List')
            if simbaList not in [None, "Error: unknown mailing list", ""]:
                if avatar.isMemberOf(simbaList):
                    return True
            else:
                return True

        if not avatar:
            return False

        if avatar.isRBAdmin() or (self.isOwnedBy(avatar) and self.is_active):
            return True

        return False

    def canBeBookedBy(self, avatar):
        """
        Reservable rooms which does not require pre-booking can be booked by anyone.
        Other rooms - only by their responsibles.
        """
        return self.canBeBookedProcess(avatar)

    def canBePreBookedBy(self, avatar):
        """
        Reservable rooms can be pre-booked by anyone.
        Other rooms - only by their responsibles.
        """
        return self.canBeBookedProcess(avatar, pre=True)

    def canBeModifiedBy(self, accessWrapper):
        """Only admin can modify rooms."""
        if not accessWrapper:
            return False
        if isinstance(accessWrapper, AccessWrapper):
            avatar = accessWrapper.getUser()
            if avatar:
                return avatar.isRBAdmin()
            else:
                return False
        elif isinstance(accessWrapper, Avatar):
            return accessWrapper.isRBAdmin()

        raise MaKaCError(_('canModify requires either AccessWrapper or Avatar object'))

    def canBeDeletedBy(self, accessWrapper):
        """Entity can modify is also capable of deletion"""
        return self.canBeModifiedBy(accessWrapper)

    def isOwnedBy(self, avatar):
        """
        Returns True if user is responsible for this room. False otherwise.
        """
        # legacy check, currently every room must be owned by someone
        if not self.responsible_id:
            return None
        if self.responsible_id == avatar.id:
            return True
        simbaList = self.getAttributeByName('Simba List')
        if (simbaList not in [None, 'Error: unknown mailing list', ''] and
            avatar.isMemberOfSimbaList(simbaList)):
            return True
        return False

    def getFullName(self):
        return '{}-{}-{}-{}'.format(
            self.building,
            self.floor,
            self.number,
            self.name
        )

    def getTotalBookedTime(self, start_date, end_date):
        reservations = (self.reservations
                            .query.filter(
                                 Reservation.start_date >= start_date,
                                 Reservation.start_date <= end_date,
                                 Reservation.is_rejected == False,
                                 Reservation.is_rejected == False
                             ).all())

        for r in reservations:
            pass

    def getTotalBookableTime(self, start_date, end_date):
        pass


    def notifyAboutResponsibility( self ):
        """
        Notifies (e-mails) previous and new responsible about
        responsibility change. Called after creating/updating the room.
        """
        pass

    def getAverageOccupation(self, period=None):
        pass

    def getReservationStats(self):
        pass

    @staticmethod
    def getBuildingCoordinatesByRoomIds(rids):
        return (Room.query
                    .with_entities(
                        Room.latitude,
                        Room.longitude
                    )
                    .filter(
                        Room.latitude != None,
                        Room.longitude != None,
                        Room.id.in_(rids)
                    )
                    .first())

    @staticmethod
    def getRoomsRequireVideoConferenceSetupByIds(rids):
        return (Room.query
                    .join(Room.equipments)
                    .filter(
                        RoomEquipment.name == 'Video Conference',
                        Room.id.in_(rids)
                    )
                    .all())

