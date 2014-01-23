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

class Register(object):
    """
    This register acts as both a wrapper against the legacy PluginsHolder
    and a quick-access object for injecting tracking codes etc into the
    extension points of Indico.
    """

    def __init__(self):
        self._registeredImplementations = {}
        self._buildRegister()

    def _getRegister(self):
        return self._registeredImplementations

    def _reInit(self):
        """
        Reinitialises the register, removes the saved attributes from the DB
        instance and reinstantiates based on those defined in _buildRegister()
        """
        self.clearAll()
        self._buildRegister()

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

    def hasActivePlugins(self):
        """
        Returns True only if any implementations are active in the PluginsHolder
        """
        # The resultant activePlugins is only True if there are any plugins.
        return bool(self.getAllPlugins(False, True))

    def getAllPluginNames(self):
        """
        Returns a list of all the plugin names (Strings).
        """
        return self._getRegister().keys()
