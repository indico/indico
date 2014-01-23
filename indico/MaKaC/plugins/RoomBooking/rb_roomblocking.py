# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
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
from MaKaC.common.Locators import Locator

"""
Part of Room Booking Module (rb_)
"""

from datetime import datetime, time
from MaKaC.rb_tools import fromUTC, toUTC
from MaKaC.user import AvatarHolder
from MaKaC.rb_factory import Factory


class RoomBlockingBase(object):
    """
    Generic room blocking, Data Access Layer independant.
    """

    # !=> Properties are in the end of class definition

    def __init__(self):
        pass

    @staticmethod
    def getTotalCount():
        return Factory.newRoomBlocking().getTotalCount()

    @staticmethod
    def getAll():
        return Factory.newRoomBlocking().getAll()

    @staticmethod
    def getById(id):
        return Factory.newRoomBlocking().getById(id)

    @staticmethod
    def getByOwner(owner):
        return Factory.newRoomBlocking().getByOwner(owner)

    @staticmethod
    def getByRoom(room, active=-1):
        return Factory.newRoomBlocking().getByRoom(room, active)

    @staticmethod
    def getByDate(date):
        return Factory.newRoomBlocking().getByDate(date)

    @staticmethod
    def getByDateSpan(begin, end):
        return Factory.newRoomBlocking().getByDateSpan(begin, end)

    def addBlockedRoom(self, blockedRoom):
        """
        Add a blocked room to the blocking
        """
        blockedRoom.block = self
        self.blockedRooms.append(blockedRoom)

    def delBlockedRoom(self, blockedRoom):
        """
        Remove a blocked room from the blocking and the indexes
        """
        # Unindexing here is necessary as after deletion the only reference to
        # the blocked room is is the room->blockedroom index which will not be
        # updated when recreating the blocking's indexes
        blockedRoom._unindex()
        blockedRoom.block = None
        self.blockedRooms.remove(blockedRoom)

    def canModify(self, user):
        """
        The following persons are authorized to modify a blocking:
        - owner (the one who created the blocking)
        - admin (of course)
        """
        if not user:
            return False
        if user.isAdmin() or self.isOwnedBy(user):
            return True
        return False

    def canDelete(self, user):
        return self.canModify(user)

    def canOverride(self, user, room=None, explicitOnly=False):
        """
        The following persons are authorized to override a blocking:
        - owner (the one who created the blocking)
        - any users on the blocking's ACL
        - unless explicitOnly is set: admins and room owners (if a room is given)
        """
        if not user:
            return False
        if self.isOwnedBy(user):
            return True
        if not explicitOnly:
            if user.isAdmin():
                return True
            elif room and room.isOwnedBy(user):
                return True
        for principal in self.allowed:
            if principal.containsUser(user):
                return True

        return False

    def isOwnedBy(self, avatar):
        """
        Returns True if avatar is the one who inserted this
        blocking. False otherwise.
        """
        if not self._createdBy:
            return None
        if self._createdBy == avatar.id:
            return True
        return False

    def _getCreatedByUser(self):
        if self._createdBy is None:
            return None
        return AvatarHolder().getById(self._createdBy)

    def _setCreatedByUser(self, user):
        self._createdBy = user.id

    def getLocator(self):
        d = Locator()
        if self.id is not None:
            d['blockingId'] = self.id
        return d

    # ==== Private ===================================================

    # datetime (DT) converters --------

    def _getCreatedDT(self):
        return fromUTC(self._utcCreatedDT)

    def _setCreatedDT(self, localNaiveDT):
        self._utcCreatedDT = toUTC(localNaiveDT)

    # --------------------------------

    # Needed for CalendarDayIndex
    def getStartDate(self):
        return datetime.combine(self.startDate, time())

    def getEndDate(self):
        return datetime.combine(self.endDate, time())

    # ==== Properties ===================================================

    id = None
    startDate = None
    endDate = None
    message = None
    allowed = None
    blockedRooms = None

    # DO NOT use these directly!
    # Use properties instead
    _utcCreatedDT = None
    _createdBy = None

    createdDT = property(_getCreatedDT, _setCreatedDT)  # datetime - when the blocking was created; internally UTC, accepted and returned in local/DST
    createdByUser = property(_getCreatedByUser, _setCreatedByUser)
