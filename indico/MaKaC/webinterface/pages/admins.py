# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
from MaKaC.common.PickleJar import DictPickler
from pytz import timezone

import os
from MaKaC.common.general import *
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.wcomponents as wcomponents
import MaKaC.webinterface.pages.conferences as conferences
from MaKaC.webinterface.pages.conferences import WConfModifBadgePDFOptions
import MaKaC.common.info as info
import MaKaC.webcast as webcast
from MaKaC.common.Configuration import Config
import MaKaC.conference as conference
import MaKaC.user as user
from MaKaC.common import utils, timezoneUtils
from MaKaC.webinterface.common.person_titles import TitlesRegistry
from MaKaC.webinterface.common.timezones import TimezoneRegistry, DisplayTimezoneRegistry
from MaKaC.common.Announcement import getAnnoucementMgrInstance
from MaKaC.webinterface.pages.main import WPMainBase
from MaKaC.common.timerExec import HelperTaskList, Alarm
from MaKaC.common.timerExec import task as Task
from MaKaC.common.pendingQueues import PendingSubmitterReminder, PendingManagerReminder, PendingCoordinatorReminder
from MaKaC.authentication import AuthenticatorMgr
from MaKaC import roomMapping
from MaKaC import domain
from MaKaC.plugins.base import PluginsHolder
import MaKaC.common.indexes as indexes
import MaKaC.webinterface.personalization as personalization
from cgi import escape
import re
from MaKaC.i18n import _
from MaKaC.modules.base import ModulesHolder
from MaKaC.plugins.pluginLoader import PluginLoader

class WPAdminsBase( WPMainBase ):

    _userData = ['favorite-user-ids']

    def _getSiteArea(self):
        return "AdministrationArea"

    def getJSFiles(self):
        return WPMainBase.getJSFiles(self) + \
               self._includeJSPackage('Admin') + \
               self._includeJSPackage('Management')

    def _getHeader( self ):
        """
        """
        wc = wcomponents.WHeader( self._getAW() )
        return wc.getHTML( { "subArea": self._getSiteArea(), \
                             "loginURL": self._escapeChars(str(self.getLoginURL())),\
                             "logoutURL": self._escapeChars(str(self.getLogoutURL())), \
                             "tabControl": self._getTabControl(), \
                             "loginAsURL": self.getLoginAsURL() } )

    def _createSideMenu(self):
        self._sideMenu = wcomponents.ManagementSideMenu()

        mainSection = wcomponents.SideMenuSection()

        self._generalSettingsMenuItem = wcomponents.SideMenuItem(_("General settings"),
            urlHandlers.UHAdminArea.getURL())
        mainSection.addItem( self._generalSettingsMenuItem)

        self._localdefMenuItem = wcomponents.SideMenuItem(_("Local Definitions"),
            urlHandlers.UHAdminLocalDefinitions.getURL())
        mainSection.addItem( self._localdefMenuItem)

        self._usersAndGroupsMenuItem = wcomponents.SideMenuItem(_("Users and Groups"),
            urlHandlers.UHUserManagement.getURL())
        mainSection.addItem( self._usersAndGroupsMenuItem)

        self._domainsMenuItem = wcomponents.SideMenuItem(_("IP Domains"),
            urlHandlers.UHDomains.getURL())
        mainSection.addItem( self._domainsMenuItem)

        self._roomsMenuItem = wcomponents.SideMenuItem(_("Rooms"),
            urlHandlers.UHRoomBookingPluginAdmin.getURL())
        mainSection.addItem( self._roomsMenuItem)

        self._templatesMenuItem = wcomponents.SideMenuItem(_("Templates"),
            urlHandlers.UHTemplates.getURL())
        mainSection.addItem( self._templatesMenuItem)

        self._servicesMenuItem = wcomponents.SideMenuItem(_("Services"),
            urlHandlers.UHWebcast.getURL())
        mainSection.addItem( self._servicesMenuItem)

        self._pluginsMenuItem = wcomponents.SideMenuItem(_("Plugins"),
            urlHandlers.UHAdminPlugins.getURL())
        mainSection.addItem( self._pluginsMenuItem)

        self._homepageMenuItem = wcomponents.SideMenuItem(_("Homepage"),
            urlHandlers.UHUpdateNews.getURL())
        mainSection.addItem( self._homepageMenuItem)

        self._systemMenuItem = wcomponents.SideMenuItem(_("System"),
            urlHandlers.UHAdminsSystem.getURL())
        mainSection.addItem( self._systemMenuItem)

        self._sideMenu.addSection(mainSection)


    def _getBody( self, params ):
        self._createSideMenu()
        self._setActiveSideMenuItem()

        self._createTabCtrl()
        self._setActiveTab()

        frame = WAdminFrame()
        p = { "body": self._getPageContent( params ),
              "sideMenu": self._sideMenu.getHTML() }

        return frame.getHTML( p )

    def _getNavigationDrawer(self):
        return wcomponents.WSimpleNavigationDrawer(_("Server Admin"), urlHandlers.UHAdminArea.getURL, bgColor="white" )

    def _createTabCtrl(self):
        pass

    def _getTabContent(self):
        return "nothing"

    def _setActiveTab(self):
        pass

    def _setActiveSideMenuItem(self):
        pass

    def _getPageContent(self, params):
        return "nothing"

class WAdmins(wcomponents.WTemplated):

    def __init__(self):
        pass

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        vars["title"] = minfo.getTitle()
        vars["organisation"] = minfo.getOrganisation()
        vars["supportEmail"] = minfo.getSupportEmail()
        vars["publicSupportEmail"] = minfo.getPublicSupportEmail()
        vars["noReplyEmail"] = minfo.getNoReplyEmail()
        vars["lang"] = minfo.getLang()
        vars["address"] = ""
        if minfo.getCity() != "":
            vars["address"] = minfo.getCity()
        if minfo.getCountry() != "":
            if vars["address"] != "":
                vars["address"] = "%s (%s)"%(vars["address"], minfo.getCountry())
            else:
                vars["address"] = "%s"%minfo.getCountry()
        try:
            vars["timezone"] = minfo.getTimezone()
        except:
            vars["timezone"] = 'UTC'
        vars["adminList"] = wcomponents.WPrincipalTable().getHTML( minfo.getAdminList().getList(),  None, vars["addAdminsURL"], vars["removeAdminsURL"], selectable=False )
        vars["systemIconAdmins"] = Config.getInstance().getSystemIconURL( "admin" )
        iconDisabled = str(Config.getInstance().getSystemIconURL( "disabledSection" ))
        iconEnabled = str(Config.getInstance().getSystemIconURL( "enabledSection" ))
        vars["features"] = ""
        url = urlHandlers.UHAdminSwitchCacheActive.getURL()
        if minfo.isCacheActive():
            icon = iconEnabled
        else:
            icon = iconDisabled
        vars["features"] += _("""<div style="margin-bottom: 5px"><a href="%s"><img src="%s" border="0" alt="Toggle on/off" style="float:left; padding-right: 5px"> _("Cache Indico Pages")</a></div>""") % (str(url), icon)
        url = urlHandlers.UHAdminSwitchNewsActive.getURL()
        if minfo.isNewsActive():
            icon = iconEnabled
        else:
            icon = iconDisabled
        #vars["features"] += _("""<br><a href="%s"><img src="%s" border="0" alt="Toggle on/off"> _("News Pages") </a>""") % (str(url), icon)
        #vars["announcement"] = WAnnouncementModif().getHTML( vars )
        vars["features"] += _("""<div style="margin-bottom: 5px"><a href="%s"><img src="%s" border="0" style="float:left; padding-right: 5px">_("News Pages")</a></div>""") % (str(url), icon)
        url = urlHandlers.UHAdminSwitchDebugActive.getURL()
        if minfo.isDebugActive():
            icon = iconEnabled
        else:
            icon = iconDisabled
        vars["features"] += _("""<div style="margin-bottom: 5px"><a href="%s"><img src="%s" border="0" style="float:left; padding-right: 5px">_("Debug")</a></div>""") % (str(url), icon)
        return vars


class WAdminFrame(wcomponents.WTemplated):

    def __init__( self ):
        pass

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["imgGestionGrey"] = Config.getInstance().getSystemIconURL( "gestionGrey" )
        vars["titleTabPixels"] = self.getTitleTabPixels()
        vars["intermediateVTabPixels"] = self.getIntermediateVTabPixels()
        return vars

    def getIntermediateVTabPixels( self ):
        return 0

    def getTitleTabPixels( self ):
        return 260

class WPAdmins( WPAdminsBase ):

    def _setActiveSideMenuItem(self):
        self._generalSettingsMenuItem.setActive()

    def _getPageContent( self, params ):
        wc = WAdmins()
        pars = { "GeneralInfoModifURL": urlHandlers.UHGeneralInfoModification.getURL(), \
                "addAdminsURL": urlHandlers.UHAdminsSelectUsers.getURL(), \
                "removeAdminsURL": urlHandlers.UHAdminsRemoveUsers.getURL() }
        return wc.getHTML( pars )

class WPAdminSelectUsers( WPAdmins ):

    def _getPageContent( self, params ):
        wc = wcomponents.WPrincipalSelection( urlHandlers.UHAdminsSelectUsers.getURL(), forceWithoutExtAuth=False )
        wc.setTitle( _("Select administrator"))
        params["addURL"] =  urlHandlers.UHAdminsAddUsers.getURL()
        html = _("""<table align="center" width="95%%">
    <tr>
       <td class="formTitle"> _("General admin data")</td>
    </tr>
    <tr>
        <td>
            <br>
        """)
        html = "%s%s"%(html,wc.getHTML( params ))
        return "%s%s"%(html,"""</td></tr></table>""")

class WGeneralInfoModification(wcomponents.WTemplated):

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        genInfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        vars["title"] = genInfo.getTitle()
        vars["organisation"] = genInfo.getOrganisation()
        vars["supportEmail"] = genInfo.getSupportEmail()
        vars["publicSupportEmail"] = genInfo.getPublicSupportEmail()
        vars["city"] = genInfo.getCity()
        vars["country"] = genInfo.getCountry()
        vars["noReplyEmail"] = genInfo.getNoReplyEmail()
        try:
            selected_tz = genInfo.getTimezone()
        except:
            selected_tz = 'UTC'
        vars["timezone"]=TimezoneRegistry.getShortSelectItemsHTML(selected_tz)
        vars["language"]= genInfo.getLang()
        return vars


class WPAdminLocalDefinitions( WPAdminsBase ):

    def __init__(self, rh):
        WPAdminsBase.__init__(self, rh)

    def __getAvailableTemplates(self):
        tplDir = Config.getInstance().getTPLDir()

        tplRE = re.compile('^([^\.]+)\.([^\.]+)\.tpl$')

        templates = {}

        fnames = os.listdir(tplDir);
        for fname in fnames:
            m = tplRE.match(fname)
            if m:
                templates[m.group(2)] = None

        tplRE = re.compile('^([^\.]+)\.([^\.]+)\.wohl$')

        fnames = os.listdir(os.path.join(tplDir,'chelp'));
        for fname in fnames:
            m = tplRE.match(fname)
            if m:
                templates[m.group(2)] = None

        return templates.keys()

    def _getPageContent( self, params ):
        wc = WAdminLocalDefinitions()
        pars = {    "defaultTemplateSet": info.HelperMaKaCInfo.getMaKaCInfoInstance().getDefaultTemplateSet(),
                    "availableTemplates": self.__getAvailableTemplates(),
                    "formURL": urlHandlers.UHAdminSaveTemplateSet.getURL() }
        return wc.getHTML( pars )

    def _setActiveSideMenuItem( self ):
        self._localdefMenuItem.setActive()

class WAdminLocalDefinitions(wcomponents.WTemplated):

    pass



class WPGenInfoModification( WPAdmins ):

    def _getPageContent( self, params ):
        wc = WGeneralInfoModification()
        pars = { "postURL": urlHandlers.UHGeneralInfoPerformModification.getURL() }
        return wc.getHTML( pars )

class WPHomepageCommon( WPAdminsBase ):
    def _setActiveSideMenuItem(self):
        self._homepageMenuItem.setActive()

    def _createTabCtrl( self ):
        self._tabCtrl = wcomponents.TabControl()

        self._subTabNews = self._tabCtrl.newTab( "news", _("News"), \
                urlHandlers.UHUpdateNews.getURL() )
        self._subTabAnnouncements = self._tabCtrl.newTab( "announcements", _("Announcements"), \
                urlHandlers.UHAnnouncement.getURL() )
        self._subTabUpcoming = self._tabCtrl.newTab( "upcoming", _("Upcoming Events"), \
                urlHandlers.UHConfigUpcomingEvents.getURL() )

    def _getPageContent(self, params):
        return wcomponents.WTabControl( self._tabCtrl, self._getAW() ).getHTML( self._getTabContent( params ) )

class WPUpdateNews( WPHomepageCommon ):

    def _setActiveTab( self ):
        self._subTabNews.setActive()

    def _getTabContent( self, params ):
        tz = timezone(timezoneUtils.DisplayTZ(self._getAW()).getDisplayTZ())
        wc = WUpdateNews()
        newsModule = ModulesHolder().getById("news")

        newslist = DictPickler.pickle(newsModule.getNewsItemsList(), tz)
        newsTypesList = newsModule.getNewsTypesAsDict()
        recentDays = newsModule.getRecentDays()

        pars = {"newslist": newslist,
                "newsTypesList": newsTypesList,
                "recentDays": recentDays }

        return wc.getHTML( pars )

class WUpdateNews(wcomponents.WTemplated):

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["baseURL"] = Config.getInstance().getBaseURL()
        vars["postURL"] = urlHandlers.UHUpdateNews.getURL()
        return vars

class WPConfigUpcomingEvents( WPHomepageCommon ):

    def _setActiveTab( self ):
        self._subTabUpcoming.setActive()

    def _getTabContent( self, params ):
        wc = WConfigUpcomingEvents()
        pars = {}
        return wc.getHTML( pars )

class WConfigUpcomingEvents(wcomponents.WTemplated):

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        return vars


class WPAnnouncementModif( WPHomepageCommon ):

    def _setActiveTab( self ):
        self._subTabAnnouncements.setActive()

    def _getTabContent( self, params ):
        wc = WAnnouncementModif()
        pars = {"saveURL": urlHandlers.UHAnnouncementSave.getURL() }
        return wc.getHTML( pars )

class WAnnouncementModif(wcomponents.WTemplated):

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        an = getAnnoucementMgrInstance()
        vars["announcement"] = escape(an.getText()).replace("\"", "&#34;")
        return vars


class WPAdminPlugins( WPAdminsBase ):

    _userData = ['favorite-user-list', 'favorite-user-ids']

    def __init__(self, rh, pluginTypeId, initialPlugin):
        WPAdminsBase.__init__(self, rh)
        self._pluginTypeId = pluginTypeId
        self._initialPlugin = initialPlugin
        self._user = rh._getUser()
        self._tabs = {}

    def _createTabCtrl(self):
        self._tabCtrl = wcomponents.TabControl()

        self._tabs["Main"] = self._tabCtrl.newTab("Main", _("Main"), urlHandlers.UHAdminPlugins.getURL())

        pluginTypes = PluginsHolder().getPluginTypes(doSort = True)
        for pluginType in pluginTypes:
            if pluginType.isVisible() and pluginType.isActive():
                self._tabs[pluginType.getId()] = self._tabCtrl.newTab(pluginType.getName(), pluginType.getName(),
                                                                       urlHandlers.UHAdminPlugins.getURL( pluginType ))

    def _setActiveSideMenuItem(self):
        self._pluginsMenuItem.setActive()

    def _setActiveTab(self):
        if self._pluginTypeId is None:
            self._tabs["Main"].setActive()
        else:
            self._tabs[self._pluginTypeId].setActive()


    def _getPageContent(self, params):
        if self._pluginTypeId is None:
            html = WAdminPluginsMainTab().getHTML(params)
        else:
            html = WAdminPlugins(self._pluginTypeId, self._initialPlugin, self._user).getHTML( params )

        return wcomponents.WTabControl( self._tabCtrl, self._getAW() ).getHTML( html )

class WAdminPlugins (wcomponents.WTemplated):

    def __init__(self, pluginType, initialPlugin, user):
        self._pluginType = pluginType
        self._initialPlugin = initialPlugin
        self._user = user

    def getVars (self):
        vars = wcomponents.WTemplated.getVars( self )

        vars["PluginType"] = PluginsHolder().getPluginType(self._pluginType)
        vars["InitialPlugin"] = self._initialPlugin
        vars["Favorites"] = DictPickler.pickle(self._user.getPersonalInfo().getBasket().getUsers())

        return vars

class WAdminPluginsMainTab(wcomponents.WTemplated):

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )

        vars["PluginsHolder"] = PluginsHolder()

        return vars

class WPAdminPluginsActionResult(WPAdminPlugins):

    def __init__(self, rh, pluginTypeId, initialPlugin, actionName, actionResult):
        WPAdminPlugins.__init__(self, rh, pluginTypeId, initialPlugin)
        self._actionName = actionName
        self._actionResult = actionResult

    def _getPageContent(self, params):
        html = WAdminPluginsActionResult(self._pluginTypeId, self._initialPlugin, self._actionName, self._actionResult).getHTML(params)
        return wcomponents.WTabControl( self._tabCtrl, self._getAW() ).getHTML( html )

class WAdminPluginsActionResult(wcomponents.WTemplated):

    def __init__(self, pluginType, initialPlugin, actionName, actionResult):
        self._pluginType = pluginType
        self._initialPlugin = initialPlugin
        self._actionName = actionName
        self._actionResult = actionResult

    def getVars(self):
        variables = wcomponents.WTemplated.getVars( self )

        variables["PluginType"] = PluginsHolder().getPluginType(self._pluginType)
        variables["InitialPlugin"] = self._initialPlugin
        variables["ActionName"] = self._actionName
        variables["ActionResult"] = self._actionResult

        return variables

class WPServicesCommon( WPAdminsBase ):

    def _setActiveSideMenuItem(self):
        self._servicesMenuItem.setActive()

    def _createTabCtrl( self ):
        self._tabCtrl = wcomponents.TabControl()

        self._subTabWebcast = self._tabCtrl.newTab( "webcast", _("Webcast"), \
                urlHandlers.UHWebcast.getURL() )
        self._subTabWebcast_Live = self._subTabWebcast.newSubTab( "live", _("Live"), \
                urlHandlers.UHWebcast.getURL() )
        self._subTabWebcast_Archive = self._subTabWebcast.newSubTab( "archive", _("Archive"), \
                urlHandlers.UHWebcastArchive.getURL() )
        self._subTabWebcast_Setup = self._subTabWebcast.newSubTab( "setup", _("Setup"), \
                urlHandlers.UHWebcastSetup.getURL() )
        self._subTabRecording = self._tabCtrl.newTab( "recording", _("Recording"), \
                urlHandlers.UHRecording.getURL() )
        self._subTabOAIPrivateConfig = self._tabCtrl.newTab( "oai-private", _("OAI Private Gateway"), \
                urlHandlers.UHOAIPrivateConfig.getURL() )

    def _getPageContent(self, params):
        return wcomponents.WTabControl( self._tabCtrl, self._getAW() ).getHTML( self._getTabContent( params ) )

class WPRecording( WPServicesCommon ):

    pageURL = "adminServices.py/recording"

    def __init__(self, rh):
        WPServicesCommon.__init__(self, rh)

    def _getTabContent( self, params ):
        return "under construction"
        #wp = WRecording()
        #return wp.getHTML(params)

    def _setActiveTab( self ):
        self._subTabRecording.setActive()

class WPWebcast( WPServicesCommon ):

    pageURL = "adminServices.py/webcast"

    def __init__(self, rh):
        WPServicesCommon.__init__(self, rh)

    def _getTabContent( self, params ):
        wp = WWebcast()
        return wp.getHTML(params)

    def _setActiveTab( self ):
        self._subTabWebcast.setActive()


class WWebcast( wcomponents.WTemplated ):

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        wm = webcast.HelperWebcastManager.getWebcastManagerInstance()
        channels = wm.getChannels()
        iconremove = Config.getInstance().getSystemIconURL( "remove" )
        iconarchive = Config.getInstance().getSystemIconURL( "archive" )
        iconadd = Config.getInstance().getSystemIconURL( "add" )
        list_onair = ""
        for ch in channels:
            name = ch.getName()
            urlchannel = ch.getURL()
            onair = ch.whatsOnAir()
            isonair = ch.isOnAir()
            color = "#edaaa8"
            iconswitch = iconadd
            urlswitch = urlHandlers.UHWebcastSwitchChannel.getURL()
            urlswitch.addParam("chname",name)
            form = ""
            if isonair:
                color = "#b7eda8"
                iconswitch = iconremove
            if onair:
                try:
                    title = onair.getTitle()
                    id = onair.getId()
                    if onair.getEvent():
                        eventurl = urlHandlers.UHConferenceDisplay.getURL(onair.getEvent())
                        title = """<a href="%s">%s</a>""" % (eventurl, title)
                except:
                    title = "Unrecognised event"
                    id = ""
                urlremovefromair = urlHandlers.UHWebcastRemoveFromAir.getURL()
                urlremovefromair.addParam("chname",name)
                form = """%s<a href="%s"><img src="%s" border="0"></a>""" % (title, urlremovefromair, iconremove)
            list_onair += """<TR bgcolor="%s"><TD><a href="%s">%s</a></TD><TD>%s</TD><TD><a href="%s"><IMG SRC="%s" border="0"></A></TD></TR>""" % (color, urlchannel, name, form, urlswitch, iconswitch)
        vars["onair"] = list_onair
        list_webcasts = ""
        webcasts = wm.getForthcomingWebcasts()
        webcasts.sort(webcast.sortWebcastByDate)
        urladdonair = urlHandlers.UHWebcastAddOnAir.getURL()
        channeloptions = ""
        for ch in wm.getChannels():
            channeloptions += "<option>%s" % ch.getName()
        for wc in webcasts:
            onair = wc in wm.whatsOnAir()
            if not onair:
                list_webcasts += """<form action="%s">""" % urladdonair
            title = wc.getTitle()
            if wc.getEvent():
                eventurl = urlHandlers.UHConferenceDisplay.getURL(wc.getEvent())
                title = """<a href="%s">%s</a>""" % (eventurl, title)
            list_webcasts += "<TD>%s - %s</TD><TD>"% (wc.getStartDate().strftime("%Y-%m-%d %H:%M"),title)
            if not onair:
                urlarchivewebcast = urlHandlers.UHWebcastArchiveWebcast.getURL()
                urlarchivewebcast.addParam("webcastid",wc.getId())
                urlremovewebcast = urlHandlers.UHWebcastRemoveWebcast.getURL()
                urlremovewebcast.addParam("webcastid",wc.getId())
                list_webcasts += """<SELECT name="chname" onchange="this.form.submit();"><option>not on air%s</SELECT>""" % channeloptions
                list_webcasts += """<input type="hidden" name="eventid" value="%s"></td><td><a href="%s"><img src="%s" border="0" alt="archive webcast"></a></td><td><a href="%s"><img src="%s" border="0" alt="delete webcast"></a>""" % (wc.getId(),urlarchivewebcast,iconarchive,urlremovewebcast,iconremove)
            list_webcasts += "</TD></TR>"
            if not onair:
                list_webcasts += "</FORM>"
        vars["addwebcastURL"] = urlHandlers.UHWebcastAddWebcast.getURL()
        vars["webcasts"] = list_webcasts
        return vars


class WPWebcastArchive( WPServicesCommon ):

    pageURL = "adminServices.py/webcastArchive"

    def __init__(self, rh):
        WPServicesCommon.__init__(self, rh)

    def _getTabContent( self, params ):
        wp = WWebcastArchive()
        return wp.getHTML(params)

    def _setActiveTab( self ):
        self._subTabWebcast_Archive.setActive()


class WWebcastArchive( wcomponents.WTemplated ):

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        iconunarchive = Config.getInstance().getSystemIconURL( "unarchive" )
        iconremove = Config.getInstance().getSystemIconURL( "remove" )
        wm = webcast.HelperWebcastManager.getWebcastManagerInstance()
        list_webcasts = ""
        webcasts = wm.getArchivedWebcasts()
        webcasts.sort(webcast.sortWebcastByDate)
        for wc in webcasts:
            title = wc.getTitle()
            if wc.getEvent():
                eventurl = urlHandlers.UHConferenceDisplay.getURL(wc.getEvent())
                title = """<a href="%s">%s</a>""" % (eventurl, title)
            list_webcasts += "<TD>%s - %s</TD><TD>"% (wc.getStartDate().strftime("%Y-%m-%d %H:%M"),title)
            urlunarchivewebcast = urlHandlers.UHWebcastUnArchiveWebcast.getURL()
            urlunarchivewebcast.addParam("webcastid",wc.getId())

            urlremovewebcast = urlHandlers.UHWebcastRemoveWebcast.getURL()
            urlremovewebcast.addParam("webcastid",wc.getId())
            list_webcasts += """<a href="%s"><img src="%s" border="0" alt="unarchive webcast"></a></td><td><a href="%s"><img src="%s" border="0" alt="delete webcast"></a>""" % (urlunarchivewebcast,iconunarchive,urlremovewebcast,iconremove)
            list_webcasts += "</TD></TR>"
        vars["webcasts"] = list_webcasts
        return vars


class WPWebcastSetup( WPServicesCommon ):

    pageURL = "adminServices.py/webcastSetup"

    def __init__(self, rh):
        WPServicesCommon.__init__(self, rh)

    def _getTabContent( self, params ):
        wp = WWebcastSetup()
        return wp.getHTML(params)

    def _setActiveTab( self ):
        self._subTabWebcast_Setup.setActive()


class WWebcastSetup( wcomponents.WTemplated ):

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        wm = webcast.HelperWebcastManager.getWebcastManagerInstance()
        managers = wm.getManagers()
        urlselectmanager = urlHandlers.UHWebcastSelectManager.getURL()
        urlremovemanager = urlHandlers.UHWebcastRemoveManager.getURL()
        vars["adminList"] = wcomponents.WPrincipalTable().getHTML( managers,  None, urlselectmanager, urlremovemanager, selectable=False )
        channels = wm.getChannels()
        iconremove = Config.getInstance().getSystemIconURL( "remove" )
        iconadd = Config.getInstance().getSystemIconURL( "add" )
        iconup = Config.getInstance().getSystemIconURL( "upArrow" )
        icondown = Config.getInstance().getSystemIconURL( "downArrow" )
        list_channels = """<table width="100%" cellspacing=0>"""
        i = 0
        for channel in channels:
            i += 1
            if int(i/2)*2 == i:
                color = "#e5e5e5"
            else:
                color = "#eeeeee"
            screenname = "%s (%sx%s)" % (channel.getName(),channel.getWidth(), channel.getHeight())
            name = channel.getName()
            churl = channel.getURL()
            width = channel.getWidth()
            height = channel.getHeight()
            urlremove = urlHandlers.UHWebcastRemoveChannel.getURL()
            urlremove.addParam("chname",name)
            urlmoveup = urlHandlers.UHWebcastMoveChannelUp.getURL()
            urlmoveup.addParam("chnb",i-1)
            urlmovedown = urlHandlers.UHWebcastMoveChannelDown.getURL()
            urlmovedown.addParam("chnb",i-1)
            list_channels += """<tr bgcolor=%s><td valign=top><ul><li><a href="%s">%s</a><a href="%s"><img src="%s" border="0"></a><a href="%s"><img src="%s" border="0"></a><a href="%s"><img src="%s" border="0"></a></li>""" % (color,churl,screenname,urlremove,iconremove,urlmoveup,iconup,urlmovedown,icondown)
            list_channels += "<ul><li>Streams:</li><ul>"
            for stream in channel.getStreams():
                url = stream.getURL()
                format = stream.getFormat()
                urlremovestream = urlHandlers.UHWebcastRemoveStream.getURL()
                urlremovestream.addParam("chname",name)
                urlremovestream.addParam("stformat",format)
                list_channels += """<li><a href="%s">%s</a><a href="%s"><img src="%s" border="0"></a></li>""" % ( url, format, urlremovestream, iconremove )
            urladdstream = urlHandlers.UHWebcastAddStream.getURL()
            urladdstream.addParam("chname",name)
            urlmodifychannel = urlHandlers.UHWebcastModifyChannel.getURL()
            urlmodifychannel.addParam("chname",name)
            list_channels += """<li>
  <table bgcolor="#bbbbbb">
    <form action="%s" method="POST">
  <tr><td>format:</td><td><input name="stformat" size=5>
  </td><td>url:</td><td><input name="sturl" size="20">
  </td><td>
  <input type="image" src="%s" name="submit" value="add stream" alt="add stream">
  </td></tr>
    </form>
  </table></li></ul></ul></ul>
    </td><td align=right>
  <form action="%s" method="POST">
  <table bgcolor="#bbbbbb">
  <tr bgcolor="#999999"><td colspan=2><font color=white>Update Channel</font>
  </td></tr><tr><td>
  name:</td><td><input name="chnewname" value="%s" size=15>
  </td></tr><tr><td>
  url:</td><td><input name="churl" value="%s" size=30>
  </td></tr><tr><td>
  width:</td><td><input name="chwidth" value="%s" size=3>
  </td></tr><tr><td>
  height:</td><td><input name="chheight" value="%s" size=3>
  </td></tr><tr><td colspan=2>
  <input type="submit" name="submit" value="modify channel">
  </td></tr>
  </table>
  </form>
  </td></tr>""" % (urladdstream,iconadd,urlmodifychannel,name,churl,width,height)
        list_channels += "</table>"
        vars["channels"] = list_channels
        vars["postURL"] = urlHandlers.UHWebcastAddChannel.getURL()

        vars["saveWebcastServiceURL"] = urlHandlers.UHWebcastSaveWebcastServiceURL.getURL()
        vars["webcastServiceURL"] = wm.getWebcastServiceURL()

        vars["saveWebcastSynchronizationURL"] = urlHandlers.UHWebcastSaveWebcastSynchronizationURL.getURL()
        vars["webcastSynchronizationURL"] = wm.getWebcastSynchronizationURL()

        vars["webcastManualSynchronize"] = urlHandlers.UHWebcastManualSynchronization.getURL()

        return vars

class WPWebcastSelectManager( WPWebcastSetup ):

    def _getTabContent( self, params ):
        wc = wcomponents.WUserSelection( urlHandlers.UHWebcastSelectManager.getURL(), forceWithoutExtAuth=True )
        wc.setTitle("Select webcast administrator")
        params["addURL"] =  urlHandlers.UHWebcastAddManager.getURL()
        return wc.getHTML( params )


class WPTemplatesCommon( WPAdminsBase ):

    def getJSFiles(self):
        return [ 'js/prototype/prototype.js',
                 'js/scriptaculous/scriptaculous.js' ] + \
                WPAdminsBase.getJSFiles(self)

    def _setActiveSideMenuItem(self):
        self._templatesMenuItem.setActive()

    def _createTabCtrl( self ):
        self._tabCtrl = wcomponents.TabControl()

        self._subTabBadges = self._tabCtrl.newTab( "badges", _("Badges"), \
                urlHandlers.UHBadgeTemplates.getURL() )
        self._subTabPosters = self._tabCtrl.newTab( "posters", _("Posters"), \
                urlHandlers.UHPosterTemplates.getURL() )
        self._subTabStyles = self._tabCtrl.newTab( "styles", _("Timetable Styles"), \
                urlHandlers.UHAdminsStyles.getURL() )
        self._subTabCSSTpls = self._tabCtrl.newTab( "styles", _("Conference Styles"), \
                urlHandlers.UHAdminsConferenceStyles.getURL() )

    def _getPageContent(self, params):
        return wcomponents.WTabControl( self._tabCtrl, self._getAW() ).getHTML( self._getTabContent( params ) )
        if self._showAdmin:
            return WPAdminsBase._getBody( self, params )
        else:
            return self._getTabContent( params )

class WPAdminsConferenceStyles( WPTemplatesCommon ):

    def _getTabContent( self, params ):
        wp = WAdminsConferenceStyles()
        return wp.getHTML(params)

    def _setActiveTab( self ):
        self._subTabCSSTpls.setActive()

class WAdminsConferenceStyles(wcomponents.WTemplated):

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["contextHelpText"] = _("This is the list of templates that an organizer can use to customize a conference")
        #from MaKaC.modules.base import ModulesHolder
        cssTplsModule=ModulesHolder().getById("cssTpls")
        vars["cssTplsModule"] = cssTplsModule
        return vars


class WPAdminsStyles( WPTemplatesCommon ):

    def _getTabContent( self, params ):
        wp = WAdminsStyles()
        return wp.getHTML(params)

    def _setActiveTab( self ):
        self._subTabStyles.setActive()

class WAdminsStyles(wcomponents.WTemplated):

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        styleMgr = info.HelperMaKaCInfo.getMaKaCInfoInstance().getStyleManager()
        vars["styleMgr"] = styleMgr
        baseXSLPath = styleMgr.getBaseXSLPath()
        baseCSSPath = styleMgr.getBaseCSSPath()
        vars["contextHelpText"] = _("""- <b>_("XSL files")</b> _("are mandatory and located in"):<br/>%s<br/>- <b>_("CSS files")</b> _("are optional and located in"):<br/>%s<br/>- <b>_("Lines in red")</b> _("indicate a missing .xsl file (these styles will not be presented to the users"))<br/>- <b>_("XSL and CSS files")</b> _("should be named after the ID of the style (+extension: .xsl or .css)")""") % (baseXSLPath,baseCSSPath)
        vars["deleteIconURL"] = Config.getInstance().getSystemIconURL("remove")
        return vars

class WPAdminsAddStyle( WPAdminsStyles ):

    def _getTabContent( self, params ):
        wp = WAdminsAddStyle()
        return wp.getHTML(params)

class WAdminsAddStyle(wcomponents.WTemplated):

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        styleMgr = info.HelperMaKaCInfo.getMaKaCInfoInstance().getStyleManager()
        vars["styleMgr"] = styleMgr
        availableStylesheets = []
        XSLBasePath = styleMgr.getBaseXSLPath()
        if os.path.exists(XSLBasePath):
            for file in os.listdir(XSLBasePath):
                if os.path.isfile(os.path.join(XSLBasePath,file)) and ".xsl" in file:
                    filename = file.replace(".xsl","")
                    if filename not in styleMgr.getStylesheets().keys():
                        availableStylesheets.append(filename)
        vars["availableStylesheets"] = availableStylesheets
        vars["contextHelpText"] = "Lists all XSL files in %s which are not already used in a declared style" % XSLBasePath
        return vars

class WAdminTemplates(wcomponents.WTemplated):

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        return vars

class WPBadgeTemplates( WPTemplatesCommon ):
    pageURL = "badgeTemplates.py"

    def __init__(self, rh):
        WPTemplatesCommon.__init__(self, rh)

    def _getTabContent( self, params ):
        wp = WBadgeTemplates(conference.CategoryManager().getDefaultConference())
        return wp.getHTML(params)

    def _setActiveTab( self ):
        self._subTabBadges.setActive()

class WPPosterTemplates( WPTemplatesCommon ):
    pageURL = "posterTemplates.py"

    def __init__(self, rh):
        WPTemplatesCommon.__init__(self, rh)

    def _getTabContent( self, params ):
        wp = WPosterTemplates(conference.CategoryManager().getDefaultConference())
        return wp.getHTML(params)

    def _setActiveTab( self ):
        self._subTabPosters.setActive()

class WPBadgeTemplateDesign( WPTemplatesCommon ):

    def __init__(self, rh, conf, templateId = None, new = False):
        WPTemplatesCommon.__init__(self, rh)
        self._conf = conf
        self.__templateId = templateId
        self.__new = new

    def _setActiveTab( self ):
        self._subTabBadges.setActive()

    def _getTabContent( self, params ):
        wc = conferences.WConfModifBadgeDesign( self._conf, self.__templateId, self.__new )
        return wc.getHTML()

class WPPosterTemplateDesign( WPTemplatesCommon ):

    def __init__(self, rh, conf, templateId = None, new = False):
        WPTemplatesCommon.__init__(self, rh)
        self._conf = conf
        self.__templateId = templateId
        self.__new = new

    def _setActiveTab( self ):
        self._subTabPosters.setActive()

    def _getTabContent( self, params ):
        wc = conferences.WConfModifPosterDesign( self._conf, self.__templateId, self.__new )
        return wc.getHTML()

class WBadgeTemplates( wcomponents.WTemplated ):

    def __init__( self, conference, user=None ):
        self.__conf = conference
        self._user=user

    def getVars( self ):

        dconf = self.__conf

        vars = wcomponents.WTemplated.getVars( self )
        vars["NewDefaultTemplateURL"] = str(urlHandlers.UHModifDefTemplateBadge.getURL(dconf,
                                                                             dconf.getBadgeTemplateManager().getNewTemplateId(), new = True))

        templateListHTML = []
        first = True


        sortedTemplates = dconf.getBadgeTemplateManager().getTemplates().items()
        sortedTemplates.sort(lambda item1, item2: cmp(item1[1].getName(), item2[1].getName()))
        for templateId, template in sortedTemplates:
            templateListHTML.append("""              <tr>""")
            templateListHTML.append("""                <td>""")

            radio = []
            radio.append("""                  <input type="radio" name="templateId" value='""")
            radio.append(str(templateId))
            radio.append("""' id='""")
            radio.append(str(templateId))
            radio.append("""'""")
            if first:
                first = False
                radio.append( _(""" CHECKED """))
            radio.append(""">""")
            templateListHTML.append("".join(radio))
            templateListHTML.append("".join (["""                  """,
                                              """<label for='""",
                                              str(templateId),
                                              """'>""",
                                              template.getName(),
                                              """</label>""",
                                              """&nbsp;&nbsp;&nbsp;"""]))

            edit = []
            edit.append("""                  <a href='""")
            edit.append(str(urlHandlers.UHConfModifBadgeDesign.getURL(dconf, templateId)))
            edit.append("""'><img src='""")
            edit.append(str(Config.getInstance().getSystemIconURL("file_edit")))
            edit.append("""' border='0'></a>&nbsp;""")
            templateListHTML.append("".join(edit))

            delete = []
            delete.append("""                  <a href='""")
            delete.append(str(urlHandlers.UHConfModifBadgePrinting.getURL(dconf, deleteTemplateId=templateId)))
            delete.append("""'><img src='""")
            delete.append(str(Config.getInstance().getSystemIconURL("smallDelete")))
            delete.append("""' border='0'></a>&nbsp;""")
            templateListHTML.append("".join(delete))

            templateListHTML.append("""                </td>""")
            templateListHTML.append("""              </tr>""")

        vars["templateList"] = "\n".join(templateListHTML)

        vars['PDFOptions'] = WConfModifBadgePDFOptions(dconf, showKeepValues = False, showTip = False).getHTML()

        return vars

class WPosterTemplates( wcomponents.WTemplated ):

    def __init__( self, conference, user=None ):
        self.__conf = conference
        self._user=user

    def getVars( self ):

        dconf = self.__conf

        vars = wcomponents.WTemplated.getVars( self )
        vars["NewDefaultTemplateURL"] = str(urlHandlers.UHModifDefTemplatePoster.getURL(dconf,
                                                                             dconf.getPosterTemplateManager().getNewTemplateId(), new = True))

        templateListHTML = []
        first = True


        sortedTemplates = dconf.getPosterTemplateManager().getTemplates().items()
        sortedTemplates.sort(lambda item1, item2: cmp(item1[1].getName(), item2[1].getName()))
        for templateId, template in sortedTemplates:
            templateListHTML.append("""              <tr>""")
            templateListHTML.append("""                <td>""")

            radio = []
            radio.append("""                  <input type="radio" name="templateId" value='""")
            radio.append(str(templateId))
            radio.append("""' id='""")
            radio.append(str(templateId))
            radio.append("""'""")
            if first:
                first = False
                radio.append( _(""" CHECKED """))
            radio.append(""">""")
            templateListHTML.append("".join(radio))
            templateListHTML.append("".join (["""                  """,
                                              """<label for='""",
                                              str(templateId),
                                              """'>""",
                                              template.getName(),
                                              """</label>""",
                                              """&nbsp;&nbsp;&nbsp;"""]))

            edit = []
            edit.append("""                  <a href='""")
            edit.append(str(urlHandlers.UHConfModifPosterDesign.getURL(dconf, templateId)))
            edit.append("""'><img src='""")
            edit.append(str(Config.getInstance().getSystemIconURL("file_edit")))
            edit.append("""' border='0'></a>&nbsp;""")
            templateListHTML.append("".join(edit))

            delete = []
            delete.append("""                  <a href='""")
            delete.append(str(urlHandlers.UHConfModifPosterPrinting.getURL(dconf, deleteTemplateId=templateId)))
            delete.append("""'><img src='""")
            delete.append(str(Config.getInstance().getSystemIconURL("smallDelete")))
            delete.append("""' border='0'></a>&nbsp;""")
            clone = []
            clone.append("""                  <a href='""")
            clone.append(str(urlHandlers.UHConfModifPosterPrinting.getURL(dconf, copyTemplateId=templateId)))
            clone.append("""'><img src='""")
            clone.append(str(Config.getInstance().getSystemIconURL("smallCopy")))
            clone.append("""' border='0'></a>&nbsp;""")
            templateListHTML.append("".join(delete))
            templateListHTML.append("".join(clone))

            templateListHTML.append("""                </td>""")
            templateListHTML.append("""              </tr>""")

        vars["templateList"] = "\n".join(templateListHTML)

        return vars


class WPUsersAndGroupsCommon(WPAdminsBase):

    def _setActiveSideMenuItem(self):
        self._usersAndGroupsMenuItem.setActive()

    def _createTabCtrl( self ):
        self._tabCtrl = wcomponents.TabControl()

        self._subTabMain = self._tabCtrl.newTab( "main", _("Main"), \
                urlHandlers.UHUserManagement.getURL() )
        self._subTabUsers = self._tabCtrl.newTab( "users", _("Manage Users"), \
                urlHandlers.UHUsers.getURL() )
        self._subTabGroups = self._tabCtrl.newTab( "groups", _("Manage Groups"), \
                urlHandlers.UHGroups.getURL() )

    def _getPageContent(self, params):

        #if self._showAdmin:
        #    html = WPAdminsBase._getBody( self, params )
        #else:
        #    html = wcomponents.WTabControl( self._tabCtrl, self._getAW() ).getHTML( self._getTabContent( params ) )

        return wcomponents.WTabControl( self._tabCtrl, self._getAW() ).getHTML( self._getTabContent( params ) )

    #def _getBody(self, params):
    #    if self._showAdmin:
    #        return WPAdminsBase._getBody( self, params )
    #    else:
    #        return self._getTabContent( params )

class WUserManagement( wcomponents.WTemplated ):

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        iconDisabled = str(Config.getInstance().getSystemIconURL( "disabledSection" ))
        iconEnabled = str(Config.getInstance().getSystemIconURL( "enabledSection" ))
        vars["accountCreationData"] = ""
        url = urlHandlers.UHUserManagementSwitchAuthorisedAccountCreation.getURL()
        if minfo.getAuthorisedAccountCreation():
            icon = iconEnabled
        else:
            icon = iconDisabled
        vars["accountCreationData"] += _("""<a href="%s"><img src="%s" border="0"> _("Public Account Creation")</a>""") % (str(url), icon)
        url = urlHandlers.UHUserManagementSwitchNotifyAccountCreation.getURL()
        if minfo.getNotifyAccountCreation():
            icon = iconEnabled
        else:
            icon = iconDisabled
        vars["accountCreationData"] += _("""<br><a href="%s"><img src="%s" border="0"> _("Notify Account Creation by Email")</a>""") % (str(url), icon)
        url = urlHandlers.UHUserManagementSwitchModerateAccountCreation.getURL()
        if minfo.getModerateAccountCreation():
            icon = iconEnabled
        else:
            icon = iconDisabled
        vars["accountCreationData"] += _("""<br><a href="%s"><img src="%s" border="0"> _("Moderate Account Creation")</a>""") % (str(url), icon)
        vars["moderators"] = ""
        vars["moderatorsURL"] = ""
        return vars


class WPUserManagement( WPUsersAndGroupsCommon ):
    pageURL = "userManagement.py"

    def __init__(self, rh, params):
        WPUsersAndGroupsCommon.__init__(self, rh)
        self._params = params

    def _getTabContent( self, params ):
        wp = WUserManagement()
        return wp.getHTML(self._params)

    def _setActiveTab( self ):
        self._subTabMain.setActive()

class WPUserCommon( WPUsersAndGroupsCommon ):

    def _setActiveTab( self ):
        self._subTabUsers.setActive()

class WBrowseUsers( wcomponents.WTemplated ):

    def __init__( self, letter=None, browseIndex="surName" ):
        self._letter = letter
        self._browseIndex = browseIndex

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        nameIndex = indexes.IndexesHolder().getById(self._browseIndex)
        letters = nameIndex.getBrowseIndex()
        vars["browseIndex"] = """
        <span class="nav_border"><a class="nav_link" href='' onClick="document.browseForm.letter.value='clear';document.browseForm.submit();return false;">clear</a></span>"""
        if self._letter == "all":
            vars["browseIndex"] += """
        [all] """
        else:
            vars["browseIndex"] += """
        <span class="nav_border"><a class="nav_link" href='' onClick="document.browseForm.letter.value='all';document.browseForm.submit();return false;">all</a></span> """
        for letter in letters:
            if self._letter == letter:
                vars["browseIndex"] += """\n[%s] """ % letter
            else:
                vars["browseIndex"] += """\n<span class="nav_border"><a class="nav_link" href='' onClick="document.browseForm.letter.value='%s';document.browseForm.submit();return false;">%s</a></span> """ % (escape(letter,True),letter)
        vars["browseResult"] = ""
        if self._letter != None:
            ah = user.AvatarHolder()
            if self._letter != "all":
                res = ah.matchFirstLetter(self._browseIndex, self._letter, onlyActivated=False, forceWithoutExtAuth=False)
            else:
                res = ah.getValuesToList()
            if self._browseIndex == "surName" or self._browseIndex == "status":
                res.sort(utils.sortUsersByName)
            elif self._browseIndex == "name":
                res.sort(utils.sortUsersByFirstName)
            elif self._browseIndex == "organisation":
                res.sort(utils.sortUsersByAffiliation)
            elif self._browseIndex == "email":
                res.sort(utils.sortUsersByEmail)
            else:
                res.sort()
            vars["browseResult"] = WHTMLUserList(res).getHTML(vars)
        return vars

class WHTMLUserList(wcomponents.WTemplated):

    def __init__(self, userList):
        self._userList = userList

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        color="white"
        ul = []
        vars["userList"] = ""
        ul.append( _("""
                        <tr>
                            <td bgcolor="white" style="color:black" align="center"><b>%s  _("users")</b></td>
                        </tr>
                        """)%len(self._userList))
        for u in self._userList:
            if color=="white":
                color="#ececec"
            else:
                color="white"
            organisation = ""
            if u.getOrganisation() != "":
                organisation = " (%s)" % u.getOrganisation()
            email = ""
            if u.getEmail() != "":
                email = " (%s)" % u.getEmail()
            url = vars["userDetailsURLGen"]( u )
            name = u.getFullName()
            if name == "":
                name = "no name"
            ul.append("""<tr>
                            <td bgcolor="%s"><a href="%s">%s</a> %s %s</td>
                         </tr>"""%(color, url, self.htmlText(name) , self.htmlText(email),self.htmlText(organisation)) )
        if ul:
            vars["userList"] += "".join( ul )
        else:
            vars["userList"] += _("""<tr>
                            <td><br><span class="blacktext">&nbsp;&nbsp;&nbsp; _("No users returned")</span></td></tr>""")
        return vars

class WUserList(wcomponents.WTemplated):

    def __init__( self, criteria, onlyActivated=True ):
        self._criteria = criteria
        self._onlyActivated=onlyActivated

    def _performSearch( self, criteria ):
        ah = user.AvatarHolder()
        if  criteria["surName"] == "*" or \
            criteria["name"] =="*" or \
            criteria["email"] =="*" or \
            criteria["organisation"] =="*":
            res=ah.getValuesToList()
        else:
            res = ah.match(criteria, onlyActivated=self._onlyActivated, forceWithoutExtAuth=True)
        res.sort(utils.sortUsersByName)
        return res

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["nbUsers"] = indexes.IndexesHolder().getById("email").getLength()
        vars["createUserURL"] = urlHandlers.UHUserCreation.getURL()
        vars["mergeUsersURL"] = urlHandlers.UHUserMerge.getURL()
        vars["logMeAsURL"] = urlHandlers.UHLogMeAs.getURL()
        vars["searchUsersURL"] = urlHandlers.UHUsers.getURL()
        vars["browseUsersURL"] = urlHandlers.UHUsers.getURL()
        vars["browseOptions"] = ""
        options = { "surName": _("by last name"),
                    "name": _("by first name"),
                    "organisation": _("by affiliation"),
                    "email": _("by email address"),
                    "status": _("by status") }
        for key in options.keys():
            if key == vars.get("browseIndex","surName"):
                vars["browseOptions"] += """<option value="%s" selected> %s""" % (key, options[key])
            else:
                vars["browseOptions"] += """<option value="%s"> %s""" % (key, options[key])
        vars["browseUsers"] = WBrowseUsers(vars.get("letter",None),vars.get("browseIndex","surName")).getHTML(vars)
        vars["users"] = ""
        if self._criteria:
            userList = self._performSearch(self._criteria)
            vars["users"] = WHTMLUserList(userList).getHTML(vars)
        return vars


class WPUserList(WPUserCommon):
    pageURL = "userList.py"

    def __init__(self, rh, params):
        WPUserCommon.__init__(self, rh)
        self._params = params

    def _getTabContent( self, params ):
        criteria = {}
        if filter(lambda x: self._params[x], self._params):
            criteria["surName"] = self._params.get("sSurName","")
            criteria["name"] = self._params.get("sName","")
            criteria["email"] = self._params.get("sEmail","")
            criteria["organisation"] = self._params.get("sOrganisation","")
        comp = WUserList(criteria, onlyActivated=False)
        self._params["userDetailsURLGen"] = urlHandlers.UHUserDetails.getURL
        return comp.getHTML(self._params)


class WPUserCreation(WPUserCommon):

    def __init__(self, rh, params, participation=None):
        WPUserCommon.__init__(self, rh)
        self._params = params
        self._participation=participation

    def _getTabContent(self, params ):
        pars = self._params
        p = wcomponents.WUserRegistration()
        pars["defaultLang"] = pars.get("lang", "")
        pars["defaultTZ"] = pars.get("timezone", "")
        pars["defaultTZMode"] = pars.get("displayTZMode", "")
        pars["postURL"] =  urlHandlers.UHUserCreation.getURL()
        if pars["msg"] != "":
            pars["msg"] = "<table bgcolor=\"gray\"><tr><td bgcolor=\"white\">\n<font size=\"+1\" color=\"red\"><b>%s</b></font>\n</td></tr></table>"%pars["msg"]
        if self._participation is not None:
            pars["email"]=self._participation.getEmail()
            pars["name"]=self._participation.getFirstName()
            pars["surName"]=self._participation.getFamilyName()
            pars["title"]=self._participation.getTitle()
            pars["organisation"]=self._participation.getAffiliation()
            pars["address"]=self._participation.getAddress()
            pars["telephone"]=self._participation.getPhone()
            pars["fax"]=self._participation.getFax()
        return p.getHTML( pars )

class WPUserCreationNonAdmin(WPUserCreation):

    def _getNavigationDrawer(self):
        pass

    def _getBody(self, params):
        return WPUserCreation._getTabContent(self, params)

class WPUserCreated( WPUserCommon ):

    def __init__(self, rh, av):
        WPUserCommon.__init__(self, rh)
        self._av = av

    def _getTabContent(self, params ):
        p = wcomponents.WUserCreated(self._av)
        pars = {"signInURL" : urlHandlers.UHSignIn.getURL()}
        return p.getHTML( pars )

class WPUserCreatedNonAdmin(WPUserCreated):

    def _getNavigationDrawer(self):
        pass

    def _getBody(self, params):
        return WPUserCreated._getTabContent(self, params)


class WPUserExistWithIdentity( WPUserCommon ):

    def __init__(self, rh, av):
        WPUserCommon.__init__(self, rh)
        self._av = av

    def _getTabContent(self, params ):
        p = wcomponents.WUserSendIdentity(self._av)
        pars = {"postURL" : urlHandlers.UHSendLogin.getURL(self._av)}
        return p.getHTML( pars )

class WPUserExistWithIdentityNonAdmin(WPUserExistWithIdentity):

    def _getNavigationDrawer(self):
        pass

    def _getBody(self, params):
        return WPUserExistWithIdentity._getTabContent(self, params)


class WPUserBase(WPUserCommon):

    def __init__( self, rh, av=None ):
        WPUserCommon.__init__( self, rh )
        self._avatar = av


class WUserIdentitiesTable(wcomponents.WTemplated):

    def __init__( self, av ):
        self._avatar = av

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        il = []
        am = AuthenticatorMgr()
        authTagList = [i.getId() for i in am.getList()]
        for item in self._avatar.getIdentityList():
            if not item.getAuthenticatorTag() in authTagList:
                continue
            changePassword = ""
            if item.getAuthenticatorTag() != "Local" :
                changePassword = _("External account")
            else :
                changeURL = urlHandlers.UHUserIdentityChangePassword.getURL()
                changeURL.addParam("userId",self._avatar.getId())
                changeURL.addParam("identityId",item.getId())
                changePassword = _("""<a href="%s"><small> _("Change password")</small></a>""")%changeURL
            il.append("""
                        <tr>
                            <td width="60%%">
                                <input type="checkbox" name="selIdentities" value="%s"> %s
                            </td>
                            <td width="20%%">
                                <small>%s</small>
                            </td>
                            <td width="20%%">
                                %s
                            </td>
                        </tr>
                        """%(item.getId(), item.getLogin(), item.getAuthenticatorTag(), changePassword) )
        vars["items"] = "".join( il )
        vars["locator"] = self._avatar.getLocator().getWebForm()
        return vars


class WUserBaskets(wcomponents.WTemplated):

    def __init__(self, av):
        self._avatar = av

    def getHTML( self, params ):
        params['user'] = self._avatar;
        return wcomponents.WTemplated.getHTML( self, params )


class WUserPreferences(wcomponents.WTemplated):

    def __init__(self, av):
        self._avatar = av

    def getHTML( self, params ):
        params['user'] = self._avatar;
        return wcomponents.WTemplated.getHTML( self, params )

class WUserDetails(wcomponents.WTemplated):

    def __init__(self, av):
        self._avatar = av

    def getHTML( self, currentUser, params ):
        self._currentUser = currentUser
        return wcomponents.WTemplated.getHTML( self, params )

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        u = self._avatar
        vars["fullName"] = self.htmlText("%s, %s"%(u.getSurName().upper(), u.getName()))
        vars["organisation"] = self.htmlText(u.getOrganisations()[0])
        vars["title"] = self.htmlText(u.getTitle())
        vars["address"] = self.htmlText(u.getAddresses()[0])
        vars["email"] = self.getEmailsHTML(u)
        vars["lang"] = self.htmlText(u.getLang())
        vars["telephon"] = self.htmlText(u.getTelephones()[0])
        vars["fax"] = self.htmlText(u.getFaxes()[0])


        try:
            vars["timezone"] = self.htmlText(u.getTimezone())
        except:
            u.setTimezone("UTC")
            vars["timezone"] = self.htmlText(u.getTimezone())

        try:
            vars["displayTZMode"] = self.htmlText(u.getDisplayTZMode())
        except:
            u.setDisplayTZMode("MyTimezone")
            vars["displayTZMode"] = self.htmlText(u.getDisplayTZMode())


        vars["locator"] = self.htmlText(self._avatar.getLocator().getWebForm())
        vars["identities"] = ""
        vars["status"] = self._avatar.getStatus()
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        al = minfo.getAdminList()
        if self._currentUser == self._avatar or \
              self._currentUser in al.getList() or \
              len(self._avatar.getIdentityList())==0:
            vars["identities"] = WUserIdentitiesTable( self._avatar ).getHTML( { "addIdentityURL": vars["addIdentityURL"], "removeIdentityURL": vars["removeIdentityURL"] })
        vars["activeButton"] = ""
        if self._currentUser in al.getList() and not self._avatar.isActivated():
            vars["activeButton"] = _("""<form action="%s" method="POST"><td bgcolor="white" width="100%%"\
                    valign="top" align="left">&nbsp;&nbsp;&nbsp;<input type="submit" class="btn" \
                    value=" _("activate the account") "></td></form>""")%vars["activeURL"]
        vars["categoryManager"] = ""
        categs = u.getLinkTo("category","manager")
        for categ in categs:
            vars["categoryManager"] += """<a href="%s">%s</a><br>""" % (urlHandlers.UHCategoryDisplay.getURL(categ), categ.getTitle())
        vars["eventManager"] = ""
        events = u.getLinkTo("conference","manager")
        for event in events:
            vars["eventManager"] += """<a href="%s">%s</a><br>""" % (urlHandlers.UHConferenceDisplay.getURL(event), event.getTitle())
        return vars

    def getEmailsHTML(self, u):
        html = [self.htmlText(u.getEmails()[0])]
        if u.getSecondaryEmails():
            html.append(""" <font color="grey"><small>(""")
            html.append(", ".join(u.getSecondaryEmails()))
            html.append(")</small></font>")
        return "".join(html)

class WPPersonalArea(WPUserBase):

    def _getBody( self, params ):
        self._createTabCtrl()
        self._setActiveTab()
        html = wcomponents.WTabControl( self._tabCtrl, self._getAW() ).getHTML( self._getTabContent( params ) )
        frame = personalization.WPersAreaFrame()
        p = { "body": html,
              "userName": self._avatar.getStraightFullName() }
        return frame.getHTML( p )

    def _createTabCtrl( self ):
        self._tabCtrl = wcomponents.TabControl()
        self._tabDetails = self._tabCtrl.newTab( "details", _("Account Details"), \
                urlHandlers.UHUserDetails.getURL(self._avatar) )

        """
            This tab is not needed any more. Currently only has information about
            showing or hiding advacned tabs. These advanced tabs has been turned into
            a side menu. Maybe the tab is needed in the future.
        """
        #self._tabPreferences = self._tabCtrl.newTab( "preferences", _("Preferences"), \
        #        urlHandlers.UHUserPreferences.getURL() )

        self._tabBaskets = self._tabCtrl.newTab( "baskets", _("Favorites"), \
                urlHandlers.UHUserBaskets.getURL() )

    def _getNavigationDrawer(self):
        return wcomponents.WSimpleNavigationDrawer(_("User Details"))


class WPUserDetails( WPPersonalArea ):

    def _getTabContent( self, params ):
        c = WUserDetails( self._avatar )
        params["modifyUserURL"] = urlHandlers.UHUserModification.getURL( self._avatar )
        params["addIdentityURL"] = urlHandlers.UHUserIdentityCreation.getURL( self._avatar )
        params["removeIdentityURL"] = urlHandlers.UHUserRemoveIdentity.getURL( self._avatar )
        params["activeURL"] = urlHandlers.UHUserActive.getURL( self._avatar )
        return c.getHTML( self._getAW().getUser(), params )

    def _setActiveTab( self ):
        self._tabDetails.setActive()


class WPUserBaskets( WPPersonalArea ):

    def _getTabContent( self, params ):
        c = WUserBaskets( self._avatar )

        return c.getHTML( params )

    def _setActiveTab( self ):
        self._tabBaskets.setActive()


class WPUserPreferences( WPPersonalArea ):

    def _getTabContent( self, params ):
        c = WUserPreferences( self._avatar )
        return c.getHTML( params )

    def _setActiveTab( self ):
        self._tabPreferences.setActive()


class WUserModify(wcomponents.WTemplated):

    def __init__( self, avatar ):
        self._avatar = avatar

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        u = self._avatar
        t = vars.get("title", u.getTitle())
        vars["titles"] = TitlesRegistry().getSelectItemsHTML(t)
        vars["locator"] = u.getLocator().getWebForm()
        tz = u.getTimezone()
        vars["timezone"] = TimezoneRegistry.getShortSelectItemsHTML(tz)
        try:
            vars["displayTZMode"] = DisplayTimezoneRegistry.getSelectItemsHTML(u.getDisplayTZMode())
        except:
            vars["displayTZMode"] = "None"
        vars["Wtitle"] = _("Modifying an existing user")
        vars["name"] = vars.get("name", u.getName())
        vars["surName"] =  vars.get("surName", u.getSurName())
        vars["title"] = vars.get("title", u.getTitle())
        vars["lang"] = u.getLang()
        vars["organisation"] = vars.get("organisation", u.getOrganisations()[0])
        vars["address"] = vars.get("address", u.getAddresses()[0])
        vars["email"] = vars.get("email", u.getEmails()[0])
        vars["secEmails"] = self._getSecEmailHTML(vars.get("secEmails", u.getSecondaryEmails()))
        vars["telephone"] = vars.get("telephone", u.getTelephones()[0])
        vars["fax"] =  vars.get("fax", u.getFaxes()[0])
        return vars

    def _getSecEmailHTML(self, secEmails):
        html = [ _("""<input type="text" name="secEmailAdd" value="" size="25"><input type="submit" name="addSecEmail" value="_("Add")"><br>""")]
        emails = []
        for email in secEmails:
            emails.append("""<input type="hidden" name="secEmails" value="%s">
                            <input type="checkbox" name="secEmailRemove" value="%s"> %s"""%(email, email, email))
        html.append("<br>".join(emails))
        if secEmails:
            html.append( _("""<input type="submit" name="removeSecEmail" value="_("Remove")">"""))

        return "\n".join(html)


class WPUserModification( WPUserBase ):

    def __init__(self, rh, avatar, params):
        WPUserBase.__init__(self, rh)
        self._avatar = avatar
        self._params = params

    def _getTabContent( self, params ):
        p = WUserModify( self._avatar )
        self._params["postURL"] =  urlHandlers.UHUserModification.getURL()
        if self._params["msg"] != "":
            self._params["msg"] = "<table bgcolor=\"gray\"><tr><td bgcolor=\"white\">\n<font size=\"+1\" color=\"red\"><b>%s</b></font>\n</td></tr></table>"%self._params["msg"]
        return p.getHTML( self._params )


class WIdentityModification(wcomponents.WTemplated):

    def __init__( self, av, identity=None ):
        self._avatar = av
        self._identity = identity

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )

        locatorList = ["""<input type="hidden" name="userId" value="%s">"""%self._avatar.getId() ]
        if self._identity == None:
            WTitle = _("New Identity for user")+" :<br>%s"%(self._avatar.getFullName())
            WDescription = ""
            login = vars.get("login",self._avatar.getEmail())
            password = ""
        else:
            WTitle, WDescription = "", ""
            login = self._identity.getId()
            password = ""

        vars["login"] = login
        vars["password"] = password

        if vars.get("WTitle",None) is None :
            vars["WTitle"] = WTitle
        if vars.get("WDescription",None) is None :
            vars["WDescription"] = WDescription
        if vars.get("disabledLogin",None) is None :
            vars["disabledLogin"] = ""
            vars["hiddenLogin"] = ""
        else :
            vars["hiddenLogin"] = """<input type=hidden name="login" value="%s">"""%vars["login"]
        if vars.get("disabledSystem",None) is None :
            vars["disabledSystem"] = ""

        vars["locator"] = "\n".join(locatorList)
        html = ""
        am = AuthenticatorMgr()
        for auth in am.getList():
            html = html + "<option value=" + auth.getId() + ">" + auth.getName() + "</option>\n"
        vars["systemList"] = html
        return vars


class WPIdentityCreation(WPUserBase):

    def __init__(self, rh, av, params):
        WPUserBase.__init__(self, rh)
        self._avatar = av
        self._params = params

    def _getTabContent(self, params):
        c = WIdentityModification( self._avatar )
        self._params["identityId"] = ""
        self._params["postURL"] = urlHandlers.UHUserIdentityCreation.getURL()
        return c.getHTML( self._params )


class WPIdentityChangePassword(WPUserBase):

    def __init__(self, rh, av, params):
        WPUserBase.__init__(self, rh)
        self._avatar = av
        self._params = params

    def _getTabContent(self, params):

        identity = self._avatar.getIdentityById(self._params["identityId"],"Local")
        c = WIdentityModification( self._avatar, identity )
        postURL = urlHandlers.UHUserIdentityChangePassword.getURL()
        self._params["postURL"] = postURL
        self._params["WTitle"] = _("Change password for user")+" :<br>%s"%self._avatar.getFullName()
        self._params["disabledLogin"] = "disabled"
        self._params["disabledSystem"] = "disabled"
        self._params["login"] = self._params["identityId"]
        return c.getHTML( self._params )



class WPGroupCommon(WPUsersAndGroupsCommon):

    def __init__( self, rh ):
        WPUsersAndGroupsCommon.__init__( self, rh )

    def _setActiveTab( self ):
        self._subTabGroups.setActive()

class WHTMLGroupList(wcomponents.WTemplated):

    def __init__(self, groupList):
        self._groupList = groupList

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        color="white"
        ul = []
        vars["groupList"] = ""
        ul.append( _("""
                        <tr>
                            <td bgcolor="white" style="color:black" align="center"><b>%s _("groups")</b></td>
                        </tr>
                        """)%len(self._groupList))
        for g in self._groupList:
            if color=="white":
                color="#ececec"
            else:
                color="white"
            url = vars["groupDetailsURLGen"]( g )
            ul.append("""<tr>
                            <td bgcolor="%s"><a href="%s">%s</a></td>
                         </tr>"""%(color, url, self.htmlText(g.getName())))
        if ul:
            vars["groupList"] += "".join( ul )
        else:
            vars["groupList"] += _("""<tr>
                            <td><br><span class="blacktext">&nbsp;&nbsp;&nbsp; _("No group returned")</span></td></tr>""")
        return vars

class WBrowseGroups( wcomponents.WTemplated ):

    def __init__( self, letter=None ):
        self._letter = letter

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        gh = user.GroupHolder()
        letters = gh.getBrowseIndex()
        vars["browseIndex"] = """
        <span class="nav_border"><a href='' class="nav_link" onClick="document.browseForm.letter.disable=1;document.browseForm.submit();return false;">clear</a></span>"""
        if self._letter == "all":
            vars["browseIndex"] += """
        [all] """
        else:
            vars["browseIndex"] += """
        <span class="nav_border"><a href='' class="nav_link" onClick="document.browseForm.letter.value='all';document.browseForm.submit();return false;">all</a></span> """
        for letter in letters:
            if self._letter == letter:
                vars["browseIndex"] += """\n[%s] """ % letter
            else:
                vars["browseIndex"] += """\n<span class="nav_border"><a href='' class="nav_link" onClick="document.browseForm.letter.value='%s';document.browseForm.submit();return false;">%s</a></span> """ % (escape(letter,True),letter)
        vars["browseResult"] = ""
        res = []
        if self._letter != None:
            if self._letter != "all":
                res = gh.matchFirstLetter(self._letter, forceWithoutExtAuth=False)
            else:
                res = gh.getValuesToList()
            res.sort(utils.sortGroupsByName)
            vars["browseResult"] = WHTMLGroupList(res).getHTML(vars)
        return vars

class WGroupList(wcomponents.WTemplated):

    def __init__( self, criteria ):
        self._criteria = criteria

    def _performSearch( self, criteria ):
        gh = user.GroupHolder()
        res = gh.match(criteria,forceWithoutExtAuth=True)
        return res

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["createGroupURL"] = urlHandlers.UHNewGroup.getURL()
        vars["nbGroups"] = user.GroupHolder().getLength()
        vars["browseGroups"] = WBrowseGroups(vars.get("letter",None)).getHTML(vars)
        vars["browseGroupsURL"] = urlHandlers.UHGroups.getURL()
        vars["searchGroupsURL"] = urlHandlers.UHGroups.getURL()
        vars["groups"] = ""
        if self._criteria and self._criteria["name"] != "":
            groupList = self._performSearch(self._criteria)
            vars["groups"] = WHTMLGroupList(groupList).getHTML(vars)
        return vars


class WPGroupList(WPGroupCommon):

    def __init__(self, rh, params):
        WPGroupCommon.__init__(self,rh)
        self._params = params

    def _getTabContent( self, params ):
        criteria = {}
        if filter(lambda x: self._params[x], self._params):
            criteria["name"] = self._params.get("sName","")
        comp = WGroupList(criteria)
        self._params["groupDetailsURLGen"]=urlHandlers.UHGroupDetails.getURL
        return comp.getHTML(self._params)


class WGroupModification(wcomponents.WTemplated):

    def __init__( self, group=None ):
        self._group = group

    def __setNewGroupVars( self, vars={} ):
        vars["Wtitle"] = _("Creating a new group")
        vars["name"] = ""
        vars["email"] = ""
        vars["description"] = ""

    def __setGroupVars( self, group, vars ):
        vars["Wtitle"] = _("Modifying group basic data")
        vars["name"] = group.getName()
        vars["email"] = group.getEmail()
        vars["description"] = group.getDescription()

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        if self._group == None:
            self.__setNewGroupVars( vars )
            vars["locator"] = ""
        else:
            self.__setGroupVars( self._group, vars )
            vars["locator"] = self._group.getLocator().getWebForm()
        return vars


class WPGroupCreation(WPGroupCommon):

    def _getTabContent( self, params ):
        comp = WGroupModification()
        pars = {"postURL": urlHandlers.UHGroupPerformRegistration.getURL(), \
                "backURL": urlHandlers.UHGroups.getURL() }
        return comp.getHTML( pars )

class WPLDAPGroupCreation(WPGroupCommon):

    def _getTabContent( self, params ):
        comp = WLDAPGroupModification()
        pars = {"postURL": urlHandlers.UHLDAPGroupPerformRegistration.getURL() }
        return comp.getHTML( pars )


class WPGroupBase( WPGroupCommon ):

    def __init__( self, rh, grp ):
        WPGroupCommon.__init__( self, rh )
        self._group = grp


class WGroupDetails(wcomponents.WTemplated):

    def __init__( self, group ):
        self._group = group

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["disabledSubmit"] = ""
        vars["disabledAdd"] = ""
        vars["disabledModify"] = ""
        if isinstance(self._group, user.CERNGroup):
            vars["disabledSubmit"] = "disabled"
            vars["disabledAdd"] = "disabled"
            vars["disabledModify"] = "disabled"
        vars["name"] = self._group.getName()
        vars["description"] = self._group.getDescription()
        vars["email"] = self._group.getEmail()
        vars["membersList"] = wcomponents.WPrincipalTable().getHTML( self._group.getMemberList(),  None, vars["addMembersURL"], vars["removeMembersURL"], selectable=False )
        vars["locator"] = self._group.getLocator().getWebForm()
        return vars


class WPGroupDetails( WPGroupBase ):

    def _getTabContent( self, params ):
        c = WGroupDetails( self._group )
        pars = { \
    "modifyURL": urlHandlers.UHGroupModification.getURL( self._group ),\
    "detailsURLGen": urlHandlers.UHPrincipalDetails.getURL, \
    "addMembersURL": urlHandlers.UHGroupSelectMembers.getURL(self._group),\
    "removeMembersURL": urlHandlers.UHGroupRemoveMembers.getURL(self._group), \
    "backURL": urlHandlers.UHGroups.getURL() }
        return c.getHTML( pars )


class WPGroupModificationBase( WPGroupBase ):
    pass


class WLDAPGroupModification(wcomponents.WTemplated):

    def __init__( self, group=None ):
        self._group = group

    def __setNewGroupVars( self, vars={} ):
        vars["Wtitle"] = _("Creating a new LDAP group")
        vars["name"] = ""
        vars["description"] = ""

    def __setGroupVars( self, group, vars ):
        vars["Wtitle"] = _("Modifying LDAP group basic data")
        vars["name"] = group.getName()
        vars["description"] = group.getDescription()

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        if self._group == None:
            self.__setNewGroupVars( vars )
            vars["locator"] = ""
        else:
            self.__setGroupVars( self._group, vars )
            vars["locator"] = self._group.getLocator().getWebForm()
        return vars


class WPGroupModification( WPGroupModificationBase ):

    def _getTabContent( self, params ):
        comp = WGroupModification( self._group )
        params["postURL"] = urlHandlers.UHGroupPerformModification.getURL()
        params["backURL"] = urlHandlers.UHGroupDetails.getURL( self._group )
        return comp.getHTML( params )


class WPGroupSelectMembers( WPGroupModificationBase ):

    def _getTabContent( self, params ):
        searchExt = params.get("searchExt","")

        if searchExt != "":
            searchLocal = False
        else:
            searchLocal = True
        comp = wcomponents.WPrincipalSelection( urlHandlers.UHGroupSelectMembers.getURL(),forceWithoutExtAuth=searchLocal )
        params["addURL"] = urlHandlers.UHGroupAddMembers.getURL()
        return comp.getHTML( params )


class WPSelectUserToLogAs(WPUserCommon ):

#    def _getTabContent( self, params ):
#        wc = WSelectUserToLogAs()
#        pars = {"submitURL":urlHandlers.UHLogMeAs.getURL()}
#        return wc.getHTML( pars )

    def _getTabContent( self, params ):
        searchURL = urlHandlers.UHLogMeAs.getURL()
        #cancelURL = urlHandlers.UHUsers.getURL()
        wc = wcomponents.WUserSelection( searchURL, multi=False, forceWithoutExtAuth=True )
        wc.setTitle(_("Select user to log in as"))
        params["addURL"] =  urlHandlers.UHLogMeAs.getURL()

        return wc.getHTML( params )




class WPUserMerge( WPUserCommon ):

    def __init__(self, rh, prin, toMerge):
        WPUserCommon.__init__(self, rh)
        self.prin = prin
        self.toMerge = toMerge

    def _getTabContent( self, params ):
        wc = WUserMerge(self.prin, self.toMerge)
        pars = {"submitURL":urlHandlers.UHUserMerge.getURL()}
        return wc.getHTML( pars )

class WUserMerge(wcomponents.WTemplated):

    def __init__(self, prin, toMerge):
        self.prin = prin
        self.toMerge = toMerge

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["prinId"] = ""
        vars["ptitle"] = ""
        vars["pname"] = ""
        vars["pfirstName"] = ""
        vars["porganisation"] = ""
        vars["pemail"] = ""
        vars["paddress"] = ""
        vars["ptelephone"] = ""
        vars["pfax"] = ""
        vars["plogins"] = ""
        vars["toMergeId"] = ""
        vars["mtitle"] = ""
        vars["mname"] = ""
        vars["mfirstName"] = ""
        vars["morganisation"] = ""
        vars["memail"] = ""
        vars["maddress"] = ""
        vars["mtelephone"] = ""
        vars["mfax"] = ""
        vars["mlogins"] = ""

        if self.prin:
            vars["prinId"] = self.prin.getId()
            vars["ptitle"] = self.prin.getTitle()
            vars["pname"] = self.prin.getSurName()
            vars["pfirstName"] = self.prin.getName()
            vars["porganisation"] = self.prin.getOrganisation()
            vars["pemail"] = "<br>".join(self.prin.getEmails())
            vars["paddress"] = self.prin.getAddress()
            vars["ptelephone"] = self.prin.getTelephone()
            vars["pfax"] = self.prin.getFax()
            il = ["<table>"]
            for item in self.prin.getIdentityList():
                il.append("""
                            <tr>
                                <td width="60%%">
                                    %s
                                </td>
                                <td width="20%%">
                                    <small>%s</small>
                                </td>
                            </tr>
                            """%(item.getLogin(), item.getAuthenticatorTag()) )
            il.append("</table>")
            vars["plogins"] = "".join( il )

        if self.toMerge:
            vars["toMergeId"] = self.toMerge.getId()
            vars["mtitle"] = self.toMerge.getTitle()
            vars["mname"] = self.toMerge.getSurName()
            vars["mfirstName"] = self.toMerge.getName()
            vars["morganisation"] = self.toMerge.getOrganisation()
            vars["memail"] = "<br>".join(self.toMerge.getEmails())
            vars["maddress"] = self.toMerge.getAddress()
            vars["mtelephone"] = self.toMerge.getTelephone()
            vars["mfax"] = self.toMerge.getFax()
            il = ["<table>"]
            for item in self.toMerge.getIdentityList():
                il.append("""
                            <tr>
                                <td width="60%%">
                                    %s
                                </td>
                                <td width="20%%">
                                    <small>%s</small>
                                </td>
                            </tr>
                            """%(item.getLogin(), item.getAuthenticatorTag()) )
            il.append("</table>")
            vars["mlogins"] = "".join( il )



        return vars

class WPUserMergeSelectPrin(WPUserMerge):

    def _getTabContent( self, params ):
        searchURL = urlHandlers.UHUserMerge.getURL()
        #searchURL.addParam("selectPrin", "sp")
        addURL = urlHandlers.UHUserMerge.getURL()
        addURL.addParam("setPrin", "setPrin")
        #cancelURL = urlHandlers.UHUserMerge.getURL()
        wc = wcomponents.WUserSelection( searchURL, multi=False, forceWithoutExtAuth=True )
        wc.setTitle("Select user")
        params["addURL"] =  addURL
        html = _("""<table align="center" width="95%%">
    <tr>
       <td class="formTitle"> _("General admin data")</td>
    </tr>
    <tr>
        <td>
            <br>
        """)
        html = "%s%s"%(html,wc.getHTML( params ))
        return "%s%s"%(html,"""</td></tr></table>""")

class WPUserMergeSelectToMerge(WPUserMerge):

    def _getTabContent( self, params ):
        searchURL = urlHandlers.UHUserMerge.getURL()
        #searchURL.addParam("selectToMerge", "sp")
        addURL = urlHandlers.UHUserMerge.getURL()
        addURL.addParam("setToMerge", "setToMerge")
        #cancelURL = urlHandlers.UHUserMerge.getURL()
        wc = wcomponents.WUserSelection( searchURL, multi=False, forceWithoutExtAuth=True )
        wc.setTitle("Select user")
        params["addURL"] =  addURL
        html = _("""<table align="center" width="95%%">
    <tr>
       <td class="formTitle"> _("General admin data")</td>
    </tr>
    <tr>
        <td>
            <br>
        """)
        html = "%s%s"%(html,wc.getHTML( params ))
        return "%s%s"%(html,"""</td></tr></table>""")

class WPRoomsBase( WPAdminsBase ):
    def _setActiveSideMenuItem(self):
        self._roomsMenuItem.setActive()

    def _createTabCtrl( self ):
        self._tabCtrl = wcomponents.TabControl()

        self._subTabRoomBooking = self._tabCtrl.newTab( "booking", _("Room Booking"), \
                urlHandlers.UHRoomBookingPluginAdmin.getURL() )
        self._subTabMain = self._subTabRoomBooking.newSubTab( "main", _("Main"), \
                urlHandlers.UHRoomBookingPluginAdmin.getURL() )
        self._subTabConfig = self._subTabRoomBooking.newSubTab( "configuration", _("Configuration"), \
                urlHandlers.UHRoomBookingAdmin.getURL() )
        self._subTabRoomMappers = self._tabCtrl.newTab( "mappers", _("Room Mappers"), \
                urlHandlers.UHRoomMappers.getURL() )

    def _getPageContent(self, params):
        return wcomponents.WTabControl( self._tabCtrl, self._getAW() ).getHTML( self._getTabContent( params ) )

class WPRoomMapperBase( WPRoomsBase ):

    def __init__( self, rh ):
        WPRoomsBase.__init__( self, rh )

    def _setActiveTab( self ):
        self._subTabRoomMappers.setActive()

class WRoomMapperList(wcomponents.WTemplated):

    def __init__( self, criteria ):
        self._criteria = criteria

    def _performSearch( self, criteria ):
        rmh = roomMapping.RoomMapperHolder()
        res = rmh.match(criteria)
        return res

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["createRoomMapperURL"] = urlHandlers.UHNewRoomMapper.getURL()
        vars["searchRoomMappersURL"] = urlHandlers.UHRoomMappers.getURL()
        vars["roomMappers"] = ""
        if self._criteria:
            vars["roomMappers"] = """<tr>
                              <td>
                    <br>
                <table width="100%%" align="left" style="border-top: 1px solid #777777; padding-top:10px">"""
            roomMapperList = self._performSearch(self._criteria)
            ul = []
            color="white"
            ul = []
            for rm in roomMapperList:
                if color=="white":
                    color="#F6F6F6"
                else:
                    color="white"
                url = vars["roomMapperDetailsURLGen"]( rm )
                ul.append("""<tr>
                                <td bgcolor="%s"><a href="%s">%s</a></td>
                            </tr>"""%(color, url, rm.getName() ) )
            if ul:
                vars["roomMappers"] += "".join( ul )
            else:
                vars["roomMappers"] += _("""<tr>
                            <td><br><span class="blacktext">&nbsp;&nbsp;&nbsp; _("No room mappers for this search")</span></td></tr>""")
            vars["roomMappers"] += """    </table>
                      </td>
                </tr>"""
        return vars


class WPRoomMapperList( WPRoomMapperBase ):

    def __init__( self, rh, params ):
        WPRoomMapperBase.__init__( self, rh )
        self._params = params

    def _getTabContent( self, params ):
        criteria = {}
        if filter(lambda x: self._params[x], self._params):
            criteria["name"] = self._params.get("sName","")
        comp = WRoomMapperList(criteria)
        pars = {"roomMapperDetailsURLGen": urlHandlers.UHRoomMapperDetails.getURL }
        return comp.getHTML(pars)


class WRoomMapperDetails(wcomponents.WTemplated):

    def __init__( self, rm):
        self._roomMapper = rm

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["name"] = self._roomMapper.getName()
        vars["description"] = self._roomMapper.getDescription()
        vars["url"] = self._roomMapper.getBaseMapURL()
        vars["placeName"] = self._roomMapper.getPlaceName()
        vars["regexps"] = "<ul><li>%s</li></ul>"%"</li><li>".join(self._roomMapper.getRegularExpressions())
        return vars


class WPRoomMapperDetails( WPRoomMapperBase ):

    def __init__(self, rh, roomMapper):
        WPRoomMapperBase.__init__(self, rh)
        self._roomMapper = roomMapper

    def _getTabContent( self, params ):
        comp = WRoomMapperDetails( self._roomMapper )
        pars = {"modifyURL": urlHandlers.UHRoomMapperModification.getURL( self._roomMapper ) }
        return comp.getHTML( pars )


class WRoomMapperEdit(wcomponents.WTemplated):

    def __init__( self, rm=None ):
        self._roomMapper = rm

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["name"] = ""
        vars["description"] = ""
        vars["url"] = ""
        vars["placeName"] = ""
        vars["regexps"] = ""
        vars["locator"] = ""
        if self._roomMapper:
            vars["name"] = self._roomMapper.getName()
            vars["description"] = self._roomMapper.getDescription()
            vars["url"] = self._roomMapper.getBaseMapURL()
            vars["placeName"] = self._roomMapper.getPlaceName()
            vars["regexps"] = "\r\n".join(self._roomMapper.getRegularExpressions())
            vars["locator"] = self._roomMapper.getLocator().getWebForm()
        return vars


class WPRoomMapperModification( WPRoomMapperBase ):

    def __init__(self, rh, domain):
        WPRoomMapperBase.__init__(self, rh)
        self._domain = domain

    def _getTabContent( self, params ):
        comp = WRoomMapperEdit( self._domain )
        pars = {"postURL": urlHandlers.UHRoomMapperPerformModification.getURL() }
        return comp.getHTML( pars )


class WPRoomMapperCreation( WPRoomMapperBase ):

    def _getTabContent( self, params ):
        comp = WRoomMapperEdit()
        pars = {"postURL": urlHandlers.UHRoomMapperPerformCreation.getURL()}
        return comp.getHTML( pars )



class WPDomainBase( WPAdminsBase ):

    def __init__( self, rh ):
        WPAdminsBase.__init__( self, rh )

    def _setActiveSideMenuItem( self ):
        self._domainsMenuItem.setActive()

class WBrowseDomains( wcomponents.WTemplated ):

    def __init__( self, letter=None ):
        self._letter = letter

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        dh = domain.DomainHolder()
        letters = dh.getBrowseIndex()
        vars["browseIndex"] = _("""
        <span class="nav_border"><a href='' class="nav_link" onClick="document.browseForm.letter.disable=1;document.browseForm.submit();return false;">_("clear")</a></span>""")
        if self._letter == "all":
            vars["browseIndex"] += """
        [all] """
        else:
            vars["browseIndex"] += _("""
        <span class="nav_border"><a href='' class="nav_link" onClick="document.browseForm.letter.value='all';document.browseForm.submit();return false;">_("all")</a></span> """)
        for letter in letters:
            if self._letter == letter:
                vars["browseIndex"] += """\n[%s] """ % letter
            else:
                vars["browseIndex"] += """\n<span class="nav_border"><a href='' class="nav_link" onClick="document.browseForm.letter.value='%s';document.browseForm.submit();return false;">%s</a></span> """ % (escape(letter,True),letter)
        vars["browseResult"] = ""
        res = []
        if self._letter not in [ None, "" ]:
            if self._letter != "all":
                res = dh.matchFirstLetter(self._letter)
            else:
                res = dh.getValuesToList()
            res.sort(utils.sortDomainsByName)
            vars["browseResult"] = WHTMLDomainList(vars,res).getHTML()
        return vars

class WDomainList(wcomponents.WTemplated):

    def __init__( self, criteria, params ):
        self._criteria = criteria
        self._params = params

    def _performSearch( self, criteria ):
        dh = domain.DomainHolder()
        res = dh.match(criteria)
        return res

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["createDomainURL"] = urlHandlers.UHNewDomain.getURL()
        vars["nbDomains"] = domain.DomainHolder().getLength()
        vars["browseDomains"] = WBrowseDomains(self._params.get("letter",None)).getHTML(vars)
        vars["browseDomainsURL"] = urlHandlers.UHDomains.getURL()
        vars["searchDomainsURL"] = urlHandlers.UHDomains.getURL()
        vars["domains"] = ""
        if self._criteria:
            domainList = self._performSearch(self._criteria)
            vars["domains"] = WHTMLDomainList(vars,domainList).getHTML()
        return vars

class WHTMLDomainList:

    def __init__(self, vars, list):
        self._vars = vars
        self._list = list

    def getHTML(self):
        text = """<tr>
                              <td>
                    <br>
                <table width="100%%" align="left" style="border-top: 1px solid #777777; padding-top:10px">"""
        color="white"
        ul = []
        for dom in self._list:
            if color=="white":
                color="#F6F6F6"
            else:
                color="white"
            url = self._vars["domainDetailsURLGen"]( dom )
            ul.append("""<tr>
                            <td bgcolor="%s"><a href="%s">%s</a></td>
                        </tr>"""%(color, url, dom.getName() ) )
        if ul:
            text += "".join( ul )
        else:
            text += """<tr>
                        <td><br><span class="blacktext">&nbsp;&nbsp;&nbsp;No domains for this search</span></td></tr>"""
        text += """    </table>
                      </td>
                </tr>"""
        return text

class WPDomainList( WPDomainBase ):

    def __init__( self, rh, params ):
        WPDomainBase.__init__( self, rh )
        self._params = params

    def _getPageContent( self, params ):
        criteria = {}
        if self._params.get("sName","") != "":
            criteria["name"] = self._params.get("sName","")
        comp = WDomainList(criteria,self._params)
        pars = {"domainDetailsURLGen": urlHandlers.UHDomainDetails.getURL }
        return comp.getHTML(pars)


class WDomainDetails(wcomponents.WTemplated):

    def __init__( self, dom):
        self._domain = dom

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["name"] = self._domain.getName()
        vars["description"] = self._domain.getDescription()
        vars["filters"] = "<br>".join(self._domain.getFilterList())
        return vars


class WPDomainDetails( WPDomainBase ):

    def __init__(self, rh, domain):
        WPDomainBase.__init__(self, rh)
        self._domain = domain

    def _getPageContent( self, params ):
        comp = WDomainDetails( self._domain )
        pars = {"modifyURL": urlHandlers.UHDomainModification.getURL( self._domain ) }
        return comp.getHTML( pars )


class WDomainDataModification(wcomponents.WTemplated):

    def __init__( self, dom ):
        self._domain = dom

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["name"] = self._domain.getName()
        vars["description"] = self._domain.getDescription()
        vars["filters"] = ";".join( self._domain.getFilterList() )
        vars["locator"] = self._domain.getLocator().getWebForm()
        return vars


class WPDomainModification( WPDomainBase ):

    def __init__(self, rh, domain):
        WPDomainBase.__init__(self, rh)
        self._domain = domain

    def _getPageContent( self, params ):
        comp = WDomainDataModification( self._domain )
        pars = {"postURL": urlHandlers.UHDomainPerformModification.getURL() }
        return comp.getHTML( pars )


class WDomainCreation(wcomponents.WTemplated):
    pass


class WPDomainCreation( WPDomainBase ):

    def _getPageContent( self, params ):
        comp = WDomainCreation()
        pars = {"postURL": urlHandlers.UHDomainPerformCreation.getURL()}
        return comp.getHTML( pars )



# Room Booking Module ========================================


class WPRoomBookingPluginAdminBase( WPRoomsBase ):

    def __init__( self, rh ):
        WPRoomsBase.__init__( self, rh )

    def getJSFiles(self):
        return WPRoomsBase.getJSFiles(self) + \
               self._includeJSPackage('Management')

    def _setActiveTab( self ):
        self._subTabRoomBooking.setActive()

class WPRoomBookingPluginAdmin( WPRoomBookingPluginAdminBase ):

    def __init__( self, rh, params ):
        WPRoomBookingPluginAdminBase.__init__( self, rh )
        self._params = params

    def _setActiveTab( self ):
        WPRoomBookingPluginAdminBase._setActiveTab( self )
        self._subTabMain.setActive()

    def _getTabContent( self, params ):
        wc = WRoomBookingPluginAdmin( self._rh )
        return wc.getHTML( params )

class WRoomBookingPluginAdmin( wcomponents.WTemplated ):

    def __init__( self, rh ):
        self._rh = rh

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()

        iconDisabled = str(Config.getInstance().getSystemIconURL( "disabledSection" ))
        iconEnabled = str(Config.getInstance().getSystemIconURL( "enabledSection" ))
        if minfo.getRoomBookingModuleActive():
            vars["iconURL"] = iconEnabled
            vars["activationText"] = _("Click to DEACTIVATE Room Booking Module")
        else:
            vars["iconURL"] = iconDisabled
            vars["activationText"] = _("Click to ACTIVATE Room Booking Module")
        rbPlugins = PluginLoader.getPluginsByType("RoomBooking")
        vars["plugins"] = rbPlugins
        vars["zodbHost"] = self._rh._host
        vars["zodbPort"] = self._rh._port
        vars["zodbRealm"] = self._rh._realm
        vars["zodbUser"] = self._rh._user
        vars["zodbPassword"] = self._rh._password

        return vars


class WPRoomBookingRoomForm( WPRoomBookingPluginAdminBase ):

    _userData = ['favorite-user-list']

    def __init__( self, rh ):
        self._rh = rh
        WPRoomBookingPluginAdminBase.__init__( self, rh )

    def _setActiveTab( self ):
        WPRoomBookingPluginAdminBase._setActiveTab( self )
        self._subTabConfig.setActive()

    def _getTabContent( self, params ):
        wc = wcomponents.WRoomBookingRoomForm( self._rh )
        return wc.getHTML( params )

class WPRoomBookingAdmin( WPRoomBookingPluginAdminBase ):

    def __init__( self, rh ):
        self._rh = rh
        WPRoomBookingPluginAdminBase.__init__( self, rh )

    def _setActiveTab( self ):
        self._subTabConfig.setActive()

    def _getTabContent( self, params ):
        wc = wcomponents.WRoomBookingAdmin( self._rh )
        return wc.getHTML( params )

class WPRoomBookingAdminLocation( WPRoomBookingPluginAdminBase ):

    def __init__( self, rh, location, actionSucceeded = False ):
        self._rh = rh
        self._location = location
        self._actionSucceeded = actionSucceeded
        WPRoomBookingPluginAdminBase.__init__( self, rh )

    def _setActiveTab( self ):
        self._subTabConfig.setActive()

    def _getTabContent( self, params ):
        wc = wcomponents.WRoomBookingAdminLocation( self._rh, self._location )
        params['actionSucceeded'] = self._actionSucceeded
        return wc.getHTML( params )

class WPAdminsSystemBase(WPAdminsBase):
    def __init__( self, rh ):
        WPAdminsBase.__init__( self, rh )

    def _setActiveSideMenuItem(self):
        self._systemMenuItem.setActive()

    def _createTabCtrl( self ):
        self._tabCtrl = wcomponents.TabControl()

        self._subTabConfiguration = self._tabCtrl.newTab( "configuration", _("Configuration"), \
                urlHandlers.UHAdminsSystem.getURL() )
        self._subTabTaskManager = self._tabCtrl.newTab( "tasks", _("Task Manager"), \
                urlHandlers.UHTaskManager.getURL() )
        self._subTabMaintenance = self._tabCtrl.newTab( "maintenance", _("Maintenance"), \
                urlHandlers.UHMaintenance.getURL() )

    def _getPageContent(self, params):
        return wcomponents.WTabControl( self._tabCtrl, self._getAW() ).getHTML( self._getTabContent( params ) )

class WPAdminsSystem(WPAdminsSystemBase):

    def _setActiveTab( self ):
        self._subTabConfiguration.setActive()

    def _getTabContent( self, params ):
        wc = WAdminsSystem()
        return wc.getHTML( params )

class WAdminsSystem(wcomponents.WTemplated):

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        vars["minfo"] = minfo
        vars["ModifURL"] = urlHandlers.UHAdminsSystemModif.getURL()
        return vars

class WPAdminsSystemModif(WPAdminsSystemBase):

    def _getTabContent( self, params ):
        wc = WAdminsSystemModif()
        return wc.getHTML( params )

class WAdminsSystemModif(wcomponents.WTemplated):

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        vars["minfo"] = minfo
        vars["postURL"] = urlHandlers.UHAdminsSystemModif.getURL()
        return vars

class WPMaintenanceBase( WPAdminsSystemBase ):

    def __init__( self, rh ):
        WPAdminsBase.__init__( self, rh )

    def _setActiveTab( self ):
        self._subTabMaintenance.setActive()

class WPMaintenance( WPMaintenanceBase ):

    def __init__(self, rh, s, dbSize, nWebsessions):
        WPMaintenanceBase.__init__(self, rh)
        self._stat = s
        self._dbSize = dbSize
        self._nWebsessions = nWebsessions

    def _getTabContent( self, params ):
        wc = WAdminMaintenance()
        pars = { "cleanupURL": urlHandlers.UHMaintenanceTmpCleanup.getURL(), \
                 "tempSize": self._stat[0], \
                 "nFiles": "%s files"%self._stat[1], \
                 "nDirs": "%s folders"%self._stat[2], \
                 "packURL": urlHandlers.UHMaintenancePack.getURL(), \
                 "dbSize": self._dbSize, \
                 "websessionCleanupURL": urlHandlers.UHMaintenanceWebsessionCleanup.getURL(), \
                 "nWebsessions": self._nWebsessions}
        return wc.getHTML( pars )

class WAdminMaintenance(wcomponents.WTemplated):

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        return vars

class WPMaintenanceTmpCleanup(WPMaintenanceBase):

    def __init__(self,rh):
        WPMaintenanceBase.__init__(self,rh)

    def _getTabContent(self,params):
        wc=wcomponents.WConfirmation()
        msg="""Are you sure you want to delete the temporary directory
        (note that all the files in that directory will be deleted)?"""
        url=urlHandlers.UHMaintenancePerformTmpCleanup.getURL()
        return """
                <table align="center" width="95%%">
                    <tr>
                        <td class="formTitle">Maintenance: Cleaning-up temporary directory</td>
                    </tr>
                    <tr>
                        <td>
		            <br>
                            %s
                        </td>
                    </tr>
                </table>
                """%wc.getHTML(msg,url,{})

class WPMaintenancePack(WPMaintenanceBase):

    def __init__(self,rh):
        WPMaintenanceBase.__init__(self,rh)

    def _getTabContent(self,params):
        wc=wcomponents.WConfirmation()
        msg="""Are you sure you want to pack the database?"""
        url=urlHandlers.UHMaintenancePerformPack.getURL()
        return """
                <table align="center" width="95%%">
                    <tr>
                        <td class="formTitle">Maintenance: Database packing</td>
                    </tr>
                    <tr>
                        <td>
		            <br>
                            %s
                        </td>
                    </tr>
                </table>
                """%wc.getHTML(msg,url,{})

class WPMaintenanceWebsessionCleanup(WPMaintenanceBase):

    def __init__(self,rh):
        WPMaintenanceBase.__init__(self,rh)

    def _getTabContent(self,params):
        wc=wcomponents.WConfirmation()
        msg="""Are you sure you want to delete all the web sessions?"""
        url=urlHandlers.UHMaintenancePerformWebsessionCleanup.getURL()
        return """
                <table align="center" width="95%%">
                    <tr>
                        <td class="formTitle">Maintenance: Cleaning-up websession</td>
                    </tr>
                    <tr>
                        <td>
		            <br>
                            %s
                        </td>
                    </tr>
                </table>
                """%wc.getHTML(msg,url,{})


class WPTaskManagerBase(WPAdminsSystemBase):

    def __init__( self, rh ):
        WPAdminsBase.__init__( self, rh )

    def _setActiveTab( self ):
        self._subTabTaskManager.setActive()

class WPTaskManager( WPTaskManagerBase ):

    def _getTabContent( self, params ):
        wc = WTaskManager(HelperTaskList.getTaskListInstance())

        pars = {}
        return wc.getHTML( pars )

class WTaskManager(wcomponents.WTemplated):

    def  __init__(self, taskList):
        self.taskList = taskList

    def groupTasks(self, taskList):
        tasks = {}
        for task in taskList:
            if isinstance(task, Alarm):
                tasks.setdefault(Alarm, []).append(task)
            elif isinstance(task, Task):
                for obj in task.getObjList():
                    if isinstance(obj, PendingSubmitterReminder):
                        tasks.setdefault(PendingSubmitterReminder, []).append(task)
                    elif isinstance(obj, PendingManagerReminder):
                        tasks.setdefault(PendingManagerReminder, []).append(task)
                    elif isinstance(obj, PendingCoordinatorReminder):
                        tasks.setdefault(PendingCoordinatorReminder, []).append(task)
                    else:
                        tasks.setdefault("Other", []).append(task)
            else:
                tasks.setdefault("Other", []).append(task)
        return tasks

    def getHTMLTasks(self, type, taskList):
        html = []
        taskList.sort(lambda x,y: cmp(x.getId(),y.getId()))
        if type == Alarm:
            taskList.sort(lambda x,y: cmp(x.getStartDate(),y.getStartDate()))
            html.append(_("""<tr><td valign="top"><b>_("Alarm")</b></td></tr>"""))
            html.append(_("""<tr><td><table><tr>
                    <td></td>
                    <td><u>_("Id")</u></td>
                    <td><u>_("Conference")</u></td>
                    <td><u>_("Date")</u></td></tr>"""))
            for task in taskList:
                delete = urlHandlers.UHRemoveTask.getURL()
                delete.addParam("taskId", task.getId())
                title = task.conf.getTitle()
                if len(title) > 30:
                    title = title[:30] + "..."
                confHtml = """<a href="%s">%s</a>"""%(urlHandlers.UHConfDisplayAlarm.getURL(task.conf), title)
                date = task.getAdjustedStartDate().strftime("%a %d %b %Y %H:%M")+" (%s)"%task.conf.getTimezone()
                html.append("""<tr>
                    <td><a href="%s">Delete</a></td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td></tr>"""%(delete, task.getId(), confHtml, date))
            html.append("</table></td></tr>")

        elif type == PendingSubmitterReminder:
            html.append("""<tr><td valign="top"><b>Pending submitters</b></td></tr>""")
            html.append("""<tr><td><table><tr>
                    <td></td>
                    <td><u>Id</u></td>
                    <td><u>Pending</u></td>
                    <td><u>Email</u></td>
                    <td><u>Contribution (start date)</u></td>
                    <td><u>Last sent on</u></td>
                    <td><u>Interval</u></td>
                    <td><u>End date</u></td></tr>""")
            for task in taskList:
                delete = urlHandlers.UHRemoveTask.getURL()
                delete.addParam("taskId", task.getId())
                obj = task.getObjList()[0]
                pending = "No pending"
                email = obj.getEmail()
                contibHtml = []
                if obj.getPendings():
                    pending = obj.getPendings()[0].getFullName()
                for pend in obj.getPendings():
                    title = pend.getContribution().getTitle()
                    if len(title) > 30:
                        title = title[:30] + "..."
                    contibDate = "---"
                    if pend.getContribution().getStartDate():
                        contibDate = pend.getContribution().getStartDate().strftime("%Y-%m-%d %H:%M")
                    contibHtml.append("""<a href="%s">%s</a><br>(%s)"""%(urlHandlers.UHContributionDisplay.getURL(pend.getContribution()), title, contibDate))
                if contibHtml != []:
                    contibHtml = "<br>".join(contibHtml)
                else:
                    contibHtml = "No contribution"
                lastDate = "None"
                if task.getLastDate():
                    lastDate = task.getLastDate().strftime("%Y-%m-%d %H:%M")
                html.append("""<tr valign="top">
                    <td><a href="%s">Delete</a></td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td nowrap>%s</td>
                    <td nowrap>%s</td>
                    <td nowrap>%s days</td>
                    <td nowrap>%s</td></tr>"""%(delete, task.getId(), pending, email, contibHtml, lastDate, str(task.getInterval().days), str(task.getEndDate().strftime("%Y-%m-%d %H:%M")) ))
            html.append("</table></td></tr>")


        elif type == PendingManagerReminder:
            html.append("""<tr><td valign="top"><b>Pending Managers</b></td></tr>""")
            html.append("""<tr><td><table><tr>
                    <td></td>
                    <td><u>Id</u></td>
                    <td><u>Pending</u></td>
                    <td><u>Email</u></td>
                    <td><u>Session (start date)</u></td>
                    <td><u>Last sent</u></td></tr>""")
            for task in taskList:
                delete = urlHandlers.UHRemoveTask.getURL()
                delete.addParam("taskId", task.getId())
                obj = task.getObjList()[0]
                pending = "No pending"
                email = obj.getEmail()
                sesHtml = []
                if obj.getPendings():
                    pending = obj.getPendings()[0].getFullName()
                for pend in obj.getPendings():
                    title = pend.getSession().getTitle()
                    if len(title) > 30:
                        title = title[:30] + "..."
                    sessionDate = "---"
                    if pend.getSession().getStartDate():
                        sessionDate = pend.getSession().getStartDate().strftime("%a %d %b %Y %H:%M")
                    sesHtml.append("""<a href="%s">%s</a> (%s)"""%(urlHandlers.UHSessionDisplay.getURL(pend.getSession()), title, sessionDate))
                if sesHtml != []:
                    sesHtml = "<br>".join(sesHtml)
                else:
                    sesHtml = "No session"
                lastDate = "None"
                if task.getLastDate():
                    lastDate = task.getLastDate().strftime("%a %d %b %Y %H:%M")
                html.append("""<tr>
                    <td><a href="%s">Delete</a></td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td nowrap>%s</td>
                    <td nowrap>%s</td></tr>"""%(delete, task.getId(), pending, email, sesHtml, lastDate))
            html.append("</table></td></tr>")


        elif type == PendingCoordinatorReminder:
            html.append("""<tr><td valign="top"><b>Pending Coordinators</b></td></tr>""")
            html.append("""<tr><td><table><tr>
                    <td></td>
                    <td><u>Id</td>
                    <td><u>Pending</td>
                    <td><u>Email</td>
                    <td><u>Session (start date)</td>
                    <td><u>Last sent</u></td></tr>""")
            for task in taskList:
                delete = urlHandlers.UHRemoveTask.getURL()
                delete.addParam("taskId", task.getId())
                obj = task.getObjList()[0]
                pending = "No pending"
                email = obj.getEmail()
                sesHtml = []
                if obj.getPendings():
                    pending = obj.getPendings()[0].getFullName()
                for pend in obj.getPendings():
                    title = pend.getSession().getTitle()
                    if len(title) > 30:
                        title = title[:30] + "..."
                    sessionDate = "---"
                    if pend.getSession().getStartDate():
                        sessionDate = pend.getSession().getStartDate().strftime("%a %d %b %Y %H:%M")
                    sesHtml.append("""<a href="%s">%s</a> (%s)"""%(urlHandlers.UHSessionDisplay.getURL(pend.getSession()), title, sessionDate))
                if sesHtml != []:
                    sesHtml = "<br>".join(sesHtml)
                else:
                    sesHtml = "No session"
                lastDate = "None"
                if task.getLastDate():
                    lastDate = task.getLastDate().strftime("%a %d %b %Y %H:%M")
                html.append("""<tr>
                    <td><a href="%s">Delete</a></td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td nowrap>%s</td>
                    <td nowrap>%s</td></tr>"""%(delete, task.getId(), pending, email, sesHtml, lastDate))
            html.append("</table></td></tr>")
        else:
            html.append("""<tr><td valign="top"><table><tr><td><b>Other</b></td><td><b>run every</b></td><td><b>last run</b></td></tr>""")
            for task in taskList:
                if task.getLastDate():
                    lastdate = task.getLastDate().strftime("%a %d %b %Y %H:%M")
                else:
                    lastdate = ""
                if task.getInterval():
                    interval = str(task.getInterval().days)
                else:
                    interval = ""
                html.append("""<tr><td>%s</td><td>%s day</td><td>%s</td></tr>""" % (task.getObjList()[0].getId(),interval,lastdate))
            html.append("""</table></td></tr>""")
        return "\n".join(html)

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        tasks = self.groupTasks(self.taskList.getTasks())

        html = []
        keys = tasks.keys()
        keys.sort()

        if "Other" in keys:
            other = keys.pop(keys.index("Other"))
            keys.append(other)

        for t in keys:
            html.append(self.getHTMLTasks(t, tasks[t]))
        vars["tasks"] = """<table>""" + "<tr><td><br><br></td></tr>".join(html) + """</table>"""
        return vars


class WPConfirmDelete(WPTaskManagerBase):

    def __init__(self, req, taskId):
        WPTaskManagerBase.__init__(self, req)
        self._taskId = taskId

    def _getTabContent( self, params ):
        wc = wcomponents.WConfirmation()
        msg="""Are you sure you want to delete the following task?<br><ul>%s</ul>
        <font color="red">(note you will permanently remove the task )</font><br>"""%(self._taskId)
        postURL = urlHandlers.UHRemoveTask.getURL()
        return wc.getHTML( msg, postURL, {"taskId":self._taskId} )

class WPOAIPrivateConfig( WPServicesCommon ):

    def __init__( self, rh, addedIP=None ):
        WPServicesCommon.__init__( self, rh )
        self._addedIP = addedIP

    def _getTabContent( self, params ):
        wc = WOAIPrivateConfig()
        params["addedIP"] = self._addedIP
        return wc.getHTML( params )

    def _setActiveTab( self ):
        self._subTabOAIPrivateConfig.setActive()

class WOAIPrivateConfig(wcomponents.WTemplated):

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        vars["ipList"] = minfo.getOAIPrivateHarvesterList()
        vars["removeIcon"] = Config.getInstance().getSystemIconURL( "remove" )
        return vars
