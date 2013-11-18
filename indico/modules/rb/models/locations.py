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

from MaKaC.common.Locators import Locator

from indico.core.db import db
from indico.modules.rb.models.aspects import Aspect
from indico.modules.rb.models.rooms import Room


class Location(db.Model):
    __tablename__ = 'locations'

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String, nullable=False, unique=True)
    support_emails = db.Column(db.String)
    is_default = db.Column(db.String, nullable=False)

    aspects = db.relationship('Aspect',
                              backref='location',
                              cascade='all, delete-orphan',
                              primaryjoin=id==Aspect.location_id)

    default_aspect_id = db.Column(db.Integer, db.ForeignKey('aspects.id',
                                                            use_alter=True,
                                                            name='fk_default_aspect_id'))

    default_aspect = db.relationship('Aspect',
                                     primaryjoin=default_aspect_id==Aspect.id,
                                     post_update=True)

    rooms = db.relationship('Room',
                            backref='location',
                            cascade='all, delete-orphan')

    attributes = db.relationship('LocationAttribute',
                                 backref='location',
                                 cascade='all, delete-orphan')


    def __init__(self, name, is_default=False, support_emails=None):
        self.name = name
        self.is_default = is_default
        self.support_emails = support_emails

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<Location({0}, {1}, {2})>'.format(self.id, self.default_aspect_id,
                                                  self.name)

    def __cmp__(self, other):
        return cmp(self.name, other.name)

    def getLocator( self ):
        d = Locator()
        d["locationId"] = self.name
        return d

    def getSupportEmails(self):
        if self.support_emails:
            return self.getSupportEmails.split(',')

    def setSupportEmails(self, emails):
        self.support_emails = ','.join(emails)

    def getRooms(self):
        return self.rooms

    def addRoom(self, room):
        self.rooms.append(room)

    def deleteRoom(self, room):
        self.rooms.remove(room)

    @staticmethod
    def getDefaultLocation(self, name):
        return Location.query.filter(Location.is_default).one()

    @staticmethod
    def setDefaultLocation(self, name):
        default_location = Location.getDefaultLocation()
        if default_location:
            default_location.is_default = False
            db.session.add(default_location)
        new_default_location = Location.getLocationsByName()
        new_default_location.is_default = True
        db.session.add(new_default_location)

    @staticmethod
    def getLocationById(lid):
        return Location.query.get(lid)

    @staticmethod
    def getLocationByName(name):
        return Location.query.filter(Location.name == name).one()

    @staticmethod
    def getAllLocations():
        return Location.query.all()

    @staticmethod
    def removeLocationByName(name):
        db.session.delete(Location.query.first(Location.name == name))

    def getAverageOccupation(self):
        rooms = self.rooms.query.filter(Room.is_active and
                                        Room.is_reservable).all()

        now = datetime.utcnow()
        end_date = datetime(now.year, now.month, now.day, 17, 30, tzinfo=pytz.utc)
        start_date = end_date - timedelta(30, 9*3600)  # 30 days + 9 hours

        booked_time = sum(map(lambda room: room.getTotalBookedTime(start_date, end_date), rooms))
        bookable_time = sum(map(lambda room: room.getTotalBookableTime(start_date, end_date), rooms))

        if bookable_time:
            return float(booked_time.seconds) / bookable_time.seconds
        return 0

    def getNumberOfRooms(self):
        return self.rooms.query.count()

    def getNumberOfActiveRooms(self):
        return self.rooms.query.filter(Room.is_active).count()

    def getNumberOfReservableRooms(self):
        return self.rooms.query.filter(Room.is_reservable).count()

    def getAllReservableRooms(self):
        return self.rooms.query.filter(Room.is_reservable).all()

    def getTotalReservableSurface(self):
        return sum(map(lambda r: r.surface if r.surface else 0,
                       self.getAllReservableRooms()))

    def getTotalReservableCapacity(self):
        return sum(map(lambda r: r.capacity,
                       self.getAllReservableRooms()))

    def getReservationStats(self):
        return {
            'liveValid': 0,
            'liveCancelled': 0,
            'liveRejected': 0,
            'archivalValid': 0,
            'archivalValid': 0,
            'archivalValid': 0
        }

    def isMapAvailable(self):
        pass
