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
import base64
import json

from MaKaC.i18n import _

from indico.ext.statistics.piwik.implementation import PiwikStatisticsImplementation


class PiwikQueryBase(PiwikStatisticsImplementation):
    """
    Base class for all queries relating to Piwik installations, provides
    a series of methods which map against expected variables in the Piwik
    API.
    """

    QUERY_SCRIPT = 'index.php'  # Different script target for queries than tracking.

    def __init__(self):
        super(PiwikQueryBase, self).__init__()
        self._APIRequiredParams = ['date', 'period', 'idSite']
        self._APISegmentation = []
        self.setAPIDate()
        self.setAPIPeriod()
        self._buildType()

    def _buildType(self):
        """
        To be overloaded by inheriting classes, widget / image etc specific
        parameters.
        """
        pass

    def getAPIQuery(self):
        """
        Overridden method call as we will use these queries to populate
        pages with remote data, for most instances, therefore these values
        will be required.
        """
        return super(PiwikQueryBase, self).getAPIQuery(https=True, withScript=True)


class PiwikQueryConferenceBase(PiwikQueryBase):
    """
    To handle all confId / contribId with dates instead of repeated code
    in multiple constructors.
    """

    def __init__(self, startDate, endDate, confId, contribId=None):
        PiwikQueryBase.__init__(self)
        segmentation = {'customVariablePageName1': ('==', 'Conference'),
                        'customVariablePageValue1': ('==', confId)}

        # If there is a contribution defined for this request, further filter.
        if contribId:
            segmentation['customVariablePageName2'] = ('==', 'Contribution')
            segmentation['customVariablePageValue2'] = ('==', contribId)

        self.setAPISegmentation(segmentation)
        self.setAPIDate([startDate, endDate])


""" Classes for returning iframe URLs relating to Piwik API Widgets. """


class PiwikQueryWidgetConferenceBase(PiwikQueryConferenceBase):
    """
    A Piwik Widget is intended to be the source of an iframe, therefore
    any objects inheriting from this class should have the resultant
    getAPIQuery() value placed into an iframe tag for use.
    """

    def _buildType(self):
        otherParams = {'widget': '1',
                       'disableLink': '1'}
        self.setAPIModule('Widgetize')
        self.setAPIAction('iframe')
        self.setAPIParams(otherParams)
        self.setAPIPeriod('range')

    def getQueryResult(self):
        return self.getAPIQuery()

    def setAPIModuleToWidgetize(self, module):
        self.setAPIParams({'moduleToWidgetize': module})

    def setAPIActionToWidgetize(self, action):
        self.setAPIParams({'actionToWidgetize': action})


class PiwikQueryWidgetConferenceWorldMap(PiwikQueryWidgetConferenceBase):

    def _buildType(self):
        super(PiwikQueryWidgetConferenceWorldMap, self)._buildType()
        self.setAPIModuleToWidgetize('UserCountryMap')
        self.setAPIActionToWidgetize('worldMap')


class PiwikQueryWidgetConferenceStats(PiwikQueryWidgetConferenceBase):

    def _buildType(self):
        super(PiwikQueryWidgetConferenceStats, self)._buildType()
        self.setAPIModuleToWidgetize('VisitFrequency')
        self.setAPIActionToWidgetize('getSparklines')


""" Classes for returning PNG static Graph images from the API. """


class PiwikQueryGraphConferenceBase(PiwikQueryConferenceBase):
    """
    The Piwik API has the option to return PNG format graphs through
    the use of a query string, objects which inherit from this class afford
    an interface to easily retrieve such PNG data.
    """

    def _buildType(self):
        self.setAPIMethod('ImageGraph.get')
        self.setAPIModule('API')

    def getQueryResult(self):
        """
        Sends a request to the API for the PNG graph data, encodes and
        prefixes the result to be inserted into the 'src' attribute
        of a HTML img tag, thus obfuscating token.
        """
        b64ImgPrefix = 'data:image/png;base64,'
        b64ImgCode = base64.b64encode(self._performCall())

        return b64ImgPrefix + b64ImgCode

    def setAPIGraphType(self, graph='verticalBar'):
        self.setAPIParams({'graphType': graph})

    def setAPIGraphDimensions(self, width=None, height=None):
        if height:
            self.setAPIParams({'height': height})
        if width:
            self.setAPIParams({'width': width})

    def setAPIGraphAliasing(self, aliasing):
        """
        Aliasing should be 1 or 0 for True & False respectively, if
        enabled Graphs will be prettier but more expensive.
        """
        self.setAPIParams({'aliasedGraph': str(aliasing)})


class PiwikQueryGraphConferenceVisits(PiwikQueryGraphConferenceBase):
    """
    Returns a PNG graphic graph of visits to the conference defined between
    the specified date range.
    """

    def _buildType(self):
        super(PiwikQueryGraphConferenceVisits, self)._buildType()
        self.setAPIInnerModule('VisitsSummary')
        self.setAPIInnerAction('get')
        self.setAPIGraphType('evolution')
        self.setAPIGraphDimensions(720, 260)


class PiwikQueryGraphConferenceDevices(PiwikQueryGraphConferenceBase):

    def _buildType(self):
        PiwikQueryGraphConferenceBase._buildType(self)
        self.setAPIInnerModule('UserSettings')
        self.setAPIInnerAction('getOS')
        self.setAPIGraphType('horizontalBar')
        self.setAPIGraphDimensions(320, 260)
        self.setAPIPeriod('range')


class PiwikQueryGraphConferenceCountries(PiwikQueryGraphConferenceBase):

    def _buildType(self):
        PiwikQueryGraphConferenceBase._buildType(self)
        self.setAPIInnerModule('UserCountry')
        self.setAPIInnerAction('getCountry')
        self.setAPIGraphType('horizontalBar')
        self.setAPIGraphDimensions(490, 260)
        self.setAPIPeriod('range')


"""
Classes for returning individual metrics (string or int values) from theAPI.
"""


class PiwikQueryMetricConferenceBase(PiwikQueryConferenceBase):

    def _buildType(self):
        self.setAPIModule('API')
        self.setAPIFormat()

    def _getJSONValueSum(self, data):
        """
        Assumes format of key: value to iterate and add all values
        returned.
        """
        jsData = json.loads(data)
        return reduce(lambda x, y: int(x) + int(y), jsData.values())

    def _stringifySeconds(self, seconds=0):
        """
        Takes time as a value of seconds and deduces the delta in human-readable
        HHh MMm SSs format.
        """
        seconds = int(seconds)
        minutes = seconds / 60
        ti = {'h': 0, 'm': 0, 's': 0}

        ti['s'] = seconds % 60
        ti['m'] = minutes % 60
        ti['h'] = minutes / 60

        return "%dh %dm %ds" % (ti['h'], ti['m'], ti['s'])

    def getQueryResult(self):
        """
        Returns the sum of all unique values, typical mode for child
        classes assumed. Overload where required.
        """
        return self._getJSONValueSum(self._performCall())


class PiwikQueryMetricConferenceUniqueVisits(PiwikQueryMetricConferenceBase):

    def _buildType(self):
        PiwikQueryMetricConferenceBase._buildType(self)
        self.setAPIMethod('VisitsSummary.getUniqueVisitors')


class PiwikQueryMetricConferenceVisits(PiwikQueryMetricConferenceBase):

    def _buildType(self):
        PiwikQueryMetricConferenceBase._buildType(self)
        self.setAPIMethod('VisitsSummary.getVisits')


class PiwikQueryMetricConferenceVisitLength(PiwikQueryMetricConferenceBase):

    def _buildType(self):
        PiwikQueryMetricConferenceBase._buildType(self)
        self.setAPIMethod('VisitsSummary.getSumVisitsLength')

    def getQueryResult(self):
        """
        Returns a string of the time in hh:mm:ss
        """
        data = self._performCall()
        seconds = self._getJSONValueSum(data)

        return self._stringifySeconds(seconds)


class PiwikQueryMetricConferenceReferrers(PiwikQueryMetricConferenceBase):

    def _buildType(self):
        PiwikQueryMetricConferenceBase._buildType(self)
        self.setAPIMethod('Referers.getRefererType')
        self.setAPIPeriod('range')

    def getQueryResult(self):
        """
        API returns a list of referrers in the JSON format, unserialize and
        commit to a Python list of dictionaries before returning.
        """
        rawjson = self._performCall()
        jdata = json.loads(rawjson)
        referrers = list(jdata)

        for referrer in referrers:
            referrer['sum_visit_length'] = self._stringifySeconds(referrer['sum_visit_length'])

        return sorted(referrers, key=lambda r: r['nb_visits'], reverse=True)[0:10]


class PiwikQueryMetricConferencePeakDateAndVisitors(PiwikQueryMetricConferenceBase):

    def _buildType(self):
        PiwikQueryMetricConferenceBase._buildType(self)
        self.setAPIMethod('VisitsSummary.getVisits')
        self.setAPIPeriod('day')

    def getQueryResult(self):
        """
        This algorithm is a bit dumb as it assumes no two dates can be
        tied for the most hits. Could do with some more mining to ascertain
        which was the busiest overall, considering uniquevistors &
        actions.
        """
        data = self._performCall()
        jData = json.loads(data)
        winner = {}
        val = 0

        for date in jData.keys():
            if jData.get(date) > val:
                val = jData.get(date)
                winner = {'date': date, 'users': jData.get(date)}

        return winner if winner else {'date': _('No Data'), 'users': '0'}
