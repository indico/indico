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
Dates to skip in a reservation
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer

from indico.core.db.schema import Base


class ExcludedDay(Base):
    __tablename__ = 'reservation_excluded_days'

    start_date = Column(DateTime, nullable=False, primary_key=True)
    end_date = Column(DateTime, nullable=False, primary_key=True)

    reservation_id = Column(Integer, ForeignKey('reservations.id'), nullable=False)

    def __repr__(self):
        return '<ExcludedDay({0}, {1}, {2})>'.format(self.reservation_id,
                                                     self.start_date,
                                                     self.end_date)
