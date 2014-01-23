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

"""
Schedule-related services
"""
from flask import session

from MaKaC.services.implementation.base import ParameterManager

import MaKaC.conference as conference
import MaKaC.schedule as schedule

from MaKaC.common import log
from MaKaC.common.PickleJar import DictPickler
from MaKaC.common.fossilize import fossilize
from MaKaC.fossils.schedule import IConferenceScheduleDisplayFossil

from MaKaC.services.interface.rpc.common import ServiceError, TimingNoReportError,\
    NoReportError, ServiceAccessError

from MaKaC.services.implementation import conference as conferenceServices
from MaKaC.services.implementation import base
from MaKaC.services.implementation import roomBooking
from MaKaC.services.implementation import session as sessionServices
from MaKaC.common.timezoneUtils import setAdjustedDate
from MaKaC.common.utils import getHierarchicalId, formatTime, formatDateTime, parseDate
from MaKaC.common.contextManager import ContextManager
import MaKaC.common.info as info
from MaKaC.errors import TimingError
from MaKaC.fossils.schedule import ILinkedTimeSchEntryMgmtFossil, IBreakTimeSchEntryMgmtFossil, \
        IContribSchEntryMgmtFossil
from MaKaC.fossils.contribution import IContributionParticipationTTMgmtFossil, IContributionFossil
from MaKaC.fossils.conference import IConferenceParticipationFossil,\
    ISessionFossil
from MaKaC.common import timezoneUtils
from MaKaC.common.Conversion import Conversion
from MaKaC.schedule import BreakTimeSchEntry
from MaKaC.conference import SessionSlot, Material, Link
from MaKaC.webinterface.pages.sessions import WSessionICalExport
from MaKaC.webinterface.pages.contributions import WContributionICalExport
from indico.web.http_api.util import generate_public_auth_request

import time, datetime, pytz, copy

def translateAutoOps(autoOps):

    result = []

    for source,op,target, newValue in autoOps:

        if type(newValue) == datetime.datetime:
            finalTime = formatTime(newValue)
        else:
            finalTime = newValue

        result.append((getHierarchicalId(source),
                       op,
                       getHierarchicalId(target),
                       finalTime))
    return result


class ConferenceGetSchedule(conferenceServices.ConferenceDisplayBase):
    def _checkParams(self):
        conferenceServices.ConferenceDisplayBase._checkParams(self)

    def _getAnswer(self):
        #TODO: tz = timezoneUtils.DisplayTZ(self._getAW()).getDisplayTZ() // use it in the fossilize?
        return self._target.getSchedule().fossilize(IConferenceScheduleDisplayFossil)

class LocationSetter:
    def _setLocationInfo(self, target):
        room = self._roomInfo.get('room', None)
        address = self._roomInfo.get('address', None)
        location = self._roomInfo.get('location', None)
        if location != None:
            loc = target.getOwnLocation()
            if not loc:
                loc = conference.CustomLocation()
            target.setLocation(loc)
            loc.setName(location)
            loc.setAddress(address)

        #same as for the location
        if room != None:
            r = target.getOwnRoom()
            if not r:
                r = conference.CustomRoom()
            target.setRoom(r)
            r.setName(room)
            minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
            if minfo.getRoomBookingModuleActive():
                r.retrieveFullName(location)
            else:
                # invalidate full name, as we have no way to know it
                r.fullName = None

class ScheduleOperation:

    def _getAnswer(self):

        self.initializeAutoOps()

        try:
            return self._performOperation()
        except TimingError, e:
            raise TimingNoReportError(e.getMessage())

    def initializeAutoOps(self):
        ContextManager.set('autoOps',[])

    def getAutoOps(self):
        return ContextManager.get('autoOps')


class ScheduleEditContributionBase(ScheduleOperation, LocationSetter):

    def __addPeople(self, contribution, pManager, elemType, addMethod, deleteMethod, getListMethod, allParticipantEmails):
        """ Generic method for adding presenters, authors and co-authors. """

        def __findPerson(personDict, peopleList):
            for person in peopleList:
                # TODO: Remove this hack when refactoring Users.js
                personDict["id"] = personDict["id"].replace('edited','')
                ##
                if person.getId() == personDict["id"]:
                    return person
            return None

        pList = pManager.extract("%ss" % elemType, pType=list,
                                 allowEmpty=True)

        peopleIds = []
        currentParticipants = getListMethod(contribution)
        currentParticipantEmails = [p.getEmail() for p in currentParticipants]

        for elemValues in pList:
            # Already existing participants have a type 'ContributionParticipation', while
            # added users can be 'Avatar'(search) or no-type (new).
            if elemValues.get("_type", "Avatar") == "ContributionParticipation": # udpate
                element = __findPerson(elemValues, currentParticipants)
                peopleIds.append(elemValues["id"])
                if element is None: continue # Most probably the part was removed in the meanwhile
                DictPickler.update(element, elemValues)
            else: # new

                # Do not add the same participant twice
                if elemValues.get("email") in currentParticipantEmails: # if it is already a participant
                    continue
                elif elemValues.get("email","").strip() != "": # keep track in case, the user is trying to add 2 times the same participant
                    currentParticipantEmails.append(elemValues["email"])

                element = conference.ContributionParticipation()
                DictPickler.update(element, elemValues)
                # call the appropriate method
                addMethod(contribution, element)
                peopleIds.append(element.getId())

            # rights that are set individually per participant
            if self._updateRights:
                if elemValues.get("isSubmitter"):
                    contribution.grantSubmission(element)
                else:
                    contribution.revokeSubmission(element)

        for person in getListMethod(contribution)[:]: #delete
            if str(person.getId()) not in peopleIds:
                deleteMethod(contribution, person)
                if person.getEmail() not in allParticipantEmails:
                    contribution.revokeSubmission(person)
            elif self._privileges[elemType] is not None:
                # rights that are set to a group of participants
                if self._privileges[elemType].get('%s-grant-submission' % elemType, False):
                    contribution.grantSubmission(person)
        allParticipantEmails += currentParticipantEmails

    def _addReportNumbers(self):
        reportNumbersSet = []
        if self._reportNumbers:
            for reportNumber in self._reportNumbers:
                system = reportNumber["system"]
                number_list = reportNumber["number"] #sometimes it is a list (e.g. from Importer)
                if type(number_list) != list:
                    number_list = [number_list]
                for number in number_list:
                    if not self._contribution.getReportNumberHolder().hasReportNumberOnSystem(system, number):
                        self._contribution.getReportNumberHolder().addReportNumber(system, number)
                    reportNumbersSet.append("""s%sr%s"""%(system, number))

        for system in self._contribution.getReportNumberHolder().getReportNumberKeys():
            for number in self._contribution.getReportNumberHolder().getReportNumbersBySystem(system):
                if """s%sr%s"""%(system, number) not in reportNumbersSet:
                    self._contribution.getReportNumberHolder().removeReportNumber(system, number)

    def _checkParams(self):
        self._pManager = ParameterManager(self._params)

        self._roomInfo = self._pManager.extract("roomInfo", pType=dict, allowEmpty=True)
        self._keywords = self._pManager.extract("keywords", pType=list,
                                          allowEmpty=True)
        self._boardNumber = self._pManager.extract("boardNumber", pType=str, allowEmpty=True, defaultValue="")
        self._reportNumbers = self._pManager.extract("reportNumbers", pType=list, allowEmpty=True, defaultValue=[])

        self._needsToBeScheduled = self._params.get("schedule", True)
        if self._needsToBeScheduled:
            self._dateTime = self._pManager.extract("startDate", pType=datetime.datetime)

        self._duration = self._pManager.extract("duration", pType=int)
        self._title = self._pManager.extract("title", pType=str)
        self._fields = {}

        for field in self._target.getConference().getAbstractMgr().getAbstractFieldsMgr().getFields():
            self._fields[field.getId()] = self._pManager.extract("field_%s"%field.getId(), pType=str,
                                                     allowEmpty=True, defaultValue='')

        self._privileges = {}
        for elemType in ["presenter", "author", "coauthor"]:
            self._privileges[elemType] = self._pManager.extract("%s-privileges"%elemType, pType=dict, allowEmpty=True)

        self._contribTypeId = self._pManager.extract("contributionType", pType=str, allowEmpty=True)
        self._materials = self._pManager.extract("materials", pType=dict, allowEmpty=True)
        self._updateRights = self._params.get("updateRights", False)


    def _performOperation(self):
        self._contribution.setTitle(self._title, notify = False)

        self._contribution.setKeywords('\n'.join(self._keywords))

        self._contribution.setBoardNumber(self._boardNumber)
        self._contribution.setDuration(self._duration/60, self._duration%60)
        self._addReportNumbers()


        if self._needsToBeScheduled:
            checkFlag = self._getCheckFlag()
            adjDate = setAdjustedDate(self._dateTime, self._conf)
            self._contribution.setStartDate(adjDate, check = checkFlag)

        if self._materials:
            for material in self._materials.keys():
                newMaterial = Material()
                newMaterial.setTitle(material)
                for resource in self._materials[material]:
                    newLink = Link()
                    newLink.setURL(resource)
                    newLink.setName(resource)
                    newMaterial.addResource(newLink)
                self._contribution.addMaterial(newMaterial)

        self._schedule(self._contribution)

        for field, value in self._fields.iteritems():
            self._contribution.setField(field, value)

        allParticipantEmails = []
        if (self._target.getConference().getType() == "conference"):
            # for conferences, add authors and coauthors
            self.__addPeople(self._contribution, self._pManager, "author", conference.Contribution.addPrimaryAuthor, conference.Contribution.removePrimaryAuthor, conference.Contribution.getPrimaryAuthorList, allParticipantEmails)
            self.__addPeople(self._contribution, self._pManager, "coauthor", conference.Contribution.addCoAuthor, conference.Contribution.removeCoAuthor, conference.Contribution.getCoAuthorList, allParticipantEmails)
            # set type, if does not exist,
            self._contribution.setType(self._target.getConference().getContribTypeById(self._contribTypeId))


        self.__addPeople(self._contribution, self._pManager, "presenter", conference.Contribution.newSpeaker, conference.Contribution.removeSpeaker, conference.Contribution.getSpeakerList, allParticipantEmails)

        self._setLocationInfo(self._contribution)

        schEntry = self._contribution.getSchEntry()
        fossilizedData = schEntry.fossilize({"MaKaC.schedule.LinkedTimeSchEntry": ILinkedTimeSchEntryMgmtFossil,
                                               "MaKaC.schedule.BreakTimeSchEntry" : IBreakTimeSchEntryMgmtFossil,
                                               "MaKaC.schedule.ContribSchEntry"   : IContribSchEntryMgmtFossil},
                                            tz=self._conf.getTimezone())
        fossilizedDataSlotSchEntry = self._getSlotEntryFossil()

        result = {'id': fossilizedData['id'],
                'entry': fossilizedData,
                'slotEntry': fossilizedDataSlotSchEntry,
                'autoOps': translateAutoOps(self.getAutoOps())}

        if self._needsToBeScheduled:
            result['day'] = schEntry.getAdjustedStartDate().strftime("%Y%m%d")

        return result


class ConferenceScheduleAddContribution(ScheduleEditContributionBase, conferenceServices.ConferenceModifBase):

    def _checkParams(self):
        conferenceServices.ConferenceModifBase._checkParams(self)
        ScheduleEditContributionBase._checkParams(self)
        self._contribution = conference.Contribution()
        self._addToParent(self._contribution)

    def _addToParent(self, contribution):
        self._target.addContribution( contribution )
        contribution.setParent(self._target)

    def _schedule(self, contribution):
        if self._needsToBeScheduled:
            self._target.getSchedule().addEntry(contribution.getSchEntry(), 2)

    def _getSlotEntryFossil(self):
        return None


class SessionSlotScheduleAddContribution(ScheduleEditContributionBase, sessionServices.SessionSlotModifCoordinationBase):

    def _checkParams(self):
        sessionServices.SessionSlotModifCoordinationBase._checkParams(self)
        ScheduleEditContributionBase._checkParams(self)
        self._contribution = conference.Contribution()
        self._addToParent(self._contribution)

    def _addToParent(self, contribution):
        self._session.addContribution( contribution )
        contribution.setParent(self._session.getConference())

    def _schedule(self, contribution):
        return  self._slot.getSchedule().addEntry(contribution.getSchEntry(),
                                                  check = self._getCheckFlag())

    def _getSlotEntryFossil(self):
        return self._slot.getConfSchEntry().fossilize({"MaKaC.schedule.LinkedTimeSchEntry": ILinkedTimeSchEntryMgmtFossil,
                                               "MaKaC.schedule.BreakTimeSchEntry" : IBreakTimeSchEntryMgmtFossil,
                                               "MaKaC.schedule.ContribSchEntry"   : IContribSchEntryMgmtFossil},
                                               tz=self._conf.getTimezone())

class ConferenceScheduleEditContribution(ScheduleEditContributionBase, conferenceServices.ConferenceScheduleModifBase):

    def _checkParams(self):
        conferenceServices.ConferenceScheduleModifBase._checkParams(self)
        ScheduleEditContributionBase._checkParams(self)
        self._contribution = self._schEntry.getOwner()

    def _addToParent(self, contribution):
        pass

    def _schedule(self, contribution):
        pass

    def _getSlotEntryFossil(self):
        return None


class SessionSlotScheduleEditContribution(ScheduleEditContributionBase, sessionServices.SessionSlotModifCoordinationBase):

    def _checkParams(self):
        sessionServices.SessionSlotModifCoordinationBase._checkParams(self)
        ScheduleEditContributionBase._checkParams(self)
        self._contribution = self._schEntry.getOwner()

    def _addToParent(self, contribution):
        pass

    def _schedule(self, contribution):
        pass

    def _getSlotEntryFossil(self):
        return self._slot.getConfSchEntry().fossilize({"MaKaC.schedule.LinkedTimeSchEntry": ILinkedTimeSchEntryMgmtFossil,
                                               "MaKaC.schedule.BreakTimeSchEntry" : IBreakTimeSchEntryMgmtFossil,
                                               "MaKaC.schedule.ContribSchEntry"   : IContribSchEntryMgmtFossil},
                                               tz=self._conf.getTimezone())

class ConferenceScheduleAddSession(ScheduleOperation, conferenceServices.ConferenceModifBase, LocationSetter):

    def __addConveners2Slot(self, slot):
        for convenerValues in self._conveners:
            convener = conference.SlotChair()
            DictPickler.update(convener, convenerValues)
            slot.addConvener(convener)

    def _checkParams(self):
        conferenceServices.ConferenceModifBase._checkParams(self)

        pManager = ParameterManager(self._params, timezone = self._conf.getTimezone())

        self._roomInfo = pManager.extract("roomInfo", pType=dict, allowEmpty=True)
        self._conveners = pManager.extract("conveners", pType=list,
                                           allowEmpty=True)
        self._startDateTime = pManager.extract("startDateTime",
                                               pType=datetime.datetime)
        self._endDateTime = pManager.extract("endDateTime",
                                             pType=datetime.datetime)
        self._title = pManager.extract("title", pType=str)
        self._subtitle = pManager.extract("subtitle", pType=str, allowEmpty=True)
        self._textColor = pManager.extract("textColor", pType=str)
        self._bgColor = pManager.extract("bgColor", pType=str)
        self._description = pManager.extract("description", pType=str,
                                          allowEmpty=True)
        self._scheduleType = pManager.extract("sessionType", pType=str,
                                          allowEmpty=False)


    def _performOperation(self):

        conf = self._target
        session = conference.Session()

        session.setValues({
                     "title": self._title or "",
                     "description": self._description or "",
                     "sDate": self._startDateTime,
                     "eDate": self._endDateTime
                     })
        conf.addSession(session)
        session.setScheduleType(self._scheduleType)
        session.setTextColor(self._textColor)
        session.setBgColor(self._bgColor)

        slot = conference.SessionSlot(session)
        slot.setScheduleType(self._scheduleType)
        slot.setTitle(self._subtitle or "")
        slot.setStartDate(session.getStartDate())

        tz = pytz.timezone(self._conf.getTimezone())
        if session.getEndDate().astimezone(tz).date() > session.getStartDate().astimezone(tz).date():
            newEndDate = session.getStartDate().astimezone(tz).replace(hour=23,minute=59).astimezone(pytz.timezone('UTC'))
        else:
            newEndDate = session.getEndDate()
        dur = newEndDate - session.getStartDate()
        if dur > datetime.timedelta(days=1):
            dur = datetime.timedelta(days=1)

        slot.setDuration(dur=dur)
        session.addSlot(slot)

        self.__addConveners2Slot(slot)
        self._setLocationInfo(slot)

        logInfo = session.getLogInfo()
        logInfo["subject"] =  _("Created new session: %s")%session.getTitle()
        self._conf.getLogHandler().logAction(logInfo, log.ModuleNames.TIMETABLE)

        schEntry = slot.getConfSchEntry()
        fossilizedData = schEntry.fossilize(ILinkedTimeSchEntryMgmtFossil, tz=conf.getTimezone())
        fossilizedData['entries'] = {}

        self.initializeFilteringCriteria(session.getId(), schEntry.getSchedule().getOwner().getId())

        return {'day': slot.getAdjustedStartDate().strftime("%Y%m%d"),
                'id': fossilizedData['id'],
                'entry': fossilizedData,
                'session': session.fossilize(ISessionFossil, tz=self._conf.getTimezone()),
                'autoOps': translateAutoOps(self.getAutoOps())}

    def initializeFilteringCriteria(self, sessionId, conferenceId):
        # Filtering criteria: by default make new session type checked
        sessionDict = session.setdefault('ContributionFilterConf%s' % conferenceId, {})
        if 'sessions' in sessionDict:
            #Append the new type to the existing list
            sessionDict['sessions'].append(sessionId)
        else:
            #Create a new entry for the dictionary containing the new type
            sessionDict['sessions'] = [sessionId]
        session.modified = True

class ConferenceScheduleDeleteSession(ScheduleOperation, conferenceServices.ConferenceScheduleModifBase):

    def _performOperation(self):
        sessionSlot = self._schEntry.getOwner()
        session = sessionSlot.getSession()

        if session.isClosed():
            raise ServiceAccessError(_("""The modification of the session "%s" is not allowed because it is closed""")%session.getTitle())

        logInfo = session.getLogInfo()
        logInfo["subject"] = "Deleted session: %s"%session.getTitle()
        self._conf.getLogHandler().logAction(logInfo, log.ModuleNames.TIMETABLE)

        self._conf.removeSession(session)

class ConferenceScheduleDeleteContribution(ScheduleOperation, conferenceServices.ConferenceScheduleModifBase):

    def _performOperation(self):
        contrib = self._schEntry.getOwner()
        logInfo = contrib.getLogInfo()

        contrib._notify("contributionUnscheduled")
        self._conf.getSchedule().removeEntry(self._schEntry)

        if self._conf.getType() == "meeting":
            logInfo["subject"] =  _("Deleted contribution: %s")%contrib.getTitle()
            contrib.delete()
        else:
            logInfo["subject"] =  _("Unscheduled contribution: %s")%contrib.getTitle()
        self._conf.getLogHandler().logAction(logInfo, log.ModuleNames.TIMETABLE)


class SessionScheduleDeleteSessionSlot(ScheduleOperation, sessionServices.SessionModifUnrestrictedTTCoordinationBase):

    def _performOperation(self):
        if len(self._session.getSlotList()) > 1:
            self._session.removeSlot(self._slot)
        else:
            logInfo = self._session.getLogInfo()
            logInfo["subject"] = "Deleted session: %s"%self._session.getTitle()
            self._conf.getLogHandler().logAction(logInfo, log.ModuleNames.TIMETABLE)
            self._conf.removeSession(self._session)

class SessionScheduleChangeSessionColors(ScheduleOperation, sessionServices.SessionModifBase):

    def _checkParams(self):
        sessionServices.SessionModifBase._checkParams(self)

        try:
            self._bgColor = self._params["bgColor"]
            self._textColor = self._params["textColor"]
        except:
            raise ServiceError("ERR-S4", "Color parameters not provided.")

    def _performOperation(self):
        self._session.setBgColor(self._bgColor)
        self._session.setTextColor(self._textColor)

class ScheduleEditBreakBase(ScheduleOperation, LocationSetter):

    def _checkParams(self):

        pManager = ParameterManager(self._params, timezone = self._conf.getTimezone())

        self._roomInfo = pManager.extract("roomInfo", pType=dict, allowEmpty=True)
        self._dateTime = pManager.extract("startDate", pType=datetime.datetime)
        self._duration = pManager.extract("duration", pType=int)
        self._title = pManager.extract("title", pType=str)
        self._description = pManager.extract("description", pType=str,
                                          allowEmpty=True)
        self._textColor = pManager.extract("textColor", pType=str)
        self._bgColor = pManager.extract("bgColor", pType=str)
        self._oldId = None

    def _performOperation(self):

        self._brk.setValues({"title": self._title or "",
                       "description": self._description or "",
                       "startDate": self._dateTime,
                       "durMins": str(self._duration),
                       "durHours": "0"},
                       check = 2,
                       tz = self._conf.getTimezone())

        self._brk.setTextColor(self._textColor)
        self._brk.setBgColor(self._bgColor)

        self._setLocationInfo(self._brk)
        self._addToSchedule(self._brk)

        fossilizedDataSlotSchEntry = self._getSlotEntryFossil()
        fossilizedData = self._brk.fossilize(IBreakTimeSchEntryMgmtFossil, tz=self._conf.getTimezone())

        res = {'day': self._brk.getAdjustedStartDate().strftime("%Y%m%d"),
                'id': fossilizedData['id'],
                'slotEntry': fossilizedDataSlotSchEntry,
                'autoOps': translateAutoOps(self.getAutoOps()),
                'entry': fossilizedData}

        if self._oldId and self._oldId != Conversion.locatorString(self._schEntry)+"b"+self._schEntry.getId():
            res['oldId'] = self._oldId

        return res

class ConferenceScheduleAddBreak(ScheduleEditBreakBase, conferenceServices.ConferenceModifBase):

    def _checkParams(self):
        conferenceServices.ConferenceModifBase._checkParams(self)
        ScheduleEditBreakBase._checkParams(self)
        self._brk = schedule.BreakTimeSchEntry()

    def _addToSchedule(self, b):
        self._target.getSchedule().addEntry(b, 2)

    def _getSlotEntryFossil(self):
        return None


class ConferenceScheduleEditBreak(ScheduleEditBreakBase, conferenceServices.ConferenceScheduleModifBase):

    def _checkParams(self):
        conferenceServices.ConferenceScheduleModifBase._checkParams(self)
        ScheduleEditBreakBase._checkParams(self)
        self._brk = self._schEntry

    def _addToSchedule(self, b):
        pass

    def _getSlotEntryFossil(self):
        return None

class ConferenceScheduleDeleteBreak(ScheduleOperation, conferenceServices.ConferenceScheduleModifBase):

    def _performOperation(self):
        self._conf.getSchedule().removeEntry(self._schEntry)

class SessionSlotScheduleAddBreak(ScheduleEditBreakBase, sessionServices.SessionSlotModifCoordinationBase):

    def _checkParams(self):
        sessionServices.SessionSlotModifCoordinationBase._checkParams(self)
        ScheduleEditBreakBase._checkParams(self)
        self._brk = schedule.BreakTimeSchEntry()

    def _addToSchedule(self, b):
        self._slot.getSchedule().addEntry(b, check = self._getCheckFlag())

    def _getSlotEntryFossil(self):
        return self._slot.getConfSchEntry().fossilize({"MaKaC.schedule.LinkedTimeSchEntry": ILinkedTimeSchEntryMgmtFossil,
                                               "MaKaC.schedule.BreakTimeSchEntry" : IBreakTimeSchEntryMgmtFossil,
                                               "MaKaC.schedule.ContribSchEntry"   : IContribSchEntryMgmtFossil},
                                               tz=self._conf.getTimezone())


class SessionSlotScheduleEditBreak(ScheduleEditBreakBase, sessionServices.SessionSlotModifCoordinationBase):

    def _checkParams(self):
        sessionServices.SessionSlotModifCoordinationBase._checkParams(self)
        ScheduleEditBreakBase._checkParams(self)
        self._brk = self._schEntry
        self._oldStartDate = self._schEntry.getStartDate().date()
        self._oldId = Conversion.locatorString(self._schEntry)+"b"+self._schEntry.getId()

    def _addToSchedule(self, b):
        # if the schedule target day is different from the current
        if self._oldStartDate != self._dateTime.date():

            # remove the entry
            self._schEntry.getSchedule().removeEntry(self._schEntry)

            # set it to the new date
            self._schEntry.setStartDate(self._dateTime)
            # add it on the new date
            self._conf.getSchedule().addEntry(self._schEntry, check=2)

    def _getSlotEntryFossil(self):
        return self._slot.getConfSchEntry().fossilize({"MaKaC.schedule.LinkedTimeSchEntry": ILinkedTimeSchEntryMgmtFossil,
                                               "MaKaC.schedule.BreakTimeSchEntry" : IBreakTimeSchEntryMgmtFossil,
                                               "MaKaC.schedule.ContribSchEntry"   : IContribSchEntryMgmtFossil},
                                               tz=self._conf.getTimezone())


class SessionSlotScheduleDeleteBreak(ScheduleOperation, sessionServices.SessionSlotModifCoordinationBase):

    def _checkParams(self):
        sessionServices.SessionSlotModifCoordinationBase._checkParams(self)

    def _performOperation(self):
        self._slot.getSchedule().removeEntry(self._schEntry)

class SessionSlotScheduleDeleteContribution(ScheduleOperation, sessionServices.SessionSlotModifCoordinationBase):

    def _checkParams(self):
        sessionServices.SessionSlotModifCoordinationBase._checkParams(self)

    def _performOperation(self):

        contrib = self._schEntry.getOwner()

        logInfo = contrib.getLogInfo()
        contrib._notify("contributionUnscheduled")
        self._slot.getSchedule().removeEntry(self._schEntry)

        if type == "meeting":
            logInfo["subject"] = "Deleted contribution: %s" %contrib.getTitle()
            contrib.delete()
        else:
            logInfo["subject"] = "Unscheduled contribution: %s"%contrib.getTitle()

        self._conf.getLogHandler().logAction(logInfo, log.ModuleNames.TIMETABLE)


class ModifyStartEndDate(ScheduleOperation):

    def _checkParams(self):

        pManager = ParameterManager(self._params, timezone = self._conf.getTimezone())
        self._startDate = pManager.extract("startDate", pType=datetime.datetime)
        self._endDate = pManager.extract("endDate", pType=datetime.datetime)
        self._reschedule = pManager.extract("reschedule", pType=bool)

    def _performOperation(self):

        checkFlag = self._getCheckFlag()

        # if we want to reschedule other entries, let's store the old parameters
        # and the list of entries that will be rescheduled (after this one)

        if self._reschedule:
            oldStartDate=copy.copy(self._schEntry.getStartDate())
            oldDuration=copy.copy(self._schEntry.getDuration())
            i = self._schEntry.getSchedule().getEntries().index(self._schEntry) + 1
            lentries = len(self._schEntry.getSchedule().getEntries())
            while i < lentries and self._schEntry.getStartDate() >= self._schEntry.getSchedule().getEntries()[i].getStartDate():
                i += 1
            j = i
            while j < lentries and self._schEntry.getAdjustedStartDate().date() == \
                      self._schEntry.getSchedule().getEntries()[j].getAdjustedStartDate().date():
                j += 1
            entriesList = self._schEntry.getSchedule().getEntries()[i:j]

        duration = self._endDate - self._startDate
        owner = self._schEntry.getOwner()
        if isinstance(owner, SessionSlot) and owner.getSession().isClosed():
            raise ServiceAccessError(_("""The modification of the session "%s" is not allowed because it is closed""")%owner.getSession().getTitle())
        if isinstance(owner, SessionSlot) and owner.getSession().getScheduleType() == "poster":
            # If it is a poster session we must modify the size of all the contributions inside it.
            for entry in owner.getSchedule().getEntries():
                entry.setDuration(dur=duration, check=0)
        # The order to set the start date and duration is important, please keep it like this.
        # Otherwise, by modifying the startDate we might find entries inside a slot that are
        # temporarly outside and an exception will be raised.
        self._schEntry.setDuration(dur=duration,check=checkFlag)
        self._schEntry.setStartDate(self._startDate, moveEntries=1, check=checkFlag)

        # In case of 'reschedule', calculate the time difference
        if self._reschedule:
            diff = (self._schEntry.getStartDate() - oldStartDate) + (self._schEntry.getDuration() - oldDuration)

            # shift accordingly
            self._schEntry.getSchedule().moveEntriesBelow(diff, entriesList)

            # retrieve results
            fossilizedData = schedule.ScheduleToJson.process(self._schEntry.getSchedule(), self._conf.getTimezone(),
                                                          None, days = [self._schEntry.getAdjustedStartDate()],
                                                          mgmtMode = True)
            entryId = fossilizedData.keys()[0]
            fossilizedData = fossilizedData.values()[0]
        else:
            entryId, fossilizedData = schedule.ScheduleToJson.processEntry(self._schEntry, self._conf.getTimezone(),
                                                                        None, mgmtMode = True)

        return {'day': self._schEntry.getAdjustedStartDate().strftime("%Y%m%d"),
                'id': entryId,
                'entry': fossilizedData,
                'autoOps': translateAutoOps(self.getAutoOps())}


class SessionSlotScheduleModifyStartEndDate(ModifyStartEndDate, sessionServices.SessionSlotModifCoordinationBase):

    def _checkParams(self):
        sessionServices.SessionSlotModifCoordinationBase._checkParams(self)
        ModifyStartEndDate._checkParams(self)
        pm = ParameterManager(self._params)
        self._isSessionTimetable = pm.extract("sessionTimetable", pType=bool, allowEmpty=True)


    def _performOperation(self):

        result = ModifyStartEndDate._performOperation(self)

        if self._isSessionTimetable:
            schEntry = self._slot.getSessionSchEntry()
        else:
            schEntry = self._slot.getConfSchEntry()

        self._slot.cleanCache()

        fossilizedDataSlotSchEntry = schEntry.fossilize({"MaKaC.schedule.LinkedTimeSchEntry": ILinkedTimeSchEntryMgmtFossil,
                                               "MaKaC.schedule.BreakTimeSchEntry" : IBreakTimeSchEntryMgmtFossil,
                                               "MaKaC.schedule.ContribSchEntry"   : IContribSchEntryMgmtFossil},
                                               tz=self._conf.getTimezone())
        fossilizedDataSession = self._session.fossilize(ISessionFossil, tz=self._conf.getTimezone())
        result.update({'slotEntry': fossilizedDataSlotSchEntry,
                       'session': fossilizedDataSession})

        return result


class ConferenceScheduleModifyStartEndDate(ModifyStartEndDate, conferenceServices.ConferenceScheduleModifBase):

   def _checkParams(self):
        conferenceServices.ConferenceScheduleModifBase._checkParams(self)
        ModifyStartEndDate._checkParams(self)


class SessionScheduleModifyStartEndDate(ModifyStartEndDate, sessionServices.SessionModifUnrestrictedTTCoordinationBase):

   def _checkParams(self):
        sessionServices.SessionModifUnrestrictedTTCoordinationBase._checkParams(self)
        ModifyStartEndDate._checkParams(self)

class ConferenceScheduleGetDayEndDate(ScheduleOperation, conferenceServices.ConferenceModifBase):

    def _checkParams(self):
        conferenceServices.ConferenceModifBase._checkParams(self)
        pManager = ParameterManager(self._params)

        date = pManager.extract("selectedDay", pType=datetime.date)
        self._date = datetime.datetime(date.year, date.month, date.day, tzinfo=pytz.timezone(self._conf.getTimezone()))

    def _performOperation(self):
        return self._target.getSchedule().calculateDayEndDate(self._date).strftime('%Y/%m/%d %H:%M')

class SessionSlotScheduleGetDayEndDate(ScheduleOperation, sessionServices.SessionSlotModifCoordinationBase):

    def _checkParams(self):
        sessionServices.SessionSlotModifCoordinationBase._checkParams(self)
        pManager = ParameterManager(self._params)
        date = pManager.extract("selectedDay", pType=datetime.date)
        self._date = datetime.datetime(date.year, date.month, date.day, tzinfo=pytz.timezone(self._conf.getTimezone()))

    def _performOperation(self):
        eDate = self._slot.getSchedule().calculateDayEndDate(self._date)
        return eDate.strftime('%Y/%m/%d %H:%M')

class SessionSlotGetFossil(sessionServices.SessionSlotDisplayBase):

    def _getAnswer(self):
        return fossilize(self._slot)

class SessionSlotGetBooking(ScheduleOperation, sessionServices.SessionSlotDisplayBase, roomBooking.GetBookingBase):
    def _performOperation(self):
        return self._getRoomInfo(self._target)

class SessionScheduleGetDayEndDate(ScheduleOperation, sessionServices.SessionModifUnrestrictedTTCoordinationBase):

    def _checkParams(self):
        sessionServices.SessionModifUnrestrictedTTCoordinationBase._checkParams(self)
        pManager = ParameterManager(self._params)

        date = pManager.extract("selectedDay", pType=datetime.date)
        self._date = datetime.datetime(date.year, date.month, date.day)

    def _performOperation(self):
        eDate = self._target.getSchedule().calculateDayEndDate(self._date)
        return eDate.strftime('%Y/%m/%d %H:%M')

class ScheduleEditSlotBase(ScheduleOperation, LocationSetter):

    def _addConveners(self, slot):
        pass

    def _setSessionTitle(self, slot):
        pass

    def _checkParams(self):
        self.pManager = ParameterManager(self._params)

        self._startDateTime = self.pManager.extract("startDateTime",
                                               pType=datetime.datetime)
        self._endDateTime = self.pManager.extract("endDateTime",
                                             pType=datetime.datetime)
        self._title = self.pManager.extract("title", pType=str, allowEmpty=True)
        self._conveners = self.pManager.extract("conveners", pType=list,
                                           allowEmpty=True)
        self._roomInfo = self.pManager.extract("roomInfo", pType=dict, allowEmpty=True)
        self._isSessionTimetable = self.pManager.extract("sessionTimetable", pType=bool, allowEmpty=True)

    def _performOperation(self):
        #if there is something inside the session we have to move it as well

        values = {"title": self._title or "",
                  "sDate": self._startDateTime,
                  "eDate": self._endDateTime}

        if len(self._slot.getEntries()) != 0 :
            values.update({"move": 1})
        self._slot.setValues(values)

        self. _addConveners(self._slot)
        self._setLocationInfo(self._slot)
        self._setSessionTitle(self._slot)

        self._addToSchedule()

        logInfo = self._slot.getLogInfo()
        logInfo["subject"] = "Created new session block: %s" % self._slot.getTitle()
        self._conf.getLogHandler().logAction(logInfo, log.ModuleNames.TIMETABLE)

        if self._isSessionTimetable:
            schEntry = self._slot.getSessionSchEntry()
        else:
            schEntry = self._slot.getConfSchEntry()
        entryId, fossilizedData = schedule.ScheduleToJson.processEntry(schEntry, self._conf.getTimezone(),
                                                                    None, mgmtMode = True)

        return {'day': schEntry.getAdjustedStartDate().strftime("%Y%m%d"),
                'id': fossilizedData['id'],
                'entry': fossilizedData,
                'autoOps': translateAutoOps(self.getAutoOps()),
                'session': self._slot.getSession().fossilize(ISessionFossil, tz=self._conf.getTimezone())}

class SessionScheduleAddSessionSlot(ScheduleEditSlotBase, sessionServices.SessionModifUnrestrictedTTCoordinationBase):

    def _checkParams(self):
        sessionServices.SessionModifUnrestrictedTTCoordinationBase._checkParams(self)
        ScheduleEditSlotBase._checkParams(self)
        self._slot = conference.SessionSlot(self._target)
        self._sessionTitle = self.pManager.extract("sessionTitle", pType = str, allowEmpty=False)


    def _addToSchedule(self):
        self._target.addSlot(self._slot)

    def _addConveners(self, slot):
        for convenerValues in self._conveners:
            convener = conference.SlotChair()
            DictPickler.update(convener, convenerValues)
            slot.addConvener(convener)

    def _setSessionTitle(self, slot):
        slot.getSession().setTitle(self._sessionTitle)

class SessionScheduleEditSessionSlot(ScheduleEditSlotBase, sessionServices.SessionModifUnrestrictedTTCoordinationBase):

    def _checkParams(self):
        sessionServices.SessionModifUnrestrictedTTCoordinationBase._checkParams(self)
        ScheduleEditSlotBase._checkParams(self)
        self._sessionTitle = self.pManager.extract("sessionTitle", pType = str, allowEmpty=False)
        self._subtitle = self.pManager.extract("subtitle", pType = str, allowEmpty=True)

    def _addToSchedule(self):
        pass

    def _addConveners(self, slot):
        convenersIds = []
        for convenerValues in self._conveners:
            if convenerValues.has_key("isConfParticipant"):
                convener = slot.getConvenerById(str(convenerValues['id']))
                DictPickler.update(convener, convenerValues)
            else:
                convener = conference.SlotChair()
                DictPickler.update(convener, convenerValues)
                slot.addConvener(convener)
            convenersIds.append(convener.getId())

        for conv in slot.getConvenerList()[:]:
            if conv.getId() not in convenersIds:
                slot.removeConvener(conv)

    def _setSessionTitle(self, slot):
        slot.getSession().setTitle(self._sessionTitle)

class SessionScheduleEditSessionSlotById(SessionScheduleEditSessionSlot):
    """
    Edits session slot. Session slot is identified by its id within a session,
    not like in the parent's class by schedule id.
    """
    def _checkParams(self):
        if self._params.has_key("scheduleEntry"):
            del self._params["scheduleEntry"]
        SessionScheduleEditSessionSlot._checkParams(self)
        self._slot = self._session.slots[self._params["sessionSlotId"]]


class ConferenceSetSessionSlots( conferenceServices.ConferenceTextModificationBase ):
    """
    Set or unset automatic conflict solving for timetable
    """
    def _handleSet(self):
        if self._value:
            if not self._target.getEnableSessions():
                raise ServiceError("ERR-S0", "Sessions must be active for"+
                                  " session slots to be enabled.")
            self._target.enableSessionSlots()
        else:
            for s in self._target.getSessionList() :
                if len(s.getSlotList()) > 1 :
                    raise ServiceError("ERR-S1", "More than one slot defined for session "+
                                      "'%s'. Cannot disable displaying multiple"
                                      " session slots." % self._target.getTitle())
            self._target.disableSessionSlots()


    def _handleGet(self):
        return self._target.getEnableSessionSlots()

class ConferenceSetScheduleSessions( conferenceServices.ConferenceTextModificationBase ):
    """
    Set or unset automatic conflict solving for timetable
    """
    def _handleSet(self):
        if self._value:
            self._target.enableSessions()
        else:
            if len(self._target.getSessionList()) > 0 :
                raise ServiceError("ERR-S2","Sessions already defined. "+
                                  "Cannot disable them now.")
            self._target.disableSessions()
            self._target.disableSessionSlots()


    def _handleGet(self):
        return self._target.getEnableSessions()

class ConferenceGetAllSpeakers(conferenceServices.ConferenceDisplayBase):
    """
    Get all speakers from contributions from the event
    """
    def _getAnswer(self):
        d = {}
        for contribution in self._target.getContributionList() :
            for elem in contribution.getSpeakerList().fossilize(IContributionParticipationTTMgmtFossil):
                elem['id'] = "%s.%s" % (contribution.getId(), elem['id'])
                d[elem['name']] = elem
        return d.values()

class ConferenceGetAllConveners(conferenceServices.ConferenceDisplayBase):
    """
    Get all conveners of sessions from the event
    """
    def _getAnswer(self):
        d = {}
        for session in self._target.getSessionList() :
            for elem in session.getConvenerList().fossilize(IConferenceParticipationFossil):
                elem['id'] = "%s.%s" % (session.getId(), elem['id'])
                d[elem['name']] = elem
        return d.values()

### Breaks

class BreakBase(object):

    def _checkParams( self ):

        try:
            self._target = self._conf = conference.ConferenceHolder().getById(self._params["conference"]);
            if self._conf == None:
                raise Exception("Conference id not specified.")
        except:
            raise ServiceError("ERR-E4", "Invalid conference id.")

        slotId = self._params.get("slot", None)

        try:
            if slotId != None:
                self._slot = self._session.getSlotById(slotId)
        except Exception, e:
            raise ServiceError("ERR-S3", "Invalid slot id.",inner=str(e))

        except:
            raise ServiceError("ERR-C0", "Invalid break id.")

        try:
            entry = self._params["break"]

            if slotId != None:
                self._break = self._slot.getSchedule().getEntryById(entry)
            else:
                self._break = self._conf.getSchedule().getEntryById(entry)

            if self._break == None:
                raise Exception("Break id not specified.")
        except:
            raise ServiceError("ERR-C0", "Invalid break id.")


        # create a parameter manager that checks the consistency of passed parameters
        self._pm = ParameterManager(self._params)

class BreakDisplayBase(base.ProtectedDisplayService, BreakBase):

    def _checkParams(self):
        BreakBase._checkParams(self)
        base.ProtectedDisplayService._checkParams(self)


class BreakGetBooking(BreakDisplayBase, roomBooking.GetBookingBase):
    def _getAnswer(self):
        return self._getRoomInfo(self._break)


class GetUnscheduledContributions(ScheduleOperation):

    """ Returns the list of unscheduled contributions for the target """

    def _performOperation(self):
        unscheduledList = []

        for contrib in self._target.getContributionList():
            if self._isScheduled(contrib):
                continue
            unscheduledList.append(contrib)

        return fossilize(unscheduledList, IContributionFossil, tz=self._conf.getTimezone())

class ConferenceGetUnscheduledContributions(GetUnscheduledContributions, conferenceServices.ConferenceModifBase):

    def _isScheduled(self, contrib):
        return contrib.getSession() is not None or \
               contrib.isScheduled() or \
               isinstance(contrib.getCurrentStatus(),conference.ContribStatusWithdrawn)

class SessionGetUnscheduledContributions(GetUnscheduledContributions, sessionServices.SessionModifCoordinationBase):

    def _isScheduled(self, contrib):
        return contrib.isScheduled() or \
               isinstance(contrib.getCurrentStatus(),conference.ContribStatusWithdrawn)



class ScheduleContributions(ScheduleOperation):

    """ Schedules the contribution in the timetable of the event"""

    def _checkParams(self):
        pManager = ParameterManager(self._params,
                                    timezone = self._target.getTimezone())

        self._ids = pManager.extract("ids", pType=list, allowEmpty=False)
        date = pManager.extract("date", pType=datetime.date, allowEmpty=False)

        # convert date to datetime
        self._date = pytz.timezone(self._target.getTimezone()).localize(datetime.datetime(*(date.timetuple()[:6]+(0,))))


    def _performOperation(self):

        entries = []

        for contribId in self._ids:

            contrib = self._getContributionId(contribId)

            isPoster = self._handlePosterContributions(contrib)

            if not isPoster:
                d = self._target.getSchedule().calculateDayEndDate(self._date)
                contrib.setStartDate(d)
                if isinstance(self._target, conference.SessionSlot):
                    contrib.setDuration(dur=self._target.getSession().getContribDuration())

            schEntry = contrib.getSchEntry()

            self._target.getSchedule().addEntry(schEntry, check = self._getCheckFlag())

            fossilizedData = schEntry.fossilize(IContribSchEntryMgmtFossil, tz=self._conf.getTimezone())
            fossilizedDataSlotSchEntry = self._getSlotEntryFossil()

            entries.append({'day': schEntry.getAdjustedStartDate().strftime("%Y%m%d"),
                            'id': fossilizedData['id'],
                            'entry': fossilizedData,
                            'slotEntry': fossilizedDataSlotSchEntry,
                            'autoOps': translateAutoOps(self.getAutoOps())
                            })
        return entries

class SessionSlotScheduleContributions(ScheduleContributions, sessionServices.SessionSlotModifCoordinationBase):
    def _checkParams(self):

        sessionServices.SessionSlotModifCoordinationBase._checkParams(self)
        ScheduleContributions._checkParams(self)

        pManager = ParameterManager(self._params,
                                    timezone = self._target.getTimezone())

        self._isSessionTimetable = pManager.extract("sessionTimetable", pType=bool, allowEmpty=True)


    def _getContributionId(self, contribId):
        return self._target.getSession().getContributionById(contribId)

    def _handlePosterContributions(self, contrib):
        if self._slot.getSession().getScheduleType() == "poster":
            contrib.setStartDate(self._slot.getStartDate())
            contrib.setDuration(dur=self._slot.getDuration())
            return True
        return False

    def _getSlotEntryFossil(self):

        if self._isSessionTimetable:
            entry = self._slot.getSessionSchEntry()
        else:
            entry = self._slot.getConfSchEntry()

        return entry.fossilize({"MaKaC.schedule.LinkedTimeSchEntry": ILinkedTimeSchEntryMgmtFossil,
                                "MaKaC.schedule.BreakTimeSchEntry" : IBreakTimeSchEntryMgmtFossil,
                                "MaKaC.schedule.ContribSchEntry"   : IContribSchEntryMgmtFossil},
                               tz=self._conf.getTimezone())

class ConferenceScheduleContributions(ScheduleContributions, conferenceServices.ConferenceModifBase):
    def _checkParams(self):
        conferenceServices.ConferenceModifBase._checkParams(self)
        ScheduleContributions._checkParams(self)

    def _getContributionId(self, contribId):
        return self._target.getContributionById(contribId)

    def _handlePosterContributions(self, contrib):
        pass

    def _getSlotEntryFossil(self):
        return None

class MoveEntryBase(ScheduleOperation):

    def _checkParams(self):
        pManager = ParameterManager(self._params, timezone = self._conf.getTimezone())
        self._contribPlace = pManager.extract("value", pType=str, allowEmpty=False)
        self._schEntryId = pManager.extract("scheduleEntryId", pType=int, allowEmpty=False)
        self._sessionId = pManager.extract("sessionId", pType=str, allowEmpty=True, defaultValue=None)
        self._sessionSlotId = pManager.extract("sessionSlotId", pType=str, allowEmpty=True, defaultValue=None)
        self._newTime = pManager.extract("newTime", pType=datetime.datetime, allowEmpty=True, defaultValue=None)

    def _performOperation(self):
        utc = pytz.timezone('UTC')
        if (self._sessionId != None and self._sessionSlotId != None):
            self._schEntry = self._conf.getSessionById(self._sessionId).getSlotById(self._sessionSlotId).getSchedule().getEntryById(self._schEntryId)
        else:
            self._schEntry = self._conf.getSchedule().getEntryById(self._schEntryId)

        if self._schEntry is None:
            raise NoReportError("It seems that the entry has been deleted or already moved. Please refresh the page.")
        owner = self._schEntry.getOwner()

        if self._contribPlace.strip() != "":
            entriesFossilsDict = {"MaKaC.schedule.LinkedTimeSchEntry": ILinkedTimeSchEntryMgmtFossil,
                                               "MaKaC.schedule.BreakTimeSchEntry" : IBreakTimeSchEntryMgmtFossil,
                                               "MaKaC.schedule.ContribSchEntry"   : IContribSchEntryMgmtFossil}
            oldSch = self._schEntry.fossilize(entriesFossilsDict)
            oldDate = self._schEntry.getStartDate()
            oldSch['startDate'] = formatDateTime(oldDate.astimezone(pytz.timezone(owner.getTimezone())))

            sessionId,sessionSlotId = self._contribPlace.split(":")

            if sessionId != "conf":
                # Moving inside a session
                session = self._conf.getSessionById(sessionId)
                if session is not None:

                    if session.isClosed():
                        raise ServiceAccessError(_("""The modification of the session "%s" is not allowed because it is closed""")%session.getTitle())

                    if session.getScheduleType() == "poster" and isinstance(self._schEntry, BreakTimeSchEntry):
                        raise NoReportError(_("It is not possible to move a break inside a poster session"))

                    slot = session.getSlotById(sessionSlotId)
                    if slot is not None:
                        fossilizedDataSession = session.fossilize(ISessionFossil, tz=self._conf.getTimezone())
                        # unschedule entry from previous place
                        self._schEntry.getSchedule().removeEntry(self._schEntry)
                        if isinstance(owner, conference.Contribution):
                            owner.setSession(session)
                        if session.getScheduleType() == "poster":
                            self._schEntry.setStartDate(slot.getStartDate())
                            self._schEntry.setDuration(dur=slot.getDuration())
                        else:
                            if self._newTime:
                                self._schEntry.setStartDate(self._newTime.astimezone(utc))
                            else:
                                # if we have no clear indication of where we should place this,
                                # put it after everything else
                                self._schEntry.setStartDate(slot.getSchedule().calculateEndDate())
                            #self._schEntry.setDuration(dur=session.getContribDuration())
                        # add it to new container
                        slot.getSchedule().addEntry(self._schEntry, check=2)
                        fossilizedDataSlotSchEntry = slot.getConfSchEntry().fossilize(entriesFossilsDict, tz=self._conf.getTimezone())
                    else:
                        raise NoReportError(_("It seems that the session slot has been deleted, please refresh the page"))
                else:
                    raise NoReportError(_("It seems that the session has been deleted, please refresh the page"))
            else:
                # Moving inside the top-level timetable

                fossilizedDataSlotSchEntry = None
                if isinstance(owner, conference.Contribution):
                    fossilizedDataSession  = owner.getOwner().fossilize(tz=self._conf.getTimezone())
                else:
                    fossilizedDataSession  = None

                # the target date/time
                parsedDate = parseDate(sessionSlotId, format="%Y%m%d")

                if self._newTime:
                    newStartDate = self._newTime.astimezone(utc)
                else:
                    owner_tz = pytz.timezone(owner.getTimezone())
                    newStartDate = owner_tz.localize(datetime.datetime.combine(parsedDate,
                                                                               oldDate.astimezone(owner_tz).time())).astimezone(utc)

                self._schEntry.getSchedule().removeEntry(self._schEntry)

                self._schEntry.setStartDate(newStartDate)
                if isinstance(owner, conference.Contribution):
                    owner.setSession(None)
                self._conf.getSchedule().addEntry(self._schEntry, check=2)

        newFossilizedEntry = self._schEntry.fossilize(entriesFossilsDict)
        return {'entry': newFossilizedEntry,
                'old': oldSch,
                'id': newFossilizedEntry['id'],
                'day': self._schEntry.getAdjustedStartDate().strftime("%Y%m%d"),
                'session': fossilizedDataSession ,
                'slotEntry': fossilizedDataSlotSchEntry,
                'autoOps': translateAutoOps(self.getAutoOps())}

class MoveEntry(MoveEntryBase, conferenceServices.ConferenceModifBase):

    def _checkParams(self):
        conferenceServices.ConferenceModifBase._checkParams(self)
        MoveEntryBase._checkParams(self)

class MoveEntryFromSessionBlock(MoveEntryBase, sessionServices.SessionSlotModifCoordinationBase):

    def _checkParams(self):
        sessionServices.SessionSlotModifCoordinationBase._checkParams(self)
        MoveEntryBase._checkParams(self)


class MoveEntryUpDown(ScheduleOperation):
    def _checkParams(self):

        pManager = ParameterManager(self._params, timezone = self._conf.getTimezone())
        self._direction = pManager.extract("direction", pType=bool, allowEmpty=False)
        self._schEntryId = pManager.extract("scheduleEntryId", pType=int, allowEmpty=False)


    def _performOperation(self):

        sched = self._target.getSchedule()
        schEntry = sched.getEntryById(self._schEntryId)

        if self._direction:
            sched.moveUpEntry(schEntry)
        else:
            sched.moveDownEntry(schEntry)

        return schedule.ScheduleToJson.process(sched, self._conf.getTimezone(), None,
                                               days = [ schEntry.getAdjustedStartDate() ],
                                               mgmtMode = True)


class ConferenceTimetableMoveEntryUpDown(MoveEntryUpDown, conferenceServices.ConferenceModifBase):

    def _checkParams(self):
        conferenceServices.ConferenceModifBase._checkParams(self)
        MoveEntryUpDown._checkParams(self)

class SessionSlotTimetableMoveEntryUpDown(MoveEntryUpDown, sessionServices.SessionSlotModifCoordinationBase):

    def _checkParams(self):
        sessionServices.SessionSlotModifBase._checkParams(self)
        MoveEntryUpDown._checkParams(self)

class SessionTimetableMoveEntryUpDown(MoveEntryUpDown, sessionServices.SessionModifCoordinationBase):

    def _checkParams(self):
        sessionServices.SessionModifCoordinationBase._checkParams(self)
        MoveEntryUpDown._checkParams(self)


class EditRoomLocationBase(ScheduleOperation, LocationSetter):
    def _checkParams(self):
        self.pManager = ParameterManager(self._params)
        self._roomInfo = self.pManager.extract("roomInfo", pType=dict, allowEmpty=True)
        self._isSessionTimetable = self.pManager.extract("sessionTimetable", pType=bool, allowEmpty=True)

    def _performOperation(self):
        self._entry.setRoom(None)
        self._entry.setLocation(None)
        self._setLocationInfo(self._entry)
        entryId, pickledData = schedule.ScheduleToJson.processEntry(self._schEntry, self._conf.getTimezone(),
                                                                        None, mgmtMode = True)

        return {'day': self._schEntry.getAdjustedStartDate().strftime("%Y%m%d"),
                'id': entryId,
                'entry': pickledData,
                'autoOps': translateAutoOps(self.getAutoOps())}


class EventEditRoomLocation(EditRoomLocationBase, conferenceServices.ConferenceScheduleModifBase):

    def _checkParams(self):
        conferenceServices.ConferenceScheduleModifBase._checkParams(self)
        EditRoomLocationBase._checkParams(self)
        self._entry = self._schEntry

class SessionEditRoomLocation(EditRoomLocationBase, sessionServices.SessionModifUnrestrictedTTCoordinationBase):

    def _checkParams(self):
        sessionServices.SessionModifUnrestrictedTTCoordinationBase._checkParams(self)
        EditRoomLocationBase._checkParams(self)
        if not hasattr(self, "_slot"):
            self._slot = self._session.slots[self._params["slot"]]
        if not hasattr(self, "_schEntry"):
            if self._params.get("sessionTimetable", False):
                self._schEntry = self._slot._sessionSchEntry
            else:
                self._schEntry = self._slot._confSchEntry
        self._entry = self._slot

class SessionSlotEditRoomLocation(EditRoomLocationBase, sessionServices.SessionSlotModifCoordinationBase):

    def _checkParams(self):
        sessionServices.SessionSlotModifCoordinationBase._checkParams(self)
        EditRoomLocationBase._checkParams(self)
        self._entry = self._schEntry

    def _performOperation(self):
        result = EditRoomLocationBase._performOperation(self)
        pickledDataSlotSchEntry = fossilize(self._slot.getConfSchEntry(), tz=self._conf.getTimezone())
        pickledDataSession = fossilize(self._session, tz=self._conf.getTimezone())
        result.update({'slotEntry': pickledDataSlotSchEntry,
                       'session': pickledDataSession})

        return result


class SessionGetExportPopup(conferenceServices.ConferenceDisplayBase):

    def _checkParams(self):
        conferenceServices.ConferenceDisplayBase._checkParams(self)
        pm = ParameterManager(self._params)
        sessionId = pm.extract("sessionId", str, False, "")
        self._session = self._conf.getSessionById(sessionId)

    def _getAnswer(self):
        return WSessionICalExport( self._session, self._getUser() ).getHTML().replace("\n","")

class SessionExportURLs(conferenceServices.ConferenceDisplayBase, base.ExportToICalBase):

    def _checkParams(self):
        conferenceServices.ConferenceDisplayBase._checkParams(self)
        base.ExportToICalBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._sessionId = pm.extract("sessionId", str, False, "")

    def _getAnswer(self):
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()

        return generate_public_auth_request(self._apiMode, self._apiKey, '/export/event/%s/session/%s.ics'%(self._target.getId(), self._sessionId), {}, minfo.isAPIPersistentAllowed() and self._apiKey.isPersistentAllowed(), minfo.isAPIHTTPSRequired())


class ContributionGetExportPopup(conferenceServices.ConferenceDisplayBase):

    def _checkParams(self):
        conferenceServices.ConferenceDisplayBase._checkParams(self)
        pm = ParameterManager(self._params)
        contribId = pm.extract("contribId", str, False, "")
        self._contribution = self._conf.getContributionById(contribId)

    def _getAnswer(self):
        return WContributionICalExport( self._contribution, self._getUser() ).getHTML().replace("\n","")

class ContributionExportURLs(conferenceServices.ConferenceDisplayBase, base.ExportToICalBase):

    def _checkParams(self):
        conferenceServices.ConferenceDisplayBase._checkParams(self)
        base.ExportToICalBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._contribId = pm.extract("contribId", str, False, "")

    def _getAnswer(self):
        result = {}

        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()

        urls = generate_public_auth_request(self._apiMode, self._apiKey, '/export/event/%s/contribution/%s.ics'%(self._target.getId(), self._contribId), {}, minfo.isAPIPersistentAllowed() and self._apiKey.isPersistentAllowed(), minfo.isAPIHTTPSRequired())
        result["publicRequestURL"] = urls["publicRequestURL"]
        result["authRequestURL"] =  urls["authRequestURL"]

        return result

methodMap = {
    "get": ConferenceGetSchedule,

    "event.addContribution": ConferenceScheduleAddContribution,
    "event.editContribution": ConferenceScheduleEditContribution,
    "event.addSession": ConferenceScheduleAddSession,
    "event.addBreak": ConferenceScheduleAddBreak,
    "event.editBreak": ConferenceScheduleEditBreak,
    "event.modifyStartEndDate": ConferenceScheduleModifyStartEndDate,
    "event.deleteContribution": ConferenceScheduleDeleteContribution,
    "event.deleteSession": ConferenceScheduleDeleteSession,
    "event.deleteBreak": ConferenceScheduleDeleteBreak,
    "event.getDayEndDate": ConferenceScheduleGetDayEndDate,
    "event.getUnscheduledContributions": ConferenceGetUnscheduledContributions,
    "event.scheduleContributions": ConferenceScheduleContributions,
    "event.moveEntry": MoveEntry,

    "slot.addContribution": SessionSlotScheduleAddContribution,
    "slot.editContribution": SessionSlotScheduleEditContribution,
    "slot.addBreak": SessionSlotScheduleAddBreak,
    "slot.editBreak": SessionSlotScheduleEditBreak,
    "slot.deleteContribution": SessionSlotScheduleDeleteContribution,
    "slot.deleteBreak": SessionSlotScheduleDeleteBreak,
    "slot.getDayEndDate": SessionSlotScheduleGetDayEndDate,
    "slot.getBooking": SessionSlotGetBooking,
    "slot.getFossil": SessionSlotGetFossil,
    "slot.modifyStartEndDate": SessionSlotScheduleModifyStartEndDate,
    "slot.moveEntry": MoveEntryFromSessionBlock,

    "session.getDayEndDate": SessionScheduleGetDayEndDate,
    "session.addSlot": SessionScheduleAddSessionSlot,
    "session.editSlot": SessionScheduleEditSessionSlot,
    "session.editSlotById": SessionScheduleEditSessionSlotById,
    "session.deleteSlot": SessionScheduleDeleteSessionSlot,
    "session.changeColors": SessionScheduleChangeSessionColors,
    "session.modifyStartEndDate": SessionScheduleModifyStartEndDate,


    "session.getUnscheduledContributions": SessionGetUnscheduledContributions,
    "slot.scheduleContributions": SessionSlotScheduleContributions,

    "break.getBooking": BreakGetBooking,

    "setSessionSlots": ConferenceSetSessionSlots,
    "setScheduleSessions": ConferenceSetScheduleSessions,

    "getAllSessionConveners": ConferenceGetAllConveners,
    "getAllSpeakers": ConferenceGetAllSpeakers,

    "event.moveEntryUpDown": ConferenceTimetableMoveEntryUpDown,
    "session.moveEntryUpDown": SessionTimetableMoveEntryUpDown,
    "slot.moveEntryUpDown": SessionSlotTimetableMoveEntryUpDown,

    "event.editRoomLocation": EventEditRoomLocation,
    "session.editRoomLocation": SessionEditRoomLocation,
    "slot.editRoomLocation": SessionSlotEditRoomLocation,

    "api.getSessionExportPopup": SessionGetExportPopup,
    "api.getSessionExportURLs": SessionExportURLs,
    "api.getContribExportPopup": ContributionGetExportPopup,
    "api.getContribExportURLs": ContributionExportURLs
}
