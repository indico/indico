# -*- coding: utf-8 -*-
##
##
## This file is part of Indico
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN)
##
## Indico is free software: you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation, either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico.  If not, see <http://www.gnu.org/licenses/>.
import indico.ext.statistics.piwik.queries as pq

from indico.ext.statistics.base.implementation import BaseStatisticsImplementation

from MaKaC.services.implementation.conference import ConferenceModifBase
from MaKaC.conference import ConferenceHolder


class PiwikService(ConferenceModifBase):
    """
    Base service for handling shared components across the Piwik AJAX
    requests.
    """

    def _checkParams(self):
        ConferenceModifBase._checkParams(self)

        if 'startDate' in self._params:
            self._startDate = self._params['startDate']
        if 'endDate' in self._params:
            self._endDate = self._params['endDate']


class PiwikConferenceService(PiwikService):
    """
    Handles requests which need conferenceID and/or contributionID
    """

    def _checkParams(self):
        PiwikService._checkParams(self)

        self._confId = self._params['confId']

        # Treat this as a flag to test against later for segmentation.
        if 'contribId' in self._params:
            self._contribId = self._params['contribId']
        else:
            self._contribId = None


class MaterialStatistics(PiwikService):
    """
    Service for returning a JSON object relating to material downloads
    over a given date range.
    """

    def _checkParams(self):
        PiwikService._checkParams(self)
        self._materialURL = self._params['materialURL']

    @BaseStatisticsImplementation.memoizeReport
    def _getAnswer(self):
        materialStats = pq.PiwikQueryJSONDownload(self._startDate,
                                                  self._endDate,
                                                  self._materialURL)

        return materialStats.getQueryResult(returnFormatted=True)


class EventVisitsStatistics(PiwikConferenceService):
    """
    Service for returning a JSON object of the number of visits to an event
    over time.
    """

    @BaseStatisticsImplementation.memoizeReport
    def _getAnswer(self):
        visitStats = pq.PiwikQueryJSONVisitors(self._startDate,
                                               self._endDate,
                                               self._confId,
                                               self._contribId)

        return visitStats.getQueryResult()


class EventGraphGeographyStatistics(PiwikConferenceService):
    """
    Service which provides Base64 encoded PNG data for the graph covering
    visitor geography.
    """

    @BaseStatisticsImplementation.memoizeReport
    def _getAnswer(self):
        geography = pq.PiwikQueryGraphConferenceCountries(self._startDate,
                                                          self._endDate,
                                                          self._confId,
                                                          self._contribId)

        return geography.getQueryResult()


class EventGraphDeviceStatistics(PiwikConferenceService):
    """
    Service which provides Base64 encoded PNG data for the graph covering
    visitor device origin.
    """

    @BaseStatisticsImplementation.memoizeReport
    def _getAnswer(self):
        devices = pq.PiwikQueryGraphConferenceDevices(self._startDate,
                                                      self._endDate,
                                                      self._confId,
                                                      self._contribId)

        return devices.getQueryResult()


class MaterialTreeService(PiwikService):
    """
    HTTP method for getting the Material dictionary of a Conference in
    the format jqTree expects.
    """

    TREE_STR_LIMIT = 24

    @BaseStatisticsImplementation.memoizeReport
    def _getAnswer(self):
        confId = self._conf.getId()
        conference = ConferenceHolder().getById(confId)
        material = conference.getAllMaterialDict()

        return self.formatForJQTree(material, returnAsList=True)

    def formatForJQTree(self, child, returnAsList=False):
        """
        Wraps around the JSON output in Conference to the specific
        format required by jqTree.
        """

        node = {}
        node['label'] = child['title']
        node['children'] = []

        for key, value in child.iteritems():

            if key not in ['children', 'material']:  # Performance only
                continue

            children = []

            if key == 'children' and len(value) > 0:

                for child in value:
                    newNode = self.formatForJQTree(child)

                    if newNode:
                        children.append(newNode)

            if key == 'material' and len(value) > 0:

                for material in value:
                    newNode = {}
                    newNode['label'] = material['title']
                    newNode['id'] = material['url']

                    children.append(newNode)

            if children:
                node['children'].extend(children)

        # If the node has no children (i.e. Sessions, Contributions & Material,
        # then there is no point in displaying it in the tree.
        if len(node['children']) > 0:

            self.shortenNodeLabel(node)

            for child in node['children']:
                self.shortenNodeLabel(child)

            return [node] if returnAsList else node
        else:
            return None

    def shortenNodeLabel(self, node):
        """
        We don't want the strings to be massive in the labels, truncate them
        to make the tree more manageable.
        """
        if len(node['label']) > self.TREE_STR_LIMIT:
            node['label'] = node['label'][:self.TREE_STR_LIMIT] + '...'


methodMap = {
    "piwik.getMaterialStatistics": MaterialStatistics,
    "piwik.getMaterialTreeData": MaterialTreeService,
    "piwik.getEventVisits": EventVisitsStatistics,
    "piwik.getGeographyGraph": EventGraphGeographyStatistics,
    "piwik.getDevicesGraph": EventGraphDeviceStatistics
}
