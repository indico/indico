# -*- coding: utf-8 -*-
##
## $Id: collaboration.py,v 1.20 2009/05/27 08:52:22 jose Exp $
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

from datetime import timedelta
from MaKaC.webinterface import wcomponents, urlHandlers
from MaKaC.webinterface.pages.conferences import WPConferenceModifBase, \
    WPConferenceDefaultDisplayBase
from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools
from MaKaC.common.timezoneUtils import nowutc, setAdjustedDate, DisplayTZ
from MaKaC.common.utils import formatDateTime, parseDateTime
from MaKaC.common.timezoneUtils import getAdjustedDate
from MaKaC.i18n import _
from MaKaC.common.PickleJar import DictPickler
from MaKaC.webinterface.rh.admins import RCAdmin
from MaKaC.webinterface.pages.main import WPMainBase
from MaKaC.common.indexes import IndexesHolder
from MaKaC.plugins.Collaboration.base import CollaborationException

################################################### Server Wide pages #########################################

class WPAdminCollaboration(WPMainBase):

    def __init__(self, rh, queryParams):
        WPMainBase.__init__(self, rh)
        self._queryParams = queryParams
        self._pluginsWithIndexing = CollaborationTools.pluginsWithIndexing() # list of names
        self._buildExtraJS()

    def getJSFiles(self):
        return WPMainBase.getJSFiles(self) + self._includeJSPackage('Collaboration')

    def _getHeader(self):
        wc = wcomponents.WHeader(self._getAW())
        return wc.getHTML({ "subArea": _("Video Services Administration"), \
                             "loginURL": self._escapeChars(str(self.getLoginURL())), \
                             "logoutURL": self._escapeChars(str(self.getLogoutURL())), \
                             "tabControl": self._getTabControl(), \
                             "loginAsURL": self.getLoginAsURL() })

    def _getBody(self, params):
        return WAdminCollaboration(self._queryParams, self._pluginsWithIndexing).getHTML()

    def _getNavigationDrawer(self):
        return wcomponents.WSimpleNavigationDrawer("Video Services Admin", urlHandlers.UHAdminCollaboration.getURL)

    def _buildExtraJS(self):
        for pluginName in self._pluginsWithIndexing:
            extraJS = CollaborationTools.getExtraJS(pluginName, None)
            if extraJS:
                self.addExtraJS(extraJS)

class WAdminCollaboration(wcomponents.WTemplated):

    def __init__(self, queryParams, pluginsWithIndexing):
        wcomponents.WTemplated.__init__(self)
        self._queryParams = queryParams
        self._pluginsWithIndexing = pluginsWithIndexing # list of names

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)

        #dictionary where the keys are names of false "indexes" for the user, and the values are IndexInformation objects
        vars["Indexes"] = CollaborationTools.getCollaborationPluginType().getOption("pluginsPerIndex").getValue()
        vars["InitialIndex"] = self._queryParams["indexName"]
        vars["InitialViewBy"] = self._queryParams["viewBy"]
        vars["InitialOrderBy"] = self._queryParams["orderBy"]
        vars["InitialOnlyPending"] = self._queryParams["onlyPending"]
        vars["InitialConferenceId"] = self._queryParams["conferenceId"]
        vars["InitialCategoryId"] = self._queryParams["categoryId"]
        vars["InitialSinceDate"] = self._queryParams["sinceDate"]
        vars["InitialToDate"] = self._queryParams["toDate"]
        vars["InitialFromDays"] = self._queryParams["fromDays"]
        vars["InitialToDays"] = self._queryParams["toDays"]
        vars["InitialFromTitle"] = self._queryParams["fromTitle"]
        vars["InitialToTitle"] = self._queryParams["toTitle"]
        vars["InitialResultsPerPage"] = self._queryParams["resultsPerPage"]
        vars["InitialPage"] = self._queryParams["page"]
        vars["BaseURL"] = urlHandlers.UHAdminCollaboration.getURL()

        if self._queryParams["queryOnLoad"]:
            ci = IndexesHolder().getById('collaboration')
            tz = self._rh._getUser().getTimezone()
            #####
            minKey = None
            maxKey = None
            if self._queryParams['sinceDate']:
                minKey = setAdjustedDate(parseDateTime(self._queryParams['sinceDate'].strip()), tz = self._tz)
            if self._queryParams['toDate']:
                maxKey = setAdjustedDate(parseDateTime(self._queryParams['toDate'].strip()), tz = self._tz)
            if self._queryParams['fromTitle']:
                minKey = self._queryParams['fromTitle'].strip()
            if self._queryParams['toTitle']:
                maxKey = self._queryParams['toTitle'].strip()
            if self._queryParams['fromDays']:
                try:
                    fromDays = int(self._queryParams['fromDays'])
                except ValueError, e:
                    raise CollaborationException(_("Parameter 'fromDays' is not an integer"), inner = e)
                minKey = nowutc() - timedelta(days = fromDays)
            if self._queryParams['toDays']:
                try:
                    toDays = int(self._queryParams['toDays'])
                except ValueError, e:
                    raise CollaborationException(_("Parameter 'toDays' is not an integer"), inner = e)
                maxKey = nowutc() + timedelta(days = toDays)

            if self._queryParams["conferenceId"]:
                conferenceId = self._queryParams["conferenceId"]
            else:
                conferenceId = None

            if self._queryParams["categoryId"]:
                categoryId = self._queryParams["categoryId"]
            else:
                categoryId = None

            result = ci.getBookings(
                        self._queryParams["indexName"],
                        self._queryParams["viewBy"],
                        self._queryParams["orderBy"],
                        minKey,
                        maxKey,
                        tz = tz,
                        onlyPending = self._queryParams["onlyPending"],
                        conferenceId = conferenceId,
                        categoryId = categoryId,
                        pickle = True,
                        dateFormat = '%a %d %b %Y',
                        page = self._queryParams["page"],
                        resultsPerPage = self._queryParams["resultsPerPage"])

            vars["InitialBookings"] = result["results"]
            vars["InitialNumberOfBookings"] = result["nBookings"]
            vars["InitialTotalInIndex"] = result["totalInIndex"]
            vars["InitialNumberOfPages"] = result["nPages"]

        else:
            vars["InitialBookings"] = None
            vars["InitialNumberOfBookings"] = -1
            vars["InitialTotalInIndex"] = -1
            vars["InitialNumberOfPages"] = -1

        JSCodes = {}
        for pluginName in self._pluginsWithIndexing:
            templateClass = CollaborationTools.getTemplateClass(pluginName, "WIndexing")
            if templateClass:
                JSCodes[pluginName] = templateClass(pluginName, None).getHTML()

        vars["JSCodes"] = JSCodes

        return vars


################################################### Event Modif pages ###############################################

class WPConfModifCSBase (WPConferenceModifBase):

    def __init__(self, rh, conf):
        """ Constructor
            The rh is expected to have the attributes _tabs, _activeTab, _tabPlugins (like for ex. RHConfModifCSBookings)
        """
        WPConferenceModifBase.__init__(self, rh, conf)
        self._conf = conf
        self._tabs = {} # list of Indico's Tab objects
        self._tabNames = rh._tabs
        self._activeTabName = rh._activeTabName

    def _createTabCtrl(self):
        self._tabCtrl = wcomponents.TabControl()

        isUsingHTTPS = CollaborationTools.isUsingHTTPS()
        for tabName in self._tabNames:
            if tabName == 'Managers':
                url = urlHandlers.UHConfModifCollaborationManagers.getURL(self._conf)
            else:
                url = urlHandlers.UHConfModifCollaboration.getURL(self._conf, secure = isUsingHTTPS, tab = tabName)
            self._tabs[tabName] = self._tabCtrl.newTab(tabName, tabName, url)

        self._setActiveTab()

    def _setActiveTab(self):
        self._tabs[self._activeTabName].setActive()

    def _setActiveSideMenuItem(self):
        self._videoServicesMenuItem.setActive()

class WPConfModifCollaboration(WPConfModifCSBase):

    def __init__(self, rh, conf):
        """ Constructor
            The rh is expected to have the attributes _tabs, _activeTabName, _tabPlugins (like RHConfModifCSBookings)
        """
        WPConfModifCSBase.__init__(self, rh, conf)
        self._tabPlugins = rh._tabPlugins
        self._buildExtraCSS()
        self._buildExtraJS()

    def getJSFiles(self):
        return WPMainBase.getJSFiles(self) + self._includeJSPackage('Collaboration') + self._includeJSPackage("Management")

    ######### private methods ###############
    def _buildExtraCSS(self):
        for plugin in self._tabPlugins:
            extraCSS = CollaborationTools.getExtraCSS(plugin.getName())
            if extraCSS:
                self.addExtraCSS(extraCSS)

    def _buildExtraJS(self):
        for plugin in self._tabPlugins:
            extraJS = CollaborationTools.getExtraJS(plugin.getName(), self._conf)
            if extraJS:
                self.addExtraJS(extraJS)

    ############## overloading methods #################

    def _getPageContent(self, params):
        if len(self._tabNames) > 0:
            self._createTabCtrl()
            wc = WConfModifCollaboration(self._conf, self._rh.getAW().getUser(), self._activeTabName, self._tabPlugins)
            return wcomponents.WTabControl(self._tabCtrl, self._getAW()).getHTML(wc.getHTML({}))
        else:
            return _("No available plugins, or no active plugins")


class WConfModifCollaboration(wcomponents.WTemplated):

    def __init__(self, conference, user, activeTab, tabPlugins):
        self._conf = conference
        self._user = user
        self._activeTab = activeTab
        self._tabPlugins = tabPlugins

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)

        plugins = self._tabPlugins
        singleBookingPlugins, multipleBookingPlugins = CollaborationTools.splitPluginsByAllowMultiple(plugins)
        CSBookingManager = self._conf.getCSBookingManager()

        bookingsS = {}
        for p in singleBookingPlugins:
            bookingList = CSBookingManager.getBookingList(filterByType = p.getName())
            if len(bookingList) > 0:
                bookingsS[p.getName()] = DictPickler.pickle(bookingList[0])

        bookingsM = DictPickler.pickle(CSBookingManager.getBookingList(
            sorted = True,
            notify = True,
            filterByType = [p.getName() for p in multipleBookingPlugins]))

        vars["Conference"] = self._conf
        vars["AllPlugins"] = plugins
        vars["SingleBookingPlugins"] = singleBookingPlugins
        vars["BookingsS"] = bookingsS
        vars["MultipleBookingPlugins"] = multipleBookingPlugins
        vars["BookingsM"] = bookingsM
        vars["Tab"] = self._activeTab
        vars["EventDate"] = formatDateTime(getAdjustedDate(nowutc(), self._conf))

        from MaKaC.webinterface.rh.collaboration import RCCollaborationAdmin, RCCollaborationPluginAdmin
        vars["UserIsAdmin"] = RCCollaborationAdmin.hasRights(user = self._user) or RCCollaborationPluginAdmin.hasRights(user = self._user, plugins = self._tabPlugins)

        singleBookingForms = {}
        multipleBookingForms = {}
        JSCodes = {}
        canBeNotified = {}

        for plugin in singleBookingPlugins:
            pluginName = plugin.getName()
            templateClass = CollaborationTools.getTemplateClass(pluginName, "WNewBookingForm")
            singleBookingForms[pluginName] = templateClass(self._conf, pluginName, self._user).getHTML()

        for plugin in multipleBookingPlugins:
            pluginName = plugin.getName()
            templateClass = CollaborationTools.getTemplateClass(pluginName, "WNewBookingForm")
            multipleBookingForms[pluginName] = templateClass(self._conf, pluginName, self._user).getHTML()

        for plugin in plugins:
            pluginName = plugin.getName()

            templateClass = CollaborationTools.getTemplateClass(pluginName, "WMain")
            JSCodes[pluginName] = templateClass(pluginName, self._conf).getHTML()

            bookingClass = CollaborationTools.getCSBookingClass(pluginName)
            canBeNotified[pluginName] = bookingClass._canBeNotifiedOfEventDateChanges

        vars["SingleBookingForms"] = singleBookingForms
        vars["MultipleBookingForms"] = multipleBookingForms
        vars["JSCodes"] = JSCodes
        vars["CanBeNotified"] = canBeNotified

        return vars


class WPConfModifCollaborationProtection(WPConfModifCSBase):

    def __init__(self, rh, conf):
        """ Constructor
            The rh is expected to have the attributes _tabs, _activeTab, _tabPlugins (like RHConfModifCSBookings)
        """
        WPConfModifCSBase.__init__(self, rh, conf)
        self._user = rh._getUser()

    def _getPageContent(self, params):
        if len(self._tabNames) > 0:
            self._createTabCtrl()
            wc = WConfModifCollaborationProtection(self._conf, self._user)
            return wcomponents.WTabControl(self._tabCtrl, self._getAW()).getHTML(wc.getHTML({}))
        else:
            return _("No available plugins, or no active plugins")

class WConfModifCollaborationProtection(wcomponents.WTemplated):

    def __init__(self, conference, user):
        self._conf = conference
        self._user = user

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["Conference"] = self._conf
        vars["CSBM"] = self._conf.getCSBookingManager()
        if self._user:
            vars["Favorites"] = DictPickler.pickle(self._user.getPersonalInfo().getBasket().getUsers())
        else:
            vars["Favorites"] = []
        return vars

################################################### Event Display pages ###############################################
class WPCollaborationDisplay(WPConferenceDefaultDisplayBase):

    def _defineSectionMenu(self):
        WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._collaborationOpt)

    def _getBody(self, params):

        wc = WCollaborationDisplay(self._getAW(), self._conf)
        return wc.getHTML()

class WCollaborationDisplay(wcomponents.WTemplated):

    def __init__(self, aw, conference):
        wcomponents.WTemplated.__init__(self)
        self._conf = conference
        self._tz = DisplayTZ(aw, conference).getDisplayTZ()

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)

        csbm = self._conf.getCSBookingManager()
        pluginNames = csbm.getEventDisplayPlugins()
        bookings = csbm.getBookingList(filterByType = pluginNames, notify = True, onlyPublic = True)
        bookings.sort(key = lambda b: b.getStartDate())

        ongoingBookings = []
        scheduledBookings = {} #date, list of bookings

        for b in bookings:
            if b.canBeStarted():
                ongoingBookings.append(b)
            if b.getStartDate() and b.getAdjustedStartDate('UTC') > nowutc():
                scheduledBookings.setdefault(b.getAdjustedStartDate(self._tz).date(), []).append(b)

        keys = scheduledBookings.keys()
        keys.sort()
        scheduledBookings = [(date, scheduledBookings[date]) for date in keys]

        vars["OngoingBookings"] = ongoingBookings
        vars["ScheduledBookings"] = scheduledBookings
        vars["Timezone"] = self._tz

        return vars
