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

import MaKaC.webinterface.wcomponents as wcomponents
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.pages.category as category
import MaKaC.webinterface.pages.conferences as conferences
from indico.core.config import Config
from MaKaC.webinterface.general import WebFactory
from MaKaC.webinterface.pages.category import WPConferenceCreationMainData
from MaKaC.webinterface import meeting
from MaKaC.i18n import _
from indico.modules.events.cloning import EventCloner
from indico.util.date_time import format_date
import MaKaC.common.timezoneUtils as timezoneUtils
from pytz import timezone


class WebFactory(WebFactory):
    id = "simple_event"
    iconURL = Config.getInstance().getSystemIconURL('lecture')
    name = "Lecture"
    description = """select this type if you want to set up a simple event thing without schedule, sessions, contributions, ... """

    def getEventCreationPage( rh, targetCateg ):
        return WPSimpleEventCreation( rh, targetCateg )
    getEventCreationPage = staticmethod( getEventCreationPage )

    def getIconURL():
        return WebFactory.iconURL
    getIconURL = staticmethod( getIconURL )

    @staticmethod
    def customiseToolsTabCtrl(tabCtrl):
        tabCtrl.getTabById("posters").enable()
        tabCtrl.getTabById("badges").disable()

    def getConfModif(rh, conf):
        return WPSEConfModif(rh, conf)
    getConfModif = staticmethod(getConfModif)

    def getConfModifAC(rh, conf):
        return WPSEConfModifAC(rh, conf)
    getConfModifAC = staticmethod(getConfModifAC)

    def getConfClone(rh, conf):
        return WPSEConfClone(rh, conf)
    getConfClone = staticmethod(getConfClone)


#################### Participants #####################################

    def getConfModifParticipantsNewPending(rh, conf):
        return WPSEConfModifParticipantsNewPending(rh, conf)
    getConfModifParticipantsNewPending = staticmethod(getConfModifParticipantsNewPending)


SimpleEventWebFactory = WebFactory


#################Conference Modification#############################

##Main##
class WPSEConfModif(conferences.WPConferenceModification):
    def _getPageContent( self, params ):
        wc = WSEConfModifMainData(self._conf, self._ct, self._rh)
        pars = { "type": params.get("type",""), "conferenceId": self._conf.getId() }
        return wc.getHTML( pars )


class WSEConfModifMainData(meeting.WMConfModifMainData):
    pass


#####Access Control # stays the same as conference for now
class WPSEConfModifAC(conferences.WPConfModifAC):
    pass


#####Tools # Stays the same as conference for now
class WPSEConfModifToolsBase (conferences.WPConfModifToolsBase):

    def __init__(self, rh, conf):
        conferences.WPConfModifToolsBase.__init__(self, rh, conf)


class WPSEConfClone(conferences.WPConfClone):
    def _getPageContent(self, params):
        p = conferences.WConferenceClone( self._conf )
        pars = {
            "cancelURL": urlHandlers.UHConfModifTools.getURL(self._conf),
            "cloning": urlHandlers.UHConfPerformCloning.getURL(self._conf),
            "cloneOptions": EventCloner.get_form_items(self._conf.as_event).encode('utf-8')
        }
        return p.getHTML(pars)


#################### Event Creation #####################################
class WPSimpleEventCreation( WPConferenceCreationMainData):

    def _getWComponent(self):
        return WSimpleEventCreation(self.category, rh=self._rh)


class WSimpleEventCreation(category.WConferenceCreation):
    def __init__( self, targetCateg, type="simple_event", rh = None ):
        self._categ = targetCateg
        self._type = type
        self._rh = rh

    def getVars( self ):
        vars = category.WConferenceCreation.getVars( self )
        vars["event_type"] = 'lecture'
        return vars

##################### Event Display ###################################

class WPSimpleEventDisplay( conferences.WPConferenceDisplayBase ):

    def _getHeader( self ):
        """
        """
        wc = wcomponents.WMenuSimpleEventHeader( self._getAW(),self._conf )
        return wc.getHTML( { "loginURL": self.getLoginURL(),\
                             "logoutURL": self.getLogoutURL(),\
                             "confId": self._conf.getId(),\
                             "currentView": "static",\
                             "type": WebFactory.getId(),\
                             "dark": True } )

    def _getBody(self, params):
        raise NotImplementedError
