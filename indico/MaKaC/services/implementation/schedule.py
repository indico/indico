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

import datetime, pytz

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

class ScheduleAddContribution(LocationSetter):

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

        self._roomInfo = self._pManager.extract("roomInfo", pType=dict)
        self._keywords = self._pManager.extract("keywords", pType=list,
                                          allowEmpty=True)
        self._needsToBeScheduled = self._params.get("schedule", True)
        if self._needsToBeScheduled:
            self._dateTime = self._pManager.extract("dateTime", pType=datetime.datetime)

        self._duration = self._pManager.extract("duration", pType=int)
        self._title = self._pManager.extract("title", pType=str)
        self._fields = {}

        for field in self._target.getConference().getAbstractMgr().getAbstractFieldsMgr().getFields():
            self._fields[field.getId()] = self._pManager.extract("field_%s"%field.getId(), pType=str,
                                                     allowEmpty=True, defaultValue='')
        self._privileges = self._pManager.extract("privileges", pType=dict,
                                                  allowEmpty=True)

    def _getAnswer(self):

        contribution = conference.Contribution()

        self._addToParent(contribution)

        contribution.setTitle(self._title)
        contribution.setKeywords('\n'.join(self._keywords))
        if self._needsToBeScheduled:
            contribution.setStartDate(setAdjustedDate(self._dateTime, self._conf))
        contribution.setDuration(self._duration/60, self._duration%60)

        for field, value in self._fields.iteritems():
            contribution.setField(field, value)

        if (self._target.getConference().getType() == "conference"):
            # for conferences, add authors and coauthors
            self.__addPeople(contribution, self._pManager, "author", conference.Contribution.addPrimaryAuthor)
            self.__addPeople(contribution, self._pManager, "coauthor", conference.Contribution.addCoAuthor)

        self.__addPeople(contribution, self._pManager, "presenter", conference.Contribution.newSpeaker)

        self._setLocationInfo(contribution)

        schEntry = contribution.getSchEntry()
        pickledData = DictPickler.pickle(schEntry, timezone=self._conf.getTimezone())
        return {'day': schEntry.getAdjustedStartDate().strftime("%Y%m%d"),
                'id': pickledData['id'],
                'entry': pickledData}


class ConferenceScheduleAddContribution(ScheduleAddContribution, conferenceServices.ConferenceModifBase):

    def _checkParams(self):
        conferenceServices.ConferenceModifBase._checkParams(self)
        ScheduleAddContribution._checkParams(self)

    def _addToParent(self, contribution):
        self._target.addContribution( contribution )
        contribution.setParent(self._target)

        # 'check' param = 1 - dates will be checked for errors
        if self._needsToBeScheduled:
            self._target.getSchedule().addEntry(contribution.getSchEntry(),1)

class SessionSlotScheduleAddContribution(ScheduleAddContribution, sessionServices.SessionSlotModifBase):

    def _checkParams(self):
        sessionServices.SessionSlotModifBase._checkParams(self)
        ScheduleAddContribution._checkParams(self)

    def _addToParent(self, contribution):
        self._session.addContribution( contribution )
        contribution.setParent(self._session.getConference())

        self._slot.getSchedule().addEntry(contribution.getSchEntry())

class ConferenceScheduleAddSession(conferenceServices.ConferenceModifBase, LocationSetter):

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

        self._roomInfo = pManager.extract("roomInfo", pType=dict)
        self._conveners = pManager.extract("conveners", pType=list,
                                           allowEmpty=True)
        self._startDateTime = pManager.extract("startDateTime",
                                               pType=datetime.datetime)
        self._endDateTime = pManager.extract("endDateTime",
                                             pType=datetime.datetime)
        self._title = pManager.extract("title", pType=str)
        self._textColor = pManager.extract("textColor", pType=str)
        self._bgColor = pManager.extract("bgColor", pType=str)
        self._description = pManager.extract("description", pType=str,
                                          allowEmpty=True)
        self._scheduleType = pManager.extract("sessionType", pType=str,
                                          allowEmpty=False)

    def _getAnswer(self):
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
                'session': DictPickler.pickle(session, timezone=self._conf.getTimezone())}

class ConferenceScheduleDeleteSession(conferenceServices.ConferenceScheduleModifBase):

    def _getAnswer(self):
        sessionSlot = self._schEntry.getOwner()
        session = sessionSlot.getSession()

        logInfo = self._target.getLogInfo()
        logInfo["subject"] = "Deleted session: %s"%self._target.getTitle()
        self._conf.getLogHandler().logAction(logInfo,"Timetable/Session",self._getUser())

        self._conf.removeSession(session)

class ConferenceScheduleDeleteContribution(conferenceServices.ConferenceScheduleModifBase):

    def _getAnswer(self):

        contrib = self._schEntry.getOwner()
        logInfo = contrib.getLogInfo()

        if self._conf.getType() == "meeting":
            logInfo["subject"] =  _("Deleted contribution: %s")%contrib.getTitle()
            contrib.delete()
        else:
            logInfo["subject"] =  _("Unscheduled contribution: %s")%contrib.getTitle()
        self._conf.getLogHandler().logAction(logInfo,"Timetable/Contribution",self._getUser())

        self._conf.getSchedule().removeEntry(self._schEntry)

class SessionScheduleDeleteSessionSlot(sessionServices.SessionSlotModifBase):

    def _getAnswer(self):
        self._session.removeSlot(self._target)

class SessionScheduleChangeSessionColors(sessionServices.SessionModifBase):

    def _checkParams(self):
        sessionServices.SessionModifBase._checkParams(self)

        try:
            self._bgColor = self._params["bgColor"]
            self._textColor = self._params["textColor"]
        except:
            raise ServiceError("ERR-S4", "Color parameters not provided.")

    def _getAnswer(self):
        self._session.setBgColor(self._bgColor)
        self._session.setTextColor(self._textColor)

class ScheduleEditBreakBase(LocationSetter):

    def _checkParams(self):

        pManager = ParameterManager(self._params, timezone = self._conf.getTimezone())

        self._roomInfo = pManager.extract("roomInfo", pType=dict)
        self._dateTime = pManager.extract("startDate", pType=datetime.datetime)
        self._duration = pManager.extract("duration", pType=int)
        self._title = pManager.extract("title", pType=str)
        self._description = pManager.extract("description", pType=str,
                                          allowEmpty=True)

    def _getAnswer(self):

        self._brk.setValues({"title": self._title or "",
                       "description": self._description or "",
                       "startDate": self._dateTime,
                       "durMins": str(self._duration),
                       "durHours": "0"},
                       check = 2,
                       tz = self._conf.getTimezone())

        self._setLocationInfo(self._brk)

        self._addToSchedule(self._brk)

        pickledData = DictPickler.pickle(self._brk, timezone=self._conf.getTimezone())
        return {'day': self._brk.getAdjustedStartDate().strftime("%Y%m%d"),
                'id': pickledData['id'],
                'entry': pickledData}

class ConferenceScheduleAddBreak(ScheduleEditBreakBase, conferenceServices.ConferenceModifBase):

    def _checkParams(self):
        conferenceServices.ConferenceModifBase._checkParams(self)
        ScheduleEditBreakBase._checkParams(self)
        self._brk = schedule.BreakTimeSchEntry()

    def _addToSchedule(self, b):
        self._target.getSchedule().addEntry(b, 2)

class ConferenceScheduleEditBreak(ScheduleEditBreakBase, conferenceServices.ConferenceScheduleModifBase):

    def _checkParams(self):
        conferenceServices.ConferenceScheduleModifBase._checkParams(self)
        ScheduleEditBreakBase._checkParams(self)
        self._brk = self._schEntry

    def _addToSchedule(self, b):
        pass

class ConferenceScheduleDeleteBreak(conferenceServices.ConferenceScheduleModifBase):

    def _getAnswer(self):
        self._conf.getSchedule().removeEntry(self._schEntry)

class SessionSlotScheduleAddBreak(ScheduleEditBreakBase, sessionServices.SessionSlotModifBase):

    def _checkParams(self):
        sessionServices.SessionSlotModifBase._checkParams(self)
        ScheduleEditBreakBase._checkParams(self)
        self._brk = schedule.BreakTimeSchEntry()

    def _addToSchedule(self, b):
        self._slot.getSchedule().addEntry(b, 2)
        
class SessionSlotScheduleEditBreak(ScheduleEditBreakBase, sessionServices.SessionSlotScheduleModifBase):

    def _checkParams(self):
        sessionServices.SessionSlotScheduleModifBase._checkParams(self)
        ScheduleEditBreakBase._checkParams(self)
        self._brk = self._schEntry

    def _addToSchedule(self, b):
        pass

class SessionSlotScheduleDeleteBreak(sessionServices.SessionSlotScheduleModifBase):

    def _checkParams(self):
        sessionServices.SessionSlotScheduleModifBase._checkParams(self)

    def _getAnswer(self):
        self._slot.getSchedule().removeEntry(self._schEntry)

class SessionSlotScheduleDeleteContribution(sessionServices.SessionSlotScheduleModifBase):

    def _checkParams(self):
        sessionServices.SessionSlotScheduleModifBase._checkParams(self)

    def _getAnswer(self):

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


class SessionSlotScheduleModifyStartEndDate(sessionServices.SessionSlotScheduleModifBase):

    def _checkParams(self):
        sessionServices.SessionSlotScheduleModifBase._checkParams(self)

        pManager = ParameterManager(self._params, timezone = self._conf.getTimezone())

        self._startDate = pManager.extract("startDate", pType=datetime.datetime)
        self._endDate = pManager.extract("endDate", pType=datetime.datetime)

    def _getAnswer(self):
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
                'session': pickledDataSession}


class ConferenceScheduleModifyStartEndDate(conferenceServices.ConferenceScheduleModifBase):

    def _checkParams(self):
        conferenceServices.ConferenceScheduleModifBase._checkParams(self)

        pManager = ParameterManager(self._params, timezone = self._conf.getTimezone())

        self._startDate = pManager.extract("startDate", pType=datetime.datetime)
        self._endDate = pManager.extract("endDate", pType=datetime.datetime)

    def _getAnswer(self):
        self._schEntry.setStartDate(self._startDate);
        duration = self._endDate - self._startDate
        self._schEntry.setDuration(dur=duration)

        pickledData = DictPickler.pickle(self._schEntry, timezone=self._conf.getTimezone())
        return {'day': self._schEntry.getAdjustedStartDate().strftime("%Y%m%d"),
                'id': pickledData['id'],
                'entry': pickledData}

class ConferenceScheduleGetDayEndDate(conferenceServices.ConferenceModifBase):

    def _checkParams(self):
        conferenceServices.ConferenceModifBase._checkParams(self)
        pManager = ParameterManager(self._params)

        date = pManager.extract("date", pType=datetime.date)
        self._date = datetime.datetime(date.year, date.month, date.day, tzinfo=pytz.timezone(self._conf.getTimezone()))

    def _getAnswer(self):
        return self._target.getSchedule().calculateDayEndDate(self._date).strftime('%d/%m/%Y %H:%M')

class SessionSlotScheduleGetDayEndDate(sessionServices.SessionSlotModifBase):

    def _checkParams(self):
        sessionServices.SessionSlotModifBase._checkParams(self)
        pManager = ParameterManager(self._params)
        date = pManager.extract("date", pType=datetime.date)
        self._date = datetime.datetime(date.year, date.month, date.day, tzinfo=pytz.timezone(self._conf.getTimezone()))

    def _getAnswer(self):
        eDate = self._slot.getSchedule().calculateDayEndDate(self._date)
        return eDate.strftime('%d/%m/%Y %H:%M')

class SessionSlotGetBooking(sessionServices.SessionSlotDisplayBase, roomBooking.GetBookingBase):
    def _getAnswer(self):
        return self._getRoomInfo(self._target)


class SessionScheduleGetDayEndDate(sessionServices.SessionModifBase):

    def _checkParams(self):
        sessionServices.SessionModifBase._checkParams(self)
        pManager = ParameterManager(self._params)

        date = pManager.extract("date", pType=datetime.date)
        self._date = datetime.datetime(date.year, date.month, date.day)

    def _getAnswer(self):
        eDate = self._target.getSchedule().calculateDayEndDate(self._date)
        return eDate.strftime('%d/%m/%Y %H:%M')



class SessionScheduleAddSessionSlot(sessionServices.SessionModifBase, LocationSetter):

    def __addConveners(self, slot):

        for convenerValues in self._conveners:
            convener = conference.SlotChair()
            DictPickler.update(convener, convenerValues)
            slot.addConvener(convener)

    def _checkParams(self):
        sessionServices.SessionModifBase._checkParams(self)
        pManager = ParameterManager(self._params)

        self._startDateTime = pManager.extract("startDateTime",
                                               pType=datetime.datetime)
        self._endDateTime = pManager.extract("endDateTime",
                                             pType=datetime.datetime)
        self._title = pManager.extract("title", pType=str, allowEmpty=True)
        self._conveners = pManager.extract("conveners", pType=list,
                                           allowEmpty=True)
        self._roomInfo = pManager.extract("roomInfo", pType=dict)

    def _getAnswer(self):
        slot = conference.SessionSlot(self._target)

        slot.setValues({"title": self._title or "",
                        "sDate": self._startDateTime,
                        "eDate": self._endDateTime})

        self. __addConveners(slot)
        self._setLocationInfo(slot)

        self._target.addSlot(slot)
        #self._target.fit()

        logInfo = slot.getLogInfo()
        logInfo["subject"] = "Create new slot: %s"%slot.getTitle()
        self._conf.getLogHandler().logAction(logInfo,"Timetable/Contribution",self._getUser())

        schEntry = slot.getConfSchEntry()
        pickledData = DictPickler.pickle(schEntry, timezone=self._conf.getTimezone())
        return {'day': schEntry.getAdjustedStartDate().strftime("%Y%m%d"),
                'id': pickledData['id'],
                'entry': pickledData,
                'session': DictPickler.pickle(slot.getSession(), timezone=self._conf.getTimezone())}

class ConferenceSetTimeConflictSolving( conferenceServices.ConferenceTextModificationBase ):
    """
    Set or unset automatic conflict solving for timetable
    """
    def _handleSet(self):
        if type(self._value) != bool:
            raise ServiceError("ERR-E1", "Invalid value type for property")
        self._target.setAutoSolveConflict(self._value)

    def _handleGet(self):
        return self._target.getAutoSolveConflict()

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


class GetUnscheduledContributions:

    """ Returns the list of unscheduled contributions for the target """

    def _getAnswer(self):
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

class SessionGetUnscheduledContributions(GetUnscheduledContributions, sessionServices.SessionModifBase):

    def _isScheduled(self, contrib):
        return contrib.isScheduled() or \
               isinstance(contrib.getCurrentStatus(),conference.ContribStatusWithdrawn)



class ScheduleContributions:

    """ Schedules the contribution in the timetable of the event"""

    def _checkParams(self):
        pManager = ParameterManager(self._params,
                                    timezone = self._target.getTimezone())

        self._ids = pManager.extract("ids", pType=list, allowEmpty=False)
        date = pManager.extract("date", pType=datetime.date,
                                            allowEmpty=False)

        # convert date to datetime
        self._date = datetime.datetime(*(date.timetuple()[:6]+(0, pytz.timezone(self._target.getTimezone()))))

    def _getAnswer(self):
        entries = []

        for contribId in self._ids:

            contrib = self._getContributionId(contribId)

            self._handlePosterContributions()

            d = self._target.getSchedule().calculateDayEndDate(self._date)
            contrib.setStartDate(d)
            schEntry = contrib.getSchEntry()
            self._target.getSchedule().addEntry(schEntry)

            pickledData = DictPickler.pickle(schEntry, timezone=self._conf.getTimezone())
            entries.append({'day': schEntry.getAdjustedStartDate().strftime("%Y%m%d"),
                            'id': pickledData['id'],
                            'entry': pickledData})
        return entries

class SessionSlotScheduleContributions(ScheduleContributions, sessionServices.SessionSlotModifBase):
    def _checkParams(self):
        sessionServices.SessionSlotModifBase._checkParams(self)
        ScheduleContributions._checkParams(self)

    def _getContributionId(self, contribId):
        return self._target.getSession().getContributionById(contribId)

    def _handlePosterContributions(self):
        if self._slot.getSession().getScheduleType() == "poster":
            contrib.setStartDate(self._slot.getStartDate())

class ConferenceScheduleContributions(ScheduleContributions, conferenceServices.ConferenceModifBase):
    def _checkParams(self):
        conferenceServices.ConferenceModifBase._checkParams(self)
        ScheduleContributions._checkParams(self)

    def _getContributionId(self, contribId):
        return self._target.getContributionById(contribId)

    def _handlePosterContributions(self):
        pass


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
    "session.deleteSlot": SessionScheduleDeleteSessionSlot,
    "session.changeColors": SessionScheduleChangeSessionColors,

    "session.getUnscheduledContributions": SessionGetUnscheduledContributions,
    "slot.scheduleContributions": SessionSlotScheduleContributions,

    "break.getBooking": BreakGetBooking,

    "setTimeConflictSolving": ConferenceSetTimeConflictSolving,
    "setSessionSlots": ConferenceSetSessionSlots,
    "setScheduleSessions": ConferenceSetScheduleSessions,

    "getAllSessionConveners": ConferenceGetAllConveners,
    "getAllSpeakers": ConferenceGetAllSpeakers
}
