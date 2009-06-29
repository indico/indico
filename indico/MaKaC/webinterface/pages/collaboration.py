# -*- coding: utf-8 -*-
##
## $Id: collaboration.py,v 1.20 2009/05/27 08:52:22 jose Exp $
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

from MaKaC.webinterface import wcomponents, urlHandlers
from MaKaC.webinterface.pages.conferences import WPConferenceModifBase
from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools
from MaKaC.common.timezoneUtils import nowutc
from MaKaC.common.utils import formatDateTime
from MaKaC.common.timezoneUtils import getAdjustedDate
from MaKaC.i18n import _
from MaKaC.common.PickleJar import DictPickler
from MaKaC.webinterface.rh.admins import RCAdmin
from MaKaC.webinterface.pages.main import WPMainBase
from MaKaC.common.indexes import IndexesHolder

################################################### Server Wide pages #########################################

class WPAdminCollaboration(WPMainBase):
    
    def __init__(self, rh, queryParams):
        WPMainBase.__init__(self, rh)
        self._queryParams = queryParams
        self._pluginsWithIndexing = CollaborationTools.pluginsWithIndexing() # list of names
        self._buildExtraJS()

    def getJSFiles(self):
        return WPMainBase.getJSFiles(self) + self._includeJSPackage('Collaboration')
    
    def _getHeader( self ):
        wc = wcomponents.WHeader( self._getAW() )
        return wc.getHTML( { "subArea": _("Video Services Administration"), \
                             "loginURL": self._escapeChars(str(self.getLoginURL())),\
                             "logoutURL": self._escapeChars(str(self.getLogoutURL())), \
                             "tabControl": self._getTabControl(), \
                             "loginAsURL": self.getLoginAsURL() } )

    def _getBody( self, params ):      
        return WAdminCollaboration(self._queryParams, self._pluginsWithIndexing).getHTML()
    
    def _getNavigationDrawer(self):
        return wcomponents.WSimpleNavigationDrawer("Video Services Admin", urlHandlers.UHAdminCollaboration.getURL )
    
    def _buildExtraJS(self):
        for pluginName in self._pluginsWithIndexing:
            extraJS = CollaborationTools.getExtraJS(pluginName, None)
            if extraJS:
                self.addExtraJS(extraJS)

class WAdminCollaboration(wcomponents.WTemplated):
    
    def __init__(self, queryParams, pluginsWithIndexing):
        wcomponents.WTemplated.__init__(self)
        self._queryParams = queryParams
        self._pluginsWithIndexing = pluginsWithIndexing # list of names
    
    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        
        #dictionary where the keys are names of false "indexes" for the user, and the values are IndexInformation objects
        vars["Indexes"] = CollaborationTools.getCollaborationPluginType().getOption("pluginsPerIndex").getValue()
        vars["InitialIndex"] = self._queryParams["indexName"]
        vars["InitialViewBy"] = self._queryParams["viewBy"]
        vars["InitialOrderBy"] = self._queryParams["orderBy"]
        vars["InitialOnlyPending"] = self._queryParams["onlyPending"]
        vars["InitialConferenceId"] = self._queryParams["conferenceId"]
        vars["InitialCategoryId"] = self._queryParams["categoryId"]
        vars["InitialMinKey"] = self._queryParams["minKey"]
        vars["InitialMaxKey"] = self._queryParams["maxKey"]
        vars["InitialResultsPerPage"] = self._queryParams["resultsPerPage"]
        vars["InitialPage"] = self._queryParams["page"]
        vars["BaseURL"] = urlHandlers.UHAdminCollaboration.getURL()
        
        if self._queryParams["queryOnLoad"]:
            ci = IndexesHolder().getById('collaboration')
            tz = self._rh._getUser().getTimezone()
            
            if self._queryParams["minKey"]:
                minKey = self._queryParams["minKey"]
            else:
                minKey = None
                
            if self._queryParams["maxKey"]:
                maxKey = self._queryParams["maxKey"]
            else:
                maxKey = None
            
            if self._queryParams["conferenceId"]:
                conferenceId = self._queryParams["conferenceId"]
            else:
                conferenceId = None
            
            if self._queryParams["categoryId"]:
                categoryId = self._queryParams["categoryId"]
            else:
                categoryId = None
            
            result, pages = ci.getBookings(self._queryParams["indexName"],
                                           self._queryParams["viewBy"],
                                           self._queryParams["orderBy"],
                                           minKey,
                                           maxKey,
                                           tz = tz,         
                                           onlyPending = self._queryParams["onlyPending"],
                                           conferenceId = conferenceId,
                                           categoryId = categoryId,
                                           pickle = True,
                                           dateFormat='%a %d %b %Y',
                                           page = self._queryParams["page"],
                                           resultsPerPage = self._queryParams["resultsPerPage"])
            
            vars["InitialNumberOfPages"] = pages
            vars["InitialBookings"] = result
        
        else:
            vars["InitialBookings"] = None
            vars["InitialNumberOfPages"] = 0
            
        JSCodes = {}
        for pluginName in self._pluginsWithIndexing:
            templateClass = CollaborationTools.getTemplateClass(pluginName, "WIndexing")
            JSCodes[pluginName] = templateClass(pluginName, None).getHTML()
     
        vars["JSCodes"] = JSCodes
     
        return vars


################################################### Event pages ###############################################

class WPConfModifCollaboration( WPConferenceModifBase ):
    
    def __init__(self, rh, conf):
        """ Constructor
            The rh is expected to have the attributes _tabs, _activeTab, _tabPlugins (like RHConfModifCSBookings)
        """
        WPConferenceModifBase.__init__(self, rh, conf)
        self._conf = conf
        self._tabNames = rh._tabs
        self._activeTab = rh._activeTab
        self._tabPlugins = rh._tabPlugins
                
        self._buildExtraCSS()
        self._buildExtraJS()

    def getJSFiles(self):
        return WPMainBase.getJSFiles(self) + self._includeJSPackage('Collaboration')
                        
    ######### private methods ###############
    def _buildExtraCSS(self):
        for plugin in self._tabPlugins:
            extraCSS = CollaborationTools.getExtraCSS(plugin.getName())
            if extraCSS:
                self.addExtraCSS(extraCSS)
                
    def _buildExtraJS(self):
        for plugin in self._tabPlugins:
            extraJS = CollaborationTools.getExtraJS(plugin.getName(), self._conf)
            if extraJS:
                self.addExtraJS(extraJS)

    ############## overloading methods #################
    def _createTabCtrl(self):
        self._tabCtrl = wcomponents.TabControl()
        #if user is not conference manager or server admin, we hide all other main tabs
        if not self._conf.canModify(self._rh.getAW()) or RCAdmin.hasRights(self._rh):
            for sect in self._sideMenu.getSections():
                for item in sect.getItems():
                    if item != self._videoServicesMenuItem:
                        item.setEnabled(False)
                    else:
                        item.setEnabled(True)
        
        self._subtabs = {}
        for subtabName in self._tabNames:
            self._subtabs[subtabName] = self._tabCtrl.newTab(
                                                subtabName, subtabName,
                                                urlHandlers.UHConfModifCollaboration.getURL(self._conf,
                                                                                            secure = CollaborationTools.isUsingHTTPS(),
                                                                                            tab=subtabName))
        
        self._setActiveTab()

    def _setActiveTab( self ):
        self._subtabs[self._activeTab].setActive()
        

    def _getPageContent( self, params ):
        if len(self._tabNames) > 0:
            self._createTabCtrl()
            wc = WConfModifCollaboration( self._conf, self._rh.getAW().getUser(), self._activeTab, self._tabPlugins)
            return wcomponents.WTabControl( self._tabCtrl, self._getAW() ).getHTML( wc.getHTML({}) )
        else:
            return _("No available plugins, or no active plugins")
        
    def _getTabContent(self, params):
        return "nothing"
        
    def _setActiveSideMenuItem(self):
        self._videoServicesMenuItem.setActive()
        

class WConfModifCollaboration( wcomponents.WTemplated ):
    
    def __init__( self, conference, user, activeTab, tabPlugins ):
        self._conf = conference
        self._user = user
        self._activeTab = activeTab
        self._tabPlugins = tabPlugins

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        
        plugins = self._tabPlugins
        singleBookingPlugins, multipleBookingPlugins = CollaborationTools.splitPluginsByAllowMultiple(plugins)
        CSBookingManager = self._conf.getCSBookingManager()
        
        bookingsS = {}
        for p in singleBookingPlugins:
            bookingList = CSBookingManager.getBookingList(filterByType = p.getName())
            if len(bookingList) > 0:
                bookingsS[p.getName()] = DictPickler.pickle(bookingList[0])
                
        bookingsM = DictPickler.pickle(CSBookingManager.getBookingList(
            sorted = True,
            notify = True,
            filterByType = [p.getName() for p in CollaborationTools.getPluginsByTab(self._activeTab)]))
        
        vars["Conference"] = self._conf
        vars["AllPlugins"] = plugins
        vars["SingleBookingPlugins"] = singleBookingPlugins
        vars["BookingsS"] = bookingsS
        vars["MultipleBookingPlugins"] = multipleBookingPlugins
        vars["BookingsM"] = bookingsM
        vars["Tab"] = self._activeTab
        vars["EventDate"] = formatDateTime(getAdjustedDate(nowutc(),self._conf))
        
        from MaKaC.webinterface.rh.collaboration import RCCollaborationAdmin, RCCollaborationPluginAdmin
        vars["UserIsAdmin"] = RCCollaborationAdmin.hasRights(user = self._user) or RCCollaborationPluginAdmin.hasRights(user = self._user, plugins = self._tabPlugins)
        
        singleBookingForms = {}
        multipleBookingForms = {}
        JSCodes = {}
        canBeNotified = {}
        
        for plugin in singleBookingPlugins:
            pluginName = plugin.getName()
            templateClass = CollaborationTools.getTemplateClass(pluginName, "WNewBookingForm")
            singleBookingForms[pluginName] = templateClass(self._conf, pluginName, self._user).getHTML()
            
        for plugin in multipleBookingPlugins:
            pluginName = plugin.getName()
            templateClass = CollaborationTools.getTemplateClass(pluginName, "WNewBookingForm")
            multipleBookingForms[pluginName] = templateClass(self._conf, pluginName, self._user).getHTML()
        
        for plugin in plugins:
            pluginName = plugin.getName()
            
            templateClass = CollaborationTools.getTemplateClass(pluginName, "WMain")
            JSCodes[pluginName] = templateClass(pluginName, self._conf).getHTML()
            
            bookingClass = CollaborationTools.getCSBookingClass(pluginName)
            canBeNotified[pluginName] = bookingClass._canBeNotifiedOfEventDateChanges
            
        vars["SingleBookingForms"] = singleBookingForms    
        vars["MultipleBookingForms"] = multipleBookingForms
        vars["JSCodes"] = JSCodes
        vars["CanBeNotified"] = canBeNotified
        
        return vars
