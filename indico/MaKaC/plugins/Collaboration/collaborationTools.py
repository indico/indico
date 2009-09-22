# -*- coding: utf-8 -*-
##
## $Id: collaborationTools.py,v 1.4 2009/04/28 14:10:01 dmartinc Exp $
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

from MaKaC.plugins.base import PluginsHolder

class CollaborationTools(object):
    """ Class with utility classmethods for the Collaboration plugins core and plugins
    """
    
    #This commented code tried to gain some performance by caching the collaboration
    # PluginType object, but sometimes there would be problems by
    # different requests sharing memory and trying to access the database
    # after a connection was closed. This happened under Apache in Windows Vista with ZODB 3.8
#    _cpt = None
#    _plugins = {}
    
    @classmethod
    def getCollaborationPluginType(cls):
        #This commented code tried to gain some performance by caching the collaboration
        # PluginType object, but sometimes there would be problems by
        # different requests sharing memory and trying to access the database
        # after a connection was closed. This happened under Apache in Windows Vista with ZODB 3.8
#        if not cls._cpt:
#            cls._cpt = PluginsHolder().getPluginType("Collaboration")
#        return cls._cpt
        return PluginsHolder().getPluginType("Collaboration")
    
    @classmethod
    def getPlugin(cls, pluginName):
        #This commented code tried to gain some performance by caching the collaboration
        # PluginType object, but sometimes there would be problems by
        # different requests sharing memory and trying to access the database
        # after a connection was closed. This happened under Apache in Windows Vista with ZODB 3.8

#        if not pluginName in cls._plugins:
#            cls._plugins[pluginName] = cls.getCollaborationPluginType().getPlugin(pluginName)
#        return cls._plugins[pluginName]
        return cls.getCollaborationPluginType().getPlugin(pluginName)
        
    @classmethod
    def getOptionValue(cls, pluginName, optionName):
        """ Returns the value of an option of a plugin (plugins/Collaboration/XXXXX/options.py)
            pluginName: a string with the name of the plugin
            optionName: a string with the name of the option
        """
        ph = PluginsHolder()
        return ph.getPluginType("Collaboration").getPlugin(pluginName).getOption(optionName).getValue()
    
    @classmethod
    def getCollaborationOptionValue(cls, optionName):
        """ Returns the value of an option of the Collaboration plugin type (plugins/Collaboration/options.py)
        """
        return cls.getCollaborationPluginType().getOption(optionName).getValue()
    
    @classmethod
    def isUsingHTTPS(cls):
        """ Utility function that returns if we should use HTTPS in collaboration pages or not.
        """
        return cls.getCollaborationPluginType().hasOption('useHTTPS') and \
               cls.getCollaborationPluginType().getOption('useHTTPS').getValue()
    
    @classmethod
    def getModule(cls, pluginName):
        """ Utility function that returns a module object given a plugin name.
            pluginName: a string such as "EVO", "DummyPlugin", etc.
        """
        return cls.getCollaborationPluginType().getPlugin(pluginName).getModule()
            
    @classmethod
    def getTemplateClass(cls, pluginName, templateName):
        """ Utility function that returns a template class object given a plugin name and the class name.
            Example: templateClass = CollaborationTools.getTemplateClass("EVO", "WNewBookingForm") will return the WNewBookingForm class in the EVO plugin.
        """
        return cls.getModule(pluginName).pages.__dict__.get(templateName, None)
    
    @classmethod
    def getServiceClass(cls, pluginName, serviceName):
        """ Utility function that returns a service class object given a plugin name and the class name.
            Example: serviceClass = CollaborationTools.getTemplateClass("WebcastRequest", "WebcastAbleTalksService") will return the WebcastAbleTalksService class in the WebcastRequest plugin.
        """
        return cls.getModule(pluginName).services.__dict__.get(serviceName + "Service", None)
    
    @classmethod
    def getExtraCSS(cls, pluginName):
        """ Utility function that returns a string with the extra CSS declared by a plugin.
            Example: templateClass = CollaborationTools.getExtraCSS("EVO").
        """
        templateClass = cls.getTemplateClass(pluginName, "WStyle")
        if templateClass:
            return templateClass(pluginName).getHTML()
        else:
            return None
        
    @classmethod
    def getExtraJS(cls, pluginName, conference):
        """ Utility function that returns a string with the extra JS declared by a plugin.
            Example: templateClass = CollaborationTools.getExtraJS("CERNMCU").
        """
        templateClass = cls.getTemplateClass(pluginName, "WExtra")
        if templateClass:
            return templateClass(pluginName, conference).getHTML()
        else:
            return None
    
    @classmethod
    def getCSBookingClass(cls, pluginName):
        """ Utility function that returns a CSBooking class given a plugin name.
            Example: templateClass = getCSBookingClass("EVO") will return the CSBooking class of the EVO plugin.
        """
        return cls.getModule(pluginName).collaboration.CSBooking
    
    @classmethod
    def getTabs(cls, conference, user = None):
        """ Returns a list of tab names corresponding to the active plugins for an event.
            If a user is specified, only tabs with plugins where the user is an plugin admin,
            or where the user is a plugin manager for this event, are returned.
        """
        csbm = conference.getCSBookingManager()
        tabNamesSet = set()
        allowedForThisEvent = csbm.getAllowedPlugins()
        showableForThisEvent = [plugin for plugin in allowedForThisEvent if plugin.isActive()] 
        for plugin in showableForThisEvent:
            if not user or user in plugin.getOption('admins').getValue() or csbm.isPluginManager(plugin.getName(), user):
                tabNamesSet.add(cls.getPluginTab(plugin))
            
        tabNames = list(tabNamesSet)
        return tabNames
    
    @classmethod
    def getPluginTab(cls, pluginObject):
        """ Utility function that returns the tab a Collaboration plugin belongs to.
            If the option was not defined, "Collaboration" is the default.
        """
        if pluginObject.hasOption("tab"):
            return pluginObject.getOption("tab").getValue()
        else:
            return "Collaboration"
        
    @classmethod
    def getPluginsByTab(cls, tabName, conference = None, user = None):
        """ Utility function that returns a list of plugin objects.
            These Plugin objects will be of the "Collaboration" type, and only those who have declared a subtab equal
            to the "tabName" argument will be returned.
            If tabName is None, [] is returned.
            The conference object is used to filter plugins that are not allowed in a conference,
            because of the conference type or the equipment of the conference room
            If a user is specified, only tabs with plugins where the user is an plugin admin,
            or where the user is a plugin manager for this event, are returned.
        """
        if tabName:
            
            csbm = conference.getCSBookingManager()
            
            if conference:
                allowedPlugins = csbm.getAllowedPlugins()
            else:
                allowedPlugins = None
            
            #we get the plugins of this tab
            return cls.getCollaborationPluginType().getPluginList(
                sorted = True,
                filter = lambda plugin: cls.getPluginTab(plugin) == tabName and
                                        (allowedPlugins is None or plugin in allowedPlugins) and
                                        (user is None or user in plugin.getOption('admins').getValue() or csbm.isPluginManager(plugin.getName(), user))
            )
        else:
            return []
    
            
    @classmethod
    def splitPluginsByAllowMultiple(cls, pluginList):
        """ Utility function that returns a tuple of 2 lists of Plugin objects.
            The first list are the plugins who only allow 1 booking of their type.
            The second list are the plugins who allow multiple bookings of their type.
        """
        
        #we split them into 2 lists
        singleBookingPlugins = [p for p in pluginList if not cls.getCSBookingClass(p.getName())._allowMultiple]
        multipleBookingPlugins = [p for p in pluginList if cls.getCSBookingClass(p.getName())._allowMultiple]

        return singleBookingPlugins, multipleBookingPlugins

    @classmethod
    def getPluginAllowedOn(cls, pluginObject):
        """ Utility function that returns a list of event types that this plugin is allowed on.
            If the option was not defined, an empty list is returned
        """
        if pluginObject.hasOption("allowedOn"):
            return pluginObject.getOption("allowedOn").getValue()
        else:
            return []
        
    @classmethod
    def pluginsWithEventDisplay(cls):
        """ Utility function that returns a list of strings with the names of the
            collaboration plugins that want to display something in event display pages
        """
        l = []
        for pluginName in cls.getCollaborationPluginType().getPlugins():
            if cls.getCSBookingClass(pluginName)._hasEventDisplay:
                l.append(pluginName)
        return l
    
    @classmethod
    def pluginsWithIndexing(cls):
        """ Utility function that returns a list of strings with the names
            of the collaboration plugins that want to be indexed
        """
        l = []
        for pluginName in cls.getCollaborationPluginType().getPlugins():
            if cls.getCSBookingClass(pluginName)._shouldBeIndexed:
                l.append(pluginName)
        return l
    
    @classmethod
    def getXMLGenerator(cls, pluginName):
        return cls.getModule(pluginName).pages.XMLGenerator