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

from MaKaC.common import Configuration
from MaKaC.common.db import DBMgr
from MaKaC.rb_dalManager import DALManagerBase
from MaKaC.errors import MaKaCError
from MaKaC.common import db, info
from BTrees.IOBTree import IOBTree
from BTrees.OOBTree import OOBTree

from ZEO import ClientStorage
from ZODB.DB import DB
import transaction


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
                              "DayReservationsIndex"]:
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


class DALManager(DALManagerBase):
    """ ZODB specific implementation. """

    _instance = None

    @staticmethod
    def usesMainIndicoDB():
        cfg = Configuration.Config.getInstance()
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        if cfg.getDBConnectionParams() == minfo.getRoomBookingDBConnectionParams():
            return True
        else:
            return False

    @staticmethod
    def getInstance():
        if not DALManager._instance:
            minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
            DALManager._instance = DBConnection(minfo)
        if not DALManager._instance:
            raise "cannot open DB backend"
        return DALManager._instance

    @staticmethod
    def isConnected():
        """
        Returns true if the current DALManager is connected
        """
        return DALManager._instance.isConnected()

    @staticmethod
    def getRoot(name=""):
        return DALManager._instance.getRoot(name)

    @staticmethod
    def connect():
        DALManager.getInstance().connect()

    @staticmethod
    def disconnect():
        DALManager._instance.disconnect()

    @staticmethod
    def commit():
        DALManager._instance.commit()

    @staticmethod
    def rollback():
        DALManager._instance.rollback()

    @staticmethod
    def sync():
        DALManager._instance.sync()

    @staticmethod
    def pack(days=1):
        DALManager._instance.pack()
