##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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

import re
import string
import urlparse
from flask import request

from MaKaC.common.url import URL, EndpointURL
from MaKaC.common.Configuration import Config
import MaKaC.user as user
from MaKaC.common.utils import utf8rep
from MaKaC.common.timezoneUtils import nowutc


class BooleanOnMixin:
    """Mixin to convert True to 'on' and remove False altogether."""
    _true = 'on'

    @classmethod
    def _translateParams(cls, params):
        return dict((key, cls._true if value is True else value)
                    for key, value in params.iteritems()
                    if value is not False)


class BooleanTrueMixin:
    _true = 'True'


class URLHandler(object):
    """This is the generic URLHandler class. It contains information about the
        concrete URL pointing to the request handler and gives basic methods to
        generate the URL from some target objects complying to the Locable
        interface.
       Actually, URLHandlers must never be intanciated as all their methods are
        classmethods.

       Attributes:
        _relativeURL - (string) Contains the relative (the part which is
            variable from the root) URL pointing to the corresponding request
            handler.
        _endpoint - (string) Contains the name of a Flask endpoint.
        _defaultParams - (dict) Default params (overwritten by kwargs)
        _fragment - (string) URL fragment to set
    """
    _relativeURL = None
    _endpoint = None
    _defaultParams = {}
    _fragment = False

    @classmethod
    def getRelativeURL(cls):
        """Gives the relative URL (URL part which is carachteristic) for the
            corresponding request handler.
        """
        return cls._relativeURL

    @classmethod
    def _getURL(cls, _force_secure=None, **params):
        """ Gives the full URL for the corresponding request handler.

            Parameters:
                _force_secure - (bool) create a secure url if possible
                params - (dict) parameters to be added to the URL.
        """

        secure = _force_secure if _force_secure is not None else request.is_secure
        if not Config.getInstance().getBaseSecureURL():
            secure = False

        if not cls._endpoint:
            # Legacy UH containing a relativeURL
            cfg = Config.getInstance()
            baseURL = cfg.getBaseSecureURL() if secure else cfg.getBaseURL()
            url = URL('%s/%s' % (baseURL, cls.getRelativeURL()), **params)
        else:
            assert not cls.getRelativeURL()
            url = EndpointURL(cls._endpoint, secure, params)

        if cls._fragment:
            url.fragment = cls._fragment

        return url

    @classmethod
    def _translateParams(cls, params):
        # When overriding this you may return a new dict or modify the existing one in-place.
        # But in any case, you must return the final dict.
        return params

    @classmethod
    def _getParams(cls, target, params):
        params = dict(cls._defaultParams, **params)
        if target is not None:
            params.update(target.getLocator())
        params = cls._translateParams(params)
        return params

    @classmethod
    def getURL(cls, target=None, **params):
        """Gives the full URL for the corresponding request handler. In case
            the target parameter is specified it will append to the URL the
            the necessary parameters to make the target be specified in the url.

            Parameters:
                target - (Locable) Target object which must be uniquely
                    specified in the URL so the destination request handler
                    is able to retrieve it.
                params - (Dict) parameters to be added to the URL.
        """

        return cls._getURL(**cls._getParams(target, params))


class SecureURLHandler(URLHandler):
    @classmethod
    def getURL(cls, target=None, **params):
        return cls._getURL(_force_secure=True, **cls._getParams(target, params))


class OptionallySecureURLHandler(URLHandler):
    @classmethod
    def getURL(cls, target=None, secure=False, **params):
        return cls._getURL(_force_secure=secure, **cls._getParams(target, params))


# Hack to allow secure Indico on non-80 ports
def setSSLPort(url):
    """
    Returns url with port changed to SSL one.
    If url has no port specified, it returns the same url.
    SSL port is extracted from loginURL (MaKaCConfig)
    """
    # Set proper PORT for images requested via SSL
    sslURL = Config.getInstance().getLoginURL() or Config.getInstance().getBaseSecureURL()
    sslPort = ':%d' % (urlparse.urlsplit(sslURL).port or 443)

    # If there is NO port, nothing will happen (production indico)
    # If there IS a port, it will be replaced with proper SSL one, taken from loginURL
    regexp = ':\d{2,5}'   # Examples:   :8080   :80   :65535
    return re.sub(regexp, sslPort, url)


class UHWelcome(URLHandler):
    _endpoint = 'misc.index'


class UHSignIn(URLHandler):
    _endpoint = 'user.signIn'

    @classmethod
    def getURL(cls, returnURL=''):
        if Config.getInstance().getLoginURL():
            url = URL(Config.getInstance().getLoginURL())
        else:
            url = cls._getURL()
        if returnURL:
            url.addParam('returnURL', returnURL)
        return url


class UHActiveAccount(URLHandler):
    _endpoint = 'user.signIn-active'


class UHSendActivation(URLHandler):
    _endpoint = 'user.signIn-sendActivation'


class UHDisabledAccount(URLHandler):
    _endpoint = 'user.signIn-disabledAccount'


class UHSendLogin(URLHandler):
    _endpoint = 'user.signIn-sendLogin'


class UHUnactivatedAccount(URLHandler):
    _endpoint = 'user.signIn-unactivatedAccount'


class UHSignOut(URLHandler):
    _endpoint = 'user.logOut'

    @classmethod
    def getURL(cls, returnURL=''):
        url = cls._getURL()
        if returnURL:
            url.addParam('returnURL', returnURL)
        return url


class UHOAuthRequestToken(URLHandler):
    _endpoint = 'oauth.oauth-request_token'


class UHOAuthAuthorization(URLHandler):
    _endpoint = 'oauth.oauth-authorize'


class UHOAuthAccessTokenURL(URLHandler):
    _endpoint = 'oauth.oauth-access_token'


class UHOAuthAuthorizeConsumer(URLHandler):
    _endpoint = 'oauth.oauth-authorize_consumer'


class UHOAuthThirdPartyAuth(URLHandler):
    _endpoint = 'oauth.oauth-thirdPartyAuth'


class UHOAuthUserThirdPartyAuth(URLHandler):
    _endpoint = 'oauth.oauth-userThirdPartyAuth'


class UHIndicoNews(URLHandler):
    _endpoint = 'misc.news'


class UHConferenceHelp(URLHandler):
    _endpoint = 'misc.help'


class UHCalendar(URLHandler):
    _endpoint = 'category.wcalendar'

    @classmethod
    def getURL(cls, categList=None):
        url = cls._getURL()
        if not categList:
            categList = []
        lst = [categ.getId() for categ in categList]
        url.addParam('selCateg', lst)
        return url


class UHCalendarSelectCategories(URLHandler):
    _endpoint = 'category.wcalendar-select'


class UHConferenceCreation(URLHandler):
    _endpoint = 'event_creation.conferenceCreation'

    @classmethod
    def getURL(cls, target):
        url = cls._getURL()
        if target is not None:
            url.addParams(target.getLocator())
        return url


class UHConferencePerformCreation(URLHandler):
    _endpoint = 'event_creation.conferenceCreation-createConference'


class UHConferenceDisplay(URLHandler):
    _endpoint = 'event.conferenceDisplay'


class UHNextEvent(URLHandler):
    _endpoint = 'event.conferenceDisplay-next'


class UHPreviousEvent(URLHandler):
    _endpoint = 'event.conferenceDisplay-prev'


class UHConferenceOverview(URLHandler):
    _endpoint = 'event.conferenceDisplay-overview'


class UHConferenceEmail(URLHandler):
    _endpoint = 'event.EMail'


class UHConferenceSendEmail(URLHandler):
    _endpoint = 'event.EMail-send'


class UHRegistrantsSendEmail(URLHandler):
    _endpoint = 'legacy.EMail-sendreg'


class UHConvenersSendEmail(URLHandler):
    _endpoint = 'event_mgmt.EMail-sendconvener'


class UHContribParticipantsSendEmail(URLHandler):
    _endpoint = 'event_mgmt.EMail-sendcontribparticipants'


class UHConferenceOtherViews(URLHandler):
    _endpoint = 'event.conferenceOtherViews'


class UHConferenceLogo(URLHandler):
    _endpoint = 'event.conferenceDisplay-getLogo'


class UHConferenceCSS(URLHandler):
    _endpoint = 'event.conferenceDisplay-getCSS'


class UHConferencePic(URLHandler):
    _endpoint = 'event.conferenceDisplay-getPic'


class UHConfModifPreviewCSS(URLHandler):
    _endpoint = 'event_mgmt.confModifDisplay-previewCSS'


class UHCategoryIcon(URLHandler):
    _endpoint = 'category.categoryDisplay-getIcon'


class UHConferenceModification(URLHandler):
    _endpoint = 'event_mgmt.conferenceModification'


class UHConfModifShowMaterials(URLHandler):
    _endpoint = 'legacy.conferenceModification-materialsShow'


class UHConfModifAddMaterials(URLHandler):
    _endpoint = 'legacy.conferenceModification-materialsAdd'

# ============================================================================
# ROOM BOOKING ===============================================================
# ============================================================================

# Free standing ==============================================================


class UHRoomBookingMapOfRooms(URLHandler):
    _endpoint = 'rooms.roomBooking-mapOfRooms'


class UHRoomBookingMapOfRoomsWidget(URLHandler):
    _endpoint = 'rooms.roomBooking-mapOfRoomsWidget'


class UHRoomBookingWelcome(URLHandler):
    _endpoint = 'rooms.roomBooking'


class UHRoomBookingSearch4Rooms(URLHandler):
    _endpoint = 'rooms.roomBooking-search4Rooms'
    _defaultParams = dict(forNewBooking=False)


class UHRoomBookingSearch4Bookings(URLHandler):
    _endpoint = 'rooms.roomBooking-search4Bookings'


class UHRoomBookingBookRoom(URLHandler):
    _endpoint = 'rooms.roomBooking-bookRoom'


class UHRoomBookingRoomList(BooleanOnMixin, URLHandler):
    _endpoint = 'rooms.roomBooking-roomList'


class UHRoomBookingBookingList(URLHandler):
    _endpoint = 'rooms.roomBooking-bookingList'

    @classmethod
    def getURL(cls, onlyMy=False, newBooking=False, ofMyRooms=False, onlyPrebookings=False, autoCriteria=False,
               newParams=None, today=False, allRooms=False):
        """
        onlyMy - only bookings of the current user
        ofMyRooms - only bookings for rooms managed by the current user
        autoCriteria - some reasonable constraints, like "only one month ahead"
        """
        url = cls._getURL()
        if onlyMy:
            url.addParam('onlyMy', 'on')
        if newBooking:
            url.addParam('newBooking', 'on')
        if ofMyRooms:
            url.addParam('ofMyRooms', 'on')
        if onlyPrebookings:
            url.addParam('onlyPrebookings', 'on')
        if autoCriteria:
            url.addParam('autoCriteria', 'True')
        if today:
            url.addParam('day', 'today')
        if allRooms:
            url.addParam('roomGUID', 'allRooms')
        if newParams:
            url.setParams(newParams)
        return url


class UHRoomBookingBookingListForBooking(UHRoomBookingBookingList):
    _endpoint = 'rooms.roomBooking-bookingListForBooking'


class UHRoomBookingRoomDetails(BooleanTrueMixin, URLHandler):
    _endpoint = 'rooms.roomBooking-roomDetails'


class UHRoomBookingRoomStats(URLHandler):
    _endpoint = 'rooms.roomBooking-roomStats'


class UHRoomBookingBookingDetails(URLHandler):
    _endpoint = 'rooms.roomBooking-bookingDetails'

    @classmethod
    def _translateParams(cls, params):
        # confId is apparently unused and thus just ugly
        params.pop('confId', None)
        return params



class UHRoomBookingRoomForm(URLHandler):
    _endpoint = 'rooms_admin.roomBooking-roomForm'


class UHRoomBookingSaveRoom(URLHandler):
    _endpoint = 'rooms_admin.roomBooking-saveRoom'


class UHRoomBookingDeleteRoom(URLHandler):
    _endpoint = 'rooms_admin.roomBooking-deleteRoom'


class UHRoomBookingBookingForm(URLHandler):
    _endpoint = 'rooms.roomBooking-bookingForm'


class UHRoomBookingModifyBookingForm(URLHandler):
    _endpoint = 'rooms.roomBooking-modifyBookingForm'


class UHRoomBookingSaveBooking(URLHandler):
    _endpoint = 'rooms.roomBooking-saveBooking'


class UHRoomBookingDeleteBooking(URLHandler):
    _endpoint = 'rooms.roomBooking-deleteBooking'


class UHRoomBookingCloneBooking(URLHandler):
    _endpoint = 'rooms.roomBooking-cloneBooking'


class UHRoomBookingCancelBooking(URLHandler):
    _endpoint = 'rooms.roomBooking-cancelBooking'


class UHRoomBookingAcceptBooking(URLHandler):
    _endpoint = 'rooms.roomBooking-acceptBooking'


class UHRoomBookingRejectBooking(URLHandler):
    _endpoint = 'rooms.roomBooking-rejectBooking'


class UHRoomBookingRejectAllConflicting(URLHandler):
    _endpoint = 'rooms.roomBooking-rejectAllConflicting'


class UHRoomBookingRejectBookingOccurrence(URLHandler):
    _endpoint = 'rooms.roomBooking-rejectBookingOccurrence'


class UHRoomBookingCancelBookingOccurrence(URLHandler):
    _endpoint = 'rooms.roomBooking-cancelBookingOccurrence'


class UHRoomBookingStatement(URLHandler):
    _endpoint = 'rooms.roomBooking-statement'


# RB Administration
class UHRoomBookingPluginAdmin(URLHandler):
    _endpoint = 'rooms_admin.roomBookingPluginAdmin'


class UHRoomBookingModuleActive(URLHandler):
    _endpoint = 'rooms_admin.roomBookingPluginAdmin-switchRoomBookingModuleActive'


class UHRoomBookingPlugAdminZODBSave(URLHandler):
    _endpoint = 'rooms_admin.roomBookingPluginAdmin-zodbSave'


class UHRoomBookingAdmin(URLHandler):
    _endpoint = 'rooms_admin.roomBooking-admin'


class UHRoomBookingAdminLocation(URLHandler):
    _endpoint = 'rooms_admin.roomBooking-adminLocation'


class UHRoomBookingSetDefaultLocation(URLHandler):
    _endpoint = 'rooms_admin.roomBooking-setDefaultLocation'


class UHRoomBookingSaveLocation(URLHandler):
    _endpoint = 'rooms_admin.roomBooking-saveLocation'


class UHRoomBookingDeleteLocation(URLHandler):
    _endpoint = 'rooms_admin.roomBooking-deleteLocation'


class UHRoomBookingSaveEquipment(URLHandler):
    _endpoint = 'rooms_admin.roomBooking-saveEquipment'


class UHRoomBookingDeleteEquipment(URLHandler):
    _endpoint = 'rooms_admin.roomBooking-deleteEquipment'


class UHRoomBookingSaveCustomAttributes(URLHandler):
    _endpoint = 'rooms_admin.roomBooking-saveCustomAttributes'


class UHRoomBookingDeleteCustomAttribute(URLHandler):
    _endpoint = 'rooms_admin.roomBooking-deleteCustomAttribute'


class UHRoomBookingBlockingsMyRooms(URLHandler):
    _endpoint = 'rooms.roomBooking-blockingsForMyRooms'


class UHRoomBookingBlockingsBlockingDetails(URLHandler):
    _endpoint = 'rooms.roomBooking-blockingDetails'


class UHRoomBookingBlockingList(BooleanOnMixin, URLHandler):
    _endpoint = 'rooms.roomBooking-blockingList'
    _defaultParams = dict(onlyThisYear=True)


class UHRoomBookingBlockingForm(URLHandler):
    _endpoint = 'rooms.roomBooking-blockingForm'


class UHRoomBookingDeleteBlocking(URLHandler):
    _endpoint = 'rooms.roomBooking-deleteBlocking'

# For the event ==============================================================

class UHConfModifRoomBookingBase(URLHandler):
    @classmethod
    def _getURL(cls, target=None, **params):
        url = super(UHConfModifRoomBookingBase, cls)._getURL(**params)
        if target:
            url.setParams(target.getLocator())
        conf = ContextManager.get("currentConference", None)
        if conf:
            url.addParams(conf.getLocator())
        return url

class UHConfModifRoomBookingChooseEvent(URLHandler):
    _endpoint = 'legacy.conferenceModification-roomBookingChooseEvent'


class UHConfModifRoomBookingSearch4Rooms(BooleanTrueMixin, URLHandler):
    _endpoint = 'legacy.conferenceModification-roomBookingSearch4Rooms'


class UHConfModifRoomBookingList(URLHandler):
    _endpoint = 'legacy.conferenceModification-roomBookingList'


class UHConfModifRoomBookingRoomList(URLHandler):
    _endpoint = 'legacy.conferenceModification-roomBookingRoomList'


class UHConfModifRoomBookingDetails(URLHandler):
    _endpoint = 'legacy.conferenceModification-roomBookingDetails'


class UHConfModifRoomBookingRoomDetails(UHConfModifRoomBookingBase):
    _endpoint = 'legacy.conferenceModification-roomBookingRoomDetails'


class UHConfModifRoomBookingBookingForm(UHConfModifRoomBookingBase):
    _endpoint = 'legacy.conferenceModification-roomBookingBookingForm'


class UHConfModifRoomBookingCloneBooking(UHConfModifRoomBookingBase):
    _endpoint = 'legacy.conferenceModification-roomBookingCloneBooking'

    @classmethod
    def getURL(cls, target=None, conf=None, **params):
        url = cls._getURL(**cls._getParams(target, params))
        if conf is not None:
            url.addParams(conf.getLocator())
        return url


class UHConfModifRoomBookingSaveBooking(URLHandler):
    _endpoint = 'legacy.conferenceModification-roomBookingSaveBooking'


class UHRoomPhoto(URLHandler):
    _endpoint = 'rooms.photo_large'

    @classmethod
    def getURL(cls, target=None):
        return super(UHRoomPhoto, cls).getURL(room=target)


class UHRoomPhotoSmall(URLHandler):
    _endpoint = 'rooms.photo_small'

    @classmethod
    def getURL(cls, target=None):
        return super(UHRoomPhotoSmall, cls).getURL(room=target)


class UHConfModSessionSlots(URLHandler):
    _endpoint = 'legacy.conferenceModification-sessionSlots'


class UHConferenceClose(URLHandler):
    _endpoint = 'event_mgmt.conferenceModification-close'


class UHConferenceModificationClosed(URLHandler):
    _endpoint = 'legacy.conferenceModification-modificationClosed'


class UHConferenceOpen(URLHandler):
    _endpoint = 'event_mgmt.conferenceModification-open'


class UHConfDataModif(URLHandler):
    _endpoint = 'event_mgmt.conferenceModification-data'


class UHConfScreenDatesEdit(URLHandler):
    _endpoint = 'event_mgmt.conferenceModification-screenDates'


class UHConfPerformDataModif(URLHandler):
    _endpoint = 'event_mgmt.conferenceModification-dataPerform'


class UHConfAddContribType(URLHandler):
    _endpoint = 'event_mgmt.conferenceModification-addContribType'


class UHConfRemoveContribType(URLHandler):
    _endpoint = 'event_mgmt.conferenceModification-removeContribType'


class UHConfEditContribType(URLHandler):
    _endpoint = 'event_mgmt.conferenceModification-editContribType'


class UHConfSectionsSettings(URLHandler):
    _endpoint = 'legacy.conferenceModification-sectionsSettings'


class UHConfModifCFAOptFld(URLHandler):
    _endpoint = 'legacy.confModifCFA-abstractFields'


class UHConfModifCFAAddOptFld(URLHandler):
    _endpoint = 'legacy.confModifCFA-addAbstractField'


class UHConfModifCFAPerformAddOptFld(URLHandler):
    _endpoint = 'legacy.confModifCFA-performAddAbstractField'


class UHConfModifCFAEditOptFld(URLHandler):
    _endpoint = 'legacy.confModifCFA-editAbstractField'


class UHConfModifCFARemoveOptFld(URLHandler):
    _endpoint = 'legacy.confModifCFA-removeAbstractField'


class UHConfModifCFAAbsFieldUp(URLHandler):
    _endpoint = 'legacy.confModifCFA-absFieldUp'


class UHConfModifCFAAbsFieldDown(URLHandler):
    _endpoint = 'legacy.confModifCFA-absFieldDown'


class UHConfModifProgram(URLHandler):
    _endpoint = 'legacy.confModifProgram'


class UHConfModifCFA(URLHandler):
    _endpoint = 'legacy.confModifCFA'


class UHConfModifCFAPreview(URLHandler):
    _endpoint = 'legacy.confModifCFA-preview'


class UHConfCFAChangeStatus(URLHandler):
    _endpoint = 'legacy.confModifCFA-changeStatus'


class UHConfCFASwitchMultipleTracks(URLHandler):
    _endpoint = 'legacy.confModifCFA-switchMultipleTracks'


class UHConfCFAMakeTracksMandatory(URLHandler):
    _endpoint = 'legacy.confModifCFA-makeTracksMandatory'


class UHConfCFAAllowAttachFiles(URLHandler):
    _endpoint = 'legacy.confModifCFA-switchAttachFiles'


class UHAbstractAttachmentFileAccess(URLHandler):
    _endpoint = 'event.abstractDisplay-getAttachedFile'


class UHConfCFAShowSelectAsSpeaker(URLHandler):
    _endpoint = 'legacy.confModifCFA-switchShowSelectSpeaker'


class UHConfCFASelectSpeakerMandatory(URLHandler):
    _endpoint = 'legacy.confModifCFA-switchSelectSpeakerMandatory'


class UHConfCFAAttachedFilesContribList(URLHandler):
    _endpoint = 'legacy.confModifCFA-switchShowAttachedFiles'


class UHCFAManagementAddType(URLHandler):
    _endpoint = 'legacy.confModifCFA-addType'


class UHCFAManagementRemoveType(URLHandler):
    _endpoint = 'legacy.confModifCFA-removeType'


class UHCFADataModification(URLHandler):
    _endpoint = 'legacy.confModifCFA-modifyData'


class UHCFAPerformDataModification(URLHandler):
    _endpoint = 'legacy.confModifCFA-performModifyData'


class UHConfAbstractManagment(URLHandler):
    _endpoint = 'legacy.abstractsManagment'


class UHConfAbstractList(URLHandler):
    _endpoint = 'legacy.abstractsManagment'


class UHAbstractSubmission(URLHandler):
    _endpoint = 'event.abstractSubmission'


class UHAbstractSubmissionConfirmation(URLHandler):
    _endpoint = 'event.abstractSubmission-confirmation'


class UHAbstractDisplay(URLHandler):
    _endpoint = 'event.abstractDisplay'


class UHAbstractDisplayPDF(URLHandler):
    _endpoint = 'event.abstractDisplay-pdf'


class UHAbstractConfManagerDisplayPDF(URLHandler):
    _endpoint = 'legacy.abstractManagment-abstractToPDF'


class UHAbstractConfSelectionAction(URLHandler):
    _endpoint = 'legacy.abstractsManagment-abstractsActions'


class UHAbstractsConfManagerDisplayParticipantList(URLHandler):
    _endpoint = 'legacy.abstractsManagment-participantList'


class UHAbstractsTrackManagerParticipantList(URLHandler):
    _endpoint = 'legacy.trackModifAbstracts-participantList'


class UHAbstractsTrackManagerDisplayPDF(URLHandler):
    _endpoint = 'legacy.trackModifAbstracts-abstractsToPDF'


class UHAbstractstrackManagerDisplayPDF(URLHandler):
    _endpoint = 'legacy.trackModifAbstracts-abstractsToPDF'


class UHUserAbstracts(URLHandler):
    _endpoint = 'event.userAbstracts'


class UHUserAbstractsPDF(URLHandler):
    _endpoint = 'event.userAbstracts-pdf'


class UHAbstractModify(URLHandler):
    _endpoint = 'event.abstractModify'


class UHCFAAbstractManagment(URLHandler):
    _endpoint = 'legacy.abstractManagment'


class UHAbstractManagment(URLHandler):
    _endpoint = 'legacy.abstractManagment'


class UHAbstractManagmentAccept(URLHandler):
    _endpoint = 'legacy.abstractManagment-accept'


class UHAbstractManagmentAcceptMultiple(URLHandler):
    _endpoint = 'legacy.abstractManagment-acceptMultiple'


class UHAbstractManagmentRejectMultiple(URLHandler):
    _endpoint = 'legacy.abstractManagment-rejectMultiple'


class UHAbstractManagmentReject(URLHandler):
    _endpoint = 'legacy.abstractManagment-reject'


class UHAbstractManagmentChangeTrack(URLHandler):
    _endpoint = 'legacy.abstractManagment-changeTrack'


class UHAbstractTrackProposalManagment(URLHandler):
    _endpoint = 'legacy.abstractManagment-trackProposal'


class UHAbstractTrackOrderByRating(URLHandler):
    _endpoint = 'legacy.abstractManagment-orderByRating'


class UHAbstractDirectAccess(URLHandler):
    _endpoint = 'legacy.abstractManagment-directAccess'


class UHAbstractToXML(URLHandler):
    _endpoint = 'legacy.abstractManagment-xml'


class UHAbstractSubmissionDisplay(URLHandler):
    _endpoint = 'event.abstractSubmission'


class UHConfAddTrack(URLHandler):
    _endpoint = 'legacy.confModifProgram-addTrack'


class UHConfDelTracks(URLHandler):
    _endpoint = 'legacy.confModifProgram-deleteTracks'


class UHConfPerformAddTrack(URLHandler):
    _endpoint = 'legacy.confModifProgram-performAddTrack'


class UHTrackModification(URLHandler):
    _endpoint = 'legacy.trackModification'


class UHTrackModifAbstracts(URLHandler):
    _endpoint = 'legacy.trackModifAbstracts'


class UHTrackAbstractBase(URLHandler):
    @classmethod
    def getURL(cls, track, abstract):
        url = cls._getURL()
        url.setParams(track.getLocator())
        url.addParam('abstractId', abstract.getId())
        return url


class UHTrackAbstractModif(UHTrackAbstractBase):
    _endpoint = 'legacy.trackAbstractModif'


class UHAbstractTrackManagerDisplayPDF(UHTrackAbstractBase):
    _endpoint = 'legacy.trackAbstractModif-abstractToPDF'


class UHAbstractsTrackManagerAction(URLHandler):
    _endpoint = 'legacy.trackAbstractModif-abstractAction'


class UHTrackAbstractPropToAcc(UHTrackAbstractBase):
    _endpoint = 'legacy.trackAbstractModif-proposeToBeAcc'


class UHTrackAbstractPropToRej(UHTrackAbstractBase):
    _endpoint = 'legacy.trackAbstractModif-proposeToBeRej'


class UHTrackAbstractAccept(UHTrackAbstractBase):
    _endpoint = 'legacy.trackAbstractModif-accept'


class UHTrackAbstractReject(UHTrackAbstractBase):
    _endpoint = 'legacy.trackAbstractModif-reject'


class UHTrackAbstractDirectAccess(URLHandler):
    _endpoint = 'legacy.trackAbstractModif-directAccess'


class UHTrackAbstractPropForOtherTrack(UHTrackAbstractBase):
    _endpoint = 'legacy.trackAbstractModif-proposeForOtherTracks'


class UHTrackModifCoordination(URLHandler):
    _endpoint = 'legacy.trackModifCoordination'


class UHTrackDataModif(URLHandler):
    _endpoint = 'legacy.trackModification-modify'


class UHTrackPerformDataModification(URLHandler):
    _endpoint = 'legacy.trackModification-performModify'


class UHTrackAbstractModIntComments(UHTrackAbstractBase):
    _endpoint = 'legacy.trackAbstractModif-comments'


class UHConfModifSchedule(URLHandler):
    _endpoint = 'legacy.confModifSchedule'


class UHConfModifScheduleCustomizePDF(URLHandler):
    _endpoint = 'legacy.confModifSchedule-customizePdf'


class UHContribConfSelectionAction(URLHandler):
    _endpoint = 'legacy.confModifContribList-contribsActions'


class UHContribsConfManagerDisplayPDF(URLHandler):
    _endpoint = 'legacy.confModifContribList-contribsToPDF'


class UHContribsConfManagerDisplayMenuPDF(URLHandler):
    _endpoint = 'legacy.confModifContribList-contribsToPDFMenu'


class UHContribsConfManagerDisplayParticipantList(URLHandler):
    _endpoint = 'legacy.confModifContribList-participantList'


class UHSessionClose(URLHandler):
    _endpoint = 'legacy.sessionModification-close'


class UHSessionOpen(URLHandler):
    _endpoint = 'legacy.sessionModification-open'


class UHSessionCreation(URLHandler):
    _endpoint = 'legacy.confModifSchedule'


class UHContribCreation(URLHandler):
    _endpoint = 'legacy.confModifSchedule'


class UHContribToXMLConfManager(URLHandler):
    _endpoint = 'legacy.contributionModification-xml'


class UHContribToXML(URLHandler):
    _endpoint = 'event.contributionDisplay-xml'


class UHContribToiCal(URLHandler):
    _endpoint = 'event.contributionDisplay-ical'


class UHContribToPDFConfManager(URLHandler):
    _endpoint = 'legacy.contributionModification-pdf'


class UHContribToPDF(URLHandler):
    _endpoint = 'event.contributionDisplay-pdf'


class UHContribModifAC(URLHandler):
    _endpoint = 'legacy.contributionAC'


class UHContributionSetVisibility(URLHandler):
    _endpoint = 'legacy.contributionAC-setVisibility'


class UHContribModifMaterialMgmt(URLHandler):
    _endpoint = 'legacy.contributionModification-materials'


class UHContribModifAddMaterials(URLHandler):
    _endpoint = 'legacy.contributionModification-materialsAdd'


class UHContributionRemoveMaterials(URLHandler):
    _endpoint = 'legacy.contributionModification-removeMaterials'


# <Deprecated>
class UHContributionAddMaterial(URLHandler):
    _endpoint = 'legacy.contributionModification-addMaterial'


class UHContributionPerformAddMaterial(URLHandler):
    _endpoint = 'legacy.contributionModification-performAddMaterial'
# </Deprecated>


class UHContribModifSubCont(URLHandler):
    _endpoint = 'legacy.contributionModifSubCont'


class UHContribAddSubCont(URLHandler):
    _endpoint = 'legacy.contributionModifSubCont-add'


class UHContribCreateSubCont(URLHandler):
    _endpoint = 'legacy.contributionModifSubCont-create'


class UHContribUpSubCont(URLHandler):
    _endpoint = 'legacy.contributionModifSubCont-up'


class UHContribDownSubCont(URLHandler):
    _endpoint = 'legacy.contributionModifSubCont-Down'


class UHSubContribActions(URLHandler):
    _endpoint = 'legacy.contributionModifSubCont-actionSubContribs'


class UHContribModifTools(URLHandler):
    _endpoint = 'legacy.contributionTools'


class UHContributionDataModif(URLHandler):
    _endpoint = 'legacy.contributionModification-modifData'


class UHContributionDataModification(URLHandler):
    _endpoint = 'legacy.contributionModification-data'


class UHConfModifAC(URLHandler):
    _endpoint = 'event_mgmt.confModifAC'


class UHConfSetVisibility(URLHandler):
    _endpoint = 'event_mgmt.confModifAC-setVisibility'


class UHConfGrantSubmissionToAllSpeakers(URLHandler):
    _endpoint = 'event_mgmt.confModifAC-grantSubmissionToAllSpeakers'


class UHConfRemoveAllSubmissionRights(URLHandler):
    _endpoint = 'event_mgmt.confModifAC-removeAllSubmissionRights'


class UHConfGrantModificationToAllConveners(URLHandler):
    _endpoint = 'event_mgmt.confModifAC-grantModificationToAllConveners'


class UHConfModifCoordinatorRights(URLHandler):
    _endpoint = 'event_mgmt.confModifAC-modifySessionCoordRights'


class UHConfModifTools(URLHandler):
    _endpoint = 'event_mgmt.confModifTools'


class UHConfModifParticipants(URLHandler):
    _endpoint = 'legacy.confModifParticipants'


class UHConfModifLog(URLHandler):
    _endpoint = 'event_mgmt.confModifLog'


class UHInternalPageDisplay(URLHandler):
    _endpoint = 'event.internalPage'


class UHConfModifDisplay(URLHandler):
    _endpoint = 'event_mgmt.confModifDisplay'


class UHConfModifDisplayCustomization(URLHandler):
    _endpoint = 'event_mgmt.confModifDisplay-custom'


class UHConfModifDisplayMenu(URLHandler):
    _endpoint = 'event_mgmt.confModifDisplay-menu'


class UHConfModifDisplayResources(URLHandler):
    _endpoint = 'event_mgmt.confModifDisplay-resources'


class UHConfModifDisplayConfHeader(URLHandler):
    _endpoint = 'event_mgmt.confModifDisplay-confHeader'


class UHConfModifDisplayAddLink(URLHandler):
    _endpoint = 'event_mgmt.confModifDisplay-addLink'


class UHConfModifDisplayAddPage(URLHandler):
    _endpoint = 'event_mgmt.confModifDisplay-addPage'


class UHConfModifDisplayModifyData(URLHandler):
    _endpoint = 'event_mgmt.confModifDisplay-modifyData'


class UHConfModifDisplayModifySystemData(URLHandler):
    _endpoint = 'event_mgmt.confModifDisplay-modifySystemData'


class UHConfModifDisplayAddSpacer(URLHandler):
    _endpoint = 'event_mgmt.confModifDisplay-addSpacer'


class UHConfModifDisplayRemoveLink(URLHandler):
    _endpoint = 'event_mgmt.confModifDisplay-removeLink'


class UHConfModifDisplayToggleLinkStatus(URLHandler):
    _endpoint = 'event_mgmt.confModifDisplay-toggleLinkStatus'


class UHConfModifDisplayToggleHomePage(URLHandler):
    _endpoint = 'event_mgmt.confModifDisplay-toggleHomePage'


class UHConfModifDisplayUpLink(URLHandler):
    _endpoint = 'event_mgmt.confModifDisplay-upLink'


class UHConfModifDisplayDownLink(URLHandler):
    _endpoint = 'event_mgmt.confModifDisplay-downLink'


class UHConfModifFormatTitleBgColor(URLHandler):
    _endpoint = 'event_mgmt.confModifDisplay-formatTitleBgColor'


class UHConfModifFormatTitleTextColor(URLHandler):
    _endpoint = 'event_mgmt.confModifDisplay-formatTitleTextColor'


class UHConfDeletion(URLHandler):
    _endpoint = 'event_mgmt.confModifTools-delete'


class UHConfClone(URLHandler):
    _endpoint = 'event_mgmt.confModifTools-clone'


class UHConfPerformCloning(URLHandler):
    _endpoint = 'event_mgmt.confModifTools-performCloning'


class UHConfAllSessionsConveners(URLHandler):
    _endpoint = 'event_mgmt.confModifTools-allSessionsConveners'


class UHConfAllSessionsConvenersAction(URLHandler):
    _endpoint = 'event_mgmt.confModifTools-allSessionsConvenersAction'


class UHConfAllSpeakers(URLHandler):
    _endpoint = 'event_mgmt.confModifListings-allSpeakers'


class UHConfAllSpeakersAction(URLHandler):
    _endpoint = 'event_mgmt.confModifListings-allSpeakersAction'


class UHConfDisplayAlarm(URLHandler):
    _endpoint = 'event_mgmt.confModifTools-displayAlarm'


class UHConfAddAlarm(URLHandler):
    _endpoint = 'event_mgmt.confModifTools-addAlarm'


class UHSaveAlarm(URLHandler):
    _endpoint = 'event_mgmt.confModifTools-saveAlarm'


class UHModifySaveAlarm(URLHandler):
    _endpoint = 'event_mgmt.confModifTools-modifySaveAlarm'


class UHSendAlarmNow(URLHandler):
    _endpoint = 'event_mgmt.confModifTools-sendAlarmNow'


class UHConfDeleteAlarm(URLHandler):
    _endpoint = 'event_mgmt.confModifTools-deleteAlarm'


class UHConfModifyAlarm(URLHandler):
    _endpoint = 'event_mgmt.confModifTools-modifyAlarm'


class UHSaveLogo(URLHandler):
    _endpoint = 'event_mgmt.confModifDisplay-saveLogo'


class UHRemoveLogo(URLHandler):
    _endpoint = 'event_mgmt.confModifDisplay-removeLogo'


class UHSaveCSS(URLHandler):
    _endpoint = 'event_mgmt.confModifDisplay-saveCSS'


class UHUseCSS(URLHandler):
    _endpoint = 'event_mgmt.confModifDisplay-useCSS'


class UHRemoveCSS(URLHandler):
    _endpoint = 'event_mgmt.confModifDisplay-removeCSS'


class UHSavePic(URLHandler):
    _endpoint = 'event_mgmt.confModifDisplay-savePic'


class UHConfModifParticipantsSetup(URLHandler):
    _endpoint = 'legacy.confModifParticipants-setup'


class UHConfModifParticipantsPending(URLHandler):
    _endpoint = 'legacy.confModifParticipants-pendingParticipants'


class UHConfModifParticipantsDeclined(URLHandler):
    _endpoint = 'legacy.confModifParticipants-declinedParticipants'


class UHConfModifParticipantsAction(URLHandler):
    _endpoint = 'legacy.confModifParticipants-action'


class UHConfModifParticipantsStatistics(URLHandler):
    _endpoint = 'legacy.confModifParticipants-statistics'


class UHConfParticipantsInvitation(URLHandler):
    _endpoint = 'legacy.confModifParticipants-invitation'


class UHConfParticipantsRefusal(URLHandler):
    _endpoint = 'legacy.confModifParticipants-refusal'


class UHConfModifToggleSearch(URLHandler):
    _endpoint = 'event_mgmt.confModifDisplay-toggleSearch'


class UHConfModifToggleNavigationBar(URLHandler):
    _endpoint = 'event_mgmt.confModifDisplay-toggleNavigationBar'


class UHTickerTapeAction(URLHandler):
    _endpoint = 'event_mgmt.confModifDisplay-tickerTapeAction'


class UHUserManagement(URLHandler):
    _endpoint = 'admin.userManagement'


class UHUserManagementSwitchAuthorisedAccountCreation(URLHandler):
    _endpoint = 'admin.userManagement-switchAuthorisedAccountCreation'


class UHUserManagementSwitchNotifyAccountCreation(URLHandler):
    _endpoint = 'admin.userManagement-switchNotifyAccountCreation'


class UHUserManagementSwitchModerateAccountCreation(URLHandler):
    _endpoint = 'admin.userManagement-switchModerateAccountCreation'


class UHUsers(URLHandler):
    _endpoint = 'admin.userList'


class UHUserCreation(URLHandler):
    _endpoint = 'user.userRegistration'

    @classmethod
    def getURL(cls, returnURL=''):
        if Config.getInstance().getRegistrationURL():
            url = URL(Config.getInstance().getRegistrationURL())
        else:
            url = cls._getURL()
        if returnURL:
            url.addParam('returnURL', returnURL)
        return url


class UHUserMerge(URLHandler):
    _endpoint = 'admin.userMerge'


class UHConfSignIn(SecureURLHandler):
    _endpoint = 'event.confLogin'

    @classmethod
    def getURL(cls, conf, returnURL=''):
        if Config.getInstance().getLoginURL():
            url = URL(Config.getInstance().getLoginURL())
        else:
            url = cls._getURL()
        if conf is not None:
            url.setParams(conf.getLocator())
        if returnURL:
            url.addParam('returnURL', returnURL)
        return url


class UHConfUserCreation(URLHandler):
    _endpoint = 'event.confUser'

    @classmethod
    def getURL(cls, conf, returnURL=''):
        if Config.getInstance().getRegistrationURL():
            url = URL(Config.getInstance().getRegistrationURL())
        else:
            url = cls._getURL()
        if conf is not None:
            url.setParams(conf.getLocator())
        if returnURL:
            url.addParam('returnURL', returnURL)
        return url


class UHConfUser(URLHandler):
    @classmethod
    def getURL(cls, conference, av=None):
        url = cls._getURL()
        if conference is not None:
            loc = conference.getLocator().copy()
            if av:
                loc.update(av.getLocator())
            url.setParams(loc)
        return url


class UHConfDisabledAccount(UHConfUser):
    _endpoint = 'event.confLogin-disabledAccount'


class UHConfUnactivatedAccount(UHConfUser):
    _endpoint = 'event.confLogin-unactivatedAccount'


class UHConfUserCreated(UHConfUser):
    _endpoint = 'event.confUser-created'


class UHConfSendLogin(UHConfUser):
    _endpoint = 'event.confLogin-sendLogin'


class UHConfSendActivation(UHConfUser):
    _endpoint = 'event.confLogin-sendActivation'


class UHConfUserExistWithIdentity(UHConfUser):
    _endpoint = 'event.confUser-userExists'


class UHConfActiveAccount(UHConfUser):
    _endpoint = 'event.confLogin-active'


class UHConfEnterAccessKey(UHConfUser):
    _endpoint = 'event.conferenceDisplay-accessKey'


class UHConfManagementAccess(UHConfUser):
    _endpoint = 'event_mgmt.conferenceModification-managementAccess'


class UHConfEnterModifKey(UHConfUser):
    _endpoint = 'legacy.conferenceModification-modifKey'


class UHConfCloseModifKey(UHConfUser):
    _endpoint = 'legacy.conferenceModification-closeModifKey'


class UHUserCreated(UHConfUser):
    _endpoint = 'user.userRegistration-created'


class UHUserActive(URLHandler):
    _endpoint = 'user.userRegistration-active'


class UHUserDisable(URLHandler):
    _endpoint = 'user.userRegistration-disable'


class UHUserDashboard(URLHandler):
    _endpoint = 'user.userDashboard'


class UHUserDetails(URLHandler):
    _endpoint = 'user.userDetails'


class UHUserBaskets(URLHandler):
    _endpoint = 'user.userBaskets'


class UHUserPreferences(URLHandler):
    _endpoint = 'user.userPreferences'


class UHUserAPI(URLHandler):
    _endpoint = 'user.userAPI'


class UHUserAPICreate(URLHandler):
    _endpoint = 'user.userAPI-create'


class UHUserAPIBlock(URLHandler):
    _endpoint = 'user.userAPI-block'


class UHUserAPIDelete(URLHandler):
    _endpoint = 'user.userAPI-delete'


class UHUserRegistration(URLHandler):
    _endpoint = 'user.userRegistration'


class UHUserIdentityCreation(URLHandler):
    _endpoint = 'user.identityCreation'


class UHUserRemoveIdentity(URLHandler):
    _endpoint = 'user.identityCreation-remove'


class UHUserExistWithIdentity(UHConfUser):
    _endpoint = 'user.userRegistration-UserExist'


class UHUserIdPerformCreation(URLHandler):
    _endpoint = 'user.identityCreation-create'


class UHUserIdentityChangePassword(URLHandler):
    _endpoint = 'user.identityCreation-changePassword'


class UHGroups(URLHandler):
    _endpoint = 'admin.groupList'


class UHNewGroup(URLHandler):
    _endpoint = 'admin.groupRegistration'


class UHGroupPerformRegistration(URLHandler):
    _endpoint = 'admin.groupRegistration-update'


class UHGroupDetails(URLHandler):
    _endpoint = 'admin.groupDetails'


class UHGroupModification(URLHandler):
    _endpoint = 'admin.groupModification'


class UHGroupPerformModification(URLHandler):
    _endpoint = 'admin.groupModification-update'


class UHPrincipalDetails:
    @classmethod
    def getURL(cls, member):
        if isinstance(member, user.Group):
            return UHGroupDetails.getURL(member)
        elif isinstance(member, user.Avatar):
            return UHUserDetails.getURL(member)
        else:
            return ''


class UHDomains(URLHandler):
    _endpoint = 'admin.domainList'


class UHNewDomain(URLHandler):
    _endpoint = 'admin.domainCreation'


class UHDomainPerformCreation(URLHandler):
    _endpoint = 'admin.domainCreation-create'


class UHDomainDetails(URLHandler):
    _endpoint = 'admin.domainDetails'


class UHDomainModification(URLHandler):
    _endpoint = 'admin.domainDataModification'


class UHDomainPerformModification(URLHandler):
    _endpoint = 'admin.domainDataModification-modify'


class UHRoomMappers(URLHandler):
    _endpoint = 'rooms_admin.roomMapper'


class UHNewRoomMapper(URLHandler):
    _endpoint = 'rooms_admin.roomMapper-creation'


class UHRoomMapperPerformCreation(URLHandler):
    _endpoint = 'rooms_admin.roomMapper-performCreation'


class UHRoomMapperDetails(URLHandler):
    _endpoint = 'rooms_admin.roomMapper-details'


class UHRoomMapperModification(URLHandler):
    _endpoint = 'rooms_admin.roomMapper-modify'


class UHRoomMapperPerformModification(URLHandler):
    _endpoint = 'rooms_admin.roomMapper-performModify'


class UHAdminArea(URLHandler):
    _endpoint = 'admin.adminList'


class UHAdminSwitchCacheActive(URLHandler):
    _endpoint = 'admin.adminList-switchCacheActive'


class UHAdminSwitchDebugActive(URLHandler):
    _endpoint = 'admin.adminList-switchDebugActive'


class UHAdminSwitchNewsActive(URLHandler):
    _endpoint = 'admin.adminList-switchNewsActive'


class UHAdminsStyles(URLHandler):
    _endpoint = 'admin.adminLayout-styles'


class UHAdminsConferenceStyles(URLHandler):
    _endpoint = 'admin.adminConferenceStyles'


class UHAdminsAddStyle(URLHandler):
    _endpoint = 'admin.adminLayout-addStyle'


class UHAdminsDeleteStyle(URLHandler):
    _endpoint = 'admin.adminLayout-deleteStyle'


class UHAdminsSystem(URLHandler):
    _endpoint = 'admin.adminSystem'


class UHAdminsSystemModif(URLHandler):
    _endpoint = 'admin.adminSystem-modify'


class UHAdminsProtection(URLHandler):
    _endpoint = 'admin.adminProtection'


class UHMaterialModification(URLHandler):

    @classmethod
    def getURL(cls, material, returnURL=""):
        from MaKaC import conference

        owner = material.getOwner()
        # return handler depending on parent type
        if isinstance(owner, conference.Category):
            handler = UHCategModifFiles
        elif isinstance(owner, conference.Conference):
            handler = UHConfModifShowMaterials
        elif isinstance(owner, conference.Session):
            handler = UHSessionModifMaterials
        elif isinstance(owner, conference.Contribution):
            handler = UHContribModifMaterials
        elif isinstance(owner, conference.SubContribution):
            handler = UHSubContribModifMaterials
        else:
            raise Exception('Unknown material owner type: %s' % owner)

        return handler.getURL(owner, returnURL=returnURL)


class UHMaterialEnterAccessKey(URLHandler):
    _endpoint = 'files.materialDisplay-accessKey'


class UHFileEnterAccessKey(URLHandler):
    _endpoint = 'files.getFile-accessKey'


class UHCategoryModification(URLHandler):
    _endpoint = 'category.categoryModification'

    @classmethod
    def getActionURL(cls):
        return ''


class UHCategoryAddMaterial(URLHandler):
    _endpoint = 'category.categoryFiles-addMaterial'


class UHCategoryActionSubCategs(URLHandler):
    _endpoint = 'category.categoryModification-actionSubCategs'


class UHCategoryActionConferences(URLHandler):
    _endpoint = 'category.categoryModification-actionConferences'


class UHCategoryClearCache(URLHandler):
    _endpoint = 'category.categoryModification-clearCache'


class UHCategoryClearConferenceCaches(URLHandler):
    _endpoint = 'category.categoryModification-clearConferenceCaches'


class UHCategModifAC(URLHandler):
    _endpoint = 'category.categoryAC'


class UHCategorySetConfCreationControl(URLHandler):
    _endpoint = 'category.categoryConfCreationControl-setCreateConferenceControl'


class UHCategorySetNotifyCreation(URLHandler):
    _endpoint = 'category.categoryConfCreationControl-setNotifyCreation'


class UHCategModifTools(URLHandler):
    _endpoint = 'category.categoryTools'


class UHCategoryDeletion(URLHandler):
    _endpoint = 'category.categoryTools-delete'


class UHCategModifTasks(URLHandler):
    _endpoint = 'category.categoryTasks'


class UHCategModifFiles(URLHandler):
    _endpoint = 'category.categoryFiles'


class UHCategModifTasksAction(URLHandler):
    _endpoint = 'category.categoryTasks-taskAction'


class UHCategoryDataModif(URLHandler):
    _endpoint = 'category.categoryDataModification'


class UHCategoryPerformModification(URLHandler):
    _endpoint = 'category.categoryDataModification-modify'


class UHCategoryTasksOption(URLHandler):
    _endpoint = 'category.categoryDataModification-tasksOption'


class UHCategorySetVisibility(URLHandler):
    _endpoint = 'category.categoryAC-setVisibility'


class UHCategoryCreation(URLHandler):
    _endpoint = 'category.categoryCreation'


class UHCategoryPerformCreation(URLHandler):
    _endpoint = 'category.categoryCreation-create'


class UHCategoryDisplay(URLHandler):
    _endpoint = 'category.categoryDisplay'

    @classmethod
    def getURL(cls, target=None):
        url = cls._getURL()
        if target:
            if target.isRoot():
                return UHWelcome.getURL()
            url.setParams(target.getLocator())
        return url


class UHCategoryMap(URLHandler):
    _endpoint = 'category.categoryMap'


class UHCategoryOverview(URLHandler):
    _endpoint = 'category.categOverview'

    @classmethod
    def getURLFromOverview(cls, ow):
        url = cls.getURL()
        url.setParams(ow.getLocator())
        return url

    @classmethod
    def getWeekOverviewUrl(cls, categ):
        url = cls.getURL(categ)
        p = {"day": nowutc().day,
             "month": nowutc().month,
             "year": nowutc().year,
             "period": "week",
             "detail": "conference"}
        url.addParams(p)
        return url

    @classmethod
    def getMonthOverviewUrl(cls, categ):
        url = cls.getURL(categ)
        p = {"day": nowutc().day,
             "month": nowutc().month,
             "year": nowutc().year,
             "period": "month",
             "detail": "conference"}
        url.addParams(p)
        return url


class UHGeneralInfoModification(URLHandler):
    _endpoint = 'admin.generalInfoModification'


class UHGeneralInfoPerformModification(URLHandler):
    _endpoint = 'admin.generalInfoModification-update'


class UHContributionDelete(URLHandler):
    _endpoint = 'legacy.contributionTools-delete'


class UHSubContributionDataModification(URLHandler):
    _endpoint = 'legacy.subContributionModification-data'


class UHSubContributionDataModif(URLHandler):
    _endpoint = 'legacy.subContributionModification-modifData'


class UHSubContributionDelete(URLHandler):
    _endpoint = 'legacy.subContributionTools-delete'


class UHSubContribModifAddMaterials(URLHandler):
    _endpoint = 'legacy.subContributionModification-materialsAdd'


class UHSubContribModifTools(URLHandler):
    _endpoint = 'legacy.subContributionTools'


class UHSessionModification(URLHandler):
    _endpoint = 'legacy.sessionModification'


class UHSessionModifMaterials(URLHandler):
    _endpoint = 'legacy.sessionModification-materials'


class UHSessionDataModification(URLHandler):
    _endpoint = 'legacy.sessionModification-modify'


class UHSessionFitSlot(URLHandler):
    _endpoint = 'legacy.sessionModifSchedule-fitSlot'


class UHSessionModifAddMaterials(URLHandler):
    _endpoint = 'legacy.sessionModification-materialsAdd'


class UHSessionModifSchedule(URLHandler):
    _endpoint = 'legacy.sessionModifSchedule'


class UHSessionModSlotCalc(URLHandler):
    _endpoint = 'legacy.sessionModifSchedule-slotCalc'


class UHSessionModifAC(URLHandler):
    _endpoint = 'legacy.sessionModifAC'


class UHSessionSetVisibility(URLHandler):
    _endpoint = 'legacy.sessionModifAC-setVisibility'


class UHSessionModifTools(URLHandler):
    _endpoint = 'legacy.sessionModifTools'


class UHSessionModifComm(URLHandler):
    _endpoint = 'legacy.sessionModifComm'


class UHSessionModifCommEdit(URLHandler):
    _endpoint = 'legacy.sessionModifComm-edit'


class UHSessionDeletion(URLHandler):
    _endpoint = 'legacy.sessionModifTools-delete'


class UHContributionModification(URLHandler):
    _endpoint = 'legacy.contributionModification'


class UHContribModifMaterials(URLHandler):
    _endpoint = 'legacy.contributionModification-materials'


class UHContributionPerformMove(URLHandler):
    _endpoint = 'legacy.contributionModification-performMove'


class UHSubContribModification(URLHandler):
    _endpoint = 'legacy.subContributionModification'


class UHSubContribModifMaterials(URLHandler):
    _endpoint = 'legacy.subContributionModification-materials'


class UHMaterialDisplay(URLHandler):
    _endpoint = 'files.materialDisplay'


class UHConferenceProgram(URLHandler):
    _endpoint = 'event.conferenceProgram'


class UHConferenceProgramPDF(URLHandler):
    _endpoint = 'event.conferenceProgram-pdf'


class UHConferenceTimeTable(URLHandler):
    _endpoint = 'event.conferenceTimeTable'


class UHConfTimeTablePDF(URLHandler):
    _endpoint = 'event.conferenceTimeTable-pdf'


class UHConferenceCFA(URLHandler):
    _endpoint = 'event.conferenceCFA'


class UHSessionDisplay(URLHandler):
    _endpoint = 'event.sessionDisplay'


class UHSessionToiCal(URLHandler):
    _endpoint = 'event.sessionDisplay-ical'


class UHContributionDisplay(URLHandler):
    _endpoint = 'event.contributionDisplay'


class UHSubContributionDisplay(URLHandler):
    _endpoint = 'legacy.subContributionDisplay'


class UHSubContributionModification(URLHandler):
    _endpoint = 'legacy.subContributionModification'


class UHFileAccess(URLHandler):
    _endpoint = 'files.getFile-access'


class UHVideoWmvAccess(URLHandler):
    _endpoint = 'files.getFile-wmv'


class UHVideoFlashAccess(URLHandler):
    _endpoint = 'files.getFile-flash'


class UHErrorReporting(URLHandler):
    _endpoint = 'misc.errors'


class UHAbstractWithdraw(URLHandler):
    _endpoint = 'event.abstractWithdraw'


class UHAbstractRecovery(URLHandler):
    _endpoint = 'event.abstractWithdraw-recover'


class UHConfModifContribList(URLHandler):
    _endpoint = 'legacy.confModifContribList'


class UHContribModifMaterialBrowse(URLHandler):
    _endpoint = 'legacy.contributionModification-browseMaterial'


class UHContribModSetTrack(URLHandler):
    _endpoint = 'legacy.contributionModification-setTrack'


class UHContribModSetSession(URLHandler):
    _endpoint = 'legacy.contributionModification-setSession'


class UHTrackModMoveUp(URLHandler):
    _endpoint = 'legacy.confModifProgram-moveTrackUp'


class UHTrackModMoveDown(URLHandler):
    _endpoint = 'legacy.confModifProgram-moveTrackDown'


class UHAbstractModAC(URLHandler):
    _endpoint = 'legacy.abstractManagment-ac'


class UHAbstractModEditData(URLHandler):
    _endpoint = 'legacy.abstractManagment-editData'


class UHAbstractModIntComments(URLHandler):
    _endpoint = 'legacy.abstractManagment-comments'


class UHAbstractModNewIntComment(URLHandler):
    _endpoint = 'legacy.abstractManagment-newComment'


class UHAbstractModIntCommentEdit(URLHandler):
    _endpoint = 'legacy.abstractManagment-editComment'


class UHAbstractModIntCommentRem(URLHandler):
    _endpoint = 'legacy.abstractManagment-remComment'


class UHTrackAbstractModIntCommentNew(UHTrackAbstractBase):
    _endpoint = 'legacy.trackAbstractModif-commentNew'


class UHTrackAbstractModCommentBase(URLHandler):
    @classmethod
    def getURL(cls, track, comment):
        url = cls._getURL()
        url.setParams(comment.getLocator())
        url.addParam("trackId", track.getId())
        return url


class UHTrackAbstractModIntCommentEdit(UHTrackAbstractModCommentBase):
    _endpoint = 'legacy.trackAbstractModif-commentEdit'


class UHTrackAbstractModIntCommentRem(UHTrackAbstractModCommentBase):
    _endpoint = 'legacy.trackAbstractModif-commentRem'


class UHAbstractReviewingNotifTpl(URLHandler):
    _endpoint = 'legacy.abstractReviewing-notifTpl'


class UHAbstractModNotifTplNew(URLHandler):
    _endpoint = 'legacy.abstractReviewing-notifTplNew'


class UHAbstractModNotifTplRem(URLHandler):
    _endpoint = 'legacy.abstractReviewing-notifTplRem'


class UHAbstractModNotifTplEdit(URLHandler):
    _endpoint = 'legacy.abstractReviewing-notifTplEdit'


class UHAbstractModNotifTplDisplay(URLHandler):
    _endpoint = 'legacy.abstractReviewing-notifTplDisplay'


class UHAbstractModNotifTplPreview(URLHandler):
    _endpoint = 'legacy.abstractReviewing-notifTplPreview'


class UHTrackAbstractModMarkAsDup(UHTrackAbstractBase):
    _endpoint = 'legacy.trackAbstractModif-markAsDup'


class UHTrackAbstractModUnMarkAsDup(UHTrackAbstractBase):
    _endpoint = 'legacy.trackAbstractModif-unMarkAsDup'


class UHAbstractModMarkAsDup(URLHandler):
    _endpoint = 'legacy.abstractManagment-markAsDup'


class UHAbstractModUnMarkAsDup(URLHandler):
    _endpoint = 'legacy.abstractManagment-unMarkAsDup'


class UHAbstractModMergeInto(URLHandler):
    _endpoint = 'legacy.abstractManagment-mergeInto'


class UHAbstractModUnMerge(URLHandler):
    _endpoint = 'legacy.abstractManagment-unmerge'


class UHConfModNewAbstract(URLHandler):
    _endpoint = 'legacy.abstractsManagment-newAbstract'


class UHConfModNotifTplConditionNew(URLHandler):
    _endpoint = 'legacy.abstractReviewing-notifTplCondNew'


class UHConfModNotifTplConditionRem(URLHandler):
    _endpoint = 'legacy.abstractReviewing-notifTplCondRem'


class UHConfModAbstractsMerge(URLHandler):
    _endpoint = 'legacy.abstractsManagment-mergeAbstracts'


class UHAbstractModNotifLog(URLHandler):
    _endpoint = 'legacy.abstractManagment-notifLog'


class UHAbstractModTools(URLHandler):
    _endpoint = 'legacy.abstractTools'


class UHAbstractDelete(URLHandler):
    _endpoint = 'legacy.abstractTools-delete'


class UHSessionModContribList(URLHandler):
    _endpoint = 'legacy.sessionModification-contribList'


class UHSessionModContribListEditContrib(URLHandler):
    _endpoint = 'legacy.sessionModification-editContrib'


class UHConfModifReschedule(URLHandler):
    _endpoint = 'legacy.confModifSchedule-reschedule'


class UHContributionList(URLHandler):
    _endpoint = 'event.contributionListDisplay'


class UHContributionListToPDF(URLHandler):
    _endpoint = 'event.contributionListDisplay-contributionsToPDF'


class UHConfModAbstractPropToAcc(URLHandler):
    _endpoint = 'legacy.abstractManagment-propToAcc'


class UHAbstractManagmentBackToSubmitted(URLHandler):
    _endpoint = 'legacy.abstractManagment-backToSubmitted'


class UHConfModAbstractPropToRej(URLHandler):
    _endpoint = 'legacy.abstractManagment-propToRej'


class UHConfModAbstractWithdraw(URLHandler):
    _endpoint = 'legacy.abstractManagment-withdraw'


class UHSessionModAddContribs(URLHandler):
    _endpoint = 'legacy.sessionModification-addContribs'


class UHSessionModContributionAction(URLHandler):
    _endpoint = 'legacy.sessionModification-contribAction'


class UHSessionModParticipantList(URLHandler):
    _endpoint = 'legacy.sessionModification-participantList'


class UHSessionModToPDF(URLHandler):
    _endpoint = 'legacy.sessionModification-contribsToPDF'


class UHConfModCFANotifTplUp(URLHandler):
    _endpoint = 'legacy.abstractReviewing-notifTplUp'


class UHConfModCFANotifTplDown(URLHandler):
    _endpoint = 'legacy.abstractReviewing-notifTplDown'


class UHConfAuthorIndex(URLHandler):
    _endpoint = 'event.confAuthorIndex'


class UHConfSpeakerIndex(URLHandler):
    _endpoint = 'event.confSpeakerIndex'


class UHContribModWithdraw(URLHandler):
    _endpoint = 'legacy.contributionModification-withdraw'


class UHTrackModContribList(URLHandler):
    _endpoint = 'legacy.trackModContribList'


class UHTrackModContributionAction(URLHandler):
    _endpoint = 'legacy.trackModContribList-contribAction'


class UHTrackModParticipantList(URLHandler):
    _endpoint = 'legacy.trackModContribList-participantList'


class UHTrackModToPDF(URLHandler):
    _endpoint = 'legacy.trackModContribList-contribsToPDF'


class UHConfModContribQuickAccess(URLHandler):
    _endpoint = 'legacy.confModifContribList-contribQuickAccess'


class UHSessionModContribQuickAccess(URLHandler):
    _endpoint = 'legacy.sessionModification-contribQuickAccess'


class UHTrackModContribQuickAccess(URLHandler):
    _endpoint = 'legacy.trackModContribList-contribQuickAccess'


class UHConfMyStuff(URLHandler):
    _endpoint = 'event.myconference'


class UHConfMyStuffMySessions(URLHandler):
    _endpoint = 'event.myconference-mySessions'


class UHConfMyStuffMyTracks(URLHandler):
    _endpoint = 'event.myconference-myTracks'


class UHConfMyStuffMyContributions(URLHandler):
    _endpoint = 'event.myconference-myContributions'


class UHConfModMoveContribsToSession(URLHandler):
    _endpoint = 'legacy.confModifContribList-moveToSession'


class UHConferenceDisplayMaterialPackage(URLHandler):
    _endpoint = 'event.conferenceDisplay-matPkg'


class UHConferenceDisplayMaterialPackagePerform(URLHandler):
    _endpoint = 'event.conferenceDisplay-performMatPkg'


class UHConfAbstractBook(URLHandler):
    _endpoint = 'event.conferenceDisplay-abstractBook'


class UHConfAbstractBookLatex(URLHandler):
    _endpoint = 'event.conferenceDisplay-abstractBookLatex'


class UHConferenceToiCal(URLHandler):
    _endpoint = 'event.conferenceDisplay-ical'


class UHConfModAbstractBook(URLHandler):
    _endpoint = 'legacy.confModBOA'


class UHConfModAbstractBookEdit(URLHandler):
    _endpoint = 'legacy.confModBOA-edit'


class UHConfModAbstractBookToogleShowIds(URLHandler):
    _endpoint = 'legacy.confModBOA-toogleShowIds'


class UHAbstractReviewingSetup(URLHandler):
    _endpoint = 'legacy.abstractReviewing-reviewingSetup'


class UHAbstractReviewingTeam(URLHandler):
    _endpoint = 'legacy.abstractReviewing-reviewingTeam'


class UHConfModScheduleDataEdit(URLHandler):
    _endpoint = 'legacy.confModifSchedule-edit'


class UHConfModMaterialPackage(URLHandler):
    _endpoint = 'legacy.confModifContribList-matPkg'


class UHConfModProceedings(URLHandler):
    _endpoint = 'legacy.confModifContribList-proceedings'


class UHConfModFullMaterialPackage(URLHandler):
    _endpoint = 'event_mgmt.confModifTools-matPkg'


class UHConfModFullMaterialPackagePerform(URLHandler):
    _endpoint = 'event_mgmt.confModifTools-performMatPkg'


class UHTaskManager(URLHandler):
    _endpoint = 'admin.taskManager'


class UHUpdateNews(URLHandler):
    _endpoint = 'admin.updateNews'


# Server Admin, plugin management related
class UHAdminPlugins(URLHandler):
    _endpoint = 'admin.adminPlugins'


class UHAdminPluginsSaveOptionReloadAll(URLHandler):
    _endpoint = 'admin.adminPlugins-saveOptionReloadAll'


class UHAdminPluginsReloadAll(URLHandler):
    _endpoint = 'admin.adminPlugins-reloadAll'


class UHAdminPluginsClearAllInfo(URLHandler):
    _endpoint = 'admin.adminPlugins-clearAllInfo'


class UHAdminReloadPlugins(URLHandler):
    _endpoint = 'admin.adminPlugins-reload'


class UHAdminTogglePluginType(URLHandler):
    _endpoint = 'admin.adminPlugins-toggleActivePluginType'


class UHAdminTogglePlugin(URLHandler):
    _endpoint = 'admin.adminPlugins-toggleActive'


class UHAdminPluginsTypeSaveOptions(URLHandler):
    _endpoint = 'admin.adminPlugins-savePluginTypeOptions'


class UHAdminPluginsSaveOptions(URLHandler):
    _endpoint = 'admin.adminPlugins-savePluginOptions'
# End of Server Admin, plugin management related


class UHMaintenance(URLHandler):
    _endpoint = 'admin.adminMaintenance'


class UHMaintenanceTmpCleanup(URLHandler):
    _endpoint = 'admin.adminMaintenance-tmpCleanup'


class UHMaintenancePerformTmpCleanup(URLHandler):
    _endpoint = 'admin.adminMaintenance-performTmpCleanup'


class UHMaintenancePack(URLHandler):
    _endpoint = 'admin.adminMaintenance-pack'


class UHMaintenancePerformPack(URLHandler):
    _endpoint = 'admin.adminMaintenance-performPack'


class UHAdminLayoutGeneral(URLHandler):
    _endpoint = 'admin.adminLayout'


class UHAdminLayoutSaveTemplateSet(URLHandler):
    _endpoint = 'admin.adminLayout-saveTemplateSet'


class UHAdminLayoutSaveSocial(URLHandler):
    _endpoint = 'admin.adminLayout-saveSocial'


class UHTemplatesSetDefaultPDFOptions(URLHandler):
    _endpoint = 'admin.adminLayout-setDefaultPDFOptions'


class UHWebcast(URLHandler):
    _endpoint = 'admin.adminServices-webcast'


class UHWebcastArchive(URLHandler):
    _endpoint = 'admin.adminServices-webcastArchive'


class UHWebcastSetup(URLHandler):
    _endpoint = 'admin.adminServices-webcastSetup'


class UHWebcastAddWebcast(URLHandler):
    _endpoint = 'admin.adminServices-webcastAddWebcast'


class UHWebcastRemoveWebcast(URLHandler):
    _endpoint = 'admin.adminServices-webcastRemoveWebcast'


class UHWebcastArchiveWebcast(URLHandler):
    _endpoint = 'admin.adminServices-webcastArchiveWebcast'


class UHWebcastUnArchiveWebcast(URLHandler):
    _endpoint = 'admin.adminServices-webcastUnArchiveWebcast'


class UHWebcastModifyChannel(URLHandler):
    _endpoint = 'admin.adminServices-webcastModifyChannel'


class UHWebcastAddChannel(URLHandler):
    _endpoint = 'admin.adminServices-webcastAddChannel'


class UHWebcastRemoveChannel(URLHandler):
    _endpoint = 'admin.adminServices-webcastRemoveChannel'


class UHWebcastSwitchChannel(URLHandler):
    _endpoint = 'admin.adminServices-webcastSwitchChannel'


class UHWebcastMoveChannelUp(URLHandler):
    _endpoint = 'admin.adminServices-webcastMoveChannelUp'


class UHWebcastMoveChannelDown(URLHandler):
    _endpoint = 'admin.adminServices-webcastMoveChannelDown'


class UHWebcastSaveWebcastSynchronizationURL(URLHandler):
    _endpoint = 'admin.adminServices-webcastSaveWebcastSynchronizationURL'


class UHWebcastManualSynchronization(URLHandler):
    _endpoint = 'admin.adminServices-webcastManualSynchronization'


class UHWebcastAddStream(URLHandler):
    _endpoint = 'admin.adminServices-webcastAddStream'


class UHWebcastRemoveStream(URLHandler):
    _endpoint = 'admin.adminServices-webcastRemoveStream'


class UHWebcastAddOnAir(URLHandler):
    _endpoint = 'admin.adminServices-webcastAddOnAir'


class UHWebcastRemoveFromAir(URLHandler):
    _endpoint = 'admin.adminServices-webcastRemoveFromAir'


class UHIPBasedACL(URLHandler):
    _endpoint = 'admin.adminServices-ipbasedacl'


class UHIPBasedACLFullAccessGrant(URLHandler):
    _endpoint = 'admin.adminServices-ipbasedacl_fagrant'


class UHIPBasedACLFullAccessRevoke(URLHandler):
    _endpoint = 'admin.adminServices-ipbasedacl_farevoke'


class UHAdminAPIOptions(URLHandler):
    _endpoint = 'admin.adminServices-apiOptions'


class UHAdminAPIOptionsSet(URLHandler):
    _endpoint = 'admin.adminServices-apiOptionsSet'


class UHAdminAPIKeys(URLHandler):
    _endpoint = 'admin.adminServices-apiKeys'


class UHAdminOAuthConsumers(URLHandler):
    _endpoint = 'admin.adminServices-oauthConsumers'


class UHAdminOAuthAuthorized(URLHandler):
    _endpoint = 'admin.adminServices-oauthAuthorized'


class UHAnalytics(URLHandler):
    _endpoint = 'admin.adminServices-analytics'


class UHSaveAnalytics(URLHandler):
    _endpoint = 'admin.adminServices-saveAnalytics'


class UHBadgeTemplates(URLHandler):
    _endpoint = 'admin.badgeTemplates'


class UHPosterTemplates(URLHandler):
    _endpoint = 'admin.posterTemplates'


class UHAnnouncement(URLHandler):
    _endpoint = 'admin.adminAnnouncement'


class UHAnnouncementSave(URLHandler):
    _endpoint = 'admin.adminAnnouncement-save'


class UHConfigUpcomingEvents(URLHandler):
    _endpoint = 'admin.adminUpcomingEvents'

# ------- DVD creation and static webpages ------

class UHConfDVDCreation(URLHandler):
    _endpoint = 'legacy.confModifTools-dvdCreation'


class UHStaticConferenceDisplay(URLHandler):
    _relativeURL = "./index.html"

class UHStaticMaterialDisplay(URLHandler):
    _relativeURL = "none-page-material.html"

    def _normalisePathItem(cls,name):
        return str(name).translate(string.maketrans(" /:()*?<>|\"","___________"))
    _normalisePathItem = classmethod( _normalisePathItem )

    def getRelativeURL(cls, target=None, escape = True):
        from MaKaC.conference import Contribution, Conference, Link, Video, Session
        if target is not None:
            if len(target.getResourceList()) == 1:
                res = target.getResourceList()[0]
                # TODO: Remove the "isinstance", it's just for CHEP04
                if isinstance(res, Link):# and not isinstance(target, Video):
                    return res.getURL()
                else:
                    return UHStaticResourceDisplay.getRelativeURL(res)
            else:
                contrib = target.getOwner()
                if isinstance(contrib, Contribution):
                    spk=""
                    if len(contrib.getSpeakerList())>0:
                        spk=contrib.getSpeakerList()[0].getFamilyName().lower()
                    contribDirName="%s-%s"%(contrib.getId(),spk)
                    relativeURL = "./%s-material-%s.html"%(contribDirName, cls._normalisePathItem(target.getId()))

                elif isinstance(contrib, Conference):
                    relativeURL = "./material-%s.html"%(cls._normalisePathItem(target.getId()))
                elif isinstance(contrib, Session):
                    relativeURL = "./material-s%s-%s.html"%(contrib.getId(), cls._normalisePathItem(target.getId()))

                if escape:
                    relativeURL = utf8rep(relativeURL)

                return relativeURL
        return cls._relativeURL
    getRelativeURL = classmethod( getRelativeURL )

class UHStaticConfAbstractBook(URLHandler):
    _relativeURL = "./abstractBook.pdf"

class UHStaticConferenceProgram(URLHandler):
    _relativeURL = "./programme.html"

class UHStaticConferenceTimeTable(URLHandler):
    _relativeURL = "./timetable.html"

class UHStaticContributionList(URLHandler):
    _relativeURL = "./contributionList.html"

class UHStaticConfAuthorIndex(URLHandler):
    _relativeURL = "./authorIndex.html"

class UHStaticContributionDisplay(URLHandler):
    _relativeURL = ""

    def getRelativeURL(cls, target=None, prevPath=".", escape=True):
        url = cls._relativeURL
        if target is not None:
            spk=""
            if len(target.getSpeakerList())>0:
                spk=target.getSpeakerList()[0].getFamilyName().lower()
            contribDirName="%s-%s"%(target.getId(),spk)
            track = target.getTrack()
            if track is not None:
                url = "./%s/%s/%s.html"%(prevPath, track.getTitle().replace(" ","_"), contribDirName)
            else:
                url = "./%s/other_contributions/%s.html"%(prevPath, contribDirName)

        if escape:
            url = utf8rep(url)

        return url
    getRelativeURL = classmethod( getRelativeURL )

class UHStaticSessionDisplay(URLHandler):
    _relativeURL = ""

    def getRelativeURL(cls, target=None):
        return "./sessions/s%s.html"%target.getId()
    getRelativeURL = classmethod( getRelativeURL )

class UHStaticResourceDisplay(URLHandler):
    _relativeURL = "none-page-resource.html"

    def _normalisePathItem(cls,name):
        return str(name).translate(string.maketrans(" /:()*?<>|\"","___________"))
    _normalisePathItem = classmethod( _normalisePathItem )

    def getRelativeURL(cls, target=None, escape=True):
        from MaKaC.conference import Contribution, Conference, Video, Link, Session
        relativeURL = cls._relativeURL
        if target is not None:
            mat = target.getOwner()
            contrib = mat.getOwner()
            # TODO: Remove the first if...cos it's just for CHEP. Remove as well, in pages.conferences.WMaterialStaticDisplay
            #if isinstance(mat, Video) and isinstance(target, Link):
            #    relativeURL = "./%s.rm"%os.path.splitext(os.path.basename(target.getURL()))[0]
            #    return relativeURL
            if isinstance(contrib, Contribution):
                relativeURL = "./%s-%s-%s-%s"%(cls._normalisePathItem(contrib.getId()), target.getOwner().getId(), target.getId(), cls._normalisePathItem(target.getFileName()))
            elif isinstance(contrib, Conference):
                relativeURL = "./resource-%s-%s-%s"%(target.getOwner().getId(), target.getId(), cls._normalisePathItem(target.getFileName()))
            elif isinstance(contrib, Session):
                relativeURL = "./resource-s%s-%s-%s"%(contrib.getId(), target.getId(), cls._normalisePathItem(target.getFileName()))

            if escape:
                relativeURL = utf8rep(relativeURL)

            return relativeURL
    getRelativeURL = classmethod( getRelativeURL )

class UHStaticTrackContribList(URLHandler):
    _relativeURL = ""

    def getRelativeURL(cls, target=None, escape=True):
        url = cls._relativeURL
        if target is not None:
            url = "%s.html"%(target.getTitle().replace(" ","_"))

        if escape:
            url = utf8rep(url)
        return url

    getRelativeURL = classmethod( getRelativeURL )

class UHDVDDone(URLHandler):
    _endpoint = 'legacy.confModifTools-dvdDone'


class UHMStaticMaterialDisplay(URLHandler):
    _relativeURL = "none-page.html"

    def _normalisePathItem(cls,name):
        return str(name).translate(string.maketrans(" /:()*?<>|\"","___________"))
    _normalisePathItem = classmethod( _normalisePathItem )

    def getRelativeURL(cls, target=None, escape=True):
        from MaKaC.conference import Contribution, Link, Session, SubContribution
        if target is not None:
            if len(target.getResourceList()) == 1:
                res = target.getResourceList()[0]
                if isinstance(res, Link):
                    return res.getURL()
                else:
                    return UHMStaticResourceDisplay.getRelativeURL(res)
            else:
                owner = target.getOwner()
                parents="./material"
                if isinstance(owner, Session):
                    parents="%s/session-%s-%s"%(parents,owner.getId(), cls._normalisePathItem(owner.getTitle()))
                elif isinstance(owner, Contribution):
                    if isinstance(owner.getOwner(), Session):
                        parents="%s/session-%s-%s"%(parents, owner.getOwner().getId(), cls._normalisePathItem(owner.getOwner().getTitle()))
                    spk=""
                    if len(owner.getSpeakerList())>0:
                        spk=owner.getSpeakerList()[0].getFamilyName().lower()
                    contribDirName="%s-%s"%(owner.getId(),spk)
                    parents="%s/contrib-%s"%(parents, contribDirName)
                elif isinstance(owner, SubContribution):
                    contrib=owner.getContribution()
                    if isinstance(contrib.getOwner(), Session):
                        parents="%s/session-%s-%s"%(parents, contrib.getOwner().getId(), cls._normalisePathItem(contrib.getOwner().getTitle()))
                    contribspk=""
                    if len(contrib.getSpeakerList())>0:
                        contribspk=contrib.getSpeakerList()[0].getFamilyName().lower()
                    contribDirName="%s-%s"%(contrib.getId(),contribspk)
                    subcontspk=""
                    if len(owner.getSpeakerList())>0:
                        subcontspk=owner.getSpeakerList()[0].getFamilyName().lower()
                    subcontribDirName="%s-%s"%(owner.getId(),subcontspk)
                    parents="%s/contrib-%s/subcontrib-%s"%(parents, contribDirName, subcontribDirName)
                relativeURL = "%s/material-%s.html"%(parents, cls._normalisePathItem(target.getId()))

                if escape:
                    relativeURL = utf8rep(relativeURL)
                return relativeURL
        return cls._relativeURL
    getRelativeURL = classmethod( getRelativeURL )

class UHMStaticResourceDisplay(URLHandler):
    _relativeURL = "none-page.html"

    def _normalisePathItem(cls,name):
        return str(name).translate(string.maketrans(" /:()*?<>|\"","___________"))
    _normalisePathItem = classmethod( _normalisePathItem )

    def getRelativeURL(cls, target=None, escape=True):
        from MaKaC.conference import Contribution, Session, SubContribution
        if target is not None:

            mat = target.getOwner()
            owner = mat.getOwner()
            parents="./material"
            if isinstance(owner, Session):
                parents="%s/session-%s-%s"%(parents,owner.getId(), cls._normalisePathItem(owner.getTitle()))
            elif isinstance(owner, Contribution):
                if isinstance(owner.getOwner(), Session):
                    parents="%s/session-%s-%s"%(parents, owner.getOwner().getId(), cls._normalisePathItem(owner.getOwner().getTitle()))
                spk=""
                if len(owner.getSpeakerList())>0:
                    spk=owner.getSpeakerList()[0].getFamilyName().lower()
                contribDirName="%s-%s"%(owner.getId(),spk)
                parents="%s/contrib-%s"%(parents, contribDirName)
            elif isinstance(owner, SubContribution):
                contrib=owner.getContribution()
                if isinstance(contrib.getOwner(), Session):
                    parents="%s/session-%s-%s"%(parents, contrib.getOwner().getId(), cls._normalisePathItem(contrib.getOwner().getTitle()))
                contribspk=""
                if len(contrib.getSpeakerList())>0:
                    contribspk=contrib.getSpeakerList()[0].getFamilyName().lower()
                contribDirName="%s-%s"%(contrib.getId(),contribspk)
                subcontspk=""
                if len(owner.getSpeakerList())>0:
                    subcontspk=owner.getSpeakerList()[0].getFamilyName().lower()
                subcontribDirName="%s-%s"%(owner.getId(),subcontspk)
                parents="%s/contrib-%s/subcontrib-%s"%(parents, contribDirName, subcontribDirName)

            relativeURL = "%s/resource-%s-%s-%s"%(parents, cls._normalisePathItem(target.getOwner().getTitle()), target.getId(), cls._normalisePathItem(target.getFileName()))
            if escape:
                relativeURL = utf8rep(relativeURL)
            return relativeURL
        return cls._relativeURL
    getRelativeURL = classmethod( getRelativeURL )


# ------- END: DVD creation and static webpages ------

class UHContribAuthorDisplay(URLHandler):
    _endpoint = 'event.contribAuthorDisplay'


class UHConfTimeTableCustomizePDF(URLHandler):
    _endpoint = 'event.conferenceTimeTable-customizePdf'


class UHConfRegistrationForm(URLHandler):
    _endpoint = 'event.confRegistrationFormDisplay'


class UHConfRegistrationFormDisplay(URLHandler):
    _endpoint = 'event.confRegistrationFormDisplay-display'


class UHConfRegistrationFormCreation(URLHandler):
    _endpoint = 'event.confRegistrationFormDisplay-creation'


class UHConfRegistrationFormConditions(URLHandler):
    _endpoint = 'event.confRegistrationFormDisplay-conditions'


class UHConfRegistrationFormSignIn(URLHandler):
    _endpoint = 'event.confRegistrationFormDisplay-signIn'

    @classmethod
    def getURL(cls, conf, returnURL=''):
        url = cls._getURL()
        url.setParams(conf.getLocator())
        if returnURL:
            url.addParam("returnURL", returnURL)
        return url


class UHConfRegistrationFormCreationDone(URLHandler):
    _endpoint = 'event.confRegistrationFormDisplay-creationDone'

    @classmethod
    def getURL(cls, registrant):
        url = cls._getURL()
        url.setParams(registrant.getLocator())
        url.addParam('authkey', registrant.getRandomId())
        return url


class UHConfRegistrationFormconfirmBooking(URLHandler):
    _endpoint = 'event.confRegistrationFormDisplay-confirmBooking'


class UHConfRegistrationFormconfirmBookingDone(URLHandler):
    _endpoint = 'event.confRegistrationFormDisplay-confirmBookingDone'


class UHConfRegistrationFormModify(URLHandler):
    _endpoint = 'event.confRegistrationFormDisplay-modify'


class UHConfRegistrationFormPerformModify(URLHandler):
    _endpoint = 'event.confRegistrationFormDisplay-performModify'


###################################################################################
## epayment url
class UHConfModifEPayment(URLHandler):
    _endpoint = 'legacy.confModifEpayment'


class UHConfModifEPaymentEnableSection(URLHandler):
    _endpoint = 'legacy.confModifEpayment-enableSection'


class UHConfModifEPaymentChangeStatus(URLHandler):
    _endpoint = 'legacy.confModifEpayment-changeStatus'


class UHConfModifEPaymentdetailPaymentModification(URLHandler):
    _endpoint = 'legacy.confModifEpayment-dataModif'


class UHConfModifEPaymentPerformdetailPaymentModification(URLHandler):
    _endpoint = 'legacy.confModifEpayment-performDataModif'

###################################################################################


class UHConfModifRegForm(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm'


class UHConfModifRegFormChangeStatus(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-changeStatus'


class UHConfModifRegFormDataModification(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-dataModif'


class UHConfModifRegFormPerformDataModification(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-performDataModif'


class UHConfModifRegFormSessions(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-modifSessions'


class UHConfModifRegFormSessionsDataModif(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-modifSessionsData'


class UHConfModifRegFormSessionsPerformDataModif(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-performModifSessionsData'


class UHConfModifRegFormSessionsAdd(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-addSession'


class UHConfModifRegFormSessionsPerformAdd(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-performAddSession'


class UHConfModifRegFormSessionsRemove(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-removeSession'


class UHConfModifRegFormSessionItemModify(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-modifySessionItem'


class UHConfModifRegFormSessionItemPerformModify(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-performModifySessionItem'


class UHConfModifRegFormAccommodation(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-modifAccommodation'


class UHConfModifRegFormAccommodationDataModif(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-modifAccommodationData'


class UHConfModifRegFormAccommodationPerformDataModif(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-performModifAccommodationData'


class UHConfModifRegFormAccommodationTypeRemove(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-removeAccommodationType'


class UHConfModifRegFormAccommodationTypeAdd(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-addAccommodationType'


class UHConfModifRegFormAccommodationTypePerformAdd(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-performAddAccommodationType'


class UHConfModifRegFormAccommodationTypeModify(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-modifyAccommodationType'


class UHConfModifRegFormAccommodationTypePerformModify(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-performModifyAccommodationType'


class UHConfModifRegFormReasonParticipation(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-modifReasonParticipation'


class UHConfModifRegFormReasonParticipationDataModif(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-modifReasonParticipationData'


class UHConfModifRegFormReasonParticipationPerformDataModif(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-performModifReasonParticipationData'


class UHConfModifRegFormFurtherInformation(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-modifFurtherInformation'


class UHConfModifRegFormFurtherInformationDataModif(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-modifFurtherInformationData'


class UHConfModifRegFormFurtherInformationPerformDataModif(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-performModifFurtherInformationData'


class UHConfModifRegFormSocialEvent(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-modifSocialEvent'


class UHConfModifRegFormSocialEventDataModif(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-modifSocialEventData'


class UHConfModifRegFormSocialEventPerformDataModif(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-performModifSocialEventData'


class UHConfModifRegFormSocialEventRemove(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-removeSocialEvent'


class UHConfModifRegFormSocialEventAdd(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-addSocialEvent'


class UHConfModifRegFormSocialEventPerformAdd(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-performAddSocialEvent'


class UHConfModifRegFormSocialEventItemModify(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-modifySocialEventItem'


class UHConfModifRegFormSocialEventItemPerformModify(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-performModifySocialEventItem'


class UHConfModifRegFormActionStatuses(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-actionStatuses'


class UHConfModifRegFormStatusModif(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-modifStatus'


class UHConfModifRegFormStatusPerformModif(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-performModifStatus'


class UHConfModifRegFormActionSection(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-actionSection'


class UHConfModifRegFormGeneralSection(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-modifGeneralSection'


class UHConfModifRegFormGeneralSectionDataModif(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-modifGeneralSectionData'


class UHConfModifRegFormGeneralSectionPerformDataModif(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-performModifGeneralSectionData'


class UHConfModifRegFormGeneralSectionFieldAdd(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-addGeneralField'


class UHConfModifRegFormGeneralSectionFieldPerformAdd(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-performAddGeneralField'


class UHConfModifRegFormGeneralSectionFieldRemove(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-removeGeneralField'


class UHConfModifRegFormGeneralSectionFieldModif(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-modifGeneralField'


class UHConfModifRegFormGeneralSectionFieldPerformModif(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-performModifGeneralField'


class UHConfModifRegistrationPreview(URLHandler):
    _endpoint = 'legacy.confModifRegistrationPreview'


class UHConfModifRegistrantList(URLHandler):
    _endpoint = 'legacy.confModifRegistrants'


class UHConfModifRegistrantNew(URLHandler):
    _endpoint = 'legacy.confModifRegistrants-newRegistrant'


class UHConfModifRegistrantsOpenMenu(URLHandler):
    _endpoint = 'legacy.confModifRegistrants-openMenu'


class UHConfModifRegistrantsCloseMenu(URLHandler):
    _endpoint = 'legacy.confModifRegistrants-closeMenu'


class UHConfModifRegistrantListAction(URLHandler):
    _endpoint = 'legacy.confModifRegistrants-action'


class UHConfModifRegistrantPerformRemove(URLHandler):
    _endpoint = 'legacy.confModifRegistrants-remove'


class UHRegistrantModification(URLHandler):
    _endpoint = 'legacy.confModifRegistrants-modification'


class UHRegistrantAttachmentFileAccess(URLHandler):
    _endpoint = 'legacy.confModifRegistrants-getAttachedFile'


class UHConfModifRegFormEnableSection(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-enableSection'


class UHConfModifRegFormEnablePersonalField(URLHandler):
    _endpoint = 'legacy.confModifRegistrationForm-enablePersonalField'


class UHCategoryStatistics(URLHandler):
    _endpoint = 'category.categoryStatistics'


class UHCategoryToiCal(URLHandler):
    _endpoint = 'category.categoryDisplay-ical'


class UHCategoryToRSS(URLHandler):
    _endpoint = 'category.categoryDisplay-rss'


class UHCategoryToAtom(URLHandler):
    _endpoint = 'category.categoryDisplay-atom'


class UHCategOverviewToRSS(URLHandler):
    _endpoint = 'category.categOverview-rss'


class UHConfRegistrantsList(URLHandler):
    _endpoint = 'event.confRegistrantsDisplay-list'


class UHConfModifRegistrantSessionModify(URLHandler):
    _endpoint = 'legacy.confModifRegistrants-modifySessions'


class UHConfModifRegistrantSessionPeformModify(URLHandler):
    _endpoint = 'legacy.confModifRegistrants-performModifySessions'


class UHConfModifRegistrantTransactionModify(URLHandler):
    _endpoint = 'legacy.confModifRegistrants-modifyTransaction'


class UHConfModifRegistrantTransactionPeformModify(URLHandler):
    _endpoint = 'legacy.confModifRegistrants-peformModifyTransaction'


class UHConfModifRegistrantAccoModify(URLHandler):
    _endpoint = 'legacy.confModifRegistrants-modifyAccommodation'


class UHConfModifRegistrantAccoPeformModify(URLHandler):
    _endpoint = 'legacy.confModifRegistrants-performModifyAccommodation'


class UHConfModifRegistrantSocialEventsModify(URLHandler):
    _endpoint = 'legacy.confModifRegistrants-modifySocialEvents'


class UHConfModifRegistrantSocialEventsPeformModify(URLHandler):
    _endpoint = 'legacy.confModifRegistrants-performModifySocialEvents'


class UHConfModifRegistrantReasonPartModify(URLHandler):
    _endpoint = 'legacy.confModifRegistrants-modifyReasonParticipation'


class UHConfModifRegistrantReasonPartPeformModify(URLHandler):
    _endpoint = 'legacy.confModifRegistrants-performModifyReasonParticipation'


class UHConfModifPendingQueues(URLHandler):
    _endpoint = 'event_mgmt.confModifPendingQueues'


class UHConfModifPendingQueuesActionConfSubm(URLHandler):
    _endpoint = 'event_mgmt.confModifPendingQueues-actionConfSubmitters'


class UHConfModifPendingQueuesActionSubm(URLHandler):
    _endpoint = 'event_mgmt.confModifPendingQueues-actionSubmitters'


class UHConfModifPendingQueuesActionMgr(URLHandler):
    _endpoint = 'event_mgmt.confModifPendingQueues-actionManagers'


class UHConfModifPendingQueuesActionCoord(URLHandler):
    _endpoint = 'event_mgmt.confModifPendingQueues-actionCoordinators'


class UHConfModifRegistrantMiscInfoModify(URLHandler):
    _endpoint = 'legacy.confModifRegistrants-modifyMiscInfo'


class UHConfModifRegistrantMiscInfoPerformModify(URLHandler):
    _endpoint = 'legacy.confModifRegistrants-performModifyMiscInfo'


class UHUserSearchCreateExternalUser(URLHandler):
    _endpoint = 'legacy.userSelection-createExternalUsers'


class UHConfModifRegistrantStatusesModify(URLHandler):
    _endpoint = 'legacy.confModifRegistrants-modifyStatuses'


class UHConfModifRegistrantStatusesPerformModify(URLHandler):
    _endpoint = 'legacy.confModifRegistrants-performModifyStatuses'


class UHGetCalendarOverview(URLHandler):
    _endpoint = 'category.categOverview'


class UHCategoryCalendarOverview(URLHandler):
    _endpoint = 'category.wcalendar'


# URL Handlers for Printing and Design
class UHConfModifBadgePrinting(URLHandler):
    _endpoint = "event_mgmt.confModifTools-badgePrinting"

    @classmethod
    def getURL(cls, target=None, templateId=None, deleteTemplateId=None, cancel=False, new=False, copyTemplateId=None):
        """
          -The deleteTemplateId param should be set if we want to erase a template.
          -The copyTemplateId param should be set if we want to duplicate a template
          -The cancel param should be set to True if we return to this url
          after cancelling a template creation or edit (it is used to delete
          temporary template backgrounds).
          -The new param should be set to true if we return to this url
          after creating a new template.
        """
        url = cls._getURL()
        if target is not None:
            if target.getId() == 'default':
                url = UHBadgeTemplatePrinting._getURL()
            url.setParams(target.getLocator())
            if templateId is not None:
                url.addParam("templateId", templateId)
            if deleteTemplateId is not None:
                url.addParam("deleteTemplateId", deleteTemplateId)
            if copyTemplateId is not None:
                url.addParam("copyTemplateId", copyTemplateId)
            if cancel:
                url.addParam("cancel", True)
            if new:
                url.addParam("new", True)
        return url


class UHBadgeTemplatePrinting(URLHandler):
    _endpoint = 'admin.badgeTemplates-badgePrinting'


class UHConfModifBadgeDesign(URLHandler):
    _endpoint = 'event_mgmt.confModifTools-badgeDesign'

    @classmethod
    def getURL(cls, target=None, templateId=None, new=False):
        """
          -The templateId param should always be set:
           *if we are editing a template, it's the id of the template edited.
           *if we are creating a template, it's the id that the template will
           have after being stored for the first time.
          -The new param should be set to True if we are creating a new template.
        """
        url = cls._getURL()
        if target is not None:
            if target.getId() == 'default':
                url = UHModifDefTemplateBadge._getURL()
            url.setParams(target.getLocator())
            if templateId is not None:
                url.addParam("templateId", templateId)
            url.addParam("new", new)
        return url


class UHModifDefTemplateBadge(URLHandler):
    _endpoint = 'admin.badgeTemplates-badgeDesign'

    @classmethod
    def getURL(cls, target=None, templateId=None, new=False):
        """
          -The templateId param should always be set:
           *if we are editing a template, it's the id of the template edited.
           *if we are creating a template, it's the id that the template will
           have after being stored for the first time.
          -The new param should be set to True if we are creating a new template.
        """
        url = cls._getURL()
        if target is not None:
            url.setParams(target.getLocator())
            if templateId is not None:
                url.addParam("templateId", templateId)
            url.addParam("new", new)
        return url


class UHConfModifBadgeSaveBackground(URLHandler):
    _endpoint = 'event_mgmt.confModifTools-badgeSaveBackground'

    @classmethod
    def getURL(cls, target=None, templateId=None):
        url = cls._getURL()
        if target is not None and templateId is not None:
            url.setParams(target.getLocator())
            url.addParam("templateId", templateId)
        return url


class UHConfModifBadgeGetBackground(URLHandler):
    _endpoint = 'event_mgmt.confModifTools-badgeGetBackground'

    @classmethod
    def getURL(cls, target=None, templateId=None, backgroundId=None):
        url = cls._getURL()
        if target is not None and templateId is not None:
            url.setParams(target.getLocator())
            url.addParam("templateId", templateId)
            url.addParam("backgroundId", backgroundId)
        return url


class UHConfModifBadgePrintingPDF(URLHandler):
    _endpoint = 'event_mgmt.confModifTools-badgePrintingPDF'


# URL Handlers for Poster Printing and Design
class UHConfModifPosterPrinting(URLHandler):
    _endpoint = 'event_mgmt.confModifTools-posterPrinting'

    @classmethod
    def getURL(cls, target=None, templateId=None, deleteTemplateId=None, cancel=False, new=False, copyTemplateId=None):
        """
          -The deleteTemplateId param should be set if we want to erase a template.
          -The copyTemplateId param should be set if we want to duplicate a template
          -The cancel param should be set to True if we return to this url
          after cancelling a template creation or edit (it is used to delete
          temporary template backgrounds).
          -The new param should be set to true if we return to this url
          after creating a new template.
        """
        url = cls._getURL()

        if target is not None:
            if target.getId() == 'default':
                url = UHPosterTemplatePrinting._getURL()
            url.setParams(target.getLocator())
            if templateId is not None:
                url.addParam("templateId", templateId)
            if deleteTemplateId is not None:
                url.addParam("deleteTemplateId", deleteTemplateId)
            if copyTemplateId is not None:
                url.addParam("copyTemplateId", copyTemplateId)
            if cancel:
                url.addParam("cancel", True)
            if new:
                url.addParam("new", True)
        return url


class UHPosterTemplatePrinting(URLHandler):
    _endpoint = 'admin.posterTemplates-posterPrinting'


class UHConfModifPosterDesign(URLHandler):
    _endpoint = 'event_mgmt.confModifTools-posterDesign'

    @classmethod
    def getURL(cls, target=None, templateId=None, new=False):
        """
          -The templateId param should always be set:
           *if we are editing a template, it's the id of the template edited.
           *if we are creating a template, it's the id that the template will
           have after being stored for the first time.
          -The new param should be set to True if we are creating a new template.
        """
        url = cls._getURL()
        if target is not None:
            if target.getId() == 'default':
                url = UHModifDefTemplatePoster._getURL()
            url.setParams(target.getLocator())
            if templateId is not None:
                url.addParam("templateId", templateId)
            url.addParam("new", new)
        return url


class UHModifDefTemplatePoster(URLHandler):
    _endpoint = 'admin.posterTemplates-posterDesign'

    @classmethod
    def getURL(cls, target=None, templateId=None, new=False):
        """
          -The templateId param should always be set:
           *if we are editing a template, it's the id of the template edited.
           *if we are creating a template, it's the id that the template will
           have after being stored for the first time.
          -The new param should be set to True if we are creating a new template.
        """
        url = cls._getURL()
        if target is not None:
            url.setParams(target.getLocator())
            if templateId is not None:
                url.addParam("templateId", templateId)
            url.addParam("new", new)
        return url


class UHConfModifPosterSaveBackground(URLHandler):
    _endpoint = 'event_mgmt.confModifTools-posterSaveBackground'

    @classmethod
    def getURL(cls, target=None, templateId=None):
        url = cls._getURL()
        if target is not None and templateId is not None:
            url.setParams(target.getLocator())
            url.addParam("templateId", templateId)
        return url


class UHConfModifPosterGetBackground(URLHandler):
    _endpoint = 'event_mgmt.confModifTools-posterGetBackground'

    @classmethod
    def getURL(cls, target=None, templateId=None, backgroundId=None):
        url = cls._getURL()
        if target is not None and templateId is not None:
            url.setParams(target.getLocator())
            url.addParam("templateId", templateId)
            url.addParam("backgroundId", backgroundId)
        return url


class UHConfModifPosterPrintingPDF(URLHandler):
    _endpoint = 'event_mgmt.confModifTools-posterPrintingPDF'


class UHJsonRpcService(OptionallySecureURLHandler):
    _endpoint = 'api.jsonrpc'


class UHAPIExport(OptionallySecureURLHandler):
    _endpoint = 'api.httpapi'
    _defaultParams = dict(prefix='export')


class UHAPIAPI(OptionallySecureURLHandler):
    _endpoint = 'api.httpapi'
    _defaultParams = dict(prefix='api')


############
#Evaluation# DISPLAY AREA
############

class UHConfEvaluationMainInformation(URLHandler):
    _endpoint = 'event.confDisplayEvaluation'


class UHConfEvaluationDisplay(URLHandler):
    _endpoint = 'event.confDisplayEvaluation-display'


class UHConfEvaluationDisplayModif(URLHandler):
    _endpoint = 'event.confDisplayEvaluation-modif'


class UHConfEvaluationSignIn(URLHandler):
    _endpoint = 'event.confDisplayEvaluation-signIn'

    @classmethod
    def getURL(cls, conf, returnURL=''):
        url = cls._getURL()
        url.setParams(conf.getLocator())
        if returnURL:
            url.addParam('returnURL', returnURL)
        return url


class UHConfEvaluationSubmit(URLHandler):
    _endpoint = 'event.confDisplayEvaluation-submit'


class UHConfEvaluationSubmitted(URLHandler):
    _endpoint = 'event.confDisplayEvaluation-submitted'


############
#Evaluation# MANAGEMENT AREA
############
class UHConfModifEvaluation(URLHandler):
    _endpoint = 'event_mgmt.confModifEvaluation'


class UHConfModifEvaluationSetup(URLHandler):
    """same result as UHConfModifEvaluation."""
    _endpoint = 'event_mgmt.confModifEvaluation-setup'


class UHConfModifEvaluationSetupChangeStatus(URLHandler):
    _endpoint = 'event_mgmt.confModifEvaluation-changeStatus'


class UHConfModifEvaluationSetupSpecialAction(URLHandler):
    _endpoint = 'event_mgmt.confModifEvaluation-specialAction'


class UHConfModifEvaluationDataModif(URLHandler):
    _endpoint = 'event_mgmt.confModifEvaluation-dataModif'


class UHConfModifEvaluationPerformDataModif(URLHandler):
    _endpoint = 'event_mgmt.confModifEvaluation-performDataModif'


class UHConfModifEvaluationEdit(URLHandler):
    _endpoint = 'event_mgmt.confModifEvaluation-edit'


class UHConfModifEvaluationEditPerformChanges(URLHandler):
    _endpoint = 'event_mgmt.confModifEvaluation-editPerformChanges'


class UHConfModifEvaluationPreview(URLHandler):
    _endpoint = 'event_mgmt.confModifEvaluation-preview'


class UHConfModifEvaluationResults(URLHandler):
    _endpoint = 'event_mgmt.confModifEvaluation-results'


class UHConfModifEvaluationResultsOptions(URLHandler):
    _endpoint = 'event_mgmt.confModifEvaluation-resultsOptions'


class UHConfModifEvaluationResultsSubmittersActions(URLHandler):
    _endpoint = 'event_mgmt.confModifEvaluation-resultsSubmittersActions'


class UHResetSession(URLHandler):
    _endpoint = 'misc.resetSessionTZ'


##############
# Reviewing
#############
class UHConfModifReviewingAccess(URLHandler):
    _endpoint = 'legacy.confModifReviewing-access'


class UHConfModifReviewingPaperSetup(URLHandler):
    _endpoint = 'legacy.confModifReviewing-paperSetup'


class UHChooseReviewing(URLHandler):
    _endpoint = 'legacy.confModifReviewing-chooseReviewing'


class UHAddState(URLHandler):
    _endpoint = 'legacy.confModifReviewing-addState'


class UHRemoveState(URLHandler):
    _endpoint = 'legacy.confModifReviewing-removeState'


class UHAddQuestion(URLHandler):
    _endpoint = 'legacy.confModifReviewing-addQuestion'


class UHRemoveQuestion(URLHandler):
    _endpoint = 'legacy.confModifReviewing-removeQuestion'


class UHSetTemplate(URLHandler):
    _endpoint = 'legacy.confModifReviewing-setTemplate'


class UHAddCriteria(URLHandler):
    _endpoint = 'legacy.confModifReviewing-addCriteria'


class UHRemoveCriteria(URLHandler):
    _endpoint = 'legacy.confModifReviewing-removeCriteria'


class UHDownloadContributionTemplate(URLHandler):
    _endpoint = 'legacy.confModifReviewing-downloadTemplate'


class UHDeleteContributionTemplate(URLHandler):
    _endpoint = 'legacy.confModifReviewing-deleteTemplate'


class UHConfModifReviewingControl(URLHandler):
    _endpoint = 'legacy.confModifReviewingControl'


class UHConfModifUserCompetences(URLHandler):
    _endpoint = 'legacy.confModifUserCompetences'


class UHConfModifUserCompetencesAbstracts(URLHandler):
    _endpoint = 'legacy.confModifUserCompetences-Abstracts'


class UHConfModifModifyUserCompetences(URLHandler):
    _endpoint = 'legacy.confModifUserCompetences-modifyCompetences'


class UHConfModifListContribToJudge(URLHandler):
    _endpoint = 'legacy.confListContribToJudge'


class UHConfModifListContribToJudgeAsReviewer(URLHandler):
    _endpoint = 'legacy.confListContribToJudge-asReviewer'


class UHConfModifListContribToJudgeAsEditor(URLHandler):
    _endpoint = 'legacy.confListContribToJudge-asEditor'


class UHConfModifReviewingAssignContributionsList(URLHandler):
    _endpoint = 'legacy.assignContributions'


class UHConfModifReviewingDownloadAcceptedPapers(URLHandler):
    _endpoint = 'legacy.assignContributions-downloadAcceptedPapers'


#Contribution reviewing
class UHContributionModifReviewing(URLHandler):
    _endpoint = 'legacy.contributionReviewing'


class UHContribModifReviewingMaterials(URLHandler):
    _endpoint = 'legacy.contributionReviewing-contributionReviewingMaterials'


class UHContributionReviewingJudgements(URLHandler):
    _endpoint = 'legacy.contributionReviewing-contributionReviewingJudgements'


class UHAssignReferee(URLHandler):
    _endpoint = 'legacy.contributionReviewing-assignReferee'


class UHRemoveAssignReferee(URLHandler):
    _endpoint = 'legacy.contributionReviewing-removeAssignReferee'


class UHAssignEditing(URLHandler):
    _endpoint = 'legacy.contributionReviewing-assignEditing'


class UHRemoveAssignEditing(URLHandler):
    _endpoint = 'legacy.contributionReviewing-removeAssignEditing'


class UHAssignReviewing(URLHandler):
    _endpoint = 'legacy.contributionReviewing-assignReviewing'


class UHRemoveAssignReviewing(URLHandler):
    _endpoint = 'legacy.contributionReviewing-removeAssignReviewing'


class UHFinalJudge(URLHandler):
    _endpoint = 'legacy.contributionReviewing-finalJudge'


class UHContributionModifReviewingHistory(URLHandler):
    _endpoint = 'legacy.contributionReviewing-reviewingHistory'


class UHContributionEditingJudgement(URLHandler):
    _endpoint = 'legacy.contributionEditingJudgement'


class UHJudgeEditing(URLHandler):
    _endpoint = 'legacy.contributionEditingJudgement-judgeEditing'


class UHContributionGiveAdvice(URLHandler):
    _endpoint = 'legacy.contributionGiveAdvice'


class UHGiveAdvice(URLHandler):
    _endpoint = 'legacy.contributionGiveAdvice-giveAdvice'


class UHRefereeDueDate(URLHandler):
    _endpoint = 'legacy.contributionReviewing-refereeDueDate'


class UHEditorDueDate(URLHandler):
    _endpoint = 'legacy.contributionReviewing-editorDueDate'


class UHReviewerDueDate(URLHandler):
    _endpoint = 'legacy.contributionReviewing-reviewerDueDate'


class UHDownloadPRTemplate(URLHandler):
    _endpoint = 'event.paperReviewingDisplay-downloadTemplate'


class UHUploadPaper(URLHandler):
    _endpoint = 'event.paperReviewingDisplay-uploadPaper'


class UHPaperReviewingDisplay(URLHandler):
    _endpoint = 'event.paperReviewingDisplay'


#### End of reviewing
class UHChangeLang(URLHandler):
    _endpoint = 'misc.changeLang'


class UHAbout(URLHandler):
    _endpoint = 'misc.about'


class UHContact(URLHandler):
    _endpoint = 'misc.contact'


class UHJSVars(URLHandler):
    _endpoint = 'misc.JSContent-getVars'


class UHHelper(object):
    """ Returns the display or modif UH for an object of a given class
    """

    modifUHs = {
        "Category": UHCategoryModification,
        "Conference": UHConferenceModification,
        "DefaultConference": UHConferenceModification,
        "Contribution": UHContributionModification,
        "AcceptedContribution": UHContributionModification,
        "Session": UHSessionModification,
        "SubContribution": UHSubContributionModification,
        "Track": UHTrackModification
    }

    displayUHs = {
        "Category": UHCategoryDisplay,
        "CategoryMap": UHCategoryMap,
        "CategoryOverview": UHCategoryOverview,
        "CategoryStatistics": UHCategoryStatistics,
        "CategoryCalendar": UHCategoryCalendarOverview,
        "Conference": UHConferenceDisplay,
        "Contribution": UHContributionDisplay,
        "AcceptedContribution": UHContributionDisplay,
        "Session": UHSessionDisplay,
        "Abstract": UHAbstractDisplay
    }

    @classmethod
    def getModifUH(cls, klazz):
        return cls.modifUHs.get(klazz.__name__, None)

    @classmethod
    def getDisplayUH(cls, klazz, type=""):
        return cls.displayUHs.get("%s%s" % (klazz.__name__, type), None)
