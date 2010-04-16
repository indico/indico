# -*- coding: utf-8 -*-
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

from persistent import Persistent
from BTrees import LOBTree, OOBTree
from MaKaC.common.timezoneUtils import datetimeToUnixTimeInt, unixTimeToDatetime
from BTrees.Length import Length
from MaKaC.common.logger import Logger


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

    def iterBookingsPerConf(self, minDate = None, maxDate = None):
        """ Will return an iterator over tuples (date, {Conference: nBookings}) for
            events whose ending date is between minDate and maxDate
        """
        minKey = EventEndDateIndex._dateToKey(minDate)
        maxKey = EventEndDateIndex._dateToKey(maxDate)
        for key, bookingList in self._tree.iteritems(min = minKey, max = maxKey):
            yield (key, bookingList.getBookingsPerConf())

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

    def getBookingsPerConf(self):
        """ Returns a dictionary where the keys are Conference objects
            and the values are the number of Vidyo bookings of that conference.
        """
        result = {}
        for b in self._bookings:
            result[b.getConference()] = result.setdefault(b.getConference(), 0) + 1
        return result

