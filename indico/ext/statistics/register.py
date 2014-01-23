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

from MaKaC.common.logger import Logger
from MaKaC.plugins.base import PluginsHolder
from indico.ext.register import Register


class StatisticsRegister(Register):
    """
    This register acts as both a wrapper against the legacy PluginsHolder
    and a quick-access object for injecting tracking codes etc into the
    extension points of Indico.
    """

    def _buildRegister(self):
        """
        Static mapping attributes for plugin implementations in register.
        Append lines to add further implementations.
        """
        from indico.ext.statistics.piwik.implementation import PiwikStatisticsImplementation

        self._registeredImplementations['Piwik'] = PiwikStatisticsImplementation

    def getAllPluginJSHooks(self, extra=None, includeInactive=False):
        """
        Returns a list of JSHook objects which contain the parameters
        required to propagate a hook with the data it needs. If extra is
        defined, it is assumed that the JSHook object is expecting it as a
        parameter.
        """
        hooks = []

        for plugin in self.getAllPlugins():

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

        for plugin in self.getAllPlugins():

            if plugin.hasDownloadListener():
                listeners.append(plugin)

        return listeners

    def getAllPluginJSHookPaths(self):
        """
        Returns a list of all the paths to JSHook TPL files for registered
        plugins
        """
        paths = []

        for plugin in self.getAllPlugins():

            if plugin.hasJSHook():
                paths.append(plugin.getJSHookPath())

        return paths

    def getJSInjectionPath(self):
        """
        Returns the path to the loop tpl file to inject different hooks into
        events.
        """
        filename = 'StatisticsHookInjection.tpl'
        return "/statistics/" + filename

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
