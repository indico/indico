# -*- coding: utf-8 -*-
##
## $Id: admins.py,v 1.27 2009/05/07 13:36:33 pferreir Exp $
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

import string
import MaKaC.webinterface.pages.admins as admins
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.user as user
import MaKaC.common.info as info
from MaKaC.errors import AdminError, MaKaCError, PluginError
from MaKaC.common import HelperMaKaCInfo
from MaKaC.webinterface.rh.base import RHProtected
from MaKaC.common.cache import CategoryCache, EventCache
from MaKaC.plugins.base import PluginsHolder
from MaKaC.i18n import _

class RCAdmin(object):
    @staticmethod
    def hasRights(request = None, user = None):
        """ Returns True if the user is a Server Admin
            request: an RH or Service object
            user: an Avatar object
            If user is not None, the request object will be used to check the user's privileges.
            Otherwise the user will be retrieved from the request object 
        """
        if user is None:
            if request is None:
                return False
            else:
                user = request._getUser()
        
        minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
        serverAdmins = minfo.getAdminList()
        return serverAdmins.isAdmin(user)

class RHAdminBase( RHProtected ):

    def _checkParams( self, params ):
        RHProtected._checkParams( self, params )
        self._minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
    
    def _checkProtection( self ):
        RHProtected._checkProtection( self )
        self._al = self._minfo.getAdminList()
        if not self._al.isAdmin( self._getUser() ):
            if self._getUser() != None and len( self._al.getList() )==0:
                return
            raise AdminError("area")

class RHAdminArea( RHAdminBase ):
    _uh = urlHandlers.UHAdminArea
    
    def _process( self ):
        p = admins.WPAdmins( self )
        return p.display()

class RHUpdateNews( RHAdminBase ):
    _uh = urlHandlers.UHUpdateNews

    def _checkParams( self, params ):
        RHAdminBase._checkParams( self, params )
        self._params = params
    
    def _process( self ):
        if self._params.has_key("news") and self._params.has_key("save"):
            minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
            minfo.setNews(self._params["news"])
        p = admins.WPUpdateNews( self )
        return p.display()

class RHConfigUpcoming( RHAdminBase ):
    _uh = urlHandlers.UHConfigUpcomingEvents
    
    def _checkParams( self, params ):
        RHAdminBase._checkParams( self, params )
        self._params = params
        
    def _process( self ):
        p = admins.WPConfigUpcomingEvents( self )
        return p.display()

    
class RHAdminSelectUsers( RHAdminBase ):
    _uh = urlHandlers.UHAdminsSelectUsers
    
    def _process( self ):
        p = admins.WPAdminSelectUsers( self )
        return p.display( **self._getRequestParams() )


class RHAdminAddUsers( RHAdminBase ):
    _uh = urlHandlers.UHAdminsAddUsers
    
    def _process( self ):
        params = self._getRequestParams()
        if "selectedPrincipals" in params:
            al = self._minfo.getAdminList()
            ph = user.PrincipalHolder()
            for id in self._normaliseListParam( params["selectedPrincipals"] ):
                if ph.getById( id ) != None:
                    al.grant( ph.getById( id ) )
        self._redirect( urlHandlers.UHAdminArea.getURL() )


class RHAdminRemoveUsers( RHAdminBase ):
    _uh = urlHandlers.UHAdminsRemoveUsers
    
    def _process( self ):
        params = self._getRequestParams()
        if "selectedPrincipals" in params:
            al = self._minfo.getAdminList()
            ph = user.PrincipalHolder()
            for id in self._normaliseListParam( params["selectedPrincipals"] ):
                if ph.getById( id ) != None:
                    al.revoke( ph.getById( id ) )
        self._redirect( urlHandlers.UHAdminArea.getURL() )        


class RHGeneralInfoModification( RHAdminBase ):
    _uh = urlHandlers.UHGeneralInfoModification
    
    def _process( self ):
        p = admins.WPGenInfoModification( self )
        return p.display()

class RHAdminLocalDefinitions( RHAdminBase ):
    _uh = urlHandlers.UHAdminLocalDefinitions

    def _process( self ):
        p = admins.WPAdminLocalDefinitions( self )
        return p.display() 

class RHAdminSaveTemplateSet( RHAdminBase ):
    _uh = urlHandlers.UHAdminSaveTemplateSet

    def _checkParams( self, params ):
        self._params = params
        self._defSet = params.get("templateSet",None)
        if self._defSet == "None":
            self._defSet = None
        RHAdminBase._checkParams( self, params )

    def _process( self ):
        self._minfo.setDefaultTemplateSet(self._defSet)
        self._redirect( urlHandlers.UHAdminLocalDefinitions.getURL() )


class RHAdminSwitchCacheActive( RHAdminBase ):
    _uh = urlHandlers.UHAdminSwitchCacheActive

    def _process( self ):
        CategoryCache().cleanUpAllFiles()
        EventCache().cleanUpAllFiles()
        self._minfo.setCacheActive( not self._minfo.isCacheActive() )
        self._redirect( urlHandlers.UHAdminArea.getURL() )     

class RHAdminSwitchNewsActive( RHAdminBase ):
    _uh = urlHandlers.UHAdminSwitchNewsActive

    def _process( self ):
        self._minfo.setNewsActive( not self._minfo.isNewsActive() )
        self._redirect( urlHandlers.UHAdminArea.getURL() )     

class RHAdminSwitchDebugActive( RHAdminBase ):
    _uh = urlHandlers.UHAdminSwitchDebugActive

    def _process( self ):
        self._minfo.setDebugActive( not self._minfo.isDebugActive() )
        self._redirect( urlHandlers.UHAdminArea.getURL() )
        
class RHAdminSwitchHighlightActive( RHAdminBase ):
    _uh = urlHandlers.UHAdminSwitchHighlightActive

    def _process( self ):
        self._minfo.setHighlightActive( not self._minfo.isHighlightActive() )
        self._redirect( urlHandlers.UHAdminArea.getURL() )     

class RHGeneralInfoPerformModification( RHAdminBase ):
    _uh = urlHandlers.UHGeneralInfoPerformModification
    
    def _process( self ):
        params = self._getRequestParams()

        if params['action'] != 'cancel':
            self._minfo.setTitle( params["title"] )
            self._minfo.setOrganisation( params["organisation"] )
            self._minfo.setSupportEmail( params["supportEmail"] )
            self._minfo.setPublicSupportEmail( params["publicSupportEmail"] )
            self._minfo.setNoReplyEmail( params["noReplyEmail"] )
            self._minfo.setCity( params["city"] )
            self._minfo.setCountry( params["country"] )
            self._minfo.setTimezone( params["timezone"] )
            self._minfo.setLang( params["lang"] )
        self._redirect( urlHandlers.UHAdminArea.getURL() )        

class RHUserMerge(RHAdminBase):
    
    def _checkParams( self, params ):
        ah = user.AvatarHolder()
        self._params = params
        RHAdminBase._checkParams( self, params )
        
        
        self.prin = None
        if self._params.get("prinId", None) and self._params["prinId"] != "":
            self.prin = ah.getById(self._params["prinId"])
        
        self.toMerge = None
        if self._params.get("toMergeId", None) and self._params["toMergeId"] != "":
            self.toMerge = ah.getById(self._params["toMergeId"])
        
        self.selectPrin = False
        if self._params.get("selectPrin", None):
            self.selectPrin = True
        
        self.selectToMerge = False
        if self._params.get("selectToMerge", None):
            self.selectToMerge = True
        
        self.merge = False
        if self._params.get("merge", None):
            self.merge = True
        self.cancel = False
        self.setPrin = False
        self.newPrin = None
        if self._params.get("setPrin", None):
            if self._params.get("selectedPrincipals", None):
                self.setPrin = True
                self.newPrin = ah.getById(self._params.get("selectedPrincipals", ""))
            else:
                self.cancel = True
        
        self.setToMerge = False
        self.newToMerge = None
        if self._params.get("setToMerge", None):
            if self._params.get("selectedPrincipals", None):
                self.setToMerge = True
                self.newToMerge = ah.getById(self._params.get("selectedPrincipals", ""))
            else:
                self.cancel = True
    
    
    def _process( self ):
        
        if self.setPrin:
            self.prin = self.newPrin
        
        elif self.setToMerge:
            self.toMerge = self.newToMerge
        
        elif self.cancel:
            pass
        
        elif self.selectPrin:
            p = admins.WPUserMergeSelectPrin( self, self.prin, self.toMerge )
            return p.display(**self._getRequestParams())
        
        elif self.selectToMerge:
            p = admins.WPUserMergeSelectToMerge( self, self.prin, self.toMerge )
            return p.display(**self._getRequestParams())
        
        elif self.merge:
            if self.prin and self.toMerge:
                ah = user.AvatarHolder()
                ah.mergeAvatar(self.prin, self.toMerge)
                url = urlHandlers.UHUserMerge.getURL()
                url.addParam("prinId", self.prin.getId())
                self._redirect(url)
                return _("[Done]")
        
        p = admins.WPUserMerge( self, self.prin, self.toMerge )
        return p.display()

class RHStyles(RHAdminBase):
    _uh = urlHandlers.UHAdminsStyles
    
    def _checkParams( self, params ):
        RHAdminBase._checkParams( self, params )
        self._new = params.get("new", "")
        self._name = params.get("name", "")
        self._xslfile = params.get("xslfile", "")
        self._eventType = params.get("event_type", "")
        self._action = params.get("action", "")
        self._newstyle = params.get("newstyle","")
        
    def _process( self ):
        styleMgr = info.HelperMaKaCInfo.getMaKaCInfoInstance().getStyleManager()
        if self._new != "":
            if self._xslfile not in styleMgr.getStylesheets().keys() and self._name != "":
                styles = styleMgr.getStylesheets()
                styles[self._xslfile] = self._name
                styleMgr.setStylesheets(styles)
        if self._action == "default" and self._eventType != "" and self._xslfile != "":
            styleMgr.setDefaultStyle(self._xslfile, self._eventType)
        if self._action == "delete" and self._eventType != "" and self._xslfile != "":
            styleMgr.removeStyle(self._xslfile, self._eventType)
        if self._action == "add" and self._eventType != "" and self._newstyle != "":
            styleMgr.addStyleToEventType(self._newstyle, self._eventType)
        p = admins.WPAdminsStyles( self )
        return p.display()

class RHDeleteStyle(RHAdminBase):
    _uh = urlHandlers.UHAdminsDeleteStyle

    def _checkParams( self, params ):
        RHAdminBase._checkParams( self, params )
        self._xslfile = params.get("xslfile", "")
        self._eventType = params.get("event_type","")
    
    def _process( self ):
        styleMgr = info.HelperMaKaCInfo.getMaKaCInfoInstance().getStyleManager()
        if self._xslfile != "":
            styleMgr.removeStyle(self._xslfile, self._eventType)
        self._redirect(urlHandlers.UHAdminsStyles.getURL())
    
class RHAddStyle(RHAdminBase):
    _uh = urlHandlers.UHAdminsAddStyle
    
    def _process( self ):
        p = admins.WPAdminsAddStyle( self )
        return p.display()
    
#Plugin admin start
class RHAdminPluginsBase(RHAdminBase):
    """ Base RH class for all plugin management requests.
        It will store 2 string parameters: pluginType and pluginId.
        Example: pluginType = "COllaboration" & pluginId = "EVO"
    """ 
    
    def _checkParams(self, params):
        RHAdminBase._checkParams(self, params)
        self._pluginType = params.get("pluginType", None)
        self._pluginId = params.get("pluginId", None)
        self._ph = PluginsHolder()
        if self._pluginType and not self._ph.hasPluginType(self._pluginType, mustBeActive = False):
            raise PluginError("The plugin type " + self._pluginType + " does not exist or is not visible")
        elif self._pluginType and self._pluginId and not self._ph.getPluginType(self._pluginType).hasPlugin(self._pluginId):
            raise PluginError("The plugin " + self._pluginId + " does not exist")

class RHAdminPlugins(RHAdminPluginsBase):
    """ Displays information about a given plugin type.
        The tab for that plugin type will be active.
    """
    _uh = urlHandlers.UHAdminPlugins
    
    def _checkParams(self, params):
        RHAdminPluginsBase._checkParams(self, params)
        if self._pluginType and not self._ph.hasPluginType(self._pluginType):
            raise PluginError("The plugin type " + self._pluginType + " does not exist, is not visible or is not active")
        self._initialPlugin = params.get('subtab', 0)
    
    def _process( self ):
        ph = self._ph
        if self._pluginType and ph.getGlobalPluginOptions().getReloadAllWhenViewingAdminTab():
            ph.reloadPluginType(self._pluginType)
        p = admins.WPAdminPlugins( self , self._pluginType, self._initialPlugin)
        return p.display()
    
class RHAdminPluginsReload(RHAdminPluginsBase):
    """ Reloads Plugins of a given type only.
    """
    _uh = urlHandlers.UHAdminPlugins
    
    def _checkParams(self, params):
        RHAdminPluginsBase._checkParams(self, params)
        if self._pluginType is None:
            raise PluginError(_("pluginType not set"))
        elif not self._ph.hasPluginType(self._pluginType):
            raise PluginError("The plugin type " + self._pluginType + " does not exist, is not visible or is not active")
    
    def _process( self ):
        ph = self._ph
        ph.reloadPluginType(self._pluginType)
        self._redirect( urlHandlers.UHAdminPlugins.getURL(self._ph.getPluginType(self._pluginType)))
    
class RHAdminTogglePluginType(RHAdminPluginsBase):
    """ Toggles the state of a plugin type between active and non active
    """
    _uh = urlHandlers.UHAdminTogglePluginType

    def _checkParams(self, params):
        RHAdminPluginsBase._checkParams(self, params)
        if self._pluginType is None:
            raise MaKaCError(_("pluginType not set"))

    def _process( self ):
        pluginType = self._ph.getPluginType(self._pluginType)
        pluginType.toggleActive()
        self._redirect( urlHandlers.UHAdminPlugins.getURL() )

class RHAdminTogglePlugin(RHAdminPluginsBase):
    """ Toggles the state of a plugin between active and non active
    """
    _uh = urlHandlers.UHAdminTogglePlugin
    
    def _checkParams(self, params):
        RHAdminPluginsBase._checkParams(self, params)
        if self._pluginType is None:
            raise PluginError(_("pluginType not set"))
        if self._pluginId is None:
            raise PluginError(_("pluginId not set"))
    
    def _process( self ):
        pluginType = self._ph.getPluginType(self._pluginType)
        pluginType.getPlugin(self._pluginId).toggleActive()
        self._redirect( urlHandlers.UHAdminPlugins.getURL(pluginType))
        

class RHAdminPluginsSaveOptionsBase(RHAdminPluginsBase):
    """ Base class for saving option values of a Plugin or a PluginType object, or processing actions.
        It defines an utility method _storeParams that will store strings in the self._optionValues dictionary
        and a string in the _action attribute. _action can be "Save" (to save option values)
        or the name of an action button if the action button was pushed.
        There is also another utility _processOption method that will turn strings into int, list, or dict objects
        if the respective option is of that type.
        The thirds utility method, _checkActionsToExecute, checks if we are saving the value of an option
        and if there are actions that should be executed in that case
        
    """
    
    def _checkParams(self, params):
        RHAdminPluginsBase._checkParams(self, params)

        if self._pluginType is None:
            raise PluginError(_("pluginType not set"))
        elif not self._ph.hasPluginType(self._pluginType):
            raise PluginError("The plugin type " + self._pluginType + " does not exist, is not visible or is not active")

        self._initialPlugin = params.get('subtab', 0)
    
    def _storeParams(self, params):
        """ Stores strings in the self._optionValues dictionary
            and a string in the _action attribute. _action can be "Save" (to save option values)
        """
        
        self._optionValues = {}
        
        optionNamePrefix = self._pluginType + '.'
        if self._pluginId is not None:
            optionNamePrefix += self._pluginId + '.'
        
        for k in params:
            if k.startswith(optionNamePrefix):
                self._optionValues[k[k.rfind('.')+1:]] = params[k]
        if "Save" in params:
            self._action = "Save"
        else:
            for k in params:
                if k.startswith("action." + optionNamePrefix):
                    self._action = k[k.rfind('.')+1:]
                    
    def _processOption(self, option, v):
        """ Will turn a string into int, list, or dict objects if the respective option is of that type.
        """
        if option.getType() == list:
            if v.strip():
                option.setValue([value.strip() for value in v.split(',')])
            else:
                option.setValue([])
        elif option.getType() == dict:
            d = {}
            items = v.split(',')
            for i in items:
                key, value = i.split(':')
                d[key.strip(string.whitespace + "{}\"\'")] = value.strip(string.whitespace + "{}\"\'")
            option.setValue(d)
        elif option.getType() == bool:
            option.setValue(True)
        else:
            option.setValue(v)
            
    def _checkActionsToExecute(self):
        """ Checks if we are saving the value of an option and if there are actions that should be executed in that case
        """
        if self._action == "Save":
            ph = self._ph
            
            pluginType = ph.getPluginType(self._pluginType)
            
            actionList = []
            
            if self._pluginId is not None:
                plugin = pluginType.getPlugin(self._pluginId)
                actionList.extend(plugin.getActionList(includeOnlyTriggeredBy = True, includeOnlyVisible = False))
            actionList.extend(pluginType.getActionList(includeOnlyTriggeredBy = True, includeOnlyVisible = False))
            
            for action in actionList:
                for savedOption in self._optionValues.keys():
                    if savedOption in action.getTriggeredBy():
                        action.call()
                        continue #ensures every action is executed only once
                    
    def _resetBoolOptions(self):
        """ Sets all bool options of this plugins to False,
            since if a checkbox is not ticked, the option will not appear in the params
        """
        boolOptions = self._target.getOptionList(filterByType = bool)
        for option in boolOptions:
            option.setValue(False)
            
    def _process(self):
        self._resetBoolOptions()
        
        if self._action == "Save":
            for k,v in self._optionValues.items():
                option = self._target.getOption(k)
                self._processOption(option, v)
            self._checkActionsToExecute()
        else:
            self._target.getAction(self._action).call()
        self._redirect( urlHandlers.UHAdminPlugins.getURL(self._ph.getPluginType(self._pluginType), subtab = self._initialPlugin))
        
class RHAdminPluginsSaveTypeOptions(RHAdminPluginsSaveOptionsBase):
    """ Saves values for options of a PluginType or executes an action for this PluginType.
    """
    _uh = urlHandlers.UHAdminPluginsTypeSaveOptions
    
    def _checkParams(self, params):
        RHAdminPluginsSaveOptionsBase._checkParams(self, params)
        self._storeParams(params)
        
        self._target = self._ph.getPluginType(self._pluginType)
    

class RHAdminPluginsSaveOptions(RHAdminPluginsSaveOptionsBase):
    """ Saves values for options of a Plugin or executes an action for this Plugin.
    """
    _uh = urlHandlers.UHAdminPluginsSaveOptions
        
    def _checkParams(self, params):
        RHAdminPluginsSaveOptionsBase._checkParams(self, params)
        if self._pluginId is None:
            raise PluginError(_("pluginId not set"))
        self._storeParams(params)
        
        self._target = self._ph.getPluginType(self._pluginType).getPlugin(self._pluginId)
        

class RHAdminPluginsReloadAll(RHAdminPluginsBase):
    """ Reloads ALL plugins from all types.
    """
    _uh = urlHandlers.UHAdminPluginsSaveOptionReloadAll
    
    def _process(self):
        ph = self._ph
        ph.reloadAllPlugins()
        self._redirect( urlHandlers.UHAdminPlugins.getURL())
        
class RHAdminPluginsClearAllInfo(RHAdminPluginsBase):
    """ Removes all information about plugins (which plugins are present, which are active, their options AND option values) from the DB.
    """
    _uh = urlHandlers.UHAdminPluginsSaveOptionReloadAll
    
    def _process(self):
        ph = self._ph
        ph.clearPluginInfo()
        self._redirect( urlHandlers.UHAdminPlugins.getURL())
        
class RHAdminPluginsSaveOptionReloadAll(RHAdminPluginsBase):
    """ Saves the value of the global option "reload plugins when navigating the plugin admin interface"
    """
    _uh = urlHandlers.UHAdminPluginsSaveOptionReloadAll

    def _checkParams(self, params):
        RHAdminPluginsBase._checkParams(self, params)
        self.__optionReloadAll = "optionReloadAll" in params
    
    def _process(self):
        ph = self._ph
        ph.getGlobalPluginOptions().setReloadAllWhenViewingAdminTab(self.__optionReloadAll)
        self._redirect( urlHandlers.UHAdminPlugins.getURL())
    
#Plugin admin end    

class RHSystem(RHAdminBase):
    _uh = urlHandlers.UHAdminsSystem
    
    def _process( self ):
        
        p = admins.WPAdminsSystem( self )
        return p.display()

class RHSystemModify(RHAdminBase):
    
    def _checkParams( self, params ):
        RHAdminBase._checkParams( self, params )
        self._action = params.get("action", None)
        self._proxy = False
        if params.get("proxy", False):
            self._proxy = True
    
    def _process( self ):
        if self._action == "ok":
            self._minfo.setProxy(self._proxy)
            self._redirect(urlHandlers.UHAdminsSystem.getURL())
        elif self._action == "cancel":
            self._redirect(urlHandlers.UHAdminsSystem.getURL())
        else:
            p = admins.WPAdminsSystemModif( self )
            return p.display()
        
class RHConferenceStyles(RHAdminBase):
    _uh = urlHandlers.UHAdminsConferenceStyles
    
    def _checkParams( self, params ):
        RHAdminBase._checkParams( self, params )
        
    def _process( self ):
        p = admins.WPAdminsConferenceStyles( self )
        return p.display() 
