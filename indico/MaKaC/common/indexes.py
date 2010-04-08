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

"""This file contains various indexes which will be used in the system in order
    to optimise some functionalities.
"""
from persistent import Persistent
from BTrees.IOBTree import IOBTree
from BTrees.OOBTree import OOBTree
from MaKaC.common.ObjectHolders import ObjectHolder
from MaKaC.common.Configuration import Config
from MaKaC.common.timezoneUtils import nowutc, date2utctimestamp
from MaKaC.errors import MaKaCError
import sets
from datetime import datetime
from datetime import timedelta
from MaKaC.i18n import _
from pytz import timezone
from MaKaC.common.logger import Logger
from MaKaC.plugins.base import PluginsHolder

from zope.index.text import textindex

class Index(Persistent):
    _name = ""

    def __init__( self, name='' ):
        if name != '':
            self._name = name
        self._words = {}

    def getLength( self ):
        return len(self._words.keys())

    def getKeys( self ):
        return self._words.keys()

    def getBrowseIndex( self ):
        letters = []
        words = self.getKeys()
        for word in words:
            if not word[0].lower() in letters:
                letters.append(word[0].lower())
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

    def matchFirstLetter( self, letter ):
        result = []
        for key in self.getKeys():
            if key[0].lower() == letter.lower():
                result += self._words[key]
        return result

    def _match( self, value, cs=1, exact=1 ):

        result = []
        lowerCaseValue = value.lower()

        if exact == 1 and cs == 1:
            if self._words.has_key(value) and len(self._words[value]) != 0:
                if '' in self._words[value]:
                    self._words[value].remove('')
                return self._words[value]
            else:
                return None
        elif exact == 1 and cs == 0:
            for key in self._words.keys():
                if key.lower() == lowerCaseValue and len(self._words[key]) != 0:
                    if '' in self._words[key]:
                        self._words[key].remove('')
                    result = result + self._words[key]
            return result
        elif exact == 0 and cs == 1:
            for key in self._words.keys():
                if key.find(value) != -1 and len(self._words[key]) != 0:
                    if '' in self._words[key]:
                        self._words[key].remove('')
                    result = result + self._words[key]
            return result
        else:
            for key in self._words.keys():
                if key.lower().find(lowerCaseValue) != -1 and len(self._words[key]) != 0:
                    if '' in self._words[key]:
                        self._words[key].remove('')
                    result = result + self._words[key]
            return result
        return None

    def dump(self):
        return self._words

    def setIndex(self, words):
        self._words = words

    def notifyModification(self):
        self._p_changed=1

class EmailIndex( Index ):
    _name = "email"

    def indexUser( self, user ):
        email = user.getEmail()
        self._addItem( email, user.getId() )
        for email in user.getSecondaryEmails():
            self._addItem( email, user.getId() )

    def unindexUser( self, user ):
        email = user.getEmail()
        self._withdrawItem( email, user.getId() )
        for email in user.getSecondaryEmails():
            self._withdrawItem( email, user.getId() )

    def matchUser( self, email, cs=0, exact=0 ):
        """this match is an approximative case insensitive match"""
        return self._match(email,cs,exact)

class NameIndex( Index ):
    _name = "name"

    def indexUser( self, user ):
        name = user.getName()
        self._addItem( name, user.getId() )

    def unindexUser( self, user ):
        name = user.getName()
        self._withdrawItem( name, user.getId() )

    def matchUser( self, name, cs=0, exact=0 ):
        """this match is an approximative case insensitive match"""
        return self._match(name,cs,exact)

class SurNameIndex( Index ):
    _name = "surName"

    def indexUser( self, user ):
        surName = user.getSurName()
        self._addItem( surName, user.getId() )

    def unindexUser( self, user ):
        surName = user.getSurName()
        self._withdrawItem( surName, user.getId() )

    def matchUser( self, surName, cs=0, exact=0 ):
        """this match is an approximative case insensitive match"""
        return self._match(surName,cs,exact)

class OrganisationIndex( Index ):
    _name = "organisation"

    def indexUser( self, user ):
        org = user.getOrganisation()
        self._addItem( org, user.getId() )

    def unindexUser( self, user ):
        org = user.getOrganisation()
        self._withdrawItem( org, user.getId() )

    def matchUser( self, org, cs=0, exact=0 ):
        """this match is an approximative case insensitive match"""
        return self._match(org,cs,exact)

class StatusIndex( Index ):
    _name = "status"

    def __init__( self ):
        Index.__init__( self )
        from MaKaC.user import AvatarHolder
        ah = AvatarHolder()
        for av in ah.getList():
            self.indexUser(av)

    def indexUser( self, user ):
        status = user.getStatus()
        self._addItem( status, user.getId() )

    def unindexUser( self, user ):
        status = user.getStatus()
        self._withdrawItem( status, user.getId() )

    def matchUser( self, status, cs=0, exact=1 ):
        """this match is an approximative case insensitive match"""
        return self._match(status,cs,exact)

class GroupIndex( Index ):
    _name = "group"

    def indexGroup( self, group ):
        name = group.getName()
        self._addItem( name, group.getId() )

    def unindexGroup( self, group ):
        name = group.getName()
        self._withdrawItem( name, group.getId() )

    def matchGroup( self, name, cs=0, exact=0 ):
        if name == "":
            return []
        return self._match(name,cs,exact)

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
        if self._idxSdate.has_key( sdate ):
            res = self._idxSdate[sdate]
        else:
            res = []
        if not confid in res:
            res.append(confid)
            self._idxSdate[sdate] = res
        edate = date2utctimestamp(conf.getEndDate())
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
        res = sets.Set()
        for val in self._idxSdate.values(self._idxSdate.minKey(), date):
            res.union_update( sets.Set( val ) )
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
        res = sets.Set()
        for val in self._idxSdate.values(date):
            res.union_update( sets.Set( val ) )
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
        res = sets.Set()
        for val in self._idxEdate.values(self._idxEdate.minKey(), date):
            res.union_update( sets.Set( val ) )
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
        res = sets.Set()
        for val in self._idxEdate.values(date):
            res.union_update( sets.Set( val ) )
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

    #def getObjectsStartingInYear( self, year ):
    #    lastDay = datetime( year, 12, 31 )
    #    s1 = sets.Set()
    #    # Objects starting before last day of year (included):
    #    s1 = self._getObjectsStartingBefore(lastDay + timedelta(days=1))
    #    if not s1:
    #        return s1
    #    firstDay = datetime( year, 1, 1 )
    #    s2 = sets.Set()
    #    # Objects starting before first day of year (excluded):
    #    s2 = self._getObjectsStartingBefore(firstDay)
    #    # Difference:
    #    s1.difference_update( s2 )
    #    return s1

class CategoryDateIndex(Persistent):

    def __init__( self ):
        self._idxCategItem = OOBTree()

    def dump(self):
        return map(lambda idx: (idx[0], idx[1].dump()), list(self._idxCategItem.items()))

    def unindexConf(self, conf):
        for owner in conf.getOwnerPath():
            self._idxCategItem[owner.getId()].unindexConf(conf)
        self._idxCategItem['0'].unindexConf(conf)

    def unindexCateg(self, categ):
        for subcat in categ.getSubCategoryList():
            self.unindexCateg(subcat)
        for conf in categ.getConferenceList():
            self.unindexConf(conf)

    def indexCateg(self, categ):
        for subcat in categ.getSubCategoryList():
            self.indexCateg(subcat)
        for conf in categ.getConferenceList():
            self.indexConf(conf)

    def _indexConf(self, categid, conf):
        # only the more restrictive setup is taken into account
        if self._idxCategItem.has_key(categid):
            res = self._idxCategItem[categid]
        else:
            res = CalendarIndex()
        res.indexConf(conf)
        self._idxCategItem[categid] = res

    def indexConf(self, conf):
        categs = conf.getOwnerPath()
        level = 0
        for categ in conf.getOwnerPath():
            self._indexConf(categ.getId(), conf)
        self._indexConf("0",conf)

    def getObjectsIn(self, categid, sDate, eDate):
        categid = str(categid)
        if self._idxCategItem.has_key(categid):
            return self._idxCategItem[categid].getObjectsIn(sDate, eDate)
        else:
            return []

    def getObjectsStartingIn( self, categid, sDate, eDate):
        categid = str(categid)
        if self._idxCategItem.has_key(categid):
            return self._idxCategItem[categid].getObjectsStartingIn(sDate, eDate)
        else:
            return []

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

class DoubleIndex(Index):

    def __init__( self, name='' ):
        if name != '':
            self._name = name
        self._words = OOBTree()
        self._ids = OOBTree()

    def _addItem( self, value, item ):
        if value != "":
            words = self._words
            if words.has_key(value):
                if item not in words[value]:
                    l = words[value]
                    l.append(item)
                    words[value] = l
            else:
                words[value] = [ item ]
            self.setIndex(words)
            id = self._itemToId(item)
            if self._ids.has_key(value):
                if id not in self._ids[value]:
                    l = self._ids[value]
                    l.append(id)
                    self._ids[value] = l
            else:
                self._ids[value] = [id]
            self._p_changed = 1

    def _withdrawItem( self, value, item ):
        if self._words.has_key(value):
            if item in self._words[value]:
                words = self._words
                l = words[value]
                l.remove(item)
                words[value] = l
                self.setIndex(words)
        id = self._itemToId(item)
        if self._ids.has_key(value):
            if id in self._ids[value]:
                l = self._ids[value]
                l.remove(id)
                self._ids[value] = l
        self._p_changed = 1

    def _itemToId(self, item):
        #to be overloaded
        return ""

    def initIndex(self):
        self._words = OOBTree()
        self._ids = OOBTree()
        self._p_changed = 1

    def getLowerIndex(self):
        if self._words.keys():
            return min(self._words.keys())
        return None

class OAIDoubleIndex(DoubleIndex):

    def __init__(self, name='' ):
        DoubleIndex.__init__(self, name)
        self.firstDate = nowutc().replace( hour=0, minute=0, second=0, microsecond=0 )

    def initIndex( self ):
        DoubleIndex.initIndex(self)
        self.firstDate = nowutc().replace( hour=0, minute=0, second=0, microsecond=0 )

    def getElements(self, from_date, until_date):
        if not (from_date or until_date):
            return self._words.values()

        if from_date:
            fd = datetime(int(from_date[0:4]), int(from_date[5:7]), int(from_date[8:10]), tzinfo=timezone('UTC'))
        else:
            fd = self.firstDate

        if until_date:
            ud = datetime(int(until_date[0:4]), int(until_date[5:7]), int(until_date[8:10]), tzinfo=timezone('UTC'))
        else:
            ud = nowutc().replace( hour=23, minute=59, second=59, microsecond=0 )

        res = []
        if fd > ud:
            return res
        delta = timedelta(1)
        while fd <= ud:
            d = fd.strftime("%Y-%m-%d")
            if d in self._words:
                res.extend(self._words[d])
            fd += delta
        return res


    def getElementIds(self, from_date, until_date):
        if not (from_date or until_date):
            return self.getAllElementIds()

        fd = self.firstDate
        if from_date:
#            fd = server2utc(datetime(int(from_date[0:4]), int(from_date[5:7]), int(from_date[8:10])))
            fd = datetime(int(from_date[0:4]), int(from_date[5:7]), int(from_date[8:10]), tzinfo=timezone('UTC'))
        ud = nowutc().replace( hour=23, minute=59, second=59, microsecond=0 )
        if until_date:
#            ud = server2utc(datetime(int(until_date[0:4]), int(until_date[5:7]), int(until_date[8:10])))
            ud = datetime(int(until_date[0:4]), int(until_date[5:7]), int(until_date[8:10]), tzinfo=timezone('UTC'))
        res = []
        if fd > ud:
            return res
        date = fd
        delta = timedelta(1)
        while date <= ud:
            if date.strftime("%Y-%m-%d") in self._ids.keys():
                res.extend(self._ids[date.strftime("%Y-%m-%d")])
            date = date + delta
        return res

    def getAllElements(self):
        res = []
        for date in self._words.keys():
            res.extend(self._words[date])
        return res

    def getAllElementIds(self):
        res = []
        for date in self._ids.keys():
            res.extend(self._ids[date])
        return res

    def unindexElement( self, cont ):
        date = cont.getOAIModificationDate().strftime("%Y-%m-%d")
        self._withdrawItem( date, cont )


class OAIContributionIndex( OAIDoubleIndex ):
    def __init__(self, name='' ):
        OAIDoubleIndex.__init__(self, name)
        self.firstDate = nowutc().replace( hour=0, minute=0, second=0, microsecond=0 )

    def initIndex( self ):
        OAIDoubleIndex.initIndex(self)
        self.firstDate = nowutc().replace( hour=0, minute=0, second=0, microsecond=0 )

    def _itemToId(self, item):
        from MaKaC.conference import Contribution, SubContribution
        if isinstance(item, Contribution):
            return "%s:%s"%(item.getConference().getId(), item.getId())
        elif isinstance(item, SubContribution):
            return "%s:%s:%s"%(item.getConference().getId(), item.getContribution().getId(), item.getId())
        return ""

    def getContributions(self, from_date, until_date):
        return OAIDoubleIndex.getElements(self, from_date, until_date)

    def getContributionsIds(self, from_date, until_date):
        return OAIDoubleIndex.getElementIds(self, from_date, until_date)

    def getAllContributions(self):
        return OAIDoubleIndex.getAllElements(self)

    def getAllContributionsIds(self):
        return OAIDoubleIndex.getAllElementIds(self)

    def unindexContribution( self, cont ):
        return OAIDoubleIndex.unindexElement(self, cont)

    def indexContribution( self, cont ):
#        Logger.get('oai/indexes').debug("\tINDEXING %s from conf %s" % (cont.getId(), cont.getConference().getId()))
        if not self.isIndexable(cont):
#            Logger.get('oai/indexes').debug("\t\tUNINDEXED - contribution is not indexable")
            self.unindexContribution(cont)
            return
        from MaKaC.conference import ContribStatusWithdrawn
        if not isinstance(cont.getContribution().getCurrentStatus(), ContribStatusWithdrawn):
            date = cont.getOAIModificationDate()
            strDate = date.strftime("%Y-%m-%d")
            if date < self.firstDate:
                self.firstDate = date
            self._addItem( strDate, cont )

class OAIContributionModificationDateIndex( OAIContributionIndex ):
    _name = "OAIContributionModificationDate"

    def isIndexable(self, conf):
        # only public conferences shoud be indexed
        return not conf.hasAnyProtection()


class OAIPrivateContributionModificationDateIndex( OAIContributionIndex ):
    _name = "OAIPrivateContributionModificationDate"

    def __init__( self, name='' ):
        OAIContributionIndex.__init__(self, name)

    def indexContribution( self, cont ):
        if not cont.hasAnyProtection():
            self.unindexContribution(cont)
            return
        from MaKaC.conference import ContribStatusWithdrawn
        if not isinstance(cont.getContribution().getCurrentStatus(), ContribStatusWithdrawn):
            date = cont.getOAIModificationDate()
            strDate = date.strftime("%Y-%m-%d")
            if date < self.firstDate:
                self.firstDate = date
            self._addItem( strDate, cont )

class OAIDeletedContributionModificationDateIndex( OAIContributionModificationDateIndex ):
    _name = "OAIDeletedContributionModificationDate"

    def indexContribution( self, cont ):
        date = cont.getOAIModificationDate()
        strDate = date.strftime("%Y-%m-%d")
        if date < self.firstDate:
            self.firstDate = date
        self._addItem( strDate, cont )

class OAIDeletedPrivateContributionModificationDateIndex(OAIDeletedContributionModificationDateIndex):
    _name = "OAIDeletedPrivateContributionModificationDate"


class OAIDeletedContributionCategoryIndex( OAIContributionIndex ):
    _name = "OAIDeletedContributionCategory"

    def __init__( self, name='' ):
        OAIContributionIndex.__init__(self, name)

    def _itemToId(self, item):
        return item.getId()

    def indexContribution( self, cont ):
        for catId in cont.getCategoryPath():
            self._addItem( catId, cont )

    def unindexContribution( self, cont ):
        for catId in cont.getCategoryPath():
            self._withdrawItem( catId, cont )

    def getContributions(self, catId):
        if not catId in self._ids.keys():
            return []
        return self._words[catId]

    def getContributionsIds(self, catId):
        if not catId in self._ids.keys():
            return []
        return self._ids[catId]

    def getAllConferences(self):
        res = []
        for catId in self._words.keys():
            res.extend(self._words[catId])
        return res

    def getAllConferencesIds(self):
        res = []
        for catId in self._ids.keys():
            res.extend(self._ids[catId])
        return res

class OAIDeletedPrivateContributionCategoryIndex( OAIDeletedContributionCategoryIndex ):
    _name = "OAIDeletedPrivateContributionCategory"


class OAIConferenceIndex( OAIDoubleIndex ):

    def __init__( self, name='' ):
        OAIDoubleIndex.__init__(self, name)
        self.firstDate = nowutc().replace( hour=0, minute=0, second=0, microsecond=0 )

    def initIndex( self ):
        OAIDoubleIndex.initIndex(self)
        self.firstDate = nowutc().replace( hour=0, minute=0, second=0, microsecond=0 )

    def _itemToId(self, item):
        return item.getId()

    def unindexElement( self, conf ):
        date = conf.getOAIModificationDate().strftime("%Y-%m-%d")
        self._withdrawItem( date, conf )

    def unindexConference( self, conf ):
        self.unindexElement(conf)

    def getConferences(self, from_date, until_date):
        return OAIDoubleIndex.getElements(self, from_date, until_date)

    def getConferencesIds(self, from_date, until_date):
        if not (from_date or until_date):
            res = []
            for key in self._ids.keys():
                res.extend(self._ids[key])
            return res

        fd = self.firstDate
        if from_date:
            #fd = server2utc(datetime(int(from_date[0:4]), int(from_date[5:7]), int(from_date[8:10])))
            fd = datetime(int(from_date[0:4]), int(from_date[5:7]), int(from_date[8:10]), tzinfo=timezone('UTC'))
        ud = nowutc().replace( hour=23, minute=59, second=29, microsecond=0 )
        if until_date:
            #ud = server2utc(datetime(int(until_date[0:4]), int(until_date[5:7]), int(until_date[8:10])))
            ud = datetime(int(until_date[0:4]), int(until_date[5:7]), int(until_date[8:10]), tzinfo=timezone('UTC'))
        res = []
        if fd > ud:
            return res
        date = fd
        delta = timedelta(1)
        while date <= ud:
            if date.strftime("%Y-%m-%d") in self._ids.keys():
                res.extend(self._ids[date.strftime("%Y-%m-%d")])
            date = date + delta

        return res

    def getAllConferences(self):
        return OAIDoubleIndex.getAllElements(self)

    def getAllConferencesIds(self):
        return OAIDoubleIndex.getAllElementIds(self)

    def unindexConference( self, cont ):
        return OAIDoubleIndex.unindexElement(self, cont)

class OAIConferenceModificationDateIndex( OAIConferenceIndex ):
    _name = "OAIConferenceModificationDate"

    def __init__( self, name='' ):
        OAIConferenceIndex.__init__(self, name)

    def indexConference( self, conf ):

        if conf.hasAnyProtection():
            self.unindexConference(conf)
            return
        date = conf.getOAIModificationDate()
        strDate = date.strftime("%Y-%m-%d")
        if date < self.firstDate:
            self.firstDate = date
        self._addItem( strDate, conf )

    def isIndexable(self, conf):
        # only public conferences shoud be indexed
        return not conf.hasAnyProtection()


class OAIPrivateConferenceModificationDateIndex( OAIConferenceModificationDateIndex ):
    _name = "OAIPrivateConferenceModificationDate"

    def __init__( self, name='' ):
        OAIConferenceIndex.__init__(self, name)

    def indexConference( self, conf ):
        if not conf.hasAnyProtection():
            self.unindexConference(conf)
            return
        date = conf.getOAIModificationDate()
        strDate = date.strftime("%Y-%m-%d")
        if date < self.firstDate:
            self.firstDate = date
        self._addItem( strDate, conf )

class OAIDeletedConferenceModificationDateIndex( OAIConferenceModificationDateIndex ):
    _name = "OAIDeletedConferenceModificationDate"

    def isIndexable(self, conf):
        # only public conferences shoud be indexed
        return not conf.hasAnyProtection()

class OAIDeletedPrivateConferenceModificationDateIndex( OAIPrivateConferenceModificationDateIndex ):
    _name = "OAIDeletedPrivateConferenceModificationDate"


class OAIDeletedPrivateConferenceModificationDateIndex( OAIPrivateConferenceModificationDateIndex ):
    _name = "OAIDeletedPrivateConferenceModificationDate"


class OAIDeletedConferenceCategoryIndex( OAIConferenceIndex ):
    _name = "OAIDeletedConferenceCategory"

    def __init__( self, name='' ):
        OAIConferenceIndex.__init__(self, name)

    def indexConference( self, conf ):
        for catId in conf.getCategoryPath():
            self._addItem( catId, conf )

    def unindexConference( self, conf ):
        for catId in conf.getCategoryPath():
            self._withdrawItem( catId, conf )

    def getConferences(self, catId):
        if not catId in self._ids.keys():
            return []
        return self._words[catId]

    def getConferencesIds(self, catId):
        if not catId in self._ids.keys():
            return []
        return self._ids[catId]

    def getAllConferences(self):
        res = []
        for catId in self._words.keys():
            res.extend(self._words[catId])
        return res

    def getAllConferencesIds(self):
        res = []
        for catId in self._ids.keys():
            res.extend(self._ids[catId])
        return res

class OAIDeletedPrivateConferenceCategoryIndex( OAIDeletedConferenceCategoryIndex ):
    _name = "OAIDeletedPrivateConferenceCategory"


class OAIDeletedPrivateContributionCategoryIndex( OAIDeletedContributionCategoryIndex ):
    _name = "OAIDeletedPrivateContributionCategory"


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

        if intId:
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
                    "categoryName",
                    "pendingSubmitters",
                    "pendingSubmittersTasks", "pendingManagers",
                    "pendingManagersTasks", "pendingCoordinators",
                    "pendingCoordinatorsTasks", "webcasts", "collaboration",
                    "OAIConferenceModificationDate",
                    "OAIContributionModificationDate",
                    "OAIPrivateConferenceModificationDate",
                    "OAIPrivateContributionModificationDate",
                    "OAIDeletedConferenceModificationDate",
                    "OAIDeletedContributionModificationDate",
                    "OAIDeletedConferenceCategory",
                    "OAIDeletedContributionCategory",
                    "OAIDeletedPrivateConferenceModificationDate",
                    "OAIDeletedPrivateContributionModificationDate",
                    "OAIDeletedPrivateConferenceCategory",
                    "OAIDeletedPrivateContributionCategory"]

    def getIndex( self, name ):
        return self.getById(name)

    def getById( self, id ):
        """returns an object from the index which id corresponds to the one
            which is specified.
        """

        if id not in self.__allowedIdxs:
            raise MaKaCError( _("Unknown index: %s")%id)
        Idx = self._getIdx()
        if id in Idx.keys():
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
                Idx[str(id)] = CategoryDateIndex()
            elif id=="categoryName":
                Idx[str(id)] = TextIndex()
            elif id=="pendingSubmitters":
                Idx[str(id)] = PendingSubmittersIndex()
            elif id=="pendingSubmittersTasks":
                Idx[str(id)] = PendingSubmittersTasksIndex()
            elif id=="pendingManagers":
                Idx[str(id)] = PendingManagersIndex()
            elif id=="pendingManagersTasks":
                Idx[str(id)] = PendingManagersTasksIndex()
            elif id=="pendingCoordinators":
                Idx[str(id)] = PendingManagersIndex()
            elif id=="pendingCoordinatorsTasks":
                Idx[str(id)] = PendingManagersTasksIndex()
            elif id=="collaboration":
                if PluginsHolder().hasPluginType("Collaboration"):
                    from MaKaC.plugins.Collaboration.indexes import CollaborationIndex
                    Idx[str(id)] = CollaborationIndex()
                else:
                    raise MaKaCError(_("Tried to retrieve collaboration index, but Collaboration plugins are not present"))

            # OAI date indices
            elif id=="OAIConferenceModificationDate":
                Idx[str(id)] = OAIConferenceModificationDateIndex()
            elif id=="OAIContributionModificationDate":
                Idx[str(id)] = OAIContributionModificationDateIndex()
            elif id=="OAIPrivateConferenceModificationDate":
                Idx[str(id)] = OAIPrivateConferenceModificationDateIndex()
            elif id=="OAIPrivateContributionModificationDate":
                Idx[str(id)] = OAIPrivateContributionModificationDateIndex()
            elif id=="OAIDeletedConferenceModificationDate":
                Idx[str(id)] = OAIDeletedConferenceModificationDateIndex()
            elif id=="OAIDeletedContributionModificationDate":
                Idx[str(id)] = OAIDeletedContributionModificationDateIndex()
            elif id=="OAIDeletedPrivateConferenceModificationDate":
                Idx[str(id)] = OAIDeletedPrivateConferenceModificationDateIndex()
            elif id=="OAIDeletedPrivateContributionModificationDate":
                Idx[str(id)] = OAIDeletedPrivateContributionModificationDateIndex()


            # category indices
            elif id=="OAIDeletedConferenceCategory":
                Idx[str(id)] = OAIDeletedConferenceCategoryIndex()
            elif id=="OAIDeletedContributionCategory":
                Idx[str(id)] = OAIDeletedContributionCategoryIndex()
            elif id=="OAIDeletedPrivateConferenceCategory":
                Idx[str(id)] = OAIDeletedPrivateConferenceCategoryIndex()
            elif id=="OAIDeletedPrivateContributionCategory":
                Idx[str(id)] = OAIDeletedPrivateContributionCategoryIndex()
            else:
                Idx[str(id)] = Index()

            return Idx[str(id)]


if __name__ == "__main__":
    print _("done")



