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

from pytz import timezone

from indico.modules import ModuleHolder
from indico.util.i18n import _

from MaKaC.common import timezoneUtils
from MaKaC.webinterface.pages.main import WPMainBase
from MaKaC.webinterface.wcomponents import WTemplated


class WPNews(WPMainBase):

    def _getBody(self, params):
        wc = WNews(tz=timezone(timezoneUtils.DisplayTZ(self._getAW()).getDisplayTZ()))
        return wc.getHTML()

    def getCSSFiles(self):
        return WPMainBase.getCSSFiles(self) + self._asset_env['news_sass'].urls()

    def _getTitle(self):
        return WPMainBase._getTitle(self) + " - " + _("News")


class WNews(WTemplated):

    def __init__(self, tz):
        WTemplated.__init__(self)
        self._tz = tz

    def getVars(self):
        vars = WTemplated.getVars(self)

        newsModule = ModuleHolder().getById("news")
        vars["news"] = newsModule.getNewsItemsList()
        vars["tz"] = self._tz

        return vars
