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
import datetime
import uuid
from persistent import Persistent
from MaKaC.common.ObjectHolders import ObjectHolder

class APIKeyHolder(ObjectHolder):
    idxName = 'apikeys'

    def makeKey(self):
        key = str(uuid.uuid4())
        while self.hasKey(key):
            key = str(uuid.uuid4())
        return key

class APIKey(Persistent):
    def __init__(self, user, key=None):
        self._user = user
        self._key = key
        self._createdDT = datetime.datetime.now()
        self._lastUsedDT = None
        self._lastUsedIP = None
        self._useCount = 0

    def getUser(self):
        return self._user

    def getKey(self):
        return self._key
    getId = getKey

    def setKey(self, key):
        akh = APIKeyHolder()
        akh.remove(self)
        self._key = key
        akh.add(self)

    def getCreatedDT(self):
        return self._createdDT

    def getLastUsedDT(self):
        return self._lastUsedDT

    def getLastUsedIP(self):
        return self._lastUsedIP

    def getUseCount(self):
        return self._useCount

    def used(self, ip):
        self._lastUsedDT = datetime.datetime.now()
        self._lastUsedIP = ip
        self._useCount += 1

    def newKey(self):
        akh = APIKeyHolder()
        self.setKey(akh.makeKey())
        return self.getKey()

    def create(self):
        akh = APIKeyHolder()
        if not self.getKey():
            self.newKey()
        self._user.setAPIKey(self)
        akh.add(self)

    def remove(self):
        akh = APIKeyHolder()
        self._user.setAPIKey(None)
        akh.removeById(self.getKey())
