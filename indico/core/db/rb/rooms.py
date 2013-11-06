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

from indico.core.db import db


class Room(db.Model):
    __tablename__ = 'rooms'

    id = db.Column(db.Integer, primary_key=True)

    # location
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)

    # user-facing identifier of the room
    name = db.Column(db.String, nullable=False)

    # address
    site = db.Column(db.String)
    division = db.Column(db.String)
    building = db.Column(db.String, nullable=False)
    floor = db.Column(db.String, nullable=False)
    number = db.Column(db.String, nullable=False)

    # notifications
    notification_for_start = db.Column(db.Integer, nullable=False, default=0)
    notification_for_end = db.Column(db.Boolean, nullable=False, default=True)
    notification_for_responsible = db.Column(db.Boolean, nullable=False, default=True)
    notification_for_assistance = db.Column(db.Boolean, nullable=False, default=True)
    reservations_need_confirmation = db.Column(db.Boolean, nullable=False, default=False)

    # extra info about room
    telephone = db.Column(db.String)
    key_location = db.Column(db.String)

    capacity = db.Column(db.Integer, default=20)
    surface_area = db.Column(db.Integer)
    latitude = db.Column(db.String)
    longitude = db.Column(db.String)

    comments = db.Column(db.String)

    # just a pointer to avatar
    owner_id = db.Column(db.String, nullable=False)

    # reservations
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_reservable = db.Column(db.Boolean, nullable=False, default=True)
    max_advance_days = db.Column(db.Integer, nullable=False, default=30)

    # links to other tables
    reservations = db.relationship('Reservation',
                                   backref='room',
                                   cascade='all, delete-orphan')

    bookable_times = db.relationship('BookableTime',
                                     backref=db.backref('room', order_by='BookableTime.start_time'),
                                     cascade='all, delete-orphan')

    nonbookable_dates = db.relationship('Interval',
                                        backref=db.backref('room', order_by='Interval.end_date desc'),
                                        cascade='all, delete-orphan')

    photos = db.relationship('Photo',
                             backref='room',
                             cascade='all, delete-orphan')

    attributes = db.relationship('RoomAttribute',
                                 backref='room',
                                 cascade='all, delete-orphan')

    blocked_rooms = db.relationship('BlockedRoom',
                                    backref='room',
                                    cascade='all, delete-orphan')

    def __repr__(self):
        return '<Room({0}, {1}, {2})>'.format(self.id, self.location_id, self.name)
