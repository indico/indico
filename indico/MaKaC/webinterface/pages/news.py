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

from MaKaC.webinterface.pages.main import WPMainBase
import MaKaC.webinterface.wcomponents as wcomponents
from MaKaC.i18n import _
from pytz import timezone
from MaKaC.common import timezoneUtils

from indico.modules import ModuleHolder

class WPNews(WPMainBase):

    def _getBody(self, params):
        wc = WNews(tz = timezone(timezoneUtils.DisplayTZ(self._getAW()).getDisplayTZ()))
        return wc.getHTML()

    def _getTitle(self):
        return WPMainBase._getTitle(self) + " - " + _("News")


class WNews(wcomponents.WTemplated):

    def __init__(self, tz):
        wcomponents.WTemplated.__init__(self)
        self._tz = tz

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )

        newsModule = ModuleHolder().getById("news")
        vars["news"] = newsModule.getNewsItemsList()
        vars["tz"] = self._tz

        return vars
