# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

import time
import uuid
from flask import session

from MaKaC.services.interface.rpc.common import (HTMLSecurityError,
                                                 NoReportError,
                                                 ResultWithWarning,
                                                 ServiceAccessError,
                                                 ServiceError, Warning)

from MaKaC.common import info
from MaKaC.common.cache import GenericCache
from MaKaC.common.fossilize import fossilize
from MaKaC.common.utils import validMail
from MaKaC.fossils.user import IAvatarAllDetailsFossil, IAvatarFossil
from MaKaC.services.implementation.base import LoggedOnlyService, AdminService, ParameterManager, ServiceBase
from MaKaC.user import AvatarHolder
from MaKaC.webinterface.common.person_titles import TitlesRegistry
from MaKaC.webinterface.common.timezones import TimezoneRegistry
from MaKaC.webinterface.mail import GenericMailer, GenericNotification
from indico.core.config import Config
from indico.core.db import db
from indico.modules.api import settings as api_settings
from indico.modules.api.models.keys import APIKey
from indico.util.i18n import _, get_all_locales, set_session_lang
from indico.util.redis import avatar_links
from indico.web.flask.util import url_for


class UserComparator(object):

    @staticmethod
    def cmpUsers(x, y):
        cmpResult = cmp(x["familyName"].lower(), y["familyName"].lower())
        if cmpResult == 0:
            cmpResult = cmp(x["firstName"].lower(), y["firstName"].lower())
        return cmpResult

    @staticmethod
    def cmpGroups(x, y):
        return cmp(x["name"].lower(), y["name"].lower())

class UserBaseService(LoggedOnlyService):

    def _checkParams(self):
        self._pm = ParameterManager(self._params)
        userId = self._pm.extract("userId", None)
        if userId is not None:
            ah = AvatarHolder()
            self._target = ah.getById(userId)
        else:
            raise ServiceError("ERR-U5", _("User id not specified"))

class UserModifyBase(UserBaseService):

    def _checkProtection(self):
        LoggedOnlyService._checkProtection(self)
        if self._aw.getUser():
            if not self._target.canModify( self._aw ):
                raise ServiceError("ERR-U6", _("You are not allowed to perform this request"))
        else:
            raise ServiceError("ERR-U7", _("You are currently not authenticated. Please log in again."))


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

class UserBasketBase:

    def _checkParams(self):
        ServiceBase._checkParams(self)
        self._pm = ParameterManager(self._params)
        userId = self._pm.extract("userId", pType=str, allowEmpty=True)
        if userId is not None:
            ah = AvatarHolder()
            self._target = ah.getById(userId)
        else:
            self._target = self._aw.getUser()

    def _checkProtection(self):
        if not self._aw.getUser():
            raise ServiceAccessError(_("You are currently not authenticated. Please log in again."))
        if not self._target.canUserModify(self._aw.getUser()):
            raise ServiceAccessError('Access denied')

class UserAddToBasket(LoggedOnlyService, UserBasketBase):

    def _checkParams(self):
        UserBasketBase._checkParams(self)

        self._userList = []
        for userData in self._params['value']:
            self._userList.append(AvatarHolder().getById(userData['id']))

    def _getAnswer(self):

        ##### Why not?
        #if (self._target in self._userList):
        #    raise ServiceError("ERR-U3","Trying to add user to his own favorites!")

        if (self._userList == []):
            raise ServiceError("ERR-U0","No users specified!")

        for user in self._userList:
            #we do not care if the user is already in the favourites
            self._target.getPersonalInfo().getBasket().addElement(user)

    def _checkProtection(self):
        LoggedOnlyService._checkProtection(self)
        UserBasketBase._checkProtection(self)


class UserRemoveFromBasket(LoggedOnlyService, UserBasketBase):
    def _checkParams(self):
        UserBasketBase._checkParams(self)
        self._userData = self._params['value']

    def _getAnswer( self):
        for obj in self._userData:
            if not self._target.getPersonalInfo().getBasket().deleteUser(obj['id']):
                raise ServiceError("ERR-U0","Element '%s' not found in favorites!" % obj['id'])

    def _checkProtection(self):
        LoggedOnlyService._checkProtection(self)
        UserBasketBase._checkProtection(self)

class UserListBasket(UserBasketBase, ServiceBase):

    """
    Service that lists the users belonging to the the user's "favorites"
    Should return None in case the user is not logged in.
    """

    def _checkParams(self):
        ServiceBase._checkParams(self)
        UserBasketBase._checkParams(self)
        self._allDetails = self._params.get("allDetails", False)

    def _getAnswer( self):

        if self._target:
            users = self._target.getPersonalInfo().getBasket().getUsers().values()

            if self._allDetails:
                fossilToUse = IAvatarAllDetailsFossil
            else:
                fossilToUse = IAvatarFossil

            fossilizedResult = fossilize(users, fossilToUse)
            fossilizedResult.sort(cmp=UserComparator.cmpUsers)
            return fossilizedResult

        else:
            return None

class UserGetEmail(LoggedOnlyService):

    def _checkParams(self):
        LoggedOnlyService._checkParams(self)
        self._target = self.getAW().getUser()


    def _getAnswer( self):
        if self._target:
            return self._target.getEmail()
        else:
            raise ServiceError("ERR-U4","User is not logged in")

class UserGetTimezone(ServiceBase):

    def _getAnswer(self):
        if self.getAW().getUser():
            tz = self.getAW().getUser().getTimezone()
        else:
            tz = info.HelperMaKaCInfo.getMaKaCInfoInstance().getTimezone()
        return tz


class UserGetSessionTimezone(ServiceBase):

    def _getAnswer(self):
        return session.timezone


class UserGetSessionLanguage(ServiceBase):

    def _getAnswer(self):
        if self.getAW().getSession():
            return self.getAW().getSession().getLang()
        else:
            minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
            return minfo.getLang()


class UserShowPastEvents(UserModifyBase):

    def _getAnswer( self):
        self._target.getPersonalInfo().setShowPastEvents(True)
        return True


class UserHidePastEvents(UserModifyBase):

    def _getAnswer( self):
        self._target.getPersonalInfo().setShowPastEvents(False)
        return True


class UserGetLanguages(UserBaseService):

    def _getAnswer(self):
        return list(get_all_locales().iteritems())


class UserSetLanguage(UserModifyBase):

    def _checkParams(self):
        UserModifyBase._checkParams(self)
        self._lang = self._params.get("lang", None)

    def _getAnswer(self):
        if self._lang and self._lang in get_all_locales():
            self._target.setLang(self._lang)
            set_session_lang(self._lang)
            return True
        else:
            return False


class UserGetTimezones(UserBaseService):

    def _getAnswer( self):
        return TimezoneRegistry.getList()


class UserSetTimezone(UserModifyBase):

    def _checkParams(self):
        UserModifyBase._checkParams(self)
        self._tz = self._params.get("tz",None)

    def _getAnswer( self):
        if self._tz and self._tz in TimezoneRegistry.getList():
            self._target.setTimezone(self._tz)
            return True
        return False


class UserGetDisplayTimezones(UserBaseService):

    def _getAnswer( self):
        if self._target.getDisplayTZMode() == "Event Timezone":
            tzMode = ["Event Timezone", "MyTimezone"]
        else:
            tzMode = ["MyTimezone", "Event Timezone"]
        return tzMode


class UserSetDisplayTimezone(UserModifyBase):

    def _checkParams(self):
        UserModifyBase._checkParams(self)
        self._tzMode = self._params.get("tzMode",None)

    def _getAnswer( self):
        if self._tzMode and self._tzMode in ["Event Timezone", "MyTimezone"]:
            self._target.setDisplayTZMode(self._tzMode)
            return True
        return False


class UserPersonalDataBase(UserModifyBase):

    _dataTypes = ["title", "surName", "name", "fullName", "straightFullName", "organisation",
                  "email", "secondaryEmails", "address", "telephone", "fax"]

    def _checkParams(self):
        self._pm = ParameterManager(self._params)
        userId = self._pm.extract("userId", None)
        if userId is not None:
            ah = AvatarHolder()
            self._user = self._avatar = self._target = ah.getById(userId)
        else:
            raise ServiceError("ERR-U5", _("User id not specified"))
        self._dataType = self._pm.extract("dataType", pType=str, allowEmpty=False)
        if self._dataType not in self._dataTypes:
            raise ServiceError("ERR-U7", _("Data argument is not valid"))


class UserRefreshRedisLinks(AdminService):
    def _checkParams(self):
        AdminService._checkParams(self)
        self._pm = ParameterManager(self._params)
        userId = self._pm.extract("userId", pType=str, allowEmpty=True)
        if userId is not None:
            ah = AvatarHolder()
            self._avatar = ah.getById(userId)
        else:
            self._avatar = self._aw.getUser()

    def _getAnswer(self):
        avatar_links.delete_avatar(self._avatar)  # clean start
        avatar_links.init_links(self._avatar)


methodMap = {
    "event.list": UserListEvents,
    "favorites.addUsers": UserAddToBasket,
    "favorites.removeUser": UserRemoveFromBasket,
    "favorites.listUsers": UserListBasket,
    "data.email.get": UserGetEmail,
    "timezone.get": UserGetTimezone,
    "session.timezone.get": UserGetSessionTimezone,
    "session.language.get": UserGetSessionLanguage,
    "showPastEvents": UserShowPastEvents,
    "hidePastEvents": UserHidePastEvents,
    "getLanguages": UserGetLanguages,
    "setLanguage": UserSetLanguage,
    "getTimezones": UserGetTimezones,
    "setTimezone": UserSetTimezone,
    "getDisplayTimezones": UserGetDisplayTimezones,
    "setDisplayTimezone": UserSetDisplayTimezone,
    "refreshRedisLinks": UserRefreshRedisLinks
}
