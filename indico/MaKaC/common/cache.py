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

from Configuration import Config
from MaKaC.errors import MaKaCError
from MaKaC.common.logger import Logger

from MaKaC.common.logger import Logger
from MaKaC.common import timezoneUtils
from MaKaC.common.utils import OSSpecific

import hashlib, os, shutil, pickle, datetime, time


class IndicoCache:
    """
    Used to cache some pages in Indico
    """
    _subDirName = ""

    def __init__( self, vars ):
        pass

    def getFileName( self ):
        return ""

    def lockCache( self, file, flag=True):
        global fp
        if flag:
            fp = open(file,"a")
            OSSpecific.lockFile(fp, 'LOCK_EX')
        else:
            if not fp:
                return
            OSSpecific.lockFile(fp, 'LOCK_UN')
            fp.close()
            fp = None

    def getCachePath( self ):
        path = os.path.join(Config.getInstance().getXMLCacheDir(),self._subDirName)
        if not os.path.exists(path):
            try:
                os.mkdir(path)
            except:
                pass
        return path

    def getFilePath( self ):
        return os.path.join(self.getCachePath(), self.getFileName())

    def cleanCache( self ):
        self.lockCache( self.getFilePath(), True )
        if os.path.exists( self.getFilePath() ):
            os.remove( self.getFilePath() )
        self.lockCache( self.getFilePath(), False )

    def cleanUpAllFiles( self ):
        """ removes an entire cache directory"""
        path = self.getCachePath()
        if os.path.exists(path):
            shutil.rmtree(path)

    def getCachePage( self ):
        if os.path.isfile(self.getFilePath()):
            fp = open(self.getFilePath(),"r")
            OSSpecific.lockFile(fp, 'LOCK_SH')
            page = fp.read()
            return page
        return ""

    def saveCachePage( self, page ):
        self.lockCache( self.getFilePath(), True )
        open(self.getFilePath(),"w").write( page )
        self.lockCache( self.getFilePath(), False )

class CategoryCache( IndicoCache ):
    _subDirName = "categories"

    def __init__( self, vars={} ):
        self._categId = vars.get("categId","")

    def getFileName( self ):
        return "cat-%s" % self._categId

class EventCache( IndicoCache ):
    _subDirName = "events"

    def __init__( self, vars={} ):
        self._eventId = vars.get("id","")
        self._type = vars.get("type", "")

    def getFileName( self ):
        return "eve-%s-%s" % (self._eventId, self._type)

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
        self._connect().set(self._makeKey(path, name), data, self.getTTL())

    def load(self, path, name, default=None):
        obj = self._connect().get(self._makeKey(path, name))
        return obj, None

    def remove(self, path, name):
        self._connect().delete(self._makeKey(path, name))


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
    A multilevel cache
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
