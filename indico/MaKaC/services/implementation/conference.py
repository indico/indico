# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.


"""
Asynchronous request handlers for conference-related data modification.
"""

# 3rd party imports
from flask import session
from indico.modules.events.layout import layout_settings
from MaKaC.webinterface.rh.categoryDisplay import UtilsConference
from indico.core import signals

import datetime

# legacy indico imports
from MaKaC.i18n import _
from MaKaC import domain, conference as conference

from MaKaC.common import indexes, filters
from MaKaC.common.utils import validMail, setValidEmailSeparators, formatDateTime
from MaKaC.common.url import ShortURLMapper
from MaKaC.common.fossilize import fossilize
from MaKaC.common.contextManager import ContextManager
from indico.core.logger import Logger

from MaKaC.errors import TimingError
from MaKaC.fossils.contribution import IContributionFossil

from MaKaC.webinterface.rh.reviewingModif import RCReferee, RCPaperReviewManager
from MaKaC.webinterface.common import contribFilters

from MaKaC.services.implementation.base import (ProtectedModificationService, ListModificationBase, ParameterManager,
                                                ProtectedDisplayService, ServiceBase, TextModificationBase,
                                                HTMLModificationBase, ExportToICalBase)
from MaKaC.services.interface.rpc.common import (HTMLSecurityError, NoReportError, ResultWithWarning,
                                                 ServiceAccessError, ServiceError, TimingNoReportError, Warning)


# indico imports
from indico.core.db.sqlalchemy.principals import EmailPrincipal, PrincipalType
from indico.modules.events.layout import theme_settings
from indico.modules.events.util import track_time_changes
from indico.modules.users.util import get_user_by_email
from indico.util.user import principal_from_fossil, principal_is_only_for_user
from indico.web.http_api.util import generate_public_auth_request
from indico.core.config import Config


class ConferenceBase:
    """
    Base class for conference modification
    """

    def _checkParams(self):

        try:
            self._target = self._conf = conference.ConferenceHolder().getById(self._params["conference"])
        except Exception:
            try:
                self._target = self._conf = conference.ConferenceHolder().getById(self._params["confId"])
            except Exception:
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
    Event type modification
    """
    def _handleSet(self):
        curType = self._target.getType()
        newType = self._value
        if newType != "" and newType != curType:
            import MaKaC.webinterface.webFactoryRegistry as webFactoryRegistry
            wr = webFactoryRegistry.WebFactoryRegistry()
            factory = wr.getFactoryById(newType)
            wr.registerFactory(self._target, factory)
            # revert to the default theme for the event type
            layout_settings.delete(self._conf, 'timetable_theme')
            signals.event.data_changed.send(self._target, attr=None, old=None, new=None)

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

        old_data = {'location': loc.name if loc else '',
                    'address': loc.address if loc else '',
                    'room': room.name if room else ''}

        newLocation = self._value.get('location')
        newRoom = self._value.get('room')

        if room is None:
            room = conference.CustomRoom()
            self._target.setRoom(room)

        if room.getName() != newRoom:
            room.setName(newRoom)

            if Config.getInstance().getIsRoomBookingActive():
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

        if loc.getAddress() != self._value['address']:
            loc.setAddress(self._value['address'])
            changed = True

        if changed:
            new_data = {'location': loc.name,
                        'address': loc.address,
                        'room': room.name}
            if old_data != new_data:
                signals.event.data_changed.send(self._target, attr='location', old=old_data, new=new_data)

    def _handleGet(self):

        loc = self._target.getLocation()
        room = self._target.getRoom()

        return {'location': loc.getName() if loc else "",
                'room': room.name if room else "",
                'address': loc.getAddress() if loc else ""}


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

    def process(self):
        try:
            return ConferenceTextModificationBase.process(self)
        except HTMLSecurityError as e:
            raise NoReportError(e.message)


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
        if self._value == theme_settings.defaults[self._conf.getType()]:
            layout_settings.delete(self._conf, 'timetable_theme')
        else:
            layout_settings.set(self._conf, 'timetable_theme', self._value)

    def _handleGet(self):
        return layout_settings.get(self._conf, 'timetable_theme')


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
            with track_time_changes():
                self._target.setDates(self._startDate, self._endDate, moveEntries=moveEntries)
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
            if not cont.isScheduled():
                continue
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
            if not contrib:
                Logger.get().warning('Contribution {} in event {} was not deleted: Could not be found'.format(contribId, self._conf.getId()))
                continue
            if contrib.getSession() is not None and contrib.getSession().isClosed():
                msg = _("""The contribution "{}" cannot be deleted because it is inside of the session "{}" that """
                        """is closed""").format(contrib.getId(), contrib.getSession().getTitle())
                raise ServiceAccessError(msg)
            contrib.getParent().getSchedule().removeEntry(contrib.getSchEntry())
            contrib.delete()

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


class ConferenceProtectionUserList(ConferenceModifBase):

    def _getAnswer(self):
        # will use IAvatarFossil or IGroupFossil
        return fossilize(self._conf.getAllowedToAccessList())


class ConferenceProtectionAddUsers(ConferenceModifBase):

    def _checkParams(self):
        ConferenceModifBase._checkParams(self)
        self._principals = [principal_from_fossil(f, allow_pending=True) for f in self._params['value']]
        self._user = self.getAW().getUser()

    def _getAnswer(self):
        for principal in self._principals:
            self._conf.grantAccess(principal)
        return fossilize(self._conf.getAccessController().getAccessList())


class ConferenceProtectionRemoveUser(ConferenceModifBase):

    def _checkParams(self):
        ConferenceModifBase._checkParams(self)
        self._principal = principal_from_fossil(self._params['value'], allow_missing_groups=True)
        self._user = self.getAW().getUser()

    def _getAnswer(self):
        self._conf.revokeAccess(self._principal)


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


class ConferenceChairPersonBase(ConferenceModifBase):
    def _getChairPersonsList(self):
        result = fossilize(self._conf.getChairList())
        for chair in result:
            user = get_user_by_email(chair['email'])
            chair['showManagerCB'] = True
            chair['showSubmitterCB'] = True
            email_submitters = {x.email for x in self._conf.as_event.acl_entries
                                if x.type == PrincipalType.email and x.has_management_role('submit', explicit=True)}
            if chair['email'] in email_submitters or (user and self._conf.as_event.can_manage(user, 'submit',
                                                                                              explicit_role=True)):
                chair['showSubmitterCB'] = False
            email_managers = {x.email for x in self._conf.as_event.acl_entries
                              if x.type == PrincipalType.email and x.has_management_role()}
            if chair['email'] in email_managers or (user and self._conf.as_event.can_manage(user, explicit_role=True)):
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
            self._conf.as_event.update_principal(av.user, add_roles={'submit'})

    def _getAnswer(self):
        for person in self._userList:
            self._newChair(principal_from_fossil(person, allow_pending=True))

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
        email = self._userData.get('email')
        if self._userData.get('manager') and email:
            self._conf.as_event.update_principal(EmailPrincipal(email), full_access=True)

        #If the chairperson needs to be given submission rights
        if self._userData.get("submission", False):
            if not email:
                raise ServiceAccessError(_("It is necessary to enter the email of the user if you want to add him as submitter."))
            self._conf.as_event.update_principal(EmailPrincipal(email), add_roles={'submit'})

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

        if chair is None:
            raise NoReportError(_('Someone may have deleted this chairperson meanwhile. Please refresh the page.'))

        self._conf.removeChair(chair)
        email = chair.getEmail()
        if email:
            # XXX: this doesn't remove managerment permissions. probably because we don't know
            # they were granted before or when adding him as a chairperson?
            self._conf.as_event.update_principal(EmailPrincipal(email), del_roles={'submit'})
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
            self._conf.as_event.update_principal(EmailPrincipal(chair.getEmail()), del_roles={'submit'})
        chair.setEmail(self._userData.get("email", ""))
        chair.setAddress(self._userData.get("address", ""))
        chair.setPhone(self._userData.get("phone", ""))
        chair.setFax(self._userData.get("fax", ""))
        #If the chairperson needs to be given management rights
        email = self._userData.get('email')
        if self._userData.get('manager') and email:
            self._conf.as_event.update_principal(EmailPrincipal(email), full_access=True)
        #If the chairperson needs to be given submission rights because the checkbox is selected
        if self._userData.get("submission", False):
            if not email:
                raise ServiceAccessError(_("It is necessary to enter the email of the user if you want to add him as submitter."))
            self._conf.as_event.update_principal(EmailPrincipal(email), add_roles={'submit'})

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
            self._conf.as_event.update_principal(EmailPrincipal(self._chairperson.getEmail()), add_roles={'submit'})
        elif self._action == "remove":
            self._conf.as_event.update_principal(EmailPrincipal(self._chairperson.getEmail()), del_roles={'submit'})
        return self._getChairPersonsList()

class ConferenceProgramDescriptionModification( ConferenceHTMLModificationBase ):
    """
    Conference program description modification
    """
    def _handleSet(self):
        self._target.setProgramDescription(self._value)

    def _handleGet(self):
        return self._target.getProgramDescription()


class ConferenceManagerListBase(ConferenceModifBase):

    def _getManagersList(self):
        return fossilize(self._conf.getManagerList())


class ConferenceProtectionAddExistingManager(ConferenceManagerListBase):

    def _checkParams(self):
        ConferenceManagerListBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._principals = (principal_from_fossil(f, allow_pending=True, legacy=False)
                            for f in pm.extract("userList", pType=list, allowEmpty=False))

    def _getAnswer(self):
        for principal in self._principals:
            self._conf.as_event.update_principal(principal, full_access=True)
        return self._getManagersList()


class ConferenceProtectionRemoveManager(ConferenceManagerListBase):
    def _getAnswer(self):
        principal = principal_from_fossil(self._params['principal'], legacy=False, allow_missing_groups=True,
                                          allow_emails=True)
        event = self._conf.as_event
        if not self._params.get('force') and principal_is_only_for_user(event.acl_entries, session.user, principal):
            # this is pretty ugly, but the user list manager widget is used in multiple
            # places so like this we keep the changes to the legacy widget to a minimum
            return 'confirm_remove_self'
        event.update_principal(principal, full_access=False)
        return self._getManagersList()


class ConferenceProtectionAddExistingRegistrar(ConferenceModifBase):

    def _checkParams(self):
        ConferenceModifBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._principals = [principal_from_fossil(f, allow_pending=True, legacy=False)
                            for f in pm.extract("userList", pType=list, allowEmpty=False)]

    def _getAnswer(self):
        for principal in self._principals:
            self._conf.as_event.update_principal(principal, add_roles={'registration'})
        return fossilize(self._conf.getRegistrarList())


class ConferenceProtectionRemoveRegistrar(ConferenceManagerListBase):

    def _checkParams(self):
        ConferenceManagerListBase._checkParams(self)
        self._principal = principal_from_fossil(self._params['principal'], legacy=False, allow_missing_groups=True,
                                                allow_emails=True)

    def _getAnswer(self):
        self._conf.as_event.update_principal(self._principal, del_roles={'registration'})
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
        urls = generate_public_auth_request(self._apiKey, '/export/event/%s.ics' % self._target.getId())
        result["publicRequestURL"] = urls["publicRequestURL"]
        result["authRequestURL"] = urls["authRequestURL"]
        urls = generate_public_auth_request(self._apiKey, '/export/event/%s.ics' % self._target.getId(),
                                            {'detail': 'contribution'})
        result["publicRequestDetailedURL"] = urls["publicRequestURL"]
        result["authRequestDetailedURL"] = urls["authRequestURL"]
        return result

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
    "contributions.list" : ConferenceListContributionsReview,
    "contributions.listAll" : ConferenceListContributions,
    "contributions.delete": ConferenceDeleteContributions,
    "sessions.listAll" : ConferenceListSessions,
    "showConcurrentEvents": ShowConcurrentEvents,
    "getFieldsAndContribTypes": ConferenceGetFieldsAndContribTypes,
    "protection.getAllowedUsersList": ConferenceProtectionUserList,
    "protection.addAllowedUsers": ConferenceProtectionAddUsers,
    "protection.removeAllowedUser": ConferenceProtectionRemoveUser,
    "protection.toggleDomains": ConferenceProtectionToggleDomains,
    "protection.setAccessKey": ConferenceProtectionSetAccessKey,
    "protection.setModifKey": ConferenceProtectionSetModifKey,
    "protection.changeContactInfo": ConferenceContactInfoModification,
    "protection.addExistingManager": ConferenceProtectionAddExistingManager,
    "protection.removeManager": ConferenceProtectionRemoveManager,
    "protection.addExistingRegistrar": ConferenceProtectionAddExistingRegistrar,
    "protection.removeRegistrar": ConferenceProtectionRemoveRegistrar,
    "protection.getProtectedChildren": ConferenceGetChildrenProtected,
    "protection.getPublicChildren": ConferenceGetChildrenPublic,
    "api.getExportURLs": ConferenceExportURLs,
}
