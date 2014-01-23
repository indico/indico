# -*- coding: utf-8 -*-
##
## $id$
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
from MaKaC.webinterface.pages.conferences import WPConferenceModifBase, WPConferenceDefaultDisplayBase
from MaKaC.webinterface.pages.conferences import WConfDisplayBodyBase
from MaKaC.webinterface import wcomponents
from MaKaC.webinterface.wcomponents import WTemplated
from MaKaC.common.utils import formatDateTime
from MaKaC.common.fossilize import fossilize
from MaKaC.common.timezoneUtils import getAdjustedDate, nowutc, DisplayTZ
from MaKaC.plugins import PluginsHolder, InstantMessaging
from MaKaC.plugins.helpers import DBHelpers
from MaKaC.plugins.util import PluginFieldsWrapper
from MaKaC.plugins.InstantMessaging import urlHandlers
from MaKaC.webinterface.rh.conferenceModif import RHMaterialsShow
from MaKaC.plugins.InstantMessaging.XMPP.helpers import generateCustomLinks, generateLogLink, XMPPLogsActivated
from MaKaC.i18n import _
import zope.interface
from indico.core.extpoint import Component
from indico.core.extpoint.events import IEventDisplayContributor
from MaKaC.common.info import HelperMaKaCInfo


class WPConfModifChat(WPConferenceModifBase):

    def __init__(self, rh, conf):
        WPConferenceModifBase.__init__(self, rh, conf)
        self._conf = conf
        self._tabs = {}  # list of Indico's Tab objects
        self._tabNames = rh._tabs
        self._activeTabName = rh._activeTabName
        self._aw = rh.getAW()

        self._tabCtrl = wcomponents.TabControl()

        info = HelperMaKaCInfo.getMaKaCInfoInstance()
        self._plugin_asset_env = PluginEnvironment('InstantMessaging', os.path.dirname(__file__), 'InstantMessaging')
        self._plugin_asset_env.debug = info.isDebugActive()
        self._plugin_asset_env.register('instant_messaging_js', Bundle('js/InstantMessaging.js',
                                                                       filters='rjsmin',
                                                                       output="InstantMessaging_%(version)s.min.js"))
        self._plugin_asset_env.register('instant_messaging_css', Bundle('css/im.css',
                                                                        filters='cssmin',
                                                                        output="InstantMessaging_%(version)s.min.css"))

    def getJSFiles(self):
        return WPConferenceModifBase.getJSFiles(self) + \
            self._plugin_asset_env['instant_messaging_js'].urls()

    def getCSSFiles(self):
        return WPConferenceModifBase.getCSSFiles(self) + \
            self._plugin_asset_env['instant_messaging_css'].urls()

    def _createTabCtrl(self):
        for tabName in self._tabNames:
            url = urlHandlers.UHConfModifChat.getURL(self._conf, tab=tabName)
            self._tabs[tabName] = self._tabCtrl.newTab(tabName, tabName, url)

        self._setActiveTab()

    def _setActiveSideMenuItem(self):
        if self._pluginsDictMenuItem.has_key('InstantMessaging'):
            self._pluginsDictMenuItem['Instant Messaging'].setActive(True)

    def _setActiveTab(self):
        self._tabs[self._activeTabName].setActive()

    def _getTitle(self):
        return WPConferenceModifBase._getTitle(self) + " - " + _("Chat management")

    def _getPageContent(self, params):
        if len(self._tabNames) > 0:
            self._createTabCtrl()
            wc = WConfModifChat.forModule(InstantMessaging, self._conf,
                                          self._activeTabName, self._tabNames, self._aw)
            return wcomponents.WTabControl(self._tabCtrl, self._getAW()).getHTML(wc.getHTML({}))
        else:
            return _("No available plugins, or no active plugins")


class WPConferenceInstantMessaging(WPConferenceDefaultDisplayBase):

    def __init__(self, rh, conf):
        WPConferenceDefaultDisplayBase.__init__(self, rh, conf)
        self._conf = conf
        self._aw = rh.getAW()

    def _getBody(self, params):
        wc = WConferenceInstantMessaging.forModule(InstantMessaging,
                                                   self._conf, self._aw)
        return wc.getHTML({})

    def _defineSectionMenu(self):
        WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._sectionMenu.getLinkByName("instantMessaging"))


class IMEventDisplayComponent(Component):

    zope.interface.implements(IEventDisplayContributor)

    # EventDisplayContributor
    def injectCSSFiles(self, obj):
        return ['InstantMessaging/im.css']

    def eventDetailBanner(self, obj, conf):
        if DBHelpers.roomsToShow(conf):
            vars = {}
            vars['chatrooms'] = DBHelpers.getShowableRooms(conf)
            vars['linksList'] = PluginsHolder().getPluginType('InstantMessaging').getOption('customLinks').getValue()
            vars['how2connect'] = PluginFieldsWrapper('InstantMessaging', 'XMPP').getOption('ckEditor')
            return WEventDetailBanner.forModule(InstantMessaging).getHTML(vars)
        else:
            return ""


class WEventDetailBanner(wcomponents.WTemplated):
    pass


class WConfModifChat(wcomponents.WTemplated):

    def __init__(self, conference, activeTab, tabNames, aw):
        self._conf = conference
        self._activeTab = activeTab
        self._tabNames = tabNames
        self._aw = aw
        self._user = aw.getUser()

    def getVars(self):
        vars = WTemplated.getVars(self)
        vars["Conference"] = self._conf
        try:
            chatrooms = list(DBHelpers.getChatroomList(self._conf))
            vars["Chatrooms"] = fossilize(chatrooms)
            if len(vars['Chatrooms']) is 0:
                vars['Chatrooms'] = None
        except Exception, e:
            vars["Chatrooms"] = None
            chatrooms = {}
        links = {}

        for cr in chatrooms:
            crinfo = links[cr.getId()] = {}
            crinfo['custom'] = generateCustomLinks(cr)
            crinfo['logs'] = generateLogLink(cr, self._conf)

        vars['links'] = links

        vars['DefaultServer'] = PluginFieldsWrapper('InstantMessaging', 'XMPP').getOption('chatServerHost')
        vars["EventDate"] = formatDateTime(getAdjustedDate(nowutc(), self._conf))
        vars["User"] = self._user
        vars["tz"] = DisplayTZ(self._aw, self._conf).getDisplayTZ()
        vars["MaterialUrl"] = RHMaterialsShow._uh().getURL(self._conf).__str__()
        vars["ShowLogsLink"] = XMPPLogsActivated()

        return vars


class WConferenceInstantMessaging(WConfDisplayBodyBase):

    _linkname = "instantMessaging"

    def __init__(self, conference, aw):
        self._conf = conference
        self._aw = aw
        self._user = aw.getUser()

    def getVars(self):
        wvars = WTemplated.getVars(self)

        wvars["body_title"] = self._getTitle()
        wvars["Conference"] = self._conf

        try:
            wvars["Chatrooms"] = DBHelpers.getShowableRooms(self._conf)
        except Exception, e:
            wvars["Chatrooms"] = None
        wvars["Links"] = {}
        for cr in wvars["Chatrooms"]:
            wvars["Links"][cr.getId()] = {}
            wvars["Links"][cr.getId()]['custom'] = generateCustomLinks(cr)

        return wvars


class WPluginHelp(wcomponents.WTemplated):
    pass
