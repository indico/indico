# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.
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
        self._lastUseAuthenticated = False
        self._oldKeys = PersistentList()
        self._persistentAllowed = False

    def __repr__(self):
        return '<APIKey({0}, {1!r}, {2})>'.format(self._key, self._user, self._lastUsedDT)

    def getUser(self):
        return self._user

    def setUser(self, user):
        self._user = user

    def getKey(self):
        return self._key
    getId = getKey

    def setKey(self, key):
        akh = APIKeyHolder()
        if self.getId() is not None:
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

    def isLastUseAuthenticated(self):
        return self._lastUseAuthenticated

    def getLastRequest(self):
        if not self._lastPath:
            return None
        if self._lastQuery:
            return '%s?%s' % (self._lastPath, self._lastQuery)
        return self._lastPath

    def getOldKeys(self):
        return self._oldKeys

    def isPersistentAllowed(self):
        return getattr(self, '_persistentAllowed', False)

    def setPersistentAllowed(self, val):
        self._persistentAllowed = val

    def used(self, ip, path, query, authenticated):
        self._lastUsedDT = datetime.datetime.now()
        self._lastUsedIP = ip
        self._lastPath = path
        self._lastQuery = query
        self._lastUseAuthenticated = authenticated
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
