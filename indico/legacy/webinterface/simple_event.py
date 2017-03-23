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

import indico.legacy.webinterface.wcomponents as wcomponents
import indico.legacy.webinterface.pages.conferences as conferences
from indico.core.config import Config
from indico.legacy.webinterface.general import WebFactory
from indico.modules.events.cloning import EventCloner
from indico.web.flask.util import url_for


class WebFactory(WebFactory):
    id = 'lecture'
    iconURL = Config.getInstance().getSystemIconURL('lecture')
    name = "Lecture"
    description = """select this type if you want to set up a simple event thing without schedule, sessions, contributions, ... """

    def getIconURL():
        return WebFactory.iconURL
    getIconURL = staticmethod( getIconURL )

    @staticmethod
    def customiseToolsTabCtrl(tabCtrl):
        tabCtrl.getTabById("posters").enable()
        tabCtrl.getTabById("badges").disable()

    def getConfClone(rh, conf):
        return WPSEConfClone(rh, conf)
    getConfClone = staticmethod(getConfClone)


SimpleEventWebFactory = WebFactory


#################Conference Modification#############################



#####Tools # Stays the same as conference for now
class WPSEConfClone(conferences.WPConfClone):
    def _getPageContent(self, params):
        p = conferences.WConferenceClone(self._conf)
        pars = {
            "cloning": url_for('event_mgmt.confModifTools-performCloning', self._conf.as_event),
            "startTime": self._conf.as_event.start_dt_local.isoformat(),
            "cloneOptions": EventCloner.get_form_items(self._conf.as_event).encode('utf-8')
        }
        return p.getHTML(pars)


##################### Event Display ###################################

class WPSimpleEventDisplay( conferences.WPConferenceDisplayBase ):

    def _getHeader( self ):
        """
        """
        wc = wcomponents.WMenuSimpleEventHeader( self._getAW(),self._conf )
        return wc.getHTML( { "loginURL": self.getLoginURL(),\
                             "logoutURL": self.getLogoutURL(),\
                             "confId": self._conf.id,
                             "currentView": "static",\
                             "type": WebFactory.getId(),\
                             "dark": True } )

    def _getBody(self, params):
        raise NotImplementedError
