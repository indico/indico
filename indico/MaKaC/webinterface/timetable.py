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

import MaKaC.schedule as schedule
import MaKaC.conference as conference
from datetime import timedelta,datetime
import pytz
from pytz import timezone
from pytz import all_timezones
from MaKaC.errors import MaKaCError

class TimeTable(object):

    def __init__( self, schedule, tz = 'UTC'):
        self.setSlotLengthInMin(5)
        sd, ed = schedule.getAdjustedStartDate(tz), schedule.getAdjustedEndDate(tz)
        self.setStartDate( sd )
        self.setEndDate( ed )
        self._sch = schedule
        #self.listEntries = schedule.getEntries()
        self._tz = tz
        self.mapEntryList(self._sch.getEntries())





    def setStartDate( self, date):
        self.__startDate = date

    def getStartDate( self ):
        return self.__startDate

    def setEndDate( self, date ):
        self.__endDate = date

    def getEndDate( self ):
        return self.__endDate

    def getTZ( self ):
        return self._tz

    def getSchedule( self ):
        return self._sch

    def setSlotLengthInMin( self, minutes ):
        self._slotLength = timedelta( minutes=int(minutes) )

    def getSlotLength( self ):
        return self._slotLength

    def __initialise( self ):
        self._days = []
        iDate = self.getStartDate()
        eDate = self.getEndDate()
        dayDict = {}
        dayList = []

        while iDate.date()<=eDate.date():
            sTime = timedelta(hours=8)
            eTime = timedelta(hours=18, minutes=59)
            if self._sch:
                s = self._sch.calculateDayStartDate(iDate)
                schSTime = timedelta(hours=s.hour)
                e = self._sch.calculateDayEndDate(iDate)
                schETime = timedelta(hours=e.hour,minutes=59)
                if schSTime < sTime:
                    sTime = schSTime
                if schETime > eTime:
                    eTime = schETime
            # dayList is a list of tuples: date,starttime,endtime
            self._days.append( Day( iDate , sTime, \
                                            eTime, \
                                            self.getSlotLength() ) )
            iDate = timezone(self._tz).normalize(iDate+timedelta(days=1))

    def reGenerate( self ):
        self.__initialise()

    def getDayList( self ):
        return self._days

    def mapEntryList( self, entryList ):
        self.__initialise()
        for day in self.getDayList():
            day.clean()
            day.mapEntryList( entryList )

    def mapContainerList( self, containerList ):
        self.__initialise()
        for day in self.getDayList():
            day.clean()
        #to be optimised
        for day in self.getDayList():
            day.mapContainerList( containerList )

    def mapDisplayContainerList(self, containerList, aw):
        self.__initialise()
        for day in self.getDayList():
            day.clean()
        for day in self.getDayList():
            day.mapDisplayContainerList(containerList, aw)

    def compactDays(self):
        for day in self.getDayList():
            day.compact()

class Day(object):

    # def __init__( self, date, startTime, endTime, slotLength):
        # self.__date = date.replace(hour=0,minute=0,second=0)
        # self._tz = date.tzinfo
        # self.__initialise( startTime, endTime, slotLength )

    # def getDate( self ):
        # return self.__date

    # def getTZ( self ):
        # return self._tz

    # def __initialise( self, startTime, endTime, slotLength ):
        # self.__slots = []
        # iTime = startTime
        # while (iTime<=endTime):
            # d = self.getDate()
            # iTime_next = iTime + slotLength - timedelta(seconds=1)
            # sDate = d + iTime
            # eDate = d + iTime_next
            # self.__slots.append( TimeSlot( sDate, eDate ) )
            # iTime = iTime + slotLength


    # def getStartHour( self ):
        # try:
            # return self.__slots[0].getStartDate().hour
        # except:
            # return 23

    # def getEndHour( self ):
        # try:
            # return self.__slots[-1].getEndDate().hour
        # except:
            # return 0

    # def getSlotList( self ):
        # return self.__slots

    # def getSlotsOnHour( self, hour ):
        # slots = []
        # for slot in self.getSlotList():
            # if slot.getStartDate().hour == hour:
                # slots.append(slot)
        # return slots

    # def clean( self ):
        # for slot in self.getSlotList():
            # slot.clean()

    # def mapEntryList( self, l ):
       ## to be MUCH optimised
        # for entry in l:
            # for slot in self.getSlotList():
                # slot.mapEntry( entry )

    # def mapContainerList( self, l ):
        ##to be MUCH optimised

        # for sesSlot in l:
            # entryList = []
            # for contrib in sesSlot.getSchedule().getEntries():
                # entryList.append(contrib)
            # container = Container(sesSlot)
            # container.setEntries(entryList)
            # if entryList:
                # for entry in entryList:
                    # for slot in self.getSlotList():
                        # slot.mapEntry(entry)
                        # slot.mapContainer(container)
            # else:
                # for slot in self.getSlotList():
                    # slot.mapContainer(container)

    # def mapDisplayContainerList(self, l, aw):
     ##   to be MUCH optimised
        # for session in l:
            # if isinstance(session, conference.Session):
                # if not session.canAccess(aw):
                    # continue
                # elif not session.canView(aw):
                    # continue
                # entryList = []
                # if session.getScheduleType()=="poster":
                    # for slotEntry in session.getSchedule().getEntries():
                        # entryList.append(slotEntry)
                # else:
                    # for elt in session.getSchedule().getEntries():
                        # if isinstance(elt, schedule.LinkedTimeSchEntry) and \
                                # isinstance(elt.getOwner(), conference.SessionSlot):
                            # sesSlot = elt.getOwner()
                            # for slotEntry in sesSlot.getSchedule().getEntries():
                                # if slotEntry.getStartDate().astimezone(self._tz).date() == self.getDate().date():
                                    # if isinstance(slotEntry,schedule.LinkedTimeSchEntry) and isinstance(slotEntry.getOwner(), conference.Contribution):
                                        # if slotEntry.getOwner().canAccess(aw):
                                            # entryList.append(slotEntry)
                                    # else:
                                        # entryList.append(slotEntry)
                # container = Container(session)
                # container.setEntries(entryList)
                # for entry in entryList:
                    # for slot in self.getSlotList():
                        # slot.mapEntry(entry)
                        # if slot.getEntryList() != []:
                            # slot.mapContainer(container)
            # else:
                # for slot in self.getSlotList():
                    # slot.mapEntry(session)

    # def getNumMaxOverlaping( self ):
        # max = 0
        # for slot in self.getSlotList():
            # if slot.getNumEntriesOverlaped() > max:
                # max = slot.getNumEntriesOverlaped()
        # return max

    # def getNumSlots( self, entry ):
        # num = 0
        # for slot in self.getSlotList():
            # if entry in slot.getEntryList():
                # num += 1
        # return num

    # def getNumContainerSlots( self, entry ):
        # num = 0
        # lastSlot = None
        # for slot in self.getSlotList():
            # if entry in slot.getEntryList():
                # num += slot.getNumRows()
                # lastSlot = slot
        # nextSlot = self.getNextSlot(lastSlot)
        # if nextSlot != None and not lastSlot.hasFooters():
            # if nextSlot.hasHeaders():
                # num += 1
        # return num

    # def getNextSlot(self, slot):
        # if slot in self.getSlotList():
            # i = self.getSlotList().index(slot)
            # if i+1 < len(self.getSlotList()):
                # return self.getSlotList()[i+1]
        # return None


    # def hasEntryOverlaps(self,entry):
        # for slot in self.getSlotList():
            # entriesInSlot=slot.getEntryList()
            # if (entry in entriesInSlot) and len(entriesInSlot)>1:
                # return True
        # return False

    # def hasContainerOverlaps(self):
        # for slot in self.getSlotList():
            # if len(slot.getContainerList())>1:
                # return True
        # return False

    # def getContainerMaxOverlap(self):
        # contSet = sets.Set()
        # for slot in self.getSlotList():
            # contSet.union_update( sets.Set(slot.getContainerList()) )
        # max = 0
        # for cont in contSet:
            # max += cont.getMaxOverlap(self)
        # return max

    # def getNumContainers(self):
        # containerSet = sets.Set()
        # for slot in self.getSlotList():
            # slotContainerSet = sets.Set(slot.getContainerList())
            # containerSet.union_update(slotContainerSet)
        # return len(containerSet)

    # def removeSlot(self, slot):
        # if slot in self.getSlotList():
            # self.getSlotList().remove(slot)

    # def compact(self):
        # slotsToDelete = []
        # lastSlotWithZeroMin = -1
        # lastSlot = None
       ## --- Getting all the empty slots at the beginning of the day
        # for slot in self.getSlotList():
            # lastSlot = slot
            # if not slot.hasContainers():
                # slotsToDelete.append(slot)
                # if slot.getStartDate().minute == 0:
                    # lastSlotWithZeroMin = slotsToDelete.index(slot)
            # else:
                # break
        # if lastSlot and lastSlot.getStartDate().minute != 0 and lastSlotWithZeroMin != -1:
            # slotsToDelete = slotsToDelete[:lastSlotWithZeroMin]
       ## --- Getting all the empty slots at the beginning of the day
        # i = len(self.getSlotList()) - 1
        # while i >= 0:
            # slot = self.getSlotList()[i]
            # if not slot.hasContainers():
                # slotsToDelete.append(slot)
            # else:
                # break
            # i -= 1
        ## --- Doing Trim
        # for slot in slotsToDelete:
            # self.removeSlot(slot)

    # def isFirstSlot(self, slot):
        # if slot in self.getSlotList():
            # return self.getSlotList()[0] == slot
        # return False

    # def isLastSlot(self, slot):
        # if slot in self.getSlotList():
            # return self.getSlotList()[len(self.getSlotList())-1] == slot
        # return False

    # def getLastContainerSlot(self, container):
        # i = len(self.getSlotList()) - 1
        # while i>=0:
            # slot = self.getSlotList()[i]
            # if container in slot.getContainerList():
                # return slot
            # i -= 1
        # return None

    # def getNumEntriesWithoutContainer(self):
        # max = 0
        # for slot in self.getSlotList():
            # num = 0
            # for entry in slot.getEntryList():
                # isinconts = False
                # for container in slot.getContainerList():
                    # if entry in container.getEntryList():
                        # isinconts = True
                        # break
                # if not isinconts:
                    # num+=1
            # if max < num:
                # max = num
        # return max

    def __init__( self, date, startTime, endTime, slotLength):
        self.__date = date.replace(hour=0,minute=0,second=0)
        self._tz = date.tzinfo
        self.__initialise( startTime, endTime, slotLength )

    def getDate( self ):
        return self.__date

    def getTZ( self ):
        return self._tz

    def __initialise( self, startTime, endTime, slotLength ):
        self.__slots = []
        self.__entries = []
        iTime = startTime
        while (iTime<=endTime):
            d = self.getDate()
            iTime_next = iTime + slotLength - timedelta(seconds=1)
            sDate = d + iTime
            sDate = self._tz.normalize(sDate)
            eDate = d + iTime_next
            eDate = self._tz.normalize(eDate)
            self.__slots.append( TimeSlot( sDate, eDate ) )
            iTime = iTime + slotLength


    def getStartHour( self ):
        try:
            return self.__slots[0].getStartDate().hour
        except:
            return 23

    def getEndHour( self ):
        try:
            return self.__slots[-1].getEndDate().hour
        except:
            return 0

    def getSlotList( self ):
        return self.__slots

    def getSlotsOnHour( self, hour ):
        slots = []
        for slot in self.getSlotList():
            if slot.getStartDate().hour == hour:
                slots.append(slot)
        return slots

    def clean( self ):
        for slot in self.getSlotList():
            slot.clean()

    def getEntryList(self ):
        return self.__entries


    def addEntry(self, entry):
        self.__entries.append(entry)

    def mapEntryList( self, l ):
                # for entry in l:
            # for slot in self.getSlotList():
                # slot.mapEntry( entry )

         # to be MUCH optimised
        for entry in l:
            if entry.inDay(self.getDate()):
                self.addEntry(entry)
            for slot in self.getSlotList():
                slot.mapEntry( entry )

    def mapContainerList( self, l ):
        # to be MUCH optimised

        for sesSlot in l:
            entryList = []
            for contrib in sesSlot.getSchedule().getEntries():
                entryList.append(contrib)
            container = Container(sesSlot)
            container.setEntries(entryList)
            if entryList:
                for entry in entryList:
                    for slot in self.getSlotList():
                        slot.mapEntry(entry)
                        slot.mapContainer(container)
            else:
                for slot in self.getSlotList():
                    slot.mapContainer(container)

    def mapDisplayContainerList(self, l, aw):
        # to be MUCH optimised
        for session in l:
            if isinstance(session, conference.Session):
                if not session.canAccess(aw):
                    continue
                elif not session.canView(aw):
                    continue
                entryList = []
                if session.getScheduleType()=="poster":
                    for slotEntry in session.getSchedule().getEntries():
                        entryList.append(slotEntry)
                else:
                    for elt in session.getSchedule().getEntries():
                        if isinstance(elt, schedule.LinkedTimeSchEntry) and \
                                isinstance(elt.getOwner(), conference.SessionSlot):
                            sesSlot = elt.getOwner()
                            for slotEntry in sesSlot.getSchedule().getEntries():
                                if slotEntry.getStartDate().astimezone(self._tz).date() == self.getDate().date():
                                    if isinstance(slotEntry,schedule.LinkedTimeSchEntry) and isinstance(slotEntry.getOwner(), conference.Contribution):
                                        if slotEntry.getOwner().canAccess(aw):
                                            entryList.append(slotEntry)
                                    else:
                                        entryList.append(slotEntry)
                container = Container(session)
                container.setEntries(entryList)
                for entry in entryList:
                    for slot in self.getSlotList():
                        slot.mapEntry(entry)
                        if slot.getEntryList() != []:
                            slot.mapContainer(container)
            else:
                for slot in self.getSlotList():
                    slot.mapEntry(session)

    def getNumMaxOverlaping( self ):
        max = 0
        for slot in self.getSlotList():
            if slot.getNumEntriesOverlaped() > max:
                max = slot.getNumEntriesOverlaped()
        return max

    def getNumSlots( self, entry ):
        num = 0
        for slot in self.getSlotList():
            if entry in slot.getEntryList():
                num += 1
        return num

    def getNumContainerSlots( self, entry ):
        num = 0
        lastSlot = None
        for slot in self.getSlotList():
            if entry in slot.getEntryList():
                num += slot.getNumRows()
                lastSlot = slot
        nextSlot = self.getNextSlot(lastSlot)
        if nextSlot != None and not lastSlot.hasFooters():
            if nextSlot.hasHeaders():
                num += 1
        return num

    def getNextSlot(self, slot):
        if slot in self.getSlotList():
            i = self.getSlotList().index(slot)
            if i+1 < len(self.getSlotList()):
                return self.getSlotList()[i+1]
        return None


    def hasEntryOverlaps(self,entry):
        for slot in self.getSlotList():
            entriesInSlot=slot.getEntryList()
            if (entry in entriesInSlot) and len(entriesInSlot)>1:
                return True
        return False

    def hasContainerOverlaps(self):
        for slot in self.getSlotList():
            if len(slot.getContainerList())>1:
                return True
        return False

    def getContainerMaxOverlap(self):
        contSet = set()
        for slot in self.getSlotList():
            contSet.update( set(slot.getContainerList()) )
        max = 0
        for cont in contSet:
            max += cont.getMaxOverlap(self)
        return max

    def getNumContainers(self):
        containerSet = set()
        for slot in self.getSlotList():
            slotContainerSet = set(slot.getContainerList())
            containerSet.update(slotContainerSet)
        return len(containerSet)

    def removeSlot(self, slot):
        if slot in self.getSlotList():
            self.getSlotList().remove(slot)

    def compact(self):
        slotsToDelete = []
        lastSlotWithZeroMin = -1
        lastSlot = None
        # --- Getting all the empty slots at the beginning of the day
        for slot in self.getSlotList():
            lastSlot = slot
            if not slot.hasContainers():
                slotsToDelete.append(slot)
                if slot.getStartDate().minute == 0:
                    lastSlotWithZeroMin = slotsToDelete.index(slot)
            else:
                break
        if lastSlot and lastSlot.getStartDate().minute != 0 and lastSlotWithZeroMin != -1:
            slotsToDelete = slotsToDelete[:lastSlotWithZeroMin]
        # --- Getting all the empty slots at the beginning of the day
        i = len(self.getSlotList()) - 1
        while i >= 0:
            slot = self.getSlotList()[i]
            if not slot.hasContainers():
                slotsToDelete.append(slot)
            else:
                break
            i -= 1
        # --- Doing Trim
        for slot in slotsToDelete:
            self.removeSlot(slot)

    def isFirstSlot(self, slot):
        if slot in self.getSlotList():
            return self.getSlotList()[0] == slot
        return False

    def isLastSlot(self, slot):
        if slot in self.getSlotList():
            return self.getSlotList()[len(self.getSlotList())-1] == slot
        return False

    def getLastContainerSlot(self, container):
        i = len(self.getSlotList()) - 1
        while i>=0:
            slot = self.getSlotList()[i]
            if container in slot.getContainerList():
                return slot
            i -= 1
        return None

    def getNumEntriesWithoutContainer(self):
        max = 0
        for slot in self.getSlotList():
            num = 0
            for entry in slot.getEntryList():
                isinconts = False
                for container in slot.getContainerList():
                    if entry in container.getEntryList():
                        isinconts = True
                        break
                if not isinconts:
                    num+=1
            if max < num:
                max = num
        return max

class TimeSlot(object):

    def __init__( self, startDateTime, endDateTime ):
        self.__start = startDateTime
        self.__end = endDateTime
        self.__entries = []
        self._containers = []
        self._header = False
        self._footer = False
        self._tz = startDateTime.tzinfo

    def getStartDate( self ):
        return self.__start

    def getAdjustedStartDate( self, tz=None ):
        if not tz:
            tz = self._tz
        else:
            tz = timezone(tz)
        return self.__start.astimezone(tz)

    def getEndDate( self ):
        return self.__end

    def getAdjustedEndDate( self, tz=None ):
        if not tz:
            tz = self._tz
        else:
            tz = timezone(tz)
        return self.__end.astimezone(tz)

    def getTZ( self ):
        return self._tz

    def clean( self ):
        self.__entries = []

    def mapEntry( self, entry ):
        c = entry.getOwner()
        sDate = self.getStartDate()
        eDate = self.getEndDate()
        if (entry.getStartDate() <= eDate and entry.getEndDate() > sDate):
            self.__entries.append( entry )
        elif entry.getDuration() is None or entry.getDuration() == timedelta(0):
            entryEndDate=entry.getStartDate()+timedelta(seconds=5)
            if (entry.getStartDate() <= eDate and entryEndDate > sDate):
                self.__entries.append( entry )

    def mapContainer( self, c ):
        sDate = self.getStartDate()
        eDate = self.getEndDate()
        if c.getStartDate() <= eDate and c.getEndDate() > sDate:
            if c not in self._containers:
                self._containers.append( c )
                if c.isFirstSlot(self):
                    self._header = True
                if c.isLastSlot(self):
                    self._footer = True

    def getEntryList( self ):
        return self.__entries

    def getContainerList( self ):
        return self._containers

    def temp(self):
        l = []
        for entry in self.getEntryList():
            l.append( entry.getTitle() )
        return "; ".join( l )

    def getNumEntriesOverlaped(self):
        return len(self.__entries)

    def getNumContainersOverlaped(self):
        return len(self._containers)

    def getContainer(self, entry):
        for cont in self._containers:
            if entry in cont.getEntryList():
                return cont
        return None

    def getContainerEntry(self, container):
        if container in self._containers:
            for entry in container.getEntryList():
                if entry in self.getEntryList():
                    return entry
        return None

    def getContainerEntries(self, container):
        l = []
        if container in self._containers:
            for entry in container.getEntryList():
                if entry in self.getEntryList():
                    l.append(entry)
        return l

    def hasContainers(self):
        return self.getContainerList() != []

    def getNumRows(self):
        num = 1
        if self._header:
            num += 1
        if self._footer:
            num += 1
        return num

    def isFirstSlotEntry(self, entry):
        if entry.getStartDate() >= self.getStartDate() and entry.getStartDate() < self.getEndDate():
            return True
        else:
            return False

    def hasHeaders(self):
        return self._header

    def hasFooters(self):
        return self._footer

    def hasEntry(self, entry):
        return entry in self.getEntryList()

    def getEntriesWithoutContainer(self):
        r = []
        for entry in self.getEntryList():
            isinconts = False
            for container in self.getContainerList():
                if entry in container.getEntryList():
                    isinconts = True
                    break
            if not isinconts:
                r.append(entry)
        return r

def sortEntries(x,y):
    try:
        return cmp(x.getOwner().getSession().getTitle(),y.getOwner().getSession().getTitle())
    except:
        return cmp(x.getTitle(),y.getTitle())

class Container(object):

    def __init__(self, sesSlot ):
        self._sesSlot = sesSlot
        self._entries = []

    def getEntryList(self):
        return self._entries

    def setEntries(self, entries):
        self._entries = entries

    def hasEntry(self, entry):
        return entry in self._entries

    def isFirstSlot(self, slot):
        sDate = slot.getStartDate()
        eDate = slot.getEndDate()
        if (self.getStartDate() >= sDate) and (self.getStartDate() <= eDate):
            return True
        return False

    def isLastSlot(self, slot):
        slot_sDate = slot.getStartDate()
        slot_eDate = slot.getEndDate()
        edate = self.getEndDate() - timedelta(minutes=1)
        if (self.getEndDate() >= slot_sDate) and ( edate <= slot_eDate):
            return True
        return False

    def getStartDate(self):
        return self._sesSlot.getStartDate()

    def getAdjustedStartDate(self, tz=None):
        return self._sesSlot.getAdjustedStartDate(tz)

    def getEndDate(self):
        return self._sesSlot.getEndDate()

    def getAdjustedEndDate(self, tz=None):
        return self._sesSlot.getAdjustedEndDate(tz)

    def getRoom(self):
        return self._sesSlot.getRoom()

    def getId(self):
        return self._sesSlot.getId()

    def getTitle(self):
        return self._sesSlot.getTitle()

    def getContribDuration(self):
        return self._sesSlot.getContribDuration()

    def getDuration(self):
        return self._sesSlot.getDuration()

    def getSessionSlot(self):
        return self._sesSlot

    def getConvenerList(self):
        return self._sesSlot.getConvenerList()

    def getMaxOverlap(self, day):
        max = 1
        for slot in day.getSlotList():
            numEntries = 0
            for entry in slot.getEntryList():
                if entry in self.getEntryList():
                    numEntries += 1
            if max < numEntries:
                max = numEntries
        return max

    def isFinalEntry(self, entry, lastSlot, tz):
        # lastSlot is a day object which is not timezone aware.
        d = lastSlot.getStartDate().astimezone(timezone(tz))
        lastSlotStartDate = d.astimezone(timezone(tz))
        if lastSlot:
            return entry.getEndDate() > lastSlotStartDate
        return False

    def getNumEntries(self):
        return len(self.getSessionSlot().getSchedule().getEntries())

    def getAllocatedTime(self):
        d = timedelta(0,0,0)
        for entry in self.getEntryList():
            d += entry.getDuration()
        return d

    def hasOverlaps(self):
        for entry in self.getEntryList():
            for entry2 in self.getEntryList():
                if entry != entry2 and \
                        entry.getStartDate() < entry2.getEndDate() and  \
                        entry.getEndDate() > entry2.getStartDate():
                    return True
        return False


class PlainTimeTable(object):

    def __init__( self, schedule=None, tz = 'UTC' ):
        self._tz = tz
        sd, ed = schedule.getAdjustedStartDate(tz), schedule.getAdjustedEndDate(tz)
        self.setStartDate( sd )
        self.setEndDate( ed )

    def getTZ(self):
        return self._tz

    def setStartDate( self, date):
        self._startDate = date

    def getStartDate( self ):
        return self._startDate

    def setEndDate( self, date):
        self._endDate = date

    def getEndDate( self ):
        return self._endDate

    def _initialise( self ):
        self._days = []
        iDate = self.getStartDate()
        while iDate.date()<=self.getEndDate().date():
            self._days.append( PlainDay( iDate ) )
            iDate = iDate+timedelta(days=1)

    def reGenerate( self ):
        self._initialise()

    def getDayList( self ):
        return self._days

    def mapEntryList( self, entryList, aw, hd ):
        self._initialise()
        #to be optimised
        lastIndex = 0
        for day in self.getDayList():
            entryList = entryList[lastIndex:]
            lastIndex = day.mapEntryList( entryList, aw, hd )


class PlainDay(object):

    def __init__( self, date ):
        self._date = date
        self._initialise()
        self._tz = date.tzinfo

    def getTZ( self ):
        return self._tz

    def getDate( self ):
        return self._date

    def _initialise( self ):
        self._events = []

    def getEventList( self ):
        return self._events

    def mapEntryList(self,l,aw,highDetail):
        # to be MUCH optimised
        addedSessions = []
        lastIndex=-1
        tz = self.getTZ()
        for entry in l:
            if self.getDate().date()==entry.getStartDate().astimezone(tz).date():
                if isinstance(entry,conference.SessionSlot):
                    session=entry.getSession()
                    s=SessionSlot(entry,self)
                    s.mapEntries(aw)
                    self._events.append(s)
                else:
                    s = ConfEntry(entry)
                    self._events.append(s)
                lastIndex=l.index(entry)
        return lastIndex+1

    def getDate(self):
        return self._date

class SessionSlot(object):

    def __init__(self,sesSlot,day):
        self._sesSlot=sesSlot
        self._entries=[]
        self._day=day

    def getTitle(self):
        if self._sesSlot.getTitle()!="":
            return "%s: %s"%(self._sesSlot.getSession().getTitle(),self._sesSlot.getTitle())
        return self._sesSlot.getSession().getTitle()

    def mapEntries(self,aw):
        for entry in self._sesSlot.getSchedule().getEntries():
            if entry.getStartDate().date() == self._day.getDate().date():
                if isinstance(entry,schedule.LinkedTimeSchEntry):
                    if isinstance(entry.getOwner(),conference.Contribution):
                        if entry.getOwner().canAccess(aw):
                            self._entries.append(entry)
                else:
                    self._entries.append(entry)

    def getOwner(self):
        return self._sesSlot

    def _getStartDateForDay(self):
        entryList=self._sesSlot.getSchedule().getEntries()
        resDate=self._sesSlot.getStartDate()
        for entry in entryList:
            if entry.getStartDate().date()==self._day.getDate().date():
                resDate=entry.getStartDate()
                break
        return resDate

    def _getEndDateForDay(self):
        entryList=self._sesSlot.getSchedule().getEntries()
        resDate=self._sesSlot.getEndDate()
        i = len(entryList)-1
        while i>0:
            entry = entryList[i]
            if entry.getEndDate().date() == self._day.getDate().date():
                resDate = entry.getEndDate()
                break
            i -= 1
        return resDate

    def getStartDate(self):
        if len(self._entries)==0:
            return self._getStartDateForDay()
        else:
            return self._entries[0].getStartDate()

    def getEndDate(self):
        if len(self._entries)==0:
            return self._getEndDateForDay()
        else:
            return self._entries[-1].getEndDate()

    def getEntryList(self):
        return self._entries

    def hasEntries(self):
        return len(self._entries)!=0

    def getAdjustedStartDate(self,tz=None):
        if not tz:
            tz = self.getTimezone()
        if tz not in all_timezones:
           tz = 'UTC'
        return self.getStartDate().astimezone(timezone(tz))

    def getAdjustedEndDate(self,tz=None):
        if not tz:
            tz = self.getTimezone()
        if tz not in all_timezones:
           tz = 'UTC'
        return self.getStartDate().astimezone(timezone(tz))


class ConfEntry(object):

    def __init__(self, entry):
        self._entry = entry

    def getTitle(self):
        return self._entry.getTitle()

    def isBreak(self):
        return not isinstance(self._entry, schedule.LinkedTimeSchEntry)

    def getOwner(self):
        return self._entry.getOwner()

    def getStartDate(self):
        return self._entry.getStartDate()

    def getEndDate(self):
        return self._entry.getEndDate()

    def getDuration(self):
        return self._entry.getDuration()

    def getAdjustedStartDate(self,tz=None):
        if not tz:
            tz = self.getTimezone()
        if tz not in all_timezones:
           tz = 'UTC'
        return self.getStartDate().astimezone(timezone(tz))

    def getAdjustedEndDate(self,tz=None):
        if not tz:
            tz = self.getTimezone()
        if tz not in all_timezones:
           tz = 'UTC'
        return self.getStartDate().astimezone(timezone(tz))
