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
import indico.ext.statistics.piwik.queries as pq

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


class MaterialStatistics(PiwikService):
    """
    Service for returning JSON object relating to material downloads
    over a given date range.
    """

    def _checkParams(self):
        PiwikService._checkParams(self)
        self._materialURL = self._params['materialURL']

    def _getAnswer(self):
        materialStats = pq.PiwikQueryMetricDownload(self._startDate,
                                                    self._endDate,
                                                    self._materialURL)

        return materialStats.getQueryResult(returnJSON=True)


class MaterialTreeService(PiwikService):
    """
    HTTP method for getting the Material dictionary of a Conference in
    the format jqTree expects.
    """

    TREE_STR_LIMIT = 24

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
    "piwik.getMaterialTreeData": MaterialTreeService
}
