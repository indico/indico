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

import threading
from contextlib import contextmanager

from indico.core import config as Configuration
from indico.core.db import DBMgr
from MaKaC.rb_dalManager import DALManagerBase
from MaKaC.errors import MaKaCError
from MaKaC.common import info
from BTrees.IOBTree import IOBTree
from BTrees.OOBTree import OOBTree

from ZEO import ClientStorage
from ZODB.DB import DB
import transaction


@contextmanager
def dummyContextManager():
    yield


class DummyConnection():
    """
    Used so that we can use context managers for database connections
    without producing failures when RB is not active.
    Of course tis is not the ideal solution, but it's the best possible
    without changing the whole RB DB code.
    """
    def transaction(self):
        return dummyContextManager()


class DBConnection:

    def __init__(self, minfo):
        self.connection = None
        self.root = None

        self.storage = ClientStorage.ClientStorage(
            minfo.getRoomBookingDBConnectionParams(),
            username=minfo.getRoomBookingDBUserName(),
            password=minfo.getRoomBookingDBPassword(),
            realm=minfo.getRoomBookingDBRealm())
        self.db = DB(self.storage)

    def connect(self):
        if not self.isConnected():
            if DALManager.usesMainIndicoDB():
                self.connection = DBMgr.getInstance().getDBConnection()
            else:
                self.connection = self.db.open()
            self.root = self.connection.root()

    def isConnected(self):
        if not self.connection:
            return False
        return True

    def getRoot(self, name=""):
        if name == "":
            return self.root
        elif self.root != None:
            if name in self.root.keys() and self.root[name]:
                return self.root[name]
            else:
                # create the branch
                if name in ["Rooms", "Reservations"]:
                    self.root[name] = IOBTree()
                elif name in ["RoomReservationsIndex", "UserReservationsIndex",
                              "DayReservationsIndex", "RoomDayReservationsIndex"]:
                    self.root[name] = OOBTree()
                elif name in ["EquipmentList", "CustomAttributesList"]:
                    self.root[name] = {}
                else:
                    return None
                return self.root[name]
        else:
            raise MaKaCError("Cannot connect to the room booking database")

    def disconnect(self):
        if DALManager.usesMainIndicoDB():
            return
        if self.isConnected():
            self.connection.close()
            self.root = None
            self.connection = None

    def commit(self):
        if DALManager.usesMainIndicoDB():
            return
        if self.isConnected():
            self.connection.transaction_manager.get().commit()

    def rollback(self):
        if DALManager.usesMainIndicoDB():
            return
        if self.isConnected():
            self.connection.transaction_manager.get().abort()

    def sync(self):
        if DALManager.usesMainIndicoDB():
            return
        if self.isConnected():
            self.connection.sync()

    def pack(self, days=1):
        if DALManager.usesMainIndicoDB():
            return
        self.db.pack(days=days)

    def transaction(self):
        """
        Calls the ZODB context manager for the connection
        """
        return self.db.transaction()


class DALManager(DALManagerBase):
    """ ZODB specific implementation. """

    _instances = {}

    @staticmethod
    def usesMainIndicoDB():
        cfg = Configuration.Config.getInstance()
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        if cfg.getDBConnectionParams() == minfo.getRoomBookingDBConnectionParams():
            return True
        else:
            return False

    @staticmethod
    def getInstance(create=True):
        tid = threading._get_ident()
        instance = DALManager._instances.get(tid)

        if not instance and create:
            minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
            instance = DBConnection(minfo)
            DALManager._instances[tid] = instance
        return instance

    @staticmethod
    def isConnected():
        """
        Returns true if the current DALManager is connected
        """
        if DALManager.getInstance(create=False):
            return DALManager.getInstance().isConnected()
        else:
            return False

    @staticmethod
    def getRoot(name=""):
        return DALManager.getInstance().getRoot(name)

    @staticmethod
    def connect():
        DALManager.getInstance().connect()

    @staticmethod
    def disconnect():
        DALManager.getInstance().disconnect()

    @staticmethod
    def commit():
        DALManager.getInstance().commit()

    @staticmethod
    def rollback():
        DALManager.getInstance().rollback()

    @staticmethod
    def sync():
        DALManager.getInstance().sync()

    @staticmethod
    def pack(days=1):
        DALManager.getInstance().pack()

    @staticmethod
    def dummyConnection():
        return DummyConnection()
