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
from sqlalchemy import func

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

    #### Common ####

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<Location({0}, {1}, {2})>'.format(
            self.id,
            self.default_aspect_id,
            self.name
        )

    def __cmp__(self, other):
        return cmp(self.name, other.name)

    # TODO: get rid of locators
    def getLocator( self ):
        d = Locator()
        d["locationId"] = self.name
        return d

    #### Supports Emails ####

    def getSupportEmails(self, to_list=True):
        if self.support_emails:
            if to_list:
                return self.support_emails.split(',')
            else:
                return self.support_emails

    def setSupportEmails(self, emails):
        if isinstance(emails, list):
            self.support_emails = ','.join(emails)
        else:
            self.support_emails = emails

    def addSupportEmails(self, *emails):
        new_support_emails = sorted(set(self.getSupportEmails() + emails))
        self.support_emails = ','.join(new_support_emails)

    def deleteSupportEmails(self, *emails):
        support_emails = self.getSupportEmails()
        for email in emails:
            if email in emails:
                support_emails.remove(email)
        self.setSupportEmails(support_emails)

    #### Aspects #####

    def getAllAspects(self):
        return self.aspects

    def addAspect(self, aspect):
        self.aspects.append(aspect)

    def deleteAspect(self, aspect):
        self.aspects.remove(aspect)

    def getDefaultAspect(self):
        return self.default_aspect

    def setDefaultAspect(self, aspect):
        self.default_aspect = aspect

    def isMapAvailable(self):
        return (self.query
                    .join(Location.aspects)
                    .count() > 0)

    #### Room Management ####

    def getAllRooms(self):
        return self.rooms

    def addRoom(self, room):
        self.rooms.append(room)

    def deleteRoom(self, room):
        self.rooms.remove(room)

    #### Default Location Management ####

    @staticmethod
    def getDefaultLocation():
        return Location.query.filter(Location.is_default).one()

    @staticmethod
    def setDefaultLocation(name):
        default_location = Location.getDefaultLocation()
        if default_location:
            if default_location.name == name:
                return
            default_location.is_default = False
            db.session.add(default_location)

        new_default_location = Location.getLocationByName(name)
        new_default_location.is_default = True
        db.session.add(new_default_location)

    #### Generic Location Management

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
        db.session.delete(Location.query.filter(Location.name == name).one())

    #### Location Helpers ####

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
        return (self.query
                    .join(Location.rooms)
                    .count())

    def getNumberOfActiveRooms(self):
        return (self.query
                    .join(Location.rooms)
                    .filter(Room.is_active)
                    .count())

    def getNumberOfReservableRooms(self):
        return (self.query
                    .join(Location.rooms)
                    .filter(Room.is_reservable)
                    .count())

    def getAllReservableRooms(self):
        return (self.query
                    .join(Location.rooms)
                    .filter(Room.is_reservable)
                    .all())

    def getTotalReservableSurfaceArea(self):
        return (self.query
                    .with_entities(func.sum(Room.surface_area))
                    .join(Location.rooms)
                    .filter(Room.is_reservable)
                    .scalar())

    def getTotalReservableCapacity(self):
        return (self.query
                    .with_entities(func.sum(Room.capacity))
                    .join(Location.rooms)
                    .filter(Room.is_reservable)
                    .scalar())

    def getReservationStats(self):
        return {
            'liveValid': 0,
            'liveCancelled': 0,
            'liveRejected': 0,
            'archivalValid': 0,
            'archivalValid': 0,
            'archivalValid': 0
        }

    def getAllBuildings(self):
        return (self.query
                    .with_entities(Room.building, Room)
                    .join(Location.rooms)
                    .filter(Room.building != None)
                    .group_by(Room.building)
                    .all())

        # # break-down the rooms by buildings
        # buildings = {}
        # for room in rooms:
        #     if room.building:

        #         # if it's the first room in that building, initialize the building
        #         building = buildings.get(room.building, None)
        #         if building is None:
        #             title = _("Building") + " %s" % room.building
        #             building = {'has_coordinates':False, 'number':room.building, 'title':title, 'rooms':[]}
        #             buildings[room.building] = building

        #         # if the room has coordinates, set the building coordinates
        #         if room.latitude and room.longitude:
        #             building['has_coordinates'] = True
        #             building['latitude'] = room.latitude
        #             building['longitude'] = room.longitude

        #         # add the room to its building
        #         if not self._forVideoConference or room.needsAVCSetup:
        #             building['rooms'].append(room.fossilize())

        # # filter the buildings with rooms and coordinates and return them
        # buildings_with_coords = [b for b in buildings.values() if b['rooms'] and b['has_coordinates']]
