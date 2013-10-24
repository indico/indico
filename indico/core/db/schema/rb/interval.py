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
Schema of Generic Intervals for Nonbookable Days, Holidays
"""

from sqlalchemy import Column, Integer, ForeignKey, DateTime

from indico.core.db.schema import Base


class Interval(Base):
    __tablename__ = 'intervals'

    id = Column(Integer, primary_key=True)

    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

    room_id = Column(Integer, ForeignKey('rooms.id'), nullable=True)
    reservation_id = Column(Integer, ForeignKey('reservations.id'), nullable=True)
