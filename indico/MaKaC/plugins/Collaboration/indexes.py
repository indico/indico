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

from persistent import Persistent
from BTrees.OOBTree import OOBTree
from BTrees.IOBTree import IOBTree 
from MaKaC.common.logger import Logger
from MaKaC.common.timezoneUtils import unixTimeToDatetime,\
    datetimeToUnixTimeInt
from MaKaC.conference import ConferenceHolder, CategoryManager
from MaKaC.common.PickleJar import Retrieves, DictPickler
from datetime import datetime
from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools


class CollaborationIndex(Persistent):
    
    def __init__(self):
        self._indexes = OOBTree()
        
    def getAllBookingsIndex(self):
        return self.getIndex("all")
    
    def getIndex(self, name):
        try:
            return self._indexes[name]
        except KeyError:
            index = BookingsIndex(name)
            self._indexes[name] = index
            return index
        
    def getBookings(self, indexName, viewBy, orderBy, minKey, maxKey,
                    tz = 'UTC', onlyPending = False, conferenceId = None, categoryId = None,
                    pickle = False, dateFormat = None, page = None, resultsPerPage = None):
        
        if onlyPending:
            indexName += "_pending"
            
        reverse = orderBy == "descending"

        try:
            index = self.getIndex(indexName)
            totalInIndex = index.getCount()
            
            if categoryId and not CategoryManager().hasKey(categoryId) or conferenceId and not ConferenceHolder().hasKey(conferenceId):
                finalResult = QueryResult([], 0, 0, totalInIndex, 0)
            else:
                if viewBy == "conferenceTitle":
                    items, nBookings = index.getBookingsByConfTitle(minKey, maxKey, conferenceId, categoryId)
                elif viewBy == "conferenceStartDate":
                    items, nBookings = index.getBookingsByConfDate(minKey, maxKey, conferenceId, categoryId)
                else:
                    items, nBookings = index.getBookingsByDate(viewBy, minKey, maxKey, tz, conferenceId, categoryId, dateFormat)
                    
                if reverse:
                    items.reverse()
                    
                
                nGroups = len(items)
                    
                if page:
                    page = int(page)
                    if resultsPerPage:
                        resultsPerPage = int(resultsPerPage)
                    else:
                        resultsPerPage = 10
        
                    nPages = nGroups / resultsPerPage
                    if nGroups % resultsPerPage > 0:
                        nPages = nPages + 1
                    
                    if page > nPages:
                        finalResult = QueryResult([], 0, 0, totalInIndex, nPages)
                    else:
                        finalResult = QueryResult(items[(page - 1) * resultsPerPage : page * resultsPerPage], nBookings, nGroups, totalInIndex, nPages)
                        
                else:
                    finalResult = QueryResult(items, nBookings, nGroups, totalInIndex, 0)
            
        except KeyError:
            Logger.get("VideoServ").warning("Tried to retrieve index with name " + indexName + " but the index did not exist. Maybe no bookings have been added to it yet")
            finalResult = QueryResult([], 0, 0, 0)
            
        if pickle:
            return DictPickler.pickle(finalResult, tz)
        else:
            return finalResult
        
    def dump(self):
        return [(k, v.dump()) for k,v in self._indexes.iteritems()]
        
    def cleanAll(self):
        """ Wipes out everything
        """
        CollaborationIndex.__init__(self)
        for pluginInfo in CollaborationTools.getCollaborationPluginType().getOption("pluginsPerIndex").getValue():
            self._indexes[pluginInfo.getName()] = BookingsIndex(pluginInfo.getName())
        
    def indexAll(self):
        """ Indexes all the bookings from all the conferences
            WARNING: obviously, this can potentially take a while
        """
        for conf in ConferenceHolder().getList():
            csbm = conf.getCSBookingManager()
            #note: probably not the most efficient implementation since _indexBooking is getting the list
            #      of indexes where each booking should be indexed on every iteration 
            for booking in csbm.getBookingList():
                csbm._indexBooking(booking)
        
    def reindexAll(self):
        """ Cleans the indexes, and then indexes all the bookings from all the conferences
            WARNING: obviously, this can potentially take a while
        """
        self.cleanAll()
        self.indexAll()

class BookingsIndex(Persistent):
    
    def __init__( self, name ):
        self._name = name
        
        self._creationDateIndex = BookingDateIndex(name + "_creationDate")
        self._modificationDateIndex = BookingDateIndex(name + "_modificationDate")
        self._startDateIndex = BookingDateIndex(name + "_startDate")
        self._confTitleIndex = BookingConferenceIndex(name + "_conferenceTitle")
        self._conferenceStartDateIndex = BookingConferenceIndex(name + "_conferenceStartDate")
        
    def getName(self):
        return self._name
        
    def getCount(self):
        return self._creationDateIndex.getNumberOfBookings()

    def indexBooking(self, booking):
        self._creationDateIndex.indexBooking(booking, booking.getCreationDateTimestamp())
        self._modificationDateIndex.indexBooking(booking, booking.getModificationDateTimestamp())
        if booking.hasStartDate():
            self._startDateIndex.indexBooking(booking, booking.getStartDateTimestamp())
        conference = booking.getConference()
        if conference:
            self._confTitleIndex.indexBooking(booking, conference, BookingsIndex._conferenceToKeyTitle(conference))
            self._conferenceStartDateIndex.indexBooking(booking, conference, BookingsIndex._conferenceToKeyStartDate(conference))
        
    def unindexBooking(self, booking):
        self._creationDateIndex.unindexBooking(booking, booking.getCreationDateTimestamp())
        self._modificationDateIndex.unindexBooking(booking, booking.getModificationDateTimestamp())
        if booking.hasStartDate():
            self._startDateIndex.unindexBooking(booking, booking.getStartDateTimestamp())
        conference = booking.getConference()
        if conference:
            self._confTitleIndex.unindexBooking(booking, BookingsIndex._conferenceToKeyTitle(conference))
            self._conferenceStartDateIndex.unindexBooking(booking, BookingsIndex._conferenceToKeyStartDate(conference))
        
    def changeEventTitle(self, booking, oldTitle, newTitle):
        conference = booking.getConference()
        confId = conference.getId()
        self._confTitleIndex.unindexBooking(booking, BookingsIndex._conferenceToKeyTitle(title = oldTitle, id = confId))
        self._confTitleIndex.indexBooking(booking, conference, BookingsIndex._conferenceToKeyTitle(title = newTitle, id = confId))
        
    def changeModificationDate(self, booking, oldDate, newDate):
        oldTimestamp = datetimeToUnixTimeInt(oldDate)
        newTimestamp = datetimeToUnixTimeInt(newDate)
        self._modificationDateIndex.unindexBooking(booking, oldTimestamp)
        self._modificationDateIndex.indexBooking(booking, newTimestamp)
        
    def changeStartDate(self, booking, oldDate, newDate):
        oldTimestamp = datetimeToUnixTimeInt(oldDate)
        newTimestamp = datetimeToUnixTimeInt(newDate)
        self._startDateIndex.unindexBooking(booking, oldTimestamp)
        self._startDateIndex.indexBooking(booking, newTimestamp)
        
    def changeConfStartDate(self, booking, oldDate, newDate):
        oldTimestamp = datetimeToUnixTimeInt(oldDate)
        newTimestamp = datetimeToUnixTimeInt(newDate)
        conference = booking.getConference()
        conferenceId = booking.getConference().getId()
        
        oldKey = str(oldTimestamp) + '_' + conferenceId
        newKey = str(newTimestamp) + '_' + conferenceId 
        
        self._conferenceStartDateIndex.unindexBooking(booking, oldKey)
        self._conferenceStartDateIndex.indexBooking(booking, conference, newKey)
        
    def getBookingsByDate(self, viewBy, fromDate = None, toDate = None, tz = 'UTC',
                                conferenceId = None, categoryId = None, dateFormat = None):
        index = self._getIndexByName(viewBy)
        return index.getBookingsBetween(fromDate, toDate, tz, conferenceId, categoryId, dateFormat)
    
    def getBookingsByConfTitle(self, fromTitle = None, toTitle = None,
                                     conferenceId = None, categoryId = None):
        return self._confTitleIndex.getBookings(fromTitle, toTitle, conferenceId, categoryId)
    
    def getBookingsByConfDate(self, fromDate = None, toDate = None, conferenceId = None, categoryId = None):
        if fromDate:
            minKey = str(datetimeToUnixTimeInt(fromDate))
        else:
            minKey = None
        if toDate:
            maxKey = str(datetimeToUnixTimeInt(toDate)) + 'a' # because '_' < 'a' is True
        else:
            maxKey = None
        return self._conferenceStartDateIndex.getBookings(minKey, maxKey, conferenceId, categoryId)
    
    def dump(self):
        return {"creationDate": self._creationDateIndex.dump(),
                "modificationDate": self._modificationDateIndex.dump(),
                "startDate": self._startDateIndex.dump(),
                "confTitle": self._confTitleIndex.dump(),
                "confStartDate": self._conferenceStartDateIndex.dump() }
        
    def _getIndexByName(self, indexName):
        """ indexName should be: "creationDate", "modificationDate", "startDate"
        """
        return getattr(self, '_'+indexName+'Index')
    
    @classmethod
    def _conferenceToKeyTitle(cls, conference = None, title = None, id = None):
        if conference:
            return conference.getTitle().lower() + '_' + conference.getId()
        else:
            return title.lower() + '_' + id
    
    @classmethod
    def _conferenceToKeyStartDate(cls, conference):
        return str(datetimeToUnixTimeInt(conference.getStartDate())) + '_' + conference.getId()
        
        
class BookingDateIndex(Persistent):
    
    def __init__(self, name):
        self._tree = IOBTree()
        self._name = name
        self._numberOfBookings = 0
        
    def getName(self):
        return self._name
    
    def getNumberOfBookings(self):
        return self._numberOfBookings
    
    def indexBooking(self, booking, timestamp):
        if timestamp:
            if not timestamp in self._tree:
                self._tree[timestamp] = set()
            self._tree[timestamp].add(booking)
            self._tree._p_changed = 1
            self._numberOfBookings = self._numberOfBookings +  1
            
    
    def unindexBooking(self, booking, timestamp):
        if timestamp:
            if timestamp in self._tree:
                try:
                    self._tree[timestamp].remove(booking)
                    self._numberOfBookings = self._numberOfBookings - 1
                    if self._tree[timestamp]: #set is empty
                        self._tree._p_changed = 1
                    else:
                        del self._tree[timestamp]
                except KeyError:
                    Logger.get('VideoServ').warning("Tried to unindex booking: (confId=%s, id=%s) with key=%s from BookingDateIndex %s, but the booking was not present in the set of bookings with key %s"%
                                                    (booking.getConference().getId(), booking.getId(), str(timestamp), self.getName(), str(timestamp)))
                    self._deepUnindexBooking(booking, timestamp)
            else:
                Logger.get('VideoServ').warning("Tried to unindex booking: (confId=%s, id=%s) with key=%s from BookingDateIndex %s, but %s was not present"%
                                                (booking.getConference().getId(), booking.getId(), str(timestamp), self.getName(), str(timestamp)))
                self._deepUnindexBooking(booking, timestamp)
                
    def _deepUnindexBooking(self, booking, timestamp):
        found = False
        for key in list(self._tree.keys()):
            bookingSet = self._tree[key]
            if booking in bookingSet:
                bookingSet.remove(booking)
                self._numberOfBookings = self._numberOfBookings - 1
                found = True
                Logger.get('VideoServ').warning("Success in deep unindexing booking: (confId=%s, id=%s) with key=%s from BookingDateIndex %s, but %s was not present"%
                                                (booking.getConference().getId(), booking.getId(), str(key), self.getName(), str(timestamp)))
            if bookingSet:
                self._tree._p_changed = 1
            else:
                del self._tree[key]
        if not found:
            Logger.get('VideoServ').warning("Could not deep unindex booking: (confId=%s, id=%s) from BookingDateIndex %s (should have had key: %s)"%
                                            (booking.getConference().getId(), booking.getId(), self.getName(), str(timestamp)))
        
    
    def getBookingsBetween(self, fromDate, toDate, tz = 'UTC', conferenceId = None, categoryId = None, dateFormat = None):
        if fromDate:
            fromDate = datetimeToUnixTimeInt(fromDate)
        if toDate:
            toDate = datetimeToUnixTimeInt(toDate)
        return self._getBookingsBetweenTimestamps(fromDate, toDate, tz, conferenceId, categoryId, dateFormat)
        
    def _getBookingsBetweenTimestamps(self, fromDate, toDate,
                                      tz = 'UTC', conferenceId = None, categoryId = None, dateFormat = None):
        
        bookings = []
        nBookings = 0
        
        date = None
        bookingsForDate = None
        
        for timestamp, s in self._tree.iteritems(fromDate, toDate):
            currentDate = unixTimeToDatetime(timestamp, tz).date()
            
            if date != currentDate:
                if date is not None and bookingsForDate:
                    bookings.append((datetime.strftime(date, dateFormat), bookingsForDate))
                    nBookings += len(bookingsForDate)
                date = currentDate
                bookingsForDate = []
            
            if conferenceId:
                for booking in s:
                    if booking.getConference().getId() == conferenceId:
                        bookingsForDate.append(booking)
            elif categoryId:
                cc = CategoryChecker(categoryId)
                for booking in s:
                    if cc.check(booking.getConference()):
                        bookingsForDate.append(booking)
            else:
                bookingsForDate.extend(s)
            
        if date is not None and bookingsForDate:
            bookings.append((datetime.strftime(date, dateFormat), bookingsForDate))
            nBookings += len(bookingsForDate)
                
        return bookings, nBookings
                
    def dump(self):
        return [(k, [_bookingToDump(b) for b in s]) for k, s in self._tree.iteritems()]
            
    
class BookingConferenceIndex(Persistent):
    
    def __init__(self, name):
        self._tree = OOBTree()
        self._name = name
        self._numberOfBookings = 0
        
    def getName(self):
        return self._name
    
    def getNumberOfBookings(self):
        return self._numberOfBookings
    
    def indexBooking(self, booking, conference, key):
        if not key in self._tree:
            self._tree[key] = (conference, set())
        self._tree[key][1].add(booking)
        self._tree._p_changed = 1
        self._numberOfBookings = self._numberOfBookings + 1
        
    
    def unindexBooking(self, booking, key):
        if key in self._tree:
            try:
                self._tree[key][1].remove(booking)
                self._numberOfBookings = self._numberOfBookings - 1
                if self._tree[key][1]:
                    self._tree._p_changed = 1
                else:
                    del self._tree[key]
            except KeyError, e:
                Logger.get('VideoServ').warning("Tried to unindex booking: (confId=%s, id=%s) with key=%s from BookingConferenceIndex %s, but the booking was not present in the set of bookings with key %s. Exception: %s"%(booking.getConference().getId(), booking.getId(), str(key), self.getName(), str(key), str(e)))
                self._deepUnindexBooking(booking, key)
        else:
            Logger.get('VideoServ').warning("Tried to unindex booking: (confId=%s, id=%s) with key=%s from BookingConferenceIndex %s, but %s was not present"%(booking.getConference().getId(), booking.getId(), str(key), self.getName(), str(key)))
            self._deepUnindexBooking(booking, key)
                
    def _deepUnindexBooking(self, booking, bookingKey):
        found = False
        for key in list(self._tree.keys()):
            value = self._tree[key]
            if booking in value[1]:
                value[1].remove(booking)
                self._numberOfBookings = self._numberOfBookings - 1
                found = True
                Logger.get('VideoServ').warning("Success in deep unindexing booking: (confId=%s, id=%s) with key=%s from BookingConferenceIndex %s, but %s was not present"%
                                (booking.getConference().getId(), booking.getId(), str(key), self.getName(), str(bookingKey)))
            if value[1]:
                self._tree._p_changed = 1
            else:
                del self._tree[key]
        if not found:
            Logger.get('VideoServ').warning("Could not deep unindex booking: (confId=%s, id=%s) from BookingConferenceIndex %s (should have had key: %s)"%
                                            (booking.getConference().getId(), booking.getId(), self.getName(), str(bookingKey)))
     
    def getBookings(self, fromTitle = None, toTitle = None, conferenceId = None, categoryId = None):
        
        if fromTitle:
            fromTitle = fromTitle.lower()
        if toTitle:
            toTitle = toTitle.lower()
        
        result = []
        nBookings = 0
        
        if conferenceId:
            for conference, s in self._tree.itervalues(fromTitle, toTitle):
                if conference.getId() == conferenceId:
                    result.append((conference,s))
                    nBookings += len(s)
            
        elif categoryId:
            cc = CategoryChecker(categoryId)
            for conference, s in self._tree.itervalues(fromTitle, toTitle):
                if cc.check(conference):
                    result.append((conference,s))
                    nBookings += len(s)
                    
        else:
            for conference, s in self._tree.itervalues(fromTitle, toTitle):
                result.append((conference,s))
                nBookings += len(s)
                    
        return result, nBookings
                
    def dump(self):
        return [(k, [_bookingToDump(b) for b in s[1]]) for k, s in self._tree.iteritems()]
        

class CategoryChecker(object):
    """ Tries to check if a conference belongs to a category (recursively),
        while keeping a cache of previously visited categories to avoid DB requests
    """
    
    def __init__(self, targetCategoryId):
        self._target = targetCategoryId
        self._homeId = CategoryManager().getRoot().getId()
        self._goodConfs = set()
        self._badConfs = set()
        self._goodCategs = set()
        self._badCategs = set()
        
    def setTarget(self, targetCategoryId):
        self._target = targetCategoryId
        
    def reset(self):
        self._goodConfs.clear()
        self._badConfs.clear()
        self._goodCategs.clear()
        self._badCategs.clear()
    
    def check(self, conference):
        confId = conference.getId()
        if confId in self._goodConfs:
            return True
        elif confId in self._badConfs:
            return False
        else:
            category = conference.getOwner()
            categoryId = category.getId()
            isGoodCateg = categoryId in self._goodCategs
            isBadCateg = categoryId in self._badCategs
            l = [categoryId]
            
            while (not isGoodCateg and not isBadCateg and
                   categoryId != self._target and categoryId != self._homeId):
                category = category.getOwner()
                categoryId = category.getId()
                isGoodCateg = categoryId in self._goodCategs
                isBadCateg = categoryId in self._badCategs
                l.append(categoryId)
                
            if isGoodCateg or categoryId == self._target:
                self._goodConfs.add(confId)
                self._goodCategs.update(l)
                return True
            else:
                self._badConfs.add(confId)
                self._badCategs.update(l)
                return False


class IndexInformation(Persistent):
    """ Represents the information about one of the 'indexes' that the user can see in the interface.
        They are not related to the Index objects defined above; one IndexInformation can correspond
        to many of these objects.
    """
    
    def __init__(self, name):
        self._name = name
        self._plugins = []
        self._hasShowOnlyPending = False
        self._hasViewByStartDate = False
    
    @Retrieves(['MaKaC.plugins.Collaboration.indexes.IndexInformation'], 'name')
    def getName(self):
        return self._name
    
    def addPlugin(self, pluginName):
        self._plugins.append(pluginName)
        self._p_changed = 1
        
    @Retrieves(['MaKaC.plugins.Collaboration.indexes.IndexInformation'], 'plugins')
    def getPlugins(self):
        return self._plugins
    
    def setHasShowOnlyPending(self, value):
        self._hasShowOnlyPending = value
        
    @Retrieves(['MaKaC.plugins.Collaboration.indexes.IndexInformation'], 'hasShowOnlyPending')
    def hasShowOnlyPending(self):
        return self._hasShowOnlyPending
    
    def setHasViewByStartDate(self, value):
        self._hasViewByStartDate = value
        
    @Retrieves(['MaKaC.plugins.Collaboration.indexes.IndexInformation'], 'hasViewByStartDate')
    def hasViewByStartDate(self):
        return self._hasViewByStartDate
    
    def __str__(self):
        return "".join(["<u>",
                        self._name,
                        ":</u>",
                        ". <em>Plugins:</em> [",
                        ", ".join(self._plugins),
                        "], <em>Start date:</em> ",
                        "<strong>",
                        str(self._hasViewByStartDate),
                        "</strong>",
                        ", <em>Show only pending:</em> ",
                        "<strong>",
                        str(self._hasShowOnlyPending),
                        "</strong>"
                        ])
        
class QueryResult(object):
    def __init__(self, results, nBookings, nGroups, totalInIndex, nPages):
        self._results = results
        self._nBookings = nBookings
        self._nGroups = nGroups
        self._totalInIndex = totalInIndex
        self._nPages = nPages
        
    @Retrieves(['MaKaC.plugins.Collaboration.indexes.QueryResult'], 'results', isPicklableObject = True)
    def getResults(self):
        return self._results
    
    @Retrieves(['MaKaC.plugins.Collaboration.indexes.QueryResult'], 'nBookings')
    def getNumberOfBookings(self):
        return self._nBookings
    
    @Retrieves(['MaKaC.plugins.Collaboration.indexes.QueryResult'], 'nGroups')
    def getNumberOfGroups(self):
        return self._nGroups
    
    @Retrieves(['MaKaC.plugins.Collaboration.indexes.QueryResult'], 'totalInIndex')
    def getTotalInIndex(self):
        return self._totalInIndex
    
    @Retrieves(['MaKaC.plugins.Collaboration.indexes.QueryResult'], 'nPages')
    def getNPages(self):
        return self._nPages
    
    
def _bookingToDump(booking):
        result = []
        conference = booking.getConference()
        if conference:
            result.append('c')
            result.append(conference.getId())
            result.append('_')
        result.append('b')
        result.append(booking.getId())
        result.append('_t')
        result.append(booking.getType())
        return "".join(result)
