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

"""
*Upcoming events* module
"""

import os, datetime, pickle, operator, time
from pytz import timezone
from persistent import Persistent

from MaKaC.common.cache import GenericCache
from MaKaC.common import timezoneUtils, indexes

from MaKaC.common.fossilize import Fossilizable, fossilizes
from MaKaC.fossils.modules import IObservedObjectFossil
import MaKaC.conference as conference

from MaKaC.common.logger import Logger
from MaKaC.common.utils import formatTime, formatDateTime
import MaKaC.webinterface.wcomponents as wcomponents

from indico.modules import Module


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
        self._ttl = datetime.timedelta(minutes=5)

    @property
    def _cache(self):
        return GenericCache('UpcomingEvents')

    def setCacheTTL(self, ttl):
        self._ttl = ttl
        self._cache.delete('public')

    def getCacheTTL(self):
        if not hasattr(self, '_ttl'):
            self._ttl = datetime.timedelta(minutes=5)
        return self._ttl

    def setNumberItems(self, number):
        self._maxEvents = number
        self._cache.delete('public')

    def getNumberItems(self):
        return self._maxEvents

    def addObject(self, object, weight, delta):
        """
        category - Category object
        weight - integer (negative allowed), zero by default
        """
        self._objects.append(ObservedObject(object, weight, delta))
        self._cache.delete('public')
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
        self._cache.delete('public')
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
        resultList = self._cache.get('public')

        if resultList is None:
            resultList = map(self._processEventDisplay, self._generateList())
            self._cache.set('public', resultList, self.getCacheTTL())

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


class WUpcomingEvents(wcomponents.WTemplated):

    def formatDateTime(self, dateTime):
        now = timezoneUtils.nowutc().astimezone(self._timezone)

        if dateTime.date() == now.date():
            return _("today") + " " + formatTime(dateTime.time())
        elif dateTime.date() == (now + datetime.timedelta(days=1)).date():
            return _("tomorrow") + " " + formatTime(dateTime.time())
        elif dateTime < (now + datetime.timedelta(days=6)):
            return formatDateTime(dateTime, format="EEEE H:mm")
        elif dateTime.date().year == now.date().year:
            return formatDateTime(dateTime, format="d MMM")
        else:
            return formatDateTime(dateTime, format="d MMM yyyy")

    def _getUpcomingEvents(self):
        # Just convert UTC to display timezone

        return map(lambda x: (x[0], x[1].astimezone(self._timezone), x[2], x[3]),
                   self._list)

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars['upcomingEvents'] = self._getUpcomingEvents()
        return vars

    def __init__(self, timezone, upcoming_list):
        self._timezone = timezone
        self._list = upcoming_list
        wcomponents.WTemplated.__init__(self)
