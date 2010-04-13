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

import os, re, datetime, cgi, time
from MaKaC.search import base
from MaKaC.search.base import SEATranslator
import MaKaC.conference as conference
from MaKaC.common import Config
from MaKaC.common.output import XSLTransformer

from xml.dom import minidom

class InvenioPublicSEA(base.SearchEngineAdapter):
    """
        Search engine adapter for CDS Invenio.
        Currently used at CERN.
    """

    def getRequestAddress(self):
        return Config().getIndicoSearchServer() + "/search"

    def _buildCategoryHierarchy(self, target):
        """
            Builds a category path, separated by ':', as indicosearch wishes.
        """
        return ':'.join(target.getCategoryPath())

    def _parseXMLDate(self, date):

        regexp = r'^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})Z$'
        m = re.match(regexp, date)

        if m:
            return datetime.datetime(*map(lambda x: int(x), list(m.groups())))
        else:
            return None

    def extractNumHits(self, text):
        regexp = re.compile('<!-- Search-Engine-Total-Number-Of-Results: (\d+) -->')

        m = regexp.match(text.split('\n')[1])

        if m:
            return int(m.group(1))
        else:
            return 0

    def _processElem(self, elem):

        authors = []
        materials = []

        id = elem.getElementsByTagName("identifier")[0].firstChild.data.encode("utf-8")
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

            authors.append(base.Author(name, role, affiliation))

        for a in elem.getElementsByTagName("material"):

            url = a.getElementsByTagName("url")[0].firstChild.data.encode("utf-8")
            matDescription = a.getElementsByTagName("description")

            if len(matDescription) > 0:
                matDescription = matDescription[0].firstChild
                if matDescription != None:
                    matDescription = cgi.escape(matDescription.data.encode("utf-8"))
            else:
                matDescription = None

            materials.append((url, matDescription))


        return base.SearchResult.create(id, title, location, startDate, materials, authors, description)


    def __init__(self, target, private=False):
        """
            Constructor

            @param target: Target event/category
            @type target: Conference/Category object
        """

        self._private = private

        if target == None:
            #search root category by default
            self._marcQuery = ''
            self._searchCategories = True
        elif type(target) == conference.Category:
            # we're dealing with a category

            hierarchy = self._buildCategoryHierarchy(target)

            if hierarchy != '0':
                # if not on root, search using path
                self._marcQuery = '650_7:"'+hierarchy+'*" '
            else:
                # perform global search
                self._marcQuery = ''
            self._searchCategories = True

        elif type(target) == conference.Conference:
            # we're looking inside an event

            # search for event identifier
            self._marcQuery = 'AND (970__:"INDICO.p%s*" OR 970__:"INDICO.r%s*")' % (target.getId(), target.getId())
            self._searchCategories = False

        else:
            raise Exception("Unknown target type.")

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

    ## Now, we have the actual translation rules
    ## Notice that the second parameter of SEATranslator is
    ## currently not being used.
    ##
    ## '@SEATranslator(sourceField, type, targetField)'

    @SEATranslator ('p', 'text', 'p')
    def translatePhrase(self, phrase):
        return phrase + ' ' + self._marcQuery

    @SEATranslator(['startDate', 'endDate'],'date', 'p')
    def translateDates(self, startDate, endDate):

        if startDate != '':
            startDate = time.strftime("%Y-%m-%d", time.strptime(startDate, "%d/%m/%Y"))
        if endDate != '':
            endDate = time.strftime("%Y-%m-%d", time.strptime(endDate, "%d/%m/%Y"))


        if startDate != '' and endDate != '':
            return '518__d:"%s"->"%s"' % (startDate, endDate)
        elif startDate != '':
            return '518__d:"%s"->"2100"' % (startDate)
        elif endDate != '':
            return '518__d:->"%s"' % (endDate)
        else:
            return ""

    @SEATranslator ('f',[],'f')
    def translateField(self, field):
        return field

    @SEATranslator ('collections',[],'p')
    def translateCollection(self, collection):
        if collection == 'Events':
            return """970__a:"INDICO.*" -970__a:'.*.'"""
        elif collection == 'Contributions':
            return """970__a:"INDICO.*" 970__a:'.*.'"""
        return ""

    @SEATranslator ('startRecord',[],'jrec')
    def translateStartRecord(self, startRecord):
        return startRecord

    @SEATranslator ('numRecords',[],'rg')
    def translateNumRecords(self, numRecords):
        return numRecords

    @SEATranslator ('sortField',[],'sf')
    def translateSortField(self, sortField):
        return sortField

    @SEATranslator ('sortOrder',[],'so')
    def translatesortOrder(self, sortOrder):
        return sortOrder
