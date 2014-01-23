# -*- coding: utf-8 -*-
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

from persistent import Persistent
from BTrees import LOBTree, OOBTree
from MaKaC.common.timezoneUtils import datetimeToUnixTimeInt, unixTimeToDatetime
from BTrees.Length import Length
from MaKaC.common.logger import Logger
from MaKaC.conference import ConferenceHolder
from zope.interface import Interface
from indico.core.index import SIndex
from indico.core.index import Catalog

BOOKINGS_BY_VIDYO_ROOMS_INDEX = "BookingsByVidyoRoomIndex"

class EventEndDateIndex(Persistent):
    """ List of bookings ordered by their event's ending date
    """

    def __init__(self):
        self._tree = LOBTree.LOBTree()
        self._count = Length(0)

    ## private class methods ##
    @classmethod
    def _dateToKey(cls, date):
        if date:
            return datetimeToUnixTimeInt(date)
        else:
            return None

    @classmethod
    def _keyToDate(cls, key):
        if key:
            return unixTimeToDatetime(key)
        else:
            return None

    @classmethod
    def _bookingToKey(cls, booking):
        return cls._dateToKey(booking.getConference().getAdjustedEndDate(tz = 'UTC'))

    ## public instance methods ##
    def clear(self):
        """ Clears all the information stored
        """
        self._tree = LOBTree.LOBTree()
        self._count = Length(0)

    def getCount(self):
        """ Returns the number of bookings (not keys) stored
        """
        return self._count() #to get the value of a Length object, one has to "call" the object

    def indexBooking(self, booking):
        """ Stores a booking in the index
        """
        key = EventEndDateIndex._bookingToKey(booking)
        if not key in self._tree:
            self._tree[key] = DateBookingList()
        self._tree[key].addBooking(booking)
        self._count.change(1)

    def unindexBooking(self, booking):
        """ Removes a booking from the index
        """
        key = EventEndDateIndex._bookingToKey(booking)
        try:
            self._tree[key].removeBooking(booking)
            if self._tree[key].getCount() == 0:
                del self._tree[key]
            self._count.change(-1)
        except KeyError:
            Logger.get('Vidyo').warning("Could not unindex booking: (confId=%s, id=%s) from Vidyo's GlobalData. Tried with key: %s." %
                                            (booking.getConference().getId(), booking.getId(), str(key)))

    def moveBooking(self, booking, oldDate):
        """ Changes the position of a booking in the index
        """
        oldKey = EventEndDateIndex._dateToKey(oldDate)
        newKey = EventEndDateIndex._bookingToKey(booking)
        try:
            self._tree[oldKey].removeBooking(booking)
            if self._tree[oldKey].getCount() == 0:
                del self._tree[oldKey]
            if not newKey in self._tree:
                self._tree[newKey] = DateBookingList()
            self._tree[newKey].addBooking(booking)
        except KeyError:
            Logger.get('Vidyo').warning("Could not move booking: (confId=%s, id=%s) from Vidyo's GlobalData. Tried moving from key: %s to key: %s." %
                                            (booking.getConference().getId(), booking.getId(), str(oldKey), str(newKey)))

    def iterbookings(self, minDate = None, maxDate = None):
        """ Will return an iterator over Vidyo bookings attached to conferences whose
            end date is between minDate and maxDate
        """
        minKey = EventEndDateIndex._dateToKey(minDate)
        maxKey = EventEndDateIndex._dateToKey(maxDate)
        for bookingList in self._tree.itervalues(min = minKey, max = maxKey):
            for b in bookingList.iterbookings():
                yield b

    def deleteKeys(self, minDate = None, maxDate = None):
        """
        """
        minKey = EventEndDateIndex._dateToKey(minDate)
        maxKey = EventEndDateIndex._dateToKey(maxDate)
        for key in list(self._tree.keys(min = minKey, max = maxKey)): #we want a copy because we are going to modify
            self._deleteKey(key)

    def _deleteKey(self, key):
        Logger.get("Vidyo").info("Vidyo EventEndDateIndex: deleting key %s (%s)" % (str(key), str(EventEndDateIndex._keyToDate(key)) + " (UTC)"))
        self._count.change(-self._tree[key].getCount())
        del self._tree[key]

    def initialize(self, dbi=None):
        """ Cleans the indexes, and then indexes all the vidyo bookings from all the conferences
            WARNING: obviously, this can potentially take a while
        """
        i = 0
        self.clear()
        for conf in ConferenceHolder().getList():
            csbm = Catalog.getIdx("cs_bookingmanager_conference").get(conf.getId())
            for booking in csbm.getBookingList():
                if booking.getType() == "Vidyo" and booking.isCreated():
                    self.indexBooking(booking)
            i += 1
            if dbi and i % 100 == 0:
                dbi.commit()
        if dbi:
            dbi.commit()

class DateBookingList(Persistent):
    """ Simple set of booking objects with a count attribute.
    """

    def __init__(self):
        self._bookings = OOBTree.OOTreeSet()
        self._count = Length(0)

    def addBooking(self, booking):
        self._bookings.insert(booking)
        self._count.change(1)

    def removeBooking(self, booking):
        self._bookings.remove(booking)
        self._count.change(-1)

    def getCount(self):
        return self._count()

    def iterbookings(self):
        """ Iterator over the bookings
        """
        return self._bookings.__iter__()

class IIndexableByVidyoRoom(Interface):
    pass

class BookingsByVidyoRoomIndex(SIndex):
    _fwd_class = OOBTree.OOBTree
    _fwd_set_class = OOBTree.OOTreeSet

    def __init__(self):
        super(BookingsByVidyoRoomIndex, self).__init__(IIndexableByVidyoRoom)

    def getBookingList(self, key):
        return list(self.get(key, self._fwd_set_class()))

    def indexBooking(self, booking):
        self.index_obj(booking)

    def unindexBooking(self, booking):
        self.unindex_obj(booking)

    def initialize(self, dbi=None):
        """ Cleans the indexes, and then indexes all the vidyo bookings from all the conferences
            WARNING: obviously, this can potentially take a while
        """
        i = 0
        self.clear()
        for conf in ConferenceHolder().getList():
            idx = Catalog.getIdx("cs_bookingmanager_conference")
            if idx is None:
                idx = Catalog.create_idx("cs_bookingmanager_conference")
            csbm = idx.get(conf.getId())
            for booking in csbm.getBookingList():
                if booking.getType() == "Vidyo" and booking.isCreated():
                    self.indexBooking(booking)
            i += 1
            if dbi and i % 100 == 0:
                dbi.commit()
        if dbi:
            dbi.commit()

    def dump(self):
        return [(k, [b for b in self.get(k)]) for k in self.__iter__()]
