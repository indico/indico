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
Schema of a reservation
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    String
)
from sqlalchemy.orm import relationship, backref

from indico.core.db.schema import Base


class Reservation(Base):
    __tablename__ = 'reservations'

    id = Column(Integer, primary_key=True)

    # dates
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    repeat_unit = Column(SmallInteger, nullable=False, default=0)  # week, month, year, etc.
    repeat_period = Column(SmallInteger, nullable=False, default=0)  # 1, 2, 3, etc.

    # user
    booked_for_id = Column(String, nullable=False)
    booked_for_name = Column(String, nullable=False)
    created_by = Column(String, nullable=False)

    # room
    room_id = Column(Integer, ForeignKey('rooms.id'), nullable=False)

    # reservation specific
    contact_email = Column(String)
    contact_phone = Column(String)

    is_confirmed = Column(Boolean, nullable=False)
    is_cancelled = Column(Boolean, nullable=False, default=False)
    is_rejected = Column(Boolean, nullable=False, default=False)

    reason = Column(String, nullable=False)

    edits = relationship('Edit',
                         backref='reservation',
                         cascade='all, delete-orphan')

    attributes = relationship('ReservationAttribute',
                              backref='reservation',
                              cascade='all, delete-orphan')

    excluded_dates = relationship('ExcludedDay',
                                  backref=backref('reservation', order_by='ExcludedDay.start_date'),
                                  cascade='all, delete-orphan')

    # moved to reservation (custom) attributes
    # needs_video_conference_support = Column(Boolean, default=False)
    # needs_assistance = Column(Boolean, default=False)
    # uses_video_conference = Column(Boolean, default=False)

    def __repr__(self):
        return '<Reservation({0}, {1}, {2}, {3}, {4})>'.format(self.id, self.room_id,
                                                               self.booked_for_name,
                                                               self.start_date,
                                                               self.end_date)
