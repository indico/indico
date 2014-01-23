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

"""
Contains definitions for the plugin's web interface
"""

# system lib imports
import os, datetime
import pkg_resources

# 3rd party lib imports
import zope.interface
from webassets import Bundle

# plugin imports
from indico.web.assets import PluginEnvironment
from indico.ext.livesync import SyncManager
from indico.ext.livesync.struct import EmptyTrackException
from indico.ext.livesync.handlers import AgentTypeInspector
import indico.ext.livesync

# indico extpoint imports
from indico.core.extpoint import Component
from indico.core.extpoint.plugins import IPluginSettingsContributor
from indico.web.handlers import RHHtdocs
from indico.util.date_time import nowutc, int_timestamp

# legacy indico imports
from MaKaC.webinterface.wcomponents import WTemplated
from MaKaC.webinterface.rh.admins import RHAdminBase
from MaKaC.webinterface.urlHandlers import URLHandler
from MaKaC.webinterface.pages.admins import WPAdminPlugins
from MaKaC.webinterface import wcomponents
from MaKaC.common.info import HelperMaKaCInfo

class UHAdminLiveSyncManagement(URLHandler):
    """URL handler for livesync agent management"""
    _endpoint = 'livesync.manage'


class UHAdminLiveSyncStatus(URLHandler):
    """URL handler for livesync status"""
    _endpoint = 'livesync.status'


# Request Handlers

class RHLiveSyncHtdocs(RHHtdocs):
    """Static file handler for LiveSync plugin"""

    _local_path = pkg_resources.resource_filename(indico.ext.livesync.__name__, "htdocs")
    _min_dir = 'livesync'


class RHAdminLiveSyncManagement(RHAdminBase):
    """LiveSync management page - request handler"""
    def _process(self):
        return WPLiveSyncAdmin(self, WPluginAgentManagement).display()


class RHAdminLiveSyncStatus(RHAdminBase):
    """LiveSync status page - request handler"""

    def _process(self):
        return WPLiveSyncAdmin(self, WPluginAgentStatus).display()


# Plugin Settings

class PluginSettingsContributor(Component):
    """
    Plugs to the IPluginSettingsContributor extension point, providing a "plugin
    settings" web interface
    """

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
        tplVars['statusLiveSyncURL'] = UHAdminLiveSyncStatus.getURL()
        return tplVars


# Settings sub-sections

class WPLiveSyncAdmin(WPAdminPlugins):

    def __init__(self, rh, templateClass):
        WPAdminPlugins.__init__(self, rh, 'livesync', '')
        self._templateClass = templateClass
        info = HelperMaKaCInfo.getMaKaCInfoInstance()
        self._plugin_asset_env = PluginEnvironment('livesync', os.path.dirname(__file__), 'livesync')
        self._plugin_asset_env.debug = info.isDebugActive()
        self._plugin_asset_env.register('livesync_js', Bundle('js/livesync.js',
                                                              filters='rjsmin',
                                                              output="livesync__%(version)s.min.js"))
        self._plugin_asset_env.register('livesync_css', Bundle('css/livesync.css',
                                                               filters='cssmin',
                                                               output="livesync__%(version)s.min.css"))

    def getJSFiles(self):
        return WPAdminPlugins.getJSFiles(self) + \
            self._plugin_asset_env['livesync_js'].urls()

    def getCSSFiles(self):
        return WPAdminPlugins.getCSSFiles(self) + \
            self._plugin_asset_env['livesync_css'].urls()

    def _getPageContent(self, params):
        return wcomponents.WTabControl(self._tabCtrl, self._getAW()).getHTML(
            self._templateClass.forModule(
                indico.ext.livesync).getHTML(params))


class WPluginAgentManagement(WTemplated):

    def getVars(self):
        tplVars = WTemplated.getVars(self)

        smanager = SyncManager.getDBInstance()
        avtypes = AgentTypeInspector.getAvailableTypes()

        tplVars['syncManager'] = smanager
        tplVars['agents'] = smanager.getAllAgents()
        tplVars['availableTypes'] = avtypes.keys()
        tplVars['extraAgentOptions'] = dict((typeName, typeClass._extraOptions)
                                            for (typeName, typeClass) in
                                            avtypes.iteritems())
        tplVars['agentTableData'] = dict((agentId, agent.fossilize()) for \
                                         (agentId, agent) in \
                                         smanager.getAllAgents().iteritems())
        return tplVars


class WPluginAgentStatus(WTemplated):

    NUM_CELLS = 10

    def _tsToDate(self, ts, granularity):
        return datetime.datetime.fromtimestamp(ts * granularity)

    def _calculateTrackData(self, smanager):
        """
        Builds a semi-graphical representation of the current agent status
        """

        # TODO: Reduce, split this!

        track = smanager.getTrack()

        try:
            first = int(track.oldestTS())
            last = int(track.mostRecentTS())
        except EmptyTrackException:
            return None, None

        self._agentMap = {}
        lastAgentTS = 0
        granularity = smanager.getGranularity()

        # create a map of agents, indexed by timestamp
        for aid in smanager.getAllAgents():
            ts = track.getPointerTimestamp(aid)
            if ts:
                ts = int(ts)
                self._agentMap.setdefault(ts, []).append(aid)
                lastAgentTS = max(ts, lastAgentTS)

        queue = []
        self._breakContinuity = False
        extra = self._sumElems = self._numBreakTS = 0

        self._agentsLeft = sorted(self._agentMap)
        self._agentsLeft.reverse()

        for ts, elems in track._container.iteritems():
            if int(ts) in [first, last] or ts in self._agentMap or \
                   extra < self.NUM_CELLS:
                self._drawCell(queue, int(ts), elems,
                               granularity)
                extra += 1
            else:
                self._sumElems += len(elems)
                self._numBreakTS += 1
                self._breakContinuity = True

        for ts in self._agentsLeft:
            self._drawCell(queue, int(ts), [],
                           granularity)

        queue.reverse()

        # return ordered rows
        return queue, lastAgentTS

    def _drawCell(self, queue, ts, elems, granularity):

        if ts not in self._agentMap:
            for agentTS in self._agentsLeft[:]:
                if ts < agentTS:
                    queue.append((agentTS,
                                  self._tsToDate(agentTS, granularity),
                                  0, self._agentMap[agentTS]))
                    self._agentsLeft.remove(agentTS)
        else:
            if ts in self._agentsLeft:
                self._agentsLeft.remove(ts)

        if self._breakContinuity:
            queue.append(('break', self._numBreakTS, self._sumElems, []))

        queue.append((ts, self._tsToDate(ts, granularity),
                          len(elems), self._agentMap.get(ts)))


        self._breakContinuity = False
        self._sumElems = self._numBreakTS = 0

        return 0

    def getVars(self):
        tplVars = WTemplated.getVars(self)

        smanager = SyncManager.getDBInstance()

        tplVars['trackData'], tplVars['lastAgentTS'] = \
                              self._calculateTrackData(smanager)
        tplVars['agents'] = smanager.getAllAgents()
        tplVars['currentTS'] = int_timestamp(nowutc())
        tplVars['granularity'] = smanager.getGranularity()

        return tplVars
