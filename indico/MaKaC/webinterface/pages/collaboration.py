# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2012 European Organization for Nuclear Research (CERN).
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

from datetime import timedelta
from MaKaC.webinterface import wcomponents, urlHandlers
from MaKaC.webinterface.pages.conferences import WPConferenceModifBase, \
    WPConferenceDefaultDisplayBase
from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools
from MaKaC.common.timezoneUtils import nowutc, setAdjustedDate, DisplayTZ,\
    minDatetime
from MaKaC.common.utils import formatDateTime, parseDateTime
from MaKaC.common.timezoneUtils import getAdjustedDate
from MaKaC.i18n import _
from MaKaC.webinterface.pages.main import WPMainBase
from MaKaC.common.indexes import IndexesHolder
from MaKaC.plugins.Collaboration.base import CollaborationException, WCSPageTemplateBase
from MaKaC.common.fossilize import fossilize
from MaKaC.fossils.user import IAvatarFossil
from MaKaC.services.implementation.user import UserComparator
from MaKaC.plugins.Collaboration.fossils import IIndexInformationFossil

#from MaKaC.fossils.contribution import IContributionWithSpeakersMinimalFossil

################################################### Server Wide pages #########################################

class WPAdminCollaboration(WPMainBase):

    def __init__(self, rh, queryParams):
        WPMainBase.__init__(self, rh)
        self._queryParams = queryParams
        self._user = self._rh.getAW().getUser()
        self._pluginsWithIndexing = CollaborationTools.pluginsWithIndexing() # list of names
        self._buildExtraJS()

    def getJSFiles(self):
        return WPMainBase.getJSFiles(self) + self._includeJSPackage('Display') \
            + self._includeJSPackage('Collaboration')

    def getCSSFiles(self):
        return WPMainBase.getCSSFiles(self) + \
            ['Collaboration/Style.css']


    def _getHeader(self):
        wc = wcomponents.WHeader(self._getAW())
        return wc.getHTML({ "subArea": _("Video Services Administration"), \
                             "loginURL": self._escapeChars(str(self.getLoginURL())), \
                             "logoutURL": self._escapeChars(str(self.getLogoutURL())), \
                             "tabControl": self._getTabControl() })

    def _getBody(self, params):
        return WAdminCollaboration(self._queryParams, self._pluginsWithIndexing, self._user).getHTML()

    def _getNavigationDrawer(self):
        return wcomponents.WSimpleNavigationDrawer("Video Services Admin", urlHandlers.UHAdminCollaboration.getURL)

    def _buildExtraJS(self):
        for plugin in self._pluginsWithIndexing:
            extraJS = CollaborationTools.getExtraJS(None, plugin, self._user)
            if extraJS:
                self.addExtraJS(extraJS)

class WAdminCollaboration(wcomponents.WTemplated):

    def __init__(self, queryParams, pluginsWithIndexing, user):
        wcomponents.WTemplated.__init__(self)
        self._queryParams = queryParams
        self._pluginsWithIndexing = pluginsWithIndexing # list of names
        self._user = user

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)

        #dictionary where the keys are names of false "indexes" for the user, and the values are IndexInformation objects
        indexes = CollaborationTools.getCollaborationPluginType().getOption("pluginsPerIndex").getValue()
        vars["Indexes"] = ['all', None, 'Vidyo', 'EVO', 'CERNMCU', 'All Videoconference', None, 'WebcastRequest', 'RecordingRequest', 'All Requests']
        vars["IndexInformation"] = fossilize(dict([(i.getName(), i) for i in indexes]), IIndexInformationFossil)
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
                midnight = nowutc().replace(hour=0, minute=0, second=0)
                minKey = midnight - timedelta(days = fromDays)
            if self._queryParams['toDays']:
                try:
                    toDays = int(self._queryParams['toDays'])
                except ValueError, e:
                    raise CollaborationException(_("Parameter 'toDays' is not an integer"), inner = e)
                midnight_1 = nowutc().replace(hour=23, minute=59, second=59)
                maxKey = midnight_1 + timedelta(days = toDays)

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
                        resultsPerPage = self._queryParams["resultsPerPage"],
                        grouped= True)

            vars["InitialBookings"] = result["results"]
            vars["InitialNumberOfBookings"] = result["nBookings"]
            vars["InitialTotalInIndex"] = result["totalInIndex"]
            vars["InitialNumberOfPages"] = result["nPages"]

        else:
            vars["InitialBookings"] = None
            vars["InitialNumberOfBookings"] = -1
            vars["InitialTotalInIndex"] = -1
            vars["InitialNumberOfPages"] = -1

        jsCodes = {}
        for plugin in self._pluginsWithIndexing:
            templateClass = CollaborationTools.getTemplateClass(plugin.getId(),
                                                                "WIndexing")
            if templateClass:
                jsCodes[plugin.getId()] = templateClass(None, plugin.getId(), self._user).getHTML()

        vars["JSCodes"] = jsCodes

        return vars


################################################### Event Modif pages ###############################################

class WPConfModifCSBase (WPConferenceModifBase):

    _userData = ['favorite-user-list']

    def __init__(self, rh, conf):
        """ Constructor
            The rh is expected to have the attributes _tabs, _activeTab, _tabPlugins (like for ex. RHConfModifCSBookings)
        """
        WPConferenceModifBase.__init__(self, rh, conf)
        self._conf = conf
        self._tabs = {} # list of Indico's Tab objects
        self._tabNames = rh._tabs
        self._activeTabName = rh._activeTabName
        self.rh = rh
        self._tabCtrl = wcomponents.TabControl()

    def _createTabCtrl(self):

        for tabName in self._tabNames:
            isPlugin = False

            for plugin in CollaborationTools.getPluginsByTab(tabName, self._conf, self.rh._getUser()):
                isPlugin = True

            if tabName != 'Managers' and not isPlugin:
                from MaKaC.plugins.Collaboration.urlHandlers import UHCollaborationElectronicAgreement
                url = UHCollaborationElectronicAgreement.getURL(self._conf)
            elif tabName == 'Managers':
                url = urlHandlers.UHConfModifCollaborationManagers.getURL(self._conf)
            else:
                url = urlHandlers.UHConfModifCollaboration.getURL(self._conf, secure = self.rh.use_https(), tab = tabName)
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
        self._buildExtraJS()

    def getCSSFiles(self):
        for plugin in self._tabPlugins:
            return WPConfModifCSBase.getCSSFiles(self) + \
                   ['Collaboration/%s/Style.css' % plugin.getId()]

    def getJSFiles(self):
        return WPMainBase.getJSFiles(self) + self._includeJSPackage("Display") + self._includeJSPackage('Collaboration') + self._includeJSPackage("Management")

    ######### private methods ###############
    def _buildExtraJS(self):
        for plugin in self._tabPlugins:
            extraJS = CollaborationTools.getExtraJS(self._conf, plugin, self._getAW().getUser())
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
        csBookingManager = self._conf.getCSBookingManager()

        bookingsS = {}

        for p in singleBookingPlugins:
            bookingList = csBookingManager.getBookingList(filterByType = p.getId())
            if len(bookingList) > 0:
                bookingsS[p.getId()] = fossilize(bookingList[0]) #will use ICSBookingConfModifBaseFossil or inheriting fossil

        bookingsM = fossilize(csBookingManager.getBookingList(
            sorted = True,
            notify = True,
            filterByType = [p.getName() for p in multipleBookingPlugins])) #will use ICSBookingConfModifBaseFossil or inheriting fossil

        vars["Conference"] = self._conf
        vars["AllPlugins"] = plugins
        vars["SingleBookingPlugins"] = singleBookingPlugins
        vars["BookingsS"] = bookingsS
        vars["MultipleBookingPlugins"] = multipleBookingPlugins
        vars["BookingsM"] = bookingsM
        vars["Tab"] = self._activeTab
        vars["EventDate"] = formatDateTime(getAdjustedDate(nowutc(), self._conf))

        from MaKaC.webinterface.rh.collaboration import RCCollaborationAdmin, RCCollaborationPluginAdmin, RCVideoServicesUser
        vars["UserIsAdmin"] = RCCollaborationAdmin.hasRights(user = self._user) or RCCollaborationPluginAdmin.hasRights(user = self._user, plugins = self._tabPlugins)

        hasCreatePermissions = {}
        videoServSupport = {}
        for plugin in plugins:
            pname = plugin.getName()
            hasCreatePermissions[pname] = RCVideoServicesUser.hasRights(user = self._user, pluginName = pname)
            videoServSupport[pname] = plugin.getOption("contactSupport").getValue() if plugin.hasOption("contactSupport") else ""
        vars["HasCreatePermissions"] = hasCreatePermissions
        vars["VideoServiceSupport"] = videoServSupport




        singleBookingForms = {}
        multipleBookingForms = {}
        jsCodes = {}
        canBeNotified = {}

        for plugin in singleBookingPlugins:
            pluginId = plugin.getId()
            templateClass = CollaborationTools.getTemplateClass(pluginId, "WNewBookingForm")
            singleBookingForms[pluginId] = templateClass(self._conf, plugin.getId(), self._user).getHTML()

        for plugin in multipleBookingPlugins:
            pluginId = plugin.getId()
            templateClass = CollaborationTools.getTemplateClass(pluginId, "WNewBookingForm")
            newBookingFormHTML = templateClass(self._conf, plugin.getId(), self._user).getHTML()

            advancedTabClass = CollaborationTools.getTemplateClass(pluginId, "WAdvancedTab")
            if advancedTabClass:
                advancedTabClassHTML = advancedTabClass(self._conf, plugin.getId(), self._user).getHTML()
            else:
                advancedTabClassHTML = WConfModifCollaborationDefaultAdvancedTab(self._conf, plugin, self._user).getHTML()
            multipleBookingForms[pluginId] = (newBookingFormHTML, advancedTabClassHTML)

        for plugin in plugins:
            pluginId = plugin.getId()

            templateClass = CollaborationTools.getTemplateClass(pluginId, "WMain")
            jsCodes[pluginId] = templateClass(self._conf, plugin.getId(), self._user).getHTML()

            bookingClass = CollaborationTools.getCSBookingClass(pluginId)
            canBeNotified[pluginId] = bookingClass._canBeNotifiedOfEventDateChanges

        vars["SingleBookingForms"] = singleBookingForms
        vars["MultipleBookingForms"] = multipleBookingForms
        vars["JSCodes"] = jsCodes
        vars["CanBeNotified"] = canBeNotified

        return vars

class WAdvancedTabBase(WCSPageTemplateBase):

    def getVars(self):
        variables = WCSPageTemplateBase.getVars(self)

        bookingClass = CollaborationTools.getCSBookingClass(self._pluginId)
        variables["CanBeNotified"] = bookingClass._canBeNotifiedOfEventDateChanges

        return variables

class WConfModifCollaborationDefaultAdvancedTab(WAdvancedTabBase):

    def _setTPLFile(self):
        wcomponents.WTemplated._setTPLFile(self)


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
        csbm = self._conf.getCSBookingManager()
        vars["CSBM"] = csbm
        allManagers = fossilize(csbm.getAllManagers(), IAvatarFossil)
        vars["AllManagers"] = sorted(allManagers, cmp = UserComparator.cmpUsers)
        return vars

################################################### Event Display pages ###############################################
class WPCollaborationDisplay(WPConferenceDefaultDisplayBase):


    def getJSFiles(self):
        return WPConferenceDefaultDisplayBase.getJSFiles(self) + self._includeJSPackage('Display') + self._includeJSPackage('Collaboration')

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
        bookings.sort(key = lambda b: b.getStartDate() or minDatetime())

        ongoingBookings = []
        scheduledBookings = {} #date, list of bookings

        for b in bookings:
            if b.isHappeningNow():
                ongoingBookings.append(b)
            if b.getStartDate() and b.getAdjustedStartDate('UTC') > nowutc():
                scheduledBookings.setdefault(b.getAdjustedStartDate(self._tz).date(), []).append(b)

        keys = scheduledBookings.keys()
        keys.sort()
        scheduledBookings = [(date, scheduledBookings[date]) for date in keys]

        vars["OngoingBookings"] = ongoingBookings
        vars["ScheduledBookings"] = scheduledBookings
        vars["all_bookings"] = fossilize(bookings)
        vars["Timezone"] = self._tz
        vars["conf"] = self._conf

        return vars
