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

"""
This module defines the PluginLoader class, that is responsible for providing methods
that allow loading plugins from the python path, and cataloguing them accordingly
"""

# system imports
import os, sys, pkg_resources, pkgutil

# database
from persistent import Persistent

# legacy MaKaC imports
from MaKaC.common.logger import Logger
from MaKaC.errors import PluginError

# package
from MaKaC.plugins.util import processPluginMetadata
import indico.ext

class ModuleLoadException(Exception):
    pass

class PluginLoader(object):
    """
    Loads the plugins/types from the source code. Execution of the contained methods
    should be avoided (currently invoked manually), as it is naturally slow.
    """

    # A dictionary where the keys are plugin type names
    # and the values are modules (e.g. MaKaC.plugins.Collaboration)
    _ptypeModules = {}

    # A dictionary where the keys are plugin type names
    # and the values are plugin module dictionaries (plugin_name:module).
    _pmodules = {}

    _ptypesLoaded = set()

    @classmethod
    def loadPlugins(cls):
        """
        Explores the subfolder structure of the MaKaC/plugins folder and loads the
        plugins into memory.
        """

        # get all available plugin types
        ptypes = pkg_resources.iter_entry_points('indico.ext_types')

        for epoint in ptypes:
            if not epoint.name in cls._ptypesLoaded:
                cls.loadPluginType(epoint.name, epoint.module_name)
                cls._ptypesLoaded.add(epoint.name)

    @classmethod
    def reloadPlugins(cls):
        """
        Forces the reload of all plugins if they are already in memory
        """
        cls._ptypeModules = {}
        cls._pmodules = {}
        cls._ptypesLoaded = set()
        cls.loadPlugins()

    @classmethod
    def reloadPluginType(cls, ptypeId):
        """
        Forces the reload of all plugins in a type if they are already in memory
        """
        if ptypeId in cls._ptypesLoaded:
            del cls._ptypeModules[ptypeId]
            cls._pmodules[ptypeId] = {}
            cls._ptypesLoaded.remove(ptypeId)

        ptypes = dict((ep.name, ep.module_name) for ep in pkg_resources.iter_entry_points('indico.ext_types'))

        print ptypes

        cls.loadPluginType(ptypeId, ptypes[ptypeId])
        cls._ptypesLoaded.add(ptypeId)

    @classmethod
    def getPluginsByType(cls, ptypeId):
        """
        Given a plugin type name (e.g. "Collaboration"), a list of modules
        corresponding to the plugins of that type is returned.
        """
        if not ptypeId in cls._ptypesLoaded:
            cls.reloadPluginType(ptypeId)
        return cls._pmodules[ptypeId].values()

    @classmethod
    def getPluginType(cls, ptypeId):
        """
        Returns the module object of a plugin type given its name
        """
        if not ptypeId in cls._ptypesLoaded:
            cls.reloadPluginType(ptypeId)

        return cls._ptypeModules[ptypeId]

    @classmethod
    def getPluginByTypeAndId(cls, ptypeId, pid):
        """
        Returns the module object of a plugin given the names of the plugin and its
        type
        """
        if not ptypeId in cls._ptypesLoaded:
            cls.reloadPluginType(ptypeId)

        modulesDict = cls._pmodules[ptypeId]

        if pid in modulesDict:
            return modulesDict[pid]
        else:
            raise PluginError("Tried to get a plugin of the type %s with id %s "
                              "but there is no such plugin" % (ptypeId,
                                                               pid))

    @classmethod
    def getPluginTypeList(cls):
        """
        Returns a list of strings with the plugin types (names)
        """
        cls.loadPlugins()
        return list(cls._ptypesLoaded)

    @classmethod
    def importName(cls, moduleName, mayFail = False):
        """
        Import a named object from a module in the context of this function,
        which means you should use fully qualified module paths.
        """

        try:
            # may raise ImportError (or others caused by the module's code)
            module = __import__(moduleName, globals(), locals())
        except ImportError:
            if mayFail:
                return None
            else:
                Logger.get('plugins.loader').exception("Error loading %s" % moduleName)
                raise ModuleLoadException("Impossible to load %s" % moduleName)
        except:
            Logger.get('plugins.loader').exception("Error loading %s" % moduleName)
            raise ModuleLoadException("Impossible to load %s" % moduleName)


        return sys.modules[moduleName]

    @classmethod
    def _checkSetuptoolsDependencies(cls, deplist, name):
        """
        Checks the dependencies for a given plugin/type, using setuptools
        """
        missing = []

        for dep in deplist:
            try:
                pkg_resources.require(dep)
            except pkg_resources.DistributionNotFound:
                Logger.get('plugins.loader').warning("Requirement '%s' not met for %s" %
                                                     (dep, name))
                missing.append(dep)

        return missing

    @classmethod
    def loadPluginType(cls, ptypeId, ptypeModulePath):
        """
        Loads a plugin type, going through its source tree and loading each plugin
        as well.
        """

        # we load the plugin type module
        ptypeModule = cls.importName(ptypeModulePath)

        metadata = processPluginMetadata(ptypeModule)

        # check if the plugin should be ignored
        if metadata['ignore']:
            # stop loading here!
            return

        #if ignore == False, we store the plugin type module in cls._ptypeModules
        cls._ptypeModules[ptypeId] = ptypeModule

        missingDeps = cls._checkSetuptoolsDependencies(metadata['requires'],
                                                       ptypeId)

        # save missing dependency info, so that the holder will know the module state
        ptypeModule.__missing_deps__ = missingDeps
        # save id information
        ptypeModule.__ptype_id__ = ptypeId

        cls._pmodules[ptypeId] = {}

        # check dependencies
        if len(missingDeps) > 0:
            # if some dependencies are not met, don't load submodules
            Logger.get('plugins.loader').warning(
                "Plugin type %s has unmet dependencies. It will be deactivated." %
                ptypeId)
            return
        else:
            pluginEps = pkg_resources.iter_entry_points('indico.ext')

            # we loop through all the specified plugins
            for epoint in pluginEps:
                mname = epoint.module_name

                # ignore plugins that don't match our plugin type
                if not epoint.name.startswith("%s." % ptypeId):
                    continue
                else:
                    print epoint, ptypeId

                    pid = epoint.name[len(ptypeId) + 1:]
                    # load plugin files
                    cls._loadPluginFromDir(mname, ptypeId, ptypeModule, pid)

            # load submodules too
            cls._loadSubModules(ptypeModule)

    @classmethod
    def _loadPluginFromDir(cls, pModuleName, ptypeId, ptypeModule, pid):
        """
        Loads a possible plugin from a directory
        """

        # we attempt to import the module.
        try:
            pmodule = cls.importName(pModuleName)
        except (ImportError, KeyError):
            raise Exception("Tried to load the plugin  %s but the module "
                            "%s does not exist. "
                            "Is there an __init__.py?" %
                            (pid, pModuleName))

        ppath = pmodule.__path__[0]
        pmetadata = processPluginMetadata(pmodule)

        # If it was a module, we check that the "type" field in the metadata
        # of the plugin corresponds to the plugin type we are currently processing
        if pmetadata['type'] == ptypeId:

            missingDeps = cls._checkSetuptoolsDependencies(pmetadata['requires'],
                                                           pid)

            # save missing dependency info, so that the holder will know the
            # module state
            pmodule.__missing_deps__ = missingDeps

            # save the plugin id, so that the holder will know it
            pmodule.__plugin_id__ = pid

            # check dependencies
            if len(missingDeps) > 0:
                # if some dependencies are not met, don't load submodules
                cls._pmodules[ptypeId][pid] = pmodule

                Logger.get('plugins.loader').warning(
                    "Plugin %s has unmet dependencies. It will be deactivated." %
                    pid)
                return


            cls._ptypeModules[ptypeId].__dict__[pid] = pmodule

            # we store the module inside the cls._pmodules object
            cls._pmodules[ptypeId][pid] = pmodule

            # load submodules too
            cls._loadSubModules(pmodule)
        else:
            Logger.get("plugins.loader").warning("Module of type %s inside %s" %
                                                 (pmetadata['type'],
                                                  ptypeId))

    @classmethod
    def _loadSubModules(cls, module):
        """
        Loads the submodules of a plugin (recursively)
        """

        modulePath = module.__path__[0]

        #dictionary whose keys are submodule names, and whose values are module objects
        foundSubModules = {}

        #we check the files in the module folder
        for itemName in os.listdir(modulePath):

            # we strip the extension from the item name
            itemName, ext = os.path.splitext(itemName)

            # if the item is a directory, we may have found a subpackage
            if os.path.isdir(os.path.join(modulePath, itemName)):

                subModule = cls.importName("%s.%s" % (module.__name__, itemName),
                                           mayFail = True)

                # we hit a folder that is not a package, such
                # plugins are allowed to have those
                if subModule == None:
                    continue

                # we store the submodule in the foundSubModules dictionary
                foundSubModules[itemName] = subModule

                if not subModule.__name__.split('.')[-1].startswith('test'):
                    # we make a recursive call
                    cls._loadSubModules(subModule)

            # if the item is a .py file and not __init__, it's a submodule that is
            # not a package
            elif ext == ".py" and itemName != "__init__":

                # this should return a subModule, unless there
                # has been an error during import
                subModule = cls.importName("%s.%s" % (module.__name__, itemName))
                foundSubModules[itemName] = subModule

        # once we have found all the submodules, we make sure they are in the
        # __dict__ of the module:
        for subModuleName, subModule in foundSubModules.iteritems():
            module.__dict__[subModuleName] = subModule

            # also, if there is a "modules" variable in the __init__.py of the
            # plugin, we store the submodules there
            # (needed by legacy epayment modules)
            if hasattr(module, "modules"):
                module.modules[subModuleName] = subModule


class GlobalPluginOptions(Persistent):
    """
    A class that stores global information about all plugins.
    """

    def __init__(self):
        self.__id = "globalPluginOptions"
        self.__reloadAllWhenViewingAdminTab = False

    def getId(self):
        return self.__id

    def getReloadAllWhenViewingAdminTab(self):
        return self.__reloadAllWhenViewingAdminTab

    def setReloadAllWhenViewingAdminTab(self, value):
        self.__reloadAllWhenViewingAdminTab = value
