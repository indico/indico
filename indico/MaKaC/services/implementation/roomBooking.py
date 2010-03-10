"""
Asynchronous request handlers for room booking
"""

from MaKaC.services.implementation.base import ProtectedService

from MaKaC.rb_location import Location
from MaKaC.rb_location import CrossLocationQueries

class RoomBookingListLocations( ProtectedService ):

    def _getAnswer( self ):
        """
        Calls _handle() on the derived classes, in order to make it happen. Provides
        them with self._value.
        """

        result = {}

        locationNames = map(lambda l: l.friendlyName, Location.allLocations);

        for name in locationNames:
            result[name] = name;

        return result


class RoomBookingListRooms( ProtectedService ):

    def _checkParams( self ):

        try:
            self._location = self._params["location"];
        except:
            from MaKaC.services.interface.rpc.common import ServiceError
            raise ServiceError("ERR-RB0", "Invalid location.")

    def _getAnswer( self ):

        if not Location.parse( self._location ):
            return {}

        res = {}
        for room in CrossLocationQueries.getRooms( location = self._location ):
            res[room.name] = room.name

        return sorted(res)

class RoomBookingFullNameListRooms( RoomBookingListRooms):

    def _getAnswer( self ):

        res = {}

        if Location.parse( self._location ):
            for room in CrossLocationQueries.getRooms( location = self._location ):
                res[room.name] = room.getFullName()

        return list((k,res[k]) for k in sorted(res))

class RoomBookingListLocationsAndRooms( ProtectedService ):

    def _getAnswer( self ):
        result = {}
        locationNames = map(lambda l: l.friendlyName, Location.allLocations);
        for loc in locationNames:
            for room in CrossLocationQueries.getRooms( location = loc ):
                result[loc +":" +room.name] = loc +":" +room.name;
        return sorted(result)

class GetBookingBase(ProtectedService):

    def _getRoomInfo(self, target):
        location = target.getOwnLocation()

        if location:
            locName = location.getName()
            locAddress = location.getAddress()
        else:
            locName = None
            locAddress = None

        room = target.getOwnRoom()

        if room:
            roomName = room.getName()
        else:
            roomName = None

        return {'location': locName,
                'room': roomName,
                'address': locAddress}

    def _getAnswer(self):
        return self._getRoomInfo(self._target)
