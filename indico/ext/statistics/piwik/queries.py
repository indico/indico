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
import urllib2
import datetime

from MaKaC.i18n import _
from MaKaC.common.externalOperationsManager import ExternalOperationsManager

from indico.ext.statistics.register import StatisticsConfig
from indico.ext.statistics.piwik.implementation import PiwikStatisticsImplementation


class PiwikQueryUtils():

    @staticmethod
    def getJSONFromRemoteServer(func, default={}, **kwargs):
        """
        Safely manage calls to the remote server by encapsulating JSON creation
        from Piwik data.
        """
        try:
            rawjson = func(kwargs)
            return json.loads(rawjson)
        except:
            # Log the exception and return the default.
            logger = StatisticsConfig().getLogger('PiwikQueryUtils')
            logger.exception('Unable to load JSON from source %s' % str(rawjson))

            return default

    @staticmethod
    def getJSONValueSum(data):
        """
        The parameter data should be a JSON object to be reduced.
        """
        return reduce(lambda x, y: int(x) + int(y), data.values())

    @staticmethod
    def getJSONValueAverage(data):
        """
        The parameter should be a JSON object to be averaged. Returns integer
        value of average.
        """
        total = PiwikQueryUtils.getJSONValueSum(data)

        return total / len(data)

    @staticmethod
    def stringifySeconds(seconds=0):
        """
        Takes time as a value of seconds and deduces the delta in human-readable
        HHh MMm SSs format.
        """
        seconds = int(seconds)
        minutes = seconds / 60
        ti = {'h': 0, 'm': 0, 's': 0}

        if seconds > 0:
            ti['s'] = seconds % 60
            ti['m'] = minutes % 60
            ti['h'] = minutes / 60

        return "%dh %dm %ds" % (ti['h'], ti['m'], ti['s'])


class PiwikQueryBase(PiwikStatisticsImplementation):
    """
    For common methods shared between information recording and retrieval
    with the API.
    """

    def getAPIQuery(self):
        """
        Overridden method call as we will use these queries to populate
        pages with remote data, for most instances, therefore these values
        will be required.
        """
        return super(PiwikQueryBase, self).getAPIQuery(https=True, withScript=True)


class PiwikQueryRequestBase(PiwikQueryBase):
    """
    Base class for all request queries relating to Piwik installations, provides
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


class PiwikQueryTrackBase(PiwikQueryBase):
    """
    Base class for all API calls which do not expect a return, that is such
    requests as server-side tracking.
    """

    QUERY_SCRIPT = 'piwik.php'

    def __init__(self):
        PiwikStatisticsImplementation.__init__(self)
        self.setAPIRecordMode()
        self.setAPITime()

    def _generateVisitorID(self, seed):
        """
        Generates a unique visitor ID based on the seed string provided.
        """
        return base64.b64encode(seed).lower()

    def performCall(self):
        """
        Fires the call against the Piwik installation, by default simply calls
        the _performCall method, to be overloaded with form-specific logic.
        """
        return self._performCall()

    def setAPITime(self, time=None):
        """
        Sets the time variables of h, m & s in the tracking request, if a
        specific time object is given, that is used, if not the current time
        is used.
        """

        if not time or not isinstance(datetime.datetime, time):
            time = datetime.datetime.now()

        params = {'h' : time.hour, 'm' : time.minute, 's' : time.second}
        self.setAPIParams(params)

    def setAPIDownloadLink(self, downloadLink):
        """
        Sets the downloaded URL for tracking, also sets the URL of the tracking
        to the same as per API recommendation.
        """
        self.setAPIParams({'download' : urllib2.quote(downloadLink)})
        self.setAPIURL(downloadLink)

    def setAPIURL(self, url):
        self.setAPIParams({'url' : urllib2.quote(url)})

    def setAPIVisitorID(self, visitorID):
        self.setAPIParams({'_id' : self._generateVisitorID(visitorID)})

    def setAPIRecordMode(self, mode=1):
        """
        This is an int boolean which forces the API into 'record' mode if flag
        is set to 1.
        """
        self.setAPIParams({'rec' : mode})

    def setAPIPageTitle(self, title):
        """
        Sets the 'title' of the page, which is to be tracked.
        """
        self.setAPIParams({'action_name' : urllib2.quote(title)})

    def setAPISiteID(self, id):
        """
        For some reason, recording to piwik has 'idSite' in the format 'idsite',
        overridden method to allow for this quirk.
        """
        self.setAPIParams({'idsite' : id})


class PiwikQueryConferenceBase(PiwikQueryRequestBase):
    """
    To handle all confId / contribId with dates instead of repeated code
    in multiple constructors.
    """

    def __init__(self, startDate, endDate, confId, contribId=None):
        PiwikQueryRequestBase.__init__(self)
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
        PNGData = self._performCall(default='none')

        if PNGData != 'none':
            b64ImgCode = base64.b64encode(PNGData)

            return b64ImgPrefix + b64ImgCode
        else:
            return PNGData

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
Classes for returning individual metrics (string or int values) from the API.
"""


class PiwikQueryMetricConferenceBase(PiwikQueryConferenceBase):

    def _buildType(self):
        self.setAPIModule('API')
        self.setAPIFormat()

    def getQueryResult(self):
        """
        Returns the sum of all unique values, typical mode for child
        classes assumed. Overload where required, if no data is received,
        returns the metric as 0.
        """
        queryResult = PiwikQueryUtils.getJSONFromRemoteServer(self._performCall)

        return int(PiwikQueryUtils.getJSONValueSum(queryResult)) if queryResult else 0


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
        self.setAPIMethod('VisitsSummary.get')

    def _getAverages(self, data):
        """
        The resultant JSON of this call returns a list containing the average
        for each day, hence we need to build the total and average it accordingly.
        """

        if len(data) == 0:
            return 0

        seconds = 0
        avgKey = 'avg_time_on_site'

        for day in data:
            # Check if the day has stastistics, because if it does not the day will be a empty list
            if isinstance(day, dict):
                seconds += day.get(avgKey, 0)

        return seconds / len(data)

    def getQueryResult(self):
        """
        Returns a string of the time in hh:mm:ss
        """
        data = PiwikQueryUtils.getJSONFromRemoteServer(self._performCall)
        seconds = 0

        if data:
            seconds = self._getAverages(data.values())

        return PiwikQueryUtils.stringifySeconds(seconds)


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
        jdata = PiwikQueryUtils.getJSONFromRemoteServer(self._performCall)
        referrers = list(jdata)

        for referrer in referrers:
            referrer['sum_visit_length'] = PiwikQueryUtils.stringifySeconds(referrer['sum_visit_length'])

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

        jData = PiwikQueryUtils.getJSONFromRemoteServer(self._performCall)

        if len(jData) > 0:
            date, value = max(jData.iteritems(), key=lambda e: e[1])
            return {'date': date, 'users': value}
        else:
            return {'date': _('No Data'), 'users': 0}


class PiwikQueryMetricDownload(PiwikQueryRequestBase):
    """
    This metric is agnostic of segmentation (though segmentation is possible)
    as the query string used to download the files is unique, matching the
    Conference and/or Contribution, therefore we can simply query Piwik based
    on this string alone.
    """

    def __init__(self, url):
        PiwikQueryRequestBase.__init__(self)
        self.setAPIDownloadURL(url)
        self._url = url

    def _parseJSONForAPI(self, json):
        """
        Returns a simpler dictionary containing form:
        {'date' : {'total_hits' : x, 'unique_hits' : y}}
        """
        cleanJSON = {}

        for date in json.keys():
            hits = json.get(date)

            dayHits = {'total_hits' : 0,
                       'unique_hits' : 0}

            if hits:
                # Piwik returns hits as a list of dictionaries, per date.
                for metrics in hits:

                    dayHits['total_hits'] += metrics['nb_hits']
                    dayHits['unique_hits'] += metrics['nb_uniq_visitors']

            cleanJSON[date] = dayHits

        return cleanJSON

    def _parseJSONForReduction(self, json):
        """
        Iterates through
        """
        pass

    def setAPIDownloadURL(self, url):
        """
        Escapes and sets the download URL to match.
        """
        self.setAPIParams({'downloadUrl' : urllib2.quote(url)})

    def _buildType(self):
        self.setAPIModule('API')
        self.setAPIFormat('JSON')
        self.setAPIMethod('Actions.getDownload')

    def getURL(self):
        return self._url

    def getQueryResult(self, returnAsJSON=False):
        downloadJSON = PiwikQueryUtils.getJSONFromRemoteServer(self._performCall)

        if returnAsJSON:
            return self._parseJSONForAPI(downloadJSON)

        return downloadJSON


class PiwikQueryMetricMultipleDownloads():
    """
    This class acts as a wrapped around multiple download requests as Piwik
    only permits retrieval one at a time.
    """

    def __init__(self, urls):
        self._resetDownloads()
        self.setAPIDownloadURLs(urls)

    def _hasDownloads(self):
        return bool(self._downloads)

    def _resetDownloads(self):
        self._downloads = {}

    def setDownloadURLs(self, urls, reset=False):
        if not isinstance(list, urls):
            raise Exception(_('This method must be passed a list of URLs.'))

        if reset:
            self._resetDownloads()

        for url in urls:
            self._downloads.append(PiwikQueryMetricDownload(url))

    def getQueryResult(self, returnAsJson=False):
        result = {}

        for download in self._downloads:
            result[download.getURL()] = download.getQueryResult(returnAsJson)


class PiwikQueryTrackDownload(PiwikQueryTrackBase):

    def __init__(self):
        PiwikQueryTrackBase.__init__(self)
        # See setAPISiteID in PiwikQueryTrackBase for reason it's 'idsite' here.
        self._requiredParams = ['h', 'm', 's', 'idsite', 'download',
                                'action_name']

    def trackDownload(self, downloadLink, downloadTitle):
        """
        Tracks the download in Piwik with the link to track and the title
        with which to track it. If either of which are not set, don't commit
        as the data integrity would be jeapordised.
        """
        if not downloadLink or not downloadTitle:
            return False

        self.setAPIPageTitle(downloadTitle)
        self.setAPIDownloadLink(downloadLink)

        self.performCall()
