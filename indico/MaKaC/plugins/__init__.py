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
import sys

""" This purpose of this file is low-level handling of plugins.
    It has functions to find the folder structure of the plugins, load them into memory, etc.
    The functions can be used through class methods of the "Plugins" class. See its description for more details.
"""

import os
import MaKaC

from MaKaC.errors import MaKaCError, PluginError

basePath = os.path.normpath(os.path.split(MaKaC.__path__[0])[0])

def importName(modulename, name):
    """ Import a named object from a module in the context of this function,
        which means you should use fully qualified module paths.

        Return None on failure.
    """
    try:
        module = __import__(modulename, globals(), locals(), [name])
    except ImportError:
        #raise "%s - %s"%(modulename, name)
        return None
    try:
        return vars(module)[name]
    except:
        return None

def absToRelative(absPath, fromPath):
    if os.path.isabs(absPath):
        return absPath[len(fromPath)+len(os.path.sep):]
    return absPath


class Plugins:
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
        -reloadPluginsByType: forces to reload plugins if they are already in memory, but only those of a given type (e.g. "epayment", "Collaboration").
        -getPluginByTypeAndName: given a type (e.g. "Collaboration"), and a name (e.g. "EVO") a module object corresponding to that plugin is returned
        -getTypeList: returns a list of strings with the plugin types (e.g. ["epayment", "Collaboration"]
        -getAllPlugins: returns a list of module objects corresponding to all plugins of all types.
        -getOptionsByType: returns a dictionary with the options of a given plugin type (for example, the Collaboration global options)
        -getDescriptionByType: returns a string with the description of a given plugin type (for example, the Collaboration plugin type description)
    """
    
    pluginList = {}
    pluginTypeVisible = {}
    pluginTypeOptions = {}
    pluginTypeActions = {}
    pluginTypeActionModules = {}
    pluginTypeDescriptions = {}
    path = None
    oldPath = None
    
    _pluginsLoaded = False

    @classmethod
    def changePath(cls):
        cls.path = sys.modules[__name__].__path__[0]
        
        if os.path.isabs(cls.path):
            cls.path = absToRelative(cls.path,basePath)
        else:
            cls.path = cls.path[len(basePath):]
            
        cls.oldPath = os.getcwd()

        
        if os.path.split(MaKaC.__path__[0])[0]:
            os.chdir(os.path.normpath(os.path.split(MaKaC.__path__[0])[0]))
            
    @classmethod
    def restorePath(cls):
        os.chdir(cls.oldPath)

    @classmethod
    def loadPlugins(cls):
        """ Explores the subfolder structure of the MaKaC/plugins folder and loads the plugins into memory.
            The modules are stored into the class attribute "pluginList"
            The dictionaries with the plugin options, if existant, are stored into the class attribute "pluginTypeOptions"
            The plugin descriptions, if existant, are stored into the class attribute "pluginTypeDescriptions"
        """
        if cls._pluginsLoaded:
            return
        
        cls.changePath()
        
        for type in os.listdir(cls.path):
            cls.findPluginsByType(type)
            
        cls._pluginsLoaded = True
        for plugin in cls.getAllPlugins():
            plugin.initModule(plugin)
        
        cls.restorePath()
    
    @classmethod
    def findPluginsByType(cls, type):
        
        if os.path.isdir(os.path.join(cls.path, type)):

            typePath = os.path.join(cls.path, type)

            for name in os.listdir(typePath):

                modPath = "MaKaC.plugins.%s"%type
                modName, ext = os.path.splitext(name)
                                
                if modName == "__init__":
                    if importName(modPath, "ignore" ):
                        if type in cls.pluginList:
                            del cls.pluginList[type]
                        return
                    
                    cls.pluginTypeVisible[type] = not (importName(modPath, "visible" ) is False)

                    optionsModule = importName(modPath, "options")
                    if optionsModule:
                        cls.pluginTypeOptions[type] = optionsModule.globalOptions
                    else:
                        cls.pluginTypeOptions[type] = None
                        
                    actionsModule = importName(modPath, "actions")
                    if actionsModule:
                        cls.pluginTypeActions[type] = actionsModule.pluginTypeActions
                    else:
                        cls.pluginTypeActions[type] = None
                    cls.pluginTypeActionModules[type] = actionsModule
                    
                    cls.pluginTypeDescriptions[type] = importName(modPath, "pluginTypeDescription" )
                    
                elif os.path.isdir(os.path.join(cls.path, type, modName)):
                    #try:
                    module = importName(modPath, modName)
                    if module and type == module.pluginType:
                        if not type in cls.pluginList.keys():
                            cls.pluginList[type] = {}
                        cls.pluginList[type][module.pluginName] = module
                        module.topModule = module
                        subMods = module.getModules(module, absToRelative(os.path.split(module.__file__)[0],basePath))
                        for subModKey in subMods.keys():
                            module.__dict__[subModKey] = subMods[subModKey]
                    #except:
                    #    pass
                    
    
    @classmethod
    def reloadPlugins(cls):
        """ Forces to reload the plugins if they are already in memory
        """
        cls.pluginList = {}
        cls._pluginsLoaded = False
        cls.loadPlugins()
    
    @classmethod
    def reloadPluginsByType(cls, type):
        """ Forces to reload plugins if they are already in memory, but only those of a given type (e.g. "epayment", "Collaboration").
        """
        cls.loadPlugins()
        if not type in cls.pluginList.keys():
            raise PluginError("Tried to reload plugins of type " + str(type) + " but that type doesn't exist")
        cls.pluginList[type] = {}
        cls._pluginsLoaded = False #TODO: have different flags for different types of plugins... but if memory isn't consistently shared between requests, it's not possible...
        cls.changePath()
        cls.findPluginsByType(type)
        cls._pluginsLoaded = True
        for plugin in cls.pluginList[type].values():
            plugin.initModule(plugin)
        cls.restorePath()
    
    @classmethod
    def getPluginsByType(cls, type):
        """ Given a type (e.g. "Collaboration"), and a name (e.g. "EVO") a module object corresponding to that plugin is returned
        """
        cls.loadPlugins()
        if type in cls.pluginList.keys():
            return cls.pluginList[type].values()
        else:
            raise PluginError("Tried to reload plugins of type " + str(type) + " but that type doesn't exist")
    
    @classmethod
    def getPluginTypeActionModuleByName(cls, name):
        cls.loadPlugins()
        return cls.pluginTypeActionModules[name]
    
    @classmethod
    def getPluginByTypeAndName(cls, type, name):
        """ Returns a list of strings with the plugin types (e.g. ["epayment", "Collaboration"]
        """
        cls.loadPlugins()
        if type in cls.pluginList.keys():
            modules = cls.pluginList[type]
            if name in modules:
                return modules[name]
            else:
                raise PluginError("Tried to get a plugin of the type " + type + " with name " + name + " but there is no plugin called " + name)
        else:
            raise PluginError("Tried to get a plugin of the type " + type + " but that type doesn't exist")
    
    @classmethod
    def getTypeList(cls):
        """ Returns a list of strings with the plugin types (e.g. ["epayment", "Collaboration"]
        """
        cls.loadPlugins()
        return cls.pluginList.keys()
    
    @classmethod
    def getAllPlugins(cls):
        """ Returns a list of module objects corresponding to all plugins of all types.
        """
        cls.loadPlugins()
        allPlugins = []
        for modules in cls.pluginList.values():
            allPlugins[:0] = modules.values()
        return allPlugins
    
    @classmethod
    def getOptionsByType(cls, type):
        """ Returns a dictionary with the options of a given plugin type (for example, the Collaboration global options)
        """
        cls.loadPlugins()
        return cls.pluginTypeOptions[type]
    
    @classmethod
    def getActionsByType(cls, type):
        """ Returns a dictionary with the actions of a given plugin type (for example, the Collaboration global actions)
        """
        cls.loadPlugins()
        return cls.pluginTypeActions[type]
    
    @classmethod
    def getDescriptionByType(cls, type):
        """ Returns a string with the description of a given plugin type (for example, the Collaboration plugin type description)
        """
        cls.loadPlugins()
        return cls.pluginTypeDescriptions[type]
    
    @classmethod
    def getIsVisibleType(cls, type):
        """ Returns if this plugin type should be shown in the Server Admin interface or not
        """
        cls.loadPlugins()
        return cls.pluginTypeVisible[type]

def reloadPlugins():
    Plugins.reloadPlugins()

def getPluginsByType(type):
    return Plugins.getPluginsByType(type)

def getTypeList():
    return Plugins.getTypeList()

def getAllPlugins():
    return Plugins.getAllPlugins()



def getModules(self, path):
    pluginList = {}
    for name in os.listdir(path):
        modName, ext = os.path.splitext(name)
        if not "__init__" in modName and (ext == ".py" or ext == ""):
            #try:
                if os.path.isdir(os.path.join(path, name)):
                    if not os.path.exists(os.path.join(path, name, "__init__.py")):
                        continue
                    isRep = True
                else:
                    isRep = False
                modPath = path.replace(os.path.sep, ".")
                mod = importName(modPath, modName)
                pluginList[modName] = mod
                if mod:
                    mod.topModule = self.topModule
                    if isRep:
                        #from MaKaC.common.logger import Logger
                        #Logger.get('plugins').debug("mod:%s"%mod)
                        subMods = mod.getModules(mod, absToRelative(os.path.split(mod.__file__)[0],basePath))
                        for subModKey in subMods.keys():
                            mod.__dict__[subModKey] = subMods[subModKey]
                            mod.modules[subModKey] = subMods[subModKey]
            #except:
            #    print "error importing module %s"%name
    return pluginList

def initModule(self):
    for module in self.modules:
        try:
            module.initModule(module)
        except:
            pass


def importPlugin(cls, name, obj):
    try:
        return getattr(__import__("MaKaC.plugins.%s.%s" % (cls, name), globals(), locals(), [obj]), obj)
    except Exception, e:
        raise e        
        return None
    
