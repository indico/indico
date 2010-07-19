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
        self._ttl = ttl
        self._dirty = dirty
        MultiLevelCache.__init__(self, 'upcoming_events')

    def _generateFileName(self, entry, version):
        return entry.getId()

    def isDirty(self, path, object):

        creationTime = datetime.datetime(*time.localtime(os.path.getmtime(path))[:6])

        if self._dirty or (datetime.datetime.now() - creationTime) > self._ttl:
            return True
        else:
            return False

    def invalidate(self):
        self._dirty = True;

    def setTTL(self, ttl):
        self._ttl = ttl

    def getTTL(self):
        return self._ttl

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
        return self._cache.getTTL()

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

        # check if there's a valid cached copy first
        fromCache = self._cache.loadObject()

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
            if isinstance(obj.getObject(), conference.Conference):
                self.processEvent(date, obj.getObject(), obj, objDict)
            elif isinstance(obj.getObject(), conference.Category):
                events = categDateIdx.getObjectsIn(obj.getObject().getId(),
                                                           date,
                                                           date+obj.getAdvertisingDelta())
                ## HACK: Remove  when this version goes into production (See above)
                for eventId in events:
                    try:
                        conf = conference.ConferenceHolder().getById(eventId)
                        self.processEvent(date, conf, obj, objDict)
                    except:
                        pass


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
