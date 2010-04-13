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

import urllib2, re
from urllib import urlencode

from MaKaC.webinterface import urlHandlers
from MaKaC.conference import ConferenceHolder

from MaKaC.common.logger import Logger
from MaKaC.common.timezoneUtils import server2utc, DisplayTZ
from pytz import timezone

# translation table, built with the help from the decorator SEATranslator
globals()['_SearchEngineAdapter__translationTable'] = {}
globals()['_SearchEngineAdapter__allowedParams'] = []

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

    def __init__(self, id, title, location, startDate, materials, authors, description):
        self._id = id
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
    def create(cls, id, title, location, startDate, materials, authors, description):
        
        regexp = r'^INDICO\.\w(\w+)(\.(\w+)(\.(\w)+)?)?$'

        m = re.match(regexp, str(id))

        if m:
            if m.group(4):
                return SubContributionEntry(m.group(5), title, location, startDate, materials, authors, description, m.group(3), m.group(1))
            elif m.group(2):
                return ContributionEntry(m.group(3), title, location, startDate, materials, authors, description, m.group(1))
            else:
                return ConferenceEntry(m.group(1), title, location, startDate, materials, authors, description)
        else:
            raise Exception('unrecognized id format: %s' % id)



class ContributionEntry(SearchResult):

    def __init__(self, id, title, location, startDate, materials, authors, description, parent):
        SearchResult.__init__(self, id, title, location, startDate, materials, authors, description)

        self._parent = parent

        materials.append((urlHandlers.UHConferenceDisplay.getURL(confId=parent), 'Event details'))

    def getConferenceId(self):
        return self._parent

    def getURL(self):
        return str(urlHandlers.UHContributionDisplay.getURL(confId=self.getConferenceId(), contribId=self.getId()))

    def getCompoundId(self):
        return "%s:%s" % (self._parent, self._id)

    def getTarget(self):
        return self.getConference()

    def getTarget(self):

        conference = self.getConference()

        if not conference:
            return None
        
        return conference.getContributionById(self.getId())


class SubContributionEntry(SearchResult):
    
    def __init__(self, id, title, location, startDate, materials, authors, description, parent, conference):
        SearchResult.__init__(self, id, title, location, startDate, materials, authors, description)

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
    

class SearchEngineAdapter:        
    """
        The basic search engine adapter.
        It should be overloaded by the specific SEA class for
        the required search engine.
        See invenioSEA.py for an example.
    """
    
    def getRequestAddress(self):
        """
            To be overloaded...
            @return: the request address, as a string
        """
        pass

    def extractNumHits(self, text):
        """
            To be overloaded...
            @return: the number of search hits
        """
        pass
    
    def getAllowedParams(self):
        """
            @return: the parameters which the search engine accepts
        """
        return globals()['_SearchEngineAdapter__allowedParams']
    
    def addParameters(self, params):
        """
            To be overloaded. Adds parameters to the already existing
            ones (at the end of parameter translation).
            
            @param params: the already translated request parameters
            @type params: dictionary
            
            @return: the parameters, with the added parameter(s)
        """
        pass

    def preProcess(self, results):
        """ To be overloaded, """
        pass

    def _fetchResults(self, service, parameters):
        url = 'http://'+self.getRequestAddress()+'?'+urlencode(parameters)

        req = urllib2.Request(url, None, {'Accept-Charset' : 'utf-8'})
        document = urllib2.urlopen(req)
        text = document.read()

        return (text, self.extractNumHits(text))

    def translateParameters(self, kwargs):

        finalArgs = {}

        for outArg, entries in __translationTable.iteritems():

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


    
    def process(self,**kwargs):
        """
            Do not overload this unless you know what you're doing.
            The main processing cycle. Translates the search request parameters
            from the web interface to those of the target search engine.
            
            @param kwargs: Input parameters            
            
        """

        Logger.get('search.SEA').debug('Translating parameters...')        
        finalArgs = self.translateParameters(kwargs)

        Logger.get('search.SEA').debug('Fetching results...')
        (preResults, numPreResults) = self._fetchResults(self.getRequestAddress(), finalArgs )

        Logger.get('search.SEA').debug('Preprocessing results...')
        results = self.preProcess(preResults)

        Logger.get('search').debug('Done!')

        return (results, numPreResults)


def SEATranslator(origFields, fieldType, output):
    """
        Decorator, for easy addition of translation functions to the table.        
    """
    
    def factory(method):
        ttable = globals()['_SearchEngineAdapter__translationTable']
        allowedParams = globals()['_SearchEngineAdapter__allowedParams']
        
        if not ttable.has_key(output):        
            ttable[output] = []

        ttable[output].append((origFields,method));

        if type(origFields) == list:
            allowedParams.extend(origFields)
        else:
            allowedParams.append(origFields)
        
    return factory
    
        
