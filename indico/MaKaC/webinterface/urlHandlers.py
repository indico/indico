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

import re
import urlparse

from flask import g, has_request_context, request

from MaKaC.common.url import URL, EndpointURL
from MaKaC.common.timezoneUtils import nowutc
from MaKaC.common.contextManager import ContextManager

from indico.core.config import Config


class BooleanMixin:
    """Mixin to convert True to 'y' and remove False altogether."""
    _true = 'y'

    @classmethod
    def _translateParams(cls, params):
        return dict((key, cls._true if value is True else value)
                    for key, value in params.iteritems()
                    if value is not False)


class BooleanTrueMixin(BooleanMixin):
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
    def _want_secure_url(cls, force_secure=None):
        if not Config.getInstance().getBaseSecureURL():
            return False
        elif force_secure is not None:
            return force_secure
        elif not has_request_context():
            return False
        else:
            return request.is_secure

    @classmethod
    def _getURL(cls, _force_secure=None, **params):
        """ Gives the full URL for the corresponding request handler.

            Parameters:
                _force_secure - (bool) create a secure url if possible
                params - (dict) parameters to be added to the URL.
        """

        secure = cls._want_secure_url(_force_secure)
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
        if not _ignore_static and g.get('static_site'):
            return URL(cls.getStaticURL(target, **params))
        return cls._getURL(**cls._getParams(target, params))


# Hack to allow secure Indico on non-80 ports
def setSSLPort(url):
    """
    Returns url with port changed to SSL one.
    If url has no port specified, it returns the same url.
    SSL port is extracted from loginURL (MaKaCConfig)
    """
    # Set proper PORT for images requested via SSL
    sslURL = Config.getInstance().getBaseSecureURL()
    sslPort = ':%d' % (urlparse.urlsplit(sslURL).port or 443)

    # If there is NO port, nothing will happen (production indico)
    # If there IS a port, it will be replaced with proper SSL one, taken from loginURL
    regexp = ':\d{2,5}'   # Examples:   :8080   :80   :65535
    return re.sub(regexp, sslPort, url)


class UHWelcome(URLHandler):
    _endpoint = 'misc.index'


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
        if g.get('static_site'):
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


class UHConvenersSendEmail(URLHandler):
    _endpoint = 'event_mgmt.EMail-sendconvener'


class UHContribParticipantsSendEmail(URLHandler):
    _endpoint = 'event_mgmt.EMail-sendcontribparticipants'


class UHConferenceOtherViews(URLHandler):
    _endpoint = 'event.conferenceOtherViews'


class UHCategoryIcon(URLHandler):
    _endpoint = 'category.categoryDisplay-getIcon'


class UHConferenceModification(URLHandler):
    _endpoint = 'event_mgmt.conferenceModification'



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


class UHRoomBookingSearch4Bookings(URLHandler):
    _endpoint = 'rooms.roomBooking-search4Bookings'


class UHRoomBookingRoomDetails(BooleanTrueMixin, URLHandler):
    _endpoint = 'rooms.roomBooking-roomDetails'


class UHRoomBookingRoomStats(URLHandler):
    _endpoint = 'rooms.roomBooking-roomStats'


class UHRoomBookingDeleteBooking(URLHandler):
    _endpoint = 'rooms.roomBooking-deleteBooking'


# RB Administration
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


class UHConfDataModif(URLHandler):
    _endpoint = 'event_mgmt.conferenceModification-data'


class UHConfScreenDatesEdit(URLHandler):
    _endpoint = 'event_mgmt.conferenceModification-screenDates'


class UHConfPerformDataModif(URLHandler):
    _endpoint = 'event_mgmt.conferenceModification-dataPerform'


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


class UHConfEnterAccessKey(UHConfUser):
    _endpoint = 'event.conferenceDisplay-accessKey'


class UHConfManagementAccess(UHConfUser):
    _endpoint = 'event_mgmt.conferenceModification-managementAccess'


class UHConfEnterModifKey(UHConfUser):
    _endpoint = 'event_mgmt.conferenceModification-modifKey'


class UHConfCloseModifKey(UHConfUser):
    _endpoint = 'event_mgmt.conferenceModification-closeModifKey'


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


class UHAdminArea(URLHandler):
    _endpoint = 'admin.adminList'


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


class UHCategoryModification(URLHandler):
    _endpoint = 'category_mgmt.categoryModification'

    @classmethod
    def getActionURL(cls):
        return ''


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


class UHCategoryDataModif(URLHandler):
    _endpoint = 'category_mgmt.categoryDataModification'


class UHCategoryPerformModification(URLHandler):
    _endpoint = 'category_mgmt.categoryDataModification-modify'


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


class UHSubContribModifTools(URLHandler):
    _endpoint = 'event_mgmt.subContributionTools'


class UHSessionModification(URLHandler):
    _endpoint = 'event_mgmt.sessionModification'


class UHSessionDataModification(URLHandler):
    _endpoint = 'event_mgmt.sessionModification-modify'


class UHSessionModifSchedule(URLHandler):
    _endpoint = 'event_mgmt.sessionModifSchedule'


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


class UHSubContribModification(URLHandler):
    _endpoint = 'event_mgmt.subContributionModification'


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


class UHErrorReporting(URLHandler):
    _endpoint = 'misc.errors'


class UHAbstractWithdraw(URLHandler):
    _endpoint = 'event.abstractWithdraw'


class UHAbstractRecovery(URLHandler):
    _endpoint = 'event.abstractWithdraw-recover'


class UHConfModifContribList(URLHandler):
    _endpoint = 'event_mgmt.confModifContribList'


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


class UHConfMyStuffMyTracks(URLHandler):
    _endpoint = 'event.myconference-myTracks'


class UHConfModMoveContribsToSession(URLHandler):
    _endpoint = 'event_mgmt.confModifContribList-moveToSession'


class UHConfAbstractBook(URLHandler):
    _endpoint = 'event.conferenceDisplay-abstractBook'

    @classmethod
    def getStaticURL(cls, target=None, **params):
        return "files/generatedPdf/BookOfAbstracts.pdf"


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


class UHUpdateNews(URLHandler):
    _endpoint = 'admin.updateNews'


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


class UHIPBasedACL(URLHandler):
    _endpoint = 'admin.adminServices-ipbasedacl'


class UHIPBasedACLFullAccessGrant(URLHandler):
    _endpoint = 'admin.adminServices-ipbasedacl_fagrant'


class UHIPBasedACLFullAccessRevoke(URLHandler):
    _endpoint = 'admin.adminServices-ipbasedacl_farevoke'


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


class UHContact(URLHandler):
    _endpoint = 'misc.contact'


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
