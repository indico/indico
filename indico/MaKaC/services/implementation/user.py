# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from flask import session

from indico.modules.users import User
from indico.util.i18n import _
from indico.util.redis import avatar_links
from MaKaC.services.interface.rpc.common import ServiceError
from MaKaC.services.implementation.base import LoggedOnlyService, AdminService, ParameterManager
from MaKaC.user import AvatarHolder


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
            if not self._target.canModify(self._aw):
                raise ServiceError("ERR-U6", _("You are not allowed to perform this request"))
        else:
            raise ServiceError("ERR-U7", _("You are currently not authenticated. Please log in again."))


class UserGetEmail(LoggedOnlyService):
    def _checkParams(self):
        LoggedOnlyService._checkParams(self)
        self._target = self.getAW().getUser()

    def _getAnswer(self):
        if self._target:
            return self._target.getEmail()
        else:
            raise ServiceError("ERR-U4", "User is not logged in")


class UserShowPastEvents(UserModifyBase):
    def _getAnswer(self):
        self._target.getPersonalInfo().setShowPastEvents(True)
        return True


class UserHidePastEvents(UserModifyBase):
    def _getAnswer(self):
        self._target.getPersonalInfo().setShowPastEvents(False)
        return True


class UserRefreshRedisLinks(AdminService):
    def _checkParams(self):
        AdminService._checkParams(self)
        self._pm = ParameterManager(self._params)
        user_id = self._pm.extract("userId", pType=int, allowEmpty=True)
        self._user = User.get(user_id) if user_id is not None else session.user

    def _getAnswer(self):
        avatar_links.delete_avatar(self._user)  # clean start
        avatar_links.init_links(self._user)


methodMap = {
    "data.email.get": UserGetEmail,
    "showPastEvents": UserShowPastEvents,
    "hidePastEvents": UserHidePastEvents,
    "refreshRedisLinks": UserRefreshRedisLinks
}
