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
import MaKaC.webinterface.linking as linking
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

    def getConferenceDisplayPage( rh, conf, params):
        return WPSimpleEventDisplay( rh, conf )
    getConferenceDisplayPage = staticmethod( getConferenceDisplayPage )

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

    def _getWComponent( self ):
        return WSimpleEventCreation( self._target, rh = self._rh )


class WSimpleEventCreation(category.WConferenceCreation):
    def __init__( self, targetCateg, type="simple_event", rh = None ):
        self._categ = targetCateg
        self._type = type
        self._rh = rh

    def getVars( self ):
        vars = category.WConferenceCreation.getVars( self )
        vars["event_type"] = WebFactory.getId()
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

    def _getBody( self, params ):
        wc = WSimpleEventDisplay( self._getAW(), self._conf )
        pars = { \
    "modifyURL": urlHandlers.UHConferenceModification.getURL( self._conf ), \
    "sessionModifyURLGen": urlHandlers.UHSessionModification.getURL, \
    "contribModifyURLGen": urlHandlers.UHContributionModification.getURL, \
    "subContribModifyURLGen":  urlHandlers.UHSubContribModification.getURL}
        return wc.getHTML( pars )


class WSimpleEventDisplay:

    def __init__( self, aw, conference ):
        self._aw = aw
        self._conf = conference

    def getHTML( self, params ):
        if self._conf.canAccess( self._aw ):
            return WSimpleEventFullDisplay( self._aw, self._conf ).getHTML( params )
        else:
            return WSimpleEventMinDisplay( self._aw, self._conf ).getHTML( params )


class WSimpleEventBaseDisplay(wcomponents.WTemplated):

    def __init__( self, aw, conference ):
        self._aw = aw
        self._conf = conference

    def __getHTMLRow( self, title, body, allowEmptyBody=1 ):
        str = """
                <tr>
                    <td align="right" valign="top" nowrap>
                        <b><strong>%s:</strong></b>
                    </td>
                    <td>
                        <font size="-1" face="arial" color="#333333">%s</font>
                    </td>
                </tr>"""%(title, body)
        if not allowEmptyBody:
            if body.strip() == "":
                return ""
        return str

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        tzUtil = timezoneUtils.DisplayTZ(self._aw,self._conf)
        tz = tzUtil.getDisplayTZ()
        sdate = self._conf.getStartDate().astimezone(timezone(tz))
        edate = self._conf.getEndDate().astimezone(timezone(tz))
        fsdate, fedate = format_date(sdate, format='full'), format_date(edate, format='full')
        fstime, fetime = sdate.strftime("%H:%M"), edate.strftime("%H:%M")
        if sdate.strftime("%Y%B%d") == edate.strftime("%Y%B%d"):
            timeInterval = fstime
            if sdate.strftime("%H%M") != edate.strftime("%H%M"):
                timeInterval = "%s - %s"%(fstime, fetime)
            vars["dateInterval"] = "<b>%s (%s) (%s)</b>"%( fsdate, timeInterval, tz )
        else:
            vars["dateInterval"] = "from <b>%s (%s)</b> to <b>%s (%s) (%s)</b>"%(\
                                fsdate, fstime, fedate, fetime, tz)
        vars["title"] = self._conf.getTitle()
        vars["description"] =  self.__getHTMLRow(  _("Description"), self._conf.getDescription(), 0 )
        vars["location"] = ""
        location = self._conf.getLocation()
        if location:
            vars["location"] = self.__getHTMLRow(  _("Location"), "%s<br><small>%s</small>"%(location.getName(), location.getAddress()) )
        vars["room"] = ""
        room = self._conf.getRoom()
        if room:
            roomLink = linking.RoomLinker().getHTMLLink( room, location )
            vars["room"] = self.__getHTMLRow( _("Room"), roomLink )
        vars["moreInfo"] = self.__getHTMLRow(  _("Additional Info"), self._conf.getContactInfo(), 0 )
        al = []
        if self._conf.getChairmanText() != "":
            al.append( self._conf.getChairmanText() )
        for organiser in self._conf.getChairList():
            al.append( """<a href="mailto:%s">%s</a>"""%(organiser.getEmail(),\
                                                     organiser.getFullName() ) )
        vars["contact"] = self.__getHTMLRow("Contact", "<br>".join( al ), 0 )
        vars["modifyItem"] = ""
        if self._conf.canModify( self._aw ):
            vars["modifyItem"] = ('<a href="{}"><img src="{}" border="0" alt="Jump to the modification interface"></a> '
                                  .format(vars["modifyURL"], Config.getInstance().getSystemIconURL("popupMenu")))
        return vars


class WSimpleEventFullDisplay(WSimpleEventBaseDisplay):
    pass


class WSimpleEventMinDisplay(WSimpleEventBaseDisplay):
    pass
