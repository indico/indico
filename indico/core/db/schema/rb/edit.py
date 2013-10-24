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
Schema of modifications done on a reservation
"""

from sqlalchemy import Column, String, DateTime, Integer, ForeignKey

from indico.core.db.schema import Base


class Edit(Base):
    __tablename__ = 'edits'

    id = Column(Integer, primary_key=True)

    timestamp = Column(DateTime)
    info = Column(String, nullable=False)
    responsible_id = Column(String, nullable=False)
    reservation_id = Column(Integer, ForeignKey('reservations.id'))
