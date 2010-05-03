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

import os as os
from persistent import Persistent
from persistent.mapping import PersistentMapping
from MaKaC.rb_room import RoomBase
from MaKaC.rb_location import CrossLocationQueries, Location
from MaKaC.plugins.RoomBooking.default.factory import Factory
from MaKaC.rb_tools import qbeMatch
from MaKaC.common.Configuration import Config

# Branch name in ZODB root
_ROOMS = 'Rooms'

class Room( Persistent, RoomBase ):
    """
    ZODB specific implementation.

    For documentation of methods see base class.
    """

    __dalManager = Factory.getDALManager()
    vcList = []

    def __init__(self):
        RoomBase.__init__( self )
        self.customAtts = PersistentMapping()
        self.avaibleVC = []
        self._nonBookableDates = []

    def getNonBookableDates(self):
        try:
            if self._nonBookableDates:
                pass
        except AttributeError, e:
            self._nonBookableDates = []
            self._p_changed = 1
        return self._nonBookableDates

    def addNonBookableDate(self, udate):
        self._nonBookableDates.append(udate)
        self._p_changed = 1

    def addNonBookableDateFromParams(self, params):
        nbd = NonBookableDate(params["startDate"], params["endDate"])
        self._nonBookableDates.append(nbd)
        self._p_changed = 1

    def clearNonBookableDates(self):
        self._nonBookableDates = []
        self._p_changed = 1

    def isNonBookableDay(self, day):
        for nbd in self.getNonBookableDates():
            if nbd.doesDayOverlap(day):
                return True
        return False

    def setAvailableVC(self, avc):
        self.avaibleVC = avc

    def getAvailableVC(self):
        try:
            return self.avaibleVC
        except:
            self.avaibleVC = []
        return self.avaibleVC

    @staticmethod
    def getRoot():
        return Room.__dalManager.getRoot(_ROOMS)

    def insert( self ):
        """ Documentation in base class. """
        RoomBase.insert( self )
        roomsBTree = Room.getRoot()
        # Ensure ID
        if self.id == None:
            # Maximum ID + 1
            if len( roomsBTree ) > 0:
                self.id = roomsBTree.maxKey() + 1
            else:
                self.id = 1 # Can not use maxKey for 1st record in a tree
        # Add self to the BTree
        roomsBTree[self.id] = self

    def update( self ):
        """ Documentation in base class. """
        RoomBase.update( self )

        # Check Simba mailing list
        listName = self.customAtts.get( 'Simba List' )
        if listName:
            from MaKaC.user import GroupHolder
            groups = GroupHolder().match( { 'name': listName }, forceWithoutExtAuth = True )
            if not groups:
                groups = GroupHolder().match( { 'name': listName } )
            if not groups:
                self.customAtts['Simba List'] = 'Error: unknown mailing list'

        self._p_changed = True

    def remove( self ):
        """ Documentation in base class. """
        RoomBase.remove( self )
        roomsBTree = Room.getRoot()
        del roomsBTree[self.id]
        from MaKaC.user import AvatarHolder
        AvatarHolder().invalidateRoomManagerIdList()

    # Typical actions
    @staticmethod
    def getRooms( *args, **kwargs ):
        """ Documentation in base class. """

        roomsBTree = Room.getRoot()
        location = kwargs.get( 'location' )

        if kwargs.get( 'allFast' ) == True:
            return [ room for room in roomsBTree.values() if room.isActive and (not location or room.locationName == location) ]

        if kwargs.get( 'reallyAllFast' ) == True:
            return [ room for room in roomsBTree.values() if (not location or room.locationName == location) ]

        if len( kwargs ) == 0:
            ret_lst = []
            for room in roomsBTree.values():
                ret_lst.append( room )

        roomID = kwargs.get( 'roomID' )
        roomName = kwargs.get( 'roomName' )
        roomEx = kwargs.get( 'roomExample' )
        resvEx = kwargs.get( 'resvExample' )
        freeText = kwargs.get( 'freeText' )
        available = kwargs.get( 'available' )
        countOnly = kwargs.get( 'countOnly' )
        minCapacity = kwargs.get( 'minCapacity' )
        location = kwargs.get( 'location' )
        ownedBy = kwargs.get( 'ownedBy' )
        customAtts = kwargs.get( 'customAtts' )
#        responsibleID = kwargs.get( 'responsibleID' )

        ret_lst = []
        counter = 0
        if roomID != None:
            return roomsBTree.get( roomID )
        if roomName != None:
            for room in roomsBTree.itervalues():
                if room.name == roomName:
                    if location == None or room.locationName == location:
                        return room
            return None

        for room in roomsBTree.itervalues():
            # Apply all conditions =========
            if location != None:
                if room.locationName != location:
                    continue
            if roomEx != None:
                if not qbeMatch( roomEx, room, Room.__attrSpecialEqual, minCapacity = minCapacity ):
                    continue
                if not room.__hasEquipment( roomEx.getEquipment() ):
                    continue
            if freeText != None:
                if not room.__hasFreeText( freeText.split() ):
                    continue
            if resvEx != None:
                resvEx.room = room
                aval = room.isAvailable( resvEx )
                if aval != available:
                    continue
            if ownedBy != None:
                if not room.isOwnedBy( ownedBy ):
                    continue
            if customAtts is not None:
                if not hasattr(room, "customAtts"):
                    continue
                discard = False
                for condition in customAtts:
                    attName = condition["name"]
                    allowEmpty = condition.get("allowEmpty", False)
                    filter = condition.get("filter", None)
                    if not attName in room.customAtts:
                        discard = True
                        break
                    elif not allowEmpty and str(room.customAtts[attName]).strip() == "":
                        discard = True
                        break
                    elif not filter(room.customAtts[attName]):
                        discard = True
                        break
                if discard:
                    continue

            # All conditions are met: add room to the results
            counter += 1
            if not countOnly:
                ret_lst.append( room )

        #print "Found %d rooms." % counter
        if countOnly:
            return counter
        else:
            return ret_lst

    # Statistics ====================================

    @staticmethod
    def countRooms( *args, **kwargs ):
        """ Documentation in base class. """
        kwargs['countOnly'] = True
        return Room.getRooms( **kwargs )

    @staticmethod
    def getNumberOfRooms( *args, **kwargs ):
        """ Documentation in base class. """
        location = kwargs.get( 'location', Location.getDefaultLocation().friendlyName )
        return Room.countRooms( location = location )

    @staticmethod
    def getNumberOfActiveRooms( *args, **kwargs ):
        """ Documentation in base class. """
        location = kwargs.get( 'location', Location.getDefaultLocation().friendlyName )
        room = Factory.newRoom()
        room.isActive = True
        return Room.countRooms( roomExample = room, location = location )

    @staticmethod
    def getNumberOfReservableRooms( *args, **kwargs ):
        """ Documentation in base class. """
        location = kwargs.get( 'location', Location.getDefaultLocation().friendlyName )
        room = Factory.newRoom()
        room.isReservable = True
        room.isActive = True
        return Room.countRooms( roomExample = room, location = location )

    def getLocationName( self ):
        #from MaKaC.plugins.RoomBooking.default.factory import Factory
        #return Factory.locationName
        return self._locationName

    def setLocationName( self, locationName ):
        self._locationName = locationName

    def savePhoto( self, photoPath ):
        filePath = Config.getInstance().getRoomPhotosDir()
        fileName = self._doGetPhotoId( force = True ) + ".jpg"
        try: os.makedirs( filePath )
        except: pass
        fullPath = os.path.join( filePath, fileName )

        f = open( fullPath, "wb" )
        f.write( photoPath.file.read() )
        f.close()

    def saveSmallPhoto( self, photoPath ):
        filePath = Config.getInstance().getRoomSmallPhotosDir()
        fileName = self._doGetPhotoId( force = True ) + ".jpg"
        try: os.makedirs( filePath )
        except: pass
        fullPath = os.path.join( filePath, fileName )

        f = open( fullPath, "wb" )
        f.write( photoPath.file.read() )
        f.close()


    # ==== Private ===================================================

    def _getSafeLocationName( self ):
        if self.locationName == None:
            return None
        s = ""
        for i in xrange( 0, len( self.locationName ) ):
            code = ord( self.locationName[i] )
            if ( code in xrange( ord( 'a' ), ord( 'z' ) + 1 ) ) or \
               ( code in xrange( ord( 'A' ), ord( 'Z' ) + 1 ) ) or \
               ( code in xrange( ord( '0' ), ord( '9' ) + 1 ) ):
                # Valid
                s += self.locationName[i]
            else:
                s += '_' # Replace all other characters with underscore
        return s

    def _doGetPhotoId( self, force = False ):
        photoId = "%s-%s-%s-%s" % ( str( self._getSafeLocationName() ), str( self.building ).strip(), str( self.floor ).strip(), str( self.roomNr ).strip() )

        filePath = Config.getInstance().getRoomPhotosDir()
        fileName = photoId + ".jpg"
        fullPath = os.path.join( filePath, fileName )
        from os.path import exists
        if exists( fullPath ) or force:
            return photoId
        else:
            return None

    def _doSetPhotoId( self ):
        """
        For this plugin, photoId is always composed of location-building-floor-room.jpg
        """
        pass

    def __hasFreeText( self, freeTextList ):
        # OR
        for freeText in freeTextList:
            freeText = freeText.lower()
            if self.__hasOneFreeText( freeText ):
                return True
        return False

    def __hasOneFreeText( self, freeText ):
        # Look for freeText in all string and int attributes
        for attrName in dir( self ):
            if attrName[0] == '_':
                continue
            attrType = eval( 'self.' + attrName + '.__class__.__name__' )
            if attrType == 'str':
                attrVal = eval( 'self.' + attrName )
                if attrVal.lower().find( freeText ) != -1:
                    return True

        # Look for freeText in equipment
        if self.__hasEquipment( [ freeText ] ):
            return True

        # Look for freeText in responsible
        if self.responsibleId != None:
            user = self.getResponsible();
            if freeText in user.getFullName().lower()  or  freeText in user.getEmail().lower():
                return True

        # Look for freeText in custom attributes
        for value in self.customAtts.itervalues():
            if value and ( freeText in value.lower() ):
                return True

        # Not found
        return False

    @staticmethod
    def __goodCapacity( val1, val2, minCapacity = None ):
        # Difference in capacity less than 20%
        if val1 < 1: val1 = 1

        if not minCapacity:
            return abs( val1 - val2 ) / float( val1 ) <= 0.2
        else:
            return val2 > val1

    @classmethod
    def __attrSpecialEqual( cls, attrName, exampleVal, candidateVal, **kwargs ):
        if attrName in ( 'guid', 'locationName', 'name', 'photoId', 'needsAVCSetup' ):
            return True # Skip by stating they match
        if attrName in ( 'responsibleId', 'responsibleID' ):
            return exampleVal == candidateVal # Just exact string matching
        if attrName[0:7] == 'verbose':
            return True
        if attrName.find( 'capacity' ) != -1:
            minCapacity = kwargs.get( 'minCapacity' )
            return cls.__goodCapacity( exampleVal, candidateVal, minCapacity )
        if attrName == 'customAtts':
            # Check if all values in exampleVal are contained
            # in corresponding values of candidateVal
            for k, v in exampleVal.iteritems():
                if v: # If value is specified
                    if candidateVal.get( k ) == None:
                        # Candidate does not have the attribute
                        return False
                    if not ( v in candidateVal[k] ):
                        # Candidate's attribute value does not match example
                        return False
            return True
        return None

    def __hasEquipment( self, requiredEquipmentList ):
        iHave = self.getEquipment()
        for reqEq in requiredEquipmentList:
            have = False
            for myEq in iHave:
                if myEq.lower().find( reqEq.lower() ) != -1:
                    have = True
                    break
            if not have:
                return False
        return True

class NonBookableDate(Persistent):

    def __init__(self, startDate, endDate):
        self.setStartDate(startDate)
        self.setEndDate(endDate)

    def toDict(self):
        return {"startDate": self._startDate,
                "endDate": self._endDate}

    def saveFromDict(self, data):
        self.setStartDate(data["startDate"])
        self.setEndDate(data["endDate"])

    def getStartDate(self):
        return self._startDate

    def setStartDate(self, startDate):
        self._startDate = startDate.replace(hour=0,minute=0,second=0)

    def getEndDate(self):
        return self._endDate

    def setEndDate(self, endDate):
        self._endDate = endDate.replace(hour=23,minute=59,second=59)

    def doesDayOverlap(self, day):
        if day >= self.getStartDate().date() and day <= self.getEndDate().date():
            return True
        else:
            return False
# ============================================================================
# ================================== TEST ====================================
# ============================================================================

class Test( object ):

    dalManager = Factory.getDALManager()

    @staticmethod
    def do():

        # Set equipment
        Test.dalManager.connect()
        em = Factory.getEquipmentManager()
        saved = ['a ', 'bbb', 'c' ]
        em.setPossibleEquipment( saved )
        Test.dalManager.commit()
        Test.dalManager.disconnect()

        # Get equipment
        Test.dalManager.connect()
        loaded = em.getPossibleEquipment()
        assert( loaded == saved )
        Test.dalManager.disconnect()

    @staticmethod
    def getRoomsByExample():
        Test.dalManager.connect()

        # By ID
        room = RoomBase.getRooms( roomID = 176 )
        assert( room.name == '4-1-021' )

        # By other attributes
        roomEx = Factory.newRoom()
        roomEx.site = 'prevessin'
        roomEx.comments = 'res'
        rooms = RoomBase.getRooms( roomExample = roomEx )
        assert( len( rooms ) == 8 ) # 20

        roomEx = Factory.newRoom()
        roomEx.capacity = 20
        rooms = RoomBase.getRooms( roomExample = roomEx )
        assert( len( rooms ) == 26 )

        roomEx = Factory.newRoom()
        roomEx.isReservable = True
        roomEx.setEquipment( [ 'Video projector', 'Wireless' ] )
        rooms = RoomBase.getRooms( roomExample = roomEx )
        assert( len( rooms ) == 33 )

        Test.dalManager.disconnect()

    @staticmethod
    def getRoomsByFreeText():
        Test.dalManager.connect()

        rooms = RoomBase.getRooms( freeText = 'meyrin vrvs' ) # 78828
        assert( len( rooms ) == 12 )

        Test.dalManager.disconnect()

    @staticmethod
    def getRoomsByExampleDemo():
        Test.dalManager.connect()

        roomEx = Factory.newRoom()

        roomEx.building = 513
        roomEx.capacity = 20

        rooms = CrossLocationQueries.getRooms( roomExample = roomEx )

        for room in rooms:
            print "============================="
            print room

        Test.dalManager.disconnect()

    @staticmethod
    def stats():
        Test.dalManager.connect()
        print "All rooms: %d" % RoomBase.getNumberOfRooms()
        print "Active rooms: %d" % RoomBase.getNumberOfActiveRooms()
        print "Reservable rooms: %d" % RoomBase.getNumberOfReservableRooms()
        Test.dalManager.disconnect()

    @staticmethod
    def getAvailableRooms():
        Test.dalManager.connect()

        from datetime import datetime

        roomEx = Factory.newRoom()
        roomEx.isActive = True
        roomEx.isReservable = True

        resvEx = Factory.newReservation()
        resvEx.startDT = datetime( 2006, 12, 01, 10 )
        resvEx.endDT = datetime( 2006, 12, 14, 15 )
        resvEx.repeatability = 0 # Daily

        rooms = RoomBase.getRooms( \
            roomExample = roomEx,
            resvExample = resvEx,
            available = True )

        for room in rooms:
            print "\n=======================================\n"
            print room

        Test.dalManager.disconnect()

if __name__ == '__main__':
    Test.getAvailableRooms()
#    Test.do()
#    Test.getRoomsByExampleDemo()
#    for i in xrange( 3 ):
#        Test.getRoomsByFreeText()
#        Test.getRoomsByExample()
#        Test.stats()

