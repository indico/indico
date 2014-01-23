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
from MaKaC.plugins.base import extension_point
from indico.ext.register import Register

class SearchRegister(Register):
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
        self._registeredImplementations =  dict((key, value) for (key, value) in extension_point("getPluginImplementation"))

    def getDefaultSearchEngineAgent(self):
        """
        Returns an individual plugin from the register by name of class,
        """
        return self.getPluginByName(SearchConfig().getDefaultSearchEngineAgent(), instantiate=False)

    def getDefaultSearchEngineAgentName(self):
        """
        Returns an individual plugin from the register by name of class,
        """
        return SearchConfig().getDefaultSearchEngineAgent()

class SearchConfig(object):
    """
    The current overall configuration of the plugin, wrapper around global
    options in PluginsHolder / plugin administration.
    """

    def setDefaultSearchEngineAgent(self, value):
        """
        Sets the default Search Engine Agent of the plugin
        """
        searchPlugin = PluginsHolder().getPluginType('search')
        searchPlugin.getOptions()['defaultSearch'].setValue(value)

    def getDefaultSearchEngineAgent(self):
        """
        Returns the default Search Engine Agent of the plugin
        """
        searchPlugin = PluginsHolder().getPluginType('search')
        return searchPlugin.getOptions()['defaultSearch'].getValue()

    def getSearchEngineAgentList(self):
        """
        Returns the default Search Engine Agent of the plugin
        """
        searchPlugin = PluginsHolder().getPluginType('search')
        return searchPlugin.getPlugins().keys()

    def getLogger(self, extraName=None):
        """
        Returns a Logger object for Statistics as a whole or per plugin.
        """
        logName = 'ext.search'

        if extraName:
            logName += '.' + extraName

        return Logger.get(logName)
