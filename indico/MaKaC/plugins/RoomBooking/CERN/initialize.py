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

"""
Initializes generic ZODB-based Room Booking database.
"""

from ZODB import FileStorage, DB
from ZODB.DB import DB, transaction
from ZODB.PersistentMapping import PersistentMapping
from persistent import Persistent
from BTrees.IOBTree import IOBTree
from BTrees.OOBTree import OOBTree

from MaKaC.common import info

from MaKaC.rb_location import RoomGUID, ReservationGUID, Location

from MaKaC.plugins.RoomBooking.CERN.equipmentManagerCERN import EquipmentManagerCERN
from MaKaC.plugins.RoomBooking.CERN.dalManagerCERN import DALManagerCERN
from MaKaC.plugins.RoomBooking.CERN.factoryCERN import FactoryCERN
import MaKaC
from MaKaC.user import AvatarHolder

def deleteRoomBookingBranches( force = False ):
    """
    !!! REMOVES DATA !!!
    
    Deletes all branches related to room booking,
    from both main and room booking databases.
    """
    if not force:
        raise 'nothing done'
    
    indicoRoot = MaKaC.common.DBMgr.getInstance().getDBConnection().root()
    root = DALManagerCERN().root
    minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
    
    # 1. INDICO -----------------------------------------

    minfo.setRoomBookingModuleActive( False )
    if indicoRoot.get( 'RoomBookingLocationList' ):
        del indicoRoot['RoomBookingLocationList']
    if indicoRoot.get( 'DefaultRoomBookingLocation' ):
        del indicoRoot['DefaultRoomBookingLocation']
    
    # 2. ROOM BOKING ------------------------------------

    if root.get( 'Rooms' ):
        del root['Rooms']
    if root.get( 'Reservations' ):
        del root['Reservations']
    
    # Create indexes
    if root.get( 'RoomReservationsIndex' ):
        del root['RoomReservationsIndex']
    if root.get( 'UserReservationsIndex' ):
        del root['UserReservationsIndex']

    # Create possible equipment branch
    if root.get( 'EquipmentList' ):
        del root['EquipmentList']

    DALManagerCERN().commit()

def initializeRoomBookingDB( location, force = False ):
    """
    Modifies Indico main database.
    - location list

    Creates necessary branches in room booking database.
    - rooms branch
    - bookings branch
    - several indexes
    """
    indicoRoot = MaKaC.common.DBMgr.getInstance().getDBConnection().root()
    root = DALManagerCERN().root
    
    # 1. Location -----------------------------------------------------------
    
    initialLocation = Location( location, FactoryCERN )
    if force or not indicoRoot.has_key( 'RoomBookingLocationList' ):
        indicoRoot['RoomBookingLocationList'] = [ initialLocation ]
        print "Locations branch created (Indico db)"
    if force or not indicoRoot.has_key( 'DefaultRoomBookingLocation' ):
        indicoRoot['DefaultRoomBookingLocation'] = location
        print "Default location set to " + location
    
    # 2. Rooms & Bookings ---------------------------------------------------

    # Create rooms branch
    if force or not root.has_key( 'Rooms' ):
        root['Rooms'] = IOBTree()
        print "Rooms branch created"

    # Create reservations branch
    if force or not root.has_key( 'Reservations' ):
        root['Reservations'] = IOBTree()
        print "Reservations branch created"
    
    # Create indexes
    if force or not root.has_key( 'RoomReservationsIndex' ):
        root['RoomReservationsIndex'] = OOBTree()
        print "Room => Reservations Index branch created"
    if force or not root.has_key( 'UserReservationsIndex' ):
        root['UserReservationsIndex'] = OOBTree()
        print "User => Reservations Index branch created"
    if force or not root.has_key( 'DayReservationsIndex' ):
        root['DayReservationsIndex'] = OOBTree()
        print "Day => Reservations Index branch created"

    # Create possible equipment branch
    if force or not root.has_key( 'EquipmentList' ):
        root['EquipmentList'] = {}
        print "Equipment branch created"

    AvatarHolder().invalidateRoomManagerIdList()
    print "Cached list of room managers invalidated"

    DALManagerCERN().commit()


def main( **kwargs ):
    location = kwargs.get( 'location', 'Universe' )
    
    from MaKaC.rb_factory import Factory
    from MaKaC.common.db import DBMgr
    DBMgr.getInstance().startRequest()
    Factory.getDALManager().connect()

    initializeRoomBookingDB( location, force = True )

    Factory.getDALManager().disconnect()
    DBMgr.getInstance().endRequest()


#def setAVCEmail_pwlodare( **kwargs ):
#    from MaKaC.rb_factory import Factory
#    from MaKaC.common.db import DBMgr
#    DBMgr.getInstance().startRequest()
#    dm = Factory.getDALManager()
#    dm.connect()
#
#    Location.setDefaultLocation( "CERN" )
#    Location.getDefaultLocation().insertAVCSupportEmail( 'pwlodare@cern.ch' )
#
#    dm.disconnect()
#    DBMgr.getInstance().endRequest()



if __name__ == '__main__':
    pass
    # Give it name of the first (initial) location!
    # Can NOT be changed later!
    #main( location = "CERN" )
