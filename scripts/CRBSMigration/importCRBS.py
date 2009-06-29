# -*- coding: utf-8 -*-
##
## $Id: importCRBS.py,v 1.6 2008/04/24 17:00:30 jose Exp $
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

Imports old CRBS data from the Oracle database.
Requirements:
- mxODBC Python library and all its sub-requirements
- ODBC DSN called cern-crbs (configured to point Oracle database)
"""

from MaKaC.rb_reservation import RepeatabilityEnum, WeekDayEnum, ReservationBase
from MaKaC.rb_room import RoomBase
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

from MaKaC.rb_location import RoomGUID, ReservationGUID, Location, CrossLocationQueries

from MaKaC.plugins.RoomBooking.CERN.equipmentManagerCERN import EquipmentManagerCERN
from MaKaC.plugins.RoomBooking.CERN.roomCERN import RoomCERN
from MaKaC.plugins.RoomBooking.CERN.reservationCERN import ReservationCERN
from MaKaC.plugins.RoomBooking.CERN.dalManagerCERN import DALManagerCERN

from tools import connect2IndicoDB, disconnectFromIndicoDB


def to_datetime( mxdt ):
#    datetime(year, month, day[, hour[, minute[, second[, microsecond[,tzinfo]]]]])    
    return datetime( mxdt.year, mxdt.month, mxdt.day, mxdt.hour, mxdt.minute, mxdt.second )

def parse1stEmail( s ):
    emails = s.split( ',' )
    if len( emails ) == 1:
        emails = s.split()
    return emails[0]

# -----------------------------------------------------------------------------
def preparePossibleEquipment():
    """ Creates CERN-specific list of possible equipment in rooms. """
    
    cernEquipment = [
        'Video projector',
        'Computer projector',
        'Slide projector',
        'Video conference ISDN',
        'Video conference H323',
        'Video conference VRVS',
        'Video conference Hermes',
        'Conference call line',
        'PC',
        'Blackboard',
        'Wireless',
        'Ethernet',
        'Microphone', # Redundant?
        ]
    cernEquipmentNew = [
        'Blackboard',
        'PC',
        'Ethernet',
        'Wireless',
        'Microphone',
        'Computer Projector',
        'Telephone conference capability',             # Rename: Conference calls
        'Video conference over ISDN',
        'Video conference over IP (H323 or VRVS/EVO)', # Merged with VRVS
        ]
    
    EquipmentManagerCERN.setPossibleEquipment( cernEquipment )
    DALManagerCERN().commit()

# -----------------------------------------------------------------------------
def importUsers( oracle ):
    """ 
    In fact, this function is only to ensure that every 
    CRBS Responsible is now Indico user ("Avatar"), so
    we can assign him/her rooms in the rooms import routine.
    """

    print "Importing users"
    c = oracle.cursor()
    c.execute( 'SELECT * FROM CRRES ORDER BY RESCRRES' )

    counter = counterSkipped = 0
    while True:
        row = c.fetchone()
        if row == None: break

        # Avatar fetch/creation and update
        
        # 1. Take first e-mail from the column
        id = row[0]
        email = parse1stEmail( row[3] )
        if email == 'It.Secretariat@cern.ch':
            email = 'Yasemin.Hauser@cern.ch'
        if email in [ 'ph-abs-secretariat-regional-bldg-13@cern.ch', 'Brigitte.Pillionnel@cern.ch' ]:
            email = 'Suzanne.Barras@cern.ch' #'Piotr.Michal.Wlodarek@cern.ch'
        print "\nAsking NICE for email: " + email

        # 2. Find existing NICE or Indico account
        list = AvatarHolder().match( { 'email': email } )
#        if len( list ) == 0:
#            print "Possibly SIMBA/group, add '-members' and ask again"
#            tmp = email.split( '@' )
#            email = tmp[0] + '-members@' + tmp[1] 
#            list = GroupHolder().match( { 'name':email } )
#            #raise str( email ) + str( list )
        
        if len( list ) == 0:
            print "No NICE account for email: " + email
            #print "No NICE account for user CRBS_ID = %d, EMAIL= %s, responsible for room %s" % (id, email, room.name)
            counterSkipped += 1
            continue 
        
        avatar = list[0]
        if avatar.id.startswith( 'Nice:' ):
            print avatar.id + "  -> Found NICE account for email: " + email
            print "=> creating Indico account"
            #avatar.id = ""
            #id = AvatarHolder().add( avatar )
            
            # Create Indico account using getById method :)
            av = AvatarHolder().getById( avatar.id )
        else:
            print avatar.id + "  -> Found Indico account for email: " + email
            print "=> doing nothing"
        
        counter += 1
        
    print "Imported %d users." % counter
    print "Skipped %d users because they have no NICE account." % counter

# -----------------------------------------------------------------------------
def importRooms( oracle ):
    """ Imports rooms (CRROM) from the old CRBS """
    
    root = DALManagerCERN().root
    if True or not root.has_key( 'Rooms' ):
        root['Rooms'] = IOBTree()
    
    c = oracle.cursor()
    c.execute( 'SELECT * FROM CRROM ORDER BY IDNCRROM' )

    counter = counterSkipped = 0
    while True:
        row = c.fetchone()
        if row == None: break

        room = RoomCERN()

        room.locationName = 'CERN'
        room.id = int( row[0] )
        # Skip 9 rooms that have ghost responsible.
        # Ghost responsible is the one I cannot find in NICE (neither as user nor as group).
        # All these rooms are active but not reservable (only IDN==72 is I/NOT).
        if room.id in ( 82, 23, 37, 38, 104, 70, 71, 72, 73, 57 ):
            continue
        room.photoId = 'B' + str( room.id )
        room.site = row[1]
        room.building = int( row[2] )
        room.floor = row[3]
        room.roomNr = row[4]
        room.division = row[5]
        #room.group = row[6]
        #room.section = row[7]
        if row[8][0].isalpha():
            room.name = row[8]
        room.externalId = int( row[9] )
        #? typcrrom = row[10]
        # concrrom = row[11]  assign responsible person
        room.isReservable = ( row[12] == None )
        if row[13] != None:
            room.surfaceArea = int( round( row[13] ) )
        room.capacity = int( row[14] )
        room.telephone = row[15]
        #ohp = row[16]
        #co2 = row[17]
        #co3 = row[18]
        room.comments = row[30]
        room.whereIsKey = row[35]

        # Equipment

        row = dict(zip([d[0] for d in c.description], row))
        if row['VIPCRROM'] != None: room.insertEquipment( 'Video projector' )
        if row['CDVCRROM'] != None: room.insertEquipment( 'Video conference ISDN' )
        if row['PKVCRROM'] != None: room.insertEquipment( 'Video conference VRVS' )
        if row['IPVCRROM'] != None: room.insertEquipment( 'Video conference H323' )
        if row['TECCRROM'] != None: room.insertEquipment( 'Conference call line' )
        if row['PCCCRROM'] != None: room.insertEquipment( 'PC' )
        if row['BLBCRROM'] != None: room.insertEquipment( 'Blackboard' )
        if row['WLNCRROM'] != None: room.insertEquipment( 'Wireless' )
        if row['MICCRROM'] != None: room.insertEquipment( 'Microphone' )
        if row['ETHCRROM'] != None: room.insertEquipment( 'Ethernet' )
        if row['COPCRROM'] != None: room.insertEquipment( 'Computer projector' )
        if row['SLPCRROM'] != None: room.insertEquipment( 'Slide projector' )



        # Responsibility issue...
        if row['CONCRROM'] != None: 
            responsibleId = int( row['CONCRROM'] )
            d = oracle.cursor()
            d.execute( 'SELECT * FROM CRRES WHERE RESCRRES = %d' % responsibleId )
            r = d.fetchone()
            if r == None:
                print "ERROR in OLD CRBS: can not find responsible [%d] for room [%s] - SKIPPING ROOM" % ( responsibleId, room.name )
                counterSkipped += 1
                continue # Next room
            
            email = parse1stEmail( r[3] )
            if email in [ 'It.Secretariat@cern.ch' ]:
                # She is doing this all the time except for holidays
                email = 'Yasemin.Hauser@cern.ch'
            if email in [ 'ph-abs-secretariat-regional-bldg-13@cern.ch' ]:
                email = 'Suzanne.Barras@cern.ch'
            if email in [ 'Brigitte.Pillionnel@cern.ch' ]:
                # I will make myself temporarily responsible for 
                # several rooms of this strange lady Brigitte Pillionnel.
                email = 'Piotr.Michal.Wlodarek@cern.ch'
            avatars = AvatarHolder().match( { 'email': email } )
#            if len( avatars ) == 0:
#                tmp = email.split( '@' )
#                email = tmp[0] + '-members@' + tmp[1] 
#                avatars = GroupHolder().match( { 'name':email } )
            if len( avatars ) == 0:
                print "ERROR in NEW CRBS: no NICE account for [%s] resp. for room [%s] - SKIPPING ROOM" % ( email, room.name )
                counterSkipped += 1
                continue # Next room
            
            # Assign room to the Indico user
            avatar = avatars[0]

            room.responsibleId = str( avatar.id )
            print "Responsibility: %s  -  %s ( %s )" % (room.name, avatar.getFullName(), avatar.getEmail() )
        else:
            print room.name + " - does not have person responsible(!!) - SKIPPING"
            continue

        room.isActive = (row['STSCRROM'].upper() == 'A')

        room.insert()
        counter += 1

    DALManagerCERN().commit()
    print "%d rooms imported" % counter
    print "%d rooms skipped" % counterSkipped



# -----------------------------------------------------------------------------
def importReservations( oracle, prebookings = False, force = False ):
    """ Imports reservations (CRBOK) from the old CRBS """

    # How to translate repetitions
    rep2rep = [
        None,
        RepeatabilityEnum.daily,
        RepeatabilityEnum.onceAWeek,
        RepeatabilityEnum.onceEvery2Weeks,
        RepeatabilityEnum.onceEvery3Weeks,
        RepeatabilityEnum.onceAMonth,
        None, #RepeatabilityEnum.saturaday,
        None, #RepeatabilityEnum.sunday,
        None #RepeatabilityEnum.cern_holiday,
    ]
    
    nowDT = datetime.now()

    root = DALManagerCERN().root
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
    
    c = oracle.cursor()
    if not prebookings: 
        c.execute( "SELECT * FROM CRBOK WHERE DAYCRBOK >= '01-JAN-2005' AND ROMCRBOK IN (146,147,148,149) ORDER BY IDXCRBOK" )
    else:
        c.execute( "SELECT * FROM CRREQ WHERE DAYCRBOK >= '01-JAN-2005'  AND ROMCRBOK IN (146,147,148,149) AND SIXCRBOK = 0 AND STSCRBOK = 'A' ORDER BY IDXCRBOK" )

    counter = 0
    checked = 0
    counterWithExcluded = 0
    counterCancelled = 0
    excludedDays = 0
    while True:
        row = c.fetchone()
        checked += 1
        if checked % 1000 == 0:
            print "Checked  so far:  ", str( checked )
            print "Imported so far: ", str( counter )
        if row == None: 
            break
        row = dict(zip([d[0] for d in c.description], row))
        
        # Skip repeatings (they are 100% redundant)
        if int( row['PIDCRBOK'] ) != int( row['IDXCRBOK'] ):
            continue
        
        # Skip reservations that are already in db.
#        if ReservationCERN.getReservations( resvID = int( row['IDXCRBOK'] ) ) != None:
#            continue

        r = ReservationCERN()
#        r.id = int( row['IDXCRBOK'] )
        
        # find the room
        room = None
        c3 = oracle.cursor()
        c3.execute( 'SELECT * FROM CRROM WHERE IDNCRROM = %d' % int( row['ROMCRBOK'] ) )
        roomRow = c3.fetchone()
        if roomRow != None:
            if int( row['ROMCRBOK'] ) == 166: # ZONE BAR B Q special treatment
                room = RoomCERN.getRooms( roomName = "ZONE BAR B Q" )
            else:
                if roomRow[2] != None  and  roomRow[3] != None  and  roomRow[4] != None:
                    roomEx = RoomBase()
                    roomEx.building = int( roomRow[2] )
                    roomEx.floor = str( roomRow[3] )
                    roomEx.roomNr = str( roomRow[4] )
                    rooms = RoomCERN.getRooms( roomExample = roomEx )
                    print str( roomEx.name ) + " => number of matching rooms: " + str( len( rooms ) )
                    if len( rooms ) == 1:
                        room = rooms[0]
                        print str( room.name )
                    if len( rooms ) > 1:
                        if rooms[0].name == '40-2-A01':
                            room = rooms[0]
                        else:
                            print "RETURNED str( len( rooms ) ) ROOMS, BUT SHOULD BE 0 OR 1:"
                            print str( rooms[0] ) + str( rooms[1] )
                
        c3.close()
        if not room:
            print "Room %s not found - skipping reservation" % (int( row['ROMCRBOK'] ))
            continue
        
        r.room = room
        r.isConfirmed = not prebookings
        
#        if row['BOBCRBOK'] != None:
#            r.createdBy = str( row['BOBCRBOK'] )
        r.createdBy = None
        if row['BOFCRBOK'] != None:
            r.bookedForName = str( row['BOFCRBOK'] )
        if row['EMLCRBOK'] != None:
            r.contactEmail = str( row['EMLCRBOK'] )
        if row['TELCRBOK'] != None:
            r.contactPhone = str( int( row['TELCRBOK'] ) )
        r.startDT = to_datetime( row['STDCRBOK'] )
        
        #find the end date (it's in another row!)
        c2 = oracle.cursor()
        if not prebookings:
            c2.execute( "SELECT * FROM CRBOK WHERE PIDCRBOK = %d  AND ROMCRBOK  IN (146,147,148,149)  ORDER BY SIXCRBOK DESC" % int( row['IDXCRBOK'] ) )
        else:
            c2.execute( "SELECT * FROM CRREQ WHERE PIDCRBOK = %d  AND ROMCRBOK  IN (146,147,148,149)  AND STSCRBOK = 'A' ORDER BY SIXCRBOK DESC" % int( row['IDXCRBOK'] ) )
        lastRow = c2.fetchone()
        r.endDT = to_datetime( lastRow[9] )
        c2.close()

        # Skip archival (pre-)reservataions
        if r.endDT < datetime( 2007, 05, 10 ): #nowDT:
            continue

        #r.isActive = row['STSCRBOK'].upper == 'A'
        # Skip "I" - archival
        #if row['STSCRBOK'] == 'I':
        #    continue
        r.isCancelled = False #( row['STSCRBOK'] == 'C' )
        r.isRejected = False
    
        r.createdDT = to_datetime( row['DAYCRBOK'] )
        if row['REPCRBOK'] != None: 
            r.repeatability = rep2rep[ int( row['REPCRBOK'] ) ]
        if row['WHYCRBOK'] != None:
            r.reason = row['WHYCRBOK']
        #r.cab = row['CABCRBOK'] ? 
        #r.cad = row['CADCRBOK'] ? # Date of cancellation?

        # Exclude days that does not have a row
        c4 = oracle.cursor()
        if not prebookings:
            c4.execute( "SELECT * FROM CRBOK WHERE PIDCRBOK = %d  AND ROMCRBOK  IN (146,147,148,149)  ORDER BY SIXCRBOK ASC" % int( row['IDXCRBOK'] ) )
        else:
            c4.execute( "SELECT * FROM CRREQ WHERE PIDCRBOK = %d  AND ROMCRBOK  IN (146,147,148,149)  AND STSCRBOK = 'A' ORDER BY SIXCRBOK ASC" % int( row['IDXCRBOK'] ) )
        # Find real repeatings
        realRepeatings = []
        while True:
            rep_row = c4.fetchone()
            if rep_row == None:
                break
            rep_row = dict(zip([d[0] for d in c4.description], rep_row))
            if rep_row['STSCRBOK'] != 'C':
                realRepeatings.append( to_datetime( rep_row['STDCRBOK'] ).date() )
        c4.close()
        # Find computed (theoretical repeatings)
        computedRepeatings = [ period.startDT.date() for period in r.splitToPeriods() ]
        # Exclude not real
        if len( realRepeatings ) == 0:
            r.isCancelled = True
            counterCancelled += 1
            #print "Found cancelled reservation, [%d]" % ( counterCancelled )
            continue # SKIP Cancelled
        else:
            thereWhereExcludedDays = False
            for repeating in computedRepeatings:
                if not repeating in realRepeatings:
                    #print "Excluded " + str( repeating ) + " from booking PID=" + str( int( row['IDXCRBOK'] ) )
                    excludedDays += 1
                    r.excludeDay( repeating )
                    thereWhereExcludedDays = True
            if thereWhereExcludedDays:
                counterWithExcluded += 1

        r.insert()
        counter = counter + 1

    DALManagerCERN().commit()
    if not prebookings:
        print "Imported %d reservations" % ( counter )
        print "- Reservations with excluded days: " + str( counterWithExcluded )
        print "-- Excluded days: " + str( excludedDays )
        print "Skipped %d cancelled reservations" % ( counterCancelled )
    else:
        print "Imported %d PRE-reservations" % ( counter )
        print "- PRE-Reservations with excluded days: " + str( counterWithExcluded )
        print "-- Excluded days: " + str( excludedDays )
        print "Skipped %d cancelled PRE-reservations" % ( counterCancelled )

# -----------------------------------------------------------------------------
def removeNonExistingPhotos():
    from datetime import datetime

    nullImages = [ 2, 165, 169, 84, 131, 168, 133, 23, 170, 158, 171, 160, 161, 176, 137, 8, 104, 105, 59, 162, 113, 114, 72, 159, 173, 74, 167, 163, 175, 174, 156, 177 ]
                 #[165, 169, 131, 133, 170, 171, 160, 176, 8, 159, 173, 74, 167, 177, 175, 174, 156]
    for ni in nullImages:
        room = RoomCERN.getRooms( roomID = ni )
        if room != None:
            room.photoId = None
            room.update()

    print "Removing non existing photos done."

# -----------------------------------------------------------------------------
def main():
    # Connect to databases
    oracleDB = mx.DriverConnect( 'DSN=cern-crbs;UID=cr;PWD=amph9' )
    connect2IndicoDB()

    # Import
    Location.setDefaultLocation( "CERN" )
    preparePossibleEquipment()
    #importUsers( oracleDB )
    #importRooms( oracleDB )
    removeNonExistingPhotos()
    importReservations( oracleDB )

    # Close databases
    oracleDB.close()
    disconnectFromIndicoDB()

# -----------------------------------------------------------------------------
#def renamePhotos( oracle ):
#    """ Delete me after use """
#    
#    import os
#    IMAGE_PATH = r"E:/Indico/code/resources/images/"
#    
#    c = oracle.cursor()
#    c.execute( 'SELECT * FROM CRROM ORDER BY IDNCRROM' )
#
#    counter = counterSkipped = 0
#    while True:
#        row = c.fetchone()
#        if row == None: break
#
#        id = int( row[0] )
#        # Skip 9 rooms that have ghost responsible.
#        # Ghost responsible is the one I cannot find in NICE (neither as user nor as group).
#        # All these rooms are active but not reservable (only IDN==72 is I/NOT).
#        if id in ( 82, 23, 37, 38, 104, 70, 71, 72, 73, 57 ):
#            continue
#        photoId = 'B' + str( id ) + ".jpg"
#        site = row[1]
#        building = int( row[2] )
#        floor = row[3]
#        roomNr = row[4]
#
#        photoNewId = str( building ) + "-" + str( floor ) + "-" + str( roomNr ) + ".jpg"
#
#        # Large
##        old = IMAGE_PATH + "rooms/" + photoId
##        new = IMAGE_PATH + "rooms/" + photoNewId
##        print "Renaming:"
##        print old + "  =>  " + new
##        try:
##            os.rename( old, new )
##            print "^ OK"
##        except Exception, e:
##            print str( e )
#
#        # Small
#        old = IMAGE_PATH + "rooms-small/" + photoId
#        new = IMAGE_PATH + "rooms-small/" + photoNewId
#        print "Renaming:"
#        print old + "  =>  " + new
#        try:
#            os.rename( old, new )
#            print "^ OK"
#        except Exception, e:
#            print str( e )
#
#        
#        counter += 1
#
#    print "%d rooms imported" % counter
#    print "%d rooms skipped" % counterSkipped



def test():
    oracleDB = mx.DriverConnect( 'DSN=cern-crbs;UID=cr;PWD=amph9' )
    connect2IndicoDB()
    
    from MaKaC.plugins.RoomBooking.CERN.equipmentManagerCERN import EquipmentManagerCERN
    from MaKaC.plugins.RoomBooking.CERN.Migration.synchronizeWithFoundation import synchronizeRooms, synchronizeEquipment, synchronizeRoomsEquipment

    synchronizeEquipment( oracleDB )
    eq = EquipmentManagerCERN.getPossibleEquipment()
    print str( eq )
    
    disconnectFromIndicoDB()
    oracleDB.close()

def getResponsibleEmails():
    connect2IndicoDB()
    
    rooms = RoomCERN.getRooms()
    print "Rooms: " + str( len( rooms ) )
    emailsTmp = [ r.getResponsible().getEmail() for r in rooms ]
    emails = []
    for e in emailsTmp:
        if not e in emails:
            emails.append( e )
    emails.sort()
    print "Emails: " + str( len( emails ) )
    print ', '.join( emails )
    
    disconnectFromIndicoDB()

def createUserReservationsIndex():
    connect2IndicoDB()
    root = DALManagerCERN().root
    root['UserReservationsIndex'] = OOBTree()
    disconnectFromIndicoDB()

def addLocationName_2_Rooms():
    connect2IndicoDB()
    rooms = RoomCERN.getRooms()
    for r in rooms:
#        print r.name + " ==> " + r.locationName
        r.locationName = 'CERN'
    disconnectFromIndicoDB()

def syncEq():
    # Connect to databases
    oracleDB = mx.DriverConnect( 'DSN=cern-crbs;UID=cr;PWD=amph9' )
    connect2IndicoDB()
    
    # Create possible equipment branch
    root = DALManagerCERN().root
    if True or not root.has_key( 'EquipmentList' ):
        root['EquipmentList'] = {}
    DALManagerCERN().commit()
    print "Equipment branch has been created"

    # Set default location
    Location.setDefaultLocation( "CERN" )

    # Sync Rooms, Possible Equipment and RoomsEquipment
    from MaKaC.plugins.RoomBooking.CERN.Migration.synchronizeWithFoundation import synchronizeEquipment
    synchronizeEquipment( oracleDB )
    
    # Close databases
    oracleDB.close()
    disconnectFromIndicoDB()
    

def setConfirmationsForBuilding40():
    rooms = CrossLocationQueries.getRooms( freeText = '40-' )
    for r in rooms:
        r.resvsNeedConfirmation = True

def addExcludedDays():
    resvEx = ReservationBase()
    resvEx.isConfirmed = None
    resvs = CrossLocationQueries.getReservations( resvExample = resvEx )
    for r in resvs:
        r._excludedDays = []

def main_RoomsFromFoundation():
    # Connect to databases
    oracleDB = mx.DriverConnect( 'DSN=cern-crbs;UID=cr;PWD=amph9' )
    connect2IndicoDB()
    
    # Import

    # Set default location
    Location.setDefaultLocation( "CERN" )
    root = DALManagerCERN().root

    # Import Users
    #importUsers( oracleDB )
    #DALManagerCERN().commit()
    
    # Sync Rooms, Possible Equipment and RoomsEquipment
    #from MaKaC.common.FoundationSync.foundationSync import FoundationSync
    #fs = FoundationSync()
    #fs.synchronizeRooms( oracleDB )
    #fs.synchronizeEquipment( oracleDB )
    #fs.synchronizeRoomsEquipment( oracleDB )
    #DALManagerCERN().commit()
    
    # Import reservations
    importReservations( oracleDB, force = False )
    #DALManagerCERN().commit()
    
    # Import requests
    #importReservations( oracleDB, force = False, prebookings = True )
    #DALManagerCERN().commit()
    
    # Close databases
    oracleDB.close()
    disconnectFromIndicoDB()




if __name__ == '__main__':
    main_RoomsFromFoundation()
    pass
