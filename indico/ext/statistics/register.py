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

import os

from MaKaC.common.logger import Logger
from MaKaC.plugins.base import PluginsHolder


class StatisticsRegister():
    """
    This register acts as both a wrapper against the legacy PluginsHolder
    and a quick-access object for injecting tracking codes etc into the
    extension points of Indico.
    """

    def __init__(self):
        self._registeredImplementations = {}
        self._buildRegister()

    def _buildRegister(self):
        """
        Static mapping attributes for plugin implementations in register.
        Append lines to add further implementations.
        """
        from indico.ext.statistics.piwik.implementation import PiwikStatisticsImplementation

        self._registeredImplementations['Piwik'] = PiwikStatisticsImplementation

    def _getPluginOSPath(self):
        """
        Returns the absolute OS path to this plugin, with ending slash included.
        """
        import indico.ext.statistics
        return os.path.join(indico.ext.statistics.__path__)[0] + '/'

    def _getRegister(self):
        return self._registeredImplementations

    def _reInit(self):
        """
        Reinitialises the register, removes the saved attributes from the DB
        instance and reinstantiates based on those defined in _buildRegister()
        """
        self.clearAll()
        self._buildRegister()

    def hasActivePlugins(self):
        """
        Returns True only if any implementations are active in the PluginsHolder
        """

        activePlugins = list(p for p in self.getAllPlugins(True) if p.isActive())

        # The resultant activePlugins is only True if there are any plugins.
        return bool(activePlugins)

    def getAllPlugins(self, instantiate=True, activeOnly=False):
        """
        Returns a list of all plugin class registered, if instantiate is
        True, instates all objects before appending to the list. By default
        this method only returns active implementations, however all implementations
        may be returned by setting activeOnly to True.
        """
        result = []

        if instantiate:
            for plugin in self._getRegister().values():

                if activeOnly and not plugin().isActive():
                    continue

                result.append(plugin())
        else:
            if activeOnly:
                result = list(p for p in self._getRegister().values() if p().isActive())
            else:
                result = self._getRegister().values()

        return result

    def getAllPluginNames(self):
        """
        Returns a list of all the plugin names (Strings).
        """
        return self._getRegister().keys()

    def getAllPluginJSHooks(self, extra=None, includeInactive=False):
        """
        Returns a list of JSHook objects which contain the parameters
        required to propagate a hook with the data it needs. If extra is
        defined, it is assumed that the JSHook object is expecting it as a
        parameter.
        """
        hooks = []

        for plugin in self.getAllPlugins(True):

            if (not includeInactive and not plugin.isActive()) \
                or not plugin.hasJSHook():
                continue

            if extra is not None:
                hook = plugin.getJSHookObject()(plugin, extra)
            else:
                hook = plugin.getJSHookObject()(plugin)

            hooks.append(hook)

        return hooks

    def getAllPluginDownloadListeners(self):
        """
        Returns a list of all the plugins which have a listener for tracking
        downloads.
        """
        listeners = []

        for plugin in self.getAllPlugins(True):

            if plugin.hasDownloadListener():
                listeners.append(plugin)

        return listeners

    def getAllPluginJSHookPaths(self):
        """
        Returns a list of all the paths to JSHook TPL files for registered
        plugins
        """
        paths = []

        for plugin in self.getAllPlugins(True):

            if plugin.hasJSHook():
                paths.append(plugin.getJSHookPath())

        return paths

    def getJSInjectionPath(self):
        """
        Returns the path to the loop tpl file to inject different hooks into
        events.
        """
        filename = 'StatisticsHookInjection.tpl'
        return self._getPluginOSPath() + 'tpls/' + filename

    def getPluginByName(self, plugin, instantiate=True):
        """
        Returns an individual plugin from the register by name of class,
        returns an instantiated method if instantiate set to True.
        """
        if plugin in self._getRegister():
            if not instantiate:
                return self._getRegister()[plugin]
            else:
                return self._getRegister()[plugin]()
        else:
            return None


class StatisticsConfig(object):
    """
    The current overall configuration of the plugin, wrapper around global
    options in PluginsHolder / plugin administration.
    """

    def getUpdateInterval(self):
        """
        Returns the interval for which cached values should live before
        new data is requested from the server.
        """
        statsPlugin = PluginsHolder().getPluginType('statistics')
        return statsPlugin.getOptions()['cacheTTL'].getValue()

    def hasCacheEnabled(self):
        """
        True if the plugin is configured for cached reporting.
        """
        statsPlugin = PluginsHolder().getPluginType('statistics')
        return statsPlugin.getOptions()['cacheEnabled'].getValue()

    def getLogger(self, extraName=None):
        """
        Returns a Logger object for Statistics as a whole or per plugin.
        """
        logName = 'ext.statistics'

        if extraName:
            logName += '.' + extraName

        return Logger.get(logName)
