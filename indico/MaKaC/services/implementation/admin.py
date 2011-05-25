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
from MaKaC.user import PrincipalHolder
import MaKaC.webcast as webcast

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

    def _getAnswer( self):
        ph = PrincipalHolder()
        pr = ph.getById(self._userId)
        if pr != None:
            self._wm.removeManager(pr)
        return True


methodMap = {
    "services.addWebcastAdministrators": AddWebcastAdministrators,
    "services.removeWebcastAdministrator": RemoveWebcastAdministrator,
}
