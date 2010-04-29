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

from MaKaC.services.implementation.base import AdminService
from MaKaC.services.interface.rpc.common import ServiceError
from MaKaC.plugins.base import PluginsHolder
from MaKaC.webinterface.user import UserListModificationBase, UserModificationBase

class PluginOptionsBase (AdminService):
    
    def _checkParams(self):
        optionName = self._params.get('optionName', None)
        if optionName:
            options = optionName.split('.')
            ph = PluginsHolder()
            if len(options) == 3:
                pluginType, plugin, option = options
                if ph.hasPluginType(pluginType):
                    if ph.getPluginType(pluginType).hasPlugin(plugin):
                        self._targetOption = ph.getPluginType(pluginType).getPlugin(plugin).getOption(option)
                    else:
                        raise ServiceError('ERR-PLUG4', 'plugin: ' + str(plugin) + ' does not exist')
                else:
                    raise ServiceError('ERR-PLUG3', 'pluginType: ' + str(pluginType) + ' does not exist, is not visible or not active')
            elif len(options) == 2:
                pluginType, option = options
                if ph.hasPluginType(pluginType):
                    self._targetOption = ph.getPluginType(pluginType).getOption(option)
                else:
                    raise ServiceError('ERR-PLUG3', 'pluginType: ' + str(pluginType) + ' does not exist, is not visible or not active')
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
            optionValue = self._targetOption.getValue()
            existingUserIds = set([u.getId() for u in optionValue])
            for u in self._avatars:
                if not u.getId() in existingUserIds:
                    optionValue.append(u)
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
            optionValue = self._targetOption.getValue()
            roomToAdd = self._params.get("room")
            if roomToAdd not in optionValue:
                optionValue.append(roomToAdd)
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
