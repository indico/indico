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

from MaKaC.services.implementation.base import ParameterManager
from MaKaC.services.implementation.user import UserModifyBase
from indico.ext.calendaring.storage import disablePluginForUser, enablePluginForUser

"""
Services for calendaring plugins
"""


class UserShowOutlookEvents(UserModifyBase):

    def _getAnswer(self):
        self._pm = ParameterManager(self._params)
        enablePluginForUser(self._pm.extract("userId", None))
        return True


class UserHideOutlookEvents(UserModifyBase):

    def _getAnswer(self):
        self._pm = ParameterManager(self._params)
        disablePluginForUser(self._pm.extract("userId", None))
        return True

methodMap = {
    "user.showOutlookEvents": UserShowOutlookEvents,
    "user.hideOutlookEvents": UserHideOutlookEvents,
}
