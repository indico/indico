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
Part of Room Booking Module (rb_)
Responsible: Piotr Wlodarek
"""

"""
Classes for uniform deeling with different locations,
global ids of objects, and cross-location queries.
"""

from persistent import Persistent
from MaKaC.common.Locators import Locator
import MaKaC
from MaKaC.i18n import _
from MaKaC.plugins.pluginLoader import PluginLoader


# ZODB branches name
_DEFAULT_ROOM_BOOKING_LOCATION = 'DefaultRoomBookingLocation'
_ROOM_BOOKING_LOCATION_LIST = 'RoomBookingLocationList'



def _ensureZODBBranch( force = False ):
    root = MaKaC.common.DBMgr.getInstance().getDBConnection().root()
    if force or not root.get( _ROOM_BOOKING_LOCATION_LIST ):
        root[_ROOM_BOOKING_LOCATION_LIST] = [ ]


class Location( Persistent, object ):
    """
    1) Introduction

    Location is a place where rooms exist. It may be seen as room namespace.
    Moreover, Location determines *room booking plugin*.

    Different locations (like CERN, some university in U.S.,
    some company in France...) may have different room booking backends.
    Indico supports them by a plugin system.

    With standard Indico distribution, there is only one,
    generic, ZODB-based plugin. It supports managing multiple locations.

    2) Location objects

    Location object is composed of friendlyName and plugin-specific factory.
    It maps location name (string) to the plugin (represented by the factory).

    3) Location static methods

    Allow you to manage locations:
    - take the list of all known locations
    - add location (if standard ZODB plugin is used)
    - remove location (if standard ZODB plugin is used)
    """

    def getLocator( self ):
        d = Locator()
        d["locationId"] = self.friendlyName
        return d

    def __init__( self, friendlyName, factory ):
        self.friendlyName = friendlyName
        self.factory = factory
        self._avcSupportEmails = []

    def __str__( self ):
        s = _(""" _("Location"): """) + self.friendlyName + "\n"
        s += _(""" _("Plugin"): """) + self.factory.__class__.__name__ + "\n"
        return s

    def __cmp__( self, second ):
        return cmp( self.friendlyName, second.friendlyName )

    friendlyName = None  # str - location's name shown for user (i.e. "CERN")
    factory = None       # Factory - determines the plugin

    def getAllRooms( self ):
        if self.factory:
            return self.factory.newRoom().getRooms(location=self.friendlyName, allFast=True)

    def newRoom( self ):
        if self.factory:
            return self.factory.newRoom( self.friendlyName )

    @staticmethod
    def parse( name ):
        """
        Parses location name into Location object.
        """
        for loc in Location.allLocations:
            if loc.friendlyName == name:
                return loc
        return None

    @staticmethod
    def getAvailablePlugins():
        mods = PluginLoader.getPluginsByType("RoomBooking")
        return mods

    # === Location Management

    @staticmethod
    def setDefaultLocation( locationName ):
        root = MaKaC.common.DBMgr.getInstance().getDBConnection().root()
        root[_DEFAULT_ROOM_BOOKING_LOCATION] = locationName

    @staticmethod
    def getDefaultLocation():
        root = MaKaC.common.DBMgr.getInstance().getDBConnection().root()
        if not root.has_key( _DEFAULT_ROOM_BOOKING_LOCATION ):
            root[_DEFAULT_ROOM_BOOKING_LOCATION] = ""
        locationName = root[_DEFAULT_ROOM_BOOKING_LOCATION]
        if not Location.parse(locationName) and len(Location.allLocations) > 0:
            # take the first available location as default
            locationName = Location.allLocations[0].friendlyName
            Location.setDefaultLocation(locationName)
        return Location.parse( locationName )

    @staticmethod
    def insertLocation( location ):
        _ensureZODBBranch()
        if not isinstance( location, Location ):
            raise 'location attribute must be of Location class'
        if Location.parse(location.friendlyName):
            # location with same name already exists
            return False
        root = MaKaC.common.DBMgr.getInstance().getDBConnection().root()
        locations = root[_ROOM_BOOKING_LOCATION_LIST]
        locations.append( location )
        root[_ROOM_BOOKING_LOCATION_LIST] = locations

    @staticmethod
    def removeLocation( locationName ):
        _ensureZODBBranch()
        if not isinstance( locationName, str ):
            raise 'locationName attribute must be string'
        root = MaKaC.common.DBMgr.getInstance().getDBConnection().root()
        locations = root[_ROOM_BOOKING_LOCATION_LIST]
        locations = [ loc for loc in locations if loc.friendlyName != locationName ]
        root[_ROOM_BOOKING_LOCATION_LIST] = locations

    @staticmethod
    def allFactories():
        """
        Returns list of Factory classes.

        Note, that many locations may use the same Factory (plugin).
        If you want the list of all locations, use Location.allLocations instead.
        """
        factories = []
        for location in Location.allLocations:
            if not location.factory in factories:
                factories.append( location.factory )
        return factories

    # Properties ============================================================

    class GetAllLocations( object ):
        def __get__( self, obj, cls = None ):
            _ensureZODBBranch()

            root = MaKaC.common.DBMgr.getInstance().getDBConnection().root()
            return root[_ROOM_BOOKING_LOCATION_LIST]

    allLocations = GetAllLocations()


    def getAVCSupportEmails( self ):
        """ Returns the list of AVC support e-mails. """
        return self._avcSupportEmails

    def setAVCSupportEmails( self, emailsList ):
        """ Sets the list of AVC support e-mails. """
        self._avcSupportEmails = emailsList

    def insertAVCSupportEmail( self, email ):
        """ Adds new AVC support email. """
        emailList = self._avcSupportEmails
        if email not in emailList:
            emailList.append( email )
        self._avcSupportEmails = emailList

    def removeAVCSupportEmail( self, email ):
        """ Removes existing AVC support email. """
        emailList = self._avcSupportEmails
        if email in emailList:
            emailList.remove( email )
        self._avcSupportEmails = emailList


"""
Here is THE place to register your plugin.

This is done in 3 steps. Let's assume your plugin name is "Foo".

1. Have your plugin in plugins/RoomBooking/Foo directory

2. Import your plugin factory class
       (
           Naming convention is FactoryName. Examples:
             * FactoryZODB  (represents built-in Indico plugin)
             * FactoryFoo
             * FactoryMyCoolPlugin
       )
   Do it with this command:
   from MaKaC.plugins.RoomBooking.Foo.factoryFoo import FactoryFoo

3. Add at least one Location that uses your plugin

   Main Indico database keeps list of all Locations available for
   room booking module. This list is kept in RoomBookingLocationList
   branch of the root.

   Initially the list looks like this:
   [ Location( "Universe", FactoryZODB ) ]

   So there is only one Location called 'Universe' (how nice),
   which uses built-in plugin 'ZODB' represented by factory FactoryZODB.

4. (optional) Update Indico web interface for plugin management to
   include your plugin. The page:
   http://localhost/indico/roomBookingPluginAdmin.py

   Your plugin will NOT appear there magically.


"""
#from MaKaC.plugins.RoomBooking.Alaska.factoryAlaska import FactoryAlaska



class ReservationGUID( Persistent, object ):
    """
    Reservation Globaly Unique ID.

    This is intented for cross-location (and cross-plugin!) reservation
    identification.
    Imagine a conference. For one conference there may be reservations in
    different locations. Therefore, Conference object will need a list of
    ReservationGUIDs.
    """
    location = None   # Location - determines the plugin
    id = None         # str - custom id, identifies object in external database

    def __init__( self, location, id ):
        """
        Initializes new instance with location:Location and id:int.
        """
        if not isinstance( location, Location ):
            raise 'location attribute must be of Location class'
        self.location = location
        self.id = id

    def __str__( self ):
        """
        Returns string representing reservation GUID.
        This string may be later parsed into ReservationGUID object.
        """
        s =  "%s  |  %s" % ( self.location.friendlyName, self.id )
        return s

    @staticmethod
    def parse( guidString ):
        """
        Parses guidString into ReservationGUID object.
        """
        # TODO: check if this code is used. self is not defined, so it will fail
        try:
            loc, id = guidString.split( "|" )
            loc = loc.strip(); id = int( id.strip() )
            self.location = Location.parse( loc )
            if not self.location: raise ''
            self.id = id
        except:
            raise guidString + ' - invalid ReservationGUID string'

    def getReservation( self ):
        """
        Returns reservation with this GUID.
        """
        if self.id == None:
            return None
        return CrossLocationQueries.getReservations(
            location = self.location.friendlyName, resvID = self.id )

class RoomGUID( Persistent, object ):
    """
    Room Globaly Unique ID.

    This is intented for cross-location (and cross-plugin!) room identification.
    """
    location = None   # Location - determines the plugin
    id = None         # str - custom id, identifies object in external database

    def __init__( self, location, id ):
        """
        Initializes new instance with location:Location and id:str.
        """
        if not isinstance( location, Location ):
            raise 'location attribute must be of Location class'
        self.location = location
        self.id = id

    def __str__( self ):
        """
        Returns string representing room GUID.
        This string may be later parsed into RoomGUID object.
        """
        s =  "%s  |  %s" % ( self.location.friendlyName, self.id )
        return s

    @staticmethod
    def parse( guidString ):
        """
        Parses guidString into RoomGUID object.
        """
        try:
            loc, id = guidString.split( "|" )
            loc = loc.strip();
            id = int( id.strip() )
            location = Location.parse( loc )
            if not location: raise 'Cannot parse location'
            return RoomGUID( location, id )
        except:
            raise guidString + ' - invalid RoomGUID string'

    def getRoom( self ):
        """
        Returns room with this GUID.
        """
        return CrossLocationQueries.getRooms(
            location = self.location.friendlyName, roomID = self.id )

class CrossLocationQueries( object ):
    """
    Enables performing _global_ queries, i.e. ask for all rooms in all
    locations (all plugins).

    Often actions are done on one location only.
    For example, when user submits new reservation of a room in CERN,
    it is clear that system will use only CERN plugin.

    However, sometimes we need to perform cross-location searches.
    I.e. we want to show all reservations associated with one Conference.
    """

    @staticmethod
    def getRooms( *args, **kwargs ):
        """
        Returns rooms from all locations, meeting specified conditions.
        (conditions are described in RoomBase.getRooms)

        Additional parameters:
        location - if specified (str), method will return only rooms
                   from this location.
        """
        location = kwargs.get( 'location' )
        if not location:
            # Return from all locations
            rooms = []
            for location in Location.allLocations:
                kwargs['location'] = location.friendlyName
                res = location.factory.newRoom().getRooms( **kwargs )
                if isinstance( res, list ): rooms.extend( res )
                else: rooms.append( res )
            return rooms
        else:
            # Return only from one location
            locObj = Location.parse( location )
            if locObj is None: return []
            rooms = locObj.factory.newRoom().getRooms( **kwargs )
            if rooms != None: return rooms
            else: return []

    @staticmethod
    def getReservations( *args, **kwargs ):
        """
        Returns reservations from all locations, meeting specified conditions.
        (conditions are described in ReservationBase.getReservations)
        """
        location = kwargs.get( 'location' )
        rooms = kwargs.get('rooms')
        if not location:
            myLocations = []
            if rooms:
                for room in rooms:
                    if Location.parse(room.locationName) not in myLocations:
                        myLocations.append(Location.parse(room.locationName))
            else:
                # Return from all locations
                myLocations = Location.allLocations
            resvs = []
            for location in myLocations:
                kwargs['location'] = location.friendlyName
                res = location.factory.newReservation().getReservations( **kwargs )
                if isinstance( res, list ): resvs.extend( res )
                else: resvs.append( res )
            return resvs
        else:
            # Return only from one location
            return Location.parse( location ).factory.newReservation().getReservations( **kwargs )

    @staticmethod
    def getCustomAttributesManager( locationName ):
        return Location.parse( locationName ).factory.getCustomAttributesManager()

    @staticmethod
    def getPossibleEquipment():
        """ Returns possible equipment list from all locations (set union)"""
        equipment = {}
        for location in Location.allLocations:
            for eq in location.factory.getEquipmentManager().getPossibleEquipment( location = location.friendlyName ):
                equipment[eq] = None
        v = equipment.keys()
        v.sort()
        return v

class CrossLocationFactory( object ):

    @staticmethod
    def newReservation( location ):
        return Location.parse( location ).factory.newReservation()


class CrossLocationDB( object ):
    """
    Enables performing global connect, disconnect,
    commit and rollback commands. It is used to manage
    all databases at once.

    Example: to perform cross-location searches, we need to
    connect to and disconnect from all backends.
    """

    @staticmethod
    def isConnected():
        """
        Returns true if request is connected to all
        room booking backends.
        """

        for factory in Location.allFactories():
            if not factory.getDALManager().connection:
                return False
        return True

    @staticmethod
    def connect():
        """
        Calls connect() on all plugins (backends).
        For documentation see DalManagerBase.
        """
        for factory in Location.allFactories():
            factory.getDALManager().connect()

    @staticmethod
    def disconnect():
        """
        Calls disconnect() on all plugins (backends).
        For documentation see DalManagerBase.
        """
        for factory in Location.allFactories():
            factory.getDALManager().disconnect()

    @staticmethod
    def commit():
        """
        Calls commit() on all plugins (backends).
        For documentation see DalManagerBase .
        """
        allFactories = Location.allFactories()
        for factory in allFactories:
            factory.getDALManager().commit()

    @staticmethod
    def rollback():
        """
        Calls rollback() on all plugins (backends).
        For documentation see DalManagerBase.
        """
        for factory in Location.allFactories():
            factory.getDALManager().rollback()

    @staticmethod
    def sync():
        """
        Calls sync() on all plugins (backends).
        For documentation see DalManagerBase.
        """
        for factory in Location.allFactories():
            factory.getDALManager().sync()

class Test:

    @staticmethod
    def PopulateRoomBookings():
        # TEMPORARY GENERATION OF RESERVATIONS FOR CONFERENCE

        from MaKaC.rb_dalManager import DALManagerBase
        DALManagerBase.connect()

        resvs = []
        #resvs.append( ReservationBase.getReservations( resvID = 395679 ) )
        #resvs.append( ReservationBase.getReservations( resvID = 394346 ) )
        #resvs.append( ReservationBase.getReservations( resvID = 377489 ) )
        #resvs.append( ReservationBase.getReservations( resvID = 384838 ) )

        resvGuids = []
        for resv in resvs:
            resvGuids.append( ReservationGUID( Location.getDefaultLocation(), resv.id ) )

        DALManagerBase.disconnect()

def connect2IndicoDB():
    from MaKaC.plugins.RoomBooking.CERN.dalManagerCERN import DALManagerCERN
    from MaKaC.common.db import DBMgr
    DBMgr.getInstance().startRequest()
    DALManagerCERN.connect()

def disconnectFromIndicoDB():
    from MaKaC.plugins.RoomBooking.CERN.dalManagerCERN import DALManagerCERN
    from MaKaC.common.db import DBMgr
    DALManagerCERN.disconnect()
    DBMgr.getInstance().endRequest()

def clean():
    import MaKaC.common.info as info
    connect2IndicoDB()

    minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
    minfo.setRoomBookingModuleActive( False )

    root = MaKaC.common.DBMgr.getInstance().getDBConnection().root()
    del root[_ROOM_BOOKING_LOCATION_LIST]

    disconnectFromIndicoDB()

if __name__ == '__main__':
    clean()
    pass
