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


class Room(Base):
    __tablename__ = 'rooms'

    roomId = Column(Integer, primary_key=True)

    name = Column(String)
    building = Column(String)
    capacity = Column(Integer)
    division = Column(String)
    floor = Column(String)
    latitude = Column(String)
    longtitude = Column(String)
    surfaceArea = Column(String)
    site = Column(String)
    roomNr = Column(String)

    isActive = Column(Boolean)
    isReservable = Column(Boolean)
    maxAdvanceDays = Column(Integer)

    responsibleId = Column(String)
    telephone = Column(String)
    whereIsKey = Column(String)

    resvEndNotification = Column(Boolean)
    resvStartNotification = Column(Boolean)
    resvStartNotificationBefore = Column(Boolean)
    resvsNeedConfirmation = Column(Boolean)
    resvNotificationAssistance = Column(Boolean)
    resvNotificationToResponsible = Column(Boolean)

    # dailyBookablePeriod
    # nonBookableDates
    # photoId
    # equipment
    # avaibleVC
    # comments
    # customAttrs
