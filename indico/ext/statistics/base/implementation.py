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
import sys
import urllib2

import indico.ext.statistics.base
import indico.ext.statistics.base.implementation

from indico.core.extpoint import Component
from indico.ext.statistics.register import StatisticsImplementationRegister

from MaKaC.plugins.base import PluginsHolder

class BaseStatisticsImplementation(Component):
    """
    This is the base of any API-based statistics implementation, it acts as
    a wrapper around a RESTful API and permits extensions thereof in queries
    for specific requirements. Constructs the REST API call and executes,
    designated logic defined later to parse.
    """

    QUERY_JOIN = '&'
    QUERY_BREAK = ';'
    QUERY_SCRIPT = ''
    QUERY_KEY_NAME = ''

    PLUGIN_HOOKFILE = 'JSHook.tpl'
    _pluginName = 'Base'

    def __init__(self):
        self._pluginFSPath = None
        self._pluginAPIPath = None
        self._pluginAPIToken = None
        self._pluginAPIParams = {}
        self._pluginAPIRequiredParams = []
        self._pluginAPIQuery = None
        self._pluginParamsChanged = False
        self._pluginImplementationPackage = indico.ext.statistics.base

        super(BaseStatisticsImplementation, self).__init__()
        self._buildPluginPath()
        self._buildAPIPath()

    def _buildPluginPath(self):
        """
        To be overloaded per implementation.
        """
        pass

    def _buildAPIPath(self):
        """
        Internally constructs the API path.
        """
        path = self._getSavedAPIPath()

        if path is None:
            return # @todo: handle this
        if not path.endswith('/'):
            path += '/'
        if path.startswith('http'):
            path = path.split('//')[1]

        self._pluginAPIPath = path

    def _buildAPIQuery(self, params=None, sorted=False):
        """
        Builds the entire API query, gives an opportunity to pass through
        futher params which will then be added to the internal dict.
        """

        if not self._hasUpdatedParams():
            return None

        if params is not None:
            self.setAPIParams(params)

        self._pluginAPIQuery = self._buildAPIQueryStructure(sorted)

    def _buildAPIQueryStructure(self, sorted=False):
        """
        This method is to be overloading in the implementation to return
        the specific format required by the tracking system being used.
        In this instance, a typical REST query is generated.
        """

        query = ""
        params = self.getAPIParams()

        if self._hasAPIToken():
            params[self.QUERY_KEY_NAME] = self.getAPIToken()

        if sorted: # This is broken, fix it.
            params.sort()

        for paramKey in params:
            value = ""

            if isinstance(self.getAPIParams().get(paramKey), list):
                value = self.getAPIParams().get(paramKey).join(',')
            else:
                value = self.getAPIParams().get(paramKey)

            query += str(paramKey) + "=" + str(value) + self.QUERY_JOIN

        return query[:-1]

    def _hasAPIParams(self):
        """
        True if some API Parameters have been reset.
        """
        return (len(self._pluginAPIParams) > 0)

    def _hasAPIToken(self):
        """
        True if an API token (authentication) has been set in this
        implementation / instantiation.
        """
        return self._pluginAPIToken is not None

    def _hasAllRequiredParams(self):
        """
        Some API implementations require certain parameters, ascertains
        if all are satisfied.
        """

        if len(self._pluginAPIRequiredParams) == 0:
            return True

        for param in self._pluginAPIRequiredParams:
            if param not in self._pluginAPIParams:
                return False

        return True

    def _hasUpdatedParams(self):
        """
        If query parameters have been altered since the last query
        generation, return True.
        """
        return self._pluginParamsChanged

    def _getMissingRequiredAPIParams(self):
        """
        Returns a list of order U\A difference between the required params
        and those provided.
        """
        required = set(self._pluginAPIRequiredParams)
        given = set(self.getAPIParams())

        return list(required.difference(given))

    def _getSavedAPIPath(self):
        """
        To be overridden in inheriting class, for plugin configurations
        where the target server is malleable and stored in the Plugins
        storage or elsewhere.
        """
        return None

    def _performCall(self):
        """
        Returns the raw results from the API to be handled elsewhere before
        being passed through to the report.
        """
        timeout = 10 # Timeout in seconds to end the call
        response = urllib2.urlopen(url = self.getAPIQuery(), timeout=timeout)

        if not response:
            raise Exception('The remote server for %s did not respond.'
                            % self.getName())

        value = response.read()
        response.close()
        return value

    def clearAPIParams(self):
        """
        Clears the internal params buffer.
        """
        self._pluginAPIParams = {}

    def isActive(self):
        """
        Wrapper around the original PluginsHolder method.
        """
        ph = PluginsHolder()
        stats = ph.getById('statistics')
        k = self.getName().lower()

        if not k in stats.getPlugins():
            return False
        else:
            return stats.getPlugins().get(k).isActive()

    def getAPIPath(self, http=False, https=False, withScript=False):
        """
        Returns the API path, which is considered to be the locatable
        address of the server hosting the tracking software. May
        designate HTTP or HTTPS prefix, or neither.
        If both defined, HTTPS takes priority.
        """
        path = self._pluginAPIPath;

        if withScript:
            path += self.QUERY_SCRIPT + "?"

        if https:
            return 'https://' + path
        elif http:
            return 'http://' + path
        else:
            return path

    def getAPIToken(self):
        """
        Returns the API authorisation token for this implementation.
        """
        return self._pluginAPIToken

    def getAPIQuery(self, onlyQuery=False, http=False, https=False, withScript=False):
        """
        Triggers internal build of query and returns the full path by
        default, can return only the query string if flag onlyQuery is true.
        """

        if not self._hasAllRequiredParams():
            exc = _('Cannot call API without all required parameters, missing: ')
            exc += str(self._getMissingRequiredAPIParams())
            raise Exception(exc)

        self._buildAPIQuery()

        if onlyQuery:
            return self._pluginAPIQuery

        return self.getAPIPath(http, https, withScript) + self._pluginAPIQuery

    def getConferenceReport(self, **kwargs):
        """
        To be implemented in inheriting class.
        """
        return None

    def getContributionReport(self, **kwargs):
        """
        To be implemented in inheriting class.
        """
        return None

    def getJSHookObject(self, instantiate=False):
        """
        Returns the Hook object for specific data arguements, to be over-
        ridden in inheriting classes.
        """
        reference = indico.ext.statistics.base.implementation.JSHookBase

        return reference() if instantiate else reference

    def getJSHookPath(self):
        """
        Returns the expected path for the JSHook file.
        """

        return self._pluginFSPath + '/tpls/' + self.PLUGIN_HOOKFILE

    def getAPIParams(self):
        """
        Returns the dictionary of API parameters currently in this
        implementation.
        """
        return self._pluginAPIParams

    def getImplementationPackage(self):
        """
        Returns a reference to the package which contains this implementation
        to avoid the use of introspection / reflection later.
        """
        return self._pluginImplementationPackage

    def getName(self):
        """
        Returns the name of this implementation.
        """
        return self._pluginName

    def getQueryResult(self):
        """
        To be overloaded per implementation.
        """
        pass

    def setAPIParams(self, params):
        """
        Internal mechanism for storing parameters for the query using
        a dictionary (params) of key=value.
        """
        for paramKey in params.keys():

            if params.get(paramKey) is None:
                del self.getAPIParams()[paramKey]
            else:
                self.getAPIParams()[paramKey] = params.get(paramKey)

        self._pluginParamsChanged = True

    def setAPIToken(self, token):
        """
        Sets the API token of this instance.
        """
        self._pluginAPIToken = token

class JSHookBase(object):
    """
    The base implementation of the hook object takes an instance of a
    plugin to populate with the dynamic parameters.
    """

    def __init__(self, instance):
        self.path = instance.getJSHookPath()
        self.url = instance.getAPIPath()
