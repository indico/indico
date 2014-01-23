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

"""
Part of Room Booking Module (rb_)
Responsible: Piotr Wlodarek
"""

"""
Classes for uniform deeling with different locations,
global ids of objects, and cross-location queries.
"""

from persistent import Persistent
from zope.interface import Interface, implements

from MaKaC.common.Locators import Locator
from MaKaC.errors import MaKaCError
from MaKaC.i18n import _
from MaKaC.plugins import PluginLoader

from indico.util.i18n import i18nformat
from indico.core.index import IUniqueIdProvider
from indico.core.db import DBMgr


class IIndexableByManagerIds(Interface):
    pass


# ZODB branches name
_DEFAULT_ROOM_BOOKING_LOCATION = 'DefaultRoomBookingLocation'
_ROOM_BOOKING_LOCATION_LIST = 'RoomBookingLocationList'


def mapper(src, dest, properties):
    if isinstance(src, dict) and not isinstance(dest, dict):
        # map from dictionary keys to object attributes
        for prop in properties:
            setattr(dest, prop, src.get(prop, None))
    elif not isinstance(src, dict) and isinstance(dest, dict):
        # map from object attributes to dictionary keys
        for prop in properties:
            dest[prop] = getattr(src, prop, None)
    return dest

class MapAspect(Persistent, object):
    """
    Map aspect is a structure of data related to a view of a Google Map of rooms.
    The rooms that are specific to a certain location can be viewed from several aspects.
    A map aspect can be percieved as a combination of map coordinates and zoom level.
    """

    def __str__(self):
        s = i18nformat(""" _("Id"): """) + self.id + "\n"
        s += i18nformat(""" _("Name"): """) + self.name + "\n"
        return s

    def __cmp__(self, second):
        return cmp(self.id, second.id)

    id = None                    # str - aspects's ID
    name = None                  # str - aspects's name
    defaultOnStartup = False     # bool - is this aspect the default one on start-up
    centerLatitude = None        # str - the latitude of the aspects's perspective center
    centerLongitude = None       # str - the longitude of the aspects's perspective center
    zoomLevel = None             # str - the zoom level of the aspects's perspective
    topLeftLatitude = None       # str - the latitude of the aspects's left corner
    topLeftLongitude = None      # str - the longitude of the aspects's left corner
    bottomRightLatitude = None   # str - the latitude of the aspects's right corner
    bottomRightLongitude = None  # str - the longitude of the aspects's right corner

    __ATTRIBUTES = ['id', 'name', 'defaultOnStartup', 'centerLatitude', 'centerLongitude', 'zoomLevel',
                    'topLeftLatitude', 'topLeftLongitude', 'bottomRightLatitude', 'bottomRightLongitude']

    def toDictionary(self):
        return mapper(self, {}, MapAspect.__ATTRIBUTES)

    def updateFromDictionary(self, aspectDict):
        return mapper(aspectDict, self, MapAspect.__ATTRIBUTES)

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
        self._aspects = {}

    def __str__( self ):
        s = i18nformat(""" _("Location"): """) + self.friendlyName + "\n"
        s += i18nformat(""" _("Plugin"): """) + self.factory.__class__.__name__ + "\n"
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
        root = DBMgr.getInstance().getDBConnection().root()
        root[_DEFAULT_ROOM_BOOKING_LOCATION] = locationName
        from MaKaC.webinterface.rh.JSContent import RHGetVarsJs
        RHGetVarsJs.removeTmpVarsFile()

    @staticmethod
    def getDefaultLocation():
        root =DBMgr.getInstance().getDBConnection().root()
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
        if not isinstance( location, Location ):
            raise MaKaCError('location attribute must be of Location class')
        if Location.parse(location.friendlyName):
            # location with same name already exists
            return False
        root = DBMgr.getInstance().getDBConnection().root()
        locations = root[_ROOM_BOOKING_LOCATION_LIST]
        locations.append( location )
        root[_ROOM_BOOKING_LOCATION_LIST] = locations
        from MaKaC.webinterface.rh.JSContent import RHGetVarsJs
        RHGetVarsJs.removeTmpVarsFile()

    @staticmethod
    def removeLocation( locationName ):
        if not isinstance( locationName, str ):
            raise MaKaCError('locationName attribute must be string')
        root = DBMgr.getInstance().getDBConnection().root()
        locations = root[_ROOM_BOOKING_LOCATION_LIST]
        locations = [ loc for loc in locations if loc.friendlyName != locationName ]
        root[_ROOM_BOOKING_LOCATION_LIST] = locations
        from MaKaC.webinterface.rh.JSContent import RHGetVarsJs
        RHGetVarsJs.removeTmpVarsFile()

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

    # Aspects management ====================================================

    def addAspect(self, aspect):
        self.aspects[aspect.id] = aspect
        self._p_changed = 1

    def removeAspect(self, aspectId):
        del self.aspects[aspectId]
        self._p_changed = 1

    def getAspect(self, aspectId):
        return self.aspects[aspectId]

    def getAspects(self):
        return sorted(self.aspects.values())

    def _getAspects(self):
        if getattr(self, '_aspects', None) is None:
            self._aspects = {}
        return self._aspects

    def isMapAvailable(self):
        return len(self._getAspects()) > 0

    aspects = property(_getAspects)

    # Properties ============================================================

    class GetAllLocations( object ):
        def __get__( self, obj, cls = None ):

            root = DBMgr.getInstance().getDBConnection().root()
            return root.get(_ROOM_BOOKING_LOCATION_LIST, [])

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
            raise MaKaCError('location attribute must be of Location class')
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
        try:
            loc, id = guidString.split( "|" )
            loc = loc.strip(); id = int( id.strip() )
            location = Location.parse( loc )
            if not location:
                raise MaKaCError('invalid location')
            return ReservationGUID(location, id)
        except:
            raise MaKaCError(guidString + ' - invalid ReservationGUID string')

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

    implements(IUniqueIdProvider, IIndexableByManagerIds)

    location = None   # Location - determines the plugin
    id = None         # str - custom id, identifies object in external database

    def __init__( self, location, id ):
        """
        Initializes new instance with location:Location and id:str.
        """
        if not isinstance( location, Location ):
            raise MaKaCError('location attribute must be of Location class')
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
            if not location:
                raise MaKaCError('Cannot parse location')
            return RoomGUID( location, id )
        except:
            raise MaKaCError(guidString + ' - invalid RoomGUID string')

    def getRoom( self ):
        """
        Returns room with this GUID.
        """
        return CrossLocationQueries.getRooms(
            location = self.location.friendlyName, roomID = self.id )

    def __cmp__(self, obj):
        if not isinstance(obj, RoomGUID):
            return -1
        else:
            return cmp(str(self), str(obj))

    def getUniqueId( self ):
        return self

    def __conform__(self, proto):
        if proto == IIndexableByManagerIds:
            return list(m.getId() for m in self.getRoom().getAllManagers())



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
                    loc = Location.parse(room.locationName)
                    if loc not in myLocations:
                        myLocations.append(loc)
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
            if not factory.getDALManager().isConnected():
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
    from indico.core.db import DBMgr
    DBMgr.getInstance().startRequest()
    DALManagerCERN.connect()

def disconnectFromIndicoDB():
    from MaKaC.plugins.RoomBooking.CERN.dalManagerCERN import DALManagerCERN
    from indico.core.db import DBMgr
    DALManagerCERN.disconnect()
    DBMgr.getInstance().endRequest()

def clean():
    import MaKaC.common.info as info
    connect2IndicoDB()

    minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
    minfo.setRoomBookingModuleActive( False )

    root = DBMgr.getInstance().getDBConnection().root()
    del root[_ROOM_BOOKING_LOCATION_LIST]

    disconnectFromIndicoDB()

if __name__ == '__main__':
    clean()
    pass
