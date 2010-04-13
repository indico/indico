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

class TheInstance:
    pass

# Version for ZEO.
class DALManager( DALManagerBase ):
    """ ZODB specific implementation. """

    _instance = None
    connection = None
    root = None

    @staticmethod
    def usesMainIndicoDB():
        cfg = Configuration.Config.getInstance()
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        if cfg.getDBConnectionParams() == minfo.getRoomBookingDBConnectionParams():
            return True
        else:
            return False
         
    @staticmethod
    def theInstance():
        if not DALManager._instance:
            DALManager._instance = TheInstance()
            minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
            DALManager._instance.storage = ClientStorage.ClientStorage( minfo.getRoomBookingDBConnectionParams(), username=minfo.getRoomBookingDBUserName(), password=minfo.getRoomBookingDBPassword(), realm=minfo.getRoomBookingDBRealm() )
            DALManager._instance.db = DB( DALManager._instance.storage ) # Should it be MaKaCDB( self._storage )?
        if not DALManager._instance:
            raise "cannot open DB backend"
        return DALManager._instance

    @staticmethod
    def isConnected():
        """
        Returns true if the current DALManager is connected
        """
        if not DALManager.connection:
            return False
        return True

    @staticmethod
    def getRoot(name=""):
        if name == "":
            return DALManager.root
        elif DALManager.root != None:
            if name in DALManager.root.keys() and DALManager.root[name]:
                return DALManager.root[name]
            else:
                # create the branch
                if name in ["Rooms","Reservations"]:
                    DALManager.root[name] = IOBTree()
                elif name in ["RoomReservationsIndex", "UserReservationsIndex", "DayReservationsIndex"]:
                    DALManager.root[name] = OOBTree()
                elif name in ["EquipmentList","CustomAttributesList"]:
                    DALManager.root[name] = {}
                else:
                    return None
                return DALManager.root[name]
        else:
            raise MaKaCError("Cannot connect to the room booking database")
            
    @staticmethod
    def connect():
        if not DALManager.isConnected():
            if DALManager.usesMainIndicoDB():
                DALManager.connection = DBMgr.getInstance().getDBConnection()
            else:
                DALManager.connection = DALManager.theInstance().db.open()
            DALManager.root = DALManager.connection.root()
        
    @staticmethod
    def disconnect():
        if DALManager.usesMainIndicoDB():
            return
        if DALManager.isConnected():
            DALManager.connection.close()
        DALManager.root = None
        DALManager.connection = None
    
    @staticmethod
    def commit():
        if DALManager.usesMainIndicoDB():
            return
        if DALManager.isConnected():
            DALManager.connection.transaction_manager.get().commit()
        
    @staticmethod
    def rollback():
        if DALManager.usesMainIndicoDB():
            return
        if DALManager.isConnected():
            DALManager.connection.transaction_manager.get().abort()

    @staticmethod
    def sync():
        if DALManager.usesMainIndicoDB():
            return
        if DALManager.isConnected():
            DALManager.connection.sync()

    @staticmethod
    def pack(days = 1):
        if DALManager.usesMainIndicoDB():
            return
        DALManager.theInstance().db.pack(days=days)
        
