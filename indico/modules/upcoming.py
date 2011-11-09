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

"""
*Upcoming events* module
"""

import os, datetime, pickle, operator, time
from pytz import timezone
from persistent import Persistent

from MaKaC.common.cache import MultiLevelCache, MultiLevelCacheEntry
from MaKaC.common import timezoneUtils, indexes

from MaKaC.common.fossilize import Fossilizable, fossilizes
from MaKaC.fossils.modules import IObservedObjectFossil
import MaKaC.conference as conference

from MaKaC.common.logger import Logger

from indico.modules import Module


class UECacheEntry(MultiLevelCacheEntry):

    def getId(self):
        """
        Fixed id
        """
        return 'events'

    @classmethod
    def create(cls, content):
        entry = cls()
        entry.setContent(content)
        return entry


class UpcomingEventsCache(MultiLevelCache, Persistent):

    """
    Cache for upcoming events (per user)
    """

    _entryFactory = UECacheEntry

    def __init__(self, ttl=datetime.timedelta(minutes=5), dirty=False):
        MultiLevelCache.__init__(self, 'upcoming_events')
        self._dirty = dirty
        self.setTTL(ttl)

    def _generateFileName(self, entry, version):
        return entry.getId()

    def isDirty(self, mtime, object):
        return self._dirty or super(UpcomingEventsCache, self).isDirty(mtime, object)

    def invalidate(self):
        self._dirty = True;

    def setTTL(self, ttl):
        if isinstance(ttl, datetime.timedelta):
            ttl = (86400 * ttl.days + ttl.seconds)
        super(UpcomingEventsCache, self).setTTL(ttl)

    def loadObject(self):
        # TODO: Use user IDs, private events
        return MultiLevelCache.loadObject(self, '')

    def cacheObject(self, object):
        # TODO: Use user IDs, private events
        MultiLevelCache.cacheObject(self, '', object)
        self._dirty = False

class ObservedObject(Persistent, Fossilizable):

    fossilizes(IObservedObjectFossil)

    def __init__(self, obj, weight, advertisingDelta):
        """
        obj - the object to encapsulate
        weight - the weight that is associated with
        the object
        """

        self.obj = obj
        self.weight = weight
        self.advertisingDelta = advertisingDelta

    def getObject(self):
        return self.obj

    def getWeight(self):
        return self.weight

    def getAdvertisingDelta(self):
        return self.advertisingDelta

class UpcomingEventsModule(Module):
    """
    This module contains all the information and logics that support
    the *upcoming events* feature.
    """

    id = "upcoming_events"

    def __init__(self):

        # id, weight dictionary = id is the category id and
        # weight determines the position of the categories'
        # events in the list
        self._objects = []
        self._maxEvents = 10
        self._cache = UpcomingEventsCache()

    def setCacheTTL(self, ttl):
        self._cache.setTTL(ttl)
        self._cache.invalidate()

    def getCacheTTL(self):
        return datetime.timedelta(seconds=self._cache.getTTL())

    def setNumberItems(self, number):
        self._maxEvents = number
        self._cache.invalidate()

    def getNumberItems(self):
        return self._maxEvents

    def addObject(self, object, weight, delta):
        """
        category - Category object
        weight - integer (negative allowed), zero by default
        """
        self._objects.append(ObservedObject(object, weight, delta))
        self._cache.invalidate()
        self._p_changed = 1

    def removeObject(self, obj):
        element = None
        for observed in self._objects:
            if observed.getObject() == obj:
                element = observed
                break

        if not element:
            raise Exception('Element not in list')
        self._objects.remove(element)
        self._cache.invalidate()
        self._p_changed = 1

    def hasObject(self, obj):
        for observed in self._objects:
            if observed.getObject() == obj:
                return True
                break

        return False

    def getObjectList(self):
        return self._objects

    def processEvent(self, date, eventObj, obj, objDict):

        if (not eventObj.hasAnyProtection() and
            (date > (eventObj.getStartDate() - obj.getAdvertisingDelta()))):
            weight = float(obj.getWeight())
            if not objDict.has_key(weight):
                objDict[weight] = []

            objDict[weight].append(eventObj)


    def _processEventDisplay(self, event):

        dateTime = event.getStartDate()

        if dateTime < timezoneUtils.nowutc():
            status = 'ongoing'
            # return end date instead (for 'ongoing till...')
            dateTime = event.getEndDate()
        elif dateTime.date() == timezoneUtils.nowutc().date():
            status = 'today'
        else:
            status = 'future'

        return (status, dateTime, event.getTitle(), event.getId())

    def getUpcomingEventList(self):

        try:
            # check if there's a valid cached copy first
            fromCache = self._cache.loadObject()
        except:
            Logger.get('upcoming_events').exception("Upcoming events cache read error")
            fromCache = None

        if fromCache:
            # Cache hit!
            resultList = fromCache.getContent()
        else:
            resultList = map(self._processEventDisplay, self._generateList())

            # cache the results
            self._cache.cacheObject(resultList)

        return resultList

    def _generateList(self, date=None):

        if not date:
            date = timezoneUtils.nowutc()

        categDateIdx = indexes.IndexesHolder().getById('categoryDate')

        objDict = {}

        for obj in self._objects:
            wrappedObj = obj.getObject()
            if isinstance(wrappedObj, conference.Conference):
                self.processEvent(date, wrappedObj, obj, objDict)
            elif isinstance(wrappedObj, conference.Category):
                events = categDateIdx.getObjectsIn(
                    wrappedObj.getId(),
                    date, date + obj.getAdvertisingDelta())
                for conf in events:
                    self.processEvent(date, conf, obj, objDict)

        resultList = []
        keys = objDict.keys()
        keys.sort(reverse=True)

        for weight in keys:
            sortedEvents = objDict[weight]
            sortedEvents.sort(key=operator.attrgetter('startDate'))
            for elem in sortedEvents:
                resultList.append(elem)
                if len(resultList) == self._maxEvents:
                    break

        # sort again, so that the final result is an ordered list
        # that is suitable for display
        resultList.sort(key=operator.attrgetter('startDate'))

        Logger.get('upcoming_events').info("Regenerated upcoming event cache")

        return resultList
