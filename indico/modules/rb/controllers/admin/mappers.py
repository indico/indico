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

from flask import session
from werkzeug.exceptions import Forbidden

from MaKaC import roomMapping
from MaKaC.webinterface import locators, urlHandlers
from MaKaC.webinterface.rh.admins import RHAdminBase

from indico.util.i18n import _
from indico.modules.rb.util import rb_is_admin
from indico.modules.rb.views.admin import mappers as mapper_views


class RHRoomMapperProtected(RHAdminBase):
    def _checkProtection(self):
        if not session.user:
            self._checkSessionUser()
        elif not rb_is_admin(session.user):
            raise Forbidden(_('You are not authorized to take this action.'))


class RHRoomMapperBase(RHRoomMapperProtected):
    def _checkParams(self, params):
        RHRoomMapperProtected._checkParams(self, params)
        self._roomMapper = locators.RoomMapperWebLocator(params).getObject()
        self._doNotSanitizeFields.append('regexps')


class RHRoomMappers(RHRoomMapperProtected):
    _uh = urlHandlers.UHRoomMappers

    def _checkParams(self, params):
        RHAdminBase._checkParams(self, params)
        self._params = params

    def _process(self):
        return mapper_views.WPRoomMapperList(self, self._params).display()


class RHRoomMapperCreation(RHRoomMapperProtected):
    _uh = urlHandlers.UHNewRoomMapper

    def _process(self):
        return mapper_views.WPRoomMapperCreation(self).display()


class RHRoomMapperPerformCreation(RHRoomMapperProtected):
    _uh = urlHandlers.UHRoomMapperPerformCreation

    def _process(self):
        rm = roomMapping.RoomMapper()
        rm.setValues(self._getRequestParams())
        roomMapping.RoomMapperHolder().add(rm)
        self._redirect(urlHandlers.UHRoomMapperDetails.getURL(rm))


class RHRoomMapperDetails(RHRoomMapperBase):
    _uh = urlHandlers.UHRoomMapperDetails

    def _process(self):
        return mapper_views.WPRoomMapperDetails(self, self._roomMapper).display()


class RHRoomMapperModification(RHRoomMapperBase):
    _uh = urlHandlers.UHRoomMapperModification

    def _process(self):
        return mapper_views.WPRoomMapperModification(self, self._roomMapper).display()


class RHRoomMapperPerformModification(RHRoomMapperBase):
    _uh = urlHandlers.UHRoomMapperPerformModification

    def _process(self):
        self._roomMapper.setValues(self._getRequestParams())
        self._redirect(urlHandlers.UHRoomMapperDetails.getURL(self._roomMapper))
