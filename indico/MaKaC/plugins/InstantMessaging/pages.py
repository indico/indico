# -*- coding: utf-8 -*-
##
## $id$
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

from MaKaC.webinterface.pages.conferences import WPConferenceModifBase, WPConferenceDefaultDisplayBase
from MaKaC.webinterface import wcomponents
from MaKaC.webinterface.wcomponents import WTemplated
from MaKaC.common.utils import formatDateTime, parseDateTime
from MaKaC.common.fossilize import fossilize
from MaKaC.common.timezoneUtils import getAdjustedDate, nowutc, setAdjustedDate, DisplayTZ, minDatetime
from MaKaC.plugins import PluginsHolder, InstantMessaging
from MaKaC.plugins.helpers import DBHelpers
from MaKaC.plugins.util import PluginFieldsWrapper
from MaKaC.plugins.InstantMessaging import urlHandlers
from MaKaC.webinterface.rh.conferenceModif import RHMaterialsShow
from MaKaC.plugins.InstantMessaging.XMPP.helpers import generateCustomLinks, generateLogLink, XMPPLogsActivated, DesktopLinkGenerator, WebLinkGenerator
from MaKaC.i18n import _
import zope.interface
from indico.core.extpoint import Component
from indico.core.extpoint.events import IEventDisplayContributor


class WPConfModifChat(WPConferenceModifBase):

    def __init__(self, rh, conf):
        WPConferenceModifBase.__init__(self, rh, conf)
        self._conf = conf
        self._tabs = {} # list of Indico's Tab objects
        self._tabNames = rh._tabs
        self._activeTabName = rh._activeTabName
        self._aw = rh.getAW()

        self._tabCtrl = wcomponents.TabControl()

    #TODO: with wsgi we want to specify another path instead of the usual one for .js files, so we'll have to make some modifications
    #to make possible specifying absoulte paths
    def getJSFiles(self):
        return WPConferenceModifBase.getJSFiles(self) + self._includeJSPackage('Plugins')

    def getJSFiles(self):
        return WPConferenceModifBase.getJSFiles(self) + \
               self._includeJSFile('InstantMessaging/js', 'InstantMessaging')

    def getCSSFiles(self):
        return WPConferenceModifBase.getCSSFiles(self) + \
               ['InstantMessaging/im.css']

    def _createTabCtrl(self):
        for tabName in self._tabNames:
            url = urlHandlers.UHConfModifChat.getURL(self._conf, tab = tabName)
            self._tabs[tabName] = self._tabCtrl.newTab(tabName, tabName, url)

        self._setActiveTab()

    def _setActiveSideMenuItem(self):
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

    def _defineSectionMenu( self ):
        WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._sectionMenu.getLinkByName("instantMessaging"))


class IMEventDisplayComponent(Component):

    zope.interface.implements(IEventDisplayContributor)

    # EventDisplayContributor
    def injectCSSFiles(self, obj):
        return ['InstantMessaging/im.css']


class WConfModifChat(wcomponents.WTemplated):

    def __init__(self, conference, activeTab, tabNames, aw):
        self._conf = conference
        self._activeTab = activeTab
        self._tabNames = tabNames
        self._aw = aw
        self._user = aw.getUser()

    def getVars( self ):
        vars = WTemplated.getVars( self )
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
            crinfo = links[cr.getId() ] = {}
            crinfo['custom'] = generateCustomLinks(cr)
            crinfo['logs'] = generateLogLink(cr, self._conf)

        vars['links'] = links

        vars['DefaultServer'] = PluginFieldsWrapper('InstantMessaging', 'XMPP').getOption('chatServerHost')
        vars["EventDate"] = formatDateTime(getAdjustedDate(nowutc(), self._conf))
        vars["User"] = self._user
        vars["tz"] = DisplayTZ(self._aw,self._conf).getDisplayTZ()
        vars["MaterialUrl"] = RHMaterialsShow._uh().getURL(self._conf).__str__()
        vars["ShowLogsLink"] = XMPPLogsActivated()

        return vars

class WConferenceInstantMessaging(wcomponents.WTemplated):

    def __init__(self, conference, aw):
        self._conf = conference
        self._aw = aw
        self._user = aw.getUser()

    def getVars( self ):
        vars = WTemplated.getVars( self )

        vars["Conference"] = self._conf

        try:
            vars["Chatrooms"] = DBHelpers.getShowableRooms(self._conf)
        except Exception, e:
            vars["Chatrooms"] = None
        vars["Links"] = {}
        for cr in vars["Chatrooms"]:
            vars["Links"][cr.getId()] = {}
            vars["Links"][cr.getId()]['custom'] = generateCustomLinks(cr)

        return vars
