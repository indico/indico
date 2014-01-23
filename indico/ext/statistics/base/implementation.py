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
import urllib2
import urlparse

import indico.ext.statistics.base
import indico.ext.statistics.base.implementation

from functools import wraps

from indico.core.extpoint import Component
from indico.ext.statistics.register import StatisticsConfig

from MaKaC.i18n import _
from MaKaC.common.cache import GenericCache
from MaKaC.common.externalOperationsManager import ExternalOperationsManager
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
    _name = 'Base'
    _config = StatisticsConfig()

    def __init__(self):
        self._FSPath = None
        self._APIPath = None
        self._APIToken = None
        self._APIParams = {}
        self._APIRequiredParams = []
        self._APIQuery = None
        self._paramsChanged = False
        self._implementationPackage = indico.ext.statistics.base
        self._hasJSHook = False
        self._hasDownloadListener = False

        Component.__init__(self)
        self._buildPluginPath()
        self._buildAPIPath()

    def _buildPluginPath(self):
        """
        To be overloaded per implementation.
        """
        pass

    def _buildAPIPath(self, server='primary'):
        """
        Internally constructs the API path.
        """
        path = self._getSavedAPIPath(server)

        if path is None:
            return
        if not path.endswith('/'):
            path += '/'

        parsed = urlparse.urlparse(path)
        self._APIPath = parsed.netloc + parsed.path

    def _buildAPIQuery(self, params=None):
        """
        Builds the entire API query, gives an opportunity to pass through
        futher params which will then be added to the internal dict.
        """

        if not self._hasUpdatedParams():
            return None

        if params is not None:
            self.setAPIParams(params)

        self._APIQuery = self._buildAPIQueryStructure()

    def _buildAPIQueryStructure(self):
        """
        This method is to be overloading in the implementation to return
        the specific format required by the tracking system being used.
        In this instance, a typical REST query is generated.
        """

        query = ""
        params = self.getAPIParams()

        if self._hasAPIToken():
            params[self.QUERY_KEY_NAME] = self.getAPIToken()

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
        return (len(self._APIParams) > 0)

    def _hasAPIToken(self):
        """
        True if an API token (authentication) has been set in this
        implementation / instantiation.
        """
        return self._APIToken is not None

    def _hasAllRequiredParams(self):
        """
        Some API implementations require certain parameters, ascertains
        if all are satisfied.
        """

        if len(self._APIRequiredParams) == 0:
            return True

        for param in self._APIRequiredParams:
            if param not in self._APIParams:
                return False

        return True

    def _hasUpdatedParams(self):
        """
        If query parameters have been altered since the last query
        generation, return True.
        """
        return self._paramsChanged

    def _getMissingRequiredAPIParams(self):
        """
        Returns a list of order U\A difference between the required params
        and those provided.
        """
        required = set(self._APIRequiredParams)
        given = set(self.getAPIParams())

        return list(required.difference(given))

    def _getSavedAPIPath(self, server='primary'):
        """
        To be overridden in inheriting class, for plugin configurations
        where the target server is malleable and stored in the Plugins
        storage or elsewhere.
        """
        return None

    def _performCall(self, default=None):
        """
        Acts as an entry point for all derivative classes to use the
        ExternalOperationsManager for performing remote calls.
        """
        return ExternalOperationsManager.execute(self,
                                                 "performCall",
                                                 self._performExternalCall,
                                                 default)

    def _performExternalCall(self, default=None):
        """
        Returns the raw results from the API to be handled elsewhere before
        being passed through to the report.
        """
        timeout = 10  # Timeout in seconds to end the call

        try:
            response = urllib2.urlopen(url=self.getAPIQuery(), timeout=timeout)
        except urllib2.URLError, e:
            # In case of timeout, log the incident and return the default value.
            logger = self.getLogger()
            logger.exception('Unable to retrieve data, exception: %s' % str(e))
            return default
        except:
            # For other exceptions, log the incident and return the default value.
            logger = self.getLogger()
            logger.exception('The remote server for %s did not respond.'
                            % self.getName())
            return default

        value = response.read()
        response.close()
        return value

    def _setHasJSHook(self, hasHook=True):
        self._hasJSHook = hasHook

    def _setHasDownloadListener(self, hasListener=True):
        self._hasDownloadListener = hasListener

    def clearAPIParams(self):
        """
        Clears the internal params buffer.
        """
        self._APIParams = {}

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
        path = self._APIPath

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
        return self._APIToken

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
            return self._APIQuery

        return self.getAPIPath(http, https, withScript) + self._APIQuery

    @staticmethod
    def getConferenceReport(**kwargs):
        """
        To be implemented in inheriting class.
        """
        return None

    @staticmethod
    def getContributionReport(**kwargs):
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
        return "/statistics/%s/"%self._name.lower() + self.PLUGIN_HOOKFILE

    def getAPIParams(self):
        """
        Returns the dictionary of API parameters currently in this
        implementation.
        """
        return self._APIParams

    def getImplementationPackage(self):
        """
        Returns a reference to the package which contains this implementation
        to avoid the use of introspection / reflection later.
        """
        return self._implementationPackage

    def getLogger(self):
        """
        Returns the logger for this implementation.
        """
        return self._config.getLogger(self.getName())

    def getName(self):
        """
        Returns the name of this implementation.
        """
        return self._name

    def getQueryResult(self):
        """
        To be overridden per implementation.
        """
        pass

    def hasJSHook(self):
        """
        Returns whether this implementation has a JSHook for tracking pageviews
        etc.
        """
        return self._hasJSHook

    def hasDownloadListener(self):
        """
        Returns whether this implementation has a download listener.
        """
        return self._hasDownloadListener

    def setAPIParams(self, params):
        """
        Internal mechanism for storing parameters for the query using
        a dictionary (params) of key=value.
        """
        for key, value in params.iteritems():

            if value is None:
                del self._APIParams[key]
            else:
                self._APIParams[key] = value

        self._paramsChanged = True

    def setAPIToken(self, token):
        """
        Sets the API token of this instance.
        """
        self._APIToken = token

    def trackDownload(self, obj):
        """
        To be overridden by those plugins which have a download listener.
        """
        pass

    @staticmethod
    def memoizeReport(function):
        """
        Decorator method for the get<reports> methods, see CachedReport for
        details on how this works with GenericCache.
        """

        @wraps(function)
        def wrapper(*args, **kwargs):
            return CachedReport(function).getReport(*args, **kwargs)

        return wrapper


class JSHookBase(object):
    """
    The base implementation of the hook object takes an instance of a
    plugin to populate with the dynamic parameters.
    """

    def __init__(self, instance):
        self.path = instance.getJSHookPath()
        self.url = instance.getAPIPath()


class CachedReport(object):
    """
    This class acts as a wrapper for functions which return a report object,
    by decorating the get<report> methods with the memonize function in the
    BaseStatisticsReport object, the result is wrapped here and its age
    is compared with the TTL if in the cache, either returning said item or
    allowing the method to generate a new one.
    """

    _config = StatisticsConfig()

    def __init__(self, function):
        self._function = function

        # Cache bucket per implementation
        plugin = function.__module__.split('.')[3]
        self._cache = GenericCache(plugin + 'StatisticsCache')

    def getReport(self, *args, **kwargs):
        """
        Ascertain if live updating first, if so disregard and continue.
        """

        ttl = self._config.getUpdateInterval()

        if not self._config.hasCacheEnabled():
            return self._function(*args, **kwargs)

        keyParams = list(args)
        keyParams.extend([self._function.__module__, self._function.__name__])
        key = self._generateKey(keyParams)

        resource = self._cache.get(key, None)

        if not resource:
            result = self._function(*args, **kwargs)
            self._cache.set(key, result, ttl)
            return result
        else:
            return resource

    def _generateKey(self, params):
        """
        Generates a unique key for caching against the params given.
        """
        return reduce(lambda x, y: str(x) + '-' + str(y), params)
