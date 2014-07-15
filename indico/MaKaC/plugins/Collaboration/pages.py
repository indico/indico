# -*- coding: utf-8 -*-
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

import os
from webassets import Bundle
from indico.web.assets import PluginEnvironment
from indico.util.date_time import now_utc

from indico.core.config import Config
from MaKaC.common.utils import formatTwoDates
from MaKaC.common.contextManager import ContextManager
from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools
from MaKaC.plugins.Collaboration.base import SpeakerStatusEnum
from indico.core.index import Catalog
from MaKaC.webinterface.pages.conferences import WPConferenceDefaultDisplayBase, WConfDisplayBodyBase
from MaKaC.webinterface.simple_event import WPSimpleEventDisplay
from MaKaC.webinterface.pages.main import WPMainBase
from MaKaC.webinterface import wcomponents, urlHandlers
from MaKaC.plugins import Collaboration
from MaKaC.plugins.Collaboration import urlHandlers as collaborationUrlHandlers

from indico.util.i18n import  L_
from indico.util.date_time import format_datetime

from datetime import timedelta, datetime
from MaKaC.webinterface.pages.conferences import WPConferenceModifBase
from MaKaC.common.timezoneUtils import nowutc, setAdjustedDate, DisplayTZ, minDatetime
from MaKaC.common.utils import formatDateTime
from MaKaC.common.timezoneUtils import getAdjustedDate
from MaKaC.i18n import _
from MaKaC.common.indexes import IndexesHolder
from MaKaC.plugins.Collaboration.base import CollaborationException, WCSPageTemplateBase
from MaKaC.common.fossilize import fossilize
from MaKaC.fossils.user import IAvatarFossil
from MaKaC.services.implementation.user import UserComparator
from MaKaC.plugins.Collaboration.fossils import IIndexInformationFossil
from MaKaC.common.info import HelperMaKaCInfo

STATUS_STRING = {
    SpeakerStatusEnum.NOEMAIL: L_("No Email"),
    SpeakerStatusEnum.NOTSIGNED: L_("Not Signed"),
    SpeakerStatusEnum.SIGNED: L_("Signed"),
    SpeakerStatusEnum.FROMFILE: L_("Uploaded"),
    SpeakerStatusEnum.PENDING: L_("Pending..."),
    SpeakerStatusEnum.REFUSED: L_("Refused")
}

class WEventDetailBanner(wcomponents.WTemplated):

    @staticmethod
    def getBookingType(booking):
        if booking.canBeStarted():
            return "ongoing"
        elif booking.hasStartDate() and booking.getStartDate() > now_utc():
            return "scheduled"
        else:
            return ""

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)

        vars["getBookingType"] = WEventDetailBanner.getBookingType
        vars["formatTwoDates"] = formatTwoDates
        vars["conf"] = self._rh._conf
        return vars


class WPCollaborationBase:

    def __init__(self):
        info = HelperMaKaCInfo.getMaKaCInfoInstance()
        self._plugin_asset_env = PluginEnvironment('Collaboration', os.path.dirname(__file__), 'Collaboration')
        self._plugin_asset_env.debug = info.isDebugActive()
        self._plugin_asset_env.register('collaboration_js', Bundle('js/Collaboration.js', 'js/bookings.js',
                                                                   filters='rjsmin',
                                                                   output="Collaboration_%(version)s.min.js"))
        self._plugin_asset_env.register('collaboration_css', Bundle('css/Style.css',
                                                                    filters='cssmin',
                                                                    output="Collaboration_%(version)s.min.css"))

    def getJSFiles(self):
        return self._includeJSPackage("Display") + self._plugin_asset_env['collaboration_js'].urls()

    def getCSSFiles(self):
        return self._plugin_asset_env['collaboration_css'].urls()

################################################### Server Wide pages #########################################


class WPAdminCollaboration(WPMainBase, WPCollaborationBase):

    def __init__(self, rh, queryParams):
        WPMainBase.__init__(self, rh)
        WPCollaborationBase.__init__(self)
        self._queryParams = queryParams
        self._user = self._rh.getAW().getUser()
        self._pluginsWithIndexing = CollaborationTools.pluginsWithIndexing(True)  # list of names
        self._buildExtraJS()

    def getJSFiles(self):
        return WPMainBase.getJSFiles(self) + WPCollaborationBase.getJSFiles(self)

    def getCSSFiles(self):
        return WPMainBase.getCSSFiles(self) + WPCollaborationBase.getCSSFiles(self)

    def _getHeader(self):
        wc = wcomponents.WHeader(self._getAW())
        return wc.getHTML({ "subArea": _("Video Services Administration"), \
                             "loginURL": self._escapeChars(str(self.getLoginURL())), \
                             "logoutURL": self._escapeChars(str(self.getLogoutURL())), \
                             "tabControl": self._getTabControl() })

    def _getBody(self, params):
        return WAdminCollaboration.forModule(Collaboration, self._queryParams, self._pluginsWithIndexing, self._user).getHTML()

    def _getNavigationDrawer(self):
        return wcomponents.WSimpleNavigationDrawer("Video Services Admin", collaborationUrlHandlers.UHAdminCollaboration.getURL)

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
        indexNames = set(i.getName() for i in indexes)
        indexList = ['all', None, 'Vidyo', 'EVO', 'CERNMCU', 'All Videoconference', None, 'WebcastRequest', 'RecordingRequest', 'All Requests']
        vars["Indexes"] = [x for x in indexList if x is None or x in indexNames]
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
        vars["BaseURL"] = collaborationUrlHandlers.UHAdminCollaboration.getURL()
        vars["ConfCollaborationDisplay"] = collaborationUrlHandlers.UHCollaborationDisplay.getURL()

        if self._queryParams["queryOnLoad"]:
            ci = IndexesHolder().getById('collaboration')
            tz = self._rh._getUser().getTimezone()
            #####
            minKey = None
            maxKey = None
            if self._queryParams['sinceDate']:
                minKey = setAdjustedDate(datetime.strptime(self._queryParams['sinceDate'].strip(), '%Y/%m/%d'),
                                         tz=tz)
            if self._queryParams['toDate']:
                maxKey = setAdjustedDate(datetime.strptime(self._queryParams['toDate'].strip(), '%Y/%m/%d'),
                                         tz=tz)
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

class WPConfModifCSBase (WPConferenceModifBase, WPCollaborationBase):

    _userData = ['favorite-user-list']

    def __init__(self, rh, conf):
        """ Constructor
            The rh is expected to have the attributes _tabs, _activeTab, _tabPlugins (for ex. RHConfModifCSBookings)
        """
        WPConferenceModifBase.__init__(self, rh, conf)
        WPCollaborationBase.__init__(self)
        self._conf = conf
        self._tabs = {}  # list of Indico's Tab objects
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
                url = collaborationUrlHandlers.UHCollaborationElectronicAgreement.getURL(self._conf)
            elif tabName == 'Managers':
                url = collaborationUrlHandlers.UHConfModifCollaborationManagers.getURL(self._conf)
            else:
                url = collaborationUrlHandlers.UHConfModifCollaboration.getURL(self._conf, secure = self.rh.use_https(), tab = tabName)
            self._tabs[tabName] = self._tabCtrl.newTab(tabName, tabName, url)

        self._setActiveTab()

    def _setActiveTab(self):
        self._tabs[self._activeTabName].setActive()

    def _setActiveSideMenuItem(self):
        if self._pluginsDictMenuItem.has_key('Video Services'):
            self._pluginsDictMenuItem['Video Services'].setActive(True)

    def getCSSFiles(self):
        return WPConferenceModifBase.getCSSFiles(self) + WPCollaborationBase.getCSSFiles(self)

    def getJSFiles(self):
        return WPConferenceModifBase.getJSFiles(self) + WPCollaborationBase.getJSFiles(self)


class WPConfModifCollaboration(WPConfModifCSBase):

    def __init__(self, rh, conf):
        """ Constructor
            The rh is expected to have the attributes _tabs, _activeTabName, _tabPlugins (like RHConfModifCSBookings)
        """
        WPConfModifCSBase.__init__(self, rh, conf)
        self._tabPlugins = rh._tabPlugins
        self._buildExtraJS()

    def getCSSFiles(self):
        return WPConfModifCSBase.getCSSFiles(self)  \
            + ['Collaboration/%s/Style.css' % plugin.getId() for plugin in self._tabPlugins]

    def getJSFiles(self):
        return WPConfModifCSBase.getJSFiles(self) + self._includeJSPackage("Management")

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
            wc = WConfModifCollaboration.forModule(Collaboration, self._conf, self._rh.getAW().getUser(), self._activeTabName, self._tabPlugins)
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
        csBookingManager = Catalog.getIdx("cs_bookingmanager_conference").get(self._conf.getId())

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

        from MaKaC.plugins.Collaboration.handlers import RCCollaborationAdmin, RCCollaborationPluginAdmin, RCVideoServicesUser

        vars["UserIsAdmin"] = RCCollaborationAdmin.hasRights(self._user) or RCCollaborationPluginAdmin.hasRights(self._user, plugins=self._tabPlugins)

        hasCreatePermissions = {}
        videoServSupport = {}
        isAllowedToSearch = {}
        for plugin in plugins:
            pname = plugin.getName()
            hasCreatePermissions[pname] = RCVideoServicesUser.hasRights(user=self._user, pluginName=pname)
            videoServSupport[pname] = plugin.getOption("contactSupport").getValue() \
                if plugin.hasOption("contactSupport") else ""
            isAllowedToSearch[pname] = plugin.getOption("searchAllow").getValue() if plugin.hasOption("searchAllow")  \
                else False
        vars["HasCreatePermissions"] = hasCreatePermissions
        vars["VideoServiceSupport"] = videoServSupport
        vars["isAllowedToSearch"] = isAllowedToSearch

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
            wc = WConfModifCollaborationProtection.forModule(Collaboration, self._conf, self._user)
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
        csbm = Catalog.getIdx("cs_bookingmanager_conference").get(self._conf.getId())
        vars["CSBM"] = csbm
        allManagers = fossilize(csbm.getAllManagers(), IAvatarFossil)
        vars["AllManagers"] = sorted(allManagers, cmp = UserComparator.cmpUsers)
        return vars

################################################### Event Display pages ###############################################
class WPCollaborationDisplay(WPConferenceDefaultDisplayBase, WPCollaborationBase):

    def __init__(self, rh, conference):
        WPConferenceDefaultDisplayBase.__init__(self, rh, conference)
        WPCollaborationBase.__init__(self)


    def _defineSectionMenu(self):
        WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._collaborationOpt)

    def getCSSFiles(self):
        return WPConferenceDefaultDisplayBase.getCSSFiles(self)

    def getJSFiles(self):
        return WPConferenceDefaultDisplayBase.getJSFiles(self)

    def _getBody(self, params):

        wc = WCollaborationDisplay.forModule(Collaboration, self._getAW(), self._conf)
        return wc.getHTML()


class WCollaborationDisplay(WConfDisplayBodyBase):

    _linkname = "collaboration"

    def __init__(self, aw, conference):
        WConfDisplayBodyBase.__init__(self)
        self._conf = conference
        self._tz = DisplayTZ(aw, conference).getDisplayTZ()

    def getVars(self):
        wvars = WConfDisplayBodyBase.getVars(self)

        csbm = Catalog.getIdx("cs_bookingmanager_conference").get(self._conf.getId())
        pluginNames = csbm.getEventDisplayPlugins()
        bookings = csbm.getBookingList(filterByType=pluginNames, notify=True, onlyPublic=True)
        bookings.sort(key=lambda b: b.getStartDate() or minDatetime())

        timeless_bookings = []
        ongoingBookings = []
        scheduledBookings = {} #date, list of bookings

        for b in bookings:
            if b.canBeDisplayed():
                if not b.hasStartDate():
                    timeless_bookings.append(b)
                else:
                    if b.isHappeningNow():
                        ongoingBookings.append(b)
                    elif b.getStartDate() and b.getAdjustedStartDate('UTC') > nowutc():
                        scheduledBookings.setdefault(b.getAdjustedStartDate(self._tz).date(), []).append(b)

        keys = scheduledBookings.keys()
        keys.sort()
        scheduledBookings = [(date, scheduledBookings[date]) for date in keys]

        wvars["body_title"] = self._getTitle()
        wvars["OngoingBookings"] = ongoingBookings
        wvars["ScheduledBookings"] = scheduledBookings
        wvars["timeless_bookings"] = timeless_bookings
        wvars["all_bookings"] = fossilize(bookings)
        wvars["Timezone"] = self._tz
        wvars["conf"] = self._conf

        return wvars


# Extra WP and W classes for the Electronic Agreement page
# Here the form page
class WPElectronicAgreementForm(WPSimpleEventDisplay, WPCollaborationBase):
    def __init__(self, rh, conf, authKey):
        WPSimpleEventDisplay.__init__(self, rh, conf)
        WPCollaborationBase.__init__(self)
        self.authKey = authKey

    def getCSSFiles(self):
        return WPSimpleEventDisplay.getCSSFiles(self) + WPCollaborationBase.getCSSFiles(self)

    def getJSFiles(self):
        return WPSimpleEventDisplay.getJSFiles(self) + WPCollaborationBase.getJSFiles(self)

    def _getBody(self, params):
        wc = WElectronicAgreementForm.forModule(Collaboration, self._conf, self.authKey)
        return wc.getHTML()

class WPElectronicAgreementFormConference(WPConferenceDefaultDisplayBase, WPCollaborationBase):
    def __init__(self, rh, conf, authKey):
        WPConferenceDefaultDisplayBase.__init__(self, rh, conf)
        WPCollaborationBase.__init__(self)
        self.authKey = authKey

    def getCSSFiles(self):
        return WPConferenceDefaultDisplayBase.getCSSFiles(self) + self._plugin_asset_env['collaboration_css'].urls()

    def getJSFiles(self):
        return WPConferenceDefaultDisplayBase.getJSFiles(self) + WPCollaborationBase.getJSFiles(self)

    def _getBody(self, params):
        wc = WElectronicAgreementForm.forModule(Collaboration, self._conf, self.authKey)
        return wc.getHTML()

class WElectronicAgreementForm(wcomponents.WTemplated):
    def __init__(self, conf, authKey):
        self._conf = conf
        self.authKey = authKey
        self.spkWrapper = None

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)

        agreement_name = CollaborationTools.getOptionValue("RecordingRequest", "AgreementName")
        manager = Catalog.getIdx("cs_bookingmanager_conference").get(self._conf.getId())

        for sw in manager.getSpeakerWrapperList():
            if sw.getUniqueIdHash() == self.authKey:
                self.spkWrapper = sw

        if self.spkWrapper:
            speaker = self.spkWrapper.getObject()
            vars['speaker'] = speaker
            vars['conf'] = self._conf

            if self.spkWrapper.getStatus() in [SpeakerStatusEnum.SIGNED,
                                               SpeakerStatusEnum.FROMFILE,
                                               SpeakerStatusEnum.REFUSED]:

                vars['error'] = 'Already Submitted'

                if self.spkWrapper.getStatus() == SpeakerStatusEnum.SIGNED:
                    dtagree = self.spkWrapper.getDateAgreementSigned()
                    vars['outcomeText'] = _("You have already submitted your electronic agreement, it appears that you accepted it on <strong>%s</strong>.") % format_datetime(dtagree)
                elif self.spkWrapper.getStatus() == SpeakerStatusEnum.REFUSED:
                    vars['outcomeText'] = _("You have already submitted your electronic agreement, it appears that you refused it.")
                else:
                    vars['outcomeText'] = _("The organizer has already uploaded a scanned copy of {0}. No electronic signature is needed.").format(
                        CollaborationTools.getOptionValue("RecordingRequest", "AgreementName"))

            else:
                vars['error'] = None
                vars['authKey'] = self.authKey

                if self._conf.getType() == 'simple_event':
                    # if it's a lecture we consider the _conf object as the normal
                    # contribution and trigger a flag, in order to not print
                    # contributions detail...
                    showContributionInfo = False
                    cont = self._conf
                else:
                    showContributionInfo = True
                    cont = self._conf.getContributionById(self.spkWrapper.getContId())

                vars['cont'] = cont
                vars['showContributionInfo'] = self.authKey

                location = cont.getLocation()
                room = cont.getRoom()
                if location and location.getName() and location.getName().strip():
                    locationText = location.getName().strip()
                    if room and room.getName() and room.getName().strip():
                        locationText += ". " + _("Room: %s" % room.getName().strip())
                    else:
                        locationText += " " + _("(room not defined)")
                else:
                    locationText = _("location/room not defined")

                vars['locationText'] = locationText

                tz = self._conf.getTimezone()
                vars['confDate'] = "%s (%s)" % (formatTwoDates(self._conf.getStartDate(), self._conf.getEndDate(), tz = tz, showWeek = True), tz)
                vars['contDate'] = "%s (%s)"%(formatTwoDates(cont.getStartDate(), cont.getEndDate(), tz = tz, showWeek = True), tz)

                vars['linkToEvent'] = urlHandlers.UHConferenceDisplay.getURL(self._conf)
                vars['agreementName'] = agreement_name
        else:
            vars['error'] = 'Error'

        return vars


# Here the administration page
class WPElectronicAgreement(WPConfModifCollaboration):

    def _setActiveTab(self):
        self._tabs[self._activeTabName].setActive()
    #only for tests...
    def getJSFiles(self):
        return WPConfModifCollaboration.getJSFiles(self) + self._includeJSPackage("MaterialEditor")

    def _getPageContent(self, params):
        if len(self._tabNames) > 0:
            self._createTabCtrl()
            wc = WElectronicAgreement.forModule(Collaboration, self._conf, self._rh.getAW().getUser(),
                                                self._activeTabName, self._tabPlugins, params.get("sortCriteria"),
                                                params.get("order"))
            return wcomponents.WTabControl(self._tabCtrl, self._getAW()).getHTML(wc.getHTML({}))
        else:
            return _("No available plugins, or no active plugins")

class WElectronicAgreement(wcomponents.WTemplated):
    def __init__(self, conference, user, activeTab, tabPlugins, sortBy, order):
        self._conf = conference
        self._user = user
        self._activeTab = activeTab
        self._tabPlugins = tabPlugins
        self.sortFields = ["speaker", "status", "cont", "reqType"] # Sorting fields allowed
        self.orderFields = ["up", "down"] # order fields allowed
        self._fromList = []
        self.sortCriteria = sortBy
        self.order = order

    def getListSorted(self, dict):
        '''
        Function used to sort the dictionary containing the contributions and speakers of the single booking.
        It returns a sorted list of list with only the necessary information:
        [[spkId, spkName, spkStatus, contId], [spkId, spkName, spkStatus, contId], ...]
        '''
        manager = Catalog.getIdx("cs_bookingmanager_conference").get(self._conf.getId())
        lst = []

        sortMap = {'speaker': 1, 'status': 2, 'cont': 3, 'reqType': 4}
        reverse = False if self.order == 'down' else True

        for cont in dict:
            for id in dict[cont]:
                sw = manager.getSpeakerWrapperByUniqueId("%s.%s"%(cont, id.getId()))
                status = ""
                reqType = "NA"
                enabled = False
                if sw:
                    status = STATUS_STRING[sw.getStatus()]
                    reqType = sw.getRequestType()
                    enabled = sw.getStatus() not in [SpeakerStatusEnum.SIGNED, SpeakerStatusEnum.FROMFILE,
                                                     SpeakerStatusEnum.NOEMAIL]

                lst.append([id.getId(), id.getFullNameNoTitle(), status, cont, reqType, enabled])

        return sorted(lst, key=lambda list: lst[sortMap[self.sortCriteria]], reverse=reverse)

    def getTableContent(self):

        manager = Catalog.getIdx("cs_bookingmanager_conference").get(self._conf.getId())
        # Here we check the rights again, and chose what contributions we should show
        requestType = CollaborationTools.getRequestTypeUserCanManage(self._conf, self._user)

        self._fromList = [{"name": self._user.getStraightFullName(), "email": email}
                          for email in self._user.getEmails()]

        contributions = manager.getContributionSpeakerByType(requestType)

        return self.getListSorted(contributions)

    def getPaperAgreementURL(self):
        recordingFormURL = CollaborationTools.getOptionValue("RecordingRequest", "ConsentFormURL")
        webcastFormURL = CollaborationTools.getOptionValue("WebcastRequest", "ConsentFormURL")
        requestType = CollaborationTools.getRequestTypeUserCanManage(self._conf, self._user)
        #return recordingFormURL
        if requestType == 'recording' and recordingFormURL != '':
            return _("""<a href="%s">Paper version</a>."""%recordingFormURL)
        elif requestType == 'webcast' and webcastFormURL != '':
            return _("""<a href="%s">Paper version</a>."""%webcastFormURL)
        elif requestType == 'both':
            if recordingFormURL == webcastFormURL and recordingFormURL != '': #same link, same file
                return _("""<a href="%s">Paper version</a>."""%recordingFormURL)
            elif recordingFormURL != '' and webcastFormURL != '':
                return _("""<a href="%s">Paper version</a> for the recording request or
                        <a href="%s">Paper version</a> for the webcast request."""%(recordingFormURL, webcastFormURL))
            elif recordingFormURL != '':
                return _("""<a href="%s">Paper version</a>."""%recordingFormURL)
            elif webcastFormURL != '':
                return _("""<a href="%s">Paper version</a>."""%webcastFormURL)
            else:
                return _("""<No agreement link available>.""")
        else:
            return _("""<No agreement link available>.""")

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)

        sortingField = None
        if self.sortCriteria in self.sortFields:
            sortingField = self.sortCriteria

        for crit in ["speaker", "status", "cont", "reqType"]:
            url = collaborationUrlHandlers.UHCollaborationElectronicAgreement.getURL(self._conf)
            vars["%sImg" % crit] = ""
            url.addParam("sortBy", crit)

            if sortingField == crit:
                if self.order == "up":
                    vars["%sImg" % crit] = '<img src="%s" alt="up">' % (Config.getInstance().getSystemIconURL("upArrow"))
                    url.addParam("order","down")
                elif self.order == "down":
                    vars["%sImg" % crit] = '<img src="%s" alt="down">' % (Config.getInstance().getSystemIconURL("downArrow"))
                    url.addParam("order","up")

            vars["%sSortingURL" % crit] = str(url)

        vars["conf"] = self._conf
        vars["contributions"] = self.getTableContent()
        vars['fromList'] = self._fromList
        manager = Catalog.getIdx("cs_bookingmanager_conference").get(self._conf.getId())
        vars['manager'] = manager
        vars['user'] = self._user

        if hasattr(manager, "_speakerWrapperList"):
            vars['signatureCompleted'] = manager.areSignatureCompleted()
        else:
            vars['signatureCompleted'] = None

        vars['STATUS_STRING'] = STATUS_STRING
        vars['canShow'] = manager.isAnyRequestAccepted()
        vars['SpeakerStatusEnum'] = SpeakerStatusEnum
        vars['user'] = self._user
        vars['collaborationUrlHandlers'] = collaborationUrlHandlers
        vars['urlPaperAgreement'] = self.getPaperAgreementURL()
        vars['agreementName'] = CollaborationTools.getOptionValue("RecordingRequest", "AgreementName")
        vars["notifyElectronicAgreementAnswer"] = manager.notifyElectronicAgreementAnswer()
        vars["emailIconURL"]=(str(Config.getInstance().getSystemIconURL("mail_grey")))
        vars["canModify"] = self._conf.canModify( self._rh.getAW() )
        return vars

class WVideoService(wcomponents.WTemplated):

    def __init__(self, conference, video):
        self._conf = conference
        self._video = video

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["conf"] = self._conf
        vars["video"] = self._video
        vars["aw"] = ContextManager.get("currentRH").getAW()
        return vars

class WPluginHelp(wcomponents.WTemplated):

    def getVars(self):
        from MaKaC.plugins.Collaboration.handlers import RCCollaborationAdmin
        from MaKaC.webinterface.rh.admins import RCAdmin

        vars = wcomponents.WTemplated.getVars(self)
        user = ContextManager.get("currentUser")
        vars["user"] = user
        vars["IsAdmin"] = RCAdmin.hasRights(self._rh)
        vars["IsCollaborationAdmin"] = RCCollaborationAdmin.hasRights(user)
        return vars
