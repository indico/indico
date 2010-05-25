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

import os, shutil, pickle, datetime


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

    def pickle(self):
        return pickle.dumps(self)

    def setContent(self, content):
        self.content = content

    def getContent(self):
        return self.content

    @classmethod
    def unpickle(self, data):
        return pickle.loads(data)



class MultiLevelCache(object):
    """
    A multilevel cache
    """

    __entryFactory = None

    def __init__(self, cacheName):

        self.cacheName = cacheName
        cacheDir = self.getCacheDir()

        if not os.path.exists(cacheDir):
            os.makedirs(cacheDir)

    def _saveObject(self, fsPath, path, fileName, data):
        """
        Performs the actual save operation
        """

        if len(path) == 0:
            filePath = os.path.join(fsPath, fileName)
            f = open(filePath, 'wb')
            OSSpecific.lockFile(f, 'LOCK_EX')
            f.write(data)
            OSSpecific.lockFile(f, 'LOCK_UN')
            f.close()
        else:
            dirPath = os.path.join(fsPath, path[0])

            if not os.path.exists(dirPath):
                os.makedirs(dirPath)

            self._saveObject(dirPath, path[1:], fileName, data)


    def getCacheDir(self):
        """
        Returns the directory where the cache is located
        Can be overriden by subclasses
        """
        return os.path.join(Config().getInstance().getXMLCacheDir(), self.cacheName)

    def cacheObject(self, version, content, *args):
        """
        Actually puts an object into the cache
        """

        entry = self._entryFactory.create(content, *args)

        path = self._generatePath(entry)

        fileName = self._generateFileName(entry, version)

        self._saveObject(self.getCacheDir(), path, fileName, entry.pickle())

        Logger.get('cache/%s' % self.cacheName).debug(
            "Saved %s" % (os.path.join(*(path + [fileName]))))

    def loadObject(self, version, *args):
        """
        Loads an object from the cache, returning None if it doesn't exist
        or in case it is dirty (has expired)
        """

        dummyEntry = self._entryFactory.create(None, *args)

        filePath = os.path.join(*([self.getCacheDir()] +
                                  self._generatePath(dummyEntry) +
                                  [self._generateFileName(dummyEntry, version)]))

        Logger.get('cache/%s'%self.cacheName).debug("Checking %s...", filePath)
        if os.path.isfile(filePath):
            # (Possible) Cache hit!
            # check dirty state first

            f = open(filePath, 'rb')

            # Lock file
            OSSpecific.lockFile(f, 'LOCK_SH')
            data = f.read()
            OSSpecific.lockFile(f, 'LOCK_UN')
            f.close()

            obj = MultiLevelCacheEntry.unpickle(data)

            if self.isDirty(filePath, obj):
                Logger.get('cache/%s'%self.cacheName).debug("DIRTY")
                # if the file is older, report a miss
                # os.remove(filePath)
                return None
            else:
                Logger.get('cache/%s'%self.cacheName).debug("HIT")
                return obj

        else:
            Logger.get('cache/%s'%self.cacheName).debug("MISS")
            # Cache miss!
            return None


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

    def isDirty(self, path, object):
        """
        Overload it, in order to define whether
        the entry has expired or not
        """
        raise Exception("this method should be overloaded")
