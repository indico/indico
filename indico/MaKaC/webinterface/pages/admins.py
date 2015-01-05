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

from collections import OrderedDict

import datetime
from pytz import timezone
from MaKaC.fossils.user import IAvatarFossil

import os
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.wcomponents as wcomponents
import MaKaC.webinterface.pages.conferences as conferences
from MaKaC.webinterface.pages.conferences import WConfModifBadgePDFOptions
import MaKaC.common.info as info
import MaKaC.webcast as webcast
from indico.core.config import Config
import MaKaC.conference as conference
import MaKaC.user as user
from MaKaC.common import utils, timezoneUtils
from MaKaC.webinterface.common.person_titles import TitlesRegistry
from MaKaC.webinterface.common.timezones import TimezoneRegistry, DisplayTimezoneRegistry
from MaKaC.common.Announcement import getAnnoucementMgrInstance
from MaKaC.webinterface.pages.main import WPMainBase
from MaKaC.webinterface.pages.base import WPDecorated
from MaKaC.common.pendingQueues import PendingSubmitterReminder, PendingManagerReminder, PendingCoordinatorReminder
from MaKaC.authentication import AuthenticatorMgr
from MaKaC.authentication.LDAPAuthentication import LDAPGroup
from MaKaC import roomMapping
from MaKaC import domain
import MaKaC.common.indexes as indexes
import MaKaC.webinterface.personalization as personalization
from cgi import escape
import re
from MaKaC.i18n import _
from MaKaC.plugins import PluginLoader, PluginsHolder

from MaKaC.common.fossilize import fossilize
from MaKaC.fossils.modules import INewsItemFossil
from indico.modules import ModuleHolder
from MaKaC.errors import MaKaCError, NotFoundError
from MaKaC.conference import ConferenceHolder
from MaKaC.webinterface.locators import CategoryWebLocator
from MaKaC.services.implementation.user import UserComparator

from indico.util.i18n import i18nformat
from indico.util.redis import client as redis_client
from indico.util.date_time import timedelta_split
from indico.web.flask.util import url_for


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
                             "tabControl": self._getTabControl() } )

    def _createSideMenu(self):
        self._sideMenu = wcomponents.ManagementSideMenu()

        mainSection = wcomponents.SideMenuSection()

        self._generalSettingsMenuItem = wcomponents.SideMenuItem(_("General settings"),
            urlHandlers.UHAdminArea.getURL())
        mainSection.addItem( self._generalSettingsMenuItem)

        self._usersAndGroupsMenuItem = wcomponents.SideMenuItem(_("Users and Groups"),
            urlHandlers.UHUserManagement.getURL())
        mainSection.addItem( self._usersAndGroupsMenuItem)

        self._domainsMenuItem = wcomponents.SideMenuItem(_("IP Domains"),
            urlHandlers.UHDomains.getURL())
        mainSection.addItem( self._domainsMenuItem)

        self._roomsMenuItem = wcomponents.SideMenuItem(_("Rooms"),
            urlHandlers.UHRoomBookingPluginAdmin.getURL())
        mainSection.addItem( self._roomsMenuItem)

        self._templatesMenuItem = wcomponents.SideMenuItem(_("Layout"),
            urlHandlers.UHAdminLayoutGeneral.getURL())
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

        self._protectionMenuItem = wcomponents.SideMenuItem(_("Protection"),
            urlHandlers.UHAdminsProtection.getURL())
        mainSection.addItem( self._protectionMenuItem)

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

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        vars["title"] = minfo.getTitle()
        vars["organisation"] = minfo.getOrganisation()
        vars['supportEmail'] = Config.getInstance().getSupportEmail()
        vars['publicSupportEmail'] = Config.getInstance().getPublicSupportEmail()
        vars['noReplyEmail'] = Config.getInstance().getNoReplyEmail()
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
        vars["systemIconAdmins"] = Config.getInstance().getSystemIconURL( "admin" )
        iconDisabled = str(Config.getInstance().getSystemIconURL( "disabledSection" ))
        iconEnabled = str(Config.getInstance().getSystemIconURL( "enabledSection" ))
        vars["features"] = ""
        url = urlHandlers.UHAdminSwitchNewsActive.getURL()
        if minfo.isNewsActive():
            icon = iconEnabled
        else:
            icon = iconDisabled
        #vars["features"] += i18nformat("""<br><a href="%s"><img src="%s" border="0" alt="Toggle on/off"> _("News Pages") </a>""") % (str(url), icon)
        #vars["announcement"] = WAnnouncementModif().getHTML( vars )
        vars["features"] += i18nformat("""<div style="margin-bottom: 5px"><a href="%s"><img src="%s" border="0" style="float:left; padding-right: 5px">_("News Pages")</a></div>""") % (str(url), icon)
        url = urlHandlers.UHAdminSwitchDebugActive.getURL()
        if minfo.isDebugActive():
            icon = iconEnabled
        else:
            icon = iconDisabled
        vars["features"] += i18nformat("""<div style="margin-bottom: 5px"><a href="%s"><img src="%s" border="0" style="float:left; padding-right: 5px">_("Debug")</a></div>""") % (str(url), icon)
        vars["administrators"] = fossilize(minfo.getAdminList())
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

class WRBAdminFrame(WAdminFrame):
    pass

class WPAdmins( WPAdminsBase ):

    def _setActiveSideMenuItem(self):
        self._generalSettingsMenuItem.setActive()

    def _getPageContent( self, params ):
        wc = WAdmins()
        pars = { "GeneralInfoModifURL": urlHandlers.UHGeneralInfoModification.getURL() }
        return wc.getHTML( pars )


class WGeneralInfoModification(wcomponents.WTemplated):

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        genInfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        vars["title"] = genInfo.getTitle()
        vars["organisation"] = genInfo.getOrganisation()
        vars["city"] = genInfo.getCity()
        vars["country"] = genInfo.getCountry()
        try:
            selected_tz = genInfo.getTimezone()
        except:
            selected_tz = 'UTC'
        vars["timezone"]=TimezoneRegistry.getShortSelectItemsHTML(selected_tz)
        vars["language"]= genInfo.getLang()
        return vars


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
        newsModule = ModuleHolder().getById("news")

        newslist = fossilize(newsModule.getNewsItemsList(), INewsItemFossil, tz=tz)
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
        module = ModuleHolder().getById("upcoming_events")
        vars["cacheTTL"] = module.getCacheTTL().seconds/60
        vars["numberItems"] = module.getNumberItems()
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
        vars["Favorites"] = fossilize(self._user.getPersonalInfo().getBasket().getUsers().values(), IAvatarFossil)
        vars["rbActive"] = info.HelperMaKaCInfo.getMaKaCInfoInstance().getRoomBookingModuleActive()
        vars["baseURL"]=Config.getInstance().getBaseURL()

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
        self._subTabIPBasedACL = self._tabCtrl.newTab( "ip_based_acl", _("IP Based ACL"), \
                urlHandlers.UHIPBasedACL.getURL() )
        self._subTabHTTPAPI = self._tabCtrl.newTab( "http_api", _("HTTP API"), \
                urlHandlers.UHAdminAPIOptions.getURL() )
        self._subTabHTTPAPI_Options = self._subTabHTTPAPI.newSubTab( "api_options", _("Options"), \
                urlHandlers.UHAdminAPIOptions.getURL() )
        self._subTabHTTPAPI_Keys = self._subTabHTTPAPI.newSubTab( "api_keys", _("API Keys"), \
                urlHandlers.UHAdminAPIKeys.getURL() )
        self._subTabOauth = self._tabCtrl.newTab( "oauth", _("OAuth"), \
                urlHandlers.UHAdminOAuthConsumers.getURL() )
        self._subTabOauth_Consumers = self._subTabOauth.newSubTab( "oauth_consumers", _("Consumers"), \
                urlHandlers.UHAdminOAuthConsumers.getURL() )
        self._subTabOauth_Authorized = self._subTabOauth.newSubTab( "oauth_authorized", _("Authorized"), \
                urlHandlers.UHAdminOAuthAuthorized.getURL() )
        self._subTabAnalytics = self._tabCtrl.newTab( "analytics", _("Analytics"), \
                urlHandlers.UHAnalytics.getURL() )

    def _getPageContent(self, params):
        return wcomponents.WTabControl( self._tabCtrl, self._getAW() ).getHTML( self._getTabContent( params ) )

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
            if wc.getAudience(): # skip webcasts with an audience
                continue
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
            if wc.getAudience(): # skip webcasts with an audience
                continue
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
        vars["adminList"] = wm.getManagers()
        vars["webcastAdmins"] = fossilize(wm.getManagers())
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

        vars["saveWebcastSynchronizationURL"] = urlHandlers.UHWebcastSaveWebcastSynchronizationURL.getURL()
        vars["webcastSynchronizationURL"] = wm.getWebcastSynchronizationURL()

        vars["webcastManualSynchronize"] = urlHandlers.UHWebcastManualSynchronization.getURL()

        return vars


class WPTemplatesCommon( WPAdminsBase ):

    def _setActiveSideMenuItem(self):
        self._templatesMenuItem.setActive()

    def _createTabCtrl( self ):
        self._tabCtrl = wcomponents.TabControl()

        self._subTabGeneral = self._tabCtrl.newTab( "general", _("General Definitions"), \
                urlHandlers.UHAdminLayoutGeneral.getURL() )
        self._subTabStyles = self._tabCtrl.newTab( "styles", _("Timetable Styles"), \
                urlHandlers.UHAdminsStyles.getURL() )
        self._subTabCSSTpls = self._tabCtrl.newTab( "styles", _("Conference Styles"), \
                urlHandlers.UHAdminsConferenceStyles.getURL() )
        self._subTabBadges = self._tabCtrl.newTab( "badges", _("Badges"), \
                urlHandlers.UHBadgeTemplates.getURL() )
        self._subTabPosters = self._tabCtrl.newTab( "posters", _("Posters"), \
                urlHandlers.UHPosterTemplates.getURL() )

    def _getPageContent(self, params):
        return wcomponents.WTabControl( self._tabCtrl, self._getAW() ).getHTML( self._getTabContent( params ) )
        if self._showAdmin:
            return WPAdminsBase._getBody( self, params )
        else:
            return self._getTabContent( params )


class WPBadgeTemplatesBase(WPTemplatesCommon):

    def getCSSFiles(self):
        return WPTemplatesCommon.getCSSFiles(self) + self._asset_env['indico_badges_css'].urls()

    def getJSFiles(self):
        return WPTemplatesCommon.getJSFiles(self) + self._includeJSPackage('badges_js')


class WPAdminLayoutGeneral( WPTemplatesCommon ):

    def _setActiveTab( self ):
        self._subTabGeneral.setActive()

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

        fnames = os.listdir(os.path.join(tplDir, 'chelp'))
        for fname in fnames:
            m = tplRE.match(fname)
            if m:
                templates[m.group(2)] = None

        cssRE = re.compile('Default.([^\.]+)\.css$')

        fnames = os.listdir(Config.getInstance().getCssDir())
        for fname in fnames:
            m = cssRE.match(fname)
            if m:
                templates[m.group(1)] = None

        return templates.keys()

    def _getTabContent(self, params):
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        socialCfg = minfo.getSocialAppConfig()
        wc = WAdminLayoutGeneral()
        pars = {
            "defaultTemplateSet": minfo.getDefaultTemplateSet(),
            "availableTemplates": self.__getAvailableTemplates(),
            "templateSetFormURL": urlHandlers.UHAdminLayoutSaveTemplateSet.getURL(),
            "socialFormURL": urlHandlers.UHAdminLayoutSaveSocial.getURL(),
            "socialActive": socialCfg.get('active', True),
            "facebookData": socialCfg.get('facebook', {})
        }
        return wc.getHTML(pars)


class WAdminLayoutGeneral(wcomponents.WTemplated):
    pass


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
        cssTplsModule=ModuleHolder().getById("cssTpls")
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
        baseTPLPath = styleMgr.getBaseTPLPath()
        baseCSSPath = styleMgr.getBaseCSSPath()
        vars["contextHelpText"] = i18nformat("""- <b>_("TPL files")</b> _("are mandatory and located in"):<br/>%s<br/>- <b>_("CSS files")</b> _("are optional and located in"):<br/>%s<br/>- <b>_("Lines in red")</b> _("indicate missing .tpl or .css files (these styles will not be presented to the users"))""") % (baseTPLPath,baseCSSPath)
        vars["deleteIconURL"] = Config.getInstance().getSystemIconURL("remove")
        return vars

class WPAdminsAddStyle( WPAdminsStyles ):

    def _getTabContent( self, params ):
        wp = WAdminsAddStyle()
        return wp.getHTML(params)

class WAdminsAddStyle(wcomponents.WTemplated):

    def _getAllFiles(self, basePath, extension, excludedDirs=[]):
        collectedFiles = []
        for root, dirs, files in os.walk(basePath):
            for excluded in excludedDirs:
                if excluded in dirs:
                    dirs.remove(excluded)
            for filename in files:
                fullPath = os.path.join(root, filename)
                if os.path.isfile(fullPath) and filename.endswith(extension):
                    collectedFiles.append(os.path.relpath(fullPath, basePath))
        return sorted(collectedFiles)

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        styleMgr = info.HelperMaKaCInfo.getMaKaCInfoInstance().getStyleManager()
        vars["styleMgr"] = styleMgr
        baseTPLPath = styleMgr.getBaseTPLPath()
        baseCSSPath = styleMgr.getBaseCSSPath()
        baseXSLPath = styleMgr.getBaseXSLPath()
        vars["availableTemplates"] = self._getAllFiles(baseTPLPath, '.tpl', excludedDirs=['include'])
        vars["availableStyleSheets"] = self._getAllFiles(baseXSLPath, '.xsl', excludedDirs=['include'])
        vars["availableCSS"] = self._getAllFiles(baseCSSPath, '.css')
        vars["xslContextHelpText"] = r"Lists all XSL files in %s (except special folders named \'include\', which are reserved)" % baseXSLPath
        vars["tplContextHelpText"] = r"Lists all TPL files in %s (except special folders named \'include\', which are reserved)" % baseTPLPath
        vars["cssContextHelpText"] = "Lists all CSS files in %s" % baseCSSPath
        return vars

class WAdminTemplates(wcomponents.WTemplated):

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        return vars

class WPBadgeTemplates(WPBadgeTemplatesBase):
    pageURL = "badgeTemplates.py"

    def __init__(self, rh):
        WPBadgeTemplatesBase.__init__(self, rh)

    def _getTabContent( self, params ):
        wp = WBadgeTemplates(conference.CategoryManager().getDefaultConference())
        return wp.getHTML(params)

    def _setActiveTab( self ):
        self._subTabBadges.setActive()


class WPPosterTemplates(WPBadgeTemplatesBase):
    pageURL = "posterTemplates.py"

    def __init__(self, rh):
        WPBadgeTemplatesBase.__init__(self, rh)

    def _getTabContent( self, params ):
        wp = WPosterTemplates(conference.CategoryManager().getDefaultConference())
        return wp.getHTML(params)

    def _setActiveTab(self):
        self._subTabPosters.setActive()


class WPBadgeTemplateDesign(WPBadgeTemplatesBase):

    def __init__(self, rh, conf, templateId=None, new=False):
        WPBadgeTemplatesBase.__init__(self, rh)
        self._conf = conf
        self.__templateId = templateId
        self.__new = new

    def _setActiveTab(self):
        self._subTabBadges.setActive()

    def _getTabContent(self, params):
        wc = conferences.WConfModifBadgeDesign(self._conf, self.__templateId, self.__new)
        return wc.getHTML()


class WPPosterTemplateDesign(WPBadgeTemplatesBase):

    def __init__(self, rh, conf, templateId=None, new=False):
        WPBadgeTemplatesBase.__init__(self, rh)
        self._conf = conf
        self.__templateId = templateId
        self.__new = new

    def _setActiveTab(self):
        self._subTabPosters.setActive()

    def _getTabContent(self, params):
        wc = conferences.WConfModifPosterDesign(self._conf, self.__templateId, self.__new)
        return wc.getHTML()


class WBadgePosterTemplatingBase(wcomponents.WTemplated):

    DEF_TEMPLATE_BADGE = None

    def __init__(self, conference, user=None):
        wcomponents.WTemplated.__init__(self)
        self._conf = conference
        self._user = user

    def getVars(self):
        uh = urlHandlers
        vars = wcomponents.WTemplated.getVars(self)
        vars['NewDefaultTemplateURL'] = str(self.DEF_TEMPLATE_BADGE.getURL(self._conf,
                                                                             self._conf.getBadgeTemplateManager().getNewTemplateId(), new=True))

        vars['templateList'] = self._getTemplates()
        self._addExtras(vars)

        return vars

    def _getConfTemplates(self):
        """
        To be overridden in inheriting class.
        """
        pass

    def _getTemplates(self):
        templates = []
        rawTemplates = self._getConfTemplates()
        rawTemplates.sort(lambda x, y: cmp(x[1].getName(), y[1].getName()))

        for templateId, template in rawTemplates:
            templates.append(self._processTemplate(templateId, template))

        return templates

    def _addExtras(self, vars):
        """
        To be overridden in inheriting class, adds specific entries
        into the dictionary vars which the child implementation may require.
        """
        pass

    def _processTemplate(self, templateId, template):
        """
        To be overridden in inheriting class, takes the template and its
        ID, the child then processes the data into the format it expects later.
        """
        pass


class WBadgeTemplates(WBadgePosterTemplatingBase):

    DEF_TEMPLATE_BADGE = urlHandlers.UHModifDefTemplateBadge

    def _addExtras(self, vars):
        vars['PDFOptions'] = WConfModifBadgePDFOptions(self._conf,
                                                       showKeepValues=False,
                                                       showTip=False).getHTML()

    def _getConfTemplates(self):
        return self._conf.getBadgeTemplateManager().getTemplates().items()

    def _processTemplate(self, templateId, template):
        uh = urlHandlers

        data = {
            'name': template.getName(),
            'urlEdit': str(uh.UHConfModifBadgeDesign.getURL(self._conf, templateId)),
            'urlDelete': str(uh.UHConfModifBadgePrinting.getURL(self._conf, deleteTemplateId=templateId))
        }

        return data


class WPosterTemplates(WBadgePosterTemplatingBase):

    DEF_TEMPLATE_BADGE = urlHandlers.UHModifDefTemplatePoster

    def _getConfTemplates(self):
        return self._conf.getPosterTemplateManager().getTemplates().items()

    def _processTemplate(self, templateId, template):
        uh = urlHandlers

        data = {
            'name': template.getName(),
            'urlEdit': str(uh.UHConfModifPosterDesign.getURL(self._conf, templateId)),
            'urlDelete': str(uh.UHConfModifPosterPrinting.getURL(self._conf, deleteTemplateId=templateId)),
            'urlCopy': str(uh.UHConfModifPosterPrinting.getURL(self._conf, copyTemplateId=templateId))
        }

        return data


class WPUsersAndGroupsCommon(WPAdminsBase):

    def _setActiveSideMenuItem(self):
        self._usersAndGroupsMenuItem.setActive()

    def _createTabCtrl(self):
        self._tabCtrl = wcomponents.TabControl()

        self._subTabMain = self._tabCtrl.newTab("main", _("Main"), \
                urlHandlers.UHUserManagement.getURL())
        self._subTabUsers = self._tabCtrl.newTab("users", _("Manage Users"), \
                urlHandlers.UHUsers.getURL())
        self._subTabGroups = self._tabCtrl.newTab("groups", _("Manage Groups"), \
                urlHandlers.UHGroups.getURL())

    def _getPageContent(self, params):
        return wcomponents.WTabControl(self._tabCtrl, self._getAW()).getHTML(self._getTabContent(params))


class WUserManagement(wcomponents.WTemplated):

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        iconDisabled = str(Config.getInstance().getSystemIconURL("disabledSection"))
        iconEnabled = str(Config.getInstance().getSystemIconURL("enabledSection"))
        vars["accountCreationData"] = ""
        url = urlHandlers.UHUserManagementSwitchAuthorisedAccountCreation.getURL()

        if minfo.getAuthorisedAccountCreation():
            icon = iconEnabled
        else:
            icon = iconDisabled

        vars["accountCreationData"] += i18nformat("""<a href="%s"><img src="%s" border="0"> _("Public Account Creation")</a>""") % (str(url), icon)
        url = urlHandlers.UHUserManagementSwitchNotifyAccountCreation.getURL()

        if minfo.getNotifyAccountCreation():
            icon = iconEnabled
        else:
            icon = iconDisabled

        vars["accountCreationData"] += i18nformat("""<br><a href="%s"><img src="%s" border="0"> _("Notify Account Creation by Email")</a>""") % (str(url), icon)
        url = urlHandlers.UHUserManagementSwitchModerateAccountCreation.getURL()

        if minfo.getModerateAccountCreation():
            icon = iconEnabled
        else:
            icon = iconDisabled

        vars["accountCreationData"] += i18nformat("""<br><a href="%s"><img src="%s" border="0"> _("Moderate Account Creation")</a>""") % (str(url), icon)

        return vars


class WPUserManagement(WPUsersAndGroupsCommon):
    pageURL = "userManagement.py"

    def __init__(self, rh, params):
        WPUsersAndGroupsCommon.__init__(self, rh)
        self._params = params

    def _getTabContent(self, params):
        wp = WUserManagement()
        return wp.getHTML(self._params)

    def _setActiveTab(self):
        self._subTabMain.setActive()


class WPUserCommon(WPUsersAndGroupsCommon):

    def _setActiveTab(self):
        self._subTabUsers.setActive()


class WBrowseUsers(wcomponents.WTemplated):

    def __init__(self, letter=None, browseIndex="surName"):
        self._letter = letter
        self._browseIndex = browseIndex

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
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
                vars["browseIndex"] += """\n<span class="nav_border"><a class="nav_link" href='' onClick="document.browseForm.letter.value='%s';document.browseForm.submit();return false;">%s</a></span> """ % (escape(letter, True), letter)

        vars["browseResult"] = ""

        if self._letter is not None:
            ah = user.AvatarHolder()
            if self._letter != "all":
                res = ah.matchFirstLetter(self._browseIndex,
                                          self._letter,
                                          onlyActivated=False,
                                          searchInAuthenticators=False)
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

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        color = "white"
        ul = []
        vars["userList"] = ""
        ul.append( i18nformat("""
                        <tr>
                            <td bgcolor="white" style="color:black" align="center"><b>%s  _("users")</b></td>
                        </tr>
                        """) % len(self._userList))

        for u in self._userList:
            if color == "white":
                color = "#ececec"
            else:
                color = "white"
            organisation = ""
            if u.getOrganisation() != "":
                organisation = " (%s)" % u.getOrganisation()
            email = ""
            if u.getEmail() != "":
                email = " (%s)" % u.getEmail()
            url = vars["userDetailsURLGen"](u)
            name = u.getFullName()
            if name == "":
                name = "no name"
            ul.append("""<tr>
                            <td bgcolor="%s"><a href="%s">%s</a> %s %s</td>
                         </tr>""" % (color, url, self.htmlText(name) , self.htmlText(email),self.htmlText(organisation)) )

        if ul:
            vars["userList"] += "".join(ul)
        else:
            vars["userList"] += i18nformat("""<tr>
                            <td><br><span class="blacktext">&nbsp;&nbsp;&nbsp; _("No users returned")</span></td></tr>""")

        return vars


class WUserList(wcomponents.WTemplated):

    def __init__(self, criteria, onlyActivated=True):
        self._criteria = criteria
        self._onlyActivated = onlyActivated

    def _performSearch(self, criteria):
        ah = user.AvatarHolder()

        if  criteria["surName"] == "*" or \
            criteria["name"] == "*" or \
            criteria["email"] == "*" or \
            criteria["organisation"] == "*":
            res = ah.getValuesToList()
        else:
            res = ah.match(criteria, onlyActivated=self._onlyActivated, searchInAuthenticators=False)
        res.sort(utils.sortUsersByName)

        return res

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["nbUsers"] = indexes.IndexesHolder().getById("email").getLength()
        vars["createUserURL"] = urlHandlers.UHUserCreation.getURL()
        vars["mergeUsersURL"] = urlHandlers.UHUserMerge.getURL()
        vars["searchUsersURL"] = urlHandlers.UHUsers.getURL()
        vars["browseUsersURL"] = urlHandlers.UHUsers.getURL()
        vars["browseOptions"] = ""
        options = {"surName": _("by last name"),
                    "name": _("by first name"),
                    "organisation": _("by affiliation"),
                    "email": _("by email address"),
                    "status": _("by status")}

        for key in options.keys():
            if key == vars.get("browseIndex", "surName"):
                vars["browseOptions"] += """<option value="%s" selected> %s""" % (key, options[key])
            else:
                vars["browseOptions"] += """<option value="%s"> %s""" % (key, options[key])

        vars["browseUsers"] = WBrowseUsers(vars.get("letter", None), vars.get("browseIndex", "surName")).getHTML(vars)
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

    def _getTabContent(self, params):
        criteria = {}
        onlyActivated = False
        if filter(lambda x: self._params[x], self._params):
            criteria["surName"] = self._params.get("sSurName", "")
            criteria["name"] = self._params.get("sName", "")
            criteria["email"] = self._params.get("sEmail", "")
            criteria["organisation"] = self._params.get("sOrganisation", "")
            onlyActivated = "onlyActivated" in self._params
        comp = WUserList(criteria, onlyActivated=onlyActivated)
        self._params["userDetailsURLGen"] = urlHandlers.UHUserDetails.getURL

        return comp.getHTML(self._params)


class WPUserCreation(WPUserCommon):

    def __init__(self, rh, params, participation=None):
        WPUserCommon.__init__(self, rh)
        self._params = params
        self._participation = participation

    def _getTabContent(self, params):
        pars = self._params
        p = wcomponents.WUserRegistration()
        pars["defaultLang"] = pars.get("lang", "")
        pars["defaultTZ"] = pars.get("timezone", "")
        pars["defaultTZMode"] = pars.get("displayTZMode", "")
        pars["postURL"] = urlHandlers.UHUserCreation.getURL()

        if pars["msg"] != "":
            pars["msg"] = "<table bgcolor=\"gray\"><tr><td bgcolor=\"white\">\n<font size=\"+1\" color=\"red\"><b>%s</b></font>\n</td></tr></table>" % pars["msg"]

        if self._participation is not None:
            pars["email"] = self._participation.getEmail()
            pars["name"] = self._participation.getFirstName()
            pars["surName"] = self._participation.getFamilyName()
            pars["title"] = self._participation.getTitle()
            pars["organisation"] = self._participation.getAffiliation()
            pars["address"] = self._participation.getAddress()
            pars["telephone"] = self._participation.getPhone()
            pars["fax"] = self._participation.getFax()

        return p.getHTML(pars)


class WPUserCreationNonAdmin(WPUserCreation):

    def _getNavigationDrawer(self):
        pass

    def _getBody(self, params):
        return WPUserCreation._getTabContent(self, params)


class WPUserCreated(WPUserCommon):

    def __init__(self, rh, av):
        WPUserCommon.__init__(self, rh)
        self._av = av

    def _getTabContent(self, params):
        p = wcomponents.WUserCreated(self._av)
        pars = {"signInURL": urlHandlers.UHSignIn.getURL()}
        return p.getHTML(pars)


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
        authTagList = [i.getId() for i in AuthenticatorMgr().getList()]

        vars["identityItems"] = filter(lambda x: x.getAuthenticatorTag() in authTagList, self._avatar.getIdentityList())
        vars["avatar"] = self._avatar
        vars["locator"] = self._avatar.getLocator().getWebForm()
        vars["accountManagementActive"] = 'Local' in authTagList
        return vars

class WUserDashboard(wcomponents.WTemplated):

    def __init__(self, av, aw):
        self._avatar = av
        self._aw = aw

    def getVars(self):
        html_vars = wcomponents.WTemplated.getVars(self)
        user = self._avatar

        now = datetime.datetime.now()

        tzUtil = timezoneUtils.DisplayTZ(self._aw)
        tz = timezone(tzUtil.getDisplayTZ())

        html_vars["timezone"] = tz

        # split offset in hours and minutes
        hours, minutes, __ = timedelta_split(tz.utcoffset(now))

        html_vars["offset"] = '{0:+02d}:{1:02d}'.format(hours, minutes)
        html_vars["categories"] = user.getRelatedCategories()
        html_vars["suggested_categories"] = user.getSuggestedCategories()
        html_vars["redisEnabled"] = bool(redis_client)

        return html_vars

class WUserBaskets(wcomponents.WTemplated):

    def __init__(self, av):
        self._avatar = av

    def getHTML(self, params):
        params['user'] = self._avatar
        params['favoriteCategs'] = [dict(id=c.getId(), title=c.getTitle()) for c in
                                    self._avatar.getLinkTo('category', 'favorite')]
        users = self._avatar.getPersonalInfo().getBasket().getUsers().values()
        fossilizedUsers = sorted(fossilize(users), cmp=UserComparator.cmpUsers)
        params['favoriteUsers'] = fossilizedUsers
        return wcomponents.WTemplated.getHTML( self, params )


class WUserPreferences(wcomponents.WTemplated):

    def __init__(self, av):
        self._avatar = av

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        vars["showPastEvents"] = self._avatar.getPersonalInfo().getShowPastEvents()
        vars["pluginUserPreferences"] = "".join(self._notify('userPreferences', self._avatar.getId()))
        vars["userId"] = self._avatar.getId()
        vars["defaultLanguage"] =  self._avatar.getLang()
        vars["defaultTimezone"] = self._avatar.getTimezone()
        vars["defaultDisplayTimeZone"] =  self._avatar.getDisplayTZMode() or "MyTimezone"
        return vars


class WUserDetails(wcomponents.WTemplated):

    def __init__(self, av):
        self._avatar = av

    def getHTML( self, currentUser, params ):
        self._currentUser = currentUser
        return wcomponents.WTemplated.getHTML( self, params )

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        u = self._avatar
        vars["userId"] = u.getId()
        vars["surName"] = self.htmlText(u.getSurName())
        vars["name"] = self.htmlText(u.getName())
        vars["organisation"] = self.htmlText(u.getOrganisations()[0])
        titleDic = {}
        for title in TitlesRegistry().getList():
            titleDic[title] = title
        vars["titleList"] = titleDic
        vars["title"] = self.htmlText(u.getTitle())
        vars["address"] = self.htmlText(u.getAddresses()[0])
        vars["email"] = self.getEmailsHTML(u)
        vars["onlyEmail"] = self.htmlText(u.getEmail())
        vars["secEmails"] = ", ".join(u.getSecondaryEmails())
        vars["lang"] = self.htmlText(u.getLang())
        vars["telephon"] = self.htmlText(u.getTelephones()[0])
        vars["fax"] = self.htmlText(u.getFaxes()[0])
        vars["locator"] = self.htmlText(self._avatar.getLocator().getWebForm())
        vars["identities"] = ""
        vars["status"] = self._avatar.getStatus()
        vars["unlockedFields"] = self._avatar.getNotSyncedFields()
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        al = minfo.getAdminList()
        vars["currentUserIsAdmin"] = self._currentUser in al.getList()
        vars["user"] = self._avatar
        if self._currentUser == self._avatar or \
              self._currentUser in al.getList() or \
              len(self._avatar.getIdentityList())==0:
            vars["identities"] = WUserIdentitiesTable( self._avatar ).getHTML( { "addIdentityURL": vars["addIdentityURL"], "removeIdentityURL": vars["removeIdentityURL"] })

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

        self._tabRights = self._tabCtrl.newTab("dashboard", _("Dashboard"),
                               urlHandlers.UHUserDashboard.getURL(self._avatar))

        self._tabDetails = self._tabCtrl.newTab( "details", _("Account Details"), \
                urlHandlers.UHUserDetails.getURL(self._avatar) )

        """
            This tab is not needed any more. Currently only has information about
            showing or hiding advacned tabs. These advanced tabs has been turned into
            a side menu. Maybe the tab is needed in the future.
        """
        self._tabPreferences = self._tabCtrl.newTab( "preferences", _("Preferences"), \
                urlHandlers.UHUserPreferences.getURL(self._avatar) )

        self._tabBaskets = self._tabCtrl.newTab( "baskets", _("Favorites"), \
                urlHandlers.UHUserBaskets.getURL(self._avatar) )

        self._tabAPI = self._tabCtrl.newTab( "api", _("HTTP API"), \
                urlHandlers.UHUserAPI.getURL(self._avatar) )

        self._tabThirdPartyAuth = self._tabCtrl.newTab("auth_control", _("Authorized Apps"),
                urlHandlers.UHOAuthUserThirdPartyAuth.getURL(self._avatar))

    def _getNavigationDrawer(self):
        return wcomponents.WSimpleNavigationDrawer(_("My Profile"))


class WPUserDashboard(WPPersonalArea):

    def getCSSFiles(self):
        return WPPersonalArea.getCSSFiles(self) + self._asset_env['dashboard_sass'].urls()

    def _getTabContent(self, params):
        c = WUserDashboard(self._avatar, self._getAW())
        return c.getHTML(params)

    def _setActiveTab(self):
        self._tabRights.setActive()


class WPUserDetails( WPPersonalArea ):

    def _getTabContent( self, params ):
        c = WUserDetails( self._avatar )
        params["addIdentityURL"] = urlHandlers.UHUserIdentityCreation.getURL( self._avatar )
        params["removeIdentityURL"] = urlHandlers.UHUserRemoveIdentity.getURL( self._avatar )
        params["activeURL"] = urlHandlers.UHUserActive.getURL( self._avatar )
        params["disableURL"] = urlHandlers.UHUserDisable.getURL( self._avatar )
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


class WIdentityModification(wcomponents.WTemplated):

    def __init__(self, av, identity=None):
        self._avatar = av
        self._identity = identity

    def getVars(self):
        wvars = wcomponents.WTemplated.getVars(self)

        wvars["avatarId"] = self._avatar.getId()
        if self._identity:
            wvars["actionLabel"] = _("Change password")
            wvars["login"] = self._identity.getId()
        else:
            wvars["actionLabel"] = _("New Identity")
            wvars["login"] = wvars.get("login", self._avatar.getEmail())

        auths = [{"id": auth.getId(), "name": auth.getName()} for auth in AuthenticatorMgr().getList()]
        wvars["systemList"] = auths
        return wvars


class WPIdentityCreation(WPUserDetails):

    def __init__(self, rh, av, params):
        WPUserDetails.__init__(self, rh)
        self._avatar = av
        self._params = params

    def _getTabContent(self, params):
        c = WIdentityModification(self._avatar)
        self._params["postURL"] = urlHandlers.UHUserIdentityCreation.getURL()
        self._params["isDisabled"] = False
        return c.getHTML(self._params)


class WPIdentityChangePassword(WPUserDetails):

    def __init__(self, rh, av, params):
        WPUserDetails.__init__(self, rh)
        self._avatar = av
        self._params = params

    def _getTabContent(self, params):
        identity = self._avatar.getIdentityById(self._params["login"], "Local")
        c = WIdentityModification(self._avatar, identity)
        self._params["postURL"] = urlHandlers.UHUserIdentityChangePassword.getURL()
        self._params["isDisabled"] = True
        return c.getHTML(self._params)


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
        ul.append( i18nformat("""
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
            if g.isObsolete():
                obsolete = 'obsolete'
            else:
                obsolete = ''
            ul.append("""<tr>
                            <td bgcolor="%s"><a href="%s">%s</a></td>
                            <td bgcolor="%s" align="center">%s</td>
                         </tr>"""%(color, url, self.htmlText(g.getName()), color, obsolete))
        if ul:
            vars["groupList"] += "".join( ul )
        else:
            vars["groupList"] += i18nformat("""<tr>
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
                res = gh.matchFirstLetter(self._letter, searchInAuthenticators=False)
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
        res = gh.match(criteria)
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
        vars["obsolete"] = False

    def __setGroupVars( self, group, vars ):
        vars["Wtitle"] = _("Modifying group basic data")
        vars["name"] = group.getName()
        vars["email"] = group.getEmail()
        vars["description"] = group.getDescription()
        vars["obsolete"] = group.isObsolete()

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["allowModif"] = True
        if self._group == None:
            self.__setNewGroupVars( vars )
            vars["locator"] = ""
        else:
            self.__setGroupVars( self._group, vars )
            vars["locator"] = self._group.getLocator().getWebForm()
            if isinstance(self._group, LDAPGroup):
                vars["allowModif"] = False
        return vars


class WPGroupCreation(WPGroupCommon):

    def _getTabContent( self, params ):
        comp = WGroupModification()
        pars = {"postURL": urlHandlers.UHGroupPerformRegistration.getURL(), \
                "backURL": urlHandlers.UHGroups.getURL() }
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
        vars["name"] = self._group.getName()
        vars["description"] = self._group.getDescription()
        vars["email"] = self._group.getEmail()
        vars["locator"] = self._group.getLocator().getWebForm()
        vars["obsolete"] = self._group.isObsolete()
        vars["groupId"] = self._group.getId()
        vars["members"] = fossilize(self._group.getMemberList())
        vars["groupExists"] = self._group.exists()
        return vars


class WPGroupDetails( WPGroupBase ):

    def _getTabContent( self, params ):
        c = WGroupDetails( self._group )
        pars = { \
    "modifyURL": urlHandlers.UHGroupModification.getURL( self._group ),\
    "detailsURLGen": urlHandlers.UHPrincipalDetails.getURL, \
    "backURL": urlHandlers.UHGroups.getURL() }
        return c.getHTML( pars )


class WPGroupModificationBase( WPGroupBase ):
    pass


class WPGroupModification( WPGroupModificationBase ):

    def _getTabContent( self, params ):
        comp = WGroupModification( self._group )
        params["postURL"] = urlHandlers.UHGroupPerformModification.getURL(self._group)
        params["backURL"] = urlHandlers.UHGroupDetails.getURL( self._group )
        return comp.getHTML( params )


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
        vars['prinId'] = self.prin.getId() if self.prin else ""
        return vars


class WPRoomsBase( WPAdminsBase ):
    def _setActiveSideMenuItem(self):
        self._roomsMenuItem.setActive()

    def _createTabCtrl( self ):
        self._tabCtrl = wcomponents.TabControl()

        if self._rh._getUser().isAdmin():
            self._subTabRoomBooking = self._tabCtrl.newTab( "booking", _("Room Booking"), \
                    urlHandlers.UHRoomBookingPluginAdmin.getURL() )
            self._subTabMain = self._subTabRoomBooking.newSubTab( "main", _("Main"), \
                    urlHandlers.UHRoomBookingPluginAdmin.getURL() )
        else:
            self._subTabRoomBooking = self._tabCtrl.newTab( "booking", _("Room Booking"), \
                    urlHandlers.UHRoomBookingAdmin.getURL() )
        self._subTabConfig = self._subTabRoomBooking.newSubTab( "configuration", _("Configuration"), \
                urlHandlers.UHRoomBookingAdmin.getURL() )
        self._subTabRoomMappers = self._tabCtrl.newTab( "mappers", _("Room Mappers"), \
                urlHandlers.UHRoomMappers.getURL() )

    def _getNavigationDrawer(self):
        if self._rh._getUser().isAdmin():
            return wcomponents.WSimpleNavigationDrawer(_("Room Booking Admin"), urlHandlers.UHRoomBookingPluginAdmin.getURL, bgColor="white")
        return wcomponents.WSimpleNavigationDrawer(_("Room Booking Admin"), urlHandlers.UHRoomBookingAdmin.getURL, bgColor="white")

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
                vars["roomMappers"] += i18nformat("""<tr>
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
        vars["regexps"] = self._roomMapper.getRegularExpressions()
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
        pars = {"postURL": urlHandlers.UHRoomMapperPerformModification.getURL(self._domain)}
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
        vars["browseIndex"] = i18nformat("""
        <span class="nav_border"><a href='' class="nav_link" onClick="document.browseForm.letter.disable=1;document.browseForm.submit();return false;">_("clear")</a></span>""")
        if self._letter == "all":
            vars["browseIndex"] += """
        [all] """
        else:
            vars["browseIndex"] += i18nformat("""
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
                        </tr>"""%(color, url, dom.getName() or _("no name") ) )
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
        pars = {
            'postURL': urlHandlers.UHDomainPerformModification.getURL(self._domain)
        }
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

    def _getSiteArea(self):
        return 'Room Booking Administration'

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


class WPRoomBookingAdmin(WPRoomBookingPluginAdminBase):

    def __init__(self, rh):
        self._rh = rh
        WPRoomBookingPluginAdminBase.__init__(self, rh)

    def _setActiveTab(self):
        self._subTabConfig.setActive()

    def _getTabContent(self, params):
        wc = wcomponents.WRoomBookingAdmin(self._rh)
        return wc.getHTML(params)


class WPRoomBookingAdminLocation(WPRoomBookingPluginAdminBase):

    def __init__(self, rh, location, actionSucceeded=False):
        self._rh = rh
        self._location = location
        self._actionSucceeded = actionSucceeded
        WPRoomBookingPluginAdminBase.__init__(self, rh)

    def _setActiveTab(self):
        self._subTabConfig.setActive()

    def _getTabContent(self, params):
        wc = wcomponents.WRoomBookingAdminLocation(self._rh, self._location)
        params['actionSucceeded'] = self._actionSucceeded
        return wc.getHTML(params)


class WPAdminsSystemBase(WPAdminsBase):
    def __init__(self, rh):
        WPAdminsBase.__init__(self, rh)

    def _setActiveSideMenuItem(self):
        self._systemMenuItem.setActive()

    def _createTabCtrl(self):
        self._tabCtrl = wcomponents.TabControl()

        self._subTabConfiguration = self._tabCtrl.newTab("configuration", _("Configuration"), \
                urlHandlers.UHAdminsSystem.getURL())
        self._subTabTaskManager = self._tabCtrl.newTab("tasks", _("Task Manager"), \
                urlHandlers.UHTaskManager.getURL())
        self._subTabMaintenance = self._tabCtrl.newTab("maintenance", _("Maintenance"), \
                urlHandlers.UHMaintenance.getURL())

    def _getPageContent(self, params):
        return wcomponents.WTabControl(self._tabCtrl, self._getAW()).getHTML(self._getTabContent(params))


class WPAdminsSystem(WPAdminsSystemBase):

    def _setActiveTab(self):
        self._subTabConfiguration.setActive()

    def _getTabContent(self, params):
        wc = WAdminsSystem()
        return wc.getHTML(params)


class WAdminsSystem(wcomponents.WTemplated):

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        vars["minfo"] = minfo
        vars["ModifURL"] = urlHandlers.UHAdminsSystemModif.getURL()
        return vars


class WPAdminsSystemModif(WPAdminsSystemBase):

    def _getTabContent(self, params):
        wc = WAdminsSystemModif()
        return wc.getHTML(params)


class WAdminsSystemModif(wcomponents.WTemplated):

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        vars["minfo"] = minfo
        vars["postURL"] = urlHandlers.UHAdminsSystemModif.getURL()
        return vars


class WPMaintenanceBase(WPAdminsSystemBase):

    def __init__(self, rh):
        WPAdminsBase.__init__(self, rh)

    def _setActiveTab(self):
        self._subTabMaintenance.setActive()


class WPMaintenance(WPMaintenanceBase):

    def __init__(self, rh, s, dbSize):
        WPMaintenanceBase.__init__(self, rh)
        self._stat = s
        self._dbSize = dbSize

    def _getTabContent(self, params):
        wc = WAdminMaintenance()
        pars = { "cleanupURL": urlHandlers.UHMaintenanceTmpCleanup.getURL(), \
                 "tempSize": self._stat[0], \
                 "nFiles": "%s files" % self._stat[1], \
                 "nDirs": "%s folders" % self._stat[2], \
                 "packURL": urlHandlers.UHMaintenancePack.getURL(), \
                 "dbSize": self._dbSize}
        return wc.getHTML(pars)


class WAdminMaintenance(wcomponents.WTemplated):

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        return vars


class WPMaintenanceTmpCleanup(WPMaintenanceBase):

    def __init__(self, rh):
        WPMaintenanceBase.__init__(self, rh)

    def _getTabContent(self, params):
        msg = """Are you sure you want to delete the temporary directory
        (note that all the files in that directory will be deleted)?"""
        wc = wcomponents.WConfirmation()
        url = urlHandlers.UHMaintenancePerformTmpCleanup.getURL()
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
                """ % wc.getHTML(msg, url, {})


class WPMaintenancePack(WPMaintenanceBase):

    def __init__(self, rh):
        WPMaintenanceBase.__init__(self, rh)

    def _getTabContent(self, params):
        wc = wcomponents.WConfirmation()
        msg = """Are you sure you want to pack the database?"""
        url = urlHandlers.UHMaintenancePerformPack.getURL()
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
                """ % wc.getHTML(msg, url, {})


class WPTaskManagerBase(WPAdminsSystemBase):

    def __init__(self, rh):
        WPAdminsBase.__init__(self, rh)

    def _setActiveTab(self):
        self._subTabTaskManager.setActive()


class WPTaskManager(WPTaskManagerBase):

    def _getTabContent(self, params):
        wc = WTaskManager()

        pars = {}
        return wc.getHTML(pars)


class WTaskManager(wcomponents.WTemplated):
    pass


class WPIPBasedACL( WPServicesCommon ):

    def __init__( self, rh ):
        WPServicesCommon.__init__( self, rh )

    def _getTabContent(self, params):
        wc = WIPBasedACL()
        return wc.getHTML(params)

    def _setActiveTab(self):
        self._subTabIPBasedACL.setActive()


class WIPBasedACL(wcomponents.WTemplated):

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        vars["ipList"] = minfo.getIPBasedACLMgr().get_full_access_acl()
        vars["removeIcon"] = Config.getInstance().getSystemIconURL("remove")
        return vars


class WPAnalytics(WPServicesCommon):

    def __init__(self, rh):
        WPServicesCommon.__init__(self, rh)

    def _getTabContent(self, params):
        wc = WAnalytics()
        return wc.getHTML(params)

    def _setActiveTab(self):
        self._subTabAnalytics.setActive()


class WAnalytics(wcomponents.WTemplated):

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        vars["analyticsActive"] = minfo.isAnalyticsActive()
        vars["analyticsCode"] = minfo.getAnalyticsCode()
        vars["analyticsCodeLocation"] = minfo.getAnalyticsCodeLocation()
        vars["analyticsFormURL"] = urlHandlers.UHSaveAnalytics.getURL()
        return vars


class WPAdminProtection(WPAdminsBase):

    def _setActiveSideMenuItem(self):
        self._protectionMenuItem.setActive()

    def _getPageContent(self, params):
        wc = WAdminProtection()
        return wc.getHTML()


class WAdminProtection(wcomponents.WTemplated):

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        vars["protectionDisclaimerProtected"] = minfo.getProtectionDisclaimerProtected()
        vars["protectionDisclaimerRestricted"] = minfo.getProtectionDisclaimerRestricted()
        return vars


class WRedirect(wcomponents.WTemplated):
    def __init__(self, title, message, delay, url, link_text):
        self.title = title
        self.message = message
        self.delay = delay
        self.link_text = link_text
        self.url = url

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars['title'] = self.title
        vars['message'] = self.message
        vars['delay'] = self.delay
        vars['url'] = self.url
        vars['link_text'] = self.link_text
        return vars


class WPRedirect(WPDecorated):
    def __init__(self, rh, title, message, delay, url, link_text=None,):
        WPDecorated.__init__(self, rh)
        self.content = WRedirect(title, message, delay, url, link_text if link_text else url)

    def _getBody(self, params):
        return self.content.getHTML(params)
