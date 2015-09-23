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

import urllib
import MaKaC.webinterface.wcomponents as wcomponents
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.pages.category as category
import MaKaC.webinterface.pages.conferences as conferences
import MaKaC.webinterface.pages.contributions as contributions
import MaKaC.webinterface.pages.subContributions as subContributions
import MaKaC.webinterface.pages.sessions as sessions
import MaKaC.webinterface.navigation as navigation
from MaKaC.conference import EventCloner
from indico.core.config import Config
from xml.sax.saxutils import quoteattr
from MaKaC.webinterface.general import WebFactory
from MaKaC.webinterface.pages.category import WPConferenceCreationMainData
from MaKaC.webinterface.pages.conferences import WPConferenceDisplayBase
from MaKaC.i18n import _
from indico.util.i18n import i18nformat
from indico.util.date_time import format_date


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
    def getEventCreationPage( rh, targetCateg ):
        return WPMeetingEventCreation( rh, targetCateg )

    @staticmethod
    def getConferenceDisplayPage( rh, conference, params ):
        return conferences.WPMeetingTimeTable(rh,conference, "static", "meeting", {})

    @staticmethod
    def getIconURL():
        return WebFactory.iconURL

    @staticmethod
    def customiseToolsTabCtrl(tabCtrl):
        tabCtrl.getTabById("badges").disable()
        tabCtrl.getTabById("posters").enable()

    @staticmethod
    def getConfModif(rh, conf):
        return WPMConfModif(rh, conf)

    @staticmethod
    def getConfModifAC(rh, conf):
        return WPMConfModifAC(rh, conf)

    @staticmethod
    def getConfModifListings(rh, conf):
        return WPMConfModifListings(rh, conf)

    @staticmethod
    def getConfClone(rh, conf):
        return WPMConfClone(rh, conf)

    @staticmethod
    def getConfModifSchedule (rh, conf):
        return WPMConfModifSchedule(rh, conf)

    @staticmethod
    def getTimeTableCustomizePDF(rh, conf, view):
        return WPMTimeTableCustomizePDF(rh, conf, view)

############# Subcontribution Display##########################################

    def getSubContributionDisplay(rh, subcontrib):
        return WPMSubContributionDisplay(rh, subcontrib)
    getSubContributionDisplay = staticmethod(getSubContributionDisplay)

############# Contribution Display #############################################

    def getContributionDisplay(rh, contrib, hideFull = 0 ):
        return WPMContributionDisplay(rh,contrib, hideFull)
    getContributionDisplay = staticmethod(getContributionDisplay)

############# Contribution modification #########################################
    def getContributionModification(rh, contrib):
        return WPMContributionModification(rh,contrib)
    getContributionModification = staticmethod(getContributionModification)

    def getContribModifSC(rh,contrib):
        return WPMContributionModifSC(rh,contrib)
    getContribModifSC = staticmethod(getContribModifSC)

    def getContribModifAC(rh, contrib):
        return WPMContribModifAC(rh,contrib)
    getContribModifAC = staticmethod(getContribModifAC)

    def getContributionModifTools(rh, contrib):
        return WPMContributionModifTools (rh,contrib)
    getContributionModifTools = staticmethod(getContributionModifTools)

    def getContributionEditData(rh, contrib):
        return WPMContribEditData(rh, contrib)
    getContributionEditData = staticmethod (getContributionEditData)

    def getContribAddSC(rh, contrib):
        return WPMContribAddSC(rh,contrib)
    getContribAddSC = staticmethod(getContribAddSC)

########## Session Display###########################################

    def getSessionDisplay(rh,session):
        return WPMSessionDisplay (rh,session)
    getSessionDisplay = staticmethod(getSessionDisplay)

############Session Modificiations###########################################

    def getSessionDataModification(self, session):
        return WPMSessionDataModification (self,session)
    getSessionDataModification = staticmethod(getSessionDataModification)

    def getSessionModification(rh,session):
        return WPMSessionModification(rh,session)
    getSessionModification = staticmethod(getSessionModification)

    def getSessionModifAC(rh, session):
        return WPMSessionModifAC(rh,session)
    getSessionModifAC = staticmethod(getSessionModifAC)

    def getSessionModifTools(rh, session):
        return WPMSessionModifTools(rh,session)
    getSessionModifTools = staticmethod(getSessionModifTools)

    def getSessionModifComm(rh, session):
        return WPMSessionModifComm(rh,session)
    getSessionModifComm = staticmethod(getSessionModifComm)

    def getSessionModifCommEdit(rh, session):
        return WPMSessionModifCommEdit(rh,session)
    getSessionModifCommEdit = staticmethod(getSessionModifCommEdit)

    def getSessionModifSchedule(rh,session):
        return WPMSessionModifSchedule(rh,session)
    getSessionModifSchedule = staticmethod(getSessionModifSchedule)


MeetingWebFactory = WebFactory

#################### Event Creation #####################################
class WPMeetingEventCreation( WPConferenceCreationMainData):

    def _getWComponent( self ):
        return WMeetingCreation( self._target, rh = self._rh )

class WMeetingCreation(category.WConferenceCreation):
    def __init__( self, targetCateg, type="meeting", rh = None ):
        self._categ = targetCateg
        self._type = type
        self._rh = rh

    def getVars( self ):
        vars = category.WConferenceCreation.getVars( self )
        vars["event_type"] = WebFactory.getId()
        return vars

################# Subcontribution Display ##############################

class WPMSubContributionDisplay(subContributions.WPSubContributionDisplay):
    def _applyConfDisplayDecoration( self, body ):
        frame = WMConfDisplayFrame( self._getAW(), self._conf )
        frameParams = {\
              "logoURL": self.logo_url, \
                      }
        if self.event.has_logo:
            frameParams["logoURL"] = self.logo_url

        confTitle = self._conf.getTitle()
        colspan=""
        imgOpen=""
        padding=""" style="padding:0px" """

        body = i18nformat("""
                <td class="confBodyBox" %s %s>
                    %s
                    <table border="0" cellpadding="0" cellspacing="0"
                                align="center" width="95%%">
                        <tr>
                            <td class="formTitle" width="100%%"> _("SubContribution View") - %s</td>
                        </tr>
                        <tr>
                            <td align="left" valign="middle" width="100%%">
                                <b><br>%s</b>
                            </td>
                       </tr>
                    </table>
                     <!--Main body-->
                    %s
                </td>""")%(colspan,padding,imgOpen,confTitle,
                        self._getNavigationBarHTML(),
                        body)
        return frame.getHTML( body, frameParams)

    def _getBody(self,params):
        wc=WMSubContributionDisplay(self._getAW(),self._subContrib)
        return wc.getHTML()


class WMSubContributionDisplayBase(subContributions.WSubContributionDisplayBase):
    def getVars( self ):
        vars = subContributions.WSubContributionDisplayBase.getVars( self )
        vars["modifyIcon"] = Config.getInstance().getSystemIconURL( "modify" )
        vars ["modifyURL"]= urlHandlers.UHSubContributionModification.getURL(self._subContrib)
        return vars

class WMSubContributionDisplay(subContributions.WSubContributionDisplay):
    def getHTML(self,params={}):
        if self._subContrib.canModify( self._aw ):
            c = WMSubContributionDisplayFull( self._aw, self._subContrib)
            return c.getHTML( params )
        if self._subContrib.canView( self._aw ):
            c = WMSubContributionDisplayMin( self._aw, self._subContrib)
            return c.getHTML( params )
        return ""

class WMSubContributionDisplayFull(WMSubContributionDisplayBase):
    pass

class WMSubContributionDisplayMin (WMSubContributionDisplayBase):
    pass


################# Contribution Display ################################

class WPMContributionDisplay(contributions.WPContributionDisplay):
    def _applyConfDisplayDecoration( self, body ):
        frame = WMConfDisplayFrame( self._getAW(), self._conf )
        frameParams = {\
              "logoURL": self.logo_url, \
                      }
        if self.event.has_logo:
            frameParams["logoURL"] = self.logo_url

        confTitle = self._conf.getTitle()
        colspan=""
        imgOpen=""
        padding=""
        padding=""" style="padding:0px" """

        body =  i18nformat("""
                <td class="confBodyBox" %s %s>
                    %s
                    <table border="0" cellpadding="0" cellspacing="0"
                                align="center" valign="top" width="95%%">
                        <tr>
                            <td class="formTitle" width="100%%">%s</td>
                        </tr>
                        <tr>
                            <td align="left" valign="middle" width="100%%">
                                <b><br>%s</b>
                            </td>
                       </tr>
                    </table>
                     <!--Main body-->
                    %s
                </td>""")%(colspan,padding,imgOpen,confTitle,
                        self._getNavigationBarHTML(),
                        body)
        return frame.getHTML( body, frameParams)

    def _getBody(self,params):
        wc=WMContributionDisplay(self._getAW(),self._contrib)
        return wc.getHTML()


class WMContributionDisplay(contributions.WContributionDisplay):
    def getHTML(self,params={}):
        if self._contrib.canAccess( self._aw ):
            c = WMContributionDisplayFull( self._aw, self._contrib)
            return c.getHTML( params )
        if self._contrib.canView( self._aw ):
            c = WMContributionDisplayMin( self._aw, self._contrib)
            return c.getHTML( params )
        return ""

class WMContributionDisplayBase(contributions.WContributionDisplayBase):
    def getVars( self ):
        vars = contributions.WContributionDisplayBase.getVars( self )
        return vars

class WMContributionDisplayFull(WMContributionDisplayBase):
    pass

class WMContributionDisplayMin (WMContributionDisplayBase):
    pass

#################Session Display ######################################

class WPMSessionDisplay(sessions.WPSessionDisplay):
    navigationEntry =  navigation.NEMeetingSessionDisplay
    def _applyConfDisplayDecoration( self, body ):
        frame = WMConfDisplayFrame( self._getAW(), self._conf )
        frameParams = {\
              "logoURL": self.logo_url, \
                      }
        if self.event.has_logo:
            frameParams["logoURL"] = self.logo_url

        confTitle = self._conf.getTitle()
        colspan=""
        imgOpen=""
        padding=""
        padding=""" style="padding:0px" """

        body =  i18nformat("""
                <td class="confBodyBox" %s %s>
                    %s
                    <table border="0" cellpadding="0" cellspacing="0"
                                align="center" valign="top" width="95%%">
                        <tr>
                            <td class="formTitle" width="100%%"> _("Session View") - %s</td>
                        </tr>
                        <tr>
                            <td align="left" valign="middle" width="100%%">
                                <b><br>%s</b>
                            </td>
                       </tr>
                    </table>
                     <!--Main body-->
                    %s
                </td>""")%(colspan,padding,imgOpen,confTitle,
                        self._getNavigationBarHTML(),
                        body)
        return frame.getHTML( body, frameParams)

    def _getBody(self, params):
        wc = WMSessionDisplay(self._getAW(), self._session)
        return wc.getHTML()

class WMSessionDisplay(sessions.WSessionDisplay):
    def getHTML(self):
        if self._session.canAccess( self._aw ):
            c = WMSessionDisplayFull(self._aw,self._session)
            return c.getHTML()
        return ""



class WMSessionDisplayBase(sessions.WSessionDisplayBase):
    pass

class WMSessionDisplayFull(WMSessionDisplayBase):
    pass

#################Contribution Modification##############################


class WPMContributionModification(contributions.WPContributionModification):

    def _getTabContent( self, params ):
        from MaKaC.webinterface.pages.contributions import WContribModifMain
        wc = WContribModifMain(self._contrib, eventType="meeting")
        return wc.getHTML()

class WPMContribEditData(contributions.WPEditData):
    pass

class WPMContributionModifSC(contributions.WPContribModifSC):
    pass

class WPMContribModifAC(contributions.WPContribModifAC):
    pass

class WPMContributionModifTools(contributions.WPContributionModifTools):
    pass
#    def _getBody( self, params ):
#        return ContribModifTabsFrame._getBody(self, params)

class WPMContribAddSC(contributions.WPContribAddSC):
    pass


class WMConfDisplayFrame(conferences.WConfDisplayFrame):
    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        vars["logo"] = ""
        if self.event.has_logo:
            vars["logoURL"] = self.event.logo_url
            vars["logo"] = "<img src=\"%s\" alt=\"%s\" border=\"0\">"%(vars["logoURL"], self._conf.getTitle())
        vars["confTitle"] = self._conf.getTitle()
        vars["displayURL"] = urlHandlers.UHConferenceDisplay.getURL(self._conf)
        vars["imgConferenceRoom"] = Config.getInstance().getSystemIconURL( "conferenceRoom" )
        #################################
        # Fermi timezone awareness      #
        #################################
        vars["confDateInterval"] = i18nformat("""_("from") %s _("to") %s""")%(format_date(self._conf.getStartDate(), format='long'), format_date(self._conf.getEndDate(), format='long'))
        if self._conf.getStartDate().strftime("%d%B%Y") == \
                self._conf.getEndDate().strftime("%d%B%Y"):
            vars["confDateInterval"] = format_date(self._conf.getStartDate(), format='long')
        elif self._conf.getStartDate().month == self._conf.getEndDate().month:
            vars["confDateInterval"] = "%s-%s %s"%(self._conf.getStartDate().day, self._conf.getEndDate().day, format_date(self._conf.getStartDate(), format='MMMM yyyy'))
        #################################
        # Fermi timezone awareness(end) #
        #################################
        vars["body"] = self._body
        vars["confLocation"] = ""
        if self._conf.getLocationList():
            vars["confLocation"] =  self._conf.getLocationList()[0].getName()
            vars["supportEmail"] = ""
        if self._conf.getSupportInfo().hasEmail():
            mailto = quoteattr("""mailto:%s?subject=%s"""%(self._conf.getSupportInfo().getEmail(), urllib.quote( self._conf.getTitle() ) ))
            vars["supportEmail"] =  _("""<a href=%s class="confSupportEmail"><img src="%s" border="0" alt="email"> %s</a>""")%(mailto,
                                                        Config.getInstance().getSystemIconURL("mail"),
                                                        self._conf.getSupportInfo().getCaption())
        return vars

    def getHTML( self, body, params ):
        self._body = body
        return wcomponents.WTemplated.getHTML( self, params )


#################Conference Modification#############################

##Main##
class WPMConfModif(conferences.WPConferenceModification):
    def _getPageContent( self, params ):
        wc = WMConfModifMainData(self._conf, self._ct, self._rh)
        pars = { "type": params.get("type",""), "conferenceId": self._conf.getId() }
        return wc.getHTML( pars )


class WMConfModifMainData(conferences.WConfModifMainData):
    pass


##Access Control ##
class WPMConfModifAC(conferences.WPConfModifAC):
    pass


class WPMConfModifListings (conferences.WPConfModifListings):

    def _getTabContent( self, params ):
        wc = WMConfModifListings( self._conf )
        return wc.getHTML()


class WMConfModifListings (conferences.WConfModifListings):
    pass


class WPMConfClone(conferences.WPConfClone):

    def _getTabContent(self, params):
        p = conferences.WConferenceClone(self._conf)
        pars = {
            "cancelURL": urlHandlers.UHConfModifTools.getURL(self._conf),
            "cloning": urlHandlers.UHConfPerformCloning.getURL(self._conf),
            "cloneOptions": i18nformat("""<li><input type="checkbox" name="cloneTimetable" id="cloneTimetable" value="1" checked="checked" />_("Full timetable")</li>
                     <li><ul style="list-style-type: none;"><li><input type="checkbox" name="cloneSessions" id="cloneSessions" value="1" />_("Sessions")</li></ul></li>
                     <li><input type="checkbox" name="cloneParticipants" id="cloneParticipants" value="1" checked="checked" />_("Participants")</li>
               """)
        }
        pars['cloneOptions'] += EventCloner.get_plugin_items(self._conf)
        return p.getHTML(pars)


##TimeTable view##
class WPMConfModifSchedule(conferences.WPConfModifScheduleGraphic):
    pass

######################### Session View #######################

##TabControl####
class WPMSessionDataModification(sessions.WPSessionDataModification):
    def _setupTabCtrl(self):
        self._tabContribs.disable()

class WPMSessionModification( sessions.WPSessionModification ):
    def _setupTabCtrl(self):
        self._tabContribs.disable()


class WPMSessionModifAC(sessions.WPSessionModifAC):
    def _setupTabCtrl(self):
        self._tabContribs.disable()

class WPMSessionModifTools(sessions.WPSessionModifTools):
    def _setupTabCtrl(self):
        self._tabContribs.disable()

class WPMSessionModifComm(sessions.WPSessionModifComm):
    def _setupTabCtrl(self):
        self._tabContribs.disable()

class WPMSessionModifCommEdit(sessions.WPSessionCommEdit):
    def _setupTabCtrl(self):
        self._tabContribs.disable()

class WPMSessionModifSchedule(sessions.WPSessionModifSchedule):
    pass

######################################################################
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
                             "confId": self._conf.getId(),\
                             "currentView": currentView,\
                             "type": WebFactory.getId(),\
                             "filterActive": False,\
                             "dark": True } )

    def _getBody(self, params):
        raise NotImplementedError


class WPMTimeTableCustomizePDF(WPMeetingDisplay):

    def __init__(self, rh, conf, view):
        WPMeetingDisplay.__init__(self, rh, conf)
        # We keep track of the view so that we can return to the meeting
        # display page with the same layout when cancelling the pdf export
        self._view = view
        # An hack to make sure that the background is the same as the header
        self._extraCSS.append("body { background: #424242; } ")

    def _getFooter( self ):
        wc = wcomponents.WFooter()
        p = {"dark":True}
        return wc.getHTML(p)

    def _getBody( self, params ):
        wc = WMTimeTableCustomizePDF( self._conf, self._view )
        return wc.getHTML(params)


class WMTimeTableCustomizePDF(wcomponents.WTemplated):

    def __init__(self, conf, view):
        self._conf = conf
        self._view = view

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars['showDays'] = vars.get('showDays', 'all')
        vars['showSessions'] = vars.get('showSessions', 'all')
        url=urlHandlers.UHConfTimeTablePDF.getURL(self._conf)
        # Add the view as a parameter so we can keep track of it
        # when the pdf export is cancelled.
        url.addParam("view", self._view)
        vars["getPDFURL"]=quoteattr(str(url))
        return vars
