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

from Configuration import Config
from MaKaC.errors import MaKaCError
from MaKaC.common.logger import Logger
from MaKaC.common import timezoneUtils
from MaKaC.common.utils import OSSpecific
from MaKaC.common.contextManager import ContextManager
from indico.util.fs import silentremove
from indico.util.redis import redis

import hashlib, os, shutil, datetime, time
import cPickle as pickle
from itertools import izip

class CacheStorage(object):
    __CACHE_STORAGE_LIST = {}
    __CACHE_STORAGE_DEFAULT = None

    @classmethod
    def new(cls, *args, **kwargs):
        backend = Config.getInstance().getCacheBackend()
        storageCls = cls.__CACHE_STORAGE_LIST.get(backend, cls.__CACHE_STORAGE_DEFAULT)
        return storageCls(*args, **kwargs)

    @classmethod
    def register(cls, default=False):
        def decorate(klass):
            cls.__CACHE_STORAGE_LIST[klass.STORAGE_NAME] = klass
            if default:
                cls.__CACHE_STORAGE_DEFAULT = klass
            return klass
        return decorate

    def __init__(self, cache):
        self._cache = cache
        self._name = cache.cacheName
        Logger.get('cache/%s' % self._name).debug('Using %s for storage' % self.STORAGE_NAME)

    def getTTL(self):
        return self._cache.getTTL()

    def save(self, path, name, data):
        raise NotImplementedError

    def load(self, path, name, default=None):
        raise NotImplementedError

    def remove(self, path, name):
        raise NotImplementedError


@CacheStorage.register(True)
class FileCacheStorage(CacheStorage):
    STORAGE_NAME = 'files'

    def __init__(self, cache):
        super(FileCacheStorage, self).__init__(cache)
        self._dir = os.path.join(Config.getInstance().getXMLCacheDir(), self._name)
        if not os.path.exists(self._dir):
            os.makedirs(self._dir)

    def save(self, path, name, data):
        fsPath = os.path.join(self._dir, path)
        if not os.path.exists(fsPath):
            os.makedirs(fsPath)
        filePath = os.path.join(fsPath, name)
        f = open(filePath, 'wb')
        OSSpecific.lockFile(f, 'LOCK_EX')
        try:
            pickle.dump(data, f)
        finally:
            OSSpecific.lockFile(f, 'LOCK_UN')
            f.close()

    def load(self, path, name, default=None):
        filePath = os.path.join(self._dir, path, name)
        if not os.path.exists(filePath):
            return default, None
        f = open(filePath, 'rb')
        OSSpecific.lockFile(f, 'LOCK_SH')
        try:
            obj = pickle.load(f)
            mtime = os.path.getmtime(filePath)
        finally:
            OSSpecific.lockFile(f, 'LOCK_UN')
            f.close()
        return obj, mtime

    def remove(self, path, name):
        filePath = os.path.join(self._dir, path, name)
        if os.path.exists(filePath):
            os.remove(filePath)


@CacheStorage.register()
class MemcachedCacheStorage(CacheStorage):
    STORAGE_NAME = 'memcached'

    def __init__(self, cache):
        super(MemcachedCacheStorage, self).__init__(cache)

    def _connect(self):
        import memcache
        return memcache.Client(Config.getInstance().getMemcachedServers())

    def _makeKey(self, path, name):
        return hashlib.sha256(os.path.join(self._name, path, name)).hexdigest()

    def save(self, path, name, data):
        self._connect().set(self._makeKey(path, name), pickle.dumps(data), self.getTTL())

    def load(self, path, name, default=None):
        obj = self._connect().get(self._makeKey(path, name))
        if obj:
            obj = pickle.loads(obj)
        return obj, None

    def remove(self, path, name):
        self._connect().delete(self._makeKey(path, name))


@CacheStorage.register()
class RedisCacheStorage(CacheStorage):
    STORAGE_NAME = 'redis'

    def __init__(self, cache):
        super(RedisCacheStorage, self).__init__(cache)

    def _connect(self):
        client = redis.StrictRedis.from_url(Config.getInstance().getRedisCacheURL())
        client.connection_pool.connection_kwargs['socket_timeout'] = 1
        return client

    def _makeKey(self, path, name):
        return 'cache/ml/' + os.path.join(self._name, path, name)

    def save(self, path, name, data):
        try:
            self._connect().setex(self._makeKey(path, name), self.getTTL(), pickle.dumps(data))
        except redis.RedisError:
            Logger.get('redisCache').exception('save failed')

    def load(self, path, name, default=None):
        try:
            obj = self._connect().get(self._makeKey(path, name))
        except redis.RedisError:
            Logger.get('redisCache').exception('load failed')
            return None, None
        if obj:
            obj = pickle.loads(obj)
        return obj, None

    def remove(self, path, name):
        try:
            self._connect().delete(self._makeKey(path, name))
        except redis.RedisError:
            Logger.get('redisCache').exception('remove failed')


class MultiLevelCacheEntry(object):
    """
    An entry(line) for a multilevel cache
    """

    def __init__(self):
        pass

    def getId(self):
        """
        Overloaded by subclasses
        """
        pass

    def setContent(self, content):
        self.content = content

    def getContent(self):
        return self.content


class MultiLevelCache(object):
    """
    A multilevel cache.

    DEPRECATED in favour of GenericCache!
    Do not use it. It is only left because the XMLCache relies on it.
    Why we don't migrate it to GenericCache? XMLCache is not used right now and when
    its caveats are fixed it will probably be enabled. At this point it should be migrated
    to GenericCache and MultiLevelCache / MultiLevelCacheEntry removed!
    """

    _entryFactory = None
    _entryTTL = 86400

    def __init__(self, cacheName):
        self.cacheName = cacheName
        self._v_storage = CacheStorage.new(self)

    def getStorage(self):
        if not hasattr(self, '_v_storage') or self._v_storage is None:
            self._v_storage = CacheStorage.new(self)
        return self._v_storage

    def setTTL(self, ttl):
        self._entryTTL = ttl

    def getTTL(self):
        return self._entryTTL

    def cacheObject(self, version, content, *args):
        """
        Puts an object into the cache
        """

        entry = self._entryFactory.create(content, *args)
        path = self._generatePath(entry)
        fileName = self._generateFileName(entry, version)

        self.getStorage().save(os.path.join(*path), fileName, entry)

        Logger.get('cache/%s' % self.cacheName).debug(
            "Saved %s" % (os.path.join(*(path + [fileName]))))

    def loadObject(self, version, *args):
        """
        Loads an object from the cache, returning None if it doesn't exist
        or in case it is dirty (has expired)
        """

        dummyEntry = self._entryFactory.create(None, *args)
        path = os.path.join(*self._generatePath(dummyEntry))
        fileName = self._generateFileName(dummyEntry, version)

        Logger.get('cache/%s' % self.cacheName).debug(
            "Checking %s..." % os.path.join(path, fileName))
        obj, mtime = self.getStorage().load(path, fileName)

        if obj is not None:
            # (Possible) Cache hit
            # check dirty state first
            if mtime is not None and self.isDirty(mtime, obj):
                Logger.get('cache/%s' % self.cacheName).debug("DIRTY")
                # if the file is older, report a miss
                # self.getStorage().remove(path, fileName)
                return None
            else:
                Logger.get('cache/%s' % self.cacheName).debug("HIT")
                return obj

        else:
            Logger.get('cache/%s' % self.cacheName).debug("MISS")
            # Cache miss
            return None

    def isDirty(self, mtime, object):
        if self._entryTTL == -1:
            return True
        creationTime = datetime.datetime(*time.localtime(mtime)[:6])
        return datetime.datetime.now() - creationTime > datetime.timedelta(seconds=self._entryTTL)

    def _generatePath(self, entry):
        """
        Generate the actual hierarchical location
        Can be overriden
        """

        return [entry.getId()[0]]

    def _generateFileName(self, entry, version):
        """
        Generate the file name
        Can be overriden
        """

        return '%s_%s' % (entry.getId(), version)


class CacheClient(object):

    def set_multi(self, mapping, ttl=0):
        for key, val in mapping.iteritems():
            self.set(key, val, ttl)

    def get_multi(self, keys):
        values = {}
        for key in keys:
            val = self.get(key)
            if val is not None:
                values[key] = val
        return values

    def delete_multi(self, keys):
        for key in keys:
            self.delete(key)


class NullCacheClient(CacheClient):
    """
    Does nothing
    """

    def set(self, key, val, ttl=0):
        pass

    def get(self, key):
        return None

    def delete(self, key):
        pass


class RedisCacheClient(CacheClient):
    """Redis-based cache client with a simple API"""

    key_prefix = 'cache/gen/'

    def __init__(self, url):
        self._client = redis.StrictRedis.from_url(url)
        self._client.connection_pool.connection_kwargs['socket_timeout'] = 1

    def _unpickle(self, val):
        if val is None:
            return None
        return pickle.loads(val)

    def hash_key(self, key):
        # Redis keys are even binary-safe, no need to hash anything
        return key

    def set_multi(self, mapping, ttl=0):
        try:
            self._client.mset(dict((k, pickle.dumps(v)) for k, v in mapping.iteritems()))
            if ttl:
                for key in mapping:
                    self._client.expire(key, ttl)
        except redis.RedisError:
            Logger.get('redisCache').exception('set_multi failed')

    def get_multi(self, keys):
        try:
            return dict(zip(keys, map(self._unpickle, self._client.mget(keys))))
        except redis.RedisError:
            Logger.get('redisCache').exception('get_multi failed')

    def delete_multi(self, keys):
        try:
            self._client.delete(*keys)
        except redis.RedisError:
            Logger.get('redisCache').exception('delete_multi failed')

    def set(self, key, val, ttl=0):
        try:
            if ttl:
                self._client.setex(key, ttl, pickle.dumps(val))
            else:
                self._client.set(key, pickle.dumps(val))
        except redis.RedisError:
            Logger.get('redisCache').exception('set failed')

    def get(self, key):
        try:
            return self._unpickle(self._client.get(key))
        except redis.RedisError:
            Logger.get('redisCache').exception('get failed')

    def delete(self, key):
        try:
            self._client.delete(key)
        except redis.RedisError:
            Logger.get('redisCache').exception('delete failed')


class FileCacheClient(CacheClient):
    """File-based cache with a memcached-like API.

    Contains only features needed by GenericCache.
    """
    def __init__(self, dir):
        self._dir = os.path.join(dir, 'generic_cache')

    def _getFilePath(self, key, mkdir=True):
        # We assume keys have a 'namespace.hashedKey' format
        parts = key.split('.', 1)
        if len(parts) == 1:
            namespace = '_'
            filename = parts[0]
        else:
            namespace, filename = parts
        dir = os.path.join(self._dir, namespace, filename[:4], filename[:8])
        if mkdir and not os.path.exists(dir):
            try:
                os.makedirs(dir)
            except OSError:
                # Handle race condition
                if not os.path.exists(dir):
                    raise
        return os.path.join(dir, filename)

    def set(self, key, val, ttl=0):
        try:
            f = open(self._getFilePath(key), 'wb')
            OSSpecific.lockFile(f, 'LOCK_EX')
            try:
                expiry = int(time.time()) + ttl if ttl else None
                data = (expiry, val)
                pickle.dump(data, f)
            finally:
                OSSpecific.lockFile(f, 'LOCK_UN')
                f.close()
        except (IOError, OSError):
            Logger.get('FileCache').exception('Error setting value in cache')
            return 0
        return 1

    def get(self, key):
        try:
            path = self._getFilePath(key, False)
            if not os.path.exists(path):
                return None

            f = open(path, 'rb')
            OSSpecific.lockFile(f, 'LOCK_SH')
            expiry = val = None
            try:
                expiry, val = pickle.load(f)
            finally:
                OSSpecific.lockFile(f, 'LOCK_UN')
                f.close()
            if expiry and time.time() > expiry:
                return None
        except (IOError, OSError):
            Logger.get('FileCache').exception('Error getting cached value')
            return None
        except (EOFError, pickle.UnpicklingError):
            Logger.get('FileCache').exception('Cached information seems corrupted. Overwriting it.')
            return None

        return val

    def delete(self, key):
        path = self._getFilePath(key, False)
        if os.path.exists(path):
            silentremove(path)
        return 1


class GenericCache(object):
    def __init__(self, namespace):
        self._client = None
        self._namespace = namespace

    def __repr__(self):
        return 'GenericCache(%r)' % self._namespace

    def _connect(self):
        # Maybe we already have a client in this instance
        if self._client is not None:
            return
        # If not, we might have one from another instance
        self._client = ContextManager.get('GenericCacheClient', None)

        if self._client is not None:
            return

        # If not, create a new one
        backend = Config.getInstance().getCacheBackend()
        if backend == 'memcached':
            import memcache
            self._client = memcache.Client(Config.getInstance().getMemcachedServers())
        elif backend == 'redis':
            self._client = RedisCacheClient(Config.getInstance().getRedisCacheURL())
        elif backend == 'files':
            self._client = FileCacheClient(Config.getInstance().getXMLCacheDir())
        else:
            self._client = NullCacheClient()

        ContextManager.set('GenericCacheClient', self._client)

    def _hashKey(self, key):
        if hasattr(self._client, 'hash_key'):
            return self._client.hash_key(key)
        return hashlib.sha256(key).hexdigest()

    def _makeKey(self, key):
        if not isinstance(key, basestring):
            # In case we get something not a string (number, list, whatever)
            key = repr(key)
        # Hashlib doesn't allow unicode so let's ensure it's not!
        key = key.encode('utf-8')
        return '%s%s.%s' % (getattr(self._client, 'key_prefix', ''), self._namespace, self._hashKey(key))

    def _processTime(self, ts):
        if isinstance(ts, datetime.timedelta):
            ts = ts.seconds + (ts.days * 24 * 3600)
        return ts

    def set(self, key, val, time=0):
        self._connect()
        time = self._processTime(time)
        Logger.get('GenericCache/%s' % self._namespace).debug('SET %r (%d)' % (key, time))
        self._client.set(self._makeKey(key), val, time)

    def set_multi(self, mapping, time=0):
        self._connect()
        time = self._processTime(time)
        mapping = dict(((self._makeKey(key), val) for key, val in mapping.iteritems()))
        self._client.set_multi(mapping, time)

    def get(self, key, default=None):
        self._connect()
        res = self._client.get(self._makeKey(key))
        Logger.get('GenericCache/%s' % self._namespace).debug('GET %r -> %r' % (key, res is not None))
        if res is None:
            return default
        return res

    def get_multi(self, keys, default=None, asdict=True):
        self._connect()
        real_keys = map(self._makeKey, keys)
        data = self._client.get_multi(real_keys)
        # Add missing keys
        for real_key in real_keys:
            if real_key not in data:
                data[real_key] = default
        # Get data in the same order as our keys
        sorted_data = (data[rk] for rk in real_keys)
        if asdict:
            return dict(izip(keys, sorted_data))
        else:
            return list(sorted_data)

    def delete(self, key):
        self._connect()
        Logger.get('GenericCache/%s' % self._namespace).debug('DEL %r' % key)
        self._client.delete(self._makeKey(key))

    def delete_multi(self, keys):
        self._connect()
        keys = map(self._makeKey, keys)
        self._client.delete_multi(keys)
