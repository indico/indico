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

# system lib imports
import os

# 3rd party lib imports
import zope.interface

# plugin imports
from indico.ext.livesync import SyncManager
from indico.ext.livesync.handlers import AgentTypeInspector
import indico.ext.livesync

# indico api imports
from indico.core.api import Component
from indico.core.api.plugins import IPluginSettingsContributor
from indico.web.rh import RHHtdocs

# legacy indico imports
from MaKaC.webinterface.wcomponents import WTemplated
from MaKaC.webinterface.rh.admins import RHAdminBase
from MaKaC.webinterface.urlHandlers import URLHandler
from MaKaC.webinterface.pages.admins import WPAdminPlugins
from MaKaC.webinterface import wcomponents


class UHAdminLiveSyncManagement(URLHandler):
    _relativeURL = "livesync/manage"


# Request Handlers

class RHLiveSyncHtdocs(RHHtdocs):

    _url = r"^/livesync/htdocs/(?P<filepath>.*)$"
    _local_path = os.path.join(indico.ext.livesync.__path__[0], 'htdocs')


class RHAdminLiveSyncManagement(RHAdminBase):

    _url = r'^/livesync/manage/?$'

    def _process(self):
        return WPPluginAgentManagement(self, 'livesync', '').display()


# Plugin Settings

class PluginSettingsContributor(Component):

    zope.interface.implements(IPluginSettingsContributor)

    def hasPluginSettings(self, obj, ptype, plugin):
        if ptype == 'livesync' and plugin == None:
            return True
        else:
            return False

    def getPluginSettingsHTML(self, obj, ptype, plugin):
        if ptype == 'livesync' and plugin == None:
            return WPluginSettings.forModule(indico.ext.livesync).getHTML()
        else:
            return None


class WPluginSettings(WTemplated):

    def getVars(self):
        tplVars = WTemplated.getVars(self)
        tplVars['adminLiveSyncURL'] = UHAdminLiveSyncManagement.getURL()
        return tplVars


# Settings sub-sections

class WPPluginAgentManagement(WPAdminPlugins):

    def getJSFiles(self):
        return WPAdminPlugins.getJSFiles(self) + \
               self._includeJSFile('livesync/htdocs/js', 'livesync')

    def _getPageContent(self, params):
        return wcomponents.WTabControl( self._tabCtrl, self._getAW() ).getHTML(
            WPluginAgentManagement.forModule(indico.ext.livesync).getHTML(params))


class WPluginAgentManagement(WTemplated):

    def getVars(self):
        tplVars = WTemplated.getVars(self)

        smanager = SyncManager.getDBInstance()

        avtypes = AgentTypeInspector.getAvailableTypes()

        tplVars['syncManager'] = smanager
        tplVars['agents'] = smanager.getAllAgents()
        tplVars['availableTypes'] = avtypes.keys()
        tplVars['extraAgentOptions'] = dict((typeName, typeClass._extraOptions) for
                                            (typeName, typeClass) in
                                            avtypes.iteritems())
        tplVars['agentTableData'] = dict((agentId, agent.fossilize()) for \
                                         (agentId, agent) in smanager.getAllAgents().iteritems())

        return tplVars
