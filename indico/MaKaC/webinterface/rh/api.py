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

from indico.web.http_api.auth import APIKey
from MaKaC.webinterface.rh.users import RHUserBase
from MaKaC.webinterface import urlHandlers
from MaKaC.webinterface.pages.api import WPUserAPI
from MaKaC.errors import AccessError

class RHUserAPI(RHUserBase):
    def _process(self):
        p = WPUserAPI(self, self._avatar)
        return p.display()

class RHUserAPICreate(RHUserBase):
    def _checkProtection(self):
        RHUserBase._checkProtection(self)
        ak = self._avatar.getAPIKey()
        if ak and ak.isBlocked():
            raise AccessError()

    def _process(self):
        ak = self._avatar.getAPIKey()
        if not ak:
            ak = APIKey(self._avatar)
            ak.create()
        else:
            ak.newKey()
        self._redirect(urlHandlers.UHUserAPI.getURL(self._avatar))