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
        'testPlugin': False
        }

    if not hasattr(obj, '__metadata__'):
        Logger.get('plugins.util').error('Plugin %s has no __metadata__ entry!' %
                                         obj)
        raise NoPluginMetadataException(obj)
    return dict((key, obj.__metadata__.get(key, _defaults[key])) for key in \
                _defaults)



class PluginsWrapper(object):
    def __init__(self, pluginType, plugin):
        self._pluginType = pluginType
        self._plugin = plugin
        try:
            from MaKaC.plugins import PluginsHolder
            self._plugin = PluginsHolder().getPluginType(pluginType).getPlugin(plugin)
        except Exception, e:
            Logger.get('Plugins').error("Exception while trying to access either the plugin type %s or the plugin %s: %s" % (pluginType, plugin, str(e)))
            raise Exception("Exception while trying to access either the plugin type %s or the plugin %s: %s" % (pluginType, plugin, str(e)))

    def isActive(self):
        return self._plugin.isActive()

class PluginFieldsWrapper(PluginsWrapper):
    """Provides a simple interface to access fields of a given plugin"""

    def __init__(self, pluginType, plugin):
        PluginsWrapper.__init__(self, pluginType, plugin)

    def getOption(self, optionName):
        try:
            return self._plugin.getOption(optionName).getValue()
        except Exception, e:
            Logger.get('Plugins').error("Exception while trying to access the option %s in the plugin %s: %s" % (self._pluginType, self._plugin, str(e)))
            raise Exception("Exception while trying to access the option %s in the plugin %s: %s" % (self._pluginType, self._plugin, str(e)))

    def getAttribute(self, attribute):
        try:
            return getattr(self._plugin, attribute)
        except AttributeError:
            Logger.get('Plugins').error("No attribute %s in plugin %s" % (attribute, self._plugin))
            raise Exception("No attribute %s in plugin %s" % (attribute, self._plugin))

    def getStorage(self):
        return self._plugin.getStorage()