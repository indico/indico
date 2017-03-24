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
from indico.legacy.webinterface.general import WebFactory
from indico.legacy.webinterface.pages.conferences import WPConferenceDisplayBase


class WebFactory(WebFactory):
    ##Don't remove this commentary. Its purpose is to be sure that those words/sentences are in the dictionary after extraction. It also prevents the developper to create an init for this class and update the 283 Webfactory occurences...
    ##_("Meeting")
    ##_("""this type is meant for events which contain several contributions or talks and that require schedulling and eventually organising of those contributions in sessions""")
    id = "meeting"
    name = "Meeting"
    description = """this type is meant for events which contain several contributions or talks and that require schedulling and eventually organising of those contributions in sessions"""


MeetingWebFactory = WebFactory


class WPMeetingDisplay( WPConferenceDisplayBase ):

    def _getNavigationDrawer(self):
        pars = {"target": self._conf.as_event, "isModif": False}
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
