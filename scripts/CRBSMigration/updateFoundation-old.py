# -*- coding: utf-8 -*-
##
## $Id: updateFoundation-old.py,v 1.2 2008/04/24 17:00:30 jose Exp $
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
USED ONLY ONCE: FOR MIGRATION BETWEEN OLD AND NEW CRBS

Generates SQL scripts which update Foundation database
with CRBS-specific data.
"""

from MaKaC.rb_reservation import RepeatabilityEnum, WeekDayEnum
from MaKaC.rb_room import RoomBase
from MaKaC.rb_crbsUser import CrbsUserBase
from MaKaC.rb_equipmentManager import EquipmentManagerBase
from MaKaC.user import AvatarHolder, Avatar, GroupHolder

from ZODB import FileStorage, DB
from ZODB.DB import DB, transaction
from ZODB.PersistentMapping import PersistentMapping
from persistent import Persistent
from BTrees.IOBTree import IOBTree
from BTrees.OOBTree import OOBTree

import mx.ODBC.Windows as mx
from datetime import datetime

from MaKaC.rb_location import RoomGUID, ReservationGUID, Location

from MaKaC.plugins.RoomBooking.CERN.equipmentManagerCERN import EquipmentManagerCERN
from MaKaC.plugins.RoomBooking.CERN.roomCERN import RoomCERN
from MaKaC.plugins.RoomBooking.CERN.reservationCERN import ReservationCERN
from MaKaC.plugins.RoomBooking.CERN.dalManagerCERN import DALManagerCERN

from tools import connect2IndicoDB, disconnectFromIndicoDB

# -----------------------------------------------------------------------------
def sql4RoomsUpdate():
    activeRoom = RoomBase()
    activeRoom.isActive = True
    allRooms = RoomCERN.getRooms( roomExample = activeRoom )
    sql_pattern = """
UPDATE foundation_pub.meeting_rooms
SET 
  FRIENDLY_NAME = %s,
  CAPACITY = %s,
  TELEPHONE = %s,
  WHERE_IS_KEY = %s,
  COMMENTS = %s,
  RESPONSIBLE_EMAIL = %s,
  IS_RESERVABLE = %s
WHERE ID = %s;

"""
    sql = """
/*
Script for updating foundation_pub.meeting_rooms
with data available in old CRBS.
*/
"""
    for room in allRooms:
        friendly_name = 'Null'
        capacity = 'Null'
        telephone = 'Null'
        where_is_key = 'Null'
        comments = 'Null'
        responsible_email = ''
        is_reservable = ''
        id = "'" + room.name + "'"

        s = str( room.building ) + '-' + str( room.floor ) + '-' + str( room.roomNr )
        if s != room.name:
            friendly_name = "'" + room.name + "'"
        if room.capacity:
            capacity = str( room.capacity )
        if room.telephone:
            telephone = "'" + room.telephone + "'"
        if room.whereIsKey:
            where_is_key = "'" + room.whereIsKey + "'"
        if room.comments:
            comments = "'" + room.comments + "'"
        
        resp = room.getResponsible()
        if isinstance( resp, Avatar ):
            responsible_email = "'" + room.getResponsible().getEmail() + "'"
        else:
            responsible_email = "'" + room.getResponsible().name + "'"
        if room.isReservable:
            is_reservable = 'Y'
        else:
            is_reservable = 'N'
        
        sql += sql_pattern % ( friendly_name,
                               capacity,
                               telephone,
                               where_is_key,
                               comments,
                               responsible_email,
                               is_reservable,
                               id )

    print sql
    f = open( r'E:\CRBS\foundation-update\foundation-meeting-rooms-update.sql', 'wb' )
    f.write( sql )
    f.close()


# -----------------------------------------------------------------------------
def sql4EquipmentUpdate():

    sql = """
/*
Deletes unnecessary / redundant / old equipment:
        'Macintosh Connection'
        'Film projector'
        'Overhead Projector'
        'Workstation Connection'
        'Translation'
*/
DELETE FROM foundation_pub.equipment
WHERE ID IN ( 'MC', 'FP', 'OP', 'SC', 'TO' );

/*
Deletes 
*/
"""
    
    print sql
    f = open( r'E:\CRBS\foundation-update\foundation-equipment-update.sql', 'wb' )
    f.write( sql )
    f.close()


# -----------------------------------------------------------------------------
def sql4RoomsEquipmentUpdate():
    activeRoom = RoomBase()
    activeRoom.isActive = True
    allRooms = RoomCERN.getRooms( roomExample = activeRoom )
    sqlPattern = """
INSERT INTO foundation_pub.room_equipment 
VALUES ( '%s', '%s' ) ;
"""
    sql = """
/*
Script for updating foundation_pub.rooms_equipment
with data available in old CRBS.
*/
"""
    for room in allRooms:
        eqList = room.getEquipment()
        for eq in eqList:
            if eq == '': code = ''
            # ...
            sql += sqlPattern % ( room.name, code )

    print sql
    f = open( r'E:\CRBS\foundation-update\foundation-rooms-equipment-update.sql', 'wb' )
    f.write( sql )
    f.close()



# -----------------------------------------------------------------------------
def main():
    """
    Creates SQL scripts to update Foundation DB.
    """
    connect2IndicoDB()
    
    sql4RoomsUpdate()
    sql4EquipmentUpdate()
    sql4RoomsEquipmentUpdate()
    
    disconnectFromIndicoDB()

if __name__ == '__main__':
    main()
