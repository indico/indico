from MaKaC.webinterface.pages.category import WPCategoryDisplayBase
from MaKaC.webinterface.pages.conferences import WPConferenceDisplayBase
from MaKaC.webinterface.wcomponents import WTemplated, WNavigationDrawer

class WSearch(WTemplated):
    def __init__(self, target, aw):
        self._target = target
        self._aw = aw
        WTemplated.__init__(self)


class WPSearch:

    def _getBody(self, params):
        wc = WSearch(self._target, self._getAW())
        self._setParams(params)

        return wc.getHTML(params)


class WPSearchCategory(WPSearch, WPCategoryDisplayBase):

    def __init__(self, rh, target):
        WPCategoryDisplayBase.__init__(self, rh, target)

    def _setParams(self, params):
        params['confId'] = None
        params['categId'] = self._target.getId()

    def _getNavigationDrawer(self):
        if self._target.isRoot() and self._target.isRoot():
            return
        else:
            pars = {"target": self._target, "isModif": False}
            return WNavigationDrawer( pars )


class WPSearchConference(WPSearch, WPConferenceDisplayBase):

    def __init__(self, rh, target):
        WPConferenceDisplayBase.__init__(self, rh, target)
        self._target = target

    def _setParams(self, params):
        params['confId'] = self._conf.getId()
        params['categId'] = None
