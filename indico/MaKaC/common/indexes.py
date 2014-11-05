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

"""This file contains various indexes which will be used in the system in order
    to optimise some functionalities.
"""
from datetime import datetime, timedelta
import itertools

from BTrees.IOBTree import IOBTree
from BTrees.OOBTree import OOBTree, OOSet
from persistent import Persistent
from pytz import timezone
from zope.index.text import textindex

from MaKaC.common.ObjectHolders import ObjectHolder
from MaKaC.common.timezoneUtils import date2utctimestamp, datetimeToUnixTime
from MaKaC.errors import MaKaCError
from MaKaC.common.logger import Logger
from MaKaC.plugins.base import extension_point

from indico.util.string import remove_accents

# BTrees are 32 bit by default
# TODO: make this configurable
# 0111 111 .... max signed int
BTREE_MAX_INT = 0x7FFFFFFF
BTREE_MIN_INT = -0x80000000
BTREE_MAX_UTC_DATE = timezone('UTC').localize(datetime.fromtimestamp(BTREE_MAX_INT))
BTREE_MIN_UTC_DATE = timezone('UTC').localize(datetime.fromtimestamp(BTREE_MIN_INT))


class Index(Persistent):
    _name = ""

    def __init__( self, name='' ):
        if name != '':
            self._name = name
        self._words = {}

    def getLength( self ):
        """ Length of an index.

        May be extremely slow for big indexes stored as persistent objects.
        Do not use unless you really have to!

        """
        return len(self._words.keys())

    def getKeys( self ):
        return self._words.keys()

    def getBrowseIndex( self ):
        letters = []
        words = self.getKeys()
        for word in words:
            uletter = remove_accents(word.decode('utf-8').lower()[0])
            if not uletter in letters:
                letters.append(uletter)
        letters.sort()
        return letters

    def _addItem( self, value, item ):
        if value != "":
            words = self._words
            if words.has_key(value):
                if item not in words[value]:
                    words[value].append(item)
            else:
                words[value] = [ item ]
            self.setIndex(words)

    def _withdrawItem( self, value, item ):
        if self._words.has_key(value):
            if item in self._words[value]:
                words = self._words
                words[value].remove(item)
                self.setIndex(words)

    def matchFirstLetter(self, letter, accent_sensitive=True):
        result = []

        cmpLetter = letter.lower()
        if not accent_sensitive:
            cmpLetter = remove_accents(cmpLetter)

        for key in self.getKeys():
            uletter = key.decode('utf8')[0].lower()
            if not accent_sensitive:
                uletter = remove_accents(uletter)
            if uletter == cmpLetter:
                result += self._words[key]

        return result

    def _match(self, value, cs=1, exact=1, accent_sensitive=True):
        # if match is exact, retrieve directly from index
        if exact == 1 and cs == 1 and accent_sensitive:
            if value in self._words and len(self._words[value]) != 0:
                if '' in self._words[value]:
                    self._words[value].remove('')
                return self._words[value]
            else:
                return None
        else:
            result = []
            cmpValue = value
            if not accent_sensitive:
                cmpValue = remove_accents(cmpValue)
            if cs == 0:
                cmpValue = cmpValue.lower()

            for key in self._words.iterkeys():
                if len(self._words[key]) != 0:
                    cmpKey = key
                    if not accent_sensitive:
                        cmpKey = remove_accents(cmpKey)
                    if cs == 0:
                        cmpKey = cmpKey.lower()
                    if (exact == 0 and cmpKey.find(cmpValue) != -1) or (exact == 1 and cmpKey == cmpValue):
                        if '' in self._words[key]:
                            self._words[key].remove('')
                        result = result + self._words[key]
            return result

    def dump(self):
        return self._words

    def setIndex(self, words):
        self._words = words

    def notifyModification(self):
        self._p_changed = 1


class EmailIndex(Index):
    _name = "email"

    def indexUser(self, user):
        for email in user.getEmails():
            self._addItem(email, user.getId())

    def unindexUser(self, user):
        for email in user.getEmails():
            self._withdrawItem(email, user.getId())

    def matchUser(self, email, cs=0, exact=0, accent_sensitive=True):
        """this match is an approximative case insensitive match"""
        return self._match(email, cs, exact)


class NameIndex(Index):
    _name = "name"

    def indexUser(self, user):
        name = user.getName()
        self._addItem(name, user.getId())

    def unindexUser(self, user):
        name = user.getName()
        self._withdrawItem(name, user.getId())

    def matchUser(self, name, cs=0, exact=0, accent_sensitive=False):
        """this match is an approximative case insensitive match"""
        return self._match(name, cs, exact, accent_sensitive)


class SurNameIndex(Index):
    _name = "surName"

    def indexUser(self, user):
        surName = user.getSurName()
        self._addItem(surName, user.getId())

    def unindexUser(self, user):
        surName = user.getSurName()
        self._withdrawItem(surName, user.getId())

    def matchUser(self, surName, cs=0, exact=0, accent_sensitive=False):
        """this match is an approximative case insensitive match"""
        return self._match(surName, cs, exact, accent_sensitive)


class OrganisationIndex(Index):
    _name = "organisation"

    def indexUser(self, user):
        org = user.getOrganisation()
        self._addItem(org, user.getId())

    def unindexUser(self, user):
        org = user.getOrganisation()
        self._withdrawItem(org, user.getId())

    def matchUser(self, org, cs=0, exact=0, accent_sensitive=False):
        return self._match(org, cs, exact, accent_sensitive)


class StatusIndex(Index):
    _name = "status"

    def __init__(self):
        Index.__init__(self)
        from MaKaC.user import AvatarHolder
        ah = AvatarHolder()
        for av in ah.getList():
            self.indexUser(av)

    def indexUser(self, user):
        status = user.getStatus()
        self._addItem(status, user.getId())

    def unindexUser(self, user):
        status = user.getStatus()
        self._withdrawItem(status, user.getId())

    def matchUser(self, status, cs=0, exact=1, accent_sensitive=True):
        """this match is an approximative case insensitive match"""
        return self._match(status, cs, exact)


class GroupIndex(Index):
    _name = "group"

    def indexGroup(self, group):
        name = group.getName()
        self._addItem(name, group.getId())

    def unindexGroup(self, group):
        name = group.getName()
        self._withdrawItem(name, group.getId())

    def matchGroup(self, name, cs=0, exact=0):
        if name == "":
            return []
        return self._match(name, cs, exact)


class CategoryIndex(Persistent):

    def __init__( self ):
        self._idxCategItem = OOBTree()

    def dump(self):
        return list(self._idxCategItem.items())

    def _indexConfById(self, categid, confid):
        # only the more restrictive setup is taken into account
        categid = str(categid)
        if self._idxCategItem.has_key(categid):
            res = self._idxCategItem[categid]
        else:
            res = []
        res.append(confid)
        self._idxCategItem[categid] = res

    def unindexConf(self, conf):
        confid = str(conf.getId())
        self.unindexConfById(confid)

    def unindexConfById(self, confid):
        for categid in self._idxCategItem.keys():
            if confid in self._idxCategItem[categid]:
                res = self._idxCategItem[categid]
                res.remove(confid)
                self._idxCategItem[categid] = res

    def reindexCateg(self, categ):
        for subcat in categ.getSubCategoryList():
            self.reindexCateg(subcat)
        for conf in categ.getConferenceList():
            self.reindexConf(conf)

    def reindexConf(self, conf):
        self.unindexConf(conf)
        self.indexConf(conf)

    def indexConf(self, conf):
        categs = conf.getOwnerPath()
        level = 0
        for categ in conf.getOwnerPath():
            if conf.getFullVisibility() > level:
                self._indexConfById(categ.getId(),conf.getId())
            level+=1
        if conf.getFullVisibility() > level:
            self._indexConfById("0",conf.getId())

    def getItems(self, categid):
        categid = str(categid)
        if self._idxCategItem.has_key(categid):
            return self._idxCategItem[categid]
        else:
            return []

    def _check(self, dbi=None):
        """
        Performs some sanity checks
        """
        i = 0
        from MaKaC.conference import ConferenceHolder
        confIdx = ConferenceHolder()._getIdx()

        for cid, confs in self._idxCategItem.iteritems():
            for confId in confs:
                # it has to be in the conference holder
                if confId not in confIdx:
                    yield "[%s] '%s' not in ConferenceHolder" % (cid, confId)
                # the category has to be one of the owners
                elif cid not in (map(lambda x:x.id, ConferenceHolder().getById(confId).getOwnerPath()) + ['0']):
                    yield "[%s] Conference '%s' is not owned" % (cid, confId)
            if dbi and i % 100 == 99:
                dbi.sync()
            i += 1


class CalendarIndex(Persistent):
    """Implements a persistent calendar-like index. Objects (need to implement
        the __hash__ method) with a starting and ending dates can be added to
        the index so it's faster and esaier to perform queries in order to
        fetch objects which are happening wihtin a given date. Indexing and
        unindexing of objects must be explicitely notified by index handlers
        i.e. these objects won't be updated when the starting or ending dates
        are changed.

       Atttributes:
        idxSDate - (IOBTree) Inverted index containing all the objects which
            are starting on a certain date.
        idxEDate - (IOBTree) Inverted index containing all the objects which
            are ending on a certain date.
    """
    def __init__( self ):
        self._idxSdate = IOBTree()
        self._idxEdate = IOBTree()

    def getIdxSdate( self ):
        return self._idxSdate

    def getIdxEdate( self ):
        return self._idxEdate

    def dump(self):
        return list(self._idxSdate.items())+list(self._idxEdate.items())

    def indexConf(self, conf):
        """Adds an object to the index for the specified starting and ending
            dates.

           Parameters:
            conf - (Conference) Object to be indexed.
        """
        confid   = conf.getId()
        sdate = date2utctimestamp(conf.getStartDate())
        edate = date2utctimestamp(conf.getEndDate())
        #checking if 2038 problem occurs
        if sdate > BTREE_MAX_INT or edate > BTREE_MAX_INT:
            return
        if self._idxSdate.has_key( sdate ):
            res = self._idxSdate[sdate]
        else:
            res = []
        if not confid in res:
            res.append(confid)
            self._idxSdate[sdate] = res
        if self._idxEdate.has_key( edate ):
            res = self._idxEdate[edate]
        else:
            res = []
        if not confid in res:
            res.append(confid)
            self._idxEdate[edate] = res

    def unindexConf( self, conf):
        """Removes the given object from the index for the specified starting
            and ending dates. If the object is not indexed at any of the
            2 values the operation won't be executed.

           Raises:
            Exception - the specified object is not indexed at the specified
                    dates

           Parameters:
            conf - (Conference) Object to be removed from the index.
            sdate - (datetime) Starting date at which the object is indexed.
            edate - (datetime) [optional] Ending date at which the object
                is indexed. If it is not specified the starting date will be
                used as ending one.
        """
        confid = conf.getId()
        sdate = date2utctimestamp(conf.getStartDate())
        edate = date2utctimestamp(conf.getEndDate())
        #checking if 2038 problem occurs
        if sdate > BTREE_MAX_INT or edate > BTREE_MAX_INT:
            return
        if not self._idxSdate.has_key( sdate ):
            for key in self._idxSdate.keys():
                res = self._idxSdate[key]
                while confid in res:
                    res.remove(confid)
                    self._idxSdate[key] = res
                    if len(self._idxSdate[key]) == 0:
                        del self._idxSdate[key]
        else:
            while confid in self._idxSdate[sdate]:
                res = self._idxSdate[sdate]
                res.remove(confid)
                self._idxSdate[sdate] = res
            if len(self._idxSdate[sdate]) == 0:
                del self._idxSdate[sdate]
        if not self._idxEdate.has_key( edate ):
            for key in self._idxEdate.keys():
                res = self._idxEdate[key]
                while confid in res:
                    res.remove(confid)
                    self._idxEdate[key] = res
                    if len(self._idxEdate[key]) == 0:
                        del self._idxEdate[key]
        else:
            while confid in self._idxEdate[edate]:
                res = self._idxEdate[edate]
                res.remove(confid)
                self._idxEdate[edate] = res
            if len(self._idxEdate[edate]) == 0:
                del self._idxEdate[edate]

    def _getObjectsStartingBefore( self, date ):
        """Returns all the objects starting before the specified day (excluded).

           Parameters:
            date - (tz aware datetime) Date for which all the indexed objects starting
                before have to be fecthed and returned.
           Returns:
            (Set) - set of objects starting before the specified day
        """
        date = date2utctimestamp(date)
        res = set()
        for val in self._idxSdate.values(self._idxSdate.minKey(), date):
            res.update( set( val ) )
        return res

    def _getObjectsStartingAfter( self, date ):
        """Returns all the objects starting after the specified day (excluded).

           Parameters:
            date - (tz aware datetime) Date for which all the indexed objects starting
                after have to be fecthed and returned.
           Returns:
            (Set) - set of objects starting before the specified day
        """
        date = date2utctimestamp(date)
        res = set()
        for val in self._idxSdate.values(date):
            res.update( set( val ) )
        return res

    def _getObjectsEndingBefore( self, date ):
        """Returns all the objects ending before the specified day (excluded).

           Parameters:
            date - (tz aware datetime) Date for which all the indexed objects ending
                before have to be fecthed and returned.
           Returns:
            (Set) - set of objects ending before the specified day
        """
        date = date2utctimestamp(date)
        res = set()
        for val in self._idxEdate.values(self._idxEdate.minKey(), date):
            res.update( set( val ) )
        return res

    def _getObjectsEndingAfter( self, date ):
        """Returns all the objects ending after the specified day (included).

           Parameters:
            date - (tz aware datetime) Date for which all the indexed objects ending
                after have to be fecthed and returned.
           Returns:
            (Set) - set of objects ending after the specified day
        """
        date = date2utctimestamp(date)
        res = set()
        for val in self._idxEdate.values(date):
            res.update( set( val ) )
        return res

    def getObjectsStartingInDay( self, date ):
        """Returns all the objects which are starting on the specified date.

           Parameters:
            date - (tz aware datetime) day

           Returns:
            (Set) - set of objects happening within the specified date interval.
        """
        sDate = date.replace(hour=0, minute=0, second=0, microsecond=0)
        eDate = date.replace(hour=23, minute=59, second=59, microsecond=0)
        return self.getObjectsStartingIn(sDate,eDate)

    def getObjectsInDay( self, date ):
        """Returns all the objects which are happening on the specified date.

           Parameters:
            date - (tz aware datetime) day

           Returns:
            (Set) - set of objects happening within the specified date interval.
        """
        sDate = date.replace(hour=0, minute=0, second=0, microsecond=0)
        eDate = date.replace(hour=23, minute=59, second=59, microsecond=0)
        return self.getObjectsIn(sDate,eDate)

    def getObjectsStartingIn( self, sDate, eDate):
        """Returns all the objects which are starting whithin the specified
            date interval.

           Parameters:
            sDate - (tz aware datetime) Lower date of the interval to be considered.
            eDate - (tz aware datetime) Higher date of the interval to be considered.

           Returns:
            (Set) - set of objects happening within the specified date interval.
        """
        s2 = self._getObjectsStartingAfter( sDate )
        if not s2:
            return s2
        s1 = self._getObjectsStartingBefore( eDate )
        s2.intersection_update( s1 )
        return s2

    def getObjectsEndingIn( self, sDate, eDate):
        """Returns all the objects which are ending whithin the specified
            date interval.
           Parameters:
            sDate - (tz aware datetime) Lower date of the interval to be considered.
            eDate - (tz aware datetime) Higher date of the interval to be considered.
           Returns:
            (Set) - set of objects ending within the specified date interval.
        """
        s2 = self._getObjectsEndingAfter( sDate )
        if not s2:
            return s2
        s1 = self._getObjectsEndingBefore( eDate )
        s2.intersection_update( s1 )
        return s2

    def getObjectsEndingInDay( self, date ):
        """Returns all the objects which are ending on the specified date.

           Parameters:
            date - (tz aware datetime) day

           Returns:
            (Set) - set of objects happening within the specified date interval.
        """
        sDate = date.replace(hour=0, minute=0, second=0, microsecond=0)
        eDate = date.replace(hour=23, minute=59, second=59, microsecond=0)
        return self.getObjectsEndingIn(sDate,eDate)

    def getObjectsIn( self, sDate, eDate ):
        """Returns all the objects which are happening whithin the specified
            date interval.

           Parameters:
            sDate - (tz aware datetime) Lower date of the interval to be considered.
            eDate - (tz aware datetime) Higher date of the interval to be considered.

           Returns:
            (Set) - set of objects happening within the specified date interval.
        """
        s2 = self._getObjectsEndingAfter( sDate )
        if not s2:
            return s2
        s1 = self._getObjectsStartingBefore( eDate )
        s2.intersection_update( s1 )
        return s2

    def getObjectsEndingAfter( self, date ):
        return self._getObjectsEndingAfter( date )

    def getObjectsStartingAfter( self, date ):
        return self._getObjectsStartingAfter( date )

    def _check(self, dbi=None):
        """
        Performs some sanity checks
        """

        from MaKaC.conference import ConferenceHolder
        confIdx = ConferenceHolder()._getIdx()

        def _check_index(desc, index, func):
            i = 0
            for ts, confs in index.iteritems():
                for confId in confs:
                    # it has to be in the conference holder
                    if confId not in confIdx:
                        yield "[%s][%s] '%s' not in ConferenceHolder" % (desc, ts, confId)
                    else:

                        conf = ConferenceHolder().getById(confId)
                        try:
                            expectedDate = date2utctimestamp(func(conf))
                        except OverflowError:
                            expectedDate = 'overflow'

                        # ts must be ok
                        if ts != expectedDate:
                            yield "[%s][%s] Conference '%s' has bogus date (should be '%s')" % (desc, ts, confId, expectedDate)
                    if dbi and i % 100 == 99:
                        dbi.sync()
                    i += 1

        return itertools.chain(
            _check_index('sdate', self._idxSdate, lambda x: x.getStartDate()),
            _check_index('edate', self._idxEdate, lambda x: x.getEndDate()))


class CalendarDayIndex(Persistent):
    def __init__( self ):
        self._idxDay = IOBTree()

    def getIdxDate( self ):
        return self._idxDay

    def dump(self):
        return list(self._idxDay.items())

    def indexConf(self, conf):
        # Note: conf can be any object which has getEndDate() and getStartDate() methods
        self._idxDay._p_changed = True
        days = (conf.getEndDate().date() - conf.getStartDate().date()).days
        startDate = datetime(conf.getStartDate().year, conf.getStartDate().month, conf.getStartDate().day)
        for day in range(days + 1):
            key = int(datetimeToUnixTime(startDate + timedelta(day)))
            #checking if 2038 problem occurs
            if key > BTREE_MAX_INT:
                continue
            if self._idxDay.has_key(key):
                self._idxDay[key].add(conf)
            else:
                self._idxDay[key] = OOSet([conf])


    def unindexConf( self, conf):
        # Note: conf can be any object which has getEndDate() and getStartDate() methods
        self._idxDay._p_changed = True
        days = (conf.getEndDate().date() - conf.getStartDate().date()).days
        startDate = datetime(conf.getStartDate().year, conf.getStartDate().month, conf.getStartDate().day)
        for dayNumber in range(days + 1):
            day = int(datetimeToUnixTime(startDate + timedelta(dayNumber)))
            #checking if 2038 problem occurs
            if day > BTREE_MAX_INT:
                continue
            if self._idxDay.has_key( day ):
                if conf in self._idxDay[day]:
                    self._idxDay[day].remove(conf)
                if len(self._idxDay[day]) == 0:
                    del self._idxDay[day]


    def getObjectsStartingInDay( self, date ):
        day = datetime(date.year, date.month, date.day, tzinfo = date.tzinfo)
        if self._idxDay.has_key(int(datetimeToUnixTime(day))):
            return set([event for event in self._idxDay[int(datetimeToUnixTime(day))] if event.getStartDate() >= day])
        else:
            return set()

    def getObjectsEndingInDay( self, date ):
        day = datetime(date.year, date.month, date.day, tzinfo = date.tzinfo)
        if self._idxDay.has_key(int(datetimeToUnixTime(day))):
            return set([event for event in self._idxDay[int(datetimeToUnixTime(day))] if event.getEndDate() < day + timedelta(1)])
        else:
            return set()

    def getObjectsInDay( self, date ):
        day = datetime(date.year, date.month, date.day)
        if self._idxDay.has_key(int(datetimeToUnixTime(day))):
            return set(self._idxDay[int(datetimeToUnixTime(day))])
        else:
            return set()

    def getObjectsStartingIn( self, sDate, eDate):
        sDay = datetime(sDate.year, sDate.month, sDate.day, tzinfo = sDate.tzinfo)
        eDay = datetime(eDate.year, eDate.month, eDate.day, tzinfo = eDate.tzinfo)
        res = set()
        if sDay == eDay:
            if self._idxDay.has_key(int(datetimeToUnixTime(sDay))):
                res = set([event for event in self._idxDay[int(datetimeToUnixTime(sDay))] if event.getStartDate() <= eDate and event.getStartDate() >= sDate])
        elif sDay < eDay:
            if self._idxDay.has_key(int(datetimeToUnixTime(sDay))):
                res = set([event for event in self._idxDay[int(datetimeToUnixTime(sDay))] if event.getStartDate() >= sDate])
            if self._idxDay.has_key(int(datetimeToUnixTime(eDay))):
                res.update([event for event in self._idxDay[int(datetimeToUnixTime(eDay))] if event.getStartDate() <= eDate and event.getStartDate() >= eDay ])
            for day in range((eDay - sDay).days - 1):
                res.update(self.getObjectsStartingInDay( sDay + timedelta(1 + day)))
        return res

    def getObjectsEndingIn( self, sDate, eDate):
        sDay = datetime(sDate.year, sDate.month, sDate.day, tzinfo = sDate.tzinfo)
        eDay = datetime(eDate.year, eDate.month, eDate.day, tzinfo = eDate.tzinfo)
        res = set()
        if sDay == eDay:
            if self._idxDay.has_key(int(datetimeToUnixTime(sDay))):
                res = set([event for event in self._idxDay[int(datetimeToUnixTime(sDay))] if event.getEndDate() <= eDate and event.getEndDate() >= sDate])
        elif sDay < eDay:
            res = set()
            if self._idxDay.has_key(int(datetimeToUnixTime(sDay))):
                res = set([event for event in self._idxDay[int(datetimeToUnixTime(sDay))] if event.getEndDate() >= sDate and event.getEndDate() < sDay + timedelta(1)])
            if self._idxDay.has_key(int(datetimeToUnixTime(eDay))):
                res.update([event for event in self._idxDay[int(datetimeToUnixTime(eDay))] if event.getEndDate() <= eDate])
            for day in range((eDay - sDay).days - 1):
                res.update(self.getObjectsEndingInDay( sDay + timedelta(1 + day)))
        return res

    def getObjectsIn( self, sDate, eDate ):
        """
        TODO: Reimplement using iterateObjectsIn!!
        (or get rid of this one, as the other should be faster)
        """

        sDay = datetime(sDate.year, sDate.month, sDate.day)
        eDay = datetime(eDate.year, eDate.month, eDate.day)
        res = set()
        if sDay == eDay:
            if self._idxDay.has_key(int(datetimeToUnixTime(sDay))):
                res = set([event for event in self._idxDay[int(datetimeToUnixTime(sDay))] if event.getStartDate() <= eDate and event.getEndDate() >= sDate])
        elif sDay < eDay:
            res = set()
            if self._idxDay.has_key(int(datetimeToUnixTime(sDay))):
                res = set([event for event in self._idxDay[int(datetimeToUnixTime(sDay))] if event.getEndDate() >= sDate])
            if self._idxDay.has_key(int(datetimeToUnixTime(eDay))):
                res.update([event for event in self._idxDay[int(datetimeToUnixTime(eDay))] if event.getStartDate() <= eDate])
            res.update(self.getObjectsInDays( sDay + timedelta(1), eDay - timedelta(1) ))
        return res

    def iterateObjectsIn(self, sDate, eDate):
        """
        Returns all the events between two dates taking into account the starting and ending times.
        """
        sDay = datetime(sDate.year, sDate.month, sDate.day) if sDate else None
        eDay = datetime(eDate.year, eDate.month, eDate.day) if eDate else None

        if sDay and sDay == eDay:
            if int(datetimeToUnixTime(sDay)) in self._idxDay:
                for event in self._idxDay[int(datetimeToUnixTime(sDay))]:
                    if event.getStartDate() <= eDate and event.getEndDate() >= sDate:
                        yield event
            return

        if sDay and int(datetimeToUnixTime(sDay)) in self._idxDay:
            for event in self._idxDay[int(datetimeToUnixTime(sDay))]:
                if event.getEndDate() >= sDate:
                    yield event

        if sDay and eDay:
            fromTS, toTS = sDay + timedelta(1), eDay - timedelta(1)
        elif sDay:
            fromTS, toTS = sDay + timedelta(), None
        elif eDay:
            fromTS, toTS = None, eDay - timedelta(1)
        else:
            fromTS, toTS = None, None

        for evt in self.iterateObjectsInDays(fromTS, toTS):
            yield evt

        if eDay and int(datetimeToUnixTime(eDay)) in self._idxDay:
            for event in self._idxDay[int(datetimeToUnixTime(eDay))]:
                if event.getStartDate() <= eDate:
                    yield event

    def getObjectsInDays( self, sDate=None, eDate=None ):
        sDay = int(datetimeToUnixTime(datetime(sDate.year, sDate.month, sDate.day))) if sDate else None
        eDay = int(datetimeToUnixTime(datetime(eDate.year, eDate.month, eDate.day))) if eDate else None
        res = set()
        #checking if 2038 problem occurs
        if sDay > BTREE_MAX_INT or eDay > BTREE_MAX_INT:
            return res

        #checking if 1901 problem ocurrs
        if sDay < BTREE_MIN_INT or eDay < BTREE_MIN_INT:
            return res
        for event in self._idxDay.values(sDay, eDay):
            res.update(event)
        return res

    def iterateObjectsInDays(self, sDate=None, eDate=None):
        """
        Returns all the events between two dates WITHOUT taking into account the starting and ending times.
        """

        sDay = int(datetimeToUnixTime(datetime(sDate.year, sDate.month, sDate.day))) if sDate else None
        eDay = int(datetimeToUnixTime(datetime(eDate.year, eDate.month, eDate.day))) if eDate else None
        for day in self._idxDay.itervalues(sDay, eDay):
            for event in day:
                yield event

    def getObjectsEndingAfter( self, date ):
        day = datetime(date.year, date.month, date.day)
        nextDay = day + timedelta(1)
        res = set()
        if self._idxDay.has_key(int(datetimeToUnixTime(day))):
            res = set([event for event in self._idxDay[int(datetimeToUnixTime(day))] if event.getEndDate() >= date])
        for day in self._idxDay.values(int(datetimeToUnixTime(nextDay))):
            res.update(set(day))
        return res

    def getObjectsStartingAfter( self, date ):
        stDay = datetime(date.year, date.month, date.day)
        nextDay = stDay + timedelta(1)
        previousDay = stDay - timedelta(1)
        res = set()
        if self._idxDay.has_key(int(datetimeToUnixTime(stDay))):
            res = set([event for event in self._idxDay[int(datetimeToUnixTime(stDay))] if event.getStartDate() >= date])
        for day in self._idxDay.values(int(datetimeToUnixTime(nextDay))):
            res.update(set(day))
        for day in self._idxDay.values(max=int(datetimeToUnixTime(previousDay))):
            res.difference_update(set(day))
        res.difference_update(set([event for event in
                              self._idxDay.get(int(datetimeToUnixTime(stDay)), []) if event.getStartDate() < date]))
        return res

    def hasObjectsAfter(self, date):
        stDay = datetime(date.year, date.month, date.day)
        if self._idxDay:
            lastDay = self._idxDay.keys()[-1]
            return lastDay > int(datetimeToUnixTime(stDay))
        else:
            # Empty index? Then there's nothing after for sure
            return False

    def iterateObjectsIn(self, sDate, eDate):
        sDay = datetime(sDate.year, sDate.month, sDate.day) if sDate else None
        eDay = datetime(eDate.year, eDate.month, eDate.day) if eDate else None

        if sDay and sDay == eDay:
            if int(datetimeToUnixTime(sDay)) in self._idxDay:
                for event in self._idxDay[int(datetimeToUnixTime(sDay))]:
                    if event.getStartDate() <= eDate and event.getEndDate() >= sDate:
                        yield event
            return

        # keep track of the records that have been already sent

        if sDay and int(datetimeToUnixTime(sDay)) in self._idxDay:
            for event in self._idxDay[int(datetimeToUnixTime(sDay))]:
                if event.getEndDate() >= sDate:
                    yield event

        if sDay and eDay:
            fromTS, toTS = sDay + timedelta(1), eDay - timedelta(1)
        elif sDay:
            fromTS, toTS = sDay + timedelta(), None
        elif eDay:
            fromTS, toTS = None, eDay - timedelta(1)
        else:
            fromTS, toTS = None, None

        for evt in self.iterateObjectsInDays(fromTS, toTS):
            yield evt

        if eDay and int(datetimeToUnixTime(eDay)) in self._idxDay:
            for event in self._idxDay[int(datetimeToUnixTime(eDay))]:
                if event.getStartDate() <= eDate:
                    yield event

    def iterateObjectsInDays(self, sDate=None, eDate=None):

        sDay = int(datetimeToUnixTime(datetime(sDate.year, sDate.month, sDate.day))) if sDate else None
        eDay = int(datetimeToUnixTime(datetime(eDate.year, eDate.month, eDate.day))) if eDate else None
        for day in self._idxDay.itervalues(sDay, eDay):
            for event in day:
                yield event

    def _check(self, dbi=None, categId=''):
        """
        Performs some sanity checks
        """
        i = 0
        from MaKaC.conference import ConferenceHolder
        confIdx = ConferenceHolder()._getIdx()

        for ts, confs in self._idxDay.iteritems():
            dt = timezone('UTC').localize(datetime.utcfromtimestamp(ts))

            for conf in confs:
                # it has to be in the conference holder
                if conf.getId() not in confIdx:
                    yield "[%s][%s] '%s' not in ConferenceHolder" % (ts, categId, conf.getId())
                else:
                    # date must be ok
                    if dt > conf.getEndDate().replace(hour=23, minute=59, second=59) \
                           or dt < conf.getStartDate().replace(hour=0, minute=0, second=0):
                        yield "[%s] '%s' has date out of bounds '%s'(%s)" % (categId, conf.getId(), ts, dt)
                    elif categId not in (map(lambda x:x.id, conf.getOwnerPath()) + ['0']):
                        yield "[%s] Conference '%s' is not owned" % (categId, conf.getId())

                if dbi and i % 100 == 99:
                    dbi.sync()
                i += 1


class CategoryDateIndex(Persistent):

    def __init__( self ):
        self._idxCategItem = OOBTree()

    def dump(self):
        return map(lambda idx: (idx[0], idx[1].dump()), list(self._idxCategItem.items()))

    def unindexConf(self, conf):
        for owner in conf.getOwnerPath():
            if self._idxCategItem.has_key(owner.getId()):
                self._idxCategItem[owner.getId()].unindexConf(conf)
        if self._idxCategItem.has_key('0'):
            self._idxCategItem['0'].unindexConf(conf)


    def reindexCateg(self, categ):
        for subcat in categ.getSubCategoryList():
            self.reindexCateg(subcat)
        for conf in categ.getConferenceList():
            self.unindexConf(conf)
            self.indexConf(conf)
#        from indico.core.db import DBMgr
#        dbi = DBMgr.getInstance()
#        for subcat in categ.getSubCategoryList():
#            self.reindexCateg(subcat)
#        for conf in categ.getConferenceList():
#            while True:
#                try:
#                    dbi.sync()
#                    self.unindexConf(conf)
#                    self.indexConf(conf)
#                    dbi.commit()
#                    break
#                except:
#                    print 'Exception commiting conf %s'%conf.getId()

    def unindexCateg(self, categ):
        for subcat in categ.getSubCategoryList():
            self.unindexCateg(subcat)
        for conf in categ.getConferenceList():
            self.unindexConf(conf)

    def indexCateg(self, categ, dbi=None, counter=0):
        for subcat in categ.getSubCategoryList():
            self.indexCateg(subcat, dbi=dbi, counter=counter+1)
            if dbi and counter < 2:
                dbi.commit()
        for conf in categ.getConferenceList():
            self.indexConf(conf)

    def _indexConf(self, categid, conf):
        # only the more restrictive setup is taken into account
        if categid in self._idxCategItem:
            res = self._idxCategItem[categid]
        else:
            res = CalendarIndex()
        res.indexConf(conf)
        self._idxCategItem[categid] = res

    # TOREMOVE?? defined in CategoryDayIndex
    def indexConf(self, conf):
        for categ in conf.getOwnerPath():
            self._indexConf(categ.getId(), conf)
        self._indexConf("0",conf)

    def getObjectsIn(self, categid, sDate, eDate):
        categid = str(categid)
        if categid in self._idxCategItem:
            return self._idxCategItem[categid].getObjectsIn(sDate, eDate)
        else:
            return []

    def getObjectsStartingIn(self, categid, sDate, eDate):
        categid = str(categid)
        if categid in self._idxCategItem:
            return self._idxCategItem[categid].getObjectsStartingIn(sDate, eDate)
        else:
            return []

    def getObjectsInDay(self, categid, sDate):
        categid = str(categid)
        if categid in self._idxCategItem:
            return self._idxCategItem[categid].getObjectsInDay(sDate)
        else:
            return []

    def hasObjectsAfter(self, categid, sDate):
        categid = str(categid)
        if categid in self._idxCategItem:
            return self._idxCategItem[categid].hasObjectsAfter(sDate)
        else:
            return False

    def getObjectsEndingAfter(self, categid, sDate):
        categid = str(categid)
        if categid in self._idxCategItem:
            return self._idxCategItem[categid].getObjectsEndingAfter(sDate)
        else:
            return []


class CategoryDateIndexLtd(CategoryDateIndex):
    """ Version of CategoryDateIndex whiself.ch indexing events
        on the base of their visibility
    """
    def indexConf(self, conf):
        level = 0
        for categ in conf.getOwnerPath():
            if conf.getFullVisibility() > level:
                self._indexConf(categ.getId(),conf)
            level+=1
        if conf.getFullVisibility() > level:
            self._indexConf("0",conf)

    def buildIndex(self, dbi=None):
        self._idxCategItem = OOBTree()
        from MaKaC.conference import CategoryManager
        self.indexCateg(CategoryManager().getById('0'), dbi=dbi)

class CategoryDayIndex(CategoryDateIndex):

    def __init__(self, visibility=True):
        super(CategoryDayIndex, self).__init__()
        self._useVisibility = visibility

    def _indexConf(self, categid, conf):
        # only the more restrictive setup is taken into account
        if self._idxCategItem.has_key(categid):
            res = self._idxCategItem[categid]
        else:
            res = CalendarDayIndex()
        res.indexConf(conf)
        self._idxCategItem[categid] = res

    def reindexConf(self, conf):
        self.unindexConf(conf)
        self.indexConf(conf)

    def indexConf(self, conf):
        level = 0
        for categ in conf.getOwnerPath():
            if not self._useVisibility or conf.getFullVisibility() > level:
                self._indexConf(categ.getId(),conf)
            level+=1
        if not self._useVisibility or conf.getFullVisibility() > level:
            self._indexConf("0",conf)

    def buildIndex(self, dbi):
        self._idxCategItem = OOBTree()
        from MaKaC.conference import CategoryManager
        self.indexCateg(CategoryManager().getById('0'), dbi=dbi)

    def getObjectsInDays(self, categid, sDate, eDate):
        if self._idxCategItem.has_key(categid):
            return self._idxCategItem[categid].getObjectsInDays(sDate, eDate)
        else:
            return []

    def iterateObjectsIn(self, categid, sDate, eDate):
        if categid in self._idxCategItem:
            return self._idxCategItem[categid].iterateObjectsIn(sDate, eDate)
        else:
            return []

    def _check(self, dbi=None):
        """
        Performs some sanity checks
        """
        for categId, calDayIdx in self._idxCategItem.iteritems():
            for problem in calDayIdx._check(dbi=dbi, categId=categId):
                yield problem


class PendingQueuesUsersIndex( Index ):
    _name = ""

    def indexPendingUser( self, user ):
        email = user.getEmail().lower()
        self._addItem( email, user )
        self.notifyModification()

    def unindexPendingUser( self, user ):
        email = user.getEmail().lower()
        self._withdrawItem( email, user )
        self.notifyModification()

    def _withdrawItem( self, value, item ):
        Index._withdrawItem( self, value, item )
        if self._words.has_key(value):
            if self._words[value]==[]:
                del self._words[value]

    def matchPendingUser( self, email, cs=0, exact=1 ):
        """this match is an approximative case insensitive match"""
        return self._match(email,cs,exact)

class PendinQueuesTasksIndex( Index ):
    _name = ""

    def indexTask( self, email, task ):
        email = email.lower().strip()
        self._addItem( email, task )
        self.notifyModification()

    def unindexTask( self, email, task ):
        email = email.lower().strip()
        self._withdrawItem( email, task )
        self.notifyModification()

    def _withdrawItem( self, value, item ):
        Index._withdrawItem( self, value, item )
        if self._words.has_key(value):
            if self._words[value]==[]:
                del self._words[value]

    def matchTask( self, email, cs=0, exact=1 ):
        """this match is an approximative case insensitive match"""
        return self._match(email,cs,exact)

class PendingSubmittersIndex( PendingQueuesUsersIndex ):
    _name = "pendingSubmitters"
    pass

class PendingConfSubmittersIndex( PendingQueuesUsersIndex ):
    _name = "pendingConfSubmitters"
    pass

class PendingConfSubmittersTasksIndex( PendinQueuesTasksIndex ):
    _name = "pendingConfSubmittersTasks"
    pass

class PendingConfManagersIndex( PendingQueuesUsersIndex ):
    _name = "pendingConfManagers"
    pass

class PendingConfManagersTasksIndex( PendinQueuesTasksIndex ):
    _name = "pendingConfManagersTasks"
    pass

class PendingSubmittersTasksIndex( PendinQueuesTasksIndex ):
    _name = "pendingSubmittersTasks"
    pass

class PendingManagersIndex( PendingQueuesUsersIndex ):
    _name = "pendingManagers"
    pass

class PendingManagersTasksIndex( PendinQueuesTasksIndex ):
    _name = "pendingManagersTasks"
    pass

class PendingCoordinatorsIndex( PendingQueuesUsersIndex ):
    _name = "pendingCoordinators"
    pass

class PendingCoordinatorsTasksIndex( PendinQueuesTasksIndex ):
    _name = "pendingCoordinatorsTasks"
    pass


class IndexException(Exception):
    pass


class IntStringMappedIndex(Persistent):
    def __init__(self):
        self._intToStrMap = {}
        self._strToIntMap = {}
        self._counter = 0

    def addString(self, stringId):
        """
        Adds a string to the index, returning the
        assigned integer
        """

        if stringId in self._strToIntMap:
            raise KeyError("Key '%s' already exists in index!" % stringId)

        intId = self._counter
        self._intToStrMap[intId] = stringId
        self._strToIntMap[stringId] = intId
        self._counter += 1

        self._p_changed = 1

        return intId

    def removeString(self, stringId):
        """
        Removes an entry from the Int-String Mapped index,
        taking the string as input, and returning the integer
        if it exists, or -1 otherwise.
        """

        intId = self._strToIntMap[stringId]
        try:
            del self._strToIntMap[stringId]
            del self._intToStrMap[intId]
        except KeyError:
            return -1

        self._p_changed = 1

        return intId

    def getString(self, intId):
        """
        0 -> 'abcd'
        """

        if type(intId) != int:
            raise TypeError
        if intId not in self._intToStrMap:
            return None

        return self._intToStrMap[intId]

    def getInteger(self, strId):
        """
        'abcd' -> 0
        """

        if type(strId) != str:
            raise TypeError
        if strId not in self._strToIntMap:
            return None

        return self._strToIntMap[strId]


class TextIndex(IntStringMappedIndex):

    def __init__(self):
        IntStringMappedIndex.__init__(self)
        self._textIdx = textindex.TextIndex()

    def index(self, entryId, title):
        intId = self.addString(entryId)
        self._textIdx.index_doc(intId, title)

    def unindex(self, entryId):
        intId = self.getInteger(entryId)

        if intId != None:
            self.removeString(entryId)
            self._textIdx.unindex_doc(intId)
        else:
            Logger.get('indexes.text').error("No such entry '%s'" % entryId)

    def search(self, text):
        records = self._textIdx.apply(text.decode('utf8')).items()
        return [(self.getString(record[0]), record[1]) for record in records]


class IndexesHolder( ObjectHolder ):

    idxName = "indexes"
    counterName = None
    __allowedIdxs = [ "email", "name", "surName", "organisation", "group",
                    "status", "calendar", "category", "categoryDate",
                    "categoryDateAll", "categoryName","conferenceTitle",
                    "pendingSubmitters", "pendingConfSubmitters",
                    "pendingConfSubmittersTasks", "pendingConfManagers",
                    "pendingConfManagersTasks","pendingSubmittersTasks", "pendingManagers",
                    "pendingManagersTasks", "pendingCoordinators",
                    "pendingCoordinatorsTasks", "webcasts", "collaboration"]

    def getIndex( self, name ):
        return self.getById(name)

    def getById( self, id ):
        """returns an object from the index which id corresponds to the one
            which is specified.
        """

        if id not in self.__allowedIdxs:
            raise MaKaCError( _("Unknown index: %s")%id)
        Idx = self._getIdx()
        if id in Idx:
            return Idx[id]
        else:
            if id=="email":
                Idx[str(id)] = EmailIndex()
            elif id=="name":
                Idx[str(id)] = NameIndex()
            elif id=="surName":
                Idx[str(id)] = SurNameIndex()
            elif id=="organisation":
                Idx[str(id)] = OrganisationIndex()
            elif id=="status":
                Idx[str(id)] = StatusIndex()
            elif id=="group":
                Idx[str(id)] = GroupIndex()
            elif id=="calendar":
                Idx[str(id)] = CalendarIndex()
            elif id=="category":
                Idx[str(id)] = CategoryIndex()
            elif id=="categoryDate":
                Idx[str(id)] = CategoryDayIndex()
            elif id=="categoryDateAll":
                Idx[str(id)] = CategoryDayIndex(visibility=False)
            elif id=="categoryName":
                Idx[str(id)] = TextIndex()
            elif id=="conferenceTitle":
                Idx[str(id)] = TextIndex()
            elif id=="pendingSubmitters":
                Idx[str(id)] = PendingSubmittersIndex()
            elif id=="pendingConfSubmitters":
                Idx[str(id)] = PendingConfSubmittersIndex()
            elif id=="pendingSubmittersTasks":
                Idx[str(id)] = PendingSubmittersTasksIndex()
            elif id=="pendingConfSubmittersTasks":
                Idx[str(id)] = PendingConfSubmittersTasksIndex()
            elif id=="pendingConfManagers":
                Idx[str(id)] = PendingConfManagersIndex()
            elif id=="pendingConfManagersTasks":
                Idx[str(id)] = PendingConfManagersTasksIndex()
            elif id=="pendingManagers":
                Idx[str(id)] = PendingManagersIndex()
            elif id=="pendingManagersTasks":
                Idx[str(id)] = PendingManagersTasksIndex()
            elif id=="pendingCoordinators":
                Idx[str(id)] = PendingManagersIndex()
            elif id=="pendingCoordinatorsTasks":
                Idx[str(id)] = PendingManagersTasksIndex()
            else:
                extension_point("indexHolderProvider", Idx, id)
            return Idx[str(id)]


if __name__ == "__main__":
    print _("done")
