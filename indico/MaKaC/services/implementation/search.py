from MaKaC.services.implementation.base import ProtectedService
from MaKaC.services.implementation.base import ServiceBase

from MaKaC.common import search

from MaKaC.common.PickleJar import DictPickler

class SearchUsersGroups(ProtectedService):
    
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


methodMap = {
    "usersGroups": SearchUsersGroups
}
