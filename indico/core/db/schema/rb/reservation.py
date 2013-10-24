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
Schema of Reservation for Room Booking module
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Short, String
from sqlalchemy.orm import relationship, backref

from indico.core.db.schema import Base
from indico.core.db.schema.rb.trait import traits_reservations


class Reservation(Base):
    __tablename__ = 'reservations'

    id = Column(Integer, primary_key=True)

    # dates
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow())
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    repeatibility = Column(Short, default=0)

    # user
    booked_for_id = Column(String, nullable=False)
    booked_for_name = Column(String, nullable=False)
    created_by = Column(String, nullable=False)

    # room
    room_id = Column(Integer, ForeignKey('rooms.id'))

    # reservation specific
    contact_email = Column(String)
    contact_phone = Column(String)

    is_confirmed = Column(Boolean, default=True)
    is_cancelled = Column(Boolean, default=False)
    is_rejected = Column(Boolean, default=False)

    needs_video_conference_support = Column(Boolean, default=False)
    needs_assistance = Column(Boolean, default=False)
    uses_video_conference = Column(Boolean, default=False)
    notification_for_start_and_end = Column(Boolean, default=True)

    reason = Column(String, nullable=False)

    edits = relationship('Edit',
                         backref='reservation',
                         cascade='all, delete, delete-orphan')

    traits = relationship('Trait',
                          secondary=traits_reservations,
                          backref='reservations')

    exceluded_dates = relationship('Interval',
                                   backref=backref('reservation', order_by='Interval.end_date desc'),
                                   cascade='all, delete, delete-orphan')
