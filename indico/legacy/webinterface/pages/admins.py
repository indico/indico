# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from indico.legacy.webinterface import wcomponents
from indico.legacy.webinterface.pages.main import WPMainBase
from indico.legacy.webinterface.wcomponents import render_header
from indico.util.i18n import _
from indico.web.menu import render_sidemenu


class WPAdminsBase(WPMainBase):
    def getJSFiles(self):
        return WPMainBase.getJSFiles(self) + self._includeJSPackage('Management')

    def _getHeader(self):
        return render_header()

    def _getBody(self, params):
        self._createTabCtrl()
        self._setActiveTab()

        frame = WAdminFrame()

        return frame.getHTML({
            "body": self._getPageContent(params),
            "sideMenu": render_sidemenu('admin-sidemenu', active_item=self.sidemenu_option)
        })

    def _getNavigationDrawer(self):
        return wcomponents.WSimpleNavigationDrawer(_("Administration"), bgColor="white")

    def _createTabCtrl(self):
        pass

    def _getTabContent(self):
        raise NotImplementedError

    def _setActiveTab(self):
        pass

    def _getPageContent(self, params):
        raise NotImplementedError


class WAdminFrame(wcomponents.WTemplated):
    def __init__( self ):
        pass

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["titleTabPixels"] = self.getTitleTabPixels()
        vars["intermediateVTabPixels"] = self.getIntermediateVTabPixels()
        return vars

    def getIntermediateVTabPixels( self ):
        return 0

    def getTitleTabPixels( self ):
        return 260
