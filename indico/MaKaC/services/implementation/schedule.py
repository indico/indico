"""
Schedule-related services
"""

from MaKaC.services.implementation.base import ParameterManager

import MaKaC.conference as conference
import MaKaC.schedule as schedule

from MaKaC.common.PickleJar import DictPickler

from MaKaC.services.interface.rpc.common import ServiceError

from MaKaC.services.implementation import conference as conferenceServices
from MaKaC.services.implementation import base
from MaKaC.services.implementation import roomBooking
from MaKaC.services.implementation import session as sessionServices
from MaKaC.common.timezoneUtils import setAdjustedDate
from MaKaC.common.logger import Logger
from MaKaC.common.utils import getHierarchicalId, formatTime, formatDateTime, parseDate
from MaKaC.common.contextManager import ContextManager
from MaKaC.errors import TimingError

import time, datetime, pytz

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
        return DictPickler.pickle(self._target.getSchedule())

class LocationSetter:
    def _setLocationInfo(self, target):
        room = self._roomInfo.get('room', None)
        address = self._roomInfo.get('address', None)
        location = self._roomInfo.get('location', None)

        if location != None:
            if location.strip()=="":
                target.setLocation(None)
            else:
                loc = target.getOwnLocation()
                if not loc:
                    loc = conference.CustomLocation()
                target.setLocation(loc)
                loc.setName(location)
                loc.setAddress(address)
        #same as for the location
        if room != None:
            if room.strip()=="":
                target.setRoom(None)
            else:
                r = target.getOwnRoom()
                if not r:
                    r = conference.CustomRoom()
                target.setRoom(r)
                r.setName(room)

class ScheduleOperation:
    def _getAnswer(self):

        self.initializeAutoOps()

        try:
            return self._performOperation()
        except TimingError, e:
            raise ServiceError("ERR-E2", e.getMsg())

    def initializeAutoOps(self):
        ContextManager.set('autoOps',[])

    def getAutoOps(self):
        return ContextManager.get('autoOps')


class ScheduleAddContribution(ScheduleOperation, LocationSetter):

    def __addPeople(self, contribution, pManager, elemType, method):
        """ Generic method for adding presenters, authors and
        co-authors. """

        pList = pManager.extract("%ss" % elemType, pType=list,
                                 allowEmpty=True)

        for elemValues in pList:
            element = conference.ContributionParticipation()
            DictPickler.update(element, elemValues)

            # call the appropriate method
            method(contribution, element)

            if self._privileges is not None:
                if self._privileges.get('%s-grant-submission' % elemType, False):
                    contribution.grantSubmission(element)

    def _checkParams(self):

        self._pManager = ParameterManager(self._params)

        self._roomInfo = self._pManager.extract("roomInfo", pType=dict, allowEmpty=True)
        self._keywords = self._pManager.extract("keywords", pType=list,
                                          allowEmpty=True)
        self._boardNumber = self._pManager.extract("boardNumber", pType=str, allowEmpty=True)
        self._needsToBeScheduled = self._params.get("schedule", True)
        if self._needsToBeScheduled:
            self._dateTime = self._pManager.extract("dateTime", pType=datetime.datetime)

        self._duration = self._pManager.extract("duration", pType=int)
        self._title = self._pManager.extract("title", pType=str)
        self._fields = {}

        for field in self._target.getConference().getAbstractMgr().getAbstractFieldsMgr().getFields():
            self._fields[field.getId()] = self._pManager.extract("field_%s"%field.getId(), pType=str,
                                                     allowEmpty=True, defaultValue='')
        self._privileges = self._pManager.extract("privileges", pType=dict,                                                  allowEmpty=True)
        self._contribTypeId = self._pManager.extract("type", pType=str, allowEmpty=True)

    def _performOperation(self):

        contribution = conference.Contribution()

        self._addToParent(contribution)

        contribution.setTitle(self._title)
        contribution.setKeywords('\n'.join(self._keywords))

        contribution.setBoardNumber(self._boardNumber)
        contribution.setDuration(self._duration/60, self._duration%60)

        if self._needsToBeScheduled:
            adjDate = setAdjustedDate(self._dateTime, self._conf)
            contribution.setStartDate(adjDate)

        self._schedule(contribution)

        for field, value in self._fields.iteritems():
            contribution.setField(field, value)

        if (self._target.getConference().getType() == "conference"):
            # for conferences, add authors and coauthors
            self.__addPeople(contribution, self._pManager, "author", conference.Contribution.addPrimaryAuthor)
            self.__addPeople(contribution, self._pManager, "coauthor", conference.Contribution.addCoAuthor)
            # and also set type if it exists
            if (self._contribTypeId):
                contribution.setType(self._target.getConference().getContribTypeById(self._contribTypeId))


        self.__addPeople(contribution, self._pManager, "presenter", conference.Contribution.newSpeaker)

        self._setLocationInfo(contribution)

        schEntry = contribution.getSchEntry()
        pickledData = DictPickler.pickle(schEntry, timezone=self._conf.getTimezone())
        pickledDataSlotSchEntry = self._getSlotEntry()

        result = {'id': pickledData['id'],
                'entry': pickledData,
                'slotEntry': pickledDataSlotSchEntry,
                'autoOps': translateAutoOps(self.getAutoOps())}

        if self._needsToBeScheduled:
            result['day'] = schEntry.getAdjustedStartDate().strftime("%Y%m%d")

        return result


class ConferenceScheduleAddContribution(ScheduleAddContribution, conferenceServices.ConferenceModifBase):

    def _checkParams(self):
        conferenceServices.ConferenceModifBase._checkParams(self)
        ScheduleAddContribution._checkParams(self)

    def _addToParent(self, contribution):
        self._target.addContribution( contribution )
        contribution.setParent(self._target)

    def _schedule(self, contribution):
        # 'check' param = 1 - dates will be checked for errors
        if self._needsToBeScheduled:
            self._target.getSchedule().addEntry(contribution.getSchEntry(),1)

    def _getSlotEntry(self):
        return None


class SessionSlotScheduleAddContribution(ScheduleAddContribution, sessionServices.SessionSlotModifCoordinationBase):

    def _checkParams(self):
        sessionServices.SessionSlotModifCoordinationBase._checkParams(self)
        ScheduleAddContribution._checkParams(self)

    def _addToParent(self, contribution):
        self._session.addContribution( contribution )
        contribution.setParent(self._session.getConference())

    def _schedule(self, contribution):
        return  self._slot.getSchedule().addEntry(contribution.getSchEntry())

    def _getSlotEntry(self):
        return DictPickler.pickle(self._slot.getConfSchEntry(), timezone=self._conf.getTimezone())


class ConferenceScheduleAddSession(ScheduleOperation, conferenceServices.ConferenceModifBase, LocationSetter):

    def __addConveners(self, session):

        for convenerValues in self._conveners:

            convener = conference.SessionChair()
            DictPickler.update(convener, convenerValues)

            session.addConvener(convener)
            if convenerValues['email'].strip() != '':
                session._addCoordinatorEmail(convenerValues['email'])
            if convenerValues.has_key("submission") and \
                convenerValues['submission'] :
                session.grantModification(convener)

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

        slot.setTitle(self._subtitle or "")
        slot.setStartDate(session.getStartDate())

        tz = pytz.timezone(self._conf.getTimezone())
        if session.getEndDate().astimezone(tz).date() > session.getStartDate().astimezone(tz).date():
            newEndDate = session.getStartDate().astimezone(tz).replace(hour=23,minute=59).astimezone(timezone('UTC'))
        else:
            newEndDate = session.getEndDate()
        dur = newEndDate - session.getStartDate()
        if dur > datetime.timedelta(days=1):
            dur = datetime.timedelta(days=1)

        slot.setDuration(dur=dur)
        session.addSlot(slot)

        self.__addConveners(session)
        self._setLocationInfo(session)

        logInfo = session.getLogInfo()
        logInfo["subject"] =  _("Create new session: %s")%session.getTitle()
        self._conf.getLogHandler().logAction(logInfo,"Timetable/Session",self._getUser())

        schEntry = slot.getConfSchEntry()
        pickledData = DictPickler.pickle(schEntry, timezone=conf.getTimezone())
        pickledData['entries'] = {}

        return {'day': slot.getAdjustedStartDate().strftime("%Y%m%d"),
                'id': pickledData['id'],
                'entry': pickledData,
                'session': DictPickler.pickle(session, timezone=self._conf.getTimezone()),
                'autoOps': translateAutoOps(self.getAutoOps())}

class ConferenceScheduleDeleteSession(ScheduleOperation, conferenceServices.ConferenceScheduleModifBase):

    def _performOperation(self):
        sessionSlot = self._schEntry.getOwner()
        session = sessionSlot.getSession()

        logInfo = self._target.getLogInfo()
        logInfo["subject"] = "Deleted session: %s"%self._target.getTitle()
        self._conf.getLogHandler().logAction(logInfo,"Timetable/Session",self._getUser())

        self._conf.removeSession(session)

class ConferenceScheduleDeleteContribution(ScheduleOperation, conferenceServices.ConferenceScheduleModifBase):

    def _performOperation(self):

        contrib = self._schEntry.getOwner()
        logInfo = contrib.getLogInfo()

        if self._conf.getType() == "meeting":
            logInfo["subject"] =  _("Deleted contribution: %s")%contrib.getTitle()
            contrib.delete()
        else:
            logInfo["subject"] =  _("Unscheduled contribution: %s")%contrib.getTitle()
        self._conf.getLogHandler().logAction(logInfo,"Timetable/Contribution",self._getUser())

        self._conf.getSchedule().removeEntry(self._schEntry)

class SessionScheduleDeleteSessionSlot(ScheduleOperation, sessionServices.SessionModifUnrestrictedTTCoordinationBase):

    def _performOperation(self):
        self._session.removeSlot(self._slot)

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

    def _performOperation(self):

        self._brk.setValues({"title": self._title or "",
                       "description": self._description or "",
                       "startDate": self._dateTime,
                       "durMins": str(self._duration),
                       "durHours": "0"},
                       check = 2,
                       tz = self._conf.getTimezone())

        self._setLocationInfo(self._brk)

        self._addToSchedule(self._brk)

        pickledDataSlotSchEntry = self._getSlotEntry()
        pickledData = DictPickler.pickle(self._brk, timezone=self._conf.getTimezone())
        return {'day': self._brk.getAdjustedStartDate().strftime("%Y%m%d"),
                'id': pickledData['id'],
                'slotEntry': pickledDataSlotSchEntry,
                'autoOps': translateAutoOps(self.getAutoOps()),
                'entry': pickledData}

class ConferenceScheduleAddBreak(ScheduleEditBreakBase, conferenceServices.ConferenceModifBase):

    def _checkParams(self):
        conferenceServices.ConferenceModifBase._checkParams(self)
        ScheduleEditBreakBase._checkParams(self)
        self._brk = schedule.BreakTimeSchEntry()

    def _addToSchedule(self, b):
        self._target.getSchedule().addEntry(b, 2)

    def _getSlotEntry(self):
        return None


class ConferenceScheduleEditBreak(ScheduleEditBreakBase, conferenceServices.ConferenceScheduleModifBase):

    def _checkParams(self):
        conferenceServices.ConferenceScheduleModifBase._checkParams(self)
        ScheduleEditBreakBase._checkParams(self)
        self._brk = self._schEntry

    def _addToSchedule(self, b):
        pass

    def _getSlotEntry(self):
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
        self._slot.getSchedule().addEntry(b, 2)

    def _getSlotEntry(self):
        return DictPickler.pickle(self._slot.getConfSchEntry(), timezone=self._conf.getTimezone())


class SessionSlotScheduleEditBreak(ScheduleEditBreakBase, sessionServices.SessionSlotModifCoordinationBase):

    def _checkParams(self):
        sessionServices.SessionSlotModifCoordinationBase._checkParams(self)
        ScheduleEditBreakBase._checkParams(self)
        self._brk = self._schEntry

    def _addToSchedule(self, b):
        pass

    def _getSlotEntry(self):
        return DictPickler.pickle(self._slot.getConfSchEntry(), timezone=self._conf.getTimezone())


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

        if type == "meeting":
            logInfo["subject"] = "Deleted contribution: %s" %contrib.getTitle()
            contrib.delete()
        else:
            logInfo["subject"] = "Unscheduled contribution: %s"%contrib.getTitle()

        self._slot.getSchedule().removeEntry(self._schEntry)
        self._conf.getLogHandler().logAction(logInfo,"Timetable/Contribution",self._getUser())
        self._slot.getSchedule().removeEntry(self._schEntry)


class SessionSlotScheduleModifyStartEndDate(ScheduleOperation, sessionServices.SessionSlotModifCoordinationBase):

    def _checkParams(self):
        sessionServices.SessionSlotModifCoordinationBase._checkParams(self)

        pManager = ParameterManager(self._params, timezone = self._conf.getTimezone())

        self._startDate = pManager.extract("startDate", pType=datetime.datetime)
        self._endDate = pManager.extract("endDate", pType=datetime.datetime)

    def _performOperation(self):

        self._schEntry.setStartDate(self._startDate);
        duration = self._endDate - self._startDate
        self._schEntry.setDuration(dur=duration)

        pickledDataEntry = DictPickler.pickle(self._schEntry, timezone=self._conf.getTimezone())
        pickledDataSlotSchEntry = DictPickler.pickle(self._slot.getConfSchEntry(), timezone=self._conf.getTimezone())
        pickledDataSession = DictPickler.pickle(self._session, timezone=self._conf.getTimezone())
        return {'day': self._schEntry.getAdjustedStartDate().strftime("%Y%m%d"),
                'id': pickledDataEntry['id'],
                'entry': pickledDataEntry,
                'slotEntry': pickledDataSlotSchEntry,
                'session': pickledDataSession,
                'autoOps': translateAutoOps(self.getAutoOps())}


class ConferenceScheduleModifyStartEndDate(ScheduleOperation, conferenceServices.ConferenceScheduleModifBase):

    def _checkParams(self):
        conferenceServices.ConferenceScheduleModifBase._checkParams(self)

        pManager = ParameterManager(self._params, timezone = self._conf.getTimezone())

        self._startDate = pManager.extract("startDate", pType=datetime.datetime)
        self._endDate = pManager.extract("endDate", pType=datetime.datetime)

    def _performOperation(self):

        self._schEntry.setStartDate(self._startDate, moveEntries=1);
        duration = self._endDate - self._startDate
        self._schEntry.setDuration(dur=duration)

        entryId, pickledData = schedule.ScheduleToJson.processEntry(self._schEntry, self._conf.getTimezone())
        return {'day': self._schEntry.getAdjustedStartDate().strftime("%Y%m%d"),
                'id': pickledData['id'],
                'entry': pickledData,
                'autoOps': translateAutoOps(self.getAutoOps())}

class SessionScheduleModifyStartEndDate(ScheduleOperation, sessionServices.SessionModifBase):

    def _checkParams(self):
        sessionServices.SessionModifBase._checkParams(self)

        pManager = ParameterManager(self._params, timezone = self._conf.getTimezone())

        self._startDate = pManager.extract("startDate", pType=datetime.datetime)
        self._endDate = pManager.extract("endDate", pType=datetime.datetime)

    def _performOperation(self):
        self._schEntry.setStartDate(self._startDate);
        duration = self._endDate - self._startDate
        self._schEntry.setDuration(dur=duration)

        pickledData = DictPickler.pickle(self._schEntry, timezone=self._conf.getTimezone())
        return {'day': self._schEntry.getAdjustedStartDate().strftime("%Y%m%d"),
                'id': pickledData['id'],
                'entry': pickledData,
                'autoOps': translateAutoOps(self.getAutoOps())}

class ConferenceScheduleGetDayEndDate(ScheduleOperation, conferenceServices.ConferenceModifBase):

    def _checkParams(self):
        conferenceServices.ConferenceModifBase._checkParams(self)
        pManager = ParameterManager(self._params)

        date = pManager.extract("date", pType=datetime.date)
        self._date = datetime.datetime(date.year, date.month, date.day, tzinfo=pytz.timezone(self._conf.getTimezone()))

    def _performOperation(self):
        return self._target.getSchedule().calculateDayEndDate(self._date).strftime('%Y/%m/%d %H:%M')

class SessionSlotScheduleGetDayEndDate(ScheduleOperation, sessionServices.SessionSlotModifCoordinationBase):

    def _checkParams(self):
        sessionServices.SessionSlotModifCoordinationBase._checkParams(self)
        pManager = ParameterManager(self._params)
        date = pManager.extract("date", pType=datetime.date)
        self._date = datetime.datetime(date.year, date.month, date.day, tzinfo=pytz.timezone(self._conf.getTimezone()))

    def _performOperation(self):
        eDate = self._slot.getSchedule().calculateDayEndDate(self._date)
        return eDate.strftime('%Y/%m/%d %H:%M')

class SessionSlotGetBooking(ScheduleOperation, sessionServices.SessionSlotDisplayBase, roomBooking.GetBookingBase):
    def _performOperation(self):
        return self._getRoomInfo(self._target)

class SessionScheduleGetDayEndDate(ScheduleOperation, sessionServices.SessionModifUnrestrictedTTCoordinationBase):

    def _checkParams(self):
        sessionServices.SessionModifUnrestrictedTTCoordinationBase._checkParams(self)
        pManager = ParameterManager(self._params)

        date = pManager.extract("date", pType=datetime.date)
        self._date = datetime.datetime(date.year, date.month, date.day)

    def _performOperation(self):
        eDate = self._target.getSchedule().calculateDayEndDate(self._date)
        return eDate.strftime('%Y/%m/%d %H:%M')

class ScheduleEditSlotBase(ScheduleOperation, LocationSetter):

    def _addConveners(self, slot):
        pass

    def _checkParams(self):
        pManager = ParameterManager(self._params)

        self._startDateTime = pManager.extract("startDateTime",
                                               pType=datetime.datetime)
        self._endDateTime = pManager.extract("endDateTime",
                                             pType=datetime.datetime)
        self._title = pManager.extract("title", pType=str, allowEmpty=True)
        self._conveners = pManager.extract("conveners", pType=list,
                                           allowEmpty=True)
        self._roomInfo = pManager.extract("roomInfo", pType=dict, allowEmpty=True)
        self._isSessionTimetable = pManager.extract("sessionTimetable", pType=bool, allowEmpty=True)

    def _performOperation(self):

        self._slot.setValues({"title": self._title or "",
                        "sDate": self._startDateTime,
                        "eDate": self._endDateTime})

        self. _addConveners(self._slot)
        self._setLocationInfo(self._slot)

        self._addToSchedule()
        #self._target.fit()

        logInfo = self._slot.getLogInfo()
        logInfo["subject"] = "Create new slot: %s"%self._slot.getTitle()
        self._conf.getLogHandler().logAction(logInfo,"Timetable/Contribution",self._getUser())

        if self._isSessionTimetable:
            schEntry = self._slot.getSessionSchEntry()
        else:
            schEntry = self._slot.getConfSchEntry()
        entryId, pickledData = schedule.ScheduleToJson.processEntry(schEntry, self._conf.getTimezone())

        return {'day': schEntry.getAdjustedStartDate().strftime("%Y%m%d"),
                'id': pickledData['id'],
                'entry': pickledData,
                'autoOps': translateAutoOps(self.getAutoOps()),
                'session': DictPickler.pickle(self._slot.getSession(), timezone=self._conf.getTimezone())}

class SessionScheduleAddSessionSlot(ScheduleEditSlotBase, sessionServices.SessionModifUnrestrictedTTCoordinationBase):

    def _checkParams(self):
        sessionServices.SessionModifUnrestrictedTTCoordinationBase._checkParams(self)
        ScheduleEditSlotBase._checkParams(self)
        self._slot = conference.SessionSlot(self._target)

    def _addToSchedule(self):
        self._target.addSlot(self._slot)

    def _addConveners(self, slot):
        for convenerValues in self._conveners:
            convener = conference.SlotChair()
            DictPickler.update(convener, convenerValues)
            slot.addConvener(convener)

class SessionScheduleEditSessionSlot(ScheduleEditSlotBase, sessionServices.SessionModifUnrestrictedTTCoordinationBase):

    def _checkParams(self):
        sessionServices.SessionModifUnrestrictedTTCoordinationBase._checkParams(self)
        ScheduleEditSlotBase._checkParams(self)

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
            for elem in DictPickler.pickle(contribution.getSpeakerList()):
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
            for elem in DictPickler.pickle(session.getConvenerList()):
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

        return DictPickler.pickle(unscheduledList)

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
        date = pManager.extract("date", pType=datetime.date,
                                            allowEmpty=False)

        # convert date to datetime
        self._date = datetime.datetime(*(date.timetuple()[:6]+(0, pytz.timezone(self._target.getTimezone()))))

    def _performOperation(self):

        entries = []

        for contribId in self._ids:

            contrib = self._getContributionId(contribId)

            self._handlePosterContributions(contrib)

            d = self._target.getSchedule().calculateDayEndDate(self._date)

            contrib.setStartDate(d)
            schEntry = contrib.getSchEntry()
            self._target.getSchedule().addEntry(schEntry)

            pickledData = DictPickler.pickle(schEntry, timezone=self._conf.getTimezone())
            pickledDataSlotSchEntry = self._getSlotEntry()

            entries.append({'day': schEntry.getAdjustedStartDate().strftime("%Y%m%d"),
                            'id': pickledData['id'],
                            'entry': pickledData,
                            'slotEntry': pickledDataSlotSchEntry,
                            'autoOps': translateAutoOps(self.getAutoOps())
                            })
        return entries

class SessionSlotScheduleContributions(ScheduleContributions, sessionServices.SessionSlotModifCoordinationBase):
    def _checkParams(self):
        sessionServices.SessionSlotModifCoordinationBase._checkParams(self)
        ScheduleContributions._checkParams(self)

    def _getContributionId(self, contribId):
        return self._target.getSession().getContributionById(contribId)

    def _handlePosterContributions(self, contrib):
        if self._slot.getSession().getScheduleType() == "poster":
            contrib.setStartDate(self._slot.getStartDate())

    def _getSlotEntry(self):
        return DictPickler.pickle(self._slot.getConfSchEntry(), timezone=self._conf.getTimezone())

class ConferenceScheduleContributions(ScheduleContributions, conferenceServices.ConferenceModifBase):
    def _checkParams(self):
        conferenceServices.ConferenceModifBase._checkParams(self)
        ScheduleContributions._checkParams(self)

    def _getContributionId(self, contribId):
        return self._target.getContributionById(contribId)

    def _handlePosterContributions(self, contrib):
        pass

    def _getSlotEntry(self):
        return None

class MoveEntry(ScheduleOperation, conferenceServices.ConferenceModifBase):

    def _checkParams(self):
        conferenceServices.ConferenceModifBase._checkParams(self)

        pManager = ParameterManager(self._params, timezone = self._conf.getTimezone())
        self._contribPlace = pManager.extract("value", pType=str, allowEmpty=False)
        self._schEntryId = pManager.extract("scheduleEntryId", pType=int, allowEmpty=False)
        self._sessionId = pManager.extract("sessionId", pType=str, allowEmpty=True, defaultValue=None)
        self._sessionSlotId = pManager.extract("sessionSlotId", pType=str, allowEmpty=True, defaultValue=None)

    def _performOperation(self):

        if (self._sessionId != None and self._sessionSlotId != None):
            self._schEntry = self._conf.getSessionById(self._sessionId).getSlotById(self._sessionSlotId).getSchedule().getEntryById(self._schEntryId)
        else:
            self._schEntry = self._conf.getSchedule().getEntryById(self._schEntryId)

        owner = self._schEntry.getOwner()

        if self._contribPlace.strip() != "":
            oldSch = DictPickler.pickle(self._schEntry)
            oldDate = self._schEntry.getStartDate()
            oldSch['startDate'] = formatDateTime(oldDate.astimezone(pytz.timezone(owner.getTimezone())))

            #we need something like 20090405
            oldDateConc = oldDate.strftime("%Y%m%d")

            sessionId,sessionSlotId = self._contribPlace.split(":")

            if sessionId != "conf":
                # Moving inside a session
                session = self._conf.getSessionById(sessionId)

                if session is not None:
                    slot = session.getSlotById(sessionSlotId)
                    if slot is not None:
                        pickledDataSession = DictPickler.pickle(session, timezone=self._conf.getTimezone())
                        # unschedule entry from previous place
                        self._schEntry.getSchedule().removeEntry(self._schEntry)
                        if isinstance(owner, conference.Contribution):
                            owner.setSession(session)
                        # add it to new container
                        slot.getSchedule().addEntry(self._schEntry, check=2)
                        pickledDataSlotSchEntry = DictPickler.pickle(slot.getConfSchEntry(), timezone=self._conf.getTimezone())
                    else:
                        raise ServiceError("ERR-S3","Invalid slot ID")
                else:
                    raise ServiceError("ERR-S4","Invalid session ID")
            else:
                # Moving inside the top-level timetable

                pickledDataSlotSchEntry = None
                if isinstance(owner, conference.Contribution):
                    pickledDataSession = DictPickler.pickle(owner.getOwner(), timezone=self._conf.getTimezone())
                else:
                    pickledDataSession = None

                # the target date/time
                parsedDate = parseDate(sessionSlotId, format="%Y%m%d")

                # oldDate is in UTC
                adjustedOldDate = oldDate.astimezone(pytz.timezone(owner.getTimezone()))

                # newStartDate will result in a naive date (but relative to the evt's timezone)
                newStartDate = datetime.datetime.combine(parsedDate, adjustedOldDate.time())
                newStartDate = pytz.timezone(owner.getTimezone()).localize(newStartDate)
                # convert to UTC for storage
                newStartDate = newStartDate.astimezone(pytz.timezone('UTC'))

                self._schEntry.getSchedule().removeEntry(self._schEntry)

                self._schEntry.setStartDate(newStartDate)
                if isinstance(owner, conference.Contribution):
                    owner.setSession(None)
                self._conf.getSchedule().addEntry(self._schEntry, check=2)

        newPickledEntry = DictPickler.pickle(self._schEntry)
        return {'entry': newPickledEntry,
                'old': oldSch,
                'id': newPickledEntry['id'],
                'day': self._schEntry.getAdjustedStartDate().strftime("%Y%m%d"),
                'session': pickledDataSession,
                'slotEntry': pickledDataSlotSchEntry,
                'autoOps': translateAutoOps(self.getAutoOps())}


class MoveEntryUpDown(ScheduleOperation, conferenceServices.ConferenceModifBase):
    def _checkParams(self):
        conferenceServices.ConferenceModifBase._checkParams(self)

        pManager = ParameterManager(self._params, timezone = self._conf.getTimezone())

        self._schEntryId = pManager.extract("scheduleEntryId", pType=int, allowEmpty=False)
        self._sessionId = pManager.extract("sessionId", pType=str, allowEmpty=True, defaultValue=None)
        self._sessionSlotId = pManager.extract("sessionSlotId", pType=str, allowEmpty=True, defaultValue=None)
        self._direction = pManager.extract("direction", pType=bool, allowEmpty=False)

    def _performOperation(self):

        if (self._sessionId != None and self._sessionSlotId != None):

            slot = self._conf.getSessionById(self._sessionId).getSlotById(self._sessionSlotId)
            sched = slot.getSchedule()
        else:
            sched = self._conf.getSchedule()

        schEntry = sched.getEntryById(self._schEntryId)

        if self._direction:
            sched.moveUpEntry(schEntry)
        else:
            sched.moveDownEntry(schEntry)

        return schedule.ScheduleToJson.process(sched, self._conf.getTimezone(), days = [ schEntry.getAdjustedStartDate() ])



methodMap = {
    "get": ConferenceGetSchedule,

    "event.addContribution": ConferenceScheduleAddContribution,
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

    "slot.addContribution": SessionSlotScheduleAddContribution,
    "slot.addBreak": SessionSlotScheduleAddBreak,
    "slot.editBreak": SessionSlotScheduleEditBreak,
    "slot.deleteContribution": SessionSlotScheduleDeleteContribution,
    "slot.deleteBreak": SessionSlotScheduleDeleteBreak,
    "slot.getDayEndDate": SessionSlotScheduleGetDayEndDate,
    "slot.getBooking": SessionSlotGetBooking,
    "slot.modifyStartEndDate": SessionSlotScheduleModifyStartEndDate,

    "session.getDayEndDate": SessionScheduleGetDayEndDate,
    "session.addSlot": SessionScheduleAddSessionSlot,
    "session.editSlot": SessionScheduleEditSessionSlot,
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

    "moveEntry": MoveEntry,
    "moveEntryUpDown": MoveEntryUpDown
}
