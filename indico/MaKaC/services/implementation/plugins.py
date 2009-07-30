# -*- coding: utf-8 -*-
##
## $Id: plugins.py,v 1.3 2009/04/14 09:45:39 jose Exp $
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

from MaKaC.services.implementation.base import AdminService
from MaKaC.services.interface.rpc.common import ServiceError
from MaKaC.plugins.base import PluginsHolder
from MaKaC.webinterface.user import UserListModificationBase, UserModificationBase

class PluginOptionsBase (AdminService):
    
    def _checkParams(self):
        optionName = self._params.get('optionName', None)
        if optionName:
            options = optionName.split('.')
            if len(options) == 3:
                pluginType, plugin, option = options
                self._targetOption = PluginsHolder().getPluginType(pluginType).getPlugin(plugin).getOption(option)
            elif len(options) == 2:
                pluginType, option = options
                self._targetOption = PluginsHolder().getPluginType(pluginType).getOption(option)
            else:
                raise ServiceError('ERR-PLUG1', 'optionName argument does not have the proper pluginType.plugin.option format')
        else:
            raise ServiceError('ERR-PLUG0', 'optionName argument not present') 
            

class PluginOptionsAddUsers ( PluginOptionsBase, UserListModificationBase):
    
    def _checkParams(self):
        PluginOptionsBase._checkParams(self)
        UserListModificationBase._checkParams(self)
        
    def _getAnswer(self):
        if self._targetOption.getType() == 'users':
            self._targetOption.getValue().extend(self._avatars)
            self._targetOption._notifyModification()
        else:
            raise ServiceError('ERR-PLUG2', "option %s.%s.%s is not of type 'users'" % (self._pluginType, self._plugin, self._targetOption))
        
        return True

class PluginOptionsRemoveUser ( PluginOptionsBase, UserModificationBase ):

    def _checkParams(self):
        PluginOptionsBase._checkParams(self)
        UserModificationBase._checkParams(self)
        
    def _getAnswer(self):
        if self._targetOption.getType() == 'users':
            self._targetOption.getValue().remove(self._targetUser)
            self._targetOption._notifyModification()
        else:
            raise ServiceError('ERR-PLUG2', "option %s.%s.%s is not of type 'users'" % (self._pluginType, self._plugin, self._targetOption))
        
        return True

class PluginOptionsAddRooms ( PluginOptionsBase ):
    
    def _checkParams(self):
        PluginOptionsBase._checkParams(self)
        
    def _getAnswer(self):
        if self._targetOption.getType() == 'rooms':
            roomToAdd=self._params.get("room")
            self._targetOption.getValue().append(roomToAdd)
            self._targetOption._notifyModification()
        else:
            raise ServiceError('ERR-PLUG2', "option %s.%s.%s is not of type 'rooms'" % (self._pluginType, self._plugin, self._targetOption))
        
        return True

class PluginOptionsRemoveRooms ( PluginOptionsBase ):

    def _checkParams(self):
        PluginOptionsBase._checkParams(self)
        
    def _getAnswer(self):
        if self._targetOption.getType() == 'rooms':
            roomToRemove=self._params.get("room")
            self._targetOption.getValue().remove(roomToRemove)
            self._targetOption._notifyModification()
        else:
            raise ServiceError('ERR-PLUG2', "option %s.%s.%s is not of type 'rooms'" % (self._pluginType, self._plugin, self._targetOption))
        
        return True

methodMap = {
    "addUsers": PluginOptionsAddUsers,
    "removeUser": PluginOptionsRemoveUser,
    "addRooms": PluginOptionsAddRooms,
    "removeRooms": PluginOptionsRemoveRooms
}
