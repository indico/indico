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
""" This purpose of this file is high-level handling of plugins.
    It has functions to store and retrieve information from the plugins that is stored in the database;
    for example, which plugins are active or not, options declared by plugins and their values, etc.
    The functions can be used through methods of the "PluginsHolder" class. See its description for more details.
"""

from MaKaC.plugins.pluginLoader import PluginLoader
from MaKaC.common.Counter import Counter
from MaKaC.common.ObjectHolders import ObjectHolder
from persistent import Persistent
from MaKaC.common.Locators import Locator
from MaKaC.errors import PluginError


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
        if len(self._getIdx()) == 0: #no plugins
            self.loadAllPlugins()

    def getGlobalPluginOptions(self):
        """ Returns server-wide options relative to the whole plugin system.
        """
        return self.getById("globalPluginOptions")

    def loadAllPlugins(self):
        """ Initially loads all plugins and stores their information
        """
        PluginLoader.loadPlugins()
        self.updateAllPluginInfo()

    def reloadAllPlugins(self):
        """ Reloads all plugins and updates their information
        """
        PluginLoader.reloadPlugins()
        self.updateAllPluginInfo()

    def reloadPluginType(self, pluginTypeName):
        """ Reloads plugins of a given type and updates their information
            pluginTypeName: a string such as "Collaboration"
        """
        PluginLoader.reloadPluginType(pluginTypeName)
        if self.hasPluginType(pluginTypeName, mustBeActive=False):
            self.getPluginType(pluginTypeName).updateInfo()
        else:
            raise PluginError("Error while trying to reload plugins of the type: " + pluginTypeName + ". Plugins of the type " + pluginTypeName + "do not exist")

    def updateAllPluginInfo(self):
        """ Updates the info about plugins in the DB
            We must keep if plugins are active or not even between reloads
            and even if plugins are removed from the file system (they may
            be present again later)
        """
        for pt in self.getPluginTypes(includeNonPresent=True):
            pt.setPresent(False)

        types = PluginLoader.getPluginTypeList()

        for pluginTypeName in types:

            if self.hasPluginType(pluginTypeName, mustBePresent=False, mustBeActive=False):
                pluginType = self.getPluginType(pluginTypeName)
                pluginType.setPresent(True)
            else:
                pluginType = PluginType(pluginTypeName)
                self.add(pluginType)

            pluginType.updateInfo()

    def clearPluginInfo(self):
        """ Removes all the plugin information from the DB
        """
        for item in self.getValuesToList():
            if item.getId() != "globalPluginOptions":
                self.remove(item)
        self._getTree("counters")[PluginsHolder.counterName] = Counter()

    def getPluginTypes(self, doSort=False, includeNonPresent=False, includeNonVisible=True):
        """ Returns a list of different PluginTypes (e.g. epayment, collaboration, roombooking)
            doSort: if True, the list of PluginTypes will be sorted alphabetically
            includeNonPresent: if True, non present PluginTypes will be included. A PluginType is present if it has a physical folder on
            disk, inside MaKaC/plugins
        """
        pluginTypes = [pt for pt in self.getList() if pt.getId() != "globalPluginOptions" and
                                                      (pt.isPresent() or includeNonPresent) and
                                                      (pt.isVisible() or includeNonVisible)]
        if doSort:
            pluginTypes.sort(key=lambda pt: pt.getId())
        return pluginTypes

    def hasPluginType(self, name, mustBePresent=True, mustBeActive=True):
        """ Returns True if there is a PluginType with the given name.
        """
        if self.hasKey(name):
            pluginType = self.getById(name)
            return (not mustBePresent or pluginType.isPresent()) and (not mustBeActive or pluginType.isActive())
        else:
            return False

    def getPluginType(self, name):
        """ Returns the PluginType object for the given name
        """
        return self.getById(name)




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
                "type": optionType,
                "defaultValue": attributes.get("defaultValue", None),
                "editable": attributes.get("editable", True),
                "visible": attributes.get("visible", True),
                "mustReload": attributes.get("mustReload", False)
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
                                            attributes["mustReload"], True, order)
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
        option.setType(attributes["type"])
        option.setEditable(attributes["editable"])
        option.setVisible(attributes["visible"])
        option.setMustReload(attributes["mustReload"])
        if option.isMustReload():
            option.setValue(attributes["defaultValue"])
        option.setOrder(order)

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

    def _notifyModification(self):
        self._p_changed = 1



class PluginType (PluginBase):
    """ This class represents a plugin type ("COllaboration", "epayment", etc.).
        It will store information about the plugin type in the db.
    """

    def __init__(self, name, description=None):
        """ Constructor
            -name: a string with the type name. e.g. "Collaboration"
            -description: a human readable description for this plugin type.
            This class will store a list of plugins in the form of a dictionary. The keys will be the plugin names
            and the values will be Plugin objects.
            Also, it will have associated options, since it inherits from PluginBase.
        """
        PluginBase.__init__(self)
        self.__id = name
        self.__description = description
        self.__present = True
        self.__plugins = {}
        self._visible = True
        self._active = False


    def updateInfo(self):
        """ This method will update the information in the DB about this plugin type.
            It will call the lower-level layer ( MaKaC/plugins/__init__.py ) to retrieve
            information about its plugins, its options, etc.
        """

        #until we detect them, the plugins of this given Type are marked as present
        for plugin in self.getPluginList(includeNonPresent=True, includeNonActive=True):
            plugin.setPresent(False)

        #we get the list of modules (plugins) of this type
        pluginModules = PluginLoader.getPluginsByType(self.getName())

        #we loop through the plugins
        for pluginModule in pluginModules:
            if hasattr(pluginModule, "ignore") and pluginModule.ignore:
                continue

            #if it already existed, we mark it as present
            pluginName = pluginModule.pluginName
            if self.hasPlugin(pluginName):
                p = self.getPlugin(pluginName)
                if hasattr(pluginModule, "pluginDescription"):
                    p.setDescription(pluginModule.pluginDescription)
                p.setPresent(True)

            #if it didn't exist, we create it
            else:
                if hasattr(pluginModule, "pluginDescription"):
                    description = pluginModule.pluginDescription
                else:
                    description = None

                p = Plugin(pluginName, pluginModule.__name__, self, description)
                self.addPlugin(p)

            if hasattr(pluginModule, "testPlugin") and pluginModule.testPlugin:
                p.setTestPlugin(pluginModule.testPlugin)

            if hasattr(pluginModule, "options") and hasattr(pluginModule.options, "globalOptions"):
                p.updateAllOptions(pluginModule.options.globalOptions)

            if hasattr(pluginModule, "actions") and hasattr(pluginModule.actions, "pluginActions"):
                p.updateAllActions(pluginModule.actions.pluginActions)


        self.updateAllOptions(self._retrievePluginTypeOptions())

        self.updateAllActions(self._retrievePluginTypeActions())

        self.__description = self._retrievePluginTypeDescription()

        self._visible = self._retrieveIsVisible()

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

    def _retrievePluginTypeDescription(self):
        hasDescription = hasattr(self.getModule(), "pluginTypeDescription")
        if hasDescription:
            return self.getModule().pluginTypeDescription
        else:
            return None

    def _retrieveIsVisible(self):
        hasIsVisible = hasattr(self.getModule(), "visible")
        if hasIsVisible:
            return not self.getModule().visible is False
        else:
            return True

    def getId(self):
        return self.__id

    def setId(self, id):
        self.__id = id

    def getName(self):
        return self.__id

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
        return PluginLoader.getPluginType(self.getName())

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
        l["pluginType"] = self.getName()
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

    def toggleActive(self):
        self._active = not self.isActive()

class Plugin(PluginBase):
    """ This class represents a plugin ("EVO", "paypal", etc.).
        It will store information about the plugin in the db.
    """


    def __init__(self, name, moduleName, owner, description=None, active=False):
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
        self.__name = name
        self.__owner = owner
        self.__present = True
        self.__moduleName = moduleName
        self.__description = description
        self.__active = active
        self._testPlugin = False
        self._globalData = self.initializeGlobalData()

    def getId(self):
        return self.__name

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
        return PluginLoader.getPluginByTypeAndName(self.getType(), self.getName())

    def getType(self):
        return self.getOwner().getName()

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

    def toggleActive(self):
        self.__active = not self.__active

    def setTestPlugin(self, testPlugin):
        self._testPlugin = testPlugin

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


class GlobalPluginOptions(Persistent):
    """ A class that stores global information about all plugins.
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
    """
    _extraTypes = {
        'users': list,
        'rooms': list
    }

    def __init__(self, name, description, valueType, value=None, editable=True, visible=True, mustReload=False, present=True, order=0):
        self.__name = name
        self.__description = description
        self.__type = valueType
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

    def getName(self):
        return self.__name

    def getDescription(self):
        return self.__description

    def getType(self):
        return self.__type

    def getValue(self):
        return self.__value

    def setName(self, value):
        self.__name = value

    def setDescription(self, description):
        self.__description = description

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
