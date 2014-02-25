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

"""This file contains the implementation of some classes dealing with the DB
    so it's usage is easier and more transparent to the rest of the application
"""
import os
import threading
import pkg_resources
from contextlib import contextmanager

from ZEO.ClientStorage import ClientStorage
import transaction

from indico.core.db.migration import MigratedDB

from MaKaC.consoleScripts.installBase import getIndicoInstallMode

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
    _instances = {}

    def __init__(self, hostname=None, port=None, max_disconnect_poll=30):
        # Please leave this import here, db.py is imported during installation process
        from indico.core import config as Configuration
        cfg = Configuration.Config.getInstance()

        if not hostname:
            hostname = cfg.getDBConnectionParams()[0]
        if not port:
            port = cfg.getDBConnectionParams()[1]

        self._storage = ClientStorage((hostname, port), username=cfg.getDBUserName(),
                                      password=cfg.getDBPassword(), realm=cfg.getDBRealm(),
                                      max_disconnect_poll=max_disconnect_poll)
        self._db = MigratedDB(self._storage)
        self._conn = threading.local()
        self._conn.conn = None

    @classmethod
    def getInstance(cls, *args, **kwargs):
        pid = os.getpid()
        if os.getpid() not in cls._instances:
            cls._instances[pid] = DBMgr(*args, **kwargs)
        return cls._instances[pid]

    @classmethod
    def setInstance(cls, dbInstance):
        if dbInstance is None:
            cls._instances.pop(os.getpid(), None)
        else:
            cls._instances[os.getpid()] = dbInstance

    def _getConnObject(self):
        return self._conn.conn

    def _setConnObject(self, obj):
        self._conn.conn = obj

    def _delConnObject(self):
        self._conn.conn = None

    def startRequest(self):
        """Initialise the DB and starts a new transaction.
        """
        self._conn.conn = self._db.open()

    def endRequest(self, commit=True):
        """Closes the DB and commits changes.
        """
        if commit:
            self.commit()
        else:
            self.abort()

        self._getConnObject().close()
        self._delConnObject()

    def getDBConnection(self):
        return self._getConnObject()

    def isConnected(self):
        return hasattr(self._conn, 'conn') and self._conn.conn is not None

    def getDBConnCache(self):
        conn = self._getConnObject()
        return conn._cache

    def getDBClassFactory(self):
        return self._db.classFactory

    def commit(self, sub=False):
        import StringIO
        import transaction._transaction
        transaction._transaction.StringIO = StringIO.StringIO
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

    def pack(self, days=1):
        self._storage.pack(days=days)

    def undoInfo(self, stepNumber=0):
        # One step is made of 1000 transactions. First step is 0 and returns
        # transactions 0 to 999.
        return self._db.undoInfo(stepNumber*1000, (stepNumber+1)*1000)

    def undo(self, trans_id):
        self._db.undo(trans_id)

    def getDBSize(self):
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

    @contextmanager
    def transaction(self, sync=False):
        """
        context manager (`with`)
        """
        if sync:
            self.sync()
        yield self.getDBConnection()
        self.commit()

    @contextmanager
    def global_connection(self, commit=False):
        """Helper if you NEED a connection and don't know if one is available or not.

        Useful e.g. in flask code that runs outside a request"""
        if self.isConnected():
            yield
        else:
            self.startRequest()
            try:
                yield
            finally:
                self.endRequest(commit)

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
