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

from zope.interface import implements
from persistent import Persistent
import oauth2 as oauth
from indico.modules.oauth.components import IIndexableByUserId
from indico.core.index import IUniqueIdProvider, Catalog
from indico.modules.oauth.fossils import IConsumerFossil
from MaKaC.common.ObjectHolders import ObjectHolder
from indico.util.fossilize import fossilizes

class OAuthServer:
    _instance = None

    @classmethod
    def getInstance(cls):
        if cls._instance == None:
            cls._instance =  oauth.Server()
            cls._instance.add_signature_method(oauth.SignatureMethod_PLAINTEXT())
            cls._instance.add_signature_method(oauth.SignatureMethod_HMAC_SHA1())
        return cls._instance

class ConsumerHolder(ObjectHolder):
    idxName = "consumers"
    counterName = "CONSUMER"


class AccessTokenHolder(ObjectHolder):
    idxName = "access_tokens"
    counterName = "ACCESS_TOKEN"

    def add(self, token):
        ObjectHolder.add(self, token)
        Catalog.getIdx('user_oauth_access_token').index_obj(token)

    def remove(self, token):
        ObjectHolder.remove(self, token)
        Catalog.getIdx('user_oauth_access_token').unindex_obj(token)


class TempRequestTokenHolder(ObjectHolder):
    idxName = "temp_request_tokens"
    counterName = "TEMP_REQUEST_TOKEN"


class RequestTokenHolder(ObjectHolder):
    idxName = "request_tokens"
    counterName = "REQUEST_TOKEN"

    def add(self, token):
        ObjectHolder.add(self, token)
        Catalog.getIdx('user_oauth_request_token').index_obj(token)

    def remove(self, token):
        ObjectHolder.remove(self, token)
        Catalog.getIdx('user_oauth_request_token').unindex_obj(token)

    def update(self, old_token, new_token):
        ObjectHolder.remove(self, old_token)
        Catalog.getIdx('user_oauth_request_token').unindex_obj(old_token)
        ObjectHolder.add(self, new_token)
        Catalog.getIdx('user_oauth_request_token').index_obj(new_token)


class Consumer(Persistent):
    fossilizes(IConsumerFossil)
    def __init__(self, key, secret, name, trusted= False, blocked= False):
        self._key = key
        self._secret = secret
        self._name = name
        self._trusted = trusted
        self._blocked = blocked

    def getId(self):
        return self._key

    def getSecret(self):
        return self._secret

    def getName(self):
        return self._name

    def isTrusted(self):
        return self._trusted

    def setTrusted(self, trusted):
        self._trusted = trusted

    def isBlocked(self):
        return self._blocked

    def setBlocked(self, blocked):
        self._blocked = blocked


class Token(Persistent):

    implements(IUniqueIdProvider, IIndexableByUserId)

    def __init__(self, key, token, timestamp, consumer, user, authorized=False):
        self._key = key
        self._token = token
        self._timestamp = timestamp
        self._consumer = consumer
        self._user = user
        self._authorized = authorized

    def getId(self):
        return self._key

    def getUniqueId(self):
        return self._key

    def getToken(self):
        return self._token

    def setToken(self, token):
        self._token = token

    def getTimestamp(self):
        return self._timestamp

    def setTimestamp(self, timestamp):
        self._timestamp = timestamp

    def getUser(self):
        return self._user

    def setUser(self, user):
        self._user = user

    def getConsumer(self):
        return self._consumer

    def setAuthorized(self, authorized):
        self._authorized = authorized

    def isAuthorized(self):
        return self._authorized

    def __conform__(self, proto):
        if proto == IIndexableByUserId:
            return self.getUser().getId()
