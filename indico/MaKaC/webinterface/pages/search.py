# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2012 European Organization for Nuclear Research (CERN).
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

from MaKaC.webinterface.pages.category import WPCategoryDisplayBase
from MaKaC.webinterface.pages.conferences import WPConferenceDisplayBase
from MaKaC.webinterface.wcomponents import WTemplated, WNavigationDrawer

class WSearch(WTemplated):
    def __init__(self, target, aw):
        self._target = target
        self._aw = aw
        WTemplated.__init__(self)


class WPSearch:

    def _getBody(self, params):
        wc = WSearch(self._target, self._getAW())
        self._setParams(params)

        return wc.getHTML(params)


class WPSearchCategory(WPSearch, WPCategoryDisplayBase):

    def __init__(self, rh, target):
        WPCategoryDisplayBase.__init__(self, rh, target)

    def _setParams(self, params):
        params['confId'] = None
        params['categId'] = self._target.getId()
        params['categName'] = self._target.getTitle()

    def _getNavigationDrawer(self):
        if self._target.isRoot() and self._target.isRoot():
            return
        else:
            pars = {"target": self._target, "isModif": False}
            return WNavigationDrawer( pars )


class WPSearchConference(WPSearch, WPConferenceDisplayBase):

    def __init__(self, rh, target):
        WPConferenceDisplayBase.__init__(self, rh, target)
        self._target = target

    def _setParams(self, params):
        params['confId'] = self._conf.getId()
        params['categId'] = None
