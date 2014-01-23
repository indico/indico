# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

from MaKaC.common.logger import Logger

class NoPluginMetadataException(Exception):
    pass

def processPluginMetadata(obj):
    _defaults = {
        'name': '',
        'description': '',
        'type': '',
        'ignore': False,
        'visible': True,
        'testPlugin': False,
        'requires': []
        }

    if not hasattr(obj, '__metadata__'):
        Logger.get('plugins.util').error('Plugin %s has no __metadata__ entry!' %
                                         obj)
        raise NoPluginMetadataException(obj)
    return dict((key, obj.__metadata__.get(key, _defaults[key])) for key in \
                _defaults)



class PluginsWrapper(object):
    def __init__(self, pluginType, plugin=None):
        self._pluginType = pluginType
        self._plugin = plugin
        try:
            from MaKaC.plugins import PluginsHolder
            if self._plugin:
                self._plugin = PluginsHolder().getPluginType(pluginType).getPlugin(plugin)
            else:
                self._pluginType = PluginsHolder().getPluginType(pluginType)
        except Exception, e:
            Logger.get('Plugins').error("Exception while trying to access either the plugin type %s or the plugin %s: %s" % (pluginType, plugin, str(e)))
            raise Exception("Exception while trying to access either the plugin type %s or the plugin %s: %s" % (pluginType, plugin, str(e)))

    def isActive(self):
        return self._plugin.isActive()

class PluginFieldsWrapper(PluginsWrapper):
    """Provides a simple interface to access fields of a given plugin"""

    def __init__(self, pluginType, plugin=None):
        PluginsWrapper.__init__(self, pluginType, plugin)

    def getOption(self, optionName):
        try:
            if self._plugin:
                return self._plugin.getOption(optionName).getValue()
            else:
                return self._pluginType.getOption(optionName).getValue()
        except Exception, e:
            Logger.get('Plugins').error("Exception while trying to access the option %s in the plugin %s: %s" % (self._pluginType, self._plugin, str(e)))
            raise Exception("Exception while trying to access the option %s in the plugin %s: %s" % (self._pluginType, self._plugin, str(e)))

    def getAttribute(self, attribute):
        try:
            if self._plugin:
                return getattr(self._plugin, attribute)
            else:
                return getattr(self._pluginType, attribute)
        except AttributeError:
            Logger.get('Plugins').error("No attribute %s in plugin %s" % (attribute, self._plugin))
            raise Exception("No attribute %s in plugin %s" % (attribute, self._plugin))

    def getStorage(self):
        return self._plugin.getStorage()
