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

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship, backref

from indico.core.db.schema import Base


class Room(Base):
    __tablename__ = 'rooms'

    id = Column(Integer, primary_key=True)

    # location
    location_id = Column(Integer, ForeignKey('locations.id'), nullable=False)

    # user-facing identifier of the room
    name = Column(String, nullable=False)

    # address
    site = Column(String)
    division = Column(String)
    building = Column(String, nullable=False)
    floor = Column(String, nullable=False)
    number = Column(String, nullable=False)

    # notifications
    resv_end_notification = Column(Boolean, nullable=False, default=True)
    resv_start_notification = Column(Integer, nullable=False, default=0)
    resvs_need_confirmation = Column(Boolean, nullable=False, default=False)
    resv_notification_to_assistance = Column(Boolean, nullable=False, default=True)
    resv_notification_to_responsible = Column(Boolean, nullable=False, default=True)

    # extra info about room
    telephone = Column(String)
    key_location = Column(String)

    capacity = Column(Integer, default=20)
    surface_area = Column(Integer)
    latitude = Column(String)
    longitude = Column(String)

    comments = Column(String)

    # just a pointer to avatar
    owner_id = Column(String, nullable=False)

    # reservations
    is_active = Column(Boolean, nullable=False, default=True)
    is_reservable = Column(Boolean, nullable=False, default=True)
    max_advance_days = Column(Integer, nullable=False, default=30)

    # links to other tables
    reservations = relationship('Reservation',
                                backref='room',
                                cascade='all, delete-orphan')

    bookable_times = relationship('BookableTime',
                                  backref=backref('room', order_by='BookableTime.start_time'),
                                  cascade='all, delete-orphan')

    nonbookable_dates = relationship('Interval',
                                     backref=backref('room', order_by='Interval.end_date desc'),
                                     cascade='all, delete-orphan')

    photos = relationship('Photo',
                          backref='room',
                          cascade='all, delete-orphan')

    attributes = relationship('RoomAttribute',
                              backref='room',
                              cascade='all, delete-orphan')

    blocked_rooms = relationship('BlockedRoom',
                                 backref='room',
                                 cascade='all, delete-orphan')

    def __repr__(self):
        return '<Room({0}, {1}, {2})>'.format(self.id, self.location_id, self.name)
