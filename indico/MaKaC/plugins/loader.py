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
import os, sys, pkg_resources

# database
from persistent import Persistent

# legacy MaKaC imports
from MaKaC.common.logger import Logger
from MaKaC.errors import PluginError

# package
from MaKaC.plugins.util import processPluginMetadata


class ModuleLoadException(Exception):
    pass

class PluginLoader(object):
    """
    Loads the plugins/types from the source code. Execution of the contained methods
    should be avoided (currently invoked manually), as it is naturally slow.

    TODO: Use setuptools extension points?
    """

    # A dictionary where the keys are plugin type names
    # and the values are modules (e.g. MaKaC.plugins.Collaboration)
    _ptypeModules = {}

    # A dictionary where the keys are plugin type names
    # and the values are plugin module dictionaries (plugin_name:module).
    _pmodules = {}

    _ptypesLoaded = set()
    _pluginsDir = os.path.abspath(sys.modules["MaKaC.plugins"].__path__[0])

    @classmethod
    def loadPlugins(cls):
        """
        Explores the subfolder structure of the MaKaC/plugins folder and loads the
        plugins into memory.
        """

        #we loop through all the files and folders of indico/MaKaC/plugins/
        for itemName in os.listdir(cls._pluginsDir):
            #we only go deeper for folders
            if os.path.isdir(os.path.join(cls._pluginsDir, itemName)):
                if not itemName in cls._ptypesLoaded:
                    cls.loadPluginType(itemName)
                    cls._ptypesLoaded.add(itemName)

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

        cls.loadPluginType(ptypeId)
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
    def getPluginByTypeAndId(cls, ptypeId, pluginName):
        """
        Returns the module object of a plugin given the names of the plugin and its
        type
        """
        if not ptypeId in cls._ptypesLoaded:
            cls.reloadPluginType(ptypeId)

        modulesDict = cls._pmodules[ptypeId]

        if pluginName in modulesDict:
            return modulesDict[pluginName]
        else:
            raise PluginError("Tried to get a plugin of the type %s with name %s "
                              "but there is no such plugin" % (ptypeId,
                                                               pluginName))

    @classmethod
    def getPluginTypeList(cls):
        """
        Returns a list of strings with the plugin types (names)
        """
        cls.loadPlugins()
        return list(cls._ptypesLoaded)

    @classmethod
    def importName(cls, moduleName, name):
        """
        Import a named object from a module in the context of this function,
        which means you should use fully qualified module paths.
        """

        try:
            # may raise ImportError (or others caused by the module's code)
            module = __import__(moduleName, globals(), locals(), [name])
        except:
            Logger.get('plugins.loader').exception(
                "Error loading %s ('%s')" % (moduleName,
                                             name))
            raise ModuleLoadException("Impossible to load %s ('%s')" % \
                                      (moduleName, name))


        # may raise KeyError
        objectToReturn = vars(module)[name]
        return objectToReturn

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
    def loadPluginType(cls, ptypeId):
        """
        Loads a plugin type, going through its source tree and loading each plugin
        as well.
        """

        # we load the plugin type module
        try:
            ptypeModule = cls.importName("MaKaC.plugins", ptypeId)
        except (ImportError, KeyError):
            raise Exception("Tried to load the plugin type: %s but the module "
                            "MaKaC.plugins.%s did not exist" % (ptypeId,
                                                                ptypeId))

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

        # check dependencies
        if len(missingDeps) > 0:
            # if some dependencies are not met, don't load submodules
            cls._pmodules[ptypeId] = {}

            Logger.get('plugins.loader').warning(
                "Plugin type %s has unmet dependencies. It will be deactivated." %
                ptypeId)
            return
        else:
            # absolute path of a plugin type folder
            ptypePath = os.path.join(cls._pluginsDir, ptypeId)

            # we loop through all the files and folders of the plugin type folder
            for itemName in os.listdir(ptypePath):

                # we strip the extension from the item name
                # splitext returns a tuple (name, file extension)
                cls._loadPluginFromDir(ptypePath, ptypeId, ptypeModule, itemName)

    @classmethod
    def _loadPluginFromDir(cls, ptypePath, ptypeId, ptypeModule, pid):
        """
        Loads a possible plugin from a directory
        """

        pid, ext = os.path.splitext(pid)

        # in case where we found a folder, i.e. a plugin folder
        if os.path.isdir(os.path.join(cls._pluginsDir, ptypeId, pid)):

            # we attempt to import the folder as a module.
            # This will only work if there's an __init__.py inside the folder
            try:
                pmodule = cls.importName(ptypeModule.__name__, pid)

            except (ImportError, KeyError):
                raise Exception("Tried to load the plugin  %s but the module "
                                "MaKaC.plugins.%s.%s did not exist. "
                                "Is there an __init__.py?" %
                                (ptypeId, ptypeId, pid))

            # we check that it was indeed a module.
            if pmodule:
                pmetadata = processPluginMetadata(pmodule)
            else:
                # Not a module? Nothing to do here...
                return

            # If it was a module, we check that the "type" field in the metadata
            # of the plugin corresponds to the plugin type we are currently processing
            if pmetadata['type'] == ptypeId:

                # if this is the first plugin for this plugin type
                if not ptypeId in cls._pmodules:
                    cls._pmodules[ptypeId] = {}

                missingDeps = cls._checkSetuptoolsDependencies(pmetadata['requires'],
                                                               pid)

                # save missing dependency info, so that the holder will know the
                # module state
                pmodule.__missing_deps__ = missingDeps

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

                #we build the path of the plugin
                pluginPath = os.path.join(ptypePath, pid)

                cls.loadSubModules(pmodule, pluginPath)
            else:
                Logger.get("plugins.loader").warning("Module of type %s inside %s" %
                                                     (pmetadata['type'],
                                                      ptypeId))

        elif ext == ".py" and pid != "__init__":
            ptypeSubModule = cls.importName(ptypeModule.__name__, pid)

            if ptypeSubModule:
                cls._ptypeModules[ptypeId].__dict__[pid] = ptypeSubModule


    @classmethod
    def loadSubModules(cls, module, modulePath):
        """
        Loads the submodules of a plugin (recursively)
        """

        #dictionary whose keys are submodule names, and whose values are module objects
        foundSubModules = {}

        #we check the files in the module folder
        for itemName in os.listdir(modulePath):

            # we strip the extension from the item name
            itemName, ext = os.path.splitext(itemName)

            # if the item is a directory, we may have found a subpackage
            if os.path.isdir(os.path.join(modulePath, itemName)):

                try:
                    subModule = cls.importName(module.__name__, itemName)
                except KeyError:
                    # we hit a folder that is not a package, such
                    # plugins are allowed to have those
                    continue


                # we store the submodule in the foundSubModules dictionary
                foundSubModules[itemName] = subModule
                # we make a recursive call
                cls.loadSubModules(subModule, os.path.join(modulePath, itemName))

            # if the item is a .py file and not __init__, it's a submodule that is
            # not a package
            elif ext == ".py" and itemName != "__init__":

                # this should return a subModule, unless there
                # has been an error during import
                subModule = cls.importName(module.__name__, itemName)
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
