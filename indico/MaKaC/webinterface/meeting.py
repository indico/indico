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

import MaKaC.webinterface.wcomponents as wcomponents
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.pages.conferences as conferences
from indico.core.config import Config
from MaKaC.webinterface.general import WebFactory
from MaKaC.webinterface.pages.conferences import WPConferenceDisplayBase
from indico.modules.events.cloning import EventCloner


class WebFactory(WebFactory):
    ##Don't remove this commentary. Its purpose is to be sure that those words/sentences are in the dictionary after extraction. It also prevents the developper to create an init for this class and update the 283 Webfactory occurences...
    ##_("Meeting")
    ##_("""this type is meant for events which contain several contributions or talks and that require schedulling and eventually organising of those contributions in sessions""")
    id = "meeting"
    iconURL = Config.getInstance().getSystemIconURL('meeting')
    name = "Meeting"
    description = """this type is meant for events which contain several contributions or talks and that require schedulling and eventually organising of those contributions in sessions"""


######### Conference Creation/Display/Modifications ##########################

    @staticmethod
    def getIconURL():
        return WebFactory.iconURL

    @staticmethod
    def customiseToolsTabCtrl(tabCtrl):
        tabCtrl.getTabById("badges").disable()
        tabCtrl.getTabById("posters").enable()

    @staticmethod
    def getConfClone(rh, conf):
        return WPMConfClone(rh, conf)


MeetingWebFactory = WebFactory

#################Conference Modification#############################


class WPMConfClone(conferences.WPConfClone):

    def _getPageContent(self, params):
        p = conferences.WConferenceClone(self._conf)
        pars = {
            "cloning": urlHandlers.UHConfPerformCloning.getURL(self._conf),
            "startTime": self._conf.as_event.start_dt_local.isoformat(),
            "cloneOptions": ''
        }
        pars['cloneOptions'] += EventCloner.get_form_items(self._conf.as_event).encode('utf-8')
        return p.getHTML(pars)


class WPMeetingDisplay( WPConferenceDisplayBase ):

    def _getNavigationDrawer(self):
        pars = {"target": self._conf, "isModif": False}
        return wcomponents.WNavigationDrawer( pars )

    def _getHeader( self ):
        """
        """

        if hasattr(self, "_view"):
            currentView = self._view
        else:
            currentView = "static"

        wc = wcomponents.WMenuMeetingHeader( self._getAW(),self._conf )
        return wc.getHTML( { "loginURL": self.getLoginURL(),\
                             "logoutURL": self.getLogoutURL(),\
                             "confId": self._conf.id,
                             "currentView": currentView,\
                             "type": WebFactory.getId(),\
                             "filterActive": False,\
                             "dark": True } )

    def _getBody(self, params):
        raise NotImplementedError
