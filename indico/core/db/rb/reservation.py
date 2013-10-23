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

"""

from sqlalchemy import Column, String, DateTime, Boolean, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Reservation(Base):
    __tablename__ = 'reservations'

    reservationId = Column(Integer, primary_key=True)

    createdDate = Column(DateTime)
    startDate = Column(DateTime)
    endDate = Column(DateTime)

    bookedForId = Column(String)
    bookedForName = Column(String)
    createdBy = Column(String)

    contactEmail = Column(String)
    contactPhone = Column(String)

    isConfirmed = Column(Boolean)
    isCancelled = Column(Boolean)
    isRejected = Column(Boolean)

    needsAVCSupport = Column(Boolean)
    needsAssistance = Column(Boolean)

    startEndNotification = Column(Boolean)

    reason = Column(String)

    # excludedDays
    # history
    # roomId
    # useVC
    # usesAVC
    # repeatibility
