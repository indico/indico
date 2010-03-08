"""
Asynchronous request handlers for conference-related data modification.
"""

from MaKaC.services.implementation.base import ProtectedModificationService,\
    ListModificationBase, ParameterManager
from MaKaC.services.implementation.base import ProtectedDisplayService, ServiceBase

import MaKaC.webinterface.displayMgr as displayMgr

from MaKaC.common.Configuration import Config
from MaKaC.common import filters
from MaKaC.common.utils import validMail, setValidEmailSeparators
from MaKaC.common.PickleJar import DictPickler
from MaKaC.common import indexes, info

from MaKaC.conference import ConferenceHolder
import MaKaC.conference as conference
from MaKaC.services.implementation.base import TextModificationBase
from MaKaC.services.implementation.base import HTMLModificationBase
from MaKaC.services.implementation.base import DateTimeModificationBase
from MaKaC.webinterface.rh.reviewingModif import RCReferee, RCPaperReviewManager
from MaKaC.webinterface.common import contribFilters
import MaKaC.webinterface.wcomponents as wcomponents
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.common.timezoneUtils as timezoneUtils
from MaKaC.common.contextManager import ContextManager

import datetime
from pytz import timezone

from MaKaC.errors import TimingError
from MaKaC.common.logger import Logger
from MaKaC.i18n import _

from MaKaC.services.interface.rpc.common import ServiceError, Warning, ResultWithWarning

class ConferenceBase(object):
    """
    Base class for conference modification
    """

    def _checkParams( self ):

        try:
            self._target = self._conf = ConferenceHolder().getById(self._params["conference"]);
            if self._target == None:
                Logger.get('rpc.conference').debug('self._target is null')
                raise Exception("Null target.")
        except:
            raise ServiceError("ERR-E4", "Invalid conference id.")

class ConferenceModifBase(ProtectedModificationService, ConferenceBase):
    def _checkParams(self):
        ConferenceBase._checkParams(self)
        ProtectedModificationService._checkParams(self)

class ConferenceScheduleModifBase(ConferenceModifBase):
    def _checkParams(self):
        ConferenceModifBase._checkParams(self)

        self._schEntry = self._conf.getSchedule().getEntryById(self._params["scheduleEntry"])
        if self._schEntry == None:
            raise ServiceError("ERR-E4", "Invalid scheduleEntry id.")

    def _checkProtection( self ):
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


class ConferenceTitleModification( ConferenceTextModificationBase ):
    """
    Conference title modification
    """
    def _handleSet(self):
        title = self._value
        if (title ==""):
            raise ServiceError("ERR-E2",
                               "The title cannot be empty")
        self._target.setTitle(self._value)

    def _handleGet(self):
        return self._target.getTitle()


class ConferenceDescriptionModification( ConferenceHTMLModificationBase ):
    """
    Conference description modification
    """
    def _handleSet(self):
        self._target.setDescription(self._value)

    def _handleGet(self):
        return self._target.getDescription()

class ConferenceAdditionalInfoModification( ConferenceHTMLModificationBase ):
    """
    Conference additional info (a.k.a contact info) modification
    """
    def _handleSet(self):
        self._target.setContactInfo(self._value)

    def _handleGet(self):
        return self._target.getContactInfo()

class ConferenceTypeModification( ConferenceTextModificationBase ):
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
            dispMgr.setDefaultStyle(styleMgr.getDefaultStylesheetForEventType(newType))

    def _handleGet(self):
        return self._target.getType()


class ConferenceBookingModification( ConferenceTextModificationBase ):
    """
    Conference location name modification
    """
    def _handleSet(self):
        room = self._target.getRoom()

        if  room == None:
            room = conference.CustomRoom()
            self._target.setRoom(room)

        # if a room name is not passed, it is assumed
        # as empty
        if 'room' in self._value:
            room.setName( self._value['room'] )

        loc = self._target.getLocation()
        if not loc:
            loc = conference.CustomLocation()
            self._target.setLocation(loc)

        if 'location' in self._value:
            loc.setName( self._value['location'] )

        loc.setAddress( self._value['address'] )

    def _handleGet(self):

        loc = self._target.getLocation()
        room = self._target.getRoom()
        if loc:
            locName = loc.getName()
            locAddress = loc.getAddress()
        else:
            locName = None
            locAddress = ''
        if room:
            roomName = room.name
        else:
            roomName = None

        return { 'location': locName,
                 'room': roomName,
                 'address': locAddress }

class ConferenceBookingDisplay( ConferenceDisplayBase ):
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

        return { 'location': locName,
                 'room': roomName,
                 'address': locAddress }

class ConferenceSpeakerTextModification( ConferenceTextModificationBase ):
    """ Conference chairman text modification (for conferences and meetings)
    """
    def _handleSet(self):
        self._target.setChairmanText(self._value)

    def _handleGet(self):
        return self._target.getChairmanText()

class ConferenceOrganiserTextModification( ConferenceTextModificationBase ):
    """ Conference organiser text modification (for lectures)
    """
    def _handleSet(self):
        self._target.setOrgText(self._value)

    def _handleGet(self):
        return self._target.getOrgText()

class ConferenceSupportEmailModification( ConferenceTextModificationBase ):
    """
    Conference support e-mail modification
    """
    def _handleSet(self):
        # handling the case of a list of emails with separators different than ","
        emailstr = setValidEmailSeparators(self._value)

        if validMail(emailstr) or emailstr == '':
            self._target.setSupportEmail(emailstr)
        else:
            raise ServiceError('ERR-E0', 'E-mail address %s is not valid!' %
                               self._value)

    def _handleGet(self):
        return self._target.getSupportEmail()

class ConferenceSupportModification( ConferenceTextModificationBase ):
    """
    Conference support caption and e-mail modification
    """
    def _handleSet(self):
        dMgr = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._target)
        caption = self._value.get("caption","")
        email = self._value.get("email")

        if caption == "":
            raise ServiceError("ERR-E2", "The caption cannot be empty")
        dMgr.setSupportEmailCaption(caption)

        # handling the case of a list of emails with separators different than ","
        email = setValidEmailSeparators(email)

        if validMail(email) or email == "":
            self._target.setSupportEmail(email)
        else:
            raise ServiceError('ERR-E0', 'E-mail address %s is not valid!' %
                               self._value)

    def _handleGet(self):
        dMgr = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._target)
        caption = dMgr.getSupportEmailCaption()
        email = self._target.getSupportEmail()

        return { "caption": caption,
                 "email": email }

class ConferenceDefaultStyleModification( ConferenceTextModificationBase ):
    """
    Conference default style modification
    """
    def _handleSet(self):
        dispManReg = displayMgr.ConfDisplayMgrRegistery()
        dispManReg.getDisplayMgr(self._target).setDefaultStyle(self._value)

    def _handleGet(self):
        dispManReg = displayMgr.ConfDisplayMgrRegistery()
        return dispManReg.getDisplayMgr(self._target).getDefaultStyle()

class ConferenceVisibilityModification( ConferenceTextModificationBase ):
    """

    Conference visibility modification
    """
    def _handleSet(self):
        try:
            val = int(self._value)
        except ValueError:
            raise ServiceError("ERR-E1","Invalid value type for property")
        self._target.setVisibility(val)

    def _handleGet(self):
        return self._target.getVisibility()

class ConferenceStartEndDateTimeModification( ConferenceModifBase ):
    """ Conference start date/time modification
        When changing the start date / time, the _setParam method will be called by DateTimeModificationBase's _handleSet method.
        The _setParam method will return None (if there are no problems),
        or a Warning object if the event start date change was OK but there were side problems,
        such as an object observing the event start date change could not perform its task
        (Ex: a videoconference booking could not be moved in time according with the conference's time change)
        For this, it will check the 'dateChangeNotificationProblems' context variable.
    """
    def _checkParams(self):

        ConferenceModifBase._checkParams(self)

        pm = ParameterManager(self._params.get('value'), timezone=self._conf.getTimezone())

        self._startDate = pm.extract('startDate', pType=datetime.datetime)
        self._endDate = pm.extract('endDate', pType=datetime.datetime)

    def _getAnswer(self):

        ContextManager.set('dateChangeNotificationProblems', {})

        if (self._startDate > self._endDate):
            raise ServiceError("ERR-E3",
                               "Date/time of start cannot " +
                               "be greater than date/time of end")

        try:
            self._target.setDates(self._startDate, self._endDate, moveEntries=1)
        except TimingError,e:
            raise ServiceError("ERR-E2", e.getMsg())

        dateChangeNotificationProblems = ContextManager.get('dateChangeNotificationProblems')

        if dateChangeNotificationProblems:

            warningContent = []
            for problemGroup in dateChangeNotificationProblems.itervalues():
                warningContent.extend(problemGroup)

            w = Warning(_('Warning'), [_('The start date of your event was changed correctly.'),
                                       _('However, there were the following problems:'),
                                       warningContent])

            return DictPickler.pickle(ResultWithWarning(self._params.get('value'), w))

        else:
            return self._params.get('value')

class ConferenceListUsedRooms( ConferenceDisplayBase ):
    """
    Get rooms that are used in the context of the conference:
     * Booked in CRBS
     * Already chosen in sessions
    """
    def _getAnswer( self ):
        """
        Calls _handle() on the derived classes, in order to make it happen. Provides
        them with self._value.
        """

        roomList = []
        roomList.extend(self._target.getRoomList())
        roomList.extend(map(lambda x: x._getName(), self._target.getBookedRooms()))

        return roomList


class ConferenceDateTimeEndModification( ConferenceDateTimeModificationBase ):
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
                               "Date/time of end cannot "+
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


class ConferenceListContributions (ConferenceListModificationBase):
    """ Returns a list of all contributions of a conference, ordered by id
    """
    def _checkParams(self):
        ConferenceListModificationBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._selTypes = pm.extract("selTypes", pType=list, allowEmpty = True) #ids of selected types
        self._selTracks = pm.extract("selTracks", pType=list, allowEmpty = True) #ids of selected tracks
        self._selSessions = pm.extract("selSessions", pType=list, allowEmpty = True) #ids of selected sessions

        self._typeShowNoValue = self._params.get("typeShowNoValue", True)
        self._trackShowNoValue = self._params.get("trackShowNoValue", True)
        self._sessionShowNoValue = self._params.get("sessionShowNoValue", True)

        self._showWithReferee = self._params.get("showWithReferee", False)
        self._showWithEditor = self._params.get("showWithEditor", False)
        self._showWithReviewer = self._params.get("showWithReviewer", False)

        self._poster = self._params.get("poster", False)
        self._posterShowNoValue = self._params.get("posterShowNoValue", True)

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
        if isOnlyReferee:
            filter["referee"] = self._getUser()
        elif self._showWithReferee:
            filter["referee"] = "any"
        else:
            filter["referee"] = None

        if self._showWithEditor:
            filter["editor"] = "any"
        else:
            filter["editor"] = None
        if self._showWithReviewer:
            filter["reviewer"] = "any"
        else:
            filter["reviewer"] = None


        #note by David: I added "if self._selTypes..." and the other ifs after this line,
        #in order to make the recording request load contributions work
        #but, it may break the paper reviewing module -> assign contributions filter
        if self._selTypes:
            filter["type"] = self._selTypes
        if self._selTracks:
            filter["track"] = self._selTracks
        if self._selSessions:
            filter["session"] = self._selSessions
        if self._poster:
            filter["poster"] = self._poster

        filterCrit = ContributionsReviewingFilterCrit(self._conf, filter)
        sortingCrit = contribFilters.SortingCriteria(["number"])

        if self._selTypes:
            filterCrit.getField("type").setShowNoValue( self._typeShowNoValue )
        if self._selTracks:
            filterCrit.getField("track").setShowNoValue( self._trackShowNoValue )
        if self._selSessions:
            filterCrit.getField("session").setShowNoValue( self._sessionShowNoValue )
        if self._poster:
            filterCrit.getField("poster").setShowNoValue( self._posterShowNoValue )

        filterCrit.getField("referee").setShowNoValue( not isOnlyReferee )

        f= filters.SimpleFilter(filterCrit, sortingCrit)
        contributions = f.apply(contributions)

        return DictPickler.pickle(contributions)

#########################
# Contribution filtering
#########################

class ContributionsReviewingFilterCrit(filters.FilterCriteria):
    _availableFields = {
        contribFilters.RefereeFilterField.getId() : contribFilters.RefereeFilterField,
        contribFilters.EditorFilterField.getId() : contribFilters.EditorFilterField,
        contribFilters.ReviewerFilterField.getId() : contribFilters.ReviewerFilterField,
        contribFilters.TypeFilterField.getId() : contribFilters.TypeFilterField,
        contribFilters.TrackFilterField.getId() : contribFilters.TrackFilterField,
        contribFilters.SessionFilterField.getId() : contribFilters.SessionFilterField,
        contribFilters.PosterFilterField.getId() : contribFilters.PosterFilterField
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

    def _getAnswer( self ):
        im = indexes.IndexesHolder()
        ch = ConferenceHolder()
        calIdx = im.getIndex("calendar")
        evtIds = calIdx.getObjectsIn(self._sDate, self._eDate)

        evtsByCateg={}
        for evtId in evtIds:
            try:
                evt = ch.getById(evtId)
                categs =evt.getOwnerList()
                categname =categs[0].getName()
                if not evtsByCateg.has_key(categname):
                    evtsByCateg[categname] = []
                evtsByCateg[categname].append((evt.getTitle().strip(),evt.getAdjustedStartDate().strftime('%d/%m/%Y %H:%M '),evt.getAdjustedEndDate().strftime('%d/%m/%Y %H:%M '), evt.getTimezone()))

            except Exception:
                continue
        return evtsByCateg


class ConferenceGetFieldsAndContribTypes(ConferenceModifBase):
    def _getAnswer( self ):
        afm = self._target.getAbstractMgr().getAbstractFieldsMgr()
        afmDict =  dict([(f.getId(), f.getName()) for f in afm.getFields()])
        cTypes = self._target.getContribTypeList()
        cTypesDict =  dict([(ct.getId(), ct.getName()) for ct in cTypes])
        return [afmDict, cTypesDict]


class ConferenceParticipationForm(ConferenceDisplayBase):
    def _getAnswer(self):

        params = {}

        if self._conf.getStartDate() < timezoneUtils.nowutc() :
            return """This event began on %s, you cannot apply for
                      participation after the event began."""%self._conf.getStartDate()

        if not self._conf.getParticipation().isAllowedForApplying() :
            return """Participation in this event is restricted to persons invited.
                      If you insist on taking part in this event, please contact the event manager."""

        p = wcomponents.WNewPerson()

        params["formAction"] = str(urlHandlers.UHConfParticipantsAddPending.getURL(self._conf))
        params["formTitle"] = None
        params["cancelButtonParams"] = """ type="button" id="cancelRegistrationButton" """

        params["titleValue"] = ""
        params["surNameValue"] = ""
        params["nameValue"] = ""
        params["emailValue"] = ""
        params["addressValue"] = ""
        params["affiliationValue"] = ""
        params["phoneValue"] = ""
        params["faxValue"] = ""

        user = self._getUser()
        if user is not None :
            params["titleValue"] = user.getTitle()
            params["surNameValue"] = user.getFamilyName()
            params["nameValue"] = user.getName()
            params["emailValue"] = user.getEmail()
            params["addressValue"] = user.getAddress()
            params["affiliationValue"] = user.getAffiliation()
            params["phoneValue"] = user.getTelephone()
            params["faxValue"] = user.getFax()

            params["disabledTitle"] = params["disabledSurName"] = True
            params["disabledName"] = params["disabledEmail"] = True
            params["disabledAddress"] = params["disabledPhone"] = True
            params["disabledFax"] = params["disabledAffiliation"] = True

        return p.getHTML(params)

methodMap = {
    "main.changeTitle": ConferenceTitleModification,
    "main.changeSupportEmail": ConferenceSupportEmailModification,
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
    "rooms.list" : ConferenceListUsedRooms,
    "contributions.list" : ConferenceListContributions,
    "pic.delete": ConferencePicDelete,
    "showConcurrentEvents": ShowConcurrentEvents,
#    "getFields": ConferenceGetFields,
    "getFieldsAndContribTypes": ConferenceGetFieldsAndContribTypes,
    "getParticipationForm": ConferenceParticipationForm
    }
