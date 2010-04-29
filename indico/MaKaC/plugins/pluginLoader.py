# -*- coding: utf-8 -*-
##
## $Id: base.py,v 1.13 2009/04/14 11:09:56 dmartinc Exp $
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
import sys

from MaKaC.errors import PluginError

class PluginLoader(object):
    """ Utility class that has methods to deal with plugins at low level.

        There is an important class variable "_pluginsLoaded" that will store if the plugins have already been loaded in this request.
        Sometimes a single request will need information about the plugins multiple times, in this way they are only loaded once.
        Ideally plugins should only be loaded once during the execution time of the Apache Server but different request don't
        (normally) share memory so this variable will (normally) start with a value of False.
        However sometimes it happens that the value of this variable can be True at the beginning of a request, and plugins are
        already loaded into memory. It is not clear when this happens; probably it depends on the execution model of Apache
        (prefork or multithread). Even with prefork, sometimes Apache (or mod_python) seems to recycle processes from one request
        to the next and the plugins will be in memory at the beginning of a request.

        Methods that should be used from outside:
        -loadPlugins: explores the subfolder structure of the MaKaC/plugins folder and loads the plugins into memory.
                      the modules are stored into the class attribute "pluginList"
                      the dictionaries with the plugin options, if existant, are stored into the class attribute "pluginTypeOptions"
                      the plugin descriptions, if existant, are stored into the class attribute "pluginTypeDescriptions"
        -reloadPlugins: forces to reload the plugins if they are already in memory
        -reloadPluginType: forces to reload plugins if they are already in memory, but only those of a given type (e.g. "epayment", "Collaboration").
        -getPluginByTypeAndName: given a type (e.g. "Collaboration"), and a name (e.g. "EVO"), a module object corresponding to that plugin is returned
        -getPluginType: given a type (e.g. "Collaboration"), a module object corresponding to that plugin type is returned
        -getTypeList: returns a list of strings with the plugin types (e.g. ["epayment", "Collaboration"]
    """

    # A dictionary where the keys are plugin type names (e.g. "Collaboration", "RoomBooking",
    # and the values are modules (e.g. MaKaC.plugins.Collaboration)
    pluginTypeModules = {}

    # A dictionary where the keys are plugin type names (e.g. "Collaboration", "RoomBooking",
    # and the values are also dictionaries.
    # These second-level dictionaries have plugin names as keys (e.g. "EVO", "Vidyo"),
    # and python module objects as values
    pluginModules = {}

    pluginTypesLoaded = set()

    pluginsDir = os.path.abspath(sys.modules["MaKaC.plugins"].__path__[0])

    @classmethod
    def loadPlugins(cls):
        """ Explores the subfolder structure of the MaKaC/plugins folder and loads the plugins into memory.
            The modules are stored into the class attribute "pluginModules"
            The dictionaries with the plugin options, if existant, are stored into the class attribute "pluginTypeOptions"
            The plugin descriptions, if existant, are stored into the class attribute "pluginTypeDescriptions"
        """
        #we loop through all the files and folders of indico/MaKaC/plugins/
        for itemName in os.listdir(cls.pluginsDir):

            #we only go deeper for folders
            if os.path.isdir(os.path.join(cls.pluginsDir, itemName)):
                if not itemName in cls.pluginTypesLoaded:
                    cls.loadPluginType(itemName)
                    cls.pluginTypesLoaded.add(itemName)

    @classmethod
    def reloadPlugins(cls):
        """ Forces to reload the plugins if they are already in memory
        """
        cls.pluginTypeModules = {}
        cls.pluginModules = {}
        cls.pluginTypesLoaded = set()
        cls.loadPlugins()

    @classmethod
    def reloadPluginType(cls, pluginTypeName):
        """ Forces to reload plugins if they are already in memory, but only those of a given type (e.g. "epayment", "Collaboration").
        """
        if pluginTypeName in cls.pluginTypesLoaded:
            del cls.pluginTypeModules[pluginTypeName]
            cls.pluginModules[pluginTypeName] = {}
            cls.pluginTypesLoaded.remove(pluginTypeName)

        cls.loadPluginType(pluginTypeName)
        cls.pluginTypesLoaded.add(pluginTypeName)

    @classmethod
    def getPluginsByType(cls, pluginTypeName):
        """ Given a plugin type name (e.g. "Collaboration"), a list of modules corresponding to the plugins of that type is returned.
        """
        if not pluginTypeName in cls.pluginTypesLoaded:
            cls.reloadPluginType(pluginTypeName)

        return cls.pluginModules[pluginTypeName].values()

    @classmethod
    def getPluginType(cls, pluginTypeName):
        """ Returns the module of a plugin type given its name
            e.g. pluginTypeName = "Collaboration" will return the MaKaC.plugins.Collaboration module object
        """
        if not pluginTypeName in cls.pluginTypesLoaded:
            cls.reloadPluginType(pluginTypeName)

        return cls.pluginTypeModules[pluginTypeName]

    @classmethod
    def getPluginByTypeAndName(cls, pluginTypeName, pluginName):
        """ Returns the module of a plugin given the names of the plugin and its type,
            e.g. pluginTypeName = "Collaboration" and pluginName = "EVO"
        """
        if not pluginTypeName in cls.pluginTypesLoaded:
            cls.reloadPluginType(pluginTypeName)

        modulesDict = cls.pluginModules[pluginTypeName]

        if pluginName in modulesDict:
            return modulesDict[pluginName]
        else:
            raise PluginError("Tried to get a plugin of the type " + pluginTypeName + " with name " + pluginName + " but there is no plugin called " + pluginName)

    @classmethod
    def getPluginTypeList(cls):
        """ Returns a list of strings with the plugin types (e.g. ["epayment", "Collaboration"]
        """
        cls.loadPlugins()
        return list(cls.pluginTypesLoaded)

    @classmethod
    def importName(cls, moduleName, name):
        """ Import a named object from a module in the context of this function,
            which means you should use fully qualified module paths.

            Return None on failure.
        """

        #may raise ImportError
        module = __import__(moduleName, globals(), locals(), [name]) #check docs on built-in __import__ to understand :)

        #may raise KeyError
        objectToReturn = vars(module)[name]

        return objectToReturn

    @classmethod
    def loadPluginType(cls, pluginTypeName):

        #we load the plugin type module
        try:
            pluginTypeModule = cls.importName("MaKaC.plugins", pluginTypeName)
        except ImportError:
            raise Exception("Tried to load the plugin type: %s but the module MaKaC.plugins.%s did not exist" % (pluginTypeName, pluginTypeName))
        except KeyError:
            raise Exception("Tried to load the plugin type: %s but the module MaKaC.plugins.%s did not exist" % (pluginTypeName, pluginTypeName))

        # we build the package name of a plugin type, e.g. MaKaC.plugins.Collaboration
        pluginTypePackageName = "MaKaC.plugins.%s" % pluginTypeName

        #we check that the plugin type does not have an "ignore" attribute
        ignore = False
        try:
            ignore = cls.importName(pluginTypePackageName, "ignore")
        except KeyError:
            pass

        if ignore is True:
            return

        #if ignore == False, we store the plugin type module in cls.pluginTypeModules
        cls.pluginTypeModules[pluginTypeName] = pluginTypeModule

        # absolute path of a plugin type folder, e.g. /xxxxx/MaKaC/plugins/Collaboration/
        pluginTypePath = os.path.join(cls.pluginsDir, pluginTypeName)

        #we loop through all the files and folders of the plugin type folder
        for itemName in os.listdir(pluginTypePath):

            # we strip the extension from the item name
            # splitext returns a tuple (name, file extension). Ex: ("conference", ".py")
            # if no extension, the 2nd element of the tuple will be an empty string
            itemName, ext = os.path.splitext(itemName)

            # case where we found a folder, i.e. a plugin folder (e.g. /xxxx/MaKaC/plugins/Collaboration/EVO/)
            if os.path.isdir(os.path.join(cls.pluginsDir, pluginTypeName, itemName)):

                # we attempt to import the folder as a module. This will only work if there's an __init__.py inside the folder
                try:
                    pluginModule = cls.importName(pluginTypePackageName, itemName)

                except ImportError:
                    raise Exception("Tried to load the plugin  %s but the module MaKaC.plugins.%s.%s did not exist. Is there an __init__.py?" % (pluginTypeName, pluginTypeName, itemName))
                except KeyError:
                    raise Exception("Tried to load the plugin  %s but the module MaKaC.plugins.%s.%s did not exist. Is there an __init__.py?" % (pluginTypeName, pluginTypeName, itemName))

                # we check that it was indeed a module. If it was, we check that there is a
                # "pluginType" variable in the __init__.py of the plugin and that it corresponds
                # to the plugin type we are currently processing
                if pluginModule and pluginTypeName == pluginModule.pluginType:

                    cls.pluginTypeModules[pluginTypeName].__dict__[itemName] = pluginModule

                    #if this is the first plugin for this plugin type, we add
                    #a new key to the cls.pluginModules dictionary
                    if not pluginTypeName in cls.pluginModules.keys():
                        cls.pluginModules[pluginTypeName] = {}

                    #we store the module inside the cls.pluginModules object
                    #note: we do not use itemName (the name of the folder) and use instead
                    #      the "pluginName" variable in the __init__.py file of the plugin,
                    #      which is its "true" name
                    cls.pluginModules[pluginTypeName][pluginModule.pluginName] = pluginModule

                    #we build the path of the plugin
                    pluginPath = os.path.join(pluginTypePath, itemName)

                    cls.loadSubModules(pluginModule, pluginPath)

            elif ext == ".py" and itemName != "__init__":

                pluginTypeSubModule = cls.importName(pluginTypePackageName, itemName)

                if pluginTypeSubModule:
                    cls.pluginTypeModules[pluginTypeName].__dict__[itemName] = pluginTypeSubModule




    @classmethod
    def loadSubModules(cls, module, modulePath):

        #dictionary whose keys are submodule names, and whose values are module objects
        #after finding the submodules, we will add them to the __dict__ of the module
        foundSubModules = {}

        #we check the files in the module folder
        for itemName in os.listdir(modulePath):

            # we strip the extension from the item name
            # splitext returns a tuple (name, file extension). Ex: ("conference", ".py")
            # if no extension, the 2nd element of the tuple will be an empty string
            itemName, ext = os.path.splitext(itemName)

            #if the item is a directory, we may have found a subpackage (also a submodule)
            if os.path.isdir(os.path.join(modulePath, itemName)):

                #this will return a module if the subdirectory has an __init__.py inside, otherwise will raise KeyError
                try:
                    subModule = cls.importName(module.__name__, itemName)
                except KeyError:
                    #we hit a folder that is not a package, such
                    #plugins are allowed to have those
                    continue


                #we store the submodule in the foundSubModules dictionary
                foundSubModules[itemName] = subModule
                #we make a recursive call
                cls.loadSubModules(subModule, os.path.join(modulePath, itemName))

            #if the item is a .py file and not __init__, its a submodule that is not a package
            elif ext == ".py" and itemName != "__init__":

                #this should return a subModule, unless there has been an error during import
                subModule = cls.importName(module.__name__, itemName)

                foundSubModules[itemName] = subModule


        #once we have found all the submodules, we make sure they are in the __dict__ of the module:
        for subModuleName, subModule in foundSubModules.iteritems():
            module.__dict__[subModuleName] = subModule
            #also, if there is a "modules" variable in the __init__.py of the plugin, we store the submodules there
            #(needed by epayment plugins, for example)
            if hasattr(module, "modules"):
                module.modules[subModuleName] = subModule
