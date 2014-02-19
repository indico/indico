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

from BTrees.OOBTree import OOSet
from ZODB import FileStorage, DB
from ZODB.DB import DB, transaction
from ZODB.PersistentMapping import PersistentMapping
from persistent import Persistent
from pytz import timezone
from datetime import datetime

from MaKaC.rb_reservation import ReservationBase, RepeatabilityEnum
from MaKaC.rb_tools import qbeMatch, containsExactly_OR_containsAny, fromUTC
from MaKaC.rb_location import CrossLocationQueries
from MaKaC.plugins.RoomBooking.default.factory import Factory
from MaKaC.common.logger import Logger
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.plugins.base import Observable
from MaKaC.plugins.RoomBooking.notifications import ReservationStartEndNotification

from indico.modules.scheduler import Client, tasks

# Branch name in ZODB root
_RESERVATIONS = 'Reservations'
_ROOM_RESERVATIONS_INDEX = 'RoomReservationsIndex'
_USER_RESERVATIONS_INDEX = 'UserReservationsIndex'
_DAY_RESERVATIONS_INDEX = 'DayReservationsIndex'
_ROOM_DAY_RESERVATIONS_INDEX = 'RoomDayReservationsIndex'

class Reservation( Persistent, ReservationBase, Observable ):
    """
    ZODB specific implementation.

    For documentation of methods see base class.
    """

    __dalManager = Factory.getDALManager()

    def __init__( self ):
        ReservationBase.__init__( self )
        self._excludedDays = []
        self.useVC = []
        self.resvHistory = ResvHistoryHandler()
        self.startEndNotification = None

    def getUseVC( self ):
        try:
            return self.useVC
        except:
            self.useVC = []
        return self.useVC

    def getResvHistory( self ):
        try:
            return self.resvHistory
        except:
            self.resvHistory = ResvHistoryHandler()
        return self.resvHistory

    @staticmethod
    def getReservationsRoot( ):
        return Reservation.__dalManager.getRoot(_RESERVATIONS)

    @staticmethod
    def getRoomReservationsIndexRoot( ):
        return Reservation.__dalManager.getRoot(_ROOM_RESERVATIONS_INDEX)

    @staticmethod
    def getUserReservationsIndexRoot( ):
        return Reservation.__dalManager.getRoot(_USER_RESERVATIONS_INDEX)

    @staticmethod
    def getDayReservationsIndexRoot( ):
        return Reservation.__dalManager.getRoot(_DAY_RESERVATIONS_INDEX)

    @staticmethod
    def getRoomDayReservationsIndexRoot():
        return Reservation.__dalManager.getRoot(_ROOM_DAY_RESERVATIONS_INDEX)

    def insert( self ):
        """ Documentation in base class. """
        ReservationBase.insert( self )

        resvBTree = Reservation.getReservationsRoot()
        # Ensure ID
        if self.id == None:
#            # Maximum ID + 1
#            if len( resvBTree ) > 0:
#                self.id = resvBTree.maxKey() + 1
#            else:
#                self.id = 1 # Can not use maxKey for 1st record in a tree
            #Faster version of the code above
            try:
                self.id = resvBTree.maxKey() + 1
            except ValueError:
                self.id = 1
        # Add self to the BTree
        resvBTree[self.id] = self

        # Update room => room reservations index
        roomReservationsIndexBTree = Reservation.getRoomReservationsIndexRoot()
        resvs = roomReservationsIndexBTree.get( self.room.id )
        if resvs == None:
            resvs = [] # New list of reservations for this room
            roomReservationsIndexBTree.insert( self.room.id, resvs )
        resvs.append( self )
        roomReservationsIndexBTree[self.room.id] = resvs

        # Update user => user reservations index
        userReservationsIndexBTree = Reservation.getUserReservationsIndexRoot()
        resvs = userReservationsIndexBTree.get( self.createdBy )
        if resvs == None:
            resvs = [] # New list of reservations for this room
            userReservationsIndexBTree.insert( self.createdBy, resvs )
        resvs.append( self )
        userReservationsIndexBTree[self.createdBy] = resvs

        # Update day => reservations index
        self._addToDayReservationsIndex()

        # Update room+day => reservations index
        self._addToRoomDayReservationsIndex()

        self._notify('reservationCreated')

        # Warning:
        # createdBy, once assigned to rerservation, CAN NOT be changed later (index!)
        # room, once assigned to reservation, CAN NOT be changed later (index!)

    def update(self):
        ReservationBase.update(self)
        self._notify('reservationUpdated')

    def getStartEndNotification(self):
        if hasattr(self, '_startEndNotification') and self._startEndNotification is not None:
            return self._startEndNotification
        self._startEndNotification = ReservationStartEndNotification(self)
        return self._startEndNotification

    def getLocalizedStartDT(self):
        tz = HelperMaKaCInfo.getMaKaCInfoInstance().getTimezone()
        return timezone(tz).localize(self._utcStartDT)

    def getLocalizedEndDT(self):
        tz = HelperMaKaCInfo.getMaKaCInfoInstance().getTimezone()
        return timezone(tz).localize(self._utcEndDT)

    def indexDayReservations( self ):
        self._addToDayReservationsIndex()
        self._addToRoomDayReservationsIndex()
        self._p_changed = True

    def unindexDayReservations( self ):
        self._removeFromDayReservationsIndex()
        self._removeFromRoomDayReservationsIndex()
        self._p_changed = True

    def remove( self ):
        """ Documentation in base class. """
        resvBTree = Reservation.getReservationsRoot()
        del resvBTree[self.id]

        # Update room => room reservations index
        roomReservationsIndexBTree = Reservation.getRoomReservationsIndexRoot()
        resvs = roomReservationsIndexBTree[self.room.id] # must exist
        resvs.remove( self )
        roomReservationsIndexBTree[self.room.id] = resvs    #roomReservationsIndexBTree._p_changed = True - does not work here!!

        # Update user => user reservations index
        userReservationsIndexBTree = Reservation.getUserReservationsIndexRoot()
        resvs = userReservationsIndexBTree[self.createdBy] # must exist
        resvs.remove( self )
        userReservationsIndexBTree[self.createdBy] = resvs

        # Update day => reservations index
        self._removeFromDayReservationsIndex()
        # Update room+day => reservations index
        self._removeFromRoomDayReservationsIndex()

        self._notify('reservationDeleted')

    def _addToDayReservationsIndex( self ):
        dayReservationsIndexBTree = Reservation.getDayReservationsIndexRoot()

        for period in self.splitToPeriods():
            day = period.startDT.date()
            resvs = dayReservationsIndexBTree.get( day )
            if resvs == None:
                resvs = [] # New list of reservations for this day
                dayReservationsIndexBTree.insert( day, resvs )
            resvs.append( self )
            dayReservationsIndexBTree[day] = resvs

    def _removeFromDayReservationsIndex( self ):
        dayReservationsIndexBTree = Reservation.getDayReservationsIndexRoot()

        # For each of the periods, checks if it is in the index
        # and removes the entry

        for period in self.splitToPeriods():
            day = period.startDT.date()
            resvs = dayReservationsIndexBTree.get( day )
            if resvs != None and self in resvs:
                resvs.remove(self)
                dayReservationsIndexBTree[day] = resvs

    def _addToRoomDayReservationsIndex(self):
        roomDayReservationsIndexBTree = Reservation.getRoomDayReservationsIndexRoot()

        for period in self.splitToPeriods():
            day = period.startDT.date()
            key = (self.room.id, day)
            resvs = roomDayReservationsIndexBTree.get(key)
            if resvs is None:
                resvs = OOSet()
            resvs.add(self)
            roomDayReservationsIndexBTree[key] = resvs

    def _removeFromRoomDayReservationsIndex(self):
        roomDayReservationsIndexBTree = Reservation.getRoomDayReservationsIndexRoot()

        for period in self.splitToPeriods():
            day = period.startDT.date()
            key = (self.room.id, day)
            resvs = roomDayReservationsIndexBTree.get(key)
            if resvs is not None and self in resvs:
                resvs.remove(self)
                roomDayReservationsIndexBTree[key] = resvs

    @staticmethod
    def getReservations( *args, **kwargs ):
        """ Documentation in base class. """

        resvID = kwargs.get( 'resvID' )
        resvEx = kwargs.get( 'resvExample' )
        rooms = kwargs.get( 'rooms' )
        countOnly = kwargs.get( 'countOnly' )
        archival = kwargs.get( 'archival' )
        heavy = kwargs.get( 'heavy' )
        location = kwargs.get( 'location' )
        days = kwargs.get( 'days' )

        ret_lst = []
        counter = 0
        root = Factory.getDALManager().getRoot()

        if resvID != None:
            return root[_RESERVATIONS].get( resvID )

        resvCandidates = None

        alreadyRoomFiltered = False
        # If we filter by room but not by day, we can use the RoomReservations index
        if rooms and not days and len(rooms) <= 10:
            # Use room => room reservations index
            resvCandidates = set()
            for room in rooms:
                if location != None and room.locationName != location:
                    continue # Skip rooms from different locations
                roomResvs = Reservation.getRoomReservationsIndexRoot().get( room.id )
                if roomResvs != None:
                    resvCandidates.update(roomResvs)
            alreadyRoomFiltered = True

        # If we don't have reservations yet but filter by creator, use the UserReservations index
        if resvCandidates == None and resvEx != None and resvEx.createdBy != None:
            resvCandidates = set(Reservation.getUserReservationsIndexRoot().get(resvEx.createdBy, []))

        # If we want to filter by day, we can choose indexes.
        dayFilteredResvs = None
        if days and rooms:
            # If there's a room filter, too - use the RoomDayReservations index
            dayFilteredResvs = set()
            for key in ((room.id, day) for day in days for room in rooms):
                dayRoomResvs = Reservation.getRoomDayReservationsIndexRoot().get(key, [])
                dayFilteredResvs.update(dayRoomResvs)
            alreadyRoomFiltered = True
        elif days:
            # If we only filter by days, use the DayReservations index
            dayFilteredResvs = set()
            for day in days:
                dayResvs = Reservation.getDayReservationsIndexRoot().get(day, [])
                dayFilteredResvs.update(dayResvs)

        # If we have some day-filtered reservations, use that list or restrict the existing one
        if dayFilteredResvs is not None:
            if resvCandidates is None:
                resvCandidates = dayFilteredResvs
            else:
                # Intersection
                resvCandidates = dayFilteredResvs & resvCandidates

        # If we still have nothing, get all reservations and filter them later in the loop (slow!)
        if resvCandidates is None:
            resvCandidates = Reservation.getReservationsRoot().itervalues()

        for resvCandidate in resvCandidates:
            # Apply all conditions

            if archival != None:
                if resvCandidate.isArchival != archival:
                    continue

            if location != None:
                # If location is specified, use only rooms from this location
                if not resvCandidate.locationName == location:
                    continue

            if heavy != None:
                if resvCandidate.isHeavy != heavy:
                    continue

            # Does the reservation overlap on the specified period?
            if resvEx != None:
                if resvEx.startDT != None and resvEx.endDT != None:
                    if not resvCandidate.overlapsOn( resvEx.startDT, resvEx.endDT ):
                        continue

                if rooms != None and not alreadyRoomFiltered:
                    if resvCandidate.room not in rooms:
                        continue

                if resvEx.createdDT != None:
                    if resvEx.createdDT != resvCandidate.createdDT:
                        continue

                if resvEx.bookedForName != None:
                    if resvCandidate.bookedForName == None:
                        continue
                    if not containsExactly_OR_containsAny( resvEx.bookedForName, resvCandidate.bookedForName ):
                        continue

                if resvEx.bookedForId != None:
                    if resvCandidate.bookedForId == None:
                        continue
                    if resvEx.bookedForId != resvCandidate.bookedForId:
                        continue

                if resvEx.reason != None:
                    if resvCandidate.reason == None:
                        continue
                    if not containsExactly_OR_containsAny( resvEx.reason, resvCandidate.reason ):
                        continue

                if resvEx.contactEmail != None:
                    if resvCandidate.contactEmail == None:
                        continue
                    if not resvEx.contactEmail in resvCandidate.contactEmail:
                        continue

                if resvEx.contactPhone != None:
                    if resvCandidate.contactPhone == None:
                        continue
                    if not resvEx.contactPhone in resvCandidate.contactPhone:
                        continue

                if resvEx.createdBy != None:
                    if resvCandidate.createdBy != resvEx.createdBy:
                        continue

                if resvEx.rejectionReason != None:
                    if resvCandidate.rejectionReason == None:
                        continue
                    if not resvEx.rejectionReason in resvCandidate.rejectionReason:
                        continue

                if resvEx.isConfirmed != None:
                    if not resvCandidate.isConfirmed == resvEx.isConfirmed:
                        continue

                if resvEx.isRejected != None:
                    if not resvCandidate.isRejected == resvEx.isRejected:
                        continue

                if resvEx.isCancelled != None:
                    if not resvCandidate.isCancelled == resvEx.isCancelled:
                        continue

                if resvEx.usesAVC != None:
                    if not resvCandidate.usesAVC == resvEx.usesAVC:
                        continue

                if resvEx.needsAVCSupport != None:
                    if not resvCandidate.needsAVCSupport == resvEx.needsAVCSupport:
                        continue

                if resvEx.needsAssistance != None:
                    if not resvCandidate.needsAssistance == resvEx.needsAssistance:
                        continue

            # META-PROGRAMMING STYLE OF CHECKING ATTRIBUTES EQUALITY
            # ABANDONED DUE TO PERFORMANCE PROBLEMS
            # Are standard conditions met? (other attributes equality)
            #if not qbeMatch( resvEx, resvCandidate, Reservation.__attrSpecialEqual ):
            #    continue


            # All conditions are met: add reservation to the results
            counter += 1
            if not countOnly:
                ret_lst.append( resvCandidate )

        #print "Found " + str( counter ) + " reservations."
        if not countOnly: return ret_lst
        else: return counter

    @staticmethod
    def countReservations( *args, **kwargs ):
        """ Documentation in base class. """
        kwargs['countOnly'] = True
        return ReservationBase.getReservations( **kwargs )

    # Excluded days management

    def getExcludedDays( self ):
        ReservationBase.getExcludedDays( self )
        from copy import copy
        lst = copy( self._excludedDays )
        lst.sort()
        return lst

    def setExcludedDays( self, excludedDays ):
        ReservationBase.setExcludedDays( self, excludedDays )
        self._excludedDays = excludedDays

    def excludeDay( self, day, unindex = False ):
        """
        Inserts day into list of excluded days.
        day should be of date type (NOT datetime).
        """
        ReservationBase.excludeDay( self, day )
        lst = self._excludedDays

        if not day in lst:
            lst.append(day)

        self._excludedDays = lst  # Force update

        if unindex:
            day_resv_idx = Reservation.getDayReservationsIndexRoot()
            room_day_resv_idx = Reservation.getRoomDayReservationsIndexRoot()

            if day in day_resv_idx:
                try:
                    resvs = day_resv_idx[day]
                    resvs.remove(self)
                    day_resv_idx[day] = resvs
                except ValueError, e:
                    Logger.get('RoomBooking').debug("excludeDay: DayReservationsIndex - unindexing "
                                                    "a day ({0}) which is not indexed".format(day))

            key = (self.room.id, day)

            if key in room_day_resv_idx:
                try:
                    resvs = room_day_resv_idx[key]
                    resvs.remove(self)
                    room_day_resv_idx[key] = resvs
                except ValueError, e:
                    Logger.get('RoomBooking').debug("excludeDay: RoomDayReservationsIndex - unindexing "
                                                    "a key ({0}) which is not indexed".format(key))

    def includeDay( self, dayD ):
        """
        Inserts dayD into list of excluded days.
        dayD should be of date type (not datetime).
        """
        ReservationBase.includeDay( self, dayD )
        lst = self._excludedDays
        lst.remove( dayD )
        self._excludedDays = lst  # Force update

        # Re-indexing that day
        dayReservationsIndexBTree = Reservation.getDayReservationsIndexRoot()
        resvs = dayReservationsIndexBTree.get(dayD)
        if resvs is None:
            resvs = []
            dayReservationsIndexBTree.insert( dayD, resvs )
        resvs.append( self )
        dayReservationsIndexBTree[dayD] = resvs

    def dayIsExcluded( self, dayD ):
        ReservationBase.dayIsExcluded( self, dayD )
        return dayD in self.getExcludedDays()

    def createSnapshot( self ):
        """
        Creates dynamically a dictionnary of the attributes of the object.
        This dictionnary will be mainly used to compare the reservation
        before and after a modification
        """
        result = {}

        for attr, val in self.__dict__.iteritems():
            result[attr] = val

        return result

    # Statistical

    @staticmethod
    def getNumberOfReservations( *args, **kwargs ):
        """
        Returns total number of reservations in database.
        """
        location = kwargs.get( 'location', Location.getDefaultLocation().friendlyName )
        return Reservation.countReservations( location = location )

    @staticmethod
    def getNumberOfLiveReservations( *args, **kwargs ):
        """ Documentation in base class. """
        location = kwargs.get( 'location', Location.getDefaultLocation().friendlyName )
        resvEx = Factory.newReservation()
        resvEx.isValid = True
        return Reservation.countReservations( resvExample = resvEx, archival = False, location = location )

    @staticmethod
    def getNumberOfArchivalReservations( *args, **kwargs ):
        """
        Returns number of archival reservations in database.
        Reservation is archival if it has end date in the past.
        Cancelled future reservations are not consider as archival.
        """
        location = kwargs.get( 'location', Location.getDefaultLocation().friendlyName )
        return Reservation.countReservations( archival = True, location = location )


    # ==== Private ===================================================

    @classmethod
    def __attrSpecialEqual( cls, attrName, attrValExample, attrValCandidate ):
        # Skip checking for now, these must be checked another way
        if attrName in ( 'startDT', 'endDT', 'room', 'guid', 'locationName', 'isArchival', 'repeatability', 'weekDay', 'weekNumber' ):
            return True # Skip by stating they match
        if attrName[0:7] == 'verbose':
            return True
        if attrName == 'createdBy':
            return attrValExample == attrValCandidate # Just exact string matching
        if attrName in ['bookedForName', 'reason']:
            # "Must contain exactly" or must contain any
            attrValExample = attrValExample.strip().lower()
            if attrValExample[0] in ['"', "'"] and attrValExample[-1] in ['"', "'"]:
                attrValExample = attrValExample[1:-1]
                return attrValExample in attrValCandidate.lower()
            else:
                words = attrValExample.split()
                for word in words:
                    if word in attrValCandidate.lower():
                        return True

        return None

    def _getLocationName( self ):
        if self.room == None:
            return None
        return self.room.locationName

class ResvHistoryEntry( Persistent ):

    def __init__( self, user, info, emails ):
        self._timestamp = datetime.utcnow().strftime("%d %b %Y %H:%M")
        self._responsibleUser = user.getFullName()
        self._info = info #List of str
        # Generate list of email addresses to which a notification email was sent,
        # and adds them to the info if there are any
        emailAddrs = ""
        for email in emails :
            for toAddr in email["toList"] :
                emailAddrs += (", " + toAddr)
        if emailAddrs != "":
            self._info.append("Emails triggered to:<span style='font-family: \"Courier New\"'>" + emailAddrs[1:] +"</span>")

    def getTimestamp( self ):
        return self._timestamp

    def getResponsibleUser( self ):
        return self._responsibleUser

    def getInfo( self ):
        return self._info


class ResvHistoryHandler( Persistent ):
    """
    Utility class used to record actions performed on a reservation
    """

    # Dictionnary used to map Reservation attribute names to human-friendly
    # names
    _attrNamesMap = {"_utcStartDT"  :   "start date",
                     "_utcEndDT"    :   "end date",
                     "repeatability":   "type",
                     "bookedForName":   "'Booked for' name",
                     "contactEmail" :   "'Booked for' email",
                     "contactPhone" :   "'Booked for' phone",
                     "reason"       :   "reason"
                     }

    # Dictionnary used to map Reservation attribute names to methods that
    # will format them into human-friendly strings
    _attrFormatMap = {"_utcStartDT" :   fromUTC,
                    "_utcEndDT"     :   fromUTC,
                    "repeatability" :   lambda x: RepeatabilityEnum.rep2description[x]
                    }

    def __init__( self ):
        self._entries = []

    def addHistoryEntry( self, entry ):
        if entry == None :
            return False
        try:
            self._entries.insert(0, entry )
        except:
            self._entries = []
            self._entries.insert(0, entry )
        self.notifyModification()
        return True

#    def clearHistory(self):
#        self._entries = []
#        self.notifyModification()

    def getEntries( self ):
        try :
            return self._entries
        except :
            self._entries = []
        return self._entries

    def hasHistory( self ):
        return not(self._entries == None or self._entries == [])

    def notifyModification( self ):
        self._p_changed=1


    def _bookingSnapshotsDiff( self, prevSnapshot, newSnapshot ):
        """
        This method compares two "snapshots" of bookings and returns a
        dictionnary containing the attributes that differs, along with their
        values
        """
        result = {}
        for attr in newSnapshot.keys() :
            if attr in prevSnapshot :
                if prevSnapshot[attr] != newSnapshot[attr] :
                    result[attr] = {"prev": prevSnapshot[attr],
                                    "new": newSnapshot[attr]}
            else :
                # The attribute was created in the meanwhile
                result[attr] = {"prev": None, "new": newSnapshot[attr]}

        return result

    def getResvModifInfo(self, info, before, after):
        """
        This utility method generates the info of the history entry when
        a reservation is modified.
        - info : List of str - The list to fill in with the info
        - before : dict - Snapshot of the reservation before modification
        - after : dict - Snapshot of the reservation after modification
        """

        info.append("Booking modified")
        # Getting the attributes that changed:
        attrDiff = self._bookingSnapshotsDiff( before, after )
        # Create the info strings out of the diffs
        for attr in attrDiff.keys() :
            try:
                attrName = self._attrNamesMap[attr]
            except KeyError:
                attrName = attr
            try:
                prevValue = self._attrFormatMap[attr](attrDiff[attr]["prev"])
            except KeyError, AttributeError:
                prevValue = str(attrDiff[attr]["prev"])
            try:
                newValue = self._attrFormatMap[attr](attrDiff[attr]["new"])
            except KeyError, AttributeError:
                newValue = str(attrDiff[attr]["new"])

            if prevValue == "" :
                info.append("The %s was set to '%s'" %(attrName, newValue))
            elif newValue == "" :
                info.append("The %s was cleared" %attrName)
            else :
                info.append("The %s was changed from '%s' to '%s'" %(attrName, prevValue, newValue))

# ============================================================================
# ================================== TEST ====================================
# ============================================================================

class Test( object ):

    dalManager = Factory.getDALManager()

    @staticmethod
    def getReservations():
        from MaKaC.rb_room import RoomBase

        Test.dalManager.connect()

        roomEx = Factory.newRoom()
        roomEx.name = 'TH AMPHITHEATRE'

        resvEx = Factory.newReservation()
        resvEx.startDT = datetime( 2006, 12, 01, 10 )
        resvEx.endDT = datetime( 2006, 12, 14, 15 )
        #resvEx.bookedForName = 'Jean-Jacques Blais'
        resvs = ReservationBase.getReservations( resvExample = resvEx, rooms = [roomEx] )

        for resv in resvs:
            print "============================="
            print resv

        Test.dalManager.disconnect()

    @staticmethod
    def getReservations2():
        from MaKaC.rb_room import RoomBase

        Test.dalManager.connect()

        resvEx = Factory.newReservation()
        resvEx.startDT = datetime( 2006, 12, 01, 10 )
        resvEx.endDT = datetime( 2006, 12, 14, 15 )
        resvEx.repeatability = 0 # Daily

        #ReservationBase.getReservations( \
        #    roomExample = roomEx,
        #    resvExample = resvEx,
        #    available = True )

        resv = ReservationBase.getReservations( resvID = 363818 )
        print resv
        r = Reservation()
        r.room = resv.room
        r.startDT = datetime( 2006, 10, 13, 8, 30 )
        r.endDT = datetime( 2006, 10, 13, 17, 30 )
        col = r.getCollisions()
        print col

        Test.dalManager.disconnect()

    @staticmethod
    def tmp():
        from MaKaC.rb_factory import Factory
        from MaKaC.rb_room import RoomBase
        from indico.core.db import DBMgr
        from BTrees.OOBTree import OOBTree

        DBMgr.getInstance().startRequest()
        Factory.getDALManager().connect()

        dayReservationsIndexBTree = OOBTree()
        raise str( dir( dayReservationsIndexBTree ) )

        Factory.getDALManager().disconnect()
        DBMgr.getInstance().endRequest()

    @staticmethod
    def indexByDay():
        from MaKaC.rb_location import CrossLocationDB
        from MaKaC.rb_room import RoomBase
        from indico.core.db import DBMgr

        DBMgr.getInstance().startRequest()
        CrossLocationDB.connect()

#        resvEx = ReservationBase()
#        resvEx.isConfirmed = None
#        resvs = CrossLocationQueries.getReservations( resvExample = resvEx )
#        print "There are " + str( len( resvs ) ) + " resvs to index..."
#        c = 0
#        for resv in resvs:
#            resv._addToDayReservationsIndex()
#            c += 1
#            if c % 100 == 0:
#                print c

        CrossLocationDB.commit()
        CrossLocationDB.disconnect()
        DBMgr.getInstance().endRequest()

    @staticmethod
    def rebuildRoomReservationsIndex():
        from indico.core.db import DBMgr
        from MaKaC.rb_location import CrossLocationDB
        from MaKaC.rb_room import RoomBase
        from MaKaC.plugins.RoomBooking.default.dalManager import DALManager
        from BTrees.OOBTree import OOBTree

        DBMgr.getInstance().startRequest()
        CrossLocationDB.connect()
        root = DALManager.getRoot()

        resvEx = ReservationBase()
        resvEx.isConfirmed = None
        allResvs = CrossLocationQueries.getReservations( resvExample = resvEx )
        print "There are " + str( len( allResvs ) ) + " resvs and pre-resvs to index..."
        c = 0

        root[_ROOM_RESERVATIONS_INDEX] = OOBTree()
        print "Room => Reservations Index branch created"

        for resv in allResvs:
            roomReservationsIndexBTree = root[_ROOM_RESERVATIONS_INDEX]
            resvs = roomReservationsIndexBTree.get( resv.room.id )
            if resvs == None:
                resvs = [] # New list of reservations for this room
                roomReservationsIndexBTree.insert( resv.room.id, resvs )
            resvs.append( resv )
            roomReservationsIndexBTree[resv.room.id] = resvs
            c += 1
            if c % 100 == 0:
                print c

        CrossLocationDB.commit()
        CrossLocationDB.disconnect()
        DBMgr.getInstance().endRequest()

    @staticmethod
    def play():
        from MaKaC.rb_location import CrossLocationDB
        from MaKaC.rb_room import RoomBase
        from indico.core.db import DBMgr

        DBMgr.getInstance().startRequest()
        CrossLocationDB.connect()

        roomEx = RoomBase()
        roomEx.isActive = False
        rooms = CrossLocationQueries.getRooms( roomExample = roomEx )
        for r in rooms:
            print r

        CrossLocationDB.commit()
        CrossLocationDB.disconnect()
        DBMgr.getInstance().endRequest()


if __name__ == '__main__':
    #Test.getReservations()
    #Test.getReservations2()
    #Test.indexByDay()
    #Test.rebuildRoomReservationsIndex()
    Test.play()
    pass
