# -*- coding: utf-8 -*-
##
## $Id: rb_room.py,v 1.12 2009/05/14 18:05:51 jose Exp $
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
Part of Room Booking Module (rb_)
Responsible: Piotr Wlodarek
"""
from MaKaC.rb_tools import Impersistant, checkPresence, iterdays
from MaKaC.rb_location import Location, RoomGUID, CrossLocationQueries
from MaKaC.user import Avatar, AvatarHolder
from MaKaC.accessControl import AccessWrapper
from datetime import datetime, timedelta


class RoomBase( object ):
    """
    Generic room, Data Access Layer independant.
    Represents physical room suitable for meetings and/or conferences.
    """

    # !=> Properties are in the end of class definition

    # Management -------------------------------------------------------------

    def __init__( self ):
        """
        Do NOT insert object into database in the constructor.
        """
        self._name = None
        self._photoId = None
        self._locationName = None

    def insert( self ):
        """
        Inserts room into database (SQL: INSERT).
        """
        AvatarHolder().invalidateRoomManagerIdList()
        self.checkIntegrity()

    def update( self ):
        """
        Updates room in database (SQL: UPDATE).
        """
        #AvatarHolder().invalidateRoomManagerIdList()
        self.checkIntegrity()

    def remove( self ):
        """
        Removes room from database (SQL: DELETE).
        """
        pass

    def notifyAboutResponsibility( self ):
        """
        FINAL (not intented to be overriden)
        Notifies (e-mails) previous and new responsible about
        responsibility change. Called after creating/updating the room.
        """
        pass

    # Query ------------------------------------------------------------------

    @staticmethod
    def getRooms( *args, **kwargs ):
        """
        Returns list of rooms meeting specified conditions.

        It is 'query by example'. You specify conditions by creating
        the object and passing it to the method.

        All arguments are optional:

        roomID - just a shortcut. Will return ONE room (not a list) or None.
        roomName - just a shortcut. Will return ONE room (not a list) or None.
        roomExample - example RoomBase object.
        reservationExample - example ReservationBase object. Represents reservation period.
        available - Bool, true if room must be available, false if must be booked, None if do not care
        freeText - str, room will be found if this string will be found anywhere in the object
            i.e. in equipment list, comments, responsible etc.
        minCapacity - Bool, defaults to False. If True, then rooms of capacity >= will be found.
            Otherwise capacity it looks for rooms with capacity within 20% range.
        allFast - Bool, defaults to False. If True, ALL active rooms will be returned
            in ultra fast way, REGARDLESS of all other options.
        ownedBy - Avatar
        customAtts - for rooms with custom attributes.
                     rooms with no .customAtts attributes will be filtered out if this parameter is present
                     The customAtts attribute should be a list of dictionaries with the attributes "name", "allowEmpty", "filter".
                     "name" -> the name of the custom attribute
                     "allowEmpty" -> if we allow the custom attribute to be empty or not (empty = "" or string with only whitespaces)
                     "filter" -> a function to which we will pass the value of the custom attribute and has to return True or False.
                     If there is more than 1 dictionary in the list, it will be like doing an AND of the conditions they represent.
                     (see example 6)

        Examples:

        # 1. Get all rooms
        rooms = RoomBase.getRooms()

        # 2. Get all rooms with capacity about 30
        r = Factory.newRoom()
        r.capacity = 30
        rooms = RoomBase.getRooms( roomExample = r )

        # 3. Get all rooms reserved on the New Year 2007,
        # which have capacity about 30, are at Meyrin site and have 'jean' in comments.

        r = Factory.newRoom()
        r.capacity = 30
        r.site = 'Meyrin'
        r.comments = 'jean'
        p = ReservationBase()
        p.startDT = datetime.datetime( 2007, 01, 01 )
        p.endDT = datetime.datetime( 2007, 01, 01 )
        p.repeatability = None

        rooms = RoomBase.getRooms( roomExample = r, reservationExample = p, available = False )

        # 4. Get all rooms containing "sex" in their attributes

        rooms = RoomBase.getRooms( freeText = 'sex' )

        # 5. Get room 'AT AMPHITHEATRE'

        oneRoom = RoomBase.getRooms( roomName = 'AT AMPHITHEATRE' )

        #6. Get rooms with a H.323 IP defined
        rooms = RoomBase.getRooms ( customAtts = [{"name":'H323 IP', "allowEmpty":False,
                                                   "filter": (lambda ip: validIP(ip))}])
        """
        # Simply redirect to the plugin
        from MaKaC.rb_factory import Factory
        return Factory.newRoom().getRooms( **kwargs )

    def getReservations( self, resvExample = None, archival = None ):
        """
        FINAL (not intented to be overriden)
        Returns reservations of this room, meeting specified criteria.
        Look ReservationBase.getReservations for details.
        """
        # Simply redirect to the plugin
        from MaKaC.rb_factory import Factory
        from MaKaC.rb_reservation import ReservationBase

        return ReservationBase.getReservations( resvExample = resvExample, rooms = [self], archival = archival )

    def getLiveReservations( self, resvExample = None ):
        """
        FINAL (not intented to be overriden)
        Returns valid, non archival reservations of this room,
        meeting specified criteria. Look ReservationBase.getReservations for details.
        """
        from MaKaC.rb_factory import Factory
        from MaKaC.rb_reservation import ReservationBase

        if resvExample == None:
            resvExample = Factory.newReservation()
        resvExample.isCancelled = False
        resvExample.isRejected = False

        return ReservationBase.getReservations( resvExample = resvExample,
                                                rooms = [self], archival = False )

    def isAvailable( self, potentialReservation ):
        """
        FINAL (not intented to be overriden)
        Checks whether the room is available for the potentialReservation.
        potentialReservation is of type ReservationBase. It specifies the period.
        """
        from MaKaC.rb_reservation import ReservationBase
        if potentialReservation.getCollisions( boolResult = True ):
            return False
        return True

    def getResponsible( self ):
        """
        FINAL (not intented to be overriden)
        Returns responsible person (Avatar object).
        """
        avatar = AvatarHolder().getById( self.responsibleId )#match( { 'id': self.responsibleId } )[0]

        return avatar

    # Statistical ------------------------------------------------------------

    @staticmethod
    def getNumberOfRooms( **kwargs ):
        """
        FINAL (not intented to be overriden)
        Returns total number of rooms in database.
        """
        name = kwargs.get( 'location', Location.getDefaultLocation().friendlyName )
        location = Location.parse(name)
        return location.factory.newRoom().getNumberOfRooms(location=name)

    @staticmethod
    def getNumberOfActiveRooms( **kwargs ):
        """
        FINAL (not intented to be overriden)
        Returns number of rooms that are active (not logicaly deleted).
        """
        name = kwargs.get( 'location', Location.getDefaultLocation().friendlyName )
        location = Location.parse(name)
        return location.factory.newRoom().getNumberOfActiveRooms(location=name)

    @staticmethod
    def getNumberOfReservableRooms( **kwargs ):
        """
        FINAL (not intented to be overriden)
        Returns number of rooms which can be reserved.
        """
        name = kwargs.get( 'location', Location.getDefaultLocation().friendlyName )
        location = Location.parse(name)
        return location.factory.newRoom().getNumberOfReservableRooms(location=name)

    @staticmethod
    def getTotalSurfaceAndCapacity( **kwargs ):
        """
        FINAL (not intented to be overriden)
        Returns (total_surface, total_capacity) of all Active rooms.
        """
        name = kwargs.get( 'location', Location.getDefaultLocation().friendlyName )
        location = Location.parse(name)
        roomEx = location.factory.newRoom()
        roomEx.isActive = True
        roomEx.isReservable = True
        rooms = CrossLocationQueries.getRooms( roomExample = roomEx, location = name )
        totalSurface, totalCapacity = 0, 0
        for r in rooms:
            if r.surfaceArea:
                totalSurface += r.surfaceArea
            if r.capacity:
                totalCapacity += r.capacity
        return ( totalSurface, totalCapacity )

    @staticmethod
    def getAverageOccupation( **kwargs ):
        """
        FINAL (not intented to be overriden)
        Returns float <0, 1> representing how often - on the avarage -
        the rooms are booked during the working hours. (1 == all the time, 0 == never).
        """

        name = kwargs.get( 'location', Location.getDefaultLocation().friendlyName )

        # Get active, publically reservable rooms
        from MaKaC.rb_factory import Factory
        roomEx = Factory.newRoom()
        roomEx.isActive = True
        roomEx.isReservable = True

        rooms = CrossLocationQueries.getRooms( roomExample = roomEx, location = name )

        # Find collisions with last month period
        from MaKaC.rb_reservation import ReservationBase, RepeatabilityEnum
        resvEx = ReservationBase()
        now = datetime.now()
        resvEx.endDT = datetime( now.year, now.month, now.day, 17, 30 )
        resvEx.startDT = resvEx.endDT - timedelta( 30, 9 * 3600 ) # - 30 days and 9 hours
        resvEx.repeatability = RepeatabilityEnum.daily
        collisions = resvEx.getCollisions( rooms = rooms )

        totalWorkingDays = 0
        weekends = 0
        for day in iterdays( resvEx.startDT, resvEx.endDT ):
            if day.weekday() in [5,6]: # Skip Saturday and Sunday
                weekends += 1
                continue
            # if c.startDT is CERN Holiday: continue
            totalWorkingDays += 1

        booked = timedelta( 0 )
        for c in collisions:
            if c.startDT.weekday() in [5,6]: # Skip Saturday and Sunday
                continue
            # if c.startDT is CERN Holiday: continue
            booked = booked + ( c.endDT - c.startDT )
        totalBookableTime = totalWorkingDays * 9 * len( rooms ) # Hours
        bookedTime = booked.days * 24 + 1.0 * booked.seconds / 3600 # Hours
        if totalBookableTime > 0:
            return bookedTime / totalBookableTime
        else:
            return 0 # Error (no rooms in db)


    def getMyAverageOccupation( self, period="pastmonth" ):
        """
        FINAL (not intented to be overriden)
        Returns float <0, 1> representing how often - on the avarage -
        the room is booked during the working hours. (1 == all the time, 0 == never).
        """
        # Find collisions with last month period
        from MaKaC.rb_reservation import ReservationBase, RepeatabilityEnum
        resvEx = ReservationBase()
        now = datetime.now()
        if period == "pastmonth":
            resvEx.endDT = datetime( now.year, now.month, now.day, 17, 30 )
            resvEx.startDT = resvEx.endDT - timedelta( 30, 9 * 3600 ) # - 30 days and 9 hours
        elif period == "thisyear":
            resvEx.endDT = datetime( now.year, now.month, now.day, 17, 30 )
            resvEx.startDT = datetime( now.year, 1, 1, 0, 0 )
        resvEx.repeatability = RepeatabilityEnum.daily
        collisions = resvEx.getCollisions( rooms = [self] )

        totalWorkingDays = 0
        weekends = 0
        for day in iterdays( resvEx.startDT, resvEx.endDT ):
            if day.weekday() in [5,6]: # Skip Saturday and Sunday
                weekends += 1
                continue
            # if c.startDT is CERN Holiday: continue
            totalWorkingDays += 1

        booked = timedelta( 0 )
        for c in collisions:
            if c.startDT.weekday() in [5,6]: # Skip Saturday and Sunday
                continue
            # if c.startDT is CERN Holiday: continue
            booked = booked + ( c.endDT - c.startDT )
        totalBookableTime = totalWorkingDays * 9 # Hours
        bookedTime = booked.days * 24 + 1.0 * booked.seconds / 3600 # Hours
        if totalBookableTime > 0:
            return bookedTime / totalBookableTime
        else:
            return 0


    # Equipment ------------------------------------------------------------

    def setEquipment( self, eq ):
        """
        Sets (replaces) the equipment list with the new one.
        It may be list ['eq1', 'eq2', ...] or str 'eq1`eq2`eq3`...'
        """
        if isinstance( eq, list ):
            self._equipment = '`'.join( eq )
            return
        elif isinstance( eq, str ):
            self._equipment = eq
            return
        raise 'Invalid equipment list'

    def getEquipment( self ):
        """
        Returns the room's equipment list.
        """
        return self._equipment.split( '`' )

    def insertEquipment( self, equipmentName ):
        """ Adds new equipment to the room. """
        if len( self._equipment ) > 0:
            self._equipment += '`'
        self._equipment += equipmentName

    def removeEquipment( self, equipmentName ):
        """ Removes equipment from the room. """
        e = self.getEquipment()
        e.remove( equipmentName )
        self.setEquipment( e )

    def hasEquipment( self, equipmentName ):
        return equipmentName in self._equipment

    def isCloseToBuilding( self, buildingNr ):
        """ Returns true if room is close to the specified building """
        raise 'Not implemented'

    def belongsTo( self, user ):
        """ Returns true if current CrbsUser is responsible for this room """
        raise 'Not implemented'

    # "System" ---------------------------------------------------------------

    def checkIntegrity( self ):
        """
        FINAL (not intented to be overriden)
        Checks whether:
        - all required attributes has values
        - values are of correct type
        - semantic coherence (i.e. star date <= end date)
        """

        # list of errors
        errors = []

        # check presence and types of arguments
        # =====================================================
        if self.id != None:         # Only for existing objects
            checkPresence( self, errors, 'id', int )
        checkPresence( self, errors, '_locationName', str )
        # check semantic integrity
        # =====================================================

        if errors:
            raise str( errors )

    # Photos -----------------------------------------------------------------

    # NOTE: In general, URL generation should be in urlHandlers.
    # This exception is because we want to allow other room booking systems
    # to override room photos.

    def getPhotoURL( self ):
        # Used to send photos via Python script
        #from MaKaC.webinterface.urlHandlers import UHSendRoomPhoto
        #return UHSendRoomPhoto.getURL( self.photoId, small = False )
        from MaKaC.webinterface.urlHandlers import UHRoomPhoto
        return UHRoomPhoto.getURL( self.photoId )

    def getSmallPhotoURL( self ):
        # Used to send photos via Python script
        #from MaKaC.webinterface.urlHandlers import UHSendRoomPhoto
        #return UHSendRoomPhoto.getURL( self.photoId, small = True )
        from MaKaC.webinterface.urlHandlers import UHRoomPhotoSmall
        return UHRoomPhotoSmall.getURL( self.photoId )

    def savePhoto( self, photoPath ):
        """
        Saves room's photo on the server.
        """
        pass

    def saveSmallPhoto( self, photoPath ):
        """
        Saves room's small photo on the server.
        """
        pass

    # Indico architecture ----------------------------------------------------

    __owner = None

    def getLocator( self ):
        """
        FINAL (not intented to be overriden)
        Returns a globaly unique identification encapsulated in a Locator object
        """
        owner = self.getOwner()
        if owner:
            loc = owner.getLocator()
        else:
            from MaKaC.common.Locators import Locator
            loc = Locator()
        loc["roomLocation"] = self.locationName
        loc["roomID"] = self.id
        return loc

    def setOwner( self, owner ):
        """
        FINAL (not intented to be overriden)
        """
        oryg = self._p_changed
        self.__owner = Impersistant( owner )
        self._p_changed = oryg

    def getOwner( self ):
        """
        FINAL (not intented to be overriden)
        """
        if self.__owner:
            return self.__owner.getObject() # Wrapped in Impersistent
        return None

    def isProtected( self ):
        """
        FINAL (not intented to be overriden)
        The one must be logged in to do anything in RB module.
        """
        return True

    def canView( self, accessWrapper ):
        """
        FINAL (not intented to be overriden)
        Room details are public - anyone can view.
        """
        return True

    def canBook( self, user ):
        """
        FINAL (not intented to be overriden)
        Reservable rooms which does not require pre-booking can be booked by anyone.
        Other rooms - only by their responsibles.
        """
        if self.isActive and self.isReservable and not self.resvsNeedConfirmation:
            simbaList = self.customAtts.get( 'Booking Simba List' )
            if simbaList and simbaList != "Error: unknown mailing list" and simbaList != "":
                if user.isMemberOfSimbaList( simbaList ):
                    return True
            else:
                return True
        if user == None:
            return False

        if (self.isOwnedBy( user ) and self.isActive) \
               or user.isAdmin():
            return True
        return False

    def canPrebook( self, user ):
        """
        FINAL (not intented to be overriden)
        Reservable rooms can be pre-booked by anyone.
        Other rooms - only by their responsibles.
        """
        if self.isActive and self.isReservable:
            simbaList = self.customAtts.get( 'Booking Simba List' )
            if simbaList and simbaList != "Error: unknown mailing list" and simbaList != "":
                    if user.isMemberOfSimbaList( simbaList ):
                        return True
            else:
                return True
        if user == None:
            return False
        if (self.isOwnedBy( user ) and self.isActive) \
               or user.isAdmin():
            return True
        return False

    def canModify( self, accessWrapper ):
        """
        FINAL (not intented to be overriden)
        Only admin can modify rooms.
        """
        if accessWrapper == None:
            return False
        if isinstance( accessWrapper, AccessWrapper ):
            if accessWrapper.getUser():
                return accessWrapper.getUser().isAdmin()
            else:
                return False
        elif isinstance( accessWrapper, Avatar ):
            return accessWrapper.isAdmin()

        raise 'canModify requires either AccessWrapper or Avatar object'

    def canDelete( self, user ):
        return self.canModify( user )

    def isOwnedBy( self, user ):
        """
        Returns True if user is responsible for this room. False otherwise.
        """
        if not self.responsibleId:
            return None
        if self.responsibleId == user.id:
            return True
        try:
            if user in self._v_isOwnedBy.keys():
                return self._v_isOwnedBy[user]
        except:
            self._v_isOwnedBy = {}
        if self.customAtts.get( 'Simba List' ):
            list = self.customAtts.get( 'Simba List' )
            if list != "Error: unknown mailing list" and list != "":
                if user.isMemberOfSimbaList( list ):
                    self._v_isOwnedBy[user] = True
                    return True
        self._v_isOwnedBy[user] = False
        return False

    def getLocationName( self ):
        if self.__class__.__name__ == 'RoomBase':
            return Location.getDefaultLocation().friendlyName
            #raise 'This method is purely virtual. Call it only on derived objects.'
        return self.getLocationName() # Subclass

    def setLocationName( self, locationName ):
        if self.__class__.__name__ == 'RoomBase':
            raise 'This method is purely virtual. Call it only on derived objects.'
        return self.setLocationName( locationName ) # Subclass

    def getAccessKey( self ): return ""

    def getFullName( self ):
        name = ""
        if self.building != None and self.floor != None and self.building != None:
            s = str( self.building ) + '-' + str( self.floor ) + '-' + str( self.roomNr )
            if s != '--':
                name = s
        if self._name != None and len( self._name.strip() ) > 0:
            name += " - %s" % self._name
        return name

    # ==== Private ===================================================

    _name = None
    _equipment = ''   # str, 'eq1`eq2`eq3' - list of room's equipment, joined by '`'

    def _getGuid( self ):
        if self.id == None or self.locationName == None:
            return None
        return RoomGUID( Location.parse( self.locationName ), self.id )

    def _getName( self ):
        if self._name != None and len( self._name.strip() ) > 0:
            return self._name
        if self.building != None and self.floor != None and self.building != None:
            s = str( self.building ) + '-' + str( self.floor ) + '-' + str( self.roomNr )
            if s != '--':
                return s
            return ''
        return None

    def _setName( self, s ):
        # Try to parse the name
        if s == None:
            self._name = None
            return
        parts = s.split( '-' )
        if len( parts ) == 3:
            try:
                self.building = int( parts[0] )
                self.floor = parts[1]
                self.roomNr = parts[2]
                return
            except:
                pass
        # Parsing failed, that means it is real name
        self._name = s

    # CERN specific; don't bother
    def _getNeedsAVCSetup( self ):
        eq = self.getEquipment()
        if not self.locationName or not eq:
            return None
        return 'Video conference' in ' '.join( eq )

    def _eval_str( self, s ):
        ixPrv = 0
        ret = ""

        while True:
            ix = s.find( "#{", ixPrv )
            if ix == -1:
                break
            ret += s[ixPrv:ix] # verbatim
            ixPrv = s.index( "}", ix + 2 ) + 1
            ret += str( eval( s[ix+2:ixPrv-1] ) )
        ret += s[ixPrv:len(s)]

        return ret

    def _getVerboseEquipment( self ):
        s = ""
        eqList = self.getEquipment()
        for eq in eqList:
            s = s + eq + ", "
        if len( eqList ) > 0: s = s[0:len(s)-2] # Cut off last ','
        return s

    def _getPhotoId( self ):
        """
        Feel free to override this in your inherited class.
        """
        return self._doGetPhotoId()

    def _setPhotoId( self, value ):
        self._photoId = value

    def _doGetPhotoId( self ):
        if '_photoId' in dir( self ): return self._photoId
        return None

    def __str__( self ):
        s = self._eval_str(
"""
               id: #{self.id}
         isActive: #{self.isActive}

             room: #{self.name}

         building: #{self.building}
            floor: #{self.floor}
           roomNr: #{self.roomNr}
     isReservable: #{self.isReservable}
rNeedConfirmation: #{self.resvsNeedConfirmation}

             site: #{self.site}
         capacity: #{self.capacity}
      surfaceArea: #{self.surfaceArea}
         division: #{self.division}
          photoId: #{self.photoId}
       externalId: #{self.externalId}

        telephone: #{self.telephone}
       whereIsKey: #{self.whereIsKey}
         comments: #{self.comments}
    responsibleId: #{self.responsibleId}
        equipment: """
        )
        s += self.verboseEquipment + "\n"
        return s

    def __cmp__( self, other ):
        if self.__class__.__name__ == 'NoneType' and other.__class__.__name__ == 'NoneType':
            return 0
        if self.__class__.__name__ == 'NoneType':
            return cmp( None, 1 )
        if other.__class__.__name__ == 'NoneType':
            return cmp( 1, None )

        if self.id != None  and  other.id != None:
            if self.id == other.id:
                return 0

        c = cmp( self.locationName, other.locationName )
        if c == 0:
            c = cmp( self.building, other.building )
            if c == 0:
                c = cmp( self.floor, other.floor )
                if c == 0:
                    c = cmp( self.name, other.name )

        return c

    # ==== Properties ===================================================

    # DO NOT set default values here, since query-by-example will change!!!

    id = None             # int - artificial ID; initialy value from oracle db
    locationName = property( getLocationName, setLocationName ) # location (plugin) name
    guid = property( _getGuid ) # RoomGUID
    isActive = None       # bool - whether the room is active (not logicaly removed) [STSCRBOK]
    resvsNeedConfirmation = None # bool - whether reservations for this room must be confirmed by responsible

    building = None       # int, positive
    floor = None          # str, alphanumeric
    roomNr = None         # str

    name = property( _getName, _setName ) # str - room name

    capacity = None       # int, positive
    site = None           # str - global room localisation, i.e. city
    division = None       # str, TODO
    isReservable = None   # bool - whether the room is reservable
    photoId = property( _getPhotoId, _setPhotoId )        # str - room picture id
    externalId = None     # str - custom external room id, i.e. for locating on the map

    telephone = None      # str
    surfaceArea = None    # int, positive - in meters^2
    whereIsKey = None     # str, typically telephone number
    comments = None       # str
    responsibleId = None  # str, responsible person id (avatar.id)

    #customAtts = {}      # Must behave like name-value dictionary of
                          # custom attributes. Must be put in derived classes.

    verboseEquipment = property( _getVerboseEquipment )
    needsAVCSetup = property( _getNeedsAVCSetup )

# ============================================================================
# ================================== TEST ====================================
# ============================================================================

class Test:
    from MaKaC.rb_factory import Factory

    @staticmethod
    def getReservations():
        from MaKaC.rb_factory import Factory
        from datetime import datetime

        dalManager = Factory.getDALManager()
        dalManager.connect()

        amphitheatre = RoomBase.getRooms( roomName = 'IT AMPHITHEATRE' )
        print "All reservations for IT AMPHITHEATRE: %d" % len( amphitheatre.getReservations() )

        resvEx = Factory.newReservation()
        resvEx.startDT = datetime( 2006, 9, 23, 0 )
        resvEx.endDT = datetime( 2006, 9, 30, 23, 59 )
        reservations = amphitheatre.getLiveReservations( resvExample = resvEx )

        dalManager.disconnect()


if __name__ == '__main__':
    Test.getReservations()

