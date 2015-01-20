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

from MaKaC.plugins.base import ActionBase
from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools
from MaKaC.conference import ConferenceHolder
from MaKaC.common.indexes import IndexesHolder
from MaKaC.plugins.Collaboration.indexes import IndexInformation
from MaKaC.plugins.Collaboration.base import CollaborationException
from indico.core.index import Catalog

pluginTypeActions = [
    ("indexPluginsPerEventType", {"visible": False,
                                 "executeOnLoad": True,
                                 "triggeredBy": ["allowedOn"]} ),
    ("indexPluginsPerIndex", {"visible": False,
                               "executeOnLoad": True}),
    ("reindexAllBookings", {"buttonText": "Reindex ALL bookings (may take a while)", "visible": False}),
    ("deleteAllBookings", {"buttonText": "Delete ALL bookings (only to be used by David) (be careful)",
                           "visible": False})
]

class IndexPluginsPerEventTypeAction(ActionBase):

    def call(self):
        allowedPlugins = {"conference": [], "meeting": [], "simple_event": []}
        for plugin in self._pluginType.getPluginList(includeNonActive = True):
            allowedOn = CollaborationTools.getPluginAllowedOn(plugin)
            for eventType in allowedOn:
                try:
                    allowedPlugins[eventType].append(plugin)
                except KeyError,e:
                    raise CollaborationException("Allowed kinds of events: conference, meeting, simple_event. %s is not allowed" % str(eventType), inner = e)

        self._pluginType.getOption("pluginsPerEventType").setValue(allowedPlugins)

class IndexPluginsPerIndexAction(ActionBase):

    def call(self):
        result = []
        itiAll = IndexInformation("all")
        pluginIndexes = []
        commonIndexes = {}
        plugins = self._pluginType.getPluginList(doSort = True, includeNonActive = True)
        pluginNames = [p.getId() for p in plugins if p.isActive()]

        for pluginName in pluginNames:
            csBookingClass = CollaborationTools.getCSBookingClass(pluginName)

            if not csBookingClass._shouldBeIndexed:
                continue
            itiAll.addPlugin(pluginName)
            if csBookingClass._hasAcceptReject:
                itiAll.setHasShowOnlyPending(True)
            if csBookingClass._hasStartDate:
                itiAll.setHasViewByStartDate(True)

            iti = IndexInformation(pluginName)
            iti.addPlugin(pluginName)
            iti.setHasShowOnlyPending(csBookingClass._hasAcceptReject)
            iti.setHasViewByStartDate(csBookingClass._hasStartDate)
            pluginIndexes.append(iti)

            for commonIndexName in csBookingClass._commonIndexes:
                if not commonIndexName in commonIndexes:
                    commonIndexes[commonIndexName] = IndexInformation(commonIndexName)
                iti = commonIndexes[commonIndexName]
                iti.addPlugin(pluginName)
                if csBookingClass._hasAcceptReject:
                    iti.setHasShowOnlyPending(True)
                if csBookingClass._hasStartDate:
                    iti.setHasViewByStartDate(True)

        commonIndexNames = commonIndexes.keys()
        commonIndexNames.sort()

        result.append(itiAll)
        result.extend(pluginIndexes)
        result.append(IndexInformation("requests"))
        result.extend([commonIndexes[k] for k in commonIndexNames])

        self._pluginType.getOption("pluginsPerIndex").setValue(result)

class ReindexAllBookingsAction(ActionBase):

    def call(self):
        collaborationIndex = IndexesHolder().getById("collaboration")
        collaborationIndex.reindexAll()

class DeleteAllBookingsAction(ActionBase):

    def call(self):
        cf = ConferenceHolder()
        for conf in cf.getValuesToList():
            csbm = Catalog.getIdx("cs_bookingmanager_conference").get(conf.getId())
            csbm._bookings = {}
            csbm._bookingsByType = {}
        collaborationIndex = IndexesHolder().getById("collaboration")
        collaborationIndex.cleanAll()
