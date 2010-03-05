# -*- coding: utf-8 -*-
##
## $Id: collaboration.py,v 1.13 2009/04/28 14:08:41 dmartinc Exp $
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

from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase
from MaKaC.errors import MaKaCError, PluginError
from MaKaC.webinterface.pages import conferences
from MaKaC.webinterface.pages import collaboration
from MaKaC.webinterface import urlHandlers
from MaKaC.i18n import _
from MaKaC.plugins.base import PluginsHolder, Plugin
from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools
from MaKaC.webinterface.rh.admins import RCAdmin, RHAdminBase
from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay

class RCCollaborationAdmin(object):
    @staticmethod
    def hasRights(request = None, user = None):
        """ Returns True if the user is a Server Admin or a Collaboration admin
            request: an RH or Service object
            user: an Avatar object
            If user is not None, the request object will be used to check the user's privileges.
            Otherwise the user will be retrieved from the request object
        """
        if not PluginsHolder().hasPluginType("Collaboration"):
            return False

        if user is None:
            if request is None:
                return False
            else:
                user = request._getUser()

        # check if user is Server Admin, Collaboration Admin
        collaborationAdmins = PluginsHolder().getPluginType('Collaboration').getOption('collaborationAdmins').getValue()

        return RCAdmin.hasRights(None, user) or user in collaborationAdmins

class RCCollaborationPluginAdmin(object):
    @staticmethod
    def hasRights(request = None, user = None, plugins = []):
        """ Returns True if the user is an admin of one of the plugins corresponding to pluginNames
            plugins: a list of Plugin objects (e.g. EVO, RecordingRequest) or strings with the plugin name ('EVO', 'RecordingRequest')
                     or the string 'any' (we will then check if the user is manager of any plugin),
        """
        if not PluginsHolder().hasPluginType("Collaboration"):
            return False

        if user is None:
            if request is None:
                return False
            else:
                user = request._getUser()

        if user:
            collaborationPluginType = PluginsHolder().getPluginType('Collaboration')

            if plugins == 'any':
                plugins = []
                for p in CollaborationTools.getCollaborationPluginType().getPluginList():
                    plugins.append(p.getName())

            if plugins:
                for plugin in plugins:
                    if not isinstance(plugin, Plugin):
                        plugin = collaborationPluginType.getPlugin(plugin)

                    if user in plugin.getOption('admins').getValue():
                        return True

        return False


class RCVideoServicesManager(object):
    @staticmethod
    def hasRights(request, plugins = []):
        """ Returns True if the logged in user has rights to operate with bookings of at least one of a list of plugins, for an event.
            This is true if:
                -the user is a Video Services manager (can operate with all plugins)
                -the user is a plugin manager of one of the plugins
            Of course, it's also true if the user is event manager or server admin, but this class does not cover that case.

            request: an RH or Service object
            plugins: either a list of plugin names, or Plugin objects (we will then check if the user is manager of any of those plugins),
                     or the string 'any' (we will then check if the user is manager of any plugin),
                     or nothing (we will then check if the user is a Video Services manager).
        """
        if not PluginsHolder().hasPluginType("Collaboration"):
            return False

        user = request.getAW().getUser()

        if user:
            csbm = request._conf.getCSBookingManager()
            if csbm.isVideoServicesManager(user):
                return True

            if plugins == 'any':
                return csbm.isPluginManagerOfAnyPlugin(user)

            for plugin in plugins:
                if isinstance(plugin, Plugin):
                    plugin = plugin.getName()
                if csbm.isPluginManager(plugin, user):
                    return True

        return False

################################################### Server Wide pages #########################################
class RHAdminCollaboration(RHAdminBase):
    _uh = urlHandlers.UHAdminCollaboration

    def _checkParams( self, params ):
        RHAdminBase._checkParams( self, params )
        self._queryParams = {}
        self._queryParams["queryOnLoad"] = (params.get('queryOnLoad', None) == 'true')
        self._queryParams["page"] = params.get("page", 1)
        self._queryParams["resultsPerPage"] = params.get("resultsPerPage", 10)
        self._queryParams["indexName"] = params.get('indexName', None)
        self._queryParams["viewBy"] = params.get('viewBy', 'modificationDate')
        self._queryParams["orderBy"] = params.get('orderBy', '')
        self._queryParams["sinceDate"] = params.get('sinceDate', '').strip()
        self._queryParams["toDate"] = params.get('toDate', '').strip()
        self._queryParams["fromDays"] = params.get('fromDays', '').strip()
        self._queryParams["toDays"] = params.get('toDays', '').strip()
        self._queryParams["fromTitle"] = params.get('fromTitle', '').strip()
        self._queryParams["toTitle"] = params.get('toTitle', '').strip()
        self._queryParams["onlyPending"] = (params.get('onlyPending', None) == 'true')
        self._queryParams["conferenceId"] = params.get('conferenceId', '').strip()
        self._queryParams["categoryId"] = params.get('categoryId', '').strip()

    def _checkProtection( self ):
        if not PluginsHolder().hasPluginType("Collaboration"):
            raise PluginError("Collaboration plugin system is not active")

        if not RCCollaborationAdmin.hasRights(self, None) and not RCCollaborationPluginAdmin.hasRights(self, plugins = "any"): #RCCollaborationPluginAdmin.hasRights(self, None, self._tabPlugins):
            RHAdminBase._checkProtection(self)

    def _process(self):
        p = collaboration.WPAdminCollaboration( self , self._queryParams)
        return p.display()


################################################### Event Modification Request Handlers ####################################

class RHConfModifCSBase(RHConferenceModifBase):
    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)

        self._activeTabName = params.get("tab", None)

        self._canSeeAllPluginTabs = self._target.canModify(self.getAW()) or RCCollaborationAdmin.hasRights(self) or RCVideoServicesManager.hasRights(self)

        # we build the list 'allowedTabs', a list of all tabs that the user can see
        if self._canSeeAllPluginTabs:
            #if the logged in user is event manager, server admin or collaboration admin: we show all plugin tabs
            allowedTabs = CollaborationTools.getTabs(self._conf)
        else:
            #else we show only the tabs of plugins of which the user is admin
            allowedTabs = CollaborationTools.getTabs(self._conf, self._getUser())

        if self._target.canModify(self.getAW()) or RCVideoServicesManager.hasRights(self):
            allowedTabs.append('Managers')

        # we order the list of allowedTabs into the self._tabs list
        tabOrder = CollaborationTools.getCollaborationOptionValue('tabOrder')
        self._tabs = []

        for tabName in tabOrder:
            if tabName in allowedTabs:
                self._tabs.append(tabName)
                allowedTabs.remove(tabName)

        for tabName in allowedTabs:
            if tabName != 'Managers':
                self._tabs.append(tabName)

        if 'Managers' in allowedTabs:
            self._tabs.append('Managers')


class RHConfModifCSBookings(RHConfModifCSBase):
    _uh = urlHandlers.UHConfModifCollaboration

    def _checkParams(self, params):
        RHConfModifCSBase._checkParams(self, params)

        if self._activeTabName and not self._activeTabName in self._tabs:
            self._cannotViewTab = True
        else:
            self._cannotViewTab = False
            if not self._activeTabName and self._tabs:
                self._activeTabName = self._tabs[0]

            if self._canSeeAllPluginTabs:
                self._tabPlugins = CollaborationTools.getPluginsByTab(self._activeTabName, self._conf)
            else:
                self._tabPlugins = CollaborationTools.getPluginsByTab(self._activeTabName, self._conf, self._getUser())

    def _checkProtection(self):
        if not PluginsHolder().hasPluginType("Collaboration"):
            raise PluginError("Collaboration plugin system is not active")

        hasRights = (not self._cannotViewTab) and \
                    (RCCollaborationAdmin.hasRights(self, None) or
                     RCCollaborationPluginAdmin.hasRights(self, None, self._tabPlugins) or
                     RCVideoServicesManager.hasRights(self, self._tabPlugins) )

        if not hasRights:
            RHConferenceModifBase._checkProtection(self)



    def _process( self ):

        if self._conf.isClosed():
            p = conferences.WPConferenceModificationClosed( self, self._target )
            return p.display()
        else:
            ph = PluginsHolder()
            if ph.getPluginType('Collaboration').getOption("useHTTPS").getValue():
                self._tohttps = True
                if self._checkHttpsRedirect():
                    return ""

            if self._cannotViewTab:
                raise MaKaCError(_("That Video Services tab doesn't exist"), _("Video Services"))
            else:
                p = collaboration.WPConfModifCollaboration( self, self._conf)
                return p.display()


class RHConfModifCSProtection(RHConfModifCSBase):
    _uh = urlHandlers.UHConfModifCollaborationManagers

    def _checkParams(self, params):
        RHConfModifCSBase._checkParams(self, params)
        self._activeTabName = 'Managers'

    def _checkProtection(self):
        if not PluginsHolder().hasPluginType("Collaboration"):
            raise PluginError("Collaboration plugin system is not active")
        if not RCVideoServicesManager.hasRights(self):
            RHConferenceModifBase._checkProtection(self)

    def _process( self ):

        if self._conf.isClosed():
            p = conferences.WPConferenceModificationClosed( self, self._target )
            return p.display()
        else:
            p = collaboration.WPConfModifCollaborationProtection( self, self._conf)
            return p.display()


################################################### Event Display Request Handlers ####################################
class RHCollaborationDisplay(RHConferenceBaseDisplay):
    _uh = urlHandlers.UHCollaborationDisplay

    def _process( self ):
        p = collaboration.WPCollaborationDisplay( self, self._target )
        return p.display()
