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

"""This file contains the implementation of some classes dealing with the DB
    so it's usage is easier and more transparent to the rest of the application
"""
import os
import sys
import threading
import pkg_resources

from ZEO.ClientStorage import ClientStorage
from ZODB.DB import DB
import transaction
import ZODB

from MaKaC.consoleScripts.installBase import getIndicoInstallMode
skip_imports = getIndicoInstallMode()

if not skip_imports:
    from MaKaC.common.logger import Logger
    from MaKaC.i18n import _

class MaKaCDB(DB):
    """Subclass of ZODB.DB necessary to remove possible existing dependencies
        from IC"""

    def classFactory(self, connection, modulename, globalname):
        if globalname=="PersistentMapping":
            modulename="persistent.mapping"
        elif globalname=="PersistentList":
            modulename="persistent.list"
        elif modulename.startswith("IndexedCatalog.BTrees."):
            modulename="BTrees.%s"%modulename[22:]
        return DB.classFactory(self, connection, modulename, globalname)



class DBMgr:
    """This class provides the access point to the Shelf (every client will
        use this class in order to obtain a shelf) and some mechanism to
        ensure there is only one connection opened to the DB during a single
        request.
        This class must not be instantiated, an instance can be obtained
        though the "getInstance" method (implements the singleton pattern
        to ensure unicity)
        Needs to be checked if the class (static) attribute _instance is
        thread-safe: as it is shared by all the objects of this class,
        it could provoke concurrency troubles having 2 threads using the db
        connection at the same time. However, the model under which we are
        programming is not multi-threaded (mod_python seems to run different
        interpreters for each apache subprocess, see mod_python doc section
        4.1) so this thechnique can be used. This has to be taken into account
        when migrating the system to a multi-threading environment.
    """
    _instance = None

    def __init__( self, hostname=None, port=None ):
        import Configuration # Please leave this import here, db.py is imported during installation process
        cfg = Configuration.Config.getInstance()

        if not hostname:
            hostname = cfg.getDBConnectionParams()[0]
        if not port:
            port = cfg.getDBConnectionParams()[1]

        self._storage=ClientStorage((hostname, port), username=cfg.getDBUserName(), password=cfg.getDBPassword(), realm=cfg.getDBRealm())
        self._db=MaKaCDB(self._storage)
        self._conn={}

    @classmethod
    def getInstance( cls, *args, **kwargs ):
        if cls._instance == None:
            Logger.get('dbmgr').debug('cls._instance is None')
            cls._instance=DBMgr(*args, **kwargs)
        return cls._instance

    def _getConnObject(self):
        tid=threading._get_ident()
        if self._conn.has_key(tid):
            return self._conn[tid]
        return None

    def _delConnObject(self):
        tid=threading._get_ident()
        del self._conn[tid]

    def startRequest( self ):
        """Initialise the DB and starts a new transaction.
        """

        conn = self._getConnObject()
        if conn is None:
            self._conn[threading._get_ident()]=self._db.open()
            Logger.get('dbmgr').debug('Allocated connection for thread %s - table size is %s' % (threading._get_ident(), len(self._conn)))
        else:
            Logger.get('dbmgr').debug('Reused connection for thread %s - table size is %s' % (threading._get_ident(), len(self._conn)))

    def endRequest( self, commit=True ):
        """Closes the DB and commits changes.
        """
        if commit:
            self.commit()
        else:
            self.abort()

        #modification vendredi 010907
#        try:
#            self._conn.close()
#            self._conn=None
#        except:
#            pass

        self._getConnObject().close()
        self._delConnObject()

    def getDBConnection( self ):
        conn = self._getConnObject()
        if conn == None:
            raise Exception( _("request not started"))
        return conn

    def isConnected( self ):
        if self._getConnObject() == None:
            return False
        else:
            return True

    def getDBConnCache(self):
        conn = self._getConnObject()
        if conn == None:
            raise Exception( _("request not started"))
        return conn._cache

    def getDBClassFactory(self):
        return self._db.classFactory

    def commit(self, sub=False):
        if (sub):
            transaction.savepoint()
        else:
            transaction.commit()

    def commitZODBOld(self, sub=False):
            transaction.commit(sub)

    def abort(self):
        transaction.abort()

    def sync(self):
        self._getConnObject().sync()

    def pack( self, days=1 ):
        self._storage.pack(days=days)

    def undoInfo(self, stepNumber=0):
        # One step is made of 1000 transactions. First step is 0 and returns
        # transactions 0 to 999.
        return self._db.undoInfo(stepNumber*1000, (stepNumber+1)*1000)

    def undo(self, trans_id):
        self._db.undo(trans_id)

    def getDBSize( self ):
        """Return an approximate size of the database, in bytes."""
        return self._storage.getSize()

    def loadObject(self, oid, version):
        return self._storage.load(oid, version)

    def storeObject(self, oid, serial, data, version, trans):
        return self._storage.store(oid, serial, data, version, trans)

    def tpcBegin(self, trans):
        self._storage.tpc_begin(trans)

    def tpcVote(self, trans):
        self._storage.tpc_vote(trans)

    def tpcFinish(self, trans):
        self._storage.tpc_finish(trans)

    # ZODB version check
    try:
        zodbPkg = pkg_resources.require('ZODB3')[0]
        zodbVersion = zodbPkg.parsed_version
        zodbVersion = (int(zodbVersion[0]), int(zodbVersion[1]))
    except pkg_resources.DistributionNotFound:
        # Very old versions, in which ZODB didn't register
        # with pkg_resources
        import ZODB
        zodbVersion = ZODB.__version__.split('.')

    if int(zodbVersion[0]) < 3:
        raise Exception("ZODB 3 required! %s found" % zodbPkg.version)
    elif int(zodbVersion[1]) < 7:
        commit = commitZODBOld


