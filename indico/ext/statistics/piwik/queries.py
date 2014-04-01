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
import base64
import json
import urllib2
import datetime

from MaKaC.i18n import _

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

    def _buildAPIPath(self, server='secondary'):
        """
        Overridden to ensure that all API calls use the secondary server if
        defined and selected for use.
        """
        PiwikStatisticsImplementation._buildAPIPath(self, server)

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

        params = {'h': time.hour, 'm': time.minute, 's': time.second}
        self.setAPIParams(params)

    def setAPIDownloadLink(self, downloadLink):
        """
        Sets the downloaded URL for tracking, also sets the URL of the tracking
        to the same as per API recommendation.
        """
        self.setAPIParams({'download': urllib2.quote(downloadLink)})
        self.setAPIURL(downloadLink)

    def setAPIURL(self, url):
        self.setAPIParams({'url': urllib2.quote(url)})

    def setAPIVisitorID(self, visitorID):
        self.setAPIParams({'_id': self._generateVisitorID(visitorID)})

    def setAPIRecordMode(self, mode=1):
        """
        This is an int boolean which forces the API into 'record' mode if flag
        is set to 1.
        """
        self.setAPIParams({'rec': mode})

    def setAPIPageTitle(self, title):
        """
        Sets the 'title' of the page, which is to be tracked.
        """
        self.setAPIParams({'action_name': urllib2.quote(title)})

    def setAPISiteID(self, id):
        """
        For some reason, recording to piwik has 'idSite' in the format 'idsite',
        overridden method to allow for this quirk.
        """
        self.setAPIParams({'idsite': id})


class PiwikQueryConferenceBase(PiwikQueryRequestBase):
    """
    To handle all confId / contribId with dates instead of repeated code
    in multiple constructors.
    """

    def __init__(self, startDate, endDate, confId, contribId=None):
        # Keep a reference for instantiating sub-queries
        self._startDate = startDate
        self._endDate = endDate
        self._confId = confId
        self._contribId = contribId

        PiwikQueryRequestBase.__init__(self)

        segmentation = {'customVariablePageName1': ('==', 'Conference'),
                        'customVariablePageValue1': ('==', confId)}

        # If there is a contribution defined for this request, further filter.
        if contribId:
            segmentation['customVariablePageName2'] = ('==', 'Contribution')
            segmentation['customVariablePageValue2'] = ('==', contribId)

        self.setAPISegmentation(segmentation)
        self.setAPIDate([startDate, endDate])


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

    def getQueryResult(self, returnJSON=False):
        """
        Returns the sum of all unique values, typical mode for child
        classes assumed. Overload where required, if no data is received,
        returns the metric as 0.
        """
        queryResult = PiwikQueryUtils.getJSONFromRemoteServer(self._performCall)

        if not queryResult:  # No useful data returned
            return 0

        return queryResult if returnJSON else int(PiwikQueryUtils.getJSONValueSum(queryResult))


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
        self.setAPIMethod('Referrers.getReferrerType')
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


""" Classes which return JSON data from the API """


class PiwikQueryJSONVisitors(PiwikQueryConferenceBase):
    """
    This class returns a JSON of unique & total hits per day, over the date
    range specified and segments via conference ID and/or contribution ID.
    """

    def _buildType(self):
        params = {'startDate': self._startDate,
                  'endDate': self._endDate,
                  'confId': self._confId,
                  'contribId': self._contribId}

        # References to the metrics which we will amalgamate later
        self._metricUnique = PiwikQueryMetricConferenceUniqueVisits(**params)
        self._metricTotal = PiwikQueryMetricConferenceVisits(**params)

    def _parseJSONForAPI(self, json):
        """
        Formats the JSON to be in a more usable syntax, collecting by date.
        """

        cleanJSON = {}

        for hitType, records in json.iteritems():
            for date, hits in records.iteritems():

                if date not in cleanJSON:
                    cleanJSON[date] = {}

                cleanJSON[date][hitType] = int(hits)

        return cleanJSON

    def getQueryResult(self):
        """
        This method prepares and amalgamates the results of self._metricUnique
        and self._metricTotal as they are references to other quieries which,
        here, form the basis of our JSON response.
        """

        raw = {'total_hits': self._metricTotal.getQueryResult(returnJSON=True),
               'unique_hits': self._metricUnique.getQueryResult(returnJSON=True)}

        return self._parseJSONForAPI(raw)


class PiwikQueryJSONDownload(PiwikQueryRequestBase):
    """
    This JSON is agnostic of segmentation (though segmentation is possible)
    as the query string used to download the files is unique, matching the
    Conference and/or Contribution, therefore we can simply query Piwik based
    on this string alone.
    """

    # These links are classed as download, therefore _totalUniqueHits is the
    # individual hosts which are referrers, _totalHitMetric is simply the
    # cumulative number of hits the link has had.
    _totalUniqueHits = 'nb_uniq_visitors'
    _totalHitMetric = 'nb_hits'
    _strTotalHits = 'total_hits'
    _strUniqueHits = 'unique_hits'

    def __init__(self, startDate, endDate, url):
        PiwikQueryRequestBase.__init__(self)
        self.setAPIDownloadURL(url)
        self.setAPIPeriod('day')
        self.setAPIDate([startDate, endDate])

        self._url = url

    def _buildType(self):
        self.setAPIModule('API')
        self.setAPIFormat('JSON')
        self.setAPIMethod('Actions.getDownload')

    def _parseJSONForAPI(self, json, excludeEmptyDates=False):
        """
        Returns a simpler dictionary containing form:
        {'date' : {'total_hits': x, 'unique_hits': y}}
        """
        cleanJSON = {}

        for date, hits in json.iteritems():
            dayHits = {self._strTotalHits: 0, self._strUniqueHits: 0}

            if hits:  # Piwik returns hits as a list of dictionaries, per date.
                for metrics in hits:
                    dayHits[self._strTotalHits] += metrics[self._totalHitMetric]
                    dayHits[self._strUniqueHits] += metrics[self._totalUniqueHits]

            elif excludeEmptyDates:
                continue

            cleanJSON[date] = dayHits

        return cleanJSON

    def _parseJSONForSum(self, json):
        """
        Returns a dictionary of {'total_hits': x, 'unique_hits': y} for the
        date range.
        """
        totalHits = {self._strTotalHits: 0, self._strUniqueHits: 0}

        # Piwik has an odd format of returning this data, dictionaries inside
        # a list of days, reduce it so that we can easily sum.
        dayDicts = list(d[0] for d in json.values() if d)

        for hits in dayDicts:
            totalHits[self._strTotalHits] += hits[self._totalHitMetric]
            totalHits[self._strUniqueHits] += hits[self._totalUniqueHits]

        return totalHits

    def setAPIDownloadURL(self, url):
        """
        Escapes and sets the download URL to match.
        """
        self.setAPIParams({'downloadUrl': urllib2.quote(url)})

    def getURL(self):
        return self._url

    def getQueryResult(self, returnFormatted=False):
        downloadJSON = PiwikQueryUtils.getJSONFromRemoteServer(self._performCall)

        if returnFormatted:

            jsData = {'cumulative': self._parseJSONForSum(downloadJSON),
                      'individual': self._parseJSONForAPI(downloadJSON)}
            return jsData

        return downloadJSON


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
