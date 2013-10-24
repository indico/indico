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
Schema of Room for Room Booking module
"""

from datetime import time

import pytz
from sqlalchemy import Column, String, Boolean, Integer, Time, ForeignKey
from sqlalchemy.orm import relationship, backref

from indico.core.db.schema import Base
from indico.core.db.schema.rb.trait import traits_rooms


class Room(Base):
    __tablename__ = 'rooms'

    id = Column(Integer, primary_key=True)

    # location
    location_id = Column(Integer, ForeignKey('locations.id'))

    # user-facing identifier of the room
    name = Column(String, nullable=False)

    # address
    site = Column(String)
    division = Column(String, nullable=False)
    building = Column(String, nullable=False)
    floor = Column(String, nullable=False)
    room_number = Column(String, nullable=False)

    # notifications
    resv_end_notification = Column(Boolean, default=True)
    resv_start_notification = Column(Boolean, default=True)
    resv_start_notification_before = Column(Boolean, default=True)
    resvs_need_confirmation = Column(Boolean, default=False)
    resv_notification_to_assistance = Column(Boolean, default=True)
    resv_notification_to_responsible = Column(Boolean, default=True)

    # extra info about room
    telephone = Column(String)
    where_is_key = Column(String)

    capacity = Column(Integer, default=20)
    surface_area = Column(Integer)
    latitude = Column(String)
    longtitude = Column(String)

    comments = Column(String)

    # just a pointer to avatar
    responsible_id = Column(String)

    # reservations
    is_active = Column(Boolean, default=True)
    is_reservable = Column(Boolean, default=True)
    max_advance_days = Column(Integer, default=30)
    daily_book_time_start = Column(Time, default=time(7, 0, tzinfo=pytz.timezone('UTC')))
    daily_book_time_end = Column(Time, default=time(16, 30, tzinfo=pytz.timezone('UTC')))

    # links to other tables
    reservations = relationship('Reservation',
                                backref='room',
                                cascade='all, delete, delete-orphan')

    nonbookable_dates = relationship('Interval',
                                     backref=backref('room', order_by='Interval.end_date desc'),
                                     cascade='all, delete, delete-orphan')

    photos = relationship('Photo',
                          backref='room',
                          cascade='all, delete, delete-orphan')

    traits = relationship('Trait',
                          secondary=traits_rooms,
                          backref='rooms')

    blocked_rooms = relationship('BlockedRoom',
                                 backref='room',
                                 cascade='all, delete, delete-orphan')
