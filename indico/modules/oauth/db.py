import MaKaC.common.ObjectHolders
from indico.core.index import IUniqueIdProvider, OOIndex, Catalog
from zope.interface import implements
from MaKaC.common.ObjectHolders import ObjectHolder
from persistent import Persistent
from indico.modules.oauth import IIndexableByUserId

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

    def add(self, token):
        ObjectHolder.add(self, token)

    def remove(self, token):
        ObjectHolder.remove(self, token)


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
    def __init__(self, key, secret, name):
        self._key = key
        self._secret = secret
        self._name = name
        self._request_token = None

    def getId(self):
        return self._key

    def getSecret(self):
        return self._secret

    def getName(self):
        return self._name


class Token(Persistent):

    implements(IUniqueIdProvider, IIndexableByUserId)

    def __init__(self, key, token, timestamp, consumer, user_id):
        self._key = key
        self._token = token
        self._timestamp = timestamp
        self._consumer = consumer
        self._user_id = user_id

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

    def getUserId(self):
        return self._user_id

    def setUserId(self, user_id):
        self._user_id = user_id

    def getConsumer(self):
        return self._consumer

    def __conform__(self, proto):
        if proto == IIndexableByUserId:
            return self.getUserId()