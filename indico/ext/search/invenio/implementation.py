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
from flask import session

import os, re, datetime, cgi, time, copy
from indico.ext.search.base.implementation import SearchEngineCallAPIAdapter, SearchEngineRedirectAdapter, Author, SearchResult, SubContributionEntry, ContributionEntry, ConferenceEntry, SEATranslator
import indico.ext.search.invenio
import MaKaC.conference as conference
from indico.core.config import Config
from MaKaC.common.output import XSLTransformer
from MaKaC.common.logger import Logger
from MaKaC.common.contextManager import ContextManager

from xml.dom import minidom

SEA = SEATranslator("invenio")

class InvenioSearchResult(SearchResult):
    @classmethod
    def create(cls, entryId, title, location, startDate, materials, authors, description):

        regexp = r'^INDICO\.(\w+)(\.(\w+)(\.(\w)+)?)?$'

        m = re.match(regexp, str(entryId))

        if m:
            if m.group(4):
                return SubContributionEntry(m.group(5), title, location, startDate, materials, authors, description, m.group(3), m.group(1))
            elif m.group(2):
                return ContributionEntry(m.group(3), title, location, startDate, materials, authors, description, m.group(1))
            else:
                return ConferenceEntry(m.group(1), title, location, startDate, materials, authors, description)
        else:
            raise Exception('unrecognized id format: %s' % id)

class InvenioBaseSEA:
    _id = "invenio"

    def __init__(self, **params):
        self._userLoggedIn = params.get("userLoggedIn", False)
        self._target = params.get("target", None)
        self._page = params.get("page", 1)
        self._noQuery = False

        if self._userLoggedIn:
            self._sessionHash = '%s_%s' % (session.sid, session.user.getId())
        else:
            self._sessionHash = 'PUBLIC'

        if type(self._target) == conference.Category:
            # we're dealing with a category
            if self._target.isRoot():
                # perform global search
                self._marcQuery = ''
            else:
                # if not on root, search using path
                self._marcQuery = '650_7:"'+self._buildCategoryHierarchy(self._target)+'*" '

        elif type(self._target) == conference.Conference:
            # we're looking inside an event
            # search for event identifier
            self._marcQuery = 'AND 970__a:"INDICO.%s.*"' % self._target.getId()
            self._searchCategories = False

        else:
            raise Exception("Unknown target type.")

    def _buildCategoryHierarchy(self, target):
        """
            Builds a category path, separated by ':', as indicosearch wishes.
        """
        return ':'.join(target.getCategoryPath())

    def getRequestAddress(self):
        return self.getVarFromPluginStorage("serverUrl")

    def isSearchTypeOnlyPublic(self):
        return self.getVarFromPluginStorage("type") != "private"

    ## Now, we have the actual translation rules
    ## Notice that the second parameter of SEATranslator is
    ## currently not being used.
    ##
    ## '@SEATranslator(sourceField, type, targetField)'

    @SEA.translate ('f',[],'p')
    def translateFieldAuthor(self, field):
        if field == "author":
            return "author:"
        else:
            return ""

    @SEA.translate ('p', 'text', 'p')
    def translatePhrase(self, phrase):
        return phrase + ' ' + self._marcQuery

    @SEA.translate(['startDate', 'endDate'],'date', 'p')
    def translateDates(self, startDate, endDate):

        if startDate != '':
            startDate = time.strftime("%Y-%m-%d", time.strptime(startDate, "%d/%m/%Y"))
        if endDate != '':
            endDate = (datetime.datetime.strptime(endDate, "%d/%m/%Y") + datetime.timedelta(days=1)).strftime("%Y-%m-%d")


        if startDate != '' and endDate != '':
            return '518__d:"%s"->"%s"' % (startDate, endDate)
        elif startDate != '':
            return '518__d:"%s"->"2100"' % (startDate)
        elif endDate != '':
            return '518__d:"1950"->"%s"' % (endDate)
        else:
            return ""

    @SEA.translate ('f',[],'f')
    def translateField(self, field):
        if field == "author":
            return ""
        else:
            return field

    @SEA.translate ('startRecord',[],'jrec')
    def translateStartRecord(self, startRecord):
        return startRecord

    @SEA.translate ('numRecords',[],'rg')
    def translateNumRecords(self, numRecords):
        return numRecords

    @SEA.translate ('sortField',[],'sf')
    def translateSortField(self, sortField):
        return sortField

    @SEA.translate ('sortOrder',[],'so')
    def translateSortOrder(self, sortOrder):
        return sortOrder

    @SEA.translate ('collections',[], 'c')
    def translateCollection(self, collection):
        if self.isSearchTypeOnlyPublic():
            return ""
        else:
            if collection == 'Events':
                suffix = 'EVENTS'
            else:
                suffix = 'CONTRIBS'

            if self._userLoggedIn:
                prefix = 'INDICOSEARCH'
            else:
                prefix = 'INDICOSEARCH.PUBLIC'
            return "%s.%s" % (prefix, suffix)

    @SEA.translate ('collections',[], 'p')
    def translateCollectionPublic(self, collection):

        if self.isSearchTypeOnlyPublic():
            if collection == 'Events':
                return """970__a:"INDICO.*" -970__a:'.*.'"""
            elif collection == 'Contributions':
                return """970__a:"INDICO.*" 970__a:'.*.'"""
            return ""
        else:
            return ""

class InvenioRedirectSEA(InvenioBaseSEA, SearchEngineRedirectAdapter):

    _implementationPackage = indico.ext.search.invenio

    def __init__(self, **params):
        InvenioBaseSEA.__init__(self, **params)

    def addParameters(self, params):
        newParams = params.copy()
        return newParams

class InvenioSEA(InvenioBaseSEA, SearchEngineCallAPIAdapter):
    """
        Search engine adapter for CDS Invenio.
    """
    _implementationPackage = indico.ext.search.invenio

    def __init__(self, **params):
        InvenioBaseSEA.__init__(self, **params)

    def _parseXMLDate(self, date):

        regexp = r'^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})Z$'
        m = re.match(regexp, date)

        if m:
            return datetime.datetime(*map(lambda x: int(x), list(m.groups())))
        else:
            return None

    def _processElem(self, elem):

        authors = []
        materials = []

        elementId = elem.getElementsByTagName("identifier")[0].firstChild.data.encode("utf-8")
        title = elem.getElementsByTagName("title")
        if len(title) > 0:
            title = title[0].firstChild
            if title != None:
                title = cgi.escape(title.data.encode("utf-8"))
        else:
            title = None

        location = elem.getElementsByTagName("location")
        if len(location) > 0:
            location = location[0].firstChild.data.encode("utf-8")
        else:
            location = None

        startDate = elem.getElementsByTagName("startDate")
        if len(startDate) > 0:
            startDate = self._parseXMLDate(startDate[0].firstChild.data.encode("utf-8"))
        else:
            startDate = None

        description = elem.getElementsByTagName("description")
        if len(description) > 0:
            description = description[0].firstChild
            if  description != None:
                description = cgi.escape(description.data.encode("utf-8"))
        else:
            description = None

        for a in elem.getElementsByTagName("author"):

            name = a.getElementsByTagName("name")[0].firstChild.data.encode("utf-8")
            role = a.getElementsByTagName("role")[0].firstChild.data.encode("utf-8")

            affiliation = a.getElementsByTagName("affiliation")[0].firstChild
            if affiliation:
                affiliation = affiliation.data.encode("utf-8")

            authors.append(Author(name, role, affiliation))

        for a in elem.getElementsByTagName("material"):

            url = a.getElementsByTagName("url")[0].firstChild
            if url:
                url = url.data.encode("utf-8")
            matDescription = a.getElementsByTagName("description")

            if len(matDescription) > 0:
                matDescription = matDescription[0].firstChild
                if matDescription != None:
                    matDescription = cgi.escape(matDescription.data.encode("utf-8"))
            else:
                matDescription = None

            materials.append((url, matDescription))


        return InvenioSearchResult.create(elementId, title, location, startDate, materials, authors, description)

    def addParameters(self, params):
        newParams = params.copy()

        # sc = "split by collection"
        newParams['of'] = 'xm'
        return newParams

    def preProcess(self, results):

        path = Config.getInstance().getStylesheetsDir()
        xslt = XSLTransformer(os.path.join(path, 'marc2short.xsl'))
        result = []
        finalXML = xslt.process(results)

        doc = minidom.parseString(finalXML)
        for elem in doc.getElementsByTagName("record"):
            # make sure it's not an empty (deleted) record
            if len(elem.getElementsByTagName("identifier")) > 0:
                result.append(self._processElem(elem))

        return result

    def extractNumHits(self, text):
        regexp = re.compile('<!-- Search-Engine-Total-Number-Of-Results: (\d+) -->')

        m = regexp.match(text.split('\n')[1])

        if m:
            return int(m.group(1))
        else:
            return 0

    def _loadBatchOfRecords(self, user, collection, number, start):

        record = start

        # by default, we should have several pages of results
        shortResult = False

        # if we're searching the private repository,
        # always request twice the number of items per page
        # (in order to account for invisible records)
        if self._userLoggedIn:
            numRequest = number * 2
        else:
            # ask always for an extra one, in order
            # to know if we reached the end
            numRequest = number+1

        results, fResults = [], []

        while (len(fResults) < number):

            Logger.get("search").debug("asking %s->%s from server (%s)" % (start, numRequest, collection))

            (r, numHits) = self.obtainRecords(startRecord=start,
                                                   numRecords=numRequest,
                                                   collections=collection,
                                                   startDate = self._filteredParams['startDate'],
                                                   endDate = self._filteredParams['endDate'],
                                                   p = self._filteredParams['p'],
                                                   f = self._filteredParams['f'],
                                                   sortField = "518__d", # this is the markxml for date. TODO: add more sortFields.
                                                   sortOrder = self._filteredParams['sortOrder'])
            results.extend(r)

            # filter
            allResultsFiltered = False
            for r in results:
                if len(fResults) == number or len(fResults) == numHits:
                    break
                if r.isVisible(user):
                    fResults.append(r)
                record += 1
            else:
                allResultsFiltered = len(fResults) > 0

            if record > numHits or numHits <= number or len(results) <= number or (allResultsFiltered and len(fResults) <= number):
                shortResult = True
                break

            Logger.get("search").debug("fResults (%s)" % len(fResults))

            start += numRequest

        Logger.get("search").debug("%s %s %s" % (len(fResults), numHits, number))

        return (fResults, numHits, shortResult, record)

    def _getResults(self, collection, number):

        params = copy.copy(self._filteredParams)
        params['collections'] = collection
        params['target'] = self._target.getId()

        queryHash = self._getQueryHash(params)

        Logger.get('search').debug('Hashing %s to %s' % (params, queryHash))

        # ATTENTION: _getStartingRecord will set self._page to 1,
        # if there's a cache miss
        start, cachedObj = self._getStartingRecord(queryHash, self._page)

        # get the access wrapper, so we can check user access privileges
        user = ContextManager.get("currentRH", None).getAW()

        results, numHits, shortResult, record = self._loadBatchOfRecords(user, collection, number, start)

        self._cacheNextStartingRecord(queryHash, self._page, record, cachedObj)

        return (numHits, shortResult, record, results)

    def process(self, filteredParams):

        self._filteredParams = filteredParams
        phrase = self._filteredParams.get('p', '')
        if phrase.strip() == '':
            self._noQuery = True

        params = copy.copy(self._filteredParams)

        nEvtRec, nContRec = 0, 0
        numEvtHits, numContHits = 0, 0
        eventResults, contribResults = [], []

        if not self._noQuery:
            if params.get('collections',"") != 'Contributions':
                numEvtHits, evtShortResult, nEvtRec, eventResults = self._getResults('Events', 25)
                params['evtShortResult'] = evtShortResult

            if params.get('collections',"") != 'Events':
                numContHits, contShortResult, nContRec, contribResults = self._getResults('Contributions', 25)
                params['contShortResult'] = contShortResult

        params['p'] = cgi.escape(phrase, quote=True)
        params['f'] = cgi.escape(filteredParams.get('f', ''), quote=True)

        params['eventResults'] = eventResults
        params['contribResults'] = contribResults

        params['nEventResult'] = nEvtRec
        params['nContribResult'] = nContRec

        params['numHits'] = numEvtHits + numContHits
        params['page'] = self._page

        params['targetObj'] = self._target

        params['searchingPublicWarning'] = self.isSearchTypeOnlyPublic() and not self._userLoggedIn
        params['accessWrapper'] = ContextManager().get("currentRH", None).getAW()

        return params
