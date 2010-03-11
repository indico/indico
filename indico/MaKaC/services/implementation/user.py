# -*- coding: utf-8 -*-
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

from MaKaC.services.implementation.base import LoggedOnlyService
from MaKaC.services.implementation.base import ServiceBase

import MaKaC.user as user
from MaKaC.services.interface.rpc.common import ServiceError

from MaKaC.common.PickleJar import DictPickler
from MaKaC.common import info

import time
from MaKaC.fossils.user import IAvatarAllDetailsFossil, IAvatarDetailedFossil,\
    IAvatarMinimalFossil
from MaKaC.common.fossilize import fossilize

from MaKaC.rb_location import CrossLocationQueries

class UserListEvents(LoggedOnlyService):

    def _checkParams(self):
        LoggedOnlyService._checkParams(self)

        self._time = self._params.get('time', None)
        self._target = self.getAW().getUser()

    def __exportElemDataFactory(self, moment):
        return lambda elem: {
            'id': elem[0].getId(),
            'title': elem[0].getTitle(),
            'roles': [elem[1]],
            'timestamp':time.mktime(elem[0].getStartDate().timetuple()),
            'startDate':str(elem[0].getStartDate().strftime("%d/%m/%Y")),
            'endDate':str(elem[0].getEndDate().strftime("%d/%m/%Y")),
            'startTime':str(elem[0].getStartDate().strftime("%H:%M")),
            'endTime':str(elem[0].getEndDate().strftime("%H:%M")),
            'type': moment,
            'evtType': elem[0].getVerboseType()
        }

    def _getAnswer( self):

        events = []

        self._target.getTimedLinkedEvents().sync()

        if (not self._time) or self._time == 'past':
            events.extend( map( self.__exportElemDataFactory('past'),
                               self._target.getTimedLinkedEvents().getPast()))

        if (not self._time) or self._time == 'present':
            events.extend( map(self.__exportElemDataFactory('present'),
                              self._target.getTimedLinkedEvents().getPresent()))

        if (not self._time) or self._time == 'future':
            events.extend( map(self.__exportElemDataFactory('future'),
                              self._target.getTimedLinkedEvents().getFuture()))

        jsonData = {}

        for event in events:
            if jsonData.has_key(event['id']):
                jsonData[event['id']]['roles'].append(event['roles'][0])
            else:
                jsonData[event['id']] = event

        return jsonData


class UserAddToBasket(LoggedOnlyService):

    def _checkParams(self):
        LoggedOnlyService._checkParams(self)

        self._userList = []

        for userData in self._params['value']:
            self._userList.append(user.AvatarHolder().getById(userData['id']))

        self._target = self.getAW().getUser()

    def _getAnswer(self):

        ##### Why not?
        #if (self._target in self._userList):
        #    raise ServiceError("ERR-U3","Trying to add user to his own favorites!")

        if (self._userList == []):
            raise ServiceError("ERR-U0","No users specified!")

        for user in self._userList:
            #we do not care if the user is already in the favourites
            self._target.getPersonalInfo().getBasket().addElement(user)


class UserRemoveFromBasket(LoggedOnlyService):
    def _checkParams(self):
        LoggedOnlyService._checkParams(self)

        self._userData = self._params['value']

        self._target = self.getAW().getUser()

    def _getAnswer( self):

        for obj in self._userData:
            self._obj = user.AvatarHolder().getById(obj['id'])

            if (self._obj == None):
                raise ServiceError("ERR-U0","User does not exist!")

            #we do not care if the user is already out of the favourites
            self._target.getPersonalInfo().getBasket().deleteElement(self._obj)


class UserListBasket(ServiceBase):

    """
    Service that lists the users belonging to the the user's "favorites"
    Should return None in case the user is not logged in.
    """

    def _checkParams(self):
        ServiceBase._checkParams(self)

        self._target = self.getAW().getUser()
        self._detailLevel = self._params.get("detailLevel", "max")

    def _getAnswer( self):

        if self._target:
            users = self._target.getPersonalInfo().getBasket().getUsers().values()

            if self._detailLevel == "min":
                fossilToUse = IAvatarMinimalFossil
            elif self._detailLevel == "medium":
                fossilToUse = IAvatarDetailedFossil
            elif self._detailLevel == "max":
                fossilToUse = IAvatarAllDetailsFossil

            return fossilize(users, fossilToUse)
        else:
            return None


class UserGetPersonalInfo(LoggedOnlyService):

    def _checkParams(self):
        LoggedOnlyService._checkParams(self)

        self._target = self.getAW().getUser()


    def _getAnswer( self):
        return DictPickler.pickle(self._target.getPersonalInfo())


class UserGetEmail(LoggedOnlyService):

    def _checkParams(self):
        LoggedOnlyService._checkParams(self)
        self._target = self.getAW().getUser()


    def _getAnswer( self):
        if self._target:
            return self._target.getEmail()
        else:
            raise ServiceError("ERR-U4","User is not logged in")


class UserSetPersonalInfo(LoggedOnlyService):

    def _checkParams(self):
        LoggedOnlyService._checkParams(self)

        self._target = self.getAW().getUser()
        self._info = self._params.get("value", None)

    def _getAnswer( self):

        if self._info == None:
            return UserGetPersonalInfo(self._params, self._aw.getIP(), self._aw.getSession()).process()

        pInfo = self._target.getPersonalInfo()

        DictPickler.update(pInfo, self._info)
        return DictPickler.pickle(pInfo)


class UserGetTimezone(ServiceBase):

    def _getAnswer(self):
        if self.getAW().getUser():
            tz = self.getAW().getUser().getTimezone()
        else:
            tz = info.HelperMaKaCInfo.getMaKaCInfoInstance().getTimezone()
        return tz


class UserGetSessionTimezone(ServiceBase):

    def _getAnswer(self):
        tz = self.getAW().getSession().getVar("ActiveTimezone")
        return tz


class UserGetSessionLanguage(ServiceBase):

    def _getAnswer(self):
        if self.getAW().getSession():
            return self.getAW().getSession().getLang()
        else:
            minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
            return minfo.getLang()

class UserCanBook(LoggedOnlyService):

    def _checkParams(self):
        LoggedOnlyService._checkParams(self)
        self._user = self.getAW().getUser()
        self._roomID = int(self._params.get("roomID", ""))
        self._roomLocation = self._params.get("roomLocation", "")
        self._room = CrossLocationQueries.getRooms(roomID = self._roomID, location = self._roomLocation)

    def _getAnswer( self):
        if self._user and self._room:
            if not self._room.isActive and not self._user.isAdmin():
                return False
            if not self._room.canBook( self._user ) and not self._room.canPrebook( self._user ):
                return False
            return True
        return False

methodMap = {
    "event.list": UserListEvents,
    "favorites.addUsers": UserAddToBasket,
    "favorites.removeUser": UserRemoveFromBasket,
    "favorites.listUsers": UserListBasket,
    "data.email.get": UserGetEmail,
    "personalinfo.get": UserGetPersonalInfo,
    "personalinfo.set": UserSetPersonalInfo,
    "timezone.get": UserGetTimezone,
    "session.timezone.get": UserGetSessionTimezone,
    "session.language.get": UserGetSessionLanguage,
    "canBook": UserCanBook
}
