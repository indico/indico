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

"""
"""
import copy
from persistent import Persistent
from datetime import datetime,timedelta
from MaKaC.common.Counter import Counter
from MaKaC.errors import MaKaCError, TimingError, ParentTimingError,\
    EntryTimingError
from MaKaC.common import utils
from MaKaC.trashCan import TrashCanManager
from MaKaC.i18n import _
from pytz import timezone
from MaKaC.common.utils import daysBetween
from MaKaC.common.PickleJar import Retrieves
from MaKaC.common.PickleJar import DictPickler
from MaKaC.common.Conversion import Conversion
from MaKaC.common.contextManager import ContextManager
from MaKaC.common.fossilize import Fossilizable, fossilizes
from MaKaC.fossils.schedule import IContribSchEntryDisplayFossil,\
        IContribSchEntryMgmtFossil, IBreakTimeSchEntryFossil,\
        IBreakTimeSchEntryMgmtFossil,\
        ILinkedTimeSchEntryDisplayFossil, ILinkedTimeSchEntryMgmtFossil

class Schedule:
    """base schedule class. Do NOT instantiate
    """

    def __init__( self, owner ):
        pass

    def getEntries( self ):
        return []

    def addEntry( self, entry, position=None ):
        return

    def removeEntry( self, entry ):
        return

    def getEntryPosition( self, entry ):
        return

    def moveEntry( self, entry, newPosition, after=1 ):
        return

    def getEntryLocator( self, entry ):
        return

    def getOwner( self ):
        return

    def reSchedule( self ):
        return

    def getEntryInPos( self, pos ):
        return None


class TimeSchedule(Schedule, Persistent):
    """
    """

    def __init__(self,owner):
        self._entries=[]
        self._owner=owner
        self._entryGen=Counter()
        self._v_allowReSchedule=True
        self._allowParallel=True

    def notifyModification(self):
        self.getOwner().notifyModification()

    @Retrieves(['MaKaC.schedule.TimeSchedule',
                'MaKaC.schedule.ConferenceSchedule'], 'entries', isPicklableObject=True)
    def getEntries( self ):
        return self._entries

    def hasEntriesBefore(self,d):
        """Tells wether there is any entry before the specified date
        """
        entries=self.getEntries()
        if len(entries)==0:
            return False
        return entries[0].getStartDate()<d

    def hasEntriesAfter(self,d):
        """Tells wether there is any entry after the specified date
        """
        entries=self.getEntries()
        if len(entries)==0:
            return False
        return self.calculateEndDate()>d

    def checkSanity( self ):
        if self.hasEntriesBefore(self.getStartDate()) or self.hasEntriesAfter(self.getEndDate()):
            raise TimingError("Sorry, cannot perform this date change as some entries in the timetable would fall outside the new dates.")

    def isOutside(self,entry):
        """Tells whether an entry is outside the date boundaries of the schedule
        """
        ######################################
        # Fermi timezone awareness           #
        ######################################
        if entry.getStartDate() is not None:
            if entry.getStartDate()<self.getStartDate('UTC') or \
                    entry.getStartDate()>self.getEndDate('UTC'):
                return True
        if entry.getEndDate() is not None:
            if entry.getEndDate()<self.getStartDate('UTC') or \
                    entry.getEndDate()>self.getEndDate('UTC'):
                return True
        return False

    def hasEntry(self,entry):
        return entry.isScheduled() and entry.getSchedule()==self and\
            entry in self._entries

    def _addEntry(self,entry,check=2):
        """check parameter:
            0: no check at all
            1: check and raise error in case of problem
            2: check and adapt the owner dates"""
        if entry.isScheduled():
            # remove it from the old schedule and add it to this one
            entry.getSchedule().removeEntry(entry)

        owner = self.getOwner()
        tz = owner.getConference().getTimezone()

        # If user has entered start date use these dates
        # if the entry has not a pre-defined start date we try to find a place
        # within the schedule to allocate it
        if entry.getStartDate() is None:
            sDate=self.findFirstFreeSlot(entry.getDuration())
            if sDate is None:
                if check==2:
                    newEndDate = self.getEndDate() + entry.getDuration()

                    ContextManager.get('autoOps').append((owner,
                                                          "OWNER_END_DATE_EXTENDED",
                                                          owner,
                                                          newEndDate.astimezone(timezone(tz))))

                    owner.setEndDate(newEndDate, check)
                    sDate = self.findFirstFreeSlot(entry.getDuration())
                if sDate is None:
                    raise ParentTimingError( _("There is not enough time found to add this entry in the schedule (duration: %s)")%entry.getDuration(), _("Add Entry"))
            entry.setStartDate(sDate)
        #if the entry has a pre-defined start date we must make sure that it is
        #   not outside the boundaries of the schedule
        else:
            if entry.getStartDate() < self.getStartDate('UTC'):
                if check==1:
                    raise TimingError( _("Cannot schedule this entry because its start date (%s) is before its parents (%s)")%(entry.getAdjustedStartDate(),self.getAdjustedStartDate()),_("Add Entry"))
                elif check == 2:
                    ContextManager.get('autoOps').append((owner,
                                                          "OWNER_START_DATE_EXTENDED",
                                                          owner,
                                                          entry.getAdjustedStartDate(tz=tz)))
                    owner.setStartDate(entry.getStartDate(),check)
            elif entry.getEndDate()>self.getEndDate('UTC'):
                if check==1:
                    raise TimingError( _("Cannot schedule this entry because its end date (%s) is after its parents (%s)")%(entry.getAdjustedEndDate(),self.getAdjustedEndDate()),_("Add Entry"))
                elif check == 2:
                    ContextManager.get('autoOps').append((owner,
                                                          "OWNER_END_DATE_EXTENDED",
                                                          owner,
                                                          entry.getAdjustedEndDate(tz=tz)))
                    owner.setEndDate(entry.getEndDate(),check)
        #we make sure the entry end date does not go outside the schedule
        #   boundaries
        if entry.getEndDate() is not None and \
                (entry.getEndDate()<self.getStartDate('UTC') or \
                entry.getEndDate()>self.getEndDate('UTC')):
            raise TimingError( _("Cannot schedule this entry because its end date (%s) is after its parents (%s)")%(entry.getAdjustedEndDate(),self.getAdjustedEndDate()), _("Add Entry"))
        self._entries.append(entry)
        entry.setSchedule(self,self._getNewEntryId())
        self.reSchedule()
        self._p_changed = 1

    def _setEntryDuration(self,entry):
        if entry.getDuration() is None:
            entry.setDuration(0,5)

    def addEntry(self,entry):
        if (entry is None) or self.hasEntry(entry):
            return
        self._setEntryDuration(entry)
        result = self._addEntry(entry)
        self._p_changed = 1
        return result

    def _removeEntry(self,entry):
        self._entries.remove(entry)
        entry.setSchedule(None,"")
        entry.setStartDate(None)
        entry.delete()
        self._p_changed = 1

    def removeEntry(self,entry):
        if entry is None or not self.hasEntry(entry):
            return
        self._removeEntry(entry)

    def getEntryPosition( self, entry ):
        return self._entries.index( entry )

    def getOwner( self ):
        return self._owner

    ####################################
    # Fermi timezone awareness         #
    ####################################

    def getStartDate( self ,tz='UTC'):
        return self.getOwner().getAdjustedStartDate(tz)

    @Retrieves(['MaKaC.schedule.TimeSchedule',
                'MaKaC.schedule.ConferenceSchedule'], 'startDate', Conversion.datetime)
    def getAdjustedStartDate( self, tz=None ):
        return self.getOwner().getAdjustedStartDate(tz)

    def getEndDate( self, tz='UTC'):
        return self.getOwner().getAdjustedEndDate(tz)

    @Retrieves(['MaKaC.schedule.TimeSchedule',
                'MaKaC.schedule.ConferenceSchedule'], 'endDate', Conversion.datetime)
    def getAdjustedEndDate( self, tz=None):
        return self.getOwner().getAdjustedEndDate(tz)

    ####################################
    # Fermi timezone awareness(end)    #
    ####################################

    def cmpEntries(self,e1,e2):
        return cmp(e1.getStartDate(),e2.getStartDate())

    def reSchedule(self):
        try:
            if self._allowParalell:
                pass
        except AttributeError:
            self._allowParallel=True
        try:
            if self._v_allowReSchedule:
                pass
        except AttributeError:
            self._v_allowReSchedule=True
        if self._v_allowReSchedule:
            self._v_allowReSchedule=False
            self._entries.sort(self.cmpEntries)
            lastEntry=None
            for entry in self._entries:
                if lastEntry is not None:
                    if not self._allowParallel:
                        if lastEntry.collides(entry):
                            entry.setStartDate(lastEntry.getEndDate())
                lastEntry=entry
            self._v_allowReSchedule=True
        self._p_changed = 1

    def calculateEndDate( self ):
        if len(self._entries) == 0:
            return self.getStartDate()
        eDate = self.getStartDate()
        for entry in self._entries:
            if entry.getEndDate()>eDate:
                eDate = entry.getEndDate()
        return eDate

    def calculateStartDate( self ):
        if len(self._entries) == 0:
            return self.getStartDate()
        else:
            return self._entries[0].getStartDate()

    def getTimezone( self ):
        return self.getOwner().getConference().getTimezone()

    def getFirstFreeSlotOnDay(self,day):
        if not day.tzinfo:
            day = timezone(self.getTimezone()).localize(day)
        tz = day.tzinfo
        entries = self.getEntriesOnDay(day)
        if len(entries)==0:
            if self.getStartDate().astimezone(tz).date() == day.date():
                return self.getStartDate().astimezone(tz)
            return day.astimezone(timezone(self.getTimezone())).replace(hour=8,minute=0).astimezone(tz)
        else:
            return self.calculateDayEndDate(day)

    def calculateDayEndDate(self,day,hour=0,min=0):
        if day is None:
            return self.calculateEndDate()
        if not day.tzinfo:
            day = timezone(self.getTimezone()).localize(day)
        tz = day.tzinfo
        maxDate=day.replace(hour=hour,minute=min)
        entries = self.getEntriesOnDay(day)
        if hour != 0 or min != 0:
            return maxDate
        elif len(entries)==0:
            confstime = self.getOwner().getAdjustedStartDate()
            return day.astimezone(timezone(self.getTimezone())).replace(hour=confstime.hour,minute=confstime.minute).astimezone(tz)
        else:
            for entry in entries:
                if entry.getEndDate()>maxDate:
                    maxDate=entry.getEndDate().astimezone(tz)
            if maxDate.date() != day.date():
                maxDate = day.replace(hour=23,minute=59)
            return maxDate

    def calculateDayStartDate( self, day ):
        #
        # This determines where the times start on the time table.
        # day is a tz aware datetime
        if not day.tzinfo:
            day = timezone(self.getTimezone()).localize(day)
        tz = day.tzinfo
        entries = self.getEntriesOnDay(day)
        if len(entries) == 0:
            return timezone(self.getTimezone()).localize(datetime(day.year,day.month,day.day,8,0)).astimezone(tz)
        else:
            for entry in entries:
                if entry.getStartDate().astimezone(tz).date() >= day.date():
                    return entry.getStartDate().astimezone(tz)
                else:
                    return day.replace(hour=0,minute=0)

    def getEntryInPos( self, pos ):
        try:
            return self.getEntries()[int(pos)]
        except IndexError:
            return None

    def getEntriesOnDay( self, day ):
        """Returns a list containing all the entries which occur whithin the
            specified day. These entries will be ordered descending.
        """
        if not day.tzinfo:
            day = timezone(self.getTimezone()).localize(day)
        res = []
        for entry in self.getEntries():
            if entry.inDay( day ):
                res.append( entry )
        return res

    def getEntriesOnDate( self, date ):
        """Returns a list containing all the entries which occur whithin the
            specified day. These entries will be ordered descending.
        """
        res = []
        for entry in self.getEntries():
            if entry.onDate( date ):
                res.append( entry )
        return res

    def _getNewEntryId(self):
        try:
            if self._entryGen:
                pass
        except AttributeError:
            self._entryGen=Counter()
        return str(self._entryGen.newCount())

    def getEntryById(self,id):
        for entry in self.getEntries():
            if entry.getId()==str(id).strip():
                return entry
        return None

    def hasGap(self):
        """check if schedule has gap between two entries"""
        entries = self.getEntries()
        if len(entries) > 1:
            sDate = self.getStartDate('UTC')
            for entry in entries:
                if entry.getStartDate()!=sDate:
                    return True
                sDate = entry.getEndDate()
        return False

    def compact(self):
        """removes any overlaping among schedule entries and make them go one
            after the other without any gap
        """
        self._v_allowReSchedule=False
        refDate=self.getStartDate('UTC')
        for entry in self._entries:
            entry.setStartDate(refDate)
            refDate=entry.getEndDate()
        self._v_allowReSchedule=True

    def moveUpEntry(self,entry,tz=None):
        pass

    def moveDownEntry(self,entry,tz=None):
        pass

    def rescheduleTimes(self, type, diff, tz, day=None):
        pass

    def clear(self):
        while len(self._entries)>0:
            self._removeEntry(self._entries[0])
        self._p_changed = 1


    def findFirstFreeSlot(self,reqDur=None):
        """Tries to find the first free time slot available where an entry with
            the specified duration could be placed
        """
        d=self.getStartDate('UTC')
        for entry in self.getEntries():
            availDur=entry.getStartDate()-d
            if availDur!=0:
                if reqDur is not None and reqDur!=0:
                    if reqDur<=availDur:
                        return d
                else:
                    return d
            d=entry.getEndDate()
        availDur=self.getEndDate()-d
        if availDur!=0:
            if reqDur is not None and reqDur!=0:
                if reqDur<=availDur:
                    return d
            else:
                return d
        return None

    def moveEntriesBelow(self, diff, entriesList):
        """diff: the difference we have to increase/decrease each entry of the list.
           entriesList: list of entries for applying the diff"""

        if diff is not None:
            from MaKaC.conference import SessionSlot
            sessionsAlreadyModif=[]
            for entry in entriesList:
                if isinstance(entry.getOwner(), SessionSlot):
                    session=entry.getOwner().getSession()
                    if session not in sessionsAlreadyModif:
                        # if the slot is the first in the session schedule
                        # we also change the session start date
                        if session.getSchedule().getEntries()[0].getOwner()==entry.getOwner():
                            session.setStartDate(session.getStartDate()+diff, check=0, moveEntries=0)
                        sessionsAlreadyModif.append(session)
                entry.setStartDate(entry.getStartDate()+diff, check=0, moveEntries=1)


class SchEntry(Persistent, Fossilizable):
    """base schedule entry class. Do NOT instantiate
    """

    @Retrieves(['MaKaC.schedule.SchEntry',
                'MaKaC.schedule.ContribSchEntry',
                'MaKaC.schedule.LinkedTimeSchEntry'], 'id',
               Conversion.locatorString)
    def __init__(self):
        self._sch=None
        self.title = ""
        self.description = ""
        self._id=""

    def getId(self):
        try:
            if self._id:
                pass
        except AttributeError:
            self._id=str(self.getSchedule()._getNewEntryId())
        return self._id

    def notifyModification(self):
        if self.getSchedule():
            self.getSchedule().notifyModification()

    def setSchedule(self,sch,id):
        if self.getSchedule() is not None:
            self.getSchedule().removeEntry(self)
        self._sch=sch
        self._id=str(id)
        if self.getSchedule() is not None:
            sch.addEntry(self)

    def getSchedule(self):
        try:
            return self._sch
        except:
            self._sch = None
        return self._sch

    def isScheduled(self):
        return self.getSchedule() is not None

    def setValues( self, data ):
        """Sets all the values of the current schedule entry object from a
            dictionary containing the following key-value pairs:
                title-(str)
                description-(str)
           Please, note that this method sets ALL values which means that if
            the given dictionary doesn't contain any of the keys the value
            will set to a default value.
        """
        if data.has_key("title"):
            self.setTitle(data["title"])
        if data.has_key("description"):
            self.setDescription(data["description"])

    @Retrieves(['MaKaC.schedule.SchEntry',
                'MaKaC.schedule.BreakTimeSchEntry'], 'title')
    def getTitle( self ):
        return self.title

    def setTitle( self, newTitle ):
        self.title = newTitle.strip()

    @Retrieves(['MaKaC.schedule.SchEntry',
                'MaKaC.schedule.BreakTimeSchEntry'], 'description')
    def getDescription( self ):
        return self.description

    def setDescription( self, newDesc ):
        self.description = newDesc

    def getLocator( self ):
        if self.getSchedule() is None:
            return None
        loc=self.getSchedule().getOwner().getLocator()
        loc["schEntryId"]=self.getId()
        return loc

    def synchro( self ):
        if self.getSchedule() is not None:
            self.getSchedule().reSchedule()

    def delete(self):
        pass

    def recover(self):
        pass

class ConferenceSchedule(TimeSchedule, Fossilizable):
    """
    """

#    fossilizes(IConferenceScheduleDisplayFossil, IConferenceScheduleMgmtFossil)

    def __init__(self,conf):
        TimeSchedule.__init__(self,conf)

    def addEntry(self,entry,check=2):
        """check parameter:
            0: no check at all
            1: check and raise error in case of problem
            2: check and adapt the owner dates"""

        if (entry is None) or self.hasEntry(entry):
            return
        if isinstance(entry,LinkedTimeSchEntry):
            from MaKaC.conference import Session, Contribution
            if isinstance(entry.getOwner(),Session):
                raise MaKaCError( _("Sessions cannot be scheduled into the event, schedule their slots instead"), _("Event"))
            elif isinstance(entry.getOwner(),Contribution):
                if entry.getOwner().getSession() is not None:
                    raise MaKaCError( _("Cannot schedule into the event a contribution that belongs to a session"), _("Event"))
                if not self.getOwner().hasContribution(entry.getOwner()):
                    raise MaKaCError( _("Cannot schedule into the event a contribution that does not belong to it"), _("Event"))
        self._setEntryDuration(entry)
        return self._addEntry(entry,check)

    def moveUpEntry(self,entry,tz=None):
        #not very smart, should be improved: contribs with same start date,
        #   can cause overlapings

        if not tz:
            tz = self.getTimezone()
        entriesDay=self.getEntriesOnDay(entry.getAdjustedStartDate())
        if len(entriesDay)<2:
            return
        self._v_allowReSchedule=False
        entrypos = 0
        if entry in entriesDay:
            entrypos = entriesDay.index(entry)
        #if the entry is the first one...then it goes to the end.
        if entrypos == 0 and len(entriesDay)>1:
            entriesDay[1].setStartDate(entriesDay[0].getStartDate(), check=0, moveEntries=1)
            i = 2
            while(i < len(entriesDay)):
                entry = entriesDay[i]
                preventry = entriesDay[i-1]
                entry.setStartDate(preventry.getEndDate(), check=0, moveEntries=1)
                i += 1
            entriesDay[0].setStartDate(entriesDay[len(entriesDay)-1].getEndDate(), check=0, moveEntries=1)
        else:
            preventry = entriesDay[entrypos-1]
            entry.setStartDate(preventry.getStartDate(), check=0, moveEntries=1)
            preventry.setStartDate(entry.getEndDate(), check=0, moveEntries=1)
        self._v_allowReSchedule=True
        self.reSchedule()
        self._p_changed = 1

    def moveDownEntry(self,entry,tz=None):
        if not tz:
            tz = self.getTimezone()
        entriesDay=self.getEntriesOnDay(entry.getAdjustedStartDate())
        if len(entriesDay)<2:
            return
        self._v_allowReSchedule=False
        entrypos = 0
        if entry in entriesDay:
            entrypos = entriesDay.index(entry)
        #if the entry is the last one...then it goes to the first place.
        if entrypos+1 == len(entriesDay) and len(entriesDay)>1:
            entriesDay[len(entriesDay)-1].setStartDate(entriesDay[0].getStartDate(), check=0, moveEntries=1)
            i = -1
            while(i < len(entriesDay)-2):
                entry = entriesDay[i]
                nextentry = entriesDay[i+1]
                nextentry.setStartDate(entry.getEndDate(), check=0, moveEntries=1)
                i += 1
        else:
            nextentry = entriesDay[entrypos+1]
            nextentry.setStartDate(entry.getStartDate(), check=0, moveEntries=1)
            entry.setStartDate(nextentry.getEndDate(), check=0, moveEntries=1)
        self._v_allowReSchedule=True
        self.reSchedule()
        self._p_changed = 1

    def rescheduleTimes( self, type, diff, day, doFit):
        """
        recalculate and reschedule the entries of the conference slot with a time "diff" of separation.
        """
        from MaKaC.conference import SessionSlot
        entries = self.getEntriesOnDay(day)
        if type=="duration":
            i=0
            while i<len(entries):
                entry=entries[i]
                if doFit:
                    if isinstance( entry.getOwner(), SessionSlot ) :
                        entry.getOwner().fit()
                if i+1 == len(entries):
                    dur=entry.getDuration()
                else:
                    nextentry=entries[i+1]
                    dur=nextentry.getStartDate()-entry.getStartDate()-diff
                if dur<timedelta(0):
                    raise EntryTimingError( _("""With the time between entries you've chosen, the entry "%s" will have a duration less than zero minutes. Please, choose another time""")%entry.getTitle())
                entry.setDuration(dur=dur, check=2)
                i+=1
        elif type=="startingTime":
            st = timezone('UTC').localize(datetime(day.year, day.month, day.day, self.getStartDate().hour, self.getStartDate().minute))
            for entry in entries:
                if doFit:
                    if isinstance( entry.getOwner(), SessionSlot ) :
                        entry.getOwner().fit()
                entry.setStartDate(st, check=2, moveEntries=1)
                st=entry.getEndDate()+diff
        elif type=="noAction" and doFit:
            for entry in entries:
                if isinstance( entry.getOwner(), SessionSlot ) :
                    entry.getOwner().fit()

class SessionSchedule(TimeSchedule):
    """
    """

    def __init__(self,session):
        TimeSchedule.__init__(self,session)

    def checkSanity( self ):
        if self.hasEntriesBefore(self.getStartDate()) or self.hasEntriesAfter(self.getEndDate()):
            raise TimingError( _("Sorry, cannot perform this date change: Some entries in the schedule would be outside the new dates"))

    def addEntry(self,entry,check=1):
        if (entry is None) or self.hasEntry(entry):
            return
        if isinstance(entry,LinkedTimeSchEntry):
            from MaKaC.conference import SessionSlot
            if not(isinstance(entry.getOwner(),SessionSlot)):
                raise MaKaCError( _("objects of class %s cannot be scheduled into a session")%(entry.getOwner().__class__), _("Session Schedule"))
        else:
            raise MaKaCError( _("objects of class %s cannot be scheduled into a session")%(entry.__class__), _("Session Schedule"))
        self._addEntry(entry)

    def removeEntry(self,entry):
        if entry is None or not self.hasEntry(entry):
            return
        if entry.getOwner() in self.getOwner().getSlotList():
            raise MaKaCError( _("Cannot remove a slot without removing it from the session slot list"), _("Session Schedule"))
        self._removeEntry(entry)

    def moveEntriesBelow(self, diff, entriesList):
        """diff: the difference we have to increase/decrease each entry of the list.
           entriesList: list of entries for applying the diff"""
        if diff is not None:
            for entry in entriesList:
                entry.setStartDate(entry.getStartDate()+diff, check=0, moveEntries=1)

class SlotSchedule(TimeSchedule):
    """
    """

    def __init__(self,slot):
        TimeSchedule.__init__(self,slot)

    def _setEntryDuration(self,entry):
        entryDur=entry.getDuration()
        if entryDur is None or entryDur == timedelta(0):
            ownerDur=self.getOwner().getContribDuration()
            if ownerDur is not None and ownerDur!=timedelta(0):
                entry.setDuration(dur=ownerDur)
            else:
                sessionDur=self.getOwner().getSession().getContribDuration()
                entry.setDuration(dur=sessionDur)

    def addEntry(self,entry,check=2):
        """check parameter:
            0: no check at all
            1: check and raise error in case of problem
            2: check and adapt the owner dates
        """

        tz = self.getTimezone();

        owner = self.getOwner()
        if (entry is None) or self.hasEntry(entry):
            return
        if isinstance(entry,LinkedTimeSchEntry):
            from MaKaC.conference import Contribution
            if not(isinstance(entry.getOwner(),Contribution)):
                raise MaKaCError( _("objects of class %s cannot be scheduled into a session slot"), _("Slot"))
            if (entry.getOwner().getSession() is None) or (not self.getOwner().getSession().hasContribution(entry.getOwner())):
                raise MaKaCError( _("Cannot schedule into this session a contribution which does not belong to it"), _("Slot"))
        if entry.getStartDate()!=None and entry.getStartDate() < self.getOwner().getStartDate():
            if check == 1:
                raise ParentTimingError( _("The entry would start at %s, which is before the start time of the time slot (%s)")%\
                    (entry.getEndDate().strftime('%Y-%m-%d %H:%M'),\
                    self.getOwner().getStartDate().strftime('%Y-%m-%d %H:%M')),\
                      _("Slot"))
            elif check == 2:
                ContextManager.get('autoOps').append((owner,
                                                      "OWNER_START_DATE_EXTENDED",
                                                      owner,
                                                      entry.getAdjustedStartDate(tz=tz)))
                self.getOwner().setStartDate(entry.getStartDate(),check,0)
        if entry.getEndDate()!=None and entry.getEndDate() > self.getOwner().getEndDate():
            if check == 1:
                raise ParentTimingError( _("The entry would finish at %s, which is after the end of the time slot (%s)")%\
                    (entry.getAdjustedEndDate(tz=tz).strftime('%Y-%m-%d %H:%M'),\
                    self.getOwner().getAdjustedEndDate(tz=tz).strftime('%Y-%m-%d %H:%M')),\
                     "Slot")
            elif check == 2:
                ContextManager.get('autoOps').append((owner,
                                                      "OWNER_END_DATE_EXTENDED",
                                                      owner,
                                                      entry.getAdjustedEndDate(tz=tz)))
                self.getOwner().setEndDate(entry.getEndDate(),check)
        self._setEntryDuration(entry)
        self._addEntry(entry,check)


    def moveUpEntry(self,entry):
        #not very smart, should be improved: contribs with same start date,
        #   can cause overlapings
        entries = self.getEntriesOnDay(entry.getAdjustedStartDate())
        if len(entries)<2:
            return
        self._v_allowReSchedule=False
        entrypos = 0
        if entry in entries:
            entrypos = entries.index(entry)
        #if the entry is the first one...then it goes to the end.
        if entrypos == 0 and len(entries)>1:
            entries[1].setStartDate(entries[0].getStartDate(),check=0,moveEntries=1)
            i = 2
            while(i < len(entries)):
                entry = entries[i]
                preventry = entries[i-1]
                entry.setStartDate(preventry.getEndDate(),check=0,moveEntries=1)
                i += 1
            entries[0].setStartDate(entries[len(entries)-1].getEndDate(),check=0,moveEntries=1)
        else:
            preventry = entries[entrypos-1]
            entry.setStartDate(preventry.getStartDate(),check=0,moveEntries=1)
            preventry.setStartDate(entry.getEndDate(),check=0,moveEntries=1)
        self._v_allowReSchedule=True
        self.reSchedule()
        self._p_changed = 1

    def moveDownEntry(self,entry):
        entries = self.getEntriesOnDay(entry.getAdjustedStartDate())
        if len(entries)<2:
            return
        self._v_allowReSchedule=False
        entrypos = 0
        if entry in entries:
            entrypos = entries.index(entry)
        #if the entry is the last one...then it goes to the first place.
        if entrypos+1 == len(entries) and len(entries)>1:
            entries[len(entries)-1].setStartDate(entries[0].getStartDate(), check=0,moveEntries=1)
            i = -1
            while(i < len(entries)-2):
                entry = entries[i]
                nextentry = entries[i+1]
                nextentry.setStartDate(entry.getEndDate(),check=0,moveEntries=1)
                i += 1
        else:
            nextentry = entries[entrypos+1]
            nextentry.setStartDate(entry.getStartDate(),check=0,moveEntries=1)
            entry.setStartDate(nextentry.getEndDate(),check=0,moveEntries=1)
        self._v_allowReSchedule=True
        self.reSchedule()
        self._p_changed = 1

    def moveEntriesBelow(self, diff, entriesList):
        """diff: the difference we have to increase/decrease each entry of the list.
           entriesList: list of entries for applying the diff"""
        if diff is not None:
            for entry in entriesList:
                entry.setStartDate(entry.getStartDate()+diff, check=0, moveEntries=1)

class PosterSlotSchedule(SlotSchedule):

    def _setEntryDuration(self,entry):
        #In the posters schedulers the duration will (by default) always be the
        #   same for every entry within the slot
        if entry.getOwner().getDuration() != None and entry.getOwner().getDuration() != 0 \
                and entry.getOwner().getDuration().seconds!=0:
                    return
        ownerDur=self.getOwner().getContribDuration()
        if ownerDur is not None and \
                                (ownerDur > timedelta(0)):
            entry.setDuration(dur=ownerDur)
        else:
            sessionDur=self.getOwner().getSession().getContribDuration()
            entry.setDuration(dur=sessionDur)

    def addEntry(self,entry,check=0):
        # check=0 is here only because we must  have 3 parameters.
        if (entry is None) or self.hasEntry(entry):
            return
        from MaKaC.conference import Contribution
        if not isinstance(entry,LinkedTimeSchEntry) or \
                            not isinstance(entry.getOwner(),Contribution):
                raise MaKaCError( _("objects of class %s cannot be scheduled into a poster session slot")%entry, _("Slot"))
        if (entry.getOwner().getSession() is None) or \
        (not self.getOwner().getSession().hasContribution(entry.getOwner())):
                raise MaKaCError( _("Cannot schedule into this session a contribution which does not belong to it"), _("Slot"))
        self._setEntryDuration(entry)
        if entry.isScheduled():
            #remove it from the old schedule and add it to this one
            entry.getSchedule().removeEntry(entry)
        entry.setStartDate(self.getStartDate())
        self._entries.append(entry)
        entry.setSchedule(self,self._getNewEntryId())
        self._p_changed = 1

    def reSchedule(self):
        try:
            if self._v_allowReSchedule:
                pass
        except AttributeError:
            self._v_allowReSchedule=True
        if self._v_allowReSchedule:
            self._v_allowReSchedule=False
            for e in self._entries:
                e.setStartDate(self.getStartDate())
            self._v_allowReSchedule=True

class SlotSchTypeFactory:
    _sch={"standard":SlotSchedule,"poster":PosterSlotSchedule}
    _default="standard"

    def getScheduleKlass(cls,id):
        id=id.strip().lower()
        if not cls._sch.has_key(id):
            id=cls._default
        return cls._sch[id]
    getScheduleKlass=classmethod(getScheduleKlass)

    def getDefaultKlass(cls):
        return cls._sch[cls._default]
    getDefaultKlass=classmethod(getDefaultKlass)

    def getDefaultId(cls):
        return cls._default
    getDefaultId=classmethod(getDefaultId)

    def getIdList(cls):
        return cls._sch.keys()
    getIdList=classmethod(getIdList)

    def getId(cls,sch):
        for (id,schKlass) in cls._sch.items():
            if sch.__class__==schKlass:
                return id
        return ""
    getId=classmethod(getId)

class TimeSchEntry(SchEntry):

    def __init__(self):
        SchEntry.__init__(self)
        self.startDate=None
        self.duration=None

    def getStartDate( self ):
        pass

    def setStartDate(self,sDate,check=1, moveEntries=0):
        pass

    def getEndDate( self ):
        pass

    def getDuration(self):
        pass

    def setDuration(self,hours=0,min=15, dur=0):
        pass

    def inDay( self, day ):
        pass

    def onDate( self, day ):
        pass


class LinkedTimeSchEntry(TimeSchEntry):

    fossilizes(ILinkedTimeSchEntryDisplayFossil,
               ILinkedTimeSchEntryMgmtFossil)
    @Retrieves (['MaKaC.schedule.LinkedTimeSchEntry'], 'title', lambda x: x.getOwner().getSession().getTitle())
    @Retrieves (['MaKaC.schedule.LinkedTimeSchEntry'], 'slotTitle', lambda x: x.getOwner().getTitle())
    @Retrieves (['MaKaC.schedule.LinkedTimeSchEntry'], 'id', Conversion.locatorString)
    @Retrieves (['MaKaC.schedule.LinkedTimeSchEntry'], 'sessionId', lambda x: x.getOwner().getSession().getId())
    @Retrieves (['MaKaC.schedule.LinkedTimeSchEntry'], 'sessionSlotId', lambda x: x.getOwner().getId())
    @Retrieves (['MaKaC.schedule.LinkedTimeSchEntry'], 'entryType', lambda x: 'Session')
    @Retrieves (['MaKaC.schedule.LinkedTimeSchEntry'], 'material', lambda x: DictPickler.pickle(x.getOwner().getSession().getAllMaterialList()))
    @Retrieves (['MaKaC.schedule.LinkedTimeSchEntry'], 'color', lambda x: x.getOwner().getColor())
    @Retrieves (['MaKaC.schedule.LinkedTimeSchEntry'], 'textColor', lambda x: x.getOwner().getTextColor())
    @Retrieves (['MaKaC.schedule.LinkedTimeSchEntry'], 'isPoster', lambda x: x.getOwner().getSession().getScheduleType() == 'poster')
    @Retrieves (['MaKaC.schedule.LinkedTimeSchEntry'], 'room', lambda x: Conversion.roomName(x.getOwner().getRoom()))
    @Retrieves (['MaKaC.schedule.LinkedTimeSchEntry'], 'location', lambda x: Conversion.locationName(x.getOwner().getLocation()))
    @Retrieves (['MaKaC.schedule.LinkedTimeSchEntry'], 'address', lambda x: Conversion.locationAddress(x.getOwner().getLocation()))
    @Retrieves (['MaKaC.schedule.LinkedTimeSchEntry'], 'inheritLoc', lambda x: x.getOwner().getOwnLocation() is None)
    @Retrieves (['MaKaC.schedule.LinkedTimeSchEntry'], 'inheritRoom', lambda x: x.getOwner().getOwnRoom() is None)
    @Retrieves (['MaKaC.schedule.LinkedTimeSchEntry'], 'description', lambda x: x.getOwner().getSession().getDescription())
    @Retrieves (['MaKaC.schedule.LinkedTimeSchEntry'], 'conveners', lambda x: x.getOwner().getOwnConvenerList(), isPicklableObject=True)
    @Retrieves(['MaKaC.schedule.ContribSchEntry','MaKaC.schedule.LinkedTimeSchEntry'], 'conferenceId',
               lambda x: x.getOwner().getConference().getId())
    @Retrieves (['MaKaC.schedule.ContribSchEntry','MaKaC.schedule.LinkedTimeSchEntry'], 'scheduleEntryId',
                lambda x: x.getId())
    @Retrieves (['MaKaC.schedule.ContribSchEntry','MaKaC.schedule.LinkedTimeSchEntry'], 'scheduleEntryType',
                lambda x: type(x).__name__)

    def __init__(self,owner):
        SchEntry.__init__(self)
        self.__owner = owner

    # fermi - pass tz here.....
    def getStartDate( self ):
        return self.__owner.getStartDate()

    @Retrieves(['MaKaC.schedule.LinkedTimeSchEntry',
                'MaKaC.schedule.ContribSchEntry'], 'startDate', Conversion.datetime)
    def getAdjustedStartDate( self, tz=None ):
        return self.__owner.getAdjustedStartDate(tz)

    def setStartDate(self,newDate,check=2, moveEntries=0):
        """check parameter:
            0: no check at all
            1: check and raise error in case of problem
            2: check and adapt the owner dates"""
        return self.getOwner().setStartDate(newDate,check, moveEntries)

    def getEndDate( self ):
        return self.__owner.getEndDate()

    @Retrieves(['MaKaC.schedule.LinkedTimeSchEntry',
                'MaKaC.schedule.ContribSchEntry'], 'endDate', Conversion.datetime)
    def getAdjustedEndDate( self, tz=None ):
        return self.__owner.getAdjustedEndDate(tz)

    @Retrieves('MaKaC.schedule.LinkedTimeSchEntry', 'duration', Conversion.timedelta)
    def getDuration(self):
        return self.__owner.getDuration()

    def setDuration(self,hours=0,minutes=15,dur=0,check=2):
        if dur!=0:
            return self.getOwner().setDuration(dur=dur,check=check)
        else:
            return self.getOwner().setDuration(hours,minutes,check=check)

    @Retrieves(['MaKaC.schedule.ContribSchEntry'], 'title')
    def getTitle( self ):
        return self.__owner.getTitle()

    def getDescription( self ):
        return self.__owner.getDescription()

    def getOwner( self ):
        return self.__owner

    def inDay( self, day ):
        """Tells whether or not the current entry occurs whithin the specified
            day (day is tz-aware)
        """
        if not self.isScheduled():
            return False
        return self.getStartDate().astimezone(day.tzinfo).date()<=day.date() and self.getEndDate().astimezone(day.tzinfo).date()>=day.date()

    def onDate( self, date ):
        """Tells whether or not the current entry occurs during the specified
            date.
        """
        if not self.isScheduled():
            return False
        return self.getStartDate()<=date and \
                self.getEndDate()>=date

    def collides(self,entry):
        return (entry.getStartDate()>=self.getStartDate() and \
                entry.getStartDate()<self.getEndDate()) or \
                (entry.getEndDate()>self.getStartDate() and \
                entry.getEndDate()<=self.getEndDate())


class IndTimeSchEntry(TimeSchEntry):

    def setValues( self, data ):
        """Sets all the values of the current schedule entry object from a
            dictionary containing the following key-value pairs:
                title-(str)
                description-(str)
                year, month, day, sHour, sMinute - (str) => components of the
                        starting date of the entry, if not specified it will
                        be set to now.
                durationHours, durationMinutes - (str)
           Please, note that this method sets ALL values which means that if
            the given dictionary doesn't contain any of the keys the value
            will set to a default value.
        """
        SchEntry.setValues(self,data)
        if data.get("sYear", None) != None and \
                data.get("sMonth", None) != None and \
                data.get("sDay", None) != None and \
                data.get("sHour", None) != None and \
                data.get("sMinute", None) != None:
            self.setStartDate(datetime(int(data["sYear"]),\
                                        int(data["sMonth"]),\
                                        int(data["sDay"]), \
                                        int(data["sHour"]),\
                                        int(data["sMinute"])) )
        if data.get("durHours",None)!=None and data.get("durMins",None)!=None:
            self.setDuration(data["durHours"],data["durMins"])

    def getTimezone( self ):
        return self.getSchedule().getOwner().getTimezone()

    def getStartDate( self ):
        return self.startDate

    @Retrieves(['MaKaC.schedule.BreakTimeSchEntry'], 'startDate', Conversion.datetime)
    def getAdjustedStartDate( self, tz=None ):
        if not tz:
            tz = self.getTimezone()

        return self.getStartDate().astimezone(timezone(tz))

    def setStartDate(self,sDate,check=1, moveEntries=0):
        self.startDate=sDate
        self._p_changed=1
        if self.isScheduled():
            self.getSchedule().reSchedule()

    def getEndDate( self ):
        if self.getStartDate() is None:
            return None
        return self.startDate+self.duration

    @Retrieves(['MaKaC.schedule.BreakTimeSchEntry'], 'endDate', Conversion.datetime)
    def getAdjustedEndDate( self, tz=None ):
        if not tz:
            tz = self.getTimezone()
        return self.getEndDate().astimezone(timezone(tz))

    @Retrieves(['MaKaC.schedule.BreakTimeSchEntry'], 'duration', Conversion.timedelta)
    def getDuration(self):
        return self.duration

    def setDuration(self,hours=0,min=15,dur=0):
        if dur==0:
            self.duration=timedelta(hours=int(hours),minutes=int(min))
        else:
            self.duration=dur
        self._p_changed = 1
        if self.isScheduled():
            self.getSchedule().reSchedule()

    def inDay( self, day ):
        """Tells whether or not the current entry occurs whithin the specified
            day (day is tz-aware)
        """
        if not self.isScheduled():
            return False
        return self.getStartDate().astimezone(day.tzinfo).date()<=day.date() and self.getEndDate().astimezone(day.tzinfo).date()>=day.date()

    def onDate( self, date ):
        """Tells whether or not the current entry occurs during the specified
            date.
        """
        if not self.isScheduled():
            return False
        return self.getStartDate()<=date and \
                self.getEndDate()>=date


class BreakTimeSchEntry(IndTimeSchEntry):

    fossilizes(IBreakTimeSchEntryFossil, IBreakTimeSchEntryMgmtFossil)
    @Retrieves(['MaKaC.schedule.BreakTimeSchEntry'], 'entryType', lambda x: 'Break')
    @Retrieves(['MaKaC.schedule.BreakTimeSchEntry'], 'conferenceId', lambda x: x.getOwner().getConference().getId())
    @Retrieves (['MaKaC.schedule.BreakTimeSchEntry'], 'sessionId', Conversion.parentSession)
    @Retrieves (['MaKaC.schedule.BreakTimeSchEntry'], 'sessionSlotId', Conversion.parentSlot)
    @Retrieves (['MaKaC.schedule.BreakTimeSchEntry'], 'scheduleEntryId', lambda x: x.getId())
    @Retrieves (['MaKaC.schedule.BreakTimeSchEntry'], 'room', lambda x: Conversion.roomName(x.getRoom()))
    @Retrieves (['MaKaC.schedule.BreakTimeSchEntry'], 'location', lambda x: Conversion.locationName(x.getLocation()))
    @Retrieves (['MaKaC.schedule.BreakTimeSchEntry'], 'address', lambda x: Conversion.locationAddress(x.getLocation()))
    @Retrieves (['MaKaC.schedule.BreakTimeSchEntry'], 'inheritLoc', lambda x: x.getOwnLocation() is None)
    @Retrieves (['MaKaC.schedule.BreakTimeSchEntry'], 'inheritRoom', lambda x: x.getOwnRoom() is None)
    @Retrieves (['MaKaC.schedule.BreakTimeSchEntry'], 'id', lambda x:Conversion.locatorString(x)+"b"+x.getId())

    def __init__(self):
        IndTimeSchEntry.__init__(self)
        self._color="#90C0F0"
        self._textColor="#202020"
        self._textColorToLink=False

    def clone(self, owner):
        btse = BreakTimeSchEntry()
        btse.setValues(self.getValues())
        olddate =  self.getOwner().getStartDate()
        newdate = owner.getSchedule().getStartDate()
        timeDifference = newdate - olddate
        btse.setStartDate(btse.getStartDate()+timeDifference)
        return btse

    def getValues(self):
        values = {}
        values["startDate"] = self.getStartDate()
        values["endDate"] = self.getEndDate()
        values["durTimedelta"] = self.getDuration()
        values["description"] = self.getDescription()
        values["title"] = self.getTitle()
        if self.getOwnLocation() is not None :
            values["locationName"] = self.getLocation().getName()
        else :
            values["locationName"] = ""
        if self.getOwnRoom() is not None :
            values["roomName"] = self.getOwnRoom().getName()
        else :
            values["roomName"] = ""
        values["backgroundColor"] = self.getColor()
        values["textColor"] = self.getTextColor()
        if self.isTextColorToLinks():
            values["textcolortolinks"]="True"

        return values

    def setValues( self, data, check=2, moveEntriesBelow=0, tz='UTC'):
        from MaKaC.conference import CustomLocation, CustomRoom
        # In order to move the entries below, it is needed to know the diff (we have to move them)
        # and the list of entries to move. It's is needed to take those datas in advance because they
        # are going to be modified before the moving.
        if moveEntriesBelow == 1 and self.getSchedule():
            oldStartDate=copy.copy(self.getStartDate())
            oldDuration=copy.copy(self.getDuration())
            i=self.getSchedule().getEntries().index(self)+1
            entriesList = self.getSchedule().getEntries()[i:]
        if data.get("startDate", None) != None:
            self.setStartDate(data["startDate"], 0)
        elif data.get("sYear", None) != None and \
                data.get("sMonth", None) != None and \
                data.get("sDay", None) != None and \
                data.get("sHour", None) != None and \
                data.get("sMinute", None) != None:
            #########################################
            # Fermi timezone awareness              #
            #  We have to store as UTC, relative    #
            #  to the timezone of the conference.   #
            #########################################
            d = timezone(tz).localize(datetime(int(data["sYear"]),
                    int(data["sMonth"]),
                    int(data["sDay"]),
                    int(data["sHour"]),
                    int(data["sMinute"])))
            sDate = d.astimezone(timezone('UTC'))
            self.setStartDate(sDate)
            ########################################
            # Fermi timezone awareness             #
            #  We have to store as UTC, relative   #
            #  to the timezone of the conference.  #
            ########################################

        if data.get("durTimedelta", None) != None:
            self.setDuration(check=0, dur=data["durTimedelta"])
        elif data.get("durHours","").strip()!="" and data.get("durMins","").strip()!="":
                self.setDuration(data["durHours"], data["durMins"], 0)
        else:
            h=data.get("durHours","").strip()
            m=data.get("durMins","").strip()
            force=False
            if h!="" or m!="":
                h=h or "0"
                m=m or "0"
                if h!="0" or m!="0":
                    self.setDuration(int(h), int(m), 0)
                else:
                    force=True
            else:
                force=True
            if force:
                if self.getDuration() is None or self.getDuration()==0:
                    self.setDuration("0", "15", 0)
        if data.get( "locationName", "" ).strip() == "":
            self.setLocation( None )
        else:
            loc = self.getOwnLocation()
            if not loc:
                loc = CustomLocation()
            self.setLocation( loc )
            loc.setName( data["locationName"] )
            loc.setAddress( data.get("locationAddress", "") )
        if data.get( "roomName", "" ).strip() == "":
            self.setRoom( None )
        else:
            room = self.getOwnRoom()
            if not room:
                room = CustomRoom()
            self.setRoom( room )
            room.setName( data["roomName"] )
        self._color=data.get("backgroundColor","#90C0F0")
        if data.has_key("autotextcolor"):
            self._textColor=utils.getTextColorFromBackgroundColor(self.getColor())
        else:
            self._textColor=data.get("textColor","#202020")
        self.setTextColorToLinks(data.has_key("textcolortolinks"))
        if data.has_key("title"):
            self.setTitle(data["title"])
        if data.has_key("description"):
            self.setDescription(data["description"])

        # now check if the slot new time is compatible with its parents limits
        if check == 1:
            if self.getSchedule() and self.getSchedule().isOutside(self):
                raise TimingError( _("This action would move the break out of its parents schedule dates"))
        elif check == 2:
            if self.getSchedule() and self.getSchedule().isOutside(self):
                self.synchro()
        if moveEntriesBelow == 1 and self.getSchedule():
            diff = (self.getStartDate() - oldStartDate) + (self.getDuration() - oldDuration)
            self.getSchedule().moveEntriesBelow(diff, entriesList)
        self.notifyModification()


    def getLocationParent( self ):
        if self.getSchedule() is not None:
            return self.getSchedule().getOwner()
        return None

    def setLocation(self, loc):
        self.place = loc

    def getLocation(self):
        if self.getOwnLocation() is None:
            return self.getInheritedLocation()
        return self.getOwnLocation()

    def getInheritedLocation(self):
        locParent = self.getLocationParent()
        if locParent:
            return locParent.getLocation();
        else:
            return None

    def getOwnLocation(self):
        try:
            if self.place:
                pass
        except AttributeError:
            self.place=None
        return self.place

    def setRoom(self, room):
        self.room = room

    def getRoom(self):
        if self.getOwnRoom() is None:
            return self.getInheritedRoom()
        return self.getOwnRoom()

    def getInheritedRoom(self):
        locParent = self.getLocationParent()
        if locParent:
            return locParent.getRoom();
        else:
            return None

    def getOwnRoom(self):
        try:
            if self.room:
                pass
        except AttributeError:
            self.room=None
        return self.room

    def getOwner(self):
        if self.getSchedule() is not None:
            return self.getSchedule().getOwner()
        return None

    def _verifyDuration(self,check=2):

        if self.getSchedule() is not None:
            owner = self.getSchedule().getOwner()
            if self.getEndDate() > owner.getEndDate():
                if check==1:
                    raise ParentTimingError( _("The break cannot end after (%s) its parent (%s)")%\
                        (self.getEndDate().strftime('%Y-%m-%d %H:%M'),\
                        owner.getEndDate().strftime('%Y-%m-%d %H:%M')),\
                         _("Break"))
                elif check==2:
                    # update the schedule
                    owner.setEndDate(self.getEndDate(),check)

    def setDuration(self, hours=0, min=15, check=2,dur=0):

        if dur==0:
            IndTimeSchEntry.setDuration(self,hours,min)
        else:
            IndTimeSchEntry.setDuration(self,dur=dur)
        self._verifyDuration(check)
        self.notifyModification()

    def setStartDate(self, newDate,check=2, moveEntries=0):

#        try:
#            tz = str(newDate.tzinfo)
#        except:
#            tz = 'undef'
        if self.getSchedule() is not None:
            owner = self.getSchedule().getOwner()
            if newDate < owner.getStartDate():
                if check==1:
                    raise ParentTimingError( _("The break \"%s\" cannot start before (%s) its parent (%s)")%\
                        (self.getTitle(), \
                        newDate.strftime('%Y-%m-%d %H:%M'),\
                        owner.getStartDate().strftime('%Y-%m-%d %H:%M')),\
                        "Break")
                elif check==2:
                    # update the schedule
                    owner.setStartDate(newDate, check)
            if newDate > owner.getEndDate():
                if check==1:
                    raise ParentTimingError("The break cannot start after (%s) its parent ends (%s)"%\
                        (newDate.strftime('%Y-%m-%d %H:%M'),\
                        owner.getEndDate().strftime('%Y-%m-%d %H:%M')),\
                         _("Break"))
                elif check==2:
                    # update the schedule
                    owner.setEndDate(newDate,check)
        IndTimeSchEntry.setStartDate(self, newDate,check)
        self.notifyModification()

    def setColor(self,newColor):
        self._color=newColor
    setBgColor=setColor

    @Retrieves(['MaKaC.schedule.BreakTimeSchEntry'], 'color')
    def getColor(self):
        try:
            if self._color:
                pass
        except AttributeError:
            self._color="#AADDEE"
        return self._color
    getBgColor=getColor

    def setTextColor(self,newColor):
        self._textColor=newColor

    @Retrieves(['MaKaC.schedule.BreakTimeSchEntry'], 'textColor')
    def getTextColor(self):
        try:
            if self._textColor:
                pass
        except AttributeError:
            self._textColor="#202020"
        return self._textColor

    def setTextColorToLinks(self,v):
        self._textColorToLink=v

    def isTextColorToLinks(self):
        try:
            if self._textColorToLink:
                pass
        except AttributeError:
            self._textColorToLink=False
        return self._textColorToLink

    def delete(self):
        TrashCanManager().add(self)

    def recover(self):
        TrashCanManager().remove(self)

class ContribSchEntry(LinkedTimeSchEntry):

    fossilizes(IContribSchEntryDisplayFossil,
               IContribSchEntryMgmtFossil )

    @Retrieves (['MaKaC.schedule.ContribSchEntry'], 'entryType', lambda x: 'Contribution')
    @Retrieves (['MaKaC.schedule.ContribSchEntry'], 'sessionId', Conversion.parentSession)
    @Retrieves (['MaKaC.schedule.ContribSchEntry'], 'sessionSlotId', Conversion.parentSlot)
    @Retrieves (['MaKaC.schedule.ContribSchEntry'], 'contributionId', lambda x: x.getOwner().getId())
    @Retrieves (['MaKaC.schedule.ContribSchEntry'], 'material', lambda x: DictPickler.pickle(x.getOwner().getAllMaterialList()))
    @Retrieves (['MaKaC.schedule.ContribSchEntry'], 'description', lambda x: x.getOwner().getDescription())
    @Retrieves (['MaKaC.schedule.ContribSchEntry'], 'presenters', lambda x: x.getOwner().getSpeakerList(), isPicklableObject=True)

    def __init__(self, owner):
        LinkedTimeSchEntry.__init__(self, owner)

    def setSchedule(self,sch,id):
        status=self.getOwner().getCurrentStatus()
        from MaKaC.conference import ContribStatusWithdrawn,ContribStatusNotSch,ContribStatusSch
        if isinstance(status,ContribStatusWithdrawn) and sch is not None:
            raise MaKaCError( _("Cannot schedule a contribution which has been withdrawn"), _("Contribution"))
        LinkedTimeSchEntry.setSchedule(self,sch,id)
        if sch is None:
            newStatus=ContribStatusNotSch(self.getOwner())
        else:
            newStatus=ContribStatusSch(self.getOwner())
        self.getOwner().setStatus(newStatus)

    @Retrieves (['MaKaC.schedule.ContribSchEntry'],'room', Conversion.roomName)
    def getRoom(self):
        return self.getOwner().getRoom()

    @Retrieves (['MaKaC.schedule.ContribSchEntry'],'location', Conversion.locationName)
    def getLocation(self):
        return self.getOwner().getLocation()

    def getOwnRoom(self):
        return self.getOwner().getOwnRoom()

class ScheduleToJson:

    @staticmethod
    def processEntry(obj, tz, aw, mgmtMode = False, useAttrCache = False):

        if mgmtMode:
            if isinstance(obj, BreakTimeSchEntry):
                entry = obj.fossilize(IBreakTimeSchEntryMgmtFossil, useAttrCache = useAttrCache)
            elif isinstance(obj, ContribSchEntry):
                entry = obj.fossilize(IContribSchEntryMgmtFossil, useAttrCache = useAttrCache)
            elif isinstance(obj, LinkedTimeSchEntry):
                entry = obj.fossilize(ILinkedTimeSchEntryMgmtFossil, useAttrCache = useAttrCache)
            else:
                entry = obj.fossilize(useAttrCache = useAttrCache)
        else:
            # the fossils used for the display of entries
            # will be taken by default, since they're first
            # in the list of their respective Fossilizable
            # objects
            entry = obj.fossilize(useAttrCache = useAttrCache)

        genId = entry['id']

        # sessions that are no poster sessions will be expanded
        if entry['entryType'] == 'Session':

            sessionSlot = obj.getOwner()

            # get session content
            entries = {}
            for contrib in sessionSlot.getSchedule().getEntries():
                if ScheduleToJson.checkProtection(contrib, aw):
                    if mgmtMode:
                        if isinstance(contrib, ContribSchEntry):
                            contribData = contrib.fossilize(IContribSchEntryMgmtFossil, useAttrCache = useAttrCache)
                        elif isinstance(contrib, BreakTimeSchEntry):
                            contribData = contrib.fossilize(IBreakTimeSchEntryMgmtFossil, useAttrCache = useAttrCache)
                        else:
                            contribData = contrib.fossilize(useAttrCache = useAttrCache)
                    else:
                        # the fossils used for the display of entries
                        # will be taken by default, since they're first
                        # in the list of their respective Fossilizable
                        # objects
                        contribData = contrib.fossilize(useAttrCache = useAttrCache)

                    entries[contribData['id']] = contribData

            entry['entries'] = entries

        return genId, entry

    @staticmethod
    def checkProtection(obj, aw):

        if aw is None:
            return True

        from MaKaC.conference import SessionSlot

        canBeDisplayed = False
        if isinstance(obj, BreakTimeSchEntry):
            canBeDisplayed = True
        else: #contrib or session slot
            owner = obj.getOwner()
            if owner.canAccess(aw):
                canBeDisplayed = True
            elif isinstance(owner, SessionSlot) and owner.canView(aw):
                canBeDisplayed = True
        return canBeDisplayed

    @staticmethod
    def process(schedule, tz, aw, days = None, mgmtMode = False, useAttrCache = False):

        scheduleDict={}

        if not days:
            days = daysBetween(schedule.getAdjustedStartDate(tz), schedule.getAdjustedEndDate(tz))

        dates = [d.strftime("%Y%m%d") for d in days]

        # Generating the days dictionnary
        for d in dates:
            scheduleDict[d] = {}

        # Filling the day dictionnary with entries
        for obj in schedule.getEntries():

            if ScheduleToJson.checkProtection(obj, aw):
                genId, resultData = ScheduleToJson.processEntry(obj, tz, aw, mgmtMode, useAttrCache)
                day = obj.getAdjustedStartDate(tz).strftime("%Y%m%d")
                # verify that start date is in dates
                if day in dates:
                    scheduleDict[day][genId] = resultData

        return scheduleDict

    @staticmethod
    def sort_dict(dict):
        new_dict = {}
        sorted_keys = dict.keys()
        sorted_keys.sort()

        for key in sorted_keys:
            new_dict[key] = dict[key]

        return new_dict
