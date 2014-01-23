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
Asynchronous request handlers for conference-related data modification.
"""

# 3rd party imports
from email.utils import formataddr
from MaKaC.webinterface.rh.categoryDisplay import UtilsConference
from indico.util.string import permissive_format

import datetime
from pytz import timezone

# legacy indico imports
from MaKaC.i18n import _
from MaKaC import domain, conference as conference

from MaKaC.common import indexes, info, filters, log, timezoneUtils
from MaKaC.common.utils import validMail, setValidEmailSeparators, formatDateTime
from MaKaC.common.url import ShortURLMapper
from MaKaC.common.fossilize import fossilize
from MaKaC.common.contextManager import ContextManager
from MaKaC.common.logger import Logger

from MaKaC.errors import TimingError
from MaKaC.user import PrincipalHolder, Avatar, Group, AvatarHolder
from MaKaC.participant import Participant
from MaKaC.fossils.contribution import IContributionFossil

import MaKaC.webinterface.displayMgr as displayMgr
from MaKaC.webinterface import urlHandlers
from MaKaC.webinterface.rh.reviewingModif import RCReferee, RCPaperReviewManager
from MaKaC.webinterface.common import contribFilters
from MaKaC.webinterface.mail import GenericMailer, GenericNotification
import MaKaC.webinterface.pages.conferences as conferences

from MaKaC.services.implementation.base import ProtectedModificationService, ListModificationBase, ParameterManager, \
    ProtectedDisplayService, ServiceBase, TextModificationBase, HTMLModificationBase, DateTimeModificationBase, ExportToICalBase
from MaKaC.services.interface.rpc.common import ServiceError, ServiceAccessError, Warning, \
        ResultWithWarning, TimingNoReportError, NoReportError


# indico imports
from indico.modules import ModuleHolder
from indico.modules.offlineEvents import OfflineEventItem
from indico.modules.scheduler.tasks.offlineEventGenerator import OfflineEventGeneratorTask
from indico.modules.scheduler import tasks, Client
from indico.util.i18n import i18nformat
from indico.web.http_api.util import generate_public_auth_request
from indico.core.config import Config


class ConferenceBase:
    """
    Base class for conference modification
    """

    def _checkParams(self):

        try:
            self._target = self._conf = conference.ConferenceHolder().getById(self._params["conference"])
        except:
            try:
                self._target = self._conf = conference.ConferenceHolder().getById(self._params["confId"])
            except:
                raise ServiceError("ERR-E4", "Invalid conference id.")
            if self._target is None:
                Logger.get('rpc.conference').debug('self._target is null')
                raise Exception("Null target.")

    def _getCheckFlag(self):
        """
        Returns the "check" flag, a value that specifies what kind of
        checking should be done before modifying. Classes that wish
        to change this behavior should overload it.
        """

        # automatically adapt everything
        return 2


class ConferenceModifBase(ProtectedModificationService, ConferenceBase):
    def _checkParams(self):
        ConferenceBase._checkParams(self)
        ProtectedModificationService._checkParams(self)


class ConferenceScheduleModifBase(ConferenceModifBase):
    def _checkParams(self):
        ConferenceModifBase._checkParams(self)
        if not self._params.has_key("scheduleEntry"):
            raise ServiceError("ERR-E4", "No scheduleEntry id set.")
        self._schEntry = self._conf.getSchedule().getEntryById(self._params["scheduleEntry"])
        if self._schEntry is None:
            raise NoReportError(_("It seems that the entry has been deleted or moved, please refresh the page"))

    def _checkProtection(self):
        self._target = self._schEntry.getOwner()
        ConferenceModifBase._checkProtection(self)


class ConferenceDisplayBase(ProtectedDisplayService, ConferenceBase):

    def _checkParams(self):
        ConferenceBase._checkParams(self)
        ProtectedDisplayService._checkParams(self)


class ConferenceTextModificationBase(TextModificationBase, ConferenceModifBase):
    #Note: don't change the order of the inheritance here!
    pass


class ConferenceHTMLModificationBase(HTMLModificationBase, ConferenceModifBase):
    #Note: don't change the order of the inheritance here!
    pass


class ConferenceDateTimeModificationBase (DateTimeModificationBase, ConferenceModifBase):
    #Note: don't change the order of the inheritance here!
    pass


class ConferenceListModificationBase (ListModificationBase, ConferenceModifBase):
    #Note: don't change the order of the inheritance here!
    pass


class ConferenceTitleModification(ConferenceTextModificationBase):
    """
    Conference title modification
    """
    def _handleSet(self):
        title = self._value
        if (title == ""):
            raise ServiceError("ERR-E2",
                               "The title cannot be empty")
        self._target.setTitle(self._value)

    def _handleGet(self):
        return self._target.getTitle()


class ConferenceDescriptionModification(ConferenceHTMLModificationBase):
    """
    Conference description modification
    """
    def _handleSet(self):
        self._target.setDescription(self._value)

    def _handleGet(self):
        return self._target.getDescription()


class ConferenceAdditionalInfoModification(ConferenceHTMLModificationBase):
    """
    Conference additional info (a.k.a contact info) modification
    """
    def _handleSet(self):
        self._target.setContactInfo(self._value)

    def _handleGet(self):
        return self._target.getContactInfo()


class ConferenceTypeModification(ConferenceTextModificationBase):
    """
    Conference title modification
    """
    def _handleSet(self):
        curType = self._target.getType()
        newType = self._value
        if newType != "" and newType != curType:
            import MaKaC.webinterface.webFactoryRegistry as webFactoryRegistry
            wr = webFactoryRegistry.WebFactoryRegistry()
            factory = wr.getFactoryById(newType)
            wr.registerFactory(self._target, factory)

            styleMgr = info.HelperMaKaCInfo.getMaKaCInfoInstance().getStyleManager()

            dispMgr = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._target)
            dispMgr.setDefaultStyle(styleMgr.getDefaultStyleForEventType(newType))
            self._target._notify('infoChanged')

    def _handleGet(self):
        return self._target.getType()


class ConferenceBookingModification(ConferenceTextModificationBase):
    """
    Conference location name modification
    """
    def _handleSet(self):
        changed = False
        room = self._target.getRoom()
        loc = self._target.getLocation()

        newLocation = self._value.get('location')
        newRoom = self._value.get('room')

        if room is None:
            room = conference.CustomRoom()
            self._target.setRoom(room)

        if room.getName() != newRoom:
            room.setName(newRoom)

            minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
            if minfo.getRoomBookingModuleActive():
                room.retrieveFullName(newLocation)
            else:
                # invalidate full name, as we have no way to know it
                room.fullName = None
            changed = True

        if loc is None:
            loc = conference.CustomLocation()
            self._target.setLocation(loc)

        if loc.getName() != newLocation:
            loc.setName(newLocation)
            changed = True

        loc.setAddress(self._value['address'])

        if changed:
            self._target._notify('placeChanged')

    def _handleGet(self):

        loc = self._target.getLocation()
        room = self._target.getRoom()

        return {'location': loc.getName() if loc else "",
                'room': room.name if room else "",
                'address': loc.getAddress() if loc else ""}


class ConferenceBookingDisplay(ConferenceDisplayBase):
    """
        Conference location
    """
    def _getAnswer(self):
        loc = self._target.getLocation()
        room = self._target.getRoom()
        if loc:
            locName = loc.getName()
            locAddress = loc.getAddress()
        else:
            locName = ''
            locAddress = ''
        if room:
            roomName = room.name
        else:
            roomName = ''

        return {'location': locName,
                'room': roomName,
                'address': locAddress}


class ConferenceShortURLModification(ConferenceTextModificationBase):
    """
    Conference short URL modification
    """
    def _handleSet(self):
        mapper = ShortURLMapper()
        if self._value:
            try:
                UtilsConference.validateShortURL(self._value, self._target)
            except ValueError, e:
                raise NoReportError(e.message)
        mapper.remove(self._target)
        self._target.setUrlTag(self._value)
        if self._value:
            mapper.add(self._value, self._target)

    def _handleGet(self):
        return self._target.getUrlTag()


class ConferenceTimezoneModification(ConferenceTextModificationBase):
    """
    Conference Timezone modification
    """
    def _handleSet(self):
        self._target.setTimezone(self._value)

    def _handleGet(self):
        return self._target.getTimezone()


class ConferenceKeywordsModification(ConferenceTextModificationBase):
    """
    Conference keywords modification
    """
    def _handleSet(self):
        self._target.setKeywords(self._value)

    def _handleGet(self):
        return self._target.getKeywords()


class ConferenceSpeakerTextModification(ConferenceTextModificationBase):
    """ Conference chairman text modification (for conferences and meetings)
    """
    def _handleSet(self):
        self._target.setChairmanText(self._value)

    def _handleGet(self):
        return self._target.getChairmanText()


class ConferenceOrganiserTextModification(ConferenceTextModificationBase):
    """ Conference organiser text modification (for lectures)
    """
    def _handleSet(self):
        self._target.setOrgText(self._value)

    def _handleGet(self):
        return self._target.getOrgText()


class ConferenceSupportModification(ConferenceTextModificationBase):
    """
    Conference support caption and e-mail modification
    """
    def _handleSet(self):
        self._supportInfo = self._target.getSupportInfo()
        caption = self._value.get("caption", "")
        email = self._value.get("email", "")
        phone = self._value.get("telephone", "")

        if caption == "":
            raise ServiceError("ERR-E2", "The caption cannot be empty")
        self._supportInfo.setCaption(caption)

        # handling the case of a list of emails with separators different than ","
        email = setValidEmailSeparators(email)

        if validMail(email) or email == "":
            self._supportInfo.setEmail(email)
        else:
            raise ServiceError('ERR-E0', 'E-mail address %s is not valid!' %
                               self._value)
        self._supportInfo.setTelephone(phone)

    def _handleGet(self):
        return fossilize(self._supportInfo)


class ConferenceDefaultStyleModification(ConferenceTextModificationBase):
    """
    Conference default style modification
    """
    def _handleSet(self):
        dispManReg = displayMgr.ConfDisplayMgrRegistery()
        dispManReg.getDisplayMgr(self._target).setDefaultStyle(self._value)

    def _handleGet(self):
        dispManReg = displayMgr.ConfDisplayMgrRegistery()
        return dispManReg.getDisplayMgr(self._target).getDefaultStyle()


class ConferenceVisibilityModification(ConferenceTextModificationBase):
    """
    Conference visibility modification
    """

    def _handleSet(self):
        try:
            val = int(self._value)
        except ValueError:
            raise ServiceError("ERR-E1", "Invalid value type for property")
        self._target.setVisibility(val)

    def _handleGet(self):
        return self._target.getVisibility()


class ConferenceStartEndDateTimeModification(ConferenceModifBase):
    """
    Conference start date/time modification

    When changing the start date / time, the _setParam method will be called
    by DateTimeModificationBase's _handleSet method.
    The _setParam method will return None (if there are no problems),
    or a Warning object if the event start date change was OK but there were
    side problems, such as an object observing the event start date change
    could not perform its task
    (Ex: a videoconference booking could not be moved in time according with
    the conference's time change)
    For this, it will check the 'dateChangeNotificationProblems' context variable.
    """

    def _checkParams(self):
        ConferenceModifBase._checkParams(self)

        pm = ParameterManager(self._params.get('value'), timezone=self._conf.getTimezone())

        try:
            self._startDate = pm.extract('startDate', pType=datetime.datetime)
            self._endDate = pm.extract('endDate', pType=datetime.datetime)
        except ValueError, e:
            raise NoReportError("Warning", e.message)
        self._shiftTimes = pm.extract('shiftTimes', pType=bool)

    def _getAnswer(self):

        ContextManager.set('dateChangeNotificationProblems', {})

        if (self._shiftTimes):
            moveEntries = 1
        else:
            moveEntries = 0

        # first sanity check
        if (self._startDate > self._endDate):
            raise ServiceError("ERR-E3",
                               "Date/time of start cannot "
                               "be greater than date/time of end")

        # catch TimingErrors that can be returned by the algorithm
        try:
            self._target.setDates(self._startDate,
                                  self._endDate,
                                  moveEntries=moveEntries)
        except TimingError, e:
            raise TimingNoReportError(e.getMessage(),
                                      title=_("Cannot set event dates"),
                                      explanation=e.getExplanation())

        dateChangeNotificationProblems = ContextManager.get('dateChangeNotificationProblems')

        if dateChangeNotificationProblems:

            warningContent = []
            for problemGroup in dateChangeNotificationProblems.itervalues():
                warningContent.extend(problemGroup)

            w = Warning(_('Warning'), [_('The start date of your event was changed correctly. '
                                       'However, there were the following problems:'),
                                       warningContent])

            return ResultWithWarning(self._params.get('value'), w).fossilize()

        else:
            return self._params.get('value')


class ConferenceListUsedRooms(ConferenceDisplayBase):
    """
    Get rooms that are used in the context of the conference:
     * Booked in CRBS
     * Already chosen in sessions
    """
    def _getAnswer(self):
        """
        Calls _handle() on the derived classes, in order to make it happen. Provides
        them with self._value.
        """
        roomList = []
        roomList.extend(self._target.getRoomList())
        roomList.extend(map(lambda x: x._getName(), self._target.getBookedRooms()))

        return roomList


class ConferenceDateTimeEndModification(ConferenceDateTimeModificationBase):
    """ Conference end date/time modification
        When changing the end date / time, the _setParam method will be called by DateTimeModificationBase's _handleSet method.
        The _setParam method will return None (if there are no problems),
        or a FieldModificationWarning object if the event start date change was OK but there were side problems,
        such as an object observing the event start date change could not perform its task
        (Ex: a videoconference booking could not be moved in time according with the conference's time change)
    """
    def _setParam(self):

        ContextManager.set('dateChangeNotificationProblems', {})

        if (self._pTime < self._target.getStartDate()):
            raise ServiceError("ERR-E3",
                               "Date/time of end cannot " +
                               "be lower than data/time of start")
        self._target.setDates(self._target.getStartDate(),
                              self._pTime.astimezone(timezone("UTC")),
                              moveEntries=0)

        dateChangeNotificationProblems = ContextManager.get('dateChangeNotificationProblems')

        if dateChangeNotificationProblems:
            warningContent = []
            for problemGroup in dateChangeNotificationProblems.itervalues():
                warningContent.extend(problemGroup)

            return Warning(_('Warning'), [_('The end date of your event was changed correctly.'),
                                          _('However, there were the following problems:'),
                                          warningContent])
        else:
            return None

    def _handleGet(self):
        return datetime.datetime.strftime(self._target.getAdjustedEndDate(),
                                          '%d/%m/%Y %H:%M')


class ConferenceListSessions (ConferenceListModificationBase):
    """ Returns a dictionary of all the Sessions within the current Conference,
        ordered by index only """

    def _getAnswer(self):
        sessions = self._conf.getSessionList()
        result = {}

        for sess in sessions:
            for slot in sess.getSortedSlotList():
                time = " (" + formatDateTime(slot.getAdjustedStartDate(), format="dd MMM yyyy HH:mm") + ")"
                result["s"+sess.getId()+"l"+slot.getId()] = sess.getTitle() + (" - " + slot.getTitle() if slot.getTitle() else "") + time

        return result


class ConferenceListContributions (ConferenceListModificationBase):
    """ Returns a dictionary of all the Contributions within the current Conference,
        if the Contribution is part of a Session, the Session name is appended
        to the name of the Contribution in parenthesis """

    def _getAnswer(self):
        contributions = self._conf.getContributionList()
        result = {}
        for cont in contributions:
            session = (" (" + cont.getSession().getTitle() + ")") if (cont.getSession() is not None) else ""
            time = " (" + formatDateTime(cont.getAdjustedStartDate(), format="dd MMM yyyy HH:mm") + ")"
            result[cont.getId()] = cont.getTitle() + session + time

        return result


class ConferenceListContributionsReview (ConferenceListModificationBase):
    """ Returns a list of all contributions of a conference, ordered by id
    """

    def _checkParams(self):
        ConferenceListModificationBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._selTypes = pm.extract("selTypes", pType=list, allowEmpty=True, defaultValue=[])  # ids of selected types
        self._selTracks = pm.extract("selTracks", pType=list, allowEmpty=True, defaultValue=[])  # ids of selected tracks
        self._selSessions = pm.extract("selSessions", pType=list, allowEmpty=True, defaultValue=[])  # ids of selected sessions

        self._typeShowNoValue = self._params.get("typeShowNoValue", True)
        self._trackShowNoValue = self._params.get("trackShowNoValue", True)
        self._sessionShowNoValue = self._params.get("sessionShowNoValue", True)

        self._showWithoutTeam = self._params.get("showWithoutTeam", True)
        self._showWithReferee = self._params.get("showWithReferee", False)
        self._showWithEditor = self._params.get("showWithEditor", False)
        self._showWithReviewer = self._params.get("showWithReviewer", False)

        self._showWithMaterial = self._params.get("showWithMaterial", False)
        self._showWithoutMaterial = self._params.get("showWithoutMaterial", False)

    def _checkProtection(self):
        if not RCPaperReviewManager.hasRights(self) and not RCReferee.hasRights(self):
            ProtectedModificationService._checkProtection(self)

    def _handleGet(self):
        contributions = self._conf.getContributionList()

        filter = {}

        #filtering if the active user is a referee: he can only see his own contribs
        isOnlyReferee = RCReferee.hasRights(self) \
            and not RCPaperReviewManager.hasRights(self) \
            and not self._conf.canModify(self.getAW())

        # We want to make an 'or', not an 'and' of the reviewing assign status

        filter["reviewing"] = {}
        if isOnlyReferee:
            filter["reviewing"]["referee"] = self._getUser()
        elif self._showWithReferee:
            filter["reviewing"]["referee"] = "any"
        if self._showWithEditor:
            filter["reviewing"]["editor"] = "any"
        if self._showWithReviewer:
            filter["reviewing"]["reviewer"] = "any"

        filter["type"] = self._selTypes
        filter["track"] = self._selTracks
        filter["session"] = self._selSessions

        filter["materialsubmitted"] = self._showWithMaterial

        filterCrit = ContributionsReviewingFilterCrit(self._conf, filter)
        sortingCrit = contribFilters.SortingCriteria(["number"])

        filterCrit.getField("type").setShowNoValue(self._typeShowNoValue)
        filterCrit.getField("track").setShowNoValue(self._trackShowNoValue)
        filterCrit.getField("session").setShowNoValue(self._sessionShowNoValue)

        filterCrit.getField("reviewing").setShowNoValue(self._showWithoutTeam)
        filterCrit.getField("materialsubmitted").setShowNoValue(self._showWithoutMaterial)

        f = filters.SimpleFilter(filterCrit, sortingCrit)
        contributions = f.apply(contributions)

        return fossilize(contributions, IContributionFossil)


class ConferenceDeleteContributions (ConferenceModifBase):
    """ Deletes a list of all contributions of a conference
    """

    def _checkParams(self):
        ConferenceModifBase._checkParams(self)
        self._selectedContributions = self._params.get('contributions', [])

    def _getAnswer(self):
        for contribId in self._selectedContributions:
            contrib = self._conf.getContributionById(contribId)
            if contrib.getSession() is not None and contrib.getSession().isClosed():
                raise ServiceAccessError(_("""The contribution "%s" cannot be deleted because it is inside of the session "%s" that is closed""") % (contrib.getId(), contrib.getSession().getTitle()))
            contrib.getParent().getSchedule().removeEntry(contrib.getSchEntry())
            self._conf.removeContribution(contrib)

#########################
# Contribution filtering
#########################


class ContributionsReviewingFilterCrit(filters.FilterCriteria):
    _availableFields = {
        contribFilters.RefereeFilterField.getId(): contribFilters.RefereeFilterField,
        contribFilters.EditorFilterField.getId(): contribFilters.EditorFilterField,
        contribFilters.ReviewerFilterField.getId(): contribFilters.ReviewerFilterField,
        contribFilters.TypeFilterField.getId(): contribFilters.TypeFilterField,
        contribFilters.TrackFilterField.getId(): contribFilters.TrackFilterField,
        contribFilters.SessionFilterField.getId(): contribFilters.SessionFilterField,
        contribFilters.MaterialSubmittedFilterField.getId(): contribFilters.MaterialSubmittedFilterField,
        contribFilters.ReviewingFilterField.getId(): contribFilters.ReviewingFilterField
    }

#############################
# Conference Modif Display  #
#############################


class ConferencePicDelete(ConferenceModifBase):

    def _checkParams(self):
        ConferenceModifBase._checkParams(self)

        pm = ParameterManager(self._params)

        self._id = pm.extract("picId", pType=str, allowEmpty=False)

    def _getAnswer(self):
        im = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getImagesManager()
        im.removePic(self._id)

#############################
# Conference cretion        #
#############################


class ShowConcurrentEvents(ServiceBase):

    def _checkParams(self):
        ServiceBase._checkParams(self)

        pm = ParameterManager(self._params)

        self._tz = pm.extract("timezone", pType=str, allowEmpty=False)
        pm.setTimezone(self._tz)
        self._sDate = pm.extract("sDate", pType=datetime.datetime, allowEmpty=False)
        self._eDate = pm.extract("eDate", pType=datetime.datetime, allowEmpty=False)

    def _getAnswer(self):
        im = indexes.IndexesHolder()
        ch = conference.ConferenceHolder()
        calIdx = im.getIndex("calendar")
        evtIds = calIdx.getObjectsIn(self._sDate, self._eDate)

        evtsByCateg = {}
        for evtId in evtIds:
            try:
                evt = ch.getById(evtId)
                categs = evt.getOwnerList()
                categname = categs[0].getName()
                if not evtsByCateg.has_key(categname):
                    evtsByCateg[categname] = []
                evtsByCateg[categname].append((evt.getTitle().strip(), evt.getAdjustedStartDate().strftime('%d/%m/%Y %H:%M '),evt.getAdjustedEndDate().strftime('%d/%m/%Y %H:%M '), evt.getTimezone()))

            except Exception:
                continue
        return evtsByCateg


class ConferenceGetFieldsAndContribTypes(ConferenceDisplayBase):
    def _getAnswer(self):
        afm = self._target.getAbstractMgr().getAbstractFieldsMgr()
        afmDict = dict([(i, fossilize(f)) for i, f in enumerate(afm.getFields())])
        cTypes = self._target.getContribTypeList()
        cTypesDict = dict([(ct.getId(), ct.getName()) for ct in cTypes])
        return [afmDict, cTypesDict]


class ConferenceParticipantBase:

    def _generateParticipant(self, av=None):
        participant = Participant(self._conf, av)
        if av is None:
            participant.setTitle(self._title)
            participant.setFamilyName(self._familyName)
            participant.setFirstName(self._firstName)
            participant.setEmail(self._email)
            participant.setAffiliation(self._affiliation)
            participant.setAddress(self._address)
            participant.setTelephone(self._telephone)
            participant.setFax(self._fax)
        return participant

    def _sendEmailWithFormat(self, participant, data):
            data["toList"] = [participant.getEmail()]
            urlInvitation = urlHandlers.UHConfParticipantsInvitation.getURL( self._conf )
            urlInvitation.addParam("participantId","%s"%participant.getId())
            urlRefusal = urlHandlers.UHConfParticipantsRefusal.getURL( self._conf )
            urlRefusal.addParam("participantId","%s"%participant.getId())

            mailEnv = dict(name=participant.getEmail(),
                           confTitle=self._conf.getTitle(),
                           url=urlHandlers.UHConferenceDisplay.getURL( self._conf ),
                           urlRefusal=urlRefusal, urlInvitation=urlInvitation)

            data["body"] = permissive_format(data["body"], mailEnv)
            data["subject"] = permissive_format(data["subject"], mailEnv)
            data["content-type"] = 'text/html'
            GenericMailer.sendAndLog(GenericNotification(data), self._conf,
                                     log.ModuleNames.PARTICIPANTS)


class ConferenceAddEditParticipantBase(ConferenceParticipantBase):

    def _checkParams(self):
        pm = ParameterManager(self._params)
        self._id = pm.extract("id", pType=str, allowEmpty=True)
        self._title = pm.extract("title", pType=str, allowEmpty=True, defaultValue="")
        self._familyName = pm.extract("surName", pType=str, allowEmpty=True)
        self._firstName = pm.extract("name", pType=str, allowEmpty=True)
        if self._familyName.strip() == "" and self._firstName.strip() == "":
            raise NoReportError(_("User has neither First Name or Family Name."))
        self._email = pm.extract("email", pType=str, allowEmpty=False)
        self._affiliation = pm.extract("affiliation", pType=str, allowEmpty=True, defaultValue="")
        self._address = pm.extract("address", pType=str, allowEmpty=True, defaultValue="")
        self._telephone = pm.extract("phone", pType=str, allowEmpty=True, defaultValue="")
        self._fax = pm.extract("fax", pType=str, allowEmpty=True, defaultValue="")


class ConferenceParticipantListBase(ConferenceModifBase):

    def _checkParams(self):
        ConferenceModifBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._userList = pm.extract("userIds", pType=list, allowEmpty=False)

    def _getWarningAlreadyAdded(self, list, typeList=""):
        if len(list) == 1:
            return _("""The participant identified by email %s
                        is already in the %s participants' list.""") % (typeList, list[0])
        else:

            return _("""The participants identified by email %s
                        are already in the %s participants' list.""") % (typeList, ", ".join(list))

    def _checkParticipantConfirmed(self, participant):
        if not participant.isConfirmed():
            raise NoReportError(_("Selected participant(s) did not confirm invitation. Until then you can not change presence status"))


class ConferenceParticipantsDisplay(ConferenceModifBase):

    def _getAnswer(self):
        if self._conf.getParticipation().displayParticipantList():
            self._conf.getParticipation().participantListHide()
        else:
            self._conf.getParticipation().participantListDisplay()
        return True


class ConferenceParticipantsAddedInfo(ConferenceModifBase):

    def _getAnswer(self):
        if self._conf.getParticipation().isAddedInfo():
            self._conf.getParticipation().setNoAddedInfo(self._getUser())
        else:
            self._conf.getParticipation().setAddedInfo(self._getUser())
        return True


class ConferenceParticipantsAllowForApplying(ConferenceModifBase):

    def _getAnswer(self):
        if self._conf.getParticipation().isAllowedForApplying():
            self._conf.getParticipation().setNotAllowedForApplying(self._getUser())
        else:
            self._conf.getParticipation().setAllowedForApplying(self._getUser())
        return True


class ConferenceParticipantsAutoAccept(ConferenceModifBase):

    def _getAnswer(self):
        participation = self._conf.getParticipation()
        participation.setAutoAccept(not participation.isAutoAccept(), self._getUser())
        return participation.isAutoAccept()


class ConferenceParticipantsNotifyMgrNewParticipant(ConferenceModifBase):

    def _getAnswer(self):
        participation = self._conf.getParticipation()
        participation.setNotifyMgrNewParticipant(not participation.isNotifyMgrNewParticipant())


class ConferenceParticipantsSetNumMaxParticipants(ConferenceTextModificationBase):
    """
    Conference num max participants modification
    """
    def _handleSet(self):
        numMaxPart = self._value
        if (self._value == ""):
            raise ServiceError("ERR-E2", _("The value of the maximum numbers of participants cannot be empty."))
        try:
            numMaxPart = int(self._value)
        except ValueError:
            raise ServiceError("ERR-E3", _("The value of the maximum numbers of participants has to be a positive number."))

        self._target.getParticipation().setNumMaxParticipants(int(numMaxPart))

    def _handleGet(self):
        return self._target.getParticipation().getNumMaxParticipants()


class ConferenceApplyParticipant(ConferenceDisplayBase, ConferenceAddEditParticipantBase):

    def _checkParams(self):
        ConferenceDisplayBase._checkParams(self)
        ConferenceAddEditParticipantBase._checkParams(self)

    def _getAnswer(self):
        if self._conf.getStartDate() < timezoneUtils.nowutc() :
            raise NoReportError(_("""This event began on %s, you cannot apply for
                                         participation after the event began."""%self._conf.getStartDate()), title=_("Event started"))
        participation = self._conf.getParticipation()

        if not participation.isAllowedForApplying() :
            raise NoReportError( _("""Participation in this event is restricted to persons invited.
                                           If you insist on taking part in this event, please contact the event manager."""), title=_("Application restricted"))
        if participation.getNumMaxParticipants() > 0 and len(participation.getParticipantList()) >= participation.getNumMaxParticipants():
            raise NoReportError( _("""You cannot apply for participation in this event because the maximum numbers of participants has been reached.
                                           If you insist on taking part in this event, please contact the event manager."""), title=_("Maximum number of participants reached"))

        result = {}
        user = self._getUser()
        pending = self._generateParticipant(user)
        if participation.alreadyParticipating(pending) != 0:
            raise NoReportError(_("The participant can not be added to the meeting because there is already a participant with the email address '%s'."
                                % pending.getEmail()),title=_('Already registered participant'))
        elif participation.alreadyPending(pending)!=0:
            raise NoReportError(_("The participant can not be added to the meeting because there is already a pending participant with the email address '%s'."
                                % pending.getEmail()),title=_('Already pending participant'))
        else:
            if participation.addPendingParticipant(pending):
                if participation.isAutoAccept():
                    result["msg"] = _("The request for participation has been accepted")
                    if participation.displayParticipantList() :
                        result["listParticipants"] = participation.getPresentParticipantListText()
                    # check if an e-mail should be sent...
                    if participation.isNotifyMgrNewParticipant():
                        # to notify the manager of new participant addition
                        data = self.preparedNewParticipantMessage(pending)
                        GenericMailer.sendAndLog(GenericNotification(data),
                                                 self._conf,
                                                 log.ModuleNames.PARTICIPANTS)
                else:
                    result["msg"] = _("The participant identified by email '%s' has been added to the list of pending participants"
                                    % pending.getEmail())
            else:
                return NoReportError(_("The participant cannot be added."), title=_("Error"))
        return result

    def preparedNewParticipantMessage(self, participant):
        if participant is None :
            return None

        profileURL = urlHandlers.UHConfModifParticipants.getURL(self._conf)

        toList = []
        for manager in self._conf.getManagerList():
            if isinstance(manager, Avatar) :
                toList.append(manager.getEmail())

        data = {}
        data["toList"] = toList
        data["fromAddr"] = Config.getInstance().getSupportEmail()
        data["subject"] = "New participant joined '%s'" % self._conf.getTitle()

        data["body"] = """
        Dear Event Manager,

            A new participant, identified by email '%s' has been added to %s.
            The full list of participants can be managed at %s

        Your Indico
        """%(participant.getEmail(), self._conf.getTitle(), profileURL)

        return data

class ConferenceAddParticipant(ConferenceModifBase, ConferenceAddEditParticipantBase):

    def _checkParams(self):
        ConferenceModifBase._checkParams(self)
        ConferenceAddEditParticipantBase._checkParams(self)

    def _getAnswer(self):
        eventManager = self._getUser()
        av = AvatarHolder().match({"email": self._email.strip()}, exact=1, searchInAuthenticators=True)
        participation = self._conf.getParticipation()
        if av != None and av != []:
            participant = self._generateParticipant(av[0])
        else:
            participant = self._generateParticipant()
        if participation.alreadyParticipating(participant) != 0 :
            raise NoReportError(_("The participant can not be added to the meeting because there is already a participant with the email address '%s'."
                                % participant.getEmail()),title=_('Already registered participant'))
        elif participation.alreadyPending(participant)!=0:
            raise NoReportError(_("The participant can not be added to the meeting because there is already a pending participant with the email address '%s'."
                                % participant.getEmail()),title=_('Already pending participant'))
        else:
            participation.addParticipant(participant, eventManager)
        return conferences.WConferenceParticipant(self._conf,participant).getHTML().replace("\n","")

class ConferenceEditParticipant(ConferenceModifBase, ConferenceAddEditParticipantBase):

    def _checkParams(self):
        ConferenceModifBase._checkParams(self)
        ConferenceAddEditParticipantBase._checkParams(self)

    def _getAnswer(self):
        participant = self._conf.getParticipation().getParticipantById(self._id)
        if participant == None:
            raise NoReportError(_("The participant that you are trying to edit does not exist."))
        participant.setTitle(self._title)
        participant.setFamilyName(self._familyName)
        participant.setFirstName(self._firstName)
        participant.setEmail(self._email)
        participant.setAffiliation(self._affiliation)
        participant.setAddress(self._address)
        participant.setTelephone(self._telephone)
        participant.setFax(self._fax)
        return conferences.WConferenceParticipant(self._conf,participant).getHTML().replace("\n","")

class ConferenceEditPending(ConferenceModifBase, ConferenceAddEditParticipantBase):

    def _checkParams(self):
        ConferenceModifBase._checkParams(self)
        ConferenceAddEditParticipantBase._checkParams(self)

    def _getAnswer(self):
        pending = self._conf.getParticipation().getPendingParticipantByKey(self._id)
        if pending == None:
            raise NoReportError(_("The pending participant that you are trying to edit does not exist."))
        pending.setTitle(self._title)
        pending.setFamilyName(self._familyName)
        pending.setFirstName(self._firstName)
        pending.setEmail(self._email)
        pending.setAffiliation(self._affiliation)
        pending.setAddress(self._address)
        pending.setTelephone(self._telephone)
        pending.setFax(self._fax)
        return conferences.WConferenceParticipantPending(self._conf, self._id, pending).getHTML().replace("\n","")

class ConferenceAddParticipants(ConferenceParticipantBase, ConferenceParticipantListBase):

    def _addParticipant(self, participant, participation):
        if participation.alreadyParticipating(participant) != 0 :
            self._usersParticipant.append(participant.getEmail())
        elif participation.alreadyPending(participant)!=0:
            self._usersPending.append(participant.getEmail())
        else:
            participation.addParticipant(participant, self._getUser())
            self._added.append(conferences.WConferenceParticipant(self._conf,participant).getHTML())

    def _getAnswer(self):
        if self._userList == []:
            raise NoReportError(_("No users were selected to be added as participants."))
        self._usersPending = []
        self._usersParticipant = []
        self._added =[]
        participation = self._conf.getParticipation()
        result = {}
        infoWarning = []

        for user in self._userList:
            ph = PrincipalHolder()
            selected = ph.getById(user['id'])
            if selected is None and user["_type"] == "Avatar":
                raise NoReportError(_("""The user with email %s that you are adding does
                                    not exist anymore in the database""") % user["email"])
            if isinstance(selected, Avatar):
                self._addParticipant(self._generateParticipant(selected), participation)
            else:
                self._addParticipant(self._generateParticipant(), participation)

        result["added"] = ("".join(self._added)).replace("\n", "")
        if self._usersPending:
            infoWarning.append(self._getWarningAlreadyAdded(self._usersPending, "pending"))
        if self._usersParticipant:
            infoWarning.append(self._getWarningAlreadyAdded(self._usersParticipant))
        if infoWarning:
            result["infoWarning"] = infoWarning
        return result

class ConferenceInviteParticipants(ConferenceParticipantBase, ConferenceParticipantListBase):

    def _checkParams(self):
        ConferenceParticipantListBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._emailSubject = pm.extract("subject", pType=str, allowEmpty=False)
        self._emailBody = pm.extract("body", pType=str, allowEmpty=False)

    def _inviteParticipant(self, participant, participation):
        if participation.alreadyParticipating(participant) != 0 :
            self._usersParticipant.append(participant.getEmail())
            return False
        elif participation.alreadyPending(participant)!=0:
            self._usersPending.append(participant.getEmail())
            return False
        else:
            participation.inviteParticipant(participant, self._getUser())
            self._added.append(conferences.WConferenceParticipant(self._conf,participant).getHTML())
            return True

    def _getAnswer(self):
        if self._userList == []:
            raise NoReportError(_("No users were selected to be invited as participants."))
        self._usersPending = []
        self._usersParticipant = []
        self._added =[]
        currentUser = self._getUser()
        participation = self._conf.getParticipation()
        infoWarning = []

        result = {}
        data = {}

        if currentUser:
            data["fromAddr"] = currentUser.getEmail()
        else:
            data["fromAddr"] = formataddr((self._conf.getTitle(), Config.getInstance().getNoReplyEmail()))

        if self._emailBody.find('{urlInvitation}') == -1:
            raise NoReportError(_("The {urlInvitation} field is missing in your email. This is a mandatory field thus, this email cannot be sent."))

        data["subject"] = self._emailSubject
        data["body"] = self._emailBody
        for user in self._userList:
            ph = PrincipalHolder()
            selected = ph.getById(user['id'])
            if isinstance(selected, Avatar):
                participant = self._generateParticipant(selected)
                if self._inviteParticipant(participant, participation):
                    self._sendEmailWithFormat(participant, data)
            else:
                participant = self._generateParticipant()
                if self._inviteParticipant(participant, participation):
                    self._sendEmailWithFormat(participant, data)
        result["added"] = ("".join(self._added)).replace("\n","")
        if self._usersPending:
            infoWarning.append(self._getWarningAlreadyAdded(self._usersPending, "pending"))
        if self._usersParticipant:
            infoWarning.append(self._getWarningAlreadyAdded(self._usersParticipant))
        if infoWarning:
            result["infoWarning"] = infoWarning
        return result

class ConferenceRemoveParticipants(ConferenceParticipantListBase):

    def _getAnswer(self):
        if self._userList == []:
            raise NoReportError(_("No participants were selected to be removed."))
        for id in self._userList:
            self._conf.getParticipation().removeParticipant(id, self._getUser())
        return True

class ConferenceMarkPresenceParticipants(ConferenceParticipantListBase):

    def _getAnswer(self):
        if self._userList == []:
            raise NoReportError(_("No participants were selected to be marked as presents."))
        for id in self._userList:
            participant = self._conf.getParticipation().getParticipantById(id)
            self._checkParticipantConfirmed(participant)
            participant.setPresent()
        return True

class ConferenceMarkAbsentParticipants(ConferenceParticipantListBase):

    def _getAnswer(self):
        if self._userList == []:
            raise NoReportError(_("No participants were selected to be marked as absents."))
        for id in self._userList:
            participant = self._conf.getParticipation().getParticipantById(id)
            self._checkParticipantConfirmed(participant)
            participant.setAbsent()
        return True

class ConferenceExcuseAbsenceParticipants(ConferenceParticipantListBase):

    def _getAnswer(self):
        if self._userList == []:
            raise NoReportError(_("No participants were selected to be excused."))
        usersPresent = []
        for id in self._userList:
            participant = self._conf.getParticipation().getParticipantById(id)
            if not participant.setStatusExcused() and participant.isPresent() :
                usersPresent.append(participant.getFullName())
        if usersPresent:
            if len(usersPresent) == 1:
                raise NoReportError(_("""You cannot excuse absence of %s - this participant was present
                in the event""")%(usersPresent[0]))
            else:
                raise NoReportError(_("""You cannot excuse absence of %s - these participants were present
                in the event""")%(", ".join(usersPresent)))

        return True

class ConferenceEmailParticipants(ConferenceParticipantBase, ConferenceParticipantListBase):

    def _getAnswer(self):
        if self._userList == []:
            raise NoReportError(_("No participants were selected."))
        emailSubject = self._params.get("subject","")
        emailBody = self._params.get("body","")
        data = {}
        currentUser = self._getUser()

        if currentUser:
            data["fromAddr"] = currentUser.getEmail()
        else:
            data["fromAddr"] = formataddr((self._conf.getTitle(), Config.getInstance().getNoReplyEmail()))

        data["content-type"] = "text/html"
        data["subject"] = emailSubject
        for id in self._userList:
            participant = self._conf.getParticipation().getParticipantById(id)
            if participant:
                data["body"] = emailBody
                self._sendEmailWithFormat(participant, data)
        return True

class ConferenceAcceptPendingParticipants(ConferenceParticipantListBase):

    def _getAnswer(self):
        if self._userList == []:
            raise NoReportError(_("No pending participants were selected to be accepted."))
        for id in self._userList:
            pending = self._conf.getParticipation().getPendingParticipantByKey(id)
            self._conf.getParticipation().addParticipant(pending)
        return True

class ConferenceRejectPendingParticipants(ConferenceParticipantListBase):

    def _getAnswer(self):
        if self._userList == []:
            raise NoReportError(_("No pending participants were selected to be rejected."))
        for id in self._userList:
            pending = self._conf.getParticipation().getPendingParticipantByKey(id)
            pending.setStatusDeclined()
            self._conf.getParticipation().declineParticipant(pending)
        return True

class ConferenceRejectWithEmailPendingParticipants(ConferenceParticipantBase, ConferenceParticipantListBase):

    def _getAnswer(self):
        if self._userList == []:
            raise NoReportError(_("No pending participants were selected to be rejected."))
        pm = ParameterManager(self._params)
        emailSubject = pm.extract("subject", pType=str, allowEmpty=True)
        emailBody = pm.extract("body", pType=str, allowEmpty=True)
        data = {}
        data["fromAddr"] = Config.getInstance().getNoReplyEmail()
        data["subject"] =  emailSubject
        data["body"] =  emailBody
        for userId in self._userList:
            pending = self._conf.getParticipation().getPendingParticipantByKey(userId)
            pending.setStatusDeclined()
            self._conf.getParticipation().declineParticipant(pending)
            self._sendEmailWithFormat(pending, data)
        return True

class ConferenceProtectionUserList(ConferenceModifBase):

    def _getAnswer(self):
        #will use IAvatarFossil or IGroupFossil
        return fossilize(self._conf.getAllowedToAccessList())

class ConferenceProtectionAddUsers(ConferenceModifBase):

    def _checkParams(self):
        ConferenceModifBase._checkParams(self)

        self._usersData = self._params['value']
        self._user = self.getAW().getUser()

    def _getAnswer(self):

        for user in self._usersData :

            userToAdd = PrincipalHolder().getById(user['id'])

            if not userToAdd :
                raise ServiceError("ERR-U0","User does not exist!")

            self._conf.grantAccess(userToAdd)

class ConferenceProtectionRemoveUser(ConferenceModifBase):

    def _checkParams(self):
        ConferenceModifBase._checkParams(self)

        self._userData = self._params['value']

        self._user = self.getAW().getUser()

    def _getAnswer(self):

        userToRemove = PrincipalHolder().getById(self._userData['id'])

        if not userToRemove :
            raise ServiceError("ERR-U0","User does not exist!")
        elif isinstance(userToRemove, Avatar) or isinstance(userToRemove, Group) :
            self._conf.revokeAccess(userToRemove)


class ConferenceProtectionToggleDomains(ConferenceModifBase):

    def _checkParams(self):
        self._params['confId'] = self._params['targetId']
        ConferenceModifBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._domainId = pm.extract("domainId", pType=str)
        self._add = pm.extract("add", pType=bool)

    def _getAnswer(self):
        dh = domain.DomainHolder()
        d = dh.getById(self._domainId)
        if self._add:
            self._target.requireDomain(d)
        elif not self._add:
            self._target.freeDomain(d)


class ConferenceProtectionSetAccessKey(ConferenceModifBase):

    def _checkParams(self):
        ConferenceModifBase._checkParams(self)
        self._accessKey = self._params.get("accessKey", "")

    def _getAnswer(self):
        self._conf.setAccessKey(self._accessKey)

class ConferenceProtectionSetModifKey(ConferenceModifBase):

    def _checkParams(self):
        ConferenceModifBase._checkParams(self)
        self._modifKey = self._params.get("modifKey", "")

    def _getAnswer(self):
        self._conf.setModifKey(self._modifKey)

class ConferenceContactInfoModification( ConferenceTextModificationBase ):
    """
    Conference contact email modification
    """
    def _handleSet(self):
        self._target.getAccessController().setContactInfo(self._value)
    def _handleGet(self):
        return self._target.getAccessController().getContactInfo()

class ConferenceAlarmSendTestNow(ConferenceModifBase):

    def _checkParams(self):
        ConferenceModifBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._fromAddr = pm.extract("fromAddr", pType=str, allowEmpty=True, defaultValue="")
        self._note = pm.extract("note", pType=str, allowEmpty=True)
        self._includeConf = pm.extract("includeConf", pType=str, allowEmpty=True, defaultValue="")

    def _getAnswer(self):
        al = tasks.AlarmTask(self._conf, 0, datetime.timedelta(), relative=datetime.timedelta())
        if self._fromAddr:
            al.setFromAddr(self._fromAddr)
        else:
            raise NoReportError(_("""Please choose a "FROM" address for the test alarm"""))
        al.setNote(self._note)
        al.setConfSummary(self._includeConf == "1")
        if self._getUser():
            al.addToAddr(self._aw.getUser().getEmail())
        else:
            raise NoReportError(_("You must be logged in to use this feature"))
        al.run(check = False)
        return True


class ConferenceSocialBookmarksToggle(ConferenceModifBase):
    def _getAnswer(self):
        val = self._conf.getDisplayMgr().getShowSocialApps()
        self._conf.getDisplayMgr().setShowSocialApps(not val)

class ConferenceChairPersonBase(ConferenceModifBase):

    def _getChairPersonsList(self):
        result = fossilize(self._conf.getChairList())
        for chair in result:
            av = AvatarHolder().match({"email": chair['email']},
                                  searchInAuthenticators=False, exact=True)
            chair['showSubmitterCB'] = True
            if not av:
                if self._conf.getPendingQueuesMgr().getPendingConfSubmittersByEmail(chair['email']):
                    chair['showSubmitterCB'] = False
            elif (av[0] in self._conf.getAccessController().getSubmitterList()):
                chair['showSubmitterCB'] = False
            chair['showManagerCB'] = True
            if (av and self._conf.getAccessController().canModify(av[0])) or chair['email'] in self._conf.getAccessController().getModificationEmail():
                chair['showManagerCB'] = False
        return result

    def _isEmailAlreadyUsed(self, email):
        for chair in self._conf.getChairList():
            if email == chair.getEmail():
                return True
        return False

class ConferenceAddExistingChairPerson(ConferenceChairPersonBase):

    def _checkParams(self):
        ConferenceChairPersonBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._userList = pm.extract("userList", pType=list, allowEmpty=False)
        self._submissionRights = pm.extract("presenter-grant-submission", pType=bool, allowEmpty=False)
        # Check if there is already a user with the same email
        for person in self._userList:
            if self._isEmailAlreadyUsed(person["email"]):
                raise ServiceAccessError(_("A user with the email address %s is already in the Chairpersons list. Chairperson(s) not added.") % person["email"])

    def _newChair(self, av):
        chair = conference.ConferenceChair()
        chair.setTitle(av.getTitle())
        chair.setFirstName(av.getFirstName())
        chair.setFamilyName(av.getSurName())
        chair.setAffiliation(av.getAffiliation())
        chair.setEmail(av.getEmail())
        chair.setAddress(av.getAddress())
        chair.setPhone(av.getTelephone())
        chair.setFax(av.getFax())
        self._conf.addChair(chair)
        if self._submissionRights:
            self._conf.getAccessController().grantSubmission(chair)

    def _getAnswer(self):
        for person in self._userList:
            ah = AvatarHolder()
            av = ah.getById(person["id"])
            if av is None:
                raise NoReportError(_("The user with email %s that you are adding does not exist anymore in the database") % person["email"])
            self._newChair(av)

        return self._getChairPersonsList()


class ConferenceAddNewChairPerson(ConferenceChairPersonBase):

    def _checkParams(self):
        ConferenceChairPersonBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._userData = pm.extract("userData", pType=dict, allowEmpty=False)
        if self._userData.get("email", "") != "" and self._isEmailAlreadyUsed(self._userData.get("email", "")):
            raise ServiceAccessError(_("The email address is already used by another chairperson. Chairperson not added."))

    def _newChair(self):
        chair = conference.ConferenceChair()
        chair.setTitle(self._userData.get("title", ""))
        chair.setFirstName(self._userData.get("firstName", ""))
        chair.setFamilyName(self._userData.get("familyName", ""))
        chair.setAffiliation(self._userData.get("affiliation", ""))
        chair.setEmail(self._userData.get("email", ""))
        chair.setAddress(self._userData.get("address", ""))
        chair.setPhone(self._userData.get("phone", ""))
        chair.setFax(self._userData.get("fax", ""))
        self._conf.addChair(chair)
        #If the chairperson needs to be given management rights
        if self._userData.get("manager", None):
            avl = AvatarHolder().match({"email": self._userData.get("email", "")}, exact=True, searchInAuthenticators=False)
            if avl:
                av = avl[0]
                self._conf.grantModification(av)
            else:
                #Apart from granting the chairman, we add it as an Indico user
                self._conf.grantModification(chair)
        #If the chairperson needs to be given submission rights
        if self._userData.get("submission", False):
            if self._userData.get("email", "") == "":
                raise ServiceAccessError(_("It is necessary to enter the email of the user if you want to add him as submitter."))
            self._conf.getAccessController().grantSubmission(chair)

    def _getAnswer(self):
        self._newChair()
        return self._getChairPersonsList()


class ConferenceRemoveChairPerson(ConferenceChairPersonBase):

    def _checkParams(self):
        ConferenceChairPersonBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._chairId = pm.extract("userId", pType=str, allowEmpty=False)

    def _getAnswer(self):
        chair = self._conf.getChairById(self._chairId)
        self._conf.removeChair(chair)
        self._conf.getAccessController().revokeSubmission(chair)
        return self._getChairPersonsList()


class ConferenceEditChairPerson(ConferenceChairPersonBase):

    def _checkParams(self):
        ConferenceChairPersonBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._userData = pm.extract("userData", pType=dict, allowEmpty=False)
        self._chairId = pm.extract("userId", pType=str, allowEmpty=False)
        if self._userData.get("email", "") != "" and self._isEmailAlreadyUsed():
            raise ServiceAccessError(_("The email address is already used by another chairperson. Chairperson not modified."))

    def _isEmailAlreadyUsed(self):
        for chair in self._conf.getChairList():
            # check if the email is already used by other different chairperson
            if self._userData.get("email", "") == chair.getEmail() and self._chairId != str(chair.getId()):
                return True
        return False

    def _editChair(self, chair):
        chair.setTitle(self._userData.get("title", ""))
        chair.setFirstName(self._userData.get("firstName", ""))
        chair.setFamilyName(self._userData.get("familyName", ""))
        chair.setAffiliation(self._userData.get("affiliation", ""))
        if self._userData.get("email", "").lower().strip() != chair.getEmail().lower().strip():
            self._conf.getPendingQueuesMgr().removePendingConfSubmitter(chair)
        chair.setEmail(self._userData.get("email", ""))
        chair.setAddress(self._userData.get("address", ""))
        chair.setPhone(self._userData.get("phone", ""))
        chair.setFax(self._userData.get("fax", ""))
        #If the chairperson needs to be given management rights
        if self._userData.get("manager", None):
            avl = AvatarHolder().match({"email": self._userData.get("email", "")},
                                       searchInAuthenticators=False, exact=True)
            if avl:
                av = avl[0]
                self._conf.grantModification(av)
            else:
                #Apart from granting the chairman, we add it as an Indico user
                self._conf.grantModification(chair)
        #If the chairperson needs to be given submission rights because the checkbox is selected
        if self._userData.get("submission", False):
            if self._userData.get("email", "") == "":
                raise ServiceAccessError(_("It is necessary to enter the email of the user if you want to add him as submitter."))
            self._conf.getAccessController().grantSubmission(chair)

    def _getAnswer(self):
        chair = self._conf.getChairById(self._chairId)
        self._editChair(chair)
        return self._getChairPersonsList()


class ConferenceSendEmailData(ConferenceChairPersonBase):
        def _getAnswer(self):
            pm = ParameterManager(self._params)
            self._chairperson = self._conf.getChairById(pm.extract("userId", pType=str, allowEmpty=False))
            return {"confTitle": self._conf.getTitle(),
                    "email": self._chairperson.getEmail()
                    }


class ConferenceChangeSubmissionRights(ConferenceChairPersonBase):

    def _checkParams(self):
        ConferenceModifBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._chairperson = self._conf.getChairById(pm.extract("userId", pType=str, allowEmpty=False))
        if self._chairperson == None:
            raise ServiceAccessError(_("The user that you are trying to delete does not exist."))
        if self._chairperson.getEmail() == "":
            raise ServiceAccessError(_("It is not possible to grant submission rights to a participant without an email address. Please set an email address."))
        self._action = pm.extract("action", pType=str, allowEmpty=False)

    def _getAnswer(self):
        if self._action == "grant":
            self._conf.getAccessController().grantSubmission(self._chairperson)
        elif self._action == "remove":
            self._conf.getAccessController().revokeSubmission(self._chairperson)
        return self._getChairPersonsList()

class ConferenceProgramDescriptionModification( ConferenceHTMLModificationBase ):
    """
    Conference program description modification
    """
    def _handleSet(self):
        self._target.setProgramDescription(self._value)

    def _handleGet(self):
        return self._target.getProgramDescription()

class ConferenceAddParticipantBase(ConferenceModifBase):

    def _checkParams(self):
        ConferenceModifBase._checkParams(self)
        self._pm = ParameterManager(self._params)


    def _isEmailAlreadyUsed(self, email):
        for part in self._conf.getParticipation().getParticipantList():
            if email == part.getEmail():
                return True
        return False


class ConferenceParticipantAddExisting(ConferenceAddParticipantBase):

    def _checkParams(self):
        ConferenceAddParticipantBase._checkParams(self)
        self._action = self._pm.extract("action", pType=str, allowEmpty=False)
        self._userList = self._pm.extract("userList", pType=list, allowEmpty=False)
        # Check if there is already a participant with the same email
        for part in self._userList:
            if self._isEmailAlreadyUsed(part["email"]):
                raise ServiceAccessError(_("The email address (%s) of a participant you are trying to add is already used by another participant. Participant(s) not added.") % part["email"])

    def _getAnswer(self):
        eventManager = self._getUser()
        for part in self._userList:
            ah = AvatarHolder()
            av = ah.getById(part["id"])
            participant = Participant(self._conf, av)
            if self._action == "add":
                self._conf.getParticipation().addParticipant(participant, eventManager)
            elif self._action == "invite":
                self._conf.getParticipation().inviteParticipant(participant, eventManager)
        return fossilize(self._conf.getParticipation().getParticipantList())

class ConferenceManagerListBase(ConferenceModifBase):

    def _getManagersList(self):
        result = fossilize(self._conf.getManagerList())
        # get pending users
        for email in self._conf.getAccessController().getModificationEmail():
            pendingUser = {}
            pendingUser["email"] = email
            pendingUser["pending"] = True
            result.append(pendingUser)
        return result


class ConferenceProtectionAddExistingManager(ConferenceManagerListBase):

    def _checkParams(self):
        ConferenceManagerListBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._userList = pm.extract("userList", pType=list, allowEmpty=False)

    def _getAnswer(self):
        ph = PrincipalHolder()
        for user in self._userList:
            principal = ph.getById(user["id"])
            if principal is None and user["_type"] == "Avatar":
                raise NoReportError(_("The user with email %s that you are adding does not exist anymore in the database") % user["email"])
            self._conf.grantModification(principal)
        return self._getManagersList()


class ConferenceProtectionRemoveManager(ConferenceManagerListBase):

    def _checkParams(self):
        ConferenceManagerListBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._managerId = pm.extract("userId", pType=str, allowEmpty=False)
        self._kindOfUser = pm.extract("kindOfUser", pType=str, allowEmpty=True, defaultValue=None)

    def _getAnswer(self):
        if self._kindOfUser == "pending":
            # remove pending email, self._submitterId is an email address
            self._conf.getAccessController().revokeModificationEmail(self._managerId)
        else:
            ph = PrincipalHolder()
            self._conf.revokeModification(ph.getById(self._managerId))
        return self._getManagersList()


class ConferenceProtectionAddExistingRegistrar(ConferenceModifBase):

    def _checkParams(self):
        ConferenceModifBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._userList = pm.extract("userList", pType=list, allowEmpty=False)

    def _getAnswer(self):
        ph = PrincipalHolder()
        for user in self._userList:
            self._conf.addToRegistrars(ph.getById(user["id"]))
        return fossilize(self._conf.getRegistrarList())


class ConferenceProtectionRemoveRegistrar(ConferenceManagerListBase):

    def _checkParams(self):
        ConferenceManagerListBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._registrarId = pm.extract("userId", pType=str, allowEmpty=False)

    def _getAnswer(self):
        ph = PrincipalHolder()
        self._conf.removeFromRegistrars(ph.getById(self._registrarId))
        return fossilize(self._conf.getRegistrarList())

class ConferenceGetChildrenProtected(ConferenceModifBase):

    def _getAnswer(self):
        return fossilize(self._conf.getAccessController().getProtectedChildren())

class ConferenceGetChildrenPublic(ConferenceModifBase):

    def _getAnswer(self):
        return fossilize(self._conf.getAccessController().getPublicChildren())

class ConferenceExportURLs(ConferenceDisplayBase, ExportToICalBase):

    def _checkParams(self):
        ConferenceDisplayBase._checkParams(self)
        ExportToICalBase._checkParams(self)

    def _getAnswer(self):
        result = {}

        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()

        urls = generate_public_auth_request(self._apiMode, self._apiKey, '/export/event/%s.ics'%self._target.getId(), {}, minfo.isAPIPersistentAllowed() and self._apiKey.isPersistentAllowed(), minfo.isAPIHTTPSRequired())
        result["publicRequestURL"] = urls["publicRequestURL"]
        result["authRequestURL"] =  urls["authRequestURL"]
        urls = generate_public_auth_request(self._apiMode, self._apiKey, '/export/event/%s.ics'%self._target.getId(), {'detail': "contribution"}, minfo.isAPIPersistentAllowed() and self._apiKey.isPersistentAllowed(), minfo.isAPIHTTPSRequired())
        result["publicRequestDetailedURL"] = urls["publicRequestURL"]
        result["authRequestDetailedURL"] =  urls["authRequestURL"]
        return result

class ConferenceOfflineAddTask(ConferenceModifBase):

    def _checkParams(self):
        ConferenceModifBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._avatar = AvatarHolder().getById(pm.extract("avatarId", pType=str, allowEmpty=False))

    def _getAnswer(self):
        offlineEventsModule = ModuleHolder().getById("offlineEvents")
        offlineEvent = OfflineEventItem(self._conf, self._avatar, "Queued")
        offlineEventsModule.addOfflineEvent(offlineEvent)
        client = Client()
        client.enqueue(OfflineEventGeneratorTask(offlineEvent))
        return True

methodMap = {
    "main.changeTitle": ConferenceTitleModification,
    "main.changeSupport": ConferenceSupportModification,
    "main.changeSpeakerText": ConferenceSpeakerTextModification,
    "main.changeOrganiserText": ConferenceOrganiserTextModification,
    "main.changeDefaultStyle": ConferenceDefaultStyleModification,
    "main.changeVisibility": ConferenceVisibilityModification,
    "main.changeType": ConferenceTypeModification,
    "main.changeDescription": ConferenceDescriptionModification,
    "main.changeAdditionalInfo": ConferenceAdditionalInfoModification,
    "main.changeDates": ConferenceStartEndDateTimeModification,
    "main.changeBooking": ConferenceBookingModification,
    "main.displayBooking": ConferenceBookingModification,
    "main.changeShortURL": ConferenceShortURLModification,
    "main.changeKeywords": ConferenceKeywordsModification,
    "main.changeTimezone": ConferenceTimezoneModification,
    "main.addExistingChairPerson": ConferenceAddExistingChairPerson,
    "main.addNewChairPerson": ConferenceAddNewChairPerson,
    "main.removeChairPerson": ConferenceRemoveChairPerson,
    "main.editChairPerson": ConferenceEditChairPerson,
    "main.sendEmailData": ConferenceSendEmailData,
    "main.changeSubmissionRights": ConferenceChangeSubmissionRights,
    "program.changeDescription": ConferenceProgramDescriptionModification,
    "rooms.list" : ConferenceListUsedRooms,
    "contributions.list" : ConferenceListContributionsReview,
    "contributions.listAll" : ConferenceListContributions,
    "contributions.delete": ConferenceDeleteContributions,
    "sessions.listAll" : ConferenceListSessions,
    "pic.delete": ConferencePicDelete,
    "social.toggle": ConferenceSocialBookmarksToggle,
    "showConcurrentEvents": ShowConcurrentEvents,
#    "getFields": ConferenceGetFields,
    "getFieldsAndContribTypes": ConferenceGetFieldsAndContribTypes,
    "participation.allowDisplay": ConferenceParticipantsDisplay,
    "participation.notifyMgrNewParticipant": ConferenceParticipantsNotifyMgrNewParticipant,
    "participation.addedInfo": ConferenceParticipantsAddedInfo,
    "participation.allowForApply": ConferenceParticipantsAllowForApplying,
    "participation.autoAccept": ConferenceParticipantsAutoAccept,
    "participation.setNumMaxParticipants": ConferenceParticipantsSetNumMaxParticipants,
    "participation.applyParticipant": ConferenceApplyParticipant,
    "participation.addParticipant": ConferenceAddParticipant,
    "participation.editParticipant": ConferenceEditParticipant,
    "participation.editPending": ConferenceEditPending,
    "participation.addParticipants": ConferenceAddParticipants,
    "participation.inviteParticipants": ConferenceInviteParticipants,
    "participation.removeParticipants": ConferenceRemoveParticipants,
    "participation.markPresent": ConferenceMarkPresenceParticipants,
    "participation.markAbsence": ConferenceMarkAbsentParticipants,
    "participation.excuseAbsence": ConferenceExcuseAbsenceParticipants,
    "participation.emailParticipants": ConferenceEmailParticipants,
    "participation.acceptPending": ConferenceAcceptPendingParticipants,
    "participation.rejectPending": ConferenceRejectPendingParticipants,
    "participation.rejectPendingWithEmail": ConferenceRejectWithEmailPendingParticipants,
    "protection.getAllowedUsersList": ConferenceProtectionUserList,
    "protection.addAllowedUsers": ConferenceProtectionAddUsers,
    "protection.removeAllowedUser": ConferenceProtectionRemoveUser,
    "protection.toggleDomains": ConferenceProtectionToggleDomains,
    "protection.setAccessKey": ConferenceProtectionSetAccessKey,
    "protection.setModifKey": ConferenceProtectionSetModifKey,
    "protection.changeContactInfo": ConferenceContactInfoModification,
    "alarm.sendTestNow": ConferenceAlarmSendTestNow,
    "protection.addExistingManager": ConferenceProtectionAddExistingManager,
    "protection.removeManager": ConferenceProtectionRemoveManager,
    "protection.addExistingRegistrar": ConferenceProtectionAddExistingRegistrar,
    "protection.removeRegistrar": ConferenceProtectionRemoveRegistrar,
    "protection.getProtectedChildren": ConferenceGetChildrenProtected,
    "protection.getPublicChildren": ConferenceGetChildrenPublic,
    "api.getExportURLs": ConferenceExportURLs,
    "offline.addTask": ConferenceOfflineAddTask
    }
