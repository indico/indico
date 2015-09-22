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

import MaKaC.webinterface.pages.base as base
import MaKaC.webinterface.wcomponents as wcomponents
from MaKaC.common import timezoneUtils
from pytz import timezone
from MaKaC.conference import Category, Conference


class WPMainBase(base.WPDecorated):
    sidemenu_option = None

    def _display(self, params):
        target = self._rh.getTarget()

        # Check if user is administrator
        self._isAdmin = session.user and session.user.is_admin
        self._isCategoryManager = (
            self._isAdmin or
            (isinstance(target, Category) and target.canModify(self._getAW())) or
            (isinstance(target, Conference) and target.getOwner() and target.getOwner().canModify(self._getAW())))
        self._showAdmin = self._isAdmin or self._isCategoryManager

        self._timezone = timezone(timezoneUtils.DisplayTZ(self._getAW()).getDisplayTZ())
        params = dict(params, **self._kwargs)
        body = WMainBase(self._getBody(params), self._timezone, self._getNavigationDrawer(),
                         isFrontPage=self._isFrontPage(),
                         isRoomBooking=self._isRoomBooking(),
                         sideMenu=self._getSideMenu()).getHTML({"subArea": self._getSiteArea()})

        return self._applyDecoration(body)

    def _getBody(self, params):
        raise NotImplementedError('_getBody() needs to be overridden.')

    def _getSideMenu(self):
        return ''


class WMainBase(wcomponents.WTemplated):

    def __init__(self, page, timezone, navigation=None, isFrontPage=False, isRoomBooking=False, sideMenu=None):
        self._page = page
        self._navigation = navigation
        self._isFrontPage = isFrontPage
        self._isRoomBooking = isRoomBooking
        self._timezone = timezone
        self._sideMenu = sideMenu

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)

        vars['body'] = self._escapeChars(self._page)
        vars["isFrontPage"] = self._isFrontPage
        vars["isRoomBooking"] = self._isRoomBooking

        vars["navigation"] = ""
        if self._navigation:
            vars["navigation"] = self._navigation.getHTML(vars)

        vars["timezone"] = self._timezone
        vars['sideMenu'] = self._sideMenu

        return vars
