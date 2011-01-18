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

"""
Contains definitions for the plugin's web interface
"""

# system lib imports
import os, datetime

# 3rd party lib imports
import zope.interface

# plugin imports
from indico.ext.livesync import SyncManager
from indico.ext.livesync.struct import EmptyTrackException
from indico.ext.livesync.handlers import AgentTypeInspector
from indico.ext.livesync.base import MPT_GRANULARITY
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
    """
    URL handler for livesync agent management
    """
    _relativeURL = "livesync/manage"


class UHAdminLiveSyncStatus(URLHandler):
    """
    URL handler for livesync status
    """
    _relativeURL = "livesync/status"


# Request Handlers

class RHLiveSyncHtdocs(RHHtdocs):
    """
    Static file handler for LiveSync plugin
    """

    _url = r"^/livesync/(?P<filepath>.*)$"
    _local_path = os.path.join(indico.ext.livesync.__path__[0], 'htdocs')


class RHAdminLiveSyncManagement(RHAdminBase):
    """
    LiveSync management page - request handler
    """
    _url = r'^/livesync/manage/?$'

    def _process(self):
        return WPLiveSyncAdmin(self, WPluginAgentManagement).display()


class RHAdminLiveSyncStatus(RHAdminBase):
    """
    LiveSync status page - request handler
    """
    _url = r'^/livesync/status/?$'

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

    def getJSFiles(self):
        return WPAdminPlugins.getJSFiles(self) + \
               self._includeJSFile('livesync/js', 'livesync')

    def getCSSFiles(self):
        return WPAdminPlugins.getCSSFiles(self) + \
               ['livesync/livesync.css']

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


NUM_CELLS = 10


class WPluginAgentStatus(WTemplated):

    def _tsToDate(self, ts):
        return datetime.datetime.utcfromtimestamp(ts * MPT_GRANULARITY)

    def _calculateTrackData(self, smanager):
        """
        Builds a semi-graphical representation of the current agent status
        """
        track = smanager.getTrack()

        try:
            first, last = int(track.oldestTS()), int(track.mostRecentTS())

            agentMap = {}
            lastAgentTS = 0

            # create a map of agents, indexed by timestamp
            for aid in smanager.getAllAgents():
                ts = track.getPointerTimestamp(aid)
                if ts:
                    ts = int(ts)
                    agentMap.setdefault(ts, []).append(aid)
                    lastAgentTS = max(ts, lastAgentTS)

            queue = []

            showTS = breakContinuity = False
            extra = sumElems = numBreakTS = 0

            for ts, elems in track._container.iteritems():

                ts = int(ts)
                showTS = ts == first or ts in agentMap

                if showTS or extra < 10:
                    if breakContinuity:
                        queue.append(('break', numBreakTS, sumElems, []))
                    queue.append((ts, self._tsToDate(ts),
                                  len(elems), agentMap.get(ts, [])))
                    breakContinuity = False
                    sumElems = numBreakTS = 0
                    if not showTS:
                        extra += 1
                else:
                    sumElems += len(elems)
                    numBreakTS += 1
                    breakContinuity = True

            queue.reverse()

            # return ordered rows
            return queue, lastAgentTS

        except EmptyTrackException:
            return None, None

    def getVars(self):
        tplVars = WTemplated.getVars(self)

        smanager = SyncManager.getDBInstance()

        tplVars['trackData'], tplVars['lastAgentTS'] = \
                              self._calculateTrackData(smanager)
        tplVars['agents'] = smanager.getAllAgents()
        return tplVars
