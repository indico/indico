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

import os
import zope.interface
import pkg_resources

from indico.core.extpoint import Component
import indico.ext.search
from indico.core.extpoint.events import INavigationContributor
from indico.core.extpoint.plugins import IPluginSettingsContributor
from indico.web.handlers import RHHtdocs
from indico.util.contextManager import ContextManager

from MaKaC.i18n import _
from MaKaC.errors import PluginError
from MaKaC.plugins import PluginsHolder
from MaKaC.webinterface.urlHandlers import URLHandler
from MaKaC.webinterface.wcomponents import WTemplated, WNavigationDrawer
from MaKaC.webinterface.rh.conferenceBase import RHCustomizable
from MaKaC.webinterface.pages.category import WPCategoryDisplayBase
from MaKaC.webinterface.pages.conferences import WPConferenceDisplayBase

from indico.core.config import Config
from MaKaC.conference import CategoryManager, ConferenceHolder, Conference
from indico.ext.search.register import SearchRegister
from MaKaC.common.info import HelperMaKaCInfo
from indico.web.assets import PluginEnvironment
from webassets import Bundle


class SearchCHContributor(Component):
    """
    Adds the Search option to the header of the Category.
    """

    zope.interface.implements(INavigationContributor)

    def fillCategoryHeader(self, obj, params):
        # Search box, in case search is active
        defaultSearchEngine = SearchRegister().getDefaultSearchEngineAgent()
        if defaultSearchEngine is not None and defaultSearchEngine.isActive():
            params["searchBox"] = WSearchBox.forModule(defaultSearchEngine.getImplementationPackage(), params.get("categId", 0)).getHTML()

    def fillConferenceHeader(self, obj, params):
        # Search box, in case search is active
        defaultSearchEngine = SearchRegister().getDefaultSearchEngineAgent()
        if params["dm"].getSearchEnabled() and defaultSearchEngine is not None and defaultSearchEngine.isActive():
            params["searchBox"] = WMiniSearchBox.forModule(defaultSearchEngine.getImplementationPackage(), params.get("confId", 0)).getHTML()


    def includeMainJSFiles(self, obj, params={}):
        """
        Includes additional javascript file.
        """
        info = HelperMaKaCInfo.getMaKaCInfoInstance()
        asset_env = PluginEnvironment('search', os.path.dirname(__file__), 'search')
        asset_env.debug = info.isDebugActive()

        asset_env.register('search', Bundle('js/search.js',
                                                           filters='rjsmin',
                                                           output="search__%(version)s.min.js"))
        params['paths'].extend(asset_env['search'].urls())


class PluginSettingsContributor(Component):

    zope.interface.implements(IPluginSettingsContributor)

    def hasPluginSettings(self, obj, ptype, plugin):
        return (ptype == 'search' and plugin == None)

    def getPluginSettingsHTML(self, obj, ptype, plugin):
        if ptype == 'search' and plugin == None:
            return WPluginSettings.forModule(indico.ext.search).getHTML()
        else:
            return None


class UHSearch(URLHandler):
    _endpoint = "search.search"


class RHSearchHtdocs(RHHtdocs):
    _local_path = os.path.join(os.path.dirname(indico.ext.search.__file__), "htdocs")
    _min_dir = 'search'


class RHSearchBase(RHCustomizable):

    def _checkProtection(self):
        if not PluginsHolder().hasPluginType("search"):
            raise PluginError(_("Search plugin is not active."))

    def _getTarget(self):
        try:
            self._target = self._conf = ConferenceHolder().getById(self._params.get("confId",""))
        except:
            self._target = CategoryManager().getById(self._params.get('categId', 0))

    def _checkParams( self, params ):
        self._params = params
        self._getTarget()
        self._seAdapter = SearchRegister().getDefaultSearchEngineAgent()(target=self._target, page=int(params.get('page', 1)), userLoggedIn=self.getAW().getUser() != None)

    def _filterParams(self, params, seaInstance):
        ret = {}

        allowedParams = seaInstance.getAllowedParams()

        for param in allowedParams:
            if param in params:
                ret[param] = params[param]
            else:
                ret[param] = ''
        return ret

    def _process(self):
        params = self._filterParams(self._params, self._seAdapter)
        result = self._seAdapter.process(params)
        if result is not None:
            wp_class = WPSearchResultConference if isinstance(self._target, Conference) else WPSearchResultCategory
            return wp_class(self, self._target, WSearchResult, self._seAdapter).display(**result)

class WSearchResult(WTemplated):
    def __init__(self, seAdapter, target):
        WTemplated.__init__(self)
        self._target = target
        self._seAdapter = seAdapter

    def getVars(self):
        vars = WTemplated.getVars(self)
        vars["searchAction"] = UHSearch.getURL()
        vars["searchIcon"] = Config.getInstance().getPluginIconURL(self._seAdapter.getId(), self._seAdapter.getId())
        return vars

class WPSearchResult:
    def __init__(self, rh, target, templateClass, seAdapter):
        self._target = target
        self._templateClass = templateClass
        self._seAdapter = seAdapter

    def _getBody(self, params):
        self._setParams(params)
        return self._templateClass.forModule(self._seAdapter.getImplementationPackage(), self._seAdapter, self._target).getHTML(params)

class WPSearchResultCategory(WPSearchResult, WPCategoryDisplayBase):

    def __init__(self, rh, target, templateClass, seAdapter):
        WPCategoryDisplayBase.__init__(self, rh, target)
        WPSearchResult.__init__(self, rh, target, templateClass, seAdapter)

    def _setParams(self, params):
        params['confId'] = None
        params['categId'] = self._target.getId()
        params['categName'] = self._target.getTitle()

    def _getNavigationDrawer(self):
        if self._target.isRoot():
            return
        else:
            pars = {"target": self._target, "isModif": False}
            return WNavigationDrawer( pars )

class WPSearchResultConference(WPSearchResult, WPConferenceDisplayBase):

    def __init__(self, rh, target, templateClass, seAdapter):
        WPConferenceDisplayBase.__init__(self, rh, target)
        WPSearchResult.__init__(self, rh, target, templateClass, seAdapter)

    def _setParams(self, params):
        params['confId'] = self._conf.getId()
        params['categId'] = None

class WBaseSearchBox(WTemplated):

    def __init__(self, targetId=0):
        WTemplated.__init__(self)
        self._targetId = targetId

    def getVars(self):
        vars = WTemplated.getVars( self )
        vars["searchAction"] = UHSearch.getURL()
        vars['targetId'] = self._targetId
        vars['searchImg'] =  Config.getInstance().getSystemIconURL( "search" )
        return vars

class WSearchBox(WBaseSearchBox):

    def __init__(self, targetId=0):
        WTemplated.__init__(self)
        self._targetId = targetId

    def getVars(self):
        vars = WBaseSearchBox.getVars( self )
        vars["categName"] = CategoryManager().getById(self._targetId).getTitle()
        vars['moreOptionsClass'] = "arrowExpandIcon"
        return vars

class WMiniSearchBox(WBaseSearchBox):

    def __init__(self, confId):
        WBaseSearchBox.__init__(self, targetId = confId)

class WPluginSettings(WTemplated):
    def getVars(self):
        vars = WTemplated.getVars( self )
        vars["defaultSearchEngine"] = SearchRegister().getDefaultSearchEngineAgentName()
        return vars

