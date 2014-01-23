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

import urllib2, re, urllib, md5
from urllib import urlencode

from MaKaC.plugins.base import PluginsHolder
from MaKaC.webinterface import urlHandlers
from MaKaC.conference import ConferenceHolder

from MaKaC.common.logger import Logger
from MaKaC.common.timezoneUtils import DisplayTZ
from pytz import timezone
from indico.core.extpoint import Component
import indico.ext.search.base
from MaKaC.common.contextManager import ContextManager
from MaKaC.errors import MaKaCError
from MaKaC.common.cache import GenericCache

class Author(object):

    def __init__(self, name, role, affiliation):
        self._name = name
        self._role = role
        self._affiliation = affiliation

    def getName(self):
        return self._name

    def getRole(self):
        return self._role

    def getAffiliation(self):
        return self._affiliation


class SearchResult(object):

    def __init__(self, resultId, title, location, startDate, materials, authors, description):
        self._id = resultId
        self._title = title
        self._location = location
        # convert naive to tz-aware
        if startDate:
            self._startDate = timezone("UTC").localize(startDate)
        else:
            self._startDate = None # no date specified
        self._materials = materials
        self._authors = authors
        self._description = description

    def getId(self):
        return self._id

    def getTitle(self):
        return self._title

    def getStartDate(self, aw):
        tzUtil = DisplayTZ(aw,self.getConference())
        locTZ = tzUtil.getDisplayTZ()
        if self._startDate:
            return self._startDate.astimezone(timezone(locTZ))
        else:
            return None

    def getAuthors(self):
        return self._authors

    def getMaterials(self):
        return self._materials

    def getDescription(self):
        return self._description

    def isVisible(self, user):
        target = self.getTarget()

        if target:
            return target.canView(user)
        else:
            Logger.get('search').warning("referenced element %s does not exist!" % self.getCompoundId())

            return False

    def getConference(self):
        try:
            return ConferenceHolder().getById(self.getConferenceId())
        except:
            return None

    @classmethod
    def create(cls, entryId, title, location, startDate, materials, authors, description):
        raise MaKaCError(_("Method create was not overriden by the search engine."))

class ContributionEntry(SearchResult):

    def __init__(self, entryId, title, location, startDate, materials, authors, description, parent):
        SearchResult.__init__(self, entryId, title, location, startDate, materials, authors, description)

        self._parent = parent

    def getConferenceId(self):
        return self._parent

    def getURL(self):
        return str(urlHandlers.UHContributionDisplay.getURL(confId=self.getConferenceId(), contribId=self.getId()))

    def getCompoundId(self):
        return "%s:%s" % (self._parent, self._id)

    def getTarget(self):

        conference = self.getConference()

        if not conference:
            return None

        return conference.getContributionById(self.getId())


class SubContributionEntry(SearchResult):

    def __init__(self, entryId, title, location, startDate, materials, authors, description, parent, conference):
        SearchResult.__init__(self, entryId, title, location, startDate, materials, authors, description)

        self._parent = parent
        self._conference = conference

        # this was previously done by BibFormat in the old IndicoSearch
        # perhaps it wouldn't be a bad idea to add it as a MARC-XML field,
        # as it happens for contributions
        materials.append((urlHandlers.UHConferenceDisplay.getURL(confId=conference), 'Event details'))

    def getConferenceId(self):
        return self._conference

    def getParent(self):
        return self._parent

    def getURL(self):
        return str(urlHandlers.UHSubContributionDisplay.getURL(confId = self.getConferenceId(), contribId = self.getParent(), subContId = self.getId()))

    def getCompoundId(self):
        return "%s:%s:%s" % (self._conference, self._parent, self._id)

    def getTarget(self):
        conference = self.getConference()

        if not conference:
            return None

        contribution = conference.getContributionById(self.getParent())

        if not contribution:
            return None

        return contribution.getSubContributionById(self.getId())


class ConferenceEntry(SearchResult):

    def getId(self):
        return self._id

    def getURL(self):
        return str(urlHandlers.UHConferenceDisplay.getURL(confId=self.getId()))

    def getCompoundId(self):
        return "%s" % self._id

    def getConferenceId(self):
        return self.getId()

    def getTarget(self):
        return self.getConference()


class SearchEngineAdapter(Component):
    """
        The basic search engine adapter.
        It should be overloaded by the specific SEA class for
        the required search engine.
        It contains:
        - The method to translate the parameters.
        - The basic method that have to be overloaded:
            - process: It will be the main method where the search is done.

        There are 3 types of Search Engine Adapters:
        - Redirect: It redirects to an external server with the query.
        - Call API: Call an API and fetch the results showing in our Indico "results" page.
        - IFrame: Fetch the query in an external server but the results are shown in a IFrame.
    """

    _implementationPackage = indico.ext.search.base
    _allowedParams = {}
    _translationTable = {}

    # PLUGIN RELATED METHODS

    @classmethod
    def getId(self):
        """
        Returns the name of this implementation.
        """
        return self._id

    def getVarFromPluginStorage(self, varName):
        """
        Retrieves varName from the options of the plugin.
        """
        plugin = PluginsHolder().getPluginType('search').getPlugin(self._id)
        return plugin.getOptions()[varName].getValue()

    @classmethod
    def isActive(self):
        """
        Wrapper around the original PluginsHolder method.
        """
        ph = PluginsHolder()
        search = ph.getById('search')
        k = self.getId().lower()

        if not k in search.getPlugins():
            return False
        else:
            return search.getPlugins().get(k).isActive()

    @classmethod
    def getImplementationPackage(self):
        return self._implementationPackage

    def getRequestAddress(self):
        """
            To be overloaded...
            @return: the request address, as a string
        """
        pass

    def addParameters(self, params):
        """
            To be overloaded. Adds parameters to the already existing
            ones (at the end of parameter translation).

            @param params: the already translated request parameters
            @type params: dictionary

            @return: the parameters, with the added parameter(s)
        """
        pass


    def getAllowedParams(self):
        """
            @return: the parameters which the search engine accepts
        """
        return SearchEngineAdapter._allowedParams[self._id]

    def translateParameters(self, kwargs):
        finalArgs = {}

        for outArg, entries in SearchEngineAdapter._translationTable[self._id].iteritems():

            for (origFields, transFunction) in entries:

                if type(origFields) != list:
                    origFields = [origFields]

                values = []
                for field in origFields:
                    if kwargs.has_key(field):
                        values.append(kwargs[field])
                    else:
                        values.append('')

                retArgs = transFunction(self, *values)

                if type(outArg) is tuple :
                    i = 0
                    for destArg in outArg:
                        if not finalArgs.has_key(destArg):
                            finalArgs[destArg] = ''
                        finalArgs[destArg] += retArgs[i]
                        i += 1
                else:
                    if not finalArgs.has_key(outArg):
                        finalArgs[outArg] = ''

                    finalArgs[outArg] += str(retArgs)

        # add extra parameters
        return self.addParameters(finalArgs)

    # MAIN METHOD

    def process(self, filteredParams):
        raise MaKaCError("Method process was not overriden for the search engine " + str(self._id))



class SearchEngineIFrameAdapter(SearchEngineAdapter):
    """
        This Search Engine fetchs the query in an external server but the results are shown in a IFrame.
        The process method should adapt the parameters to their own query.
    """
    def process(self, filteredParams):
        raise MaKaCError("Method process was not overriden for the search engine " + str(self._id))

class SearchEngineCallAPIAdapter(SearchEngineAdapter):
    """
        This Search Engine calls an API and fetch the results showing in our Indico "results" page.
        You need to implement how to get the results from the server (the query parameters) and how to convert
        them into Indico "style".
        A cache system is provided to make the pagination.
    """


    # Methods for cache the pagination. Should be used in the plugin

    def _getQueryHash(self, params):
        keys = params.keys()
        keys.sort()

        # in order to generate the same id for every copy of the
        # same dictionary, we should generated a list, sorted by
        # keys, since this way we guarantee that str() will
        # have always the same output

        uniqueId = str(list((key,params[key]) for key in keys))

        return md5.new(uniqueId).hexdigest()

    def _getStartingRecord(self, queryHash, page):
        obj = GenericCache('Search').get((self._sessionHash, queryHash), {})

        if page == 1:
            Logger.get("search").debug("first page")
            # first page, start with 0
            return 0, None
        elif page in obj:
            Logger.get("search").debug("hit! %s %s" % (obj[page], obj))
            # cache hit!
            return obj[page], obj
        else:
            Logger.get("search").debug("miss")
            # cache miss, force first page to be loaded
            self._page = 1
            return 0, None

    def _cacheNextStartingRecord(self, queryHash, page, record, obj):
        data = obj or {}
        data[self._page+1] = record + 1

        Logger.get("search").debug("set page: %s" % data)
        GenericCache('Search').set((self._sessionHash, queryHash), data, 12*3600)


    def _fetchResultsFromServer(self, service, parameters):
        url = self.getRequestAddress()+'?'+urlencode(parameters)

        req = urllib2.Request(url, None, {'Accept-Charset' : 'utf-8'})
        document = urllib2.urlopen(req)
        text = document.read()

        return (text, self.extractNumHits(text))

    def obtainRecords(self,**kwargs):
        """
            The main processing cycle. Translates the search request parameters
            from the web interface to those of the target search engine.

            @param kwargs: Input parameters

        """

        Logger.get('search.SEA').debug('Translating parameters...')
        finalArgs = self.translateParameters(kwargs)

        Logger.get('search.SEA').debug('Fetching results...')
        (preResults, numPreResults) = self._fetchResultsFromServer(self.getRequestAddress(), finalArgs )

        Logger.get('search.SEA').debug('Preprocessing results...')
        results = self.preProcess(preResults)

        Logger.get('search').debug('Done!')

        return (results, numPreResults)

    def preProcess(self, results):
        """ To be overloaded, """
        pass

    def process(self, filteredParams):
        raise MaKaCError("Method process was not overriden for the search engine " + str(self._id))

class SearchEngineRedirectAdapter(SearchEngineAdapter):
    """
        This Search engine redirects to an external server with the query.
    """
    def process(self, filteredParams):
        searchQuery = self.translateParameters(filteredParams)
        url = self.getRequestAddress()
        ContextManager.get("currentRH")._redirect(url+'?'+urllib.urlencode(searchQuery))

class SEATranslator(object):

    def __init__(self, module):
        self._module = module

    def translate(self, origFields, fieldType, output):

        def factory(method):
            if not SearchEngineAdapter._translationTable.has_key(self._module):
                SearchEngineAdapter._translationTable[self._module] = {}
            if not SearchEngineAdapter._allowedParams.has_key(self._module):
                SearchEngineAdapter._allowedParams[self._module] = []

            if not SearchEngineAdapter._translationTable[self._module].has_key(output):
                SearchEngineAdapter._translationTable[self._module][output] = []

            SearchEngineAdapter._translationTable[self._module][output].append((origFields,method));

            if type(origFields) == list:
                SearchEngineAdapter._allowedParams[self._module].extend(origFields)
            else:
                SearchEngineAdapter._allowedParams[self._module].append(origFields)
        return factory
