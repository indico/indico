# -*- coding: utf-8 -*-

from MaKaC.conference import CategoryManager

from MaKaC.services.implementation.base import ServiceBase

from MaKaC.common import search

from MaKaC.common.PickleJar import DictPickler
from MaKaC.common.logger import Logger

from MaKaC.webinterface import urlHandlers

from zope.index.text import parsetree

class SearchUsersGroups(ServiceBase):

    @staticmethod
    def _cmpUsers(x, y):
        cmpResult = cmp(x["familyName"].lower(), y["familyName"].lower())
        if cmpResult == 0:
            cmpResult = cmp(x["firstName"].lower(), y["firstName"].lower())
        return cmpResult

    @staticmethod
    def _cmpGroups(x, y):
        return cmp(x["name"].lower(), y["name"].lower())


    def _getAnswer(self):

        results = search.searchPeople(surName = self._params.get("surName", ""),
                               name = self._params.get("name", ""),
                               organisation = self._params.get("organisation", ""),
                               email = self._params.get("email", ""),
                               group = self._params.get("group", ""),
                               conferenceId = self._params.get("conferenceId", None),
                               exactMatch = self._params.get("exactMatch", False),
                               searchExt = self._params.get("searchExt", False))
        results["people"] = sorted([DictPickler.pickle(human) for human in results.get("people", [])], cmp=SearchUsersGroups._cmpUsers)
        results["groups"] = sorted([DictPickler.pickle(group) for group in results.get("groups", [])], cmp=SearchUsersGroups._cmpGroups)
        return results


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
    "usersGroups": SearchUsersGroups,
    "categoryName": SearchCategoryNames
}
