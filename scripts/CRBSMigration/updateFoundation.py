# -*- coding: utf-8 -*-
##
## $Id: updateFoundation.py,v 1.2 2008/04/24 17:00:30 jose Exp $
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
INSERT INTO TMP_MEETING_ROOMS
VALUES (
  %s, /* ID */
  %s, /* FRIENDLY_NAME */
  %s, /* SITE */
  %s, /* BUILDING */
  %s, /* FLOOR */
  %s, /* ROOM_NUMBER */
  %s, /* CAPACITY */
  %s, /* SURFACE */
  %s, /* DEPARTMENT */
  %s, /* TELEPHONE */
  %s, /* WHERE_IS_KEY */
  %s, /* COMMENTS */
  %s, /* RESPONSIBLE_ID */
  %s, /* RESPONSIBLE_EMAIL */
  %s /* IS_RESERVABLE */
);

"""
    sql = """/*
Script for updating foundation_pub.meeting_rooms
with data available in old CRBS.
*/

DELETE FROM TMP_MEETING_ROOMS;

"""
    print len( allRooms )
    for room in allRooms:
        id = str( room.building ) + '-' + str( room.floor ) + '-' + str( room.roomNr )
        friendly_name = 'Null'

        site = 'Null'
        building = str( room.building )
        floor = "'" + room.floor + "'"
        room_number = "' '"
        
        capacity = 'Null'
        surface = 'Null'
        department = 'Null'
        telephone = 'Null'
        where_is_key = 'Null'
        comments = 'Null'
        
        responsible_id = 'Null'
        responsible_email = ''
        is_reservable = "'Y'"

        if id != room.name: friendly_name = "'" + room.name + "'"
        if room.site: 
            if room.site == 'Meyrin': site = 'MEYR'
            if room.site == 'Prevessin': site = 'PREV'
            if room.site == 'LEP 6': site = 'L6'
            if room.site == 'Point 2': site = 'P2'
            site = "'" + site + "'"
        if room.roomNr: room_number = "'" + room.roomNr + "'"
        if room.capacity: capacity = str( room.capacity )
        if room.surfaceArea: surface = str( room.surfaceArea )
        if room.division: department = "'" + room.division + "'"
        if room.telephone: telephone = "'" + room.telephone + "'"
        if room.whereIsKey: where_is_key = "'" + room.whereIsKey + "'"
        if room.comments: comments = "'" + room.comments + "'"
        
        responsible_id = responsible_id     # Do nothing
        resp = room.getResponsible()
        if isinstance( resp, Avatar ): responsible_email = "'" + room.getResponsible().getEmail() + "'"
        else: responsible_email = "'" + room.getResponsible().name + "'"

        if room.isReservable: is_reservable = "'Y'"
        else: is_reservable = "'N'"
        
        sql += sql_pattern % ( "'" + id + "'",
                               friendly_name,
                               site,
                               building,
                               floor,
                               room_number,
                               capacity,
                               surface,
                               department,
                               telephone,
                               where_is_key,
                               comments,
                               responsible_id,
                               responsible_email,
                               is_reservable )

    f = open( r'E:\CRBS\foundation-update\foundation-meeting-rooms.sql', 'wb' )
    f.write( sql )
    f.close()


# -----------------------------------------------------------------------------
def sql4RoomEquipmentUpdate():
    activeRoom = RoomBase()
    activeRoom.isActive = True
    allRooms = RoomCERN.getRooms( roomExample = activeRoom )
    sqlPattern = """
INSERT INTO TMP_ROOM_EQUIPMENT 
VALUES ( '%s', '%s' ) ;
"""
    sql = """/*
Script for updating foundation_pub.rooms_equipment
with data available in old CRBS.
*/

DELETE FROM TMP_ROOM_EQUIPMENT;
"""
    for room in allRooms:
        eqList = room.getEquipment()
        if room.roomNr:
            room_number = room.roomNr
        else:
            room_number = ' '
        room_id = str( room.building ) + "-" + room.floor + "-" + room_number
        for eq in eqList:
            if eq in ['Video conference ISDN']: code = 'VI'
            if eq in ['Video conference H323', 'Video conference VRVS', 'Video conference Hermes']: code = 'VH'
            if eq in ['Video projector', 'Computer projector', 'Slide projector']: code = 'CP'
            if eq in ['Conference call line']: code = 'TC'
            if eq in ['Microphone']: code = 'MO'
            if eq in ['Wireless']: code = 'WC'
            if eq in ['Ethernet']: code = 'EC'
            if eq in ['PC']: code = 'PC'
            if eq in ['Blackboard']: code = 'BO'
            sql += sqlPattern % ( room_id, code )

    print sql
    f = open( r'E:\CRBS\foundation-update\foundation-room-equipment.sql', 'wb' )
    f.write( sql )
    f.close()



# -----------------------------------------------------------------------------
def main():
    """
    Creates SQL scripts to update Foundation DB.
    """
    connect2IndicoDB()
    
    sql4RoomsUpdate()
    #sql4RoomEquipmentUpdate()
    
    disconnectFromIndicoDB()

if __name__ == '__main__':
    main()
