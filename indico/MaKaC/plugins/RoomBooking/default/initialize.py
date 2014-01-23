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
from MaKaC.common.indexes import CalendarDayIndex

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

from MaKaC.rb_room import RoomBase
from MaKaC.rb_location import RoomGUID, ReservationGUID, Location

from MaKaC.plugins.RoomBooking.CERN.equipmentManagerCERN import EquipmentManagerCERN
from MaKaC.plugins.RoomBooking.CERN.dalManagerCERN import DALManagerCERN
from MaKaC.plugins.RoomBooking.CERN.factoryCERN import FactoryCERN

from indico.core.index import Catalog
from indico.core.db import DBMgr


def deleteRoomBookingBranches( force = False ):
    """
    !!! REMOVES DATA !!!

    Deletes all branches related to room booking,
    from both main and room booking databases.
    """
    if not force:
        raise Exception('nothing done')

    indicoRoot = DBMgr.getInstance().getDBConnection().root()
    root = DALManagerCERN().getRoot()
    minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()

    # 1. INDICO -----------------------------------------

    minfo.setRoomBookingModuleActive( False )
    if indicoRoot.get( 'RoomBookingLocationList' ):
        del indicoRoot['RoomBookingLocationList']
    if indicoRoot.get( 'DefaultRoomBookingLocation' ):
        del indicoRoot['DefaultRoomBookingLocation']

    # 2. ROOM BOOKING ------------------------------------

    if root.get( 'Rooms' ):
        del root['Rooms']
    if root.get( 'Reservations' ):
        del root['Reservations']
    if root.get( 'RoomBlocking' ):
        del root['RoomBlocking']

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
    indicoRoot = DBMgr.getInstance().getDBConnection().root()
    root = DALManagerCERN().getRoot()
    # 1. Location -----------------------------------------------------------

    initialLocation = Location( location, FactoryCERN )
    if force or not indicoRoot.has_key( 'RoomBookingLocationList' ):
        indicoRoot['RoomBookingLocationList'] = [ initialLocation ]
    if force or not indicoRoot.has_key( 'DefaultRoomBookingLocation' ):
        indicoRoot['DefaultRoomBookingLocation'] = location

    # 2. Rooms & Bookings ---------------------------------------------------

    # Create rooms branch
    if force or not root.has_key( 'Rooms' ):
        root['Rooms'] = IOBTree()

    # Create reservations branch
    if force or not root.has_key( 'Reservations' ):
        root['Reservations'] = IOBTree()

    # Create blocking branch
    if force or not root.has_key( 'RoomBlocking' ):
        root['RoomBlocking'] = OOBTree()
        root['RoomBlocking']['Blockings'] = IOBTree()
        root['RoomBlocking']['Indexes'] = OOBTree()
        root['RoomBlocking']['Indexes']['OwnerBlockings'] = OOBTree()
        root['RoomBlocking']['Indexes']['DayBlockings'] = CalendarDayIndex()
        root['RoomBlocking']['Indexes']['RoomBlockings'] = OOBTree()

    # Create indexes
    if force or not root.has_key( 'RoomReservationsIndex' ):
        root['RoomReservationsIndex'] = OOBTree()
    if force or not root.has_key( 'UserReservationsIndex' ):
        root['UserReservationsIndex'] = OOBTree()
    if force or not root.has_key( 'DayReservationsIndex' ):
        root['DayReservationsIndex'] = OOBTree()
    if force or not root.has_key( 'RoomDayReservationsIndex' ):
        root['RoomDayReservationsIndex'] = OOBTree()

    # Create possible equipment branch
    if force or not root.has_key( 'EquipmentList' ):
        root['EquipmentList'] = {}

    # update Catalog with new rb indexes
    Catalog.updateDB()

    DALManagerCERN().commit()


def main( **kwargs ):
    location = kwargs.get( 'location', 'Universe' )

    from MaKaC.rb_factory import Factory
    from indico.core.db import DBMgr
    DBMgr.getInstance().startRequest()
    Factory.getDALManager().connect()

    initializeRoomBookingDB( location, force = True )

    Factory.getDALManager().disconnect()
    DBMgr.getInstance().endRequest()
