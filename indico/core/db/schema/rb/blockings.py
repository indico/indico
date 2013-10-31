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
Schema of a blocking (dates, related rooms and principals)
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from indico.core.db.schema import Base


class Blocking(Base):
    __tablename__ = 'blockings'

    id = Column(Integer, primary_key=True)

    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow())
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

    reason = Column(String, nullable=False)
    allowed = relationship('BlockingPrincipal',
                           backref='blocking',
                           cascade='all, delete, delete-orphan')

    blocked_rooms = relationship('BlockedRoom',
                                 backref='blocking',
                                 cascade='all, delete, delete-orphan')
