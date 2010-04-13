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

import copy, md5, cgi, urllib
import MaKaC.webinterface.rh.base as base
from MaKaC.webinterface.rh.conferenceBase import RHConferenceBase
from MaKaC.webinterface.rh.categoryDisplay import RHCategDisplayBase

from MaKaC.webinterface.pages import search
import MaKaC.common.MaKaCConfig as MaKaCConfig
from MaKaC.common.Configuration import Config
from MaKaC.common.logger import Logger
import MaKaC.webinterface.locators as locators
import MaKaC.conference as conference
from MaKaC.search.base import ConferenceEntry, ContributionEntry
from MaKaC.search.cache import SECache, SECacheEntry

class RHSearchBase:

    def _checkParams( self, params ):

        self._params = params
        self._noQuery = False        
        self._page = int(params.get('page', 1))

        isearch = Config.getInstance().getIndicoSearchServer()
        SEAClassName = Config.getInstance().getIndicoSearchClass()
        
        moduleName = '.'.join(SEAClassName.split('.')[:-1])
        self._SEAClassName = SEAClassName.split('.')[-1]
        self._searchingPrivate = self.getAW().getUser() != None
    
        # and now for some introspection magic...
        # load the requestClass from wherever it is, and instantiate a classobj
        clazz = getattr(__import__(moduleName,globals(),locals(),['']), self._SEAClassName)

        # now we can call the constructor
        self._seAdapter = clazz(self._target, self._searchingPrivate)

        if self._searchingPrivate:
            self._sessionHash = "%s_%s" % (self._getSession().getId(), self.getAW().getUser().getId())
        else:
            self._sessionHash = 'PUBLIC'
        
    def _filterParams(self, params, seaInstance):
        ret = {}
        
        allowedParams = seaInstance.getAllowedParams()
        
        for param in allowedParams:
            if param in params:
                ret[param] = params[param]
            else:
                ret[param] = ''
                
        return ret

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
        obj = SECache().loadObject([self._sessionHash, "%s_"%queryHash])

        if page == 1:
            Logger.get("search").debug("first page")
            # first page, start with 0
            return 0, None
        elif obj and obj.getData().has_key(page):
            Logger.get("search").debug("hit! %s %s", (obj.getData()[page], obj))
            # cache hit!
            return obj.getData()[page], obj
        else:
            Logger.get("search").debug("miss")
            # cache miss, force first page to be loaded
            self._page = 1
            return 0, None

    def _cacheNextStartingRecord(self, queryHash, page, record, obj):
        if not obj:
            obj = SECacheEntry(self._sessionHash, queryHash)
        
        obj.setPage(self._page+1, record+1)

        Logger.get("search").debug("set page: %s" % obj._data)
        
        SECache().cacheObject(obj, "")


    def _loadBatchOfRecords(self, user, collection, number, start):

        record = start

        # by default, we should have several pages of results
        shortResult = False   
        
        # if we're searching the private repository,
        # always request twice the number of items per page
        # (in order to account for invisible records)
        if self._searchingPrivate:
            numRequest = number * 2
        else:
            # ask always for an extra one, in order
            # to know if we reached the end
            numRequest = number+1

        results, fResults = [], []

        while (len(fResults) < number):

            Logger.get("search").debug("asking %s->%s from server (%s)" % (start, numRequest, collection))

            (r, numHits) = self._seAdapter.process(startRecord=start,
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
            for r in results:
                if len(fResults) == number or len(fResults) == numHits:
                    break
                if r.isVisible(user):
                    fResults.append(r)
                record += 1

            if record > numHits or numHits <= number or len(results) <= number:
                shortResult = True
                break

            Logger.get("search").debug("fResults (%s)" % len(fResults))
            
            start += numRequest

        Logger.get("search").debug("%s %s %s" % (len(fResults), numHits, number))

        return (fResults, numHits, shortResult, record)


    def _fillResults(self, collection, number):

        params = copy.copy(self._filteredParams)
        params['collections'] = collection
        params['target'] = self._target.getId()

        queryHash = self._getQueryHash(params)

        Logger.get('search').debug('Hashing %s to %s' % (params, queryHash))

        # ATTENTION: _getStartingRecord will set self._page to 1,
        # if there's a cache miss
        start, cachedObj = self._getStartingRecord(queryHash, self._page)

        # get the access wrapper, so we can check user access privileges
        user = self.getAW()

        results, numHits, shortResult, record = self._loadBatchOfRecords(user, collection, number, start)

        self._cacheNextStartingRecord(queryHash, self._page, record, cachedObj)
        
        return (numHits, shortResult, record, results)

    def _process(self):

        self._filteredParams = self._filterParams(self._params, self._seAdapter)

        if self._SEAClassName != 'InvenioRedirectSEA' :
            phrase = self._filteredParams.get('p', '')
            if phrase.strip() == '':
                self._noQuery = True

            params = copy.copy(self._filteredParams)        
                
            nEvtRec, nContRec = 0, 0
            numEvtHits, numContHits = 0, 0
            eventResults, contribResults = [], []

            if not self._noQuery:
                if params['collections'] != 'Contributions':
                    numEvtHits, evtShortResult, nEvtRec, eventResults = self._fillResults('Events', 25)
                    params['evtShortResult'] = evtShortResult

                if params['collections'] != 'Events':
                    numContHits, contShortResult, nContRec, contribResults = self._fillResults('Contributions', 25)
                    params['contShortResult'] = contShortResult

            params['p'] = cgi.escape(phrase, quote=True)
            params['f'] = cgi.escape(self._filteredParams.get('f', ''), quote=True)

            params['eventResults'] = eventResults
            params['contribResults'] = contribResults

            params['nEventResult'] = nEvtRec
            params['nContribResult'] = nContRec
            
            params['numHits'] = numEvtHits + numContHits
            params['page'] = self._page
            
            params['targetObj'] = self._target

            params['searchingPublicWarning'] = self._SEAClassName != 'InvenioPublicSEA' and not self._searchingPrivate

            return self._getPage().display(**params)
        else:
            # translate                   
            search = self._seAdapter.translateParameters(self._filteredParams)
            url = self._seAdapter.getRequestAddress()
            self._redirect('http://'+url+'?'+urllib.urlencode(search))


    @classmethod
    def create(self, req, params):
        
        l = locators.WebLocator()

        try:            
            l.setCategory(params)                    
            return RHSearchCategory(req)
        except:
            try:
                l.setConference(params)
                return RHSearchConference(req)
            except:
                # fallback - root category search page
                params['categId'] = [0]
                return RHSearchCategory(req)

class RHSearchConference(RHConferenceBase, RHSearchBase):

    def _checkParams( self, params ):
        RHConferenceBase._checkParams(self, params)
        RHSearchBase._checkParams(self, params)

    def _getPage(self):
        return search.WPSearchConference(self, self._target)

    def _process(self):
        return RHSearchBase._process(self)

class RHSearchCategory(RHCategDisplayBase, RHSearchBase):

    def _checkParams( self, params ):
        RHCategDisplayBase._checkParams(self, params)
        RHSearchBase._checkParams(self, params)

    def _getPage(self):
        return search.WPSearchCategory(self, self._target)

    def _process(self):
        return RHSearchBase._process(self)
