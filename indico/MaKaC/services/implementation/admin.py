# -*- coding: utf-8 -*-
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
from MaKaC.services.implementation.base import ParameterManager
from MaKaC.user import PrincipalHolder, AvatarHolder, GroupHolder
import MaKaC.webcast as webcast
import MaKaC.common.timezoneUtils as timezoneUtils
from MaKaC.services.interface.rpc.common import ServiceError
import MaKaC.common.info as info
from MaKaC.common.fossilize import fossilize


### Webcast Administrators classes ###
class AddWebcastAdministrators(AdminService):

    def _checkParams(self):
        AdminService._checkParams(self)
        pm = ParameterManager(self._params)
        self._wm = webcast.HelperWebcastManager.getWebcastManagerInstance()
        self._userList = pm.extract("userList", pType=list, allowEmpty=False)

    def _getAnswer( self):
        ph = PrincipalHolder()
        for user in self._userList:
            pr = ph.getById(user["id"])
            if pr != None:
                self._wm.addManager(pr)
        return True

class RemoveWebcastAdministrator(AdminService):

    def _checkParams(self):
        AdminService._checkParams(self)
        pm = ParameterManager(self._params)
        self._wm = webcast.HelperWebcastManager.getWebcastManagerInstance()
        self._userId = pm.extract("user", pType=str, allowEmpty=False)
        self._pr = PrincipalHolder().getById(self._userId)
        if self._pr == None:
            raise ServiceError("ER-U0", _("Cannot found user with id %s") % self._userId)

    def _getAnswer( self):
        ph = PrincipalHolder()
        pr = ph.getById(self._userId)
        if pr != None:
            self._wm.removeManager(pr)
        return True


### Administrator Login as... class ###
class AdminLoginAs(AdminService):

    def _checkParams(self):
        AdminService._checkParams(self)
        pm = ParameterManager(self._params)
        self._userId = pm.extract("userId", pType=str, allowEmpty=False)
        self._av = AvatarHolder().getById(self._userId)
        if self._av == None:
            raise ServiceError("ER-U0", _("Cannot found user with id %s") % self._userId)

    def _getAnswer(self):
        tzUtil = timezoneUtils.SessionTZ(self._av)
        tz = tzUtil.getSessionTZ()
        self._getSession().setVar("ActiveTimezone", tz)
        self._getSession().setUser(self._av)
        return True


class GetAdministratorList(AdminService):

    def _getAnswer(self):
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        return fossilize(minfo.getAdminList())


class AddExistingAdministrator(AdminService):

    def _checkParams(self):
        AdminService._checkParams(self)
        pm = ParameterManager(self._params)
        self._userList = pm.extract("userList", pType=list, allowEmpty=False)

    def _getAnswer(self):
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        adminList = minfo.getAdminList()
        ph = PrincipalHolder()
        for user in self._userList:
            principal = ph.getById(user["id"])
            if principal != None:
                adminList.grant(principal)
            else:
                raise ServiceError("ER-U0", _("Cannot found user with id %s") % user["id"])
        return fossilize(minfo.getAdminList())


class RemoveAdministrator(AdminService):

    def _checkParams(self):
        AdminService._checkParams(self)
        pm = ParameterManager(self._params)
        self._userId = pm.extract("userId", pType=str, allowEmpty=False)

    def _getAnswer(self):
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        adminList = minfo.getAdminList()
        ph = PrincipalHolder()
        user = ph.getById(self._userId)
        if user != None:
            adminList.revoke(user)
        else:
            raise ServiceError("ER-U0", _("Cannot found user with id %s") % self._userId)
        return fossilize(minfo.getAdminList())


class GroupMemberBase(AdminService):

    def _checkParams(self):
        AdminService._checkParams(self)
        self._pm = ParameterManager(self._params)
        gh = GroupHolder()
        groupId = self._pm.extract("groupId", pType=str, allowEmpty=False)
        self._group = gh.getById(groupId)
        if self._group == None:
            raise ServiceError("ER-G0", _("Cannot found group with id %s") % groupId)


class GroupGetMemberList(GroupMemberBase):

    def _getAnswer(self):
        return fossilize(self._group.getMemberList())


class GroupAddExistingMember(GroupMemberBase):

    def _checkParams(self):
        GroupMemberBase._checkParams(self)
        self._userList = self._pm.extract("userList", pType=list, allowEmpty=False)

    def _getAnswer(self):
        ph = PrincipalHolder()
        for user in self._userList:
            principal = ph.getById(user["id"])
            if principal != None:
                self._group.addMember(principal)
            else:
                raise ServiceError("ER-U0", _("Cannot found user with id %s") % user["id"])
        return fossilize(self._group.getMemberList())


class GroupRemoveMember(GroupMemberBase):

    def _checkParams(self):
        GroupMemberBase._checkParams(self)
        self._userId = self._pm.extract("userId", pType=str, allowEmpty=False)

    def _getAnswer(self):
        ph = PrincipalHolder()
        user = ph.getById(self._userId)
        if user != None:
            self._group.removeMember(user)
        else:
            raise ServiceError("ER-U0", _("Cannot found user with id %s") % self._userId)
        return fossilize(self._group.getMemberList())


methodMap = {
    "services.addWebcastAdministrators": AddWebcastAdministrators,
    "services.removeWebcastAdministrator": RemoveWebcastAdministrator,

    "general.addExistingAdmin": AddExistingAdministrator,
    "general.removeAdmin": RemoveAdministrator,
    "general.getAdminList": GetAdministratorList,

    "header.loginAs": AdminLoginAs,

    "groups.addExistingMember": GroupAddExistingMember,
    "groups.removeMember": GroupRemoveMember,
    "groups.getMemberList": GroupGetMemberList
}
