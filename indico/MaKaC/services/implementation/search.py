# -*- coding: utf-8 -*-
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

from MaKaC.conference import CategoryManager

from MaKaC.services.implementation.base import ServiceBase

from MaKaC.common import search

from MaKaC.common.PickleJar import DictPickler

from MaKaC.webinterface import urlHandlers
from MaKaC.fossils.user import IAvatarFossil, IGroupFossil
from MaKaC.common.fossilize import fossilize

from zope.index.text import parsetree
from MaKaC.services.implementation.user import UserComparator

from MaKaC.common.Configuration import Config

#################################
# User and group search
#################################

class SearchBase(ServiceBase):

    def _checkParams(self):
        """ Checks for external authenticators
            For now the underlying MaKaC.common.search code only supports
            1 external authenticator, so we just see if a proper external authenticator is present or not
        """
        self._searchExt = False
        config = Config.getInstance()
        for authenticatorName in config.getAuthenticatorList():
            authParamName = "searchExternal-" + authenticatorName
            if authParamName in self._params and self._params[authParamName]:
                self._searchExt = True
                break


class SearchUsers(SearchBase):

    def _checkParams(self):
        SearchBase._checkParams(self)
        self._surName = self._params.get("surName", "")
        self._name = self._params.get("name", "")
        self._organisation = self._params.get("organisation", "")
        self._email = self._params.get("email", "")
        self._confId = self._params.get("conferenceId", None)
        self._exactMatch = self._params.get("exactMatch", False)

    def _getAnswer(self):

        results = search.searchUsers(self._surName, self._name, self._organisation, self._email,
                                     self._confId, self._exactMatch, self._searchExt)

        #will use either IAvatarFossil or IContributionParticipationFossil
        fossilizedResults = fossilize(results)
        fossilizedResults.sort(cmp=UserComparator.cmpUsers)

        return fossilizedResults


class SearchGroups(SearchBase):

    def _checkParams(self):
        SearchBase._checkParams(self)
        self._group = self._params.get("group", "")

    def _getAnswer(self):

        results = search.searchGroups(self._group, self._searchExt)

        fossilizedResults = fossilize(results, IGroupFossil)
        fossilizedResults.sort(cmp=UserComparator.cmpGroups)

        for fossilizedGroup in fossilizedResults:
            fossilizedGroup["isGroup"] = True

        return fossilizedResults


class SearchUsersGroups(ServiceBase):

    def _getAnswer(self):
        results = {}
        users = search.searchUsers(surName = self._params.get("surName", ""),
                               name = self._params.get("name", ""),
                               organisation = self._params.get("organisation", ""),
                               email = self._params.get("email", ""),
                               conferenceId = self._params.get("conferenceId", None),
                               exactMatch = self._params.get("exactMatch", False),
                               searchExt = self._params.get("searchExt", False))

        groups = search.searchGroups(group = self._params.get("group", ""),
                               searchExt = self._params.get("searchExt", False))

        pickledUsers = [DictPickler.pickle(human) for human in users]
        pickledGroups = [DictPickler.pickle(group) for group in groups]

        pickledUsers.sort(cmp=UserComparator.cmpUsers)
        pickledGroups.sort(cmp=UserComparator.cmpGroups)

        results["people"] = pickledUsers
        results["groups"] = pickledGroups

        return results


#################################
# Category search
#################################

class SearchCategoryNames(ServiceBase):

    def _checkParams(self):
        self._searchString = self._params.get("value")

    def _getPath(self, cat):
        return cat.getCategoryPathTitles()[1:-1]

    def _getAnswer(self):

        import MaKaC.common.indexes as indexes
        nameIdx = indexes.IndexesHolder().getIndex('categoryName')

        try:
            query = ' AND '.join(map(lambda y: "*%s*" % y, filter(lambda x: len(x) > 0, self._searchString.split(' '))))
            foundEntries = nameIdx.search(query)
        except parsetree.ParseError:
            foundEntries = []

        number = len(foundEntries)

        # get only the first 10 results
        foundEntries = foundEntries[:7]

        entryNames = []

        for (categId, value) in foundEntries:
            categ = CategoryManager().getById(categId)
            entryNames.append({
                'title': categ.getTitle(),
                'path': self._getPath(categ),
                'url': str(urlHandlers.UHCategoryDisplay.getURL(categ))
                })

        return {
            "list": entryNames,
            "number": number
            }


methodMap = {
    "users" : SearchUsers,
    "groups" : SearchGroups,
    "usersGroups": SearchUsersGroups,
    "categoryName": SearchCategoryNames
}
