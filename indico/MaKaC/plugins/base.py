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

""" This purpose of this file is high-level handling of plugins.
    It has functions to store and retrieve information from the plugins that is stored in the database;
    for example, which plugins are active or not, options declared by plugins and their values, etc.
    The functions can be used through methods of the "PluginsHolder" class. See its description for more details.
"""

import types
import pkg_resources
import zope.interface
from BTrees.OOBTree import OOBTree
from persistent import Persistent
from flask import Blueprint

from MaKaC.common.Counter import Counter
from MaKaC.common.Locators import Locator
from MaKaC.errors import PluginError
from indico.core.db import DBMgr
from MaKaC.common.logger import Logger
from MaKaC.plugins.loader import PluginLoader, GlobalPluginOptions
from MaKaC.common.ObjectHolders import ObjectHolder
from MaKaC.plugins.util import processPluginMetadata

from indico.core.extpoint import Component, IListener, IContributor
from indico.util.importlib import import_module


def pluginId(mod):
    """
    Takes a module and spits out its plugin id
    """
    return mod.__name__.split('.')[-1]


def extension_point(event, *args, **kwargs):
    """
    "light" version of notification - no need for inheritance
    """
    _self = kwargs.pop('self', None)
    return PluginsHolder().getComponentsManager().notifyComponent(
        event, _self, *args, **kwargs)

class Observable(object):
    """
    DEPRECATED: just use "extension_point" above
    """
    def _notify(self, event, *params):
        return extension_point(event, *params, self=self)


class OldObservable:
    """
    Version for old style classes
    DEPRECATED: just use "extension_point" above
    """
    def _notify(self, event, *params):
        return extension_point(event, *params, self=self)


class ComponentsManager(Persistent):
    '''
    Manages all what is related to the components.

    eventComponentsDict keeps a record of the components that implement a certain event, and is used to register and unregister
    events when a plugin or a pluginType is either activated or desactivated.
    components is a list with all the components found in MaKaC/plugins, it is updated every time that the method loadPlugins is called.
    '''

    def __init__(self):
        self.__id = "componentsManager"
        self.__eventComponentsDict = {}
        self.__components = []

    def getId(self):
        return self.__id

    def addComponent(self, component):
        if component is not None and component not in self.__components:
            self.__components.append(component)
        self._notifyModification()

    def registerAllComponents(self):
        '''We register all the components, but if a plugintype is passed we should just register the changes
        in the part referred to that plugintype'''

        for component in self.__components:
            pluginTypeName, possiblePluginName = self.getAssociatedPlugin(component)

            #it's a plugin
            if possiblePluginName:
                try:
                    isActive = PluginsHolder().getPluginType(pluginTypeName).getPlugin(possiblePluginName).isActive()
                except KeyError, e:
                    Logger.get('components.register').warning(
                        "Skipped {0} ({1}:{2}) - Plugin doesn't exist or disabled?".format(
                            component, pluginTypeName, possiblePluginName))

                #if the pluginType that the plugin belongs to is not active we won't register the components for the plugin
                if not PluginsHolder().getPluginType(pluginTypeName).isActive():
                    isActive = False

            #it's a pluginType
            else:
                isActive = PluginsHolder().getPluginType(pluginTypeName).isActive()

            if isActive:
                self.registerComponent(component)

    def registerComponent(self, component):
        #Register it. We take the list of the interfaces implemented by the component
        implementedInterfaces = list(zope.interface.implementedBy(component))

        for interface in implementedInterfaces:

            #we take the list of the methods in the interface
            for met in list(interface):
                #if the method is implemented in the component, then we register it
                if met in dir(component):
                    self.registerNewEvent(met, component)

    def registerNewEvent(self, event, componentClass):
        changed = False
        if event not in self.__eventComponentsDict:
            self.__eventComponentsDict[event] = []
            changed = True

        isInList = False
        #we just need aux to make the comparation, since componentClass is just a type and component is an instance of an object
        aux = componentClass()
        for component in self.__eventComponentsDict[event]:
            if component.__class__ == aux.__class__:
                isInList = True
        #we don't want to have the 2 same components in the list, so we check it
        if not isInList:
            self.__eventComponentsDict[event].append(componentClass())
            #we order the list according to each method's priority
            self.__eventComponentsDict[event].sort(cmp=lambda x,y: cmp(x.getPriority(), y.getPriority()))
            changed = True
        if changed:
            self._notifyModification()

    def notifyComponent(self, event, obj, *params):
        results = []
        subscribers = self.getAllSubscribers(event)

        for subscriber in subscribers:
            try:
                f = getattr(subscriber,event)
                results.append(f(obj, *params))
            except Exception, e:
                Logger.get('ext.notification').exception("Exception while calling subscriber %s" % str(subscriber.__class__))
                raise

        return results

    def getAllSubscribers(self, method):
        if self.__eventComponentsDict.has_key(method):
            return self.__eventComponentsDict[method]
        else:
            return []

    def getAssociatedPlugin(self, component):
        ''' returns the plugin the component belongs to, according to the component path'''

        componentClassModuleName = component.__module__

        for epoint in pkg_resources.iter_entry_points('indico.ext'):
            if component.__module__.startswith(epoint.module_name):
                moduleId = epoint.name.split('.')
                return moduleId[0], moduleId[1]

        for epoint in pkg_resources.iter_entry_points('indico.ext_types'):
            if component.__module__.startswith(epoint.module_name):
                return epoint.name, None
        else:
            raise Exception('Component %s does not belong to any plugin? %s ' % (component, list(ep.module_name for ep in pkg_resources.iter_entry_points('indico.ext'))))

    def cleanPlugin(self, name):
        '''receives the name of the plugin, (EVO, CERNMCU...) and unregisters it'''
        #TODO: VERY inefficient!
        changed = False
        for event in self.__eventComponentsDict.keys():
            #check if the component is in the dictionary to erase it
            oldSize = len(self.__eventComponentsDict[event])
            self.__eventComponentsDict[event] = list( component for component in self.__eventComponentsDict[event] if not self.pluginContainsComponent(name, component))
            if oldSize != len(self.__eventComponentsDict[event]):
                changed = True
        if changed:
            self._notifyModification()

    def pluginContainsComponent(self, plugin, component):
        associatedPlugin = self.getAssociatedPlugin(component)
        if plugin == associatedPlugin[1]:
            return True
        return False

    def addPlugin(self, name):
        '''Someone activated a plugin (EVO, CERNMCU) and we need to register it again for the notifications'''

        for component in self.__components:
            if self.pluginContainsComponent(name, component):
                self.registerComponent(component)

    def cleanAll(self):
        self.__eventComponentsDict.clear()
        del self.__components[:]
        self._notifyModification()

    def _notifyModification(self):
        self._p_changed = 1


class AJAXMethodMap(Persistent):
    def __init__(self):
        self.__id = "ajaxMethodMap"
        self.__map = {}

    def _notifyModification(self):
        self._p_changed = 1

    def getAJAXMethodMap(self):
        if not self.hasKey('ajaxMethodMap'):
            self.add(AJAXMethodMap())
        return self.getById('ajaxMethodMap')

    def getId(self):
        return self.__id

    def addMethods2AJAXDict(self, dict):
        """ Every time a handlers.py file is checked in the pluginLoader, it fills this dictionary with AJAX methods from its methodMap
        """
        self.__map.update(dict)
        self._notifyModification()

    def getAJAXDict(self):
        return self.__map

    def cleanAJAXDict(self):
        """ Attributes in this class are persistent, so when we want to erase them we'll need to explicitely invoke this method
        """
        self.__map.clear()
        self._notifyModification()



class RHMap(Persistent):
    """ This class is the representation in the DB of the RHMap """
    def __init__(self):
        self.__id = "RHMap"
        self.__blueprints = set()

    def _notifyModification(self):
        self._p_changed = 1

    def getBlueprints(self):
        try:
            blueprints = self.__blueprints
        except AttributeError:
            blueprints = self.__blueprints = set()
        for module, name in blueprints:
            try:
                yield getattr(import_module(module), name)
            except ImportError:
                Logger.get('plugins.rhmap').exception('Could not import {0}'.format(module))

    def hasBlueprint(self, module, name):
        return (module.__name__, name) in self.__blueprints

    def getId(self):
        return self.__id

    def addBlueprint(self, module, attr):
        self.__blueprints.add((module.__name__, attr))
        self._notifyModification()

    def cleanRHDict(self):
        """ Attributes in this class are persistent, so when we want to erase them we'll need to explicitely invoke this method
        """
        try:
            if hasattr(self, '_RHMap__map'):
                delattr(self, '_RHMap__map')
            self.__blueprints.clear()
        except AttributeError:
            self.__blueprints = set()
        self._notifyModification()


class PluginsHolder (ObjectHolder):
    """ A PluginsHolder object is the "gateway" to all the methods for getting plugin meta-data stored in the DB.
    """

    idxName = "plugins"
    counterName = "PLUGINS"

    def __init__(self):
        """ Creates / Returns a PluginsHolder object,
            which is the "gateway" to all the methods for getting plugin meta-data.
        """
        ObjectHolder.__init__(self)
        if not self.hasKey("globalPluginOptions"):
            self.add(GlobalPluginOptions())
        if not self.hasKey('componentsManager'):
            self.add(ComponentsManager())
        if len(self._getIdx()) == 0: #no plugins
            self.loadAllPlugins()
        if not self.hasKey('ajaxMethodMap'):
            self.add(AJAXMethodMap())
        if not self.hasKey('RHMap'):
            self.add(RHMap())

    def getRHMap(self):
        if not self.hasKey('RHMap'):
            self.add(RHMap())
        return self.getById('RHMap')
        # Replace with the real dict obtained while exploring the directories
        #return {'algo': 'MaKaC.webinterface.rh.welcome.RHWelcome'}

    def getGlobalPluginOptions(self):
        """ Returns server-wide options relative to the whole plugin system.
        """
        return self.getById("globalPluginOptions")

    def getComponentsManager(self):
        if not self.hasKey('componentsManager'):
            self.add(ComponentsManager())
        return self.getById('componentsManager')

    def loadAllPlugins(self):
        """ Initially loads all plugins and stores their information
        """
        PluginLoader.loadPlugins()
        self.updateAllPluginInfo()

    def reloadAllPlugins(self, disable_if_broken=True):
        """ Reloads all plugins and updates their information
        """

        self.getComponentsManager().cleanAll()
        self.getById("ajaxMethodMap").cleanAJAXDict()
        self.getById("RHMap").cleanRHDict()
        PluginLoader.reloadPlugins()
        self.updateAllPluginInfo(disable_if_broken)
        self.getComponentsManager().registerAllComponents()

    def reloadPluginType(self, pluginTypeName):
        """ Reloads plugins of a given type and updates their information
            pluginTypeName: a string such as "Collaboration"
        """
        PluginLoader.reloadPluginType(pluginTypeName)
        if self.hasPluginType(pluginTypeName, mustBeActive=False):
            self.getPluginType(pluginTypeName).updateInfo()
        else:
            raise PluginError("Error while trying to reload plugins of the type: " + pluginTypeName + ". Plugins of the type " + pluginTypeName + "do not exist")

    def updateAllPluginInfo(self, disable_if_broken=True):
        """ Updates the info about plugins in the DB
            We must keep if plugins are active or not even between reloads
            and even if plugins are removed from the file system (they may
            be present again later)
        """
        for pt in self.getPluginTypes(includeNonPresent=True):
            pt.setPresent(False)

        ptypes = PluginLoader.getPluginTypeList()

        for ptypeId in ptypes:

            if self.hasPluginType(ptypeId, mustBePresent=False, mustBeActive=False):
                ptype = self.getPluginType(ptypeId)
                ptype.setPresent(True)
            else:
                ptype = PluginType(ptypeId)
                self.add(ptype)

            ptype.configureFromMetadata(processPluginMetadata(ptype.getModule()))
            missingDeps = ptype.getModule().__missing_deps__

            # if there are dependencies missing, set as not usable
            if missingDeps:
                ptype.setUsable(False, reason="Dependencies missing: {0}".format(', '.join(missingDeps)))
                if disable_if_broken and ptype.isActive():
                    ptype.setActive(False)
            else:
                ptype.setUsable(True)

            ptype.updateInfo(disable_if_broken)

    def clearPluginInfo(self):
        """ Removes all the plugin information from the DB
        """
        for item in self.getValuesToList():
            if isinstance(item, PluginType):
                self.remove(item)
        self._getTree("counters")[PluginsHolder.counterName] = Counter()

    def getPluginTypes(self, doSort=False, includeNonPresent=False, includeNonVisible=True):
        """ Returns a list of different PluginTypes (e.g. epayment, collaboration, roombooking)
            doSort: if True, the list of PluginTypes will be sorted alphabetically
            includeNonPresent: if True, non present PluginTypes will be included. A PluginType is present if it has a physical folder on
            disk, inside MaKaC/plugins
        """
        pluginTypes = [pt for pt in self.getList() if isinstance(pt, PluginType) and
                                                      (pt.isPresent() or includeNonPresent) and
                                                      (pt.isVisible() or includeNonVisible)]
        if doSort:
            pluginTypes.sort(key=lambda pt: pt.getId())
        return pluginTypes

    def hasPluginType(self, name, mustBePresent=True, mustBeActive=True):
        """
        Returns True if there is a PluginType with the given name.
        """
        if self.hasKey(name):
            pluginType = self.getById(name)
            return (not mustBePresent or pluginType.isPresent()) and (not mustBeActive or pluginType.isActive())
        else:
            return False

    def getPluginType(self, ptypeid):
        """ Returns the PluginType object for the given name
        """
        return self.getById(ptypeid)



class RHMapMemory:
    """ Stores the RHMap for every python process in memory
    If there's no Map attribute, we fetch it from the database,
    otherwise just return it.
    """

    ## Stores the unique Singleton instance-
    _iInstance = None

    ## Class used with this Python singleton design pattern
    #  @todo Add all variables, and methods needed for the Singleton class below
    class Singleton:
        def __init__(self):
            if not hasattr(self, '_blueprints'):
                with DBMgr.getInstance().global_connection():
                    self._blueprints = set(PluginsHolder().getRHMap().getBlueprints())

    ## The constructor
    #  @param self The object pointer.
    def __init__( self ):
        # Check whether we already have an instance
        if RHMapMemory._iInstance is None:
            # Create and remember instance
            RHMapMemory._iInstance = RHMapMemory.Singleton()

        # Store instance reference as the only member in the handle
        self._EventHandler_instance = RHMapMemory._iInstance

    ## Delegate access to implementation.
    #  @param self The object pointer.
    #  @param attr Attribute wanted.
    #  @return Attribute
    def __getattr__(self, aAttr):
        return getattr(self._iInstance, aAttr)


    ## Delegate access to implementation.
    #  @param self The object pointer.
    #  @param attr Attribute wanted.
    #  @param value Vaule to be set.
    #  @return Result of operation.
    def __setattr__(self, aAttr, aValue):
        return setattr(self._iInstance, aAttr, aValue)


class PluginBase(Persistent):
    """ Base class for the Plugin and PluginType classes.
        Both of these classes can store "options" and "actions" so the common logic is handled by this class.
        It inherits from Persistent so that Plugin and PluginType don't have double inheritance.
    """

    def __init__(self):
        """ Constructor.
            The options are stored in a dictionary where the key is the option name and the value is a PluginOption object
            (see the PluginOption class)
        """
        self.__options = {}
        self.__actions = {}
        self.__HTTPAPIHooks = []

        self.__usable = False

    ############## actions related ###############
    @classmethod
    def checkOptionAttributes(cls, name, attributes):
        """ Utility method that takes a dictionary with option attributes.
            It verifies some attributes and sets default values for others if they don't exist.
        """
        if attributes.has_key("description"):
            description = attributes["description"]
        else:
            raise PluginError('Option ' + str(name) + ' does not have a "description" attribute')

        if attributes.has_key("type"):
            optionType = attributes["type"]
        else:
            raise PluginError('Option ' + str(name) + ' does not have a "type" attribute')

        return {"description": description,
                "note": attributes.get("note", None),
                "type": optionType,
                "subType": attributes.get("subType", None),
                "defaultValue": attributes.get("defaultValue", None),
                "editable": attributes.get("editable", True),
                "visible": attributes.get("visible", True),
                "mustReload": attributes.get("mustReload", False),
                "options": attributes.get("options", [])
                }


    def updateAllOptions(self, retrievedPluginOptions):
        """ Updated the attributes of the options of this Plugin / PluginType object.
            retrievedPluginOptions can be a dictionary with the options or None if none were found
        """
        #we mark all the options as non present
        for pto in self.getOptions().values():
            pto.setPresent(False)

        #we get the list of options of this type
        if retrievedPluginOptions is not None:
            for index, (name, attributes) in enumerate(retrievedPluginOptions):
                if self.hasOption(name):
                    self.updateOption(name, PluginBase.checkOptionAttributes(name, attributes), index)
                else:
                    self.addOption(name, PluginBase.checkOptionAttributes(name, attributes), index)

    def getOptions(self, includeNonPresent=False, includeOnlyEditable=False,
                   includeOnlyNonEditable=False, includeOnlyVisible=False,
                   filterByType=None):
        """ Returns all the options of this PluginType / Plugin, in dictionary form.
            -if includeNonPresent == True, all the options are returned, otherwise, only the present ones
            (present = declared in the relevant __init__.py file).
            -if includeOnlyEditable = True, only the "editable" options are returned
            -if includeOnlyNonEditable = True, only the non "editable" options are returned
            -if includeOnlyVisible = True, only the "visible" options are returned
            WARNING: this method returns a copy of the options, so use it only for reading, not for adding options.
        """
        return dict([(k, v) for k, v in self.__options.items()
                     if (v.isPresent() or includeNonPresent) and
                          ((v.isEditable() and not includeOnlyNonEditable) or (not v.isEditable() and not includeOnlyEditable)) and
                          (v.isVisible() or not includeOnlyVisible) and
                          (not filterByType or v.getType() == filterByType)
                    ])

    def getOptionList(self, doSort=False, includeNonPresent=False,
                      includeOnlyEditable=False, includeOnlyNonEditable=False, includeOnlyVisible=False,
                      filterByType=None):
        """ Returns all the options of this PluginType / Plugin, in list form.
            -if doSort = True, the options will be sorted by their order attribute.
            -if includeNonPresent == True, all the options are returned, otherwise, only the present ones
            (present = declared in the relevant __init__.py file).
            -if includeOnlyEditable = True, only the "editable" options are returned
            -if includeOnlyNonEditable = True, only the non "editable" options are returned
            -if includeOnlyVisible = True, only the "visible" options are returned
            WARNING: this method returns a copy of the options, so use it only for reading, not for writing values/ adding options.
        """

        options = self.getOptions(includeNonPresent, includeOnlyEditable, includeOnlyNonEditable, includeOnlyVisible, filterByType).values()
        if doSort:
            options.sort(key=lambda option: option.getOrder())
        return options

    def getOption(self, optionName):
        """ Returns a PluginOption object given its name.
        """
        return self.__options[optionName]

    def addOption(self, name, attributes, order):
        """ Adds a new option to the set of options of this Plugin / PluginType object.
            name: a string
            attributes: a dictionary
            order: an integer with the order of the options
        """
        self.__options[name] = PluginOption(name, attributes["description"], attributes["type"],
                                            attributes["defaultValue"], attributes["editable"], attributes["visible"],
                                            attributes["mustReload"], True, order, attributes["subType"], attributes["note"],
                                            attributes["options"])
        self._notifyModification()

    def updateOption(self, name, attributes, order):
        """ Updates an existing option with new attribute values
            name: a string
            attributes: a dictionary
            order: an integer with the order of the options
        """
        option = self.getOption(name)
        option.setPresent(True)
        option.setDescription(attributes["description"])
        option.setNote(attributes["note"])
        option.setType(attributes["type"])
        option.setSubType(attributes["subType"])
        option.setEditable(attributes["editable"])
        option.setVisible(attributes["visible"])
        option.setMustReload(attributes["mustReload"])
        if option.isMustReload():
            option.setValue(attributes["defaultValue"])
        option.setOrder(order)
        option.setOptions(attributes["options"])

    def hasOption(self, name):
        """ Returns if this Plugin / PluginType object has an option given this name
            name: a string with the name of the options
        """
        return name in self.__options

    def hasAnyOptions(self):
        """ Returns if this Plugin / PluginType object has any options at all
        """
        return len(self.getOptions()) > 0

    def clearAssociatedActions(self):
        """ Every option can have many associated actions. (an action is a button that will do something that changes the value of the option)
            This utility method clears the actions for all options.
        """
        for option in self.__options.values():
            option.clearActions()

    ############## end of options related ###############


    ############## actions related ###############
    @classmethod
    def checkActionAttributes(cls, name, attributes):
        """ Utility method that takes a dictionary with actions attributes.
            It verifies some attributes and sets default values for others if they don't exist.
        """
        if (not attributes.has_key("visible") or (attributes.has_key("visible") and attributes["visible"])) and not attributes.has_key("buttonText"):
            raise PluginError('Action ' + str(name) + ' does not have a "buttonText" attribute, but it is visible')

        return {"buttonText": attributes.get("buttonText", None),
                "associatedOption": attributes.get("associatedOption", None),
                "visible": attributes.get("visible", True),
                "executeOnLoad": attributes.get("executeOnLoad", False),
                "triggeredBy": attributes.get("triggeredBy", [])
                }

    def updateAllActions(self, retrievedPluginActions):
        """ Updates information about the actions.
            -retrievedPluginActions: a dictionary where
            keys are strings (the action name) and values are 2-tuples of strings (buttonText, associatedOptionName)
        """
        self.__actions = {}
        self.clearAssociatedActions()
        #we get the list of actions of this type
        if retrievedPluginActions is not None:
            for index, (name, attributes) in enumerate(retrievedPluginActions):
                checkedAttributes = PluginBase.checkActionAttributes(name, attributes)
                associatedOptionName = checkedAttributes["associatedOption"]

                if associatedOptionName is None:
                    associatedOption = None
                else:
                    if self.hasOption(associatedOptionName):
                        associatedOption = self.getOption(associatedOptionName)
                    else:
                        raise PluginError("action " + name + " of plugin " + self.getName() + " tried to associate with option " + associatedOptionName + " but this option doesn't exist")

                newAction = self.addAction(name, checkedAttributes, index)

                if associatedOption is not None:
                    associatedOption.addAssociatedAction(self.getAction(name))

                if newAction.isExecuteOnLoad():
                    newAction.call()

    def getActions(self, includeOnlyNonAssociated=False, includeOnlyTriggeredBy=False, includeOnlyVisible=True):
        """ Returns all the actions of this Plugin, as a dictionary where
            keys are strings (the action name) and values are PluginAction objects.
        """
        return dict([(k, v) for k, v in self.__actions.items()
            if (not includeOnlyNonAssociated or not v.hasAssociatedOption()) and
                (not includeOnlyTriggeredBy or v.hasTriggeredBy()) and
                (not includeOnlyVisible or v.isVisible())
        ])

    def getActionList(self, doSort=False, includeOnlyNonAssociated=False, includeOnlyTriggeredBy=False, includeOnlyVisible=True):

        actions = self.getActions(includeOnlyNonAssociated, includeOnlyTriggeredBy, includeOnlyVisible).values()
        if doSort:
            actions.sort(key=lambda action: action.getOrder())
        return actions

    def getAction(self, actionName):
        return self.__actions[actionName]

    def addAction(self, name, attributes, index):
        newAction = PluginAction(name, self, attributes["buttonText"],
                                 attributes["associatedOption"], attributes["visible"],
                                 attributes["executeOnLoad"], attributes["triggeredBy"], index)
        self.__actions[name] = newAction
        self._notifyModification()
        return newAction

    def hasAction(self, name):
        return self.__actions.has_key(name)

    def hasAnyActions(self, includeOnlyNonAssociated=False):
        return len(self.getActionList(includeOnlyNonAssociated=includeOnlyNonAssociated)) > 0
    ############## end of actions related ###############

    ############## HTTPAPIHook related ###############
    def updateAllHTTPAPIHooks(self, retrievedPluginHTTPAPIHooks):
        self.__HTTPAPIHooks = []
        if retrievedPluginHTTPAPIHooks is not None:
            self.__HTTPAPIHooks = retrievedPluginHTTPAPIHooks
        self._notifyModification()

    def getHTTPAPIHookList(self):
        try:
            return self.__HTTPAPIHooks
        except:
            self.__HTTPAPIHooks = []
            return self.__HTTPAPIHooks

    ############## end of HTTPAPIHooks related ###############

    def _notifyModification(self):
        self._p_changed = 1

    def setUsable(self, value, reason = ''):
        self.__notUsableReason = None if value else reason

    def getNotUsableReason(self):
        return self.__notUsableReason

    def isUsable(self):
        return self.__notUsableReason == None

    def getStorage(self):
        if not hasattr(self, "_storage") or self._storage is None:
            self._storage = OOBTree()
        return self._storage


class PluginType (PluginBase):
    """ This class represents a plugin type ("COllaboration", "epayment", etc.).
        It will store information about the plugin type in the db.
    """

    def __init__(self, ptypeId, description=None):
        """ Constructor
            -name: a string with the type name. e.g. "Collaboration"
            -description: a human readable description for this plugin type.
            This class will store a list of plugins in the form of a dictionary. The keys will be the plugin names
            and the values will be Plugin objects.
            Also, it will have associated options, since it inherits from PluginBase.
        """
        PluginBase.__init__(self)
        self.__id = ptypeId
        self.__name = ptypeId
        self.__description = description
        self.__present = True
        self.__plugins = {}
        self._visible = True
        self._active = False

    def configureFromMetadata(self, metadata):
        self.__name = metadata['name']

    def _updatePluginInfo(self, pid, pluginModule, metadata, disable_if_broken=True):

        if self.hasPlugin(pid):
            p = self.getPlugin(pid)
            p.setDescription(metadata['description'])
            p.setPresent(True)

        #if it didn't exist, we create it
        else:
            p = Plugin(pid,
                       pluginModule.__name__,
                       self,
                       metadata['description'])

            self.addPlugin(p)

        p.configureFromMetadata(processPluginMetadata(p.getModule()))

        missingDeps = p.getModule().__missing_deps__

        if missingDeps:
            p.setUsable(False, reason="Dependencies missing: {0}".format(missingDeps))
            if disable_if_broken:
                p.setActive(False)
        else:
            p.setUsable(True)

        if hasattr(pluginModule, "options") and \
               hasattr(pluginModule.options, "globalOptions"):
            p.updateAllOptions(pluginModule.options.globalOptions)

        if hasattr(pluginModule, "actions") and \
               hasattr(pluginModule.actions, "pluginActions"):
            p.updateAllActions(pluginModule.actions.pluginActions)

        if hasattr(pluginModule, "http_api") and \
               hasattr(pluginModule.options, "globalHTTPAPIHooks"):
            p.updateAllHTTPAPIHooks(pluginModule.http_api.globalHTTPAPIHooks)

        self._updateComponentInfo(p, pluginModule)
        self._updateHandlerInfo(p, pluginModule)
        self._updateRHMapInfo(p, pluginModule)

    def updateInfo(self, disable_if_broken=True):
        """
        Will update the information in the DB about this plugin type.
        """

        # until we detect them, the plugins of this given Type are marked as non-present
        for plugin in self.getPluginList(includeNonPresent=True,
                                         includeNonActive=True):
            plugin.setPresent(False)

        # we get the list of modules (plugins) of this type
        pluginModules = PluginLoader.getPluginsByType(self.getId())

        # we loop through the plugins
        for pluginModule in pluginModules:
            metadata = processPluginMetadata(pluginModule)

            # skip ignored plugins
            if metadata['ignore']:
                continue
            else:
                self._updatePluginInfo(pluginModule.__plugin_id__, pluginModule, metadata, disable_if_broken=disable_if_broken)

        ptypeModule = self.getModule()
        ptypeMetadata = processPluginMetadata(ptypeModule)

        # basic information
        self.__name = ptypeMetadata['name']
        self.__description = ptypeMetadata['description']
        self.__visible = ptypeMetadata['visible']

        # components, handlers, options, actions and HTTPAPIHooks
        self._updateComponentInfo(self, ptypeModule)
        self._updateRHMapInfo(self, ptypeModule)
        self._updateHandlerInfo(self, ptypeModule)
        self.updateAllOptions(self._retrievePluginTypeOptions())
        self.updateAllActions(self._retrievePluginTypeActions())
        self.updateAllHTTPAPIHooks(self._retrievePluginTypeHTTPAPIHooks())


    def _getAllSubmodules(self, module):
        accum = []

        for obj in module.__dict__.itervalues():

            # check if it's a module and it is inside the parent module
            # ignore test modules
            if type(obj) == types.ModuleType and \
                   obj.__name__.startswith(module.__name__) and \
                   obj.__name__.split('.')[-1] != 'tests':
                    accum += [obj]
                    accum += self._getAllSubmodules(obj)

        return accum

    def _updateComponentInfo(self, plugin, module):
        Logger.get('plugins.holder').info("Updating component info for '%s'" % \
                                          plugin.getFullId())
        for smodule in self._getAllSubmodules(module):
            for obj in smodule.__dict__.values():
                if type(obj) == type and Component in obj.mro() and \
                   (IListener.implementedBy(obj) or IContributor.implementedBy(obj)):
                    Logger.get('plugins.holder.component').debug(
                        "Registering component %s" % obj)
                    PluginsHolder().getComponentsManager().addComponent(obj)

    def _updateRHMapInfo(self, plugin, module):
        rh_map = PluginsHolder().getRHMap()
        for smodule in self._getAllSubmodules(module):
            Logger.get('plugins.holder.rhmap').debug('Analyzing %s' % smodule)
            for name, obj in smodule.__dict__.iteritems():
                if not isinstance(obj, Blueprint):
                    continue
                if rh_map.hasBlueprint(smodule, name):
                    # If a submodule defines a blueprint it is also seen when this method runs for the parent
                    # plugin type. However, since submodules are always checked first we can simply skip
                    # already-registered blueprints!
                    continue
                # For a plugin type the blueprint is named 'foo', for a subplugin 'foo-bar'
                if isinstance(plugin, PluginType):
                    expected_name = plugin.getId().lower()
                else:
                    expected_name = '%s-%s' % (plugin.getOwner().getId().lower(), plugin.getId().lower())
                if obj.name not in (expected_name, 'compat_' + expected_name):
                    raise PluginError('Blueprint in plugin %s must be named %s, not %s' % (
                                      plugin.getName(), expected_name, obj.name))
                rh_map.addBlueprint(smodule, name)

    def _updateHandlerInfo(self, plugin, module):

        for attribute in module.__dict__.values():
            if isinstance(attribute, types.ModuleType):
                if hasattr(attribute, 'methodMap') and type(attribute.methodMap) == dict:
                    PluginsHolder().getById('ajaxMethodMap').addMethods2AJAXDict(
                       attribute.methodMap)
                    Logger.get('plugins.holder').warning("Found methodMap in module: %s"% \
                                                            module.__name__)

    def _retrievePluginTypeOptions(self):

        hasOptionsModule = hasattr(self.getModule(), "options")
        hasGlobalOptionsVariable = hasOptionsModule and hasattr(self.getModule().options, "globalOptions")
        if hasOptionsModule and hasGlobalOptionsVariable:
            return self.getModule().options.globalOptions
        else:
            return None

    def _retrievePluginTypeActions(self):
        hasActionsModule = hasattr(self.getModule(), "actions")
        hasPluginTypeActions = hasActionsModule and hasattr(self.getModule().actions, "pluginTypeActions")
        if hasActionsModule and hasPluginTypeActions:
            return self.getModule().actions.pluginTypeActions
        else:
            return None

    def _retrievePluginTypeHTTPAPIHooks(self):

        hasHTTPAPIModule = hasattr(self.getModule(), "http_api")
        hasGlobalHTTPAPIHooksVariable = hasHTTPAPIModule and hasattr(self.getModule().http_api, "globalHTTPAPIHooks")
        if hasHTTPAPIModule and hasGlobalHTTPAPIHooksVariable:
            return self.getModule().http_api.globalHTTPAPIHooks
        else:
            return None

    def getId(self):
        return self.__id

    def getFullId(self):
        return self.__id

    def setId(self, id):
        self.__id = id

    def getName(self):
        return self.__name if hasattr(self, '_PluginType__name') and self.__name is not None else self.__id

    def getDescription(self):
        return self.__description

    def hasDescription(self):
        return (self.__description is not None) and len(self.__description) > 0

    def isPresent(self):
        return self.__present

    def setPresent(self, present):
        self.__present = present

    def getPlugin(self, id):
        return self.__plugins[id]

    def hasPlugin(self, id):
        return id in self.__plugins

    def addPlugin(self, plugin):
        self.__plugins[plugin.getId()] = plugin
        self._notifyModification()

    def getModule(self):
        return PluginLoader.getPluginType(self.getId())

    def hasPlugins(self):
        """ Returns if this plugin type has any plugins at all.
        """
        return len(self.__plugins) > 0

    def getPlugins(self, includeNonPresent=False, includeTestPlugins=False, includeNonActive=False, filterFunction=lambda plugin: True):
        """ Returns a dictionary with the plugins of this PluginType.
            They keys of the dictionary will be strings, with the name of each plugin (e.g. "EVO"). The values will be Plugin objects.
            -includeNonPresent: if True, non present plugins (i.e., plugins in the DB but no longer in the file system) will be returned
            -includeNonActive: if True, non active plugins will be returned
            -filterFunction: a function that will be passed a plugin as argument and returns if the plugin should be returned or not.
        """
        return dict([(k, v) for k, v in self.__plugins.items()
                     if (v.isPresent() or includeNonPresent) and (not v.isTestPlugin() or includeTestPlugins) and (v.isActive() or includeNonActive) and filterFunction(v)])

    def getPluginList(self, doSort=False, includeNonPresent=False, includeTestPlugins=False, includeNonActive=False, filterFunction=lambda plugin: True):
        """ Returns a list with the plugins of this PluginType, as a list of Plugin objects.
            -doSort: if True, the list will be sorted alphabetically by plugin name.
            -includeNonPresent: if True, non present plugins (i.e., plugins in the DB but no longer in the file system) will be returned
            -includeNonActive: if True, non active plugins will be returned
            -filterFunction: a function that will be passed a plugin as argument and returns if the plugin should be returned or not.
        """
        plugins = self.getPlugins(includeNonPresent, includeTestPlugins, includeNonActive, filterFunction)
        if doSort:
            keys = plugins.keys()
            keys.sort()
            return [plugins[k] for k in keys]
        else:
            return plugins.values()

    def getLocator(self):
        l = Locator()
        l["pluginType"] = self.getId()
        return l

    def isVisible(self):
        if not hasattr(self, "_visible"):
            self._visible = True
        return self._visible

    def isActive(self):
        if not hasattr(self, "_active"):
            self._active = False
        return self._active

    def setActive(self, value):
        self._active = value
        PluginsHolder().reloadAllPlugins()

    def toggleActive(self):
        if not self.isActive():
            self._active = True
            #register the components related to the plugin
            PluginsHolder().reloadAllPlugins()
            #PluginsHolder().getComponentsManager().addPluginType(self.getName(), True)
        else:
            self._active = False
            #unregister the components related to the plugin
            PluginsHolder().reloadAllPlugins()
            #PluginsHolder().getComponentsManager().cleanPluginType(self.getName(), True)


class Plugin(PluginBase):
    """ This class represents a plugin ("EVO", "paypal", etc.).
        It will store information about the plugin in the db.
    """


    def __init__(self, pid, moduleName, owner, description=None, active=False):
        """ Constructor
            -moduleName: the module name corresponding to this plugin. e.g. "MaKaC.plugins.Collaboration.EVO"
            -owner : the PluginType of this Plugin
            -description: a human readable description of the purpose of this plugin
            -active: a boolean that stores if this plugin is active or not. If not active, it shouldn't exist for the rest of Indico.

            A plugin object will have associated options that can be set up from the Server Admin interface.
            Also it will have "actions". For example, the EVO plugin has a "reload communities" action which will
            contact the EVO server and change the value of the "community list" option. The list of communities
            needs to be used later when interacting with the Indico user. Information about the actions will be stored in
            the DB in a similar way to options.
        """
        PluginBase.__init__(self)
        self.__name = pid
        self.__id = pid.replace(' ','')
        self.__owner = owner
        self.__present = True
        self.__moduleName = moduleName
        self.__description = description
        self.__active = active
        self._testPlugin = False
        self._globalData = self.initializeGlobalData()
        self._storage = OOBTree() # storage.....

    def configureFromMetadata(self, metadata):
        self.__name = metadata['name']
        self._testPlugin = metadata['testPlugin']

    def getId(self):
        return self.__id

    def setId(self, newId):
        self.__id = newId

    def getFullId(self):
        return "%s.%s" % (self.getOwner().getId(), self.__id)

    def getName(self):
        return self.__name

    def getOwner(self):
        return self.__owner

    def isPresent(self):
        return self.__present

    def setPresent(self, present):
        self.__present = present

    def getModuleName(self):
        return self.__moduleName

    def getModule(self):
        return PluginLoader.getPluginByTypeAndId(self.getType(), self.getId())

    def getType(self):
        return self.getOwner().getId()

    def hasDescription(self):
        return (self.__description is not None) and len(self.__description) > 0

    def getDescription(self):
        return self.__description

    def setDescription(self, description):
        self.__description = description

    def isActive(self):
        return self.__active

    def setActive(self, value):
        self.__active = value
        if value:
            # register the components related to the plugin
            PluginsHolder().getComponentsManager().addPlugin(self.getName())
        else:
            # unregister the components related to the plugin
            PluginsHolder().getComponentsManager().cleanPlugin(self.getName())

    def toggleActive(self):
        self.setActive(not self.isActive())

    def isTestPlugin(self):
        if not hasattr(self, "_testPlugin"): #TODO: remove when safe
            self._testPlugin = False
        return self._testPlugin

    def initializeGlobalData(self):
        module = self.getModule()
        if hasattr(module, 'common') and hasattr(module.common, 'GlobalData'):
            return module.common.GlobalData()
        else:
            return None

    def getGlobalData(self):
        if not hasattr(self, "_globalData") or self._globalData is None:
            self._globalData = self.initializeGlobalData()
        return self._globalData

    def setGlobalData(self, globalData):
        self._globalData = globalData

    def getLocator(self):
        l = self.__owner.getLocator()
        l["pluginId"] = self.getId()
        return l

    def __str__(self):
        return str(self.__name)


class PluginOption(Persistent):
    """ Represents an option of a PluginType or a Plugin object.
        name: the id / name of the option
        description: a human-readable description
        type: the type of the value of the option: str, int, list, dict ...
        value: the initial value of the option, if given
        editable: says if this option's value will be editable in the plugin admin interface
        visible: says if this option's value will be visible in the plugin admin interface
        mustReload: says if this option's value should be set to the default value when the options are reloaded.
                    this is the only way to change values of a non-editable option without accessing the DB directly
        present: this will be false if the option is still in the DB, but not anymore in the __init__.py file of the plugin
        order: an integer so that the options can be displayed in a given order (ascending order)
        options: a list of options when the type is select
    """
    _extraTypes = {
        'users': list,
        'usersGroups': list,
        'rooms': list,
        'password': str,
        'ckEditor': str,
        'textarea': str,
        'list_multiline': list,
        'links': list,
        'currency': list,
        'paymentmethods': list,
        'select': str,

    }

    def __init__(self, name, description, valueType, value=None, editable=True, visible=True, mustReload=False, present=True, order=0, subType=None, note=None, options=[]):
        self.__name = name
        self.__description = description
        self.__note = note
        self.__type = valueType
        self.__subType = subType
        self.__present = present
        self.__editable = editable
        self.__visible = visible
        self.__mustReload = mustReload
        if value is None:
            self.__value = None
        else:
            self.setValue(value)
        self.__associatedActions = []
        self.__order = order
        self.__options = options

    def getName(self):
        return self.__name

    def getDescription(self):
        return self.__description

    def getNote(self):
        return self.__note

    def getType(self):
        return self.__type

    def getSubType(self):
        return self.__subType

    def getValue(self):
        return self.__value

    def getRooms(self):
        from MaKaC.rb_location import RoomGUID
        if self.getType() != 'rooms':
            raise PluginError('getRooms() called on non-rooms option')
        rooms = []
        for guid in self.getValue():
            room = RoomGUID.parse(guid).getRoom()
            if room:
                rooms.append(room)
        return rooms

    def setName(self, value):
        self.__name = value

    def setDescription(self, description):
        self.__description = description

    def setNote(self, note):
        self.__note = note

    def isPresent(self):
        return self.__present

    def setPresent(self, present):
        self.__present = present

    def isEditable(self):
        return self.__editable

    def setEditable(self, editable):
        self.__editable = editable

    def isVisible(self):
        return self.__visible

    def setVisible(self, visible):
        self.__visible = visible

    def isMustReload(self):
        try:
            return self.__mustReload
        except AttributeError:
            self.__mustReload = False
            return self.__mustReload

    def setMustReload(self, mustReload):
        self.__mustReload = mustReload

    def setType(self, valueType):
        self.__type = valueType

    def setSubType(self, subType):
        self.__subType = subType

    def setValue(self, value):
        if isinstance(self.__type, type):
            self.__value = self.__type(value)
        elif self.__type in PluginOption._extraTypes:
            self.__value = PluginOption._extraTypes[self.__type](value)
        else:
            raise PluginError("""Tried to set value of option %s with type %s but this type is not recognized""" % (self.__name, self.__type))

    def addAssociatedAction(self, action):
        self.__associatedActions.append(action)

    def hasActions(self):
        return len(self.__associatedActions) > 0

    def getActions(self):
        return self.__associatedActions

    def clearActions(self):
        self.__associatedActions = []

    def getOrder(self):
        if not hasattr(self, "_PluginOption__order"): #TODO: remove when safe
            self.__order = 0
        return self.__order

    def setOrder(self, order):
        self.__order = order

    def getOptions(self):
        if not hasattr(self, "_PluginOption__options"): #TODO: remove when safe
            self.__options = []
        return self.__options

    def setOptions(self, options):
        self.__options = options

    def _notifyModification(self):
        self._p_changed = 1


class PluginAction(Persistent):
    """ Represents an "action" of a Plugin object.
        An "action" is a button that can be pressed to trigger a function call
        Its name is the function inside the actions.py file of each plugin that will be called.
    """

    def __init__(self, name, owner, buttonText, associatedOption=None, visible=True, executeOnLoad=False, triggeredBy=[], order=0):
        """ Constructor for the PluginAction class
            name: the name of the action. It's also the name of the function inside the actions.py file of each plugin that will be called.
            owner: the Plugin or PluginType object that owns this action
            buttonText: a string that will be used in the button to trigger this action
            associatedOption: the name of a PluginOption of this same plugin. It implies that this action will change the value of that option.
                              thus, its button should appear next to the value of that option.
            visible: if True, a button to execute the action will appear
            executeOnLoad: if True, the action will be executing when loading / reloading the plugins
            triggeredBy: a list of PluginOption names of the same Plugin or child Plugins (if it's a PluginType)
                         if not an empty list, this action will be executed when one of those options is saved.
            order: an integer so that the actions can be displayed in a given order (ascending order)
        """
        self.__name = name
        self.__owner = owner
        self.__buttonText = buttonText
        self.__associatedOption = associatedOption
        self.__visible = visible
        self.__executeOnLoad = executeOnLoad
        self.__triggeredBy = triggeredBy
        self.__order = order

    def getName(self):
        return self.__name

    def getOwner(self):
        return self.__owner

    def getButtonText(self):
        return self.__buttonText

    def hasAssociatedOption(self):
        return self.__associatedOption is not None

    def getAssociatedOption(self):
        return self.__associatedOption

    def setName(self, name):
        self.__name = name

    def setButtonText(self, buttonText):
        self.__buttonText = buttonText

    def setAssociatedOption(self, associatedOption):
        self.__associatedOption = associatedOption

    def isVisible(self):
        return self.__visible

    def setVisible(self, visible):
        self.__visible = visible

    def isExecuteOnLoad(self):
        return self.__executeOnLoad

    def setExecuteOnLoad(self, executeOnLoad):
        self.__executeOnLoad = executeOnLoad

    def hasTriggeredBy(self):
        return len(self.__triggeredBy) > 0

    def getTriggeredBy(self):
        return self.__triggeredBy

    def setTriggeredBy(self, triggeredBy):
        self.__triggeredBy = triggeredBy

    def getOrder(self):
        if not hasattr(self, "_PluginAction__order"): #TODO: remove when safe
            self.__order = 0
        return self.__order

    def setOrder(self, order):
        self.__order = order

    def call(self):
        actionClassName = self.__name[0].upper() + self.__name[1:] + "Action"
        clazz = getattr(self.__owner.getModule().actions, actionClassName)
        return clazz(self).call()


class ActionBase(object):
    """ Base class for plugins to implement their actions.
        The "call" method will be called when a button representing an action is pushed.
    """

    def __init__(self, pluginAction):
        self._pluginAction = pluginAction
        if isinstance(pluginAction.getOwner(), Plugin):
            self._plugin = pluginAction.getOwner()
            self._pluginType = self._plugin.getOwner()
        else:
            self._pluginType = pluginAction.getOwner()

    def call(self):
        """ To be implemented by inheriting classes
        """
        raise PluginError("Action of class " + str(self.__class__.__name__) + " has not implemented the method call()")
