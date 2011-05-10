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
from persistent.list import PersistentList
from MaKaC.common.ObjectHolders import ObjectHolder

class APIKeyHolder(ObjectHolder):
    idxName = 'apikeys'

    def makeKey(self):
        key = str(uuid.uuid4())
        while self.hasKey(key):
            key = str(uuid.uuid4())
        return key

class APIKey(Persistent):
    def __init__(self, user, key=None, signKey=None):
        self._user = user
        self._key = key
        self._signKey = signKey
        self._createdDT = datetime.datetime.now()
        self._isBlocked = False
        self._lastUsedDT = None
        self._lastUsedIP = None
        self._useCount = 0
        self._lastPath = None
        self._lastQuery = None
        self._oldKeys = PersistentList()

    def getUser(self):
        return self._user

    def getKey(self):
        return self._key
    getId = getKey

    def setKey(self, key):
        akh = APIKeyHolder()
        akh.remove(self)
        if self.getKey():
            self._oldKeys.append(self.getKey())
        self._key = key
        akh.add(self)

    def getSignKey(self):
        return self._signKey

    def setSignKey(self, signKey):
        self._signKey = signKey

    def getCreatedDT(self):
        return self._createdDT

    def getLastUsedDT(self):
        return self._lastUsedDT

    def isBlocked(self):
        return self._isBlocked

    def setBlocked(self, blocked):
        self._isBlocked = blocked

    def getLastUsedIP(self):
        return self._lastUsedIP

    def getUseCount(self):
        return self._useCount

    def getLastRequest(self):
        if not self._lastPath:
            return None
        if self._lastQuery:
            return '%s?%s' % (self._lastPath, self._lastQuery)
        return self._lastPath

    def getOldKeys(self):
        return self._oldKeys

    def used(self, ip, path, query):
        self._lastUsedDT = datetime.datetime.now()
        self._lastUsedIP = ip
        self._lastPath = path
        self._lastQuery = query
        self._useCount += 1

    def newKey(self):
        akh = APIKeyHolder()
        self.setKey(akh.makeKey())
        return self.getKey()

    def newSignKey(self):
        self.setSignKey(str(uuid.uuid4()))

    def create(self):
        akh = APIKeyHolder()
        if not self.getKey():
            self.newKey()
        if not self.getSignKey():
            self.newSignKey()
        self._user.setAPIKey(self)
        akh.add(self)

    def remove(self):
        akh = APIKeyHolder()
        self._user.setAPIKey(None)
        akh.removeById(self.getKey())
