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

import re
import os
import string
import urlparse
from flask import request, session, url_for

from MaKaC.common.url import URL, EndpointURL
from indico.core.config import Config
import MaKaC.user as user
from MaKaC.common.utils import utf8rep
from MaKaC.common.timezoneUtils import nowutc
from MaKaC.common.contextManager import ContextManager


class BooleanOnMixin:
    """Mixin to convert True to 'on' and remove False altogether."""
    _true = 'on'

    @classmethod
    def _translateParams(cls, params):
        return dict((key, cls._true if value is True else value)
                    for key, value in params.iteritems()
                    if value is not False)


class BooleanTrueMixin(BooleanOnMixin):
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
    def getStaticURL(cls, target=None, **params):
        if cls._relativeURL:
            return cls._relativeURL.replace('.py', '.html')
        else:
            # yay, super ugly, but it works...
            return re.sub(r'^event\.', '', cls._endpoint) + '.html'

    @classmethod
    def _getURL(cls, _force_secure=None, **params):
        """ Gives the full URL for the corresponding request handler.

            Parameters:
                _force_secure - (bool) create a secure url if possible
                params - (dict) parameters to be added to the URL.
        """

        try:
            secure = _force_secure if _force_secure is not None else request.is_secure
        except RuntimeError:
            # Outside Flask request context
            secure = False

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
    def getURL(cls, target=None, _ignore_static=False, **params):
        """Gives the full URL for the corresponding request handler. In case
            the target parameter is specified it will append to the URL the
            the necessary parameters to make the target be specified in the url.

            Parameters:
                target - (Locable) Target object which must be uniquely
                    specified in the URL so the destination request handler
                    is able to retrieve it.
                params - (Dict) parameters to be added to the URL.
        """
        if not _ignore_static and ContextManager.get('offlineMode', False):
            return URL(cls.getStaticURL(target, **params))
        return cls._getURL(**cls._getParams(target, params))


class SecureURLHandler(URLHandler):
    @classmethod
    def getURL(cls, target=None, **params):
        return cls._getURL(_force_secure=True, **cls._getParams(target, params))


class OptionallySecureURLHandler(URLHandler):
    @classmethod
    def getURL(cls, target=None, secure=False, **params):
        return cls._getURL(_force_secure=secure, **cls._getParams(target, params))


class UserURLHandler(URLHandler):
    """Strips the userId param if it's the current user"""

    @classmethod
    def _translateParams(cls, params):
        if 'userId' in params and session.get('_avatarId') == params['userId']:
            del params['userId']
        return params


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


class UHSignInSSO(SecureURLHandler):
    _endpoint = "user.signIn-sso"


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


class UHOAuthAuthorizeConsumer(UserURLHandler):
    _endpoint = 'oauth.oauth-authorize_consumer'


class UHOAuthThirdPartyAuth(UserURLHandler):
    _endpoint = 'oauth.oauth-thirdPartyAuth'


class UHOAuthUserThirdPartyAuth(UserURLHandler):
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

    @classmethod
    def getURL(cls, target):
        if ContextManager.get('offlineMode', False):
            return URL(UHConferenceDisplay.getStaticURL(target))
        return super(UHConferenceOverview, cls).getURL(target)


class UHConferenceEmail(URLHandler):
    _endpoint = 'event.EMail'

    @classmethod
    def getStaticURL(cls, target, **params):
        if target is not None:
            return "mailto:%s" % str(target.getEmail())
        return cls.getURL(target)


class UHConferenceSendEmail(URLHandler):
    _endpoint = 'event.EMail-send'


class UHRegistrantsSendEmail(URLHandler):
    _endpoint = 'event_mgmt.EMail-sendreg'


class UHConvenersSendEmail(URLHandler):
    _endpoint = 'event_mgmt.EMail-sendconvener'


class UHContribParticipantsSendEmail(URLHandler):
    _endpoint = 'event_mgmt.EMail-sendcontribparticipants'


class UHConferenceOtherViews(URLHandler):
    _endpoint = 'event.conferenceOtherViews'


class UHConferenceLogo(URLHandler):
    _endpoint = 'event.conferenceDisplay-getLogo'

    @classmethod
    def getStaticURL(cls, target, **params):
        return os.path.join(Config.getInstance().getImagesBaseURL(), "logo", str(target.getLogo()))


class UHConferenceCSS(URLHandler):
    _endpoint = 'event.conferenceDisplay-getCSS'

    @classmethod
    def getStaticURL(cls, target, **params):
        return cls.getURL(target, _ignore_static=True, **params)


class UHConferencePic(URLHandler):
    _endpoint = 'event.conferenceDisplay-getPic'


class UHConfModifPreviewCSS(URLHandler):
    _endpoint = 'event_mgmt.confModifDisplay-previewCSS'


class UHCategoryIcon(URLHandler):
    _endpoint = 'category.categoryDisplay-getIcon'


class UHConferenceModification(URLHandler):
    _endpoint = 'event_mgmt.conferenceModification'


class UHConfModifShowMaterials(URLHandler):
    _endpoint = 'event_mgmt.conferenceModification-materialsShow'


class UHConfModifAddMaterials(URLHandler):
    _endpoint = 'event_mgmt.conferenceModification-materialsAdd'

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
    _endpoint = 'event_mgmt.conferenceModification-roomBookingChooseEvent'


class UHConfModifRoomBookingSearch4Rooms(BooleanTrueMixin, URLHandler):
    _endpoint = 'event_mgmt.conferenceModification-roomBookingSearch4Rooms'


class UHConfModifRoomBookingList(URLHandler):
    _endpoint = 'event_mgmt.conferenceModification-roomBookingList'


class UHConfModifRoomBookingRoomList(URLHandler):
    _endpoint = 'event_mgmt.conferenceModification-roomBookingRoomList'


class UHConfModifRoomBookingDetails(URLHandler):
    _endpoint = 'event_mgmt.conferenceModification-roomBookingDetails'


class UHConfModifRoomBookingRoomDetails(UHConfModifRoomBookingBase):
    _endpoint = 'event_mgmt.conferenceModification-roomBookingRoomDetails'


class UHConfModifRoomBookingBookingForm(UHConfModifRoomBookingBase):
    _endpoint = 'event_mgmt.conferenceModification-roomBookingBookingForm'


class UHConfModifRoomBookingModifyBookingForm(UHConfModifRoomBookingBase):
    _endpoint = 'event_mgmt.conferenceModification-roomBookingModifyBookingForm'


class UHConfModifRoomBookingCloneBooking(UHConfModifRoomBookingBase):
    _endpoint = 'event_mgmt.conferenceModification-roomBookingCloneBooking'

    @classmethod
    def getURL(cls, target=None, conf=None, **params):
        url = cls._getURL(**cls._getParams(target, params))
        if conf is not None:
            url.addParams(conf.getLocator())
        return url


class UHConfModifRoomBookingSaveBooking(URLHandler):
    _endpoint = 'event_mgmt.conferenceModification-roomBookingSaveBooking'


class UHRoomPhoto(URLHandler):
    _endpoint = 'rooms.photo_large'

    @classmethod
    def getURL(cls, target=None, extension="jpg"):
        return super(UHRoomPhoto, cls).getURL(room=target, ext=extension)


class UHRoomPhotoSmall(URLHandler):
    _endpoint = 'rooms.photo_small'

    @classmethod
    def getURL(cls, target=None, extension="jpg"):
        return super(UHRoomPhotoSmall, cls).getURL(room=target, ext=extension)


class UHConferenceClose(URLHandler):
    _endpoint = 'event_mgmt.conferenceModification-close'


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


class UHConfModifCFAOptFld(URLHandler):
    _endpoint = 'event_mgmt.confModifCFA-abstractFields'


class UHConfModifCFARemoveOptFld(URLHandler):
    _endpoint = 'event_mgmt.confModifCFA-removeAbstractField'


class UHConfModifCFAAbsFieldUp(URLHandler):
    _endpoint = 'event_mgmt.confModifCFA-absFieldUp'


class UHConfModifCFAAbsFieldDown(URLHandler):
    _endpoint = 'event_mgmt.confModifCFA-absFieldDown'


class UHConfModifProgram(URLHandler):
    _endpoint = 'event_mgmt.confModifProgram'


class UHConfModifCFA(URLHandler):
    _endpoint = 'event_mgmt.confModifCFA'


class UHConfModifCFAPreview(URLHandler):
    _endpoint = 'event_mgmt.confModifCFA-preview'


class UHConfCFAChangeStatus(URLHandler):
    _endpoint = 'event_mgmt.confModifCFA-changeStatus'


class UHConfCFASwitchMultipleTracks(URLHandler):
    _endpoint = 'event_mgmt.confModifCFA-switchMultipleTracks'


class UHConfCFAMakeTracksMandatory(URLHandler):
    _endpoint = 'event_mgmt.confModifCFA-makeTracksMandatory'


class UHConfCFAAllowAttachFiles(URLHandler):
    _endpoint = 'event_mgmt.confModifCFA-switchAttachFiles'


class UHAbstractAttachmentFileAccess(URLHandler):
    _endpoint = 'event.abstractDisplay-getAttachedFile'


class UHConfCFAShowSelectAsSpeaker(URLHandler):
    _endpoint = 'event_mgmt.confModifCFA-switchShowSelectSpeaker'


class UHConfCFASelectSpeakerMandatory(URLHandler):
    _endpoint = 'event_mgmt.confModifCFA-switchSelectSpeakerMandatory'


class UHConfCFAAttachedFilesContribList(URLHandler):
    _endpoint = 'event_mgmt.confModifCFA-switchShowAttachedFiles'


class UHCFADataModification(URLHandler):
    _endpoint = 'event_mgmt.confModifCFA-modifyData'


class UHCFAPerformDataModification(URLHandler):
    _endpoint = 'event_mgmt.confModifCFA-performModifyData'


class UHConfAbstractManagment(URLHandler):
    _endpoint = 'event_mgmt.abstractsManagment'


class UHConfAbstractList(URLHandler):
    _endpoint = 'event_mgmt.abstractsManagment'


class UHAbstractSubmission(URLHandler):
    _endpoint = 'event.abstractSubmission'


class UHAbstractSubmissionConfirmation(URLHandler):
    _endpoint = 'event.abstractSubmission-confirmation'


class UHAbstractDisplay(URLHandler):
    _endpoint = 'event.abstractDisplay'


class UHAbstractDisplayPDF(URLHandler):
    _endpoint = 'event.abstractDisplay-pdf'


class UHAbstractConfManagerDisplayPDF(URLHandler):
    _endpoint = 'event_mgmt.abstractManagment-abstractToPDF'


class UHAbstractConfSelectionAction(URLHandler):
    _endpoint = 'event_mgmt.abstractsManagment-abstractsActions'


class UHAbstractsConfManagerDisplayParticipantList(URLHandler):
    _endpoint = 'event_mgmt.abstractsManagment-participantList'


class UHUserAbstracts(URLHandler):
    _endpoint = 'event.userAbstracts'


class UHUserAbstractsPDF(URLHandler):
    _endpoint = 'event.userAbstracts-pdf'


class UHAbstractModify(URLHandler):
    _endpoint = 'event.abstractModify'


class UHCFAAbstractManagment(URLHandler):
    _endpoint = 'event_mgmt.abstractManagment'


class UHAbstractManagment(URLHandler):
    _endpoint = 'event_mgmt.abstractManagment'


class UHAbstractManagmentAccept(URLHandler):
    _endpoint = 'event_mgmt.abstractManagment-accept'


class UHAbstractManagmentAcceptMultiple(URLHandler):
    _endpoint = 'event_mgmt.abstractManagment-acceptMultiple'


class UHAbstractManagmentRejectMultiple(URLHandler):
    _endpoint = 'event_mgmt.abstractManagment-rejectMultiple'


class UHAbstractManagmentReject(URLHandler):
    _endpoint = 'event_mgmt.abstractManagment-reject'


class UHAbstractManagmentChangeTrack(URLHandler):
    _endpoint = 'event_mgmt.abstractManagment-changeTrack'


class UHAbstractTrackProposalManagment(URLHandler):
    _endpoint = 'event_mgmt.abstractManagment-trackProposal'


class UHAbstractTrackOrderByRating(URLHandler):
    _endpoint = 'event_mgmt.abstractManagment-orderByRating'


class UHAbstractDirectAccess(URLHandler):
    _endpoint = 'event_mgmt.abstractManagment-directAccess'


class UHAbstractToXML(URLHandler):
    _endpoint = 'event_mgmt.abstractManagment-xml'


class UHAbstractSubmissionDisplay(URLHandler):
    _endpoint = 'event.abstractSubmission'


class UHConfAddTrack(URLHandler):
    _endpoint = 'event_mgmt.confModifProgram-addTrack'


class UHConfDelTracks(URLHandler):
    _endpoint = 'event_mgmt.confModifProgram-deleteTracks'


class UHConfPerformAddTrack(URLHandler):
    _endpoint = 'event_mgmt.confModifProgram-performAddTrack'


class UHTrackModification(URLHandler):
    _endpoint = 'event_mgmt.trackModification'


class UHTrackModifAbstracts(URLHandler):
    _endpoint = 'event_mgmt.trackModifAbstracts'


class UHTrackAbstractBase(URLHandler):
    @classmethod
    def getURL(cls, track, abstract):
        url = cls._getURL()
        url.setParams(track.getLocator())
        url.addParam('abstractId', abstract.getId())
        return url


class UHTrackAbstractModif(UHTrackAbstractBase):
    _endpoint = 'event_mgmt.trackAbstractModif'


class UHAbstractTrackManagerDisplayPDF(UHTrackAbstractBase):
    _endpoint = 'event_mgmt.trackAbstractModif-abstractToPDF'


class UHAbstractsTrackManagerAction(URLHandler):
    _endpoint = 'event_mgmt.trackAbstractModif-abstractAction'


class UHTrackAbstractPropToAcc(UHTrackAbstractBase):
    _endpoint = 'event_mgmt.trackAbstractModif-proposeToBeAcc'


class UHTrackAbstractPropToRej(UHTrackAbstractBase):
    _endpoint = 'event_mgmt.trackAbstractModif-proposeToBeRej'


class UHTrackAbstractAccept(UHTrackAbstractBase):
    _endpoint = 'event_mgmt.trackAbstractModif-accept'


class UHTrackAbstractReject(UHTrackAbstractBase):
    _endpoint = 'event_mgmt.trackAbstractModif-reject'


class UHTrackAbstractDirectAccess(URLHandler):
    _endpoint = 'event_mgmt.trackAbstractModif-directAccess'


class UHTrackAbstractPropForOtherTrack(UHTrackAbstractBase):
    _endpoint = 'event_mgmt.trackAbstractModif-proposeForOtherTracks'


class UHTrackModifCoordination(URLHandler):
    _endpoint = 'event_mgmt.trackModifCoordination'


class UHTrackDataModif(URLHandler):
    _endpoint = 'event_mgmt.trackModification-modify'


class UHTrackPerformDataModification(URLHandler):
    _endpoint = 'event_mgmt.trackModification-performModify'


class UHTrackAbstractModIntComments(UHTrackAbstractBase):
    _endpoint = 'event_mgmt.trackAbstractModif-comments'


class UHConfModifSchedule(URLHandler):
    _endpoint = 'event_mgmt.confModifSchedule'


class UHContribConfSelectionAction(URLHandler):
    _endpoint = 'event_mgmt.confModifContribList-contribsActions'


class UHContribsConfManagerDisplayMenuPDF(URLHandler):
    _endpoint = 'event_mgmt.confModifContribList-contribsToPDFMenu'


class UHContribsConfManagerDisplayParticipantList(URLHandler):
    _endpoint = 'event_mgmt.confModifContribList-participantList'


class UHSessionClose(URLHandler):
    _endpoint = 'event_mgmt.sessionModification-close'


class UHSessionOpen(URLHandler):
    _endpoint = 'event_mgmt.sessionModification-open'


class UHSessionCreation(URLHandler):
    _endpoint = 'event_mgmt.confModifSchedule'


class UHContribCreation(URLHandler):
    _endpoint = 'event_mgmt.confModifSchedule'


class UHContribToXMLConfManager(URLHandler):
    _endpoint = 'event_mgmt.contributionModification-xml'


class UHContribToXML(URLHandler):
    _endpoint = 'event.contributionDisplay-xml'

    @classmethod
    def getStaticURL(cls, target, **params):
        return ""


class UHContribToiCal(URLHandler):
    _endpoint = 'event.contributionDisplay-ical'

    @classmethod
    def getStaticURL(cls, target, **params):
        return ""


class UHContribToPDFConfManager(URLHandler):
    _endpoint = 'event_mgmt.contributionModification-pdf'


class UHContribToPDF(URLHandler):
    _endpoint = 'event.contributionDisplay-pdf'

    @classmethod
    def getStaticURL(cls, target, **params):
        if target is not None:
            return "files/generatedPdf/%s-Contribution.pdf" % target.getId()


class UHContribModifAC(URLHandler):
    _endpoint = 'event_mgmt.contributionAC'


class UHContributionSetVisibility(URLHandler):
    _endpoint = 'event_mgmt.contributionAC-setVisibility'


class UHContribModifMaterialMgmt(URLHandler):
    _endpoint = 'event_mgmt.contributionModification-materials'


class UHContribModifAddMaterials(URLHandler):
    _endpoint = 'event_mgmt.contributionModification-materialsAdd'


class UHContribModifSubCont(URLHandler):
    _endpoint = 'event_mgmt.contributionModifSubCont'


class UHContribAddSubCont(URLHandler):
    _endpoint = 'event_mgmt.contributionModifSubCont-add'


class UHContribCreateSubCont(URLHandler):
    _endpoint = 'event_mgmt.contributionModifSubCont-create'


class UHSubContribActions(URLHandler):
    _endpoint = 'event_mgmt.contributionModifSubCont-actionSubContribs'


class UHContribModifTools(URLHandler):
    _endpoint = 'event_mgmt.contributionTools'


class UHContributionDataModif(URLHandler):
    _endpoint = 'event_mgmt.contributionModification-modifData'


class UHContributionDataModification(URLHandler):
    _endpoint = 'event_mgmt.contributionModification-data'


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
    _endpoint = 'event_mgmt.confModifParticipants'


class UHConfModifLog(URLHandler):
    _endpoint = 'event_mgmt.confModifLog'


class UHInternalPageDisplay(URLHandler):
    _endpoint = 'event.internalPage'

    @classmethod
    def getStaticURL(cls, target, **params):
        params = target.getLocator()
        url = os.path.join("internalPage-%s.html" % params["pageId"])
        return url


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


class UHConfModifDisplayToggleTimetableView(URLHandler):
    _endpoint = 'event_mgmt.confModifDisplay-toggleTimetableView'


class UHConfModifDisplayToggleTTDefaultLayout(URLHandler):
    _endpoint = 'event_mgmt.confModifDisplay-toggleTTDefaultLayout'


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
    _endpoint = 'event_mgmt.confModifParticipants-setup'


class UHConfModifParticipantsPending(URLHandler):
    _endpoint = 'event_mgmt.confModifParticipants-pendingParticipants'


class UHConfModifParticipantsDeclined(URLHandler):
    _endpoint = 'event_mgmt.confModifParticipants-declinedParticipants'


class UHConfModifParticipantsAction(URLHandler):
    _endpoint = 'event_mgmt.confModifParticipants-action'


class UHConfModifParticipantsStatistics(URLHandler):
    _endpoint = 'event_mgmt.confModifParticipants-statistics'


class UHConfParticipantsInvitation(URLHandler):
    _endpoint = 'event.confModifParticipants-invitation'


class UHConfParticipantsRefusal(URLHandler):
    _endpoint = 'event.confModifParticipants-refusal'


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
    def getURL(cls, conf, returnURL=""):
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
    _endpoint = 'event_mgmt.conferenceModification-modifKey'


class UHConfCloseModifKey(UHConfUser):
    _endpoint = 'event_mgmt.conferenceModification-closeModifKey'


class UHUserCreated(UHConfUser):
    _endpoint = 'user.userRegistration-created'


class UHUserActive(UserURLHandler):
    _endpoint = 'user.userRegistration-active'


class UHUserDisable(UserURLHandler):
    _endpoint = 'user.userRegistration-disable'


class UHUserDashboard(UserURLHandler):
    _endpoint = 'user.userDashboard'


class UHUserDetails(UserURLHandler):
    _endpoint = 'user.userDetails'


class UHUserBaskets(UserURLHandler):
    _endpoint = 'user.userBaskets'


class UHUserPreferences(UserURLHandler):
    _endpoint = 'user.userPreferences'


class UHUserAPI(UserURLHandler):
    _endpoint = 'user.userAPI'


class UHUserAPICreate(UserURLHandler):
    _endpoint = 'user.userAPI-create'


class UHUserAPIBlock(UserURLHandler):
    _endpoint = 'user.userAPI-block'


class UHUserAPIDelete(UserURLHandler):
    _endpoint = 'user.userAPI-delete'


class UHUserRegistration(URLHandler):
    _endpoint = 'user.userRegistration'


class UHUserIdentityCreation(UserURLHandler):
    _endpoint = 'user.identityCreation'


class UHUserRemoveIdentity(UserURLHandler):
    _endpoint = 'user.identityCreation-remove'


class UHUserExistWithIdentity(UHConfUser):
    _endpoint = 'user.userRegistration-UserExist'


class UHUserIdPerformCreation(UserURLHandler):
    _endpoint = 'user.identityCreation-create'


class UHUserIdentityChangePassword(UserURLHandler):
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
    _endpoint = 'category_mgmt.categoryModification'

    @classmethod
    def getActionURL(cls):
        return ''


class UHCategoryAddMaterial(URLHandler):
    _endpoint = 'category_mgmt.categoryFiles-addMaterial'


class UHCategoryActionSubCategs(URLHandler):
    _endpoint = 'category_mgmt.categoryModification-actionSubCategs'


class UHCategoryActionConferences(URLHandler):
    _endpoint = 'category_mgmt.categoryModification-actionConferences'


class UHCategModifAC(URLHandler):
    _endpoint = 'category_mgmt.categoryAC'


class UHCategorySetConfCreationControl(URLHandler):
    _endpoint = 'category_mgmt.categoryConfCreationControl-setCreateConferenceControl'


class UHCategorySetNotifyCreation(URLHandler):
    _endpoint = 'category_mgmt.categoryConfCreationControl-setNotifyCreation'


class UHCategModifTools(URLHandler):
    _endpoint = 'category_mgmt.categoryTools'


class UHCategoryDeletion(URLHandler):
    _endpoint = 'category_mgmt.categoryTools-delete'


class UHCategModifTasks(URLHandler):
    _endpoint = 'category_mgmt.categoryTasks'


class UHCategModifFiles(URLHandler):
    _endpoint = 'category_mgmt.categoryFiles'


class UHCategModifTasksAction(URLHandler):
    _endpoint = 'category_mgmt.categoryTasks-taskAction'


class UHCategoryDataModif(URLHandler):
    _endpoint = 'category_mgmt.categoryDataModification'


class UHCategoryPerformModification(URLHandler):
    _endpoint = 'category_mgmt.categoryDataModification-modify'


class UHCategoryTasksOption(URLHandler):
    _endpoint = 'category_mgmt.categoryDataModification-tasksOption'


class UHCategorySetVisibility(URLHandler):
    _endpoint = 'category_mgmt.categoryAC-setVisibility'


class UHCategoryCreation(URLHandler):
    _endpoint = 'category_mgmt.categoryCreation'


class UHCategoryPerformCreation(URLHandler):
    _endpoint = 'category_mgmt.categoryCreation-create'


class UHCategoryDisplay(URLHandler):
    _endpoint = 'category.categoryDisplay'

    @classmethod
    def getURL(cls, target=None, **params):
        url = cls._getURL(**params)
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
    _endpoint = 'event_mgmt.contributionTools-delete'


class UHSubContributionDataModification(URLHandler):
    _endpoint = 'event_mgmt.subContributionModification-data'


class UHSubContributionDataModif(URLHandler):
    _endpoint = 'event_mgmt.subContributionModification-modifData'


class UHSubContributionDelete(URLHandler):
    _endpoint = 'event_mgmt.subContributionTools-delete'


class UHSubContribModifAddMaterials(URLHandler):
    _endpoint = 'event_mgmt.subContributionModification-materialsAdd'


class UHSubContribModifTools(URLHandler):
    _endpoint = 'event_mgmt.subContributionTools'


class UHSessionModification(URLHandler):
    _endpoint = 'event_mgmt.sessionModification'


class UHSessionModifMaterials(URLHandler):
    _endpoint = 'event_mgmt.sessionModification-materials'


class UHSessionDataModification(URLHandler):
    _endpoint = 'event_mgmt.sessionModification-modify'


class UHSessionFitSlot(URLHandler):
    _endpoint = 'event_mgmt.sessionModifSchedule-fitSlot'


class UHSessionModifAddMaterials(URLHandler):
    _endpoint = 'event_mgmt.sessionModification-materialsAdd'


class UHSessionModifSchedule(URLHandler):
    _endpoint = 'event_mgmt.sessionModifSchedule'


class UHSessionModSlotCalc(URLHandler):
    _endpoint = 'event_mgmt.sessionModifSchedule-slotCalc'


class UHSessionModifAC(URLHandler):
    _endpoint = 'event_mgmt.sessionModifAC'


class UHSessionSetVisibility(URLHandler):
    _endpoint = 'event_mgmt.sessionModifAC-setVisibility'


class UHSessionModifTools(URLHandler):
    _endpoint = 'event_mgmt.sessionModifTools'


class UHSessionModifComm(URLHandler):
    _endpoint = 'event_mgmt.sessionModifComm'


class UHSessionModifCommEdit(URLHandler):
    _endpoint = 'event_mgmt.sessionModifComm-edit'


class UHSessionDeletion(URLHandler):
    _endpoint = 'event_mgmt.sessionModifTools-delete'


class UHContributionModification(URLHandler):
    _endpoint = 'event_mgmt.contributionModification'


class UHContribModifMaterials(URLHandler):
    _endpoint = 'event_mgmt.contributionModification-materials'


class UHSubContribModification(URLHandler):
    _endpoint = 'event_mgmt.subContributionModification'


class UHSubContribModifMaterials(URLHandler):
    _endpoint = 'event_mgmt.subContributionModification-materials'


class UHMaterialDisplay(URLHandler):
    _endpoint = 'files.materialDisplay'

    @classmethod
    def getStaticURL(cls, target, **params):
        if target is not None:
            params = target.getLocator()
            resources = target.getOwner().getMaterialById(params["materialId"]).getResourceList()
            if len(resources) == 1:
                return UHFileAccess.getStaticURL(resources[0])
            return "materialDisplay-%s.html" % params["materialId"]
        return cls._getURL()


class UHConferenceProgram(URLHandler):
    _endpoint = 'event.conferenceProgram'


class UHConferenceProgramPDF(URLHandler):
    _endpoint = 'event.conferenceProgram-pdf'

    @classmethod
    def getStaticURL(cls, target, **params):
        return "files/generatedPdf/Programme.pdf"


class UHConferenceTimeTable(URLHandler):
    _endpoint = 'event.conferenceTimeTable'


class UHConfTimeTablePDF(URLHandler):
    _endpoint = 'event.conferenceTimeTable-pdf'

    @classmethod
    def getStaticURL(cls, target, **params):
        if target is not None:
            params = target.getLocator()
            from MaKaC import conference

            if isinstance(target, conference.Conference):
                return "files/generatedPdf/Conference.pdf"
            if isinstance(target, conference.Contribution):
                return "files/generatedPdf/%s-Contribution.pdf" % (params["contribId"])
            elif isinstance(target, conference.Session) or isinstance(target, conference.SessionSlot):
                return "files/generatedPdf/%s-Session.pdf" % (params["sessionId"])
        return cls._getURL()


class UHConferenceCFA(URLHandler):
    _endpoint = 'event.conferenceCFA'


class UHSessionDisplay(URLHandler):
    _endpoint = 'event.sessionDisplay'

    @classmethod
    def getStaticURL(cls, target, **params):
        if target is not None:
            params.update(target.getLocator())
        return "%s-session.html" % params["sessionId"]


class UHSessionToiCal(URLHandler):
    _endpoint = 'event.sessionDisplay-ical'


class UHContributionDisplay(URLHandler):
    _endpoint = 'event.contributionDisplay'

    @classmethod
    def getStaticURL(cls, target, **params):
        if target is not None:
            params = target.getLocator()
            return "%s-contrib.html" % (params["contribId"])
        return cls.getURL(target, _ignore_static=True, **params)


class UHSubContributionDisplay(URLHandler):
    _endpoint = 'event.subContributionDisplay'

    @classmethod
    def getStaticURL(cls, target, **params):
        if target is not None:
            params = target.getLocator()
            return "%s-subcontrib.html" % (params["subContId"])
        return cls.getURL(target, _ignore_static=True, **params)


class UHSubContributionModification(URLHandler):
    _endpoint = 'event_mgmt.subContributionModification'


class UHFileAccess(URLHandler):
    _endpoint = 'files.getFile-access'

    @staticmethod
    def generateFileStaticLink(target):
        from MaKaC import conference

        params = target.getLocator()
        owner = target.getOwner().getOwner()

        if isinstance(owner, conference.Conference):
            path = "events/conference"
        elif isinstance(owner, conference.Session):
            path = "agenda/%s-session" % owner.getId()
        elif isinstance(owner, conference.Contribution):
            path = "agenda/%s-contribution" % owner.getId()
        elif isinstance(owner, conference.SubContribution):
            path = "agenda/%s-subcontribution" % owner.getId()
        else:
            return None
        url = os.path.join("files", path, params["materialId"], params["resId"] + "-" + target.getName())
        return url

    @classmethod
    def getStaticURL(cls, target, **params):
        return cls.generateFileStaticLink(target) or cls.getURL(target, _ignore_static=True, **params)


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
    _endpoint = 'event_mgmt.confModifContribList'


class UHContribModifMaterialBrowse(URLHandler):
    _endpoint = 'event_mgmt.contributionModification-browseMaterial'


class UHContribModSetTrack(URLHandler):
    _endpoint = 'event_mgmt.contributionModification-setTrack'


class UHContribModSetSession(URLHandler):
    _endpoint = 'event_mgmt.contributionModification-setSession'


class UHTrackModMoveUp(URLHandler):
    _endpoint = 'event_mgmt.confModifProgram-moveTrackUp'


class UHTrackModMoveDown(URLHandler):
    _endpoint = 'event_mgmt.confModifProgram-moveTrackDown'


class UHAbstractModEditData(URLHandler):
    _endpoint = 'event_mgmt.abstractManagment-editData'


class UHAbstractModIntComments(URLHandler):
    _endpoint = 'event_mgmt.abstractManagment-comments'


class UHAbstractModNewIntComment(URLHandler):
    _endpoint = 'event_mgmt.abstractManagment-newComment'


class UHAbstractModIntCommentEdit(URLHandler):
    _endpoint = 'event_mgmt.abstractManagment-editComment'


class UHAbstractModIntCommentRem(URLHandler):
    _endpoint = 'event_mgmt.abstractManagment-remComment'


class UHTrackAbstractModIntCommentNew(UHTrackAbstractBase):
    _endpoint = 'event_mgmt.trackAbstractModif-commentNew'


class UHTrackAbstractModCommentBase(URLHandler):
    @classmethod
    def getURL(cls, track, comment):
        url = cls._getURL()
        url.setParams(comment.getLocator())
        url.addParam("trackId", track.getId())
        return url


class UHTrackAbstractModIntCommentEdit(UHTrackAbstractModCommentBase):
    _endpoint = 'event_mgmt.trackAbstractModif-commentEdit'


class UHTrackAbstractModIntCommentRem(UHTrackAbstractModCommentBase):
    _endpoint = 'event_mgmt.trackAbstractModif-commentRem'


class UHAbstractReviewingNotifTpl(URLHandler):
    _endpoint = 'event_mgmt.abstractReviewing-notifTpl'


class UHAbstractModNotifTplNew(URLHandler):
    _endpoint = 'event_mgmt.abstractReviewing-notifTplNew'


class UHAbstractModNotifTplRem(URLHandler):
    _endpoint = 'event_mgmt.abstractReviewing-notifTplRem'


class UHAbstractModNotifTplEdit(URLHandler):
    _endpoint = 'event_mgmt.abstractReviewing-notifTplEdit'


class UHAbstractModNotifTplDisplay(URLHandler):
    _endpoint = 'event_mgmt.abstractReviewing-notifTplDisplay'


class UHAbstractModNotifTplPreview(URLHandler):
    _endpoint = 'event_mgmt.abstractReviewing-notifTplPreview'


class UHTrackAbstractModMarkAsDup(UHTrackAbstractBase):
    _endpoint = 'event_mgmt.trackAbstractModif-markAsDup'


class UHTrackAbstractModUnMarkAsDup(UHTrackAbstractBase):
    _endpoint = 'event_mgmt.trackAbstractModif-unMarkAsDup'


class UHAbstractModMarkAsDup(URLHandler):
    _endpoint = 'event_mgmt.abstractManagment-markAsDup'


class UHAbstractModUnMarkAsDup(URLHandler):
    _endpoint = 'event_mgmt.abstractManagment-unMarkAsDup'


class UHAbstractModMergeInto(URLHandler):
    _endpoint = 'event_mgmt.abstractManagment-mergeInto'


class UHAbstractModUnMerge(URLHandler):
    _endpoint = 'event_mgmt.abstractManagment-unmerge'


class UHConfModNewAbstract(URLHandler):
    _endpoint = 'event_mgmt.abstractsManagment-newAbstract'


class UHConfModNotifTplConditionNew(URLHandler):
    _endpoint = 'event_mgmt.abstractReviewing-notifTplCondNew'


class UHConfModNotifTplConditionRem(URLHandler):
    _endpoint = 'event_mgmt.abstractReviewing-notifTplCondRem'


class UHConfModAbstractsMerge(URLHandler):
    _endpoint = 'event_mgmt.abstractsManagment-mergeAbstracts'


class UHAbstractModNotifLog(URLHandler):
    _endpoint = 'event_mgmt.abstractManagment-notifLog'


class UHAbstractModTools(URLHandler):
    _endpoint = 'event_mgmt.abstractTools'


class UHAbstractDelete(URLHandler):
    _endpoint = 'event_mgmt.abstractTools-delete'


class UHSessionModContribList(URLHandler):
    _endpoint = 'event_mgmt.sessionModification-contribList'


class UHSessionModContribListEditContrib(URLHandler):
    _endpoint = 'event_mgmt.sessionModification-editContrib'


class UHConfModifReschedule(URLHandler):
    _endpoint = 'event_mgmt.confModifSchedule-reschedule'


class UHContributionList(URLHandler):
    _endpoint = 'event.contributionListDisplay'


class UHContributionListToPDF(URLHandler):
    _endpoint = 'event.contributionListDisplay-contributionsToPDF'

    @classmethod
    def getStaticURL(cls, target=None, **params):
        return "files/generatedPdf/Contributions.pdf"


class UHConfModAbstractPropToAcc(URLHandler):
    _endpoint = 'event_mgmt.abstractManagment-propToAcc'


class UHAbstractManagmentBackToSubmitted(URLHandler):
    _endpoint = 'event_mgmt.abstractManagment-backToSubmitted'


class UHConfModAbstractPropToRej(URLHandler):
    _endpoint = 'event_mgmt.abstractManagment-propToRej'


class UHConfModAbstractWithdraw(URLHandler):
    _endpoint = 'event_mgmt.abstractManagment-withdraw'


class UHSessionModAddContribs(URLHandler):
    _endpoint = 'event_mgmt.sessionModification-addContribs'


class UHSessionModContributionAction(URLHandler):
    _endpoint = 'event_mgmt.sessionModification-contribAction'


class UHSessionModParticipantList(URLHandler):
    _endpoint = 'event_mgmt.sessionModification-participantList'


class UHSessionModToPDF(URLHandler):
    _endpoint = 'event_mgmt.sessionModification-contribsToPDF'


class UHConfModCFANotifTplUp(URLHandler):
    _endpoint = 'event_mgmt.abstractReviewing-notifTplUp'


class UHConfModCFANotifTplDown(URLHandler):
    _endpoint = 'event_mgmt.abstractReviewing-notifTplDown'


class UHConfAuthorIndex(URLHandler):
    _endpoint = 'event.confAuthorIndex'


class UHConfSpeakerIndex(URLHandler):
    _endpoint = 'event.confSpeakerIndex'


class UHContribModWithdraw(URLHandler):
    _endpoint = 'event_mgmt.contributionModification-withdraw'


class UHTrackModContribList(URLHandler):
    _endpoint = 'event_mgmt.trackModContribList'


class UHTrackModContributionAction(URLHandler):
    _endpoint = 'event_mgmt.trackModContribList-contribAction'


class UHTrackModParticipantList(URLHandler):
    _endpoint = 'event_mgmt.trackModContribList-participantList'


class UHTrackModToPDF(URLHandler):
    _endpoint = 'event_mgmt.trackModContribList-contribsToPDF'


class UHConfModContribQuickAccess(URLHandler):
    _endpoint = 'event_mgmt.confModifContribList-contribQuickAccess'


class UHSessionModContribQuickAccess(URLHandler):
    _endpoint = 'event_mgmt.sessionModification-contribQuickAccess'


class UHTrackModContribQuickAccess(URLHandler):
    _endpoint = 'event_mgmt.trackModContribList-contribQuickAccess'


class UHConfMyStuff(URLHandler):
    _endpoint = 'event.myconference'


class UHConfMyStuffMySessions(URLHandler):
    _endpoint = 'event.myconference-mySessions'


class UHConfMyStuffMyTracks(URLHandler):
    _endpoint = 'event.myconference-myTracks'


class UHConfMyStuffMyContributions(URLHandler):
    _endpoint = 'event.myconference-myContributions'


class UHConfModMoveContribsToSession(URLHandler):
    _endpoint = 'event_mgmt.confModifContribList-moveToSession'


class UHConferenceDisplayMaterialPackage(URLHandler):
    _endpoint = 'event.conferenceDisplay-matPkg'


class UHConferenceDisplayMaterialPackagePerform(URLHandler):
    _endpoint = 'event.conferenceDisplay-performMatPkg'


class UHConfAbstractBook(URLHandler):
    _endpoint = 'event.conferenceDisplay-abstractBook'

    @classmethod
    def getStaticURL(cls, target=None, **params):
        return "files/generatedPdf/BookOfAbstracts.pdf"


class UHConfAbstractBookLatex(URLHandler):
    _endpoint = 'event.conferenceDisplay-abstractBookLatex'


class UHConferenceToiCal(URLHandler):
    _endpoint = 'event.conferenceDisplay-ical'


class UHConfModAbstractBook(URLHandler):
    _endpoint = 'event_mgmt.confModBOA'


class UHConfModAbstractBookToogleShowIds(URLHandler):
    _endpoint = 'event_mgmt.confModBOA-toogleShowIds'


class UHAbstractReviewingSetup(URLHandler):
    _endpoint = 'event_mgmt.abstractReviewing-reviewingSetup'


class UHAbstractReviewingTeam(URLHandler):
    _endpoint = 'event_mgmt.abstractReviewing-reviewingTeam'


class UHConfModScheduleDataEdit(URLHandler):
    _endpoint = 'event_mgmt.confModifSchedule-edit'


class UHConfModMaterialPackage(URLHandler):
    _endpoint = 'event_mgmt.confModifContribList-matPkg'


class UHConfModProceedings(URLHandler):
    _endpoint = 'event_mgmt.confModifContribList-proceedings'


class UHConfModFullMaterialPackage(URLHandler):
    _endpoint = 'event_mgmt.confModifTools-matPkg'


class UHConfModFullMaterialPackagePerform(URLHandler):
    _endpoint = 'event_mgmt.confModifTools-performMatPkg'


class UHConfOffline(URLHandler):
    _endpoint = 'event_mgmt.confModifTools-offline'


class UHOfflineEventAccess(URLHandler):
    _endpoint = 'event_mgmt.getFile-offlineEvent'


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


# ------- Static webpages ------

class UHStaticConferenceDisplay(URLHandler):
    _relativeURL = "./index.html"


class UHStaticMaterialDisplay(URLHandler):
    _relativeURL = "none-page-material.html"

    @classmethod
    def _normalisePathItem(cls, name):
        return str(name).translate(string.maketrans(" /:()*?<>|\"", "___________"))

    @classmethod
    def getRelativeURL(cls, target=None, escape=True):
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
                relativeURL = None
                if isinstance(contrib, Contribution):
                    spk = ""
                    if len(contrib.getSpeakerList()) > 0:
                        spk = contrib.getSpeakerList()[0].getFamilyName().lower()
                    contribDirName = "%s-%s" % (contrib.getId(), spk)
                    relativeURL = "./%s-material-%s.html" % (contribDirName, cls._normalisePathItem(target.getId()))
                elif isinstance(contrib, Conference):
                    relativeURL = "./material-%s.html" % cls._normalisePathItem(target.getId())
                elif isinstance(contrib, Session):
                    relativeURL = "./material-s%s-%s.html" % (contrib.getId(), cls._normalisePathItem(target.getId()))

                if escape:
                    relativeURL = utf8rep(relativeURL)

                return relativeURL
        return cls._relativeURL


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

    @classmethod
    def getRelativeURL(cls, target=None, prevPath=".", escape=True):
        url = cls._relativeURL
        if target is not None:
            spk = ""
            if len(target.getSpeakerList()) > 0:
                spk = target.getSpeakerList()[0].getFamilyName().lower()
            contribDirName = "%s-%s" % (target.getId(), spk)
            track = target.getTrack()
            if track is not None:
                url = "./%s/%s/%s.html" % (prevPath, track.getTitle().replace(" ", "_"), contribDirName)
            else:
                url = "./%s/other_contributions/%s.html" % (prevPath, contribDirName)

        if escape:
            url = utf8rep(url)

        return url


class UHStaticSessionDisplay(URLHandler):
    _relativeURL = ""

    @classmethod
    def getRelativeURL(cls, target=None):
        return "./sessions/s%s.html" % target.getId()


class UHStaticResourceDisplay(URLHandler):
    _relativeURL = "none-page-resource.html"

    @classmethod
    def _normalisePathItem(cls, name):
        return str(name).translate(string.maketrans(" /:()*?<>|\"", "___________"))

    @classmethod
    def getRelativeURL(cls, target=None, escape=True):
        from MaKaC.conference import Contribution, Conference, Video, Link, Session

        relativeURL = cls._relativeURL
        if target is not None:
            mat = target.getOwner()
            contrib = mat.getOwner()
            # TODO: Remove the first if...cos it's just for CHEP.
            # Remove as well in pages.conferences.WMaterialStaticDisplay
            #if isinstance(mat, Video) and isinstance(target, Link):
            #    relativeURL = "./%s.rm"%os.path.splitext(os.path.basename(target.getURL()))[0]
            #    return relativeURL
            if isinstance(contrib, Contribution):
                relativeURL = "./%s-%s-%s-%s" % (cls._normalisePathItem(contrib.getId()), target.getOwner().getId(),
                                                 target.getId(), cls._normalisePathItem(target.getFileName()))
            elif isinstance(contrib, Conference):
                relativeURL = "./resource-%s-%s-%s" % (target.getOwner().getId(), target.getId(),
                                                       cls._normalisePathItem(target.getFileName()))
            elif isinstance(contrib, Session):
                relativeURL = "./resource-s%s-%s-%s" % (contrib.getId(), target.getId(),
                                                        cls._normalisePathItem(target.getFileName()))

            if escape:
                relativeURL = utf8rep(relativeURL)

            return relativeURL


class UHStaticTrackContribList(URLHandler):
    _relativeURL = ""

    @classmethod
    def getRelativeURL(cls, target=None, escape=True):
        url = cls._relativeURL
        if target is not None:
            url = "%s.html" % (target.getTitle().replace(" ", "_"))

        if escape:
            url = utf8rep(url)
        return url


class UHMStaticMaterialDisplay(URLHandler):
    _relativeURL = "none-page.html"

    @classmethod
    def _normalisePathItem(cls, name):
        return str(name).translate(string.maketrans(" /:()*?<>|\"", "___________"))

    @classmethod
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
                parents = "./material"
                if isinstance(owner, Session):
                    parents = "%s/session-%s-%s" % (parents, owner.getId(), cls._normalisePathItem(owner.getTitle()))
                elif isinstance(owner, Contribution):
                    if isinstance(owner.getOwner(), Session):
                        parents = "%s/session-%s-%s" % (parents, owner.getOwner().getId(),
                                                        cls._normalisePathItem(owner.getOwner().getTitle()))
                    spk = ""
                    if len(owner.getSpeakerList()) > 0:
                        spk = owner.getSpeakerList()[0].getFamilyName().lower()
                    contribDirName = "%s-%s" % (owner.getId(), spk)
                    parents = "%s/contrib-%s" % (parents, contribDirName)
                elif isinstance(owner, SubContribution):
                    contrib = owner.getContribution()
                    if isinstance(contrib.getOwner(), Session):
                        parents = "%s/session-%s-%s" % (parents, contrib.getOwner().getId(),
                                                        cls._normalisePathItem(contrib.getOwner().getTitle()))
                    contribspk = ""
                    if len(contrib.getSpeakerList()) > 0:
                        contribspk = contrib.getSpeakerList()[0].getFamilyName().lower()
                    contribDirName = "%s-%s" % (contrib.getId(), contribspk)
                    subcontspk = ""
                    if len(owner.getSpeakerList()) > 0:
                        subcontspk = owner.getSpeakerList()[0].getFamilyName().lower()
                    subcontribDirName = "%s-%s" % (owner.getId(), subcontspk)
                    parents = "%s/contrib-%s/subcontrib-%s" % (parents, contribDirName, subcontribDirName)
                relativeURL = "%s/material-%s.html" % (parents, cls._normalisePathItem(target.getId()))

                if escape:
                    relativeURL = utf8rep(relativeURL)
                return relativeURL
        return cls._relativeURL


class UHMStaticResourceDisplay(URLHandler):
    _relativeURL = "none-page.html"

    @classmethod
    def _normalisePathItem(cls, name):
        return str(name).translate(string.maketrans(" /:()*?<>|\"", "___________"))

    @classmethod
    def getRelativeURL(cls, target=None, escape=True):
        from MaKaC.conference import Contribution, Session, SubContribution

        if target is not None:

            mat = target.getOwner()
            owner = mat.getOwner()
            parents = "./material"
            if isinstance(owner, Session):
                parents = "%s/session-%s-%s" % (parents, owner.getId(), cls._normalisePathItem(owner.getTitle()))
            elif isinstance(owner, Contribution):
                if isinstance(owner.getOwner(), Session):
                    parents = "%s/session-%s-%s" % (parents, owner.getOwner().getId(),
                                                    cls._normalisePathItem(owner.getOwner().getTitle()))
                spk = ""
                if len(owner.getSpeakerList()) > 0:
                    spk = owner.getSpeakerList()[0].getFamilyName().lower()
                contribDirName = "%s-%s" % (owner.getId(), spk)
                parents = "%s/contrib-%s" % (parents, contribDirName)
            elif isinstance(owner, SubContribution):
                contrib = owner.getContribution()
                if isinstance(contrib.getOwner(), Session):
                    parents = "%s/session-%s-%s" % (parents, contrib.getOwner().getId(),
                                                    cls._normalisePathItem(contrib.getOwner().getTitle()))
                contribspk = ""
                if len(contrib.getSpeakerList()) > 0:
                    contribspk = contrib.getSpeakerList()[0].getFamilyName().lower()
                contribDirName = "%s-%s" % (contrib.getId(), contribspk)
                subcontspk = ""
                if len(owner.getSpeakerList()) > 0:
                    subcontspk = owner.getSpeakerList()[0].getFamilyName().lower()
                subcontribDirName = "%s-%s" % (owner.getId(), subcontspk)
                parents = "%s/contrib-%s/subcontrib-%s" % (parents, contribDirName, subcontribDirName)

            relativeURL = "%s/resource-%s-%s-%s" % (parents, cls._normalisePathItem(target.getOwner().getTitle()),
                                                    target.getId(), cls._normalisePathItem(target.getFileName()))
            if escape:
                relativeURL = utf8rep(relativeURL)
            return relativeURL
        return cls._relativeURL


# ------- END: Static webpages ------

class UHContribAuthorDisplay(URLHandler):
    _endpoint = 'event.contribAuthorDisplay'

    @classmethod
    def getStaticURL(cls, target, **params):
        if target is not None:
            return "contribs-%s-authorDisplay-%s.html" % (target.getId(), params.get("authorId", ""))
        return cls._getURL()


class UHConfTimeTableCustomizePDF(URLHandler):
    _endpoint = 'event.conferenceTimeTable-customizePdf'

    @classmethod
    def getStaticURL(cls, target, **params):
        return "files/generatedPdf/Conference.pdf"


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


class UHConferenceTicketPDF(URLHandler):
    _endpoint = 'event.e-ticket-pdf'

    @classmethod
    def getURL(cls, conf):
        url = cls._getURL()
        user = ContextManager.get("currentUser")
        if user:
            registrant = user.getRegistrantById(conf.getId())
            if registrant:
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
    _endpoint = 'event_mgmt.confModifEpayment'


class UHConfModifEPaymentEnableSection(URLHandler):
    _endpoint = 'event_mgmt.confModifEpayment-enableSection'


class UHConfModifEPaymentChangeStatus(URLHandler):
    _endpoint = 'event_mgmt.confModifEpayment-changeStatus'


class UHConfModifEPaymentdetailPaymentModification(URLHandler):
    _endpoint = 'event_mgmt.confModifEpayment-dataModif'


class UHConfModifEPaymentPerformdetailPaymentModification(URLHandler):
    _endpoint = 'event_mgmt.confModifEpayment-performDataModif'

###################################################################################


class UHConfModifRegForm(URLHandler):
    _endpoint = 'event_mgmt.confModifRegistrationForm'


class UHConfModifRegFormChangeStatus(URLHandler):
    _endpoint = 'event_mgmt.confModifRegistrationForm-changeStatus'


class UHConfModifRegFormDataModification(URLHandler):
    _endpoint = 'event_mgmt.confModifRegistrationForm-dataModif'


class UHConfModifRegFormPerformDataModification(URLHandler):
    _endpoint = 'event_mgmt.confModifRegistrationForm-performDataModif'


class UHConfModifRegFormActionStatuses(URLHandler):
    _endpoint = 'event_mgmt.confModifRegistrationForm-actionStatuses'


class UHConfModifRegFormStatusModif(URLHandler):
    _endpoint = 'event_mgmt.confModifRegistrationForm-modifStatus'


class UHConfModifRegFormStatusPerformModif(URLHandler):
    _endpoint = 'event_mgmt.confModifRegistrationForm-performModifStatus'


class UHConfModifRegistrationModification(URLHandler):
    _endpoint = 'event_mgmt.confModifRegistrationModification'


class UHConfModifRegistrationModificationSectionQuery(URLHandler):
    _endpoint = 'event_mgmt.confModifRegistrationModificationSection-query'


class UHConfModifRegistrantList(URLHandler):
    _endpoint = 'event_mgmt.confModifRegistrants'


class UHConfModifRegistrantNew(URLHandler):
    _endpoint = 'event_mgmt.confModifRegistrants-newRegistrant'


class UHConfModifRegistrantListAction(URLHandler):
    _endpoint = 'event_mgmt.confModifRegistrants-action'


class UHConfModifRegistrantPerformRemove(URLHandler):
    _endpoint = 'event_mgmt.confModifRegistrants-remove'


class UHRegistrantModification(URLHandler):
    _endpoint = 'event_mgmt.confModifRegistrants-modification'


class UHRegistrantAttachmentFileAccess(URLHandler):
    _endpoint = 'event_mgmt.confModifRegistrants-getAttachedFile'


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

    @classmethod
    def getStaticURL(cls, target, **params):
        return "confRegistrantsDisplay.html"


class UHConfModifRegistrantSessionModify(URLHandler):
    _endpoint = 'event_mgmt.confModifRegistrants-modifySessions'


class UHConfModifRegistrantSessionPeformModify(URLHandler):
    _endpoint = 'event_mgmt.confModifRegistrants-performModifySessions'


class UHConfModifRegistrantTransactionModify(URLHandler):
    _endpoint = 'event_mgmt.confModifRegistrants-modifyTransaction'


class UHConfModifRegistrantTransactionPeformModify(URLHandler):
    _endpoint = 'event_mgmt.confModifRegistrants-peformModifyTransaction'


class UHConfModifRegistrantAccoModify(URLHandler):
    _endpoint = 'event_mgmt.confModifRegistrants-modifyAccommodation'


class UHConfModifRegistrantAccoPeformModify(URLHandler):
    _endpoint = 'event_mgmt.confModifRegistrants-performModifyAccommodation'


class UHConfModifRegistrantSocialEventsModify(URLHandler):
    _endpoint = 'event_mgmt.confModifRegistrants-modifySocialEvents'


class UHConfModifRegistrantSocialEventsPeformModify(URLHandler):
    _endpoint = 'event_mgmt.confModifRegistrants-performModifySocialEvents'


class UHConfModifRegistrantReasonPartModify(URLHandler):
    _endpoint = 'event_mgmt.confModifRegistrants-modifyReasonParticipation'


class UHConfModifRegistrantReasonPartPeformModify(URLHandler):
    _endpoint = 'event_mgmt.confModifRegistrants-performModifyReasonParticipation'


class UHConfModifPendingQueues(URLHandler):
    _endpoint = 'event_mgmt.confModifPendingQueues'


class UHConfModifPendingQueuesActionConfSubm(URLHandler):
    _endpoint = 'event_mgmt.confModifPendingQueues-actionConfSubmitters'


class UHConfModifPendingQueuesActionConfMgr(URLHandler):
    _endpoint = 'event_mgmt.confModifPendingQueues-actionConfManagers'


class UHConfModifPendingQueuesActionSubm(URLHandler):
    _endpoint = 'event_mgmt.confModifPendingQueues-actionSubmitters'


class UHConfModifPendingQueuesActionMgr(URLHandler):
    _endpoint = 'event_mgmt.confModifPendingQueues-actionManagers'


class UHConfModifPendingQueuesActionCoord(URLHandler):
    _endpoint = 'event_mgmt.confModifPendingQueues-actionCoordinators'


class UHConfModifRegistrantMiscInfoModify(URLHandler):
    _endpoint = 'event_mgmt.confModifRegistrants-modifyMiscInfo'


class UHConfModifRegistrantMiscInfoPerformModify(URLHandler):
    _endpoint = 'event_mgmt.confModifRegistrants-performModifyMiscInfo'


class UHConfModifRegistrantStatusesModify(URLHandler):
    _endpoint = 'event_mgmt.confModifRegistrants-modifyStatuses'


class UHConfModifRegistrantStatusesPerformModify(URLHandler):
    _endpoint = 'event_mgmt.confModifRegistrants-performModifyStatuses'


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

    @classmethod
    def getStaticURL(cls, target=None, **params):
        return ""


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
    _endpoint = 'event_mgmt.confModifReviewing-access'


class UHConfModifReviewingPaperSetup(URLHandler):
    _endpoint = 'event_mgmt.confModifReviewing-paperSetup'


class UHSetTemplate(URLHandler):
    _endpoint = 'event_mgmt.confModifReviewing-setTemplate'


class UHDownloadContributionTemplate(URLHandler):
    _endpoint = 'event_mgmt.confModifReviewing-downloadTemplate'


class UHConfModifReviewingControl(URLHandler):
    _endpoint = 'event_mgmt.confModifReviewingControl'


class UHConfModifUserCompetences(URLHandler):
    _endpoint = 'event_mgmt.confModifUserCompetences'


class UHConfModifListContribToJudge(URLHandler):
    _endpoint = 'event_mgmt.confListContribToJudge'


class UHConfModifListContribToJudgeAsReviewer(URLHandler):
    _endpoint = 'event_mgmt.confListContribToJudge-asReviewer'


class UHConfModifListContribToJudgeAsEditor(URLHandler):
    _endpoint = 'event_mgmt.confListContribToJudge-asEditor'


class UHConfModifReviewingAssignContributionsList(URLHandler):
    _endpoint = 'event_mgmt.assignContributions'


class UHConfModifReviewingDownloadAcceptedPapers(URLHandler):
    _endpoint = 'event_mgmt.assignContributions-downloadAcceptedPapers'


#Contribution reviewing
class UHContributionModifReviewing(URLHandler):
    _endpoint = 'event_mgmt.contributionReviewing'


class UHContribModifReviewingMaterials(URLHandler):
    _endpoint = 'event_mgmt.contributionReviewing-contributionReviewingMaterials'


class UHContributionReviewingJudgements(URLHandler):
    _endpoint = 'event_mgmt.contributionReviewing-contributionReviewingJudgements'


class UHAssignReferee(URLHandler):
    _endpoint = 'event_mgmt.contributionReviewing-assignReferee'


class UHRemoveAssignReferee(URLHandler):
    _endpoint = 'event_mgmt.contributionReviewing-removeAssignReferee'


class UHAssignEditing(URLHandler):
    _endpoint = 'event_mgmt.contributionReviewing-assignEditing'


class UHRemoveAssignEditing(URLHandler):
    _endpoint = 'event_mgmt.contributionReviewing-removeAssignEditing'


class UHAssignReviewing(URLHandler):
    _endpoint = 'event_mgmt.contributionReviewing-assignReviewing'


class UHRemoveAssignReviewing(URLHandler):
    _endpoint = 'event_mgmt.contributionReviewing-removeAssignReviewing'


class UHContributionModifReviewingHistory(URLHandler):
    _endpoint = 'event_mgmt.contributionReviewing-reviewingHistory'


class UHContributionEditingJudgement(URLHandler):
    _endpoint = 'event_mgmt.contributionEditingJudgement'


class UHContributionGiveAdvice(URLHandler):
    _endpoint = 'event_mgmt.contributionGiveAdvice'


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

    @classmethod
    def getStaticURL(cls, target=None, **params):
        # We want a relative URL here, so just use url_for directly...
        return url_for(cls._endpoint)


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
        "Track": UHTrackModification,
        "Abstract": UHAbstractModify
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
